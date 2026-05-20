# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

project = 'Ananke'
copyright = '2025, Ananke Team'
author = 'Ananke Team'
version = ''
release = '0.6'

extensions = ['myst_parser']
myst_heading_anchors = 4

html_static_path = ['_static']

html_theme = 'sphinx_book_theme'

html_theme_options = {
    'extra_footer': '<div><a href="https://www2.htw-dresden.de/~fjeme691/flemming/impressum.html" target="_blank" rel="noopener noreferrer">Imprint</a> &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;<a href="https://www2.htw-dresden.de/~fjeme691/flemming/barrierefreiheit.html" target="_blank" rel="noopener noreferrer">Accessibility</a> &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;<a href="https://www2.htw-dresden.de/~fjeme691/flemming/datenschutz.html" target="_blank" rel="noopener noreferrer">Data privacy</a></div>',
}