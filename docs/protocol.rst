AsyncAPY - The Protocol
=======================


The protocol - Why not HTTP?
----------------------------
   
AsyncAProto is built on top of raw TCP, and now you might be wondering: `"Why not HTTP?"`
	                 
I know this `looks kinda like a NIH sindrome`, but when I was building this framework I realized that HTTP was way too overkill for this purpose
and thought that creating a simpler and dedicated application protocol to handle simple packets, would have done the thing. And it actually did!
(Moreover, HTTP is basically TCP with lots of headers so meh)

The protocol - A simple header system
--------------------------------------

AsyncAProto is divided into 2 versions, V1 and V2, which differ in the number of headers that are used.

AsyncAProto V1 does not have the ``Content-Encoding`` header and has been thought for the cases when it's not possible to determine the payload's encoding.

The three headers are:

- ``Content-Length``: A byte-encoded integer representing the length of the packet (excluding itself). The recommended size is 4 bytes
- ``Protocol-Version``: A 1 byte-encoded integer that can either be 11, for V1 version, or 22, for V2 
- ``Content-Encoding``: A 1 byte-encoded integer that can either be 0, for JSON, or 1, for ZiProto. Consider that if the server cannot decode the payload because of an error in the header, the server will reject the packet

**P.S.**: Note that V1 requests **CANNOT** contain the ``Content-Encoding`` header. Also consider that the headers order must follow the one exposed above
   
    
The protocol - Supported encodings
-----------------------------------
                          
AsyncAPY has been designed to deal with JSON and ZiProto encoded payloads, depending on configuration and/or client specifications (ZiProto is highly recommended for internal purposes as it has less overhead than JSON) 

A JSON packet with a 4 byte header encoded as a big-endian sequence of bytes (Which is the default), to an AsyncAPY server will look like this:

``\x00\x00\x00\x10\x16\x01{"foo": "bar"}``
                          
and the ZiProto equivalent:
 
``\x00\x00\x00\x0b\x16\x01\x81\xa3foo\xa3bar``

Both the byte order and the header size can be customized, by setting the ``AsyncAPY.byteorder`` and ``AsyncAPY.header_size`` parameters
  
**Note**: Internally, also ZiProto requests are converted into JSON-like data structures, and then converted back to ZiProto before
being sent to the client. In order to be valid, then, the request MUST have a key-value structure, and then be encoded in ZiProto
     

The protocol - Warnings
-----------------------
    
Please note, that if an invalid header is prepended to the payload, or no header is provided at all, the packet will be considered as corrupted and it'll be ignored. Specifically, the possible cases are:

- If the ``Content-Length`` header is bigger than ``AsyncAPY.header_size`` bytes, the server will read only ``AsyncAPY.header_size`` bytes as the ``Content-Length`` header, thus resulting in undesired behavior (most likely the server won't be able to read the socket correctly, thus resulting in the timeout to expire) 

- If the packet is shorter than ``AsyncAPY.header_size`` bytes, the server will attempt to request more bytes from the client until the packet is at least ``AsyncAPY.header_size`` bytes long and then proceed normally, or close the connection if the process takes longer than ``AsyncAPY.timeout`` seconds, whichever occurs first

- If the payload is longer than ``Content-Length`` bytes, the packet will be truncated to the specified size and the remaining bytes will be read along with the next request (Which is undesirable and likely to cause decoding errors)
      
- If either the ``Content-Encoding`` or the ``Protocol-Version`` headers are not valid, the packet will be rejected

- If both ``Content-Encoding`` and ``Protocol-Version`` are correct, but the actual encoding of the payload is different from the specified one, the packet will be rejected

- In case of a V1 request, the server will use the server's default encoding to decode the payload (and reject the packet on decoding failure)

- If the complete stream is shorter than ``AsyncAPY.header_size + 3`` bytes, the packet will be rejected

                       
**Note 3**: AsyncAPY is not meant for users staying connected a long time, as it's an API server framework, the recommended timeout is 60 seconds (default) 

**Note 4**: Please also know that the byte order is important and **must be consistent** between the client and the server! The number 24 encoded in big endian is decoded as 6144 if decoded with little endian, the same things happens with little endian byte sequences being decoded as big endian ones, so be careful! 

**Note 5**: Just as the server must be able to manage any package fragmentation, the clients must also implement the same strategies discussed above


