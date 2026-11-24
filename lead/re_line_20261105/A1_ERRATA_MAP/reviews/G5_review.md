# G5_review · 独立复核员·G5 对 ERRATA_G5.md 的复核

```
被核对象 = W9_SINGLESTEP.md / W8_STATIC_LOCATE.md / W7_W4_REVIEW.md / V6_V3_REVIEW.md
W9_SINGLESTEP.md   SHA256 = 13fa9fe35339ea40d123cf340b09c9ac692e848305ebc48d9d35f5421d895e36，字节数 = 40,592
W8_STATIC_LOCATE.md SHA256 = 20e4eeac49254b274a8382e94505525a614ec5bf24ccb89316fcd8f914406262，字节数 = 26,485
W7_W4_REVIEW.md    SHA256 = 22753a0ef603c6999c95b25e28a2b5a2d5820ded39c9b59559d088bf20da6ca6，字节数 = 19,225
V6_V3_REVIEW.md    SHA256 = 75cad20763952e7a6d92274f8d29e7db30c307194e45437d8d459242baceffdb，字节数 = 17,892
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4,825,360（本会话 sha256sum + wc -c 实算，未运行、未反汇编）
回件时刻 = 2026-11-06 10:04 +0800
```

> 以上五个哈希/字节数均为**本复核会话自己实跑**所得，命令：
> `cd "D:/Project/ra2-campaign-forge" && for f in lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/W9_SINGLESTEP.md lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md lead/re_line_20261105/W7_W4_REVIEW/W7_W4_REVIEW.md lead/re_line_20261105/V6_V3_REVIEW/V6_V3_REVIEW.md; do sha256sum "$f"; wc -c < "$f"; done && sha256sum ra2youli/gamemd.exe && wc -c < ra2youli/gamemd.exe`
> 输出（`sha256sum` 值 / `wc -c` 值）：`13fa9fe3…d895e36`/`40592`、`20e4eeac…4406262`/`26485`、`22753a0e…20da6ca6`/`19225`、`75cad207…2baceffdb`/`17892`、`73201cc0…f67476`/`4825360`。
> 与 ask「参考实算值」逐一相符 ⇒ **四个被核对象未变**（`shaBindingPresent` 前提成立）。
> 本复核零真机、零采样注入、零活进程读取、零 `ra2tool.Engine`；唯一写入 = 本件 + 本复核自建的两件探针副本（见 §9）；未 commit / 未 push。

---

## 0 总判 = **PARTIAL**

**G5 的五问主干全部独立复现成立**：Q1/Q2 才绑 `eb53a617…`、Q3 无副本绑定行、Q4 全文零哈希；V6 确已对 V3 重跑 R1–R5 且总判 CONFIRMED、绑定 `5081780c…`/499,047 B 与现盘逐字一致；V6 R1–R5 定义负担关键词全零；`RULING_D21.md:23` 的条件算式与自注不可作验收属实；四位精确值 `+13.094%`/`+31.355%` 的实算者仍只有 Leader。G5 对 Leader 的三处纠错（超范围 / 措辞 / 行号）我也逐条坐实。**没有发现 W7 phase 2 重建痕迹，G5 也没有改动任何既有件。**

但订正回件存在 **5 处必须修的引用与证据链缺陷**（详见 §7/§8），其中两处是实质性的：

1. **「探针 36/36 PASS」现在不可复现**：把 G5 自己保存的 `_a1_g5_probe.py` 原样重跑（只把输出重定向到新文件），实测 **34 PASS / 2 FAIL** —— 因 Leader 在 08:57 与 09:25 分别改了 `PENDING_DECISIONS.md` 与 `GOAL_RE_CONTINUOUS.md`，而探针把易变台账的**行号与命中数硬编码**为期望值、无版本绑定。
2. **§1 问 4 的「全线清点 / out/ 全目录 0 命中」不受探针支撑**：探针输出全文无 `out/`、无 `GOAL_THREE`、无「全线」字样（`_a1_g5_probe.py:144-153` 只硬编码点算了 6 个文件）；我实跑全树 `grep -rl "13\.094" . --exclude-dir=.git` 在 `out/` 找到 **16 个文件含裸子串 `13.094`**（多为时间戳巧合），另在 `lead/qc161_u0400_trip/` 找到 2 个 G5 表格未列的 JSON。**结论仍成立**（精确负担记号 `+13.094%`/`13.0942%`/`+31.355` 在 `out/` 实测 0 命中），但「0 命中」按字面写是错的、且缺实跑输出支撑。

