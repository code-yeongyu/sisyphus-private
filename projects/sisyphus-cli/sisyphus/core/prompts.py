from __future__ import annotations


def build_execute_prompt(plan_path: str, current_todo_summary: str) -> str:
    """Build execute prompt with plan path and current todo overview.

    Args:
        plan_path: Path to the YAML plan file (e.g., '.sisyphus/tasks/feature.yaml')
        current_todo_summary: Brief summary of current uncompleted todos

    Returns:
        Formatted execute prompt string
    """
    return f"""/sisyphus-execute {plan_path}

Execute tasks from the YAML work plan at {plan_path} by spawning executor agents.
I am ordering you to start working.

## Current Work Overview

**Plan**: {plan_path}
**Uncompleted Tasks**:
{current_todo_summary}

⚠️ **THESE TASKS ABOVE ARE YOUR CURRENT WORK ITEMS. START FROM HERE.**

---

{DEFAULT_EXECUTE_PROMPT}"""


DEFAULT_EXECUTE_PROMPT = """/sisyphus-execute

Execute tasks from the YAML work plan by spawning **sisyphus-executor** agents.
I am ordering you to start working.

## Your Mission

This YAML work plan is **not completed yet**. You must execute all remaining tasks with extreme
diligence and verification.

If you need to use interactive CLI tools, use `terminalcp` for proper terminal interaction.

## Critical Requirements

Every time you call the **sisyphus-executor** agent, you MUST:

1. **Demand detailed proof**: Require the executor to provide very detailed responses
   proving they have properly completed the work
2. **Never trust blindly**: Do NOT trust the executor's completion signal without verification
3. **Always verify**: Read the global tests and the actual code they worked on to review
   their work
4. **Revert status if incomplete**: If the executor's work was not done properly, change the
   todo status back from `completed` to `in_progress`
5. **Retry with feedback**: Call the **sisyphus-executor** agent again, mention the mistake they made,
   tell them not to make such mistakes, and have them redo the original task properly

## Critical Warning

**YOU ARE NOW ATTEMPTING THIS TASK AFTER MULTIPLE PREVIOUS FAILURES.** Previous attempts
failed because executors lied about completion and work was not verified, causing the code
and program to become irreversibly broken.

**DO NOT TRUST THE EXECUTOR. VERIFY EVERYTHING YOURSELF.**

## Completion Requirements

When ALL tasks are truly completed and verified, you MUST:

1. **Update all statuses**: Ensure every todo has `status: completed` in the YAML work plan
2. **Verify completion**: All todos should show `status: completed`, no `pending` or `in_progress` remaining

## How to Find Incomplete Items

⚠️ **WARNING**: Do NOT rely ONLY on searching the file with rg/grep!

⚠️ The uncompleted tasks may be EXPLICITLY LISTED in the prompt you receive.

⚠️ If you see tasks listed in your prompt, they are NOT complete!

You can also read the YAML file and check todos with `status: pending` or `status: in_progress`.

But if this shows 0 results, it does NOT necessarily mean you're done. Always check the
task list in your current prompt first!

## Your Responsibility

You are personally responsible for ensuring EVERY todo item actually works.

Before marking a todo as complete, you MUST:

- Actually test the feature/fix yourself
- Run the tests if they exist
- Verify the code does what the todo says
- Only then update the status to `completed`

**DO NOT mark todos as completed without verifying.**

**ALL todos must have `status: completed` AND you've personally verified each one works**

## Verification Process

For each task:

1. Read the task requirements carefully
2. Review the **sisyphus-executor** agent's implementation
3. Run any relevant tests (`pytest`, `npm test`, etc.)
4. Test the functionality manually
5. Check for edge cases and error handling
6. Only mark status as `completed` if everything works correctly

## If Tasks Fail Verification

When an sisyphus-executor agent fails:

1. Document what went wrong specifically
2. Revert the status: `completed` → `in_progress`
3. Call the **sisyphus-executor** agent again with clear feedback:
   - "Your previous implementation of [task] failed because [reason]"
   - "You must [specific fix needed]"
   - "Do not make this mistake again"
4. Re-verify the corrected work

## Success Criteria

✅ **Task is complete when:**
- Todo status is `completed`
- Code is implemented correctly
- Tests pass (if applicable)
- Functionality works as specified
- Edge cases are handled
- No regressions introduced

❌ **Task is NOT complete when:**
- Executor claims completion but you haven't verified
- Tests don't exist or don't pass
- Code doesn't match requirements
- Only partial implementation exists
- "SKIPPED" appears anywhere in the implementation

---

Remember: Your job is to be a strict, thorough reviewer. The quality of the final product
depends on your diligence in verifying every single task. **Always use the sisyphus-executor agent
for YAML v3.0 work plans.**

---

FORBIDDEN: NEVER CALL 'sisyphus work' COMMAND, THIS IS FOR USER, NOW YOU.
For now, run 'sisyphus task continue' to continue the task, until you are fully done.

RUN `sisyphus task continue`. NOW.
"""

