# 사용자의 최초 요청 (기록용)

그 외에 불명확한것들까지 최대한 명시화해서 계획서로 작성하고, 리뷰받으며 iterate 해줘.

(이전 대화 컨텍스트: Sisyphus 멀티 에이전트 시스템 - Claude, Droid, OpenCode 에이전트를 지원하며, execute와 verify를 별개 에이전트로 실행할 수 있고, TUI/CLI 모드를 지원하는 확장 가능한 SOLID 원칙 기반 시스템 구축)

## 사용자가 이후에 추가 요청한 내용들 (기록용)

- 세션 관리는 ExecutionLoop에서 조율, SessionStore가 영속성 담당, 각 에이전트가 실제 세션 처리
- Verify는 항상 새 세션으로 독립적 검증
- Droid는 autonomy를 항상 "skip-permissions-unsafe"로 고정
- UI는 `--no-tui` 플래그로 CLI/TUI 선택
- 프롬프트는 'slash-command' | 'plain-text' | PathLike | str 형태 지원
- execute-extra-prompt와 verify-extra-prompt로 추가 프롬프트 append
- 바이너리는 `--binary` 하나로 통합 (개별 override 가능)
- OpenCode는 자동으로 서버 시작 (--opencode-server-url로 외부 서버 지정 가능)
- SDK 옵션은 JSON으로 주입 가능 (--execute-sdk-options, --verify-sdk-options)
- **Plan-reviewer 피드백 반영**:
  - UIProtocol을 ExecutionLoop 전에 정의 (의존성 순서 수정)
  - utils 모듈 구현 추가 (process.py, logging.py)
  - OpenCode/Droid 안전성 강화 (헬스체크, 타임아웃, 에러 처리)
  - SessionStore 안정성 (원자적 쓰기, 파일 락)
  - CLI 옵션별 검증 테스트 확대
  - 타임아웃/재시도 기본값 명시
- **메시지 큐잉 및 인터랙티브 TUI 추가**:
  - OpenCode 스타일 TUI: 상단 진행상황/chat, 하단 입력창
  - 인터랙티브 메시지 입력 지원 (Claude, OpenCode만)
  - 메시지 큐 관리로 적절한 타이밍에 전달
  - UP 키로 미전송 메시지 수정 가능
  - Ctrl+C/Ctrl+D 안정적 처리

# 작업 목표

- Claude, Droid, OpenCode 세 가지 에이전트를 지원하는 통합 시스템 구축
- Execute 페이즈와 Verify 페이즈를 별개 에이전트로 실행 가능한 유연한 아키텍처
- TUI(Textual 기반)와 CLI(Rich 기반) 두 가지 UI 모드 지원
- **인터랙티브 TUI**: OpenCode 스타일로 상단 채팅/진행상황, 하단 입력창
- **메시지 큐잉**: 사용자 입력을 큐에 저장하고 적절한 타이밍에 전달
- SOLID 원칙을 준수하는 확장 가능한 설계
- 세션 관리, 프롬프트 처리, 작업 검증을 모듈화하여 유지보수 용이성 확보
- Protocol 기반 인터페이스로 새 에이전트 추가 시 기존 코드 수정 불필요
- 외부 통합 안정성 (서브프로세스, SSE, 서버 기동) 확보

## 아키텍처 플로우 다이어그램

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLI Entry Point                           │
│                        (sisyphus/cli.py)                          │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                      UI Layer (Protocol)                          │
│  ┌──────────────────┐              ┌──────────────────┐          │
│  │   TUI (Textual)  │              │   CLI (Rich)     │          │
│  │  - ChatLog       │              │  - Console       │          │
│  │  - StatusPanel   │              │  - Markdown      │          │
│  │  - InputBar      │              │                  │          │
│  └──────────────────┘              └──────────────────┘          │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                      ExecutionLoop (Core)                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │ PromptResolver │  │  SessionStore  │  │ TaskValidator  │     │
│  │  - Slash cmd   │  │  - File lock   │  │  - ai-todolist │     │
│  │  - Plain text  │  │  - Atomic save │  │    validation  │     │
│  │  - File path   │  │                │  │                │     │
│  └────────────────┘  └────────────────┘  └────────────────┘     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Phase 1: Execute  →  Phase 2: Verify (new session)    │    │
│  └─────────────────────────────────────────────────────────┘    │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Agent Layer (Protocol)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐          │
│  │ ClaudeAgent │  │ DroidAgent  │  │ OpenCodeAgent   │          │
│  │  - SDK      │  │  - anyio    │  │  - anyio        │          │
│  │  - Resume   │  │    subprocess│  │    subprocess  │          │
│  │             │  │  - JSONL    │  │  - REST API     │          │
│  │             │  │  - unsafe   │  │  - SSE stream   │          │
│  │             │  │    autonomy │  │  - Health check │          │
│  └─────────────┘  └─────────────┘  └─────────────────┘          │
└──────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Utils & Infrastructure                         │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  ProcessManager │  │ LoggerFactory│  │    Types     │        │
│  │  - anyio only   │  │ - Session log│  │  - Protocols │        │
│  │  - Timeout      │  │ - File/Console│ │  - Errors    │        │
│  │  - SIGTERM/KILL │  │              │  │              │        │
│  │  - JSONL parser │  │              │  │              │        │
│  └─────────────────┘  └──────────────┘  └──────────────┘        │
└──────────────────────────────────────────────────────────────────┘

