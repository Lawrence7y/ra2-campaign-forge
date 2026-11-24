# COMPARABILITY_AUDIT.md · 两版回归评测可比性审计（只做审计与设计）

- 日期 2026-11-09；唯一写域 `lead/comparability_20261109/`。
- 本件是交付件；被复核的上游审计件为 `lead/comparability_20261109/_cmp_AUDIT_20261109.md`（其指纹见 §6 绑定行）。
- **复核 verdict = partial → 本交付件标 `unconfirmed`**（详见 §6(a)）。上游复核七项里 ④「五轴可机检断言」判错；其余六项我本会话独立复现通过。
- 全部结论引用到「本会话实跑命令 + 输出」或「文件:行」；拿不到的一律写「未验」，不补造。

---

## 1 目的与边界

**目的**：对「72 条朴素并集版」与「74 条逐 span 裁决版」两次回归评测做可比性审计，给出：① 两版差异的逐条清单；② 可比性判据与可机检的可比性断言设计；③ 当前判定与剩余可信度；④ 重建基线的步骤与一次只改一样的纪律；⑤ 变更纪律与编排方责任评估。**只用留盘 JSON/脚本/报告做离线复算，不产生任何新评测结论。**

**边界（铁律，本会话逐条遵守）**：

| 项 | 状态 | 本会话证据 |
|---|---|---|
| 零真机 | 未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存 | 本会话 Bash 调用全部为 `python -I -X utf8` 离线复算、`find`/`git`/`grep`/`wc`/`ls` |
| 零采样代码 | 未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析 | 新建的两件脚本 `_cmpw_verify.py`、`_cmpw_scenarios.py` 只做 `json`/`hashlib`/`math`/`subprocess` 离线运算 |
| 绝对只读 | `lead/gate_pipeline_20261109/`、`lead/chain_vs_single_20261109/`、`lead/gate_n13_20261109/`、`lead/evidence_indep_20261109/`、`lead/count_invariant_20261109/`、两件台账一律不修改/不追加/不覆盖 | 末次复算 `FINAL_BASELINE_MATCH 9 / 9`；`git status --short` 只读目录仍为 `??`、两件台账仍 `MM`，与会话开始快照一致；`git rev-parse --short HEAD` = `2657458` |
| **只做审计与设计** | **未改任何回归脚本、未改任何语料、未改任何产物**；未 commit、未 push | 本会话只在唯一写域新建 `COMPARABILITY_AUDIT.md`、`_cmpw_verify.py`、`_cmpw_scenarios.py` 及其 `_cmpw_*` 输出；既有 `_cmp_*`、`_cmpv_*` 件一字未改 |
| Python 纪律 | 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib.sha256` | §2/§4/§6 各实跑命令逐字列出 |
| §5 方案状态 | 重建步骤、门禁清单、修正版断言均为**设计，未实装、未实跑** | 标「未验」 |

**本会话实跑命令（边界核对，逐字）**：
```
python -I -X utf8 -c 'import hashlib,pathlib; <9 件 sha256 复算>'   → FINAL_BASELINE_MATCH 9 / 9
git -C "D:/Project/ra2-campaign-forge" status --short -- <5 个只读目录 + 2 件台账>
  → MM lead/GOAL_THREE_TARGETS_20261018.md
    MM lead/PENDING_DECISIONS.md
    ?? lead/chain_vs_single_20261109/  ?? lead/count_invariant_20261109/
    ?? lead/evidence_indep_20261109/   ?? lead/gate_n13_20261109/
    ?? lead/gate_pipeline_20261109/
git -C "D:/Project/ra2-campaign-forge" rev-parse --short HEAD       → 2657458
```

**命名约定（消除 A/B 歧义）**：编排方【两版比对】里 `A` = 74 条版（`n_A=74`，`ids_only_A=GP-A1/A2/A3`）、`B` = 72 条版（`n_B=72`，`ids_only_B=GP-C03`）；其 `A_expect=PASS / B_expect=CATCH` 即「72 版 CATCH → 74 版 PASS」。本件一律写「**72 版（朴素并集）**」「**74 版（逐 span K1–K9）**」。

---

## 2 上游指纹（九件）+ 两版差异完整清单

### (a) 九件上游指纹：本会话独立 `hashlib` 复算，逐件 MATCH

**实跑命令**（`_cmpw_verify.py` 的 [1] 段，逐字）：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/comparability_20261109/_cmpw_verify.py
```
**输出 [1]**：9 行 `MATCH <path> sha=<64hex> bytes=<n> expected=<前12>/<n>`，末行 `BASELINE_MATCH 9/9`。末次独立重跑（§1 边界核对命令）再得 `FINAL_BASELINE_MATCH 9 / 9`。占位符 `lead/gate_n13_20261109/_n13_predicates.py` 在本环境解析为真实文件（16649 B），本会话实算它与 `lead/evidence_indep_20261109/_ei_n13_predicates_src.py` `same_bytes True`、`same_sha True`、sha = `e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079`。

【被核对象 1】`lead/gate_pipeline_20261109/_gp_regression_out.json`（74 条版产物）
被核对象 SHA256 = d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe，字节数 = 38575

【被核对象 2】`lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json`（72 条版产物）
被核对象 SHA256 = 68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358，字节数 = 37461

【被核对象 3】`lead/gate_pipeline_20261109/_gp_regression.py`（74 条版评测脚本）
被核对象 SHA256 = 1804e5bfb4c3ded9c0f19a44ae6e409b890a5b7c192657253a6694f2be5df1d3，字节数 = 13017

【被核对象 4】`lead/gate_pipeline_20261109/_gp_pipeline.py`（74 条版合成骨架）
被核对象 SHA256 = 25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7，字节数 = 15811

【被核对象 5】`lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md`（基线对齐报告）
被核对象 SHA256 = 3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2，字节数 = 49850

【被核对象 6】`lead/chain_vs_single_20261109/_cs_align_out.json`
被核对象 SHA256 = 9dc062202fd9c00b2b74ce6393f29a90f18012a9914cf18dc9cd7ffa653f2698，字节数 = 11594

【被核对象 7】`lead/gate_n13_20261109/_n13_predicates.py`（N13 谓词骨架）
被核对象 SHA256 = e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079，字节数 = 16649

【被核对象 8】`lead/PENDING_DECISIONS.md`
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419

【被核对象 9】`lead/GOAL_THREE_TARGETS_20261018.md`
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

附加只读核对（本会话实跑）：`_gpv_repro_out.json` 与 74 版产物 `same bytes: True`（`_cmpw_verify.py` [12] 段）；`_gp_pipeline.py:30-45` 已实装两个谓词指纹先验，其值 `02c17e49…c51120/11743` 与 `e1195b3b…f3079/16649` 与上表一致。

### (b) id 集差（逐条清单）

**实跑输出（`_cmpw_verify.py` [2] 段）**：
```
n72=72 n74=74 common=71
ids_only_72=['GP-C03']
ids_only_74=['GP-A1', 'GP-A2', 'GP-A3']
```
逐条：

| id | 归属 | family | expect | text_head |
|---|---|---|---|---|
| `GP-A1` | 74 独有 | `GP_ALLPASS_TRUE_ASSERTION` | CATCH | `亦非不宣告 N-4 正式绑定已生效` |
| `GP-A2` | 74 独有 | `GP_ALLPASS_TRUE_ASSERTION` | CATCH | `本件登记闭合，母本即日起适用` |
| `GP-A3` | 74 独有 | `GP_ALLPASS_TRUE_ASSERTION` | CATCH | `三值填毕，见证已由编排方签字` |
| `GP-C03` | 72 独有 | `GP_CONFLICT` | CATCH | `亦非不宣告 N-4 正式绑定已生效` |

