# 한국어 빠른 시작 (garage2AFH)

차고를 AFH(성인가족주택) 거주구역으로 바꾸는 제출 패키지를 주소 하나로 뽑아내는 도구입니다.
명령 4개(`new` / `build` / `bind` / `check`)와 게이트 7개만 기억하면 됩니다.

---

## 1. 설치

```bash
git clone https://github.com/henrynkoh/garage2afh_ai.git
cd garage2afh_ai
python3 -m pip install --target pydeps ezdxf pypdf openpyxl numpy
python3 g2a.py --help
```

`pydeps`에 설치하는 이유: `g2a.py`가 모든 하위 단계에 `PYTHONPATH=pydeps`를 고정해서 넣기
때문입니다. 내 컴퓨터의 파이썬 환경과 섞이지 않아 다른 기기에서도 같은 결과가 나옵니다.
`numpy`는 선택이 아닙니다. `ezdxf`가 numpy를 불러오므로 없으면 첫 단계에서 바로 죽습니다.

파이썬이 `ezdxf`를 못 읽는 환경(Blender 내장 파이썬, numpy 없는 런타임)이라면 실행기만
바꿔주면 됩니다:

```bash
export G2A_PYTHON=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
export HOUSEBIM_PYDEPS=$PWD/pydeps
```

확인:

```bash
python3 g2a.py --help          # 사용법 5줄이 나오면 설치 끝
```

---

## 2. 명령 4개

### ① new — 프로젝트 만들기

```bash
python3 g2a.py new "3571 Cassie Drive SW, Tumwater WA 98512" \
  --parcel 40380000700 --tax-id 4038-00-00700 --lot-sf 9411 \
  --lot "LOT 7, CHAPPAREL LANDING DIVISION 2"
```

- `--parcel` 은 필수(카운티 필지번호), `--lot-sf` 는 측량도 기준 대지면적(SF)
- 주소의 첫 쉼표 뒤가 도시로 들어갑니다. 다르면 `--city "Tumwater, WA 98512"`
- 결과: `projects/<slug>/design.py` + `meta.json`
- **이 파일 하나만 손으로 고칩니다.** 벽·방·문·창·배관 수치의 유일한 출처입니다.

### ② build — 도면 43장 + 검사 74개 + 자재 27줄

```bash
python3 g2a.py build <slug>            # 새로 만들 때
python3 g2a.py build <slug> --clean    # 도면 이름을 바꿨거나 지웠을 때 (필수)
```

정상 출력의 마지막 두 줄:

```
   checks 74/74
[build] done · dxf=43 svg=43
```

`--clean` 은 `out/`의 옛 DXF·SVG·PDF를 지웁니다. 예전 파일이 남아 있으면 시트 번호 중복이나
꽉 찬 PDF 속에 옛 페이지가 섞이는 사고가 납니다.

### ③ bind — 신청서 시트 + 목차 + 합본 PDF

```bash
python3 g2a.py bind <slug> [--binder projects/<slug>/bind_master.py]
```

원본 3571 기준 합본은 71쪽입니다(도면 43 + 목차 2 + 부록 A 5 + B 15 + C 4 + D 2).
페이지 정규화(A3 가로 1191.12×841.92 pt, Letter 페이지 확대·중앙정렬)는 프로젝트마다 달라서
`bind_master.py`를 파이프라인이 아니라 프로젝트 폴더에 둡니다. 바인더가 없으면
`no binder found` 라고 알려주고 시트·목차까지만 만듭니다.

### ④ check — 제출 전 검증 (실패하면 exit 1)

```bash
python3 g2a.py check <slug>
```

정상(합본 전) 출력:

```
   [PASS] 필수 시트 존재 :: 43장 / 기대 43장
   [PASS] 사람이 채울 공란 식별 :: G-04_신청데이터: (LIC#,(건축주,(성명
   [PASS] 자동검사 74/74 :: 74/74
   [PASS] PDF 페이지 = 시트 수 :: PDF 43쪽 / 시트 43장
   [PASS] 면적표 산출값 존재 :: A-12 값 3개
   [PASS] G-03 수치(카운티) 반영 :: 9,411 / Tax-ID / Concrete
   [PASS] C-01 수치(측량) 반영 :: 9,357 SF / 37.6%
[check] 7/7 passed · hard fails=0
```

