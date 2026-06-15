"""Sphinx configuration for the blanket documentation."""

from importlib.metadata import version as _get_version

project = "blanket"
author = "Larry Hastings"
copyright = "2025-2026, Larry Hastings"
release = _get_version("blanket")
version = ".".join(release.split(".")[:2])

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.mermaid",
    "sphinx_copybutton",
]

myst_enable_extensions = [
    "alert",
    "colon_fence",
    "deflist",
    "fieldlist",
    "attrs_inline",
    "linkify",
    "smartquotes",
]
myst_heading_anchors = 3
myst_fence_as_directive = ["mermaid"]

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_attr_annotations = True

autodoc_member_order = "groupwise"
autodoc_typehints = "none"
autoclass_content = "both"
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
}

always_use_bars_union = True
always_document_param_types = True
typehints_defaults = "comma"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "bytecode": ("https://bytecode.readthedocs.io/en/stable", None),
}

html_theme = "furo"
html_title = "blanket"
html_theme_options = {
    "source_repository": "https://github.com/larryhastings/blanket/",
    "source_branch": "master",
    "source_directory": "docs/",
    "navigation_with_keys": True,
    "top_of_page_buttons": ["view", "edit"],
}
