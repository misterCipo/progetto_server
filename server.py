# server.py
import asyncio
import logging
from websockets.asyncio.server import serve, ServerConnection
from rich.logging import RichHandler
from utils import *

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[RichHandler()]
)
logger = logging.getLogger("ChatServer")
logging.getLogger("websockets").setLevel(logging.WARNING)


class ChatServer:
    def __init__(self, host: str, port: int, fUsersDB: str):
        self.host = host
        self.port = port
        self.connected_users = {}
        self.lock = asyncio.Lock()
        self.authorized_users = parse_password_file(fUsersDB)

    async def _send(self, ws: ServerConnection, data: str):
        try:
            await ws.send(data)
        except Exception as e:
            logger.error(f"Errore invio a {ws}: {e}")

    async def _broadcast(self, data: str):
        async with self.lock:
            coros = [self._send(ws, data) for ws in self.connected_users.values()]
            if coros:
                await asyncio.gather(*coros, return_exceptions=True)

    async def _loginUser(self, ws: ServerConnection, username: str, pwd: str) -> bool:
        # Controlla credenziali
        if username not in self.authorized_users or self.authorized_users[username] != pwd:
            logger.warning(f"Login errato: username={username} password errata")
            return False

        async with self.lock:
            # Se già connesso, chiude la vecchia connessione
            if username in self.connected_users:
                old_ws = self.connected_users[username]
                logger.warning(f"{username} già loggato, chiudo la vecchia connessione")
                try:
                    await old_ws.close(code=4000, reason="Connessione sostituita")
                except Exception as e:
                    logger.error(f"Errore chiusura vecchio socket di {username}: {e}")

            # Registra la nuova connessione
            self.connected_users[username] = ws

        logger.info(f"{username} login corretto")
        await self._broadcast(build_users_list_payload(self.connected_users))
        logger.info("Lista utenti aggiornata inviata in broadcast")
        return True

    async def _isUserLogged(self, username: str) -> bool:
        return username in self.connected_users

    async def _parseRawMsg(self, ws: ServerConnection, rawMsg: str):
        if not is_valid_protocol_message(rawMsg):
            logger.warning(f"Messaggio formattato male ricevuto: {rawMsg}")
            return

        parts = rawMsg.strip().split(Protocol.SEPARATOR)
        cmd = parts[0]

        match cmd:
            case Protocol.LOGIN_REQUEST:
                login_result = await self._loginUser(ws, parts[1], parts[2])
                await self._send(ws, build_login_response(login_result))

            case Protocol.MSG:
                username = parts[1]
                if await self._isUserLogged(username):
                    message_text = parts[3]
                    logger.info(f"Messaggio corretto ricevuto da {username}: {message_text}")
                    await self._broadcast(rawMsg)
                    logger.info(f"Messaggio inviato in broadcast da {username}: {message_text}")
                else:
                    logger.warning(f"Messaggio ricevuto da {username} senza login corretto: {rawMsg}")
                    await ws.close(code=1000, reason="Loggati prima!")

    async def _onClientDisconnect(self, ws: ServerConnection):
        async with self.lock:
            user = next((u for u, s in self.connected_users.items() if s == ws), None)
            if user:
                del self.connected_users[user]
                logger.info(f"{user} client disconnesso")
                await self._broadcast(build_users_list_payload(self.connected_users))
                logger.info("Lista utenti aggiornata inviata in broadcast")

    async def _handler(self, ws: ServerConnection):
        try:
            async for msg in ws:
                await self._parseRawMsg(ws, msg)
        finally:
            await self._onClientDisconnect(ws)

    async def start(self):
        async with serve(self._handler, self.host, self.port):
            logger.info(f"Server in ascolto su {self.host}:{self.port}")
            await asyncio.Future()


if __name__ == "__main__":
    server = ChatServer("localhost", 6784, "users.txt")
    asyncio.run(server.start())
