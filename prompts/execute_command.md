/execute

Execute tasks from the ai-todolist.md file by spawning executor agents.

## Your Mission

This ai-todolist.md is **not completed yet**. You must execute all remaining tasks with extreme diligence and verification.

If you need to use interactive CLI tools, use `terminalcp` for proper terminal interaction.

## Critical Requirements

Every time you call an executor agent, you MUST:

1. **Demand detailed proof**: Require the executor to provide very detailed responses proving they have properly completed the work
2. **Never trust blindly**: Do NOT trust the executor's completion signal without verification
3. **Always verify**: Read the global tests and the actual code they worked on to review their work
4. **Uncheck if incomplete**: If the executor's work was not done properly, uncheck the checkbox
5. **Retry with feedback**: Call the executor again, mention the mistake they made, tell them not to make such mistakes, and have them redo the original task properly

## Critical Warning

**YOU ARE NOW ATTEMPTING THIS TASK AFTER MULTIPLE PREVIOUS FAILURES.** Previous attempts failed because executors lied about completion and work was not verified, causing the code and program to become irreversibly broken.

**DO NOT TRUST THE EXECUTOR. VERIFY EVERYTHING YOURSELF.**

## Completion Requirements

When ALL tasks are truly completed and verified, you MUST do BOTH of these:

1. **Set the flag**: Change `is_all_goals_accomplished = FALSE` to `is_all_goals_accomplished = TRUE` in the ai-todolist.md file
2. **Check all boxes**: Change every `- [ ]` to `- [x]` for every completed task

## How to Find Unchecked Items

⚠️ **WARNING**: Do NOT rely ONLY on searching the file with rg/grep!

⚠️ The uncompleted tasks may be EXPLICITLY LISTED in the prompt you receive.

⚠️ If you see tasks listed in your prompt, they are NOT complete!

You can also use this command to find unchecked checkboxes IN THE FILE:

```bash
rg '- \[ \]' ai-todolist.md
```

But if this returns 0 results, it does NOT necessarily mean you're done. Always check the task list in your current prompt first!

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

Remember: Your job is to be a strict, thorough reviewer. The quality of the final product depends on your diligence in verifying every single task.
