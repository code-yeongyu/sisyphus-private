# 사용자의 최초 요청 (기록용)
분명히 말하는데 아직 yaml 기능이 완전히 구현전이니 markdown 형식으로 작성하세요.

sisyphus cli 에 지금 continue-work 가 구현이 안돼있고 show previous 가 없습니다

이를 구현하고 싶습니다.

continue work 는 아직 작업시작전이라면 작업을 시작상태로 바꾸고 1번 작업으로 이동해야합니다. 참고로 todo 자체가 아예없는 경우는 린터가 잡아주어야 합니다.
그리고 작업이 진행중인 상태에서 continue work 를 진행하면 verified 상태를 모두 검증하고서 넘길 수 있는 경우에서만 넘기게 됩니다. 그렇지 않을경우 아직 verify 가 안되어서 넘길 수 없다며 거절해야 합니다.

show previous 는 show next 와 비슷하게 돌되, 방금전까지 어떤 작업을 했는지에 대해서의 맥락을 제공하기 위해서 그렇습니다.

## 추가 사용자 요청 (기록용)
없음

# 작업 목표 (WHAT & WHY)

## 핵심 목표 (TL;DR)
sisyphus CLI에 `continue-work`와 `show previous` 명령어를 구현하여 작업 네비게이션을 개선

## 상세 목표
- `continue-work` 명령어: 작업 시작 및 진행 상태 자동 관리
  - 미시작 → 작업 시작 상태로 변경 + 첫 작업 이동
  - 진행중 → verification 검증 후 조건부 다음 작업 이동
- `show previous` 명령어: 이전 작업 조회로 작업 맥락 제공
- Linter 검증: Todo 없을 경우 에러 처리

# 작업 배경 (WHY & WHAT - 현재 상태)

## 현재 상황
- `task.py`의 `continue_work` 함수는 구현 스텁만 존재 (line 101-111)
- `show_next`는 구현되어 있으나 `show_previous`는 없음
- `PlanNavigator`는 `get_next_task()`는 있으나 `get_previous_task()` 없음
- Verification 상태 검증 로직 없음

## 변경 이유
- 작업 재개시 수동으로 상태 변경해야 하는 불편함
- 이전 작업 맥락 확인 불가능
- Verification 미완료시 다음 작업으로 넘어가는 문제

## 변경할 내용
- 현재: `continue_work` 스텁, `show_previous` 없음
- 변경: 완전 구현된 `continue_work`, 새로운 `show_previous` 명령어

# 작업 시작 여부
is_execution_started = TRUE

# 전체 목표 달성 여부
is_all_goals_accomplished = FALSE

# 병렬 실행
parallel_requested = FALSE

# 현재 진행 중인 작업
- [x] 4. `continue_work` 명령어 완전 구현

# 필수 배경 지식
Sisyphus CLI는 Python 3.12+ 기반의 LLM agent orchestration CLI입니다.
- Typer로 CLI 라우팅
- YAML v2.1 WorkPlan 형식 (plan_types.py)
- PlanNavigator로 task 탐색 (DFS 알고리즘)
- anyio 기반 async (Protocol pattern)

## 파일 구조 및 역할
- `projects/sisyphus-cli/sisyphus/cli/task.py`: Task 관련 CLI 명령어들
- `projects/sisyphus-cli/sisyphus/core/plan_navigator.py`: Task 탐색 로직 (get_current_task, get_next_task 등)
- `projects/sisyphus-cli/sisyphus/utils/plan_types.py`: WorkPlan Pydantic 모델 (Status, Todo, VerificationItem 등)
- `projects/sisyphus-cli/sisyphus/core/plan_linter.py`: YAML 검증 로직
- `projects/sisyphus-cli/sisyphus/core/plan_loader.py`: YAML 로드/저장

**Note**: 모든 명령어는 프로젝트 루트(`/Users/yeongyu/local-workspaces/sisyphus`)에서 실행

