# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

project = 'Ananke'
copyright = '2023, Ananke Team'
author = 'Ananke Team'
version = ''
release = '0.3'

extensions = ['myst_parser']
myst_heading_anchors = 4

html_static_path = ['_static']

html_theme = 'sphinx_book_theme'
