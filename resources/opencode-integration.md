# OpenCode Integration Guide

## Overview
OpenCode는 SST에서 개발한 AI 코딩 어시스턴트로, 서버 모드와 REST API를 통한 프로그래머틱 통합을 지원합니다.

## 설치 및 기본 정보

### 설치 경로
```bash
/Users/yeongyu/.bun/bin/opencode
```

### 기본 사용법
```bash
# TUI 모드 (기본)
opencode

# 특정 프로젝트에서 시작
opencode /path/to/project

# 비대화형 실행
opencode run "analyze this code"

# 서버 모드 시작 (headless)
opencode serve --port 4096 --hostname 127.0.0.1

# 세션 내보내기
opencode export [sessionID]
```

## 서버 모드 상세

### 1. 서버 시작

#### 명령어
```bash
opencode serve [options]
```

#### 옵션
- `-p, --port`: 리스닝 포트 (기본: 0 = 랜덤 포트)
- `-h, --hostname`: 호스트명 (기본: "127.0.0.1")
- `--print-logs`: stderr로 로그 출력
- `--log-level`: 로그 레벨 (DEBUG, INFO, WARN, ERROR)

#### 예시
```bash
# 프로덕션 서버
opencode serve --port 4096 --hostname 0.0.0.0 --log-level INFO

# 개발 서버 (디버그 모드)
opencode serve --port 4096 --print-logs --log-level DEBUG
```

## REST API 상세 명세

### 1. 앱 관련 엔드포인트

#### GET /app
- **설명**: 앱 정보 조회
- **응답**: `App` 객체
```json
{
  "name": "opencode",
  "version": "x.x.x",
  "status": "ready"
}
```

#### POST /app/init
- **설명**: 앱 초기화
- **응답**: `boolean`
```bash
curl -X POST http://localhost:4096/app/init
```

### 2. 설정 관련 엔드포인트

#### GET /config
- **설명**: 설정 정보 조회
- **응답**: `Config` 객체
```json
{
  "models": {...},
  "providers": [...],
  "session": {
    "auto_save": true,
    "history_limit": 100,
    "database_path": "~/.opencode/sessions.db"
  }
}
```

#### GET /config/providers
- **설명**: 프로바이더와 기본 모델 목록
- **응답**:
```json
{
  "providers": [
    {
      "id": "openai",
      "name": "OpenAI",
      "models": ["gpt-4", "gpt-3.5-turbo"],
      "authenticated": true
    },
    {
      "id": "anthropic",
      "name": "Anthropic",
      "models": ["claude-3-opus", "claude-3-sonnet"],
      "authenticated": false
    }
  ],
  "default": {
    "openai": "gpt-4",
    "anthropic": "claude-3-opus"
  }
}
```

### 3. 인증 관련 엔드포인트

#### PUT /auth/:id
- **설명**: 프로바이더 인증 설정
- **파라미터**: `:id` - 프로바이더 ID
- **요청 본문**: 프로바이더별 스키마
- **응답**: `boolean`

##### OpenAI 인증 예시
```bash
curl -X PUT http://localhost:4096/auth/openai \
  -H "Content-Type: application/json" \
  -d '{"apiKey": "sk-..."}'
```

##### Anthropic 인증 예시
```bash
curl -X PUT http://localhost:4096/auth/anthropic \
  -H "Content-Type: application/json" \
  -d '{"apiKey": "sk-ant-..."}'
```

### 4. 세션 관리 엔드포인트 (추정)

#### POST /session
- **설명**: 새 세션 생성
- **요청 본문**:
```json
{
  "model": "gpt-4",
  "agent": "default",
  "prompt": "Initial prompt"
}
```
- **응답**:
```json
{
  "id": "session-123",
  "created_at": "2025-10-09T05:00:00Z",
  "model": "gpt-4",
  "status": "active"
}
```

#### GET /session
- **설명**: 세션 목록 조회
- **응답**:
```json
[
  {
    "id": "session-123",
    "created_at": "2025-10-09T05:00:00Z",
    "last_active": "2025-10-09T05:30:00Z",
    "model": "gpt-4",
    "status": "active",
    "message_count": 15
  }
]
```

#### GET /session/:id
- **설명**: 특정 세션 재개/조회
- **파라미터**: `:id` - 세션 ID
- **응답**: 세션 상세 정보 및 메시지 히스토리

#### DELETE /session/:id
- **설명**: 세션 삭제
- **파라미터**: `:id` - 세션 ID
- **응답**: `boolean`

#### POST /session/:id/message
- **설명**: 세션에 메시지 전송
- **파라미터**: `:id` - 세션 ID
- **요청 본문**:
```json
{
  "content": "User message",
  "role": "user"
}
```

