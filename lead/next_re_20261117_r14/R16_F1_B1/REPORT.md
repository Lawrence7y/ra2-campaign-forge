# R16-F1-B1 · F1 缺口成文批次 1/2 · 执行报告

> 角色：执行器 · 日期 2026-11-20（R16 第 7 轮）· 本批 18 行（派生集合按 entry 升序第 1–18 行）
> 写域：`lead\next_re_20261117_r14\R16_F1_B1\`（仅此目录）
> 依据裁决：D-47(A)（维持 D-43(A) 优先，§12.3 对「活 vtable 槽位」形态让位 + 整批披露）
> 披露节号：**§12.6**（重号后；不是 §12.4）

---

## 1. 独立派生集合：判据与命中数

**权威输入**：`R16_PROBE_4GAP\scan_F1_audit.tsv`（122 数据行，本执行器只读）；壳层 `coverage.tsv`（只读）。

**判据**（照卡面 §3，逐条落到扫描列 / 盘上列）：

| # | 判据 | 落点 |
|---|---|---|
| 1 | `same_source == no`（④ 与 ② 不同源，守 §12.3 精神） | `scan_F1_audit.tsv:same_source == 'no'` |
| 2 | `ring4_at` 解出装表指令 `mov <mem>, imm32` 且 imm32 指向该行活表 | `n_install_decoded > 0`（扫描卡已解码） |
| 3 | 装表点在 entry 体外 | `n_install_outside_body > 0` |
| 4 | 现盘 `coverage.tsv` grade == `[已证]` 且第 4 列尚不含 `④ 活表槽位见证` | 逐行读盘上字节 |
| 附 | ③ 全干净 | `sem_unproved == 0` |

**实测命中：76 行**（entry 全部唯一）——**与卡面预期 76 完全一致，无差异**。

拒绝计次（每行可命中多项）：`same_source=14`（14 行 `sem_virtual_witness_only`，审计列 `-`）、`no_install_decoded=46`（上述 14 行 + 32 行 `audit_ring4_alloc_reg_pivot`）、`no_install_outside=46`（同上）、`sem_unproved=0`、`not_in_cov=0`、`grade_not_proved=0`、`already_has_witness=0`。即 122 − 14（无审计/同源未知）− 32（分配/注册点，装表地址只在 reason 散文）= 76，与 REPORT.md §3.3 的 108 PASS 中 76 可转写口径逐值吻合。

**并发合并留痕**：本卡读数期间 `coverage.tsv` 被并发改写一次——首次读数（`derive_set.py` 第 1 次）sha `0046BAD980E9055AF61CC94DB9DA72C5346E087A49A00BA0009705807AA6ACF9` / 4,034,144 B（与 `R16_PROBE_4GAP\REPORT.md` 快照同）；随后变为 `95DFAC9E6CEC2D464691D84DF1EF64A0AD850C86500A4CD1348275F0FBC419D1` / 4,040,803 B。本执行器**以新盘为准**：重新跑 `derive_set.py` 得同一 76 行、同一 B1 18 行（新盘未给任何命中行加 `④ 活表槽位见证`），`delta.tsv` 的所有非第 4 列均取新盘字节。生成前后及写报告前共四次取 sha 均为 `95DFAC9E…`，稳定。

**B1 = 第 1–18 行（entry 升序）**：`00421730, 00428EA0, 004370C0, 004684E0, 00491210, 004A7C90, 004AF720, 004B6470, 004C5A30, 004C5AC0, 004F45B0, 00524D70, 0054DC60, 005550C0, 00555110, 00555150, 005F44A0, 005F9950`。

---

## 2. 成功 / SKIP

- **成功：18 行**（全部进 `delta.tsv` / `fields.tsv`）
- **SKIP：0 行**

18/18 行 vtaddr、COL、offset、TD、RTTI、装表点、宿主函数全部取到（宿主 18/18 为 atlas 命中，无「未取得」）。`same_source` 18/18 = `no`（取自 `scan_F1_audit.tsv`，与派生判据一致）。

---

## 3. 类一致选表披露（卡面 §4.1；本批 0 行改选）

`scan_F1_audit.tsv` 无 `site_of` 列，装表主站点直接取自各行的 `ring4_at`；18 行 `ring4_at` 主站点解码 `imm32` 后的目标表，其 RTTI 装饰名均精确等于 `.?AV<行名类>@@`，**无需丢弃错类站点另选**，故 §4.1 型「改选」为 **0 行**。

但有两行同槽多表，按「表属类与行名类一致 + ring4 主站点」双重条件在候选表中定表，逐字披露如下：

- `004F45B0 MouseClass::slot17`：slot17 命中 **9 张表**（MouseClass / DisplayClass / GScreenClass / MapClass / TabClass / PowerClass / RadarClass / ScrollClass / SidebarClass）。`ring4_at=005BDA4A` 只在 `MouseClass` 表 `vt=007E1964`（COL=`007FAB38`, TD=`00816C90`, `TD+8=.?AVMouseClass@@`）的体外装表点中出现，且该点 `imm32=007E1964`；其余 8 张表站点不含 `005BDA4A` ⇒ 取 MouseClass 表，无归属歧义。
- `005F44A0 AnimClass::slot84`：slot84 命中 **21 张表**（含 AircraftClass / BuildingLightClass / BuildingClass / BulletClass / FootClass / InfantryClass / … / VoxelAnimClass / WaveClass 等）。`ring4_at=0042201C` 只在 `AnimClass` 表 `vt=007E3354`（COL=`007FBA60`, TD=`008182C8`, `TD+8=.?AVAnimClass@@`）的体外装表点中出现，`imm32=007E3354`；注意 `VoxelAnimClass` 虽被 `col_name_match` 子串规则误判为 match，但其装饰名 `.?AVVoxelAnimClass@@` 与行名类 `AnimClass` 不精确相等、且站点不含 `0042201C`，已排除。⇒ 取 AnimClass 表。

同一张表多处装表点属正常（如 `LightSourceClass` 表 `007ED028` 有 `005547A0/00554869/005548ED/00554916` 四点），本批按 `ring4_at` 主站点选取，不构成问题。

---

## 4. 六项字节级复核

`gen_delta.py` 逐行回 `gamemd.exe` 只读复算，`verify_delta.py` 独立再算一遍，两者一致（18/18 全 True）：

| 项 | 校验 | 结果 |
|---|---|---|
| 1 | `u32(vt + slot*4) == entry` | 18/18 True |
| 2 | `u32(vt - 4) == COL` | 18/18 True |
| 3 | `u32(COL + 4) == offset` | 18/18 True |
| 4 | `u32(COL + 12) == TD` | 18/18 True |
| 5 | `cstr(TD + 8) == mangled`（内联串） | 18/18 True |
| 6 | capstone 解码 `imm32@site == vt`（`mov`，且体外、== ring4 主站点） | 18/18 True |

附加自检：`rtti_exact_class == row_class`（`mangled == .?AV<行名类>@@`）18/18 True；`install_site_outside_entry` 18/18 True；`site == ring4 主站点` 18/18 True。

`delta.tsv` 独立复核（`verify_delta.py`）：18 行全部 8 列；entry 集 == B1 18 行；第 1/2/3/5/6/7/8 列与当前盘上 `coverage.tsv` 对应行逐字节相同（18/18）；第 4 列严格以原第 4 列字节为前缀（18/18）；grade 列逐字节 == `[已证]`（18/18）；18 行追加正文均含 `④ 活表槽位见证`、含 `§12.6`、不含 `§12.4`（18/18）——**BAD = 0，PASS**。

---

## 5. 行行不同自检

脚本 `gen_delta.py`（结果存 `verify_summary.json`），`verify_delta.py` 独立复核：

1. 18 条实际追加的 ④ 正文取 `set()`：`18/18` 不同。
2. 把每条正文中的 8 位十六进制全部替换为 `ENTRY` 后取 `set()`：`18/18` 不同（不存在「除 entry 外完全相同」的两行）。
3. 四字段多样性：`vt` 15 个不同值、`slot` 7 个、`class` 15 个、`site` 15 个——均非单一值。
4. 手工复核同族同 vt 行：`EMPulseClass::slot5/slot8` 同 `vt=007E87A8` 同 site 但槽号 5/8 不同；三条 `LightSourceClass::slot5/6/8` 同 `vt=007ED028` 同 site 但槽号 5/6/8 不同——均靠槽号区分，属事实同族、非抄袭，已写清区分依据。

结论：**行行不同，无抄袭/复制**（完整 18/18、entry 归一后 18/18）。

样例 ④（第 1 行 `00421730`，披露指针 §12.6）：
```
④ 活表槽位见证：AlphaShapeClass::slot8（vt=007E32A4，槽 8 值=00421730，COL=007FB990 offset=0，RTTI=008182A8→.?AVAlphaShapeClass@@；装表点 0042097C 位于 00420960 体内，entry 体外） ④升级句：AlphaShapeClass::slot8（④ 表属类与行名类一致，均为 AlphaShapeClass；该槽即其 vt=007E32A4 表 slot8，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

