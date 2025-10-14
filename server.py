# server.py
import asyncio
import logging
from websockets.asyncio.server import serve, ServerConnection
from rich.logging import RichHandler

from utils import *

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[RichHandler()]
)
logger = logging.getLogger("ChatServer")

logging.getLogger("websockets").setLevel(logging.WARNING)

class ChatServer:
    def __init__(self, host: str, port: int, fUsersDB: str) -> None:
        self.host = host
        self.port = port
        self.connected_users = {}
        self.lock = asyncio.Lock()
        self.authorized_users = parse_password_file(fUsersDB)


    async def _send(self, ws: ServerConnection, data: str):
        try:
            await ws.send(data)
        except Exception as e:
            logger.error(f"Error sending: {e}")


    async def _broadcast(self, data: str):
        async with self.lock:
            coros = [self._send(ws, data) for ws in self.connected_users.values()]
            if coros:
                await asyncio.gather(*coros, return_exceptions=True)


    async def _loginUser(self, ws, user: str, pwd: str) -> bool:
        if user in self.connected_users:
            return False  # già loggato
        if user in self.authorized_users and pwd == self.authorized_users[user]:
            async with self.lock:
                self.connected_users[user] = ws
            logger.info(f"{user} si è loggato")
            self._log_connected_users()
            return True
        return False


    async def _isUserLogged(self, user: str) -> bool:
        return user in self.connected_users


    async def _parseRawMsg(self, ws: ServerConnection, rawMsg: str):
        if is_valid_protocol_message(rawMsg):
            parts = rawMsg.strip().split(Protocol.SEPARATOR)
            cmd = parts[0]

            match cmd:
                case Protocol.LOGIN_REQUEST:
                    login_result = await self._loginUser(ws, parts[1], parts[2])
                    await self._send(ws, build_login_response(login_result))

                case Protocol.MSG:
                    if await self._isUserLogged(parts[1]):
                        await self._broadcast(rawMsg)
                    else:
                        await ws.close(code=1000, reason="Loggati prima!")


    async def _onClientDisconnect(self, ws: ServerConnection):
        async with self.lock:
            user = next((u for u, s in self.connected_users.items() if s == ws), None)
            if user:
                del self.connected_users[user]
                logger.info(f"{user} si è disconnesso")
                

    async def _handler(self, ws: ServerConnection):
        try:
            async for msg in ws:
                await self._parseRawMsg(ws, msg)
        finally:
            await self._onClientDisconnect(ws)


    async def start(self):
        async with serve(self._handler, self.host, self.port):
            logger.info(f"Server listening on {self.host}:{self.port}")
            await asyncio.Future()


if __name__ == "__main__":
    server = ChatServer('localhost', 6784, 'users.txt')
    asyncio.run(server.start())
