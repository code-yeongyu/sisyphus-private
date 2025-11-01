# Codex Phase별 상세 계획 (2차)

**작성일**: 2025-11-01
**출처**: Codex GPT-5

---

## Phase Breakdown (전체 6단계)

### Phase 1 – 계획 스키마 및 로더 재구성
- **목표**: v3.0 YAML 스키마 정의, 로더/검증 경로 정리, `status.json` 토대 마련
- **산출물**: 새로운 Pydantic 모델, v3 인식 로더, 기본 `StatusManager`
- **선행 의존성**: 없음
- **복잡도**: High

### Phase 2 – 그래프/검증 코어 구축
- **목표**: 의존성 그래프 구성, 순환/미도달 검증, 상태 추적과 연동
- **산출물**: `core/graph/` 모듈, 검증기, 상태 업데이트 로직
- **선행 의존성**: Phase 1
- **복잡도**: High

### Phase 3 – CLI 리팩터링 (plan/task 앱 분리)
- **목표**: Typer 서브앱 재편, 신규 명령 구조 도입, --cwd 지원
- **산출물**: `cli/plan_app.py`, `cli/task_app.py`, 루트 CLI 배선
- **선행 의존성**: Phase 1, Phase 2 (검증 호출 필요)
- **복잡도**: Medium

### Phase 4 – 참조 시스템 및 변환기
- **목표**: 참조 ID/inline 처리, v2→v3 컨버터, 다중 파일 구성
- **산출물**: `core/converters/`, 참조 해석 모듈
- **선행 의존성**: Phase 1 (모델), Phase 2 (그래프 활용)
- **복잡도**: Medium

### Phase 5 – 상태 워크플로 강화
- **목표**: `status.json` 원자적 갱신, 세션 관리, --cwd 연동
- **산출물**: `core/status/StatusManager` 완성, 동시성 안전성 확보
- **선행 의존성**: Phase 1 (기본 모델), Phase 3 (CLI 경로)
- **복잡도**: Medium

### Phase 6 – 종합 테스트/문서
- **목표**: 통합 테스트, 예제 리소스, 마이그레이션 가이드
- **산출물**: 테스트 확장, `/docs/` 업데이트, `spec-document-example.yaml` 활용
- **선행 의존성**: Phase 1~5
- **복잡도**: Medium

---

## Phase 1 상세 태스크

### Task 1.1: v3 모델 정의
- **File**: `sisyphus/core/plans/models.py`
- **Action**: 생성
- **Implementation**:
  ```python
  class WorkPlan(BaseModel):
      name: str
      tasks: list[Todo]
      references: list[ReferenceItem] | None = None
      depends_on: list[str] = Field(default_factory=list)

  class Todo(BaseModel):
      id: str
      title: str
      description: str | None = None
      status: Literal["pending","in-progress","done"]
      references: list[str] = Field(default_factory=list)

  class ReferenceItem(BaseModel):
      ref_id: str
      uri: HttpUrl | FilePath | None = None
      inline: str | None = None

      @model_validator(mode="after")
      def validate_target(self) -> "ReferenceItem":
          if not (self.uri or self.inline):
              raise ValueError("ReferenceItem must define either uri or inline content.")
          if self.uri and self.inline:
              raise ValueError("ReferenceItem cannot define both uri and inline.")
          return self

  class PlanDocument(BaseModel):
      version: Literal["3.0"]
      work: WorkPlan
  ```
- **Tests**: `tests/core/plans/test_models_v3.py`
- **Depends on**: 없음

### Task 1.2: 로더 리팩터링
- **File**: `sisyphus/core/plans/loader.py`
- **Action**: 수정/재작성
- **Implementation**:
  ```python
  def load_plan(path: Path) -> PlanDocument:
      # YAML 로딩
      with path.open() as f:
          data = yaml.safe_load(f)

      # 버전 감지
      version = data.get("version")
      if version != "3.0":
          raise UnsupportedPlanVersionError(f"Version {version} not supported")

      # v3 모델 검증
      return PlanDocument.model_validate(data)
  ```
- **Tests**: `tests/core/plans/test_loader_v3.py`
- **Depends on**: Task 1.1

### Task 1.3: 예외/유틸 정의
- **File**: `sisyphus/core/plans/exceptions.py`
- **Action**: 생성
- **Implementation**:
  ```python
  class UnsupportedPlanVersionError(ValueError):
      """Raised when plan version is not supported."""

  class PlanValidationError(ValueError):
      """Raised when plan fails validation."""
  ```
- **Tests**: 기존 테스트에서 import 후 assert
- **Depends on**: 없음