---

## 6. `coverage.tsv` 与 `gamemd.exe` sha256（证明未改）

| 文件 | SHA-256 | 字节数 |
|---|---|---|
| `coverage.tsv`（首次读数，已被并发合并覆盖） | `0046BAD980E9055AF61CC94DB9DA72C5346E087A49A00BA0009705807AA6ACF9` | 4,034,144 |
| `coverage.tsv`（生成前，= 生成后 = 写报告前复查 = 现盘） | `95DFAC9E6CEC2D464691D84DF1EF64A0AD850C86500A4CD1348275F0FBC419D1` | 4,040,803 |
| `gamemd.exe`（全程只读） | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` | 4,825,360 |

本执行器**从未写** `coverage.tsv`：`derive_set.py` / `gen_delta.py` 只用 `open(COV,'rb')` / `Get-FileHash` 只读打开；sha 变化来自其它并发会话（非本卡）。`gamemd.exe` 经 `pefile.PE(..., fast_load=True)` 只读打开，sha 始终为卡面给定值。**合并员并表时须以最终盘上 `coverage.tsv` 为准重新校验第 1/2/3/5/6/7/8 列字节一致性**（见 §1 并发留痕）。

---

## 7. 脚本与命令

产物目录内脚本：
- `derive_set.py` —— 独立派生 F1 集合（4 判据 + ③ 干净），打印命中数并写 `derived_set.tsv`（76 行，entry 升序）。
- `scan_fields.py` —— 复用 `PROBE_802\probe.py` 的 `Image/TextScan/vtable_start/col_of/scan_dd/load_atlas_sizes/body_ranges/which_body/col_name_match`，对前 18 行只读回二进制解 vt/COL/TD/RTTI/装表点/函数体，写 `scan_raw.json`。
- `gen_delta.py` —— 读 `scan_raw.json`，按「类一致 + ring4 主站点体外」选表，6 项字节复核 + 精确类一致，生成 `fields.tsv`（14 列，含 `same_source`）/ `delta.tsv` / `verify_summary.json`（披露指针 §12.6）。
- `verify_delta.py` —— 独立复核 delta 列字节一致 / col4 严格前缀 / grade `[已证]` / §12.6 披露 / 6 项字节校验 / 类一致 / 体外 / 行行不同；结果 BAD=0 PASS。
- 中间产物：`derived_set.tsv`、`scan_raw.json`、`verify_summary.json`。

命令（均在 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_F1_B1` 下执行）：
```bash
python derive_set.py
python scan_fields.py
python gen_delta.py
python verify_delta.py
```
只读辅助命令：
```powershell
Get-FileHash -LiteralPath '...\COVERAGE\coverage.tsv' -Algorithm SHA256
Get-FileHash -LiteralPath '...\ra2youli\gamemd.exe' -Algorithm SHA256
```