### 5. 이벤트 스트리밍 (SSE)

#### GET /event
- **설명**: Server-Sent Events 스트림
- **프로토콜**: SSE (Server-Sent Events)
- **응답 형식**:

##### 초기 연결 이벤트
```
event: server.connected
data: {"timestamp": "2025-10-09T05:13:37Z", "session_id": "current-session"}
```

##### 메시지 이벤트
```
event: message.start
data: {"id": "msg-1", "role": "assistant", "timestamp": "2025-10-09T05:13:38Z"}

event: message.chunk
data: {"id": "msg-1", "content": "Hello, ", "index": 0}

event: message.chunk
data: {"id": "msg-1", "content": "how can I help?", "index": 1}

event: message.end
data: {"id": "msg-1", "tokens": 5, "duration_ms": 234}
```

##### 도구 사용 이벤트
```
event: tool.start
data: {"id": "tool-1", "name": "read_file", "args": {"path": "/src/main.py"}}

event: tool.result
data: {"id": "tool-1", "success": true, "result": "file content..."}

event: tool.end
data: {"id": "tool-1", "duration_ms": 45}
```

##### 에러 이벤트
```
event: error
data: {"code": "RATE_LIMIT", "message": "Rate limit exceeded", "retry_after": 60}
```

### 6. TUI 제어 엔드포인트

#### GET /tui
- **설명**: TUI 제어를 위한 프로그래머틱 인터페이스
- **쿼리 파라미터**:
  - `prompt`: 초기 프롬프트
  - `model`: 사용할 모델
  - `session`: 재개할 세션 ID
- **용도**: IDE 플러그인에서 TUI 미리 채우기

### 7. OpenAPI 명세

#### GET /doc
- **설명**: OpenAPI 3.1 명세서
- **응답**: HTML 페이지 또는 JSON 스키마
- **용도**: 자동 클라이언트 생성

## CLI 옵션 상세

### opencode run 명령어

#### 기본 사용법
```bash
opencode run [message..] [options]
```

#### 주요 옵션
- `-c, --continue`: 마지막 세션 계속
- `-s, --session <id>`: 특정 세션 ID로 계속
- `-m, --model <provider/model>`: 모델 지정
- `--agent <name>`: 에이전트 지정
- `--format <default|json>`: 출력 형식
- `--share`: 세션 공유
- `--command <cmd>`: 실행할 명령 (메시지는 인자로)

#### 예시
```bash
# 단순 실행
opencode run "analyze this file"

# 이전 세션 계속
opencode run -c "continue the previous work"

# 특정 모델 사용
opencode run -m openai/gpt-4 "complex task"

# JSON 출력
opencode run --format json "get project structure"
```

## Python SDK 구현

### 기본 구조
```python
import httpx
import asyncio
import json
from typing import AsyncIterator, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class OpenCodeProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GROQ = "groq"
    BEDROCK = "bedrock"

@dataclass
class OpenCodeSession:
    id: Optional[str] = None
    model: Optional[str] = None
    agent: str = "default"
    created_at: Optional[datetime] = None
    status: str = "pending"
```

