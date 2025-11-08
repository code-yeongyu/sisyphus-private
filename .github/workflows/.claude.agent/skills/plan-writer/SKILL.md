---
name: plan-writer
description: Analyze user requirements to create or modify systematic work plans saved as YAML files in .sisyphus/tasks/. Understand project structure, gather implementation information, and generate detailed actionable plans in v3.0 YAML format that workers can follow. ALWAYS includes mandatory plan-reviewer verification. Activate when users request work planning, task breakdown, or implementation roadmap creation.
---

# Plan Writer

Create systematic, actionable work plans by analyzing user requirements and project context. **Every plan is automatically reviewed by plan-reviewer agent before finalization.**

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

3. **Verifiability Through LLM Judge**
   - Every task MUST have LLM-based verification criteria:
     - **context_commands**: List of bash commands to gather context (grep, cat, ls, etc.)
     - **instruction**: Clear criteria for LLM to evaluate completion
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
   - Are LLM judge criteria clear and objective?
   - Can I verify completion through context gathering commands?

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

### The 4 Critical Questions Framework

**MANDATORY: Answer these 4 questions BEFORE proceeding to information gathering.**

#### Question 1: Final Deliverable Vision
**"사용자가 이 계획서대로 작업이 끝나고서 최종적으로 원하는 결과물의 모습이 무엇인가?"**

**What to identify:**
- End-state from user/product perspective (NOT just "code works")
- Observable user experience or business outcome
- Tangible artifacts that will exist after completion

**If unclear → Ask:**
- "이 작업이 완료되면 사용자는 무엇을 할 수 있게 되나요?"
- "완료 후 어떤 화면/기능/결과물이 존재해야 하나요?"
- "이 작업의 최종 산출물은 무엇인가요?"

**Example of clear answer:**
- ✅ "Users can toggle between light/dark theme using a button in the header, and their preference persists across sessions"
- ❌ "Add dark mode" (too vague - no user experience described)

#### Question 2: Concrete Success Criteria
**"1의 내용을 구체화하고 명료화된 기준으로 설명할 수 있는가?"**

**What to identify:**
- Measurable, observable outcomes
- Specific behavior descriptions (not vague goals)
- Clear boundary between "done" and "not done"

**If unclear → Ask:**
- "어떤 상태가 되면 '완료'라고 판단할 수 있나요?"
- "예를 들어 구체적인 시나리오를 말씀해주실 수 있나요?"
- "'제대로 작동한다'는 것을 어떻게 확인할 수 있나요?"

**Example of clear answer:**
- ✅ "When user clicks toggle button, theme switches within 100ms, CSS variables update, and localStorage saves the choice"
- ❌ "Theme switching works properly" (not measurable - what is "properly"?)

#### Question 3: Verification Expressibility
**"최종 검증 기준으로써 이를 표현할 수 있는가?"**

**What to identify:**
- LLM-judgeable criteria (context commands + instruction)
- Observable file states, code patterns, test outputs
- Objective pass/fail conditions

**If unclear → Ask:**
- "완료를 확인하려면 어떤 파일/코드를 확인해야 하나요?"
- "어떤 명령어를 실행하면 완료 여부를 알 수 있나요?"
- "테스트는 어떤 시나리오를 커버해야 하나요?"

**Example of clear answer:**
- ✅ "Check: 1) ThemeToggle component exists, 2) onClick handler calls theme switch function, 3) localStorage.setItem is called, 4) test file covers toggle scenarios"
- ❌ "Make sure theme works" (not verifiable - no specific checks defined)

#### Question 4: Success/Failure Boundary Definition
**"실제로 작업계획서로 만들어 진행한다면, 작업 완료를 선언할 만한 기준점은 무엇인가? 어떤 상태라면 실패이고, 어떤 상태라면 성공으로 정의할 수 있는가?"**

**What to identify:**
- **Success state**: Clear pass conditions (all must be true)
- **Failure state**: Explicit fail conditions (any makes it fail)
- **Edge cases**: Boundary scenarios and expected handling

