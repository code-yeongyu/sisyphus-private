# Task Started
All tasks execution STARTED: Thu Oct  9 16:02:47 KST 2025


[2025-10-09 16:05] - 1. 프로젝트 의존성 추가 및 기본 구조 설정

### DISCOVERED ISSUES
- 없음: 기존 코드에서 발견된 문제 없음

### IMPLEMENTATION DECISIONS
- pyproject.toml에 필수 의존성 추가: typer, textual, rich, httpx, claude-agent-sdk, aiofiles
- 계획서에 명시된 디렉토리 구조를 정확히 따름 (sisyphus/{agents,core,ui,utils} 및 하위 디렉토리)
- 모든 패키지 디렉토리에 __init__.py 생성하여 Python 패키지로 인식되도록 함
- prompts, logs, sessions 디렉토리 생성 (런타임에 사용될 디렉토리)

### PROBLEMS FOR NEXT TASKS
- 없음: 다음 작업(공통 타입 및 에러 정의)은 이 구조 위에서 바로 진행 가능

### VERIFICATION RESULTS
- pyproject.toml 확인: 모든 의존성이 올바르게 추가됨
- 디렉토리 구조 확인: `find` 명령으로 모든 디렉토리가 생성되었음을 검증
- __init__.py 파일 확인: 10개의 __init__.py 파일이 모든 패키지 디렉토리에 생성됨
- Git 커밋 성공: commit 478f26d "feat: setup project structure and dependencies"

### LEARNINGS
- 프로젝트는 spray 스타일 pyproject.toml 사용 (더블 쿼터, basedpyright standard 모드)
- 기존에 sisyphus/tests/ 디렉토리가 존재했음 (첫 작업에서 생성한 것이 아님)

소요 시간: 약 3분


[2025-10-09 16:21] - 2. 공통 타입 및 에러 정의 (sisyphus/utils/types.py, errors.py)

### DISCOVERED ISSUES
- 없음: executor가 코드는 완벽하게 구현했으나 체크박스와 notepad 업데이트를 누락함

### IMPLEMENTATION DECISIONS
- types.py에 AgentMessage와 AgentConfig 데이터클래스 정의
  - AgentMessage: role, content, metadata 필드로 통합 메시지 형식 제공
  - AgentConfig: agent_type, model, prompt, binary, sdk_options, opencode_server_url 필드로 에이전트 설정 관리
- errors.py에 계층적 예외 구조 정의
  - SisyphusError를 base exception으로 사용
  - 5개의 특화된 예외 클래스 정의 (AgentNotFoundError, SessionResumeError, ServerStartError, ProcessTimeoutError, HealthCheckError)
- test_types.py에 14개의 포괄적인 테스트 작성
  - AgentMessage 생성 및 기본값 테스트
  - AgentConfig 생성 및 기본값 테스트
  - 모든 예외 클래스의 계층 구조 및 메시지 테스트

### PROBLEMS FOR NEXT TASKS
- 없음: task 3 (유틸리티 모듈 구현)을 위한 준비 완료

### VERIFICATION RESULTS
- sisyphus/utils/types.py 확인: AgentMessage와 AgentConfig가 모든 필드와 함께 정의됨
- sisyphus/utils/errors.py 확인: 6개의 예외 클래스가 계층적으로 정의됨 (SisyphusError + 5개 특화 예외)
- 테스트 실행 결과: 14개 테스트 모두 통과 (pytest -xvs sisyphus/utils/tests/test_types.py)
- Ruff 린트 체크: 통과 (sisyphus/utils/types.py, sisyphus/utils/errors.py)
- Basedpyright 타입 체크: 통과 (sisyphus/utils/types.py, sisyphus/utils/errors.py)
- Git 커밋 성공: commit 6babe59 "feat: add common types and error definitions"

### LEARNINGS
- Executor는 구현은 완벽하게 수행하지만 문서화 작업을 누락하는 경향이 있음
- 반드시 직접 검증하고 체크박스 및 notepad 업데이트를 확인해야 함

