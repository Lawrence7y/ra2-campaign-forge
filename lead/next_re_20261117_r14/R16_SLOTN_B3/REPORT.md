# R16-R4-SLOTN-B3 · 批次 3/3 · 执行报告（43 行收官）

> 角色：执行器 · 日期 2026-11-20（R16 第 4 轮）· 本批 13 行（`slotN43.tsv` 数据行 31–43）
> 写域：`lead\next_re_20261117_r14\R16_SLOTN_B3\`（仅此目录）
> 依据裁决：D-47(A)（维持 D-43(A) 优先，§12.3 对「活 vtable 槽位」形态让位 + 整批披露）
> 披露节号：**§12.6**（重号后；不是 §12.4）

---

## 1. 前置 5 项自核结果

| # | 核对项 | 要求 | 实测 | 结论 |
|---|---|---|---|---|
| 1 | `PROBE_802\slotN43.tsv` 数据行数 | 43（1 表头 + 43 数据） | 43（文件 44 行） | 通过 |
| 2 | 本批 13 行 entry 互不重复 | 13 个不同值 | 13 个不同值 | 通过 |
| 3 | 与批次 1/2 交集为空、三批并集 = 43 | 交集 ∅ / 并集 43 | B1∩B3=∅、B2∩B3=∅；B1(15)+B2(15)+B3(13)=43，并集 43 | 通过 |
| 4 | 13 行 `col_ok=match`、`install_ext=y` | 全 match / 全 y | 13/13 match、13/13 y | 通过 |
| 5 | 13 行在 `coverage.tsv` 存在且 grade=`[已证]` | 全存在、全 `[已证]` | 13/13 存在、13/13 `[已证]` | 通过 |

权威源：`lead\next_re_20261117_r14\PROBE_802\slotN43.tsv`（未被本执行器修改）。
批次 1 的 entry 集合取 `R16_SLOTN_B1\fields.tsv`（15 行），批次 2 取 `R16_SLOTN_B2\fields.tsv`（15 行），均为只读；本批 13 行与二者交集均为空，三批并集正好 43 行——**三批无重叠、无遗漏**。
`scan_fields.py` 在跑前用断言复核了全部 5 项（输出 `B1/B2 intersection: EMPTY ; union = 43`），全部通过。
`work_scan.json`（未被本执行器修改）的 `A_agg.site_of` 与 13 行 `reason` 中的 `ext@` 装表点逐行一致（惟行 32/33 的多表类歧义见 §2.1）。

---

## 2. 成功 / SKIP

- **成功：13 行**（全部进入 `delta.tsv` / `fields.tsv`）
- **SKIP：0 行**

每行 `<VTADDR>` 都取到（13/13），故无「vt 未取得」型 SKIP。COL / offset / RTTI / 装表点也全部取到：其中 4 行的 FUNC 由 capstone 反汇编定界取得（atlas 未收该装表点宿主），非「未取得」。

### 2.1 行 32/33（005B3570/005B35E0 InfantryClass::slot123/122）的多表类一致选择（§3.1）

这两条 entry 的 `dd` 各命中 7 张表（BuildingClass / FootClass / InfantryClass / MissionClass / RadioClass / TechnoClass / UnitClass），均在对应 slot。`work_scan.json:A_agg.site_of[005B3570]=A_agg.site_of[005B35E0]=0043B71F` 是「第一命中表的第一装表点」启发式结果，落在 **BuildingClass** 表 `vt=007E3EBC`（`TD+8=.?AVBuildingClass@@`）——与行名类 `InfantryClass` 冲突，若照抄会违反审计 C「④ 表属类与行名类一致」。这正是卡面 §3.1 点明、批次 2 行 30 踩到的同一个坑。

按「类一致优先」另选：两行均改取**类一致的 InfantryClass 表** `vt=007EB058`（`COL=008033B8`，`TD=00825508`，`TD+8=.?AVInfantryClass@@`，`col_ok=match`）。因 `0043B71F` 的 `imm32=007E3EBC`（BuildingClass），不能用作本表的装表点（审计 B6 要求 `imm32@site==vt`）；改取该 InfantryClass 表自己的装表点：
- 行 32（slot123）：`00517D9D`（`capstone` 解码 `mov [esi], 0x7EB058`，imm32=`007EB058`，位于函数 `00517D90` 体内，entry 体外）；
- 行 33（slot122）：`00521A11`（同样 `imm32=007EB058`，位于函数 `00521960` 体内，atlas 命中，entry 体外）——与行 32 取不同装表点以增强行行不同性。

两处覆写在 `fields.tsv` 的 `source_of_vtaddr`/`note` 中逐字披露（`CLASS_FIX: site_of=0043B71F(BuildingClass) 弃用, 改取类一致表 vt=007EB058 / site=… / func=…`），非编造。行 32 的 final candidate 经 6 项字节复核 + `rtti_class==row_class` 全部 True。

其余多表行（行 31/34/35 MissionClass）的 `site_of=005B2DE9` 的 `imm32=007EDCC0` 恰为 MissionClass 表，与行名类一致，沿用 site_of 选表即可（另一同槽表为 RadioClass `007F0508`，未采用）。

逐行字段（完整见 `fields.tsv`）：

| # | entry | class | slot | vt | COL/off | RTTI(mangled) | site | func | status |
|---|---|---|---|---|---|---|---|---|---|
| 31 | 005B3060 | MissionClass | 23 | 007EDCC0 | 00805D28/0 | 00817B18→.?AVMissionClass@@ | 005B2DE9 | 005B2DA0 | OK |
| 32 | 005B3570 | InfantryClass | 123 | 007EB058 | 008033B8/0 | 00825508→.?AVInfantryClass@@ | 00517D9D* | 00517D90* | OK |
| 33 | 005B35E0 | InfantryClass | 122 | 007EB058 | 008033B8/0 | 00825508→.?AVInfantryClass@@ | 00521A11* | 00521960* | OK |
| 34 | 005B3650 | MissionClass | 125 | 007EDCC0 | 00805D28/0 | 00817B18→.?AVMissionClass@@ | 005B2DE9 | 005B2DA0 | OK |
| 35 | 005B36B0 | MissionClass | 126 | 007EDCC0 | 00805D28/0 | 00817B18→.?AVMissionClass@@ | 005B2DE9 | 005B2DA0 | OK |
| 36 | 005B4630 | MixFileClass | 0 | 007EDF50 | 00805DE0/0 | 0082C318→.?AVMixFileClass@@ | 005B3C52 | 005B3C20 | OK |
| 37 | 00653100 | RadarClass | 16 | 007F0344 | 008083C0/0 | 00816BF8→.?AVRadarClass@@ | 00652B45 | 00652960 | OK |
| 38 | 0065CBF0 | RawFileClass | 5 | 007F0904 | 00808790/0 | 00815DF8→.?AVRawFileClass@@ | 0065CA03 | 0065CA00 | OK |
| 39 | 006B1850 | T_DynamicVectorClass_PAVSlaveManagerClass__ | 2 | 007F315C | 00809620/0 | 0083FCD0→.?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@ | 006AF13D | 006AF120* | OK |
| 40 | 006B1900 | T_DynamicVectorClass_PAVSlaveManagerClass__ | 4 | 007F315C | 00809620/0 | 0083FCD0→.?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@ | 006AF13D | 006AF120* | OK |
| 41 | 006B8660 | T_DynamicVectorClass_PAVSpawnManagerClass__ | 2 | 007F35E4 | 00809A08/0 | 008400E0→.?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@ | 006B6C2D | 006B6C10* | OK |
| 42 | 006B8710 | T_DynamicVectorClass_PAVSpawnManagerClass__ | 4 | 007F35E4 | 00809A08/0 | 008400E0→.?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@ | 006B6C2D | 006B6C10* | OK |
| 43 | 006F9E50 | TechnoClass | 23 | 007F4960 | 0080C058/0 | 00817B58→.?AVTechnoClass@@ | 006F3130 | 006F2B40 | OK |

\* 行 32/33 的 site/func 为类一致改选值；行 39/40/41/42 的 FUNC 由 capstone 反汇编定界（atlas 未收该装表点宿主）：
- 行 39/40：`006AF120 = 31 C0(xor eax,eax) + 68 60 F1 6A 00(push 0x6AF160)` prologue → `006AF13D = C7 05 F0 B5 B0 00 5C 31 7F 00(mov [0xB0B5F0], 0x7F315C)` → `006AF15C = C3(ret)`；
- 行 41/42：`006B6C10 = 31 C0 + 68 50 6C 6B 00(push 0x6B6C50)` prologue → `006B6C2D = C7 05 80 B8 B0 00 E4 35 7F 00(mov [0xB0B880], 0x7F35E4)` → `006B6C4C = C3(ret)`。

模板伪名行（39–42）的 `<Class>` 取 `name` 的 `::slotN` 前缀全文，RTTI 装饰名 `.?AV?$DynamicVectorClass@…@@@@` 与之对得上（`probe.py:col_name_match` 的模板归一化口径，`rtti_class==row_class:True` 已逐行复核）。

---

## 3. 13 行 ④ 正文的两两不同性自检

**方法**（脚本 `gen_delta.py`，结果存 `verify_summary.json`；另由 `verify_delta.py` 独立复核）：

1. 收集 13 条实际追加的 ④ 正文，取 `set()`：`len(set(texts)) == 13 / 13`。
2. 更严格地把每条正文中的 8 位十六进制全部替换为占位符 `ENTRY` 后再取 `set()`：`len(set(norm)) == 13 / 13`。即**不存在**「除 entry 外完全相同」的两行（卡面判不合格的情形）。
3. 四字段多样性统计：`vt` 8 个不同值、`slot` 10 个不同值、`class` 8 个不同值、`site` 9 个不同值 —— 四个字段均非单一值，远超「至少 3 个字段不同」。
4. 手工复核：同 vt 同 site 的行组（行 31/34/35 皆 MissionClass::slot23/125/126，靠 slot 区分；行 39/40 同 vt 同 site 但 slot 2/4；行 41/42 同 vt 同 site 但 slot 2/4；行 32/33 同 vt 但 slot 123/122 且 site 00517D9D/00521A11）均靠 slot（及 site）区分；跨 vt 行靠 vt/class/site 区分。

结论：**行行不同，无抄袭/复制**（完整正文 13/13 不同；entry 归一后仍 13/13 不同）。

样例（第 31 行追加正文，注意披露指针为 §12.6）：
```
④ 活表槽位见证：MissionClass::slot23（vt=007EDCC0，槽 23 值=005B3060，COL=00805D28 offset=0，RTTI=00817B18→.?AVMissionClass@@；装表点 005B2DE9 位于 005B2DA0 体内，entry 体外） ④升级句：MissionClass::slot23（④ 表属类与行名类一致，均为 MissionClass；该槽即其 vt=007EDCC0 表 slot23，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

