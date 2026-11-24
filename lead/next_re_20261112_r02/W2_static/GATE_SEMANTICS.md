# 四个门控字节的静态语义 — NEXT_RE_20261112_R02 / W2_static

**纯静态**：只读磁盘 PE 字节。未启动游戏、未 attach、未读活进程、未挂起线程、未注入。
真机只读观测由同轮另一代理负责；本文只给「真机该期待什么值」。

## 0. 镜像实测（开工前实算）

`[本次实测]` 命令与原始 stdout / 退出码见 `EVIDENCE/00_commands_and_exit.txt`、`EVIDENCE/00_run_log.txt`。

```
PATH   = D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe
SIZE   = 4825360 (0x49A110)
SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
期望     = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
结论     = 一致，允许开工
```

PE 事实复核 `[本次实测]`（`EVIDENCE/00_run_log.txt`）：

| 校验 | 项 | 值 |
|---|---|---|
| OK | SHA-256 | 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 |
| OK | file size | 0x49A110 (4825360) |
| OK | ImageBase | 0x400000 |
| OK | SizeOfImage | 0x796000 |
| OK | IMAGE_FILE_RELOCS_STRIPPED (COFF char bit0) | COFF=0x32F |
| OK | DYNAMIC_BASE == False | DllCharacteristics=0x20 |
| OK | .text file_off == RVA | RawPtr=0x1000 RVA=0x1000 |
| OK | .rsrc file_off == VA - 0x6FC000 | VA-RawPtr=0x6FC000 |
| OK | .detour file_off == VA - 0x6FC000 | VA-RawPtr=0x6FC000 |
| OK | G1 0x00A83D49 无文件 backing (BSS) | section=.data |
| OK | G2 0x00A8ECD0 无文件 backing (BSS) | section=.data |
| OK | G3 0x008B41C0 无文件 backing (BSS) | section=.data |
| OK | G4 0x00A83D48 无文件 backing (BSS) | section=.data |

> 注：`RELOCS_STRIPPED` 是 COFF `IMAGE_FILE_HEADER.Characteristics` bit0，不是 `DllCharacteristics`；本镜像 `DllCharacteristics=0x20`，`DYNAMIC_BASE`(0x40) 未置位。两者不矛盾。

**地址换算** `[本次读码]` `gate_semantics.py:PEImage.va_to_off/off_to_va`：`.text`/`.rdata`/`.data` 文件偏移 = RVA；`.rsrc`/`.detour` 文件偏移 = VA − 0x6FC000。四个门控 VA 全部落在 `.data` 的 **BSS 尾**（VA 0x812000..0xB79BE4，但 `.data` 只有 0x6C000 字节文件 backing，到 VA 0x87E000 为止），**磁盘上没有这些字节**，加载器零填充。因此「4 字节 VA 模式命中」必然是指令里的地址操作数 / 立即数 / 数据指针，不会是门控字节本身。

## 1. 方法与覆盖度

双通道 + 复扫交叉验证；全部原始输出在 `EVIDENCE/`。

| 通道 | 做法 | 输出 |
|---|---|---|
| A | 全文件 `[0x0, 0x49A110)` 共 4825360 字节做 4 字节小端 VA 搜索；每个命中向前 k=1..12 试指令起点，capstone 逐操作数 `access`/`size`/`type` 分类 | `02_pattern_hits_all.csv`, `03_channelA_decoded.txt` |
| B1 | 从 **0x90(≥4)/0xCC(≥2) 填充区间边界** 做确定性线性扫描（skipdata），记录 `uncovered_intervals` | `04_B1_linear.txt`, `05_uncovered_intervals.txt` |
| B2 | **第二可信边界复扫**：独立于 B1 的原始字节级 `E8 rel32` 目标（16 字节对齐）作为边界重扫 | `04_B2_rescan.txt`, `06_cross_validation.txt` |

支持编码清单见 `EVIDENCE/10_encoding_coverage.txt`（A0/A1/A2/A3、B0..B7、B8..BF、C6 05 / 66 C7 05 / C7 05、88/89/8A/8B（含 SIB 绝对地址）、80/81/83、FE/FF、F6/F7、0F B0/B1/C0/C1、8D、68、05/0D/25/2D/35/3D）。

