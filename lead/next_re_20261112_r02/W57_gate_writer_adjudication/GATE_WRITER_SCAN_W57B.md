# GATE_WRITER_SCAN · W57b · `0xA8F7AD` 静态写入者判定

> **本文件是 W57b（W57 重派）的独立交付。** 同目录的 `GATE_WRITER_SCAN.md` 可能被前实例 W57
> 的延迟产出覆盖；若有歧义，**以本文件（`GATE_WRITER_SCAN_W57B.md`）为准**。
> W57b：模型 `Hy4`，22:50 起，时间盒 70 min，纯离线只读。
> 目标 `ra2bench\gamemd.exe` 4,825,360 B，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（已知前缀 `73201cc0…` 一致）。
> 纪律：**I launched 0 / attached 0**；观察到的 `gamemd` 属其他卡、未触碰；未取 `.game_instance.lock`；未读活进程内存；只写本卡目录；`git` 只读（本卡未执行任何 `git` 命令）。

## 0 · 结论（三选一，严格）

**② 不存在 —— 但这是「有边界的否定」，不是全称否定。**

`[本次实测]` 在**本镜像的静态代码**、在 §4 所列**已覆盖形态**内，`.data` 字节 `0xA8F7AD` **没有任何静态写入者**：

- 全 `.text` 1,394,120 条线性指令边界（覆盖 99.9984%）+ 66 个未覆盖字节逐一 anchored 复核；
- 135,330 个内存写操作数（绝对 18,705 / `[reg+disp]` 116,625）；
- W56 的 773 个页窗口候选逐条指令边界分类，**0 条 `write` 覆盖 gate**；
- 37 条「绝对写 disp 落在门控页 `0xA8F700–0xA8F7FF`」逐条核 `[disp, disp+w-1]`，**0 条覆盖 `0xA8F7AD`**；
- 3,268 个 `rep stos/movs` 批量写点按 EDI/ECX/DF 求范围，**0 条覆盖 gate**；
- 独立全字节 anchored superset（4,005,210 次解码）复核：`DETERMINATE gate hits: 0`。

`[静态推断]` 唯一以 gate 为操作数的静态指令是 VA `0x52F00B` 的 `A0 AD F7 A8 00` = `mov al, byte ptr [0xa8f7ad]`，是**读**。

**红线限定**：本结论**不是**「我扫的形态 0 命中 ⇒ 不存在」那种推理。§5 逐项列出未覆盖形态；把它们计入后，「不存在任何写入者」这一**全称命题无法判定**（等价于 ③ 的边界）。本卡给的是**受 §4 覆盖矩阵约束的 ②**。若 Lead 要求无边界的全称结论，应按 ③ 读。

> 时间盒备注：第二层在 22:58（开始后约 11 分钟）即 `exit 0` 完成，远早于 35 分钟检查点，未触发「先交第一层 + 第二层进度」降级；第一层、探针、批量写专项、全量交叉验证均完整落盘。

## 1 · 承重的先行事实（`[转引]`，不重做、不当成果）

| 事实 | 来源 |
|---|---|
| `0xA8F7AD` 以绝对 VA 操作数形式全镜像 **1 次**，文件偏移 `0x12F00C`，即 VA `0x52F00B` 处 `A0` 读指令的操作数 | `lead\next_re_20261112_r02\REVIEW\LEAD_CHECK_gate_byte.md` |
| RVA `0x68F7AD` 与页内相对 `0x27D7AD` 形式均 **0 命中** | 同上 |
| 相邻字节 `0xA8F7AC` 绝对 VA **1 次**（文件偏移 `0x2BE030` → VA `0x6BE02F` 读） | 同上 |
| W56 报 `.text` **740** 个「页窗口候选」（宽匹配，非精确匹配） | `W56_gate_writer_scan\EVIDENCE\w56_scan1_stdout.txt` / `w56_scan2_stdout.txt` |

