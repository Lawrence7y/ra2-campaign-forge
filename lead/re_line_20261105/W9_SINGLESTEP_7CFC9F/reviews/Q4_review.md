# Q4 独立复核 · `Q4_RELATION.md` 与 `_w9_q4.py` / `_w9_q4_out.txt`

> 复核员：独立复核员·Q4（默认怀疑）。复核时刻 2026-11-06 03:4x–04:1x。
> 被复核件：`D:/Project/ra2-campaign-forge/lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/`（下称 `W9/`）
> 下的 `Q4_RELATION.md`、`_w9_q4.py`、`_w9_q4_out.txt`。
> 零真机、零采样代码、零活进程读取；**唯一写域 = `W9/reviews/`**（本次新建
> `_Q4_review_probe.py` / `_Q4_review_probe_out.txt` / `_Q4_review_probe_stdout.txt` /
> `_Q4_exact_rerun.py` / `_Q4_exact_rerun_out.txt` / `_Q4_exact_rerun_stdout.txt`、本件）。
> 记法：`Q4_RELATION.md:L` = 回件行；`_w9_q4.py:L` / `_w9_q4_out.txt:L` = 探针行；
> `TASK.md:L` = `W9/TASK.md` 行；其余一律给仓库相对路径 + 行号。

---

## 0 · 复核结论（先给答案）

| 项 | 值 |
|---|---|
| **verdict** | **PARTIAL** |
| **sha256BindingPresent** | **true** —— `Q4_RELATION.md:10-15` 真含两个自算 64 位 SHA256 + 两个字节数 + Engine 自证 + 回件时刻 |
| **independentlyReproduced** | **true** —— 本次自写探针、`sha256sum`/`wc -c`、GNU `find` 全量哈希、原探针逐字重跑，四路独立复现 |
| **核心二选一（Q4 受命问题）** | **CONFIRMED** —— EXCEPT 件与整仓 113 份 `except_post_*.txt` 同哈希、逐字节全等，113/113，反例 0 |
| **REFUTED 判定 / 全局性解释** | **PARTIAL，部分被反证**（见 §3.3、§3.4、§4）—— 找到 4 组反例，其中 1 组直接推翻「不是任何一趟的崩溃」 |
| **substantiveDefect** | **有**（§3.3 / §3.4 / §3.5 / §5），但**不推翻二选一本身** |

**一句话**：Q4 把它受命要答的那一问（`TASK.md:61-68` 的「是否就是那 107 份之一」）答对了，
且哈希比对**确为全量、该全量**；但它把这个口径内的结论外推成
「该证据不是任何一趟的崩溃」「该异常从未在任何一趟发生」
「目标② 目前没有一件把某次异常归因到某趟游戏运行的证据」，
而仓内静态可读的记录（`qc124_observe_chain/QC124_VERDICT.json`）显示
`6694b75e…` 这 26,405 B **本身是某一趟运行期写出的 except.txt**（DR0 断点命中），
其寄存器与 EXCEPT 件 L11-14 逐字全等。Q4 全文未提 QC124 / DR0 / qc164 / drift，
把这些本可读到的记录漏在了「未验」里，于是 REFUTED 的论据被反证。

---

## 1 · 点名检查 1：回件是否真含自算 SHA256 头部（两个哈希都要）

**结论：真含，两个哈希都是自算的，且我独立复算一致。**

`Q4_RELATION.md:9-15` 原文：

```
被核对象 = gamemd.exe + EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360
EXCEPT 件 SHA256 = 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251，字节数 = 26405
Engine 自证 = COVERAGE 99.998375677293% (1394120 insns, 66 resync-fails) / IMAGEBASE 0x400000
回件时刻 = 2026-11-06 02:12
```

五个字段齐全，符合 `TASK.md:77-83` 模板。**「自算」可追**：`_w9_q4.py:105-120`
的 `[A]` 段用 `sha_file()`（`:44-45`，`hashlib.sha256(Path(path).read_bytes())`）
自己读盘算，没有抄 `TASK.md:19` 的期望值；`_w9_q4.py:125-136` 真实例化 `Engine()`。
（`ra2tool.py:29,55` 的 `EXPECT_SHA` 是 `Engine()` 构造内的 assert，不是 Q4 头部来源。）

**本次实跑 C-R1**（Git-Bash 原生 `sha256sum` + `wc -c`）：

```
cd "D:/Project/ra2-campaign-forge" && sha256sum "ra2youli/gamemd.exe" && wc -c "ra2youli/gamemd.exe" && EX="out/re_work/work_chain/CONTINUE_20261003/lead/boot_hang_triage_20261018/EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt" && sha256sum "$EX" && wc -c "$EX"
```

输出：

```
73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 *ra2youli/gamemd.exe
4825360 ra2youli/gamemd.exe
6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251 *out/re_work/.../EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
26405 out/re_work/.../EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
```

**本次实跑 C-R2**（自写探针，不调用 `_w9_q4.py`）：
`python -I -X utf8 W9/reviews/_Q4_review_probe.py` → `EXIT=0`，
`reviews/_Q4_review_probe_out.txt:4-5` 用 `hashlib` 独立读盘得同值同字节数；
`:6-7` 打印 EXCEPT 首行/第 3 行（`EXCEPTION_SINGLE_STEP` / `Exception occurred at 007CFC9F`）。

