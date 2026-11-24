# R16-F1-B4 · F1 缺口 ④ 成文 · 执行报告（派生集合第 55–72 行）

> 角色：执行器 · 日期 2026-11-20（R16 第 7 轮）· 本批 18 行（派生集合按 entry 升序第 55–72 行）
> 写域：`lead\next_re_20261117_r14\R16_F1_B4\`（仅此目录）
> 依据裁决：D-47(A)（维持 D-43(A) 优先，§12.3 对「活 vtable 槽位」形态正式让位 + 整批披露）
> 披露节号：**§12.6**（重号后；不是 §12.4）

---

## 1. 独立派生集合（卡面 §3 第一步，必做）

**权威输入**：`R16_PROBE_4GAP\scan_F1_audit.tsv`（122 数据行，未被本执行器修改）。
**背景报告**：`R16_PROBE_4GAP\REPORT.md`（F1 定义 + `ring4_at` 字段解释）。

### 1.1 判据（逐条写清，脚本 `derive_set.py`）

1. `same_source == no`（④ 与 ② 不同源，守 §12.3 精神；D-47(A) 只对「活 vtable 槽位」形态让位，本报告全批为该形态，仍按卡面要求守此列）。
2. `ring4_at` 能解析出装表指令 `mov <mem>, imm32` 且 `imm32` 指向该行活表 —— 在审计 TSV 里的代理列是 `n_install_decoded >= 1`（本批命中行全部是 `f_reason=audit_ring4_ctor_install`；`audit_ring4_alloc_reg_pivot` 那 32 行 `n_install_decoded=0`，不入集合）。
3. 装表点位于 entry 体外（装表点所在函数 ≠ 该 entry）—— 代理列 `n_install_outside_body >= 1`。
4. 现盘 `coverage.tsv` 里 `grade == [已证]` 且第 4 列尚不含 `④ 活表槽位见证`（已写过的不重做）。

### 1.2 命中行数（与卡面 76 比对）

| 阶段 | 判据 | 行数 |
|---|---|---:|
| S0 | 全部 F1 缺口行 | 122 |
| S1 | + `same_source == no` | 108 |
| S2 | + `ring4_at` 装表指令可解（`n_install_decoded>=1`） | 76 |
| S3 | + 装表点在 entry 体外（`n_install_outside_body>=1`） | **76** ← 分批用的权威基集 |
| S4 | + 开工时现盘 `[已证]` 且无 `④ 活表槽位见证` | **76**（开工读数时判据 4 剔除 0 行） |

**派生基集命中 76 行，与卡面转述的 76 完全一致，无差异。** 判据 1–3 全部来自稳定的 `scan_F1_audit.tsv`（不随盘变动），故分批边界固定为 76 行；76 行的 `f_reason` 全为 `audit_ring4_ctor_install`、`sem_unproved` 全为 `0`（③ 全干净）。

> **必须披露的并发并表时点事实**：本卡**开工时**（第一次 `derive_set.py`）读到 `coverage.tsv` sha256 `95DFAC9E6CEC2D464691D84DF1EF64A0AD850C86500A4CD1348275F0FBC419D1`（4,040,803 B），判据 4 对 76 行**剔除 0 行**（76 = 76，与 B1/B2/B3 完全一致）。在本卡执行期间，`coverage.tsv` 被**并表员并发改写**为 sha `BB62A995447A5D87C9A03ADCAE99E348E08B480BCE6E9A368973543BA47F01F2`（4,049,509 B，+8,706 B）：此刻重跑判据 4 会剔除 18 行，剔除集合恰为 `00421730 00428EA0 004370C0 004684E0 00491210 004A7C90 004AF720 004B6470 004C5A30 004C5AC0 004F45B0 00524D70 0054DC60 005550C0 00555110 00555150 005F44A0 005F9950`，即 **B1（派生第 1–18 行）的 entry 全部已被 B1 delta 并表、带上 `④ 活表槽位见证`**。这属预期下游进展，**不改变分批边界**：B4 仍是稳定 76 基集的第 55–72 行；经逐行复核，本批 18 行在现盘仍 `grade==[已证]` 且均不含 `④ 活表槽位见证`（`B4 rows clean on current disk: 18/18`）。本卡 `delta.tsv` 第 1/2/3/5/6/7/8 列取**现盘（BB62A99…）**整行原值，第 4 列以现盘原文为严格前缀（见 §5、§7）。

### 1.3 批次切片与交集（硬要求）

76 行按 entry 数值升序排序：第 1–18 行 = B1，第 19–36 行 = B2，第 37–54 行 = B3，**第 55–72 行 = 本批 B4**，第 73–76 行留给后续批次。

- 本执行器自己去 `R16_F1_B1\fields.tsv`（18 行）、`R16_F1_B2\fields.tsv`（18 行）、`R16_F1_B3\fields.tsv`（18 行）取已用 entry 集合做交集检查：
  - `B1(派生第1-18行) == B1/fields.tsv`：True（18/18 逐值相同）
  - `B2(派生第19-36行) == B2/fields.tsv`：True（18/18 逐值相同）
  - `B3(派生第37-54行) == B3/fields.tsv`：True（18/18 逐值相同）
  - **B4 ∩ B1(fields) = ∅；B4 ∩ B2(fields) = ∅；B4 ∩ B3(fields) = ∅**（硬要求全部通过）。
- B4 18 行 entry：`006E6470 0071CDA0 0071E1D0 0071F8C0 0071F930 0071FA80 007220A0 007220D0 00726860 007268D0 00726950 00727BF0 00727C80 007281A0 00749F30 0074BA30 0075E0C0 0075E2C0`。
- B1∪B2∪B3∪B4 = 72 行 ⊆ 稳定派生基集 76 行。

---

## 2. 成功 / SKIP

- **成功：18 行**（全部进入 `delta.tsv` / `fields.tsv`）。
- **SKIP：0 行**；无「vt 未取得」型 SKIP —— **vtaddr 取得 18/18 行**。
- COL / offset / RTTI / 装表点 / 宿主函数也全部取到：18/18 的装表点宿主函数由 atlas `which_body` 命中（无 atlas 缺失、无需 capstone 函数定界兜底）。
- 本批 18 行的分组与区分依据（反抄袭 §4.2）：`TEventClass` 3 行（ctor + slot6 + slot8）同表同 vt `007F5578`、同站点同宿主，靠「ctor 名 / 槽号」区分；`TiberiumClass` 2 行同表、靠槽号 7/6；`TriggerClass` 3 行同表、靠槽号 5/6/8；`TriggerTypeClass` 2 行同表、靠槽号 5/6；`WarheadTypeClass` 2 行同表同写点、靠槽号 5/6；其余 6 行各用独立 vt/COL/site/RTTI。逐行写在 `fields.tsv` 的 `note` 列。

### 2.1 §4.1 类一致改选披露（若有）

**无改选（0 行）。** 本批 18 行每行 `scan_dd(.rdata/.data)` 各命中恰好 **1 张**合法活表（`vtable_start` → COL → TD → `TD+8` 全通过），其 `probe.col_name_match(行名类, mangled)` 全部 `match`（18/18），且该表的 install sites 命中 `ring4_at` 指定的装表点（capstone `imm32==vt`）。因此不存在「`site_of` 表属类与行名类不一致」的坑，直接采用唯一候选表，未触发 §4.1 改选。
（同 vt 的多行共享装表点属正常，且按卡面 §4.1「同一张表可以有多处装表点」处理：如 `TeventClass` 表 5 处、`TriggerClass` 表 4 处、WarheadTypeClass 表 5 处；本批一律按 ring4_at 指定点取，见 `fields.tsv` note。含「本行析构/就地构造写点已排除」的行——`0071FA80`/`00726860`/`00726950`/`00727BF0`/`0074BA30`/`00763200` 类——`diag.py` 显式只在 entry **体外**的 ring site 中选装表点，不与审计已排除的体内写点混同。）

### 2.2 逐行字段（完整见 `fields.tsv`）

| # | entry | class | slot | vt | COL/off | RTTI(mangled) | site | func | status |
|---:|---|---|---:|---|---|---|---|---|---|
| 55 | 006E6470 | TagTypeClass | 6 | 007F45C4 | 0080BCF0/0 | 00842CB0→.?AVTagTypeClass@@ | 006E5B8E | 006E5B60 | OK |
| 56 | 0071CDA0 | TerrainClass | 5 | 007F522C | 0080C3E0/0 | 00842D48→.?AVTerrainClass@@ | 0071BBFF | 0071BB90 | OK |
| 57 | 0071E1D0 | TerrainTypeClass | 5 | 007F5458 | 0080C498/0 | 008445E8→.?AVTerrainTypeClass@@ | 0071DAF7 | 0071DA80 | OK |
| 58 | 0071F8C0 | TEventClass | 5 | 007F5578 | 0080C5E0/0 | 008446F8→.?AVTEventClass@@ | 0071E6C1 | 0071E6A0 | OK |
| 59 | 0071F930 | TEventClass | 6 | 007F5578 | 0080C5E0/0 | 008446F8→.?AVTEventClass@@ | 0071E6C1 | 0071E6A0 | OK |
| 60 | 0071FA80 | TEventClass | 8 | 007F5578 | 0080C5E0/0 | 008446F8→.?AVTEventClass@@ | 0071E6C1 | 0071E6A0 | OK |
| 61 | 007220A0 | TiberiumClass | 7 | 007F5728 | 0080C7D8/0 | 008448C8→.?AVTiberiumClass@@ | 007217A6 | 007216C0 | OK |
| 62 | 007220D0 | TiberiumClass | 6 | 007F5728 | 0080C7D8/0 | 008448C8→.?AVTiberiumClass@@ | 007217A6 | 007216C0 | OK |
| 63 | 00726860 | TriggerClass | 5 | 007F5858 | 0080C968/0 | 00842CE8→.?AVTriggerClass@@ | 00725FCE | 00725FA0 | OK |
| 64 | 007268D0 | TriggerClass | 6 | 007F5858 | 0080C968/0 | 00842CE8→.?AVTriggerClass@@ | 00725FCE | 00725FA0 | OK |
| 65 | 00726950 | TriggerClass | 8 | 007F5858 | 0080C968/0 | 00842CE8→.?AVTriggerClass@@ | 00725FCE | 00725FA0 | OK |
| 66 | 00727BF0 | TriggerTypeClass | 5 | 007F5904 | 0080CA20/0 | 00842D08→.?AVTriggerTypeClass@@ | 00726CD2 | 00726C80 | OK |
| 67 | 00727C80 | TriggerTypeClass | 6 | 007F5904 | 0080CA20/0 | 00842D08→.?AVTriggerTypeClass@@ | 00726CD2 | 00726C80 | OK |
| 68 | 007281A0 | TubeClass | 5 | 007F59B0 | 0080CAD0/0 | 00844A70→.?AVTubeClass@@ | 00727FFD | 00727FD0 | OK |
| 69 | 00749F30 | VoxelAnimClass | 23 | 007F6318 | 0080CDF8/0 | 00845E50→.?AVVoxelAnimClass@@ | 00749434 | 007493B0 | OK |
| 70 | 0074BA30 | VoxelAnimTypeClass | 8 | 007F6548 | 0080CEB0/0 | 00845E70→.?AVVoxelAnimTypeClass@@ | 0074AE6B | 0074AD80 | OK |
| 71 | 0075E0C0 | WarheadTypeClass | 5 | 007F6B30 | 0080D360/0 | 00847C18→.?AVWarheadTypeClass@@ | 0075D0BA | 0075CEC0 | OK |
| 72 | 0075E2C0 | WarheadTypeClass | 6 | 007F6B30 | 0080D360/0 | 00847C18→.?AVWarheadTypeClass@@ | 0075D0BA | 0075CEC0 | OK |

---

## 3. 18 行 ④ 正文两两不同性自检（§4.2）

`gen_delta.py` 收集 18 条实际追加的 ④ 正文，`verify_delta.py` 独立再核一次（结果见 `verify_summary.json`）：

1. 完整正文取 `set()`：**18/18 不同**。
2. 把每条正文里全部 8 位十六进制替换为占位符 `ENTRY` 后再取 `set()`：**18/18 不同** —— 不存在「除 entry 外完全相同」的两行。
3. 字段多样性：`vt` **11** 个不同值、`slot` **5** 个、`class` **11** 个、`site` **11** 个 —— 四个字段均非单一值。
4. 同族同 vt 的区分依据：`TEventClass` 3 行靠 ctor 名 + 槽号 5/6/8；同表多行靠各自槽号；其余靠独立 vt/class/site。逐行写在 `fields.tsv` 的 `note` 列（§2.2）。

**结论：行行不同，无抄袭/复制。**

样例（第 55 行追加正文，披露指针为 §12.6）：

```
④ 活表槽位见证：TagTypeClass::slot6（vt=007F45C4，槽 6 值=006E6470，COL=0080BCF0 offset=0，RTTI=00842CB0→.?AVTagTypeClass@@；装表点 006E5B8E 位于 006E5B60 体内，entry 体外） ④升级句：TagTypeClass::slot6（④ 表属类与行名类一致，均为 TagTypeClass；该槽即其 vt=007F45C4 表 slot6，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
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
- `delta.tsv` 独立复核（`verify_delta.py`）：18 行全部 8 列；entry 集 == 派生稳定基集第 55–72 行；第 1/2/3/5/6/7/8 列与 `coverage.tsv` 现盘对应行逐字节相同（18/18）；第 4 列严格以原第 4 列字节为前缀（18/18）；grade 列逐字节 == `[已证]`（18/18）；18 行追加正文均含 `§12.6` 且不含 `§12.4`（18/18）—— **PASS**。
- `fields.tsv` 14 列表头与卡面 §5.2 逐项一致（含 `same_source` 列，值全为 `no`），status 全 `OK`（18/18）。