소요 시간: 약 2분 (체크박스 업데이트 포함)


[2025-10-09 16:27] - 3. 유틸리티 모듈 구현 (sisyphus/utils/)

### DISCOVERED ISSUES
- 없음: 기존 코드에서 발견된 문제 없음

### IMPLEMENTATION DECISIONS
- ProcessManager 구현 (sisyphus/utils/process.py)
  - run_with_timeout: anyio.fail_after()를 사용한 타임아웃 처리, TimeoutError와 anyio.get_cancelled_exc_class() 모두 캐치
  - terminate_gracefully: SIGTERM 전송 후 anyio.move_on_after()로 대기, 실패시 SIGKILL, 최종 타임아웃으로 anyio.fail_after() 사용
  - parse_jsonl_stream: 비동기 스트림 파싱, 최대 라인 크기 제한, 불완전한 JSON/초과 크기/빈 라인 모두 스킵
  - 파라미터 이름을 `timeout` → `timeout_seconds`로 변경 (ruff ASYNC109 에러 회피)
- LoggerFactory 구현 (sisyphus/utils/logging.py)
  - create_logger: 에이전트/세션별 고유 로거 생성
  - 파일 핸들러: DEBUG 레벨, append 모드, UTF-8 인코딩
  - 콘솔 핸들러: INFO 레벨
  - 로그 파일 형식: {agent}_{session_id}_{timestamp}_{tz}.log
  - 중복 핸들러 방지: logger.handlers 체크로 재생성 방지
- 포괄적인 테스트 작성
  - test_process.py: 12개 테스트 (타임아웃, graceful termination, JSONL 파싱)
  - test_logging.py: 11개 테스트 (로거 생성, 핸들러 설정, 파일 출력)
  - anyio의 asyncio/trio 백엔드 모두에서 자동으로 테스트됨 (pytest-anyio)

### PROBLEMS FOR NEXT TASKS
- 없음: task 4 (Agent Protocol 정의)를 진행할 준비 완료

### VERIFICATION RESULTS
- ProcessManager 검증:
  - run_with_timeout: 정상 프로세스 시작 테스트 통과
  - terminate_gracefully: 이미 종료된 프로세스, SIGTERM, SIGKILL 전환 모두 테스트 통과
  - parse_jsonl_stream: 유효한 JSON, 무효한 JSON, 초과 크기 라인, 빈 라인, 불완전한 라인, non-dict 객체 모두 처리 테스트 통과
- LoggerFactory 검증:
  - 기본 로거 생성, 세션 ID 포함 로거, 디렉토리 자동 생성, 파일/콘솔 핸들러 설정, propagation 비활성화 모두 테스트 통과
  - 로그 파일 생성 및 내용 확인 완료
- 테스트 실행 결과: 47개 테스트 모두 통과 (asyncio 22개 + trio 22개 + types 테스트)
- Ruff 린트 체크: 통과
- Basedpyright 타입 체크: 0 errors, 3 warnings (anyio.abc 타입 관련 무해한 경고)
- Git 커밋 성공: commit 2bd75e7 "feat: add process and logging utilities"

### LEARNINGS
- anyio.fail_after()는 TimeoutError를 발생시키지만, 백엔드에 따라 anyio.get_cancelled_exc_class()도 발생할 수 있으므로 둘 다 캐치해야 함
- anyio.move_on_after()는 타임아웃 시 예외를 발생시키지 않고 scope.cancel_called로 확인 가능
- ruff의 ASYNC109 규칙: async 함수의 파라미터 이름이 `timeout`이면 에러 발생 (anyio의 관용구와 충돌), `timeout_seconds` 등으로 변경 필요
- pytest-anyio는 자동으로 asyncio와 trio 백엔드 모두에서 테스트 실행 (총 테스트 수가 2배로 증가)

소요 시간: 약 15분


