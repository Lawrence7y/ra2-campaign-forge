# MINHARD_SET_CHECK.md — 三组硬项原位状态 / 「4 件最小」 / 零边际成本 / 只批 4 件的最坏情形（校核件）

- 角色：最小硬项校核撰写员（动态工作流子代理）。日期 2026-11-09。
- 本件唯一写域 = `lead/minhard_check_20261109/`；本件与同域 `_mhz_*` 脚本/输出是本会话**唯一**写入。
- 纪律（全部遵守）：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；`lead/s604_refsync_full_20261109/`、`lead/s604_attribution_20261108/`、`lead/s604_verdict_entry_20261109/`、`lead/ledger_appendix_20261108/`、`lead/ledger_bound_20261109/`、两件台账一律只读；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib。
- 被核对象 = `lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md`（全量清单交付件，61819 B）。

---

## 1 目的与边界（只校核，不改件、不入账）

**目的**：按任务书要求，如实登记三组硬项（处8 / 处9 / #C1 / #C2 / #A3）在现盘的原位状态；核算「4 件最小」是否成立；核算「加注零边际成本」是否成立并给出**执行顺序**建议；给出 Leader **执行前必读**四分类与**只批 4 件的最坏情形**。

**边界（硬）**：

1. 本任务**只校核，不改任何既有件、不入账**。以下每一处「应当改成什么」「建议怎么排顺序」都是**建议**，不是执行，也不是已执行。§5 中凡涉及「改后」「追加后」均明确写作条件句；对上游回件里被复核指出「把建议写成完成态」的措辞（如 `_mh_MINHARD_CHECK.md:208` 的「:123 已改」），本件照记为**瑕疵**，不沿用其完成态。
2. 只读域与两台账一律不改一字；写入仅限 `lead/minhard_check_20261109/`。
3. 「引用必须追到『实跑命令+输出』或『文件:行』；拿不到写『未验』，不补造」。本会话所有事实均给出二者之一；未跑/未拿到的列在 §6「未验」。
4. 若某组硬项在现盘的实际状态与清单描述不符，**如实记为不符**，不为让「4 件最小」成立而牵强。
5. 复核 verdict 如实记；`partial` 按铁律标 **unconfirmed**（见 §6）。

**本会话实跑命令（逐条，均为 `D:/Project/ra2-campaign-forge` 下）**：

| # | 命令 | 结果 |
|---|---|---|
| 1 | `pwd && ls -la lead/minhard_check_20261109/` | 写域起始已有 `_mh_*` 20 件、`_mhv_*` 17 件（后核 `_mhz_lines2_out.txt:172-178`） |
| 2 | `python --version` + `ls -1` 五个只读目录 | Python 3.12.10；五目录文件清册在盘 |
| 3 | `git status --short -- <五只读目录 + 两台账>` ; `git log -1 --format='%h %s'` | 五目录均 `??`、两台账均 `MM`（与起始 gitStatus 快照一致）；`2657458 GOAL-3T: …` |
| 4 | `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/minhard_check_20261109/_mhz_verify.py" > "…/_mhz_verify_out.txt"` | `EXIT=0`，239 行（11 件指纹 / 三组逐字 / 块标记 / 全 lead 扫描 / 两台账 grep / 上游关键行） |
| 5 | `python -I -X utf8 "…/_mhz_blocks2.py" > "…/_mhz_blocks2_out.txt"` | 首次整仓 `os.walk(ROOT)` 超 120 s 被转后台并 `TaskStop` 终止（如实记，见 §6 未验）；改 `os.walk(lead/)` 后 `EXIT=0`，205 行 |
| 6 | `python -I -X utf8 "…/_mhz_lines2.py" > "…/_mhz_lines2_out.txt"` | `EXIT=0`，179 行（§5.2 / §4.2 / 模板槽 / 合订本顺序 / 上游回件节选） |
| 7 | `python -I -X utf8 "…/_mhz_slice.py" > "…/_mhz_slice_out.txt"` | `EXIT=0`，§607 正文段切片口径差异复算 |
| 8 | `grep -rn "ALL_UNCHANGED" lead/minhard_check_20261109/`；`grep -rn -E "verdict\|partial\|unconfirmed" _mhv_*.txt`；`grep -rn -E "33\|17 件" _mhv_final_out.txt` | `_mhv_verify_out.txt:60` = `ALL_UNCHANGED = True`；`_mhv_final_out.txt:84` = `_mhv_* 件数 = 17` |
| 9 | `timeout 90 grep -rIl … "只能判「不可复现」、不能定位当年错误步骤" .` | `GREP_DONE_EXIT=124`（超时，整仓非 `lead/` 部分**未验**） |
| 10 | `ls -1` 顶层 + `find .tmp -type f \| wc -l` | 顶层含 GLM / Qwen / `Step。**dfmodel=DeepSeek` / `.tmp`(129 文件) 等大目录，说明整仓 walk 慢的原因 |
| 11 | 收尾：`git status --short -- <七只读路径>`；`git log -1`；`python -I -X utf8 -c` 校验本件绑定行格式 | 见 §6 |

**自纠二处（如实记）**：#4 脚本的 C 段用了宽松子串匹配标记行，把描述性正文（如 `LEDGER_APPENDIX_DRAFT.md:4` 的「逐字转录」说明、`LEDGER_BOUND_VOLUME.md:115` 的抽取口径说明）误判为标记，导致 `starts/ends` 数量不等、`IN_BLOCK=None`（`_mhz_verify_out.txt:38-40,54-55,67-68,80-81,93`）。已由 #5 脚本的**锚定正则**重跑取代；本件所有 `IN_BLOCK` 结论只采 `_mhz_blocks2_out.txt:1-24`，不采 #4 的 C 段。另 `_mhz_slice.py` / `_mhz_final.py` 初版把换行计数字面量写成 `b'\\n'`（计的是反斜杠+n 而非 LF 字节），输出曾出现 `newlines=0` / `LF count=0`；已改为 `bytes([10])` 并重跑，`_mhz_final_out.txt:2` 现为 `newlines=294`、`_mhz_slice_out.txt:14` 现为 `LF count=40`，其余结论不变。

---

## 2 上游指纹（十一件）

任务书【编排方指纹】给 11 件 SHA256 / 字节数 / 行数。本会话 `python -I -X utf8 …/_mhz_verify.py` 独立 hashlib 实算（`_mhz_verify_out.txt:1-14`）：

