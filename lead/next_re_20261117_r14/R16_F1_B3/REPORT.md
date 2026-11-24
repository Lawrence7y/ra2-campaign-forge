# R16-F1-B3 · F1 缺口 ④ 成文 · 执行报告（派生集合第 37–54 行）

> 角色：执行器 · 日期 2026-11-20（R16 第 7 轮）· 本批 18 行（派生集合按 entry 升序第 37–54 行）
> 写域：`lead\next_re_20261117_r14\R16_F1_B3\`（仅此目录）
> 依据裁决：D-47(A)（维持 D-43(A) 优先，§12.3 对「活 vtable 槽位」形态正式让位 + 整批披露）
> 披露节号：**§12.6**（重号后；不是 §12.4）

---

## 1. 独立派生集合（卡面 §3 第一步，必做）

**权威输入**：`R16_PROBE_4GAP\scan_F1_audit.tsv`（122 数据行，未被本执行器修改）。
**背景报告**：`R16_PROBE_4GAP\REPORT.md`（F1 定义 + `ring4_at` 字段解释）。

### 1.1 判据（逐条写清，脚本 `derive_set.py`）

1. `same_source == no`（④ 与 ② 不同源，守 §12.3 精神；D-47(A) 只对「活 vtable 槽位」形态让位，本报告全批为该形态，仍按卡面要求守此列）。
2. `ring4_at` 能解析出装表指令 `mov <mem>, imm32` 且 `imm32` 指向该行活表 —— 在审计 TSV 里的代理列是 `n_install_decoded >= 1`（本批 76 行全部是 `f_reason=audit_ring4_ctor_install`；`audit_ring4_alloc_reg_pivot` 那 32 行 `n_install_decoded=0`，不入集合）。
3. 装表点位于 entry 体外（装表点所在函数 ≠ 该 entry）—— 代理列 `n_install_outside_body >= 1`。
4. 现盘 `coverage.tsv` 里 `grade == [已证]` 且第 4 列尚不含 `④ 活表槽位见证`。

### 1.2 命中行数（与卡面 76 比对）

| 阶段 | 判据 | 行数 |
|---|---|---:|
| S0 | 全部 F1 缺口行 | 122 |
| S1 | + `same_source == no` | 108 |
| S2 | + `ring4_at` 装表指令可解（`n_install_decoded>=1`） | 76 |
| S3 | + 装表点在 entry 体外（`n_install_outside_body>=1`） | 76 |
| S4 | + 现盘 `[已证]` 且无 `④ 活表槽位见证` | **76** ← 派生集合 |

**派生集合命中 76 行，与卡面转述的 76 完全一致，无差异。** 判据 4 剔除 0 行；76 行的 `f_reason` 全为 `audit_ring4_ctor_install`、`sem_unproved` 全为 `0`（③ 全干净）。

> 读数说明：本批全程读到同一份稳定盘 —— `coverage.tsv` sha256 `95DFAC9E6CEC2D464691D84DF1EF64A0AD850C86500A4CD1348275F0FBC419D1`（4,040,803 B）。该 sha 相对 `R16_PROBE_4GAP` 快照 `0046BAD9…`（4,034,144 B）的 +6,659 B 差异，B2 报告已定位为 `R16_MERGE_SLOTN_B3` 的 13 行并发并表，与本 F1 派生集合 76 行无交集。派生阶段计数与 B1/B2 完全一致（122/108/76/76/76）。

### 1.3 批次切片与交集（硬要求）

76 行按 entry 数值升序排序：第 **1–18** 行 = B1，第 **19–36** 行 = B2，第 **37–54** 行 = **本批 B3**，第 55–76 行留给后续批次。

- 本执行器自己去 `R16_F1_B1\fields.tsv`（18 行）与 `R16_F1_B2\fields.tsv`（18 行）取已用 entry 集合做交集检查：
  - `B1(派生第1-18行) == B1/fields.tsv`：True（18/18 逐值相同）
  - `B2(派生第19-36行) == B2/fields.tsv`：True（18/18 逐值相同）
  - **B3 ∩ B1(fields) = ∅；B3 ∩ B2(fields) = ∅**（硬要求通过）。
- B3 18 行 entry：`006C3890 006C3A10 006C3B90 006C5210 006C5390 006C5510 006C5690 006C5810 006C5990 006C5B10 006C5C90 006C5E10 006C5F90 006C6110 006DBD20 006DBE00 006E3E30 006E57A0`。
- B1∪B2∪B3 = 54 行 ⊆ 派生集合 76 行。

---

## 2. 成功 / SKIP

- **成功：18 行**（全部进入 `delta.tsv` / `fields.tsv`）。
- **SKIP：0 行**；无「vt 未取得」型 SKIP —— **vtaddr 取得 18/18 行**。
- COL / offset / RTTI / 装表点 / 宿主函数也全部取到：18/18 的装表点宿主函数由 atlas `which_body` 命中（无 atlas 缺失、无需 capstone 函数定界兜底）。
- 本批 18 行中：第 37–50 行（14 个 `TClassFactory` 工厂类）各用自己独立的 vt / COL / site / RTTI；第 51/52 行（`Tactical::slot5/slot6`）同表同 vt `007F4348`、同站点 `006D1D54`、同宿主 `006D1C20`，仅槽号 5/6 区分；第 53/54 行（`TActionClass::slot6`、`TagClass::slot6`）各用独立 vt/site。均在 `fields.tsv` 的 `note` 列逐行写明区分依据（§4.2 反抄袭）。

### 2.1 §4.1 类一致改选披露（若有）

**无改选（0 行）。** 本批 18 行每行 `scan_dd(.rdata/.data)` 各命中恰好 **1 张**合法活表（`vtable_start` → COL → TD → `TD+8` 全通过），其 `probe.col_name_match(行名类, mangled)` 全部 `match`（18/18，`T_` 模板伪名按 `TClassFactory` + 内层类双 token 命中），且该表的 install sites 命中 `ring4_at` 指定的装表点（capstone `imm32==vt`）。因此不存在「`site_of` 表属类与行名类不一致」的坑，直接采用唯一候选表，未触发 §4.1 改选。
（同 vt 的多行共享装表点属正常：第 51/52 行 `Tactical` 表有 4 处装表点 `006D1D54/006D1E58/006D1E80/006DC473`、第 53 行 `TActionClass` 表有 5 处、第 54 行 `TagClass` 表有 3 处；本批一律按 ring4_at 指定点取，见 `fields.tsv` note。）

### 2.2 逐行字段（完整见 `fields.tsv`）

| # | entry | class | slot | vt | COL/off | RTTI(mangled) | site | func | status |
|---:|---|---|---:|---|---|---|---|---|---|
| 37 | 006C3890 | T_TClassFactory_VInfantryClass__ | 3 | 007F3C00 | 0080ABB8/0 | 00841928→.?AV?$TClassFactory@VInfantryClass@@@@ | 006C37C9 | 006C37C0 | OK |
| 38 | 006C3A10 | T_TClassFactory_VAnimClass__ | 3 | 007F3C18 | 0080AC08/0 | 00841958→.?AV?$TClassFactory@VAnimClass@@@@ | 006C3949 | 006C3940 | OK |
| 39 | 006C3B90 | T_TClassFactory_VAnimTypeClass__ | 3 | 007F3C30 | 0080AC58/0 | 00841988→.?AV?$TClassFactory@VAnimTypeClass@@@@ | 006C3AC9 | 006C3AC0 | OK |
| 40 | 006C5210 | T_TClassFactory_VFactoryClass__ | 3 | 007F3D98 | 0080B108/0 | 00841CB8→.?AV?$TClassFactory@VFactoryClass@@@@ | 006C5149 | 006C5140 | OK |
| 41 | 006C5390 | T_TClassFactory_VWarheadTypeClass__ | 3 | 007F3DB0 | 0080B158/0 | 00841CE8→.?AV?$TClassFactory@VWarheadTypeClass@@@@ | 006C52C9 | 006C52C0 | OK |
| 42 | 006C5510 | T_TClassFactory_VWeaponTypeClass__ | 3 | 007F3DC8 | 0080B1A8/0 | 00841D20→.?AV?$TClassFactory@VWeaponTypeClass@@@@ | 006C5449 | 006C5440 | OK |
| 43 | 006C5690 | T_TClassFactory_VParticleClass__ | 3 | 007F3DE0 | 0080B1F8/0 | 00841D58→.?AV?$TClassFactory@VParticleClass@@@@ | 006C55C9 | 006C55C0 | OK |
| 44 | 006C5810 | T_TClassFactory_VParticleTypeClass__ | 3 | 007F3DF8 | 0080B248/0 | 00841D88→.?AV?$TClassFactory@VParticleTypeClass@@@@ | 006C5749 | 006C5740 | OK |
| 45 | 006C5990 | T_TClassFactory_VParticleSystemClass__ | 3 | 007F3E10 | 0080B298/0 | 00841DC0→.?AV?$TClassFactory@VParticleSystemClass@@@@ | 006C58C9 | 006C58C0 | OK |
| 46 | 006C5B10 | T_TClassFactory_VParticleSystemTypeClass__ | 3 | 007F3E28 | 0080B2E8/0 | 00841DF8→.?AV?$TClassFactory@VParticleSystemTypeClass@@@@ | 006C5A49 | 006C5A40 | OK |
| 47 | 006C5C90 | T_TClassFactory_VAITriggerTypeClass__ | 3 | 007F3E40 | 0080B338/0 | 00841E38→.?AV?$TClassFactory@VAITriggerTypeClass@@@@ | 006C5BC9 | 006C5BC0 | OK |
| 48 | 006C5E10 | T_TClassFactory_VNeuronClass__ | 3 | 007F3E58 | 0080B388/0 | 00841E70→.?AV?$TClassFactory@VNeuronClass@@@@ | 006C5D49 | 006C5D40 | OK |
| 49 | 006C5F90 | T_TClassFactory_VFoggedObjectClass__ | 3 | 007F3E70 | 0080B3D8/0 | 00841EA0→.?AV?$TClassFactory@VFoggedObjectClass@@@@ | 006C5EC9 | 006C5EC0 | OK |
| 50 | 006C6110 | T_TClassFactory_VAlphaShapeClass__ | 3 | 007F3E88 | 0080B428/0 | 00841ED8→.?AV?$TClassFactory@VAlphaShapeClass@@@@ | 006C6049 | 006C6040 | OK |
| 51 | 006DBD20 | Tactical | 5 | 007F4348 | 0080B9A8/0 | 00842A38→.?AVTactical@@ | 006D1D54 | 006D1C20 | OK |
| 52 | 006DBE00 | Tactical | 6 | 007F4348 | 0080B9A8/0 | 00842A38→.?AVTactical@@ | 006D1D54 | 006D1C20 | OK |
| 53 | 006E3E30 | TActionClass | 6 | 007F443C | 0080BAF0/0 | 00842B78→.?AVTActionClass@@ | 006DD036 | 006DD000 | OK |
| 54 | 006E57A0 | TagClass | 6 | 007F44E0 | 0080BBA0/0 | 008249E8→.?AVTagClass@@ | 006E4E07 | 006E4DE0 | OK |

---

## 3. 18 行 ④ 正文两两不同性自检（§4.2）

`gen_delta.py` 收集 18 条实际追加的 ④ 正文，`verify_delta.py` 独立再核一次（结果见 `verify_summary.json`）：

1. 完整正文取 `set()`：**18/18 不同**。
2. 把每条正文里全部 8 位十六进制替换为占位符 `ENTRY` 后再取 `set()`：**18/18 不同** —— 不存在「除 entry 外完全相同」的两行。
3. 四字段多样性：`vt` **17** 个不同值、`slot` **3** 个、`class` **17** 个、`site` **17** 个 —— 四个字段均非单一值。
4. 同族同 vt 的区分依据：行 51/52 同表同站点、靠槽号 5/6 区分；行 37–50 靠各自独立 vt/class/site 区分；行 53/54 靠类+vt+site 区分。逐行写在 `fields.tsv` 的 `note` 列（§2.2）。

**结论：行行不同，无抄袭/复制。**

样例（第 37 行追加正文，披露指针为 §12.6）：

```
④ 活表槽位见证：T_TClassFactory_VInfantryClass__::slot3（vt=007F3C00，槽 3 值=006C3890，COL=0080ABB8 offset=0，RTTI=00841928→.?AV?$TClassFactory@VInfantryClass@@@@；装表点 006C37C9 位于 006C37C0 体内，entry 体外） ④升级句：T_TClassFactory_VInfantryClass__::slot3（④ 表属类与行名类一致，均为 T_TClassFactory_VInfantryClass__；该槽即其 vt=007F3C00 表 slot3，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

