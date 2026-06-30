# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
# We import from the root directory the web_novel_scraper module
import sys

sys.path.append("../..")
from importlib.metadata import version

__version__ = version("web-novel-scraper")

project = "Web Novel Scraper"
copyright = "2026, ImagineBrkr"
author = "ImagineBrkr"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx_click", "sphinx_rtd_dark_mode"]

templates_path = ["_templates"]
exclude_patterns = []

version = __version__
release = __version__

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "titles_only": False,
    "includehidden": True,
}
# html_sidebar = ['globaltoc.html', 'sourcelink.html', 'searchbox.html']
html_static_path = ["_static"]
