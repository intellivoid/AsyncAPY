.. AsyncAPY documentation master file, created by
   sphinx-quickstart on Sat Feb  8 16:48:59 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

AsyncAPY - Official Documentation
====================================
.. image:: ./images/logo.png

AsyncAPY is a fully fledged framework to easily deploy asynchronous API endpoints over a custom-made protocol (`AsyncAProto`)

It deals with all the low level I/O stuff, error handling and async calls, exposing a high-level and easy-to-use API designed with simplicity in mind.

Some of its features include:

- **Fully** asynchronous
- Automatic timeout and error handling
- Custom application layer protocol to reduce overhead
- Groups: multiple functions can handle the same packet and interact with the remote client
- **Powerful, easy-to-use and high level** API for clients and packets
- Packets filtering

As of today, there is no native TLS support, as AsyncAPY is meant to be ran behind a load balancer/reverse proxy such as HaProxy or Nginx. If you really want to use it as a stand-alone API server, 
feel free to open an issue on the `repository <https://github.com/intellivoid/AsyncAPY>`_  with the label "enhancement" and I'll consider adding optional TLS support.
											

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules
   intro
   faqs
   examples
   protocol

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
