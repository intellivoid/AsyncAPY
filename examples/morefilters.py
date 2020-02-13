from AsyncAPY.base import AsyncAPY
from AsyncAPY.filters import Filters

server = AsyncAPY(addr='0.0.0.0', port=1500)

# This filter will match any digit in the 'foo' field,
# and anything in the 'bar' field, e.g.:
# {"foo": 12355, "bar": "anything"}
# Also, only packets coming from localhost (127.0.0.1) and from 151.53.88.15, will reach
# this handler


@server.handler_add([Filters.Fields(foo='\d+', bar=None), Filters.Ip(["127.0.0.1", "151.53.88.15"])])
async def filtered_handler(client, packet):
    ...


server.start()
