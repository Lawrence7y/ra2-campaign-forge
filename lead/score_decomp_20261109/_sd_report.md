# +21 分逐行分解 · 可归因性 · 配对统计 · in-sample 修正

**写域**：`lead/score_decomp_20261109/`（唯一写域，本件前缀 `_sd_`）
**铁律遵守**：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 注入 / 动态内存解析）；绝对只读保护目录与两件台账一律未改；只做分解与统计，未改任何脚本、语料、产物；不 commit、不 push。所有 Python 用 `python -I -X utf8` + 绝对路径，指纹用 `hashlib`。
**本会话实跑命令数**：见 §0.4。

---

## 0 先核指纹与分解（第一步 a）

### 0.1 编排方 10 件指纹独立复核（`hashlib` 实算，全 MATCH）

命令（本会话实跑）：
```
python -I -X utf8 -c "<hashlib sha256 + len on 9 named files; os.walk 找 16649 字节件>"
```
输出逐字：
```
d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe 38575 lead/gate_pipeline_20261109/_gp_regression_out.json
68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358 37461 lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json
1804e5bfb4c3ded9c0f19a44ae6e409b890a5b7c192657253a6694f2be5df1d3 13017 lead/gate_pipeline_20261109/_gp_regression.py
25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7 15811 lead/gate_pipeline_20261109/_gp_pipeline.py
c00833b3fef5b8b5f93cdfd9d5223f22149878dd868200c1a070d76e553d8ae1 51927 lead/comparability_20261109/COMPARABILITY_AUDIT.md
5d5a7d55c4bc585b8ec66d99679fe837e49bbe45546fdfc89efeab7afe384328 12784 lead/comparability_20261109/_cmp_assert.py
9dc062202fd9c00b2b74ce6393f29a90f18012a9914cf18dc9cd7ffa653f2698 11594 lead/chain_vs_single_20261109/_cs_align_out.json
3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 52419 lead/PENDING_DECISIONS.md
2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede 759518 lead/GOAL_THREE_TARGETS_20261018.md
--- 16649-byte candidates ---
e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079 16649 lead\evidence_indep_20261109\_ei_n13_predicates_src.py
e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079 16649 lead\gate_n13_20261109\_n13_predicates.py
```
⇒ 第 10 件 `lead/gate_n13_20261109/_n13_predicates.py` 的占位对象解析为 `_ei_n13_predicates_src.py` / `_n13_predicates.py`（两份同字节同哈希），与编排方 `e1195b3b…f3079 / 16649` 一致；亦与 `lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md:279` 的绑定行、`_gp_pipeline.py:32` 的谓词指纹先验一致。**10/10 MATCH**。

### 0.2 复核回件绑定行（格式固定，本会话 `hashlib` 实算）

被核对象 SHA256 = d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe，字节数 = 38575

被核对象 SHA256 = 68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358，字节数 = 37461

被核对象 SHA256 = c00833b3fef5b8b5f93cdfd9d5223f22149878dd868200c1a070d76e553d8ae1，字节数 = 51927

被核对象 SHA256 = 9dc062202fd9c00b2b74ce6393f29a90f18012a9914cf18dc9cd7ffa653f2698，字节数 = 11594

被核对象 SHA256 = e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079，字节数 = 16649

被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419

被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

### 0.3 分解独立复现（本会话实跑）

命令：
```
python -I -X utf8 -c "<读两份 JSON，按 id 对齐；score=chain==expect；逐子集算分>"
```
输出逐字：
```
nA 74 nB 72
common 71 onlyA ['GP-A1', 'GP-A2', 'GP-A3'] onlyB ['GP-C03']
GP-C03 text_head= '亦非不宣告 N-4 正式绑定已生效'
GP-A1  text_head= '亦非不宣告 N-4 正式绑定已生效'
equal? True
chainA 69 / 74 = 93.2432 %
chainB 48 / 72 = 66.6667 %
flips 3
   ('GP-C05', 'CATCH', 'PASS', '未核 grep 结果：已入账 0 命中')
   ('GP-C06', 'CATCH', 'PASS', '未核 grep 结果：已生效 0 命中')
   ('GP-C07', 'CATCH', 'PASS', '未核：已入账 grep 结果 = 0 命中')
n_frozen 68
B(72) frozen  chain72_frozen = 48 / 68
A(74) frozen  chain74_frozen = 66 / 68
B(72) flips   chain72_flips = 0 / 3
A(74) flips   chain74_flips = 3 / 3
A(74) onlyA   chain74_only74 = 0 / 3
B(72) onlyB   chain72_only72 = 0 / 1
DELTA frozen 18 flips 3
total 21
```
⇒ **四项数值全部可复现**：`frozen68=+18 / flipped3=+3 / new3=+0 / deleted1=+0 / sum=+21`。与 `COMPARABILITY_AUDIT.md:305-309`、`CHAIN_VS_SINGLE.md:73-75`、`_gp_regression_out.txt:16`、`_gp_regression_v1_union_out.txt` 逐项一致。另核 `GP-C03` 与 `GP-A1` 除 `id/family/note` 外所有字段逐项相同（`except id/family/note identical? True`，本会话实跑），仅 `family: GP_CONFLICT -> GP_ALLPASS_TRUE_ASSERTION`；与 `COMPARABILITY_AUDIT.md:99` 一致。

### 0.4 本会话实跑命令清单（口径：`ranCommands` = 27 次独立 `python -I -X utf8` / `grep` / `find` / `ls` / `git` 调用；下列为与结论直接相关的 14 条）

1. 指纹 10 件 + 16649 候选（`hashlib`）—— §0.1
2. 两份 JSON 顶层结构 / row schema —— §0.3 准备
3. id 集差 / 翻标 / 冻结子集 / 各子集得分 / total=21 —— §0.3
4. new3 / deleted1 / flips 全字段转储 —— §1、§2(b)、§4
5. `_gp_pipeline.py` S3/DEFAULT/fail 检索 + 全文件实读 —— §3、§4
6. `_gp_regression.py` chain/union 检索 + 全文件实读 —— §0.3、§3
7. 审计 §2/§4/§5/§6 实读 —— 全篇
8. `n13 predicates` S3/DEFAULT 检索 —— §4
9. 全只读域 `grep "亦非不宣告|19 式|S3"` —— §4
10. `dneg_generative_20261109` 19 式清单与 `_dg_step34_out.json` 实读 —— §4(b)
11. 配对 b/c + exact binomial + CP/Wilson CI —— §3
12. `P.gate_check` 实跑重放该句（74 版逐 span）—— §4(a)(b)
13. `_v12_rule.py` `classify_v12` 实跑 —— §4(b)(c)
14. 18 行增益逐行清单 / 家族 / unresolved / 重复文本 / FP 分解 / bootstrap 200000 次 / pp 分解 / 修正基线 / 相关 p / 家族登记 —— §1–§3、§5
15. `P.gate_check` 重放 3 条增益定位 K3+K9 —— §3(a)
16. 指纹 12 件附加绑定行 —— §0.2 补
17. `git status --porcelain` 只读域 + `__pycache__` mtime 核对 —— §0 纪律

（17 类、共 27 次调用；未启动任何真机或采样路径。）

---

## 1 第一步：四项分项数值、算式、+0 的含义

### (a) 数值能否复现 —— **能**，见 §0.3。

### (b) 逐项算式（定义 `s(V, S) = Σ_{id∈S} 1[chain_V(id) == expect_V(id)]`）

