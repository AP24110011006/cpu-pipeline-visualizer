"""Repository intelligence: structural inspection, dependency graph, and symbol search."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class RepoInspector:
    """Inspects repository structure, AST imports, and module responsibilities."""

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        if root_dir is None:
            # Default to repo root (one level up from agents/)
            self.root = Path(__file__).resolve().parent.parent
        else:
            self.root = Path(root_dir).resolve()

    def get_module_responsibilities(self) -> Dict[str, str]:
        """Map codebase subdirectories and core files to engineering responsibilities."""
        return {
            "simulator/": "5-stage MIPS pipeline simulation, cycle execution, parser, reference CPU",
            "simulator/analytics/": "Hazard analytics, stall telemetry, forwarding paths, and conservation laws",
            "ui/": "Streamlit engineering studio dashboard, Plotly diagrams, and design tokens",
            "ui/pages/": "11 modular workspace views, cycle inspectors, and team progress tracking",
            "bots/": "5 automated verification bots (testing, differential verifier, scheduler, stress, hazard)",
            "agents/": "Full Stack Engineering Agent: repo intelligence, planning, code execution, verification",
            "tests/": "Automated pytest regression suites covering all CPU architectural features",
            "docs/": "Architectural documentation, hazard accounting, team roles, and user guides",
            "examples/": "MIPS assembly workloads (arithmetic, hazards, memory, loops, stress)",
        }

    def list_files(self, relative_subdirs: Optional[List[str]] = None) -> List[str]:
        """List relevant source files (.py, .s, .md) ignoring caches and virtualenvs."""
        ignore_dirs = {
            ".git", ".pytest_cache", "__pycache__", "venv", ".venv",
            "env", "build", "dist", ".system_generated"
        }
        files: List[str] = []

        subdirs = relative_subdirs or ["simulator", "ui", "bots", "agents", "tests", "examples", "docs"]
        for subdir in subdirs:
            p = self.root / subdir
            if not p.exists() or not p.is_dir():
                continue
            for item in p.rglob("*"):
                if item.is_file() and not any(part in ignore_dirs for part in item.parts):
                    if item.suffix in {".py", ".s", ".md", ".txt", ".bat", ".ini"}:
                        files.append(str(item.relative_to(self.root)).replace("\\", "/"))

        # Add top-level root files
        for item in self.root.iterdir():
            if item.is_file() and item.suffix in {".py", ".md", ".txt", ".bat", ".ini"}:
                files.append(item.name)

        return sorted(files)

    def read_file(self, relative_path: str) -> str:
        """Safely read a file within the workspace root."""
        clean_path = (self.root / relative_path).resolve()
        if not clean_path.is_relative_to(self.root):
            raise PermissionError(f"Access denied: path {relative_path} escapes workspace root.")
        if not clean_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        return clean_path.read_text(encoding="utf-8", errors="replace")

    def search_code(self, pattern: str, subdirs: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search source code for a text pattern."""
        results: List[Dict[str, Any]] = []
        files = self.list_files(subdirs)
        low_pat = pattern.lower()

        for fpath in files:
            if not fpath.endswith((".py", ".s", ".md")):
                continue
            try:
                content = self.read_file(fpath)
                lines = content.splitlines()
                for idx, line in enumerate(lines, start=1):
                    if low_pat in line.lower():
                        results.append({
                            "file": fpath,
                            "line": idx,
                            "content": line.strip(),
                        })
            except Exception:
                continue
        return results

    def analyze_imports(self) -> Dict[str, List[str]]:
        """Parse Python files with AST to discover internal import dependencies."""
        dependencies: Dict[str, Set[str]] = {}
        files = [f for f in self.list_files() if f.endswith(".py")]

        for fpath in files:
            dependencies[fpath] = set()
            try:
                code = self.read_file(fpath)
                tree = ast.parse(code, filename=fpath)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            root_pkg = alias.name.split(".")[0]
                            if root_pkg in {"simulator", "ui", "bots", "agents"}:
                                dependencies[fpath].add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            root_pkg = node.module.split(".")[0]
                            if root_pkg in {"simulator", "ui", "bots", "agents"}:
                                dependencies[fpath].add(node.module)
            except Exception:
                continue

        return {k: sorted(list(v)) for k, v in dependencies.items()}

    def check_broken_imports(self) -> List[str]:
        """Scan Python files and verify that referenced local modules exist."""
        broken: List[str] = []
        import_map = self.analyze_imports()

        for source_file, imported_modules in import_map.items():
            for mod in imported_modules:
                mod_rel_py = mod.replace(".", "/") + ".py"
                mod_rel_init = mod.replace(".", "/") + "/__init__.py"
                path_py = self.root / mod_rel_py
                path_init = self.root / mod_rel_init
                if not path_py.exists() and not path_init.exists():
                    broken.append(f"{source_file}: import '{mod}' cannot be resolved on disk.")

        return broken
