import hashlib
from typing import Protocol


class GraphRenderer(Protocol):
    def render(self, graph: dict[str, list[str]]) -> str | bytes: ...


class AsciiRenderer:
    def render(self, graph: dict[str, list[str]]) -> str:
        if not graph:
            return "(empty graph)"

        lines: list[str] = []
        visited: set[str] = set()

        root_nodes = [node for node in graph if node not in self._get_all_dependencies(graph)]
        if not root_nodes:
            root_nodes = list(graph.keys())

        def render_node(node: str, prefix: str, is_last: bool) -> None:
            if node in visited:
                lines.append(f"{prefix}{'└── ' if is_last else '├── '}{node} (circular)")
                return

            visited.add(node)
            lines.append(f"{prefix}{'└── ' if is_last else '├── '}{node}")

            dependencies = graph.get(node, [])
            for i, dep in enumerate(dependencies):
                is_last_dep = i == len(dependencies) - 1
                new_prefix = prefix + ("    " if is_last else "│   ")
                render_node(dep, new_prefix, is_last_dep)

        for i, root in enumerate(root_nodes):
            is_last_root = i == len(root_nodes) - 1
            render_node(root, "", is_last_root)

        return "\n".join(lines)

    def _get_all_dependencies(self, graph: dict[str, list[str]]) -> set[str]:
        all_deps: set[str] = set()
        for deps in graph.values():
            all_deps.update(deps)
        return all_deps


class MermaidRenderer:
    def render(self, graph: dict[str, list[str]]) -> str:
        if not graph:
            return "graph TD\n  empty[Empty Graph]"

        lines = ["graph TD"]

        for node, dependencies in graph.items():
            node_id = self._hash_node_id(node)
            lines.append(f'  {node_id}["{node}"]')

            for dep in dependencies:
                dep_id = self._hash_node_id(dep)
                lines.append(f"  {node_id} --> {dep_id}")

        return "\n".join(lines)

    def _hash_node_id(self, node: str) -> str:
        return "node_" + hashlib.md5(node.encode()).hexdigest()[:8]


class PngRenderer:
    def render(self, graph: dict[str, list[str]]) -> bytes:
        try:
            import graphviz  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
        except ImportError as e:
            msg = (
                "graphviz library not found. Install it with:\n"
                "  uv add graphviz\n\n"
                "You may also need to install Graphviz system package:\n"
                "  macOS: brew install graphviz\n"
                "  Ubuntu: sudo apt-get install graphviz\n"
                "  Windows: choco install graphviz"
            )
            raise ImportError(msg) from e

        dot = graphviz.Digraph(comment="Plan Dependencies")
        dot.attr(rankdir="TB")

        for node in graph:
            dot.node(node, node)

        for node, dependencies in graph.items():
            for dep in dependencies:
                dot.edge(node, dep)

        return dot.pipe(format="png")
