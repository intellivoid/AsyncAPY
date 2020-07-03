.. AsyncAPY documentation master file, created by
   sphinx-quickstart on Sat Feb  8 16:48:59 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

AsyncAPY - Official Documentation
====================================
.. image:: ./images/logo.png

.. image:: https://readthedocs.org/projects/asyncapy/badge/?version=latest
    :target: https://asyncapy.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


.. image:: https://travis-ci.com/intellivoid/AsyncAPY.svg?branch=master
    :target: https://travis-ci.com/intellivoid/AsyncAPY
    :alt: Build Status

    
AsyncAPY is a fully fledged framework to easily deploy asynchronous API 
endpoints over a custom-made protocol (`AsyncAProto`)

It deals with all the low level I/O stuff, error handling and async calls, exposing a high-level and easy-to-use API designed with simplicity in mind.

Some of its features include:

- **Fully** asynchronous
- Automatic timeout and error handling
- Custom application layer protocol
- Groups: multiple functions can handle the same packet and interact with the remote client
- **Powerful, easy-to-use and high level** API for clients, packets and sessions
- Packets filtering


What's new in AsyncAPY 0.4
--------------------------

- Groups and handlers have been completely reworked, check the docs
- The ``AsyncAPY`` class has been renamed to ``Server`` and some breaking changes have been done
- The V1 protocol has been deprecated
- The ``AsyncAPY.objects`` module has been made private. ``Client`` and ``Packet`` objects can be imported from the top-level package
- The code for the server has been polished and improved

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   intro
   faqs
   examples
   protocol

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
