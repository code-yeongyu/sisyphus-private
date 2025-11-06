# Sisyphus v3.0 마이그레이션 QA 체크리스트

## 생성 정보
- **생성일시**: 2025-11-06
- **대상 브랜치**: master
- **최근 커밋**: fb86e8c
- **목적**: v2.1 → v3.0 완전 전환 검증

---

## 1. 코드베이스 레거시 제거 검증

### 1.1 v2.1 파일 삭제 확인
- [ ] `sisyphus/utils/plan_types.py` 파일이 존재하지 않음
- [ ] `sisyphus/core/plan_navigator.py` 파일이 존재하지 않음
- [ ] `sisyphus/core/plan_loader.py` 파일이 존재하지 않음
- [ ] `sisyphus/core/tasks.py` 파일이 존재하지 않음

### 1.2 마크다운 참조 제거
- [ ] `grep -r "ai-todolist\.md" sisyphus/` → 0 결과
- [ ] `grep -r "ai-todolist\.yaml" sisyphus/` → 0 결과

### 1.3 v2.1 Import 제거
- [ ] `grep -r "from sisyphus.utils.plan_types import" sisyphus/` → 0 결과
- [ ] `grep -r "from sisyphus.core.plan_navigator import" sisyphus/` → 0 결과
- [ ] `grep -r "from sisyphus.core.plan_loader import" sisyphus/` → 0 결과
- [ ] `grep -r "PlanNavigator" sisyphus/ | grep -v "#"` → 0 결과 (주석 제외)

---

## 2. v3.0 YAML 스펙 검증

### 2.1 WorkPlan 필드 완전성
- [ ] `ExecutionStatus` 클래스 존재 (started, completed, started_at, completed_at)
- [ ] `WorkMode` 클래스 존재 (parallel_requested, current_task_id)
- [ ] `Progress` 클래스 존재 (total_tasks, completed, in_progress, pending)
- [ ] `WorkPlan`에 `execution` 필드 존재
- [ ] `WorkPlan`에 `work_mode` 필드 존재
- [ ] `WorkPlan`에 `progress` 필드 존재
- [ ] `WorkPlan`에 `current_work` 필드 존재

### 2.2 v2.1 7개 필드 포팅 검증
- [ ] `WorkPlan`에 `user_request` 필드 존재
- [ ] `WorkPlan`에 `objectives` 필드 존재
- [ ] `WorkPlan`에 `background` 필드 존재
- [ ] `WorkPlan`에 `required_background` 필드 존재
- [ ] `WorkPlan`에 `workflow` 필드 존재
- [ ] `WorkPlan`에 `success_vision` 필드 존재
- [ ] `WorkPlan`에 `final_verification` 필드 존재

### 2.3 Verification 구조 검증
- [ ] `BashVerification` 클래스 존재 (execute, expected_stdout, expected_stderr, expected_exit_code)
- [ ] `LLMJudgeVerification` 클래스 존재 (by, context_commands, instruction)
- [ ] `VerificationItem` 클래스가 v2.1 스펙 유지 (bash, llm_judge 리스트 필드)

### 2.4 기본값 제공 확인
- [ ] 상태 필드들이 `Field(default_factory=...)` 패턴 사용
- [ ] 기존 v3.0 YAML (상태 필드 없음) 로드 시 에러 없음

---

## 3. status.json 불변성 검증

### 3.1 스키마 변경 없음
- [ ] `CurrentPlan` 클래스가 3개 필드만 유지: `plan_path`, `plan_root`, `updated_at`
- [ ] status.json에 새 필드 추가 안됨
- [ ] `StatusManager` 코드에서 status.json 확장 시도 없음

---

## 4. CLI 명령어 기능 검증

### 4.1 sisyphus plan
- [ ] `plan init <path>` 동작: v3.0 형식 + 모든 필수 필드 포함
- [ ] `plan validate <path>` 동작: v3.0 YAML 검증
- [ ] 생성된 템플릿에 v2.1 흔적 없음

### 4.2 sisyphus task
- [ ] `task current` 동작: 현재 작업 표시
- [ ] `task next` 동작: 다음 작업으로 전환
- [ ] `task continue` 동작: 현재 완료 + 다음 시작
- [ ] `task show <id>` 동작: 특정 작업 표시
- [ ] `task previous` 동작: 이전 작업으로 돌아가기

### 4.3 sisyphus verify
- [ ] `verify bash <item-id>` 동작: Bash 검증 실행
- [ ] `verify llm <item-id>` 동작: LLM Judge 검증
- [ ] `verify manual <item-id>` 동작: 수동 검증 입력
- [ ] `verify manual-mark <item-id>` 동작: 수동 검증 마크
- [ ] `verify status` 동작: 검증 상태 표시

### 4.4 sisyphus work
- [ ] `work` 동작: TUI 모드 실행
- [ ] `work --no-tui` 동작: 백그라운드 모드 실행
- [ ] 마크다운 체크 로직 제거 확인
- [ ] v3.0 YAML 파일 로드 및 실행

---

## 5. 실제 시나리오 테스트

### 5.1 테스트 YAML 생성
```bash
uv run sisyphus plan init .sisyphus/tasks/qa-test.yaml
```
- [ ] 파일 생성 성공
- [ ] `version: "3.0"` 확인
- [ ] 모든 WorkPlan 필드 존재 확인
- [ ] 상태 필드 기본값 확인

### 5.2 status.json 설정
```json
{
  "version": 1,
  "current_plan": {
    "plan_path": ".sisyphus/tasks/qa-test.yaml",
    "plan_root": "/Users/yeongyu/local-workspaces/sisyphus",
    "updated_at": "2025-11-06T11:00:00Z"
  }
}
```
- [ ] status.json 생성 및 설정

