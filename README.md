# AsyncAPY - A fully fledged Python 3.6+ library to serve APIs asynchronously 

![Logo](https://i.ibb.co/2jsY3Kv/IMG-20200316-114028-125.png)

[![Documentation Status](https://readthedocs.org/projects/asyncapy/badge/?version=latest)](https://asyncapy.readthedocs.io/en/dev/?badge=latest) 
[![Build Status](https://travis-ci.com/intellivoid/AsyncAPY.svg?branch=master)](https://travis-ci.com/intellivoid/AsyncAPY)
![Open Issues](https://img.shields.io/github/issues/intellivoid/AsyncAPY) 
![License](https://img.shields.io/github/license/intellivoid/AsyncAPY)
![Stars](https://img.shields.io/github/stars/intellivoid/AsyncAPY)
![Python version](https://img.shields.io/badge/python-%3E%3D3.6-yellow)
![GitHub repo size](https://img.shields.io/github/repo-size/intellivoid/AsyncAPY)
![Version](https://img.shields.io/badge/version-0.4.3-blue)

AsyncAPY is a Python framework, supporting Python 3.6 and above, that simplifies the process of creating API backends with an async flavor without having to actually deal with the low-level I/O operation, cancellation/timeout handling and all that messy stuff, because AsyncAPY does that automatically under the hood, and it does so in a smart way that grants stability and low resource demand.

Some of its features are:

- **Fully** asynchronous
- Automatic timeout and error handling
- Custom application layer protocol
- Groups: multiple functions can handle the same packet and interact with the remote client
- __Powerful, easy-to-use and high level API__ for clients, packets and sessions
- Packets filtering
- Easy to _code, read and understand_
- **Minimize** boilerplate code
- Native support for JSON and a custom standard (see [here](https://github.com/netkas/ZiProto-Python))
- Simple protocol specifications: The protocol can be easily reimplemented in any language
- Automatic handling of API subscriptions (API keys)

# Documentation

The official documentation is available [here](https://asyncapy.readthedocs.io)

# Getting started

## Installing

Right now, the package is not available on PyPi because some custom dependencies need to be documented and published to the index before AsyncAPY can be succesfully installed via pip. In the meanwhile, you can run the following command in your terminal/shell (assuming pip and git are already installed):

`python3 -m pip install --user git+https://github.com/intellivoid/AsyncAPY`

This will install AsyncAPY and its dependencies in your system

__Note__: _On Windows systems, unless you are using PowerShell, you may need to replace python3 with `py` or `py3`, assuming you added Python to PYTHONPATH when installed it._

# Credits

## The main mastereloper

Nocturn9x aka IsGiambyy - [Github](https://github.com/nocturn9x) & [Telegram](https://t.me/isgiambyy)

## Contributors

Penn5 - [Github](https://github.com/penn5) & [Telegram](https://t.me/Hackintosh5)


