# W9 / Q2 · `0x7CFC9F` 属于哪个函数 —— 定谳

```
被核对象 = gamemd.exe + EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360
EXCEPT 件 SHA256 = 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251，字节数 = 26405
Engine 自证 = COVERAGE 99.9984% / IMAGEBASE 0x400000
回件时刻 = 2026-11-06 01:28:18
```

> 判读纪律：本件对 `TASK.md` §2 Q2 的**三条要求逐条作答**，全部数字来自本轮实跑的
> `python -I -X utf8 lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q2.py`
> （输出：`_w9_q2_out.txt`）+ 补充定向复核命令，**不采信任何既有文字结论作为字节证据**。
> 只读、零真机、零采样注入（E3 维持暂停 D-13）。唯一写域 = `W9_SINGLESTEP_7CFC9F/`。

---

## 0 · 一句话结论

**`0x7CFC9F` 属于函数起 `0x7CFB13`、止 `0x7CFE1B`（唯一 `ret`）、体长 `0x309 B = 777 B`、275 条指令的那个函数；既有分析把它命名为内嵌 MSVC 6.0 CRT `__sbh_alloc_block`。该函数在 `docs/re/`、`lead/` 与 `out/re_work/…/crashspec*` 里被反复、密集地分析过 —— 「未被覆盖」的假说被多口径搜索直接否定。**

`0x7CFC9F` 在重同步流里（`va in e.by()` = `True`），位于该函数 `+0x18C`（+396 B）。

---

## 1 · 前置自证（强制头部的数据来源）

| 项 | 值 | 来源 |
|---|---|---|
| gamemd.exe SHA256 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | `_w9_q2_out.txt:3`；`Engine()` 构造内 `assert self.sha == EXPECT_SHA` 通过，`_w9_q2_out.txt:7` 打印 `一致 = True` |
| gamemd.exe 字节数 | 4,825,360 | `_w9_q2_out.txt:3` |
| EXCEPT 件 SHA256 | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` | `_w9_q2_out.txt:4` |
| EXCEPT 件字节数 | 26,405 | `_w9_q2_out.txt:4`；与 `ls -la` 一致 |
| COVERAGE | 99.9984 %，1,394,120 条指令，resync_fails = 66 | `_w9_q2_out.txt:5`（`e.coverage`，即 `ra2tool.py:110-113`） |
| IMAGEBASE | `0x400000` | `_w9_q2_out.txt:5`（`e.IB`，`ra2tool.py:60`） |
| `.text` | `0x401000 .. 0x7E1000`，TSZ = `0x3E0000` | `_w9_q2_out.txt:6`；节表见 `_w9_q2_explore_out.txt:4` |

`e.raw` 是 `bytes`（`ra2tool.py:53`），读字节一律用 `e.rd(va,n)`（`ra2tool.py:83-85`）；
「是否指令起始」一律用 `va in e.by()`（`ra2tool.py:115-117`），本件未把 `e.disasm` 的返回值当作流成员判据。

> 附带观察（**不属 Q2 判定范围，交 Q4 定谳**）：EXCEPT 件 SHA256 前缀 `6694b75e…`
> 与 `lead/GOAL_THREE_TARGETS_20261018.md:5475` §555 所记 107 份 `except_post_*.txt` 的
> 单一哈希 `6694b75e…` 前缀相同。本件**只报告这一实算哈希**，不据此断言 Q4 的二选一结论。

---

## 2 · Q2-(1) 向上回溯到最近的函数序言

### 2.1 实跑方法

探针在窗口 `[0x7CF000, 0x7CFC9F]`（向上 0xC9F B，**未全盘扫**）内，对每一个
`va in e.by()` 的地址读 `e.rd(va,5)`，匹配两类序言签名：

- `55 8B EC 83 EC` = `push ebp; mov ebp,esp; sub esp,imm8`
- `55 8B EC` = `push ebp; mov ebp,esp`（TASK §2 Q2 点名的第一种）

并按 TASK §2 Q2 的第二种口径单独核了 `83/81 EC imm`（`sub esp,imm`）且前方是 `ret`/`int3` 对齐的候选。

### 2.2 结果（`_w9_q2_out.txt:16-32`）

| 距离（近→远） | 序言 VA | 签名 | 前 8 字节 | Δ 到 EIP |
|---|---|---|---|---|
| **1** | **`0x007CFB13`** | `push ebp; mov ebp,esp; sub esp,imm8` | `55 8B EC 83 EC 14 A1 94` | **+0x18C** |
| 2 | `0x007CF7E8` | 同上 | `55 8B EC 83 EC 14 8B 55` | +0x4B7 |
| 3 | `0x007CF64C` | `push ebp; mov ebp,esp` | `55 8B EC 51 51 DD 45 08` | +0x653 |
| 4 | `0x007CF51C` | 同上 | `55 8B EC 51 51 DD 45 08` | +0x783 |
| 5 | `0x007CF347` | 同上 | `55 8B EC 83 C4 E0 89 45` | +0x958 |
| 6 | `0x007CF330` | 同上 | `55 8B EC 83 C4 E0 89 45` | +0x96F |

**最近序言 = `0x7CFB13`。**

### 2.3 序言前方的 `ret` 对齐（TASK 明确要求）

```
e.rd(0x7CFB0D, 6) = 00 5F 5E 5B C9 C3          (_w9_q2_out.txt:24)
e.rd(0x7CFB12,10) = C3 55 8B EC 83 EC 14 A1 94 8B   (补充复核命令输出)
紧邻前 1 字节 = C3  → ret 对齐               (_w9_q2_out.txt:25)
前一函数尾声 in by(): 0x7CFB0E pop edi / 0x7CFB0F pop esi / 0x7CFB10 pop ebx
                     / 0x7CFB11 leave / 0x7CFB12 ret   (_w9_q2_out.txt:26)