---

## 4. 六项字节级复核（卡面 §5.3）

`gen_delta.py` 逐行回 `gamemd.exe` 只读复算（`verify_summary.json`），并由 `verify_delta.py` 独立复核 delta 结构，全部 18/18 True：

| # | 校验 | 结果 |
|---|---|---|
| 1 | `u32(vt + slot*4) == entry` | 18/18 True |
| 2 | `u32(vt - 4) == COL` | 18/18 True |
| 3 | `u32(COL + 4) == offset` | 18/18 True |
| 4 | `u32(COL + 12) == TD` | 18/18 True |
| 5 | `cstr(TD + 8) == mangled`（内联串，非指针） | 18/18 True |
| 6 | capstone 解码 `imm32@site == vt`（`mov [mem], imm32`） | 18/18 True |

附加自检（防「写得漂亮但不对」）：
- `rtti_class==row_class`（`probe.col_name_match`）18/18 True。
- 装表点在 entry 体外（`which_body(site) != entry` 且 atlas body 区间不含 site）18/18 True。
- `delta.tsv` 独立复核（`verify_delta.py`）：18 行全部 8 列；entry 集 == 派生集合第 37–54 行；第 1/2/3/5/6/7/8 列与 `coverage.tsv` 对应行逐字节相同（18/18）；第 4 列严格以原第 4 列字节为前缀（18/18）；grade 列逐字节 == `[已证]`（18/18）；18 行追加正文均含 `§12.6`（18/18）—— **PASS**。
- `fields.tsv` 14 列表头与卡面 §5.2 逐项一致（含 `same_source` 列，值全为 `no`），status 全 `OK`（18/18）。

