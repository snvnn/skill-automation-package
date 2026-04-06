# Docs Information Architecture Analysis and Archive Plan

Note: This analysis was written before the first execution-stage move. Path references below reflect the pre-move layout used during the analysis pass.

## TL;DR

- 현재 리포 기준에서 사용자와 유지보수자가 계속 참조하는 핵심 문서는 루트 `README.md`이고, `docs/` 안에서는 `docs/publish-workflow.md`가 사실상 유일한 evergreen 운영 문서다.
- `docs/npm-wrapper-detailed-design.md`와 `docs/npm-wrapper-rollout-plan.md`는 아직 구현되지 않은 npm wrapper 작업을 위한 문서라서 active reference가 아니라 working set으로 다뤄야 한다.
- `docs/reviews/` 아래 문서들은 릴리스 시점의 리뷰와 후속 조치 기록이므로 보존은 하되 active 구조에서는 분리하는 것이 맞다.
- `docs/launch-post.md`는 엔지니어링 기준 문서가 아니라 커뮤니케이션 초안이므로 active docs에 두지 말고 working 또는 archive로 분리해야 한다.
- active docs는 작고 명확해야 한다. 이 리포에서는 `operations/` 중심으로 유지하고, in-flight 설계 문서는 `working/`, 과거 기록은 `archive/`로 분리하는 구조가 가장 자연스럽다.

## Current docs inventory and classification

판정 기준:

- `docs/` 전체 문서를 읽었다.
- 현재 리포의 실제 기준 문서와 구조를 맞춰 보기 위해 `README.md`, `package.json`, 그리고 `scripts/`, `assets/`, `templates/`, `tests/`의 현재 구성도 함께 확인했다.
- 현재 구현된 제품 현실은 Python 중심이다. `scripts/install.py`, `assets/.claude/tools/skill_agent.py`, `templates/`, `package.json`의 asset manifest가 실제 동작 기준이며, 아직 Node wrapper용 `bin/` 또는 유사 구현은 없다.

### Active reference docs

| Current path | 문서 목적 한 줄 요약 | 현재도 계속 참조해야 하는지 | 권장 상태 | 근거 |
| --- | --- | --- | --- | --- |
| `docs/publish-workflow.md` | stale 또는 dirty checkout에서도 안전하게 publish하는 maintainer runbook | Yes | Keep in active docs | `README.md`에서 직접 참조되고 있고, 현재 리포 운영 절차와 맞물린 evergreen 성격의 운영 문서다. 다만 문서 안의 2026-04-06 사례 기록은 장기적으로 archive로 분리하는 편이 더 명확하다. |

### Working docs

| Current path | 문서 목적 한 줄 요약 | 현재도 계속 참조해야 하는지 | 권장 상태 | 근거 |
| --- | --- | --- | --- | --- |
| `docs/npm-wrapper-detailed-design.md` | npm wrapper 도입을 위한 상세 설계와 결정 후보 정리 | Partial | Move to working docs | 구현되지 않은 기능의 설계 문서이며 현재 리포의 실제 동작 기준은 아니다. 향후 npm wrapper 작업이 재개되면 참고 가치가 높지만, 지금 active reference로 두면 현재 코드베이스의 truth와 혼동된다. |
| `docs/launch-post.md` | 패키지 소개용 외부 발표문 초안 | Partial | Move to working docs | 구현·설계·운영 기준 문서가 아니라 커뮤니케이션 초안이다. 아직 launch 작업이 살아 있다면 working 영역에 두는 것이 맞고, launch가 끝났다면 archive로 이동하면 된다. |

### Historical / archive candidates

| Current path | 문서 목적 한 줄 요약 | 현재도 계속 참조해야 하는지 | 권장 상태 | 근거 |
| --- | --- | --- | --- | --- |
| `docs/reviews/2026-04-06-v0.1.2-code-review.md` | `v0.1.2` 릴리스 대상 변경분에 대한 코드 리뷰 기록 | Partial | Archive | 릴리스 시점의 point-in-time review다. 현재 구현을 운영하는 기준 문서는 아니지만, 왜 어떤 후속 조치가 나왔는지 추적하는 근거로는 보존 가치가 있다. |
| `docs/reviews/2026-04-06-v0.1.3-follow-up-execution.md` | `v0.1.2` 리뷰 후 `v0.1.3`까지 실제로 수행한 조치와 검증 기록 | Partial | Archive | 완료된 실행 로그와 검증 증거를 담은 문서다. 현재 작업 기준서라기보다 완료 이력에 가깝고, 향후 감사나 회고를 위해 보존하면 충분하다. |

### Redundant / overlapping docs

