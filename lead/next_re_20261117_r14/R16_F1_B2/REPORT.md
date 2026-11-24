# R16-F1-B2 · F1 缺口 ④ 成文 · 执行报告（派生集合第 19–36 行）

> 角色：执行器 · 日期 2026-11-20（R16 第 7 轮）· 本批 18 行（派生集合按 entry 升序第 19–36 行）
> 写域：`lead\next_re_20261117_r14\R16_F1_B2\`（仅此目录）
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

**派生集合命中 76 行，与卡面转述的 76 完全一致，无差异。** 判据 4 在两次读数（sha `0046BAD9…` 与并发改写后的 `95DFAC9…`）下都剔除 0 行；76 行的 `f_reason` 全为 `audit_ring4_ctor_install`、`sem_unproved` 全为 `0`（③ 全干净）。

### 1.3 批次切片与交集

76 行按 entry 数值升序排序：第 **1–18** 行 = B1，第 **19–36** 行 = **本批 B2**，第 37–76 行留给后续批次。
- B1∩B2 = **∅**；两批并集 ⊆ 派生集合（实测 36/76）。
- B2 18 行 entry：`005FEAF0 00629FD0 0062D7A0 0062D9A0 0062FE90 00630090 00644960 006457A0 00645950 006B5850 006C2B10 006C2C90 006C2E10 006C2F90 006C3110 006C3290 006C3410 006C3590`。
- 并发改写后重新派生（§5）：集合仍 76 行、B2 仍为上述 18 行、B1∩B2 仍 ∅。

---

## 2. 成功 / SKIP

- **成功：18 行**（全部进入 `delta.tsv` / `fields.tsv`）。
- **SKIP：0 行**；无「vt 未取得」型 SKIP —— **vtaddr 取得 18/18 行**。
- COL / offset / RTTI / 装表点 / 宿主函数也全部取到：18/18 的装表点宿主函数由 atlas `which_body` 命中（无 atlas 缺失、无需 capstone 函数定界兜底）。
- 行 21/22（同 vt `007EF954`）、行 23/24（同 vt `007EFB9C`）、行 26/27（同 vt `007F0188`）各共享装表点与宿主函数，但槽号不同（5/8、10/6、6/8）；行 29–36（8 个 TClassFactory 工厂类）各用自己独立的 vt / site / RTTI。均在 `fields.tsv` 的 `note` 中逐行写明区分依据（§4.2 反抄袭）。

### 2.1 §4.1 类一致改选披露（若有）

**无改选（0 行）。** 本批 18 行每行 `scan_dd(.rdata)` 各命中恰好 **1 张**合法活表（`vtable_start` → COL → TD → `TD+8` 全通过），其 `probe.col_name_match(行名类, mangled)` 全部 `match`（18/18），且该表的 install sites 命中 `ring4_at` 指定的装表点。因此不存在「`site_of` 表属类与行名类不一致」的坑，直接采用唯一候选表，未触发 §4.1 改选。
（注意：同 vt 的多行共享装表点属正常，本批 3 组，见 §2；`REPORT` 已按「类一致优先」逐行核对，无一处需弃用改写。）

### 2.2 逐行字段（完整见 `fields.tsv`）

| # | entry | class | slot | vt | COL/off | RTTI(mangled) | site | func | status |
|---:|---|---|---:|---|---|---|---|---|---|
| 19 | 005FEAF0 | OverlayTypeClass | 5 | 007EF600 | 008076F0/0 | 008334B0→.?AVOverlayTypeClass@@ | 005FE2F1 | 005FE250 | OK |
| 20 | 00629FD0 | ParasiteClass | 23 | 007EF890 | 00807B30/0 | 00836640→.?AVParasiteClass@@ | 00629231 | 00629210 | OK |
| 21 | 0062D7A0 | ParticleClass | 5 | 007EF954 | 00807BE8/0 | 008366E8→.?AVParticleClass@@ | 0062B767 | 0062B5E0 | OK |
| 22 | 0062D9A0 | ParticleClass | 8 | 007EF954 | 00807BE8/0 | 008366E8→.?AVParticleClass@@ | 0062B767 | 0062B5E0 | OK |
| 23 | 0062FE90 | ParticleSystemClass | 10 | 007EFB9C | 00807CA0/0 | 00836748→.?AVParticleSystemClass@@ | 0062DD16 | 0062DC50 | OK |
| 24 | 00630090 | ParticleSystemClass | 6 | 007EFB9C | 00807CA0/0 | 00836748→.?AVParticleSystemClass@@ | 0062DD16 | 0062DC50 | OK |
| 25 | 00644960 | ParticleSystemTypeClass | 8 | 007F00A8 | 00808238/0 | 00836F18→.?AVParticleSystemTypeClass@@ | 0064419C | 006440A0 | OK |
| 26 | 006457A0 | ParticleTypeClass | 6 | 007F0188 | 008082F0/0 | 008370D0→.?AVParticleTypeClass@@ | 00644CF4 | 00644BE0 | OK |
| 27 | 00645950 | ParticleTypeClass | 8 | 007F0188 | 008082F0/0 | 008370D0→.?AVParticleTypeClass@@ | 00644CF4 | 00644BE0 | OK |
| 28 | 006B5850 | SmudgeTypeClass | 5 | 007F3528 | 008099A0/0 | 00840008→.?AVSmudgeTypeClass@@ | 006B529B | 006B5260 | OK |
| 29 | 006C2B10 | T_TClassFactory_VAircraftTypeClass__ | 3 | 007F3B28 | 0080A8E8/0 | 00841748→.?AV?$TClassFactory@VAircraftTypeClass@@@@ | 006C2A49 | 006C2A40 | OK |
| 30 | 006C2C90 | T_TClassFactory_VInfantryTypeClass__ | 3 | 007F3B40 | 0080A938/0 | 00841780→.?AV?$TClassFactory@VInfantryTypeClass@@@@ | 006C2BC9 | 006C2BC0 | OK |
| 31 | 006C2E10 | T_TClassFactory_VBulletTypeClass__ | 3 | 007F3B58 | 0080A988/0 | 008417B8→.?AV?$TClassFactory@VBulletTypeClass@@@@ | 006C2D49 | 006C2D40 | OK |
| 32 | 006C2F90 | T_TClassFactory_VIsometricTileTypeClass__ | 3 | 007F3B70 | 0080A9D8/0 | 008417F0→.?AV?$TClassFactory@VIsometricTileTypeClass@@@@ | 006C2EC9 | 006C2EC0 | OK |
| 33 | 006C3110 | T_TClassFactory_VOverlayTypeClass__ | 3 | 007F3B88 | 0080AA28/0 | 00841828→.?AV?$TClassFactory@VOverlayTypeClass@@@@ | 006C3049 | 006C3040 | OK |
| 34 | 006C3290 | T_TClassFactory_VSmudgeTypeClass__ | 3 | 007F3BA0 | 0080AA78/0 | 00841860→.?AV?$TClassFactory@VSmudgeTypeClass@@@@ | 006C31C9 | 006C31C0 | OK |
| 35 | 006C3410 | T_TClassFactory_VUnitClass__ | 3 | 007F3BB8 | 0080AAC8/0 | 00841898→.?AV?$TClassFactory@VUnitClass@@@@ | 006C3349 | 006C3340 | OK |
| 36 | 006C3590 | T_TClassFactory_VBuildingClass__ | 3 | 007F3BD0 | 0080AB18/0 | 008418C8→.?AV?$TClassFactory@VBuildingClass@@@@ | 006C34C9 | 006C34C0 | OK |

---

## 3. 18 行 ④ 正文两两不同性自检（§4.2）

`gen_delta.py` 收集 18 条实际追加的 ④ 正文，`verify_delta.py` 独立再核一次（结果见 `verify_summary.json`）：

1. 完整正文取 `set()`：**18/18 不同**。
2. 把每条正文里全部 8 位十六进制替换为占位符 `ENTRY` 后再取 `set()`：**18/18 不同** —— 不存在「除 entry 外完全相同」的两行。
3. 四字段多样性：`vt` **15** 个不同值、`slot` **6** 个、`class` **15** 个、`site` **15** 个 —— 四个字段均非单一值。
4. 同族同 vt 的区分依据（行 21/22、23/24、26/27 靠槽号；行 29–36 靠 vt/class/site 各自独立）逐行写在 `fields.tsv` 的 `note` 列（§2.2）。

**结论：行行不同，无抄袭/复制。**

样例（第 19 行追加正文，披露指针为 §12.6）：

```
④ 活表槽位见证：OverlayTypeClass::slot5（vt=007EF600，槽 5 值=005FEAF0，COL=008076F0 offset=0，RTTI=008334B0→.?AVOverlayTypeClass@@；装表点 005FE2F1 位于 005FE250 体内，entry 体外） ④升级句：OverlayTypeClass::slot5（④ 表属类与行名类一致，均为 OverlayTypeClass；该槽即其 vt=007EF600 表 slot5，无归属歧义）（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
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
- `delta.tsv` 独立复核：18 行全部 8 列；entry 集 == 派生集合第 19–36 行；第 1/2/3/5/6/7/8 列与 `coverage.tsv` 对应行逐字节相同（18/18）；第 4 列严格以原第 4 列字节为前缀（18/18）；grade 列逐字节 == `[已证]`（18/18）；18 行追加正文均含 `§12.6` 且均不含 `§12.4`（18/18）—— **BAD=0**（`verify_delta.json` 的 `errors: []`）。
- `fields.tsv` 14 列表头与卡面 §5.2 逐项一致（含 `same_source` 列，值全为 `no`），status 全 `OK`。

