# _ab_RULING_MATRIX_AB_20261109 — STATE_MATRIX.json「:2 收紧」方案 A/B 裁决

- 撰写：方案裁决员（动态工作流子代理 GLM），2026-11-09。性质：**只裁决、不施行**——本件通篇为方案与处方，不含任何「已改/已收紧」既成事实断言。唯一写域 = `lead/matrix_ab_ruling_20261109/`；被核件全部零改动（指纹 §0 逐件与编排方基线一致即证）。
- 裁决对象：上轮评估 `lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md` 实证的三处文档层缺陷（W1 矩阵 :2 后件过宽、W2 矩阵 :4 无跑后限定、O1 absent_confirmed × read_error 无行）与三选项（A 只收紧 :2 / B 同时动 :2 与 :5 / C 改结构）。
- **裁决结论：采 B（耦合件 §4.3 完整形态，含随批 :4 句）。C 与窄义 A 均不采。** 理由与改动清单见 §5/§6。

## 0 绑定行（本轮 `python -I -X utf8 -c` + hashlib 逐件实算；前 11 件与编排方下发指纹逐字节一致 = 11/11 MATCH）

被核对象 SHA256 = 6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8，字节数 = 29818
被核对象 SHA256 = 625436050020104bb6e40bd7b1ec0543b22e3e31cb5bb56a12b0480cff64e26f，字节数 = 14616
被核对象 SHA256 = b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b，字节数 = 22048
被核对象 SHA256 = 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016，字节数 = 3558
被核对象 SHA256 = 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf，字节数 = 66735
被核对象 SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759
被核对象 SHA256 = c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801，字节数 = 28897
被核对象 SHA256 = 1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b，字节数 = 23129
被核对象 SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
被核对象 SHA256 = a3975d0f44fe6e23187ddd98805101f2c12c061841158d98c9a4a13619bbf720，字节数 = 2900
被核对象 SHA256 = ce84dbd5c8f3eb4386737e994447414a137ed2513d53ef977451f7700ff089c1，字节数 = 12979
被核对象 SHA256 = 11d44321d5462f49edcfeb0a0d7aa1a0a99151924c1ec72fbb3c88fba91f2923，字节数 = 2791
被核对象 SHA256 = c18c7108882a69e2f294359d279ae7e8c2226f54f6f012b8172eddd26e088a6a，字节数 = 13230
被核对象 SHA256 = 8f0d7f077dd11a812099a5edaf238f1f5988586f74db08d54a92e521274c667e，字节数 = 7550

（第 1–11 行 = 编排方基线：耦合件 / 上轮评估回件 / pf2 修正提案 / 乙矩阵 / 乙设计 / 候选 LF / V2 / 重签件 / 母本 / PENDING 台账 / GOAL 台账。第 12–14 行 = 上轮探针输出三件：`_r5_probe_import_out.txt` / `_r5v_probe_out.txt` / `_r5_static_order_out.txt`——本轮实读验证对象。第 15–16 行 = 本轮自产两件：`_ab_probe.py` / `_ab_probe_out.txt`。）

## 0.1 本轮实跑命令清单（全部为只读取证；零真机、零采样、零写入被核域）

1. `mkdir -p …/lead/matrix_ab_ruling_20261109` + `ls`（建写域、列 row5 目录 15 件）
2. `python -I -X utf8 -c`（hashlib 14 件逐件实算 SHA256/字节数）→ §0 前 14 行
3. `grep -n "def \|verify\|VERIFY" …/_draft_semantics_check.py` + `wc -l`（T2 脚本结构定位，633 行）
4. `python -I -X utf8 …/_ab_probe.py > …/_ab_probe_out.txt`（EXIT=0，`AB_PROBE_ALL_PASS`，81 格全落定）
5. `grep -rn "跑后任意" --include="*.md" --include="*.json" . --exclude-dir=.git`（分布复核）+ `grep -c "任意文件状态" B2B_DESIGN.md`（=0）+ hashlib 自产两件

