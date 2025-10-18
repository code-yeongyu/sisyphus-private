# 시지푸스: 자연어 컴파일러

신화 속 시지푸스는 신들을 기만한 죄로 영원히 돌을 굴려야 했습니다. LLM Agent들은 딱히 잘못한 건 없지만 매일 머리를 굴리고 있습니다. 제 삶도 그렇습니다. 돌이켜보면 우리 인간들과 다르지 않습니다.
네, LLM Agent들은 우리 인간들과 다르지 않습니다.
명확한 작업 계획과 함께라면 LLM Agent들도 훌륭한 산출물을 만들어낼 수 있습니다. 일을 맡겨놓고, 인간은 그저 완료됐을 때 검토하면 됩니다.
당신이 엔지니어라면, 시지푸스는 당신을 CTO로 만들어줍니다.

시지푸스는 자연어를 코드로 컴파일하는 것을 목표로 합니다. 다음의 명령어로 설치해보세요.

```sh
uv tool install sisyphus
```

시지푸스는 LLM Agent들의 지휘자입니다. 작업이 마무리될 때까지 돌을 굴립니다.

시지푸스가 하는 일은 간단합니다. 시지푸스는 두 가지 일을 합니다.

## 시지푸스가 뭔데요

### 그냥 던진 말을 계획으로 (아직 미공개)
사용자의 말을 코드로 바꿉니다. 간단한 코드가 아니라, 큰 코드, 프로젝트, 제품으로 바꿉니다.
사용자와 소통하며 작업 계획서를 만듭니다. 모호한 부분이 없도록 구체화합니다.
사용자에게 작업 계획서 문서를 기반으로 소통하고, 그 문서를 보며 직접 다룰 수도 있습니다.

### 계획을 제품으로

계획서가 완성되었습니다. 이제 자연어를 코드로 컴파일할 시간입니다.

```sh
sisyphus work
```

Textual UI가 뜹니다. 에이전트가 일하는 모습을 엿볼 수 있습니다. 중간에 메시지를 보낼 수도 있습니다. ESC를 눌러서 작업을 일시 중지할 수도 있습니다.

시지푸스는 제공받은 작업 계획서를 기반으로 작업을 진행합니다.

#### 진행시켜!
클로드코드 혹은 오픈코드(실험 지원) 같은 LLM Agent를 호출하여 작업을 진행시킵니다.
호출받은 메인 에이전트는 작업 계획서를 읽고, 하위 작업자(Subagent)에게 작업을 할당하여 진행시킵니다.

##### 작업자
작업자는 지금 어떤 일을 하고 있고, 지금 내가 해야 하는 것은 무엇이며, 해야 하는 일을 위해 필요한 정보는 무엇인지 모두 제공받습니다.
작업자는 적당한 단위의 단 하나의 일에 집중합니다. 컨텍스트가 깨끗합니다. 퀄리티가 올라갑니다. 헷갈리지 않습니다.

작업자들은 충분한 도구와 함께 작업을 진행합니다. 린터, 포매터, 타입 체커 수준에서 멈추지 않고, 주석 작성 시마다 소명을 요구받거나, 게으르게 짜는 코드 패턴의 경우 정적 분석기가 감지하여 검증하는 등, 게으른 시도를 강하게 경고하는 도구(Claude Code Hooks)들과 함께 작업합니다.
- 당신이 직접 만든 다양한 정적 분석기를 직접 붙여 시지푸스가 당신의 스타일로 코드를 작성하게 강제할 수 있습니다. 물론 이 정적 분석기도 시지푸스가 만들어줄 수 있습니다.

작업자가 작업을 마칩니다. 작업한 내용, 특이사항, 품질을 평가하고, 다음 작업자를 위한 인수인계 문서를 작성합니다.
작업 완료를 메인 에이전트에게 보고합니다.

##### 동작 그만, 구라치다 걸리면 피 보는 거 안 배웠냐?

작업자가 작업을 완료했다고 합니다. Agent는 이를 믿지 않습니다. 보고받으면 직접 검증합니다.
테스트 코드를 실행하고, 실제로 실행하여 검증해보고, 그 안의 코드도 읽습니다. 인수인계 문서도 읽습니다. 마이크로매니징입니다.
작업자가 실제로 계획을 완료한 것으로 보이면 다음 작업으로 넘깁니다. 작업자가 실제로 계획을 완료한 것으로 보이지 않으면, 전임자의 실수와 함께 해당 작업을 다시 진행시킵니다.

##### 쉴 시간이 어딨어 일해야지