| 件 | sha256（前 12 位 + 结论） | 字节数 | 行数口径 |
|---|---|---|---|
| `lead/s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md` | `d9b9c5acd007…` MATCH | 55331 MATCH | 换行 337 / 编排 338 |
| `lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md` | `8ccf9866ebd7…` MATCH | 61819 MATCH | 换行 365 / 编排 366 |
| `lead/s604_attribution_20261108/S604_ATTRIBUTION.md` | `8e9a606752ce…` MATCH | 27182 MATCH | 换行 195 / 编排 196 |
| `lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md` | `724102612297…` MATCH | 17272 MATCH | 换行 128 / 编排 129 |
| `lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md` | `823476680c4c…` MATCH | 30536 MATCH | 换行 266 / 编排 267 |
| `lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md` | `d5dc8f979503…` MATCH | 7703 MATCH | 换行 40 / 编排 41 |
| `lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md` | `724458d9e2fd…` MATCH | 45719 MATCH | 换行 236 / 编排 237 |
| `lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md` | `058630a1b34a…` MATCH | 18980 MATCH | 换行 82 / 编排 83 |
| `lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md` | `1e4ceb37187c…` MATCH | 36097 MATCH | 换行 170 / 编排 171 |
| `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d41…` MATCH | 759518 MATCH | 换行 9757 / 编排 9758 |
| `lead/PENDING_DECISIONS.md` | `3765eddbe96d…` MATCH | 52419 MATCH | 换行 381 / 编排 382 |

`_mhz_verify_out.txt:13` = `ALL_SHA_MATCH=True  ALL_BYTES_MATCH=True`（**11/11** 逐位一致）。任务书三组原位文本给的 `total`（LEDGER 236 / DRAFT3 40 / ATTR 195）与本会话 `splitlines()` 实算逐位相同（`_mhz_verify_out.txt:35`）；编排方 `lines` 比实际换行数大 1，**不是内容差异**（`_mhz_verify_out.txt:2-12` 每行 `lines_diff=1`）。

复核回件（`_mhv_fp_out.txt:58` = `ALL_SHA_MATCH = True   ALL_BYTES_MATCH = True`，`:60` 绑定行）独立得到同一结论。但撰写人回件 `_mh_MINHARD_CHECK.md:9` 把「11/11 逐位一致」引到 `_mh_fp_verify_out.txt:2-12`，而该文件实为 `DIFF` 且 `:13` `ALL_OK= False`（本会话读取 `_mh_fp_verify_out.txt:1,13`；`_mhv_final_out.txt:69-80` 逐行转录了 11 条 DIFF）——**引证行号不实**，【复核】① 指出属实，本件照记。

---

## 3 三组硬项逐组原位核实

三组逐字原句由本会话 #4 脚本按 1-based 行号直取，与任务书【三组硬项原位文本】`want` 值逐字比对全部 `MATCH_TASK_TEXT=True`（`_mhz_verify_out.txt:16-35`）；两对同文也实算为 `True`（`:31-32`）。以下逐字给出，**不用「已核对」概括**。

### 3.1 组① 处8 ≡ 处9（`LEDGER_APPENDIX_DRAFT.md:123` ≡ `_la_draft3_s604_gapdiff.md:25`）

两行逐字相同（`_mhz_verify_out.txt:17-20,31`），原句：

```
- **边界（如实）**：§604 内联生成脚本未落盘（:9751-9755 两次自认），**只能判「不可复现」、不能定位当年错误步骤**；§603 项（:9673/:9680 ratio_max=0.9831 等）未核；本节只登记复算事实与可引用边界，**台账 :9704-9729 原文是否修订由台账所有者裁决**。
```

**是否真过时：是**，逐条依据：
- `lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md:22`（逐字）：「其边界句「只能判『不可复现』、不能定位当年错误步骤」（:123）**自本节起不再成立**——错误步骤已定位（dur 字典错位），该句属被本节取代的过时表述」；同件 `:15` 定谳本体、`:46-48` 判「需要补充（最小修订一处），不是整体修订」、`:69-70` 给出改前/改后逐字文本。
- `lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md:107`（§4.2 #14）：「『不能定位』过时（最小修订建议见 §5.2(c)）」；`:151` 给出同款改文。
- `lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md:307`：「**硬度最高（入账污染）**」。

**「随段进永久台账」理由是否成立：成立，但须限定为「待入账正文块内」，不是「已进台账」**：
- `LEDGER_APPENDIX_DRAFT.md:110`/`:125` = 「草案正文 3 逐字转录开始/结束」注释行，`:123` 在块内；`_la_draft3_s604_gapdiff.md:11`/`:28` = 「↓↓↓ 草案正文（从这里开始整段复制）」/「草案正文结束」，`:25` 在块内。本会话锚定正则实算 `blocks=[(46,61),(80,92),(110,125),(149,179)]` 与 `[(11,28)]`，两处 `IN_BLOCK=True`（`_mhz_blocks2_out.txt:2-3,5-6`）。
- `LEDGER_APPENDIX_DRAFT.md:11`（逐字）：「四段『草案正文』（暂编 §605–§608），建议均**整段追加**于 `lead/GOAL_THREE_TARGETS_20261018.md` … 之后」；`:31`「追加时无需再编辑正文本身」；`:4` 自述「本文件是草案汇编，**不是台账、不入台账**；台账只由 Leader 追加」；`:209`「**任何一笔在 Leader 整段复制追加进台账之前，都不构成台账内容**」。`_la_draft3_s604_gapdiff.md:1,4` 同类自述。
- 本会话 `_mhz_verify_out.txt:118-120`：对两台账跑 `§60[5-9]|§610|码形定谳|dur 字典|512655` → **两台账各 0 命中**；`LEDGER_BOUND_VOLUME.md:83-85` 在案同结论。⇒ 5 笔**全部尚未入账**，污染发生在 Leader 动笔追加时，现在改仍来得及（但该结论的前提见 §5 执行顺序）。
- §607 正文段身份：`:13-26` / `:111-124` / 合订本 `:184-197` / `:117-130` 四份逐字相同，本会话实算四段同哈希 `2d795bebe3cc2ec47ece6fe178876d3f3f8b3f5f1cf5dbaac655671db3737ffd`（`_mhz_blocks2_out.txt:38-42`）。口径说明见 §6 未验第 7 条。

### 3.2 组② #C1 ≡ #C2（`LEDGER_APPENDIX_DRAFT.md:215` ≡ `_lad_tpl.md:151`）

两行逐字相同（`_mhz_verify_out.txt:21-24,32`），原句：

```
3. §604 当年内联脚本未落盘（台账 :9751-9755 两次自认）——只能判「不可复现」，不能定位当年错误步骤；§603 项（:9673/:9680 ratio_max=0.9831 等）未核。
```