`[本次实测·交叉验证，非成果]` 第一层 PRECISE 两行复算：`0x0052F00B: a0adf7a800 mov al, byte ptr [0xa8f7ad]`（cat=read）、`0x006BE02F: a0acf7a800 mov al, byte ptr [0xa8f7ac]`（cat=read），与 Lead 一致。**本卡成果是 §3/§4 的「绝对形式之外」形态，不是把这些重扫一遍。**

## 2 · 本次新增的结构事实

`[本次实测]`（`EVIDENCE\w57b_scan_stdout.txt`）：ImageBase `0x400000`；`.text` RVA `0x1000` / RawSize `0x3E0000` / chars `0x60000020`（CODE|EXEC|READ，**不含 WRITE**）；`.data` VA `0x812000` / VSize `0x367BE4` / RawSize `0x6C000`；`.detour` VA `0xB93000` / RawSize `0x3000`。

`[本次实测]` gate RVA `0x68F7AD` 相对 `.data` 起点偏移 `0x27D7AD` = 2,602,925 B > RawSize `0x6C000` ⇒ **`0xA8F7AD` 落在 `.data` 的 BSS（未初始化）区，磁盘上无对应字节**（`va_to_off` 返回 `None`），由加载器零填充。这正是 Lead 表中「页内相对 `0x27D7AD`」的来历，也解释了零售态恒 0。

## 3 · 第一层：W56 候选的指令边界解码分类

**方法**（`[本次读码]`+`[本次实测]`，`EVIDENCE\w57b_layer1.py`）：
1. 逐行过滤 `w56_scan1_stdout.txt`（4,301 行）/ `w56_scan2_stdout.txt`（2,307 行）的 `CAND`/`FOFF` 行，**先抽出候选表** `EVIDENCE\w57b_w56_candidates_raw.tsv`：**773 个唯一候选**（`.text 740 / .rdata 14 / .data 19`），与 W56 报数一致；未整读 358 KB 到分析里。
2. 每个候选 `(FOFF i, LE32 v)`：对 `s ∈ [i-15, i]` 用 capstone `md.disasm(RAW[s:s+16], IB+s, count=1)` 解码一条指令，要求 `s+size ≥ i+4` 且 `encoding.disp_offset/imm_offset` 精确起始于 `i`（disp32/imm32/rel32 字段），且存在 MEM/IMM 操作数等于 `v`；以 1,394,120 个线性扫描起点标注 `sweep-start` / `off-path`。
3. 分类 `read` / `write` / `address-taken` / `immediate` / `false-positive`，**逐条**写依据（解码起点、边界、字段、操作数访问位、宽度、是否覆盖 gate、上下文 hex）。

**产出** `candidates_classified.tsv`：**773 行，逐条**，列含 `VA / 反汇编文本 / 类别 / 依据`（另附 FOFF/LE32/tags/section/ins_VA/边界/字段便于机检）。

`[本次实测]` 类别计数：`false-positive 99 / immediate 5 / write 215 / read 380 / address-taken 74`；**`WRITE rows covering GATE_VA: 0`**。
`[本次读码+实测·参考性交叉验证]` 前实例遗留 `EVIDENCE\w57_scan.py`（本卡 22:51 前逐行复核，当时 40,129 B / 879 行）重跑 `classify`：`740` 行、`fp 72 / imm 4 / write 211 / read 379 / at 74`、`gate_write rows (yes/unknown) = 2`（均 `unknown`＝基址相对写，无静态确定地址）。**版本漂移**：该文件 22:51:55 被并发进程改写为 41,809 B（§8），运行时版本与读码版本非同一字节；其 stdout 与读码所见逻辑一致，但**仅作参考性交叉验证，本卡结论完全由 `w57b_*` 独立脚本支撑**。差异见 `DISAGREE_W57B.md`，决定性结论一致。

## 4 · 第二层：基址相对写入普查 + 覆盖矩阵

### 4.1 方法（`EVIDENCE\w57b_layer2.py`）

`[本次实测]` 分块线性 detail 扫描 `.text`（无效字节 1 字节重启）：**1,394,120 条 / 覆盖 4,063,166 of 4,063,232 B = 99.9984% / 65 次重启**；66 个未覆盖字节逐个 anchored 单指令复核，**0 个写形式命中**。