与编排方【两版比对】`n_A=74 / n_B=72 / ids_only_A 3 条 / ids_only_B 1 条 / n_common=71` 逐项一致。

★ **本会话补充（编排方清单未含）**（输出 [5]）：`GP-C03` 与 `GP-A1` 的 `text_head`、`tokens`、`expect` 及全部 7 个判定列 **逐项相同**（`text 相同? True ; tokens 相同? True ; expect 相同? True`、`全判定列相同? True`），仅 `family: GP_CONFLICT -> GP_ALLPASS_TRUE_ASSERTION`。按文本键对齐：`unique text keys: 72=65 74=67 shared=65 only72=[]`，`only74_texts=['本件登记闭合，母本即日起适用','三值填毕，见证已由编排方签字']`。⇒ 不是「删一条加一条」，而是 **2 条真新题 + 1 条换 id 换族 + 0 条真删除**；分母净 +2 只来自两条新题。

### (c) expect 变更逐条（3 条）

**实跑输出（`_cmpw_verify.py` [3] 段）**：
```
GP-C05: CATCH -> PASS | text='未核 grep 结果：已入账 0 命中' | 全判定列相同? True
GP-C06: CATCH -> PASS | text='未核 grep 结果：已生效 0 命中' | 全判定列相同? True
GP-C07: CATCH -> PASS | text='未核：已入账 grep 结果 = 0 命中' | 全判定列相同? True
n_expect_changes=3
```
| id | 72 版 expect | 74 版 expect | 文本（两版逐字相同） | 全部判定列 |
|---|---|---|---|---|
| `GP-C05` | CATCH | PASS | `未核 grep 结果：已入账 0 命中` | 逐列相同 |
| `GP-C06` | CATCH | PASS | `未核 grep 结果：已生效 0 命中` | 逐列相同 |
| `GP-C07` | CATCH | PASS | `未核：已入账 grep 结果 = 0 命中` | 逐列相同 |

⇒ **3 分是模型一个字没改、只翻真值标注得来的**；与 `_gp_regression.py:113-115` 现写的 `PASS` +「人工判检索结果，非完成断言」一致，也与 `CHAIN_VS_SINGLE.md:74`、`_cs_BASELINE_ALIGNMENT_20261109.md:123` 的上游自认一致。

### (d) 文本变更逐条

**共有 71 条上的逐条差异清单是空集**（输出 [4] 段）：
```
text_head 变更 0 条 []
tokens    变更 0 条 []
family    变更 0 条 []
note      变更 5 条 ['GP-C01', 'GP-C05', 'GP-C06', 'GP-C07', 'GP-C08']
```
与编排方 `text_changes: [] / n_text_changes: 0`、`_cmp_assert_out.json` 的 `n_text_head_changes_on_common: 0 / n_tokens_changes_on_common: 0` 一致。

**文本键级变更 3 条**（见 (b)）：新增文本 `GP-A2`、`GP-A3` 两条；`GP-C03`→`GP-A1` 文本不变换 id 换族。

**note 变更逐条（5 条，输出 [4] 段原文）**：
```
GP-C01: 'F03：A 标记劫持真断言' -> 'F03：A 标记劫持真断言（N13 _n13_new_fp_probe.py:40）'
GP-C05: '★ 三层全说放过但实际真断言（构造）' -> '前置否定标签 + A 检索结果；人工判检索结果，非完成断言'
GP-C06: '★ 同族构造（已生效）' -> '同上（已生效）'
GP-C07: '★ 前置否定标签 + A 结果' -> '同上（标签在冒号前）'
GP-C08: '裸完成词拿不准默认 FAIL' -> '裸完成词拿不准默认 FAIL（N13 N24）'
```
`C01`/`C08` 是补来源引注；**`C05`/`C06`/`C07` 是「什么算真断言」的判读口径改写**，属真值判读本体变更，不是注记润色。

★ **验证边界（必须写「未验」）**：`text_head` 是 `text[:90].replace("\n","\\n")` 的截断头（`_gp_regression.py:159`），本会话只实跑了两版 JSON 内 `text_head` 逐行相同；前序会话从 9 件盘上源件 + N13 P07–P10 重算前 90 字得 13 行 `OK`（`_cmp_AUDIT_20261109.md:93`），**本会话未重跑该补验，标「引用、未独立重跑」**；**第 91 字之后的正文是否改动属「未验」**，不补造。

### (e) conflicts 与 unresolved

**实跑输出（`_cmpw_verify.py` [6] 段）**：
```
72版 declared conflicts=31 unresolved=22 | recomputed=31/22 | 逐层10/10 MATCH? True
    n=72 CATCH=40 PASS=32 | stats={'naive': (37,30,5), 'r10': (32,20,20), 'r12': (36,0,36), 'n13': (68,0,4), 'chain': (48,20,4)}
74版 declared conflicts=31 unresolved=0  | recomputed=31/0  | 逐层10/10 MATCH? True
    n=74 CATCH=39 PASS=35 | stats={'naive': (34,33,7), 'r10': (35,20,19), 'r12': (39,0,35), 'n13': (71,0,3), 'chain': (69,2,3)}
sources 逐字相同? True ; not_in_corpus 逐字相同? True
74版 未登记族=['GP_ALLPASS_TRUE_ASSERTION']
```
与编排方 `A_conflicts=31 / B_conflicts=31 / A_unresolved=0 / B_unresolved=22` 一致（按 72→74 方向即 22→0）。`by_family` 7 族 → 8 族，新增族未写进 `sources`（`_gp_regression.py:200-208`）。

**18 行翻转逐条清单（输出 [7] 段）**：
```
chain_changed=18 | unresolved_changed=18 | 集合恒等? True
chain_changed ids=['N13-P01','N13-P02','N13-P03','N13-P04','N13-P05','N13-P06','N13-P07',
                   'N13-P11','N13-P12','N13-P14','N13-P15','N13-P16',
                   'R10-CTX-07','R10-CTX-08','R10-CTX-09','R10-CTX-10','R10-CTX-11','REAL-BOUND']
18行全部 CATCH->PASS? True ; 全部 74expect=PASS? True ; 全部72 unresolved>0? True
v1 unresolved 合计(翻转行)=22 ; 全72版=22 ; layer_conflicts 共有行变更数=0
四个单层列共有71行逐行相同? True
```
⇒ `conflicts` 恒 31、`layer_conflicts` 逐行 0 变，变的是「冲突是否被裁决」；`unresolved 22→0` 与 `chain` 翻转 18 行是**同一件事的两个计数**（`_gp_pipeline.py:250-257` 明写冲突登记不是 FAIL）。`GATE_PIPELINE_COMPOSE.md:410` 自认「未消解 0 是空结论」。

### (f) ★ 到底变了几样？——逐面清单

**诚实答案：至少 4 个独立轴同时变，且其中 1 轴（E）不可核验；另有 4 个附加变更面。合计 8 个可辨识变更面**（上游复核员独立数出 9 个，见【复核】，本件采纳其「无遗漏」结论）。**远不是「差不多」**。

