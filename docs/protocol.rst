AsyncAPY - The Protocol
=======================


The protocol - Why not HTTP?
----------------------------
   
AsyncAProto is built on top of raw TCP, and now you might be wondering: `"Why not HTTP?"`

I know this `kinda looks like a NIH sindrome`, but when I was building this framework, I realized that HTTP was way too overkill for this purpose,
and so I thought that creating a simpler and dedicated application protocol to handle simple packets would have done the thing. And it actually did!
(Moreover, HTTP is basically TCP with lots of headers so meh)

The protocol - A simple header system
--------------------------------------

AsyncAProto has just three headers that must be prepended to the payload in this exact order:

- ``Content-Length``: A byte-encoded integer representing the length of the packet (excluding this header itself, but including the next ones). The recommended size is 4 bytes
- ``Protocol-Version``: A 1 byte-encoded integer that indicates the protocol version. Will be used in future releases, for now it must be set to 22
- ``Content-Encoding``: A 1 byte-encoded integer that can either be 0, for JSON, or 1, for ZiProto. Consider that if the server cannot decode the payload because of an error in the header, the server will reject the packet

    
The protocol - Supported encodings
-----------------------------------
                          
AsyncAPY has been designed to deal with JSON and ZiProto encoded payloads, depending on configuration and/or client specifications (ZiProto is highly recommended for internal purposes as it has less overhead than JSON) 

A JSON packet with a 4 byte header encoded as a big-endian sequence of bytes (Which is the default), to an AsyncAPY server will look like this:

``\x00\x00\x00\x10\x16\x01{"foo": "bar"}``
                          
and the ZiProto equivalent:
 
``\x00\x00\x00\x0b\x16\x01\x81\xa3foo\xa3bar``

Both the byte order and the header size can be customized, by setting the ``AsyncAPY.byteorder`` and ``AsyncAPY.header_size`` parameters, but the ones exposed above are the protocol standards
            
.. warning::
   Internally, also ZiProto requests are converted into JSON-like data structures, and then converted back to ZiProto before
   being sent to the client. In order to be valid, then, the request MUST have a key-value structure, and then be encoded in ZiProto


The protocol - Warnings
-----------------------

.. warning::
   Please note, that if an invalid header is prepended to the payload, or no header is provided at all, the packet will be considered as corrupted and it'll be ignored.

AsyncAProto's Default Behaviours:

- If the ``Content-Length`` header is bigger than ``AsyncAPY.header_size`` bytes, the server will read only ``AsyncAPY.header_size`` bytes as the ``Content-Length`` header, thus resulting in undesired behavior (most likely the server won't be able to read the socket correctly, causing the timeout to expire) 

- If the packet is shorter than ``AsyncAPY.header_size`` bytes, the server will attempt to request more bytes from the client until the packet is at least ``AsyncAPY.header_size`` bytes long and then proceed normally, or close the connection if the process takes longer than ``AsyncAPY.timeout`` seconds, whichever occurs first

- If the payload is longer than ``Content-Length`` bytes, the packet will be truncated to the specified size and the remaining bytes will be read along with the next request (Which is undesirable and likely to cause decoding errors)
      
- If either the ``Content-Encoding`` or the ``Protocol-Version`` headers are not valid, the packet will be rejected

- If both ``Content-Encoding`` and ``Protocol-Version`` are correct, but the actual encoding of the payload is different from the specified one, the packet will be rejected

- If the complete stream is shorter than ``AsyncAPY.header_size + 5`` bytes, which is the minimum size of a packet, the packet will be rejected

                              
.. note::
   AsyncAPY is not meant for users staying connected a long time, as it's an API server framework. The recommended timeout is 60 seconds (default) 
             
.. warning::
   Please also know that the byte order is important and **must be consistent** between the client and the server! The number 24 encoded in big endian is decoded as 6144 if decoded with little endian, the same thing happens with little endian byte sequences being decoded as big endian ones, so be careful! 
            
.. note::
   Just as the server must be able to manage any package fragmentation, the clients must also implement the same strategies discussed above