**负控 `--selftest`** `[本次实测]`：合成字节流五类必须可分 → **PASS，5/5 可分**；仅前三类算写。见 `EVIDENCE/01_selftest.txt`。

**反例校验（0x8B41C0 低位地址污染）** `[本次实测]`：`B8 C0 41 8B 00` (`mov eax,0x8B41C0`)、`B9/BA`、`68 C0 41 8B 00` (`push`)、`05 ...` (`add eax,imm32`) 均被判为 `imm_coincidence` / `is_write=False`；`8D 35 ...` (`lea`) 判 `lea_addr`；`A0 ...` 判 `read8`。真实文件里的非写命中逐条列于 `EVIDENCE/09_counterexamples.txt`。结论：分类器**不会**把立即数巧合算成内存写。

**交叉验证** `[本次实测]`：A 写点=29，B1=29，B2=29，三通道交集=29，并集=29，A-only=0，B-only=0。明细 `EVIDENCE/06_cross_validation.txt`。

**扫描无命中说明 / 零命中 ≠ 运行期不存在**：本次搜索范围是**磁盘文件全部 4825360 字节**，只覆盖上列「指令里直接内嵌 4 字节绝对 VA」的编码。寄存器间接写（`mov reg,VA` 后 `mov byte [reg],1`）、通过结构体基址 + 偏移写、运行期自修改代码、以及加载器写入，都不会在写指令里内嵌该 VA。`EVIDENCE/12_indirect_pathways.txt` 做了前向 32 指令的寄存器间接写候选扫描，命中 0 条（全部 `[静态推断-弱]`）。本次**没有**对任何门控宣称「运行期不存在其他写者」。

**未覆盖区间** `[本次实测]`：B1 skipdata 区间 278 处、cover_bitmap 空隙 0 段；B2 skipdata 66 处、空隙 0 段。另有 FE 头、`.rdata`/`.data` 文件段、`.rsrc`/`.detour`、`.data` BSS 尾不做线性反汇编（只由通道 A 覆盖）。明细 `EVIDENCE/05_uncovered_intervals.txt`。

## 2. 写入点总表

`GATE_WRITERS.csv` 为权威清单。下表按门控分组（VA / RVA / FOFF / 字节 / 反汇编 / 基本块 / 前一条调用或条件分支 / 宽度 / RMW / 推定值 / 等级）。

[本次实测] 全部写点均来自 `python gate_semantics.py` 的字节解码输出（命令+stdout+退出码见 `EVIDENCE/00_commands_and_exit.txt`）；`kind` 末尾 `/A+B1+B2` 等标注了确认通道。

### G1 = 0x00A83D49 — 写点 9 处（置位 4 / 清零 5 / 其他 0）