- 全量普查 `mov/movzx/or/and/add/sub/inc/dec/xor`（及完整 store 集合，含 capstone 对 x87/SSE store 报 READ 的修正）对 `byte ptr [reg+disp8]` 与 `[reg+disp32]` 的写入，记录 base / index / disp / `disp_size` / 宽度。
- 卡字面筛选 `disp ∈ [0xA8F700, 0xA8F800)`；另加宽 `base 常量 ∈ [0xA8F000,0xA90000)`、`eff 覆盖 gate`、`disp 在宽带但不在门控页` 的 near-miss 对照，确保主表**逐条**而非只给汇总数。
- 前向常量传播（8 GPR：`mov/lea/xor/sub/add/pop/call-clobber/ret-reset`）+ 320 B 局部回溯（`mov reg,imm32` / `lea reg,[imm]` / `xor reg,reg` / 内存装载 / `pop` / 无定义＝函数入参）。
- 三分类 `可能可达 / 不可达 / 无法判定`，**逐条给理由**。

### 4.2 普查数字（`[本次实测]`）

| 项 | 值 |
|---|---:|
| 内存写操作数 | 135,330 |
| 绝对 `[disp]` 写 | 18,705 |
| `[reg+disp]` 写 | 116,625 |
| `disp_size` = 0 / 1(disp8) / 4(disp32) | 19,443 / 78,717 / 37,168 |
| 宽度 = 1 / 2 / 4 / 8 / 10 / 28 | 20,460 / 9,646 / 100,083 / 5,002 / 137 / 2 |
| 卡指定 mnemonic 写 | mov 119,516 / add 3,689 / or 468 / inc 400 / and 292 / dec 296 / sub 141 / xor 29 |
| **绝对写覆盖 gate** | **0** |
| 门控页内绝对写 | 37 |
| `mov reg, imm32` 常量落在门控页 | 6 |
| 批量写点（专项 2b） | 3,268（覆盖 gate **0**） |

### 4.3 决定性发现：绝对形式之外的形态

`[本次实测]`（`EVIDENCE\w57b_probe_gatepage_stdout.txt` **P1**）37 条绝对写 disp 落在 `0xA8F700–0xA8F7FF`，逐条核 `[disp, disp+w-1]`：

- 密集写 `0xA8F7A0..A3`、`0xA8F7A4..A7`、`0xA8F7A8..AB`、`0xA8F7B0..B3`、`0xA8F7F0..F3` 等（如 `0x0052DF5F: mov dword ptr [0xa8f7a8], ebx` 覆盖 `0xA8F7A8–0xA8F7AB`）；
- **`0xA8F7AC–0xA8F7AF` 这一 dword 没有任何写者**，`0xA8F7AD` 恰在这个「洞」里；
- 37 条中 **0 条**字节范围覆盖 `0xA8F7AD`。

⇒ 这补上了 Lead 精确值扫描（只查 `0xA8F7AD` 这个 dword 本身）**没覆盖**的「页内相邻地址 + 宽度>1 写」形态，且结论仍为 0。这是本卡最有力的一条新证据。

`[本次实测]` `baserel_writes.tsv` **4 行，逐条含理由**：

| VA | 指令 | 类别 | 理由 |
|---|---|---|---|
| `0x00531E77` | `mov byte ptr [esi + 0xa8f7b8], al` | 不可达 | `xor esi,esi`（`0x531E65`）清零 ⇒ eff `0xA8F7B8`，宽 1 |
| `0x00531EC8` | `rep stosd dword ptr es:[edi], eax` | 不可达 | 2b 专项：EDI=`0xA8F7B8`，ECX=8，DF=0 ⇒ 范围 `[0xA8F7B8..0xA8F7D7]` |
| `0x00531F3E` | `rep stosd dword ptr es:[edi], eax` | 不可达 | 同上 |
| `0x007E0369` | `mov byte ptr [edi + 0xa8f91c], al` | 无法判定 | EDI 来自 `mov edi, [ebp-0x10]`（栈局部变量），值静态不可界定；disp 在宽带但不在门控页 |

