# 사용자의 최초 요청 (기록용)

sisyphus-cc-hooks 패키지를 `uv tool install`로 설치 가능하게 만들고, `sisyphus-cc-hooks post-tool-use` 명령으로 실행 가능하게 하기. 훅 등록은 수동으로 하되, 실행 가능한 바이너리 경로를 얻어서 settings.json에 넣을 수 있어야 함.

## 추가 사용자 요청 (기록용)

- CLI 도구로 만들기
- CLI entry point 이름: `sisyphus-cc-hooks`
- Subcommand: `post-tool-use`
- 기존 90% 커버리지 테스트 유지
- 모든 구현은 사용자가 말한 대로 진행

# 작업 목표 (WHAT & WHY)

## 핵심 목표 (TL;DR)

sisyphus-cc-hooks 패키지를 uv tool install 가능한 CLI 도구로 전환하여, `sisyphus-cc-hooks post-tool-use` 명령으로 훅 스크립트를 실행 가능하게 만들기

## 상세 목표

- **목표**: uv tool install로 설치 후 PATH에서 바로 실행 가능
  - **측정 기준**: `uv tool install projects/sisyphus-cc-hooks` 성공 → `which sisyphus-cc-hooks` 경로 출력

- **목표**: CLI 명령으로 기존 훅 로직 실행
  - **측정 기준**: `sisyphus-cc-hooks post-tool-use` 실행 시 stdin에서 JSON 읽어 검증 메시지 출력

- **목표**: 기존 90% 테스트 커버리지 유지
  - **측정 기준**: `uv run pytest --cov` 실행 시 90% 이상 커버리지 유지

# 작업 배경 (WHY & WHAT - 현재 상태)

## 현재 상황

- sisyphus-cc-hooks는 단일 스크립트 실행 방식 (`uv run --script`)
- 훅 설치 시 스크립트 파일 경로를 직접 settings.json에 등록해야 함
- sisyphus-cli는 이미 `uv tool install` 가능한 CLI 도구로 구현됨
- Typer 기반 CLI 구조 (`app.command()`, `app.add_typer()` 패턴)

## 변경 이유

- 설치 후 바로 사용 가능한 CLI 도구로 개선
- `which sisyphus-cc-hooks`로 경로 확인하여 settings.json 등록 간편화
- sisyphus-cli와 동일한 패키지 구조로 통일

## 수행할 변경

- **현재**: `uv run --script post_tool_use_executor_verification.py` 직접 실행
- **변경 후**: `sisyphus-cc-hooks post-tool-use` CLI 명령 실행
- **현재**: pyproject.toml에 dependencies만 정의
- **변경 후**: [project.scripts] entry point 추가, typer dependency 추가

# 작업 시작됨
is_execution_started = FALSE

# 모든 목표 달성됨
is_all_goals_accomplished = FALSE

# 병렬 실행
parallel_requested = FALSE

# 현재 진행 중인 작업
- [x] 4. 통합 테스트 및 검증
  - 진행 상태: in_progress
  - 시작 시각: Fri Nov  7 20:29:52 KST 2025

# 필요한 배경 지식

## 기술 스택

- **언어**: Python 3.12+
- **패키지 관리**: uv (workspace 구조)
- **CLI 프레임워크**: Typer 0.15+
- **비동기**: anyio 4.11+ (기존 코드에서 사용)
- **YAML**: ruamel.yaml 0.18+
- **Pydantic**: 2.0+

## 파일 구조 및 역할

### 참조 파일

#### 1. `projects/sisyphus-cli/pyproject.toml`
- **역할**: sisyphus-cli 패키지 설정 (참고용)
- **검색 키워드**: `[project.scripts]` 섹션 찾기
- **패턴 이해**: entry point 정의 방식 (`sisyphus = "sisyphus.cli:app"`)
- **코드 참조**:
```toml
[project.scripts]
sisyphus = "sisyphus.cli:app"
```

