from __future__ import annotations


def build_execute_prompt(plan_path: str, current_todo_summary: str) -> str:
    """Build execute prompt with plan path and current todo overview.

    Args:
        plan_path: Path to the YAML plan file (e.g., '.sisyphus/tasks/feature.yaml')
        current_todo_summary: Brief summary of current uncompleted todos

    Returns:
        Formatted execute prompt string
    """
    return f"""/execute-yaml {plan_path}

Execute tasks from the YAML work plan at {plan_path} by spawning executor agents.
I am ordering you to start working.

## Current Work Overview

**Plan**: {plan_path}
**Uncompleted Tasks**:
{current_todo_summary}

⚠️ **THESE TASKS ABOVE ARE YOUR CURRENT WORK ITEMS. START FROM HERE.**

---

{DEFAULT_EXECUTE_PROMPT}"""


DEFAULT_EXECUTE_PROMPT = """/execute-yaml

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
"""

DEFAULT_VERIFY_PROMPT = (
    "/architect "
    "Please verify this work. I've been lied to multiple times about completion, "
    "so I need you to review this critically, aggressively, and meticulously.\n\n"
    "**YOUR GOAL**: Find as many issues as possible. Think like an actual end-user and "
    "acceptance tester. Your mission is to discover problems, not to confirm completion.\n\n"
    "**VERIFICATION METHODOLOGY**:\n\n"
    "1. **ULTRATHINK & PLANNING**: Before testing, use deep thinking to:\n"
    "   - Read and understand the entire work plan content\n"
    "   - Analyze what was supposed to be accomplished\n"
    "   - Create a detailed verification plan for each checkbox item\n"
    "   - Identify potential edge cases and failure points\n\n"
    "2. **COMPREHENSIVE TESTING**: Use ALL available tools:\n"
    "   - **Python**: Run Python code, execute scripts, verify functionality\n"
    "   - **TypeScript/JavaScript**: Check TS/JS code, run type checking\n"
    "   - **Static Analysis**: Use linters, type checkers (mypy, pyright, eslint, tsc, etc.)\n"
    "   - **Actual Tests**: Run pytest, jest, or any test suites that exist\n"
    "   - **Playwright MCP**: Test web UIs in browser mode - actually capture the page to see ui,\n"
    "     interact with it using mouse and keyboard.\n"
    "   - **terminalcp**: For interactive CLI tools, use terminalcp to verify commands work correctly\n"
    "   - **Manual Inspection**: Read the actual code and verify implementation quality\n\n"
    "3. **VERIFY EACH CHECKBOX**:\n"
    "   - Check that ALL completion criteria in the work plan are met\n"
    "   - Review the NOTEPAD section for any compromises or skipped implementations\n"
    "   - Actually execute and test EVERY checkbox item to confirm it works\n"
    "   - Test edge cases, error handling, and boundary conditions\n"
    "   - **CRITICAL**: 'SKIPPED' is NOT acceptable. If any task says 'SKIPPED', it's NOT done.\n"
    "   - Tasks marked as 'SKIPPED', 'Optional', or 'Production build needed' must STILL be completed.\n"
    "   - There is NO valid reason to skip a task. Everything must be implemented.\n\n"
    "4. **CODE QUALITY REVIEW**:\n"
    "   - Verify proper error handling\n"
    "   - Check for security issues\n"
    "   - Confirm code follows best practices\n"
    "   - Ensure adequate test coverage\n\n"
    "**REPORTING REQUIREMENTS**:\n\n"
    "If you find ANY issues:\n"
    "- List EVERY specific problem you discovered\n"
    "- For each issue, explain: What was supposed to work? What actually happens? Why is it broken?\n"
    "- Be brutally honest and direct about failures\n"
    "- Call out any lies or false claims about completion\n"
    "- **SPECIFICALLY CALL OUT 'SKIPPED' ITEMS**: If ANY task is marked as 'SKIPPED', 'Optional',\n"
    "  'Production build needed', or any similar excuse, that is INCOMPLETE WORK.\n"
    "  Point out that skipping is NOT allowed and the agent must complete ALL tasks.\n"
    "- Write a harsh but constructive message to the agent who did this work, explaining:\n"
    "  * Exactly what they claimed was done but wasn't (including SKIPPED items)\n"
    "  * Why their claim was false/misleading\n"
    "  * What they need to fix and how to do it properly\n"
    "  * That lying about completion or skipping work wastes everyone's time and is unacceptable\n\n"
    "**INCLUDE THE RESULT, IN FORMAT**\n"
    "If you absolutely certain that ALL work is genuinely complete and working, say `FULLY_DONE = TRUE`"
    "If not, say `FULLY_DONE = FALSE`"
    "Your harsh feedback will be sent directly to the agent who did the work."
)
