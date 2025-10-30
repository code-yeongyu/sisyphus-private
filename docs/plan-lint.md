# sisyphus plan lint

YAML 작업계획서 (`ai-todolist.yaml`)의 스키마 유효성을 검증하는 명령어입니다.

## 사용법

```bash
# 기본 (./ai-todolist.yaml 검증)
sisyphus plan lint

# 특정 파일 검증
sisyphus plan lint --file path/to/plan.yaml
sisyphus plan lint -f ai-todolist-draft.yaml
```

## 검증 항목

### 1. 필수 필드 누락
WorkPlan의 모든 필수 섹션 (metadata, user_request, objectives, background, required_background, status, workflow, todos, success_vision, final_verification) 존재 여부를 확인합니다.

중첩된 필드의 필수 여부도 검증합니다:
- `metadata.created_at`, `metadata.updated_at`
- `status.execution.started`, `status.execution.completed`
- `todos[].id`, `todos[].title`, `todos[].status`, 등

### 2. 타입 불일치
각 필드의 타입이 스키마 정의와 일치하는지 검증합니다:
- **Boolean**: `status.execution.started` (true/false, not "true"/"false")
- **String**: `metadata.created_at`, `todos[].title`, 등
- **Integer**: `status.progress.total_tasks`, `todos[].parallel_group`, 등
- **List**: `todos`, `final_verification`, 등
- **Dictionary**: `metadata`, `status`, 등

### 3. 무의미한 키 (Extra Fields)
스키마에 정의되지 않은 필드를 검출합니다. WorkPlan은 Pydantic에서 `extra="allow"` 설정이지만, linter는 strict 검증을 수행하여 LLM의 YAML 사용 시 오류를 방지합니다.

### 4. 값 유효성 (Enum)
Enum 필드의 값이 허용된 값 목록에 포함되는지 검증합니다:
- **TodoStatus**: `"pending"`, `"in_progress"`, `"completed"`
- **ReferenceType**: `"file"`, `"url"`, `"code_snippet"`, `"text"`
- **InputType**: `"command"`, `"prompt"`, `"manual"`, `"multi_command"`
- **VerifyType**: `"programmatic"`, `"llm_judge"`, `"none"`, `"prompt"`
- **RetrievalType**: `"keywords"`, `"prompt"`

### 5. 참조 무결성
SimpleReference의 `ref_id`가 `required_background.references`에 실제 존재하는지 확인합니다. 존재하지 않는 ref_id는 에러로 처리됩니다.

예시:
```yaml
required_background:
  references:
    - type: "file"
      path: "test.py"
      description: "Test file"
      # id 필드가 없으면 ref_id로 참조 불가

todos:
  - id: "1"
    references:
      - ref_id: "nonexistent"  # Error: Reference ID not found
```

**주의**: ReferenceSpec에는 `id` 필드가 없습니다. SimpleReference에서 ref_id로 참조하려면 required_background.references에 id 필드를 추가해야 하지만, 현재 스키마는 이를 지원하지 않습니다.

### 6. 패턴 검증
특정 필드의 형식을 검증합니다:
- **Todo ID**: `^\d+(\.\d+)*$` 형식 (예: "1", "1.1", "1.1.1")

## 에러 메시지 형식

```
Error: <location> - <message>. Expected: <expected>. Actual: <actual>. Suggestion: <suggestion>
```

### 예시

#### Missing Required Field
```
Error: metadata.updated_at - Missing required field. Expected: field must exist. Suggestion: Add 'updated_at' to metadata
```

#### Type Mismatch
```
Error: status.execution.started - Type mismatch. Expected: boolean. Actual: DoubleQuotedScalarString. Suggestion: Use true/false (not 'true')
```

#### Invalid Enum Value
```
Error: todos[0].status - Invalid enum value. Expected: one of ['pending', 'in_progress', 'completed']. Actual: invalid_status. Suggestion: Change to one of: pending, in_progress, completed
```

#### Unknown Field
```
Error: unknown_field - Unknown field (not in schema). Expected: one of ['background', 'final_verification', 'metadata', 'objectives', 'required_background', 'status', 'success_vision', 'todos', 'user_request', 'workflow']. Actual: unknown_field. Suggestion: Remove 'unknown_field' or check spelling
```

#### Reference Integrity Violation
```
Error: todos[0].references[0].ref_id - Reference ID not found. Expected: one of ['ref1', 'ref2']. Actual: nonexistent_ref. Suggestion: Add reference with id='nonexistent_ref' to required_background.references or fix typo
```

## Exit Codes

- **0**: 검증 성공 (에러 없음)
- **1**: 검증 실패 (에러 발견) 또는 파일 없음

Exit code를 활용하여 CI/CD 파이프라인에 통합할 수 있습니다.

## CI/CD 통합

### GitHub Actions 예시

```yaml
# .github/workflows/validate-plan.yml
name: Validate Work Plan

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync

      - name: Validate work plan
        run: uv run sisyphus plan lint --file ai-todolist.yaml
```

### Pre-commit Hook 예시

```bash
# .git/hooks/pre-commit
#!/bin/bash
set -e

echo "Validating work plan..."
uv run sisyphus plan lint --file ai-todolist.yaml

if [ $? -ne 0 ]; then
  echo "Work plan validation failed. Commit aborted."
  exit 1
fi

echo "Work plan validation passed."
```

## 관련 문서

- [WorkPlan YAML Schema](./plan-schema.md): 전체 스키마 정의 및 필드 설명
- Pydantic 모델: `sisyphus/utils/plan_types.py`

## 제한사항

1. **날짜 형식 검증 제외**: created_at, updated_at, timestamp 등의 날짜 필드는 타입(string)만 검증하며, ISO 8601 형식 여부는 Pydantic이 처리합니다.

2. **Discriminated Union의 type 필드**: InputSpec, VerifySpec, ReferenceSpec, RetrievalSpec는 type 필드가 필수이며, 누락 시 즉시 에러가 발생합니다.

## 예시

### Valid YAML (검증 성공)

```bash
$ uv run sisyphus plan lint --file ai-todolist.yaml
✓ YAML validation passed. 0 errors.
```

### Invalid YAML (검증 실패)

```bash
$ uv run sisyphus plan lint --file broken-plan.yaml
✗ Validation failed: 5 error(s)

  • Error: unknown_field - Unknown field (not in schema). Expected: one of ['background', 'final_verification', 'metadata', 'objectives', 'required_background', 'status', 'success_vision', 'todos', 'user_request', 'workflow']. Actual: unknown_field. Suggestion: Remove 'unknown_field' or check spelling
  • Error: metadata.updated_at - Missing required field. Expected: field must exist. Suggestion: Add 'updated_at' to metadata
  • Error: status.execution.started - Type mismatch. Expected: boolean. Actual: DoubleQuotedScalarString. Suggestion: Use true/false (not 'true')
  • Error: todos[0].status - Invalid enum value. Expected: one of ['pending', 'in_progress', 'completed']. Actual: invalid_status. Suggestion: Change to one of: pending, in_progress, completed
  • Error: todos[0].references[0].ref_id - Reference ID not found. Expected: no references defined. Actual: nonexistent_ref. Suggestion: Add reference with id='nonexistent_ref' to required_background.references or fix typo
```

### File Not Found

```bash
$ uv run sisyphus plan lint --file nonexistent.yaml
Error: File not found: nonexistent.yaml
```
