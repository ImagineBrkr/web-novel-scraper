Basic Usage
===========

Managing Metadata
------------------------

Metadata is used when exporting novels and can be updated at any time.

You can set information such as the author, language, description, and publication dates.

.. code-block:: bash

   web-novel-scraper set-metadata 
   -t "My First Novel" 
   --author "Author Name" 
   --language "en"

To view the current metadata:

.. code-block:: bash

   web-novel-scraper show-metadata 
   -t "My First Novel"

Managing Tags
------------------------

Tags can be used to organize and classify novels.

Add one or more tags:

.. code-block:: bash

   web-novel-scraper add-tags 
   -t "My First Novel" 
   --tag fantasy 
   --tag action

Remove tags:

.. code-block:: bash

   web-novel-scraper remove-tags 
   -t "My First Novel" 
   --tag action

Show all tags:

.. code-block:: bash

   web-novel-scraper show-tags 
   -t "My First Novel"

Managing Covers
------------------------

A custom cover image can be attached to a novel and will be included in supported export formats.

Currently, only JPG images are supported.

.. code-block:: bash

   web-novel-scraper set-cover-image 
   -t "My First Novel" 
   --cover-image "/path/to/cover.jpg"

Downloading Chapters
------------------------

The export commands automatically download missing chapters before generating the output files.

For example:

.. code-block:: bash

   web-novel-scraper save-novel-to-epub 
   -t "My First Novel" 
   --sync-toc

However, exports will fail if a chapter cannot be downloaded.

For large novels, it is recommended to download all chapters first:

.. code-block:: bash

   web-novel-scraper request-all-chapters 
   -t "My First Novel"

Unlike the export commands, `request-all-chapters` continues downloading even when individual chapters fail. This makes it easier to identify and retry problematic chapters before exporting.

Syncing TOC
------------

The TOC may change over time as new chapters are updated. To sync your local list of chapters you can use:

.. code-block:: bash

   web-novel-scraper sync-toc --title "Novel 1"

Changing the Novel Directory
------------------------------------

By default, novels are stored in the configured novels directory.

To store a specific novel in a different location, use `--novel-base-dir` when creating the novel:

.. code-block:: bash

   web-novel-scraper create-novel 
   --novel-base-dir "/custom/location" 
   -t "My First Novel" 
   --toc-main-url "https://example.com/toc"

You must provide the same option in every command that interacts with that novel:

.. code-block:: bash

   web-novel-scraper show-novel-info 
   --novel-base-dir "/custom/location" 
   -t "My First Novel"

Changing the Base Directory for Multiple Novels
------------------------------------------------------------

To use a different base directory for all novels, use `--base-novels-dir`.

.. code-block:: bash

   web-novel-scraper create-novel 
   --base-novels-dir "/novels" 
   -t "My First Novel" 
   --toc-main-url "https://example.com/toc"

As with `--novel-base-dir`, the same option must be provided in every command that accesses novels stored in that location.

.. code-block:: bash

   web-novel-scraper show-novel-info 
   --base-novels-dir "/novels" 
   -t "My First Novel"

Additional configuration methods are described in the Advanced Usage section.

Exporting Novels
-----------------

Novels can be exported to multiple formats, including EPUB, HTML, TXT, and other supported formats.

See :ref:`installation` for the complete list of available exporters.

Example:

.. code-block:: bash

   web-novel-scraper save-novel-to-epub 
   -t "My First Novel"

You can also export only a portion of the novel.

Export chapters 100 through 500:

.. code-block:: bash

   web-novel-scraper save-novel-to-epub 
   -t "My First Novel" 
   --start-chapter 100 
   --end-chapter 500

Control how many chapters are included in each generated book (by default 100):

.. code-block:: bash

   web-novel-scraper save-novel-to-epub 
   -t "My First Novel" 
   --chapters-by-book 200
