from AsyncAPY.base import AsyncAPY


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
   await client.send(packet)


server.start()

