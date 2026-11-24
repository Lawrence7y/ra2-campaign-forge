# Q3 独立复核 · 默认怀疑

> 复核对象：`lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/Q3_MECHANISM.md` 及其三条探针
> （`_w9_q3*_{out,stdout}.txt` / `_w9_q3*.py`），以及被点名的 Q4 哈希比对口径。
> 复核方式：**自己重跑**关键 SHA256 / 字节读 / 反汇编 / 文件系统普查；零真机、零活进程读取、
> 零采样注入；不改任何既有文件；唯一写域 = `reviews/`。
> 复核探针：`reviews/_Q3_review_probe.py` → `reviews/_Q3_review_probe_out.txt`（161 行，EXIT=0，85.62s）。

## 复核自证（我自己实算，非引用 Q3 输出）

```
被核对象 = gamemd.exe + EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360
EXCEPT 件 SHA256 = 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251，字节数 = 26405
Engine 自证 = COVERAGE 99.998375677293% (1394120 insns, 66 resync-fails) / IMAGEBASE 0x400000
复核时刻 = 2026-11-06 03:53:54 起（探针 :3）
```

实跑命令：
`cd D:/Project/ra2-campaign-forge && sha256sum ra2youli/gamemd.exe out/re_work/.../EXCEPT_...txt && wc -c <两件>`
→ `73201cc0…f67476 *ra2youli/gamemd.exe` / `6694b75e…a8c251 *…EXCEPT…txt` / `4825360` / `26405` / `4851765 total`。
`python -I -X utf8 D:\...\reviews\_Q3_review_probe.py` → EXIT=0，`reviews/_Q3_review_probe_out.txt:7-8,26-27`。

---

## 0 · 总判

**verdict = PARTIAL**（对 Q3 回件的复核结论，不是 Q3 自报档的照抄）。

| 检查项 | 结论 | 依据 |
|---|---|---|
| 1) 回件真含自算 SHA256 头部（两个哈希都要） | **通过** | `Q3_MECHANISM.md:2-3`，我独立实算一致 |
| 2) 结论有「反汇编地址 + 原始字节」支撑，不是只给地址 | **通过** | 我亲跑复现 8 组关键地址+字节，`_Q3_review_probe_out.txt:69-157` |
| 3) 默认找反例 / Q4 哈希比对该不该全量 | **找到实质反例** | 见 §3：`except_post_*` 全量成立，但**范围外另存 5 份不同哈希的同地址 SINGLE_STEP 记录** |
| 关键反汇编/字节读/SHA256 是否独立复现 | **是** | §2 全表 |
| 与邻题（Q4 REFUTED）一致性 | **有缺口** | §3.3 |

Q3 的**字节级机制分析几乎全部可复现且正确**：EFlags 来自 `CONTEXT.EFlags`（`[ebp+0xC0]`）、
③ 游戏二进制自抛排除、④ ICEBP/INT3 字节排除、①② 因无 DR6 未验、Esi/Edi 语义、
旧件 SF/ZF 误标——我都自己实跑确认。因此 **不是 REFUTED**。
但不能判 CONFIRMED：有 4 条异议（其中 1 条探针输出件数值错误、1 条是任务点名的
「全量」范围反例、1 条是与 Q4 的前提冲突未登记），见 §6。

---

## 1 · 检查点 1：强制头部（两个哈希都要）

我逐行读了 `Q3_MECHANISM.md:1-5`（`_Q3_review_probe_out.txt:11-23`）：

```
:1 被核对象 = gamemd.exe + EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
:2 gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360
:3 EXCEPT 件 SHA256 = 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251，字节数 = 26405
:4 Engine 自证 = COVERAGE 99.998375677293% / IMAGEBASE 0x400000
:5 回件时刻 = 2026-11-06 02:34:24
```

`_Q3_review_probe_out.txt:17-23` 逐项布尔：`头部含 gamemd.exe SHA256=True`、
`头部含 EXCEPT 件 SHA256=True`、`4825360=True`、`26405=True`、`COVERAGE=True`、
`IMAGEBASE 0x400000=True`、`回件时刻=True`。
两个哈希值与我 `sha256sum`/`hashlib` 实算一致（`_Q3_review_probe_out.txt:7-8`）；
COVERAGE/IMAGEBASE/insns/fails 与我实例化 `Engine()` 一致（`:26`）。

