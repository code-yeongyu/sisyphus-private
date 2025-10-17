# 작업 목표

CLI 구조 변경을 통한 명령어 체계 개선:
1. `sisyphus run` → `sisyphus work`로 커맨드 이름 변경
2. `sisyphus reset` 커맨드 추가 (생성 파일 정리)
   - 기본: `sessions/`, `logs/` 삭제
   - 옵션: `ai-todolist.md`, `notepad.md` 추가 삭제

# 작업 시작 여부
is_execution_started = FALSE

# 모든 목표 달성 여부
is_all_goals_accomplished = FALSE

# 병렬 실행 여부
parallel_requested = FALSE

# 현재 진행 중인 작업
- 작업 시작 전입니다.
   - 작업을 시작하면 위의 `is_execution_started` 의 값을 TRUE 로 바꾸세요.
   - 사용자가 명시적으로 "작업을 시작하라" 라고 말하기 전까지는 절대로 작업하지 않습니다.
   - **plan reviewer 에게 OKAY 사인을 받았더라도 절대 시작하지마십시오**
   - 사용자가 명시적으로 "작업을 시작하라" 라고 말하기 전까지는 절대로 작업하지 않습니다.

# 작업 계획

## 파일: `/Users/yeongyu/local-workspaces/sisyphus/sisyphus/cli.py`

**현재 파일 구조 (414줄)**:
- line 1-11: import stdlib
- line 13-26: import 3rd-party & internal
- line 28-34: constants (app, console, error_console)
- line 314-409: run 커맨드 정의
- line 412-413: `if __name__ == "__main__":`

### 변경 1: import 섹션에 shutil 추가

**위치**: line 5와 line 6 사이
**현재 (line 5-6)**:
```python
import json
import time
```

**변경 후**:
```python
import json
import shutil
import time
```

**이유**: reset 커맨드에서 `shutil.rmtree()` 사용

### 변경 2: run 커맨드 이름을 work로 변경

**위치**: line 314
**현재**:
```python
@app.command(name="run")
```

**변경 후**:
```python
@app.command(name="work")
```

**주의**: 함수명은 `def run(` 그대로 유지 (Typer는 decorator의 name 파라미터 사용)

### 변경 3: docstring 업데이트

**위치**: line 342
**현재**:
```python
    """Run Sisyphus multi-agent system."""
```

**변경 후**:
```python
    """Work with Sisyphus multi-agent system."""
```

### 변경 4: reset 커맨드 추가

**위치**: line 411과 line 412 사이 (run 함수 끝과 `if __name__` 사이)
**추가할 코드 (완전한 함수)**:
```python


@app.command(name="reset")
def reset(
    include_task_specs: bool = typer.Option(
        False,
        "--include-task-specs",
        help="Also delete ai-todolist.md and notepad.md"
    ),
) -> None:
    """Clean up generated files (sessions/, logs/, optionally docs)."""
    base_targets = [Path("sessions"), Path("logs")]
    doc_targets = [Path("ai-todolist.md"), Path("notepad.md")]
    targets = base_targets + (doc_targets if include_task_specs else [])

    for target in targets:
        try:
            if target.is_dir():
                shutil.rmtree(target)
                console.print(f"[green]✓[/green] Deleted directory: {target}")
            elif target.is_file():
                target.unlink()
                console.print(f"[green]✓[/green] Deleted file: {target}")
            else:
                console.print(f"[yellow]⊘[/yellow] Not found: {target}")
        except (PermissionError, OSError) as e:
            error_console.print(f"[red]✗[/red] Failed to delete {target}: {e}")

    console.print("\n[bold green]Reset complete![/bold green]")

```

**참고**:
- `Path`: line 9에서 이미 import됨
- `console`, `error_console`: line 33-34에서 이미 정의됨
- `shutil`: 변경 1에서 추가함
- 함수는 2줄 공백 후 추가 (PEP 8)

## 예상 결과

### sisyphus --help 출력
```
Usage: sisyphus [OPTIONS] COMMAND [ARGS]...

  Sisyphus Multi-Agent System

Options:
  --help  Show this message and exit.

Commands:
  work   Work with Sisyphus multi-agent system.
  reset  Clean up generated files (sessions/, logs/, optionally docs).
```

