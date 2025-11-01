# 사용자 원본 메시지 (토씨 하나 틀리지 않고 그대로)

## 메시지 1
```
현재의 sisyphus plan, sisyphus verify phase execute phase 다 지우고서 그냥

sisyphus task 로 통일하고싶어. 단 현재 있는 애들은 이름이 바뀌는거고 기능 자체는 있어야 함.

task master 가 제공하는 sisyphus 에 있는 비슷한 기능이지만 advanced 한 부분들을 참고해서 어떤식으로 새로 바뀔 수 있을지 상상하고 나한테 제시해볼래 ?
```

## 메시지 2
```
마이그레이션 맵

  | 기존 명령어                 | 새 명령어           | 비고      |
  | --------------------------- | ------------------- | --------- |
  | plan get task --id X        | task show X         | 간결화    |
  | plan get task --current     | task current        | 간결화    |
  | plan get task --next        | task next           | 간결화    |
  | plan lint                   | task lint           | 통일      |
  | execute-phase get-overview  | task overview       | 통일      |
  | execute-phase continue-work | task continue       | 통일      |
  | execute-phase bash-verify X | task verify bash X  | 체계화    |
  | execute-phase llm-verify    | task verify llm     | 체계화    |
  | execute-phase manual-verify | task verify manual  | 체계화    |
  | verify-phase bash-verify    | task verify bash    | 중복 제거 |
  | verify-phase llm-verify     | task verify llm     | 중복 제거 |
  | ❌ 없음                      | task add            | NEW       |
  | ❌ 없음                      | task update         | NEW       |
  | ❌ 없음                      | task parse-prd      | NEW       |
  | ❌ 없음                      | task expand         | NEW       |
  | ❌ 없음                      | task dep add/remove | NEW       |

전반적으로 좋은데, plan lint 는 그대로 두는게 맞겠다.
그리고 plan init 도 새로 두는게 맞겠음.

task verify bash X 는 굳이 필요없을거같고 그냥 task verify bash 를 입력하면 current task 에 해당하는 verification 이 실행되고 알아서 마킹되고 체킹되고 그 결과가 반환되는 느낌으로. 그리고 실패 혹은 성공시에 어떤값을출력해줄지도 고민해야할거같아.
또한 task verify llm 의 경우에는 그냥 저렇게 두면 안될거같구 마킹하는 형태로써의 기능이 되어야 할 거같은데. 이게 어쨌든 orchestrator 를 위한 verification 스펙을 잘 확인하는거랑 마킹하는 기능 두가지가 필요하면서도, 확인 자체도 여러개일수가있으니까 또 여러개를 하나하나 확인시키게 해줘야하고(한번에 하나만 집중하도록) 또 external llm 이 verify 하는거면 그냥 저거 task verify bash 처럼 task verify llm 하면 바로 됐으면 좋겠는 그런 마음이라 이게 인터페이스가 햇갈리네. task verify manual 도 조회를 할 수 있게 해주고 마킹할 수 있게 해주는거가 따로 필요할듯, 대신 이거는 mark 시에 evidence 를 항상 작성을 시켜야할거같아 이건 verify llm 도 마찬가지.

그 외에 기존에 없는것들은 일단은 제외하자.

네의견좀 줄래 ?
```

## 메시지 3
```
evidence 필수라니까 그리고 status 조회는 좋은거같애

근데 씨발 내가 물어본걸 네가 나한테 또물어보면 어떻게해

llm verify 의 경우에는 external llm verify 도 있고, orchestrator 의 직접 verification 을 위한 그 내용 확인도 필요한데 이게 또 여러개일수도있으니까 순차적으로 하나씩 조회가가능하고 마킹도 하나씩되어야 한다니까? 한번에 다 보여지게되면은 안되고
```

## 메시지 4
```
괜찮네. 근데 bash verify 의 경우에는 실패하면 구체적으로 어떻게 왜 실패했는지를 보여줘야할거같은데
```