> 主表两行 `rep stosd` 的「依据」列按单次操作数宽度给出；完整批量写范围论证见 `EVIDENCE\w57b_bulk_store.tsv`，类别经其复核确认不变。

`[本次实测]` 2b 专项（`EVIDENCE\w57b_bulk_store.py` / `.tsv`）：3,268 行逐条，`无法判定 3,043`（EDI/ECX/DF 至少一个不可静态界定）、`不可达 225`、**覆盖 gate 0**；两处 EDI 常量在 `.data` 页窗口的 `rep stosd` 范围 `[0xA8F7B8..0xA8F7D7]`，不含 `0xA8F7AD`。`.text` 中 `cld` 28 处 / `std` 27 处，两处 `rep stosd` 之前无 `std`（且前接 `repne scasb` 递增扫描），DF=0 判定可靠。

`[本次实测]` 门控页内地址常量装载 6 处（`EVIDENCE\w57b_layer2_base_loads.tsv`）：`mov edi, 0xA8F7B8`（`0x531E4C`、`0x531EA9`、`0x531F39`）、`push 0xA8F7B8`（`0x531E87`）、`mov ecx, 0xA8F7F8`（`0x538C14`、`0x632C0F`）。**均不是 `0xA8F7AD`，也不指向覆盖它的范围**。

### 4.4 覆盖矩阵

| 形态 | 覆盖 | 结果 | 证据路径 |
|---|---|---|---|
| 绝对 VA `0xA8F7AD` 精确值 | `[转引]` Lead + 本次交叉验证 | 1 次，读 | `REVIEW\LEAD_CHECK_gate_byte.md`；L1 PRECISE 行 |
| RVA / 页内相对精确值 | `[转引]` Lead | 0 | 同上 |
| W56 页窗口候选的指令边界分类 | ✅ 本次 | 773 行逐条；0 `write` 覆盖 gate | `candidates_classified.tsv` |
| 绝对 `[disp]` 写 + 宽度>1 覆盖 gate | ✅ **本次新增** | 37 条门控页内绝对写，0 覆盖 | `EVIDENCE\w57b_probe_gatepage_stdout.txt` P1 |
| `[reg+disp8]` / `[reg+disp32]` 写 | ✅ 本次 | 116,625 普查；4 条筛后逐条三分类 | `baserel_writes.tsv` |
| 基址常量装载 `mov/lea reg,imm` | ✅ 本次 | 门控页 6 处，均不落 gate | `EVIDENCE\w57b_layer2_base_loads.tsv` |
| 前向常量传播 + 320 B 回溯 | ✅ 本次 | 逐条理由 | `baserel_writes.tsv` |
| `rep stos/movs` 批量写范围 | ✅ **本次新增** | 3,268 点，0 覆盖 gate | `EVIDENCE\w57b_bulk_store.tsv` |
| 线性扫描未覆盖字节 | ✅ 本次 | 66 B anchored 复核，0 写命中 | `EVIDENCE\w57b_layer2_stdout.txt` |
| 全字节 anchored superset（4M 次解码） | ✅ `[本次读码+实测]` 独立复核 | 37 条页内绝对写；`DETERMINATE gate hits: 0` | `EVIDENCE\w57_prior_regbase_stdout.txt` |
| 间接跳转表 / 虚调用 | ❌ | 未覆盖 | §5.1 |
| 自修改代码 | ❌ | 未覆盖 | §5.2 |
| 外部 `ddraw.dll` / 其它模块 | ❌ | 未覆盖 | §5.3 |
| `.detour` 段语义 | ❌ | 未做完整分析 | §5.4 |
| 运行期 `WriteProcessMemory` | ❌ | 未覆盖 | §5.5 |
| 函数入参/全局指针承载的写 | ⚠️ 部分 | 3,043 点判「无法判定」，未证明不可达 | §5.6 |

## 5 · 未覆盖形态（`[静态推断]`，红线：必须列）

