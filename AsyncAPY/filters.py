import re


class Filter(object):
    pass


class Filters(Filter):

    """This class implements all standard filters"""

    class Ip:
        def __init__(self, ips: list or str):
            pat = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
            if isinstance(ips, list):
                for ip in ips:
                    if not pat.match(ip):
                        raise ValueError("Invalid IP address in filter!")
            elif isinstance(ips, str):
                if not pat.match(ips):
                    raise ValueError("Invalid IP address in filter!")
            self.ips = {ips}

        def __eq__(self, other):
            if other is None:
                return False
            if not isinstance(other, Filters.Ip):
                raise ValueError
            if isinstance(other, Filters.Ip):
                return True if self.ips - other.ips == set() else False

        def check(self, c):
            return c.address not in c._server.banned and c.address in self.ips

        def __call__(self, c):
            return self.check(c)




