import socket
import ziproto
import json
import time

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
       :param byteorder: The client's byteorder, it can either be ``"json"`` or ``"ziproto"``, default to ``"json"``
       :type byteorder: str
       :param header_size: The size of the ``Content-Length`` header, defaults to 4
       :type header_size: int
    """


    def __init__(self, addr: str, port: int, byteorder: str = "big", header_size: int = 4):
        """Object constructor"""

        if not isinstance(addr, str):
            raise ValueError("address must be string!")
        if not isinstance(port, int):
            raise ValueError("port must be an integer!")
        if not byteorder in ("big", "little"):
            raise ValueError("byteorder must either be big or little!")
        if not isinstance(header_size, int):
            raise ValueError("header_size must be an integer!")
        self.addr = addr
        self.port = port
        self.byteorder = byteorder
        self.header_size = header_size
        self.sock = None

    def connect(self):
        """Connects to ``self.addr:self.port``"""

        self.sock = socket.socket()
        self.sock.connect((self.addr, self.port))

    def disconnect(self):
        """Disconnects from the server"""

        self.sock.close()

    def send(self, payload: dict or str, encoding: str = "json"):
        """Encodes the passed payload and sends it across the socket"""

        if isinstance(payload, dict):
            payload = json.dumps(payload).encode()
        else:
            payload = json.loads(payload).encode()
        if encoding == "ziproto":
            payload = ziproto.encode(json.loads(payload))
        content_length = len(payload).to_bytes(self.header_size, self.byteorder)
        content_encoding = (0).to_bytes(1, "big") if encoding == "json" else (1).to_bytes(1, "big")
        protocol_version = (22).to_bytes(1, "big")
        headers = content_length + protocol_version + content_encoding
        packet = headers + payload
        self.sock.sendall(packet)

    def rebuild_stream(size: int):
        """Rebuilds a stream if too short"""

        data = b""
        times = 0
        while len(data) < size:
            try:
                data += self.sock.recv(size)
            except Exception as error:
                print(f"An error occurred while reading from socket -> {error}")
            if not len(data) >= size:
                time.sleep(0.1)
                times += 1
            if times == 600:
                print("The 60 seconds timeout for reading the socket has expired, exiting...")
                break

        return data

    def receive_all(self):
        """Reads from ``self.sock`` until the packet is complete"""

        data = b""
        times = 0
        while len(data) < self.header_size:
            try:
                data += self.sock.recv(1024)
            except Exception as error:
                print(f"An error occurred while reading from socket -> {error}")
            if not len(data) >= self.header_size:
                time.sleep(0.1)
                times += 1
            else:
                content_length = int.from_bytes(data[0:self.header_size], self.byteorder)
                if len(data) - self.header_size < content_length:
                    print(f"Stream is fragmented, attempting to rebuild")
                    missing = self.rebuild_stream(content_length)
                    if missing:
                        data += missing
                    else:
                        print("Could not rebuild stream, bye")
                        break
                elif len(data) - self.header_size > content_length:
                    print("Invalid Content-Length header, discarding packet")
                    del data
                    del times
                    break
            if times == 600:
                print("The 60 seconds timeout for reading the socket has expired, exiting...")
                break

        return data
