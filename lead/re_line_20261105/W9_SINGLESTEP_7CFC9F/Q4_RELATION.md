# Q4 · 这件 EXCEPT 证据与「主崩溃」是什么关系

> W9 任务书 §2 Q4（TASK.md:61-68）——**本节最关键的一问**。
> 定谳员默认怀疑旧结论（§555、§590、SINGLESTEP_0x7CFC9F_ANALYSIS.md 一律先当旁证），
> 全部结论重建于本次会话亲自实跑的 `find` + `sha256sum` + `python -I -X utf8` + `ra2tool.Engine`。

---

```
被核对象 = gamemd.exe + EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360
EXCEPT 件 SHA256 = 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251，字节数 = 26405
Engine 自证 = COVERAGE 99.998375677293% (1394120 insns, 66 resync-fails) / IMAGEBASE 0x400000
回件时刻 = 2026-11-06 02:12
```

（来源：§3 强制头部四项均由 `_w9_q4.py` 的 `[A]`/`[B]` 段自己实算；
`_w9_q4_out.txt:6-20`。`Engine()` 实例化真跑，`e.rd`/`e.by()`/`e.disasm` 均实调用，
非引用 Q1 回件。IMAGEBASE 与节表见 `_w9_q4_out.txt:17-20`。）

---

## 0 · 明确二选一（先给答案）

**★ 同哈希（SAME-HASH）。**

- 我自己算了 EXCEPT 件的 SHA256 = `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251`。
- 我 `find` 出**全仓 113 份** `except_post_*.txt`，**逐份算了哈希并逐一比对**：
  **比对 113 份，113 份同哈希，0 份不同哈希，distinct 哈希数 = 1**。
- 并且做了不依赖哈希的**逐字节全文比对**：`113/113` 与 EXCEPT 件逐字节完全相同，全部 `26405` B。
- ⇒ 按任务书 §2 Q4 的判据（TASK.md:66）：**这件 EXCEPT 不是任何一趟的崩溃，是历史基线残件**；
  **整个「主崩溃」叙事要重新定位**。

依据（本次实跑）：
- `sha256sum EXCEPT_SINGLESTEP_...txt` → `6694b75e…a8c251 *…`，`wc -c` → `26405`（命令 [A]）。
- `find . -type f -name 'except_post_*.txt' -print0 | sort -z | xargs -0 sha256sum` →
  `files hashed: 113`；`cut|sort|uniq -c` → `113 6694b75e…a8c251`；
  `grep -c '^6694b75e…'` → `113`，`grep -vc` → `0`（命令 [D]）。
- `_w9_q4.py [D]`（`_w9_q4_out.txt:47-62`）：`比对份数 = 113 / 同哈希份数 = 113 / 不同哈希份数 = 0 /
  distinct 哈希数 = 1 / 逐字节 == 的份数 = 113/113 / 尺寸分布 = {26405: 113}`。

---

## 1 · 与 §555 / §590 的口径差异（不盲信旧数字）

| 口径 | 份数 | 说明 |
|---|---:|---|
| §555（GOAL_THREE_TARGETS_20261018.md:5475, 5565） | 107 | 「107 份 `except_post_*.txt` 全部同哈希」，**诚实账自陈只验单一哈希**（:5570-5571）|
| §590（:8488-8495） | 107 | `os.walk` **限定在 `qc161_u0400_trip` 单子树**（:8491, :8496）|
| **本次 Q4（整仓 `find`，剪枝仅 `.git`）** | **113** | 全仓口径；比 107 多 **6 份** |

多出的 6 份（命令 [F]/[G]，`_w9_q4_out.txt` D4 段亦给出代表）：

```
./lead/qc161_u0400_trip/l1b_20261021/except_post_20261021T184518530551.txt
./lead/qc161_u0400_trip/l1c_20261021/except_post_20261021T190509073827.txt
./lead/qc161_u0400_trip/l1d_20261021/except_post_20261021T192647245700.txt
./lead/qc161_u0400_trip/l1e_20261021/except_post_20261021T204059731043.txt
./lead/qc161_u0400_trip/l3_20261021/except_post_20261021T211447471728.txt
./out/re_work/work_chain/CONTINUE_20261003/lead/q161/except_post_20261017T230724883941.txt
```

```
count under out/.../qc161_u0400_trip = 107
count OUTSIDE that subtree          = 6
```

