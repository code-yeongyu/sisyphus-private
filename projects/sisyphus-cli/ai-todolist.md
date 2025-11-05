# 사용자의 최초 요청 (기록용)

v2.1의 8개 필드 전체를 v3.0에 추가하되, **모두 필수**로 처리. ai-todolist.md의 모든 섹션을 YAML로 표현 가능하도록 복구.

v2.1 코드를 재활용하되 v3.0 구조에 맞게 재작성. `.sisyphus/tasks/` 기반으로 완전 전환.

## 추가 사용자 요청 (기록용)

**v2.1 전체 구조 사용**:
- user_request, objectives, background, required_background
- status, workflow, success_vision, final_verification
- PlanDocument 컨테이너 구조 재활용

**Status 관리 구조**:
- WorkPlan.status: YAML 파일에 실행 상태 저장 (Standalone)
- status.json: worktree → plan 매핑 테이블만 담당
- YAML 파일이 Single Source of Truth

**필수 처리**: Optional 금지, 모든 필드 필수

# 작업 목표 (WHAT & WHY)

## 핵심 목표 (TL;DR)

v3.0 WorkPlan 모델을 v2.1의 완전한 구조로 확장하여 ai-todolist.md의 모든 섹션을 YAML로 표현 가능하게 함. 동시에 v2.1 참조 코드를 완전히 제거하여 `.sisyphus/tasks/*.yaml` 기반으로 전환.

## 상세 목표

1. **v3.0 모델 확장**: v2.1의 8개 필드 전체 추가 (모두 필수)
   - user_request, objectives, background, final_verification
   - required_background, status, workflow, success_vision
   - ai-todolist.md의 모든 섹션을 YAML로 표현 가능
   - 더 프로그래머블: 진행 상태 추적, 의존성 관리, 자동 검증

2. **v2.1 코드 완전 재활용**
   - `plan_types.py`의 모든 모델 클래스를 `plans/models.py`로 이전
   - 필드 구조는 v2.1과 동일하게 유지 (필수 필드로)

3. **v2.1 참조 완전 제거**
   - `ai-todolist.yaml` 하드코딩 제거
   - PlanLoader (v2.1용) 제거
   - PlanNavigator를 v3.0 기반으로 재작성

4. **`.sisyphus/tasks/*.yaml` 전환**
   - 모든 CLI 명령이 `.sisyphus/tasks/` 기반으로 동작

# 작업 배경 (WHY & WHAT - 현재 상태)

## 현재 상황

- **v3.0 모델**: 최소한의 필드만 (id, name, todos, references)
- **v2.1 모델**: 완전한 작업 계획서 구조 (user_request, objectives, background, required_background, status, workflow, success_vision, final_verification)
- **혼재**: v2.1 코드(`plan_types.py`, `PlanNavigator`)가 여전히 존재
- **하드코딩**: `ai-todolist.yaml` 경로가 11회 하드코딩
- **손실**: ai-todolist.md의 "필요 배경 지식", "작업 흐름", "성공 비전" 등 섹션을 YAML로 표현 불가

## 변경 이유

1. **작업 맥락 완전 손실**: v3.0은 너무 간결해서 작업의 배경, 목표, 성공 기준을 표현 불가
2. **프로그래머블 부족**: 진행 상태, 의존성 다이어그램, 자동 검증 기능 없음
3. **v2.1 잔재**: 사용하지 않는 v2.1 코드가 혼란 유발
4. **마이그레이션 완성**: `.sisyphus/tasks/` 기반으로 완전 전환 필요

## 변경 내용

**현재 상태 → 미래 상태**

```python
# 현재 v3.0 WorkPlan (단순)
class WorkPlan(BaseModel):
    id: str
    name: str
    depends_on: list[str] = []
    todos: list[Todo]
    references: list[ReferenceItem] = []

# 미래 v3.0 WorkPlan (v2.1 완전 구조)
class WorkPlan(BaseModel):
    id: str
    name: str
    depends_on: list[str] = []

    # v2.1 필드 8개 추가 (모두 필수)
    user_request: UserRequest
    objectives: Objectives
    background: Background
    required_background: RequiredBackground
    status: Status
    workflow: Workflow
    success_vision: SuccessVision
    final_verification: list[FinalVerificationItem]

    todos: list[Todo]
    references: list[ReferenceItem] = []
```

**v2.1 제거/재작성 항목**:
- `sisyphus/utils/plan_types.py` 전체 파일 삭제
- `sisyphus/core/plan_loader.py` (v2.1용) 삭제
- `sisyphus/core/plan_navigator.py` (v2.1 의존) → v3.0 기반 재작성

# 작업 시작 여부
is_execution_started = FALSE

# 모든 목표 달성 여부
is_all_goals_accomplished = FALSE

# 병렬 실행
parallel_requested = FALSE

# 현재 진행 중인 작업
- 작업이 시작되지 않았습니다.
   - 작업 시작 시, 위의 `is_execution_started` 값을 TRUE로 변경하세요.
   - 사용자가 명시적으로 "작업을 시작해"라고 말하기 전까지는 절대 작업을 시작하지 마세요.
   - **plan reviewer로부터 OKAY를 받아도, 절대 작업을 시작하지 마세요**
   - 사용자가 명시적으로 "작업을 시작해"라고 말하기 전까지는 절대 작업을 시작하지 마세요.

# 필요 배경 지식

## 도메인 지식
- **Pydantic 모델**: v2.0+ 기반, BaseModel 상속, Field validation
- **v2.1 vs v3.0 차이**: v2.1은 단일 WorkPlan, v3.0은 PlanDocument 컨테이너 + 다중 WorkPlan
- **YAML 파싱**: ruamel.yaml 사용 (preserve_quotes, default_flow_style)

## 아키텍처 이해

### v2.1 아키텍처 (제거 대상)
```
WorkPlan (utils/plan_types.py):
- status.work_mode.current_task_id  ← YAML에 상태 저장
- status.execution.started
- todos[].status

파일: ai-todolist.yaml (루트)
```

### v3.0 아키텍처 (목표)
```
WorkPlan (core/plans/models.py):
- status.work_mode.current_task_id  ← v3.0도 동일하게 YAML에 저장!
- status.execution.started
- todos[].status

PlanDocument:
- version: "3.0"
- work_plans[]

status.json (.sisyphus/status.json):
- 워크트리 → plan 파일 매핑만
- 예: {"current_plan_path": ".sisyphus/tasks/plan-a.yaml"}

파일: .sisyphus/tasks/*.yaml
```

**핵심 차이**:
- ✅ **v3.0도 상태를 YAML에 저장** (v2.1과 동일)
- ✅ status.json은 워크트리:플랜 매핑 테이블만 담당
- ✅ YAML 파일이 Single Source of Truth

## 기술 스택
- Python 3.12+
- Pydantic 2.0+
- ruamel.yaml 0.18+
- anyio 4.11+ (비동기 파일 I/O)

## 파일 구조 및 역할

### 핵심 파일

**1. `sisyphus/core/plans/models.py` (v3.0 모델)**
- **역할**: v3.0 YAML 스키마 정의
- **검색 키워드**: `class WorkPlan(BaseModel)`, `class PlanDocument`
- **패턴**: Pydantic 모델, Optional 필드는 `| None = None`

**2. `sisyphus/utils/plan_types.py` (v2.1 모델 - 제거 대상)**
- **역할**: v2.1 YAML 스키마 정의 (248줄)
- **검색 키워드**: `class UserRequest`, `class Objectives`, `class Background`
- **재활용 대상**: UserRequest, Objectives, Background, FinalVerificationItem 클래스

**3. `sisyphus/core/plan_loader.py` (v2.1 로더 - 제거 대상)**
- **역할**: v2.1 WorkPlan 로드/저장
- **대체**: `sisyphus/core/plans/loader.py` (v3.0 로더 - 이미 존재)

**4. `sisyphus/core/plan_navigator.py` (v2.1 의존 - 재작성 대상)**
- **역할**: v2.1 WorkPlan 네비게이션 (DFS, CompletionReport)
- **변경**: v2.1 WorkPlan → v3.0 WorkPlan 모델 사용 (status 필드는 v3.0에도 있음)
- **대체**: v3.0 모델 기반으로 재작성 (`sisyphus/core/plans/navigator.py`)

