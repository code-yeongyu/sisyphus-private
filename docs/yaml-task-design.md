# YAML Task Planning System - Design Document

## Overview

A graph-based task planning system using YAML format with pointer references, nested subtasks, programmatic verification, and automatic splitting capabilities.

## Core Design Principles

### 1. **DAG (Directed Acyclic Graph) Structure**
- Tasks form a directed graph via `depends_on` relationships
- No circular dependencies allowed (enforced by validator)
- Topological sort determines execution order
- Parallel execution where dependencies allow

### 2. **Pointer-Based References**
- Tasks identified by unique IDs (e.g., `t1`, `t2.1`, `ct1`)
- References use ID strings, not object embedding
- External file references for complex subtask trees
- Bidirectional links: `depends_on` (predecessors), `blocks` (successors)

### 3. **Hierarchical Task Structure**
```
Task (t1)
├── Subtask (t1.1)
│   ├── Subtask (t1.1.1)
│   └── Subtask (t1.1.2)
├── Subtask (t1.2) [references external file]
└── Subtask (t1.3)
```

### 4. **Programmatic Verification**
Multiple verification types composable via AND/OR logic:
- **command**: Execute shell command, check exit code
- **http**: REST API call, validate response
- **prompt**: LLM-based semantic verification
- **manual**: Human approval required
- **subtasks_complete**: All children must finish
- **composite**: Combine multiple checks with AND/OR
- **static_analysis**: Run linters, type checkers
- **coverage**: Code coverage thresholds

### 5. **Critical Task System**
- Runtime-discovered issues (bugs, security, blockers)
- Automatically extends agent loop
- High priority, blocks project completion
- Linked to original tasks for context

### 6. **Auto-Splitting Strategy**
Triggers when:
- Total tasks > threshold (default: 30)
- Nesting depth > limit (default: 3)
- File size > limit (default: 10KB)

Split methods:
- **by_milestone**: One file per milestone
- **by_size**: Balanced task distribution
- **by_complexity**: Group by dependency chains

## YAML Schema Structure

### Complete Example

