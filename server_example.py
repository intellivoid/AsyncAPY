# AsyncAPY - A fully fledged Python 3.6+ library to serve APIs asynchronously
# Copyright (C) 2019-2020 nocturn9x <https://github.com/nocturn9x>
#
# This file is part of AsyncAPY.
#
# AsyncAPY is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# AsyncAPY is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with AsyncAPY.  If not, see <http://www.gnu.org/licenses/>.

from AsyncAPY import Server, Packet
from AsyncAPY.filters import Filters


server = Server(config='config.ini')

@server.add_handler(Filters.Fields(foo='test_payload'))   # This is checked before the echo handler
async def filtered_handler(client, packet):
    print(f"Hello 1 from {client}!")
    print(f"Packet received is {packet}")
    await client.send(Packet({"response": "OK"}, encoding=client.encoding))   # You can choose an encoding
    await client.close()


@server.add_handler(group=-1)  # Will be executed before any other handler because -1 < 0
async def grouped_handler(client, packet):
    print(f"Propagation for {client} was succesful!")
    if "foo" in packet and packet["foo"] != "test_payload":
        await client.send(packet)


@server.add_handler()   # This will execute if filtered_handler doesn't match
async def echo_server(client, packet):
    print(f"Hello world from {client}!")
    print(f"Echoing back {packet}...")
    await client.send(packet)
    await client.close()


server.start()