**5. `sisyphus/cli/task.py` (수정 필요)**
- **역할**: task 명령어 핸들러
- **문제**: `ai-todolist.yaml` 11회 하드코딩, v2.1 모델 import
- **검색 키워드**: `plan_path = working_dir / "ai-todolist.yaml"`

**6. `sisyphus/cli/plan.py` (수정 필요)**
- **역할**: plan 명령어 핸들러
- **문제**: `ai-todolist.yaml` 참조
- **검색 키워드**: `Path("./ai-todolist.yaml")`

**7. `sisyphus/utils/formatting.py` (수정 필요)**
- **역할**: 출력 포맷팅 유틸리티
- **문제**: v2.1 plan_types import 사용
- **검색 키워드**: `from sisyphus.utils.plan_types import`

**8. `sisyphus/core/plan_linter.py` (수정 필요)**
- **역할**: YAML 플랜 검증
- **문제**: v2.1 plan_types import 사용
- **검색 키워드**: `from sisyphus.utils.plan_types import`

### 참조 파일 (패턴 이해용)

**1. `.sisyphus/tasks/2024/q4/deep-plan.yaml`**
- **역할**: v3.0 YAML 실제 예시
- **패턴**: `version: "3.0"`, `work_plans:`, `todos:`

**2. `sisyphus/core/plans/loader.py`**
- **역할**: v3.0 YAML 로드 (async)
- **패턴**: `await anyio.open_file()`, `PlanDocument(**data)`

**3. `sisyphus/core/exporters/markdown.py`**
- **역할**: v3.0 → Markdown 변환
- **패턴**: PlanDocument 순회, Todo 재귀 포맷

**4. `sisyphus/cli/work.py:100-206`**
- **역할**: `.sisyphus/tasks/` 자동 감지 로직
- **패턴**: `_detect_plan_path` 함수, StatusManager 사용

# 작업 흐름 (HOW - 태스크 플로우 & 의존성)

## 태스크 의존성 다이어그램

```
Task 1 (v3.0 모델 확장 - 기초)
   ↓
Task 2 (v2.1 파일 제거 및 Navigator 재작성 - 1 의존)
   ↓
Task 3 (하드코딩 제거 및 동적 감지 - 2 완료 필요)
   ↓
Task 4 (테스트 업데이트 - 3 완료 필요)
   ↓
Task 5 (문서 업데이트 - 4 완료 필요)
```

## 단계별 설명

- **Phase 1 (Task 1)**: v3.0 모델에 오버뷰 필드 추가
  - UserRequest, Objectives, Background, FinalVerificationItem 클래스 추가

- **Phase 2 (Task 2)**: v2.1 제거 및 Navigator 재작성
  - v2.1 전용 파일 삭제
  - PlanNavigator를 v3.0 기반으로 재작성

- **Phase 3 (Task 3)**: 참조 마이그레이션
  - `ai-todolist.yaml` 하드코딩 제거
  - 동적 플랜 감지 로직 추가

- **Phase 4 (Task 4-5)**: 검증 및 문서화
  - 테스트 업데이트
  - AGENTS.md 문서 업데이트

# 작업 계획

## 구현 상세

### 아키텍처 제약사항
- **비동기 우선**: anyio 사용 (asyncio/trio 호환)
- **Pydantic v2**: BaseModel, Field, model_validator 사용
- **YAML 포맷**: ruamel.yaml로 파싱 (preserve_quotes 유지)

### 완전 복구 결정
- **포함 항목**: v2.1의 8개 필드 전체 복구
  - user_request, objectives, background, final_verification
  - required_background, status, workflow, success_vision
- **필수 처리**: 모든 필드를 필수로 (ai-todolist.md의 모든 섹션을 YAML로 표현)
- **이유**:
  - ai-todolist.md와 완벽히 매핑됨 (필요 배경 지식, 작업 흐름, 성공 비전 등)
  - 더 프로그래머블: 진행 상태 자동 추적, 의존성 검증, 성공 기준 자동 실행

### PlanNavigator 재작성 결정
- **선택한 옵션**: v3.0 기반 재작성 (DFS 로직 유지)
- **이유**: 현재 작업 추적 기능은 유용하므로 로직 보존
- **변경**: v2.1 모델 의존성만 제거, v3.0 Todo 모델 사용
- **새 위치**: `sisyphus/core/plans/navigator.py`

### Status 관리 구조 (중요!)
- **WorkPlan.status** (YAML 파일):
  - **모든 실행 상태를 YAML 자체에 저장** (Standalone)
  - 예: 작업 시작 여부(execution.started), 병렬 실행 여부(work_mode.parallel_requested), 현재 태스크(work_mode.current_task_id), 진행 상태(progress)
  - ai-todolist.md의 "작업 시작 여부", "병렬 실행", "현재 진행 중인 작업", "진행 상태" 섹션이 모두 이 필드로 표현됨
  - YAML 파일만 있으면 완전한 작업 상태 복원 가능

- **StatusManager (.sisyphus/status.json)**:
  - **워크트리 : 계획서 매핑 테이블** 역할만 수행
  - 예: worktree1 → .sisyphus/tasks/plan-a.yaml
  - 다중 worktree 환경에서 "어떤 worktree가 어떤 plan을 사용하는지" 매핑 정보만 저장
  - 실행 상태는 저장하지 않음 (모두 WorkPlan.status에 있음)

→ **YAML 파일이 상태의 유일한 소스 (Single Source of Truth)**

### 암묵적 가정 명시
- v3.0 YAML 파일은 `.sisyphus/tasks/` 디렉토리 내에 존재
- **기존 v3.0 YAML 파일은 8개 필드 추가 필요**: 모든 필드가 필수이므로 기존 YAML 파일 수동 업데이트 필요
- v2.1 YAML 파일은 더 이상 지원하지 않음 (UnsupportedPlanVersionError)
- **Breaking Change**: 이 마이그레이션 후 기존 v3.0 YAML 파일은 로드 실패함 (필수 필드 누락 에러)

### 기존 v3.0 YAML 파일 마이그레이션 가이드

**문제**: 이 변경 후 기존 v3.0 YAML 파일은 8개 필드 누락으로 로드 실패 (ValidationError 발생)

**해결 방법 1: 수동 업데이트** (소규모 프로젝트, 1-3개 파일):
1. `.sisyphus/tasks/*.yaml` 파일 열기
2. Task 1.1에서 생성한 v3.0 템플릿 참조
3. 8개 필드 블록을 기존 YAML에 복사하여 추가:
   ```yaml
   work_plans:
     - id: "existing-plan"
       name: "Existing Plan"
       # === 추가할 8개 필드 (시작) ===
       user_request:
         original: "작업 요청 내용"
         created_at: "2025-11-06T00:00:00Z"
         additional: []
       objectives:
         core: "핵심 목표"
         detailed: []
       background:
         current_situation: "현재 상황"
         reason_for_change: "변경 이유"
         changes_to_make: "변경 내용"
       required_background:
         description: "필요한 배경 지식"
         file_structure: null
         references: []
       status:
         execution:
           started: false
           completed: false
           started_at: null
           completed_at: null
         work_mode:
           parallel_requested: false
           current_task_id: null
         progress:
           total_tasks: 0
           completed: 0
           in_progress: 0
           pending: 0
         current_work: "작업 시작 전"
       workflow:
         dependency_diagram: "Task 1 → Task 2 → Task 3"
         critical_path: []
       success_vision:
         user_perspective: []
         business_perspective: []
         technical_criteria: []
       final_verification: []
       # === 추가할 8개 필드 (끝) ===
       todos: [...]
   ```

**해결 방법 2: 자동 변환 스크립트** (대규모 프로젝트, 4개 이상 파일):
- Task 1에 하위 작업 추가:
  - [ ] 1.8 기존 v3.0 YAML 마이그레이션 스크립트 작성
    - **파일**: `scripts/migrate_v3_to_extended_v3.py`
    - **기능**: 기존 v3.0 YAML에 8개 필드 자동 추가 (기본값 사용)
    - **실행**: `uv run python scripts/migrate_v3_to_extended_v3.py .sisyphus/tasks/`
    - **백업**: 변환 전 자동 백업 (.yaml.bak)