---

## 4. 六项字节级复核结果

`gen_delta.py` 逐行回 `gamemd.exe` 只读复算（结果存 `verify_summary.json`，13/13 全 True），并由 `verify_delta.py` 独立再算一次（13/13 全 True）：

| 项 | 校验 | 结果 |
|---|---|---|
| 1 | `u32(vt + slot*4) == entry` | 13/13 True |
| 2 | `u32(vt - 4) == COL` | 13/13 True |
| 3 | `u32(COL + 4) == offset` | 13/13 True |
| 4 | `u32(COL + 12) == TD` | 13/13 True |
| 5 | `cstr(TD + 8) == mangled`（内联串） | 13/13 True |
| 6 | capstone 解码 `imm32@site == vt`（`mov [reg+disp], imm32`） | 13/13 True |

附加自检（审计 C 的防「写得漂亮但不对」）：`rtti_class==row_class`（`probe.col_name_match`）13/13 True —— 含行 32/33 的类一致选表修正。

`delta.tsv` 独立复核（`verify_delta.py` 只读读字节）：13 行全部 8 列；entry 集 == 数据行 31–43；第 1/2/3/5/6/7/8 列与 `coverage.tsv` 对应行逐字节相同（`13/13`）；第 4 列严格以原第 4 列字节为前缀（`13/13`）；grade 列逐字节 == `[已证]`（`13/13`）；13 行追加正文均含 `§12.6` 且均不含 `§12.4`（`13/13`）——**BAD=0**。

