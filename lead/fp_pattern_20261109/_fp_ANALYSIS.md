# _FP_ANALYSIS.md — 误报模式分析：「误报全在训练构式上」是因果还是构造偏差

**角色**：误报模式分析员（只做模式分析）。
**纪律**：零真机 / 零采样代码 / 零 hook；绝对只读保护树；唯一写域 `lead/fp_pattern_20261109/`，产出前缀 `_fp_`；不改任何对抗集、谓词、语料；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。
**本会话实跑脚本**：`_fp_recompute.py`（41 条六判定器重跑 + 分级/构式/min_edit 复算）、`_fp_classify.py`（fp/fn 逐条分类 + 三判定器对照）。输出分别在 `_fp_recompute_stdout.txt` / `_fp_classify_stdout.txt` 与同名 `_out.json`。

---

## 0 绑定行（本会话 `hashlib.sha256` 独立重算，完整值见 `_fp_recompute_stdout.txt:2-33`）

被核对象 SHA256 = 2e60c913ceb2755fef4cb42020c3362ff63e0acbaa99541012ab7a361c8a232a，字节数 = 51456
（`lead/advset_indep_20261109/ADVSET_INDEPENDENCE.md`）

被核对象 SHA256 = f3e52f828c3c75875ed82fb41c5d38d04419e3c1e87a5ce01b6b1f3f1ea27298，字节数 = 28117
（`lead/advset_indep_20261109/_ai_grade_out.json`）

被核对象 SHA256 = 395a0a0a3f9316504510b83c023d078d8adcede33f0d20432cf31fcccf99286c，字节数 = 55528
（`lead/dg_adversarial_20261109/_dga_adversarial_out.json`）

被核对象 SHA256 = 7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1，字节数 = 12322
（`lead/dneg_generative_20261109/_dg_core.py`）

被核对象 SHA256 = b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c，字节数 = 8540
（`lead/h5_governance_20261109/_h5_pasteable.py`）

编排方申报的 9 件指纹逐件比对结果：`_fp_recompute_stdout.txt:34` → `orch_fingerprint_match = {"n": 9, "all_match": true, "mismatch": []}`。即 9/9 全同。本会话共核 16 件，其余 11 件的绑定行见 `_fp_recompute_stdout.txt:8-33`（格式同上，逐件给完整 64 位 SHA256 与字节数）。

---

## 1 第一步：复核分级与构式对应（全部实跑复现）

### 1(a) 四个分级数字能否复现 —— **能**

我未直接采信编排方数字，做了两层独立复算：

- **层 1（判定器重跑）**：`_fp_recompute.py:§1` 用 `ast.literal_eval` 抽 `lead/dg_adversarial_20261109/_dga_adversarial.py` 的 `CASES`，`compile/exec` 内存加载 `_dg_core.py` / `_h5_pasteable.py` / `_g7_predicates.py`（不写 `__pycache__`），重跑 41 条 × 6 判定器，再按 `_ai_verify.py:210-223` 的 `score()` 口径算 strict fp/fn。输出 `_fp_recompute_stdout.txt:37`：`strict_rerun_vs_orch = {"n_cases": 41, "all_identical": true, ...}`，六判定器 `fp/fn/fp_ids/fn_ids` 与 `_dga_adversarial_out.json:scoring_strict` **逐项全同**。
- **层 2（分级函数复算）**：`_fp_recompute.py:§3` 用 `_ai_grade.py:134-139` 的 `grade()` 分支对 `_ai_grade_out.json:rows` 的 41 行重算，并对 `_ai_verify_out.json:grade_rows` 重数。输出 `_fp_recompute_stdout.txt:44`：

| 口径 | L0 | L1 | L2 | L3 | 输出 |
|---|---|---|---|---|---|
| 严格（重算） | 24 | 17 | 0 | 0 | `strict_recomputed_from_rows` |
| 严格（存储） | 24 | 17 | — | — | `strict_stored = {"L1":17,"L0":24}` |
| 宽松（重算） | 33 | 8 | 0 | 0 | `loose_recomputed_from_rows` |
| 宽松（存储） | 33 | 8 | — | — | `loose_stored = {"L0":33,"L1":8}` |

`strict_match = true`、`loose_match = true`（`_fp_recompute_stdout.txt:44`）。严格 L0 的 24 个 id、L1 的 17 个 id 逐条打印在 `:44`，与 `ADVSET_INDEPENDENCE.md:258-259` 完全一致。两口径 `L2=L3=0` 复现。

- **文档其余统计**（`_fp_recompute_stdout.txt:45`）：`d1 非空=19`、`d2 非空=41`、`d3(任一)=21`、`d1∪d3=24`、`最长公共子串>=6 字=33`、`exact_overlap=[]`、`DG_pure 非空 hit 全部可由 DG 表拼出=true`。与任务书【背景】的 `24/41`、`41/41`、`33/41`、`0 []` 全同。
- **min_edit 重建**：`_fp_recompute.py:§2` 自建 79 条训练句集合、自写 Levenshtein 重算 41 条最小编辑距 → `_fp_recompute_stdout.txt:41` `min_edit_rebuild = {"n_train_sentences": 79, "all_match_stored": true, "diff": {}}`，41/41 与存储值一致。

### 1(b) 7 条误报的 `d1` 是否全部非空、`d3` 是否全部 True —— **是，但 `d3` 部分是恒真式，不是发现**

逐条（`_fp_recompute_stdout.txt:48` 的 `fp7_rows`；原始行见 `_ai_grade_out.json:rows`）：

| id | expect | verdict | d1 | d3_pure | d3_dropin | hit | min_edit | grade | attack |
|---|---|---|---|---|---|---|---|---|---|
| P06 | PASS | CATCH | 不敢不 | True | True | 不敢不承认 | 3 | L0 | ① |
| P07 | PASS | CATCH | 不敢不 | True | True | 不敢不承认 | 4 | L0 | ① |
| P08 | PASS | CATCH | 并不否认 | True | True | 并不否认 | 2 | L0 | ①④ |
| P09 | PASS | CATCH | 并不否认 | True | True | 并不否认 | 4 | L0 | ③④ |
| P10 | PASS | CATCH | 并不否认 | True | True | 并不否认 | 5 | L0 | ⑤ |
| P11 | PASS | CATCH | 并非不,非不 | True | True | 并非不宣告 | 3 | L0 | ② |
| P12 | PASS | CATCH | 并不否认 | True | True | 并不否认 | 6 | L0 | ② |

`fp7_all_d1_nonempty = true`、`fp7_all_d3_true = true`（`_fp_recompute_stdout.txt:49-50`）。

**★ 但必须指出 `d3` 的定义性同义反复**（这是本题的核心）：
- `_ai_verify.py:394-402` 定义 `hit_in_tables(h)`：`d3 := t12_decomp(h) or t3(h)`，其中入参 `h` 就是 `x["hits"]["DG_pure"]`（`:413-414`）。
- `_ai_verify.py:128-130` 定义 `DG_pure = "CATCH" if p else "PASS"`，`hits["DG_pure"] = h[0]["hit"] if h else ""` —— 即 **hit 非空 ⇔ CATCH**。
- 实跑核对（`_fp_recompute_stdout.txt:58`）：`d3_tautology = {"n_mismatch": 0, "ids": [], "n_DG_pure_CATCH": 19, "n_d3_pure_true": 19, ...}`。41 条里 `CATCH != hit非空` 的条数 = 0，`hit非空但 d3_pure=False` 的条数 = 0，`DG_pure` 的 19 个 CATCH 与 19 个 `d3_pure=True` 一一对应。
- 结论：**「7 条误报 d3 全 True」等价于「7 条误报都 CATCH」，是定义性恒真，零信息量**。`d3` 不是独立观测到的「训练构式」标签，而是从判定结果反推出来的。