Data Flow:
1. CLI parses options → creates agents via factory
2. UI renders messages from ExecutionLoop
3. ExecutionLoop orchestrates Execute → Verify
4. Agents communicate via Protocol methods
5. SessionStore persists state with file locks
6. Utils provide cross-cutting concerns (process, logging)
```

# 작업 배경

현재 `agentloop_sdk.py`는 Claude Agent SDK만 지원하며, UI와 로직이 강하게 결합되어 있어 확장이 어려움. 새로운 에이전트(Droid, OpenCode)를 추가하고, execute와 verify를 별개 에이전트로 실행하며, 다양한 프롬프트 형식을 지원하는 유연한 시스템이 필요함. SOLID 원칙을 따르면서도 실용적인 설계를 통해 확장성과 유지보수성을 확보. Plan-reviewer 피드백을 반영하여 외부 통합 안정성과 에러 처리를 강화.

# 작업 시작 여부
is_execution_started = TRUE

# 모든 목표 달성 여부
is_all_goals_accomplished = FALSE

# 병렬 실행 여부
parallel_requested = FALSE

# 현재 진행 중인 작업
- Task 15.1: Typer CLI 구현 (sisyphus/cli.py)

# 작업 계획

## 필요한 사전 지식

### 기술 스택
- **Python 3.12**: 타입 힌팅, Protocol, async/await
- **anyio**: 비동기 런타임 추상화 (asyncio/trio 지원)
- **Typer**: CLI 프레임워크
- **Textual**: TUI 프레임워크
- **Rich**: CLI 렌더링
- **pytest + pytest-anyio**: 비동기 테스트
- **httpx**: HTTP/SSE 클라이언트 (OpenCode용)

### 에이전트별 SDK
- **Claude Agent SDK**: `claude_agent_sdk` 패키지, ClaudeAgentOptions, ClaudeSDKClient
- **Droid CLI**: `droid exec` 서브프로세스, stream-json 모드, JSONL 통신
- **OpenCode**: REST API 서버 모드, httpx 클라이언트, SSE 스트리밍

### 설계 패턴
- **Protocol (PEP 544)**: 구조적 서브타이핑, 덕 타이핑
- **Dependency Injection**: 의존성 역전
- **Factory Pattern**: UI/에이전트 생성
- **Strategy Pattern**: 세션 재개 전략

### 타임아웃 기본값 (시스템 전체 표준)
- Droid 프로세스 시작: 30초
- OpenCode 서버 시작: 10초
- OpenCode 헬스체크 재시도: 최대 5회, 2초 간격
- SSE 스트림 idle timeout: 60초
- 일반 HTTP 요청: 30초
- 서브프로세스 종료 대기: 5초 (SIGTERM → SIGKILL)

## 파일 구조 및 역할

```
sisyphus/
├── prompts/
│   ├── execute_command.md       # 기본 execute 프롬프트
│   └── architect_command.md     # 기본 verify 프롬프트
│
├── sisyphus/
│   ├── __init__.py
│   ├── __main__.py             # Entry point
│   ├── cli.py                  # Typer CLI 정의
│   │
│   ├── agents/                 # 에이전트 구현
│   │   ├── __init__.py
│   │   ├── base.py            # Agent Protocol
│   │   ├── claude.py          # ClaudeAgent
│   │   ├── droid.py           # DroidAgent
│   │   ├── opencode.py        # OpenCodeAgent
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_agents.py
│   │
│   ├── core/                   # 핵심 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── loop.py            # ExecutionLoop
│   │   ├── prompts.py         # PromptResolver
│   │   ├── session.py         # SessionStore (파일 락 포함)
│   │   ├── tasks.py           # TaskValidator
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_loop.py
│   │       ├── test_prompts.py
│   │       └── test_session.py
│   │
│   ├── ui/                     # UI 구현
│   │   ├── __init__.py
│   │   ├── base.py            # UIProtocol
│   │   ├── tui/
│   │   │   ├── __init__.py
│   │   │   ├── app.py
│   │   │   ├── components/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chat_log.py
│   │   │   │   ├── status_panel.py
│   │   │   │   └── input_bar.py
│   │   │   └── layouts/
│   │   │       ├── __init__.py
│   │   │       └── main.py
│   │   ├── cli/
│   │   │   ├── __init__.py
│   │   │   └── console.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_ui.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py         # 통합 로거 (세션별 핸들러)
│       ├── process.py         # 프로세스 관리 (타임아웃, 종료)
│       ├── types.py           # 공통 타입 정의
│       ├── errors.py          # 커스텀 예외
│       └── tests/
│           ├── __init__.py
│           ├── test_logging.py
│           └── test_process.py
│
├── logs/                       # 로그 파일 (자동 생성)
├── sessions/                   # 세션 저장소 (자동 생성)
└── pyproject.toml
```

## 맥락 이해를 위해 참고해야 할 파일들

### 1. pyproject.toml
- **역할**: 프로젝트 설정 및 의존성 정의
- **참고할 부분**:
  - `dependencies`: anyio, trio, uvloop
  - `dev` 그룹: pytest-anyio, basedpyright, ruff
  - `tool.ruff`: 더블 쿼터, 타입 힌팅 필수(ANN001)
  - `tool.basedpyright`: standard 모드
- **주의사항**:
  - 모든 함수 파라미터에 타입 힌팅 필수
  - 더블 쿼터 사용
  - pytest mark와 fixture는 괄호 사용

### 2. resources/droid-cli-integration.md
- **역할**: Droid CLI 통합 가이드
- **참고할 부분**:
  - stream-json 모드 사용법
  - 세션 ID는 클라이언트가 UUID 생성
  - autonomy는 항상 "skip-permissions-unsafe"
- **주의사항**:
  - Droid는 서버가 아닌 서브프로세스로 실행
  - JSONL 파싱 에러 처리 필수
  - 타임아웃 및 프로세스 종료 처리

### 3. resources/opencode-integration.md
- **역할**: OpenCode 통합 가이드
- **참고할 부분**:
  - REST API 엔드포인트 (/session, /app, etc.)
  - SSE 스트리밍 (/event)
  - 서버 자동 시작 (`opencode serve`)
- **주의사항**:
  - 서버 시작 후 헬스체크 필수 (재시도 로직)
  - SSE 파싱 에러 처리
  - 서버 준비 완료 확인

### 4. resources/session-management-analysis.md
- **역할**: 세션 관리 전략 분석
- **참고할 부분**:
  - Claude: UUID v4, resume 파라미터
  - Droid: 클라이언트 관리, UUID 필수
  - OpenCode: 서버 관리, ses_xxx 형식
- **주의사항**:
  - Verify는 항상 새 세션
  - 세션 파일 동시 접근 시 락 필요

### 5. local-ignore/agentloop_sdk.py
- **역할**: 기존 Claude 전용 구현 (참고용)
- **참고할 부분**:
  - SessionManager 구현
  - Textual TUI 구조
  - 로깅 방식
- **주의사항**:
  - UI와 로직이 결합되어 있음 (분리 필요)
  - Claude 전용이므로 일반화 필요

## 구현 세부사항

### 핵심 설계 원칙

1. **Protocol 기반 인터페이스**
   - `Agent(Protocol)`: 모든 에이전트가 구현
   - `UIProtocol`: 모든 UI가 구현
   - 런타임 타입 체크 가능 (`@runtime_checkable`)

2. **의존성 역전**
   - ExecutionLoop는 Agent/UI Protocol에 의존
   - 구체 클래스에 의존하지 않음

3. **세션 관리 계층**
   - CLI → ExecutionLoop (전략 결정)
   - ExecutionLoop → SessionStore (영속성, 락)
   - SessionStore → Agent (실제 처리)

4. **프롬프트 처리 유연성**
   - 'slash-command': /execute, /architect
   - 'plain-text': 내장 평문 프롬프트
   - PathLike: 파일에서 읽기
   - str: 직접 텍스트 사용

5. **에이전트별 특성**
   - Claude: SDK 사용, resume 지원, **인터랙티브 지원**
   - Droid: 서브프로세스, stream-json, 항상 unsafe, JSONL 파싱, **인터랙티브 미지원**
   - OpenCode: REST API, 자동 서버 시작, SSE 스트리밍, 헬스체크, **인터랙티브 지원**

6. **안정성 및 에러 처리**
   - 모든 외부 통합에 타임아웃 적용
   - 서브프로세스 정리 (SIGTERM → SIGKILL)
   - 파일 락으로 동시 접근 방지
   - 원자적 파일 쓰기 (임시 파일 + rename)

7. **인터랙티브 TUI (OpenCode 스타일)**
   - **레이아웃**:
     - 상단 70%: 진행상황/채팅 로그 (스크롤 가능)
     - 중간 20%: 상태 패널 (현재 작업, 도구 사용 등)
     - 하단 10%: 입력창 (메시지 입력)
   - **메시지 큐**:
     - anyio 메모리 객체 스트림 (anyio.create_memory_object_stream)
     - 에이전트 응답 대기 중에도 입력 가능
     - 적절한 타이밍에 메시지 전달
   - **키 바인딩**:
     - UP 화살표: 미전송 메시지 수정
     - Ctrl+C: 인터럽트 (2회 누르면 종료) - **현재 agentloop_sdk.py는 작동 안 함**
     - Ctrl+D: 세션 종료
     - Enter: 메시지 큐에 추가
   - **Ctrl+C 처리 개선** (agentloop_sdk.py의 문제 해결):
     ```python
     class TUI(App):
         def __init__(self):
             super().__init__()
             self.ctrl_c_count = 0
             self.last_ctrl_c_time = None
             self.shutdown_event = anyio.Event()

         async def on_key(self, event: Key) -> None:
             """키 이벤트 처리 - Textual의 실제 키 이벤트 사용"""
             if event.key == "ctrl+c":
                 await self._handle_interrupt()

         async def _handle_interrupt(self) -> None:
             """올바른 Ctrl+C 처리"""
             current_time = datetime.now()

             # 1초 내 두 번째 Ctrl+C인지 확인
             if (self.last_ctrl_c_time and
                 (current_time - self.last_ctrl_c_time).total_seconds() < 1.0):
                 self.ctrl_c_count += 1

                 if self.ctrl_c_count >= 2:
                     # 안전한 종료 시작
                     await self._safe_shutdown()
             else:
                 self.ctrl_c_count = 1
                 self.last_ctrl_c_time = current_time
                 # 상태 패널에 표시
                 self.show_status("⚠️ Ctrl+C 한 번 더 누르면 종료됩니다")

         async def _safe_shutdown(self) -> None:
             """안전한 종료 절차"""
             try:
                 self.show_status("🔄 종료 중...")
                 # 1. 현재 에이전트 작업 중단
                 if self.current_agent:
                     await self.current_agent.close()
                 # 2. 세션 저장
                 await self.session_store.save()
                 # 3. 메시지 큐 정리
                 self.message_stream.close()
                 # 4. 종료 이벤트 설정
                 self.shutdown_event.set()
             finally:
                 self.exit()
     ```
   - **주의사항**:
     - Textual의 action_interrupt 대신 on_key 사용
     - anyio.Event로 graceful shutdown
     - 프로세스/리소스 정리 필수
   - **인터랙티브 모드**:
     - Claude: 대화 턴마다 메시지 전송 가능
     - OpenCode: REST API를 통한 메시지 전송
     - Droid: 인터랙티브 미지원 (단일 세션만)

### 구현 시 주의사항

1. **타입 안전성**
   - 모든 함수에 파라미터와 반환값 타입 힌팅
   - Protocol 사용 시 @runtime_checkable 데코레이터

2. **비동기 처리**
   - anyio 사용으로 asyncio/trio 모두 지원
   - 모든 I/O는 async

3. **에러 처리**
   - 커스텀 예외 계층 (SisyphusError)
   - 에이전트별 에러 (AgentNotFoundError, SessionResumeError, ServerStartError)
   - UI에 에러 메시지 표시

4. **로깅**
   - 파일은 append 모드
   - 세션이 공유되면 같은 로그 파일에 계속 기록
   - 형식: `{agent}_{timestamp}_{tz}.log`
   - 레벨별 핸들러 (파일: DEBUG, 콘솔: INFO)

5. **테스트**
   - pytest-anyio로 비동기 테스트
   - 각 모듈별 독립 테스트
   - Protocol 기반이므로 mock 쉬움
   - 외부 통합은 mock과 실제 통합 테스트 모두 작성

## 프로젝트 커밋 메시지 스타일

현재 커밋 히스토리가 짧아 명확한 패턴 없음. 다음 컨벤션 제안:
- 구조: `<type>: <subject>`
- 타입: feat, fix, refactor, test, docs
- 예시:
  - `feat: add Agent Protocol and base implementation`
  - `feat: implement ClaudeAgent with session support`
  - `test: add unit tests for PromptResolver`
  - `fix: handle SSE parsing errors in OpenCodeAgent`

# TODOs

## Phase 1: 기반 구조 및 타입 정의

- [x] 1. 프로젝트 의존성 추가 및 기본 구조 설정
  - [x] 1.1 pyproject.toml에 의존성 추가
    ```toml
    dependencies = [
        "anyio>=4.11.0",
        "trio>=0.31.0",
        "uvloop>=0.21.0",
        "typer>=0.15.0",
        "textual>=1.0.0",
        "rich>=13.0.0",
        "httpx>=0.28.0",  # OpenCode용
        "claude-agent-sdk>=1.0.0",  # Claude용
        "aiofiles>=24.0.0",  # 비동기 파일 I/O
    ]
    ```
    - 현재: anyio, trio, uvloop만 존재
    - 변경: typer, textual, rich, httpx, claude-agent-sdk, aiofiles 추가
  - [x] 1.2 디렉토리 구조 생성
    ```bash
    mkdir -p sisyphus/{agents,core,ui/{tui/components,tui/layouts,cli},utils}
    mkdir -p sisyphus/agents/tests sisyphus/core/tests sisyphus/ui/tests sisyphus/utils/tests
    mkdir -p prompts logs sessions
    touch sisyphus/{agents,core,ui,ui/tui,ui/tui/components,ui/tui/layouts,ui/cli,utils}/__init__.py
    ```
  - [x] 1.3 커밋: `git add pyproject.toml sisyphus/ prompts/ && git commit -m "feat: setup project structure and dependencies"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] pyproject.toml에 모든 필수 의존성이 추가되었는가?
    - [x] 디렉토리 구조가 설계대로 생성되었는가?
    - [x] 모든 패키지에 __init__.py가 존재하는가?
    - [x] 커밋이 정상적으로 되었는가?

