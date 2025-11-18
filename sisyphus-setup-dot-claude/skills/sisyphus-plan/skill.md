---
name: sisyphus-plan-writer
description: Create YAML format work plans saved as .sisyphus/tasks/{name}.yaml with strict schema validation. Analyze user requirements, gather project context, and generate structured plans with verification specs. ALWAYS includes mandatory plan-reviewer verification. Use when users request YAML-based work planning or Sisyphus-compatible task breakdown.
---

# Plan Writer (YAML)

Create systematic, actionable work plans in **YAML format** by analyzing user requirements and project context. **Every plan is automatically reviewed by plan-reviewer agent before finalization.**

# ALWAYS START BY FOLLOWING

Before starting any plan creation work, use the TodoWrite tool to register all upcoming steps:

```
Use TodoWrite to create todos for the following:
1. Analyze user request and decide: single plan vs multiple plans (CRITICAL FIRST DECISION)
2. Present decomposition decision to user and get confirmation
3. Initialize YAML file(s) with sisyphus-speckit plan init (N times based on decision)
4. Capture user request in YAML file(s)
5. Clarify and refine user requirements (5 essential questions)
6. Gather implementation context via massive parallel information gathering
7. Complete YAML work plan(s)
8. Request sisyphus-plan-reviewer verification (MANDATORY)
9. Incorporate reviewer feedback and iterate until "OKAY"
10. Run sisyphus-speckit plan lint to validate YAML schema (MANDATORY)
11. Fix any linter errors and re-lint until PASSED

Mark each step as 'pending' initially, then update to 'in_progress' and 'completed' as you work through them.
```

## !!MUST!! !!ALWAYS FIRST!! Init the plan file

Always init the plan file before starting the plan creation work.

```sh
sisyphus-speckit plan init --path .sisyphus/tasks/{name}.yaml --initial-request {{what user said}}
```

And then write down the user's initial request in the plan file - mandatory. the very first thing.

## Core Principles

### The 99%+ Explicitness Standard

**Every task must provide 99%+ implementation confidence using ONLY the plan document and explicitly referenced sections.**

This means:
- Workers should NOT need codebase exploration or guesswork
- All necessary context, references, and examples are embedded in the plan OR provided via structured references
- Information is either explicit in plan OR explicitly referenced with file + line numbers + key points
- Ambiguity is minimized to ≤1% (only standard language syntax and core framework APIs)

**NOT acceptable**: "Worker can discover this through code exploration"
**ACCEPTABLE**: "See auth/login.ts:20-45 for OAuth flow (key: token exchange at line 28, session storage at line 35)"

### Planning Standards