```yaml
# ==============================================================================
# METADATA
# ==============================================================================
schema_version: "1.0.0"

project:
  id: "proj_auth_system"
  name: "User Authentication System"
  description: "Implement JWT-based authentication with OAuth2 support"
  repository: "https://github.com/org/repo"
  created_at: "2025-10-21T00:00:00Z"
  updated_at: "2025-10-21T12:00:00Z"

# ==============================================================================
# CONFIGURATION
# ==============================================================================
config:
  # Auto-split settings
  auto_split:
    enabled: true
    max_tasks: 30
    max_depth: 3
    max_file_size_kb: 10
    strategy: "milestone"  # milestone | size | complexity

  # Verification behavior
  verification:
    verify_on_task_complete: true
    verify_on_project_complete: true
    cache_results: true
    cache_ttl_seconds: 3600
    fail_fast: false

  # Agent execution
  agent:
    parallel_execution: true
    max_concurrent_tasks: 3
    retry_failed_tasks: true
    max_retries: 3
    retry_delay_seconds: 5

# ==============================================================================
# GOAL
# ==============================================================================
goal:
  description: |
    Build a complete authentication system with:
    - User registration and login
    - JWT token management
    - OAuth2 social login
    - Password reset flow
    - Email verification

  success_criteria:
    - "All tasks marked complete"
    - "No critical_tasks remaining"
    - "All tests passing (>80% coverage)"
    - "Security audit passed"
    - "Performance benchmarks met"

  is_accomplished: false

# ==============================================================================
# MILESTONES
# ==============================================================================
milestones:
  - id: "m1"
    name: "Database Foundation"
    description: "Set up database schema, models, and migrations"
    status: "in_progress"  # pending | in_progress | completed | blocked
    completion: 0.4
    tasks: ["t1", "t2"]

  - id: "m2"
    name: "Core Authentication"
    description: "Implement JWT-based auth endpoints"
    status: "pending"
    completion: 0.0
    depends_on: ["m1"]
    tasks: ["t3", "t4"]

  - id: "m3"
    name: "OAuth2 Integration"
    description: "Add social login support"
    status: "pending"
    completion: 0.0
    depends_on: ["m2"]
    tasks: ["t5"]

  - id: "m4"
    name: "Security Hardening"
    description: "Security audit and hardening"
    status: "pending"
    completion: 0.0
    depends_on: ["m2", "m3"]
    tasks: ["t6"]

# ==============================================================================
# TASKS
# ==============================================================================
tasks:
  # ----------------------------------------------------------------------------
  # TASK 1: Database Schema
  # ----------------------------------------------------------------------------
  - id: "t1"
    title: "Create user database schema"
    description: |
      Design and implement database schema for users table with:
      - Primary key (UUID)
      - Email (unique, indexed)
      - Password hash
      - Timestamps (created_at, updated_at)
      - Soft delete support

    # Status & Progress
    status: "in_progress"
    completion: 0.6

    # Organization
    milestone: "m1"
    priority: "high"
    tags: ["database", "schema", "migration", "postgres"]

    # Relationships (task IDs)
    depends_on: []
    blocks: ["t2", "t3"]
    related_to: []

    # Time tracking
    estimated_time_hours: 2.0
    actual_time_hours: 1.2
    started_at: "2025-10-21T09:00:00Z"
    completed_at: null
    deadline: "2025-10-21T18:00:00Z"

    # Assignment
    assignee: "agent_claude"
    session_id: "sess_20251021_090000"

    # Nested subtasks (inline)
    subtasks:
      - id: "t1.1"
        title: "Design schema fields"
        description: "Define all table columns, types, constraints"
        status: "completed"
        completion: 1.0
        completed_at: "2025-10-21T09:30:00Z"

        verification:
          type: "manual"
          description: "Schema design reviewed and approved"
          passed: true
          verified_at: "2025-10-21T09:30:00Z"
          verified_by: "human"

      - id: "t1.2"
        title: "Write Alembic migration"
        description: "Create migration script with upgrade/downgrade"
        status: "in_progress"
        completion: 0.7
        depends_on: ["t1.1"]

        verification:
          type: "composite"
          operator: "AND"
          checks:
            - type: "command"
              name: "migration_syntax"
              command: "python -m py_compile alembic/versions/001_users.py"
              expected_exit_code: 0
              timeout_seconds: 10

            - type: "command"
              name: "upgrade"
              command: "alembic upgrade head"
              expected_exit_code: 0
              timeout_seconds: 30

          passed: null
          verified_at: null

      - id: "t1.3"
        title: "Test migration rollback"
        description: "Verify upgrade → downgrade → upgrade cycle works"
        status: "pending"
        completion: 0.0
        depends_on: ["t1.2"]

        verification:
          type: "composite"
          operator: "AND"
          checks:
            - type: "command"
              name: "initial_upgrade"
              command: "alembic upgrade head"
              expected_exit_code: 0

            - type: "command"
              name: "downgrade"
              command: "alembic downgrade -1"
              expected_exit_code: 0

            - type: "command"
              name: "re_upgrade"
              command: "alembic upgrade head"
              expected_exit_code: 0

            - type: "command"
              name: "test_data_integrity"
              command: "pytest tests/migrations/test_001_users.py"
              expected_exit_code: 0

      - id: "t1.4"
        title: "Add database indexes"
        description: "Create indexes on email, created_at for performance"
        status: "pending"
        completion: 0.0
        depends_on: ["t1.3"]

        verification:
          type: "composite"
          operator: "AND"
          checks:
            - type: "command"
              name: "check_indexes"
              command: |
                psql $DATABASE_URL -c "SELECT indexname FROM pg_indexes WHERE tablename='users';"
              expected_exit_code: 0
              expected_output_contains: ["idx_users_email", "idx_users_created_at"]

            - type: "command"
              name: "performance_test"
              command: "pytest tests/performance/test_user_queries.py"
              expected_exit_code: 0

    # Task-level verification (must pass after all subtasks)
    verification:
      type: "composite"
      operator: "AND"
      checks:
        - type: "subtasks_complete"
          description: "All subtasks completed successfully"
          weight: 0.4

        - type: "command"
          name: "table_exists"
          description: "Verify users table exists"
          command: "psql $DATABASE_URL -c '\\dt users'"
          expected_exit_code: 0
          weight: 0.2

        - type: "command"
          name: "test_suite"
          description: "All migration tests pass"
          command: "pytest tests/migrations/ -v"
          expected_exit_code: 0
          weight: 0.3

        - type: "prompt"
          name: "code_review"
          description: "LLM code quality review"
          prompt: |
            Review the database migration and verify:
            1. Uses UUID for primary key (security best practice)
            2. Email field has unique constraint and index
            3. Password stored as hash, not plaintext
            4. Includes created_at and updated_at timestamps
            5. Migration has proper downgrade logic
            6. No SQL injection vulnerabilities
          llm_check: true
          llm_model: "claude-sonnet-4.5"
          expected_keywords: ["uuid", "unique", "hash", "timestamp", "downgrade"]
          weight: 0.1

      passed: null
      verified_at: null
      verification_output: null

    # Notes & context
    notes:
      - timestamp: "2025-10-21T09:00:00Z"
        author: "agent_claude"
        content: "Starting database schema design"

      - timestamp: "2025-10-21T09:15:00Z"
        author: "human"
        content: "Use UUID not integer for primary key (security requirement)"

      - timestamp: "2025-10-21T10:00:00Z"
        author: "agent_claude"
        content: "Added indexes for email lookups (performance optimization)"

    # Artifacts produced
    artifacts:
      - type: "file"
        path: "alembic/versions/001_create_users.py"
        description: "Database migration script"

      - type: "file"
        path: "docs/schema_design.md"
        description: "Schema design documentation"

      - type: "diagram"
        path: "docs/diagrams/users_schema.png"
        description: "ER diagram"

  # ----------------------------------------------------------------------------
  # TASK 2: User Model (with external subtasks reference)
  # ----------------------------------------------------------------------------
  - id: "t2"
    title: "Implement User model and repository"
    description: |
      Create SQLAlchemy User model with:
      - ORM mapping
      - Password hashing (bcrypt)
      - Email validation
      - Relationships
      - Repository pattern for queries

    status: "pending"
    completion: 0.0
    milestone: "m1"
    priority: "high"
    depends_on: ["t1"]
    blocks: ["t3", "t4"]

    estimated_time_hours: 3.0

    # Reference external file for complex subtask tree
    subtasks_ref:
      file: "tasks/t2_user_model_subtasks.yaml"
      task_count: 12
      total_depth: 3
      description: "Detailed breakdown of model implementation"

    verification:
      type: "composite"
      operator: "AND"
      checks:
        - type: "subtasks_complete"
          weight: 0.3

        - type: "command"
          name: "unit_tests"
          command: "pytest tests/models/test_user.py -v --cov=src/models/user"
          expected_exit_code: 0
          coverage_threshold: 90
          weight: 0.3

        - type: "static_analysis"
          name: "type_check"
          command: "mypy src/models/user.py --strict"
          expected_exit_code: 0
          weight: 0.2

        - type: "prompt"
          name: "security_review"
          prompt: |
            Security review of User model:
            1. Password hashing uses bcrypt with proper work factor (≥12)
            2. Passwords never logged or exposed in __repr__
            3. Email validation prevents injection
            4. No sensitive data in API serialization
            5. Constant-time password comparison
          llm_check: true
          llm_model: "claude-sonnet-4.5"
          weight: 0.2

  # ----------------------------------------------------------------------------
  # TASK 3: Authentication API
  # ----------------------------------------------------------------------------
  - id: "t3"
    title: "Build authentication REST API endpoints"
    description: |
      Implement FastAPI endpoints:
      - POST /auth/register
      - POST /auth/login
      - POST /auth/logout
      - POST /auth/refresh
      - GET /auth/me

    status: "pending"
    completion: 0.0
    milestone: "m2"
    priority: "critical"
    depends_on: ["t2"]
    blocks: ["t5"]

    estimated_time_hours: 4.0

    subtasks:
      - id: "t3.1"
        title: "POST /auth/register"
        description: "User registration endpoint"
        status: "pending"

        verification:
          type: "composite"
          operator: "AND"
          checks:
            - type: "command"
              name: "unit_tests"
              command: "pytest tests/api/test_auth.py::test_register -v"
              expected_exit_code: 0

            - type: "http"
              name: "integration_test"
              method: "POST"
              url: "http://localhost:8000/auth/register"
              headers:
                Content-Type: "application/json"
              body:
                email: "test@example.com"
                password: "SecurePass123!"
              expected_status: 201
              expected_response_schema:
                type: "object"
                required: ["user_id", "email", "created_at"]
                properties:
                  user_id:
                    type: "string"
                    format: "uuid"

      - id: "t3.2"
        title: "POST /auth/login"
        description: "User login endpoint with JWT generation"
        status: "pending"
        depends_on: ["t3.1"]

        verification:
          type: "composite"
          operator: "AND"
          checks:
            - type: "http"
              name: "valid_login"
              method: "POST"
              url: "http://localhost:8000/auth/login"
              body:
                email: "test@example.com"
                password: "SecurePass123!"
              expected_status: 200
              expected_response_schema:
                type: "object"
                required: ["access_token", "refresh_token", "token_type"]
                properties:
                  token_type:
                    enum: ["Bearer"]

            - type: "http"
              name: "invalid_password"
              method: "POST"
              url: "http://localhost:8000/auth/login"
              body:
                email: "test@example.com"
                password: "WrongPassword"
              expected_status: 401

            - type: "command"
              name: "security_tests"
              command: "pytest tests/security/test_auth_endpoints.py -v"
              expected_exit_code: 0

      - id: "t3.3"
        title: "POST /auth/refresh"
        description: "Refresh access token using refresh token"
        status: "pending"
        depends_on: ["t3.2"]

        verification:
          type: "http"
          method: "POST"
          url: "http://localhost:8000/auth/refresh"
          headers:
            Authorization: "Bearer {refresh_token}"
          expected_status: 200
          expected_response_schema:
            type: "object"
            required: ["access_token"]

      - id: "t3.4"
        title: "GET /auth/me"
        description: "Get current user profile (authenticated)"
        status: "pending"
        depends_on: ["t3.2"]

        verification:
          type: "http"
          method: "GET"
          url: "http://localhost:8000/auth/me"
          headers:
            Authorization: "Bearer {access_token}"
          expected_status: 200
          expected_response_schema:
            type: "object"
            required: ["user_id", "email"]

      - id: "t3.5"
        title: "POST /auth/logout"
        description: "Logout and invalidate tokens"
        status: "pending"
        depends_on: ["t3.2"]

        verification:
          type: "composite"
          operator: "AND"
          checks:
            - type: "http"
              name: "logout_succeeds"
              method: "POST"
              url: "http://localhost:8000/auth/logout"
              headers:
                Authorization: "Bearer {access_token}"
              expected_status: 204

            - type: "http"
              name: "token_invalidated"
              method: "GET"
              url: "http://localhost:8000/auth/me"
              headers:
                Authorization: "Bearer {access_token}"
              expected_status: 401
              description: "Token should be invalid after logout"

    verification:
      type: "composite"
      operator: "AND"
      checks:
        - type: "subtasks_complete"

        - type: "command"
          name: "integration_tests"
          command: "pytest tests/integration/test_auth_flow.py -v"
          expected_exit_code: 0

        - type: "command"
          name: "security_scan"
          command: "bandit -r src/api/auth/ -ll"
          expected_exit_code: 0

        - type: "prompt"
          name: "owasp_review"
          prompt: |
            Review authentication endpoints against OWASP Top 10:
            1. A01 Broken Access Control - proper authorization checks
            2. A02 Cryptographic Failures - secure password storage
            3. A03 Injection - parameterized queries, input validation
            4. A07 Identification and Authentication Failures - secure session management
            5. Rate limiting implemented to prevent brute force
            6. JWT tokens have expiration and proper signing
          llm_check: true

  # Additional tasks omitted for brevity...

# ==============================================================================
# CRITICAL TASKS (discovered during execution)
# ==============================================================================
critical_tasks:
  - id: "ct1"
    title: "FIX: SQL injection in login endpoint"
    description: |
      SECURITY VULNERABILITY - HIGH SEVERITY

      The login endpoint constructs SQL queries using string formatting:
      ```python
      query = f"SELECT * FROM users WHERE email='{email}'"
      ```

      This allows SQL injection attacks. Must use parameterized queries or ORM.

      Location: src/api/auth/routes.py:45

      Example exploit:
      ```
      POST /auth/login
      {"email": "' OR '1'='1", "password": "anything"}
      ```

    # Severity classification
    priority: "critical"
    severity: "high"
    security_impact: true
    blocks_release: true

    # Discovery metadata
    discovered_at: "2025-10-21T10:30:00Z"
    discovered_by: "agent_architect"
    discovery_method: "code_review"
    discovery_context: "verify_phase_iteration_1"

    # Status
    status: "pending"
    completion: 0.0

    # Relationships
    related_task: "t3.2"
    blocks: []

    # Assignment
    assignee: "agent_claude"
    estimated_time_hours: 1.0
    deadline: "2025-10-21T14:00:00Z"

    # Resolution verification
    verification:
      type: "composite"
      operator: "AND"
      checks:
        - type: "command"
          name: "security_scan"
          description: "Bandit security linter finds no issues"
          command: "bandit -r src/api/auth/ -ll"
          expected_exit_code: 0

        - type: "prompt"
          name: "code_review"
          description: "Manual verification of fix"
          prompt: |
            Verify SQL injection vulnerability is fixed:
            1. All queries use parameterized statements or ORM
            2. No string formatting/concatenation in SQL
            3. Input validation on email field
            4. Escaping not relied upon (use parameterization)
          llm_check: true
          llm_model: "claude-sonnet-4.5"

        - type: "command"
          name: "penetration_test"
          description: "Automated SQL injection tests"
          command: "pytest tests/security/test_sql_injection.py -v"
          expected_exit_code: 0

        - type: "http"
          name: "injection_attempt"
          description: "Verify injection payload fails safely"
          method: "POST"
          url: "http://localhost:8000/auth/login"
          body:
            email: "' OR '1'='1"
            password: "anything"
          expected_status: 400  # Bad request, not 200

    # Tracking
    notes:
      - timestamp: "2025-10-21T10:30:00Z"
        author: "agent_architect"
        content: |
          Found during verify phase code review.
          This is a critical security vulnerability that must be fixed before release.
          OWASP A03:2021 - Injection

      - timestamp: "2025-10-21T11:00:00Z"
        author: "agent_claude"
        content: "Starting fix - will migrate to SQLAlchemy ORM queries"

  - id: "ct2"
    title: "FIX: Missing rate limiting on auth endpoints"
    description: |
      Authentication endpoints lack rate limiting, allowing brute force attacks.
      Need to implement rate limiting (e.g., 5 attempts per 15 minutes per IP).

    priority: "critical"
    severity: "medium"
    security_impact: true
    blocks_release: true

    discovered_at: "2025-10-21T10:35:00Z"
    discovered_by: "agent_architect"
    discovery_method: "security_audit"

    status: "pending"
    related_task: "t3"
    estimated_time_hours: 2.0

    verification:
      type: "composite"
      operator: "AND"
      checks:
        - type: "http"
          name: "rate_limit_enforced"
          description: "6th attempt within window should be blocked"
          method: "POST"
          url: "http://localhost:8000/auth/login"
          repeat: 6
          body:
            email: "test@example.com"
            password: "wrong"
          expected_status_last: 429  # Too Many Requests
          expected_headers:
            Retry-After: "900"  # 15 minutes

        - type: "command"
          name: "load_test"
          command: "locust -f tests/load/test_rate_limiting.py --headless -u 100 -r 10"
          expected_exit_code: 0

# ==============================================================================
# PROJECT-LEVEL VERIFICATION
# ==============================================================================
project_verification:
  description: "Verification checks that must pass for project completion"

  checks:
    # Structural completeness
    - type: "all_tasks_complete"
      description: "All regular tasks marked completed"
      required: true
      weight: 0.2

    - type: "no_critical_tasks"
      description: "No outstanding critical tasks"
      required: true
      weight: 0.2

    - type: "milestones_complete"
      description: "All milestones reached 100%"
      required: true
      weight: 0.1

    # Testing
    - type: "command"
      name: "full_test_suite"
      description: "Complete test suite passes"
      command: "pytest --maxfail=0 -v"
      expected_exit_code: 0
      required: true
      timeout_seconds: 300
      weight: 0.15

    - type: "coverage"
      name: "code_coverage"
      description: "Test coverage meets threshold"
      command: "pytest --cov=src --cov-report=term --cov-fail-under=80"
      expected_exit_code: 0
      min_coverage: 80
      required: true
      weight: 0.1

    # Static analysis
    - type: "command"
      name: "type_check"
      description: "Type checking passes"
      command: "mypy src/ --strict"
      expected_exit_code: 0
      required: true
      weight: 0.05

    - type: "command"
      name: "lint"
      description: "Linting passes"
      command: "ruff check src/"
      expected_exit_code: 0
      required: false  # Warning only
      weight: 0.05

    # Security
    - type: "command"
      name: "security_scan"
      description: "Security vulnerabilities scan"
      command: "bandit -r src/ -ll"
      expected_exit_code: 0
      required: true
      weight: 0.1

    - type: "command"
      name: "dependency_audit"
      description: "No known vulnerable dependencies"
      command: "pip-audit"
      expected_exit_code: 0
      required: true
      weight: 0.05

    # Final review
    - type: "prompt"
      name: "final_review"
      description: "Comprehensive final review"
      prompt: |
        Perform comprehensive final project review:

        **Functional Completeness:**
        1. All specified features implemented
        2. All acceptance criteria met
        3. No known bugs or issues

        **Code Quality:**
        4. Code follows project conventions
        5. Proper error handling
        6. Comprehensive documentation
        7. Clean, maintainable code structure

        **Security:**
        8. OWASP Top 10 mitigations in place
        9. Input validation comprehensive
        10. Authentication/authorization secure
        11. Sensitive data protected

        **Performance:**
        12. No obvious performance issues
        13. Database queries optimized
        14. Caching where appropriate

        **Production Readiness:**
        15. Logging adequate for debugging
        16. Monitoring/metrics in place
        17. Error handling user-friendly
        18. Ready for production deployment
      llm_check: true
      llm_model: "claude-sonnet-4.5"
      required: true
      weight: 0.0  # Qualitative only

  # Result tracking
  passed: false
  last_verified: null
  verification_output: null
  failed_checks: []

# ==============================================================================
# EXECUTION HISTORY
# ==============================================================================
execution_history:
  - session_id: "sess_20251021_090000"
    agent: "agent_claude"
    phase: "execute"
    task_id: "t1"
    started_at: "2025-10-21T09:00:00Z"
    ended_at: "2025-10-21T10:00:00Z"
    status: "in_progress"
    progress_snapshot:
      total_tasks: 6
      completed: 0
      in_progress: 1

  - session_id: "sess_20251021_100000"
    agent: "agent_architect"
    phase: "verify"
    task_id: null  # Whole project verification
    started_at: "2025-10-21T10:00:00Z"
    ended_at: "2025-10-21T10:45:00Z"
    status: "completed"
    feedback_given: true

# ==============================================================================
# FEEDBACK HISTORY (from verify agent)
# ==============================================================================
feedback_history:
  - iteration: 1
    timestamp: "2025-10-21T10:45:00Z"
    agent: "agent_architect"
    session_id: "sess_20251021_100000"

    feedback: |
      **EXECUTE PHASE FEEDBACK - ITERATION 1**

      ## Critical Issues Found (2)

      ### 1. SQL Injection Vulnerability (HIGH SEVERITY)
      - **Location:** src/api/auth/routes.py:45
      - **Issue:** String formatting used in SQL query construction
      - **Impact:** Allows authentication bypass and data exfiltration
      - **Action:** Created critical task ct1

      ### 2. Missing Rate Limiting (MEDIUM SEVERITY)
      - **Location:** All auth endpoints
      - **Issue:** No rate limiting, enables brute force attacks
      - **Impact:** Account takeover via password guessing
      - **Action:** Created critical task ct2

      ## Task Progress
      - t1: 60% complete, on track
      - t2: Not started (blocked by t1)
      - t3: Not started (blocked by t2)

      ## Recommendations
      1. Fix ct1 immediately (security blocker)
      2. Implement rate limiting (ct2)
      3. Continue t1 subtasks as planned
      4. Schedule security training for team

      **VERDICT:** REWORK REQUIRED

    tasks_affected: ["t3"]
    critical_tasks_created: ["ct1", "ct2"]
    requires_rework: true

  - iteration: 2
    timestamp: "2025-10-21T14:00:00Z"
    agent: "agent_architect"
    session_id: "sess_20251021_130000"

    feedback: |
      **EXECUTE PHASE FEEDBACK - ITERATION 2**

      ## Critical Issues Resolution
      - ct1: RESOLVED ✓ (migrated to SQLAlchemy ORM)
      - ct2: RESOLVED ✓ (implemented Redis-based rate limiting)

      ## Task Progress
      - t1: 100% complete ✓
      - t2: 40% complete, in progress
      - t3: Not started (blocked by t2)

      ## Code Quality
      - All tests passing
      - Security scan clean
      - Type checking passes

      **VERDICT:** CONTINUE EXECUTION

    tasks_affected: ["ct1", "ct2", "t1", "t2"]
    critical_tasks_created: []
    requires_rework: false

# ==============================================================================
# METRICS & ANALYSIS
# ==============================================================================
metrics:
  # Task counts
  total_tasks: 6
  completed_tasks: 1
  in_progress_tasks: 1
  pending_tasks: 4
  blocked_tasks: 0
  failed_tasks: 0
  skipped_tasks: 0

  critical_tasks_total: 2
  critical_tasks_resolved: 2
  critical_tasks_pending: 0

  total_subtasks: 23
  completed_subtasks: 3

  # Time tracking
  estimated_total_hours: 20.0
  actual_total_hours: 8.5
  time_efficiency: 0.425  # actual/estimated

  # Progress
  completion_percentage: 16.7  # weighted by task importance
  on_track: true
  projected_completion: "2025-10-22T18:00:00Z"

  # Quality metrics
  verify_iterations: 2
  critical_issues_found: 2
  critical_issues_resolved: 2
  tests_passing: true
  coverage_percentage: 85.3

  # Agent performance
  agent_sessions: 4
  average_session_duration_hours: 2.1
  tasks_per_session: 1.5

# ==============================================================================
# GRAPH ANALYSIS (computed by static analyzer)
# ==============================================================================
graph_analysis:
  # DAG validation
  is_dag: true
  has_cycles: false
  cycle_paths: []

  # Critical path (longest dependency chain)
  critical_path:
    task_ids: ["t1", "t2", "t3", "t5"]
    estimated_duration_hours: 12.0
    actual_duration_hours: 5.0  # in progress
    completion: 0.083

  # Parallel execution opportunities
  parallel_groups:
    - level: 0
      task_ids: ["t1"]
      can_run_parallel: false
      estimated_duration_hours: 2.0

    - level: 1
      task_ids: ["t2"]
      can_run_parallel: false
      estimated_duration_hours: 3.0

    - level: 2
      task_ids: ["t3", "t4"]
      can_run_parallel: true
      estimated_duration_hours: 4.0  # max of parallel tasks

    - level: 3
      task_ids: ["t5", "t6"]
      can_run_parallel: true
      estimated_duration_hours: 3.0

  # Topological sort (valid execution orders)
  topological_order: ["t1", "t2", "t3", "t4", "t5", "t6"]

  # Dependency statistics
  max_depth: 4
  max_dependencies_per_task: 2
  isolated_tasks: 0
  leaf_tasks: ["t5", "t6"]
  root_tasks: ["t1"]

  # Complexity metrics
  total_edges: 8
  branching_factor: 1.33
  complexity_score: "medium"

# ==============================================================================
# AUTO-SPLIT METADATA
# ==============================================================================
splits:
  enabled: true
  strategy: "milestone"

  split_files:
    - file: "tasks/milestone_m1_database.yaml"
      milestone: "m1"
      task_ids: ["t1", "t2"]
      subtask_count: 23
      status: "active"
      created_at: "2025-10-21T09:00:00Z"

    - file: "tasks/milestone_m2_auth_api.yaml"
      milestone: "m2"
      task_ids: ["t3", "t4"]
      subtask_count: 18
      status: "pending"

    - file: "tasks/milestone_m3_oauth.yaml"
      milestone: "m3"
      task_ids: ["t5"]
      subtask_count: 8
      status: "pending"

    - file: "tasks/milestone_m4_security.yaml"
      milestone: "m4"
      task_ids: ["t6"]
      subtask_count: 12
      status: "pending"

  # Split trigger history
  split_history:
    - timestamp: "2025-10-21T09:00:00Z"
      reason: "Initial project split by milestone"
      files_created: 4
```

