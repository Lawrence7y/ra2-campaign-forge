被核对象 = gamemd.exe + EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360
EXCEPT 件 SHA256 = 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251，字节数 = 26405
Engine 自证 = COVERAGE 99.998375677293% / IMAGEBASE 0x400000
回件时刻 = 2026-11-06 02:34:24

# Q3 · `EXCEPTION_SINGLE_STEP` 但 `EFlags` 无 TF 位 —— 机制定谳

> 判档：**PARTIAL**。位分解、字段来源、③的排除、Esi/Edi 语义、④中三项字节排除均有
> 「反汇编地址 + 原始字节」或「文件:行」支撑；但**本件没有 DR6 / DR0-3 / DR7 /
> ExceptionInformation**，故 ① 与 ② 的机制身份**无法定谳**，只能给判据与「未验」。
> 旧分析 `SINGLESTEP_0x7CFC9F_ANALYSIS.md` 未发现改动其 Q3 结论的**字节级实质错误**；
> 发现 1 处措辞错误 + 2 处置信度越界，逐条列于 §7（非实质，`substantiveDefect=false`）。

---

## 0 总判（先给答案）

**「TF=0 却是单步异常」不是悖论，是把两个不同对象混为一谈造成的假问题：**

1. `EXCEPTION_SINGLE_STEP = 0x80000004` 是 Windows 给 **x86 #DB（int 1）整类调试异常**的命名。
   TF 单步只是 #DB 的**一个**触发源；**DR0-3 硬件断点（执行/数据/I/O）、ICEBP(0xF1)、
   General Detect 都不需要 TF=1**。所以「无 TF」对 DR 系毫无矛盾，不需要任何解释。
2. 更关键：本件打印的 `EFlags:00000286` **不是陷阱发生瞬间 CPU 的活 EFLAGS**，而是
   游戏最后机会过滤器从**异常帧 `CONTEXT`** 里读出来的 `CONTEXT.EFlags`（偏移 +0xC0）。
   交付给 handler 的 CONTEXT 里的 TF 是否等于陷阱前的 TF，是 OS 派发语义问题，
   **本件无字段可判**。因此 `TF=0` 连「TF 单步」这一子机制都排除不掉。
3. 现场 `Eip=0x7CFC9F` 在**两种**主流机制下字节级同构：
   - TF 单步 = **trap-after**：`0x7CFC9B`（4B）刚执行完 → EIP=下一条 `0x7CFC9F`；
   - DR **执行**断点 @0x7CFC9F = **fault-before**：EIP 正指向尚未执行的 `0x7CFC9F`。
   两者都让 `Edx=0x0E73276C` 已载入、`Eip=0x7CFC9F`，**EIP 不带判别力**。

⇒ 正确的机制表述应是：**这是一次 #DB，其触发源在本件上不可判定（TF / DR-exec / 其它均开放）；
「无 TF」只是把一个子机制的可能性表述得更复杂了，并没有缩小或扩大整个候选集。**

---

## 1 强制头部与自证（全部自己实跑）

| 项 | 值 | 来源 |
|---|---|---|
| gamemd.exe SHA256 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | `_w9_q3_out.txt:8`（hashlib 实算） |
| gamemd.exe 字节数 | 4825360 | `_w9_q3_out.txt:9` |
| EXCEPT 件 SHA256 | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` | `_w9_q3_out.txt:10` |
| EXCEPT 件 字节数 | 26405 | `_w9_q3_out.txt:11` |
| Engine 自证 | COVERAGE 99.998375677293% / 1394120 insns / 66 resync-fails / IMAGEBASE 0x400000 | `_w9_q3_out.txt:14-16` |
| `.text` | `[0x401000, 0x7E1000)` raw=0x1000 size=0x3E0000 | `_w9_q3_out.txt:17` |
| `fo(0x7CFC9F)` | `0x3CFC9F` = VA − 0x400000 | `_w9_q3_out.txt:108` |
| 崩点 32 字节 vs 证据件 | 32/32 零差异（差异索引=`[]`） | `_w9_q3_out.txt:109-111` |
| `0x7CFC9F in e.by()` | True，`mov ecx, dword ptr [edx]` size=2 | `_w9_q3_out.txt:112-113` |
| 回件时刻 | 2026-11-06 02:34:24 | `date '+%Y-%m-%d %H:%M:%S'` |

**实跑命令（三条主探针，均 `python -I -X utf8` + 绝对路径，各自 EXIT=0 自退出）：**

```
python -I -X utf8 D:\Project\ra2-campaign-forge\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\_w9_q3.py
   -> EXIT=0 ; _w9_q3_out.txt 307 行 ; 140.12 s   （[A]-[I]：SHA/位分解/字段普查/崩点/函数前段/导入表/串 xref）
python -I -X utf8 ...\_w9_q3_handler.py
   -> EXIT=0 ; _w9_q3_handler_out.txt 237 行 ; 100.19 s （[J]-[N]：handler 打印值来源 / RaiseException IAT 与调用点）
python -I -X utf8 ...\_w9_q3_final.py
   -> EXIT=0 ; _w9_q3_final_out.txt 96 行 ; 66.67 s  （[O]-[Q]：±0x20 字节排除 / 两处调用点实参 / 异常码表）
