from AsyncAPY.base import AsyncAPY
from AsyncAPY.filters import Filters
from AsyncAPY.objects import Client, Packet
import base64
import json
import logging

logging.getLogger(__name__)

server = AsyncAPY(config="server.conf")


@server.handler_add([Filters.Fields(payload=None, encoding=r"base64")])
async def base64_encoder(client: Client, packet: Packet):
    logging.info("Base64 encoder activated, attempting to encode")
    response_payload = base64.b64encode(json.dumps(packet.payload).encode("utf-8"))
    response_packet = Packet({"status": "OK", "payload": response_payload.decode("utf-8")}, encoding=client.encoding)
    await client.send(response_packet)
    logging.info("Done! Request processed")


@server.handler_add([Filters.Fields(payload=None, encoding=r"base32")])
async def base64_encoder(client: Client, packet: Packet):
    logging.info("Base32 encoder activated, attempting to encode")
    response_payload = base64.b32encode(json.dumps(packet.payload)["payload"].encode("utf-8"))
    response_packet = Packet({"status": "OK", "payload": response_payload.decode("utf-8")}, encoding=client.encoding)
    await client.send(response_packet)
    logging.info("Done! Request processed")


@server.handler_add([Filters.Fields(payload=None, decode=r"base64")])
async def base64_decoder(client: Client, packet: Packet):
    logging.info("Base64 decoder activated, attempting to decode")
    try:
        response_payload = base64.b64decode(json.loads(packet.payload)["payload"].encode("utf-8"))
    except Exception as e:
        logging.error(f"Error: '{e}' was raised while trying to decode!")
        await client.close()
    else:
        logging.info("Payload decoded! Sending result")
        response_packet = Packet({"status": "OK", "payload": response_payload.decode("utf-8")}, encoding=client.encoding)
        await client.send(response_packet)
        logging.info("Done! Request processed")


@server.handler_add([Filters.Fields(payload=None, decode=r"base32")])
async def base32_decoder(client: Client, packet: Packet):
    logging.info("Base32 decoder activated, attempting to decode")
    try:
        response_payload = base64.b32decode(json.loads(packet.payload)["payload"].encode("utf-8"))
    except Exception as e:
        logging.error(f"Error: '{e}' was raised while trying to decode!")
        await client.close()
    else:
        logging.info("Payload decoded! Sending result")
        response_packet = Packet({"status": "OK", "payload": response_payload.decode("utf-8")}, encoding=client.encoding)
        await client.send(response_packet)
        logging.info("Done! Request processed")

server.start()