## 메시지 5 (plan 명령어 실행 후)
```
@ai-todolist.md 에 그렇게 우리가 말한대로 기존거 지우거나 정리하고 이런식으로 새로 정리하는 계획서 작성. 특히 어떤게 어떻게 바뀌고 어떤 기능이 새로 추가되고 이런것들이 오버뷰로써 배경이나 작업 흐름에 잘 드러나도록 작성하게 해주고, 또 출력 형식같은것들도 각 태스크별로 꼭 필요한 레퍼런스 일테니 이를 참고해서 적게해줘. 또한 .sisyphus/resources/spec-document-example.yaml 를 테스트용도로써 검증용으로써 항상 활용하도록 하게해주고, 당연히 그 특성상 지금 작업계획서 내에 기능들이 잘 동작하고 하는것들 확인하고 검증하는 기능들 여러가지가 필요하니만큼 그런것들은 ./temp 밑에다가 만들어서 사용하고 잘 정리할 수 있도록 계획서를 구상해줘.

모든 기능들이 실제 유효한 yaml 파일로서 테스트 되고 확인될 수 있도록 해줬으면 해.

그리고 또한 몇가지 조사도 하고서 작성해줬으면 좋겠는데,
만약 by: 가 없을경우 그 기본값은 orchestrator 여야 하며, by external 이 구현되지 않았을경우 verification phase 처럼 동작하도록 구현해야하며, external orchestrator 는 'sisyphus plan overview' (task overview 라고 내가 말했었는데 plan 이 맞는거같아) 의 내용과 그 태스크의 내용 (sisyphus task current?) 의 출력값 그리고 저 verification 안의 instruction 과 함께 같이 최초 프롬프트가 제공될 수 있도록 해야하며, 또한 그 피드백 또한 같이 출력이 되어야함 - sisyphus task verify llm 했을떄. 그리고 verify llm 이 by 가 external 인거랑 orchestrator  인거랑 섞일수가있으니까 이거에대한 핸들링도 어떻게 해야할지 ultrathink 하도록 하고
사실상 현재의 plan 관련 기능을 모두 지우고서 새로 작성하는 느낌으로 하고, 그러니만큼 좋은 구조와 아키텍쳐에대해서 codex 와 이 배경들을 전부 다넘기고해서 상의하고 설계하고 질문하면서 만들어주고,

또한 todo 안의 작업들이 references 도 가질 수 있고, 이게 포인터일수도있고, 직접 그 자체로 하나일수도있고, description 도 가질 수 있도록 스펙도 만들어져야하며,
그 안에서 nested 구조로 표현되는 children 의 경우 simplified todo 같은 스펙의 느낌으로 한번 더의 nested 는 지원되지는 않지만, title, description, reference, 등의 내용들도 가질 수 있도록 해야해
그리고 각 todo 안에 parallel group 을 둬서 병렬 실행 가능 그룹들은 같은 그룹에 묶이도록 표현할 수 있어야 하며 이것들의 유효성 검사도 린터가 지원해야할 스펙이야.

그리고 depends_on 이라는 키도 맨 위에 들어가도록 (optional 로) 스펙 구조를 추가해줘 이거는 depends on 하고서 cwd 기준 relative file path 를 받아야하고 linter 는 이게 실제로 존재하는 유효한 형식의 내용인지까지도 검사할 수 있어야해

그리고 plan 문서는 위치 자체는 지정이 가능하도록 하되 기본적으로 그냥 init 하게 되면 .sisyphus/tasks/ 밑에 들어가게 해줘

그래서 저 안의 모든 yaml 을 읽어서 동작하는게 기본 동작이되 이제 직접 파일 패스 넘길수도 있어야하고, dependes on 을 통해 의존성과 병렬 실행 가능 여부들에 대해서 표현할 수 있어야 하며, 현재 작업중인 작업계획서가 어떤것인지는 그럼 어떻게 판단하냐?
그거는 .sisyphus/status.json 을 통해서 표현이 가능하도록 해서 이걸 참조해서 저런 동작들이 이뤄질 수 있도록 해줘야 할 거같아. 그래서 sisyphus reset 의 동작도 당연히 달라져야겠고.

복잡하니까 codex 랑 상의 진짜 많이하고, 혹시나 내가말한 부분중에 애매하거나 빠뜨린 부분이있다면은 나한테 주저말고 질문해줘.
```