⇒ **sha256BindingPresent = true**。且 Q3 的 SHA 不是抄 TASK.md：`_w9_q3.py:39-44,103-109`
确实 `hashlib` 实算；`_w9_q3_out.txt:7-11` 与头部逐字相同。

---

## 2 · 检查点 2：「反汇编地址 + 原始字节」支撑（我自己重跑，不采信 Q3 探针输出）

我用同一个 `ra2tool.Engine`（`ra2tool.py:51-123`，`e.rd`/`e.by()`/`e.disasm` 真调用）亲跑。
下列**全部**为本次会话实跑结果（`reviews/_Q3_review_probe_out.txt`），不是读 Q3 的输出件：

| 结论 | 我亲跑的地址 + 原始字节 | 出处 |
|---|---|---|
| 崩点 32B 与证据件零差异 | `fo=0x3CFC9F`；`e.rd(0x7CFC9F,32)=8B 0A 2B 4D F0 8B F1 89 4D F8 C1 FE 04 4E 83 FE 3F 7E 03 6A 3F 5E 3B F7 0F 84 0D 01 00 00 8B 4A`；差异索引 `[]`；`in by()=True` → `mov ecx,dword ptr [edx]` size=2 | `:29-34` |
| `0x7CFC9B` 末址 = `0x7CFC9F` | `0x7CFC98 8b4df4` / `0x7CFC9B 8b54f904 mov edx,[ecx+edi*8+4] (末址=0x7CFC9F)` / `0x7CFC9F 8b0a` | `:45-46` |
| ★ EFlags 取自 `[ebp+0xC0]` | `0x4C8C63 8b8dc0000000 mov ecx,[ebp+0xc0]` → `0x4C8C6D 51 push ecx` → `0x4C8C6E 68501e8200 push 0x821e50` → `0x4C8C74 ffd3 call ebx` | `:70-76` |
| 10/10 CONTEXT 偏移吻合 | 我另跑 `e.disasm(0x4C8B79,0x100)`：`+0x9C/+0xA0/+0xA4/+0xA8/+0xAC/+0xB0/+0xB4/+0xB8/+0xC0/+0xC4` 全在，`10/10 present = True`（`0xC0` 在 `0x4C8C63`，见下方「已排除疑似反例」） | 本会话 `python -I -X utf8 -c` |
| 格式串 | `e.rd(0x821E50,16)=b'EFlags:%08X \r\n\x00\x00'`；`e.rd(0x820F74,110)=b'EXCEPTION_SINGLE_STEP\r\r\nDescription: A trace trap …'` | `:89-90` |
| IAT | `e.resolve_iat`: `0x7E115C=IsBadReadPtr` / `0x7E1160=lstrcatA` / `0x7E11B4=IsBadCodePtr` / `0x7E12C0=RaiseException` | `:92-95` |
| 异常码 0x80000004 + BREAKPOINT 独立表项 | `e.rd(0x7E8840,8)=03 00 00 80 02 00 00 80`；`e.rd(0x7E8880,8)=04 00 00 80 FD 00 00 C0` | `:98-99` |
| ICEBP/0xF1 排除 | `e.rd(0x7CFC9E,1)=04`、`0x7CFC9E in by()=False`、`e.rd(0x7CFC9B,4)=8B 54 F9 04`；±0x20 窗口仅 `0xF0@0x7CFCA3`、`0xF1@0x7CFCA5` 均 `in by()=False` | `:103-107` |
| ③ 立即数/调用点 | 全 `.text` 立即数 `==0x80000004` = **0**；`call [0x7E12C0]` = **2**（`0x7D2F92`/`0x7DB8A0`）；`e.rd(0x7F9928,32)=63 73 6D E0 01 00 00 00 …`，首 dword `0xE06D7363` | `:110-113` |
| 返回链 | `e.rd(0x7C9484,8)=E8 8A 66 00 00 6A 09 8B` → `0x7C9484 e88a660000 call 0x7cfb13` / `0x7C9489 6a09 push 9` | `:114-116` |
| 非任何直接分支落点 | `direct call/jmp targets == 0x7CFC9F : 0 []` | `:118` |
| EFlags 位分解 | 置位 `[1,2,7,9]`；`TF=0 IF=1 RF=0 VM=0 SF=1 ZF=0` | `:49-50` |
| 字段普查 | `Dr0..Dr7/DR0/DR6/DR7/ExceptionInformation/ExceptionFlags/ExceptionRecord/NumberParameters/ExceptionAddress/CONTEXT` 全文零命中，`EFlags -> [15]` | `:52-67` |
| 导入表 372 项 / 调试 API | `SetThreadContext=GetThreadContext=SuspendThread=AddVectoredExceptionHandler=IsDebuggerPresent=DebugActiveProcess=False`；`RaiseException/SetUnhandledExceptionFilter/UnhandledExceptionFilter=True` | `:121-130`（计数差异见 §4） |
| Esi/Edi 链 | `0x7CFB13=55 8B EC 83 EC`、`0x7CFB12=C3`；`0x7CFB45 83ceff or esi,0xffffffff` / `0x7CFB48 d3ee shr esi,cl` / `0x7CFB4A 834df8ff` …；窗口内立即数 `0x7FFFFFFF`=**0**、`0xFFFFFFFF`=**5** | `:133-147` |
| 全部文件小端 `0x80000004` | 我另跑：raw offsets `0x2a6ed/0x4de02/0x265ce1/0x3d1bb9/0x3e8880` → VA `0x42A6ED/0x44DE02/0x665CE1/0x7D1BB9/0x7E8880`，**5 处**，与 Q3 §5③ 一致 | 本会话 `python -I -X utf8 -c` |

