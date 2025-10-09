# Multi-Agent Session Management Analysis

## Overview
This document provides a comprehensive analysis of session management mechanisms for three AI coding agents: Claude Agent SDK, Droid CLI, and OpenCode. Each agent has distinct session handling approaches that need to be properly abstracted for a unified multi-agent system.

## 1. Claude Agent SDK

### Session Storage
- **Format**: JSON file (`agentloop.json` by default)
- **Location**: Working directory (configurable)
- **Structure**:
```json
{
  "session_ids": ["uuid-1", "uuid-2", ...],
  "last_updated": "timestamp",
  "last_prompt": "last executed prompt"
}
```

### Session ID Format
- **Type**: UUID v4 format
- **Pattern**: `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`
- **Example**: `550e8400-e29b-41d4-a716-446655440000`

### Session Management Strategy
- **Default Behavior**: Resume last session, create new on failure
- **Resume Logic**:
  1. Load session file
  2. Get last session ID from list
  3. Validate UUID format
  4. Pass to ClaudeAgentOptions with `resume` parameter
  5. If resume fails, create new session without resume
- **Session Tracking**: Maintains list of all session IDs
- **Persistence**: Save after each session initialization

### API Implementation
```python
class ClaudeAgentOptions:
    resume: str | None  # Session ID to resume
    permission_mode: str
    include_partial_messages: bool

class SessionManager:
    def get_last_session_id() -> str | None
    def add_session_id(session_id: str)
    def save_session_data()
```

### Key Features
- Automatic session recovery
- Multiple session history tracking
- Graceful fallback to new session on resume failure
- Session metadata storage (prompt, timestamp)

## 2. Droid CLI

### Session Storage
- **Format**: Client-managed (no built-in persistence)
- **Location**: N/A (client responsibility)
- **Session ID**: Must be provided by client

### Session ID Format
- **Type**: UUID format (client-generated)
- **Pattern**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **Example**: Must be valid UUID

### Session Management Strategy
- **Default Behavior**: No session by default
- **Resume Logic**:
  1. Client provides session ID via `-s/--session-id` flag
  2. Must provide new prompt with session ID
  3. No built-in session validation
- **Session Tracking**: Client responsibility
- **Persistence**: None built-in

### CLI Implementation
```bash
# New session (no session ID)
droid exec "task"

# Resume session (requires prompt)
droid exec -s <session-id> "continue work"

# Stream JSON mode for programmatic use
droid exec --input-format stream-json --output-format stream-json
```

### Python SDK Approach
```python
class DroidSession:
    id: Optional[str] = None  # Client manages
    model: str
    autonomy: str

# Client must:
# 1. Generate UUID for new sessions
# 2. Store session IDs persistently
# 3. Provide session ID for resume
```

### Key Features
- Lightweight, no built-in persistence
- Client has full control over session management
- Supports multi-turn via stream-json format
- Session resume requires new prompt

## 3. OpenCode

### Session Storage
- **Format**: JSON files in hierarchical directory structure
- **Location**: `~/.local/share/opencode/storage/session/`
- **Structure**:
  - Project directories (SHA hash)
  - Session JSON files per project
  - Message and part storage separate

### Session File Structure
```json
{
  "id": "ses_674040488ffeXSOX26w2OGwb60",
  "version": "0.12.1",
  "projectID": "1e70143eddb2db46524b99873f4a9b75f2be28c5",
  "directory": "/Users/yeongyu/local-workspaces/project",
  "title": "Session title",
  "time": {
    "created": 1758990170999,
    "updated": 1758990174571
  }
}
```

### Session Management Strategy
- **Default Behavior**: Auto-save, resume last session
- **Resume Logic**:
  1. CLI: `-c/--continue` flag for last session
  2. CLI: `-s/--session <id>` for specific session
  3. Server: POST /session for new, GET /session/:id for resume
- **Session Tracking**: SQLite + file system storage
- **Persistence**: Automatic with configurable intervals

### Server API Implementation
```python
# Create session
POST /session
{
  "model": "gpt-4",
  "agent": "default",
  "prompt": "initial"
}

# Resume session
GET /session/:id

# Send message to session
POST /session/:id/message
{
  "content": "message",
  "role": "user"
}
```

### Storage Configuration
```yaml
session:
  auto_save: true
  save_interval: 30  # seconds
  history_limit: 1000  # messages
  cleanup_after: 30  # days
```

### Key Features
- Automatic session persistence
- Project-based session organization
- Server mode with REST API
- SSE streaming for real-time updates
- SQLite for metadata, filesystem for content

## Comparison Table