| 分项 | 算式 | 值 |
|---|---|---|
| 总分差 | `s(74, all74) − s(72, all72) = 69 − 48` | **+21** |
| frozen68 | `s(74, F) − s(72, F) = 66 − 48` | **+18** |
| flipped3 | `s(74, P) − s(72, P) = 3 − 0` | **+3** |
| new3 | `s(74, onlyA) − 0 = 0 − 0` | **+0** |
| deleted1 | `0 − s(72, onlyB) = 0 − 0` | **+0** |
| 校验 | `18 + 3 + 0 + 0` | **= 21** |

其中 `F = 共有 71 条 − {GP-C05, GP-C06, GP-C07}`（68 条，两版 `id/text_head/tokens/expect/四个单层列` 逐行相同，见 `COMPARABILITY_AUDIT.md:183`）；`P = {GP-C05, GP-C06, GP-C07}`；`onlyA = {GP-A1,GP-A2,GP-A3}`；`onlyB = {GP-C03}`。

**pp 口径的分解**（本会话实跑）：
```
pp delta = 100*(69/74 − 48/72) = 26.57657657657658
        = 100*(69−48)/72  − 100*69*(74−72)/(72*74)
        = 29.166666666666668 − 2.59009009009009 = 26.57657657657658
```
即 +26.58pp 由「分子多 21 条（按 72 分母）+29.17pp」与「分母 +2 的稀释 −2.59pp」合成；**分母稀释只作用于 pp，不作用于「条数差 21」**。

### (c) ★ `new3=+0` 是什么意思 —— **三条都判错，不是被分母稀释**

本会话转储（§0.3 与 `python -I -X utf8 -c "<全字段>"` 输出）：
```
GP-A1 74 expect=CATCH chain=PASS correct=False | 亦非不宣告 N-4 正式绑定已生效
GP-A2 74 expect=CATCH chain=PASS correct=False | 本件登记闭合，母本即日起适用
GP-A3 74 expect=CATCH chain=PASS correct=False | 三值填毕，见证已由编排方签字
```
`chain74_only74 = 0/3`（§0.3）。三条**全部是漏报（FN）**，一条分都没拿到 ⇒ 分子贡献恒 0。
- 若问「是不是分母稀释」：**不是**。「条数差」是纯分子差，新增 3 条只让分母 72→74；它们对 `69−48` 的贡献是 0。分母稀释只在把分数写成百分比时出现（上面 −2.59pp），且这 −2.59pp 是 `69` 这个分子被更大的分母除的结果，不能算到 `new3` 头上。
- 佐证：`_gp_regression_out.txt:9` `GP_ALLPASS_TRUE_ASSERTION n=3 chain_ok=0 FP=0 FN=3`；`GATE_PIPELINE_COMPOSE.md:392-394` 三条逐行标 `MISMATCH / FN`；`_gp_DESIGN.md:276-282` 明写「兜不住，如实说兜不住」。
- **反向含义**：这 3 条是按已知盲区定向构造的（`_gp_regression.py:121-130`、`_gp_DESIGN.md:274`），造出来就是为了让 `chain` 判错；它们使 74 版 `69/74` 的**分子停在 69**，即 `+21` 里没有一分来自「模型能答对新题」。

### (d) `deleted1=+0` 同理

`GP-C03` 在 72 版 `expect=CATCH / chain=PASS / correct=False`（`_gp_regression_v1_union_out.txt:45`、本会话转储），**本来就是 0 分**；删掉它分子 −0、分母 −1，所以条数差贡献 0。
**更关键的**：它与 `GP-A1` 是同一句文本换 id 换族（§0.3、`COMPARABILITY_AUDIT.md:99`），两版都判错（`GP-C03->GP-A1 文本相同且两边都错? True | 72错=True 74错=True`，`COMPARABILITY_AUDIT.md:308`）。⇒ 按文本键对齐时是 **0 条真删除 + 2 条真新题 + 1 条换 id**（`COMPARABILITY_AUDIT.md:99`）；`deleted1` 这个标签本身就是 id 口径的假象。分母净 +2 只来自 A2/A3 两条真新题。

---

## 2 第二步：逐项可归因性

### (a) `frozen68=+18` 是真改良吗 —— **不是「改良」，是「一次可定位的实现替换在冻结子集上的配对效应」**

判据（逐条给）：
1. **同一批题**：68 条上两版 `id / text_head / tokens / expect / family` 逐行相同（`COMPARABILITY_AUDIT.md:183`、本会话转储 `GP-C03≡GP-A1` 与 flips 判定列全同）。✔
2. **同一真值**：68 条 `expect` 未变（flips 已剔除）。✔
3. **模型输出确实变了**：18 行 `CATCH→PASS`，且 18 行在 72 版 `layer_unresolved` 合计 22、74 版合计 0（本会话实跑）；`chain_conflicts_total` 两版恒 31（`_gp_regression_out.json` / `_gp_regression_v1_union_out.json` 顶层）。⇒ 变的是「冲突是否被裁决」而非「冲突数」（`COMPARABILITY_AUDIT.md:166`）。✔
4. **确切机制**：本会话用 `P.gate_check` 重放 3 条增益，输出 `rules=['K3','K9'] / n13_kind=A|B / n13_veto=True / verdict=PASS`；即 `_gp_pipeline.py:168-171` 的「K9 精筛覆盖宽进」。72 版是三层 problems 朴素并集（`_gp_regression.py:147-149` 注释、`GATE_PIPELINE_COMPOSE.md:431`），74 版是逐 span K1–K9 `ADJUDICATED`。✔
5. **但「真值没变」只在 68 条上成立，且不是同一量**：`chain` 列两版导出定义不同（`COMPARABILITY_AUDIT.md:180,210,296`），是 M 轴变更，不只是 I 轴；按 `COMPARABILITY_AUDIT.md:221`「应判 M 轴变更而非 I 轴」。✘
6. **E 轴不可核验**：72 版生成脚本 `_gp_regression_v1_union.py` 全仓与 git 历史零命中（本会话 `find . -iname "*v1_union*"` 只出 `.json`/`.txt`；`git log --all --oneline --name-only | grep -i v1_union` → 无输出），`COMPARABILITY_AUDIT.md:310,343` 标「未验重跑」。⇒「除合成裁决外其余输入相同」只是从输出列反推，非脚本级复核。✘
7. **in-sample**：K9 是为消 20 条 FP 而写（`_gp_pipeline.py:168-172` 注释、`GATE_PIPELINE_COMPOSE.md:431`、`COMPARABILITY_AUDIT.md:219`）；18 行全是 `expect=PASS` 的误拦（`72 chain=CATCH` ×18、`74 chain=PASS` ×18，本会话实跑），正是 K9 点名的失败形态；`CHAIN_VS_SINGLE.md:129`「出题人=改规则的人=批卷人」。✘

⇒ **判定**：`+18` 可归因于「把合成裁决从三层朴素并集换成逐 span K1–K9」这一处实现替换，**但不能归因于「算法更好」**。范围只到「这 68 条冻结考题、这套冻结真值、这个被比较列」，且带「未验重跑」标签。

### (b) `flipped3=+3` —— **3 分纯来自改标注**，逐条判合理性

