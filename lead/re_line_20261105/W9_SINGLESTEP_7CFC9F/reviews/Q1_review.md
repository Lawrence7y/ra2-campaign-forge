# Q1 独立复核 · `0x7CFC9F` 代码身份回件

> 复核员：独立复核员·Q1（默认怀疑）。被复核件：`Q1_CODE.md`、`_w9_q1.py`、
> `_w9_q1_out.txt`、`_w9_q1_stdout.txt`（均在 `D:/Project/ra2-campaign-forge/lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/`，下文简称 `W9/`）。
> 复核时刻：2026-11-06 03:1x–03:3x。零真机、零采样、零活进程；**唯一写域 = `W9/reviews/`**。
>
> 记法：`Q1_CODE.md:L` 指回件行；`_w9_q1_out.txt:L` 指探针输出行；
> `ra2tool.py:L` 指 `lead/goal3t_nightwatch_20261102/swarm_20261104/ra2tool.py` 行；
> `TASK.md:L` 指 `W9/TASK.md` 行。

---

## 0 · 复核结论（先给答案）

| 项 | 值 |
|---|---|
| **verdict** | **CONFIRMED**（对 Q1 自身范围内的结论） |
| **sha256BindingPresent** | **true** —— `Q1_CODE.md:1-5` 真含两个自算 64 位 SHA256 + 两个字节数 + COVERAGE/IMAGEBASE + 回件时刻 |
| **independentlyReproduced** | **true** —— 本次用自写探针 + `sha256sum` + 原探针重定向重跑，三路独立复现 |
| **substantiveDefect（Q1 范围内）** | **无**（未发现旧分析 `SINGLESTEP_0x7CFC9F_ANALYSIS.md` 在「代码身份」上的实质错误） |
| 但有 mustFix | 3 条（§6）；objections 5 条（§5），其中 2 条指向 Q4 / 汇总件，不降 Q1 判定 |

**理由一句话**：Q1 的每一条 Q1 范围内结论都能追到「反汇编地址 + 原始字节」或「文件:行」，且我在本次会话用**不调用 Q1 探针的自写代码**逐项复算得到完全相同的结果；但 Q1 的结论标题缺少一句关键的「字节相等 ≠ 证据件来源成立」限定，且 Q4 的哈希比对虽在其受命口径内确为全量，在「全仓 7CFC9F 异常件」口径下并不全量（找到了反例）。

---

## 1 · 本次实跑的命令与输出（每条数字可追）

### C-R1 · 两个 SHA256 + 字节数（独立 `sha256sum`/`wc -c`）

```
cd "D:/Project/ra2-campaign-forge" && sha256sum "ra2youli/gamemd.exe" && wc -c "ra2youli/gamemd.exe" && sha256sum "out/re_work/work_chain/CONTINUE_20261003/lead/boot_hang_triage_20261018/EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt" && wc -c "out/.../EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt"
```

输出（原样）：

```
73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 *ra2youli/gamemd.exe
4825360 ra2youli/gamemd.exe
6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251 *out/.../EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
26405 out/.../EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
```

与 `Q1_CODE.md:2-3`、`Q1_CODE.md:18-19`、`_w9_q1_out.txt:9-13`、`TASK.md:19-20` 一致。

### C-R2 · 自写独立探针（不调用 `_w9_q1.py`）

```
cd "D:/Project/ra2-campaign-forge" && python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/_Q1_review_probe.py" > "D:/.../reviews/_Q1_review_probe_stdout.txt" 2>&1; echo "EXIT=$?"
```

`EXIT=0`。输出存 `W9/reviews/_Q1_review_probe_out.txt`（108 行），关键行：

