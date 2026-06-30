Quick Start
===========

The basic workflow is:

1. Create a novel
2. Synchronize the table of contents
3. Download chapters
4. Export the novel

Create a Novel
--------------

Create a new local novel project from a table-of-contents URL.

.. code-block:: bash

   web-novel-scraper create-novel \
     -t "My First Novel" \
     --toc-main-url "https://novelbin.me/novel/my-novel/toc"

This command creates the novel directory locally.

Export a Novel
--------------

The simplest way to download missing chapters and generate an EPUB file is:

.. code-block:: bash

   web-novel-scraper save-novel-to-epub \
     -t "My First Novel" \
     --sync-toc

The command will:

* Synchronize the table of contents
* Download any missing chapters
* Generate EPUB files

View the Novel Directory
------------------------

To see where the novel files are stored:

.. code-block:: bash

   web-novel-scraper show-novel-dir \
     -t "My First Novel"

Manage Metadata
---------------

Add metadata such as author and language:

.. code-block:: bash

   web-novel-scraper set-metadata \
     -t "My First Novel" \
     --author "Author Name" \
     --language "en"

Set a Cover Image
-----------------

Attach a custom cover image to the novel:

.. code-block:: bash

   web-novel-scraper set-cover-image \
     -t "My First Novel" \
     --cover-image "/path/to/cover.jpg"

Show Novel Information
----------------------

Display the current novel configuration and metadata:

.. code-block:: bash

   web-novel-scraper show-novel-info \
     -t "My First Novel"

Next Steps
----------

Continue with:

* :doc:`./basic_usage`
* :doc:`./advanced_usage/index`