## 참고 파일 및 컨텍스트 이해

### 1. `projects/sisyphus-cli/sisyphus/cli/task.py`
- **역할**: Task 관련 CLI 명령어 정의
- **검색할 내용**: `show_current`, `show_next` 함수 구조
- **핵심 패턴**:
  - Typer decorator 사용 (`@task_app.command`)
  - PlanLoader로 YAML 로드
  - PlanNavigator로 task 조회
  - `print_task`로 출력
- **코드 스니펫** (line 49-98):
```python
@task_app.command(name="current")
def show_current(
    rich: bool = typer.Option(False, "--rich", help="Use Rich table format"),
    cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
) -> None:
    working_dir = resolve_cwd(cwd)
    plan_path = working_dir / "ai-todolist.yaml"

    try:
        loader = PlanLoader(plan_path)
        plan = loader.load()
        navigator = PlanNavigator(plan)

        task = navigator.get_current_task()
        if task is None:
            console.print("[yellow]작업이 시작되지 않았습니다[/yellow]")
            raise typer.Exit(0)

        output_format = OutputFormat.RICH if rich else OutputFormat.PLAIN
        print_task(task, format=output_format)

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
```

### 2. `projects/sisyphus-cli/sisyphus/core/plan_navigator.py`
- **역할**: DFS 기반 Task 탐색
- **검색할 내용**: `get_current_task`, `get_next_task` 함수
- **핵심 패턴**:
  - `plan.status.work_mode.current_task_id`로 현재 작업 추적
  - DFS 순서: children → sibling → parent's sibling
  - `check_task_completion` 으로 verification 검증
- **구현할 메서드**: `get_previous_task()` (역방향 DFS)

### 3. `projects/sisyphus-cli/sisyphus/utils/plan_types.py`
- **역할**: Pydantic models (WorkPlan, Todo, Status 등)
- **검색할 내용**:
  - `TodoStatus` enum (line 10-13): `pending`, `in_progress`, `completed`
  - `Status` 클래스 (line 192-197): `execution.started`, `work_mode.current_task_id`
  - `VerificationItem` (line 60-76): `verified` 필드
- **Notes**:
  - `Status.execution.started`가 작업 시작 여부
  - `Status.work_mode.current_task_id`가 현재 작업 ID

### 4. `projects/sisyphus-cli/sisyphus/core/plan_linter.py`
- **역할**: YAML 검증 (schema, references, cycles 등)
- **검색할 내용**: `_validate_todos` 함수 (line 568-579)
- **추가할 검증**: todos가 empty list일 때 에러

# 작업 흐름 (HOW - Task Flow & Dependencies)

## Task Dependency Diagram
```
Task 1 (PlanNavigator에 get_previous_task 추가)
   ↓
Task 2 (show previous 명령어 구현)
   ↓
Task 3 (PlanLinter에 empty todos 검증 추가)
   ↓
Task 4 (continue_work 명령어 구현) ← Task 3에 의존
   ↓
Task 5 (통합 테스트 작성)
```

## 단계별 설명
- **Phase 1 (Task 1-2)**: PlanNavigator 확장 및 show previous 구현 (역방향 탐색 로직)
- **Phase 2 (Task 3-4)**: Linter 검증 추가 후 continue_work 구현 (linter가 empty 체크)
- **Phase 3 (Task 5)**: 전체 통합 테스트 (모든 기능 검증)

# 작업 계획

## 프로젝트 커밋 메시지 스타일
```
feat: add new feature
fix: fix bug
refactor: refactor code
test: add tests
docs: update docs
```

# TODOs