`_Q3_review_probe_out.txt:149-157` 对回件 8 组结论做「地址+字节串」字符串普查，
全部 `True`（例：`3.2 EFlags 取数 : {'0x4C8C63': True, '8b8dc0000000': True, '0x4C8C6E': True, '68501e8200': True}`）。

⇒ **不是「只给地址」**：回件 §3.2/§4.3/§6.1/§6.2/§5③/§5④ 都带原始字节，
且字节与我亲跑一致。**independentlyReproduced = true**。

---

## 3 · 检查点 3：反例猎取（重点：Q4 的哈希比对「该不该全量」）

### 3.1 先确认 Q3/Q4 声称的「全量」本身没错

Q3 `Q3_MECHANISM.md:70-73` 与 Q4 `Q4_RELATION.md:36-40` 报 `find` 113 份、distinct=1。我独立跑：

```
cd D:/Project/ra2-campaign-forge
/usr/bin/find . -path ./.git -prune -o -type f -name 'except_post_*.txt' -print0 \
  | /usr/bin/xargs -0 /usr/bin/sha256sum > /tmp/q3rev_all_hashes.txt
awk '{print $1}' … | sort | uniq -c
```
→ `113 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251`；
`wc -l = 113`；`grep -c '^6694b75e…' = 113`；`grep -vc = 0`。
另核：Q3 那条**未剪枝**的 `find . -type f -name 'except_post_*.txt'` 也是 113
（`./.git` 内 0 份、非 regular file 0 份），`-iname` 与 `-name` 的清单 `diff` 为空
（无大小写变体）。§555 的 107 我也复核了：

```
find ./out/re_work/.../qc161_u0400_trip -name 'except_post_*.txt' | wc -l -> 107
find ./lead/qc161_u0400_trip            -name 'except_post_*.txt' | wc -l ->   5
整仓 -> 113
```
`107 6694b75e…`（该子树全同哈希）与 Q4 §1 一致。

⇒ **就该 glob 指定的集合而言，「全量」该做且 Q4 确实做了，113/113 全同哈希成立**。

### 3.2 ★ 反例：「全量」只是**一个文件名 glob** 的全量，不是「全仓异常证据」的全量

TASK.md:65 指定的比对对象是 `except_post_*.txt`。但「同哈希 ⇒ 只有一份基线字节 ⇒
不是任何一趟的崩溃」这个推论（TASK.md:66、Q4 §0/§4）的强度取决于**仓内是否另有独立异常证据**。
我扩大口径猎取：

```
find . -path ./.git -prune -o -type f -iname '*except*.txt' -print     -> 259 份
find . -path ./.git -prune -o -type f -iname '*except*.txt' -print0 | xargs -0 sha256sum
```
→ 259 份、**多个 distinct 哈希**：`207 × 6694b75e…`，其余 52 份分属 ~40 个不同哈希。

再按内容（不看文件名）猎取同地址异常：

