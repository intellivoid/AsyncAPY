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

import trio
import logging
import sys
import uuid
import json
from typing import Optional
from .core import Handler, Client, Packet, Session
from .errors import StopPropagation
import ziproto
import configparser
import time
import socket
from collections import defaultdict
from types import FunctionType


class Server:
    """AsyncAPY server class

    :param addr: The address to which the server will bind to, defaults to ``'127.0.0.1'``
    :type addr: str, optional
    :param port: The port to which the server will bind to, defaults to 8081
    :type port: int, optional
    :param buf: The size of the TCP buffer, defaults to 1024
    :type buf: int, optional
    :param logging_level: The logging level for the ``logging`` module, defaults to 10 (`DEBUG`)
    :type logging_level: int, optional
    :param console_format: The output formatting string for the ``logging`` module,
    defaults to ``'[%(levelname)s] %(asctime)s %(message)s'``
    :type console_format: str, optional
    :param datefmt: A string for the logging module to format date and time, see the `logging` module for more info,
    defaults to ``'%d/%m/%Y %H:%M:%S %p'``
    :type datefmt: str, optional
    :param timeout: The timeout (in seconds) that the server will wait before considering a connection as dead and
    close it, defaults to 60
    :type timeout: int, optional
    :param header_size: The size of the ``Content-Length`` header can be customized.
    In an environment with small payloads a 2-byte header may be used to reduce overhead, defaults to 4
    :type header_size: int, optional
    :param byteorder: The order that the server will follow to read packets. It can either be ``'little'`` or ``'big'``,
    defaults to ``'big'``
    :type byteorder: str, optional
    :param config: The path to the configuration file, defaults to ``None`` (no config)
    :type config: str, None, optional
    :param cfg_parser:  If you want to use a custom configparser object, you can specify it here
    :type cfg_parser: class: ``configparser.ConfigParser()``
    :param session_limit: Defines how many concurrent sessions a client can instantiate, defaults to 0 (disabled)
    :type session_limit: int, optional
    """

    _handlers = {}
    _sessions = defaultdict(list)

    def __init__(
        self,
        addr: Optional[str] = "127.0.0.1",
        port: Optional[int] = 8081,
        buf: Optional[int] = 1024,
        logging_level: int = logging.INFO,
        console_format: Optional[str] = "[%(levelname)s] %(asctime)s %(message)s",
        datefmt: Optional[str] = "%d/%m/%Y %H:%M:%S %p",
        timeout: Optional[int] = 60,
        header_size: int = 4,
        byteorder: str = "big",
        config: str or None = None,
        cfg_parser=None,
        session_limit: int = 0,
    ):
        """Object constructor"""

        # Type checking

        if not isinstance(addr, str):
            raise TypeError("addr must be a string!")
        if not isinstance(port, int):
            raise TypeError("port must be an integer!")
        if not isinstance(buf, int):
            raise TypeError("buf must be an integer!")
        if byteorder not in ("big", "little"):
            raise TypeError("byteorder must either be 'little' or 'big'!")
        if not isinstance(header_size, int):
            raise TypeError("header_size must be an integer!")
        if not isinstance(timeout, int):
            raise TypeError("timeout must be an integer!")
        if not isinstance(console_format, str):
            raise TypeError("console_format must be a string!")
        if not isinstance(session_limit, int):
            raise TypeError("session_limit must be int!")
        self.addr = addr
        self.port = port
        self.buf = buf
        self.logging_level = logging_level
        self.console_format = console_format
        self.datefmt = datefmt
        self.timeout = timeout
        socket.setdefaulttimeout(
            self.timeout
        )  # Just to make sure the socket doesn't die
        self.header_size = header_size
        self.byteorder = byteorder
        self.config = None
        self.session_limit = session_limit
        if config:
            self.config, self.parser = config, cfg_parser
            self.load_config()

    # noinspection PyMethodMayBeStatic
    async def run_sync_task(self, sync_fn, *args, cancellable=False, limiter=None):
        """
        Convert a blocking operation into an async operation using a thread.

        This is just a shorthand for ``trio.to_thread.run_sync()``,  check `trio's documentation <https://trio.readthedocs.io/en/stable/reference-core.html#trio.to_thread.run_sync>`_
        to know more
        """

        return await trio.to_thread.run_sync(
            sync_fn, *args, cancellable=cancellable, limiter=limiter
        )

    def load_config(self):
        """
        Loads the configuration file and applies changes. This method is meant for internal use
        """

        parser = self.parser if self.parser else configparser.ConfigParser()
        with open(self.config) as config:
            parser.read_file(config)
        configs = (
            "port",
            "addr",
            "header_size",
            "byteorder",
            "timeout",
            "datefmt",
            "console_format",
            "encoding",
            "buf",
            "logging_level",
            "session_limit",
        )
        options = {}
        for config in configs:
            options[config] = parser.get("AsyncAPY", config, fallback=None)
        for option_name, option_value in options.items():
            if option_value:
                if option_value.isdigit():
                    option_value = int(option_value)
                setattr(self, option_name, option_value)

    # DEFAULT API RESPONSE HANDLERS #

    async def _malformed_request(
        self, session_id: uuid.uuid4, stream: trio.SocketStream, encoding=None
    ):
        """
        This is an internal method used to reply to a malformed packet/payload.
        Please note, that this function deals with raw objects, not with the high-level API objects used inside handlers

        :param session_id: A unique UUID, used to identify the current session
        :type session_id: class: ``uuid.uuid4``
        :param stream: The trio asynchronous socket associated to a client, can be found in ``Client._stream``
        :type stream: class: ``trio.SocketStream``
        """

        json_response = bytes(
            json.dumps({"status": "failure", "error": "ERR_REQUEST_MALFORMED"}), "u8"
        )
        response_header = (len(json_response) + 2).to_bytes(
            self.header_size, self.byteorder
        )
        response_data = response_header + json_response
        await self._send(
            stream, response_data, session_id, from_client=False, encoding=encoding
        )

    async def _invalid_header(
        self, session_id: uuid.uuid4, stream: trio.SocketStream, encoding=None
    ):
        """
        This is an internal method used to reply to a packet with a malformed header.
        Please note, that this function deals with raw objects, not with the high-level API objects used inside handlers

        :param session_id: A unique UUID, used to identify the current session
        :type session_id: class: ``uuid.uuid4``
        :param stream: The trio asynchronous socket associated to a client, can be found in ``Client._stream``
        :type stream: class: ``trio.SocketStream``
        """

        json_response = bytes(
            json.dumps({"status": "failure", "error": "ERR_HEADER_INVALID"}), "u8"
        )
        response_header = (len(json_response) + 2).to_bytes(
            self.header_size, self.byteorder
        )
        response_data = response_header + json_response
        await self._send(
            stream, response_data, session_id, from_client=False, encoding=encoding
        )

    async def _timed_out(
        self, session_id: uuid.uuid4, stream: trio.SocketStream, encoding=None
    ):
        """
        This is an internal method used to reply to a client that has timed out.
        Please note, that this function deals with raw objects, not with the high-level API objects used inside handlers

        :param session_id: A unique UUID, used to identify the current session
        :type session_id: class: ``uuid.uuid4``
        :param stream: The trio asynchronous socket associated to a client, can be found in ``Client._stream``
        :type stream: class: ``trio.SocketStream``
        """

        json_response = bytes(
            json.dumps({"status": "failure", "error": "ERR_TIMED_OUT"}), "u8"
        )
        response_header = (len(json_response) + 2).to_bytes(
            self.header_size, self.byteorder
        )
        response_data = response_header + json_response
        await self._send(
            stream, response_data, session_id, from_client=False, encoding=encoding
        )

    async def _session_limit_reached(
        self, session_id: uuid.uuid4, stream: trio.SocketStream, encoding=None
    ):
        """
        This is an internal method used to reply to a client that has reached the concurrent session limit.
        Please note, that this function deals with raw objects, not with the high-level API objects used inside handlers

        :param session_id: A unique UUID, used to identify the current session.
        :type session_id: class: ``uuid.uuid4``
        :param stream: The trio asynchronous socket associated to a client, can be found in ``Client._stream``
        :type stream: class: ``trio.SocketStream``
        """

        json_response = bytes(
            json.dumps({"status": "failure", "error": "ERR_SESSION_LIMIT_REACHED"}),
            "u8",
        )
        response_header = (len(json_response) + 2).to_bytes(
            self.header_size, self.byteorder
        )
        response_data = response_header + json_response
        await self._send(
            stream, response_data, session_id, from_client=False, encoding=encoding
        )

    # END OF RESPONSE HANDLERS SECTION #

    def register_handler(self, handler, *filters, **kwargs):
        """
        Registers an handler

        :param handler: A function object
        :type handler: FunctionType
        :param filters: Pass one or more filters to allow only a subset of client/packet pair to reach your handler
        :type filters: Filter, optional
        :param group: The group id, default to 0
        :type group: int, optional
        """

        group = kwargs.get("group", 0)
        if group in self._handlers:
            self._handlers[group].append(Handler(handler, list(filters)))
        else:
            self._handlers[group] = [
                Handler(handler, list(filters)),
            ]
        # This keeps our handlers sorted
        self._handlers = dict(sorted(self._handlers.items()))

    def add_handler(self, *filters, **kwargs):
        """
        Registers an handler, as a decorator. This does
        the same of ``AsyncAPY.register_handler()``, but in a
        cleaner way.

        :param handler: A function object
        :type handler: FunctionType
        :param filters: Pass one or more filters to allow only a subset of client/packet pair to reach your handler
        :type filters: Filter, optional
        :param group: The group id, default to 0
        :type group: int, optional
        """

        def wrapper(func):
            self.register_handler(func, *filters, **kwargs)
        return wrapper

    async def _send(
        self,
        stream: trio.SocketStream,
        response_data: bytes,
        session_id,
        close: bool = True,
        encoding=None,
        from_client: bool = True,
    ):
        """
        This function sends the passed response to the client

        :param stream: The trio asynchronous socket associated with the client, can be found at ``Client._stream``
        :type stream: class: ``trio.SocketStream``
        :param response_data: The payload, in JSON format (encoding into ZiProto is processed internally) already
        prepended with the ``Content-Length`` header
        :type response_data: bytes
        :param session_id: A unique UUID, used to identify the current session.
        :type session_id: class: ``uuid.uuid4``
        :param close: If ``True``, the client connection will be closed right after the payload has been sent,
        it must be set to ``False`` to take full advantage of packets propagation, defaults to ``True``
        :type close: bool, optional
        :param encoding: The encoding with which the packet should be encoded in, possible values are ``'json'`` or
        ``'ziproto'``
        :type encoding: str
        :param from_client: If ``True``, the payload will undergo no modifications and will be sent straight away:
        This parameter is needed to distinguish internal calls to the method from the Client API calls which behave
        differently, defaults to ``False``
        :type from_client: bool, optional
        :returns: Returns ``True`` on success, ``False`` on failure (e.g. the client disconnects abruptly)
        :rtype: bool

        """

        if not from_client:
            if encoding == 1:
                payload = ziproto.encode(json.loads(response_data[self.header_size:]))
                header = (
                    (len(payload) + 2).to_bytes(self.header_size, self.byteorder)
                    + (22).to_bytes(1, self.byteorder)
                    + (1).to_bytes(1, self.byteorder)
                )
                response_data = header + payload
            else:
                header = (
                    response_data[0:self.header_size]
                    + (22).to_bytes(1, self.byteorder)
                    + (0).to_bytes(1, self.byteorder)
                )
                payload = json.loads(response_data[self.header_size:])
                response_data = header + json.dumps(payload).encode("utf-8")
        try:
            logging.debug(
                f"({session_id}) {{Response Handler}} Sending response to client"
            )
            await stream.send_all(response_data)
        except trio.BrokenResourceError:
            logging.info(
                f"({session_id}) {{Response Handler}} The connection was closed abruptly"
            )
            await stream.aclose()
            return False
        except trio.ClosedResourceError:
            logging.info(
                f"({session_id}) {{Response Handler}} The connection was closed"
            )
            await stream.aclose()
            return False
        except trio.BusyResourceError as busy:
            logging.error(
                f"({session_id}) {{Response Handler}} Client is sending too fast! Or is the server overloaded? -> "
                f"{busy}"
            )
            await stream.aclose()
            return False
        else:
            logging.debug(f"({session_id}) {{Response Handler}} Response sent")
            if close:
                await stream.aclose()
            return True

    async def _rebuild_header(
        self, session_id: uuid.uuid4, stream: trio.SocketStream, raw_data: bytes
    ):
        """
        This function gets called when a stream's length is smaller than ``self.header_size`` bytes, which
        is the minimum amount of data needed to parse an API call (The length header)

        :param session_id: A unique UUID, used to identify the current session
        :type session_id: class: ``uuid.uuid4``
        :param stream: The trio asynchronous socket associated with the client
        :type stream: class : ``trio.SocketStream``
        :param raw_data: If some data was received already, it has to be passed here as paramater
        :type raw_data: bytes
        :returns: The rebuilt length header or None if the connection dies
        :rtype: Union[bytes, None]
        """

        while len(raw_data) < self.header_size:
            try:
                logging.debug(
                    f"({session_id}) {{Stream rebuilder}} Requesting 1 more byte"
                )
                raw_data += await stream.receive_some(1)
            except trio.BrokenResourceError:
                logging.info(
                    f"({session_id}) {{Stream rebuilder}} The connection was closed abruptly"
                )
                await stream.aclose()
                break
            except trio.ClosedResourceError:
                logging.info(
                    f"({session_id}) {{Stream rebuilder}} The connection was closed"
                )
                await stream.aclose()
                break
            except trio.BusyResourceError as busy:
                logging.error(
                    f"({session_id}) {{Response Handler}} Client is sending too fast! Or is the server overloaded? -> "
                    f"{busy}"
                )
                await stream.aclose()
                return
        logging.debug(
            f"({session_id}) {{Stream rebuilder}} Stream is now {self.header_size} byte(s) long"
        )
        return raw_data

    async def _complete_stream(
        self, header, stream: trio.SocketStream, session_id: uuid.uuid4
    ):
        """
        This functions completes the stream until the specified length is reached

        :param header: The ``Content-Length`` header, already decoded as an integer
        :type header: int
        :param stream: The trio asynchronous socket associated with the client
        :type stream: class : ``trio.SocketStream``
        :param session_id: A unique UUID, used to identify the current session
        :type session_id: class: ``uuid.uuid4``
        :returns: The complete packet, or ``None`` if the connection dies
        :rtype: Union[bytes, None]
        """

        stream_data = b""
        logging.debug(
            f"({session_id}) {{Rebuilder}} Requesting {self.buf} more bytes until length {header}"
        )
        while len(stream_data) < header:
            try:
                stream_data += await stream.receive_some(max_bytes=self.buf)
            except trio.BusyResourceError as busy:
                logging.error(
                    f"({session_id}) {{Rebuilder}} Client is sending too fast! Or is the server overloaded? -> {busy}"
                )
                await stream.aclose()
                return
            except trio.BrokenResourceError:
                logging.info(
                    f"({session_id}) {{Rebuilder}} The connection was closed abruptly"
                )
                await stream.aclose()
                break
            except trio.ClosedResourceError:
                logging.info(f"({session_id}) {{Rebuilder}} The connection was closed")
                await stream.aclose()
                break
            if not stream:
                logging.info(f"({session_id}) {{Rebuilder}} Stream has ended")
                await stream.aclose()
                break
        return stream_data

    async def _decode_payload(
        self, content, session_id: str, stream: trio.SocketStream, encoding=None
    ):
        """Decodes the payload with the specified encoding

        :param content: The byte-encoded payload
        :type content: bytes
        :param stream: The trio asynchronous socket associated with the client
        :type stream: class : ``trio.SocketStream``
        :param session_id: A unique UUID, used to identify the current session
        :type session_id: class: ``uuid.uuid4``
        :param encoding: The encoding with which the packet should be encoded in. Must be 1 for ziproto, 0 for json
        :type encoding: int
        :returns: The decoded payload
        :rtype: dict
        """

        data = ""
        if not encoding:
            try:
                data = json.loads(content)
            except json.decoder.JSONDecodeError as json_error:
                logging.error(
                    f"({session_id}) {{Request Decoder}} Invalid JSON data, full exception -> {json_error}"
                )
                await self._malformed_request(session_id, stream, encoding=0)
        else:
            try:
                data = ziproto.decode(content)
                if not isinstance(data, dict):
                    logging.error(
                        f"({session_id}) {{Request Decoder}} Invalid ziproto encoded payload!"
                    )
                    await self._malformed_request(session_id, stream, encoding=1)
            except Exception as e:
                logging.error(
                    f"({session_id}) {{Request Decoder}} Something went wrong while deserializing ZiProto -> {e}"
                )
                await self._malformed_request(session_id, stream, encoding=1)
        return data

    async def _set_session(self, session_id: uuid.uuid4, client: Client):
        """
        Internal method to perform session setup
        """

        self._sessions[client.address].append(Session(session_id, client, time.time()))
        client.session = self._sessions[client.address][-1]
        if self.session_limit:
            if len(client.get_sessions()) > self.session_limit:
                logging.warning(
                    f"({session_id}) {{Session Handler}} Maximum number of concurrent sessions reached! "
                    f"Closing the current one"
                )
                self._sessions[client.address].remove(client.session)
                await self._session_limit_reached(session_id, client._stream)
                await client.close()
                return
            return True
        return True

    async def _parse_packet(
        self, session_id: uuid.uuid4, raw: bytes, stream: trio.SocketStream
    ):
        """
        Internal method to parse a packet
        """

        if len(raw) < 5:
            logging.error(
                f"({session_id}) {{Packet Parser}} Stream is too short, ignoring!"
            )
            await self._malformed_request(session_id, stream)
            return None, None, None
        protocol_version, content_encoding = raw[0], raw[1]
        if protocol_version != 22:
            logging.error(
                f"({session_id}) {{Packet Parser}} Invalid Protocol-Version header in packet!"
            )
            await self._invalid_header(session_id, stream)
            return None, None, None
        if content_encoding not in (0, 1):
            logging.error(
                f"({session_id}) {{Packet Parser}} Invalid Content-Encoding header in packet!"
            )
            await self._invalid_header(session_id, stream)
            return None, None, None
        logging.debug(
            f"({session_id}) {{Packet Parser}} Protocol-Version is V2, Content-Encoding is "
            f"{'json' if not content_encoding else 'ziproto'}"
        )
        return (
            await self._decode_payload(
                raw[2:], session_id, stream, encoding=content_encoding
            ),
            content_encoding,
            protocol_version,
        )

    async def _dispatch(self, session_id: uuid.uuid4, client: Client, packet: Packet):
        """
        Dispatches packets and clients to handlers
        """

        for group, handlers in self._handlers.items():
            logging.debug(f"({session_id}) {{Dispatcher}} Checking group {group}")
            for handler in handlers:
                if handler.check(client, packet):
                    logging.debug(
                        f"({session_id}) {{Dispatcher}} Calling '{handler.function.__name__}' in group {group}"
                    )
                    await handler.call(client, packet)
                    break

    async def _close_session(self, client: Client):
        """
        Deletes a client session and closes the underlying client connection
        """

        if client.session in self._sessions[client.address]:
            self._sessions[client.address].remove(client.session)
        await client.close()

    async def _parse_call(
        self, session_id: uuid.uuid4, request: bytes, stream: trio.SocketStream
    ):
        """
        Parses the API request and acts accordingly (e.g. decoding the payload and calling handlers)

        :param request: The byte-encoded payload
        :type request: bytes
        :param stream: The trio asynchronous socket associated with the client
        :type stream: class : ``trio.SocketStream``
        :param session_id: A unique UUID, used to identify the current session.
        :type session_id: class: ``uuid.uuid4``
        """

        payload, encoding, protocol_version = await self._parse_packet(
            session_id, request, stream
        )
        if payload:
            encoding = "json" if not encoding else "ziproto"
            try:
                client = Client(
                    stream.socket.getsockname()[0],
                    server=self,
                    session=session_id,
                    stream=stream,
                    encoding=encoding,
                )
            except OSError:
                logging.warning(f"({session_id}) {{API Parser}} The client died")
            else:
                packet = Packet(payload, sender=client, encoding=encoding)
                if await self._set_session(session_id, client):
                    await self._dispatch(session_id, client, packet)
                await self._close_session(client)

    async def setup(self):
        """
        This method is called when the server is started and it has been thought to be overridden by a custom
        user defined class to perform pre-startup operations
        """

        return

    async def shutdown(self):
        """
        This method is called when the server shuts down and it has been thought to be overridden by a custom user
        defined class to perform post-shutdown operations

        Note that this method is called only after a proper ``KeyboardInterrupt`` exception is raised
        """

        return

    async def _handle_client(self, stream: trio.SocketStream):
        """
        Handles a single client connection

        :param stream: The trio asynchronous socket associated with the client
        :type stream: class: ``trio.SocketStream``
        """

        session_id = uuid.uuid4()
        try:
            logging.info(
                f"{{Client handler}} New session started, UUID is {session_id}"
            )
            with trio.move_on_after(self.timeout) as cancel_scope:
                while True:
                    try:
                        raw_data = await stream.receive_some(max_bytes=self.buf)
                    except trio.BrokenResourceError:
                        logging.info(
                            f"({session_id}) {{Client handler}} The connection was closed"
                        )
                        await stream.aclose()
                        break
                    except trio.ClosedResourceError:
                        logging.info(
                            f"({session_id}) {{Client handler}} The connection was closed"
                        )
                        await stream.aclose()
                        break
                    except trio.BusyResourceError as busy:
                        logging.error(
                            f"({session_id}) {{Client handler}} Client is sending too fast! Or is the server "
                            f"overloaded? -> {busy} "
                        )
                        await stream.aclose()
                        return
                    if not raw_data:
                        logging.info(
                            f"({session_id}) {{Client handler}} Stream has ended"
                        )
                        await stream.aclose()
                        break
                    if len(raw_data) < self.header_size:
                        logging.debug(
                            f"({session_id}) {{Client handler}} Stream is shorter than header size, rebuilding"
                        )
                        header = await self._rebuild_header(
                            session_id, stream, raw_data
                        )
                        if header:
                            header = int.from_bytes(header, self.byteorder)
                        else:
                            logging.warning(
                                f"({session_id}) {{Client handler}} The client did something nasty while attempting "
                                f"to complete the header! "
                            )
                    else:
                        header = int.from_bytes(
                            raw_data[: self.header_size], self.byteorder
                        )
                    logging.debug(
                        f"({session_id}) {{Client handler}} Expected stream length is {header}"
                    )
                    if len(raw_data) - self.header_size == header:
                        raw_data = raw_data[self.header_size:]
                    else:
                        logging.debug(
                            f"({session_id}) {{Client handler}} Fragmented stream detected, rebuilding"
                        )
                        raw_data = await self._complete_stream(
                            header, stream, session_id
                        )
                    logging.debug(
                        f"({session_id}) {{Client handler}} Stream complete, processing API call"
                    )
                    try:
                        await self._parse_call(session_id, raw_data, stream)
                    except StopPropagation:
                        await stream.aclose()
                        logging.debug(
                            f"({session_id}) {{Client handler}} Uh oh! Propagation stopped, sorry next handlers"
                        )
                        break
            if cancel_scope.cancelled_caught:
                logging.error(
                    f"({session_id}) {{Client handler}} The operation has timed out"
                )
                await self._timed_out(session_id, stream)
        except BaseException as error:
            logging.error(
                f"({session_id}) {{Client handler}} A fatal unhandled exception occurred -> "
                f"{type(error).__name__}: {error} "
            )

    async def _serve_forever(self):
        """
        The server's main loop: sets up logging, calls setup and
        shutdown handlers and serves on the given address and port
        """

        logging.basicConfig(
            datefmt=self.datefmt, format=self.console_format, level=self.logging_level
        )
        logging.info("{API main} AsyncAPY server is starting up")
        logging.debug("{API main} Running setup function...")
        await self.setup()
        try:
            logging.info(f"{{API main}} Now serving at {self.addr}:{self.port}")
            await trio.serve_tcp(self._handle_client, host=self.addr, port=self.port)
        except KeyboardInterrupt:
            logging.debug("{API main} Running shutdown function...")
            await self.shutdown()
            logging.info("{API main} Ctrl + C detected, exiting")
            sys.exit(0)
        except (PermissionError, OSError) as perms_error:
            logging.error(
                f"{{API main}} Could not bind to chosen port, full error: {perms_error}"
            )
            sys.exit("PORT_UNAVAILABLE")

    def start(self):
        """
        Starts serving asynchronously on ``self.addr:self.port``
        """

        trio.run(self._serve_forever)