---

## 5. `coverage.tsv` 与 `gamemd.exe` sha256（证明未改）

| 时点 | `coverage.tsv` SHA-256 | 字节数 |
|---|---|---|
| 独立派生读数时（`derive_set.py`） | `95DFAC9E6CEC2D464691D84DF1EF64A0AD850C86500A4CD1348275F0FBC419D1` | 4,040,803 |
| 生成 delta 前（`gen_delta.py` cov_before） | `95DFAC9E6CEC2D464691D84DF1EF64A0AD850C86500A4CD1348275F0FBC419D1` | 4,040,803 |
| 生成 delta 后（`gen_delta.py` cov_after） | `95DFAC9E6CEC2D464691D84DF1EF64A0AD850C86500A4CD1348275F0FBC419D1` | 4,040,803 |
| 独立复核时（`verify_delta.py`） | `95DFAC9E6CEC2D464691D84DF1EF64A0AD850C86500A4CD1348275F0FBC419D1` | 4,040,803 |

**本批全程 `coverage.tsv` 未变**（四个时点 sha 全部相同），无并发改写发生；`cov_before == cov_after`。相对 `R16_PROBE_4GAP` 快照 `0046BAD9…` 的差异由 B2 报告定位为 SLOTN_B3 并表，与本批 18 行无交集，不影响字节一致性。

