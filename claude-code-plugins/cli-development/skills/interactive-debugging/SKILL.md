---
name: interactive-debugging
description: Patterns for controlling interactive debuggers (pdb, ipdb, gdb, lldb, node debug) via terminalcp
---

# Interactive Debugging with terminalcp

This skill provides comprehensive patterns for automating interactive debugger sessions using terminalcp MCP. It enables AI agents to spawn, control, and extract information from debuggers in real-time.

## Overview

terminalcp enables:
- Real-time debugger control via PTY
- Breakpoint management and inspection
- Step-by-step execution with state capture
- Variable inspection and expression evaluation
- Multi-debugger session management

The MCP server runs via `npx @mariozechner/terminalcp@latest --mcp` and provides full terminal emulation for debugger interaction.

## Python Debugging (pdb/ipdb)

### Starting a Debug Session

```json
{
  "action": "start",
  "command": "python -m pdb script.py",
  "name": "python-debug"
}
```

Or with ipdb for enhanced debugging:

```json
{
  "action": "start",
  "command": "python -m ipdb script.py",
  "name": "python-debug"
}
```

### Setting Breakpoints

```json
{
  "action": "stdin",
  "id": "python-debug",
  "data": "b script.py:42\r"
}
```

Set conditional breakpoint:

```json
{
  "action": "stdin",
  "id": "python-debug",
  "data": "b script.py:42, x > 10\r"
}
```

Set breakpoint in function:

```json
{
  "action": "stdin",
  "id": "python-debug",
  "data": "b my_function\r"
}
```

### Execution Control

```json
// Continue execution
{
  "action": "stdin",
  "id": "python-debug",
  "data": "c\r"
}

// Step into function
{
  "action": "stdin",
  "id": "python-debug",
  "data": "s\r"
}

// Step over (next line)
{
  "action": "stdin",
  "id": "python-debug",
  "data": "n\r"
}

// Return from current function
{
  "action": "stdin",
  "id": "python-debug",
  "data": "r\r"
}

// Continue until next breakpoint or return
{
  "action": "stdin",
  "id": "python-debug",
  "data": "unt 50\r"
}
```

### Variable Inspection

```json
// Print variable value
{
  "action": "stdin",
  "id": "python-debug",
  "data": "p variable_name\r"
}

// Pretty print
{
  "action": "stdin",
  "id": "python-debug",
  "data": "pp complex_object\r"
}

// List all local variables
{
  "action": "stdin",
  "id": "python-debug",
  "data": "locals()\r"
}

// Evaluate expression
{
  "action": "stdin",
  "id": "python-debug",
  "data": "p len(my_list) + 5\r"
}
```

### Stack Frame Navigation

```json
// Show stack trace
{
  "action": "stdin",
  "id": "python-debug",
  "data": "w\r"
}

// Move up one frame
{
  "action": "stdin",
  "id": "python-debug",
  "data": "u\r"
}

// Move down one frame
{
  "action": "stdin",
  "id": "python-debug",
  "data": "d\r"
}

// List source code at current location
{
  "action": "stdin",
  "id": "python-debug",
  "data": "l\r"
}
```

### Capturing Debugger Output

```json
{
  "action": "stdout",
  "id": "python-debug"
}
```

This returns the current terminal state including all debugger output, variable values, and stack traces.

## GDB/LLDB Debugging (C/C++)

### Starting GDB Session

```json
{
  "action": "start",
  "command": "gdb ./myprogram",
  "name": "gdb-debug"
}
```

### Starting LLDB Session

```json
{
  "action": "start",
  "command": "lldb ./myprogram",
  "name": "lldb-debug"
}
```

### GDB Breakpoint Management

```json
// Set breakpoint at line
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "break main.c:42\r"
}

// Set breakpoint at function
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "break my_function\r"
}

// Conditional breakpoint
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "break main.c:42 if x > 10\r"
}

// List all breakpoints
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "info breakpoints\r"
}

// Delete breakpoint
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "delete 1\r"
}
```

### LLDB Breakpoint Management

