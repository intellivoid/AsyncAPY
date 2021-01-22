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
import ssl
import json
import socket
import ziproto
from typing import Union, Dict, Any, Optional, Tuple


class Client:
    """
    Basic Python implementation of an AsyncAProto client

    :param byteorder: The packets' byteorder, can either be ``"big"`` or ``"little"``. Defaults to ``"big"`` (standard)
    :type byteorder: str
    :param header_size: The size in bytes of the ``Content-Length`` header for packets, defaults to 4 (standard)
    :type header_size: int
    :param tls: Instructs the client to use the Transport Layer Security encryption standard for the underlying TCP
    connection, defaults to ``True``. Recommended for production servers
    :type tls: optional, bool
    :param encoding: The session's payload type, used to encode and decode packets. Defaults to ``"json"``,
    but another valid option is ``"ziproto"`` (a custom encoding which is more compact, but less flexible and
    not human-readable, recommended for when the information is not meant to be seen by the general public)
    :param timeout: The max. duration in seconds to read the socket before timing out, defaults to 60
    :type timeout: int, optional
    """

    def __init__(
        self,
        byteorder: Optional[str] = "big",
        header_size: Optional[int] = 4,
        tls: Optional[bool] = True,
        encoding: Optional[str] = "json",
        timeout: Optional[int] = 60,
    ):
        """
        Object constructor
        """

        if byteorder not in ("big", "little"):
            raise ValueError("byteorder must either be 'big' or 'little'!")
        if not isinstance(header_size, int):
            raise ValueError("header_size must be an integer!")
        self.byteorder: str = byteorder
        self.header_size: int = header_size
        self.sock: Optional[socket.socket] = None
        self.tls: bool = tls
        self.encoding: str = encoding
        self.timeout: int = timeout

    def connect(self, hostname: str, port: int):
        """
        Connects to the given hostname and port

        :param hostname: The address of the server to connect to
        :type hostname: str
        :param port: The port of the server to connect to
        :type port: int
        """

        if not isinstance(hostname, str):
            raise ValueError("address must be string!")
        if not isinstance(port, int):
            raise ValueError("port must be an integer!")
        self.sock = (
            socket.socket() if not self.tls else ssl.wrap_socket(socket.socket())
        )
        self.sock.settimeout(self.timeout)
        self.sock.connect((hostname, port))

    def disconnect(self):
        """
        Closes the underlying TCP socket. No further
        action is needed client-side as the server
        will automatically drop its end of the pipe when
        it notices that the client is gone
        """

        self.sock.close()

    def send(self, payload: Union[str, Dict[Any, Any]]):
        """
        Sends the given payload across the underlying
        TCP connection as a proper AsyncAproto packet

        :param payload: The payload to send to the server. Pass either a dictionary object or a valid JSON string
        :type payload: dict or str, optional
        """

        if isinstance(payload, dict) and self.encoding == "json":
            payload: bytes = json.dumps(payload).encode()
        elif isinstance(payload, str) and self.encoding == "ziproto":
            payload: bytes = ziproto.encode(json.loads(payload))
        elif self.encoding == "ziproto":
            payload: bytes = ziproto.encode(payload)
        content_length = (len(payload) + 2).to_bytes(self.header_size, self.byteorder)
        content_encoding = (
            (0).to_bytes(1, "big")
            if self.encoding == "json"
            else (1).to_bytes(1, "big")
        )
        protocol_version = (22).to_bytes(1, "big")
        headers = content_length + protocol_version + content_encoding
        packet = headers + payload
        self.sock.sendall(packet)

    def _rebuild_stream(self, size: int) -> bytes:
        """
        Internal method to rebuild a fragmented
        packet stream up to a given size

        :param size: The amount of bytes to be returned
        :type size: int
        :returns: The required amount of data, as bytes
        :rtype: bytes
        """

        data = b""
        while len(data) < size:
            data += self.sock.recv(size)
            size -= len(data)
        return data

    # noinspection PyMethodMayBeStatic
    def _split_packet(self, packet: bytes) -> Tuple:
        """
        Splits a raw packet into its headers
        and payload
        """

        return (int.from_bytes(packet[0:self.header_size], self.byteorder),
                int.from_bytes(packet[self.header_size:self.header_size + 1], self.byteorder),
                int.from_bytes(packet[self.header_size + 1:self.header_size + 2], self.byteorder),
                packet[self.header_size + 2:]
                )

    def receive(self) -> Dict[Any, Any]:
        """
        Receives a complete AsyncAproto packet and returns
        the decoded payload
        """

        data = self.receive_raw()
        payload = self._split_packet(data)[-1]
        print(self._split_packet(data))
        if self.encoding == "json":
            return json.loads(payload.decode())
        else:
            return ziproto.decode(payload)

    def receive_raw(self) -> bytes:
        """
        Reads the internal socket until an
        entire AsyncAproto packet is complete
        and returns the raw packet (including
        headers). An empty byte string is returned
        if the socket gets closed abruptly
        """

        data = b""
        while len(data) < self.header_size:
            # We receive at most up to our
            # headers' size so we can know
            # how to proceed later
            raw = self.sock.recv(4)
            if not raw:
                # Socket has been closed
                return b""
            else:
                data += raw
        # Once we received our 4-byte content-length header, we
        # just rebuild the packet up to said size and let the TCP
        # buffer handle any truncated data that may come after the
        # packet
        content_length = int.from_bytes(data[0 : self.header_size], self.byteorder)
        data += self._rebuild_stream(content_length)
        return data
