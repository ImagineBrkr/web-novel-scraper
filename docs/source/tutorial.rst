Tutorial
========

Installation
------------
To install the **Web Novel Scraping CLI**, you can use ``pip``:

.. code-block:: bash

   pip install web-novel-scraper

Alternatively, you can install it manually:

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/ImagineBrkr/web-novel-scraper.git

2. Navigate to the project directory:

   .. code-block:: bash

      cd web-novel-scraper

3. Install the project:

   .. code-block:: bash

      python -m pip install .

4. Run the CLI tool:

   .. code-block:: bash

      web-novel-scraper

Creating a Novel
----------------
You can create a new novel by specifying a title and a Table of Contents (TOC). The TOC can come from a URL or from a local HTML file.

.. code-block:: bash

   # Create a novel from a TOC URL
   web-novel-scraper create-novel --title "Novel 1" \
       --toc-main-url "https://novelbin.me/novela-1" \
       --host "novelbin.me"

In most cases, the ``--host`` option is automatically detected from the ``toc-main-url``, so it can often be omitted. However, if you want to load a TOC from a local HTML file:

.. code-block:: bash

   # Create a novel from a local HTML file
   web-novel-scraper create-novel --title "Novel 1" \
       --toc-html "novela_1_toc.html" \
       --host "novelbin.me"

By default, the novel is saved to ``%AppData%/ImagineBrkr/web-novel-scraper`` (on Windows). You can specify a different directory with the ``--novel-base-dir`` option or set an environment variable:

.. code-block:: bash

   # Store the novel in a custom directory
   web-novel-scraper create-novel --title "Novel 1" \
       --toc-main-url "https://novelbin.me/novela-1" \
       --novel-base-dir "D:/novelas"

   # Or set the environment variable instead:
   export SCRAPER_BASE_DATA_DIR=D:/novelas

.. note::

   If you choose a custom directory, you must use the same directory in **all** subsequent commands that reference this novel, unless you rely on the environment variable.

For all available options you can specify when creating a novel, refer to :ref:`create-novel Documentation <create-novel>` .

Syncing the TOC
---------------
The TOC may change over time (new chapters, etc.). To update your local list of chapters, simply run:

.. code-block:: bash

   web-novel-scraper sync-toc --title "Novel 1"

This will fetch all chapter URLs in the TOC and create local chapter records (initially containing only the URL). You can then view the TOC or chapter list:

.. code-block:: bash

   web-novel-scraper show-toc --title "Novel 1"
   web-novel-scraper show-chapters --title "Novel 1"

Obtaining Chapters
------------------
Fetching and storing chapter content locally can be time-consuming, but it only needs to be done once. Use:

.. code-block:: bash

   web-novel-scraper request-all-chapters --title "Novel 1"

This command iterates through all chapters, requests the HTML content, and saves it locally. Even if you skip this step, the next command (generating the final EPUB) will attempt to fetch any missing chapters on the fly.

Generating the EPUB
-------------------
Once chapters have been retrieved, you can generate an EPUB:

.. code-block:: bash

   web-novel-scraper save-novel-to-epub --title "Novel 1"

By default, each EPUB contains up to 100 chapters. You can locate the folder where EPUB files are saved by running:

.. code-block:: bash

   web-novel-scraper show-novel-dir --title "Novel 1"

This command displays the local path where the novel and its generated EPUB files are stored.