| VA | RVA | FOFF | bytes | disasm | basic_block | prev_call_or_branch | width | RMW | 值 | grade |
|---|---|---|---|---|---|---|---|---|---|---|
| 0x004F867C | 0x000F867C | 0x000F867C | `c6 05 49 3d a8 00 01` | `mov byte ptr [0xa83d49], 1` | 0x004F867C | 0x004F867A \\| je 0x4f86f7 | 1B | false | SET1 | [本次实测] |
| 0x004F8692 | 0x000F8692 | 0x000F8692 | `c6 05 49 3d a8 00 01` | `mov byte ptr [0xa83d49], 1` | 0x004F8692 | 0x004F8690 \\| je 0x4f869b | 1B | false | SET1 | [本次实测] |
| 0x004F86EE | 0x000F86EE | 0x000F86EE | `c6 05 49 3d a8 00 01` | `mov byte ptr [0xa83d49], 1` | 0x004F86EE | 0x004F86EC \\| je 0x4f86f7 | 1B | false | SET1 | [本次实测] |
| 0x004F87BB | 0x000F87BB | 0x000F87BB | `c6 05 49 3d a8 00 01` | `mov byte ptr [0xa83d49], 1` | 0x004F87BB | 0x004F87B0 \\| je 0x4f87bb | 1B | false | SET1 | [本次实测] |
| 0x0052DA78 | 0x0012DA78 | 0x0012DA78 | `c6 05 49 3d a8 00 00` | `mov byte ptr [0xa83d49], 0` | 0x0052DA56 | 0x0052DA49 \\| jge 0x52da4f | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D129 | 0x0015D129 | 0x0015D129 | `88 1d 49 3d a8 00` | `mov byte ptr [0xa83d49], bl` | 0x0055D123 | 0x0055D11E \\| call 0x6c6f50 | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D1B1 | 0x0015D1B1 | 0x0015D1B1 | `88 1d 49 3d a8 00` | `mov byte ptr [0xa83d49], bl` | 0x0055D1B1 | 0x0055D1AC \\| call 0x6c6f50 | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D219 | 0x0015D219 | 0x0015D219 | `88 1d 49 3d a8 00` | `mov byte ptr [0xa83d49], bl` | 0x0055D214 | 0x0055D212 \\| je 0x55d250 | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D25C | 0x0015D25C | 0x0015D25C | `88 1d 49 3d a8 00` | `mov byte ptr [0xa83d49], bl` | 0x0055D25C | 0x0055D256 \\| je 0x55d341 | 1B | false | CLEAR0 | [本次实测] |


### G2 = 0x00A8ECD0 — 写点 8 处（置位 3 / 清零 5 / 其他 0）

| VA | RVA | FOFF | bytes | disasm | basic_block | prev_call_or_branch | width | RMW | 值 | grade |
|---|---|---|---|---|---|---|---|---|---|---|
| 0x004F86F7 | 0x000F86F7 | 0x000F86F7 | `c6 05 d0 ec a8 00 01` | `mov byte ptr [0xa8ecd0], 1` | 0x004F86F7 | 0x004F86EC \\| je 0x4f86f7 | 1B | false | SET1 | [本次实测] |
| 0x004F879C | 0x000F879C | 0x000F879C | `c6 05 d0 ec a8 00 01` | `mov byte ptr [0xa8ecd0], 1` | 0x004F879C | 0x004F879A \\| je 0x4f87bb | 1B | false | SET1 | [本次实测] |
| 0x004F87B2 | 0x000F87B2 | 0x000F87B2 | `c6 05 d0 ec a8 00 01` | `mov byte ptr [0xa8ecd0], 1` | 0x004F87B2 | 0x004F87B0 \\| je 0x4f87bb | 1B | false | SET1 | [本次实测] |
| 0x0052DA7F | 0x0012DA7F | 0x0012DA7F | `c6 05 d0 ec a8 00 00` | `mov byte ptr [0xa8ecd0], 0` | 0x0052DA56 | 0x0052DA49 \\| jge 0x52da4f | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D123 | 0x0015D123 | 0x0015D123 | `88 1d d0 ec a8 00` | `mov byte ptr [0xa8ecd0], bl` | 0x0055D123 | 0x0055D11E \\| call 0x6c6f50 | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D1B7 | 0x0015D1B7 | 0x0015D1B7 | `88 1d d0 ec a8 00` | `mov byte ptr [0xa8ecd0], bl` | 0x0055D1B1 | 0x0055D1AC \\| call 0x6c6f50 | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D21F | 0x0015D21F | 0x0015D21F | `88 1d d0 ec a8 00` | `mov byte ptr [0xa8ecd0], bl` | 0x0055D214 | 0x0055D212 \\| je 0x55d250 | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D262 | 0x0015D262 | 0x0015D262 | `88 1d d0 ec a8 00` | `mov byte ptr [0xa8ecd0], bl` | 0x0055D25C | 0x0055D256 \\| je 0x55d341 | 1B | false | CLEAR0 | [本次实测] |


### G3 = 0x008B41C0 — 写点 6 处（置位 1 / 清零 5 / 其他 0）