```

序言逐条 `e.disasm(0x7CFB13, 0x10)`（`_w9_q2_out.txt:27-31`）：

```
0x007CFB13  55              push ebp
0x007CFB14  8BEC            mov ebp, esp
0x007CFB16  83EC14          sub esp, 0x14
0x007CFB19  A1948BB700      mov eax, dword ptr [0xb78b94]
```

### 2.4 对「`sub esp,imm` 且前方 ret/int3」候选的排除（不满足即写依据，不写「没有」）

补充复核命令（`python -I -X utf8 -c …`，输出见本会话）在 `[0x7CF000,0x7CFC9F]`
枚举出 8 个 `83/81 EC` 起始；其中**唯一**前方紧邻字节为 `C3` 的是
`0x7CF465`（`83 EC 08 DD 14 24`），前置 `0x7CF464 in by() = True, mnemonic = ret`。
但它**不能**拥有 `0x7CFC9F`，依据：

```
ret 指令起始 in [0x7CF465, 0x7CFB13) = 16 个
  ['0x7cf4bd','0x7cf4c4','0x7cf4c9','0x7cf64b','0x7cf6ac','0x7cf6b0',
   '0x7cf6e8','0x7cf6ec','0x7cf761','0x7cf767','0x7cf775','0x7cf77e',
   '0x7cf79b','0x7cf7bc','0x7cf7e7','0x7cfb12']
⇒ 中间隔着 16 个 ret + 0x7CFB13 的独立序言/ret 边界，故 0x7CF465 属更前面的另一函数。
```

另：`(0x7CFB13, 0x7CFC9F)` 开区间内 **ret/int3 指令起始 = NONE**（补充复核输出），
即 EIP 与序言之间不存在任何函数边界。

### 2.5 `0x7CFB13` 确为函数入口（xref 交叉，非仅靠签名）

补充复核命令对全重同步流枚举 `call/jmp` 的 imm 目标：

```
0x007C9484  call 0x7cfb13 | E8 8A 66 00 00
0x007D0FB6  call 0x7cfb13 | E8 58 EB FF FF
0x007D33AB  call 0x7cfb13 | E8 63 C7 FF FF
total direct call/jmp xrefs to 0x7CFB13 = 3
```

第一处与 `docs/re/ARCHITECTURE_ATLAS.md:2318`、`docs/re/crt_memory_pool_deep_dive.md:129`
所记 `0x007C9484: E8 8A 66 00 00 call 0x007CFB13` 逐字节吻合。

---

## 3 · Q2-(2) 函数起止 VA、长度、函数内 `ret` 数量

### 3.1 定界依据（全部字节 + `e.func_rets`）

`_w9_q2_out.txt:36-56`：

```
[边界] 前向 0x600 窗口内全部 ret 指令起始：
        [('0x7cfe1b','ret',''), ('0x7cfecc','ret',''), ('0x7cffc7','ret','')]
