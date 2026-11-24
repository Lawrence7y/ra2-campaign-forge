# Q5 独立复核 · `Q5_ROUTES.md` 与 `_w9_q5.py` / `_w9_q5_out.txt`

> 复核员：独立复核员·Q5（默认怀疑）。复核时刻 2026-11-06 04:2x–04:4x。
> 被复核件：`D:/Project/ra2-campaign-forge/lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/`（下称 `W9/`）
> 下的 `Q5_ROUTES.md`（22,405 B / mtime 2026-11-06 03:05:03）、`_w9_q5.py`（4,237 B / 02:47:08）、
> `_w9_q5_out.txt`（2,063 B / 02:48:00）。
> 零真机、零采样代码、零活进程读取；**唯一写域 = `W9/reviews/`**（本次新建
> `_Q5_review_probe.py` / `_Q5_review_probe_out.txt` / `_Q5_review_probe_stdout.txt` /
> `_Q5_exact_rerun.py` / `_Q5_exact_rerun_out.txt` / `_Q5_exact_rerun_stdout.txt`、本件）。
> 记法：`Q5_ROUTES.md:L` = 回件行；`_w9_q5.py:L` / `_w9_q5_out.txt:L` = 探针行；
> `TASK.md:L` = `W9/TASK.md` 行；其余一律给仓库相对路径 + 行号。

---

## 0 · 复核结论（先给答案）

| 项 | 值 |
|---|---|
| **verdict** | **PARTIAL** |
| **sha256BindingPresent** | **true** —— `Q5_ROUTES.md:1-5` 真含两个自算 64 位 SHA256 + 两个字节数 + Engine 自证 + 回件时刻 |
| **independentlyReproduced** | **true** —— 本次 `sha256sum`/`wc -c`、自写 clean-room 探针、GNU `find` 全量哈希+全文 `cmp`、原探针逐字重跑，四路独立复现 |
| **点名检查 1（自算 SHA256 头部，两个哈希都要）** | **CONFIRMED** —— 见 §1 |
| **点名检查 2（反汇编地址 + 原始字节，不是只给地址）** | **CONFIRMED，但有 1 处行号/证据归属错误** —— 见 §2 |
| **点名检查 3（Q4 哈希比对该不该全量）** | **该全量；Q5 做了；我全量重做结果一致** —— 见 §3.1 |
| **默认找反例** | **找到 1 个实质反例 + 3 组边界反例** —— 见 §3.2–§3.5 |
| **substantiveDefect** | **有**（§3.2 / §3.3 / §3.4），但**不推翻**哈希绑定、字节/反汇编、全量比对这些硬事实 |

**一句话**：Q5 的强制头部、两个 SHA256、`Engine` 字节/反汇编/函数边界、`113/113` 全量哈希、
`20 distinct / 206 / b42c7014 命中 2 份`、`68 份 new_exception_count=0`、两套母本、mtime、
harness 源码行号——**本次全部独立复现，数字无一错**。三条路线也都齐备
「需要什么数据 / 是否受 D-13 限制 / 代价」（`TASK.md:70-73`）。
但 **Q5 把 Q4 的全局断言「目标② 目前没有一件把某次异常归因到某趟游戏运行的证据」
原样当作全部路线的起点**（`Q5_ROUTES.md:23,192,252`），而这断言被仓内
**2026-10-16 即已存在、Q5 写作时静态可读**的 `QC124_VERDICT.json` 反证：
`6694b75e…` 是人为 `DR0=0x007CFC9F` 断点命中后运行期写出的 `except.txt`。
Q5 全文对 `QC124`/`断点`/`人为`/`运行期写出` **零命中**，并把该哈希归类为路线 A 的
「(i) `6694b75e…` 残件类」（`Q5_ROUTES.md:76`）——**分类前提错，连带路线排序理由错**。
另有 `PENDING_DECISIONS.md` 文件:行引用系统性错位、`:112-113` 的 RC-1 字节行行号错误。
⇒ 硬事实 CONFIRMED，结论层起点 PARTIAL。

---

## 1 · 点名检查 1：回件是否真含自算 SHA256 头部（两个哈希都要）

**结论：真含，两个哈希都是自算的，且我独立复算一致。**

`Q5_ROUTES.md:1-5` 原文：

```
被核对象 = gamemd.exe + EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360
EXCEPT 件 SHA256 = 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251，字节数 = 26405
Engine 自证 = COVERAGE 99.998375677293% / IMAGEBASE 0x400000
回件时刻 = 2026-11-06 02:57:32
```

五个字段齐全，符合 `TASK.md:77-83` 模板（§3「每份回件强制头部，缺则整份作废」）。
**「自算」可追**：`_w9_q5.py:34-42` 的 `[A]` 段用
`hashlib.sha256(Path(EXE).read_bytes())` / `hashlib.sha256(Path(EXCEPT).read_bytes())`
自己读盘算，`_w9_q5.py:44-51` 真实例化 `Engine()` 并打印 `e.sha == 自算 exe sha`；
没有抄 `TASK.md:19` 的期望值。（`ra2tool.py:29,55` 的 `EXPECT_SHA` 是 `Engine()` 构造内
assert，不是 Q5 头部来源。）

**本次实跑 C-R1**（Git-Bash 原生 `sha256sum` + `wc -c`，两条哈希都算）：

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

**本次实跑 C-R2**（自写 clean-room 探针，不导入 `_w9_q5.py`）：
`python -I -X utf8 W9/reviews/_Q5_review_probe.py` → `EXIT=0`；
`reviews/_Q5_review_probe_out.txt:1-7` 用 `hashlib` 独立读盘得同值同字节数，
并多算 RC-1 AV 件 = `b42c7014c96…5870` / `26830` B。

**本次实跑 C-R3**（原探针逐字重跑，唯一差异 = OUT 路径）：
把 `_w9_q5.py` 复制为 `reviews/_Q5_exact_rerun.py`，语义差异仅 1 行
（`L24 OUT` 改指 `reviews/_Q5_exact_rerun_out.txt`）；`diff <(grep -n '^OUT' …)` 只显示这一行。
`python -I -X utf8 reviews/_Q5_exact_rerun.py` → `EXIT=0`；
`diff <(grep -v '回件时刻' _w9_q5_out.txt) <(grep -v '回件时刻' reviews/_Q5_exact_rerun_out.txt)`
→ **空**（除探针自报时刻外 41 行逐行全等）。⇒ 头部不是手抄，是探针真跑生成的。

> 轻微 objection（不降判定）：`Q5_ROUTES.md:5` 写「回件时刻 = 02:57:32」，
> `_w9_q5_out.txt:6` 探针自报 `02:47:12`，`Q5_ROUTES.md` 文件 mtime = `03:05:03`。
> 三个时刻口径未在正文说明（与 `reviews/Q4_review.md:83-86`、`Q2_review.md:60` 同类问题）。
> 不影响哈希绑定。

---

## 2 · 点名检查 2：结论是否有「反汇编地址 + 原始字节」支撑，还是只给了地址

**结论：有，且我独立重跑了反汇编与字节读，逐项一致。不是只给地址。但 `:112-113` 有一处行号/证据归属错误。**

### 2.1 Q5 给出的字节与反汇编

