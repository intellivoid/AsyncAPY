import pytest
import defaultclient
import json
import ziproto
import socket


class TestAsyncAPY:


    def test_headers(self):
       client = defaultclient.Client("127.0.0.1", 1500)
       enc = 'json'
       client.connect()
       client.send({"test": 1}, encoding=enc)
       response = client.receive_all()
       content_length = int.from_bytes(response[0:client.header_size], client.byteorder)
       protocol_version = int.from_bytes(response[client.header_size:client.header_size + 1], "big")
       content_encoding = int.from_bytes(response[client.header_size + 1:client.header_size + 2], "big")
       assert len(response[client.header_size:]) == content_length, content_length
       assert protocol_version in (11, 22), protocol_version
       assert content_encoding in (0, 1), content_encoding
       if enc == 'json':
           payload = json.loads(response[client.header_size + 2:])
       else:
           payload = ziproto.decode(response[client.header_size + 2:])
       assert payload == {"test": 1}
       client.disconnect()
       del client

    def test_encodings(self):
        client = defaultclient.Client("127.0.0.1", 1500)
        client.connect()
        encodings = ("json", "ziproto")
        payload = {"req": "test_payload"}
        client.send(payload, encoding=encodings[0])
        response = client.receive_all()
        response_payload = response[client.header_size + 2:]
        assert json.loads(response_payload) == payload, response_payload
        client.disconnect()
        client.sock = socket.socket()
        client.connect()
        client.send(payload, encoding=encodings[1])
        response = client.receive_all()
        response_payload = response[client.header_size + 2:]
        assert ziproto.decode(response_payload) == payload, response_payload
        client.disconnect()

TestAsyncAPY().test_encodings()
