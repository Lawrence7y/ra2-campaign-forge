# FP_PATTERN_ANALYSIS.md — 误报模式分析定稿（含复核回件 partial 修正）

**角色**：误报模式分析件撰写员（只做模式分析）。
**纪律**：零真机 / 零采样代码 / 零 hook；`lead/advset_indep_20261109/`、`lead/dg_adversarial_20261109/`、`lead/dneg_generative_20261109/`、`lead/h5_governance_20261109/`、`lead/gate_fp7_20261108/`、两件台账绝对只读；唯一写域 `lead/fp_pattern_20261109/`。不改任何对抗集 / 谓词 / 语料；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib.sha256`。
**本会话实跑**：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_pattern_20261109/_fpw_verify.py > D:/Project/ra2-campaign-forge/lead/fp_pattern_20261109/_fpw_verify_stdout.txt 2>&1` → `PYTHON_EXIT=0`，77 行（自写 detect / grade，不 import、不 exec 任何 `_fp_` / `_fpv_` 脚本）；另有 1 次 `-c` 绑定行核算与 1 次 `git status --porcelain` + `git log --oneline -1`（下文逐处给命令与输出）。输出：`_fpw_verify_stdout.txt` / `_fpw_verify_out.json`。

---

## 1 目的与边界

**目的**：判定「本集 7 条误报全在训练构式上」是因果、构造偏差，还是两者的混合；给因果与偏差**两侧各自可成立**的证据；逐条分类 fp/fn；给 DG/H5/R12 失败类型对照与最小修复顺序；如实登记复核 verdict 与未验项。

