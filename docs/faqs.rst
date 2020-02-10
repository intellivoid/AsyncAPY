AsyncAPY - Frequently Asked Questions
=====================================


My console output is not ordered, why?
--------------------------------------

Don't worry, it's nothing related to how you deployed your server.
AsyncAPY uses `trio <https://trio.readthedocs.io>`_ as asynchronous framework, but this would happen with any aysnc framework like gevent or asyncio. It happens because the order in which coroutines are executed is only partially deterministic, this means that
trio's runner function will choose according to some non-predictable conditions when and to which functions give execution control. That's also the reason why AsyncAPY has session ids, to allow users to understand what is what.