⇒ **§590 的「107」不是错，是范围窄**；整仓是 113，且这 6 份同样是 `6694b75e…`。
**结论方向不变（同哈希），但份数按本次整仓口径报 113。**
另：§590 称 mtime 跨「42 小时」（:8512）——本次实跑整仓为
`2026-10-17 08:14:58 .. 2026-11-04 18:26:58`（约 **18 天**，命令 [H]，`_w9_q4_out.txt` D3 段）；
文件名时间戳 `20261017T081458810997 .. 20261104T182658693950`。
§590 的「42 小时」是其单子树/子集口径，整仓更宽。**这反而更强地支持「残件复制」。**

---

## 2 · 为什么能断定「不是任何一趟的崩溃」（四条独立硬证据）

### 2.1 同一份字节在**声称崩溃之前**就已存在（时间反证）

- EXCEPT 件自身 mtime = `2026-10-19 13:54:38`（命令 [J]，`_w9_q4_out.txt:12`），
  文件名自称 `20261019T1352`（13:52 那趟「内核二分 v2 秒退」，ROUND_SUBAGENT_LOG:1962-1969）。
- 但**最早的 `except_post`** = `archive_T5/except_post_20261017T081458810997.txt`，
  mtime `2026-10-17 08:14:58`（命令 [H]/[J]），**比 13:52 早约 2 天 5 小时**，
  且 `cmp` 与 EXCEPT 件**逐字节相同**（命令 [I]：`IDENTICAL`），
  头部 `Eip:007CFC9F Esp:00F9C614 Ebp:00F9C634 / Esi:7FFFFFFF Edi:00000001 / EFlags:00000286`
  **一字不差**（命令 [R]，与 EXCEPT 件 L11-17 全等，`diff` 空、exit=0，命令 [S]）。
- **同一次真实崩溃不可能在它发生前 2 天就以完全相同的寄存器/栈快照存在。**
- 本次实跑计数：文件名时间戳 `< 20261019T1352` 的 **58 份**，`>=` 的 **55 份**
  （`_w9_q4_out.txt` D3 段）。即**过半快照早于那趟所谓的崩溃**。

### 2.2 harness 源码：这些文件是**每趟无条件复制**，不是「抓到异常」

`copy_post_except_evidence()`（多个 harness 版本一致）：
- `W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py:6029-6050`：
  `src = carrier_dir / "except.txt"` → `blob = src.read_bytes()` →
  `dst = out_dir / f"except_post_{datetime.now()...}.txt"` → `dst.write_bytes(blob)`。
- 原版 `out/.../qc151_u0400_trip/qc151_trip.py:4561-4598` 同逻辑；
  `evid_diffmode_20261019/qc151_trip_eviddiff.py:3645` 同逻辑。
- 调用点 `qc151_trip.py:5938-5939, 6042-6052`：`_except_evidence_copy()` 被放进
  `run_guarded_steps([...])` 的**第 1 项**，`finalize_trip` 在 `finally` 内执行（:5931），
  注释明写「收尾项**逐个落盘、各自独立、互不跳过**」（:5929）、
  「**前一步失败也继续后面的**」（:6041）。函数 docstring 自己写的是
  「把本趟跑后的 `except.txt` 原件**另存一份证据副本**」（:6031-6033）。
- ⇒ **`except_post_<时间戳>.txt` 只是「该趟跑后载体 except.txt 的快照」，文件名是复制时刻，
  不是崩溃时刻**；它**不以「本趟是否发生异常」为条件**。这解释了为什么 113 份内容全等。
  （§590 诚实账第 2 条 :8578 把「复制而非重复发生」列为强推断、留给 Q4；本节**读源码坐实**。）

### 2.3 上游 `except.txt` 源件：91/102 就是同一份基线

`find('except.txt')` → 102 份，8 个 distinct 哈希，其中 **91 份 == `6694b75e…`**
（`_w9_q4_out.txt` [E] 段；命令 [O]）。母模板 `_src_L3_sf10c_20261021/except.txt`
哈希即 `6694b75e…`（命令 [P]）。XVERIFY 旧件亦记：
`except_post_*.txt 中的 007CFC9F 系母本载体模板 _src_L3_sf10c_20261021/except.txt 历史固有的基线文件`
（`swarm_20261104/XVERIFY_S544_ae38d56c/V3/_write_report.py:29`）。

