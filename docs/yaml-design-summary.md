# YAML Task Planning System - Design Summary

## TL;DR

YAML 기반 작업 계획 시스템 설계:
- **그래프 구조**: DAG (순환 참조 방지), 포인터 기반 참조
- **중첩 서브태스크**: 3단계 깊이, 외부 파일 참조 가능
- **프로그래머틱 검증**: 7가지 타입 (command, http, prompt, composite, etc.)
- **크리티컬 태스크**: 런타임 발견 이슈, 자동 루프 연장
- **자동 분할**: 30개 이상 or 3단계 깊이 초과 시 분할
- **정적 분석**: 그래프 분석, 크리티컬 패스, 병렬화 기회

## 핵심 설계 결정

### 1. 포인터 기반 참조 (Pointer-Based References)

**결정**: Task ID를 통한 간접 참조 사용

```yaml
tasks:
  - id: "t1"
    depends_on: ["t2", "t3"]  # ID로 참조
    blocks: ["t4"]
```

**이유**:
- ✅ **순환 참조 탐지 가능**: 그래프 알고리즘으로 cycle detection
- ✅ **파일 분할 용이**: 다른 파일의 task 참조 가능
- ✅ **직렬화 간단**: YAML로 직접 표현 가능
- ✅ **변경 전파 없음**: Task 내용 변경해도 참조 유지
- ❌ **깨진 참조 가능**: Validation 단계 필수

**대안 고려**:
- ~~Object embedding~~: 순환 참조 불가능, 파일 분할 어려움
- ~~Path-based~~: 리팩토링 시 참조 깨짐

### 2. 양방향 관계 표현 (Bidirectional Links)

**결정**: `depends_on` (전제 조건) + `blocks` (차단 대상)

```yaml
- id: "t1"
  depends_on: []      # t1은 아무것도 의존하지 않음
  blocks: ["t2"]      # t1이 완료되어야 t2 시작 가능

- id: "t2"
  depends_on: ["t1"]  # t2는 t1에 의존
  blocks: []
```

**이유**:
- ✅ **명시적 관계**: 양쪽에서 관계 확인 가능
- ✅ **검증 용이**: 양방향 일치 확인으로 무결성 보장
- ✅ **쿼리 최적화**: "이 task가 완료되면 뭐가 시작 가능한가?" 빠르게 답변
- ⚠️ **중복성**: 정보가 중복 저장됨 (트레이드오프)

**대안 고려**:
- ~~`depends_on`만 사용~~: 역방향 쿼리 시 전체 순회 필요
- ~~계산된 필드~~: 파싱 시 자동 생성 (복잡도 증가)

### 3. 하위 태스크 구조 (Nested Subtasks)

**결정**: Inline + External Reference 혼합

```yaml
tasks:
  - id: "t1"
    # 간단한 경우: inline
    subtasks:
      - id: "t1.1"
        title: "Simple subtask"

  - id: "t2"
    # 복잡한 경우: external file
    subtasks_ref:
      file: "tasks/t2_subtasks.yaml"
      task_count: 50
```

**이유**:
- ✅ **유연성**: 간단한 경우 편리, 복잡한 경우 분리
- ✅ **가독성**: 작은 파일 유지
- ✅ **재사용**: 같은 subtask 구조 여러 곳에서 참조 가능
- ✅ **버전 관리**: 대형 subtask tree 독립적 관리

**계층 ID 규칙**: `t1.1.1.2` (부모.자식.손자.증손)

**제한사항**:
- 최대 깊이: 3단계 (설정 가능)
- 이유: 너무 깊으면 복잡도 폭발, 병렬화 불가능

### 4. 프로그래머틱 검증 (Programmatic Verification)

**결정**: 7가지 검증 타입 + 조합

```yaml
verification:
  type: "composite"
  operator: "AND"
  checks:
    - type: "command"
      command: "pytest"
      expected_exit_code: 0

    - type: "http"
      method: "POST"
      url: "http://localhost:8000/api/test"
      expected_status: 200

    - type: "prompt"
      prompt: "코드 품질 확인..."
      llm_check: true

    - type: "coverage"
      min_coverage: 80

    - type: "static_analysis"
      tools: ["mypy", "ruff", "bandit"]
```

**검증 타입**:
1. **manual**: 사람이 체크 (체크박스)
2. **command**: CLI 명령 실행, exit code 확인
3. **http**: REST API 호출, response 검증
4. **prompt**: LLM 기반 semantic 검증
5. **subtasks_complete**: 모든 하위 태스크 완료
6. **composite**: 여러 검증 조합 (AND/OR)
7. **coverage**: 코드 커버리지 임계값
8. **static_analysis**: 린터, 타입 체커 등

