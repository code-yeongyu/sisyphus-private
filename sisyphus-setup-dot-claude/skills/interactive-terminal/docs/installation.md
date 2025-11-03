# Installation & Troubleshooting

## Installation

### Quick Install
```bash
npm install -g @mariozechner/terminalcp@latest
```

### Verify Installation
```bash
terminalcp --version
```

Expected output: Client and server version numbers

## Common Issues

### Command Not Found
**Error**: `terminalcp: command not found`

**Solutions**:
1. Check npm global bin path is in PATH:
   ```bash
   npm config get prefix
   # Add <prefix>/bin to PATH if missing
   ```

2. Reinstall with proper permissions:
   ```bash
   npm install -g @mariozechner/terminalcp@latest
   ```

3. Use npx as alternative (no install needed):
   ```bash
   npx @mariozechner/terminalcp list
   ```

### Server Connection Issues
**Error**: Connection refused or timeout

**Solutions**:
1. Server auto-starts on first command, wait a moment and retry
2. Manually restart server:
   ```bash
   terminalcp kill-server
   terminalcp list  # auto-starts server
   ```

### Session Not Responding
**Issue**: stdin commands not working

**Diagnostics**:
```bash
# Check session status
terminalcp list

# View current output
terminalcp stdout <session-id>
```

**Common causes**:
- Process still initializing (add `sleep` delays)
- Process exited (check `Status: stopped` in list)
- Escape sequences sent as literals (CLI limitation)

## Compatibility

- **Node.js**: v14+ required
- **OS**: macOS, Linux, WSL2
- **Shells**: Tested with bash, zsh, fish (wrap bash syntax in quotes)

## Alternative: MCP Tool

For complex TUI interactions requiring full escape sequence support, use the MCP tool `mcp__terminalcp__terminalcp` which properly handles all control characters.
