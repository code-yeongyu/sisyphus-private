---
name: process-monitoring
description: Patterns for managing and monitoring long-running processes (builds, tests, servers, etc.) via terminalcp
---

# Process Monitoring with terminalcp

This skill provides comprehensive patterns for managing long-running processes using terminalcp MCP. It enables AI agents to start, monitor, control, and analyze processes without blocking execution.

## Overview

terminalcp enables:
- Non-blocking process execution and monitoring
- Real-time log streaming and analysis
- Process lifecycle management (start, stop, restart)
- Parallel process coordination
- Persistent sessions across disconnections

The MCP server runs via `npx @mariozechner/terminalcp@latest --mcp` and maintains background processes independently.

## Basic Process Management

### Starting a Long-Running Process

```json
{
  "action": "start",
  "command": "npm run dev",
  "name": "dev-server"
}
```

Returns a session ID for future reference.

### Checking Process Status

```json
{
  "action": "list"
}
```

Returns all active sessions with their names and IDs.

### Stopping a Process

```json
{
  "action": "stop",
  "id": "dev-server"
}
```

Terminates the process gracefully.

## Build Process Monitoring

### Running a Build

```json
// Start build process
{
  "action": "start",
  "command": "npm run build",
  "name": "build-process"
}

// Check build progress (non-blocking)
{
  "action": "stream",
  "id": "build-process",
  "since_last": true
}

// Get full output when complete
{
  "action": "stdout",
  "id": "build-process"
}
```

### Monitoring Compiler Output

```json
// Start TypeScript compiler in watch mode
{
  "action": "start",
  "command": "tsc --watch",
  "name": "tsc-watch"
}

// Periodically check for compilation errors
{
  "action": "stream",
  "id": "tsc-watch",
  "since_last": true
}

// Parse output for error patterns:
// "error TS2345:", "Found N errors", etc.
```

### Parallel Build Monitoring

```json
// Start frontend build
{
  "action": "start",
  "command": "npm run build:frontend",
  "name": "frontend-build"
}

// Start backend build
{
  "action": "start",
  "command": "npm run build:backend",
  "name": "backend-build"
}

// Monitor both in parallel
{
  "action": "stream",
  "id": "frontend-build",
  "since_last": true
}

{
  "action": "stream",
  "id": "backend-build",
  "since_last": true
}

// List all builds
{
  "action": "list"
}
```

## Test Process Management

### Running Test Suites

```json
// Start test runner
{
  "action": "start",
  "command": "pytest tests/ -v",
  "name": "test-run"
}

// Stream test results as they complete
{
  "action": "stream",
  "id": "test-run",
  "since_last": true
}

// Get final summary
{
  "action": "stdout",
  "id": "test-run"
}
```

### Watch Mode Testing

```json
// Start test watcher
{
  "action": "start",
  "command": "npm test -- --watch",
  "name": "test-watch"
}

// Monitor for test failures
{
  "action": "stream",
  "id": "test-watch",
  "since_last": true
}

// Parse output for:
// "FAIL", "PASS", test counts, coverage changes
```

### Continuous Integration Monitoring

```json
// Run full CI pipeline locally
{
  "action": "start",
  "command": "make ci",
  "name": "ci-pipeline"
}

// Check progress
{
  "action": "stream",
  "id": "ci-pipeline",
  "since_last": true
}

// Parse for stage completions:
// "✓ Lint", "✓ Test", "✓ Build", "✗ Deploy"
```

## Development Server Management

### Starting Development Servers

```json
// Start backend server
{
  "action": "start",
  "command": "uvicorn app:app --reload",
  "name": "backend-server"
}

// Start frontend dev server
{
  "action": "start",
  "command": "npm run dev",
  "name": "frontend-server"
}

// Start database
{
  "action": "start",
  "command": "docker-compose up postgres",
  "name": "database"
}
```

### Monitoring Server Startup

```json
// Check if server is ready
{
  "action": "stream",
  "id": "backend-server",
  "since_last": true
}

// Parse for readiness indicators:
// "Application startup complete"
// "Uvicorn running on http://127.0.0.1:8000"
// "Listening on port 3000"
```

### Server Log Analysis

```json
// Continuous log monitoring
{
  "action": "stream",
  "id": "backend-server",
  "since_last": true
}

// Parse logs for:
// - Error patterns (500 errors, exceptions)
// - Request patterns (endpoints hit, response times)
// - Warning messages
```

### Restarting Servers

```json
// Stop existing server
{
  "action": "stop",
  "id": "backend-server"
}

// Start new instance
{
  "action": "start",
  "command": "uvicorn app:app --reload",
  "name": "backend-server"
}

// Verify startup
{
  "action": "stream",
  "id": "backend-server",
  "since_last": true
}
```