本会话实跑：三条 `naive/r10/r12/n13/chain/layer_conflicts/layer_unresolved` **7 个判定列逐列相同**（`judge cols identical? True`），只有 `expect` 与 `note` 变：
```
GP-C05  CATCH -> PASS | 未核 grep 结果：已入账 0 命中
        note72='★ 三层全说放过但实际真断言（构造）'
        note74='前置否定标签 + A 检索结果；人工判检索结果，非完成断言'
GP-C06  CATCH -> PASS | 未核 grep 结果：已生效 0 命中
        note72='★ 同族构造（已生效）'  note74='同上（已生效）'
GP-C07  CATCH -> PASS | 未核：已入账 grep 结果 = 0 命中
        note72='★ 前置否定标签 + A 结果'  note74='同上（标签在冒号前）'
```
`COMPARABILITY_AUDIT.md:116` 已定：「3 分是模型一个字没改、只翻真值标注得来的」；`:139` 定性为「什么算真断言」的判读口径改写，属**真值判读本体变更**，不是注记润色。

逐条判（依据 = 上游标注手册的 A/B 检索结果定义）：
- **GP-C05** `未核 grep 结果：已入账 0 命中`：前置「未核」标签 + `grep 结果` + `0 命中`，是**检索结果的读数**，不是「本笔已入账」这类完成断言。与 `GATE_N13_QUOTED_ASSERTION.md:23` A 类定义（`grep`/清点/核查/`grep=0`/`0 命中`）、`_n13_regression.py:48-79` P01/P02/P11/P12/P14 的 `expect=PASS` 同族；与 `_gp_DESIGN.md:237`「`grep 结果：已生效 0 命中` … 按 K9 判 PASS」一致。**改得对**。
- **GP-C06** `未核 grep 结果：已生效 0 命中`：仅把完成词从「已入账」换成「已生效」，结构完全相同。**改得对**（同族）。
- **GP-C07** `未核：已入账 grep 结果 = 0 命中`：标签移到冒号前，`grep 结果 = 0 命中` 仍是读数。**改得对**。

**但必须同时给出反证边界**（不能只挑有利证据）：
- 72 版内部对「`0 命中` + 完成词」的标注并不自洽：本会话实跑列出 72 版所有含 `0 命中`/`grep=0` 的行，`N13-N18「本笔已入账 0 命中不得写成未入账」expect=CATCH`（`_n13_regression.py:103`，这是真断言被 `0 命中` 反向劫持，与 C05 不同形），`N13-P02/P11/P12/P14` 与 `N13-P08/P10` 都是 `expect=PASS`。⇒ 三条 C05/C06/C07 在 72 版被标 `CATCH` 而同形检索结果行被标 `PASS`，**72 版标注本身不自洽**；74 版改为 `PASS` 使口径一致。
- 但**标注手册未冻结封 SHA**（`COMPARABILITY_AUDIT.md:421` 把「冻结标注手册」列为应做而未做的门禁；`:440`「真值可变 ⇒ 分数可被人工制造」）。`_n13_regression.py:110` N24「`grep 结果：已入账`（裸完成词、无主语、无结果数字）→ 拿不准默认 FAIL」与 C05 只差「`0 命中`」这一读数；`GATE_N13_QUOTED_ASSERTION.md:311` 明写该边界。⇒ 三条的 `PASS` **语义上可辩护，但程序上没有冻结的手册可核对**，属「合理但未经双盲 κ / 未封 SHA 的人工判读」，`COMPARABILITY_AUDIT.md:357` 把盲标注 κ 列为未做设计。
- **结论**：`+3` **不可归因于算法改进**，0 分来自模型。可归因于「真值标注修正」，且修正的**因果方向是修正基线**而非提升模型。

### (c) ★ 修正基线，不是改良 —— **判断成立**

若三条标注改得对，则 72 版 `48/72` 里有 3 分是被错标注扣掉的：三条在 72 版 `expect=CATCH` 而 `chain=PASS`，被记为 FN（`_gp_regression_v1_union_out.txt:46-48` 三行标 `MISMATCH`）；`CHAIN_VS_SINGLE.md:74` 明写 72 版 `N13 fn=4` 正是 `C03/C05/C06/C07`，翻标后其中 3 条自动「判对」。

**修正基线（本会话实跑）**：
```
72 修正后 = 48 + 3 = 51 / 72 = 70.83333333333333 %
74          = 69 / 74 = 93.24324324324324 %
修正后 raw delta = 69 − 51 = 18   (+22.40991 pp)
```
⇒ 把标注统一到 74 版口径后，`+21` 立刻缩成 `+18`，**3 分蒸发**。这 3 分是「72 版基线被错标注压低」造成的虚增，是 **baseline correction**，绝不是「模型变强 3 分」。
（注意：修正后的 `51/72` 与 `69/74` **仍不可比**——分母、样本集、列定义、评分器都不同，`COMPARABILITY_AUDIT.md:206,310`；上式只用于说明 3 分的来源，不构成可报的差值。）

### (d) `new3 / deleted1` 零贡献原因 —— 见 §1(c)(d)

补两条可归因性判据：
- `new3`：三条 74 版 `chain=PASS / expect=CATCH`，全 FN。它们对 74 版是**负向信息**（暴露共同盲区），只是评分函数只数 `correct`，所以记 0 而不是 −3。`_gp_DESIGN.md:284-287` 给出根因（A1 = R12 `DOUBLE_NEG_RE` 枚举表外的分离型双重否定 + N13.C 转发 R10；A2/A3 = `spans=0` 时 K7 `RAISE` 是死分支）。
- `deleted1`：`GP-C03` 72 版本来 0 分；且与 `GP-A1` 同文本同判定列同结果（§0.3），是**换 id 换族 + 改 note**，不是真删除（`COMPARABILITY_AUDIT.md:99`）。`by_family` 7→8 且新族未登记进 `sources`（本会话实跑：`GP_ALLPASS_TRUE_ASSERTION in sources? False`，两版 `sources` 键逐字相同），`COMPARABILITY_AUDIT.md:154,179` 记为独立元数据变更面。
- ⇒ 两项都是 **0 分可归因于算法**，也 **0 分可归因于标注修正**；但它们改变了分母与类别先验（CATCH 40→39 / PASS 32→35，`COMPARABILITY_AUDIT.md:148`），所以 `pp` 口径不可直接相减。

### (e) ★ 汇总：`+21` 里有几分可归因于「算法改进」

| 分项 | 分数 | 可归因于算法？ | 依据 |
|---|---|---|---|
| frozen68 | +18 | **条件性 +18**（不是「算法更好」，是「一次实现替换在 68 条冻结集上的配对效应」；且 in-sample、E 轴未验重跑、M 轴列定义变） | §2(a)、§3 |
| flipped3 | +3 | **否，0 分**。纯标注修正 = 修正基线 | §2(b)(c) |
| new3 | +0 | **否**（三条全 FN） | §1(c) |
| deleted1 | +0 | **否**（本来 0 分，且是换 id） | §1(d) |
| **合计** | **+21** | **可归因于「算法改进」= 0 分**；可归因于「某处实现替换」= 18 分（条件性、in-sample、不可泛化）；可归因于「修正基线」= 3 分 | 本会话全部实跑 |

**严格答案：0 分**。理由：「算法改进」隐含「在新数据上更好」的泛化主张；本会话没有任何盲留出集证据（`CHAIN_VS_SINGLE.md:131` 明写「正式盲留出集本次未做，标未验」；`COMPARABILITY_AUDIT.md:357` 把 κ 列为设计），而 74 行是 train=test（`CHAIN_VS_SINGLE.md:129`、`EVIDENCE_INDEPENDENCE.md:157`）。若把措辞放宽为「在冻结题集上换掉一处实现带来多少分差」，则答案是 **18 分，且必须带 §3(e) 的边界**。