**If unclear → Ask:**
- "어떤 경우에 '실패'라고 판단하나요? (예: 테스트 실패? 성능 기준 미달?)"
- "부분 완료는 성공인가요, 실패인가요?"
- "예외 상황(에러, 엣지케이스)은 어떻게 처리해야 하나요?"

**Example of clear answer:**
- ✅ **Success**: All tests pass + theme persists + no console errors + works in Chrome/Firefox
  **Failure**: Any test fails OR theme doesn't persist OR console errors exist
- ❌ "It should work well" (no clear success/failure criteria)

### Mandatory Clarification Gate

**CRITICAL: Do NOT proceed to Phase 1 (Information Gathering) until:**

- [ ] **Question 1 answered**: Final deliverable vision is clear (user/product outcome defined)
- [ ] **Question 2 answered**: Success criteria are concrete and measurable (no vague terms)
- [ ] **Question 3 answered**: Verification method is expressible (context commands + LLM judge criteria)
- [ ] **Question 4 answered**: Success/failure boundary is defined with examples (clear pass/fail conditions)

**If ANY checkbox is unchecked:**
1. Identify which question(s) lack clear answers
2. Formulate targeted questions for unclear areas
3. Ask user for clarification (refer to "If unclear → Ask" examples above)
4. Wait for user response
5. Update understanding and re-verify checklist
6. Repeat until all 4 questions are answerable with ≥90% confidence

### Additional Clarification Process

After completing the 4 Critical Questions, also verify:

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

### Phase 0: Detect Multi-Context & Initialize Plan Paths

**CRITICAL: Determine if request requires SINGLE file or MULTIPLE files with dependencies.**

#### Step 1: Multi-Context Detection

Analyze user request for multiple independent contexts (맥락):

**Indicators of MULTIPLE contexts:**
- Conjunction: "AND", "그리고", "또한", "ALSO"
- Independent features: "Add auth AND payments" (2 domains)
- Separate deliverables: Each can ship independently

**Examples:**
- SINGLE: "Add OAuth with Google/GitHub" → 1 file
- MULTI: "Add OAuth AND Stripe payments" → 2 files with depends_on

#### Step 2A: If SINGLE context

1. Ask for plan name:
   ```
   Plan name? (e.g., 'add-authentication')
   → .sisyphus/tasks/{name}.yaml
   ```

2. Store: `PLAN_PATH = ".sisyphus/tasks/{name}.yaml"`

#### Step 2B: If MULTI-context

1. Extract contexts and propose structure:
   ```markdown
   Detected contexts:
   1. OAuth Auth → oauth-auth.yaml
   2. Stripe Payment → stripe-payment.yaml (depends_on: [oauth-auth])

   Create separate files?
   ```

2. Store:
   ```python
   PLAN_PATHS = {
       "oauth-auth": {
           "file": ".sisyphus/tasks/oauth-auth.yaml",
           "plan_id": "oauth-authentication",
           "depends_on": []
       },
       "stripe-payment": {
           "file": ".sisyphus/tasks/stripe-payment.yaml",
           "plan_id": "stripe-integration",
           "depends_on": ["oauth-authentication"]  # uses depends_on field
       }
   }
   ```

3. For review, submit directory: `".sisyphus/tasks/"` (not single file)

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

#### 1.3 MASSIVE PARALLEL INFORMATION GATHERING (CRITICAL PHASE)

**CORE PRINCIPLE: PARALLEL EXECUTION FIRST**

🚀 **Performance Target**: Launch 15-25 parallel tool calls in a SINGLE message for maximum efficiency.

**MANDATORY PARALLEL EXECUTION STRATEGY:**

1. **Launch ALL Independent Read-Only Operations Simultaneously**
   - **NEVER execute tools sequentially during information gathering**
   - **ALWAYS use single message with multiple tool use blocks**
   - Over-fetch rather than under-fetch - gather 10x more context than initially seems necessary
   - Better to have unused context than miss critical information