#### 2. `projects/sisyphus-cli/sisyphus/cli.py`
- **역할**: Typer CLI entry point 구조
- **검색 키워드**: `typer.Typer(`, `app.command(`, `app.add_typer(`
- **패턴 이해**: CLI app 생성 → command/subapp 등록 방식
- **코드 참조**:
```python
import typer

app = typer.Typer(name="sisyphus", help="...")

from sisyphus.cli.plan import plan_app
app.add_typer(plan_app)  # subcommand 추가
```

#### 3. `projects/sisyphus-cc-hooks/sisyphus_cc_hooks/post_tool_use_executor_verification.py`
- **역할**: 기존 훅 로직 (main() 함수 포함)
- **검색 키워드**: `def main()` 함수
- **패턴 이해**: stdin → JSON 파싱 → 검증 로직 → stderr 출력 + exit code
- **재사용**: 기존 main() 함수를 CLI에서 호출

#### 4. `projects/sisyphus-cc-hooks/tests/test_post_tool_use_executor_verification.py`
- **역할**: subprocess 기반 통합 테스트
- **검색 키워드**: `subprocess.run(`, `run_hook_script(` 함수
- **패턴 이해**: 스크립트 실행 → exit code + stderr 검증
- **업데이트**: CLI 명령 실행 방식 테스트 추가

## 프로젝트 커밋 메시지 스타일

```
<type>: <subject>

Types: feat, fix, docs, test, refactor, build
Examples:
- feat: add CLI entry point for sisyphus-cc-hooks
- test: add CLI command execution tests
- build: add typer dependency to pyproject.toml
```

# 작업 흐름 (HOW - 작업 흐름 및 의존성)

## 작업 의존성 다이어그램

```
Task 1 (pyproject.toml 수정)
   ↓
Task 2 (CLI wrapper 구현) - depends on Task 1
   ↓
Task 3 (테스트 추가) - depends on Task 2
   ↓
Task 4 (통합 테스트 및 검증) - depends on Task 3
```

## 단계별 설명

- **Phase 1 (Task 1)**: pyproject.toml 수정 (dependencies, scripts 추가)
- **Phase 2 (Task 2)**: CLI wrapper 구현 (Typer app 생성)
- **Phase 3 (Task 3)**: 테스트 추가 (CLI 명령 실행 테스트)
- **Phase 4 (Task 4)**: 전체 검증 (설치, 실행, 커버리지 확인)

# 작업 계획

## PRD 및 구조

### 시스템 구조

```mermaid
graph TB
    User[User] -->|uv tool install| Install[Install Package]
    Install --> Entry[Entry Point: sisyphus-cc-hooks]

    Entry --> CLI[CLI App<br/>Typer]
    CLI -->|post-tool-use| Cmd[post_tool_use command]

    Cmd --> Main[Existing main()<br/>verification logic]
    Main -->|stdin| Parse[Parse JSON]
    Main -->|stderr + exit 2| Output[Verification Message]
```

### 구현 세부사항

**CLI 구조**:
```python
# sisyphus_cc_hooks/cli.py
import typer
from sisyphus_cc_hooks.post_tool_use_executor_verification import main

app = typer.Typer(name="sisyphus-cc-hooks")

@app.command(name="post-tool-use")
def post_tool_use():
    """Execute post-tool-use hook for executor verification."""
    exit_code = main()
    raise typer.Exit(code=exit_code)
```

**Entry Point**:
```toml
[project.scripts]
sisyphus-cc-hooks = "sisyphus_cc_hooks.cli:app"
```

## 구현 세부사항

### 암묵적 가정 명시

- **가정**: 기존 main() 함수는 수정 없이 재사용 가능
- **가정**: stdin/stdout/stderr 처리는 기존 로직 그대로 사용
- **가정**: 테스트는 subprocess + 직접 import 방식 모두 유지
- **가정**: pyproject.toml 수정 후 `uv sync` 필요