**本次实跑 C-R3**（原探针逐字重跑，只改 OUT 路径）：
把 `_w9_q4.py` 复制为 `reviews/_Q4_exact_rerun.py`，语义差异仅 1 行：
`L26 OUT = ROOT + r"\...\_w9_q4_out.txt"` → `r"\...\reviews/_Q4_exact_rerun_out.txt"`。
`python -I -X utf8 reviews/_Q4_exact_rerun.py` → `EXIT=0`；
`reviews/_Q4_exact_rerun_out.txt:9-12` 自算得同值；113 行输出与既有
`_w9_q4_out.txt` 逐行比对，**除 `[find] 命中行数=561979` vs `562167`（仓库漂移）外全等**。
⇒ 头部不是手写/抄的，是探针真跑生成的。

> 轻微 objection：`Q4_RELATION.md:14` 写「回件时刻 = 02:12」，
> 而 `Q4_RELATION.md` 文件 mtime = `2026-11-06 02:15:47`、
> `_w9_q4_out.txt` mtime = `02:12:08`、`_w9_q4_out.txt:4` 探针自报 `02:10:46`。
> 三个时刻口径未在正文说明（与 Q2_review.md:60 同类问题）。不影响哈希绑定。

---

## 2 · 点名检查 2：结论是否有「反汇编地址 + 原始字节」支撑，还是只给了地址

**结论：有，且我独立重跑了反汇编与字节读，逐项一致。不是只给地址。**

`Q4_RELATION.md:141-156`（§3）给出
`e.rd(0x7CFC9F,32) = 8B 0A 2B 4D F0 … 8B 4A`、
EXCEPT L17 逐字节比对、`fo(0x7CFC9F)=0x3cfc9f`、
`va in e.by()=True`、`e.disasm(VA,32)` 12 条、前 8 条逐条列
`0x7CFC9F 8B0A mov ecx, dword ptr [edx]` … `0x7CFCB0 7E03 jle 0x7cfcb5`。
`_w9_q4_out.txt:25-44` 是对应探针输出。

**本次实跑 C-R4**（自写探针 `[R2]` 段，`reviews/_Q4_review_probe_out.txt:8-25`）：

```
[R2] Engine.sha == 自算 : True
[R2] IMAGEBASE = 0x400000
[R2] fo(0x7CFC9F) = 0x3cfc9f (VA-0x400000=0x3cfc9f)
[R2] COVERAGE = 99.998375677293% / 1394120 insns / 66 resync-fails
[R2] e.rd(0x7CFC9F,32) = 8B 0A 2B 4D F0 8B F1 89 4D F8 C1 FE 04 4E 83 FE 3F 7E 03 6A 3F 5E 3B F7 0F 84 0D 01 00 00 8B 4A
[R2] EXCEPT L17 解析 = 8B 0A … 8B 4A (len=32)
[R2] rd[0:32] == EXCEPT L17 : True ; diff idx = []
[R2] VA in e.by() = True
[R2] e.disasm(VA,32) 条数 = 12
     [0] 0x007CFC9F 8B0A         mov     ecx, dword ptr [edx]
     … [7] 0x007CFCB0 7E03         jle     0x7cfcb5
[R2] by()[VA] bytes=8B0A mov ecx, dword ptr [edx]
```

我也自己读了证据件原文（命令 `sed -n '11,17p' <EXCEPT>`），
L17 = `Bytes at CS:EIP (007CFC9F)  : 8B 0A 2B 4D F0 … 8B 4A`，
L11-14 寄存器行 = `Eip:007CFC9F Esp:00F9C614 Ebp:00F9C634` /
`Eax:0D94B7B8 Ebx:03BE0610 Ecx:0D94F574` /
`Edx:0E73276C Esi:7FFFFFFF Edi:00000001` / `EFlags:00000286`。

**Q4 的结论也都有「文件:行」支撑**，我逐项核过：
- 复制机制：`W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py:6029-6050`
  （`src = carrier_dir / "except.txt"` → `blob = src.read_bytes()` →
  `dst.write_bytes(blob)`，`:6042-6050`）；
  `out/.../qc151_u0400_trip/qc151_trip.py:5938-5939`（`_except_evidence_copy()`）、
  `:6042-6052`（`run_guarded_steps([...])` 第 1 项
  `"except_evidence_copy_and_verify"`）、`:5929-5931`（docstring「本函数在 `finally` 内执行」
  /「收尾项逐个落盘、各自独立、互不跳过」）；
  `out/.../evid_diffmode_20261019/qc151_trip_eviddiff.py:3645` 同逻辑。
- `EXCEPT_MASTER`：`qc151_trip.py:228-230` =
  `EXCEPT_MASTER = BENCH / "except.txt"` / `ca175a71…` / `26515`；
  我实算 `ra2bench/except.txt` = `ca175a71c8a2…f39d` / 26515 B /
  L1 `EXCEPTION_ACCESS_VIOLATION` / L4 `Exception occurred at 006F9DB6`
  （`reviews/_Q4_review_probe_out.txt:78`）。
- §555 / §590 / LOG：`GOAL_THREE_TARGETS_20261018.md:5473-5476`、
  `:5564-5571`（诚实账第 3 条：「0 趟崩溃这条结论我未独立验证」）、
  `:8488-8496`（§590 自陈 `os.walk` 只在单子树）、`:8507-8512`；
  `ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:1898`、`:1962-1969`。
- 旧分析：`out/.../boot_hang_triage_20261018/SINGLESTEP_0x7CFC9F_ANALYSIS.md:12`
  （「一个真实的…外源陷阱…置信度高」）、`:51`（「指令尚未执行」）、
  `:61,68`（DR/TF 候选）、`:89,92`（「巧合地址」「掩盖假说成立」）——
  Q4 §5 点名的条目编号与原文一致。