## Advanced Features

### 1. External Subtask References

For complex tasks with many subtasks, use external files:

**Main file (`plan.yaml`):**
```yaml
tasks:
  - id: "t2"
    title: "Implement User model"
    subtasks_ref:
      file: "tasks/t2_user_model_subtasks.yaml"
      task_count: 12
```

**Referenced file (`tasks/t2_user_model_subtasks.yaml`):**
```yaml
# This file contains subtasks for t2
# Parent task: t2 - Implement User model

subtasks:
  - id: "t2.1"
    title: "Create SQLAlchemy model class"
    # ... full task definition

  - id: "t2.2"
    title: "Add password hashing"
    depends_on: ["t2.1"]
    # ...
```

### 2. Verification Type Reference

#### Command Verification
```yaml
verification:
  type: "command"
  name: "run_tests"
  command: "pytest tests/test_auth.py -v"
  expected_exit_code: 0
  timeout_seconds: 60
  retry_on_failure: true
  max_retries: 3
```

#### HTTP Verification
```yaml
verification:
  type: "http"
  name: "api_endpoint_works"
  method: "POST"
  url: "http://localhost:8000/api/users"
  headers:
    Content-Type: "application/json"
    Authorization: "Bearer {token}"
  body:
    email: "test@example.com"
  expected_status: 201
  expected_response_schema:
    type: "object"
    required: ["id", "email"]
  expected_headers:
    Content-Type: "application/json"
  timeout_seconds: 10
```

