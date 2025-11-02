---
name: tui-applications
description: Patterns for controlling TUI applications (vim, htop, tig, lazygit, etc.) via terminalcp
---

# TUI Applications Control with terminalcp

This skill provides comprehensive patterns for automating Text User Interface (TUI) applications using terminalcp MCP. It enables AI agents to control interactive terminal applications with full visual feedback.

## Overview

terminalcp enables:
- Full PTY terminal emulation for TUI apps
- ANSI color and cursor positioning preservation
- Complex key sequence automation
- Screen content capture and parsing
- Multi-TUI session management

The MCP server runs via `npx @mariozechner/terminalcp@latest --mcp` and provides complete terminal rendering.

## Vim/Neovim Automation

### Starting Vim/Neovim

```json
// Open file in vim
{
  "action": "start",
  "command": "vim myfile.txt",
  "name": "vim-session"
}

// Open file in neovim
{
  "action": "start",
  "command": "nvim myfile.txt",
  "name": "nvim-session"
}

// Start vim without file
{
  "action": "start",
  "command": "vim",
  "name": "vim-session"
}
```

### Vim Mode Navigation

```json
// Enter insert mode
{
  "action": "stdin",
  "id": "vim-session",
  "data": "i"
}

// Type text
{
  "action": "stdin",
  "id": "vim-session",
  "data": "Hello, World!"
}

// Exit insert mode (Escape)
{
  "action": "stdin",
  "id": "vim-session",
  "data": "\u001b"
}

// Move cursor (in normal mode)
{
  "action": "stdin",
  "id": "vim-session",
  "data": "h"  // left
}

{
  "action": "stdin",
  "id": "vim-session",
  "data": "j"  // down
}

{
  "action": "stdin",
  "id": "vim-session",
  "data": "k"  // up
}

{
  "action": "stdin",
  "id": "vim-session",
  "data": "l"  // right
}
```

Note: `\u001b` is the Escape key in MCP notation.

### Vim Editing Commands

```json
// Delete line
{
  "action": "stdin",
  "id": "vim-session",
  "data": "dd"
}

// Undo
{
  "action": "stdin",
  "id": "vim-session",
  "data": "u"
}

// Redo
{
  "action": "stdin",
  "id": "vim-session",
  "data": "\u0012"  // Ctrl+R
}

// Copy line (yank)
{
  "action": "stdin",
  "id": "vim-session",
  "data": "yy"
}

// Paste
{
  "action": "stdin",
  "id": "vim-session",
  "data": "p"
}

// Find and replace
{
  "action": "stdin",
  "id": "vim-session",
  "data": ":%s/old/new/g\r"
}
```

### Vim File Operations

```json
// Save file
{
  "action": "stdin",
  "id": "vim-session",
  "data": ":w\r"
}

// Save and quit
{
  "action": "stdin",
  "id": "vim-session",
  "data": ":wq\r"
}

// Quit without saving
{
  "action": "stdin",
  "id": "vim-session",
  "data": ":q!\r"
}

// Open another file
{
  "action": "stdin",
  "id": "vim-session",
  "data": ":e another_file.txt\r"
}

// Save as
{
  "action": "stdin",
  "id": "vim-session",
  "data": ":saveas newfile.txt\r"
}
```

### Vim Search and Navigation

```json
// Search forward
{
  "action": "stdin",
  "id": "vim-session",
  "data": "/search_term\r"
}

// Search backward
{
  "action": "stdin",
  "id": "vim-session",
  "data": "?search_term\r"
}

// Next search result
{
  "action": "stdin",
  "id": "vim-session",
  "data": "n"
}

// Previous search result
{
  "action": "stdin",
  "id": "vim-session",
  "data": "N"
}

// Go to line
{
  "action": "stdin",
  "id": "vim-session",
  "data": ":42\r"
}

// Go to end of file
{
  "action": "stdin",
  "id": "vim-session",
  "data": "G"
}

// Go to beginning of file
{
  "action": "stdin",
  "id": "vim-session",
  "data": "gg"
}
```

### Vim Visual Mode

