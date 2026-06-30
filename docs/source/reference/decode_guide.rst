Decode Guide Reference
======================

This page describes the decode guide format.

The decode guide is a JSON file with one entry per host. Each entry defines how
the scraper extracts title, chapter content, TOC links, and optional pagination
links.

Where It Is Used
----------------

- Default file: ``web_novel_scraper/decode_guide/decode_guide.json``
- Custom file in CLI: ``--decode-guide-file /path/to/decode_guide.json``

Root Structure
--------------

The root JSON value must be a list.

.. code-block:: json

	 [
		 {
			 "host": "example.com",
			 "title": { ... },
			 "content": { ... },
			 "index": { ... }
		 }
	 ]

Each host is matched by exact string value (case-sensitive).

Top-Level Keys (Per Host Entry)
-------------------------------

Required keys
~~~~~~~~~~~~~

``host`` (string)
	Exact hostname used to pick this entry (for example ``novelbin.com``).

``title`` (object)
	Rules to extract chapter title from chapter HTML.

``content`` (object)
	Rules to extract chapter content from chapter HTML.

``index`` (object)
	Rules to extract chapter URLs from TOC HTML.

Optional keys
~~~~~~~~~~~~~

``next_page`` (object)
	Rules to extract the next TOC page URL when the TOC has pagination.

``title_in_content`` (``YES`` | ``NO`` | ``SEARCH``)
	Controls whether the chapter title is prepended to exported content.

	- ``YES``: always prepend title.
	- ``NO``: never prepend title.
	- ``SEARCH``: prepend only if the title is not already in content.

``has_pagination`` (boolean, default ``false``)
	Indicates if TOC pages are paginated for this host.

``chapters_in_descending_order`` (boolean, default ``false``)
	Set to true when chapter URLs are listed in descending order on the TOC page.

``pagination_in_descending_order`` (boolean, default ``false``)
    Set to true when TOC pages are listed in descending order.

``add_host_to_chapter`` (boolean, default ``false``)
	If true, each URL extracted from ``index`` is prefixed with
	``https://<host>``.

``toc_main_url_processor`` (boolean, default ``false``)
	Enables custom processing hook for TOC main URL before use.

Section Decoder Keys
--------------------

These keys are used inside ``title``, ``content``, ``index``, and ``next_page``.

Required shape
~~~~~~~~~~~~~~

Must be defined either:

- ``selector``
- or one or more selector parts: ``element``, ``id``, ``class``, ``attributes``

Key reference
~~~~~~~~~~~~~

``selector`` (string)
	Full CSS selector used by BeautifulSoup ``select()``.

``element`` (string)
	Tag name part used to build selector when ``selector`` is not provided.

``id`` (string)
	ID selector part used to build selector (becomes ``#id``).

``class`` (string)
	Class selector part used to build selector (becomes ``.class``).

``attributes`` (object)
	Attribute filters used to build selector. Example:
	``{"data-id": "123", "hidden": null}``.

``array`` (boolean)
	If true, returns all matched values as list. If false or omitted, returns the
	first match.

``extract`` (object)
	Defines what to extract from each matched element (text or attribute).

``use_custom_processor`` (boolean)
	Declares this section should rely on a custom processor. In this mode, this
	key should be the only key in that section.

Extract Keys
------------

``extract.type``
	Extraction mode:

	- ``text``: use text content.
	- ``attr``: use an HTML attribute.

``extract.key`` (string, required when ``type=attr``)
	Attribute name to extract (for example ``href``, ``src``).

Selector Fallback With XOR
--------------------------

If ``selector`` contains ``XOR``, selectors are tried left-to-right until one
returns elements.

.. code-block:: json

	 {
		 "selector": "div.primary p XOR div.fallback p",
		 "array": true
	 }

Defaults Summary
----------------

- ``title_in_content`` -> ``SEARCH``
- ``has_pagination`` -> ``false``
- ``add_host_to_chapter`` -> ``false``
- ``chapters_in_descending_order`` -> ``false``
- ``pagination_in_descending_order`` -> ``false``

Minimal Valid Example
---------------------

.. code-block:: json

	 [
		 {
			 "host": "example.com",
			 "title_in_content": "SEARCH",
			 "has_pagination": false,
			 "title": {
				"selector": "h1.chapter-title",
				"extract": {
                    "type": "text"
                }
			 },
			 "content": {
				 "selector": "div.chapter-content p",
				 "array": true
			 },
			 "index": {
				 "selector": "ul.chapter-list a",
				 "array": true,
				 "extract": {
                    "type": "attr",
                    "key": "href"
                }
			 }
		 }
	 ]

Example With Pagination
-----------------------

.. code-block:: json

	 [
		 {
			 "host": "example.com",
			 "has_pagination": true,
			 "title": {
				 "selector": "h1.chapter-title",
				 "extract": {
                    "type": "text"
                 }
			 },
			 "content": {
				 "selector": "div.chapter-content p",
				 "array": true
			 },
			 "index": {
				 "selector": "ul.chapter-list a",
				 "array": true,
				 "extract": {
                    "type": "attr",
                    "key": "href"
                 }
			 },
			 "next_page": {
				 "selector": "a.next",
				 "array": false,
				 "extract": {
                    "type": "attr",
                    "key": "href"
                 }
			 }
		 }
	 ]

