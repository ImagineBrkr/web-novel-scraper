Configuring Requests
====================

Some websites may respond slowly, and some systems may require more time to process requests.

If chapter downloads fail due to timeouts, consider increasing the timeout value or the number of retries.

Increasing Timeout
------------------

.. code-block:: bash

   web-novel-scraper \
     --request-timeout 60 \
     request-all-chapters \
     -t "My Novel"

Increasing Retries
------------------

.. code-block:: bash

   web-novel-scraper \
     --request-retries 10 \
     request-all-chapters \
     -t "My Novel"

Waiting Between Retries
-----------------------

.. code-block:: bash

   web-novel-scraper \
     --request-time-between-retries 5 \
     request-all-chapters \
     -t "My Novel"

These options can also be configured through environment variables or a configuration file, see :doc:`../reference/config` .