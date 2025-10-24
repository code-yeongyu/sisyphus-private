---
name: repl-interaction
description: Patterns for controlling REPL sessions (Python, IPython, Node.js, Ruby, etc.) via terminalcp
---

# REPL Interaction with terminalcp

This skill provides comprehensive patterns for managing and automating REPL (Read-Eval-Print Loop) sessions using terminalcp MCP. It enables AI agents to execute code interactively, explore APIs, and prototype solutions in real-time.

## Overview

terminalcp enables:
- Interactive code execution in multiple languages
- Real-time output capture and parsing
- Persistent REPL sessions for stateful exploration
- Parallel REPL management for multi-language projects
- History and context preservation

The MCP server runs via `npx @mariozechner/terminalcp@latest --mcp` and provides full terminal emulation for REPL interaction.

## Python REPL

### Starting Python REPL

```json
{
  "action": "start",
  "command": "python3 -i",
  "name": "python-repl"
}
```

### Starting IPython (Enhanced REPL)

```json
{
  "action": "start",
  "command": "ipython",
  "name": "ipython-repl"
}
```

### Basic Code Execution

```json
// Simple expression
{
  "action": "stdin",
  "id": "python-repl",
  "data": "2 + 2\r"
}

// Variable assignment
{
  "action": "stdin",
  "id": "python-repl",
  "data": "x = 42\r"
}

// Import module
{
  "action": "stdin",
  "id": "python-repl",
  "data": "import math\r"
}

// Use imported module
{
  "action": "stdin",
  "id": "python-repl",
  "data": "math.sqrt(16)\r"
}
```

### Multi-Line Code Execution

```json
// Start multi-line code
{
  "action": "stdin",
  "id": "python-repl",
  "data": "def greet(name):\r"
}

{
  "action": "stdin",
  "id": "python-repl",
  "data": "    return f'Hello, {name}!'\r"
}

// Empty line to finish
{
  "action": "stdin",
  "id": "python-repl",
  "data": "\r"
}

// Call the function
{
  "action": "stdin",
  "id": "python-repl",
  "data": "greet('Alice')\r"
}
```

### Capturing REPL Output

```json
{
  "action": "stdout",
  "id": "python-repl"
}
```

Returns the current terminal state including all executed code and output.

### Stream Mode for Real-Time Monitoring

```json
{
  "action": "stream",
  "id": "python-repl",
  "since_last": true
}
```

Returns only new output since last check, useful for monitoring long-running computations.

## IPython Advanced Features

### Magic Commands

```json
// Time execution
{
  "action": "stdin",
  "id": "ipython-repl",
  "data": "%timeit sum(range(1000))\r"
}

// Run external script
{
  "action": "stdin",
  "id": "ipython-repl",
  "data": "%run script.py\r"
}

// Show history
{
  "action": "stdin",
  "id": "ipython-repl",
  "data": "%history\r"
}

// List variables
{
  "action": "stdin",
  "id": "ipython-repl",
  "data": "%whos\r"
}

// Edit code in external editor
{
  "action": "stdin",
  "id": "ipython-repl",
  "data": "%edit myfunction\r"
}
```

### Object Introspection

```json
// Get help
{
  "action": "stdin",
  "id": "ipython-repl",
  "data": "str.split?\r"
}

// Detailed help
{
  "action": "stdin",
  "id": "ipython-repl",
  "data": "str.split??\r"
}

// List methods
{
  "action": "stdin",
  "id": "ipython-repl",
  "data": "dir(str)\r"
}

// Type inspection
{
  "action": "stdin",
  "id": "ipython-repl",
  "data": "type(my_variable)\r"
}
```

### Shell Commands in IPython

```json
// Run shell command
{
  "action": "stdin",
  "id": "ipython-repl",
  "data": "!ls -la\r"
}

// Capture shell output
{
  "action": "stdin",
  "id": "ipython-repl",
  "data": "files = !ls *.py\r"
}

// Use Python variables in shell
{
  "action": "stdin",
  "id": "ipython-repl",
  "data": "!echo {my_var}\r"
}
```

## Node.js REPL

### Starting Node REPL

```json
{
  "action": "start",
  "command": "node",
  "name": "node-repl"
}
```

### Basic JavaScript Execution

```json
// Simple expression
{
  "action": "stdin",
  "id": "node-repl",
  "data": "2 + 2\r"
}

// Variable declaration
{
  "action": "stdin",
  "id": "node-repl",
  "data": "const x = 42\r"
}

// Array methods
{
  "action": "stdin",
  "id": "node-repl",
  "data": "[1, 2, 3].map(n => n * 2)\r"
}

// Require module
{
  "action": "stdin",
  "id": "node-repl",
  "data": "const fs = require('fs')\r"
}
```

### Multi-Line Code

