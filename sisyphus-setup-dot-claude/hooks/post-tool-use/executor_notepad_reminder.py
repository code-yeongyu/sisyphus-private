#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

import asyncio
import json
import sys
from datetime import datetime


def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")


async def run_git_command(command: list[str], cwd: str) -> tuple[int, str]:
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, _ = await process.communicate()
        return (process.returncode or 0, stdout_bytes.decode(errors="replace").strip())
    except Exception:
        return (1, "")


async def get_git_info(cwd: str) -> dict[str, str]:
    info = {}

    is_git_result = await run_git_command(["git", "rev-parse", "--git-dir"], cwd)
    if is_git_result[0] != 0:
        return info

    commands = [
        ("branch", ["git", "branch", "--show-current"]),
        ("commit_hash", ["git", "rev-parse", "--short", "HEAD"]),
        ("commit_message", ["git", "log", "-1", "--pretty=%s"]),
        ("commit_author", ["git", "log", "-1", "--pretty=%an"]),
        ("commit_time", ["git", "log", "-1", "--pretty=%ar"]),
        ("status", ["git", "status", "--porcelain"]),
        ("git_root", ["git", "rev-parse", "--show-toplevel"]),
    ]

    tasks = [run_git_command(cmd, cwd) for _, cmd in commands]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for (key, _), result in zip(commands, results, strict=False):
        if isinstance(result, BaseException):
            continue

        returncode, stdout = result
        if returncode != 0:
            if key == "branch":
                info["branch"] = "detached"
            continue

        match key:
            case "status":
                unstaged = len([line for line in stdout.split("\n") if line])
                if unstaged > 0:
                    info["unstaged"] = str(unstaged)
            case "git_root":
                if stdout != cwd:
                    info["git_root"] = stdout
            case _:
                info[key] = stdout

    return info


async def _main() -> int:
    EXECUTOR = "executor"

    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        return 1

    subagent_type = input_data.get("tool_input", {}).get("subagent_type", "")

    if subagent_type != EXECUTOR:
        print(
            f"Skipping executor hook: Not an executor agent (subagent_type: {subagent_type})",
            file=sys.stderr,
        )
        return 0

    cwd = input_data.get("cwd", ".")
    current_time = get_current_time()

    print(
        f"""
{"=" * 40}
📝 EXECUTOR DOCUMENTATION MODE
{"=" * 40}

[SYSTEM TIME]
Current system time: {current_time}
""",
        file=sys.stderr,
    )

    git_info = await get_git_info(cwd)
    if git_info:
        git_lines = ["[GIT INFO]"]
        if "branch" in git_info:
            git_lines.append(f"Git branch: {git_info['branch']}")
        if all(k in git_info for k in ["commit_hash", "commit_message", "commit_author", "commit_time"]):
            git_lines.append(
                f"Git commit: [{git_info['commit_hash']}] "
                + f'"{git_info["commit_message"]}" by {git_info["commit_author"]} ({git_info["commit_time"]})'
            )
        if "unstaged" in git_info:
            git_lines.append(f"Git unstaged: {git_info['unstaged']} files")
        if "git_root" in git_info:
            git_lines.append(f"Git root: {git_info['git_root']}")
        print("\n".join(git_lines) + "\n", file=sys.stderr)

    print(
        f"""
{"=" * 40}
📋 NOTEPAD FILE DOCUMENTATION REQUIREMENTS
{"=" * 40}

**당신은 executor agent입니다. .sisyphus/notepads/{{plan-name}}.md에 메모하며 진행하는 것을 잊지마세요!**

메모해야 할 내용:
- 작업 시점에 요구받은 내용 (정확한 요구사항 기록)
- 작성 시점의 시간 (타임스탬프)
- 상세한 작업 로그 (수행한 모든 단계)
- 작업 전 만들었던 가설 (예상했던 내용)
- 작업 이후 가설과 달랐던 부분 (실제 결과와 차이점)
- 작업하며 드는 생각들 메모 (중요한 판단 포인트)
- 작업하며 얻은 인사이트 (발견한 패턴, 개선점)
- 작업 도중 예상과 달랐던 부분 (놀라운 발견)
- 아무것도 모르는 다른 새로운 작업자를 위한 팁 및 조언
- 발견한 문제 및 해결 방법
- 테스트 결과 (성공/실패 여부와 이유)
- 코드 변경 사항 요약 (어떤 파일을 왜 수정했는지)

**CRITICAL: ALWAYS use bash append - NEVER use Edit tool**

메모 추가 방법 (MANDATORY):
```bash
# ALWAYS use heredoc append for notepad updates
cat >> .sisyphus/notepads/{{plan-name}}.md <<'NOTEPAD_EOF'

[$(date '+%Y-%m-%d %H:%M')] - 작업 제목

### 요구사항
- [작업 시작 시 받은 요구사항]

### 작업 로그
1. [수행한 첫 번째 단계]
2. [수행한 두 번째 단계]

### 인사이트
- [발견한 중요한 내용]

### LEARNINGS
- [프로젝트 특화 발견사항]
- [올바른 명령어: npm run build:prod not build]

NOTEPAD_EOF
```

**Why bash append?**
✅ Guarantees append-only (no overwrites)
✅ Atomic operation
✅ Works with large files
❌ Edit tool risks file corruption
""",
        file=sys.stderr,
    )

    print(
        f"""
[EXECUTION REQUIREMENTS]
사용자가 제시한, 그리고 계획서 속의 요구사항과 지시사항을 어떠한 게으름도 없이 정직하게 이행하세요.
작업해야 할 내용을 TODO로 코드 내에 남기는 것, 테스트가 온전하고 완전하게 통과하지 않았는데
넘어가는 것은 엄격히 금지됩니다.
어떠한 경우에서도 작업 계획서 속 내용을 모두 구현해야하고, 테스트가 모두 통과해야 합니다 -
어떠한 이유도 허용되지 않습니다.
(일시적인 세팅 오류라도 넘어가서는 안되고 성공하는 것을 명시적으로 확인하여야 합니다.)

[COMMIT REMINDER]
After modifying .sisyphus/notepads/{{plan-name}}.md, don't forget to commit your changes!
Example: git add .sisyphus/notepads/{{plan-name}}.md && git commit -m 'docs: update notepad with [task name] findings'

[CRITICAL EXECUTION STANDARDS]
✅ MUST DO:
  - Write detailed notes in .sisyphus/notepads/{{plan-name}}.md BEFORE, DURING, and AFTER each task
  - Run ALL tests and ensure they pass (pytest, ruff, typecheck, etc.)
  - Verify your work thoroughly - assume orchestrator will check everything
  - Document REAL findings, not placeholders or generic statements
  - Complete 100% of assigned work - no partial implementations

❌ MUST NOT DO:
  - Leave TODO comments in code instead of implementing
  - Skip tests or claim they pass when they don't
  - Report completion when work is incomplete
  - Write vague or unhelpful notepad entries
  - Take shortcuts or compromise on quality

{"=" * 40}
🎯 EXECUTOR MISSION: EXECUTE PERFECTLY
{"=" * 40}
""",
        file=sys.stderr,
    )

    return 2


def main() -> int:
    return asyncio.run(_main())


if __name__ == "__main__":
    sys.exit(main())
