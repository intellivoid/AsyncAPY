# AsyncAPY - A fully fledged Python 3.6+ library to serve APIs asynchronously
# Copyright (C) 2019-2020 Intellivoid <https://github.com/Intellivoid>
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
import ziproto
import uuid


class Client:
    """This class represents a client, it is a high-level wrapper around the methods and objects of AsyncAPY

       :param addr: The client's IP address
       :type address: str
       :param server: The server object, needed to send back packets, it is stored in ``self._server``
       :type server: class: ``AsyncAPY.base.AsyncAPY``
       :param stream: The trio socket object associated with the client
       :type stream: class: ``trio.SocketStream``
       :param session: The session_id of the client, defaults to ``None``. Note that, internally, this parameter is replaced by a ``Session`` object
       :type session: str
       :param encoding: The client encoding, determined at every new session (can't change across the session), it can either be 0, for json, or 1, for ziproto, defaults to ``None``
       :type encoding: int
    """

    def __init__(self, addr: str, server, stream=None, session: str = None, encoding: int = None):
        self.address = addr
        self._server = server
        self._stream = stream
        self.session = session
        self.encoding = "json" if not encoding else "ziproto"

    def ban(self):
        """
        Bans the client's IP address from the server, without closing the currently
        open connection
        """

        self._server._banned.add(self.address)

    async def send(self, packet, close: bool = True):
        """High-level wrapper function around `AsyncAPY.send_response()`

           :param packet: A ``Packet`` object
           :type packet: class: ``Packet``
           :param close: If ``True``, the connection will be closed right after the packet is sent, it has to be set to ``False`` to take full advantages of packet propagation, defaults to ``True``
           :type close: bool, optional
        """

        payload = packet.payload.encode("utf-8")
        length_header = (packet.length + 2).to_bytes(self._server.header_size, self._server.byteorder)
        if packet.encoding == "json":
            content_encoding = (0).to_bytes(1, self._server.byteorder)
        else:
            payload = ziproto.encode(json.loads(payload))
            content_encoding = (1).to_bytes(1, self._server.byteorder)
            length_header = (len(payload) + 2).to_bytes(self._server.header_size, self._server.byteorder)
        protocol_version = (22).to_bytes(1, self._server.byteorder)
        headers = length_header + protocol_version + content_encoding
        data = headers + payload

        return await self._server.send_response(self._stream, data, self.session, close, from_client=True)

    async def close(self):
        """Closes the client connection
        """

        await self._stream.aclose()
        if self.session in self._server._sessions[self.address]:
            self._server._sessions[self.address].remove(self.session)

    def __repr__(self):
        return f"Client({self.address})"

    def get_sessions(self):
        """Returns all the active sessions associated with the client's IP address"""

        return self._server._sessions[self.address]


class Packet:
    """
    This class implements a high-level wrapper around AsyncAProto packets

    :param fields: The payload, it can either be a Python dictionary or valid JSON string (it can also be encoded as bytes)
    :type fields: Union[dict, str, bytes]
    :param encoding: The payload desired encoding, it can either be 0, for json, or 1 for ziproto
    :type encoding: int
    :param sender: This parameter is meant to be initialized internally, and points to the ``Client`` object that sent the associated payload, defaults to ``None``
    :type sender: Union[Client, None], optional

    ``Packet`` objects have a dict-like interface to access the payload easily. If the packet's payload is ``{"foo": "bar"}``, you can get the value of foo by doing ``yourpacket["foo"]``
    """

    def __init__(self, fields: Union[dict, str, bytes], encoding: str, sender: Union[Client, None] = None):
        """Object constructor"""

        self.sender = sender
        if not isinstance(encoding, int):
            raise ValueError("The encoding must be int!")
        if encoding not in (0, 1):
            raise ValueError("The encoding must either be 0 or 1!")
        if encoding == 0:
            self.encoding = "json"
        elif encoding == 1:
            self.encoding = "ziproto"
        if isinstance(fields, dict):
            self.payload = json.dumps(fields)
        elif isinstance(fields, bytes):
            self.payload = json.dumps(json.loads(fields.decode("utf-8")))
        else:
            self.payload = json.dumps(json.loads(fields))
        self.length = len(self.payload)
        self.dict_payload = json.loads(self.payload)

    async def stop_propagation(self):
        """Stops a packet within a group, see ``AsyncAPY.errors.StopPropagation``

        :raises: StopPropagation"""
        raise StopPropagation

    def __repr__(self):
        return f"Packet({self.payload})"

    def __iter__(self):
        return self.dict_payload.__iter__()

    def __contains__(self, other):
        return self.dict_payload.__contains__(other)

    def __getitem__(self, key):
        return self.dict_payload.__getitem__(key)