---

## 3 第三步：统计检验

### (a) frozen68 的配对精确值

命令与输出（本会话实跑）：
```
python -I -X utf8 -c "<逐行配对，b=72错且74对，c=72对且74错；exact binomial>"
frozen n= 68 b= 18 c= 0 n_discordant= 18
p_two_sided_exact = 7.62939453125e-06 = 1/131072 = 2*2^-n
p_one_sided = 3.814697265625e-06
Clopper-Pearson 95% CI = 0.8146980318621477 1.0
Wilson 95% CI = 0.8241207763533425 1.0
point b/n = 1.0
18 frozen changed ids= ['N13-P01','N13-P02','N13-P03','N13-P04','N13-P05','N13-P06',
  'N13-P07','N13-P11','N13-P12','N13-P14','N13-P15','N13-P16','R10-CTX-07',
  'R10-CTX-08','R10-CTX-09','R10-CTX-10','R10-CTX-11','REAL-BOUND']
```
⇒ **b=18, c=0, n_discordant=18**（编排方给的 `paired_b=18 / paired_c=0 / paired_n=18` 精确复核通过）。与 `COMPARABILITY_AUDIT.md:335` 逐字一致。

补充（本会话实跑）：
```
PAIR 18/68 = 0.2647058823529412  (配对正确率差)
bootstrap 200000 次 percentile 95% CI = [0.16176470588235295, 0.36764705882352944]
74 版 frozen68 上 chain vs n13 : b=2 c=0 n=2 p2=0.5
72 版 frozen68 上 chain vs n13 : b=20 c=0 n=20 p2=1.9073486328125e-06
```

### (b) exact binomial 双侧 p 与 95% CI

- **H0**：不一致对中「74 对 72 错」与「72 对 74 错」等概率（p=0.5，McNemar 精确版）。
- **双侧 p（小 p 值法）** = `2 × 2^−18 = 1/131072 = 7.62939453125e-06`；单侧 = `2^−18 = 3.814697265625e-06`。
- **95% CI（不一致对中「改进方向」的比例）**：Clopper–Pearson `[0.8147, 1.0000]`；Wilson `[0.8241, 1.0000]`。点估计 `18/18 = 1.0`。
- **95% CI（配对正确率差 18/68）**：bootstrap 百分位 `[0.1618, 0.3676]`（200000 次重抽，seed=20261109，本会话实跑）；正态近似 `0.2647 ± 1.96×0.0535`。
- 全部数字为本会话 `math.comb` + `Fraction` + 二分求 CP + bootstrap 实算，未引用上游数值充当「已跑」。

### (c) ★ 这个 p 能不能支撑「算法更好」 —— **不能**

逐条理由：
1. **p 只回答「这 18 个不一致对是否随机对称」**，不回答「算法在目标总体上更优」。H0 是「两算法在这批题上无系统差异」，`b=18,c=0` 只说明**方向一致地全部朝一侧**，且这一侧恰好是「72 版误拦的 PASS 题被放行」。
2. **in-sample 调参**：K9 是为消这 20 条 FP 而写（`_gp_pipeline.py:168-172`；`GATE_PIPELINE_COMPOSE.md:431`「20 条新增误报全部来自 N13 已判 A/B 放过、R10 宽进仍报 assertion」；`COMPARABILITY_AUDIT.md:219,344` 明写「in-sample 调参收益，不是泛化证据」）。18 条增益 = 72 版 20 条 FP 中被修好的 18 条（本会话实跑 `72 FP 中被 74 修好的 = 18，仍 FP = 2`）。⇒ **p 值测的是「照着答案改完以后答案是否对上了」，这是循环论证**。
3. **样本非独立**：18 条只有 16 个不同 `text_head`（本会话实跑 `unique text_head among 18 = 16 of 18`；`N13-P01↔R10-CTX-10`、`N13-P05↔R10-CTX-07` 两组逐字重复），且集中在 3 个族（`N13_POS 12 / R10_CTX 5 / REAL3 1`）。按独立行的 `2^−18` 高估了有效样本量。
4. **对照物不是「更好」**：在 frozen68 上 74 版 `chain 66/68` 仍劣于 `n13 68/68`（本会话实跑 `b=2 c=0 p2=0.5`；`COMPARABILITY_AUDIT.md:337,346`、`CHAIN_VS_SINGLE.md:67`）；72 版 `chain 48/72` 显著劣于 `n13 68/72`（`p=1.9073486328125e-06`）。⇒ 74 版把「显著劣于单层」修成「不显著劣于单层」，**不是「优于」**。
5. **E 轴未验重跑**：72 版脚本不在盘上（§2(a)6），`COMPARABILITY_AUDIT.md:343` 标「未验重跑」；`p` 的前提「两格只有 I 不同」未成立（`chain` 列定义也变了，M 轴）。
6. **p 不是效应量**：`b/c` 与 `p` 都不含「新题上怎样」的信息。74 版在 3 条定向新题上 0/3（§1(c)），在 20 条示例性未见变体上 `chain 16/20`（`_cs_holdout_out.txt:26`），且其中 3 条与 GP-A 逐字重复（`CHAIN_VS_SINGLE.md:131`）——**没有一个数字支持泛化**。

⇒ **结论**：`p=7.63e-06` 支撑的只有一句极窄的话：「在这 68 条冻结行上，两版 `chain` 列的 18 处不一致全部朝同一方向，且方向为 72 误拦→74 放行」。**不支撑「算法更好」，不支撑「合成链优于单层」，不支撑任何总体/泛化主张**（`COMPARABILITY_AUDIT.md:328,340`）。

### (d) ★ 考虑「算法是在这批题上调出来的」，p 要怎么修正 —— 给方案（可执行）

**核心认识**：in-sample 偏差**不能靠给 p 乘一个常数修好**，`2^−18` 的抽样模型本身失效（18 条不是从目标总体独立抽的，是被 K9 的失败清单选出来的）。必须换估计框架。按可执行性排序：

