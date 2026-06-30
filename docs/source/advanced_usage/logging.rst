Logging
=======

Web Novel Scraper provides configurable logging for troubleshooting and monitoring.

Logging Level
-------------

The logging level can be configured using the ``SCRAPER_LOGGING_LEVEL`` environment variable.

The default value is:

.. code-block:: text

   INFO

The available logging levels are:

- ``DEBUG``: Detailed information, typically of interest only when diagnosing problems.
- ``INFO``: Confirmation that things are working as expected.
- ``WARNING``: An indication that something unexpected happened.
- ``ERROR``: A more serious problem, the software has not been able to perform some function.

Example:

.. code-block:: bash

   export SCRAPER_LOGGING_LEVEL=DEBUG

Log File
--------

By default, logs are written to standard output (stdout).

To save logs to a file, set the ``SCRAPER_LOGGING_FILE`` environment variable:

.. code-block:: bash

   export SCRAPER_LOGGING_FILE=/path/to/scraper.log

Example
-------

.. code-block:: bash

   export SCRAPER_LOGGING_LEVEL=DEBUG
   export SCRAPER_LOGGING_FILE=/tmp/web-novel-scraper.log

   web-novel-scraper request-all-chapters -t "My Novel"