# AsyncAPY - A fully fledged Python 3.6+ library to serve APIs asynchronously
# Copyright (C) 2019-2020 intellivoid <https://github.com/intellivoid>
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

    def __init__(self, addr: str, server, stream: trio.SocketStream, session: str, encoding: int):
        self.address = addr
        self._server = server
        self._stream = stream
        self.session = session
        self.encoding = encoding

    def ban(self):
        """
        Bans the client's IP address from the server, without closing the currently
        open connection
        """

        self._server._banned.add(self.address)

    async def send(self, packet, close: bool = False):
        """High-level wrapper function around `AsyncAPY._send()`

           :param packet: A ``Packet`` object
           :type packet: class: ``Packet``
           :param close: If ``True``, the connection will be closed right after the packet is sent, it has to be set to ``False`` to take full advantages of packet propagation, defaults to ``False``
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
        await self._server._send(self._stream, data, self.session, close, from_client=True)

    async def close(self):
        """Closes the client connection
        """

        await self._stream.close()
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
    :param encoding: The payload desired encoding, it can either be ``json`` or ``ziproto``
    :type encoding: str
    :param sender: This parameter is meant to be initialized internally, and points to the ``Client`` object that sent the associated payload, defaults to ``None``
    :type sender: Union[Client, None], optional

    ``Packet`` objects behave mostly like Python dictionaries and can be iterated over, used with the ``in`` operator and support item access trough slicing.
    """

    def __init__(self, fields: Union[dict, str, bytes], encoding: str, sender: Union[Client, None] = None):
        """Object constructor"""

        self.sender = sender
        if not isinstance(encoding, str):
            raise ValueError("The encoding must be str!")
        if encoding not in ("json", "ziproto"):
            raise ValueError("The encoding must either be 'json' or 'ziproto'!")
        if isinstance(fields, dict):
            self.payload = json.dumps(fields)
        elif isinstance(fields, bytes):
            self.payload = json.dumps(json.loads(fields.decode("utf-8")))
        else:
            self.payload = json.dumps(json.loads(fields))
        self.length = len(self.payload)
        self.dict_payload = json.loads(self.payload)
        self.encoding = encoding

    async def stop_propagation(self):
        """Stops a packet from being propagated, see ``AsyncAPY.errors.StopPropagation``

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

    """
    An object meant for internal use. Every function is wrapped inside a ``Handler`` object together
    with its filters

    :param function: The asynchronous function, accepting two positional parameters (a ``Client`` object and a ``Packet`` object)
    :type function: function
    :param filters: A list of ``AsyncAPY.filters.Filter`` objects, defaults to ``None``
    :type filters: List[Filter]

    """

    def __init__(self, function: FunctionType, filters: List[Filter] = None):
        """Object constructor"""

        if not filters:
            filters = []
        self.filters = filters
        self.function = function

    def __repr__(self):
        """Returns ``repr(self)``

        :returns repr: A string representation of the object
        :rtype: str
        """

        return f"Handler({self.function}, {self.filters})"

    def check(self, client: Client, packet: Packet):
        """Iteratively calls the ``check()`` method on ``self.filters``, returns ``True`` if all filters return ``True``, ``False`` otherwise

           :param client: The client to check for
           :type client: class: ``Client``
           :param packet: The packet object to check for
           :type packet: class: ``Packet``
           :returns shall_pass: ``True`` if the handler matches all filters, ``False`` otherwise
           :rtype: bool

        """

        return all(filter(lambda f: f.check(client, packet), self.filters))

    async def call(self, *args):
        """Calls ``self.function`` asynchronously, passing ``*args`` as parameters"""

        return await self.function(*args)


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

    def ban_client(self, close: bool = False):
        """Bans the associated client' IP from the server

           :param close: If ``True``, the associated client connection will be closed after its IP gets banned, defaults to ``False``
        """

        self.client.ban()
        if close:
            self.close()

    def __repr__(self):
        return f"Session({str(self.session_id)})"

    def __str__(self):
        return str(self.session_id)

    def __hash__(self):
        return hash(self.session_id)

    def __eq__(self, other):
        if hash(self) == hash(other):
            return True
        return False
