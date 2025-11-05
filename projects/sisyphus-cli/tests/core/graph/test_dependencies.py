from pathlib import Path

import pytest

from sisyphus.core.graph.dependencies import (
    build_plan_graph,
    detect_cycles,
    discover_plan_files,
    topo_sort,
)
from sisyphus.core.plans.models import (
    Background,
    Objectives,
    RequiredBackground,
    SuccessVision,
    UserRequest,
    Workflow,
    WorkPlan,
)

pytestmark = [pytest.mark.anyio]


# ============================================================
# discover_plan_files tests
# ============================================================


async def test_discover_plan_files__if_tasks_dir_exists_with_yaml_files__returns_sorted_paths(
    tmp_path: Path,
) -> None:
    # given
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    (tasks_dir / "plan-a.yaml").touch()
    (tasks_dir / "plan-b.yml").touch()
    (tasks_dir / "plan-c.yaml").touch()

    # when
    result = discover_plan_files(tmp_path)

    # then
    assert len(result) == 3
    assert all(isinstance(p, Path) for p in result)
    assert any(p.name == "plan-a.yaml" for p in result)
    assert any(p.name == "plan-b.yml" for p in result)
    assert any(p.name == "plan-c.yaml" for p in result)


async def test_discover_plan_files__if_tasks_dir_does_not_exist__returns_empty_list(
    tmp_path: Path,
) -> None:
    # given
    # .sisyphus/tasks/ 디렉토리 생성하지 않음

    # when
    result = discover_plan_files(tmp_path)

    # then
    assert result == []


async def test_discover_plan_files__if_tasks_dir_exists_but_empty__returns_empty_list(
    tmp_path: Path,
) -> None:
    # given
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    # when
    result = discover_plan_files(tmp_path)

    # then
    assert result == []


async def test_discover_plan_files__if_both_yaml_and_yml_extensions__returns_both(
    tmp_path: Path,
) -> None:
    # given
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    (tasks_dir / "plan1.yaml").touch()
    (tasks_dir / "plan2.yml").touch()

    # when
    result = discover_plan_files(tmp_path)

    # then
    assert len(result) == 2
    extensions = {p.suffix for p in result}
    assert ".yaml" in extensions
    assert ".yml" in extensions


async def test_discover_plan_files__if_nested_subdirectories__returns_all_yaml_files(
    tmp_path: Path,
) -> None:
    # given
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)

    (tasks_dir / "root.yaml").touch()
    sub_dir = tasks_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "nested.yml").touch()

    # when
    result = discover_plan_files(tmp_path)

    # then
    assert len(result) == 2
    assert any(p.name == "root.yaml" for p in result)
    assert any(p.name == "nested.yml" for p in result)


# ============================================================
# build_plan_graph tests
# ============================================================