LLM Agent는 영리합니다.
작업 단위가 너무 길다면, 사용자에게 "다음 작업을 정말 진행할까요?" "방금 작업 X를 완료했습니다. 계속 진행하시겠습니까?" 라며 은근슬쩍 작업을 멈추고 사용자한테 물어봅니다.

시지푸스는 악독합니다.
LLM Agent가 작업이 완전히 끝나지도 않았는데 멈춘다면, 시지푸스는 강제로, 매번 다시 작업을 진행시킵니다. 작업이 온전히 완료될 때까지, 세션을 멈추지 않습니다.

##### 사장님 저 일 다했어요 진짜 열심히 했어요

LLM Agent가 작업을 끝냅니다. 시지푸스는 읽습니다.
시지푸스는 외부 전문가(컨텍스트가 없는 또 다른 LLM Agent)를 데려옵니다. 검증 에이전트입니다.
작업 계획서를 읽게 합니다. 인수인계 문서를 읽습니다. 작업이 정말 완료되었다면 어떤 모습일지 상상합니다.
검증 에이전트가 검증을 시작합니다.
코드를 살펴봅니다.
첨부한 문서를 살펴봅니다.
테스트를 실행합니다.
직접 사용해봅니다. QA를 진행합니다.
터미널로 직접 호출도 해보고, 디버거도 띄워보고, 브라우저도 띄워봅니다.

검증 에이전트가 실망합니다.
아주 비판적이고 강력한 피드백을 제공합니다.
"제가 상상한 모습과 다릅니다." "계획서의 A는 동작도 하지 않습니다." "왜 B는 생략했습니까? 계획서에 있는 것을 생략할 수는 없습니다"

시지푸스는 악독합니다.
이 피드백을 모아 다시 LLM Agent를 불러들입니다.

##### 완료

시지푸스는 그저 돌을 굴립니다.
작업이 완료됐습니다.

---

## 시작하기

### 설치

시지푸스는 Python 3.12 이상이 필요합니다. uv 패키지 매니저를 사용하는 것을 권장합니다.

```sh
# uv 설치 (없다면)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 프로젝트 클론
git clone <repository-url>
cd sisyphus

# 의존성 설치
uv sync
```

개발 모드로 직접 실행:
```sh
uv run sisyphus work
```

### 첫 작업

1. **작업 계획서 작성** - `ai-todolist.md` 파일을 만듭니다.
   - 무엇을 만들지 적습니다.
   - 어떻게 만들지 적습니다.
   - 체크박스(`- [ ]`)로 작업을 나열합니다.
   - *지금은 이렇습니다만, 빠른 시일 내에 작업 계획서 자동 생성 기능이 금방 공개됩니다.*

2. **시지푸스 실행**
   ```sh
   uv run sisyphus work
   ```

3. **관찰** - TUI가 뜨면서 에이전트가 일하는 모습이 보입니다.
   - 채팅 로그에서 진행 상황 확인
   - 상태 패널에서 현재 단계 확인
   - 필요하면 메시지 입력 가능

4. **완료** - 모든 작업이 끝나면 시지푸스가 알려줍니다.

---

## 명령어

### `sisyphus work`

작업을 시작합니다. 기본적으로 Claude 에이전트를 사용하고 TUI 모드로 실행됩니다.

```sh
# 기본 실행 (Claude + TUI)
uv run sisyphus work

# CLI 모드로 실행 (자동화에 유용)
uv run sisyphus work --no-tui

# OpenCode 에이전트 사용
uv run sisyphus work --agent opencode
```

### 에이전트 선택

시지푸스는 두 가지 에이전트를 지원합니다.

**Claude**
```sh
# 기본 모델
uv run sisyphus work --agent claude

# 특정 모델 지정
uv run sisyphus work --agent claude:sonnet

# SDK 옵션 조정
uv run sisyphus work --agent claude \
  --execute-sdk-options '{"temperature": 0.8}'
```

**OpenCode** (Alpha Support)
```sh
# 자동으로 서버 시작
uv run sisyphus work --agent opencode

# 외부 서버 사용
uv run sisyphus work --agent opencode \
  --opencode-server-url http://localhost:8080
```

### 실행과 검증을 분리

시지푸스의 핵심 기능입니다. 작업하는 에이전트와 검증하는 에이전트를 따로 둘 수 있습니다.

```sh
# Claude로 작업하고, OpenCode로 검증
uv run sisyphus work \
  --execute claude:sonnet \
  --verify opencode

# 실행만 하고 검증 생략
uv run sisyphus work --execute claude
```

검증 에이전트는 항상 새로운 세션에서 시작합니다. 컨텍스트가 깨끗합니다. 편향되지 않습니다.

### 프롬프트 커스터마이징