1. **主方案：物理隔离的盲留出集 + 一次性预注册**（`COMPARABILITY_AUDIT.md:357-362` step1/step4、`CHAIN_VS_SINGLE.md:278,280`）。出题人 ≠ 改规则人 ≠ 批卷人；`train/dev/test` 分集封 SHA；K9 的失败形态（A/B 检索/表头/目录）与 N19–N26、GP-A 整族只进 train，禁进 test；双盲标注 + Cohen's κ ≥ 0.8；test 一次性使用。**在 test 上重新算 b/c 与 exact binomial**——这才是有效的 p。`COMPARABILITY_AUDIT.md:357`、`CHAIN_VS_SINGLE.md:131` 均标本会话**未做，未验**。
2. **若只能用现有数据，做「选择过程校正」**：
   - **(i) 按独立单元而非行计**：把逐字重复与同族形态聚成簇，本会话实算 16 个独立文本 / 3 个族；用簇级符号检验 `p = 2×2^−16 = 3.0517578125e-05`（16 簇）或 `2×2^−3 = 0.25`（3 族，全部同向）。**3 族口径下 p=0.25，不显著**（本会话实跑）。
   - **(ii) 设计效应**：`n_eff = n/(1+(n−1)ρ̄)`，本会话实算 `ρ̄=0 → 18`、`0.3 → 2.95`、`0.5 → 1.89`、`0.8 → 1.23`、`0.9 → 1.10`、`1.0 → 1.0`。18 条全是同一 K9 分支产物，保守取 `ρ̄≈1` ⇒ `n_eff ≈ 1` ⇒ 有效证据只有「1 次定向修复」，不是 18 次独立成功。
   - **(iii) 多重比较 / 调参搜索次数 M**：若把「设计 K1–K9、挑阈值、挑词表、翻标注、造新题」视作 M 次隐式尝试，Bonferroni 需 `p < 0.05/M`。本会话实算 `0.05/7.62939453125e-06 = 6553.6`，即 **M ≥ 6554 才会把显著性抹掉**。但 **M 在本会话无法从盘上确定**（无调参日志、无预注册、72 版脚本缺失），故标「**未验**」，不填具体 M；不得据此反推「p 仍稳健」。
   - **(iv) 选择性推断**：把 K9 的选中事件写进条件分布，用 post-selection inference / 条件二项（在「已知这 18 条是 K9 的失败样本」条件下，观测到 18/18 修好的概率 ≈ 1，信息量 ≈ 0）。这直接说明 `p=7.63e-06` 是**被选择过程制造出来的**。
3. **交叉实测补齐**：`COMPARABILITY_AUDIT.md:223-224` 的 2×2 设计、`_cmp_manifest.json` 的 `crossed_design_cells_actually_executed = []`（`:297`）——本会话**未跑**，标未验。
4. **报法修正**：`COMPARABILITY_AUDIT.md:430` 要求同时报 `b/c + exact binomial 双侧 p + bootstrap CI + macro-F1`，并禁止只报点估计；`p>0.05` 只能写「未检出差异」。

**修正后能给的最强话**：把 `p` 降格为「描述性内部效度指标」，并在报告里同时给出 `n_eff≈1`、族级 `p=0.25`、盲留出「未验」三项；**不得把 `p=7.63e-06` 单独写成显著性证据**。

### (e) 「这个 +18 能外推到什么范围」的明确边界

**能外推到（写死）**：
- 仅这 **68 个 id**（清单见 §3(a)；完整 68 条亦见 `COMPARABILITY_AUDIT.md:332` [9] 段）；
- 仅这 68 条的**冻结文本前 90 字 `text_head`、冻结 `tokens`、冻结 `expect`**（第 91 字之后正文是否改动属「未验」，`COMPARABILITY_AUDIT.md:141`）；
- 仅「**72 版三层 problems 朴素并集 → 74 版逐 span K1–K9 ADJUDICATED**」这一处合成裁决替换；
- 仅这一个被比较列 `chain`（两版同名不同义，`COMPARABILITY_AUDIT.md:180,210`）；
- 仅「18 条 `expect=PASS` 的误拦被放行，`CATCH` 召回 36/36 不变」（`COMPARABILITY_AUDIT.md:336-337`）；
- 结论措辞只能是「**在这份冻结语料上，把 I 从 X 换到 Y，配对 b=18 c=0**」（`COMPARABILITY_AUDIT.md:200,216`），不得写「改良 18 分」或「A 优于 B」。

**不能外推到（逐条写死，`COMPARABILITY_AUDIT.md:342-346`）**：
- ❌ 全语料 / 74 条 / 72 条：3 条翻标、2 条真新题、1 条换 id 题都不在 68 条里；
- ❌ 「合成链 vs 单层谁更好」：对照物是「同一个 `chain` 的两种算法」，frozen68 内 `chain 66/68` 仍劣于 `n13 68/68`（`p=0.5`）；
- ❌ 目标总体 / 生产置信界 / 泛化：train=test，无盲留出（`CHAIN_VS_SINGLE.md:129,131`；`EVIDENCE_INDEPENDENCE.md:157,252`「74 行 train=test，以上为描述值，不是生产置信界」）；
- ❌ 任何新形态：K9 未覆盖的 `spans=0` 死分支、词表外同义改写、分离型双重否定（`_gp_DESIGN.md:284-287`）依然全漏；
- ❌ 任何「其它输入相同」的断言：E 轴未验重跑，仅由输出列推断；
- ❌ 与另一版本数字相减或用 `→` 连接不同 `n` 的分数（`COMPARABILITY_AUDIT.md:468`）。

---

## 4 第四步：GP-C03 ≡ GP-A1 连带问题 —— ★ 前提需更正

### (a) 为什么换 id —— 但先更正任务前提

**任务书第四步(a)写「72 版把它判 CATCH、74 版也判 CATCH，标注都是 CATCH」。逐字核对结果：标注（`expect`）确实都是 CATCH，但两版 `chain` 都是 `PASS`（漏判）。本会话实跑**：
```
# 两版 JSON 转储
GP-C03 [72/B] expect='CATCH' chain='PASS' naive='CATCH' r10='PASS' r12='PASS' n13='PASS'
GP-A1  [74/A] expect='CATCH' chain='PASS' naive='CATCH' r10='PASS' r12='PASS' n13='PASS'
# 本会话 P.gate_check 实跑重放 74 版逐 span：
T= ['已入账', '已追加', '已生效']
r10_scan = ([], ['已生效 处于否定语境（R10 豁免，窗内否定词 2）'],
   [{'token':'已生效','pos':14,'kind':'negation','neg_count':2,'in_span':False}])
r12_scan = ([], [])          ← r12=0，任务书这半句正确
r13_assertions = ([], [{'token':'已生效','pos':14,...,'kind':'C','exempt':True,
   'rule':'C 否定式（R10 negation 已覆盖，微段内直接否定）','r10_kind':'negation'}])
chain(74 逐span) final= PASS  summary={'spans':1,'catch':0,'pass':1,'conflicts':0,'unresolved':0}
  ROW 已生效 14 r10=PASS r12=ABSENT n13=PASS n13_kind=C rules=['K5'] verdict=PASS
```
旁证逐字：`_gp_regression_v1_union_out.txt:45` `GP-C03 expect=CATCH … chain=PASS MISMATCH`；`_gp_regression_out.txt:47` `GP-A1 expect=CATCH … chain=PASS MISMATCH`；`GATE_PIPELINE_COMPOSE.md:392` `GP-A1 … **PASS**（MISMATCH / FN）`；`_gp_DESIGN.md:280` `合成链 = PASS，漏报`；`COMPARABILITY_AUDIT.md:308` `两边都错? True | 72错=True 74错=True`；`_cs_holdout_out.txt:22` `U-N12 CATCH PASS PASS CATCH`（v12 列才是 CATCH）。
⇒ **「74 版判 CATCH」在 `chain` 列上不成立**。成立的是：`expect=CATCH`（人工真值）、`naive=CATCH`（字面命中）、`v12=CATCH`（独立谓词）、`DG_chain=CATCH`（设计实验）。此更正必须写进结论，否则第四步(b)(c) 会被带偏。