- [x] 2. 공통 타입 및 에러 정의 (sisyphus/utils/types.py, errors.py)
  - [x] 2.1 구현: sisyphus/utils/types.py 작성
    ```python
    from dataclasses import dataclass, field
    from typing import Any, Optional
    from pathlib import Path

    @dataclass
    class AgentMessage:
        """통합 메시지 형식"""
        role: str  # 'user', 'assistant', 'system'
        content: str
        metadata: dict[str, Any] = field(default_factory=dict)

    @dataclass
    class AgentConfig:
        """에이전트 설정"""
        agent_type: str  # 'claude', 'droid', 'opencode'
        model: Optional[str]
        prompt: tuple[str, Optional[str]]  # (base_prompt, extra_prompt)
        binary: Optional[Path]
        sdk_options: dict[str, Any]
        opencode_server_url: Optional[str] = None
    ```
  - [x] 2.2 구현: sisyphus/utils/errors.py 작성
    ```python
    class SisyphusError(Exception):
        """Base exception"""
        pass

    class AgentNotFoundError(SisyphusError):
        """Agent binary not found"""
        pass

    class SessionResumeError(SisyphusError):
        """Session resume failed"""
        pass

    class ServerStartError(SisyphusError):
        """Failed to start server"""
        pass

    class ProcessTimeoutError(SisyphusError):
        """Process operation timed out"""
        pass

    class HealthCheckError(SisyphusError):
        """Health check failed"""
        pass
    ```
  - [x] 2.3 테스트 작성: sisyphus/utils/tests/test_types.py
  - [x] 2.4 테스트 실행: `pytest -xvs sisyphus/utils/tests/test_types.py`
  - [x] 2.5 린트 및 타입 체크
    - [x] `ruff check sisyphus/utils/types.py sisyphus/utils/errors.py`
    - [x] `basedpyright sisyphus/utils/types.py sisyphus/utils/errors.py`
  - [x] 2.6 커밋: `git add sisyphus/utils/{types.py,errors.py,tests/} && git commit -m "feat: add common types and error definitions"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] AgentMessage와 AgentConfig 타입이 모든 필드와 함께 정의되었는가?
    - [x] 커스텀 예외가 계층적으로 정의되었는가?
    - [x] 타입 체크와 린트가 통과하는가?
    - [x] 테스트가 작성되고 통과하는가?

- [x] 3. 유틸리티 모듈 구현 (sisyphus/utils/)
  - [x] 3.1 구현: sisyphus/utils/process.py 작성
    - anyio 서브프로세스 래퍼
    - 타임아웃 지원
    - SIGTERM → SIGKILL 처리
    - JSONL 파서 (최대 라인 크기 제한)
    ```python
    import anyio
    import signal
    from typing import Optional, AsyncIterator
    from sisyphus.utils.errors import ProcessTimeoutError

    class ProcessManager:
        """서브프로세스 관리 유틸"""

        @staticmethod
        async def run_with_timeout(
            cmd: list[str],
            timeout: float = 30.0
        ) -> anyio.abc.Process:
            """타임아웃과 함께 프로세스 실행"""
            # 구현 필요
            pass

        @staticmethod
        async def terminate_gracefully(
            process: anyio.abc.Process,
            timeout: float = 5.0
        ) -> None:
            """SIGTERM 후 SIGKILL"""
            # 구현 필요
            pass

        @staticmethod
        async def parse_jsonl_stream(
            stream: anyio.abc.ByteReceiveStream,
            max_line_size: int = 10_000_000
        ) -> AsyncIterator[dict]:
            """JSONL 스트림 파싱 (에러 처리 포함)"""
            # 구현 필요
            pass
    ```
  - [x] 3.2 구현: sisyphus/utils/logging.py 작성
    - 세션/에이전트별 로거 팩토리
    - 파일 핸들러 관리 (rotate, 권한)
    - 레벨별 핸들러 (파일: DEBUG, 콘솔: INFO)
    ```python
    import logging
    from pathlib import Path
    from typing import Optional

    class LoggerFactory:
        """로거 팩토리"""

        @staticmethod
        def create_logger(
            agent_type: str,
            session_id: Optional[str] = None,
            log_dir: Path = Path("./logs")
        ) -> logging.Logger:
            """에이전트/세션별 로거 생성"""
            # 구현 필요
            pass
    ```
  - [x] 3.3 테스트 작성: sisyphus/utils/tests/test_process.py, test_logging.py
  - [x] 3.4 테스트 실행: `pytest -xvs sisyphus/utils/tests/`
  - [x] 3.5 린트 및 타입 체크
    - [x] `ruff check sisyphus/utils/{process.py,logging.py}`
    - [x] `basedpyright sisyphus/utils/{process.py,logging.py}`
  - [x] 3.6 커밋: `git add sisyphus/utils/{process.py,logging.py,tests/} && git commit -m "feat: add process and logging utilities"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] ProcessManager의 타임아웃 처리가 작동하는가?
    - [x] SIGTERM → SIGKILL 전환이 올바른가?
    - [x] JSONL 파서가 에러를 처리하는가?
    - [x] LoggerFactory가 세션별 로거를 생성하는가?
    - [x] 테스트가 모든 케이스를 커버하는가?

