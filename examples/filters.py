from AsyncAPY import Server
from AsyncAPY.filters import Filters

server = Server(addr='0.0.0.0', port=1500)

# This filter will match any digit in the 'foo' field,
# and anything in the 'bar' field, e.g.:
# {"foo": 12355, "bar": "anything"}

@server.add_handler(Filters.Fields(foo='\d+', bar=None))
async def filtered_handler(client, packet):
    print(f"Look at this! {client} sent me {packet}!")
    await client.close()


server.start()
