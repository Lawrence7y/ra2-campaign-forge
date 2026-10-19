# 门禁词汇与档位定义表（GATE_VOCABULARY）

> 出品：W3-DOC2（卡面 `docs/re/dispatch/W3_20261002_DOC2_runbook_terms.md:19` 授权：「门禁词汇文档若不存在则在 `docs/re/` 下新建 `GATE_VOCABULARY.md`，报告里写明新建理由」）
> 本件性质：**档位定义 + 门禁词汇注记**。**零改**两份 ATLAS 正文、补丁源件、`claims*.txt`、`tools/**.py`、`ra2opt/**.py`、`coverage_ledger/**`、任何 `verify_*.py`。
> 纪律：下面每一个 `文件:行号` 都由本包**现读打开该行**并逐字复验（登记表 = `out/re_work/qc/W3_20261002/doc2_runbook_terms/citations.json`，自检件 `scripts/check_citations.py`，50/50 通过；终检 `verify_doc2.py` 每次重跑再验一遍）。

---

## 0. 为什么要新建这份文件（空扫描对照）

现读普查 `GATE-MAP` / `GATE-LAA` / `GATE-REDLINE` / `GATE-B0` / `GATE-EIP` 这些门禁 id 在 `docs/re/**` 的命中：

| 待扫面 | 命中 | 判读 |
|:--|--:|:--|
| `docs/re/**` 的 `.md`/`.txt`（**除本卡写入的两件**：本文件与 `execution_runbook.md`；写入前的原始 641 行 runbook 亦 0 命中） | **0** | 门禁 id 在治理文档侧**从未定义** |
| `out/re_work/zcode_live/W3_20261001/m35_ch13_expand/M35_ch13_atlas_patch.md`（`GATE-`） | **13** | 正面对照：仪器有效 |
| `out/re_work/zcode_live/W3_20261001/m35_ch13_expand/claims.txt`（`GATE-`） | **36** | 正面对照：同上 |

⇒ 「0 命中」是**真·缺表**而不是扫描器失灵（同批 id 在被引用件里命中 13/36；终检 `verify_doc2.py` 每次重跑这条普查，并把「正面对照为 0」判为 `INSTRUMENT_FAILED`）。这些 id 目前只在 §13 补丁与 claims 里当标签用，没有任何一处定义「谁读它、判据是什么、实测站得住吗」⇒ 本件补的就是这张定义表。
同一份普查还确认：`docs/re/audit_bytes_toolfix.md` 通篇 **`0x200` 命中 0**，而两个字节审计工具源码各 1 命中该回退常量（`tools/audit_bytes.py:51`、`tools/verify_bss_claims.py:80`）⇒ 回退语义此前无任何成文处（见 §3）。

---

## 1. 档位定义表