# TODO

- [x] 1. pyproject.toml 수정

   **참조 소스**:
   - 패턴: `projects/sisyphus-cli/pyproject.toml:47-48` (검색: `[project.scripts]`)
   - Typer 버전: `projects/sisyphus-cli/pyproject.toml:36` (검색: `typer>=`)

   - [x] 1.1 dependencies에 typer 추가

      **구현 세부사항**:
      - 현재: `dependencies = ["anyio>=4.11.0", "pydantic>=2.12.3", "ruamel-yaml>=0.18.16"]`
      - 변경 후: `"typer>=0.15.0"` 추가

      **참조**: sisyphus-cli pyproject.toml:36 참고하여 동일 버전 사용

   - [x] 1.2 [project.scripts] 섹션 추가

      **구현 세부사항**:
      ```toml
      [project.scripts]
      sisyphus-cc-hooks = "sisyphus_cc_hooks.cli:app"
      ```

      **참조**: sisyphus-cli pyproject.toml:47-48 패턴 따르기

   - [x] 1.3 변경사항 적용

      **실행 명령**: `uv sync`
      **예상 결과**: typer 설치 완료

   - [x] **작업 완료 검증 체크리스트**
      - [x] pyproject.toml에 typer dependency 추가 확인
      - [x] [project.scripts] 섹션 추가 확인
      - [x] `uv sync` 실행 성공 확인
      - [x] ruff check 통과: `ruff check projects/sisyphus-cc-hooks`

- [x] 2. CLI wrapper 구현

   **참조 소스**:
   - CLI 구조: `projects/sisyphus-cli/sisyphus/cli.py` (검색: `typer.Typer(`, `app.command(`)
   - 기존 main: `projects/sisyphus-cc-hooks/sisyphus_cc_hooks/post_tool_use_executor_verification.py:320` (검색: `def main()`)

   - [x] 2.1 sisyphus_cc_hooks/cli.py 생성

      **구현 세부사항**:
      ```python
      """CLI entry point for sisyphus-cc-hooks."""

      from __future__ import annotations

      import typer

      from sisyphus_cc_hooks.post_tool_use_executor_verification import main as verification_main

      app = typer.Typer(
          name="sisyphus-cc-hooks",
          help="Claude Code hooks for Sisyphus task verification"
      )

      @app.command(name="post-tool-use")
      def post_tool_use() -> None:
          """Execute post-tool-use hook for executor verification.

          Reads JSON from stdin, validates executor completion,
          and outputs verification instructions to stderr.
          """
          exit_code = verification_main()
          raise typer.Exit(code=exit_code)

      if __name__ == "__main__":
          app()
      ```

      **참조**:
      - sisyphus-cli/sisyphus/cli.py:7-8 참고 (Typer app 생성 패턴)
      - 기존 main() 함수 재사용 (수정 없이)

   - [x] 2.2 타입 체크 및 린트

      **실행 명령**:
      - `basedpyright projects/sisyphus-cc-hooks/sisyphus_cc_hooks/cli.py`
      - `ruff check projects/sisyphus-cc-hooks/sisyphus_cc_hooks/cli.py`

      **예상 결과**: 0 errors

   - [x] **작업 완료 검증 체크리스트**
      - [x] cli.py 파일 생성 확인
      - [x] typer.Typer app 인스턴스 생성 확인
      - [x] post-tool-use command 구현 확인
      - [x] 기존 main() 함수 호출 확인
      - [x] basedpyright 통과
      - [x] ruff check 통과

