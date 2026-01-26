"""Sphinx configuration."""

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
html_theme = "shibuya"
