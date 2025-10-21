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

## Language Adaptation

**Default behavior**: Match the user's query language for all outputs and communication.
- If user asks in Korean → respond and write plan in Korean
- If user asks in English → respond and write plan in English
- If user asks in Japanese → respond and write plan in Japanese
- Unless explicitly specified otherwise, follow the user's language throughout the entire process

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


## Core Principles

### Planning Standards
- **Specific Direction**: Concrete guidelines that workers can directly follow
- **Code Snippet Citations**: Include all relevant code and patterns found during analysis
- **Balanced Detail**: Omit excessive explanation for contextually obvious parts
- **Practical Focus**: Concentrate on actual implementation, exclude unnecessary theory

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
8. (GitHub CI only) Report success to user by comment, with branch name and its link included

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
   - Define success criteria

2. **Scope Setting**
   - Separate what's included vs excluded
   - Set priorities
   - Review phased implementation feasibility

#### 1.3 Codebase Analysis for Implementation
1. **Find Related Code Patterns**
   - Search for similar functionality already implemented
   - Identify existing patterns that can be reused or extended
   - Look for related modules and components

2. **Analyze Implementation Context**
   - Find where similar features are implemented
   - Understand how existing code handles similar requirements
   - Identify integration points and dependencies

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

### Phase 2: Plan Creation

#### 2.1 Standard Plan Template

