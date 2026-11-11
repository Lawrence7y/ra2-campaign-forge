# ROUND_BATCH1 · 第一批 5 个静态逆向轮 成本台账固化

> 执行方：受限执行方（ra2-campaign-forge 逆向项目，子代理）
> 时点：2026-11-12 00:29:38+08:00（BASELINE 实跑，`_enum_batch1_stdout.txt:L0008`）；VERIFY 实跑时刻见 `_fp_check.txt:L0008`
> 工作区：`D:\Project\ra2-campaign-forge`
> 唯一写域：`lead\re_round_batch1_20261111\`（只新建，既有件零改动）
> 铁律：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 attach、未读活内存、未写 hook/采样/MiniDump/SuspendThread/StackWalk）；只读；python 一律 `python -I -X utf8 <绝对路径>`；指纹一律 hashlib 实算；只写材料直接支持的话。
> 定级标签（本文只用这三档，不使用无后缀的【已证】）：
> **【已证（字节级）】** = 磁盘文件字节 / 静态镜像字节扫描 / 文件内计数、地址、哈希的直接读数；
> **【已证（CFG）】** = 由静态反汇编控制流图、静态污点传播得到的图结构结论（不含运行期实际取值）；
> **【未证】** = 运行期机制、因果推断、跨图/跨版本普适性，以及材料未覆盖的完备性判断。

---

## STEP 1 · Top-10 定位与第一批 5 轮判定

### 1.1 全 10 条 Top-10（据 DISPOSITION.md §5 表格，行号来自实跑解析）

解析来源：`_enum_batch1_stdout.txt:L0012-L0024`（脚本正则解析 DISPOSITION.md，非手抄）。

| 排序 | 轮次目录名 | DISPOSITION.md 行号 | CSV 对应行 | CSV 建议批次 | 是否第一批入选 |
|:---:|:---|:---:|:---:|:---|:---:|
| **1** | `re_crashwriter_static_20261110` | `DISPOSITION.md:L149` | `DISPOSITION.csv:L148` | 第一批（补写 md 报告） | **★ 入选（静态逆向）** |
| **2** | `slot2_fullscan_20261111` | `DISPOSITION.md:L150` | `DISPOSITION.csv:L169` | 第一批（补写 md 报告） | **★ 入选（静态逆向）** |
| **3** | `playerctrl_semantics_20261111` | `DISPOSITION.md:L151` | `DISPOSITION.csv:L140` | 第一批（补写 md 报告） | **★ 入选（静态逆向）** |
| **4** | `re_loadbench_diff_20261110` | `DISPOSITION.md:L152` | `DISPOSITION.csv:L151` | 第一批（补写 md 报告） | **★ 入选（静态逆向）** |
| **5** | `re_map_preset_decode_20261110` | `DISPOSITION.md:L153` | `DISPOSITION.csv:L152` | 第一批（补写 md 报告） | **★ 入选（静态逆向）** |
| **6** | `ledger_apply_prep_20261110` | `DISPOSITION.md:L154` | `DISPOSITION.csv:L104` | 第二批（P1 优先补做） | 否 |
| **7** | `e3_unify_20261111` | `DISPOSITION.md:L155` | `DISPOSITION.csv:L69` | 第二批 | 否 |
| **8** | `dup_audit_20261110` | `DISPOSITION.md:L156` | `DISPOSITION.csv:L64` | 第二批（补写 md 报告） | 否 |
| **9** | `ok_falsify_20261110` | `DISPOSITION.md:L157` | `DISPOSITION.csv:L132` | 第二批（补写 md 报告） | 否 |
| **10** | `const_exit_fix_20261110` | `DISPOSITION.md:L158` | `DISPOSITION.csv:L36` | 第三批 | 否 |

（逐条 MD↔CSV 映射实跑输出：`_enum_batch1_stdout.txt:L0079-L0088`。）

### 1.2 哪 5 条属于「第一批 = 静态逆向轮」，据以判定的 DISPOSITION.md 行号

入选 5 条 = **Top-1 至 Top-5**，判定依据为 DISPOSITION.md 三处互相咬合的原文：

1. `DISPOSITION.md:L121-L127`：§5 mermaid `subgraph P0["第一批：P0 核心静态读数沉淀 (1-2天)"]`，其内 `R1..R5` 逐一点名 `re_crashwriter_static` / `slot2_fullscan` / `playerctrl_semantics` / `re_loadbench_diff` / `re_map_preset_decode`（实跑转录 `_enum_batch1_stdout.txt:L0027-L0032`）。
2. `DISPOSITION.md:L167`：§6 第一批执行内容第 1 条原文「为 Top-1 至 Top-5 轮次（…五者全名…）撰写 5 份标准 Markdown 报告（严格引用已落盘的 `_out.txt` 结论行）」（`_enum_batch1_stdout.txt:L0045`）。
3. `DISPOSITION.md:L21`：§1 高价值发现原文把「11-10 与 11-11 实施的 gamemd.exe 静态逆向」点名为同 5 个目录（`_enum_batch1_stdout.txt:L0051`）。

分类（来自 DISPOSITION）：5 轮在 `DISPOSITION.md:L74,L78,L73,L75,L76` 均为「仅探针 / **入账** / **第一批 (补md)」；CSV 对应行 `DISPOSITION.csv:L148,L169,L140,L151,L152` 均为「仅探针无报告 / 入账 / 第一批（补写 md 报告）」。

**关于「`re_*` 前缀」口径的如实报告（不擅自选一个）**：任务书把静态逆向轮描述为「`re_*` 前缀、纯静态分析的轮次」。按字面 `re_` 前缀，Top-10 中仅 **3** 条命中（`re_crashwriter_static`、`re_loadbench_diff`、`re_map_preset_decode`），`slot2_fullscan_20261111` 与 `playerctrl_semantics_20261111` **不带 `re_` 前缀**。但 DISPOSITION.md 自身以上三处（L21 / L121-L127 / L167）明确把这 5 个并列为「第一批 / 静态逆向 / 核心静态读数」，且两者探针 docstring 分别写明「100% 分块覆盖重验…纯静态」（`_sf_scan.py:L4-L7`）与「静态反汇编分析…只读磁盘文件」（`_ps_disasm.py:L2-L4`），确属纯静态分析。故本批次按 **DISPOSITION.md 明示的 5 条** 执行；「`re_` 前缀」只能覆盖其中 3 条，属命名口径差异，如实登记，不据此删改入选集。另 `DISPOSITION.md:L18` 写「6 轮静态逆向成果价值极高」、附录 X `L250` 写「5 个静态探针」、§6 `L168` 另列「同步登记入账」3 轮（`re_orphan_owners` / `ledger_exit_census` / `unknown_locate`），数字 6 与 5 不一致；本文按 §5/§6 明确的 5 个执行，「6」所指第 6 轮材料未指明，**未验**。

### 1.3 DISPOSITION.md 与 CSV 的 Top-10 一致性核对（如实报告差异）

- **CSV 没有 Top-10 排名清单**：CSV 为 185 行全量处置表，表头 7 列无排名/排序列（`_enum_batch1_stdout.txt:L0064-L0067`；`DISPOSITION.csv:L1`）。因此无法做「两个 Top-10 清单」的逐名次对比，只能比「建议批次」列。
- **一致部分**：Top-10 的 10 条在 CSV 都能找到同名行；批次归属与 MD §5 mermaid（P0/P1/P2）逐条一致：Top-1..5→第一批，Top-6..9→第二批，Top-10→第三批（`_enum_batch1_stdout.txt:L0079-L0088`）。
- **差异（不择一，全部登记）**：
  1. CSV「第一批」共 **8** 行（`_enum_batch1_stdout.txt:L0068-L0076`），比 MD Top-10 中的第一批 5 行多 **3** 轮：`ledger_exit_census_20261110`（`DISPOSITION.csv:L106`）、`re_orphan_owners_20261110`（`L153`）、`unknown_locate_20261110`（`L182`）。这 3 轮在 MD 中不进 Top-10 排名，但见 `DISPOSITION.md:L71,L77,L79`（入账 / 第一批 (补md)）与 `DISPOSITION.md:L168`（「同步登记入账」）。实跑差异行：`_enum_batch1_stdout.txt:L0089`。
  2. MD Top-10 中 5 条在 CSV 非第一批（Top-6..10），实跑差异行：`_enum_batch1_stdout.txt:L0090`。
  3. **CSV 与 MD 措辞口径的既有差异**：`DISPOSITION.md:L21` 与 §5 表格把若干读数写成机制结论（如「证得 0x0084F2BA 属 DEP 取指违规」「HouseClass 实例严格由 [Houses] 节条目数决定」「PercentBuilt 引擎零读取」），而 MD 附录 X（`DISPOSITION.md:L247-L272`）已把其中三条降级；CSV 对应行（`DISPOSITION.csv:L140,L148`）仍保留旧措辞。本文按附录 X 与后续件降级处理，见各轮「结论与定级」。
- **另记一处指纹自洽差异**：`DISPOSITION.md:L233` 自登记 `DISPOSITION.md` 为 31,032 B / sha256 `273d2789…`，实算为 33,471 B / sha256 `4d316342…`（`_enum_batch1_stdout.txt:L0219`、`L0328`），尺寸与哈希均不匹配；疑因附录 X 在该登记表之后追加。该行不能用作零改动证据；改用 §9 中 12 条外部既有件登记指纹（均匹配，见 `_enum_batch1_stdout.txt:L0322-L0334`）与 `_fp_check.txt` 前后实算比对。**本轮未修改该文件**（`_fp_check.txt` 复核）。

---

## STEP 2 / STEP 3 · 逐轮固化

> 各轮「目录文件清单」均来自实跑 `_enum_batch1_stdout.txt`（相对仓库根路径 + 字节数 + mtime，sha256 为 hashlib 实算）。
> 交叉核对统一对照三份后续/旁证件：`lead\re_chain_synthesis_20261111\`（CHAIN_SYNTHESIS.md + LEDGER_SECTION_DRAFT.md + _compare_repro_out.txt）、`lead\slot2_fullscan_20261111\`、`lead\re_orphan_owners_20261110\`。

---

### 轮次 ① `re_crashwriter_static_20261110`

- **轮次目录名 / 日期 / 分类**：`re_crashwriter_static_20261110` / 20261110 / 仅探针无报告、判定入账、第一批（补 md）（`DISPOSITION.md:L74`；`DISPOSITION.csv:L148`）。
- **探了什么（一句话）**：`_cw_disasm.py:L3-L12` 用 pefile+capstone 纯静态只读还原 `gamemd.exe` 中 0x0054A56E 的数据依赖链与 RTTI/虚表槽位，main 把结果写入同目录 `_cw_disasm_out.txt/.json` 并统计 MISMATCH（`_cw_disasm.py:L618-L626`）。
- **目录文件清单（实跑）**：`_enum_batch1_stdout.txt:L0094-L0097`，共 3 件：

  | 相对路径 | B | mtime (UTC) |
  |:---|---:|:---|
  | `lead/re_crashwriter_static_20261110/_cw_disasm.py` | 33570 | 2026-11-10T16:17:23Z |
  | `lead/re_crashwriter_static_20261110/_cw_disasm_out.json` | 23176 | 2026-11-11T13:15:22Z |
  | `lead/re_crashwriter_static_20261110/_cw_disasm_out.txt` | 13117 | 2026-11-11T13:15:22Z |

- **实际读数（每条给证据文件:行）**
  - `gamemd.exe` = 4,825,360 B，sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` — `_cw_disasm_out.txt:L4`、`:L150-L151`
  - `.data` = `[0x812000..0xB79BE4]`，`Characteristics=0xC0000040`（无 EXECUTE）；`0x0084F2BA` 落 .data — `_cw_disasm_out.txt:L8-L10`、`:L153`
  - `0x0084F2BA` 处 16 字节 `dd 3d c3 9c de 3d 7d 2c e0 3d 2e bc e1 3d d6 4b` — `_cw_disasm_out.txt:L145`
  - `0x0054A56E` 处字节 `c7 46 04 00 00 00 00` = `mov dword ptr [esi+4], 0` — `_cw_disasm_out.txt:L66`、`:L156`
  - 基类 vtable `0x7ECBFC` slot0..6 = `0x54a7b0, 0x54a4b0, 0x54a4f0, 0x54a5a0, 0x54a5d0, 0x54a610, 0x54a240`；派生 `0x7ECBDC` slot0..6 = `0x54a800, 0x54a4b0, 0x54a630, 0x54a1f0, 0x54a6e0, 0x54a220, 0x54a240` — `_cw_disasm_out.txt:L14-L17`
  - 全局对象 `0xAA1078` 在 .text 立即数引用恰 4 处：`0x543E8F / 0x543EC0 / 0x546060 / 0x546065` — `_cw_disasm_out.txt:L23`、`:L170`
  - `0x546069` = `call dword ptr [eax+8]`，slot2 虚派发：vptr `0x7ECBDC`→`0x54A630`，`0x7ECBFC`→`0x54A4F0` — `_cw_disasm_out.txt:L117-L122`、`:L171-L172`
  - `0x7C8B3D` 有 4499 个调用点、`0x7C8E17` 有 2832 个调用点；函数 `0x54A4F0` 线性 disasm 52 条指令到达目标 — `_cw_disasm_out.txt:L175`、`:L157`
  - `0x54A577` = `mov dword ptr [esi+4], edi`（置 0 后 8 字节内无条件覆盖） — `_cw_disasm_out.txt:L68`、`:L177`

