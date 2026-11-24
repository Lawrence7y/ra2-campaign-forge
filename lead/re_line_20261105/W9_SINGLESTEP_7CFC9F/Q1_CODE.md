被核对象 = gamemd.exe + EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360
EXCEPT 件 SHA256 = 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251，字节数 = 26405
Engine 自证 = COVERAGE 99.998375677293% (1394120 insns, 66 resync-fails) / IMAGEBASE 0x400000
回件时刻 = 2026-11-06 01:23:00

# Q1 · `0x7CFC9F` 处的代码到底是什么

> 本回件只答 TASK.md §2 Q1。Q2（函数归属）/Q3（机制）/Q4（与主崩溃关系）/Q5（路线）
> 不属本项，未验，不补造。
> 铁律遵守：零真机、零采样注入（E3 维持暂停 D-13）、零活进程读取；只读磁盘文件；
> 唯一写域 = `W9_SINGLESTEP_7CFC9F/`。Python 一律 `python -I -X utf8`。

## 0 · 本次实跑的命令与前置件

| # | 命令 / 动作 | 结果 |
|---|---|---|
| C1 | `sha256sum "ra2youli/gamemd.exe"` + `wc -c` | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` / `4825360`（与 TASK §0 目标镜像一致） |
| C2 | `sha256sum "…/EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt"` + `wc -c` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` / `26405`（与 TASK §1 声明 26,405 B 一致） |
| C3 | `python -I -X utf8 …\_w9_q1.py > …\_w9_q1_stdout.txt 2>&1` | `EXIT=0`，末尾 `PROBE DONE -- exit 0`，自写 `_w9_q1_out.txt`（235 行） |
| C4 | `python -I -X utf8 -c "…Engine…"`（前置计时/探路） | SHA 一致，`by()` 构建 61.74s，COVERAGE 99.998375677293% |

§1 前置件按序已读（只读）：
1. `EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt` 全文（1046 行）：L1 `Error code: EXCEPTION_SINGLE_STEP`、L3 `Exception occurred at 007CFC9F`、L11 `Eip:007CFC9F`、L14 `EFlags:00000286`、L13 `Esi:7FFFFFFF Edi:00000001`、L17 `Bytes at CS:EIP (007CFC9F)`。
2. `SINGLESTEP_0x7CFC9F_ANALYSIS.md`（17,473 B）全文——**默认怀疑**，本回件只对其 §1.1 指令流与 §2 的 ±32B 字节断言做字节复核（见 §5）。
3. `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:1898` 附近（§163 附带发现①：将 `0x7CFC9F` 记为「SBH freelist 区」）与 `:1962-1969` 附近（§162 重大证据：13:5x 秒退现场）。
4. `lead/GOAL_THREE_TARGETS_20261018.md` §555（L5466 起）：107 份 `except_post_*.txt` 全同哈希 `6694b75e…`，判「历史基线残件，不是任何一趟的崩溃证据」。

**越界提示（只记事实，不下结论）**：本回件自算 EXCEPT 件 SHA256 前缀 = `6694b75e`（`_w9_q1_out.txt:230`），
与 §555 所记 107 份哈希前缀相同。是否「就是那 107 份之一」属 **Q4**，本项不作定谳。

## 1 · Q1 要求①：`Engine().rd(0x7CFC9F, 32)` 原始字节重读 + 逐条反汇编到 0x30 字节

### 1.1 原始字节（真读，非引用）

`ra2tool.Engine` 自证：`Engine.sha == 自算 SHA`（`_w9_q1_out.txt:24`），`IMAGEBASE = 0x400000`（`:25`）。
`fo(0x7CFC9F) = 3996831 = 0x3CFC9F`，与 `VA − 0x400000 = 0x3CFC9F` 相等（`:27-28`）——
即旧分析 §0/§6 的「正确映射 `file_off = VA − 0x400000`」在本点成立。