---

## 5. `coverage.tsv` 与 `gamemd.exe` sha256（证明未改）

| 时点 | `coverage.tsv` SHA-256 | 字节数 |
|---|---|---|
| 开工独立派生读数时（`derive_set.py` 第一次） | `95DFAC9E6CEC2D464691D84DF1EF64A0AD850C86500A4CD1348275F0FBC419D1` | 4,040,803 |
| 生成 delta 前（`gen_delta.py` cov_before） | `BB62A995447A5D87C9A03ADCAE99E348E08B480BCE6E9A368973543BA47F01F2` | 4,049,509 |
| 生成 delta 后（`gen_delta.py` cov_after） | `BB62A995447A5D87C9A03ADCAE99E348E08B480BCE6E9A368973543BA47F01F2` | 4,049,509 |
| 独立复核时（`verify_delta.py` / 末尾复测） | `BB62A995447A5D87C9A03ADCAE99E348E08B480BCE6E9A368973543BA47F01F2` | 4,049,509 |

**本卡全程对 `coverage.tsv` 只读**：开工读数与 delta 生成之间发生一次**外部并发并表**（B1 delta 写入，sha `95DFAC9E…` → `BB62A99…`，见 §1.2），非本卡所为。自 delta 生成起 cov_before == cov_after 且末尾复测一致，本卡未写该文件。B4 这 18 行在并表前后的第 4 列逐字节相同（无 witness、原有 ④ 计数不变，见 §5.1），故 delta 基于现盘原值成立。