### 비동기 SDK 구현
```python
class OpenCodeSDK:
    def __init__(self, base_url: str = "http://localhost:4096", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {}
        )
        self.sse_client = None

    # === 앱 관리 ===
    async def get_app_info(self) -> Dict[str, Any]:
        """앱 정보 조회"""
        response = await self.client.get("/app")
        response.raise_for_status()
        return response.json()

    async def init_app(self) -> bool:
        """앱 초기화"""
        response = await self.client.post("/app/init")
        response.raise_for_status()
        return response.json()

    # === 설정 관리 ===
    async def get_config(self) -> Dict[str, Any]:
        """설정 조회"""
        response = await self.client.get("/config")
        response.raise_for_status()
        return response.json()

    async def get_providers(self) -> Dict[str, Any]:
        """프로바이더 목록 조회"""
        response = await self.client.get("/config/providers")
        response.raise_for_status()
        return response.json()

    # === 인증 관리 ===
    async def set_auth(self, provider: str, credentials: Dict[str, str]) -> bool:
        """프로바이더 인증 설정"""
        response = await self.client.put(f"/auth/{provider}", json=credentials)
        response.raise_for_status()
        return response.json()

    # === 세션 관리 ===
    async def create_session(
        self,
        model: Optional[str] = None,
        agent: str = "default",
        prompt: Optional[str] = None
    ) -> OpenCodeSession:
        """새 세션 생성"""
        payload = {
            "model": model,
            "agent": agent,
            "prompt": prompt
        }
        response = await self.client.post("/session", json=payload)
        response.raise_for_status()
        data = response.json()
        return OpenCodeSession(
            id=data["id"],
            model=data.get("model"),
            agent=data.get("agent", "default"),
            created_at=datetime.fromisoformat(data["created_at"]),
            status=data["status"]
        )

    async def list_sessions(self) -> list[OpenCodeSession]:
        """세션 목록 조회"""
        response = await self.client.get("/session")
        response.raise_for_status()
        sessions = []
        for item in response.json():
            sessions.append(OpenCodeSession(
                id=item["id"],
                model=item.get("model"),
                agent=item.get("agent", "default"),
                created_at=datetime.fromisoformat(item["created_at"]),
                status=item["status"]
            ))
        return sessions

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """특정 세션 조회"""
        response = await self.client.get(f"/session/{session_id}")
        response.raise_for_status()
        return response.json()

    async def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        response = await self.client.delete(f"/session/{session_id}")
        response.raise_for_status()
        return response.json()

    async def send_message(self, session_id: str, content: str, role: str = "user") -> Dict[str, Any]:
        """세션에 메시지 전송"""
        payload = {
            "content": content,
            "role": role
        }
        response = await self.client.post(f"/session/{session_id}/message", json=payload)
        response.raise_for_status()
        return response.json()

    # === 이벤트 스트리밍 (SSE) ===
    async def stream_events(self) -> AsyncIterator[Dict[str, Any]]:
        """서버 이벤트 스트리밍"""
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', f"{self.base_url}/event") as response:
                async for line in response.aiter_lines():
                    if line.startswith('event: '):
                        event_type = line[7:].strip()
                    elif line.startswith('data: '):
                        data = json.loads(line[6:])
                        yield {
                            "event": event_type,
                            "data": data
                        }

    # === 고급 스트리밍 응답 ===
    async def with_streaming_response(self, session_id: str) -> AsyncIterator[str]:
        """스트리밍 응답과 함께 세션 처리"""
        # SDK 문서에서 언급된 기능
        url = f"{self.base_url}/session/{session_id}/stream"
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', url) as response:
                async for line in response.aiter_lines():
                    yield line

    # === 헬퍼 메서드 ===
    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()

    async def health_check(self) -> bool:
        """서버 상태 확인"""
        try:
            response = await self.client.get("/app")
            return response.status_code == 200
        except Exception:
            return False
```

### 사용 예시

#### 기본 사용
```python
async def basic_usage():
    sdk = OpenCodeSDK()

    # 앱 초기화
    await sdk.init_app()

    # 프로바이더 인증
    await sdk.set_auth("openai", {"apiKey": "sk-..."})

    # 세션 생성
    session = await sdk.create_session(
        model="openai/gpt-4",
        prompt="Help me refactor this code"
    )

    # 메시지 전송
    response = await sdk.send_message(
        session.id,
        "Let's start with the main.py file"
    )

    print(response)

    # 클라이언트 종료
    await sdk.close()
```

#### 이벤트 스트리밍
```python
async def streaming_example():
    sdk = OpenCodeSDK()

    # 세션 생성
    session = await sdk.create_session()

    # 이벤트 스트리밍 시작
    async for event in sdk.stream_events():
        event_type = event["event"]
        data = event["data"]

        if event_type == "message.chunk":
            print(data["content"], end="", flush=True)
        elif event_type == "message.end":
            print("\n[Message completed]")
        elif event_type == "tool.start":
            print(f"\n[Tool: {data['name']}]")
        elif event_type == "error":
            print(f"\n[Error: {data['message']}]")
```

#### 세션 관리
```python
async def session_management():
    sdk = OpenCodeSDK()

    # 모든 세션 조회
    sessions = await sdk.list_sessions()
    for session in sessions:
        print(f"Session {session.id}: {session.status}")

    # 특정 세션 재개
    if sessions:
        last_session = sessions[-1]
        session_data = await sdk.get_session(last_session.id)
        print(f"Resuming session with {len(session_data.get('messages', []))} messages")

        # 계속 대화
        await sdk.send_message(last_session.id, "Continue from where we left off")
```

## MCP (Model Context Protocol) 통합

### MCP 서버 설정
OpenCode는 Model Context Protocol을 지원하여 외부 도구와 통합됩니다.

#### 설정 구조
```yaml
mcp_servers:
  - name: "filesystem"
    type: "stdio"  # or "sse"
    command: "mcp-server-filesystem"
    args: ["--root", "/workspace"]
    env:
      MCP_DEBUG: "true"

  - name: "github"
    type: "sse"
    url: "http://localhost:5000/events"
    headers:
      Authorization: "Bearer token"
```

#### 통신 타입
- **stdio**: 동기식 표준 입출력 통신
- **sse**: Server-Sent Events를 통한 스트리밍