不改判 REFUTED 的理由：上述两处都不推翻 G5 的残余定性（我独立确认精确值仍只有 Leader 自算），订正方向正确、五项事实全部复现；§4.4 自陈的「两读」判断我接受。但缺陷数量与性质超过「一行收窄」即可修补的程度，故不能记 CONFIRMED。

---

## 1 检查 1 · 回件是否真含自己实算的四 SHA256 + 字节数 —— **通过**

- `ERRATA_G5.md:10-20` 强制头部齐备：四个 .md 的 SHA256 + 字节数（`13-17`）、`gamemd.exe` 哈希（`18`）、回件时刻（`19`）、被核对象（`13`）。
- **不是照抄**：`_a1_g5_probe.py:41-48` 用 `hashlib.sha256(...).hexdigest()` + `len(...)` 对四份 `read_bytes()` 现场计算，`_a1_g5_probe_out.txt:5-10` 打印同值；`ERRATA_G5.md:10`、`:22`、`:95` 明示为自算/实算。我另用 `sha256sum`(1) 实算，与头部及 ask 参考值三方逐位一致。
- ⇒ `shaBindingPresent = true`。
- **小疵（objection，不改判）**：`ERRATA_G5.md:10` 写「自行 `sha256sum` / `wc -c` 实算」，而探针实际用 Python `hashlib` + `len()`，并未跑 shell 的 `sha256sum`/`wc -c`。等价但方法标注不精确；`:18` 却写「`sha256sum ra2youli/gamemd.exe` 实算」而探针里并无 gamemd 计算（`_a1_g5_probe.py` 全文无 `gamemd`）。方法描述宜按实际改成「Python `hashlib.sha256` + `len()`；gamemd 值另由 shell `sha256sum` 实算」。

## 2 检查 2 · rows 是否逐条覆盖应有条数 —— **通过（G5 组 5/5，非抽样）**

口径说明：ask 列的「W9 20 条 / W8 12 条 / W7 7 项 + A1」属**另三组**各自的回件，不是 G5 组的应有条数（`TASK.md:12-20` 把四组并列，G5 为「第四组（本轮新发现）…见 §3」；`TASK.md:80` 对 G5 只要求「在勘误表里登记一行」）。G5 自报 `rowCount=5`，其 `ERRATA_G5.md:3-4` 自述「五项事实」。故本组应有 = **5 问**。

实跑 `grep -n "^### 问" ERRATA_G5.md` → `:36/:52/:60/:70/:90` = **问 1–问 5 连续无缺**，与我逐条重跑的五项事实一一对应（见 §6 表，五行全部独立复现，无一条只靠转述）。⇒ `checkedEveryRow = true`。

**但结构性缺项须登记**：`TASK.md:22-28` 要求「每一条必须写清六件事」（原位置 / 原断言逐字 / 修订表述 / 原证据出处 / **现有汇总件是否已落实** / 当前判定档）。实测 `grep -c "已落实\|未落实\|部分落实" ERRATA_G5.md` = **0**，`grep -c "原断言"` = **0**，`grep -c "修订表述"` = **1**（仅 `:104` 的 §2 标题）；对照同批 `ERRATA_W9.md`（47/20/23）、`ERRATA_W8.md`（14/15/13）、`ERRATA_W7.md`（19/8/0）。**G5 是四组里唯一完全没有六列结构、完全没有落实列的一组**。§8 列为 mustFix。

## 3 检查 3 · alreadyLanded 是否真去看了汇总件落实处行号 —— **N/A，且无虚假声明**