- [x] 1. PlanNavigator에 `get_previous_task()` 메서드 추가

   **참고 소스**:
   - 파일: `projects/sisyphus-cli/sisyphus/core/plan_navigator.py` (line 40-80에서 `get_next_task` 찾기)
   - 패턴: DFS 역순 탐색 (next의 반대 방향)

   - [ ] 1.1 구현: `get_previous_task()` 메서드 작성

      **검색할 패턴**: `get_next_task` 함수 (line 40-80)

      **get_previous_task() 로직 (상세)**:

      **목적**: 현재 작업의 "바로 이전에 실행되었을" 작업 찾기

      **DFS 순서 예시**:
      - 정방향: `1 → 1.1 → 1.1.1 → 1.1.2 → 1.2 → 2`
      - 역방향 (previous): `2 ← 1.2 ← 1.1.2 ← 1.1.1 ← 1.1 ← 1`

      **구현 로직**:
      ```python
      def get_previous_task(self, current_id: str | None = None) -> Todo | None:
          """Get previous task in DFS traversal order (reverse).

          Reverse DFS order:
          1. current=None or first task → return None
          2. Has previous sibling → return last descendant of previous sibling
          3. No previous sibling → return parent
          """
          if current_id is None:
              current_id = self.plan.status.work_mode.current_task_id

          if current_id is None:
              return None  # No current task

          current = self.find_todo_by_id(current_id)
          if current is None:
              raise ValueError(f"작업 ID를 찾을 수 없습니다: {current_id}")

          # 1. Find previous sibling
          siblings = self._get_siblings(current_id)
          if siblings is not None:
              for i, sibling in enumerate(siblings):
                  if sibling.id == current_id and i > 0:
                      # Found previous sibling
                      previous_sibling = siblings[i - 1]
                      # Return last descendant of previous sibling
                      return self._get_last_descendant(previous_sibling)

          # 2. No previous sibling → return parent
          parent = self._find_parent(current_id)
          return parent

      def _get_last_descendant(self, todo: Todo) -> Todo:
          """Get last descendant (deepest rightmost node) of a todo."""
          current = todo
          while current.children:
              current = current.children[-1]  # Last child
          return current
      ```

      **예시**:
      - `current_id = "1.2"`: 이전 sibling `1.1` → 마지막 descendant `1.1.2` 리턴
      - `current_id = "1.1"`: 이전 sibling 없음 → parent `1` 리턴
      - `current_id = "1"`: 첫 작업 → `None` 리턴
      - `current_id = "1.1.1"`: 이전 sibling 없음 → parent `1.1` 리턴

      **Status 고려**: Status 무관 (모든 작업 포함, show previous는 맥락 확인용)

      **구현 세부사항**:
      - Current: `get_next_task`만 존재
      - Change: `get_previous_task` + `_get_last_descendant` 헬퍼 메서드 추가
      - 리턴: 이전 작업 Todo 또는 None (첫 작업이면)

   - [ ] 1.2 테스트: `test_plan_navigator.py`에 테스트 추가

      **테스트 패턴**: 기존 `get_next_task` 테스트 참조

      **테스트 케이스**:
      - current_id=None일 때: None 리턴
      - 첫 작업일 때: None 리턴
      - 중간 작업일 때: 이전 sibling 리턴
      - child의 첫 작업일 때: parent 리턴

   - [ ] 1.3 Lint 및 type check
      - [ ] `uv run ruff check projects/sisyphus-cli/sisyphus/core/plan_navigator.py` → 0 errors
      - [ ] `uv run basedpyright projects/sisyphus-cli/sisyphus/core/plan_navigator.py` → 0 errors

   - [ ] 1.4 테스트 실행 및 검증

      **실행 명령어**: `uv run pytest projects/sisyphus-cli/sisyphus/core/tests/test_plan_navigator.py -xvs`

      **예상 출력**:
      ```
      test_get_previous_task__if_first_task__returns_none PASSED
      test_get_previous_task__if_middle_task__returns_sibling PASSED
      ===================== 2 passed =====================
      ```

   - [ ] 1.5 커밋
      - 작업 완료 확인 후 커밋
      - 예시: `git add projects/sisyphus-cli/sisyphus/core/plan_navigator.py projects/sisyphus-cli/sisyphus/core/tests/test_plan_navigator.py && git commit -m "feat: add get_previous_task to PlanNavigator"`

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] `get_previous_task` 메서드가 `plan_navigator.py`에 정확히 추가되었는가?
      - [ ] DFS 역방향 로직이 올바르게 구현되었는가?
      - [ ] 테스트가 `test_plan_navigator.py`에 추가되었는가?
      - [ ] `uv run pytest projects/sisyphus-cli/sisyphus/core/tests/test_plan_navigator.py -xvs` → 모든 테스트 PASSED 확인
      - [ ] `uv run ruff check projects/sisyphus-cli/sisyphus/core/plan_navigator.py` → 0 errors 확인
      - [ ] `uv run basedpyright projects/sisyphus-cli/sisyphus/core/plan_navigator.py` → 0 errors 확인
      - [ ] git commit 완료? (`git log -1 --oneline` 확인)