### sisyphus reset 출력 (파일 존재 시)
```
✓ Deleted directory: sessions
✓ Deleted directory: logs

Reset complete!
```

### sisyphus reset --include-task-specs 출력 (모든 파일 존재 시)
```
✓ Deleted directory: sessions
✓ Deleted directory: logs
✓ Deleted file: ai-todolist.md
✓ Deleted file: notepad.md

Reset complete!
```

### sisyphus reset 출력 (파일 없을 시)
```
⊘ Not found: sessions
⊘ Not found: logs

Reset complete!
```

# TODOs

- [ ] 1. CLI 구조 변경 및 reset 커맨드 구현
   - [ ] 1.1 구현: `sisyphus/cli.py` 수정
      - [ ] line 5-6 사이에 `import shutil` 추가
      - [ ] line 314: `@app.command(name="run")` → `@app.command(name="work")`
      - [ ] line 342: `"""Run Sisyphus multi-agent system."""` → `"""Work with Sisyphus multi-agent system."""`
      - [ ] line 411-412 사이에 reset 커맨드 전체 추가 (위 코드 참조)
   - [ ] 1.2 수동 테스트: 더미 파일 생성 및 CLI 테스트
      ```bash
      # 테스트 준비: 더미 파일 생성
      mkdir -p sessions logs
      echo '{"test": "data"}' > sessions/test.json
      echo 'log content' > logs/test.log
      touch ai-todolist.md notepad.md

      # 테스트 1: help 확인
      uv run sisyphus --help
      # 예상: "work", "reset" 커맨드 표시

      # 테스트 2: work help 확인
      uv run sisyphus work --help
      # 예상: 기존 run 옵션들 전부 표시

      # 테스트 3: reset (기본)
      uv run sisyphus reset
      # 예상: sessions/, logs/ 삭제 메시지

      # 테스트 4: reset --include-task-specs (더미 재생성 후)
      mkdir -p sessions logs && touch ai-todolist.md notepad.md
      uv run sisyphus reset --include-task-specs
      # 예상: 모든 파일 삭제 메시지

      # 테스트 5: reset (파일 없을 때)
      uv run sisyphus reset
      # 예상: "Not found" 메시지
      ```
   - [ ] 1.3 린트 및 타입 체크
      ```bash
      uv run ruff check sisyphus/cli.py
      # 예상: 에러 없음

      uv run basedpyright sisyphus/cli.py
      # 예상: 타입 에러 없음
      ```
   - [ ] 1.4 기존 테스트 통과 확인
      ```bash
      uv run pytest -x
      # 예상: 모든 테스트 통과
      ```
   - [ ] 1.5 커밋
      ```bash
      git add sisyphus/cli.py
      git commit -m "refactor cli to use work and reset subcommands"
      ```

# 최종 작업 검증 체크리스트

- [ ] 1. CLI 명령어 구조 변경
   - [ ] `sisyphus work` 명령어로 기존 run 기능 실행 가능
   - [ ] `sisyphus reset` 명령어로 파일 정리 가능
   - [ ] `sisyphus --help`에 두 커맨드 모두 표시됨
- [ ] 2. reset 커맨드 기능
   - [ ] 기본 실행 시 `sessions/`, `logs/` 디렉토리 삭제
   - [ ] `--include-task-specs` 옵션 사용 시 `ai-todolist.md`, `notepad.md` 추가 삭제
   - [ ] 존재하지 않는 파일/디렉토리에 대해 "Not found" 메시지 표시
   - [ ] 삭제 실패 시 에러 메시지 출력 후 계속 진행
- [ ] 3. 기존 기능 유지
   - [ ] `work` 커맨드가 기존 `run` 커맨드와 동일하게 작동
   - [ ] 모든 옵션 파라미터 정상 작동
   - [ ] TUI/CLI 모드 선택 정상 작동
- [ ] 4. 코드 품질
   - [ ] 타입 체크 통과 (basedpyright)
   - [ ] 린트 규칙 준수 (ruff)
   - [ ] nested import 사용 안 함 (프로젝트 컨벤션)
- [ ] 5. 과도한 구현 방지
   - [ ] 요청하지 않은 기능 추가 없음
   - [ ] 기존 로직 불필요한 리팩토링 없음
   - [ ] 최소한의 변경으로 요구사항 충족
