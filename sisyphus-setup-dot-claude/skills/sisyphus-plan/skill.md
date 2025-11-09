---
name: plan-writer-yaml
description: Create YAML format work plans saved as .sisyphus/tasks/{name}.yaml with strict schema validation. Analyze user requirements, gather project context, and generate structured plans with verification specs. ALWAYS includes mandatory plan-reviewer verification. Use when users request YAML-based work planning or Sisyphus-compatible task breakdown.
---

# Plan Writer (YAML)

Create systematic, actionable work plans in **YAML format** by analyzing user requirements and project context. **Every plan is automatically reviewed by plan-reviewer agent before finalization.**

## When to Use This Skill

Activate when users:
- Request to create a work plan in YAML format
- Ask for Sisyphus-compatible task breakdown
- Want to create structured implementation roadmap with verification specs
- Need plans with automated bash/LLM verification
- Request to modify existing YAML work plans
- Explicitly mention "YAML plan" or "sisyphus plan"

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

### Step 0: Essential Requirement Gathering (ABSOLUTE GATE - DO NOT SKIP)

**🚨 CRITICAL BLOCKING REQUIREMENT 🚨**

**YOU ARE ABSOLUTELY FORBIDDEN FROM PROCEEDING TO PLAN CREATION UNTIL ALL ESSENTIAL QUESTIONS ARE ANSWERED.**

This is NOT a suggestion. This is NOT optional. This is an ABSOLUTE GATE that BLOCKS all plan creation work.

**Enforcement:**
- If user provides vague answers → Ask again with specific examples
- If user skips a question → STOP and request answer before proceeding
- If user says "I don't know" → Help them think through it with guided questions
- If user tries to rush → Explain that incomplete requirements lead to failed plans

**Why this is non-negotiable:**
- Vague requirements → Vague plans → Executor makes wrong assumptions → Wasted work
- Missing constraints → Executor violates rules → Need to redo everything
- Unknown risks → Executor breaks critical systems → Production incidents
- Unclear success criteria → No way to verify completion → Endless iteration

**MANDATORY: Before ANY analysis or plan creation, ask the user these questions to gather critical requirements that MUST be documented in the plan.**

#### Question 1: Expected Outcome (Success Vision)

**Ask the user:**
```
이 작업이 완료되었을 때 기대하는 모습을 구체적으로 알려주세요.

예를 들어:
- 특정 기능이 어떻게 작동해야 하나요?
- 어떤 기술/언어로 작성되어야 하나요? (예: TypeScript로 작성되어야 합니다)
- 어떤 결과물이 나와야 하나요?
- 사용자 관점에서 어떤 경험을 제공해야 하나요?
```

**What to capture:**
- Functional requirements (feature behavior, user experience)
- Technical requirements (language, framework, architecture)
- Quality attributes (performance, security, maintainability)
- Deliverables (code, documentation, tests)

**Where to document in plan:**
- `user_request.additional[]` - **ALWAYS add**: "Expected Outcome: [full answer]"
- `objectives.core` - Core goal
- `objectives.detailed[]` - Measurable objectives
- `success_vision.user_perspective[]` - User scenarios
- `success_vision.technical_criteria[]` - Technical success criteria

#### Question 2: Forbidden Outcomes (What Must NOT Happen)

**Ask the user:**
```
이 작업이 완료되었을 때 절대 있으면 안 되는 것들을 알려주세요.

예를 들어:
- 피해야 할 코드 패턴이 있나요? (예: any 타입 사용 금지)
- 기존 기능 중 영향받으면 안 되는 부분이 있나요?
- 사용하면 안 되는 라이브러리나 접근 방식이 있나요?
- 성능 저하가 있으면 안 됩니까?
```

**What to capture:**
- Anti-patterns to avoid (code smells, bad practices)
- Regression constraints (existing features that must remain untouched)
- Forbidden dependencies (libraries, frameworks to avoid)
- Performance/security red lines (must not exceed/violate)

**Where to document in plan:**
- `user_request.additional[]` - **ALWAYS add**: "Forbidden Outcomes: [full answer]"
- `required_background.description` - Include constraints section
- `todos[].references[].inline` - Task-specific constraints
- `final_verification[]` - Verification items to check forbidden outcomes

**Example documentation:**
```yaml
required_background:
  description: |
    Technical Stack: TypeScript, React 18, Next.js 14

    CRITICAL CONSTRAINTS:
    - NO any types allowed (must use proper TypeScript types)
    - NO modification to existing auth module (src/auth/*)
    - NO new external dependencies without approval
    - NO breaking changes to public API contracts
    - Performance: API response time must stay < 200ms
```

#### Question 3: Special Concerns & Risks (What to Watch Out For)

**Ask the user:**
```
이 작업을 진행하면서 제가 특별히 주의해야 할 것들을 알려주세요.

예를 들어:
- 특정 기능을 건드릴까 봐 걱정되시나요?
- 데이터 손실 위험이 있는 부분이 있나요?
- 성능 영향을 받기 쉬운 부분이 있나요?
- 다른 팀이나 시스템과의 조율이 필요한가요?
```

**What to capture:**
- Fragile code areas (high-risk modules to handle carefully)
- Data integrity concerns (migrations, destructive operations)
- Integration points (external systems, APIs, dependencies)
- Team coordination needs (code review, approval gates)

**Where to document in plan:**
- `user_request.additional[]` - **ALWAYS add**: "Special Concerns: [full answer]"
- `background.current_situation` - Mention risky areas
- `required_background.description` - Detail concerns
- `todos[].references[].inline` - Task-specific warnings
- `workflow.dependency_diagram` - Show careful sequencing

**Example documentation:**
```yaml
background:
  current_situation: |
    Current payment system handles 10K daily transactions.

    HIGH-RISK AREAS:
    - src/payment/processor.ts handles live transactions (CRITICAL - any bug = money loss)
    - Database migration on users table (500K rows - downtime sensitive)
    - Integration with Stripe API (rate limits, webhook handling)
```

#### Question 4: Tech Stack Selection (CONDITIONAL - Ask Only for New Features)

**⚠️ IMPORTANT: This question is OPTIONAL and depends on task type.**

**DECISION LOGIC - Should I ask this question?**

