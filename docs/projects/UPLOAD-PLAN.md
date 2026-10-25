# 마스터 PDF 업로드 계획

`python3 g2a.py publish-index` 가 만든 목록입니다. 손으로 고치지 마세요.
GitHub 웹 UI: **Add file → Upload files**, 폴더마다 한 번씩 올립니다.

| # | slug | 올릴 파일 (repo 경로) | 원본 | 크기 | 쪽 |
|---|---|---|---|---|---|
| 1 | 3515-hawthorne-pl | `docs/projects/3515-hawthorne-pl/3515 Hawthorne Pl SE - Master Package - Plans plus Appendix.pdf` | `out/submit/3515 Hawthorne Pl SE - Master Package - Plans plus Appendix.pdf` | 2.8 MB | 48 |
| 2 | 7021-southwick-ct | `docs/projects/7021-southwick-ct/7021 Southwick Ct SW - Master Package - Plans plus Appendix.pdf` | `out/submit/7021 Southwick Ct SW - Master Package - Plans plus Appendix.pdf` | 2.7 MB | 47 |
| 3 | 133-jalyn-st | `docs/projects/133-jalyn-st/133 Jalyn St - Master Package - Plans plus Appendix.pdf` | `out/submit/133 Jalyn St - Master Package - Plans plus Appendix.pdf` | 2.8 MB | 47 |
| 4 | 1713-winterwood-dr | `docs/projects/1713-winterwood-dr/1713 Winterwood Dr - Master Package - Plans plus Appendix.pdf` | `out/submit/1713 Winterwood Dr - Master Package - Plans plus Appendix.pdf` | 2.8 MB | 47 |
| 5 | 7504-32nd-ave-se | `docs/projects/7504-32nd-ave-se/7504 32nd Ave SE - Master Package - Plans plus Appendix.pdf` | `out/submit/7504 32nd Ave SE - Master Package - Plans plus Appendix.pdf` | 3.2 MB | 49 |
| 6 | 3571-cassie | `docs/projects/3571-cassie/3571 Cassie Dr SW - Master Package - Plans plus Appendix.pdf` | `out/submit/3571 Cassie Dr SW - Master Package - Plans plus Appendix.pdf` | 4.4 MB | 71 |

합계: 6 프로젝트 · 261장 · 309쪽 · 2026-10-24 ~ 2026-10-25

## 빠진 것

없음.

업로드 뒤 확인:

```
curl -sI <raw pdf url> | head -1     # 200
```