| VA | RVA | FOFF | bytes | disasm | basic_block | prev_call_or_branch | width | RMW | 值 | grade |
|---|---|---|---|---|---|---|---|---|---|---|
| 0x0048CB2E | 0x0008CB2E | 0x0008CB2E | `c6 05 c0 41 8b 00 01` | `mov byte ptr [0x8b41c0], 1` | 0x0048CB2E | 0x0048CAF4 \\| call dword ptr [0x7e1530] | 1B | false | SET1 | [本次实测] |
| 0x0052DA86 | 0x0012DA86 | 0x0012DA86 | `c6 05 c0 41 8b 00 00` | `mov byte ptr [0x8b41c0], 0` | 0x0052DA56 | 0x0052DA49 \\| jge 0x52da4f | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D12F | 0x0015D12F | 0x0015D12F | `88 1d c0 41 8b 00` | `mov byte ptr [0x8b41c0], bl` | 0x0055D123 | 0x0055D11E \\| call 0x6c6f50 | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D1BD | 0x0015D1BD | 0x0015D1BD | `88 1d c0 41 8b 00` | `mov byte ptr [0x8b41c0], bl` | 0x0055D1B1 | 0x0055D1AC \\| call 0x6c6f50 | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D225 | 0x0015D225 | 0x0015D225 | `88 1d c0 41 8b 00` | `mov byte ptr [0x8b41c0], bl` | 0x0055D214 | 0x0055D212 \\| je 0x55d250 | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D268 | 0x0015D268 | 0x0015D268 | `88 1d c0 41 8b 00` | `mov byte ptr [0x8b41c0], bl` | 0x0055D25C | 0x0055D256 \\| je 0x55d341 | 1B | false | CLEAR0 | [本次实测] |


### G4 = 0x00A83D48 — 写点 6 处（置位 1 / 清零 5 / 其他 0）

| VA | RVA | FOFF | bytes | disasm | basic_block | prev_call_or_branch | width | RMW | 值 | grade |
|---|---|---|---|---|---|---|---|---|---|---|
| 0x004C7917 | 0x000C7917 | 0x000C7917 | `c6 05 48 3d a8 00 01` | `mov byte ptr [0xa83d48], 1` | 0x004C7903 | 0x004C790F \\| call 0x4068e0 | 1B | false | SET1 | [本次实测] |
| 0x0052DA8D | 0x0012DA8D | 0x0012DA8D | `c6 05 48 3d a8 00 00` | `mov byte ptr [0xa83d48], 0` | 0x0052DA56 | 0x0052DA49 \\| jge 0x52da4f | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D135 | 0x0015D135 | 0x0015D135 | `88 1d 48 3d a8 00` | `mov byte ptr [0xa83d48], bl` | 0x0055D123 | 0x0055D11E \\| call 0x6c6f50 | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D1C3 | 0x0015D1C3 | 0x0015D1C3 | `88 1d 48 3d a8 00` | `mov byte ptr [0xa83d48], bl` | 0x0055D1B1 | 0x0055D1AC \\| call 0x6c6f50 | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D22B | 0x0015D22B | 0x0015D22B | `88 1d 48 3d a8 00` | `mov byte ptr [0xa83d48], bl` | 0x0055D214 | 0x0055D212 \\| je 0x55d250 | 1B | false | CLEAR0 | [本次实测] |
| 0x0055D26E | 0x0015D26E | 0x0015D26E | `88 1d 48 3d a8 00` | `mov byte ptr [0xa83d48], bl` | 0x0055D25C | 0x0055D256 \\| je 0x55d341 | 1B | false | CLEAR0 | [本次实测] |


## 3. 语义判定（分档）

等级严格使用 `[静态推断-强]` / `[静态推断-弱]` / `[待运行验证]`；「我猜它是暂停」不写成已证。

### 共同事实 `[本次读码]`

