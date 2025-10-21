"""
YAML Task Planning System - Implementation Reference

This file shows the core data structures and algorithms for the YAML-based
task planning system. This is a reference implementation showing the design.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal

import anyio
import networkx as nx
import yaml


# ==============================================================================
# ENUMS
# ==============================================================================


class TaskStatus(str, Enum):
    """Task execution status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskPriority(str, Enum):
    """Task priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VerificationType(str, Enum):
    """Types of verification checks"""

    MANUAL = "manual"
    COMMAND = "command"
    HTTP = "http"
    PROMPT = "prompt"
    SUBTASKS_COMPLETE = "subtasks_complete"
    COMPOSITE = "composite"
    STATIC_ANALYSIS = "static_analysis"
    COVERAGE = "coverage"


# ==============================================================================
# VERIFICATION STRUCTURES
# ==============================================================================


@dataclass
class VerificationCheck:
    """Base verification check"""

    type: VerificationType
    name: str | None = None
    description: str | None = None
    required: bool = True
    weight: float = 1.0


@dataclass
class ManualVerification(VerificationCheck):
    """Manual verification by human"""

    type: Literal[VerificationType.MANUAL] = VerificationType.MANUAL
    passed: bool | None = None
    verified_by: str | None = None
    verified_at: str | None = None


@dataclass
class CommandVerification(VerificationCheck):
    """Command execution verification"""

    type: Literal[VerificationType.COMMAND] = VerificationType.COMMAND
    command: str = ""
    expected_exit_code: int = 0
    timeout_seconds: int = 60
    expected_output_contains: list[str] | None = None
    expected_output_regex: str | None = None


@dataclass
class HttpVerification(VerificationCheck):
    """HTTP request/response verification"""

    type: Literal[VerificationType.HTTP] = VerificationType.HTTP
    method: str = "GET"
    url: str = ""
    headers: dict[str, str] | None = None
    body: dict[str, Any] | None = None
    expected_status: int = 200
    expected_response_schema: dict[str, Any] | None = None
    expected_headers: dict[str, str] | None = None
    timeout_seconds: int = 10


@dataclass
class PromptVerification(VerificationCheck):
    """LLM-based verification"""

    type: Literal[VerificationType.PROMPT] = VerificationType.PROMPT
    prompt: str = ""
    llm_check: bool = True
    llm_model: str = "claude-sonnet-4.5"
    llm_temperature: float = 0.0
    expected_keywords: list[str] | None = None
    min_confidence: float = 0.8


@dataclass
class CompositeVerification(VerificationCheck):
    """Composite verification combining multiple checks"""

    type: Literal[VerificationType.COMPOSITE] = VerificationType.COMPOSITE
    operator: Literal["AND", "OR"] = "AND"
    checks: list[VerificationCheck] = field(default_factory=list)


@dataclass
class VerificationResult:
    """Result of verification execution"""

    passed: bool
    verified_at: str
    output: str | None = None
    error: str | None = None
    duration_seconds: float | None = None


# ==============================================================================
# TASK STRUCTURES
# ==============================================================================


@dataclass
class Note:
    """Task note/comment"""

    timestamp: str
    author: str
    content: str


@dataclass
class Artifact:
    """Task artifact (file, diagram, etc.)"""

    type: str
    path: str
    description: str | None = None


@dataclass
class SubtasksRef:
    """Reference to external subtasks file"""

    file: str
    task_count: int | None = None
    total_depth: int | None = None
    description: str | None = None


@dataclass
class Task:
    """Main task definition"""

    id: str
    title: str
    description: str = ""

    # Status
    status: TaskStatus = TaskStatus.PENDING
    completion: float = 0.0

    # Organization
    milestone: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    tags: list[str] = field(default_factory=list)

    # Relationships
    depends_on: list[str] = field(default_factory=list)
    blocks: list[str] = field(default_factory=list)
    related_to: list[str] = field(default_factory=list)

    # Time tracking
    estimated_time_hours: float | None = None
    actual_time_hours: float | None = None
    started_at: str | None = None
    completed_at: str | None = None
    deadline: str | None = None

    # Assignment
    assignee: str | None = None
    session_id: str | None = None

    # Subtasks
    subtasks: list[Task] = field(default_factory=list)
    subtasks_ref: SubtasksRef | None = None

    # Verification
    verification: VerificationCheck | None = None

    # Metadata
    notes: list[Note] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)

    def can_start(self, plan: TaskPlan) -> bool:
        """Check if task can start (all dependencies completed)"""
        if self.status != TaskStatus.PENDING:
            return False

        for dep_id in self.depends_on:
            dep_task = plan.get_task(dep_id)
            if dep_task is None:
                raise ValueError(f"Dependency {dep_id} not found")
            if dep_task.status != TaskStatus.COMPLETED:
                return False

        return True

    def get_all_subtasks(self) -> list[Task]:
        """Recursively get all subtasks including from external refs"""
        result = list(self.subtasks)

        if self.subtasks_ref:
            # Load external subtasks (would load from file in real implementation)
            # result.extend(self._load_external_subtasks())
            pass

        return result


@dataclass
class CriticalTask:
    """Critical task discovered during execution"""

    id: str
    title: str
    description: str

    # Severity
    priority: TaskPriority = TaskPriority.CRITICAL
    severity: Literal["low", "medium", "high", "critical"] = "high"
    security_impact: bool = False
    blocks_release: bool = True

    # Discovery
    discovered_at: str = ""
    discovered_by: str = ""
    discovery_method: str = ""
    discovery_context: str | None = None

    # Status
    status: TaskStatus = TaskStatus.PENDING
    completion: float = 0.0

    # Relationships
    related_task: str | None = None
    blocks: list[str] = field(default_factory=list)

    # Assignment
    assignee: str | None = None
    estimated_time_hours: float | None = None
    deadline: str | None = None

    # Verification
    verification: VerificationCheck | None = None

    # Metadata
    notes: list[Note] = field(default_factory=list)


@dataclass
class Milestone:
    """Project milestone"""

    id: str
    name: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    completion: float = 0.0
    depends_on: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)


@dataclass
class Goal:
    """Project goal"""

    description: str
    success_criteria: list[str] = field(default_factory=list)
    is_accomplished: bool = False


@dataclass
class AutoSplitConfig:
    """Auto-split configuration"""

    enabled: bool = True
    max_tasks: int = 30
    max_depth: int = 3
    max_file_size_kb: int = 10
    strategy: Literal["milestone", "size", "complexity"] = "milestone"


@dataclass
class VerificationConfig:
    """Verification configuration"""

    verify_on_task_complete: bool = True
    verify_on_project_complete: bool = True
    cache_results: bool = True
    cache_ttl_seconds: int = 3600
    fail_fast: bool = False


@dataclass
class AgentConfig:
    """Agent execution configuration"""

    parallel_execution: bool = True
    max_concurrent_tasks: int = 3
    retry_failed_tasks: bool = True
    max_retries: int = 3
    retry_delay_seconds: int = 5


@dataclass
class PlanConfig:
    """Plan configuration"""

    auto_split: AutoSplitConfig = field(default_factory=AutoSplitConfig)
    verification: VerificationConfig = field(default_factory=VerificationConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)


@dataclass
class ProjectMetadata:
    """Project metadata"""

    id: str
    name: str
    description: str = ""
    repository: str | None = None
    created_at: str = ""
    updated_at: str = ""


@dataclass
class FeedbackEntry:
    """Feedback from verify agent"""

    iteration: int
    timestamp: str
    agent: str
    session_id: str
    feedback: str
    tasks_affected: list[str] = field(default_factory=list)
    critical_tasks_created: list[str] = field(default_factory=list)
    requires_rework: bool = False


@dataclass
class ExecutionSession:
    """Agent execution session"""

    session_id: str
    agent: str
    phase: Literal["execute", "verify"]
    task_id: str | None
    started_at: str
    ended_at: str | None = None
    status: TaskStatus = TaskStatus.IN_PROGRESS
    feedback_given: bool = False


@dataclass
class Metrics:
    """Project metrics"""

    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    pending_tasks: int = 0
    blocked_tasks: int = 0
    failed_tasks: int = 0
    skipped_tasks: int = 0

    critical_tasks_total: int = 0
    critical_tasks_resolved: int = 0
    critical_tasks_pending: int = 0

    total_subtasks: int = 0
    completed_subtasks: int = 0

    estimated_total_hours: float = 0.0
    actual_total_hours: float = 0.0
    time_efficiency: float = 0.0

    completion_percentage: float = 0.0
    on_track: bool = True
    projected_completion: str | None = None

    verify_iterations: int = 0
    critical_issues_found: int = 0
    critical_issues_resolved: int = 0


@dataclass
class GraphAnalysis:
    """Graph analysis results"""

    is_dag: bool
    has_cycles: bool
    cycle_paths: list[list[str]] = field(default_factory=list)

    critical_path: list[str] = field(default_factory=list)
    critical_path_duration_hours: float = 0.0

    topological_order: list[str] = field(default_factory=list)
    parallel_groups: list[list[str]] = field(default_factory=list)

    max_depth: int = 0
    max_dependencies_per_task: int = 0
    isolated_tasks: int = 0


@dataclass
class TaskPlan:
    """Complete task plan"""

    schema_version: str
    project: ProjectMetadata
    config: PlanConfig
    goal: Goal
    milestones: list[Milestone]
    tasks: list[Task]
    critical_tasks: list[CriticalTask] = field(default_factory=list)
    feedback_history: list[FeedbackEntry] = field(default_factory=list)
    execution_history: list[ExecutionSession] = field(default_factory=list)
    metrics: Metrics = field(default_factory=Metrics)
    graph_analysis: GraphAnalysis | None = None

    @classmethod
    def from_yaml(cls, path: Path) -> TaskPlan:
        """Load plan from YAML file"""
        with open(path) as f:
            data = yaml.safe_load(f)

        # Convert dict to dataclass (simplified)
        # In real implementation, would use proper deserialization
        return cls(**data)

    def to_yaml(self, path: Path) -> None:
        """Save plan to YAML file"""
        # Update timestamp
        self.project.updated_at = datetime.now(timezone.utc).isoformat()

        # Convert to dict
        data = self._to_dict()

        # Write to file
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def _to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization"""
        # Simplified - would use proper serialization in real implementation
        return {}

    def validate(self) -> list[str]:
        """Validate plan structure"""
        errors = []

        # Check for duplicate task IDs
        task_ids = [t.id for t in self.tasks]
        duplicates = [tid for tid in task_ids if task_ids.count(tid) > 1]
        if duplicates:
            errors.append(f"Duplicate task IDs: {duplicates}")

        # Check for broken references
        all_task_ids = {t.id for t in self.tasks}
        for task in self.tasks:
            for dep_id in task.depends_on:
                if dep_id not in all_task_ids:
                    errors.append(f"Task {task.id} depends on non-existent task {dep_id}")

        # Check for cycles
        analyzer = GraphAnalyzer(self)
        if analyzer.has_cycles():
            cycles = analyzer.find_cycles()
            errors.append(f"Circular dependencies found: {cycles}")

        return errors

    def get_task(self, task_id: str) -> Task | None:
        """Get task by ID"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def has_task(self, task_id: str) -> bool:
        """Check if task exists"""
        return any(t.id == task_id for t in self.tasks)

    def update_metrics(self) -> None:
        """Update plan metrics"""
        self.metrics.total_tasks = len(self.tasks)
        self.metrics.completed_tasks = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        self.metrics.in_progress_tasks = sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS)
        self.metrics.pending_tasks = sum(1 for t in self.tasks if t.status == TaskStatus.PENDING)
        self.metrics.blocked_tasks = sum(1 for t in self.tasks if t.status == TaskStatus.BLOCKED)
        self.metrics.failed_tasks = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)

        self.metrics.critical_tasks_total = len(self.critical_tasks)
        self.metrics.critical_tasks_resolved = sum(
            1 for ct in self.critical_tasks if ct.status == TaskStatus.COMPLETED
        )
        self.metrics.critical_tasks_pending = sum(
            1 for ct in self.critical_tasks if ct.status != TaskStatus.COMPLETED
        )

        # Calculate completion percentage
        if self.metrics.total_tasks > 0:
            self.metrics.completion_percentage = (self.metrics.completed_tasks / self.metrics.total_tasks) * 100


# ==============================================================================
# GRAPH ANALYZER
# ==============================================================================


class GraphAnalyzer:
    """Analyze task dependency graph"""

    def __init__(self, plan: TaskPlan):
        self.plan = plan
        self.graph = self._build_graph()

    def _build_graph(self) -> nx.DiGraph:
        """Build NetworkX directed graph from tasks"""
        G = nx.DiGraph()

        # Add nodes
        for task in self.plan.tasks:
            G.add_node(
                task.id,
                task=task,
                estimated_hours=task.estimated_time_hours or 0,
                priority=task.priority.value,
            )

        # Add edges (dependencies)
        for task in self.plan.tasks:
            for dep_id in task.depends_on:
                G.add_edge(dep_id, task.id)

        return G

    def has_cycles(self) -> bool:
        """Check if graph has cycles"""
        try:
            nx.find_cycle(self.graph)
            return True
        except nx.NetworkXNoCycle:
            return False

    def find_cycles(self) -> list[list[str]]:
        """Find all cycles in graph"""
        return list(nx.simple_cycles(self.graph))

    def topological_sort(self) -> list[str]:
        """Get valid execution order"""
        try:
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXError:
            # Graph has cycles
            return []

    def critical_path(self) -> list[str]:
        """Find longest dependency chain"""
        if not nx.is_directed_acyclic_graph(self.graph):
            return []

        # Find longest path using dynamic programming
        return list(nx.dag_longest_path(self.graph, weight="estimated_hours"))

    def parallel_groups(self) -> list[list[str]]:
        """Find tasks that can run in parallel"""
        if not nx.is_directed_acyclic_graph(self.graph):
            return []

        # Group by topological generation (level)
        return [list(generation) for generation in nx.topological_generations(self.graph)]

    def estimate_duration(self) -> float:
        """Estimate total project duration (critical path)"""
        if not nx.is_directed_acyclic_graph(self.graph):
            return 0.0

        critical = self.critical_path()
        total = 0.0

        for task_id in critical:
            task = self.plan.get_task(task_id)
            if task and task.estimated_time_hours:
                total += task.estimated_time_hours

        return total

    def analyze(self) -> GraphAnalysis:
        """Perform complete graph analysis"""
        analysis = GraphAnalysis(
            is_dag=nx.is_directed_acyclic_graph(self.graph),
            has_cycles=self.has_cycles(),
            cycle_paths=self.find_cycles() if self.has_cycles() else [],
            critical_path=self.critical_path(),
            critical_path_duration_hours=self.estimate_duration(),
            topological_order=self.topological_sort(),
            parallel_groups=self.parallel_groups(),
        )

        # Calculate depth
        if analysis.is_dag:
            analysis.max_depth = len(analysis.parallel_groups)

        # Calculate max dependencies
        analysis.max_dependencies_per_task = max(
            (self.graph.in_degree(node) for node in self.graph.nodes()), default=0
        )

        # Find isolated tasks
        analysis.isolated_tasks = sum(
            1 for node in self.graph.nodes() if self.graph.degree(node) == 0
        )

        return analysis


# ==============================================================================
# VERIFICATION ENGINE
# ==============================================================================


class VerificationEngine:
    """Execute verification checks"""

    async def verify_task(self, task: Task) -> VerificationResult:
        """Run verification for a task"""
        if task.verification is None:
            return VerificationResult(
                passed=True,
                verified_at=datetime.now(timezone.utc).isoformat(),
                output="No verification defined",
            )

        return await self._verify_check(task.verification)

    async def verify_project(self, plan: TaskPlan) -> VerificationResult:
        """Run project-level verification"""
        # Would check project_verification field
        # Placeholder implementation
        return VerificationResult(
            passed=True,
            verified_at=datetime.now(timezone.utc).isoformat(),
        )

    async def _verify_check(self, check: VerificationCheck) -> VerificationResult:
        """Execute a single verification check"""
        start_time = datetime.now(timezone.utc)

        try:
            if isinstance(check, CommandVerification):
                passed = await self._verify_command(check)
            elif isinstance(check, HttpVerification):
                passed = await self._verify_http(check)
            elif isinstance(check, PromptVerification):
                passed = await self._verify_prompt(check)
            elif isinstance(check, CompositeVerification):
                passed = await self._verify_composite(check)
            else:
                passed = False

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            return VerificationResult(
                passed=passed,
                verified_at=datetime.now(timezone.utc).isoformat(),
                duration_seconds=duration,
            )

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return VerificationResult(
                passed=False,
                verified_at=datetime.now(timezone.utc).isoformat(),
                error=str(e),
                duration_seconds=duration,
            )

    async def _verify_command(self, check: CommandVerification) -> bool:
        """Execute command verification"""
        try:
            process = await anyio.run_process(
                check.command,
                shell=True,
                check=False,
            )
            return process.returncode == check.expected_exit_code

        except Exception:
            return False

    async def _verify_http(self, check: HttpVerification) -> bool:
        """Execute HTTP verification"""
        # Would use httpx to make request
        # Placeholder
        return True

    async def _verify_prompt(self, check: PromptVerification) -> bool:
        """Execute LLM-based verification"""
        # Would call LLM API
        # Placeholder
        return True

    async def _verify_composite(self, check: CompositeVerification) -> bool:
        """Execute composite verification"""
        results = []

        for sub_check in check.checks:
            result = await self._verify_check(sub_check)
            results.append(result.passed)

        if check.operator == "AND":
            return all(results)
        else:  # OR
            return any(results)


# ==============================================================================
# PLAN SPLITTER
# ==============================================================================


class PlanSplitter:
    """Split large plans into smaller files"""

    def __init__(self, plan: TaskPlan):
        self.plan = plan

    def should_split(self) -> bool:
        """Check if plan should be split"""
        if not self.plan.config.auto_split.enabled:
            return False

        # Check thresholds
        if len(self.plan.tasks) > self.plan.config.auto_split.max_tasks:
            return True

        # Check depth
        analyzer = GraphAnalyzer(self.plan)
        analysis = analyzer.analyze()
        if analysis.max_depth > self.plan.config.auto_split.max_depth:
            return True

        return False

    def split_by_milestone(self) -> dict[str, TaskPlan]:
        """Split plan by milestones"""
        splits: dict[str, TaskPlan] = {}

        for milestone in self.plan.milestones:
            # Filter tasks for this milestone
            milestone_tasks = [t for t in self.plan.tasks if t.milestone == milestone.id]

            # Create sub-plan
            sub_plan = TaskPlan(
                schema_version=self.plan.schema_version,
                project=self.plan.project,
                config=self.plan.config,
                goal=self.plan.goal,
                milestones=[milestone],
                tasks=milestone_tasks,
            )

            splits[milestone.id] = sub_plan

        return splits

    def merge(self, plans: list[TaskPlan]) -> TaskPlan:
        """Merge multiple plans"""
        # Combine all tasks, milestones, etc.
        merged = TaskPlan(
            schema_version=plans[0].schema_version,
            project=plans[0].project,
            config=plans[0].config,
            goal=plans[0].goal,
            milestones=[],
            tasks=[],
        )

        for plan in plans:
            merged.milestones.extend(plan.milestones)
            merged.tasks.extend(plan.tasks)
            merged.critical_tasks.extend(plan.critical_tasks)

        return merged


# ==============================================================================
# TASK VALIDATOR (Integration with Sisyphus)
# ==============================================================================


class YAMLTaskValidator:
    """
    Task validator for YAML plans.
    Replaces existing markdown-based TaskValidator.
    """

    def __init__(self, plan_path: Path):
        self.plan_path = plan_path
        self.plan = TaskPlan.from_yaml(plan_path)

        # Validate plan
        errors = self.plan.validate()
        if errors:
            raise ValueError(f"Invalid task plan: {errors}")

        self.analyzer = GraphAnalyzer(self.plan)
        self.verifier = VerificationEngine()

        # Run initial analysis
        self.plan.graph_analysis = self.analyzer.analyze()

    async def is_complete(self) -> bool:
        """Check if all tasks are complete"""
        # All regular tasks complete
        if not all(t.status == TaskStatus.COMPLETED for t in self.plan.tasks):
            return False

        # All critical tasks resolved
        if any(ct.status != TaskStatus.COMPLETED for ct in self.plan.critical_tasks):
            return False

        # Project verification passed
        if self.plan.config.verification.verify_on_project_complete:
            result = await self.verifier.verify_project(self.plan)
            if not result.passed:
                return False

        # Goal accomplished
        return self.plan.goal.is_accomplished

    async def get_next_tasks(self) -> list[Task]:
        """Get tasks ready to execute"""
        executable = []

        # Check regular tasks
        for task in self.plan.tasks:
            if task.can_start(self.plan):
                executable.append(task)

        # Add critical tasks (higher priority)
        for ctask in self.plan.critical_tasks:
            if ctask.status == TaskStatus.PENDING:
                # Convert to Task for execution
                # In real implementation, would handle properly
                pass

        # Sort by priority
        priority_order = {
            TaskPriority.CRITICAL: 4,
            TaskPriority.HIGH: 3,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 1,
        }

        executable.sort(key=lambda t: priority_order[t.priority], reverse=True)

        return executable

    async def mark_complete(self, task_id: str) -> None:
        """Mark task as complete"""
        task = self.plan.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Update status
        task.status = TaskStatus.COMPLETED
        task.completion = 1.0
        task.completed_at = datetime.now(timezone.utc).isoformat()

        # Run verification
        if self.plan.config.verification.verify_on_task_complete:
            result = await self.verifier.verify_task(task)

            if not result.passed:
                # Mark as failed
                task.status = TaskStatus.FAILED
                raise TaskVerificationError(f"Task {task_id} failed verification: {result.error}")

        # Update metrics
        self.plan.update_metrics()

        # Save plan
        await self._save_plan()

    async def add_critical_task(self, critical_task: CriticalTask) -> None:
        """Add critical task discovered during execution"""
        self.plan.critical_tasks.append(critical_task)
        self.plan.update_metrics()
        await self._save_plan()

    async def should_continue_loop(self) -> bool:
        """Check if execution loop should continue"""
        # Has pending tasks
        if any(t.status == TaskStatus.PENDING for t in self.plan.tasks):
            return True

        # Has in-progress tasks
        if any(t.status == TaskStatus.IN_PROGRESS for t in self.plan.tasks):
            return True

        # Has unresolved critical tasks
        if any(ct.status != TaskStatus.COMPLETED for ct in self.plan.critical_tasks):
            return True

        # Project not complete
        if not await self.is_complete():
            return True

        return False

    async def _save_plan(self) -> None:
        """Save plan to YAML"""
        self.plan.to_yaml(self.plan_path)


class TaskVerificationError(Exception):
    """Task verification failed"""

    pass


# ==============================================================================
# EXAMPLE USAGE
# ==============================================================================


async def example_usage():
    """Example of how to use the YAML task system"""

    # Load plan
    plan_path = Path("tasks/plan.yaml")
    validator = YAMLTaskValidator(plan_path)

    # Get next tasks
    tasks = await validator.get_next_tasks()
    print(f"Found {len(tasks)} executable tasks")

    for task in tasks:
        print(f"  - {task.id}: {task.title} (priority: {task.priority})")

    # Check if should continue
    should_continue = await validator.should_continue_loop()
    print(f"\nShould continue loop: {should_continue}")

    # Graph analysis
    if validator.plan.graph_analysis:
        analysis = validator.plan.graph_analysis
        print(f"\nGraph analysis:")
        print(f"  - Is DAG: {analysis.is_dag}")
        print(f"  - Has cycles: {analysis.has_cycles}")
        print(f"  - Critical path: {' -> '.join(analysis.critical_path)}")
        print(f"  - Estimated duration: {analysis.critical_path_duration_hours}h")

    # Mark task complete
    if tasks:
        first_task = tasks[0]
        print(f"\nCompleting task: {first_task.id}")

        try:
            await validator.mark_complete(first_task.id)
            print("  ✓ Task completed and verified")
        except TaskVerificationError as e:
            print(f"  ✗ Verification failed: {e}")


if __name__ == "__main__":
    # Run example
    anyio.run(example_usage)
