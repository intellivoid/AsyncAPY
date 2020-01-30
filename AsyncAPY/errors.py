class StopPropagation(StopIteration):
    pass


class ClientBan(RuntimeError):

    def __init__(self, addr):
        self.addr = addr
