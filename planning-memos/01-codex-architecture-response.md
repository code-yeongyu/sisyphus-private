# Codex 아키텍처 설계 제안 (1차)

**작성일**: 2025-11-01
**출처**: Codex GPT-5

---

## 모듈 구조 제안

### CLI 레이어 분리
- `sisyphus/cli/`에 `__init__.py`, `plan.py`, `task.py`, `reset.py`, `common.py` 배치
- 기존 995줄 `cli.py`는 서브커맨드 정의만 남기는 얇은 엔트리로 축소

### 코어 도메인 로직 정리

#### Plans 관련
- `sisyphus/core/plans/loader.py`: 단일 YAML 로딩 + 버전 판별 + 스키마 매핑
- `sisyphus/core/plans/parser_v3.py`: pydantic 모델, 레거시 매핑, 인라인/참조 처리
- `sisyphus/core/plans/dependencies.py`: 그래프 구성, 순환/고립/존재 검증, 토폴로지 정렬
- `sisyphus/core/plans/references.py`: ref_id 인덱싱, 인라인 라벨링, 단일 책임 분리

#### Status 관리
- `sisyphus/core/status/manager.py`: `status.json` CRUD + 파일 잠금(`anyio` 기반) + worktree key 관리

#### Graph 렌더링
- `sisyphus/core/graph/renderer.py`: 멀티 렌더러(ASCII, Mermaid, PNG) 전략 패턴으로 분리

#### 변환 및 내비게이션
- `sisyphus/core/converters/legacy.py`: v2.1 → v3.0 변환 파이프라인
- `sisyphus/core/tasks/navigator.py`: current/next/continue 해석, 검증 워크플로 orchestration

#### 공통
- 공용 예외는 `sisyphus/core/exceptions.py`로 이동

### 테스트
- 테스트용 리소스는 `.sisyphus/resources/` 패키지화하여 fixtures에서 직접 사용

---

## 의존성 그래프 설계

### 내부 표현
- `PlanGraph = nx.DiGraph` 수준의 기능을 직접 구현
- 노드: 절대경로(최종) + 메타데이터
- 엣지: `depends_on` → 종속 대상

### 로딩 알고리즘
1. 파일 스캔 후 파서에서 metadata.format_version 읽어 자동 분기
2. v3.0이면 `PlanModelV3`, v2.1이면 `LegacyPlanAdapter`가 공통 인터페이스로 변환
3. 모든 노드 삽입 후 DFS/BFS로 파일 존재 확인, 스키마 오류 수집

### 순환 검출
- 색상마킹 DFS 또는 Kahn 실패 검출
- 실패 시 사이클 경로를 반환해야 디버깅 용이

### 고립/미도달 검출
- 루트 후보 = 의존받지 않는 플랜
- 거기서부터 BFS
- 방문 못한 노드는 경고

### 토폴로지 출력
- Kahn 알고리즘 결과 리스트
- 병렬 그룹(`parallel_group`)은 레벨별 리스트로 유지

### 그래프 시각화: Strategy 패턴
- `AsciiRenderer`: 박스드로잉, Graphviz 의존 없이
- `MermaidRenderer`: `graph TD` + 노드 ID 해시
- `PngRenderer`: 내부적으로 `graphviz` 사용 (있으면), 없으면 친절히 안내

---

## status.json 운용

### 구조
```json
{
  "worktrees": [
    {
      "worktree_path": "...",
      "current_plan": "...",
      "updated_at": "..."
    }
  ]
}
```

### 키 결정
- `Path.resolve()` + `git rev-parse --show-toplevel` 기반
- 워크트리 존재 여부 `git worktree list --porcelain`에서 캐싱

### 동시성
- `anyio.Lock` + `filelock` 대체 없이 `anyio.open_file` + 임시파일 쓰기 → atomic rename

### API
- `StatusManager.get(worktree)`
- `set_current(plan)`
- `clear()`
- `list_all()`

### 캐시
- in-memory + mtime 체크로 재로딩 최소화

### 에러 처리
- 워크트리 미등록, 손상 JSON → 백업 복구 (기존 SessionStore 패턴 재사용)

---

## 레퍼런스 시스템

### 모델
- `ReferenceItemInline(text: str)`
- `ReferenceItemRef(ref_id: str)`

### 파서
- 하단 섹션 먼저 인덱싱
- 상단 todos 처리 시 유효성 검사

### Linter 규칙
- ref_id 누락/중복 → 오류
- 인라인 텍스트는 길이/URL 패턴 검사
- 타 플랜으로 참조? 금지 또는 추후 확장; 우선은 동일 플랜 제한 권장

