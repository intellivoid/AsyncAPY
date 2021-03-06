# AsyncAPY - A fully fledged Python 3.6+ library to serve APIs asynchronously
# Copyright (C) 2019-2020 intellivoid <https://github.com/intellivoid>
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

import re
from typing import Union, List
from copy import deepcopy
from .util import APIKeyFactory


class Filter(object):
    """The standard base for all filters"""

    def check(self, c, p):
        """Dummy check method"""
        return


class Filters(Filter):

    """
    This class implements all the filters in AsyncAPY
    """

    class Ip(Filter):
        """
        Filters one or more IP addresses, allowing only the ones inside the filter to pass
        Note: This filter is dynamic, it can be updated at runtime if assigned to a variable

        :param ips: An ip or a list of ip addresses
        :type ips: Union[List[str], str]
        :raises ValueError: If the provided ip, or ips, isn't a valid IP address
        """

        def __init__(self, ips: Union[List[str], str]):
            """
            Object constructor
            """

            pat = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
            if isinstance(ips, list):
                for ip in ips:
                    if not pat.match(ip):
                        raise ValueError("Invalid IP address in filter!")
            elif isinstance(ips, str):
                if not pat.match(ips):
                    raise ValueError("Invalid IP address in filter!")
            else:
                raise ValueError("ips parameter must be string or list of strings!")
            if isinstance(ips, list):
                self.ips = {*ips}
            else:
                self.ips = {ips}

        def __repr__(self):
            """
            Returns ``repr(self)``

            :returns repr: A string representation of ``self``
            :rtype: str
            """

            return f"Filters.Ip({self.ips})"

        def check(self, c, _):
            """
            Implements the method to check if a filter matches a given packet/client couple or not

            :param c: A client object
            :type c: class: ``Client``
            :param _: A packet object, unused in this specific case
            :type _: class: ``Packet``
            :returns shall_pass: ``True`` if the client's IP is in the filters, ``False`` otherwise
            :rtype: bool
            """

            return c.address in self.ips

    class Fields(Filter):
        """
        Filters fields inside packets.
        This filter accepts an unlimited number of keyword arguments, that can either be ``None``, or a valid regex.
        In the first case, the filter will match if the request contains the specified field name, while in the other case
        the field value will also be checked with ``re.match()``, using the provided parameter as pattern.

        :param kwargs: A list of key-word arguments, which reflects the desired key-value structure of a payload
        :type kwargs: Union[None, str]"""

        def __init__(self, **kwargs):
            self.fields = {}
            for key, value in kwargs.items():
                if value is None:
                    self.fields[key] = value
                else:
                    self.fields[key] = re.compile(value)

        def check(self, _, p):
            """
            Implements the method to check if a filter matches a given packet/client couple or not

            :param _: A client object
            :type _: class: ``Client``, unused in this specific case
            :param p: A packet object
            :type p: class: ``Packet``
            :returns shall_pass: ``True`` if the packet's payload follows the given structure, ``False`` otherwise
            :rtype: bool
            """

            fields = deepcopy(p.dict_payload)
            for field_name in self.fields:
                regex = self.fields[field_name]
                if field_name not in fields:
                    return False
                elif regex is not None:
                    if not regex.match(str(fields[field_name])):
                        return False
                del fields[field_name]
            if (
                fields
            ):  # There are still some extra fields which aren't in filter, fail the check
                return False
            return True  # If we are here, all filters match, good!

        def __repr__(self):
            """
            Returns ``repr(self)``

            :returns repr: A string representation of ``self``
            :rtype: str
            """

            return f"Filter.Fields({self.fields})"

    class APIFactory(Filter):

        """
        A class that wraps around the ``APIKeyFactory`` class and its children, but as a filter.
        This filter passes if the provided field name is in the incoming packet and its value is a valid API key inside
        ``self.factory``

        :param factory: The ``APIKeyFactory`` object
        :type factory: class: APIKeyFactory
        :param field_name: The name of the field to lookup into incoming packets, if the field is not present
        the filter won't pass
        :type field_name: str

        """

        def __init__(self, factory: APIKeyFactory, field_name: str):
            """
            Object constructor
            """

            self.factory = factory
            self.field_name = field_name

        def check(self, _, p):
            """
            Implements ``self.check``, returns ``True`` if ``self.field_name`` exist in the provided packet and
            its value is a valid API key

            :param _: A client object
            :type _: class: ``Client``, unused in this specific case
            :param p: A packet object
            :type p: class: ``Packet``
            :returns shall_pass: ``True`` if the filter passed, ``False`` otherwise
            :rtype: bool
            """

            return p.dict_payload.get(self.field_name, None) in self.factory
