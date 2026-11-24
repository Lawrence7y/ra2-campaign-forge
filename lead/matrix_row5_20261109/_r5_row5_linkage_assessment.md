# _r5_ STATE_MATRIX.json:5 行「码序下欠宽」连带评估（只评估，未改任何被核件）

评估对象：`lead/b2b_design_20261106/STATE_MATRIX.json` 第 5 行（文件行 :5，14 数据行之第 4 行）
`{"state":"post_read_error","preState":"present","condition":"跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口","verdict":"post_read_error","confidence":"none","usableAsCrashEvidence":false}`
（本轮 Read 实读全文 16 行，:5 即上原文；与编排方指纹一致。）

## 0 指纹绑定（本轮 `python -I -X utf8 _r5_fingerprint.py` 实算，9/9 与编排方一致）

```
被核对象 SHA256 = `1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016`，字节数 = 3558
被核对象 SHA256 = `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf`，字节数 = 66735
被核对象 SHA256 = `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2`，字节数 = 412759
被核对象 SHA256 = `c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801`，字节数 = 28897
被核对象 SHA256 = `1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b`，字节数 = 23129
被核对象 SHA256 = `b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b`，字节数 = 22048
被核对象 SHA256 = `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636`，字节数 = 399508
被核对象 SHA256 = `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7`，字节数 = 52419
被核对象 SHA256 = `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede`，字节数 = 759518
```
（顺序：乙矩阵 / 乙设计 / 候选 LF / V2 / 重签件 / 修正提案 / 母本 / PENDING_DECISIONS / GOAL 台账。）

## 1 第一步：码序逐行（实读 + AST 静态序列 + 全格实跑三重证实）

`classify_except_freshness` 候选 :4616-4698。顶层分支序列（`_r5_static_order.py` AST 实跑，输出 `_r5_static_order_out.txt`）：

| 码序 | 行 | 分支头 | 出口 |
|--:|--:|:--|:--|
| 0 | :4634-4639 | pre 归一（非 dict→{}；state 不在 `FRESHNESS_SNAPSHOT_STATES`（:228 四态元组）→ unknown），只赋 `out["pre_snapshot_state"]`，**无 return** | — |
| 1 | :4641 | post 归一（非 dict→{}），**无 return** | — |
| 2 | **:4643-4646** | `if post.get("read_error"):` | `post_read_error/none/None` |
| 3 | :4648-4651 | `if st == "unknown":` | `unknown/none/None` |
| 4 | :4652-4654 | `if st == "error":` | `error_pre_snapshot/none/None` |
| 5 | :4656-4664 | `if not post.get("exists"):`（内分 absent_confirmed→absent_both / 其余→vanished） | :4659/:4662 |
| 6 | :4666-4669 | `if st == "absent_confirmed":`（在场） | `new_first_appearance/high/True` |
| 7 | :4672-4697 | present 支：缺 pre.sha→error_pre_snapshot(:4673)、缺 post.sha→post_read_error(:4678)、sha 异→new_write(:4681)、mtime 四分支(:4686/:4690/:4693/:4697) | 见左 |

**回答：是——read_error 出口（:4643-4646）在所有 pre 分支（unknown :4648、error :4652、无件 :4657、absent_confirmed :4666、present 支 :4672 起）之前。**
实跑复核（`_r5_probe_import.py`，标准 import 协议加载真实函数，9 pre × 8 post = 72 格，输出 `_r5_probe_import_out.txt`，`PROBE_ALL_PASS`）：
- 9 类 pre（None / {} / 缺state / 脏值 / 显式unknown / absent_confirmed / present / present缺pre_sha / error）× read_error 全部落 `post_read_error|none|None`（C1-C5 全 PASS）。
- 故 **:5 行确属欠宽**：read_error 出口的真实输入域 = 四态 preState 全体 + pre=None/{} 等，而 :5 只登记 `preState="present"`。但 :5 自身覆盖的 (present × read_error) 格**正确**（实跑同格吻合）；欠宽的是「行」对「出口域」的覆盖，不是已登记格的取值。
- 对照：post_read_error 的**第二个**出口 :4678-4680（缺 post.sha256）确为 present 独占（实跑：absent_conf×缺post_sha→new_first_appearance、显式unknown×→unknown、error×→error_pre_snapshot），与矩阵 :14（preState=present）吻合。

