# COMMON-R10 PROGRESS — R14_COMMON.md 增补（3 条 + §1 +1 + §9.0e）

## 改前/改后
- 改前：**110094 B / 713 行**（split 长度）；备份 `_hygiene\R14_COMMON.COMMON-R10.bak`（改前字节逐字一致）
- 改后：**115367 B / 745 行**（split 长度）
- 未建 venv、未 pip install；写域仅限 R14_COMMON.md / _hygiene\ / COMMON_R10\

## 逐条落点
| # | 加了什么 | 加在哪个 § | 来源 |
|---|---|---|---|
| 1（主条） | `docs\re\` 与台账不得作名字异源通道；只 YRpp 地址绑定原文行或跨项目独立源算通道②；单通道不得升 `[已证]`；S08 的 0047F250 回退 sub_ | §8.5（新小节，接 §8.4 后） | `S08_K1\_audit\VERDICT.md` §3；`STATUS_BOARD.md`:196-207；`M29\MERGE_LOG.tsv`；`M29\PROGRESS.md` |
| 2 | named% 必须标 L/S 口径；S08 的 19 名全槽/占位式 ⇒ L 19/22、S 12/22 | §8.5 第 2 行 | `S08_K1\_audit\VERDICT.md` §4；`STATUS_BOARD.md`:215-219 |
| 3 | 族级判据必须给结构性反例；S13_K10 随机 1.53%~2.02% vs 同族槽 1,843/1,975=93.3%，跨类误挂 0/1,975 | §8.5 第 3 行 | `S13_K10\_audit\VERDICT.md` §4 |
| 4 | §1 作废索引 +1：`S08-K1` 的 `0047F250 → Draw_Fog` 命名作废（docs-only 单通道） | §1 表末（COMMON-R9 行后） | `S08_K1\_audit\VERDICT.md` §3/§6；`M29\MERGE_LOG.tsv`；`M29\PROGRESS.md` |
| 5 | 现态刷新：coverage 18,431/1,458/5,947/11,026/conflict 254；CONFLICTS 470 行 + 007C978A OPEN；达标 3（S15/S16/S17）；只差 proved 五子系统；台账 3,370,848 B/35,216 行/§1006 | §9.0e（新小节，接 §9.0d 后） | `COVERAGE\coverage.tsv`/`CONFLICTS.tsv`/`PANEL.md`；`STATUS_BOARD.md`；`M29\PROGRESS.md`；盘上单遍读取 |
| 6 | 本轮刷新记录（COMMON-R10） | 文末 | 本 PROGRESS |

## 并入条数
**5**（3 条主条 + §1 作废索引 1 条 + §9.0e 现态刷新 1 节）。

## 拒绝并入
**0**。全部 3 条 + §1 +1 + §9.0e 现态均与盘上逐字核对一致，无与盘上不符项。
- 主条 / 第 2 条 / §1：`S08_K1\_audit\VERDICT.md` §3/§4/§6 + `M29\MERGE_LOG.tsv`（Draw_Fog 不采纳、name 回退 sub_）+ `STATUS_BOARD.md`:196-219。
- 第 3 条：`S13_K10\_audit\VERDICT.md` §4（1.53%–1.65% 四 seed / 2.02% 执行员、1,843/1,975=93.3%、跨类误挂 0）。
- §9.0e：`COVERAGE\coverage.tsv` 实读 18,431 行 / 已证 1,458 / 静态 5,947 / 未证 11,026 / conflict 254；`CONFLICTS.tsv` 470 行含 007C978A OPEN；`PANEL.md` S15 144/158+101/158、S16 81/90+46/90、S17 94/102+54/102；`STATUS_BOARD.md`:225-227；台账 3,370,848 B / split 35,216 行 / 最大 §1006。