**검증 방법**:
```bash
# 변환 후 로드 테스트
uv run python -c "
import anyio
from sisyphus.core.plans.loader import load_plan
from pathlib import Path

async def test():
    plan = await load_plan(Path('.sisyphus/tasks/your-plan.yaml'))
    print('✓ 마이그레이션 성공: 8개 필드 모두 로드됨')

anyio.run(test)
"
```

**예상 에러 (변환 전)**:
```
ValidationError: 3 validation errors for WorkPlan
  user_request
    Field required [type=missing, input_value=...]
  objectives
    Field required [type=missing, input_value=...]
  background
    Field required [type=missing, input_value=...]
```

## 프로젝트 커밋 메시지 스타일

```
feat: v3.0 모델에 오버뷰 필드 추가
refactor: v2.1 모델 제거 및 Navigator v3.0 재작성
fix: ai-todolist.yaml 하드코딩 제거
docs: AGENTS.md 업데이트 - v2.1 제거 완료
test: v3.0 확장 모델 테스트 추가
```

# TODOs

- [ ] 1. v3.0 WorkPlan 모델 확장 - v2.1의 8개 필드 전체 추가 (필수)

   **참조 소스 (REQUIRED)**:
   - 패턴 파일: `sisyphus/utils/plan_types.py` (v2.1 모델 - 전체 248줄)
   - 대상 파일: `sisyphus/core/plans/models.py` (v3.0 모델 - 검색: `class WorkPlan(BaseModel)`)
   - Pydantic 패턴: `sisyphus/core/plans/models.py` (검색: Field, model_validator 패턴)

   - [ ] 1.1 v2.1 모델 클래스 전체 분석

      **검색 위치**: `sisyphus/utils/plan_types.py:145-261`

      **패턴 이해** (8개 필드와 의존 클래스):
      ```python
      # 1. UserRequest (145-149)
      class UserRequest(BaseModel):
          original: str
          created_at: str
          additional: list[str] = []

      # 2. Objectives (151-159)
      class DetailedObjective(BaseModel):
          goal: str
          measurable: str

      class Objectives(BaseModel):
          core: str
          detailed: list[DetailedObjective] = []

      # 3. Background (161-165)
      class Background(BaseModel):
          current_situation: str
          reason_for_change: str
          changes_to_make: str

      # 4. RequiredBackground (167-171)
      class RequiredBackground(BaseModel):
          description: str
          file_structure: str | None = None
          references: list[ReferenceItem] = []

      # 5. Status (173-197)
      class ExecutionStatus(BaseModel):
          started: bool
          completed: bool
          started_at: str | None = None
          completed_at: str | None = None

      class WorkMode(BaseModel):
          parallel_requested: bool
          current_task_id: str | None = None

      class Progress(BaseModel):
          total_tasks: int
          completed: int
          in_progress: int
          pending: int

      class Status(BaseModel):
          execution: ExecutionStatus
          work_mode: WorkMode
          progress: Progress
          current_work: str

      # 6. Workflow (199-202)
      class Workflow(BaseModel):
          dependency_diagram: str
          critical_path: list[str] = []

      # 7. SuccessVision (204-225)
      class UserScenario(BaseModel):
          scenario: str
          experience: str

      class BusinessMetric(BaseModel):
          metric: str
          target: str

      class TechnicalCriterion(BaseModel):
          category: str
          criteria: str
          command: str | None = None
          expected: str

      class SuccessVision(BaseModel):
          user_perspective: list[UserScenario] = []
          business_perspective: list[BusinessMetric] = []
          technical_criteria: list[TechnicalCriterion] = []

      # 8. FinalVerificationItem (227-244)
      class FinalVerificationItem(BaseModel):
          id: str
          title: str
          category: str
          description: str
          verified: bool = False
          verified_at: str | None = None
          verification_evidence: str | None = None
          orchestrator_manually_verified: bool
          manual_verification_evidence: str
          bash: list[BashVerification] = []
          llm_judge: list[LLMJudgeVerification] = []
      ```

      **구현 세부사항**:
      - 현재: v2.1에 8개 필드 존재
      - 변경: **8개 전체 복구** (user_request, objectives, background, required_background, status, workflow, success_vision, final_verification)
      - 노트: 모든 필드 **필수**로 (Optional 금지)

   - [ ] 1.2 v3.0 WorkPlan에 8개 필드 추가

      **수정 파일**: `sisyphus/core/plans/models.py:47-52`

      **구현 세부사항**:
      ```python
      # 현재 v3.0 WorkPlan
      class WorkPlan(BaseModel):
          id: str
          name: str
          depends_on: list[str] = []
          todos: list[Todo]
          references: list[ReferenceItem] = []

      # 변경 후 (v2.1 완전 구조)
      class WorkPlan(BaseModel):
          id: str
          name: str
          depends_on: list[str] = []

          # v2.1 필드 8개 추가 (모두 필수)
          user_request: UserRequest
          objectives: Objectives
          background: Background
          required_background: RequiredBackground
          status: Status
          workflow: Workflow
          success_vision: SuccessVision
          final_verification: list[FinalVerificationItem]

          todos: list[Todo]
          references: list[ReferenceItem] = []
      ```

      **중요**: 모든 필드를 필수로 선언 (Optional 처리 금지)

   - [ ] 1.3 의존 클래스 전체 정의 (8개 필드의 모든 의존 클래스)

      **참조 패턴**: `sisyphus/utils/plan_types.py:145-261`

      **구현 세부사항** (필드별 클래스 목록):

      **1. UserRequest 관련**:
      - `UserRequest`: original, created_at, additional

      **2. Objectives 관련**:
      - `DetailedObjective`: goal, measurable
      - `Objectives`: core, detailed

      **3. Background 관련**:
      - `Background`: current_situation, reason_for_change, changes_to_make

      **4. RequiredBackground 관련**:
      - `RequiredBackground`: description, file_structure, references

      **5. Status 관련**:
      - `ExecutionStatus`: started, completed, started_at, completed_at
      - `WorkMode`: parallel_requested, current_task_id
      - `Progress`: total_tasks, completed, in_progress, pending
      - `Status`: execution, work_mode, progress, current_work

      **6. Workflow 관련**:
      - `Workflow`: dependency_diagram, critical_path

      **7. SuccessVision 관련**:
      - `UserScenario`: scenario, experience
      - `BusinessMetric`: metric, target
      - `TechnicalCriterion`: category, criteria, command, expected
      - `SuccessVision`: user_perspective, business_perspective, technical_criteria

      **8. FinalVerificationItem 관련**:
      - `BashVerification`: execute, expected_stdout, expected_stderr, expected_exit_code, notes
      - `LLMJudgeBy` Enum: ORCHESTRATOR, EXTERNAL
      - `LLMJudgeVerification`: by, context_commands, instruction
      - `FinalVerificationItem`: id, title, category, description, verified, verified_at, verification_evidence, orchestrator_manually_verified, manual_verification_evidence, bash, llm_judge

      **참고**: v2.1의 모든 클래스를 그대로 복사하여 `sisyphus/core/plans/models.py`에 추가 (총 20개 이상의 클래스)

   - [ ] 1.4 Pydantic validator 추가 (FinalVerificationItem)

      **참조 패턴**: `sisyphus/utils/plan_types.py:240-244`

      **코드 패턴**:
      ```python
      @model_validator(mode="after")
      def validate_at_least_one(self) -> Self:
          if not self.bash and not self.llm_judge:
              raise ValueError("bash 또는 llm_judge 중 하나 이상 필수")
          return self
      ```

   - [ ] 1.5 타입 체크 및 import 정리

      **실행 명령어**: `uv run basedpyright sisyphus/core/plans/models.py`

      **예상 출력**:
      ```
      0 errors, 0 warnings, 0 informations
      ```

      **실패 시**:
      - Import 누락 → `from typing import Self` 추가
      - 순환 참조 → `from __future__ import annotations` 확인

   - [ ] 1.6 테스트 작성 - v2.1 완전 구조 모델 파싱

      **테스트 파일**: `tests/core/plans/test_models_v3.py` (신규 또는 수정)

      **테스트 케이스**:
      ```python
      def test_workplan_with_all_v21_fields():
          """v3.0 WorkPlan이 v2.1의 8개 필드를 모두 파싱하는지 확인"""
          data = {
              "id": "plan-1",
              "name": "Test Plan",
              "user_request": {
                  "original": "Add feature X",
                  "created_at": "2025-11-06T00:00:00Z",
                  "additional": ["Use library Y"]
              },
              "objectives": {
                  "core": "Implement feature X",
                  "detailed": [{"goal": "Goal 1", "measurable": "Metric 1"}]
              },
              "background": {
                  "current_situation": "No feature X",
                  "reason_for_change": "User requests",
                  "changes_to_make": "Add feature X"
              },
              "required_background": {
                  "description": "Domain knowledge about feature X",
                  "file_structure": "src/features/x/",
                  "references": []
              },
              "status": {
                  "execution": {
                      "started": False,
                      "completed": False,
                      "started_at": None,
                      "completed_at": None
                  },
                  "work_mode": {
                      "parallel_requested": False,
                      "current_task_id": None
                  },
                  "progress": {
                      "total_tasks": 10,
                      "completed": 0,
                      "in_progress": 0,
                      "pending": 10
                  },
                  "current_work": "Not started"
              },
              "workflow": {
                  "dependency_diagram": "Task 1 -> Task 2 -> Task 3",
                  "critical_path": ["Task 1", "Task 2", "Task 3"]
              },
              "success_vision": {
                  "user_perspective": [
                      {"scenario": "User opens app", "experience": "Sees feature X"}
                  ],
                  "business_perspective": [
                      {"metric": "User engagement", "target": "20% increase"}
                  ],
                  "technical_criteria": [
                      {
                          "category": "Performance",
                          "criteria": "Tests pass",
                          "command": "pytest",
                          "expected": "All pass"
                      }
                  ]
              },
              "final_verification": [
                  {
                      "id": "verify-1",
                      "title": "Test passes",
                      "category": "functional",
                      "description": "All tests pass",
                      "orchestrator_manually_verified": False,
                      "manual_verification_evidence": "",
                      "bash": [{"execute": "pytest", "expected_exit_code": 0}]
                  }
              ],
              "todos": [],
              "references": []
          }
          plan = WorkPlan(**data)
          assert plan.user_request.original == "Add feature X"
          assert plan.objectives.core == "Implement feature X"
          assert plan.status.progress.total_tasks == 10
          assert plan.workflow.dependency_diagram == "Task 1 -> Task 2 -> Task 3"
          assert len(plan.success_vision.technical_criteria) == 1
      ```

   - [ ] 1.7 테스트 실행 및 검증

      **실행 명령어**: `uv run pytest tests/core/plans/test_models_v3.py -xvs`

      **예상 출력**:
      ```
      test_workplan_with_overview_fields ... PASSED
      ===================== 1 passed in 0.15s =====================
      ```

   - [ ] 1.8 커밋 (모델 확장 완료 후)

      **커밋 명령어**:
      ```bash
      git add sisyphus/core/plans/models.py tests/core/plans/test_models_v3.py
      git commit -m "feat: add v2.1 complete structure to v3.0 WorkPlan model

Add all 8 fields from v2.1 to v3.0 WorkPlan (user_request, objectives,
background, required_background, status, workflow, success_vision,
final_verification). All fields are REQUIRED (no Optional).

This enables ai-todolist.md sections to be fully represented in YAML.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
      ```

   - [ ] **작업 완료 검증 체크리스트** (Orchestrator용 acceptance criteria)
      - [ ] `sisyphus/core/plans/models.py`에 20개 이상의 클래스 추가되었는가?
        - [ ] 8개 메인 필드: UserRequest, Objectives, Background, RequiredBackground, Status, Workflow, SuccessVision, FinalVerificationItem
        - [ ] 의존 클래스: DetailedObjective, ExecutionStatus, WorkMode, Progress, UserScenario, BusinessMetric, TechnicalCriterion, BashVerification, LLMJudgeBy, LLMJudgeVerification 등
      - [ ] WorkPlan에 8개 필드 추가되었는가? (user_request, objectives, background, required_background, status, workflow, success_vision, final_verification)
      - [ ] 모든 8개 필드가 **필수**인가? (Optional 처리 없음)
      - [ ] `uv run basedpyright sisyphus/core/plans/models.py` → 0 errors?
      - [ ] 테스트 파일 `tests/core/plans/test_models_v3.py` 작성되었는가?
      - [ ] 테스트가 8개 필드를 모두 검증하는가?
      - [ ] `uv run pytest tests/core/plans/test_models_v3.py -xvs` → PASSED?
      - [ ] git commit 완료되었는가? (`git log -1 --oneline` 확인)