- `:7-8` 两个 SHA256/字节数（Python `hashlib.sha256(Path(...).read_bytes())`，与 C-R1 全等）
- `:11-15` `Engine.sha == 自算: True`；`IMAGEBASE = 0x400000`；`fo(VA)=0x3cfc9f`；`COVERAGE = 99.998375677293% / 1394120 insns / 66 resync-fails`；`TLO/THI/TSZ = 0x401000 / 0x7e1000 / 0x3e0000`
- `:18-24` `rd(VA,32)`、`rd(VA,0x30)` 原始字节；`rd32 == EXCEPT : True ; diff idx = []`；`EXCEPT == TASK : True`；三源长度 `32/32/32`
- `:27-65` E1 线性 18 条 / E2 重同步 18 条，逐条列 `addr + bytes + mnemonic + op_str`；`E2 ... bytes_ok=True` ×18；`end VA = 0x007CFCCF`；`E1==E2 first 18 (addr,mnem,op_str) : True`
- `:68-80` 前 8 条；`rd(0x7CFC7F,64)`；`0xCC positions = NONE`、`0xF1 = ['0x7cfca5']`、`0xF0 = ['0x7cfca3']`；`±32 window instruction starts with opcode0 in CC/F1/F0 = NONE`
- `:83-97` `VA in by() = True`；`by()[VA] = size=2 bytes=8B0A mov ecx, dword ptr [edx]`；前序 12 条上下文；`prev insn end = 0x007CFC9F ; adjacent to VA = True`
- `:100-104` **带调试计数的直接分支普查**：`local window [0x007CF000,0x007D1000): scanned=2815 insns, j/call=501, imm-typed=452`；`local direct refs to VA = 0 []`；`full .text (1394120 insns) direct refs to VA = 0 []`；`rd(0x7CFC9B,4) = 8B 54 F9 04`

> 调试计数是我特意加的：Q1 探针 `_w9_q1.py:247-262` 只打印「0 条」，不打印扫了多少条，无法区分「真普查」与「循环没进去」。本次 2815/501/452 与 1394120 证明循环确实跑满。

### C-R3 · 原 Q1 探针逐字重跑（只改 OUT 路径，输出落 `reviews/`）

`W9/reviews/_Q1_prep_rerun.py` 把 `_w9_q1.py` 复制到 `W9/reviews/_Q1_exact_rerun.py`，**唯一改动**是第 24 行 `OUT` 指向 `W9/reviews/_Q1_exact_rerun_out.txt`。语义差异核对（`python -I -X utf8 -c` 比对 `splitlines()`）：

```
lines 355 355
semantic differing lines: 1
  L24: OUT = ROOT + r"\lead\...\_w9_q1_out.txt"  ->  OUT = ROOT + r"\lead\...\reviews\_Q1_exact_rerun_out.txt"
```

（行尾由 LF 变 CRLF 是 `Path.write_text` 所致，不改变语义。）

```
cd "W9/reviews" && python -I -X utf8 "D:/.../reviews/_Q1_exact_rerun.py" > "D:/.../reviews/_Q1_exact_rerun_stdout.txt" 2>&1; echo "EXIT=$?"
```

```
EXIT=0  ELAPSED_SEC=53
last 3 stdout lines:
PROBE DONE -- exit 0
==============================================================================
wrote D:\Project\ra2-campaign-forge\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\reviews\_Q1_exact_rerun_out.txt
rerun lines 234 orig lines 234 EQUAL = True
```

⇒ `EXIT=0`、`PROBE DONE -- exit 0`、自退出、约 53 s（Q1 自报「约 62 s」，同量级，均 < 8 min）全部复现；去 `run command`/`回件时刻`/`wrote` 三行后，重跑输出与既有 `_w9_q1_out.txt` **逐行全等**。另 `grep -c "PROBE EXCEPTION"` 在 `_w9_q1_out.txt` 与重跑输出均为 `0`（`_w9_q1.py:346-355` 的 `except` 分支未触发）。

### C-R4 · 独立校验 Q1 交付物的字节/行数声明

```
cd W9 && python -I -X utf8 -c "...read_bytes(); print(len, LF, splitlines, CRLF)..."
```

