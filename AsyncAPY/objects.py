from typing import List, Dict, Union
from .filters import Filter
from types import FunctionType
from .errors import StopPropagation
import json


class Client:

    def __init__(self, addr: str, server, stream=None, session: str = None):
        self.address = addr
        self._server = server
        self._stream = stream
        self.session = session

    async def ban(self):
        self._server.add(self.address)

    async def send(self, packet):
        payload = packet.payload.encode("utf-8")
        header = packet.length.to_bytes(self._server.header_size, self._server.byteorder)
        data = header + payload
        await self._server.send_response(self._stream, data, self.session)

    async def close(self):
        await self._stream.close()


class Packet:

    def __init__(self, fields: Union[Dict[str, str], str, bytes], sender: Client or None):
        self.sender = sender
        if isinstance(fields, dict):
            self.payload = json.dumps(fields)
        elif isinstance(fields, bytes):
            self.payload = json.dumps(json.loads(fields.decode("utf-8")))
        else:
            self.payload = json.dumps(json.loads(fields))
        self.length = len(self.payload)

    async def stop_propagation(self):
        raise StopPropagation


class Handler:

    def __init__(self, function: FunctionType, name: str, filters: List[Filter] = None, priority: int = 0):
        self.filters = filters
        self.function = function
        self.name = name
        self.priority = priority

    def __repr__(self):
        return f"Handler({self.function}, '{self.name}', {self.filters}, {self.priority})"

    def compare_names(self, other):
        return other.name == self.name

    def compare_priority(self, other):
        return self.priority != other.priority

    def compare_filters(self, other):
        if len(self.filters) != len(other.filters):
            return False
        for index, filter in enumerate(self.filters):
            ofilter = other.filters[index]
            if ofilter != filter:
                return False
        return True


    def __eq__(self, other):
        if not isinstance(other, Handler):
            raise TypeError("The __eq__ operator is meant to compare Handler objects only!")
        if self.compare_names(other) and self.compare_filters(other) and not self.compare_priority(other):
            raise RuntimeError("Multiple handlers with identical filters and names cannot share priority level!")
        elif self.compare_names(other):
            if self.compare_priority(other):
                if self.compare_filters(other):
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def call(self, *args):
        return self.function.__call__(*args)


class Group:

    def __init__(self, handlers: List[Handler], name: str):
        self.handlers = sorted(handlers, key=lambda x: x.priority)
        self.name = name

    def __repr__(self):
        return f"Group({self.handlers})"

    def __iter__(self):
        return self.handlers.__iter__()




