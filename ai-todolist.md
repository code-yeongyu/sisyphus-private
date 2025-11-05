# 사용자의 최초 요청 (기록용)
아직은 마크다운 형식으로 작업해야합니다. 이를 명심하세요.

현재 아직 sisyphus cli 에서 yaml 2.1 기반의 코드가 많습니다. 무조건 3.0 기반으로만 동작하도록, .sisyphus 안의 태스크파일을 참조하도록 코드를 재작성해야합니다.

코드 전방위적으로 살펴보고, 고치는 플랜을 생각하세요. 2.1은 사용자가 없으므로 폴백이나마이그레이션은 전부 생각하지 않아도 되고, 3.0 만을 지원하도록 2.1의 흔적과 마크다운의 흔적(혹시남아있다면) 을 모두 없애야합니다. 이 모든것들을 살펴보시고 쭉 나열하세요.

## 추가 사용자 요청 (기록용)
없음

# 작업 목표 (WHAT & WHY)

## 핵심 목표 (TL;DR)
Sisyphus CLI에서 v2.1 기반 코드를 완전히 제거하되, **기존 v2.1 기능은 유지**한다. `.sisyphus/tasks/` 경로만 지원하도록 단순화하되, `task` 명령어 등 핵심 워크플로우는 정상 동작하도록 보장한다.

## 상세 목표
- v2.1 모델(`plan_types.py`)을 제거하되, v3.0에 없는 기능(상태 관리)은 `status.json`으로 이관
- 하드코딩된 `ai-todolist.yaml` → status.json 기반 동적 로드로 전환
- 마크다운 관련 코드 완전 제거
- v2.1 폴백 에러 메시지 제거
- 테스트 및 문서 업데이트

# 작업 배경 (WHY & WHAT - 현재 상태)

## 현재 상황
- **v2.1 아키텍처**: `WorkPlan` 모델이 `status.work_mode.current_task_id` 등 상태 필드 포함
- **v3.0 아키텍처**: `PlanDocument`는 순수 데이터 구조, 상태 없음
- **혼재 상태**:
  - `cli/task.py`: v2.1 `WorkPlan` 전제, `ai-todolist.yaml` 하드코딩
  - `core/plans/loader.py`: v3.0 `PlanDocument` 로드, 하지만 CLI와 연결 안됨
  - `core/plan_navigator.py`: v2.1 모델 전용

## 변경 이유
- v3.0으로 완전 전환하여 이중 모델 관리 부담 제거
- 상태 관리를 파일(`status.json`)로 분리하여 YAML 파일 단순화
- 일관된 `.sisyphus/` 구조로 사용자 경험 개선

## 변경할 내용
- 현재: v2.1 `WorkPlan` (상태 포함) + v3.0 `PlanDocument` (상태 없음) 공존
- 변경 후: v3.0 `PlanDocument` 전용 + `status.json` (상태 별도 관리)

# 작업 시작 여부
is_execution_started = FALSE

# 전체 목표 달성 여부
is_all_goals_accomplished = FALSE

# 병렬 실행
parallel_requested = FALSE

# 현재 진행 중인 작업
- 작업이 아직 시작되지 않았습니다.
  - 작업 시작 시 위의 `is_execution_started` 값을 TRUE로 변경하세요.
  - **사용자가 명시적으로 "작업 시작해"라고 말하기 전까지는 절대 작업을 시작하지 마세요.**
  - **plan reviewer로부터 OKAY를 받았더라도, 절대 작업을 시작하지 마세요**
  - **사용자가 명시적으로 "작업 시작해"라고 말하기 전까지는 절대 작업을 시작하지 마세요.**

# 필요 배경 지식

## 아키텍처 이해

### v2.1 아키텍처 (제거 대상)
```
WorkPlan (utils/plan_types.py):
- status.work_mode.current_task_id  ← 상태 포함
- status.execution.started
- todos[].status

파일: ai-todolist.yaml (루트)
```

### v3.0 아키텍처 (목표)
```
PlanDocument (core/plans/models.py):
- version: "3.0"
- work_plans[].todos[].status  ← 데이터만

status.json (.sisyphus/status.json):
- current_plan.plan_path
- current_plan.plan_id  ← 추가 필요
- current_task_id  ← 추가 필요

파일: .sisyphus/tasks/*.yaml
```