## Phase 2: Protocol 및 UI 기반 정의

- [x] 4. Agent Protocol 정의 (sisyphus/agents/base.py)
  - [x] 4.1 구현: sisyphus/agents/base.py 작성
    ```python
    from typing import Protocol, AsyncIterator, Optional, runtime_checkable
    from sisyphus.utils.types import AgentMessage

    @runtime_checkable
    class Agent(Protocol):
        """모든 에이전트가 구현해야 하는 프로토콜"""

        supports_interactive: bool

        async def initialize(self) -> None:
            """에이전트 초기화"""
            ...

        async def start_session(self, session_id: Optional[str] = None) -> str:
            """세션 시작 또는 재개, 실제 세션 ID 반환"""
            ...

        async def send(self, message: str) -> None:
            """메시지 전송"""
            ...

        async def stream(self) -> AsyncIterator[AgentMessage]:
            """응답 스트리밍"""
            ...

        async def close(self) -> None:
            """정리"""
            ...
    ```
  - [x] 4.2 테스트 작성: sisyphus/agents/tests/test_base.py
    - Protocol 체크 테스트 (isinstance 검증)
  - [x] 4.3 테스트 실행: `pytest -xvs sisyphus/agents/tests/test_base.py`
  - [x] 4.4 린트 및 타입 체크
    - [x] `ruff check sisyphus/agents/base.py`
    - [x] `basedpyright sisyphus/agents/base.py`
  - [x] 4.5 커밋: `git add sisyphus/agents/{base.py,tests/} && git commit -m "feat: define Agent Protocol with runtime checking"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] Protocol이 @runtime_checkable로 데코레이트되었는가?
    - [x] 모든 필수 메서드가 정의되었는가?
    - [x] 타입 힌팅이 정확한가?
    - [x] 테스트가 Protocol 검증을 포함하는가?

- [x] 5. UIProtocol 정의 및 팩토리 (sisyphus/ui/base.py)
  - [x] 5.1 구현: sisyphus/ui/base.py 작성
    ```python
    from typing import Protocol, Optional, runtime_checkable
    from sisyphus.utils.types import AgentMessage

    @runtime_checkable
    class UIProtocol(Protocol):
        """UI 구현이 따라야 할 프로토콜"""

        async def initialize(self) -> None:
            """UI 초기화"""
            ...

        async def show_message(self, message: AgentMessage, source: str) -> None:
            """메시지 표시 (source: 'execute' or 'verify')"""
            ...

        async def show_status(self, status: str) -> None:
            """상태 메시지 표시"""
            ...

        async def get_input(self) -> Optional[str]:
            """사용자 입력 받기 (TUI only, CLI는 None 반환)"""
            ...

        async def close(self) -> None:
            """UI 종료"""
            ...

    def create_ui(mode: str) -> UIProtocol:
        """UI 팩토리"""
        if mode == "tui":
            from sisyphus.ui.tui import TUI
            return TUI()
        else:
            from sisyphus.ui.cli import CLI
            return CLI()
    ```
  - [x] 5.2 테스트 작성: sisyphus/ui/tests/test_base.py
  - [x] 5.3 린트 및 타입 체크
    - [x] `ruff check sisyphus/ui/base.py`
    - [x] `basedpyright sisyphus/ui/base.py`
  - [x] 5.4 커밋: `git add sisyphus/ui/{base.py,tests/} && git commit -m "feat: define UIProtocol and factory"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] Protocol이 올바르게 정의되었는가?
    - [x] 팩토리 함수가 작동하는가?