2. **Tool Categories to Parallelize:**

   **A. File Reading (Read tool) - Launch 10-15 in parallel:**
   ```
   Launch simultaneously:
   - Read: package.json / pyproject.toml / Cargo.toml (dependencies)
   - Read: README.md / CONTRIBUTING.md (project conventions)
   - Read: .sisyphus/tasks/*.yaml (existing plan examples)
   - Read: All relevant source files identified from user request
   - Read: Test files matching the feature domain
   - Read: Configuration files (tsconfig, .eslintrc, pytest.ini, etc.)
   - Read: API route files / controller files
   - Read: Database model/schema files
   - Read: Component/module files related to feature
   - Read: Utility/helper files that might be relevant
   ```

   **B. Code Search (Grep/Glob) - Launch 5-10 in parallel:**
   ```
   Launch simultaneously:
   - Grep: Search for similar feature implementations
   - Grep: Search for API endpoint patterns
   - Grep: Search for database query patterns
   - Grep: Search for test patterns
   - Grep: Search for error handling patterns
   - Grep: Search for validation logic
   - Glob: Find all test files matching domain
   - Glob: Find all component files in feature area
   - Glob: Find configuration files
   ```

   **C. External Context (WebFetch/mcp__zen__chat) - Launch 3-5 in parallel:**
   ```
   Launch simultaneously:
   - WebFetch: Framework documentation for key features
   - WebFetch: Library API references
   - mcp__zen__chat with perplexity: Latest best practices research
   - mcp__zen__chat with perplexity: Performance optimization patterns
   - mcp__zen__chat with perplexity: Security considerations for feature type
   ```

   **D. Project History (Bash) - Launch 3-5 in parallel:**
   ```
   Launch simultaneously:
   - Bash: git log -20 --oneline (commit patterns)
   - Bash: git log --grep="feature" -10 (similar feature commits)
   - Bash: git diff main...HEAD --stat (recent changes)
   - Bash: find . -name "*.test.*" | head -20 (test file patterns)
   - Bash: ls -la .sisyphus/tasks/ (existing plans)
   ```

3. **Information Gathering Checklist (Verify Before Moving to Phase 2):**

   Before proceeding to plan creation, ensure you have gathered:

   - [ ] **Project Structure**: README, package.json/pyproject.toml, directory structure
   - [ ] **Similar Features**: 3-5 files implementing related functionality
   - [ ] **Test Patterns**: 2-3 test files showing project testing style
   - [ ] **API/Endpoint Patterns**: Existing route/controller implementations
   - [ ] **Data Models**: Relevant schema/model definitions
   - [ ] **Configuration**: Build config, linter config, env variables
   - [ ] **Commit History**: 10-20 recent commits for message patterns
   - [ ] **External Documentation**: Framework docs, library APIs (2-3 sources)
   - [ ] **Best Practices Research**: Latest patterns from web search (2-3 queries)
   - [ ] **Architectural Context**: How feature fits into existing system
   - [ ] **Existing Plans**: Example YAML plans from .sisyphus/tasks/

   **If any checkbox is unchecked → Launch another round of parallel searches immediately**

4. **Context Extraction & Pattern Capture (During Parallel Execution):**

   As results arrive from parallel tools:
   - **CRITICAL**: Capture file paths + searchable concepts for EVERY relevant pattern
   - Note architectural decisions (SSR/CSR, sync/async, state management)
   - Document error handling approaches
   - Record testing strategies and patterns
   - Map integration points and dependencies
   - Extract project conventions (naming, structure, commit messages)
   - **CRITICAL**: Assess pattern complexity → mark which need code snippets in plan

### Phase 2: Plan Creation (v3.0 YAML Format)

#### 2.1 v3.0 YAML Plan Structure

**CRITICAL: Use YAML format, NOT Markdown**

Reference the example structure from:
- `/Users/yeongyu/local-workspaces/sisyphus/.github/workflows/.claude.agent/skills/plan-writer/references/example-work-plan.yaml`

