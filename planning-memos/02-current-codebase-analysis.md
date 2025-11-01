# 기존 코드베이스 분석

**작성일**: 2025-11-01

---

## 현재 디렉토리 구조

```
sisyphus/
├── cli.py (995줄 - 매우 큼)
├── agents/
│   ├── base.py (Agent Protocol)
│   ├── claude.py (ClaudeAgent)
│   └── opencode.py (OpenCodeAgent)
├── core/
│   ├── loop.py (ExecutionLoop)
│   ├── plan_loader.py (PlanLoader - 단일 YAML 로딩)
│   ├── plan_linter.py (PlanLinter - v2.1 검증)
│   ├── plan_navigator.py (PlanNavigator - DFS 기반 태스크 탐색)
│   ├── prompts.py (PromptResolver)
│   ├── session.py (SessionStore)
│   └── tasks.py (TaskValidator - ai-todolist.md 체크)
├── ui/
│   ├── base.py (UIProtocol, create_ui)
│   ├── tui/ (Textual TUI)
│   └── cli/ (Rich CLI)
└── utils/
    ├── plan_types.py (WorkPlan, Todo, ReferenceItem, VerificationItem 등 v2.1 모델)
    ├── formatting.py (출력 포맷팅)
    ├── types.py (AgentMessage, MessageRole)
    ├── logging.py (LoggerFactory)
    ├── process.py (ProcessManager)
    ├── session_limit.py (Retry error handling)
    ├── theme.py (TUI theme)
    ├── git.py (Git 유틸)
    └── errors.py (예외)
```

---

## 현재 CLI 구조 (cli.py:587-994)

### Typer 앱 분리 상황
```python
plan_app = typer.Typer(name="plan", help="Work plan management")
execute_phase_app = typer.Typer(name="execute-phase", help="Execute phase commands")
verify_phase_app = typer.Typer(name="verify-phase", help="Verify phase commands")
```

### plan_app 명령어
- `plan get task --id X` / `--current` / `--next`
  - 구현: `get_plan_info()` (cli.py:883-951)
  - 로직: PlanLoader + PlanNavigator 사용
- `plan lint`
  - 구현: `lint_plan()` (cli.py:953-991)
  - 로직: YAML 파싱 → PlanLinter 검증

### execute_phase_app 명령어
- `execute-phase get-overview`
  - 구현: `get_overview()` (cli.py:597-608)
  - 로직: PlanLoader → print_overview
- `execute-phase continue-work`
  - 구현: `continue_work()` (cli.py:610-687)
  - 로직: PlanNavigator.get_next_task() → 상태 업데이트 → YAML 저장
- `execute-phase bash-verify <task_id>`
  - 구현: `bash_verify()` (cli.py:689-769)
  - 로직: subprocess 실행 → 성공 시 verification_spec 업데이트
- `execute-phase llm-verify <task_id> --verify-id --evidence`
  - 구현: `llm_verify()` (cli.py:771-819)
  - 로직: verification_spec 업데이트 (수동 마킹)
- `execute-phase manual-verify <task_id> --evidence`
  - 구현: `manual_verify()` (cli.py:821-865)
  - 로직: orchestrator_manually_verified 업데이트

### verify_phase_app 명령어 (중복)
- `verify-phase bash-verify` → execute_phase_app.bash_verify 호출
- `verify-phase llm-verify` → execute_phase_app.llm_verify 호출

---

## 현재 YAML 스키마 (v2.1)

### WorkPlan (plan_types.py:248-261)
```python
class WorkPlan(BaseModel):
    model_config = ConfigDict(extra="allow")

    metadata: Metadata
    user_request: UserRequest
    objectives: Objectives
    background: Background
    required_background: RequiredBackground
    status: Status
    workflow: Workflow
    todos: list[Todo]
    success_vision: SuccessVision
    final_verification: list[FinalVerificationItem]
```

### Todo (plan_types.py:118-136)
```python
class Todo(BaseModel):
    id: str | int
    title: str
    status: TodoStatus
    parallel_group: int | None = None
    created_at: str
    updated_at: str
    status_changed_at: str | None = None
    references: list[ReferenceItem] = []
    details: dict[str, Any] = {}
    verification_spec: list[VerificationItem] = []
    children: list[Todo] = []
    parallel_note: str | None = None
```

### ReferenceItem (plan_types.py:111-114)
```python
ReferenceItem = Annotated[
    ReferencePointer | FileReference | URLReference | MarkdownReference,
    Field(discriminator="type"),
]
```
- ReferencePointer: type="pointer", ref_id, notes
- FileReference: type="file", path, description, retrieval, notes, id
- URLReference: type="url", url, description, retrieval, notes, id
- MarkdownReference: type="markdown", description, content, id