1. **间接跳转表 / 虚调用**：`jmp/call dword ptr [reg*4+table]`、`call dword ptr [IAT]`（探针中 `0x00531F18: call dword ptr [0x7e10d4]`）目标运行时才定，被调函数体内可能有写。
2. **自修改代码（SMC）**：`.text` 节属性不含 WRITE，但运行期 `VirtualProtect` 后改写自身代码产生的写指令不在静态字节里。
3. **外部 `ddraw.dll`**：外部模块（ddraw.dll 及其它 DLL、注入模块）在自己的代码里写本进程 `.data`；本卡**只读 `gamemd.exe` 镜像**，未扫描任何外部模块。
4. **`.detour` 段**：VA `0xB93000` / RawSize `0x3000` / chars `0xC0000040`（可写）。W56 报该段 0 候选；本卡未对其做完整指令解码与执行语义分析，运行期 hook 代码可能在此写 `.data`。
5. **运行期 `WriteProcessMemory` / 外部进程注入**：调试器、外挂、patcher、其它卡的运行期实验对本进程 `.data` 的写入。
6. **函数入参 / 全局指针承载的 `[reg+disp]` 写**：2b 专项 3,043 个批量写点与 `0x7E0369` 判「无法判定」——值来自栈局部变量、堆、全局或跨基本块数据流。它们**未被证明不可达**，只是未被证明可达；这是静态分析的内生边界，不是「0 命中」。
7. **DF=1 路径 / 运行期方向标志**：2b 用 x86-32 ABI 默认 DF=0 + 显式 `cld`/`std` 追踪；若某调用返回前未恢复 DF，批量写范围可能反向。
8. **运行期 BSS 初始化 / 指针表驱动的间接循环**：BSS 由加载器零填充；游戏 CRT/初始化代码若通过指针表循环写整片 `.data`，可能扫过 gate。本卡覆盖静态 `rep stos/movs`，未覆盖指针表驱动的间接循环。
9. **其它段的数据驱动写**：`.rdata`/`.data`/`.rsrc`/导入表中的函数指针、跳转表、配置数据在运行时被解引用成写地址。
10. **off-path 解码 / 运行期生成指令**：线性扫描 99.9984% + 66 B anchored 复核 + 4M 次全字节 anchored superset，仍不能保证覆盖所有非对齐/动态生成的指令流。

`[待运行验证]` 上述 1–10 的排除需要运行期观测（断点/内存断点/`VirtualProtect` 监控/模块枚举/进程间写监控），**本卡纪律禁止且未执行**。

## 6 · 证据与复现

所有本卡脚本在 `EVIDENCE\` 且为 `w57b_*` 前缀，每个脚本有 `<name>_stdout.txt` / `<name>_stderr.txt` / `<name>_exitcode.txt`：

| 脚本 | 作用 | exit |
|---|---|---:|
| `w57b_scan.py` | 第一步骨架：PE/VA↔off 映射、SHA-256、capstone 自检 | 0 |
| `w57b_layer1.py` | 第一层：W56 CAND 行抽取 + 指令边界分类 | 0 |
| `w57b_layer2.py` | 第二层：线性 detail 全普查 + 常量传播 + 回溯 | 0 |
| `w57b_probe_gatepage.py` | 门控页探针：37 条绝对写 / 6 处常量 / 反汇编窗口 / DF 统计 | 0 |
| `w57b_bulk_store.py` | 2b：`rep stos/movs` 范围普查 | 0 |
| `w57_scan.py`（前实例遗留，参考性交叉验证，见 §8） | `env`/`classify`/`regbase`，本卡输出命名为 `w57_prior_*` | 0 / 0 / 0 |

辅助表：`w57b_w56_candidates_raw.tsv`、`w57b_layer2_abs_writes.tsv`、`w57b_layer2_base_loads.tsv`、`w57b_layer2_census.tsv`、`w57b_bulk_store.tsv`、`w57_prior_classified.tsv`（前实例版备份）、`regbase_*.tsv`。
分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`。

## 7 · 纪律声明