```json
// Set breakpoint at line
{
  "action": "stdin",
  "id": "lldb-debug",
  "data": "breakpoint set --file main.c --line 42\r"
}

// Set breakpoint at function
{
  "action": "stdin",
  "id": "lldb-debug",
  "data": "breakpoint set --name my_function\r"
}

// List breakpoints
{
  "action": "stdin",
  "id": "lldb-debug",
  "data": "breakpoint list\r"
}
```

### GDB Execution Control

```json
// Start program
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "run\r"
}

// Start with arguments
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "run arg1 arg2\r"
}

// Continue
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "continue\r"
}

// Step into
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "step\r"
}

// Step over
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "next\r"
}

// Finish current function
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "finish\r"
}
```

### GDB Variable Inspection

```json
// Print variable
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "print variable_name\r"
}

// Print with format (hex)
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "print/x pointer\r"
}

// Display variable (auto-display on each stop)
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "display my_var\r"
}

// Show all local variables
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "info locals\r"
}

// Examine memory
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "x/10x $rsp\r"
}
```

### Stack and Backtrace

```json
// Show backtrace
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "backtrace\r"
}

// Show full backtrace with locals
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "backtrace full\r"
}

// Select frame
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "frame 2\r"
}

// Move up frame
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "up\r"
}

// Move down frame
{
  "action": "stdin",
  "id": "gdb-debug",
  "data": "down\r"
}
```

## Node.js Debugging

### Starting Node Debug Session

```json
{
  "action": "start",
  "command": "node inspect script.js",
  "name": "node-debug"
}
```

### Node Debugger Commands

```json
// Continue execution
{
  "action": "stdin",
  "id": "node-debug",
  "data": "c\r"
}

// Step over
{
  "action": "stdin",
  "id": "node-debug",
  "data": "n\r"
}

// Step into
{
  "action": "stdin",
  "id": "node-debug",
  "data": "s\r"
}

// Step out
{
  "action": "stdin",
  "id": "node-debug",
  "data": "o\r"
}

// Set breakpoint at current line
{
  "action": "stdin",
  "id": "node-debug",
  "data": "sb()\r"
}

// Set breakpoint at line
{
  "action": "stdin",
  "id": "node-debug",
  "data": "sb('script.js', 42)\r"
}

// List breakpoints
{
  "action": "stdin",
  "id": "node-debug",
  "data": "breakpoints\r"
}

// Clear breakpoint
{
  "action": "stdin",
  "id": "node-debug",
  "data": "cb('script.js', 42)\r"
}
```

### Node Variable Inspection

```json
// Evaluate expression
{
  "action": "stdin",
  "id": "node-debug",
  "data": "exec('myVariable')\r"
}

// Enter REPL mode
{
  "action": "stdin",
  "id": "node-debug",
  "data": "repl\r"
}

// In REPL, inspect objects
{
  "action": "stdin",
  "id": "node-debug",
  "data": "myObject.property\r"
}

// Exit REPL
{
  "action": "stdin",
  "id": "node-debug",
  "data": "\u0003"
}
```

Note: `\u0003` is Ctrl+C to exit REPL mode.

## Advanced Patterns

### Automated Bug Investigation Workflow

```json
// 1. Start debugger
{
  "action": "start",
  "command": "python -m pdb buggy_script.py",
  "name": "bug-hunt"
}

// 2. Set breakpoint at suspected line
{
  "action": "stdin",
  "id": "bug-hunt",
  "data": "b buggy_script.py:100\r"
}

// 3. Run until breakpoint
{
  "action": "stdin",
  "id": "bug-hunt",
  "data": "c\r"
}

// 4. Inspect variables
{
  "action": "stdin",
  "id": "bug-hunt",
  "data": "pp locals()\r"
}

// 5. Get current state
{
  "action": "stdout",
  "id": "bug-hunt"
}

// 6. Step through suspicious code
{
  "action": "stdin",
  "id": "bug-hunt",
  "data": "n\r"
}

// 7. Check variable changes
{
  "action": "stdout",
  "id": "bug-hunt"
}
```