```

另有 5 次内联 `python -I -X utf8 -c` 有界核（格式串 VA、handler xref、RaiseException 模板、
IAT 解析、0x80000004 常量、直接分支落点），输出与结论并入下列 §3/§5，命令原文见 §9。

**文件系统事实（按 TASK.md §6 先用 `find`/`sha256sum`，未上全仓 Python 遍历）：**

```
find . -type f -name "except_post_*.txt" | wc -l                      -> 113
find . -type f -name "except_post_*.txt" -print0 | xargs -0 sha256sum | awk '{print $1}' | sort -u
   -> 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251 （distinct = 1）
```

⇒ 本件 SHA256 **与那批 `except_post` 完全相同**。此事实只登记，**Q4 定谳**（不在本题裁）。
（差额：§555:5475 记 107 份，本探针 `find` 得 113 份，全部同哈希；差额归属亦交 Q4。）

---

## 2 `EFlags = 0x286` 逐位分解（`_w9_q3_out.txt:51-82`）

`0x286 = 0x2 + 0x4 + 0x80 + 0x200`；置位 bits = **[1, 2, 7, 9]**。

| bit | mask | 名称 | 值 | 与本题关系 |
|---:|---:|---|---:|---|
| 0 | 0x000001 | CF | 0 | — |
| 1 | 0x000002 | reserved(恒 1) | **1** | 正常 |
| 2 | 0x000004 | PF | **1** | 正常 |
| 3 | 0x000008 | reserved | 0 | — |
| 4 | 0x000010 | AF | 0 | — |
| 5 | 0x000020 | reserved | 0 | — |
| 6 | 0x000040 | **ZF** | **0** | ★ 旧分析误标为 1，见 §7 |
| 7 | 0x000080 | **SF** | **1** | ★ 旧分析漏标，见 §7 |
| **8** | **0x000100** | **TF Trap Flag** | **0** | **本题核心：报告字里无 TF** |
| 9 | 0x000200 | **IF** | **1** | 中断使能，用户态常态 |
| 10 | 0x000400 | DF | 0 | — |
| 11 | 0x000800 | OF | 0 | — |
| 12/13 | 0x1000/0x2000 | IOPL | 0/0 | ring3 |
| 14 | 0x004000 | NT | 0 | 非任务嵌套 |
| 15 | 0x008000 | reserved | 0 | — |
| **16** | **0x010000** | **RF Resume Flag** | **0** | 非「恢复执行」路径 |
| **17** | **0x020000** | **VM Virtual-8086** | **0** | 非 V86；`CS=0x23` 亦合 `_w9_q3_out.txt:37` |
| 18 | 0x040000 | AC | 0 | — |
| 19 | 0x080000 | VIF | 0 | — |
| 20 | 0x100000 | VIP | 0 | — |
| 21 | 0x200000 | ID | 0 | — |

**逐位结论**：TF=0、RF=0、VM=0、IF=1；SF=1、PF=1、reserved-bit1=1、ZF=0。
`0x286` 是一个**完全正常的用户态标志字**（`CS=0023`、ring3、中断开），没有任何
「调试态残留」的特征位。

**★ 勘误（字节依据）**：旧分析 `SINGLESTEP_0x7CFC9F_ANALYSIS.md:51` 写
「`EFlags=0x286`（IF|ZF|PF，无 TF）」—— `0x286 & 0x40 = 0`、`0x286 & 0x80 = 0x80`，
即 **ZF=0、SF=1**，旧件把 SF 误标成 ZF。属措辞精度缺陷，不改变任何结论（TF=0 仍正确）。

---

## 3 决定性前提纠正：`0x286` 是「交付给 handler 的 `CONTEXT.EFlags`」

这是本题**最要紧的一条**，也是我独立反汇编出来的（不采信旧件 §2#5 的转述）：

### 3.1 打印串与 xref（自己 `raw.find` + 节表反查 + stream 单遍 xref）

| 串 | raw off | VA | 内容 | 主要 xref |
|---|---|---|---|---|
| `Eip:%08X\tEsp:%08X\tEbp:%08X` | 0x421EA0 | 0x821EA0 | `_w9_q3_handler_out.txt:9` | `push 0x821ea0 @0x4C8B92` |
| `Eax:%08X\tEbx:%08X\tEcx:%08X` | 0x421E80 | 0x821E80 | `:11` | `push 0x821e80 @0x4C8BE0` |
| `Edx:%08X\tEsi:%08X\tEdi:%08X` | 0x421E60 | 0x821E60 | `:12` | `push 0x821e60 @0x4C8C2E` |
| **`EFlags:%08X`** | 0x421E50 | **0x821E50** | `:10` | **`push 0x821e50 @0x4C8C6E`** |
| `Exception occurred at %08X` | 0x421F78 | 0x821F78 | `:14` | `push 0x821f78 @0x4C898B` |
| `\r\nBytes at CS:EIP (%08X)  : ` | 0x421DE4 | 0x821DE4 | `:185` | `push 0x821de4 @0x4C8D1B` |

### 3.2 `EFlags` 的取数指令（字节级）

```
0x4C8C63  8b8dc0000000  mov ecx, dword ptr [ebp + 0xc0]      ; ★ 唯一喂给 EFlags printf 的值
0x4C8C69  8d542434      lea  edx, [esp + 0x34]
0x4C8C6D  51            push ecx
0x4C8C6E  68501e8200    push 0x821e50                        ; "EFlags:%08X \r\n"
0x4C8C73  52            push edx                             ; 输出缓冲
0x4C8C74  ffd3          call ebx                             ; sprintf 类
```
（`_w9_q3_handler_out.txt:159-164`）

全组寄存器取数（`_w9_q3_handler_out.txt:87-164`）与 Win32 x86 `CONTEXT` 字段偏移**逐项吻合 10/10**：

```
+0x9C Edi  +0xA0 Esi  +0xA4 Ebx  +0xA8 Edx  +0xAC Ecx  +0xB0 Eax
+0xB4 Ebp  +0xB8 Eip  +0xBC SegCs  +0xC0 EFlags  +0xC4 Esp  +0xC8 SegSs
实测：0x4C8B85 mov eax,[ebp+0xB8]=Eip ; 0x4C8B7F mov edx,[ebp+0xC4]=Esp ;
      0x4C8B79 mov ecx,[ebp+0xB4]=Ebp ; 0x4C8C63 mov ecx,[ebp+0xC0]=EFlags ; ...
