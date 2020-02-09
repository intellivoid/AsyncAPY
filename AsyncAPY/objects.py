# AsyncAPY - A fully fledged Python 3.6+ library to serve APIs asynchronously
# Copyright (C) 2019-2020 Nocturn9x <https://github.com/nocturn9x>
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
    """This class represents a client, it is a high-level wrapper around the methods and objects of AsyncAPY

       :param address: The client's IP address
       :type address: str
       :param _server: The server object, needed to send back packets
       :type _server: class: `AsyncAPY.base.AsyncAPY`
       :param _stream: The trio socket object associated with the client
       :type stream: class: `trio.SocketStream`
       :param session: The session_id of the client
       :type session: str
    """

    def __init__(self, addr: str, server, stream=None, session: str = None):
        self.address = addr
        self._server = server
        self._stream = stream
        self.session = session

    async def ban(self):
        """
        Bans the client's IP address from the server
        """

        self._server.banned.add(self.address[0])

    async def send(self, packet, close: bool = True):
        """High-level wrapper function around `AsyncAPY.send_response()`

           :param packet: A `Packet` object
           :type packet: class: `Packet`
           :param close: If `True`, the connection will be closed right after the packet is sent, it has to be set to `False` to take full advantages of packet propagation, defaults to `True`
           :type close: bool, optional
        """

        payload = packet.payload.encode("utf-8")
        length_header = packet.length.to_bytes(self._server.header_size, self._server.byteorder)
        if packet.encoding == "json":
            content_encoding = (0).to_bytes(1, self._server.byteorder)
        else:
            content_encoding = (1).to_bytes(1, self._server.byteorder)
        protocol_version = (22).to_bytes(1, self._server.byteorder)
        headers = length_header + content_encoding + protocol_version
        data = headers + payload
        return await self._server.send_response(self._stream, data, self.session, close, packet.encoding, from_client=True)

    async def close(self):
        """Closes the client connection
        """

        await self._stream.aclose()


class Packet:
    """
    This class implements a high-level wrapper around AsyncAProto packets

    :param fields: The payload, it can either be a Python dictionary or valid JSON string (it can also be encoded as bytes)
    :type fields: Union[dict, str, bytes]
    :param encoding: The payload desired encoding, it can either be `"json"` or `"ziproto"`
    :type encoding: str
    :param sender: This parameter is meant to be initialized internally, and points to the `Client` object that sent the associated payload, defaults to `None`
    :type sender: Union[Client, None], optional
    """

    def __init__(self, fields: Union[dict, str, bytes], encoding: str, sender: Union[Client, None] = None):
        """Object constructor"""

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
        self.length = len(self.payload) + 2

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