**핵심 차이**: v3.0은 상태를 YAML에 저장하지 않고, `status.json`에 별도 관리

## 전환 전략 결정

**선택: 옵션 B - status.json 확장 + v3.0 전용 Navigator 생성**

**이유**:
- v2.1 `PlanNavigator` 재작성 불필요 (사용 중단)
- v3.0 전용 간단한 Navigator 새로 생성
- 상태 관리 로직을 `status.json`으로 이관
- 기존 테스트 최소 영향

**구현 방향**:
1. `status.json`에 `current_task_id`, `plan_id` 추가
2. v3.0 전용 `TaskManager` 생성 (`PlanNavigator` 대체)
3. `cli/task.py`를 v3.0 + `TaskManager`로 재작성
4. v2.1 모델 및 Navigator 제거

## 파일 구조 및 역할

### 제거 대상 파일
- `sisyphus/utils/plan_types.py`: v2.1 Pydantic 모델
- `sisyphus/core/plan_navigator.py`: v2.1 전용 Navigator
- `sisyphus/core/plan_loader.py`: v2.1 전용 Loader
- `sisyphus/core/tasks.py`: 마크다운 검증 로직

### 수정 대상 파일
- `sisyphus/core/status/manager.py`: `StatusFile` 모델 확장
- `sisyphus/cli/task.py`: v3.0 기반 재작성
- `sisyphus/cli/plan.py`: 경로 수정, 템플릿 업데이트
- `sisyphus/cli/work.py`: 마크다운 체크 제거
- `sisyphus/core/prompts.py`: 텍스트 수정
- `sisyphus/core/plans/loader.py`: v2.1 폴백 제거

### 생성 대상 파일
- `sisyphus/core/task_manager.py`: v3.0 전용 태스크 관리자

## 참조 파일 리스트

### 1. `sisyphus/core/plans/models.py`
- **역할**: v3.0 Pydantic 모델 (PlanDocument, WorkPlan, Todo)
- **검색 키워드**: `class PlanDocument`, `class Todo`, `status: TodoStatus`
- **패턴**: 순수 데이터 모델 (상태 로직 없음)
- **코드 예시**:
  ```python
  class Todo(BaseModel):
      id: str
      title: str
      status: TodoStatus  # pending/in_progress/completed
      children: list[Todo] | None = None
  ```

### 2. `sisyphus/core/status/manager.py`
- **역할**: `.sisyphus/status.json` 관리
- **검색 키워드**: `class StatusManager`, `set_current()`, `get()`
- **현재 스키마**:
  ```python
  class CurrentPlan(BaseModel):
      plan_path: str  # .sisyphus/tasks/feature.yaml
      plan_root: str  # /Users/user/project
      updated_at: str
  ```
- **확장 필요**: `plan_id: str`, `current_task_id: str | None` 추가

### 3. `sisyphus/core/plans/loader.py`
- **역할**: v3.0 YAML 파일 로드
- **검색 키워드**: `load_plan()`, `version == "3.0"`, line 38-43
- **패턴**:
  ```python
  async def load_plan(path: Path) -> PlanDocument:
      # line 38-43: v2.1 폴백 에러 (제거 대상)
      if version == "3.0":
          return PlanDocument(**data)
  ```

### 4. `sisyphus/cli/task.py`
- **역할**: task 명령어 (current, next, continue 등)
- **검색 키워드**: `ai-todolist.yaml` (11회 출현), `PlanNavigator`
- **현재 패턴**: 하드코딩된 경로 + v2.1 모델
- **변경 방향**: `status.json` 기반 + v3.0 모델

### 5. `.sisyphus/tasks/hello-world.yaml`
- **역할**: v3.0 형식 예시
- **구조**:
  ```yaml
  version: "3.0"
  work_plans:
    - id: "hello-world"
      todos:
        - id: "1"
          status: pending
  ```

# 작업 흐름 (HOW - 태스크 흐름 & 의존성)