### Task 1.4: status.json 관리 베이스
- **File**: `sisyphus/core/status/manager.py`
- **Action**: 생성
- **Implementation**:
  ```python
  class CurrentPlan(BaseModel):
      plan_path: str
      plan_root: str
      updated_at: datetime

  class StatusFile(BaseModel):
      version: Literal[1] = 1
      current_plan: CurrentPlan | None = None

  class StatusManager:
      STATUS_NAME = "status.json"

      @classmethod
      def get(cls, worktree: Path) -> CurrentPlan | None:
          status_path = cls._path(worktree)
          if not status_path.exists():
              return None
          data = json.loads(status_path.read_text())
          status = StatusFile.model_validate(data)
          return status.current_plan

      @classmethod
      def set_current(cls, worktree: Path, plan: Path) -> None:
          status_path = cls._path(worktree)
          status = StatusFile(current_plan=CurrentPlan(
              plan_path=str(plan),
              plan_root=str(plan.parent),
              updated_at=datetime.now(tz=timezone.utc),
          ))
          status_path.write_text(status.model_dump_json(indent=2))

      @classmethod
      def _path(cls, worktree: Path) -> Path:
          return worktree / ".sisyphus" / cls.STATUS_NAME
  ```
- **Tests**: `tests/core/status/test_manager.py`
- **Depends on**: Task 1.1 (경로 모델 import 불필요, 독립)

### Task 1.5: 기존 CLI 종속성 정리
- **File**: `sisyphus/cli.py`
- **Action**: 수정
- **Implementation**:
  - `load_plan` 호출 경로를 신 모듈로 위임
  - v2 관련 로직 만남 시 일단 `UnsupportedPlanVersionError` 재전파
- **Tests**: `tests/cli/test_cli_plan_load.py`
- **Depends on**: Task 1.2, Task 1.4

### Task 1.6: 테스트 리소스 구성
- **File**: `tests/fixtures/plans/v3_basic.yaml`, `tests/fixtures/plans/v2_legacy.yaml`
- **Action**: 생성
- **Implementation**:
  - v3: version 3.0, depends_on 예시, inline reference 포함
  - v2: version 2.1 (로딩 실패 용)
- **Tests**: 사용
- **Depends on**: 없음

---

## v3.0 스키마 변경사항

### WorkPlan 변경
```python
# 신규 필드
depends_on: list[str]  # 의존 플랜 경로 배열
```

### Todo 변경
```python
# 신규 필드
description: str | None  # 태스크 설명 (선택)
```

### ReferenceItem 변경
```python
# 기존: uri 필드만
uri: HttpUrl | FilePath | None

# v3.0: inline 필드 추가
uri: HttpUrl | FilePath | None = None
inline: str | None = None

# 검증: 둘 중 하나만 필수, 둘 다 있으면 오류
@model_validator(mode="after")
def validate_target(self) -> "ReferenceItem":
    if not (self.uri or self.inline):
        raise ValueError("Must define either uri or inline")
    if self.uri and self.inline:
        raise ValueError("Cannot define both uri and inline")
    return self
```

### 버전 필드
```python
version: Literal["3.0"]  # 엄격한 버전 체크
```

### 불변 필드
- `id`, `title`, `status` 등 기존 필드는 유지

---

## 의존성 그래프 알고리즘

### 그래프 구성
```python
def build_plan_graph(plans: dict[str, WorkPlan]) -> DiGraph[str, DependencyInfo]:
    graph = DiGraph()
    for plan_id, plan in plans.items():
        graph.add_node(plan_id)
        for dep in plan.depends_on:
            graph.add_edge(dep, plan_id, details=DependencyInfo(source=dep, target=plan_id))
    return graph
```

### 순환 검출 (DFS 기반)
```python
def detect_cycles(graph: DiGraph) -> list[list[str]]:
    temp_mark, perm_mark = set(), set()
    cycles = []

    def visit(node, stack):
        if node in perm_mark:
            return
        if node in temp_mark:
            # 순환 발견
            idx = stack.index(node)
            cycles.append(stack[idx:])
            return
        temp_mark.add(node)
        stack.append(node)
        for neighbor in graph.successors(node):
            visit(neighbor, stack)
        temp_mark.remove(node)
        perm_mark.add(node)
        stack.pop()

    for node in graph.nodes():
        if node not in perm_mark:
            visit(node, [])
    return cycles
```

### 토폴로지 정렬 (Kahn's Algorithm)
```python
def topo_sort(graph: DiGraph) -> list[str]:
    in_degree = {node: graph.in_degree(node) for node in graph.nodes()}
    queue = deque(node for node, deg in in_degree.items() if deg == 0)
    ordered = []

    while queue:
        node = queue.popleft()
        ordered.append(node)
        for neighbor in graph.successors(node):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(ordered) != len(graph.nodes()):
        raise CycleDetectedError()
    return ordered
```

