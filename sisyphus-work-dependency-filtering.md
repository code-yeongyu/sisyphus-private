# sisyphus work 의존성 필터링 기능 추가

## 목표
`sisyphus work` 명령어에서 다중 계획서 선택 시, 의존성이 모두 해결된 계획서만 후보로 표시하도록 개선

## 현재 문제점
- `work.py`의 `_detect_plan_path()` 함수가 `.sisyphus/tasks/`의 모든 YAML 파일을 표시
- `depends_on` 의존성 해결 여부를 전혀 확인하지 않음
- 사용자가 의존성 미해결 계획서를 선택하면 실행 오류 발생 가능

## 작업 내역

### Task 1: 의존성 검증 함수 구현
**파일**: `sisyphus/cli/work.py`

**추가할 함수 1**: `_is_plan_executable()`
```python
async def _is_plan_executable(
    plan_path: Path,
    tasks_dir: Path
) -> bool:
    """
    계획서의 depends_on이 모두 완료되었는지 확인

    Args:
        plan_path: 검증할 계획서 경로
        tasks_dir: .sisyphus/tasks 디렉토리 경로

    Returns:
        실행 가능하면 True, 아니면 False
    """
    from sisyphus.core.plans.loader import load_plan

    try:
        plan_doc = await load_plan(plan_path)

        for work_plan in plan_doc.work_plans:
            # depends_on이 없으면 즉시 실행 가능
            if not work_plan.depends_on:
                return True

            # 모든 의존성 확인
            for dep_id in work_plan.depends_on:
                if not await _is_dependency_satisfied(dep_id, tasks_dir):
                    return False

        return True
    except Exception:
        # 파싱 실패 시 실행 불가능으로 간주
        return False
```

**추가할 함수 2**: `_is_dependency_satisfied()`
```python
async def _is_dependency_satisfied(
    dep_id: str,
    tasks_dir: Path
) -> bool:
    """
    의존성이 완료되었는지 확인

    Args:
        dep_id: 의존성 ID (file:..., registry:..., 또는 단순 plan-id)
        tasks_dir: .sisyphus/tasks 디렉토리 경로

    Returns:
        의존성이 완료되었으면 True, 아니면 False
    """
    from sisyphus.core.plans.loader import load_plan

    # file:path/to/plan.yaml#plan-id 형식 처리
    if dep_id.startswith("file:"):
        file_ref = dep_id[5:]  # "file:" 제거
        if "#" in file_ref:
            file_path_str, plan_id = file_ref.split("#", 1)
            file_path = tasks_dir / file_path_str
        else:
            file_path = tasks_dir / file_ref
            plan_id = None

    # registry:plan-id 형식 처리
    elif dep_id.startswith("registry:"):
        # registry에서 실제 파일 경로 조회
        registry_path = tasks_dir.parent / "registry.yaml"
        if not registry_path.exists():
            return False

        # registry.yaml 파싱하여 plan_id → 파일 경로 매핑 조회
        # (실제 구현 필요: registry 형식에 따라)
        return False  # 임시

    # 단순 plan-id 형식 (로컬 검색)
    else:
        for yaml_file in tasks_dir.glob("*.yaml"):
            try:
                plan_doc = await load_plan(yaml_file)
                for wp in plan_doc.work_plans:
                    if wp.id == dep_id:
                        return wp.execution.completed
            except Exception:
                continue
        return False

    # file: 참조인 경우 파일 확인
    if not file_path.exists():
        return False

    plan_doc = await load_plan(file_path)

    # plan_id 지정된 경우 해당 plan 찾기
    if plan_id:
        for wp in plan_doc.work_plans:
            if wp.id == plan_id:
                return wp.execution.completed
        return False

    # plan_id 없으면 첫 번째 plan 확인
    if plan_doc.work_plans:
        return plan_doc.work_plans[0].execution.completed

    return False
```

---

### Task 2: `_detect_plan_path()` 함수 수정
**파일**: `sisyphus/cli/work.py` (Line 125-193)

