import socket
import json

s = socket.socket()
json_data = {"request_type": "ping"}
header = len(json.dumps(json_data))
packet = header.to_bytes(2, "big") + json.dumps(json_data).encode()
s.connect(("127.0.0.1", 1500))
s.sendall(packet)
print(s.recv(2048))