```json
// Start function definition
{
  "action": "stdin",
  "id": "node-repl",
  "data": "function greet(name) {\r"
}

{
  "action": "stdin",
  "id": "node-repl",
  "data": "  return `Hello, ${name}!`\r"
}

{
  "action": "stdin",
  "id": "node-repl",
  "data": "}\r"
}

// Call function
{
  "action": "stdin",
  "id": "node-repl",
  "data": "greet('Bob')\r"
}
```

### Async/Await in REPL

```json
// Define async function
{
  "action": "stdin",
  "id": "node-repl",
  "data": "async function fetchData() { return 'data' }\r"
}

// Call with await (Node 16+)
{
  "action": "stdin",
  "id": "node-repl",
  "data": "await fetchData()\r"
}
```

### Node REPL Commands

```json
// Show help
{
  "action": "stdin",
  "id": "node-repl",
  "data": ".help\r"
}

// Load file
{
  "action": "stdin",
  "id": "node-repl",
  "data": ".load script.js\r"
}

// Save session to file
{
  "action": "stdin",
  "id": "node-repl",
  "data": ".save session.js\r"
}

// Exit REPL
{
  "action": "stdin",
  "id": "node-repl",
  "data": ".exit\r"
}
```

## Ruby REPL (irb)

### Starting Ruby REPL

```json
{
  "action": "start",
  "command": "irb",
  "name": "ruby-repl"
}
```

### Ruby Code Execution

```json
// Simple expression
{
  "action": "stdin",
  "id": "ruby-repl",
  "data": "2 + 2\r"
}

// String manipulation
{
  "action": "stdin",
  "id": "ruby-repl",
  "data": "'hello'.upcase\r"
}

// Array operations
{
  "action": "stdin",
  "id": "ruby-repl",
  "data": "[1, 2, 3].map { |n| n * 2 }\r"
}

// Define method
{
  "action": "stdin",
  "id": "ruby-repl",
  "data": "def greet(name); \"Hello, #{name}!\"; end\r"
}

// Call method
{
  "action": "stdin",
  "id": "ruby-repl",
  "data": "greet('Charlie')\r"
}
```

## Lua REPL

### Starting Lua REPL

```json
{
  "action": "start",
  "command": "lua",
  "name": "lua-repl"
}
```

### Lua Code Execution

```json
// Simple expression
{
  "action": "stdin",
  "id": "lua-repl",
  "data": "print(2 + 2)\r"
}

// Table manipulation
{
  "action": "stdin",
  "id": "lua-repl",
  "data": "t = {1, 2, 3}\r"
}

{
  "action": "stdin",
  "id": "lua-repl",
  "data": "print(t[1])\r"
}
```

## Advanced Patterns

### API Exploration Workflow

```json
// 1. Start IPython session
{
  "action": "start",
  "command": "ipython",
  "name": "api-explore"
}

// 2. Import library
{
  "action": "stdin",
  "id": "api-explore",
  "data": "import requests\r"
}

// 3. Inspect module
{
  "action": "stdin",
  "id": "api-explore",
  "data": "dir(requests)\r"
}

// 4. Get help on specific function
{
  "action": "stdin",
  "id": "api-explore",
  "data": "requests.get?\r"
}

// 5. Test API call
{
  "action": "stdin",
  "id": "api-explore",
  "data": "response = requests.get('https://api.github.com')\r"
}

// 6. Inspect response
{
  "action": "stdin",
  "id": "api-explore",
  "data": "response.json()\r"
}

// 7. Capture all output
{
  "action": "stdout",
  "id": "api-explore"
}
```

### Data Analysis Session

```json
// 1. Start IPython
{
  "action": "start",
  "command": "ipython",
  "name": "data-analysis"
}

// 2. Import pandas
{
  "action": "stdin",
  "id": "data-analysis",
  "data": "import pandas as pd\r"
}

// 3. Load data
{
  "action": "stdin",
  "id": "data-analysis",
  "data": "df = pd.read_csv('data.csv')\r"
}

// 4. Explore data
{
  "action": "stdin",
  "id": "data-analysis",
  "data": "df.head()\r"
}

{
  "action": "stdin",
  "id": "data-analysis",
  "data": "df.describe()\r"
}

// 5. Analyze
{
  "action": "stdin",
  "id": "data-analysis",
  "data": "df.groupby('category').mean()\r"
}

// 6. Get results
{
  "action": "stdout",
  "id": "data-analysis"
}
```

### Multi-Language Development

```json
// Start Python REPL for backend logic
{
  "action": "start",
  "command": "python3 -i",
  "name": "backend-repl"
}

// Start Node REPL for frontend logic
{
  "action": "start",
  "command": "node",
  "name": "frontend-repl"
}

// Test Python API
{
  "action": "stdin",
  "id": "backend-repl",
  "data": "def process_data(data): return data.upper()\r"
}

// Test JavaScript frontend
{
  "action": "stdin",
  "id": "frontend-repl",
  "data": "const formatData = (data) => data.toLowerCase()\r"
}

// List all active REPLs
{
  "action": "list"
}
```

