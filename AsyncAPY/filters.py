# AsyncAPY - A fully fledged Python 3.6+ library to serve APIs asynchronously
# Copyright (C) 2019-2020 Nocturn9x <https://github.com/nocturn9x>
#
# This file is part of AsyncAPY.
#
# AsyncAPY is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# AsyncAPY is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with AsyncAPY.  If not, see <http://www.gnu.org/licenses/>.

import re, json


class Filter(object):
    pass


class Filters(Filter):

    """This class implements all standard filters"""

    class Ip(Filter):

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
            if not isinstance(other, Filter):
                raise ValueError("The equality comparison is meant for Filters objects only!")
            if isinstance(other, Filters.Ip):
                return True if self.ips - other.ips == set() else False
            else:
                return False

        def __repr__(self):
            return f"Filters.Ip({self.ips})"

        def check(self, c, _):
            return c.address in self.ips

        def __call__(self, c):
            return self.check(c)

    class Fields(Filter):
        def __init__(self, **kwargs):
            self.fields = {}
            for key, value in kwargs.items():
                if value is None:
                    self.fields[key] = value
                else:
                    self.fields[key] = re.compile(value)

        def __eq__(self, other):
            return self.fields == other.fields

        def check(self, _, p):
            fields = json.loads(p.payload)
            for field_name in self.fields:
                regex = self.fields[field_name]
                if field_name not in fields:
                    return False
                elif regex is not None:
                    if not regex.match(str(fields[field_name])):
                        return False
                del fields[field_name]

            if fields:    # There are still some extra fields which aren't in filter, fail the check
                return False
            return True    # If we are here, all filters match, good!

        def __repr__(self):
            return f"Filter.Fields({self.fields})"