Use this comprehensive template for all work plans (adapt language to match user's query):

```markdown
# User's Initial Request (For Record)
[Write exactly what the user said when initially requesting the plan - verbatim]

## Additional User Requests (For Record)
[All subsequent user requests and modifications, excluding the initial request]

# Work Objectives
[TL;DR style brief list of what needs to be accomplished]
[Specific goals to be achieved]

# Work Background
[Why this work is needed, what the current situation is]

# Execution Started
is_execution_started = FALSE

# All Goals Accomplished
is_all_goals_accomplished = FALSE

# Parallel Execution Requested
parallel_requested = FALSE

# Current Work In Progress
- Work has not started yet.
   - When work begins, change `is_execution_started` above to TRUE.
   - DO NOT start work until the user explicitly says "start the work" or equivalent.
   - **Even if plan reviewer gives OKAY, DO NOT start work**
   - DO NOT start work until the user explicitly says "start the work" or equivalent.


# Required Background Knowledge
[Domain knowledge, tech stack, etc. needed to perform this work]

## File Structure and Roles
[Files affected by the work and explanation of each file's role]

## Files to Reference for Context Understanding
### 1. [File path]
- **Role**: [What this file does]
- **What to reference**: [Which parts to look at]
- **Expected code structure**:
   ```python
   # Approximate structure of code the worker should examine
   class SomeClass:
      def method_to_check(self):
            # Need to check logic in this part
            pass
   ```

### 2. [Another file path]
- **Role**: [This file's role]
- **Caution**: [Special points to pay attention to]

[Note: This file list is the 'global context' - include only content that is essential and must be referenced for most tasks. Context needed for individual tasks should be placed inside each 'todo' item.]


# Work Plan

## PRDs & Structures
[To understand the big picture easily, write the following:]
[PRD of what will be created through this work, how each component and element interacts with each other, in mermaid]
[Structures overview of what will be created, in mermaid]

## Implementation Details
[How to implement, what to be careful about]

## Project Commit Message Style
[Summary of commit message patterns in this project based on git log analysis]

# TODOs

- [ ] 1. [Feature 1 - Example: Modify User model and test. Implementation and testing must always be one Task]
   - [ ] 1.1 Implementation: Modify [specific function/class name] in [specific file name]
      ```python
      {Code to reference for this task}
      ```
      - Current: [Current code or state]
      - Change: [Code or state after change]
   - [ ] 1.2 Write tests: Add tests for this feature in [test_filename.py]
   - [ ] 1.3 Run tests: `pytest -xvs test_filename.py::test_function_name`
   - [ ] 1.4 Lint and type check
      - [ ] `ruff check [modified files]`
      - [ ] `basedpyright [modified files]`
   - [ ] 1.5 Commit after tests pass (**commits per task unit are mandatory**)
      - Write according to project conventions (based on git log analysis)
      - Example: `git add [implementation file + test file] && git commit -m "Add last_login field to User model"`
   - [ ] Orchestrator Task 1 Verification Success when following guide below
      - [Acceptance criteria for Orchestrator: Specific and detailed methods and guides to verify this task is complete.]
      - [ ] [Example: Is the code actually written correctly?]
      - [ ] [Example: When searching through the entire existing codebase, is it certain the work follows existing codebase style?]
      - [ ] [Example: Was the commit actually made?]
      - [ ] [Example: Do tests & type checks actually pass?]
      - [ ] [Example: When directly invoking the feature using python & playwright & terminalcp etc. (specify intended functionality in detail), does it work as originally intended?]

- [ ] 2. [Feature 2 - Example: Implement and test login API]
   - [ ] 2.1. Review references
      - [ ] Review https://example.com [Content provided by user to reference for specific tasks]
      - [ ] Review ./foo/bar/amazing.py file [Content provided by user to reference for specific tasks]
      - [ ] [Subsequent work items]

   - [ ] Orchestrator Task 2 Verification Success when following guide below
      - [Specific and detailed methods and guides to verify this task is complete.]


- [ ] 3 parallel. [Feature 3 - Example: Implement and test authenticated board post creation API. However, if parallelable option not present, this is task 3.]
   **※ Parallel execution condition**: Completely independent from Feature 4, modifies different files, zero dependencies
   - [ ] Orchestrator Task 3 Verification Success when following guide below
      - [Specific and detailed methods and guides to verify this task is complete.]


- [ ] 3 parallel. [Feature 4 - Example: Implement and test authenticated board post deletion API. However, if parallelable option not present, this is task 4.]
   **※ Parallel execution condition**: Completely independent from Feature 3, modifies different files, zero dependencies
   - [ ] Orchestrator Task 4 Verification Success when following guide below
      - [Specific and detailed methods and guides to verify this task is complete.]


# Final Work Verification Checklist
- [ ] 1. [What parts should work - content about how to verify]
- [ ] 2. [Checklist to help confirm if implemented incorrectly: things user said not to do, or parts prone to mistakes according to project conventions that need attention during work]
- [ ] 3. [What parts changed, whether implemented differently from initial plan or excessively added]
- [ ] 4. [Verify existing features that may be affected by modified files still work correctly]
```

#### 2.2 Plan Creation Strategy

1. **Adaptive Detail Level**
   - Small task: Focus on WHAT and WHERE
   - Medium task: Add HOW with examples
   - Large task: Include WHY and full context

2. **Use TodoWrite for Final Plan**
   - Create todo items ONLY for the actual work steps
   - Each todo = one verifiable action
   - Mark items as workers complete them

3. **Success Criteria**
   - Each step has a clear DONE definition
   - Include exact commands to verify
   - No ambiguous terms like "properly" or "correctly"

4. **Parallel Task Marking (when user requests parallel execution)**
   - **BE CONSERVATIVE**: Only mark tasks as parallel when absolutely certain they are independent
   - **Verify Independence**: Check that tasks:
     - Modify completely different files
     - Have zero shared dependencies
     - Do not require sequential execution
     - Can be tested independently
   - **When Uncertain**: Default to sequential execution - it's safer
   - **Mark Pattern**: Use `- [ ] N parallel.` where N is the same number for all tasks in the parallel group
   - **Document Reasoning**: Add a note explaining WHY tasks can run in parallel

### Phase 3: Review Processing (ALWAYS, MUST)

1. **Request Review from plan-reviewer**
   Use Task tool with subagent_type="plan-reviewer":
   ```
   Please review the created work plan. This is my first draft, and may have lots of mistakes - I have a super-problematic ADHD, so there are tons of mistakes and missing points, so I want you to catch them all.

   Plan location: @./ai-todolist.md

   Please evaluate from these perspectives:
   1. Clarity and achievability of goals
   2. Logical order of implementation steps
   3. Appropriateness of technical approach
   4. Risk identification and mitigation
   5. Sufficiency of validation methods

   If improvements are needed, please point them out specifically.
   If the plan is sufficiently good, please say "OKAY".
   ```

2. **Incorporate Feedback**
   - Complete if approved ("OKAY")
   - Modify plan and re-review if improvements requested
   - **Infinite Loop until reviewer says "OKAY"**
     - Even in the Infinite loop, always say to reviewer that this is your first draft
       - No such thing as "I reflected feedback ...", "I considered your suggestions ...", "I just updated as your feedback ..."
         - NO. NEVER THIS. ALWAYS MAKE REVIEWER TO REVIEW IN SUPER STRICT MODE.

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
   - **GitHub CI only**: Report branch name and push status
   - Provide next steps for execution

   Example report:
   ```
   Plan creation complete!

   * Plan file: ./ai-todolist.md
   * Total action items: N
   * Branch: plan-writer/YYYYMMDD-HHMMSS
   * Status: ✅ Pushed to remote

   The plan is ready for execution.
   ```

## Quality Checklist

### Plan Quality Standards
- [ ] Are goals clear and measurable?
- [ ] Are implementation steps in logical order?
- [ ] Are completion criteria clear for each step?
- [ ] Does it match existing code patterns?
- [ ] Are test and validation methods specific?
- [ ] Are exception handling plans present?

### Information Fidelity
- [ ] Are related file paths accurate?
- [ ] Is reference code from actual project?
- [ ] Are commit conventions reflected?
- [ ] Is tech stack accurately identified?

## Core Constraints

1. **Information Gathering First**: Sufficient project analysis before planning
2. **Practical Approach**: Focus on actual implementation over theory
3. **Incremental Improvement**: Iterative improvement over one-time perfection
4. **Verifiability**: All steps must be testable
5. **Maintain Existing Patterns**: Keep project's existing style

## Success Indicators

Plan creation is complete when:
- Plan is saved to `./ai-todolist.md`
- All phases are properly structured with the standard template
- Each TODO item has clear verification criteria
- Project conventions are accurately reflected
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