### Code Prototyping Workflow

```json
// 1. Start REPL
{
  "action": "start",
  "command": "python3 -i",
  "name": "prototype"
}

// 2. Test idea
{
  "action": "stdin",
  "id": "prototype",
  "data": "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)\r"
}

// 3. Test with examples
{
  "action": "stdin",
  "id": "prototype",
  "data": "factorial(5)\r"
}

// 4. Check edge cases
{
  "action": "stdin",
  "id": "prototype",
  "data": "factorial(0)\r"
}

{
  "action": "stdin",
  "id": "prototype",
  "data": "factorial(1)\r"
}

// 5. Refine implementation
{
  "action": "stdin",
  "id": "prototype",
  "data": "def factorial_iterative(n):\r    result = 1\r    for i in range(2, n + 1):\r        result *= i\r    return result\r\r"
}

// 6. Compare performance
{
  "action": "stdin",
  "id": "prototype",
  "data": "import time\r"
}

{
  "action": "stdin",
  "id": "prototype",
  "data": "start = time.time(); factorial(100); print(time.time() - start)\r"
}

// 7. Capture final output
{
  "action": "stdout",
  "id": "prototype"
}
```

### Interactive Documentation Generation

```json
// 1. Start IPython
{
  "action": "start",
  "command": "ipython",
  "name": "doc-gen"
}

// 2. Import module
{
  "action": "stdin",
  "id": "doc-gen",
  "data": "import mymodule\r"
}

// 3. Get function signatures
{
  "action": "stdin",
  "id": "doc-gen",
  "data": "import inspect\r"
}

{
  "action": "stdin",
  "id": "doc-gen",
  "data": "inspect.signature(mymodule.my_function)\r"
}

// 4. Get docstrings
{
  "action": "stdin",
  "id": "doc-gen",
  "data": "mymodule.my_function.__doc__\r"
}

// 5. Test examples from docs
{
  "action": "stdin",
  "id": "doc-gen",
  "data": "mymodule.my_function('test')\r"
}

// 6. Extract for documentation
{
  "action": "stdout",
  "id": "doc-gen"
}
```

### Session State Management

```json
// Save current REPL state to file
{
  "action": "stdin",
  "id": "python-repl",
  "data": "import dill\r"
}

{
  "action": "stdin",
  "id": "python-repl",
  "data": "dill.dump_session('session.pkl')\r"
}

// Later, restore state
{
  "action": "stdin",
  "id": "python-repl",
  "data": "dill.load_session('session.pkl')\r"
}
```

## Best Practices

### REPL Session Hygiene

1. **Name sessions descriptively**: Use `name` that reflects purpose (e.g., "api-test", "data-explore")
2. **Clean up variables**: Use `del variable` to free memory
3. **Restart when needed**: Stop and start fresh sessions to avoid state pollution
4. **Use stream mode for long operations**: Avoid blocking on compute-intensive tasks

### Error Handling

```json
// Catch and inspect errors
{
  "action": "stdin",
  "id": "python-repl",
  "data": "try:\r    risky_operation()\rexcept Exception as e:\r    print(f'Error: {e}')\r    import traceback\r    traceback.print_exc()\r\r"
}
```

### Output Parsing

- Use `stdout` action after commands that produce output
- Parse REPL prompt patterns to extract results
- Use `stream` with `since_last: true` for incremental output
- Strip ANSI codes if needed for clean parsing

### Managing Long-Running Operations

```json
// Start long computation
{
  "action": "stdin",
  "id": "python-repl",
  "data": "result = expensive_computation()\r"
}

// Check progress with stream mode
{
  "action": "stream",
  "id": "python-repl",
  "since_last": true
}

// Don't block - continue other work
// Check back later with stdout
{
  "action": "stdout",
  "id": "python-repl"
}
```

### Multi-Session Coordination

```json
// List all active sessions
{
  "action": "list"
}

// Stop specific session
{
  "action": "stop",
  "id": "python-repl"
}

// Stop all sessions (clean shutdown)
// Iterate through list results and stop each
```

## Common REPL Workflows

### Quick Script Testing

1. Start REPL
2. Paste/type code snippets
3. Test with various inputs
4. Capture output
5. Refine code
6. Save final version to file

### Library Evaluation

1. Start REPL
2. Import library
3. Explore API with `dir()` and help
4. Test key functions
5. Measure performance with `%timeit`
6. Document findings

### Debugging Production Issues

1. Start REPL with production environment
2. Import relevant modules
3. Reproduce issue with test data
4. Inspect intermediate states
5. Test fixes
6. Verify solution

### Interactive Configuration

1. Start REPL
2. Load configuration
3. Test different settings
4. Validate outcomes
5. Save working configuration

This skill provides comprehensive patterns for AI-driven REPL interaction using terminalcp's persistent session management.