```
grep -rl "Exception occurred at 007CFC9F" --include='except*.txt' . | wc -l  -> 211
其 distinct 哈希 = 206×6694b75e… / 2×ca1acc37… / 1×94656085… / 1×77f5a4cb… / 1×27eef06b…
其中 basename 不是 except_post_* 的 = 98 份
其中 basename 不是 except_post_* 且哈希 != 6694b75e… 的 = 5 份
```

这 **5 份**是 `EXCEPTION_SINGLE_STEP @ 0x7CFC9F` 的**不同哈希**记录，全部在 `except_post_*`
glob 之外（因此 Q4 的「全量」哈希比对**根本没覆盖**）：

| 文件（`out/re_work/work_chain/CONTINUE_20261003/lead/` 下） | SHA256 前缀 | size | mtime |
|---|---|---:|---|
| `qc119_after_entry/carrier/except.txt` | `77f5a4cb…` | 26324 | 2026-10-16 18:39:27 |
| `qc120_entry_then_arm/carrier/except.txt` | `27eef06b…` | 26459 | 2026-10-16 18:45:57 |
| `qc121_entry_then_arm/carrier/except.txt` | `ca1acc37…` | 26468 | 2026-10-16 19:06:58 |
| `qc123_rc1_only/carrier/except.txt` | `94656085…` | 26621 | 2026-10-16 18:59:45 |
| `qc124_observe_chain/_backup/except_pre_qc124.txt` | `ca1acc37…` | 26468 | 2026-10-16 19:06:58 |

它们**不是同一份字节**（`cmp -l qc119 vs EXCEPT` 首个差异在 offset 358），
且**寄存器/栈快照各不相同**（`sed -n '11,18p'`，例 qc119：`Esp:00F9BE34`、
`Eax:0D97B7B8`、`Edx:0E75276C`、`Ecx:0D97F574`；EXCEPT 件：`Esp:00F9C614`、
`Eax:0D94B7B8`、`Edx:0E73276C`、`Ecx:0D94F574`）。栈 dump 亦不同
（qc119 `:20 00F9BE34: 00000113 … :25 0D97F574`；EXCEPT `:20 00F9C614: … :25 0D94F574`）。
但**共同点**：都是 `Error code: EXCEPTION_SINGLE_STEP`、`Exception occurred at 007CFC9F`、
`EFlags:00000286`、`Esi:7FFFFFFF`、`Edi:00000001`、同一条 `Bytes at CS:EIP` 32 字节、
`00F9C634: 767460C0`-类的 `0x767460C0` 帧与 `0x007C9489/0x007C9452/0x007C8E22` 返回链。
mtime 全部 **2026-10-16**，比声称的 13:52 那趟（EXCEPT mtime 2026-10-19 13:54:38）早 3 天。

⇒ 这 5 份是不是「独立发生的异常」需要另行定谳（本复核不下此结论，记未验），
但它们**构成「仓内只有一份 7CFC9F 基线字节」这一叙事的反例**：
至少存在 5 份**内容不同**的同地址 SINGLE_STEP 记录，Q4 的 `except_post_*` 全量比对
在**范围外**，Q3 `Q3_MECHANISM.md:75-76` 引用「113 份单一哈希 = 本件 SHA256」时
也未提示范围外还有不同哈希的同地址记录。
「全量」的**正确读法**应是：对任务书指定的 glob 全量（已做到），
**不是**「全仓所有异常证据全量」（未做到）。

（Q3 在 `:75` 写了「此事实只登记，Q4 定谳」「差额归属亦交 Q4」，**没有越权下结论**，
这一点我确认并计入加分；问题在范围措辞与反例未提示，不在「Q3 结论错」。）

### 3.3 ★ 与邻题 Q4 REFUTED 的前提冲突（Q3 未登记）

Q4 `Q4_RELATION.md:179-201` 判 **REFUTED**，实质错误是「把一份历史基线残件当成一次真实
发生于 13:52 那趟的 CPU #DB 异常现场」，并明确 `:201` 说「旧分析对 TF=0 的 EFlags
位分解本身未被本项复核」。

但 Q3 全篇的**实在论措辞**仍以「这次异常真实发生」为前提：

- `Q3_MECHANISM.md:33-34`「**这是一次 #DB**，其触发源在本件上不可判定」；
- `:228`「**现场** `Edx=0x0E73276C` 说明 `0x7CFC9B` 已执行完」；
- `:230-231`「两者产生**逐字节相同的 CONTEXT**」；
- `:320`「它们是 `__sbh_alloc_block` 的**普通运行态**」；
- `:293`「栈首 `00F9C614: 00000113` … ⇒ 一条**正常**分配链」。