```
STEP 1: Analyze the user request
→ Is this creating NEW functionality/features/modules?
  → YES: Proceed to STEP 2
  → NO: Skip Question 4 (existing tech stack is fine)

STEP 2: Check if existing tech stack handles the requirement
→ Read project's current tech stack (package.json, requirements.txt, etc.)
→ Can existing stack handle this new feature?
  → YES and sufficient: Skip Question 4
  → NO or uncertain: Proceed to STEP 3

STEP 3: Research is MANDATORY before asking
→ DO NOT ask user immediately
→ REQUIRED: Use WebSearch/WebFetch to research
→ Research these aspects:
  1. Industry-standard tech stacks for this feature type
  2. Popular libraries/frameworks (by GitHub stars, npm downloads, PyPI stats)
  3. Compatibility with existing project tech stack
  4. Pros/cons of top 2-3 options
→ ONLY AFTER research: Proceed to ask user with AskUserQuestion tool
```

**Examples of when to ASK:**
- ✅ Adding new authentication system (research: OAuth libraries, JWT vs sessions, etc.)
- ✅ Implementing real-time features (research: WebSocket vs SSE, Socket.io vs native, etc.)
- ✅ Adding payment processing (research: Stripe vs PayPal SDK, server-side vs client-side)
- ✅ Implementing data visualization (research: Chart.js vs D3.js vs Recharts)
- ✅ Adding state management to new frontend (research: Redux vs Zustand vs Jotai)

**Examples of when to SKIP:**
- ❌ Modifying existing auth endpoints (already using Passport.js → use Passport.js)
- ❌ Adding new API endpoint (already using Express → use Express)
- ❌ Fixing bug in React component (already using React → use React)
- ❌ Refactoring database queries (already using Prisma → use Prisma)
- ❌ Adding test for existing feature (already using Jest → use Jest)

**Research Process (MANDATORY before asking):**

1. **Identify Feature Category**
   ```
   Example: "Add real-time chat" → Category: Real-time communication
   Example: "Add charts" → Category: Data visualization
   Example: "Add auth" → Category: Authentication/Authorization
   ```

2. **Web Research (Use WebSearch + WebFetch)**
   ```bash
   # Execute parallel searches:
   WebSearch("best [category] libraries 2025")
   WebSearch("[category] [language] popular frameworks comparison")
   WebFetch("https://npmjs.com") → Search for category
   WebFetch("https://pypi.org") → Search for category (if Python)
   ```

3. **Gather Top 3 Options**
   - Identify 3 most popular/recommended solutions
   - Check compatibility with project's existing stack
   - Note pros/cons of each option

4. **Prepare Research Summary**
   ```
   Example summary:
   "I researched real-time communication options for your Node.js project.

   Top 3 popular choices:
   1. Socket.io (★60K GitHub stars)
      - Pros: Auto-fallback, room support, battle-tested
      - Cons: Heavier, custom protocol

   2. Native WebSocket + ws library (★20K stars)
      - Pros: Standard protocol, lightweight, simple
      - Cons: No auto-fallback, manual room management

   3. Server-Sent Events (SSE) native
      - Pros: HTTP-based, simple server→client
      - Cons: One-way only, no binary support

   For bidirectional chat, Socket.io or native WebSocket would work."
   ```

5. **Ask User with AskUserQuestion (ONLY after research)**

   ```python
   AskUserQuestion(
       questions=[
           {
               "question": "제가 실시간 채팅 기능을 위한 기술 스택을 조사했습니다. 어떤 방식을 사용하시겠습니까?",
               "header": "Tech Stack",
               "multiSelect": false,
               "options": [
                   {
                       "label": "Socket.io (가장 인기)",
                       "description": "양방향 통신, 자동 fallback, room 지원. 가장 많이 사용됨 (GitHub 60K stars)"
                   },
                   {
                       "label": "Native WebSocket",
                       "description": "표준 프로토콜, 가볍고 심플. 직접 구현 필요 (GitHub 20K stars)"
                   },
                   {
                       "label": "Server-Sent Events",
                       "description": "HTTP 기반, 서버→클라이언트 단방향만 가능. 간단한 푸시용"
                   }
               ]
           }
       ]
   )
   ```

**What to capture:**
- Selected tech stack/library/framework
- Version requirements (if specified)
- Integration approach (how it fits with existing stack)
- Any special setup needs

**Where to document in plan:**
- `user_request.additional[]` - **IF APPLICABLE, add**: "Tech Stack Decision: [full answer with rationale]"
- `required_background.description` - Tech stack section
- `required_background.references[]` - Official docs for chosen tech
- `todos[]` - Installation/setup tasks if needed
- `success_vision.technical_criteria[]` - Tech-specific success criteria

**Example documentation:**
```yaml
required_background:
  description: |
    Existing Stack: Node.js 18, Express 4, React 18, TypeScript

    NEW TECH STACK (for real-time chat):
    - Socket.io 4.x (user selected)
    - Reason: Bidirectional communication, automatic fallback, room support
    - Integration: Socket.io server on existing Express app, Socket.io client in React

  references:
    - ref_id: 'socketio-docs'
      uri: 'https://socket.io/docs/v4/'
      inline: null
```

**CRITICAL REMINDERS:**

1. **ALWAYS research BEFORE asking** - Never ask user to choose without providing researched options
2. **Use AskUserQuestion tool** - This ensures user sees formatted options with descriptions
3. **Only ask for NEW features** - Don't ask about tech stack for modifications to existing code
4. **Make it optional** - If existing stack works fine, don't force user to make a choice
5. **Document the decision** - Whatever user chooses MUST be documented in required_background

### Clarification Process (After Essential Questions)

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
   - **CRITICAL**: Ensure all essential questions are answered and documented

**🚨 ABSOLUTE BLOCKING GATE - DO NOT PROCEED 🚨**

**YOU ARE FORBIDDEN FROM STARTING PLAN CREATION UNTIL ALL OF THE FOLLOWING ARE SATISFIED:**

### Mandatory Requirements (MUST be completed):

✅ **Question 1 (Expected Outcome)** - ANSWERED
   - User has provided specific, concrete expected outcomes
   - Success criteria are clear and measurable
   - No vague statements like "make it work" or "improve performance"