- [ ] 2. v2.1 파일 제거 및 PlanNavigator v3.0 재작성

   **참조 소스 (REQUIRED)**:
   - 제거 대상 1: `sisyphus/utils/plan_types.py` (v2.1 모델 전체 - 248줄)
   - 제거 대상 2: `sisyphus/core/plan_loader.py` (v2.1 로더 - 28줄)
   - 재작성 대상: `sisyphus/core/plan_navigator.py` (v2.1 네비게이터 - 320줄)
   - 대체 확인: `sisyphus/core/plans/loader.py` (v3.0 로더 - 이미 존재)

   - [ ] 2.1 v2.1 파일 사용처 검색 및 분석

      **검색 명령어**:
      ```bash
      # plan_types.py 사용처
      uv run rg "from sisyphus.utils.plan_types import" --type py

      # plan_loader.py 사용처
      uv run rg "from sisyphus.core.plan_loader import" --type py

      # plan_navigator.py 사용처
      uv run rg "from sisyphus.core.plan_navigator import" --type py
      ```

      **예상 결과**: `cli/task.py`, `cli/plan.py`, `formatting.py`, `plan_linter.py`, 테스트 파일들

   - [ ] 2.2 모든 v2.1 의존 파일에서 import 제거 및 수정

      **수정 필요 파일 전체 목록** (12개):
      1. `sisyphus/cli/task.py` - v2.1 import 제거, v3.0 모델로 대체
      2. `sisyphus/cli/plan.py` - v2.1 import 제거, v3.0 모델로 대체
      3. `sisyphus/utils/formatting.py` - plan_types import → plans.models로 변경
         - **추가**: `print_overview` 함수 재작성 (8개 필드 모두 REQUIRED이므로 직접 접근 가능)
      4. `sisyphus/core/plan_linter.py` - plan_types import → plans.models로 변경
      5. `sisyphus/tests/test_cli_plan.py` - 테스트 픽스처 v3.0으로 전환
      6. `sisyphus/tests/test_integration_yaml_plan.py` - 테스트 픽스처 v3.0으로 전환
      7. `sisyphus/tests/test_integration_plan_filtering_completion.py` - 테스트 픽스처 v3.0으로 전환
      8. `sisyphus/utils/tests/test_plan_types.py` - 삭제 (v2.1 전용 테스트)
      9. `sisyphus/core/tests/test_plan_loader.py` - 삭제 (v2.1 전용 테스트)
      10. `sisyphus/core/tests/test_plan_navigator.py` - 삭제 (v2.1 전용 테스트)
      11-12. v2.1 의존하는 기타 테스트 파일 2개 (Grep으로 확인 후 수정)

      **각 파일 수정 패턴**:
      ```python
      # 현재 (제거)
      from sisyphus.core.plan_loader import PlanLoader
      from sisyphus.core.plan_navigator import PlanNavigator
      from sisyphus.utils.plan_types import Todo, TodoStatus

      # 변경 후 (v3.0 사용)
      from sisyphus.core.plans.loader import load_plan
      from sisyphus.core.plans.navigator import PlanNavigator  # v3.0 재작성 버전
      from sisyphus.core.plans.models import Todo, TodoStatus
      ```

      **formatting.py 재작성 상세**:
      ```python
      # 현재 (v2.1 의존)
      def print_overview(plan: WorkPlan):
          print(plan.user_request.original)
          print(plan.background.current_situation)

      # 변경 후 (v3.0 - 8개 필드 모두 REQUIRED)
      def print_overview(plan: WorkPlan):
          print(plan.user_request.original)  # 필수 필드이므로 직접 접근
          print(plan.background.current_situation)  # 필수 필드이므로 직접 접근
      ```

      **노트**: `ai-todolist.yaml` 하드코딩은 Task 3에서 처리

   - [ ] 2.3 v2.1 전용 파일 삭제

      **삭제 명령어**:
      ```bash
      rm sisyphus/utils/plan_types.py
      rm sisyphus/core/plan_loader.py
      rm sisyphus/core/plan_navigator.py  # 다음 단계에서 v3.0 버전 생성
      ```

   - [ ] 2.4 PlanNavigator v3.0 재작성

      **신규 파일**: `sisyphus/core/plans/navigator.py`

      **참조 패턴**: `sisyphus/core/plan_navigator.py` (v2.1 버전 - 로직 재사용)

      **구현 방향**:
      - **유지**: DFS 알고리즘, CompletionReport, 모든 public 메서드
      - **변경**: v2.1 WorkPlan → v3.0 WorkPlan/Todo 모델 사용
      - **중요**: `plan.status.work_mode.current_task_id` 접근은 **그대로 유지** (v3.0에도 status 필드 있음!)

      **주요 변경 사항**:
      ```python
      # v2.1 버전
      def __init__(self, plan: WorkPlan) -> None:
          self.plan = plan  # v2.1 WorkPlan (status 필드 포함)

      def get_current_task(self) -> Todo | None:
          current_id = self.plan.status.work_mode.current_task_id
          return self.find_todo_by_id(current_id)

      # v3.0 버전 (거의 동일!)
      def __init__(self, work_plan: WorkPlan) -> None:
          self.work_plan = work_plan  # v3.0 WorkPlan (status 필드 포함!)

      def get_current_task(self) -> Todo | None:
          current_id = self.work_plan.status.work_mode.current_task_id  # v3.0도 동일!
          return self.find_todo_by_id(current_id)
      ```

      **노트**: v3.0에도 status 필드가 있으므로 v2.1 로직을 거의 그대로 복사 가능. 모델만 교체하면 됨.

      **핵심 메서드 목록** (v2.1에서 유지):
      - `find_todo_by_id(target_id)` → DFS 검색
      - `get_current_task()` → 현재 작업 조회
      - `get_next_task(current_id)` → DFS 기반 다음 작업
      - `get_previous_task(current_id)` → 역방향 DFS
      - `get_task_references(task_id)` → 참조 조회
      - `get_task_children(task_id)` → 자식 조회
      - `get_all_descendants(task_id)` → 모든 자손
      - `get_task_verification(task_id)` → 검증 스펙
      - `get_parallel_group_tasks(group_id)` → 병렬 그룹
      - `check_task_completion(task_id)` → 완료 체크
      - `next_unverified()` → 다음 미검증 항목

      **CompletionReport** (v3.0 버전):
      ```python
      @dataclass
      class CompletionReport:
          task_id: str
          task_status: TodoStatus
          all_children_completed: bool
          children_summary: dict[str, int]
          all_verifications_completed: bool
          verification_summary: dict[str, int]
          can_complete: bool
      ```

   - [ ] 2.5 타입 체크 (전체 프로젝트)

      **실행 명령어**: `uv run basedpyright`

      **예상 출력**: 0 errors (import 에러 없음)

      **실패 시**: 누락된 import 또는 파일 확인

   - [ ] 2.6 커밋 (v2.1 파일 제거 및 Navigator 재작성 완료 후)

      **커밋 명령어**:
      ```bash
      git add -A
      git commit -m "refactor: remove v2.1 files and rewrite PlanNavigator for v3.0

Remove plan_types.py, plan_loader.py, plan_navigator.py (v2.1).
Create new plans/navigator.py with v3.0 models.
Update all imports to use v3.0 models and loaders.

Key changes:
- PlanNavigator now uses v3.0 WorkPlan/Todo models
- current_task_id accessed from plan.status.work_mode.current_task_id (v3.0 also has status field)
- All DFS logic and CompletionReport preserved

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
      ```

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] `sisyphus/utils/plan_types.py` 파일이 삭제되었는가?
      - [ ] `sisyphus/core/plan_loader.py` 파일이 삭제되었는가?
      - [ ] `sisyphus/core/plan_navigator.py` 파일이 삭제되었는가?
      - [ ] `sisyphus/core/plans/navigator.py` 파일이 생성되었는가?
      - [ ] 모든 파일(12개)에서 v2.1 import가 제거되었는가?
        - [ ] `cli/task.py` - v3.0 import 사용?
        - [ ] `cli/plan.py` - v3.0 import 사용?
        - [ ] `formatting.py` - v3.0 import 사용? (print_overview 함수 재작성 포함)
        - [ ] `plan_linter.py` - v3.0 import 사용?
        - [ ] `tests/*.py` (8개) - v3.0 import 사용?
      - [ ] `formatting.py`의 `print_overview` 함수가 Optional 필드 처리로 재작성되었는가?
      - [ ] PlanNavigator v3.0이 모든 핵심 메서드를 포함하는가? (11개 메서드)
      - [ ] `uv run basedpyright` → 0 errors?
      - [ ] git commit 완료되었는가?


