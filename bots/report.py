"""Result containers shared by both bots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class BotReport:
    bot: str
    checks: List[CheckResult] = field(default_factory=list)
    stats: Dict[str, object] = field(default_factory=dict)       # extra numbers (coverage etc.)
    failures: List[str] = field(default_factory=list)            # readable failure descriptions

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def passed(self) -> int:
        return sum(1 for check in self.checks if check.passed)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def all_passed(self) -> bool:
        return self.total > 0 and self.failed == 0

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append(CheckResult(name, passed, detail))

    def summary(self) -> str:
        verdict = "ALL PASSED" if self.all_passed else "FAILURES FOUND"
        return f"{self.bot}: {self.passed}/{self.total} checks passed - {verdict}"

    def to_text(self) -> str:
        lines = [self.summary(), ""]
        for check in self.checks:
            lines.append(f"  [{'PASS' if check.passed else 'FAIL'}] {check.name}" + (f"  ({check.detail})" if check.detail else ""))
        if self.stats:
            lines += ["", "  Stats: " + ", ".join(f"{key}={value}" for key, value in self.stats.items())]
        for failure in self.failures:
            lines += ["", failure]
        return "\n".join(lines)