```
_w9_q1_out.txt         bytes=15395   LF=236   splitlines=236   CRLF=236
_w9_q1_stdout.txt      bytes=15490   LF=237   splitlines=237   CRLF=237
Q1_CODE.md             bytes=14724   LF=246   splitlines=246   CRLF=0
_w9_q1.py              bytes=14693   LF=355   splitlines=355   CRLF=0
PROBE DONE 所在行:  _w9_q1_out.txt:235
EXCEPT 件: len=26405  LF=1045  CR=1046  CRLF=1045  lone CR=1  splitlines=1046
旧分析 SINGLESTEP_0x7CFC9F_ANALYSIS.md: 17473 B
```

`diff <(grep -v '^wrote ' _w9_q1_stdout.txt) _w9_q1_out.txt` → `DIFF_EXIT=0`（Q1 自报的 stdout↔out.txt 一致性成立）。

### C-R5 · 独立全量校验 Q4 的哈希比对（本次复核的重点反例猎捕）

```
cd "D:/Project/ra2-campaign-forge"
"D:/Git/usr/bin/find.exe" . -path ./.git -prune -o -type f -name 'except_post_*.txt' -print | wc -l
"D:/Git/usr/bin/find.exe" . -path ./.git -prune -o -type f -name 'except_post_*.txt' -print0 | sort -z | xargs -0 sha256sum > /tmp/q1rev_hashes.txt
```

```
113
hashed lines: 113
distinct hashes:
    113 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251
EXCEPT sha: 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251
```

不依赖哈希的逐字节全文比对（`cmp` 循环遍历 113 份）：

```
cmp: compared=113 differing=0
```

扩展性口径核对：

```
find . -type f -name 'except_post_*.txt' (无 prune)        -> 113
find . -type f -iname 'except_post*.txt' (大小写不敏感)     -> 113
cut -d' ' -f1 /tmp/q1rev_hashes.txt | sort | uniq -c        -> 1 distinct
grep -c '^6694b75e...' /tmp/q1rev_hashes.txt                -> 113
grep -vc '^6694b75e...' /tmp/q1rev_hashes.txt               -> 0
```

Q4 探针源码核对（`W9/_w9_q4.py`）：`:165` `posts = find_named(ROOT, "except_post_*.txt")` → `:168-170` `for fp in posts: sha_file(fp)` 逐份算 → `:171-172` 逐份比对 → `:188` `identical_bytes = [r for r in recs if Path(r[2]).read_bytes() == exc_bytes]`（**全文 read_bytes 比对，非仅比长度/前缀**）。`W9/_w9_q4_out.txt:48-57` 打印 `find 命中总数 = 113 / 比对份数 = 113 / 同哈希份数 = 113 / 不同哈希份数 = 0 / distinct 哈希数 = 1 / 逐字节 == 的份数 = 113 / 113`。

⇒ **Q4 在其受命口径（`except_post_*.txt`，`TASK.md:65`）内确为全量**：113 份逐份 SHA256 + 113 份逐字节全文比对，我用另一套实现（`find -print0 | xargs sha256sum` + `cmp` 循环）独立复现，结论一致。§555 的 107 是子树口径（`GOAL_THREE_TARGETS_20261018.md:5475`、`:5564-5570` 诚实账自陈「只验单一哈希」）；我实测 `out/.../qc161_u0400_trip` = 107、`lead/qc161_u0400_trip` = 5、整仓 = 113（`5+1` 份在 `out/.../q161`），与 `Q4_RELATION.md:64-68` 相符。

### C-R6 · 反例猎捕：全仓「7CFC9F 且 SINGLE_STEP」件里是否存在不同哈希

```
find . -path ./.git -prune -o -type f -name 'except*.txt' -print0 | xargs -0 grep -l "007CFC9F" | wc -l
... | xargs sha256sum | cut -d' ' -f1 | sort | uniq -c
```

