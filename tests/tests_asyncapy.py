import defaultclient
import json
import ziproto
import socket
import time


class TestAsyncAPY:

    def test_headers(self):
        client = defaultclient.Client("127.0.0.1", 1501, tls=False)
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

    def test_encodings(self):
        client = defaultclient.Client("127.0.0.1", 1501, tls=False)
        client.connect()
        encodings = ("json", "ziproto")
        payload = {"req": "bar"}
        client.send(payload, encoding=encodings[0])
        response = client.receive_all()
        response_payload = response[client.header_size + 2:]
        assert json.loads(response_payload) == payload, response_payload
        del payload, response, response_payload
        expected = {"response": "OK"}
        client.send({"req": "test_payload"}, encoding="json")
        print(client.receive_all())  # Discard the echoed packet
        response = client.receive_all()
        response_payload = response[client.header_size + 2:]
        assert json.loads(response_payload) == expected, response_payload
        client.disconnect()

    def test_header_rebuilding(self):
        client = defaultclient.Client("127.0.0.1", 1501, tls=False)
        client.connect()
        payload = {"foo": "test_payload"}
        payload = json.dumps(payload)
        length_header = (len(payload) + 2).to_bytes(client.header_size, client.byteorder)
        content_encoding = (0).to_bytes(1, "big")
        protocol_version = (22).to_bytes(1, "big")
        headers = length_header + protocol_version + content_encoding
        packet = headers + payload.encode()
        for byte in packet:
            client.sock.send(byte.to_bytes(1, client.byteorder))
            time.sleep(0.1)
        assert json.loads(client.receive_all()[client.header_size + 2:]) == json.loads(payload)

    def test_invalid_v1_request(self):
        client = defaultclient.Client("127.0.0.1", 1501, tls=False)
        client.connect()
        payload = {"req": "test_payload"}
        payload = json.dumps(payload)
        length_header = (len(payload) + 2).to_bytes(client.header_size, client.byteorder)
        content_encoding = (0).to_bytes(1, "big")
        protocol_version = (11).to_bytes(1, "big")
        headers = length_header + protocol_version + content_encoding
        packet = headers + payload.encode()
        client.sock.sendall(packet)
        resp = client.receive_all()
        assert json.loads(resp[client.header_size + 2:]) == {"status": "failure", "error": "ERR_REQUEST_MALFORMED"}, resp[client.header_size + 2:]

    def test_wrong_encoding_header(self):
        client = defaultclient.Client("127.0.0.1", 1501, tls=False)
        client.connect()
        payload = {"invalid": True}
        payload = json.dumps(payload)
        length_header = (len(payload) + 2).to_bytes(client.header_size, client.byteorder)
        content_encoding = (1).to_bytes(1, "big")
        protocol_version = (22).to_bytes(1, "big")
        headers = length_header + protocol_version + content_encoding
        packet = headers + payload.encode()
        client.sock.sendall(packet)
        resp = client.receive_all()
        assert json.loads(ziproto.decode(resp[client.header_size + 2:]).tobytes()) == {"status": "failure", "error": "ERR_REQUEST_MALFORMED"}

    def test_timeout(self):
        client = defaultclient.Client("127.0.0.1", 1501, tls=False)
        client.connect()
        time.sleep(60)
        try:
            stuff = client.receive_all()
        finally:
            assert not stuff, ("Timeout not expired!", stuff)


