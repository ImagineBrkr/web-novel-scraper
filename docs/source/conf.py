# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
# We import from the root directory the web_novel_scraper module
import sys
sys.path.append('../..')
from web_novel_scraper.version import __version__

project = 'Web Novel Scraper'
copyright = '2025, ImagineBrkr'
author = 'ImagineBrkr'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx_click',
]

templates_path = ['_templates']
exclude_patterns = []

version = __version__
release = __version__

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False, 
    "titles_only": False,
    "includehidden": True,
}
# html_sidebar = ['globaltoc.html', 'sourcelink.html', 'searchbox.html']
html_static_path = ['_static']
