AsyncAPY - Getting started
==========================

Installing
-----------

Right now, the package is not available on PyPi because some custom dependencies need to be documented and published to the index before AsyncAPY can be succesfully installed via ``pip``.
In the meanwhile, you can run the following command in your terminal/shell (assuming ``pip`` and ``git`` are already installed):

``python3 -m pip install --user git+https://github.com/intellivoid/AsyncAPY``

This will install AsyncAPY and its dependencies in your system


**Note**: On Windows systems, unless you are using PowerShell, you may need to replace ``python3`` with ``py`` or ``py3`` for the commands to work, assuming you added it to ``PYTHONPATH`` when installed Python.
Please consider also that this command needs admin privileges to be run properly (There is one dependency which needs to be installed from ``setup.py``)


Hello, world!
-------------

Let's write our very first API server with AsyncAPY, an echo server.

An echo server is fairly simple, it always replies with the same request that it got from the client

.. code-block:: python
   
   from AsyncAPY.base import AsyncAPY   # Import the base class


   server = AsyncAPY(addr='0.0.0.0',
                     logging_level=10,  # Debug mode
                     encoding="json",
                     port=1500
                    )

   async def echo_server(client, packet):
       print(f"Hello world from {client}!")
       print(f"Echoing back {packet}...")
       await client.send(packet)

   server.add_handler(echo_server)   # Register our handler

   server.start()    # Start the server


Save this script into a file named ``example.py`` and try running it; your output should look like the one below
 
::

    [INFO] 10/02/2020 16:28:38 PM  {API main} AsyncAPY server is starting up

    [DEBUG] 10/02/2020 16:28:38 PM {API main} Running setup function...

    [DEBUG] 10/02/2020 16:28:38 PM {API main} The buffer is set to 1024 bytes, logging is set to DEBUG,...

    [INFO] 10/02/2020 16:28:38 PM  {API main} Now serving  at 0.0.0.0:1500

What happens if we send a packet to our new, shiny, echo server? Let's try to use the testing client to send a packet to our server: create a new empty file, name it ``testclient.py`` and paste the following

**Note**: We will be using the test client available in the official `Github Repository <https://github.com/nocturn9x/AsyncAPY/tree/dev/tests/defaultclient.py>`_, be sure to download that file and put it in your working directory

.. code-block:: python

   import defaultclient  # Make sure defaultclient.py is in your workdir

   client = defaultclient.Client("0.0.0.0", 1500)  
   enc = 'json'
   client.connect()
   client.send({"test": 1}, encoding=enc)
   response = client.receive_all()
   print(response)

Now open two terminal windows, run ``example.py`` again and then ``testclient.py``, your server output should look like the following:
 
::

    [INFO] 10/02/2020 16:39:35 PM  {Client handler} New session started, UUID is 7fd5fab0-5393-44ec-a75d-fa4f2c7e4562

    [DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {Client handler} Expected stream length is 11

    [DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {Client handler} Fragmented stream detected, rebuilding

    [DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {API Parser} Protocol-Version is V2, Content-Encoding is json

    [DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {API Parser} Done! Filters check passed, calling 'echo_server'

    Hello world from Client(127.0.0.1)!

    Echoing back Packet({"test": 1})...

    [DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {Response handler} Sending response to client

    [DEBUG] 10/02/2020 16:39:35 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {Response Handler} Response sent

    [DEBUG] 10/02/2020 16:39:36 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {API Parser} Execution of 'echo_server' terminated

    [INFO] 10/02/2020 16:39:36 PM (7fd5fab0-5393-44ec-a75d-fa4f2c7e4562) {Client handler} The connection was closed

while your client output will look like this:
 ::

    b'\x00\x00\x00\r\x16\x00{"test": 1}'

As you can see, we got the same JSON encoded packet that we sent!


.. note::
   Note that the line ``server.add_handler(echo_server)`` can be shortened the following way:
          
.. code-block:: python

   @server.handler_add()
   async def your_handler(c, p):
      ...



Filtering payloads and clients
------------------------------

AsyncAPY gives you the possibility to set some conditions to your handlers, which must all be met for it to be executed. Those conditions are represented in Python trough ``Filter`` objects, which are located in the ``Filters`` class of the ``AsyncAPY.filters`` module (see `here <https://asyncapy.readthedocs.io/en/latest/AsyncAPY.html#module-AsyncAPY.filters>`_)

Filters can be applied to a handler by passing a list of the desired filter(s) objects to the ``AsyncAPY.add_handler()`` method and of course to its decorator counterpart, ``@AsyncAPY.handler_add``.

An example of a filtered handler can be found in our dedicated `examples section <https://asyncapy.readthedocs.io/en/latest/examples.html#filters-examples>`_
						   
If you have issues with non-passing filters, try reading our `FAQ <https://asyncapy.readthedocs.io/en/latest/faqs.html#why-don-t-my-filter-pass>`_ on this topic

