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

import trio
import logging
import sys
import uuid
import json
from typing import Optional
from .objects import Handler, Group, Client, Packet, Session
from .errors import StopPropagation
import ziproto
import configparser
import time
# import ssl -> TODO Add TLS support soon, not a priority though


class AsyncAPY:
    """This class is the base class for the AsyncAPY framework.

        It implements AsyncAProto, the dedicated application protocol
        developed specifically for AsyncAPY. It also implements all the functionalities of the AsyncAPY framework

        :param addr: The address to which the server will bind to, defaults to ``'127.0.0.1'``
        :type addr: str, optional
        :param port: The port to which the server will bind to, defaults to 8081
        :type port: int, optional
        :param buf: The size of the TCP buffer, defaults to 1024
        :type buf: int, optional
        :param logging_level: The logging level for the ``logging`` module, defaults to 10 (`DEBUG`)
        :type logging_level: int, optional
        :param console_format: The output formatting string for the ``logging`` module, defaults to ``'[%(levelname)s] %(asctime)s %(message)s'``
        :type console_format: str, optional
        :param datefmt: A string for the logging module to format date and time, see the `logging` module for more info, defaults to ``'%d/%m/%Y %H:%M:%S %p'``
        :type datefmt: str, optional
        :param timeout: The timeout (in seconds) that the server will wait before considering a connection as dead and close it, defaults to 60
        :type timeout: int, optional
        :param header_size: The size of the ``Content-Length`` header can be customized. In an environment with small payloads a 2-byte header may be used to reduce overhead, defaults to 4
        :type header_size: int, optional
        :param byteorder: The order that the server will follow to read packets. It can either be ``'little'`` or ``'big'``, defaults to ``'big'``
        :type byteorder: str, optional
        :param encoding: The server's default encoding for payloads. It is used for V1 packets and it can either be ``'json'`` or ``'ziproto'``, defaults to ``'json'``
        :type encoding: str, optional
        :param config: The path to the configuration file, defaults to ``None`` (no config)
        :type config: str, None, optional
        :param cfg_parser:  If you want to use a custom configparser object, you can specify it here
        :type cfg_parser: class: ``configparser.ConfigParser()``
        :param session_limit: Defines how many concurrent sessions a client can instantiate, defaults to 0 (disabled)
        :type session_limit: int, optional
    """

    _banned = set()
    _handlers = []
    _levels = {0: "NOTSET", 10: "DEBUG", 20: "INFO", 30: "WARNING", 40: "ERROR", 50: "Critical"}
    _sessions = {}

    def __init__(self, addr: Optional[str] = "127.0.0.1", port: Optional[int] = 8081, buf: Optional[int] = 1024,
                 logging_level: int = logging.INFO,
                 console_format: Optional[str] = "[%(levelname)s] %(asctime)s %(message)s",
                 datefmt: Optional[str] = "%d/%m/%Y %H:%M:%S %p", timeout: Optional[int] = 60, header_size: int = 4,
                 byteorder: str = "big", encoding: str = "json", config: str or None = None, cfg_parser=None, session_limit: int = 0):
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
        if encoding not in ("json", "ziproto"):
            raise TypeError("encoding must either be 'json' or 'ziproto'!")
        if not isinstance(header_size, int):
            raise TypeError("header_size must be an integer!")
        if not isinstance(timeout, int):
            raise TypeError("timeout must be an integer!")
        if logging_level not in list(self._levels.keys()):
            raise TypeError("logging_level must either be 0, 10, 20, 30, 40 or 50!")
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
        self.header_size = header_size
        self.byteorder = byteorder
        self.encoding = encoding
        self.config = None
        self.session_limit = session_limit
        if config:
            self.config, self.parser = config, cfg_parser
            self.load_config()

    async def run_sync_task(self, sync_fn, *args, cancellable=False, limiter=None):
       """Convert a blocking operation into an async operation using a thread.

          This is just a shorthand for ``trio.to_thread.run_sync()``, check `trio's documentation <https://trio.readthedocs.io/en/stable/reference-core.html#trio.to_thread.run_sync>`_ to know more
       """

       return await trio.to_thread.run_sync(sync_fn, *args, cancellable=cancellable, limiter=limiter)


    def load_config(self):
        """Loads the configuration file and applies changes, this method is meant for internal use"""

        parser = self.parser if self.parser else configparser.ConfigParser()
        parser.read_file(open(self.config, "r"))
        configs = {"port", "addr", "header_size", "byteorder", "timeout", "datefmt", "console_format", "encoding", "buf", "logging_level"}
        opts = {}
        for config in configs:
            opts[config] = parser.get("AsyncAPY", config, fallback=None)
        for opt in opts:
            if opts[opt]:
                if opts[opt].isdigit():
                    opts[opt] = int(opts[opt])
                setattr(self, opt, opts[opt])

    # API RESPONSE HANDLERS #

    async def malformed_request(self, session_id: uuid.uuid4, stream: trio.SocketStream, encoding=None):
        """This is an internal method used to reply to a malformed packet/payload. Please note, that this function deals with raw objects, not with the high-level API objects used inside handlers

        :param session_id: A unique UUID, used to identify the current session. Currently the session_id is used to distinguish between different clients in the logging output
        :type session_id: class: ``uuid.uuid4``
        :param stream: The trio asynchronous socket associated to a client, can be found in ``Client._stream``
        :type stream: class: ``trio.SocketStream``
        """

        json_response = bytes(json.dumps({"status": "failure", "error": "ERR_REQUEST_MALFORMED"}), "u8")
        response_header = (len(json_response) + 2).to_bytes(self.header_size, self.byteorder)
        response_data = response_header + json_response
        await self.send_response(stream, response_data, session_id, from_client=False, encoding=encoding)

    # END OF RESPONSE HANDLERS SECTION #

    def add_handler(self, handler, filters=None, priority: int = 0):
        """Registers an handler, creating a ``Handler`` object and appending it to the ``self._handlers`` attribute

           :param handler: A function object, it can either be synchronous or asynchronous, but the former is not recommended
           :type handler: function
           :param filters: A list of filters object, to filter incoming packets, defaults to ``None``
           :type filters: Union[List[Filter], None]
           :param priority: Defines the execution priority inside a group of handlers, defaults to 0
        """

        self._handlers.append(Handler(handler, filters, priority))

    def handler_add(self, filters=None, priority: int = 0):
        """Decorator version of ``AsyncAPY.add_handler()``"""

        def decorator(func):
            self.add_handler(func, filters, priority)
        return decorator

    async def send_response(self, stream: trio.SocketStream, response_data: bytes, session_id, close: bool = True, encoding=None, from_client: bool = True):
        """
        This function sends the passed response to the client after elaboration

        :param stream: The trio asynchronous socket associated with the client, can be found at ``Client._stream``
        :type stream: class: ``trio.SocketStream``
        :param response_data: The payload, in JSON format (encoding into ZiProto is processed internally) already prepended with the ``Content-Length`` header
        :type response_data: bytes
        :param session_id: A unique UUID, used to identify the current session. Currently the session_id is used to distinguish between different clients in the console output
        :type session_id: class: ``uuid.uuid4``
        :param close: If ``True``, the client connection will be closed right after the payload has been sent, it must be set to ``False`` to take full advantage of packets propagation, defaults to ``True``
        :type close: bool, optional
        :param encoding: The encoding with which the packet should be encoded in, if ``None``, the server will fall back to ``self.encoding``. Other possible values are `'json'` or `'ziproto'`, defaults to ``None``
        :type encoding: Union[None, str], optional
        :param from_client: If ``True``, the payload will undergo no modifications and will be sent straight away: This parameter is needed to distinguish internal calls to the method from the Client API calls which behave differently, defaults to ``False``
        :type from_client: bool, optional
        :returns Union[bool, None]: Returns ``True`` on success, ``False`` on failure (e.g. the client disconnects abruptly) or ``None`` if the operation takes longer than ``self.timeout`` seconds
        :rtype: Union[bool, None]

        """

        if not from_client:
            if encoding is None:
               encoding = 0 if self.encoding == 'json' else 1
            if encoding == 1:
                payload = ziproto.encode(response_data[self.header_size:])
                header = (len(payload) + 2).to_bytes(self.header_size, self.byteorder) + (22).to_bytes(1, self.byteorder) + (1).to_bytes(1, self.byteorder)
                response_data = header + payload
            else:
                header = response_data[0:self.header_size] + (22).to_bytes(1, self.byteorder) + (0).to_bytes(1, self.byteorder)
                payload = json.loads(response_data[self.header_size:])
                response_data = header + json.dumps(payload).encode("utf-8")

        with trio.move_on_after(self.timeout) as cancel_scope:
            try:
                logging.debug(f"({session_id}) {{Response handler}} Sending response to client")
                await stream.send_all(response_data)
            except trio.BrokenResourceError:
                logging.info(f"({session_id}) {{Response Handler}} The connection was closed")
                await stream.aclose()
                return False
            except trio.ClosedResourceError:
                logging.info(f"({session_id}) {{Response Handler}} The connection was closed")
                await stream.aclose()
                return False
            except trio.BusyResourceError as busy:
                logging.error(f"({session_id}) {{Response Handler}} Client is sending too fast! Or is the server overloaded? -> {busy}")
                await stream.aclose()
                return False
        if cancel_scope.cancelled_caught:
            return None
        else:
            logging.debug(f"({session_id}) {{Response Handler}} Response sent")
            if close:
                await stream.aclose()
            return True

    async def rebuild_incomplete_stream(self, session_id: uuid.uuid4, stream: trio.SocketStream, raw_data: bytes):
        """
        This function gets called when a stream's length is smaller than ``self.header_size`` bytes, which
        is the minimum amount of data needed to parse an API call (The length header)

        :param session_id: A unique UUID, used to identify the current session. Currently the session_id is used to distinguish between different clients in the console output
        :type session_id: class: ``uuid.uuid4``
        :param stream: The trio asynchronous socket associated with the client
        :type stream: class : ``trio.SocketStream``
        :param raw_data: If some data was received already, it has to be passed here as paramater
        :type raw_data: bytes
        :returns: At least ``self.header_size`` bytes, and at most the whole packet, or None if the timeout expires or the connection gets closed
        :rtype: Union[bytes, None]
        """

        with trio.move_on_after(self.timeout) as cancel_scope:
            while len(raw_data) < self.header_size:
                try:
                    logging.debug(f"({session_id}) {{Stream rebuilder}} Requesting 1 more byte")
                    raw_data += await stream.receive_some(1)
                except trio.BrokenResourceError:
                    logging.info(f"({session_id}) {{Stream rebuilder}} The connection was closed")
                    await stream.aclose()
                    break
                except trio.ClosedResourceError:
                    logging.info(f"({session_id}) {{Stream rebuilder}} The connection was closed")
                    await stream.aclose()
                    break
        if cancel_scope.cancelled_caught:
            return None
        logging.debug(f"({session_id}) {{Stream rebuilder}} Stream is now {self.header_size} byte(s) long")
        return raw_data

    async def complete_stream(self, header, stream: trio.SocketStream, session_id: uuid.uuid4):
        """
        This functions completes the stream until the specified length is reached

        :param header: The ``Content-Length`` header, already decoded as an integer
        :type header: int
        :param stream: The trio asynchronous socket associated with the client
        :type stream: class : ``trio.SocketStream``
        :param session_id: A unique UUID, used to identify the current session. Currently the session_id is used to distinguish between different clients in the console output
        :type session_id: class: ``uuid.uuid4``
        :returns: The complete packet, or ``None`` if the timeout expires or the connection gets closed
        :rtype: Union[bytes, None]
        """

        stream_data = b""
        logging.debug(f"({session_id}) {{Stream completer}} Requesting {self.buf} more bytes until length {header}")
        with trio.move_on_after(self.timeout) as cancel_scope:
            while len(stream_data) < header:
                try:
                    stream_data += await stream.receive_some(max_bytes=self.buf)
                except trio.BrokenResourceError:
                    logging.info(f"({session_id}) {{Stream completer}} The connection was closed")
                    await stream.aclose()
                    break
                except trio.ClosedResourceError:
                    logging.info(f"({session_id}) {{Stream completer}} The connection was closed")
                    await stream.aclose()
                    break
                if not stream:
                    logging.info(f"({session_id}) {{Stream completer}} Stream has ended")
                    await stream.aclose()
                    break
        if cancel_scope.cancelled_caught:
            return None
        return stream_data

    async def decode_content(self, content, session_id: str, stream: trio.SocketStream, encoding=None):
        """Decodes the payload with the specified encoding, if any, or falls back to ``self.encoding``

           :param content: The byte-encoded payload
           :type content: bytes
           :param stream: The trio asynchronous socket associated with the client
           :type stream: class : ``trio.SocketStream``
           :param session_id: A unique UUID, used to identify the current session. Currently the session_id is used to distinguish between different clients in the console output
           :type session_id: class: ``uuid.uuid4``
           :param encoding: The encoding with which the packet should be encoded in, if ``None``, the server will fall back to ``self.encoding``, it can either be 1 for ziproto, 0 for json or ``None`` if the encoding is unknown, defaults to ``None``
           :type encoding: Union[None, int], optional
           :returns: The decoded payload
           :rtype: dict
        """

        data = ""
        if encoding is None:
            encoding = 0 if self.encoding == "json" else 1
        if encoding == 0:
            try:
                data = json.loads(content, encoding="utf-8")
            except json.decoder.JSONDecodeError as json_error:
                logging.error(f"({session_id}) {{Request Decoder}} Invalid JSON data, full exception -> {json_error}")
                await self.malformed_request(session_id, stream, encoding=0)
        else:
            try:
                data = ziproto.decode(content)
                if not isinstance(data, dict):
                    logging.error(f"({session_id}) {{Request Decoder}} Invalid ziproto encoded payload!")
                    await self.malformed_request(session_id, stream, encoding=1)
            except Exception as e:
                logging.error(f"({session_id}) {{Request Decoder}} Something went wrong while deserializing ZiProto -> {e}")
                await self.malformed_request(session_id, stream, encoding=1)

        return data

    async def parse_call(self, session_id: uuid.uuid4, request: bytes, stream: trio.SocketStream):

        """This function parses the API request and acts accordingly (e.g. decoding the payload and calling handlers)

           :param request: The byte-encoded payload
           :type request: bytes
           :param stream: The trio asynchronous socket associated with the client
           :type stream: class : ``trio.SocketStream``
           :param session_id: A unique UUID, used to identify the current session. Currently the session_id is used to distinguish between different clients in the console output
           :type session_id: class: ``uuid.uuid4``
        """

        req_valid = False
        protocol_version = request[0]
        content_encoding = request[1]
        if len(request) < 5:
            logging.error(f"({session_id}) {{API Parser}} Stream is too short, ignoring!")
            await stream.aclose()
            return None
        if protocol_version not in (11, 22):
            logging.error(f"({session_id}) {{API Parser}} Invalid Protocol-Version header in packet!")
            await stream.aclose()
            return None
        if content_encoding not in (0, 1):
            logging.error(f"({session_id}) {{API Parser}} Invalid Content-Encoding header in packet!")
            await stream.aclose()
            return None
        if protocol_version == 11 and content_encoding in (0, 1):
            logging.error(f"({session_id}) {{API Parser}} V1 packets shouldn't include a Content-Encoding header!")
            await self.malformed_request(session_id, stream, encoding=content_encoding)
        payload = await self.decode_content(request[2:], session_id, stream, encoding=content_encoding)
        logging.debug(f"({session_id}) {{API Parser}} Protocol-Version is {'V1' if protocol_version == 11 else 'V2'}, Content-Encoding is {'json' if not content_encoding else 'ziproto'}")
        try:
            client = Client(stream.socket.getsockname()[0], server=self, session=session_id, stream=stream, encoding=content_encoding)
        except OSError:
            logging.error(f"({session_id}) {{API Parser}} The connection was closed abruptly")
            await stream.aclose()
            return
        packet = Packet(payload, sender=client, encoding=content_encoding)
        session = Session(session_id, client, time.time())
        if not self._sessions.get(client.address, None):
            self._sessions[client.address] = [session, ]
        else:
            self._sessions[client.address].append(session)
        client.session = session
        if self.session_limit:
            if len(client.get_sessions()) >= self.session_limit:
                logging.warning(f"({session_id}) {{API Parser}} Maximum number of concurrent sessions reached! Closing the current one")
                if session in self._sessions[client.address]:
                    self._sessions[client.address].remove(session)
                await stream.aclose()
                return None
        if client.address not in self._banned:
            for handler in self._handlers:
                if isinstance(handler, Group):
                    if handler.check(client, packet):
                        req_valid = True
                        logging.debug(f"({session_id}) {{API Parser}} Done! Filters check passed, running group of functions")
                        for group_handler in handler:
                            logging.debug(f"({session_id}) {{API Parser}} Calling '{group_handler.function.__name__}'")
                            await group_handler.call(client, packet)
                            logging.debug(f"({session_id}) {{API Parser}} Execution of '{group_handler.function.__name__}' terminated")
                        if session in self._sessions[client.address]:
                            self._sessions[client.address].remove(session)
                else:
                    if handler.check(client, packet):
                        req_valid = True
                        logging.debug(f"({session_id}) {{API Parser}} Done! Filters check passed, calling '{handler.function.__name__}'")
                        await handler.call(client, packet)
                        logging.debug(
                                f"({session_id}) {{API Parser}} Execution of '{handler.function.__name__}' terminated")
        else:
            logging.debug(f"({session_id}) {{API Parser}} Whoops, that user is banned! Ignoring")
            if session in self._sessions[client.address]:
                self._sessions[client.address].remove(session)
            await stream.aclose()
            return None
        if not req_valid:
            logging.warning(f"({session_id}) {{API Parser}} No such handler for this request, closing the connection to spare memory!")
            await stream.aclose()
            if session in self._sessions[client.address]:
                self._sessions[client.address].remove(session)
            return None

    async def setup(self):
        """This function is called when the server is started.
           It has been thought to be overridden by a custom user-defined class to perform pre-startup operations
        """
        return

    async def shutdown(self):
        """This function is called when the server shuts down.
           It has been thought to be overridden by a custom user-defined class to perform post-shutdown operations.

           Note that this function is called only after a proper ``KeyboardInterrupt``, aka ``Ctrl+C``
           """
        return

    async def unban(self, ip: str):
        """Unbans an IP address from the server

           :param ip: The IP address to unban
           :type ip: str
        """

        if ip in self._banned:
            logging.debug(f"{{BanHammer}} '{ip}' unbanned!")
            self._banned.remove(ip)

    async def handle_client(self, stream: trio.SocketStream):
        """This function handles a single client connection, assigning it a unique UUID, and acts accordingly

           :param stream: The trio asynchronous socket associated with the client
           :type stream: class: ``trio.SocketStream``
        """
        session_id = uuid.uuid4()
        logging.info(f" {{Client handler}} New session started, UUID is {session_id}")
        with trio.move_on_after(self.timeout) as cancel_scope:
            while True:
                try:
                    raw_data = await stream.receive_some(max_bytes=self.buf)
                except trio.BrokenResourceError:
                    logging.info(f"({session_id}) {{Client handler}} The connection was closed")
                    await stream.aclose()
                    break
                except trio.ClosedResourceError:
                    logging.info(f"({session_id}) {{Client handler}} The connection was closed")
                    await stream.aclose()
                    break
                if not raw_data:
                    logging.info(f"({session_id}) {{Client handler}} Stream has ended")
                    await stream.aclose()
                    break
                if len(raw_data) < self.header_size:
                    logging.debug(f"({session_id}) {{Client handler}} Stream is shorter than header size, rebuilding")
                    stream_complete = await self.rebuild_incomplete_stream(session_id, stream, raw_data)
                    if stream_complete is None:
                        logging.error(f"({session_id}) {{Client handler}} The operation has timed out")
                        await stream.aclose()
                        break
                    else:
                        raw_data = stream_complete
                        header = int.from_bytes(raw_data[0:self.header_size], self.byteorder)
                        logging.debug(f"({session_id}) {{Client handler}} Expected stream length is {header}")
                        if len(raw_data) - self.header_size == header:
                            logging.debug(f"({session_id}) {{Client handler}} Stream completed, processing API call")
                            try:
                                await self.parse_call(session_id, raw_data, stream)
                            except StopPropagation:
                                logging.debug(f"({session_id}) {{Client Handler}} Uh oh! Propagation stopped, sorry next handlers")
                                await stream.aclose()
                                break
                        else:
                            logging.debug(
                                f"({session_id}) {{Client handler}} Fragmented stream detected, rebuilding in progress")
                            actual_data = await self.complete_stream(header, stream, session_id)
                            if actual_data is None:
                                logging.error(f"({session_id}) {{Client Handler}} The operation has timed out")
                                await stream.aclose()
                                break
                            logging.debug(f"({session_id}) {{Client handler}} Stream completed, processing API call")
                            try:
                                await self.parse_call(session_id, actual_data, stream)
                            except StopPropagation:
                                await stream.aclose()
                                logging.debug(f"({session_id}) {{Client Handler}} Uh oh! Propagation stopped, sorry next handlers")
                                break
                else:
                    header = int.from_bytes(raw_data[0:self.header_size], self.byteorder)
                    logging.debug(f"({session_id}) {{Client handler}} Expected stream length is {header}")
                    if len(raw_data[self.header_size:]) == header:
                        logging.debug(f"({session_id}) {{Client handler}} Stream complete, processing API call")
                        try:
                            await self.parse_call(session_id, raw_data[self.header_size:], stream)
                        except StopPropagation:
                            await stream.aclose()
                            logging.debug(f"({session_id}) {{Client Handler}} Uh oh! Propagation stopped, sorry next handlers")
                            break
                    else:
                        logging.debug(f"({session_id}) {{Client handler}} Fragmented stream detected, rebuilding")
                        stream_complete = await self.complete_stream(header, stream, session_id)
                        if stream_complete is None:
                            logging.debug(f"({session_id}) {{Client handler}} The operation has timed out")
                            await stream.aclose()
                            break
                        else:
                            raw_data += stream_complete
                            try:
                                await self.parse_call(session_id, raw_data[self.header_size:], stream)
                            except StopPropagation:
                                await stream.aclose()
                                logging.debug(f"({session_id}) {{Client Handler}} Uh oh! Propagation stopped, sorry next handlers")
                                break
        if cancel_scope.cancelled_caught:
            logging.error(f"({session_id}) {{Client handler}} The operation has timed out")
            if Session(session_id, None, None) in self._sessions.get(stream.getsockname()[0], None):
                self._sessions.remove(Session(session_id, None, None))

    async def serve_forever(self):
        """This function is the server's main loop
        """

        logging.basicConfig(datefmt=self.datefmt, format=self.console_format, level=self.logging_level)
        logging.info(" {API main} AsyncAPY server is starting up")
        logging.debug("{API main} Running setup function...")
        await self.setup()
        logging.debug(f"{{API main}} The buffer is set to {self.buf} bytes, logging is set to {self._levels[self.logging_level]}, \
encoding is {self.encoding}, header size is set to {self.header_size} bytes, byteorder is '{self.byteorder}', \
settings were loaded from '{self.config if self.config else 'attributes'}'")
        try:
            logging.info(f" {{API main}} Now serving  at {self.addr}:{self.port}")
            await trio.serve_tcp(self.handle_client, host=self.addr, port=self.port)
        except KeyboardInterrupt:
            logging.debug("{API main} Running shutdown function...")
            await self.shutdown()
            logging.info(" {API main} Ctrl + C detected, exiting")
            sys.exit(0)
        except PermissionError as perms_error:
            logging.error(f"{{API main}} Could not bind to chosen port, full error: {perms_error}")
            sys.exit("PORT_UNAVAILABLE")

    def start(self):
        """Starts the server, doing some magic to group handlers before calling ``self.serve_forever()``"""

        handlers = []
        grps = []
        for handler in self._handlers:
            comparison = handler.compare(self._handlers)
            if len(comparison) > 1:
                grps.append(Group(comparison))
            else:
                handlers.append(handler)
        for index, grp in enumerate(grps):
            if index != len(grps) - 1:
                if grp in grps[index:]:
                    grps.remove(grp)
        self._handlers = grps + handlers
        del grps, handlers
        trio.run(self.serve_forever) 
