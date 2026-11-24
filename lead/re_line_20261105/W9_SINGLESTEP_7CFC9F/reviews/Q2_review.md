# 独立复核 · Q2（`Q2_FUNCTION.md` 与 `_w9_q2*.py/_out.txt`）

> 复核员：独立复核员·Q2（默认怀疑）。零真机、零采样注入、零活进程读取。
> 唯一写域 = `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/`；既有文件一律未改。
> 复核时刻：2026-11-06 03:10–03:30。所有数字均为本会话亲自实跑。

---

## 0 · 结论

**verdict = CONFIRMED（对 Q2 自身判定范围），但附 3 项必须登记的反例/边界 objection。**

- `Q2_FUNCTION.md` 的强制头部**确有**自算的两个 64 位 SHA256（gamemd.exe 与 EXCEPT 件），且两项哈希、字节数、Engine 自证全部被本会话独立复算复现。
- Q2 三条结论（最近序言 / 函数起止长度与唯一 `ret` / 既有分析覆盖）**每一条都有「反汇编地址 + 原始字节」或「文件:行」支撑**，不是只给地址。本会话重跑关键反汇编与字节读，逐项一致。
- 默认找反例：找到了 **3 项不能算实质错误、但应登记的边界**（见 §5）：
  1. 头部「回件时刻 = 01:28:18」与探针落盘输出「01:20:23」相差 7m55s，交付件未说明该时刻是**正文成稿时刻**而非探针运行时刻；
  2. `0x7CFC9F in e.by()=True` 被解读为「非 call/jmp 落点」在逻辑上不严格（指令起始与「是跳转落点」并不互斥），本会话补跑全流立即数目标枚举才把它坐实为 0；
  3. **覆盖度搜索的绝对数字是时点快照**：本会话同口径重跑为 109/71，Q2 报 80/66；差异经净列表 diff 坐实为 Q2 探针落盘（01:22:16）**之后**新建/改写的 5 个既有文件，不是 Q2 算错。Q2 §6.4 已登记 80/81 微差，但未（也无法）预见后续 W9 兄弟任务继续加文件。结论方向「覆盖极密」不受影响。
- **Q4 的哈希比对该不该全量**：该全量，且本会话**独立全量重跑**了整仓 `except_post_*.txt` 的 SHA256 逐份比对（113 份，非抽样），结果 113/113 同哈希、distinct=1、尺寸全 26405 B，与 Q4_RELATION.md 一致。Q2 只报告实算哈希前缀、把二选一交给 Q4 是**正确的范围纪律**，不是漏项。详见 §6。

---

## 1 · 强制头部：真含两个自算 SHA256 吗？（点名检查 1）

**结论：真含，且两项哈希与字节数均独立复现。**

`Q2_FUNCTION.md:3-9` 原文：

```
被核对象 = gamemd.exe + EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，字节数 = 4825360
EXCEPT 件 SHA256 = 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251，字节数 = 26405
Engine 自证 = COVERAGE 99.9984% / IMAGEBASE 0x400000
回件时刻 = 2026-11-06 01:28:18
```

五个字段齐全（被核对象 / 两个 SHA256 各 64 位 + 字节数 / Engine 自证 / 回件时刻），符合 `TASK.md:77-83` 的强制头部模板。

**本会话独立实跑（两条不同实现互证）：**

命令 A（Git-Bash 原生）：
```
cd D:/Project/ra2-campaign-forge && sha256sum ra2youli/gamemd.exe \
  out/re_work/work_chain/CONTINUE_20261003/lead/boot_hang_triage_20261018/EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt \
  && ls -la <两文件>
```
输出（`reviews/_q2_review_probe_out.txt:1-2`、`reviews/_q2_review_hash_out.txt` 复核）：
```
73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 *ra2youli/gamemd.exe   (4,825,360 B)
6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251 *...EXCEPT...txt      (26,405 B)
```
命令 B（`python -I -X utf8 -c`，hashlib 独立读盘）：输出同值同字节数（`reviews/_q2_review_probe_out.txt:1-2`）。