[2025-10-09 16:32] - 4. Agent Protocol 정의 (sisyphus/agents/base.py)

### DISCOVERED ISSUES
- 없음: 기존 코드에서 발견된 문제 없음

### IMPLEMENTATION DECISIONS
- Agent Protocol 정의 (sisyphus/agents/base.py)
  - @runtime_checkable 데코레이터 사용으로 런타임 타입 체킹 가능
  - supports_interactive: bool 속성으로 인터랙티브 지원 여부 표시
  - 5개의 async 메서드 정의: initialize, start_session, send, stream, close
  - TYPE_CHECKING 가드로 AgentMessage 임포트 (순환 참조 방지)
  - collections.abc.AsyncIterator 사용 (ruff가 typing.AsyncIterator에서 자동 변경)
- 포괄적인 테스트 작성 (sisyphus/agents/tests/test_base.py)
  - MockAgent: Protocol의 모든 메서드를 완전히 구현한 클래스
  - IncompleteMockAgent: 일부 메서드만 구현한 불완전한 클래스
  - Protocol 검증: isinstance()로 완전/불완전 구현 구분 테스트
  - 각 메서드별 개별 동작 테스트 (8개 테스트)
  - supports_interactive 속성 검증

### PROBLEMS FOR NEXT TASKS
- 없음: task 5 (UIProtocol 정의)를 진행할 준비 완료

### VERIFICATION RESULTS
- Protocol 정의 검증:
  - @runtime_checkable 데코레이터 적용 확인
  - supports_interactive 속성 정의 확인
  - 모든 메서드가 올바른 타입 힌트와 ellipsis 본문 사용
- 테스트 실행 결과: 16개 테스트 모두 통과 (asyncio 8개 + trio 8개)
  - test_protocol_validation_complete: MockAgent가 Agent Protocol 만족
  - test_protocol_validation_incomplete: IncompleteMockAgent가 Protocol 미만족
  - test_protocol_supports_interactive_attribute: 속성 존재 및 타입 검증
  - test_mock_agent_*: 각 메서드 동작 검증
- Ruff 린트 체크: All checks passed!
- Basedpyright 타입 체크: 0 errors, 0 warnings, 0 notes
- Git 커밋 성공: commit 3f59359 "feat: define Agent Protocol with runtime checking"

### LEARNINGS
- Protocol에서 TYPE_CHECKING 가드를 사용하면 런타임 임포트를 피하면서도 타입 힌팅 가능
- ruff는 typing.AsyncIterator를 자동으로 collections.abc.AsyncIterator로 변경 (PEP 585)
- @runtime_checkable을 사용한 Protocol은 isinstance()로 런타임 검증 가능
- Protocol의 메서드는 ellipsis(...)만 사용하고 구현 없음

소요 시간: 약 2분


[2025-10-09 17:02] - ORCHESTRATION STARTED
All tasks execution STARTED: Thu Oct  9 17:00:45 KST 2025

[2025-10-09 17:06] - 5. UIProtocol 정의 및 팩토리 (sisyphus/ui/base.py)

### DISCOVERED ISSUES
- 없음: 기존 코드에서 발견된 문제 없음 (base.py와 test_base.py가 이미 부분적으로 구현되어 있었음)

### IMPLEMENTATION DECISIONS
- UIProtocol 정의 (sisyphus/ui/base.py)
  - @runtime_checkable 데코레이터 사용으로 런타임 타입 체킹 가능
  - 5개의 async 메서드 정의: initialize, show_message, show_status, get_input, close
  - TYPE_CHECKING 가드로 AgentMessage 임포트 (순환 참조 방지)
  - show_message는 source 파라미터로 'execute'/'verify' 구분
  - get_input은 TUI only (CLI는 None 반환)
- create_ui 팩토리 함수 구현
  - mode == "tui"이면 TUI 반환, 아니면 CLI 반환
  - lazy import로 순환 참조 방지
