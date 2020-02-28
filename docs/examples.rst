AsyncAPY - Code Examples
========================


Filters Examples
----------------

Here is an example on how to use AsyncAPY's ``Filters`` objects

.. literalinclude:: ../examples/filters.py

You can also use multiple ``Filters`` objects, e.g. ``Filters.Ip``, by doing the following

.. literalinclude:: ../examples/morefilters.py

.. warning::
    If you want to allow multiple ips inside the ``Filters.Ip`` filter, pass
    a list of ips, **NOT** multiple ``Filters.Ip`` objects!


Groups Examples
---------------

Here is an example on how to use AsyncAPY's grouping features

.. literalinclude:: ../examples/groups.py

.. note::
    It is possible to group handlers with filters, as long as they
    share the same filters, not necessarily in the same order, and have
    different priorities