#### Prompt (LLM) Verification
```yaml
verification:
  type: "prompt"
  name: "code_quality_review"
  prompt: |
    Review this code and verify:
    1. Follows PEP 8 style guide
    2. Has proper error handling
    3. Includes type hints
    4. Documentation is clear
  llm_check: true
  llm_model: "claude-sonnet-4.5"
  llm_temperature: 0.0
  expected_keywords: ["PEP 8", "type hints", "documented"]
  min_confidence: 0.8
```

#### Composite Verification
```yaml
verification:
  type: "composite"
  operator: "AND"  # or "OR"
  checks:
    - type: "command"
      name: "tests"
      command: "pytest"
      expected_exit_code: 0
      weight: 0.5

    - type: "command"
      name: "lint"
      command: "ruff check src/"
      expected_exit_code: 0
      weight: 0.3

    - type: "prompt"
      name: "review"
      prompt: "Code quality acceptable?"
      llm_check: true
      weight: 0.2

  # For AND: all must pass
  # For OR: at least one must pass
  # Weighted scoring for partial credit
```

#### Coverage Verification
```yaml
verification:
  type: "coverage"
  name: "test_coverage"
  command: "pytest --cov=src --cov-report=term-missing"
  expected_exit_code: 0
  min_coverage: 80
  coverage_format: "cobertura"  # or "lcov", "json"
  exclude_patterns:
    - "*/tests/*"
    - "*/migrations/*"
```

