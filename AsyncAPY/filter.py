# Credits to Dan Tès <https://github.com/delivrance> - Pyrogram <https://github.com/delivrance/pyrogram>


class Filter:
    def __call__(self, message):
        raise NotImplementedError

    def __invert__(self):
        return InvertFilter(self)

    def __and__(self, other):
        return AndFilter(self, other)

    def __or__(self, other):
        return OrFilter(self, other)


class InvertFilter(Filter):
    def __init__(self, base):
        self.base = base

    def __call__(self, message):
        return not self.base(message)


class AndFilter(Filter):
    def __init__(self, base, other):
        self.base = base
        self.other = other

    def __call__(self, message):
        return self.base(message) and self.other(message)


class OrFilter(Filter):
    def __init__(self, base, other):
        self.base = base
        self.other = other

    def __call__(self, message):
        return self.base(message) or self.other(message)