```
211
      1 27eef06bca05fa7d4aeecf3d63b291265e3250d0d9672544eea4e10e47778ce0
    206 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251
      1 77f5a4cb1350ccc3e75bc375eb8cfa953906a59e84930479e1faec6ff4cb822f
      1 94656085fbd0ef81a730d5258307c8af76fd92cdfcc10dcd3eddd6c6277e5d33
      2 ca1acc378bf6cee0e3fe056842c8a40aeeabbfb9d57703433290b7a98c1ed05f
```

逐件读头（`sed -n '1,3p;11p;13,14p;17p'`）确认其中 4 件是**独立的** `EXCEPTION_SINGLE_STEP @ 007CFC9F`，且 `Esp`/`Edx` 与 EXCEPT 件（`Esp:00F9C614`、`Edx:0E73276C`，EXCEPT 件 L11/L13）**不同**：

| 文件（`out/re_work/work_chain/CONTINUE_20261003/lead/`） | SHA 前缀 | Eip | Esp | Edx |
|---|---|---|---|---|
| `qc119_after_entry/carrier/except.txt` | `77f5a4cb` | `007CFC9F` | `00F9BE34` | `0E75276C` |
| `qc120_entry_then_arm/carrier/except.txt` | `27eef06b` | `007CFC9F` | `00F9C614` | `0E74276C` |
| `qc121_entry_then_arm/carrier/except.txt` | `ca1acc37` | `007CFC9F` | `00F9C124` | `0EFA276C` |
| `qc123_rc1_only/carrier/except.txt` | `94656085` | `007CFC9F` | `00F9C614` | `0E7EA76C` |

（`qc116_clear_and_run/carrier/except.txt` 哈希 `e369a911`，是真 SINGLE_STEP 但 Eip=`77159DAC`，只是文件里别处提到 `007CFC9F`，不算同点件。）

⇒ **找到了反例**：`except_post_*` 语料之外，仓内确有 4 份不同哈希的 `EXCEPTION_SINGLE_STEP @ 007CFC9F` 件。`Q4_RELATION.md:111-112` 只统计了「102 份 `except.txt` / 8 个 distinct 哈希 / 91 份 == `6694b75e…`」，`:223` 的命令清单 [O]/[P] 亦只报计数，**未逐件读这 4 份的寄存器头**，因此 Q4 的「历史基线残件 / 主崩溃叙事要重新定位」目前只在 `except_post_*` 与手上这一件 EXCEPT 上被坐实，不能外推成「仓内所有 7CFC9F SINGLE_STEP 件都是同一份残件」。详见 §5 objection 3。

### C-R7 · 反例猎捕：Q1「0 条直接落点」在更宽谓词下是否成立

```
python -I -X utf8 -c "... Engine(); for ins in e.stream: any operand.type==2 and op.imm==VA ..."
```

```
stream insns = 1394120
any-insn-with-imm==VA count = 0
loop* insns in stream = 23
loop* targeting VA = 0 []
Q1-predicate j/call direct refs to VA = 0 []
```

Q1 探针的谓词是 `mn.startswith("j") or mn == "call"`（`_w9_q1.py:253`、`:272`），原则上会漏 `loop/loope/loopne`（本镜像 23 条）与其它带立即数的非 j/call 指令。我把谓词放宽到「**任意指令的任意立即数操作数 == VA**」，结果仍是 0；`loop*` 23 条亦无一指向 VA。⇒ 未找到反例，Q1 的「0 条」在更宽口径下仍成立。

### C-R8 · 反例猎捕：间接落点 / 跳转表

```
python -I -X utf8 -c "... raw.find(struct.pack('<I', 0x7CFC9F)) ... ; decode non-.text sections for imm==VA ..."
```

```
raw little-endian DWORD 9F FC 7C 00 occurrences in WHOLE image = 0
.rdata   scanned=196608 bytes  imm==VA hits=0
.data    scanned=196608 bytes  imm==VA hits=0
.rsrc    scanned=102400 bytes  imm==VA hits=0
.detour  scanned=12288 bytes   imm==VA hits=0
```