async def test_build_plan_graph__if_plans_with_various_dependencies__builds_correct_adjacency_list(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    plans = {
        "plan-a": WorkPlan(
            id="plan-a",
            name="Plan A",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=["plan-b", "plan-c"],
            todos=[],
        ),
        "plan-b": WorkPlan(
            id="plan-b",
            name="Plan B",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=["plan-d"],
            todos=[],
        ),
        "plan-c": WorkPlan(
            id="plan-c",
            name="Plan C",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=[],
            todos=[],
        ),
        "plan-d": WorkPlan(
            id="plan-d",
            name="Plan D",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=[],
            todos=[],
        ),
    }

    # when
    graph = build_plan_graph(plans)

    # then
    assert graph["plan-a"] == ["plan-b", "plan-c"]
    assert graph["plan-b"] == ["plan-d"]
    assert graph["plan-c"] == []
    assert graph["plan-d"] == []


async def test_build_plan_graph__if_empty_dependencies__builds_graph_with_empty_lists(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    plans = {
        "plan-a": WorkPlan(
            id="plan-a",
            name="Plan A",
            depends_on=[],
            todos=[],
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
        ),
        "plan-b": WorkPlan(
            id="plan-b",
            name="Plan B",
            depends_on=[],
            todos=[],
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
        ),
    }

    # when
    graph = build_plan_graph(plans)

    # then
    assert graph["plan-a"] == []
    assert graph["plan-b"] == []


async def test_build_plan_graph__if_multiple_dependencies__preserves_order(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    plans = {
        "plan-main": WorkPlan(
            id="plan-main",
            name="Main",
            user_request=minimal_user_request,
            objectives=minimal_objectives,
            background=minimal_background,
            required_background=minimal_required_background,
            workflow=minimal_workflow,
            success_vision=minimal_success_vision,
            final_verification=[],
            depends_on=["plan-x", "plan-y", "plan-z"],
            todos=[],
        ),
    }

    # when
    graph = build_plan_graph(plans)

    # then
    assert graph["plan-main"] == ["plan-x", "plan-y", "plan-z"]


# ============================================================
# detect_cycles tests
# ============================================================


async def test_detect_cycles__if_no_cycle__returns_empty_list(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    graph = {
        "plan-a": ["plan-b"],
        "plan-b": ["plan-c"],
        "plan-c": [],
    }

    # when
    cycles = detect_cycles(graph)

    # then
    assert cycles == []


async def test_detect_cycles__if_simple_cycle__detects_cycle(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: A → B → A
    graph = {
        "plan-a": ["plan-b"],
        "plan-b": ["plan-a"],
    }

    # when
    cycles = detect_cycles(graph)

    # then
    assert len(cycles) == 1
    cycle = cycles[0]
    # Cycle should contain plan-a and plan-b
    assert "plan-a" in cycle
    assert "plan-b" in cycle


async def test_detect_cycles__if_complex_cycle__detects_cycle(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: A → B → C → A
    graph = {
        "plan-a": ["plan-b"],
        "plan-b": ["plan-c"],
        "plan-c": ["plan-a"],
    }

    # when
    cycles = detect_cycles(graph)

    # then
    assert len(cycles) == 1
    cycle = cycles[0]
    assert "plan-a" in cycle
    assert "plan-b" in cycle
    assert "plan-c" in cycle


async def test_detect_cycles__if_multiple_disconnected_cycles__detects_all_cycles(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given:
    # Cycle 1: A → B → A
    # Cycle 2: C → D → C
    graph = {
        "plan-a": ["plan-b"],
        "plan-b": ["plan-a"],
        "plan-c": ["plan-d"],
        "plan-d": ["plan-c"],
        "plan-e": [],
    }

    # when
    cycles = detect_cycles(graph)

    # then
    assert len(cycles) == 2
    # Check both cycles exist
    cycle_nodes = [set(cycle) for cycle in cycles]
    assert any({"plan-a", "plan-b"}.issubset(nodes) for nodes in cycle_nodes)
    assert any({"plan-c", "plan-d"}.issubset(nodes) for nodes in cycle_nodes)


async def test_detect_cycles__if_self_reference__detects_cycle(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: A → A
    graph = {
        "plan-a": ["plan-a"],
    }

    # when
    cycles = detect_cycles(graph)

    # then
    assert len(cycles) == 1
    cycle = cycles[0]
    assert "plan-a" in cycle


async def test_detect_cycles__if_diamond_dependency_no_cycle__returns_empty_list(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given:
    #     A
    #    / \
    #   B   C
    #    \ /
    #     D
    graph = {
        "plan-a": ["plan-b", "plan-c"],
        "plan-b": ["plan-d"],
        "plan-c": ["plan-d"],
        "plan-d": [],
    }

    # when
    cycles = detect_cycles(graph)

    # then
    assert cycles == []


async def test_detect_cycles__if_long_chain_with_cycle__detects_cycle(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: A → B → C → D → B (cycle at B-C-D-B)
    graph = {
        "plan-a": ["plan-b"],
        "plan-b": ["plan-c"],
        "plan-c": ["plan-d"],
        "plan-d": ["plan-b"],
    }

    # when
    cycles = detect_cycles(graph)

    # then
    assert len(cycles) == 1
    cycle = cycles[0]
    assert "plan-b" in cycle
    assert "plan-c" in cycle
    assert "plan-d" in cycle


# ============================================================
# topo_sort tests
# ============================================================


async def test_topo_sort__if_linear_dependency_chain__returns_correct_order(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: A → B → C
    graph = {
        "plan-a": ["plan-b"],
        "plan-b": ["plan-c"],
        "plan-c": [],
    }

    # when
    result = topo_sort(graph)

    # then
    assert len(result) == 3
    # plan-c should come before plan-b, plan-b before plan-a
    assert result.index("plan-c") < result.index("plan-b")
    assert result.index("plan-b") < result.index("plan-a")


async def test_topo_sort__if_diamond_dependency__returns_valid_topological_order(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given:
    #     A
    #    / \
    #   B   C
    #    \ /
    #     D
    graph = {
        "plan-a": ["plan-b", "plan-c"],
        "plan-b": ["plan-d"],
        "plan-c": ["plan-d"],
        "plan-d": [],
    }

    # when
    result = topo_sort(graph)

    # then
    assert len(result) == 4
    # D should come before B and C
    assert result.index("plan-d") < result.index("plan-b")
    assert result.index("plan-d") < result.index("plan-c")
    # B and C should come before A
    assert result.index("plan-b") < result.index("plan-a")
    assert result.index("plan-c") < result.index("plan-a")


async def test_topo_sort__if_no_dependencies__returns_all_nodes(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    graph = {
        "plan-a": [],
        "plan-b": [],
        "plan-c": [],
    }

    # when
    result = topo_sort(graph)

    # then
    assert len(result) == 3
    assert set(result) == {"plan-a", "plan-b", "plan-c"}


async def test_topo_sort__if_graph_with_cycles__raises_value_error(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: A → B → A (cycle)
    graph = {
        "plan-a": ["plan-b"],
        "plan-b": ["plan-a"],
    }

    # when & then
    with pytest.raises(ValueError, match=r".*cycles.*"):
        topo_sort(graph)


async def test_topo_sort__if_complex_dag__returns_valid_order(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given:
    #     A
    #    / \
    #   B   C
    #   |   |
    #   D   E
    #    \ /
    #     F
    graph = {
        "plan-a": ["plan-b", "plan-c"],
        "plan-b": ["plan-d"],
        "plan-c": ["plan-e"],
        "plan-d": ["plan-f"],
        "plan-e": ["plan-f"],
        "plan-f": [],
    }

    # when
    result = topo_sort(graph)

    # then
    assert len(result) == 6
    # F should be first (no dependencies)
    assert result.index("plan-f") < result.index("plan-d")
    assert result.index("plan-f") < result.index("plan-e")
    # D before B, E before C
    assert result.index("plan-d") < result.index("plan-b")
    assert result.index("plan-e") < result.index("plan-c")
    # B and C before A
    assert result.index("plan-b") < result.index("plan-a")
    assert result.index("plan-c") < result.index("plan-a")


async def test_topo_sort__if_single_node__returns_single_element_list(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given
    graph = {
        "plan-a": [],
    }

    # when
    result = topo_sort(graph)

    # then
    assert result == ["plan-a"]


async def test_topo_sort__if_parallel_branches__maintains_dependencies(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given:
    #   A   B
    #   |   |
    #   C   D
    graph = {
        "plan-a": ["plan-c"],
        "plan-b": ["plan-d"],
        "plan-c": [],
        "plan-d": [],
    }

    # when
    result = topo_sort(graph)

    # then
    assert len(result) == 4
    # C before A
    assert result.index("plan-c") < result.index("plan-a")
    # D before B
    assert result.index("plan-d") < result.index("plan-b")
