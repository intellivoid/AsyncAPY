# AsyncAPY - A fully fledged Python 3.6+ library to serve APIs asynchronously 

![Intellivoid](https://i.imgur.com/me1E7z9.jpg)

[![Documentation Status](https://readthedocs.org/projects/asyncapy/badge/?version=latest)](https://asyncapy.readthedocs.io/en/latest/?badge=latest) [![Build Status](https://travis-ci.com/nocturn9x/AsyncAPY.svg?branch=master)](https://travis-ci.com/nocturn9x/AsyncAPY)

This repo contains the source code of the AsyncAPY framework, which is provided to the end-user "as is" without any warranty of any kind. 

The developer and/or Intellivoid Technologies will not take any responsibility for any sort of damage caused by this software, be it economical, a data loss or whatever. 

This project is published under the `Lesser General Public License Version 3`, for more detailed information check the `LICENSE` file provided within the repository. 

As of today, the latest version of AsyncAPY is 0.2.3

# Documentation

__Warning__: This documentation is not always up to date and it's not as complete as the official one available [here](https://asyncapy.readthedocs.io)

AsyncAPY is divided into two key components:
                            
- The AsyncAPY **protocol**, a.k.a. `AsyncAProto`, which is AsyncAPY's application protocol, that handles incoming packets, fragmentation and stuff like that
- The AsyncAPY **framework**, basically a wrapper around AsyncAProto and a customizable base class
            

This documentation will face both components of the AsyncAPY library


## AsyncAPY - The Protocol

AsyncAProto is built on top of raw TCP, and now you might be wondering: _"Why not HTTP?"_
												                 
I know this _looks kinda like a NIH sindrome_, but when I was building this framework I realized that HTTP was way too overkill for this purpose
and thought that creating a simpler and dedicated application protocol to handle simple packets, would have done the thing. And it actually did!
(Moreover, HTTP is basically TCP with lots of headers so meh)

### The protocol - A simple header system

AsyncAProto is divided into 2 versions, V1 and V2, which differ in the number of headers that are used.
AsyncAProto V1 does not have the `Content-Encoding` header and has been thought for the cases when it's not possible to determine the payload's encoding.

The three headers are:

- `Content-Length`: A byte-encoded integer representing the length of the packet (excluding itself). The recommended size is 4 bytes
- `Protocol-Version`: A 1 byte-encoded integer that can either be 11, for V1 version, or 22, for V2 
- `Content-Encoding`: A 1 byte-encoded integer that can either be 0, for JSON, or 1, for ZiProto. Consider that if the server cannot decode the payload because of an error in the header, the server will reject the packet

__P.S.__: Note that V1 requests **CANNOT** contain the `Content-Encoding` header. Also consider that the headers order must follow the one exposed above


### The protocol - Supported encodings

This server specifically deals with JSON and ZiProto encoded payloads, depending on configuration and/or client specifications (ZiProto is highly recommended for internal purposes as it has less overhead than JSON) 

A JSON packet with a 4 byte header encoded as a big-endian sequence of bytes (Which is the default), to an AsyncAPY server will look like this:

```\x00\x00\x00\x10\x16\x01{"foo": "bar"}```  
                         
and the ZiProto equivalent:

```\x00\x00\x00\x0b\x16\x01\x81\xa3foo\xa3bar```  

Both the byte order and the header size can be customized, by setting the `AsyncAPY.byteorder` and ` AsyncAPY.header_size` parameters

__Note__: Internally, also ZiProto requests are converted into JSON-like data structures, and then converted back to ZiProto before
being sent to the client. In order to be valid, then, the request MUST have a key-value structure, and then be encoded in ZiProto
     

### The protocol - Warnings

Please note, that if an invalid header is prepended to the payload, or no header is provided at all, the packet will be considered as corrupted and it'll be ignored. Specifically, the possible cases are:

- If the `Content-Length` header is bigger than `AsyncAPY.header_size` bytes, the server will read only `AsyncAPY.header_size` bytes as the `Content-Length` header, thus resulting in undesired behavior (most likely the server won't be able to read the socket correctly, thus resulting in the timeout to expire) 

- If the packet is shorter than `AsyncAPY.header_size`, the server will attempt to request more bytes from the client until the packet is at least `AsyncAPY.header_size` bytes long and then proceed normally, or close the connection if the process takes longer than `AsyncAPY.timeout` seconds, whichever occurs first

- If the payload is longer than `Content-Length` bytes, the packet will be truncated to the specified size and the remaining bytes will be read along with the next request (Which is undesirable and likely to cause decoding errors)
      
- If either the `Content-Encoding` or the `Protocol-Version` headers are not valid, the packet will be rejected

- If both `Content-Encoding` and `Protocol-Version` are correct, but the actual encoding of the payload is different from the specified one, the packet will be rejected

- In case of a V1 request, unless a `Content-Encoding` header is present (Remember: If you can determine the payload's encoding, just use V2!), the server will fall back to the default encoding and reject the request on decoding failure

- If the complete stream is shorter than `AsyncAPY.header_size + 3` bytes, the packet will be rejected


__Note 3__: The AsyncAPY server is not meant for users staying connected a long time, as it's an API server framework, the recommended timeout is 60 seconds (default) 

__Note 4__: Please also know that the byte order is important and __must be consistent__ between the client and the server! The number 24 encoded in big endian is decoded as 6144 if decoded with little endian, the same things happens with little endian byte sequences being decoded as big endian ones, so be careful! 

__Note 5__: Just as the server must be able to manage any package fragmentation, the clients must also implement the same strategies discussed above


## AsyncAPY - The framework 

After all those nasty words, let's write some code!

A simple Hello World with AsyncAPY looks like this


```
from AsyncAPY.base import AsyncAPY
from AsyncAPY.objects import Packet

server = AsyncAPY(port=1500, addr='0.0.0.0', encoding='json')

@server.handler_add()
async def hello_world(client, packet):

    print("Hello world from {client}!")
    await client.send(Packet({"status": "success", "response_code": "OK", "message": "Hello world!"), encoding='json')
    
server.start()
```


Ok, this is lots of code so let's break it into pieces:

- First, we imported the `AsyncAPY` class from the `AsyncAPY.base` Python file. We also imported `AsyncAPY.objects.Packet`, which is AsyncAPY's standard API for packets
- Then, we defined a server object that binds to our public IP address on port 1500, we chose JSON as the encoding as it's more human-readable, but you could have also used ziproto instead
- Here comes the fun part, the line `@server.handler_add()`, which is a Python decorator, is just a shorthand for `server.add_handler()`: This function registers the handler
inside our server so that it can handle incoming requests
- Then we defined our async handler: a handler in AsyncAPY is an asynchronous function which takes two parameters: A Client object and a Packet object which are high-level wrappers around the internal objects of AsyncAPY

What this handler does is just calling the client's method `send()` with a `Packet` object, and that's done! The internals of AsyncAPY will handle all the nasty low-level socket operations such as errors and timeouts!

__Note 6__: The payload, which is the parameter to the `Packet` object, can be any valid JSON string or Python dict, but not a ZiProto encoded object! The conversion to ZiProto is handled internally to avoid human errors


### The framework - Types and Objects

__Note 7__: Please note that this list does not include objects used internally by AsyncAPY such as `Group`s and `Handler`s objects, to avoid confusion. Also, protected attributes of objects such as `Client._server` or methods meant for internal use won't be listed here


The AsyncAPY framework exposes some high level methods and objects to ease the deployment of the server.


#### Types and Objects - Packet and Client API

The API to handle packets and clients is extremely easy, here is the list of all methods and attributes


The following objects can be imported from `AsyncAPY.objects`


  - `Client(addr, server, stream=None, session)` : The high-level API wrapped around internal AsyncAPY objects

      __Methods__:
      - `ban()` : Will ban the client's IP from the server, preventing further connections, but won't close the current session
      - `send(packet, close=True)` : Sends the given `Packet` object to the connected socket, if `close` is set to `True`, the server will automatically call `close()` on the client, it has to be set to `False` to take the advantages of `Packet`s propagation
          - Parameters:
	        - `packet`: A `Packet` object
            - `close`: A boolean value
      - `close()` : Closes the client underlying connection

      __Attributes__:
      - `session`: A unique UUID identifying the current client session
      - `address`: The client's remote IP address

__Note 8__: Here it is not shown how to initialize a `Client` object because this operation is meant to be done internally. 

                            
   - `Packet(payload, sender, encoding)` : A wrapper representing an AsyncAProto packet
     
      __Methods__: 
      - `stop_propagation()` : Raises `AsyncAPY.errors.StopPropagation`, thus preventing the packet from being forwarded to the next handler in the queue. It makes sense only if called in a handler within a group. 
      
       - Parameters to `__init__()`:
	        - `sender`: If the packet comes from the server, this parameter points to the `Client` object that sent that packet, if it needs to be initialized externally from the server, this parameter can be `None`
	        - `payload`: A python dictionary or a valid JSON string
	        - `encoding`: The packet encoding, it can either be "json" or "ziproto". If no encoding is specified, a `ValueError` exception will be raised

#### Types and Objects - Filters

The following objects are subclasses of `AsyncAPY.filters.Filters`, they can be used to filter the packets arriving to each handler

   - `Filters.Ip(ips)` : A filter for one or multiple IP addresses. Will match if the client IP is in the provided list of ips

     - Parameters to `__init__()`:
        - `ips`: A single IP, or a list of IP addresses. Please note that the IP(s) must be syntactically valid (They are checked upon initialization)

   - `Filters.Fields(**kwargs)`

     - Parameters to `__init__()`:
        - `**kwargs`: This filter accepts an unlimited number of keyword arguments, whose corresponding parameters can either be `None`, or a valid regular expression. In the first case, the filter will match if the request contains the specified field name, while in the other case the field value will also be checked with `re.match()`, using the provided parameter as pattern.

            For example, `Filters.Fields(this=None, foo='bar')` will match `{"this": "anything", "foo": "bar"}`, because the field `this` is present in the request (Note how the content of `this` is ignored) and also the value to the key `foo` matches the regex `bar`


### The framework - Setup and Shutdown functions, configuration files

AsyncAPY is highly customizable! If you need to perform some extra operation before starting to serve, or need to do some cleanups after the server exits, you can simply make a child class from `AsyncAPY.base.AsyncAPY` and override the `setup() ` and `shutdown()` methods respectively (Note that these methods are called internally with no parameters other than `self`) 

__Note 9__: The `shutdown()` function is called only after a proper `KeyboardInterrupt`, e.g. `Ctrl+C`

Also, AsyncAPY can be configured with an external config file, whose path needs to be passed to the `AsyncAPY` object as the `config` parameter. An example config looks like the one below, please know that the parser is whitespace-sensitive and that a space between the key and the equal sign, and between the equal sign itself and the following value is compulsory. 

__Example config File__:

```
[AsyncAPY]
addr = 127.0.0.1
port = 1500
encoding = ziproto
header_size = 4
byteorder = little
buf = 1024
logging_level = 10
```

__Note 10__: Please note that a configuration file will overwrite all the instance attributes of the `AsyncAPY` object!
Also, the config showed above lists all the values that can be passed through the config file, other values will be ignored


### The framework - Exposed Methods

Here is the list of all the methods that are needed to deploy an AsyncAPY server

   - `AsyncAPY.add_handler(handler, filters, priority)`

      - Parameters:
         - `handler`: An asynchronous function that has to accept two parameters, a `Client` and a `Packet` instance, in this order
         - `filters`: A list of one or more `Filter` objects
         - `priority`: An integer: if the handler shares filters with other handlers, this parameter tells the server which handler within that group has to be executed first. The lower this number, the higher execution priority

   - `AsyncAPY.handler_add(filters, priority)`: Decorator version of `AsyncAPY.add_handler()`


### One last thing - Groups 

The methods `AsyncAPY.add_handler()` and `@AsyncAPY.handler_add()` accept a `priority` parameter which has to be an integer. Defining handlers with identical filters makes no sense, but what If I wanted to handle the same request multiple times? That's where propagation enters the game! If you define handlers with identical names and filters and you want that both of them have a chance to handle that request, choose the one that has to be executed first and assign it a lower priority than the second one. Example, if two handlers have priorities set to -1 and 0, the handler with priority -1 will be executed first. Please note that defining handlers with same filters/names and also same priority, which is 0 by default, raises `RuntimeError`. Same thing happens if you define another handler which is not in the group, but has the same name as an already existing group. 

__P.S. 3__: This is another stupid limitation brought by the nonsense implementation of handler names, which will be removed along with other pointless and buggy features in the next release (AsyncAPY 0.2)