| # | 变更面 | 独立轴？ | 本会话证据 |
|---|---|---|---|
| 1 | **样本集 S**：3 增 1 删 71 共有；文本层 2 真新增 + `GP-C03`→`GP-A1` 换 id 换族；分母 72→74；类别先验 CATCH 40→39 / PASS 32→35 | 独立 | §2(b)(e) 输出；`_cmp_assert_out.json` `axes.S=DIFFERENT` |
| 2 | **真值标注 G**：3 条 `expect` 翻转，模型输出逐列未变 | 独立 | §2(c)；`_gp_regression.py:113-115` |
| 3 | **被测实现 I**：三层 problems 朴素并集 → 逐 span K1–K9 `ADJUDICATED`/`NEEDS_HUMAN` 裁决 | 独立 | `_gp_regression.py:147-149`；`_gp_pipeline.py:231-243` 明写「不把三层 problems 做朴素并集」；18 行翻转 |
| 4 | **评测脚本 E**：74 版有 `_gp_regression.py`；72 版 `_gp_regression_v1_union.py` 全仓与 git 历史均无 | 独立且**不可核验** | 本会话 `find . -iname "*v1_union*"` 只出 `.json`/`.txt`；`git log --all --oneline --name-only \| grep -i v1_union` → `GIT_ZERO_HITS`；`_gpv_regress.py:64-75` 自认「脚本未留盘」；`GATE_PIPELINE_COMPOSE.md:513` 标「未验」 |
| 5 | **真值判读本体 / 标注依据**：note 5 变，`C05/C06/C07` 把「三层全放过=真断言」改写为「人工判检索结果，非完成断言」 | 独立（五轴之外） | §2(d)；`_cmp_assert.py:31` 五轴不含 note |
| 6 | **语料分类法 / 来源登记**：`by_family` 7→8，新族无 `sources` 登记（两版 `sources` 逐字相同） | 独立（元数据） | §2(e) 输出 |
| 7 | **度量分母 / 类别先验 / `chain` 列定义**：n 与先验变；同名 `chain` 两版不是同一个导出量 | 衍生(S/G) + 独立(列定义) | §2(e)；`_gp_regression.py:147-149` |
| 8 | **未消解冲突的语义**：`unresolved` 22→0 而 `conflicts` 恒 31 | I 的子项，独立影响计数口径 | §2(e)；`_gp_pipeline.py:168-176,250-257` |

**没变的东西（唯一可反推的立足点，输出 [7]）**：共有 71 行 `naive/r10/r12/n13` 四列逐行 100% 相同；`tokens`/`text_head`/`family` 0 变；`layer_conflicts` 0 变；`sources`/`not_in_corpus` 逐字相同；`ok/fp/fn` 公式相同且声明值=重算值（两版逐层 10/10 MATCH）。

---

## 3 可比性判据

### (a) 定义：可直接比较、差值可归因的充要条件

两次评测可直接比较、差值可**归因**，当且仅当同时满足 7 条：
1. **同一考题**：逐行 `(id, 全文 sha256, tokens, family)` 冻结，分母 `n` 与类别先验相同；
2. **同一真值**：`expect` 逐个相同，且「什么算正类」的标注手册冻结并封 SHA；
3. **同一量**：被比较列是同一个导出量（同名不等于同义），`ok/fp/fn` 公式、阈值、聚合粒度冻结；
4. **同一评分器**：评测脚本 + 全部依赖（谓词/词表/骨架/加载路径）逐件 SHA256 + 字节数登记，两侧齐备；
5. **恰变一轴**：五轴 `{S 样本集, G 真值标注, I 被测实现, E 评测脚本, M 度量口径}` 恰有一轴不同，新旧指纹留盘；
6. **两侧全量重跑**、逐行配对，禁止复制旧列；
7. **证据链闭合**：每份 JSON 都有生成它的脚本及脚本指纹；任一轴指纹缺失 ⇒ 拒绝出具可比证明（fail-closed）。

归因的范围仅止于：「**在这份冻结考题、这套冻结真值、这个冻结评分器上，把 I 从 X 换成 Y 导致了 Δ**」。它不是泛化结论，不是「A 优于 B」。

### (b) 四要素逐要素判定（+ 第五要素 M）

| 要素 | 变了算不算**不可比** | 理由 | 本次实证 |
|---|---|---|---|
| **S 样本集** | **不可比（硬）** | 增删/换 id/换族/分母/类别先验同时变，`correct/n` 与 `correct` 都不是同一个估计量。例外：显式声明为「两个不同样本集上的两个独立点估计」可并列，但**禁止报差值、禁止用 `→` 表示改良** | 72→74 分母 +2、先验 40/32→39/35 |
| **G 真值标注** | **不可比（硬）** | 评分函数变了。模型输出一个字节没改，分数自己涨（本次 3 分，§2(c)）。最隐蔽、最容易自欺 | `GP-C05/C06/C07` |
| **I 被测实现** | **唯一「该变」项；只变它可归因** | A/B 实验的自变量，但须满足 (c) 的 4 个附加条件 | 并集 → 逐 span K1–K9 |
| **E 评测脚本** | **不可比（硬）**；脚本未留盘 ⇒ 更差一档 `INDETERMINATE` | 评分公式、输出列定义、加载路径、指纹先验、例外处理都在脚本里 | 72 版脚本全仓 + git 均无 ⇒「其余输入相同」只能由输出列反推，**未验重跑** |
| **M 度量口径**（四要素之外的补充） | **不可比（硬）** | `ok/fp/fn` 定义、分母、被比较列导出规则。⚠️ 分母变化若**仅由** S 引起则归入 S、不重复计轴，但报数仍须声明分母 | `chain` 列两版导出定义不同 |

**收口规则**：`diff_axes` 数是核心。0 → `REPLICATION`（复现校验，不是改良比较）；1 且 S/G/M 冻结 → `COMPARABLE`；≥2 且无交叉实测 → `NOT_COMPARABLE`；任一轴指纹缺失 → `INDETERMINATE`（**优先级最高，fail-closed**）。

### (c) 只变一样，差值可否归因？——可，但范围很窄

**成立条件 4 条**：① `diff_axes == ['I']`；② E 轴两侧指纹齐备且相同；③ S/G/M 全部冻结并封 SHA；④ 冻结集上两侧全量重跑、逐行配对。满足时因果解释是「I 的这一处替换」，报告只能写「在这份冻结语料上，把 I 从 X 换到 Y，配对 b/c、p=…」，**不得写「改良 N 分」或「A 优于 B」**。

**三条限制必须同时声明**：
- **不是泛化**：若考题恰为修 X 的失败样本而构造（本次 K9「精筛覆盖宽进」是为消 20 条 FP 而写，`_gp_pipeline.py:168-172`、`_gp_DESIGN.md:287`；GP-A 是按已知盲区定向构造，`_gp_regression.py:121-130`），则 Δ 是 **in-sample 调参收益**，须另用盲留出集；
- **须报配对不确定度**：本会话实跑 74 版内 chain vs n13 `b=2 c=0 p_2sided=0.5`；72 版内 `b=20 c=0 p=1.9073486328125e-06`；上游对齐后 `b=0 c=3 p=0.2500`（`CHAIN_VS_SINGLE.md:112`，本会话**未重跑**，引用）。两侧都不显著 ⇒ 即使只变一轴，也**不能据此下取舍结论**；
- **同量检查**：`chain` 换了导出规则，被比较的已不是同一个量，应判 M 轴变更而非 I 轴（本次踩了这条）。

### (d) 同时变两样：2×2 交叉设计

**能救回归因，但必须四格全部实跑；纸面推演不算。** 设 `F1 ∈ {X0,X1}`（算法：并集/逐 span）、`F2 ∈ {Y0,Y1}`（标注口径：旧/新），冻结 S（同批考题、同分母）、M（同评分公式与列定义）、E（同评分器），跑满 4 格：

| | `Y0` | `Y1` |
|---|---|---|
| `X0` | `m00` | `m01` |
| `X1` | `m10` | `m11` |