## 태스크 의존성 다이어그램
```
Task 1 (status.json 확장)
   ↓
Task 2 (TaskManager 생성)
   ↓
Task 3 (cli/task.py 재작성)
   ↓
Task 4 (cli/plan.py 수정)
   ↓
Task 5 (기타 CLI 수정)
   ↓
Task 6 (프롬프트 수정)
   ↓
Task 7 (v2.1 폴백 제거)
   ↓
Task 8 (v2.1 파일 제거)
   ↓
Task 9 (테스트 수정)
   ↓
Task 10 (문서 정리)
   ↓
Task 11 (최종 검증)
```

## 단계별 설명
- **Phase 1 (Task 1-2)**: 인프라 구축 - status.json 확장 + TaskManager 생성
- **Phase 2 (Task 3-5)**: CLI 전환 - v3.0 기반 재작성
- **Phase 3 (Task 6-8)**: 레거시 제거 - 프롬프트, 폴백, v2.1 파일
- **Phase 4 (Task 9-11)**: 테스트 & 문서 - 최종 검증

# 작업 계획

## PRD & 구조

**최종 아키텍처**:
```mermaid
graph TB
    CLI[CLI Commands] --> STATUS[StatusManager]
    CLI --> TM[TaskManager v3.0]
    TM --> LOADER[PlanLoader v3.0]
    LOADER --> YAML[.sisyphus/tasks/*.yaml]
    STATUS --> JSON[.sisyphus/status.json]

    JSON -.current_plan.plan_id.-> YAML
    JSON -.current_task_id.-> TM
```

**상태 관리 분리**:
- YAML: 순수 데이터 (todos, references)
- status.json: 현재 플랜, 현재 작업 ID

## 프로젝트 커밋 메시지 스타일
```
refactor: simplify X
feat: add Y
fix: resolve Z
docs: update A
test: add test for B
```

# TODOs

- [ ] 1. status.json 스키마 확장

   **참조 소스**:
   - 수정 대상: `projects/sisyphus-cli/sisyphus/core/status/manager.py` (line 14-17)
   - 패턴 참조: 기존 `CurrentPlan` 클래스

   - [ ] 1.1 `CurrentPlan` 모델 확장

      **구현 세부사항**:
      - 현재:
        ```python
        class CurrentPlan(BaseModel):
            plan_path: str
            plan_root: str
            updated_at: str
        ```
      - 변경:
        ```python
        class CurrentPlan(BaseModel):
            plan_path: str  # .sisyphus/tasks/feature.yaml
            plan_root: str  # /Users/user/project
            plan_id: str  # work_plans[].id
            current_task_id: str | None = None  # 현재 작업 ID
            updated_at: str
        ```
      - 이유: v3.0 다중 work_plans 지원, 현재 작업 추적

   - [ ] 1.2 `StatusManager.set_current()` 시그니처 변경

      **구현 세부사항**:
      - 현재: `set_current(plan_path: str, plan_root: str)`
      - 변경: `set_current(plan_path: str, plan_root: str, plan_id: str, current_task_id: str | None = None)`
      - 호출부: `cli/plan.py`, `cli/task.py` 등에서 호출 - 함께 수정 필요

   - [ ] 1.3 테스트 작성

      **검증 명령어**:
      ```bash
      # 테스트 파일 생성: projects/sisyphus-cli/tests/core/status/test_manager_extended.py
      # 검증 항목:
      # - plan_id 저장/로드
      # - current_task_id 저장/로드
      # - 기존 기능 회귀 테스트
      ```

   - [ ] 1.4 테스트 및 린트
      - [ ] `uv run pytest projects/sisyphus-cli/tests/core/status/ -xvs` → 통과
      - [ ] `uv run ruff check sisyphus/core/status/manager.py` → 0 errors

   - [ ] 1.5 커밋
      - `git add sisyphus/core/status/manager.py tests/core/status/`
      - `git commit -m "refactor: extend status.json schema for v3.0 support"`

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] `CurrentPlan`에 `plan_id`, `current_task_id` 필드 추가?
      - [ ] `set_current()` 시그니처 업데이트?
      - [ ] 테스트 작성 및 통과?
      - [ ] 린트 0 errors?
      - [ ] 커밋 완료?