### 5.1 改前第 4 列已含 ④ 的逐行披露（并表净增用）

派发要求：审计已实测本类别相当比例行**改前第 4 列已有其它 ④ 表述**，须在 `fields.tsv` 的 `note` 列逐行记下改前是否已含 ④，供并表算净增。本批实测：

- **改前已含 ④ 的行 = 2 行**：
  - `00749F30`（VoxelAnimClass::slot23）：改前 ④ 计数 = 2（含 `③b④` 环标签 1 处 + `④ 00749434（构造器 007493B0，首条 007493BE call 0x5F3900 基类构造后装表，atexit=False、行外）` 1 处）。
  - `0074BA30`（VoxelAnimTypeClass::slot8）：改前 ④ 计数 = 1（`④ 0074AE6B（构造器 0074AD80，首条 0074AD89 call 0x5F7090 基类构造后装表，行内 0074BA36 已排除）`）。
- **改前不含 ④ 的行 = 16 行**：其余全部（④ 计数 = 0）。
- 逐行标记格式：`fields.tsv` 第 14 列 `note` 末尾均含 `【改前第4列已含④=是/否（④ 计数=N[；改前片段: …]）】`（18/18 行都有此标记，`verify_delta.py` 已核）。
- 原第 4 列均**不含** `④ 活表槽位见证`（18/18），本卡追加的是该成文形态，不与既有 ④ 表述重复。