✅ **Question 2 (Forbidden Outcomes)** - ANSWERED
   - User has identified constraints and anti-patterns to avoid
   - Regression boundaries are defined (what must NOT break)
   - Clear list of "must not" items documented

✅ **Question 3 (Special Concerns & Risks)** - ANSWERED
   - User has identified risky areas and concerns
   - High-risk modules/features are flagged
   - Coordination needs are clarified

### Conditional Requirement (Complete if applicable):

⚠️ **Question 4 (Tech Stack Selection)** - IF APPLICABLE
   - IF creating new features/functionality:
     - ✅ Research completed (WebSearch/WebFetch for popular options)
     - ✅ Top 3 options identified with pros/cons
     - ✅ User asked via AskUserQuestion tool
     - ✅ User's selection documented
   - IF modifying existing code with existing tech stack:
     - ⏭️ SKIP this question (not applicable)

### Additional Clarifications:

✅ **All ambiguities resolved** - User has answered follow-up questions
✅ **Requirements are concrete** - No guesswork needed (≥90% confidence)
✅ **User has confirmed understanding** - You presented summary, user agreed

---

**ENFORCEMENT PROTOCOL:**

If ANY mandatory question is unanswered or vague:
1. 🛑 **STOP IMMEDIATELY** - Do not proceed to information gathering or planning
2. 📢 **NOTIFY USER** - Explain which question needs better answer and why
3. 🔄 **RE-ASK** - Ask the question again with specific examples
4. ⏸️ **WAIT** - Do not continue until user provides satisfactory answer

**Example Enforcement Response:**
```
🚨 계획 작성을 시작할 수 없습니다

Question 2 (금지사항)에 대한 답변이 불충분합니다.

현재 답변: "그냥 잘 만들면 돼요"

이것은 구체적이지 않습니다. 명확한 제약사항이 필요합니다.

다시 질문드립니다:
이 작업 완료 후 절대 있으면 안 되는 것들을 구체적으로 알려주세요.

예를 들어:
- any 타입 사용 금지
- 기존 인증 모듈(src/auth/*) 수정 금지
- 새로운 외부 라이브러리 추가 금지
- API 응답 시간 200ms 이상 증가 금지

위와 같이 구체적으로 말씀해주세요.
```

**Why This Gate Exists:**

Without complete answers:
- ❌ Executor makes wrong assumptions → Waste time building wrong thing
- ❌ Executor violates constraints → Need to redo everything
- ❌ Executor breaks critical code → Production incidents
- ❌ No clear success criteria → Endless revisions and debates

With complete answers:
- ✅ Executor knows exactly what to build
- ✅ Executor knows exactly what to avoid
- ✅ Executor handles risks carefully
- ✅ Clear verification of success

**This gate is not negotiable. This gate saves time, prevents mistakes, and ensures quality plans.**

## Work Process

### Phase 0: Register Plan Creation Steps (ALWAYS EXECUTE FIRST)

Before starting any plan creation work, use the TodoWrite tool to register all upcoming steps:

```
Use TodoWrite to create todos for the following:
1. Analyze user request and decide: single plan vs multiple plans (CRITICAL FIRST DECISION)
2. Clarify and refine user requirements
3. Gather implementation context via massive parallel information gathering
4. Create YAML work plan draft (v3.0 format)
5. Request plan-reviewer verification (MANDATORY)
6. Incorporate reviewer feedback and iterate until "OKAY"
7. Run sisyphus plan lint to validate YAML schema (MANDATORY)
8. Fix any linter errors and re-lint until PASSED
9. Save final approved and validated plan to .sisyphus/tasks/{name}.yaml

Mark each step as 'pending' initially, then update to 'in_progress' and 'completed' as you work through them.
```

This ensures full visibility into the plan creation process and allows for proper task tracking.

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

#### 1.3 Multi-Plan Decomposition Analysis (CRITICAL FIRST QUESTION)

**Before gathering information or creating any plan, ALWAYS ask yourself:**

**"Should this user request be decomposed into multiple work plans with dependency relationships?"**

This is the FIRST and most important architectural decision. Analyze:

1. **Functional Boundaries**
   - Does the request span multiple independent features/modules?
   - Can work be naturally separated into distinct functional units?
   - Example: "Add auth + payment system" → Two plans: auth plan, payment plan

2. **Dependency Analysis**
   - Do some parts need to complete before others can start?
   - Are there clear prerequisite relationships?
   - Example: Payment system depends_on auth system being complete

3. **Size and Complexity**
   - Would a single plan exceed ~15-20 tasks?
   - Is the scope too broad for one cohesive work plan?
   - Can the work be broken into logical phases?

4. **Parallelization Opportunities**
   - Can multiple teams/workers work on different parts simultaneously?
   - Are there independent work streams that don't block each other?
   - Example: Frontend + Backend can often work in parallel

**Decomposition Decision Framework:**

```
Ask: "Does this request involve 2+ major features/modules?"
→ YES: Consider multi-plan decomposition
→ NO: Single plan is likely appropriate

Ask: "Would a single plan have 15+ tasks?"
→ YES: Look for natural split points by feature/phase
→ NO: Single plan is manageable

Ask: "Are there clear dependency chains?"
→ YES: Each chain may be a separate plan with depends_on
→ NO: Evaluate other criteria

Ask: "Can work be parallelized across teams?"
→ YES: Each parallel stream may be a separate plan
→ NO: Sequential work often fits in one plan
```

**When to Use Multiple Plans:**

✅ **USE multiple plans when:**
- Request spans 2+ major features (e.g., "auth + payments + analytics")
- Clear prerequisite dependencies exist (e.g., "API must exist before frontend can consume it")
- Total scope exceeds ~15-20 tasks when estimated
- Multiple independent work streams can progress in parallel
- Different technical domains are involved (e.g., infrastructure + application + frontend)

❌ **USE single plan when:**
- Request is focused on one feature/module
- Tasks naturally flow sequentially without major branching
- Scope is manageable (< 15 tasks estimated)
- Work is tightly coupled without clear separation points

**Multi-Plan Structure in YAML:**

When creating multiple plans, structure them in the `work_plans` array with `depends_on` relationships:

