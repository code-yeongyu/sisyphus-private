# WorkPlan YAML Schema v2.0

Complete schema definition for `ai-todolist.yaml` work plan files. This document serves as the source of truth for the PlanLinter validation rules.

## Table of Contents
- [Root Fields (WorkPlan)](#root-fields-workplan)
- [Metadata](#metadata)
- [UserRequest](#userrequest)
- [Objectives](#objectives)
- [Background](#background)
- [RequiredBackground](#requiredbackground)
- [Status](#status)
- [Workflow](#workflow)
- [Todo (Recursive)](#todo-recursive)
- [SuccessVision](#successvision)
- [FinalVerification](#finalverification)
- [Enums](#enums)
- [Discriminated Unions](#discriminated-unions)

## Root Fields (WorkPlan)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| metadata | Metadata | ✓ | - | Document metadata |
| user_request | UserRequest | ✓ | - | Original user request |
| objectives | Objectives | ✓ | - | Project objectives |
| background | Background | ✓ | - | Background context |
| required_background | RequiredBackground | ✓ | - | Required background knowledge |
| status | Status | ✓ | - | Execution status |
| workflow | Workflow | ✓ | - | Task workflow |
| todos | list[Todo] | ✓ | - | Task list |
| success_vision | SuccessVision | ✓ | - | Success vision |
| final_verification | list[FinalVerificationCategory] | ✓ | - | Final verification items |

**Note**: WorkPlan has `model_config = ConfigDict(extra="allow")` in Pydantic (plan_types.py:293), but PlanLinter validates strictly (no extra fields allowed).

## Metadata

| Field | Type | Required | Default |
|-------|------|----------|---------|
| created_at | str | ✓ | - |
| updated_at | str | ✓ | - |
| format_version | str | - | "2.0" |

## UserRequest

| Field | Type | Required | Default |
|-------|------|----------|---------|
| original | str | ✓ | - |
| timestamp | str | ✓ | - |
| additional | list[str] | - | [] |

## Objectives

| Field | Type | Required | Default |
|-------|------|----------|---------|
| core | str | ✓ | - |
| detailed | list[DetailedObjective] | - | [] |

### DetailedObjective

| Field | Type | Required | Default |
|-------|------|----------|---------|
| goal | str | ✓ | - |
| measurable | str | ✓ | - |

## Background

| Field | Type | Required | Default |
|-------|------|----------|---------|
| current_situation | str | ✓ | - |
| reason_for_change | str | ✓ | - |
| changes_to_make | str | ✓ | - |

## RequiredBackground

| Field | Type | Required | Default |
|-------|------|----------|---------|
| description | str | ✓ | - |
| file_structure | str \| None | - | None |
| references | list[ReferenceSpec] | - | [] |

## Status

| Field | Type | Required | Default |
|-------|------|----------|---------|
| execution | ExecutionStatus | ✓ | - |
| work_mode | WorkMode | ✓ | - |
| progress | Progress | ✓ | - |
| current_work | str | ✓ | - |

### ExecutionStatus

| Field | Type | Required | Default |
|-------|------|----------|---------|
| started | bool | ✓ | - |
| completed | bool | ✓ | - |
| started_at | str \| None | - | None |
| completed_at | str \| None | - | None |

### WorkMode

| Field | Type | Required | Default |
|-------|------|----------|---------|
| parallel_requested | bool | ✓ | - |
| current_task_id | str \| None | - | None |

### Progress

| Field | Type | Required | Default |
|-------|------|----------|---------|
| total_tasks | int | ✓ | - |
| completed | int | ✓ | - |
| in_progress | int | ✓ | - |
| pending | int | ✓ | - |

## Workflow

| Field | Type | Required | Default |
|-------|------|----------|---------|
| dependency_diagram | str | ✓ | - |
| critical_path | list[str] | - | [] |

## Todo (Recursive)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| id | str \| int | ✓ | - | "1", "1.1", "1.1.1" format (integers converted to strings) |
| title | str | ✓ | - | Task title |
| status | TodoStatus | ✓ | - | pending/in_progress/completed |
| parallel_group | int \| None | - | None | Parallel group number |
| parallel_note | str \| None | - | None | Notes about parallel execution |
| created_at | str | ✓ | - | ISO 8601 format |
| updated_at | str | ✓ | - | ISO 8601 format |
| status_changed_at | str \| None | - | None | Status change timestamp |
| references | list[ReferenceSpec \| SimpleReference] | - | [] | Reference list |
| details | dict[str, Any] | - | {} | Additional details |
| verification_spec | list[VerificationItem] | - | [] | Verification items |
| children | list[Todo] | - | [] | Child tasks (recursive) |

**Note**: `id` field accepts both string and integer (Pydantic @field_validator at plan_types.py:183-186 converts int → str).

## SuccessVision

| Field | Type | Required | Default |
|-------|------|----------|---------|
| user_perspective | list[UserScenario] | - | [] |
| business_perspective | list[BusinessMetric] | - | [] |
| technical_criteria | list[TechnicalCriterion] | - | [] |

### UserScenario

| Field | Type | Required | Default |
|-------|------|----------|---------|
| scenario | str | ✓ | - |
| experience | str | ✓ | - |

### BusinessMetric

| Field | Type | Required | Default |
|-------|------|----------|---------|
| metric | str | ✓ | - |
| target | str | ✓ | - |

### TechnicalCriterion

| Field | Type | Required | Default |
|-------|------|----------|---------|
| category | str | ✓ | - |
| criteria | str | ✓ | - |
| command | str \| None | - | None |
| expected | str | ✓ | - |

## FinalVerification

Root field is `list[FinalVerificationCategory]`.

### FinalVerificationCategory

| Field | Type | Required | Default |
|-------|------|----------|---------|
| category | str | ✓ | - |
| items | list[FinalVerificationItem] | ✓ | - |

### FinalVerificationItem

| Field | Type | Required | Default |
|-------|------|----------|---------|
| id | str | ✓ | - |
| description | str | ✓ | - |
| input | InputSpec | ✓ | - |
| verify | VerifySpec | ✓ | - |
| note | str \| None | - | None |

## Enums

### TodoStatus
```python
class TodoStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
```
Valid values: `"pending"`, `"in_progress"`, `"completed"`

### ReferenceType
```python
class ReferenceType(str, Enum):
    file = "file"
    url = "url"
    code_snippet = "code_snippet"
    text = "text"
```
Valid values: `"file"`, `"url"`, `"code_snippet"`, `"text"`

### InputType
```python
class InputType(str, Enum):
    command = "command"
    prompt = "prompt"
    manual = "manual"
    multi_command = "multi_command"
```
Valid values: `"command"`, `"prompt"`, `"manual"`, `"multi_command"`

### VerifyType
```python
class VerifyType(str, Enum):
    programmatic = "programmatic"
    llm_judge = "llm_judge"
    none = "none"
    prompt = "prompt"
```
Valid values: `"programmatic"`, `"llm_judge"`, `"none"`, `"prompt"`

### RetrievalType
```python
class RetrievalType(str, Enum):
    keywords = "keywords"
    prompt = "prompt"
```
Valid values: `"keywords"`, `"prompt"`

## Discriminated Unions

### InputSpec (Discriminated by `type` field)

#### CommandInput
| Field | Type | Required | Default |
|-------|------|----------|---------|
| type | Literal["command"] | ✓ | - |
| command | str | ✓ | - |
| capture_output | bool | - | True |

#### PromptInput
| Field | Type | Required | Default |
|-------|------|----------|---------|
| type | Literal["prompt"] | ✓ | - |
| prompt | str | ✓ | - |
| context | dict[str, Any] | - | {} |

#### ManualInput
| Field | Type | Required | Default |
|-------|------|----------|---------|
| type | Literal["manual"] | ✓ | - |
| instructions | str | ✓ | - |

#### MultiCommandInput
| Field | Type | Required | Default |
|-------|------|----------|---------|
| type | Literal["multi_command"] | ✓ | - |
| commands | list[str] | ✓ | - |

**Union**: `InputSpec = CommandInput | PromptInput | ManualInput | MultiCommandInput`
**Discriminator**: `type` field must be one of `["command", "prompt", "manual", "multi_command"]`

### VerifySpec (Discriminated by `type` field)

#### ProgrammaticVerify
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| type | Literal["programmatic"] | ✓ | - | - |
| method | str | ✓ | - | "contains", "exact", "regex", "exit_code" |
| expected | str \| int | ✓ | - | - |

#### LLMJudgeVerify
| Field | Type | Required | Default |
|-------|------|----------|---------|
| type | Literal["llm_judge"] | ✓ | - |
| criteria | list[str] | - | [] |
| accept_if | str | - | "All criteria met" |

#### NoneVerify
| Field | Type | Required | Default |
|-------|------|----------|---------|
| type | Literal["none"] | ✓ | - |

#### PromptVerify
| Field | Type | Required | Default |
|-------|------|----------|---------|
| type | Literal["prompt"] | ✓ | - |
| prompt | str | ✓ | - |

**Union**: `VerifySpec = ProgrammaticVerify | LLMJudgeVerify | NoneVerify | PromptVerify`
**Discriminator**: `type` field must be one of `["programmatic", "llm_judge", "none", "prompt"]`

### ReferenceSpec (Discriminated by `type` field)

#### FileReference
| Field | Type | Required | Default |
|-------|------|----------|---------|
| type | Literal["file"] | - | "file" |
| id | str \| None | - | None |
| path | str | ✓ | - |
| description | str | ✓ | - |
| retrieval | RetrievalSpec \| None | - | None |
| notes | str \| None | - | None |

#### URLReference
| Field | Type | Required | Default |
|-------|------|----------|---------|
| type | Literal["url"] | - | "url" |
| id | str \| None | - | None |
| url | str | ✓ | - |
| description | str | ✓ | - |
| retrieval | RetrievalSpec \| None | - | None |
| notes | str \| None | - | None |

#### CodeSnippetReference
| Field | Type | Required | Default |
|-------|------|----------|---------|
| type | Literal["code_snippet"] | - | "code_snippet" |
| id | str \| None | - | None |
| language | str | ✓ | - |
| description | str | ✓ | - |
| code | str | ✓ | - |

#### TextReference
| Field | Type | Required | Default |
|-------|------|----------|---------|
| type | Literal["text"] | - | "text" |
| id | str \| None | - | None |
| description | str | ✓ | - |
| content | str | ✓ | - |

**Union**: `ReferenceSpec = FileReference | URLReference | CodeSnippetReference | TextReference`
**Discriminator**: `type` field must be one of `["file", "url", "code_snippet", "text"]`

### RetrievalSpec (Discriminated by `type` field)

#### KeywordsRetrieval
| Field | Type | Required | Default |
|-------|------|----------|---------|
| type | Literal["keywords"] | ✓ | - |
| keywords | list[str] | ✓ | - |
| line_range | list[int] \| None | - | None |

#### PromptRetrieval
| Field | Type | Required | Default |
|-------|------|----------|---------|
| type | Literal["prompt"] | ✓ | - |
| prompt | str | ✓ | - |

**Union**: `RetrievalSpec = KeywordsRetrieval | PromptRetrieval`
**Discriminator**: `type` field must be one of `["keywords", "prompt"]`

## SimpleReference

Used in Todo.references for referencing required_background.references by ID.

| Field | Type | Required | Default |
|-------|------|----------|---------|
| ref_id | str | ✓ | - |
| note | str \| None | - | None |

**Referential Integrity**: `ref_id` must exist in `required_background.references[].id`

## VerificationItem

Used in Todo.verification_spec.

| Field | Type | Required | Default |
|-------|------|----------|---------|
| id | str | ✓ | - |
| description | str | ✓ | - |
| input | InputSpec | ✓ | - |
| verify | VerifySpec | ✓ | - |
| note | str \| None | - | None |
| completed | bool | - | False |

## Pattern Validations

### Todo ID Format
- Pattern: `^\d+(\.\d+)*$`
- Valid examples: `"1"`, `"1.1"`, `"1.1.1"`
- Invalid examples: `"abc"`, `"1a"`, `"1."`

Note: Integer IDs are automatically converted to strings by Pydantic validator (plan_types.py:183-186).

## Notes

- All timestamp fields (created_at, updated_at, timestamp, etc.) are strings in ISO 8601 format
- Recursive structures: Todo.children contains list of Todo objects
- Discriminated unions MUST have `type` field for Pydantic to determine the correct subtype
- WorkPlan root allows extra fields in Pydantic (extra="allow"), but linter should validate strictly
