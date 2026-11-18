"""Configuration de Sphinx pour la documentation de la bibliothèque bujo."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

project = "Bullet Journal"
copyright = "2026, Équipe Bullet Journal"
author = "Équipe Bullet Journal"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

language = "fr"

html_theme = "alabaster"
html_static_path = ["_static"]

autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "special-members": "__init__",
    "show-inheritance": True,
}