```yaml
version: '3.0'
metadata:
  created_at: "2025-11-09T00:00:00Z"
  updated_at: "2025-11-09T00:00:00Z"

work_plans:
  - id: 'plan-auth'
    name: 'Authentication System Implementation'
    depends_on: []  # No dependencies, can start immediately
    # ... rest of plan

  - id: 'plan-payment'
    name: 'Payment System Integration'
    depends_on: ['plan-auth']  # Requires auth to be complete first (same file)
    # ... rest of plan

  - id: 'plan-frontend'
    name: 'Frontend Dashboard'
    depends_on: ['plan-auth', 'plan-payment']  # Needs both auth and payment (same file)
    # ... rest of plan
```

**depends_on Format:**

The `depends_on` field supports TWO formats:

1. **Same-file reference** (simple plan ID):
   ```yaml
   depends_on: ['plan-foundation']  # References plan in same YAML file
   ```

2. **Cross-file reference** (file path + plan ID):
   ```yaml
   depends_on: ['file:backend.yaml#backend-api']  # References plan in different file
   ```

**Cross-file reference syntax:**
- Format: `file:<path>#<plan-id>`
- Path can be relative or absolute
- Example: `file:../infrastructure/database.yaml#db-setup`
- Example: `file:.sisyphus/tasks/backend.yaml#backend-api`

**Multi-file example:**

`.sisyphus/tasks/backend.yaml`:
```yaml
version: '3.0'
metadata: { ... }
work_plans:
  - id: 'backend-api'
    name: 'Backend API'
    depends_on: []  # No dependencies
```

`.sisyphus/tasks/frontend.yaml`:
```yaml
version: '3.0'
metadata: { ... }
work_plans:
  - id: 'frontend-app'
    name: 'Frontend App'
    depends_on: ['file:backend.yaml#backend-api']  # Cross-file dependency
```

**Important Notes:**

- **Document decisions**: In each plan's `background.reason_for_change`, explain why it's separate
- **Cross-plan references**: Plans can reference each other in `required_background.references`
- **Execution order**: Sisyphus executor respects `depends_on` and won't start dependent plans until prerequisites complete
- **Atomic commits**: Each plan should represent a logically complete, committable unit of work
- **File path validation**: Linter will ERROR if file path in `file:path#id` doesn't exist
- **Plan ID validation**: Linter will ERROR if plan ID doesn't exist in referenced file

**This analysis MUST happen BEFORE information gathering** - it determines what context you need to collect and how to organize your research.