- `ERRATA_G5.md` 全文 **0 处**「已落实/未落实/部分落实」，即 G5 **从未做过 alreadyLanded 判定**，因此不存在「凭感觉标已落实」的问题；同时也构成 §2 的六列缺项。
- 汇总件 `A1_ERRATA_MAP.md`（`TASK.md:94` 要求的 `## 5 G5 订正` 载体）**当前不存在**：实跑 `ls lead/re_line_20261105/A1_ERRATA_MAP/A1_ERRATA_MAP.md` → `No such file or directory`（A1 于 09:0x 被 provider 配额中断在 phase 3，`GOAL_RE_CONTINUOUS.md:270,272` 自述汇总与门槛未落盘）。故 G5 当时也**无汇总件可查**。
- 值得注意的**实际落实**：G5 §2 给的收窄文本已被编排者采纳，`PENDING_DECISIONS.md:88-95` 现为「【08:5x A1-G5 组复核后，我这两句被核实为超范围/措辞不当，就地收窄】」(i)(ii) 两条，并回引 `A1_ERRATA_MAP/ERRATA_G5.md:108,129`。**但 G5 回件本身没有、也不可能登记这一后续落实**（其 mtime 08:41 早于 PD 的 08:57）。
- ⇒ 本项不判 FAIL，但须在汇总件的 §5 G5 订正里补上「已落实 / 落实处 `PENDING_DECISIONS.md:88-95`（版本时刻 08:57）」这一列。

## 4 检查 4 · W7 组有无偷偷重做 phase 2 —— **通过（零痕迹）**

实跑 `grep -n -i "phase 2\|phase2\|W7\|ra2tool\|Engine\|gamemd\|MiniDump\|SuspendThread" ERRATA_G5.md _a1_g5_probe.py _a1_g5_probe_out.txt`，全部命中仅为：

| 位置 | 内容 | 性质 |
|---|---|---|
| `ERRATA_G5.md:13,16` / `_a1_g5_probe.py:43,47` / `_a1_g5_probe_out.txt:9` | `W7_W4_REVIEW.md` 的 SHA256 头部绑定 | 只读哈希，非复核 |
| `ERRATA_G5.md:5,138` / `_a1_g5_probe.py:3` | 「不用 `ra2tool.Engine`」「未触碰 W7 phase 2」 | 纯否定声明 |

无 W7 七项任何实质内容的重审、无「顺便验证」、无另起 run、无换名重建；`_a1_g5_probe.py` 全文 184 行只有 `Path(...).read_bytes()/read_text()/is_file()` 与一次 `write_text`（写自己的 `_a1_g5_probe_out.txt`），无 hook / MiniDump / SuspendThread / StackWalk / 注入 / 活进程读取。**D-24 `RULING_D24.md:75` 禁令遵守**，不触发「总判直接 REFUTED」。

## 5 检查 5 · 回件有没有修改任何既有件 —— **G5 未改；但编排者改了只读清单内的件，须如实登记**

**G5 侧通过**：
- 四个被核对象 SHA256 与参考值逐位一致（§0）；`stat -c '%y %s'` 显示 mtime 分别为 `2026-11-06 05:04:21` / `02:33:04` / `00:42:19` / `2026-11-05 21:16:15`，**全部早于** A1 会话（TASK.md 07:44）与 G5 落盘（08:34/08:41）。
- 实跑 `find <W9/W8/W7/V6/W5/D21/D24/A1_SAMPLER_CANDIDATE/_leader/ra2youli> -type f -newermt '2026-11-06 08:30:00'` → 仅 1 条：`W9_SINGLESTEP_7CFC9F/.mimosa/hook-status/…json`（485 B @08:58:52），是插件钩状态、非内容件，且时间对应 W9 复核会话，非 G5（G5 三件落盘 ≤08:41）。
- G5 自身三件全部在唯一写域 `A1_ERRATA_MAP/` 内：`_a1_g5_probe.py`(08:34:16)、`_a1_g5_probe_out.txt`(08:34:21)、`ERRATA_G5.md`(08:41:57, 12,134 B, SHA256 `59f3841b…d835b`)。
- `git status --short -- <受保护目录>` → 全部 `?? lead/re_line_20261105/<dir>/`（整树 untracked）。**诚实声明**：git 无法对 untracked 树内文件做修改比对，故此处以 SHA256 + mtime 双证为准（与 `W8_review.md:24,82` 同口径）。

