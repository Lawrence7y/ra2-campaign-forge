# R16-F1-B5 · F1 缺口 ④ 成文 · 执行报告（派生集合第 73–76 行，收官批）

> 角色：执行器 · 日期 2026-11-20（R16 第 7 轮）· 本批 **4 行**（派生集合按 entry 升序第 73–76 行，76 行最后一小批）
> 写域：`lead\next_re_20261117_r14\R16_F1_B5\`（仅此目录）
> 依据裁决：D-47(A)（维持 D-43(A) 优先，§12.3 对「活 vtable 槽位」形态正式让位 + 整批披露）
> 披露节号：**§12.6**（重号后；不是 §12.4）

---

## 1. 独立派生集合（卡面 §3 第一步，必做）

**权威输入**：`R16_PROBE_4GAP\scan_F1_audit.tsv`（122 数据行，未被本执行器修改）。
**背景报告**：`R16_PROBE_4GAP\REPORT.md`（F1 定义 + `ring4_at` 字段解释）。

### 1.1 判据（逐条写清，脚本 `derive_set.py`）

1. `same_source == no`（④ 与 ② 不同源，守 §12.3 精神；D-47(A) 只对「活 vtable 槽位」形态让位，本报告全批为该形态，仍按卡面要求守此列）。
2. `ring4_at` 能解析出装表指令 `mov <mem>, imm32` 且 `imm32` 指向该行活表 —— TSV 代理列 `n_install_decoded >= 1`（本批命中行全部 `f_reason=audit_ring4_ctor_install`；`audit_ring4_alloc_reg_pivot` 那 32 行 `n_install_decoded=0`，不入集合）。
3. 装表点位于 entry 体外（装表点所在函数 ≠ 该 entry）—— TSV 代理列 `n_install_outside_body >= 1`。
4. 现盘 `coverage.tsv` 里 `grade == [已证]` 且第 4 列尚不含 `④ 活表槽位见证`（已写过的不重做）。

### 1.2 命中行数（与卡面 76 比对）

| 阶段 | 判据 | 行数 |
|---|---|---:|
| S0 | 全部 F1 缺口行 | 122 |
| S1 | + `same_source == no` | 108 |
| S2 | + `ring4_at` 装表指令可解（`n_install_decoded>=1`） | 76 |
| S3 | + 装表点在 entry 体外（`n_install_outside_body>=1`） | **76** ← 分批用的权威基集 |
| S4 | + 开工时现盘 `[已证]` 且无 `④ 活表槽位见证` | 58（开工读数时判据 4 已剔除 B1 的 18 行已并表行） |

**派生基集命中 76 行，与卡面转述的 76 完全一致，无差异。** 判据 1–3 全部来自稳定的 `scan_F1_audit.tsv`（不随盘变动），故分批边界固定为 76 行。76 行 `f_reason` 全为 `audit_ring4_ctor_install`、`sem_unproved` 全为 `0`（③ 全干净）。

> **必须披露的并发并表时点事实（本卡观测到两次盘变化，均非本卡所为）**：
> - 本卡**开工独立派生时**（`derive_set.py`）读到 `coverage.tsv` sha256 `BB62A995447A5D87C9A03ADCAE99E348E08B480BCE6E9A368973543BA47F01F2`（4,049,509 B）：判据 4 对 76 行剔除 18 行，剔除集合恰为 B1（派生第 1–18 行）entry —— 即 B1 delta 已被并表。
> - 本卡**生成 delta 时**（`gen_delta.py`）读到 sha256 `6428B4EB06280BD56C250CC1156E0B24A72E6BC4A11B5E9FD17E500718642D5F`（4,058,895 B，+9,386 B）：并表员又并入了后续批次。`gen_delta.py` 的 `cov_before == cov_after` 均为此值，且对 4 个 B5 entry 逐行 `assert WITNESS not in orig_sem` 全部通过 ⇒ **本批 4 行在生成 delta 的现盘快照上仍 `grade==[已证]` 且无 `④ 活表槽位见证`**。
>
> 两次并表都**不改变分批边界**：B5 仍是稳定 76 基集的第 73–76 行；`delta.tsv` 第 1/2/3/5/6/7/8 列取生成时现盘（`6428B4EB…`）整行原值，第 4 列以该原文为严格前缀（见 §4、§5）。本卡对 `coverage.tsv` 全程只读。

### 1.3 批次切片与交集（硬要求）

76 行按 entry 数值升序：第 1–18 = B1，19–36 = B2，37–54 = B3，55–72 = B4，**73–76 = 本批 B5（收官）**。

本执行器自己去四批 `fields.tsv` 取已用 entry 集合做交集检查（`derive_set.py` + `verify_delta.py` 双重）：

- `B1(1-18) == B1/fields.tsv`：True（18/18 逐值相同）
- `B2(19-36) == B2/fields.tsv`：True（18/18）
- `B3(37-54) == B3/fields.tsv`：True（18/18）
- `B4(55-72) == B4/fields.tsv`：True（18/18）
- **B5 ∩ B1(fields) = ∅；B5 ∩ B2(fields) = ∅；B5 ∩ B3(fields) = ∅；B5 ∩ B4(fields) = ∅**（四条硬要求全部通过）
- **B1∪B2∪B3∪B4∪B5 = 76 行 == 派生基集全集**（收官批补齐 76 行，无遗漏、无重叠）

本批 4 行 entry：`00763200`（WaveClass::slot8）、`00763D90`（WaypointPathClass::slot6）、`00772CD0`（WeaponTypeClass::slot5）、`00772EB0`（WeaponTypeClass::slot6）。

---

## 2. 成功 / SKIP

- **成功：4 行**（全部进入 `delta.tsv` / `fields.tsv`）。
- **SKIP：0 行**；无「vt 未取得」型 SKIP —— **vtaddr 取得 4/4 行**。
- COL / offset / RTTI / 装表点 / 宿主函数全部取到：4/4 宿主函数由 atlas `which_body` 命中（无 atlas 缺失、无需 capstone 函数定界兜底）。
- 4 行分组与区分依据（反抄袭 §4.2）：`WeaponTypeClass` 2 行（slot5 + slot6）同表同 vt `007F73B8`、同写点 `00771E77`、同宿主 `00771C70`，靠「槽号 5/6」区分；`WaveClass`、`WaypointPathClass` 各 1 行用独立 vt/COL/site/RTTI。逐行写在 `fields.tsv` 的 `note` 列。

### 2.1 §4.1 类一致改选披露

**无改选（0 行）。** 本批 4 行每行 `scan_dd(.rdata/.data)` 各命中恰好 **1 张**合法活表（`vtable_start` → COL → TD → `TD+8` 全通过），其 `probe.col_name_match(行名类, mangled)` 全部 `match`（4/4），且该表 install sites 命中 `ring4_at` 指定装表点（capstone `imm32==vt`）。因此不存在「`site_of` 表属类与行名类不一致」的坑，直接采用唯一候选表，未触发 §4.1 改选。

- 同 vt 的多行共享装表点属正常，按卡面 §4.1「同一张表可以有多处装表点」处理：`WeaponTypeClass` 表 4 处装表点（00771E77/00771F28/00771F57/007730F7），slot5/slot6 两行一律按 `ring4_at` 指定点取 00771E77（`fields.tsv` note 逐行记录）。
- `00763200` 的 `ring4_at` 含两个装表点：`0075EA3F`（构造器 `0075E950` 内、entry 体外，采用）与 `00763206`（本行析构器体内自装表，审计原文按 ㉓ 明确排除）。`diag.py` 显式取落在 entry 体外的站点 `0075EA3F`，不与审计已排除的体内写点混同。

### 2.2 逐行字段（完整见 `fields.tsv`）

| # | entry | class | slot | vt | COL/off | RTTI(mangled) | site | func | status |
|---:|---|---|---:|---|---|---|---|---|---|
| 73 | 00763200 | WaveClass | 8 | 007F6BF4 | 0080D418/0 | 00847EB0→.?AVWaveClass@@ | 0075EA3F | 0075E950 | OK |
| 74 | 00763D90 | WaypointPathClass | 6 | 007F6E70 | 0080D5C8/0 | 00847FB0→.?AVWaypointPathClass@@ | 0076375F | 00763730 | OK |
| 75 | 00772CD0 | WeaponTypeClass | 5 | 007F73B8 | 0080E460/0 | 00849248→.?AVWeaponTypeClass@@ | 00771E77 | 00771C70 | OK |
| 76 | 00772EB0 | WeaponTypeClass | 6 | 007F73B8 | 0080E460/0 | 00849248→.?AVWeaponTypeClass@@ | 00771E77 | 00771C70 | OK |

---

## 3. 4 行 ④ 正文两两不同性自检（§4.2）

`gen_delta.py` 收集 4 条实际追加的 ④ 正文，`verify_delta.py` 独立再核一次（结果见 `verify_summary.json`）：

1. 完整正文取 `set()`：**4/4 不同**。
2. 把每条正文里全部 8 位十六进制替换为占位符 `ENTRY` 后再取 `set()`：**4/4 不同** —— 不存在「除 entry 外完全相同」的两行。
3. 字段多样性：`vt` **3** 个不同值、`slot` **3** 个、`class` **3** 个、`site` **3** 个 —— 四个字段均非单一值。
4. 同族同 vt 的区分依据：`WeaponTypeClass` slot5/slot6 两行虽 vt/COL/site/func/RTTI 全同，但 `ident`（`WeaponTypeClass::slot5` vs `::slot6`）、槽号（5 vs 6）、槽值（本 entry）均不同 ⇒ 归一 entry 后正文仍以「slot5/槽 5/slot5」vs「slot6/槽 6/slot6」区分，逐行写在 `fields.tsv` note。

**结论：行行不同，无抄袭/复制。**

样例（第 73 行追加正文，披露指针为 §12.6）：

```
④ 活表槽位见证：WaveClass::slot8（vt=007F6BF4，槽 8 值=00763200，COL=0080D418 offset=0，RTTI=00847EB0→.?AVWaveClass@@；装表点 0075EA3F 位于 0075E950 体内，entry 体外） ④升级句：WaveClass::slot8（④ 表属类与行名类一致，均为 WaveClass；该槽即其 vt=007F6BF4 表 slot8，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