### 1(c) 所有 `d1=-` 的样本是否全部判对 —— **仅在编排方列举的 8 条负样本上成立；全 41 条口径下不成立**

- **编排方列举的 8 条**：8/8 判对。逐条（`_fp_recompute_stdout.txt:51` 前 8 行；原始行见 `_ai_grade_out.json:rows`）：

| id | expect → verdict | d1 | d3_pure | hit | min_edit | grade |
|---|---|---|---|---|---|---|
| P01 | PASS → PASS | `-` | False | `-` | 3 | L1 |
| P02 | PASS → PASS | `-` | False | `-` | 7 | L1 |
| P03 | PASS → PASS | `-` | False | `-` | 15 | L1 |
| P04 | PASS → PASS | `-` | False | `-` | 8 | L1 |
| P05 | PASS → PASS | `-` | False | `-` | 6 | L1 |
| P13 | PASS → PASS | `-` | False | `-` | 10 | L1 |
| P14 | PASS → PASS | `-` | False | `-` | 4 | L1 |
| P15 | PASS → PASS | `-` | False | `-` | 4 | L1 |

`negative_all_judged_correct = true`（`:52`）。这 8 条与任务书给的 15 条列表中的「判对」组一致。

- **任务书列表内 7 条误报的 15 条对照**：编排方给的 P01–P15 共 15 条，其中 7 条 fp、8 条判对；`min_edit` 分别为 3/4/2/4/5/3/6（fp）与 3/7/15/8/6/10/4/4（判对），与 `_ai_grade_out.json:rows` 逐条全同。
- **★ 但全 41 条口径下 `d1` 为空的样本是 22 条，不是 8 条**。实跑（`_fp_recompute_stdout.txt:51-52` + 本会话补充核算）：

| 分组 | 条数 | 判对 | 判错 |
|---|---|---|---|
| `d1=-` 且 `expect=PASS`（8 条 P 负样本） | 8 | 8 | 0 |
| `d1=-` 且 `expect=CATCH`（C 组） | 13 | 4（C06/C13/C14/C15） | **9（C01–C05, C07, C08, C09, C10 = fn）** |
| `d1=-` 且 `expect=AMBIG`（A04，strict 排除） | 1 | — | — |
| 合计 `d1=-` | **22** | 12 / 21 可评分 | **9** |

`d1_empty_all_correct = {"n": 22, "all_verdict_PASS": false, "n_strict_negative": 8, "negative_all_judged_correct": true, ...}`（`_fp_recompute_stdout.txt:52`）。

**这是构造偏差的直接证据**：编排方的「所有 `d1=-` 全部判对」把 9 条 `d1=-` 的 **fn（漏判）** 从视野里切掉了；同一特征 `d1=-` 在负样本组 8/8 判对、在正样本组 9/13 漏判。支配结果的是 `expect` 类型（句子里有没有表内构式），不是「是否训练构式」。

- **★ 另有 2 条 `d1` 非空却判对的负样本被列表省略**：P16（`d1=['莫不']`，`min_edit=7`，`verdict=PASS`，`why=前句「莫不」周遍 DN，逗号切断`）、P17（`d1=['并非不','非不']`，`min_edit=3`，`verdict=PASS`，`why=DG 的 _mask_quotes 把跨度内部置空格⇒PASS 正确`）。见 `_fp_recompute_stdout.txt:53`。任务书给的列表只到 P15，**漏列了 P16/P17**。加上后：17 条 `expect=PASS` 负样本里 `d1` 非空共 9 条，其中 7 条 fp、2 条判对 → 「`d1` 非空 ⇒ 误报」不是全称规律。

### 1(d) `min_edit` 与误报有无单调关系 —— **无**

判据与实跑（`_fp_recompute_stdout.txt:55`）：17 条负样本按 `min_edit` 排序后的 fp 指示序列为 `[(2,P08,fp),(3,P01,ok),(3,P17,ok),(3,P06,fp),(3,P11,fp),(4,P14,ok),(4,P15,ok),(4,P07,fp),(4,P09,fp),(5,P10,fp),(6,P05,ok),(6,P12,fp),(7,P02,ok),(7,P16,ok),(8,P04,ok),(10,P13,ok),(15,P03,ok)]`。

- `fp_me = [2,3,3,4,4,5,6]`，`correct_me = [3,3,4,4,6,7,7,8,10,15]`，**重叠值集 = {3,4,6}**。
- 违「单调递增」的 (fp,ok) 对 = 12，违「单调递减」的 = 49 —— 两个方向的单调性都被违反。
- 穷举阈值 0..19 的最佳分离只有 `correct=10/17`，且最佳阈值 16 退化为「全部判 PASS」。
- 具体反例（任务书已点出）：P01 `min_edit=3` 判对，P12 `min_edit=6` 误报；反之 P08 `min_edit=2` 误报，P05 `min_edit=6` 判对。
- **判据**：若存在 `me(fp) < me(ok)` 且存在 `me(fp) > me(ok)`，则任何以 `min_edit` 为阈值/单调预测器的判据都不成立；本集两者皆存在 ⇒ **无单调关系**，`min_edit` 不是分界。

### 1 小结：关联强度（用于第二步）

17 条负样本的 2×2 列联（`_fp_recompute_stdout.txt:54`）：`d1非空 & fp = 7`、`d1非空 & 判对 = 2`、`d1空 & fp = 0`、`d1空 & 判对 = 8`；`P(fp|d1非空)=0.7778`、`P(fp|d1空)=0.0`；Fisher 单侧 `p = C(9,7)*C(8,0)/C(17,7) = 0.00185109`。**统计关联显著 ≠ 因果**，且该关联同时可由「因果机制」与「特征内生 + 样本构造」两种解释产生（见 §2）。

---

## 2 第二步：判这个模式的性质（本任务核心）

### 结论前置

**本集数据不能把「误报全在训练构式上」判为因果。它主要是（i）定义性恒真 +（ii）构造偏差，外加（iii）一个被限定在「表内构式 + 护栏未穷尽」的局部机制。三种解释各自都有实跑证据，但按「相关性不是因果」的纪律，因果解释不能成立为一般机制。更重要的是：本项目里 DG/H5/R12 都是静态正则/闭合表，无训练、无参数拟合，「记忆污染」这个术语是范畴错误（见 §3(b)）。**

### 2(a) 两种解释各自都可能成立的证据

#### 解释 A（真实因果 / 「训练构式使误报更易发生」）—— 可成立的证据