`Q5_ROUTES.md:27-31`（§0）与 `:225`（§5 [A]）给出：
两个自算 SHA、`Engine()` 真跑 `COVERAGE 99.998375677293% / 1394120 insns / 66 resync-fails` /
IMAGEBASE `0x400000`；`e.rd(0x7CFC9F,32)` 32/32 与 EXCEPT L17 一致；
`0x7CFC9F in e.by()=True`（`8b0a size=2 mov ecx,[edx]`）；`e.disasm(VA,0x30)` 18 条、
前 8 条逐条列助记符；`e.func_rets(0x7CFB13,0x7CFE1C)` ret 数=1 @`0x7CFE1B`；
函数长 `0x309/0x308` B；前序 `0x7CFC9B 8b54f904` 末址=`0x7CFC9F`。
`_w9_q5_out.txt:2-38` 是对应探针输出。

### 2.2 本次独立重跑（clean-room，不经 Q5 探针）

`python -I -X utf8 W9/reviews/_Q5_review_probe.py` → `EXIT=0`，
`reviews/_Q5_review_probe_out.txt:8-39`：

```
[2] e.sha == self-computed exe sha : True
    IB = 0x400000
    COVERAGE = 99.998375677293% / 1394120 insns / 66 resync-fails
    fo(VA)=0x3CFC9F ; VA-IB=0x3CFC9F
    e.rd(VA,32) = 8B 0A 2B 4D F0 8B F1 89 4D F8 C1 FE 04 4E 83 FE 3F 7E 03 6A 3F 5E 3B F7 0F 84 0D 01 00 00 8B 4A
    EXCEPT L17 = 8B 0A … 8B 4A
    rd==L17 : True ; diff idx=[]
[3] VA in e.by() = True ; by()[VA] bytes=8b0a size=2 mov ecx, dword ptr [edx]
    disasm(VA,0x30) count = 18
      #1 0x7CFC9F 8b0a       mov ecx, dword ptr [edx]
      … #8 0x7CFCB0 7e03     jle 0x7cfcb5
    0x7CFC98 8b4df4 / 0x7CFC9B 8b54f904 mov edx, dword ptr [ecx + edi*8 + 4]
    0x7CFC9F 8b0a
[4] e.rd(0x7CFB13,5)=558bec83ec ; e.rd(0x7CFB12,1)=c3
    func_rets count=1 addrs=['0x7CFE1B'] ; e.rd(0x7CFE1B,1)=c3
    length incl ret = 0x309 / excl = 0x308
```

我也独立读了证据件原文（`sed -n '1,4p;11,17p' <EXCEPT>`）：L1 `EXCEPTION_SINGLE_STEP`、
L3 `Exception occurred at 007CFC9F`、L11-14 寄存器、L17 `Bytes at CS:EIP (007CFC9F) : 8B 0A … 8B 4A`。
与探针的 L17 解析一致。

**Q5 的「文件:行」支撑我也逐项核过（本次亲读）**：
- `qc151_trip.py:228-230` = `EXCEPT_MASTER = BENCH / "except.txt"` /
  `ca175a71c8a25228685d28bf5b3a9d883665aec429dc03c46478cf486672f39d` / `26515`；
- `:672-708` `except_set_diff` = `collections.Counter` 多重集差、`new_exception_count` = 新增含
  `Exception occurred at` 的行数（`:679, :689, :699`）——与 `Q5_ROUTES.md:39` 一致；
- `:4561-4599` `copy_post_except_evidence`（`:4574-4582`：`src = carrier_dir/"except.txt"`、
  `:4575-4578 if not src.exists(): return None`、`blob = src.read_bytes()`、
  `dst = out_dir/f"except_post_{datetime.now()…}.txt"`、`dst.write_bytes(blob)`）——与 `:36-37` 一致；
  **注意**：`:4575` 有 `src.exists()` 守卫，严格说是「载体存在时无条件、不以本趟是否异常为条件」，
  Q5 的「无条件复制」措辞与 `Q4_review.md:355-358` 同类不精确；
- `:6042-6052` `run_guarded_steps([...])` 第 1 项 `("except_evidence_copy_and_verify", _except_evidence_copy)`；
  `:7117` `FINALIZE_CODE[0] = finalize_trip(...)` 位于 `main()` 的 `finally` 区（`:7112-7114` 有
  `script:main:finally`）——与 `:38` 一致；
- `RC_SPEC_V4.md:16`（「具体写点 VA 未指认」）、`:18,:20`（PW-1 6B 窗）、`:51`（E1-1 现场
  `b42c7014…` / 26,830 B / mtime 2026-09-29 22:38:24）、`:57-62`（压缩重排版现场块）、
  `:74`（`identical=True`）、`:85`（`FE00FFFF` imm32 零命中）、`:95,99-101`（`0x7CFC9B`/`0x7CFC9F`/
  `0x7CFD30`/`0x7CFD39`）——我 `sed -n '1,120p'` 亲读，行号与内容一致；
- `GOAL_THREE_TARGETS_20261018.md:5570`（诚实账第 3 条「『游戏崩溃 0 趟』这条结论我未独立验证」）、
  `:8541`（「不能由此推出『游戏不会崩』」）、`Q3_MECHANISM.md:243-247,388-390,426-435`、
  `Q4_RELATION.md:243,246` —— 我逐段 `sed` 亲读，行号与内容一致。

⇒ **检查 2 主体通过**：字节 + 反汇编 + 函数边界 + 文件行都齐，不是只给地址。

### 2.3 objection：`:112-113` 的 RC-1 字节行行号与证据归属错误

`Q5_ROUTES.md:111-113` 原文：

```
1. 用 `Engine` 复核 RC-1 现场字节与磁盘一致（`RC_SPEC_V4.md:74` 记 `identical=True`，
   本次 W9 各探针已自证 `e.rd(0x7CFC9F,32)` 32/32；RC-1 件的 L17 同样是这 32 字节——
   我本次亲读 `except.txt.final_isolated` 头部，:62 与 EXCEPT 件 :17 字节串相同）。
```

**本次实跑反证**（AV = `out/re_work/zcode_live/zc11/evidence/closeout/except.txt.final_isolated`）：

```
$ sed -n '1,4p;11,18p' "$AV" | nl -ba          # 摘要
1  Error code: EXCEPTION_ACCESS_VIOLATION
3  Access address:FE00FFFF was read from.
4  Exception occurred at 007CFC9F
14 Edx:FE00FFFF  Esi:7FFFFFFF  Edi:00000004
15 EFlags:00010286
17 (空行)
18 Bytes at CS:EIP (007CFC9F)  : 8B 0A … 8B 4A

$ sed -n '17p' "$AV" | cat -A     →  $           （L17 是空行，不是字节行）
$ sed -n '18p' "$AV" | cat -A     →  Bytes at CS:EIP … 8B 4A $
$ grep -n 'Bytes at CS:EIP' "$AV" →  18:…
$ sed -n '62p' "$AV"             →  00F9D1EC: 00000000 DATA_PTR   （栈 dump，不是字节行）
$ grep -c 'Bytes at CS:EIP' "$AV" →  1
```

Q5 说的 `:62` 实际是 **`RC_SPEC_V4.md:62`**（其 §1.1 E1-1 的「来源压缩重排版」代码块里的
`Bytes at CS:EIP` 行，`RC_SPEC_V4.md:53` 自陈该块是压缩重排、非逐字原文），
**不是 AV 文件的第 62 行**。
Python `splitlines()` 因 L1 含 `\r\r` 双回车多算一行得 L19（`reviews/_Q5_review_probe_out.txt:42`），
无论哪种口径都**不是 L17**。