#### Static Analysis Verification
```yaml
verification:
  type: "static_analysis"
  name: "code_quality"
  tools:
    - name: "mypy"
      command: "mypy src/ --strict"
      expected_exit_code: 0
      weight: 0.4

    - name: "ruff"
      command: "ruff check src/"
      expected_exit_code: 0
      weight: 0.3

    - name: "bandit"
      command: "bandit -r src/ -ll"
      expected_exit_code: 0
      weight: 0.3
```

### 3. Task Status Lifecycle

```
┌──────────┐
│ pending  │
└────┬─────┘
     │ agent starts work
     ▼
┌──────────────┐
│ in_progress  │
└──┬─────┬──┬──┘
   │     │  │ agent finishes
   │     │  ▼
   │     │ ┌───────────┐
   │     │ │ completed │
   │     │ └───────────┘
   │     │
   │     │ agent encounters blocker
   │     ▼
   │    ┌─────────┐
   │    │ blocked │
   │    └────┬────┘
   │         │ blocker resolved
   │         ▼
   │     (back to pending)
   │
   │ verification fails
   ▼
┌─────────┐
│ failed  │
└────┬────┘
     │ retry
     ▼
(back to pending)
```

### 4. Dependency Resolution Algorithm

```python
def get_executable_tasks(plan: TaskPlan) -> list[Task]:
    """
    Get all tasks that can be executed now.
    A task is executable if:
    1. Status is 'pending'
    2. All dependencies are 'completed'
    3. Not blocked by any 'failed' or 'blocked' tasks
    """
    executable = []

    for task in plan.tasks:
        if task.status != "pending":
            continue

        # Check all dependencies completed
        deps_complete = all(
            plan.get_task(dep_id).status == "completed"
            for dep_id in task.depends_on
        )

        if deps_complete:
            executable.append(task)

    return executable
```