## 메시지 6
```
depends_on: ./other-plan.yaml  # 이게 의미하는 것이?
  - 질문: depends_on이 "이 plan YAML 파일이 다른 plan YAML 파일에 의존한다"는 의미인가요?
  - 예시: feature-b.yaml이 feature-a.yaml에 depends_on하면, feature-a가 완료되어야 feature-b를 시작할 수 있다는 뜻인가요?
  - 아니면: Todo 내부에서 파일(소스코드)에 대한 의존성을 표현하는 건가요?

dependes on 은 일단 배열 형태로 표현되어야해
네가 말한 예시가 맞아. feature a 가 완료되지 않으면 feature b 가 진행될 수 없지.
reference 는 ref id 로 재사용성 참조를 할 수 도 있고, 아니면 그 안에 직접 텍스트를 넣어서 그냥 이거 참고해 정도의 레퍼런스라는 이름으로 이중적 의미가 될 수 있음을 표현해야한다고 한거야 내가말한게.
세개의 yaml 은 독립적일수도, 쪼개어진 의존적인걸수도있어. 그러니까 그걸 depends on 으로 표현하는거야.
status json 의 구조는 git worktree 와 함께 사용되는 느낌으로 해서 하나의 워크트리 당 하나의 작업계획서 정도로 표현이되어야하고, 마찬가지로 이것도 이제 린트나 이런게 필요할거같기도하고. 세팅하는 도구도 필요할거같아 왜냐면 의존성 관계를 갖고서 유효한 동시작업들만 진행이 되어야 한다고 나는 생각하거든. status.json 이 current task id 를 가질필요는 없다고봐 일단은. 왜냐하면 이거는 그냥 문서 보면 될테니까.

sisyphus reset 을 하게 되면 notepad sessions logs 이걸 지우는게 맞고, sisyphus reset --include-task-specs 를 하게 되면 task 내용도 다같이, json 도 다같이. 시지프스의 흔적자체를 하나하나 다 지우는 그런 느낌으로 구성해주면 될 것같아.
지금 생각난건데, notepad.md 도 .sisyphus/notepad.md 로 들어가게해주고 sessions 랑 logs 도 마찬가지로 되게 해주라.

  6. Children nested 제한

  todos:
    - id: "1"
      children:
        - id: "1.1"
          title: "Subtask"
          children: []  # 이건 지원 안함?
  - 확인: Children은 1단계만 nested 가능 (children의 children은 불가)?

이건 네가 말한게 맞아. 참고로 우리가 지금 작업할거는 아닌데, 작업범위아니라고 분명히 말했다?

sisyphus work 한 뒤에 yaml 파일의 이름을 제시해야해 예를들면 feature-a 혹은 feature-a.yml 혹은 feature-a.yaml 이라고 말하면 그걸 status.json 을 업데이트 해야해 당연히 그 의존관계 검사도 해야하고

그리고 의존관계 검사를 해서 순환하게 된다거나 영원히 닿을수 없다거나 이러한 의존관계의 전형적인내용들도 그 린터가 검사를 해줄 수 있어야겠다 싶네. 친절하고 명확한 에러메시지와 함께.
또한 의존관계에 대한 내용을 그래프로 해서 그릴 수 있게 해주는 기능도 하나 같이 구상해줘. 혹시나 질문 또 있으면 또 물어보렴.
```

## 메시지 7
```
references 는 무조건 밑으로 가게 해줬으면 좋겠어 그래야 작업 계획의 전반적인 흐름이 사람이 딱 봤을떄 이해하기가 쉽잖아.

sisyphus work 자체는 지금 수정하지않을거기때문에 무시해줘.

sisyphus plan graph 가 맞는거같고, 출력형식은 네 추천이 맞는거같아.

그리고 하나만 더. sisyphus plan convert-legacy {path} 로 해서 지금의 플랜 생성자가 생성하는 형태로 .md 형태로 컨버팅해서 새로 생성해주는 유틸만드는 계획까지 포함해줘.

내가 말한게 많아서, 내가 말한내용들 as-is 로 user-requests-initial.md 로 일단 먼저 작성을 하고 나한테 말해줄래 ? 혹시 질문있으면 또 물어봐
```

