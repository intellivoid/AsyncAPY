import socket
import ziproto
import json
import time
import ssl
import logging


ADDR = '127.0.0.1'
PORT = 1500
ENCODING = 'json'
BYTEORDER = 'big'


class Client:
    """This is the official python implementation of the AsyncAProto client

       :param addr: The address of the server to connect to
       :type addr: str
       :param port: The port of the server to connect to
       :type port: int
       :param byteorder: The client's byteorder, it can either be ``"big"`` or ``"little"``, detault to ``"big"``
       :type byteorder: str
       :param header_size: The size of the ``Content-Length`` header, defaults to 4
       :type header_size: int
       :param tls: If ``True``, the client will initiate a TLS encrypted connection, defaults to ``False``
       :type tls: optional, bool
    """

    def __init__(self, addr: str, port: int, byteorder: str = "big", header_size: int = 4, tls: bool = False):
        """Object constructor"""

        if not isinstance(addr, str):
            raise ValueError("address must be string!")
        if not isinstance(port, int):
            raise ValueError("port must be an integer!")
        if byteorder not in ("big", "little"):
            raise ValueError("byteorder must either be big or little!")
        if not isinstance(header_size, int):
            raise ValueError("header_size must be an integer!")
        self.addr = addr
        self.port = port
        self.byteorder = byteorder
        self.header_size = header_size
        self.sock = None
        self.tls = tls
        self._extra_data = None


    def connect(self):
        """Connects to ``self.addr:self.port``"""

        if not self.tls:
            self.sock = socket.socket()
        else:
            self.sock = ssl.wrap_socket(socket.socket())
        self.sock.connect((self.addr, self.port))

    def disconnect(self):
        """Closes ``self.sock``"""

        self.sock.close()

    def send(self, payload: dict or str, encoding: str = "json"):
        """Encodes the passed payload and sends it across the socket, please note that this method does NOT catch any exception if an error occurs

           :param payload: The payload to send as a dictionary object or a valid JSON serializable string
           :type payload: dict or str, optional
           :param encoding: The encoding of the payload, note that this should be kept consistent across the session, as the encoding of responses cannot change during a session once defined (your packets will still be decoded properly, but you won't get the same encoding of your payloads)
           :type encoding: str, optional
        """

        if isinstance(payload, dict):
            payload = json.dumps(payload).encode()
        if encoding == "ziproto":
            payload = ziproto.encode(payload)
        content_length = (len(payload) + 2).to_bytes(self.header_size, self.byteorder)
        content_encoding = (0).to_bytes(1, "big") if encoding == "json" else (1).to_bytes(1, "big")
        protocol_version = (22).to_bytes(1, "big")
        headers = content_length + protocol_version + content_encoding
        packet = headers + payload
        self.sock.sendall(packet)

    def _rebuild_stream(self, size: int):
        """Rebuilds a stream if too short"""

        data = b""
        times = 0
        while len(data) < size:
            try:
                data += self.sock.recv(size)
            except Exception as error:
                logging.error(f"An error occurred while reading from socket -> {error}")
            if not len(data) >= size:
                time.sleep(0.1)
                times += 1
            if times == 600:
                logging.debug("The 60 seconds timeout for reading the socket has expired, exiting...")
                return None

        return data

    def receive_all(self):
        """Reads from ``self.sock`` until the packet is complete"""

        data = b""
        times = 0
        if self._extra_data:
            data += self._extra_data
            self._extra_data = None
        while len(data) < self.header_size:
            try:
                data += self.sock.recv(1024)
            except socket.error as error:
                logging.error(f"An error occurred while reading from socket -> {error}")
                return None
            if not len(data) >= self.header_size:
                time.sleep(0.1)
                times += 1
            else:
                content_length = int.from_bytes(data[0:self.header_size], self.byteorder)
                if len(data[self.header_size:]) < content_length:
                    logging.debug(f"Stream is fragmented, attempting to rebuild")
                    missing = self._rebuild_stream(content_length)
                    if missing:
                        data += missing
                    else:
                        logging.error("Could not rebuild stream")
                        return None
            if times == 600:
                logging.debug("The 60 seconds timeout for reading the socket has expired, exiting...")
                break
        if len(data[self.header_size:content_length]) > content_length:
            self._extra_data = data[content_length + 1:]
            data = data[:content_length]
        return data