```

`[ebp+0xB8]`（=CONTEXT.Eip）还被三处复用，进一步锁死「这是同一份异常 CONTEXT」：
`0x4C88DF` 喂 `IsBadCodePtr`（IAT 0x7E11B4）、`0x4C8980` 喂「Exception occurred at」、
`0x4C8D23` 喂 `IsBadReadPtr`（IAT 0x7E115C）+ `0x4C8D56 mov dl, byte ptr [edi]` 读 32 字节
（`_w9_q3_handler_out.txt:49-52, 70-75, 196-232`）。IAT 已亲解析：
`0x7E115C=IsBadReadPtr`、`0x7E1160=lstrcatA`、`0x7E11B4=IsBadCodePtr`、
`0x7E12C0=RaiseException`（内联 `-c` 实跑输出）。

### 3.3 推论（严格区分「已证」与「未验」）

- **已证（字节）**：`except.txt` 里 `EFlags:00000286`、所有寄存器、`Bytes at CS:EIP` 的 32 字节、
  `Stack dump` 全部来自**异常派发给用户态过滤器时的那一份 CONTEXT**，不是 trap 瞬间 `pushfd`
  的活标志，也不是 handler 自己的 EFLAGS。
- **未验（本件无字段）**：这份 CONTEXT 的 `EFlags` 是否保留了**陷阱前**的 TF。
  x86 在进入 #DB handler 时会清活 EFLAGS 的 TF（防止 handler 自身被单步），Windows 在向
  用户态异常处理器派发时对 CONTEXT.EFlags.TF 的处理属 **OS 派发约定**——本件既无
  trap-frame 原始 EFLAGS，也无 DR6，**无法自证**。按 TASK.md §6「查不到 ≠ 不存在」，
  不能把 `TF=0` 当成「陷阱前 TF=0」。
- ⇒ **TASK.md:55 的前提「若 TF=0，硬件单步陷阱不可能触发」只在「TF 子机制 + 已证明
  CONTEXT 保留陷阱前 TF」两个附加条件下成立**；本件一个都没给。旧件 §0/§1.2 把
  `#DB 入栈清 TF` 写成既成事实（`:51`），属把架构假设当结论，本件不支持也不反对，标未验。

### 3.4 现场台账里那句前提本身就是错的（源头定位）

`lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:1898` 原文：
「`EFlags=0x286 无 TF 位=非 DR 非调试端口——debugport_enum 全机零命中`」。
- 「无 TF 位 ⇒ 非 DR」是**非推论**：DR0-3 断点由 DR7 使能位控制，与 EFLAGS.TF 完全正交；
- 「debugport 零命中 ⇒ 非 DR」亦不成立：内核态/驱动或 `SetThreadContext` 写
  `CONTEXT_DEBUG_REGISTERS` 不需要用户态 debug port。
⇒ **「TF=0 悖论」是这条现场记录引入的假前提**，不是异常本身的属性。TASK.md §2 Q3  inherited
了这个框架；本回件按机制正解纠正之。

---

## 4 机制正解：`EXCEPTION_SINGLE_STEP` = #DB 类，TF 只是触发源之一

### 4.1 异常码确实是 0x80000004（排除「handler 误报」）

- 字符串池 `0x820F74` 亲读 = `EXCEPTION_SINGLE_STEP\r\r\nDescription: A trace trap or other
  single-instruction mechanism signaled that one instruction has been executed.`
  ——与 `except.txt:1-3` **逐字一致**（内联 `-c` 实跑）。
- `.rdata` 异常码表 `0x7E8840..0x7E888C` 亲读（`_w9_q3_final_out.txt:73-77`）：
  ```
  [0x7E8840] 0x80000003  0x80000002  0xC000008D  0xC000008E
  ...
  [0x7E8880] 0x80000004  0xC00000FD  0xFFFFFFFF  0x00000000
  ```
  `0x7E8880` 处 dword 实读 = `04 00 00 80`（内联 `-c`），即 **0x80000004**。
  `0x80000003`（BREAKPOINT）是**相邻但不同**的表项 ⇒ 不会把 INT3 说成 SINGLE_STEP。
- handler 按 `ExceptionRecord->ExceptionCode` 查表（表+串+逐字一致三者互证）。
  **未验**：查表循环本体我未逐条反汇编（`_w9_q3_final_out.txt:93` 已登记）。