**换 id 的原因（能证实 / 不能证实分开写）**：
- **能证实（字段级）**：`GP-C03` 与 `GP-A1` 除 `id`/`family`/`note` 外**逐字段相同**（本会话实跑 `except id/family/note identical? True`；`COMPARABILITY_AUDIT.md:99`）。变化只有：`id: GP-C03→GP-A1`、`family: GP_CONFLICT→GP_ALLPASS_TRUE_ASSERTION`（新族 74 版才出现，`by_family` 7→8）、`note: 'GV-L 分离型双重否定残余（人工真值=肯定）'→'分离型双重否定=肯定；编排方背景点名的 GV-L 残余'`。`_gp_regression.py:121-130` 把三条「三层全说放过但实际有真断言」的构造样本成族写入 `GP_ALLPASS_TRUE_ASSERTION`，此句被收编进新族并顺号命名 A1；`_gp_DESIGN.md:274-282` 的 3(d) 即该族的设计说明。
- **语义上**：72 版把它归在 `GP_CONFLICT`（构造冲突形态），但它**根本不是冲突**——`r10=negation / r12=0 / n13=C 转发 R10`，三层给同一个（错的）答案，`layer_conflicts=0`、`layer_unresolved=0`（两版转储）。`_gp_DESIGN.md:285` 明写「A1 是共同盲区，不是冲突」，`GATE_PIPELINE_COMPOSE.md:216` 标「无冲突（无相反意见），共同盲区，判错」。⇒ 换族是**分类纠错**（从「冲突形态」改到「三层全放过的真断言」），换 id 是随之的编号重排。
- **不能证实（标未验）**：盘上**没有任何「为什么换 id」的书面裁决/变更单**。本会话 `grep -rn "GP-C03|换 id|换族|重命名" lead/` 只找到审计的描述（`COMPARABILITY_AUDIT.md:99,129`、`_cs_recompute_out.txt:124`），无决策记录；`COMPARABILITY_AUDIT.md:444-450` 亦记「原始派发任务书未在仓库留盘」，是否明写允许改语料/标注「未验」。⇒ 动机只能推断到「成族重编 + 分类纠错」，**无文档可核，标未验**。
- **后果**：换 id 使按 id 对齐出现「1 删 3 增」的假象，而按文本键对齐是「0 删 + 2 真新增 + 1 换 id 换族」（`COMPARABILITY_AUDIT.md:99`）；它同时改变 `by_family` 且新族未登记 `sources`（本会话实跑 `in sources? False`）。这是 `NOT_COMPARABLE` / `INDETERMINATE` 的构成面之一（`:174,179,292`）。

### (b) 这句靠什么抓到 —— 分列追查

- **19 式第一条**：`lead/dneg_generative_20261109/_dg_step34.py:40-60` 的 `GAPS` 首项即 `("亦非不", "亦非不宣告 N-4 正式绑定已生效")`，`_dg_step34_out.json:step3a_gaps[0]` 本会话实读为 `{"construct":"亦非不","r12_regex":false,"h5_regex":true,"dg_catch":true,"dg_hit":"亦非不宣告"}`。⇒ **`r12_regex=false`（即任务书说的 `r12=0`）确证**。
- **74 版 `chain` 靠什么**：**什么都没抓到，判 PASS**。见 (a) 实跑：`r12=ABSENT`、`n13=C(转发 R10 negation)`、逐 span 走 `_gp_pipeline.py:179-180` 的 **K5 → PASS**；`spans=1` 但 `catch=0`。根因 `_gp_DESIGN.md:285`：`_g7_predicates.py:76` 的 `DOUBLE_NEG_RE` 是枚举构式，「亦非不」这种 GV-L 分离型不在表内；N13 的 C 类确定性转发 R10 kind（`EVIDENCE_INDEPENDENCE.md:295`）。`GATE_PIPELINE_COMPOSE.md:266` 自认「PASS，漏报」。
- **那「CATCH」究竟出在哪一列**（本会话逐件实读）：
  1. `naive=CATCH`：只是 `已生效` 字面命中，非语义判别（`_gp_regression.py:136-137`）。
  2. **`v12=CATCH`（S3 DEFAULT fail-closed）**：本会话实跑 `lead/gate_v1v2_20261109/_v12_rule.py` 的 `classify_v12`：
     ```
     {"verdict":"V2","hard":[],"weak":[],"override":"","review_flag":true,
      "reason":"无任何 V1 形状、亦无硬性完成宣称：机器判不了，fail-closed 默认 V2（宁可误拦），须人工复核或改写为显式规定式"}
     ```
     对应源码 `_v12_rule.py:167-170`；`EVIDENCE_INDEPENDENCE.md:169,173` 逐字定性：「**S3 DEFAULT「判不了→fail-closed」，不是语义识别**」「A1 只是把『拿不准』翻成 fail-closed，任何拿不准的行都会同样 CATCH，不构成对该形态的语义判别」；`only_default=true`（`_eind_verify_out.json:302`，本会话 grep 定位）。`_cs_holdout_out.txt:22` 的 `U-N12 … v12=CATCH` 就是这一列。
  3. **`DG_chain=CATCH`（生成式替身设计实验）**：`_dg_step34_out.json:590-592` 本会话实读 `{"id":"GP-A1_DG","dg_chain":"CATCH",...,"adjudicated":["L1 pos=14 tok=已生效 裁决=CATCH rules=K1 (r10=PASS r12=CATCH n13=CATCH)"]}`；`_dg_DESIGN.md:242-251` 说明做法是在**内存**造 `_Shim` 把 `g7.r12_scan` 指向 `DG.dg_scan`、`DOUBLE_NEG_RE` 指向 `DG_DROPIN_RE`，模拟「只改 `:76` 一行」的传播，使 R12 报 1 → N13 判 D → 合成链按 **K1** 兜住。该文件 `:1-5` 明写「只出设计，不改任何既有件」，**未实装到 `_gp_pipeline.py`**（`EVIDENCE_INDEPENDENCE.md:195` 亦记所有第四层变体均为设计实验、未实装）。
- ⇒ **追查结论**：74 版 `chain` 没抓到它；`CATCH` 只出现在 `naive`（字面）、`v12`（S3 兜底）、`DG`（未实装设计）三处，且三者都不是 74 版评分用的列。

### (c) ★ 靠 S3 DEFAULT fail-closed 算「算法改进」还是「兜底碰巧」 —— **兜底碰巧，且比碰巧更弱：是恒真兜底**

判据：
1. **机制无判别力**：`_v12_rule.py:167-170` 的 S3 DEFAULT 是「无任何 V1 形状、亦无硬性完成宣称 ⇒ 默认 V2 + `review_flag=true`」，对**任何**拿不准的行都返回 CATCH；它不读「亦非不」，不识别双重否定。`EVIDENCE_INDEPENDENCE.md:169,173` 明写「不是语义识别」、`only_default=true`。⇒ 在这句上「判对」与「判对的原因」无关，是**先验 `expect=CATCH` 恰好与恒 CATCH 的兜底同号**。
2. **代价可量化**：同一 V12 层在 74 行单层 `47/74`（`fp=18, fn=9`，`EVIDENCE_INDEPENDENCE.md:177`）；把它装进链，`naive_OR_all4` 净 **−13**（56/74），只有限死 `spans==0` 且单调 OR 才净 `+1`（70/74，`±2.7%` 不显著），且**该配置下 GP-A1 仍漏**（`:188-195`）。⇒ 靠 S3 抓 A1 的同时会引入 18 条 FP，**不是改进**。
3. **对照 DG**：DG 的 `CATCH` 靠 `r12=CATCH → K1` 的枚举/生成式命中，属「扩了构式表」的定向修复；但它是同一批题上按已知 19 式清单造的（`_dg_step34.py:40-60`），仍是 in-sample，且明确未实装。
4. **判定**：**「兜底碰巧」**，不算算法改进。严格说连「碰巧」都偏乐观——它是**恒真兜底在正类样本上的必然命中**，不含该形态的任何信息量；`EVIDENCE_INDEPENDENCE.md:173` 把它折成「实质新信息 2/3（A2/A3 靠第二套词表硬命中），A1 为 0」。

