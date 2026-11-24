# R16-R4-SLOTN-B2 · 批次 2/3 · 执行报告

> 角色：执行器 · 日期 2026-11-20（R16 第 3 轮）· 本批 15 行（`slotN43.tsv` 数据行 16–30）
> 写域：`lead\next_re_20261117_r14\R16_SLOTN_B2\`（仅此目录）
> 依据裁决：D-47(A)（维持 D-43(A) 优先，§12.3 对「活 vtable 槽位」形态让位 + 整批披露）

---

## 1. 前置核对结果

| 核对项 | 要求 | 实测 | 结论 |
|---|---|---|---|
| `PROBE_802\slotN43.tsv` 数据行数 | 43（1 表头 + 43 数据） | 43（文件 44 行） | 通过 |
| 本批取数范围 | 数据行 16–30（含两端） | 行 16–30 = 文件第 17–31 行 | 通过 |
| 15 行 entry 互不重复 | 15 个不同值 | 15 个不同值 | 通过 |
| 与批次 1 交集 | 空 | 空（`R16_SLOTN_B1\fields.tsv` 15 个 entry 与本批 15 个无交集） | 通过 |
| 15 行 `col_ok` | 全部 = `match` | 15/15 = `match` | 通过 |
| 15 行 `install_ext` | 全部 = `y` | 15/15 = `y` | 通过 |
| 15 行在 coverage.tsv 中存在 | 全部存在 | 15/15 存在 | 通过 |

权威源：`lead\next_re_20261117_r14\PROBE_802\slotN43.tsv`（未被本执行器修改）。
`work_scan.json`（未被本执行器修改）的 `A_agg.site_of` 与 15 行 `reason` 中的 `ext@` 装表点逐行一致（惟行 30 的多表歧义见 §2.1）。
`scan_fields.py` 在跑前用断言复核了「43 行 / 本批 15 行 entry 互异 / 与批次 1 交集为空 / 全 col_ok=match / 全 install_ext=y」，全部通过（输出 `batch1 intersection: EMPTY (15 vs 15)`）。

---

## 2. 成功 / SKIP

- **成功：15 行**（全部进入 `delta.tsv` / `fields.tsv`）
- **SKIP：0 行**

每行 `<VTADDR>` 都取到（15/15），故无「vt 未取得」型 SKIP。COL / offset / RTTI / FUNC 也全部取到：
其中 5 行的 FUNC 由 capstone 反汇编定界取得（atlas 未收该装表点宿主），非「未取得」。

### 2.1 行 30（005B2FD0 InfantryClass::slot124）的多表类一致选择

该 entry 的 `dd` 命中 7 张表（BuildingClass / FootClass / InfantryClass / MissionClass / RadioClass / TechnoClass / UnitClass），均在 slot 124。`work_scan.json:A_agg.site_of[005B2FD0]=0043B71F` 是「第一命中表的第一装表点」启发式结果，落在 **BuildingClass** 表 `vt=007E3EBC`（`TD+8=.?AVBuildingClass@@`）——与行名类 `InfantryClass` 冲突，若照抄会违反审计 C「④ 表属类与行名类一致」。

按批次 1 的「多表行按 site + 类名一致选表」原则，本行改取**类一致的 InfantryClass 表** `vt=007EB058`（`COL=008033B8`，`TD=00825508`，`TD+8=.?AVInfantryClass@@`，`col_ok=match`）。因 `0043B71F` 的 `imm32=007E3EBC`（BuildingClass），不能用作本表的装表点（审计 B6 要求 `imm32@site==vt`）；改取该 InfantryClass 表自己的装表点 `00517D9D`（`capstone` 解码 `mov dword [esi], 0x7eb058`，imm32=`007EB058`，位于函数 `00517D90` 体内，entry 体外）。该覆写在 `fields.tsv` 的 `source_of_vtaddr`/`note` 中逐字披露，非编造。

其余多表行（16 / 21 / 22 / 23 / 24）的 site_of 恰好与行名类一致，沿用 site_of 选表即可：
- 行 16/23（AircraftClass::slot134/150）：4 表持有，按 `site=00413D87` + 类名取 `007E22A4`
- 行 21/22（FootClass::slot144/140）：3 表持有，按 `site=004D345D` + 类名取 `007E8C94`
- 行 24（InfantryClass::slot132）：单表 `007EB058`，`site=00517ACC`

逐行字段（完整见 `fields.tsv`）：

| # | entry | class | slot | vt | COL/off | RTTI(mangled) | site | func | status |
|---|---|---|---|---|---|---|---|---|---|
| 16 | 004D4CB0 | AircraftClass | 134 | 007E22A4 | 007FB4C0/0 | 00817B90→.?AVAircraftClass@@ | 00413D87 | 00413D20 | OK |
| 17 | 004D4DC0 | FootClass | 132 | 007E8C94 | 00800948/0 | 00817B78→.?AVFootClass@@ | 004D345D | 004D31E0 | OK |
| 18 | 004D5070 | FootClass | 135 | 007E8C94 | 00800948/0 | 00817B78→.?AVFootClass@@ | 004D345D | 004D31E0 | OK |
| 19 | 004D5350 | FootClass | 138 | 007E8C94 | 00800948/0 | 00817B78→.?AVFootClass@@ | 004D345D | 004D31E0 | OK |
| 20 | 004D6AA0 | FootClass | 136 | 007E8C94 | 00800948/0 | 00817B78→.?AVFootClass@@ | 004D345D | 004D31E0 | OK |
| 21 | 004D9290 | FootClass | 144 | 007E8C94 | 00800948/0 | 00817B78→.?AVFootClass@@ | 004D345D | 004D31E0 | OK |
| 22 | 004DA2C0 | FootClass | 140 | 007E8C94 | 00800948/0 | 00817B78→.?AVFootClass@@ | 004D345D | 004D31E0 | OK |
| 23 | 004DDF90 | AircraftClass | 150 | 007E22A4 | 007FB4C0/0 | 00817B90→.?AVAircraftClass@@ | 00413D87 | 00413D20 | OK |
| 24 | 0051F3E0 | InfantryClass | 132 | 007EB058 | 008033B8/0 | 00825508→.?AVInfantryClass@@ | 00517ACC | 00517A50 | OK |
| 25 | 0053C6A0 | T_DynamicVectorClass_PBVAnimClass__ | 2 | 007EBFCC | 008047B8/0 | 00828000→.?AV?$DynamicVectorClass@PBVAnimClass@@@@ | 0053959D | 00539580* | OK |
| 26 | 005514B0 | T_DynamicVectorClass_PAVLaserDrawClass__ | 2 | 007ECEDC | 00804DF0/0 | 00829710→.?AV?$DynamicVectorClass@PAVLaserDrawClass@@@@ | 0054FDDD | 0054FDC0* | OK |
| 27 | 00551560 | T_DynamicVectorClass_PAVLaserDrawClass__ | 4 | 007ECEDC | 00804DF0/0 | 00829710→.?AV?$DynamicVectorClass@PAVLaserDrawClass@@@@ | 0054FDDD | 0054FDC0* | OK |
| 28 | 00557090 | T_DynamicVectorClass_PAVLineTrail__ | 2 | 007ED0CC | 008051A8/0 | 00829D78→.?AV?$DynamicVectorClass@PAVLineTrail@@@@ | 005569BD | 005569A0* | OK |
| 29 | 00557140 | T_DynamicVectorClass_PAVLineTrail__ | 4 | 007ED0CC | 008051A8/0 | 00829D78→.?AV?$DynamicVectorClass@PAVLineTrail@@@@ | 005569BD | 005569A0* | OK |
| 30 | 005B2FD0 | InfantryClass | 124 | 007EB058 | 008033B8/0 | 00825508→.?AVInfantryClass@@ | 00517D9D | 00517D90* | OK |

\* 行 25/26/27/28/29/30 的 FUNC 由 capstone 反汇编定界（atlas 未收该装表点宿主）：
- 行 25：`00539580 = 31 C0(xor eax,eax)` prologue → `0053959D = C7 05 60 FA A9 00 CC BF 7E 00(install imm=007EBFCC)` → `005395BC = C3(ret)`
- 行 26/27：`0054FDC0 = 31 C0` prologue → `0054FDDD = C7 05 78 C8 AB 00 DC CE 7E 00(imm=007ECEDC)` → `0054FDFC = C3(ret)`
- 行 28/29：`005569A0 = 31 C0` prologue → `005569BD = C7 05 78 CB AB 00 CC D0 7E 00(imm=007ED0CC)` → `005569DC = C3(ret)`
- 行 30：`00517D90 = 83 EC 08(sub esp,8)` prologue → `00517D9D = C7 06 00 7E 05 00(mov [esi],0x7EB058)` → 函数体（InstallShield 类构造器）

模板伪名行（25–29）的 `<Class>` 取 `name` 的 `::slotN` 前缀全文（`T_DynamicVectorClass_PBVAnimClass__` 等），RTTI 装饰名 `.?AV?$DynamicVectorClass@…@@@@` 与之对得上（与 `probe.py:col_name_match` 的模板归一化口径一致，`rtti_class==row_class:True` 已逐行复核）。

---

## 3. 15 行 ④ 正文的两两不同性自检

**方法**（脚本 `gen_delta.py`，结果存 `verify_summary.json`）：

1. 收集 15 条实际追加的 ④ 正文，取 `set()`：`len(set(texts)) == 15 / 15`。
2. 更严格地把每条正文中的 8 位十六进制全部替换为占位符 `ENTRY` 后再取 `set()`：`len(set(norm)) == 15 / 15`。即**不存在**「除 entry 外完全相同」的两行（卡面判不合格的情形）。
3. 四字段多样性统计：`vt` 6 个不同值、`slot` 11 个不同值、`class` 6 个不同值、`site` 7 个不同值 —— 四个字段均非单一值，远超「至少 3 个字段不同」。
4. 手工复核：同 vt 同 site 的行组（行 16/23 皆 AircraftClass 但 slot 134/150；行 17–22 皆 FootClass 但 slot 132/135/138/136/144/140；行 26/27 同 vt 但 slot 2/4；行 28/29 同 vt 但 slot 2/4；行 24/30 同 vt 但 slot 132/124 且 site 00517ACC/00517D9D）均靠 slot（及 site）区分；跨 vt 行靠 vt/class/site 区分。

结论：**行行不同，无抄袭/复制**（完整正文 15/15 不同；entry 归一后仍 15/15 不同）。

样例（第 16 行追加正文）：
```
④ 活表槽位见证：AircraftClass::slot134（vt=007E22A4，槽 134 值=004D4CB0，COL=007FB4C0 offset=0，RTTI=00817B90→.?AVAircraftClass@@；装表点 00413D87 位于 00413D20 体内，entry 体外） ④升级句：AircraftClass::slot134（④ 表属类与行名类一致，均为 AircraftClass；该槽即其 vt=007E22A4 表 slot134，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）
```

---

## 4. 六项字节级复核结果

`gen_delta.py` 逐行回 `gamemd.exe` 只读复算（结果存 `verify_summary.json`，15/15 全 True）：

| 项 | 校验 | 结果 |
|---|---|---|
| 1 | `u32(vt + slot*4) == entry` | 15/15 True |
| 2 | `u32(vt - 4) == COL` | 15/15 True |
| 3 | `u32(COL + 4) == offset` | 15/15 True |
| 4 | `u32(COL + 12) == TD` | 15/15 True |
| 5 | `cstr(TD + 8) == mangled`（内联串） | 15/15 True |
| 6 | capstone 解码 `imm32@site == vt`（`mov [reg+disp], imm32`） | 15/15 True |

附加自检（审计 C 的防「写得漂亮但不对」）：`rtti_class==row_class`（`probe.col_name_match`）15/15 True —— 含行 30 的类一致选表修正。
`delta.tsv` 独立复核（只读 PS/Python 脚本读字节）：15 行全部 8 列；第 1/2/3/5/6/7/8 列与 `coverage.tsv` 对应行逐字节相同（`OK=15 BAD=0`）；第 4 列严格以原第 4 列字节为前缀，其后才追加 `；④ …`。

---

## 5. `coverage.tsv` 改前改后 sha256（证明未改）

`gen_delta.py` 在同一次运行中，于生成 `delta.tsv` 前后各取一次 `coverage.tsv` 的 SHA-256：

| | SHA-256 |
|---|---|
| 改前（本执行器生成前） | `2BCA384650AC31BCFC9661280A1863C2D51C6548B96F5EE372DE94EDDA8104A6` |
| 改后（生成完成后再取） | `2BCA384650AC31BCFC9661280A1863C2D51C6548B96F5EE372DE94EDDA8104A6` |

完全一致，证明**本执行器的生成过程未写 `coverage.tsv`**。本执行器全程只用 `open(COV,'rb')` / `Get-FileHash` 只读打开，未写入。

> **外部变更留痕（透明披露）**：本执行器会话开始时（2026-11-20 约 22:59）`coverage.tsv` 的 SHA-256 为 `325158B588636AA3AA170B74B6F4F0E7E5020CA0AC3960232C1DFEAD42CFCEA2`（与批次 1 REPORT 记录值一致）。会话期间另一并发进程于 **23:02:33** 改写了该文件，使哈希变为上表 `2BCA3846…`。该改写**不是本执行器所为**（本执行器脚本对 coverage 仅只读打开）。本批 `delta.tsv` 的第 1/2/3/5/6/7/8 列与**当前盘上** `coverage.tsv` 逐字节一致（见 §4），合并员并表时应以最终盘上版本为准。

`ra2youli\gamemd.exe` 全程只读打开（`pefile.PE(...)` 只读 + `f.read()`），SHA-256 始终为
`73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（4,825,360 B），未修改。