```json
// Enter visual mode
{
  "action": "stdin",
  "id": "vim-session",
  "data": "v"
}

// Select text (move cursor while in visual mode)
{
  "action": "stdin",
  "id": "vim-session",
  "data": "jjj"  // Select 3 lines down
}

// Copy selection
{
  "action": "stdin",
  "id": "vim-session",
  "data": "y"
}

// Exit visual mode
{
  "action": "stdin",
  "id": "vim-session",
  "data": "\u001b"
}
```

### Capturing Vim Screen

```json
{
  "action": "stdout",
  "id": "vim-session"
}
```

This returns the full terminal rendering including vim's UI, status line, and content.

## System Monitoring TUIs

### htop

```json
// Start htop
{
  "action": "start",
  "command": "htop",
  "name": "htop-session"
}

// Navigate processes
{
  "action": "stdin",
  "id": "htop-session",
  "data": "\u001b[B"  // Down arrow
}

{
  "action": "stdin",
  "id": "htop-session",
  "data": "\u001b[A"  // Up arrow
}

// Sort by CPU
{
  "action": "stdin",
  "id": "htop-session",
  "data": "P"
}

// Sort by memory
{
  "action": "stdin",
  "id": "htop-session",
  "data": "M"
}

// Filter processes
{
  "action": "stdin",
  "id": "htop-session",
  "data": "F4"
}

{
  "action": "stdin",
  "id": "htop-session",
  "data": "python\r"
}

// Kill process
{
  "action": "stdin",
  "id": "htop-session",
  "data": "F9"
}

// Capture current state
{
  "action": "stdout",
  "id": "htop-session"
}

// Quit
{
  "action": "stdin",
  "id": "htop-session",
  "data": "q"
}
```

### btop

```json
// Start btop
{
  "action": "start",
  "command": "btop",
  "name": "btop-session"
}

// Toggle menu
{
  "action": "stdin",
  "id": "btop-session",
  "data": "m"
}

// Switch views
{
  "action": "stdin",
  "id": "btop-session",
  "data": "1"  // CPU view
}

{
  "action": "stdin",
  "id": "btop-session",
  "data": "2"  // Memory view
}

{
  "action": "stdin",
  "id": "btop-session",
  "data": "3"  // Network view
}

// Capture state
{
  "action": "stdout",
  "id": "btop-session"
}
```

## Git TUIs

### tig

```json
// Start tig (git commit history viewer)
{
  "action": "start",
  "command": "tig",
  "name": "tig-session"
}

// Navigate commits
{
  "action": "stdin",
  "id": "tig-session",
  "data": "j"  // Next commit
}

{
  "action": "stdin",
  "id": "tig-session",
  "data": "k"  // Previous commit
}

// View commit details
{
  "action": "stdin",
  "id": "tig-session",
  "data": "\r"  // Enter to view diff
}

// Search
{
  "action": "stdin",
  "id": "tig-session",
  "data": "/search_term\r"
}

// View specific branch
{
  "action": "stdin",
  "id": "tig-session",
  "data": ":toggle refs\r"
}

// Capture view
{
  "action": "stdout",
  "id": "tig-session"
}

// Quit
{
  "action": "stdin",
  "id": "tig-session",
  "data": "q"
}
```

### lazygit

```json
// Start lazygit
{
  "action": "start",
  "command": "lazygit",
  "name": "lazygit-session"
}

// Navigate panels
{
  "action": "stdin",
  "id": "lazygit-session",
  "data": "1"  // Files panel
}

{
  "action": "stdin",
  "id": "lazygit-session",
  "data": "2"  // Branches panel
}

{
  "action": "stdin",
  "id": "lazygit-session",
  "data": "3"  // Commits panel
}

// Stage file
{
  "action": "stdin",
  "id": "lazygit-session",
  "data": " "  // Space to stage
}

// Commit
{
  "action": "stdin",
  "id": "lazygit-session",
  "data": "c"
}

{
  "action": "stdin",
  "id": "lazygit-session",
  "data": "Commit message\u001b:wq\r"
}

// Push
{
  "action": "stdin",
  "id": "lazygit-session",
  "data": "P"
}

// Capture state
{
  "action": "stdout",
  "id": "lazygit-session"
}

// Quit
{
  "action": "stdin",
  "id": "lazygit-session",
  "data": "q"
}
```

