
import asyncio
from websockets.asyncio.client import connect


async def hello():
    async with connect("ws://localhost:9999") as websocket:
        await websocket.send("log|matm|ciao")
        message = await websocket.recv()
        print(message)


if __name__ == "__main__":
    asyncio.run(hello())