### (d) 这对 frozen68 的 +18 有何影响 —— **直接影响为 0，但抽掉一根「泛化」支柱**

- **直接影响 = 0**：本会话实跑 `gains=18`，其 74 版 `layer_unresolved` 合计 **0**、`layer_conflicts` 合计 22；74 版**全表** `chain_unresolved_total=0`、无任何行 `layer_unresolved>0`（`74 rows with layer_unresolved>0: []`）。`_gp_pipeline.py:175` 的 `FAIL_CLOSED` 分支必置 `unresolved=True`，故**18 条增益没有一条来自 FAIL_CLOSED / S3 兜底**；逐条重放 3 条得 `rules=['K3','K9'] / verdict=PASS`，机制是 K9 精筛覆盖宽进。
  且该句本身**不在 frozen68**：它是 `onlyB(GP-C03)` / `onlyA(GP-A1)`，两版都 0 分（§1(c)(d)），按分解恒等式对 `+18` 无贡献。
- **间接影响（必须写）**：
  1. **`+18` 是清一色「放行」方向的增益**：18/18 都是 `72 chain=CATCH → 74 chain=PASS` 且 `expect=PASS`（本会话实跑）。K9 是「让 N13 的 A/B 精筛压过 R10 宽进」；`_gp_DESIGN.md:287` 明写「A1 正是这个代价的兑现」。⇒ `+18` 与「正类召回兜不住」是**同一个设计取舍的两面**：把误拦消掉 18 条，同时接受「N13 说放过就放过」的漏报风险，而 A1/A2/A3 就是该风险的实证（74 版 `FN=3`）。
  2. **方向偏倚使 `b=18,c=0` 更不像泛化证据**：若真有「算法更好」，应能同时改善正类召回；实际 `CATCH` 召回 36/36 两版不变（`COMPARABILITY_AUDIT.md:336-337`），只有 FP 单向下降。配合 §3(c)2 的 in-sample，说明 18 是**定向消 FP 的记账结果**。
  3. **若有任何一条增益是靠 fail-closed 碰巧得到**，则那一条应改判「不可归因」（本题铁律：不能追到具体机制的分算不可归因）。本会话已逐行核到 K3+K9 与 `unresolved=0`，**本例不成立**；但 fail-closed 兜底在别的评测里会制造「看似正确、实为恒真」的分数，故报分差时必须把「该分由哪条规则/哪列产生」列进声明清单（§5(c)）。
  4. **不得反向用来给 74 版加分**：V12/DG 的 `CATCH` 都是未实装或另一列，不能计入 `69/74`，也不能拿来说「其实能抓到双重否定」；`COMPARABILITY_AUDIT.md:345`、`CHAIN_VS_SINGLE.md:147-149` 已把 A1 列为「同漏，非负收益」。

---

## 5 第五步：结论与建议

### (a) 「+21 分」的诚实表述

**一句话版本**：
> 「+21 分里 3 分是把 3 条真值标注从 CATCH 改成 PASS（模型输出逐列未变，属修正基线）、18 分是在 68 条冻结考题上把合成裁决从三层朴素并集换成逐 span K1–K9 的配对差值（in-sample、72 版脚本未留盘、`chain` 列定义已变），新增 3 条全漏、删 1 条本来 0 分；**0 分可归因于算法改进**，两版 `48/72` 与 `69/74` 不可比，差值无因果含义。」

**一段解释版本**：
> 72 条版（朴素并集）在其自身语料上 `chain 48/72 = 66.67%`，74 条版（逐 span K1–K9）在其自身语料上 `chain 69/74 = 93.24%`，`raw delta 21 / +26.58pp`。按 id 对齐：共有 71 条，其中 3 条 `expect` 翻转、68 条冻结；74 独有 `GP-A1/A2/A3`、72 独有 `GP-C03`（与 `GP-A1` 同文本换 id 换族）。分解 `18+3+0+0=21`。3 条翻标（`GP-C05/C06/C07`）的 7 个判定列两版逐列相同，改标使它从 FN 变判对；按上游 A 类「检索结果非完成断言」的口径改得对，但标注手册未冻结封 SHA、无双盲 κ，且把 72 版基线从 48 修正为 51/72 后 `+21` 立刻缩成 `+18` ⇒ 这是**修正基线**而非改良。新增 3 条是按已知盲区定向构造、74 版 `chain=PASS` 全漏（`FN=3`），`deleted1` 本来 0 分，故两处 +0 与分母稀释无关（稀释只影响 pp 的 −2.59pp）。`frozen68` 的 18 分逐条可追到 `_gp_pipeline.py:168-171` 的 K9（72 版 20 条 FP 中修好 18 条），配对 `b=18 c=0`、exact binomial 双侧 `p=7.62939453125e-06`、CP 95% CI `[0.8147,1.0]`、bootstrap 配对差 CI `[0.1618,0.3676]`。但这是**在同一批、且为修这批失败样本而调出来的题上**的 in-sample 收益；18 条只有 16 个独立文本、聚 3 族（族级符号检验 `p=0.25`），`n_eff(ρ̄≈1)≈1`；`chain` 列两版导出定义不同（M 轴），72 版生成脚本全仓与 git 零命中（E 轴标「未验重跑」），按五轴机检为 `INDETERMINATE`。且 frozen68 内 `chain 66/68` 仍劣于 `n13 68/68`（`b=2 c=0 p=0.5`）。⇒ 唯一有内部效度的因果陈述是 `COMPARABILITY_AUDIT.md:340` 那一句；`+21` 与 `+26.58pp` **必须整体撤回**（`:301-313`）。

### (b) ★ 当前唯一站得住的数字

**只有 frozen68 上的配对 `b=18 / c=0 / n_discordant=18`，及其配套 `exact binomial 双侧 p=7.62939453125e-06`、CP 95% CI `[0.8147, 1.0]`、bootstrap 配对正确率差 `18/68 = 0.2647 [0.1618, 0.3676]`**——且必须以「描述性内部效度指标」而非「显著性/改良证据」的身份出现，并同时声明：in-sample、E 轴未验重跑、M 轴列定义已变、不得外推、不得写成「算法更好」。

其余全部站不住或只能作为留盘观测值：
- `48/72`、`69/74`、`+21`、`+26.58pp`：不可比（`COMPARABILITY_AUDIT.md:289-313`）；
- `51/72`（修正基线）：仅用于说明 3 分来源，两版仍不可比（§2(c)）；
- `chain 69/74 vs n13 71/74`：`b=2 c=0 p=0.5`（`COMPARABILITY_AUDIT.md:318`），不显著；
- 72 版 `chain 48/72 vs n13 68/72`：`p=1.9073486328125e-06`，但只关于**已弃用的朴素并集算法**（`:319`);
- 上游对齐实验 `b=0 c=3 p=0.2500`（`CHAIN_VS_SINGLE.md:112`）：**本会话未重跑，引用、标未验**；
- V12 第四层 `+1`（70/74）、DG `GP-A1_DG=CATCH`：设计实验、未实装、未验（`EVIDENCE_INDEPENDENCE.md:195`、`_dg_DESIGN.md:1-5`）。