**Core YAML Structure:**
```yaml
version: "3.0"

metadata:
  created_at: "2025-11-08T00:00:00Z"
  updated_at: "2025-11-08T00:00:00Z"

work_plans:
  - id: {plan-id}
    name: "{Plan Name}"
    depends_on: []  # List of plan IDs this depends on

    user_request:
      original: "{User's exact request}"
      created_at: "2025-11-08T00:00:00Z"
      additional:
        - "{Additional request 1}"
        - "{Additional request 2}"

    objectives:
      core: "{One-sentence core objective}"
      detailed:
        - goal: "{Specific goal}"
          measurable: "{How to measure success}"

    background:
      current_situation: "{Current state}"
      reason_for_change: "{Why this is needed}"
      changes_to_make: |
        Current: {current state}
        Target: {target state}

    required_background:
      description: "{Domain knowledge, tech stack}"
      file_structure: |
        {ASCII tree of relevant files}
      references:
        - inline: "{File path} - {searchable concept}"
        - uri: "{URL}"

    workflow:
      dependency_diagram: |
        Task 1 (Foundation)
           ↓
        Task 2 (depends on 1)
           ↓
        Task 3 || Task 4 (parallel)

      critical_path:
        - "{Phase description}"

    success_vision:
      # Links to Question 1 (Final Deliverable Vision) & Question 2 (Concrete Success Criteria)
      user_perspective:
        - scenario: "{User action}"
          experience: "{Expected outcome}"

      business_perspective:
        - metric: "{Business metric}"
          target: "{Target value}"

      technical_criteria:
        # Links to Question 3 (Verification Expressibility)
        - category: "{Category}"
          criteria: "{What to verify}"
          command: "{Optional: bash command for context}"
          expected: "{Expected result}"

    final_verification:
      # Links to Question 3 (Verification Expressibility) & Question 4 (Success/Failure Boundary)
      - id: "final-1"
        title: "{Verification title}"
        category: "{Category}"
        description: "{What to verify}"
        verified: false
        orchestrator_manually_verified: false
        manual_verification_evidence: ""
        bash: []  # No bash execution in v3.0
        llm_judge:
          - by: "orchestrator-agent"
            context_commands:
              - "cat path/to/file"
              - "grep 'pattern' path/to/file"
            instruction: |
              Verify (all must be true for success):
              1. {Criterion 1}
              2. {Criterion 2}
              3. {Criterion 3}

              Success: All criteria met
              Failure: Any criterion fails

    todos:
      - id: "1"
        title: "{Task title}"
        description: |
          {Detailed task description}
        status: pending

        references:
          - inline: "{File path} - {searchable concept}"
          - uri: "{URL}"

        children:
          - id: "1.1"
            title: "{Subtask title}"
            status: pending

          - id: "1.2"
            title: "{Subtask title}"
            status: pending

        verification_spec:
          # Links to Question 3 (Verification Expressibility) & Question 4 (Success/Failure Boundary)
          - id: "verify-1-1"
            title: "{Verification title}"
            description: "{What to verify}"
            verified: false
            verified_at: null
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash: []  # Context gathering only, no execution
            llm_judge:
              - by: "orchestrator-agent"
                context_commands:
                  - "cat {file}"
                  - "grep '{pattern}' {file}"
                instruction: |
                  Verify (all must be true for success):
                  1. {Check 1}
                  2. {Check 2}

                  Success: All checks pass
                  Failure: Any check fails

    references: []  # Global references

    execution:
      started: false
      completed: false
      started_at: null
      completed_at: null

    work_mode:
      parallel_requested: false

    progress:
      total_tasks: 0
      completed: 0
      in_progress: 0
      pending: 0

    current_work: ""
```

#### 2.2 LLM Judge Verification Pattern

**CRITICAL: Use llm_judge for verification, NOT bash execution**

**Correct Pattern:**
```yaml
verification_spec:
  - id: "verify-1-1"
    title: "Feature X is implemented correctly"
    description: "Verify implementation follows project patterns"
    verified: false
    verified_at: null
    orchestrator_manually_verified: false
    manual_verification_evidence: ""
    bash: []  # Empty or context-gathering commands only
    llm_judge:
      - by: "orchestrator-agent"
        context_commands:
          - "cat src/components/ThemeToggle.tsx"
          - "grep -A 10 'const toggleTheme' src/hooks/useTheme.ts"
          - "ls -la tests/components/"
        instruction: |
          Verify the implementation meets these criteria:

          1. Does ThemeToggle component exist at src/components/ThemeToggle.tsx?
          2. Does it export a default React component?
          3. Does clicking the toggle call the theme switch function?
          4. Are CSS custom properties updated on theme change?
          5. Is localStorage.setItem('theme', ...) called?
          6. Does test file exist at tests/components/ThemeToggle.test.tsx?

          Success criteria: All 6 items must be true.
```

