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

import string
import random


class APIKeyFactory(object):

    """Generic class to manage a basic in-memory storage of API subscriptions, represented as keys of variable size, implementing functionality to issue, revoke and reissue keys

    :param size: The desired size of the API key. By default, it's just a random string, defaults to 32
    :type size: int, optional
    """

    def __init__(self, size: int = 32):
        self.size = size
        self._keys = {}

    def issue(self, metadata: dict = None):
        """Returns a new random API key of ``self.size`` length, saves it and attaches to it eventual metadata

        :param metadata: A dictionary object containing meaningful information that is returned with the ``self.get`` method. Defaults to ``None``
        :type metadata: dict, optional
        :returns key: The generated API key
        :rtype: str
        """

        key = "".join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(self.size)
        )
        self._keys[key] = metadata
        return key

    def get(self, key: str):
        """Returns the associated metadata with the given key, raises ``KeyError`` if the key doesn't exist

        :param key: The API key
        :type key: str
        :returns: The associated metadata with the given API key
        :rtype: str
        :raises KeyError: If the given key does not exist
        """

        return self._keys[key]

    def revoke(self, key: str):
        """Revokes an API key, removing its associated data from the internal dictionary

        :param key: The API key to revoke
        :type key: str
        :raises KeyError: If the given key does not exist
        """

        self._keys.pop(key)

    def reissue(self, key):
        """Reissues an API key, replacing the old ``key`` with a new one, keeping the old metadata

        :param key: The API key to reissue
        :type key: str
        :raises KeyError: If the given key does not exist
        :returns: The new API key
        """

        return self.issue(self.get(key))

    def update(self, key: str, metadata: dict):
        """Updates the associated metadata for the given key with the provided value

        :param key: The API key to update data for
        :type key: str
        :param metadata: A dictionary object containing meaningful information that is returned with the ``self.get`` method
        :type metadata: dict
        :raises KeyError: If the given key does not exist
        """

        self._keys[key] = metadata

    def __contains__(self, item):
        """Implements item in self"""

        return self._keys.__contains__(item)