- **结论与定级**
  - **R1-01【已证（字节级）】**：靶件身份、节属性、目标指令字节、VA 地址处文件字节、RTTI 虚表槽位值、`0xAA1078` 引用计数 4、堆原语调用点计数 4499/2832、52 条指令均为磁盘静态字节直接读数（证据逐条见上）。缺什么证据：无（对当前静态镜像成立）；**不覆盖**其它 gamemd.exe 版本、其它地图、运行期状态。
  - **R1-02【已证（CFG）】**：函数 `0x54A4F0..0x54A58E` 静态控制流图 — `0x54A53A je 0x54A575`、`0x54A560 je 0x54A575` 跳过置零点；仅 `Vector!=0 && IsAllocated!=0` 时经 `0x54A566 call 0x7C8B3D` 到达 `0x54A56E`；`esi←ecx←0xAA1078`，`0x546069` 为唯一虚派发点；vptr 值决定派发去向（`_cw_disasm_out.txt:L58-L68, L108-L122, L126-L135, L168-L177`；后续件同口径 `CHAIN_SYNTHESIS.md:L72-L73`）。缺什么证据：运行期执行轨迹、各条件分支实际取值；静态 CFG 不等于运行期路径。
  - **R1-03【未证】**：「0x0054A56E 正常态不可达 ⇒ 崩在该点必由状态异常导致」及「0x0084F2BA 属 DEP 取指违规/崩因」。缺什么证据：崩溃现场寄存器上下文、MiniDump、调用栈回溯、真机动态复现。`_cw_disasm_out.txt:L136` 自述「该状态归因超出静态能力, 如实报」、`:L147` 自述「静态不能证实因果」；`DISPOSITION.md:L210` 明列静态推论在真机端到端复现仍属未验；附录 X.1 `DISPOSITION.md:L252-L256` 明确降级为「故障地址，性质未定谳」；`CHAIN_SYNTHESIS.md:L74, L133, L143-L145` 标【未证】并禁止定谳。仅 R1-01 中的 .data 范围/标志/字节读数属已证。
  - **R1-04【已证（字节级）】**：`0x7ECBDC` 写入仅 1 处 `0x543E8D`，`0x7ECBFC` 写入 3 处 `0x543EBE / 0x54A7B6 / 0x54A806`；孪生函数 `0x54A630` 同构 free-then-null（`free 0x54A699 / null 0x54A6A1`）（`_cw_disasm_out.txt:L139-L142, L162-L165, L173`）。缺什么证据：无（静态镜像内计数）；不含「运行期仅有一个实例」的动态证明。