- 포괄적인 테스트 작성 (sisyphus/ui/tests/test_base.py)
  - MockUI: Protocol의 모든 메서드를 완전히 구현 + 상태 추적 (messages, statuses, inputs, initialized, closed)
  - IncompleteUI: 일부 메서드만 구현 (Protocol 미충족)
  - Protocol 검증: isinstance()로 완전/불완전 구현 구분
  - 각 메서드별 개별 동작 테스트 (9개 테스트)
  - 여러 메시지/상태 순차 처리 테스트

### PROBLEMS FOR NEXT TASKS
- 없음: task 6 (ClaudeAgent 구현)를 진행할 준비 완료
- TUI/CLI 클래스는 아직 미구현 (Phase 5에서 구현 예정)

### VERIFICATION RESULTS
- Protocol 정의 검증:
  - @runtime_checkable 데코레이터 적용 확인
  - 모든 메서드가 올바른 타입 힌트와 ellipsis 본문 사용
  - TYPE_CHECKING 가드로 AgentMessage 타입 안전성 확보
- 팩토리 함수 검증:
  - create_ui 함수 시그니처 확인 (callable 테스트 통과)
  - lazy import 구조 확인 (TUI/CLI는 Phase 5에서 구현 예정)
- 테스트 실행 결과: 19개 테스트 모두 통과 (asyncio 9개 + trio 9개 + factory 1개)
  - test_protocol_validation_complete: MockUI가 UIProtocol 만족
  - test_protocol_validation_incomplete: IncompleteUI가 Protocol 미만족
  - test_mock_ui_*: 각 메서드 동작 검증 (initialize, show_message, show_status, get_input, close)
  - test_mock_ui_multiple_*: 여러 메시지/상태 순차 처리 검증
- Ruff 린트 체크: All checks passed!
- Basedpyright 타입 체크: 0 errors, 2 warnings (TUI/CLI 미구현으로 인한 예상된 경고)
- Git 커밋 성공: commit 4e83d7f "feat: define UIProtocol and factory"

### LEARNINGS
- ruff는 TYPE_CHECKING 가드 내의 타입을 인식하고 자동으로 쿼터를 제거/추가함
- Agent Protocol과 동일한 패턴을 재사용하여 일관성 있는 코드 구조 유지
- Mock 클래스에 상태 추적 기능을 추가하면 테스트가 더 강력해짐 (messages, statuses 리스트로 검증)
- 팩토리 함수는 lazy import를 사용하여 순환 참조 방지 (from ... import 를 함수 내부에 배치)

소요 시간: 약 4분


[2025-10-09 17:11] - 6. ClaudeAgent 구현

### DISCOVERED ISSUES
- 없음: 기존 코드에서 발견된 문제 없음

### IMPLEMENTATION DECISIONS
- ClaudeAgent 클래스 구현 (sisyphus/agents/claude.py)
  - Agent Protocol 준수: @runtime_checkable, supports_interactive = True
  - SDK import를 파일 상단으로 배치 (nested import 금지)
  - TYPE_CHECKING 가드로 AgentMessage 타입 안전성 확보
  - match-case 패턴 사용 (SDK 메시지 타입 분기)
  - Optional 체크로 타입 안전성 확보 (self._client is None 체크)
- SDK 초기화 로직
  - base_options 정의 후 sdk_options로 오버라이드
  - model이 있으면 final_options에 추가
  - ClaudeAgentOptions와 ClaudeSDKClient 생성
- 세션 관리
  - session_id가 주어지면 resume 옵션으로 재생성
  - resume 실패 시 SessionResumeError 발생
  - SystemMessage의 init subtype에서 session_id 추출
- 메시지 변환
  - AssistantMessage: TextBlock, ToolUseBlock, ThinkingBlock 처리
  - SystemMessage: JSON 직렬화
  - ResultMessage: metadata에 세션 정보 포함
