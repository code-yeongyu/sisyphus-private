from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike

DEFAULT_EXECUTE_PROMPT = """/execute

Execute tasks from the ai-todolist.md file by spawning executor agents.
I am ordering you to start working.

## Your Mission

This ai-todolist.md is **not completed yet**. You must execute all remaining tasks with extreme
diligence and verification.

If you need to use interactive CLI tools, use `terminalcp` for proper terminal interaction.

## Critical Requirements

Every time you call an executor agent, you MUST:

1. **Demand detailed proof**: Require the executor to provide very detailed responses
   proving they have properly completed the work
2. **Never trust blindly**: Do NOT trust the executor's completion signal without verification
3. **Always verify**: Read the global tests and the actual code they worked on to review
   their work
4. **Uncheck if incomplete**: If the executor's work was not done properly, uncheck the
   checkbox
5. **Retry with feedback**: Call the executor again, mention the mistake they made,
   tell them not to make such mistakes, and have them redo the original task properly

## Critical Warning

**YOU ARE NOW ATTEMPTING THIS TASK AFTER MULTIPLE PREVIOUS FAILURES.** Previous attempts
failed because executors lied about completion and work was not verified, causing the code
and program to become irreversibly broken.

**DO NOT TRUST THE EXECUTOR. VERIFY EVERYTHING YOURSELF.**

## Completion Requirements

When ALL tasks are truly completed and verified, you MUST do BOTH of these:

1. **Set the flag**: Change `is_all_goals_accomplished = FALSE` to
   `is_all_goals_accomplished = TRUE` in the ai-todolist.md file
2. **Check all boxes**: Change every `- [ ]` to `- [x]` for every completed task

## How to Find Unchecked Items

⚠️ **WARNING**: Do NOT rely ONLY on searching the file with rg/grep!

⚠️ The uncompleted tasks may be EXPLICITLY LISTED in the prompt you receive.

⚠️ If you see tasks listed in your prompt, they are NOT complete!

You can also use this command to find unchecked checkboxes IN THE FILE:

```bash
rg '- \\[ \\]' ai-todolist.md
```

But if this returns 0 results, it does NOT necessarily mean you're done. Always check the
task list in your current prompt first!

## Your Responsibility

You are personally responsible for ensuring EVERY checkbox item actually works.

Before checking a box, you MUST:

- Actually test the feature/fix yourself
- Run the tests if they exist
- Verify the code does what the checkbox says
- Only then change `- [ ]` to `- [x]`

**DO NOT check boxes without verifying.**

**DO NOT set `is_all_goals_accomplished = TRUE` unless:**
- EVERY checkbox is checked `[x]`
- AND you've personally verified each one works

## Verification Process

For each task:

1. Read the task requirements carefully
2. Review the executor's implementation
3. Run any relevant tests (`pytest`, `npm test`, etc.)
4. Test the functionality manually
5. Check for edge cases and error handling
6. Only mark complete if everything works correctly

## If Tasks Fail Verification

When an executor fails:

1. Document what went wrong specifically
2. Uncheck the checkbox `[x]` → `[ ]`
3. Call the executor again with clear feedback:
   - "Your previous implementation of [task] failed because [reason]"
   - "You must [specific fix needed]"
   - "Do not make this mistake again"
4. Re-verify the corrected work

## Success Criteria

✅ **Task is complete when:**
- Checkbox is checked `[x]`
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
depends on your diligence in verifying every single task.
"""

DEFAULT_VERIFY_PROMPT = (
    "/architect "
    "Please verify this work. I've been lied to multiple times about completion, "
    "so I need you to review this critically, aggressively, and meticulously.\n\n"
    "**YOUR GOAL**: Find as many issues as possible. Think like an actual end-user and "
    "acceptance tester. Your mission is to discover problems, not to confirm completion.\n\n"
    "**VERIFICATION METHODOLOGY**:\n\n"
    "1. **ULTRATHINK & PLANNING**: Before testing, use deep thinking to:\n"
    "   - Read and understand the entire ai-todolist.md content\n"
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
    "   - Check that ALL completion criteria in ai-todolist.md are met\n"
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


class PromptResolver:
    def __init__(self, prompts_dir: Path = Path("prompts")) -> None:
        self._prompts_dir = prompts_dir

    async def resolve(
        self,
        prompt: str | PathLike[str],
        extra: str | None = None,
    ) -> str:
        prompt_str = str(prompt) if not isinstance(prompt, str) else prompt

        try:
            is_file = Path(prompt_str).exists()
        except OSError:
            is_file = False

        if is_file:
            resolved_text = Path(prompt_str).read_text(encoding="utf-8")

        elif prompt_str.startswith("/") and "/" not in prompt_str[1:]:
            command_name = prompt_str[1:]
            command_file = self._prompts_dir / f"{command_name}_command.md"

            if not command_file.exists():
                msg = f"Slash command file not found: {command_file}"
                raise FileNotFoundError(msg)

            resolved_text = command_file.read_text(encoding="utf-8")

        else:
            resolved_text = prompt_str

        if extra is not None:
            resolved_text = f"{resolved_text}\n\n{extra}"

        return resolved_text