- **是否已被取代 / 与哪份后续件一致或冲突**
  - 未被取代：`DISPOSITION.md:L74` 判「入账 第一批 (补md)」；`DISPOSITION.md:L88`、`L109` 把空目录 `re_chain_semantics_20261110` 废弃并点名本轮已交付 `_cw_disasm_out.txt` 与 `.json`。
  - 一致（读数被复用）：`CHAIN_SYNTHESIS.md:L71-L73` 直接引用 `_cw_disasm_out.txt:L66,L68,L34-L66` 并标为「已证」（该后续件原文标签）；`LEDGER_SECTION_DRAFT.md:L10` 收口「0x0054A56E 静态覆盖」；`_compare_repro_out.txt:L16-L17` 复现门 MATCH（整体 `L49` MATCH=14 / MISMATCH=0）。
  - 冲突/降级：`DISPOSITION.md:L252-L256`（附录 X.1）、`CHAIN_SYNTHESIS.md:L74` 把 DEP 结论降级；**源输出 `_cw_disasm_out.json:L38` 仍保留旧 verdict「EIP 进入不可执行页 → 静态上为取指违规(DEP)」**，与后续件口径冲突，如实登记（本文按后续件降级，不改写既有件）。
- **可入账摘要**：`0x54A56E=c7460400000000；.data=0xC0000040；0xAA1078引用4处`（≤60 字，仅含已证字节级读数）

---

### 轮次 ② `slot2_fullscan_20261111`

- **轮次目录名 / 日期 / 分类**：`slot2_fullscan_20261111` / 20261111 / 仅探针无报告、判定入账、第一批（补 md）（`DISPOSITION.md:L78`；`DISPOSITION.csv:L169`）。
- **探了什么（一句话）**：`_sf_scan.py:L4-L34` 以 100% 分块覆盖 + 字节级普查重验「全 .text 经 vtable slot2 调用 `0x54A4F0 / 0x54A630`」的所有调用点（T1–T5 + G1a–G6 闸门），main 写出 `_sf_scan_out.txt/.json` 并统计 MISMATCH（`_sf_scan.py:L1136-L1144`）。
- **目录文件清单（实跑）**：`_enum_batch1_stdout.txt:L0098-L0101`，共 3 件：

  | 相对路径 | B | mtime (UTC) |
  |:---|---:|:---|
  | `lead/slot2_fullscan_20261111/_sf_scan.py` | 55866 | 2026-11-11T00:13:38Z |
  | `lead/slot2_fullscan_20261111/_sf_scan_out.json` | 1522576 | 2026-11-11T13:16:05Z |
  | `lead/slot2_fullscan_20261111/_sf_scan_out.txt` | 158502 | 2026-11-11T13:16:05Z |

- **实际读数（每条给证据文件:行）**
  - 靶件 4,825,360 B / sha256 `73201cc0…`（`_sf_scan_out.txt:L4`）；`.text = [0x401000..0x7E038D] = 4,060,045 B`（`:L8`）
  - 单次 disasm 155,215 条、末条 `0x46F59D`、覆盖 452,000 B（11.13%）；分块 `0x10000`×62 块 = 1,150,117 条；分块 seg-extend = 1,392,527 条 / 65 个自然停点（`_sf_scan_out.txt:L9-L11`）
  - 字节级（解码无关）：`call [reg+8]` 1715、`jmp [reg+8]` 1、异形 2；主流 seg-extend `call+jmp [reg+8]` = 1714（call 1713 / jmp 1）；对照流 1311（`_sf_scan_out.txt:L32-L34`）
  - `dword==0x54A4F0` 全镜像仅 1 处 `0x7ECC04`；`dword==0x54A630` 仅 1 处 `0x7ECBE4`；直接 call/jmp 与 E8/E9 字节级命中均为 `[]`（`_sf_scan_out.txt:L14-L15, L18-L19`）
  - `0x7ECBFC×3 + 0x7ECBDC×1` 共 4 处均落在 c7 立即数内（`0x543EC4 / 0x54A7B8 / 0x54A808 / 0x543E93`）；`0xAA1078` 的 imm32/disp32 引用恰 4 处（`0x543E8F / 0x543EC0 / 0x546060 / 0x546065`）；`load r32 ← [0xAA1078]` 恰 1 处 `0x54605F`，`store reg → [0xAA1078]` = 0（`_sf_scan_out.txt:L22, L26-L28`）
  - `0x546069` = `call dword ptr [eax+8]`，this 来自 `0x546064 mov ecx, 0xaa1078`，vptr 来自 `0x54605F mov eax, [0xaa1078]`（`_sf_scan_out.txt:L43-L47, L66-L68`）
  - T5：GROW `0x545150..0x546D92`，从唯一 vptr 装载 `0x54605F` 污点传播消费者恰 1 个 `0x546069`，逃逸 `[]`；`[FACT] T5-final: 1714 个主流 slot2 点中可能指向 0x54A4F0/0x54A630 的恰 1 个: 0x546069`（`_sf_scan_out.txt:L40, L1831-L1834`）

