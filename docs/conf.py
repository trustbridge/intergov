#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os


cwd = os.getcwd()  # expected $PROJECT_ROOT/docs/
project_root = os.path.dirname(cwd)
sys.path.insert(0, project_root)
import intergov  # noqa


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
