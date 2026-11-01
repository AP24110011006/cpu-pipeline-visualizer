"""Foundation integrity tests verifying core environment and configuration."""

from pathlib import Path
import sys


def test_python_version_compatible():
    """Verify running on Python 3.10+."""
    assert sys.version_info >= (3, 10), "Requires Python 3.10 or newer"


def test_requirements_file_exists():
    """Verify requirements.txt is present and readable."""
    req_file = Path(__file__).resolve().parent.parent / "requirements.txt"
    assert req_file.exists(), "requirements.txt must exist"
    content = req_file.read_text(encoding="utf-8")
    assert "pytest" in content, "pytest must be specified in requirements"


def test_project_structure_root():
    """Verify root repository files exist."""
    root = Path(__file__).resolve().parent.parent
    assert (root / ".gitignore").exists(), ".gitignore must exist"
    assert (root / "README.md").exists(), "README.md must exist"