```
rd(0x7CFC9F, 32) = 8B 0A 2B 4D F0 8B F1 89 4D F8 C1 FE 04 4E 83 FE 3F 7E 03 6A 3F 5E 3B F7 0F 84 0D 01 00 00 8B 4A
```
（`_w9_q1_out.txt:34`；`type(e.rd(...)) = bytes`, `len = 32`, `:33`）

```
rd(0x7CFC9F, 0x30=48) = 8B 0A 2B 4D F0 8B F1 89 4D F8 C1 FE 04 4E 83 FE 3F 7E 03 6A 3F 5E 3B F7 0F 84 0D 01 00 00 8B 4A 04 3B 4A 08 75 61 83 FF 20 7D 2B BB 00 00 00 80
```
（`:37`）

### 1.2 逐条反汇编到 0x30 字节（两条独立口径互证）

TASK §0 警示 `disasm` 会吞异常。故本探针同时跑：
- **E1** `e.disasm(VA, 0x30)`（capstone 线性直读）：18 条，覆盖 48 字节（`:120-127`）；
- **E2** 重同步流 `e.by()` 逐址推进，逐条校验 `bytes(ins.bytes) == e.rd(ins.address, ins.size)`：
  18 条全部 `bytes_ok=True`，覆盖 48 字节，末址 `0x7CFCCF`（`:149-161`）；
- **E1 与 E2 前 18 条 `(addr, mnemonic, op_str)` 全等 = True**（`:162`）。

完整 18 条（`_w9_q1_out.txt:149-160`）：

| # | VA | bytes | 助记符 / 操作数 |
|---|---|---|---|
| 1 | `0x7CFC9F` | `8B0A` | `mov ecx, dword ptr [edx]` |
| 2 | `0x7CFCA1` | `2B4DF0` | `sub ecx, dword ptr [ebp - 0x10]` |
| 3 | `0x7CFCA4` | `8BF1` | `mov esi, ecx` |
| 4 | `0x7CFCA6` | `894DF8` | `mov dword ptr [ebp - 8], ecx` |
| 5 | `0x7CFCA9` | `C1FE04` | `sar esi, 4` |
| 6 | `0x7CFCAC` | `4E` | `dec esi` |
| 7 | `0x7CFCAD` | `83FE3F` | `cmp esi, 0x3f` |
| 8 | `0x7CFCB0` | `7E03` | `jle 0x7cfcb5` |
| 9 | `0x7CFCB2` | `6A3F` | `push 0x3f` |
| 10 | `0x7CFCB4` | `5E` | `pop esi` |
| 11 | `0x7CFCB5` | `3BF7` | `cmp esi, edi` |
| 12 | `0x7CFCB7` | `0F840D010000` | `je 0x7cfdca` |
| 13 | `0x7CFCBD` | `8B4A04` | `mov ecx, dword ptr [edx + 4]` |
| 14 | `0x7CFCC0` | `3B4A08` | `cmp ecx, dword ptr [edx + 8]` |
| 15 | `0x7CFCC3` | `7561` | `jne 0x7cfd26` |
| 16 | `0x7CFCC5` | `83FF20` | `cmp edi, 0x20` |
| 17 | `0x7CFCC8` | `7D2B` | `jge 0x7cfcf5` |
| 18 | `0x7CFCCA` | `BB00000080` | `mov ebx, 0x80000000` |

`0x7CFC9F` 之前的顺序上下文（`:173-186`）：`0x7CFC98 8B4DF4 mov ecx,[ebp-0xC]` →
`0x7CFC9B 8B54F904 mov edx,[ecx+edi*8+4]` → `0x7CFC9F`。即崩点是**顺序直线流**中的一条，
不是孤立的孤立字节。

**代码身份（字节级结论）**：`0x7CFC9F` 处是 2 字节 x86 指令 `8B 0A` = `mov ecx, dword ptr [edx]`，
在其后紧接 `sub ecx,[ebp-0x10]`、`mov esi,ecx`、`sar esi,4`、`dec esi`、`cmp esi,0x3F`、
`jle`、`push 0x3F`/`pop esi`、`cmp esi,edi`、`je 0x7CFDCA` —— 一个「读节点字段 → 算余量 →
按 16 字节粒度换 class → 钳位到 63 → 与请求 class 比较」的算术/分支序列。
**（语义层面「是否即 `__sbh_alloc_block`」属 Q2，本项只给字节与指令身份，不越界定名。）**

