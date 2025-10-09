# Droid CLI Integration Guide

## Overview
Droid는 Factory AI의 터미널 기반 AI 코딩 에이전트로, 프로그래머틱 통합을 위한 다양한 옵션을 제공합니다.

## 설치 및 기본 정보

### 설치 경로
```bash
/Users/yeongyu/.local/bin/droid
```

### 기본 사용법
```bash
# 대화형 모드 (기본)
droid

# 초기 프롬프트와 함께 대화형 모드 시작
droid "review app.tsx"

# 비대화형 실행 (스크립트/자동화용)
droid exec "analyze this file"

# 표준 입력으로부터 실행
droid exec - < prompt.txt
```

## 프로그래머틱 통합을 위한 핵심 기능

### 1. Stream JSON 모드

#### 개요
`--input-format stream-json` 및 `--output-format stream-json` 옵션을 사용하여 JSONL(JSON Lines) 형식으로 통신할 수 있습니다.

#### 사용 예시
```bash
droid exec --input-format stream-json --output-format stream-json --auto low
```

#### 입력 형식
```json
{"role":"user","content":"hello"}
{"role":"user","content":"what can you do?"}
```

#### 특징
- 다중 턴 대화 지원
- 표준 입출력을 통한 비동기 통신
- Ctrl+C 또는 Ctrl+D로 정상 종료

### 2. 세션 관리

#### 세션 ID 옵션
```bash
# 기존 세션 계속하기 (프롬프트 필요)
droid exec -s <session-id> "continue the work"

# UUID 형식 검증
# 형식: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

#### 세션 특징
- UUID 형식의 세션 ID 사용
- 세션 재개 시 새 프롬프트 필수
- 세션 ID는 클라이언트가 관리

### 3. 자율성 레벨 (Autonomy Levels)

#### DEFAULT (플래그 없음) - 읽기 전용 모드
- 파일 읽기: `cat`, `less`, `head`, `tail`
- 정보 수집: `ls`, `find`, `git status`, `git log`, `git diff`
- 시스템 정보: `pwd`, `date`, `uname`, `ps`, `top`
- ❌ 파일이나 시스템 수정 불가

#### --auto low - 저위험 작업
- 파일 생성/수정 (비시스템 디렉토리)
- `touch`, `mkdir`, `mv`, `cp` 허용
- ❌ 시스템 수정이나 패키지 설치 불가

#### --auto medium - 개발 작업
- 패키지 설치: `npm install`, `pip install` (sudo 없이)
- 네트워크 요청: 신뢰할 수 있는 엔드포인트
- Git 작업 (로컬): `git commit`, `git checkout`, `git pull`
- 빌드: `make`, `npm run build`, `mvn compile`
- ❌ `git push`, `sudo` 명령, 프로덕션 변경 불가

#### --auto high - 프로덕션 작업
- 임의 코드 실행: `curl | bash`, `eval`
- 포트 노출 및 방화벽 규칙 수정
- Git push 작업: `git push`, `git push --force`
- 프로덕션 배포, DB 마이그레이션
- ❌ 여전히 `sudo rm -rf /` 같은 시스템 전체 변경은 차단

#### --skip-permissions-unsafe - 모든 검사 우회
- ⚠️ 위험: 모든 작업 확인 없이 허용
- 되돌릴 수 없는 작업 실행 가능
- 격리된 환경(Docker, 일회용 VM)에서만 사용
- ❌ --auto 플래그와 함께 사용 불가

### 4. 모델 선택

#### 사용 가능한 모델
```bash
# 기본 모델
gpt-5-codex (OpenAI GPT-5-Codex Auto)

# 다른 모델들
claude-opus-4-1-20250805     # Claude Opus 4.1
claude-sonnet-4-20250514      # Claude Sonnet 4
gpt-5-2025-08-07              # OpenAI GPT-5
claude-sonnet-4-5-20250929    # Claude Sonnet 4.5
```

#### 모델별 추론(Reasoning) 지원
- **Claude 모델들**: `off`, `low`, `medium`, `high` 지원 (기본: off)
- **GPT-5**: `low`, `medium`, `high` 지원 (기본: medium)
- **GPT-5-Codex**: 추론 미지원

#### 사용 예시
```bash
droid exec --model claude-opus-4-1-20250805 --reasoning-effort high "complex task"
```

### 5. 도구(Tools) 제어

#### 도구 관련 옵션
```bash
# 사용 가능한 도구 목록 출력
droid exec --list-tools
droid exec --model gpt-5 --list-tools --output-format json

# 특정 도구 활성화
droid exec --enabled-tools ApplyPatch "refactor files"

# 특정 도구 비활성화
droid exec --auto medium --disabled-tools execute-cli "make edits only"
```

### 6. 기타 옵션

#### 작업 디렉토리
```bash
droid exec --cwd /path/to/project "analyze code"
```

#### 파일 입력
```bash
# 파일에서 프롬프트 읽기
droid exec -f requirements.md

# 파일 입력 + 자율성 레벨
droid exec -f task.md --auto medium
```

#### 출력 형식
```bash
# 텍스트 형식 (기본)
droid exec -o text "task"