### YAML 로딩 프로세스
1. `plan_paths = discover_plan_files(root)` (Phase 2 작업)
2. 각 파일 `PlanDocument` 인스턴스 생성
3. `plans[plan.work.name] = plan.work`
4. 의존 대상이 없는 ID는 `dangling` 검출 리스트에 추가

---

## status.json 구조

### JSON 스키마
```json
{
  "version": 1,
  "current_plan": {
    "plan_path": "plans/main.yaml",
    "plan_root": "plans/",
    "updated_at": "2025-02-10T03:21:45.123456Z"
  }
}
```

### Python 모델
```python
class CurrentPlan(BaseModel):
    plan_path: str
    plan_root: str
    updated_at: datetime

class StatusFile(BaseModel):
    version: Literal[1] = 1
    current_plan: CurrentPlan | None = None
```

---

## CLI Typer 구조

```python
plan_app = typer.Typer(help="Work plan management commands.")
task_app = typer.Typer(help="Task execution helpers.")

@plan_app.command("init")
def init_plan(
    destination: Path = typer.Option(..., dir_okay=True, file_okay=False),
    template: str | None = typer.Option(None),
    cwd: Path = typer.Option(Path("."), "--cwd"),
) -> None:
    ...

@plan_app.command("lint")
def lint_plan(
    path: Path = typer.Argument(...),
    format: Literal["yaml", "json"] = typer.Option("yaml"),
    cwd: Path = typer.Option(Path("."), "--cwd"),
) -> None:
    ...

@task_app.command("verify")
def verify_task(
    mode: Literal["bash", "llm", "manual"],
    plan: Path = typer.Option(None, "--plan"),
    cwd: Path = typer.Option(Path("."), "--cwd"),
    strict: bool = typer.Option(False),
) -> None:
    ...
```

---

## 테스트 전략

### 디렉토리 구조
```
tests/
  core/
    plans/
      test_models_v3.py
      test_loader_v3.py
    status/
      test_manager.py
  cli/
    test_cli_plan_load.py
  fixtures/
    plans/
      v3_basic.yaml
      v2_legacy.yaml
```

### 테스트 케이스

#### test_models_v3.py
- `test_reference_inline_requires_value()`: inline이나 uri 중 하나 필수
- `test_workplan_depends_on_default_empty()`: depends_on 기본값 빈 리스트

#### test_loader_v3.py
- `test_load_v3_yaml()`: v3 파일 정상 로딩
- `test_load_v2_yaml_raises()`: v2 파일은 UnsupportedPlanVersionError
- `test_auto_version_detection()`: version 누락 시 PlanValidationError

#### test_manager.py
- `test_get_returns_none_when_missing()`: status.json 없으면 None 반환
- `test_set_current_creates_file(tmp_path)`: set_current가 파일 생성

### Fixtures
```python
# tests/conftest.py
@pytest.fixture
def temp_worktree(tmp_path):
    """./temp/ 시뮬레이션"""
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    return worktree
```

### 엣지 케이스
- depends_on이 자기 자신 참조
- ReferenceItem에서 uri/inline 동시 제공
- status.json 파싱 실패 (손상 파일) → Phase 5에서 확장 예정

---

## 리스크 완화

### 그래프-로더 순환
- **문제**: Phase 1에서 그래프 미도입
- **해결**: loader → models 단방향 유지

### 파괴적 변경
- **문제**: 기존 CLI 로직 손상
- **해결**: v3 경로만 우선 조정, 기존 로직 유지

### 테스트 깨짐
- **문제**: v2 관련 테스트 실패
- **해결**: 임시로 스킵 또는 v2 로더 분리, Phase 4에서 변환기로 해소

### 경로 처리 실수
- **문제**: --cwd 반영은 Phase 3
- **해결**: Phase 1 테스트에서 `temp_worktree` 활용해 대비

### 버전 탐지 오동작
- **해결**: 명확한 예외 메시지와 테스트로 방지

### status.json 동시성
- **문제**: Phase 1은 간단 구현
- **해결**: Phase 5에서 파일락/원자쓰기 추가 예정

---

## Phase 1 완료 기준

- [ ] `sisyphus/core/plans/models.py` 생성 및 v3 모델 정의
- [ ] `sisyphus/core/plans/loader.py`가 v3 로더 수행, v2 거부
- [ ] `sisyphus/core/status/manager.py` 기본 클래스 동작
- [ ] `sisyphus/core/plans/exceptions.py` 정의
- [ ] 테스트 픽스처와 샘플 YAML 추가
- [ ] Phase 1 전용 테스트 모두 통과 (`pytest tests/core/plans tests/core/status`)
- [ ] ruff/basedpyright에서 Phase 1 변경 무경고 (새 에러 없음)
- [ ] CLI가 v3 로더로 계획 파일을 읽고 오류 시 명확한 메시지 출력