- `0x55DE4F..0x55DE81` 四门控**串联 `test al,al` + `jne 0x55DEC8`**：任一非 0 ⇒ 跳到 0x55DEC8 清 `[0xABCD58]=0` 后返回，**不推进帧计数**（`EVIDENCE/07_context.txt`、`GATE_DECODE.txt` 复核一致）。
- 四门控在 `0x52DA78/7F/86/8D` 被**一次性同时写 0**，紧接着 `0x52DA94..0x52DAD1` 大量全局归零；同函数 `0x52DA08` 把帧计数 `0xA8ED84` 归零。这是**场景/对局初始化路径** `[静态推断-强]`。
- 四门控在 `0x55D123/129/12F/135`、`0x55D1B1/B7/BD/C3`、`0x55D219/21F/225/22B`、`0x55D25C/262/268/26E` 被**成组清 0**，每组后面跟随 `call 0x72DFB0`、`0x69BB40`、`0x685670/0x685DC0/0x6863E0/0x686570`、`0x69BAB0` 和 `mov byte [0xABCD58],bl`。这是**「门控被消费后的恢复路径」** `[静态推断-强]`：门控是「挂起请求」标志，处理完即全部清零。
- `0xA8B238` 是模式枚举（0 / 3 / 4 / 5）；`0x55D3A0` 附近对模式 0/5 用 `Sleep(500)`、其他用 `Sleep(10)`；`0x55D3BB` 起把帧计数与 `[0xA8E2E4]` 比较、`timeGetTime`。`0xA8E9A0` 为「循环活动」标志（`0x55D371 je 0x55DECF` 直接返回）。
- `0x82637C` = `"Loaded recording values for scenario : %s\n"`（在 `0x52DC17` 被 printf 引用）；`0x82A044` = `"Disconnect_Gracefully\n"`（在 `0x55D298` 被引用）；`0x831A60` = `"Pregame setup for %d players.\n"`；`0x820E0C` = `"Processing EXIT event on frame %d\n"`（在 `0x4C790A` 作为 printf 格式串、实参为 `[0xA8ED84]` 帧号，紧邻 G4 置位点）。`[本次读码] EVIDENCE/08_imports_strings.txt`。

### G1 = 0x00A83D49

| 项 | 结论 | 等级 |
|---|---|---|
| 置位者 | 4 处 `mov byte ptr [0xa83d49], 1`，全部在 `0x4F8440` 起的同一函数内（`0x4F867C`、`0x4F8692`、`0x4F86EE`、`0x4F87BB`）。上游条件：`[esi+0x1F7]` / `[esi+0x1F8]` / `[esi+0x1F6]` 三个对象标志、`[0xA8B238]` 模式 ==0 或 3/4、`cmp esi,[0xA83D4C]`、两次虚调用 `[edx+4]`/`[eax+8]` 返回布尔；函数内先用 `0x6C8C40`/`0x7529E0`/`0x48D080` 做**等待循环**（`0x4F860B..0x4F8655`、`0x4F8732..0x4F877E`），再置位。 | `[静态推断-强]`（有直接写入条件） |
| 清零者 | `0x52DA78`（初始化）、`0x55D129`、`0x55D1B1`、`0x55D219`、`0x55D25C`（消费路径，写 `bl=0`，`bl` 由同函数 `0x55D05E xor ebx,ebx` 得 0）。 | `[静态推断-强]` |
| 语义假设 | 与**联机/多人同步等待**相关（所在函数以帧计数 `0xA8ED84` 为时间基准、按 `[esi+0x2A4]/[esi+0x2AC]` 做帧差、判模式 3/4、等待循环），置位 = 「请求挂起帧推进直到同步/等待条件解除」。**不是**已证的「暂停菜单」。 | `[静态推断-弱]`（仅函数邻近性 + 模式枚举） |
| 真机期待值 | 正常对战推进中应为 **0**；进入等待/同步/断线处理时应短时读到 **1**，随后被 `0x55D1xx/0x55D2xx` 清回 0。 | `[待运行验证]` |

### G2 = 0x00A8ECD0