如果按 Q4 的结论这份 CONTEXT 是被 harness 无条件复制的历史基线（Q4 §2.2 读
`copy_post_except_evidence` 源码坐实），那 Q3 这些「一次 / 现场 / 已执行完 / 正常」的
表述就**失去观测基础**——它们描述的是被复制的文本内容，不是 13:52 那趟的 CPU 现场。
Q3 §8「未验清单」（`:426-438`）列了 DR6、DR0-3、ExceptionInformation、OS 派发语义、
查表循环、外部施动者、RC_SPEC_V4、107/113 差额、EIP 语义等 9 项，
**唯独没有「本件是否是一次真实发生的异常」这一条**。

Q3 §7 #3（`:400`）把旧件 §0:12「真实外源陷阱、置信度高」定性为
「**置信度/范围越界（非字节级事实错误）**」，进而 `:406` 判 `substantiveDefect=false`；
而 Q4 §5 恰恰把同一条判为**实质错误（REFUTED）**。这是两题**判定档冲突**，
Q3 未登记、未给出「字节级限定口径」的说明。

**边界（公平计入）**：Q3 是在 TASK.md §2 Q3 给定框架内作答，且比旧件谨慎得多——
①② 明确标「未验」、§4.2 给开放集、§4.1/§5④d/§8 三处标「查表循环未验」、
§5③ 把「游戏二进制自抛排除」限定为静态字节结论（该结论不依赖「异常真实发生」，仍成立）。
所以这是**范围/一致性缺口**，不是字节级实质错误。

### 3.4 探针输出件的数值错误（未进回件，但被列为依据）

`_w9_q3_final.py:79`：`p("  含 0x80000004 的表项 VA = 0x%X" % (TBL + 0x40 + 8))`，
其中 `TBL = 0x7E8880 - 0x40 = 0x7E8840`，故算得 `0x7E8888`；
`_w9_q3_final_out.txt:89` 输出「含 0x80000004 的表项 VA = 0x7E8888」。

我亲跑 `python -I -X utf8 -c` + `e.rd`：
```
0x7e8880 dword = 0x80000004
0x7e8888 dword = 0xffffffff
```
且同文件 `:77` 自己那行表 `[0x7E8880] 0x80000004  0xC00000FD  0xFFFFFFFF  0x00000000`
也证明 `0x80000004` 在 `0x7E8880`。**正确 VA 是 `0x7E8880`**（Q3 回件 `:200` 写的就是 0x7E8880，
`:194-199` 表格也对）。我 `grep -n "7E8888" Q3_MECHANISM.md` → 无命中，
**错误没有进回件**；但 `Q3_MECHANISM.md:461` 把「`e.rd(0x7E8880,8)=04 00 00 80…`」
列为内联实跑依据，而 `:196-199` 的表格出处指向 `_w9_q3_final_out.txt:73-77`，
该输出件 `:89` 的错值仍在交付物清单内（`:456`）。属**探针输出瑕疵**，需订正或加勘误注。

---

## 4 · 已排除的疑似反例（我自己的探针伪影，不算 Q3 的错，诚实登记）

1. **导入表 372 vs 我探针报 339**：`_Q3_review_probe_out.txt:121` 我报 339。
   我另跑 PE 解析：`total entries = 372 ; by-name = 339 ; by-ordinal = 33`。
   我的 `[9]` 只数了 by-name（`tv & 0x80000000` 的 ordinal 被跳过），
   **Q3 的 372 是对的**（`_w9_q3_out.txt:273` / `Q3_MECHANISM.md:256`）。
2. **`[ebp+0xC0]` 在我 `[5b]` 报 `False`**：`_Q3_review_probe_out.txt:87`。
   我 `e.disasm(0x4C8B79,0xE0)` 只覆盖到 `0x4C8C59`，而 `0x4C8C63` 在窗外——
   **窗口伪影**。改 `0x100` 窗口重跑得 `10/10 present = True`，`+0xC0 → 0x4C8C63 8b8dc0000000`。
   Q3 §3.2 的 10/10 正确。
