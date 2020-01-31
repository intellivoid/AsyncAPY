import logging
from AsyncAPY.base import AsyncAPY
from AsyncAPY.filters import Filters
from AsyncAPY.objects import Packet, Client

srv = AsyncAPY(port=1500, logging_level=logging.DEBUG, addr="localhost")


@srv.handler_add("ping", filters=[Filters.Ip("127.0.0.1")])
async def ping(client: Client, packet: Packet):
    await client.send(Packet({"status": "PONG!"}, None))
    await packet.stop_propagation()


@srv.handler_add("ping", filters=[Filters.Ip("127.0.0.1")], priority=1)
async def another_ping(client: Client, packet: Packet):
    print(f"Hey there! I'm worthless!\nLook at these:\n{client}\n{packet}")

if __name__ == "__main__":
    srv.start()
