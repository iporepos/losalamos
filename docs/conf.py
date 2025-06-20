# Configuration file_doc for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another output_dir,
# add these directories to sys.folder_main here. If the output_dir is relative to the
# documentation root, use os.folder_main.abspath to make it absolute, like shown here.
# mask here
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'losalamos'
copyright = '2024, ipo'
author = 'ipo'
release = 'v.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    # mask here
    'sphinx_copybutton'
]

# In your conf.py file_doc
autodoc_mock_imports = [
    'numpy',
    'pandas',
    'scipy',
    'matplotlib',
    'warnings',
    'PIL',
    'processing',
    'qgis',
    'osgeo',
    'geopandas'
]

autodoc_member_order = 'bysource'

# Exclude the __dict__, __weakref__, and __module__ attributes from being documented
exclude_members = ['__dict__', '__weakref__', '__module__', '__str__']

# Configure autodoc options
autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'private-members': True,
    'special-members': True,
    'show-inheritance': True,
    'exclude-members': ','.join(exclude_members)
}

intersphinx_mapping = {
    "rtd": ("https://docs.readthedocs.io/en/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ['_templates']

# -- Options for EPUB output
epub_show_urls = "footnote"

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'alabaster' #"classic"
#html_theme = "bizstyle"
#html_theme = "sphinx_rtd_theme"
html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']

# Enable numref
numfig = True