### 5. Auto-Split Strategies

#### Strategy 1: By Milestone
```yaml
config:
  auto_split:
    strategy: "milestone"
    # Creates one file per milestone
    # Result: tasks/milestone_{milestone_id}.yaml
```

#### Strategy 2: By Size
```yaml
config:
  auto_split:
    strategy: "size"
    max_tasks: 30
    # Distributes tasks evenly across files
    # Respects dependency boundaries
```

#### Strategy 3: By Complexity
```yaml
config:
  auto_split:
    strategy: "complexity"
    max_depth: 3
    # Groups tasks by dependency depth
    # Creates layers: level_0.yaml, level_1.yaml, etc.
```

## Integration with Sisyphus

### Updated TaskValidator

```python
class YAMLTaskValidator:
    """
    Replaces existing TaskValidator.
    Reads YAML task plans instead of markdown checklists.
    """

    def __init__(self, plan_path: Path):
        self.plan_path = plan_path
        self.plan = self._load_plan()
        self.analyzer = GraphAnalyzer(self.plan)
        self.verifier = VerificationEngine()

    def _load_plan(self) -> TaskPlan:
        """Load and validate YAML plan"""
        with open(self.plan_path) as f:
            data = yaml.safe_load(f)

        plan = TaskPlan.from_dict(data)

        # Validate DAG structure
        errors = plan.validate()
        if errors:
            raise PlanValidationError(errors)

        return plan

    async def is_complete(self) -> bool:
        """Check if all tasks are complete"""
        # Check regular tasks
        if not all(t.status == "completed" for t in self.plan.tasks):
            return False

        # Check critical tasks
        if any(ct.status != "completed" for ct in self.plan.critical_tasks):
            return False

        # Check project-level verification
        if self.plan.config.verification.verify_on_project_complete:
            result = await self.verifier.verify_project(self.plan)
            if not result.passed:
                return False

        # Check goal accomplished
        return self.plan.goal.is_accomplished

    async def get_next_tasks(self) -> list[Task]:
        """Get tasks ready to execute"""
        executable = []

        for task in self.plan.tasks:
            if task.status != "pending":
                continue

            # Check dependencies
            if task.can_start(self.plan):
                executable.append(task)

        # Sort by priority
        executable.sort(key=lambda t: PRIORITY_ORDER[t.priority], reverse=True)

        return executable

    async def mark_complete(self, task_id: str) -> None:
        """Mark task as complete"""
        task = self.plan.get_task(task_id)
        task.status = "completed"
        task.completion = 1.0
        task.completed_at = datetime.now(timezone.utc).isoformat()

        # Run task verification
        if self.plan.config.verification.verify_on_task_complete:
            result = await self.verifier.verify_task(task)
            task.verification.passed = result.passed
            task.verification.verified_at = datetime.now(timezone.utc).isoformat()
            task.verification.verification_output = result.output

            if not result.passed:
                task.status = "failed"
                raise TaskVerificationError(f"Task {task_id} failed verification")

        # Save plan
        await self._save_plan()

    async def add_critical_task(self, critical_task: CriticalTask) -> None:
        """Add critical task discovered during execution"""
        self.plan.critical_tasks.append(critical_task)
        self.plan.metrics.critical_tasks_total += 1
        self.plan.metrics.critical_tasks_pending += 1
        await self._save_plan()

    async def should_continue_loop(self) -> bool:
        """Check if execution loop should continue"""
        # Continue if:
        # 1. There are pending tasks
        # 2. There are pending critical tasks
        # 3. Project verification hasn't passed

        has_pending = any(t.status == "pending" for t in self.plan.tasks)
        has_critical = any(ct.status != "completed" for ct in self.plan.critical_tasks)

        return has_pending or has_critical or not await self.is_complete()

    async def _save_plan(self) -> None:
        """Save plan to YAML"""
        self.plan.updated_at = datetime.now(timezone.utc).isoformat()
        self.plan.to_yaml(self.plan_path)
```

