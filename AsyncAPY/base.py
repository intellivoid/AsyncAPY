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

import trio
import logging
import sys
import uuid
import json
from typing import Optional
from .objects import Handler, Group, Client, Packet
from .errors import StopPropagation
import ziproto
import configparser
# import ssl -> TODO Add TLS support soon, not a priority though


class AsyncAPY:
    """This class is the base class for the AsyncAPython framework.

        It implements AsyncAProto, the dedicated application protocol
        developed specifically for AsyncAPY. It also implements all the functionalities of the AsyncAPY framework

        :param addr: The address to which the server will bind to, defaults to `'127.0.0.1'`
        :type addr: str, optional
        :param port: The port to which the server will bind to, defaults to 8081
        :type port: int, optional
        :param buf: The size of the TCP buffer, defaults to 1024
        :type buf: int, optional
        :param logging_level: The logging level for the `logging` module, defaults to 10 (`DEBUG`)
        :type logging_level: int, optional
        :param console_format: The output formatting string for the `logging` module, defaults to `'[%(levelname)s] %(asctime)s %(message)s'`
        :type console_format: str, optional
        :param datefmt: A string for the logging module to format date and time, see the `logging` module for more info, defaults to `'%d/%m/%Y %H:%M:%S %p'`
        :type datefmt: str, optional
        :param timeout: The timeout (in seconds) that the server will wait before considering a connection as dead and close it, defaults to 60
        :type timeout: int, optional
        :param header_size: The size of the `Content-Length` header can be customized. In an environment with small payloads a 2-byte header may be used to reduce overhead, defaults to 4
        :type header_size: int, optional
        :param byteorder: The order that the server will follow to read packets. It can either be `'little'` or `'big'`, defaults to `'big'`
        :type byteorder: str, optional
        :param encoding: The server's default encoding for payloads. It is used for V1 packets and it can either be `'json'` or `'ziproto'`, defaults to `'json'`
        :type encoding: str, optional
        :param config: The path to the configuration file
        :type config: str, None, optional
        :param cfg_parser:  If you want to use a custom configparser object, you can specify it here
        :type cfg_parser: class: `configparser.ConfigParser()`
    """

    banned = set()
    handlers = []
    levels = {0: "NOTSET", 10: "DEBUG", 20: "INFO", 30: "WARNING", 40: "ERROR", 50: "Critical"}

    def __init__(self, addr: Optional[str] = "127.0.0.1", port: Optional[int] = 8081, buf: Optional[int] = 1024,
                 logging_level: int = logging.INFO,
                 console_format: Optional[str] = "[%(levelname)s] %(asctime)s %(message)s",
                 datefmt: Optional[str] = "%d/%m/%Y %H:%M:%S %p", timeout: Optional[int] = 60, header_size: int = 4,
                 byteorder: str = "big", encoding: str = "json", config: str or None = None, cfg_parser=None):
        """Object constructor"""

        # Type checking
        if not isinstance(addr, str):
            raise ValueError("addr must be a string!")
        if not isinstance(port, int):
            raise ValueError("port must be an integer!")
        if not isinstance(buf, int):
            raise ValueError("buf must be an integer!")
        if byteorder not in ("big", "little"):
            raise ValueError("byteorder must either be 'little' or 'big'!")
        if encoding not in ("json", "ziproto"):
            raise ValueError("encoding must either be 'json' or 'ziproto'!")
        if not isinstance(header_size, int):
            raise ValueError("header_size must be an integer!")
        if not isinstance(timeout, int):
            raise ValueError("timeout must be an integer!")
        if logging_level not in list(self.levels.keys()):
            raise ValueError("logging_level must either be 0, 10, 20, 30, 40 or 50!")
        if not isinstance(console_format, str):
            raise ValueError("console_format must be a string!")
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
        if config:
            self.config, self.parser = config, cfg_parser
            self.load_config()

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

    async def malformed_request(self, session_id: uuid.uuid4, stream: trio.SocketStream):
        """This is an internal method used to reply to a malformed packet/payload. Please note, that this function deals with raw objects, not with the high-level API objects used inside handlers

        :param session_id: A unique UUID, used to identify the current session. Currently the session_id is used to distinguish between different clients in the logging output
        :type session_id: class: `uuid.uuid4`
        :param stream: The trio asynchronous socket associated to a client, can be found in `Client._stream`
        :type stream: class: `trio.SocketStream`
        """

        json_response = bytes(json.dumps({"status": "failure", "error": "ERR_REQUEST_MALFORMED"}), "u8")
        response_header = len(json_response).to_bytes(self.header_size, self.byteorder)
        response_data = response_header + json_response
        await self.send_response(stream, response_data, session_id)

    # END OF RESPONSE HANDLERS SECTION #

    def add_handler(self, handler, filters=None, priority: int = 0):
        """Registers an handler, creating a `Handler` object and appending it to the `self.handlers` attribute

           :param handler: A function object, it can either be synchronous or asynchronous, but the former is not recommended
           :type handler: function
           :param filters: A list of filters object, to filter incoming packets, defaults to `None`
           :type filters: Union[List[Filter], None]
           :param priority: Defines the execution priority inside a group of handlers, defaults to 0
        """

        self.handlers.append(Handler(handler, filters, priority))

    def handler_add(self, filters=None, priority: int = 0):
        """Decorator version of `AsyncAPY.add_handler()`"""

        def decorator(func):
            self.add_handler(func, filters, priority)
        return decorator

    async def send_response(self, stream: trio.SocketStream, response_data: bytes, session_id, close: bool = True, encoding=None):
        """
        This function sends the passed response to the client after elaboration

        :param stream: The trio asynchronous socket associated with the client, can be found at `Client._stream`
        :type stream: class: `trio.SocketStream`
        :param response_data: The payload, in JSON format (encoding into ZiProto is processed internally) already prepended with the `Content-Length` header
        :type response_data: bytes
        :param session_id: A unique UUID, used to identify the current session. Currently the session_id is used to distinguish between different clients in the console output
        :type session_id: class: `uuid.uuid4`
        :param close: If `True`, the client connection will be closed right after the payload has been sent, it must be set to `False` to take full advantage of packets propagation, defaults to `True`
        :type close: bool, optional
        :param encoding: The encoding with which the packet should be encoded in, if `None`, the server will fall back to `self.encoding`. Other possible values are `'json'` or `'ziproto'`, defaults to `None`
        :type encoding: Union[None, str], optional
        :returns Union[bool, None]: Returns `True` on success, `False` on failure (e.g. the client disconnects abruptly) or `None` if the operation takes longer than `self.timeout` seconds
        :rtype Union[True, False, None]
        """

        if encoding is None:
            encoding = self.encoding
        if encoding == 1:
            header = response_data[0:self.header_size] + (22).to_bytes(1, self.byteorder) + (1).to_bytes(1, self.byteorder)
            payload = ziproto.encode(json.loads(response_data[self.header_size:]))
            response_data = header + payload
        else:
            header = response_data[0:self.header_size] + (22).to_bytes(1, self.byteorder) + (0).to_bytes(1, self.byteorder)
            payload = json.loads(response_data[self.header_size:])
            response_data = header + json.dumps(payload).encode()

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
        if cancel_scope.cancelled_caught:
            return None
        else:
            logging.debug(f"({session_id}) {{Response Handler}} Response sent")
            if close:
                await stream.aclose()
            return True

    async def rebuild_incomplete_stream(self, session_id: uuid.uuid4, stream: trio.SocketStream, raw_data: bytes):
        """
        This function gets called when a stream's length is smaller than self.header_size bytes, which
        is the minimum amount of data needed to parse an API call (The length header)

        :param session_id: A unique UUID, used to identify the current session. Currently the session_id is used to distinguish between different clients in the console output
        :type session_id: class: `uuid.uuid4`
        :param stream: The trio asynchronous socket associated with the client
        :type stream: class : `trio.SocketStream`
        :param raw_data: If some data was received already, it has to be passed here as paramater
        :type raw_data: bytes
        :returns: At least `self.header_size` bytes, and at most the whole packet, or None if the timeout expires or the connection gets closed
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

        :param header: The `Content-Length` header, already decoded as an integer
        :type header: int
        :param stream: The trio asynchronous socket associated with the client
        :type stream: class : `trio.SocketStream`
        :param session_id: A unique UUID, used to identify the current session. Currently the session_id is used to distinguish between different clients in the console output
        :type session_id: class: `uuid.uuid4`
        :returns: The complete packet, or None if the timeout expires or the connection gets closed
        :rtype: Union[bytes, None]
        """

        stream_data = b""
        with trio.move_on_after(self.timeout) as cancel_scope:
            while len(stream_data) < header:
                try:
                    logging.debug(
                        f"({session_id}) {{Stream completer}} Requesting {self.buf} more bytes until length {header}")
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
        """Decodes the payload with the specified encoding, if any, or falls back to the `self.encoding`

           :param content: The byte-encoded payload
           :type content: bytes
           :param stream: The trio asynchronous socket associated with the client
           :type stream: class : `trio.SocketStream`
           :param session_id: A unique UUID, used to identify the current session. Currently the session_id is used to distinguish between different clients in the console output
           :type session_id: class: `uuid.uuid4`
           :param encoding: The encoding with which the packet should be encoded in, if `None`, the server will fall back to `self.encoding`, it can either be 1 for ziproto, 0 for json or `None` if the encoding is unknown, defaults to `None`
           :type encoding: Union[None, int], optional
           :returns: The decoded payload
           :rtype: dict
        """

        if encoding is None:
            encoding = 0 if self.encoding == "json" else 1
        if encoding == 0:
            try:
                data = json.loads(content, encoding="utf-8")
            except json.decoder.JSONDecodeError as json_error:
                logging.error(f"({session_id}) {{Request Decoder}} Invalid JSON data, full exception -> {json_error}")
                await self.malformed_request(session_id, stream)
        else:
            try:
                data = ziproto.decode(content)
            except Exception as e:
                logging.error(f"({session_id}) {{Request Decoder}} Something went wrong while deserializing ZiProto -> {e}")
                await self.malformed_request(session_id, stream)
        return data

    async def parse_call(self, session_id: uuid.uuid4, request: bytes, stream: trio.SocketStream):

        """This function parses the API request and acts accordingly

           :param request: The byte-encoded payload
           :type request: bytes
           :param stream: The trio asynchronous socket associated with the client
           :type stream: class : `trio.SocketStream`
           :param session_id: A unique UUID, used to identify the current session. Currently the session_id is used to distinguish between different clients in the console output
           :type session_id: class: `uuid.uuid4`
        """

        if len(request) < self.header_size + 3:  # Content-Length + Protocol-Version + Content-Encoding + 1 byte-payload
            logging.error(f"({session_id}) {{API Parser}} Request is too short! Ignoring")
            await stream.aclose()
            return None
        protocol_version = request[0]
        content_encoding = request[1]
        if protocol_version not in (11, 22):
            logging.error(f"({session_id}) {{API Parser}} Invalid Protocol-Version header in packet!")
            await stream.aclose()
            return None
        if content_encoding not in (0, 1):
            logging.error(f"({session_id}) {{API Parser}} Invalid Content-Encoding header in packet!")
            await stream.aclose()
            return None
        payload = await self.decode_content(request[2:], session_id, stream, encoding=content_encoding)
        logging.debug(f"({session_id}) {{API Parser}} Protocol-Version is {'V1' if protocol_version == 11 else 'V2'}, Content-Encoding is {'json' if not content_encoding else 'ziproto'}")
        if protocol_version == 11 and content_encoding in (0, 1):
            logging.warning(f"({session_id}) {{API Parser}} V1 packets shouldn't include a Content-Encoding header!")
            await stream.aclose()
        else:
            client = Client(stream.socket.getsockname()[0], server=self, session=session_id, stream=stream)
            packet = Packet(payload, sender=client, encoding="json" if not content_encoding else "ziproto")
            if client.address not in self.banned:
                for handler in self.handlers:
                    if isinstance(handler, Group):
                        if handler.check(client, packet):
                            logging.debug(f"({session_id}) {{API Parser}} Done! Filters check passed, running group of functions")
                            for group_handler in handler:
                                logging.debug(f"({session_id}) {{API Parser}} Calling '{group_handler.function.__name__}'")
                                await group_handler.call(client, packet)
                                logging.debug(f"({session_id}) {{API Parser}} Execution of '{group_handler.function.__name__}' terminated")
                    else:
                        if handler.check(client, packet):
                            logging.debug(f"({session_id}) {{API Parser}} Done! Filters check passed, calling '{handler.function.__name__}'")
                            await handler.call(client, packet)
                            logging.debug(
                                f"({session_id}) {{API Parser}} Execution of '{handler.function.__name__}' terminated")
            else:
                logging.debug(f"({session_id}) {{API Parser}} Whoops, that user is banned! Ignoring")
                await stream.aclose()

    async def setup(self):
        """This function is called when the server is started"""

        return

    async def shutdown(self):
        """This function is called when the server shuts down"""
        return

    async def unban(self, ip: str):
        """Unbans an IP address from the server

           :param ip: The IP address to unban
           :type ip: str
        """

        if ip in self.banned:
            logging.debug(f"{{BanHammer}} '{ip}' unbanned!")
            self.banned.remove(ip)

    async def handle_client(self, stream: trio.SocketStream):
        """
        This function handles a single client connection:

        - It assigns a unique ID to each client session
        - It listens on the asynchronous socket and acts accordingly
        e.g. incomplete streams or abrupt disconnection
        - It handles timeouts if the client hangs for some reason

        :param stream: The trio asynchronous socket associated with the client
        :type stream: class : `trio.SocketStream`

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
                                logging.debug("({session_id}) {{Client Handler}} Uh oh! Propagation stopped, sorry next handlers")
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
                                await self.parse_call(session_id, raw_data, stream)
                            except StopPropagation:
                                await stream.aclose()
                                logging.debug("({session_id}) {{Client Handler}} Uh oh! Propagation stopped, sorry next handlers")
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
                            logging.debug("({session_id}) {{Client Handler}} Uh oh! Propagation stopped, sorry next handlers")
                            break
                    else:
                        logging.debug(f"({session_id}) {{Client handler}} Fragmented stream detected, rebuilding")
                        stream_complete = await self.complete_stream(header - len(raw_data[self.header_size:]), stream,
                                                                     session_id)
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
                                logging.debug("({session_id}) {{Client Handler}} Uh oh! Propagation stopped, sorry next handlers")
                                break
        if cancel_scope.cancelled_caught:
            logging.error(f"({session_id}) {{Client handler}} The operation has timed out")

    async def serve_forever(self):
        """
        This function is the server's main loop, what it does is:
        - Starts to serve the asynchronous TCP socket
        - Waits forever for clients to connect and redirect them to
        the handle_client() function defined above
        """

        logging.basicConfig(datefmt=self.datefmt, format=self.console_format, level=self.logging_level)
        logging.info(" {API main} AsyncAPY server is starting up")
        logging.debug("{API main} Running setup function...")
        await self.setup()
        logging.debug(f"{{API main}} The buffer is set to {self.buf} bytes, logging is set to {self.levels[self.logging_level]}, \
encoding is {self.encoding}, header size is set to {self.header_size} bytes, byteorder is '{self.byteorder}', \
settings were loaded from '{self.config}'")
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
        """Starts the server, doing some magic to group handlers before calling `self.serve_forever()`"""

        new = []
        for handler in self.handlers:
            comparison, self.handlers = handler.compare(self.handlers, self.handlers)
            if len(comparison) > 1:
                new.append(Group(comparison))
        for handler in self.handlers:
            new.append(handler)
        self.handlers = new
        del new
        trio.run(self.serve_forever)