**이유**:
- ✅ **자동화**: 반복 작업 자동 검증
- ✅ **일관성**: 사람마다 다른 기준 제거
- ✅ **추적성**: 검증 결과 기록
- ✅ **확장성**: 새 타입 추가 용이

**Composite Verification**:
```yaml
# AND: 모두 통과해야 함 (엄격)
operator: "AND"

# OR: 하나만 통과하면 됨 (유연)
operator: "OR"

# Weighted: 점수 기반 (0-1)
checks:
  - type: "command"
    weight: 0.5
  - type: "prompt"
    weight: 0.3
  - type: "coverage"
    weight: 0.2
```

### 5. 크리티컬 태스크 시스템 (Critical Tasks)

**결정**: 런타임 발견 이슈를 별도 섹션에 추가

```yaml
critical_tasks:
  - id: "ct1"
    title: "FIX: SQL injection vulnerability"
    priority: "critical"
    severity: "high"
    security_impact: true
    blocks_release: true

    discovered_at: "2025-10-21T10:30:00Z"
    discovered_by: "agent_architect"
    discovery_method: "code_review"

    related_task: "t3"  # 원래 task와 링크

    verification:
      type: "composite"
      # ... 검증 로직
```

**이유**:
- ✅ **우선순위 관리**: Critical 이슈 명시적 추적
- ✅ **루프 연장**: `should_continue_loop()` 자동 트리거
- ✅ **컨텍스트 보존**: 발견 시점, 방법, 담당자 기록
- ✅ **릴리즈 블로킹**: `blocks_release` 플래그로 명시

**트리거 조건**:
- Security vulnerability 발견
- Major bug 발견
- Architecture issue 발견
- Performance blocker 발견

**처리 흐름**:
```
Verify Phase
  ↓
Security Issue 발견
  ↓
Critical Task 생성 (ct1)
  ↓
Execute Phase 재실행
  ↓
ct1 수정
  ↓
Verify Phase
  ↓
ct1 검증 통과
  ↓
Continue
```

### 6. 자동 분할 (Auto-Splitting)

**결정**: 임계값 기반 자동 파일 분할

```yaml
config:
  auto_split:
    enabled: true
    max_tasks: 30        # Task 수
    max_depth: 3         # 중첩 깊이
    max_file_size_kb: 10 # 파일 크기
    strategy: "milestone" # 분할 전략
```

**분할 전략**:

1. **By Milestone** (추천)
   ```
   plan.yaml
   ├── tasks/milestone_m1.yaml  (t1, t2)
   ├── tasks/milestone_m2.yaml  (t3, t4)
   └── tasks/milestone_m3.yaml  (t5, t6)
   ```

2. **By Size**
   ```
   plan.yaml
   ├── tasks/part_1.yaml  (t1-t10)
   ├── tasks/part_2.yaml  (t11-t20)
   └── tasks/part_3.yaml  (t21-t30)
   ```

3. **By Complexity** (DAG depth)
   ```
   plan.yaml
   ├── tasks/level_0.yaml  (root tasks)
   ├── tasks/level_1.yaml  (1단계 의존)
   └── tasks/level_2.yaml  (2단계 의존)
   ```

**이유**:
- ✅ **가독성**: 큰 파일 → 작은 파일들
- ✅ **병렬 작업**: 팀원별 다른 파일 수정
- ✅ **버전 관리**: Merge conflict 감소
- ✅ **로딩 성능**: 필요한 부분만 로딩

**참조 무결성 유지**:
```yaml
# Main file
tasks:
  - id: "t1"
    blocks: ["t2"]  # t2는 다른 파일에 있어도 OK

# Validator가 모든 파일 로드 후 검증
validator.validate()
  ↓ Load all split files
  ↓ Build complete graph
  ↓ Check references
  ↓ Report broken links
```

### 7. 그래프 분석 (Graph Analysis)

**결정**: NetworkX 기반 DAG 분석

```python
class GraphAnalyzer:
    def __init__(self, plan: TaskPlan):
        self.graph = self._build_graph()  # nx.DiGraph

    def has_cycles(self) -> bool:
        """순환 참조 탐지"""

    def critical_path(self) -> list[str]:
        """가장 긴 의존 체인 (병목)"""

    def parallel_groups(self) -> list[list[str]]:
        """병렬 실행 가능한 task 그룹"""

    def topological_sort(self) -> list[str]:
        """유효한 실행 순서"""
```