**是否真过时：是**：`S604_VERDICT_ENTRY_DRAFT.md:108`（§4.2 #15）「批级未验项 3 同款过时句」；`S604_REFSYNC_FULL.md:126-127` 给出改文与硬度更正。

**「随段进永久台账」理由是否成立：不成立 —— 与清单背景描述不符，如实记为不符**：
- `:215` 落在 `LEDGER_APPENDIX_DRAFT.md:211` 起的 **§6.3 未验项（全批汇总）**，四段逐字转录区块止于 `:179`（本会话 `blocks` 见 `_mhz_blocks2_out.txt:2`）；`_lad_tpl.md:151` 落在 `:147` 起 §6.3，四段区块止于 `:115`（`:87-89` 是 `__DRAFT3__` 占位符）。本会话实算两者 `IN_BLOCK=False`（`_mhz_blocks2_out.txt:4,8`）；复核回件 `_mhv_blocks3_out.txt:9,17` 同判。
- 清单**自己承认**：`S604_REFSYNC_FULL.md:126`「R6 实跑证明 §6.3（`:211-218`）在四段待追加区块（止于 `:179`）之外 ⇒ `:215` **不在**待追加正文内，**不会随笔3 整段进永久台账** …（属**草案自洽硬项，非入账污染**）」；`:308` 同判「非入账污染」。
- `S604_REFSYNC_FULL.md:126,338-339` 已把「构建脚本重建会回退」降为**未验推断**；本会话 `_mhz_blocks2_out.txt:198` 实算 `lead/ledger_appendix_20261108/_lad_build.py exists=False`（注意：`lead/ledger_bound_20261109/_lb_build.py exists=True`，是另一写域的另一脚本，`:199`）。
- **真实硬度**只剩「:123 若改而 :215 未改的同件自相矛盾 + 两件逐字同文」，`S604_REFSYNC_FULL.md:308` 自定「硬度次高（草案自洽硬项）」。

### 3.3 组③ #A3（`S604_ATTRIBUTION.md:171`，单点）

原句（与任务书 `ATTR_171` 给值逐字一致，`_mhz_verify_out.txt:25-26`）：

```
3. **无法归属（缺口，还差什么）**：**确切错误机理无法归属**——§604 空档列当年内联脚本体未落盘（台账 :9751 自述；:9752-9755 仅自认两次已改正的错误），N-8 侧 `_n8_variants2.py` 亦未落盘（`SLOW_WINDOW_LIMITS.md:92`），故「实现 bug / 誊写错 / 未测奇异口径」三选一**不可定谳**。要补齐需：当年内联脚本的落盘副本，或含空档列中间值的等价产物；在此之前本归属止于「数字错误」这一事实类。
```

**是否真过时：是**：`S604_VERDICT_ENTRY_DRAFT.md:101`（§4.2 #8）「◆「确切错误机理无法归属…三选一不可定谳。要补齐需：当年内联脚本的落盘副本」——**已闭合为「实现 bug」**；「落盘副本」以 CLI 会话存档形式满足」；`_ve_DRAFT_S609.md:22`(2)「已由本定谳闭合为「实现 bug（脚本码形错误）、非誊写」」。

**「随段进永久台账」理由是否成立：完全不适用 —— 与清单背景描述不符，如实记为不符**：
- `S604_ATTRIBUTION.md:1` 自题「归属裁定（**撰写终件**）」，是历史结论件、非待入账草案；全件**无任何逐字转录块**，本会话实算 `blocks=[]`、`IN_BLOCK=False`（`_mhz_blocks2_out.txt:9-10`）。
- 清单自定硬度为「**假开口**」而非入账污染（`S604_REFSYNC_FULL.md:309`），并**自给降级出口**：`:85`「本处判『改』为**建议**；若台账所有者坚持终件历史记录一字不动，可**降级为同文案行尾加注**——届时该处不再计入『必须改』硬项」；`:309`「则本组从『必须改』移出，最小硬项集降为 **2 组**」。同一件 `:238` 三选一分布表却把 #A3 计入「改 3」——这是**清单内部软性矛盾**，非本件推断。

### 3.4 三组硬度汇总

| 组 | 逐字原句 | 过时 | 「随整段进永久台账」 | 现盘真实硬度 |
|---|---|---|---|---|
| ① 处8≡处9 | 两件逐字同文 ✓ | ✓ `_ve_DRAFT_S609.md:22`、`S604_VERDICT_ENTRY_DRAFT.md:107` | **成立（待入账正文块内）** | 入账污染，最高；§609 同批入账则两节互斥 |
| ② #C1≡#C2 | 两件逐字同文 ✓ | ✓ `S604_VERDICT_ENTRY_DRAFT.md:108` | **不成立**（`IN_BLOCK=False`；清单 `:126/:308` 自认） | 草案自洽，次；可降级 |
| ③ #A3 | 单点 ✓ | ✓ `S604_VERDICT_ENTRY_DRAFT.md:101` | **完全不适用**（`blocks=[]`，历史终件） | 假开口，且清单 `:85/:309` 明示可降级加注 |

**不符登记**：任务书背景把三组并列为「必须处理、不能靠加注吸收」并把组①的「会随整段进永久台账」推广为三组共性；现盘实际只有组①满足，组② 清单自己判「非入账污染」，组③ 清单自己允许降级为加注。**照记不符，不牵强**。

---

## 4 「4 件最小」核算

### 4.1 三组落在几件（去重）

`_mh_final_out.txt:10-14`（撰写人实算）与 `S604_REFSYNC_FULL.md:319`（清单逐件列出）一致，并集 = **4 件**：

1. `lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md`（:123 + :215，同件一遍）
2. `lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md`（:25）
3. `lead/ledger_appendix_20261108/_lad_tpl.md`（:151）
4. `lead/s604_attribution_20261108/S604_ATTRIBUTION.md`（:171，顺手并 处5 `:136`）

⇒ **在「三组全算必须改」这个前提下，「4」的算术本身对**（`S604_REFSYNC_FULL.md:319`），13 − 4 = **9 次**节省（`S604_REFSYNC_FULL.md:320`）也不错。**错的是前提**：组②、组③按现盘不该算入「不能靠加注吸收」（§3.2/§3.3）。

### 4.2 独立找漏项（本会话实跑，不沿用撰写人结论）

**(a) 全 lead/ 逐字同文扫描**：`python -I -X utf8 …/_mhz_blocks2.py` 扫 `D:\Project\ra2-campaign-forge\lead`，`files_scanned=5396`，组①边界句**整行精确命中 9 处**（`_mhz_blocks2_out.txt:26-36`；另 #4 脚本 `lead/` 5381 件亦 9 命中，`_mhz_verify_out.txt:106-116`）：

