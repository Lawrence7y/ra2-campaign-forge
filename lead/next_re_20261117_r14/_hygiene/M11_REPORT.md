# M11 合并报告（COVERAGE 唯一写者；快照 `_hygiene/M11_before/`）

## 快照 SHA-256（before）
- coverage.tsv 9ef239c22f5c100e3a5ac65e83fafa15ca44cd626c591465c195ecfb496eec94
- PANEL.md c6792286efa5d94b3b9f0c987debb14a968e0e6fa34fc11a340883e06b77099d
- CONFLICTS.tsv 66cd43dbff81d3f77c32c35093efc4c4d8a1b6e4660bd15183616dbd960f6d3e
- PENDING_CORRECTIONS.tsv a709a3df8639e3fb8cb380e94989eb11b68ccdceca32ab50bb1011f53ed178c9

## 并入 / 排除
- 并入 S10_K10（PARTIAL 审计，四环独立成立，`[已证]` 可留）2 行：006FCDB0、004D8FB0；grade 提级 + 真名/语义替换。
- 并入 S10_K11（无审计，仅措辞修正）2 行：004DFCB0、004DFE00；name 与 grade 不变，只改 one_line_semantics；字节证据 @0x004DFDBA / 0x004DFF00 独立反汇编确认 and。
- 排除 S10_K9（5 行）：PARTIAL 审计指出 0051BAB0 应退 `[静态推断]`、00522340 语义串错（005B3A00 实为按 mission 索引取 32B 表项，台账 S12/`[未证]`，非已证删除析构）、行 3/4 循环论证；5 行盘上仍 `[静态推断]`，等返工卡 S10-K12 重交后再并；不擅自升 `[已证]`。

## coverage.tsv 行数与第 5 列 grade 分布
| 项 | before | after | Δ |
|---|---:|---:|---:|
| 数据行（不含表头） | 18,431 | 18,431 | 0 |
| [已证] | 1,362 | 1,364 | +2 |
| [静态推断] | 6,038 | 6,036 | −2 |
| [未证] | 11,031 | 11,031 | 0 |
+2 恰来自 S10_K10 的 2 行；S10_K11 不改 grade。无越界：无新增/删除 entry，K9 5 行仍是 `[静态推断]`。

## S10_K11 one_line_semantics diff（改前 → 改后）
- 004DFCB0 改前：`... passing 0x457ce0 filter with [v+0x2C]()==0xF, writes [this+0x690]=1 ...`
  改后：`... passing 0x457ce0 filter with [v+0x2C]()==0xF, skips when [this+0x5A4]==best and [this+0xAC]==8, writes [this+0x690]=1 ...`
  差异：补入跳过条件 `skips when [this+0x5A4]==best and [this+0xAC]==8`。
- 004DFE00 改前：`... nearest candidate passing 0x457ce0 filter, skips when [this+0x5A4]==best or cur==8, writes [this+0x691]=1 ...`
  改后：`... nearest candidate passing 0x457ce0 filter, skips when [this+0x5A4]==best and [this+0xAC]==8, writes [this+0x691]=1 ...`
  差异：`or cur==8` → `and [this+0xAC]==8`。
- 两行其余 7 列（name/subsystem/grade/evidence_path/n_sources/conflict/entry）逐列不变。

## 登记与面板
- CONFLICTS.tsv 新增 **0**（K10 提级非同 grade 冲突；K11 同 grade 且 name/subsystem 原值一致）；PENDING_CORRECTIONS.tsv 新增 **5**（K10 grade×2、K11 措辞×2、K10 D2/D3/D4 语义待改×1）。
- PANEL.md：S10 proved **109/526 = 20.72%**（107 + K10 的 2），注明「S10_K9 的 +5 未审计、未计入」；S10 named **513**（非 M7 旧截面 511）；保留 named_pct_S 双列 / S13 240+148 双分母 / S22 不参与排名 / 三分母 12,916·14,487·18,431。
- 仅写 COVERAGE/ 与 _hygiene/；未改游戏文件，未 git commit。