**必须如实登记的外部事实（不归属 G5）**：`lead/PENDING_DECISIONS.md` mtime = `2026-11-06 08:57:44`（34,403 B）、`lead/re_line_20261105/GOAL_RE_CONTINUOUS.md` mtime = `09:25:33`（173,882 B），均在 G5 回件之后被改动；`GOAL_RE_CONTINUOUS.md:268` 自述「我已就地收窄 `PENDING_DECISIONS.md`」、`:272` 自述「已改 `ERRATA_W8.md` 两处」。其中 `PENDING_DECISIONS.md` 位于 `TASK.md:128` 的「一律只读」清单。**该改动是编排者（Leader）所为，G5 探针纯只读、不可能是它做的；但该只读铁律在 A1 会话期间确被编排者自己破坏**，且正是这次改动造成 §7 的行号漂移与探针 36→34。本复核不计为 G5 舞弊，但按「不许修改任何既有件」的字面核对，不能写「全部既有件零改动」而不加此注。

---

## 6 五问逐条独立复现（非抽样，每行都重跑了实命令）

| 问 | G5 断言 | 本复核实跑命令与输出 | 复现 |
|---|---|---|---|
| 1 `:36-50` | Q1 2 处/Q2 3 处绑 `eb53a617…`；Q3 无副本绑定行、Q4 全文零哈希；四件 `5081780c` 全 0 | `for f in Q1 Q2 Q3 Q4; do grep -c "eb53a617" …; done` → `2,3,0,0`；`grep -n "eb53a617"` → Q1 `:47,:132`、Q2 `:6,:35,:106`；`grep -c "5081780c"` → `0,0,0,0`；`grep -nE "[0-9a-f]{64}"` → Q3 仅 `:235`（母本 `38244d29…`，「删块即还原」语境）、Q4 无输出 | ✅ |
| 2 `:52-58` | V6 总判 CONFIRMED、绑定 `5081780c…`/499,047 B | `V6_V3_REVIEW.md:16`「最终裁决：CONFIRMED」、`:24` 全项全绿、`:30-35` 总表 R1–R5 三列全 CONFIRMED、`:79/:88/:96/:104/:113` 逐项终审 CONFIRMED；`grep -c "CONFIRMED"`=20；`sha256sum W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py` = `5081780c5a2e…d83f161`、`wc -c` = `499047`，与 `:48` 一致；母本 `38244d29…`/`489502` 亦一致；`grep -c dwfrun`=0（run ID 出处 `PENDING_DECISIONS.md:85`） | ✅ |
| 3 `:60-68` | V6 R1–R5 定义无负担关键词、判定书 13.094/31.355 全 0、`:17` 只列参考件 | `python -I -X utf8 -c` 读 `V6_V3_REVIEW/TASK.md` L44–L77 → `{'负担':0,'burden':0,'13.094':0,'31.355':0,'开销':0,'百分比':0}`，`L78=''`（⇒ R5 实止于 **:77**，`TASK.md:71` 的「:44-76」确为小误）；`grep -c` 于 `V6_V3_REVIEW.md`：`13\.094`=0、`31\.355`=0、`负担`=0、`burden`=0、`百分比`=0；`V6_V3_REVIEW/TASK.md:17` 确列 `_d21_burden5_out.txt`「五读负担实算（+13.094% / 最坏窗 +31.355%）」 | ✅ |
| 4 `:70-88` | 四位精确值实算者仅 Leader；`RULING_D21.md:23` 有四舍五入条件算式且自注不可作验收 | `EXECUTION_D21.md` 实为 §4 跨 `:89-113`（`:94` +13.094%、`:101` +31.3550%、`:111` +13.094%、`:113` 31.3549）；`_d21_burden5_out.txt:12,17,26` 有两组数；`RULING_D21.md:23` 逐字含 `约 +13.09%`/`约 +31.36%`/「条件算式和近似换算」/「没有运行计算脚本、普查数据或确认改后运行计数，**不能充作改后验收结果**」；`GOAL_THREE_TARGETS_20261018.md:7537,7590,7594,7602,7605`、`PENDING_DECISIONS.md:97-99`、`V6_V3_REVIEW/TASK.md:17`、`A1_ERRATA_MAP/TASK.md:71,74` 均为台账/派单转引；全树精确记号 `+13.094%\|13.0942%\|+31.355` 在 `out/` = **0** 命中 | ✅（但「全线清点/out/ 0」表述有缺陷，见 §7-②） |
| 5 `:90-95` | V6 绑定段完整（`:47-51` 五对象 + `:57-66` 十回件哈希，含 `5081780c`/`38244d29`） | 逐行实读 `:39-66`；`grep -n "38244d29\|5081780c" V6_V3_REVIEW.md` → `:48`(5081780c)、`:50,:101,:127`(38244d29)，G5 所述「5081780c 行数=1、38244d29 行数=3」成立；现盘两哈希与绑定值一致 | ✅ |