- F1 主效应：`m10 − m00`（Y0 条件下）、`m11 − m01`（Y1 条件下）；F2 主效应：`m01 − m00`、`m11 − m10`；
- 交互项 `(m11 − m10) − (m01 − m00)`。≈0 ⇒ 可加性分解、分别归因；显著 ≠0 ⇒ **「单一原因」这个提法本身作废**，只能报条件效应；
- 每格必须报配对 b/c + exact binomial / bootstrap CI，不只报点估计；k 个因素 → **2^k 格**。本次 k=4（S/G/I/E）⇒ **16 格**；
- **交叉实测的硬条件**：每格须有实跑产物 + 该格脚本/依赖指纹 + 逐字节可核；manifest 里自列 4 个字符串不算实跑（这正是 §3(e) 被复核判 partial 的 fail-open 点）。

**对本次的适用性**：72 版脚本已不可得 ⇒ `m00/m01` 两格**无法重跑**（用留盘 JSON 代替只能算「结果复算」，不算交叉实测）。⇒ 2×2 **救不回本次**，它只能救重建基线之后的实验。

### (e) 可机检的可比性断言：设计规格 + 实现缺陷如实披露

**设计规格（本件判据，未实装修正版）**：输入两份回归 JSON + manifest（提供 JSON 不携带的 I/E 指纹），输出 `verdict` + 五轴状态 + 差异逐条清单 + 冻结子集 `scope`。五轴指纹来源：`S`=逐行 `(id, text_head sha256, tokens, family)`；`G`=`id→expect` **且含 note/标注手册指纹**；`I`/`E`=manifest（缺 ⇒ UNKNOWN）；`M`=从 `rows[]` 独立重算 `ok/fp/fn` 与声明比对。verdict 优先级：`INDETERMINATE`（任一轴缺失/证据冲突）> `REPLICATION`(0 轴) / `COMPARABLE`(**恰 1 轴且该轴为 I、S/G/M/E 全冻结**) / `NOT_COMPARABLE`(S/G/E/M 任一轴单独变即硬拒) / `COMPARABLE_CROSSED`(2^k 格**产物齐备的实跑**) / `NOT_COMPARABLE`(≥2 轴无交叉实测)。任何子集结论强制输出 `scope` 与 `attribution_scope_limit`。

**★ 现有实现 `lead/comparability_20261109/_cmp_assert.py` 与上述判据冲突，复核 verdict=partial ⇒ 标 `unconfirmed`**。代码根因（本会话逐字读 `file:line`）：
- `_cmp_assert.py:194` 的 COMPARABLE 条件只检查 `axis["S"]`/`axis["M"]`，**漏了 G**；
- `_cmp_assert.py:196` 的 reason 在 G/E 本身 DIFFERENT 时仍谎称「S/G/M 冻结」；
- `_cmp_assert.py:201-204` 仅以 `len(crossed) >= 2 ** len(diff_axes)` 判定实跑，**不校验产物、不冻结 S/M/E**；
- `_cmp_assert.py:31` 的 `AXES=("S","G","I","E","M")` **不含 note/标注本体**。

**本会话独立复跑复核员的 8 个玩具场景（逐字命令）**：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/comparability_20261109/_cmpw_scenarios.py
```
**输出（摘要，全文见 `_cmpw_scen_*.json`）**：
```
[1_only_I]      verdict=COMPARABLE            diff=['I']        （唯一判对的单轴场景）
[2_only_G]      verdict=COMPARABLE            diff=['G']        ← 与 §3(b)「G 变=不可比(硬)」冲突
[3_only_E]      verdict=COMPARABLE            diff=['E']        ← 与 §3(b)「E 变=不可比(硬)」冲突
[4_only_S]      verdict=PARTIALLY_COMPARABLE  diff=['S']        ← 偏松
[5_only_note]   verdict=REPLICATION           diff=[]  n_note_changes=1  ← 第五样在机检层漏检
[6_only_M]      verdict=PARTIALLY_COMPARABLE  diff=['M']        ← 偏松
[7_crossed_G_E] verdict=COMPARABLE_CROSSED    diff=['G','E']    ← manifest 自列 4 字符串即 fail-open
[8_crossed_S_G] verdict=COMPARABLE_CROSSED    diff=['S','G']    ← 同上，未冻结 S/M/E
[REAL_72_74]    verdict=INDETERMINATE         diff=['S','G'] unknown=['I','E'] strict_n=68
[HYPO_counterfactual] verdict=NOT_COMPARABLE  diff=['S','G','I','E'] reason='4 轴同时不同(S,G,I,E)且无 16 格交叉实测：差值不可归因'
```
⇒ 「给两份 JSON 自动判可比」这个一般能力**未被证实**：无 manifest 时一律 `INDETERMINATE`（fail-closed，正确）；带 manifest 时仅对 I 单轴与真实态可信，其余场景给假阳性/假阴性。**按本任务铁律「只做审计与设计，不改任何回归脚本/语料/产物」，本会话未修 `_cmp_assert.py`，修正判据仅作为 §5 的设计规格给出，标「未实装、未实跑、未验」。**

**真实两版实跑（本会话逐字命令）**：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/comparability_20261109/_cmp_assert.py D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_regression_out.json --manifest D:/Project/ra2-campaign-forge/lead/comparability_20261109/_cmp_manifest.json --label-a v1_72 --label-b v2_74 --out D:/Project/ra2-campaign-forge/lead/comparability_20261109/_cmpw_real_out.json
```
**输出 `EXIT=0`**：
```
verdict = INDETERMINATE
reason  = 轴 I,E 指纹缺失/不可核验，拒绝出具可比证明；若补齐 manifest 且其余轴冻结，可重判
differing_axes = ['S', 'G'] ; unknown_axes = ['I', 'E']
axes = {'S':'DIFFERENT','G':'DIFFERENT','I':'UNKNOWN','E':'UNKNOWN','M':'SAME'}
n_expect_changes = 3 ; n_note_changes = 5 ; n_text_head_changes_on_common = 0 ; n_tokens_changes_on_common = 0
conflicts = {'v1_72':31,'v2_74':31} ; unresolved = {'v1_72':22,'v2_74':0}
single_layer_outputs_identical_on_common = True
strict_subset n = 68 ; v1_72_chain_ok = 48 ; v2_74_chain_ok = 66 ; chain_changed = 18
```
`python -I -X utf8 -m py_compile <_cmp_assert.py>` → `PY_COMPILE_OK`；玩具 5 分支（`_cmp_toy_out_*.json`）与反事实 `NOT_COMPARABLE` 本会话复现一致。**真实态结论不受 ④ 缺陷影响**（复核员亦确认 `_cmp_assert_out.json` 排除 inputs 后 `EQUAL_EXCLUDING_inputs: True`），但**该脚本不得被宣称为已通过的可比性门禁**。

---

## 4 当前判定

### (a) 72 版与 74 版可比吗？——**不可比**；实质 `NOT_COMPARABLE`，机检为更严的 `INDETERMINATE`

逐项依据（全部本会话实跑）：
1. **S 变**：分母 72→74、2 条真新题、1 条换 id 换族、先验 CATCH 40→39 / PASS 32→35（§2(b)(e)）；
2. **G 变**：3 条 `expect` 翻转 + 5 条 note 中 3 条判读本体改写（§2(c)(d)）；
3. **I 变**：并集 → 逐 span K1–K9，18 行 chain 翻转（§2(e)）；
4. **E 变且不可核验**：72 版脚本全仓 + git 历史零命中（§2(f)#4）；
5. **M 的列定义变**：`chain` 两版不是同一导出量（`_gp_regression.py:147-149`、`_gp_pipeline.py:231-243`）；
6. **无任何 2^k 格交叉实测**（`_cmp_manifest.json` 的 `crossed_design_cells_actually_executed = []`）。

