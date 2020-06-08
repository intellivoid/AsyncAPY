AsyncAPY - Frequently Asked Questions
=====================================


My console output is not ordered, why?
--------------------------------------

Don't worry, it's nothing related to how you deployed your server.

The reason why this happens is that AsyncAPY uses `trio <https://trio.readthedocs.io>`_ as asynchronous framework, in order to process multiple requests at the same time. This  happens because the order in which coroutines are executed is only partially deterministic, this means that
trio's runner function will choose according to some non-predictable conditions when and to which functions give execution control. That's also the reason why AsyncAPY has session ids, to allow users to understand what is what.


Why don't my filter pass?
-------------------------

Well, this can happen for a number of reasons. An example could be if you want to allow 2 specific IP addresses to a handler and pass 2 different ``Filters.Ip``: This will never work. Why? Because you're telling AsyncAPY `"I want that only clients that have these 2 IP addresses at the same time can reach this handler"`, which is obviously impossible.
Try passing the two IP addresses to the same filter as a list, and check if it works.

In general, it's better to have few ``Filter`` objects which match all your desired conditions, than many smaller filters, as this also has impacts on performance (More filters == more time spent iterating over them to check them)


The encoding of the responses is wrong!
---------------------------------------

This can be related to many things, but please note that the encoding of the responses is related to the ``Content-Encoding`` header that you send to the server, but that it is defined **only once per session**.
If you send your first request encoded with json, and the next with ziproto, in the same session, you'll get two JSON encoded responses.
If you need two different encodings, start a new session by closing and opening a new connection to the server.


What the hell is ZiProto?
-------------------------

Directly from `ZiProto's official repo <https://github.com/netkas/ZiProto-Python>`_:

`ZiProto is a format for serializing and compressing data`
`[...] ZiProto is designed with the intention to be used for transferring data instead of using something like JSON`
`which can use up more bandwidth when you don't intend to have the data shown to the public or end-user`