⇒ **检查 2 通过**：不是只给地址，字节 + 反汇编 + 文件行都齐。

---

## 3 · 点名检查 3：Q4 的哈希比对该不该全量 + 默认找反例

### 3.1 该全量，且 Q4 在其受命口径内确为全量（CONFIRMED）

`TASK.md:64-67` 把判据写成「自己算它的 SHA256，并与 `except_post_*.txt` 的哈希比对
（`find` + `sha256sum` 或 python）」，且称「本节最关键的一问」。
单一哈希/前缀比对只给必要条件；「107 份彼此同哈希」与
「这件 EXCEPT 是其中之一」是方向不同的两个命题，必须逐份算完整 64 位哈希
（或逐字节比）才能排除「107 份是另一份仅前缀相同的文件」。
⇒ **该全量，抽样或借用 §555 记的 `6694b75e…` 前缀都不够。**

Q4 实现核对：`_w9_q4.py:165` `posts = find_named(ROOT, "except_post_*.txt")` →
`:168-170` `for fp in posts: sha_file(fp)` 逐份算 → `:171-172` 逐份比对 →
`:188` `Path(r[2]).read_bytes() == exc_bytes` 全文逐字节比（非比长度/前缀）→
`:271-275` 仅当 `len(same)==len(recs) and len(diff)==0` 才判 SAME-HASH。

**本次独立全量实跑 C-R5**（GNU find，与 Q4 实现不同）：

```
cd "D:/Project/ra2-campaign-forge"
find . -path ./.git -prune -o -type f -name 'except_post_*.txt' -print0 | sort -z | xargs -0 sha256sum > /tmp/rev_q4_hashes.txt
wc -l < /tmp/rev_q4_hashes.txt
cut -d' ' -f1 /tmp/rev_q4_hashes.txt | sort | uniq -c
grep -vc '^6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251' /tmp/rev_q4_hashes.txt
```

输出：`113` / `113 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` / `0`。
另跑 `find . -type f -name 'except_post_*.txt' | wc -l`（不 prune `.git`）= `113`、
`-iname` = `113`、`-type l -name 'except_post_*.txt'` = 空、
`find . -type f -iname '*except_post*' | wc -l` = `114`
（多出的 1 份是 `T42E4_FORENSIC_085458ab/_except_post.py`，非 .txt，不算反例）。
`W9/re_line_20261105` 树下 `except_post_*.txt` = 0 份 ⇒ 无自我污染。

`reviews/_Q4_review_probe_out.txt:27-31` 用第二套实现复核：
`总数 = 113 / 同哈希 = 113 / 不同 = 0 / distinct = 1 / 逐字节全文 == EXCEPT = 113/113 /
尺寸集合 = [26405]`。
`reviews/_Q4_exact_rerun_out.txt:47-57,99-103` 逐字重跑亦同。

**Q4 其余数字我也独立复现**：107 + 6（子树 107、外 6 份逐名列全等，命令
`find ... | grep -v <subtree> | wc -l` → `6`）、
mtime 范围 `2026-10-17T08:14:58 .. 2026-11-04T18:26:58`、
文件名时间戳 `58` 早于 / `55` 不早于 `20261019T1352`、
`stat` EXCEPT = `2026-10-19 13:54:38`、最早件 = `2026-10-17 08:14:58`、
`cmp -s` / `diff` 与 EXCEPT 全等（`diff rc=0`）、
上游 `except.txt` `102 / 8 / 91`、odd-named `15 / 3`、
ra2bench 母本 `ca175a71… / 26515 / ACCESS_VIOLATION`。
全部与 `Q4_RELATION.md` 及 `_w9_q4_out.txt` 一致（`reviews/_Q4_review_probe_out.txt:76-83`）。

⇒ **该全量、Q4 做了、我做的结果一样。这一问 CONFIRMED。**

### 3.2 反例 A：全仓 `7CFC9F` SINGLE_STEP 件不止一份字节（Q4 只计数未读内容）

`Q4_RELATION.md:111-112`、`:223` 只报「102 份 `except.txt` / 8 哈希 / 91 份 == 目标」，
**从未逐件打开那 11 份不同哈希件**。我独立猎捕（命令见下）：

```
find . -path ./.git -prune -o -type f -name 'except*.txt' -print0 | xargs -0 grep -l '007CFC9F' \
  | while read -r f; do h=$(sha256sum "$f" | cut -d' ' -f1); \
      [ "$h" != "6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251" ] && echo "$h  $f"; done | sort
```

输出 **5 份 / 4 个不同哈希**（`reviews/_Q4_review_probe_out.txt:33-39` 给出
`212` 份含 `007CFC9F`、`distinct=5`、非目标 `x5`）：

| 文件（`out/re_work/work_chain/CONTINUE_20261003/lead/`） | SHA 前缀 | size | Eip | Esp | Edx |
|---|---|---:|---|---|---|
| `qc119_after_entry/carrier/except.txt` | `77f5a4cb` | 26324 | `007CFC9F` | `00F9BE34` | `0E75276C` |
| `qc120_entry_then_arm/carrier/except.txt` | `27eef06b` | 26459 | `007CFC9F` | `00F9C614` | `0E74276C` |
| `qc121_entry_then_arm/carrier/except.txt` | `ca1acc37` | 26468 | `007CFC9F` | `00F9C124` | `0EFA276C` |
| `qc123_rc1_only/carrier/except.txt` | `94656085` | 26621 | `007CFC9F` | `00F9C614` | `0E7EA76C` |
| `qc124_observe_chain/_backup/except_pre_qc124.txt` | `ca1acc37` | 26468 | `007CFC9F` | `00F9C124` | `0EFA276C` |