**분석 결과 활용**:

1. **Critical Path**: 프로젝트 완료 최소 시간
   ```
   t1 → t2 → t3 → t5
   (2h + 3h + 4h + 5h = 14h)
   ```

2. **Parallel Execution**: 동시 실행 가능
   ```
   Level 0: [t1]              (2h)
   Level 1: [t2]              (3h)
   Level 2: [t3, t4]          (4h)  ← 병렬 가능!
   Level 3: [t5]              (5h)

   Total: 14h (순차) → 14h (병렬, 이 경우 병렬화 효과 없음)
   ```

3. **Cycle Detection**: 무한 루프 방지
   ```
   t1 → t2 → t3 → t1  ❌ ERROR
   ```

**이유**:
- ✅ **실행 계획**: 최적 실행 순서 자동 계산
- ✅ **병렬화**: 에이전트 동시 실행 가능성 파악
- ✅ **시간 예측**: Critical path로 완료 시간 추정
- ✅ **병목 식별**: 가장 오래 걸리는 경로 파악

### 8. Feedback History (Verify Agent)

**결정**: Verify agent의 피드백을 구조화하여 저장

```yaml
feedback_history:
  - iteration: 1
    timestamp: "2025-10-21T10:00:00Z"
    agent: "agent_architect"
    session_id: "sess_xxx"

    feedback: |
      **ITERATION 1 FEEDBACK**

      ## Critical Issues Found (2)
      1. SQL injection in t3.2
      2. Missing rate limiting

      ## Recommendations
      - Fix ct1 immediately
      - Add tests for ct2

      **VERDICT:** REWORK REQUIRED

    tasks_affected: ["t3"]
    critical_tasks_created: ["ct1", "ct2"]
    requires_rework: true
```

**이유**:
- ✅ **히스토리 추적**: 모든 iteration의 피드백 기록
- ✅ **학습 데이터**: 향후 LLM 학습에 활용 가능
- ✅ **디버깅**: 왜 이 decision을 했는지 확인
- ✅ **루프 제어**: `requires_rework` 플래그로 다음 action 결정

**Sisyphus 통합**:
```python
# ExecutionLoop에서 사용
async def _verify_phase(self) -> VerifyFeedback:
    feedback = await self.verify_agent.run(context)

    # Add to history
    self.validator.plan.feedback_history.append(feedback)

    # Handle critical tasks
    for ct in feedback.critical_tasks_created:
        await self.validator.add_critical_task(ct)

    # Check if should continue
    if feedback.requires_rework:
        # Execute phase again
        return await self._execute_phase()
```

### 9. Metrics & Progress Tracking

**결정**: 실시간 메트릭 자동 계산

```yaml
metrics:
  # Task counts
  total_tasks: 6
  completed_tasks: 2
  in_progress_tasks: 1
  pending_tasks: 3

  # Critical tasks
  critical_tasks_total: 2
  critical_tasks_resolved: 1

  # Time tracking
  estimated_total_hours: 20.0
  actual_total_hours: 8.5
  time_efficiency: 0.425  # actual/estimated

  # Progress
  completion_percentage: 33.3
  on_track: true
  projected_completion: "2025-10-22T18:00:00Z"

  # Quality
  verify_iterations: 2
  critical_issues_found: 2
  critical_issues_resolved: 1
  tests_passing: true
  coverage_percentage: 87.5
```

**이유**:
- ✅ **가시성**: 현재 진행 상황 한눈에 파악
- ✅ **예측**: 완료 시점 예측
- ✅ **최적화**: 비효율 영역 식별
- ✅ **리포팅**: Stakeholder에게 진행도 보고

## 시스템 통합

### Sisyphus ExecutionLoop 통합

```python
# 기존 (Markdown)
validator = TaskValidator("ai-todolist.md")
while not validator.is_complete():
    await execute_phase()
    await verify_phase()

# 새로운 (YAML)
validator = YAMLTaskValidator("tasks/plan.yaml")
while await validator.should_continue_loop():
    # Get executable tasks
    tasks = await validator.get_next_tasks()

    # Parallel execution
    if plan.config.agent.parallel_execution:
        await execute_parallel(tasks)
    else:
        await execute_sequential(tasks)

    # Verify
    feedback = await verify_phase()

    # Handle critical tasks
    for ct in feedback.critical_tasks_created:
        await validator.add_critical_task(ct)
```

