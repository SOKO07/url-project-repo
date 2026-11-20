# 구현 계획

SPEC.md 기준. 테스트를 먼저 쓰고, 구현은 그 다음에 한다.

1. **base62** (끝남, 단계 1): `src/base62.py`, `tests/test_base62.py`.
2. **테스트 작성** (단계 4a): SPEC 6장의 경계 사례를 `tests/test_hash_table.py`, `tests/test_shortener.py`로 옮긴다. 구현은 하지 않는다.
3. **해시 테이블** (`src/hash_table.py`): `Node(key, value, next)`, 슬롯 리스트, Horner 해시(`hash_steps`로 단계별 값도 노출), `put/get/find/__len__/__contains__/load_factor`, 적재율 초과 시 재해시. `dict`·`set`·`hash()` 금지.
4. **단축기** (`src/shortener.py`): 일련번호 → `base62.encode`. URL→코드, 코드→URL 두 테이블. URL 검증. 코드를 URL 해시로 만들지 않는다(충돌 방지).
5. **규칙 파일** (단계 5): `.github/copilot-instructions.md`, grep으로 금지어 확인.
6. **실험** (단계 6): `experiments/probe_experiment.py`, `results.csv`, SVG. 시드를 고정한다.
7. **서버** (단계 7): `src/server.py`, `/`, `POST /shorten`, `/<code>`, `/table`. `X-Forwarded-*` 처리.
8. **숙제**: `LinearProbingTable`(같은 인터페이스), 테스트, 두 테이블 비교 실험, `/table` 확장.

## 검토 메모
- URL→코드를 `dict`로 저장하지 않는다(자체 해시 테이블 사용).
- 코드는 해시가 아니라 일련번호다.
- 테스트가 구현보다 먼저다. 구현 중 테스트를 고치지 않는다.
