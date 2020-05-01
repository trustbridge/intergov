#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

cwd = os.getcwd()
project_root = os.path.dirname(cwd)
# modules = ('intergov',)
# for module in modules:
#    mod = os.path.join(project_root, module)
sys.path.insert(0, project_root)

# import intergov  # noqa
# TODO: fix this hack
class intergov:
    __version__ = '0.1.0'


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.graphviz',
    'sphinxcontrib.plantuml',
    'sphinxcontrib.spelling'
]

spelling_lang='en_US'
spelling_word_list_filename='wordlist.txt'

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = u'Intergov Ledger'
copyright = u"2019, Commonwealth of Australia"
version = intergov.__version__
release = intergov.__version__
exclude_patterns = ['_build', '.venv']
pygments_style = 'sphinx'
html_theme = 'alabaster'  #'default'
html_static_path = ['_static']
htmlhelp_basename = 'intergov_ledgerdoc'

latex_elements = {
    'papersize': 'a4paper',
}
latex_documents = [
    ('index', 'intergov_ledger.tex',
     u'Intergov Ledger Documentation',
     u'Chris Gough', 'manual'),
]

man_pages = [
    ('index', 'intergov_ledger',
     u'Intergov Ledger Documentation',
     [u'Chris Gough'], 1)
]

texinfo_documents = [
    ('index', 'intergov_ledger',
     u'Intergov Ledger Documentation',
     u'Chris Gough',
     'intergov_ledger',
     'One line description of project.',
     'Miscellaneous'),
]