### 4.2 #DB 触发源集合（机制分类）

| #DB 源 | 需要 TF=1？ | EIP 语义 | 与本件兼容？ |
|---|---|---|---|
| TF 单步 | **是** | trap-after：0x7CFC9B 完成 → EIP=0x7CFC9F | **兼容** |
| DR0-3 **执行**断点 @0x7CFC9F | 否 | fault-before：EIP=0x7CFC9F | **兼容** |
| DR0-3 数据/I/O 断点 | 否 | 按 x86 约定为 trap（EIP 指向下一条） | 倾向不符，但本件无 DR6 ⇒ 未验 |
| ICEBP / 0xF1 | 否 | trap-after | **字节排除**（§5④b） |
| General Detect（DR7.GD） | 否 | fault | 未验 |

⇒ **「无 TF」对第 2 行根本不构成矛盾**；对第 1 行，只要交付 CONTEXT 时 TF 已被清（OS
派发语义，未验），也不构成矛盾。`EXCEPTION_SINGLE_STEP` 这个名字里的 "single-step"
是 Windows 对 #DB 的历史命名，不是「TF 一定被置过」的断言。

### 4.3 EIP 的「退化性」——为什么 ① 和 ② 在本件上不可区分

```
0x7CFC98  8b4df4        mov ecx, dword ptr [ebp - 0xc]        (末址 0x7CFC9B)
0x7CFC9B  8b54f904      mov edx, dword ptr [ecx + edi*8 + 4]  (末址 0x7CFC9F) ★ 唯一载入 Edx 的指令
0x7CFC9F  8b0a          mov ecx, dword ptr [edx]               (崩点，2B)
```
（`_w9_q3_out.txt:145-153`）

现场 `Edx=0x0E73276C`（`_w9_q3_out.txt:48`）说明 `0x7CFC9B` **已执行完**。
- TF trap-after：EIP = 0x7CFC9F ✓
- DR-exec fault-before @0x7CFC9F：EIP = 0x7CFC9F ✓
两者产生**逐字节相同的 CONTEXT**（除 DR6 外），而 DR6 恰是本件没有的字段。
⇒ **判别 ①/② 的唯一硬判据是 `DR6.BS`（TF）vs `DR6.B0..B3`（DR），本件零命中 ⇒ 未验。**
（旧分析 `SINGLESTEP_0x7CFC9F_ANALYSIS.md:51` 亦指出两者时序，但它据此给「置信度高」，见 §7。）

补充：`0x7CFC9F` **不是任何直接 call/jmp 的落点**（内联 `-c` 全 `.text` 扫描：
`direct call/jmp targets == 0x7CFC9F : 0 []`），前序 `0x7CFC9B` 顺序落下 ⇒
不存在「call 返回地址恰好=崩点」这类第三种解释（Q1 亦已定谳）。

---

## 5 四候选逐条判据（可否被这份证据支持 / 排除）

> 统一说明：本件 `token` 普查（`_w9_q3_out.txt:84-105`）显示
> `Dr0..Dr7 / DR0 / DR6 / DR7 / ExceptionInformation / ExceptionFlags / ExceptionRecord /
> NumberParameters / ExceptionAddress / CONTEXT / Debug` **全文零命中**；
> 只有 `EFlags`（:15）与寄存器/Bytes/Stack dump。
> **这是「报告没印」，不是「寄存器当时为零」**——按 TASK.md:109-110 铁律，不得当成排除证据。

### ① `SetThreadContext` 置 TF 后又清掉（外部 agent 布单步）

| 判据 | 内容 | 本件是否具备 |
|---|---|---|
| **支持所需** | 崩溃线程 `DR6.BS=1`；或崩溃前采到 `EFlags.TF=1` 的活样本；或可核的外部 agent 调用记录 | **全部缺**（无 DR6 字段、无活进程可读、无 agent 日志） |
| **排除所需** | `DR6.BS=0 且 Bn=1`（⇒ DR 系）；或 trap-frame 原始 EFLAGS 显示陷阱前 TF=0 且该 CONTEXT 未改写 | **全部缺** |
| 时序兼容性 | `0x7CFC9B` 末址=0x7CFC9F，trap-after 成立，`Edx` 已载入 | **具备**（`_w9_q3_out.txt:151-153`） |
| 施动者静态面 | `gamemd.exe` 导入表 372 项，调试/异常相关仅 3 项：`SetUnhandledExceptionFilter` / `RaiseException` / `UnhandledExceptionFilter`；**`SetThreadContext`=False、`GetThreadContext`=False、`SuspendThread`=False、`AddVectoredExceptionHandler`=False、`IsDebuggerPresent`=False** | **具备**（`_w9_q3_out.txt:272-285`） |

**结论：不能支持，也不能排除 ⇒ 未验。**
两点机制订正：(a) 「后又清掉」并非必要步骤——#DB 入口 CPU 清活 TF、OS 派发时对
CONTEXT.EFlags.TF 的处理（未验）会自然产生 `TF=0`；(b) 若 ① 成立，**施动者必在
`gamemd.exe` 之外**（该二进制根本不导入 `SetThreadContext`），但「是哪一家外部组件」
本件零证据，旧件 §2 残留名单（`SINGLESTEP_0x7CFC9F_ANALYSIS.md:68`）属推测，不采信。

### ② DR0-3 执行断点命中

