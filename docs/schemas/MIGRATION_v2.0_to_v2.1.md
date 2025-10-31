# Migration Guide: v2.0 → v2.1

## Overview

YAML work plan schema v2.1 simplifies the verification structure by removing discriminated unions and introducing direct `bash` and `llm_judge` fields.

## Breaking Changes

### 1. VerificationItem Structure

**Before (v2.0):**
```yaml
todos:
  - id: "1"
    verification_spec:
      - id: "v1"
        description: "Check file exists"
        completed: false
        input:
          type: "command"
          command: "ls -al"
        verify:
          type: "programmatic"
          expected_stdout: "a.txt"
          expected_exit_code: 0
```

**After (v2.1):**
```yaml
todos:
  - id: "1"
    verification_spec:
      - id: "v1"
        title: "Check file exists"
        description: "Check if the file exists"
        verified: false
        orchestrator_manually_verified: false
        manual_verification_evidence: ""
        bash:
          - execute: "ls -al"
            expected_stdout: "a.txt"
            expected_exit_code: 0
```

**Key Changes:**
- `completed` → `verified`
- `input` + `verify` → `bash` (list) or `llm_judge` (list)
- Added `title`, `verified_at`, `verification_evidence` fields
- Added `orchestrator_manually_verified`, `manual_verification_evidence` (required)

### 2. Field Name Changes

| v2.0 | v2.1 |
|------|------|
| `user_request.timestamp` | `user_request.created_at` |
| `note` (everywhere) | `notes` (plural) |
| `VerificationItem.completed` | `VerificationItem.verified` |
| N/A | `VerificationItem.title` (new) |

### 3. FinalVerification Structure

**Before (v2.0):**
```yaml
final_verification:
  - category: "Feature Validation"
    items:
      - id: "fv1"
        description: "Test passes"
        completed: false
        input: {...}
        verify: {...}
```

**After (v2.1):**
```yaml
final_verification:
  - id: "fv1"
    title: "Test passes"
    category: "Feature Validation"
    description: "Test passes"
    verified: false
    orchestrator_manually_verified: false
    manual_verification_evidence: ""
    bash:
      - execute: "pytest"
        expected_exit_code: 0
```

**Key Changes:**
- Flattened structure: removed `items` nesting
- `category` moved to item-level field
- Same fields as `VerificationItem`

### 4. References Structure

**Before (v2.0):**
```yaml
todos:
  - id: "1"
    references:
      - ref_id: "ref-1"  # SimpleReference
        note: "See this"
```

**After (v2.1):**
```yaml
todos:
  - id: "1"
    references:
      - type: "pointer"  # ReferencePointer (explicit type)
        ref_id: "ref-1"
        notes: "See this"
```

**Key Changes:**
- `SimpleReference` removed → use `ReferencePointer` with `type: "pointer"`
- `type` field now **required** for all references (discriminated union)
- `note` → `notes` (plural)

### 5. Reference Types Merged

**Before (v2.0):**
```yaml
references:
  - id: "ref-1"
    type: "text"
    description: "Plain text"
    text: "Some content"

  - id: "ref-2"
    type: "code_snippet"
    description: "Code example"
    language: "python"
    code: "print('hello')"
```

**After (v2.1):**
```yaml
references:
  - id: "ref-1"
    type: "markdown"
    description: "Plain text or code"
    content: |
      Some content

      ```python
      print('hello')
      ```
```

**Key Changes:**
- `text` and `code_snippet` merged into `markdown`
- Use markdown code fences for code blocks
- `language` + `code` → single `content` field with markdown formatting

## New Features

### 1. Bash and LLM Judge as Lists

Both `bash` and `llm_judge` are now lists, allowing multiple verifications per item:

```yaml
verification_spec:
  - id: "v1"
    title: "Multi-step verification"
    description: "Run multiple checks"
    verified: false
    orchestrator_manually_verified: false
    manual_verification_evidence: ""
    bash:
      - execute: "ls -al"
        expected_stdout: "a.txt"
      - execute: "cat a.txt"
        expected_stdout: "content"
    llm_judge:
      - by: "orchestrator-agent"
        context_commands:
          - "git status"
        instruction: "Verify git state is clean"
```