命令 C（自写探针 `reviews/_q2_review_probe.py:22-25`，`python -I -X utf8`）输出同值；`reviews/_q2_replay_out.txt:3-4` 为 Q2 原探针重放，亦同值。

**头部来源可追**：`_w9_q2.py:38-45` 用 `open(...,"rb").read()` + `hashlib.sha256` 自算并 `P` 打印，`_w9_q2_out.txt:2-4` 落盘。`_w9_q2.py:47-54` 真实例化 `Engine()`，`_w9_q2_out.txt:5-7` 打印 COVERAGE 99.9984% / 1394120 insns / resync_fails=66 / IMAGEBASE 0x400000 / `Engine.sha 一致=True`。这些不是抄 TASK.md 的期望值：`ra2tool.py:29,55` 的 `EXPECT_SHA` 是 `Engine()` 构造内的断言，而 Q2 的头部数字来自它**自己**读盘算的 `raw_exe`/`raw_exc`。

**→ `sha256BindingPresent = true`。**

> 小 objection（非作废）：`Q2_FUNCTION.md:8` 的「回件时刻 = 2026-11-06 01:28:18」≠ `_w9_q2_out.txt:2` 的「01:20:23」，也 ≠ `_w9_q2_out.txt` 文件 mtime `01:22:16`（`ls -la --time-style=full-iso`）。Q2 正文 `:30` 把哈希来源标为 `_w9_q2_out.txt:3`，但头部自己写的时间是另一个值，未在正文交代。按 TASK.md:82「回件时刻 = 实际时刻」，两个都是合法时刻（探针启动 vs 正文成稿），不影响哈希绑定，但**建议在 W9 汇总件里注明口径**。

---

## 2 · 结论有「反汇编地址 + 原始字节」支撑吗？（点名检查 2）

**结论：有，且本会话重跑全部关键项逐字节一致。不是只给地址。**

自写只读探针 `reviews/_q2_review_probe.py`（`python -I -X utf8`，EXIT=0，2m3.410s）输出在 `reviews/_q2_review_probe_out.txt`。逐项对照：