## 1 第一步：三处缺陷核对——全部成立（本轮独立复证，不采信上轮）

**码序**（证据：本轮 Read 候选 :4616-4698 逐行实读 + 自研 AST 探针 `_ab_probe_out.txt:15-29`）：
`classify_except_freshness`（候选 :4616-4698）顶层 if 链 = :4637 归一 → **:4643 `if post.get("read_error")` ⇒ post_read_error/none/None（:4644）** → :4648 unknown → :4652 error_pre_snapshot → :4657 无件（:4659 absent_both / :4662 vanished）→ :4666 new_first_appearance → :4673 缺 pre.sha → :4678 缺 post.sha → :4681-:4697 mtime 四支。**read_error 出口在码序第 2 位，先于一切 pre 分支**；设计同源：`B2B_DESIGN.md:310-311` 补丁原文「★ N1：错误独立出口，优先于一切状态折叠」与候选 :4642 注释同文（本轮实读）。

**探针验证声明（任务第一步点名要求，未采信上轮）**：
- 实读上轮输出：`_r5_probe_import_out.txt`（9 pre × 8 post，C1-C5 全 PASS :16-20，`PROBE_ALL_PASS` :22）；`_r5v_probe_out.txt`（独立 AST 码序 :4-29 与上同；P3 CELLS 72、C1-C4 PASS :104-108；P4 运行期显式 unknown 不产出 :113；P5 claimant 交叉表 :114-136）。
- 本轮自跑超集复现：`_ab_probe.py`（写域内、全程零文件写入、路径 safe() 白名单校验）81 格（9 pre × 9 post，含 read_error 拆 `exists=None`/`exists=True` 两型）`AB_PROBE_ALL_PASS`（`_ab_probe_out.txt:72`），关键格与上轮两份输出**同值**。
- 三处缺陷逐条：W1（:2 后件「跑后任意文件状态」把 read_error 格错盖为 unknown——探针 P5 [W1] MISMATCH :55-56）、W2（:4 无跑后限定把 error × read_error 错盖为 error_pre_snapshot——P5 [W2] MISMATCH :57-58）、O1（absent_confirmed × read_error 主子格无行 + exists=True 子格被 :6 字面「跑后在场」错盖为 new_first_appearance/high——P5 [O1′] MISMATCH :59-60；实流可达性实读 copy 路径 :4769 置 exists=True → :4772 write_bytes 可败 → :4786 置 read_error）。另登记：W3（:5/:13 fixture 域重叠，实流不可达：make_pre 在场必算 sha :4607）、O2（显式 unknown × 跑后在，运行期不可达——P4 复现）、O3（:2 收紧后的严格键孤儿，由 :2 分流句兜底记载）。
- 排他性检查：A6 基线 17 格四元组全对（`_ab_probe_out.txt:49`）——除已登记三处文档层缺陷外，矩阵 14 行与实码**无其它取值分叉**。

## 2 第二步：A 的完整性（A = 只收紧 :2 + 必修镜像 :148）

**(a) W1 是否关闭——关闭（错答消除），但严格键层留 O3 孤儿。** :2 新 condition（pf2 §4.5:193 文案）以「跑后读取正常（post.read_error 为空）」把 read_error 格划出自身主张，并内嵌分流句「post.read_error 非空时先落 post_read_error……见 :5 行」——探针 P5 [after-B] W1 RESOLVED（:61-62，该推演对 A/B 的 :2 部分同效）。残留：该格在 A 下无行可配（:5 的 preState 字段=present，按耦合件 §3.2「匹配键 = preState 字段 + condition 前件」不吸收 unknown pre 态），正确答案只写在 :2 的文字里——即耦合件 §4.2-1 的 O3：把「错答」换成「不答 + 文字兜底」。