| 文件 | SHA-256 | 字节数 |
|---|---|---|
| `gamemd.exe`（全程只读） | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` | 4,825,360 |

`gamemd.exe` 仅以 `pefile.PE(path, fast_load=True)` + `f.read()` 只读打开，sha256 全程等于卡面给定值（`73201CC0…CF67476`）。

---

## 6. 脚本与命令

产物目录内脚本（全部只读 `gamemd.exe` / `coverage.tsv`，只写本目录）：
- `derive_set.py` —— 从 `scan_F1_audit.tsv` 按卡面 §3 四判据独立派生集合，报阶段计数 / 命中数 / 与 76 比对 / B1·B2·B3 切片与交集（含去 `R16_F1_B1/B2/fields.tsv` 取 entry 做无交集硬检查）。
- `scan_fields.py` —— 复用 `PROBE_802\probe.py` 的 `Image/TextScan/vtable_start/col_of/scan_dd/body_ranges/which_body`，对 18 行只读取数：`ring4_at` token 抽取 + `dd entry` → 表候选 + install sites，写 `scan_raw.json`。
- `diag.py` —— 选 site / 求宿主函数（atlas）+ 判体外 + 6 项字节复核，写 `diag.json`。
- `gen_delta.py` —— 读 `scan_raw.json`/`diag.json`，回二进制独立复核 6 项 + RTTI 类一致 + 体外，生成 `fields.tsv`/`delta.tsv`/`verify_summary.json`（披露指针 §12.6）。
- `verify_delta.py` —— 独立复核 delta 列字节一致 / col4 严格前缀 / 无 witness / §12.6 披露 / fields 14 列结构 / entry 集与排序。

命令（均在 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_F1_B3` 下执行）：

```bash
python derive_set.py
python scan_fields.py
python diag.py
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

**只补 ④ 成文**：在 `delta.tsv` 第 4 列原语义后追加 ④ 文本，**不改 grade**（第 5 列逐字节保持 `[已证]`）、**不改判定**、**不并表**。
未写 `COVERAGE\coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账 / 看板 / `_drafts\` / `_cards\` / 任何其它卡目录（`R16_PROBE_4GAP\`、`R16_F1_B1\`、`R16_F1_B2\`、`R16_SLOTN_*\`、`PROBE_802\` 全部只读未改）。产物全部在 `lead\next_re_20261117_r14\R16_F1_B3\` 下：`delta.tsv`、`fields.tsv`、`REPORT.md`（另附只读扫描/生成/复核脚本与中间 JSON）。每行 ④ 自带披露指针 `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`，不写成「已过 §12.3」；节号为重号后的 **§12.6**（不是 §12.4）。