- [x] 2. `show previous` CLI 명령어 구현

   ### show previous의 정확한 동작

   **정의**: DFS 순회 순서에서 현재 작업의 직전 노드 반환 (작업 상태 무관)

   **예시**:
   - DFS 순서: 1 → 1.1 → 1.1.1 → 1.1.2 → 1.2 → 2
   - 현재 작업 1.2 → previous는 1.1.2 (마지막 완료 작업이 아님)
   - 현재 작업 1 → previous는 None (첫 작업)

   **히스토리 기반 아님**: WorkPlan에 작업 히스토리 필드가 없으므로, "마지막 완료 작업"이 아닌 "DFS 구조상 이전 노드"를 반환합니다.

   **참고 소스**:
   - 파일: `projects/sisyphus-cli/sisyphus/cli/task.py` (line 75-98에서 `show_next` 찾기)
   - 패턴: `show_next`와 동일한 구조, `navigator.get_next_task()` → `navigator.get_previous_task()` 변경

   - [x] 2.1 구현: `show_previous` 함수 추가

      **코드 패턴 참조**: `show_next` (line 75-98)

      **코드 스니펫**:
      ```python
      @task_app.command(name="next")
      def show_next(
          rich: bool = typer.Option(False, "--rich", help="Use Rich table format"),
          cwd: str | None = typer.Option(None, "--cwd", help="Working directory"),
      ) -> None:
          working_dir = resolve_cwd(cwd)
          plan_path = working_dir / "ai-todolist.yaml"

          try:
              loader = PlanLoader(plan_path)
              plan = loader.load()
              navigator = PlanNavigator(plan)

              task = navigator.get_next_task()  # ← 여기를 get_previous_task()로
              if task is None:
                  console.print("[green]모든 작업이 완료되었습니다![/green]")
                  raise typer.Exit(0)

              output_format = OutputFormat.RICH if rich else OutputFormat.PLAIN
              print_task(task, format=output_format)

          except FileNotFoundError as e:
              console.print(f"[red]{e}[/red]")
              raise typer.Exit(1)
      ```

      **구현 세부사항**:
      - Current: `show_previous` 없음
      - Change: `show_next` 복사 후 수정
      - Decorator: `@task_app.command(name="previous")`
      - 함수명: `show_previous`
      - 메시지 처리 (task가 None일 때):
        ```python
        if task is None:
            if plan.status.execution.started:
                console.print("[yellow]첫 작업입니다[/yellow]")
            else:
                console.print("[yellow]작업이 시작되지 않았습니다[/yellow]")
            raise typer.Exit(0)
        ```
      - 이유: 작업 시작 전과 첫 작업 도달 구분

   - [x] 2.2 테스트: CLI 명령어 테스트 작성

      **테스트 파일**: `tests/cli/test_task_commands.py` (새로 생성 또는 기존 파일)

      **테스트 케이스**:
      - 첫 작업일 때: "첫 작업입니다" 메시지
      - 이전 작업 있을 때: task 정보 출력

   - [x] 2.3 Lint 및 type check
      - [x] `uv run ruff check projects/sisyphus-cli/sisyphus/cli/task.py` → 0 errors
      - [x] `uv run basedpyright projects/sisyphus-cli/sisyphus/cli/task.py` → 0 errors

   - [x] 2.4 수동 테스트

      **실행 명령어**: `uv run sisyphus task previous --cwd /path/to/test/plan`

      **예상 동작**:
      - 첫 작업: "[yellow]첫 작업입니다[/yellow]"
      - 이전 작업 존재: task ID, title 출력

   - [x] 2.5 커밋
      - 예시: `git add projects/sisyphus-cli/sisyphus/cli/task.py projects/sisyphus-cli/tests/cli/test_task_commands.py && git commit -m "feat: add show previous command"`

   - [x] **작업 완료 검증 체크리스트**
      - [x] `show_previous` 함수가 `task.py`에 정확히 추가되었는가?
      - [x] `@task_app.command(name="previous")` decorator가 있는가?
      - [x] `navigator.get_previous_task()` 호출하는가?
      - [x] 테스트가 작성되었는가?
      - [x] `uv run sisyphus task previous` 명령어가 작동하는가?
      - [x] `uv run ruff check projects/sisyphus-cli/sisyphus/cli/task.py` → 0 errors 확인
      - [x] `uv run basedpyright projects/sisyphus-cli/sisyphus/cli/task.py` → 0 errors 확인
      - [x] git commit 완료?