| 档 | 名字 | 谁读（现读 `文件:行号`） | 判据（读来干什么） | 实测状态 |
|:--|:--|:--|:--|:--|
| **`GATE-LAA`** | 特性位（LAA / DllCharacteristics） | `ra2opt/pe.py:107`（取 `0x0020`）、`ra2opt/pe.py:289`（`set_laa` 据此写或 no-op）、`ra2opt/cli.py:269`（CLI 据此跳过/执行）、`ra2opt/audit.py:263`（据此出 `exe.laa` 告警）、`tools/verify_anchors.py:244`（读 `dll_characteristics`） | **`0x00400066`（COFF Characteristics）的 `0x0020` = 要不要写 LAA / 报不报内存告警**；`0x004000AE`（DllCharacteristics）+ `0x004000B0`（StackReserve）= 三态放行留痕判定 | game.exe 侧真判据成立（`RPT1_REPORT.md:118` 的 idx 6 升档依据）。**注意**：`0xAE` 的同数值 `0x0020` 是 `HIGH_ENTROPY_VA`，与 LAA 无关（`ra2opt/pe.py:116`）——旧写法把两者混谈即错在此 |
| **`GATE-MAP`** | 段映射 / 头区上界 | `tools/verify_anchors.py:85`（取 `size_of_headers`，**只取不判**）、`tools/verify_anchors.py:82`、`tools/verify_anchors.py:83`（两个对齐字段**只赋值无分支**）、`tools/audit_bytes.py:51`、`tools/verify_bss_claims.py:80`（用 `SizeOfHeaders` 定头区上界） | **头区上界 = `SizeOfHeaders`**（两工具据此建 `PE-header` 伪节）；**段映射只用节表四元组**，不除也不比 `SectionAlignment`/`FileAlignment` | `SizeOfHeaders` 一档：判据成立但**回退语义未成文**（§3）。对齐两档：仓库自研门禁**无判据** ⇒ 见 `FIELD-REG` |
| **`GATE-REDLINE`** | 窗口外段头红线 | `out/re_work/qc/W3_20261001/scripts/b7_exclusions_probe.py:119`（读 `.rsrc` 段头 `+12..+15`）；`.detour` 侧成文条款在 `docs/re/execution_runbook.md` 的 `G0-5` 行 | **严禁写入/注入该节**；`.rsrc` 侧此前**无成文条款**（`RPT1_REPORT.md:25` 申报「G0-5 只覆盖 .detour」）⇒ 本卡补 `G0-5b` | `.rsrc` 16B 中**只有 4 字节有读者**（`RPT1_REPORT.md:129`）；成文红线补位后：红线按 16B 守、断言按 4B 立（§2） |
| **`FIELD-REG`**（新档） | **字段登记 / 库层校验字段**（有取证价值，但**不是放闸判据**） | `tools/verify_anchors.py:70`（`self.machine` 赋值后无人引用）、`tools/verify_anchors.py:82`、`tools/verify_anchors.py:83`（同） | **只登记字节事实**；不得写成「门禁读取点……直接读取该字段判定放闸条件」。第三方库 pefile 的校验分支可作**库层**证据，但那是**库层**不是仓库自研门禁 | 依据 `RPT1_REPORT.md:127` 的阈值敏感实测与 `RPT1C_SCOPING.md:13` 的「新档位无定义表」判定；治理文档侧的首个定义面（并发情况见 §9） |
| （参照）硬拒位 | PE32 身份的一票否决 | `tools/verify_anchors.py:78`（`if self.magic != 0x010B: raise`） | 只有 `OptionalHeader.Magic`（文件 `0x68`）在自研门禁里**硬拒**；`Machine` 没有任何分支以它为条件 | 与 `coverage_ledger` 的 `gate.pe_header_field_registration` 登记同向（CS3B 裁定落地件） |
| `GATE-B0` / `GATE-EIP` | 未定义（**本卡不取证**） | 本卡未现读到读者/判据 | — | 留给后续卡（`RPT2_gate_vocabulary` 全表化时补），本表刻意不编内容 |

**写法约定**（四条建议里"措辞半区"的落点）：一句「门禁读取点」必须同时能回答**谁读**（`文件:行号`）与**读了改判什么**。答不出改判链条的，一律写成 `FIELD-REG · 字段登记`，不得写 `GATE-*`。

---

## 2. `GATE-REDLINE` 的 `.rsrc` 侧（DOC2 任务② 的成文半区）

现读 `ra2youli/game.exe`（4,497,680 B / sha256[:12] `c4bf2a57a80f`，e_lfanew `0x50`，5 节）：