- [ ] 3. ai-todolist.yaml 하드코딩 제거 및 동적 플랜 감지 추가

   **참조 소스 (REQUIRED)**:
   - 수정 대상: `sisyphus/cli/task.py` (검색: `"ai-todolist.yaml"` - 11회 출현)
   - 수정 대상: `sisyphus/cli/plan.py` (검색: `"ai-todolist.yaml"`)
   - 참조 패턴: `sisyphus/cli/work.py:100-206` (`.sisyphus/tasks/` 자동 감지 로직)
   - StatusManager: `sisyphus/core/status/manager.py`

   - [ ] 3.1 work.py의 플랜 감지 로직 분석

      **검색 위치**: `sisyphus/cli/work.py:100-206` (`_detect_plan_path` 함수)

      **패턴 이해**:
      ```python
      async def _detect_plan_path(ui: UIProtocol) -> Path | None:
          """
          1. ai-todolist.md 존재 시 에러 (Markdown 미지원)
          2. .sisyphus/tasks/**/*.yaml 파일이 1개면 자동 선택
          3. 여러 파일이면 사용자 선택 프롬프트
          """
          worktree_root = await StatusManager.detect_worktree()
          tasks_dir = worktree_root / ".sisyphus" / "tasks"
          yaml_files = list(tasks_dir.glob("**/*.y*ml"))

          if len(yaml_files) == 1:
              return yaml_files[0].absolute()
          elif len(yaml_files) > 1:
              # 사용자 선택 로직
              pass
      ```

   - [ ] 3.2 플랜 감지 유틸리티 함수 추가 (detect_plan_path() 생성 - Task 3.3/3.4에서 사용)

      **신규 파일**: `sisyphus/utils/plan_helpers.py`

      **함수 구현**:
      ```python
      from __future__ import annotations

      from pathlib import Path

      from sisyphus.core.status.manager import StatusManager


      async def detect_plan_path(working_dir: Path) -> Path:
          """
          Detect plan file path from .sisyphus/tasks/ or status.json.

          Priority order:
          1. StatusManager.current_plan_path (worktree:plan 매핑)
          2. .sisyphus/tasks/**/*.yaml (if only 1 file found)
          3. Multiple files → ValueError (ambiguous)
          4. No files → FileNotFoundError

          Args:
              working_dir: Working directory (project root)

          Returns:
              Path: Absolute path to plan file

          Raises:
              FileNotFoundError: No .sisyphus/tasks/ or no plan files
              ValueError: Multiple plans found (ambiguous)

          Note:
              StatusManager는 worktree → plan_path 매핑만 저장.
              실행 상태는 YAML 파일의 WorkPlan.status에 저장됨.
          """
          # 1. StatusManager 체크 (워크트리:플랜 매핑)
          status_path = working_dir / ".sisyphus" / "status.json"
          manager = StatusManager(status_path)
          status = await manager.get()

          if status.current_plan_path:  # 워크트리에 매핑된 플랜
              return working_dir / status.current_plan_path

          # 2. .sisyphus/tasks/ 자동 감지
          tasks_dir = working_dir / ".sisyphus" / "tasks"
          if not tasks_dir.exists():
              raise FileNotFoundError(
                  f"No .sisyphus/tasks/ directory found in {working_dir}"
              )

          # 대소문자 무시 (yaml, yml, YAML, YML)
          yaml_files = []
          for pattern in ("**/*.yaml", "**/*.yml", "**/*.YAML", "**/*.YML"):
              yaml_files.extend(tasks_dir.glob(pattern))
          yaml_files = list(set(yaml_files))  # 중복 제거

          if len(yaml_files) == 0:
              raise FileNotFoundError(
                  f"No YAML plan files in {tasks_dir}. "
                  "Create one with 'sisyphus plan init'."
              )
          elif len(yaml_files) == 1:
              return yaml_files[0].absolute()
          else:
              # 여러 파일 발견 → 에러 (사용자 선택 필요)
              relative_paths = [f.relative_to(working_dir) for f in yaml_files]
              raise ValueError(
                  f"Multiple plan files found ({len(yaml_files)}):\n"
                  + "\n".join(f"  - {p}" for p in relative_paths)
                  + "\n\nUse 'sisyphus work' to select or set current plan."
              )
      ```

      **StatusManager 역할 명확화**:
      - **.sisyphus/status.json**: worktree → plan_path 매핑만 저장
      - 실행 상태는 YAML 파일의 WorkPlan.status에 저장됨

   - [ ] 3.3 task.py, plan.py, docs/, tests/의 모든 `ai-todolist.yaml` 하드코딩 제거 (detect_plan_path() 함수 사용)

      **수정 파일 범위** (총 13개 파일, 104회 출현):

      **코드 파일** (8개):
      1. `sisyphus/cli/task.py` (11회) - 동적 감지 로직으로 대체
      2. `sisyphus/cli/plan.py` (6회) - 동적 감지 로직으로 대체
      3. `sisyphus/core/plan_loader.py` (1회) - 동적 감지 로직으로 대체
      4-8. v2.1 의존하는 기타 코드 파일 (Grep 결과 확인)

      **문서 파일** (5개):
      - `docs/plan-lint.md` - 예시 경로를 `.sisyphus/tasks/example.yaml`로 업데이트
      - `docs/migration-v2-to-v3.md` - 예시 경로 업데이트
      - `docs/api.md` - 예시 경로 업데이트
      - `docs/plan-schema.md` - 예시 경로 업데이트
      - 기타 1개 문서 파일 (Grep 결과 확인)

      **테스트 파일** (6개):
      - `tests/cli/test_plan_commands.py` - 픽스처 경로를 `.sisyphus/tasks/test.yaml`로 업데이트
      - `tests/cli/test_task_commands.py` - 픽스처 경로 업데이트
      - `tests/integration/test_full_workflow.py` - 픽스처 경로 업데이트
      - `tests/cli/test_cwd_option.py` - 픽스처 경로 업데이트
      - 기타 2개 테스트 파일 (Grep 결과 확인)

      **검색 키워드**: `"ai-todolist.yaml"` (총 104회 출현)

      **조치 사항**:
      - **코드**: `ai-todolist.yaml` → `detect_plan_path()` 함수 사용
      - **문서**: 예시 경로를 `.sisyphus/tasks/example.yaml`로 업데이트
      - **테스트**: 픽스처 경로를 `.sisyphus/tasks/test.yaml`로 업데이트

      **통일된 플랜 감지 전략 (우선순위 순서)**:
      ```python
      async def detect_plan_path(working_dir: Path) -> Path:
          """
          Detect plan file path with clear priority.

          Priority order:
          1. StatusManager.current_plan_path (워크트리:플랜 매핑 테이블)
          2. .sisyphus/tasks/**/*.yaml (if only 1 file)
          3. Multiple files → Error (user must select)
          4. No files → Error
          """
          # 1. StatusManager 체크 (워크트리:플랜 매핑만 저장)
          status_path = working_dir / ".sisyphus" / "status.json"
          manager = StatusManager(status_path)
          status = await manager.get()

          if status.current_plan_path:  # 워크트리에 매핑된 플랜 경로
              return working_dir / status.current_plan_path

          # 2. .sisyphus/tasks/ 자동 감지
          tasks_dir = working_dir / ".sisyphus" / "tasks"
          if not tasks_dir.exists():
              raise FileNotFoundError("No .sisyphus/tasks/ directory")

          yaml_files = list(tasks_dir.glob("**/*.y*ml"))

          if len(yaml_files) == 1:
              return yaml_files[0].absolute()
          elif len(yaml_files) > 1:
              raise ValueError(f"Multiple plans found ({len(yaml_files)}). Use 'sisyphus work' to select.")
          else:
              raise FileNotFoundError("No plan files in .sisyphus/tasks/")
      ```

      **구현 세부사항**:
      ```python
      # 현재 (제거)
      plan_path = working_dir / "ai-todolist.yaml"

      # 변경 후 (동적 감지 - Task 3.2에서 생성한 함수 사용)
      plan_path = await detect_plan_path(working_dir)
      ```

   - [ ] 3.4 plan.py의 `ai-todolist.yaml` 하드코딩 제거 (detect_plan_path() 함수 사용)

      **수정 파일**: `sisyphus/cli/plan.py`

      **검색 키워드**: `"ai-todolist.yaml"`

      **구현 세부사항**: `task.py`와 동일한 패턴 적용 (Task 3.2의 detect_plan_path() 함수 사용)

   - [ ] 3.5 타입 체크 및 린트

      **실행 명령어**:
      ```bash
      uv run basedpyright sisyphus/cli/task.py sisyphus/cli/plan.py sisyphus/utils/plan_helpers.py
      uv run ruff check sisyphus/cli/task.py sisyphus/cli/plan.py sisyphus/utils/plan_helpers.py
      ```

      **예상 출력**: 0 errors

   - [ ] 3.6 테스트 작성 - plan_helpers.py

      **테스트 파일**: `tests/utils/test_plan_helpers.py` (신규)

      **테스트 케이스**:
      - `test_detect_plan_from_status_json()` - StatusManager 우선
      - `test_detect_plan_single_file()` - 1개 파일 자동 선택
      - `test_detect_plan_multiple_files_error()` - 여러 파일 에러
      - `test_detect_plan_no_files_error()` - 파일 없음 에러

   - [ ] 3.7 테스트 실행

      **실행 명령어**: `uv run pytest tests/utils/test_plan_helpers.py -xvs`

      **예상 출력**: All tests pass

   - [ ] 3.8 커밋 (하드코딩 제거 완료 후)

      **커밋 명령어**:
      ```bash
      git add sisyphus/cli/task.py sisyphus/cli/plan.py sisyphus/utils/plan_helpers.py tests/
      git commit -m "fix: remove ai-todolist.yaml hardcoding, add dynamic plan detection

Replace all ai-todolist.yaml references with dynamic plan detection.
Add plan_helpers.py with clear priority:
1. StatusManager.current_plan.plan_path
2. .sisyphus/tasks/**/*.yaml (if single file)
3. Error if multiple/no files

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
      ```

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] CLI 파일에서 `"ai-todolist.yaml"` 문자열이 0개인가?
        - [ ] `sisyphus/cli/task.py` (`rg "ai-todolist.yaml" sisyphus/cli/task.py`)
        - [ ] `sisyphus/cli/plan.py`
      - [ ] 문서 파일에서 예시 경로가 업데이트되었는가?
        - [ ] `docs/*.md` (5개) - `.sisyphus/tasks/example.yaml` 패턴 사용
      - [ ] 테스트 파일에서 픽스처 경로가 업데이트되었는가?
        - [ ] `tests/*.py` (6개) - `.sisyphus/tasks/test.yaml` 패턴 사용
      - [ ] `sisyphus/utils/plan_helpers.py` 파일이 생성되었는가?
      - [ ] `detect_plan_path()` 함수가 구현되었는가?
      - [ ] 우선순위가 명확한가? (1. StatusManager, 2. 단일 파일, 3. 에러)
      - [ ] `uv run basedpyright` → 0 errors?
      - [ ] `uv run pytest tests/utils/test_plan_helpers.py -xvs` → All pass?
      - [ ] git commit 완료되었는가?