**(b) W2 仍开——活性误配。** A 不动 :4。按矩阵逐行匹配验收时，输入「error × read_error」被 :4 错配为 **error_pre_snapshot**，实码为 **post_read_error**（探针 A2 + P5 [W2] MISMATCH）。取值层无损（conf=none/is_new=None/usable=False 两出口同值，pf2:176；探针 A5），错的是 verdict 标签：一次「跑后证据复制失败」（典型如游戏独占锁住 except.txt）会被验收记录归因为「跑前采集失败」——error 出口的语义细分被抹掉，且这正是 V2:110「矩阵 = 机器可读唯一口径」下按行匹配的真实使用场景（pf2:175 点名）。可达性：pre 采集抛异常与 post read_bytes/stat/write_bytes 失败两机制正交（:4634-4639 归一不依赖 post；:4773-4786 copy 异常路径独立置 read_error）。

**(c) O1 仍裸——一半是孤儿、一半是虚高误配。** A 不动 :6/:5。
- 主子格（read/stat 失败，exists=None）：无行（:5 要 present、:6 要「跑后在场」、:7 要「无件」，皆不满足）——验收要么「无行 = FAIL」要么静默漏过；而该格恰是「本趟疑似新出现却读不出来」的最需诚实登记场景（崩溃证据邻接位）。
- 子格（write_bytes 失败，exists=True）：:6 字面「跑后在场（存在性硬证）」被满足 → 矩阵宣称 **new_first_appearance/high/True**，实码 **post_read_error/none/None**（探针 A3 + P5 [O1′]）——**虚报 high 的活性误配，三处缺陷中后果最重的一格**。

**(d) 「必修 :148」有多硬——硬在防静默分叉，但既定门禁全抓不到。** `B2B_DESIGN.md:144` 明言 §2 表「下表与之逐行一致」，:148 以「跑后任意」承载与 JSON:2 完全相同的过宽语义（本轮实读）；只改 JSON:2 即双源不一致。抓不到它的门禁（本轮逐一实读定性）：T5（V2:184）只对 14 组 fixture 断言四元组、只读 STATE_MATRIX.json 不读设计镜像；T2（`_draft_semantics_check.py` :574 do_verify 只核草案 hunk 可套用性、:470-533 do_matrix 是**旧草案 classify 代码内嵌副本**的合成单测）均不比对镜像；T3/T4 为 AST/指纹，无关；重签件 :154 条件 2 的「三方不分叉」= STATE_MATRIX ↔ V2 §4.2 ↔ 候选实码、只比 (verdict,confidence)、**不含 B2B_DESIGN**。故不同步 :148 会静默通过全部既定门禁，只能靠人工/代理复读发现（pf2:205「滞留风险」已登记；耦合件 §4.5-2 同判）。本轮独立 grep 复现滞留分布：绑定域仅 `B2B_DESIGN.md:148` 一处，另有 4 件非绑定陈旧副本（`_draft_semantics.md:146`、`B2B_PREAUDIT.md:138`、`B_EXECUTION_SPEC.md:102`、`_n4_SPEC_N4_B2B_MATRIX.md:89`）；「任意文件状态」词组在乙设计 0 命中（单源断言成立）。

## 3 第三步：B 的边际成本（B = A + 改 :5 + 同步 :151；本裁决取耦合件完整形态另含随批 :4）

**(a) 增量改动 = 核心 2 处 + 随批 2 处，全部 1 行/处：** `STATE_MATRIX.json:5`（1 行）、`B2B_DESIGN.md:151`（1 行）、随批 `STATE_MATRIX.json:4`（1 行）、`B2B_DESIGN.md:150`（1 行）。绑定级联与 A **完全相同**：A 反正已打开 JSON 与 B2B_DESIGN 两个文件（:148 必修），B 的 4 行增量零额外文件进级联——换版登记清单不变（§6 登记 7/8）。

**(b) V2:120 确实不用动——已实读核实。** V2 §4.2 表（V2:114-130）列 = 文件行 / preState / verdict / confidence / usable，**无 condition 列**；V2:120 = 「| :5 | present | post_read_error | none | false |」。B 不改 :5 的 preState 字段（B2B_DESIGN:142 四态值域契约，写 any 违约；耦合件 :132/:134 同判），故该行仍真。pf2:204 的「放宽 :5 需连带 V2:120」只在「放宽 = 改 preState 字段」读法下成立——本裁决不采该读法，域覆盖由 condition 文本承载。同理 V2:117-130 其余 13 行与重签件 §3 表（:60-77）均不动：14 行 (verdict,confidence) 零变化（探针 A6），重签件 :154 条件 2「三方不分叉」保持。

