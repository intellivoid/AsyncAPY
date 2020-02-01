class StopPropagation(Exception):
    """This exception is called when Packet.stop_propagation() is called
    to prevent the runner function from going further and forwarding the request to the next handler in the queue"""

    pass