### Updated ExecutionLoop

```python
class ExecutionLoop:
    """
    Modified to work with YAML task plans.
    """

    def __init__(
        self,
        execute_agent: Agent,
        verify_agent: Agent,
        ui: UIProtocol,
        plan_path: Path,
    ):
        self.execute_agent = execute_agent
        self.verify_agent = verify_agent
        self.ui = ui
        self.validator = YAMLTaskValidator(plan_path)
        self.iteration = 0

    async def run(self) -> None:
        """Main execution loop"""
        while await self.validator.should_continue_loop():
            self.iteration += 1

            # Execute phase
            await self._execute_phase()

            # Verify phase
            feedback = await self._verify_phase()

            # Handle critical tasks
            for critical_task in feedback.critical_tasks_created:
                await self.validator.add_critical_task(critical_task)

            # Check if rework required
            if not feedback.requires_rework:
                break

        # Final verification
        if await self.validator.is_complete():
            self.ui.show_message("✓ Project completed successfully!", "success")
        else:
            self.ui.show_message("✗ Project incomplete", "error")

    async def _execute_phase(self) -> None:
        """Execute phase - work on tasks"""
        # Get next tasks
        tasks = await self.validator.get_next_tasks()

        if not tasks:
            return

        # Parallel execution if enabled
        if self.validator.plan.config.agent.parallel_execution:
            await self._execute_parallel(tasks)
        else:
            await self._execute_sequential(tasks)

    async def _verify_phase(self) -> VerifyFeedback:
        """Verify phase - check work quality"""
        # Build verify prompt with current state
        verify_prompt = self._build_verify_prompt()

        # Run verify agent (always new session)
        feedback = await self._run_verify_agent(verify_prompt)

        # Record feedback
        self.validator.plan.feedback_history.append(feedback)
        await self.validator._save_plan()

        return feedback
```

