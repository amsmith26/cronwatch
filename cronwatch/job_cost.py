"""Track and report estimated execution cost per job run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CostRule:
    """Cost configuration for a single job."""
    job_name: str
    cost_per_second: float = 0.0
    fixed_cost: float = 0.0
    currency: str = "USD"


@dataclass
class CostEntry:
    job_name: str
    duration_seconds: float
    variable_cost: float
    fixed_cost: float
    currency: str

    @property
    def total(self) -> float:
        return self.variable_cost + self.fixed_cost


@dataclass
class CostRegistry:
    _rules: Dict[str, CostRule] = field(default_factory=dict)
    _entries: Dict[str, List[CostEntry]] = field(default_factory=dict)

    def register(self, rule: CostRule) -> None:
        self._rules[rule.job_name] = rule

    def record(self, job_name: str, duration_seconds: float) -> Optional[CostEntry]:
        rule = self._rules.get(job_name)
        if rule is None:
            return None
        entry = CostEntry(
            job_name=job_name,
            duration_seconds=duration_seconds,
            variable_cost=rule.cost_per_second * duration_seconds,
            fixed_cost=rule.fixed_cost,
            currency=rule.currency,
        )
        self._entries.setdefault(job_name, []).append(entry)
        return entry

    def total_cost(self, job_name: str) -> float:
        return sum(e.total for e in self._entries.get(job_name, []))

    def all_entries(self, job_name: str) -> List[CostEntry]:
        return list(self._entries.get(job_name, []))

    def summary(self) -> Dict[str, float]:
        return {name: self.total_cost(name) for name in self._entries}