`push imm32 VA`（`68 9F FC 7C 00`）、绝对跳转表项若存 VA，都会在原始字节里留下该 DWORD；全镜像 0 次。这是比 Q1 更强的旁证，但**仍不能排除「相对偏移表 / 运行时算出的间接目标」**，故我同意 Q1 `_w9_q1_out.txt:205`、`Q1_CODE.md:186-187` 把间接落点写「未验」，不把它改写成「不存在」。

### C-R9 · 旧分析 §1.1 的 14/14 字节吻合（独立复算）

```
python -I -X utf8 -c "... for (addr,hex) in 14 claims: bytes(by[addr].bytes).hex().upper() == hex ..."
```

`14/14 OK = True ( 14 / 14 )`，14 条 `mov/sub/sar/dec/cmp/jle/push/pop/je` 的助记符与操作数亦与 `SINGLESTEP_0x7CFC9F_ANALYSIS.md:25-37` 一致。旧分析 `:12`、`:60` 的「±32B 无 `F1`/`CC`/`F0`」按原始字节字面读确实不精确（`_w9_q1_out.txt:87-88`、我 C-R2 `:78-79` 均实测 `F1@0x7CFCA5`、`F0@0x7CFCA3`），但按指令起始操作码读无独立 INT1/INT3/LOCK（`_w9_q1_out.txt:117-118`）。Q1 把它判为「措辞精度缺陷，非实质错误」（`Q1_CODE.md:133-135`、`:197-198`）我认可；按 `TASK.md:88-89` 的 REFUTED 档（须「实质错误 + 字节依据」），Q1 不判 REFUTED 成立。

### C-R10 · 铁律遵守核对

```
stat -c '%y %s %n' _w9_q1.py _w9_q1_out.txt _w9_q1_stdout.txt Q1_CODE.md
```

四个既有件的 mtime 仍是 `2026-11-06 01:22:55 / 01:24:13 / 01:24:13 / 01:25:39`，**未被本次复核改动**。我新建的文件全部在 `W9/reviews/` 下。未启动 `gamemd.exe`/`ra2loader`/`YURI.exe`，未读活进程内存，未写采样代码，未 commit/push。Python 一律 `python -I -X utf8` + 绝对路径。

---

## 2 · 检查①：回件是否真含自算 SHA256 头部（两个哈希都要）

**通过。** `Q1_CODE.md:1-5` 为完整的 TASK §3 头部：

```
1  被核对象 = gamemd.exe + EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
2  gamemd.exe SHA256 = 73201cc0…f67476，字节数 = 4825360
3  EXCEPT 件 SHA256 = 6694b75e…a8c251，字节数 = 26405
4  Engine 自证 = COVERAGE 99.998375677293% (1394120 insns, 66 resync-fails) / IMAGEBASE 0x400000
5  回件时刻 = 2026-11-06 01:23:00
```

两个哈希都是**完整 64 位**，不是 8 位前缀。且不是抄来的：

- `_w9_q1.py:68-75` 用 `hashlib.sha256(Path(path).read_bytes()).hexdigest()` 自算，`_w9_q1_out.txt:9-13` 打印；
- `_w9_q1.py:86-87` 再让 `Engine()` 自身断言（`ra2tool.py:53-55` 的 `EXPECT_SHA`）与自算值比对，`_w9_q1_out.txt:24` 打印 `== 自算: True`；
- 我 C-R1（`sha256sum`）、C-R2（`hashlib` + `Engine.sha`）、C-R3（原探针重跑）三路独立得到同一对值。

⇒ `sha256BindingPresent = true`。

## 3 · 检查②：结论是否有「反汇编地址 + 原始字节」支撑，还是只给了地址

**通过，且是逐条带字节。** Q1 不是只给地址：

