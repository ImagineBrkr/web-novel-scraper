Configuration
=============

Web Novel Scraper can be configured using command-line parameters, environment variables, or a configuration file.

Configuration Priority
----------------------

When the same setting is defined in multiple places, the following priority order is used:

1. Command-line parameters
2. Environment variables
3. Configuration file
4. Default values

For example, if a timeout is defined in all three locations, the value provided through the command line will be used.

Command-Line Parameters
-----------------------

Example:

.. code-block:: bash

   web-novel-scraper show-novel-info \
     -t "My Novel" \
     --request-timeout 60

Environment Variables
---------------------

Example:

.. code-block:: bash

   export SCRAPER_REQUEST_TIMEOUT=60

Configuration File
------------------

Example:

.. code-block:: yaml

   request_config:
     request_timeout: 60

Using a Configuration File
--------------------------

.. code-block:: bash

   web-novel-scraper \
     --config-file scraper.yaml \
     show-novel-info \
     -t "My Novel"

Configuration Reference
-----------------------

See :doc:`../reference/config` for a complete list of available configuration options.