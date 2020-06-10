AsyncAPY - Code Examples
========================


Filters Examples
----------------

Here is an example on how to use AsyncAPY's ``Filters`` objects

.. literalinclude:: ../examples/filters.py

You can also use multiple ``Filters`` objects, by doing the following:

.. literalinclude:: ../examples/morefilters.py


You can pass as many filters as you want in any order. For a detailed look at filters check their docs.

Groups Examples
---------------


The way AsyncAPY handles incoming requests has been specifically designed to be simple yet effective.

If you register two or more handlers with conflicting/overlapping filters, only the first one that was registered will be executed.

To handle the same request more than once, you need to register the handler in a different group, like in the following example:

.. literalinclude:: ../examples/groups.py


The ``group`` parameter defaults to 0, the lower this number, the higher will be the position of the handler in the queue.
In the example above, ``group`` equals ``-1``, that is lower than ``0`` and therefore causes that handler to execute first. You could have also set it to 1 (or any other value greather than 0) to make it execute last instead.
