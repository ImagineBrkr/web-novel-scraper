Using a Custom Decode Guide
===========================

Web Novel Scraper uses decode guides to extract content from supported websites.

If a website is not currently supported, you can create your own decode guide and instruct the CLI to use it.

.. code-block:: bash

   web-novel-scraper \
     --decode-guide-file my_decode_guide.yaml \
     create-novel \
     -t "My Novel" \
     --toc-main-url "https://example.com"

The custom decode guide will be used instead of the default one.

This allows advanced users to add support for additional websites without modifying the application itself.
The decode guide format is documented in :doc:`../reference/decode_guide`.