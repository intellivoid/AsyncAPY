import socket
import ziproto
import json

s = socket.socket()

s.connect(("127.0.0.1", 1500))

payload = ziproto.encode({"field": 55})
payload_json = json.dumps({"field": 55}).encode()
protocol_version = (22).to_bytes(1, "little")
content_encoding = (1).to_bytes(1, "little") # Change here
content_length = (len(payload) + 2).to_bytes(4, "little")
packet = content_length + protocol_version + content_encoding + payload
print(protocol_version)
print(content_encoding)
print(packet)
s.sendall(packet)
resp = s.recv(2048)
print(resp)
print(ziproto.decode(resp[6:]))
resp = s.recv(2048)
print(resp)
print(json.loads(resp[6:]))