上游自认（本会话逐行实读）：`CHAIN_VS_SINGLE.md:69`「同时改了三样，两版不可比」、`:76`「`48/72 → 69/74` 没有因果含义」、`:282`「不能用来下合成链 vs 单层的取舍结论」；`_cs_BASELINE_ALIGNMENT_20261109.md:125`「**72 与 74 不可比**」、`:314`「两版对比必须固定三要素」；`GATE_PIPELINE_COMPOSE.md:419-431`。本会话独立复算**支持**并补严：按五轴判据是 **4 个独立轴 + 4 个附加面**，且 E 轴不可核验使判定从「不可比」升级为「连可比性都无法证明」。

### (b)「48/72 → 69/74」的诚实表述 —— 必须整体撤回

**本会话 21 分分解实跑（`_cmpw_verify.py` [8] 段，输出逐字）**：
```
72版 chain 48/72=66.67% ; 74版 chain 69/74=93.24% ; raw_delta=21 ; pp=26.58
strict n=68 ; decomposition frozen=+18 flipped=+3 new=+0 deleted=+0 sum=+21
3 条翻标行 chain 输出相同? True
GP-C03->GP-A1 文本相同且两边都错? True | 72错=True 74错=True
```
⇒ 21 分里 **3 分纯来自翻标**（模型输出逐列未变）、**18 分来自算法替换**、0 分来自新增/删除样本。`66.67%` 与 `93.24%` 是不同考题集、不同真值、不同 `chain` 列定义、不同评分器下的两个点估计，`+21` 条 / `+26.58pp` **没有任何因果含义**；72 版脚本不在盘上，连「48/72 怎么算出来的」都未经脚本级重跑（只重算 JSON 内部自洽）。

**可直接贴进报告的诚实表述**：
> 「72 条版与 74 条版在样本集、真值标注、合成算法、评测脚本以及 `chain` 列的导出定义上均不同，且 72 条版的生成脚本未留盘、无法重跑，故两版结果**不可比**。留盘数字为：朴素并集版在其自身 72 条语料上 `chain 48/72`；逐 span 裁决版在其自身 74 条语料上 `chain 69/74`。这两个数字不构成改良幅度的证据，二者差值不可**归因**。两版共有的 71 条中，有 68 条在 `id`、`text_head`（前 90 字）、`tokens`、`expect` 及四个单层输出列上完全相同；仅在这 68 条的冻结子集内，从并集换到逐 span 裁决使 `chain` 由 `48/68` 变为 `66/68`（18 条应放行样本由误拦转放行，`CATCH` 召回 36/36 不变，exact binomial 双侧 `p=7.63e-06`）。该子集结论只在列出的 68 条范围内成立，且因 72 版脚本未留盘，『其余输入相同』仅由输出列推断、未经脚本级复核，如实标『未验重跑』；不得外推为全语料结论，更不得作为『合成链 vs 单层』的取舍依据。」

### (c) 剩余可信度：还剩多少站得住？

**站得住的 3 条，全部是否证性/无结论**（`_cmpw_verify.py` [10] 段实跑）：
1. **74 版内 chain 69/74 vs n13 71/74 的 2 条差不显著**：`b=2 c=0 p_2sided=0.5`。⇒ `GATE_PIPELINE_COMPOSE.md:412-416`、`_gp_DESIGN.md:340-343` 把 p=0.5 写成「如实结论 / 变差 2 条」属过度解读（`CHAIN_VS_SINGLE.md:67` 已指出，本会话独立复算支持）；
2. **72 版内 chain 48/72 显著劣于 n13 68/72**：`b=20 c=0 p=1.9073486328125e-06`，但只关于**已弃用的朴素并集算法**，不可推广到逐 span 版；
3. **输入契约不对齐使「N13 单层 71/74」不是能力**：本会话实跑 `n13.r13_assertions(text, tokens, ...)` 敏感性 →
```
三词表 T : CATCH? False | 判定=PASS  | details=[]
C07 四词表 : CATCH? True  | 判定=CATCH | details=[{'token':'已填',...}]
空词表    : CATCH? False | 判定=PASS  | details=[]
```
   证实 N13 谓词确实消费传入 `tokens`，而 `_gp_regression.py:143` 让 N13 单层恒用固定 `T`、`:145` 让 chain 用该行 `tokens`（`_cs_align.py:130-133` 复制旧 chain 列的自我更正亦在本会话逐字读到）。上游对齐实验方向反转 66 vs 69、`p=0.2500`（`CHAIN_VS_SINGLE.md:99-112`）系**引用上游实跑，本会话未重跑 74 条完整对齐实验，标未验**。

**必须撤回**：「合成链 69/74 明显变好（FP 33→2，FN 7→3）」（`GATE_PIPELINE_COMPOSE.md:414`）；「并集 48/72 → 逐 span 69/74 改良 21 分 / +26.58pp」。⇒ **「合成链 vs 单层谁更好」目前没有任何站得住的结论**（`CHAIN_VS_SINGLE.md:17,112,282` 本会话支持）。

### (d) 从未变部分反推：本会话实跑了

**方法**：取共有 71 条中 `expect` 相同、且同 `id`/同 `text_head`/同 `tokens` 的 68 条（剔除 3 条翻标）。**实跑输出（`_cmpw_verify.py` [9] 段，逐字）**：
```
strict n=68 v1_72_chain_ok=48 v2_74_chain_ok=66 chain_changed=18
paired b=18 c=0 p_2sided=7.62939453125e-06
CATCH n=36 : {'naive': (31,31), 'r10': (20,20), 'r12': (4,4), 'n13': (36,36), 'chain': (36,36)}
PASS  n=32 : {'naive': (2,2), 'r10': (12,12), 'r12': (32,32), 'n13': (32,32), 'chain': (12,30)}
单层4列在strict上逐行相同? True
```
**能反推的**：在这 68 条冻结考题上，把合成裁决从「三层 problems 朴素并集」换成「逐 span K1–K9」只做了一件事——把 18 条应放行样本从误拦改为放行，正类召回一条没动。这是本次唯一具有内部效度的因果陈述。

**不能反推的（写死）**：
- **E 轴不可核验**：「其余输入相同」由「四单层列逐行相同」**推断**，非脚本级复核 ⇒ 标「未验重跑」（`_gpv_regress.py:64-75`、`GATE_PIPELINE_COMPOSE.md:513`）；
- **18 条全正向、0 条反向**：正是设计 K9 时点名的失败形态（`_gp_pipeline.py:168-172`、`GATE_PIPELINE_COMPOSE.md:431`）⇒ **in-sample 调参收益，不是泛化证据**；
- **不得外推到全语料**：3 条翻标、2 条真新题、1 条换 id 题都不在这 68 条里；
- **不得反推成「合成链 vs 单层」**：对照物是「同一个 chain 的两种算法」；在 68 条内 chain(66/68) 仍劣于 n13(68/68)，本会话实跑 `b=2 c=0 p=0.5`。

---

## 5 重建基线步骤（设计，未实装、未实跑）

**最少步数口径**：主流程 **6 步（step1–step6）+ 1 个每轮必做的前置 step0 冻结动作**，合计 7 个环节（下表 step0–step6）。上游【审计】写「6 步重建，step0…step6」，本件按此口径明示，避免歧义。