**WRONG Pattern (DO NOT USE):**
```yaml
# ❌ WRONG - Do not use bash execution expectations
verification_spec:
  - id: "verify-1-1"
    bash:
      - execute: "npm test -- ThemeToggle"
        expected_exit_code: 0
        expected_output: "3/3 tests pass"
```

**Context Commands Guidelines:**
- Use bash commands to **gather context only** (cat, grep, ls, find, etc.)
- LLM evaluates the gathered context against criteria
- Commands should be **read-only** (no side effects)
- Provide enough context for LLM to make informed judgment

**Instruction Guidelines:**
- Be specific and measurable
- List clear numbered criteria
- Define what "success" means
- Avoid subjective terms ("properly", "correctly", "well")

#### 2.3 Plan Creation Strategy

**Core Strategy: Maximize Clarity and Minimize Ambiguity**

The goal is to achieve ≥90% worker confidence at every step. This means:

1. **Every Task Must Have Clear Reference Sources**

   For each task, provide AT LEAST ONE of:
   - **File reference with searchable concepts**: `models/User.ts` (search for `@Column` decorator, examine timestamp field patterns)
   - **URL with searchable section**: `https://stripe.com/docs/api/payment_intents` (find "Creating a PaymentIntent" section)
   - **Code snippet when pattern is complex**: Show actual code pattern when it's not obvious from reading the file

   [FAIL] **BAD**: "Add OAuth login"
   [PASS] **GOOD**: "Add OAuth login following the pattern in `auth/google.ts` (search for `AuthProvider` interface implementation, examine session storage mechanism usage)"

