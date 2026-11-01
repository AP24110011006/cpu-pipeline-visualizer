"""Controlled file operations, safe command execution, and diagnostic parsing."""

from __future__ import annotations

import difflib
from pathlib import Path
import re
import subprocess
import time
from typing import Dict, List, Optional, Tuple

from agents.models import DiagnosticError, ExecutionResult, FileChange


class CodeExecutor:
    """Safe execution sandbox enforcing workspace isolation and bounded commands."""

    PERMITTED_COMMAND_PREFIXES = (
        "py -3.12 -m pytest",
        "python -m pytest",
        "pytest",
        "py -3.12 -m bots",
        "python -m bots",
        "git status",
        "git diff",
        "git log -n",
    )

    FORBIDDEN_PATTERNS = (
        "rmdir",
        "rm -rf",
        "del /",
        "format ",
        "shutil.rmtree",
        "mkfs",
        "curl",
        "wget",
        "Invoke-WebRequest",
        "nc ",
        "netcat",
    )

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        if root_dir is None:
            self.root = Path(__file__).resolve().parent.parent
        else:
            self.root = Path(root_dir).resolve()
        self._backup_store: Dict[str, str] = {}

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """Resolve path and verify it does not escape the repository root."""
        resolved = (self.root / relative_path).resolve()
        if not resolved.is_relative_to(self.root):
            raise PermissionError(f"Security Violation: '{relative_path}' escapes workspace boundary '{self.root}'.")
        return resolved

    def generate_diff(self, original: str, proposed: str, filepath: str) -> str:
        """Generate a standard unified diff between original and proposed code."""
        orig_lines = original.splitlines(keepends=True)
        prop_lines = proposed.splitlines(keepends=True)
        diff = difflib.unified_diff(
            orig_lines,
            prop_lines,
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}",
            lineterm="",
        )
        return "".join(diff)

    def stage_change(self, relative_path: str, proposed_content: str) -> FileChange:
        """Create a FileChange record with unified diff without modifying disk yet."""
        target = self._resolve_safe_path(relative_path)
        is_new = not target.exists()
        original = target.read_text(encoding="utf-8", errors="replace") if not is_new else ""
        diff = self.generate_diff(original, proposed_content, relative_path)
        return FileChange(
            filepath=relative_path,
            original_content=original,
            proposed_content=proposed_content,
            diff=diff,
            is_new_file=is_new,
            applied=False,
        )

    def apply_change(self, change: FileChange) -> bool:
        """Apply a staged FileChange to disk, recording original for rollback."""
        target = self._resolve_safe_path(change.filepath)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and change.filepath not in self._backup_store:
            self._backup_store[change.filepath] = target.read_text(encoding="utf-8", errors="replace")
        target.write_text(change.proposed_content, encoding="utf-8")
        change.applied = True
        change.applied_at = time.time()
        return True

    def rollback_change(self, change: FileChange) -> bool:
        """Revert a change from backup or delete newly created file."""
        target = self._resolve_safe_path(change.filepath)
        if change.is_new_file:
            if target.exists():
                target.unlink()
            change.applied = False
            return True
        elif change.filepath in self._backup_store:
            target.write_text(self._backup_store[change.filepath], encoding="utf-8")
            change.applied = False
            return True
        return False

    def run_safe_command(self, command: str, timeout_sec: int = 45) -> ExecutionResult:
        """Execute a whitelisted shell command within the workspace."""
        cmd_stripped = command.strip()

        # Check safety whitelist
        is_permitted = any(cmd_stripped.startswith(prefix) for prefix in self.PERMITTED_COMMAND_PREFIXES)
        has_forbidden = any(pat in cmd_stripped for pat in self.FORBIDDEN_PATTERNS)

        if not is_permitted or has_forbidden:
            return ExecutionResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=f"Security Policy: Command '{command}' is not in the permitted development whitelist.",
                passed=False,
                duration_sec=0.0,
            )

        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd_stripped,
                cwd=str(self.root),
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            elapsed = time.perf_counter() - t0
            return ExecutionResult(
                command=command,
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                passed=(proc.returncode == 0),
                duration_sec=elapsed,
            )
        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - t0
            return ExecutionResult(
                command=command,
                returncode=-2,
                stdout="",
                stderr=f"Execution timed out after {timeout_sec}s.",
                passed=False,
                duration_sec=elapsed,
            )
        except Exception as err:
            elapsed = time.perf_counter() - t0
            return ExecutionResult(
                command=command,
                returncode=-3,
                stdout="",
                stderr=f"Process invocation failure: {err}",
                passed=False,
                duration_sec=elapsed,
            )

    def run_pytest(self, test_filter: Optional[str] = None) -> ExecutionResult:
        """Run pytest with optional target test selector."""
        cmd = "py -3.12 -m pytest"
        if test_filter:
            cmd += f" {test_filter}"
        res = self.run_safe_command(cmd, timeout_sec=45)
        # If py -3.12 fails with command not found (e.g. standard python environment), fallback to python -m pytest
        if res.returncode != 0 and "not recognized" in (res.stdout + res.stderr):
            cmd = "python -m pytest"
            if test_filter:
                cmd += f" {test_filter}"
            res = self.run_safe_command(cmd, timeout_sec=45)
        return res

    def parse_diagnostics(self, test_output: str) -> List[DiagnosticError]:
        """Extract structured failure details from pytest stdout/stderr."""
        errors: List[DiagnosticError] = []
        # Pattern for pytest failure header: __________________ test_name __________________
        failure_blocks = re.split(r"_{10,}\s+([^\s_]+)\s+_{10,}", test_output)

        if len(failure_blocks) > 1:
            for i in range(1, len(failure_blocks), 2):
                test_name = failure_blocks[i]
                block_content = failure_blocks[i + 1] if i + 1 < len(failure_blocks) else ""

                # Try to extract file and line number
                file_match = re.search(r"(\S+\.py):(\d+):", block_content)
                file_str = file_match.group(1) if file_match else "unknown"
                line_no = int(file_match.group(2)) if file_match else None

                # Extract last error line (E   AssertionError: ...)
                err_lines = [line for line in block_content.splitlines() if line.startswith("E   ")]
                msg = "\n".join(err_lines) if err_lines else "Assertion failed."

                errors.append(
                    DiagnosticError(
                        test_id=test_name,
                        file=file_str,
                        line_number=line_no,
                        error_message=msg,
                        traceback=block_content[:1000],
                    )
                )
        elif "FAILED" in test_output:
            # Fallback for simple single-line failure reports
            for line in test_output.splitlines():
                if line.startswith("FAILED "):
                    errors.append(
                        DiagnosticError(
                            test_id=line.strip(),
                            file="",
                            line_number=None,
                            error_message=line.strip(),
                            traceback="",
                        )
                    )

        return errors
