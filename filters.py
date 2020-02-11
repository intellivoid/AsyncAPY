from AsyncAPY.base import AsyncAPY
from AsyncAPY.filters import Filters  # Import the built-in filters


server = AsyncAPY(addr='0.0.0.0',
                  port=1500,
                  encoding='json',
                 )


@server.handler_add(filters=filters.Fields(foo='bar'))
async def filtered_handler(client, packet):