**字节串本身确实相同**（我 `reviews/_Q5_review_probe_out.txt:43-44` 实跑
`AV L18/L19 bytes == EXCEPT L17 bytes : True`），所以结论方向对；
但「亲读 `except.txt.final_isolated` 头部，:62」把 `RC_SPEC_V4.md` 的行号混入
AV 文件行号，且 `:112` 的「RC-1 件的 L17」是错的。
`Q5_ROUTES.md:231` 自述 [G] 只跑了 `head -17`（覆盖不到 L18 的字节行），
**却声称亲读到了该字节行**——这属证据归属不精确，不能写成「Q5 已亲读 AV 文件字节行」。
（我不推断 Q5 是否真的打开过该文件，只报告盘面行号与引用不符。）

---

## 3 · 点名检查 3：Q4 的哈希比对该不该全量 + 默认找反例

### 3.1 该全量，且 Q5 做了、我全量重做结果一致（CONFIRMED）

`TASK.md:64-67` 把 Q4 判据写成「自己算它的 SHA256，并与 `except_post_*.txt` 的哈希比对
（`find` + `sha256sum` 或 python）」，且称「本节最关键的一问」；按 `TASK.md:66`，
同哈希 ⇒「该证据不是任何一趟的崩溃，整个『主崩溃』叙事要重新定位」。
单一哈希/前缀比对只给必要条件；「113 份彼此同哈希」与「这件 EXCEPT 是其中之一」
是方向不同的两个命题，必须逐份算完整 64 位哈希（或逐字节比）才能排除
「113 份是另一份仅前缀相同的文件」。⇒ **该全量，抽样或借用 §555 记的 `6694b75e…` 前缀都不够。**
这一判断与 `reviews/Q4_review.md:153-160`（§3.1）一致。

Q5 在其 §0 自称「本次会话独立复核」重跑了 Q4 这块（`Q5_ROUTES.md:32-35`、§5 [B]/[C] `:226-227`）：
`find … -name 'except_post_*.txt' -print0 | xargs -0 sha256sum | awk '{print $1}' | sort | uniq -c`
→ `113 6694b75e…a8c251`；`wc -l` → `113`。

**本次独立全量实跑 C-R4**（GNU find，与 Q5 实现不同）：

```
cd "D:/Project/ra2-campaign-forge"
/usr/bin/find . -path ./.git -prune -o -type f -name 'except_post_*.txt' -print0 | sort -z | xargs -0 sha256sum > /tmp/rev_q5_posts.txt
wc -l < /tmp/rev_q5_posts.txt                       → 113
cut -d' ' -f1 /tmp/rev_q5_posts.txt | sort | uniq -c → 113 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251
grep -vc '^6694b75e…aac251' /tmp/rev_q5_posts.txt   → 0
```

**本次独立全文逐字节比 C-R5**（不依赖哈希）：

```
EX="out/.../EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt"
n=0; same=0; while IFS= read -r -d '' f; do n=$((n+1)); cmp -s "$EX" "$f" && same=$((same+1)); \
  done < <(/usr/bin/find . -path ./.git -prune -o -type f -name 'except_post_*.txt' -print0)
echo "posts=$n byte-identical=$same"                 → posts=113 byte-identical=113
```

更宽口径：`-name` = `113`、`-iname` = `113`、`-iname '*except_post*'` = `114`
（多出的 1 份是 `_except_post.py`，非 .txt，不算反例）、`-type l` = `0`。
⇒ **该全量、Q5 做了、我做的结果一样（113/113 同哈希 + 113/113 逐字节全等 + 反例 0）。这一问 CONFIRMED。**

Q5 其余数字我也独立复现：
- mtime：`stat -c '%y %s %n'` EXCEPT → `2026-10-19 13:54:38.293170200 +0800 | 26405`；
  `find … -printf '%TY-%Tm-%TdT%TH:%TM:%TS %p\n' | sort | sed -n '1p;$p'` →
  最早 `2026-10-17T08:14:58.8125028000 ./…/archive_T5/except_post_20261017T081458810997.txt`、
  最晚 `2026-11-04T18:26:58.6949750000 ./…/l3_1101v4h/except_post_20261104T182658693950.txt`
  ——与 `Q5_ROUTES.md:34-35, :228` 一致；
- `except_set_diff.json`：`find … -name 'except_set_diff.json'` → `68`；
  `xargs grep -h '"new_exception_count"' | sort | uniq -c` → `68  "new_exception_count": 0,`
  ——与 `:81, :230` 一致；Q5 自己声明「这只是必要条件的一个面，不等于逐趟 console 已核」（`:81-82`），诚实；
- [H] glob：`find . … \( -name 'except*.txt' -o -name '*.final_isolated' \) -print0 | xargs -0 sha256sum`
  → `230` 文件 / `20` distinct 哈希 / `206 6694b75e…` + `3 e369a911…` + `3 584069ad…` +
  `2 ca1acc37…` + 16×1；`b42c7014…` 在该 glob 内 **1** 份——与 `:44-46, :232` 全一致；
- [I] 两份同哈希件：`sha256sum except.txt.final_isolated` 与
  `except.txt.ra2bench.zc11_window` 均 `b42c7014…5870 / 26830 B`（`:233` 一致）；
- [J] 两套母本：`ra2bench/except.txt` = `ca175a71…f39d / 26515 / AV@006F9DB6`、
  `out/.../qc161_u0400_trip/_src_L3_sf10c_20261021/except.txt` = `6694b75e… / 26405`；
- [K] `lead/goal2_sbh_guard_20261020/` 4 件（`RECEIPT.md` / `assembly_report.json` /
  `sbh_guard.diff` / `sbh_guard_snippet.txt`）；
- [I] 的诚实反例：`except_crash_r1off_nr.txt` = `e5ed1a45… / 26650`、
  `ra2youli/except.txt` = `584069ad… / 27631`、`final_isolated` = `b42c7014… / 26830`
  ——三件互不同哈希，`Q5_ROUTES.md:233` 自承「`RC_SPEC_V4.md:41` 的『与上同 sha256』按当前盘面
  字节未复现…记未验」。**这是 Q5 自己找的反例，加分**，我复现一致。

> 一次**未跑**的检查（如实登记）：我试图跑
> `find . -type f -print0 | xargs -0 sha256sum | grep '^b42c7014…'`（全仓全扩展名绝对计数），
> 300 s 超时后被我 `TaskStop` 终止，输出未产生 ⇒ **全仓全扩展名绝对计数：本次未跑**。
> Q5 自己也在 `:52-53, :200` 明写「非全仓全扩展名绝对计数」，未冒充已跑，两者一致。
> 我用定向 `find … \( -name 'except.txt.ra2bench.zc11_window' -o -name 'except.txt.final_isolated' \)`
> 只确认了这 2 个具名同哈希件，这是**更窄的口径**，不冒充全仓计数。

### 3.2 反例 A（最实质）：Q5 的路线起点「Q4 全局断言」被仓内既有书面记录反证

Q5 把 Q4 的 REFUTED 当作**全部路线的起点**，并原样继承了 Q4 被其独立复核驳回的全局断言：