## File Managers

### ranger

```json
// Start ranger file manager
{
  "action": "start",
  "command": "ranger",
  "name": "ranger-session"
}

// Navigate
{
  "action": "stdin",
  "id": "ranger-session",
  "data": "j"  // Down
}

{
  "action": "stdin",
  "id": "ranger-session",
  "data": "k"  // Up
}

{
  "action": "stdin",
  "id": "ranger-session",
  "data": "l"  // Enter directory
}

{
  "action": "stdin",
  "id": "ranger-session",
  "data": "h"  // Go up directory
}

// Search
{
  "action": "stdin",
  "id": "ranger-session",
  "data": "/filename\r"
}

// Delete file
{
  "action": "stdin",
  "id": "ranger-session",
  "data": "dD"
}

// Capture current view
{
  "action": "stdout",
  "id": "ranger-session"
}

// Quit
{
  "action": "stdin",
  "id": "ranger-session",
  "data": "q"
}
```

## Database TUIs

### mycli (MySQL client)

```json
// Start mycli
{
  "action": "start",
  "command": "mycli -u user -p password -D database",
  "name": "mycli-session"
}

// Execute query
{
  "action": "stdin",
  "id": "mycli-session",
  "data": "SELECT * FROM users LIMIT 10;\r"
}

// Navigate results with arrow keys
{
  "action": "stdin",
  "id": "mycli-session",
  "data": "\u001b[B"  // Scroll down
}

// Capture results
{
  "action": "stdout",
  "id": "mycli-session"
}

// Exit
{
  "action": "stdin",
  "id": "mycli-session",
  "data": "\\q\r"
}
```

### pgcli (PostgreSQL client)

```json
// Start pgcli
{
  "action": "start",
  "command": "pgcli -h localhost -U user database",
  "name": "pgcli-session"
}

// Execute query
{
  "action": "stdin",
  "id": "pgcli-session",
  "data": "SELECT * FROM products WHERE price > 100;\r"
}

// Capture output
{
  "action": "stdout",
  "id": "pgcli-session"
}
```

## Advanced Patterns

### Automated Code Editing Workflow

```json
// 1. Open file in vim
{
  "action": "start",
  "command": "vim script.py",
  "name": "edit-session"
}

// 2. Go to specific line
{
  "action": "stdin",
  "id": "edit-session",
  "data": ":50\r"
}

// 3. Enter insert mode
{
  "action": "stdin",
  "id": "edit-session",
  "data": "i"
}

// 4. Type new code
{
  "action": "stdin",
  "id": "edit-session",
  "data": "    print('Debug info')\r"
}

// 5. Exit insert mode
{
  "action": "stdin",
  "id": "edit-session",
  "data": "\u001b"
}

// 6. Save file
{
  "action": "stdin",
  "id": "edit-session",
  "data": ":w\r"
}

// 7. Capture result
{
  "action": "stdout",
  "id": "edit-session"
}

// 8. Quit
{
  "action": "stdin",
  "id": "edit-session",
  "data": ":q\r"
}
```

### System Monitoring and Alert

```json
// 1. Start htop
{
  "action": "start",
  "command": "htop",
  "name": "monitor"
}

// 2. Sort by CPU
{
  "action": "stdin",
  "id": "monitor",
  "data": "P"
}

// 3. Capture current state
{
  "action": "stdout",
  "id": "monitor"
}

// Parse output for high CPU processes...
// If high CPU detected, capture more details

// 4. Periodic monitoring with stream mode
{
  "action": "stream",
  "id": "monitor",
  "since_last": true
}

// Continue monitoring...
```

### Git Workflow Automation