| 命中点 | `IN_BLOCK`（锚定正则实算） | 性质 |
|---|---|---|
| `LEDGER_APPENDIX_DRAFT.md:123` | **True** | 组① 原件 |
| `_la_draft3_s604_gapdiff.md:25` | **True** | 组① 单件版 |
| `LEDGER_BOUND_VOLUME.md:196` | **True**（块 `:181-200`） | **漏项**：2026-11-09 另一写域合订本 |
| `_lb_BOUND_VOLUME.md:129` | **True**（块 `:114-133`） | **漏项**：同式合订本单件版 |
| `_dnv_sandbox36/…/LEDGER_APPENDIX_DRAFT.md:123` | **True** | sandbox 副本，效力未判（§6 未验 5） |
| `_dnw_sandbox/…/LEDGER_APPENDIX_DRAFT.md:123` | **True** | sandbox 副本，效力未判 |
| `S604_REFSYNC_DRAFT.md:102` | False（`blocks=[]`） | 分析件引文，非可追加块 |
| `_rs_REFSYNC_DRAFT.md:131` / `:144` | False | 分析件引文 |

`_mhz_blocks2_out.txt:1-24` 逐件给出块配对与 `IN_BLOCK`。**清单 43 处扫描口径是「13 件」（`S604_VERDICT_ENTRY_DRAFT.md:90`：「按 file:line 严数 = 13 件 43 处」）**，漏了 `lead/ledger_bound_20261109/` 这两份「可整段复制追加、草案正文逐字照抄已验」的第三、第四份 §607 载体：`LEDGER_BOUND_VOLUME.md:3`「不是台账、不入台账」、`:10`「草案正文 5 段全部**逐字照抄**…ALL_VERBATIM = True」、`:28` 登记笔 3 出处 `_la_draft3_s604_gapdiff.md:13-26`（即含 `:25`）、`:34`「5 笔状态**全部「未入账、可整段复制追加、草案正文逐字照抄已验」**」。若 Leader 从合订本复制，错句照样进**永久台账**，机理与组①完全相同。

**(b) 连带漏项：改 `:25` 后即失效的指纹登记面**（本会话 `_mhz_blocks2_out.txt:44-78`，按 `d5dc8f97…/7703` 与 `e9842d41…/4894` 全 lead/ grep）：`LEDGER_BOUND_VOLUME.md:65,105,177,202,203,372`；`_lb2_TEMPLATE.md:65,105,150,160,161,286`；`_lb_BOUND_VOLUME.md:111,135,136,256`；以及**撰写人未计入 N 的** `_lb_build.py:37`、`_lb_VERIFY.md:32`、`_lb_fp_out.txt:5,16`、`_lbv_final.py:76`、`_lbv_fp.py:12`、`_lbv_verbatim.py:83`、`_lb_verify_print.py:34`（【复核】③ 亦点名前四者，`_mhv_blocks3_out.txt:59-83`）。另 `_lb2_TEMPLATE.md:154-158` 为 `@@BODY_3@@` 占位符（`_mhz_lines2_out.txt:98-102`），模板本身不含字面错句，但登记值失效。

**(c) 13 件内清单未登记的同类过时句 / 连带项**（本会话 `_mhz_blocks2_out.txt:186-195`）：
- `lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md:127` 逐字：「`1. §604 空档列的**真实生成代码**——语料与台账均不存在（:9751 只记「内联脚本，见本轮台账」；:9752-9755 只记两次自认错误），只能判「不可复现」，不能定位错在哪一步。`」——§4.2 对该件只列 `:91`（`S604_VERDICT_ENTRY_DRAFT.md:121`），`:127` 不在 43 处内。
- `S604_ATTRIBUTION.md:136` ≡ `_sa_ATTRIBUTION_S604.md:90`，本会话实算 `True`（`_mhz_blocks2_out.txt:190-195`）；`S604_REFSYNC_DRAFT.md:95` 自认「**不在**定谳交付件 §4.2 的 43 处清单内」，须由编排方裁决登记方式。

### 4.3 加 S609 定谳本身，件数是否变

- **历史改件数不变**：`_ve_DRAFT_S609.md:1`「供 Leader 整段复制追加；**本文件本身不是台账，不入台账**」；`S604_REFSYNC_FULL.md:251` 已把「A 批 GOAL 台账 §609 正文追加」单列、`:275`「加批次 A 台账追加 **1 次** ⇒ 全链 14 次」、`:319`「4 次历史件指纹变更（**+ A 台账 1 次**）」。⇒ 加 §609 不改「历史改件数」，全链 = N + 1。本会话 `_mhz_verify_out.txt:118-120` 两台账 0 命中，5 笔全部未入账。【复核】⑤ 确认此点成立。
- **但组① 硬度再升一级**：`_ve_DRAFT_S609.md:22` 与 `S604_VERDICT_ENTRY_DRAFT.md:79` 都在**会进台账的 §609 正文里**写「:123 边界句自本节起不再成立」（本会话 `_mhz_blocks2_out.txt:171-184` 逐件命中该关系句的副本，含两件合订本 `:270`/`:201` 与模板 `:184`）。若 §609 入账而 :123/:25（及两件合订本）未改，GOAL 台账内 §607 与 §609 直接互斥。
- **执行顺序上有冲突必须记明**：撰写人建议「先 A 批追加 §609」（`_mh_MINHARD_CHECK.md:183`），但 `LEDGER_BOUND_VOLUME.md:46` 把「笔3 §607 ↔ 第五笔 §609」列为「**唯一「建议成组」的一对**」（`_mhz_lines2_out.txt:108-119`），`_lb_BOUND_VOLUME.md:295` 明写「若 §609 先于笔3 入账…**叙述自洽性**上宜笔3 在先、§609 在后（或同批并明确两节互引）」（`:120-127`），且撰写人自己 `:279` 也自批「分批处理正好拆散这一对」。【复核】⑤ 据此指出「现在改仍来得及」缺「§607 载体须先修」的明示前提 —— 属实，本件在 §5 执行顺序中补上。

### 4.4 判定：「4 件最小」**不成立**（方向经【复核】④ 确认）

分口径如实给数，**不牵强**：

