from AsyncAPY.base import AsyncAPY
import trio

server = AsyncAPY(addr='127.0.0.1',
                  port=1500,
                  encoding="json",
                  logging_level=10,
                  byteorder='big'
                 )

@server.handler_add()
async def echo_server(client, packet):
   print(f"Hello world from {client}!")
   print(f"Echoing back {packet}...")
   await client.send(packet, close=False)
   await trio.sleep(1)
   await client.close()

server.start()