## Phase 3: Agent 구현

- [x] 6. ClaudeAgent 구현 (sisyphus/agents/claude.py)
  - [x] 6.1 구현: sisyphus/agents/claude.py 작성
    - 참고 코드: local-ignore/agentloop_sdk.py의 ClaudeStreamClient
    - ClaudeAgent 클래스는 Agent Protocol을 만족해야 함
    - SDK 초기화, 세션 재개, 메시지 변환 구현
    - SessionResumeError 처리
  - [x] 6.2 테스트 작성: sisyphus/agents/tests/test_claude.py
    - Mock을 사용한 초기화/세션 테스트
  - [x] 6.3 테스트 실행: `pytest -xvs sisyphus/agents/tests/test_claude.py`
  - [x] 6.4 린트 및 타입 체크
    - [x] `ruff check sisyphus/agents/claude.py`
    - [x] `basedpyright sisyphus/agents/claude.py`
  - [x] 6.5 커밋: `git add sisyphus/agents/{claude.py,tests/test_claude.py} && git commit -m "feat: implement ClaudeAgent with SDK integration"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] Agent Protocol을 만족하는가? (isinstance 검증)
    - [x] SDK 옵션 오버라이드가 작동하는가?
    - [x] 세션 재개 로직이 구현되었는가?
    - [x] 메시지 변환이 정확한가?
    - [x] 타입 체크와 린트가 통과하는가?

- [x] 7. DroidAgent 구현 (sisyphus/agents/droid.py)
  - [x] 7.1 구현: sisyphus/agents/droid.py 작성
    - 참고: resources/droid-cli-integration.md, utils/process.py
    - 바이너리 자동 탐색 (PATH → --binary → 환경변수)
    - stream-json 모드, UUID 생성
    - autonomy 항상 "skip-permissions-unsafe"
    - ProcessManager 활용 (타임아웃, JSONL 파싱)
    - 에러 처리: 불량 JSONL, 프로세스 조기 종료, 타임아웃
  - [x] 7.2 테스트 작성: sisyphus/agents/tests/test_droid.py
    - Mock 프로세스, JSONL 파싱 에러, 타임아웃 테스트
  - [x] 7.3 테스트 실행: `pytest -xvs sisyphus/agents/tests/test_droid.py`
  - [x] 7.4 린트 및 타입 체크
    - [x] `ruff check sisyphus/agents/droid.py`
    - [x] `basedpyright sisyphus/agents/droid.py`
  - [x] 7.5 커밋: `git add sisyphus/agents/{droid.py,tests/test_droid.py} && git commit -m "feat: implement DroidAgent with stream-json mode"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] Agent Protocol을 만족하는가?
    - [x] 바이너리 자동 탐색이 작동하는가?
    - [x] UUID 생성 및 세션 재개가 구현되었는가?
    - [x] JSONL 파싱 에러가 처리되는가?
    - [x] 타임아웃이 작동하는가?
    - [x] autonomy가 항상 unsafe인가?

