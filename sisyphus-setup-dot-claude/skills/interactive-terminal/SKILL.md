---
name: interactive-terminal
description: Control interactive CLI/TUI applications (debuggers, REPLs, shells, database CLIs) using terminalcp. Use for language debuggers (pdb/gdb/lldb/node), REPL sessions, shell interactions, database clients (psql/mysql/redis), or monitoring long-running processes with stdin/stdout control.
---

# Interactive Terminal

## Overview

Enables interaction with CLI/TUI applications through background terminal sessions. Use `terminalcp` CLI to start sessions, send input, monitor output, and control interactive processes without blocking your workflow.

## Primary Use Cases

### Debugging & Development
- **pdb/pudb/ipdb**: Python debuggers - set breakpoints, step through code, inspect variables
- **python -i / IPython**: REPL for testing code snippets, API exploration
- **python manage.py shell / shell_plus**: Django ORM testing, database queries
- **node --inspect**: Node.js debugger sessions
- **gdb/lldb**: Native code debugging

### Interactive Shells & Tools
- **bash/zsh sessions**: Long-running shell operations
- **psql/mysql**: Database CLI interactions
- **redis-cli**: Redis command-line testing
- **kubectl exec -it**: Interactive pod shells

### Build & Test Monitoring
- **pytest -v**: Watch test output incrementally
- **npm run dev**: Monitor dev server logs
- **docker logs -f**: Follow container output

## Core Commands

### Session Management
```bash
# Start session
terminalcp start <session-id> "<command>"

# List all sessions
terminalcp list

# Stop session(s)
terminalcp stop <session-id>  # specific
terminalcp stop                # all sessions
```

### Input/Output
```bash
# Send input (use \r for Enter)
terminalcp stdin <session-id> "command\r"

# Get terminal screen output
terminalcp stdout <session-id> [lines]

# Get raw stream output
terminalcp stream <session-id> [--since-last] [--with-ansi]
```

## Common Patterns

### Debugger Sessions

**Python (pdb/pudb)**
```bash
terminalcp start debug "python -m pdb script.py"
sleep 1
terminalcp stdin debug "b main\r"
terminalcp stdin debug "c\r"
terminalcp stdin debug "n\r"  # next
terminalcp stdin debug "p variable\r"  # print
terminalcp stdout debug 20
```

**Node.js**
```bash
terminalcp start node-debug "node inspect app.js"
sleep 1
terminalcp stdin node-debug "sb(10)\r"  # set breakpoint line 10
terminalcp stdin node-debug "c\r"  # continue
terminalcp stdin node-debug "repl\r"  # enter REPL mode
terminalcp stdout node-debug
```

**GDB (C/C++)**
```bash
terminalcp start gdb "gdb ./myapp"
sleep 1
terminalcp stdin gdb "break main\r"
terminalcp stdin gdb "run\r"
terminalcp stdin gdb "next\r"
terminalcp stdin gdb "print myvar\r"
terminalcp stdout gdb
```

### Database CLIs

**PostgreSQL**
```bash
terminalcp start psql "psql -U user -d dbname"
sleep 1
terminalcp stdin psql "SELECT * FROM users LIMIT 10;\r"
terminalcp stdout psql
terminalcp stdin psql "\\dt\r"  # list tables
terminalcp stdout psql
```

**Redis**
```bash
terminalcp start redis "redis-cli"
sleep 1
terminalcp stdin redis "KEYS *\r"
terminalcp stdin redis "GET mykey\r"
terminalcp stdout redis
```

**MySQL**
```bash
terminalcp start mysql "mysql -u root -p"
sleep 2
terminalcp stdin mysql "password123\r"
terminalcp stdin mysql "SHOW DATABASES;\r"
terminalcp stdout mysql
```

### REPL Sessions

**Python**
```bash
terminalcp start py "python3 -i"
terminalcp stdin py "import requests\r"
terminalcp stdin py "r = requests.get('https://api.example.com')\r"
terminalcp stdout py
```

**Node.js**
```bash
terminalcp start node "node"
terminalcp stdin node "const fs = require('fs')\r"
terminalcp stdin node "fs.readdirSync('.')\r"
terminalcp stdout node
```

**Ruby**
```bash
terminalcp start irb "irb"
terminalcp stdin irb "require 'net/http'\r"
terminalcp stdin irb "puts 'Hello'.upcase\r"
terminalcp stdout irb
```

### Incremental Build Monitoring
```bash
# Start build in background
terminalcp start build "npm run build"

# Poll for new output only (efficient for long builds)
while true; do
  terminalcp stream build --since-last
  sleep 2
done

terminalcp stop build
```

### Framework Shells

**Django**
```bash
terminalcp start django "python manage.py shell_plus"
sleep 2
terminalcp stdin django "User.objects.count()\r"
terminalcp stdout django
```

**Rails**
```bash
terminalcp start rails "rails console"
sleep 2
terminalcp stdin rails "User.count\r"
terminalcp stdout rails
```

## Output Modes

### stdout (Terminal Emulator)
- Rendered screen as user sees it
- 10K lines scrollback limit
- Best for: TUI apps, interactive shells, debuggers
```bash
terminalcp stdout <session-id> [lines]
```

### stream (Raw Output)
- Complete stdout/stderr from process start
- ANSI codes stripped by default (`--with-ansi` to keep)
- Unlimited history
- `--since-last`: Only new output since last call
- Best for: Build logs, test output, monitoring
```bash
terminalcp stream <session-id>              # all output
terminalcp stream <session-id> --since-last  # incremental
```

## Limitations

### Escape Sequences (CLI)
❌ Arrow keys, ESC, function keys **do NOT work** via CLI
- `\u001b[A` (Up), `\u001b[D` (Left) sent as literal strings
- Affects: vim navigation, shell history, TUI cursor movement

✅ **Working escape sequences:**
- `\r` - Enter
- `\t` - Tab
- `\u0003` - Ctrl+C

**Workaround**: Use commands that don't require cursor navigation. For complex TUI interactions, consider alternative approaches or direct attachment.

### Shell Compatibility
- Commands run via `bash -c` by default
- If default shell is fish/zsh, wrap bash syntax: `bash -c 'command'`

## Key Strategies

### Incremental Monitoring
Use `--since-last` to avoid re-processing output:
```bash
terminalcp stream build --since-last  # 1st call: all output
terminalcp stream build --since-last  # 2nd call: only new lines
```

### Session Cleanup
Always stop sessions when done to free resources:
```bash
# At end of workflow
terminalcp stop  # stops all sessions
```

### Timing Considerations
Add `sleep` after `start` before first interaction:
```bash
terminalcp start py "python3 -i"
sleep 1  # let process initialize
terminalcp stdin py "2+2\r"
```

## Troubleshooting

If `terminalcp` not found, see [docs/installation.md](docs/installation.md) for setup.

## Resources

### docs/
Detailed documentation for installation and advanced usage patterns.
