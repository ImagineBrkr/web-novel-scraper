Web Novel Scraper CLI
====================

Why Use Web Novel Scraper?
-------------------------

- **Read Offline**: Download your favorite novels and read them anywhere, even without internet
- **Device Friendly**: EPUB format optimized for e-readers and mobile devices
- **Resource Efficient**: Smart caching system prevents unnecessary downloads
- **Server Friendly**: Prevents accidental server overloads
- **Simple Interface**: Basic and direct commands for a hassle-free experience
- **Automatic Organization**: Keep your novels organized and easy to find

Main Features
------------

- Downloads and converts web novels to EPUB format
- Smart caching: downloads chapters only once
- Simple and straightforward command-line interface
- Support for multiple web novel sites

Quick Tutorial
-------------

1. Installation
~~~~~~~~~~~~~~

.. code-block:: bash

    pip install web-novel-scraper

2. Download Your First Novel
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Create a new novel**:

.. code-block:: bash

    web-novel-scraper create-novel -t "My First Novel" --toc-main-url "https://novelbin.me/novel/my-novel/toc"

2. **Convert to EPUB**:

.. code-block:: bash

    web-novel-scraper save-novel-to-epub -t "My First Novel" --sync-toc

3. **Find your files**:

.. code-block:: bash

    web-novel-scraper show-novel-dir -t "My First Novel"

3. Additional Options
~~~~~~~~~~~~~~~~~~~

- **Add metadata**:

.. code-block:: bash

    web-novel-scraper set-metadata -t "My First Novel" --author "Author" --language "en"

- **Add cover image**:

.. code-block:: bash

    web-novel-scraper set-cover-image -t "My First Novel" --cover "path/to/image.jpg"

- **View novel information**:

.. code-block:: bash

    web-novel-scraper show-novel-info -t "My First Novel"

Supported Sites
--------------

- Novelbin
- Novelhi
- Novellive
- Royalroad
- GenesisStudio
- HostedNovel
- ScribbleHub
- NovelCool
- FreeWebNovel
- Foxaholic
- Fanmtl
- Pandamtl

Full Documentation
----------------

For a detailed guide, advanced use cases, and complete command reference, visit:
`Web Novel Scraper Documentation <https://web-novel-scraper.readthedocs.io/stable/>`_

Responsible Usage Note
--------------------

Please use this tool responsibly and respect the terms of service and rate limits of the web novel sites.