| Q1 结论 | 地址依据 | 原始字节依据 | 我的独立复现 |
|---|---|---|---|
| `rd(VA,32)` 内容 | `Q1_CODE.md:37` `fo=0x3CFC9F` | `Q1_CODE.md:41`（32 B 全串）、`_w9_q1_out.txt:34` | C-R2 `:18` |
| `rd(VA,0x30)` | `Q1_CODE.md:46` | 48 B 全串、`_w9_q1_out.txt:37` | C-R2 `:19` |
| 0x30 窗口 18 条指令 | `Q1_CODE.md:60-79` 逐条列 VA | 逐条列 `8B0A`…`BB00000080`，`_w9_q1_out.txt:122-160` | C-R2 `:28-64`（18/18 `bytes_ok=True`，E1==E2 True，末址 `0x7CFCCF`） |
| 前 8 条助记符/操作数 | `Q1_CODE.md:141-150` | 同表逐条列原始字节 | C-R2 `:68-75` |
| 证据件 32/32 零差异 | `Q1_CODE.md:101` 逐字节表（VA `0x7CFC9F`…`0x7CFCBE`） | `_w9_q1_out.txt:46-82` 索引 0–31 三源并列 | C-R2 `:20-24`（`diff idx=[]`） |
| `VA in e.by()` / `by()[VA]=8B0A` | `Q1_CODE.md:160-161` | `_w9_q1_out.txt:189-190` | C-R2 `:83-84` |
| 非直接落点 / 非数据区 / 顺序落下 | `Q1_CODE.md:172-183` | 前序 `0x7CFC9B 8B 54 F9 04`（`_w9_q1_out.txt:206`）、`rd(VA,16)`（`:208`） | C-R2 `:96-97`、`:100-104`；C-R7 更宽谓词 |
| ±32B 的 `F1/F0` 归属 | `Q1_CODE.md:124-131` | `_w9_q1_out.txt:85-88`、`:92-118` 逐条 opcode0 枚举 | C-R2 `:76-80` |
| `fo(VA)=VA−0x400000` | `Q1_CODE.md:37-38` | `_w9_q1_out.txt:27-28`；`ra2tool.py:76-85` | C-R2 `:13` |
| 旧分析 §1.1 14/14 | `Q1_CODE.md:193-195` | `_w9_q1_out.txt:214-227` 逐条 `bytes=OK` | C-R9 |

`ra2tool.py:91-113`（`stream` 重同步 +1 解码 / `by()`）、`:119-123`（`disasm`）证实 Q1 用的两条口径确实独立；`TASK.md:25-26` 的「`disasm` 会吞异常、查起点用 `va in e.by()`、查字节用 `e.rd`」Q1 遵守了（`_w9_q1.py:94`、`:103`、`:108`、`:173`、`:184-188`）。

⇒ 按 `TASK.md:87` 的 CONFIRMED 档（每个结论都有「反汇编地址 + 原始字节」或「文件:行」支撑），Q1 达标。

## 4 · 检查③：`va in e.by()` 与「查不到 ≠ 不存在」

`Q1_CODE.md:225-226` 自陈「全 `.text` 直接分支 0 条是实跑普查，不是搜一次说没有」。我认可且加严了：

- 我的 C-R2 打印了 `scanned=2815 / j-call=501 / imm-typed=452`（局部）与 `1394120`（全 `.text`），证明循环确实跑满而非空转；
- C-R7 把谓词放宽到「任意指令任意立即数 == VA」→ 0，`loop*` 23 条 → 0；
- C-R8 全镜像搜 `9F FC 7C 00` DWORD → 0 次，非 `.text` 四节反汇编 `imm==VA` → 0；
- 但 Q1 与我**都**把「间接分支 / 跳转表落点」写「未验」（`_w9_q1_out.txt:205`、`Q1_CODE.md:186-187`）——符合 `TASK.md:109` 铁律。

`Q1_CODE.md:217-224` 的未验清单（运行态镜像字节、Q2/Q3/Q4/Q5 范围、间接落点）与 `TASK.md:12`（纯静态、零真机）一致，不补造。

## 5 · Objections（默认找反例）