- [ ] 4. 테스트 전체 업데이트 및 회귀 테스트

   **참조 소스 (REQUIRED)**:
   - 테스트 디렉토리: `tests/` (전체)
   - 픽스처 패턴: `tests/fixtures/plans/` (v2 vs v3 YAML 예시)
   - pytest 패턴: `tests/core/plans/test_models_v3.py` (v3.0 모델 테스트)

   - [ ] 4.1 v2.1 의존 테스트 검색

      **검색 명령어**:
      ```bash
      # plan_types 사용 테스트
      uv run rg "from sisyphus.utils.plan_types" tests/

      # PlanLoader 사용 테스트
      uv run rg "PlanLoader" tests/

      # PlanNavigator 사용 테스트
      uv run rg "PlanNavigator" tests/
      ```

   - [ ] 4.2 v2.1 의존 테스트 수정 또는 삭제

      **테스트 파일 처리 계획**:

      **삭제 (v2.1 전용)**:
      - `tests/utils/test_plan_types.py` - v2.1 모델 테스트 (더 이상 필요 없음)
      - `tests/core/test_plan_loader.py` - v2.1 로더 테스트 (v3.0 loader 테스트로 대체)
      - `tests/core/test_plan_navigator.py` - v2.1 네비게이터 테스트 (v3.0 navigator 테스트 작성 필요)

      **수정 (공통 기능 - v3.0으로 전환)**:
      - `tests/test_cli_plan.py` → v3.0 모델 import로 변경
      - `tests/test_integration_yaml_plan.py` → v3.0 YAML 픽스처 사용
      - `tests/test_integration_plan_filtering_completion.py` → v3.0 모델 사용
      - `tests/cli/test_task_commands.py` → `.sisyphus/tasks/test.yaml` 픽스처로 변경
      - `tests/cli/test_plan_commands.py` → v3.0 모델 사용

      **신규 작성**:
      - `tests/core/plans/test_navigator_v3.py` - v3.0 PlanNavigator 테스트

      **대상 파일**: 검색 결과에서 나온 테스트 파일들

   - [ ] 4.3 전체 테스트 실행 (첫 번째)

      **실행 명령어**: `uv run pytest --tb=short`

      **예상 결과**: 일부 실패 가능 (v2.1 의존 테스트)

      **실패 시**: 에러 메시지 분석 → 누락된 마이그레이션 식별

   - [ ] 4.4 실패 테스트 수정

      **실패 패턴 예시**:
      ```
      ImportError: cannot import name 'PlanNavigator' from 'sisyphus.core.plan_navigator'
      → 해당 테스트를 v3.0 기반으로 재작성 또는 삭제

      FileNotFoundError: ai-todolist.yaml not found
      → 픽스처를 .sisyphus/tasks/test.yaml로 변경
      ```

   - [ ] 4.5 전체 테스트 실행 (두 번째 - 회귀 테스트)

      **실행 명령어**: `uv run pytest -v`

      **예상 출력**: All tests pass

      **목표**: 기존 기능이 깨지지 않았는지 확인

   - [ ] 4.6 코드 커버리지 확인 (선택사항)

      **실행 명령어**: `uv run pytest --cov=sisyphus --cov-report=term-missing`

      **목표**: 새로 추가한 모델 클래스가 테스트되는지 확인

   - [ ] 4.7 커밋 (테스트 업데이트 완료 후)

      **커밋 명령어**:
      ```bash
      git add tests/
      git commit -m "test: update tests for v3.0 migration

Remove v2.1-dependent tests, update fixtures to use .sisyphus/tasks/.
Add v3.0 PlanNavigator tests.
All tests pass with v3.0 models and loaders.

Deleted:
- tests/utils/test_plan_types.py
- tests/core/test_plan_loader.py
- tests/core/test_plan_navigator.py

Updated:
- tests/test_cli_plan.py
- tests/test_integration_yaml_plan.py
- tests/cli/test_task_commands.py

Added:
- tests/core/plans/test_navigator_v3.py

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
      ```

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] `tests/` 디렉토리에 v2.1 import가 0개인가? (`rg "from sisyphus.utils.plan_types" tests/`)
      - [ ] v2.1 전용 테스트 파일이 삭제되었는가?
        - [ ] `tests/utils/test_plan_types.py` 삭제됨?
        - [ ] `tests/core/test_plan_loader.py` 삭제됨?
        - [ ] `tests/core/test_plan_navigator.py` 삭제됨?
      - [ ] v3.0 PlanNavigator 테스트가 추가되었는가? (`tests/core/plans/test_navigator_v3.py`)
      - [ ] `uv run pytest -v` → All tests pass?
      - [ ] 주요 기능 회귀 테스트 통과했는가?
        - [ ] `uv run pytest tests/cli/test_task_commands.py -xvs` → PASSED
        - [ ] `uv run pytest tests/cli/test_plan_commands.py -xvs` → PASSED
        - [ ] `uv run pytest tests/core/plans/test_models_v3.py -xvs` → PASSED
        - [ ] `uv run pytest tests/core/plans/test_navigator_v3.py -xvs` → PASSED
      - [ ] git commit 완료되었는가?


