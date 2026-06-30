Installation
============

Requirements
------------

* Python 3.10 or newer
* Internet connection
* Optional: FlareSolverr for Cloudflare-protected websites

Install the CLI
---------------

You can install Web Novel Scraper using ``uv``, ``pip``, or ``pipx``.

Using uv
^^^^^^^^

.. code-block:: bash

   # Linux / macOS
   curl -LsSf https://uvx.sh/web-novel-scraper/install.sh | sh

   # Windows
   powershell -ExecutionPolicy ByPass -c "irm https://uvx.sh/web-novel-scraper/install.ps1 | iex"

Installing a specific version:

.. code-block:: bash

   curl -LsSf https://uvx.sh/web-novel-scraper/2.9.1/install.sh | sh

   powershell -c "irm https://uvx.sh/web-novel-scraper/2.9.1/install.ps1 | iex"

Using pip
^^^^^^^^^

.. code-block:: bash

   pip install web-novel-scraper

Using pipx
^^^^^^^^^^

.. code-block:: bash

   pipx install web-novel-scraper

Verify Installation
-------------------

Verify that the CLI was installed correctly:

.. code-block:: bash

   web-novel-scraper version

You should see the installed version displayed in the terminal.

FlareSolverr Setup (Optional)
-----------------------------

Some supported websites use Cloudflare protection. To access them, install and run FlareSolverr.
You can find the installation instructions for FlareSolverr at https://github.com/FlareSolverr/FlareSolverr

If FlareSolverr is running on a different host or port than the default
(``http://localhost:8191``), configure the URL using the
``FLARESOLVER_URL`` environment variable.

Linux/macOS:

.. code-block:: bash

   export FLARESOLVER_URL=http://new-host:8080

Windows:

.. code-block:: powershell

   setx FLARESOLVER_URL "http://new-host:8080"