5 份首行均为 `Error code: EXCEPTION_SINGLE_STEP`、第 3 行均为
`Exception occurred at 007CFC9F`，L17 的 `Bytes at CS:EIP` 与 EXCEPT 件相同，
但 **Esp / Edx / Eax 各不相同**（逐件 `sed -n '1,3p;11,14p;17p'` 实读）。
mtime 全部 `2026-10-16 18:39..19:07`，**也早于 13:52**。
（`Q1_review.md:145-172` 的 C-R6 已报同组反例：其计数 `1+1+1+2=5` 与我一致，
表格只列了 4 行；本次额外点名第 5 份 `qc124_observe_chain/_backup/except_pre_qc124.txt`。）

⇒ **Q4 的「历史基线残件 / 主崩溃叙事重新定位」只在
手上这一件 EXCEPT + 113 份 `except_post_*` 上被坐实，不能外推成
「仓内所有 7CFC9F SINGLE_STEP 件都是同一份残件」。**
注意：这 5 份的**性质/来源**我只读了头部与哈希，**未验**，不推断其为真捕获还是构造件。

### 3.3 反例 B（最实质）：`6694b75e…` 字节本身被仓内记录为某趟运行期写出

这一条直接反证 Q4 的全局性断言。我**静态读**（零真机）到一条完整的写入链：

1. `out/.../qc124_observe_chain/QC124_VERDICT.json:8`：
   「挂 RC1 后命中 ⇒ 进程在挂点后 0.63 s 终止，载体 `except.txt` 记为
   `EXCEPTION_SINGLE_STEP @ 007CFC9F`（**= 我设的 DR0**）。这是断点异常无人处理的
   必然后果，不是游戏本身的崩溃。」
2. 同件 `:35-72` `group2_rc1_armed`：
   `single_bp = {"name":"RC1","va":"0x007CFC9F","dr":"DR0"}`、
   `except_file_rewritten: true`、
   `except_pre_sha256 = e369a911…`（`qc116/…/carrier/except.txt`，我实算一致）、
   **`except_post_sha256 = 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251`**、
   `error_code = EXCEPTION_SINGLE_STEP`、`eip = 007CFC9F`、
   `bytes_at_cs_eip` 与 EXCEPT L17 逐字相同、
   `regs_at_hit_from_carrier_dump`（`:60-63`）：
   `Eip:007CFC9F Esp:00F9C614 Ebp:00F9C634 / Eax:0D94B7B8 Ebx:03BE0610 Ecx:0D94F574 /
   Edx:0E73276C Esi:7FFFFFFF Edi:00000001 EFlags:00000286`
   —— **与 EXCEPT 件 L11-14 逐字全等**（我实读比对，见 §2）。
3. 同件 `:12-33` `group1_no_breakpoint`：`breakpoints_armed: 0`、
   `except_file_rewritten: false`、`except_post_sha256 = e369a911…`、
   「活满 138.68 s、`except.txt` 逐字节未被触碰」；
   `:74-87` `group3_discrimination`：「第 2 组的死 = EXCEPTION_SINGLE_STEP（断点异常），
   不是原始崩溃」，并给出 5 条判据含不挂断点的对照臂。
4. 独立登记链：`out/.../qc161_audit_T11/VERDICT_T11.md:148`（§9.3 ②）：
   「`except.txt`：26,405 B / `6694B75E…` … mtime **2026-10-16 19:21:11**
   （**qc124 观测趟运行期写出**），早于 T11 一天」；
   `out/.../qc164_a4_prep_20261017/ERRATA_EXCEPT_RESTORE.md:12`：
   `"before": {"size": 26405, "sha256": "6694b75e…aac251", "mtime": "2026-10-16T19:21:11+08:00"}`、
   `"reason": "漂移系 qc124 观测趟运行期写出（游戏整体重写 except.txt）"`、
   `"action": "restore-from-ra2bench"`（2026-10-17 22:43 把该件恢复成 `ca175a71…`）；
   `BASELINE_A4_PROPOSAL.md:79`（「qc124 观测趟运行期写出」）、`:92`、`:104`
   （「漂移值现存 18 份」）、`:106`（把 `qc119/120/121/123` 的 4 个不同哈希
   列为「其他历史值」）。
5. 漂移字节实体仍在：`out/.../qc164_a4_prep_20261017/raw/except.drift.6694B75E.26405B.bin`，
   我实算 `sha256sum` = `6694b75e…a8c251`、`wc -c` = `26405`，
   `head -c 400` 首行 `EXCEPTION_SINGLE_STEP` / `Exception occurred at 007CFC9F`，
   mtime `2026-10-16 19:21:11`。

⇒ **按仓内自身记录，`6694b75e…` 这 26,405 B 不是「从来不是任何一趟的产物」，
而是 2026-10-16 QC124 第 2 组（DR0@0x7CFC9F armed）跑后由游戏重写 `except.txt`
留下的快照**，随后被 `qc164` 明确「另存/恢复」、被后续 113 趟 harness 反复复制。
它**确实不是 2026-10-19 13:52 那趟的产物**（Q4 的时间反证成立），
但 Q4 的以下措辞被反证：

