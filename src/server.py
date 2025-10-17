'''
RICHIEDE PYTHON 3.10 O SUPERIORE

python -m venv venv (Windows)
python -m venv venv (macOS)
-> Creazione ambiente virtuale

venv\Scripts\activate (Windows)
source venv\bin\activate (macOS)
-> Attivazione ambiente virtuale.

pip install -r requirements.txt (Windows)
pip3 install -r requirements.txt (macOS)
-> Installazione librerie richieste


python server.py [-H host] [-p port]
-H Opzionale - Default localhost
-p Opzionale - Default 6784

Esempio
(venv) C:\\marco > python server.py -p 3000
'''



import os
import asyncio  # gestione asincrona, server e client in parallelo
import logging  # log per debug e monitoraggio
import argparse  # gestione argomenti da riga di comando
from datetime import datetime  # timestamp per log e file

from websockets.asyncio.server import serve, ServerConnection
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
# Serve per creare server WebSocket asincrono, gestire connessioni, eccezioni su chiusura connessione.

from rich.logging import RichHandler  # migliora la leggibilità dei log in console

from utils import *  # import funzioni helper e classi per protocollo

# ============================
# Default settings
# ============================
DEFAULT_HOST = "localhost"  # host di default su cui ascolta il server
DEFAULT_PORT = 6784         # porta di default
LOGS_DIR = "logs"           # cartella dove vengono salvati i log

# ============================
# Logging setup
# ============================
# Creazione della cartella log se non esiste
os.makedirs(LOGS_DIR, exist_ok=True)

# Nome file log con timestamp preciso fino ai secondi
log_filename = datetime.now().strftime(f"{LOGS_DIR}/log-%Y-%m-%d_%H-%M-%S.mrCipo")

# Log su file, con formato leggibile
file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))

# Log su console con colori e tracebacks leggibili
console_handler = RichHandler(rich_tracebacks=True)

# Configurazione globale del logging
logging.basicConfig(
    level=logging.INFO,
    format="[mrCipo says] %(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[console_handler, file_handler]
)

logger = logging.getLogger("ChatServer")  # logger specifico per il server
logging.getLogger("websockets").setLevel(logging.WARNING)  # silenzia log dettagliati di websockets

# ============================
# Chat Server Class
# ============================
class ChatServer:

    def __init__(self, host: str, port: int, fUsersDB: str) -> None:
        self.host = host
        self.port = port
        self.connected_users = {}   # dizionario username -> websocket
        self.lock = asyncio.Lock()  # lock per evitare race condition su connected_users
        # carica utenti autorizzati dal file (username:password)
        self.authorized_users = parse_password_file(fUsersDB)

    async def _send(self, ws: ServerConnection, data: str) -> None:
        #Invia messaggio al singolo client
        try:
            await ws.send(data)
        except Exception as e:
            logger.error(f"Failed to send to {ws.remote_address}: {e}")

    async def _broadcast(self, data: str) -> None:
        recipients = list(self.connected_users.values())
        logger.info(f"Broadcast to {len(recipients)} user(s): {data}")

        if not recipients: return

        # invia a tutti in parallelo, gestendo eventuali eccezioni individuali
        tasks = [self._send(ws, data) for ws in recipients]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                addr = recipients[idx].remote_address if recipients[idx] else "unknown"
                logger.error(f"Broadcast send failed to {addr}: {result}")

    async def _loginUser(self, ws: ServerConnection, username: str, pwd: str) -> bool:
        #Gestisce il login di un utente. Controlla credenziali e sostituisce eventuale sessione attiva
        # verifica credenziali
        if username not in self.authorized_users or self.authorized_users[username] != pwd:
            logger.warning(f"Login failed for username '{username}'")
            return False

        async with self.lock:  # protezione su connected_users
            # se l'utente era già connesso, chiude la vecchia connessione
            if username in self.connected_users:
                old_ws = self.connected_users[username]
                logger.warning(f"User '{username}' is already logged in. Closing previous connection.")
                try:
                    await old_ws.close(code=4000, reason="Connection replaced")
                except Exception as e:
                    logger.error(f"Error closing previous socket for '{username}': {e}")
        
            self.connected_users[username] = ws  # registra nuova connessione
        
        logger.info(f"User '{username}' logged in successfully")
        # aggiorna lista utenti per tutti i client
        await self._broadcast(build_users_list_payload(self.connected_users))
        return True

    async def _isUserLogged(self, username: str) -> bool:
        #Verifica se l'utente è loggato
        return username in self.connected_users

    async def _parseRawMsg(self, ws: ServerConnection, rawMsg: str):
        #Analizza e gestisce i messaggi ricevuti secondo il protocollo
        if not is_valid_protocol_message(rawMsg):
            logger.warning(f"Malformed message received: {rawMsg}")
            return

        parts = rawMsg.strip().split(Protocol.SEPARATOR)
        cmd = parts[0]

        # gestione comandi specifici
        match cmd:
            case Protocol.LOGIN_REQUEST:
                login_result = await self._loginUser(ws, parts[1], parts[2])
                await self._send(ws, build_login_response(login_result))

            case Protocol.MSG:
                username = parts[1]
                if await self._isUserLogged(username):
                    message_text = parts[3]
                    logger.info(f"Message from '{username}': {message_text}")
                    await self._broadcast(rawMsg)
                else:
                    logger.warning(f"Message received from '{username}' without valid login")
                    # forza disconnessione se messaggio inviato senza login
                    await ws.close(code=1000, reason="Please log in first, CANE!")

    async def _onClientDisconnect(self, ws: ServerConnection):
        #Gestisce la disconnessione del client, aggiorna lista utenti
        payload = None
        async with self.lock:
            # trova username corrispondente alla connessione
            user = next((u for u, s in self.connected_users.items() if s == ws), None)
            if user:
                del self.connected_users[user]
                logger.info(f"User '{user}' disconnected")
                payload = build_users_list_payload(self.connected_users)
        # aggiorna lista utenti per tutti i client
        if payload:
            await self._broadcast(payload)
            logger.info("User list updated and broadcasted")

    async def _handler(self, ws: ServerConnection):
        #Handler principale per un singolo client
        try:
            async for msg in ws:  # ciclo continuo fino a chiusura connessione
                await self._parseRawMsg(ws, msg)
        except (ConnectionClosedOK, ConnectionClosedError):
            pass  # chiusura normale
        except Exception as e:
            logger.error(f"Unexpected error in client handler: {e}", exc_info=True)
        finally:
            await self._onClientDisconnect(ws)  # pulizia connessione

    async def start(self):
        #Avvia il server e rimane in ascolto infinito
        try:
            async with serve(self._handler, self.host, self.port):
                logger.info(f"Server listening on {self.host}:{self.port}")
                logger.info(f"Log file: {log_filename}")
                await asyncio.Future()  # mantiene server in esecuzione infinita
        except Exception as e:
            logger.critical(f"Server error: {e}", exc_info=True)

# ============================
# Argomenti da riga di comando
# ============================
def parse_args():
    parser = argparse.ArgumentParser(description="Mr.Cipo Chat Server")
    parser.add_argument("-p", "--port", type=int, help=f"Port (default {DEFAULT_PORT})")
    parser.add_argument("-H", "--host", type=str, help=f"Host (default {DEFAULT_HOST})")
    return parser.parse_args()

# ============================
# Main
# ============================
if __name__ == "__main__":
    args = parse_args()
    host = args.host if args.host else DEFAULT_HOST
    port = args.port if args.port else DEFAULT_PORT

    server = ChatServer(host, port, "users.txt")
    asyncio.run(server.start())
