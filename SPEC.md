# 명세: URL 단축기

> 이 문서는 에이전트(Claude Code)가 쓴 **초안**이다. 사용자가 읽고 고친 뒤 확정한다.

## 1. 무엇을 만드는가

긴 URL(`http://` 또는 `https://`)을 입력하면 짧은 코드(`1`, `2`, ..., `a`, ...)를 돌려주고,
그 코드로 접속하면 원래 주소로 이동하는 URL 단축 서비스. 웹 페이지에서 쓸 수 있고,
저장은 직접 구현한 해시 테이블로 한다.

## 2. base62 인코딩

- `encode(n)`: 정수 `n >= 0` → 문자열. 글자 순서는 `0-9`, `a-z`, `A-Z`.
- `decode(s)`: `encode`의 역함수.
- `encode(0) == "0"`. 빈 문자열을 돌려주지 않는다.
- 음수·정수가 아닌 값(`bool` 포함): `encode`는 `ValueError`/`TypeError`.
- 빈 문자열이나 알파벳 밖 글자: `decode`는 `ValueError`.

## 3. 해시 테이블 (`src/hash_table.py`)

- 충돌 처리: **분리 연쇄**(슬롯마다 연결 리스트). 노드는 직접 만든 클래스.
- 해시 함수: Horner 방식 `h = (31 * h + ord(c)) mod M`, 처음 `h = 0`.
- 처음 크기 `M = 11`. 적재율이 `max_load`(기본 0.75)를 넘으면 크기를 약 2배(다음 홀수)로 늘리고 다시 넣는다.
  `max_load=None`이면 늘리지 않는다(실험용).
- 인터페이스: `put(key, value)`(같은 키면 값 교체), `get(key, default=None)`,
  `find(key)`(비교한 노드 수와 값을 돌려줌), `len(t)`, `key in t`, `load_factor`.
- 쓰면 안 되는 것: `dict`, `set`, 내장 `hash()`. 표준 모듈만 쓴다.

## 4. 단축기 (`src/shortener.py`)

- `shorten(url)`: 코드를 돌려준다. 코드는 **일련번호**(1부터)를 base62로 바꾼 값이며, URL의 해시값이 아니다.
- 같은 URL을 두 번 넣으면 **같은 코드**를 돌려주고 번호를 쓰지 않는다.
- `expand(code)`: 원래 URL. 없는 코드는 `None`.
- 잘못된 URL(`http://`/`https://`로 시작하지 않음, 공백 포함, 비어 있음, 2048자 초과)은 `ValueError`.
- URL→코드와 코드→URL 두 해시 테이블을 쓴다.

## 5. 웹 서버 (`src/server.py`, 표준 `http.server`)

| 요청 | 응답 |
| --- | --- |
| `GET /` | URL 입력 폼 |
| `POST /shorten` (`url` 필드) | 짧은 링크가 든 페이지. 잘못된 입력은 400과 안내 |
| `GET /<code>` | 원래 주소로 302 이동. 없는 코드는 404 |
| `GET /table` | 해시 테이블 시각화: 슬롯별 연결 리스트(노드: URL, 코드, 짧은 링크), 노드를 펼치면 Horner 계산 과정 |

- 짧은 링크의 주소는 `X-Forwarded-Proto`/`X-Forwarded-Host`가 있으면 그것을, 없으면 `Host`를 쓴다.
- `make serve`로 포트 8000에서 시작한다(`--port`로 변경 가능).
- 데이터는 메모리에만 두며 서버를 껐다 켜면 사라진다.

## 6. 경계 사례

- base62: `encode(0)=="0"`, `encode(61)=="Z"`, `encode(62)=="10"`, `decode(encode(n))==n`, 음수, 빈 문자열, 잘못된 글자
- 해시 테이블: 빈 테이블 `get`은 `None`, 같은 키 `put`은 값 교체(길이 그대로), 같은 슬롯으로 가는 키들이 모두 찾아짐,
  없는 키 `find`, 적재율 초과 시 크기 증가 후에도 모든 키 유지, `max_load=None`이면 늘지 않음,
  `dict`·`set`·`hash(` 미사용
- 단축기: 같은 URL 두 번 → 같은 코드, 다른 URL → 다른 코드, 코드는 1, 2, 3... 순서, 없는 코드는 `None`,
  `ftp://`·공백·빈 문자열·매우 긴 URL은 `ValueError`
- 서버: `/` 200, 단축 후 링크 표시, 코드 접속 시 302와 `Location`, 없는 코드 404, `X-Forwarded-Host` 반영, `/table` 200