---

## 6. 用的脚本与命令

产物目录内脚本：
- `R16_SLOTN_B2\scan_fields.py` —— 复用 `PROBE_802\probe.py` 的 `Image/TextScan/vtable_start/col_of/scan_dd/body_ranges/which_body`，只读扫描本批 15 行，写 `scan_raw.json`。
- `R16_SLOTN_B2\gen_delta.py` —— 读 `scan_raw.json`，回二进制逐字节复核 6 项 + RTTI 类一致，生成 `fields.tsv` / `delta.tsv` / `verify_summary.json`。

命令（均在 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_SLOTN_B2` 下执行）：
```bash
python scan_fields.py
python gen_delta.py
```
只读辅助命令：
```powershell
Get-FileHash -LiteralPath '...\COVERAGE\coverage.tsv' -Algorithm SHA256
Get-FileHash -LiteralPath '...\ra2youli\gamemd.exe' -Algorithm SHA256
```

方法保真度自检（`scan_fields.py` 输出）：`method anchors: OK`（`004011C0=1`、`0054F5C0=44`、`007DC720=437`，与 `probe.py` 的 `ANCHORS` 一致），`.text` 反汇编 1,392,527 条指令 / skip 65。

---

## 7. 边界声明

- 本批**只补 ④ 成文**：在 `delta.tsv` 第 4 列原语义后追加 ④ 文本，**不改 grade**（第 5 列逐字节保持）、**不改判定**、**不并表**。
- **未写** `COVERAGE\coverage.tsv`、**未写** `PANEL.md` / `R14_COMMON.md` / `PROBE_802\*` / `_cards\` / `_drafts\` / 任何其它卡目录（含 `R16_SLOTN_B1\` 只读未改）。
- 产物全部在 `lead\next_re_20261117_r14\R16_SLOTN_B2\` 下：`delta.tsv`、`fields.tsv`、`REPORT.md`（另附只读扫描/生成脚本与中间 JSON）。
- 每行 ④ 自带披露指针 `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）`，不写成「已过 §12.3」。