| 项 | 结论 | 等级 |
|---|---|---|
| 置位者 | 3 处 `mov byte ptr [0xa8ecd0], 1`（`0x4F86F7`、`0x4F879C`、`0x4F87B2`），与 G1 置位**同一函数 `0x4F8440`、互补分支**：G1 置位路径的 `else` 落到 `0x4F86F7 c6 05 d0 ec a8 00 01`。前置条件同样是 `[esi+0x1F8]` / `[esi+0x1F6]` 帧差计时与等待循环。 | `[静态推断-强]` |
| 清零者 | `0x52DA7F`、`0x55D123`、`0x55D1B7`、`0x55D21F`、`0x55D262`。 | `[静态推断-强]` |
| 语义假设 | G1/G2 是同一「等待/同步」状态机的两个互补标志；G2 可能对应另一类等待（如「另一方向/另一阶段的同步」），但**无法静态区分**二者各自对应的具体状态。 | `[静态推断-弱]` |
| 真机期待值 | 正常推进中 **0**；与 G1 互斥地短时为 **1**。 | `[待运行验证]` |

### G3 = 0x008B41C0 —— 旧记录纠错

> **[转引] 点名纠正**：旧记录把「门控 3」写成 `0x41C0`，那是**从非法起点 `0x55DE60` 解码产生的 `67` (address-size override) 前缀伪影**（该 `0x67` 实为 `0x55DE5F jne 0x55DEC8` 的 rel8 位移），并非真实地址。精确复现见 `EVIDENCE/14_gate3_artifact.txt`。复核 `[本次实测]`：`0x0055DE61 a0 c0 41 8b 00` = `mov al, byte ptr [0x8b41c0]`，4 字节小端操作数 `c0 41 8b 00` ⇒ **门控 3 = 0x008B41C0**，RVA `0x004B41C0`，FOFF `0x004B41C0`（该 VA 在 `.data` BSS 尾，无文件字节）。见 `EVIDENCE/03_channelA_decoded.txt` 与 `DISAGREE.md`。

| 项 | 结论 | 等级 |
|---|---|---|
| 置位者 | `0x48CB2E  c6 05 c0 41 8b 00 01  mov byte ptr [0x8b41c0], 1`。位于 `0x48C...` 的一个分发函数：`0x48CB22 c6 05 fc 2c 82 00 00` 与 `0x48CB2E` 是**相邻 switch 分支**（各自 `jmp 0x48CC31` 汇合），其邻居 `0x48CB4C` 起读 `[0xA83D4C]` 对象的 `+0x1F5/+0x1F7/+0x1F8` 标志。 | `[静态推断-强]`（有直接写入点与其所在分支结构） |
| 清零者 | `0x52DA86`、`0x55D12F`、`0x55D1BD`、`0x55D225`、`0x55D268`。 | `[静态推断-强]` |
| 语义假设 | 该地址位于一块**全局对象/配置块**：邻近 `0x8B41B8`(17 命中)、`0x8B41C8`(12)、`0x8B41CC`(27)、`0x8B41D8`(35)、`0x8B41F8/FC/0x8B4200` 在初始化函数 `0x52D9E4..0x52D9F0` 被成组写 0；`0x8B41E0`(10 命中)。它**不像**独立布尔，更像某个结构体的成员（`EVIDENCE/08_imports_strings.txt`）。置位分支与「回合/网络消息分发」同处一函数。 | `[静态推断-弱]` |
| 真机读到非零时的解释 | 不能只解释成「暂停」：应同时检查同块的 `0x8B41B8 / 0x8B41CC / 0x8B41D8` 以及 `[0xA83D4C]` 对象 `+0x1F5/+0x1F7/+0x1F8`，判断是分发状态还是挂起请求。 | `[待运行验证]` |

### G4 = 0x00A83D48