1. **选择器必然性有源码依据**：`_dg_core.py:114-128` 的 `DG_DROPIN_RE` 只由 `NEG1·MID·NEG2`（T12）与 `NEG1·GAP·V·COMP·X`（T3）两条模板 + 7 张闭合表的笛卡尔积拼成，`pattern = "(?:t12|t3)" + govern`（`:128`），零自由通配（T12 完全零通配，`:138` `wildcards:1` 仅 T3 的受控补语）。因此**任何 CATCH 的 `hit_text` 必然是表内构式拼出**。实跑 `all_pure_hit_decomposable = true`（`_fp_recompute_stdout.txt:45`）、`_ai_verify.py:435-436` 同结论。这使「fp 全部落在表内构式上」有结构性必然，而非巧合。
2. **fp 的根因可逐条定位到具体部件**（`_ai_grade_out.json:fp_attr`、`:rows`、`_fp_classify_stdout.txt:9-16`）：P06/P07 未登记转折/追补词（`DG_BREAK_RE` 仅 10 词，`_dg_core.py:89`）；P08 未登记让步词 + `NEG2` 收「否认」使 T12 零通配拼出（`:63-67`）；P09 第二主语「监理方」不在 `_SECOND`（`:88`）且二次 veto 只查 `hit_text`（`:182-184`）；P10 「或」在 `hit_text` 之外使并列 veto 失效（`:91`,`:182-184`）；P11/P12 未登记引号（ASCII 双引号 / 书名号，`DG_QUOTE_RE` 仅 4 类，`:92`）。`ADVSET_INDEPENDENCE.md:399-410` 归纳为失败模式 A（5/7，词表/作用域未穷尽）与 B（2/7，guard 位置错误）。
3. **最接近因果的既有受控替换实跑**：`lead/advset_indep_20261109/_ai_verify_stdout.txt:245` → 14 个未登记边界词造 `前稿不敢不承认{词}本件不宣告已生效`，`BREAK=False 且 DG_pure=CATCH 的条数 = 14`（14/14）；`DG_ADVERSARIAL.md:178-179` 反向对照「已登记 10 词上 `DG_pure=PASS 10/10`」。**保持表内构式不变、只换边界词 ⇒ fp 开/关**，这支持「护栏缺失」是 fp 的直接原因。
4. **统计关联显著**：Fisher 单侧 `p=0.00185`（`_fp_recompute_stdout.txt:54`），17 条负样本上 `d1` 非空与 fp 强关联。

#### 解释 B（构造偏差 / 「误报恰好都用了训练构式，是造样本的方式决定的」）—— 可成立的证据

1. **特征与结果共用同一张表（非独立观测）**：`d1` 的构式目录 `CATALOG` 在 `_ai_grade.py:48-58` 由 `DG.R12_TEN` + `DG.PSEUDO_DN` + `GAPS`(19 式) + `H5_EXTRA`/`H5_SPLIT` + H5 字面支拼成，`FAMILY` 在 `:91` 又并入 `DG.MID/PSEUDO/NEG1/NEG2`；`CAT_IN_TRAIN` 在 `:64-78` 定义为「目录条目在 DG 训练句子里作子串」；`d1 = [k for k in CAT_IN_TRAIN if k in text]`（`:103`）。而 CATCH 由同一批表生成的 `DG_DROPIN_RE` 判定。**「用了训练构式」与「被 DG 命中」不是两个独立变量，而是同一批常量表的两面**。实跑记录 `_fp_recompute_stdout.txt:59`。
2. **`d3` 恒真**（§1(b)）：19 个 CATCH ⇔ 19 个 `d3_pure=True`，零反例。「7/7 d3=True」不含经验信息。
3. **样本按被测实现逐条定制**：`DG_ADVERSARIAL.md:23` 自述「七条不变式来源」逐字复述 `_dg_DESIGN.md:141-158`；41 条里 `attack` 非空 26 条（`_fp_recompute_stdout.txt:61`），`why` 直接引 `_dg_core.py:` 行号 5 条、点名表/常量/行号 18 条；**7 条 fp 的 `attack` 全部非空**（`:60`，`all_attack_nonempty=true`）。例如 P06 `why` 明写「不在 DG_BREAK_RE(`_dg_core.py:89`) 也不在 `_BQ`(`:86`)」。`ADVSET_INDEPENDENCE.md:266-281` 已判「L3 生成机制与受测对象同源，L3 完全不成立」。
4. **fp 组被单一模板占满**：`ADVSET_INDEPENDENCE.md:399` 自述「7/7 是『表内构式』+『应切断/veto 而未切断』」；`:544` 自建规范明写「**不得让『表内构式 + 未登记边界词』占满 fp 组**」；`:588` 明写「若 L2+L3=0，必须在结论里写明『**本集只测构式记忆**』」。本集 L2=L3=0（§1(a)）。
5. **反例被省略、对照组被切掉**（§1(c)）：P16/P17 两条 `d1` 非空却判对的负样本未列入任务书 15 条列表；9 条 `d1=-` 的 fn 未列入。构造者按 `expect` 分工造样本 —— P 组设计成「两个独立否定、无 DN 构式」（自然 `d1=-` 且判对），fp 组设计成「表内构式 + 未登记边界」（自然 `d1` 非空且 CATCH）。`d1` 的分布是**构造决定**的。
6. **★ 跨判定器的决定性反证**：`_fp_recompute_stdout.txt:37` 六判定器 strict 全同 + `_fp_classify_stdout.txt:27-32` 显示 **DG_pure 7/7、DG_dropin 8/8、H5_lit 9/9、H5_gov 7/7、R12 2/2、R12_lit 2/2 的 fp 全部落在 `d1` 非空样本上**（`fp_all_d1_nonempty=true`、`fp_d1_empty_ids=[]` 六个全真）。而 H5_DOUBLE_NEG_RE 是 `H5_R12_TEN`(10 支) + `H5_DN_EXTRA`(19 式字面 + 1 通配) 的**手写正则**（`_h5_pasteable.py:31-40`），R12 是 10 支字面正则（`_g7_predicates.py:76`），两者**没有训练、没有学习、没有记忆存储**。若「训练构式记忆污染」是 DG 特有的机制，三个纯字面判定器不可能呈现完全相同的「fp 全在训练构式上」。我另实跑 `h5_lit_fp_all_from_literal_table = true`（`_fp_classify_stdout.txt:37`）：H5_lit 9 条 fp 的命中串 `不敢不/并不否认/并非不/莫不` 全部出自其手写字面支（`_fp_classify_stdout.txt:35-36`）。
7. **权衡曲线指向「机会面积」而非「记忆毒性」**：R12（10 支）`fp=2/fn=17` → DG_pure（105,492 生成串）`fp=7/fn=11` → H5_lit（37 字面支）`fp=9/fn=14`。fp 随表覆盖面增长、fn 随表覆盖面下降，呈同一条权衡曲线（数据：`_dga_adversarial_out.json:scoring_strict`）。`DG_ADVERSARIAL.md:247` 给出放大倍数（加 1 项 MID = +1,239 串、SPLIT_TAIL = +15,399）。这说明 fp 是「表内构式被塞进未登记边界」的**机会面积**，不是某个判定器的记忆缺陷。

#### 判定

- 两种解释都有证据，**按纪律不能判为因果**。
- 其中解释 B 的证据更强且更直接：`d3` 恒真（定义性）、`d1` 目录内生（测量内生性）、构造者读源码行号、`ADVSET_INDEPENDENCE.md` 三处自陈、跨三判定器同一模式（含两个零学习系统）。
- 解释 A 的有效部分应被**降级并限定**为：「在给定闭合表 + 2 模板下，护栏词表未穷尽导致的过宽」这一局部机制；它解释的是「为什么这 7 条会误报」，不是「为什么误报恰好都在训练构式上」。后者的答案是：**因为 DG 只能命中表内构式（`_dg_core.py:128`），构造者要造 fp 就别无选择**。这是选择偏差（selection on the dependent variable），不是因果。

### 2(b) 若是因果：机制是什么 —— 源码依据

「训练构式更易误报」若强行作因果读，机制不在「训练」，而在 **DG 的三层护栏全是闭合词表，且切断动作只在纯函数里执行**：

