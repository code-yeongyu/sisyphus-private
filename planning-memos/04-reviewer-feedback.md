# Plan-Reviewer 피드백 및 개선 계획

**작성일**: 2025-11-01
**판정**: REJECT
**주요 문제**: 핵심 구현 세부사항 모호함

---

## 주요 거부 사유

### 1. Pydantic 모델 검증 로직 불명확 (태스크 1.1)
**문제**: uri와 inline 중 하나만 필수, 둘 다 있으면 오류 구현 방법 부재
**해결**: 모델 스켈레톤 제공

```python
class ReferenceItem(BaseModel):
    ref_id: str | None = None
    uri: str | None = None
    inline: str | None = None

    @model_validator(mode='after')
    def validate_exclusivity(self) -> Self:
        if self.uri and self.inline:
            raise ValueError("uri와 inline은 동시에 사용할 수 없습니다")
        if not self.uri and not self.inline:
            raise ValueError("uri 또는 inline 중 하나는 필수입니다")
        return self

class Todo(BaseModel):
    id: str
    title: str
    description: str | None = None
    status: TodoStatus
    children: list["Todo"] | None = None  # 1레벨만
    references: list[ReferenceItem] = []
    verification_spec: list[VerificationItem] = []

class WorkPlan(BaseModel):
    name: str
    depends_on: list[str] = []  # 플랜 ID (파일명 제외)
    todos: list[Todo]
```

### 2. CLI 마이그레이션 전략 부재 (태스크 3.6)
**문제**: 995줄 cli.py의 기존 로직 처리 방법 불명확
**해결**: 매핑 테이블 제공

```
기존 → 신규 매핑:
- plan_app.get(task, --id) → task_app.show(id)
- plan_app.get(task, --current) → task_app.current()
- plan_app.get(task, --next) → task_app.next()
- execute_phase_app.get_overview() → plan_app.overview()
- execute_phase_app.continue_work() → task_app.continue()
- execute_phase_app.bash_verify() → task_app.verify(bash)
- execute_phase_app.llm_verify() → task_app.verify(llm mark)
- execute_phase_app.manual_verify() → task_app.verify(manual mark)
- verify_phase_app.* → (execute_phase_app과 중복, 삭제)

유지:
- plan_app.lint() → plan_app.lint()

신규:
- plan_app.init()
- plan_app.graph()
- plan_app.convert_legacy()
- task_app.verify(status)
```

### 3. 검증 시나리오 불완전 (검증 2, 7)
**문제**: llm 검증 시 입력 데이터 및 기대 출력 불명확
**해결**: 구체적인 YAML 예시

```yaml
# tests/fixtures/plans/circular.yaml
version: "3.0"
metadata:
  format_version: "3.0"
work_plans:
  - id: plan-a
    name: "Plan A"
    depends_on: [plan-b]
    todos: []
  - id: plan-b
    name: "Plan B"
    depends_on: [plan-a]
    todos: []

# 기대 출력:
# Error: Circular dependency detected: plan-a → plan-b → plan-a
```

### 4. 명령어 실행 예시 추가 (태스크 3.4)
**해결**: UX 시나리오

```bash
$ uv run sisyphus task verify bash
━━━ 검증 1/8: Phase 1 완료 ━━━
카테고리: Phase 1
설명: v3 스키마 정의, 로더 재구성

명령어: pytest tests/core/plans tests/core/status
실행 중...
✓ 성공 (exit_code=0)

증거 입력 (선택): [Enter로 건너뛰기]
> test output saved to logs/

다음 검증으로 이동합니다...
```

### 5. 워크트리 캐시 전략 명시 (태스크 5.2)
**해결**: 캐시 구현 명세

```python
class StatusManager:
    _worktree_cache: dict[Path, list[Path]] | None = None
    _cache_timestamp: float | None = None
    CACHE_TTL = 60.0  # 60초

    @classmethod
    def detect_worktree(cls) -> Path:
        # 캐시가 만료되었거나 없으면 재탐색
        if cls._is_cache_expired():
            cls._refresh_worktree_cache()
        return cls._get_current_worktree()

    @classmethod
    def _is_cache_expired(cls) -> bool:
        if cls._cache_timestamp is None:
            return True
        return time.time() - cls._cache_timestamp > cls.CACHE_TTL
```

---

## 추가 개선사항

### 버전 필드 위치 명확화
```yaml
# YAML 최상위 레벨
version: "3.0"  # 또는 metadata.format_version?

# 제안: 최상위 version 필드 사용
version: "3.0"
metadata:
  created_at: "2025-11-01T..."
  updated_at: "2025-11-01T..."
```

### discover_plan_files() 탐색 로직
```python
def discover_plan_files(root: Path) -> list[Path]:
    """
    .sisyphus/tasks/ 하위의 모든 YAML 파일 탐색

    - 패턴: *.yaml, *.yml
    - 재귀: Yes (하위 디렉토리 포함)
    - 제외: .gitignore 준수, 숨김 파일 제외
    """
    return list(root.glob("**/*.y*ml"))
```

### 성능 벤치마크 기준
```python
# 절대 성능 기준 (v2.1 없어도 측정 가능)
PERFORMANCE_TARGETS = {
    "load_100_todos": 100,  # ms
    "graph_50_plans": 500,  # ms
    "lint_large_plan": 200,  # ms
}
```

---

## 수정 계획

1. ai-todolist.md 재작성
2. Phase 1 태스크에 Pydantic 모델 스켈레톤 추가
3. Phase 3 태스크에 CLI 마이그레이션 매핑 추가
4. 각 검증 항목에 구체적인 입력/출력 예시 추가
5. Phase 5 태스크에 캐시 전략 명시
6. 통합 테스트 시나리오 구체화