- [ ] 2. TaskManager v3.0 생성

   **참조 소스**:
   - 패턴 참조: `sisyphus/core/plan_navigator.py` (기존 v2.1 Navigator - 로직 참고용)
   - 모델 참조: `sisyphus/core/plans/models.py` (v3.0 `PlanDocument`, `Todo`)
   - 생성 위치: `projects/sisyphus-cli/sisyphus/core/task_manager.py`

   - [ ] 2.1 `TaskManager` 클래스 생성

      **구현 세부사항**:
      - 입력: `PlanDocument`, `plan_id`, `current_task_id`
      - 메서드:
        - `get_current_work_plan() -> WorkPlan`: plan_id로 work_plan 찾기
        - `find_todo_by_id(todo_id: str) -> Todo | None`: DFS 탐색
        - `get_next_pending_todo() -> Todo | None`: 첫 번째 pending todo
        - `update_todo_status(todo_id: str, new_status: TodoStatus) -> None`: 상태 업데이트
      - 특징: 순수 함수형, 파일 I/O 없음 (Loader와 분리)

      **코드 패턴**:
      ```python
      class TaskManager:
          def __init__(self, plan_doc: PlanDocument, plan_id: str) -> None:
              self.plan_doc = plan_doc
              self.plan_id = plan_id
              self.work_plan = self._find_work_plan()

          def _find_work_plan(self) -> WorkPlan:
              for wp in self.plan_doc.work_plans:
                  if wp.id == self.plan_id:
                      return wp
              raise ValueError(f"WorkPlan not found: {self.plan_id}")

          def find_todo_by_id(self, todo_id: str) -> Todo | None:
              # DFS 구현
              ...
      ```

   - [ ] 2.2 테스트 작성

      **테스트 파일**: `projects/sisyphus-cli/tests/core/test_task_manager.py`
      **테스트 항목**:
      - [ ] WorkPlan 찾기 (존재/부재)
      - [ ] Todo DFS 탐색
      - [ ] 다음 pending todo 찾기
      - [ ] Children 재귀 탐색

   - [ ] 2.3 테스트 실행
      - [ ] `uv run pytest projects/sisyphus-cli/tests/core/test_task_manager.py -xvs` → 통과
      - [ ] `uv run ruff check sisyphus/core/task_manager.py` → 0 errors
      - [ ] `uv run basedpyright sisyphus/core/task_manager.py` → 0 errors

   - [ ] 2.4 커밋
      - `git add sisyphus/core/task_manager.py tests/core/test_task_manager.py`
      - `git commit -m "feat: add TaskManager for v3.0 PlanDocument"`

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] `TaskManager` 클래스 생성?
      - [ ] 필수 메서드 구현 (find_todo, get_next_pending)?
      - [ ] 테스트 작성 및 통과?
      - [ ] 타입 체크 통과?
      - [ ] 커밋 완료?

- [ ] 3. cli/task.py 재작성 (v3.0 전용)

   **참조 소스**:
   - 수정 대상: `projects/sisyphus-cli/sisyphus/cli/task.py` (전체 509줄)
   - 패턴 참조: `sisyphus/core/plans/loader.py:96-119` (status.json 기반 로드)
   - 사용 모델: `TaskManager` (Task 2), `load_plan()`, `StatusManager`

   - [ ] 3.1 `task current` 명령 재작성

      **구현 세부사항**:
      - 현재: `ai-todolist.yaml` 하드코딩, `PlanNavigator` 사용
      - 변경:
        1. `StatusManager.get()` → `current_plan` 로드
        2. `load_plan(current_plan.plan_path)` → `PlanDocument`
        3. `TaskManager(plan_doc, current_plan.plan_id)`
        4. `manager.find_todo_by_id(current_plan.current_task_id)` → Todo
        5. 출력

   - [ ] 3.2 `task next` 명령 재작성

      **구현 세부사항**:
      - 로직: `TaskManager.get_next_pending_todo()` 사용
      - 상태 업데이트: status.json에 `current_task_id` 저장

   - [ ] 3.3 `task continue` 명령 재작성

      **구현 세부사항**:
      - 로직: 현재 작업 → completed, 다음 작업 → in_progress
      - YAML 파일 저장: `ruamel.yaml`로 status 필드 업데이트
      - status.json 저장: `current_task_id` 업데이트

   - [ ] 3.4 기타 명령 재작성
      - [ ] `task show <id>`
      - [ ] `task previous`
      - [ ] `verify` 서브명령들

   - [ ] 3.5 테스트 작성 및 실행
      - [ ] `uv run pytest projects/sisyphus-cli/tests/cli/test_task.py -xvs` → 통과
      - [ ] `uv run ruff check sisyphus/cli/task.py` → 0 errors

   - [ ] 3.6 커밋
      - `git add sisyphus/cli/task.py tests/cli/test_task.py`
      - `git commit -m "refactor: rewrite task commands for v3.0"`

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] `ai-todolist.yaml` 하드코딩 제거 (11회 → 0회)?
      - [ ] `status.json` 기반 동적 로드로 전환?
      - [ ] `TaskManager` 사용?
      - [ ] 테스트 통과?
      - [ ] 커밋 완료?
      - [ ] 수동 테스트:
        ```bash
        # .sisyphus/tasks/test.yaml 생성
        uv run sisyphus task current --cwd .
        uv run sisyphus task next --cwd .
        ```