| 字段 | 现读 |
|:--|:--|
| `.rsrc` 节表项 | `VA=0x00B2D000`、`VirtualSize=0x15FB8`、`RawSize=0x16000`、`RawPtr=0x431000`（与正文节表行 `out/re_work/qc/W3_20261001/scope/atlas_game/ARCHITECTURE_ATLAS_GAME.md:96` 逐字相符） |
| 段头（资源目录头）16B @ 文件 `0x431000` | `00 00 00 00 00 00 00 00 00 00 00 00 00 00 07 00`（与 `out/re_work/zcode_live/W3_20261001/m35_ch13_expand/M35_ch13_atlas_patch.md:65` 登记的 16B 逐字相同；claims 侧 `out/re_work/zcode_live/W3_20261001/m35_ch13_expand/claims.txt:38`） |
| 分解 | `+0..+3 Characteristics=0x00000000`、`+4..+11 TimeDateStamp/Major/Minor=0`、**`+12..+13 NumberOfNamedEntries=0x0000`**、**`+14..+15 NumberOfIdEntries=0x0007`** ⇒ 一级目录枚举边界 7 条 |
| 唯一读者 | `out/re_work/qc/W3_20261001/scripts/b7_exclusions_probe.py:119` 的 `struct.unpack_from("<HH", data, off + 12)`（取 `+12..+15` 定 `for i in range(n_named + n_id)` 的循环界） |
| 实测 | `RPT1_REPORT.md:129` 的三档变异：`n_id 7→0` 使 `has_RT_VERSION True→False`；`7→9` 枚举出 9 条；`+0..+3` 改 `deadbeef` ⇒ **零邻判**（`RPT1_REPORT.md:147` 同段残留申报） |
| `.detour` 对照 | 原生签名 `40 00 00 00 44 74 72 00` @ 文件 `0x447000`（本包现读，与成文 `G0-5` 行逐字相符） |

⇒ **成文条款**：已作为 **`G0-5b`** 行补进 `docs/re/execution_runbook.md` 的阶段 0 门禁表（紧邻 `G0-5`），措辞为「`.rsrc` 原生资源目录头 16B ⇒ **严禁写入/注入**；有门禁读者的只有 `+12..+15` 四字节」。
⇒ **断言与红线分档**（这是 RPT1 §8.3 两条路里"补成文红线"那条，不改字节）：claims 的 16B 断言**保留**为取证对象，但**判据只站 4 字节**；若某卡把这 16B 整串当"门禁判据"写，应改挂 `FIELD-REG`，红线归 `GATE-REDLINE`（写入禁止条款），两者不要混写。
⇒ 字节侧改动（16B 缩 4B）**不在本卡**：撞已验收件（`RPT1C_SCOPING.md:14` 判档），转 `CS4_s13_readpoint_recalib`。

---

## 3. `SizeOfHeaders`：回退语义 + 「`00001000h` 只是记录值，不是判据」（DOC2 任务③）

### 3.1 回退语义（治理文档侧的首个成文处；见 §9 并发报备）

两个字节审计工具的段表构造函数里都写：

```
tools/audit_bytes.py:51         size_headers = struct.unpack_from('<I', d, pe + 24 + 60)[0] or 0x200
tools/verify_bss_claims.py:80   size_headers = struct.unpack_from("<I", d, pe + 24 + 60)[0] or 0x200
```

⇒ 语义：**头区上界取 `SizeOfHeaders`（文件 `0xA4`，`pe+24+60`）；该字段为 0 时回退 `0x200`**。回退只在这两处生效；`tools/verify_anchors.py:85` 取同一字段但**没有**回退（读到 0 就是 0）⇒ 两台仪器在 `SizeOfHeaders=0` 的副本上口径**不同**，跨包对拍时必须先声明用的哪一台。

实测分档（`RPT1_REPORT.md` 的三行读数，本包逐字现读）：

| 副本 | `SizeOfHeaders` | `audit_bytes` OK/bad | 判读 |
|:--|:--|:--|:--|
| `E12_sizehdr_40.exe` | `0x40` | **4 / 31**（`RPT1_REPORT.md:55`） | 另外 30 条 VA 由 OK→NOREAD ⇒ 工具**按该字段值分档**，头区映射长度真被它决定 |
| `E12b_sizehdr_200.exe` | `0x200` | 34 / 1（`RPT1_REPORT.md:56`） | 仅自身 `0x4000a4` MISMATCH（其余头区 VA `< 0x200` 仍可映射） |
| `E12c_sizehdr_0.exe` | `0` | 34 / 1（`RPT1_REPORT.md:57`） | **走 `or 0x200` 回退** ⇒ 回退路径有实测，不是死代码 |

