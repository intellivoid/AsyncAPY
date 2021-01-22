from asyncapy import Server

server = Server(addr="127.0.0.1", port=1500)


@server.add_handler()
async def echo_server(client, packet):
    print(f"Hello world from {client}!")
    print(f"Echoing back {packet}...")
    await client.send(packet)
    await client.close()


@server.add_handler(group=-1)
async def echo_server_2(client, packet):
    print(f"Hello world from {client} inside a group!")
    print(f"Echoing back {packet}...")
    await client.send(packet)
    # packet.stop_propagation()  # This would prevent the packet from being forwarded to the next handler


server.start()