| Q5 位置 | 原文 |
|---|---|
| `Q5_ROUTES.md:23`（§0 收敛表） | 「**目标② 目前没有一件「把某次异常归因到某趟游戏运行」的证据**。第一要务…**重定位观测/证据**」 |
| `Q5_ROUTES.md:192`（§4 排序理由） | 「Q4 已废掉**唯一**『有异常上下文』的锚点…⇒ 先修观测（A）是所有后续路线的公共前置」 |
| `Q5_ROUTES.md:252`（§6） | 「按 Q1–Q4 的收敛，**Q4 的 REFUTED 是本节全部路线的起点**」 |
| `Q5_ROUTES.md:76`（路线 A 第 2 步） | 把 `6694b75e…` 直接归类为「(i) `6694b75e…` **残件类**」 |
| `Q5_ROUTES.md:148,155`（路线 C） | 「唯一能补 Q3/Q4 缺口的数据是运行期证据」「这能补 **Q4 的归因缺口**」 |

**本次静态实读（零真机）反证链**，全部是 2026-10-16/17 的既有件，mtime 均**早于 Q5（03:05）**：

1. `out/.../qc124_observe_chain/QC124_VERDICT.json`（mtime `2026-10-16 19:22:21`）：
   - `:8` `answer_detail`：「挂 RC1 后命中 ⇒ 进程在挂点后 0.63 s 终止，载体 `except.txt` 记为
     `EXCEPTION_SINGLE_STEP @ 007CFC9F`（**= 我设的 DR0**）。这是断点异常无人处理的必然后果，
     **不是游戏本身的崩溃**。」
   - `:36` `"single_bp": {"name": "RC1", "va": "0x007CFC9F", "dr": "DR0"}`、`:37` `n_armed 31/31`；
   - `:47` `except_setdiff_new_lines: ["007CFC9F"]`、`:48` `except_file_rewritten: true`、
     `:50` `except_post_sha256: "6694b75e…aac251"`、`:51` `error_code: EXCEPTION_SINGLE_STEP`、
     `:53` `eip: 007CFC9F`、`:54` `eip_equals_set_dr0: true`、`:55` `bytes_at_cs_eip` 与静态 32 B 全等；
   - 对照组 `:23-25`：`except_setdiff_new_lines: []` / `except_file_rewritten: false` /
     `except_post_sha256: e369a911…`（**0 断点组文件未被重写**）。
   ⇒ **这是一件把某次异常归因到某趟游戏运行（QC124 group2）的书面证据**，
   直接反证 `Q5_ROUTES.md:23` 的「没有一件」。
2. `out/.../qc164_a4_prep_20261017/raw/except.drift.6694B75E.26405B.bin`
   （mtime `2026-10-16 19:21:11`）：本次实算
   `sha256sum` = `6694b75e…a8c251`、`wc -c` = `26405` —— 该字节实体仍在盘。
3. `out/.../qc161_audit_T11/VERDICT_T11.md`（mtime `2026-10-17 15:51:35`）与
   `out/.../qc164_a4_prep_20261017/ERRATA_EXCEPT_RESTORE.md`（mtime `2026-10-17 22:43:34`）
   亦把它登记为「qc124 观测趟运行期写出」。`reviews/Q4_review.md:235-309`（§3.3）已完整引用这条链。
4. **Q5 之后落盘的两件独立订正**（我实读，用于交叉验证方向，不作为「Q5 当时应引用」的依据）：
   - `GOAL_THREE_TARGETS_20261018.md:9229-9290` §599（mtime `2026-11-06 04:23:28`）：
     `:9279-9287` 明写「`6694b75e…` 这份 26,405 B 是 2026-10-16 QC124 实验里人为设 DR0 断点、
     命中后游戏自己写出的 `except.txt` 原件」「我原先的表述…后半错」「目标② 目前一件真实崩溃
     证据都没有 → **过强**」；`:9289` 给正确表述。
   - `lead/PENDING_DECISIONS.md:144` D-22（mtime `2026-11-06 04:23:40`）：
     「**它既不是『历史基线残件』，也不是『游戏自身崩溃的证据』，而是一次人为断点造成的真实异常记录**。
     目标② 准确状态：**有一件人为注入断点造成的异常记录，无任何『游戏自身崩溃』证据**」。

**Q5 全文零提及**：`grep -c` 实测 `QC124=0`、`§599=0`、`D-22=0`、`断点=0`、`人为=0`、
`运行期写出=0`、`except_file_rewritten=0`、`不是任何一趟=0`（`DR0` 仅 4 次，
全部是 `Q3_MECHANISM.md` 的寄存器候选用语，见 `:22,155,158,212`）。

**公平性边界（不苛求不可得之事）**：`reviews/Q4_review.md`（mtime 04:20:06）、
§599（04:23:28）、`PENDING_DECISIONS.md:144`（04:23:40）都**晚于** Q5（03:05:03），
Q5 写作时不可能引用它们；且 `TASK.md:70` 只要求「基于 Q1–Q4 的结论」，
Q5 在 §4 第 7 条（`:216-217`）也明写「Q1–Q4 四份回件本身…不复核、不反驳其定谳」。
**但**：`QC124_VERDICT.json` / drift bin / VERDICT_T11 / ERRATA 都是 2026-10-16/17 的既有件，
Q5 §0 自称「本次会话独立复核（不采信前置回件文字）」（`:25`）并做了全仓 `except*.txt`
哈希普查（[H] 230 件/20 哈希），**却未读这些本来静态可读的 provenance 书面件**，
反而照抄 Q4 的全局断言，并把该哈希在路线 A 里直接定性为「残件类」。
`Q5_ROUTES.md:210-211`（§4 未验第 4 条）还把「两套基线各自的来源与写入时序」列为
「本次只确认两者哈希/首行/字节数不同，来源未验」——**而 `QC124_VERDICT.json:48` 的
`except_file_rewritten: true` / `ERRATA` 的「运行期写出」已给出书面答案**（属旧趟真机记录，
本任务零真机不能重演，但静态可读）。⇒ 与 `Q4_review.md:401-405` 指出的同型自相矛盾：
一边列「来源未验」，一边断言「没有一件归因证据」。

**对路线的实际损害**：
- 路线 A 第 2 步（`:74-77`）的 provenance 分档把 `6694b75e…` 预设为「残件类」，
  分档前提错；正确分档应含「QC124 人为 DR0 断点产物」这一类。
- 路线 C1（`:150-156`）说「补 Q4 的归因缺口」——缺口方向写错：QC124 已有归因
  （人为断点），真正缺的是「**游戏自身崩溃**」的可归因证据；§599 / D-22 已给出该精确表述。
- 排序理由（`:191-195`）「Q4 已废掉唯一有异常上下文的锚点」不成立；
  A 仍是合理首选（D-22 = A 也这么裁），但**理由须改写**，不能建立在被反证的全局断言上。

> 边界说明：上述 QC124/§599/D-22 是**仓内既有书面记录**，我本次只读文件、算了 drift bin 的
> SHA256 与 mtime，**没有启动任何进程、没有重新复现那次运行**。故表述是
> 「Q5 的起点断言被仓内既有记录反证」，不是「我独立验证了 QC124 那趟真机事件」。

### 3.3 反例 B：`PENDING_DECISIONS.md` 文件:行引用系统性错位（当前盘面全对不上）

Q5 在「是否受 D-13 限制」字段里密集引用 `PENDING_DECISIONS.md`。本次逐条 `sed -n` 亲读
**当前工作树版本**（mtime `2026-11-06 04:23:40`，比 Q5 晚 1h18）：