| 判据 | 内容 | 本件是否具备 |
|---|---|---|
| **支持所需** | 崩溃进程 `DR6.B0..B3` 置位、`DR0..3` 含 0x7CFC9F、`DR7` 对应 L/G 使能；或 fault-before 语义（已具备） | DR 值**全缺**；fault-before 语义具备 |
| **排除所需** | 崩溃进程 `DR6=0 / BS=1`，或可信的崩溃态 `DR0-7` 全零读 | **全缺** |

**结论：不能支持，也不能排除 ⇒ 未验（TASK.md 四候选中与 ① 并列开放）。**
- 旧件 §2#3（`:61`）把「DR0-DR7=0」判为**不可用**是对的，理由我也独立核到：
  该读数出自 `gamemd_crawl.dmp`（14:11 卡 logo 趟，**非** 13:52 崩溃进程），
  且看门狗对 WoW64 线程读 `CONTEXT_DEBUG_REGISTERS` 常得全零。
- 现场台账 `:1967`「有组件在用调试寄存器/单步机制盯游戏进程」是**推测**，本件无 DR 字段可证。
- **TASK.md 四候选之外的重要遗漏**：`0x7CFC9F` 是 `mov ecx,[edx]`（一次内存**读**），
  与项目 PW-1/PW-2 守卫窗对自由块节点的关注天然吻合，**DR 数据读断点**是同族第三变体。
  按 x86 约定数据断点为 trap（EIP 应指向 0x7CFCA1），倾向与观测不符；
  但本件无 DR6，**不写死排除，标未验**（并入 ④）。

### ③ `RaiseException(EXCEPTION_SINGLE_STEP, ...)` 手工抛

**这是四候选中唯一能用字节给出明确排除的一条（对「游戏二进制自抛」）。**

| 判据 | 实跑结果 | 出处 |
|---|---|---|
| `RaiseException` 是否导入 | **是**，IAT 槽 `0x7E12C0`（亲解析 = `KERNEL32.dll!RaiseException`） | `_w9_q3_handler_out.txt:177,180` |
| 全 `.text` 中 `call [0x7E12C0]` | **恰好 2 处**：`0x7D2F92`、`0x7DB8A0` | `_w9_q3_handler_out.txt:180` |
| 全 `.text` 立即数 `== 0x80000004` | **0 条**（`imm_hits=[]`） | `_w9_q3_handler_out.txt:179` |
| 全文件小端 `0x80000004` 出现 | 5 处，均在 `.rdata/.data`（含异常码表 `0x7E8880`），**无一处是代码立即数** | 内联 `-c` 实跑 |
| 调用点 1 的第一实参 | 模板 `0x7F9928` 首 dword 亲读 = **`0xE06D7363`**（MSVC C++ 异常 `"msc"|0xE0000000`），flags=1、nArgs=3、magic `0x19930520` ⇒ `__CxxThrowException`，非 SINGLE_STEP | `_w9_q3_final_out.txt:18-43` + 内联 `-c` |
| 调用点 2 的第一实参 | `push dword ptr [ebp+0x10]`（运行时参数），静态无 0x80000004 常量来源 | `_w9_q3_final_out.txt:46-64` |
| 结构性判据（最硬） | `RaiseException` 是**同步软件异常**，交付的 `CONTEXT.Eip` = 调用方 `call` 之后那条指令，`ExceptionAddress` = RaiseException 返回地址。本件 `CONTEXT.Eip=0x7CFC9F`、`Bytes at CS:EIP` 由 `[ebp+0xB8]` 读出并逐字节亲读（`_w9_q3_handler_out.txt:214-232`），栈首 `00F9C614: 00000113`、返回链 `0x007C9489`（=`call 0x7CFB13 @0x7C9484` +5，`e.rd(0x7C9484,8)=E8 8A 66 00 00 6A 09 8B` 亲读）、`0x007C9452`、`0x007C8E22` ⇒ 一条正常 `new→_nh_malloc→heap_alloc→__sbh_alloc_block` 分配链，**栈上无任何 KERNEL32/RaiseException 帧** | `EXCEPT...txt:20-38`；`_w9_q3_handler_out.txt:196-232`；内联 `-c` |

**结论：`gamemd.exe` 自身手工抛 `0x80000004` ⇒ 排除（有字节依据）。**
残口（诚实登记）：**外部施动者**在本线程内注入一次 `RaiseException` 调用不是本件能排除的，
但那需要先劫持线程（`SuspendThread`/`SetThreadContext`），已折回 ①/② 的施动者问题；
且本件**没有任何支持该剧本的证据**（栈帧干净、无该常量、无注入痕迹）。故记为
「外部伪造 = 未验且零支持证据」，不写成排除。

### ④ 其它（逐子项给字节排除 / 未验）