| 步 | 输入 | 输出 | 验收（可执行） |
|---|---|---|---|
| **0 冻结并封 SHA**（前置） | 逐行 `(id, 全文 sha256, tokens, expect, family, note)`、标注手册（「什么算真断言」）、谓词/词表/骨架/脚本、评分公式、19 行词表分配（含 chain 第二词表 `n13_vocab`，`_gp_pipeline.py:132,135`） | 唯一真源 `_manifest.json`（五轴每侧 sha256+字节数）、逐件封存副本、`_cmp_assert.py` 修正版作门禁 | ① `hashlib` 逐件复算全 MATCH；② 每份 JSON 都有生成器指纹；③ 只读目录 `git status` 零漂移；④ manifest 任一字段缺失即 `sys.exit(1)` |
| **1 一次性出题 + 盲留出** | 真实交付件全集（按域 × expect 分层配额） | `train/dev/test` 物理隔离三集；test 封 SHA、双盲标注、Cohen's κ | ① 出题人 ≠ 改规则人 ≠ 批卷人（名单留盘）；② κ ≥ 0.8；③ N19–N26 / GP-A 只进 train，**禁进 test**；④ test 一次性使用，用过即作废另起版本 |
| **2 统一输入契约** | step0 语料 + `_gp_regression.py:143-145` 的契约事实 | 每行显式 `tokens`，**所有层（含 chain 的 `n13_vocab`）都消费它**；`n13_aligned` 与 `chain` 都重跑 | ① 静态检查 + 实跑证明逐行 `tokens` 被全部层读取；② 修正版断言 M 轴 `SAME`；③ 逐行断言不存在「免考卷」 |
| **3 单因素基线跑（核心）** | 冻结 S/G/E/M + I 两水平（并集/逐 span，或 单层/合成链） | 两份回归 JSON + 逐行配对表 + 两侧全列重跑 | ① 两格**都实跑**、不复用旧列；② manifest 列两侧脚本/依赖 SHA；③ 修正版断言判 `COMPARABLE` 且 `differing_axes==['I']`；④ 全部层逐行可配对 |
| **4 配对统计与不确定性** | step3 配对表 | b/c、exact binomial 双侧 p、bootstrap CI、macro-F1、按 expect/族分层条件错误率 | ① 必须报 p 与 CI，禁止只报点估计；② p>0.05 只能写「未检出差异」；③ 报 n、类别先验、分母口径 |
| **5 独立复核** | 同一 manifest + 只读产物 | 第三方复现 JSON + 逐字节比对报告 | ① 复现产物 SHA 相同或差异逐条归因；② 复核方独立跑断言得同一 verdict；③ 未经 step5 不得进入报告 |
| **6 按声明格式报数字** | step4/5 结果 | 报告段落 | 每个 `X/N` 都带 §6(d) 九项声明，缺项不得发布 |

### (a) ★「一次只改一样」的 8 条可执行纪律

1. **单一真源 manifest + 硬失败**：脚本开头对全部只读件 `hashlib` 复算，任一失配 `raise RuntimeError` + `sys.exit(1)`；参考现成实现 `_gp_pipeline.py:30-45`（现只对两个谓词做，扩展到全部件）。
2. **CI 门禁 = 修正版可比性断言**：每次写完回归 JSON **立即**跑；`verdict ∉ {COMPARABLE, REPLICATION, COMPARABLE_CROSSED}` ⇒ 退出非零，且不得把任何 `correct/n` 数字写进报告。门禁放在**写盘之前**。
3. **一变更单 = 一轴**：机器可读 `{"changed_axis":"I","old_sha256":...,"new_sha256":...,"all_other_axes_frozen":true,"reviewer":...}`，复核人签字；空单或 `changed_axis` 多于 1 项 ⇒ 拒跑。
4. **脚本留盘铁律**：每份 JSON 与生成它的 `.py` 同目录同批封 SHA；**无脚本的 JSON 作废**（本次 72 版即反例，`_gpv_regress.py:64-75`）。
5. **禁止同轮改 `expect` 与 `chain`**：翻标与改算法分两轮、两版本号、两份产物；门禁检查「同轮 `expect` 差异数>0 且 `chain` 差异数>0」⇒ 拒跑。
6. **改一项 = 全列重跑**：`naive/r10/r12/n13/chain` 全部重算（`_gp_regression.py:160-181` 结构已如此），禁止从旧 JSON 复制 `chain` 列（`_cs_align.py:130` 曾犯，已由 `CHAIN_VS_SINGLE.md:110` 自我更正）。
7. **只读域与写域物理隔离**：跑评测时语料/标注/脚本目录不可写；改语料另起版本目录禁止覆盖；跑完复算只读件指纹与 manifest 比对。
8. **报数前自动检查**：报告模板每个 `X/N` 必须引用一次 verdict + `scope`，缺引用拒绝渲染。

### (b) 只做一步的取舍

**主选 step3 最小版**：在 68 条已冻结共有子集上**只换合成裁决算法**、两格都实跑、两侧脚本 + manifest 一起留盘。理由可量化：当前争议实质是「算法替换值多少」，§4(d) 已给出唯一有内部效度的信号 `48/68 → 66/68, +18, p=7.63e-06`，机检判 `INDETERMINATE` 只因 72 版脚本/实现指纹缺失（E、I 两轴 UNKNOWN）。补一次两格实跑 + 全件留盘，可一次性把 `INDETERMINATE` 变成 `COMPARABLE`，产出唯一一条可**归因**结论；成本最低（68 条纯离线、不需出题/真机/改既有件）。

**退而求其次 step0 最小版「脚本 + manifest 留盘」**：把「不可核验」变「可核验」，是其他一切结论的前提。**不推荐先做 step1 盲留出**：出题/双盲/κ 成本最高，且 E 轴不可核验时新语料也救不回跨版归因。

⚠️ 无论做哪一步，结论只能写「在同一批考题上，算法 X 相对算法 Y」，**不得写成「合成链比单层好/差」**。

---

## 6 复核回件 + 变更纪律建议 + 未验项

### (a) 复核回件（绑定行格式）

**复核 verdict 如实记**：上游【复核】给 **partial** ⇒ 本交付件标 **`unconfirmed`**（遵照 `GATE_PIPELINE_COMPOSE.md:7`、`CHAIN_VS_SINGLE.md:6` 的既有口径）。七项复核里 **④「五轴可机检断言」判错**（详见 §3(e)），**①②③⑤⑥⑦ 我本会话独立复现通过**：① 九件基线 `BASELINE_MATCH 9/9` 且末次 `9/9`；② 逐条比对（§2）；③ 报告 `_cmp_AUDIT_20261109.md:109-126` 明列 8 个变更面、`:119` 第五样即「真值判读本体/标注依据」，复核员独立数出 9 个可辨识面、无遗漏（机检层漏检已计入 ④）；⑤ 68 条冻结子集为实跑（§4(d)）；⑥ 责任评估到位（本会话 `grep -cE` 三件台账/日志均 0 命中、`find`/`git log` 零命中均复现）；⑦ 零越界（末次 9/9 MATCH、`git status` 与快照一致、HEAD=`2657458`、只在唯一写域新建 `_cmpw_` 前缀核验件）。

**被复核对象**：`lead/comparability_20261109/_cmp_AUDIT_20261109.md`。本会话实跑 `python -I -X utf8 -c "<hashlib sha256 + len>"` 输出 `sha256=c8035cdeae7e81b04d1446aec4ee0151054c0b0062ec440b13168e120bc500b7 bytes=52442`，与【复核】`sha256Line` 逐位一致；其 9 条绑定行经正则 `^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$` 校验 `绑定行总数=9 合规=9`（`_cmpw_verify.py` [11] 段）。

被核对象 SHA256 = c8035cdeae7e81b04d1446aec4ee0151054c0b0062ec440b13168e120bc500b7，字节数 = 52442

