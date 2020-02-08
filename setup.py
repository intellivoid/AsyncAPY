# AsyncAPY - A fully fledged Python 3.6+ library to serve APIs asynchronously
# Copyright (C) 2019-2020 Intellivoid <https://github.com/intellivoid>
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

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="AsyncAPY",
    version="0.2.1",
    author="Mattia Giambirtone aka Nocturn9x",
    author_email="nocturn9x@intellivoid.info",
    description="A fully fledged Python 3.6+ library to serve APIs asynchronously",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/intellivoid/AsyncAPY",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