- [ ] 5. 문서 업데이트 - AGENTS.md 및 README

   **참조 소스 (REQUIRED)**:
   - 문서 파일: `projects/sisyphus-cli/AGENTS.md` (프로젝트 지식 베이스)
   - 참조 파일: `projects/sisyphus-cli/CLAUDE.md` (기존 문서 스타일)
   - v3.0 예시: `.sisyphus/tasks/2024/q4/deep-plan.yaml`

   - [ ] 5.1 AGENTS.md에서 v2.1 언급 제거

      **수정 파일**: `projects/sisyphus-cli/AGENTS.md`

      **검색 키워드**: `v2.1`, `plan_types`, `PlanNavigator`, `ai-todolist.yaml`

      **구현 세부사항**:
      - v2.1 관련 설명 제거
      - v3.0 확장 모델 설명 추가 (user_request, objectives, background, final_verification)
      - PlanNavigator v3.0 버전 설명 추가

   - [ ] 5.2 v3.0 확장 모델 문서 작성

      **추가 섹션**: AGENTS.md의 "v3.0 WorkPlan Format" 섹션

      **내용**:
      ```markdown
      ### v3.0 WorkPlan Format (Extended)

      v3.0 WorkPlan now includes required overview fields (all 8 fields from v2.1) for complete task context:

      - **user_request**: Original user request and additional requests
      - **objectives**: Core objective and detailed measurable goals
      - **background**: Current situation, reason for change, changes to make
      - **required_background**: Domain knowledge and references
      - **status**: Execution status and work mode
      - **workflow**: Dependency diagram and critical path
      - **success_vision**: User/business/technical criteria
      - **final_verification**: Overall verification checklist

      Example:
      ```yaml
      version: "3.0"
      work_plans:
        - id: "feature-x"
          name: "Add Feature X"
          user_request:
            original: "Add dark mode feature"
            created_at: "2025-11-06T00:00:00Z"
            additional: ["Use Tailwind CSS"]
          objectives:
            core: "Implement dark mode toggle"
            detailed:
              - goal: "Add theme switcher"
                measurable: "Toggle button in header"
          background:
            current_situation: "Light mode only"
            reason_for_change: "User requests"
            changes_to_make: "Add dark theme"
          todos: [...]
          final_verification:
            - id: "verify-1"
              title: "Dark mode works"
              category: "functional"
              description: "All pages render correctly in dark mode"
              bash:
                - execute: "npm test"
                  expected_exit_code: 0
      ```

      ### PlanNavigator v3.0

      PlanNavigator has been rewritten to use v3.0 models:
      - **Location**: `sisyphus/core/plans/navigator.py`
      - **Models**: Uses v3.0 WorkPlan and Todo
      - **current_task_id**: Accessed from plan.status.work_mode.current_task_id (v3.0 has status field)
      - **All features preserved**: DFS, CompletionReport, parallel groups
      ```

   - [ ] 5.3 "v2.1 → v3.0 완전 복구" 섹션 추가

      **검색 위치**: AGENTS.md 또는 CLAUDE.md에서 "v2.1 → v3.0 변경" 언급

      **구현 세부사항**:
      ```markdown
      ### v2.1 → v3.0 Field Migration Summary

      **Fully Restored** (모든 필드 복구):
      1. ✅ user_request - Original user request tracking
      2. ✅ objectives - Work goals and measurable outcomes
      3. ✅ background - Work context (current/reason/changes)
      4. ✅ required_background - Domain knowledge and file structure
      5. ✅ status - Execution state (started, progress, current_task_id)
      6. ✅ workflow - Dependency diagram and critical path
      7. ✅ success_vision - User/business/technical success criteria
      8. ✅ final_verification - Overall verification checklist

      **No Information Loss**: v3.0은 v2.1의 모든 필드를 포함하며, ai-todolist.md의 모든 섹션을 YAML로 표현 가능

      **Key Architectural Change**:
      - **WorkPlan.status**: YAML에 저장되는 실행 상태 (Standalone)
      - **StatusManager (.sisyphus/status.json)**: worktree → plan 매핑 테이블만 담당
      ```

   - [ ] 5.4 README 업데이트 (프로젝트 루트)

      **수정 파일**: `projects/sisyphus-cli/README.md`

      **구현 세부사항**:
      - v2.1 언급 제거
      - v3.0 확장 모델 간략 소개
      - PlanNavigator v3.0 언급

   - [ ] 5.5 예시 YAML 파일 추가 (선택사항)

      **신규 파일**: `examples/v3-extended-overview.yaml`

      **내용**: user_request, objectives, background, final_verification 포함한 완전한 예시

   - [ ] 5.6 커밋 (문서 업데이트 완료 후)

      **커밋 명령어**:
      ```bash
      git add projects/sisyphus-cli/AGENTS.md projects/sisyphus-cli/README.md examples/
      git commit -m "docs: update documentation for v3.0 extended model

Remove v2.1 references, add v3.0 overview fields documentation.
Include example YAML with user_request, objectives, background.
Update PlanNavigator section for v3.0 version.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
      ```

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] AGENTS.md에 "v2.1" 문자열이 0개인가? (`rg "v2\.1" projects/sisyphus-cli/AGENTS.md`)
      - [ ] AGENTS.md에 v3.0 확장 모델 설명이 추가되었는가?
      - [ ] AGENTS.md에 PlanNavigator v3.0 섹션이 추가되었는가?
      - [ ] "손실된 정보" 섹션이 업데이트되었는가? (8개 필드 전체 복구, 단순화 없음)
      - [ ] README.md가 업데이트되었는가?
      - [ ] 예시 YAML 파일이 추가되었는가? (선택사항)
      - [ ] git commit 완료되었는가?
      - [ ] 문서가 읽기 쉽고 명확한가? (수동 검토)