- `DG_DROPIN_RE`（`_dg_core.py:100-142`）：`n1,mid,n2 = _alt(NEG1),_alt(MID),_alt(NEG2)`（`:114`），`pattern = "(?:t12|t3)" + govern`（`:128`），`govern = (?=[^BQ]{0,24}$)`（`:125`）。构式必须落表内；且 24 字窗口允许跨边界搭桥。
- `_BQ = "。！？；;，,、：:\n「」『』“”`"`（`:86`）**不含转折词**；转折词只靠 `DG_BREAK_RE`（`:89`，10 词）在 `_scope()`（`:161-165`）里切断。
- `DG_QUOTE_RE`（`:92`）只认 4 类引号；`_mask_quotes`（`:148-158`）只在 `dg_double_neg`（`:167-186`）内被调用；`DG_SECOND_SUBJ_RE`（`:90`）/`DG_COORD_RE`（`:91`）的二次 veto 在 `:179-184` **只检查 `hit_text` 内部**，而 `hit_text = m.group(0)`（`:177`）只是命中的构式串，不含其后的边界/第二主语/并列词 ⇒ P09/P10 必然绕过。
- 交付形态更严重：`_g7_predicates.py:92` 的 `dbl = bool(DOUBLE_NEG_RE.search(pre))` 直接跑正则，`r12_scan`（`:144`）复用 `r10_context`，**四个 guard 在 `r10_context`/`r12_scan` 的 `co_names` 里全 False**（`DNEG_GENERATIVE.md:173`、`DG_ADVERSARIAL.md:247`）。
- 因此「表内构式 + 未登记边界词」三层护栏同时失效 ⇒ CATCH。`ADVSET_INDEPENDENCE.md:405-410` 归纳同结论。

**但这不是「训练构式被记住所以误报」**：DG 没有训练集权重、没有拟合参数，`NEG1/MID/NEG2` 等是人工枚举常量（`:37-82` 每行注释都写明收词规则）。所谓「训练构式」只是 `ADVSET_INDEPENDENCE.md:189` 定义的「DG 训练句子集合」—— 即 DG 自己用于自测的语料目录。

### 2(c) 若是构造偏差：为什么误报样本恰好都用了训练构式 —— 分析

四条互补理由，均有实跑/文件依据：

1. **fp 的必要条件就是「句子含表内构式」**：要触发 `CATCH`，必须让 `DG_DROPIN_RE.search()` 返回 Match；该正则只由闭合表笛卡尔积生成（`_dg_core.py:114-128`），表外构式拼不出。构造者想造 fp，**没有别的选择**。`all_pure_hit_decomposable=true`（`_fp_recompute_stdout.txt:45`）就是这个约束的实测。
2. **构造者读着被测源码造样本**：`DG_ADVERSARIAL.md:23` 明说七条不变式逐字复述 DG 设计文档；`attack` 以受测不变式编号命名（①–⑦）；`why` 引 `_dg_core.py:89/:86/:92/:118/:182-184` 行号。`ADVSET_INDEPENDENCE.md:266-281` 判「生成机制与受测对象同源，L3 完全不成立」。这使「表内构式 + 未登记边界词」成为**唯一被系统性枚举的 fp 族**。
3. **负样本组被设计成互补形状**：P01–P05/P13–P15 的 `why` 全是「两个独立否定、无 ¬¬P 管辖链」（`_dga_adversarial_out.json:cases[*].why`），按 `DG` 设计就该放过 ⇒ `d1=-`、`d3=False`、判对。两组按 `expect` 分工，`d1` 分布是构造的输入而非模型的输出。
4. **分界口径本身也来自被测表**：`d1` 的目录 `CATALOG` 取自 DG 自身常量（`_ai_grade.py:48-58`），`d3` 取自 DG 自身命中串（`:394-402`）。所以「误报都在训练构式上」这句话里的「训练构式」是**用被测对象的表定义的**，与「误报」用的是同一把尺子 —— 这是循环论证，不是独立检验。

`ADVSET_INDEPENDENCE.md:544`（不得让表内构式占满 fp 组）、`:588`（L2+L3=0 时须写明「本集只测构式记忆」）、`:569`（一般性断言标 unconfirmed）三处自陈，等于上游已经把这条构造偏差写明了。

### 2(d) ★ 能区分这两者的实验（**设计，不执行**）

共同原则：把「构式是否在表内」从「是否被检测」里解耦；构造者盲化；按族分层；真值第三方裁定。

- **E1 表内/表外 × 边界已登记/未登记 2×2 析因**（最小判别）：固定模板 `{构式}{边界词}本件不宣告已生效`，构式取 (a) 表内（不敢不承认/并不否认）、(b) 表外但语义等价真 DN（未登记 MID，如「不容不承认」）；边界词取 (a) 已登记（「另外」）、(b) 未登记（「其实」）。**预判（不执行）**：表外格 DG 恒 PASS ⇒ 说明「fp 全在表内构式」是选择器约束而非训练效应。若表外格也出现 fp，因果的「训练构式」必要条件即被否证。
- **E2 消融对照（直接判「去污染」还是「补护栏」）**：两组干预，均不动构式表 —— (甲) 只把 14 个边界词 + 4 类引号登记进 `DG_BREAK_RE`/`DG_QUOTE_RE`；(乙) 只把 7 条 fp 命中的构式从 `NEG1/MID/NEG2` 里删掉。若 (甲) 让 7/7 fp→PASS 而真阳 C06/C13–C16 不退化，则根因是**护栏未穷尽**（覆盖/护栏问题），「记忆污染」被否证；若必须靠 (乙) 才消 fp，才支持「表内构式本身带毒性」。这是本任务最推荐的判别实验。（`DG_ADVERSARIAL.md:308` 已把「补转折/让步词 + guard 入 `r10_context`」列为修复项，但**未执行**。）
- **E3 盲化 held-out 重造（因果的外部效度检验）**：由**不读 `_dg_core.py`/DG 设计文档**的第三方按外部语料（BCC/CCL）或独立随机生成 ≥200 条，强制按「表内 / 表外 / 族外」三层各 1/3 分层，真值由语言学裁定、`AMBIG` 显式标 `NEEDS_HUMAN`（`ADVSET_INDEPENDENCE.md:542-550` 已给清单）。报每层 fp/fn + 置信区间。若表外/族外层样本量充足仍出现 fp ⇒ 构造偏差解释胜；若 fp 仍只集中在表内层且表外层 0 fp ⇒ 支持「表内构式 + 护栏」局部机制，但仍需 E2 分离「构式」与「护栏」两个因素。
- **E4 交叉判定器（既有数据已部分给出）**：把同一批盲化样本喂给表规模不同的三判定器（R12 10 支 / H5_lit 37 字面支 / DG 105,492 生成串）。若三者 fp 高度重合且都落在「各自表内构式」上 ⇒ 构造偏差（谁的表都能被照着造出 fp）；若 fp 按表结构分化 ⇒ 才有机制信息。**本会话既有实跑已倾向构造偏差**：六判定器 fp 全部 `d1` 非空（`_fp_classify_stdout.txt:27-32`），H5_lit 9/9 命中串来自手写表（`:37`）。
- **E5 负对照扩样**：把「表内构式 + 正确切断」的负样本（现有 P16/P17 两条）扩到与 fp 组等规模。若这些稳定判对 ⇒ 「表内构式」是 fp 的必要非充分条件，「未登记边界词」才是充分条件的候选；这能直接拆开「构式记忆」与「护栏缺失」两个被混为一谈的因素。
- **E6 表宽扰动**：按 `DG_ADVERSARIAL.md:247` 的放大倍数，逐项增删 `NEG1/MID/NEG2/SPLIT_TAIL` 并重跑 E3 集，看 fp 是否随「表宽机会面积」线性变化。线性 ⇒ 支持构造/机会面积解释；出现与表宽无关的 fp 集中簇 ⇒ 才可能有独立的记忆机制。

