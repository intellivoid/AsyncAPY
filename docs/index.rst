.. AsyncAPY documentation master file, created by
   sphinx-quickstart on Sat Feb  8 16:48:59 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

AsyncAPY - Official Documentation
====================================
.. image:: ./images/logo.png

.. image:: https://readthedocs.org/projects/asyncapy/badge/?version=v0.3-alpha
   :target: https://asyncapy.readthedocs.io/en/v0.3-alpha/?badge=v0.3-alpha
   :alt: Documentation Status


.. image:: https://travis-ci.com/intellivoid/AsyncAPY.svg?branch=master
    :target: https://travis-ci.com/intellivoid/AsyncAPY

AsyncAPY is a fully fledged framework to easily deploy asynchronous API endpoints over a custom-made protocol (`AsyncAProto`)

It deals with all the low level I/O stuff, error handling and async calls, exposing a high-level and easy-to-use API designed with simplicity in mind.

Some of its features include:

- **Fully** asynchronous
- Automatic timeout and error handling
- Custom application layer protocol
- Groups: multiple functions can handle the same packet and interact with the remote client
- **Powerful, easy-to-use and high level** API for clients, packets and sessions
- Packets filtering

As of today, there is no native TLS support, as AsyncAPY is meant to be ran behind a load balancer/reverse proxy such as HaProxy. If you really want to use it as a stand-alone API server, 
feel free to open an issue on the `repository <https://github.com/intellivoid/AsyncAPY>`_  with the label "enhancement" and I'll consider adding optional TLS support.


What's new in AsyncAPY 0.3
--------------------------

The version 0.3 brought some great changes, listed below:

- The way both ``Client`` and ``Packet`` object get their ``encoding`` parameter has changed for consistency purposes, check the `docs <https://asyncapy.readthedocs.io/en/newversions-v0.3/AsyncAPY.html>`_
- Sessions are no longer just a useful way to recognize different clients in the console output, but are now ``Session`` objects which can be handy in a number of cases to interact with different clients in the same handler
- ``Packet`` objects now have a ``dict_payload`` attribute, which is a dictionary representation of the ``payload`` attribute
- ``Packet`` objects now suppport dict-like accessing! With a payload like ``{"foo": "bar"}``, you can do ``packet["foo"]`` to get ``"bar"``

.. warning::

   AsyncAPY 0.3 is still in the staging phase and it's not stable enough for production!
   If you find any bugs, please let us know by opening an `issue on the repository <https://github.com/intellivoid/AsyncAPY/issues/new/choose>`_


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