### 순환 의존
- 레퍼런스끼리는 텍스트라 순환 개념 없음
- 대신 depends_on 기반으로만 순환 평가

---

## Task 커맨드 리팩터링

### Typer 앱 분리
- `plan_app = typer.Typer()` (lint, overview, init, graph, convert-legacy)
- `task_app = typer.Typer()` (show/current/next/continue/verify …)
- 루트 CLI는 두 앱만 마운트

### 공통 코드
- 공통 옵션/출력은 `cli/common.py`에서 헬퍼 제공 (Rich Table, JSON 출력 등)
- 비즈니스 로직 호출은 모두 `core/` 모듈로 이동 → CLI는 thin wrapper

### task verify 계열
- sequential enforcement를 `TaskNavigator.next_unverified()`에서 제공
- `--evidence`는 파일 경로/텍스트 인풋 처리
- 저장 위치 `.sisyphus/tasks/<plan>.evidence/` 고려

### 레거시 명령 처리
- 기존 실행/검증 커맨드는 완전히 제거
- alias 제공 시 deprecated 경고 추가 가능

---

## 테스트 전략

### 파일 구조
- `tests/fixtures/`에 `.sisyphus/resources/spec-document-example.yaml` 복사하지 말고 symlink or loader로 참조

### 기능별 테스트
- `test_plan_loader_v3.py`: 버전 감지, description/references 파싱
- `test_dependency_graph.py`: 순환/고립/토폴로지 케이스 (fixtures/graph/*.yaml)
- `test_status_manager.py`: temp dir에서 locking, concurrent writes (anyio pytest)
- `test_cli_task.py`: Typer CliRunner로 커맨드 플로 검증, temp `.sisyphus` 구성
- `test_legacy_converter.py`: v2.1 샘플 → v3.0 기대 YAML 비교

### 테스트 파일 관리
- 테스트 파일 생성은 `tmp_path / ".sisyphus"` 사용
- cleanup 자동화
- PNG 렌더링은 optional dependency → `pytest.importorskip("graphviz")`

---

## 마이그레이션 경로

### 버전 감지
- 로더에서 `metadata.format_version` 읽고:
  - `None` 또는 `<3.0`: 레거시 → `LegacyPlanAdapter convert()` 호출
  - CLI `plan convert-legacy`는 명시적 파일/디렉터리 입력, 결과 `tasks/`으로 출력

### Linter 처리
- lint 시 v2.1 감지 → "사용 중지, sisyphus plan convert-legacy 사용" 오류
- `plan lint`는 v3.0만 지원
- v2.1은 에러 메시지에서 변환 가이드 제공

### 파일 이동
- 기존 루트 파일 이동: `plan init`가 `.sisyphus/` 디렉토리 생성
- 필요 시 `--migrate-existing` 옵션으로 자동 이동

### status.json 초기화
- `.sisyphus/status.json` 없으면 초기화
- 기존 단일 파일 구조 감지 시 자동 변환 기능

---

## 주의해야 할 함정

### 경로 처리
- 워크트리 경로 상대/절대 혼선 → 내부는 절대경로 저장, 출력 시 상대 표시

### 병렬 그룹과 의존성
- 병렬 그룹과 depends_on 충돌: 동일 병렬 그룹 내에서 교차 의존 금지 → lint rule 필요

### 외부 의존성
- PNG 렌더링 실패 시 사용자에게 graphviz 설치 안내 (자동 설치 금지)
- 제한된 네트워크 환경 → 외부 의존성 (graphviz) optional 처리

### 동시성
- 다중 프로세스에서 status.json race → 반드시 atomic write

### 레거시 변환
- 레거시 변환 시 `references` 포맷 손실 방지
- 가이드 없는 텍스트는 인라인으로 변환

### CLI 변경
- CLI 하위 명령 이름 변경 시 auto-complete 깨짐
- Typer `hidden=True` 경고 alias로 전환 기간 제공 가능

### 성능
- 대형 YAML (수백 todo) → 파서/검증 성능 고려
- 싱글 패스 검증, 중복 순회 피하기

---

## 다음 행동 제안

1. `sisyphus/cli/` 및 `sisyphus/core/` 하위 새 패키지 뼈대와 빈 모듈 생성
2. v3.0 pydantic 모델 + 로더/어댑터부터 구현해 기존 테스트에 통합
3. 의존성 그래프 모듈 완성 후 `plan lint` 재작성해 새로운 검증 통합