- [x] 8. OpenCodeAgent 구현 (sisyphus/agents/opencode.py)
  - [x] 8.1 구현: sisyphus/agents/opencode.py 작성
    - 참고: resources/opencode-integration.md
    - 서버 자동 시작 (opencode serve)
    - 헬스체크 (최대 5회, 2초 간격, /app 엔드포인트)
    - REST API, SSE 스트리밍 (/event)
    - SSE 파싱: httpx.stream + aiter_lines(), "data: " 라인만 처리
    - 에러 처리: 서버 시작 실패, 헬스체크 실패, SSE 파싱 에러
  - [x] 8.2 테스트 작성: sisyphus/agents/tests/test_opencode.py
    - Mock httpx, 서버 헬스체크 실패, SSE 이벤트 누락/깨진 JSON
  - [x] 8.3 테스트 실행: `pytest -xvs sisyphus/agents/tests/test_opencode.py`
  - [x] 8.4 린트 및 타입 체크
    - [x] `ruff check sisyphus/agents/opencode.py`
    - [x] `basedpyright sisyphus/agents/opencode.py`
  - [x] 8.5 커밋: `git add sisyphus/agents/{opencode.py,tests/test_opencode.py} && git commit -m "feat: implement OpenCodeAgent with server auto-start"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] Agent Protocol을 만족하는가?
    - [x] 서버 자동 시작이 작동하는가?
    - [x] 헬스체크 재시도가 구현되었는가?
    - [x] 외부 서버 URL 주입이 가능한가?
    - [x] REST API 호출이 정확한가?
    - [x] SSE 스트리밍이 구현되었는가?
    - [x] SSE 파싱 에러가 처리되는가?

## Phase 4: Core 로직 구현

- [x] 9. PromptResolver 구현 (sisyphus/core/prompts.py)
  - [x] 9.1 구현: sisyphus/core/prompts.py 작성
    - slash-command, plain-text, 파일, 직접 텍스트 지원
    - extra 프롬프트 append 기능
  - [x] 9.2 테스트 작성: sisyphus/core/tests/test_prompts.py
    - 모든 프롬프트 타입 테스트
  - [x] 9.3 테스트 실행: `pytest -xvs sisyphus/core/tests/test_prompts.py`
  - [x] 9.4 린트 및 타입 체크
    - [x] `ruff check sisyphus/core/prompts.py`
    - [x] `basedpyright sisyphus/core/prompts.py`
  - [x] 9.5 커밋: `git add sisyphus/core/{prompts.py,tests/test_prompts.py} && git commit -m "feat: implement PromptResolver with multiple formats"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] 모든 프롬프트 타입이 지원되는가?
    - [x] 파일 읽기가 정확한가?
    - [x] extra 프롬프트 추가가 작동하는가?
    - [x] 테스트가 모든 케이스를 커버하는가?

- [x] 10. SessionStore 구현 (sisyphus/core/session.py)
  - [x] 10.1 구현: sisyphus/core/session.py 작성
    - JSON 파일 기반 저장소
    - 에이전트별 세션 분리
    - 원자적 쓰기 (임시 파일 + rename)
    - 파일 락 (anyio.Lock)
    - 손상 복구 (백업 파일)
    ```python
    import json
    import anyio
    from pathlib import Path
    from typing import Optional
    from datetime import datetime

    class SessionStore:
        """세션 영속성 관리 (파일 락 포함)"""

        def __init__(self, base_dir: Path = Path("./sessions")):
            self.base_dir = base_dir
            self.base_dir.mkdir(exist_ok=True)
            self.sessions_file = self.base_dir / "sessions.json"
            self.lock = anyio.Lock()
            self.sessions = self._load_sessions()

        async def _save_sessions(self) -> None:
            """원자적 저장 (임시 파일 + rename)"""
            # 구현 필요
            pass
    ```
  - [x] 10.2 테스트 작성: sisyphus/core/tests/test_session.py
    - 동시 접근, 손상 복구 테스트
  - [x] 10.3 테스트 실행: `pytest -xvs sisyphus/core/tests/test_session.py`
  - [x] 10.4 린트 및 타입 체크
    - [x] `ruff check sisyphus/core/session.py`
    - [x] `basedpyright sisyphus/core/session.py`
  - [x] 10.5 커밋: `git add sisyphus/core/{session.py,tests/test_session.py} && git commit -m "feat: implement SessionStore with file locking"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] 세션 저장/로드가 작동하는가?
    - [x] 에이전트별 세션 분리가 되는가?
    - [x] 원자적 쓰기가 구현되었는가?
    - [x] 파일 락이 작동하는가?
    - [x] JSON 파일 형식이 올바른가?

- [x] 11. TaskValidator 구현 (sisyphus/core/tasks.py)
  - [x] 11.1 구현: sisyphus/core/tasks.py 작성
    - ai-todolist.md 기반 검증
    - 플래그 및 체크박스 확인
  - [x] 11.2 테스트 작성: sisyphus/core/tests/test_tasks.py
  - [x] 11.3 테스트 실행: `pytest -xvs sisyphus/core/tests/test_tasks.py`
  - [x] 11.4 린트 및 타입 체크
    - [x] `ruff check sisyphus/core/tasks.py`
    - [x] `basedpyright sisyphus/core/tasks.py`
  - [x] 11.5 커밋: `git add sisyphus/core/{tasks.py,tests/test_tasks.py} && git commit -m "feat: implement TaskValidator for todolist"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] 플래그와 체크박스 검증이 작동하는가?
    - [x] 미완료 항목 추출이 정확한가?
    - [x] 정규식이 올바른가?