### VerificationItem (plan_types.py:60-76)
```python
class VerificationItem(BaseModel):
    id: str
    title: str
    description: str
    verified: bool = False
    verified_at: str | None = None
    verification_evidence: str | None = None
    orchestrator_manually_verified: bool
    manual_verification_evidence: str
    bash: list[BashVerification] = []
    llm_judge: list[LLMJudgeVerification] = []
```

---

## PlanLoader (plan_loader.py)

### 현재 구현
```python
class PlanLoader:
    def __init__(self, plan_path: Path = Path("./ai-todolist.yaml")):
        self.plan_path = plan_path
        self.yaml = YAML()

    def load(self) -> WorkPlan:
        # YAML 파싱 → Pydantic 검증
        with self.plan_path.open("r") as f:
            data = self.yaml.load(f)
        return WorkPlan(**data)

    def save(self, plan: WorkPlan) -> None:
        # model_dump → YAML 저장
        data = plan.model_dump(mode="json")
        with self.plan_path.open("w") as f:
            self.yaml.dump(data, f)
```

### 문제점
- 단일 YAML 파일만 지원
- 버전 판별 없음 (v2.1 고정)
- depends_on 처리 없음
- 여러 플랜 로딩 불가

---

## PlanLinter (plan_linter.py)

### 현재 구현
- v2.1 스키마 기반 검증
- 필수 필드, 타입, enum 값 검증
- references 무결성 검증 (ref_id 존재 여부)
- discriminated union 검증

### 문제점
- depends_on 검증 없음
- 순환 의존성 검증 없음
- 고립 의존성 검증 없음
- v3.0 스키마 미지원

---

## PlanNavigator (plan_navigator.py)

### 현재 구현
- DFS 기반 태스크 탐색
- get_current_task(), get_next_task()
- find_todo_by_id() (재귀적)
- get_parallel_group_tasks()
- check_task_completion()

### 특징
- 단일 플랜 내에서만 동작
- parallel_group 지원
- children 재귀 탐색

### 문제점
- 여러 플랜 간 의존성 미지원
- verification 순차 처리 없음 (next_unverified 메서드 없음)

---

## TaskValidator (tasks.py)

### 현재 구현
```python
class TaskValidator:
    def __init__(self, todolist_path: Path = Path("./ai-todolist.md")):
        self.todolist_path = todolist_path

    def check_all_goals_accomplished(self) -> bool:
        # is_all_goals_accomplished = TRUE 패턴 검색

    def check_all_checkboxes_completed(self) -> bool:
        # [ ] vs [x] 패턴 검색
```

### 문제점
- .md 파일만 지원 (YAML 미지원)
- .sisyphus/tasks/ 디렉토리 구조 미지원

---

## 현재 파일 위치

### 루트 레벨
- ai-todolist.yaml (또는 .md)
- notepad.md
- sessions/
- logs/

### v3.0에서 변경
- .sisyphus/tasks/ (플랜 YAML들)
- .sisyphus/status.json (워크트리별 현재 플랜)
- .sisyphus/notepad.md
- .sisyphus/sessions/
- .sisyphus/logs/
- .sisyphus/resources/ (테스트용)

---

## 주요 변경 필요 사항

### 1. 모듈 재구성
- cli.py → cli/__init__.py, cli/plan.py, cli/task.py, cli/reset.py
- core/plans/ 패키지 생성
- core/status/ 패키지 생성
- core/graph/ 패키지 생성
- core/converters/ 패키지 생성

### 2. 새로운 모듈 필요
- core/plans/dependencies.py (의존성 그래프)
- core/plans/parser_v3.py (v3.0 파서)
- core/plans/references.py (레퍼런스 관리)
- core/status/manager.py (status.json 관리)
- core/graph/renderer.py (ASCII/Mermaid/PNG)
- core/converters/legacy.py (v2.1→v3.0)

### 3. 기존 모듈 확장
- plan_loader.py → 버전 판별 + 멀티 플랜 로딩
- plan_linter.py → depends_on 검증 추가
- plan_navigator.py → 멀티 플랜 지원
- tasks.py → YAML 지원

### 4. plan_types.py 확장
- WorkPlan에 depends_on 필드 추가
- Todo에 description 필드 추가
- ReferenceItem에 inline 타입 추가
- LLMJudgeVerification에 by 필드 명시적 추가