#### 1.4 MASSIVE PARALLEL INFORMATION GATHERING (CRITICAL PHASE)

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
   - Read: .github/workflows/* (CI/CD patterns)
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

   **D. Codebase Exploration (Task with Explore agent) - Launch 2-4 in parallel:**
   ```
   Launch simultaneously:
   - Task(Explore): "Find all authentication-related code"
   - Task(Explore): "Locate API endpoint implementation patterns"
   - Task(Explore): "Discover testing strategies in codebase"
   - Task(Explore): "Map data flow for similar features"
   ```

   **E. Project History (Bash) - Launch 3-5 in parallel:**
   ```
   Launch simultaneously:
   - Bash: git log -20 --oneline (commit patterns)
   - Bash: git log --grep="feature" -10 (similar feature commits)
   - Bash: git diff main...HEAD --stat (recent changes)
   - Bash: find . -name "*.test.*" | head -20 (test file patterns)
   - Bash: ls -la .github/workflows/ (CI setup)
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

### Phase 2: YAML Plan Creation

#### 2.1 YAML Plan Structure (MANDATORY FORMAT)

**CRITICAL: Use ONLY this YAML structure. This is the required format with strict schema validation.**

```yaml
# Root Document Structure
version: '3.0'  # REQUIRED, string

metadata:
  created_at: "2025-11-04T00:00:00Z"  # ISO 8601 format, REQUIRED
  updated_at: "2025-11-04T00:00:00Z"  # ISO 8601 format, REQUIRED

work_plans:  # REQUIRED, list[WorkPlan] - array of work plans
  - id: 'plan-id'              # REQUIRED, string - unique plan identifier
    name: '작업 계획서 이름'     # REQUIRED, string - human-readable plan name
    depends_on: []             # REQUIRED, list[string] - array of plan IDs this depends on

    user_request:
      original: "[사용자의 정확한 최초 요청 내용]"  # REQUIRED, string
      created_at: "2025-11-04T00:00:00Z"            # REQUIRED, ISO 8601
      additional: []                                 # OPTIONAL, list[string]
        # USE THIS FIELD to document Step 0 question answers:
        # - "Expected Outcome: [Answer to Question 1]"
        # - "Forbidden Outcomes: [Answer to Question 2]"
        # - "Special Concerns: [Answer to Question 3]"
        # - "Tech Stack Decision: [Answer to Question 4 if applicable]"

    objectives:
      core: "[핵심 목표를 1-2문장으로 명확하게 설명]"  # REQUIRED, string
      detailed: []  # OPTIONAL, list of {goal: str, measurable: str}
        # - goal: "[세부 목표 설명]"
        #   measurable: "[측정 가능한 지표]"

    background:
      current_situation: "[시스템의 현재 상태, 존재하는 문제점]"  # REQUIRED, string
      reason_for_change: "[이 작업이 필요한 이유, 해결하려는 문제]"  # REQUIRED, string
      changes_to_make: "[현재 상태 → 미래 상태 명확하게 대비]"      # REQUIRED, string

    required_background:
      description: "[이 작업을 수행하는데 필요한 도메인 지식, 기술 스택 등]"  # REQUIRED, string
      file_structure: null  # OPTIONAL, string | null
      references: []  # OPTIONAL, list[ReferenceItem]
        # Example:
        # - ref_id: 'ref-docs-001'
        #   uri: 'https://docs.example.com'
        #   inline: null
        #
        # - ref_id: null
        #   uri: null
        #   inline: "Quick inline reference content"

    workflow:
      dependency_diagram: |  # REQUIRED, string (multi-line)
        Task 1 (Foundation)
           ↓
        Task 2 (depends on 1's output)
           ↓
        Task 3 || Task 4 (parallel, both depend on 2)
           ↓
        Task 5 (integration, depends on 3 & 4)
      critical_path: []  # OPTIONAL, list[string]

    success_vision:
      user_perspective: []     # OPTIONAL, list of {scenario: str, experience: str}
      business_perspective: [] # OPTIONAL, list of {metric: str, target: str}
      technical_criteria: []   # OPTIONAL, list of {category: str, criteria: str, command: str | null, expected: str}

    final_verification: []  # REQUIRED, list[FinalVerificationItem]
      # - id: "final-1"
      #   title: "Feature works end-to-end"
      #   category: "Integration"
      #   description: "User can complete full workflow"
      #   verified: false
      #   verified_at: null
      #   verification_evidence: null
      #   orchestrator_manually_verified: false  # REQUIRED
      #   manual_verification_evidence: ""       # REQUIRED
      #   bash:  # OPTIONAL (bash OR llm_judge required)
      #     - execute: "curl -X POST http://localhost:8000/api/test"
      #       expected_stdout: "success"
      #       expected_exit_code: 0
      #   llm_judge: []  # OPTIONAL

    todos:  # REQUIRED, list[Todo]
      - id: "1"           # REQUIRED, string (pattern: ^\d+(\.\d+)*$)
        title: "[Task 1 - 기능 설명]"  # REQUIRED, string
        description: null   # OPTIONAL, string | null - brief task summary
        status: pending     # REQUIRED, enum: pending | in_progress | completed
        references: []      # OPTIONAL, list[ReferenceItem]
          # - ref_id: 'ref-docs-001'
          #   uri: null
          #   inline: null
        verification_spec: []  # OPTIONAL, list[VerificationItem]
          # - id: "verify-1"
          #   title: "Test passes"
          #   description: "All tests pass"
          #   verified: false
          #   verified_at: null
          #   verification_evidence: null
          #   orchestrator_manually_verified: false  # REQUIRED
          #   manual_verification_evidence: ""       # REQUIRED
          #   bash:  # OPTIONAL (bash OR llm_judge required)
          #     - execute: "pytest tests/"
          #       expected_stdout: "passed"
          #       expected_exit_code: 0
          #       notes: null
          #   llm_judge: []  # OPTIONAL
        children: null      # OPTIONAL, list[Todo] | null (recursive)

    references: []  # REQUIRED, list[ReferenceItem] - global references
      # - ref_id: 'ref-docs-001'
      #   uri: 'https://example.com/framework-docs'
      #   inline: null

    execution:
      started: false      # REQUIRED, boolean
      completed: false    # REQUIRED, boolean
      started_at: null    # OPTIONAL, string | null (ISO 8601)
      completed_at: null  # OPTIONAL, string | null (ISO 8601)

    work_mode:
      parallel_requested: false  # REQUIRED, boolean
      current_task_id: null      # OPTIONAL, string | null

    progress:
      total_tasks: 0      # REQUIRED, int
      completed: 0        # REQUIRED, int
      in_progress: 0      # REQUIRED, int
      pending: 0          # REQUIRED, int

    current_work: ''      # REQUIRED, string
```

#### 2.2 YAML Schema Constraints (STRICT VALIDATION)

**CRITICAL: Linter (`sisyphus plan lint`) will REJECT plans that violate these rules.**

##### Root Level Rules (PlanDocument)
- **ONLY** these 3 fields allowed at root:
  - `version`: string (REQUIRED) - e.g., "3.0"
  - `metadata`: Metadata object (REQUIRED)
  - `work_plans`: list[WorkPlan] (REQUIRED) - array of work plans
- **NO extra root fields** permitted

##### Metadata Rules
- **REQUIRED fields**:
  - `created_at`: ISO 8601 timestamp string
  - `updated_at`: ISO 8601 timestamp string or null

##### WorkPlan Rules (items in work_plans array)
- **REQUIRED fields**:
  - `id`: string - unique plan identifier
  - `name`: string - human-readable plan name
  - `depends_on`: list[string] - array of plan IDs this depends on (can be empty)
  - `user_request`: UserRequest object
  - `objectives`: Objectives object
  - `background`: Background object
  - `required_background`: RequiredBackground object
  - `workflow`: Workflow object
  - `success_vision`: SuccessVision object
  - `final_verification`: list[FinalVerificationItem]
  - `todos`: list[Todo]
  - `references`: list[ReferenceItem] (default: [])
  - `execution`: ExecutionStatus object
  - `work_mode`: WorkMode object
  - `progress`: Progress object
  - `current_work`: string (default: "")

##### ExecutionStatus, WorkMode, Progress Fields
- **ExecutionStatus** (`execution` field in WorkPlan):
  - `started`: boolean (REQUIRED)
  - `completed`: boolean (REQUIRED)
  - `started_at`: ISO 8601 string | null (OPTIONAL)
  - `completed_at`: ISO 8601 string | null (OPTIONAL)

- **WorkMode** (`work_mode` field in WorkPlan):
  - `parallel_requested`: boolean (REQUIRED)
  - `current_task_id`: string | null (OPTIONAL)

- **Progress** (`progress` field in WorkPlan):
  - `total_tasks`: int (REQUIRED)
  - `completed`: int (REQUIRED)
  - `in_progress`: int (REQUIRED)
  - `pending`: int (REQUIRED)

##### Todo ID Pattern (CRITICAL)
- **Pattern**: `^\d+(\.\d+)*$`
- **Valid**: "1", "1.1", "1.2.3", "2"
- **Invalid**: "a", "1.a", "task-1", "1-2"

##### TodoStatus Enum
- **Valid values**: `pending`, `in_progress`, `completed`
- **Invalid**: "done", "finished", "working", etc.

##### Todo Description Field
- **OPTIONAL**: `description` field in Todo is optional (string | null)
- Use `description` for brief task summary
- For detailed implementation notes, use verification context or reference materials

##### ReferenceItem Structure
- **Available fields**:
  - `ref_id`: string | null (OPTIONAL) - reference to global reference ID
  - `uri`: string | null (OPTIONAL) - external URL
  - `inline`: string | null (OPTIONAL) - inline content
- **Exclusivity rule**: `uri` and `inline` CANNOT coexist (use one or the other)
- **At least one required**: Must have at least one of `ref_id`, `uri`, or `inline`

**Inline Content Multiline Formatting:**
Use YAML literal block scalar (`|`) for multiline inline content to avoid `\n` escape sequences:

```yaml
references:
  - ref_id: 'ref-example'
    uri: null
    inline: |
      This is a multiline inline reference.

      You can include code snippets:
      ```python
      def example():
          return "Hello"
      ```

      Or detailed notes spanning multiple lines
      without using \n escape sequences.
```

##### VerificationItem Rules
- **MUST have `orchestrator_manually_verified` (boolean)**
- **MUST have `manual_verification_evidence` (string)**
- **MUST have at least ONE of**: `bash` (list) OR `llm_judge` (list)
- **BashVerification** fields:
  - `execute` (string, REQUIRED)
  - `expected_stdout`, `expected_stderr` (string | null, OPTIONAL)
  - `expected_exit_code` (int, OPTIONAL, default: 0)
  - `notes` (string | null, OPTIONAL)
- **LLMJudgeVerification** fields:
  - `instruction` (string, REQUIRED)
  - `by` (enum: "orchestrator-agent" | "external-agent", OPTIONAL, default: "orchestrator-agent")
  - `context_commands` (list[string], OPTIONAL)

##### Reference Integrity
- When using `ref_id` in ReferenceItem, the ID MUST exist in the global `references[]` array
- Linter will ERROR if ref_id references non-existent reference

##### Timestamps
- **Format**: ISO 8601 (e.g., "2025-11-04T00:00:00Z")
- **Required in Metadata**: `created_at`, `updated_at`
- **Required in UserRequest**: `created_at`

#### 2.3 Verification Spec Design (CRITICAL GUIDELINES)

**YAML plans enable AUTOMATED verification via `bash` and `llm_judge` specs. Design these carefully.**

##### Bash Verification (CONSERVATIVE APPROACH)

**⚠️ WARNING: Bash verification runs AUTOMATICALLY and can block progress if flaky.**

**When to use Bash verification:**
- [ ] Command is **deterministic** (same input → same output)
- [ ] Expected output is **100% predictable**
- [ ] No flaky tests or timing issues
- [ ] Exit code is reliable indicator of success
- [ ] Command completes quickly (< 30 seconds recommended)

**When to AVOID Bash verification:**
- ❌ Flaky tests that sometimes fail
- ❌ Commands with variable output (timestamps, random IDs, etc.)
- ❌ Long-running commands (> 1 minute)
- ❌ Commands that modify state without easy rollback
- ❌ Tests that depend on external services (network, database)
- ❌ Output format changes between runs

**Bash Verification Best Practices:**

1. **Use exit codes over output matching when possible**
   ```yaml
   bash:
     - execute: "pytest tests/unit/test_auth.py"
       expected_exit_code: 0  # Reliable: 0 = success, non-zero = failure
   ```

2. **If matching output, be VERY specific**
   ```yaml
   bash:
     - execute: "curl -s http://localhost:8000/health"
       expected_stdout: '{"status":"ok"}'  # Exact match
       expected_exit_code: 0
   ```

3. **Add notes for troubleshooting**
   ```yaml
   bash:
     - execute: "npm run build"
       expected_exit_code: 0
       notes: "If fails: check node_modules installed, check TypeScript version"
   ```

4. **Prefer unit tests over integration tests**
   - Unit tests: Fast, deterministic, isolated
   - Integration tests: Slow, flaky, environment-dependent

5. **Test specific functionality, not entire suites**
   ```yaml
   # GOOD: Specific test
   bash:
     - execute: "pytest tests/unit/test_user_model.py::test_create_user"
       expected_exit_code: 0

   # BAD: Entire suite (may include unrelated failures)
   bash:
     - execute: "pytest tests/"
       expected_exit_code: 0
   ```

**Conservative Decision Framework:**
```
Ask yourself: "Will this command ALWAYS produce this output?"
- YES + Fast (< 30s) → Use bash verification
- YES + Slow (> 30s) → Consider llm_judge or manual
- NO (variable output) → Use llm_judge or manual
- UNSURE → Default to llm_judge or manual (safer)
```

##### LLM Judge Verification (FLEXIBLE APPROACH)

**Use LLM judge when:**
- Output format varies but meaning is consistent
- Need human-like assessment (code quality, readability, etc.)
- Complex multi-step validation
- Subjective criteria (e.g., "API response is reasonable")

**LLM Judge Best Practices:**

1. **Provide clear, objective instructions**
   ```yaml
   llm_judge:
     - by: orchestrator-agent
       instruction: |
         Check if API endpoint exists by:
         1. Run: curl http://localhost:8000/api/users
         2. Verify: Response status is 200 or 201
         3. Verify: Response body is valid JSON
         4. Verify: JSON contains "users" array field
   ```

2. **Include context commands**
   ```yaml
   llm_judge:
     - by: orchestrator-agent
       context_commands:
         - "cat src/api/routes.ts"
         - "grep -r 'export.*Router' src/api/"
       instruction: "Verify that user authentication routes are properly registered"
   ```

3. **Choose appropriate judge**
   - `orchestrator-agent`: For quick checks during execution
   - `external-agent`: For thorough review requiring deep analysis

##### Combining Bash + LLM Judge

**You can use BOTH for comprehensive verification:**

```yaml
verification_spec:
  - id: "verify-api"
    title: "API endpoint works correctly"
    description: "Login API returns valid JWT token"
    orchestrator_manually_verified: false
    manual_verification_evidence: ""
    bash:
      - execute: "pytest tests/api/test_login.py"
        expected_exit_code: 0
        notes: "Fast check: test suite passes"
    llm_judge:
      - by: orchestrator-agent
        instruction: |
          Manual check:
          1. Run: curl -X POST http://localhost:8000/api/login -d '{"email":"test@example.com","password":"test"}'
          2. Verify: Response contains "access_token" field
          3. Verify: Token format is valid JWT (3 parts separated by dots)
          4. Verify: Can decode token header and payload
```

##### Verification Spec Template

```yaml
verification_spec:
  - id: "verify-implementation"
    title: "[What to verify]"
    description: "[Detailed verification criteria]"
    verified: false
    verified_at: null
    verification_evidence: null
    orchestrator_manually_verified: false  # REQUIRED
    manual_verification_evidence: ""       # REQUIRED

    # Option 1: Bash (CONSERVATIVE - use only if deterministic)
    bash:
      - execute: "[command]"
        expected_stdout: "[exact output]"  # OPTIONAL
        expected_exit_code: 0              # OPTIONAL (default: 0)
        notes: "[troubleshooting hints]"   # OPTIONAL

    # Option 2: LLM Judge (FLEXIBLE - use when output varies)
    llm_judge:
      - by: orchestrator-agent  # or: external-agent
        context_commands:       # OPTIONAL
          - "[command to gather context]"
        instruction: |
          [Clear, step-by-step verification instructions]
          1. [Step 1]
          2. [Step 2]
          3. [Success criteria]
```

#### 2.4 Plan Creation Strategy

**Core Strategy: Maximize Clarity and Minimize Ambiguity**

The goal is to achieve ≥90% worker confidence at every step. This means:

1. **Every Task Must Have Clear Reference Sources**

   For each task, provide AT LEAST ONE of:
   - **File reference with searchable concepts**: `models/User.ts` (search for `@Column` decorator, examine timestamp field patterns)
   - **URL with searchable section**: `https://stripe.com/docs/api/payment_intents` (find "Creating a PaymentIntent" section)
   - **Code snippet when pattern is complex**: Show actual code pattern when it's not obvious from reading the file

2. **Every Task Must Have Measurable Acceptance Criteria**

   - Store in `verification_spec` field using appropriate method (bash/llm_judge)
   - Follow conservative guidelines for bash verification
   - Use llm_judge for flexible, human-like assessment

3. **Provide Complete Context (90% Confidence Threshold)**

   - Store in `required_background` for global context
   - Store in `todos[].references` for task-specific context
   - Use `todos[].details` for implementation notes

4. **Big Picture Before Details**

   - Document in `objectives`, `background`, `workflow` sections
   - Ensure WHY, WHAT, HOW are clear before diving into tasks

5. **Reference-First Approach**

   - Store file references in `required_background.references[]`
   - Use `type: file` with `retrieval.keywords` for searchable concepts
   - Use `type: url` for external documentation
   - Use `type: markdown` for inline notes

6. **Worker Simulation: Test Sufficiency**

   After writing each task, simulate being the worker:
   - Can I find where to start? (Clear `references` with search keywords?)
   - Do I know WHAT to build? (Business logic in `details`?)
   - Do I know HOW to build it? (Pattern in `references`?)
   - Can I verify completion? (`verification_spec` clear and executable?)

7. **Use Proper YAML Types**
   - Strings: Use quotes for clarity
   - Booleans: `true`, `false` (lowercase)
   - Nulls: `null` (lowercase)
   - Multi-line strings: Use `|` or `>` for readability

8. **Include Explicit Commit Steps**

   **CRITICAL: After each meaningful unit of work, include a dedicated task for creating a git commit.**

   This ensures:
   - Work is properly versioned at logical checkpoints
   - Commit messages are thoughtful and descriptive
   - Code history is clean and understandable
   - Rollback points are clearly defined

   **When to add commit tasks:**
   - After completing a feature implementation
   - After fixing a bug
   - After refactoring a module
   - After adding tests
   - Before starting a new major task that depends on previous work

   **Commit task structure:**
   ```yaml
   - id: 'X.Y'
     title: 'Commit changes with appropriate message'
     description: 'Create git commit for completed work'
     status: 'pending'
     references:
       - ref_id: null
         uri: null
         inline: |
           Create a descriptive commit message following project conventions.

           Commit message should:
           - Summarize what was implemented/fixed/refactored
           - Follow conventional commits format if applicable (feat:, fix:, refactor:, etc.)
           - Include relevant context about why changes were made
           - Reference related issues or tasks if applicable

           Example:
           ```bash
           git add .
           git commit -m "feat: implement feature X

           - Add core functionality for X
           - Include comprehensive unit tests
           - Update relevant documentation
           - Ensure backward compatibility"
           ```
     verification_spec:
       - id: 'verify-X.Y-1'
         title: 'Commit created'
         description: 'Changes are committed to git with appropriate message'
         verified: false
         verified_at: null
         verification_evidence: null
         orchestrator_manually_verified: false
         manual_verification_evidence: ''
         bash:
           - execute: 'git log -1 --oneline'
             expected_stdout: null
             expected_stderr: null
             expected_exit_code: 0
             notes: 'Verify latest commit exists'
         llm_judge:
           - by: 'orchestrator-agent'
             instruction: |
               Verify that:
               1. A new commit was created
               2. Commit message is descriptive and follows project conventions
               3. All relevant changes from previous tasks are included
               4. No unrelated changes are included in this commit
             context_commands:
               - 'git log -1 --stat'
               - 'git show --name-only'
               - 'git diff HEAD~1'
   ```

   **Best practices for commit tasks:**
   - Place commit task immediately after the implementation task it commits
   - Use descriptive commit messages that explain "why" not just "what"
   - Follow project's commit message conventions (conventional commits, etc.)
   - Ensure commit includes all related changes (code + tests + docs)
   - Keep commits atomic - one logical change per commit
   - Use llm_judge to verify commit quality and completeness

### Phase 3: Mandatory Review Processing (ALWAYS EXECUTE)

**CRITICAL: Plan review by plan-reviewer agent is MANDATORY. No plan is finalized without "OKAY" approval.**

**Review Protocol:**

1. **The plan-reviewer requires ONLY the file location. DO NOT include:**
   - "This is my first draft"
   - "I reflected your feedback"
   - "This is the Nth revision"
   - Any other context about iterations or improvements

2. **Request Review from plan-reviewer**
   ```python
   Task(
       subagent_type="plan-reviewer",
       description="Review YAML work plan",
       prompt=".sisyphus/tasks/{name}.yaml"
   )
   ```

3. **Incorporate Feedback (Iterative Loop)**
   - If approved ("OKAY") → Proceed to Phase 4
   - If improvements requested → Modify plan and re-request review
   - **Infinite Loop until "OKAY"**:
     - Read reviewer feedback carefully
     - Make ALL requested changes
     - Re-submit with ONLY file path: `".sisyphus/tasks/{name}.yaml"`
     - NEVER add context about revisions
     - Repeat until reviewer responds "OKAY"

**Important Notes:**
- Review is NOT optional - it is a required quality gate
- Do NOT skip review even if you think the plan is perfect
- Plan may require multiple revision rounds - this is normal

### Phase 4: Edit Mode Processing (If Editing Existing Plan)

When modifying existing plan:

1. **Read Existing Plan**
   Read `.sisyphus/tasks/{name}.yaml`

2. **Identify Modification Scope**
   - Analyze user requests
   - Identify sections needing changes

3. **Update Plan**
   - Maintain YAML structure
   - Update only necessary fields
   - Preserve existing task IDs and structure

4. **Validate YAML**
   - Ensure schema compliance
   - Check reference integrity
   - Verify enum values

5. **Submit for Review (MANDATORY)**
   - Even edits must go through review process

### Phase 5: Final Validation and Output

**CRITICAL: This phase has TWO MANDATORY validation gates that must BOTH pass before completion.**

#### Step 1: Save Plan
- Write to `.sisyphus/tasks/{name}.yaml`
- Ensure UTF-8 encoding
- Use proper YAML indentation (2 spaces)
- Quote strings with special characters
- Use `|` for multi-line strings

#### Step 2: Run Linter (MANDATORY VALIDATION #1)

**⚠️ CRITICAL: ALWAYS run the linter after saving the plan. This is NOT optional.**

```bash
sisyphus plan lint --file .sisyphus/tasks/{name}.yaml
```

**Linter validates:**
- YAML syntax correctness
- Schema compliance (all required fields present)
- Field type correctness (string, boolean, int, list, dict)
- Todo ID pattern validity (`^\d+(\.\d+)*$`)
- TodoStatus enum values (pending/in_progress/completed)
- Timestamp ISO 8601 format
- ReferenceItem structure and integrity
- VerificationItem required fields
- No extra root fields

**Action based on linter result:**
- ✅ **If PASSED**: Proceed to success report
- ❌ **If ERRORS**:
  1. Read error messages carefully
  2. Fix ALL reported issues
  3. Re-save the plan
  4. Re-run linter
  5. Repeat until PASSED

**Common linter errors and fixes:**

| Error | Fix |
|-------|-----|
| `Missing required field: X` | Add the required field with appropriate value |
| `Invalid todo ID pattern` | Use format like "1", "1.1", "1.2.3" (digits + dots only) |
| `Invalid enum value for status` | Use only: pending, in_progress, completed |
| `Reference integrity error` | Ensure ref_id exists in global references[] |
| `Extra field at root` | Remove any fields not in schema (only version, metadata, work_plans allowed) |
| `Invalid timestamp format` | Use ISO 8601: "2025-11-09T00:00:00Z" |

**NEVER skip the linter.** Plans that pass plan-reviewer but fail linter are invalid and will cause execution errors.

#### Step 3: Success Report (Only After Lint PASSED)

```
✅ YAML plan creation complete!

📄 Plan file: .sisyphus/tasks/{name}.yaml
📋 Format: Sisyphus YAML v3.0
📊 Total tasks: N
✓ Verification specs: N bash, N llm_judge
🌐 Language: [Korean/English]
✓ Review status: ✅ APPROVED by plan-reviewer
✓ Lint status: ✅ PASSED

Ready for execution:
  sisyphus task continue --execute claude:sonnet
```

**Both validations must show ✅:**
1. ✅ APPROVED by plan-reviewer (Phase 3)
2. ✅ PASSED sisyphus plan lint (Phase 5)

Only when BOTH are satisfied is the plan truly complete and ready for execution.

## Quality Checklist

**Before requesting plan-reviewer, verify ALL criteria:**

### Criterion 1: YAML Schema Compliance

- [ ] **All 10 root fields present**
- [ ] **No extra root fields**
- [ ] **All required fields have values** (not null where required)
- [ ] **Correct field types** (string, boolean, int, list, dict)
- [ ] **Todo IDs match pattern** (`^\d+(\.\d+)*$`)
- [ ] **TodoStatus is valid enum** (pending/in_progress/completed)
- [ ] **Timestamps in ISO 8601 format**
- [ ] **ReferenceItem has valid `type`** (pointer/file/url/markdown)
- [ ] **Reference pointers exist** (ref_id points to valid ID)

### Criterion 2: Verification Spec Quality

- [ ] **Each VerificationItem has required fields**
  - `orchestrator_manually_verified` (boolean)
  - `manual_verification_evidence` (string)
- [ ] **At least ONE of bash OR llm_judge**
- [ ] **Bash specs are conservative** (deterministic, predictable)
- [ ] **Bash specs have exit codes** (preferred over output matching)
- [ ] **LLM judge instructions are clear** (step-by-step, objective)
- [ ] **No flaky bash commands** (avoid timing-dependent tests)

### Criterion 3: Clarity of Work Content

- [ ] **Every task has clear references**
  - File paths with searchable concepts
  - URLs with searchable sections
  - Code snippets when patterns are complex
- [ ] **90%+ information from references**
- [ ] **No vague instructions**

### Criterion 4: Context Completeness

- [ ] **90% confidence threshold met**
- [ ] **Business logic explicit**
- [ ] **Architectural decisions stated**
- [ ] **Edge cases documented**
- [ ] **Project conventions cited**

### Criterion 5: Big Picture

- [ ] **Purpose statement (WHY)** in `objectives.core`
- [ ] **Background context (WHAT)** in `background`
- [ ] **Task flow (HOW)** in `workflow.dependency_diagram`
- [ ] **Success vision** in `success_vision`

### Criterion 6: Language Consistency

- [ ] **Entire plan matches user's language**
- [ ] **All sections consistent** (no mixing)

## Core Constraints

1. **YAML v3.0 Format**: ONLY use Sisyphus YAML structure
2. **Schema Validation**: Pass `sisyphus plan lint` check
3. **Conservative Bash Specs**: Only deterministic commands
4. **Mandatory Review**: ALL plans need plan-reviewer "OKAY"
5. **90% Confidence**: Workers need minimal guesswork
6. **Big Picture First**: WHY, WHAT, HOW before tasks

## Success Indicators

Plan creation is complete when:
- Plan saved to `.sisyphus/tasks/{name}.yaml`
- YAML schema valid (passes linter)
- All verification specs follow guidelines (conservative bash)
- Approved by plan-reviewer ("OKAY")
- Ready for `sisyphus task continue` execution