| Q2 断言 | Q2 出处 | 本会话独立实跑输出 | 判定 |
|---|---|---|---|
| `e.rd(0x7CFB12,10) = C3 55 8B EC 83 EC 14 A1 94 8B` | `Q2_FUNCTION.md:76`、`_w9_q2_out.txt:24` | `_q2_review_probe_out.txt:7` 同值 | ✅ |
| 序言 `e.rd(0x7CFB13,5)=55 8B EC 83 EC`；逐条 `55 / 8BEC / 83EC14 / A1948BB700` | `:85-89`、`_w9_q2_out.txt:27-31` | `_q2_review_probe_out.txt:8-9` 同值同助记符 | ✅ |
| 前一函数尾声 `0x7CFB0E..12 = pop edi/esi/ebx, leave, ret`；`e.rd(0x7CFB0D,6)=00 5F 5E 5B C9 C3` | `:75-79`、`_w9_q2_out.txt:24-26` | `_q2_review_probe_out.txt:10` + `_q2_review_bytes_out.txt:1` 同值 | ✅ |
| `e.rd(0x7CFC9F,32) = 8B 0A 2B 4D F0 8B F1 89 4D F8 C1 FE 04 4E 83 FE 3F 7E 03 6A 3F 5E 3B F7 0F 84 0D 01 00 00 8B 4A` | `:209`、`_w9_q2_out.txt:11` | `_q2_review_probe_out.txt:5` 同值；且 `_q2_review_bytes_out.txt:3-5` 与 EXCEPT 件 `Bytes at CS:EIP` 行 32/32 逐字节一致、diff=[] | ✅ |
| `0x7CFC9F in e.by() = True` | `:208`、`_w9_q2_out.txt:10` | `_q2_review_probe_out.txt:5` `True`；`_q2_review_probe_out.txt:6` 前 8 条反汇编（`8b0a mov ecx,[edx]` 起） | ✅ |
| 275 条、完全连续无 gap、first=`0x7cfb13` / last=`0x7cfe1b` / last_end=`0x7cfe1c` | `:206`、`_w9_q2_out.txt:43` | `_q2_review_probe_out.txt:13-15` `275` / `gaps=[] count=0` / 同地址 | ✅ |
| 长度 `0x309=777 B`、EIP 相对 `+0x18C=+396 B` | `:204,207`、`_w9_q2_out.txt:41-42` | `_q2_review_probe_out.txt:16-17` 同值 | ✅ |
| `e.func_rets(0x7CFB13,0x7CFE1C)=1`，ret @ `0x7CFE1B` bytes=`C3` | `:205`、`_w9_q2_out.txt:44-45` | `_q2_review_probe_out.txt:18-19` 同值 | ✅ |
| 交叉 `e.func_rets(0x7CFB13,0x7D0113)=3`（`0x7cfe1b/0x7cfecc/0x7cffc7`） | `:148-150`、`_w9_q2_out.txt:46` | `_q2_review_probe_out.txt:20` 同值 | ✅ |
| 5 个 `C3` 字节偏移，只有 `0x7cfe1b` 在 `by()`；4 个内部者都属 `83 C3 14` | `:187-193`、`_w9_q2_out.txt` 补充命令 | `_q2_review_probe_out.txt:21-26` 同 5 个偏移、同 `in by()` 结果、逐条定位到 `add ebx,0x14` | ✅ |
| 下一函数 `0x7CFE1C`: `A1 94 8B B7 00 8B 0D 84` = `mov eax,[0xb78b94]` | `:160-161`、`_w9_q2_out.txt:47-48` | `_q2_review_probe_out.txt:27` 同字节同助记符，`in by()=True` | ✅ |
| 尾声 `89 08 / 8D 42 04 / 5F / 5E / 5B / C9 / C3` | `:163-170`、`_w9_q2_out.txt:49-56` | `_q2_review_probe_out.txt:28` 逐条同值；`_q2_review_bytes_out.txt:2` `rd(0x7CFE11,11)=FC 89 08 8D 42 04 5F 5E 5B C9 C3` | ✅ |
| 3 处 `call 0x7CFB13` xref，含 `0x7C9484 E8 8A 66 00 00` | `:114-118` | `_q2_review_probe_out.txt:12` 同 3 处同字节；`_q2_review_edges_out.txt:3` 再核 | ✅ |
| 6 个序言候选表（最近 `0x7CFB13` Δ=0x18C） | `:61-70`、`_w9_q2_out.txt:16-22` | `reviews/_q2_review_cands_out.txt:1-8` 独立重跑，6 行逐项同地址/签名/字节/Δ | ✅ |
| 越界 `call/jmp` 目标仅 2 处（`0x7CFBDF→0x7CFE1C`、`0x7CFBEE→0x7CFECD`） | `:194-196` | `_q2_review_probe_out.txt:29` 同 2 处 | ✅ |

另外，把 Q2 原探针**原样重放**到本写域（不改原件）：
```
time python -I -X utf8 lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q2.py \
  > lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/_q2_replay_out.txt 2>&1
```
`REPLAY_EXIT=0`，`real 1m22.978s`，247 行（原 230 行，差在 grep 清单膨胀）。对核心反汇编段做
`diff <(sed -n '3,58p' _w9_q2_out.txt) <(sed -n '3,58p' reviews/_q2_replay_out.txt)` →
**`SECTION 3-58 IDENTICAL`**（无输出）。即头部 + Q2-(1) + Q2-(2) 的全部字节/地址逐行可复现。

**→ 本项通过。Q2 不是「只给地址」。**

---

## 3 · 三条 Q2 要求逐条核（`TASK.md:45-50`）

### Q2-(1) 最近函数序言
`_w9_q2.py:69-82` 限定窗口 `[0x7CF000,0x7CFC9F]`（未全盘扫），对 `va in by()` 逐址匹配 `55 8B EC 83 EC` / `55 8B EC`。本会话独立重跑得 6 个候选、最近 `0x7CFB13`（`_q2_review_cands_out.txt`）。