- [x] 3. PlanLinter에 empty todos 검증 추가

   **참고 소스**:
   - 파일: `projects/sisyphus-cli/sisyphus/core/plan_linter.py` (line 568-579에서 `_validate_todos` 찾기)
   - 로직: `todos`가 empty list일 때 LintError 추가

   - [x] 3.1 구현: `_validate_todos`에 empty check 추가

      **검색할 패턴**: `_validate_todos` 함수 (line 568-579)

      **구현 세부사항**:
      - Current: type check만 존재
      - Change: empty list check 추가
      - 조건: `if isinstance(todos, list) and len(todos) == 0:`
      - 에러: `LintError(location="todos", message="Empty todos list", expected="at least one todo", actual="empty list")`

   - [x] 3.2 테스트: empty todos 케이스 테스트 추가

      **테스트 파일**: `projects/sisyphus-cli/sisyphus/core/tests/test_plan_linter.py`

      **테스트 케이스**:
      ```python
      def test_validate_todos__if_empty__returns_error():
          # given
          data = {"todos": []}
          linter = PlanLinter({})

          # when
          errors = linter.lint(data)

          # then
          assert any(e.location == "todos" and "empty" in e.message.lower() for e in errors)
      ```

   - [x] 3.3 Lint 및 type check
      - [x] `uv run ruff check projects/sisyphus-cli/sisyphus/core/plan_linter.py` → 0 errors
      - [x] `uv run basedpyright projects/sisyphus-cli/sisyphus/core/plan_linter.py` → 0 errors

   - [x] 3.4 테스트 실행

      **실행 명령어**: `uv run pytest projects/sisyphus-cli/sisyphus/core/tests/test_plan_linter.py::test_validate_todos__if_empty__returns_error -xvs`

      **예상 출력**: PASSED

   - [x] 3.5 커밋
      - 예시: `git add projects/sisyphus-cli/sisyphus/core/plan_linter.py projects/sisyphus-cli/sisyphus/core/tests/test_plan_linter.py && git commit -m "feat: add empty todos validation to PlanLinter"`

   - [x] **작업 완료 검증 체크리스트**
      - [x] `_validate_todos`에 empty check 로직이 추가되었는가?
      - [x] LintError가 올바르게 생성되는가?
      - [x] 테스트가 통과하는가?
      - [x] `uv run pytest projects/sisyphus-cli/sisyphus/core/tests/test_plan_linter.py -xvs` → PASSED 확인
      - [x] `uv run ruff check projects/sisyphus-cli/sisyphus/core/plan_linter.py` → 0 errors 확인
      - [x] git commit 완료?