| Q5 位置 | 引用 | 当前盘面实际内容 | 判定 |
|---|---|---|---|
| `:89` | `PD:67` 明写「本条纯静态、不需真机、不受 D-13 限制」 | `:67` = 「- **原 A**：采用其**数据分层**与**追加勘误路径**…」 | **对不上** |
| `:172` | `PD:72`「申请真机趟专抓崩溃…需用户明示授权」 | `:72` = 「`33 = 22 + 11`、`38 = 33 + 5`；**主指标 `fps_avg`**」 | **对不上** |
| `:90,:132,:160` | `PD:301-302` = D-13 禁令（E3/MiniDump/…/真机发射） | `:301-302` = 「**D-04 已裁决**（2026-10-23）…全屏 125 s 矩形空等」「**执行**：条目已删除」 | **对不上**；D-13 禁令实际在 `:78-80`、`:248-249`、`:206` |
| `:176` | `PD:171`「**(暂停)** E3 暂不执行」 | `:171` = 「**执行顺序由 gpt-6.1-sol 裁决**（本轮同时立 D-20）」；「(暂停) E3 暂不执行」在 **`:114`** | **对不上** |
| `:178` | `PD:176`「`E3_FOR_GOAL1_CARD_20261103.md` 等原文零改动」 | `:176` = D-19 裁决要点第 1 条；该证据句在 **`:119-120`** | **对不上** |
| `:179` | `PD:77`「不因本条放宽 D-13」 | `:77` = 「`C15:458` 的拟追加标题『§545』已被 `L:4489` 占用…」；「不因本裁决放宽」在 `:80`/`:249` | **对不上** |
| `:182` | `PD:169-172`「可能自造死锁」 | `:169-172` = D-17 授权面/E3 重裁/执行顺序；「可能自造死锁」在 **`:113`** | **对不上** |
| `:97,:183` | `PD:73-74`「harness 未修新证据仍被污染」 | `:73-74` = 「11 个低 avg 停摆窗的观测不删除…」「`21/32` 只保留…」 | **对不上** |

**短语出处实查**（本次 `grep -n` 全文件）：
「本条纯静态」「不需真机」「不受 D-13 限制」「申请真机趟专抓」「不因为本条而放宽」
「harness 写入逻辑」「仍会被」「分别授权」「纯静态」——**在 `PENDING_DECISIONS.md` 中全部 0 命中**。
它们实际出自 `lead/re_line_20261105/D22_RULING/TASK.md:29`（「**纯静态、不需真机、不受 D-13 限制**」）、
`:31`（「**申请真机趟专抓崩溃**。**需用户明示授权，受 D-13 约束**」）、`:38`（「不得放宽 D-13」）、
`:54`（「E3 维持暂停（D-13）」）。`RULING_D22.md:17`（02:31:57，**早于 Q5**）引的是
`PENDING_DECISIONS.md:52-54`（纯静态）、`:24`、`:48`、`:122-124`（D-13 维持暂停）——
说明 Q5 写作时 PD 的行号布局与当前不同。

**版本漂移已核**：`git diff --stat -- lead/PENDING_DECISIONS.md` →
`258 insertions(+), 24 deletions(-)`；`git show HEAD:lead/PENDING_DECISIONS.md` = 59 行、
`git show :lead/PENDING_DECISIONS.md`（index）= 86 行，**两者也都无上述短语**；
当前工作树 = 300+ 行。`Q5_ROUTES.md` 未注明引用的是哪个时点版本。
⇒ 我**不能**断言 Q5 写作时全部引用皆错（那时布局不同，`RULING_D22.md:17` 用的
`:52-54` 佐证当时确有纯静态段），但可以确证：
(a) 当前盘面这些行号**全部失效**；(b) 至少「本条纯静态」「申请真机趟专抓崩溃」
两个短语的**出处归属错误**（应为 `D22_RULING/TASK.md:29,31`，不是 PD）；
(c) Q5 未标注版本/时刻，使「文件:行」不可复核。
按 `TASK.md:108`「每个数字追到实跑命令+输出或文件:行」，这是可核缺陷。

**另有一处内容级反例**：`PENDING_DECISIONS.md:155-171`（当前盘面）记
「**【用户授权 · 2026-11-05 · 全开】**…第二项真机活进行采集也授权，所有的行动都授权」
（`:155-160`），`:168-169` 明写「D-13（E3 栈采样）的「暂停」由本授权**解除其授权面**」。
Q5 `:176` 断言「C2：完全受 D-13 且**当前被禁**」、`:160-162` 把
`E3 / MiniDump / SuspendThread / StackWalk` 一律列为「暂停」——与 `:155-171` 的
「全开」授权面存在张力。但同一文件 `:78-80, :248-249, :206` 又反复写「D-13 维持暂停」、
`:194-195`「D-13/D-16 暂停…继续有效」、`:146`「D-13 继续暂停」，
文件内部口径本身不一致；且 `D22_RULING/TASK.md:38`（Q5 时代）确实写「不得放宽 D-13」。
⇒ **我不把这一条判为 Q5 定论错误**，只登记为「授权面口径冲突，Q5 未核 `PD:155-171`，
C2 状态须按最新裁决另定，不能只写『当前被禁』」。

### 3.4 反例 C：Q5 未引用早于它落盘的 D-22 = A 裁决与 W11 既有工作

`lead/re_line_20261105/D22_RULING/RULING_D22.md`（mtime **02:31:57，早于 Q5 03:05**）：
`:3` 「★ 定谳：**D-22 = A**」、`:4`「目标② 转向『先修观测』」、`:30-35` 给出 5 步 `nextSteps`
（第 1 步逐段列 `qc151_trip.py` 文件处理函数、第 2 步区分设计/缺陷/无法区分、
第 3 步写离线候选 + 合成文件 4 分支、第 5 步需授权才能应用到正式 harness）。
`Q5_ROUTES.md` 全文 `grep -c 'D-22\|D22\|W11'` = **0**。
`PENDING_DECISIONS.md:144`（当前）另记「W11 `dwfrun-7d468cc0` 离线候选 **14/14 测试全绿**、
`qc151_trip.py` 未被改动」（W11 件 mtime 03:08–03:59，部分晚于 Q5）。
⇒ Q5 路线 A 把「读 harness 源码、坐实复制链」当作「**立即可做** / 代价最低」的推荐
（`:63, :94`），却未扣除**同一会话 02:31 已裁决、部分已执行**的 A 路线前置工作，
也未提「把候选应用到正式 harness 仍需用户授权」（`RULING_D22.md:34` / `PD:144` 末句）。
这不改变 A 的方向（与 D-22 一致），但使「代价 / 需要什么数据」字段不完整。

### 3.5 其它小 objection（不降判定）

- **判定档自相矛盾**：被核者自述 `partVerdict: "CONFIRMED"`，而 `Q5_ROUTES.md:249-251`
  §6 明写「Q5 是『只给路线、不执行』的规划题…故**不套** §4 的 CONFIRMED/PARTIAL/REFUTED
  三分档」。自述与正文冲突；`TASK.md:85-89` 的三分档确为字节级事实题设，Q5 是规划题，
  正文的说法更站得住。不影响本次复核按自身标准给 verdict。
- **「无条件复制」不精确**：`qc151_trip.py:4575-4578` 有 `if not src.exists(): return None`
  守卫（同 `Q4_review.md:355-358`）。Q5 `:37, :40, :23` 的「无条件复制」应为
  「载体存在时无条件、不以本趟是否发生异常为条件」。
- **回件时刻三口径**：见 §1 末。
- **`_w9_q5_out.txt:6` 时刻 02:47:12 vs 文件 mtime 02:48:00**：探针自报与落盘差 48 s，
  属正常写盘延迟，不构成反例。