| 子项 | 判据 | 结论 | 出处 |
|---|---|---|---|
| **a. INT3 / 0xCC 软件断点** | 异常码应为 `0x80000003`（表 `0x7E8840` 是独立表项），且 `±0x20` 窗口内任何**指令起始**处无 0xCC | **排除**（异常码表 + 字节双证） | `_w9_q3_final_out.txt:9,73-77` |
| **b. ICEBP / INT1 / 0xF1** | 若 0xF1 造成 trap-after 且 EIP=0x7CFC9F，则 0xF1 必须是 `0x7CFC9E` 处的 1 字节独立指令。实读 `e.rd(0x7CFC9E,1)=04`、`0x7CFC9E in by()=False`（是 `8B 54 F9 04` 的 disp8）；窗口内仅两枚可疑字节 `0xF0@0x7CFCA3`（`2B 4D F0` 的 disp8）、`0xF1@0x7CFCA5`（`8B F1` 的 ModRM），**均非指令起始** | **排除** | `_w9_q3_final_out.txt:8-15`；`_w9_q3_out.txt:114-116` |
| **c. RF / VM / V86 相关** | `RF(bit16)=0`、`VM(bit17)=0`、`CS=0x23` | **排除** | `_w9_q3_out.txt:68-69,37` |
| **d. handler 异常类型误报** | 表项 `0x80000004 @0x7E8880` + 描述串 `0x820F74` 与 `except.txt:1-3` 逐字一致；`Exception occurred at`/`Bytes at CS:EIP` 同源于 `[ebp+0xB8]` | **排除**（查表循环本体未逐条反汇编，标局部未验） | `_w9_q3_final_out.txt:72-93`；`_w9_q3_handler_out.txt:49-52,70-75` |
| **e. 崩溃二进制被替换 / 镜像错位** | `e.rd(0x7CFC9F,32)` 与证据件 Bytes 行 **32/32 零差异**；`fo=0x3CFC9F`；handler 从 `[CONTEXT.Eip]` 亲读的 32 字节与磁盘一致 | **排除**（就本异常而言） | `_w9_q3_out.txt:108-111` |
| **f. DR 数据/I/O 断点、DR7.GD、架构级其它** | 需 DR6/DR7；本件零字段 | **未验** | `_w9_q3_out.txt:84-105` |
| **g. 外部 agent 身份 / 是否挂调试端口** | 本件无进程、无端口、无 agent 日志；现场 `:1898` 的 `debugport_enum` 属另一时点且不能排除 DR | **未验** | `ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:1898` |

**④ 汇总**：4 个子项有字节排除（a/b/c/d/e），2 项（f/g）未验。
⇒ 但**排除掉的全是「别的异常码 / 别的指令字节」**，并没有排除 #DB 本身的两个主流触发源。

---

## 6 `Esi=7FFFFFFF` / `Edi=00000001` 是否特征值？

**结论：不是任何陷阱候选的特征值；它们是 `__sbh_alloc_block` 的普通运行态，
且是「请求 class=1 的一次小分配」这一工作负载特征，与异常机制零因果。**
下列整条链是我自己 `e.disasm` + `e.stream` 反汇编出来的（`_w9_q3_out.txt:155-270`），
未采信旧件 `SINGLESTEP_0x7CFC9F_ANALYSIS.md:44` 的文字。

### 6.1 Esi = 位图搜索掩码（class_req 计算链，函数头前 40 条）

```
0x7CFB13  55            push ebp                          ; 序言（Q2 已定谳的函数头）
0x7CFB14  8bec          mov  ebp, esp
0x7CFB16  83ec14        sub  esp, 0x14
0x7CFB2D  8b4508        mov  eax, dword ptr [ebp + 8]     ; req（用户请求字节数）
0x7CFB33  8d4817        lea  ecx, [eax + 0x17]
0x7CFB36  83e1f0        and  ecx, 0xfffffff0
0x7CFB39  894df0        mov  dword ptr [ebp - 0x10], ecx  ; 对齐后的 sizeNeeded
0x7CFB3C  c1f904        sar  ecx, 4
0x7CFB3F  49            dec  ecx                          ; class_req
0x7CFB40  83f920        cmp  ecx, 0x20
0x7CFB43  7d0e          jge  0x7cfb53                     ; >=32 走另一支
0x7CFB45  83ceff        or   esi, 0xffffffff              ; esi = 0xFFFFFFFF
0x7CFB48  d3ee          shr  esi, cl                      ; ★ esi = 0xFFFFFFFF >> class_req
0x7CFB4E  8975f4        mov  dword ptr [ebp - 0xc], esi   ; 存位图掩码
0x7CFB51  eb10          jmp  0x7cfb63
0x7CFB53  83c1e0        add  ecx, -0x20
0x7CFB56  83c8ff        or   eax, 0xffffffff
0x7CFB59  33f6          xor  esi, esi                     ; >=32 支：esi=0
```

`0xFFFFFFFF >> 1 = 0x7FFFFFFF` ⇒ **`cl = class_req = 1`**；
反推 `((req+0x17)&~0xF)>>4 − 1 = 1` ⇒ `((req+0x17)&~0xF) = 0x20` ⇒ **req ∈ [9, 24] 字节**。
该掩码随后在 `0x7CFC47 mov esi,[ebp-0xC]` 重新载入，并在
`0x7CFC7E and ecx, esi` / `0x7CFC5B mov edi,esi` 一路用到崩点 ⇒ **崩点时刻 Esi 是活值**。

**关键反证**：全函数窗口 `[0x7CFB13,0x7CFC9F)` 内**没有任何立即数 `0x7FFFFFFF`**
（`_w9_q3_out.txt:265-270` 只列出 5 条 `0xFFFFFFFF` 立即数：
`0x7CFB45 / 0x7CFB4A / 0x7CFB56 / 0x7CFBFC / 0x7CFC13`）。
⇒ `0x7FFFFFFF` 是**纯算术算出来的运行态值**，不是二进制里烘焙的魔数；
任何「某 agent 以 0x7FFFFFFF 为暗号」的剧本在本二进制层面无锚点。

