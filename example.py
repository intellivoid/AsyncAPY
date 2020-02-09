from AsyncAPY.base import AsyncAPY


server = AsyncAPY(addr='0.0.0.0',
                  port=1500,
                  encoding="json",
                  logging_level=10,
                  byteorder='little'
                 )

@server.handler_add()
async def echo_server(client, packet):
   print(f"Hello world from {client}!")
   print(f"Echoing back {packet}...")
   await client.send(packet)


server.start()