**수정 내용**:
```python
async def _detect_plan_path(ui: UIProtocol, worktree_root: Path) -> Path | None:
    """Detect plan path from .sisyphus/tasks/ directory (v3.0 YAML format).

    If multiple YAML files exist, prompts user for selection.
    Only shows plans with all dependencies satisfied.  # 🆕 추가
    """
    tasks_dir = worktree_root / ".sisyphus" / "tasks"

    if not tasks_dir.exists():
        await ui.show_status(
            "[yellow]No '.sisyphus/tasks/' directory found.[/yellow]\n\n"
            "Create v3.0 YAML plan:\n"
            "  mkdir -p .sisyphus/tasks\n"
            "  vi .sisyphus/tasks/my-plan.yaml"
        )
        return None

    # 재귀 탐색 + 대소문자 무시
    yaml_files = []
    for pattern in ("**/*.yaml", "**/*.yml", "**/*.YAML", "**/*.YML"):
        yaml_files.extend(tasks_dir.glob(pattern))
    yaml_files = list(set(yaml_files))
    yaml_files.sort(key=lambda p: p.name)

    # 🆕 추가: 의존성 해결 가능한 파일만 필터링
    executable_plans = []
    for yaml_file in yaml_files:
        if await _is_plan_executable(yaml_file, tasks_dir):
            executable_plans.append(yaml_file)

    if len(executable_plans) == 0:
        await ui.show_status(
            "[yellow]No executable plans found.[/yellow]\n\n"
            "All plans have unresolved dependencies. Complete dependency plans first."
        )
        return None
    elif len(executable_plans) == 1:
        return executable_plans[0].absolute()
    else:
        # 다중 선택 로직 (executable_plans 사용)
        rel_paths = [f.relative_to(worktree_root) for f in executable_plans]

        await ui.show_status(
            f"[yellow]Multiple executable plans found ({len(executable_plans)} files).[/yellow]\n\nAvailable plans:"
        )

        for idx, path in enumerate(rel_paths, start=1):
            await ui.show_status(f"  {idx}. {path}")

        # 입력 받기 (기존과 동일)
        if isinstance(ui, TUI):
            await ui.show_status(f"\n[yellow]Enter selection (1-{len(executable_plans)}):[/yellow]")
            selection = await ui.get_input()
            if selection is None:
                raise ValueError("User cancelled selection")
        else:
            selection = str(
                await anyio.to_thread.run_sync(
                    lambda: typer.prompt(f"Select plan (1-{len(executable_plans)})", default=1, type=int)
                )
            )

        try:
            idx = int(selection) - 1
            if idx < 0 or idx >= len(executable_plans):
                raise ValueError("Index out of range")
            return executable_plans[idx].absolute()
        except (ValueError, IndexError) as e:
            await ui.show_status(f"[red]Invalid selection: {selection}[/red]")
            raise ValueError(f"Invalid plan selection: {selection}") from e
```

---

### Task 3: import 추가
**파일**: `sisyphus/cli/work.py` (상단)

**추가할 import**:
```python
from sisyphus.core.plans.loader import load_plan
```

---

### Task 4: 테스트 작성
**파일**: `sisyphus/cli/tests/test_work.py` (신규 또는 기존)

**테스트 케이스**:
1. `test_is_plan_executable__if_no_dependencies__returns_true`
2. `test_is_plan_executable__if_dependency_completed__returns_true`
3. `test_is_plan_executable__if_dependency_not_completed__returns_false`
4. `test_is_dependency_satisfied__if_file_reference_completed__returns_true`
5. `test_is_dependency_satisfied__if_file_not_exists__returns_false`
6. `test_detect_plan_path__if_all_plans_have_unresolved_deps__shows_warning`

---

## 검증 기준

1. **기능 검증**:
   - 의존성 없는 계획서는 항상 표시됨
   - 의존성이 모두 완료된 계획서만 표시됨
   - 의존성 미완료 계획서는 숨겨짐
   - 실행 가능한 계획서가 없으면 안내 메시지 표시

2. **의존성 형식 지원**:
   - `file:path/to/plan.yaml#plan-id` ✓
   - `registry:plan-id` ✓
   - 단순 `plan-id` (로컬 검색) ✓

3. **성능**:
   - 파일 수가 적으면 (<10개) 체감 지연 없음
   - 파일 수가 많으면 (>50개) 캐싱 고려 필요

---

## 주의사항

1. **PlanLinter와의 관계**:
   - PlanLinter는 순환 의존성 검증
   - 이 기능은 의존성 완료 여부 확인
   - 두 기능은 독립적

2. **`sisyphus task continue`와의 차이**:
   - `task continue`는 DFS로 자동 순서 결정
   - `work`는 사용자가 직접 선택 (필터링만 제공)

3. **registry 참조 구현**:
   - registry.yaml 형식 확인 필요
   - 현재 임시로 `return False` 처리

---

## 예상 사용자 경험

**Before**:
```
Multiple YAML plans found (5 files).

Available plans:
  1. .sisyphus/tasks/backend.yaml
  2. .sisyphus/tasks/frontend.yaml  # depends_on: [backend]
  3. .sisyphus/tasks/database.yaml
  4. .sisyphus/tasks/api.yaml       # depends_on: [database]
  5. .sisyphus/tasks/deploy.yaml    # depends_on: [api, frontend]

Enter selection (1-5): 5  # 선택 가능하지만 의존성 미해결로 실패
```

**After**:
```
Multiple executable plans found (2 files).

Available plans:
  1. .sisyphus/tasks/backend.yaml
  2. .sisyphus/tasks/database.yaml

Enter selection (1-2): 1  # frontend, api, deploy는 숨겨짐 (의존성 미해결)
```

---

## 구현 순서

1. `_is_dependency_satisfied()` 함수 구현
2. `_is_plan_executable()` 함수 구현
3. `_detect_plan_path()` 함수 수정 (필터링 로직 추가)
4. import 추가
5. 테스트 작성 및 실행
6. 수동 테스트 (다양한 의존성 시나리오)

---

이렇게 구현하면 **의존성이 모두 해결된 계획서만 선택지로 표시**됩니다!