2. **Every Task Must Have LLM Judge Verification**

   Provide CLEAR verification with:
   - **context_commands**: Commands to gather relevant files/outputs
   - **instruction**: Numbered criteria for LLM to evaluate
   - **Observable outcomes**: "Toggle button appears in header (top-right)"

   [FAIL] **BAD**: "Make sure it works properly"
   [PASS] **GOOD**:
   ```yaml
   llm_judge:
     - by: "orchestrator-agent"
       context_commands:
         - "cat src/components/DarkModeToggle.tsx"
         - "cat tests/components/DarkModeToggle.test.tsx"
         - "grep 'localStorage' src/components/DarkModeToggle.tsx"
       instruction: |
         Verify:
         1. Component exists and renders toggle UI
         2. Click handler calls theme switch function
         3. Theme changes within 100ms (check implementation)
         4. Theme persists (localStorage usage confirmed)
         5. Tests exist and cover all scenarios
   ```

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
   - YES → File path + searchable concept is sufficient (use inline reference)
   - NO → Add code snippet showing the key pattern (in description field)
   ```

6. **Worker Simulation: Test Sufficiency**

   After writing each task, simulate being the worker:

   - [ ] "Can I find where to start?" (Clear file path + searchable concept?)
   - [ ] "Do I know WHAT to build?" (Business logic clear? Desired behavior explicit?)
   - [ ] "Do I know HOW to build it?" (Architectural approach specified? Pattern clear?)
   - [ ] "Can I trace necessary information?" (References lead to full context? Can follow breadcrumbs?)
   - [ ] "Do I know WHEN it's done?" (LLM judge criteria clear? Context commands sufficient?)

   If ANY answer is uncertain → Add more context, references, or explanations.

7. **Implicit Knowledge Elimination**

   Before finalizing, check for implicit assumptions:

   - [ ] **Business Logic**: Did I document WHAT feature does and WHY?
   - [ ] **Architectural Decisions**: Did I specify WHICH approach to use?
   - [ ] **Integration Points**: Did I clarify HOW systems connect?
   - [ ] **Edge Cases**: Did I define WHAT to do in error scenarios?
   - [ ] **Project Conventions**: Did I cite WHERE conventions are documented?

   If you find yourself thinking "the worker should know this" → **Stop. Document it.**

### Phase 3: Mandatory Review Processing (ALWAYS EXECUTE)

**CRITICAL: Plan review by plan-reviewer agent is MANDATORY. No plan is finalized without "OKAY" approval.**

**Review Protocol:**

1. **The plan-reviewer requires ONLY the file location. DO NOT include:**
   - "This is my first draft"
   - "I reflected your feedback"
   - "This is the Nth revision"
   - Any other context about iterations or improvements

   The reviewer will REJECT any submission that includes such information.

2. **Request Review from plan-reviewer**
   ```python
   Task(
       subagent_type="plan-reviewer",
       description="Review work plan",
       prompt=PLAN_PATH  # Use the stored plan path variable
   )
   ```

3. **Incorporate Feedback (Iterative Loop)**
   - If approved ("OKAY") → Proceed to Phase 4
   - If improvements requested → Modify plan and re-request review
   - **Infinite Loop until "OKAY"**:
     - Read reviewer feedback carefully
     - Make ALL requested changes
     - Re-submit with ONLY file path: `PLAN_PATH`
     - NEVER add context about revisions, feedback, or iterations
     - Repeat until reviewer responds "OKAY"

**Important Notes:**
- Review is NOT optional - it is a required quality gate
- Do NOT skip review even if you think the plan is perfect
- Do NOT proceed to final output without "OKAY" from reviewer
- Plan may require multiple revision rounds - this is normal and expected

### Phase 4: Edit Mode Processing (If Editing Existing Plan)

When modifying existing plan:

1. **Read Existing Plan**
   Read the YAML file at specified path

2. **Identify Modification Scope**
   - Analyze user requests
   - Identify sections needing changes

3. **Update Plan**
   - Maintain existing YAML structure while modifying only necessary parts
   - Reflect new requirements
   - Update progress status
   - Preserve version: "3.0"

4. **Submit for Review (MANDATORY)**
   - Even edits must go through review process
   - Follow same review protocol as new plans

### Phase 5: Final Output

1. **Save Plan**
   - Write to PLAN_PATH (stored from Phase 0)
   - Use v3.0 YAML format
   - Validate YAML syntax before saving

2. **Success Report**
   - Confirm plan saved to specified path
   - State total number of todos created
   - Report language used in the plan (Korean/English/etc.)
   - Confirm plan has been reviewed and approved
   - Provide next steps for execution

   Example report:
   ```
   ✅ Plan creation complete!

   * Plan file: .sisyphus/tasks/{plan-name}.yaml
   * Format: YAML v3.0
   * Total todos: N
   * Language: English
   * Review status: ✅ Approved by plan-reviewer

   Next steps:
   1. Run: sisyphus plan lint .sisyphus/tasks/{plan-name}.yaml
   2. Run: sisyphus task continue
   ```

## Quality Checklist

**Before requesting plan-reviewer (MANDATORY), verify ALL of these criteria:**

### Criterion 1: YAML Format Compliance

- [ ] **File uses v3.0 YAML format**
  - version: "3.0" specified
  - All required fields present (metadata, work_plans, etc.)
  - Proper YAML syntax and indentation

- [ ] **No Markdown format elements**
  - No `# Headers` or `- [ ]` checkbox syntax
  - Uses YAML lists and objects
  - Proper string formatting with `|` for multiline

- [ ] **Plan saved to correct location**
  - Path is `.sisyphus/tasks/{name}.yaml`
  - NOT `./ai-todolist.md`

### Criterion 2: Clarity of Work Content

- [ ] **Every task specifies WHERE to find implementation details**
  - File paths with searchable concepts (inline references)
  - URLs (uri references)
  - Code snippets in description when complex

- [ ] **90%+ of information accessible from referenced sources**
  - Workers can find what they need by searching referenced files
  - References provide clear search keywords and concepts
  - Referenced files contain the claimed patterns