**执行状态：以上 6 个实验本会话一律未执行**（纪律：只做模式分析，不改对抗集/谓词/语料）。E4/E5 我只利用了既有 41 条数据的被动观察，未新造样本。

---

## 3 第三步：区分两种失败类型

### 3(a) 覆盖不足（新构式抓不到 = fn）

**可观测定义**：句子含真 DN（`¬(¬P)`）但 `DG_pure=PASS`，且 `hit_text` 为空 / `d3=False`。本集 11 条 fn 中 **8 条**属此类（逐条见 §3(c)）。根因均为「闭合表/模板未穷尽」：`MID` 23 项（`_dg_core.py:55-61`）、T3 `comp{0,4}?`（`:118`）、`_SECOND` 负向前瞻（`:88`,`:118`）。

### 3(b) 记忆污染（训练构式上误报 = fp）

**7 条 fp 全部满足 `d1` 非空、`d3=True`、`hit` 为表内构式**（§1(b)），表面符合「训练构式上误报」。但按任务给的定义，必须如实修正三点：

1. **术语是范畴错误**：DG/H5/R12 全是静态正则或闭合常量表 —— `DG_DROPIN_RE`（`_dg_core.py:142`）、`H5_DOUBLE_NEG_RE`（`_h5_pasteable.py:40`）、`DOUBLE_NEG_RE`（`_g7_predicates.py:76`）。无训练集权重、无拟合参数、无梯度、无记忆存储。「训练构式」在本项目里指 `ADVSET_INDEPENDENCE.md:189` 的「DG 训练句子集合」，即**构造者用来造样本的语料目录**，不是模型训练所记住的东西。**没有学习系统，就没有「记忆」可污染。**
2. 可观测的替代命名是 **「过宽 / over-inclusive（护栏污染）」**：表内构式被放进「本应切断但没切断」的语境，正则仍命中。这既解释了 7 条 fp，也解释了 H5_lit 的 9 条 fp 与 R12 的 2 条 fp（三者同一模式，§2(a) 证据 6）。
3. **`d3` 部分是恒真**（§1(b)）：「fp 全在训练构式上」有一半是定义性必然（任何 CATCH 的 hit 必是表内构式），不是经验发现。

### 3(c) ★ fp=7 / fn=11 逐条分类（strict，`DG_pure`，n=36）

完整机器可读版：`_fp_classify_out.json:fp7_classified` / `fn11_classified`；逐行输出 `_fp_classify_stdout.txt:9-22`。

**fp = 7 条 —— 全部「过宽 / 护栏污染」（任务所谓「记忆污染」）**

| id | 分类 | d1 | 缺失护栏 | 源码依据 |
|---|---|---|---|---|
| P06 | fp / 过宽 | 不敢不 | 未登记转折词「其实」 | `_dg_core.py:89` `DG_BREAK_RE` 10 词；`:86` `_BQ` 不含转折词；`:125` govern≤24 搭桥 |
| P07 | fp / 过宽 | 不敢不 | 未登记追补词「说到底」 | 同上 |
| P08 | fp / 过宽 | 并不否认 | 未登记让步词「尽管」+ `NEG2` 收「否认」使 T12 零通配拼出 | `_dg_core.py:63-67`, `:89`, `:126` |
| P09 | fp / 过宽 | 并不否认 | 第二主语「监理方」未登记 + veto 只查 `hit_text` | `_dg_core.py:88`, `:179-181` |
| P10 | fp / 过宽 | 并不否认 | 并列词「或」在 `hit_text` 之外 ⇒ 并列 veto 不触发 | `_dg_core.py:91`, `:182-184` |
| P11 | fp / 过宽 | 并非不,非不 | ASCII 双引号未登记 ⇒ `_mask_quotes` 不生效 | `_dg_core.py:92`, `:148-158` |
| P12 | fp / 过宽 | 并不否认 | 书名号《》未登记 | 同上 |

`fp_attr`（`_ai_grade_out.json:fp_attr`）逐条同归因；`ADVSET_INDEPENDENCE.md:399-402` 把 P06/P07/P08/P11/P12 归「失败模式 A（5/7）」、P09/P10 归「失败模式 B（2/7）」。

**fn = 11 条 —— 8 条覆盖不足，★ 3 条并非覆盖不足而是「过严 veto 误杀」**

| id | 分类 | d1 | 具体缺口 / 误杀 | 源码依据 |
|---|---|---|---|---|
| C01 | 覆盖不足 | 空 | MID「容」不在 23 项闭合表 | `_dg_core.py:55-61` |
| C02 | 覆盖不足 | 空 | MID「许」未登记 | 同上 |
| C03 | 覆盖不足 | 空 | MID「想」未登记 | 同上 |
| C04 | 覆盖不足 | 空 | MID「想」未登记 | 同上 |
| C05 | 覆盖不足 | 空 | MID「准」未登记 | 同上 |
| C07 | 覆盖不足 | 空 | T3 `comp{0,4}?` 硬界：COMP=5 字越界 | `_dg_core.py:118` |
| C09 | 覆盖不足 | 空 | comp 负向前瞻排除 `_SECOND`「本件」，真 DN 被排除 | `_dg_core.py:88`, `:118` |
| C10 | 覆盖不足 | 空 | `_SECOND` 第二主语一刀切，未建模 `¬(本件¬宣告)` 的命题管辖 | `_dg_core.py:90`, `:179-181` |
| **C08** | **抑制污染（veto 误杀）** | 空 | COMP 含「或」触发并列 veto，把真 DN 当两项独立否定否决 | `_dg_core.py:91`, `:182-184` |
| **C11** | **抑制污染（veto 误杀）** | 非不 | 「非不」在 `PSEUDO_DN` 被词首负向前瞻否决 | `_dg_core.py:81-82`, `:116` |
| **C12** | **抑制污染（veto 误杀）** | 非不 | 同上（「非不认可」） | 同上 |

汇总（`_fp_classify_stdout.txt:24`）：`fn_types = {"覆盖不足": 8, "抑制污染(veto 误杀)": 3}`；`fn_d1_empty = 9`、`fn_d1_nonempty = 2`（C11/C12）。

**★ 因此任务的「覆盖不足 vs 记忆污染」二分不完备，如实修正为三类**：(1) 覆盖不足（表/模板未穷尽 → fn，8 条）；(2) 过宽 / 护栏污染（训练构式上 fp，7 条）；(3) 抑制污染 / veto 误杀（表内构式上 fn，3 条）。而且 C11/C12 是 **`d1` 非空（训练构式）上的漏判**，与「训练构式 ⇒ 误报」正好反向 —— 这又是一条反对因果读法的证据。`ADVSET_INDEPENDENCE.md:212` 也记「PSEUDO 词表既误杀真 DN C11/C12…」、`DG_ADVERSARIAL.md:212` 同。

### 3(d) ★ 两种失败的修复方向完全不同（给方案，不实施）

