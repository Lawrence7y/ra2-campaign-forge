# COMMON-R9 PROGRESS

改动文件：`R14_COMMON.md`｜备份先行：`_hygiene\R14_COMMON.COMMON-R9.bak`（改前写入，102,102 B / SHA-256 a91e4f36…，与源文件逐字节相同）
改前：**102,102 B / 679 行**（split 长度，含末空行）→ 改后：**110,094 B / 713 行**（+7,992 B / +34 行；只增不减，原 679 行全部保留为子序列，0 丢失）

## 并入清单（逐条 / § / 来源路径）

### A · 新错源（§8.1，接 ㉒ 之后 → ㉓㉔㉕㉖）
1. ㉓「活 vptr 必须是构造器写的，atexit 析构器表不算」→ §8.1，来源 `S10_KPROVED\_audit\VERDICT.md` §3 + `S13_K12\_audit\VERDICT.md` §2 + `S20_KPROVED\_audit\VERDICT.md` §2–3。
2. ㉔「同源系统性错误随机基线恒 0，必须差分检验」→ §8.1，来源 `S10_KPROVED\_audit\VERDICT.md` §4 + `S13_K12\_audit\VERDICT.md` §3。
3. ㉕「P=R=100% / 恰命中 N 可能是判据自证」→ §8.1，来源 `S13_K12\_audit\VERDICT.md` §3 + `S13_K12\work\reverify_core.py:121-122,169-171`。
4. ㉖「direct_call_sites 与自报扫描规模必须自洽」→ §8.1，来源 `S10_KPROVED\_audit\VERDICT.md` 头部/§1–2 + `S10_KPROVED\EVIDENCE\direct_call_sites.tsv`。
### B · §6 纪律 +1
5. 第 21 条：虚派发式环④卡面必须点名「构造器 vs atexit 析构器」判别（已 3 次复发）→ §6，来源 `S10_KPROVED\_audit\VERDICT.md` §6 + `S13_K12\_audit\VERDICT.md` §2 + `S20_KPROVED\_audit\VERDICT.md` §2–3。
### C · §1 作废索引 +2
6. S13_K12「全 S13 240 行恰命中 17、P=R=100%」作废（正确恰 3 行）→ §1，来源 `S13_K12\_audit\VERDICT.md` §3。
7. S10-KPROVED「并入后 157/526 = 29.85%」作废（正确 151/526 = 28.71%，白名单 34 行）→ §1，来源 `S10_KPROVED\_audit\VERDICT.md` §6。
### D · §9.0d 现态（新小节）
8. 现态刷新：coverage 18,431/1,449/5,951/11,031、conflict=254、SHA 502A56FE…；达标 3 个 S15/S16/S17；只差 proved S10 151/526（差 112）｜S11 29/184｜S20 68/410｜S13 89/240（差 31）；台账 3,370,848 B/35,216 行/§1006 → 新 §9.0d。来源：`COVERAGE\coverage.tsv` 单遍盘上读取 + `STATUS_BOARD.md` + `S10_KPROVED/S13_K12\_audit\VERDICT.md` + `lead\GOAL_THREE_TARGETS_20261018.md` + `_hygiene\H26_archive_result.json` gate B6。

## 拒绝并入（纪律 ⑨：与盘上不符则不改）
无（0 条）。全部 8 条逐条对照来源 VERDICT/源码与盘上实算核实一致。

## 盘上核验记录（⑨ 自算）
- coverage.tsv：18,431 数据行；[已证] 1,449 / [静态推断] 5,951 / [未证] 11,031（和=18,431）；conflict=1 254；SHA-256 前缀 502A56FE——与 CARD §9.0d 一致。
- atlas∩coverage（function_atlas.tsv 12,916 行求交）：S10 526/151、S11 368/29（29/184 中 184=门槛 ceil(368/2)，见 STATUS_BOARD）、S20 410/68、S13 240/86（86→89 为 K12 审计白名单投影）、S15 158/101、S16 90/46、S17 102/54。
- 台账 `lead\GOAL_THREE_TARGETS_20261018.md`：3,370,848 B / split 35,216 行 / 最大 §1006；H26 gate B6 size=3370848、prefix_sha 77D8DCB1… 与 baseline 相同。
- 错源实证：S10 VERDICT §3/§4/头部、S13_K12 VERDICT §2/§3、S20 VERDICT §2–3 逐条命中；S13 `work/reverify_core.py:121-122,169-171` 根因代码在位。
- 原文件 679 行全部保留为子序列（0 丢失），只增不减；未建 venv、未 pip install。

## 并入统计
并入条数：**8**（4 新错源 + 1 §6 纪律 + 2 §1 作废 + 1 §9.0d 小节）｜拒绝并入：**0**。