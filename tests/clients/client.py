# Test client
import asyncio
from websockets.asyncio.client import connect


async def hello():
    async with connect("ws://localhost:6784") as websocket:
        await websocket.send("log|matm|ciao")
        while True:
            message = await websocket.recv()
            print(message)



if __name__ == "__main__":
    asyncio.run(hello())