# 성공 비전

## 사용자 관점에서의 성공

- **작업 맥락 파악 용이**: v3.0 YAML 파일을 열면 user_request, objectives, background 섹션으로 "왜 이 작업을 하는지" 즉시 이해
- **v2.1 혼란 제거**: v2.1 관련 파일이 없어 혼란 없음
- **`.sisyphus/tasks/` 일관성**: 모든 명령어가 `.sisyphus/tasks/` 기반으로 동작
- **PlanNavigator 기능 유지**: 현재 작업 추적 기능 정상 동작

## 비즈니스 관점에서의 성공

- **유지보수성 향상**: v2.1/v3.0 이중 구조 제거로 코드 단순화
- **마이그레이션 완료**: v3.0 전용 시스템으로 안정화

## 기술적 성공 기준

- [ ] 모든 테스트 통과: `uv run pytest` → 100% pass
- [ ] 타입 체크 통과: `uv run basedpyright` → 0 errors
- [ ] 린트 통과: `uv run ruff check` → 0 errors
- [ ] v2.1 파일 완전 제거: `sisyphus/utils/plan_types.py`, `sisyphus/core/plan_loader.py`, `sisyphus/core/plan_navigator.py` 삭제 확인
- [ ] v3.0 PlanNavigator 생성: `sisyphus/core/plans/navigator.py` 존재 확인
- [ ] `ai-todolist.yaml` 하드코딩 0개: `rg "ai-todolist.yaml" sisyphus/` → No matches

# 최종 작업 검증 체크리스트

- [ ] 1. **기능 동작 확인**
   - [ ] v3.0 YAML 파일에 오버뷰 필드 추가 가능
     ```bash
     # 테스트 YAML 생성
     cat > .sisyphus/tasks/test.yaml <<EOF
     version: "3.0"
     metadata:
       created_at: "2025-11-06T00:00:00Z"
     work_plans:
       - id: "test"
         name: "Test Plan"
         user_request:
           original: "Test feature"
           created_at: "2025-11-06T00:00:00Z"
           additional: []
         objectives:
           core: "Test core objective"
           detailed: []
         background:
           current_situation: "No test"
           reason_for_change: "Testing"
           changes_to_make: "Add test"
         todos:
           - id: "1"
             title: "Test task"
             status: "pending"
         final_verification: []
     EOF

     # 로드 테스트
     python -c "
     import anyio
     from sisyphus.core.plans.loader import load_plan
     from pathlib import Path
     plan = anyio.run(load_plan, Path('.sisyphus/tasks/test.yaml'))
     assert plan.work_plans[0].user_request.original == 'Test feature'
     print('✓ v3.0 extended model works')
     "
     ```

   - [ ] PlanNavigator v3.0이 정상 동작
     ```bash
     python -c "
     from sisyphus.core.plans.navigator import PlanNavigator
     from sisyphus.core.plans.models import WorkPlan, Todo, TodoStatus

     work_plan = WorkPlan(
         id='test',
         name='Test',
         todos=[
             Todo(id='1', title='Task 1', status=TodoStatus.pending),
             Todo(id='2', title='Task 2', status=TodoStatus.pending),
         ]
     )
     nav = PlanNavigator(work_plan, current_task_id='1')
     assert nav.get_current_task().id == '1'
     assert nav.get_next_task('1').id == '2'
     print('✓ PlanNavigator v3.0 works')
     "
     ```

   - [ ] task 명령어가 `.sisyphus/tasks/` 기반으로 동작
     ```bash
     uv run sisyphus task current
     # 에러 없이 실행되거나, "작업이 시작되지 않았습니다" 메시지 출력
     ```

- [ ] 2. **잘못된 구현 방지**
   - [ ] v2.1 파일이 완전히 삭제되었는지 확인
     ```bash
     test ! -f sisyphus/utils/plan_types.py && echo "✓ plan_types.py deleted"
     test ! -f sisyphus/core/plan_loader.py && echo "✓ plan_loader.py deleted"
     test ! -f sisyphus/core/plan_navigator.py && echo "✓ plan_navigator.py deleted (v2.1)"
     test -f sisyphus/core/plans/navigator.py && echo "✓ navigator.py created (v3.0)"
     ```

   - [ ] `ai-todolist.yaml` 하드코딩이 없는지 확인
     ```bash
     if ! rg "ai-todolist.yaml" sisyphus/ > /dev/null 2>&1; then
       echo "✓ No ai-todolist.yaml hardcoding"
     else
       echo "✗ Found ai-todolist.yaml references:"
       rg "ai-todolist.yaml" sisyphus/
     fi
     ```

- [ ] 3. **범위 준수 확인**
   - [ ] 계획과 다르게 구현되지 않았는지 확인
     - v3.0 모델에 8개 필드 전체 추가했는가? (user_request, objectives, background, required_background, status, workflow, success_vision, final_verification)
     - 모든 필드가 REQUIRED로 정의되었는가? (Optional 처리 없음)
     - PlanNavigator가 v3.0 기반으로 재작성되었는가?

   - [ ] 과도하게 구현되지 않았는지 확인
     - 추가 기능 없이 계획된 작업만 완료했는가?

- [ ] 4. **기존 기능 회귀 테스트**
   - [ ] v3.0 기본 기능이 깨지지 않았는지 확인
     ```bash
     # 기존 v3.0 YAML (오버뷰 필드 없음) 로드 테스트
     uv run pytest tests/core/plans/test_loader_v3.py -xvs
     # 예상: PASSED (Optional 필드라 기존 YAML 호환)
     ```

   - [ ] CLI 명령어가 정상 동작하는지 확인
     ```bash
     uv run sisyphus plan lint .sisyphus/tasks/
     # 예상: 정상 실행 또는 "No errors"

     uv run sisyphus plan graph .sisyphus/tasks/
     # 예상: 그래프 출력 또는 에러 없음
     ```

   - [ ] PlanNavigator 기능이 유지되는지 확인
     ```bash
     # task 명령어 (PlanNavigator 의존)
     uv run sisyphus task show 1
     # 예상: 작업 정보 출력 또는 에러 없음
     ```
