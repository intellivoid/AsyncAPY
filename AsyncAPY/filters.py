from typing import Callable
from filter import Filter


def make_filter(function: Callable, name: str, **kwargs) -> Filter:

    """
    Credits to Dan Tès <https://github.com/delivrance> at <https://github.com/delivrance/pyrogram> for the great idea
    and inspiration
    This function creates new classes dynamically and can be used to create custom filters. The function parameter
    must either be a non-async function or a lambda function accepting two parameters (a server instance and a packet
    instance, in this order) and return a boolean value. True = request can be handled, False = do not handle request
    """

    properties = {"__call__": function}
    properties.update(**kwargs)

    return type(name, (Filter, ), properties)


class Filters:

    """This class implements all standard filters"""

    ip = make_filter(lambda server, packet: packet.sender.address not in server.banned)