| Feature | Claude Agent SDK | Droid CLI | OpenCode |
|---------|-----------------|-----------|----------|
| **Storage Format** | JSON file | None (client-managed) | JSON + SQLite |
| **Storage Location** | Working directory | N/A | ~/.local/share/opencode |
| **Session ID Format** | UUID v4 | UUID (client) | Custom (ses_xxx) |
| **Auto-persist** | Yes | No | Yes |
| **Resume Method** | Auto with fallback | Manual with flag | Auto or manual |
| **Multi-session** | List tracking | Client managed | Project-based |
| **API Type** | Python SDK | CLI/subprocess | REST API + CLI |
| **Streaming** | Native | JSONL | SSE |
| **Session Validation** | UUID format check | None | Server-side |
| **Prompt Required for Resume** | No | Yes | No |

## Unified Session Management Design Recommendations

### Core Requirements
1. **Abstract Session Interface**
```python
class SessionInterface(Protocol):
    async def create_session(self, **kwargs) -> SessionInfo
    async def resume_session(self, session_id: str) -> SessionInfo
    async def list_sessions(self) -> List[SessionInfo]
    async def delete_session(self, session_id: str) -> bool
    async def save_session_state(self, session_id: str, state: dict)
```

2. **Unified Session Storage**
```python
class UnifiedSessionStore:
    # Central storage for all agents
    # SQLite for metadata
    # JSON files for agent-specific data
    # Configurable paths per agent type
```

3. **Session ID Mapping**
- Internal unified ID (UUID v4)
- Agent-specific ID mapping
- Translation layer for each agent

4. **Resume Strategy**
```python
class ResumeStrategy(Enum):
    ALWAYS_RESUME = "always"  # Try resume, fail if not possible
    RESUME_OR_NEW = "resume_or_new"  # Try resume, create new on fail
    ALWAYS_NEW = "always_new"  # Never resume
    MANUAL = "manual"  # User decides
```

5. **Session State Tracking**
```python
@dataclass
class SessionState:
    id: str
    agent_type: AgentType
    agent_session_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    status: SessionStatus
    metadata: Dict[str, Any]
    prompt_history: List[str]
    resume_count: int
    last_error: Optional[str]
```

### Implementation Considerations

#### For Claude Agent SDK
- Use existing SessionManager pattern
- Map internal session IDs to Claude's UUIDs
- Leverage built-in resume with fallback

#### For Droid CLI
- Implement client-side session management
- Generate and track UUIDs
- Store session-prompt pairs for resume
- Handle stream-json mode for multi-turn

#### For OpenCode
- Use REST API for server mode
- Parse CLI output for direct mode
- Map project directories to unified sessions
- Handle both auto-save and manual save

### Session Lifecycle Management

1. **Creation**
   - Generate unified session ID
   - Initialize agent-specific session
   - Store mapping and metadata
   - Set up logging and state tracking

2. **Resume**
   - Load session metadata
   - Attempt agent-specific resume
   - Handle failures with strategy
   - Update state and counters

3. **Persistence**
   - Periodic auto-save for active sessions
   - Save on significant events
   - Agent-specific persistence hooks
   - Cleanup old sessions

4. **Termination**
   - Graceful shutdown
   - Final state save
   - Resource cleanup
   - Archive if configured

### Error Handling

1. **Resume Failures**
   - Claude: Automatic fallback to new session
   - Droid: Retry with new session ID
   - OpenCode: Check server status, retry or new

2. **Storage Failures**
   - Fallback to memory-only mode
   - Queue saves for retry
   - Alert user of persistence issues

3. **Agent Crashes**
   - Detect via heartbeat/timeout
   - Save partial state
   - Mark session as crashed
   - Offer recovery options

## Configuration Schema

```yaml
session_management:
  storage:
    base_path: "~/.local/share/multi-agent"
    sqlite_db: "sessions.db"

  agents:
    claude:
      session_file: "claude_sessions.json"
      resume_strategy: "resume_or_new"
      timeout: 300

    droid:
      session_tracking: true
      prompt_required_for_resume: true
      resume_strategy: "manual"

    opencode:
      server_mode: true
      server_url: "http://localhost:4096"
      resume_strategy: "resume_or_new"
      auto_save_interval: 30

  global:
    max_sessions_per_agent: 10
    cleanup_after_days: 30
    auto_save: true
    save_interval: 60
```

## Testing Considerations

1. **Session Creation Tests**
   - Verify unique ID generation
   - Test agent-specific initialization
   - Validate metadata storage

2. **Resume Tests**
   - Test successful resume for each agent
   - Test resume failure handling
   - Test strategy application

3. **Concurrency Tests**
   - Multiple agents with sessions
   - Concurrent session operations
   - Race condition handling

4. **Persistence Tests**
   - Save/load cycle integrity
   - Corruption recovery
   - Migration between versions

5. **Integration Tests**
   - Full lifecycle per agent
   - Cross-agent session switching
   - Error recovery scenarios