### 6.2 Edi = 位扫描命中索引（崩点前 24 条）

```
0x7CFC68  33ff          xor  edi, edi                     ; edi = 0
0x7CFC6A  69c904020000  imul ecx, ecx, 0x204
0x7CFC70  8d8c0144010000 lea ecx, [ecx + eax + 0x144]     ; group 基址
0x7CFC77  894df4        mov  dword ptr [ebp - 0xc], ecx
0x7CFC7A  8b4c9044      mov  ecx, dword ptr [eax + edx*4 + 0x44]
0x7CFC7E  23ce          and  ecx, esi                     ; 位图 & 掩码
0x7CFC8F  85c9          test ecx, ecx
0x7CFC91  7c05          jl   0x7cfc98                     ; 命中最高位则出循环
0x7CFC93  d1e1          shl  ecx, 1
0x7CFC95  47            inc  edi                          ; ★ 每次左移 edi++
0x7CFC96  ebf7          jmp  0x7cfc8f
0x7CFC98  8b4df4        mov  ecx, dword ptr [ebp - 0xc]
0x7CFC9B  8b54f904      mov  edx, dword ptr [ecx + edi*8 + 4]  ; ★ edi 就是 class 索引
```

崩点前对 `edi` 的**最后一次写** = `0x7CFC95 inc edi` ⇒ `Edi=1` 表示该位扫描循环
**只自增一次就命中**。`0x7CFC9B` 直接用 `edi*8+4` 索引 freelist 头数组，
与 `Edi=1` 完全自洽；`Ecx=0x0D94F574` / `Edx=0x0E73276C` 都落在这条链的合理值域。

### 6.3 对四候选的判别力

- Esi/Edi **对 ①②③④ 全部无判别力**：它们描述「这次分配请求的是 class 1、命中 class 1
  自由链」，是**被陷阱打断的那条指令自己在算的东西**，不是「谁布下陷阱」留下的签名。
- 二者相关（都等于 1 / 都来自 class_req=1）反而印证「同一份普通分配器状态」。
- 旧件 `:44` 称 `Esi` 不是 freelist 端哨兵而是位图掩码 ⇒ **我独立反汇编确认其正确**；
  对 `:44` 的「请求 class 1（9-24B）」亦由 `0x7CFB33-0x7CFB48` 字节链独立复算得到。
- **未验**：旧件 `:44/:86` 称 ② RC-1（AV `FE00FFFF`）现场 `Esi` 同为 `0x7FFFFFFF`；
  本探针未独立读 `RC_SPEC_V4.md` 的寄存器块，故「两现场同值」标未验。
  即便成立，也只说明是**同一条热分配指令**，不构成陷阱机制证据。

---

## 7 与旧分析 / 现场台账的逐条对照

| # | 旧件位置 | 旧件说法 | 本回件独立判定 | 性质 |
|---|---|---|---|---|
| 1 | `SINGLESTEP_0x7CFC9F_ANALYSIS.md:51` | `EFlags=0x286（IF\|ZF\|PF，无 TF）` | 实算 `ZF=0 / SF=1`，`0x286=IF\|SF\|PF\|reserved-b1`；**SF 误标为 ZF** | 措辞精度缺陷，**非实质**（TF=0 结论不变） |
| 2 | `:51` | 「与 #DB 入栈清 TF 的 CPU 行为一致——对 TF/DR 源充分，不构成排除」 | 该 CPU/OS 语义本件无字段可证；旧件把架构假设写成既成事实 | 证据越界（标未验），但「不构成排除」的**结论**与本件一致 |
| 3 | `:12`（§0 TL;DR） | 「**判定**：真实的外源陷阱…机制判定**置信度高**；施动者身份 INSUFFICIENT」 | 本件无 DR6/DR/ExceptionInformation、无外部 agent 可核证据、无活进程；只能判「#DB 触发源开放集」，**不能收窄成「必为外部调试机制」**，更不能给高置信度 | **置信度/范围越界**（非字节级事实错误） |
| 4 | `:61`（§2#3） | 「DR0-DR7=0 出自 14:11 crawl dump，不是崩溃进程」 | 独立核到该读数确属另一趟；本件亦零 DR 字段 ⇒ 「未排除」结论**与本件一致** | 一致 |
| 5 | `:61` / `:68` | 「DR 执行断点可完美解释两次同 EIP」/ 施动者候选名单 | 「同 EIP」对 TF trap-after 与 DR fault-before **同样完美**（§4.3），故不具排他性；名单属推测 | 过度解读，标未验 |
| 6 | `ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:1898` | 「无 TF 位=非 DR 非调试端口」 | **逻辑非推论**：DR 与 TF 正交；debug port 亦非 DR 必要条件。这是「TF=0 悖论」的源头 | 前提错误（台账层，非旧分析件） |
| 7 | `TASK.md:55` | 「若 TF=0，硬件单步陷阱不可能触发 ⇒ 只能来自 ①…④」 | 仅对 **TF 子机制**成立，且需附加「CONTEXT 保留陷阱前 TF」；对 DR 系，TF=0 是常态，无「不可能」可言。四候选框架本身可保留 | 前提需限定 |