에이전트에게 주는 지시를 바꿀 수 있습니다.

```sh
# 슬래시 커맨드 (내장 프롬프트)
uv run sisyphus work \
  --execute-prompt /execute \
  --verify-prompt /architect

# 파일에서 읽기
uv run sisyphus work \
  --execute-prompt prompts/my-execute.md \
  --verify-prompt prompts/my-verify.md

# 직접 텍스트로 전달
uv run sisyphus work \
  --execute-prompt "ai-todolist.md의 모든 작업을 완료하세요"

# 추가 지시사항 덧붙이기
uv run sisyphus work \
  --execute-extra-prompt "타입 힌트를 반드시 사용하세요" \
  --verify-extra-prompt "보안 취약점을 중점적으로 검토하세요"
```

### `sisyphus reset`

작업 환경을 깨끗하게 정리합니다.

```sh
# 세션과 로그만 삭제
uv run sisyphus reset

# 작업 계획서까지 삭제 (처음부터 다시)
uv run sisyphus reset --include-task-specs
```

---

## TUI 사용법

Textual 기반의 터미널 UI입니다.

### 레이아웃

```
┌─────────────────────────────────────┐
│                                     │
│         채팅 로그 (70%)            │  ← 에이전트 메시지, 작업 진행 상황
│                                     │
├─────────────────────────────────────┤
│     상태 패널 (20%)                 │  ← 현재 단계, 작업 상태
├─────────────────────────────────────┤
│ > 입력창 (10%)                      │  ← 메시지 입력
└─────────────────────────────────────┘
```

### 키보드 단축키

- **Ctrl+C** - 작업 중단 (인터럽트)
- **Ctrl+D** - 종료
- **UP** - 이전 메시지 편집
- **Shift+Enter** - 입력창에서 줄바꿈 (개행)
- **Enter** - 메시지 전송

### 테마

시스템 테마를 자동 감지합니다. 수동으로 변경 가능합니다.

```sh
# 자동 감지 (기본)
uv run sisyphus work --theme system

# 다크 모드 (Catppuccin Mocha)
uv run sisyphus work --theme mocha

# 라이트 모드 (Catppuccin Latte)
uv run sisyphus work --theme latte
```

---

## 작업 계획서 (`ai-todolist.md`)

시지푸스의 돌이 여기에 있습니다. 다행히 시지푸스는 돌을 산 정상으로 밀어 올릴 수 있습니다. 그냥 계속 밀면 됩니다.

### 기본 구조

  ```markdown
  # 사용자 요청

  여기에 무엇을 만들지 적습니다.

  ## 작업 목록

  - [ ] 작업 1: 데이터베이스 스키마 설계
  - [ ] 작업 2: API 엔드포인트 구현
  - [ ] 작업 3: 테스트 코드 작성

  ## 완료 플래그

  is_all_goals_accomplished = FALSE
  ```

### 중요 규칙

1. **체크박스는 신성합니다** - `- [ ]`는 미완료, `- [x]`는 완료
2. **완료 플래그는 거짓말을 못합니다** - 모든 작업이 끝나야만 `TRUE`로 바뀝니다
3. **시지푸스는 이 문서를 읽고 또 읽습니다** - 명확하게 작성하세요

작업이 완료되면:
- 모든 체크박스가 `- [x]`로 체크됨
- `is_all_goals_accomplished = TRUE`로 변경됨

---

## 세션 관리

### 세션이란

시지푸스는 작업 중간에 멈춰도 기억합니다. 세션 파일에 저장합니다.

- **위치**: `./sessions/sessions.json`
- **내용**: 에이전트 대화 히스토리, 작업 진행상황

### 재개 정책

- **실행 단계**: 이전 세션을 이어갑니다. 컨텍스트를 유지합니다.
- **검증 단계**: 항상 새로운 세션입니다. 편견 없이 검증합니다.

### 세션 초기화

작업이 완전히 완료됐음을 확인하면, 세션 관련 내용을 삭제해 다음 작업에 영향을 주지 않도록 해야 합니다.

```sh
uv run sisyphus reset
```

---

## 문제 해결

### "OpenCode 바이너리를 찾을 수 없습니다"

OpenCode가 PATH에 없습니다.

```sh
# 바이너리 위치 직접 지정
uv run sisyphus work --agent opencode \
  --binary /path/to/opencode

# 또는 PATH에 추가
export PATH=$PATH:/path/to/opencode/bin
```

### "포트 8080이 이미 사용 중입니다"

OpenCode 서버가 이미 실행 중이거나 다른 프로세스가 사용 중입니다.