1. **【最重要，指向 Q4 / 汇总件，不降 Q1】Q4 的哈希比对「在其口径内全量」，但「全仓 7CFC9F 异常件」口径下不全量。** `TASK.md:65` 明令比对对象是 `except_post_*.txt`，Q4 确实 113/113 逐份 SHA256 + 113/113 逐字节全文比对（C-R5 独立复现），**该口径下该不该全量 = 该，且做了**。但 C-R6 找到 4 份不同哈希的真 `EXCEPTION_SINGLE_STEP @ 007CFC9F` 件（`qc119/qc120/qc121/qc123` 的 `except.txt`，`Esp`/`Edx` 各异），另有 `qc116` 为不同 Eip。`Q4_RELATION.md:111-112`、`:223` 只报「102 份 / 8 哈希 / 91 同哈希」的计数，未逐件读头；而 `:168-175`、`:179-201` 的「历史基线残件 / 主崩溃叙事重新定位 / REFUTED」措辞是全局性的。⇒ 结论应限定为「**手上这件 EXCEPT 与 113 份 `except_post_*` 是同一份基线残件**」，不能外推成「仓内不存在独立的 7CFC9F 单步异常证据」。这是我在反例猎捕中真正找到的一条。

2. **【指向 Q1 措辞】Q1 的标题/§2 结论缺一句「字节相等 ≠ 证据件来源成立」的限定。** `Q1_CODE.md:206-208` 与自述 headline 均写「Q1 CONFIRMED：… 证据件 32/32 字节零差异」。字面为真，但 `Q4_RELATION.md:159` 明写「这只证明『文本抄的是真实代码』，不证明『2026-10-19 13:52 那趟在 0x7CFC9F 崩了』」，`:179-201` 判 REFUTED。Q1 虽在 `:29-30`、`:223` 明确把 Q4 列为未验且不越界，但汇总件 `W9_SINGLESTEP.md`（`TASK.md:96`）若把「Q1 CONFIRMED」读成「主崩溃锚点证据已验证」，就会与 Q4 冲突。

3. **【指向 Q1 §0 的绑定强度】`Q1_CODE.md:29` 的「与 §555 所记 107 份哈希前缀相同」只是 8 位前缀比对**，Q1 自己没跑任何 `except_post_*` 的哈希，也未核对 §555 的 107 vs 整仓 113 口径。Q1 已用「只记事实，Q4 定谳」正确免责（`:29-30`），故非实质错误；但汇总件不得把这一行当作 Q1 已建立的 SHA256 绑定，真正的绑定来自 Q4 的全量比对与我的 C-R5。

4. **【数值精度】`_w9_q1_out.txt` 的行数自报错 1 行，行数口径未声明。** `Q1_CODE.md:20` 与 `:237` 写「235 行」；实测 `wc -l` = 236、`splitlines()` = 236、`PROBE DONE -- exit 0` 在 `:235`（C-R4）。Q1 大概把「PROBE DONE 所在行号」当成了总行数。另 `Q1_CODE.md:24` 的 EXCEPT 件「1046 行」是 `splitlines()` 口径（文件有 1 个 lone CR，`wc -l` 只有 1045），口径未写明。均不影响结论，但违反 `TASK.md:108`「每个数字追到实跑命令 + 输出」的严格读法。

5. **【探针自检强度】`EXIT=0` 本身不足以证明探针无异常。** `_w9_q1.py:346-355` 的 `except Exception` 只打印标记、不 `raise`、不 `sys.exit(1)`，所以即使主逻辑抛异常进程仍返回 0。Q1 `:20` 以 `EXIT=0` 作为「跑成功」的依据偏弱；我补验了两份输出里 `grep -c "PROBE EXCEPTION"` 均为 0，且 C-R3 重跑输出逐行全等，才确认无隐藏异常。

## 6 · mustFix