⇒ 未发现改动旧件 Q3 结论的**字节级实质错误**；`substantiveDefect = false`。
§7#1 建议回写订正（与 Q1 回件登记的「措辞精度缺陷」同类）。

---

## 8 诚实账 / 未验清单（不补造）

**已证（本 ask 内实跑）**：
1. 强制头部 4 项 + Engine 覆盖率 + SHA 断言通过（`_w9_q3_out.txt:7-18`）。
2. `EFlags=0x286` 22 位逐位分解，TF/RF/VM=0、IF=1（`_w9_q3_out.txt:51-82`）。
3. 打印的 EFlags 来自 `[ebp+0xC0]=CONTEXT.EFlags`，全组 10/10 寄存器偏移吻合
   （`_w9_q3_handler_out.txt:85-172`）。
4. 异常码确为 0x80000004，表项 `0x7E8880` + 串 `0x820F74` 与 `except.txt:1-3` 逐字一致。
5. ③「游戏二进制自抛」排除（导入表、0 条 0x80000004 立即数、2 处调用点实参、干净栈链）。
6. ④ 中 INT3 / ICEBP / RF-VM / handler 误报 / 镜像错位 5 项字节排除。
7. Esi/Edi 语义由自己反汇编复算（class_req=1 位图掩码 + 命中索引），且窗口内无
   0x7FFFFFFF 立即数。
8. 崩点 32/32 字节零差异、`0x7CFC9F in by()=True`、非任何直接 call/jmp 落点。
9. `find` 113 份 `except_post` 单一哈希 `6694b75e…` = 本件 SHA256（Q4 定谳）。

**未验（拿不到就写未验，不把「查不到」当「不存在」）**：
- `DR6.BS` / `DR6.B0-B3` 的值 —— 本件无字段；判别 ①/② 的唯一硬判据。
- 崩溃进程 `DR0-3` / `DR7` 实际值 —— 本件无字段；14:11 crawl dump 属另一进程，不可代用。
- `ExceptionRecord.ExceptionInformation` / `NumberParameters` / `ExceptionFlags` —— 本件无字段
  （若 ③ 为外部伪造，这些本可给出旁证）。
- Windows 向用户态派发 #DB 时是否清 `CONTEXT.EFlags.TF`；以及 trap-frame 原始 EFLAGS ——
  OS/架构约定，静态字节不能自证。
- handler 异常码**查表循环本体**（表项与串已亲读，循环未逐条反汇编）。
- `0x7DB8A0` 处 `RaiseException` 第一实参 `[ebp+0x10]` 的运行时值（静态无常量来源）。
- 外部施动者身份、是否挂调试端口、是否注入/伪造 —— 零支持证据，亦无法从本件排除。
- 旧件 `:44/:86` 所称「② RC-1 现场 Esi 同为 0x7FFFFFFF」—— 未独立复核 `RC_SPEC_V4.md`。
- 113 份 `except_post` vs §555 记 107 份的差额归属、以及「是否就是那 107 份之一」—— **Q4 定谳**。
- 数据/I/O 断点的 EIP 语义（x86 约定为 trap，倾向与 0x7CFC9F 不符）—— 架构约定 + 无 DR6，未验。

**铁律遵守**：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；
零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入，**E3 维持暂停 D-13**）；
只读 `ra2youli/`、`out/re_work/…`、`lead/GOAL_*`、现场台账与 W1-W8 既有件；
唯一写域 `W9_SINGLESTEP_7CFC9F/`（本次仅新增 Q3 件）；Python 全部 `python -I -X utf8` +
绝对路径；不 commit / 不 push。`git status --porcelain` 仅显示 `?? lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/`，
未改动任何既有文件。三条探针单次 140.12s / 100.19s / 66.67s，均 EXIT=0 自退出（< 8 min）。

---

## 9 交付物与探针索引（全部在唯一写域内）

| 文件 | 内容 |
|---|---|
| `Q3_MECHANISM.md` | 本回件正本 |
| `_w9_q3.py` / `_w9_q3_out.txt` / `_w9_q3_stdout.txt` | 主探针：SHA 头部、位分解、字段普查、崩点字节与反汇编、函数前段、导入表、串 xref（307 行 / EXIT=0 / 140.12s） |
| `_w9_q3_handler.py` / `_w9_q3_handler_out.txt` / `_w9_q3_handler_stdout.txt` | 补充探针：handler 打印值来源、RaiseException IAT 与调用点（237 行 / EXIT=0 / 100.19s） |
| `_w9_q3_final.py` / `_w9_q3_final_out.txt` / `_w9_q3_final_stdout.txt` | 第三探针：±0x20 字节排除、两处调用点实参、异常码表（96 行 / EXIT=0 / 66.67s） |

内联有界核（`-c`，均 `python -I -X utf8`，未写文件）：格式串 raw offset→VA 与
`0x821DE4` 内容；handler xref 单遍扫描；`e.rd(0x7F9928,32)` RaiseException 模板；
`e.rd(0x7C9484,8)` + `e.disasm` 返回地址；全 `.text` 直接 call/jmp 落点 == 0x7CFC9F 计数；
全文件小端 `0x80000004` 出现位置；`e.resolve_iat` 七槽；`e.rd(0x7E8880,8)=04 00 00 80 FD 00 00 C0`；
`stat` 原件与 `except_post` 样本 mtime；`date` 回件时刻。
