import os
import asyncio
from websockets.asyncio.server import serve, ServerConnection

from utils import *

class ChatServer:
    def __init__(self, host: str, port: int, fUsersDB: str) -> None:
        self.host = host
        self.port = port

        self.connected_users = []
        self.lock = asyncio.Lock()

        self.authorized_users = parse_password_file(fUsersDB)
    
    async def _send(self, data):
        ''
        
    async def _loginUser(self, user: str, pwd: str) -> bool:
        if user in self.authorized_users and pwd == self.authorized_users[user]:
            async with self.lock:
                self.connected_users.append(user)
        else:
            print('login errato')


    async def _parseRawMsg(self, rawMsg: str) -> None:
        msg = rawMsg.split('|')

        match msg[0]:
            case 'log':
                if len(msg) == 3:
                    await self._loginUser(msg[1], msg[2])

            case _:
                pass

        

    async def _handler(self, ws: ServerConnection) -> None:
        async for message in ws:
            await self._parseRawMsg(message)


    async def start(self) -> None:
        async with serve(self._handler, self.host, self.port) as server:
            await server.serve_forever()


if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')
    server = ChatServer('localhost', 9999, 'users.txt')
    asyncio.run(server.start())