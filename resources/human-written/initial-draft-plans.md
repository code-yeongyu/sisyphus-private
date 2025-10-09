@./local-ignore/agentloop_sdk.py 를 프로젝트 형태로 재작성 하려고 해. 기본적으로 여러 형태의 cli agent 를 지원하도록 변경하는것이 목표야. 이에 따라 여러가지 변경사항이 필요한데, 일단 대표적인 예시는 다음과 같아.

루프 매니저
- claude agent sdk
- droid: `droid exec`
- opencode
    - https://opencode.ai/docs/sdk/ (typescript sdk. not applicable for our current case)
    - https://opencode.ai/docs/server (server docs)
    - @~/.opencode/sourceocde/opencode for actual source code

session 관리
- claude agent sdk 는 그냥 옵션으로 넘기면 됨
    - 그리고 기본적으로 resume, 실패시에만 new
- droid: droid cli 로 help 쳐가면서 찾아봐야 함
    - 없는 경우를 대비해서 세션자체를 다루지 않는 옵션도 필요 (이건 모든 sdk 에 적용 되어야 함)
- opencode https://opencode.ai/docs/server 문서에 있을것같음
    - 그리고 기본적으로 resume, 실패시에만 new

프롬프트 매니저
- 실행 프롬프트
    - '/execute' 형태의 프롬프트
    - 전문 형태의 프롬프트 (예시: @~/.claude/commands/execute.md)
    - 커스텀 프롬프트 주입가능 (replace or append (to one of above))
- 작업 완수 확인 프롬프트
    - '/architect' 형태의 프롬프트
    - 전문 형태의 프롬프트 (예시: @~/.claude/commands/architect.md)
    - 커스텀 프롬프트 주입 가능 (replace or append(to one of above)

작업 관리자
- 작업 완료 여부를 확인하는 코드 (모듈러하게, 쉽게 확장가능하고 변경 가능하고 주입해서 replace 가능해야 함)

중간에 쿼리 추가 입력 가능해야함 (지원하는것만. 대표적으로 claude agent sdk 와 opencode 가 가능. 얘네들은 차례가 되었을때 메시지 큐잉하도록 구현해야함)

ui
- tui support (based on textual, but support resizing windows, no terminal flickering, good ui, fancy ui)
    - shows text input at the bottom
    - remaing whole parts should render the current agent status, fancy ui.
        - 현재의 agentloop_sdk.py 와는 달리, 해당 에이전트의 모든 활동과 이벤트를 chat 부분에 보여주어야 함
- 기본적으로 opencode 와 유사한 느낌이어야 함
    - terminalcp 사용해서 직접 살펴볼것

- cli support (based on rich - that shares rich.console for whole application, but no intercepting or message queueing, only works as a daemon-like. uses logging for every events for both agent cli and our application, like when it was closed, when it was resumed, is resume succeed or not)

logging
- should always create .log files- appending it.
    - 기본적으로 같은 로그파일에 여러번 실행하더라도 append 되어야 함 (세션이 공유되는것이 맞다면)

이런식으로.

---

관련해서 첨부한 링크들과 내용들을 모두 살펴보고 resources/ 안에 기록해줘.