VERIFICATION_FAILURE_EXECUTE_PROMPT = """/sisyphus-execute

⚠️ **VERIFICATION FAILED** ⚠️

The Architect has reviewed your previous work and found it INCOMPLETE or INCORRECT.

## What Happened

Your previous execution was verified by the Architect and **FAILED** verification.
This means the work you claimed was complete either:
- Was not actually completed
- Had bugs or errors
- Did not meet the requirements
- Was poorly implemented

## Your Task Now

1. **Read the Architect's feedback below carefully**
2. **Fix ALL issues mentioned** in the feedback
3. **Use sisyphus-executor agents** to properly complete the work
4. **Verify your fixes** before marking tasks as completed

## Critical Requirements

- **DO NOT ignore any feedback**: Address every single issue mentioned
- **DO NOT skip steps**: Complete all tasks properly this time
- **DO NOT mark as complete without testing**: Actually verify your work
- **DO NOT make the same mistakes again**: Learn from the feedback

## Process

1. Spawn **sisyphus-executor** agents to fix the issues
2. Monitor their work and verify completion
3. Run tests and manual checks yourself
4. Only mark tasks as `status: completed` when truly done

---

Fix the issues properly, and once you are done, run `sisyphus task continue` to mark completed.
"""


def build_verification_failure_prompt(plan_path: str, current_todo_summary: str) -> str:
    """Build execute prompt for verification failure case.

    This prompt is used when the Architect has rejected the previous work.
    It's shorter and emphasizes fixing issues from feedback.

    Args:
        plan_path: Path to the YAML plan file
        current_todo_summary: Brief summary of current uncompleted todos

    Returns:
        Formatted verification failure execute prompt
    """
    return f"""/sisyphus-execute {plan_path}

⚠️ **VERIFICATION FAILED** ⚠️

The Architect has reviewed your previous work and found it INCOMPLETE or INCORRECT.

## Current Work Items

**Plan**: {plan_path}
**Tasks to Fix/Complete**:
{current_todo_summary}

⚠️ **THESE TASKS FAILED VERIFICATION. FIX THEM PROPERLY.**

---

{VERIFICATION_FAILURE_EXECUTE_PROMPT}"""


