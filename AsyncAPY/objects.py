from typing import List, Dict

from types import FunctionType
from errors import StopPropagation, ClientBan
from filter import Filter


class Client:

    def __init__(self, addr: str):
        self.address = addr

    def ban(self):
        raise ClientBan(self.address)


class Packet:

    def __init__(self, fields: Dict[str, str], sender: Client):
        self.fields = fields
        self.sender = sender

    async def stop_propagation(self):
        raise StopPropagation


class Handler:

    def __init__(self, function: FunctionType, name: str, filters: Filter = None, priority: int = 0):
        self.filters = filters
        self.function = function
        self.name = name

    def __repr__(self):
        return f"Handler({self.function}, '{self.name}', {self.filters})"

    def __eq__(self, other):
        if not isinstance(other, Handler):
            raise TypeError("The __eq__ operator is meant to compare Handler objects only!")

    def __call__(self, *args):
        return self.function.__call__(*args)


class Group:

    def __init__(self, handlers: List[Handler]):
        self.handlers = sorted(handlers, key=lambda x: x.priority)

    def __repr__(self):
        return f"Group({self.handlers})"

    def __iter__(self):
        return self.handlers.__iter__()