- `Q4_RELATION.md:25` / headline「**该证据不是任何一趟的崩溃**，是历史基线残件」；
- `Q4_RELATION.md:170`「**若该异常从未在任何一趟发生**，则『TF/DR 施动者』…全部失去观测基础」；
- `Q4_RELATION.md:173`「**⇒ 目标② 目前没有一件「把某次异常归因到某趟游戏运行」的证据。**」
  —— `QC124_VERDICT.json` 正是这样一件（把一次 `EXCEPTION_SINGLE_STEP` 归因到
  特定趟、特定 DR0、并给出对照臂）；
- `Q4_RELATION.md:190-192` 把旧分析的错误定为「把…历史基线残件，当成一次真实发生于
  13:52 那趟的 CPU #DB 异常现场」——**这一条（针对 13:52）仍成立**，
  但紧接着「该异常从未在任何一趟发生」的推论不成立。

**Q4 全文未提这条链**：命令
`grep -n -i 'QC124\|DR0\|qc164\|ERRATA\|drift' Q4_RELATION.md` 只命中
`6694b75e` 相关行，**零命中 QC124 / DR0 / qc164 / ERRATA / drift**。
同时 `Q4_RELATION.md:246` 把「两套基线各自的来源与写入时序」列入「未验」，
`:247` 把「`except.txt` 在真实崩溃时是否会被游戏追加/改写」列入「未验」——
而 `QC124_VERDICT.json:48` `except_file_rewritten: true`、
`QC121_except_rejudge.json:49` 「`except.txt` 系整文件重写（每趟被游戏重写、非追加）」
已在仓内给出书面答案（属旧趟真机记录，本任务零真机**不能重新复现**，
但**静态可读**）。⇒ **Q4 的「未验」清单与其 §0/§4 全局断言自相矛盾**：
一边说来源/写入时序未验，一边断言「不是任何一趟的崩溃」「无一件归因证据」。

> 边界说明（不越界）：上述 QC124/VERDICT_T11/ERRATA 是**仓内既有的书面记录**，
> 我本次只读了这些文件、算了相关 SHA256 与 mtime，**没有启动任何进程、
> 没有重新复现那次运行**。故我的表述是「Q4 的结论被仓内既有记录反证」，
> 不是「我独立验证了 QC124 那趟真机事件」。Q4 若坚持「静态不可核」，
> 应把结论收窄为「手上这件 EXCEPT 不是 13:52 那趟的产物」，而非全局断言。

另：Q3 回件 `Q3_MECHANISM.md:210,264-272` 把「DR0-3 执行断点 @0x7CFC9F」
列为与 `EFlags=0x286` 兼容的头号候选、并说「本件无 DR6 ⇒ 未验」；
`QC124_VERDICT.json` 恰是「有人设了 DR0」的书面记录。
⇒ **Q4 判 REFUTED 所依赖的「施动者假说失去观测基础」也因此站不住**，
至少应改判为「有一条仓内书面记录支持 DR0 施动者，其可靠性未独立复核」。

### 3.4 反例 C：Q4 的「母模板」时序倒置

`Q4_RELATION.md:112-115`、`:223` 称
`_src_L3_sf10c_20261021/except.txt` 是「母模板 / 历史固有的基线文件」
（引 `XVERIFY_S544_ae38d56c/V3/_write_report.py:29`，我实读该行确实这么写）。
但 mtime 实跑：

```
stat -c '%y | %n' \
  out/.../qc161_u0400_trip/_src_L3_sf10c_20261021/except.txt \
  out/.../qc161_u0400_trip/archive_T5/except_post_20261017T081458810997.txt \
  out/.../qc164_a4_prep_20261017/raw/except.drift.6694B75E.26405B.bin
```

输出：

```
2026-10-17 22:16:07 | .../_src_L3_sf10c_20261021/except.txt      (Q4 的「母模板」)
2026-10-17 08:14:58 | .../archive_T5/except_post_20261017T081458810997.txt  (最早副本)
2026-10-16 19:21:11 | .../qc164_a4_prep_20261017/raw/except.drift...bin     (漂移留痕)
```

⇒ 所谓「母模板」比它自己的「副本」晚 14 小时，比漂移留痕晚约 27 小时，
**不是来源而是后续副本**；Q4 照抄 XVERIFY 的「历史固有基线」说法未做时序核对。
这不改变「113 份同哈希」，但削弱 Q4 §2.3 关于「哪份基线被复制进载体」的叙事。

### 3.5 反例 D：Q4 对 §590「42 小时」的解释不成立

`Q4_RELATION.md:70-73`：「§590 的「42 小时」是其单子树/子集口径，整仓更宽」。
我实跑**同一 107 份子树**的 mtime/文件名时间戳：

```
find out/.../qc161_u0400_trip -type f -name 'except_post_*.txt' -printf '%TY-%Tm-%TdT%TH:%TM:%TS\n' | sort | awk 'NR==1{min=$0}{max=$0}END{print min;print max}'
```

输出 `2026-10-17T08:14:58 .. 2026-11-04T18:26:58`（**约 18 天**）；
其中落在 §590 声称的 `2026-10-18 04:41 .. 2026-10-19 22:39` 窗口内的只有 **44 / 107**。
⇒ 单子树口径同样是 18 天，Q4 把 §590 的 42 小时归因为「范围窄」**没有依据**；
更可能是 §590 当时的子集/陈旧数字有误。Q4 用「这反而更强地支持残件复制」
收尾，结论方向不受影响，但**归因是错的**。

### 3.6 其它小 objection（不降判定）