- **结论与定级**
  - **R2-01【已证（字节级）】**：上述 .text 范围/字节数、三种反汇编计数（155215 / 1150117 / 1392527）、1715/1/2 与 1714 的调用点计数、两组 dword 各 1 处、直接调用 0 命中、4 处 c7 立即数、4 处 `0xAA1078` 引用、1 处 load / 0 处 store 均为磁盘静态字节扫描读数（`_sf_scan_out.txt:L8-L34, L18-L28, L1820-L1830`）。缺什么证据：无（对该静态镜像）；不覆盖运行期动态生成/复制的指针值。
  - **R2-02【已证（CFG）】**：静态污点传播与派发图 — `GROW = 0x545150..0x546D92`，唯一 vptr 装载 `0x54605F` 的消费者恰 1 个 `0x546069`，无 push/store/ret 逃逸；该点 this/vptr 来源与常态 `0x7ECBDC→0x54A630`、atexit 后 `0x7ECBFC→0x54A4F0` 的去向（`_sf_scan_out.txt:L39-L47, L1831-L1834`；后续件 `CHAIN_SYNTHESIS.md:L69-L70` 同口径）。缺什么证据：运行期寄存器实际值、间接/动态派发轨迹；静态图结论不含运行期完备性。
  - **R2-03【未证】**：「函数指针值不可能在运行期被复制/物化到任何其它单元」「终结虚表调用点漂移猜想」「100% 覆盖 ⇒ 运行期调用面穷尽」，以及结论对其它地图/其它 exe 版本的普适性。缺什么证据：动态执行轨迹、断点/采样日志、跨版本镜像对照扫描。`_sf_scan_out.txt:L20` 本身是静态编码扫描结论（`FF15/FF25/A1/8B/89/SIB-abs 全编码 = 0`），不能升格为运行期机制；`DISPOSITION.md:L210` 要求运行期机制标未验；`CHAIN_SYNTHESIS.md:L67` 边界栏的「无法在运行期逃逸」按本铁律不予采纳。
  - **R2-04【已证（字节级）】**：G1b 全编码装载/调用 slot2 单元计数 = 0；G2 值 `0x7ECBFC×3 + 0x7ECBDC×1` = 4 处；G4-load `load r32 ← [0xAA1078]` 恰 1 处、`store reg →` 0 处；G5 `.rdata/.data` 无 `dword==0xAA1078`（`_sf_scan_out.txt:L20, L22, L27-L29, L1821-L1829`）。缺什么证据：无（静态镜像字节普查）；不含「无别名合成路径读取 vptr 单元」的运行期证明。

- **是否已被取代 / 与哪份后续件一致或冲突**
  - **本轮是取代者而非被取代者**：`DISPOSITION.md:L68` 与 `DISPOSITION.csv:L74` 载明 `esi_caller_trace_20261111` 因 capstone 在 `0x6F59D` 截断风险被本轮 100% 分块重验取代；`DISPOSITION.md:L150` 仍把本轮列为 Top-2 第一批。
  - 一致：`CHAIN_SYNTHESIS.md:L66-L70` 逐项引用 `_sf_scan_out.txt:L13-L20, L7-L11, L43-L47, L21-L24`；`LEDGER_SECTION_DRAFT.md:L8-L9` 收口「直接调用为零 / 唯一实效调用点」；`_compare_repro_out.txt:L21-L22` 复现门 MATCH。
  - 冲突/边界：`CHAIN_SYNTHESIS.md:L67` 的边界说明「函数指针值无法在运行期逃逸或复制」被本文按铁律降为【未证】；`DISPOSITION.md:L21` 的「终结虚表调用点漂移猜想」同为机制化措辞，本文不采信为已证。
- **可入账摘要**：`1714个[reg+8]点；0x54A4F0/0x54A630各1处；0xAA1078引用4处`（≤60 字，仅含已证字节级读数）

---

### 轮次 ③ `playerctrl_semantics_20261111`

- **轮次目录名 / 日期 / 分类**：`playerctrl_semantics_20261111` / 20261111 / 仅探针无报告、判定入账、第一批（补 md）（`DISPOSITION.md:L73`；`DISPOSITION.csv:L140`）。
- **探了什么（一句话）**：`_ps_disasm.py:L2-L10` 以 0x800 分块容错反汇编只读分析 `gamemd.exe` 中 PlayerControl / PercentBuilt 的字符串、xref、读写点与 HouseClass 创建循环，main 流式写出 `_ps_disasm_out.txt/.json`（`_ps_disasm.py:L455-L474`）。
- **目录文件清单（实跑）**：`_enum_batch1_stdout.txt:L0102-L0105`，共 3 件：

  | 相对路径 | B | mtime (UTC) |
  |:---|---:|:---|
  | `lead/playerctrl_semantics_20261111/_ps_disasm.py` | 20572 | 2026-11-10T18:16:14Z |
  | `lead/playerctrl_semantics_20261111/_ps_disasm_out.json` | 3297 | 2026-11-11T13:16:39Z |
  | `lead/playerctrl_semantics_20261111/_ps_disasm_out.txt` | 65202 | 2026-11-11T13:16:39Z |

- **实际读数（每条给证据文件:行）**
  - 靶件 4,825,360 B / sha256 `73201cc0…`（`_ps_disasm_out.txt:L4-L6`）
  - 字符串出现次数：`PlayerControl` 1 处 `0x824E28`、`PercentBuilt` 1 处 `0x8189A0`、`NodeCount` 1 处 `0x818994`、`MaxPlayer` 0 处、`MinPlayer` 0 处、`MaxPlayers` 2 处 `0x83407E/0x83F3F0`、`MinPlayers` 1 处 `0x83F3FC`（`_ps_disasm_out.txt:L11-L18`；`_ps_disasm_out.json:L30-L50`）
  - .text xrefs：`PlayerControl` → `0x500BBF / 0x5012ED`；`PercentBuilt` → `0x42EC05 / 0x42ED80`；`NodeCount` → `0x42EC14 / 0x42ED93`（`_ps_disasm_out.txt:L32-L42`）
  - 分块扫描 `instructions = 1328762`、`max_va = 0x7e0ffe`、`trap_va = 0x46f59d`、`passed = true`；`n_call_targets = 7279`（`_ps_disasm_out.json:L74-L80`）
  - `0x500BD6 call 0x5295F0`（Get_Bool "PlayerControl"）→ `0x500BDD mov byte ptr [ebx+0x1ED], al`；`0x500BE3 je 0x500c51`；`0x500C51` 分支写入 `[ebx+0x30C]`（`_ps_disasm_out.txt:L113-L147`）
  - HouseClass 创建点 8 处：`0x500a30, 0x500b19, 0x59a198, 0x687fc3, 0x6881a0, 0x6882fe, 0x688351, 0x6c3ed1`（`_ps_disasm_out.txt:L905`；`_ps_disasm_out.json:L101-L110`）
  - PercentBuilt 直接读点普查：含 `[reg+0x1C]` 且引用 0x5700 族的函数 0 个；三处原始字节 `1c 57 00 00` 命中 `0x401E00 / 0x674FC0 / 0x6750B0` 均为 call rel32 位移巧合；`runtime_consumers = 0`（`_ps_disasm_out.txt:L893-L898`；`_ps_disasm_out.json:L93-L100`）