### 권한 모델
```json
{
  "permissions": {
    "allowed_commands": ["ls", "cat", "grep"],
    "blocked_commands": ["rm", "sudo"],
    "require_confirmation": ["git push", "npm publish"]
  }
}
```

## 세션 영속성

### SQLite 데이터베이스
- 위치: `~/.opencode/sessions.db`
- 스키마:
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    last_active TIMESTAMP,
    model TEXT,
    agent TEXT,
    status TEXT,
    messages JSON,
    metadata JSON
);
```

### 자동 저장 설정
```yaml
session:
  auto_save: true
  save_interval: 30  # seconds
  history_limit: 1000  # messages
  cleanup_after: 30  # days
```

## 에러 처리

### HTTP 상태 코드
- `200 OK`: 성공
- `201 Created`: 리소스 생성 성공
- `400 Bad Request`: 잘못된 요청
- `401 Unauthorized`: 인증 필요
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 리소스 없음
- `429 Too Many Requests`: 속도 제한
- `500 Internal Server Error`: 서버 오류

### 에러 응답 형식
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": {
      "limit": 100,
      "remaining": 0,
      "reset_at": "2025-10-09T06:00:00Z"
    }
  }
}
```

## 성능 최적화

### 연결 풀링
```python
class OptimizedOpenCodeSDK:
    def __init__(self, base_url: str = "http://localhost:4096"):
        self.base_url = base_url
        # 연결 풀 설정
        self.client = httpx.AsyncClient(
            base_url=base_url,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30
            ),
            timeout=httpx.Timeout(30.0, connect=5.0)
        )
```

### 배치 처리
```python
async def batch_messages(sdk: OpenCodeSDK, session_id: str, messages: list[str]):
    """여러 메시지를 효율적으로 처리"""
    tasks = []
    for msg in messages:
        task = sdk.send_message(session_id, msg)
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results
```

### 캐싱
```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_cached_session_data(session_id: str):
    """세션 데이터 캐싱"""
    return await sdk.get_session(session_id)
```

## 보안 고려사항

### API 키 관리
```python
import os
from pathlib import Path

def get_api_key():
    # 1. 환경 변수 확인
    if key := os.getenv("OPENCODE_API_KEY"):
        return key

    # 2. 설정 파일 확인
    config_path = Path.home() / ".opencode" / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            return config.get("apiKey")

    # 3. 키체인/시크릿 매니저 사용
    # ... implementation
```

### HTTPS 사용
```python
sdk = OpenCodeSDK(
    base_url="https://api.opencode.ai",
    api_key=get_api_key()
)
```

### 입력 검증
```python
def validate_session_id(session_id: str) -> bool:
    """세션 ID 형식 검증"""
    import re
    # 알파벳, 숫자, 하이픈만 허용
    pattern = r"^[a-zA-Z0-9-]+$"
    return bool(re.match(pattern, session_id))
```

## 디버깅 및 모니터링

### 로깅 설정
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("opencode_sdk")
```

### 요청/응답 로깅
```python
class DebugOpenCodeSDK(OpenCodeSDK):
    async def _log_request(self, method: str, url: str, **kwargs):
        logger.debug(f"Request: {method} {url}")
        logger.debug(f"Headers: {kwargs.get('headers', {})}")
        logger.debug(f"Body: {kwargs.get('json', {})}")

    async def _log_response(self, response: httpx.Response):
        logger.debug(f"Response: {response.status_code}")
        logger.debug(f"Headers: {dict(response.headers)}")
        try:
            logger.debug(f"Body: {response.json()}")
        except:
            logger.debug(f"Body: {response.text[:200]}")
```

### 메트릭 수집
```python
from dataclasses import dataclass
from time import time

@dataclass
class Metrics:
    request_count: int = 0
    error_count: int = 0
    total_latency: float = 0.0

    def record_request(self, latency: float, error: bool = False):
        self.request_count += 1
        self.total_latency += latency
        if error:
            self.error_count += 1

    @property
    def average_latency(self):
        if self.request_count == 0:
            return 0
        return self.total_latency / self.request_count
```

## 마이그레이션 가이드

### CLI에서 SDK로 마이그레이션
```python
# Before (CLI)
# opencode run "analyze code" --model gpt-4

# After (SDK)
async def migrate_from_cli():
    sdk = OpenCodeSDK()
    session = await sdk.create_session(model="openai/gpt-4")
    response = await sdk.send_message(session.id, "analyze code")
```

### 다른 AI SDK에서 마이그레이션
```python
# OpenAI SDK에서 마이그레이션
# Before
import openai
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

# After
sdk = OpenCodeSDK()
await sdk.set_auth("openai", {"apiKey": openai.api_key})
session = await sdk.create_session(model="openai/gpt-4")
response = await sdk.send_message(session.id, "Hello")
```