- `Q4_RELATION.md:100-105` 称 harness「**无条件**复制载体 `except.txt`」：
  `W5_HARNESS_EXT/...:6042-6046` 实有 `if not src.exists(): … return None` 守卫，
  严格说是「载体存在时无条件、不以本趟是否发生异常为条件」。后者 Q4 说对了，
  「无条件」三字不精确。
- `Q4_RELATION.md:251-253` 自述曾因 `find.exe`/MSYS glob 产生两次「命中 0」并删中间件
  `_w9_q4_stdout.txt`：目录中确无该文件，与自述一致；但这段是**自报**，
  我无法从现有文件独立验证中间失败曾发生，记为「未验」。
- 仓库漂移：Q4 `_w9_q4_out.txt:47` `find` 清单 `561979` 行、
  我自写探针 `562151` 行、原探针逐字重跑 `562167` 行（`reviews/_Q4_review_probe_out.txt:26`、
  `reviews/_Q4_exact_rerun_out.txt:45`）。三次不同时刻、并行兄弟任务在加文件；
  `except_post_*.txt` 计数与哈希结论三次均 `113/113` 同哈希，不受影响
  （与 `Q1_review.md:302` 同因）。

---

## 4 · 对 Q4 判定档（REFUTED）的复核结论

| Q4 的结论 | 本次裁定 | 依据 |
|---|---|---|
| 二选一 = **同哈希**（EXCEPT == 113 份 `except_post_*`） | **CONFIRMED** | §3.1，四路独立全量复现 |
| 手上这件 EXCEPT **不是 2026-10-19 13:52 那趟**的产物 | **CONFIRMED** | 时间反证：最早件 `2026-10-17 08:14:58` 与其逐字节全等，`stat`/`cmp`/`diff` 实跑；harness 复制源码 |
| 「**不是任何一趟的崩溃**」「**该异常从未在任何一趟发生**」 | **REFUTED（被仓内记录反证）** | §3.3：`QC124_VERDICT.json:8,35-72`、`VERDICT_T11.md:148`、`ERRATA_EXCEPT_RESTORE.md:12` 记 `6694b75e…` 为 QC124 第 2 组 DR0 命中后运行期写出的 `except.txt` |
| 「**目标② 目前没有一件把某次异常归因到某趟游戏运行的证据**」 | **REFUTED** | §3.3：`QC124_VERDICT.json` 即为此类证据（含对照臂与 5 条判据） |
| 旧分析 `SINGLESTEP_0x7CFC9F_ANALYSIS.md` 把该件当 **13:52 真实 #DB 现场** | **REFUTED 成立**（Q4 这部分对） | 该件 mtime `2026-10-19 13:54:38` 但内容早 2 天已存在；`ROUND_SUBAGENT_LOG:1898,1962-1969` 把「跑后总有快照」误读成「必现异常」 |
| 旧分析的「TF/DR 施动者 / 巧合地址 / 掩盖假说」**全部失去观测基础** | **PARTIAL，论据不成立** | §3.3 末：Q3 与 QC124 书面记录均支持 DR0 施动者；只能说「13:52 那趟」无观测基础 |
| 107 是单子树口径、整仓 113 | **CONFIRMED** | §3.1，`107 + 6 = 113` 实跑 |
| §590「42 小时」是单子树/子集口径 | **REFUTED** | §3.5，同一子树 mtime 跨 18 天，窗口内仅 44/107 |

⇒ **综合 verdict = PARTIAL**：Q4 的核心二选一、SHA256 绑定、字节/反汇编证据、
源码与台账引用、时间反证对「13:52」的否定都通过独立复核；
但 REFUTED 判定所依赖的「该异常从未在任何一趟发生」及其 3 条全局性外推
被仓内静态可读记录反证，另有 4 组边界反例未处理。
按 `TASK.md:87-89`，Q4 的 REFUTED 档**可以保留**（确实点名了旧分析的实质错误：
把非 13:52 产物的残件当 13:52 现场），但**必须收窄论据与结论范围**。

---

## 5 · objections（逐条，均带本次读/跑的依据）

1. **【主要】全局性结论超出受命口径。** `TASK.md:65` 只要求比 `except_post_*.txt`；
   Q4 的 headline、`:31-32`、`:168-175`、`:179-201` 却写成「不是任何一趟的崩溃」
   「目标② 目前没有一件把某次异常归因到某趟游戏运行的证据」。
   依据 §3.1（Q4 口径内确为全量）+ §3.2/§3.3（口径外有反例）。
2. **【主要】`6694b75e…` 的来源链被漏读，且与「不是任何一趟的崩溃」直接冲突。**
   依据 §3.3 的 `QC124_VERDICT.json` / `VERDICT_T11.md:148` /
   `ERRATA_EXCEPT_RESTORE.md:12` / drift 实体哈希+mtime，全部本次静态实读实算。
3. **【主要】Q4 的「未验」清单与 §0/§4 断言自相矛盾。** `:246` 自列
   「两套基线各自的来源与写入时序 —— 记未验」、`:247` 自列
   「except.txt 在真实崩溃时是否会被游戏追加/改写 —— 未验」，
   却在 `:173` 断言「没有一件归因证据」。依据 `Q4_RELATION.md:173,246-247` 原文 +
   §3.3 的仓内书面答案。
4. **【主要】REFUTED 的论据「施动者假说失去观测基础」不成立。**
   依据 `Q3_MECHANISM.md:210,264-272`（DR0 执行断点兼容）+ `QC124_VERDICT.json:36,59,82`。