class Handler:

    """An object meant for internal use. Every function is wrapped inside a ``Handler`` object together
    with its priority and filters

    :param function: The asynchronous function, accepting two positional parameters (a ``Client`` object and a ``Packet`` object)
    :type function: function
    :param filters: A list of ``AsyncAPY.filters.Filter`` objects, defaults to ``None``
    :type filters: List[Filter]
    :param priority: An integer representing the priority of the handler within a group, the lower this number, the higher execution precedence, defaults to 0
    :type priority: int"""

    def __init__(self, function: FunctionType, filters: List[Filter] = None, priority: int = 0):
        """Object constructor"""

        if filters is None:
            filters = []
        self.filters = filters
        self.function = function
        self.priority = priority

    def __repr__(self):
        """Returns ``repr(self)``

        :returns repr: A string representation of the object
        :rtype: str
        """

        return f"Handler({self.function}, {self.filters}, {self.priority})"

    def compare_priority(self, other):
        """Method meant for internal use to compare 2 handlers priorities, used for grouping

        :param other: Another instance of ``Handler``
        :type other: class: ``Handler``
        :returns comparison: ``True`` if the priorities are equal, ``False`` otherwhise
        :rtype: bool
        """

        return self.priority == other.priority

    def compare_filters(self, other):
        """A method meant for internal use, used inside ``self.__eq__()``, compares filters instead of priorities

        :param other: Another instance of ``Handler``
        :type other: class: ``Handler``
        """

        if len(self.filters) != len(other.filters):
            return False
        for index, filter in enumerate(self.filters):
            ofilter = other.filters[index]
            if ofilter != filter:
                return False
        return True

    def compare(self, others: List):
        """Compares one or more handlers to self, returns the list of the matching handlers and the original list

        :param others: A list of one or more handlers to compare to ``self``
        :type others: List[Handler]
        :returns ret: The list of the handlers with common filters and different priorities, please note that this always contains at least one element (which is ``self``)
        :rtype: List[Handler]
        """

        ret = [self]
        for handler in others:
            if handler == self:
                ret.append(handler)
        return ret

    def __eq__(self, other):
        """Implements ``self == other``, only meant to compare ``Handler`` objects

        :param other: Another instance of ``Handler``
        :type other: class: ``Handler``
        """

        if not isinstance(other, Handler):
            raise TypeError(f"The __eq__ operator is meant to compare Handler objects only, not {other}!")
        filters_equals = self.compare_filters(other)
        priority_equals = self.compare_priority(other)
        if not priority_equals:
            if filters_equals:
                return True
            else:
                return False
        else:
            return False

    def check(self, client: Client, packet: Packet):
        """Iteratively calls the ``check()`` method on ``self.filters``, returns ``True`` if all filters return ``True``, ``False`` otherwise

           :param client: The client to check for
           :type client: class: ``Client``
           :param packet: The packet object to check for
           :type packet: class: ``Packet``
           :returns shall_pass: ``True`` if the handler matches all filters, ``False`` otherwise
           :rtype: bool

        """

        for obj in self.filters:
            if not obj.check(client, packet):
                return False
        return True

    async def call(self, *args):
        """Calls ``self.function`` asynchronously, passing ``*args`` as parameters"""

        return await self.function(*args)

    def __hash__(self):
        return hash(self.function.__name__)

class Group:

    """Implements a ``Group`` object, used to group multiple handlers with identical filters
       and different priorities, this object is meant to be initialized internally

       :param handlers: The list of handlers that has to be grouped, they will be sorted by their ``priority`` attribute
       :type handlers: List[Handler]
    """

    def __init__(self, handlers: List[Handler]):
        """Object constructor"""

        self.handlers = sorted(handlers, key=lambda x: x.priority)
        for index, handler in enumerate(self.handlers):
            if not len(self.handlers) - index == 1:
                first = handler.priority
                second = self.handlers[index + 1].priority
                if first == second:
                    raise RuntimeError("Handlers with identical filters cannot share priority level!")

    def check(self, client: Client, packet: Packet):
        """Checks the filters of the group, one time only on the first filter

           :param client: The client to check for
           :type client: class: ``Client``
           :param packet: The packet object to check for
           :type packet: class: ``Packet``
           :returns shall_pass: ``True`` if the group matches all filters, ``False`` otherwise
           :rtype: bool

        """

        return self.handlers[0].check(client, packet)

    def __repr__(self):
        """Returns ``repr(self)``

           :returns repr: A string representation of the object
           :rtype: str
        """

        return f"Group({self.handlers})"

    def __iter__(self):
        """Implements the ``__iter__()`` method of ``self.handlers`` in ``self``,
        thus making the ``Group`` object itself an iterable
        """

        return self.handlers.__iter__()

    def __hash__(self):
        return hash(self.handlers[0].function.__name__)

class Session:

    """This class represents a client session

       :param session_id: The UUID of the session
       :type session_id: class: ``uuid.uuid4``
       :param client: The client object associated with the current session
       :type client: class: ``Client``
       :param date: The UNIX Epoch timestamp of when the session was created
       :type date: float
    """

    def __init__(self, session_id: uuid.uuid4, client: Client, date: float):
       """Object constructor"""

       self.session_id = session_id
       self.client = client
       self.date = date

    async def close(self):
        """Closes the associated client connection"""

        await self.client.close()

    def get_client(self):
        """Returns the associated client object"""

        return self.client

    def ban_client(self, close=False):
        """Bans the associated client' IP from the server

           :param close: If ``True``, the associated client connection will be closed after its IP gets banned, defaults to ``False``
        """

        self.client.ban()
        if close:
            self.close()

    def __repr__(self):
        return f"Session({str(self.session_id)})"

    def __hash__(self):
        return hash(self.session_id)

    def __eq__(self, other):
        if self.__hash__() == other.__hash__() and other.date == self.date:
            return True
        return False