- [x] 12. ExecutionLoop 구현 (sisyphus/core/loop.py)
  - [x] 12.1 구현: sisyphus/core/loop.py 작성
    - Execute/Verify 페이즈 분리
    - 세션 관리 통합
    - UI Protocol 통합
    - Verify 실패 시 폴백 정책
    - 로깅 통합 (utils/logging.py)
  - [x] 12.2 테스트 작성: sisyphus/core/tests/test_loop.py
    - Execute 성공/실패, Verify 성공/실패, 루프 제어
  - [x] 12.3 테스트 실행: `pytest -xvs sisyphus/core/tests/test_loop.py`
  - [x] 12.4 린트 및 타입 체크
    - [x] `ruff check sisyphus/core/loop.py`
    - [x] `basedpyright sisyphus/core/loop.py`
  - [x] 12.5 커밋: `git add sisyphus/core/{loop.py,tests/test_loop.py} && git commit -m "feat: implement ExecutionLoop with two-phase execution"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] Execute와 Verify 페이즈가 분리되어 있는가?
    - [x] 세션 관리가 올바르게 작동하는가?
    - [x] Verify는 항상 새 세션인가?
    - [x] 루프 제어가 작동하는가?
    - [x] UI Protocol을 통한 출력이 작동하는가?
    - [x] 로깅이 올바르게 작동하는가?

## Phase 5: UI 구현

- [x] 13. CLI UI 구현 (sisyphus/ui/cli/console.py)
  - [x] 13.1 구현: sisyphus/ui/cli/console.py 작성
    - Rich 기반 콘솔 출력
    - 소스별 색상 (execute: yellow, verify: cyan)
  - [x] 13.2 테스트 작성: sisyphus/ui/tests/test_cli.py
  - [x] 13.3 테스트 실행: `pytest -xvs sisyphus/ui/tests/test_cli.py`
  - [x] 13.4 린트 및 타입 체크
    - [x] `ruff check sisyphus/ui/cli/console.py`
    - [x] `basedpyright sisyphus/ui/cli/console.py`
  - [x] 13.5 커밋: `git add sisyphus/ui/cli/ && git commit -m "feat: implement CLI UI with Rich"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] UIProtocol을 만족하는가?
    - [x] Rich 콘솔이 작동하는가?
    - [x] 메시지와 상태 표시가 작동하는가?

- [ ] 14. TUI 기본 구조 및 컴포넌트 구현 (sisyphus/ui/tui/)
  - [x] 14.1 구현: sisyphus/ui/tui/app.py
    - [x] Textual App 기본 구조
    - [x] terminalcp 로 'opencode' 실행해서 ui 구조 살펴보고, 어떻게 구현할지 ultrathink 하고, 또한 그 계획을 notepad.md 에도 적어두기
  - [x] 14.2 구현: sisyphus/ui/tui/components/chat_log.py
  - [x] 14.3 구현: sisyphus/ui/tui/components/status_panel.py
  - [x] 14.4 구현: sisyphus/ui/tui/components/input_bar.py
  - [x] 14.5 구현: sisyphus/ui/tui/layouts/main.py
  - [x] 14.6 테스트 작성: sisyphus/ui/tests/test_tui.py
  - [x] 14.7 테스트 실행: `pytest -xvs sisyphus/ui/tests/test_tui.py`
  - [x] 14.8 린트 및 타입 체크
    - [x] `ruff check sisyphus/ui/tui/`
    - [x] `basedpyright sisyphus/ui/tui/`
  - [x] 14.9 커밋: `git add sisyphus/ui/tui/ && git commit -m "feat: implement TUI with Textual components"`
  - [x] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [x] UIProtocol을 만족하는가?
    - [x] 컴포넌트가 분리되어 있는가?
    - [x] 입력창이 작동하는가?
    - [x] flickering 없이 렌더링되는가?

## Phase 6: CLI 통합

- [ ] 15. Typer CLI 구현 (sisyphus/cli.py)
  - [ ] 15.1 구현: sisyphus/cli.py 작성
    - 모든 CLI 옵션 구현
    - 에이전트 팩토리
    - 프롬프트 resolve
    - 비동기 _main 함수
    - JSON 옵션 파싱 (검증 포함)
    - URL 검증
    - 바이너리 오버라이드 우선순위
  - [ ] 15.2 테스트 작성: CLI 통합 테스트
    - 각 옵션별 단위 테스트
    - JSON 파싱 실패 테스트
  - [ ] 15.3 테스트 실행: `pytest -xvs`
  - [ ] 15.4 린트 및 타입 체크
    - [ ] `ruff check sisyphus/cli.py`
    - [ ] `basedpyright sisyphus/cli.py`
  - [ ] 15.5 커밋: `git add sisyphus/cli.py && git commit -m "feat: implement Typer CLI with all options"`
  - [ ] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [ ] 모든 CLI 옵션이 작동하는가?
    - [ ] 에이전트 팩토리가 작동하는가?
    - [ ] 프롬프트 resolve가 작동하는가?
    - [ ] UI 팩토리가 작동하는가?
    - [ ] JSON 파싱 에러가 처리되는가?

- [ ] 16. 엔트리 포인트 수정 (sisyphus/__main__.py)
  - [ ] 16.1 구현: sisyphus/__main__.py 수정
    - Typer app 실행으로 변경
  - [ ] 16.2 sisyphus/main.py 삭제
  - [ ] 16.3 테스트: `uv run sisyphus --help` 실행 확인
  - [ ] 16.4 커밋: `git add sisyphus/__main__.py && git rm sisyphus/main.py && git commit -m "feat: update entry point to use Typer CLI"`
  - [ ] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [ ] `uv run sisyphus --help`가 작동하는가?
    - [ ] 모든 옵션이 표시되는가?

## Phase 7: 프롬프트 파일 및 문서 작성