- **e.disasm 条数 18 vs Q4 报 12**：Q5 `:30, :225` 报 `disasm(VA,0x30)` = **18 条**，
  `Q4_RELATION.md:147` 报 `disasm(VA,32)` = **12 条**。参数不同（`0x30`=48 B vs 32 B），
  我的 clean-room 探针 `disasm(VA,0x30)` = 18 条（`_Q5_review_probe_out.txt:19`）。**不矛盾**，
  不列反例。
- **写域自述**：`Q5_ROUTES.md:241` 称本次仅新增 3 件、唯一写域 `W9_SINGLESTEP_7CFC9F/`；
  本次实跑 `find W9 -maxdepth 1 -type f -newermt '2026-11-06 02:45:00'` 恰得
  `_w9_q5.py` / `_w9_q5_out.txt` / `Q5_ROUTES.md` 三件，一致；
  `git status --porcelain -- W9/` → `?? lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/`（整树未跟踪）。
  本次复核新建件全部落在 `W9/reviews/`（本 ask 指定的唯一写域），未改任何既有件。

---

## 4 · 对 Q5 三条路线与判定档的复核结论

| Q5 的结论 / 字段 | 本次裁定 | 依据 |
|---|---|---|
| 强制头部两个自算 SHA256 + 字节数 + Engine 自证 | **CONFIRMED** | §1，C-R1/C-R2/C-R3 四路 |
| `e.rd(VA,32)` 32/32、`8b0a size=2`、`disasm(VA,0x30)` 18 条、唯一 ret @`0x7CFE1B`、`0x309/0x308`、前序 `0x7CFC9B` | **CONFIRMED** | §2.2 clean-room 探针逐项一致 |
| Q4 的 113 份 `except_post_*.txt` 全量哈希 = 113/113 同哈希（该全量、已做） | **CONFIRMED** | §3.1，C-R4/C-R5 全量 + 全文 `cmp` |
| 20 distinct / 206 / `b42c7014` 在该 glob 1 份 + 具名同哈希件共 2 份 | **CONFIRMED（按 Q5 自述口径）** | §3.1 [H]/[I]；全仓全扩展名绝对计数**本次未跑**（Q5 亦未跑） |
| 68 份 `except_set_diff.json` 全为 0（≠37 archive 逐趟已核） | **CONFIRMED** | §3.1；Q5 自设边界诚实 |
| 两套母本 / mtime / harness 5 处源码行 / RC_SPEC_V4 行号 / Q3/Q4/台账行号 | **CONFIRMED** | §2.2 逐段亲读 |
| 三条路线齐备「数据 / D-13 / 代价」、零采样代码、零真机 | **CONFIRMED（形式上）** | `Q5_ROUTES.md:84,89,94 / 125,131,136 / 164,171,181 / 237-243`；`TASK.md:70-73` |
| 「目标② 目前**没有一件**把某次异常归因到某趟游戏运行的证据」作为全路线起点 | **REFUTED（被仓内记录反证）** | §3.2：`QC124_VERDICT.json:8,36,47-55`、§599 `GOAL…:9279-9289`、`PD:144` |
| 路线 A 把 `6694b75e…` 分档为「残件类」 | **PARTIAL / 前提错** | §3.2；应含「QC124 人为 DR0 断点产物」类 |
| C1「补 Q4 的归因缺口」的缺口方向 | **须改写** | §3.2；缺的是「游戏自身崩溃」归因，非「任何异常」归因 |
| D-13「不受/受/完全受且当前被禁」三档的方向 | **方向大体成立，但引用的文件:行全部失效** | §3.3；`RULING_D22.md:17` 与 `D22_RULING/TASK.md:29,31,38,54` 才是当时出处 |
| `Q5_ROUTES.md:112-113`「RC-1 件 L17 = 这 32 字节 / 亲读…:62」 | **行号与证据归属错**（字节内容相同） | §2.3：AV 字节行在 L18（splitlines L19），L62 是栈 dump；`:62` 实为 `RC_SPEC_V4.md:62` |
| 「Q5 = CONFIRMED」（自述） vs §6「不套三分档」 | **自相矛盾** | §3.5；正文说法更站得住 |

⇒ **综合 verdict = PARTIAL**：全部可核硬事实（哈希绑定、字节、反汇编、全量比对、
文件行、计数）独立复现通过；但结论层的**路线起点**建立在被仓内既有记录反证的
Q4 全局断言上，且 `PENDING_DECISIONS.md` 引用不可复核、RC-1 字节行行号错、
未引用早于它落盘的 D-22=A 裁决。按 `TASK.md:108-110`（每个数字可追、
拿不到写未验、不把查不到当不存在），Q5 作为「只给路线」的规划题**可以交**，
但 §0 起点、路线 A 分档、C1 缺口表述、D-13 引用**必须改**。

---

## 5 · objections（逐条，均带本次读/跑的依据）

1. **【主要】路线起点照抄 Q4 被反证的全局断言。** `Q5_ROUTES.md:23,192,252` 的
   「没有一件把某次异常归因到某趟游戏运行的证据」「废掉唯一有异常上下文的锚点」
   被 `QC124_VERDICT.json:8,36,47-55`（mtime 2026-10-16 19:22，早于 Q5）、
   drift bin 实算 `6694b75e…/26405`、§599 `GOAL…:9279-9289`、`PD:144` 反证。
   依据 §3.2；Q5 全文对 QC124/断点/人为/运行期写出零命中。
2. **【主要】路线 A 的 provenance 分档前提错、C1 缺口方向错。** `:76` 把该哈希预设为
   「残件类」、`:155` 说「补 Q4 的归因缺口」；正确状态按 `PD:144` / §599 是
   「有一件人为注入断点造成的异常记录，无任何游戏自身崩溃证据」。依据 §3.2。
3. **【主要】`PENDING_DECISIONS.md` 文件:行引用系统性失效 + 短语出处归属错。**
   8 组行号在当前盘面全对不上（§3.3 表）；「本条纯静态」「申请真机趟专抓崩溃」
   在 PD 任何版本 0 命中，实际出自 `D22_RULING/TASK.md:29,31`；
   `git diff` 258+/24- 证明版本漂移，Q5 未标注版本。依据 §3.3。
4. **【中】`:112-113` 的 RC-1 字节行行号/证据归属错。** AV 文件 L17 是空行、
   字节行 L18（splitlines L19）、L62 是栈 dump；`:62` 实为 `RC_SPEC_V4.md:62` 的压缩块；
   Q5 [G] 自述只 `head -17` 却声称亲读到字节行。依据 §2.3 实跑。
5. **【中】未引用早于 Q5 落盘的 D-22=A 裁决（`RULING_D22.md:3,30-35`，02:31:57）**
   与 W11 既有工作，使路线 A 的「代价/需要什么数据」未扣除已做部分、
   未提「应用到正式 harness 仍需授权」。依据 §3.4。