**默认找反例（TASK 第二种口径 `sub esp,imm` 且前方 ret/int3 对齐）**：自写 `reviews/_q2_review_counter.py` 全量枚举（`_q2_review_counter_out.txt:4-13`）：窗口内 8 个 `83/81 EC` 起始，**唯一**紧邻前置字节为 `C3` 的是 `0x7CF465`（`83 EC 08 DD 14 24`），与 Q2 `:94-96` 一致。Q2 用「中间隔着 16 个 ret」排除它 —— 本会话复核该 16 个地址列表（`_q2_review_counter_out.txt:3` 中 `[0x7CF465,0x7CFB13)` 子集）确含 `0x7cf4bd,0x7cf4c4,0x7cf4c9,0x7cf64b,0x7cf6ac,0x7cf6b0,0x7cf6e8,0x7cf6ec,0x7cf761,0x7cf767,0x7cf775,0x7cf77e,0x7cf79b,0x7cf7bc,0x7cf7e7,0x7cfb12` 共 16 个，且 `0x7CFB12` 是紧邻 HEAD 的 `ret`（`_q2_review_counter_out.txt:16` `nearest preceding ret = 0x7cfb12 delta=1`）。`(0x7CFB13,0x7CFC9F)` 内 ret 起始 = `[]`（`_q2_review_probe_out.txt:11`）。**未找到反例。**

补充反例搜索（`_q2_review_edges_out.txt`）：外部 `call/jmp` 立即数目标落入 `(0x7CFB13,0x7CFE1C)` 开区间 = **0**；到 HEAD 的分支 = 3（全为 `call`）；窗口内间接 call/jmp = **0**；窗口内 `55 8B EC` 字节三元组只有 HEAD 自身 1 处。**未找到「函数中间另有入口」的反例。**

### Q2-(2) 起止 / 长度 / ret 数
全部见 §2 表。`e.func_rets` 定义 `ra2tool.py:216-218` 取 `[lo,hi)` 内 `ret*`，传 `hi=0x7CFE1C` 恰好计入 `0x7CFE1B` → 1，与 Q2 `:152-154` 的口径解释一致。唯一 ret 的防漏核（4 个内部 `C3` 数据字节）本会话独立复现。**未找到反例。**

> 严格边界（登记为 objection，非错误）：`func_rets` 是**线性区间内 ret 指令枚举**，不是控制流可达性证明。Q2 用「越界 call 仅 2 处且都是 call、无尾部外跳」补强，本会话 `_q2_review_counter_out.txt:15` 复核「无条件 jmp 立即数越界 = []」、`_q2_review_probe_out.txt:29` 复核越界目标仅 2 个 call。故在此镜像的静态线性解码口径下「唯一 ret = 唯一出口」成立；但「运行期无外部跳入/间接调用」本会话静态只证了**直接立即数分支为 0**（`_q2_review_edges_out.txt:2`），不能排除间接跳转——Q2 `:368-370` 已把运行期 hook 记「未验」，口径诚实。

### Q2-(3) 既有分析覆盖（至少两种写法）
`_w9_q2.py:168-182` 定义 5+5 种口径，`_w9_q2_out.txt:64-226` 逐条打印完整命令与命中文件。TASK.md:50 要求「至少两种口径（`7CFC9F`、`0x7CFC9F`、`7cfc9f`）」，Q2 用了 10 种，超标完成。

本会话全口径重跑（`reviews/_q2_review_grep_out.txt`，2026-11-06 03:16:41，`ugrep 7.8.4`）：

