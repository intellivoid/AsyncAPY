# AsyncAPY - A fully fledged Python 3.6+ library to serve APIs asynchronously
# Copyright (C) 2019-2020 Intellivoid <https://github.com/intellivoid>
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

from typing import List, Dict, Union
from .filters import Filter
from types import FunctionType
from .errors import StopPropagation
import json


class Client:
    """This class represents a client"""

    def __init__(self, addr: str, server, stream=None, session: str = None):
        self.address = addr
        self._server = server
        self._stream = stream
        self.session = session

    async def ban(self):
        self._server.banned.add(self.address[0])

    async def send(self, packet, close: bool = True):
        payload = packet.payload.encode("utf-8")
        header = packet.length.to_bytes(self._server.header_size, self._server.byteorder)
        data = header + payload
        return await self._server.send_response(self._stream, data, self.session, close, packet.encoding)

    async def close(self):
        await self._stream.aclose()


class Packet:

    def __init__(self, fields: Union[Dict[str, str], str, bytes], encoding: str,sender: Client or None = None):
        self.sender = sender
        if not isinstance(encoding, str):
            raise ValueError("The encoding must be string!")
        if not encoding in ("json", "ziproto"):
            raise ValueError("The encoding must either be 'ziproto' or 'json'!")
        if encoding == "json":
            self.encoding = 0
        else:
            self.encoding = 1
        if isinstance(fields, dict):
            self.payload = json.dumps(fields)
        elif isinstance(fields, bytes):
            self.payload = json.dumps(json.loads(fields.decode("utf-8")))
        else:
            self.payload = json.dumps(json.loads(fields))
        self.length = len(self.payload)

    async def stop_propagation(self):
        raise StopPropagation


class Handler:

    def __init__(self, function: FunctionType, filters: List[Filter] = None, priority: int = 0):
        if filters is None:
            filters = []
        self.filters = filters
        self.function = function
        self.priority = priority

    def __repr__(self):
        return f"Handler({self.function}, {self.filters}, {self.priority})"

    def compare_priority(self, other):
        return self.priority == other.priority

    def compare_filters(self, other):
        if len(self.filters) != len(other.filters):
            return False
        for index, filter in enumerate(self.filters):
            ofilter = other.filters[index]
            if ofilter != filter:
                return False
        return True

    def compare(self, others: List, handlers, start=0):
        ret = []
        for handler in others[start:]:
            if handler == self:
                ret.append(handler)
                try:
                    handlers.remove(handler)
                except ValueError:
                    pass
        return ret, handlers

    def __eq__(self, other):
        if not isinstance(other, Handler):
            raise TypeError(f"The __eq__ operator is meant to compare Handler objects only, not {other}!")
        filters_equals = self.compare_filters(other)
        priority_equals = self.compare_priority(other)
        if other is self:
            return True
        if filters_equals & priority_equals:
            raise RuntimeError("Multiple handlers with identical filters cannot share priority level!")
        elif not priority_equals:
            if filters_equals:
                return True
            else:
                return False
        else:
            return False

    def check(self, client: Client, packet: Packet):
        for obj in self.filters:
            if not obj.check(client, packet):
                return False
        return True

    async def call(self, *args):
        return await self.function.__call__(*args)

    def __hash__(self):
        return self.function.__name__.__hash__()


class Group:

    def __init__(self, handlers: List[Handler]):
        self.handlers = sorted(handlers, key=lambda x: x.priority)
        self.filter = None

    def check(self, client: Client, packet: Packet):
        return self.handlers[0].check(client, packet)

    def __repr__(self):
        return f"Group({self.handlers})"

    def __iter__(self):
        return self.handlers.__iter__()