5. **【中】5 份不同哈希的 `EXCEPTION_SINGLE_STEP @ 007CFC9F` 件未逐件读头。**
   依据 §3.2 表格（本次实读），Q4 `:111-112`、`:223` 只报计数。
6. **【中】「母模板 `_src_L3_sf10c_20261021/except.txt`」时序倒置。** 依据 §3.4 的 `stat`。
7. **【中】§590「42 小时」归因错误。** 依据 §3.5 的 107 份子树 mtime 实测。
8. **【轻微】「无条件复制」不精确**（有 `src.exists()` 守卫）；
   **回件时刻 02:12 / 文件 mtime 02:15:47 / 探针 02:10:46 三口径未说明**；
   **中间失败件删除属自报未验**。依据 §3.6。
9. **【轻微】`_w9_q4.py:51-67` 的 `find` 把 `.git` 过滤放在 Python 侧，
   且 `find_named()` 用 `fnmatch` 对整个清单按 basename 过滤**——
   我另跑 `-iname`、含 `.git` 不剪枝、`-type l` 三种更宽口径均为 113 份，
   故本次未造成漏计；但「剪枝仅 .git」的自述与实现（`-prune` + Python 二次过滤）
   略有出入，属实现细节，不影响结论。

---

## 6 · mustFix（给 Q4 / `W9_SINGLESTEP.md` 汇总件的具体改项）

1. **把结论限定到口径内。** 改 `Q4_RELATION.md:25-32`、`:168-175`、`:179-201`
   与 headline 为：「手上这件 EXCEPT 与整仓 113 份 `except_post_*.txt` 是同一份字节；
   它**不是 2026-10-19 13:52 那趟**的产物；仓内 `except_post` 语料对判定该趟崩溃
   无信息量」。删除/改写「不是任何一趟的崩溃」「该异常从未在任何一趟发生」
   「目标② 目前没有一件把某次异常归因到某趟游戏运行的证据」。
2. **补登记 QC124 运行期写入链。** 在 `Q4_RELATION.md` §2 增一节，逐件引用
   `out/.../qc124_observe_chain/QC124_VERDICT.json:8,35-72,74-87`、
   `out/.../qc161_audit_T11/VERDICT_T11.md:148`、
   `out/.../qc164_a4_prep_20261017/ERRATA_EXCEPT_RESTORE.md:12`、
   `BASELINE_A4_PROPOSAL.md:79,92,104`，并给出
   `except.drift.6694B75E.26405B.bin` 的实算 SHA256/字节数/mtime
   与「其寄存器 == EXCEPT L11-14」的比对。把「历史基线残件」改判为
   「QC124 某趟运行期写出的 `except.txt` 快照，后被 harness 反复复制」，
   **或**明确写「该书面记录未被本次静态复核独立复现，列为未验」——
   但不得再反向断言「从未在任何一趟发生」。
3. **逐件处理 5 份不同哈希件。** 列出 §3.2 表格的 5 个路径、各自的 SHA256、
   size、`Eip/Esp/Edx`，说明它们不是 `6694b75e` 基线；若无法判定其性质则列「未验」，
   并删除「仓内 7CFC9F 异常证据全为同一残件」的任何等价表述。
4. **修正「母模板」说法。** `Q4_RELATION.md:112-115`、`:223` 按 §3.4 的 mtime
   把 `_src_L3_sf10c_20261021/except.txt` 改称「后续副本」，并注明 XVERIFY
   「历史固有基线」的说法未经时序核对。
5. **修正 §590「42 小时」的归因。** `Q4_RELATION.md:70-73` 按 §3.5 改为
   「同一 107 份子树 mtime 实为 2026-10-17 08:14 .. 2026-11-04 18:26（约 18 天），
   仅 44/107 落在 §590 窗口内；§590 的 42 小时不能归因为单子树口径」。
6. **REFUTED 档收窄论据。** `Q4_RELATION.md:184-201` 把「实质错误」精确限定为
   「把一件非 13:52 产物的残件当成 13:52 那趟的真实 #DB 现场」；
   删去「若该异常从未在任何一趟发生 ⇒ TF/DR 施动者全部失去观测基础」，
   改为「仓内另有 QC124 书面记录支持 DR0 施动者，其可靠性未独立复核」。
7. **汇总件 `W9_SINGLESTEP.md` 的「## 5 Q4 与主崩溃的关系」「## 7 必须改项」**
   必须与 1–6 一致，并与 `Q1_review.md:278-291`、`Q2_review.md:200,221`
   已提出的 Q4 口径边界对齐；「## 1 SHA256 绑定」可照抄 Q4 头部（已复核为真）。
8. **（轻微）** 在头部或 §6 注明「回件时刻」是正文成稿时刻而非探针运行时刻；
   把「无条件复制」改成「载体 `except.txt` 存在时无条件、不以本趟是否发生异常为条件」。

---

## 7 · 诚实账 / 未验（不把「查不到」当「不存在」）

- **本次亲验**：两个 SHA256 + 字节数（3 路）、Engine 自证 / `rd` / `by()` / `disasm`
  （2 路）、EXCEPT L1/L3/L11-14/L17 原文、整仓 `except_post_*.txt` 全量 113 份
  逐份 SHA256 + 逐字节全文比对（3 路，含原探针逐字重跑）、
  `-iname` / 不剪 `.git` / 符号链接 / 任意 `*except_post*` 四种更宽口径、
  107+6 口径差、mtime/文件名时间戳分布、`cmp`/`diff`、上游 102 份 `except.txt`、
  15 份 odd-named、ra2bench 母本、harness 复制源码 4 处调用点、
  旧分析/§555/§590/LOG 原文、QC124 写入链 5 份书面件、5 份不同哈希件的头部。