| 口径 | Q2 报（`_w9_q2_out.txt`） | 复核时点 | 差 |
|---|---:|---:|---:|
| A `7CFC9F -i` | 80 | 109 | +29 |
| B `0x7CFC9F -i` | 32 | 59 | +27 |
| C `7cfc9f` 敏感 | 6 | 9 | +3 |
| D `7CFC9F` 敏感 | 79 | 109 | +30 |
| E `007CFC9F -i` | 60 | 73 | +13 |
| F-HEAD `7CFB13` | 27 | 40 | +13 |
| F-HEAD0x | 11 | 24 | +13 |
| F-TAIL `7CFE1B` | 5 | 11 | +6 |
| F-NAME | 29 | 38 | +9 |
| F-WIN `7CFC9B` | 43 | 61 | +18 |
| 净数（排 W9 + `.mimosa`） | 66（docs/re 10 / lead 56） | 71（docs/re 10 / lead 61） | +5 |

**数字差不是 Q2 算错**：用 Python 解析 `_w9_q2_out.txt:214-215` 的净列表与复核时点净列表做集合 diff，输出（`_q2_review_netlist.txt` + 本会话命令）：
```
Q2 delivered net = 66  review-time net = 71
ADDED since Q2 = ['lead/PENDING_DECISIONS.md',
  'lead/re_line_20261105/D22_RULING/FACTCHECK.md',
  'lead/re_line_20261105/D22_RULING/RULING_D22.md',
  'lead/re_line_20261105/D22_RULING/_d22_facts.py',
  'lead/re_line_20261105/D22_RULING/_d22_facts_out.txt']
REMOVED since Q2 = []
```
`ls -la --time-style=full-iso` 证实：`_w9_q2_out.txt` mtime = `2026-11-06 01:22:16`，`D22_RULING/` 四件 mtime = `02:25–02:31`，`PENDING_DECISIONS.md` mtime = `03:07:34` —— **全部晚于 Q2 探针**。Q2 原探针重放（`_q2_replay_out.txt`）在同一时点也报净 71，原始 A=115，进一步坐实是时点差异而非实现差异。`crashspec` 三目录计数用 Q2 原探针重放仍为 `11 / 11 / 7`（`_q2_replay_out.txt` 末段），与 Q2 报数一致。

> 实现差异登记：本机 `grep` 交互式是 `ugrep 7.8.4` 包装函数（默认跳过 `.gitignore`/隐藏目录），而 `python -I -X utf8` 的 `subprocess.run(["grep",...])` 解析到 `D:\Git\usr\bin\grep.EXE`（`shutil.which('grep')` 实测，见 `_q2_review_cite_out.txt`）。因此我手工 shell 重跑 crashspec 得 9、而 Q2 探针/GNU grep 得 11：差的 2 个是 `crashspec_v4/.zcode/workflow-drafts/*.dwf.ts` 与 `.zcode/workflow-runs/*.mjs` 被 `.gitignore` 隐藏（`_q2_review_cite_out.txt` 列出两实现清单）。Q2 用的是 GNU grep，报 11 正确；**两种口径都 ≥7 个实质语料文件，「被密集分析」结论不受影响**。

**文件:行 支撑**（本会话亲读）：`docs/re/except_zc11_forensics.md:112-120` 逐条给出 `007CFB13: 55 / 8BEC / 83EC14 / A1948BB700`，与本会话 `e.rd` 同字节；`:160` `★ 崩溃于 +0x18C = 0x007CFC9F`；`docs/re/sbh_freelist_deep_dive.md:30-38,74-75`；`docs/re/ARCHITECTURE_ATLAS.md:2257,2318,4727`（`:2318` = `0x007C9484: E8 8A 66 00 00 call 0x007CFB13`）；`docs/re/crt_memory_pool_deep_dive.md:48,129`；`docs/re/LESSONS_20261003_RE_INSTRUMENTS.md:75,151`；`out/re_work/work_chain/CONTINUE_20261003/crashspec_v4/RC_SPEC_V4.md:109`（「函数边界 `0x7CFB13–0x7CFE1B`、线性序唯一 `ret` 在 `0x7CFE1B`，`0x7CFE1C` 为另一函数」）与 `:158`（「275 条指令」）。旧分析 `SINGLESTEP_0x7CFC9F_ANALYSIS.md:43` 原文（本会话 `sed -n '40,47p'` 亲读）与 Q2 `:334-335` 引文一致。