⇒ 因此「`SizeOfHeaders` 是正向门禁项」的**准确写法**是：它决定 `audit_bytes` / `verify_bss_claims` 的头区映射上界（改它会挪动 OK/NOREAD 边界），**并且**有一个 `or 0x200` 的零值回退；引用它做结论时必须同时带上回退注记，否则"字段为 0"与"字段为 0x200"两种状态会被读成同一个。

### 3.2 「`00001000h` 只是记录值，不是判据」

正文现读 `out/re_work/qc/W3_20261001/scope/atlas_game/ARCHITECTURE_ATLAS_GAME.md:98`：

```
| `(PE headers)` | `0x00400000` | `00001000h` | `000000h` | `001000h` | `400000h` |
```

⇒ 该行是**节表口径的记录行**（VirtualSize `00001000h` / PointerToRawData `000000h` / SizeOfRawData `001000h` / 映射 delta `400000h`），它**没有**绑定字段 `0x004000A4`。本包现读 `game.exe` 的 `0xA4` = `0x1000`，**数值上恰好等于**该行记录的 `00001000h` ⇒ 这是巧合性一致，不是"该行就是 SizeOfHeaders 判据"。
⇒ 这正是 `RPT1_REPORT.md:23`（idx 12）判 `UNATTESTED` 的理由原句：「§0.0.4 的 PE-headers 行用 0x1000 **记录而非该字段**」。
⇒ 措辞约定：引用 `00001000h` 时**不得**写成"门禁判据"；要写成判据必须落到 `out/re_work/zcode_live/W3_20261001/m35_ch13_expand/claims.txt:15` 的 `0x004000A4 = 00100000` 这条断言 + 本节 §3.1 的读者链。补丁行 `out/re_work/zcode_live/W3_20261001/m35_ch13_expand/M35_ch13_atlas_patch.md:42` 已写「GATE-MAP (头区上界)」方向正确，但**缺回退注记与实测背书** ⇒ 那半区属正文（等 APP2 收口），不在本卡写域。

---

## 4. `GATE-LAA` 在 game.exe 侧的准确表述（DOC2 任务①）

**成文 `G0-4` 的现状**（`docs/re/execution_runbook.md` 的 G0-4 行，本包现读）：比对基准 = `ra2youli/.ra2opt/orig/gamemd.exe`，仅允许文件偏移 `0xAE`（`0x00→0x20`，LAA）与 `0xB2`（`0x10→0x40`）两处差异 ⇒ **该条是 gamemd 基线比对条款**，且把 `0xAE` 称作 LAA 与 `ra2opt/pe.py:116` 的正名冲突（`0xAE` 的同数值位是 `HIGH_ENTROPY_VA`）。

**game.exe 侧的准确表述**（已作为 `G0-4b` 行补进同一张表）：