| 失败类型 | 修复方向 | 具体方案 | 代价 / 反作用 |
|---|---|---|---|
| **覆盖不足**（fn 8 条） | **加表 / 放宽模板** | ① `MID` 补 9 个未登记项（容/许/想/愿/甘/料/要/需/欲，`DG_ADVERSARIAL.md:189`）；② T3 `comp{0,4}?` 放宽或改语义长度判据；③ `_SECOND` 的一刀切改为「是否处于 `N1` 的命题管辖内」判定（救 C09/C10）；④ T12 增 `N2` 前后向的第二主语/并列检查 | 加表按 `DG_ADVERSARIAL.md:247` 放大：+1 MID = +1,239 串、+1 NEG1 = +1,788、+1 SPLIT_TAIL = +15,399 ⇒ **会反过来扩大过宽面**，须全量 fp 扰动审计 |
| **过宽 / 护栏污染**（fp 7 条） | **去污染 = 补护栏 / 收紧，不动构式表** | ① 14 个边界词补进 `DG_BREAK_RE`（`:89`）或 `_BQ`（`:86`）；② 引号补 ASCII 双引号 / 书名号进 `DG_QUOTE_RE`（`:92`）；③ **把 `_mask_quotes`/`_scope`/`DG_SECOND_SUBJ_RE`/`DG_COORD_RE` 并入 `_g7_predicates.py:92` 的 `dbl` 判定**（当前 4 个 guard 在 `r10_context`/`r12_scan` 的 `co_names` 全 False，`DNEG_GENERATIVE.md:173`）；④ 二次 veto 从「只查 `hit_text`」改为查 `N2` 之后到 token 的整个窗口（`:179-184`） | 收紧会**扩大漏判面**（可能新添 fn）；且 ③ 与 DG 申报的「一行替换、调用点零改动」冲突（`DNEG_GENERATIVE.md:184` 自标 unconfirmed） |
| **抑制污染 / veto 误杀**（fn 3 条） | **去污染 = 缩小 veto 作用域** | ① `PSEUDO_DN` 从「词首负向前瞻」改为位置局部判定；② `DG_COORD_RE` 不否决 T3 COMP 内的并列（区分「补语内并列」与「两项独立否定」） | 可能放过真的伪构式（N14「非但不」、A01/A02） |

**关键判断**：两类主修复方向**相反且互相放大** —— 加表扩大过宽面、补护栏扩大漏判面。因此不能「先加表再去污」串行做，必须六判定器 + 74 条回归双跑，并以 `fp=0` 为上线门槛（`DG_ADVERSARIAL.md:308`）。本会话**未实施任何修复**（纪律）。

---

## 4 第四步：评估这个发现对 DG 结论的影响

### 4(a) 「DG 不误判不成立」要不要修正 —— **数字不修，表述要限定**

- **数字层面不修**：7 条 fp 我逐条独立重跑复现（`_fp_recompute_stdout.txt:37` `all_identical=true`、`:38` `DG_pure_strict fp=7 fn=11`）；`ADVSET_INDEPENDENCE.md:567` 已给「高（已复现）」。
- **表述必须限定**：原句若读作「DG 对自然语言新句会误判 / 泛化差」，**不成立**。本集 L2=L3=0、构造者与实现同源、7 条 fp 全是「表内构式 + 未登记边界词」模板变体（`ADVSET_INDEPENDENCE.md:399`, `:570` 已把「DG 泛化差」标「低 / 未验」）。准确表述见 §5(a)。
- **「记忆污染」这个定性要撤**：本发现**不足以**把失败类型升级为记忆污染；DG 无学习机制（§3(b)）。若保留该定性，会误导修复方向走向「去表/重训」，而实际该做的是补护栏 + 加表 + 缩 veto。
- 上游 `ADVSET_INDEPENDENCE.md:569` 已把「一般性『不误判』不成立」标 `unconfirmed`，`:571` 维持 `severity=high`（针对 fp 本身）。本工作不改上游判定，只补上「这个新模式主要是构造偏差 + 恒真式，不是因果、不是记忆污染」。

### 4(b) ★ 「DG 需要独立 held-out」是否仍成立 —— **仍成立，且理由反而加强；但功能要重定位**

- **若失败是记忆污染**（对表内构式过拟合）：held-out 显然必要 —— 需要表外样本才能检验去污染是否成功。**成立**。
- **若失败是构造偏差**：held-out 同样必要，而且更必要 —— 因为本集 L2=L3=0、构造者读着 `_dg_core.py` 行号造样本，`ADVSET_INDEPENDENCE.md:281` 判「L3 完全不成立」。构造偏差**不是**「不需要 held-out」的理由，而是「现有 41 条不能替代 held-out」的直接证明。按 `:542-550` 的清单，需要的是盲化、按构式族分层、真值第三方裁定、≥200 条的 held-out。
- **两种解释下结论一致 ⇒ 该要求对失败类型不敏感，稳健成立**。
- **功能重定位**：本集能把 fp 定位到具体源码行（§2(b)），所以**最小修复不需要等 held-out**；held-out 的职责应从「判定因果/验收原结论」改为「**验收修复 + 提供分布外样本**」。`DG_ADVERSARIAL.md:308`「先过独立 held-out 对抗集」、`ADVSET_INDEPENDENCE.md:559`「held-out 与回归分离」均维持有效。
- 附带：`ADVSET_INDEPENDENCE.md:604` 已把「DG 泛化能力 / 对分布外新句误判率」列为「本集测不到」，这正是 held-out 不可替代的部分。

### 4(c) H5 的失败类型（fp=9 / fn=14）—— **不是记忆污染**

数据（`_fp_classify_stdout.txt:29`）：`H5_lit fp=9 fn=14`，`fp_ids = P06..P12, P16, P17`，`fp_all_d1_nonempty=true`；`H5_gov fp=7 fn=14`（`:30`）。

判据：

1. **H5 没有学习/记忆机制**：`H5_DOUBLE_NEG_RE = re.compile("(" + H5_R12_TEN + "|" + H5_DN_EXTRA + ")")`（`_h5_pasteable.py:40`），`H5_R12_TEN` 是 10 支字面（`:31-33`），`H5_DN_EXTRA` 是 19 式字面 + 1 条通配（`:34-38`）。纯手写正则，无训练、无参数 ⇒ **无记忆可污染**。
2. **但 9/9 fp 命中串全出自 H5 手写表内构式**（`_fp_classify_stdout.txt:35-37`：`不敢不/并不否认/并非不/莫不`，`h5_lit_fp_all_from_literal_table=true`，手写纯字面支 37 条），且 9/9 `d1` 非空 —— **与 DG 完全相同的「fp 全在训练构式上」模式**。
3. 这**反证**「记忆污染是 DG 特有的学习缺陷」：一个零学习的字面正则也呈现同模式 ⇒ 模式来自样本构造（照着表造 fp），不来自记忆。
4. H5 的**实际**失败类型：fp 是「字面表过宽 + 不看引证/边界」—— P16/P17 是 H5_lit 独有的 fp（`H5_DOUBLE_NEG_RE.search(text)` 直接跑全句，不执行 `_h5_mask_quotes`，`_ai_verify.py:140-142`），而 `H5_gov` 走 `h5_govern()` 后这两条消失（fp 由 9 降到 7，`:30`）；fn=14 主要是覆盖不足（19 式之外的 C13–C16 全漏，`DNEG_GENERATIVE.md:344` 记「复核员 17 条都漏：H5 0/17」）。
5. 结论：**H5 = 覆盖不足为主 + 字面过宽为辅 + 无 veto 误杀**（它没有 `PSEUDO_DN` 这类 veto）。与 DG 同类但更偏覆盖不足，且同样不是记忆污染。

### 4(d) 三者失败类型对照表（strict，n=36，5 条 AMBIG 排除）

数据：`_dga_adversarial_out.json:scoring_strict`、`_fp_classify_stdout.txt:27-32`、`_fp_recompute_stdout.txt:37`（六判定器全同复现）。