---

## 5. `coverage.tsv` 与 `gamemd.exe` sha256（证明未改）

`gen_delta.py` 在同一次运行中，于生成 `delta.tsv` 前后各取一次 `coverage.tsv` 的 SHA-256，随后又在写报告前独立复查一次，三者一致：

| 文件 | SHA-256 | 字节数 |
|---|---|---|
| `coverage.tsv`（生成前） | `2BCA384650AC31BCFC9661280A1863C2D51C6548B96F5EE372DE94EDDA8104A6` | 4,018,942 |
| `coverage.tsv`（生成后） | `2BCA384650AC31BCFC9661280A1863C2D51C6548B96F5EE372DE94EDDA8104A6` | 4,018,942 |
| `coverage.tsv`（写报告前复查） | `2BCA384650AC31BCFC9661280A1863C2D51C6548B96F5EE372DE94EDDA8104A6` | 4,018,942 |
| `gamemd.exe`（全程只读） | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` | 4,825,360 |

两者均未修改：本执行器全程只用 `open(COV,'rb')` / `Get-FileHash` 只读打开 `coverage.tsv`；`gamemd.exe` 经 `pefile.PE(...)` + `f.read()` 只读打开，SHA-256 始终为卡面给定值。

> **并发合并留痕**：本批执行期间 `coverage.tsv` 的 SHA-256 稳定为 `2BCA3846…`（与批次 2 REPORT 记录值一致），未发生会话内变更。本批 `delta.tsv` 的第 1/2/3/5/6/7/8 列与**当前盘上** `coverage.tsv` 逐字节一致（见 §4）；合并员并表时应以最终盘上版本为准。若盘上版本在并表前再变，需重新校验上述字节一致性。

---

## 6. 用的脚本与命令

产物目录内脚本：
- `R16_SLOTN_B3\scan_fields.py` —— 复用 `PROBE_802\probe.py` 的 `Image/TextScan/vtable_start/col_of/scan_dd/body_ranges/which_body`，只读扫描本批 13 行，跑前断言 5 项前置核对（含与 B1/B2 交集为空、并集=43），写 `scan_raw.json`。
- `R16_SLOTN_B3\gen_delta.py` —— 读 `scan_raw.json`，回二进制逐字节复核 6 项 + RTTI 类一致，应用两处类一致选表覆写（§2.1）与四处 capstone 函数定界，生成 `fields.tsv` / `delta.tsv` / `verify_summary.json`（披露指针 §12.6）。
- `R16_SLOTN_B3\verify_delta.py` —— 独立复核 delta 列字节一致 / col4 严格前缀 / grade `[已证]` / §12.6 披露 / 6 项字节校验 / rtti 类一致。
- `R16_SLOTN_B3\inspect_sites.py`、`inspect_func.py`、`inspect_body2.py` —— 只读诊断脚本（装表点 imm32 解码、函数体定界）。

命令（均在 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_SLOTN_B3` 下执行）：
```bash
python scan_fields.py
python gen_delta.py
python verify_delta.py
```
只读辅助命令：
```powershell
Get-FileHash -LiteralPath '...\COVERAGE\coverage.tsv' -Algorithm SHA256
Get-FileHash -LiteralPath '...\ra2youli\gamemd.exe' -Algorithm SHA256
```