## 2 第二步：14 行匹配矩阵与重叠输入

匹配键 = `preState` 字段 + condition 前件。逐行核（condition 原文见矩阵 :2-:15；判定依据码序 + 72 格实跑）：

| 格（pre × post） | 实码落点 | 矩阵现况 | 判 |
|:--|:--|:--|:--|
| None/{}/缺state/脏值 × read_error | post_read_error | **:2 误盖**（「跑后任意文件状态」→unknown） | W1（已登记 R2:53/R3:47/V2:132/重签件:89） |
| 同上四态 × 跑后正常（无件/在场各变体） | unknown | :2（收紧后）/ :3（显式unknown×无件） | ✓ |
| 显式unknown × 跑后在 | unknown | **无行**（:2 前件不含显式unknown；:3 只写「跑后无件」） | **O2 孤儿（既有）**，实际流不可达（make_pre :4589-4613 各路必覆写初值，永不产出显式 "unknown"） |
| error × read_error | post_read_error | **:4 误盖**（condition 无 post 限定→error_pre_snapshot） | **W2（本轮新发现，前轮各登记均未载）**，实际流可达（make_pre error 态 dict → copy 异常路径 :4786） |
| error × 其余 | error_pre_snapshot | :4 | ✓ |
| absent_confirmed × read_error | post_read_error | **无行**（:5 要 present；:6/:7 要「在场/无件」硬证，read_error 时 exists=None） | **O1 孤儿（既有）**，实际流可达 |
| absent_confirmed × 无件 / 在场 | absent_both / new_first_appearance | :7 / :6 | ✓ |
| present × read_error | post_read_error | :5 | ✓ |
| present × 缺pre.sha × read_error | post_read_error（read_error 先于 :4673） | **:13 误配风险**（缺pre.sha 前件也命中）；实际流不可达（make_pre 在场必算 sha，算炸→error） | W3（仅 fixture 域） |
| present × 缺pre.sha × 正常 | error_pre_snapshot | :13 | ✓ |
| present × 缺post.sha | post_read_error | :14（与 :5 在 read_error 时重叠，但四元组同值，无害） | ✓ |
| present × 其余（无件/sha异/mtime 四支） | vanished/new_write/leftover×2/rewritten×2 | :15/:10/:8/:9/:11/:12 | ✓（R3:43 映射同） |

**(a) 收紧 :2 后，「pre 未采集 + post 读失败」还有行可匹配吗？** 没有——:2 前件限定「跑后读取正常（post.read_error 为空）」后该格严格按键无行（孤儿 O3）。但按上轮建议文案（修正提案 §4.5 :193），:2 的 condition 内嵌分流句「post.read_error 非空时先落 post_read_error（……见 :5 行）」，落点在**文档层**有记载，仅严格键匹配层面为空。今天该格不是孤儿而是**误配**（W1，声称 unknown，实码 post_read_error）——收紧把「错答」换成「不答」，方向正确。
**(b) 会不会有孤儿？** 会，且三类：O3 由 :2 收紧新造；O1、O2 在收紧**之前**就无行（与 :2 无关）。
**(c) 归因**：不是 :5 单方、也不是 :2 单方——矩阵缺「read_error × 非 present preState」的承载（该出口按设计 B2B_DESIGN.md:310-311「N1 错误独立出口，优先于一切状态折叠」本就 preState 无关；矩阵 :5 键却是 present 独占）。:2 过宽是把其中一格（W1）**错盖住**，:4 过宽把另一格（W2）**错盖住**，absent_confirmed 格本来就裸露（O1）。收紧 :2 只是掀开盖子，不制造问题本体。

## 3 第三步：三选项与推荐