---

## 5. `coverage.tsv` 与 `gamemd.exe` sha256（证明未改 + 并发改写留痕）

| 时点 | `coverage.tsv` SHA-256 | 字节数 |
|---|---|---|
| 派生集合读数时（§1） | `0046BAD980E9055AF61CC94DB9DA72C5346E087A49A00BA0009705807AA6ACF9` | 4,034,144 |
| 生成 delta 前（`gen_delta.py` cov_before） | `0046BAD980E9055AF61CC94DB9DA72C5346E087A49A00BA0009705807AA6ACF9` | 4,034,144 |
| 生成 delta 后（`gen_delta.py` cov_after） | `0046BAD980E9055AF61CC94DB9DA72C5346E087A49A00BA0009705807AA6ACF9` | 4,034,144 |
| 独立复核时（`verify_delta.py` / `recheck_coverage.py`） | `95DFAC9E6CEC2D464691D84DF1EF64A0AD850C86500A4CD1348275F0FBC419D1` | 4,040,803 |

**并发改写留痕**：本批生成 delta 期间 `coverage.tsv` 未变（前=后 = `0046BAD9…`）；写报告前复查时发现盘上 sha 已变为 `95DFAC9…`（4,040,803 B，+6,659 B）。按卡面 §5.1 要求重新校验并留痕：
- 差异经与 `R16_PROBE_4GAP\_pin_coverage.tsv`（sha `0046BAD9…`）逐行比对，定位为 **13 行**被并发改写，entry 为 `005B3060/005B3570/005B35E0/005B3650/005B36B0/005B4630/00653100/0065CBF0/006B1850/006B1900/006B8660/006B8710/006F9E50` —— 即 **`R16_MERGE_SLOTN_B3` 的 13 行**，与本 F1 派生集合 76 行**无交集**（`recheck_coverage.json` 的 `b2_unchanged: true`、`b1_b2_intersect: []`）。
- 重新派生：集合仍 76 行、判据 4 仍剔除 0 行、B2 仍为 §1.3 那 18 行。
- 用当前盘（`95DFAC9…`）重跑 `verify_delta.py` / `recheck_coverage.py`：本批 18 行的第 1/2/3/5/6/7/8 列仍与当前盘逐字节相同、第 4 列仍以原字节为前缀、grade 仍 `[已证]`（`delta_cols_vs_current_coverage: true`、`delta_grade_ok: true`、`delta_col4_prefix_ok: true`）。
- 合并员并表时应以最终盘上版本为准；若并表前盘再变，需重新校验上述字节一致性。

