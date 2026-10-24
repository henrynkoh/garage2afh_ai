# Marketing kit — garage2AFH

Tone rules: concrete numbers, no hype, one call to action per post. Replace
`https://github.com/henrynkoh/garage2afh_ai` only if the repo moves.

---

## 1. Facebook (build/real-estate groups)

Converting a garage into a licensed AFH means a drawing set, a code trail, a budget and
an appendix — usually four vendors. We turned it into one repeatable run: address +
photos in, 43-sheet package out, with 74 automated checks and a materials takeoff that
adds up.

First case study: a 790 SF 3-car garage in Tumwater WA. 71-page package, 43 sheets,
appendix A–D, one page size, zero blank pages, budget discrepancy caught before it
reached the city.

The toolkit is open source: https://github.com/henrynkoh/garage2afh_ai

If you have a garage and an AFH plan, comment "AFH" and I'll send the checklist.

## 2. Instagram (carousel, 6 slides)

1. 790 SF garage → 3-bedroom AFH suite
2. One address + 2 sketches = 43 sheets
3. 74 automated checks, every failure named
4. Materials takeoff: line items, not guesses
5. Appendix A–D: survey, specs, budget, site QA
6. One PDF, A3, ready for the portal

Caption: Turning a garage into an AFH is 20 % design and 80 % paperwork. We automated
the 80 %. Repo in bio. #AFH #accessorydwelling #remodel #constructiontech #adultfamilyhome

## 3. Threads (short, conversational)

Built a thing: give it a property address and a photo of a hand sketch, it produces a
43-sheet garage-to-AFH package with an audit log and a material takeoff.

The interesting part wasn't the drawings. It was making the numbers stop lying — the
budget PDF said one total, the line items said another. Now totals are computed.

https://github.com/henrynkoh/garage2afh_ai

## 4. Blogger

Title: From garage to AFH: a repeatable package pipeline

Body: Most garage-to-AFH projects stall on documentation, not construction. This post
walks through a pipeline that takes a property address, a couple of sketches and a
listing record, and produces a full submittal package: 43 drawings (plans, elevations,
sections, MEP, life safety, energy), a 74-item automated audit, a materials takeoff, and
a bound appendix with survey and county records.

We also cover the four defects that broke earlier attempts: unit collisions between
sheet frames and model geometry, validators checking a stale PDF, asserted budget totals
that did not match line items, and blank pages from HEIC conversion. Each has a gate now.

Repo and manual: https://github.com/henrynkoh/garage2afh_ai

## 5. Naver Blog (Korean)

제목: 차고를 AFH로 — 서류 패키지를 자동으로 만드는 파이프라인

본문: 차고를 성인가족가정(AFH) 거주공간으로 바꾸는 일은 설계보다 서류에서 막힙니다.
주소와 손스케치 사진 몇 장을 넣으면 43장 도면 세트, 74개 자동검사, 자재 물량표,
측량도·카운티 기록이 포함된 부록까지 한 번에 나오는 파이프라인을 만들었습니다.

실제 사례는 Tumwater WA의 790 SF 차고였고, 결과물은 71페이지 패키지였습니다. 이 과정에서
잡은 대표 결함 네 가지도 정리했습니다. 단위 충돌(도곽과 모델), 오래된 PDF를 검증하던
버그, 합계가 아닌 주장으로 적힌 예산, HEIC 변환으로 생긴 검은 페이지입니다.

깃허브: https://github.com/henrynkoh/garage2afh_ai

## 6. Tistory

Title: 43장 도면을 자동으로 — garage2AFH 사용기

Body: 설치 5분, 첫 프로젝트 15분. `g2a.py new` 로 주소를 넣고 `design.py` 의 벽·방·창
좌표를 고친 뒤 `build` → `bind` → `check` 세 번이면 도면 43장과 71페이지 패키지가
나옵니다. 검증기는 하드 실패 시 exit 1을 반환하므로 "됐다고 기억하는" 상태가 남지
않습니다. 전체 매뉴얼과 튜토리얼은 저장소 docs에 있습니다.

## 7. WordPress

Title: A Six Sigma view of AI-generated construction documents

Body: AI can draft a drawing set in an afternoon. The hard part is repeatability. We
reverse-engineered a delivered 71-page permit package into its ingredients, then applied
DMAIC: CTQs for sheet completeness, page uniformity, blank pages, number integrity and
audit pass rate; a defect log from the first run; four control mechanisms (manifest,
build-time derivation, three-level gate, explicit human-field list) that took the
pipeline from roughly 80k DPMO to zero hard-gate defects at submission.

The result is open source: https://github.com/henrynkoh/garage2afh_ai

## 8. Newsletter (email)

Subject: 43 sheets, 74 checks, one PDF — the garage-to-AFH toolkit

Hi {{first_name}},

Most garage-to-AFH projects die in documentation: the drawing set, the code notes, the
budget, the appendix, the portal naming rule.

We packaged the whole thing into one open-source toolkit. You give it an address and a
sketch; it produces a 43-sheet package with an automated audit, a material takeoff, and a
bound appendix — then tells you exactly which fields only a human can sign.

Case study inside: a 790 SF garage in Tumwater WA, 71 pages, one page size, zero blank
pages, and a budget error caught before it reached the city.

→ Read the case study and grab the toolkit: https://github.com/henrynkoh/garage2afh_ai

Reply "CHECKLIST" and I'll send the pre-submittal checklist as a PDF.

— {{sender_name}}

---

## Email follow-up sequence (3 touches)

1. **Day 0** — the email above.
2. **Day 3** — "The four defects that break AI document sets" (unit collisions, stale
   PDFs, asserted totals, blank pages) with one-line fixes.
3. **Day 7** — invitation: send one address, get a scope memo back in 48 hours.