---

# 요구사항 정리 (엄밀하게)

## 1. 명령어 구조 재설계: `sisyphus task` 통합

### 1.1 기본 방향
- 기존 `plan`, `execute-phase`, `verify-phase` 명령어 모두 삭제
- `sisyphus task` 중심으로 통일
- **기능 자체는 유지**, 이름만 변경

### 1.2 마이그레이션 맵

| 기존 명령어                   | 새 명령어                                        | 변경 사항                         |
| ----------------------------- | ------------------------------------------------ | --------------------------------- |
| `plan get task --id X`        | `task show X`                                    | 간결화                            |
| `plan get task --current`     | `task current`                                   | 간결화                            |
| `plan get task --next`        | `task next`                                      | 간결화                            |
| `plan lint`                   | `plan lint`                                      | **유지** (변경 없음)              |
| ❌ 없음                        | `plan init`                                      | **NEW**                           |
| `execute-phase get-overview`  | `plan overview`                                  | 통일 (task → plan으로 수정)       |
| `execute-phase continue-work` | `task continue`                                  | 통일                              |
| `execute-phase bash-verify X` | `task verify bash`                               | Task ID 불필요, current task 기준 |
| `execute-phase llm-verify`    | `task verify llm` + `task verify llm mark <id>`  | 조회/마킹 분리                    |
| `execute-phase manual-verify` | `task verify manual` + `task verify manual mark` | 조회/마킹 분리                    |
| `verify-phase bash-verify`    | `task verify bash`                               | 중복 제거 (execute-phase와 통합)  |
| `verify-phase llm-verify`     | `task verify llm`                                | 중복 제거 (execute-phase와 통합)  |

**질문**: Task Master의 add/update/parse-prd/expand/dep 기능은?
**결정**: 일단 제외 (기존에 없는 것들)

---

## 2. Verification 명령어 상세 설계

### 2.1 `task verify bash`
```bash
sisyphus task verify bash
```

**동작**:
1. Current task 조회
2. `verification_spec[*].bash` 전체 실행
3. 성공 시: 자동 마킹 (`verified=true`, `verified_at`, `verification_evidence`)
4. 실패 시: **구체적 출력**

**실패 출력 요구사항**:
- 어떤 커맨드가 실패했는지
- Expected vs Actual exit code
- Stdout/Stderr 실제 내용
- 실패 요약 (한 줄)
- 재시도 가이드

**질문**: Task ID를 인자로 받아야 하나?
**결정**: 불필요. Current task 기준으로 동작

---

### 2.2 `task verify llm`

**조회/실행 모드**:
```bash
sisyphus task verify llm
```

**동작**:
1. Current task의 `verification_spec[*].llm_judge` 확인
2. **첫 번째 미검증 항목만 출력** (여러 개여도 하나씩 집중)
3. `by` 필드 처리:
   - `by: external` → 자동 실행 + 자동 마킹
   - `by: orchestrator` (또는 `by` 없음) → instruction 출력, 마킹 대기
4. `by: external`인 경우 프롬프트 구성:
   - `sisyphus plan overview` 출력
   - `sisyphus task current` 출력
   - verification instruction
   - 피드백 내용
   - 위 모두를 최초 프롬프트로 제공

**수동 마킹 모드**:
```bash
sisyphus task verify llm mark <verify-id> --evidence "..."
```

**동작**:
- `<verify-id>` 찾아서 마킹
- `evidence` 필수 (없으면 에러)

**질문**: by가 external과 orchestrator 섞이면?
**결정**: 순차적으로 하나씩 처리 (첫 번째 미검증 항목만 출력)

---

### 2.3 `task verify manual`

**조회 모드**:
```bash
sisyphus task verify manual
```

**동작**:
- Current task의 manual verification 상태 출력
- 미검증 항목 표시