---

## 4. 六项字节级复核（卡面 §5.3）

`gen_delta.py` 逐行回 `gamemd.exe` 只读复算（`verify_summary.json`），并由 `verify_delta.py` 独立复核 delta 结构，全部 4/4 True：

| # | 校验 | 结果 |
|---|---|---|
| 1 | `u32(vt + slot*4) == entry` | 4/4 True |
| 2 | `u32(vt - 4) == COL` | 4/4 True |
| 3 | `u32(COL + 4) == offset` | 4/4 True |
| 4 | `u32(COL + 12) == TD` | 4/4 True |
| 5 | `cstr(TD + 8) == mangled`（内联串，非指针） | 4/4 True |
| 6 | capstone 解码 `imm32@site == vt`（`mov [mem], imm32`） | 4/4 True |

附加自检（防「写得漂亮但不对」）：

- `rtti_class==row_class`（`probe.col_name_match`）4/4 True。
- 装表点在 entry 体外 4/4 True（含 `00763200` 排除体内 00763206 后取 0075EA3F）。
- `delta.tsv` 独立复核（`verify_delta.py`）：4 行全部 8 列；entry 集 == 派生稳定基集第 73–76 行；第 1/2/3/5/6/7/8 列与 `coverage.tsv` 生成时现盘对应行逐字节相同（4/4）；第 4 列严格以原第 4 列字节为前缀（4/4）；grade 列逐字节 == `[已证]`（4/4）；4 行追加正文均含 `§12.6` 且不含 `§12.4`（4/4）—— **PASS**。
- `fields.tsv` 14 列表头与卡面 §5.2 逐项一致（含 `same_source` 列，值全为 `no`），status 全 `OK`（4/4）。

