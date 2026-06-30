Moving Novels Between Directories
=================================

A novel is completely self-contained inside its novel directory.

By default, the directory name matches the novel title, but the exact location can be displayed using:

.. code-block:: bash

   web-novel-scraper show-novel-dir \
     -t "My Novel"

Moving a Novel
--------------

To move a novel to another location:

1. Locate the novel directory.
2. Copy or move the entire directory.
3. Preserve all files and subdirectories.

For example:

.. code-block:: text

   My Novel/
   ├── data/
   │   ├── main.json
   │   └── chapters/
   └── ...

After moving the directory, tell the CLI where the novel is located using ``--novel-base-dir``.

.. code-block:: bash

   web-novel-scraper \
     --novel-base-dir "/new/location" \
     show-novel-info \
     -t "My Novel"

The ``--novel-base-dir`` option must be provided whenever you interact with that novel unless the new location is configured as your default novels directory.