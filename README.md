# AsyncAPY - A fully fledged Python 3.6+ library to serve APIs asynchronously 

![Logo](https://i.ibb.co/2jsY3Kv/IMG-20200316-114028-125.png)

[![Documentation Status](https://readthedocs.org/projects/asyncapy/badge/?version=dev)](https://asyncapy.readthedocs.io/en/dev/?badge=dev) 
[![Build Status](https://travis-ci.com/intellivoid/AsyncAPY.svg?branch=dev)](https://travis-ci.com/intellivoid/AsyncAPY)
![Open Issues](https://img.shields.io/github/issues/intellivoid/AsyncAPY) 
![License](https://img.shields.io/github/license/intellivoid/AsyncAPY)
![Stars](https://img.shields.io/github/stars/intellivoid/AsyncAPY)
![Python version](https://img.shields.io/badge/python-%3E%3D3.6-yellow)
![GitHub repo size](https://img.shields.io/github/repo-size/intellivoid/AsyncAPY)
![Version](https://img.shields.io/badge/version-0.3.3-blue)

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

## Hello, world!

Let’s write our very first API server with AsyncAPY, an echo server.

An echo server is fairly simple, it always replies with the same request that it got from the client


```python

from AsyncAPY.base import AsyncAPY   # Import the base class


server = AsyncAPY(addr='0.0.0.0',
                  logging_level=10,  # Debug mode
                  encoding="json",
                  port=1500
                 )

async def echo_server(client, packet):
    print(f"Hello world from {client}!")
    print(f"Echoing back {packet}...")
    await client.send(packet)

server.add_handler(echo_server)   # Register our handler

server.start()    # Start the server
```

Save this script into a file named ```example.py``` and try running it; your output should look like the one below

```
[INFO] 10/02/2020 16:28:38 PM  {API main} AsyncAPY server is starting up

[DEBUG] 10/02/2020 16:28:38 PM {API main} Running setup function...

[DEBUG] 10/02/2020 16:28:38 PM {API main} The buffer is set to 1024 bytes, logging is set to DEBUG,...

[INFO] 10/02/2020 16:28:38 PM  {API main} Now serving  at 0.0.0.0:1500
```

What happens if we send a packet to our new, shiny, echo server? Let’s try to use the testing client to send a packet to our server: create a new empty file, name it testclient.py and paste the following

```python
import AsyncAPY.defaultclient

client = defaultclient.Client("0.0.0.0", 1500, tls=False)
enc = 'json'
client.connect()
client.send({"test": 1}, encoding=enc)
response = client.receive_all()
print(response)
```


Now open two terminal windows, run `example.py` again and then `testclient.py`, your server output should look like the following:

```[INFO] 10/02/2020 16:39:35 PM  {Client handler} New session started, UUID is 7fd5fab0-5393-44ec-a75d-fa4f2c7e4562

[DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {Client handler} Expected stream length is 11

[DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {Client handler} Fragmented stream detected, rebuilding

[DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {API Parser} Protocol-Version is V2, Content-Encoding is json

[DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {API Parser} Done! Filters check passed, calling 'echo_server'

Hello world from Client(127.0.0.1)!

Echoing back Packet({"test": 1})...

[DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {Response handler} Sending response to client

[DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {Response Handler} Response sent

[DEBUG] 10/02/2020 16:39:36 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {API Parser} Execution of 'echo_server' terminated


[INFO] 10/02/2020 16:39:36 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {Client handler} The connection was closed
```

while your client output will look like this:

`b'\x00\x00\x00\r\x16\x00{"test": 1}'`

As you can see, we got the same JSON encoded packet that we sent!


__Note__: The line `server.add_handler(echo_server)` can be shortened the following way:

```python
@server.handler_add()
async def your_handler(c, p):
   ...
```

For a much more advanced usage you may want to check the official [documentation](https://asyncapy.readthedocs.io)

# Credits

## The main developer

Nocturn9x aka IsGiambyy - [Github](https://github.com/nocturn9x) & [Telegram](https://t.me/isgiambyy)

## Contributors

Penn5 - [Github](https://github.com/penn5) & [Telegram](https://t.me/Hackintosh5)