| Current path | 문서 목적 한 줄 요약 | 현재도 계속 참조해야 하는지 | 권장 상태 | 근거 |
| --- | --- | --- | --- | --- |
| `docs/npm-wrapper-rollout-plan.md` | npm wrapper 작업의 단계별 rollout 계획과 리스크 정리 | Partial | Merge candidate | npm wrapper의 아키텍처 판단, Python 버전 정책, publish surface, open questions가 `docs/npm-wrapper-detailed-design.md`와 크게 겹친다. 유지하려면 execution checklist로 더 짧게 줄이거나, 상세 설계와 합쳐 하나의 working doc으로 정리하는 편이 낫다. |
| `docs/reviews/2026-04-06-follow-up-priorities.md` | `v0.1.2` 리뷰 이후 후속 작업 우선순위 정리 | No | Merge candidate | 문서 안의 모든 항목이 완료 처리되어 있고, 상당수 내용이 `docs/reviews/2026-04-06-v0.1.3-follow-up-execution.md`에 다시 나타난다. 독립 active 문서로 둘 이유는 약하고, archived retrospective로 합치거나 archive 내에서 superseded plan으로 처리하는 편이 명확하다. |

## Proposed active-doc structure

권장 active 구조는 작고 목적별로 명확해야 한다.

- `docs/operations/`
  - 현재 코드베이스를 유지·배포·운영할 때 반복 참조하는 runbook을 둔다.
  - 현재 기준으로는 `publish-workflow.md`가 이 영역의 핵심 문서다.
- `docs/design/`
  - 이미 구현되어 있고 README에 다 담기기 어려운 안정된 설계 문서만 둔다.
  - 아직 이 리포에서 반드시 필요한 문서는 없으므로 빈 디렉토리를 억지로 채울 필요는 없다.
- `docs/working/`
  - 아직 구현되지 않았거나 open question이 남아 있는 initiative 문서를 둔다.
  - npm wrapper 관련 문서는 `docs/working/npm-wrapper/` 같이 initiative 단위로 묶는 편이 적절하다.
- `docs/README.md` 또는 `docs/index.md`
  - active docs의 짧은 인덱스를 두고, working/archive는 별도 영역이라고 명시한다.
  - 이 파일은 "지금 무엇이 canonical reference인가"를 빠르게 보여주는 역할만 하면 된다.

이 리포의 성격상 active docs는 많아야 3개 안팎으로 유지하는 것이 좋다. 나머지는 working 또는 archive로 밀어내야 top-level docs가 다시 혼탁해지지 않는다.

## Proposed archive structure

archive는 삭제 구역이 아니라 현재 참조 구조에서 분리된 보존 구역으로 본다.

- `docs/archive/reviews/`
  - 릴리스 리뷰, QA 메모, point-in-time 검토 기록
  - 예: `2026-04-06-v0.1.2-code-review.md`
- `docs/archive/plans/`
  - 완료된 우선순위 문서, 완료된 실행 로그, superseded rollout plan
  - 예: `2026-04-06-follow-up-priorities.md`
  - 예: `2026-04-06-v0.1.3-follow-up-execution.md`
  - 향후 npm wrapper 문서가 완료되거나 폐기되면 여기에 이동
- `docs/archive/communications/`
  - launch post, announcement draft, 외부 공유용 초안
  - 예: `launch-post.md`

현재 상태에서 가장 단순한 방향은 `archive/reviews`, `archive/plans`, `archive/communications` 3갈래면 충분하다. 이보다 더 세밀한 taxonomy는 지금 단계에서는 과하다.

## Archiving policy

### Archive로 보내야 하는 기준

- 날짜, 버전, 특정 릴리스에 강하게 묶여 있는 문서
- 현재 구현/운영의 기준이라기보다 당시 판단 근거나 완료 기록을 남기는 문서
- README나 더 최신 문서에 의해 이미 실질적으로 superseded된 문서
- 앞으로도 가끔 근거 확인은 필요하지만, 일상적인 참조 빈도는 낮은 문서

### Active 상태로 남겨야 하는 기준

- 현재 코드베이스와 실제 운영 절차를 직접 설명하는 문서
- install, publish, maintenance처럼 반복 수행되는 작업에서 계속 참조되는 문서
- README 또는 다른 canonical 문서에서 직접 링크할 가치가 있는 문서
- 내용이 현재 구현 상태와 충돌하지 않고, 문서 하나만 읽어도 현재 truth를 이해할 수 있는 문서

### Working docs가 active docs로 승격되는 조건

- 문서가 다루는 기능이나 절차가 실제로 구현되었거나 팀의 승인된 기준이 되었을 때
- open question보다 확정된 정책과 실제 코드/테스트 상태가 더 많을 때
- README 또는 docs index에서 "현재 참고 문서"로 링크할 준비가 되었을 때
- 문서 내용이 speculative plan이 아니라 유지보수자가 반복 참조할 stable guidance가 되었을 때