- **结论与定级**
  - **R3-01【已证（字节级）】**：靶件身份、所列字符串的精确出现次数与 VA、xref 地址清单、分块扫描指令数 1,328,762 / 陷阱 VA `0x46f59d`、调用目标数 7279、8 处创建点地址均为静态镜像字节/字面扫描读数（证据逐条见上）。缺什么证据：无（对该静态镜像）；`MaxPlayer=0 处`只说明精确字符串不存在，不说明引擎读不到任何等价键（后者属机制，见 R3-03）。
  - **R3-02【已证（CFG）】**：`Read_INI 0x500B40` 内 `0x500BD6` 读到 `HouseClass+0x1ED`，分支只改 `+0x30C` 起始资金（`_ps_disasm_out.txt:L113-L147, L492-L495`）；创建 wrapper `0x5009B0` 的 LOOP1 `0x5009D1..0x500A83` 无 PlayerControl 条件、LOOP2 只调 Read_INI 与难度、LOOP3 仅 HouseArray 为空时兜底（`_ps_disasm_out.txt:L636-L642`）；8 处创建点均未测试该标志（`_ps_disasm_out.json:L135-L136`）。缺什么证据：运行期分支实际取值、ctor 实际命中次数与返回地址（本轮自己把断点验证列为「静态无法裁定」，`_ps_disasm_out.txt:L1271-L1282`）。
  - **R3-03【未证】**：「HouseClass 实例数严格由 [Houses] 节条目数决定 / 无 PlayerControl 门控（运行期机制）」「PercentBuilt 写入后引擎零读取、Neutral=100 无行为差异」「地图键 MaxPlayer 引擎读不到」。缺什么证据：全镜像间接读点（虚表/回调/别名）普查表与计数、运行期 ctor 拦截日志、动态键解析轨迹。`DISPOSITION.md:L258-L264`（附录 X.2）只认可「该地图内 [Houses]↔house 节一一对应」、`L266-L268`（附录 X.3）把零读取按未验处理；`CHAIN_SYNTHESIS.md:L76, L84, L146-L151` 与 `LEDGER_SECTION_DRAFT.md:L23-L24` 同标未证/未验；`_oo_map_out.txt:L141-L150` 明写「运行期 meta_count=4 是引擎侧的实例化结果，文件本身…无法从文件验证或反驳」。
  - **R3-04【已证（字节级）】**：全 `.text` 对 `[reg+0x571C]` 的**直接**读指令数 = 0；同时引用 0x5700 族且含 `[reg+0x1C]` 的函数 0 个；三处 `1c 57 00 00` 字节命中均为 call rel32 位移巧合（`_ps_disasm_out.txt:L893-L898`；`_ps_disasm_out.json:L93-L100`）。缺什么证据：静态直接读点普查不含间接读（虚表/基类指针别名），该完备性判断本身属【未证】，见 R3-03 与 `CHAIN_SYNTHESIS.md:L84`。

- **是否已被取代 / 与哪份后续件一致或冲突**
  - 未被取代：`DISPOSITION.md:L73` 判「入账 第一批 (补md)」；`DISPOSITION.md:L84`、`L105` 把空目录 `housecount_trace_20261111` 废弃并点名本轮闭环交付。
  - 一致（读数被复用）：`CHAIN_SYNTHESIS.md:L81-L83` 引用 `_ps_disasm_out.txt:L11, L113-L115, L116-L147, L36-L39`；`LEDGER_SECTION_DRAFT.md:L18-L19` 收口两项静态字面语义；`_compare_repro_out.txt:L26-L27` MATCH（stdout 0 B 原因见 `CHAIN_SYNTHESIS.md:L56`）。
  - 冲突/降级：`DISPOSITION.md:L258-L268`（附录 X.2/X.3）把「House 实例由 [Houses] 严格决定」「PercentBuilt 引擎零读取」降级；`DISPOSITION.csv:L140` 仍保留旧措辞；`CHAIN_SYNTHESIS.md:L76, L84` 标未证/未验；`re_orphan_owners_20261110/_oo_map_out.txt:L28-L30, L141-L150` 只给文件层 14↔14 事实，不构成引擎机制证据。
- **可入账摘要**：`PlayerControl@0x824E28；PercentBuilt@0x8189A0；8处创建点`（≤60 字，仅含已证字节级读数）

---

### 轮次 ④ `re_loadbench_diff_20261110`

- **轮次目录名 / 日期 / 分类**：`re_loadbench_diff_20261110` / 20261110 / 仅探针无报告、判定入账、第一批（补 md）（`DISPOSITION.md:L75`；`DISPOSITION.csv:L151`）。
- **探了什么（一句话）**：`_ld_diff.py:L2-L13` 对 6 份在盘 LoadBench 地图/参照件做指纹、节结构、实体计数、压缩/编码六维逐维比对，main 写出 `_ld_diff_out.txt/.json`（`_ld_diff.py:L434-L454`）。
- **目录文件清单（实跑）**：`_enum_batch1_stdout.txt:L0106-L0109`，共 3 件：

  | 相对路径 | B | mtime (UTC) |
  |:---|---:|:---|
  | `lead/re_loadbench_diff_20261110/_ld_diff.py` | 24231 | 2026-11-10T15:55:15Z |
  | `lead/re_loadbench_diff_20261110/_ld_diff_out.json` | 28794 | 2026-11-11T13:18:50Z |
  | `lead/re_loadbench_diff_20261110/_ld_diff_out.txt` | 15142 | 2026-11-11T13:18:50Z |

- **实际读数（每条给证据文件:行）**
  - 六份在盘件指纹：`big` 92,332 B / md5 `3c47bff8915ba94de3ad33c9958a33dd` / crc32 `0ad4855d` / entropy 5.652 / CRLF 1808；`small` 25,604 B / md5 `d9a57d5f3d0844ad0ca186f537feeb8d` / crc32 `db493c05` / entropy 4.699 / CRLF 0、LF 696；`ref` 92,332 B（与 big md5+sha256 全等 `True`）；`xmp_t32` 与 `carrier_qc104` 均 222,799 B / md5 `11ec8ff6bb56cca2951c608985f28d67`；`xmp_l1` 311,822 B / md5 `7aca9c218314939140319cdbdd64bc1c`（`_ld_diff_out.txt:L6-L12`）
  - 实体行数：big Units 240 / Infantry 160 / Structures 41（Americans 120+80、Russians 120+80、Neutral 41）；small 240/160/0；`xmp_t32` 1680/1120/41（14 房各 120 车+80 步）；`xmp_l1` 3360/2240/0（14 房各 240 车+160 步）（`_ld_diff_out.txt:L24-L38`）
  - 小节差集 `big=34 small=28 common=13`（`_ld_diff_out.txt:L40`）
  - `[Map]` 几何：big `0,0,52,53` / `Header 46×44`、small `0,0,100,100` / `100×100`（`_ld_diff_out.txt:L19-L20`）；`IsoMapPack5` b64 大版 36,912 B→解码 27,684 B、小版 16 B→解码 12 B（`_ld_diff_out.txt:L83-L84`）
  - 压缩检验：small `zlib_magic_0x78=False`、`printable=1.0000`；头 32 字节 big `'; Map created with FinalAlert 2('`、small `'[Header]\nWidth=100\nHeight=100\nSt'`（`_ld_diff_out.txt:L7, L15-L16, L89-L90`）
  - 结论行原文：「两份只是共享同一个文件名」「不是同一张图、不是其子集、不是其压缩形态」（`_ld_diff_out.txt:L100`）