| 口径 | 最少件数 | 依据 |
|---|---|---|
| A. 严格交集（「随段进永久台账」∩「已定谳但表述旧」），**13 件内** | **2 件**：`LEDGER_APPENDIX_DRAFT.md`、`_la_draft3_s604_gapdiff.md` | `_mh_MINHARD_CHECK.md:155`；只有组① 命中 |
| A′. 同上交集，**全 lead/ 实盘**（本会话独立扫） | **6 件** `IN_BLOCK=True`：上述 2 件 + `LEDGER_BOUND_VOLUME.md` + `_lb_BOUND_VOLUME.md` + 2 件 sandbox 副本 | `_mhz_blocks2_out.txt:3,6,12,14,17,19`；【复核】③ 亦指出「严格交集回件答 2 件只在其自己批判的『13 件内』口径成立，全仓实盘至少 6 件」 |
| B. 清单三组 + 清单自认的 #A3 降级分支 | **3 件**（若连降级加注都不做则 2 件；清单自述「降为 2 组」） | `S604_REFSYNC_FULL.md:85,309` |
| C. 撰写人推荐「Leader 动笔前不留会进台账的过时表述 + 不留失效登记」 | **6 件**（4 件 + 两件合订本）；+ 模板指纹登记 = 7；+ 处5 连带 `_sa:90` = 8 | `_mh_MINHARD_CHECK.md:157`、`_mh_final_out.txt:25,32` |
| C′. 按 C 口径**自身**严格剔除组②/③（撰写人自己判二者不进台账、可降级） | **4 件**：`LEDGER_APPENDIX_DRAFT.md`、`_la_draft3_s604_gapdiff.md`、`LEDGER_BOUND_VOLUME.md`、`_lb_BOUND_VOLUME.md`；+ 模板 = 5；+ `_sa:90` = 6；再计 §4.2(b) 的脚本/输出登记件则更多 | 【复核】④「推荐 6 件 … 其中 `_lad_tpl.md`、`S604_ATTRIBUTION.md` 回件自己判不会进台账、可降级，按其口径 C 不该计入最小集」 |

**差在哪**：一是把两组硬度理由抬高（组② 清单自认「非入账污染」、组③ 历史终件且可降级加注）；二是 43 处扫描口径 = 13 件（`S604_VERDICT_ENTRY_DRAFT.md:90`），漏掉 `lead/ledger_bound_20261109/` 里同一段 §607 正文的第三、第四份可整段复制载体及其指纹登记件；另有 13 件内未登记的同类过时句 `SLOW_WINDOW_LIMITS.md:127`。因此「省 9 次」也不可靠：按 C=6 为 13−6=7，C=7 为 6，C=8 为 5；按 C′=4 反而仍是 9 —— **节省次数随口径漂移，不是稳定结论**。

补充如实登记：撰写人 `what` 申报「产出 …（21 件）」，本会话实算 `_mh_*` 为 **20 件**（`_mhz_lines2_out.txt:172-174`、`_mhv_final_out.txt:83`），申报数不实；【复核】④ 指出属实。另 `_mh_MINHARD_CHECK.md:9` 的「11/11 MATCH」引证行号不实（§2 末）、`:208` 把建议写成完成态「:123 已改」（【复核】⑦）—— 均照记，不掩盖。

---

## 5 「加注零边际成本」前提分析、执行顺序、Leader 必读四分类、只批 4 件的最坏情形

### 5.1 清单原句与三个前提

清单原句：`S604_REFSYNC_FULL.md:322`（`_mhz_lines2_out.txt:41`）「**建议**：取全量方案——**22 处加注并入各件既定单遍，边际指纹成本为零**，却使 9 个件的读者免于自行对照修读层」；`:247`「按件分组：同件一遍完成 = 一次指纹变更」；`:267`「零新增遍、直接并入既有遍」；`:68`「节号联动：若 … 节号变 §608，全部注文『（暂编 §609）』**全局替换**」。

「零边际成本」成立须三条前提同时满足（`_mh_MINHARD_CHECK.md:169-172`）：① 同一次写入同时落「改点 + 加注 + 保留」（每件只一遍）；② 该件本来就会被触达（否则加注就是净新增指纹）；③ 节号已先钉死（否则注文要二次全局替换）。

**结论：三前提分析正确，但「零边际成本」只对「已决定执行全量 13 件」成立** —— 撰写人自己 `_mh_MINHARD_CHECK.md:179` 承认「『零边际成本』只在『已决定执行全量 13 件』这个前提下成立」，【复核】⑥ 亦如此判定。对「4 件最小」基线，加注**不是**零边际，反而是被省掉那 9 次变更的主要来源：本批 22 条加注中 **7 点**落在原 13 处已触达的 3 件、**15 点**落在 6 个从未触达的新件（`_mh_final_out.txt:34-46`）。若分「先改点、后加注」两批执行，同时含改点与加注的件会产生两次写入、两次指纹变更，且 §3.1 前提③必被触发（33 条注文的「（暂编 §609）」需二次替换）；`S604_REFSYNC_FULL.md:278` 还实跑证实 errata 级联面被既有草案低估（五件旧指纹已被 `PENDING_DECISIONS.md:26`、`RULING_DIRECTION.md:56`、`S604_EXCLUSIVITY.md:27`、`_exw_verify.py:46`、`_ow_raw_hits.json` 等第三方登记）。

### 5.2 执行顺序建议（含对上游建议的更正）

1. **先裁四件前置**（Leader 职权，本任务不代裁）：① §609 最终节号（零重排 §609 / 相邻 §608，`_ve_DRAFT_S609.md:66-67`、`S604_VERDICT_ENTRY_DRAFT.md:148`）；② #A3 取「改」还是降级「同文案行尾加注」（`S604_REFSYNC_FULL.md:85,309`）；③ `_sa:90` 连带是否采纳（`S604_REFSYNC_DRAFT.md:95`）；④ 两件合订本与模板是否纳入本批、sandbox 两件副本如何处理（§6 未验 5）。
2. **先修 §607 载体，再追加 §609**（**更正撰写人 §3.3 的「先 A 批」**）：按 `LEDGER_BOUND_VOLUME.md:46`、`_lb_BOUND_VOLUME.md:295` 与撰写人自己 `:279`，「笔3 ↔ 第五笔」是唯一建议成组的一对，宜 **§607 在先、§609 在后，或同批并明确两节互引**；至少须在 §609 入账前把四处可复制载体（:123 / :25 / 合订本 :196 / :129）的边界句改定，否则 §609 正文「:123 自本节起不再成立」指向台账内仍存在的旧句，GOAL 内两节互斥。
3. **钉死节号后，改文一次成型**：所有改文与注文按最终节号一次写对，不得事后「（暂编 §609）」全局替换（`S604_REFSYNC_FULL.md:68`）。
4. **按件单遍**：每件「改 + 加注」合并为**一次写入**（`S604_REFSYNC_FULL.md:249-262` 的 A→B→C-①…C-⑥ 内每遍只写一次）；B 批一次写完 `LEDGER_APPENDIX_DRAFT.md`(:123+:215) / `_la_draft3`(:25) / `_lad_tpl`(:151) / 两件合订本(:196/:129 + 其指纹登记行)。
5. **单遍即封 + 验收**：每遍写完立刻 hashlib 复算新 SHA/字节并登记 errata，之后不重开该件。验收须覆盖：① 逐件「件数 = 指纹变更次数」；② `grep -rn "不能定位当年错误步骤"` 在**全部待入账正文块内** 0 命中（含两件合订本与 sandbox 副本）；③ `grep -rn "（暂编 §609）"` 与最终节号一致；④ **§4.2(b) 的旧指纹登记面同批复核**（【复核】⑥ 指出撰写人 `_mh_MINHARD_CHECK.md:187` 的验收只写「件数=指纹变更次数」，未覆盖 `:176/:277` 点名的 errata 级联写入）；⑤ 两件台账 `git status` 只有 A 批那一次追加；⑥ 合订本 `ALL_VERBATIM`（`LEDGER_BOUND_VOLUME.md:10`）在新正文下重新成立。