## 2 · Q1 要求②：证据件字节逐字节比对（自己重读一遍）

三源各自独立解析为 32 字节：

| 源 | 出处 | 解析字节数 |
|---|---|---|
| 磁盘 | `e.rd(0x7CFC9F,32)` | 32 |
| 证据件 L17 `Bytes at CS:EIP (007CFC9F)` | `…EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt:17` | 32 |
| TASK.md §2 Q1 内嵌串 | `TASK.md:40` | 32 |

逐字节表见 `_w9_q1_out.txt:46-79`（索引 0–31，VA `0x7CFC9F`…`0x7CFCBE`，
每行 `磁盘rd / EXCEPT / TASK` 三值并列，全部 `OK`）。

```
磁盘 rd[0:32] vs EXCEPT 逐字节差异索引 = []          (_w9_q1_out.txt:80)
磁盘 rd[0:32] == EXCEPT[0:32] : True                  (:81)
证据件 == TASK.md 内嵌串 : True                        (:44)
长度一致性: len(rd32)=32 len(EXCEPT)=32 len(TASK)=32  (:82)
```

**结论：32/32 字节完全一致，零处不一致。** 证据件 L17 的字节串与当前磁盘镜像在
`0x7CFC9F..0x7CFCBE` 上逐字节吻合；TASK.md §2 Q1 抄录的内嵌串也与证据件一字不差。

### 2.1 附带核对：±32B 窗口的 `CC / F1 / F0`（对旧分析 §0/§2 措辞的精度复核）

`rd(0x7CFC7F, 64)`（`:85`）：

```
0xCC 出现位置 = 无
0xF1 出现位置 = ['0x7cfca5']
0xF0 出现位置 = ['0x7cfca3']
```

旧分析 §0 L12 写「崩溃点前后 ±32 字节与磁盘逐字节全等（无 `F1`/`CC`/`F0`）」、
§2 #2 L60 写「±32B 无 `F1`」。**按原始字节字面读，这两句不精确**：窗口内确有 `F1` 与 `F0`。

但按**指令起始操作码**读（D3 枚举，`:90-118`）：±32 窗口内 24 条指令的 opcode0
无一为 `CC/F1/F0`，`±32 窗口内以 CC/F1/F0 为独立操作码起点的指令 = 无`（`:117`）。
两处字节的归属是：
- `0x7CFCA5 = F1` 是 `0x7CFCA4 8B F1 mov esi,ecx` 的 **ModRM 字节**；
- `0x7CFCA3 = F0` 是 `0x7CFCA1 2B 4D F0 sub ecx,[ebp-0x10]` 的 **disp8 字节**。

⇒ 旧分析「无独立 INT1/ICEBP(`0xF1`)/INT3(`0xCC`)/LOCK(`0xF0`) 指令」的**实质结论成立**，
「±32B 无 F1/F0 字节」是**措辞精度缺陷，不是实质错误**（不影响其 §2 #1/#2 的排除判据）。
本项不据此改判 REFUTED；详见 §5 诚实账。

## 3 · Q1 要求③：前 8 条指令的助记符与操作数

（`_w9_q1_out.txt:165-172`，由 E2 重同步流锚定、并与 E1 全等互证）