**一个值得单列的旁证（防止过度推广）**：harness 里声明的 `EXCEPT_MASTER`
是 `ra2bench/except.txt`，哈希 `ca175a71…`、26,515 B、首行
`Error code: EXCEPTION_ACCESS_VIOLATION`、`Exception occurred at 006F9DB6`
（命令 [Y7]；源码 `qc151_trip.py:228-230`）。
⇒ **仓内至少两套基线**：一套 AV@0x6F9DB6（ra2bench 母本，26,515 B）、
一套 SINGLE_STEP@0x7CFC9F（26,405 B，本次核的对象）。
**7CFC9F 件不是 ra2bench 那个母本**，而是另一条载体模板里的固有基线。
这不改变 Q4 结论，但说明「哪份基线被复制进载体」本身是需单独定谳的事（列未验）。

### 2.4 其它 odd-named 件也指向同一份基线

`except_*.txt`（不含 `except_post_*`）15 份中 **3 份** == `6694b75e…`：
`except_carrier_6694b75e.txt`（名字直接带哈希前缀）、
`_r2_singlestep/except_r2.txt`、以及 EXCEPT 件自身（`_w9_q4_out.txt` [E2] 段；命令 [Y13]/[Y14]）。
`except_carrier_6694b75e.txt` 首行同为 `EXCEPTION_SINGLE_STEP / 007CFC9F`（命令 [Y14]）。
⇒ 这份字节在仓里被以 4 类文件名承载，全是同一份历史件。

---

## 3 · 这份文本本身确实是「真代码」，但那与「这一趟崩了」是两件事

按铁律要求，我用 `Engine` **真读字节 + 真反汇编**把文本与镜像绑定
（`_w9_q4_out.txt` [C] 段，独立实跑，不引用 Q1 结论）：

```
e.rd(0x7CFC9F, 32) = 8B 0A 2B 4D F0 8B F1 89 4D F8 C1 FE 04 4E 83 FE 3F 7E 03 6A 3F 5E 3B F7 0F 84 0D 01 00 00 8B 4A
EXCEPT L17 字节     = 8B 0A 2B 4D F0 8B F1 89 4D F8 C1 FE 04 4E 83 FE 3F 7E 03 6A 3F 5E 3B F7 0F 84 0D 01 00 00 8B 4A
差异索引 = []  ⇒ 32/32 逐字节一致
fo(0x7CFC9F) = 0x3cfc9f = VA - 0x400000（映射自证）
va 0x7CFC9F in e.by() = True（合法指令起始，重同步流里）
e.disasm(VA,32) 12 条，前 8 条：
  0x7CFC9F 8B0A     mov ecx, dword ptr [edx]
  0x7CFCA1 2B4DF0   sub ecx, dword ptr [ebp-0x10]
  0x7CFCA4 8BF1     mov esi, ecx
  0x7CFCA6 894DF8   mov dword ptr [ebp-8], ecx
  0x7CFCA9 C1FE04   sar esi, 4
  0x7CFCAC 4E       dec esi
  0x7CFCAD 83FE3F   cmp esi, 0x3f
  0x7CFCB0 7E03     jle 0x7cfcb5
```

⇒ 这份文本**抄的是 gamemd.exe 里真实存在的代码**（size-class 计算段），字节无误。
**但这只证明「文本产生时确实读过这个镜像」，不证明「2026-10-19 13:52 那趟在 0x7CFC9F 崩了」。**
一个真实的寄存器/栈快照可以作为历史基线文件被复制任意多次；§2.1 的时间反证已排除它记录的是 13:52 那趟。

---

## 4 · 对「主崩溃」叙事的裁定

| 旧叙事 | 本次裁定 |
|---|---|
| TASK.md:8-10 / §545 口径：「唯一有真实异常上下文的一件证据」| **不成立**。它与 113 份 `except_post_*.txt` 逐字节相同，属 §555 判定的历史基线残件（§590 :8507-8508 先给出方向，本次**独立全仓复算坐实**）|
| LOG :1898 / :1962-1969：「去包装后必现 `EXCEPTION_SINGLE_STEP@0x7CFC9F`，价值极高」「秒退=重大证据」| **「必现」的是文件复制，不是异常**。这些现场记录把「跑后总有一份 except.txt 快照」误读成「每趟都抓到一次单步崩溃」。WER LiveKernelEvent 193（LOG :1964）不在本项静态可核范围，记未验 |
| SINGLESTEP_0x7CFC9F_ANALYSIS.md §0/§4（:12, :89, :92）：真实外源陷阱、与 ②「巧合地址」、包装器自旋掩盖 | **其实质前提被推翻**：它把这份残件当作一次真实发生的异常来定谳机制与「与 ② 的关系」。**若该异常从未在任何一趟发生，则「TF/DR 施动者」「两次同 EIP=确定性」「掩盖假说」全部失去观测基础**（详见 §5）|
| §555 :5473-5481「37 个 archive 零趟游戏崩溃」| **本次不推翻也不独立验证**。§555 诚实账 :5570 自陈「0 趟崩溃这条从未独立验证」；Q4 只证「现有 except_post 语料对判定崩溃无信息量」，**不等于「游戏不会崩」**（§590 :8541 同此保留）|