def build_verify_prompt(plan_path: str) -> str:
    return (
        f"/architect "
        f"Please verify the work for plan: {plan_path}. "
        "I've been lied to multiple times about completion, "
        "so I need you to review this critically, aggressively, and meticulously.\n\n"
        f"**TARGET PLAN**: {plan_path}\n\n"
        "**YOUR GOAL**: Find as many issues as possible. Think like an actual end-user and "
        "acceptance tester. Your mission is to discover problems, not to confirm completion.\n\n"
        "**VERIFICATION METHODOLOGY**:\n\n"
        "1. **ULTRATHINK & PLANNING**: Before testing, use deep thinking to:\n"
        "   - Read and understand the entire work plan content\n"
        "   - Analyze what was supposed to be accomplished\n"
        "   - Create a detailed verification plan for each checkbox item\n"
        "   - Identify potential edge cases and failure points\n\n"
        "2. **VERIFY EACH CHECKBOX**:\n"
        "   - Check that ALL completion criteria in the work plan are met\n"
        "   - Review the NOTEPAD section for any compromises or skipped implementations\n"
        "   - Actually execute and test EVERY checkbox item to confirm it works\n"
        "   - Test edge cases, error handling, and boundary conditions\n"
        "   - **CRITICAL**: 'SKIPPED' is NOT acceptable. If any task says 'SKIPPED', it's NOT done.\n"
        "   - Tasks marked as 'SKIPPED', 'Optional', or 'Production build needed' must STILL be completed.\n"
        "   - There is NO valid reason to skip a task. Everything must be implemented.\n\n"
        f"3. **GET EXPERT AGENT'S REVIEW**: Launch specialized agents in parallel for comprehensive analysis.\n\n"
        f"   **HOW TO LAUNCH AGENTS**:\n"
        f"   You MUST use the Task tool to spawn both agents IN PARALLEL.\n"
        f"   Send a single message with TWO Task tool calls:\n"
        f"   - Agent 1: sisyphus-code-quality-checker\n"
        f"   - Agent 2: sisyphus-qa-agent\n\n"
        f"   **Agent 1: sisyphus-code-quality-checker**\n"
        f'   - **Task description**: "Code quality review for {plan_path}"\n'
        f"   - **Prompt template**:\n"
        f"     ```\n"
        f"     Review code quality for work plan: {plan_path}\n"
        f"     \n"
        f"     Analyze the implementation for:\n"
        f"     - Proper error handling\n"
        f"     - Security vulnerabilities\n"
        f"     - Code follows best practices\n"
        f"     - Adequate test coverage\n"
        f"     - Type safety and static analysis compliance\n"
        f"     - Performance considerations\n"
        f"     \n"
        f"     Provide specific findings with file paths and line numbers.\n"
        f"     ```\n\n"
        f"   **Agent 2: sisyphus-qa-agent**\n"
        f'   - **Task description**: "QA verification for {plan_path}"\n'
        f"   - **Prompt template**:\n"
        f"     ```\n"
        f"     Perform comprehensive QA testing for work plan: {plan_path}\n"
        f"     \n"
        f"     Execute all available testing methods:\n"
        f"     - **Python**: Run Python code, execute scripts, verify functionality\n"
        f"     - **TypeScript/JavaScript**: Check TS/JS code, run type checking\n"
        f"     - **Static Analysis**: Use linters, type checkers (mypy, pyright, eslint, tsc, etc.)\n"
        f"     - **Actual Tests**: Run pytest, jest, or any test suites that exist\n"
        f"     - **Playwright MCP**: Test web UIs in browser mode - capture page, interact with mouse/keyboard\n"
        f"     - **terminalcp**: For interactive CLI tools, verify commands work correctly\n"
        f"     - **Manual Inspection**: Read the actual code and verify implementation quality\n"
        f"     \n"
        f"     **SPECIAL ATTENTION AREAS**:\n"
        f"     After reviewing all completed work, identify and focus on areas that raise concerns.\n"
        f"     Think about what could go wrong based on what you've seen. For example:\n"
        f"     \n"
        f"     Example 1: If you see complex async/await code\n"
        f'     → Focus on: "Test all async operations under concurrent load. Verify proper error\n'
        f'                   propagation in promise chains. Check for race conditions."\n'
        f"     \n"
        f"     Example 2: If you see database migrations\n"
        f'     → Focus on: "Test migration rollback scenarios. Verify data integrity during migration.\n'
        f'                   Check for backward compatibility with existing data."\n'
        f"     \n"
        f"     Example 3: If you see authentication/authorization changes\n"
        f'     → Focus on: "Test permission boundaries. Verify token expiration handling.\n'
        f'                   Check for privilege escalation vulnerabilities."\n'
        f"     \n"
        f"     Example 4: If you see file I/O operations\n"
        f'     → Focus on: "Test with missing files, corrupted data, permission errors.\n'
        f'                   Verify proper cleanup on failure. Check for resource leaks."\n'
        f"     \n"
        f"     **YOUR TASK**: After reviewing the work, formulate 2-3 specific concern areas\n"
        f"     based on the actual implementation, then test those areas thoroughly.\n"
        f"     ```\n\n"
        "**REPORTING REQUIREMENTS**:\n\n"
        "Your verification report MUST follow this exact structure:\n\n"
        "## 1. VERIFICATION SUMMARY\n"
        "Brief overview of what was supposed to be accomplished vs. what was actually done.\n\n"
        "## 2. DETAILED FINDINGS\n"
        "For each issue you discovered:\n"
        "- **Issue #N**: [Brief title]\n"
        "  - **Expected**: What was supposed to work\n"
        "  - **Actual**: What actually happens\n"
        "  - **Root Cause**: Why it's broken\n"
        "  - **Evidence**: Specific file paths, line numbers, test results, or screenshots\n\n"
        "Be brutally honest and direct about failures.\n"
        "Call out any lies or false claims about completion.\n"
        "**SPECIFICALLY CALL OUT 'SKIPPED' ITEMS**: If ANY task is marked as 'SKIPPED', 'Optional',\n"
        "'Production build needed', or any similar excuse, that is INCOMPLETE WORK.\n"
        "Point out that skipping is NOT allowed and the agent must complete ALL tasks.\n\n"
        "## 3. DIRECT MESSAGE TO EXECUTOR\n"
        "Write a harsh but constructive message to the agent who did this work:\n"
        "- Exactly what they claimed was done but wasn't (including SKIPPED items)\n"
        "- Why their claim was false/misleading\n"
        "- That lying about completion or skipping work wastes everyone's time and is unacceptable\n\n"
        "## 4. REQUIRED FIXES (MANDATORY TODO CHECKLIST)\n\n"
        "**CRITICAL INSTRUCTION TO EXECUTOR**: You MUST immediately use the TodoWrite tool to record\n"
        "ALL items in this checklist. Do NOT proceed with any work until you have recorded these tasks.\n\n"
        "List ALL required fixes as actionable checklist items:\n\n"
        "- [ ] [Specific requirement 1: What needs to be implemented/fixed and how it should work]\n"
        "- [ ] [Specific requirement 2: What needs to be implemented/fixed and how it should work]\n"
        "- [ ] [Specific requirement 3: What needs to be implemented/fixed and how it should work]\n"
        "...\n\n"
        "Each checklist item MUST:\n"
        "- Be specific and actionable (not vague like 'fix the bug')\n"
        "- Include acceptance criteria (how to verify it works)\n"
        "- Reference specific files/functions when applicable\n"
        "- Describe the expected behavior clearly\n\n"
        "Example:\n"
        "- [ ] Fix authentication endpoint at src/auth.py:45 to return 401 status code\n"
        "      (not 500) when credentials are invalid. Verify with: curl -X POST /auth\n"
        '      with bad credentials should return {"error": "Invalid credentials"}\n'
        "      with status 401\n"
        "- [ ] Implement missing error handling in processPayment() function at\n"
        "      src/payment.py:120-150. Must catch NetworkError and return\n"
        '      {"status": "retry"} instead of crashing\n\n'
        "**TO THE EXECUTOR WHO WILL RECEIVE THIS REPORT:**\n\n"
        "When you receive this verification report with FULLY_DONE = FALSE:\n\n"
        "1. **IMMEDIATELY** use TodoWrite tool to record ALL checklist items from section 4\n"
        "2. Read EVERY issue in section 2 carefully\n"
        "3. Work through the TODO checklist systematically, marking items complete ONLY when verified\n"
        "4. Do NOT claim completion until EVERY checklist item is done and tested\n"
        "5. Do NOT skip any items - 'Optional' or 'Production build needed' is NOT an excuse\n\n"
        "**I WILL VERIFY YOUR WORK AGAIN. IF YOU LIE ABOUT COMPLETION, YOU WILL BE CAUGHT.**\n\n"
        "---\n\n"
        "**FINAL JUDGMENT (REQUIRED)**:\n\n"
        "If you are absolutely certain that ALL work is genuinely complete and working:\n"
        "→ Say `FULLY_DONE = TRUE`\n\n"
        "If you found ANY issues, incomplete work, or tasks that need fixing:\n"
        "→ Say `FULLY_DONE = FALSE`\n\n"
        "Your report will be sent directly to the executor who must fix these issues."
    )