### Multi-Breakpoint Analysis

```json
// Set multiple breakpoints
{
  "action": "stdin",
  "id": "python-debug",
  "data": "b function_a\r"
}

{
  "action": "stdin",
  "id": "python-debug",
  "data": "b function_b\r"
}

{
  "action": "stdin",
  "id": "python-debug",
  "data": "b function_c\r"
}

// Run and collect state at each breakpoint
{
  "action": "stdin",
  "id": "python-debug",
  "data": "c\r"
}

// Capture state
{
  "action": "stdout",
  "id": "python-debug"
}

// Continue to next breakpoint
{
  "action": "stdin",
  "id": "python-debug",
  "data": "c\r"
}

// Capture state again
{
  "action": "stdout",
  "id": "python-debug"
}
```

### Conditional Debugging

```json
// Set conditional breakpoint
{
  "action": "stdin",
  "id": "python-debug",
  "data": "b process_item, item_id == 'problematic-id'\r"
}

// Run until condition met
{
  "action": "stdin",
  "id": "python-debug",
  "data": "c\r"
}

// Inspect when condition triggers
{
  "action": "stdin",
  "id": "python-debug",
  "data": "pp item\r"
}

{
  "action": "stdout",
  "id": "python-debug"
}
```

### Post-Mortem Debugging

```python
# In your code, catch exceptions and drop into debugger
try:
    risky_operation()
except Exception:
    import pdb; pdb.post_mortem()
```

```json
// When exception occurs, debugger starts automatically
// terminalcp will capture the interactive session
{
  "action": "stdout",
  "id": "python-debug"
}

// Inspect exception state
{
  "action": "stdin",
  "id": "python-debug",
  "data": "pp sys.exc_info()\r"
}
```

### Stream-Based Monitoring

For long-running debug sessions, use stream mode to capture incremental output:

```json
{
  "action": "stream",
  "id": "python-debug",
  "since_last": true
}
```

This returns only new output since last check, useful for monitoring debugger progress without blocking.

## Best Practices

### Effective Breakpoint Strategy

1. **Start broad, then narrow**: Set breakpoints at function entry points first
2. **Use conditional breakpoints**: Avoid stopping at every iteration in loops
3. **Combine with logging**: Use `p` command output to understand state progression
4. **Clean up**: Remove unnecessary breakpoints to avoid clutter

### State Capture Timing

- Capture state **after** stepping, not before
- Use `stdout` action after each significant command
- For rapid iteration, use `stream` mode with `since_last: true`

### Managing Multiple Debug Sessions

```json
// Start multiple debuggers for comparison
{
  "action": "start",
  "command": "python -m pdb version_a.py",
  "name": "debug-a"
}

{
  "action": "start",
  "command": "python -m pdb version_b.py",
  "name": "debug-b"
}

// List all active sessions
{
  "action": "list"
}

// Control each independently
{
  "action": "stdin",
  "id": "debug-a",
  "data": "b main\r"
}

{
  "action": "stdin",
  "id": "debug-b",
  "data": "b main\r"
}
```

### Cleanup

Always stop debugger sessions when done:

```json
{
  "action": "stop",
  "id": "python-debug"
}
```

## Common Debugging Workflows

### Python Exception Investigation

1. Run script in debugger
2. Let it crash or set breakpoint before error
3. Use `w` to see stack trace
4. Use `u`/`d` to navigate frames
5. Use `p` to inspect variables at each frame
6. Identify root cause

### Memory Leak Detection (C/C++)

1. Start GDB with program
2. Set breakpoint at allocation site
3. Use `info proc mappings` to see memory layout
4. Compare memory before/after operations
5. Use `x` command to examine memory regions

### Race Condition Debugging

1. Set breakpoints at critical sections
2. Run multiple debug sessions
3. Use conditional breakpoints on shared state
4. Capture timing of variable changes

This skill provides the foundation for AI-driven interactive debugging using terminalcp's real-time PTY capabilities.