**默认找「覆盖注水」反例**：本会话对 Q2 的 66 个净命中文件逐一算 SHA256，发现其中 **6 个与 EXCEPT 件逐字节相同**（`_q2_review_redundancy_out.txt`）：`lead/l1_u0800_20261020/evidence_r2/except_carrier_6694b75e.txt` 与 5 份 `except_post_20261021T*.txt`。即 66 里有 6 个是**基线残件副本**而非独立分析文字。扣除后仍有 60 个，其中 `docs/re` 10 个全部为独立分析文档，故「覆盖极密」依然成立，但**「66 个既有分析」的措辞略偏宽**，应说「66 个含该 VA 的既有文件（内含 6 份同一基线残件副本）」。这是本次唯一找到的实质内容层面的注水点，登记为 objection。

`F-TAIL 7CFE1B` 的真正既有字面命中只有 2 个（`lead/dropped611/raw/dis_007C8E17.txt`、`dis_007CA564.txt`，本会话复核），Q2 `:376-379` 已如实登记为「3 个是本轮 W9 自产物」，诚实。

---

## 4 · 旧分析 Q2 范围内有没有实质错误？

Q2 `:345-347` 判 `substantiveDefect = false` → 按 `TASK.md:88-89` 判 CONFIRMED。本会话核对：旧件 `:43` 的三条 Q2 范围内断言（入口 `0x7CFB13` / 体止 `0x7CFE1B` 唯一 ret / 275 条 / `+0x18C`）全部被 §2 的独立实跑逐字节证实，**未发现 Q2 范围内的实质错误**。

但要注意：**Q4_RELATION.md:179-201 对同一份旧分析判了 REFUTED**，理由是旧分析 §0/§1.2/§4 把这份 EXCEPT 件当作「真实发生于 13:52 那趟的异常」来定谳机制。这与 Q2 的 CONFIRMED 不矛盾：Q2 的范围被明确限定在函数归属（`:349-353`、`:365-367`、`:371` 均把机制/语义/Q4 列为「未验」），Q4 推翻的是**前提**而非函数归属。Q2 §6.2 明写「Q4 的二选一……本件只报告实算哈希前缀，不判定」——范围纪律正确。

**→ 在 Q2 自身判定档内，CONFIRMED 成立。**

---

## 5 · objections（默认找反例的结果）

1. **头部时间口径未交代**：`Q2_FUNCTION.md:8` `01:28:18` vs `_w9_q2_out.txt:2` `01:20:23`（差 7m55s），vs 输出文件 mtime `01:22:16`。哈希绑定不受影响，但 TASK.md:82 要求「回件时刻 = 实际时刻」，建议 W9 汇总注明「01:20:23 为探针启动、01:28:18 为正文成稿」。
2. **「`va in e.by()` ⇒ 非 call/jmp 落点」的推理不严格**：`Q2_FUNCTION.md:208` 把 `in by()=True` 括注「非 call/jmp 落点、非数据区」。`by()` 只说明该地址是重同步流中某条指令的**起始**，与「是否有分支以它为立即数目标」是两个独立命题（一个地址可以既是合法指令起始又是 jmp 落点）。Q2 探针本身也未枚举落点。本会话补跑全流立即数目标枚举：`_q2_review_counter_out.txt:1` `branch/call imm targets == 0x7CFC9F = 0 []`，`:2` 前一条指令 `0x7cfc9b ... 8B 54 F9 04` 恰好结束于 `0x7cfc9f`，才把该断言坐实。**结论正确但原论证略跳步**，应补上这条实跑。
3. **覆盖度数字是时点快照 + 6 份注水副本**：见 §3。Q2 报 80/66，复核时点 109/71，差由 Q2 探针落盘后新建的 5 个文件（`D22_RULING/*`、`PENDING_DECISIONS.md`）解释，Q2 没有算错；但 W9 汇总若直接引用「66」应标注「截至 01:22 的时点数」。另 66 个净命中里有 6 个是 EXCEPT 基线残件的逐字节副本，不是独立分析文字，`Q2_FUNCTION.md:322` 的「核心对象/密集分析」结论仍成立（扣后 60，docs/re 10 全为独立文档），但措辞应更精确。
4. **（边界，非缺陷）`func_rets` 是线性枚举非 CFG 证明**：见 §3 Q2-(2) 注。Q2 已用越界 call 检查补强，且把运行期 hook 记「未验」，口径可接受。