[边界] 函数起 START = 0x7CFB13
[边界] 唯一/首个 ret @ 0x7CFE1B (ret, size=1)
[边界] 函数止 END(不含) = 0x7CFE1C；含 ret 末字节 = 0x7CFE1B
[边界] 长度（不含 ret 字节）= 0x308 = 776 B
[边界] 长度（含 ret 1B）  = 0x309 = 777 B
[边界] 0x7CFC9F 相对函数头 = +0x18C (+396 B)
[边界] 函数体指令数（by() 内 [START,END)）= 275
```

**`e.func_rets` 实跑（TASK 点名要求）**：

```
[边界] e.func_rets(0x7CFB13, 0x7CFE1C) → ret 数 = 1
        ret @ 0x007CFE1B  ret   bytes=C3
[边界] 交叉 e.func_rets(0x7CFB13, 0x7D0113) → ret 数 = 3，
        地址 = ['0x7cfe1b', '0x7cfecc', '0x7cffc7']
```

`e.func_rets` 定义见 `ra2tool.py:216-218`（`_edges` 取 `[lo,hi)` 内的 `ret*`），
故传 `hi = 0x7CFE1C` 恰好把 `0x7CFE1B` 的 `ret` 计入 → **1**；
放宽到 `0x7D0113` 才出现 3 个，说明 `0x7CFECC` / `0x7CFFC7` 属**后续函数**，不属本函数。

### 3.2 边界三件套（尾声 + 下一函数起点 + 字节）

```
[边界] 下一函数起点候选 0x7CFE1C: in by()=True,
       e.rd(...,8) = A1 94 8B B7 00 8B 0D 84
       0x007CFE1C  mov eax, dword ptr [0xb78b94]     (_w9_q2_out.txt:47-48)

[边界] 尾声 in by() [0x7CFE11,0x7CFE1C):
  0x007CFE12  89 08        mov dword ptr [eax], ecx
  0x007CFE14  8D 42 04     lea eax, [edx + 4]
  0x007CFE17  5F           pop edi
  0x007CFE18  5E           pop esi
  0x007CFE19  5B           pop ebx
  0x007CFE1A  C9           leave
  0x007CFE1B  C3           ret                      (_w9_q2_out.txt:49-56)
```

`0x7CFE1C` 无 `int3`/`nop` 填充，紧接 `mov eax,[0xB78B94]` 即下一函数首指令 —— 与
`RC_SPEC_V4.md:109` 所记「`0x7CFE1C` 为另一函数（region 扩容/新建）」一致，
但本件是**自己读字节**得出，非采信该文字。

### 3.3 「只有一个 ret」的额外防漏（避免把数据字节 `C3` 误当/漏当 ret）

补充复核命令输出：

```
instruction count in [0x7CFB13,0x7CFE1C) = 275
gaps (end != next start) = NONE — 完全连续的重同步线性解码
first/last insn = 0x7cfb13 / 0x7cfe1b
last insn end = 0x7cfe1c ; HI = 0x7cfe1c
ret insns = ['0x7cfe1b']
all offsets whose byte == C3 :
   ['0x7cfb80','0x7cfba7','0x7cfbbb','0x7cfbd7','0x7cfe1b']
  of those, in by() : ['0x7cfe1b']