### Migration Path

**Phase 1**: Parallel Support (3 weeks)
- YAMLTaskValidator 구현
- Markdown + YAML 동시 지원
- CLI flag: `--plan-format yaml`

**Phase 2**: Migration Tool (1 week)
```bash
sisyphus convert ai-todolist.md --output tasks/plan.yaml
```

**Phase 3**: Deprecation (2 weeks)
- Markdown format deprecated
- Documentation 업데이트
- Migration guide

**Phase 4**: YAML Only (1 week)
- Markdown 코드 제거
- 클린업

## 장점 (Benefits)

### 1. 확장성 (Scalability)
- ✅ 프로젝트 크기 무제한 (auto-split)
- ✅ 팀 규모 확장 가능 (파일 분할)
- ✅ 복잡도 관리 (계층 구조)

### 2. 자동화 (Automation)
- ✅ 검증 자동화 (7가지 타입)
- ✅ 병렬 실행 (그래프 분석)
- ✅ 진행도 추적 (자동 metrics)

### 3. 품질 (Quality)
- ✅ 일관된 검증 기준
- ✅ Critical issue 추적
- ✅ 피드백 루프

### 4. 가시성 (Visibility)
- ✅ 실시간 진행도
- ✅ 병목 지점 파악
- ✅ 완료 시점 예측

### 5. 협업 (Collaboration)
- ✅ 명확한 의존성
- ✅ 파일 분할로 conflict 감소
- ✅ 히스토리 추적

## 단점 & 트레이드오프

### 1. 복잡도 증가
- ❌ Markdown보다 학습 곡선 가파름
- ❌ 더 많은 코드 필요
- ✅ **완화**: 템플릿, 예제, 문서

### 2. 파일 크기
- ❌ YAML이 Markdown보다 verbose
- ✅ **완화**: auto-split으로 작은 파일 유지

### 3. 편집 경험
- ❌ Markdown이 더 직관적
- ❌ YAML 문법 오류 가능성
- ✅ **완화**: Schema validation, IDE support

### 4. 마이그레이션 비용
- ❌ 기존 프로젝트 변환 필요
- ✅ **완화**: 자동 변환 도구, 단계적 마이그레이션

## 다음 단계 (Next Steps)

### 1. 프로토타입 구현 (2 weeks)
- [ ] TaskPlan 데이터 클래스
- [ ] YAML parser/writer
- [ ] GraphAnalyzer
- [ ] VerificationEngine (기본 타입만)
- [ ] YAMLTaskValidator

### 2. 기본 통합 (1 week)
- [ ] ExecutionLoop 수정
- [ ] CLI 명령어 추가
- [ ] 테스트 작성

### 3. 검증 시스템 (2 weeks)
- [ ] 7가지 검증 타입 구현
- [ ] Composite verification
- [ ] 캐싱 시스템

### 4. 자동 분할 (1 week)
- [ ] PlanSplitter 구현
- [ ] 3가지 전략
- [ ] 병합 로직

### 5. 도구 & 문서 (1 week)
- [ ] Migration tool (md → yaml)
- [ ] Visualization tool (graph PNG)
- [ ] User documentation
- [ ] API documentation

**Total**: ~7 weeks for MVP

## 결론

이 YAML 기반 설계는 Sisyphus를 **확장 가능하고**, **자동화된**, **품질 중심의** 시스템으로 발전시킵니다.

**핵심 가치**:
1. 📊 **그래프 기반 사고**: Task 간 관계를 명시적으로 표현
2. 🤖 **자동화 우선**: 프로그래머틱 검증으로 반복 작업 제거
3. 🔍 **가시성**: 실시간 진행도, 병목, 예측
4. 🛡️ **품질 게이트**: Critical task로 품질 보장
5. 🔧 **유연성**: 다양한 프로젝트 크기와 복잡도 지원

**트레이드오프**:
- 초기 학습 곡선 vs 장기 생산성
- 복잡도 증가 vs 기능 향상
- 파일 크기 증가 vs 명확성

**권장 사항**:
- 소규모 프로젝트 (<10 tasks): Markdown 계속 사용
- 중대형 프로젝트 (>10 tasks): YAML 전환 고려
- 팀 프로젝트: YAML 강력 권장
- 장기 프로젝트: YAML 필수

---

**문서 작성**: 2025-10-21
**버전**: 1.0.0
**상태**: Design Complete, Ready for Implementation
