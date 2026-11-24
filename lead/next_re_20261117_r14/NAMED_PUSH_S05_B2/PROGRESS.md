# NAMED-PUSH S05 B2 — PROGRESS

> 每核完一行即落盘 EVIDENCE；每 5 行追加一次进度。18 行全核完。

## 进度记录（按筛选序，entry 升序）

- **第 1–5 行**（00459900 / 00459C20 / 00523B10 / 00523B40 / 005240A0）：② 全钉住；③ 全 FAIL（malloc 空判断模板假句 / 布尔 NULL 探测 / 无站点）；④ 全 PASS。EVIDENCE 已落盘 5 份。
- **第 6 行**（00524D70）：② PASS、③ PASS（call [edx+0x10]→cmp eax,-1→je，-1 哨兵 + 数组前移循环非栈写，与 B1 00410C30 同构）、④ PASS → **四环齐全，产出**。EVIDENCE 已落盘。
- **第 7–10 行**（005F7900 / 005F9950 / 006F3F40 / 00703860）：005F9950 ③ PASS（call 0x410320→jl，E_POINTER 0x80004003 可伪证 HRESULT，负→原值/非负→0）→ **四环齐全，产出**；其余 3 行 ③ FAIL（bool {0,1} / malloc 模板 / imm=6,100 非 falsifiable）；② ④ 全 PASS。EVIDENCE 累计 10 份。
- **第 11–15 行**（00704350 / 00712040 / 007120D0 / 007170A0 / 007474B0）：② 全钉住；③ 全 FAIL（imm=1 布尔 / 无站点 / bool getter / malloc 模板）；④ 全 PASS。EVIDENCE 累计 15 份。
- **第 16–18 行**（00747560 / 00748010 / 007480B0）：② 全钉住；③ 全 FAIL（malloc 模板 / {0} 布尔探测 / 无站点）；④ 全 PASS。EVIDENCE 累计 18 份。

## 收口
- 核完 18/18 行；② 钉住 18、③b 成立 2、④ 成立 18、四环齐全 2。
- delta.tsv 2 行（00524D70、005F9950）；base_rate.tsv 已写；REPORT.md 已补全。