- [x] 3. CLI 명령 실행 테스트 추가

   **참조 소스**:
   - 기존 테스트: `projects/sisyphus-cc-hooks/tests/test_post_tool_use_executor_verification.py:8-16` (검색: `run_hook_script(` 함수)

   - [x] 3.1 CLI 실행 테스트 추가

      **테스트 파일**: `tests/test_cli.py` (새 파일 생성)

      **구현 세부사항**:
      ```python
      # pyright: reportMissingImports=false
      import json
      import subprocess
      from pathlib import Path

      import pytest


      def test_cli_post_tool_use_command__with_valid_input__executes_hook(tmp_path: Path) -> None:
          # given: YAML plan with task in progress
          sisyphus_dir = tmp_path / ".sisyphus"
          sisyphus_dir.mkdir()
          tasks_dir = sisyphus_dir / "tasks"
          tasks_dir.mkdir()

          plan_file = tasks_dir / "test.yaml"
          plan_file.write_text(\"\"\"work_plans:
        - id: test-plan
          todos:
            - id: task-1
              title: "Test Task"
              status: in_progress
              verification_spec: []
          work_mode:
            current_task_id: task-1
      \"\"\")

          status_file = sisyphus_dir / "status.json"
          status_file.write_text(json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}}))

          json_input = {
              "tool_input": {"subagent_type": "sisyphus-executor"},
              "cwd": str(tmp_path),
              "session_id": "test",
          }

          # when: Execute CLI command
          proc = subprocess.run(
              ["sisyphus-cc-hooks", "post-tool-use"],
              input=json.dumps(json_input),
              capture_output=True,
              text=True,
              check=False,
          )

          # then: Hook executes and outputs message
          assert proc.returncode == 2
          assert "EXECUTOR TASK COMPLETION DETECTED" in proc.stderr
          assert "[ALL VERIFICATIONS COMPLETED]" in proc.stderr


      def test_cli_help__displays_usage() -> None:
          # when
          proc = subprocess.run(
              ["sisyphus-cc-hooks", "--help"],
              capture_output=True,
              text=True,
              check=False,
          )

          # then
          assert proc.returncode == 0
          assert "sisyphus-cc-hooks" in proc.stdout
          assert "post-tool-use" in proc.stdout
      ```

      **참조**: 기존 test_post_tool_use_executor_verification.py의 run_hook_script 패턴 따르되, CLI 명령 사용

   - [x] 3.2 테스트 실행

      **실행 명령**: `cd projects/sisyphus-cc-hooks && uv run pytest tests/test_cli.py -v`

      **예상 결과**: 2/2 tests passed

   - [x] **작업 완료 검증 체크리스트**
      - [x] test_cli.py 파일 생성 확인
      - [x] CLI 실행 테스트 구현 확인
      - [x] 테스트 통과 확인
      - [x] ruff check 통과

- [x] 4. 통합 테스트 및 검증

   - [x] 4.1 uv tool install 테스트

      **실행 명령**:
      ```bash
      # 설치
      uv tool install projects/sisyphus-cc-hooks

      # 경로 확인
      which sisyphus-cc-hooks
      ```

      **예상 결과**:
      - 설치 성공
      - 경로 출력 (예: `~/.local/bin/sisyphus-cc-hooks`)

   - [x] 4.2 CLI 명령 실행 테스트

      **실행 명령**:
      ```bash
      echo '{"tool_input": {"subagent_type": "other"}, "cwd": ".", "session_id": "test"}' | \
      sisyphus-cc-hooks post-tool-use
      ```

      **예상 결과**: Exit 0 + "Skipping hook" 메시지

   - [x] 4.3 전체 테스트 스위트 실행

      **실행 명령**: `cd projects/sisyphus-cc-hooks && uv run pytest --cov=sisyphus_cc_hooks --cov-report=term-missing`

      **예상 결과**:
      - 모든 테스트 통과
      - 커버리지 90% 이상 유지

   - [x] 4.4 Help 명령 테스트

      **실행 명령**:
      ```bash
      sisyphus-cc-hooks --help
      sisyphus-cc-hooks post-tool-use --help
      ```

      **예상 결과**: 사용법 출력

   - [ ] **작업 완료 검증 체크리스트**
      - [x] uv tool install 성공
      - [x] which 명령으로 경로 확인 가능
      - [x] CLI 명령 실행 성공
      - [x] 전체 테스트 통과 (기존 60개 + 신규 4개 = 64개)
      - [x] 커버리지 90% 이상 유지
      - [x] Help 명령 정상 동작
      - [x] ruff check 전체 통과
      - [x] basedpyright 전체 통과