```

4 个内部 `C3` 字节全部是 `add ebx, 0x14`（`83 C3 14`）的第 3 字节，
**不是**指令起始、更不是 `ret`；唯一 `C3` 指令起始就是 `0x7CFE1B`。
另：函数内 `call`/`jmp` 立即数目标越出本函数窗的仅 2 处
（`0x7CFBDF call 0x7CFE1C`、`0x7CFBEE call 0x7CFECD`），**无尾部外跳**，
故「1 个 ret 即函数唯一出口」的读法成立。

### 3.4 汇总表

| 项 | 值 | 依据 |
|---|---|---|
| 函数起始 VA | **`0x7CFB13`** | `e.rd(0x7CFB13,5)=55 8B EC 83 EC`；前置 `0x7CFB12 = C3 ret`；3 处 `call` xref |
| 函数结束 VA | **`0x7CFE1B`**（`ret C3` 所在）；END 不含 = `0x7CFE1C` | `_w9_q2_out.txt:39,45` |
| 长度 | **`0x309 = 777 B`**（含 `ret` 1B）；`0x308 = 776 B`（不含） | `_w9_q2_out.txt:40-41` |
| 函数内 `ret` 数 | **1**（`0x7CFE1B`） | `e.func_rets(0x7CFB13,0x7CFE1C)` = 1，`_w9_q2_out.txt:44` |
| 指令数 | **275** | 连续重同步解码，`_w9_q2_out.txt:43` |
| EIP 相对位置 | `+0x18C`（+396 B） | `_w9_q2_out.txt:42` |
| `0x7CFC9F in e.by()` | **True**（真指令起始，非 call/jmp 落点、非数据区） | `_w9_q2_out.txt:10` |
| `e.rd(0x7CFC9F,32)` | `8B 0A 2B 4D F0 8B F1 89 4D F8 C1 FE 04 4E 83 FE 3F 7E 03 6A 3F 5E 3B F7 0F 84 0D 01 00 00 8B 4A` | `_w9_q2_out.txt:11` |

**符号名**（注意证据等级）：`__sbh_alloc_block` 是**既有分析的命名**，不是本轮反汇编能自证的符号。
本轮只核实「该 VA 被该名指称」：
`docs/re/except_zc11_forensics.md:112`（`### 2.2 函数识别：__sbh_alloc_block @ 0x007CFB13`）、
`:160`（`★ 崩溃于 +0x18C = 0x007CFC9F`）、
`docs/re/sbh_freelist_deep_dive.md:32,38`、
`docs/re/ARCHITECTURE_ATLAS.md:2257,4727`、
`out/re_work/work_chain/CONTINUE_20261003/crashspec_v4/RC_SPEC_V4.md:16,82,109,158`。
「内嵌 MSVC 6.0 CRT / SBH 小块堆」这一**来源归属属既有分析的推演**，本轮未独立证明 → **未验**（见 §6）。

---

## 4 · Q2-(3) 既有分析覆盖情况（**两种以上写法搜**）

### 4.1 命令与口径

全部跑自 `_w9_q2.py` 内的 `subprocess.run(["grep", …], cwd=ROOT)`，
`ROOT = D:\Project\ra2-campaign-forge`，搜索目录 = 任务书点名的 **`lead` + `docs/re`**。
`_w9_q2_out.txt:64-210` 逐条打印了完整 `cmd` 与命中文件列表。

| 口径 | 写法 | 精确命令 | 命中文件数 |
|---|---|---|---|
| **A** | `7CFC9F`（裸 VA，不分大小写） | `grep -r -I -i -l -e 7CFC9F lead docs/re` | **80** |
| **B** | `0x7CFC9F`（0x 前缀） | `grep -r -I -i -l -e 0x7CFC9F lead docs/re` | **32** |
| **C** | `7cfc9f`（全小写，**大小写敏感**） | `grep -r -I -l -e 7cfc9f lead docs/re` | **6** |
| **D** | `7CFC9F`（全大写，**大小写敏感**） | `grep -r -I -l -e 7CFC9F lead docs/re` | **79** |
| **E** | `007CFC9F`（EIP 8 位写法） | `grep -r -I -i -l -e 007CFC9F lead docs/re` | **60** |

> 口径 A/B/C 已满足并**超过** TASK §2 Q2「至少用两种口径（`7CFC9F`、`0x7CFC9F`、`7cfc9f`）」的硬要求；
> 另补 D（大小写敏感大写）与 E（EIP 写法），共 5 种。
> 口径 C 的 6 个命中里 3 个是本轮 W9 自产物（`TASK.md`、`_w9_q2.py`、`_w9_q2_out.txt`），
> 真正既有的只 3 个：`lead/goal2_rc4_frameproof_20261022/REPRO_AND_RISK.txt`、
> `…/XVERIFY_S544_ae38d56c/V3/census_check.py`、`…/recheck_calc.py`
> （`_w9_q2_out.txt:98-105`）——说明**小写写法确有独立命中，不是靠 A 的大小写不敏感兜出来的**。

补充四种口径（为定位「函数本身」而非仅 EIP）：

| 口径 | 写法 | 命中文件数 | 出处 |
|---|---|---|---|
| F-HEAD | `7CFB13` | 27 | `_w9_q2_out.txt:140-156` |
| F-HEAD0x | `0x7CFB13` | 11 | `_w9_q2_out.txt:157-169` |
| F-TAIL | `7CFE1B` | 5 | `_w9_q2_out.txt:170-176` |
| F-NAME | `sbh_alloc_block` | 29 | `_w9_q2_out.txt:177-193` |
| F-WIN | `7CFC9B`（PW-1 窗） | 43 | `_w9_q2_out.txt:194-210` |

