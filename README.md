# Internal-API-Server
This repo contains the source code of the AsyncAPY framework, which will be used to deploy an asynchronous TCP based API server with JSON requests meant for internal use at Intellivoid

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
      - `send(packet)`: Sends the given `Packet` object to the connected socket
          - Parameters:
	        - `packet`: A `Packet` object
	
	 
	


	
	

				