| 文件 | SHA-256 | 字节数 |
|---|---|---|
| `gamemd.exe`（全程只读） | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` | 4,825,360 |

`gamemd.exe` 仅以 `pefile.PE(path, fast_load=True)` + `f.read()` 只读打开，sha256 全程等于卡面给定值（`73201CC0…CF67476`）。

---

## 6. 脚本与命令

产物目录内脚本（全部只读 `gamemd.exe` / `coverage.tsv`，只写本目录）：
- `derive_set.py` —— 从 `scan_F1_audit.tsv` 按卡面 §3 四判据独立派生集合，报阶段计数 / 命中数 / 与 76 比对 / B1·B2·B3·B4 切片与交集（含去三个 fields.tsv 取 entry 做无交集硬检查）；并留痕并发并表导致的判据 4 现盘计数变化。
- `scan_fields.py` —— 复用 `PROBE_802\probe.py` 的 `Image/TextScan/vtable_start/col_of/scan_dd/body_ranges/which_body`，对 18 行只读取数：`ring4_at` token 抽取 + `dd entry` → 表候选 + install sites，写 `scan_raw.json`。
- `diag.py` —— 选候选表（cls 一致 + ring site 命中 + slot 匹配）+ 选体外装表点（排除析构/就地构造写点）+ 求宿主函数（atlas）+ 6 项字节复核，写 `diag.json`。
- `gen_delta.py` —— 读 `scan_raw.json`/`diag.json`，回二进制独立复核 6 项 + RTTI 类一致 + 体外，生成 `fields.tsv`/`delta.tsv`/`verify_summary.json`（披露指针 §12.6；note 含改前④标记）。
- `verify_delta.py` —— 独立复核 delta 列字节一致 / col4 严格前缀 / 无 witness / §12.6 有且 §12.4 无 / fields 14 列结构 / 改前④标记 / entry 集与排序 / 与 B1·B2·B3 无交集 / 行行不同。

命令（均在 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_F1_B4` 下执行）：

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
未写 `COVERAGE\coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账 / 看板 / `_drafts\` / `_cards\` / 任何其它卡目录（`R16_PROBE_4GAP\`、`R16_F1_B1\`、`R16_F1_B2\`、`R16_F1_B3\`、`R16_SLOTN_*\`、`PROBE_802\` 全部只读未改）。产物全部在 `lead\next_re_20261117_r14\R16_F1_B4\` 下：`delta.tsv`、`fields.tsv`、`REPORT.md`（另附只读扫描/生成/复核脚本与中间 JSON）。每行 ④ 自带披露指针 `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`，不写成「已过 §12.3」；节号为重号后的 **§12.6**（不是 §12.4）。
