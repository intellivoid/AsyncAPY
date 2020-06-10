AsyncAPY - Getting started
==========================

Installing
-----------

Right now, the package is not available on PyPi because some custom dependencies need to be documented and published to the index before AsyncAPY can be succesfully installed via ``pip``.
In the meanwhile, you can run the following command in your terminal/shell (assuming ``pip`` and ``git`` are already installed):

``python3 -m pip install --user git+https://github.com/intellivoid/AsyncAPY``

This will install AsyncAPY and its dependencies in your system


**Note**: On Windows systems, unless you are using PowerShell, you may need to replace ``python3`` with ``py`` or ``py3`` for the commands to work, assuming you added it to ``PYTHONPATH`` when installed Python.


Hello, world!
-------------

Let's write our very first API server with AsyncAPY, an echo server.

An echo server is fairly simple, it always replies with the same request that it got from the client

.. code-block:: python
   
   from AsyncAPY import Server

   server = Server(addr='0.0.0.0',
                   port=1500
                  )

   async def echo_server(client, packet):
       print(f"Hello world from {client}!")
       print(f"Echoing back {packet}...")
       await client.send(packet)
       await client.close()

   server.register_handler(echo_server)   # Register our handler

   server.start()    # Start the server


Save this script into a file named ``example.py``. 

What happens if we send a packet to our new, shiny, echo server? Let's try to use the testing client to send a packet to our server: create a new empty file, name it ``testclient.py`` and paste the following

.. code-block:: python

   import AsyncAPY.defaultclient


   client = defaultclient.Client("0.0.0.0", 1500, tls=False)  
   enc = 'json'
   client.connect()
   client.send({"test": 1}, encoding=enc)
   response = client.receive_all()
   print(response)

Now open two terminal windows, run ``example.py`` and then ``testclient.py``, your server output should look like the following:
 
::

    [INFO] 10/02/2020 16:39:35 PM  {Client handler} New session started, UUID is 7fd5fab0-5393-44ec-a75d-fa4f2c7e4562

    [DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {Client handler} Expected stream length is 11

    [DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {API Parser} Protocol-Version is V2, Content-Encoding is json

    [DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {API Parser} Checking group 0

    [DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {API Parser} Calling 'echo_server' in group 0

    Hello world from Client(127.0.0.1)!

    Echoing back Packet({"test": 1})...

    [DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {Response handler} Sending response to client

    [DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {Response Handler} Response sent

    [INFO] 10/02/2020 16:39:36 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {Client handler} The connection was closed

while your client output will look like this:

 ::

    b'\x00\x00\x00\r\x16\x00{"test": 1}'

As you can see, we got the same JSON encoded packet that we sent!


Filters
--------

You can allow only a subset of packet/client pair to reach your handler, see `here <https://asyncapy.readthedocs.io/en/latest/AsyncAPY.html#module-AsyncAPY.filters>`_ to know more.

Filters can be applied to a handler by passing one or more ``Filter`` objects to the ``Server.register_handler()``.

An example of a filtered handler can be found in our dedicated `examples section <https://asyncapy.readthedocs.io/en/dev/examples.html#filters-examples>`_
						   
If you have issues with filters, try reading our `FAQ <https://asyncapy.readthedocs.io/en/dev/faqs.html#why-don-t-my-filter-pass>`_ on this topic


Using the decorators
--------------------

Decorators are a nicer way to add handlers to your server. The line ``Server.register_handler()`` can be also written as follows:


.. code-block:: python

   @server.add_handler()
   async def your_handler(c, p):
       ...

The decorator behaves the same as ``Server.register_handler`` and take the filter object(s) and the group identifier as optional parameters.


Groups
------

The way AsyncAPY handles incoming requests has been specifically designed to be simple yet effective.

If you register two or more handlers with conflicting/overlapping filters, only the first one that was registered will be executed.

To handle the same request more than once, you need to register the handler in a different handlers group, like in the following example:



The ``group`` parameter defaults to 0, the lower this number, the higher will be the position of the handler in the queue.
In the example above, ``group`` equals ``-1``, that is lower than ``0`` and therefore causes that handler to execute first. You could have also set it to 1 (or any other value greather than 0) to make it execute last instead.

