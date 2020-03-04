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

from AsyncAPY.base import AsyncAPY
from AsyncAPY.filters import Filters

server = AsyncAPY(addr='127.0.0.1', port=1500, encoding="json", logging_level=10, byteorder='big')


@server.handler_add()
async def echo_server(client, packet):
    print(f"Hello world from {client}!")
    print(f"Echoing back {packet}...")
    await client.send(packet, close=False)


@server.handler_add([Filters.Fields(req=r'test_payload')])
async def filtered_handler(client, packet):
    print(f"Propagation succesful from {client}!")
    print(f"Packet received is {packet}")
    await client.close()


server.start()
