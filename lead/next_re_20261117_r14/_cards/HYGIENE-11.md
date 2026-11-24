# HYGIENE-11 — 11 行「全镜像 0 引用」的地址可信性核查

## 为什么要查

`R4_DERIVABILITY` 全量扫描 848 行 `name_only_no_ring4` 时，发现 **11 行属于 `NOT_DERIVABLE`**：它们的 entry

- 不被任何虚表槽持有（`vt_count = 0`）
- 无任何直接调用者（`direct_callers = 0`）
- `.text` 与 `.data` 中该 4 字节值出现 **0 次**（`text_imm_refs = data_imm_refs = 0`）

**这在物理上很可疑**：其中包含 `MapClass::MapClass`（构造函数）、`TriggerClass::GetInstance`、`TagClass::IsOnlyInstanceOfType` 这类**必然会被调用**的函数。构造函数 0 引用是不可能的。

**最可能的解释：这些行的 entry 地址与名字对不上**（名字→地址映射来自 YRpp/知识库，可能错位）。若如此，这些行就是「**用错地址证明了错误的函数**」——属数据完整性问题，必须查清。

**并且 11 行里 6 行属 S15**（`006E5850`/`007262D0`/`00726310`/`00726350`/`00726630`/`00727120`），而 S15 是本项目临界子系统（strict 63 / 门槛 79）。

## 待查的 11 行

| entry | 子系统 | 名字 |
|---|---|---|
| `004C52B0` | S20 | `EMPulseClass::noinit_t` |
| `004C6800` | S18 | `NetworkEvents::FillEvent_Animation` |
| `004CC680` | S06 | `MapClass::MapClass` |
| `004F6E70` | S14 | `HouseClass::GetStoragePercentage` |
| `0054E690` | S13 | `Kamikaze::Kamikaze` |
| `006E5850` | S15 | `TagClass::IsOnlyInstanceOfType` |
| `007262D0` | S15 | `TriggerClass::HasZoneEntryByEvent` |
| `00726310` | S15 | `TriggerClass::HasAllowWinAction` |
| `00726350` | S15 | `TriggerClass::HasGlobalSetOrClearedEvent` |
| `00726630` | S15 | `TriggerClass::GetInstance` |
| `00727120` | S15 | `TriggerTypeClass::FindByNameOrID` |

## 输入与工具

- `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`；（用 pefile 自取实际段范围）
- capstone 5.0.7（**必须 `skipdata=True`**）+ pefile 2024.8.26
- 技术条：RTTI 的 `pTD`/`pCHD` 是**绝对 VA**；装饰名在 `TD+8` 是**内联串**
- 只读输入：`COVERAGE\coverage.tsv`（第 3 列 name、第 6 列 evidence_path）、`R4_DERIVABILITY\all848.tsv`

## 对每一行要回答的四问

### 问 1 · 该地址处是不是一个「像函数」的东西？

- 是否有函数序言（`push ebp` / `sub esp,N` / 典型 `mov edi,edi` 前置）
- entrada 是否落在 atlas `function_atlas.tsv` 的 `entry` 列里（atlas 的 `entry` 是**小写**，须归一）
- 若是函数，函数体大小、指令数（用 capstone 走到 `ret` / 下溢）

### 问 2 · 该条目是不是「指向了函数中段」的错位地址？

- 检查该地址**之前 1–16 字节内**是否存在函数序言；若存在，给出真实函数起点
- 这是 YRpp 名字表最常见的错位形态

### 问 3 · 该 4 字节值在全镜像真的 0 次吗？（独立复算）

- 独立扫 `.text`/`.data`/`.rdata`/`.idata`：`dd <entry>`、`E8 <rel32>` 目标、`push imm32`、`mov reg,imm32`
- 与 `all848.tsv` 的 `text_imm_refs`/`data_imm_refs` 对比；**若你的结果与它不一致，如实报告差异**

### 问 4 · 名字与地址是否对得上？（最关键的判定）

- 若该函数在某个虚表里（哪怕不是主表），给出表与槽号，用 RTTI 类名与名字里的类名比对
- 若名字含类名（如 `MapClass::MapClass`、`TriggerClass::GetInstance`），检查该类的 RTTI 在镜像里是否存在、其虚表里第 N 槽是否指向**别的**地址（即名字的真身可能在别处）
- 给出结论：`地址可信` / `地址错位（附真实地址）` / `名字可疑（该类不存在或无此方法）` / `无法判定（说明缺什么）`

## 输出（只写 `HYGIENE_R11\`）

- `rows.tsv`：表头
  `entry	subsystem	name	in_atlas	looks_like_func	prologue_within_16	real_func_start	vt_count_recheck	text_refs_recheck	data_refs_recheck	class_rtti_exists	name_addr_verdict	reason`
  11 行数据
- `REPORT.md`：四问逐行结论 + **明确回答**
  1. 11 行里有几行是**地址错位**？各真实起点是什么？
  2. 有几行**地址可信但确实 0 引用**（真死代码 / 纯导出未用）？
  3. 有几行**名字可疑**（该类或该方法在本镜像不存在）？
  4. **这 11 行对 `coverage.tsv` 的影响**：若有错位或名字可疑，指出该行是 `[已证]` 还是其它级别，并说明「据错地址记 `[已证]` 是否需要撤回」——**只给建议，不自行改表**
- `probe.py`：可复跑

## 纪律

- **只读**。不许改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、`STATUS_BOARD.md`、`BOARD_ARCHIVE.md`、`R4_DERIVABILITY`、任何 `R4_FILL_*` / `AUDIT*` / `NAMED_PUSH_*`；只写 `HYGIENE_R11\`。
- 结论要如实：**「地址可信、真死代码」是完全有效的结论**，不要为了"发现问题"而硬判错位。
- 每行必须给地址与字节；只给判断不给依据的不算完成。