## Static Analysis Tools

### Graph Validator
```python
class GraphValidator:
    """Validate task dependency graph"""

    def validate(self, plan: TaskPlan) -> list[ValidationError]:
        errors = []

        # Build graph
        G = self._build_graph(plan)

        # Check for cycles
        try:
            cycles = list(nx.simple_cycles(G))
            if cycles:
                errors.append(ValidationError(
                    type="circular_dependency",
                    message=f"Circular dependencies found: {cycles}"
                ))
        except nx.NetworkXNoCycle:
            pass

        # Check for broken references
        for task in plan.tasks:
            for dep_id in task.depends_on:
                if not plan.has_task(dep_id):
                    errors.append(ValidationError(
                        type="broken_reference",
                        message=f"Task {task.id} depends on non-existent task {dep_id}"
                    ))

        # Check for orphaned tasks
        all_referenced = set()
        for task in plan.tasks:
            all_referenced.update(task.depends_on)
            all_referenced.update(task.blocks)

        all_ids = {t.id for t in plan.tasks}
        orphaned = all_referenced - all_ids
        if orphaned:
            errors.append(ValidationError(
                type="orphaned_reference",
                message=f"Referenced but undefined tasks: {orphaned}"
            ))

        return errors
```

### Complexity Analyzer
```python
class ComplexityAnalyzer:
    """Analyze task plan complexity"""

    def analyze(self, plan: TaskPlan) -> ComplexityReport:
        G = self._build_graph(plan)

        return ComplexityReport(
            total_tasks=len(plan.tasks),
            max_depth=self._calculate_depth(G),
            branching_factor=self._calculate_branching(G),
            critical_path_length=len(self._critical_path(G)),
            parallelization_opportunity=self._parallel_score(G),
            complexity_score=self._overall_complexity(G),
            estimated_duration=self._estimate_duration(plan),
        )

    def _calculate_depth(self, G: nx.DiGraph) -> int:
        """Maximum dependency chain length"""
        return nx.dag_longest_path_length(G)

    def _parallel_score(self, G: nx.DiGraph) -> float:
        """Ratio of tasks that can run in parallel"""
        levels = list(nx.topological_generations(G))
        parallel_tasks = sum(len(level) - 1 for level in levels if len(level) > 1)
        return parallel_tasks / G.number_of_nodes()
```

## CLI Commands

```bash
# Validate task plan
sisyphus validate-plan tasks/plan.yaml

# Analyze plan complexity
sisyphus analyze-plan tasks/plan.yaml

# Visualize dependency graph
sisyphus visualize-plan tasks/plan.yaml --output graph.png

# Split large plan
sisyphus split-plan tasks/plan.yaml --strategy milestone

# Merge split plans
sisyphus merge-plans tasks/milestone_*.yaml --output tasks/merged.yaml

# Run with YAML plan
sisyphus run --plan tasks/plan.yaml

# Convert markdown to YAML
sisyphus convert ai-todolist.md --output tasks/plan.yaml
```

## Migration Path

### Phase 1: Parallel Support
- Add YAML support alongside existing markdown
- TaskValidator becomes abstract base class
- Implement YAMLTaskValidator and MarkdownTaskValidator
- User chooses format via CLI flag

### Phase 2: Deprecation
- Markdown format marked deprecated
- Migration tool provided
- Documentation updated

### Phase 3: YAML Only
- Remove markdown support
- YAML becomes standard format

## Summary

This YAML-based task planning system provides:

1. ✅ **Graph structure** with pointer-based references
2. ✅ **Nested subtasks** with external file support
3. ✅ **Programmatic verification** with multiple types
4. ✅ **Critical task system** for runtime discoveries
5. ✅ **Auto-splitting** by size/complexity/milestone
6. ✅ **Static analysis** for validation and optimization
7. ✅ **Rich metadata** for tracking and analytics
8. ✅ **Flexible integration** with existing Sisyphus

The design is:
- **Scalable**: Handles projects of any size via auto-split
- **Analyzable**: Static analysis tools for optimization
- **Extensible**: Easy to add new verification types
- **Type-safe**: Schema validation enforces correctness
- **Human-readable**: YAML format is clear and editable