- [ ] **No vague instructions without reference sources**
  - No "add authentication" without saying where/how
  - No "improve performance" without concrete targets

### Criterion 3: LLM Judge Verification

- [ ] **Every task has llm_judge verification**
  - context_commands list bash commands for gathering context
  - instruction provides clear numbered criteria
  - NO bash execution with expected_exit_code/expected_output

- [ ] **Context commands are read-only**
  - Use cat, grep, ls, find, etc.
  - No commands with side effects
  - Provide enough context for LLM evaluation

- [ ] **Instructions are specific and measurable**
  - Numbered criteria (1, 2, 3...)
  - Observable outcomes described
  - Success defined clearly

### Criterion 4: Context Completeness

- [ ] **90% confidence threshold met (≤10% guesswork)**
  - Workers can proceed without external research
  - Ambiguities minimized to acceptable level

- [ ] **Worker can START work from provided references**
  - Each task provides clear file path + searchable concept
  - Worker can open file and search to find starting point
  - Referenced patterns are findable through logical search

- [ ] **Business logic is explicit (not implicit)**
  - What feature does, why it works certain way is documented
  - Desired behavior from user perspective is clear
  - No assumptions about requirements or expected outcomes

- [ ] **Architectural decisions are stated (not assumed)**
  - Which pattern to use, how systems integrate is clear
  - State management approach specified
  - Error handling strategy documented
  - No guessing about which approach to take

- [ ] **Implicit assumptions stated explicitly**
  - Authentication state, data flow, async handling clarified
  - Architecture constraints documented (SSR, browser APIs, etc.)

- [ ] **Edge cases handled**
  - Empty lists, loading states, errors, timeouts addressed
  - Concurrent edit conflicts, network failures covered

- [ ] **Integration points clarified**
  - How to access shared services
  - Data formats and API contracts specified

- [ ] **No project-specific conventions left undocumented**
  - Custom patterns unique to this codebase are explained
  - References backed by file citations with search concepts
  - Commit message style, testing conventions documented

### Criterion 5: Big Picture & Workflow Understanding

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

1. **v3.0 YAML Format**: Plans MUST be in YAML format, NOT Markdown
2. **LLM Judge for Verification**: Use llm_judge with context_commands, NOT bash execution
3. **Information Gathering First**: Sufficient project analysis before planning
4. **Practical Approach**: Focus on actual implementation over theory
5. **90% Confidence Threshold**: Workers should NOT need external research beyond natural code exploration
6. **Verifiability**: All steps must have LLM judge criteria
7. **Maintain Existing Patterns**: Keep project's existing style
8. **Big Picture First**: WHY, WHAT, HOW before diving into tasks
9. **Mandatory Review**: ALL plans must receive "OKAY" from plan-reviewer before finalization

## Success Indicators

Plan creation is complete when:
- Plan is saved to `.sisyphus/tasks/{name}.yaml`
- Format is YAML v3.0 (NOT Markdown)
- All todos have LLM judge verification (NOT bash execution)
- Each todo has clear reference sources (inline/uri)
- Verification uses context_commands + instruction pattern
- Big picture is clear (WHY, WHAT, HOW, Success Vision)
- Project conventions are accurately reflected
- Language is consistent with user's request
- **Plan has been reviewed and approved ("OKAY") by plan-reviewer**
- User can execute with: `sisyphus task continue`

## Command Reference

**Correct v3.0 Commands:**
- Initialize plan: `sisyphus plan init .sisyphus/tasks/{name}.yaml`
- Lint plan: `sisyphus plan lint .sisyphus/tasks/{name}.yaml`
- Execute tasks: `sisyphus task continue`
- Show current task: `sisyphus task current`
- Verify task: `sisyphus task verify llm` (LLM judge verification)

**Deprecated v2.1 Commands (DO NOT USE):**
- ❌ `sisyphus work` → Use `sisyphus task continue`
- ❌ `./ai-todolist.md` → Use `.sisyphus/tasks/{name}.yaml`
- ❌ Markdown format → Use YAML v3.0 format