### 4.2 净数（排除本轮自产物与 `.mimosa` hook 缓存）

`_w9_q2_out.txt:212-221` + 本会话补充独立复核命令
`grep -rIil --exclude-dir=W9_SINGLESTEP_7CFC9F "7CFC9F" lead docs/re | grep -v "\.mimosa" | wc -l`：

```
all files（口径 A）                       = 81
minus W9_SINGLESTEP_7CFC9F/ 自产物        = 72
minus W9 自产物 AND .mimosa hook 缓存      = 66
    of which docs/re                     = 10
    of which lead                        = 56
```

> 注：探针内 A 打印 80、补充复核打印 81，差 1 是本轮 W9 目录下新建文件被
> 后续 grep 计入；排除 W9 自产物后两者同为 72 → 净数 66 稳定。
> 这一差异已如实登记，不抹平。

### 4.3 具体「既有分析」证据（**不是查不到，是覆盖极密**）

`docs/re/` 净命中 10 个文件（`_w9_q2_out.txt:214`），关键者：

| 文件:行 | 内容要点 |
|---|---|
| `docs/re/except_zc11_forensics.md:14-16` | EIP `0x007CFC9F` 落在 `.text`，函数为 `__sbh_alloc_block`（入口 `0x007CFB13`）；`mov ecx,[edx]`；调用链 |
| `docs/re/except_zc11_forensics.md:112-120` | `### 2.2 函数识别`，逐条给出 `007CFB13: 55 push ebp` / `8BEC` / `83EC14` / `A1948BB700`（**与本轮 `e.rd` 逐字节相同**） |
| `docs/re/except_zc11_forensics.md:160` | `★ 崩溃于 +0x18C = 0x007CFC9F`（**与本轮 `+0x18C` 相同**） |
| `docs/re/sbh_freelist_deep_dive.md:30-38` | `## [1] __sbh_alloc_block 逐指令语义`；入口 `0x007CFB13`；`0x7CFB13 push ebp;mov ebp,esp;sub esp,0x14 标准序` |
| `docs/re/sbh_freelist_deep_dive.md:74-75` | `0x7CFC9B mov edx,[ecx+edi*8+4]` / `0x7CFC9F mov ecx,[edx]` |
| `docs/re/ARCHITECTURE_ATLAS.md:2257,2318,4635,4727` | `__sbh_alloc_block @ 0x007CFB13` 命名与 `0x007C9484: E8 8A 66 00 00 call 0x007CFB13` |
| `docs/re/rtrack_bridge_h1rm.md:22-41` | 同函数 `__sbh_alloc_block @ 0x7CFB13` 摘链段，`{0x7CFC9B,0x7CFC9F,0x7CFCA3}` 三码 EIP 集 |
| `docs/re/crt_memory_pool_deep_dive.md:48,129` | 调用链与 `call 0x007CFB13` |
| `docs/re/iface_mimo_re.md:14,271` | 「except 取证定谳」、EIP 集 |
| `docs/re/LESSONS_20261003_RE_INSTRUMENTS.md:75,151` | `0x7CFC9F` 作为反汇编金样例 G1；`0x007CFC9B` 处 dump=CC/onfile=8B 的运行态补丁注记 |

`lead/` 净命中 56 个文件（含 `GOAL_THREE_TARGETS_20261018.md`、
`ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md`、`goal2_sbh_guard_20261020/{sbh_guard.diff,sbh_guard_snippet.txt}`、
`goal3_p1sbh_merge_20261020/_work/sbh*.diff`、5 份 `except_post_*.txt` 等），
清单见 `_w9_q2_out.txt:215`。

### 4.4 「crashspec 工作范围」的专门核（关键：语料不在两个搜索目录里）

TASK 问的是「是否在既有的 **crashspec 工作范围**里被分析过」。
按 §6「否定性/存在性事实先用文件系统命令核」，本轮先用
`find . -iname "RC_SPEC*" -o -iname "*crashspec*" …` 定位到该语料实际在
**`out/re_work/work_chain/CONTINUE_20261003/crashspec{,v3,v4}/`**（不在 `lead/`、`docs/re/` 内），
再对这三目录单独 grep（`_w9_q2_out.txt:223-226`）：