**选项 A（只收紧 :2，pf2 §4.5 :193 文案）**：修 W1；O3 成为文档级孤儿（分流句兜底）；**O1 仍裸、W2（:4 格）仍是错配**——最刺眼残留是 W2：一个按 :4 匹配的输入会被声称 error_pre_snapshot，实码 post_read_error，正是 pf2:175 警告的「标签误配」换了个格子继续存在。验收面：T5（V2:184，14 组 fixture 断言 verdict/confidence/is_new/usable 四元组，R3:42 同法）不受影响（condition 文本不进四元组断言；R3:42 行1 fixture benign-post 已 match）；T2（unknown->high=0）不受影响。A 可接受但不完整。
**选项 B（同时动 :2 与 :5，推荐）**：
- JSON:2 ← 修正提案 §4.5 :193 文案原样。
- JSON:5 condition 追加码序注记（preState 字段**不动**，理由见下）：
  `「跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口（★ N1 码序 read_error 出口先于一切 pre 分支：候选 :4643-4646 先于 :4648 unknown / :4652 error / :4657 无件 / :4666 absent_confirmed / :4672 起 present 支；pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行，preState 列的 present 为最常见登记态，匹配以本 condition 为准）」`
  （B2B_DESIGN.md:142 约束 preState ∈ 四态、由 H01 `FRESHNESS_SNAPSHOT_STATES` 约束，字段写 "any" 会破坏值域契约；域覆盖由 condition 文本承载。）
- **镜像核对（本轮实读定论）**：`B2B_DESIGN.md:151` **必须**同步（该表带 condition 列，且 :144 明言「下表与之逐行一致」）；`B2B_DESIGN.md:148`（:2 镜像「跑后任意」）同样必须同步（pf2:205 已登记滞留风险）；**`V2:120` 在本形态下不需要动**——V2 §4.2 表（:114-130）只有 文件行/preState/verdict/confidence/usable 五列，无 condition 列，preState 字段未变则该行仍为真。登记项「放宽需连带 V2:120 与 B2B_DESIGN.md:151」只在「放宽 = 改 preState 字段」的读法下才对 V2:120 成立。
- 绑定级联（A 与 B 相同）：乙矩阵 sha 变 → V2:46 / 重签件 §2 第 5 行（:34）/ 重签件 :153 生效条件 1 换版登记（pf2:200/:232 同口径）；B 下乙设计 sha 亦变 → V2:45 行同入换版。14 行结构不动 → T5 的「14 组 fixture/14/14」无需重述。
- **建议随批（本轮新发现，同一族）**：JSON:4 condition 加一句「（post.read_error 非空时仍先落 post_read_error，见 :5 行）」+ B2B_DESIGN.md:150 镜像同句，关闭 W2。不加亦应在登记中如实保留 W2。
**选项 C（改结构：拆 :5 成四行或新增行）**：能消严格键孤儿，但 14→15/17 行会击穿至少六处**内容级**绑定文本——B2B_DESIGN:144「14 项」/:163 八类对账、V2:110「14 数据行」/:114/:184「14 组 fixture/14/14 match」、重签件 §3:56「矩阵十四行逐行比对」/:148 五项必查 14/14、R3:42-43——不止指纹换版而是断言重写 + T5 重规约；且四态值域约束（B2B_DESIGN:142）使「preState=any」新行自身违域。对三个落点 confidence=none/is_new=None/usable=False 的 error 格而言收益边际、代价全面，**不推荐**。
**推荐：选项 B**（:2 收紧 + :5 condition 注记 + :148/:151 镜像；:4/:150 随批为佳）。理由：① 72 格实跑证实 read_error 出口域=四态全体，只在 :2 写分流句（A）会留下 W2 错配与 O1 裸格；② A→B 的边际代价仅一句话（JSON:5 + B2B_DESIGN:151），而绑定级联与 A 完全相同（B2B_DESIGN:148 反正要随 :2 修，:144「逐行一致」不变式一破俱破）；③ C 的全量断言重写与三个 none 格的收益不成比例。

## 4 第四步：「最小修复面」说法复核（grep 本轮自跑，不采信上轮）