**⇒ 目标② 目前没有一件「把某次异常归因到某趟游戏运行」的证据。**
不是「证据不足」的措辞问题：是**这件被当作主崩溃锚点的证据，本身就是被反复复制的历史文件**。
按 TASK.md:66，整个「主崩溃」叙事要重新定位。

---

## 5 · 判定档：REFUTED（点名旧分析的实质错误）

按 §4（TASK.md:88-89），本节判 **REFUTED**——发现了旧分析
`SINGLESTEP_0x7CFC9F_ANALYSIS.md` 的**实质错误**：

- **错误条目**：§0（:12）「**一个真实的**、由外部调试机制……布下但无人消费的陷阱……
  `except.txt` 自身完全自洽……机制判定置信度**高**」、
  §1.2（:51）「保存的 `Eip=0x7CFC9F` 指向的指令**尚未执行**……陷阱恰在其后触发」、
  §4（:89）「**巧合地址（同一条分配热指令）**，非 ② 腐化链的一环……证据强度**高**」、
  §4（:92）「包装器自旋掩盖此崩假说**成立**」、
  §2（:61, :68）「两次同 EIP / 确定性」以及 §5 E1/E2/E3 全部以「这次异常真实发生」为前提。
- **实质错误**：**把一份在 2026-10-19 13:52 之前至少 2 天就已存在、且被 harness 无条件复制了
  113 次的历史基线残件，当成一次真实发生于 13:52 那趟的 CPU #DB 异常现场**，
  进而对「TF/DR 施动者」「与 ② 主崩溃的关系」「掩盖假说」作高置信度机制定谳。
- **字节/文件依据**：EXCEPT 件 SHA256 `6694b75e…a8c251`（26,405 B）==
  113/113 份 `except_post_*.txt`（`_w9_q4_out.txt:47-62`）；
  最早 `archive_T5/except_post_20261017T081458810997.txt` mtime 2026-10-17 08:14:58，
  `cmp`/`diff` 与 EXCEPT 件完全相同（命令 [I]/[S]）；
  其 L11-17 寄存器/字节与 EXCEPT 件全等（命令 [R]）；
  harness `copy_post_except_evidence` 无条件复制（`W5_HARNESS_EXT/...:6042-6050`、`qc151_trip.py:6042-6052`）。
- **注意边界**：REFUTED 针对的是「这次异常真实发生 + 由此推出的一切机制/②关系结论」，
  **不是**推翻它 §1.1 的代码语义（`0x7CFC9F` 处的指令字节与磁盘一致，本次 [C] 段复核通过），
  也**不是**断言「游戏不会崩」。旧分析对 TF=0 的 EFlags 位分解本身（§1.2）未被本项复核。

---

## 6 · 实跑命令清单（每个数字可追）

