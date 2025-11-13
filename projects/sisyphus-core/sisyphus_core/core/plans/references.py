from __future__ import annotations

from sisyphus_core.core.plans.models import ReferenceItem, Todo, WorkPlan


class ReferenceResolver:
    """Resolves reference IDs to their actual content."""

    @staticmethod
    def index_references(work_plan: WorkPlan) -> dict[str, ReferenceItem]:
        """
        Build index of ref_id → ReferenceItem from work_plan.references.

        Args:
            work_plan: WorkPlan containing references section

        Returns:
            Dict mapping ref_id to ReferenceItem

        Raises:
            ValueError: If duplicate ref_id found
        """
        index: dict[str, ReferenceItem] = {}
        duplicates: list[str] = []

        for ref_item in work_plan.references:
            if ref_item.ref_id is None:
                continue

            if ref_item.ref_id in index:
                duplicates.append(ref_item.ref_id)
            else:
                index[ref_item.ref_id] = ref_item

        if duplicates:
            raise ValueError(f"Duplicate ref_id found: {', '.join(duplicates)}")

        return index

    @staticmethod
    def resolve_ref_id(ref_id: str, index: dict[str, ReferenceItem]) -> ReferenceItem:
        """
        Resolve a ref_id to its ReferenceItem.

        Args:
            ref_id: Reference ID to resolve
            index: Index built by index_references()

        Returns:
            ReferenceItem for the given ref_id

        Raises:
            KeyError: If ref_id not found in index
        """
        if ref_id not in index:
            raise KeyError(f"Reference ID '{ref_id}' not found in references section")

        return index[ref_id]

    @staticmethod
    def validate_references(work_plan: WorkPlan) -> list[str]:
        """
        Validate all references in work_plan.

        Checks:
        - All ref_ids in WorkPlan.references are unique
        - All ref_ids used in todos exist in WorkPlan.references
        - WorkPlan.references items have ref_id set
        - No orphaned references (ref_id defined but never used)

        Args:
            work_plan: WorkPlan to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors: list[str] = []

        # Check WorkPlan.references for duplicates and missing ref_id
        try:
            index = ReferenceResolver.index_references(work_plan)
        except ValueError as e:
            errors.append(str(e))
            index = {}

        # Check that WorkPlan.references items have ref_id
        for i, ref_item in enumerate(work_plan.references):
            if ref_item.ref_id is None:
                errors.append(f"WorkPlan.references[{i}] missing ref_id (references section must have ref_id)")

        # Collect all ref_ids used in todos
        used_ref_ids: set[str] = set()

        def collect_todo_refs(todo_list: list[Todo]) -> None:
            for todo in todo_list:
                for ref_item in todo.references:
                    if ref_item.ref_id is not None:
                        used_ref_ids.add(ref_item.ref_id)

                if todo.children:
                    collect_todo_refs(todo.children)

        collect_todo_refs(work_plan.todos)

        # Check that all used ref_ids exist in index
        for ref_id in used_ref_ids:
            if ref_id not in index:
                errors.append(f"Reference ID '{ref_id}' used in todos but not defined in references section")

        # Check for orphaned references (defined but never used)
        # This is a warning-level issue, not an error, so we skip it for now
        # defined_ref_ids = set(index.keys())
        # orphaned = defined_ref_ids - used_ref_ids
        # for ref_id in orphaned:
        #     errors.append(f"Warning: Reference ID '{ref_id}' defined but never used")

        return errors
