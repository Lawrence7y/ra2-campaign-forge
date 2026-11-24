# R16-R4-SLOTN-B1 · 批次 1/3 · 执行报告

> 角色：执行器 · 日期 2026-11-20（R16 第 2 轮）· 本批 15 行（`slotN43.tsv` 数据行 1–15）
> 写域：`lead\next_re_20261117_r14\R16_SLOTN_B1\`（仅此目录）
> 依据裁决：D-47(A)（维持 D-43(A) 优先，§12.3 对「活 vtable 槽位」形态让位 + 整批披露）

---

## 1. 前置核对结果

| 核对项 | 要求 | 实测 | 结论 |
|---|---|---|---|
| `PROBE_802\slotN43.tsv` 数据行数 | 43（1 表头 + 43 数据） | 43（文件 44 行） | 通过 |
| 本批取数范围 | 数据行 1–15（含两端） | 行 1–15 = 文件第 2–16 行 | 通过 |
| 15 行 entry 互不重复 | 15 个不同值 | 15 个不同值 | 通过 |
| 15 行 `col_ok` | 全部 = `match` | 15/15 = `match` | 通过 |
| 15 行 `install_ext` | 全部 = `y` | 15/15 = `y` | 通过 |

权威源：`lead\next_re_20261117_r14\PROBE_802\slotN43.tsv`（未被本执行器修改）。
`work_scan.json`（未被本执行器修改）的 `A_agg.site_of` 与 15 行 `reason` 中的 `ext@` 装表点逐行一致。

---

## 2. 成功 / SKIP

- **成功：15 行**（全部进入 `delta.tsv` / `fields.tsv`）
- **SKIP：0 行**

每行 `<VTADDR>` 都取到，故无「vt 未取得」型 SKIP。COL / offset / RTTI / FUNC 也全部取到（FUNC 中 4 行由反汇编定界取得，非「未取得」）。

逐行字段（`fields.tsv` 全文所见）+ 字节级复核（每一行的 6 项校验全部为 True）：

| # | entry | class | slot | vt | COL/off | RTTI | site | func | status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0045A560 | T_DynamicVectorClass_PAVInfantryClass__ | 2 | 007E43C8 | 007FC298/0 | 00818D28→.?AV?$DynamicVectorClass@PAVInfantryClass@@@@ | 0043B6DB | 0043B680 | OK |
| 2 | 0045A610 | T_DynamicVectorClass_PAVInfantryClass__ | 4 | 007E43C8 | 007FC298/0 | 00818D28→.?AV?$DynamicVectorClass@PAVInfantryClass@@@@ | 0043B6DB | 0043B680 | OK |
| 3 | 0045A680 | T_DynamicVectorClass_PAVFoggedObjectClass__ | 2 | 007E44F4 | 007FC528/0 | 00819230→.?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@ | 00457BFD | 00457AA0 | OK |
| 4 | 0045A730 | T_DynamicVectorClass_PAVFoggedObjectClass__ | 4 | 007E44F4 | 007FC528/0 | 00819230→.?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@ | 00457BFD | 00457AA0 | OK |
| 5 | 00473BA0 | CCFileClass | 10 | 007E16B0 | 007FA590/0 | 00815E58→.?AVCCFileClass@@ | 004014AC | 004011C0 | OK |
| 6 | 00473C50 | CCFileClass | 5 | 007E16B0 | 007FA590/0 | 00815E58→.?AVCCFileClass@@ | 004014AC | 004011C0 | OK |
| 7 | 00473D10 | CCFileClass | 7 | 007E16B0 | 007FA590/0 | 00815E58→.?AVCCFileClass@@ | 004014AC | 004011C0 | OK |
| 8 | 004A9890 | DisplayClass | 36 | 007E6114 | 007FFCB8/0 | 00816BD8→.?AVDisplayClass@@ | 004A8830 | 004A8730 | OK |
| 9 | 004D24A0 | FoggedObjectClass | 6 | 007E8B38 | 00800768/0 | 00822438→.?AVFoggedObjectClass@@ | 004D088D | 004D0860* | OK |
| 10 | 004D2510 | FoggedObjectClass | 5 | 007E8B38 | 00800768/0 | 00822438→.?AVFoggedObjectClass@@ | 004D088D | 004D0860* | OK |
| 11 | 004D27D0 | FoggedObjectClass | 3 | 007E8B38 | 00800768/0 | 00822438→.?AVFoggedObjectClass@@ | 004D088D | 004D0860* | OK |
| 12 | 004D2810 | FoggedObjectClass | 13 | 007E8B38 | 00800768/0 | 00822438→.?AVFoggedObjectClass@@ | 004D088D | 004D0860* | OK |
| 13 | 004D4200 | FootClass | 139 | 007E8C94 | 00800948/0 | 00817B78→.?AVFootClass@@ | 004D345D | 004D31E0 | OK |
| 14 | 004D4280 | FootClass | 151 | 007E8C94 | 00800948/0 | 00817B78→.?AVFootClass@@ | 004D345D | 004D31E0 | OK |
| 15 | 004D4B20 | AircraftClass | 133 | 007E22A4 | 007FB4C0/0 | 00817B90→.?AVAircraftClass@@ | 00413D87 | 00413D20 | OK |

\* 行 9–12 的 FUNC `004D0860` 由反汇编定界取得：`004D085F = C3(ret)` → `004D0860 = 8B 44 24 04(prologue)` → `004D088D = C7 06 38 8B 7E 00(install, imm=007E8B38)` → `004D08AB = C2 04 00(ret 4)` → `004D08B0 = 下一函数`。`W130_atlas\function_atlas.tsv` 未收 `004D0860`（附近有 `004D0870 size=3` 的错位项），故此处以反汇编边界为准；不是写「未取得」。

多表行的表选择（保证「表属类与行名类一致，无归属歧义」）：
- 行 14 `004D4280`：`dd` 命中两张表 —— `007E8C94`（FootClass，site=004D345D）与 `007EB058`（InfantryClass，site=00517ACC）。按 `site_of=004D345D` + 行名类 `FootClass` 取 `007E8C94`。
- 行 15 `004D4B20`：`dd` 命中四张表 —— `007E22A4`（AircraftClass，site=00413D87）、`007E8C94`（FootClass）、`007EB058`（InfantryClass）、`007F5C70`（UnitClass）。按 `site_of=00413D87` + 行名类 `AircraftClass` 取 `007E22A4`。

模板伪名行（1–4）的 `<Class>` 取 `name` 的 `::slotN` 前缀全文（`T_DynamicVectorClass_PAVInfantryClass__` / `T_DynamicVectorClass_PAVFoggedObjectClass__`），RTTI 装饰名 `.?AV?$DynamicVectorClass@PAV…@@@@` 与之对得上（与 `probe.py:col_name_match` 的模板归一化口径一致）。

---

## 3. 15 行 ④ 正文的两两不同性自检

**方法**（脚本 `gen_delta.py`，结果存 `verify_summary.json`）：

1. 收集 15 条实际追加的 ④ 正文，取 `set()`：`len(set(texts)) == 15 / 15`。
2. 更严格地把每条正文中的 8 位十六进制 entry 全部替换为占位符 `ENTRY` 后再取 `set()`：`len(set(norm)) == 15 / 15`。即**不存在**「除 entry 外完全相同」的两行（卡面判不合格的情形）。
3. 四字段多样性统计：`vt` 7 个不同值、`slot` 12 个不同值、`class` 7 个不同值、`site` 7 个不同值 —— 四个字段均非单一值，远超「至少 3 个字段不同」。
4. 手工复核：同 vt 同 site 的行组（1–2 / 3–4 / 5–7 / 9–12 / 13–14）均靠 slot 号区分；跨 vt 行靠 vt/class/site 区分。

结论：**行行不同，无抄袭/复制**。

样例（第 1 行追加正文）：
```
；④ 活表槽位见证：T_DynamicVectorClass_PAVInfantryClass__::slot2（vt=007E43C8，槽 2 值=0045A560，COL=007FC298 offset=0，RTTI=00818D28→.?AV?$DynamicVectorClass@PAVInfantryClass@@@@；装表点 0043B6DB 位于 0043B680 体内，entry 体外） ④升级句：T_DynamicVectorClass_PAVInfantryClass__::slot2（④ 表属类与行名类一致，均为 T_DynamicVectorClass_PAVInfantryClass__；该槽即其 vt=007E43C8 表 slot2，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）
```

---

## 4. `coverage.tsv` 改前改后 sha256（证明未改）

| | SHA-256 |
|---|---|
| 改前 | `325158B588636AA3AA170B74B6F4F0E7E5020CA0AC3960232C1DFEAD42CFCEA2` |
| 改后（生成完成后再取） | `325158B588636AA3AA170B74B6F4F0E7E5020CA0AC3960232C1DFEAD42CFCEA2` |

完全一致。`coverage.tsv` 全程只用只读方式打开（`open(...,'rb')` / `Get-FileHash`），未写入。
`ra2youli\gamemd.exe` 全程只读打开（`pefile.PE(...)` 只读 + `f.read()`），SHA-256 始终为
`73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，未修改。