1. **给 Q1 的结论标题/§2 结论补限定句**：在 `Q1_CODE.md:206-208`（及 §2 `:111-112`、headline）加一句——「32/32 字节一致仅证明该文本抄录自 `gamemd.exe` 的 `0x7CFC9F..0x7CFCBE`，**不证明该 EXCEPT 件记录了一次真实发生于 2026-10-19 13:52 的异常**；证据件来源与「主崩溃」关系由 Q4 定谳（本项未验）」。并在 `W9_SINGLESTEP.md` 的「## 2 Q1 代码」显式标注 Q1 CONFIRMED 的边界，避免与「## 5 Q4 与主崩溃的关系」的 REFUTED 冲突。
2. **把 Q4 的结论限定到口径内，并处理 C-R6 的 4 份反例**：在 `Q4_RELATION.md:23-32`、`:164-175`、`:179-201` 与汇总件的「## 5」「## 7 必须改项」写明「同哈希结论适用于 `except_post_*`（113/113）与手上这件 EXCEPT」；对 `out/.../qc119_after_entry|cq120_entry_then_arm|qc121_entry_then_arm|qc123_rc1_only/carrier/except.txt` 这 4 份不同哈希 7CFC9F SINGLE_STEP 件补一次逐件读头 + 哈希 + 时序判定（或明确列「未验」），否则不得写「仓内 7CFC9F 异常证据全为同一残件」。
3. **修正数字口径**：`Q1_CODE.md:20`、`:237` 的「235 行」改为「236 行（`wc -l` / `splitlines()`；`PROBE DONE` 在第 235 行）」；`:24` 的「1046 行」注明是 `splitlines()` 口径（`wc -l` 为 1045，因 1 个 lone CR）。

> 三条均属措辞/口径/边界修补，**不改变 Q1 在代码身份范围内的 CONFIRMED**。若汇总件已按 1、2 处理，则 mustFix 1/2 可视为对汇总件的约束而非 Q1 的返工。

## 7 · 未验 / 不补造（与 Q1 一致，并经我确认）

- 间接分支 / 跳转表落点：Q1 与我都写「未验」（C-R8 的 DWORD 全镜像 0 次只是更强旁证，不构成排除）。
- 运行态镜像字节是否与磁盘一致：零真机、零活进程，**未验**（`TASK.md:12`）。
- 函数起止、`e.func_rets`、crashspec 检索（Q2）；`EFlags=0x286` 位分解 / TF·DR·RaiseException 候选 / `Esi`·`Edi` 语义（Q3）；Q5 路线 —— 本复核不触碰，不采信也不反驳。
- C-R6 那 4 份不同哈希 7CFC9F 件的**来源、写入时序、是否为真捕获**：我只读了头部与哈希，**未验**，不推断其性质；只据以说明 Q4 结论的口径边界。
- C-R5 中我这次全仓 `find -type f -print | wc -l` = 562083，Q4 记录 `_w9_q4_out.txt:47` = 561979；两次运行时刻不同（Q4 02:10，本次 03:2x）仓内有新文件，属仓库漂移；`except_post_*.txt` 计数与哈希结论两次均为 113/113 同哈希，不受影响。
- 未复核 Q2/Q3/Q4/Q5 回件的其余结论；本复核只答 Q1 + 指定的 Q4 哈希比对全量性检查。

## 8 · 复核产物（全部在 `W9/reviews/`）

| 文件 | 说明 |
|---|---|
| `Q1_review.md` | 本复核正文 |
| `_Q1_review_probe.py` / `_Q1_review_probe_out.txt` / `_Q1_review_probe_stdout.txt` | 自写独立探针（C-R2，108 行输出） |
| `_Q1_prep_rerun.py` / `_Q1_exact_rerun.py` / `_Q1_exact_rerun_out.txt` / `_Q1_exact_rerun_stdout.txt` | 原 Q1 探针逐字重跑（仅改 OUT 路径），C-R3 |

（`reviews/` 下另有其它复核员的 `Q2_review.md` 与 `_q2_review_*` 文件，非本复核所写，未改动。）