| 编号 | 命令 | 关键输出 |
|---|---|---|
| [A] | `sha256sum <EXCEPT>; wc -c <EXCEPT>; sha256sum ra2youli/gamemd.exe; wc -c ra2youli/gamemd.exe` | `6694b75e…a8c251 / 26405`；`73201cc0…f67476 / 4825360` |
| [B] | `python -I -X utf8 _w9_q4.py`（`Engine()` 真跑） | `[B]` 段：sha 自证 True / IMAGEBASE 0x400000 / COVERAGE 99.998375677293% |
| [C] | 同上 `[C]` 段 `e.rd/e.by()/e.disasm` | 32/32 字节一致；`va in by()=True`；12 条指令 |
| [C-find] | `find . -type f -name 'except_post_*.txt' \| wc -l`（及 `-printf '%h\n'`） | `113`；distinct dirs 60+ |
| [D] | `find . -type f -name 'except_post_*.txt' -print0 \| sort -z \| xargs -0 sha256sum > /tmp/w9_q4_hashes.txt` + `cut\|sort\|uniq -c` + `grep -c/-vc '^6694b75e…'` | `files hashed: 113`；`113 6694b75e…`；`matching=113 / NOT=0`；无任何不同哈希 |
| [E] | `find . -type f -name 'except_post_*.txt' -printf '%s\n' \| sort \| uniq -c` | `113 26405` |
| [F] | `find <subtree> -name 'except_post_*.txt' \| wc -l` + 整仓减 | `107` / `6` |
| [G] | 6 份清单 + 列出 | 见 §1 |
| [H] | `find ... -printf '%TY-%Tm-%TdT%TH:%TM:%TS %p\n' \| sort` | `2026-10-17T08:14:58 .. 2026-11-04T18:26:58` |
| [I] | `cmp -s <EXCEPT> <3 代表 except_post>` | 三份全 `IDENTICAL` |
| [J] | `stat -c '%y %s %n'` EXCEPT 与最早件 | `2026-10-19 13:54:38` / `2026-10-17 08:14:58` |
| [K] | 文件名时间戳排序 | `20261017T081458810997 .. 20261104T182658693950` |
| [R]/[S] | `sed -n '1,17p' <最早件>` / `diff <EXCEPT> <最早件>` | 头部全等 / diff 空 exit=0 |
| [T] | 按文件名时间戳与 `20261019T1352` 比较 | `58` 早于 / `55` 不早于 |
| [O]/[P] | `find -name 'except.txt' -print0 \| xargs -0 sha256sum` | 102 份 / 8 哈希 / **91 份 == 目标**；`_src_L3_sf10c_20261021/except.txt` 同哈希 |
| [Y7] | `ra2bench/except.txt` 哈希+头 | `ca175a71…` / 26,515 B / `EXCEPTION_ACCESS_VIOLATION @006F9DB6` |
| [Y13]/[Y14] | odd-named `except_*.txt` 逐一哈希 | 15 份中 3 份同哈希，含 `except_carrier_6694b75e.txt` |
| [Z] | `qc151_trip.py:5938-5939,6042-6052` 读源码 | `copy_post_except_evidence` 在 `finally` 的 guarded-steps 第 1 项，无条件 |

探针与原始输出：`_w9_q4.py` / `_w9_q4_out.txt`（本目录，113 行）。
`_w9_q4_out.txt` 内 `[F]` 段由脚本按实算数据自动判定为 `同哈希（SAME-HASH）`，非手写。

---

## 7 · 诚实账 / 未验

1. **亲验**：两份 SHA256+字节数、Engine 自证（真 `Engine()`）、`e.rd/e.by()/e.disasm` 32 字节、
   整仓 `find` 113 份、113 份逐份 SHA256、113 份逐字节全文比对、尺寸/mtime/时间戳分布、
   上游 102 份 `except.txt`、15 份 odd-named、harness 复制源码调用点、旧分析/台账/LOG 原文。
2. **口径声明**：整仓 `find` 剪枝仅 `.git`（561,979 行清单，Python 侧按 basename 过滤）；
   §555/§590 的 107 是单子树口径。二者不矛盾，但**报数按本项整仓 113**。
3. **未验（不把「查不到」当「不存在」）**：
   - **37 个 archive 逐趟 console / 是否另有别的崩溃形态** —— §555 诚实账第 3 条（:5570）仍未闭，Q4 不触碰。
   - **「游戏是否会崩」** —— 不能由本结论推出；本结论只说现有 `except_post` 语料无信息量。
   - **WER `LiveKernelEvent 193/0x80e ×2`（LOG :1964）** 的真实性/与 13:49、13:52 两次发射的关联 —— 静态不可核，记未验。
   - **「13:52 那趟是否真的产生过一次 0x7CFC9F 异常」** —— 本项证的是「手上这份文件不是那趟的产物」；
     那趟**可能**另外产生过异常但未留存、也可能没有。此项**未验**，不写死。
   - **两套基线（AV@0x6F9DB6 的 ra2bench 母本 vs SINGLE_STEP@0x7CFC9F 的 L3 模板）各自的来源与写入时序** —— 记未验。
   - **`except.txt` 在真实崩溃时是否会被游戏追加/改写** —— 属 Q5 路线（需读 handler / 实测），本项未验。
   - **Q1/Q2/Q3 的结论** —— 本项不复核、不采信、不反驳；仅独立用到 `[C]` 段的字节自证。
4. **零真机、零采样注入（E3 维持暂停 D-13）、零活进程读取、未改任何既有文件、
   唯一写域 = `W9_SINGLESTEP_7CFC9F/`、未 commit、未 push。**
   探针曾因 Windows `find.exe`/MSYS glob 产生两次「命中 0」的中间输出，已定位并修正为
   `D:\Git\usr\bin\find.exe` + `-prune` 写法；失败中间件 `_w9_q4_stdout.txt` 已删，
   最终 `_w9_q4_out.txt` 为 `rc=0 / 命中行数=561979` 那次成功运行所写。