3. **栈上 `0x767460C0` 疑似 KERNEL32 帧**：EXCEPT `:28 00F9C634: 767460C0`。
   该地址恰是 `Ebp=00F9C634` 指向处，存的是**上一帧 saved ebp**，返回地址在 `:29 = 0x007C9489`。
   我 `grep -ni 'kernel\|raiseexception' EXCEPT` → 零命中；`grep -c '\*' = 1`（仅 :19 的说明行），
   1046 行 dump 无 `*` 标注。Q3 §5③「栈上无任何 KERNEL32/RaiseException 帧」在 `:20-38`
   窗口内成立，但严格说是**部分栈窗口**上的否定结论；因这是原始数据 dump 而非符号化调用栈，
   我**不列**为实质异议。
4. **三条探针运行时/EXIT**：`tail -2` 得 `140.12s / 100.19s / 66.67s`，均 `EXIT=0`；
   `_w9_q3*_out.txt` 与 `_w9_q3*_stdout.txt` 三对 `cmp -s` 全 `IDENTICAL`；
   `git status --porcelain -- …/W9_SINGLESTEP_7CFC9F/` → `?? …/W9_SINGLESTEP_7CFC9F/`。
   Q3 的自述属实。

---

## 5 · 判定档与 substantiveDefect

- Q3 自报 **PARTIAL**（`:9`），理由「本件没有 DR6/DR0-3/DR7/ExceptionInformation，
  故 ①② 无法定谳」——我复核 `_Q3_review_probe_out.txt:52-67` 字段普查零命中，
  **该理由成立**。按 TASK.md:88-89 的档位定义（PARTIAL = 部分结论有支撑，部分只能给可能性），
  就 Q3 本体而言 PARTIAL 是自洽的。
- 但 `substantiveDefect=false`（`:406`）**只在「字节级」限定口径下自洽**：
  Q4 `Q4_RELATION.md:179-201` 已把「把历史基线残件当成真实异常」判为**实质错误**。
  Q3 §7 #3 把同一条降格为「非字节级事实错误」而未声明口径，两题结论冲突。
  我**不据此判 Q3 REFUTED**（Q3 没有字节级错误），但把冲突登记为必须改项。

---

## 6 · mustFix / objections（汇总）

### mustFix（必须改项）
1. **订正 `_w9_q3_final.py:79` / `_w9_q3_final_out.txt:89` 的表项 VA**：`0x7E8888` → `0x7E8880`
   （实测 `e.rd(0x7E8880,4)=0x80000004`，`e.rd(0x7E8888,4)=0xFFFFFFFF`）；
   `Q3_MECHANISM.md:461` 若继续把该输出件列为内联依据，需加勘误注。
2. **§0/§4.3/§6 的「一次 #DB / 现场 / 已执行完 / 正常分配链」实在论表述**，
   须显式加一句边界：本件按 Q4 为历史基线残件，「是否是一次真实发生的异常」**未验**；
   机制判据是**对文本内容**的静态分析，不是对 13:52 那趟 CPU 现场的定谳。
   并把该项补进 §8 未验清单。
3. **§1:75-76 的「113 份单一哈希」补范围声明**：`except_post_*` 全量 = 113/113 同哈希，
   但仓内 `*except*.txt` 共 259 份，其中 **5 份不同哈希**的 `EXCEPTION_SINGLE_STEP@0x7CFC9F`
   记录（`qc119/120/121/123/124` 的 `carrier/except.txt`、`except_pre_qc124.txt`）在 glob 之外，
   Q4 全量比对未覆盖。「全量」= 对指定 glob 全量，**不是**全仓异常证据全量。
4. **§7 #3 / §7 `substantiveDefect=false` 登记与 Q4 REFUTED 的判定档冲突**，
   明确「非实质」是「字节级事实」限定口径；否则汇总件 `W9_SINGLESTEP.md` 的 §7 必须改项
   会同时收到 Q3=false 与 Q4=REFUTED 两个互斥结论。

### objections（异议）
- Q3 引用的文件系统事实（113 份单一哈希）本身真，但**范围措辞易误导**且未提示
  §3.2 的 5 份范围外不同哈希同地址记录；这是任务点名「默认找反例」的核心命中点。
- Q3 全篇隐含「这次异常真实发生」，与 Q4 REFUTED 冲突且未列入未验清单（§3.3）。
- 探针输出件 `_w9_q3_final_out.txt:89` 存在未订正的 VA 数值错误（§3.4）。
- `substantiveDefect=false` 与 Q4 判定互斥，缺口径声明（§5）。