| 判定器 | 规则形态 | fp | fn | fp 全在 `d1` 非空 | fp 类型 | fn 类型 | 有无学习/记忆 |
|---|---|---|---|---|---|---|---|
| **DG_pure** | 2 模板 + 7 闭合表，105,492 生成串（`_dg_core.py:129-139`） | **7** | **11** | 7/7 是 | 过宽 / 护栏污染（表内构式 + 未登记边界词/引号/veto 作用域） | 覆盖不足 8 + veto 误杀 3 | **无**（人工常量表 + 正则） |
| **H5_lit** | 10 支 + 19 式字面 + 1 通配，37 纯字面支（`_h5_pasteable.py:31-40`） | **9** | **14** | 9/9 是 | 字面表过宽 + 不屏蔽引证（P16/P17 独有） | 覆盖不足为主（C13–C16 全漏） | **无**（手写正则） |
| **R12** | 10 支字面正则（`_g7_predicates.py:76`） | **2** | **17** | 2/2 是 | 字面表过宽（P11/P17 引文内命中） | 覆盖不足为主（十式之外全漏） | **无**（手写正则） |

附加对照：`DG_dropin 8/10`、`H5_gov 7/14`、`R12_lit 2/17`（`_fp_recompute_stdout.txt:37`）。三者呈现**同一条「表越宽 ⇒ fp 越多、fn 越少」的权衡曲线**（10 支 → 37 支 → 105,492 生成串），六判定器 fp 无一落在 `d1` 空样本上。**这条曲线是「构造/机会面积」的证据，不是任一判定器的记忆毒性。**

---

## 5 第五步：结论与建议

### 5(a) ★ 本集的准确表述（不只是「DG 不误判不成立」）

> 在本 41 条由构造者读着 `_dg_core.py` 行号、按其七条不变式自造（26/41 带 `attack` 标签）、**L2=L3=0** 的对抗集上，严格口径（36 条可评分）`DG_pure` 为 **fp=7 / fn=11**，六判定器逐条独立重跑全同。7 条 fp **全部**落在 DG 闭合表可拼出的构式上 —— 但这首先是**定义性必然**（`DG_DROPIN_RE` 只由闭合表笛卡尔积生成，任何 CATCH 的 `hit_text` 必为表内构式；`d3` 由 `hit` 反推，41 条里 `CATCH⇔d3=True` 无反例），其次是**构造偏差**（`d1` 的构式目录取自 DG 自身常量表，构造者按 `expect` 分工把 fp 组填满单一模板；9 条 `d1=-` 的 fn 与 2 条 `d1` 非空却判对的 P16/P17 被 15 条列表省略），因此**不能判为「训练构式导致误报」的因果，更不能定性为「记忆污染」**（DG/H5/R12 均无学习机制；三者 fp 全部呈同模式）。可成立的局部机制是「**表内构式 + 未登记边界词/引号/第二主语/veto 作用域 ⇒ 三层护栏同时失效的过宽**」。11 条 fn 中 8 条为**覆盖不足**、3 条为**过严 veto 误杀**。本集只测「表内构式 + 护栏」，能证伪「未限定词表的一般性不误判宣称」，**不能**证明「DG 泛化差 / 对分布外新句误判」，也**不能**判定因果方向。

### 5(b) 以后设计对抗集时如何区分两种失败的操作建议

1. **2×2 强制分层**：每条样本标「构式 ∈ {表内 / 表外 / 族外}」×「边界 ∈ {已登记 / 未登记 / 无边界}」，各格样本数均衡，`fp/fn` 按格分别报（`ADVSET_INDEPENDENCE.md:544` 已提，本任务补上「构式 × 边界」双因素）。**不允许 fp 组只由「表内 × 未登记」一格构成**。
2. **构造者盲化 + 真值第三方**：生成过程不读被测表/常量/源码行号；形状来自外部语料或第三方语言学家；`expect` 附语言学理由与裁定人；`AMBIG` 显式标 `NEEDS_HUMAN`（`ADVSET_INDEPENDENCE.md:543,547`）。
3. **特征与判定解耦**：`d1`-类标签须来自**独立语料**（外部构式表），不得由被测对象的 `NEG1/MID/NEG2/PSEUDO_DN` 拼出；`d3`-类标签不得从 `hit_text` 反推（本集 `d3` 恒真）。至少报一个与判定器无关的分层变量（如外部语料频次、构式族、句长）。
4. **负对照必须等量**：每组「表内构式 + 未登记边界」的 fp 候选，配等量「表内构式 + 已登记边界」与「表外构式 + 未登记边界」负对照；本集只有 P16/P17 两条负对照，且被列表省略，不足判因果。
5. **修前/修后双跑 + 消融登记**：对每次干预（加表 / 补护栏 / 缩 veto）分别跑，报 Δfp/Δfn；把「只补护栏」与「只删构式」两组消融作为区分「去污染」与「补表」的标准动作（§2(d) E2）。
6. **报每族 fp/fn + 置信区间 + 表宽对照**：≥200 条、按族分层，同时跑表规模不同的 ≥2 个判定器并报 fp 重合度（`ADVSET_INDEPENDENCE.md:550,588`）；`L2+L3=0` 时结论里强制写「本集只测构式记忆」。
7. **登记「本集能证伪 / 不能证伪」**：把「因果方向」「分布外误判率」「修版后状态」显式列入不能证伪清单（`ADVSET_INDEPENDENCE.md:550,604`）。

### 5(c) 若在 DG 上做最小修复，先修哪类 —— **先修 fp（过宽 / 护栏污染）**

理由（按可验证性排序）：

1. **危害**：fp 是把合规件误拦成违规（门禁误杀），fn 是漏判；`DG_ADVERSARIAL.md:308` 把「P 组 `fp=0` 才准上线」列为验收门槛、`ADVSET_INDEPENDENCE.md:571` 采「fp 优先口径」。
2. **修复是局部、可验证、不放大表规模**：7 条 fp 全部可定位到 4 处护栏（`_dg_core.py:89/92/88/182-184`），补边界词/引号 + 把 4 个 guard 并入 `_g7_predicates.py:92` 即可；**不动构式表**，不触发 1,239–15,399 倍的生成串放大（`DG_ADVERSARIAL.md:247`）。
3. **顺序理由**：覆盖不足的修复要加表，而加表会**扩大过宽面**（§3(d) 反作用）。若先加表再补护栏，等于先把 fp 面放大再去堵，回归成本更高。
4. **既有实跑支持**：14/14 未登记边界词 fp、已登记 10 词 10/10 PASS（`_ai_verify_stdout.txt:245`、`DG_ADVERSARIAL.md:178-179`）—— 护栏开关直接控制 fp，是最短路径。
5. **约束**：补护栏会扩大漏判面，且 ③ 与「一行替换」交付形态冲突（`DNEG_GENERATIVE.md:184` 自标 unconfirmed）。故必须同步跑 11 条 fn + 74 条回归，不能单独上线。**本会话未实施任何修复。**

### 5(d) 这条工作判不了什么（如实列）