**마킹 모드**:
```bash
sisyphus task verify manual mark --evidence "..."
```

**동작**:
- `evidence` 필수 (없으면 에러)
- `orchestrator_manually_verified=true` 업데이트

---

### 2.4 `task verify status`
```bash
sisyphus task verify status
```

**동작**:
- Current task의 전체 verification 상태 조회
- Bash/LLM/Manual 각각 진행률 표시

**질문**: 새로 추가할 명령어인가?
**결정**: Yes, 전체 상황 파악용

---

## 3. YAML 스키마 재설계 (v3.0)

### 3.1 파일 구조 변경
```
.sisyphus/
  ├── tasks/              # NEW - plan YAML들
  │   ├── feature-a.yaml
  │   ├── feature-b.yaml
  │   └── bugfix-123.yaml
  ├── status.json         # NEW - 현재 작업 중인 plan 추적
  ├── notepad.md          # 이동 (기존: ./notepad.md)
  ├── sessions/           # 이동 (기존: ./sessions/)
  └── logs/               # 이동 (기존: ./logs/)
```

**질문**: 기존 파일들 위치 변경?
**결정**: Yes, `.sisyphus/` 하위로 통합

---

### 3.2 YAML 스키마 구조

```yaml
# .sisyphus/tasks/feature-auth.yaml

depends_on:  # NEW - 배열 형태, optional
  - ./feature-database.yaml
  - ./feature-user.yaml

metadata:
  created_at: "..."
  format_version: "3.0"  # NEW version

user_request:
  original: "..."

objectives:
  core: "..."
  detailed: []

background:
  current_situation: "..."
  reason_for_change: "..."
  changes_to_make: "..."

required_background:
  description: "..."
  file_structure: null
  references: []

status:
  execution:
    started: false
    completed: false
  work_mode:
    current_task_id: null  # status.json에서 제거될 예정
  progress:
    total_tasks: 0
    completed: 0

todos:
  - id: "1"
    title: "..."
    description: "..."  # NEW - optional
    status: "pending"
    parallel_group: null  # 기존 유지
    references:  # NEW - 혼합 가능
      - ref_id: "ref_db_pattern"  # 재사용
      - type: "inline"
        text: "이거 참고해"  # 직접 텍스트
    verification_spec: [...]
    children:  # Simplified Todo
      - id: "1.1"
        title: "..."
        description: "..."  # NEW
        references: [...]  # NEW
        # children 불가 (1단계만 nested)

# References는 맨 아래 (전반적인 흐름 이해를 위해)
references:
  ref_db_pattern:
    type: file
    path: models/Product.ts
    search_for: "@Column decorator"
  ref_api_docs:
    type: url
    url: "https://..."
```

**질문**: depends_on은 plan YAML 간 의존성?
**결정**: Yes. feature-a.yaml 완료되어야 feature-b.yaml 시작 가능

**질문**: references는 ref_id 재사용 + inline 혼합?
**결정**: Yes. ref_id로 하단 references 섹션 참조 OR inline으로 직접 텍스트

**질문**: children은 1단계만 nested?
**결정**: Yes. children의 children은 불가

**질문**: references 위치?
**결정**: 무조건 YAML 하단 (전반적인 흐름 이해를 위해)

---

## 4. status.json 설계

```json
{
  "current_plan": ".sisyphus/tasks/feature-auth.yaml",
  "worktree_path": "/Users/.../sisyphus"
}
```

**개념**: Git worktree와 함께 사용
- 하나의 worktree 당 하나의 작업계획서
- `current_task_id` 불필요 (문서 보면 됨)

**질문**: current_task_id 필요?
**결정**: 불필요. YAML 문서 보면 됨

**질문**: sisyphus work 명령어 수정?
**결정**: 지금 수정하지 않음 (무시)

---

## 5. Plan Linter 확장

### 5.1 기존 검증
- YAML 스키마 검증

### 5.2 새로 추가할 검증

**depends_on 검증**:
- 파일이 실제로 존재하는지
- 유효한 YAML 형식인지
- **순환 의존성 (circular dependency)** 감지
- **영원히 닿을 수 없는 의존성 (unreachable)** 감지
- 친절하고 명확한 에러 메시지