---

## 7 · 实跑命令清单（每个数字可追）

| # | 命令 | 关键输出 / 出处 |
|---|---|---|
| 1 | `sha256sum ra2youli/gamemd.exe …EXCEPT…txt && wc -c <两件>` | 两哈希 + `4825360`/`26405` |
| 2 | `python -I -X utf8 D:\...\reviews\_Q3_review_probe.py` | EXIT=0，85.62s，`_Q3_review_probe_out.txt:1-161` |
| 3 | `find . -path ./.git -prune -o -type f -name 'except_post_*.txt' -print0 \| xargs -0 sha256sum` + `uniq -c` | `113 6694b75e…`；113/113；NOT=0 |
| 4 | `find … -iname 'except_post_*.txt'` vs `-name` + `diff` | 均 113；diff 空；`.git` 内 0；非 regular 0 |
| 5 | `find … -iname '*except*.txt'` + 全量 `sha256sum` | 259 份；`207×6694b75e…` + 52 份其它哈希 |
| 6 | `grep -rl "Exception occurred at 007CFC9F" --include='except*.txt' .` | 211 份；distinct `206/2/1/1/1`；非 `except_post` 98 份；其中不同哈希 **5** 份 |
| 7 | `sed -n '11,18p'` / `sed -n '20,30p'` / `cmp -l` 对 qc119 与 EXCEPT | 寄存器/栈不同；`cmp -l` 首差异 offset 358 |
| 8 | `stat -c '%y %s %n'` 对 5 份 + EXCEPT | 5 份 mtime 2026-10-16；EXCEPT 2026-10-19 13:54:38 |
| 9 | `find …/qc161_u0400_trip -name 'except_post_*.txt' \| wc -l` | 107（另 `lead/…` 5，整仓 113）；子树 `107 6694b75e…` |
| 10 | `python -I -X utf8 -c`（`e.rd` 0x7E8880/0x7E8888、PE 372/339/33、`0x100` 窗口 10/10、5 处小端常量） | 见 §2/§3.4/§4 |
| 11 | `grep -n '7E8888' Q3_MECHANISM.md` | 无命中（错误未进回件） |
| 12 | `tail -2 _w9_q3*_{out}.txt` / `cmp -s out stdout` / `git status --porcelain` | `140.12/100.19/66.67 EXIT=0`；3 对 IDENTICAL；`?? W9…/` |

---

## 8 · 诚实账（本复核未验，不补造）

- **未验**：§3.2 那 5 份不同哈希的同地址记录是否属于「独立发生的异常」、
  各自来自哪趟 / 哪个载体、与 13:52 那趟的关系——本复核只证「内容不同且存在」，不下机制定谳。
- **未验**：`0x7DB8A0` 处 `RaiseException` 第一实参 `[ebp+0x10]` 的运行时值（与 Q3 §8 同）。
- **未验**：Windows 向用户态派发 #DB 时 `CONTEXT.EFlags.TF` 的清/留语义、DR6/DR0-3 实际值、
  handler 查表循环本体——静态字节不可自证（与 Q3 §8 同，我未另跑）。
- **未验**：Q3 声称的 5 次内联 `-c` 逐条命令原文（回件 §9:458-462 只给描述未给完整命令）；
  我按同一 `Engine` 重跑了其中可对应的字节读/常量/落点/分支，结论一致，但**未逐字复现**其命令行。
- **未跑**：Q3 三条主探针本身（140.12s/100.19s/66.67s）——我核了其输出件/stdout 一致性、
  运行时尾行与 EXIT，并用**自己的** `_Q3_review_probe.py` 重跑了关键项；
  没有重跑 Q3 的原脚本。按复核标准如实登记为「未跑原脚本，已独立重跑关键项」。
- **铁律**：零真机（未启动 gamemd.exe/ra2loader/YURI.exe，未 taskkill，未读活进程内存）；
  零采样代码；未改任何既有文件；唯一写域 `reviews/`（本次新增 `Q3_review.md`、
  `_Q3_review_probe.py`、`_Q3_review_probe_out.txt`、`_Q3_review_probe_stdout.txt`）；
  Python 全部 `python -I -X utf8` + 绝对路径；不 commit、不 push。
  `git status --porcelain -- …/W9_SINGLESTEP_7CFC9F/` → `?? …/W9_SINGLESTEP_7CFC9F/`。