6. **【中】「未验」清单与 §0 全局断言自相矛盾。** `:210-211` 自列「两套基线来源与
   写入时序…来源未验」，却在 `:23` 断言「没有一件归因证据」；
   `QC124_VERDICT.json:48 `except_file_rewritten: true` / ERRATA 已给书面答案。依据 §3.2。
7. **【轻微】判定档自述 CONFIRMED 与 §6「不套三分档」冲突；「无条件复制」不精确
   （`qc151_trip.py:4575` 有 `src.exists()` 守卫）；回件时刻 02:57:32 / 探针 02:47:12 /
   mtime 03:05:03 三口径未说明。** 依据 §3.5、§1。
8. **【轻微／授权面口径冲突，不定为 Q5 错】** `PD:155-171` 的「用户授权全开…解除 D-13 授权面」
   与同文件 `:78-80,146,194-195,206,248-249` 的「D-13 维持暂停」内部冲突；
   Q5 `:176`「C2 当前被禁」未核 `:155-171`。依据 §3.3 末。

---

## 6 · mustFix（给 Q5 / `W9_SINGLESTEP.md` 汇总件的具体改项）

1. **改写 §0 起点与 §4 排序理由。** 把 `Q5_ROUTES.md:23,192,252` 的
   「目标② 目前没有一件把某次异常归因到某趟游戏运行的证据」「废掉唯一锚点」
   「Q4 REFUTED 是全部路线的起点」改为按 `PD:144` / §599 的精确表述：
   「手上这件 EXCEPT 不是 2026-10-19 13:52 那趟的产物；仓内 `except_post` 语料
   对判定该趟崩溃无信息量；`6694b75e…` 的唯一一次真实产生是 QC124 group2
   人为 DR0 断点命中（**仓内书面记录，本次零真机未独立复现**）；目标② 准确状态 =
   有一件人为注入断点造成的异常记录，**无任何游戏自身崩溃证据**」。
   保留「先修观测」为首选（与 D-22=A 一致），但理由不得再依赖被反证的全局断言。
2. **修正路线 A 第 2 步的分档。** `:74-77` 的 (i) 类改称
   「QC124 人为断点产物 + 其 113/206 份复制件」，并把
   `QC124_VERDICT.json:8,36,47-55`、`VERDICT_T11.md:148`、`ERRATA_EXCEPT_RESTORE.md:12`、
   drift bin 的实算 SHA/字节数/mtime、§599 `GOAL…:9229-9290`、`PD:144`
   加入「需要什么数据」与证据索引；删去任何「历史基线残件 / 从来不是任何一趟产物」的等价表述。
3. **修正 C1 的缺口表述。** `:148,155` 把「补 Q4 的归因缺口」改为
   「补『游戏自身崩溃可归因证据』的缺口」；保留「C1 仍拿不到 DR6/DR0-3」（`:155-156` 正确）。
4. **全部 `PENDING_DECISIONS.md` 引用改为可复核形式。** 按 §3.3 表逐条改：
   纯静态/真机授权短语改引 `D22_RULING/TASK.md:29,31,38,54`；
   D-13 禁令改引 `PD:78-80`（或 `:248-249`、`:206`），E3 暂停改引 `PD:114`
   （并注明当前盘面行号 + 版本时刻，因该文件在 04:23 有 258+/24- 的改动）；
   `:301-302`/`:171`/`:176`/`:77`/`:169-172`/`:73-74` 全部撤换。
   **同时**核 `PD:155-171` 的「全开授权」与「维持暂停」冲突，C2 状态交由最新裁决定，
   不要只写「当前被禁」。
5. **修正 `:112-113` 的行号与证据归属。** 改为「`except.txt.final_isolated` 的
   `Bytes at CS:EIP` 在 **L18**（按 `splitlines()` 计 L19，因 L1 含双 CR），
   `RC_SPEC_V4.md:62` 是其压缩重排版块；本次实跑该行 32 字节 == EXCEPT 件 L17 32 字节」，
   并补上实跑命令与 `AV L17 = 空行 / L62 = 栈 dump` 的核对记录。
6. **补登记 D-22 / W11 既有工作。** 在路线 A 的「代价」与「需要什么数据」里注明
   `RULING_D22.md:3,30-35`（02:31 已裁 A、5 步 nextSteps）、`PD:144`（W11 离线候选
   14/14 全绿、正式 harness 未改、应用仍需授权），把「立即可做/代价最低」按已做部分重估。
7. **判定档统一。** 在 §6 或头部明确「Q5 为规划题，不套三分档」，
   与自述 `partVerdict` 对齐；「无条件复制」改为「载体存在时无条件、不以本趟是否异常为条件」；
   注明「回件时刻」是正文成稿时刻而非探针运行时刻（并解释 02:47:12 / 02:57:32 / 03:05:03 三口径）。
8. **汇总件 `W9_SINGLESTEP.md` 的「## 6 Q5 路线」「## 7 必须改项」「## 8 诚实账」**
   必须与 1–7 一致，并与 `reviews/Q4_review.md:423-455`（§6 mustFix）、
   `reviews/Q1_review.md`、`reviews/Q2_review.md` 已提出的 Q4 口径边界对齐；
   「## 1 SHA256 绑定」可照抄 Q5 头部（已复核为真）。

---

## 7 · 诚实账 / 未验（不把「查不到」当「不存在」）

- **本次亲验**：两个 SHA256 + 字节数（3 路：`sha256sum`/`wc -c`、自写 `hashlib` 探针、
  原探针逐字重跑）；`Engine()` 覆盖率 / IB / `fo` / `rd` / `by()` / `disasm` / `func_rets`
  （clean-room 2 路）；EXCEPT L1/L3/L11-14/L17 原文；AV 件 L1-18/L62 逐行 + 行尾字节分析；
  整仓 `except_post_*.txt` 全量 113 份逐份 SHA256 + 逐字节全文 `cmp`（含 4 种更宽口径）；
  `except*.txt`/`*.final_isolated` 230 件 / 20 distinct 分布全量；`b42c7014` 2 个具名同哈希件；
  RC-1/母本/guard/[I] 各哈希；68 份 `except_set_diff.json`；mtime 三件与最早/最晚快照；
  harness 5 处源码段；`RC_SPEC_V4.md:1-120`；`PENDING_DECISIONS.md` 当前版逐段 + `git diff` 版本漂移；
  `D22_RULING/TASK.md` 全文 + `RULING_D22.md:1-52` + `FACTCHECK.md:1-40`；
  `GOAL_THREE_TARGETS…:5564-5575, 8488-8496, 8535-8545, 9229-9290`；
  `QC124_VERDICT.json` 关键行 + drift bin 哈希/字节/mtime；
  `Q3_MECHANISM.md` / `Q4_RELATION.md` / `reviews/Q4_review.md` 所引行；写域 `git status`。
- **未验（不填猜）**：
  - **QC124 group2 那次运行期事件本身** —— 零真机，只读了仓内书面记录 + 算了 drift bin 哈希，
    **未重新复现**；其记录可靠性按 `Q4_review.md:470-472` 同规格记「未验」。
  - **全仓全扩展名下 `b42c7014…` 的绝对份数** —— `find . -type f -print0 | xargs -0 sha256sum`
    300 s 超时被我 `TaskStop` 终止，**本次未跑**；Q5 亦自述未跑，只报「该 glob 1 份 +
    具名直哈希命中 1 份 = 2 个」。我用定向文件名只确认这 2 件，属更窄口径。
  - **Q5 写作时刻（03:05）`PENDING_DECISIONS.md` 的确切行号布局** —— 当前版 04:23 有
    258+/24- 改动，HEAD 59 行 / index 86 行均无 Q5 所引短语，我**无法恢复**该时点全文，
    故 §3.3 只判「当前盘面全失效 + 短语出处归属错」，不判「Q5 当时全错」。
  - **37 个 archive 逐趟 console、WER `LiveKernelEvent 193/0x80e ×2`、「游戏是否会崩」、
    13:52 那趟是否另有未留存异常、RC-1 AV 件是否真机原生 / 是否被 harness 复制过** ——
    沿用 `Q5_ROUTES.md:199-215` 与 `Q4_review.md:473-476` 的未验清单，本次不触碰、不反驳。
  - **Q1/Q2/Q3/Q4 四份回件本身** —— 本复核只答本 ask 的 3 项点名检查 + 默认找反例，
    不重定谳前四问（同 `Q5_ROUTES.md:216-217` 的自设边界）。
  - **EFlags=0x286 位分解 / TF=0 机制 / PW-1 补丁正确性** —— 属 Q3/RC_SPEC 范围，本次未复核。
- **铁律核对**：本次新建件全部在 `W9/reviews/`；
  只读源 `ra2youli/gamemd.exe`、EXCEPT 件、AV 件、`qc151_trip.py`、`PENDING_DECISIONS.md`、
  `GOAL_THREE_TARGETS_20261018.md` 的 mtime 均为旧值（未改）；零真机、零采样、零活进程读取、
  未 commit、未 push；Python 全部 `python -I -X utf8` + 绝对路径。

---

## 8 · 实跑命令清单（每个数字可追）

| 编号 | 命令（均在 `D:/Project/ra2-campaign-forge`） | 关键输出 |
|---|---|---|
| C-R1 | `sha256sum ra2youli/gamemd.exe; wc -c …; sha256sum <EXCEPT>; wc -c <EXCEPT>` | `73201cc0…f67476 / 4825360`；`6694b75e…a8c251 / 26405` |
| C-R2 | `python -I -X utf8 W9/reviews/_Q5_review_probe.py`（自写，不导入 Q5 探针） | `EXIT=0`，`_Q5_review_probe_out.txt:1-48`：两 SHA + AV SHA、`Engine` 全量、字节/反汇编/函数边界、AV 字节行 L18/L19 与 EXCEPT L17 相等 |
| C-R3 | `python -I -X utf8 W9/reviews/_Q5_exact_rerun.py`（Q5 原探针仅改 OUT） | `EXIT=0`；`diff <(grep -v '回件时刻' …)` 空 |
| C-R4 | `find . -path ./.git -prune -o -type f -name 'except_post_*.txt' -print0 \| sort -z \| xargs -0 sha256sum > /tmp/rev_q5_posts.txt` + `wc -l` + `cut\|sort\|uniq -c` + `grep -vc` | `113` / `113 6694b75e…` / `0` |
| C-R5 | `while read -r -d '' f; do cmp -s "$EX" "$f"; done < <(find … -print0)` | `posts=113 byte-identical=113` |
| C-R5b | `-name` / `-iname` / `-iname '*except_post*'` / `-type l` 四种口径 `wc -l` | `113 / 113 / 114 / 0` |
| C-R6 | `stat -c '%y %s %n' <EXCEPT>`；`find … -printf '%TY…%TS %p\n' \| sort \| sed -n '1p;$p'` | `2026-10-19 13:54:38 \| 26405`；`2026-10-17T08:14:58 …081458810997.txt` / `2026-11-04T18:26:58 …182658693950.txt` |
| C-R7 | `find … -name 'except_set_diff.json' \| wc -l`；`xargs grep -h '"new_exception_count"' \| sort \| uniq -c` | `68`；`68  "new_exception_count": 0,` |
| C-R8 | `find . … \( -name 'except*.txt' -o -name '*.final_isolated' \) -print0 \| xargs -0 sha256sum > /tmp/rev_q5_exceptglob.txt` + `cut\|sort -u\|wc -l` + `uniq -c\|sort -rn` | `230` 文件 / `20` distinct / `206 6694b75e…` + `3 e369a911…` + `3 584069ad…` + `2 ca1acc37…` + 16×1；`b42c7014` 该 glob 内 `1` |
| C-R9 | `sha256sum except.txt.final_isolated` / `except.txt.ra2bench.zc11_window` / `ra2bench/except.txt` / `_src_L3_sf10c_20261021/except.txt` / `except_crash_r1off_nr.txt` / `ra2youli/except.txt` + `wc -c` | `b42c7014…/26830` ×2；`ca175a71…/26515`；`6694b75e…/26405`；`e5ed1a45…/26650`；`584069ad…/27631` |
| C-R10 | `sed -n '1,4p;11,18p;55,70p' <AV> \| nl -ba`；`sed -n '17p;18p;62p' <AV> \| cat -A`；`grep -n/-c 'Bytes at CS:EIP' <AV>`；`python -I -X utf8 -c` 按 `\n` 分行核 L1 `\r\r` | L17 空行、L18 字节行、L62 栈 dump、`grep -c`=1；`splitlines()` 计 L19 |
| C-R11 | `sed -n` 核 `qc151_trip.py:228-230, 616-666, 672-708, 4561-4599, 6040-6055, 7112-7122`；`RC_SPEC_V4.md:1-120` | 行号与内容一致；`:4575` 有 `src.exists()` 守卫 |
| C-R12 | `sed -n '60,90p;95,120p;140,150p;245,255p;298,310p' lead/PENDING_DECISIONS.md \| nl -ba` + `grep -n` 9 个 Q5 短语 + `git diff --stat` + `git show HEAD:/:lead/PENDING_DECISIONS.md` | 8 组行号全对不上；9 短语在 PD 0 命中；`258+/24-`；HEAD 59 行 / index 86 行亦无短语 |
| C-R13 | `sed -n '1,61p' D22_RULING/TASK.md`；`sed -n '1,52p' D22_RULING/RULING_D22.md`；`sed -n '1,40p' D22_RULING/FACTCHECK.md`；`stat` 各件 | `:29,31,38,54` 才是 Q5 短语出处；`RULING_D22.md:3` D-22=A（02:31:57 < Q5 03:05:03） |
| C-R14 | `grep -n 'except_post_sha256\|except_file_rewritten\|except_setdiff_new_lines\|DR0\|answer_detail' QC124_VERDICT.json`；`sha256sum/wc -c except.drift.6694B75E.26405B.bin`；`sed -n '9229,9290p' GOAL_THREE_TARGETS_20261018.md`；`sed -n '144p' PENDING_DECISIONS.md` | §3.2 反例链；drift bin `6694b75e…/26405`；§599 / D-22 订正原文 |
| C-R15 | `grep -c 'QC124\|§599\|D-22\|断点\|人为\|运行期写出\|except_file_rewritten' Q5_ROUTES.md`（逐词） | 全部 `0`；`DR0` 仅 4 次（Q3 候选用语） |
| C-R16 | `find W9 -maxdepth 1 -type f -newermt '2026-11-06 02:45:00'`；`git status --porcelain -- W9/`；`stat` 6 件只读源 | 仅 `_w9_q5.py`/`_w9_q5_out.txt`/`Q5_ROUTES.md` 三件；整树未跟踪；只读源 mtime 旧值 |
| — | `find . -type f -print0 \| xargs -0 sha256sum \| grep '^b42c7014…'`（全仓全扩展名绝对计数） | **300 s 超时，`TaskStop` 终止，未跑完 ⇒ 记未验**（Q5 亦自述未跑） |

探针与原始输出：`W9/reviews/_Q5_review_probe.py` / `_Q5_review_probe_out.txt` /
`_Q5_review_probe_stdout.txt` / `_Q5_exact_rerun.py` / `_Q5_exact_rerun_out.txt` /
`_Q5_exact_rerun_stdout.txt`。