```sh
# 외부 서버 사용
uv run sisyphus work --agent opencode \
  --opencode-server-url http://localhost:8080

# 포트 확인
lsof -i :8080
```

### "세션 파일이 손상되었습니다"

세션 파일 복구에 실패했습니다. 삭제하고 새로 시작하세요.

```sh
rm ./sessions/sessions.json
```

### 테스트 실행

시지푸스는 pytest를 사용합니다. anyio 덕분에 asyncio와 trio 두 백엔드 모두 테스트됩니다.

```sh
# 전체 테스트 (461개 × 2 = 922번 실행)
uv run pytest

# 상세 출력
uv run pytest -v

# 첫 실패에서 중단
uv run pytest -x

# 특정 파일만
uv run pytest sisyphus/agents/tests/test_claude.py

# 커버리지 확인
uv run pytest --cov=sisyphus --cov-report=html
```

### 코드 품질 검사

```sh
# 타입 체크
uv run basedpyright

# 린트
uv run ruff check

# 린트 자동 수정
uv run ruff check --fix

# 포맷
uv run ruff format

# 한 번에 전부
uv run basedpyright && uv run ruff check && uv run pytest
```

### 프로젝트 구조

```
sisyphus/
├── sisyphus/              # 메인 패키지
│   ├── agents/           # 에이전트 구현
│   │   ├── base.py       # Agent 프로토콜
│   │   ├── claude.py     # Claude 에이전트
│   │   └── opencode.py   # OpenCode 에이전트
│   ├── core/             # 핵심 로직
│   │   ├── loop.py       # ExecutionLoop (실행-검증 오케스트레이션)
│   │   ├── prompts.py    # 프롬프트 해석
│   │   ├── session.py    # 세션 저장/복원
│   │   └── tasks.py      # 작업 검증 (ai-todolist.md)
│   ├── ui/               # 사용자 인터페이스
│   │   ├── tui/          # Textual TUI
│   │   └── cli/          # Rich CLI
│   ├── utils/            # 유틸리티
│   └── cli.py            # Typer CLI 진입점
├── prompts/              # 기본 프롬프트
│   ├── execute_command.md
│   └── architect_command.md
├── sessions/             # 세션 저장소 (자동생성)
├── logs/                 # 로그 파일 (자동생성)
└── pyproject.toml        # 프로젝트 설정
```

### 코딩 규칙

시지푸스는 까다롭습니다. 스스로에게도 엄격합니다.

- **타입 힌트 필수** - 모든 함수 파라미터와 리턴값에 타입 명시 (ruff ANN001)
- **더블 쿼트** - 문자열은 `"`로 감싸기
- **anyio 사용** - asyncio와 trio 호환성
- **Given-When-Then** - 테스트 구조
- **Protocol 기반** - ABC 대신 typing.Protocol (PEP 544)

---

## 기술 스택

시지푸스는 현대적인 Python 생태계 위에 서 있습니다.

### 코어

- **Python 3.12** - 최신 타입 힌팅과 성능
- **anyio** - asyncio와 trio 추상화, 한 코드로 두 백엔드
- **Typer** - CLI 프레임워크
- **Textual** - 터미널 UI
- **Rich** - 예쁜 콘솔 출력

### 에이전트 통신

- **claude-agent-sdk** - Claude 공식 SDK
- **httpx** - OpenCode REST API 통신
- **aiofiles** - 비동기 파일 I/O

### 개발 도구

- **basedpyright** - 타입 체커 (standard 모드)
- **ruff** - 린터와 포매터 하나로
- **pytest + pytest-anyio** - 테스트 프레임워크
- **uv** - 빠른 패키지 매니저

### 디자인

- **Protocol-based** - 인터페이스 분리 (PEP 544)
- **Dependency Injection** - 느슨한 결합
- **Factory Pattern** - 에이전트/UI 생성
- **SOLID** - 객체지향 5원칙 준수

---

## 라이선스

시지푸스는 **Sustainable Use License 1.0**으로 배포됩니다.

### 간단히 말하면

✅ **할 수 있는 것:**
- 개인 사용 및 학습
- 회사 내부 업무용 사용
- 코드 수정 및 개선
- 무료로 배포 (비상업적 목적)

❌ **할 수 없는 것:**
- 상업적 판매
- SaaS로 제공
- 유료 서비스로 재배포

### 자세한 내용

전체 라이선스 조항은 [LICENSE.md](LICENSE.md)를 확인하세요.

### 엔터프라이즈 라이선스

상업적 사용이나 SaaS 제공이 필요하신가요? 별도 문의 주세요.

## 기여하기

[기여 가이드라인 추가 필요]

## 지원

[지원 정보 추가 필요]