- [x] 4. `continue_work` 명령어 완전 구현

   **참고 소스**:
   - 파일: `projects/sisyphus-cli/sisyphus/cli/task.py` (line 101-111, 현재 스텁)
   - 로직:
     1. Plan 로드
     2. `status.execution.started` 확인
     3. 미시작 → `started=True`, `current_task_id=첫 task ID` 설정
     4. 시작됨 → `check_task_completion` 호출, verification 검증
     5. 조건 충족시 `current_task_id` 업데이트, Plan 저장

   - [ ] 4.1 구현: `continue_work` 함수 재작성

      **필요한 imports** (task.py 파일 상단에 추가):
      ```python
      # 기존 imports (line 1-12):
      from datetime import UTC, datetime  # 이미 존재 (line 4)

      # 추가 필요한 imports:
      from sisyphus.utils.plan_types import TodoStatus  # 추가 필요
      # Note: CompletionReport는 런타임 import 불필요 (타입 힌트용)
      ```

      **CompletionReport 구조** (참고용):
      ```python
      # navigator.check_task_completion() 리턴 타입
      # from sisyphus.core.plan_navigator import CompletionReport

      @dataclass
      class CompletionReport:
          task_id: str | int
          task_status: TodoStatus
          all_children_completed: bool
          children_summary: dict[str, int]  # {'completed': N, 'in_progress': M, 'pending': K}
          all_verifications_completed: bool
          verification_summary: dict[str, int]  # {'completed': N, 'total': M}
          can_complete: bool
      ```

      **구현 세부사항**:
      ```python
      # 1. Plan 로드
      loader = PlanLoader(plan_path)
      plan = loader.load()
      navigator = PlanNavigator(plan)

      # 2. 작업 시작 여부 확인
      if not plan.status.execution.started:
          # 2-1. 첫 작업 찾기
          first_task = navigator.get_next_task(current_id=None)
          if first_task is None:
              # Linter가 이미 잡아야 함
              console.print("[red]작업이 없습니다[/red]")
              raise typer.Exit(1)

          # 2-2. 상태 업데이트
          plan.status.execution.started = True
          plan.status.execution.started_at = datetime.now(UTC).isoformat()
          plan.status.work_mode.current_task_id = first_task.id

          # 2-3. 첫 작업을 in_progress로
          first_task.status = TodoStatus.in_progress
          first_task.status_changed_at = datetime.now(UTC).isoformat()

          loader.save(plan)
          console.print(f"[green]작업을 시작합니다: {first_task.title}[/green]")
          return

      # 3. 진행중 → verification 검증
      current_task_id = plan.status.work_mode.current_task_id
      if current_task_id is None:
          console.print("[red]현재 작업 ID가 없습니다[/red]")
          raise typer.Exit(1)

      report = navigator.check_task_completion(current_task_id)

      # 자식 완료 AND 검증 완료 모두 체크
      if not report.can_complete:
          console.print("[yellow]다음 작업으로 넘어갈 수 없습니다[/yellow]")

          if not report.all_children_completed:
              descendants = navigator.get_all_descendants(current_task_id)
              console.print(f"자식 작업: {report.children_summary['completed']}/{len(descendants)} 완료")

          if not report.all_verifications_completed:
              console.print(f"검증: {report.verification_summary['completed']}/{report.verification_summary['total']} 완료")

          raise typer.Exit(1)

      # 4. 현재 작업 완료 처리
      current_task = navigator.find_todo_by_id(current_task_id)
      current_task.status = TodoStatus.completed
      current_task.status_changed_at = datetime.now(UTC).isoformat()

      # 5. 다음 작업으로 이동
      next_task = navigator.get_next_task(current_task_id)
      if next_task is None:
          plan.status.execution.completed = True
          plan.status.execution.completed_at = datetime.now(UTC).isoformat()
          plan.status.work_mode.current_task_id = None
          loader.save(plan)
          console.print("[green]모든 작업이 완료되었습니다![/green]")
          return

      next_task.status = TodoStatus.in_progress
      next_task.status_changed_at = datetime.now(UTC).isoformat()
      plan.status.work_mode.current_task_id = next_task.id

      loader.save(plan)
      console.print(f"[green]다음 작업으로 이동: {next_task.title}[/green]")

      # Note: status.progress 필드는 이 구현에서 갱신하지 않음
      # (기존 CLI 코드 전반에서 progress 갱신을 강제하지 않음)
      # 필요시 별도 이슈로 전체 CLI 통일 작업 진행
      ```

   - [ ] 4.2 테스트: `continue_work` 통합 테스트 작성

      **테스트 케이스**:
      - 작업 미시작 → 첫 작업으로 이동
      - 자식 작업 미완료 (검증은 완료) → 에러 및 자식 작업 상태 출력
      - Verification 미완료 (자식은 완료) → 에러 및 검증 상태 출력
      - 자식 AND 검증 모두 완료 → 다음 작업으로 이동
      - 마지막 작업 완료 → "모든 작업 완료" 메시지

      **추가 테스트 함수 예시**:
      ```python
      def test_continue_work__if_children_incomplete__rejects():
          # given: 현재 작업의 자식 1개 pending, 검증은 완료
          # when: continue_work 실행
          # then: 에러 메시지 "자식 작업 1/2 완료", Exit(1)
      ```

   - [ ] 4.3 Lint 및 type check
      - [ ] `uv run ruff check projects/sisyphus-cli/sisyphus/cli/task.py` → 0 errors
      - [ ] `uv run basedpyright projects/sisyphus-cli/sisyphus/cli/task.py` → 0 errors

   - [ ] 4.4 수동 테스트

      **테스트 시나리오**:
      1. 새 plan → `continue_work` → 첫 작업 시작
      2. Verification 없는 상태 → `continue_work` → 에러
      3. Verification 완료 → `continue_work` → 다음 작업 이동

   - [ ] 4.5 커밋
      - 예시: `git add projects/sisyphus-cli/sisyphus/cli/task.py projects/sisyphus-cli/tests/cli/test_task_commands.py && git commit -m "feat: implement continue_work command"`

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] `continue_work` 함수가 완전히 구현되었는가?
      - [ ] 작업 미시작시 첫 작업으로 이동하는가?
      - [ ] Verification 검증 로직이 있는가?
      - [ ] Verification 미완료시 에러를 출력하는가?
      - [ ] Plan 저장이 올바르게 되는가?
      - [ ] 테스트가 통과하는가?
      - [ ] `uv run ruff check projects/sisyphus-cli/sisyphus/cli/task.py` → 0 errors 확인
      - [ ] `uv run basedpyright projects/sisyphus-cli/sisyphus/cli/task.py` → 0 errors 확인
      - [ ] 수동 테스트 3가지 시나리오 모두 통과하는가?
      - [ ] git commit 완료?