**未找到的反例（明确写「未找到」，不写「不存在」）**：更近的序言、区间内第二个 ret、内部 `C3` 被误判为 ret、外部直接分支落入函数体、间接 call/jmp、窗口内嵌套 `55 8B EC` 序言、EXCEPT 件字节与磁盘不符、两个 SHA256 不符、Q2 原探针不能复现 —— 在本会话实跑的口径下全部未找到。

---

## 6 · Q4 的哈希比对该不该全量？（点名检查 3）

**该全量，且本会话独立全量做了，Q4 的做法正确，Q2 不越界也正确。**

理由：`TASK.md:64-67` 把 Q4 定为「本节最关键的一问」，判据是「**是否就是那 107 份之一**」，并明写 `find + sha256sum 或 python`。单一哈希/前缀比对只能给必要条件；「107 份全部同哈希」与「这件 EXCEPT 是其中之一」是两个方向不同的命题，必须逐份算完整 64 位哈希（或逐字节比）才能排除「107 份是另一份与 EXCEPT 仅前缀相同的文件」。抽样或只看 §555 记的 `6694b75e…` 前缀都不够。

**本会话独立全量实跑**（`reviews/_q2_review_hash_out.txt`，2026-11-06 03:17:24；未采信 Q4 输出）：
```
D:\Git\usr\bin\find.exe . -path ./.git -prune -o -type f -name "except_post_*.txt" -print | wc -l
  → 113
D:\Git\usr\bin\find.exe . -path ./.git -prune -o -type f -name "except_post_*.txt" -print0 \
    | sort -z | xargs -0 sha256sum > /tmp/q2_posts_hashes.txt
  → files hashed: 113
cut -d' ' -f1 /tmp/q2_posts_hashes.txt | sort | uniq -c
  → 113 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251
matching=113   NOT_matching=0
find ... -printf "%s\n" | sort | uniq -c
  → 113 26405
```
即 **113/113 全量同哈希、distinct=1、尺寸全 26405 B**，与 `Q4_RELATION.md:25-40` 的 113/113、`_w9_q4.py:164-189` 的逐份 `sha_file` + 逐字节 `==` 实现、`_w9_q4_out.txt:47-62` 一致。Q4 的判据实现（`_w9_q4.py:271-275`：`len(same)==len(recs) and len(diff)==0` 才判 SAME-HASH，否则逐件列 DIFF）**没有用抽样代替全量**，正确。

**对 Q2 的意义**：`Q2_FUNCTION.md:41-43` 只报告「EXCEPT 件 SHA256 前缀 `6694b75e…` 与 §555 所记相同」，并明写「本件只报告这一实算哈希，不据此断言 Q4 的二选一结论」；`:371` 再列 Q4 为「未验」。本会话亲读 `lead/GOAL_THREE_TARGETS_20261018.md:5475`（`107 份 except_post_*.txt 全部同哈希 6694b75e…`）与 `:8503`（§590 已记完整 64 位），确认 Q2 没有把前缀相同误升格为结论。**这是正确的范围纪律，不是漏项**；Q4 才是承担全量比对的一方，且它做了。

> 附带核（防「查不到当不存在」）：本会话也复核了 `Q4_RELATION.md:50,64-68` 的 107 vs 113 口径差：`find` 子树 `lead/qc161_u0400_trip` 得 107、整仓 113，Q4 把 §555 的 107 判为「范围窄而非错」；本会话的全仓 113 与之一致。Q4 的 REFUTED 判定与 Q2 的 CONFIRMED 不冲突（见 §4）。

---

## 7 · 纪律与交付