# JSON 형식
droid exec -o json "task"
```

## Python 통합 구현 예시

### 기본 구조
```python
import asyncio
import json
import subprocess
from typing import AsyncIterator, Optional
from dataclasses import dataclass
from enum import Enum

class DroidAutonomyLevel(Enum):
    READ_ONLY = None  # 플래그 없음
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNSAFE = "skip-permissions-unsafe"

class DroidModel(Enum):
    GPT5_CODEX = "gpt-5-codex"
    CLAUDE_OPUS_41 = "claude-opus-4-1-20250805"
    CLAUDE_SONNET_4 = "claude-sonnet-4-20250514"
    GPT5 = "gpt-5-2025-08-07"
    CLAUDE_SONNET_45 = "claude-sonnet-4-5-20250929"

@dataclass
class DroidSession:
    id: Optional[str] = None
    model: DroidModel = DroidModel.GPT5_CODEX
    autonomy: DroidAutonomyLevel = DroidAutonomyLevel.LOW
    reasoning: Optional[str] = None
    cwd: Optional[str] = None
```

### 비동기 SDK 구현
```python
class DroidSDK:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FACTORY_API_KEY")
        self.process: Optional[asyncio.subprocess.Process] = None

    async def start_session(
        self,
        session: DroidSession,
        stream_mode: bool = True
    ) -> None:
        """새 세션 시작 또는 기존 세션 재개"""
        cmd = ["droid", "exec"]

        if stream_mode:
            cmd.extend(["--input-format", "stream-json"])
            cmd.extend(["--output-format", "stream-json"])

        if session.id:
            cmd.extend(["--session-id", session.id])

        if session.model:
            cmd.extend(["--model", session.model.value])

        if session.autonomy:
            if session.autonomy == DroidAutonomyLevel.UNSAFE:
                cmd.append("--skip-permissions-unsafe")
            elif session.autonomy.value:
                cmd.extend(["--auto", session.autonomy.value])

        if session.reasoning:
            cmd.extend(["--reasoning-effort", session.reasoning])

        if session.cwd:
            cmd.extend(["--cwd", session.cwd])

        # 환경 변수 설정
        env = os.environ.copy()
        if self.api_key:
            env["FACTORY_API_KEY"] = self.api_key

        # 프로세스 시작
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )

    async def send_message(self, content: str, role: str = "user") -> None:
        """메시지 전송"""
        if not self.process or not self.process.stdin:
            raise RuntimeError("Session not started")

        message = json.dumps({"role": role, "content": content})
        self.process.stdin.write(message.encode() + b'\n')
        await self.process.stdin.drain()

    async def receive_messages(self) -> AsyncIterator[dict]:
        """응답 스트리밍"""
        if not self.process or not self.process.stdout:
            raise RuntimeError("Session not started")

        while True:
            line = await self.process.stdout.readline()
            if not line:
                break

            try:
                data = json.loads(line.decode().strip())
                yield data
            except json.JSONDecodeError:
                # 디버깅용 로그
                print(f"Failed to parse: {line}")
                continue

    async def close(self) -> None:
        """세션 종료"""
        if self.process:
            if self.process.stdin and not self.process.stdin.is_closing():
                self.process.stdin.close()
                await self.process.stdin.wait_closed()

            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.terminate()
                await self.process.wait()
```

### 사용 예시
```python
async def main():
    # SDK 초기화
    sdk = DroidSDK()

    # 세션 설정
    session = DroidSession(
        model=DroidModel.CLAUDE_OPUS_41,
        autonomy=DroidAutonomyLevel.MEDIUM,
        reasoning="high",
        cwd="/path/to/project"
    )

    # 세션 시작
    await sdk.start_session(session)

    # 메시지 전송
    await sdk.send_message("Analyze the project structure and create a summary")

    # 응답 수신
    async for message in sdk.receive_messages():
        print(json.dumps(message, indent=2))

    # 세션 종료
    await sdk.close()

# 실행
asyncio.run(main())
```

## 고려사항 및 제한사항

### 1. 타임아웃 처리
- Stream JSON 모드에서 응답 대기 시 타임아웃 발생 가능
- 적절한 타임아웃 설정 필요

### 2. 에러 처리
- 프로세스 실패
- API 키 인증 실패
- 세션 ID 형식 오류
- 네트워크 문제

### 3. 리소스 관리
- 프로세스 정리
- 스트림 닫기
- 메모리 관리

### 4. 보안 고려사항
- API 키 안전한 저장
- 자율성 레벨 적절한 설정
- 격리된 환경에서 테스트

## 디버깅 팁

### 로그 확인
```bash
# stderr로 로그 출력 확인
droid exec --auto low "task" 2> droid_error.log
```

### 프로세스 모니터링
```bash
# 프로세스 상태 확인
ps aux | grep droid

# 네트워크 활동 모니터링
netstat -an | grep ESTABLISHED
```

### 일반적인 문제 해결
1. **API 키 오류**: 환경 변수 확인
2. **세션 재개 실패**: UUID 형식 확인
3. **권한 오류**: 자율성 레벨 조정
4. **타임아웃**: 작업 복잡도에 따라 타임아웃 증가