**G5 对 Leader 的三处纠错也逐条坐实**：① `TASK.md:68` 逐字为「W5 四道旧复核绑的是 `eb53a617…`」，而 Q3/Q4 无此绑定 ⇒ 超范围属实；② `Q4_review.md:1` 标题即「Q4（观测开销复算）独立复核报告」、`:17` 判「计算准确性…独立重跑 `_w5_burden.py`」、`:61` 负担表 `+10.475/+15.713/+15.665` ⇒ 「Q4 没有独立复核」按字面相抵属实；③ `V6_V3_REVIEW/TASK.md` R5 止于 `:77`、`EXECUTION_D21.md` §4 跨 `:89-113`（`:101` 在区间内）⇒ 两处行号小偏差属实。

---

## 7 本复核新发现 / Objections（按严重度）

**①【实质·可复现性】「36/36 PASS」是当前不可复现的历史时点值，探针缺版本绑定。**
保存的 `_a1_g5_probe_out.txt:150` 确实是 `36 PASS / 0 FAIL`（`grep -c '^\[PASS\]'`=36、`'^\[FAIL\]'`=0），这在 08:34:21 属实。但把 **同一份** `_a1_g5_probe.py` 复制到 `reviews/_g5_probe_reverify.py`（仅把 `write_text` 目标改为新文件，其余一字未改）后实跑 `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_ERRATA_MAP/reviews/_g5_probe_reverify.py"` → 打印 `PASS 34 / 36`，`_g5_probe_reverify_out.txt:150` = `总计 36 项检查：34 PASS / 2 FAIL`。两处 FAIL：
- `'13.094' 计数 == bash grep 结果: GOAL_RE_CONTINUOUS.md = 5（2 行）` → `实跑计数 = 6`（`GOAL_RE_CONTINUOUS.md:268` 节拍轮 55 新增一次转引，mtime 09:25）；
- `PENDING_DECISIONS.md L93 含『唯一出处 … EXECUTION_D21.md:89-101』` → 现 `PD:93` 是 Q4 收窄文字，该句已移至 `PD:99`（mtime 08:57）。

根因：`_a1_g5_probe.py:141-153,164-169` 把易变台账的命中数与行号硬编码为期望值。34 项静态检查（Q1–Q4 / V6 / D21 / EXECUTION）仍全绿 ⇒ **结论未受影响**，但自述「探针 36/36 PASS」若无版本时刻，读者现在重跑会得到 34/36 并误判回件不实。ask 给的 `headerLines` 也把这一历史值当作现况陈述，需同步加注。

**②【实质·证据链】「全线清点 / `out/` 全目录 0 命中」不受探针支撑，字面还被实测反例击中。**
`ERRATA_G5.md:72` 写「实跑 `grep -o "13\.094" | wc -l` 全线清点（re_line_20261105 全树 + 台账 + `out/` 全目录）」，`:82` 表格记 `out/ 全目录 | **0**`，`:137` 写「`out/` 仅做 `grep -rl "13\.094"` 全目录存在性扫描（0 命中）」。但：
- `_a1_g5_probe_out.txt` 全文**不含** `out/`、`GOAL_THREE`、`全线`（实跑 Python `in` 检查：`False/False/False`）；探针只硬编码点算了 6 个文件（`_a1_g5_probe.py:144-153`），**没有全线清点这一动作的输出**。
- 我实跑 `grep -rl --exclude-dir=.git "13\.094" . 2>/dev/null | sort`（后台任务 120 s 上限内完成）→ 除 G5 表列 7 项外，另有 `lead/qc161_u0400_trip/l1c_20261021/measure_w1.json`、`l1e_20261021/measure_w2.json`，以及 `out/re_work/work_chain/CONTINUE_20261003/lead/...` 下 **16 个文件**含裸子串 `13.094`。
- 抽查这些 `out/` 命中的性质：`…33513.091871, 33513.094406, 33513.097…`（measure_w1.json）、`…[13.0922, 0], [13.0946, 0], [13.097…`（h8_wait_trace.json）——**都是时间戳/采样数值的巧合子串**，不是负担百分比。对这 16 个 + 2 个 JSON 逐一读字节查精确记号 `+13.094%`/`13.0942%`/`+31.355` → **0 命中**。
- ⇒ **G5 的实质结论（精确值实算者仅 Leader）成立**，但「out/ 0 命中」按裸子串字面写是**错的**，且「全线清点」是**无输出支撑的方法宣称**。须改成「精确负担记号在 `out/` 0 命中；裸子串 `13.094` 在 `out/` 有 16 个时间戳巧合文件」并附实跑命令与输出。另 `timeout 60 grep -rl … out/ | wc -l` 我这边两次均 `exit=124`（超时），故 **out/ 的完整枚举本复核记为「未验（受时限）」**，仅以已完成的后台全树扫描所列 16 文件为界；不把「查不到」当「不存在」。

