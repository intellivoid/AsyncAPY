from AsyncAPY.base import AsyncAPY
from AsyncAPY.filters import Filters

server = AsyncAPY(addr='0.0.0.0', port=1500)

# This filter will match any digit in the 'foo' field,
# and anything in the 'bar' field, e.g.:
# {"foo": 12355, "bar": "anything"}

@server.handler_add([Filters.Fields(foo='\d+', bar=None)])
async def filtered_handler(client, packet):
    ...


server.start()