### 2. Context Commands for LLM Judge

Renamed `bash_execute` → `context_commands` (list):

```yaml
llm_judge:
  - by: "orchestrator-agent"
    context_commands:
      - "ls -al"
      - "cat config.json"
    instruction: |
      Review the file list and config.
      Verify a.txt exists and config is valid.
```

### 3. Manual Verification Fields

Two new required fields for orchestrator oversight:

```yaml
orchestrator_manually_verified: false  # Orchestrator approval flag
manual_verification_evidence: ""       # Orchestrator's review notes
```

### 4. Inline References Support

References can now be defined inline (not just pointers):

```yaml
todos:
  - id: "1"
    references:
      # Pointer to global reference
      - type: "pointer"
        ref_id: "ref-1"

      # Inline file reference
      - type: "file"
        path: "/path/to/file.py"
        description: "Implementation file"
        retrieval:
          line_range: [10, 50]

      # Inline markdown content
      - type: "markdown"
        description: "Quick note"
        content: "This is important"
```

## Migration Checklist

- [ ] Replace `user_request.timestamp` with `created_at`
- [ ] Replace all `note` with `notes` (plural)
- [ ] Replace `VerificationItem.completed` with `verified`
- [ ] Add `VerificationItem.title` field
- [ ] Remove `input` and `verify` fields
- [ ] Add `bash` or `llm_judge` lists (at least one required)
- [ ] Add `orchestrator_manually_verified` and `manual_verification_evidence` fields
- [ ] Flatten `final_verification` structure (remove `items` nesting)
- [ ] Add `category` field to each `FinalVerificationItem`
- [ ] Add `type: "pointer"` to all pointer references
- [ ] Convert `text` and `code_snippet` references to `markdown`
- [ ] Rename `bash_execute` → `context_commands` in LLM judge

## Validation

After migration, validate your YAML with:

```bash
uv run sisyphus plan lint --file your-plan.yaml
```

## Example: Complete Migration

**Before (v2.0):**
```yaml
metadata:
  created_at: "2025-01-01"
  updated_at: "2025-01-01"
user_request:
  original: "Implement feature X"
  timestamp: "2025-01-01"
todos:
  - id: "1"
    title: "Task 1"
    status: pending
    created_at: "2025-01-01"
    updated_at: "2025-01-01"
    verification_spec:
      - id: "v1"
        description: "Test passes"
        completed: false
        input:
          type: "command"
          command: "pytest"
        verify:
          type: "programmatic"
          expected_exit_code: 0
    references:
      - ref_id: "ref-1"
        note: "See docs"
final_verification:
  - category: "Tests"
    items:
      - id: "fv1"
        description: "All tests pass"
        completed: false
        input:
          type: "command"
          command: "pytest --cov"
        verify:
          type: "programmatic"
          expected_exit_code: 0
```

**After (v2.1):**
```yaml
metadata:
  created_at: "2025-01-01"
  updated_at: "2025-01-01"
user_request:
  original: "Implement feature X"
  created_at: "2025-01-01"
todos:
  - id: "1"
    title: "Task 1"
    status: pending
    created_at: "2025-01-01"
    updated_at: "2025-01-01"
    verification_spec:
      - id: "v1"
        title: "Test passes"
        description: "Run pytest to verify implementation"
        verified: false
        verified_at: null
        verification_evidence: null
        orchestrator_manually_verified: false
        manual_verification_evidence: ""
        bash:
          - execute: "pytest"
            expected_exit_code: 0
    references:
      - type: "pointer"
        ref_id: "ref-1"
        notes: "See docs"
final_verification:
  - id: "fv1"
    title: "All tests pass"
    category: "Tests"
    description: "Run full test suite with coverage"
    verified: false
    verified_at: null
    verification_evidence: null
    orchestrator_manually_verified: false
    manual_verification_evidence: ""
    bash:
      - execute: "pytest --cov"
        expected_exit_code: 0
```

## Support

For issues or questions, refer to:
- Schema documentation: `docs/schemas/ai-todolist-spec-v2.1-final.yaml`
- Linter errors: `uv run sisyphus plan lint --file <path>`