- [ ] 5. 문서화 및 커밋

   - [ ] 5.1 README 업데이트 (선택사항)

      **참고**: 필요 시 설치 및 사용법 문서 추가

   - [ ] 5.2 변경사항 커밋

      **실행 명령**:
      ```bash
      cd projects/sisyphus-cc-hooks
      git add pyproject.toml sisyphus_cc_hooks/cli.py tests/test_cli.py
      git commit -m "feat: add CLI entry point for uv tool install support

      - Add typer dependency to pyproject.toml
      - Create CLI wrapper (sisyphus-cc-hooks post-tool-use command)
      - Add CLI execution tests
      - Maintain 90%+ test coverage
      - Enable installation via: uv tool install projects/sisyphus-cc-hooks

      🤖 Generated with [Claude Code](https://claude.com/claude-code)

      Co-Authored-By: Claude <noreply@anthropic.com>"
      ```

   - [ ] **작업 완료 검증 체크리스트**
      - [ ] 모든 파일 staged 확인
      - [ ] 커밋 메시지 프로젝트 스타일 준수
      - [ ] git log 확인

# 성공 비전

## 사용자 관점의 성공

- **시나리오**: 패키지 설치 후 바로 CLI 명령 사용
  - **경험**: `uv tool install` 한 번으로 설치 완료 → `which sisyphus-cc-hooks`로 경로 확인 → settings.json에 등록

- **시나리오**: 훅 실행 확인
  - **경험**: JSON 파이프로 전달 → 검증 메시지 출력 → 기존 동작과 동일

## 비즈니스 관점의 성공

- **측정 지표**: 설치 단계 단순화 (2단계 → 1단계)
  - **목표**: uv tool install 한 번으로 완료

- **측정 지표**: 코드 품질 유지
  - **목표**: 테스트 커버리지 90% 이상 유지

## 기술적 성공 기준

- [ ] uv tool install 성공: `uv tool install projects/sisyphus-cc-hooks` → 설치 완료
- [ ] CLI 실행 성공: `sisyphus-cc-hooks post-tool-use` → 정상 동작
- [ ] 경로 확인 가능: `which sisyphus-cc-hooks` → 경로 출력
- [ ] 모든 테스트 통과: `pytest` → 62/62 PASSED
- [ ] 커버리지 유지: `pytest --cov` → 90% 이상
- [ ] 타입 체크 통과: `basedpyright` → 0 errors
- [ ] 린트 통과: `ruff check` → 0 errors

# 최종 작업 검증 체크리스트

- [ ] 1. **기능 동작 검증**
   - [ ] uv tool install로 설치 가능
   - [ ] which 명령으로 경로 확인 가능
   - [ ] CLI 명령 실행 시 기존 훅 로직 동작
   - [ ] Help 명령 정상 동작

- [ ] 2. **코드 품질 검증**
   - [ ] 모든 테스트 통과 (기존 60개 + 신규 2개)
   - [ ] 커버리지 90% 이상 유지
   - [ ] ruff check 통과
   - [ ] basedpyright 통과

- [ ] 3. **범위 준수 검증**
   - [ ] 기존 main() 함수 수정 없이 재사용
   - [ ] 기존 테스트 유지
   - [ ] pyproject.toml, cli.py, test_cli.py만 추가/수정

- [ ] 4. **기존 기능 회귀 테스트**
   - [ ] 기존 subprocess 테스트 정상 동작
   - [ ] 직접 import 테스트 정상 동작
   - [ ] 전체 테스트 스위트 통과