**边界（铁律）**：只做模式分析，**不改任何对抗集 `CASES`、谓词、语料**。§3 的 E1–E6 判别实验**只给设计、全部未执行**；§4 的最小修复**只给方向、未实施**；未模拟补词 / 加表 / veto 调整后的效果；未裁定语言学真值；未跑真实门禁 74 条回归。零真机（未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`、未 `taskkill`、未读活进程内存）、零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）。保护件均用 `compile/exec` 内存加载或 `ast.literal_eval` 静态抽取，`sys.dont_write_bytecode = True`。

**被核对象与复核结论（本 ask 的【复核】字段）**：`_fp_ANALYSIS.md`（50001 B）经复核员独立实现复现，核心结论确认，但支撑证据有 **7 处缺陷**，`verdict = partial`。按本 ask 的纪律：**partial 标 unconfirmed**，本定稿逐一吸收 D1–D7 并修正原表述；核心结论（不能判因果 / 定义性恒真 + 构造偏差 + 局部过宽 / 非记忆污染）保留，但因复核为 partial，本件对该结论整体标 **unconfirmed（复核 partial）**，不冒充已确认。

**本会话复核输出定位**：`_fpw_verify_stdout.txt:34`（9 件指纹）、`:37`（六判定器全同）、`:38`（41×6 verdicts 零差）、`:40`（四级分级）、`:41`（fp7 逐条）、`:42`（7/7 d1/d3）、`:43`（d3 口径）、`:44`（d1=- 全 41）、`:45`（P16/P17）、`:46`（2×2 + Fisher）、`:47`（min_edit 双方向阈值）、`:48`（79 句重建）、`:50`（边界探针）、`:51`（DG_STATS）、`:52`（fp7 护栏探针）、`:53`（d1 目录源码）、`:54`（构造同源计数）、`:55`（零学习扫描）、`:56`（d1 内生性）、`:57`（d1 空负样本六判定器）、`:58`（六判定器 fp 全 d1 非空）、`:60`（D1）、`:61`（D2）、`:62`（D3）、`:63`（D5）、`:64`（D7）、`:66`（fp7 逐条）、`:67`（fn11 探针）、`:68`（fn 三类计数）、`:69`（fn d1 非空）、`:71`（held-out 条款）、`:72`（H5/G7 源码）、`:73`（P16/P17）、`:74`（对照表）、`:76`（保护树零写）。

---

## 2 上游指纹（九件）+ 分级与构式对应复核

### 2.1 九件编排方指纹（本 ask 的【编排方指纹】字段逐字录入，本会话 hashlib 独立实算）

`_fpw_verify_stdout.txt:34` → `[orch9_check] {"n": 9, "all_sha_and_bytes_match": true, "mismatch": []}`，即 **9/9 SHA256 + 字节数双同**。复核员亦独立重算 9/9 全同（`_fpv_verify_stdout.txt:34` `orch9_fingerprint_check`）。九件完整绑定行（本会话 `_fpw_verify_stdout.txt:3-33` 给 16 件，此处列编排方 9 件）：

被核对象 SHA256 = 668f4606f1a54c51433074f6271b3ee336acee7348aab89e91b75a46e6557b6f，字节数 = 41557
被核对象 SHA256 = f3e52f828c3c75875ed82fb41c5d38d04419e3c1e87a5ce01b6b1f3f1ea27298，字节数 = 28117
被核对象 SHA256 = a7bbb835b9cca4dafb2bfd27d1959aa4b139a8a0f532b14d726411a66f800cea，字节数 = 43943
被核对象 SHA256 = 395a0a0a3f9316504510b83c023d078d8adcede33f0d20432cf31fcccf99286c，字节数 = 55528
被核对象 SHA256 = 7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1，字节数 = 12322
被核对象 SHA256 = b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c，字节数 = 8540
被核对象 SHA256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120，字节数 = 11743
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

（依次对应 `_AI_ADVSET_INDEPENDENCE.md` / `_ai_grade_out.json` / `_ai_verify_stdout.txt` / `_dga_adversarial_out.json` / `_dg_core.py` / `_h5_pasteable.py` / `_g7_predicates.py` / `PENDING_DECISIONS.md` / `GOAL_THREE_TARGETS_20261018.md`；完整 16 件及路径见 `_fpw_verify_stdout.txt:2-33`。）

### 2.2 四级数字（L0 / L1 / L2 / L3）

`_fpw_verify_stdout.txt:40`：`strict = {L0:24, L1:17, L2:0, L3:0}`、`strict_stored = {L1:17, L0:24}`；`loose = {L0:33, L1:8, L2:0, L3:0}`、`loose_stored = {L0:33, L1:8}`。严格 / 宽松两口径 `strict_match = true` / `loose_match = true`（`_fp_recompute_stdout.txt:44`），本会话自写 `grade_strict()` 复算与存储一致（判据源码 `_ai_grade.py:134-139`）。**两口径 L2 = L3 = 0**。`_fpw_verify_stdout.txt:37` 另给 41 条 × 6 判定器自写重跑与 `_dga_adversarial_out.json:scoring_strict` 逐项全同（`all_identical=true`：`DG_pure 7/11`、`DG_dropin 8/10`、`H5_lit 9/14`、`H5_gov 7/14`、`R12 2/17`、`R12_lit 2/17`）；`:38` 给与 `_ai_verify_out.json` 41×6 verdicts `n_diff=0`。

### 2.3 ★ 7 条误报的 `d1` / `d3` 逐条（strict，`DG_pure`，n=36）

`_fpw_verify_stdout.txt:41`（复核员 `_fpv_verify_stdout.txt:44` 同）：

| id | expect → verdict | `d1` | `d3_pure` | `d3_dropin` | `hit` | `min_edit` | grade | attack |
|---|---|---|---|---|---|---|---|---|
| P06 | PASS → CATCH | 不敢不 | True | True | 不敢不承认 | 3 | L0 | ① |
| P07 | PASS → CATCH | 不敢不 | True | True | 不敢不承认 | 4 | L0 | ① |
| P08 | PASS → CATCH | 并不否认 | True | True | 并不否认 | 2 | L0 | ①④ |
| P09 | PASS → CATCH | 并不否认 | True | True | 并不否认 | 4 | L0 | ③④ |
| P10 | PASS → CATCH | 并不否认 | True | True | 并不否认 | 5 | L0 | ⑤ |
| P11 | PASS → CATCH | 并非不,非不 | True | True | 并非不宣告 | 3 | L0 | ② |
| P12 | PASS → CATCH | 并不否认 | True | True | 并不否认 | 6 | L0 | ② |

`fp7_all_d1_nonempty_and_d3_true = {all_d1_nonempty:true, all_d3_pure_true:true}`（`:42`）。

**★ `d3` 是定义性恒真，且必须指明判定器口径（修正 D4）**：`_ai_verify.py:394-402` 的 `hit_in_tables(h)` 以 `x["hits"]["DG_pure"]` 为入参（`:413-414`），而 `_ai_verify.py:128-130` 定义 `DG_pure = CATCH if p`、`hits["DG_pure"] = h[0]["hit"] if h else ""` ⇒ **hit 非空 ⇔ CATCH**，`d3_pure` 由 hit 反推。本会话 `_fpw_verify_stdout.txt:43`：`n_pure_catch=19, n_d3_pure=19, pure_catch_eq_d3_pure_set=true`；`n_dropin_catch=21, n_d3_dropin=21`；`n_d3_any=21`、`d3_any_eq_pure_catch=false`、`d3_any_eq_dropin_catch=true`。故原回件「41 条 CATCH⇔d3=True 零反例」应精确写为「**`DG_pure` CATCH ⇔ `d3_pure`，19/19**」；按 `d3_any=21` 读则不等价（多 P17、C08）。「7/7 `d3`=True」等价于「7/7 都 CATCH」，零信息量。

### 2.4 `d1=-` 是否全判对

**仅在编排方列举的 8 条负样本上成立；全 41 条口径不成立**。本会话 `_fpw_verify_stdout.txt:44`：`d1` 空共 **22 条**；8 条 `expect=PASS` 负样本 **8/8 判对**（`_fp_recompute_stdout.txt:51` 逐条 P01 me=3 / P02 7 / P03 15 / P04 8 / P05 6 / P13 10 / P14 4 / P15 4，全 `d3_pure=false`、全 PASS）；但 13 条 `expect=CATCH` 的 `d1=-` 样本里 **4 判对 / 9 判错（fn）**，`pos_fn_ids = [C01,C02,C03,C04,C05,C07,C08,C09,C10]`，`all_correct=false`。另有 `A04`（AMBIG，strict 排除）1 条。全 41 条口径 12 判对 / 9 判错（21 条可评分）。**另有 2 条 `d1` 非空却判对的负样本被 15 条列表省略**：`_fpw_verify_stdout.txt:45` → P16（`d1=['莫不']`, me=7, PASS）、P17（`d1=['并非不','非不']`, me=3, PASS）。加上后 17 条负样本 2×2 为 `(d1非空&fp=7, d1非空&判对=2, d1空&fp=0, d1空&判对=8)`，`P(fp|d1非空)=0.7778`、`P(fp|d1空)=0.0`、Fisher 单侧 `p=0.00185109`（`:46`；复核员精算 36/19448 同）。**统计关联显著 ≠ 因果**（§3）。同一 `d1=-` 在负样本 8/8 判对、在正样本 9/13 漏判 ⇒ 支配结果的是 `expect` 分组，不是「是否训练构式」。

### 2.5 `min_edit` 与误报的关系（含 D2 修正）

`_fpw_verify_stdout.txt:48`：自建 79 条训练句、自写 Levenshtein 重建 41 条 `min_edit`，与 `V["near"]` 41/41 全同（`all_match_stored=true`）。`:47`：`fp_me=[2,3,3,4,4,5,6]`、`ok_me=[3,3,4,4,6,7,7,8,10,15]`，**重叠 {3,4,6}**；违单调递增 12 对、违单调递减 49 对；具体反例 P08(me=2,fp) vs P01(me=3,ok)、P12(me=6,fp) vs P05(me=6,ok) / P01(me=3,ok)。**D2 修正**：原回件「穷举阈值最佳 10/17」只搜了 `me>=t ⇒ CATCH` 一侧（`_fp_recompute.py:303-304`）；本会话双方向穷举（`:47`、`:61`）得 `me>=t` 最佳 **10/17**（t=16..19 并列，原脚本取 t=16），`me<=t ⇒ CATCH` 最佳 **12/17**（t=5 或 6）。「10/17 是全局最优」不成立，须限定为单侧。两方向均 <17/17 且值域重叠 ⇒ **无单调关系、无阈值可分**，结论保住。

---

## 3 模式性质：★ 因果 vs 构造偏差双解释（不许只选一边）

**判定前置**：两侧证据**各自都能成立**，按「相关性不是因果」的纪律**不能判为因果**，也不能判两者谁是主因（判别实验 E1–E6 全部未执行）。构造偏差侧证据更强且更直接；因果解释 A 只能**降级限定**为「表内构式 + 护栏未穷尽 ⇒ 过宽」的局部机制。整体标 **unconfirmed（复核 partial）**。

### 3.1 解释 A（真实因果 / 「训练构式使误报更易发生」）—— 可成立的证据

1. **选择器必然性有源码依据**：`_dg_core.py:114-128` 的 `DG_DROPIN_RE` 只由 `NEG1·MID·NEG2`（T12）与 `NEG1·GAP·V·COMP·X`（T3）两条模板 + 7 张闭合表的笛卡尔积拼成，`pattern = "(?:t12|t3)" + govern`（`:128`），零自由通配（`:138` `wildcards=1` 仅 T3 受控补语）。本会话 `_fpw_verify_stdout.txt:51` → `cartesian_total=105492, rule_count=2, pattern_chars=836, all_pure_hit_decomposable=true`。⇒ **任何 CATCH 的 `hit_text` 必为表内构式**，这是结构性必然。
2. **★ 受控替换实跑（本会话自跑）**：固定表内构式「前稿不敢不承认」不变、只换边界词。`_fpw_verify_stdout.txt:50` → 14 个未登记词 `unreg_BREAK_false_and_pure_CATCH = 14`（14/14 CATCH），10 个已登记词 `reg_pure_PASS=10`（10/10 PASS）且 `reg_dropin_CATCH=10`（10/10）。边界词能开关 fp，是「护栏未穷尽 ⇒ 过宽」的直接候选机制。词表源码：`_ai_verify.py:486-504`。
3. **fp 根因逐条可定位护栏**（`_fpw_verify_stdout.txt:52` 精确正则探针）：每条恰 1 个 regex Match；P06/P07/P08 的 `pre` 分别含未登记「其实 / 说到底 / 尽管」；P10 `coord_outside_hit=true`（「或」在 hit_text 外）；P11/P12 `quote_re_matched=false, masked_changed=false`（ASCII 双引号 / 书名号未登记）。复核员 `_fpv_probe2_stdout.txt:9-10` 同。源码：`DG_BREAK_RE` 10 词（`_dg_core.py:89`）、`_BQ` 不含转折词（`:86`）、`DG_QUOTE_RE` 4 类（`:92`）、`_SECOND` 14 词（`:88`）、`DG_COORD_RE`（`:91`）、`comp{0,4}?`（`:118`）、`govern≤24`（`:125`）、`_mask_quotes`（`:148-158`）、`_scope`（`:161-165`）、二次 veto 只查 `hit_text`（`:179-184`）。
4. **统计关联显著**：Fisher `p=0.00185109`（`:46`）。

### 3.2 解释 B（构造偏差 / 「误报恰好都用了训练构式，是造样本的方式决定的」）—— 可成立且更强的证据

1. **特征与结果共用同一张表（测量内生）**：本会话 `_fpw_verify_stdout.txt:53` 直读 `_ai_grade.py:48-58`：`CATALOG` 由 `s34["GAPS"]`、`DG.R12_TEN`、`H5.H5_DN_EXTRA.split("|")`、`DG.PSEUDO_DN` 拼成；`:103` `d1 = [k for k in CAT_IN_TRAIN if k in s]`；`:64-78` `CAT_IN_TRAIN` 定义为「目录条目在 DG 训练句子里作子串」；`:91` `FAMILY` 再并入 `DG.MID/PSEUDO/NEG1/NEG2`。而 CATCH 由同一批表生成的 `DG_DROPIN_RE` 判定 ⇒ 「用了训练构式」与「被 DG 命中」不是两个独立变量。
2. **`d3` 恒真**（§2.3，`:43`）：19 CATCH ⇔ 19 `d3_pure`，零经验信息。
3. **构造者读被测源码造样本**：`DG_ADVERSARIAL.md:23` 自述七条不变式逐字复述设计文档；`_fpw_verify_stdout.txt:54` → `attack 非空 26/41`、`why` 引 `_dg_core.py:` 行号 5/41、点名表/行号 18/41（沿用 `_fp_recompute.py:341` 口径；本会话另给一个更窄正则得 16/41，如实并列）、**fp7 7/7 `attack` 非空**。`ADVSET_INDEPENDENCE.md:266-281` 判「生成机制与受测对象同源，L3 完全不成立」；`:544-546` 要求构造者盲化；`:550` 明写「不得让表内构式 + 未登记边界词占满 fp 组」；`:588` 明写「L2+L3=0 须写『本集只测构式记忆』」。
4. **反例被省略、对照组被切掉**（§2.4）：9 条 `d1=-` 的 fn 与 P16/P17 两条 `d1` 非空却判对的负样本被 15 条列表省略；P 组按「两个独立否定、无 DN 构式」造（自然 `d1=-` 且判对），fp 组按「表内构式 + 未登记边界」造（自然 `d1` 非空且 CATCH）⇒ `d1` 分布是构造输入。
5. **★ 修正 D6：原回件「跨判定器决定性反证」属论证误设，但结论方向被加强**。原回件把「六判定器 fp 全落 `d1` 非空」当作三个独立系统的经验巧合来否证「DG 特有记忆毒性」。本会话 `_fpw_verify_stdout.txt:56-58` 与复核员独立加核显示：H5 真正 **29 条纯字面支 29/29 全在 `CAT_IN_TRAIN`**、G7 十式 **10/10 在 `CAT_IN_TRAIN`** 且 `g7_ten_equals_DG_R12_TEN=true`；8 条 `d1` 空负样本在六判定器上 `n_any_CATCH=0`。故「六判定器 fp 全 `d1` 非空」（`:58`）对 H5/R12 是**测量口径的近乎定义性必然 + 负样本被构造成无 DN 构式**，不是三个独立系统的经验重合。**但「H5/R12 零学习」这一源码事实独立成立**（`:55`：三份源码 learning-keyword 全 0 命中，仅 `re.compile`；`_h5_pasteable.py:31-40`、`_g7_predicates.py:76`），故「记忆污染是 DG 特有学习缺陷」仍被否证 —— 只是不能靠「三系统经验巧合」这条推理链。本发现**加强**构造偏差结论。
6. **修正 D3：「机会面积」表述须弱化**。原回件 §4(d) 写「表越宽 ⇒ fp↑fn↓ 同一条权衡曲线」。本会话 `:62`：R12(10 支) fp=2/fn=17 → H5_lit(30 支) fp=9/fn=14 → DG_pure(105,492 串) fp=7/fn=11，`fp_monotone_increasing=false`（反例 H5_lit 表窄于 DG 却 fp=9>7），仅 `fn_monotone_decreasing=true`。准确表述：**表更宽使 fn 下降；fp 另受护栏/引证屏蔽影响**，不能说同一条递增曲线。D1 修正后的 H5 支数见 §5(c)。

### 3.3 若因果：源码机制（限定版）

「训练构式更易误报」若作因果读，机制不在「训练」，而在三层护栏全是闭合词表、且切断动作只在纯函数里执行：`DG_DROPIN_RE` 构式必须落表内且 24 字窗口允许跨边界搭桥（`_dg_core.py:100-142`）；`_BQ`（`:86`）不含转折词，转折只靠 `DG_BREAK_RE`（`:89` 10 词）在 `_scope()`（`:161-165`）切断；`DG_QUOTE_RE` 4 类（`:92`）、`_mask_quotes`（`:148-158`）只在 `dg_double_neg`（`:167-186`）内调用；`DG_SECOND_SUBJ_RE`（`:90`）/`DG_COORD_RE`（`:91`）的二次 veto 在 `:179-184` **只检查 `hit_text = m.group(0)`**（`:177`），不含其后的边界/第二主语/并列词 ⇒ P09/P10 必然绕过。交付形态更严重：`_g7_predicates.py:92` `dbl = bool(DOUBLE_NEG_RE.search(pre))` 直接跑正则，`r12_scan`（`:144`）复用 `r10_context`，四个 guard 在 `co_names` 全 False（`DNEG_GENERATIVE.md:173`）。**但这不是「训练构式被记住所以误报」**：DG 无训练集权重、无拟合参数，`NEG1/MID/NEG2`（`:37-82`）是人工枚举常量；「训练构式」只是构造者用来造样本的自测语料目录。

### 3.4 若构造偏差：为什么 fp 恰好都用了训练构式

四条互补理由（均有实跑 / 文件依据）：(i) 要触发 CATCH 必须让只由闭合表笛卡尔积生成的 `DG_DROPIN_RE.search()` 返回 Match（`_dg_core.py:114-128`），表外构式拼不出，构造者想造 fp 别无选择（`:51` `all_pure_hit_decomposable=true`）；(ii) `attack` 以受测不变式编号命名、`why` 引 `_dg_core.py:89/:86/:92/:118/:182-184` 行号（`DG_ADVERSARIAL.md:23`、`ADVSET_INDEPENDENCE.md:266-281`）；(iii) 负样本组被设计成互补形状（`_dga_adversarial_out.json:cases[*].why` 全是「两个独立否定、无 ¬¬P 管辖链」）；(iv) 分界口径本身来自被测表：`d1` 目录取自 DG 自身常量（`_ai_grade.py:48-58`），`d3` 取自 DG 自身命中串（`_ai_verify.py:394-402`）⇒ 循环论证，不是独立检验。`ADVSET_INDEPENDENCE.md:544/569/588` 三处自陈等于上游已把这条偏差写明。

### 3.5 ★ 能区分两者的实验设计（**全部未执行**）

共同原则：把「构式是否在表内」从「是否被检测」解耦；构造者盲化；按族分层；真值第三方裁定。

- **E1 表内/表外 × 边界已登记/未登记 2×2 析因**：固定模板 `{构式}{边界词}本件不宣告已生效`，构式取 (a) 表内（不敢不承认 / 并不否认）、(b) 表外语义等价真 DN（未登记 MID，如「不容不承认」）；边界词取 (a) 已登记（「另外」）、(b) 未登记（「其实」）。预判：表外格恒 PASS ⇒ 选择器约束；若表外格也 fp，因果的 «训练构式» 必要条件被否证。
- **E2 消融（直接判「补护栏」还是「删构式」）**：均不动构式表 —— (甲) 只把 14 个边界词 + 4 类引号登记进 `DG_BREAK_RE`/`DG_QUOTE_RE`；(乙) 只把 7 条 fp 命中的构式从 `NEG1/MID/NEG2` 删掉。若 (甲) 让 7/7 fp→PASS 且真阳不退化 ⇒ 根因是护栏未穷尽；若必须 (乙) 才消 fp ⇒ 才支持「表内构式本身带毒性」。**最推荐的判别实验**（`DG_ADVERSARIAL.md:308` 已列修复项但未执行）。
- **E3 盲化 held-out 重造**：由不读 `_dg_core.py` / 设计文档的第三方按外部语料（BCC/CCL）生成 ≥200 条，按「表内 / 表外 / 族外」各 1/3 分层，真值语言学裁定、`AMBIG` 标 `NEEDS_HUMAN`（`ADVSET_INDEPENDENCE.md:542-550`），报每层 fp/fn + 置信区间。
- **E4 交叉判定器**：同一批盲化样本喂表规模不同的三判定器（R12 10 支 / H5_lit 30 支 / DG 105,492 串），看 fp 是否按表结构分化。**注意 D6**：既有 41 条上「六判定器 fp 全 d1 非空」是口径必然，不能当独立证据用，须用盲化新样本。
- **E5 负对照扩样**：把「表内构式 + 正确切断」负样本（现只有 P16/P17）扩到与 fp 组等规模，拆开「构式记忆」与「护栏缺失」。
- **E6 表宽扰动**：按 `DG_ADVERSARIAL.md:247` 放大倍数逐项增删部件表并重跑 E3 集，看 fp 是否随机会面积线性变化（D3 后须同时记录护栏/引证屏蔽变量）。

**执行状态**：§3.5 六个实验本会话**全部未执行**（纪律：只做模式分析）。既有实跑只是对 41 条既有数据的被动观察与复算。

**什么会推翻主结论**：在本 41 条、L2=L3=0、构造者读源码自造、`d1` 与被测表同源的前提下主结论稳固；能推翻它的是 E1–E3（尤其表外/族外层出现足量 fp，或只有「删构式」才能消 fp）。因未执行，只能判「因果不能成立为一般机制」，不能判两者谁为主因。

---

## 4 两种失败类型：定义 + ★ fp/fn 逐条分类 + 修复方向

### 4.1 定义（含术语修正）

- **覆盖不足**（新构式抓不到 = fn）：句子含真 ¬(¬P) 但 `DG_pure=PASS`，且 `hit_text` 空 / `d3_pure=false`。本集 11 条 fn 中 **8 条**属此类。
- **记忆污染**（训练构式上误报 = fp）：7 条 fp 全满足「`d1` 非空 + `d3_pure=True` + `hit` 为表内构式」，表面符合。但 **★ 本项目里这是范畴错误**：DG / H5 / R12 全是静态正则或人工闭合常量表（`_dg_core.py:142`、`_h5_pasteable.py:40`、`_g7_predicates.py:76`），无训练集权重、无拟合参数、无学习、无记忆存储（本会话 `_fpw_verify_stdout.txt:55` 三份源码学习关键字 0 命中）。「训练构式」只是构造者自测语料目录（`ADVSET_INDEPENDENCE.md:189`）。可观测的替代命名是 **「过宽 / over-inclusive（护栏污染）」**：表内构式被放进本应切断却未切断的语境。该机制不可测、不可证伪，标 **unconfirmed**。
- **★ 第三类：抑制污染 / veto 误杀**（表内构式上的 fn，3 条）。任务的二分不完备，如实修正为三类；其中 C11/C12 恰是 `d1` 非空（训练构式）上的**漏判**，与「训练构式 ⇒ 误报」反向，又一条反对因果读法的证据。

### 4.2 ★ fp=7 逐条分类（全部「过宽 / 护栏污染」）

本会话 `_fpw_verify_stdout.txt:66`（逐条 `why`）、`:52`（精确护栏探针）、`_fp_classify_stdout.txt:2-8`（复核后正确行号；原回件引 `:9-16` 错位见 D5）：

| id | `d1` | `d3_pure` | `hit` | me | 缺失护栏 / 源码 |
|---|---|---|---|---|---|
| P06 | 不敢不 | True | 不敢不承认 | 3 | 未登记转折「其实」；`DG_BREAK_RE` 10 词 `_dg_core.py:89`、`_BQ:86`、`govern≤24 :125` |
| P07 | 不敢不 | True | 不敢不承认 | 4 | 未登记追补「说到底」；同上 |
| P08 | 并不否认 | True | 并不否认 | 2 | 未登记让步「尽管」+ `NEG2` 收「否认」`:63-67` 使 T12 零通配拼出 |
| P09 | 并不否认 | True | 并不否认 | 4 | 第二主语「监理方」不在 `_SECOND:88` + 二次 veto 只查 `hit_text :179-184` |
| P10 | 并不否认 | True | 并不否认 | 5 | 「或」在 hit_text 之外 ⇒ `DG_COORD_RE:91` 二次 veto 不触发（`:182-184`） |
| P11 | 并非不,非不 | True | 并非不宣告 | 3 | ASCII 双引号不在 `DG_QUOTE_RE:92` 4 类内 ⇒ `_mask_quotes:148-158` 不生效 |
| P12 | 并不否认 | True | 并不否认 | 6 | 书名号《》未登记；引证跨度未被屏蔽 |

`_ai_grade_out.json:fp_attr` 逐条同归因；`ADVSET_INDEPENDENCE.md:399-410` 把 P06/P07/P08/P11/P12 归失败模式 A（5/7）、P09/P10 归 B（2/7）。

### 4.3 ★ fn=11 逐条分类（8 覆盖不足 + 3 veto 误杀）

本会话 `_fpw_verify_stdout.txt:67-69`（精确 regex/veto 探针）、`_fp_classify_stdout.txt:11-21`（正确行号）：

| id | 分类 | `d1` | 缺口 / 误杀 | 源码 |
|---|---|---|---|---|
| C01 | 覆盖不足（无 Match） | 空 | MID「容」不在 23 项表 | `_dg_core.py:55-61` |
| C02 | 覆盖不足（无 Match） | 空 | MID「许」未登记 | 同上 |
| C03 | 覆盖不足（无 Match） | 空 | MID「想」未登记 | 同上 |
| C04 | 覆盖不足（无 Match） | 空 | MID「想」未登记 | 同上 |
| C05 | 覆盖不足（无 Match） | 空 | MID「准」未登记 | 同上 |
| C07 | 覆盖不足（无 Match） | 空 | T3 `comp{0,4}?` COMP=5 字越界 | `:118` |
| C09 | 覆盖不足（无 Match） | 空 | comp 负向前瞻排除 `_SECOND`「本件」 | `:88`,`:118` |
| C10 | 覆盖不足（无 Match） | 空 | `_SECOND` 第二主语一刀切，未建模 ¬(本件¬宣告) | `:90`,`:179-181` |
| **C08** | **抑制污染（后置 veto 误杀）** | 空 | 有 Match「非登记一或二不可」再被 `DG_COORD_RE` 二次 veto 否（真 DN 当并列项） | `:91`,`:182-184` |
| **C11** | **抑制污染（正则内 PSEUDO 负向前瞻）** | 非不 | 「非不」在 `PSEUDO_DN` 被词首负向前瞻否决（根本不产生 Match） | `:81-82`,`:116` |
| **C12** | **抑制污染（同上）** | 非不 | 「非不认可」同机制 | `:81-82`,`:116` |

汇总：`fn_types = {覆盖不足:8, 抑制污染(veto 误杀):3}`、`fn_d1_empty=9`、`fn_d1_nonempty_ids=[C11,C12]`（`_fp_classify_stdout.txt:24`、`_fpw_verify_stdout.txt:68-69`）。**复核员加核**：3 条「veto 误杀」含**两种不同机制** —— C08 是后置 veto（`:182-184`），C11/C12 是正则内负向前瞻（`:116`），`_fpv_probe2_stdout.txt:2-3,13`；原回件正文合并称呼略粗，§3(d) 已分开列修复方向。

### 4.4 两类（实为三类）各自的修复方向 —— 只给方案，未实施

| 失败类型 | 修复方向 | 具体方案 | 代价 / 反作用 |
|---|---|---|---|
| **覆盖不足**（fn 8） | 加表 / 放宽模板 | ① `MID` 补 9 项（容/许/想/愿/甘/料/要/需/欲，`DG_ADVERSARIAL.md:189`）；② 放宽 `comp{0,4}?`；③ `_SECOND` 改命题管辖判定（救 C09/C10） | 按 `DG_ADVERSARIAL.md:247`：+1 MID = +1,239 串、+1 SPLIT_TAIL = +15,399 串 ⇒ **反向扩大过宽面** |
| **过宽 / 护栏污染**（fp 7） | 补护栏 / 收紧，**不动构式表** | ① 14 边界词补进 `:89`/`:86`；② 引号补 ASCII 双引号 / 书名号进 `:92`；③ 把 `_mask_quotes`/`_scope`/`DG_SECOND_SUBJ_RE`/`DG_COORD_RE` 并入 `_g7_predicates.py:92` 的 `dbl`（当前 4 guard 在 `co_names` 全 False，`DNEG_GENERATIVE.md:173`）；④ 二次 veto 改查 N2 后整窗 `:179-184` | 收紧会**扩大漏判面**；③ 与「一行替换、调用点零改动」交付形态冲突（`DNEG_GENERATIVE.md:184` 自标 unconfirmed） |
| **抑制污染 / veto 误杀**（fn 3） | 缩小 veto 作用域（两种机制分开） | ① `PSEUDO_DN` 词首负向前瞻改位置局部判定（C11/C12，`:116`）；② `DG_COORD_RE` 不否决 T3 COMP 内并列（C08，`:91/:182-184`） | 可能放过真伪构式（N14「非但不」、A01/A02） |

**关键判断**：加表扩大 fp 面、补护栏扩大 fn 面，两类主修复方向相反且互相放大 ⇒ 不能串行「先加表再去污」，必须六判定器 + 74 条回归双跑，以 `fp=0` 为上线门槛（`DG_ADVERSARIAL.md:308`）。**本会话未实施任何修复**。

---

## 5 对结论的影响

### 5.1 「不误判不成立」要不要修正 —— **数字不修，表述限定，撤「记忆污染」定性**

7 条 fp 逐条独立重跑复现（`_fpw_verify_stdout.txt:37`、`:38` `DG_pure fp=7 fn=11`）；`ADVSET_INDEPENDENCE.md:568` 已给「高（已复现）」。但原句若读作「DG 对自然语言新句会误判 / 泛化差」**不成立**：本集 L2=L3=0、构造者与实现同源、7 条 fp 全是「表内构式 + 未登记边界词」模板变体（`ADVSET_INDEPENDENCE.md:399,570` 已把「泛化差」标「低 / 未验」）。「记忆污染」定性要撤（§4.1 范畴错误）。上游 `:569` 已把「一般性不误判不成立」标 `unconfirmed`；**`:571` 实测是空行**，`severity = high` 正文在 `:574`（本会话 `_fpw_verify_stdout.txt:63`：原回件引 `:571` 属行号错位，见 D5）。本工作不改上游判定，只补「新模式主要是构造偏差 + 恒真式」。

### 5.2 ★ 记忆污染下 held-out 是否仍必要 —— **两种解释下均成立**

- **若失败是记忆污染**（对表内构式过拟合）：held-out 显然必要 —— 需表外样本验去污染是否成功。
- **若失败是构造偏差**：held-out 同样必要且更必要 —— 本集 L2=L3=0、构造者读 `_dg_core.py` 行号造样本，`ADVSET_INDEPENDENCE.md:281` 判「L3 完全不成立」；构造偏差不是「不需要 held-out」的理由，而是「现有 41 条不能替代 held-out」的直接证明。
- **两种解释下结论一致 ⇒ 对失败类型不敏感，稳健成立**。条款实读（本会话 `_fpw_verify_stdout.txt:71`）：`:542-543`（至少要有 L2 样本）、`:544-546`（构造者盲化，不得出现「未登记 MID」「COMP=5」「PSEUDO veto」）、`:550`（按族分层，不得让表内构式占满 fp 组）、`:559`（held-out 与回归分离）、`:569`（一般性断言受 partial / unconfirmed 约束）、`:570`（泛化差 低 / 未验）、`:588`（L2+L3=0 须写「本集只测构式记忆」）、`:604`（分布外误判率测不到）、`DG_ADVERSARIAL.md:308`（≥200 条第三方 held-out + P 组 `fp=0` 门槛 + guard 并入 `r10_context`）。
- **功能重定位**：本集能把 fp 定位到具体源码行（§3.3），故**最小修复不必等 held-out**；held-out 职责从「判定因果 / 验收原结论」改为「**验收修复 + 提供分布外样本**」。

### 5.3 H5 是否同类 —— **不是记忆污染，是覆盖不足为主 + 字面过宽为辅**

数据：`_fp_classify_stdout.txt:29-30` `H5_lit fp=9 fn=14`（fp_ids P06–P12 + P16 + P17）、`H5_gov fp=7 fn=14`；`:27-32` 六判定器 fp 全 `d1` 非空（但按 D6 此点不能当独立反证用）。判据：
1. **零学习**：`H5_DOUBLE_NEG_RE = re.compile("(" + H5_R12_TEN + "|" + H5_DN_EXTRA + ")")`（`_h5_pasteable.py:40`），10 支 + 19 式字面 + 1 通配的手写正则（`:31-40`，本会话 `_fpw_verify_stdout.txt:72` 逐行实读）；`_g7_predicates.py:76` 同。`:55` 学习关键字 0 命中 ⇒ 无记忆可污染。
2. **9/9 fp 命中串** `不敢不/并不否认/并非不/莫不` 全出自手写字面表（`_fp_classify_stdout.txt:35-37`；**D1 修正**：纯字面支数应为 **29**、总选择支 **30**，不是 37 —— 见下）。
3. **P16/P17 是 H5_lit 独有 fp**：`_fpw_verify_stdout.txt:73` → P16 lit=CATCH「莫不」/ gov=PASS，P17 lit=CATCH「并非不」/ gov=PASS；`H5_gov` 走 `h5_govern()`（`:102`、`:121`）后这两条消失，fp 由 9 降到 7（`_fpv_probe_stdout.txt:14-15` `lit_only=[P16,P17]`）。
4. 结论：**H5 = 覆盖不足为主（C13–C16 等全漏）+ 字面过宽为辅 + 无 veto 误杀**；与 DG 同类但更偏覆盖不足，同样不是记忆污染。

### 5.4 ★ DG / H5 / R12 失败类型对照表（strict，n=36，5 条 AMBIG 排除）

数据：`_dga_adversarial_out.json:scoring_strict`、`_fp_classify_stdout.txt:27-32`、`_fpw_verify_stdout.txt:37,74`。**D1 修正**：H5 支数按 `_h5_pasteable.py:31-40` 正确切分 = `H5_R12_TEN` 10 支 + `H5_DN_EXTRA` 19 纯字面 + 1 带通配 = **30 支（29 纯字面）**；`_fp_classify.py:108` 按 `|` 朴素切得 38 片、减 1 含 `[^` 片得 37，把通配支 `(?:宣告|认定|…|填)` 的 8 个内层碎片当成了独立支；`DG_ADVERSARIAL.md:245` 自述「30 支（19 纯字面 + 1 带通配 + 10）」与之冲突。本会话 `_fpw_verify_stdout.txt:60` 用正确 29 支重验 9/9 fp 命中仍全 true（结论保住，数字改）。**D3 修正**：下表不再写「同一条 fp↑fn↓ 曲线」，只报实测 fp/fn 与 fn 单调下降。

| 判定器 | 规则形态 | fp | fn | fp 全在 `d1` 非空 | fp 类型 | fn 类型 | 学习/记忆 |
|---|---|---|---|---|---|---|---|
| **DG_pure** | 2 模板 + 7 闭合表，105,492 生成串（`_dg_core.py:129-139`） | **7** | **11** | 7/7 是 | 过宽 / 护栏污染（未登记边界词/引号/第二主语/veto 作用域） | 覆盖不足 8 + veto 误杀 3（C08 后置 / C11,C12 前瞻） | **无** |
| **H5_lit** | 10 支 + 19 式字面 + 1 通配 = **30 支**（`_h5_pasteable.py:31-40`） | **9** | **14** | 9/9 是 | 字面表过宽 + 不屏蔽引证（P16/P17 独有） | 覆盖不足为主（C13–C16 全漏） | **无**（手写正则） |
| **R12** | 10 支字面正则（`_g7_predicates.py:76`） | **2** | **17** | 2/2 是 | 字面表过宽（P11/P17 引文内命中） | 覆盖不足为主（十式之外全漏） | **无**（手写正则） |

附加对照：`DG_dropin 8/10`、`H5_gov 7/14`、`R12_lit 2/17`（`:37`）。**表更宽 ⇒ fn 下降（17→14→11）成立；fp 不单调（2→9→7），另受护栏/引证屏蔽影响**。六判定器 fp 全在 `d1` 非空是测量口径必然（D6），不是三个独立系统的记忆毒性证据。

---

## 6 复核回件（绑定行格式）+ 结论 + 未验项

### 6.1 复核回件（verdict 如实记）

**复核员 verdict = partial**（本 ask 的【复核】字段）：核心结论确认（不能判因果 / 定义性恒真 + 构造偏差 + 局部过宽 / 非记忆污染，独立实现全部复现），但 2 处数字错误、1 处过度概括、1 处口径含糊、1 组引用行号错位、1 处「决定性反证」误设、1 处两批探针混引 ⇒ 整体 **partial，标 unconfirmed**。本会话逐项复跑 D1–D7 并吸收（下表给本会话实跑定位）：

| 缺陷 | 内容 | 修正后表述 | 本会话实跑 |
|---|---|---|---|
| D1 | H5 纯字面支 37 错 | **29 纯字面 / 30 总选择支**；9/9 fp 命中在 29 支下仍全 true | `_fpw_verify_stdout.txt:60`；复核员 `_fpv_probe3_stdout.txt:1-2` |
| D2 | 「最佳阈值仅 10/17」是单侧搜索 | `me>=t` 最佳 10/17（t=16..19 并列）、`me<=t` 最佳 **12/17**（t=5/6）；无单调关系结论保住 | `:47`,`:61` |
| D3 | 「表越宽 ⇒ fp↑fn↓ 同一曲线」过度概括 | **fn 单调下降成立；fp 不单调（2→9→7）**；机会面积表述弱化 | `:62`；`_fpv_probe3_stdout.txt:3` |
| D4 | 「41 条 CATCH⇔d3=True」未指明判定器 | 精确写「**`DG_pure` CATCH ⇔ `d3_pure` 19/19**」；`d3_any=21`、`DG_dropin CATCH⇔d3_dropin 21/21` | `:43`；`_fpv_probe3_stdout.txt:4` |
| D5 | 引用行号错位 | `_fp_classify_stdout.txt` fp7 在 **:2-8**、fn11 在 **:11-21**、汇总 :24、六判定器 :27-32、H5 命中串 :35-37；`:9` 空行、`:10` fn 标题；`ADVSET_INDEPENDENCE.md:571` 空行、`severity=high` 在 **:574** | `:63` |
| D6 | 「跨判定器决定性反证」误设 | H5 29 支 29/29、G7 十式 10/10 全在 `CAT_IN_TRAIN`；8 条 `d1` 空负样本六判定器 0/8 CATCH ⇒ 该模式是口径必然，不是三独立系统巧合；**但零学习源码事实独立成立**，结论方向不变而推理链重写 | `:56-58`；`_fpv_probe_stdout.txt:8` |
| D7 | 两批 14 词混引 | `_ai_verify_stdout.txt:245` 的 14 词含「哪怕/说白了」，`DG_ADVERSARIAL.md:177` 的 14 词含「反倒说/可」，**两次独立探针**，均 14/14 CATCH；反向 10/10 PASS 属第二批（`:178`） | `:64`；`_fpv_probe_stdout.txt:21` |

**复核员其他通过项**（本 ask 的【复核】字段）：① 九件指纹 9/9 双同、16 件绑定行格式全合规；② 分级/构式对应不采信自写实现全同；③ 双解释两侧证据齐备；④ fp/fn 逐条分类齐备；⑤ held-out 两解释下均成立；⑥ H5 非记忆污染确认；⑦ 越界检查通过（140 文件 / 89 次外部基线 `MISMATCH_vs_any_baseline=[]`、`ZERO_WRITES_BY_MTIME=True`、两支 stdout 落盘字节相同）。本会话独立复跑 `:76` → 140 保护文件、69 件有外部基线、`baseline_mismatch=[]`、`files_mtime_after_script_start=[]`、`new_pyc_after_script_start=[]`（**本会话的基线数 69 与复核员的 89 不同，因我只汇入 9 编排 + 16 绑定 + `_ai_verify_out.json` + `_dgv_protected_snapshot.json` 四组，少于复核员的汇入组数；两侧均为「零不一致」，本会话不冒充 89 件全量比对**）。

### 6.2 复核回件绑定行（格式固定，本会话 hashlib 独立重算）

被核对象 SHA256 = 5873fa7079b415cd5ca5fc51f4e9aaca84c702b897596aa50fdfd07df6e15277，字节数 = 50001

（`lead/fp_pattern_20261109/_fp_ANALYSIS.md`；命令：`python -I -X utf8 -c "…hashlib.sha256(read_bytes)…"`，输出即上式；与复核回件 `sha256Line` 字段全同。）

被核对象 SHA256 = e3fa86c3553b34a9914e3765482cf891db7d5befc9a1fcc84b9eafd66c234ba8，字节数 = 14277

（`_fp_recompute_stdout.txt`）

被核对象 SHA256 = c7a44e120fb090dca2f0965945292f6b9e233253b9f0f3ee3ff292b907e39cf2，字节数 = 9522

（`_fp_classify_stdout.txt`）

九件编排方指纹 + 16 件完整绑定行见 §2.1 与 `_fpw_verify_stdout.txt:2-33`。

### 6.3 ★ 本集准确表述（吸收 D1–D7 后）

> 在本 41 条由构造者读着 `_dg_core.py` 行号、按其七条不变式自造（26/41 带 `attack` 标签）、**L2=L3=0** 的对抗集上，严格口径（36 条可评分）`DG_pure` 为 **fp=7 / fn=11**，六判定器逐条独立重跑全同；7 条 fp 全部落在 DG 闭合表可拼出的构式上 —— 但这首先是**定义性必然**（`DG_DROPIN_RE` 只由闭合表笛卡尔积生成，任何 CATCH 的 `hit_text` 必为表内构式；`DG_pure` CATCH ⇔ `d3_pure` 19/19，`d3` 由 hit 反推），其次是**构造偏差**（`d1` 目录取自 DG 自身常量表并与 H5/G7 表同源，构造者按 `expect` 分工把 fp 组填满单一模板；9 条 `d1=-` 的 fn 与 P16/P17 两条 `d1` 非空却判对的负样本被 15 条列表省略）。因此**不能判为「训练构式导致误报」的因果，更不能定性为「记忆污染」**（DG/H5/R12 均无学习机制，三份源码学习关键字 0 命中；且「六判定器 fp 全 d1 非空」是口径必然而非独立反证，D6）。可成立的局部机制是「**表内构式 + 未登记边界词/引号/第二主语/veto 作用域 ⇒ 三层护栏同时失效的过宽**」（14 未登记词 14/14 CATCH 对 10 已登记词 10/10 PASS）。11 条 fn 中 **8 条覆盖不足、3 条过严 veto 误杀**（C08 后置 veto / C11,C12 正则内前瞻）。本集只测「表内构式 + 护栏」，能证伪「未限定词表的一般性不误判宣称」，**不能**证明「DG 泛化差 / 对分布外新句误判」，**不能**判定因果方向；Fisher `p=0.00185109` 的关联本身大半是定义性 / 构造性产物。**整体 verdict = partial → unconfirmed**（复核回件 partial；E1–E6 未执行）。

### 6.4 对抗集设计建议（7 条操作）

1. **2×2 强制分层**：每条标「构式 ∈ {表内/表外/族外}」×「边界 ∈ {已登记/未登记/无边界}」，各格均衡，fp/fn 按格分报（`ADVSET_INDEPENDENCE.md:544,550`）；**不允许 fp 组只由「表内 × 未登记」一格构成**。
2. **构造者盲化 + 真值第三方**：生成过程不读被测表/常量/源码行号；形状来自外部语料或第三方语言学家；`AMBIG` 显式标 `NEEDS_HUMAN`（`:543,547`）。
3. **特征与判定解耦**：`d1` 类标签须来自独立外部语料，不得由被测 `NEG1/MID/NEG2/PSEUDO_DN` 拼出；`d3` 类标签不得从 `hit_text` 反推（本集 `d3` 恒真）。至少报一个与判定器无关的分层变量。
4. **负对照等量**：每组「表内 × 未登记」fp 候选配等量「表内 × 已登记」与「表外 × 未登记」负对照；本集只有 P16/P17 两条且被列表省略。
5. **修前/修后消融双跑**：每次干预（加表 / 补护栏 / 缩 veto）分别跑，报 Δfp/Δfn；把 E2 的「只补护栏」vs「只删构式」作为标准动作。
6. **报每族 fp/fn + 置信区间 + 表宽对照**：≥200 条按族分层，同时跑 ≥2 个表规模不同的判定器报 fp 重合度；`L2+L3=0` 时强制写「本集只测构式记忆」（`:550,588`）。
7. **登记「能/不能证伪」**：把因果方向、分布外误判率、修版后状态显式列入不能证伪清单（`:550,604`）。

### 6.5 DG 最小修复先修哪类 —— **先修 fp（过宽 / 护栏污染）**，未实施

1. **危害**：fp 是门禁误杀；`DG_ADVERSARIAL.md:308` 把「P 组 `fp=0` 才准上线」列为门槛，`ADVSET_INDEPENDENCE.md:574` 维持 `severity=high`（fp 优先）。
2. **局部可验证、不放大表规模**：7 条 fp 全可定位到 4 处护栏（`_dg_core.py:89/92/88/182-184`），补边界词/引号 + 把 4 个 guard 并入 `_g7_predicates.py:92` 即可；**不动构式表**，不触发 1,239–15,399 倍生成串放大（`DG_ADVERSARIAL.md:247`）。
3. **顺序**：先加表会先扩大过宽面，回归成本更高。
4. **既有实跑支持**：14/14 vs 10/10 边界探针（`:50`；注意 D7 两批 14 词不同，不可合并为一次实验）。
5. **约束**：补护栏会扩大漏判面，且与「一行替换」交付形态冲突（`DNEG_GENERATIVE.md:184` 自标 unconfirmed）；须同步跑 11 条 fn + 74 条回归，不能单独上线。**本会话未实施任何修复。**

### 6.6 判不了什么 / 未验项（如实列）

1. **因果方向**：E1–E6 **全部未执行**，只做被动观察与既有数据复算；不能判两解释谁是主因，只能判「因果不能成立为一般机制」。
2. **「记忆污染」机制存在性**：本项目无学习系统，该机制在本项目内不可测、不可证伪；只否证了它作为本集失败类型的适用性。
3. **DG 泛化能力 / 对分布外新句误判率**：L2=L3=0，测不到（`ADVSET_INDEPENDENCE.md:604`）。
4. **修版后状态**：未改任何谓词、未模拟补词/加表/veto 调整效果（`:606`）；7 条不变式在修版后是否仍可绕过，未验。
5. **真实门禁落地效果**：`DG_dropin` 是内存第二模块实例模拟；未改 `_g7_predicates.py`，未跑 74 条全量回归（`:603`）。
6. **5 条 AMBIG 最终真值**（C20/A01–A04）：`FORCED` 只是保守应判，不裁定；forced 口径 `DG_pure fp=10/fn=12`（`_dga_adversarial_out.json:scoring_forced`），本工作主结论只取 strict。
7. **语言学真值裁定**：C05「没准」、C11/C12「非不」、A01/A02/A03 是否成词/真 DN 需第三方裁定（`:569`），本工作按 `expect` 采信。
8. **繁体 / 英文 / 被动 / 跨行 / >24 字距 / 多语种 / BCC-CCL 加权覆盖率**：本集无覆盖（`:604`）。
9. **统计关联外部效度**：Fisher `p=0.00185109` 只在 17 条负样本、单个 41 条集上成立；未做跨集 / 跨判定器置信区间，不能外推。
10. **上游结论是否被推翻**：不改上游 `partial → unconfirmed` 判定、不改 `severity`、不改任何台账（两件台账绝对只读）；只补「构造偏差 + 恒真式」这一层。
11. **未做会话首/末全量快照逐文件 mtime+hash 比对**：本会话只做 140 文件 / 69 件外部基线的 hash 比对 + 全量 mtime 检查（`:76`），复核员做了 140 文件 / 89 次基线全量比对（其【复核】⑦）；本会话不冒充该全量证明，标「未做全量快照比对」。
12. **本定稿自身状态**：复核 verdict = **partial → 本件标 unconfirmed**；核心结论经两轮独立实现复现但未被 E1–E6 判别实验确认。

### 6.7 纪律自检（本会话实跑）

- **★ 主实跑**：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_pattern_20261109/_fpw_verify.py > D:/Project/ra2-campaign-forge/lead/fp_pattern_20261109/_fpw_verify_stdout.txt 2>&1` → `PYTHON_EXIT=0`，77 行。
- **绑定行核算**：`python -I -X utf8 -c "…hashlib.sha256 三件被核交付件…"` → `_fp_ANALYSIS.md` 50001 B、`_fp_recompute_stdout.txt` 14277 B、`_fp_classify_stdout.txt` 9522 B，SHA 见 §6.2。
- **越界 / 状态**：`git status --porcelain -- lead/advset_indep_20261109/ lead/dg_adversarial_20261109/ lead/dneg_generative_20261109/ lead/h5_governance_20261109/ lead/gate_fp7_20261108/ lead/PENDING_DECISIONS.md lead/GOAL_THREE_TARGETS_20261018.md` → 输出 `MM lead/GOAL_THREE_TARGETS_20261018.md` / `MM lead/PENDING_DECISIONS.md` / `??` 五目录，与会话首 gitStatus 快照一致；`git status --porcelain -- lead/fp_pattern_20261109/` → `?? lead/fp_pattern_20261109/`；`git log --oneline -1` → `2657458 GOAL-3T: 台账 §400→§508 与 D-07..D-11 裁决登记入账`。HEAD 未变，未 commit / push。
- `_fpw_verify_stdout.txt:76`：140 保护文件、69 件外部基线、`baseline_mismatch=[]`、`files_mtime_after_script_start=[]`、`new_pyc_after_script_start=[]`；写域文件全部 `_fp_` / `_fpv_` / `_fpw_` 前缀或本定稿 `FP_PATTERN_ANALYSIS.md`。
- 零真机 / 零采样 / 零 hook；Python 全为 `python -I -X utf8` + 绝对路径；`sys.dont_write_bytecode = True`；指纹只用 `hashlib.sha256`；未改任何 `CASES`、谓词、语料；E1–E6 与最小修复均**未执行 / 未实施**。

---

**必现要素索引**：L0/L1/L2/L3（§2.2）、`d1`（§2.3/2.4/3.2）、`d3`（§2.3/3.2 D4）、`min_edit`（§2.5 D2）、因果（§3.1/3.3）、构造偏差（§3.2/3.4）、覆盖不足（§4.1/4.3）、记忆污染（§4.1，范畴错误 + unconfirmed）、held-out（§5.2）、H5 对照（§5.3/5.4）、未验（§6.6）、复核 verdict partial → unconfirmed（§1/§6.1/§6.3）。