- [ ] 5. 통합 테스트 작성 및 전체 기능 검증

   **참고 소스**:
   - 테스트 파일: `projects/sisyphus-cli/tests/integration/test_full_workflow.py` (새로 생성)
   - 시나리오: 실제 YAML plan으로 전체 workflow 테스트

   - [ ] 5.1 통합 테스트 작성

      **테스트 시나리오**:
      ```python
      async def test_full_workflow__from_start_to_finish():
          # given: 3개 task가 있는 plan
          plan_yaml = """
          metadata: ...
          todos:
            - id: "1"
              title: "Task 1"
              status: pending
              verification_spec: [...]
            - id: "2"
              title: "Task 2"
              status: pending
            - id: "3"
              title: "Task 3"
              status: pending
          """

          # when/then: continue_work 반복 실행
          # 1. continue_work → Task 1 시작
          # 2. verification 완료 → continue_work → Task 2 이동
          # 3. show previous → Task 1 확인
          # 4. 반복... → 모든 작업 완료

          # verify
          assert plan.status.execution.completed is True
      ```

   - [ ] 5.2 전체 테스트 스위트 실행

      **실행 명령어**: `uv run pytest projects/sisyphus-cli/ -xvs`

      **예상 결과**: 모든 테스트 PASSED

   - [ ] 5.3 Lint 전체 실행

      **실행 명령어**: `uv run ruff check projects/sisyphus-cli/`

      **예상 결과**: 0 errors

   - [ ] 5.4 Type check 전체 실행

      **실행 명령어**: `cd projects/sisyphus-cli && uv run basedpyright`

      **예상 결과**: 0 errors

   - [ ] 5.5 최종 커밋
      - 예시: `git add projects/sisyphus-cli/tests/ && git commit -m "test: add integration tests for continue_work and show_previous"`

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] 통합 테스트가 작성되었는가?
      - [ ] 모든 시나리오가 커버되는가?
      - [ ] `uv run pytest projects/sisyphus-cli/ -xvs` → 모든 테스트 PASSED 확인
      - [ ] `uv run ruff check projects/sisyphus-cli/` → 0 errors 확인
      - [ ] `cd projects/sisyphus-cli && uv run basedpyright` → 0 errors 확인
      - [ ] git commit 완료?
      - [ ] 실제로 `sisyphus task continue`, `sisyphus task previous` 명령어가 작동하는가?