- `0x00400066` = COFF Characteristics，本包现读 `0x030F` ⇒ **LAA 位 `0x0020` 未置**。读取点与判据链：`ra2opt/pe.py:107` 取位 → `ra2opt/pe.py:289`（`set_laa` 据此**写入或 no-op**）与 `ra2opt/cli.py:269`（CLI 据此**跳过或执行**）→ `ra2opt/audit.py:263`（据此出 `exe.laa` 告警文案）。
- `0x004000AE` = DllCharacteristics，现读 `0x0000`；`0x004000B0` = SizeOfStackReserve，现读 `0x100000`。判据链 = `tools/verify_anchors.py:244` 取值 → `tools/verify_anchors.py:247` 判 `RA2OPT_PERF`、`tools/verify_anchors.py:250` 判 `VANILLA_ORIGINAL`、`tools/verify_anchors.py:252` 出 `CUSTOM`。
- ⇒ **成文 `G0-4` 的 `0xAE/0xB2` 白名单不适用于 game.exe**（game.exe 侧没有等价的成文放闸条款）；引用 game.exe 的 LAA 状态时，只允许引上面这条判据链，**不要**引 gamemd 白名单。
- 升档依据的实测出处：`RPT1_REPORT.md:118`（idx 6 的读者清单与 `E06/E06b` 变异读数：动 `0x66` 才让 `set_laa(True)` 的返回值从 `true`（写入）变 `false`（no-op））。
- 补丁/claims 侧的对应措辞半区（`out/re_work/zcode_live/W3_20261001/m35_ch13_expand/M35_ch13_atlas_patch.md:36`、`:43`、`out/re_work/zcode_live/W3_20261001/m35_ch13_expand/claims.txt:9`、`:16`）**不在本卡写域**（正文与补丁件逐字节绑定，等 APP2 收口）。

---

## 5. `GATE-MAP` 的对齐两档：改挂 `FIELD-REG`（任务① 的词汇半区）

`out/re_work/zcode_live/W3_20261001/m35_ch13_expand/M35_ch13_atlas_patch.md:39`、`:40` 与 `out/re_work/zcode_live/W3_20261001/m35_ch13_expand/claims.txt:12`、`:13` 现均写「门禁读取点：**GATE-MAP (段映射自洽)** 直接读取该字段判定放闸条件」。
本包现读仓库自研门禁：`tools/verify_anchors.py:82`、`tools/verify_anchors.py:83` 只是把两字段**赋值给实例**，全文无分支读它们；段映射一律用节表四元组。⇒ **那句判据已被实测证否**（`RPT1_REPORT.md:127` 给出的是 pefile **库层**校验分支的邻判，且阈值敏感：`0x200`/`0x100` 两档零邻判，`0` 档被探针表示差冒充——见 §6）。

**词汇裁定（本件给出的唯一定义）**：
- `SectionAlignment`（`0x00400088`，现读 `0x1000`）与 `FileAlignment`（`0x0040008C`，现读 `0x1000`）应登记为 **`FIELD-REG · 库层校验字段`**，注记「判据在第三方库 pefile 的校验分支（含阈值：`SA<0x1000` 须等于 `FA`；`FA>0x200` 须为 2 的幂；`PRPD % FA == 0`），仓库自研门禁不读」。
- 若验收要求「读取点必须在仓库自研门禁代码里」⇒ 这两条应回退 `UNATTESTED`（Lead 在 CS3B 已裁 **B 案：双档单列**，两档并存，不替验收选档）。
- 正文/claims 侧的措辞改动**不在本卡**（等 APP2 收口 + 台账引用面走 CS 卡）。

---

## 6. 前件勘误登记（append 方式；原行一字不动）

`out/re_work/qc/W3_20261002/rpt1_readpoints/RPT1C_SCOPING.md:149` 登记的勘误（本包现读 RPT1C 原文）：

