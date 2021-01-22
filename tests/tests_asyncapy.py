from asyncapy.client import Client
import json
import ziproto
import time


class TestAsyncAPY:
    def test_headers(self):
        enc = 'json'
        client = Client(tls=False, encoding=enc)
        client.connect("127.0.0.1", 1500)
        client.send({"test": 1})
        response = client.receive_raw()
        content_length, protocol_version, content_encoding, payload = client._split_packet(response)
        assert len(payload) + 2 == content_length, content_length
        assert protocol_version == 22, protocol_version
        assert content_encoding in (0, 1), content_encoding
        if enc == 'json':
            payload = json.loads(payload)
        else:
            payload = ziproto.decode(payload)
        assert payload == {"test": 1}
        client.disconnect()

    def test_encodings(self):
        client = Client(tls=False, encoding="json")
        client.connect("127.0.0.1", 1500)
        client.send({"req": "bar"})
        assert client.receive() == {"req": "bar"}
        client.disconnect()
        client.connect("127.0.0.1", 1500)
        client.encoding = "ziproto"
        client.send({"foo": "lol"})
        assert client.receive() == {"foo": "lol"}
        client.disconnect()

    def test_header_rebuilding(self):
        """
        Tests the capabilities of the AsyncAPY server
        and the underlying protocol of rebuilding broken
        packets by simulating a worst-case scenario where
        a packet is broken into individual bytes
        """

        client = Client(tls=False, encoding="json")
        client.connect("127.0.0.1", 1500)
        payload = {"foo": "test_payload"}
        payload = json.dumps(payload).encode()
        length_header = (len(payload) + 2).to_bytes(
            client.header_size, client.byteorder
        )
        content_encoding = (0).to_bytes(1, "big")
        protocol_version = (22).to_bytes(1, "big")
        headers = length_header + protocol_version + content_encoding
        packet = headers + payload
        for byte in packet:
            client.sock.send(byte.to_bytes(1, "big"))
            time.sleep(0.1)   # Simulates network congestion
        assert client.receive() == {"response": "OK"}

    def test_wrong_encoding_header(self):
        """
        Tests that the server recognizes and
        properly refuses payloads with malformed
        encoding headers
        """

        client = Client(tls=False, encoding="json")
        client.connect("127.0.0.1", 1500)
        payload = {"invalid": True}
        payload = json.dumps(payload).encode()
        length_header = (len(payload) + 2).to_bytes(
            client.header_size, client.byteorder
        )
        content_encoding = (1).to_bytes(1, "big")
        protocol_version = (22).to_bytes(1, "big")
        headers = length_header + protocol_version + content_encoding
        packet = headers + payload
        client.sock.sendall(packet)
        client.encoding = "ziproto"  # So the client can decode the response
        assert client.receive() == {"status": "failure", "error": "ERR_REQUEST_MALFORMED"}

    def test_timeout(self):
        """
        Tests that timeouts work as intended
        """

        client = Client(tls=False)
        client.connect("127.0.0.1", 1500)
        time.sleep(15)
        assert client.receive() == {"status": "failure", "error": "ERR_TIMED_OUT"}