### 5.3 Leader 执行前必读四分类（**均为建议，本任务不执行**）

**(一) 必改 / 不能靠加注吸收**
- 严格组① 四份可整段复制载体：`LEDGER_APPENDIX_DRAFT.md:123`、`_la_draft3_s604_gapdiff.md:25`、`LEDGER_BOUND_VOLUME.md:196`、`_lb_BOUND_VOLUME.md:129`（后两件为清单漏项）。四者改文须**同批逐字同文**。建议改文逐字见 `_ve_DRAFT_S609.md:69-70` = `S604_VERDICT_ENTRY_DRAFT.md:151`：
  ```
  §604 内联生成脚本未落盘（:9751-9755 两次自认；2026-11-09 更新：脚本本体已得于 CLI 会话存档，错误步骤已定谳为 dur 字典推导错位，见码形定谳节——本句「不能定位」自该节起不再成立，本节复算数字与订正清单不受影响），当时**只能判「不可复现」**；
  ```
- 失效指纹登记面（§4.2(b)）：改 `:25` 后 `d5dc8f97…/7703` 与 `e9842d41…/4894` 全部失效，须同批改为改后实算值或标 errata。
- **条件必改（可降级，须 Leader 先裁）**：#C1/:215、#C2/:151（改文见 `S604_REFSYNC_FULL.md:127`，硬度只是草案自洽）；#A3/:171（改文见 `S604_REFSYNC_FULL.md:86`，可按 `:85/:309` 降级为行尾加注）。按 C′ 口径这三者**不该计入最小集**。

**(二) 可加注**
- 全 43 点合并 = 改 6 / 加注 33 / 保留 4（`S604_REFSYNC_FULL.md:62`）；本批 28 处 = 改 3 / 加注 22 / 保留 3（`:238`）。统一注格式见 `S604_REFSYNC_FULL.md:68`，逐条文案见该件 §3 与 `S604_REFSYNC_DRAFT.md:74-291`。
- 清单外同类句须补裁：`SLOW_WINDOW_LIMITS.md:127`（`_mhz_blocks2_out.txt:188`）、`S604_ATTRIBUTION.md:169`、`_sa_ATTRIBUTION_S604.md:90`（与 `ATTRIBUTION:136` 逐字同文，本会话实算 True）。
- 加注必须并入该件**同一次写入**才有零边际；否则按 §5.1 结论不成立。

**(三) 可保留**
- `S604_SCRIPT_GAP.md:55/:56/:57`（#D2–D4）：三条是对 `GAP_RECHECK:101/:153`、`SLOW_WINDOW_LIMITS:91` 的**逐字引文**，改/注引文会混淆引文边界（`S604_REFSYNC_FULL.md:142-155,313`）。
- `S604_EXCLUSIVITY.md:206`（处14）：实测事实陈述，定谳后逐字仍真（`S604_REFSYNC_FULL.md:314`）。
- 定谳交付件 `:127` 的四条「不失效附注」：`S604_ATTRIBUTION.md:14`、`S604_SCRIPT_GAP.md:131`、`S604_EXCLUSIVITY.md:101`、`SLOW_WINDOW_LIMITS.md:92`。
- 理论保留选项（`S604_REFSYNC_FULL.md:315`）：若台账所有者明示「§609 关系节 + §4.2 为权威修读层、13 件全部零动作」，除三组外 25 处可全不动而自洽；代价由修读层承担。**注意**：按本件 §4 判定，该选项若不含两件合订本仍会留入账污染。

**(四) 执行顺序与验收**
即 §5.2 五步。要点：先裁前置 → **先修 §607 四载体**（或同批）→ 钉节号 → 改文一次成型 → 按件单遍 → 单遍即封 → 六项验收（含 errata 级联与合订本 `ALL_VERBATIM` 重验）。

### 5.4 只批 4 件的最坏情形

按「只批清单三组那 4 件」执行，且 §609 同批或随后入账，最坏会发生：