---

## 5. `coverage.tsv` 与 `gamemd.exe` sha256（证明未改）

| 时点 | `coverage.tsv` SHA-256 | 字节数 |
|---|---|---|
| 开工独立派生读数时（`derive_set.py`） | `BB62A995447A5D87C9A03ADCAE99E348E08B480BCE6E9A368973543BA47F01F2` | 4,049,509 |
| 生成 delta 前（`gen_delta.py` cov_before） | `6428B4EB06280BD56C250CC1156E0B24A72E6BC4A11B5E9FD17E500718642D5F` | 4,058,895 |
| 生成 delta 后（`gen_delta.py` cov_after） | `6428B4EB06280BD56C250CC1156E0B24A72E6BC4A11B5E9FD17E500718642D5F` | 4,058,895 |
| 独立复核时（`verify_delta.py`） | `6428B4EB06280BD56C250CC1156E0B24A72E6BC4A11B5E9FD17E500718642D5F` | 4,058,895 |

**本卡全程对 `coverage.tsv` 只读**：开工读数与 delta 生成之间发生一次外部并发并表（BB62A99… → 6428B4EB…，+9,386 B，见 §1.2），非本卡所为。自 delta 生成起 `cov_before == cov_after` 且独立复核时一致，本卡未写该文件。本批 4 行在并表前后的第 4 列逐字节相同（无 witness），故 delta 基于生成时现盘原值成立。