---

## 5. 用的脚本与命令

产物目录内脚本：
- `R16_SLOTN_B1\scan_fields.py` —— 复用 `PROBE_802\probe.py` 的 `Image/TextScan/vtable_start/col_of/scan_dd/body_ranges/which_body`，只读扫描 15 行，写 `scan_raw.json`。
- `R16_SLOTN_B1\gen_delta.py` —— 读 `scan_raw.json`，回二进制逐字节复核 6 项字段，生成 `fields.tsv` / `delta.tsv` / `verify_summary.json`。

命令（均在 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_SLOTN_B1` 下执行）：
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

字节级复核（`gen_delta.py`，每行 6 项全 True）：
`u32(vt+slot*4)==entry`、`u32(vt-4)==COL`、`u32(COL+4)==offset`、`u32(COL+12)==TD`、`cstr(TD+8)==mangled`、capstone 解码 `imm32@site==vt`。

`delta.tsv` 结构复核（独立 PS 脚本读字节）：15 行全部 8 列；第 1/2/3/5/6/7/8 列与 `coverage.tsv` 对应行逐字节相同（`OK=15 BAD=0`）；第 4 列严格以原第 4 列字节为前缀，其后才追加 `；④ …`。

---

## 6. 边界声明

- 本批**只补 ④ 成文**：在 `delta.tsv` 第 4 列原语义后追加 ④ 文本，**不改 grade**（第 5 列逐字节保持）、**不改判定**、**不并表**。
- **未写** `COVERAGE\coverage.tsv`、**未写** `PANEL.md` / `R14_COMMON.md` / 台账 / 看板 / `_drafts\` / `_cards\` / 其它卡目录。
- 产物全部在 `lead\next_re_20261117_r14\R16_SLOTN_B1\` 下：`delta.tsv`、`fields.tsv`、`REPORT.md`（另附只读扫描脚本与中间 JSON）。
- 每行 ④ 自带披露指针 `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）`，不写成「已过 §12.3」。
