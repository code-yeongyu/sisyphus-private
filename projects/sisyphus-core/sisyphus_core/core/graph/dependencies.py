from pathlib import Path

from sisyphus.core.plans.models import WorkPlan


def discover_plan_files(root: Path) -> list[Path]:
    """
    .sisyphus/tasks/ 하위의 모든 YAML 파일 탐색

    Args:
        root: 워크트리 루트 경로 (--cwd 또는 현재 디렉토리)

    Returns:
        YAML 파일 경로 리스트 (절대 경로)
    """
    tasks_dir = root / ".sisyphus" / "tasks"
    if not tasks_dir.exists():
        return []
    return list(tasks_dir.glob("**/*.y*ml"))


def build_plan_graph(plans: dict[str, WorkPlan]) -> dict[str, list[str]]:
    """
    Build dependency graph from plans.

    Args:
        plans: Dict of plan_id -> WorkPlan

    Returns:
        Adjacency list (plan_id -> list of dependencies)
    """
    graph: dict[str, list[str]] = {}

    for plan_id, plan in plans.items():
        graph[plan_id] = plan.depends_on

    return graph


def detect_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    """
    Detect cycles using DFS with temp/perm marks.

    Args:
        graph: Adjacency list representation

    Returns:
        List of cycles (each cycle is a list of node IDs)
    """
    temp_mark: set[str] = set()
    perm_mark: set[str] = set()
    cycles: list[list[str]] = []

    def visit(node: str, stack: list[str]) -> None:
        if node in perm_mark:
            return
        if node in temp_mark:
            idx = stack.index(node)
            cycles.append(stack[idx:])
            return

        temp_mark.add(node)
        stack.append(node)

        for neighbor in graph.get(node, []):
            visit(neighbor, stack)

        stack.pop()
        temp_mark.remove(node)
        perm_mark.add(node)

    for node in graph.keys():
        if node not in perm_mark:
            visit(node, [])

    return cycles


def topo_sort(graph: dict[str, list[str]]) -> list[str]:
    """
    Topological sort using Kahn's algorithm.

    Args:
        graph: Adjacency list representation where graph[A] = [B] means A depends on B

    Returns:
        List of node IDs in topological order (dependencies first)

    Raises:
        ValueError: If graph has cycles
    """
    # Build reverse graph: if A depends on B, then B -> A in execution order
    reverse_graph: dict[str, list[str]] = {node: [] for node in graph}
    in_degree: dict[str, int] = dict.fromkeys(graph, 0)

    for node, dependencies in graph.items():
        for dependency in dependencies:
            # node depends on dependency, so dependency -> node in execution order
            if dependency not in reverse_graph:
                reverse_graph[dependency] = []
            reverse_graph[dependency].append(node)
            in_degree[node] += 1

    # Start with nodes that have no dependencies
    queue: list[str] = [node for node, degree in in_degree.items() if degree == 0]
    result: list[str] = []

    while queue:
        node = queue.pop(0)
        result.append(node)

        # Process all nodes that depend on current node
        for dependent in reverse_graph.get(node, []):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(result) != len(graph):
        raise ValueError("Graph has cycles, cannot perform topological sort")

    return result
