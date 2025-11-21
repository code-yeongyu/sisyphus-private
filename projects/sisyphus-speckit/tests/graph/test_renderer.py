import pytest
from sisyphus_core.core.graph.renderer import AsciiRenderer, MermaidRenderer, PngRenderer

pytestmark = [pytest.mark.anyio]


async def test_ascii_renderer__if_empty_graph__returns_empty_message() -> None:
    # given
    renderer = AsciiRenderer()
    graph: dict[str, list[str]] = {}

    # when
    result = renderer.render(graph)

    # then
    assert result == "(empty graph)"


async def test_ascii_renderer__if_single_node_no_deps__returns_node_name() -> None:
    # given
    renderer = AsciiRenderer()
    graph = {"plan-a": []}

    # when
    result = renderer.render(graph)

    # then
    assert "plan-a" in result
    assert "└──" in result or "├──" in result


async def test_ascii_renderer__if_simple_dependency__shows_tree_structure() -> None:
    # given
    renderer = AsciiRenderer()
    graph = {"plan-a": ["plan-b"], "plan-b": []}

    # when
    result = renderer.render(graph)

    # then
    assert "plan-a" in result
    assert "plan-b" in result
    assert "└──" in result or "├──" in result


async def test_ascii_renderer__if_complex_graph__renders_all_nodes() -> None:
    # given
    renderer = AsciiRenderer()
    graph = {
        "plan-a": ["plan-b", "plan-c"],
        "plan-b": ["plan-d"],
        "plan-c": [],
        "plan-d": [],
    }

    # when
    result = renderer.render(graph)

    # then
    assert "plan-a" in result
    assert "plan-b" in result
    assert "plan-c" in result
    assert "plan-d" in result
    assert "│" in result or "└" in result or "├" in result


async def test_ascii_renderer__if_circular_dependency__marks_circular() -> None:
    # given
    renderer = AsciiRenderer()
    graph = {"plan-a": ["plan-b"], "plan-b": ["plan-a"]}

    # when
    result = renderer.render(graph)

    # then
    assert "(circular)" in result


async def test_mermaid_renderer__if_empty_graph__returns_empty_graph_node() -> None:
    # given
    renderer = MermaidRenderer()
    graph: dict[str, list[str]] = {}

    # when
    result = renderer.render(graph)

    # then
    assert result == "graph TD\n  empty[Empty Graph]"


async def test_mermaid_renderer__if_single_node_no_deps__returns_mermaid_syntax() -> None:
    # given
    renderer = MermaidRenderer()
    graph = {"plan-a": []}

    # when
    result = renderer.render(graph)

    # then
    assert "graph TD" in result
    assert "plan-a" in result
    assert "node_" in result


async def test_mermaid_renderer__if_simple_dependency__shows_arrow() -> None:
    # given
    renderer = MermaidRenderer()
    graph = {"plan-a": ["plan-b"], "plan-b": []}

    # when
    result = renderer.render(graph)

    # then
    assert "graph TD" in result
    assert "plan-a" in result
    assert "plan-b" in result
    assert "-->" in result


async def test_mermaid_renderer__if_complex_graph__renders_all_edges() -> None:
    # given
    renderer = MermaidRenderer()
    graph = {
        "plan-a": ["plan-b", "plan-c"],
        "plan-b": ["plan-d"],
        "plan-c": [],
        "plan-d": [],
    }

    # when
    result = renderer.render(graph)

    # then
    lines = result.split("\n")
    assert any("plan-a" in line for line in lines)
    assert any("plan-b" in line for line in lines)
    assert any("plan-c" in line for line in lines)
    assert any("plan-d" in line for line in lines)
    arrow_count = sum(1 for line in lines if "-->" in line)
    assert arrow_count == 3


async def test_mermaid_renderer__if_node_with_special_chars__hashes_node_id() -> None:
    # given
    renderer = MermaidRenderer()
    graph = {"plan-with-special-chars!@#": []}

    # when
    result = renderer.render(graph)

    # then
    assert "node_" in result
    assert "plan-with-special-chars!@#" in result


async def test_png_renderer__if_graphviz_not_installed__raises_import_error() -> None:
    # given
    renderer = PngRenderer()
    graph = {"plan-a": ["plan-b"], "plan-b": []}

    # when/then
    try:
        import graphviz  # noqa: F401  # pyright: ignore[reportUnusedImport]

        pytest.skip("graphviz is installed, skipping test")
    except ImportError:
        with pytest.raises(ImportError, match="graphviz library not found"):
            _ = renderer.render(graph)


async def test_png_renderer__if_graphviz_installed__returns_png_bytes() -> None:
    # given
    pytest.importorskip("graphviz")
    renderer = PngRenderer()
    graph = {"plan-a": ["plan-b"], "plan-b": []}

    # when
    result = renderer.render(graph)

    # then
    assert isinstance(result, bytes)
    assert result.startswith(b"\x89PNG")


async def test_png_renderer__if_empty_graph__returns_png_bytes() -> None:
    # given
    pytest.importorskip("graphviz")
    renderer = PngRenderer()
    graph: dict[str, list[str]] = {}

    # when
    result = renderer.render(graph)

    # then
    assert isinstance(result, bytes)
    assert result.startswith(b"\x89PNG")


async def test_png_renderer__if_complex_graph__returns_png_bytes() -> None:
    # given
    pytest.importorskip("graphviz")
    renderer = PngRenderer()
    graph = {
        "plan-a": ["plan-b", "plan-c"],
        "plan-b": ["plan-d"],
        "plan-c": [],
        "plan-d": [],
    }

    # when
    result = renderer.render(graph)

    # then
    assert isinstance(result, bytes)
    assert result.startswith(b"\x89PNG")
