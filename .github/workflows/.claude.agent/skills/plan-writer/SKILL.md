---
name: plan-writer
description: Analyze user requirements to create or modify systematic work plans saved as ./ai-todolist.md. Understand project structure, gather implementation information, and generate detailed actionable plans that workers can follow. Support new plan creation, existing plan modification, and plan-reviewer agent review. Activate when users request work planning, task breakdown, or implementation roadmap creation.
---

# Plan Writer

Create systematic, actionable work plans by analyzing user requirements and project context.

## When to Use This Skill

Activate when users:
- Request to create a work plan or implementation roadmap
- Ask to break down tasks or plan a feature implementation
- Want to modify an existing work plan
- Need detailed implementation guidance with step-by-step instructions
- Request structured planning for coding tasks
- User requests to write a task plan

## Core Principles

### The 90% Confidence Threshold

**Every task must enable workers to proceed with ≥90% confidence using ONLY the plan document.**

This means:
- Workers should NOT need external research or guesswork
- All necessary context, references, and examples are embedded in the plan
- Ambiguity is minimized to ≤10% uncertainty per task
- The plan is self-contained and complete

### Planning Standards

1. **Big Picture First (WHY, WHAT, HOW)**
   - **WHY**: Purpose statement (business value, user problem to solve)
   - **WHAT**: Background context (current state → what we're changing)
   - **HOW**: Task flow (dependencies, sequence, logical connections)
   - **Success Vision**: End state from product/user perspective (not just "code works")

2. **Clarity Through Logical References**
   - Every task MUST provide clear navigation paths:
     - File paths with searchable concepts (e.g., `models/User.ts` - search for `@Column` decorator patterns)
     - URLs with searchable sections (e.g., `https://example.com/docs` - find "JWT token creation" section)
     - Code snippets when patterns are complex or non-obvious
   - No vague instructions like "add authentication" without reference sources

3. **Verifiability Through Measurable Criteria**
   - Every task MUST have objective completion criteria:
     - Executable commands (e.g., `npm test -- AuthModule`)
     - Expected outputs (e.g., "3/3 tests pass", "API returns 201 status")
     - Observable outcomes (e.g., "Dark mode toggle appears in header")
   - NEVER use subjective terms like "properly", "correctly", "good enough"

4. **Completeness Through Explicit Context**
   - State all implicit assumptions explicitly
   - Document data flows, state management, error handling strategies
   - Provide edge case handling guidance
   - Clarify architectural constraints (SSR vs client, sync vs async, etc.)

### Worker-Centric Writing Philosophy

**CRITICAL: Always write from the worker's perspective. The test is: "Can a competent developer execute this task with ≥90% confidence using ONLY what's written?"**

#### The Core Test: "Can I Start and Trace?"

For every task you write, simulate being the worker:

1. **Can I find the starting point?**
   - Is there a clear file path and searchable concept to begin?
   - Do I know which file to open and what to search for?

2. **Can I trace the information I need?**
   - If I read the referenced file and search for the concept, will I find the pattern?
   - If I follow imports and related code, will I understand the full context?
   - Are there logical breadcrumbs that lead me to all necessary information?

3. **Do I know WHAT to build?**
   - Is the business logic clear? (What should this feature do?)
   - Is the desired behavior explicit? (How should it work from user's perspective?)

4. **Do I know HOW to build it?**
   - Is the architectural approach specified? (Which pattern, which library, which method?)
   - Are integration points clear? (How does this connect to existing systems?)

5. **Do I know WHEN it's done?**
   - Are success criteria measurable and objective?
   - Can I verify completion without subjective judgment?

#### What Workers Need vs What They Can Discover

**Workers MUST get from the plan (not through exploration):**
- **Business requirements**: What feature does, why it works certain way
- **Architectural decisions**: Which pattern to use, how systems integrate
- **Starting points**: Where to begin, which files contain relevant patterns, what to search for
- **Edge case handling**: How to handle errors, empty states, concurrent edits
- **Project-specific conventions**: Custom patterns unique to this codebase

**Workers CAN discover through natural exploration (10% allowance):**
- **Technical details**: Exact function signatures, import statements
- **Framework conventions**: Standard React hooks usage, Django ORM patterns
- **Type definitions**: Following type references to understand data structures
- **Related utilities**: Helper functions imported by referenced code

#### Avoiding Implicit Knowledge

Before writing each task, ask yourself:

- [ ] **Am I assuming the worker knows the business logic?**
  - If yes → Document it explicitly
  - Example: Don't assume worker knows "payment is async via background job"

- [ ] **Am I assuming the worker knows which approach to use?**
  - If yes → Specify the architectural decision
  - Example: Don't say "add state" → Say "add to Redux store following pattern in store/auth.ts (search for `createSlice` usage)"

- [ ] **Am I assuming the worker knows project conventions?**
  - If yes → Either cite where convention is documented OR explain it
  - Example: Don't assume worker knows "we always colocate tests with implementation"

- [ ] **Am I leaving edge cases undefined?**
  - If yes → Document how to handle them
  - Example: Don't leave empty state handling to worker's judgment

## Language Adaptation

**CRITICAL: Match the user's language throughout the entire plan document.**

1. **Language Detection**
   - If user requests in **Korean** → Write entire plan in Korean
   - If user requests in **English** → Write entire plan in English
   - If user requests in **Japanese** → Write entire plan in Japanese
   - If mixed → Use the dominant language (majority of user's words)

2. **Consistency Requirements**
   - ALL sections must use the same language
   - Section headers, descriptions, explanations, examples
   - Code comments within snippets
   - Verification instructions
   - Success criteria

3. **Code and Technical Terms**
   - Code snippets remain in their original programming language
   - File paths, URLs, and commands remain as-is
   - Technical terms (e.g., "OAuth", "JWT", "API") can remain in English
   - Explanatory text around technical terms follows the plan's language

## Initial Requirements Clarification (CRITICAL FIRST STEP)

**90% of user requests are highly abbreviated, implicit, and abstract.** Before creating any plan, you MUST engage in a clarification dialogue with the user.

### Clarification Process

1. **Identify Implicit Knowledge**
   - What assumptions is the user making?
   - What domain knowledge are they assuming you already have?
   - What context from the project is not explicitly stated?

2. **Attempt Contextual Inference**
   - Can the requirement be clearly inferred from project context?
   - Are there similar features or patterns that suggest the user's intent?
   - Does the codebase structure provide enough clues?

3. **Ask Clarifying Questions**
   When inference is insufficient, ask targeted questions:
   - "I understand you want [X]. Could you clarify [specific ambiguous point]?"
   - "Should this feature work like [similar existing feature], or differently?"
   - "What should happen when [edge case scenario]?"
   - "Are there any specific constraints or requirements I should know about?"

4. **Iterative Refinement**
   - Present your understanding and ask for confirmation
   - Refine based on user feedback
   - Continue until the requirement is concrete and unambiguous

5. **Document Clarified Requirements**
   - Once clarified, document the final understood requirements
   - Include both explicit user statements and confirmed implicit assumptions

**DO NOT PROCEED** to plan creation until requirements are sufficiently concrete and verified with the user.

## Work Process

### Phase 0: Register Plan Creation Steps (ALWAYS EXECUTE FIRST)

Before starting any plan creation work, use the TodoWrite tool to register all upcoming steps:

```
Use TodoWrite to create todos for the following:
1. Clarify and refine user requirements
2. Analyze codebase and gather implementation information
3. Create work plan draft
4. Request plan-reviewer verification
5. Incorporate reviewer feedback (iterative)
6. Save final plan to ./ai-todolist.md
7. (GitHub CI only) Push branch to remote
8. (GitHub CI only) Report success to user by comment that includes:
- Branch Name
- file permalink (make sure it is from that actual branch's permalink)

Mark each step as 'pending' initially, then update to 'in_progress' and 'completed' as you work through them.
```

This ensures full visibility into the plan creation process and allows for proper task tracking.

### Phase 0.5: Repository Preparation (ALWAYS EXECUTE AFTER TODOWRITE)

Before starting any plan creation work, ALWAYS execute these steps in order:

1. **Create New Branch**
   ```bash
   # Generate branch name with timestamp
   BRANCH_NAME="plan-writer/$(date +%Y%m%d-%H%M%S)"
   git checkout -b "$BRANCH_NAME"
   ```
   - Branch naming: `plan-writer/YYYYMMDD-HHMMSS`
   - This ensures each plan creation is on a fresh branch

2. **Reset Work Environment**
   ```bash
   uv run sisyphus reset --include-task-specs
   ```
   - Removes: `sessions/`, `logs/`, `ai-todolist.md`, `notepad.md`
   - Ensures clean slate for new work plan

3. **Commit Reset State**
   ```bash
   git add -A
   git commit -m "chore: reset work environment for new plan"
   ```
   - Commits the cleaned state
   - Provides baseline for plan generation

**CRITICAL**: These steps are MANDATORY before proceeding to Phase 1. Do NOT skip or reorder them.

### Phase 1: Initial Analysis and Information Gathering

#### 1.1 Determine Mode
Check user request for mode indicators:
- Keywords like "edit", "modify", "update" → Edit existing plan
- Default → New plan creation

#### 1.2 Requirements Analysis
1. **Identify Work Goals**
   - Clarify final objectives user wants to achieve
   - Distinguish functional and non-functional requirements
   - Define success criteria (product/user outcomes, not just technical)

2. **Scope Setting**
   - Separate what's included vs excluded
   - Set priorities
   - Review phased implementation feasibility

#### 1.3 Codebase Analysis for Implementation
1. **Find Related Code Patterns**
   - Search for similar functionality already implemented
   - Identify existing patterns that can be reused or extended
   - Look for related modules and components
   - **CRITICAL**: Capture file paths + searchable concepts for every relevant pattern found

2. **Analyze Implementation Context**
   - Find where similar features are implemented
   - Understand how existing code handles similar requirements
   - Identify integration points and dependencies
   - **CRITICAL**: Note down patterns with searchable keywords (prepare to cite file paths with search terms)

3. **Extract Project Conventions**
   ```bash
   git log -10 --oneline
   ```
   - Learn commit message patterns from recent commits
   - Observe code organization and naming conventions
   - Understand testing and validation approaches used in project

#### 1.4 Smart Code Exploration
1. **Semantic Code Search**
   - Use `ck --sem "[concept]"` for understanding code by meaning
   - Use `ck --hybrid "[keyword]"` for both exact and semantic matches
   - Fallback to `Grep` for specific text patterns

2. **Pattern Discovery**
   - Identify existing implementation patterns in project
   - Find reusable components and conventions
   - Map architectural decisions from actual code
   - **CRITICAL**: Assess pattern complexity → determine if code snippets needed in plan

### Phase 2: Plan Creation

#### 2.1 Standard Plan Template

Use this comprehensive template for all work plans (adapt language to match user's query):

**For English plans:**
```markdown
# User's Original Request (For Record)
[Write exactly what the user said when initially requesting the plan]

## Additional User Requests (For Record)
[Write all subsequent requests excluding the initial request]

# Work Objectives (WHAT & WHY)

## Core Objective (TL;DR)
[One or two sentences clearly explaining what we want to achieve]

## Detailed Objectives
[List specific objectives to accomplish]
- Describe from business value or user problem-solving perspective
- Include measurable success metrics

# Work Background (WHY & WHAT - Current State)

## Current Situation
[Current state of the system, what problems exist]

## Reason for Change
[Why this work is necessary, what problem it solves]

## Changes to Make
[Clearly contrast current state → future state]

# Work Started
is_execution_started = FALSE

# All Goals Accomplished
is_all_goals_accomplished = FALSE

# Parallel Execution
parallel_requested = FALSE

# Current Work in Progress
- Work has not started yet.
   - When starting work, change the value of `is_execution_started` above to TRUE.
   - Never start work until the user explicitly says "start the work".
   - **Even if you receive OKAY from plan reviewer, NEVER start work**
   - Never start work until the user explicitly says "start the work".


# Required Background Knowledge
[Domain knowledge, tech stack, etc. needed to perform this work]

## File Structure and Roles
[Files affected by the work and each file's role]

## Reference Files for Context Understanding
### 1. [File path]
- **Role**: [What this file does]
- **What to search for**: [Searchable concepts, function names, class names, patterns to look for]
- **Key pattern to understand**: [Brief description of what pattern looks like - e.g., "decorator usage with nullable option", "middleware chain pattern"]
- **Code Snippet** [OPTIONAL - include only when pattern is complex or multi-step]:
   ```python
   # Code extracted from actual project showing the key pattern
   class SomeClass:
      def method_to_check(self):
            # Must follow this pattern
            pass
   ```

### 2. [Another file path]
- **Role**: [This file's role]
- **What to search for**: [Searchable keywords or concepts]
- **Notes**: [Special points to pay attention to]
- **Reference URL**: [Related documentation URL + searchable section keyword if available]

[Note: This file list should be 'global context' - include only essential content needed for most tasks. Context needed for individual tasks should go inside 'todo' items.]

# Work Flow (HOW - Task Flow & Dependencies)

## Task Dependency Diagram
```
Task 1 (Foundation)
   ↓
Task 2 (depends on 1's output)
   ↓
Task 3 || Task 4 (parallel, both depend on 2)
   ↓
Task 5 (integration, depends on 3 & 4)
```

## Phase-by-Phase Explanation
- **Phase 1 (Task 1-2)**: [What this phase does, why it must come first]
- **Phase 2 (Task 3-4)**: [Reason for parallel execution: different files, no dependencies]
- **Phase 3 (Task 5)**: [Final integration phase]

# Work Plan

## PRDs & Structures
[To understand the big picture easily, write the following:]
[PRD for what we want to build through this work, how each component and element interacts with each other, in mermaid]
[Structures Overview for what we want to build, in mermaid]

## Implementation Details

### Architecture Constraints
- [Specify SSR vs Client-side, Sync vs Async, etc.]
- [State management approach: Redux/Context/Local state, etc.]
- [Error handling strategy: Toast/Inline/Redirect, etc.]

### Edge Case Handling
- [When list is empty: what UI to show?]
- [When loading: what state to show?]
- [When error occurs: how to handle?]
- [Concurrent edit conflicts: how to resolve?]

### Making Implicit Assumptions Explicit
- [Example: "User is already authenticated (session context exists)"]
- [Example: "Payment processing is handled asynchronously via background job"]

## Project Commit Message Style
[Summary of this project's commit message pattern based on git log analysis]

# TODOs

- [ ] 1. [Feature 1 - Example: Modify User model and test. Implementation and testing should always be one Task]

   **Reference Sources (REQUIRED)**:
   - Pattern file: `models/Product.ts` (search for `@Column` decorator, look at timestamp field patterns like `last_updated`)
   - Test file: `tests/models/Product.test.ts` (search for model test structure, find tests for timestamp fields)
   - Documentation: https://docs.example.com/models (search for "adding fields" section)

   - [ ] 1.1 Implementation: Modify [specific function/class name] in [specific file name]

      **What to search in reference file**: [e.g., "Search for `@Column` decorator usage with `nullable: true`, examine how timestamp fields are defined"]

      **Code Pattern Reference** [OPTIONAL - include only if pattern is complex or non-obvious]:
      ```python
      # Actual code extracted from project showing the pattern
      class Product extends BaseModel {
         @Column({ type: "timestamp", nullable: true })
         last_updated: Date | null;
      }
      ```

      **Implementation Details**:
      - Current: [Current code or state]
      - Change: [Code or state to change to]
      - Note: [Project convention notes, architectural decisions]

   - [ ] 1.2 Write test: Add test for this feature to [test_filename.py]

      **Test Pattern Reference**: `tests/models/Product.test.ts` (search for `describe("Product model")`, examine timestamp field test structure)
      [Code snippet OPTIONAL - include only if test pattern is non-standard]

   - [ ] 1.3 Run and verify tests

      **Execute Command**: `pytest -xvs test_filename.py::test_function_name`

      **Expected Output**:
      ```
      test_user_last_login ... PASSED
      ===================== 1 passed in 0.23s =====================
      ```

      **If Fails**:
      - Timestamp type error → Check `datetime` import
      - Null value error → Check `nullable=True` option

   - [ ] 1.4 Lint and type check
      - [ ] `ruff check [modified files]` → 0 errors expected
      - [ ] `basedpyright [modified files]` → 0 errors expected

   - [ ] 1.5 Commit after confirming tests pass (**commit per work unit is mandatory**)
      - Write according to project convention (based on git log analysis)
      - Example: `git add [implementation file + test file] && git commit -m "Add last_login field to User model"`

   - [ ] **Work Completion Verification Checklist** (Acceptance criteria for Orchestrator)
      - [ ] Is code accurately added to `models/User.ts`?
      - [ ] Is it written in the same style as existing Product model pattern?
      - [ ] Is test added to test file `tests/models/User.test.ts`?
      - [ ] Run `pytest -xvs tests/models/User.test.ts::test_user_last_login` → Confirm PASSED
      - [ ] Run `ruff check models/User.ts tests/models/User.test.ts` → Confirm 0 errors
      - [ ] Run `basedpyright models/User.ts` → Confirm 0 errors
      - [ ] Is git commit completed? (Check with `git log -1 --oneline`)
      - [ ] Verify actual feature works:
        ```python
        # Test directly with Python REPL
        from models import User
        user = User.create(email="test@example.com")
        user.update_last_login()
        assert user.last_login is not None
        ```

- [ ] 2. [Feature 2 - Example: Implement and test login API]

   **Reference Sources (REQUIRED)**:
   - API pattern: `api/auth/register.ts` (search for authentication endpoint structure, examine request validation and response format)
   - Validation: `utils/validators.ts` (search for email/password validation functions)
   - Documentation: https://fastapi.tiangolo.com/tutorial/security/ (find "OAuth2 with Password" section)

   - [ ] 2.1. Review references
      - [ ] Review https://example.com/docs (search for "JWT token creation" section)
        - Learn `create_access_token` function pattern from example code
      - [ ] Review `./api/auth/register.ts` file
        - Search for request body validation method
        - Check response format (status code, body structure)
      - [ ] [Subsequent tasks]

   - [ ] **Work Completion Verification Checklist**
      - [ ] Confirm API endpoint `/api/auth/login` exists
      - [ ] Manual test:
        ```bash
        curl -X POST http://localhost:8000/api/auth/login \
          -H "Content-Type: application/json" \
          -d '{"email": "test@example.com", "password": "password123"}'
        ```
        Expected response:
        ```json
        {
          "access_token": "eyJ...",
          "token_type": "bearer",
          "user": {"id": 1, "email": "test@example.com"}
        }
        ```
      - [ ] Automated test: `pytest tests/api/auth/test_login.py` → 5/5 PASSED
      - [ ] Confirm 401 returned for wrong password
      - [ ] Confirm 404 returned for non-existent email


- [ ] 3 parallel. [Feature 3 - Example: Implement and test board post creation API requiring authentication. If parallelable option is not set, this is task 3.]

   **※ Parallel Execution Condition**: Completely independent from Feature 4, modifies different files, no dependencies at all
   - Task 3: Modifies `api/posts/create.ts`
   - Task 4: Modifies `api/posts/delete.ts`
   - No common dependencies (each independent endpoint)

   **Reference Sources (REQUIRED)**:
   - [file path + what to search for in that file]
   - [URL + searchable section keyword if applicable]
   - [Code snippet only if pattern is complex]

   - [ ] **Work Completion Verification Checklist**
      - [Specific and measurable verification methods]


- [ ] 3 parallel. [Feature 4 - Example: Implement and test board post deletion API requiring authentication. If parallelable option is not set, this is task 4.]

   **※ Parallel Execution Condition**: Completely independent from Feature 3, modifies different files, no dependencies at all

   **Reference Sources (REQUIRED)**:
   - [file path + searchable concept/keyword]

   - [ ] **Work Completion Verification Checklist**
      - [Specific and measurable verification methods]


# Success Vision

## Success from User Perspective
- [Changes users will experience: "Can now log in with one-click OAuth"]
- [User journey: Access login page → Click Google button → Immediately logged in]

## Success from Business Perspective
- [Measurable metrics: "OAuth login accounts for 80% of total logins"]
- [Expected effect: "Password reset support tickets decrease by 30%"]

## Technical Success Criteria
- [All tests pass: `npm test` → 45/45 PASSED]
- [Performance criteria: "Login API response time < 200ms (95th percentile)"]
- [Security criteria: "OAuth token expiration handling works correctly"]

# Final Work Verification Checklist
- [ ] 1. **Verify Feature Works**
  - [What parts work - how to verify them]
  - [Executable commands and expected outputs]

- [ ] 2. **Prevent Incorrect Implementation**
  - [Check what user said not to do]
  - [Check easily mistaken parts according to project conventions]

- [ ] 3. **Verify Scope Compliance**
  - [Check if implemented differently from initial plan]
  - [Check if over-implemented]

- [ ] 4. **Existing Feature Regression Test**
  - [List of existing features that may be affected by modified files]
  - [Verification method for each feature: execution command + expected result]
```

**For Korean plans:** Translate all section headers and field names to Korean while maintaining the same structure.

#### 2.2 Plan Creation Strategy

**Core Strategy: Maximize Clarity and Minimize Ambiguity**

The goal is to achieve ≥90% worker confidence at every step. This means:

1. **Every Task Must Have Clear Reference Sources**

   For each task, provide AT LEAST ONE of:
   - **File reference with searchable concepts**: `models/User.ts` (search for `@Column` decorator, examine timestamp field patterns)
   - **URL with searchable section**: `https://stripe.com/docs/api/payment_intents` (find "Creating a PaymentIntent" section)
   - **Code snippet when pattern is complex**: Show actual code pattern when it's not obvious from reading the file

   [FAIL] **BAD**: "Add OAuth login"
   [PASS] **GOOD**: "Add OAuth login following the pattern in `auth/google.ts` (search for `AuthProvider` interface implementation, examine session storage mechanism usage)"

2. **Every Task Must Have Measurable Acceptance Criteria**

   Provide CONCRETE, OBJECTIVE success criteria:
   - **Executable commands**: `npm test -- AuthModule`
   - **Expected outputs**: "3/3 tests pass", "API returns 201 status with token"
   - **Observable outcomes**: "Toggle button appears in header (top-right)"
   - **Numeric criteria**: "Response time < 200ms for 95th percentile"

   [FAIL] **BAD**: "Make sure it works properly"
   [PASS] **GOOD**: "Verify: Run `npm test -- DarkMode` → 3/3 tests pass. Manual test: Click toggle → theme changes within 100ms → reload → theme persists (check localStorage)."

3. **Provide Complete Context (90% Confidence Threshold)**

   Workers should NOT need to guess about:
   - **Business logic**: What feature does, why it works certain way
   - **Data flow**: How data moves through the system
   - **State management**: Where and how state is stored/updated
   - **Error handling**: What to do when things fail
   - **Edge cases**: Empty lists, loading states, timeouts, concurrent edits
   - **Architecture constraints**: SSR vs client, sync vs async, browser APIs availability

   Make implicit assumptions EXPLICIT:
   [PASS] "Assume user is already authenticated (session exists in context)"
   [PASS] "Payment processing is handled by background job, not synchronously"

4. **Big Picture Before Details**

   Before diving into tasks, ensure the plan answers:
   - **WHY**: Why are we building this? (business value, user problem)
   - **WHAT**: What's the current state? What are we changing?
   - **HOW**: How do tasks connect? What's the flow and dependencies?
   - **SUCCESS**: What does "done" look like from product/user perspective?

5. **Reference-First Approach (Code Snippets Only When Complex)**

   **Default: File paths + searchable concepts + brief description**
   - Most tasks: Workers can read the file and understand the pattern
   - Provide file path, what to search for, and what pattern looks like
   - Trust workers to follow imports and trace related code

   **When to add code snippets:**
   - Pattern is complex or has multiple steps
   - Pattern is non-obvious even when reading the source file
   - Pattern involves subtle details that might be missed
   - Pattern requires understanding interaction between multiple pieces

   **Decision Framework:**
   ```
   Ask yourself: "If I open this file and search for this concept, is it obvious what pattern to follow?"
   - YES → File path + searchable concept is sufficient
   - NO → Add code snippet showing the key pattern
   ```

6. **Worker Simulation: Test Sufficiency**

   After writing each task, simulate being the worker:

   - [ ] "Can I find where to start?" (Clear file path + searchable concept?)
   - [ ] "Do I know WHAT to build?" (Business logic clear? Desired behavior explicit?)
   - [ ] "Do I know HOW to build it?" (Architectural approach specified? Pattern clear?)
   - [ ] "Can I trace necessary information?" (References lead to full context? Can follow breadcrumbs?)
   - [ ] "Do I know WHEN it's done?" (Success criteria measurable? Verification method clear?)

   If ANY answer is uncertain → Add more context, references, or explanations.

7. **Implicit Knowledge Elimination**

   Before finalizing, check for implicit assumptions:

   - [ ] **Business Logic**: Did I document WHAT feature does and WHY?
   - [ ] **Architectural Decisions**: Did I specify WHICH approach to use?
   - [ ] **Integration Points**: Did I clarify HOW systems connect?
   - [ ] **Edge Cases**: Did I define WHAT to do in error scenarios?
   - [ ] **Project Conventions**: Did I cite WHERE conventions are documented?

   If you find yourself thinking "the worker should know this" → **Stop. Document it.**

8. **Use TodoWrite for Final Plan**
   - Create todo items ONLY for the actual work steps
   - Each todo = one verifiable action
   - Mark items as workers complete them

9. **Parallel Task Marking (when user requests parallel execution)**
   - **BE CONSERVATIVE**: Only mark tasks as parallel when absolutely certain they are independent
   - **Verify Independence**: Check that tasks:
     - Modify completely different files
     - Have zero shared dependencies
     - Do not require sequential execution
     - Can be tested independently
   - **When Uncertain**: Default to sequential execution - it's safer
   - **Mark Pattern**: Use `- [ ] N parallel.` where N is the same number for all tasks in the parallel group
   - **Document Reasoning**: Add a note explaining WHY tasks can run in parallel

#### 2.3 Special Case: Bug Fix Plans

**CRITICAL**: When creating plans for bug fixes (not new features), you MUST include additional information that proves the bug exists, can be reproduced, has a clear root cause, and has a sound fix direction.

**Why This Matters**: plan-reviewer will automatically REJECT bug fix plans that lack these components. Bug fixes require higher scrutiny than feature implementations because they involve understanding existing broken behavior and proving the fix is correct.

##### Required Components for Bug Fix Plans

Every bug fix task in your plan MUST include ALL of these sections:

###### 1. Bug Existence Verification

**What to Document**:
- **Current Behavior** (what's broken): Observable, specific description of the bug
  - [PASS] Good: "API returns 500 error when user submits form with empty email field"
  - [FAIL] Bad: "The feature doesn't work properly"

- **Expected Behavior** (what should happen): Clear specification of correct behavior
  - [PASS] Good: "API should return 400 with validation error message 'Email is required'"
  - [FAIL] Bad: "It should work correctly"

- **Evidence** (proof bug exists): Logs, screenshots, error messages, user reports
  - [PASS] Good: "See error in production logs: `logs/error-2024-01-15.log:450-455`"
  - [PASS] Good: "Screenshot: `docs/bugs/dark-mode-issue.png`"
  - [FAIL] Bad: "Users have complained"

**Template to Use**:
```markdown
### Bug Description
**Current Behavior**: [Exact observable problem]

**Expected Behavior**: [What should happen instead]

**Evidence**: [File paths to logs/screenshots, error messages, user report references]
```

###### 2. Reproduction Steps

**What to Document**:
- **Step-by-step reproduction**: Exact sequence to trigger the bug
- **Preconditions**: Required setup, environment, data state
- **Consistency**: How often bug occurs (100%? intermittent?)

**Template to Use**:
```markdown
### Reproduction Steps
1. [First action - be specific]
2. [Second action - include exact clicks/inputs]
3. [Third action]
4. **Observe**: [What happens - the bug]
5. **Expected**: [What should happen instead]

**Prerequisites**: [Environment, login state, data requirements]

**Reproducibility**: [100% consistent / ~30% intermittent / rare]
```

**Quality Check**: Can someone follow these steps blindly and see the bug?

###### 3. Root Cause Analysis

**What to Document**:
- **Code Location**: Exact file and line numbers where bug originates
- **Technical Explanation**: WHY the code produces the bug (not just symptoms)
- **Logical Flow**: How the bug manifests through the system

**Template to Use**:
```markdown
### Root Cause Analysis
**Location**: `path/to/file.ts:145-160`

**Technical Cause**:
[Explain what the code does wrong and why it causes the bug]

**Code Reference**:
```language
// Show the problematic code from the actual file
[actual buggy code snippet]
```

**Why This Causes the Bug**:
1. [Step 1 of logical flow]
2. [Step 2 - what goes wrong]
3. [Step 3 - resulting bug symptom]

**Logical Flow**: [Brief summary: trigger → defect → symptom]
```

**Quality Check**:
- Is the file path + line number specified?
- Does explanation show WHY code is broken (not just describe symptoms)?
- Can you trace cause from trigger to symptom?

###### 4. Fix Direction

**What to Document**:
- **Fix Strategy**: High-level approach to resolve root cause
- **Code Changes Scope**: Which files/functions to modify
- **Implementation Sketch**: Enough detail to prove fix works (not complete code)
- **Why This Fix Works**: Logical connection from fix to root cause
- **Side Effects & Risks**: What else might be affected

**Template to Use**:
```markdown
### Fix Direction

**Strategy**: [One sentence describing the fix approach]

**Files to Modify**:
1. `path/to/file.ts:line` - [What to change]
2. `another/file.ts:line` - [What to change]

**Implementation Sketch**:
```language
// Current (problematic code):
[show current code]

// Fixed:
[show fixed code with key change highlighted]
```

**Why This Works**:
[Explain how this fix addresses the root cause and prevents the bug]

**Side Effects**:
- [What else might change]
- [Potential risks]
- **Mitigation**: [How to handle risks]
```

**Quality Check**:
- Is fix strategy clear and concrete?
- Are file paths and code locations specified?
- Does implementation sketch show the key change?
- Is there a logical explanation of why fix works?
- Are side effects/risks acknowledged?

##### Bug Fix Plan Template

When user requests a bug fix, structure your plan like this:

```markdown
# User's Original Request (For Record)
[User's exact bug report]

# Work Objectives (WHAT & WHY)

## Core Objective (TL;DR)
Fix [bug description] to restore [expected functionality]

## Detailed Objectives
- Resolve bug where [current broken behavior]
- Ensure [expected behavior] works correctly
- Prevent similar bugs in [related areas]

# Work Background (WHY & WHAT - Current State)

## Current Situation
[Describe the buggy behavior and its impact]

## Reason for Change
[Why this bug is critical, who it affects, business impact]

# Work Started
is_execution_started = FALSE

# All Goals Accomplished
is_all_goals_accomplished = FALSE

# TODOs

- [ ] 1. Verify and analyze the bug

   **Bug Existence Verification**:
   - **Current Behavior**: [Observable problem]
   - **Expected Behavior**: [Correct behavior]
   - **Evidence**: [Logs/screenshots/reports]

   **Reproduction Steps**:
   1. [Step 1]
   2. [Step 2]
   3. **Observe**: [Bug appears]
   4. **Expected**: [Should work this way]

   **Prerequisites**: [Environment, setup needed]
   **Reproducibility**: [Consistency rate]

   **Root Cause Analysis**:
   - **Location**: `file.ts:line`
   - **Technical Cause**: [Why code is broken]
   - **Code Reference**:
     ```typescript
     // Buggy code from actual file
     ```
   - **Logical Flow**: [Trigger → defect → symptom]

   - [ ] 1.1 Reproduce the bug locally
      - Follow reproduction steps above
      - **Verify**: Bug appears as described
      - **Document**: Any additional findings

- [ ] 2. Implement the fix

   **Fix Direction**:
   - **Strategy**: [How to fix]
   - **Files to Modify**: `file.ts:line` - [change description]

   **Implementation Sketch**:
   ```typescript
   // Current:
   [buggy code]

   // Fixed:
   [corrected code]
   ```

   **Why This Works**: [Explanation]
   **Side Effects**: [Risks and mitigations]

   - [ ] 2.1 Implement fix in `file.ts`
      - Apply changes as outlined in implementation sketch
      - **Reference**: [Similar fix pattern if exists]

   - [ ] 2.2 Write/update tests to cover the bug
      - Add test that would fail with bug, passes with fix
      - **Test file**: `tests/file.test.ts`
      - **Test case**: Should [expected behavior] when [trigger condition]

   - [ ] 2.3 Run tests and verify fix
      **Execute Command**: `npm test -- file.test.ts`
      **Expected Output**: All tests pass, new test prevents regression

- [ ] 3. Verify fix resolves the bug

   - [ ] 3.1 Re-run reproduction steps
      - Follow original reproduction steps
      - **Verify**: Bug no longer appears
      - **Confirm**: Expected behavior now occurs

   - [ ] 3.2 Test edge cases
      - [Related scenario 1]
      - [Related scenario 2]
      - Ensure fix doesn't break other functionality

   - [ ] 3.3 Check for regressions
      - Run full test suite: `npm test`
      - **Expected**: All existing tests still pass

   - [ ] **Work Completion Verification Checklist**
      - [ ] Original bug reproduction steps no longer trigger bug
      - [ ] Expected behavior now works as specified
      - [ ] New tests added that would catch this bug in future
      - [ ] All tests pass (including new regression test)
      - [ ] No new bugs introduced (full test suite passes)
      - [ ] Code review confirms fix addresses root cause
      - [ ] Side effects documented and mitigated

# Success Vision

## Success from User Perspective
- [Bug no longer occurs in user's workflow]
- [Feature works as originally expected]

## Technical Success Criteria
- [All tests pass including new regression test]
- [Bug cannot be reproduced following original steps]
- [Root cause is eliminated from codebase]
```

##### Gathering Information for Bug Fix Plans

**Before creating the plan, you MUST:**

1. **Confirm Bug Exists**
   - Ask user to provide evidence (logs, screenshots, steps)
   - Try to reproduce the bug yourself in the codebase
   - Verify it's actually a bug, not expected behavior

2. **Get Reproduction Steps**
   - If user provides vague report, ask for specific steps
   - Clarify preconditions (environment, data state, user state)
   - Ask about consistency (always? sometimes? rare?)

3. **Investigate Root Cause**
   - Use code search to find relevant code sections
   - Read the code to understand why bug occurs
   - Trace logical flow from trigger to symptom
   - **CRITICAL**: Find the EXACT file and line numbers

4. **Determine Fix Approach**
   - Identify the minimal change that fixes root cause
   - Consider side effects and risks
   - Look for similar patterns in codebase (how were similar issues fixed?)

**Clarification Questions for Bug Reports**:
```
When user reports a bug, ask:
1. "Can you provide the exact steps to reproduce this bug?"
2. "What do you see happening? What did you expect to see instead?"
3. "Do you have any error messages, logs, or screenshots?"
4. "Does this happen every time, or only sometimes?"
5. "What environment are you using? (browser, OS, app version)"
```

##### Quality Checklist for Bug Fix Plans

Before requesting plan-reviewer, verify:

- [ ] **Bug Existence Proven**
  - Current behavior is observable and specific
  - Expected behavior is clearly different
  - Evidence provided (logs/screenshots/reports)

- [ ] **Reproduction Steps Complete**
  - Step-by-step instructions provided
  - Preconditions specified
  - Reproducibility rate stated

- [ ] **Root Cause Identified**
  - Exact code location specified (file:line)
  - Technical explanation of WHY bug occurs
  - Logical flow traced from trigger to symptom

- [ ] **Fix Direction Sound**
  - Fix strategy clearly stated
  - Files and code locations specified
  - Implementation sketch shows key change
  - Explanation of why fix works
  - Side effects and risks acknowledged

**plan-reviewer will REJECT if ANY of these is missing or insufficient.**

##### Common Mistakes to Avoid

**Mistake 1: Describing symptoms instead of root cause**
- [FAIL] Bad: "The page crashes when user clicks submit"
- [PASS] Good: "In `FormHandler.ts:145`, `handleSubmit()` calls `validateEmail()` with undefined when email field is empty, causing null pointer exception"

**Mistake 2: Vague reproduction steps**
- [FAIL] Bad: "Try to submit the form"
- [PASS] Good: "1. Navigate to /profile, 2. Click Edit, 3. Clear email field, 4. Click Save, 5. Observe 500 error"

**Mistake 3: Missing evidence**
- [FAIL] Bad: "Users reported the bug"
- [PASS] Good: "Error in logs/production-2024-01-15.log:450-455: `TypeError: Cannot read property 'value' of undefined`"

**Mistake 4: Vague fix direction**
- [FAIL] Bad: "Fix the validation"
- [PASS] Good: "Add null check in `validateEmail()` at line 145: `if (!email) return { error: 'Email required' }`"

**Mistake 5: No side effects consideration**
- [FAIL] Bad: "Just add the validation middleware"
- [PASS] Good: "Add validation middleware. Risk: May reject partial PATCH updates. Mitigation: Configure middleware to allow partial data for PATCH."

#### 2.4 Reference Quality Guidelines

**The key question: "Can a worker open this file, search for this concept, and trace to everything they need?"**

##### Reference Quality Levels

**Level 1: Minimal (File Path Only) - [FAIL] Usually Insufficient**
```
- [ ] Add authentication
  - Reference: See `auth/login.ts`
```
**Problem**: No starting point within file, no guidance on what to look for.

**Level 2: Basic (File Path + Searchable Concept) - [PASS] Sufficient for Simple Tasks**
```
- [ ] Add timestamp field to User model
  - Reference: `models/Product.ts` (search for `@Column` decorator, look at timestamp field like `last_updated`)
  - Follow the same decorator approach with `nullable: true` option
```
**Good for**: Straightforward patterns, standard framework usage, simple modifications.
**Worker can**: Read the file, search for the concept, see the pattern, copy and adapt.

**Level 3: Detailed (File Path + Searchable Concept + Context) - [PASS] Recommended for Most Tasks**
```
- [ ] Implement JWT authentication for API endpoints
  - Reference: `auth/oauth.ts` (search for token validation middleware, find error handling for expired tokens)
  - What to understand: Middleware chain pattern, token refresh logic
  - Adaptation needed: Use JWT instead of OAuth2, shorter token expiry (15min vs 1hr)
  - Integration: Apply middleware to routes in `api/routes.ts` (search for `router.use` middleware patterns)
```
**Good for**: Standard features with some complexity, common patterns that need adaptation.
**Worker can**: Read file, search concept, understand pattern, see how to integrate, know what to adapt.

**Level 4: Comprehensive (File + Context + Code Snippet) - [PASS] Required for Complex Tasks**
```
- [ ] Implement optimistic UI update with rollback on error
  - Reference: `store/posts.ts` (search for `deletePost` function, examine optimistic update pattern)
  - Business logic: Update UI immediately, show success state, but rollback if API fails
  - Code pattern to follow:
    ```typescript
    // From store/posts.ts deletePost function
    async function deletePost(id: string) {
      // 1. Optimistically remove from UI
      dispatch({ type: 'POST_DELETE_OPTIMISTIC', payload: id });

      try {
        // 2. Call API
        await api.deletePost(id);
        // 3. Confirm deletion
        dispatch({ type: 'POST_DELETE_SUCCESS', payload: id });
      } catch (error) {
        // 4. Rollback on error
        dispatch({ type: 'POST_DELETE_ROLLBACK', payload: id });
        showErrorToast(error.message);
      }
    }
    ```
  - Why snippet needed: Multi-step flow, error handling, state synchronization not obvious from file alone
```
**Good for**: Complex interactions, multi-step flows, non-obvious patterns, subtle details.
**Worker can**: See complete pattern, understand all steps, copy structure, adapt details.

##### When to Include Code Snippets

**Include code snippet when:**
- Pattern involves multiple coordinated steps
- Pattern has subtle details that might be missed
- Pattern requires understanding interaction between pieces
- Pattern is project-specific and non-standard
- Worker needs to see exact structure to replicate

**Skip code snippet when:**
- Pattern is straightforward (single function, simple change)
- Pattern follows standard framework conventions
- File reference + searchable concept makes pattern obvious
- Worker can trace pattern by reading file naturally

**Decision Matrix:**

| Task Complexity | File Reference | Searchable Concept | Code Snippet |
|----------------|----------------|-------------------|--------------|
| Simple (add field, import module) | Required | Required | Skip |
| Moderate (implement endpoint, add validation) | Required | Required | Optional |
| Complex (optimistic updates, multi-step flow) | Required | Required | Required |

##### Examples: Good vs Bad References

**Example 1: Simple Task - Good Reference**
```
- [ ] Add `last_login` field to User model
  - Reference: `models/Product.ts` (search for `@Column` decorator usage, examine timestamp field patterns like `last_updated`)
  - Use same pattern: decorator with `{ type: "timestamp", nullable: true }` options
  - Test pattern: `tests/models/Product.test.ts` (search for timestamp field tests)
```
[PASS] **Why good**: Worker can search file, find pattern, understand approach. No snippet needed.

**Example 2: Simple Task - Bad Reference**
```
- [ ] Add authentication to the API
  - Reference: Various files in `auth/` directory
```
[FAIL] **Why bad**: No specific file, no search keyword, no guidance. Worker must search and guess.

**Example 3: Complex Task - Good Reference**
```
- [ ] Implement webhook event handling with retry logic
  - Reference: `webhooks/github.ts` (search for `handleWebhook` function, examine signature verification and retry pattern)
  - Business logic: Verify signature, process event, retry on failure (3 attempts, exponential backoff)
  - Key pattern:
    ```typescript
    async function handleWebhook(req: Request) {
      // 1. Verify signature (critical for security)
      if (!verifySignature(req.headers, req.body)) {
        return res.status(401).json({ error: 'Invalid signature' });
      }

      // 2. Process with retry
      await retryWithBackoff(
        () => processEvent(req.body),
        { attempts: 3, baseDelay: 1000 }
      );
    }
    ```
  - Adaptation: Use Stripe signature verification instead of GitHub's
  - Integration: Add route in `api/webhooks/stripe.ts`, use existing `retryWithBackoff` from `utils/retry.ts`
```
[PASS] **Why good**: Complex flow, security-critical, non-obvious steps → snippet clarifies. Searchable concept provided.

**Example 4: Complex Task - Bad Reference**
```
- [ ] Implement webhooks properly
  - Reference: `webhooks/github.ts`
```
[FAIL] **Why bad**: No searchable concept, no explanation of what "properly" means, no business logic documented.

### Phase 3: Review Processing (ALWAYS, MUST)

**CRITICAL**: The plan-reviewer requires ONLY the file location. DO NOT mention:
- "This is my first draft"
- "I reflected your feedback"
- "This is the Nth revision"
- Any other context about iterations or improvements

The reviewer will REJECT any submission that includes such information.

1. **Request Review from plan-reviewer**
   ```python
   Task(
       subagent_type="sisyphus:plan-reviewer",
       description="Review work plan",
       prompt="@./ai-todolist.md"
   )
   ```

2. **Incorporate Feedback**
   - Complete if approved ("OKAY")
   - Modify plan and re-review if improvements requested
   - **Infinite Loop until "OKAY"**
     - ALWAYS send ONLY the file path: `"@./ai-todolist.md"`
     - NEVER add context about revisions, feedback, or iterations

### Phase 4: Edit Mode Processing (If Editing Existing Plan)

When modifying existing plan:

1. **Read Existing Plan**
   Read `./ai-todolist.md`

2. **Identify Modification Scope**
   - Analyze user requests
   - Identify sections needing changes

3. **Update Plan**
   - Maintain existing structure while modifying only necessary parts
   - Reflect new requirements
   - Update progress status

### Phase 5: Final Output

1. **Save Plan**
   - Write to `./ai-todolist.md`
   - Use standard template for new plans
   - Preserve structure for edited plans

2. **Create TodoWrite Items**
   - Add each implementation step as a todo
   - Format: Clear, actionable items
   - Workers will check these off during execution

3. **Commit Plan to Git**
   ```bash
   git add ai-todolist.md
   git commit -m "plan: create work plan"
   ```
   - Commits the finalized plan to the branch

4. **GitHub CI: Push Branch to Remote**

   **Only execute this step if running in GitHub CI environment** (check for `GITHUB_ACTIONS` or `CI` environment variables):

   ```bash
   # Get current branch name
   BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)

   # Push branch to remote
   git push -u origin "$BRANCH_NAME"
   ```

   - Pushes the plan-writer branch to remote for further processing
   - This allows the subsequent workflow (sisyphus-trigger) to access the plan

5. **Success Report**
   - Confirm plan saved to `./ai-todolist.md`
   - State number of action items created
   - Report language used in the plan (Korean/English/etc.)
   - **GitHub CI only**: Report branch name and push status
   - Provide next steps for execution

   Example report:
   ```
   Plan creation complete!

   * Plan file: ./ai-todolist.md
   * Total action items: N
   * Language: English
   * Branch: plan-writer/YYYYMMDD-HHMMSS
   * Status: ✅ Pushed to remote

   The plan is ready for execution.
   ```

## Quality Checklist

**Before finalizing the plan, verify ALL of these criteria:**

### Criterion 1: Clarity of Work Content

- [ ] **Every task specifies WHERE to find implementation details**
  - File paths with searchable concepts (e.g., `models/User.ts` - search for `@Column` decorator patterns)
  - URLs with searchable sections (e.g., `https://example.com/docs` - find "JWT creation" section)
  - Code snippets when patterns are complex or non-obvious
- [ ] **90%+ of information accessible from referenced sources**
  - Workers can find what they need by searching referenced files
  - References provide clear search keywords and concepts
  - Referenced files contain the claimed patterns
- [ ] **No vague instructions without reference sources**
  - No "add authentication" without saying where/how
  - No "improve performance" without concrete targets

### Criterion 2: Verification & Acceptance Criteria

- [ ] **Every task has concrete, measurable success criteria**
  - Executable validation commands (tests, builds, curl)
  - Expected outputs clearly specified
  - Observable outcomes (UI elements, API responses, metrics)
- [ ] **No subjective success criteria**
  - No "properly", "correctly", "good enough"
  - No "clean code", "good UX", "robust implementation"
- [ ] **Failure scenarios addressed**
  - What to do when tests fail
  - How to debug common issues
  - Retry strategies for flaky operations

### Criterion 3: Context Completeness

- [ ] **90% confidence threshold met (≤10% guesswork)**
  - Workers can proceed without external research
  - Ambiguities minimized to acceptable level
- [ ] **Worker can START work from provided references (no extensive searching needed)**
  - Each task provides clear file path + searchable concept
  - Worker can open file and search to find starting point
  - Referenced patterns are findable through logical search
- [ ] **Business logic is explicit (not implicit)**
  - What feature does, why it works certain way is documented
  - Desired behavior from user perspective is clear
  - No assumptions about requirements or expected outcomes
- [ ] **Architectural decisions are stated (not assumed)**
  - Which pattern to use, how systems integrate is clear
  - State management approach specified (Redux/Context/Local)
  - Error handling strategy documented (Toast/Inline/Redirect)
  - No guessing about which approach to take
- [ ] **Implicit assumptions stated explicitly**
  - Authentication state, data flow, async handling clarified
  - Architecture constraints documented (SSR, browser APIs, etc.)
- [ ] **Edge cases handled**
  - Empty lists, loading states, errors, timeouts addressed
  - Concurrent edit conflicts, network failures covered
- [ ] **Integration points clarified**
  - How to access shared services (auth, analytics, feature flags)
  - Data formats and API contracts specified
- [ ] **No project-specific conventions left undocumented**
  - Custom patterns unique to this codebase are explained
  - References to "how we do things here" are backed by file citations with search concepts
  - Commit message style, testing conventions, code organization documented

### Criterion 4: Big Picture & Workflow Understanding

- [ ] **Purpose statement present (WHY)**
  - Business value or user problem clearly explained
  - Motivation for work stated upfront
- [ ] **Background context provided (WHAT)**
  - Current state described
  - What we're changing and why
- [ ] **Task flow & dependencies clear (HOW)**
  - Dependencies explicitly mapped
  - Sequence and logical connections explained
  - Parallel vs sequential execution justified
- [ ] **Success vision defined**
  - Product/user perspective on "done" state
  - Business outcomes beyond "code works"
  - Measurable success metrics

### Information Fidelity

- [ ] **File paths are accurate and exist in project**
- [ ] **Searchable concepts are findable in referenced files**
  - Keywords/concepts mentioned actually exist in the files
  - Worker can grep/search for them successfully
- [ ] **Commit conventions reflected**
  - Commit message format matches project style
  - Branching strategy aligned with team practices
- [ ] **Tech stack accurately identified**
  - Libraries and versions correct
  - Framework conventions understood

### Language Consistency

- [ ] **Entire plan matches user's request language**
  - Korean request → Korean plan
  - English request → English plan
  - Consistent throughout (no mixing)

## Core Constraints

1. **Information Gathering First**: Sufficient project analysis before planning
2. **Practical Approach**: Focus on actual implementation over theory
3. **90% Confidence Threshold**: Workers should NOT need external research beyond natural code exploration
4. **Verifiability**: All steps must be objectively testable
5. **Maintain Existing Patterns**: Keep project's existing style
6. **Big Picture First**: WHY, WHAT, HOW before diving into tasks

## Success Indicators

Plan creation is complete when:
- Plan is saved to `./ai-todolist.md`
- All phases are properly structured with the standard template
- Each TODO item has clear verification criteria with:
  - Concrete reference sources (file paths with searchable concepts, URLs, code snippets)
  - Measurable acceptance criteria
  - Complete context (90% confidence threshold)
- Big picture is clear (WHY, WHAT, HOW, Success Vision)
- Project conventions are accurately reflected
- Language is consistent with user's request
- User can immediately begin execution by following the plan

## GitHub CI Context Handling

**When execution context is GitHub CI/CD environment:**

### Context Recognition
Identify GitHub CI execution by:
- Environment variables (GITHUB_ACTIONS, CI, etc.)
- Presence of workflow run context
- Issue/PR references in conversation history

### Communication Protocol
1. **Review All Conversation History**
   - Read all prior comments and discussions on the issue/PR
   - Understand full context of user requests and team discussions
   - Identify any prior decisions or constraints mentioned

2. **Use GitHub Comments for Communication**
   - Post clarifying questions as GitHub comments
   - Wait for user responses via comments
   - Document all clarifications in the conversation thread

3. **Adapt Workflow for Asynchronous Communication**
   - Structure questions to minimize back-and-forth rounds
   - Group related questions together
   - Provide multiple options when applicable to speed up decision-making

4. **Reference GitHub Context**
   - Link to specific code lines when discussing implementation
   - Reference previous commits or PRs when relevant
   - Use GitHub's markdown features for clear communication

**Key Principle**: In GitHub CI context, treat comments as the primary communication channel, not real-time chat. Be comprehensive in each interaction to account for asynchronous response times. And always write the full ai-todolist.md file as a single comment.