### Merge candidate를 실제 병합하기 전에 확인해야 할 조건

- 두 문서의 대상 독자와 목적이 실제로 같은지 확인할 것
- 서로 다른 정책이나 open question을 아직 unresolved 상태로 함께 섞지 말 것
- 병합 후 canonical 문서가 무엇인지 한 개로 명확하게 정할 것
- 병합 과정에서 과거 의사결정 근거나 검증 증거가 사라지지 않도록 원본 archive 또는 링크를 남길 것

## Merge / consolidation candidates

### 1. npm wrapper 문서 쌍

- 대상: `docs/npm-wrapper-detailed-design.md`, `docs/npm-wrapper-rollout-plan.md`
- 문제: 아키텍처 판단, Python 버전 정책, publish surface, test strategy, open questions가 크게 겹친다.
- 권장 방향:
  - npm wrapper 작업이 곧 시작된다면 `docs/working/npm-wrapper/` 아래로 묶고, 하나는 canonical design doc, 다른 하나는 짧은 execution checklist로 축소한다.
  - 아직 작업 착수가 불확실하다면 두 문서를 바로 합치기보다 canonical 문서 후보를 먼저 정하고 나머지는 archive-ready draft로 다듬는 편이 낫다.

### 2. v0.1.2 review follow-up 문서 쌍

- 대상: `docs/reviews/2026-04-06-follow-up-priorities.md`, `docs/reviews/2026-04-06-v0.1.3-follow-up-execution.md`
- 문제: 우선순위 문서의 완료 항목이 실행 로그에서 다시 설명되어 역사적 서사가 중복된다.
- 권장 방향:
  - active로 둘 필요는 없다.
  - archive 안에서 둘 다 보존하되, 나중에 필요하면 하나의 retrospective summary로 묶고 원본은 그대로 보존한다.

## Risks and cautions

- `docs/publish-workflow.md`는 현재 active로 둘 가치가 있지만, 문서 안에 2026-04-06 사례 기록이 섞여 있어 evergreen 절차와 historical note가 혼재한다.
- npm wrapper 문서를 top-level `docs/`에 그대로 두면 아직 구현되지 않은 계획이 현재 truth처럼 보일 수 있다.
- review 문서를 active 영역에서 분리하지 않으면 완료된 과거 작업과 현재 기준 문서가 한 레벨에 섞여 탐색 비용이 커진다.
- `launch-post.md`는 엔지니어링 문서가 아니라서 상태를 빨리 결정하지 않으면 계속 top-level noise로 남는다.
- merge는 문서 수를 줄이는 데 유용하지만, 의사결정 근거를 지워버리면 나중에 왜 그런 판단을 했는지 복원하기 어려워진다.

## Immediate TODO list

1. active docs의 경계를 먼저 확정한다.
이유: 현재 기준 문서와 기록 문서의 경계가 먼저 정해져야 이후 이동 기준이 흔들리지 않는다.

2. `docs/operations/`, `docs/working/`, `docs/archive/` 중심의 목표 구조를 문서 차원에서 승인한다.
이유: 실제 이동이나 rename은 합의된 구조가 있어야 일관되게 진행된다.

3. `docs/publish-workflow.md`를 active docs의 canonical 운영 문서로 지정하고, 안에 섞인 dated note를 분리할지 결정한다.
이유: 현재 `docs/`에서 실질적으로 계속 참조할 문서를 먼저 고정해야 active surface를 작게 유지할 수 있다.

4. npm wrapper 문서 두 개 중 어떤 문서를 canonical working doc으로 둘지 결정한다.
이유: 구현 전 단계에서 기준 문서가 둘이면 이후 작업이 분산되고 중복 업데이트가 발생한다.

5. `docs/reviews/` 문서들을 archive-bound 세트로 묶고 보존 정책만 먼저 확정한다.
이유: 과거 기록은 버리지 않되 active 탐색 경로에서 빼는 것이 이번 정리의 핵심이다.

6. `docs/launch-post.md`가 아직 살아 있는 launch 작업인지, 아니면 archive 대상인지 상태를 확인한다.
이유: 이 문서는 engineering reference가 아니므로 상태 판정이 끝나야 적절한 위치가 결정된다.

7. docs 인덱스 문서의 필요 여부를 결정한다.
이유: 구조를 바꿔도 canonical entrypoint가 없으면 다시 top-level 혼잡이 생긴다.

8. 실제 이동/병합 작업은 별도 단계로 분리하고, 이번 분석 문서를 기준 승인안으로 사용한다.
이유: 분석과 구조 변경을 한 번에 섞으면 과도한 문서 이동이나 잘못된 병합을 유발할 수 있다.