**(c) B 之后四项关闭状态：** W1 **关**（同 A，且 :5 注记使该格在文本层有家，O3 一并收容——P5 [after-B] O3 RESOLVED :69-70）；W2 **关**（随批 :4 carve-out + :5 注记双承载——P5 [after-B] W2 RESOLVED :63-64）；O1 **关**（主子格与 exists=True 子格均由 :5 注记「pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行，匹配以本 condition 为准」显式收容，注记点名「先于 :4666 absent_confirmed」——P5 [after-B] O1′/O1-main RESOLVED :65-68）；W3 **不关但无验收风险**（仅 fixture 域：实流不可达 :4607；码序 :4643 < :4673 已被注记「先于 :4672 起 present 支」覆盖，登记即可）。O2 维持「不可达 + 登记即可」。

**(d) B 不引入新问题（逐项排查）：**
1. :2 分流句 ↔ :5 注记：一致不冲突——:2 的「先落 post_read_error……见 :5 行」恰是 :5 一般声明（全部 pre 态 × read_error 落 :5）的特例指向，互为交叉引用。
2. 重复表述：轻度存在（码序声明在 :2/:5 两处出现），但方向一致且各有必要（:2 需要它划出自己的排除域，:5 需要它声明全域）——可接受，非冲突。
3. :5 注记 ↔ :6 字面（exists=True 子格）与 :4（随批前）：文本重叠仍在，但注记末句「匹配以本 condition 为准」+ 码序枚举给出确定消解规则；这是「注记方案 vs 选项 C 结构分离」的已知取舍，不是 B 新造的问题（该重叠今日已存在于 :5/:14 与 :5/:13，耦合件 §3.2 同判）。
4. JSON 合法性：三条新 condition 均单行、无 ASCII 双引号，严格 JSON 不破；14 行结构不动 → T5 的「14 组 fixture」无需重述（耦合件 :136）。
5. 探针 P5 [after-B] 五格推演全 RESOLVED——处方文案的文本层路由与实码逐格相符。

## 4 第四步：裁决

**裁决：采 B（完整形态）。A 不采；C 不采。**

