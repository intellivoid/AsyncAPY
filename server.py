from AsyncAPY.base import AsyncAPY
from AsyncAPY.objects import Client, Packet
from AsyncAPY.filters import Filters
import logging


server = AsyncAPY(addr='127.0.0.1', port=1500, timeout=86400, logging_level=10)

@server.handler_add([Filters.Fields(request="sudo", password='Benetton', action='shutdown', recipient="^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")])
async def send_shutdown_signal(client: Client, packet: Packet):
    logging.info(f"({client.session}) {{Shutdown signal}} Sending shutdown signal to {packet['recipient']}")
    if not client._server._sessions.get(packet["recipient"], None):
        logging.info(f"({client.session}) {{Shutdown signal}} No such active session for {packet['recipient']}")
        await client.send(Packet({"status": "failure", "code": 404, "msg": "ERR_NO_SUCH_SESSION"}, 0 if client.encoding == "json" else 1), close=False)
        await client.close()
    else:
        admin = client
        logging.info(f"({client.session}) {{Shutdown signal}} Found {len(client._server.sessions[packet['recipient']])} active sessions for {packet['recipient']}, sending shutdown signal")
        for session in client._server._sessions[packet['recipient']]:
            client = session.get_client()
            logging.info(f"({client.session}) {{Shutdown signal}} Now interacting with {client} at {session}")
            await client.send(Packet({"signal": "shutdown"}, encoding=0 if client.encoding == "json" else 1), close=False)
        await admin.send(Packet({"status": "success", "code": 200, "msg": null}, encoding=0 if client.encoding == 'json' else 1))

if __name__ == "__main__":
    logging.getLogger(__name__)
    server.start()