```
pattern=7CFC9F        → 命中文件 11 个
pattern=7CFB13        → 命中文件 11 个
pattern=sbh_alloc_block → 命中文件  7 个
```

含 `RC_SPEC.md`、`RC_SPEC_V2.md`、`RC_SPEC_V3.md`、`RC_SPEC_V4.md`、
`claims_rc_guard_windows.txt`（+ `.bak_pre_13_20261018`）、`AUDIT_MERGE_TABLE.md`、
`M1_RULING_ANNOTATION.md`、`V3_REGRESSION_LEDGER.md` 等。

其中 `out/re_work/work_chain/CONTINUE_20261003/crashspec_v4/RC_SPEC_V4.md:109` 明写：

> **v2 补充 `[实证]`**（S5，capstone 5.0.7 全函数反汇编，函数体 275 条指令）：逐条印证上表；
> 函数边界 `0x7CFB13–0x7CFE1B`、线性序唯一 `ret` 在 `0x7CFE1B`，`0x7CFE1C` 为另一函数
> （region 扩容/新建，`raw/13`）

`RC_SPEC_V4.md:158` 又写「`__sbh_alloc_block`（`0x7CFB13–0x7CFE1B`，函数体 275 条指令）」；
`RC_SPEC_V4.md:20` 定义 PW-1 = `0x7CFC9B–0x7CFCA0` 6B 窗（`8B 54 F9 04 8B 0A`）；
`RC_SPEC_V4.md:682` 列 13 条 claims，其中 #4 = `0x7CFC9F`。

**结论：该函数不仅被分析过，而且是 `crashspec` / `RC_SPEC_V1→V4` 整条工作线的核心对象
（PW-1 守卫窗口、`claims_rc_guard_windows.txt` 断言、275 条全函数反汇编、区域扫描语义）。
「未被覆盖」被多口径搜索明确否定。**

---

## 5 · 与旧分析 `SINGLESTEP_0x7CFC9F_ANALYSIS.md` 的关系（默认怀疑 → 逐条核对）

`TASK.md:31` 要求「默认怀疑它」。本轮对 **Q2 范围内**旧分析的唯一实质断言逐字节复核：

旧件 `SINGLESTEP_0x7CFC9F_ANALYSIS.md:43`：

> 函数归属：**内嵌 MSVC 6.0 CRT `__sbh_alloc_block`，入口 `0x7CFB13`，函数体
> `0x7CFB13`–`0x7CFE1B`（唯一 `ret` 在 0x7CFE1B）**，与 RC_SPEC_V4 E1-4/S5 全函数反汇编一致。

| 旧分析断言 | 本轮独立实跑 | 判定 |
|---|---|---|
| 入口 `0x7CFB13` | `e.rd(0x7CFB13,5)=55 8B EC 83 EC`，前置 `0x7CFB12=C3 ret`，3 处 `call` xref | ✅ 一致 |
| 函数体止 `0x7CFE1B` | 尾声 `…5F 5E 5B C9 C3`，`0x7CFE1C` 为下一函数首指令 `A1 94 8B B7 00` | ✅ 一致 |
| 唯一 `ret` | `e.func_rets(0x7CFB13,0x7CFE1C)` = **1**；区间内 4 个 `C3` 数据字节均属 `83 C3 14` | ✅ 一致 |
| 275 条（旧件 §1.1 引 RC_SPEC_V4） | `by()` 内 `[0x7CFB13,0x7CFE1C)` = **275**，完全连续无 gap | ✅ 一致 |
| 崩溃点 `+0x18C` | `0x7CFC9F − 0x7CFB13 = 0x18C` | ✅ 一致 |

⇒ **Q2 范围内未发现旧分析的实质错误**（`substantiveDefect = false`）。
按 `TASK.md` §4 判定档，本件为 **CONFIRMED**：Q2 三条结论每一条都有
「反汇编地址 + 原始字节」或「文件:行」支撑，且 `e.func_rets` 为实跑。

