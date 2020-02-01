import trio
import logging
import sys
import uuid
import json
from typing import Optional
from .objects import Handler, Group, Client, Packet
from .errors import StopPropagation
import ziproto


class AsyncAPY:
    """This class is the base class for the AsyncAPython framework.

        It implements a simple but reliable protocol over TCP with JSON requests,
        handling the hassle of sockets and other protocol-related operations
        at a low level and asynchronously, exposing a high level and easy
        to use API only.

        Also, things such as TCP slow start and stream fragmentation are also
        handled by the AsyncAPython protocol, which grants that every request
        is separated from another one thanks to a simple header system
    """

    banned = set()
    handlers = {}
    groups = {}

    def __init__(self, addr: Optional[str] = "127.0.0.1", port: Optional[int] = 8081, buf: Optional[int] = 1024,
                 logging_level: int = logging.INFO,
                 console_format: Optional[str] = "[%(levelname)s] %(asctime)s %(message)s",
                 datefmt: Optional[str] = "%d/%m/%Y %H:%M:%S %p", timeout: Optional[int] = 60, header_size: int = 2,
                 byteorder: str = "big", proto: str = "json", workers: int = 4):
        """Initializes server"""

        self.addr = addr
        self.port = port
        self.buf = buf
        self.logging_level = logging_level
        self.console_format = console_format
        self.datefmt = datefmt
        self.timeout = timeout
        self.header_size = header_size
        self.byteorder = byteorder
        if proto not in ("json", "ziproto"):
            raise ValueError("Protocol must either be 'json' or 'ziproto'!")
        self.proto = proto
        self.workers = trio.CapacityLimiter(workers)

    # API RESPONSE HANDLERS #

    async def malformed_request(self, session_id: uuid.uuid4, stream: trio.SocketStream):
        json_response = bytes(json.dumps({"status": "failure", "error": "ERR_REQUEST_MALFORMED"}), "u8")
        response_header = len(json_response).to_bytes(self.header_size, self.byteorder)
        response_data = response_header + json_response
        await self.send_response(stream, response_data, session_id)

    async def invalid_json_request(self, session_id: uuid.uuid4, stream: trio.SocketStream):
        json_response = bytes(json.dumps({"status": "failure", "error": "ERR_REQUEST_INVALID"}), "u8")
        response_header = len(json_response).to_bytes(self.header_size, self.byteorder)
        response_data = response_header + json_response
        await self.send_response(stream, response_data, session_id)

    async def missing_field(self, session_id: uuid.uuid4, stream: trio.SocketStream, missing_field: str):
        missing_field = missing_field.upper().strip("'")
        json_response = bytes(json.dumps({"status": "failure", "error": f"ERR_MISSING_{missing_field}_FIELD"}), "u8")
        response_header = len(json_response).to_bytes(self.header_size, self.byteorder)
        response_data = response_header + json_response
        await self.send_response(stream, response_data, session_id)

    # END OF RESPONSE HANDLERS SECTION #

    def add_handler(self, handler, name, filters=None, priority: int = 0):
        self.handlers[hash(handler.__name__)] = Handler(handler, name, filters, priority)

    def remove_handler(self, name):
        if self.handlers.get(name, None):
            del self.handlers[name]
            return True

    def handler_add(self, name, filters=None, priority: int = 0):
        def decorator(func):
            self.add_handler(func, name, filters, priority)

        return decorator

    async def send_response(self, stream: trio.SocketStream, response_data: bytes, session_id):
        """
        This function sends the JSON response to the client after elaboration, returns False on failure
        or None if the timeout (generally 60 seconds) expires
        """

        if self.proto == "ziproto":
            header = response_data[0:self.header_size]
            payload = ziproto.encode(json.loads(response_data[self.header_size:]))
            response_data = header + payload
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
            return True

    async def rebuild_incomplete_stream(self, session_id: uuid.uuid4, stream: trio.SocketStream, raw_data):
        """
        This function gets called when a stream's length is smaller than self.header_size bytes, which
        is the minimum amount of data needed to parse an API call (The length header)
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

    async def parse_call(self, session_id: uuid.uuid4, request: bytes, stream: trio.SocketStream):

        """This function parses the API request and acts accordingly"""

        if self.proto == "json":
            try:
                data = json.loads(request, encoding="utf-8")
            except json.decoder.JSONDecodeError as json_error:
                logging.error(f"({session_id}) {{API Parser}} Invalid JSON data, full exception -> {json_error}")
                await self.malformed_request(session_id, stream)
            else:
                request_type = data.get("request_type", None)
                if not request_type:
                    logging.error(f"({session_id}) {{API Parser}} Missing request_type field in JSON request")
                    await self.missing_field(session_id, stream, "request_type")
                else:
                    to_call = self.handlers.get(request_type, None)
        else:
            try:
                data = ziproto.decode(request)
            except Exception as e:
                logging.error(f"({session_id}) {{API Parser}} Something went wrong while deserializing ZiProto -> {e}")
                await self.malformed_request(session_id, stream)
            else:
                request_type = data.get("request_type", None)
                if not request_type:
                    logging.error(f"({session_id}) Missing request_type field in ZiProto request!")
                    await self.missing_field(session_id, stream, "request_type")
                else:
                    to_call = self.handlers.get(request_type, None)
                handle = []
                if to_call:
                    client = Client(stream.socket.getsockname()[0], self, stream, session_id)
                    if client.address not in self.banned:
                        packet = Packet(data, client)
                        if isinstance(to_call, Group):
                            for handler in to_call:
                                if handler.filters:
                                    for fil in handler.filters:
                                        handle.append(fil.check(client, packet))
                                if all(handle):
                                    handle = []
                                    await handler.call(client, packet)
                                else:
                                    logging.info(f"({session_id}) {{API Parser}} Filters check failed, request won't be handled")
                                    await client.close()
                                    await packet.stop_propagation()
                        else:
                            if to_call.filters:
                                for fil in to_call.filters:
                                    handle.append(fil.check(client, packet))
                            if all(handle):
                                handle = []
                                await to_call.call(client, packet)
                                await client.close()
                            else:
                                logging.info(f"({session_id}) {{API Parser}} Filters check failed, request won't be handled")
                                await client.close()
                                await packet.stop_propagation()
                                handle = []
                else:
                    logging.warning(f"({session_id}) {{API Parser}} Unimplemented API method '{request_type}'")
                    await self.invalid_json_request(session_id, stream)

    async def setup(self):
        """This function is called when the server is started"""

        return

    async def shutdown(self):
        """This function is called when the server shuts down"""
        return

    async def handle_client(self, stream: trio.SocketStream):
        """
        This function handles a single client connection:

        - It assigns a unique ID to each client session
        - It listens on the asynchronous socket and acts accordingly
        e.g. incomplete streams or abrupt disconnection
        - It handles timeouts if the client hangs for some reason
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
                                break
                else:
                    header = int.from_bytes(raw_data[0:self.header_size], self.byteorder)
                    logging.debug(f"({session_id}) {{Client handler}} Expected stream length is {header}")
                    if len(raw_data[self.header_size:]) == header:
                        logging.debug(f"({session_id}) {{Client handler}} Stream complete, processing API call")
                        try:
                            await self.parse_call(session_id, raw_data[self.header_size:], stream)
                        except StopPropagation:
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
        logging.debug(f"{{API main}} The buffer is set to {self.buf} bytes, logging is set to {self.logging_level}, protocol is {self.proto}")
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
        except OSError as os_error:
            logging.error(f"{{API main}} An error occurred while preparing to serve: {os_error}")
            sys.exit(os_error)

    def start(self):
        for index, (iname, ihandler) in enumerate(self.handlers.copy().items()):
            for name, handler in self.handlers.copy().items():
                if name != iname:
                    if ihandler == handler:
                        del self.handlers[name]
                        if not self.groups.get(ihandler.name, None):
                            self.groups[ihandler.name] = [ihandler, handler]
                        elif ihandler not in self.groups[ihandler.name]:
                            self.groups[ihandler.name].append(handler)
        for name, handlers in self.groups.copy().items():
            self.groups[name] = Group(handlers=handlers, name=name)
        for group in self.groups.values():
            self.handlers[group.name] = group
        for key, value in self.handlers.copy().items():
            if isinstance(key, int):
                self.handlers[value.name] = value
                del self.handlers[key]
        trio.run(self.serve_forever)