- **I launched 0 / attached 0**；观察到的 `gamemd` 属其他卡、未触碰；**未取 `.game_instance.lock`**；未读活进程内存；未启动 `gamemd.exe`。
- 只写本卡目录 `W57_gate_writer_adjudication\`；未写 `ra2youli` / `ra2forge` / `ra2opt` / `ra2bench`；未动 `W21`–`W60`；`git` 只读（未执行任何 `git` 写操作，也未执行 `git` 命令）。
- 目标只读：`ra2bench\gamemd.exe`，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`。
- 工具：Python 3.12.10 + capstone 5.0.7；`pefile 2024.8.26` 仅用于前实例遗留脚本的交叉验证（本卡自己的脚本全部 stdlib + capstone，不依赖 pefile）。
- 未启用 REA MCP / 外部反汇编引擎：本会话未注册其工具，且卡限定 python + capstone 纯离线；REA 的「区分 observation / inference / unknown、保留 coverage 限制」原则已采纳进本文分级。
- `STARTED_W57B.txt`（ISO 时间戳 + `Hy4` + `W57b retry`）与 `HEARTBEAT.txt`（每阶段一行时间戳 + 阶段，含本卡 22:50–23:10 的 7 行）已落盘。

## 8 · 并发写入观察（诚实记录，影响验收）

`[本次实测]` 本卡工作期间（22:51:55–23:08:50），**另一个实例/进程**（自称 `W57` / `Hy4` / 时间盒 75 min，应为前实例延迟产出而非真正冻结）在同一 `EVIDENCE\` 内持续写入 `w57_*` 前缀文件：`w57_scan.py` 由 40,129 B 改写为 41,809 B，新增 `w57_targeted.py` 及 `w57_env/classify/regbase/targeted_*` 全套 stdout/exitcode/tsv。并于 23:07:34 / 23:08:05 / 23:08:50 **覆盖了 `GATE_WRITER_SCAN.md` / `UNKNOWNS.md` / `DISAGREE.md`**（当时这三份被写成 W57 版；本卡于 23:13 从 `*_W57B.md` 副本写回 W57b 版，当前为 W57b 版。W57 原版报告正文因此未留副本，但其全套 `EVIDENCE\w57_*` stdout/TSV 完整保留可重建；W57 另留 `COLLISION_NOTE.md` 说明归属，并确认两份独立分析结论同为 ②不存在）。`HEARTBEAT.txt` 中 3 行纯 UTC 记录（`14:32:12Z` / `14:50:01Z` / `14:57:12Z`）亦非本卡格式。

- 本卡**未触碰、未修改、未删除**这些 `w57_*` 文件；**观察到的其它实例/进程属其他卡、未触碰**。
- 本卡的**全部产物**是 `w57b_*` 脚本、5 份 `*_W57B.md` / 规定文件名文档、以及 `candidates_classified.tsv` / `baserel_writes.tsv`；§3/§4 的结论与逐条 TSV **不依赖** `w57_*` 文件。
- `candidates_classified.tsv`（773 数据行，本卡 23:02 写）与 `baserel_writes.tsv`（4 行，本卡 22:58 写）经复核仍是本卡版本（表头含 `反汇编文本 / 类别 / 依据 / 筛选来源`）。
- 版本漂移影响：`w57_scan.py` 于 22:51:55 被改写，故 §6「重跑前实例脚本」运行的是改写后版本，与 §3 里 22:51 前逐行读码的版本非同一字节 —— 已据此把前实例脚本降权为**参考性交叉验证**。

## 9 · 交付文件对照（防覆盖）

| 卡要求文件名 | W57b 独立副本（不可混淆） | 状态 |
|---|---|---|
| `GATE_WRITER_SCAN.md` | **`GATE_WRITER_SCAN_W57B.md`**（本文件） | 规定名可能被 W57 覆盖，以副本为准 |
| `UNKNOWNS.md` | **`UNKNOWNS_W57B.md`** | 同上 |
| `DISAGREE.md` | **`DISAGREE_W57B.md`** | 同上 |
| `candidates_classified.tsv` | — | 本卡版本（773 行） |
| `baserel_writes.tsv` | — | 本卡版本（4 行） |
| `EVIDENCE\`（脚本+stdout+退出码） | `w57b_*` 前缀 | 本卡版本，未被覆盖 |