> 诚实边界：旧分析 `:43-47` 还写了「崩溃点=从 side-list 取出自由块读 size」、
> `Esi=0x7FFFFFFF` 位图掩码、`Edi` 语义、class 1 勘误、调用链、帧一致性等
> **语义/机制断言**。这些属 Q1/Q3/Q4 范围，**本轮（Q2）未逐条重验 → 未验**，
> 不因函数归属对得上就顺带背书。旧分析 §0 的「外源陷阱/施动者 INSUFFICIENT」等
> 机制结论同样**不在 Q2 判定范围内**，本件不置评。

---

## 6 · 诚实账 / 未验项

1. **自己实跑并自证**：头部 4 项哈希与字节数、`e.coverage` / `e.IB` / 节表、
   `e.rd(0x7CFC9F,32)`、`0x7CFC9F in e.by()`、6 个序言候选、`ret` 对齐、
   `e.func_rets`（1 ret + 3 ret 交叉）、275 条连续解码、4 个内部 `C3` 数据字节、
   3 处 `call 0x7CFB13` xref、尾跳检查、5+5 种 grep 口径与净数、
   crashspec 三目录 grep。全部落盘于 `_w9_q2_out.txt`（230 行）与本会话补充命令输出。
2. **判为「未验」**：
   - 符号名 `__sbh_alloc_block` 及「MSVC 6.0 CRT / SBH」来源归属 —— 采自既有分析命名
     （`docs/re/except_zc11_forensics.md:112` 等），非本轮反汇编可独立证明的符号。
   - 旧分析 §1.1 的 size-class / 位图掩码 / 调用链 / 帧一致性等语义断言（Q1/Q3 范围）。
   - 该函数运行期是否被 hook / 补丁改写（本轮只读磁盘镜像，零真机、零活进程读取；
     `docs/re/LESSONS_20261003_RE_INSTRUMENTS.md:151` 已记 `0x7CFC9B` 曾有 `dump=CC onfile=8B`
     的运行态差异，本件不延伸判定）。
   - Q4 的二选一（EXCEPT 件是否 107 份基线之一）—— 本件只报告实算哈希前缀，不判定。
3. **未把「查不到」当「不存在」**：`0x7CF465` 这一「`sub esp,imm` 且前方 ret」候选被逐条
   列出并以 16 个中间 ret 排除；4 个内部 `C3` 字节逐条定位到 `add ebx,0x14`；
   `crashspec` 语料先 `find` 定位再 grep，未因 `lead/`、`docs/re/` 里没有而断言不存在。
4. **两处数字微差如实登记**：口径 A 探针打印 80 / 补充复核 81（本轮 W9 自产物增量），
   排除 W9 后同为 72；`F-TAIL 7CFE1B` 的 5 个命中里 3 个是本轮 W9 自产物，
   **真正既有的 `0x7CFE1B` 字面命中只有 2 个**（`lead/dropped611/raw/dis_007C8E17.txt`、
   `dis_007CA564.txt`，见 `_w9_q2_out.txt:170-176`）—— 但 `RC_SPEC_V4.md:109,158`
   以 `0x7CFB13–0x7CFE1B` 形式记载该边界，故「边界被既有分析覆盖」仍成立。
5. **零真机 / 零采样注入 / 零活进程读取 / 零既有文件改动**：仅新建
   `Q2_FUNCTION.md`、`_w9_q2.py`、`_w9_q2_out.txt`、`_w9_q2_explore.py`、
   `_w9_q2_explore_out.txt`，全部在唯一写域 `W9_SINGLESTEP_7CFC9F/` 内；未 commit、未 push。
6. **探针独立性**：`python -I -X utf8 lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q2.py`
   单跑 `EXIT=0`、2m6s（`< 8 min` 上限）、230 行输出后自行退出；未全盘扫 `.text`
   （仅在 `e.coverage` 构造时按 `ra2tool.py:92-108` 建一次全 `.text` 重同步流，
   这是 `e.by()`/`e.func_rets` 的固有前置，业务检索窗口限定在 `[0x7CF000,0x7D0113]`）。

---

## 7 · 交付物

| 文件 | 内容 |
|---|---|
| `Q2_FUNCTION.md` | 本件（Q2 正文） |
| `_w9_q2.py` | Q2 定谳探针（`python -I -X utf8` 独立跑完即退出） |
| `_w9_q2_out.txt` | `_w9_q2.py` 的完整 stdout（230 行） |
| `_w9_q2_explore.py` / `_w9_q2_explore_out.txt` | 前置探索探针（0x7CFA80–0x7CFE80 逐指令窗口 + 覆盖率），357 行 |
