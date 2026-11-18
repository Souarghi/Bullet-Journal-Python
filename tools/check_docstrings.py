"""Contrôle CI : présence des docstrings sur l'API publique du paquet."""

import ast
import pathlib
import sys


def check(paths: list[str]) -> int:
    """Retourne 0 si toute l'API publique du paquet est documentée."""
    missing: list[str] = []
    for path in paths:
        for file in sorted(pathlib.Path(path).rglob("*.py")):
            tree = ast.parse(file.read_text(encoding="utf-8"))
            if not ast.get_docstring(tree):
                missing.append(f"{file}: module")
            for node in ast.walk(tree):
                public = isinstance(
                    node,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                ) and not node.name.startswith("_")
                if public and not ast.get_docstring(node):
                    missing.append(f"{file}:{node.lineno} {node.name}")
    for item in missing:
        print(f"Docstring manquante : {item}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(check(sys.argv[1:] or ["bujo"]))
