from AsyncAPY.base import AsyncAPY
from AsyncAPY.filters import Filters
from AsyncAPY.objects import Client, Packet

server = AsyncAPY(config='server.conf')

@server.handler_add("test", filters=[Filters.Fields(field=r'\d+')])
async def test_function(client: Client, packet: Packet):

    print("Hi, I am test function")
    await client.send(Packet({"status": 200, "msg": "ur mom gay"}, None), False)
#    await packet.stop_propagation()


@server.handler_add("test", filters=[Filters.Fields(field=r'\d+')], priority=1)
async def woah_func(c, p):
    print("Hey, packet propagation works, well done master!")
    await c.send(Packet({"status": 200, "msg": "heh"}, None))


server.start()