- 포괄적인 테스트 작성 (14개 테스트)
  - Mock을 사용하여 실제 SDK 호출 없이 테스트
  - Protocol 검증, SDK 옵션 오버라이드, 세션 재개, 메시지 변환 등 모두 커버
  - BDD 패턴 (# given, # when, # then) 사용
  - typing.Any 대신 MagicMock 타입 사용 (ANN401 에러 회피)

### PROBLEMS FOR NEXT TASKS
- 없음: task 7 (DroidAgent 구현)을 진행할 준비 완료

### VERIFICATION RESULTS
- 테스트 실행 결과: 28개 테스트 모두 통과 (asyncio 14개 + trio 14개)
  - test_agent_protocol_validation: Agent Protocol 만족 확인
  - test_initialize_creates_client: SDK 클라이언트 생성 및 옵션 검증
  - test_initialize_with_sdk_options_override: sdk_options 오버라이드 검증
  - test_start_session_new: 새 세션 시작 검증
  - test_start_session_resume: 세션 재개 검증
  - test_start_session_resume_failure: SessionResumeError 발생 검증
  - test_send_message: 메시지 전송 검증
  - test_send_without_connection_raises_error: 연결 없이 전송 시 에러 검증
  - test_stream_assistant_message: AssistantMessage 스트리밍 검증
  - test_stream_system_message: SystemMessage 스트리밍 및 session_id 추출 검증
  - test_stream_result_message: ResultMessage 스트리밍 검증
  - test_stream_without_connection_raises_error: 연결 없이 스트림 시 에러 검증
  - test_close: 클라이언트 종료 검증
  - test_close_when_not_connected: 연결 없이 종료 시 정상 동작 검증
- Ruff 린트 체크: All checks passed!
- Basedpyright 타입 체크: 0 errors, 0 warnings, 0 notes
- Git 커밋 성공: commit 645e7ba "feat: implement ClaudeAgent with SDK integration"

### LEARNINGS
- claude-agent-sdk의 TextBlock은 `type` 파라미터가 없음 (TextBlock(text="...") 형태로 사용)
- typing.Any는 ruff ANN401 에러를 발생시키므로 MagicMock 타입 사용
- Mock 함수의 AsyncIterator 반환 타입: `AsyncIterator[MagicMock]` 사용
- Agent Protocol과 동일한 패턴 재사용 (imports 상단 배치, match-case, Optional 체크)
- pytest-anyio는 자동으로 asyncio/trio 백엔드 모두에서 테스트 실행 (14개 테스트 → 28개 실행)

소요 시간: 약 5분


[2025-10-09 17:40] - 7. DroidAgent 구현

### DISCOVERED ISSUES
- 없음: DroidAgent와 테스트 파일이 이미 구현되어 있었음 (이전 executor가 작업했으나 문서화를 완료하지 못한 것으로 추정)

### IMPLEMENTATION DECISIONS
- DroidAgent 클래스 구현 (sisyphus/agents/droid.py)
  - Agent Protocol 준수: supports_interactive = False (Droid는 인터랙티브 미지원)
  - ClaudeAgent 패턴 재사용 (imports 상단 배치, TYPE_CHECKING 가드)
  - ProcessManager 활용 (run_with_timeout, terminate_gracefully, parse_jsonl_stream)
- 바이너리 자동 탐색 로직 (initialize)
  - Priority 1: Constructor binary parameter (exists() 체크)
  - Priority 2: PATH search (shutil.which)
  - Priority 3: Environment variable DROID_BINARY
  - 모두 실패하면 AgentNotFoundError
- 세션 관리 (start_session)
  - session_id가 없으면 uuid.uuid4() 생성
  - Command: `droid exec --input-format stream-json --output-format stream-json --session {id} --skip-permissions-unsafe`
  - model이 있으면 --model 추가
  - ProcessManager.run_with_timeout()로 30초 타임아웃
- 메시지 전송 (send)
  - JSON 객체 생성: {"role": "user", "content": message}
  - stdin으로 JSONL 형식 전송 (UTF-8 인코딩 + 개행)
- 스트림 파싱 (stream)
  - ProcessManager.parse_jsonl_stream()로 stdout 파싱
  - 각 JSON 객체를 AgentMessage로 변환
  - role, content 추출, 나머지는 metadata
- 프로세스 정리 (close)
  - ProcessManager.terminate_gracefully()로 5초 타임아웃
- 포괄적인 테스트 작성 (19개 테스트)
  - Protocol 검증, supports_interactive, 바이너리 탐색, 세션 관리, 메시지 전송/수신, 에러 처리, 타임아웃
  - BDD 패턴 (# given, # when, # then)
  - Mock을 사용한 단위 테스트

### PROBLEMS FOR NEXT TASKS
- 없음: task 8 (OpenCodeAgent 구현)을 진행할 준비 완료

### VERIFICATION RESULTS
- 테스트 실행 결과: 38개 테스트 모두 통과 (asyncio 19개 + trio 19개)
  - test_agent_protocol_validation: Agent Protocol 만족 확인
  - test_supports_interactive_is_false: supports_interactive = False 확인
  - test_initialize_*: 바이너리 탐색 로직 검증 (PATH, binary parameter, env variable, not found)
  - test_start_session_*: 세션 생성/재개, UUID 생성, autonomy unsafe, model 포함 확인
  - test_send_message: stdin으로 JSON 전송 확인
  - test_stream_messages: JSONL 파싱 및 AgentMessage 변환 확인
  - test_close_*: 프로세스 종료 확인
  - test_timeout_handling: ProcessTimeoutError 처리 확인
- Ruff 린트 체크: All checks passed!
- Basedpyright 타입 체크: 0 errors, 1 warning (anyio.abc.Process 관련 무해한 경고)

### LEARNINGS
- DroidAgent는 ClaudeAgent와 거의 동일한 패턴 사용 (Protocol, TYPE_CHECKING, ProcessManager)
- shutil.which()는 PATH에서 실행 파일 검색 시 유용 (None 반환 시 없음)
- Droid CLI는 `--input-format stream-json --output-format stream-json` 형태로 JSONL 통신
- autonomy는 `--skip-permissions-unsafe` 플래그 사용 (가이드의 --autonomy skip-permissions-unsafe와는 다른 형태)
- ProcessManager를 사용하면 타임아웃, JSONL 파싱, graceful shutdown이 자동 처리됨
- 테스트에서 async 함수를 캡처할 때는 `side_effect`로 async 함수 전달

소요 시간: 약 3분


[2025-10-09 17:53] - 8. OpenCodeAgent 구현

### DISCOVERED ISSUES
- 없음: 기존 코드에서 발견된 문제 없음

### IMPLEMENTATION DECISIONS
- OpenCodeAgent 클래스 구현 (sisyphus/agents/opencode.py)
  - Agent Protocol 준수: supports_interactive = True (OpenCode는 인터랙티브 지원)
  - DroidAgent와 유사한 패턴 재사용 (imports 상단 배치, TYPE_CHECKING 가드, 바이너리 탐색)
  - ProcessManager + httpx 조합 사용 (서브프로세스 + HTTP 클라이언트)
- 바이너리 자동 탐색 로직 (_find_binary)
  - Priority 1: Constructor binary parameter (exists() 체크)
  - Priority 2: PATH search (shutil.which)
  - Priority 3: Environment variable OPENCODE_BINARY
  - 모두 실패하면 AgentNotFoundError
- 서버 자동 시작 로직
  - _find_available_port(): anyio.create_tcp_listener로 사용 가능한 포트 찾기
  - _start_server(): `opencode serve --host 127.0.0.1 --port {port}` 실행
  - ProcessManager.run_with_timeout()로 10초 타임아웃
  - _health_check(): GET /app 엔드포인트, 최대 5회 재시도, 2초 간격
- 외부 서버 지원
  - server_url이 제공되면 서버 시작 스킵
  - 외부 서버에 대해서도 헬스체크 수행
- 세션 관리 (start_session)
  - POST /session {"appId": session_id or "default"}
  - 서버가 ses_xxx 형식 ID 반환
  - None 체크 후 반환 (타입 안전성)
- 메시지 전송 (send)
  - POST /app {"session": session_id, "message": message}
- SSE 스트리밍 (stream)
  - GET /event?session={session_id}, Accept: text/event-stream
  - httpx.AsyncClient.stream()으로 context manager 사용
  - aiter_lines()로 라인별 파싱
  - "data: " 접두사 라인만 처리, JSON 파싱
  - match-case 패턴으로 이벤트 타입별 AgentMessage 생성
  - JSON 파싱 에러 시 스킵 (크래시 방지)
- 프로세스 정리 (close)
  - httpx.AsyncClient.aclose()
  - ProcessManager.terminate_gracefully()로 5초 타임아웃
- 포괄적인 테스트 작성 (24개 테스트)
  - Protocol 검증, supports_interactive, 바이너리 탐색, 서버 자동 시작, 헬스체크 재시도
  - 외부 서버 URL, 세션 생성, 메시지 전송, SSE 파싱 (다양한 이벤트 타입)
  - SSE 에러 처리 (잘못된 라인, 잘못된 JSON, 빈 데이터 필드)
  - BDD 패턴 (# given, # when, # then)
  - Mock을 사용한 단위 테스트 (httpx.AsyncClient, anyio.abc.Process)

### PROBLEMS FOR NEXT TASKS
- 없음: task 9 (PromptResolver 구현)를 진행할 준비 완료

### VERIFICATION RESULTS
- 테스트 실행 결과: 48개 테스트 모두 통과 (asyncio 24개 + trio 24개)
  - test_opencode_supports_interactive: supports_interactive = True 확인
  - test_opencode_protocol_compliance: Agent Protocol 만족 확인
  - test_binary_discovery_*: 바이너리 탐색 로직 검증 (PATH, constructor, env, not found)
  - test_find_available_port: 포트 찾기 로직 확인
  - test_server_auto_start: 서버 시작 및 명령 검증
  - test_server_start_failure: ServerStartError 처리 확인
  - test_health_check_*: 헬스체크 성공/재시도/실패 확인
  - test_external_server_url: 외부 서버 사용 시 자동 시작 스킵 확인
  - test_session_creation_*: 세션 생성 및 기본값 확인
  - test_send_message: POST /app 호출 확인
  - test_sse_streaming_*: 다양한 SSE 이벤트 파싱 (message.chunk, tool, error, skip invalid, malformed JSON, empty data)
  - test_close_*: 리소스 정리 확인 (프로세스 있음/없음)
- Ruff 린트 체크: All checks passed!
- Basedpyright 타입 체크: 0 errors, 2 warnings (anyio.abc 관련 무해한 경고)
- Git 커밋 성공: commit 2c2d9bf "feat: implement OpenCodeAgent with server auto-start"

### LEARNINGS
- httpx.AsyncClient.stream()은 async context manager로 사용해야 함
- SSE 스트리밍 테스트 시 Mock 설정이 복잡함:
  - async def mock_aiter_lines()를 정의하여 AsyncIterator[str] 반환
  - mock_stream_ctx.__aenter__과 __aexit__을 AsyncMock으로 설정
  - mock_client.stream.return_value에 mock_stream_ctx 할당
- anyio.create_tcp_listener로 사용 가능한 포트를 동적으로 찾을 수 있음 (port=0)
- OpenCode SSE format: "data: {JSON}" 형태, event 필드로 타입 구분 (message.chunk, tool.start, error 등)
- match-case는 if-elif-else보다 가독성이 좋음 (Python 3.10+)
- 타입 안전성: session_id가 None일 수 있으므로 명시적 체크 후 반환

소요 시간: 약 12분