- **零真机 / 零采样注入 / 零活进程读取**：本会话只跑 `sha256sum`、`grep`、`find`、`python -I -X utf8`（`hashlib` + `ra2tool.Engine` 只读磁盘镜像）、`sed`/`ls`/`git status`（只读）。未启动 gamemd/ra2loader/YURI，未写 hook/MiniDump/SuspendThread。
- **既有文件未改**：`ls -la --time-style=full-iso` 复核 `Q2_FUNCTION.md`(01:36:18)、`_w9_q2.py`(01:20:18)、`_w9_q2_out.txt`(01:22:16) 的 mtime 未变；Q2 原探针重放的 stdout 重定向到 `reviews/_q2_replay_out.txt`，未覆盖 `_w9_q2_out.txt`。`git status --porcelain -- lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/` 只显示该目录整体为 `??`（未跟踪），无既有件被改。
- **唯一写域**：本复核产出的全部文件均在 `W9_SINGLESTEP_7CFC9F/reviews/`：
  `Q2_review.md`（本件）、`_q2_review_probe.py/_out.txt`、`_q2_review_counter.py/_out.txt`、`_q2_review_cands.py/_out.txt`、`_q2_review_edges.py/_out.txt`、`_q2_review_grep_out.txt`、`_q2_review_net_out.txt`、`_q2_review_netlist.txt`、`_q2_review_hash_out.txt`、`_q2_review_cite_out.txt`、`_q2_review_bytes_out.txt`、`_q2_review_redundancy_out.txt`、`_q2_replay_out.txt`。
  （目录内另有 `_Q1_review_probe*` 三件，为并行 Q1 复核员所写，非本复核产物，未读改。）
- **独立复现 = true**：两个 SHA256、全部关键 `e.rd`/`e.disasm`/`e.by()`/`e.func_rets`、275 条连续解码、6 个序言候选、全流 xref/C3/越界分支枚举、10 种 grep 口径、整仓 113 份哈希全量比对、Q2 原探针重放 —— 全部在本会话亲自执行，未采信回件文字作为字节证据。
- **未验（不填猜）**：运行期该函数是否被 hook/改写（静态只读磁盘）；间接跳转的运行期落点；Q1/Q3/Q5 的结论；Q4 中「13:52 那趟是否另有未留存的异常」（Q4_RELATION.md:244-245 自列未验）；符号名 `__sbh_alloc_block` 与「MSVC 6.0 CRT」来源归属（Q2 `:211,365` 自列未验，本会话同意）。

---

## 8 · mustFix（给 W9 汇总件的可操作项）

1. 在汇总件的「SHA256 绑定」节注明 `Q2_FUNCTION.md:8` 的 `01:28:18` 是**正文成稿时刻**，探针运行时刻为 `_w9_q2_out.txt:2` 的 `01:20:23`（输出落盘 `01:22:16`），避免被下游误读为「探针未跑/时间造假」。
2. 在 Q2 结论的「`0x7CFC9F in e.by()`」处补一行实跑依据：全流立即数分支目标枚举 = 0（`reviews/_q2_review_counter_out.txt:1`），前一条指令 `0x7CFC9B` 结束于 `0x7CFC9F`（`:2`），把「非 call/jmp 落点」从推断升格为已证。
3. 引用 Q2 的覆盖度数字时标注「截至 2026-11-06 01:22 的时点数：原始 80 / 净 66（docs/re 10 / lead 56）」；若按复核时点则 109 / 71。并注明净 66 中含 6 份与 EXCEPT 逐字节相同的基线残件副本（`_q2_review_redundancy_out.txt`），宜表述为「66 个含该 VA 的既有文件，其中 60 个非基线副本」。
4. 汇总件引用 Q2 的 CONFIRMED 时必须带范围限定「仅函数归属」，避免与 Q4 对同一旧分析的 REFUTED（针对「异常真实发生」前提）在字面上打架；建议并排写明两者各自的前提。

> 以上 4 项均**不改变 Q2 的 CONFIRMED 判定**，属措辞/可追溯性加固；Q2 的字节证据与结论本会话全部复现通过。
