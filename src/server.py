# server.py
import asyncio
import logging
import os
import argparse
from datetime import datetime
from websockets.asyncio.server import serve, ServerConnection
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
from rich.logging import RichHandler

from utils import *

# ============================
# Default settings
# ============================
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6784
LOGS_DIR = "logs"

# ============================
# Logging setup
# ============================
os.makedirs(LOGS_DIR, exist_ok=True)
log_filename = datetime.now().strftime(f"{LOGS_DIR}/log-%Y-%m-%d_%H-%M-%S.log")

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))

console_handler = RichHandler(rich_tracebacks=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[console_handler, file_handler]
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

    async def _send(self, ws: ServerConnection, data: str) -> None:
        try:
            await ws.send(data)
        except Exception as e:
            logger.error(f"Failed to send to {ws.remote_address}: {e}")

    async def _broadcast(self, data: str) -> None:
        recipients = list(self.connected_users.values())
        count = len(recipients)
        logger.info(f"Broadcast to {count} user(s): {data}")

        if not recipients:
            return

        tasks = [self._send(ws, data) for ws in recipients]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                addr = recipients[idx].remote_address if recipients[idx] else "unknown"
                logger.error(f"Broadcast send failed to {addr}: {result}")

    async def _loginUser(self, ws: ServerConnection, username: str, pwd: str) -> bool:
        if username not in self.authorized_users or self.authorized_users[username] != pwd:
            logger.warning(f"Login failed for username '{username}'")
            return False

        async with self.lock:
            if username in self.connected_users:
                old_ws = self.connected_users[username]
                logger.warning(f"User '{username}' is already logged in. Closing previous connection.")
                try:
                    await old_ws.close(code=4000, reason="Connection replaced")
                except Exception as e:
                    logger.error(f"Error closing previous socket for '{username}': {e}")
        
            self.connected_users[username] = ws
        
        logger.info(f"User '{username}' logged in successfully")
        await self._broadcast(build_users_list_payload(self.connected_users))
        return True

    async def _isUserLogged(self, username: str) -> bool:
        return username in self.connected_users

    async def _parseRawMsg(self, ws: ServerConnection, rawMsg: str):
        if not is_valid_protocol_message(rawMsg):
            logger.warning(f"Malformed message received: {rawMsg}")
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
                    logger.info(f"Message from '{username}': {message_text}")
                    await self._broadcast(rawMsg)
                else:
                    logger.warning(f"Message received from '{username}' without valid login")
                    await ws.close(code=1000, reason="Please log in first")

    async def _onClientDisconnect(self, ws: ServerConnection):
        payload = None
        async with self.lock:
            user = next((u for u, s in self.connected_users.items() if s == ws), None)
            if user:
                del self.connected_users[user]
                logger.info(f"User '{user}' disconnected")
                payload = build_users_list_payload(self.connected_users)
        if payload:
            await self._broadcast(payload)
            logger.info("User list updated and broadcasted")

    async def _handler(self, ws: ServerConnection):
        try:
            async for msg in ws:
                await self._parseRawMsg(ws, msg)
        except (ConnectionClosedOK, ConnectionClosedError):
            pass
        except Exception as e:
            logger.error(f"Unexpected error in client handler: {e}", exc_info=True)
        finally:
            await self._onClientDisconnect(ws)

    async def start(self):
        try:
            async with serve(self._handler, self.host, self.port):
                logger.info(f"Server listening on {self.host}:{self.port}")
                logger.info(f"Log file: {log_filename}")
                await asyncio.Future()
        except Exception as e:
            logger.critical(f"Server error: {e}", exc_info=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Chat WebSocket Server")
    parser.add_argument("-p", "--port", type=int, help=f"Port (default {DEFAULT_PORT})")
    parser.add_argument("-H", "--host", type=str, help=f"Host (default {DEFAULT_HOST})")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    host = args.host if args.host else DEFAULT_HOST
    port = args.port if args.port else DEFAULT_PORT

    server = ChatServer(host, port, "users.txt")
    asyncio.run(server.start())