- [ ] 4. cli/plan.py 수정

   **참조 소스**:
   - 수정 대상: `projects/sisyphus-cli/sisyphus/cli/plan.py` (line 127: format_version, line 44/91/106: 경로)
   - 패턴 참조: `sisyphus/core/plans/loader.py` (`.sisyphus/tasks/` 탐색)

   - [ ] 4.1 `plan init` 템플릿 수정

      **구현 세부사항**:
      - 현재: line 127 `format_version: "2.1"`
      - 변경: `version: "3.0"` (v3.0은 최상위 version 필드 사용)
      - 템플릿 구조:
        ```python
        template = {
            "version": "3.0",
            "metadata": {...},
            "work_plans": [{
                "id": "new-plan",
                "name": "New Plan",
                "depends_on": [],
                "todos": [],
                "references": []
            }]
        }
        ```

   - [ ] 4.2 경로 기본값 변경

      **구현 세부사항**:
      - 현재: `Path("./ai-todolist.yaml")` 기본값 (line 44, 106)
      - 변경: `.sisyphus/tasks/` 경로 사용 또는 status.json 기반

   - [ ] 4.3 `plan overview` 명령 수정

      **구현 세부사항**:
      - 현재: `PlanLoader` (v2.1) 사용
      - 변경: `load_plan()` (v3.0) 사용, status.json 기반

   - [ ] 4.4 테스트 및 린트
      - [ ] `uv run pytest projects/sisyphus-cli/tests/cli/test_plan.py -xvs` → 통과
      - [ ] `uv run ruff check sisyphus/cli/plan.py` → 0 errors

   - [ ] 4.5 커밋
      - `git add sisyphus/cli/plan.py`
      - `git commit -m "refactor: update plan commands for v3.0"`

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] `init` 템플릿이 v3.0 형식?
      - [ ] `ai-todolist.yaml` 하드코딩 제거?
      - [ ] 테스트 통과?
      - [ ] 커밋 완료?

- [ ] 5. 기타 CLI 수정 (work.py)

   **참조 소스**:
   - 수정 대상: `projects/sisyphus-cli/sisyphus/cli/work.py` (line 122-138)

   - [ ] 5.1 `work.py` 마크다운 체크 제거

      **구현 세부사항**:
      - 현재: `ai-todolist.md` 존재 시 에러 (line 122-138)
      - 변경: 해당 블록 완전 삭제
      - 이유: v3.0에서 마크다운 지원 안함

   - [ ] 5.2 테스트 및 린트
      - [ ] `uv run ruff check sisyphus/cli/work.py` → 0 errors

   - [ ] 5.3 커밋
      - `git add sisyphus/cli/work.py`
      - `git commit -m "refactor: remove markdown check from work command"`

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] `ai-todolist.md` 체크 로직 제거?
      - [ ] 린트 통과?
      - [ ] 커밋 완료?

