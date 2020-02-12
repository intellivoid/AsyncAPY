from AsyncAPY.base import AsyncAPY

server = AsyncAPY(addr='127.0.0.1', port=1500, encoding="json", logging_level=10, byteorder='big')


@server.handler_add()
async def echo_server(client, packet):
    print(f"Hello world from {client}!")
    print(f"Echoing back {packet}...")
    await client.send(packet, close=False)
    # packet.stop_propagation()  # Uncomment to prevent the packet from being forwarded to the next handler


@server.handler_add(priority=1)    # Adding a priority is compulsory, or a RuntimeError exception will be raised
async def echo_server_2(client, packet):
    print(f"Hello world from {client} inside a group!")
    print(f"Echoing back {packet}...")
    await client.send(packet)

server.start()