| # | VA | 原始字节 | 助记符 | 操作数 |
|---|---|---|---|---|
| 1 | `0x7CFC9F` | `8B 0A` | `mov` | `ecx, dword ptr [edx]` |
| 2 | `0x7CFCA1` | `2B 4D F0` | `sub` | `ecx, dword ptr [ebp-0x10]` |
| 3 | `0x7CFCA4` | `8B F1` | `mov` | `esi, ecx` |
| 4 | `0x7CFCA6` | `89 4D F8` | `mov` | `dword ptr [ebp-8], ecx` |
| 5 | `0x7CFCA9` | `C1 FE 04` | `sar` | `esi, 4` |
| 6 | `0x7CFCAC` | `4E` | `dec` | `esi` |
| 7 | `0x7CFCAD` | `83 FE 3F` | `cmp` | `esi, 0x3f` |
| 8 | `0x7CFCB0` | `7E 03` | `jle` | `0x7cfcb5` |

注：`0x7CFCB0` 的 `jle` 目标 `0x7CFCB5` 恰是跳过 `push 0x3F; pop esi` 钳位对的落点，
这条 `push/pop` 是「class 钳位到 63」的实现（`:129-130`、`_w9_q1_out.txt:157-158`）。

## 4 · Q1 要求④：`0x7CFC9F` 是否在重影流里（`va in e.by()`）

**是。**

```
0x007CFC9F in e.by() = True                                     (_w9_q1_out.txt:189)
by()[0x007CFC9F] -> size=2 bytes=8B0A  mov ecx, dword ptr [edx]  (:190)
COVERAGE = 99.998375677293% / 1394120 insns / 66 resync-fails   (:29)
```

`ra2tool.py:91-113` 定义 `stream` 为 `.text` 上「逐址 +1 重同步线性解码」的指令集合，
`by()` 返回其 `{address: insn}` 索引；`coverage` = 解码字节 / `.text` 大小。
本地址是重同步流中的**合法指令起始**（2 字节，恰好 `8B0A`），不是流中某条指令的中段。

TASK §2 Q1 的「**若不在**，说明它是 `call`/`jmp` 的落点还是数据区」这一条件分支
**不适用**（前提为假）。但为免「查不到就当不存在」，仍给出落点/数据区的直接依据：

| 判据 | 实跑结果 | 出处 |
|---|---|---|
| 是否数据区 | `by()[VA] 存在 = True` → 合法指令起始，**不是数据区** | `:209` |
| VA 处字节 | `8B 0A 2B 4D F0 8B F1 89 4D F8 C1 FE 04 4E 83 FE`（非全零、非不可解码、非 `CC`/`int3`） | `:208` |
| 局部窗口 `[0x7CF000,0x7D1000)` 内以 VA 为**直接**目标的 `call/jmp/jcc` | **0 条** | `:201` |
| 全 `.text`（1,394,120 条指令）内以 VA 为**直接**目标的 `call/jmp/jcc` | **0 条** | `:204` |
| 前一条指令 | `0x7CFC9B 8B54F904 mov edx,[ecx+edi*8+4]`，size=4，末址 `= 0x7CFC9F`，**紧邻 VA: True** | `:211` |
| `0x7CFC9B..0x7CFC9E` 字节 | `8B 54 F9 04`（无独立 `F1` 指令） | `:206` |

**判定**：`0x7CFC9F` **不是**任何 `call`/`jmp`/`jcc` 的直接落点（限定窗口与全 `.text`
两口径均为 0 条），也**不是**数据区；它是**顺序直线流**中紧接
`0x7CFC9B`（4 字节指令，末址正好 `0x7CFC9F`）的下一条指令起始。
即：控制流靠「上一条指令自然落下」到达此处，而非靠分支跳入。

**未验（不补造）**：间接分支 / 跳转表落点（`push VA; ret`、`jmp [table]`、
`call [reg]` 等）本探针未解析，写「未验」；这不影响「非直接落点、非数据区」的字节级结论。

## 5 · 对旧分析 `SINGLESTEP_0x7CFC9F_ANALYSIS.md` 的复核（默认怀疑 → 实测）

本项只核其**代码身份相关**的断言（Q1 范围内），不核机制/施动者（Q3 范围）。