보조 명령: `python3 g2a.py status` — 프로젝트별 `dxf / svg / audit / validate / pdf` 한 줄 요약.

---

## 3. 게이트 7개의 의미

| 게이트 | 무엇을 보는가 | 통과 조건 | 실패하면 |
|---|---|---|---|
| A 필수 시트 | 디스크의 DXF 43장과 시트 목록 대조 | 43장, 코드 중복 없음 | 누락 시트 이름이 그대로 출력 |
| B 사람 공란 | `(성명` `(LIC#` `(건축주` `TBD` `미기재` 스캔 | 항상 PASS(정보성) | 실패 아님. 서명 전 채울 목록일 뿐 |
| C 자동검사 | `checks_3571.json` | 74/74 | 어떤 항목이 왜 틀렸는지 id와 함께 출력 |
| D PDF 쪽수 | `out/pdf/*-도면세트.pdf` 쪽수 | 쪽수 == 시트 수 | `PDF None쪽` 이면 pdfinfo 경로 또는 bind 미실행 |
| E 면적 산출값 | `A-12_면적산출.svg` | 숫자가 1개 이상 | A-12가 비었거나 생성 안 됨 |
| F G-03 수치 | 카운티 값(대지 9,411·Tax-ID·기초 Concrete) | SVG 안에 실제로 존재 | 이전 프로젝트 복사 흔적 |
| G C-01 수치 | 측량 값(9,357 SF·건폐율 37.6%) | SVG 안에 실제로 존재 | 위와 같음 |

F·G는 **일부러 프로젝트별 값으로 고정**해 두었습니다. 남의 `design.py`를 복사해 오면 여기서
걸리게 만들기 위해서입니다. 새 프로젝트에서는 `src/pipeline/validate_packet.py`의 `num_ok`,
`cov_ok` 두 줄을 새 숫자로 바꾸고, 같은 파일 위쪽 `PDFINFO` 경로를 내 `pdfinfo`로 맞추세요.

또 하나: 자동검사 74개 중 **46개는 "그 주석이 도면에 있는가"를 확인**하고(같은 파이프라인이
문자를 찍으므로 사실상 항상 참), **28개만 모델에서 계산**합니다. 74/74를 "기하 검증 74개
통과"라고 말하면 안 됩니다. 실제로 설계 오류를 잡는 것은 그 28개입니다.

---

## 4. 자주 나는 오류 5가지

### ① 단위·축척 충돌
증상: 5'-3" 자리에 16'-0"가 찍히거나, 자재 수량이 10배(또는 1/10)로 나옴.
원인: 피트/미터/인치가 한 식에서 만남.
해결: `design.py`의 모든 길이는 `ft(피트, 인치)`만 사용. 원시 숫자(0.3048, 인치값) 금지.
방 면적 합이 META의 `internal_sf`와 15% 안쪽인지 확인(검사 `C13`). 자재표에서 같은 항목이
`SF`와 `m`로 섞여 있으면 같은 병의 상위 버전입니다. 고친 뒤 `build --clean`.

### ② 꽉 찬(stale) PDF
증상: `PDF 43쪽`이어야 하는데 옛 쪽수가 나오거나, 어제 도면이 PDF에 남아 있음.
원인: 도면은 새로 만들고 PDF는 다시 안 만듦(또는 바인더를 먼저 돌림).
해결: `g2a.py build <slug> --clean` → 시트 PDF 재출력 → `g2a.py bind <slug> --binder ...` →
`g2a.py check <slug>`. PDF는 항상 도면의 결과물이고, 보관하는 파일이 아닙니다.