实跑 `grep -rn "任意文件状态" D:/Project/ra2-campaign-forge --exclude-dir=.git`：命中 = `STATE_MATRIX.json:2`（唯一规范源）+ 12 处**引用该登记**的复审/台账/规格件（R2 :53/:91/:107、R3:47 及其审计 :78、旧草案 :117、旧复审 :202/:56、`_r2_leftovers_out.txt:12`、cs 复核 :44、重签件:89、YI 规格 :150、修正提案两件多处）。均为转引，非第二规范源。
`grep -n "任意" B2B_DESIGN.md`：仅 **:148** 一处，且措辞是「跑后任意」而非「任意文件状态」——上轮「B2B_DESIGN grep 0 命中」**字面为真**。
**但「最小修复只动一行」在语义层不成立**：B2B_DESIGN.md:144 明言设计 §2 表「下表与之逐行一致」，:148 以「跑后任意」承载与 JSON:2 完全相同的过宽语义。只改 JSON:2 不同步 :148，即成**双源不一致**（同一行两处口径：JSON 说「跑后读取正常+分流」，设计表仍说「跑后任意→unknown」）。
**T5 抓不到**：T5（V2:184）只做 14 组 fixture 的代码↔矩阵四元组断言，从不比对 B2B_DESIGN §2 表与 JSON；T2 只查 verdict 级性质（unknown->high=0）；重签件 :154 条件 2「三方不分叉」的三方是 STATE_MATRIX↔V2 §4.2↔候选实码，不含 B2B_DESIGN 且只比 (verdict,confidence)。故该不一致会**静默通过全部既定门禁**，只能靠人工/代理复读（即本轮这类回溯）发现。

## 5 本轮新发现登记（如实，不改件）

1. **W2**：矩阵 :4（error/error）condition 无跑后限定，pre=error + post.read_error 格被声称 error_pre_snapshot，实码 post_read_error（72 格实跑第 9 行第 1 列）。前轮 R2/R3/V2/重签件/pf2 各登记均只涉 :2 与 :5，未载此格。同族同性质（文档措辞精度、无 high/崩溃证据泄漏）。
2. **O1**：absent_confirmed × read_error 无行（实际流可达）。**O2**：显式unknown × 跑后在 无行（实际流不可达，make_pre 永不产出显式 "unknown"；R3:43 的行1-2 映射实际上已按「unknown 态合并」理解，与 :3 的「+跑后无件」限定不符）。**W3**：present×缺pre.sha×read_error 的 :5/:13 重叠（仅 fixture 域可达）。
3. **登记位置勘正**：该「连带供裁量」项登记于 `V2_PRECISION_FIX_PROPOSAL.md:202-207`（§4.7）与 `_pf2_findings_20261109.md:35`；`grep -n "连带供裁量\|matrix_row5\|:5 行\|欠宽"` 于 `lead/PENDING_DECISIONS.md` **0 命中**——两台账（PENDING_DECISIONS.md、GOAL_THREE_TARGETS_20261018.md）均未载此项。

## 6 未验事项

1. R3 的 14 组 fixture 原始档 `_review_probe_r3_out.txt` 未复读，R3:42「行1 unknown/none/None/False」为转引；T1/T2/T5 本轮未跑（属 N-5 门禁件，本轮任务未要求）。
2. pre=present + exists=False + read_error 同置的组合格未测（调用方错误路径 exists 恒 None，实际流不可达；仅 fixture 域理论重叠 :15/:5）。
3. 「跑后载体件快照」:4816-4825 等本函数之外的收尾链未展开（与本项无涉）。

## 7 纪律声明

零真机、零采样（探针为纯函数级 import + AST 静态分析，无 hook/MiniDump/SuspendThread/StackWalk/注入/动态内存解析）；被核九件零改动（指纹实算前后一致）；产出仅落本写域 `lead/matrix_row5_20261109/`（_r5_fingerprint.py、_r5_static_order.py(.txt)、_r5_probe_import.py(.txt)、本件）；未 commit、未 push。
