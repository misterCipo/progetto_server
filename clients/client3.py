# client_msg_ok.py
import asyncio
from websockets.asyncio.client import connect
from datetime import datetime

async def main():
    async with connect("ws://localhost:6784") as ws:
        # login
        await ws.send("log|matm|ciao")
        print(await ws.recv())

        # invio messaggio
        now = datetime.now().isoformat()
        await ws.send(f"msg|matm|{now}|Ciao a tutti!")
        # eventuale broadcast ricevuto
        while True:
            print(await ws.recv())

asyncio.run(main())