- [ ] 6. 프롬프트 텍스트 수정

   **참조 소스**:
   - 수정 대상: `projects/sisyphus-cli/sisyphus/core/prompts.py` (line 156, 170, 666)

   - [ ] 6.1 `prompts.py` 텍스트 수정

      **구현 세부사항**:
      - 검색: `ai-todolist.md` (전체 파일)
      - 변경:
        - `"Read and understand the entire ai-todolist.md content"` → `"Read and understand the work plan"`
        - `"Check that ALL completion criteria in ai-todolist.md are met"` → `"Check that ALL completion criteria in the work plan are met"`
        - `"all goals in ai-todolist.md"` → `"all goals in the work plan"`

   - [ ] 6.2 테스트 및 린트
      - [ ] `uv run ruff check sisyphus/core/prompts.py` → 0 errors

   - [ ] 6.3 커밋
      - `git add sisyphus/core/prompts.py`
      - `git commit -m "refactor: update prompts to remove markdown references"`

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] `ai-todolist.md` 텍스트 모두 제거?
      - [ ] "work plan" 등으로 대체?
      - [ ] 린트 통과?
      - [ ] 커밋 완료?

- [ ] 7. v2.1 폴백 제거

   **참조 소스**:
   - 수정 대상: `projects/sisyphus-cli/sisyphus/core/plans/loader.py` (line 38-43)
   - 테스트 영향: `projects/sisyphus-cli/tests/core/plans/test_loader_v3.py`

   - [ ] 7.1 `plans/loader.py` 수정

      **구현 세부사항**:
      - 현재:
        ```python
        if version == "3.0":
            return PlanDocument(**data)
        elif version in ("2.1", "2.0"):
            raise UnsupportedPlanVersionError("...convert-legacy...")
        else:
            raise ValueError(f"Unknown plan version: {version}")
        ```
      - 변경:
        ```python
        if version == "3.0":
            return PlanDocument(**data)
        else:
            raise ValueError(f"Unsupported plan version: {version}. Only v3.0 is supported.")
        ```

   - [ ] 7.2 테스트 수정

      **구현 세부사항**:
      - 파일: `projects/sisyphus-cli/tests/core/plans/test_loader_v3.py`
      - 검색: `convert-legacy` 문자열
      - 변경: assertion 업데이트 (에러 메시지 변경 반영)

   - [ ] 7.3 테스트 실행
      - [ ] `uv run pytest projects/sisyphus-cli/tests/core/plans/ -xvs` → 통과

   - [ ] 7.4 커밋
      - `git add sisyphus/core/plans/loader.py tests/core/plans/test_loader_v3.py`
      - `git commit -m "refactor: remove v2.1 fallback logic from loader"`

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] v2.1/2.0 특별 처리 제거?
      - [ ] 에러 메시지 단순화?
      - [ ] 테스트 수정 및 통과?
      - [ ] 커밋 완료?

- [ ] 8. v2.1 파일 제거

   **참조 소스**:
   - 제거 대상:
     - `projects/sisyphus-cli/sisyphus/utils/plan_types.py` (v2.1 모델)
     - `projects/sisyphus-cli/sisyphus/core/plan_navigator.py` (v2.1 Navigator)
     - `projects/sisyphus-cli/sisyphus/core/plan_loader.py` (v2.1 Loader)
     - `projects/sisyphus-cli/sisyphus/core/tasks.py` (마크다운 검증)

   - [ ] 8.1 파일 삭제

      **구현 세부사항**:
      ```bash
      git rm sisyphus/utils/plan_types.py
      git rm sisyphus/core/plan_navigator.py
      git rm sisyphus/core/plan_loader.py
      git rm sisyphus/core/tasks.py
      ```

   - [ ] 8.2 Import 정리

      **검증 명령어**:
      ```bash
      # 삭제된 파일을 import하는 곳 찾기
      grep -r "from sisyphus.utils.plan_types import" projects/sisyphus-cli/sisyphus/
      grep -r "from sisyphus.core.plan_navigator import" projects/sisyphus-cli/sisyphus/
      # 발견된 파일 수정
      ```

   - [ ] 8.3 테스트 파일 정리

      **구현 세부사항**:
      - 삭제: `projects/sisyphus-cli/tests/core/test_plan_navigator.py` (존재 시)
      - 삭제: `projects/sisyphus-cli/tests/core/test_plan_loader.py` (존재 시)
      - 삭제: `projects/sisyphus-cli/tests/core/test_tasks.py`

   - [ ] 8.4 전체 테스트 실행
      - [ ] `uv run pytest projects/sisyphus-cli/ -x` → 통과 (import 에러 없어야 함)

   - [ ] 8.5 커밋
      - `git add -A`
      - `git commit -m "refactor: remove v2.1 legacy files"`

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] v2.1 파일 4개 삭제?
      - [ ] Import 에러 해결?
      - [ ] 관련 테스트 삭제?
      - [ ] 전체 테스트 통과?
      - [ ] 커밋 완료?