1. **错句仍会进永久台账**：`LEDGER_BOUND_VOLUME.md:196` 与 `_lb_BOUND_VOLUME.md:129` 与 :123 逐字相同（本会话 `_mhz_blocks2_out.txt:12,14,33-34`），各在「#### ↓↓↓ 草案正文（逐字照抄，从下一行起）」块 `:181-200` / `:114-133` 内；合订本 `:34` 自述 5 笔「未入账、**可整段复制追加**、草案正文逐字照抄已验」。改了源件却漏了另两份同样可入账的载体 —— 这是最坏的一条。
2. **GOAL 台账内两节互斥**：§609 正文（_ve_DRAFT_S609.md:22 / S604_VERDICT_ENTRY_DRAFT.md:79，及合订本 `:270`/`:201` 副本）明写 :123 边界句「自本节起不再成立」，而 §607 仍写「不能定位当年错误步骤」，一节否证另一节。
3. **失效指纹登记 + 自证失真**：`_lb2_TEMPLATE.md:150,160,161`、两件合订本 `:65,105,177,202,203,372` / `:111,135,136,256`、以及 `_lb_build.py:37`、`_lb_VERIFY.md:32`、`_lb_fp_out.txt:5,16` 仍登记旧 `d5dc8f97…/7703` 与 `e9842d41…/4894`；`LEDGER_BOUND_VOLUME.md:10` 的「ALL_VERBATIM = True」随正文被改而失真。
4. **叙述自洽破裂**：`LEDGER_BOUND_VOLUME.md:46` 把「笔3 ↔ 第五笔」列为唯一建议成组的一对；只批 4 件且先追加 §609 正好拆散这一对（撰写人自己 `:279` 亦自批）。
5. **#A3 假开口与连带项无人处理**：若按 `S604_REFSYNC_FULL.md:85` 把 #A3 降为加注，4 件里少一件实质修复；若不降级而改，终件仍留 `:169` 同类名与 `_sa_ATTRIBUTION_S604.md:90` 逐字同文未同步（`_mhz_blocks2_out.txt:190-195`）。
6. **33 处加注 + 4 处保留全部不落**：9 个件（`GAP_RECHECK`、`_sa`、`SCRIPT_GAP`、`_sg`、`EXCLUSIVITY`、`_ex`、`SLOW_WINDOW`、`RULING_DIRECTION`、`_dr_RULING`）读者须自行对照修读层（`S604_REFSYNC_FULL.md:315`）；`SLOW_WINDOW_LIMITS.md:127` 等 43 清单外过时句亦无人处理。
7. **节号联动风险**：若采相邻方案变 §608，全部注文「（暂编 §609）」错误，且 `S604_VERDICT_ENTRY_DRAFT.md:148` 点名汇总表 `:204-207`、`:11`、`:222` 约 4 处编号引用需同步改。
8. **纠正代价升级**：一旦台账正文已固化，改 §607 属改台账正文（授权层级更高，`_ve_DRAFT_S609.md:24`「一律留台账所有者裁决，本节不代判、不代改」）；须重开批次、每件第二次指纹变更（违反 `S604_REFSYNC_FULL.md:247`「同件一遍」）；errata 级联面 `:278` 已实跑证实被低估且 `:358` 自认「未逐一枚举全部登记文件」；`S604_REFSYNC_FULL.md:356` 自认「28 处全量反链 grep 未做」；两件 sandbox 副本（`_mhz_blocks2_out.txt:17-19`）也是 43 清单外同文命中点，须一并核。

---

## 6 复核回件（绑定行）+ 未改既有件声明 + 未验项

### 6.1 绑定行（被核对象 = `lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md`）

被核对象 SHA256 = 8ccf9866ebd7860f03d71e939960e018fd0cfbbe6b94add04dd50f7004c11ac5，字节数 = 61819

本会话 `python -I -X utf8 …/_mhz_verify.py` 用 hashlib 实算（`_mhz_verify_out.txt:3,13,14`），与任务书【编排方指纹】给值、【校核】与【复核】的 `sha256Line` 逐位一致。格式按铁律：`被核对象 SHA256 = ` 紧跟完整 64 位十六进制、中间不插任何路径/括号/星号/反引号/空格，随后 `，字节数 = ` 再写数字。

### 6.2 复核 verdict 如实登记

- **【复核】verdict = `partial`**（任务书【复核】原值：`"verdict":"partial"`，`ranCommands:33`）。按铁律「refuted 或 partial 标 unconfirmed」⇒ **本交付件整体登记为 `unconfirmed`**，最终效力由编排方与台账所有者裁决。
- 上游另有两处同源 `partial` 如实并记：`S604_REFSYNC_FULL.md:292`「**复核 verdict = partial**（任务书【复核】原样转录）⇒ … **本交付件整体登记为 unconfirmed**」；`LEDGER_BOUND_VOLUME.md:34`「第 5 笔 §609 状态 **unconfirmed**（复核 verdict = partial）」。
- **未标 refuted**：【复核】`whatBreaksIt` 明确「三组原句自取与回件引文逐字 True、行号无错指（_mhv_quotes_out.txt:28-43），不报 refuted」「11/11 指纹独立 hashlib 复算 MATCH」「『4 件不成立』方向确认」「无越界」。本会话独立复算亦全部支持（§2、§3、§4）。

### 6.3 【复核】`whatBreaksIt` 七项，逐项如实转录 + 本会话可复核状态

| 项 | 【复核】结论 | 本会话核对 |
|---|---|---|
| ① | 11/11 指纹 MATCH（`_mhv_fp_out.txt:58`）；`lines` 差 1 属换行口径；回件把 `_mh_fp_verify_out.txt:2-12` 称「11/11 MATCH」，实为 `DIFF`/`ALL_OK=False`（`_mhv_final_out.txt:69-80`） | 属实：`_mhz_verify_out.txt:13` 11/11 MATCH；`_mh_fp_verify_out.txt:13` `ALL_OK= False` 已读 |
| ② | 三组原句自取与回件引文逐字 True、行号无错指，**不报 refuted** | 属实：`_mhz_verify_out.txt:17-35` |
| ③ | 独立全仓扫 50614 件得边界句 9 命中，与回件一致；组② `IN_BLOCK=False`、组③ 无块，确认不符；但严格交集「2 件」只在 13 件口径成立，全仓实盘至少 6 件（含 2 件 sandbox `IN_BLOCK=True`）；另多找出 `_lb_build.py:37`、`_lb_VERIFY.md:32`、`_lb_fp_out.txt:5,16` 及模板/合订本多处失效登记 | 本会话 `lead/` 5396 件亦 9 命中（`_mhz_blocks2_out.txt:27-36`）；6 件 `IN_BLOCK=True`（`:3,6,12,14,17,19`）；失效登记面见 `:44-78`，与【复核】一致。**全仓非 `lead/` 部分未验**（§6 未验 6） |
| ④ | 「4 件不成立」方向确认，但推荐 6 件含 `_lad_tpl.md`、`S604_ATTRIBUTION.md`（回件自己判不会进台账、可降级），按其口径 C 不该计入；`what` 称「21 件」实盘 `_mh_*` 为 20 件 | 属实：`_mhz_lines2_out.txt:173` `_mh_ count=20`；本件 §4.4 补 C′ 口径 |
| ⑤ | §609 加进来历史改件数不变成立；漏洞：回件 §3.3 建议先追加 §609 与合订本 `:46`「唯一建议成组」及回件 `:279` 自批冲突，「现在改仍来得及」缺「§607 载体须先修」的明示前提 | 属实：`_mhz_lines2_out.txt:108-127`；本件 §4.3 / §5.2 已补前提并更正顺序 |
| ⑥ | 零边际三前提分析正确但只对全量 13 件成立（回件 `:179` 自认）；A 批先钉节号与 `:279` 自相矛盾；`:187` 验收「件数=指纹变更次数」未覆盖 `:176/:277` 点名的 errata 级联写入 | 属实；本件 §5.1 / §5.2 第 5 步补 errata 验收 |
| ⑦ | 无越界：9 件收尾复算 `ALL_UNCHANGED=True`、`git status/log` 与起始一致、未 commit/push；但 `:208`「(:123 已改)」把建议写成完成态，`:9` 的 MATCH 引证行号不实 | 属实：`_mhv_verify_out.txt:60` = `ALL_UNCHANGED = True`（本会话 #8 实跑取得）；两处措辞瑕疵本件 §1/§2/§4.4 均照记 |