1. **因果方向**：本工作只做了被动观察与既有数据复算，§2(d) 的 E1–E6 全部**未执行**；不能判「训练构式 ⇒ 误报」是因果还是构造偏差中的哪一个是主因（只能判「因果不能成立为一般机制」）。
2. **「记忆污染」机制是否存在**：本项目无学习系统（DG/H5/R12 全为静态正则/闭合表），该机制在本项目内不可测、不可证伪；本工作只否证了它作为本集失败类型的适用性。
3. **DG 的泛化能力 / 对分布外自然语言新句的误判率**：本集 L2=L3=0，测不到（`ADVSET_INDEPENDENCE.md:604`）。
4. **修版后的状态**：未改任何谓词、未模拟补词/加表/veto 调整后的效果（`ADVSET_INDEPENDENCE.md:606`）；7 条不变式在修版后是否仍可绕过，未验。
5. **真实门禁落地效果**：`DG_dropin` 是内存第二模块实例模拟；未改 `_g7_predicates.py`，未跑真实门禁 74 条全量回归（`:603`）。
6. **5 条 AMBIG 的最终真值**（C20/A01–A04）：`FORCED` 只是保守应判，本工作不裁定（`:602`）；`forced` 口径下 DG_pure fp=10/fn=12（`_dga_adversarial_out.json:scoring_forced`），本工作主结论只取 strict。
7. **语言学真值裁定**：C05「没准」、C11/C12「非不」、A01/A02/A03 等是否成词/是否真 DN，需第三方裁定（`ADVSET_INDEPENDENCE.md:569`），本工作按 `expect` 字段采信，未独立裁定。
8. **繁体 / 英文 / 被动 / 跨行 / >24 字距 / 多语种混合 / BCC-CCL 语料加权覆盖率**：本集无此覆盖（`:604`、`DNEG_GENERATIVE.md:121` 标 token 级覆盖率未验）。
9. **统计关联的外部效度**：Fisher `p=0.00185` 只在 17 条负样本、单个 41 条集上成立；未做跨集/跨判定器的置信区间，不能外推。
10. **上游结论是否被推翻**：本工作不改上游 `partial → unconfirmed` 判定、不改 `severity`、不改任何台账（「两件台账」绝对只读）。只补「这个新模式是构造偏差 + 恒真式」这一层。

---

## 6 纪律自检

- 保护树零写：会话末实跑 `git status --porcelain -- <7 保护路径>`（`_fp_ANALYSIS.md` §7 命令 25）输出为 `MM` 两件台账 + `??` 五个目录，HEAD 仍 `2657458`。本会话对这些路径只做只读操作（`ls`/`grep`/`sed`/`Read`、Python 的 `ast.literal_eval` 与 `compile/exec` 内存加载），两个自写脚本均设 `sys.dont_write_bytecode = True` 且只把结果写到 `lead/fp_pattern_20261109/`；9 件编排方指纹会话末 `ALL_MATCH = true`（`_fp_recompute_stdout.txt:34`）—— 未发现写入痕迹，但**未**对全部保护文件逐一做会话首/末 mtime+hash 全量比对（会话首 gitStatus 快照被截断），故此项标「未做全量快照比对」，不冒充全量证明。
- 9 件编排方指纹 `ALL_MATCH = true`（`_fp_recompute_stdout.txt:34`）。
- 零真机（未启动 `gamemd.exe`/`ra2loader`/`YURI.exe`，未 `taskkill`，未读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；未 commit、未 push。
- Python 全为 `python -I -X utf8`；脚本内 `sys.dont_write_bytecode = True`，保护件用 `compile/exec` 内存加载或 `ast.literal_eval`，未写 `__pycache__`；指纹只用 `hashlib.sha256`。
- 只做模式分析：未改任何对抗集 `CASES`、未改任何谓词、未改语料；§2(d) 的判别实验**只给设计、未执行**。

## 7 本会话实跑命令清单（Bash 工具调用 25 次；部分为一次调用内的复合命令）

> 以下按类型列举，不用序号断言调用顺序；两次主实跑以 ★ 标出。`cd /d/Project/ra2-campaign-forge &&` 为各命令前缀，从略。

- 目录清点（1 次）：`ls -la` 五个只读目录 + `mkdir -p lead/fp_pattern_20261109/`（写域创建）
- 指纹与 JSON 结构（5 次）：`python -I -X utf8 -c "…hashlib 复核 10 件指纹…"`（9/9 与编排方一致）；`…三份 JSON 顶层键…`；`…_ai_grade_out.json 判据/首行…`（`grade_distribution={"L1":17,"L0":24}`、`d1_n=19 d2_n=41 d3_n=21`）；`…逐行打印 41 行…`（**失败**：`KeyError: 'len'`，C03 的 `lcs_train` 为空 dict；已如实记录）；`…逐行完整打印 41 行（兼容 lcs 缺 len）…`
- 评分/分级数据结构（3 次）：`…_dga_adversarial_out.json scoring_strict/forced + cases[0]…`；`…_ai_verify_out.json 分级/评分…`（`{"L0":33,"L1":8}`、`orch_hits_match=true`）；`…verify rows/share_rows 结构…`
- 源码定位（6 次）：`grep -n "L0|L1|…" _ai_grade.py`（`:134-139 grade()`）；`grep -n "L0|…|记忆污染|…" ADVSET_INDEPENDENCE.md`；`grep -n "decomposable|share_rows|…" _ai_verify.py`（`:394-402`）；`grep -n "def detect|CATCH|PASS|…" _ai_verify.py`；`grep -n "训练集|…|held-out|…" DNEG_GENERATIVE.md`；`grep -n "构造|生成|…|同源|…" DG_ADVERSARIAL.md`
- 逐条数据（3 次）：`…41 cases attack/why 逐条…`；`…验证 CATCH⇔hit非空⇔d3_pure…`（0 反例）；`…17 条 P 样本原文/判定/最近训练句…`
- ★ **主实跑 1**：`python -I -X utf8 lead/fp_pattern_20261109/_fp_recompute.py > lead/fp_pattern_20261109/_fp_recompute_stdout.txt 2>&1` → `PYTHON_EXIT=0`，65 行；随后 `wc -l` 确认
- 文档条款与对照实跑（3 次）：`grep -n "① 未登记词|14/14|…" _ai_verify_stdout.txt` + `sed -n '174,181p' DG_ADVERSARIAL.md` + `sed -n '542,560p' ADVSET_INDEPENDENCE.md`（14/14 CATCH、10/10 PASS）；`sed -n` 读 `DNEG_GENERATIVE.md:274-281,330-350` 与 `ADVSET_INDEPENDENCE.md:395-420,563-575,599-606`；`git status --porcelain -- <7 保护路径>` + `git status --porcelain -- lead/fp_pattern_20261109/` + `grep … H5_GOVERNANCE_FIX.md`
- 补充核算（1 次）：`python -I -X utf8 -c "…两种读法核算 d1=- 判对…"` → 8/8 负样本判对；22 条口径 12 判对 / 9 判错
- ★ **主实跑 2**：`python -I -X utf8 lead/fp_pattern_20261109/_fp_classify.py > lead/fp_pattern_20261109/_fp_classify_stdout.txt 2>&1` → `PYTHON_EXIT=0`，39 行
- 会话末校验（1 次）：`ls -la lead/fp_pattern_20261109/` + `python -I -X utf8 -c "…绑定行格式校验…"`（报告 5 行 + stdout 16 行） + `git status --porcelain -- <7 保护路径>` + `git log --oneline -1`（HEAD `2657458`）

合计 Bash 工具调用 **25 次**（另 8 次 `Read`/`Write`/`Edit`/`TodoWrite` 等非 Bash 工具调用，不计入）。

关键实跑输出定位：`_fp_recompute_stdout.txt:3`（绑定行）、`:34`（9/9 指纹）、`:37`（六判定器全同）、`:38`（fp=7/fn=11）、`:41`（min_edit 79 句全同）、`:44`（分级 24/17/0/0 与 33/8/0/0）、`:45`（文档统计）、`:48-50`（fp7 逐条）、`:51-53`（d1 空逐条 + P16/P17 反例）、`:54`（Fisher p=0.00185）、`:55`（min_edit 无单调）、`:58`（d3 恒真）、`:59`（d1 目录内生）、`:60-61`（构造同源计数）、`:62`（判定器对照）、`:63`（fn11 逐条）；`_fp_classify_stdout.txt:9-16`（fp7 分类）、`:17-22`（fn11 分类）、`:24`（汇总）、`:27-32`（六判定器对照）、`:35-37`（H5 9/9 命中串来自手写表）。