## Docker Container Management

### Starting Docker Containers

```json
// Start docker-compose services
{
  "action": "start",
  "command": "docker-compose up",
  "name": "docker-services"
}

// Monitor startup logs
{
  "action": "stream",
  "id": "docker-services",
  "since_last": true
}

// Parse for:
// "Container started"
// "Listening on port..."
// Health check status
```

### Following Container Logs

```json
// Follow specific container logs
{
  "action": "start",
  "command": "docker logs -f mycontainer",
  "name": "container-logs"
}

// Stream logs
{
  "action": "stream",
  "id": "container-logs",
  "since_last": true
}
```

### Docker Build Monitoring

```json
// Start image build
{
  "action": "start",
  "command": "docker build -t myimage:latest .",
  "name": "docker-build"
}

// Monitor build progress
{
  "action": "stream",
  "id": "docker-build",
  "since_last": true
}

// Parse for:
// "Step 1/10", "Successfully built", errors
```

## Database Operations

### Running Database Migrations

```json
// Start migration
{
  "action": "start",
  "command": "alembic upgrade head",
  "name": "db-migration"
}

// Monitor progress
{
  "action": "stream",
  "id": "db-migration",
  "since_last": true
}

// Check completion
{
  "action": "stdout",
  "id": "db-migration"
}

// Parse for:
// "Running upgrade", "OK", errors
```

### Database Seeding

```json
// Start seed process
{
  "action": "start",
  "command": "python seed_database.py",
  "name": "db-seed"
}

// Monitor with progress updates
{
  "action": "stream",
  "id": "db-seed",
  "since_last": true
}

// Parse for:
// "Seeded X records", progress bars, completion
```

## Advanced Patterns

### Automated Deployment Pipeline

```json
// 1. Run tests
{
  "action": "start",
  "command": "pytest",
  "name": "deploy-test"
}

// 2. Wait for tests to complete
{
  "action": "stream",
  "id": "deploy-test",
  "since_last": true
}

// Parse output, if tests pass:

// 3. Build application
{
  "action": "start",
  "command": "npm run build",
  "name": "deploy-build"
}

// 4. Monitor build
{
  "action": "stream",
  "id": "deploy-build",
  "since_last": true
}

// If build succeeds:

// 5. Deploy
{
  "action": "start",
  "command": "npm run deploy",
  "name": "deploy-push"
}

// 6. Monitor deployment
{
  "action": "stream",
  "id": "deploy-push",
  "since_last": true
}

// 7. Clean up sessions
{
  "action": "stop",
  "id": "deploy-test"
}

{
  "action": "stop",
  "id": "deploy-build"
}

{
  "action": "stop",
  "id": "deploy-push"
}
```

### Multi-Service Health Monitoring

```json
// Start all services
{
  "action": "start",
  "command": "docker-compose up",
  "name": "services"
}

// Create monitoring loop
// Every 30 seconds:

{
  "action": "stream",
  "id": "services",
  "since_last": true
}

// Parse for error patterns:
// - "error", "exception", "failed"
// - Service restart indicators
// - Connection errors
// - Memory/resource issues

// If errors detected, alert and capture full context:
{
  "action": "stdout",
  "id": "services"
}
```

### Progressive Log Analysis

```json
// Start application
{
  "action": "start",
  "command": "node server.js",
  "name": "app-server"
}

// Continuous monitoring with analysis
// Stream logs in chunks:

{
  "action": "stream",
  "id": "app-server",
  "since_last": true
}

// Analyze each chunk:
// - Count error types
// - Track request patterns
// - Identify anomalies
// - Build metrics

// Aggregate findings over time
// Alert on threshold breaches
```

### Parallel Test Execution

```json
// Start unit tests
{
  "action": "start",
  "command": "pytest tests/unit -v",
  "name": "unit-tests"
}

// Start integration tests
{
  "action": "start",
  "command": "pytest tests/integration -v",
  "name": "integration-tests"
}

// Start e2e tests
{
  "action": "start",
  "command": "npm run test:e2e",
  "name": "e2e-tests"
}

// Monitor all in parallel
{
  "action": "stream",
  "id": "unit-tests",
  "since_last": true
}

{
  "action": "stream",
  "id": "integration-tests",
  "since_last": true
}

{
  "action": "stream",
  "id": "e2e-tests",
  "since_last": true
}

// Aggregate results when all complete
```

### Development Environment Bootstrap