- **结论与定级**
  - **R4-01【已证（字节级）】**：6 份在盘文件的尺寸、md5、crc32、熵、行尾计数，4 组实体行数（240/160/41、240/160/0、1680/1120/41、3360/2240/0）、小节数 34/28/13、`[Map]` 几何与 `Header` 尺寸均为磁盘文件字节与文本解析直接读数（`_ld_diff_out.txt:L6-L12, L19-L40, L95-L96`）。缺什么证据：无（对所列在盘文件成立）；不覆盖历史任一时刻不在盘的其它副本。
  - **R4-02【已证（字节级）】**：`IsoMapPack5` 解码体积 27,684 B vs 12 B、小版 zlib 魔数 False、可打印比 1.0000、两版头 32 字节不同；据此「两版非同一张图、非子集、非压缩形态」是所列两文件之间的字节层面对照结论（`_ld_diff_out.txt:L15-L16, L83-L91, L100`）。缺什么证据：无（对该两文件）；不含「哪份被游戏实载」的结论。
  - **R4-03【未证】**：「台账所指 1680 实载图 = 222,799 B 变体以 XMP29U2.MAP 名被游戏实载」「小版是生成器 2026-09-25 18:41 第一代合成图」「l1 时代换成 U0800 H1 字节」。缺什么证据：游戏加载轨迹/文件打开日志、生成器原始产物与时间戳链、运行期地图名↔字节映射记录。静态文件比对只能证明「这些文件互异、这些计数如此」，不能证明「谁被载入」；`_ld_diff_out.txt:L96-L101` 的「实载/含义」属跨文件口径推断，`DISPOSITION.md:L210` 要求运行期机制未验，后续件 `CHAIN_SYNTHESIS.md:L80` 与 `LEDGER_SECTION_DRAFT.md:L15` 也只采信「三份物理互异」。
  - **R4-04【未证】**：台账指纹 `93c2974b` 的算法与归属。`_ld_diff_out.txt:L97` 写「台账指纹 93c2974b 未能在在盘候选的 md5/sha1 前缀/CRC32 上复现…本项未破解」、`:L103` 逐项列出否证数值。缺什么证据：该内部指纹的算法说明与可复现实算；`CHAIN_SYNTHESIS.md:L80` 却把 222,799 B 件写作「sha `93c2974b` / md5 `11ec8ff6`」，与源输出 L103 的「未匹配」表述**冲突**，如实登记，不择一。

- **是否已被取代 / 与哪份后续件一致或冲突**
  - 未被取代：`DISPOSITION.md:L75` 判「入账 第一批 (补md)」；`DISPOSITION.md:L87`、`L108` 把空目录 `mapfile_1680_hunt_20261111` 废弃并点名本轮已查清 1680 寻源（本文按 R4-03 只采信「在盘文件计数」，把「实载」留未证）。
  - 一致：`CHAIN_SYNTHESIS.md:L78-L80` 引用 `_ld_diff_out.txt:L25-L28, L29-L31, L88-L103`；`LEDGER_SECTION_DRAFT.md:L15`「三份地图物理互异」；`_compare_repro_out.txt:L46-L47` 复现门 MATCH。
  - 冲突：`CHAIN_SYNTHESIS.md:L80` 的 `93c2974b` 归属表述 vs `_ld_diff_out.txt:L97,L103`（详见 R4-04）；另 `DISPOSITION.md:L76` 与 `re_map_preset_decode` 的计数互相咬合，无数值冲突。
- **可入账摘要**：`big 92332B/240-160-41；small 25604B/240-160-0；ref与big全等`（≤60 字，仅含已证字节级读数）

---

### 轮次 ⑤ `re_map_preset_decode_20261110`

- **轮次目录名 / 日期 / 分类**：`re_map_preset_decode_20261110` / 20261110 / 仅探针无报告、判定入账、第一批（补 md）（`DISPOSITION.md:L76`；`DISPOSITION.csv:L152`）。
- **探了什么（一句话）**：`_md_parse.py:L2-L12` 对三份在盘地图按 INI 小节逐槽位解析 Units/Infantry/Structures/Aircraft 条目并按 house 分组计数，main 写出 `_md_parse_out.txt/.json` 并附「台账声称核对」表（`_md_parse.py:L338-L366`）。
- **目录文件清单（实跑）**：`_enum_batch1_stdout.txt:L0110-L0113`，共 3 件：

  | 相对路径 | B | mtime (UTC) |
  |:---|---:|:---|
  | `lead/re_map_preset_decode_20261110/_md_parse.py` | 15205 | 2026-11-10T15:55:05Z |
  | `lead/re_map_preset_decode_20261110/_md_parse_out.json` | 29521 | 2026-11-11T13:18:29Z |
  | `lead/re_map_preset_decode_20261110/_md_parse_out.txt` | 12845 | 2026-11-11T13:18:29Z |

- **实际读数（每条给证据文件:行）**
  - A `scratch/boot_probe/arm_a/XMP29U2.MAP` = 311,822 B / sha256 `0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc` / 27 节 / `LF_only=5884`；`[Units]` 3360、`[Infantry]` 2240、`[Structures]` 不存在→0、`[Aircraft]` 0；14 个 owner 各 240 车 + 160 步；Special 屋 240 车 / 160 步（`_md_parse_out.txt:L6-L18, L33-L34, L49-L51`）
  - B `ra2bench/[2]0LoadBench_U0400.yrm` = 92,332 B / sha256 `cb5785a1e540b8fcdbb7e8948dfb5a0b77fde4e5d8a0c38172e7676531c94ba7` / 34 节 / CRLF 1808；Units 240 / Infantry 160 / Structures 41；Russians 与 Americans 各 120 车 + 80 步，Neutral 41 建筑（`_md_parse_out.txt:L54-L78`）
  - C `out/loadbench/[2]0LoadBench_U0400.yrm` = 25,604 B / sha256 `6027eb2061a48e58c8876827f54575f3698bc2d619c00f945e12b4beef5eaa14` / 28 节 / LF 696；Units 240 / Infantry 160 / Structures 0；Russians 与 Americans 各 120/80（`_md_parse_out.txt:L81-L103`）
  - 台账声称核对表 7 项：MAP 建筑 0 / Units 3360 / Infantry 2240 / Special 240 → 「符合」；yrm 建筑 41 → `{"ra2bench_yrm": 41, "out_yrm": 0}`「ra2bench 符合 / out 不符」；yrm Special 车辆 120 → `{"ra2bench_yrm": 0, "out_yrm": 0}`「不符」；yrm 车辆 1680 / 步兵 1120 → 两份实算均 `240/160`「两份 yrm 均不符」（`_md_parse_out.txt:L138-L166`）
  - LoadBench 家族出处扫描逐件尺寸/计数清单（EMPTY 3,669 B / U0050 6,501 B / U0200_H1 79,411 B / U0800_H1 309,822 B 等；逐件见 `_md_parse_out.txt:L113-L135`）

