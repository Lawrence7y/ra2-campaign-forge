# M33 PROGRESS — 并入 a-S21-C3 白名单 2 行（`0053AF40` `00595740`）

## 结论
- 并入行数（applied）：**2**（`0053AF40` `PsyDom::Update`、`00595740` `sub_00595740`，均 `[未证]`→`[已证]`）
- rejected 数：**3**（`00539760`、`0053AB50`、`00599650`，整行不动，保持盘上现值）
- `[已证]` 前后：**1,386 → 1,388**（+2）
- S21 proved 前后：**26 → 28**（129，20.16% → 21.71%；门槛 65，差 37）
- coverage 前后 SHA-256：
  - 前：`aa91cd6b9ddc2567a5e69d7ae7d9de4277282bae66676fd5ec1bbe182d1a4f52`
  - 后：`5258d75a209b2f89573404fae854ad13693737026b18caaf7ee29d4062950f2a`
  - 备份：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M33.bak`

## 口径与写域
- 写域：`COVERAGE\`（coverage.tsv / PANEL.md）+ `M33\`（MERGE_LOG.tsv / PROGRESS.md）；改前备份 `_hygiene\coverage.M33.bak`（原样，SHA 与改前 coverage 一致）。
- 只改 2 行的第 4/5/6 列（one_line_semantics / grade / evidence_path）；name 与 subsystem 一律不动；表头逗号、数据行 TAB（8 列）不变。
- 未建 venv、未 pip install。

## 前后直方图（全表 18,431 行）
| grade | 前 | 后 | 差 |
|---|---:|---:|---:|
| `[已证]` | 1,386 | 1,388 | +2 |
| `[未证]` | 11,026 | 11,024 | −2 |
| `[静态推断]` | 6,019 | 6,019 | 0 |
| 合计 | 18,431 | 18,431 | 0 |
- atlas 内 `[已证]`：1,381 → 1,383（2 行均不在 `coverage_outside_atlas.tsv`，在 atlas 内）；atlas 外 5 行不变。
- `conflict=1`：254 → 254（本卡不新增 conflict）。
- 数据行：18,431 → 18,431；entry 增删 0；name/subsystem 逐行零差异。

## 2 行改动
| entry | 子系统 | name（不动） | 改动列 | 审计依据 |
|---|---|---|---|---|
| `0053AF40` | S21 | `PsyDom::Update` | semantics ← `S21_C3/coverage_delta.tsv` 原文；grade `[未证]`→`[已证]`；evidence_path 保持盘上现值 | VERDICT §2：③ 成立（11/11 断言全中，跳表 stage0→+0x11E / 1→+0x17 / 2→+0x24 / 3→+0x82 / 4→+0xB3 / 5→+0xFF）；§3 YRpp SuperClass.h:178-191 类属通道 + ④ 站点 0053A742 |
| `00595740` | S21 | `sub_00595740` | semantics ← delta 原文 + `YRpp MapSeedClass.h + 字节双吻合；另有 +0x13D/+0x152 两处成员 ctor（vt 0x7ED90C）`；grade `[未证]`→`[已证]`；evidence_path `EVIDENCE/classification_trace.tsv#00595740` → `S21_C3/_audit/VERDICT.md#3` | VERDICT §2：③ 成立（13 处成员 ctor，只漏列 +0x13D/+0x152）；§3 YRpp MapSeedClass.h:8-109 + 0x7E4DD8/0x7ED90C 的 COL→TD 链实测 + ④ 站点 0058B745 |

## 3 行 rejected（整行不动，保持盘上现值）
| entry | 盘上 grade | 审计理由 |
|---|---|---|
| `00539760` | `[未证]` | ③ 属 P 级（清零/置默认值，「多个全局」未具名），+0xE7 偏移错（拷贝实为 +0xF3/+0xF9）；② 无通道 |
| `0053AB50` | `[未证]` | 整个函数仅 4 条指令（call 0x53C280 + 写一字段 + ret），D-40 明文排除；② 无通道 |
| `00599650` | `[静态推断]` | ③ 内容真但两处偏移区间坏（应为 +0x15~+0xF8 与 +0xEF8~+0xF9C），② 仍缺；灰名单不作 +1 |

按 D-41 默认(A)：② 无通道即不升。

## 校验
- 2 行且仅 2 行发生变化；变化列仅第 4/5/6 列；name/subsystem 与其余 5 列逐字节不变。
- 3 行 rejected（00539760 / 0053AB50 / 00599650）与备份逐行一致。
- 备份字节一致；未建 venv、未 pip install。

## 来源
- `M33/CARD.md`
- `S21_C3/coverage_delta.tsv`、`S21_C3/_audit/VERDICT.md`（a-S21-C3 裁 PARTIAL）