方法保真度自检（`scan_fields.py` 输出）：`method anchors: OK`（`004011C0=1`、`0054F5C0=44`、`007DC720=437`，与 `probe.py` 的 `ANCHORS` 一致），`.text` 反汇编 1,392,527 条指令 / skip 65。

---

## 7. 边界声明

- 本批**只补 ④ 成文**：在 `delta.tsv` 第 4 列原语义后追加 ④ 文本，**不改 grade**（第 5 列逐字节保持 `[已证]`）、**不改判定**、**不并表**。
- **未写** `COVERAGE\coverage.tsv`、**未写** `PANEL.md` / `R14_COMMON.md` / `PROBE_802\*` / `_cards\` / `_drafts\` / 任何其它卡目录（`R16_SLOTN_B1\`、`R16_SLOTN_B2\` 只读未改）。
- 产物全部在 `lead\next_re_20261117_r14\R16_SLOTN_B3\` 下：`delta.tsv`、`fields.tsv`、`REPORT.md`（另附只读扫描/生成/复核脚本与中间 JSON）。
- 每行 ④ 自带披露指针 `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`，不写成「已过 §12.3」；节号为重号后的 **§12.6**（不是 §12.4）。
- 三批（B1 15 行 + B2 15 行 + B3 13 行）并集正好 43 行、两两交集为空，本批为 43 行收官批次。
