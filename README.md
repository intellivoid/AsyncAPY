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