**(i) 活性错配 vs 文档瑕疵**（判准：按矩阵逐行匹配验收——V2:110「矩阵 = 机器可读唯一口径」、V2:184 T5 同法——会不会给出错误的预期 verdict）：
- **活性错配（会给错答案）**：W1（read_error 格被 :2 声称 unknown）、W2（被 :4 声称 error_pre_snapshot）、O1′ 子格（write_bytes 失败型被 :6 声称 new_first_appearance/**high**——唯一虚报置信的一格）。
- **文档瑕疵（不给错答案）**：O1 主子格与 O3（孤儿，「不答」，其中 O3 有 :2 分流句文字兜底）、O2（运行期不可达）、W3（fixture 域重叠、实流不可达）。取值层（conf/is_new/usable）在全部涉事格零影响（pf2:176、重签件 :87 11 对互为充要、探针 A5/A6）。

**(ii) 边际成本收益成比例。** A = 2 行 + 级联；B 核心 = 4 行 + 同一级联；B 完整 = 6 行 + 同一级联。多出的每 2 行都落在 A 已打开的两个文件内、不新增任何批准主体或换版登记项，却各关掉一个活性误配（W2）或收容两个裸格（O1）。选 A 的唯一收益是 diff 最小，代价是留下 pf2:175 警告的「标签误配换个格子存在」（耦合件 :129 原话）+ 一个 high 虚标 + 两个孤儿——**为省 2 行保留三个活性/半活性缺陷，不成比例**。

**(iii) 分阶段方案存在但劣后。** 技术上可 A→B 两批（A 即 pf2 §4.5 已登记处方），但两批 = 两次批准 + 同一批文件两次指纹换版登记（JSON/B2B_DESIGN 各改两遍）——严格更贵。仅作退路：若批准人今日只批 :2 一行，则 A 可先行，**但必须在台账如实登记 W2/O1/O3 残留**（耦合件 :138 同要求），并以下列为补做 B 的触发条件：① 验收口径升级为全格枚举（如本轮 81 格探针式验收）；② 真机趟实流出现 pre≠present 的 read_error 格（游戏锁件 + 跑前快照为 absent_confirmed/error）；③ N-5 集成前签发侧要求矩阵全格可配。若批准权限一次可覆盖 6 行（同一主体：乙设计责任人），**没有理由分批**。

## 5 第五步：可执行改动清单（★ 处方，未实施；全部改动须先经批准，改后立即做 §6 换版登记）

### 改动 1｜`lead/b2b_design_20261106/STATE_MATRIX.json` 第 2 行（关 W1；pf2 §4.5:193 文案原样）

原文（本轮 Read 实读 + 探针 P0 复印 `_ab_probe_out.txt:4`）：
```
  {"state":"unknown","preState":"unknown","condition":"pre=None / {} / 缺 state / 脏值（跑前快照未采集或采集未完成），跑后任意文件状态","verdict":"unknown","confidence":"none","usableAsCrashEvidence":false},
```
改为：
```
  {"state":"unknown","preState":"unknown","condition":"pre=None / {} / 缺 state / 脏值（跑前快照未采集或采集未完成），跑后读取正常（post.read_error 为空）；post.read_error 非空时先落 post_read_error（码序 read_error 出口先于 unknown 出口，候选 :4643 先于 :4648，见 :5 行）","verdict":"unknown","confidence":"none","usableAsCrashEvidence":false},
```
该行其余键值不动。批准：**乙设计责任人**（pf2 §4.6:200）。

### 改动 2｜`STATE_MATRIX.json` 第 5 行（B 核心新增；耦合件 §4.3-B:132 文案原样）

原文（本轮 Read 实读）：
```
  {"state":"post_read_error","preState":"present","condition":"跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口","verdict":"post_read_error","confidence":"none","usableAsCrashEvidence":false},
```
改为（condition 追加码序注记；**preState 字段不动**——B2B_DESIGN:142 四态值域契约）：
```
  {"state":"post_read_error","preState":"present","condition":"跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）⇒ 独立 error 出口（★ N1 码序 read_error 出口先于一切 pre 分支：候选 :4643-4646 先于 :4648 unknown / :4652 error / :4657 无件 / :4666 absent_confirmed / :4672 起 present 支；pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行，preState 列的 present 为最常见登记态，匹配以本 condition 为准）","verdict":"post_read_error","confidence":"none","usableAsCrashEvidence":false},
```
批准：**乙设计责任人**。

### 改动 3｜`STATE_MATRIX.json` 第 4 行（随批，关 W2；耦合件 §4.3-B:135 文案）

原文（本轮 Read 实读）：
```
  {"state":"error","preState":"error","condition":"跑前采集抛异常（snap.error 非空）⇒ 独立 error 出口，不降级、不静默、不给 high","verdict":"error_pre_snapshot","confidence":"none","usableAsCrashEvidence":false},
```
改为：
```
  {"state":"error","preState":"error","condition":"跑前采集抛异常（snap.error 非空）⇒ 独立 error 出口（post.read_error 非空时仍先落 post_read_error，见 :5 行），不降级、不静默、不给 high","verdict":"error_pre_snapshot","confidence":"none","usableAsCrashEvidence":false},
```
批准：**乙设计责任人**（同一主体、同一级联）。若批准人不采随批：B 核心仍成立，但 **W2 必须在台账如实登记为未关闭**，不得声称为已关闭。

### 改动 4｜`lead/b2b_design_20261106/B2B_DESIGN.md` 第 148 行（镜像必修，A/B 共同要求；pf2:205、耦合件 §4.5-1）

原文（本轮 Read 实读）：
```
| `unknown` | `unknown` | `pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后任意 | `unknown` | `none` | `None` | `false` |
```
改为（condition 列与 JSON:2 同步；「见 :5 行」在设计文档内改写为「见矩阵第 5 行」以免与本文行号混淆）：
```
| `unknown` | `unknown` | `pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后读取正常（`post.read_error` 为空）；`post.read_error` 非空时先落 `post_read_error`（码序 read_error 出口先于 unknown 出口，候选 `:4643` 先于 `:4648`，见矩阵第 5 行） | `unknown` | `none` | `None` | `false` |
```
批准：**乙设计责任人**（改在乙设计本体内，耦合件 §5.4-2）。

### 改动 5｜`B2B_DESIGN.md` 第 151 行（镜像，B 核心新增；与改动 2 同文案）

原文（本轮 Read 实读）：
```
| `post_read_error` | `present` | 跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口 | `post_read_error` | `none` | `None` | `false` |
```
改为：
```
| `post_read_error` | `present` | 跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口（★ N1 码序 read_error 出口先于一切 pre 分支：候选 `:4643-4646` 先于 `:4648` unknown / `:4652` error / `:4657` 无件 / `:4666` absent_confirmed / `:4672` 起 present 支；pre 任意态——unknown/absent_confirmed/present/error——+ read_error 均落本行，preState 列的 present 为最常见登记态，匹配以本 condition 为准） | `post_read_error` | `none` | `None` | `false` |
```
批准：**乙设计责任人**。

### 改动 6｜`B2B_DESIGN.md` 第 150 行（随批镜像，与改动 3 同步）

原文（本轮 Read 实读）：
```
| `error` | `error` | 跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口 | `error_pre_snapshot` | `none` | `None` | `false` |
```
改为：
```
| `error` | `error` | 跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口（`post.read_error` 非空时仍先落 `post_read_error`，见矩阵第 5 行） | `error_pre_snapshot` | `none` | `None` | `false` |
```
批准：**乙设计责任人**。

### 登记 7｜指纹换版登记（A/B 同级联；改后必须立即执行，否则重签件 :153 条件 1「任一漂移即失效」令既有 YES 自动作废）

- `lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md` **:45**（乙设计绑定行）与 **:46**（乙矩阵绑定行）：按改后实算 SHA256/字节数更新（B2B_DESIGN.md 与 STATE_MATRIX.json 两件）。执行主体：V2 签发侧。
- `lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md` **:33**（§2 第 4 行乙设计）与 **:34**（§2 第 5 行乙矩阵）：同上。执行主体：重签件签发侧。
- 重签件 :153 条件 1 的引用值随上两行更新，正文措辞不改；:154 条件 2（三方 (verdict,confidence) 不分叉）不受影响——探针 A6 证 14 行值零变化。V2/重签件**正文内容无需改**，不需要 V2 来源会话对内容另行批准，仅签发侧换版登记（耦合件 §5.4-3、pf2:231 先例）。

### 登记 8｜台账补登（编排方义务）

`lead/PENDING_DECISIONS.md` 与 `lead/GOAL_THREE_TARGETS_20261018.md` 补登「:5 欠宽 + W2/O1/O2/O3 + 选项 B 裁决」登记行——本轮 grep 实跑两台账对 `连带供裁量|matrix_row5|欠宽|:5 行|post_read_error` 均 0 命中（耦合件 §4.4-3/4 同判）。补登致台账指纹变化 → 重签件 :40-41 两行同入换版登记。

## 6 「确认不用改」清单（逐处给依据）

1. **V2:120 及 V2:117-130 全表**——§4.2 表五列、无 condition 列（V2:114-116 本轮实读）；B 不改 preState 字段 → 14 行全部仍真；pf2:204 的连带要求仅适用于「改 preState 字段」读法，本裁决不采。
2. **候选 `qc151_trip.candidate_lf.py`**——零改动。实码按设计实现（B2B:310-311 补丁注释与候选 :4642 同文）；pf2:171「错在矩阵措辞滞后于设计，非候选缺陷」；探针 A6 基线 17 格全对；动候选即击穿重签件 :157 条件 5（范围不变）并触发全量重签——绝对禁止。
3. **重签件 §3 表（:60-77）与 V2 §4.2 表内容**——(verdict,confidence) 值零变化 → :154 条件 2 保持；只做登记 7 的指纹换版。
4. **B2B_DESIGN:163 八类对账**——按类别计数（①-⑧），不引 condition 文本，行序不变 → 不受影响。
5. **STATE_MATRIX.json:3 行**——O2（显式 unknown × 跑后在）运行期不可达（make_pre :4589-4610 三路必覆写；本轮 P4 探针复现「explicit 'unknown' never produced at runtime」PASS）→ 不新增行，登记即可。
6. **STATE_MATRIX.json:6 行**——O1′ 由改动 2 的 :5 注记显式吸收（注记点名「先于 :4666 absent_confirmed」）；不加 carve-out 句。若批准人求更强确定性可加同句（可选、非必需、非本裁决必改项）。
7. **STATE_MATRIX.json:13 行**——W3 仅 fixture 域（实流不可达：make_pre 在场必算 sha :4607，算炸→error；码序 :4643 < :4673 被注记「先于 :4672 起 present 支」覆盖）→ 不动，登记即可。
8. **四件非绑定陈旧副本**（`_draft_semantics.md:146`、`B2B_PREAUDIT.md:138`、`B_EXECUTION_SPEC.md:102`、`_n4_SPEC_N4_B2B_MATRIX.md:89`）——本轮独立 grep 复现分布；均不在 V2:45-46 绑定表、非重签件 :153 指纹对象 → 不动（可选随批批注「措辞已陈旧」）。
9. **母本 `out/re_work/.../qc151_trip.py`**——绝对不动。

## 7 未验项（如实登记，不补造）

1. **T1/T2/T5 门禁本轮未跑**（V2:180-184 三项均自记「本轮未跑」；本轮任务未授权跑门禁；R3:42「14/14 match」为历史转引）。若施行本裁决，N-5 集成时须对**应用后副本**重跑（V2:187）。
2. 候选 412,759 字节仅实读 :4575-4804 区间 + AST 顶层扫描，未逐行通读全文（与裁决对象无关部分）。
3. 「匹配以本 condition 为准」的机器可执行性依赖消费方实现——STATE_MATRIX.json 无 match-order/priority 字段，严格键匹配器如何消解 :4/:5（随批后）与 :5/:6 的文本重叠属读方行为。若需更强确定性，可加 `match_priority` 字段——属结构改动（选项 C 温和版），本裁决不推荐，仅登记为后续可选项。
4. 本轮未重跑 row5 两份探针脚本本体（其 P4 需在 row5 只读域建临时件，与本轮写域约束冲突）；替代：实读其输出三件（§0 第 12-14 行绑定）+ 本轮自研零写入探针独立复现（81 格 ⊃ 其 72 格口径，关键格同值）。
5. B2B_DESIGN §2 表与 JSON 14 行的一致性为人工逐行对照 + 探针 P0 复印，未做程序化逐字 diff（耦合件 §5.5-6 同项未解）。

## 8 纪律声明

本轮**未改任何被核件**：§0 前 14 件 hashlib 实算与编排方基线/历史绑定逐字节一致（11/11 基线 MATCH）。新增文件仅三个、全部落唯一写域 `lead/matrix_ab_ruling_20261109/`：`_ab_probe.py`、`_ab_probe_out.txt`、本件。零真机（未启动 gamemd.exe/ra2loader/YURI.exe，未 taskkill，未读活进程内存）；零采样代码（探针 = 标准 import 协议隔离加载 + AST 静态分析 + 纯内存字典，运行期零文件写入；无 hook/MiniDump/SuspendThread/StackWalk/注入/动态内存解析）；未 commit、未 push。本件为裁决与处方，不含既成事实改动断言。
