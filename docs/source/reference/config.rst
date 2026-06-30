Config Reference
================

This page documents how configuration values are resolved and what
each configuration key does.

Ways to Provide Configuration
-----------------------------

You can provide configuration values using these sources:

1. Config File
2. Environment Variables
3. CLI Parameters

Config File
~~~~~~~~~~~

Configuration can be loaded from a JSON file. The scraper resolves the config
file location in this order:

1. ``config_file`` CLI parameter
2. ``SCRAPER_CONFIG_FILE`` environment variable
3. Internal default path (``$HOME/.config/web-novel-scraper/config.json`` on Linux)

If file loading fails (missing, empty, malformed), the scraper falls back to
an empty file config.

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Any supported key can be provided through environment variables such as
``SCRAPER_BASE_NOVELS_DIR`` or ``SCRAPER_REQUEST_TIMEOUT``.

CLI Parameters
~~~~~~~~~~~~~~

CLI parameters are passed directly in commands and have the highest priority. For more information, see :doc:`/reference/commands`.

Precedence
----------

When a value exists in more than one source, this precedence is applied:

1. CLI Parameter
2. Environment Variable
3. Config File
4. Default (Host)
5. Default

Default (host) values come from ``web_novel_scraper/resources/host_config.json``
and have some default settings for different hosts like using FlareSolverr or a
bigger timeout.

Configuration Schema
--------------------

Top-level keys:

- ``base_novels_dir`` (string)
- ``decode_guide_file`` (string)
- ``request_config`` (object)

``request_config`` keys:

- ``force_flaresolver`` (bool)
- ``flaresolver_url`` (string)
- ``request_timeout`` (int)
- ``request_retries`` (int)
- ``request_time_between_retries`` (int)
- ``request_cookies`` (dict)

Options Detail
--------------

``base_novels_dir``
~~~~~~~~~~~~~~~~~~~

- Type: string path
- Default: ``platformdirs.user_data_dir("web-novel-scraper", "web-novel-scraper")``
- Purpose: base directory where novel folders are stored.
- Sources:
	- ``parameter: base_novels_dir``
	- ``env: SCRAPER_BASE_NOVELS_DIR``
	- ``config file: base_novels_dir``

``decode_guide_file``
~~~~~~~~~~~~~~~~~~~~~

- Type: string path
- Default: bundled decode guide path
	``web_novel_scraper/decode_guide/decode_guide.json``
- Purpose: file used to load host extraction rules.
- Sources:
	- ``parameter: decode_guide_file``
	- ``env: SCRAPER_DECODE_GUIDE_FILE``
	- ``config file: decode_guide_file``

``request_config.force_flaresolver``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Type: bool
- Default: ``false``
- Purpose: force requests through FlareSolverr.
- Accepted bool-like values:
	``true/false``, ``1/0``, ``yes/no`` (case-insensitive), plus native bool/int.
- Sources:
	- ``parameter: force_flaresolver``
	- ``env: SCRAPER_FORCE_FLARESOLVER``
	- ``config file: request_config.force_flaresolver``
	- ``default(host): request_config.force_flaresolver``

``request_config.flaresolver_url``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Type: string URL
- Default: ``http://localhost:8191``
- Purpose: FlareSolverr endpoint.
- Sources:
	- ``env: SCRAPER_FLARESOLVER_URL``
	- ``config file: request_config.flaresolver_url``

``request_config.request_timeout``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Type: int
- Default: ``20``
- Purpose: request timeout in seconds.
- Sources:
	- ``parameter: request_timeout``
	- ``env: SCRAPER_REQUEST_TIMEOUT``
	- ``config file: request_config.request_timeout``
	- ``default(host): request_config.request_timeout``

``request_config.request_retries``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Type: int
- Default: ``3``
- Purpose: max retries per request.
- Sources:
	- ``parameter: request_retries``
	- ``env: SCRAPER_REQUEST_RETRIES``
	- ``config file: request_config.request_retries``
	- ``default(host): request_config.request_retries``

``request_config.request_time_between_retries``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Type: int
- Default: ``3``
- Purpose: seconds to wait between retries if request fails.
- Sources:
	- ``parameter: request_time_between_retries``
	- ``env: SCRAPER_REQUEST_TIME_BETWEEN_RETRIES``
	- ``config file: request_config.request_time_between_retries``
	- ``default(host): request_config.request_time_between_retries``

``request_config.request_cookies``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Type: dict
- Default: ``{}``
- Purpose: cookies sent with requests, useful for sites requiring specific
	session or preference cookies.
- Sources:
	- ``config file: request_config.request_cookies``
	- ``default(host): request_config.request_cookies``


Config File Example
---------------------------

.. code-block:: json

	 {
		 "base_novels_dir": "/home/user/novels",
		 "decode_guide_file": "/home/user/custom_decode_guide.json",
		 "request_config": {
			 "force_flaresolver": true,
			 "flaresolver_url": "http://localhost:8191",
			 "request_timeout": 30,
			 "request_retries": 5,
			 "request_time_between_retries": 4,
			 "request_cookies": {
				 "custom_toc": "10000"
			 }
		 }
	 }