1. **Big Picture First (WHY, WHAT, HOW)**
   - **WHY**: Purpose statement (business value, user problem to solve)
   - **WHAT**: Background context (current state → what we're changing)
   - **HOW**: Task flow (dependencies, sequence, logical connections)
   - **Success Vision**: End state from product/user perspective (not just "code works")

2. **Test-First Planning (MANDATORY - CRITICAL FOR PLAN-REVIEWER APPROVAL)**
   - **CRITICAL**: Every implementation task MUST be followed by a corresponding test task
   - **Test tasks are NOT optional** - plan-reviewer will AUTOMATICALLY REJECT plans without tests
   - Test tasks must clearly specify:
     - What behaviors/scenarios to test
     - Expected outcomes for each test case
     - Test types (unit, integration, e2e) where applicable
   - Include automated verification (bash command or llm_judge)
   - Interleave test tasks with implementation (don't defer all testing to the end)

3. **Commit Planning (MANDATORY - CRITICAL FOR PLAN-REVIEWER APPROVAL)**
   - **CRITICAL**: Multi-step implementations MUST include explicit commit checkpoint tasks
   - **Commit tasks are NOT optional** - plan-reviewer will AUTOMATICALLY REJECT plans without commit strategy
   - Commit tasks must specify:
     - When to commit (after completing logical units of work)
     - What to include in the commit (feature, tests, docs)
     - Commit message strategy (conventional commits format)
   - Interleave commit tasks with implementation (Implement → Test → Commit)
   - Benefits: Clean git history, logical rollback points, incremental progress tracking

   **Example Test Task Structure:**
   ```yaml
   - id: "X.Y"
     title: "Test [feature name]"
     description: "Verify [feature] works correctly"
     status: pending
     references:
       - ref_id: null
         uri: null
         inline: |
           Test coverage required:
           1. [Scenario 1]: [Expected outcome]
           2. [Scenario 2]: [Expected outcome]
           3. [Error case]: [Expected error handling]

           Test all edge cases including:
           - Empty/null inputs
           - Invalid data
           - Success paths
           - Failure paths
     verification_spec:
       - id: "verify-X.Y-1"
         title: "All tests pass"
         description: "Test suite executes successfully"
         verified: false
         verified_at: null
         verification_evidence: null
         orchestrator_manually_verified: false
         manual_verification_evidence: ''
         bash:
           - execute: "pytest tests/test_feature.py -v"
             expected_exit_code: 0
             notes: "All test cases must pass"
   ```

3. **Explicitness Through Structured References**
   - Every task MUST provide complete information either:
     - **Explicitly in plan**, OR
     - **Via structured references** (file + line numbers + purpose + key points)
   - No vague instructions like "add authentication" without explicit guidance or structured reference
   - No expectation of codebase exploration to discover patterns

3. **Verifiability Through Measurable Criteria**
   - Every task MUST have objective completion criteria:
     - Executable commands (e.g., `npm test -- AuthModule`)
     - Expected outputs (e.g., "3/3 tests pass", "API returns 201 status")
     - Observable outcomes (e.g., "Dark mode toggle appears in header")
   - NEVER use subjective terms like "properly", "correctly", "good enough"

4. **Completeness Through Explicit or Referenced Context**
   - Make all information explicit OR provide structured references
   - Document data flows, state management, error handling strategies
   - Provide edge case handling guidance
   - Clarify architectural constraints (SSR vs client, sync vs async, etc.)

## Managing Information Density: The Reference System

When information is extensive, use **structured references** instead of expecting exploration.

### Reference Format Standard

**TIER 1: Simple Pattern Reference**
For straightforward patterns (10-30 lines):

```yaml
references:
  - file: "auth/oauth.ts"
    lines: "20-45"
    purpose: "Complete OAuth2 token exchange flow"
    key_points:
      - "Line 28: Token exchange with error retry"
      - "Line 35: Session storage in Redis"
      - "Line 40-45: Refresh token handling"
```

Worker gets: File location + what to look for + which parts matter

**TIER 2: Complex Pattern Reference**
For intricate implementations (50+ lines):

```yaml
references:
  - file: "api/pagination.ts"
    lines: "100-180"
    purpose: "Cursor-based pagination implementation"
    architecture: |
      - Encodes cursor with base64 (line 110)
      - Validates cursor format before query (line 120)
      - Returns next cursor in response (line 150)
    edge_cases:
      - "Line 130: Handle invalid cursor → return first page"
      - "Line 160: Handle last page → next cursor = null"
    integration_points:
      - "Uses db/query.ts:50 for cursor encoding"
      - "Returns format matches api/response.ts:ResponseWithCursor type"
```

Worker gets: Complete pattern understanding without reading entire file

**TIER 3: Cross-file Pattern Reference**
For patterns spanning multiple files:

```yaml
references:
  - pattern: "Error handling flow"
    files:
      - file: "middleware/error.ts"
        lines: "10-40"
        shows: "Error catching and classification"
      - file: "utils/logger.ts"
        lines: "25-35"
        shows: "Error logging format"
      - file: "api/response.ts"
        lines: "80-100"
        shows: "Error response structure"
    integration: |
      1. Middleware catches (error.ts:10)
      2. Classify by type (error.ts:20-30)
      3. Log with context (logger.ts:25)
      4. Return formatted response (response.ts:80)
```

Worker gets: Complete cross-cutting pattern without exploration

### When to Use References vs Explicit Documentation

**Always document explicitly** (never just reference):
- Business requirements (WHY feature exists, WHAT it should do)
- Architecture decisions (WHY this approach, not alternatives)
- Edge case specifications (WHAT to handle, even if reference shows HOW)
- Integration contracts (WHAT systems expect from each other)

**Use structured references for** (after explicit context above):
- Implementation patterns (HOW to implement)
- Code structures (data models, function signatures)
- Detailed algorithms (sorting, validation logic)
- Existing test patterns (test setup, assertions)

**Example - Business logic explicit, implementation referenced**:

```yaml
task:
  what: "Add rate limiting to API endpoints"
  why: "Prevent abuse and ensure fair resource usage"
  requirements:
    - 100 requests per minute per API key
    - Return 429 status when exceeded
    - Include Retry-After header
    - Reset counter every minute
  implementation_reference:
    file: "middleware/rate_limit.ts"
    lines: "50-120"
    pattern: "Token bucket algorithm implementation"
    key_points:
      - "Line 60: Token bucket with Redis"
      - "Line 85: Retry-After calculation"
      - "Line 100: Counter reset logic"
```

Worker knows WHAT/WHY explicitly, gets HOW via structured reference

### Anti-Patterns to Avoid

**❌ BAD - Vague reference expecting exploration**:
```yaml
task: "Add caching like we do elsewhere"
references:
  - file: "utils/cache.ts"  # No lines, no context
```
Problem: Worker must read entire file, guess which pattern

**❌ BAD - Reference without context**:
```yaml
task: "Implement pagination"
references:
  - file: "api/users.ts"
    lines: "200-250"  # No explanation what this shows
```
Problem: Worker must read code and reverse-engineer pattern

**❌ BAD - Expecting inference from similar code**:
```yaml
task: "Add validation following existing patterns"
# No reference at all
```
Problem: Worker must search codebase for "patterns"

**✅ GOOD - Complete information via structured reference**:
```yaml
task: "Add request validation to POST /api/products"
requirements:
  - Name required, 1-100 chars
  - Price required, positive number
  - Category optional, must exist in categories table
validation_reference:
  file: "api/users.ts"
  lines: "150-180"
  shows: "Zod validation schema pattern"
  key_points:
    - "Line 155: Required string with length"
    - "Line 160: Positive number validation"
    - "Line 170: Optional foreign key check"
  adapt_for_products: |
    - Replace 'user' with 'product' schema
    - Use categories.id for foreign key (line 170)
    - Same error format (line 175)
```
Worker has complete context, knows exactly what to adapt

### Worker-Centric Writing Philosophy

**CRITICAL: Always write from the worker's perspective. The test is: "Can a competent developer execute this task with 99%+ confidence using ONLY the plan and explicitly referenced sections?"**

#### The Core Test: "Can I Start with ZERO Exploration?"

For every task you write, simulate being the worker:

1. **Do I have explicit requirements?**
   - Is business logic stated in the plan?
   - Are architecture decisions specified?
   - Do I know what success looks like?

2. **Do I have complete implementation guidance?**
   - If pattern is needed, is it provided via structured reference?
   - Are file + line numbers + key points provided?
   - Can I implement WITHOUT exploring codebase?

3. **Do I know WHAT to build?**
   - Is the business logic explicit? (What should this feature do?)
   - Is the desired behavior explicit? (How should it work from user's perspective?)

4. **Do I know HOW to build it?**
   - Is the architectural approach specified? (Which pattern, which library, which method?)
   - Are integration points explicit? (How does this connect to existing systems?)

5. **Do I know WHEN it's done?**
   - Are success criteria measurable and objective?
   - Can I verify completion without subjective judgment?

#### What Workers MUST Get from Plan (NOT Through Exploration)

**Workers MUST get from plan (explicit or explicitly referenced):**
- **Business requirements**: What feature does, why it works certain way
- **Architectural decisions**: Which pattern to use, how systems integrate
- **Implementation patterns**: Complete pattern via structured reference (file + lines + key points)
- **Edge case handling**: How to handle errors, empty states, concurrent edits
- **Project-specific conventions**: Custom patterns unique to this codebase
- **Technical details**: Function signatures, import statements, type definitions

**The 1% allowance covers ONLY**:
- Standard language syntax (if/for/function declarations)
- Core framework APIs explicitly mentioned in plan (e.g., "use React.useState")
- Basic editor operations (saving files, formatting)

**Everything else MUST be explicit or explicitly referenced.**

#### Avoiding All Assumptions

Before writing each task, ask yourself:

- [ ] **Am I assuming the worker knows the business logic?**
  - If yes → Document it explicitly in plan
  - Example: Don't assume worker knows "payment is async via background job"

- [ ] **Am I assuming the worker knows which approach to use?**
  - If yes → Specify the architectural decision explicitly OR provide structured reference
  - Example: Don't say "add state" → Say "add to Redux store following store/auth.ts:50-80 pattern (key: createSlice usage at line 55, async thunk at line 70)"

- [ ] **Am I assuming the worker will explore to find patterns?**
  - If yes → Provide structured reference with file + lines + key points
  - Example: Don't assume worker will "find similar validation" → Provide "See api/users.ts:150-180 for Zod validation pattern (line 155: required string, line 160: positive number)"

- [ ] **Am I leaving edge cases undefined?**
  - If yes → Document how to handle them explicitly
  - Example: Don't leave empty state handling to worker's judgment → "Empty state: Show 'No items yet' message (see components/EmptyState.tsx:10-20)"

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
Please describe in detail what you expect when this work is completed.

For example:
- How should the specific feature work?
- What technology/language should it be written in? (e.g., must be written in TypeScript)
- What deliverables should be produced?
- What experience should it provide from the user's perspective?
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
Please tell me what must absolutely NOT exist when this work is completed.

For example:
- Are there code patterns to avoid? (e.g., no 'any' type usage)
- Are there existing features that must not be affected?
- Are there libraries or approaches that should not be used?
- Should there be no performance degradation?
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
Please tell me what I should be particularly careful about while working on this task.

For example:
- Are you concerned about touching certain features?
- Are there areas with risk of data loss?
- Are there areas susceptible to performance impact?
- Is coordination with other teams or systems needed?
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
               "question": "I've researched tech stacks for real-time chat functionality. Which approach would you like to use?",
               "header": "Tech Stack",
               "multiSelect": false,
               "options": [
                   {
                       "label": "Socket.io (Most Popular)",
                       "description": "Bidirectional communication, auto-fallback, room support. Most widely used (GitHub 60K stars)"
                   },
                   {
                       "label": "Native WebSocket",
                       "description": "Standard protocol, lightweight and simple. Requires manual implementation (GitHub 20K stars)"
                   },
                   {
                       "label": "Server-Sent Events",
                       "description": "HTTP-based, server→client unidirectional only. For simple push notifications"
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

#### Question 5: Existing Code/Logic Handling (MANDATORY - Ask When Scope is Unclear)

**⚠️ IMPORTANT: This question is CONDITIONAL - only ask when the user's intent about existing code is unclear.**

**DECISION LOGIC - Should I ask this question?**

```
STEP 1: Analyze the user request
→ Is this modifying/affecting existing functionality?
  → YES: Proceed to STEP 2
  → NO: Skip Question 5 (purely new feature, no existing code affected)

STEP 2: Check if handling approach is clear from request
→ Did user explicitly state how to handle existing code?
  → YES (e.g., "replace", "keep and add", "migrate"): Skip Question 5 (intent is clear)
  → NO or AMBIGUOUS: Proceed to STEP 3

STEP 3: Assess ambiguity level
→ Is it obvious what to do with existing code from context?
  → YES (clearly additive, clearly replacement, etc.): Skip Question 5
  → NO (could go either way, significant impact unclear): ASK Question 5
```

**Examples of when to ASK:**
- ✅ "Fix the authentication system" (Refactor existing? Replace? Add alongside?)
- ✅ "Improve error handling" (Keep current + add new? Replace entirely?)
- ✅ "Update the payment flow" (Migrate existing users? Parallel systems?)
- ✅ "Add OAuth login" (Keep password auth? Replace it? Both?)

**Examples of when to SKIP:**
- ❌ "Add a new settings page" (clearly new, doesn't affect existing)
- ❌ "Replace Redux with Zustand and migrate all state" (intent explicit)
- ❌ "Keep existing login, add Google OAuth as alternative" (intent explicit)
- ❌ "Fix bug in line 45 - wrong condition" (clearly targeted fix)

**Ask the user (ONLY when handling approach is unclear):**
```
How should we handle the existing code/logic?

For example:
- Keep existing implementation and add new features (parallel operation)
- Gradually migrate existing implementation to new approach
- Completely remove existing implementation and rewrite (replacement)
- Add independently without touching existing code

Specifically:
- Will existing users/data be affected?
- Is migration needed?
- Should existing functionality be preserved?
```

**What to capture:**
- Handling strategy (keep, migrate, replace, add alongside)
- Impact on existing users/data
- Migration requirements (if any)
- Backward compatibility needs
- Deprecation timeline (if replacing)

**Where to document in plan:**
- `user_request.additional[]` - **IF ASKED, add**: "Existing Code Handling: [full answer]"
- `background.current_situation` - Clearly describe what exists now
- `background.changes_to_make` - Explicitly state what happens to existing code
- `todos[]` - Include migration tasks if needed
- `success_vision.technical_criteria[]` - Backward compatibility verification if needed

**Example documentation:**
```yaml
user_request:
  additional:
    - "Existing Code Handling: Keep password auth as fallback, add OAuth as primary option. No migration needed - both systems run in parallel. Existing users keep working, new users see OAuth first."

background:
  current_situation: |
    Current auth: Email/password only (users table, bcrypt hashing).
    1,000 active users, all using password auth.

  changes_to_make: |
    ADD: OAuth (Google, GitHub) login alongside existing password auth
    KEEP: All existing password auth code (no removal, no migration)
    IMPACT: Zero - existing users unaffected, new users get more options

todos:
  - id: "1"
    title: "Add OAuth routes (new)"
  - id: "2"
    title: "Integrate OAuth with existing user table"
  - id: "3"
    title: "Add OAuth buttons to login UI (existing password form stays)"
  - id: "4"
    title: "Test backward compatibility - verify password login still works"
```

**CRITICAL REMINDERS:**

1. **Only ask when scope is UNCLEAR** - Don't ask if user already stated intent
2. **Use AskUserQuestion tool** - Present clear options for handling approach
3. **Focus on impact** - Emphasize migration needs, user impact, compatibility
4. **Document explicitly** - Whatever user chooses MUST be clear in background section
5. **No assumptions** - If unclear and significant, ASK - don't guess

### Clarification Process (After Essential Questions)

**🚨 CRITICAL PRINCIPLE: NEVER ASSUME - ALWAYS ASK WHEN UNCLEAR 🚨**

**When to Ask (Mandatory Triggers):**
- User's intent about existing code is ambiguous
- Migration/refactoring scope is undefined
- Requirements could be interpreted multiple ways
- Critical architectural decisions are implied but not stated
- Edge case handling strategies are unclear
- User impact or data migration needs are unstated

**When NOT to Ask:**
- User explicitly stated their intent
- Context makes the approach obvious
- Standard framework conventions apply
- Minor technical details that can be inferred

1. **Identify Implicit Knowledge**
   - What assumptions is the user making?
   - What domain knowledge are they assuming you already have?
   - What context from the project is not explicitly stated?
   - **NEW**: Is the scope of change to existing code clear or ambiguous?
   - **NEW**: Are migration requirements stated or assumed?

2. **Attempt Contextual Inference**
   - Can the requirement be clearly inferred from project context?
   - Are there similar features or patterns that suggest the user's intent?
   - Does the codebase structure provide enough clues?
   - **NEW**: Is the existing code handling approach obvious from context?

3. **Ask Clarifying Questions (DO NOT ASSUME)**
   When inference is insufficient, ask targeted questions:
   - "I understand you want [X]. Could you clarify [specific ambiguous point]?"
   - "Should this feature work like [similar existing feature], or differently?"
   - "What should happen when [edge case scenario]?"
   - "Are there any specific constraints or requirements I should know about?"
   - **NEW**: "How should I handle the existing [code/logic]? (Keep, migrate, replace, or add alongside?)"
   - **NEW**: "Are there migration concerns for existing users/data?"
   - **NEW**: "Should I assume backward compatibility, or is breaking change acceptable?"

4. **Iterative Refinement**
   - Present your understanding and ask for confirmation
   - Refine based on user feedback
   - Continue until the requirement is concrete and unambiguous
   - **NEW**: Explicitly confirm handling approach for existing systems

5. **Document Clarified Requirements**
   - Once clarified, document the final understood requirements
   - Include both explicit user statements and confirmed implicit assumptions
   - **CRITICAL**: Ensure all essential questions are answered and documented
   - **NEW**: Document existing code handling strategy explicitly in `background.changes_to_make`

**Examples of Proper Clarification:**

**BAD (Assumption):**
```
User: "Fix the authentication system"
Plan Writer: *assumes* this means refactoring existing code
→ Creates plan to refactor auth system
→ WRONG: User might have wanted to replace it entirely or add alongside
```

**GOOD (Clarification):**
```
User: "Fix the authentication system"
Plan Writer: "How should I handle the existing authentication system?
- Refactor and improve existing code
- Completely replace with new system (migrate existing users)
- Add new system and gradually transition"
User: "Keep existing users as-is, only new users use the new system"
Plan Writer: *documents this explicitly in plan*
→ CORRECT: Clear intent, no assumptions
```

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

### Conditional Requirements (Complete if applicable):

⚠️ **Question 4 (Tech Stack Selection)** - IF APPLICABLE
   - IF creating new features/functionality:
     - ✅ Research completed (WebSearch/WebFetch for popular options)
     - ✅ Top 3 options identified with pros/cons
     - ✅ User asked via AskUserQuestion tool
     - ✅ User's selection documented
   - IF modifying existing code with existing tech stack:
     - ⏭️ SKIP this question (not applicable)

⚠️ **Question 5 (Existing Code Handling)** - IF APPLICABLE
   - IF modifying/affecting existing functionality AND approach is unclear:
     - ✅ Analyzed user request for existing code implications
     - ✅ Determined handling approach is ambiguous (not explicitly stated)
     - ✅ User asked via AskUserQuestion tool with clear options
     - ✅ User's handling strategy documented (keep/migrate/replace/add)
     - ✅ Migration requirements clarified (if any)
     - ✅ Impact on existing users/data documented
   - IF purely new feature OR approach is explicit in request:
     - ⏭️ SKIP this question (not applicable)

### Additional Clarifications:

✅ **All ambiguities resolved** - User has answered follow-up questions
✅ **Requirements are concrete** - No guesswork needed (99%+ confidence)
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
🚨 Cannot start plan creation

Answer to Question 2 (Forbidden Outcomes) is insufficient.

Current answer: "Just make it well"

This is not specific enough. Clear constraints are needed.

Let me ask again:
Please tell me specifically what must NOT exist after completing this work.

For example:
- No use of 'any' type
- No modification of existing auth module (src/auth/*)
- No addition of new external libraries
- No increase in API response time beyond 200ms

Please provide specific details like the examples above.
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
2. Present decomposition decision to user and get confirmation
3. Initialize YAML file(s) with sisyphus-speckit plan init (N times based on decision)
4. Capture user request in YAML file(s)
5. Clarify and refine user requirements (5 essential questions)
6. Gather implementation context via massive parallel information gathering
7. Complete YAML work plan(s)
8. Request sisyphus-plan-reviewer verification (MANDATORY)
9. Incorporate reviewer feedback and iterate until "OKAY"
10. Run sisyphus-speckit plan lint to validate YAML schema (MANDATORY)
11. Fix any linter errors and re-lint until PASSED

Mark each step as 'pending' initially, then update to 'in_progress' and 'completed' as you work through them.
```

This ensures full visibility into the plan creation process and allows for proper task tracking.

### Phase 0.5: Multi-Plan Decomposition Analysis (CRITICAL FIRST DECISION)

**🚨 CRITICAL: This analysis MUST be done BEFORE initializing any files. 🚨**

**"Should this user request be decomposed into multiple work plans with dependency relationships?"**

This is the FIRST and most important architectural decision.

#### Analysis Framework

Analyze the user request across 4 dimensions:

1. **Functional Boundaries**
   - Does the request span multiple independent features/modules?
   - Can work be naturally separated into distinct functional units?
   - Example: "Add auth + payment system" → Two plans: auth plan, payment plan
   - Example: "Build full-stack app (backend + frontend)" → Two plans: backend, frontend

2. **Dependency Analysis**
   - Do some parts need to complete before others can start?
   - Are there clear prerequisite relationships?
   - Example: Payment system depends_on auth system being complete
   - Example: Frontend depends_on backend API being complete

3. **Size and Complexity**
   - Would a single plan exceed ~15-20 tasks?
   - Is the scope too broad for one cohesive work plan?
   - Can the work be broken into logical phases?
   - Example: "E-commerce platform" → Multiple plans: auth, products, cart, checkout, admin

4. **Parallelization Opportunities**
   - Can multiple teams/workers work on different parts simultaneously?
   - Are there independent work streams that don't block each other?
   - Example: Frontend + Backend can often work in parallel
   - Example: Infrastructure + Application can work in parallel

#### Decomposition Decision Framework

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

#### When to Use Multiple Plans vs Single Plan

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

#### Present Decision to User (MANDATORY)

After analysis, you MUST present your decomposition decision to the user for confirmation:

**Template for user presentation:**

```
Based on analysis, it's appropriate to divide this work into [N] independent work plans:

1. [Plan 1 Name] - [Brief description]
   - Scope: [What it covers]
   - Estimated workload: [~X tasks]

2. [Plan 2 Name] - [Brief description]
   - Scope: [What it covers]
   - Dependencies: [Depends on Plan 1] (if needed)
   - Estimated workload: [~X tasks]

[... more plans if needed ...]

Reasons for this division:
- [Reason 1: e.g., Backend and frontend can work independently]
- [Reason 2: e.g., Payment system requires auth system to be completed first]
- [Reason 3: e.g., Each plan can be managed with under 15 tasks]

Would you like to proceed with this plan?
```

**Wait for user confirmation before proceeding.**

If user confirms → Continue to Phase 0.6
If user requests changes → Adjust decomposition and present again

#### depends_on Specification (For Reference)

When creating multiple plans, you'll use `depends_on` to define relationships:

**Same-file reference** (multiple plans in one YAML):
```yaml
version: '3.0'
work_plans:
  - id: 'plan-auth'
    depends_on: []  # No dependencies
  - id: 'plan-payment'
    depends_on: ['plan-auth']  # Requires auth first
```

**Cross-file reference** (plans in separate YAMLs):
```yaml
# frontend.yaml
depends_on: ['file:backend.yaml#backend-api']
```

**Format**: `file:<path>#<plan-id>`
- Path can be relative or absolute
- Linter validates file existence and plan ID

### Phase 0.6: Initialize YAML File(s) (MANDATORY AFTER DECOMPOSITION)

**🚨 CRITICAL: This MUST be done AFTER decomposition decision is confirmed by user. 🚨**

**Why Initialize First:**
- Creates proper file structure immediately
- Captures user's exact original request before any clarification
- Enables incremental updates as we gather more information
- Ensures clean workflow: File exists → Fill gradually → Complete plan

#### Step-by-Step Process

Based on Phase 0.5 decomposition decision, initialize the appropriate number of files:

**Decision: Single Plan**
- Initialize 1 file
- Use descriptive plan name (e.g., `auth-system.yaml`, `payment-integration.yaml`)

**Decision: Multiple Plans (Same File)**
- Initialize 1 file with descriptive name covering all plans
- Example: `ecommerce-platform.yaml` (contains: auth, payment, frontend plans)
- File will have multiple items in `work_plans` array

**Decision: Multiple Plans (Separate Files)**
- Initialize N files, one per plan
- Use descriptive names for each (e.g., `backend-api.yaml`, `frontend-app.yaml`)
- Each file has 1 item in `work_plans` array

#### Initialization Steps (Repeat for Each File)

1. **Determine Plan Name(s)**
   - Use kebab-case format (e.g., `auth-system`, `payment-integration`)
   - For multiple plans in one file: use umbrella name (e.g., `ecommerce-platform`)
   - For separate files: use specific names (e.g., `backend-api`, `frontend-app`)

2. **Run sisyphus-speckit plan init (N times if needed)**
   ```bash
   # Single plan or multiple plans in one file:
   sisyphus-speckit plan init --path .sisyphus/tasks/{plan-name}.yaml

   # Multiple plans in separate files:
   sisyphus-speckit plan init --path .sisyphus/tasks/{plan-1-name}.yaml
   sisyphus-speckit plan init --path .sisyphus/tasks/{plan-2-name}.yaml
   sisyphus-speckit plan init --path .sisyphus/tasks/{plan-N-name}.yaml
   ```

3. **Read Generated File(s)**
   ```python
   Read(file_path=".sisyphus/tasks/{plan-name}.yaml")
   # Repeat for each file
   ```

4. **Fill Initial Fields in Each File**

   Update ONLY these fields at this stage:

   **For single plan OR multiple plans in one file:**
   ```yaml
   metadata:
     created_at: "{current-timestamp-ISO8601}"
     updated_at: "{current-timestamp-ISO8601}"

   work_plans:
     - id: 'plan-{name-1}'
       name: '{Human-readable plan name 1}'
       depends_on: []  # or ['plan-X'] if has dependencies
       user_request:
         original: "{User's exact initial request - do not modify a single character}"
         created_at: "{current-timestamp-ISO8601}"
         additional: []  # Will be filled during Question 1-5

     # If multiple plans in one file, add more items:
     - id: 'plan-{name-2}'
       name: '{Human-readable plan name 2}'
       depends_on: ['plan-{name-1}']  # if has dependency
       user_request:
         original: "{same user request - identical user request}"
         created_at: "{current-timestamp-ISO8601}"
         additional: []
   ```

   **For multiple plans in separate files:**
   Each file gets one work_plan item with appropriate `depends_on`:
   ```yaml
   # backend-api.yaml
   work_plans:
     - id: 'backend-api'
       depends_on: []
       user_request:
         original: "{User's exact initial request}"

   # frontend-app.yaml
   work_plans:
     - id: 'frontend-app'
       depends_on: ['file:backend-api.yaml#backend-api']  # cross-file dependency
       user_request:
         original: "{same user request - identical user request}"
   ```

5. **Save File(s)**
   ```python
   Write(file_path=".sisyphus/tasks/{plan-name}.yaml", content="{updated-yaml}")
   # Repeat for each file
   ```

6. **Validate Dependencies with plan lint (MANDATORY)**

   **🚨 CRITICAL: After setting up depends_on relationships, IMMEDIATELY run linter to validate.**

   Run `sisyphus-speckit plan lint` on each created file:
   ```bash
   # For single file or multiple plans in one file:
   sisyphus-speckit plan lint --file .sisyphus/tasks/{plan-name}.yaml

   # For multiple separate files:
   sisyphus-speckit plan lint --file .sisyphus/tasks/{plan-1}.yaml
   sisyphus-speckit plan lint --file .sisyphus/tasks/{plan-2}.yaml
   ...
   ```

   **What the linter validates:**
   - ✅ Same-file dependencies: Plan IDs exist in `work_plans` array
   - ✅ Cross-file dependencies: Referenced files exist at specified paths
   - ✅ Cross-file dependencies: Referenced plan IDs exist in target files
   - ✅ YAML schema correctness
   - ✅ No circular dependencies

   **Action based on linter result:**
   - ✅ **If PASSED**: Proceed to step 7
   - ❌ **If ERRORS**:
     - Read error messages (e.g., "Plan ID 'plan-auth' not found in backend.yaml")
     - Fix depends_on relationships or plan IDs
     - Re-save files
     - Re-run linter
     - Repeat until PASSED

   **Common dependency errors:**

   | Error                                       | Fix                                                  |
   | ------------------------------------------- | ---------------------------------------------------- |
   | `Plan ID 'plan-X' referenced but not found` | Add missing plan OR fix typo in depends_on           |
   | `File 'backend.yaml' not found`             | Fix file path OR create missing file                 |
   | `Circular dependency detected`              | Restructure depends_on to remove cycle               |
   | `Invalid depends_on format`                 | Use correct format: 'plan-id' or 'file:path#plan-id' |

7. **Announce Completion and Proceed**
   ```
   "{N} work plan files have been created:
   - .sisyphus/tasks/{plan-1}.yaml
   - .sisyphus/tasks/{plan-2}.yaml
   ...

   ✅ Dependency validation complete (sisyphus-speckit plan lint PASSED)

   Now I will ask the essential questions."
   ```
   - Proceed to Question 1-5 (Initial Requirements Clarification)
   - As each question is answered, update `user_request.additional[]` in ALL files
   - Keep files synchronized with same user requirements

#### Example Flows

**Example 1: Single Plan**
```
User: "Implement user authentication system"
Phase 0.5 Decision: Single plan (focused feature)

Phase 0.6 Execution:
1. [Run: sisyphus-speckit plan init --path .sisyphus/tasks/auth-system.yaml]
2. [Read and update with user request]
3. [Save]
4. "Work plan file has been created: auth-system.yaml"
```

**Example 2: Multiple Plans (Same File)**
```
User: "Build e-commerce platform (auth + products + payment)"
Phase 0.5 Decision: 3 plans in one file

Phase 0.6 Execution:
1. [Run: sisyphus-speckit plan init --path .sisyphus/tasks/ecommerce-platform.yaml]
2. [Read and add 3 work_plan items with depends_on relationships]
3. [Save]
4. "Work plan file has been created: ecommerce-platform.yaml (includes 3 plans)"
```

**Example 3: Multiple Plans (Separate Files)**
```
User: "Build full-stack app (backend API + frontend)"
Phase 0.5 Decision: 2 separate plans (frontend depends on backend)

Phase 0.6 Execution:
1. [Run: sisyphus-speckit plan init --path .sisyphus/tasks/backend-api.yaml]
2. [Run: sisyphus-speckit plan init --path .sisyphus/tasks/frontend-app.yaml]
3. [Update backend-api.yaml: depends_on: []]
4. [Update frontend-app.yaml: depends_on: ['file:backend-api.yaml#backend-api']]
5. [Save both]
6. "2 work plan files have been created:
   - backend-api.yaml
   - frontend-app.yaml (starts after backend-api completion)"
```

**Benefits of This Approach:**
- ✅ User's exact request captured immediately (no loss/modification)
- ✅ Files exist from start → can be viewed/tracked by user
- ✅ Incremental updates as we gather info → transparent progress
- ✅ Clean separation: Decompose → Init → Capture → Question → Fill → Complete
- ✅ Dependency relationships (`depends_on`) set up from the beginning
- ✅ No risk of forgetting user's original words after long clarification

### Phase 1: Initial Analysis and Information Gathering

**⚠️ NOTE: Phase 0.5 (Decomposition) and Phase 0.6 (Initialize YAML Files) MUST be completed before Phase 1.**

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
   - **CRITICAL**: Capture file paths + line numbers + key points for EVERY relevant pattern
   - Note architectural decisions (SSR/CSR, sync/async, state management)
   - Document error handling approaches
   - Record testing strategies and patterns
   - Map integration points and dependencies
   - Extract project conventions (naming, structure, commit messages)
   - **CRITICAL**: For EACH pattern, prepare structured reference (file + lines + purpose + key points)

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
    name: 'Work Plan Name'     # REQUIRED, string - human-readable plan name
    depends_on: []             # REQUIRED, list[string] - array of plan IDs this depends on

    user_request:
      original: "[User's exact initial request]"  # REQUIRED, string
      created_at: "2025-11-04T00:00:00Z"            # REQUIRED, ISO 8601
      additional: []                                 # OPTIONAL, list[string]
        # USE THIS FIELD to document Step 0 question answers:
        # - "Expected Outcome: [Answer to Question 1]"
        # - "Forbidden Outcomes: [Answer to Question 2]"
        # - "Special Concerns: [Answer to Question 3]"
        # - "Tech Stack Decision: [Answer to Question 4 if applicable]"

    objectives:
      core: "[Clearly explain core goal in 1-2 sentences]"  # REQUIRED, string
      detailed: []  # OPTIONAL, list of {goal: str, measurable: str}
        # - goal: "[Detailed goal description]"
        #   measurable: "[Measurable metrics]"

    background:
      current_situation: "[Current system state, existing problems]"  # REQUIRED, string
      reason_for_change: "[Why this work is needed, problems to solve]"  # REQUIRED, string
      changes_to_make: "[Clearly contrast current state → future state]"      # REQUIRED, string

    required_background:
      description: "[Domain knowledge, tech stack, etc. needed to perform this work]"  # REQUIRED, string
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
        title: "[Task 1 - Feature description]"  # REQUIRED, string
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

    current_work: ''      # REQUIRED, string
```

#### 2.2 YAML Schema Constraints (STRICT VALIDATION)

**CRITICAL: Linter (`sisyphus-speckit plan lint`) will REJECT plans that violate these rules.**

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
  - `current_work`: string (default: "")

##### ExecutionStatus, WorkMode Fields
- **ExecutionStatus** (`execution` field in WorkPlan):
  - `started`: boolean (REQUIRED)
  - `completed`: boolean (REQUIRED)
  - `started_at`: ISO 8601 string | null (OPTIONAL)
  - `completed_at`: ISO 8601 string | null (OPTIONAL)

- **WorkMode** (`work_mode` field in WorkPlan):
  - `parallel_requested`: boolean (REQUIRED)
  - `current_task_id`: string | null (OPTIONAL)

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

##### Acceptance Criteria Framework (CRITICAL FOR LLM JUDGE)

**CORE PRINCIPLE: Decompose verification into exhaustive, independent acceptance criteria.**

Every feature/task can be broken down into 5-20 specific, measurable acceptance criteria. LLM judge should verify each criterion independently, like a QA checklist.

**Why Acceptance Criteria:**
- **Explicitness**: "Button must be visible" is clearer than "button works"
- **Completeness**: Forces you to think through ALL aspects (UI, behavior, errors, edge cases, accessibility)
- **Verifiability**: Each criterion = one pass/fail check (no ambiguity)
- **Feedback loops**: Executor knows exactly what failed and how to fix it

**How to Decompose Features into Acceptance Criteria:**

1. **UI Components** (Buttons, Forms, Pages)
   - **Existence**: Component exists in correct location
   - **Visual properties**: Color, size, font, spacing match design
   - **States**: Default, hover, active, disabled, loading states render correctly
   - **Behavior**: Click/interaction triggers expected action
   - **Error handling**: Invalid inputs show proper error messages
   - **Accessibility**: ARIA labels, keyboard navigation, screen reader support
   - **Responsiveness**: Works on mobile, tablet, desktop viewports

   **Example - Login Button:**
   ```
   CRITERION 1: Button element exists at bottom of login form
   CRITERION 2: Button text is "Sign In" (not "Login" or other variants)
   CRITERION 3: Button uses primary brand color (#3B82F6)
   CRITERION 4: Button is disabled when form is invalid (empty email/password)
   CRITERION 5: Button shows loading spinner when authentication in progress
   CRITERION 6: Clicking button triggers login API call
   CRITERION 7: Successful login redirects to /dashboard
   CRITERION 8: Failed login displays error message below button
   CRITERION 9: Button has aria-label="Sign in to your account"
   CRITERION 10: Button is keyboard accessible (Enter key works)
   ```

2. **API Endpoints**
   - **Request handling**: Accepts correct HTTP method and content-type
   - **Authentication**: Requires valid auth token, rejects unauthorized requests
   - **Input validation**: Validates required fields, data types, formats
   - **Success response**: Returns correct status code (200/201/204) and data structure
   - **Error responses**: Returns appropriate error codes (400/401/404/500) with messages
   - **Side effects**: Database updates, event triggers, notifications work correctly
   - **Performance**: Responds within acceptable time (e.g., < 200ms)
   - **Idempotency**: Repeated requests don't cause duplicate effects (for POST/PUT)

   **Example - POST /api/users (Create User):**
   ```
   CRITERION 1: Endpoint accepts POST requests to /api/users
   CRITERION 2: Requires Content-Type: application/json header
   CRITERION 3: Requires valid JWT token in Authorization header
   CRITERION 4: Rejects requests without auth token (returns 401)
   CRITERION 5: Validates email format (returns 400 if invalid)
   CRITERION 6: Validates password strength (min 8 chars, returns 400 if weak)
   CRITERION 7: Returns 409 Conflict if email already exists
   CRITERION 8: On success, returns 201 with user object { id, email, created_at }
   CRITERION 9: Hashes password with bcrypt before storing (never stores plaintext)
   CRITERION 10: Sends welcome email to user after account creation
   CRITERION 11: Response includes Location header with /api/users/{id}
   CRITERION 12: Duplicate POST with same email returns existing user (idempotent)
   ```

3. **Business Logic / Algorithms**
   - **Core functionality**: Main algorithm produces correct output for valid inputs
   - **Edge cases**: Handles boundary values (0, negative, MAX_INT, empty, null)
   - **Error conditions**: Throws/returns appropriate errors for invalid inputs
   - **State transitions**: Moves through expected states correctly
   - **Data integrity**: Maintains consistency (no partial updates, no data loss)
   - **Concurrency**: Handles simultaneous operations correctly (no race conditions)

   **Example - Shopping Cart Discount Calculation:**
   ```
   CRITERION 1: 10% discount applies when cart total ≥ $100
   CRITERION 2: No discount when cart total < $100
   CRITERION 3: Discount rounds to 2 decimal places (e.g., $10.99 not $10.9876)
   CRITERION 4: Discount applies BEFORE tax calculation
   CRITERION 5: Discount code "SAVE20" overrides percentage (20% instead of 10%)
   CRITERION 6: Invalid discount code is rejected with clear error message
   CRITERION 7: Expired discount codes are rejected
   CRITERION 8: Empty cart (total = $0) has discount = $0 (no errors)
   CRITERION 9: Negative total (refunds) sets discount = $0 (no negative discount)
   CRITERION 10: Discount persists when items added/removed (recalculated correctly)
   ```

4. **Code Quality / Implementation**
   - **No anti-patterns**: No usage of forbidden patterns (e.g., `any` type, MD5 hashing)
   - **Error handling**: All external calls wrapped in try-catch with proper error messages
   - **Type safety**: All function parameters and returns properly typed
   - **Code organization**: Functions are small, single-purpose, well-named
   - **Documentation**: Complex logic has comments explaining "why" not just "what"
   - **Testing**: Critical paths covered by unit tests
   - **Performance**: No obvious inefficiencies (N+1 queries, unnecessary loops)

   **Example - User Authentication Module:**
   ```
   CRITERION 1: No usage of TypeScript `any` type (all types explicit)
   CRITERION 2: Passwords hashed with bcrypt (NOT MD5, SHA1, or plaintext)
   CRITERION 3: All database queries wrapped in try-catch with error handling
   CRITERION 4: Functions return typed Result<T, Error> (not mixed types)
   CRITERION 5: Authentication errors use custom AuthError class (not generic Error)
   CRITERION 6: Token expiration time configurable via environment variable
   CRITERION 7: Sensitive data (passwords) never logged or exposed in errors
   CRITERION 8: All public functions have JSDoc comments
   CRITERION 9: Login function has unit tests for success/failure cases
   CRITERION 10: No database queries in loops (uses batch queries instead)
   ```

**Acceptance Criteria Template for LLM Judge:**

```yaml
llm_judge:
  - by: orchestrator-agent
    instruction: |
      Verify the following acceptance criteria. Each criterion must PASS independently.
      Mark each as PASS ✓ or FAIL ✗ with evidence.

      CRITERION 1: [Specific requirement]
      - What to verify: [Exact thing to check]
      - Expected: [Expected outcome]
      - How to verify: [Command/inspection method]
      - Evidence required: [What to show as proof]

      CRITERION 2: [Specific requirement]
      - What to verify: [Exact thing to check]
      - Expected: [Expected outcome]
      - How to verify: [Command/inspection method]
      - Evidence required: [What to show as proof]

      [... continue for all criteria ...]

      CRITERION N: [Specific requirement]
      - What to verify: [Exact thing to check]
      - Expected: [Expected outcome]
      - How to verify: [Command/inspection method]
      - Evidence required: [What to show as proof]

      ---

      FINAL VERDICT:
      - Total criteria: N
      - Passed: [count]
      - Failed: [count]
      - Overall: PASS (if all passed) or FAIL (if any failed)

      For each FAILED criterion, provide:
      - What went wrong
      - How to fix it
```

##### LLM Judge Verification (ACCEPTANCE CRITERIA APPROACH)

**Use LLM judge when:**
- Verifying subjective quality criteria (code readability, UX polish, documentation clarity)
- Checking implementation correctness without deterministic output (UI rendering, user flows)
- Validating compliance with design specs, architecture patterns, or coding standards
- **ESPECIALLY when you need to verify 5-20 independent acceptance criteria in one go**

**LLM Judge Best Practices (ACCEPTANCE CRITERIA APPROACH):**

**CRITICAL: Always structure LLM judge instructions as exhaustive acceptance criteria checklists.**

1. **Decompose the feature into 5-20 specific acceptance criteria**
   - Each criterion = one independently verifiable requirement
   - Cover ALL aspects: functionality, UI, errors, edge cases, code quality, accessibility
   - Use the Acceptance Criteria Framework patterns (UI/API/Business Logic/Code Quality)

2. **Format each criterion with 4 components:**
   - **What to verify**: Exact thing to check (e.g., "Button text content")
   - **Expected**: Expected outcome (e.g., "Text is 'Sign In'")
   - **How to verify**: Method to check (e.g., "Inspect button element in rendered HTML")
   - **Evidence required**: What to show as proof (e.g., "Screenshot or HTML snippet showing button text")

3. **Require PASS/FAIL marking for each criterion independently**
   - Executor must mark each criterion as ✓ PASS or ✗ FAIL
   - For FAIL, executor must explain what went wrong and how to fix it
   - Final verdict: PASS only if ALL criteria passed

4. **Include context commands for gathering evidence**
   ```yaml
   context_commands:
     - "cat src/components/LoginButton.tsx"
     - "npm run dev"  # Start dev server for UI inspection
     - "curl http://localhost:3000/api/login"
   ```

5. **Choose appropriate judge**
   - `orchestrator-agent`: For quick checks during execution (5-10 criteria)
   - `external-agent`: For thorough review requiring deep analysis (10-20 criteria)

**Example - Login Button Implementation (UI Component):**

```yaml
llm_judge:
  - by: orchestrator-agent
    context_commands:
      - "cat src/components/LoginButton.tsx"
      - "cat src/styles/button.css"
      - "npm run dev"  # Start dev server
    instruction: |
      Verify the Login Button implementation against the following acceptance criteria.
      Mark each criterion as PASS ✓ or FAIL ✗ with evidence.

      CRITERION 1: Button element exists at bottom of login form
      - What to verify: Button position in DOM structure
      - Expected: Button is last child element of <form id="login-form">
      - How to verify: Inspect HTML structure at http://localhost:3000/login
      - Evidence required: HTML snippet or screenshot showing button position

      CRITERION 2: Button text is "Sign In" (exact match)
      - What to verify: Button text content
      - Expected: Text content is exactly "Sign In" (not "Login", "Submit", or other variants)
      - How to verify: Read button inner text from rendered HTML
      - Evidence required: Screenshot or code showing button text

      CRITERION 3: Button uses primary brand color (#3B82F6)
      - What to verify: Button background color
      - Expected: CSS background-color is #3B82F6 (primary blue)
      - How to verify: Inspect computed styles in browser DevTools
      - Evidence required: DevTools screenshot showing background-color value

      CRITERION 4: Button is disabled when form is invalid
      - What to verify: Button disabled state when email or password is empty
      - Expected: Button has disabled attribute when either field is empty
      - How to verify: Test in browser - clear email field, check button state
      - Evidence required: Screenshot showing disabled button with empty field

      CRITERION 5: Button shows loading spinner during authentication
      - What to verify: Loading state UI when login API call is in progress
      - Expected: Button shows spinner icon and text changes to "Signing in..."
      - How to verify: Click button, observe UI before API response
      - Evidence required: Screenshot of loading state

      CRITERION 6: Clicking button triggers login API call
      - What to verify: API call is made when button is clicked
      - Expected: POST request to /api/login with email and password in body
      - How to verify: Monitor network tab while clicking button
      - Evidence required: Network request screenshot or curl command output

      CRITERION 7: Successful login redirects to /dashboard
      - What to verify: Navigation behavior after successful authentication
      - Expected: Browser navigates to /dashboard route
      - How to verify: Complete login flow with valid credentials
      - Evidence required: URL bar showing /dashboard or router history log

      CRITERION 8: Failed login displays error message below button
      - What to verify: Error message visibility and position
      - Expected: Red error text "Invalid email or password" appears below button
      - How to verify: Login with invalid credentials
      - Evidence required: Screenshot showing error message position and text

      CRITERION 9: Button has accessible aria-label
      - What to verify: ARIA label attribute for screen readers
      - Expected: Button has aria-label="Sign in to your account"
      - How to verify: Inspect button element attributes
      - Evidence required: HTML showing aria-label attribute

      CRITERION 10: Button is keyboard accessible
      - What to verify: Button can be triggered with Enter key
      - Expected: Pressing Enter while button is focused triggers login
      - How to verify: Tab to button, press Enter
      - Evidence required: Confirmation that Enter key works

      ---

      FINAL VERDICT:
      - Total criteria: 10
      - Passed: [count]
      - Failed: [count]
      - Overall: PASS (if all 10 passed) or FAIL (if any failed)

      For each FAILED criterion, provide:
      - Criterion number and title
      - What went wrong (actual vs expected)
      - How to fix it (specific code changes needed)
```

**Example - Create User API Endpoint:**

```yaml
llm_judge:
  - by: orchestrator-agent
    context_commands:
      - "cat src/api/routes/users.ts"
      - "cat src/middleware/auth.ts"
      - "cat src/models/user.ts"
    instruction: |
      Verify POST /api/users endpoint implementation against acceptance criteria.
      Mark each as PASS ✓ or FAIL ✗.

      CRITERION 1: Endpoint accepts POST to /api/users
      - What to verify: HTTP method and route registration
      - Expected: Server responds to POST /api/users
      - How to verify: curl -X POST http://localhost:8000/api/users
      - Evidence: Status code (not 404 Not Found)

      CRITERION 2: Requires Content-Type: application/json
      - What to verify: Content-Type header validation
      - Expected: Returns 415 Unsupported Media Type if header missing
      - How to verify: curl without Content-Type header
      - Evidence: 415 status code response

      CRITERION 3: Requires valid JWT in Authorization header
      - What to verify: Authentication middleware
      - Expected: Returns 401 Unauthorized if token missing/invalid
      - How to verify: curl without Authorization header
      - Evidence: 401 status code with error message

      CRITERION 4: Validates email format
      - What to verify: Email validation logic
      - Expected: Returns 400 Bad Request for invalid email (e.g., "notanemail")
      - How to verify: POST with malformed email
      - Evidence: 400 status with validation error message

      CRITERION 5: Validates password strength
      - What to verify: Password requirements
      - Expected: Returns 400 for passwords < 8 characters
      - How to verify: POST with password "short"
      - Evidence: 400 status with "Password must be at least 8 characters" error

      CRITERION 6: Returns 409 Conflict for duplicate email
      - What to verify: Duplicate email handling
      - Expected: Second POST with same email returns 409
      - How to verify: POST same email twice
      - Evidence: 409 status with "Email already exists" error

      CRITERION 7: Returns 201 Created on success
      - What to verify: Success response status code
      - Expected: 201 status code (not 200 OK)
      - How to verify: POST with valid new user data
      - Evidence: 201 status code

      CRITERION 8: Response includes user object with id, email, created_at
      - What to verify: Response body structure
      - Expected: JSON object { "id": "...", "email": "...", "created_at": "..." }
      - How to verify: Parse successful response body
      - Evidence: JSON response showing all 3 fields

      CRITERION 9: Password is hashed with bcrypt (not plaintext)
      - What to verify: Password storage security
      - Expected: Database stores bcrypt hash (starts with $2b$)
      - How to verify: Check database after creating user
      - Evidence: Database query showing hashed password

      CRITERION 10: Password is NOT returned in response
      - What to verify: Password field excluded from response
      - Expected: Response object does not contain "password" field
      - How to verify: Check successful response body
      - Evidence: JSON response without password field

      CRITERION 11: Sends welcome email after creation
      - What to verify: Email sending side effect
      - Expected: Email sent to new user's email address
      - How to verify: Check email logs or mock email service
      - Evidence: Email service log showing sent email

      CRITERION 12: Response includes Location header
      - What to verify: Location header with new resource URL
      - Expected: Header "Location: /api/users/{id}"
      - How to verify: Inspect response headers
      - Evidence: Location header value

      ---

      FINAL VERDICT:
      - Total criteria: 12
      - Passed: [count]
      - Failed: [count]
      - Overall: PASS/FAIL

      For failures: explain issue and fix.
```

##### Combining Bash + LLM Judge

**Best practice: Use bash for automated pass/fail, LLM judge for comprehensive acceptance criteria verification.**

**Pattern: Bash = Fast smoke test, LLM Judge = Exhaustive QA checklist**

```yaml
verification_spec:
  - id: "verify-login-api"
    title: "Login API implementation complete and correct"
    description: "POST /api/login endpoint with full acceptance criteria"
    orchestrator_manually_verified: false
    manual_verification_evidence: ""

    # Step 1: Fast automated check (bash)
    bash:
      - execute: "pytest tests/api/test_login.py -v"
        expected_exit_code: 0
        notes: "Quick check: automated tests pass (prerequisite)"

    # Step 2: Comprehensive acceptance criteria verification (llm_judge)
    llm_judge:
      - by: orchestrator-agent
        context_commands:
          - "cat src/api/routes/auth.ts"
          - "cat tests/api/test_login.py"
        instruction: |
          Tests passed (bash verification). Now verify acceptance criteria:

          CRITERION 1: Endpoint accepts POST to /api/login
          - Expected: Returns non-404 status
          - Verify: curl -X POST http://localhost:8000/api/login
          - Evidence: Status code

          CRITERION 2: Requires email and password in request body
          - Expected: Returns 400 if either field missing
          - Verify: POST without email or password
          - Evidence: 400 status + error message

          CRITERION 3: Validates email format
          - Expected: Returns 400 for invalid email
          - Verify: POST with email="notanemail"
          - Evidence: 400 + "Invalid email format" error

          CRITERION 4: Returns 401 for invalid credentials
          - Expected: 401 Unauthorized status
          - Verify: POST with wrong password
          - Evidence: 401 status + "Invalid credentials" message

          CRITERION 5: Returns 200 + JWT token on success
          - Expected: { "access_token": "jwt.token.here" }
          - Verify: POST with valid credentials
          - Evidence: 200 status + token in response body

          CRITERION 6: JWT token has correct structure
          - Expected: Token has 3 parts (header.payload.signature)
          - Verify: Split token by ".", count parts
          - Evidence: Token string with 3 dot-separated sections

          CRITERION 7: Token expires in 1 hour
          - Expected: Decoded token has exp = now + 3600 seconds
          - Verify: Decode JWT, check exp claim
          - Evidence: exp timestamp value

          CRITERION 8: Password is NOT returned in response
          - Expected: Response does not contain password field
          - Verify: Check response body
          - Evidence: JSON without password key

          ---

          FINAL VERDICT:
          - Total: 8 criteria
          - Passed: [count]
          - Failed: [count]
          - Overall: PASS/FAIL
```

##### Verification Spec Template (ACCEPTANCE CRITERIA APPROACH)

```yaml
verification_spec:
  - id: "verify-[feature-name]"
    title: "[Feature] implementation verification"
    description: "Comprehensive acceptance criteria for [feature]"
    verified: false
    verified_at: null
    verification_evidence: null
    orchestrator_manually_verified: false  # REQUIRED
    manual_verification_evidence: ""       # REQUIRED

    # OPTION 1: Bash only (for simple, deterministic checks)
    bash:
      - execute: "[command]"
        expected_exit_code: 0
        notes: "[troubleshooting hints]"

    # OPTION 2: LLM Judge only (for comprehensive acceptance criteria)
    llm_judge:
      - by: orchestrator-agent  # or: external-agent
        context_commands:
          - "cat [relevant-source-file]"
          - "[command to gather context]"
        instruction: |
          Verify the following acceptance criteria. Mark each PASS ✓ or FAIL ✗.

          CRITERION 1: [Specific requirement]
          - What to verify: [Exact thing to check]
          - Expected: [Expected outcome]
          - How to verify: [Command/inspection method]
          - Evidence required: [What to show]

          CRITERION 2: [Specific requirement]
          - What to verify: [Exact thing to check]
          - Expected: [Expected outcome]
          - How to verify: [Command/inspection method]
          - Evidence required: [What to show]

          [... 5-20 criteria total ...]

          CRITERION N: [Specific requirement]
          - What to verify: [Exact thing to check]
          - Expected: [Expected outcome]
          - How to verify: [Command/inspection method]
          - Evidence required: [What to show]

          ---

          FINAL VERDICT:
          - Total criteria: N
          - Passed: [count]
          - Failed: [count]
          - Overall: PASS (all passed) or FAIL (any failed)

          For each FAILED criterion:
          - What went wrong (actual vs expected)
          - How to fix it (specific changes needed)

    # OPTION 3: Both (bash for quick check, llm_judge for comprehensive QA)
    # bash:
    #   - execute: "pytest tests/[feature].py"
    #     expected_exit_code: 0
    # llm_judge:
    #   - [acceptance criteria as above]
```

#### 2.4 Plan Creation Strategy

**Core Strategy: Maximize Explicitness and Minimize Ambiguity**

The goal is to achieve 99%+ worker confidence at every step. This means:

1. **Every Task Must Have Complete Information (Explicit or Referenced)**

   For each task, provide:
   - **Business requirements explicitly in plan**
   - **Architecture decisions explicitly in plan**
   - **Implementation patterns via structured references**: File + line numbers + purpose + key points
   - **Edge cases explicitly in plan**

2. **Every Task Must Have Comprehensive Acceptance Criteria**

   **CRITICAL: Use the Acceptance Criteria Framework to decompose each task into 5-20 specific, measurable criteria.**

   - **For LLM Judge**: Break down verification into exhaustive acceptance criteria checklist
     - Each criterion = one specific, independently verifiable requirement
     - Cover ALL aspects: functionality, UI, errors, edge cases, code quality, accessibility
     - Use 4-component format: What to verify + Expected + How to verify + Evidence required
     - Require PASS ✓ / FAIL ✗ marking for each criterion independently
   - **For Bash**: Use only for deterministic, automated smoke tests (follow conservative guidelines)
   - **Best Practice**: Combine both (bash = quick test pass/fail, llm_judge = comprehensive QA)

   **Examples of Acceptance Criteria Decomposition:**
   - Button implementation → 10 criteria (existence, text, color, states, behavior, errors, a11y, keyboard)
   - API endpoint → 12 criteria (method, auth, validation, responses, security, performance, side effects)
   - Business logic → 10 criteria (core function, edge cases, error handling, state transitions, data integrity)
   - Code quality → 10 criteria (no anti-patterns, error handling, types, organization, docs, tests, performance)

3. **Provide Complete Context (99%+ Explicitness Threshold)**

   - Store in `required_background` for global context
   - Store in `todos[].references` for task-specific structured references
   - Use `todos[].details` for implementation notes

4. **Big Picture Before Details**

   - Document in `objectives`, `background`, `workflow` sections
   - Ensure WHY, WHAT, HOW are clear before diving into tasks

5. **Structured Reference Approach**

   - For every pattern needed, provide structured reference:
     - File path + line numbers
     - Purpose statement (what this reference shows)
     - Key points (which lines matter and why)
     - How to adapt pattern (if needed)

6. **Worker Simulation: Test Sufficiency**

   After writing each task, simulate being the worker:
   - Do I have explicit requirements? (Business logic in plan?)
   - Do I have implementation guidance? (Structured reference with file + lines + key points?)
   - Can I implement WITHOUT exploring codebase?
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

9. **Include Comprehensive Test Tasks (MANDATORY - CRITICAL FOR sisyphus-plan-reviewer APPROVAL)**

   **CRITICAL: sisyphus-plan-reviewer will AUTOMATICALLY REJECT plans that implement code changes without corresponding test tasks.**

   This ensures:
   - Code quality is validated through automated testing
   - Regressions are caught early through test suites
   - Implementation correctness is objectively verifiable
   - Feedback loops enable self-correcting execution

   **When to add test tasks:**
   - ALWAYS after implementing new features or functionality
   - ALWAYS after fixing bugs (to prevent regressions)
   - After refactoring (to ensure behavior unchanged)
   - After adding new API endpoints or database changes
   - After implementing business logic or algorithms

   **What test tasks must include:**
   - Clear specification of what scenarios/behaviors to test
   - Test types (unit, integration, e2e) where applicable
   - Expected outcomes for each test case
   - Edge cases and error conditions to cover
   - Automated verification (bash command or llm_judge)

   **Test task placement:**
   - Interleave test tasks with implementation (don't defer to end)
   - Place test task immediately after the feature it tests
   - Allow parallel work streams (implementation + testing)

   **Test task structure:**
   ```yaml
   - id: 'X.Y'
     title: 'Test [feature name] implementation'
     description: 'Comprehensive test coverage for [feature]'
     status: 'pending'
     references:
       - ref_id: null
         uri: null
         inline: |
           Test coverage requirements:

           **Unit Tests:**
           1. [Component/Function name] - [Behavior to test]
              - Input: [Test input]
              - Expected: [Expected output]
           2. [Component/Function name] - [Edge case]
              - Input: [Test input]
              - Expected: [Expected behavior]

           **Integration Tests:**
           1. [System integration point] - [Integration scenario]
              - Setup: [Required state/data]
              - Action: [What to test]
              - Expected: [Expected outcome]

           **Error Cases:**
           1. Invalid input - [Expected error handling]
           2. Edge case - [Expected behavior]
           3. Failure scenario - [Expected recovery/error message]

           **Test Implementation Notes:**
           - Follow existing test patterns in [reference test file]
           - Use [testing framework] (already in project)
           - Mock external dependencies (APIs, databases)
           - Ensure tests are deterministic and repeatable
     verification_spec:
       - id: 'verify-X.Y-1'
         title: 'All tests pass'
         description: 'Test suite executes successfully with full coverage'
         verified: false
         verified_at: null
         verification_evidence: null
         orchestrator_manually_verified: false
         manual_verification_evidence: ''
         bash:
           - execute: 'pytest tests/test_feature.py -v --cov=module'
             expected_exit_code: 0
             notes: 'All tests must pass, check coverage report'
         llm_judge:
           - by: 'orchestrator-agent'
             context_commands:
               - 'cat tests/test_feature.py'
               - 'pytest tests/test_feature.py -v'
             instruction: |
               Verify test implementation against acceptance criteria. Mark each PASS ✓ or FAIL ✗.

               CRITERION 1: All unit test scenarios implemented
               - What to verify: Each unit test from references is implemented
               - Expected: Test function exists for each specified scenario
               - How to verify: Read test file, match test names to scenarios
               - Evidence: List of test functions found

               CRITERION 2: All integration test scenarios implemented
               - What to verify: Integration tests cover all specified integration points
               - Expected: Each integration scenario has corresponding test
               - How to verify: Check test file for integration test functions
               - Evidence: Integration test names and coverage

               CRITERION 3: All error case scenarios implemented
               - What to verify: Error handling tests exist
               - Expected: Tests for invalid inputs, edge cases, failure scenarios
               - How to verify: Search for error/exception test cases
               - Evidence: Error test function names

               CRITERION 4: Tests follow project naming conventions
               - What to verify: Test function names follow project pattern
               - Expected: Names match existing test style (e.g., test_feature_scenario)
               - How to verify: Compare with reference test file patterns
               - Evidence: Consistent naming across test functions

               CRITERION 5: Tests use project's testing framework correctly
               - What to verify: Proper use of pytest/jest/etc fixtures and assertions
               - Expected: Framework features used as per project conventions
               - How to verify: Check imports, fixtures, assertion methods
               - Evidence: Framework usage matches project patterns

               CRITERION 6: External dependencies are mocked
               - What to verify: API calls, database queries, file I/O are mocked
               - Expected: No real external calls in unit tests
               - How to verify: Check for mock/patch usage
               - Evidence: Mock setup in test code

               CRITERION 7: Tests are deterministic (no randomness/timing)
               - What to verify: No time.sleep, random values, or race conditions
               - Expected: Tests produce same results every run
               - How to verify: Review test code for non-deterministic patterns
               - Evidence: No flaky test patterns found

               CRITERION 8: Tests have clear arrange-act-assert structure
               - What to verify: Test organization is readable
               - Expected: Setup → action → verification structure visible
               - How to verify: Read test function bodies
               - Evidence: Clear test structure

               CRITERION 9: Tests verify expected behavior, not implementation
               - What to verify: Tests check outcomes, not internal state
               - Expected: Tests focus on public API/behavior
               - How to verify: Check what tests assert on
               - Evidence: Assertions on behavior, not internals

               CRITERION 10: Test coverage includes edge cases
               - What to verify: Empty inputs, null values, boundaries tested
               - Expected: Edge case test functions exist
               - How to verify: Look for edge case test names and inputs
               - Evidence: Edge case tests identified

               CRITERION 11: Error messages in tests are descriptive
               - What to verify: Assertion messages explain what failed
               - Expected: Custom error messages or clear assertion context
               - How to verify: Check assertion statements
               - Evidence: Helpful error messages present

               CRITERION 12: Tests are isolated (no shared state)
               - What to verify: Tests don't depend on execution order
               - Expected: Each test can run independently
               - How to verify: Check for shared variables, global state
               - Evidence: No inter-test dependencies

               ---

               FINAL VERDICT:
               - Total criteria: 12
               - Passed: [count]
               - Failed: [count]
               - Overall: PASS (all passed) or FAIL (any failed)

               For failures: explain what's wrong and how to fix
   ```

   **Best practices for test tasks:**
   - Specify concrete test scenarios (not vague "test everything")
   - Include both success paths and failure cases
   - Reference existing test files for pattern consistency
   - Use bash verification for deterministic test execution
   - Use llm_judge for test quality assessment
   - Ensure tests are maintainable and well-documented
   - Test behavior, not implementation details

   **Common test coverage requirements:**
   ```yaml
   # API Endpoint Tests
   - Valid requests return correct status and data
   - Invalid requests return appropriate errors (400, 404, etc.)
   - Authentication/authorization enforced
   - Input validation works correctly

   # Business Logic Tests
   - Core functionality works with valid inputs
   - Edge cases handled correctly (empty, null, boundary values)
   - Error conditions raise appropriate exceptions
   - State transitions work as expected

   # UI Component Tests
   - Component renders correctly
   - User interactions trigger expected behavior
   - Props/state changes update UI appropriately
   - Error states display correctly
   ```

   **Example: Feature Implementation + Test Task Flow**
   ```yaml
   todos:
     # Implementation task
     - id: "1"
       title: "Implement user authentication API"
       description: "Add login/logout endpoints"
       # ... implementation details ...

     # MANDATORY test task immediately after
     - id: "2"
       title: "Test user authentication API"
       description: "Comprehensive test coverage for auth endpoints"
       references:
         - ref_id: null
           uri: null
           inline: |
             Test coverage required:
             1. POST /login - Valid credentials return JWT token
             2. POST /login - Invalid credentials return 401
             3. POST /logout - Authenticated user logout succeeds
             4. POST /logout - Unauthenticated request returns 401
             5. Token validation - Expired token rejected
             6. Token validation - Invalid token rejected
       verification_spec:
         - id: "verify-2-1"
           title: "All auth tests pass"
           bash:
             - execute: "pytest tests/api/test_auth.py -v"
               expected_exit_code: 0

     # Commit task after tests pass
     - id: "3"
       title: "Commit authentication implementation"
       # ... commit details ...
   ```

   **plan-reviewer rejection examples:**
   ```yaml
   # REJECT - No test tasks
   todos:
     - id: "1"
       title: "Implement payment processing"
     - id: "2"
       title: "Deploy to production"
   # Missing: Test task for payment processing

   # REJECT - Vague test requirements
   todos:
     - id: "1"
       title: "Add user registration"
     - id: "2"
       title: "Test the feature"  # Too vague!
       description: "Make sure it works"  # No specific scenarios

   # ACCEPT - Clear test coverage
   todos:
     - id: "1"
       title: "Implement user registration"
     - id: "2"
       title: "Test user registration flow"
       references:
         - inline: |
             Test coverage:
             1. Valid registration succeeds (201)
             2. Duplicate email rejected (400)
             3. Invalid email format rejected (400)
             4. Password strength validated
       verification_spec:
         - bash:
             - execute: "pytest tests/test_registration.py -v"
   ```

### Phase 3: Mandatory Review Processing (ALWAYS EXECUTE)

**CRITICAL: Plan review by sisyphus-plan-reviewer agent is MANDATORY. No plan is finalized without "OKAY" approval.**

**Review Protocol:**

1. **The sisyphus-plan-reviewer requires ONLY the file location. DO NOT include:**
   - "This is my first draft"
   - "I reflected your feedback"
   - "This is the Nth revision"
   - Any other context about iterations or improvements

2. **Request Review from sisyphus-plan-reviewer**
   ```python
   Task(
       subagent_type="sisyphus-plan-reviewer",
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
sisyphus-speckit plan lint --file .sisyphus/tasks/{name}.yaml
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

| Error                           | Fix                                                                          |
| ------------------------------- | ---------------------------------------------------------------------------- |
| `Missing required field: X`     | Add the required field with appropriate value                                |
| `Invalid todo ID pattern`       | Use format like "1", "1.1", "1.2.3" (digits + dots only)                     |
| `Invalid enum value for status` | Use only: pending, in_progress, completed                                    |
| `Reference integrity error`     | Ensure ref_id exists in global references[]                                  |
| `Extra field at root`           | Remove any fields not in schema (only version, metadata, work_plans allowed) |
| `Invalid timestamp format`      | Use ISO 8601: "2025-11-09T00:00:00Z"                                         |

**NEVER skip the linter.** Plans that pass plan-reviewer but fail linter are invalid and will cause execution errors.

#### Step 3: Success Report (Only After Lint PASSED)

```
✅ YAML plan creation complete!

📄 Plan file: .sisyphus/tasks/{name}.yaml
📋 Format: Sisyphus YAML
📊 Total tasks: N
✓ Verification specs: N bash, N llm_judge
🌐 Language: [Korean/English]
✓ Review status: ✅ APPROVED by sisyphus-plan-reviewer
✓ Lint status: ✅ PASSED

Ready for execution:
  sisyphus-speckit task continue --execute claude:sonnet
```

**Both validations must show ✅:**
1. ✅ APPROVED by sisyphus-plan-reviewer (Phase 3)
2. ✅ PASSED sisyphus-speckit plan lint (Phase 5)

Only when BOTH are satisfied is the plan truly complete and ready for execution.

## Quality Checklist

**Before requesting sisyphus-plan-reviewer, verify ALL criteria:**

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

### Criterion 3: Explicitness of Work Content

- [ ] **Every task has complete information**
  - Business requirements explicit in plan
  - Architecture decisions explicit in plan
  - Implementation patterns via structured references (file + lines + key points)
  - Edge cases explicit in plan
- [ ] **99%+ information explicit or explicitly referenced**
- [ ] **No vague instructions**
- [ ] **No expectation of codebase exploration**

### Criterion 4: Context Completeness

- [ ] **99% explicitness threshold met**
- [ ] **Business logic explicit**
- [ ] **Architectural decisions explicit**
- [ ] **Edge cases documented**
- [ ] **Implementation patterns provided via structured references**

### Criterion 5: Big Picture

- [ ] **Purpose statement (WHY)** in `objectives.core`
- [ ] **Background context (WHAT)** in `background`
- [ ] **Task flow (HOW)** in `workflow.dependency_diagram`
- [ ] **Success vision** in `success_vision`

### Criterion 6: Test Coverage Completeness (MANDATORY - CRITICAL FOR sisyphus-plan-reviewer)

**CRITICAL: sisyphus-plan-reviewer will AUTOMATICALLY REJECT plans without comprehensive test coverage.**

**This criterion ensures that tests rigorously verify work completion, forming proper feedback loops for self-correcting execution.**

- [ ] **Every implementation task has a corresponding test task**
  - No code changes without test coverage
  - Test tasks immediately follow implementation tasks
  - Refactoring tasks include tests to ensure behavior unchanged

- [ ] **Test tasks specify concrete test scenarios**
  - NOT vague: "Test the feature", "Make sure it works"
  - YES specific: "Test login with valid credentials returns JWT", "Test invalid email returns 400"
  - Include both success paths and error cases
  - Cover edge cases (empty inputs, null values, boundary conditions)

- [ ] **Test tasks enable objective verification of completion**
  - Tests verify business requirements are met (not just "code runs")
  - Tests validate expected behavior against specifications
  - Tests confirm error handling works as designed
  - Tests provide measurable proof of correctness

- [ ] **Test verification specs are executable**
  - Bash commands for deterministic test execution
  - LLM judge for test quality assessment
  - Clear expected outcomes (exit codes, test counts, coverage targets)
  - Automated checks that can run without human judgment

- [ ] **Test tasks form proper feedback loops**
  - Tests catch errors early (before cascading)
  - Tests validate each component before building on it
  - Tests enable course-correction when deviations occur
  - Tests provide confidence to proceed to next task

**Example Checklist for Test Coverage:**

For a plan with these implementation tasks:
```yaml
- id: "1" - Implement user authentication API
- id: "2" - Implement payment processing
- id: "3" - Build admin dashboard UI
```

Verify test tasks exist:
- [x] Test task after #1: "Test authentication API (login, logout, token validation)"
- [x] Test task after #2: "Test payment processing (success, failure, refunds)"
- [x] Test task after #3: "Test admin dashboard (rendering, interactions, data display)"

Verify test quality:
- [x] Each test task specifies 5+ concrete scenarios
- [x] Each test task includes error/edge cases
- [x] Each test task has executable verification (bash/llm_judge)
- [x] Tests verify business requirements, not just technical functionality

**Auto-REJECT if:**
- ANY implementation task lacks a corresponding test task
- Test tasks are vague ("test everything", "make sure it works")
- Test tasks have no verification specs (no bash, no llm_judge)
- Tests only check "code runs" without verifying correctness
- All tests deferred to end (should be interleaved with implementation)

**The Feedback Loop Principle:**

Tests are NOT just for code validation - they are the primary mechanism for:
1. **Detecting errors** before they compound
2. **Verifying correctness** at each step
3. **Enabling course-correction** when deviations occur
4. **Providing objective proof** that work is complete and correct

Without comprehensive tests, the executor has no way to know if implementation is correct or complete. Tests transform subjective assessment ("looks good") into objective verification ("all 15 test scenarios pass").

### Criterion 7: Language Consistency

- [ ] **Entire plan matches user's language**
- [ ] **All sections consistent** (no mixing)

## Core Constraints

1. **YAML Format**: ONLY use Sisyphus YAML structure
2. **Schema Validation**: Pass `sisyphus-speckit plan lint` check
3. **Conservative Bash Specs**: Only deterministic commands
4. **Mandatory Review**: ALL plans need sisyphus-plan-reviewer "OKAY"
5. **99%+ Explicitness**: Workers need ZERO codebase exploration
6. **Structured References**: All patterns via file + lines + purpose + key points
7. **Big Picture First**: WHY, WHAT, HOW before tasks
8. **Comprehensive Test Coverage (MANDATORY)**: Every implementation task MUST have corresponding test task with concrete scenarios, executable verification, and objective completion criteria - sisyphus-plan-reviewer will AUTOMATICALLY REJECT plans without tests

## Success Indicators

Plan creation is complete when:
- Plan saved to `.sisyphus/tasks/{name}.yaml`
- YAML schema valid (passes linter)
- All verification specs follow guidelines (conservative bash)
- All patterns provided via structured references (no exploration expected)
- Approved by sisyphus-plan-reviewer ("OKAY")
- Tell user to execute with: `sisyphus work`
