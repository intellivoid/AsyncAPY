import logging
from AsyncAPY.base import AsyncAPY
from AsyncAPY.filters import Filters
from AsyncAPY.objects import Packet, Client

srv = AsyncAPY(port=1500, logging_level=logging.DEBUG, addr="localhost")


@srv.handler_add("ping", filters=[Filters.Ip("127.0.0.1")])
async def ping(client: Client, _):
    await client.send(Packet({"status": "PONG!"}, None))


if __name__ == "__main__":
    srv.start()
