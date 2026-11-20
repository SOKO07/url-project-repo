# 과제2 · 에이전트와 함께 만드는 URL 단축기

2026-2 고급알고리즘(SIT2001-01) 과제2. 직접 만든 해시 테이블(분리 연쇄, 숙제로 선형 탐사)
위에 URL 단축 서비스를 만든다. `dict`·`set`·내장 `hash()`는 쓰지 않고, 표준 라이브러리만 쓴다.

## 실행 방법

Python 3.10 이상. 아래는 모두 저장소 루트에서 실행한다. `make`가 있으면 `make test`·`make serve`·`make experiment`도 된다
(Windows처럼 `python3`가 없으면 `make PYTHON=python test`).

```powershell
# 테스트
python -m unittest discover -s tests

# 웹 서버 (http://localhost:8000). 선형 탐사 테이블로 돌리려면 --table probing
python src/server.py --port 8000
python src/server.py --table probing

# 실험 (experiments/ 에 csv와 svg를 쓴다)
python experiments/probe_experiment.py
python experiments/compare_experiment.py
```

서버는 `/`(입력 폼), `POST /shorten`, `/<코드>`(원래 주소로 302), `/table`(해시 테이블 보기)를 제공한다.
`/table`에서 노드를 펼치면 Horner 해시 계산 과정이 나온다. 짧은 링크의 주소는
`X-Forwarded-Host`/`X-Forwarded-Proto`가 있으면 그것을 쓴다.
같은 Wi-Fi의 휴대폰에서는 `http://<PC의 IP>:8000`으로 연다(서버는 모든 인터페이스에서 받는다. 끝나면 Ctrl+C로 끈다).

## 구성

| 경로 | 내용 |
| --- | --- |
| `SPEC.md` · `PLAN.md` | 명세(AI 초안), 구현 계획 |
| `src/base62.py` | 정수 ↔ base62 (`0-9a-zA-Z`) |
| `src/hash_table.py` | 분리 연쇄 해시 테이블, Horner 해시 |
| `src/probing_table.py` | 선형 탐사 해시 테이블 (같은 인터페이스) |
| `src/shortener.py` | 일련번호 → base62 코드, URL↔코드 테이블 |
| `src/server.py` | `http.server` 웹 서비스 |
| `tests/` | `unittest` (단축기·서버 테스트는 두 테이블 모두에 돌린다) |
| `experiments/` | 적재율 실험(`results.csv`, `chart.svg`), 연쇄 대 탐사 비교(`compare_results.csv`, `compare_chart.svg`) |
| `.github/copilot-instructions.md` · `CLAUDE.md` | 에이전트 규칙 파일 |

## 실험 결과 (M = 4093, 시드 2026)

적재율 0.9에서 탐색 비용(비교한 노드 수 또는 살펴본 슬롯 수):

| 방식 | 성공 탐색 | 실패 탐색 |
| --- | --- | --- |
| 분리 연쇄 (이론 1+α/2, α) | 1.44 | 0.91 |
| 선형 탐사 (이론 5.5, 50.5) | 5.21 | 39.4 |

## 작업 기록과 AI 사용

단계마다 이슈(#1~#8), `feature/<번호>-<이름>` 브랜치, `Step N: … (#번호)` 커밋으로 남겼다.
구현은 에이전트(Claude Code, 로컬 Windows)가 했고 진행 상황은 이슈 댓글에 있다.
`SPEC.md`는 에이전트 초안이며 사용자가 검토 후 그대로 확정했다. 보고서는 사용자가 직접 쓴다.
