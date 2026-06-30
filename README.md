# Web Novel Scraper CLI
---

Download web novels from supported websites and export them as EPUB, HTML or any other supported formats for offline reading, see below for a full list of the supported sites.

The HTML Files are downloaded and stored locally to avoid unnecessary requests, making repeated updates faster and reducing load on source websites.

Full documentation, configuration options, and command reference are available in the **[documentation site](https://web-novel-scraper.readthedocs.io/stable/)**.

## Features
---

* Download web novels from multiple supported sources
* Export novels to multiple supported formats (EPUB, HTML, TXT,...)
* Incremental chapter downloads through local caching
* Simple command-line interface
* Metadata management (title, author, language, etc.)
* Custom cover image support
* Local novel organization and storage

## Quickstart
---

### 1. Install

You can install it in your machine using uv, pip or pipx.

```bash
# On macOS and Linux.
curl -LsSf https://uvx.sh/web-novel-scraper/install.sh | sh

# On Windows.
powershell -ExecutionPolicy ByPass -c "irm https://uvx.sh/web-novel-scraper/install.ps1 | iex"

# For a specific version.
curl -LsSf https://uvx.sh/web-novel-scraper/2.9.1/install.sh | sh
powershell -c "irm https://uvx.sh/web-novel-scraper/2.9.1/install.ps1 | iex"

# With pip
pip install web-novel-scraper

# With pipx
pipx install web-novel-scraper
```

### 1.5. Setup Flaresolverr

A lot of sites use CloudFlare Protection to avoid bots, to bypass it you need to install **[FlareSolverr](https://github.com/FlareSolverr/FlareSolverr/)**. This link shows the complete install instructions.

If you are using a differente Port or Hostname for FlareSolverr (by default localhost:8191), you can configure it with the environment variable `FLARESOLVER_URL`:

```
# Linux
export FLARESOLVER_URL=http://new-host:8080

# Windows
setx FLARESOLVER_URL "http://new-host:8080"
```

### 2. Create a Novel

Create a new local novel project from a table-of-contents URL:

```bash
web-novel-scraper create-novel \
  -t "My First Novel" \
  --toc-main-url "https://novelbin.me/novel/my-novel/toc"
```

### 3. Export to EPUB

Download missing chapters and generate an EPUB file:

```bash
web-novel-scraper save-novel-to-epub \
  -t "My First Novel" \
  --sync-toc
```

### 4. View the Novel Directory

```bash
web-novel-scraper show-novel-dir \
  -t "My First Novel"
```

## Common Commands

### Set Metadata
The metadata will be included in 

```bash
web-novel-scraper set-metadata \
  -t "My First Novel" \
  --author "Author Name" \
  --language "en"
```

### Set Cover Image

```bash
web-novel-scraper set-cover-image \
  -t "My First Novel" \
  --cover "path/to/cover.jpg"
```

### Show Novel Information

```bash
web-novel-scraper show-novel-info \
  -t "My First Novel"
```

## Documentation

Useful documentation links:

* Main docs: https://web-novel-scraper.readthedocs.io/stable/
* Commands reference: https://web-novel-scraper.readthedocs.io/stable/reference/commands.html
* Config reference: https://web-novel-scraper.readthedocs.io/stable/reference/config.html
* Supported sites: https://web-novel-scraper.readthedocs.io/stable/reference/supported_sites.html
* Supported export formats: https://web-novel-scraper.readthedocs.io/stable/reference/supported_export_formats.html
