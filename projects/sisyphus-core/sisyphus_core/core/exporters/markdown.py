from __future__ import annotations

from sisyphus_core.core.plans.models import PlanDocument, Todo, TodoStatus


class MarkdownExporter:
    @staticmethod
    def export(plan_document: PlanDocument) -> str:
        lines: list[str] = []

        lines.append("# 사용자의 최초 요청")
        lines.append("")

        for plan in plan_document.work_plans:
            lines.append(plan.name)
            lines.append("")

        lines.append("# TODOs")
        lines.append("")

        for plan in plan_document.work_plans:
            for todo in plan.todos:
                MarkdownExporter._format_todo(todo, lines, indent=0)

        has_refs = any(plan.references for plan in plan_document.work_plans)
        if has_refs:
            lines.append("")
            lines.append("## References")
            lines.append("")
            for plan in plan_document.work_plans:
                for ref in plan.references:
                    if ref.uri:
                        lines.append(f"- [{ref.ref_id}]: {ref.uri}")
                    elif ref.inline:
                        lines.append(f"- [{ref.ref_id}]: {ref.inline}")

        return "\n".join(lines)

    @staticmethod
    def _format_todo(todo: Todo, lines: list[str], indent: int) -> None:
        prefix = "   " * indent
        checkbox = "[x]" if todo.computed_status == TodoStatus.completed else "[ ]"
        lines.append(f"{prefix}- {checkbox} {todo.id}. {todo.title}")

        if todo.children:
            for child in todo.children:
                MarkdownExporter._format_todo(child, lines, indent + 1)
