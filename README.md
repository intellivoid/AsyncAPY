# Internal-API-Server
This repo contains the source code of the AsyncAPY framework, which will be used to deploy an asynchronous TCP based API server with JSON requests meant for internal use at Intellivoid

As of today, the latest version of AsyncAPY is 0.1.49

# Documentation

AsyncAPY is divided into two things:

- The AsyncAPY **protocol** which is the implementation of a TLV standard application protocol which handles incoming packets and stuff like that
- The AsyncApy **framework**, basically a wrapper around the AsyncAPY protocol and a customizable base class
            




This documentation will face both components of the AsyncAPY library


## AsyncAPY - The Protocol

AsyncAPY's protocol is built on top of raw TCP, and now you might be wondering: "Why not HTTP?"
												                 
I know this _looks kinda like a NIH sindrome_, but when I was building this framework I realized that HTTP was way too overkill for this purpose
and thought that creating a, simpler, dedicated application protocol to handle simple requests, would have done the thing. And it actually did!
(Moreover, HTTP is basically TCP with lots of headers so meh)

### The protocol - A simple header system

AsyncAPY's protocol needs just one and only one header to work properly, which can be seen as the equivalent of the `Content-Length` header in an HTTP request. It is a byte-encoded integer which tells the server the length of the payload following the header itself. 

And that's just how it is, it is as simple as that! Pretty neat, deh? 

__P.S.__: In the future, a couple more headers could be added. An example could be a single byte, named `ProtocolVersion` to determine the version of the protocol implementation that the client runs, or a `Content-Type` header which could be used to guess dynamically the type of the payload, either ziproto or json, before falling back to the server default encoding

### The protocol - Supported formatting system

This server specifically deals with JSON and ZiProto encoded requests, depending on configuration (ZiProto is highly recommended for internal purposes as it has less overhead than JSON) 

A JSON request with a 2 byte header encoded as a big-endian sequence of bytes (Which is the default), to an AsyncAPY server will look like this:

```\x00\x18{"request_type": "ping"}```

and the ZiProto equivalent:

```\x00\x13\x81\xacrequest_type\xa4ping```

Both the byte order and the header size can be customized, by setting the `AsyncAPY.byteorder` and ` AsyncAPY.header_size` parameters

__Note__: Internally, also ZiProto requests are converted into JSON-like structures and then into Python dictionaries, and then converted back to ZiProto before
being sent back to the client. In order to be valid, then, the request MUST have a key-value structure, and then be encoded in ZiProto. 


### The protocol - Fields

Both JSON and ZiProto formatted requests can have an arbitrary amount of fields, as long as the header size is big enough, but there's only one, compulsory, field which is `request_type` and is crucial for the server to identify the handler(s) that should handle that request. When you register a handler its name will be the associated `request_type`, read the section below for more information. 

__P.S. 2__: This, stupid, limitation on the field name/content has been realized to be totally nonsense and will be removed in a future release of AsyncAPY--namely _from version 0.2 and above_.

__Note 2__: The order of fields in a request isn't important


### The protocol - Warnings

Please note, that if an invalid header is prepended to the payload, or no header is provided at all, the request will be considered as corrupted and it'll be ignored. Specifically, the possible cases are:

- If the header is bigger than `AsyncAPY.header_size` bytes, the server will read only `AsyncAPY.header_size` bytes as the header, thus resulting in undesired behavior (See below) 

- If the stream is shorter than `AsyncAPY.header_size`, the server will attempt to request more bytes from the client until the stream is at least `AsyncAPY.header_size` bytes long and then proceed normally, or close the connection if the process takes longer than `AsyncAPY.timeout` seconds, whichever occurs first

- If the payload is longer than `AsyncAPY.header_size` bytes, the packet will be truncated to the specified size and the remaining bytes will be read along with the next request (Which is undesirable)


__Note 3__: The AsyncAPY server is not meant for users staying connected a long time, as it's an API server framework, the recommended timeout is 60 seconds (default) 

__Note 4__: Please also know that the byte order is important and __must be consistent__ between the client and the server! The number 24 encoded in big endian is decoded as 6144 if decoded with little endian, the same things happens with little endian byte sequences being decoded as big endian ones, so be careful! 

__Note 5__: Just as the server must be able to manage any package fragmentation, the clients must also implement the same strategies discussed above


## AsyncAPY - The framework 

After all those nasty words, let's write some code!

A simple Hello World with AsyncAPY looks like this


```
from AsyncAPY.base import AsyncAPY
from AsyncAPY.objects import Packet

server = AsyncAPY(port=1500, addr='0.0.0.0', proto='json')

@server.handler_add("ping")
async def hello_world(client, packet):

    print("Hello world from {client}!")
    await client.send(Packet({"status": "success", "response_code": "OK", "message": "Hello world!")
    
server.start()
```


Ok, this is lots of code so let's break it into pieces:

- First, we imported the `AsyncAPY` class from the `AsyncAPY.base` Python file. We also imported `AsyncAPY.objects.Packet`, which is AsyncAPY's standard API for packets
- Then, we defined a server object that binds to our public IP address on port 1500, we chose JSON as the formatting stile as it's more human-readable, but you could have also used ziproto instead
- Here comes the fun part, the line `@server.handler_add()`, which is a Python decorator, is just a shorthand for `server.add_handler()`: This function registers the handler
inside our server so that it can handle incoming requests. As we registered our handler with the name 'ping', all requests which have `"ping"` as their `request_type` field will be forwarded to this handler
- Then we defined our async handler, a handler in AsyncAPY is an asynchronous function which takes two parameters: A Client object and a Packet object which are high-level wrappers around the internal objects of AsyncAPY

What this handler does is just calling the client's method `send()` with a `Packet` object, and that's done! The internals of AsyncAPY will handle all the nasty low-level socket operations such as errors and timeouts!

__Note 6__: The payload, which is the parameter to the `Packet` object, can be any valid JSON string or Python dict, but not a ZiProto encoded object! The conversion to ZiProto is handled internally to avoid human errors


### The framework - Types and Objects

__Note 7__: Please note that this list does not include objects used internally by AsyncAPY such as `Group`s and `Handler`s objects, to avoid confusion. Also, protected attributes of objects such as `Client._server` won't be listed here


The AsyncAPY framework exposes some high level methods and objects to ease the deployment of the server.

#### Types and Objects - Packet and Client API

The API to handle packets and clients is extremely easy, here is the list of all methods and attributes


  - `Client(addr, server, stream=None, session)`
     
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


   - `Packet(payload, sender)`
      
      __Methods__: 
      - `stop_propagation()` : Raises `AsyncAPY.errors.StopPropagation`, thus preventing the packet from being forwarded to the next handler in the queue. It makes sense only if called in a handler within a group. 
      
       - Parameters to `__init__()`:
	        - `sender`: If the packet comes from the server, this parameter points to the `Client` object that sent that packet, if it needs to be initialized externally from the server, this parameter can be `None`
	        - `payload`: A python dictionary or a valid JSON string
		
		
		
### The framework - Setup and Shutdown functions, configuration files

AsyncAPY is highly customizable! If you need to perform some extra operation before starting to serve, or need to do some cleanups after the server exits, you can simply make a child class from `AsyncAPY.base.AsyncAPY` and override the `setup() ` and `shutdown()` methods respectively (Note that these methods are called internally with no parameters other than `self`) 

__Note 9__: The `shutdown()` function is called only after a proper `KeyboardInterrupt`, e.g. `Ctrl+C`

Also, AsyncAPY can be configured with an external config file, whose path needs to be passed to the `AsyncAPY` object as the `config` parameter. An example config looks like the one below, please know that the parser is whitespace-sensitive and that a space between the key and the equal sign, and between the equal sign itself and the following value is compulsory. 

__Example config File__:

```
[AsyncAPY]
addr = 127.0.0.1
port = 1500
proto = ziproto
header_size = 4
byteorder = little
buf = 1024
logging_level = 10
```

__Note 10__: Please note that a configuration file will overwrite all the instance attributes of the `AsyncAPY` objects!
Also, the config showed above lists all the values that can be passed through the config file, other values will be ignored


### The framework - Filter objects 


AsyncAPY supports two kind of filters, but in the future some more may be added. 

To use the filters you first need to import the `AsyncAPY.filters.Filters` class, which has two subclasses:
- `Ip(ips)`: Matches an ip, or a list of ips. IP(s) must be properly formatted or a 
`ValueError` exception will be raised
- `Fields(**kwargs)` : The `__init__()` constructor of this class accepts an unlimited number of keyword arguments. If the value of the argument is `None`, the filter will match if the field(s) name(s) are present in the incoming request and in the keyword arguments. Optionally, if a string is assigned to an argument, the server will check, with the passed parameter as a regex, the value of the request instead of the presence of the field only. 

Filters can be applied to handlers, by passing a list of `Filters` objects to the `filters` parameter of `AsyncAPY.add_handler()` or `@AsyncAPY.handler_add()`


__Note 11__: For obvious reasons, fields inside a `Filter.Fields` object can only be valid python identifiers, and their values must either be valid regular expressions or `None`


### One last thing - Groups 

The methods `AsyncAPY.add_handler()` and `@AsyncAPY.handler_add()` accept a `priority` parameter which has to be an integer. Defining handlers with identical filters makes no sense, but what If I wanted to handle the same request multiple times? That's where propagation enters the game! If you define handlers with identical names and filters and you want that both of them have a chance to handle that request, choose the one that has to be executed first and assign it a lower priority than the second one. Example, if two handlers have priorities set to -1 and 0, the handler with priority -1 will be executed first. Please note that defining handlers with same filters/names and also same priority, which is 0 by default, raises `RuntimeError`. Same thing happens if you define another handler which is not in the group, but has the same name as an already existing group. 