```json
// 1. Start tig to review changes
{
  "action": "start",
  "command": "tig status",
  "name": "git-review"
}

// 2. Navigate to unstaged file
{
  "action": "stdin",
  "id": "git-review",
  "data": "j"
}

// 3. View diff
{
  "action": "stdin",
  "id": "git-review",
  "data": "\r"
}

// 4. Capture diff view
{
  "action": "stdout",
  "id": "git-review"
}

// 5. Stage file
{
  "action": "stdin",
  "id": "git-review",
  "data": "u"
}

// 6. Quit tig
{
  "action": "stdin",
  "id": "git-review",
  "data": "q"
}

// 7. Start lazygit for commit
{
  "action": "start",
  "command": "lazygit",
  "name": "git-commit"
}

// 8. Commit staged files
{
  "action": "stdin",
  "id": "git-commit",
  "data": "c"
}

{
  "action": "stdin",
  "id": "git-commit",
  "data": "iCommit message\u001b:wq\r"
}

// 9. Capture result
{
  "action": "stdout",
  "id": "git-commit"
}
```

### Database Query and Analysis

```json
// 1. Start database client
{
  "action": "start",
  "command": "mycli -u root mydb",
  "name": "db-query"
}

// 2. Run analysis query
{
  "action": "stdin",
  "id": "db-query",
  "data": "SELECT category, COUNT(*), AVG(price) FROM products GROUP BY category;\r"
}

// 3. Capture results
{
  "action": "stdout",
  "id": "db-query"
}

// Parse results...

// 4. Run follow-up query based on analysis
{
  "action": "stdin",
  "id": "db-query",
  "data": "SELECT * FROM products WHERE category = 'electronics' ORDER BY price DESC LIMIT 5;\r"
}

// 5. Capture final results
{
  "action": "stdout",
  "id": "db-query"
}

// 6. Exit
{
  "action": "stdin",
  "id": "db-query",
  "data": "\\q\r"
}
```

## Key Sequences Reference

### Special Keys in MCP Notation

```
Enter:      \r
Escape:     \u001b
Tab:        \t
Ctrl+C:     \u0003
Ctrl+D:     \u0004
Ctrl+Z:     \u001a
Ctrl+R:     \u0012
Ctrl+L:     \u000c
Backspace:  \u007f
Up Arrow:   \u001b[A
Down Arrow: \u001b[B
Right Arrow: \u001b[C
Left Arrow: \u001b[D
Home:       \u001b[H
End:        \u001b[F
Page Up:    \u001b[5~
Page Down:  \u001b[6~
Delete:     \u001b[3~
F1-F12:     \u001bOP to \u001b[24~
```

### Vim Key Combinations

```
Ctrl+W + W:  Switch windows
Ctrl+W + V:  Vertical split
Ctrl+W + S:  Horizontal split
Ctrl+F:      Page down
Ctrl+B:      Page up
Ctrl+U:      Half page up
Ctrl+D:      Half page down
```

## Best Practices

### Screen Capture Timing

- Capture after significant actions complete
- Use `stream` mode for continuous monitoring
- Wait for UI to settle before capture
- Parse output carefully - TUIs include ANSI codes

### Navigation Strategy

- Use shortcuts when available (e.g., `gg` in vim vs many `k` presses)
- Learn application-specific navigation
- Test key sequences in isolation first
- Handle different terminal sizes

### Error Handling

```json
// Vim: Handle if file doesn't exist
// Check output after :e command
{
  "action": "stdout",
  "id": "vim-session"
}
// Parse for error messages like "Cannot open file"
```

### Session Management

- Name TUI sessions by purpose
- Close applications gracefully (quit commands)
- Use `stop` action if application hangs
- List sessions to track active TUIs

### Output Parsing

- TUI output includes formatting codes
- Use regex to extract data from formatted tables
- Be aware of terminal width affecting layout
- Strip ANSI codes for text-only analysis

## Common TUI Workflows

### Quick File Edit

1. Open vim with file
2. Navigate to target location
3. Make changes in insert mode
4. Save and quit

### System Health Check

1. Start htop
2. Capture CPU/memory state
3. Identify high-usage processes
4. Document findings

### Git Change Review

1. Start tig or lazygit
2. Navigate through commits/changes
3. Capture relevant diffs
4. Make staging/commit decisions

### Database Investigation

1. Connect to database with TUI client
2. Run exploratory queries
3. Capture results
4. Refine queries based on findings

This skill provides comprehensive automation patterns for TUI applications using terminalcp's full terminal emulation capabilities.
