import socket
import ziproto
import json


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


    def __init__(addr: str, port: int, byteorder: str = "big", header_size: int = 4):
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

    def receive_all(self):
        """Reads from ``self.sock`` until the packet is complete"""

        pass