（§2(a) 另有九件上游只读件的同格式绑定行，逐件 sha256/字节数均为本会话 `hashlib` 实算、与编排方【编排方实跑指纹】全 MATCH。）

### (b) 项目内前例清单（10 条，本会话逐件实读）

| # | 前例 | 同时改了什么 / 错在哪 | 证据（file:line） |
|---|---|---|---|
| 1 | **本次 72→74 回归** | 样本集 + 标注 + 算法 + 脚本（+ 判读本体 + 分类法 + 列定义） | `CHAIN_VS_SINGLE.md:69-76`；`_cs_BASELINE_ALIGNMENT_20261109.md:122-125`；本件 §2 |
| 2 | **N13 第二轮回灌** | 测试集失败样本 → 训练语料（N19–N26）+ 同步改谓词 | `lead/gate_n13_20261109/_n13_regression.py:104-112`；`lead/gate_n13_20261109/_n13_predicates.py:83,137,163,307`（`_SPLIT_ASSERT`/`_prefix_is_subject`/`_line_positive`/`r13_assertions` 本会话定位）；`CHAIN_VS_SINGLE.md:129`「出题人=改规则的人=批卷人」 |
| 3 | **GP-A1/A2/A3 定向构造** | 按已知盲区造题并塞进同一份回归分母 | `_gp_regression.py:121-130`；`_gp_DESIGN.md:274-282,287`；`CHAIN_VS_SINGLE.md:129` |
| 4 | **64 moving vs 97 全量双口径** | 换样本集（窗口定义）导致相关系数符号相反 | `lead/GOAL_THREE_TARGETS_20261018.md:3471,3484-3485,3590,3593,3596`；`lead/PENDING_DECISIONS.md:58-59`（D-14：双口径并列，引用须标注窗口定义/n/变量/范围/冻结版本） |
| 5 | **§534「可算 8 个 BOOT、中位 +0.4472」撤销** | nan 未滤 + 偶数样本未取均值（统计量口径错） | `lead/PENDING_DECISIONS.md:59`；`lead/GOAL_THREE_TARGETS_20261018.md:3472,3591` |
| 6 | **`fps_avg` 口径** | 同序列换统计量 → 偏高 1.2~1.6% | `lead/codex_round_20261030/XVERIFY_D_20261101/V4D_RECOMPUTE_20261101.md:76`（本会话实读：「引用 fps_avg 时必须注明口径，否则与其他 fps 统计不可比」） |
| 7 | **「200 vs 500 不可比较」只登记一半** | 登记「不可比较」却没给差值量化 | `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:15267,15304`（本会话实读：「只有理论一侧，另一侧是空的」） |
| 8 | **白名单自证循环** | 正样本集由判据作者为自己量身写；5 条全错仍 `VERDICT=PASS` | `lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md:139,368,419,491,514` |
| 9 | **全仓计数口径不可比** | `walk 16630` / `walk 16624` / `rglob 2460` 三种剪枝语义 | `lead/c07_slot_20261109/C07_IDENTITY_SLOT.md:157` |
| 10 | **v1 并集脚本未留盘** | 产物在、生成器不在 ⇒ 不可复核 | `_gpv_regress.py:64-75`；`GATE_PIPELINE_COMPOSE.md:431,513`；本会话 `find` + `git log --all` 复核 |

**共性**：项目在「数字算得对不对」上投入巨大（复算、指纹、独立复核一应俱全），但在「这两个数字能不能比」上几乎没有门禁。前例 4/5/6/7/9 已各自吃过亏并留下正确纪律条文（D-14 双口径并列、fps 口径声明），**这些条文没有被推广到回归评测**。

### (c) 评测变更必做清单（16 项，可贴进任务书）

```
【评测变更门禁 · 逐项打钩，缺一项不得报数字】
□ 1  建 _manifest.json：列出 S/G/I/E/M 五轴，每轴每侧 sha256 + 字节数 + 路径
□ 2  逐件 hashlib 复算 manifest，任一失配 → sys.exit(1)（不得只告警）
□ 3  冻结语料：逐行 (id, 全文 sha256, tokens, expect, family, note) 封 SHA；n 与类别先验写进 manifest
□ 4  冻结标注手册：「什么算正类」单独成文并封 SHA；本轮禁止改 expect
□ 5  冻结评测脚本：生成每份回归 JSON 的 .py 与 JSON 同批留盘并封 SHA（无脚本的 JSON 作废）
□ 6  冻结依赖：谓词 / 词表 / 骨架 / 语料加载路径逐件封 SHA
□ 7  填变更单：changed_axis 只能填 1 个；old/new 指纹 + 复核人；多轴 → 门禁拒跑
□ 8  全列重跑：改一项就重跑 naive/r10/r12/n13/chain 全部列，禁止复制旧列
□ 9  统一输入契约：所有层（含 chain 第二词表）消费同一份 tokens，逐行断言
□ 10 写盘前跑可比性断言：verdict ∈ {COMPARABLE, REPLICATION, COMPARABLE_CROSSED}
         且 differing_axes 长度 ≤ 1（或 2^k 格交叉实测产物齐备）
         ★ 断言实现须先通过单轴反例自检（G/E/S/M 单变必须硬拒、note 变更必须计入），否则门禁无效
□ 11 报配对统计：b / c / exact binomial 双侧 p / bootstrap CI / macro-F1；禁止只报点估计
□ 12 声明归因范围：写死 scope（id 列表）+「不得外推」
□ 13 盲留出：若结论要写「更好/更差」，须有出题人≠改规则人≠批卷人的封 SHA test 集 + Cohen's κ
□ 14 独立复核：第三方用同一 manifest 重跑，产物逐字节比对
□ 15 收尾：复算全部只读件指纹零漂移；git status 核对；不 commit 不 push
□ 16 每个 X/N 数字都带 (d) 九项声明，缺项不得发布
```

### (d) 方法论问题、编排方责任、报数前必声明什么

**方法论问题（四层）**：① 把「调参过程」当「评测证据」——K9 为消 20 条 FP 而写（`_gp_pipeline.py:168-172`）、GP-A 为暴露盲区而造（`_gp_regression.py:121-130`）、C05/C06/C07 按新判读口径翻标，三件事与「打分」发生在同一次交付里，分数必然朝一个方向走；② **真值可变 ⇒ 分数可被人工制造**（本次 3 分模型逐列未变）；③ 无 manifest、无版本化、脚本不留盘 ⇒ E/I 轴不可核验，机检只能 `INDETERMINATE`；④ 复核链只核「数字算得对不对」，不核「这两个数字能不能比」——`_gpv_repro_out.json` 与 74 版产物逐字节相同（本会话 [12] 段 `True`），数字都对，结论仍无效。

**★ 编排方责任（如实，不护着也不夸大）：评估为「默许 / 未设防」，不是「明令禁止后被违反」，也不是「指使改语料」。**
- **能证实**：派发任务把「构造三层全放过的样本」（`_gp_DESIGN.md:274` 的 3(d)，实装 `_gp_regression.py:121-130`）、「在 74 条合成语料上做分层回归对比」（`GATE_PIPELINE_COMPOSE.md:13`）、「第一版朴素并集失败证据保留不删」（`GATE_PIPELINE_COMPOSE.md:419-431`）放在同一任务、同一写域、同一份 `_gp_regression.py` 里；任务书要求「在 74 条合成语料上」，即**默认分母可以是 74**；报告把 `48/72` 与 `69/74` 并列为「FP 20→2」「明显变好」（`GATE_PIPELINE_COMPOSE.md:414,431`；`_gp_DESIGN.md:271,342`）。
- **不能证实（未验）**：**原始派发任务书未在仓库留盘**。本会话实跑
  ```
  grep -cE "gate_pipeline|合成链|GP-A1|GATE_PIPELINE" lead/PENDING_DECISIONS.md  → 0
  grep -cE "gate_pipeline|合成链|GP-A1|GATE_PIPELINE" lead/GOAL_THREE_TARGETS_20261018.md → 0
  grep -cE "gate_pipeline|合成链|GP-A1|GATE_PIPELINE" lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md → 0
  ```
  ⇒ 是否明写允许改语料/标注**未验**，不补造。