- [ ] 17. 기본 프롬프트 파일 작성
  - [ ] 17.1 작성: prompts/execute_command.md
    - agentloop_sdk.py의 DEFAULT_PROMPT 참고
  - [ ] 17.2 작성: prompts/architect_command.md
    - agentloop_sdk.py의 verification_prompt 참고
  - [ ] 17.3 커밋: `git add prompts/ && git commit -m "feat: add default prompt files"`
  - [ ] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [ ] 프롬프트가 명확하고 구체적인가?
    - [ ] 검증 기준이 포함되어 있는가?

- [ ] 18. README 및 문서 작성
  - [ ] 18.1 작성: README.md 업데이트
    - 프로젝트 설명, 설치, 사용 예시
    - 의존성 설치 방법 (uv 없을 시 대안)
    - CLI 옵션 설명
  - [ ] 18.2 커밋: `git add README.md && git commit -m "docs: update README with usage guide"`
  - [ ] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [ ] README가 명확하고 완전한가?

## Phase 8: 통합 테스트 및 검증

- [ ] 19. 전체 통합 테스트
  - [ ] 19.1 테스트: 모든 유닛 테스트 실행
    ```bash
    pytest -xvs
    ```
  - [ ] 19.2 테스트: 전체 린트 및 타입 체크
    ```bash
    ruff check sisyphus/
    basedpyright sisyphus/
    ```
  - [ ] 19.3 수동 테스트: CLI 모드 실행
    ```bash
    uv run sisyphus run --agent claude --no-tui
    ```
  - [ ] 19.4 수동 테스트: TUI 모드 실행
    ```bash
    uv run sisyphus run --agent claude
    ```
  - [ ] 19.5 수동 테스트: Execute + Verify 분리
    ```bash
    uv run sisyphus run --execute claude:sonnet --verify droid:gpt-5 --no-tui
    ```
  - [ ] 19.6 수동 테스트: CLI 옵션 검증
    ```bash
    # JSON 파싱 에러
    uv run sisyphus run --execute-sdk-options '{invalid}'
    # 프롬프트 파일
    uv run sisyphus run --execute-prompt prompts/execute_command.md
    # 바이너리 오버라이드
    uv run sisyphus run --agent droid --binary /custom/path/droid
    ```
  - [ ] 19.7 커밋: `git add . && git commit -m "test: verify all integration tests pass"`
  - [ ] 아래의 가이드대로 진행했을 때 작업 검증 성공 여부
    - [ ] 모든 테스트가 통과하는가?
    - [ ] 린트/타입 체크에 에러가 없는가?
    - [ ] CLI/TUI 모두 작동하는가?
    - [ ] 세션 관리가 작동하는가?
    - [ ] 프롬프트 처리가 올바른가?
    - [ ] CLI 옵션 검증이 작동하는가?
    - [ ] 에러 메시지가 명확한가?

# 최종 작업 검증 체크리스트

- [ ] 1. 기능 검증
  - [ ] Claude, Droid, OpenCode 세 에이전트 모두 작동하는가?
  - [ ] Execute와 Verify를 별개 에이전트로 실행 가능한가?
  - [ ] TUI와 CLI 모드 모두 작동하는가?
  - [ ] 세션 관리 (생성/재개/저장)가 올바르게 작동하는가?
  - [ ] 프롬프트 처리 (slash/plain/file/text)가 모두 작동하는가?
  - [ ] 작업 검증 (todolist)이 작동하는가?
  - [ ] 외부 통합 안정성 (타임아웃, 헬스체크, 에러 처리)이 확보되었는가?

- [ ] 2. 코드 품질 검증
  - [ ] 모든 함수에 타입 힌팅이 있는가?
  - [ ] Protocol을 올바르게 사용했는가?
  - [ ] SOLID 원칙을 준수하는가?
  - [ ] 더블 쿼터를 사용하는가?
  - [ ] 린트와 타입 체크에 에러가 없는가?

- [ ] 3. 테스트 검증
  - [ ] 모든 모듈에 테스트가 있는가?
  - [ ] 테스트가 모두 통과하는가?
  - [ ] 엣지 케이스를 커버하는가? (타임아웃, JSONL 에러, SSE 파싱, 동시 접근)

- [ ] 4. 안정성 검증
  - [ ] 타임아웃이 모든 외부 통합에 적용되었는가?
  - [ ] 프로세스 정리가 올바른가? (SIGTERM → SIGKILL)
  - [ ] 파일 락이 작동하는가?
  - [ ] 원자적 쓰기가 구현되었는가?
  - [ ] 헬스체크 재시도가 작동하는가?

- [ ] 5. 확장성 검증
  - [ ] 새 에이전트 추가가 간단한가? (기존 코드 수정 불필요)
  - [ ] 새 UI 모드 추가가 간단한가?
  - [ ] 새 프롬프트 타입 추가가 간단한가?

- [ ] 6. 실용성 검증
  - [ ] 사용자 경험이 직관적인가?
  - [ ] CLI 옵션이 명확한가?
  - [ ] 에러 메시지가 도움이 되는가?
  - [ ] 로깅이 충분한가?
  - [ ] 문서가 완전한가? (README, 의존성 설치 방법)

# Notepad

[2025-10-09 17:59] - Task 9: PromptResolver 구현

### DISCOVERED ISSUES
- None

### IMPLEMENTATION DECISIONS
- 파일 경로 체크를 slash command 체크보다 먼저 수행: 절대 경로(`/path/to/file`)가 slash command로 오인되는 것 방지
- Slash command를 단일 단어로 제한: `"/" not in prompt_str[1:]` 조건으로 `/execute`는 허용, `/path/to/file`은 제외
- PathLike를 str로 변환하여 통일된 처리 로직 구현
- extra append 시 `\n\n` 구분자 사용

### PROBLEMS FOR NEXT TASKS
- None

### VERIFICATION RESULTS
- 테스트: 20 tests passed (10 test cases × 2 backends: asyncio + trio)
- 린트: ruff check 통과
- 타입 체크: basedpyright 0 errors
- 커버리지: slash command, file path, plain text, extra append, error cases 모두 포함

### LEARNINGS
- 절대 경로와 slash command 구분 필요: 파일 존재 여부 체크 우선, 그 다음 slash command 패턴 확인
- Slash command는 단일 단어만 허용하여 파일 경로와 명확히 구분

소요 시간: 약 5분