**③【实质·行号漂移】§2 / §4 的 PD 锚点在 G5 定稿后即失效，且「原句」现已不存在。**
`ERRATA_G5.md:100-102` 标「**原句**（`PENDING_DECISIONS.md:88`…）」并逐字引用「旧的 W5 四道复核（`W5_HARNESS_EXT/reviews/Q1~Q4_review.md`）绑的是 `eb53a617…`，**已被 V6 取代**。」实跑 `grep -n "旧的 W5 四道复核（" lead/PENDING_DECISIONS.md` → **无匹配**；当前 `PD:88` 是「★【08:5x …就地收窄】」、`PD:89` 收窄 (i)、`PD:92-94` 收窄 (ii)、`PD:95` 只剩「旧的 W5 四道复核已被 V6 取代。」。同样，自述 `leaderErrors` 里的 `PENDING_DECISIONS.md:88`、`:89` 与探针 `:168-169` 的 `L88`/`L93` 均已漂移。这正是 `W9_review.md:65,87` 已确立的「引 PD 必须带版本时刻」问题。收窄文本本身没问题（编排者已照它改），但「可直接替换」的**原句定位**已不可复现，须改为带 `PD@2026-11-06 08:34 版本` 的历史锚点或改标「已被采纳并就地替换，见 `PD:88-95`（08:57 版）」。

**④【结构】六列 / alreadyLanded 全缺**（见 §2、§3）：`TASK.md:22-28` 的六件事里，G5 只做了「原位置/修订表述/原证据出处/判定档」四项，`已落实` 列与「原断言逐字」列全无；汇总件 `A1_ERRATA_MAP.md` 亦未落盘。

**⑤【轻微·登记性】** `:10` 方法标注（hashlib 写成 `sha256sum`，gamemd 值与探针不符，见 §1）；`:19` 回件时刻 `08:38` 与文件 mtime `08:41:57` 差约 4 分钟（与「先定稿后落盘」相容，仅记录）；`:22`「四值与任务书参考实算值逐字一致 —— 是核对结果，不是抄录来源」措辞可保留但宜补上实跑命令以便第三方复核。

---

## 8 mustFix（须在 G5 回件 / 汇总件进入引用规则前修完）

1. **给「36/36 PASS」加版本时刻与重跑现状**：在 `ERRATA_G5.md:6`、`:30`、`:136` 与 `_a1_g5_probe_out.txt` 头部注明「36/36 为 `2026-11-06 08:34:21` 盘面值；`PENDING_DECISIONS.md`(08:57) 与 `GOAL_RE_CONTINUOUS.md`(09:25) 后续被编排者改动，现盘重跑为 34/36，2 处 FAIL 均为易变台账锚点、与 G5 五项结论无关」，并把两份台账的 SHA256/字节数写进探针绑定段（`PENDING_DECISIONS.md` = `be22211c…40541`/34,403 B、`GOAL_RE_CONTINUOUS.md` = `9479d3b2…70541`/173,882 B，均为本复核 09:0x 实算）。
2. **改正 §1 问 4 的清点表述**：把「全线清点 / `out/` 全目录 0」改为有实跑输出支撑的**精确记号**版本，明确区分裸子串时间戳巧合（16 个 `out/` 文件 + 2 个 lead JSON）与四位精确值，并补 `GOAL_THREE_TARGETS_20261018.md` 之外漏列的两份 JSON；把无法在时限内完成的 `out/` 完整枚举标为「未验（超时）」，不得写成 0。
3. **修 §2 / §4 的 PD 行号锚点**：`PENDING_DECISIONS.md:88`、`:89`、`:93` 全部改为带版本时刻的历史锚点，或改标「已由编排者于 08:57 就地收窄，见 `PD:88-95`」；§2 的「原句」须注明是 **08:34 盘面** 的逐字引用，现盘已不存在。
4. **补六列结构**：至少为 5 问各补 `原断言（逐字）` 与 `现有汇总件是否已落实` 两列；落实列写「已落实 — `PENDING_DECISIONS.md:88-95`（08:57 版，采纳 ERRATA_G5.md §2/§4）」，并在汇总件 `## 5 G5 订正` 落成后回填行号。
5. **补方法标注**：`:10` 改为「Python `hashlib.sha256` + `len()`（四份 .md）/ shell `sha256sum`（gamemd.exe）」；`:18` 的 gamemd 实算声明与探针解绑或补进探针。
6. **汇总件补登记**：`TASK.md:94` 要求的 `A1_ERRATA_MAP.md` 当前不存在（`ls` 已证），其 `## 5 G5 订正` 须纳入本复核 §7 的三处新发现，不能只抄 G5 自陈的 `PARTIAL(5 行)`。