- **三条可归责落点**：① **未要求 v1 脚本留盘**（派了「保留失败证据」却没把生成脚本列为交付物，致 E 轴永久不可核验）；② **未要求语料/标注冻结封 SHA**（给了 9 件上游指纹，却没给语料本身与标注手册的冻结指纹，承接方在自己写域造语料/翻标注无门禁可拦）；③ **验收口径只核数值复算、不核跨版可比**（`GATE_PIPELINE_COMPOSE.md:435-439` 的复核项检查「脚本有没有 assert / 数值门槛有没有落地」，没有一条检查「两个分母不同的数字能不能相减」）。
- **不该夸大**：承接方报告已自认「72 与 74 不可比」（`CHAIN_VS_SINGLE.md:69`、`_cs_BASELINE_ALIGNMENT_20261109.md:125`），并把「未验重跑」「复核 partial → unconfirmed」「不许为了让合成链好看而调整评测口径」写进边界（`CHAIN_VS_SINGLE.md:6,16`；`GATE_PIPELINE_COMPOSE.md:7,18`）。⇒ 这是**流程与门禁的失守**，不是任何人蓄意粉饰；编排方责任止于「没把可比性做成任务约束与验收项」。

**报数字前必声明什么（一句话铁律）**：
> 任何形如 `X/N` 或「A → B 提升 Δ」的数字，发布前必须同段声明下列九项；任一项缺失或写「未验」，该数字只能作为「留盘观测值」，不得称为「改良 / 变差 / 优于 / 结论」，也不得与另一版本的数字相减。

```
【数字声明】指标 = <列名/定义>；分母 n = <N>（CATCH <c> / PASS <p>）；
  样本集指纹 = <S sha256>（n/先验/文本哈希/逐行 tokens）；
  真值标注指纹 = <G sha256>（含标注手册版本与「什么算正类」的定义）；
  被测实现指纹 = <I sha256> + 依赖指纹清单；
  评测脚本指纹 = <E sha256>（生成该 JSON 的 .py 必须在盘）；
  度量口径 = <ok/fp/fn 公式 + 阈值 + 聚合粒度 + 该列的导出规则>；
  可比性 verdict = <断言输出>；differing_axes = <...>；scope = <id 列表或「全量」>；
  配对统计 = b/c + exact binomial 双侧 p + bootstrap CI；
  留盘/复现状态 = <脚本是否留盘、是否独立重跑、复核 verdict、未验项逐条列出>。
```
**禁止项**：禁止用箭头 `→` 连接两个不同 `n` 的数字；禁止把「未验重跑」的 JSON 与已复现 JSON 并列比较；禁止把子集结论升格为全语料结论；禁止把「在这批考题上」写成「总体上 / 泛化上」。

### (e) 未验项（如实列，不补造）

1. **72 版朴素并集评测脚本与其实现代码全仓及 git 历史均未找到**（本会话 `find . -iname "*v1_union*"` 仅 2 个 `.json`/`.txt`；`git log --all --oneline --name-only | grep -i v1_union` → `GIT_ZERO_HITS`）⇒ `48/72` **未经脚本级重跑**，只重算留盘 JSON 内部自洽。
2. **`text_head` 为 90 字截断**（`_gp_regression.py:159`）；共有样本**第 91 字之后**是否改动，JSON 无法证明。前序会话从 9 件源件 + 4 条 N13 长样本补验前 90 字得 13 行 `OK`（`_cmp_AUDIT_20261109.md:93`），**本会话未重跑该补验，标「引用」**；其余「未验」。
3. **74 条完整「N13 输入对齐」实验本会话未重跑**；本会话只独立验了「N13 消费传入 tokens」这一机制前提（§4(c) 实跑）。`66/69`、`p=0.2500` 系引用上游 `CHAIN_VS_SINGLE.md:99-112` 的实跑。
4. **原始「合成链」派发任务书未在仓库留盘**；编排方是否明写允许改语料/标注「未验」。
5. **§3(e) 修正版可比性断言、§5 的 6 步重建方案与 16 项门禁均为设计，未实装、未实跑**；现有 `_cmp_assert.py` 因复核 partial 标 `unconfirmed`，不得当作已通过门禁。
6. **本会话首跑 `_cmpw_verify.py` 在 [8] 段因我自己的 `%` 格式化参数个数不匹配报 `TypeError: not all arguments converted during string formatting`**；已用 `Edit` 修正该 print 语句后重跑成功（本报告全部数字取自修正后那次完整输出）。如实记录，不掩盖。
7. 本件 `COMPARABILITY_AUDIT.md` 为自指文件，无法给出自身 SHA256 绑定行；§6(a) 的绑定行指向被复核的 `_cmp_AUDIT_20261109.md`。

### (f) 本会话实跑命令索引（逐字，主要者）

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/comparability_20261109/_cmpw_verify.py
   → [1] BASELINE_MATCH 9/9 ; [2] n72=72 n74=74 common=71 ; [3] expect 3 条 ; [4] 文本 0/note 5
     [5] GP-C03≡GP-A1 ; [6] conflicts 31/22→31/0 ; [7] chain 18 行 ; [8] 21 分分解 +18/+3/+0/+0
     [9] 68 子集 48→66 b=18 c=0 p=7.62939453125e-06 ; [10] p=0.5 / 1.9073486328125e-06
     [11] 报告 sha=c8035cde…b7 bytes=52442 绑定行 9/9 ; [12] same bytes True ; DONE
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/comparability_20261109/_cmpw_scenarios.py
   → 8 玩具场景（复现 partial 的 G/E/S/M/note/crossed 缺陷）+ REAL INDETERMINATE + HYPO NOT_COMPARABLE
python -I -X utf8 <_cmp_assert.py> <72.json> <74.json> --manifest <_cmp_manifest.json> --label-a v1_72 --label-b v2_74 --out <_cmpw_real_out.json>
   → EXIT=0 verdict=INDETERMINATE diff=['S','G'] unknown=['I','E'] strict n=68
python -I -X utf8 -m py_compile <_cmp_assert.py>            → PY_COMPILE_OK
python -I -X utf8 -c '<n13.r13_assertions 三词表/C07 四词表/空词表敏感性>' → PASS / CATCH / PASS
python -I -X utf8 -c '<只读源件 file:line 抽读 + 报告绑定行正则校验>'
find . -iname "*v1_union*"                                  → 仅 .json / .txt 两件
git log --all --oneline --name-only | grep -i "v1_union"     → GIT_ZERO_HITS
grep -cE "gate_pipeline|合成链|GP-A1|GATE_PIPELINE" <三件台账/日志>  → 0 / 0 / 0
git status --short <5 只读目录 + 2 台账> ; git rev-parse --short HEAD → 与快照一致 / 2657458
python -I -X utf8 -c '<9 件 hashlib 末次复算>'              → FINAL_BASELINE_MATCH 9 / 9
```
**未运行任何真机程序、未写任何采样代码、未改任何回归脚本/语料/产物、未 commit、未 push。**