【复核】另自述「我本人只写 `_mhv_*`（17 件），全部 `python -I -X utf8` + 绝对路径、hashlib；`_mhv_blocks.py` 曾因 D:/ 路径解析异常失败，已由 `_mhv_blocks3.py` 成功复跑替代」—— 本会话实算 `_mhv_*` = **17 件**（`_mhv_final_out.txt:84`、`_mhz_lines2_out.txt:175-176`），一致。

### 6.4 未改任何既有件 / 未入账 / 未 commit / 未 push 声明

- 本会话**未写入**任何只读域：`lead/s604_refsync_full_20261109/`、`lead/s604_attribution_20261108/`、`lead/s604_verdict_entry_20261109/`、`lead/ledger_appendix_20261108/`、`lead/ledger_bound_20261109/`、`lead/GOAL_THREE_TARGETS_20261018.md`、`lead/PENDING_DECISIONS.md` 及 §4.2 全部 13 件，一字未改；两台账未追加任何一节（本会话 `_mhz_verify_out.txt:118-120` 各 0 命中，5 笔全部未入账）。
- 写入仅限 `lead/minhard_check_20261109/`：`MINHARD_SET_CHECK.md`（本件）+ `_mhz_verify.py/_mhz_verify_out.txt`、`_mhz_blocks2.py/_mhz_blocks2_out.txt`、`_mhz_lines2.py/_mhz_lines2_out.txt`、`_mhz_slice.py/_mhz_slice_out.txt`。**未改**既有 `_mh_*` 20 件与 `_mhv_*` 17 件中的任何一件。
- 实跑佐证：#3 与 #11 `git status --short -- <五只读目录 + 两台账>` 与起始 gitStatus 快照一致（五目录 `??`、两台账 `MM`，无本会话新增 `M`）；`git log -1 --format='%h %s'` = `2657458 GOAL-3T: 台账 §400→§508 与 D-07..D-11 裁决登记入账` 未变 ⇒ 未 commit / 未 push。#4 与复核回件两次 hashlib 收尾均 11/11 逐位一致；`_mhv_verify_out.txt:60` `ALL_UNCHANGED = True`。
- 零真机、零采样代码：未启动任何游戏进程、未 taskkill、未读活进程内存；未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。

### 6.5 未验项（不补造，如实登记）

1. **定谳本体未重跑**：C8a 75/75 逐格复现、`_sh_generator_512655.txt:14` 内容、CLI 会话库只读点查、15/15 逐位比对 —— 本会话未重跑/未复读，仅引用 `_ve_DRAFT_S609.md:15-22` 与 `S604_VERDICT_ENTRY_DRAFT.md:72-79` 的在案亲读（与 `S604_REFSYNC_FULL.md:353` 未验 #1 同源）。
2. **两台账全文未通读**：本会话只做正则 `§60[5-9]|§610|码形定谳|dur 字典|512655` 各 0 命中与 11 件 hashlib 指纹核对；「两台账无旧引用面」沿 `S604_VERDICT_ENTRY_DRAFT.md:129` 在案结论，非本会话全文亲读。
3. **Leader 实际从哪份载体复制入账未验**：本会话只能证实两件合订本 `:34`「可整段复制追加、逐字照抄已验」与 §607 正文逐字在盘；是否真被选为复制源属编排方裁决事实，本件只登记「存在该风险」，不宣称一定发生。
4. **旧指纹登记面未做全树全量反链枚举**：本会话 D 段只扫 `lead/`（并含本写域自身文件），未扫 `lead/` 之外；`S604_REFSYNC_FULL.md:278` 自认「未逐一枚举全部登记文件」，`:356` 自认「28 处全量反链 grep 未做」。执行前须补。
5. **sandbox 两件副本效力未判**：`_dnv_sandbox36/`、`_dnw_sandbox/` 两件 `LEDGER_APPENDIX_DRAFT.md:123` 逐字同文且 `IN_BLOCK=True`（`_mhz_blocks2_out.txt:17-19`），是否需同步改动属其他写域授权范围，本会话未判、未动；【复核】③ 亦指出撰写人以「未验的其他写域授权」排除二者不严谨。
6. **整仓（非 `lead/`）扫描未验**：`_mhz_blocks2.py` 首次 `os.walk(ROOT)` 超 120 s 被转后台后由 `TaskStop` 终止；`timeout 90 grep -rIl … .` 亦 `GREP_DONE_EXIT=124`（超时）。本会话的「9 命中」结论**只对 `lead/` 5396 件成立**；`GLM/`、`Qwen/`、`Step。**dfmodel=DeepSeek/`、`.tmp/` 等顶层目录未扫完。【复核】③ 的「50614 件」是其本人实跑，本会话未复跑该规模，不冒充本会话结论。
7. **§607 正文段指纹口径差异未完全复现**：本会话 `_mhz_slice_out.txt:3-8` 实算 `:13-26` 去尾换行 = 4892 B / `a758a87b…`（与 `_mhv_blocks3_out.txt:52-56` 一致），带尾换行 = 4893 B / `2d795beb…`（与 `_mhz_blocks2_out.txt:39-42` 一致）；在案登记的 `e9842d41…/4894 B`（`LEDGER_BOUND_VOLUME.md:202`、`_lb2_TEMPLATE.md:160`）本会话**未重跑 `_lb_build.py`**、未以该脚本口径复现 ⇒ 该值记「未验」，四份正文逐字相同的结论不受影响。
8. **行数口径**：编排方 `lines` 比实际换行数大 1（`:2-12` 每行 `lines_diff=1`），SHA256 与字节数 11/11 逐位 MATCH，非内容差异。
9. **复核回件 33 条命令未逐条重放**：本会话只读取其输出文件（`_mhv_*_out.txt`）并独立复算了其中可复算的部分；未逐条重放。
10. **`_lad_build.py` 重建回退推断未验**：本会话实算该文件 `exists=False`（`_mhz_blocks2_out.txt:198`），故 `S604_REFSYNC_FULL.md:126,338-339` 已把该理由降为未验推断；本件不把它当硬理由。
