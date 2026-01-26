"""Sphinx configuration."""
import os
import sys
sys.path.insert(0, os.path.abspath("../src"))

project = "Facial Recognition"
author = "Aimine Meddeb"
copyright = "2026, Aimine Meddeb"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