- 被更正句 = `RPT1_REPORT.md:127` 里的「**`0x200`/`0x100`/`0` 三档实测零邻判**」——多算一档：`E10b_filealign_0` 档在 `pefile_collateral` 里出现 5 个 `section_*` 差项，被记为**有邻判**。
- 那 5 项是**探针自身的表示差**（`FileAlignment=0` 时探针写作 `None` 并省掉 `PRPD_aligned` 键），`n_warnings` 仍为 0 ⇒ pefile 未发告警、未改判定。
- 准确表述应为：「`0x200`/`0x100` 两档零邻判；`0` 档 pefile 告警数不变（0），其在 JSON 上的差项来自本卡探针的除零守卫表示，不构成判定」（`RPT1C_SCOPING.md:149` 原文）。
- 该修正**不改变 idx 10 的判决**（升档依据是 `E10c_filealign_600` 的 4 条告警 + 3 节 `PRPD_aligned true→false`），也**不改变 verdict tally 计数**。
- **承载方式**：本卡**未回改** `RPT1_REPORT.md`（它属 RPT1 会话交付件，不在 DOC2 写域；卡面 `docs/re/dispatch/W3_20261002_DOC2_runbook_terms.md:15` 给出「若判其只读则在 DOC2 报告里单列并说明」的替代项 ⇒ 采此项）。逐条内容与复算见 `out/re_work/qc/W3_20261002/doc2_runbook_terms/DOC2_REPORT.md` §④；RPT1C 亦允许该勘误在 CS4/RPT2 交付时 append 追加，**不得回改原行**（避免行号与引用面漂移）。

---

## 7. 未做（如实）与归属

| 项 | 为何不做 | 归属 |
|:--|:--|:--|
| 改 `docs/re/audit_bytes_toolfix.md` 补回退口径段 | 该文件不在 DOC2 写域（卡面写域 = runbook + 门禁词汇文档 + doc2 目录）⇒ 回退口径已在**本件 §3** 成文，toolfix 文档侧留作后续 | 建议 `DOC2b`/`RPT2` 或直接由 Lead 裁是否扩写域 |
| 改 `M35_ch13_atlas_patch.md` / `claims.txt` / ATLAS 正文措辞 | 补丁件被 `verify_m35p` 按 size `17571` 钉死；正文与补丁逐字节绑定且 APP2 是唯一写者（`RPT1C_SCOPING.md:15`、`:16`、`:14`） | `APP3_atlas_s13_semantics`（APP2 之后 append-only 加注） |
| `SizeOfHeaders` 升为正向门禁项的**工具代码**改动 / 16B 缩 4B | 改工具与改已验收件链路 ⇒ 需重跑 `audit_bytes` 存档读数并重钉三件验证器 | `CS4_s13_readpoint_recalib` |
| 台账引用面（`synthesis_data.json` 三处字面钉值）随 ①/② 措辞变更 | 会移线 ⇒ 属重钉流程 | `CS4` |

---

## 8. 现读证据与可复跑性

- 引文登记表：`out/re_work/qc/W3_20261002/doc2_runbook_terms/citations.json`（50 条，逐条 `path:line + 片段`）
- 自检：`out/re_work/qc/W3_20261002/doc2_runbook_terms/scripts/check_citations.py` ⇒ `runs/citation_selfcheck.txt`
- 终检：`out/re_work/qc/W3_20261002/doc2_runbook_terms/verify_doc2.py`（逐条复验引文 + 条款落位 + 写域快照 + 负控）
- 快照：`out/re_work/qc/W3_20261002/doc2_runbook_terms/snapshots/`（写域两件 + 11 个只读监视组共 560+ 件逐件 sha）

---

## 9. 并发报备（非本包所为）

本包交付时现读：`out/re_work/qc/W3_20261002/rpt2_gate_vocab/` 目录存在，目录 mtime **21:15**（RPT2 会话产物；本包**未读其内容、未写入**，不在 DOC2 写域）。
同批普查里，`out/re_work/qc/**` 中含 `GATE-MAP` / `GATE-REDLINE` 字面的文件清单**不含**该目录下任何文件 ⇒ 它若在用别的 token 或是机读表，与本件不构成同名重复定义；但「档位定义面」此刻可能有两处（本件 + 该机读产物）。
⇒ **由 Lead 裁定谁承载**：后续卡引用 `FIELD-REG` / `GATE-*` 定义前应同时检查这两处，避免第三处漂移。
另：只读监视组的并发情况以 `out/re_work/qc/W3_20261002/doc2_runbook_terms/runs/verify_doc2.txt` 的快照段为唯一依据（本包不凭印象写数字）。