方法保真度自检（`scan_fields.py` 输出）：`method anchors: OK`（`004011C0=1`、`0054F5C0=44`、`007DC720=437`，与 `probe.py` 的 `ANCHORS` 一致），`.text` 反汇编 1,392,527 条指令 / skip 65（与 `R16_SLOTN_B3` 同口径）。

---

## 8. 边界声明

- 本批**只补 ④ 成文**：在 `delta.tsv` 第 4 列原语义后追加 ④ 文本，**不改 grade**（第 5 列逐字节保持 `[已证]`）、**不改判定**、**不并表**。
- **未写** `COVERAGE\coverage.tsv`、**未写** `PANEL.md` / `R14_COMMON.md` / `R16_PROBE_4GAP\*` / `_cards\` / `_drafts\` / 任何其它卡目录。
- 产物全部在 `lead\next_re_20261117_r14\R16_F1_B1\` 下：`delta.tsv`、`fields.tsv`、`REPORT.md`（另附派生/扫描/生成/复核脚本与中间数据）。
- 每行 ④ 自带披露指针 `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`，节号为重号后的 **§12.6**（不是 §12.4）。
- B1（本批 18 行）取自 76 行派生集合按 entry 升序第 1–18 行；B2 应取第 19–36 行；两批 entry 集合无交集、并集 ⊆ 76 行派生集合。
