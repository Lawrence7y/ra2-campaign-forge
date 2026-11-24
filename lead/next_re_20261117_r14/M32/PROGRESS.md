# M32 · PROGRESS — 按 D-40 回退 53 行 direct-only 升格

## 口径与依据
- 裁定：`lead\PENDING_DECISIONS.md` D-40（2026-11-18 17:2x，已按此执行）。「有 direct call」不能单独支撑 `[已证]`；最小环集 = ①入口 + ②类属 + ③整体合同 + ④使用见证（direct call 或活 vtable 槽位派发），任一缺不得升。
- 写域：`COVERAGE\`（coverage.tsv / PANEL.md）+ `M32\`（CARD.md / MERGE_LOG.tsv / PROGRESS.md）；改前备份 `_hygiene\coverage.M32.bak`（原样，SHA 与改前 coverage 一致）。
- 只改回退行第 5 列 `[已证]`→`[静态推断]`；其余 7 列逐行零差异；entry 增删 0；表头逗号 / 数据行 TAB（8 列）不变。

## 前后直方图（全表 18,431 行）
| grade | 前 | 后 | 差 |
|---|---:|---:|---:|
| `[已证]` | 1,439 | 1,386 | −53 |
| `[静态推断]` | 5,966 | 6,019 | +53 |
| `[未证]` | 11,026 | 11,026 | 0 |
| 合计 | 18,431 | 18,431 | 0 |
- atlas 内 `[已证]`：1,434 → 1,381（−53；53 行全在 atlas，atlas 外 5 行不变）。
- `conflict=1`：254 → 254（本卡不新增 conflict）。

## S10 / S20 proved 前后（atlas 分母口径，与 PANEL 一致）
- S10：proved **151 → 123**（526，28.71% → 23.38%；回退 28 行 direct；门槛 263，差 112 → 差 140）。
- S20：proved **72 → 47**（410，17.56% → 11.46%；回退 21+4=25 行 direct；门槛 205，差 133 → 差 158）。
- 附注（全表口径，仅说明差异）：coverage 全表 S10 `[已证]` 152 → 124（多出的 1 行是 atlas 外的 `005B3740`，PANEL M12 note 已记「表外 0041B860/005B3740」）；S20 全表 72 → 47（与 atlas 口径一致）。CARD 预期 151/72 用的是 atlas 口径。

## 回退 53 行清单（entry / old / new / 来源）
| # | entry | 来源 | old → new |
|---:|---|---|---|
| | **S20_KPROVED/M24（21 direct）** | | |
| 1 | 0045A270 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 2 | 005251C0 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 3 | 005F3E30 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 4 | 005F42C0 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 5 | 005F4520 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 6 | 005F5280 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 7 | 005F5320 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 8 | 005F5390 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 9 | 005F5930 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 10 | 005F5940 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 11 | 005F5FA0 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 12 | 005F65A0 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 13 | 005F6A70 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 14 | 005F6B60 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 15 | 005F6BD0 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 16 | 005F6C70 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 17 | 005F6C80 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 18 | 005F6DA0 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 19 | 005F9970 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 20 | 0067ABE0 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| 21 | 0075F8B0 | S20_KPROVED/M24 | `[已证]` → `[静态推断]` |
| | **S10_KPROVED/M25（28 direct）** | | |
| 22 | 004CBBA0 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 23 | 004D5690 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 24 | 004D7170 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 25 | 004D74E0 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 26 | 004D7D50 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 27 | 004D82B0 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 28 | 004D85D0 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 29 | 004D8F40 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 30 | 004D94B0 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 31 | 004D9920 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 32 | 004D9960 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 33 | 004DB1A0 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 34 | 004DB250 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 35 | 004DB260 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 36 | 004DB3C0 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 37 | 004DB690 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 38 | 004DBAD0 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 39 | 004DBED0 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 40 | 004DC030 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 41 | 004DDDE0 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 42 | 004DDED0 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 43 | 004DE620 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 44 | 004DF040 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 45 | 00517CC0 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 46 | 006F3AD0 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 47 | 006F3D60 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 48 | 006F77B0 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| 49 | 005F5E80 | S10_KPROVED/M25 | `[已证]` → `[静态推断]` |
| | **S20_DIRECT/M28（4 行纯 direct）** | | |
| 50 | 0070F1D0 | S20_DIRECT/M28 | `[已证]` → `[静态推断]` |
| 51 | 0070FD70 | S20_DIRECT/M28 | `[已证]` → `[静态推断]` |
| 52 | 00739AC0 | S20_DIRECT/M28 | `[已证]` → `[静态推断]` |
| 53 | 00739CD0 | S20_DIRECT/M28 | `[已证]` → `[静态推断]` |

## 保留 13 行 exact（活 vtable 派发，合法环④，不回退）
| entry | 来源 | 保留理由 |
|---|---|---|
| 0040F0A0 | S20_KPROVED/M24 | ④=EXACT：构造器装的活表 + vt[slot]==entry + 写点在行外 + site 不共用（M24 MERGE_LOG EXACT PASS；S20_KPROVED _audit VERDICT §3 PASS 7） |
| 0040F150 | S20_KPROVED/M24 | ④=EXACT：构造器装的活表 + vt[slot]==entry + 写点在行外 + site 不共用（M24 MERGE_LOG EXACT PASS；S20_KPROVED _audit VERDICT §3 PASS 7） |
| 0053C6A0 | S20_KPROVED/M24 | ④=EXACT：构造器装的活表 + vt[slot]==entry + 写点在行外 + site 不共用（M24 MERGE_LOG EXACT PASS；S20_KPROVED _audit VERDICT §3 PASS 7） |
| 005514B0 | S20_KPROVED/M24 | ④=EXACT：构造器装的活表 + vt[slot]==entry + 写点在行外 + site 不共用（M24 MERGE_LOG EXACT PASS；S20_KPROVED _audit VERDICT §3 PASS 7） |
| 00551560 | S20_KPROVED/M24 | ④=EXACT：构造器装的活表 + vt[slot]==entry + 写点在行外 + site 不共用（M24 MERGE_LOG EXACT PASS；S20_KPROVED _audit VERDICT §3 PASS 7） |
| 00557090 | S20_KPROVED/M24 | ④=EXACT：构造器装的活表 + vt[slot]==entry + 写点在行外 + site 不共用（M24 MERGE_LOG EXACT PASS；S20_KPROVED _audit VERDICT §3 PASS 7） |
| 00557140 | S20_KPROVED/M24 | ④=EXACT：构造器装的活表 + vt[slot]==entry + 写点在行外 + site 不共用（M24 MERGE_LOG EXACT PASS；S20_KPROVED _audit VERDICT §3 PASS 7） |
| 0045A560 | S10_KPROVED/M25 | ④=EXACT：活表 vptr 写点/site 齐备（S10_KPROVED _audit VERDICT §3 PASS 6，非 atexit 析构器基类表） |
| 0045A610 | S10_KPROVED/M25 | ④=EXACT：活表 vptr 写点/site 齐备（S10_KPROVED _audit VERDICT §3 PASS 6，非 atexit 析构器基类表） |
| 006B1850 | S10_KPROVED/M25 | ④=EXACT：活表 vptr 写点/site 齐备（S10_KPROVED _audit VERDICT §3 PASS 6，非 atexit 析构器基类表） |
| 006B1900 | S10_KPROVED/M25 | ④=EXACT：活表 vptr 写点/site 齐备（S10_KPROVED _audit VERDICT §3 PASS 6，非 atexit 析构器基类表） |
| 006B8660 | S10_KPROVED/M25 | ④=EXACT：活表 vptr 写点/site 齐备（S10_KPROVED _audit VERDICT §3 PASS 6，非 atexit 析构器基类表） |
| 006B8710 | S10_KPROVED/M25 | ④=EXACT：活表 vptr 写点/site 齐备（S10_KPROVED _audit VERDICT §3 PASS 6，非 atexit 析构器基类表） |

- D-40 结论明确 ④ 的两种形态含「活 vtable 槽位派发（构造器装的活表 + `vt[slot]==entry` + site 不共用）」，故上述 13 行满足最小环集且 ④ 为合法形态，不属 direct-only 回退范围。

## coverage 前后 SHA-256
- 改前：`11326f62fd7b16e43fe4f8dd0600eebb7fb1e5c86d9fc052d2e70e1870dcd2f1`
- 改后：`aa91cd6b9ddc2567a5e69d7ae7d9de4277282bae66676fd5ec1bbe182d1a4f52`
- 备份：`_hygiene\coverage.M32.bak`（= 改前原样，SHA 与上「改前」一致）。

## 核对记录
- S20_KPROVED：`S20_KPROVED\coverage_delta.tsv` 内 ④=DIRECT 恰 21 行（与 CARD 清单逐字一致）；④=EXACT 共 19 行，但仅 7 行被 M24 实际并入（M24 MERGE_LOG APPLIED 中 EXACT-match=7），其余 12 行为黑名单（盘上仍 `[静态推断]`，未动）。
- S10_KPROVED：`S10_KPROVED\_audit\VERDICT.md` §2 的 28 条 DIRECT 与 M25 MERGE_LOG 一致（004CBBA0 备注写 "DIRECT PASS" 而非 "DIRECT 28 PASS"，已并入核对）；§3 PASS 6 exact 一并保留。
- S20_DIRECT：M28 MERGE_LOG 的 4 行全为纯 direct，全部回退。
- 回退数 21+28+4 = 53，保留数 7+6 = 13；与 CARD「若算出回退数不是 53 先停下」一致，未凑数。