**parallel_group 유효성**:
- 같은 그룹 내 task들의 독립성 검사

**references 검증**:
- ref_id가 references 섹션에 정의되어 있는지
- file type의 경우 파일 존재 여부 확인

**질문**: Linter에 의존성 검증 추가?
**결정**: Yes. 순환/unreachable 감지 + 명확한 에러 메시지

---

## 6. 의존성 그래프 출력

```bash
sisyphus plan graph [--format ascii|mermaid|png]
```

**기본 (ASCII)**:
```
feature-database.yaml
  └─> feature-auth.yaml
      └─> feature-posts.yaml
```

**Mermaid** (--format mermaid):
```
graph TD
  A[feature-database.yaml] --> B[feature-auth.yaml]
  B --> C[feature-posts.yaml]
```

**PNG** (--format png):
- Graphviz로 deps.png 생성

**질문**: 출력 형식?
**결정**: ASCII 기본 + --format으로 mermaid/png 선택

---

## 7. Legacy 변환 도구

```bash
sisyphus plan convert-legacy <path>
```

**동작**:
- 기존 `/plan` 명령어가 생성하는 `.md` 형태
- 새로운 YAML v3.0 형식으로 변환
- `.sisyphus/tasks/` 하위에 생성

**질문**: 변환 방향?
**결정**: .md → YAML (플랜 생성자가 생성하는 .md 형태를 YAML로)

---

## 8. `sisyphus reset` 동작 변경

**기본**:
```bash
sisyphus reset
```
**삭제 대상**:
- `.sisyphus/notepad.md`
- `.sisyphus/sessions/`
- `.sisyphus/logs/`

**전체 삭제**:
```bash
sisyphus reset --include-task-specs
```
**추가 삭제**:
- `.sisyphus/tasks/`
- `.sisyphus/status.json`
- 시지프스의 흔적 전체 제거

**질문**: notepad/sessions/logs 위치 변경?
**결정**: Yes. `.sisyphus/` 하위로 이동

---

## 9. `plan init` 명령어

```bash
sisyphus plan init
```

**동작**:
- `.sisyphus/tasks/` 디렉토리 생성
- 기본 template YAML 생성 (위치: `.sisyphus/tasks/`)

**질문**: 기본 위치?
**결정**: `.sisyphus/tasks/`

---

## 10. Verification `by` 필드 기본값

```yaml
verification_spec:
  - id: "verify_1"
    llm_judge:
      - by: orchestrator  # 기본값 (명시 안 하면 orchestrator)
        instruction: "..."
      - by: external
        instruction: "..."
```

**by 없으면**: `orchestrator`가 기본값

**by: external 미구현 시**: verification phase처럼 동작

**by: external의 경우 프롬프트**:
- `sisyphus plan overview` 출력
- `sisyphus task current` 출력
- instruction
- 피드백
- 위 모두를 최초 프롬프트로 제공

**질문**: by 기본값?
**결정**: orchestrator

**질문**: task overview → plan overview?
**결정**: Yes. plan overview가 맞음

---

## 11. 테스트 검증

- `.sisyphus/resources/spec-document-example.yaml` 파일을 테스트/검증용으로 활용
- 모든 기능이 실제 유효한 YAML 파일로서 테스트되고 확인될 수 있도록
- 검증용 임시 파일은 `./temp/` 하위에 생성하여 정리

**질문**: 테스트 파일 위치?
**결정**: `.sisyphus/resources/spec-document-example.yaml` + `./temp/`

---

## 12. 아키텍처 설계

- **현재 plan 관련 기능을 모두 삭제하고 새로 작성**하는 느낌
- Codex와 상의하여 좋은 구조와 아키텍처 설계
- 애매하거나 빠뜨린 부분이 있으면 질문

**질문**: 기존 코드 재사용?
**결정**: 새로 작성하는 느낌 (clean slate)

---

## 정립되지 않은 부분 (생략)

없음 - 모든 질문에 대한 결정 완료