### 5.1 改前第 4 列已含 ④ 的逐行披露（并表净增用）

派发要求：在 `fields.tsv` 的 `note` 列逐行记下改前是否已含 ④，供并表算净增。本批实测（在生成 delta 的现盘快照 `6428B4EB…` 上读取）：

- **改前已含 ④ 的行 = 1 行**：
  - `00763200`（WaveClass::slot8）：改前 ④ 计数 = 1，为散文式 `④ 0075EA3F（构造器 0075E950，首条 0075E956 call 0x5F3900 基类构造后装表，atexit=False、行外；本行体内 00763206 自装表在析构器内，按 ㉓ 已排除）`。本卡追加的是 `④ 活表槽位见证` 成文形态（原第 4 列**不含**该 witness 子串），不改变既有 ④ 表述，净增按「+1 成文形态」计。
- **改前不含 ④ 的行 = 3 行**：`00763D90`、`00772CD0`、`00772EB0`（④ 计数 = 0）。
- 逐行标记格式：`fields.tsv` 第 14 列 `note` 末尾均含 `【改前第4列已含④=是/否（④ 计数=N[；改前片段: …]）】`（4/4 行都有此标记，`verify_delta.py` 已核）。
- 原第 4 列均**不含** `④ 活表槽位见证`（4/4），本卡追加的是该成文形态，不与既有 ④ 表述重复。

| 文件 | SHA-256 | 字节数 |
|---|---|---|
| `gamemd.exe`（全程只读） | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` | 4,825,360 |

`gamemd.exe` 仅以 `pefile.PE(path, fast_load=True)` + 只读字节缓冲打开，sha256 全程等于卡面给定值（`73201CC0…CF67476`）。

---

## 6. 脚本与命令

产物目录内脚本（全部只读 `gamemd.exe` / `coverage.tsv`，只写本目录）：

- `derive_set.py` —— 从 `scan_F1_audit.tsv` 按卡面 §3 四判据独立派生集合，报阶段计数 / 命中数 / 与 76 比对 / B1·B2·B3·B4·B5 切片与交集（含去四个 fields.tsv 取 entry 做无交集硬检查 + 并集覆盖 76 行检查）；留痕并发并表导致的判据 4 现盘计数变化。写 `derived_set.tsv`。
- `scan_fields.py` —— 复用 `PROBE_802\probe.py` 的 `Image/TextScan/vtable_start/col_of/scan_dd/body_ranges/which_body`，对 4 行只读取数：`ring4_at` token 抽取 + `dd entry` → 表候选 + install sites，写 `scan_raw.json`。
- `diag.py` —— 选候选表（cls 一致 + ring site 命中 + slot 匹配）+ 选体外装表点（排除 `00763200` 析构体内写点）+ 求宿主函数（atlas）+ 6 项字节复核，写 `diag.json`。
- `gen_delta.py` —— 读 `scan_raw.json`/`diag.json`，回二进制独立复核 6 项 + RTTI 类一致 + 体外，生成 `fields.tsv`/`delta.tsv`/`verify_summary.json`（披露指针 §12.6；note 含改前④标记）。
- `verify_delta.py` —— 独立复核 delta 列字节一致 / col4 严格前缀 / 无 witness / §12.6 有且 §12.4 无 / fields 14 列结构 / 改前④标记 / entry 集与排序 / 与四批无交集 / 并集覆盖 76 / 行行不同。

命令（均在 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_F1_B5` 下执行；控制台设 `PYTHONIOENCODING=utf-8` 以正确打印 ㉓ 等字符）：

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
未写 `COVERAGE\coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账 / 看板 / `_drafts\` / `_cards\` / 任何其它卡目录（`R16_PROBE_4GAP\`、`R16_F1_B1\`、`R16_F1_B2\`、`R16_F1_B3\`、`R16_F1_B4\`、`R16_SLOTN_*\`、`PROBE_802\` 全部只读未改）。产物全部在 `lead\next_re_20261117_r14\R16_F1_B5\` 下：`delta.tsv`、`fields.tsv`、`REPORT.md`（另附只读扫描/生成/复核脚本与中间 JSON）。每行 ④ 自带披露指针 `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`，不写成「已过 §12.3」；节号为重号后的 **§12.6**（不是 §12.4）。