---

## 9 诚实账

- **本复核实跑的关键命令**（均在本会话执行）：四个 `sha256sum`/`wc -c`；`gamemd.exe` 的 `sha256sum`/`wc -c`；Q1–Q4 的 `grep -c/-n "eb53a617"`、`grep -c "5081780c"`、`grep -nE "[0-9a-f]{64}"`、`wc -l`；V6 的 `grep -c` 五组 + `awk NR==14..37/47..51/39..66`；V6 TASK 的 `python -I -X utf8 -c`（L44–L77 关键词）；`EXECUTION_D21.md:86-116`、`RULING_D21.md:20-26` 的 `awk`/逐字 `python` 读；副本/母本 `sha256sum`+`wc -c`；`PENDING_DECISIONS.md` 与 `GOAL_RE_CONTINUOUS.md` 的 `stat -c '%y %s'`/`sha256sum`/`awk`；`find … -newermt '2026-11-06 08:30:00'`；`git status --short/--porcelain`；`grep -c '^\[PASS\]'/'^\[FAIL\]'`；`python -I -X utf8 reviews/_g5_probe_reverify.py`（34/36）；`diff` 两份探针输出；全树 `grep -rl --exclude-dir=.git "13\.094" .` 与 `31.355`；16+2 个文件的精确记号逐字节检查；`ls A1_ERRATA_MAP.md`。
- **未做 / 未验**：未启动任何真机、未读活进程内存、未用 `ra2tool.Engine`、未反汇编 `gamemd.exe`、未重算负担数字（与 `TASK.md:78-82` 一致，不持异议）、未重建 W7 phase 2；`out/` 的**完整**文件级枚举两次 `timeout 60` 均 `exit=124`，记为「未验（受时限）」（§7-②）；git 对 untracked 树无法做修改比对，已以 SHA256 + mtime 双证替代（§5）。
- **本复核新建文件（均在唯一写域 `A1_ERRATA_MAP/reviews/` 内）**：`G5_review.md`（本件）、`_g5_probe_reverify.py`（G5 探针的逐字副本，仅替换输出路径）、`_g5_probe_reverify_out.txt`（其 34/36 原始输出）。**未覆盖 `_a1_g5_probe_out.txt`**（`diff` 仍显示原件的 36 PASS 行可证）。未修改任何既有件，未 commit / 未 push。
- **判档**：`verdict = PARTIAL`；`shaBindingPresent = true`；`checkedEveryRow = true`（G5 组 5/5 问逐条独立复现，非抽样；W9/W8/W7 条数属另三组，不适用）。四项专项检查（SHA / 逐条 / 无 phase 2 / 未改既有件）均通过；检查 3（alreadyLanded）为 N/A 且无虚假落实声明，但构成六列缺项。若按「发现给定事实有实质错误即 REFUTED」字面口径，§7-①/② 可支持 REFUTED；我不取该档，理由是两处缺陷都不推翻 G5 残余定性、且 4/5 项检查干净通过，与 G5 §4.4 自陈的两读判断一致 —— 两读在此明示。