- **§1.1 崩溃点指令流（`0x7CFC98`–`0x7CFCB7`，14 条）**：逐条拿 `e.by()[addr]` 的
  `.bytes` 与旧分析列出的十六进制比对，**14/14 全部 `bytes=OK`**，助记符/操作数一致
  （`_w9_q1_out.txt:213-227`）。旧分析在「这段是什么代码」上**没有实质错误**。
  其坐标校正（`file_off = VA − 0x400000`）本点亦实测成立（`:27-28`）。
- **§2 #1/#2 的 `CC`/`F1` 排除**：实质结论成立（无独立 INT3/INT1 指令，见 §2.1），
  但「±32B 无 F1/F0」按原始字节字面读不精确 —— 记为**措辞精度缺陷，非实质错误**。
- 旧分析 §1.1 把它定名为 `__sbh_alloc_block` / `0x7CFB13–0x7CFE1B`、并对
  `Esi=0x7FFFFFFF` 给语义 —— 这些属 **Q2/Q3**，本项**未验**，不采信也不反驳。

⇒ 按 TASK §4 判定档：本项**未发现旧分析的实质错误**，不判 REFUTED。

## 6 · 判定与诚实账

**partVerdict = CONFIRMED**：Q1 四条要求的每条结论都有「反汇编地址 + 原始字节」或
「文件:行」支撑；两条独立反汇编口径（线性 `disasm` / 重同步 `by()`）互证，
两处独立哈希命令 + Engine 自身 SHA 断言三方一致。

**已验**：
- 原始字节 32 B / 48 B 真读；0x30 窗口 18 条指令双口径全等；
- 证据件 L17 / TASK.md:40 / 磁盘 三源 32/32 逐字节零差异；
- 前 8 条助记符与操作数；
- `va in e.by() = True` + 局部/全 `.text` 直接分支落点普查 + 前序指令紧邻性；
- 两个 SHA256、两个字节数、IMAGEBASE、COVERAGE。

**未验 / 不越界（拿不到就写未验，不补造）**：
- 间接分支 / 跳转表落点 —— 未验（§4 已标）；
- 运行态镜像字节是否与磁盘一致 —— 本任务零真机、零活进程，只做磁盘静态，**未验**；
  旧分析 §0 的「运行态=磁盘」断言本项不复核；
- 函数起止 VA、`e.func_rets`、crashspec 工作范围检索 —— **Q2**，未验；
- `EFlags=0x286` 位分解、TF/DR/RaiseException 候选、`Esi/Edi` 语义 —— **Q3**，未验；
- 该 EXCEPT 件是否即 107 份 `except_post_*.txt` 之一（`6694b75e…` 同前缀已在 §0 记为事实） —— **Q4**，未验；
- 目标② 下一步路线 —— **Q5**，未验；
- 「查不到 ≠ 不存在」：全 `.text` 直接分支 0 条是**实跑普查**结果，不是「搜一次说没有」；
  间接落点明确写未验，不推断为不存在。

**substantiveDefect = false**（在 Q1 代码身份范围内，旧分析 §1.1 指令流 14/14 字节吻合；
仅一处措辞精度缺陷，非实质）。

## 7 · 交付物与复现

| 文件 | 说明 |
|---|---|
| `Q1_CODE.md` | 本回件（含 §3 强制头部） |
| `_w9_q1.py` | 只读探针，独立可跑、自写输出、自行退出（单次约 62 s，远低 8 分钟上限） |
| `_w9_q1_out.txt` | 探针输出（235 行，全量证据） |
| `_w9_q1_stdout.txt` | 同次运行的 stdout 捕获（含末尾 `wrote …` 一行），`EXIT=0` |

复现命令（在 `D:\Project\ra2-campaign-forge` 下）：
```
python -I -X utf8 "D:\Project\ra2-campaign-forge\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\_w9_q1.py"
```
探针内固定绝对路径，读 `ra2youli\gamemd.exe`、EXCEPT 件、`TASK.md`；
`sys.path.insert` 指向 `lead\goal3t_nightwatch_20261102\swarm_20261104` 取 `ra2tool.Engine`；
不启动进程、不读活内存、不改既有文件。
