"""Job pipeline support — chain multiple jobs into an ordered execution pipeline.

A pipeline defines a sequence of jobs that run one after another. If any step
fails (and the pipeline is configured to stop on failure), subsequent steps are
skipped. Each step records its own RunRecord via the tracker.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional

from cronwatch.config import JobConfig
from cronwatch.tracker import JobTracker, RunStatus

log = logging.getLogger(__name__)


@dataclass
class PipelineStep:
    """A single step inside a pipeline."""

    job: JobConfig
    # Optional per-step condition: receives the previous step's status.
    # Return True to allow this step to run, False to skip it.
    condition: Optional[Callable[[RunStatus], bool]] = None


@dataclass
class PipelineResult:
    """Aggregated result of a full pipeline run."""

    pipeline_name: str
    steps_total: int
    steps_run: int
    steps_skipped: int
    steps_failed: int
    # Final status is SUCCESS only when every executed step succeeded.
    final_status: RunStatus = RunStatus.SUCCESS
    # Per-step outcomes in execution order.
    step_statuses: List[RunStatus] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.final_status == RunStatus.SUCCESS


def build_pipeline(
    name: str,
    jobs: Iterable[JobConfig],
    *,
    stop_on_failure: bool = True,
) -> tuple[str, List[PipelineStep], bool]:
    """Construct a pipeline descriptor from a list of JobConfig objects.

    Returns a 3-tuple of (name, steps, stop_on_failure) that can be passed
    directly to :func:`run_pipeline`.
    """
    steps = [PipelineStep(job=j) for j in jobs]
    return name, steps, stop_on_failure


def run_pipeline(
    name: str,
    steps: List[PipelineStep],
    tracker: JobTracker,
    runner: Callable[[JobConfig, JobTracker], bool],
    *,
    stop_on_failure: bool = True,
) -> PipelineResult:
    """Execute a pipeline, recording each step through *tracker*.

    Parameters
    ----------
    name:
        Human-readable pipeline identifier used in log messages.
    steps:
        Ordered list of :class:`PipelineStep` objects.
    tracker:
        The :class:`~cronwatch.tracker.JobTracker` used to record run state.
    runner:
        Callable that executes a single job and returns ``True`` on success.
        Typically :func:`cronwatch.job_runner.run_job`.
    stop_on_failure:
        When ``True`` (default), remaining steps are skipped after the first
        failure.  When ``False``, all steps are attempted regardless.
    """
    result = PipelineResult(
        pipeline_name=name,
        steps_total=len(steps),
        steps_run=0,
        steps_skipped=0,
        steps_failed=0,
    )

    previous_status: RunStatus = RunStatus.SUCCESS
    halted = False

    for idx, step in enumerate(steps):
        job_name = step.job.name

        if halted:
            log.info("pipeline '%s': skipping step %d (%s) — pipeline halted",
                     name, idx + 1, job_name)
            result.steps_skipped += 1
            result.step_statuses.append(RunStatus.MISSED)
            continue

        # Evaluate optional per-step condition.
        if step.condition is not None and not step.condition(previous_status):
            log.info("pipeline '%s': skipping step %d (%s) — condition not met",
                     name, idx + 1, job_name)
            result.steps_skipped += 1
            result.step_statuses.append(RunStatus.MISSED)
            continue

        log.info("pipeline '%s': running step %d/%d (%s)",
                 name, idx + 1, len(steps), job_name)
        result.steps_run += 1

        success = runner(step.job, tracker)
        step_status = RunStatus.SUCCESS if success else RunStatus.FAILURE
        previous_status = step_status
        result.step_statuses.append(step_status)

        if not success:
            result.steps_failed += 1
            log.warning("pipeline '%s': step %d (%s) FAILED",
                        name, idx + 1, job_name)
            if stop_on_failure:
                halted = True

    if result.steps_failed > 0:
        result.final_status = RunStatus.FAILURE

    log.info(
        "pipeline '%s' finished — ran=%d skipped=%d failed=%d status=%s",
        name,
        result.steps_run,
        result.steps_skipped,
        result.steps_failed,
        result.final_status.value,
    )
    return result