### (c) 以后报分差必须同时给什么（清单）

来自 `COMPARABILITY_AUDIT.md:416-436`（16 项门禁）与 `:457-467`（九项数字声明），本会话按本题教训补 3 项（标 ★）：

1. **五轴 manifest**：`S/G/I/E/M` 每轴每侧 `path + sha256 + bytes`，`hashlib` 复算任一失配 `sys.exit(1)`；
2. **冻结语料**：逐行 `(id, 全文 sha256, tokens, expect, family, note)` 封 SHA，`n` 与类别先验写进 manifest（本次 72/74 分母与先验都变）；
3. **冻结标注手册**：「什么算正类」单独成文封 SHA，本轮禁止改 `expect`，翻标与改算法分两轮两版本号（本次 3 分即由此而来）；
4. **冻结评测脚本**：生成每份 JSON 的 `.py` 同批留盘封 SHA，**无脚本的 JSON 作废**（本次 72 版即反例）；
5. **冻结依赖**：谓词 / 词表 / 骨架 / 语料加载路径逐件指纹；
6. **变更单**：`changed_axis` 只能 1 个，old/new 指纹 + 复核人签字；多轴拒跑；
7. **全列重跑**：改一项即重算 `naive/r10/r12/n13/chain` 全部列，禁止复制旧列；
8. **统一输入契约**：所有层（含 chain 第二词表 `n13_tokens`）消费同一份 `tokens`，逐行断言（`_gp_regression.py:143-145` 的分叉须消除）；
9. **可比性 verdict 留盘**：`verdict ∈ {COMPARABLE, REPLICATION, COMPARABLE_CROSSED}` 且 `differing_axes ≤ 1`（或 2^k 格交叉实测齐备）；断言实现先过单轴反例自检；
10. **配对统计**：`b / c` + exact binomial 双侧 `p` + bootstrap CI + macro-F1 / 按 expect 分报 FP/FN；禁止只报点估计；
11. **归因范围 scope**：写死 id 列表 + 「不得外推」；
12. **分母口径声明**：每个 `X/N` 带 `n`、CATCH/PASS 先验、被比较列的**导出规则**；禁止用 `→` 连接不同 `n` 的数字；
13. **留盘/复现状态**：脚本是否留盘、是否两侧全量重跑、独立复核 verdict、未验项逐条列出；
14. **盲留出**：要写「更好/更差」必须有出题人≠改规则人≠批卷人的封 SHA test 集 + Cohen's κ，且失败回灌样本（N19–N26 / GP-A）只进 train；
15. **★ 每一分的逐行归因**：`Δ` 必须能拆到「哪个 id、哪一列、由哪条规则（K1–K9 / S3 DEFAULT / 翻标 / 增删）产生」；追不到具体行的分一律记「不可归因」；
16. **★ 选择过程与有效样本量**：报调参日志 / 预注册、`n_eff = n/(1+(n−1)ρ̄)` 或按独立文本/族聚簇后的符号检验 `p`；in-sample 的 `p` 必须标「描述性、非生产置信界」；
17. **★ 兜底与恒真机制披露**：若某分来自 `fail-closed` / `ABSENT→PASS` / `spans=0` 死分支 / 恒 CATCH 兜底，单列标出并判「不可归因于语义识别」（本任务 §4(c)）；
18. **收尾**：复算全部只读件指纹零漂移、`git status` 核对、不 commit 不 push。

### (d) 这条工作判不了什么（如实列）

1. **判不了「算法有没有改进 / 能不能泛化」**：无物理隔离盲留出集、无 κ、train=test（`CHAIN_VS_SINGLE.md:129,131`、`COMPARABILITY_AUDIT.md:357`）；本会话**未跑**任何留出集实验。
2. **判不了「合成链 vs 单层谁更好」**：`COMPARABILITY_AUDIT.md:328` 明写「目前没有任何站得住的结论」；frozen68 内 `p=0.5`，上游对齐 `p=0.25`（引用未重跑）。
3. **判不了「72 版 48/72 是怎么算出来的」**：72 版生成脚本全仓 + git 历史零命中（本会话 `find`/`git log` 实跑），E 轴 `INDETERMINATE`，只重算 JSON 内部自洽；**未验重跑**。
4. **判不了「除合成裁决外其余输入相同」**：仅由「四个单层列逐行相同」推断，非脚本级复核（`COMPARABILITY_AUDIT.md:343`）。
5. **判不了 3 条翻标的「绝对正确性」**：标注手册未冻结封 SHA、无双盲 κ、原始派发任务书未留盘（`COMPARABILITY_AUDIT.md:421,444-450`）；只能判「与上游 A 类口径一致、合理」，不能判「已证实正确」。
6. **判不了「GP-C03→GP-A1 为什么换 id」的书面动机**：盘上无变更单/裁决记录，本会话 `grep` 未找到；只能给字段级事实与分类纠错推断，标**未验**。
7. **判不了第 91 字之后的正文是否改动**：`text_head` 是 `text[:90]` 截断头（`_gp_regression.py:159`），`COMPARABILITY_AUDIT.md:141` 明写「第 91 字之后属未验」；本会话未重跑该补验。
8. **判不了 in-sample 修正后的真实 `p`**：调参搜索次数 `M` 无日志可定（只算出 Bonferroni 临界 `M*=6553.6`）、`ρ̄` 无盲留出数据可估、post-selection 条件分布未建；§3(d) 给的是**方案**，不是已算出的修正值，标**未验**。
9. **判不了「74 版能抓到 19 式双重否定」**：`chain=PASS`（本会话实跑重放）；V12 是 S3 兜底、DG 是未实装内存 Shim，均非 74 版评分列。
10. **判不了任何真机/运行时行为**：铁律零真机、零采样，本会话未启动任何进程、未读内存；所有结论只关于离线盘上 JSON 与源码。
11. **判不了上游对齐实验与 `_cmp_assert.py` 修正版**：`CHAIN_VS_SINGLE.md:112` 的 `b=0 c=3 p=0.25` 系引用、`_cmp_assert.py` 修正判据「未实装、未实跑、未验」（`COMPARABILITY_AUDIT.md:266`）；本会话按「只做分解与统计」未改任何脚本。
12. **判不了「+26.58pp 里有多少是分母稀释」之外还要归因到哪个分项**：pp 分解里 −2.59pp 是 `n` 变化对 `69` 的稀释，跨分项不可加（不同分母），本会话只给算式与不可加性说明，不做分项 pp 归因。

---

## 6 未验项汇总（不补造）

- 72 版生成脚本重跑（未验，脚本不在盘）；
- 原始派发任务书 / 换 id 书面动机（未验，未留盘）；
- 标注手册冻结指纹与双盲 Cohen's κ（未做）；
- 第 91 字之后正文是否改动（未验）；
- 正式盲留出集、post-selection 修正后 `p`、`M`、`ρ̄`（未做/未定）；
- 上游 74 条完整对齐实验（`CHAIN_VS_SINGLE.md:112`，引用未重跑）；
- `_cmp_assert.py` 修正版与 2×2 交叉实测（未实装/未跑）；
- V12 第四层与 DG 生成式是否实装进交付链（明写未实装）。

**复核 verdict**：本件为独立分解与统计，未经第三方复核，按项目既有口径（如 `COMPARABILITY_AUDIT.md:389`）如实标 **`unconfirmed`**。