- **未验（不填猜）**：
  - QC124 第 2 组那次运行期事件本身 —— 零真机，只读了仓内书面记录，
    **未重新复现**；其记录可靠性按 `Q4_RELATION.md:243` 同规格记「未验」。
  - §3.2 那 5 份不同哈希件的来源/写入时序/是否真捕获 —— 只读了头部与哈希，未验。
  - 37 个 archive 逐趟 console、WER `LiveKernelEvent 193/0x80e ×2`、
    「游戏是否会崩」、「13:52 那趟是否另有未留存异常」 —— 沿用
    `Q4_RELATION.md:241-245` 的未验清单，本次不触碰、不反驳。
  - Q1/Q2/Q3/Q5 回件的其余结论 —— 本复核只答 Q1 已点名的 Q4 哈希全量性、
    Q2 已点名的同一问题，以及本 ask 的 3 项点名检查。
  - `EFlags=0x286` 的位分解 / TF=0 的机制判定 —— 属 Q3，Q4 `:201` 已声明未复核，
    本次同意。
- **铁律核对**：`git status --porcelain -- W9/` → `?? lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/`
  （整树未跟踪）；本次新建件全部在 `W9/reviews/`；
  `stat` 三件只读源（`ra2youli/gamemd.exe` `2026-09-25 16:10:48`、
  EXCEPT 件 `2026-10-19 13:54:38`、`QC124_VERDICT.json` `2026-10-16 19:22:21`）
  mtime 均为旧值，未改；零真机、零采样、未 commit、未 push。

---

## 8 · 实跑命令清单（每个数字可追）

| 编号 | 命令（均在 `D:/Project/ra2-campaign-forge`） | 关键输出 |
|---|---|---|
| C-R1 | `sha256sum ra2youli/gamemd.exe; wc -c …; sha256sum <EXCEPT>; wc -c <EXCEPT>` | `73201cc0…f67476 / 4825360`；`6694b75e…a8c251 / 26405` |
| C-R2 | `python -I -X utf8 W9/reviews/_Q4_review_probe.py`（自写，不调用 Q4 探针） | `EXIT=0`，`reviews/_Q4_review_probe_out.txt:1-84` |
| C-R3 | `python -I -X utf8 W9/reviews/_Q4_exact_rerun.py`（Q4 原探针仅改 OUT） | `EXIT=0`，113 行；与 `_w9_q4_out.txt` 除 `[find] 命中行数` 外逐行全等 |
| C-R5 | `find . -path ./.git -prune -o -type f -name 'except_post_*.txt' -print0 \\| sort -z \\| xargs -0 sha256sum > /tmp/rev_q4_hashes.txt` + `cut\\|sort\\|uniq -c` + `grep -vc` | `113` / `113 6694b75e…` / `0` |
| C-R5b | `find . -type f -name 'except_post_*.txt' \\| wc -l`；`-iname`；`-type l`；`*except_post*` | `113` / `113` / 空 / `114`（1 份 `.py`） |
| C-R5c | `find <subtree> -name 'except_post_*.txt' \\| wc -l` + 整仓差 | `107` / `6`（6 份逐名列出） |
| C-R6 | `stat -c '%y \\| %s \\| %n'`；`cmp -s`；`diff`；文件名时间戳 `awk` | EXCEPT `2026-10-19 13:54:38` / 最早件 `2026-10-17 08:14:58` / `IDENTICAL` / `diff rc=0` / `58+55=113` |
| C-R7 | `find … -name 'except*.txt' -print0 \\| xargs -0 grep -l '007CFC9F'` 逐件再算哈希 + `sed -n '1,3p;11,14p;17p'` | 5 份 / 4 个不同哈希，`Esp`/`Edx`/`Eax` 各异（§3.2 表） |
| C-R8 | `cat QC124_VERDICT.json`；`sed -n '146,152p' VERDICT_T11.md`；`cat ERRATA_EXCEPT_RESTORE.md`；`sed -n '70,109p' BASELINE_A4_PROPOSAL.md` | §3.3 的 5 步写入链 |
| C-R9 | `sha256sum except.drift.6694B75E.26405B.bin; wc -c …; head -c 400 …; stat …` | `6694b75e…a8c251 / 26405 / 2026-10-16 19:21:11` |
| C-R10 | `stat _src_L3_sf10c_20261021/except.txt` vs 最早副本 vs drift bin | `10-17 22:16` > `10-17 08:14` > `10-16 19:21`（§3.4） |
| C-R11 | 107 份子树 `-printf '%TY…%TS\\n'` 排序 + `-newermt '2026-10-18 04:41' ! -newermt '2026-10-19 22:39' \\| wc -l` | `10-17 08:14 .. 11-04 18:26`；窗口内 `44 / 107`（§3.5） |
| C-R12 | `sed -n` 核对 harness 4 处、`qc151_trip.py:228-230`、§555/§590/LOG/旧分析 | 全部行号与原文一致 |

探针与原始输出：`W9/reviews/_Q4_review_probe.py` / `_Q4_review_probe_out.txt` /
`_Q4_review_probe_stdout.txt` / `_Q4_exact_rerun.py` / `_Q4_exact_rerun_out.txt` /
`_Q4_exact_rerun_stdout.txt`。