- [ ] 9. 테스트 파일 수정

   **참조 소스**:
   - 수정 대상: `projects/sisyphus-cli/tests/` 전체
   - 검색 패턴: `ai-todolist.md`, `ai-todolist.yaml` 하드코딩

   - [ ] 9.1 테스트 목록 작성

      **검증 명령어**:
      ```bash
      grep -r "ai-todolist\.md\|ai-todolist\.yaml" projects/sisyphus-cli/tests/ --files-with-matches
      ```

   - [ ] 9.2 주요 테스트 파일 수정
      - [ ] `tests/test_cli_ignore.py`: `.sisyphus/` 참조로 변경
      - [ ] `tests/test_integration_yaml_plan.py`: `.sisyphus/tasks/` 구조로 변경
      - [ ] `tests/test_cli_clean_history.py`: 패턴 업데이트
      - [ ] `tests/utils/test_git.py`: 패턴 업데이트

   - [ ] 9.3 전체 테스트 실행
      - [ ] `uv run pytest projects/sisyphus-cli/tests/ -x` → 통과

   - [ ] 9.4 커밋
      - `git add tests/`
      - `git commit -m "test: update tests for v3.0 structure"`

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] 마크다운 참조 제거?
      - [ ] 하드코딩 경로 제거?
      - [ ] 전체 테스트 통과?
      - [ ] 커밋 완료?

- [ ] 10. 문서 정리

   **참조 소스**:
   - 수정 대상:
     - `projects/sisyphus-cli/docs/schemas/` (v2.1 스펙)
     - `projects/sisyphus-cli/docs/migration-v2-to-v3.md`
     - `projects/sisyphus-cli/README.md`
     - `projects/sisyphus-cli/AGENTS.md`

   - [ ] 10.1 레거시 문서 정리

      **구현 세부사항**:
      - 삭제: `docs/schemas/MIGRATION_v2.0_to_v2.1.md`
      - 삭제: `docs/schemas/ai-todolist-spec-v2.1-final.yaml`
      - 업데이트: `docs/migration-v2-to-v3.md` → "더 이상 지원 안함" 노트 추가

   - [ ] 10.2 README 업데이트

      **구현 세부사항**:
      - v2.1 참조 제거
      - `.sisyphus/tasks/` 구조 명시
      - v3.0 전용임을 명확히 기술

   - [ ] 10.3 AGENTS.md 업데이트

      **구현 세부사항**:
      - 아키텍처 다이어그램 업데이트
      - v2.1 참조 제거
      - `TaskManager` 추가

   - [ ] 10.4 커밋
      - `git add docs/ README.md AGENTS.md`
      - `git commit -m "docs: update documentation for v3.0-only"`

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] v2.1 스펙 문서 제거?
      - [ ] README/AGENTS.md 업데이트?
      - [ ] v3.0 전용 명시?
      - [ ] 커밋 완료?