### 5.3 Task 명령 시퀀스 테스트
```bash
# 1. 현재 작업 확인
uv run sisyphus task current

# 2. 다음 작업으로 이동
uv run sisyphus task next

# 3. 작업 계속
uv run sisyphus task continue

# 4. 특정 작업 조회
uv run sisyphus task show <id>
```
- [ ] 각 명령어 에러 없이 실행
- [ ] YAML 파일에 상태 업데이트 확인
- [ ] `work_mode.current_task_id` 변경 확인

### 5.4 Work TUI 모드 테스트
```bash
# interactive-terminal skill 사용
uv run sisyphus work
```
- [ ] TUI 실행
- [ ] 화면에 작업 목록 표시
- [ ] 키보드 인터랙션 동작
- [ ] 종료 시 상태 저장 확인

### 5.5 Work 백그라운드 모드 테스트
```bash
uv run sisyphus work --no-tui
```
- [ ] 백그라운드 실행
- [ ] 로그 출력 확인
- [ ] 작업 진행 상태 확인
- [ ] 종료 시 상태 저장 확인

### 5.6 Verify 명령 테스트
```bash
# Bash 검증
uv run sisyphus verify bash <item-id>

# LLM Judge 검증
uv run sisyphus verify llm <item-id>

# 수동 검증
uv run sisyphus verify manual <item-id>

# 검증 상태
uv run sisyphus verify status
```
- [ ] 각 검증 타입 동작
- [ ] 검증 결과 YAML에 저장
- [ ] `verified`, `verified_at` 필드 업데이트

---

## 6. 에러 메시지 검증

### 6.1 "미지원" 메시지 없음
- [ ] 코드베이스에 "3.0에서 지원하지 않음" 메시지 없음
- [ ] 코드베이스에 "구현 예정" 메시지 없음
- [ ] 코드베이스에 "아직 미지원" 메시지 없음

### 6.2 명확한 에러 메시지
- [ ] v2.1 YAML 로드 시 명확한 에러 메시지
- [ ] 잘못된 YAML 구조 시 Pydantic 검증 에러
- [ ] status.json 없을 때 적절한 안내 메시지

---

## 7. 테스트 스위트 검증

### 7.1 Unit 테스트
```bash
uv run pytest projects/sisyphus-cli/tests/core/ -xvs
```
- [ ] 모든 core 테스트 통과
- [ ] TaskManager 테스트 통과
- [ ] PlanDocument 로더 테스트 통과

### 7.2 Integration 테스트
```bash
uv run pytest projects/sisyphus-cli/tests/test_integration_yaml_plan.py -xvs
```
- [ ] v3.0 fixture 사용 확인
- [ ] 전체 워크플로우 테스트 통과

### 7.3 CLI 테스트
```bash
uv run pytest projects/sisyphus-cli/tests/cli/ -xvs
```
- [ ] task 명령어 테스트 통과
- [ ] plan 명령어 테스트 통과
- [ ] work 명령어 테스트 통과

### 7.4 전체 테스트
```bash
uv run pytest projects/sisyphus-cli/ -x
```
- [ ] 전체 테스트 통과
- [ ] 0 failures

---

## 8. 타입 체크 및 Lint

### 8.1 타입 체크
```bash
uv run basedpyright projects/sisyphus-cli/sisyphus/
```
- [ ] 0 errors

### 8.2 Lint 체크
```bash
uv run ruff check projects/sisyphus-cli/sisyphus/
```
- [ ] 0 errors

---

## 9. 문서 일관성

### 9.1 README 업데이트
- [ ] v2.1 참조 제거
- [ ] v3.0 전용임을 명시
- [ ] 예시 코드가 v3.0 사용

### 9.2 AGENTS.md 업데이트
- [ ] TaskManager 추가됨
- [ ] PlanNavigator 제거됨
- [ ] 아키텍처 다이어그램 최신화

### 9.3 레거시 문서 삭제
- [ ] `docs/schemas/MIGRATION_v2.0_to_v2.1.md` 삭제됨
- [ ] `docs/schemas/ai-todolist-spec-v2.1-final.yaml` 삭제됨

---

## 10. 최종 체크

### 10.1 요구사항 준수
- [ ] v2.1 폴백 코드 **모두** 제거
- [ ] v3.0 YAML이 **모든** 상태 포함
- [ ] status.json 스펙 **변경 없음**
- [ ] work/plan/task/verify **모든** 기능 동작
- [ ] "미지원" 메시지 **0개**

### 10.2 시스템 격리
- [ ] `uv run sisyphus` 형태로 실행
- [ ] 시스템 sisyphus 바이너리에 영향 없음
- [ ] 가상환경 분리 확인

---

## 검증 실행 가이드

### Phase 1: 정적 검증 (grep, 파일 존재 확인)
```bash
# 체크리스트 1, 2, 3 검증
```

### Phase 2: 테스트 스위트 검증
```bash
# 체크리스트 7, 8 검증
```

### Phase 3: 실제 시나리오 테스트
```bash
# 체크리스트 5 검증 (TUI/백그라운드 모드)
```

### Phase 4: CLI 명령어 기능 테스트
```bash
# 체크리스트 4 검증
```

### Phase 5: 문서 및 최종 확인
```bash
# 체크리스트 9, 10 검증
```

---

## 예상 결과

**성공 기준**: 모든 체크박스 ✅
**실패 기준**: 단 하나라도 ❌

**Critical 항목** (반드시 통과):
- 1.2 마크다운 참조 제거
- 1.3 v2.1 Import 제거
- 3.1 status.json 불변성
- 4.1~4.4 모든 CLI 명령어 동작
- 6.1 "미지원" 메시지 없음
- 10.1 요구사항 100% 준수