# 성공 비전

## 사용자 관점의 성공
- `sisyphus task continue` 명령어로 작업 재개 가능
- `sisyphus task previous` 명령어로 이전 작업 맥락 확인 가능
- Verification 미완료시 명확한 에러 메시지

## 비즈니스 관점의 성공
- 작업 흐름이 자동화되어 수동 개입 감소
- 작업 맥락 유지로 생산성 향상

## 기술적 성공 기준
- 모든 테스트 통과: `uv run pytest projects/sisyphus-cli/ -xvs` → 100% PASSED
- Lint 에러 0개: `uv run ruff check projects/sisyphus-cli/` → 0 errors
- Type 에러 0개: `cd projects/sisyphus-cli && uv run basedpyright` → 0 errors
- 실제 CLI 명령어 동작: `uv run sisyphus task continue`, `uv run sisyphus task previous`

# 최종 작업 검증 체크리스트
- [ ] 1. **기능이 작동하는가**
  - [ ] `sisyphus task continue` 명령어가 작동하는가?
  - [ ] `sisyphus task previous` 명령어가 작동하는가?
  - [ ] Verification 미완료시 에러가 발생하는가?
  - [ ] Linter가 empty todos를 잡아내는가?

- [ ] 2. **잘못된 구현 방지**
  - [ ] 사용자가 요청한 기능만 구현했는가?
  - [ ] 불필요한 refactoring을 하지 않았는가?

- [ ] 3. **범위 준수 확인**
  - [ ] 계획과 다르게 구현한 부분이 있는가?
  - [ ] 과도하게 구현한 부분이 있는가?

- [ ] 4. **기존 기능 회귀 테스트**
  - [ ] `show_current` 명령어가 여전히 작동하는가?
  - [ ] `show_next` 명령어가 여전히 작동하는가?
  - [ ] 기존 PlanNavigator 메서드들이 작동하는가?
  - [ ] 전체 테스트 스위트 실행: `uv run pytest projects/sisyphus-cli/ -xvs` → 모든 테스트 PASSED
