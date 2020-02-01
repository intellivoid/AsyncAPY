import logging
from AsyncAPY.base import AsyncAPY
from AsyncAPY.filters import Filters
from AsyncAPY.objects import Packet, Client

srv = AsyncAPY(port=1500, logging_level=logging.DEBUG, addr="localhost", proto='ziproto')


@srv.handler_add("ping", filters=[Filters.Ip("127.0.0.1"), Filters.Fields(name=None)])
async def ping(client: Client, packet: Packet):
    await client.send(Packet({"status": "PONG!"}, None))
    await packet.stop_propagation()
    print("heh")

@srv.handler_add("ping", filters=[Filters.Ip("127.0.0.1")], priority=1)
async def another_ping(client: Client, packet: Packet):
    print(f"Hey there! I'm worthless!\nLook at these:\n{client}\n{packet}")
    await client.send(Packet({"status": "meh"}, None))

@srv.handler_add("banana", filters=[Filters.Fields(sob=None)])
async def useless(_, __):
    print("Ran!")
    await _.send(Packet({"a": "b"}, None))

if __name__ == "__main__":
    srv.start()
