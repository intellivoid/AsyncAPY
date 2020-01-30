import trio
import logging
import sys
import uuid
import json
import sqlite3.dbapi2 as sqlite3
from typing import Optional
from base import AsyncAPY
from filters import Filters


class UCSAPIServer(AsyncAPY):

    def __init__(self, addr: Optional[str] = "127.0.0.1", port: Optional[int] = 8081, buf: Optional[int] = 1024,
                 database: Optional[str] = "", logging_level: int = logging.INFO,
                 console_format: Optional[str] = "[%(levelname)s] %(asctime)s %(message)s",
                 datefmt: Optional[str] = "%d/%m/%Y %H:%M:%S %p", timeout: Optional[int] = 60):
        """Initializes self"""
        super().__init__(addr, port, buf, logging_level,
        console_format, datefmt, timeout)
        self.database_path = database
        self.database = None

srv = UCSAPIServer(port=1500, database="database1.db", logging_level=logging.DEBUG)

async def server_busy(server, session_id: uuid.uuid4, stream: trio.SocketStream):
    json_response = bytes(json.dumps({"status": "failure", "error": "SERVER_BUSY"}), "u8")
    response_header = len(json_response).to_bytes(2, "big")
    response_data = response_header + json_response
    await server.send_response(stream, response_data, session_id)


def query_manager(server, query, *args):
    database = sqlite3.connect(server.database_path)
    cursor = database.cursor()
    try:
        executed = cursor.execute(query, args)
    except sqlite3.OperationalError as sqlite3_error:
        return None, sqlite3_error
    return True, executed.fetchall()


@srv.handler_add("check_license")
async def check_license(server, session_id: uuid.uuid4, data: dict, stream: trio.SocketStream):
    """
    This functions checks whether a license-device_id couple is valid or not
    """

    status = "failure"
    license_exists = "invalid"
    authorized = False
    error = None
    end = False
    try:
        client_license = str(data["license"])
        device_id = str(data["device_id"])
    except KeyError as missing_field:
        logging.error(f"({session_id}) {{License checker}} Missing {missing_field} field in JSON check_license request")
        await server.missing_json_field(session_id, stream, str(missing_field))
        end = True
    else:
        logging.debug(f"({session_id}) {{License checker}} License is {client_license}")
        logging.debug(f"({session_id}) {{License checker}} Device ID is {device_id}")
        check = await trio.to_thread.run_sync(server.query_manager,
                                              "SELECT authorized_devices FROM customers WHERE license = ?", client_license)
        if check[0] is None:
            logging.error(
                f"({session_id}) {{License checker}} Something went wrong while dealing with database: {check[1]}")
            await server.server_busy(session_id, stream)
        else:
            query_result = check[1]
            if not query_result:
                error = "ERR_LICENSE_INVALID"
                logging.debug(f"({session_id}) {{License checker}} License {client_license} does not exist")
            else:
                logging.debug(f"({session_id}) {{License checker}} License {client_license} is valid, checking device ID")
                authorized_devices = query_result[0][0].split("-")
                if device_id in authorized_devices:
                    authorized = True
                    license_exists = "valid"
                    status = "success"
                    logging.debug(
                        f"({session_id}) {{License checker}} Device {device_id} is authorized, verification complete")
                else:
                    error = "ERR_DEVICE_UNAUTHORIZED"
                    logging.warning(f"({session_id}) {{License checker}} Device {device_id} isn't an authorized device")
    if not end:
        json_response = bytes(
            json.dumps({"status": status, "license": license_exists, "authorized": authorized, "error": error}), "u8")
        response_header = len(json_response).to_bytes(2, "big")
        response_data = response_header + json_response
        await server.send_response(stream, response_data, session_id)


@srv.handler_add("ping", filters=Filters.Ip("193.187.152.161"))
async def ping_request(server, session_id: uuid.uuid4, data: dict, stream: trio.SocketStream):
    """Just a test function"""

    json_response = bytes(json.dumps({"status": "success", "error": None}), "u8")
    response_header = len(json_response).to_bytes(2, "big")
    response_data = response_header + json_response
    await server.send_response(stream, response_data, session_id)


@srv.handler_add("ping", priority=1, filters=Filters.Ip("193.187.152.161"))
async def ping_request_2(server, session_id: uuid.uuid4, data: dict, stream: trio.SocketStream):
    """Just a test function"""

    json_response = bytes(json.dumps({"status": "success", "error": None}), "u8")
    response_header = len(json_response).to_bytes(2, "big")
    response_data = response_header + json_response
    await server.send_response(stream, response_data, session_id)


async def load_database(server):
    """
    This function loads the SQLite3 database on startup.
    If the database file is not present, or if the customers table is
    missing, a fresh database will be created and loaded.
    """

    try:
        server.database = sqlite3.connect(server.database_path)
    except sqlite3.DatabaseError as db_error:
        logging.debug(f"{{API main}} Something went wrong while attempting to connect to the database: {db_error}")
        sys.exit(db_error)
    cursor = server.database.cursor()
    try:
        cursor.execute("SELECT * from customers")
    except sqlite3.OperationalError as sqlite3_error:
        if str(sqlite3_error) == "no such table: customers":
            logging.debug("{API main} Database is empty, creating table 'customers'")
            query = """CREATE TABLE customers(
                customer_id INTEGER NULL PRIMARY KEY AUTOINCREMENT,
                license TEXT NOT NULL UNIQUE,
                authorized_devices TEXT NOT NULL
                );"""
            try:
                cursor.execute(query)
                server.database.commit()
            except sqlite3.OperationalError as sqlite3_error:
                logging.error(f"{{API main}} Error while dealing with database: {sqlite3_error}")
                sys.exit(sqlite3_error)
            else:
                logging.debug("{API main} Database created")
                cursor.close()
        else:
            logging.error(f"{{API main}} Error while dealing with database: {sqlite3_error}")
            sys.exit(sqlite3_error)


async def setup(server):
    logging.debug("{API main} Preparing to load SQLite3 Database")
    await server.load_database()
    logging.debug("{API main} Database loaded")


if __name__ == "__main__":
    srv.start()

