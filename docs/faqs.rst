AsyncAPY - Frequently Asked Questions
=====================================


My console output is not ordered, why?
--------------------------------------

Don't worry, it's nothing related to how you deployed your server.

AsyncAPY uses `trio <https://trio.readthedocs.io>`_ as asynchronous framework, but this would happen with any aysnc framework like gevent or asyncio. It happens because the order in which coroutines are executed is only partially deterministic, this means that
trio's runner function will choose according to some non-predictable conditions when and to which functions give execution control. That's also the reason why AsyncAPY has session ids, to allow users to understand what is what.


Why don't my filter pass?
-------------------------

Well, this can happen for a number of reasons. An example could be if you want to allow 2 specific IP addresses to a handler and pass 2 different ``Filters.Ip``: This will never work. Why? Because it would mean that a client would have to have 2 associated IPV4 addresses at the same time, which is impossible

Try passing the two IP addresses to the same filter as a list, and check if it works.

In general, it's better to have just 1 or 2 ``Filter`` objects which match all your desired conditions, than many smaller filters, as this also has impacts on performance (More filters == more time spent iterating over them to check them)