- [ ] 11. 최종 검증

   **참조 소스**:
   - 전체 코드베이스

   - [ ] 11.1 Grep 검증

      **검증 명령어**:
      - [ ] `grep -r "ai-todolist\.md" projects/sisyphus-cli/sisyphus/ --exclude-dir=tests` → 0 results
      - [ ] `grep -r "plan_types" projects/sisyphus-cli/sisyphus/` → 0 results (v2.1 모델)
      - [ ] `grep -r "PlanNavigator" projects/sisyphus-cli/sisyphus/ | grep -v "# "` → 0 results

   - [ ] 11.2 전체 테스트

      **검증 명령어**:
      - [ ] `uv run pytest projects/sisyphus-cli/ -xvs` → 모든 테스트 통과
      - [ ] `uv run pytest --cov=sisyphus --cov-report=term` → 커버리지 확인

   - [ ] 11.3 타입 체크 및 린트

      **검증 명령어**:
      - [ ] `uv run basedpyright projects/sisyphus-cli/sisyphus/` → 0 errors
      - [ ] `uv run ruff check projects/sisyphus-cli/sisyphus/` → 0 errors
      - [ ] `uv run ruff format projects/sisyphus-cli/sisyphus/`

   - [ ] 11.4 수동 기능 테스트

      **검증 시나리오**:
      ```bash
      # 1. 플랜 생성
      uv run sisyphus plan init .sisyphus/tasks/verify-test.yaml
      # 예상: version: "3.0" 포함

      # 2. status.json 설정
      # .sisyphus/status.json 수동 생성:
      {
        "version": 1,
        "current_plan": {
          "plan_path": ".sisyphus/tasks/verify-test.yaml",
          "plan_root": "/Users/yeongyu/local-workspaces/sisyphus",
          "plan_id": "verify-test",
          "current_task_id": null,
          "updated_at": "2025-11-05T10:00:00Z"
        }
      }

      # 3. task 명령 테스트
      uv run sisyphus task current
      # 예상: 에러 없이 실행 (task 없으면 "작업 없음")

      uv run sisyphus task next
      # 예상: 첫 번째 pending task 출력
      ```

   - [ ] 11.5 최종 커밋
      - `git add -A`
      - `git commit -m "refactor: complete v3.0 migration - remove all v2.1 legacy"`

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] Grep 검증 통과? (레거시 참조 0개)
      - [ ] 전체 테스트 통과?
      - [ ] 타입 체크 및 린트 0 errors?
      - [ ] 수동 기능 테스트 정상?
      - [ ] 최종 커밋 완료?
      - [ ] 실제 기능 검증:
        ```bash
        # v3.0 파일 생성
        uv run sisyphus plan init .sisyphus/tasks/final-check.yaml

        # version 필드 확인
        grep "^version:" .sisyphus/tasks/final-check.yaml
        # 예상: version: "3.0"

        # CLI 명령 동작 확인
        uv run sisyphus plan lint .sisyphus/tasks/final-check.yaml
        uv run sisyphus task --help
        ```

# 성공 비전

## 사용자 관점의 성공
- 일관된 `.sisyphus/tasks/` 구조만 사용
- 단순하고 명확한 v3.0 전용 경험
- `status.json` 통한 작업 상태 추적

## 비즈니스 관점의 성공
- 코드베이스 복잡도 40% 감소 (v2.1 모델 제거)
- 유지보수 부담 감소
- 버그 발생 가능성 최소화

## 기술적 성공 기준
- 전체 테스트 통과: `uv run pytest` → 100% 통과
- 타입 체크: `uv run basedpyright` → 0 errors
- Lint: `uv run ruff check` → 0 errors
- Grep 검증:
  - `grep -r "ai-todolist\.md" sisyphus/` → 0 results
  - `grep -r "plan_types" sisyphus/` → 0 results
  - `grep -r "PlanNavigator" sisyphus/ | grep -v "#"` → 0 results

# 최종 작업 검증 체크리스트

- [ ] 1. **기능 동작 확인**
  - [ ] v3.0 플랜 생성: `sisyphus plan init .sisyphus/tasks/test.yaml` → version: "3.0"
  - [ ] status.json 기반 로드 동작
  - [ ] `task current/next` 명령 정상 동작
  - [ ] YAML 파일 status 업데이트 동작

- [ ] 2. **레거시 코드 제거 확인**
  - [ ] v2.1 파일 4개 제거 (plan_types.py, plan_navigator.py, plan_loader.py, tasks.py)
  - [ ] `ai-todolist.md` 참조 0개
  - [ ] `PlanNavigator` 사용 0개

- [ ] 3. **기존 기능 회귀 테스트**
  - [ ] 전체 테스트: `uv run pytest` → 100% 통과
  - [ ] 타입 체크: `uv run basedpyright` → 0 errors
  - [ ] Lint: `uv run ruff check` → 0 errors

- [ ] 4. **범위 준수 확인**
  - [ ] v3.0 전용 (v2.1 폴백 제거)
  - [ ] `.sisyphus/tasks/` 구조 전용
  - [ ] status.json 확장 (plan_id, current_task_id)
  - [ ] TaskManager 생성 및 사용