| 项 | 结论 | 等级 |
|---|---|---|
| 置位者 | `0x4C7917  c6 05 48 3d a8 00 01  mov byte ptr [0xa83d48], 1`。**直接上游** `[静态推断-强]`：`0x4C7903 mov ecx,[0xa8ed84]` → `0x4C790A push 0x820e0c` → `0x4C790F call 0x4068e0`（printf）→ `0x4C7914 add esp,8` → 立刻置位。`0x820E0C` 的字符串实测为 `"Processing EXIT event on frame %d\n"`（`EVIDENCE/08_imports_strings.txt`），即**打印当前帧号后立即置 G4=1**。函数尾部 `0x4C7929` 起还有 `test byte [0xa8d5f8],2` / `mov dword [0xa8eda0],1` 分支。 | `[静态推断-强]`（有直接写入点 + 相邻字符串 + 帧号实参） |
| 清零者 | `0x52DA8D`、`0x55D135`、`0x55D1C3`、`0x55D22B`、`0x55D26E`。 | `[静态推断-强]` |
| 语义假设 | 与 G1 (`0xA83D49`) **地址相邻**，中间 `0xA83D4A/4B` 为填充、`0xA83D4C` 是全局对象指针（`cmp esi,[0xA83D4C]` 多处出现），推测四者同属一个 8 字节全局头 `0xA83D48..0xA83D4F`：`+0`=G4, `+1`=G1, `+4`=对象指针。置位前以帧号为参数打印 `"Processing EXIT event on frame %d"` → 更可能是**事件/退出事件处理（含录像回放事件）**相关标志；另有 `0x82637C "Loaded recording values for scenario : %s"` 在初始化区被引用，但与本写点**不在同一函数**，仅为弱邻近性。 | `[静态推断-弱]`（状态名） |
| 真机期待值 | 正常推进中 **0**；触发 EXIT 事件/回放事件处理时读到 **1**，同时应在日志或真机侧看到帧号被打印。 | `[待运行验证]` |

### 正常状态映射表（**全部为假设，非已证**）

| 状态 | 候选门控 | 依据 | 等级 |
|---|---|---|---|
| 加载中 / 场景初始化 | 全部 4 个被清 0 | `0x52DA78..8D` 与帧计数归零同函数 | `[静态推断-强]`（清零事实）/ 映射 `[待运行验证]` |
| 联机同步 / 等待其他玩家 | G1 / G2 | `0x4F8440` 函数以帧计数计时、模式 3/4、等待循环 | `[静态推断-弱]` |
| 回放 / 录像 / EXIT 事件处理 | G4（弱） | `0x4C7903` 以帧号为参数打印 `"Processing EXIT event on frame %d"` 后立刻置 G4；`0x82637C "Loaded recording values for scenario : %s"` 在初始化区 | `[静态推断-弱]` |
| 暂停 / 菜单 / 失焦 | 未提供直接 API 证据 | 导入表含 `PeekMessageA`/`GetForegroundWindow`/`GetActiveWindow`/`DialogBoxParamA`/`MessageBoxA`/`Sleep`，但**未定位到**这些 API 与四门控写入点在同一基本块/调用链上 | `[待运行验证]` |
| 编辑器 | 无静态证据 | — | `[待运行验证]` |

> 明确否认：本次**没有**证明任何一个门控等于「暂停」。静态只能证明「非 0 ⇒ 帧推进被跳过」以及各写点的直接条件。

## 4. 真机侧该期待什么值（给同轮只读观测代理）

| 场景 | G1 0xA83D49 | G2 0xA8ECD0 | G3 0x8B41C0 | G4 0xA83D48 | `[0xA8ED84]` |
|---|---|---|---|---|---|
| 主菜单 / 未进入对局 | 0（或未初始化 0） | 0 | 0 | 0 | 冻结/上次值 |
| 场景加载完成瞬间 | 0 | 0 | 0 | 0 | 0（`0x52DA08` 归零） |
| 正常对战推进（预期稳态） | **0** | **0** | **0** | **0** | 单调递增 |
| 挂起/等待/同步窗口 | 短时 1（G1 或 G2 互斥） | 短时 1 | 视触发源 | 视触发源 | **停止递增** |
| 挂起被消费后 | 0 | 0 | 0 | 0 | 恢复递增 |

以上除「正常推进中 0」为 `[静态推断-强]`（由 `0x55DE4F..71` 串联跳过逻辑反推）外，其余取值均为 `[待运行验证]`。真机只读观测若读到非 0，请同时采 `[0xA8ED84]` 是否停止递增、`[0xA8B238]` 模式、`[0xA8E9A0]` 活动标志与 `[0xABCD58]`，以便区分「挂起请求」与「残留脏值」。

