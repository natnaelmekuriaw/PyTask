from dataclasses import dataclass

from pytask_service.benchmarks.cases import CaseSpec
from pytask_service.benchmarks.metrics import CaseMetrics


@dataclass(frozen=True, slots=True)
class CaseResult:
    case: CaseSpec
    metrics: CaseMetrics | None = None
    error_code: str | None = None
    retained_schema: str | None = None

    @property
    def valid(self) -> bool:
        return self.metrics is not None and self.error_code is None


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    valid: bool
    elapsed_seconds: float | None = None
    attempt_statuses: tuple[str, ...] = ()
    error_code: str | None = None
    retained_schema: str | None = None

