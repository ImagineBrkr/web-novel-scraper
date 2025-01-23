Configuration Options
=====================

You can configure the CLI tool behavior using environment variables.

Environment Variables
---------------------

The Web Novel Scraping CLI uses the following environment variables for configuration:

- `SCRAPER_LOGGING_LEVEL`: Sets the logging level for the application. By default, no logs are written. It accepts the following log levels: (DEBUG, INFO, WARNING, ERROR, CRITICAL).
  
.. code-block:: bash

    export SCRAPER_LOGGING_LEVEL=INFO

- `SCRAPER_LOGGING_FILE`: Specifies the file where logs will be written. By default, logs are written to the terminal.
  
.. code-block:: bash

    export SCRAPER_LOGGING_FILE=/path/to/logfile.log

- `SCRAPER_BASE_DATA_DIR`: Defines the base directory for storing novel data. The default is the user data directory.
  
.. code-block:: bash

    export SCRAPER_BASE_DATA_DIR=/path/to/data/dir

- `SCRAPER_FLARESOLVER_URL`: URL for the FlareSolverr service. The default is `http://localhost:8191/v1`.
  
.. code-block:: bash

    export SCRAPER_FLARESOLVER_URL=http://localhost:8191/v1