| 文件 | SHA-256 | 字节数 |
|---|---|---|
| `gamemd.exe`（全程只读） | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` | 4,825,360 |

`gamemd.exe` 仅以 `pefile.PE(path, fast_load=True)` + `f.read()` 只读打开，sha256 全程等于卡面给定值。

---

## 6. 脚本与命令

产物目录内脚本（全部只读 `gamemd.exe` / `coverage.tsv`，只写本目录）：
- `derive_set.py` —— 从 `scan_F1_audit.tsv` 按卡面 §3 四判据独立派生集合，报阶段计数 / 命中数 / 与 76 比对 / B1·B2 切片与交集。
- `scan_fields.py` —— 复用 `PROBE_802\probe.py` 的 `Image/TextScan/vtable_start/col_of/scan_dd/body_ranges/which_body`，对 18 行只读取数：`ring4_at` token 抽取 + `dd entry` → 表候选 + install sites，写 `scan_raw.json`。
- `diag.py` —— 选 site / 求宿主函数（atlas）+ 判体外 + 6 项字节复核，写 `diag.json`。
- `gen_delta.py` —— 读 `scan_raw.json`/`diag.json`，回二进制独立复核 6 项 + RTTI 类一致 + 体外，生成 `fields.tsv`/`delta.tsv`/`verify_summary.json`（披露指针 §12.6）。
- `verify_delta.py` —— 独立复核 delta 列字节一致 / col4 严格前缀 / grade `[已证]` / §12.6 披露 / §12.4 缺席 / fields 14 列结构，写 `verify_delta.json`。
- `recheck_coverage.py` —— 并发改写后用当前盘重新派生 + 复核 delta 字节一致，写 `recheck_coverage.json`。

命令（均在 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_F1_B2` 下执行）：

```bash
python derive_set.py
python scan_fields.py
python diag.py
python gen_delta.py
python verify_delta.py
python recheck_coverage.py
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
未写 `COVERAGE\coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账 / 看板 / `_drafts\` / `_cards\` / 任何其它卡目录（`R16_PROBE_4GAP\`、`R16_SLOTN_B1\`、`R16_SLOTN_B3\`、`PROBE_802\` 全部只读未改）。产物全部在 `lead\next_re_20261117_r14\R16_F1_B2\` 下：`delta.tsv`、`fields.tsv`、`REPORT.md`（另附只读扫描/生成/复核脚本与中间 JSON）。每行 ④ 自带披露指针 `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`，不写成「已过 §12.3」；节号为重号后的 **§12.6**（不是 §12.4）。
