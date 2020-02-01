import re, json


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
                raise ValueError("The equality comparison is meant for Filters.Ip objects only!")
            if isinstance(other, Filters.Ip):
                return True if self.ips - other.ips == set() else False

        def check(self, c, _):
            return c.address in self.ips

        def __call__(self, c):
            return self.check(c)


    class Fields:

        def __init__(self, **kwargs):
            self.fields = {}
            for key, value in kwargs.items():
                if value is None:
                    self.fields[key] = value
                else:
                    self.fields[key] = re.compile(str(value))

        def __eq__(self, other):
            return self.fields == other.fields

        def check(self, _ , p):
            fields = json.loads(p.payload)
            del fields["request_type"]
            for field_name in self.fields:
                regex = self.fields[field_name]
                if field_name not in fields:
                    return False
                elif regex is not None:
                    if not regex.match(fields[field_name]):
                        return False
                del fields[field_name]

            if fields:    # There are still some extra fields which aren't in filter, fail the check
                return False
            return True    # If we are here, all filters match, good!