- **结论与定级**
  - **R5-01【已证（字节级）】**：A 文件尺寸/哈希/节数/行尾、`[Units]` 3360 / `[Infantry]` 2240 / `[Structures]` 0 / `[Aircraft]` 0、14 个 owner 各 240+160、Special 240/160 均为磁盘文本逐行解析读数（`_md_parse_out.txt:L6-L18, L33-L34, L49-L51`）。缺什么证据：无（对该在盘文件）；不覆盖其它时点/其它路径的同名文件。
  - **R5-02【已证（字节级）】**：B/C 两份 yrm 的尺寸/哈希/节数/行尾与 240/160/41、240/160/0、2 房各 120+80、Neutral 41 均为磁盘文本解析读数（`_md_parse_out.txt:L54-L103`）。缺什么证据：无（对该两份在盘 yrm）。
  - **R5-03【已证（字节级）】**：「台账声称核对」7 项判定所依赖的实算数值（3360 / 2240 / 0 / 240 / 41 / 0 / 两份 yrm 均 240·160）与家族件逐件尺寸/计数清单均为文件解析读数（`_md_parse_out.txt:L113-L135, L138-L166`）。缺什么证据：无（对所列文件）；「证伪」仅指与所列在盘文件的实算值不符。
  - **R5-04【未证】**：「彻底证伪在盘 yrm 存在 1680 单位的声称」的跨版本/跨时点普适性，以及「为卡顿压测建立真实实体底数」这类业务因果。缺什么证据：历史时点文件快照链、运行期压测/卡顿数据；`DISPOSITION.md:L153` 自身只给「从文件字节层面」口径、`L210` 明列运行期机制未验。本文只把 R5-03 的「所列两份在盘 yrm 实算 240/160」登记为已证。

- **是否已被取代 / 与哪份后续件一致或冲突**
  - 未被取代：`DISPOSITION.md:L76` 判「入账 第一批 (补md)」；`DISPOSITION.md` 附录 X（`L247-L272`）未触及本轮读数；`_compare_repro_out.txt:L41-L42` 复现门 MATCH。
  - 一致：`CHAIN_SYNTHESIS.md:L77, L79` 引用 `_md_parse_out.txt:L17-L50, L81-L103`；`LEDGER_SECTION_DRAFT.md:L13` 收口「3360/2240/0、共 5600、14 带各 400」；`_ld_diff_out.txt:L25-L38` 的 big/small/xmp_t32/xmp_l1 计数与 R5-01/02 逐项吻合；`re_orphan_owners_20261110/_oo_map_out.txt:L50`（Units 3360）亦一致。
  - 冲突：读数层面无冲突；仅措辞口径收紧 — `DISPOSITION.md:L76`「彻底证伪在盘 yrm 含 1680 单位的声称」被本文限定为「所列在盘文件」范围（R5-04），属口径收紧而非数值冲突。
- **可入账摘要**：`MAP 3360/2240/0；两份yrm均240/160；台账1680/1120在盘均不符`（≤60 字，仅含已证字节级读数）

---

## 批次小结 · 5 轮定级条目计数

每轮「结论与定级」按 R*-NN 编号逐条计数（共 20 条，每条只挂一档）：

| 轮次 | 【已证（字节级）】 | 【已证（CFG）】 | 【未证】 | 小计 |
|:---|:---:|:---:|:---:|:---:|
| ① `re_crashwriter_static_20261110` | 2（R1-01, R1-04） | 1（R1-02） | 1（R1-03） | 4 |
| ② `slot2_fullscan_20261111` | 2（R2-01, R2-04） | 1（R2-02） | 1（R2-03） | 4 |
| ③ `playerctrl_semantics_20261111` | 2（R3-01, R3-04） | 1（R3-02） | 1（R3-03） | 4 |
| ④ `re_loadbench_diff_20261110` | 2（R4-01, R4-02） | 0 | 2（R4-03, R4-04） | 4 |
| ⑤ `re_map_preset_decode_20261110` | 3（R5-01, R5-02, R5-03） | 0 | 1（R5-04） | 4 |
| **合计** | **11** | **3** | **6** | **20** |

- 三档全部用到；**【已证（字节级）】只挂在磁盘字节/静态镜像字节扫描/文件计数的直接读数上**，【已证（CFG）】只挂静态反汇编控制流图与静态污点传播结论，运行期机制、因果推断、跨图/跨版本普适性一律【未证】并逐条写明缺什么证据。本文不使用无后缀的【已证】。
- 5 轮的「可入账摘要」均 ≤60 字且只含已证字节级读数，不含推测性内容。
- 5 轮合计目录文件 **15 件**（每轮 3 件，`_enum_batch1_stdout.txt:L0094-L0113`）；交叉核对目录 `re_chain_synthesis_20261111` 35 件、`slot2_fullscan_20261111` 3 件、`re_orphan_owners_20261110` 6 件（`_enum_batch1_stdout.txt:L0115-L0162`）。

---

## 边界与未验