```json
// 1. Start database
{
  "action": "start",
  "command": "docker-compose up postgres",
  "name": "dev-db"
}

// 2. Wait for database readiness
{
  "action": "stream",
  "id": "dev-db",
  "since_last": true
}

// Parse for: "database system is ready to accept connections"

// 3. Run migrations
{
  "action": "start",
  "command": "alembic upgrade head",
  "name": "dev-migrations"
}

{
  "action": "stdout",
  "id": "dev-migrations"
}

// 4. Seed data
{
  "action": "start",
  "command": "python seed.py",
  "name": "dev-seed"
}

// 5. Start backend
{
  "action": "start",
  "command": "uvicorn app:app --reload",
  "name": "dev-backend"
}

// 6. Start frontend
{
  "action": "start",
  "command": "npm run dev",
  "name": "dev-frontend"
}

// 7. Monitor all services
{
  "action": "list"
}
```

### Graceful Shutdown Orchestration

```json
// List all running processes
{
  "action": "list"
}

// Stop frontend first (no dependencies)
{
  "action": "stop",
  "id": "dev-frontend"
}

// Stop backend
{
  "action": "stop",
  "id": "dev-backend"
}

// Stop database last
{
  "action": "stop",
  "id": "dev-db"
}

// Verify all stopped
{
  "action": "list"
}
```

## Log Parsing Patterns

### Error Detection

```python
# Parse stream output for errors
error_patterns = [
    r"error:",
    r"ERROR",
    r"Exception:",
    r"Traceback",
    r"failed",
    r"\[ERROR\]",
    r"FAIL:",
    r"✗"
]

# Check each line from stream
for line in output.split('\n'):
    for pattern in error_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            # Found error, capture context
```

### Progress Tracking

```python
# Parse for progress indicators
progress_patterns = [
    r"(\d+)%",                          # Percentage
    r"(\d+)/(\d+)",                     # X of Y
    r"Step (\d+) of (\d+)",             # Build steps
    r"✓",                                # Success marks
    r"Running (\d+) tests?",            # Test count
]
```

### Performance Metrics

```python
# Extract timing information
timing_patterns = [
    r"Time: (\d+\.?\d*)s",
    r"Elapsed: (\d+:\d+)",
    r"Duration: (\d+)ms",
    r"in (\d+\.?\d*)s",
]
```

### Service Readiness

```python
# Detect when services are ready
readiness_patterns = [
    r"Application startup complete",
    r"Listening on .+:\d+",
    r"Server running at",
    r"Ready in (\d+)ms",
    r"Uvicorn running on",
    r"Started server on",
]
```

## Best Practices

### Monitoring Strategy

1. **Use stream mode for active monitoring**: Get incremental output without blocking
2. **Use stdout for final results**: Capture complete output when process completes
3. **Set monitoring intervals**: Don't poll too frequently (30s-60s is often sufficient)
4. **Parse incrementally**: Analyze each stream chunk as it arrives

### Process Naming

- Use descriptive names: `frontend-build`, not `build1`
- Include purpose: `test-integration`, `db-migration-prod`
- Use consistent naming conventions across workflows

### Resource Management

```json
// Always clean up completed processes
{
  "action": "stop",
  "id": "completed-process"
}

// Verify cleanup
{
  "action": "list"
}
```

### Error Handling

```json
// Check if process started successfully
{
  "action": "stream",
  "id": "new-process",
  "since_last": false
}

// Parse for startup errors:
// - "command not found"
// - "port already in use"
// - "permission denied"

// If errors detected, stop and report
{
  "action": "stop",
  "id": "new-process"
}
```

### Timeout Handling

- Set expectations for process duration
- Check for hangs via repeated stream calls with no new output
- Implement timeout logic in monitoring loops
- Force stop if process exceeds expected duration

### Log Retention

- Capture full stdout when process completes
- Store logs for analysis
- Parse and extract key metrics
- Clean up session after capturing logs

## Common Workflows

### CI/CD Pipeline Execution

1. Start all CI stages (lint, test, build)
2. Monitor each stage with stream
3. Parse for success/failure
4. Proceed to next stage or abort
5. Capture final results
6. Clean up sessions

### Development Environment

1. Start required services (DB, cache, etc.)
2. Wait for services to be ready
3. Start application servers
4. Monitor startup logs
5. Keep running, periodic health checks
6. Graceful shutdown on exit

### Performance Testing

1. Start application under test
2. Start load generator
3. Monitor both processes
4. Parse metrics from load generator
5. Detect performance degradation
6. Stop both processes
7. Analyze results

### Automated Testing

1. Start test suite
2. Stream test results in real-time
3. Parse for failures
4. Stop on first failure if needed
5. Capture full test report
6. Clean up

This skill provides comprehensive patterns for process management and monitoring using terminalcp's persistent session capabilities.
