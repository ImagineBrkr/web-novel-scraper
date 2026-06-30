Avoid Rate Limit Blocks
=======================

If a site suddenly starts blocking your IP because of too many requests,
increase the time between requests using ``--request-time-between-requests``.

This slows down scraping and helps reduce rate-limit or anti-bot blocks.

Example
-------

.. code-block:: bash

	 web-novel-scraper \
		 --request-time-between-requests 10 \
		 request-all-chapters \
		 -t "My Novel"

``10`` means waiting 10 seconds between each request. Increase it further if the
site is still blocking requests.

This option can also be configured through environment variables or a config
file, see :doc:`../reference/config`.