1. **零真机边界**：本轮只读磁盘既有件（python `open(..., 'rb')` / `read` 工具 / `glob` / `grep`），**未启动** `gamemd.exe`、`ra2loader.exe`、`YURI.exe`；未 attach、未读活进程内存、未写 hook / 采样 / MiniDump / SuspendThread / StackWalk 代码；未执行任何探针脚本的 main（仅静态阅读其源码）。所有「实际读数」均引自已落盘的 `_out.txt` / `_out.json` 与脚本源码行，不是本轮重跑所得。
2. **只读与写域隔离**：仅在 `lead\re_round_batch1_20261111\` 内新建文件；未修改、覆盖或删除任何既有件；未执行 `git add/commit/push/reset/checkout`。既有件零改动证据见 `_fp_check.txt`：前后两次 hashlib 实算逐件比对（size / mtime_ns / sha256），`_fp_check.txt:L492` 汇总 `PASS=154 FAIL/异常=0 比对件数=154`、`L493` 结论「本任务全过程未修改任何既有件（在所测 154 件范围内）」；另 `_enum_batch1_stdout.txt:L0320-L0334` 与 DISPOSITION.md §9 已登记指纹逐条比对，13 条中 12 条匹配，唯一不匹配项是 DISPOSITION.md 自登记行 `L233`（见 STEP 1.3）。
3. **既有件历史覆盖事实（如实登记，非本轮所为）**：`CHAIN_SYNTHESIS.md:L11-L28` 与 `_WRITE_BOUNDARY_RULE.md:L3-L13` 记载，上一轮复跑探针曾把输出写回 7 处只读既有目录，物理 mtime 被更新、内容哈希与原件一致；本轮 `_enum_batch1_stdout.txt:L0095-L0113` 显示的 21:15–21:18 mtime 与该记载对应。本轮不据此推断「原件从未被写过」，只以哈希比对证明**本轮**零改动。
4. **未验项清单（拿不到证据即写未验，不补造）**：
   - 未验 1：0x0084F2BA 崩溃性质（DEP / 取指 / 数据访问）— 缺崩溃现场寄存器上下文、MiniDump、栈回溯（`DISPOSITION.md:L252-L256`、`CHAIN_SYNTHESIS.md:L143-L145`）。
   - 未验 2：引擎运行期 HouseClass 实例数及其驱动机制（遭遇战 4 vs 战役 14）— 缺 `0x4F54A0` 动态调用拦截日志（`CHAIN_SYNTHESIS.md:L146-L148`；`_ps_disasm_out.txt:L1271-L1280` 自列断点计划）。
   - 未验 3：PercentBuilt 全镜像间接读点（基类指针别名 / 虚表回调 / 动态偏移）完备性 — 缺全量间接读点普查表与计数（`DISPOSITION.md:L266-L268`、`CHAIN_SYNTHESIS.md:L149-L151`）。
   - 未验 4：「哪份地图字节被游戏实载」及 `93c2974b` 指纹算法与归属 — 缺加载轨迹/文件打开日志与指纹算法说明（`_ld_diff_out.txt:L97,L103`；`CHAIN_SYNTHESIS.md:L152-L154`）。
   - 未验 5：本文所有结论对其它 gamemd.exe 版本、其它地图、其它时点的普适性 — 缺跨版本镜像对照扫描与历史快照链；单图/单镜像读数不升格为跨图机制。
   - 未验 6：DISPOSITION.md §1「6 轮静态逆向成果」中第 6 轮所指 — 材料未点名（`DISPOSITION.md:L18` vs `L21`、`L167`、`L250`）。
   - 未验 7：本轮未实跑 5 个探针脚本；「清单来自实跑」仅指枚举/指纹脚本 `_enum_batch1.py` 的实跑，探针输出的可复现性依赖既有件 `CHAIN_SYNTHESIS.md:L44`、`_compare_repro_out.txt:L49`（MATCH=14 / MISMATCH=0）的记载，本轮未独立复跑验证。
5. **口径冲突登记（不择一、不改写）**：
   - `DISPOSITION.md:L21,L149-L153` / `DISPOSITION.csv:L140,L148` 的机制化措辞 vs 附录 X `L247-L272` 与 `CHAIN_SYNTHESIS.md:L74,L76,L84` 的降级结论 — 本文按后者，并在各轮「冲突/降级」列明。
   - `_cw_disasm_out.json:L38` 的旧 DEP verdict vs 附录 X.1 — 如实登记，不修改既有件。
   - `CHAIN_SYNTHESIS.md:L80` 的 `93c2974b` 归属表述 vs `_ld_diff_out.txt:L97,L103` 的「未匹配/未破解」 — 如实登记，标未证。
   - `DISPOSITION.md:L233` 自登记指纹 vs 当前实算字节 — 如实登记，不用于零改动证明。
6. **Top-10 口径差异**：CSV 无 Top-10 排名清单（185 行全量表），「第一批」8 行 vs MD Top-10 第一批 5 行，详见 STEP 1.3；本文未擅自择一，按 MD §5/§6 明示的 5 轮执行并把差异全部列出。

---

## 收尾回执

- **改了哪些文件（全部为写域内新建，既有件零改动）**：
  1. `lead/re_round_batch1_20261111/ROUND_BATCH1.md`（主交付，本文）
  2. `lead/re_round_batch1_20261111/_enum_batch1.py`（只读枚举 + hashlib 指纹脚本）
  3. `lead/re_round_batch1_20261111/_enum_batch1_stdout.txt`（BASELINE 实跑 stdout 同步落盘，336 行）
  4. `lead/re_round_batch1_20261111/_fp_baseline.json`（首跑指纹基线，脚本产出）
  5. `lead/re_round_batch1_20261111/_fp_verify.flag`（触发 VERIFY 模式的标记文件）
  6. `lead/re_round_batch1_20261111/_fp_check.txt`（复跑：前后指纹逐件 PASS/FAIL 比对，既有件零改动证明）
  7. `lead/re_round_batch1_20261111/_enum_batch1_stdout_run2.txt`（VERIFY 实跑 stdout 同步落盘）
- **跑了哪些命令**（全部为 `python -I -X utf8 <绝对路径>` 形式，绝对路径恒为 `D:\Project\ra2-campaign-forge\lead\re_round_batch1_20261111\_enum_batch1.py`）：
  1. `python -I -X utf8 <绝对路径>` — 首跑，**失败**：CSV 带 UTF-8 BOM，`csv.DictReader` 抛 `KeyError: '目录名'`（exit code 1，未落盘任何文件）；随后只读编辑本写域内新建的 `_enum_batch1.py`，把 CSV 读取改为 `utf-8-sig`。
  2. `python -I -X utf8 <绝对路径>` — BASELINE 成功（写 `_fp_baseline.json`、`_enum_batch1_stdout.txt`）。
  3. 二次只读编辑 `_enum_batch1.py`（调整 stdout/落盘一致性、把模式判定改为 `_fp_verify.flag` 触发）；随后复合 pwsh 命令内两次同一 python 调用：`python -I -X utf8 <绝对路径> | Select-Object -First 12` 与 `python -I -X utf8 <绝对路径> | Select-Object -Last 6` — 两跑均 BASELINE，按最终脚本重新生成上面两个脚本产出物（头 12 行 / 尾 6 行仅用于抽查，完整 stdout 以 `_enum_batch1_stdout.txt` 为准，336 行）。
  4. 新建 `_fp_verify.flag` 后执行 `python -I -X utf8 <绝对路径> | Select-Object -Last 12` — VERIFY 成功，产出 `_fp_check.txt`（493 行）与 `_enum_batch1_stdout_run2.txt`，末 12 行显示 `PASS=154 FAIL/异常=0`。
  - 其余取证全部为只读 `read` / `glob` / `grep` 工具调用，未执行任何 python 探针、未执行 git 命令、未启动任何游戏或加载器进程。
- **结论一句话**：Top-10 中第一批 5 个静态逆向轮共固化 20 条定级结论（11 条【已证（字节级）】、3 条【已证（CFG）】、6 条【未证】），其读数被 `re_chain_synthesis_20261111` 全量复现复用、机制结论已被附录 X 与该后续件降级，5 轮均可按「只含已证读数」的可入账摘要入账。
- **遗留未验项**：见「边界与未验」第 4 条 7 项（崩溃性质、运行期 House 实例数、PercentBuilt 间接读点、实载归因与 93c2974b、跨图普适性、「6 轮」所指、探针本轮未独立复跑）+ 第 5 条 4 处口径冲突。