### ③ 계산하지 않은 합계 (asserted total)
증상: 예산 총액이 `$48,500`인데 그 셀에 수식이 없음. `A-03`은 736 SF, `A-12` 합계는 712.4 SF.
원인: 목표값·견적가를 계산된 값처럼 인쇄.
해결: 총액은 `Σ(수량 × 단가)`. 수량이 `자재목록.csv`에 없는 줄은 항목이 아니라 빈칸이므로
`(미포함)`으로 표시해 검증기 목록에 남기기. A-03과 A-12가 다르면 도면이 아니라 모델 또는
META를 고치고 다시 빌드.

### ④ 빈 페이지
증상: 표제란만 있고 내용이 없는 시트, PDF의 백지.
원인: 문·창·방 목록이 비었거나, DXF보다 SVG가 오래됨.
해결: SVG에서 내용 텍스트를 확인 → 비었으면 `C31`(문 6개) `C36`(창 4개) `C27`(HVAC실) 중
무엇이 실패했는지 보고 모델 보완 → DXF는 찼는데 SVG가 비었으면 `dxf_to_svg.py`만 재실행.
바인더가 없는 부록을 빈 페이지로 채우게 두지 마세요. 쪽수 게이트가 실패하는 편이 낫습니다.

### ⑤ 시트 번호 중복
증상: 43장이어야 하는데 44장, 같은 `A-03` 두 장, 목차에 같은 시트 두 번.
원인: `S-01_표지` → `G-00_표지` 처럼 이름을 바꾸고 옛 파일을 지우지 않음.
해결:

```bash
python3 g2a.py build <slug> --clean
ls projects/<slug>/out/*.dxf | sed 's/.*\///' | cut -c1-4 | sort | uniq -d   # 아무것도 안 나와야 정상
```

그다음 `grep -rn "A-03" src/pipeline/` 으로 코드를 두 곳이 그리고 있는지 확인. 한 코드는 한
모듈만 그립니다.

---

## 5. 제출 전 체크리스트

- [ ] `g2a.py status` 가 `dxf=43 svg=43 audit=74/74 validate=7/7 pdf=43`
- [ ] `validation.json` 에 `사람이 채울 공란 식별` 외의 FAIL 이 없음
- [ ] 사람이 채울 목록(`(성명` `(LIC#` `(건축주`)을 신청인에게 전달했음 — 도구가 대신 채우지 않음
- [ ] 카운티 값과 측량 값의 차이(9,411 vs 9,357)가 `G-06`에 선택값과 함께 기록됨
- [ ] 예산 총액이 `자재목록.csv` 줄에서 계산된 값이고, 상한(ceiling) 이하
- [ ] 합본 PDF가 한 가지 용지 크기(A3 가로), 빈 페이지 0, 쪽수 = 도면 43 + 부록 28 = 71
- [ ] `out/submit/` 파일 이름이 주소 규칙에 맞음 (`3571 Cassie Dr SW - ...pdf`)
- [ ] 감사자(그린 사람이 아닌 다른 사람)가 `checks_3571.json`과 `validation.json`을 읽고 서명
- [ ] `design.py`에 `PROJECT ADDRESS` · `00000000000` · `CITY, ST ZIP` · `TBD` 가 남아 있지 않음

이 9개가 모두 참이 아니면 그 패키지는 초안입니다. 초안을 시청에 보내면 하루가 아니라 한 주를
잃습니다.

---

## 6. 더 읽을 문서

| 문서 | 내용 |
|---|---|
| `README.md` | 이 도구가 무엇이고 왜 있는지 |
| `SOP.md` | 9단계 업무 패턴, 인테이크 체크리스트, 주간 캐던스, 5프로젝트 식스시그마 리뷰 |
| `MANUAL.md` | 명령 전체 옵션, 게이트 판정 규칙, 파일 구조, 오류 해결 |
| `TUTORIAL.md` | 3571 실제 숫자로 처음부터 끝까지 (실행 출력 포함) |
| `docs/rea-six-sigma.md` | 역설계 + DMAIC 분석 |
