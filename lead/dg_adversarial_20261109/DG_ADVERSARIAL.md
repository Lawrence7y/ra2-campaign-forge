# DG_ADVERSARIAL.md — DG 生成式「不误判两个独立否定」的独立对抗验证

> 本件为 DG 对抗撰写员交付件。落点：`lead/dg_adversarial_20261109/DG_ADVERSARIAL.md`（唯一写域）。
> 编排方【复核】verdict = **partial**；按交付规则 partial 一律标 **unconfirmed**，见 §6。本件如实登记，不把 partial 写成通过。
> 纪律：零真机（不启动 gamemd.exe / ra2loader / YURI.exe，不 taskkill，不读活进程内存）；零采样代码（不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；保护件绝对只读；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。

---

## 1 目的与边界

**目的**：只做对抗验证，独立检验 `lead/dneg_generative_20261109/`（DG 生成式双重否定方案）宣称的「19/19 覆盖、十式不退化、不误判两个独立否定、`fp=0`」是否成立，并把 DG 与 H5 字面超集、R12 十式三者做量化取舍。

**边界（全部实读 / 实跑，不改动任何既有件）**：

| 项 | 口径 | 证据 |
|---|---|---|
| 不改 DG 生成式 / 不改 H5 / 不改任何既有件 | 保护件绝对只读；本会话只写 `lead/dg_adversarial_20261109/` | 会话首/末 `git status --porcelain -- <7 保护路径>` 结果完全相同（§1 命令 C0/C7）；`git log --oneline -1` 仍 `2657458` |
| 对抗样本必须自己构造 | 41 条全部由本任务自造，与 DG 训练集（N01-N20 / V01-V15 / W01-W30 / 19 式 / H5_EXTRA）**精确零重合** | `_dgaw_verify_stdout.txt:37`：AST 抽取 272/125/147/154 串，`精确重合 = 0 []`；`_dga_adversarial_stdout.txt:12-18` 同源复核 |
| 「改后」数字 | 全部是**内存 Shim / 第二真实模块实例**模拟，非真实门禁落地 | `_dgaw_regress_stdout.txt:2` 被拦截写盘 = `lead/gate_pipeline_20261109/_gp_regression_out.json`；真实落地标 **未验** |
| 本会话实跑命令 | 4 条 Python 脚本 + 3 次 git/ls 检查，全部 `--` 绝对路径、`-I -X utf8` | §6 逐条列「实跑命令 + 输出」，代码引用 `文件:行` |
| 交付形态 | DG 申报「只换 `_g7_predicates.py:76` 一行、调用点零改动」；本件验证其 `co_names` 下 8 个 guard 全不执行 | `_dgaw_verify_stdout.txt:167-168`；`_dga_delivery_probe_stdout.txt:7-9` |

**七条不变式来源**：`lead/dneg_generative_20261109/DNEG_GENERATIVE.md:167` 逐字复述 `_dg_DESIGN.md:141-158` 的 7 条结构不变式：① `_scope()`/`DG_BREAK_RE` 按句界·逗号·冒号·转折词切断；② `_mask_quotes()` 屏蔽引证跨度；③ T12 零通配 + `MID` 闭合虚词表；④ `DG_SECOND_SUBJ_RE` 第二主语负向前瞻 + 二次 veto；⑤ `DG_COORD_RE` 并列 veto；⑥ `PSEUDO_DN` 伪构式 veto；⑦ 全程不做否定词奇偶计数。作者自述（`DNEG_GENERATIVE.md:184`）：这是「给定闭合表下的结构不变式，不是自然语言完备性定理」。

---

## 2 上游指纹（九件）+ DG 成绩复核

### 2.1 九件指纹（本会话 `hashlib` 独立重算，会话首/末两次）

实跑命令（脚本 `lead/dg_adversarial_20261109/_dgaw_verify.py:23-36`，执行见 C1）：
`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dg_adversarial_20261109/_dgaw_verify.py`

输出（`_dgaw_verify_stdout.txt:3-13` 与 `:171-182` 两次一致）：9 行 `MATCH`、`ALL_MATCH = True`、`ALL_MATCH_2 = True`。九件逐一见 §6 绑定行。**会话末二次重算仍 9/9 MATCH**，且 4 棵保护树 + 3 个保护件的 git status 与会话首完全相同（C0 与 C7），HEAD 未变。

### 2.2 DG 成绩复核（全部本会话独立重算，未采信原脚本输出）

| 申报成绩 | 本会话实跑输出 | 结论 |
|---|---|---|
| **19/19 覆盖** | `_dgaw_verify_stdout.txt:16`：`DG 19 式 = 19/19 ; H5 字面超集 = 19/19 ; R12 = 0/19` | 可复现 |
| **十式不退化** | `:17`：`十式 DG 全 CATCH = True ; R12 全 CATCH = True ; n(十式) = 10` | 可复现 |
| **作者自造 20 条 fp=0** | `:31`：`pure 真负样本 n=19 ; fp = 0 []`；`:34`：`N03 对照 pure/dropin/base = ['CATCH','CATCH','CATCH']` | 可复现（**但见 §2.5 双限定**） |
| **三层改善** | `_dgaw_regress_stdout.txt:6-13`：`r12 ok 39→40 (FN 35→34)`、`n13 71→72 (FN 3→2)`、`chain 69→70 (FP 2→2 零新增、FN 3→2)`；`:15`：结论变更仅 `[('GP-A1','PASS->CATCH')]` 1 条 | 可复现 |
| **core 与 pasteable 一致** | `_dgaw_verify_stdout.txt:18`：`core.pattern == pasteable.pattern = True ; pattern_chars = 836` | 可复现 |

### 2.3 ★ H5 超集是否也 19/19 —— 是

`_dgaw_verify_stdout.txt:16` 明确：`H5 字面超集 = 19/19`，与 DG 同分；`R12 = 0/19`。逐条 19 式在 `_dga_step1_stdout.txt:22-41`：`亦非不 / 未尝不 / … / 并不否认` 每条 `H5=True  DG_catch=True  R12=False`。
**结论**：「19 式全覆盖」只靠把 19 个字面加进词表即可达到，**不构成 DG 独特价值**（`_dga_compare_stdout.txt:27-31` 同结论）。DG 相对 H5 的增量在本自造集上只有 5 条：`C06/C13/C14/C15/C16`（`_dgaw_verify_stdout.txt:96-97`：DG_pure 独对 7 条里除 P16/P17 的 5 条 CATCH 项，均为「何尝不 / 不见得不 / 岂敢不 / 不由得不」等 19 式之外构式与分离式 COMP=4，H5_lit 全漏、DG_pure 全中）。

### 2.4 H5 支数口径修正（复核回件指出的可证伪数字）

编排方【验证】/【DG 实跑】曾写「`H5_DN_EXTRA` 28 支（27 纯字面 + 1 通配），连十式共 38 支」。本会话用 `sre_parse` 精确解析（`_dgaw_verify.py:79-100`）：

- `_dgaw_verify_stdout.txt:22-26`：`H5_DN_EXTRA 顶层 BRANCH arity = 20 ; 纯字面支 = 19 ; 含通配/内层选择支 = 1`；`H5_R12_TEN = 10`；`合计 = 20 + 10 = 30`；`朴素 re.findall(r'[^|]+', H5_DN_EXTRA) = 28`。
- 源码依据 `lead/h5_governance_20261109/_h5_pasteable.py:34-38`：`H5_DN_EXTRA` 是 19 个纯字面 + 1 支 `非[^，,。；;]{0,4}不(?:宣告|认定|…|填)`，该支内部还有 9 个 `|`；朴素按 `|` 切把它算成 10 段，故得 28。
- **本件采用精确口径 20 / 30 / 19**；§5 表内「H5 字面支」按 30 支（20 EXTRA + 10 TEN）记。此错误方向上把 H5 说大了，不改「19/19 同分」结论。

### 2.5 ★ `fp=0` 是「集内 + 纯函数」双限定，不只是集内

复核回件指出的新破口，本会话独立重跑（`_dgaw_verify.py:117-148`）：
`_dgaw_verify_stdout.txt:31-33`：`pure fp = 0 []`；`dropin fp = 1 ['N20']`；`base fp = 1 ['N20']`。
N20 = `「并非不宣告已生效」只是引文，本件不采信该说法`（`lead/dneg_generative_20261109/_dg_step34.py:83`）。`_mask_quotes` 只在纯函数 `dg_double_neg` 里执行（`lead/dneg_generative_20261109/_dg_core.py:167-173`），「一行替换」交付形态下不执行（`_dgaw_verify_stdout.txt:167-168` co_names 全 False），故**连作者自己的 20 条都守不住**，`DNEG_GENERATIVE.md:334` 自记 N20「R12 字面误命中」但 `:336` 的 `fp=0` 口径没写「纯函数」。
→ 正确表述：`fp=0` 只在「作者自造 20 条 + 纯函数口径」成立；交付形态下同集即 `fp=1`；本任务 41 条独立集上 `fp=7/17`（§3）。

### 2.6 GP-A2 / GP-A3 未改善的验证

`_dgaw_regress_stdout.txt:26-30`（逐条诊断）：

```
GP-A2  spans=0 tokens=[] r10=0 r12=0 n13=0 DG_r12=0 base_chain=PASS  DG_chain=PASS  | 本件登记闭合，母本即日起适用
GP-A3  spans=0 tokens=[] r10=0 r12=0 n13=0 DG_r12=0 base_chain=PASS  DG_chain=PASS  | 三值填毕，见证已由编排方签字
DEFAULT_TOKENS = ['已入账', '已追加', '已生效']
同义完成词族逐词 in_vocab = {'登记闭合': False, '即日起适用': False, '填毕': False, '已由编排方签字': False}
```

两条 `spans=0`（`lead/gate_pipeline_20261109/_gp_pipeline.py:58-70` 的 `extract_spans` 只认 `DEFAULT_TOKENS` 三词），各层 problems 全 0，结论均 `PASS→PASS` 无变化。`BAD_BAN` 五词（`_gp_regression.py:50`）亦不含上述四词。三条共同盲区里另两条属「同义完成词族未登记」，**不在双重否定方案射程**；标 **未验** 的是「是否应另立 C07 词表」，不是本件判定范围。

### 2.7 层间冲突与三项「未验其实已验」

- 作者 Shim 口径 `31→32`：`_dgaw_regress_stdout.txt:14` 复现。
- 真实一行替换口径 `31→31`：`_dgaw_regress_stdout.txt:19-21`（`chain 69/2/3 → chain_oneline 70/2/2`，`层间冲突 = 31 → 31`），与 `DNEG_GENERATIVE.md:393` 一致；**本会话已独立重跑，升为已验**。
- `DNEG_GENERATIVE.md:346` 的 `16/17 vs 0/17`：`_dgaw_extra_stdout.txt:9-26` → `DG 16/17 ; H5 0/17 ; R12 0/17`，**已验**。
- `DNEG_GENERATIVE.md:347` 分离型 post 整句 `0/4`：`_dgaw_extra_stdout.txt:29-34` → `DG_pure 0/4 ; DG_dropin 0/4 ; H5_lit 0/4`，**已验**（共同缺口）。
- 闭合表数量：`_dgaw_extra_stdout.txt:3-10` AST 实查 = **7 张**参与生成式（NEG1 59 / MID 23 / NEG2 21 / GAP 9 / SCOPE_VERB 29 / SPLIT_TAIL 5 / PSEUDO_DN 12）+ R12_TEN 对账锚 1 张 = 8 张；`DNEG_GENERATIVE.md:163` 写「6 张」与实现不符，本件采用 7 张。

---

## 3 自造对抗集（41 条，逐条应判 + 理由 + 六判定器实跑 + fp/fn）

### 3.1 构造与零重合

**全部 41 条由本任务自行构造，不从 DG 的负样本集里挑**（铁律：训练集自证无效）。逐条「应判什么 + 理由」在 `lead/dg_adversarial_20261109/_dga_adversarial.py:66-166`（`CASES` 每项第 4 字段 `expect`、第 5 字段 `why`），机器可读副本在 `_dga_adversarial_out.json:cases[*].why`。
AST（不执行）从 `_dg_step34.py` / `_dgv_probe.py` / `_dgv_neg2.py` / `_dg_step1.py` 抽取训练集字符串，精确零重合：`_dgaw_verify_stdout.txt:37` → `自造样本数 = 41 ; 训练集逐件抽取串数 = [('_dg_step34.py', 272), ('_dgv_probe.py', 125), ('_dgv_neg2.py', 147), ('_dg_step1.py', 154)] ; 精确重合 = 0 []`。

分组：`P01–P17`（17 条「两个**独立否定**」，应 PASS：逗号分隔、顿号并列、递进、无标点连写、带转折真否定、跨句、未登记引号引证）；`C01–C19`（19 条真 DN，应 CATCH：19 式外构式、分离式 COMP、第二主语、带转折真 DN、三否定词）；`C20 + A01–A04`（5 条 AMBIG 歧义，主统计排除，另给 forced 保守应判做敏感性分析）。

### 3.2 逐条结果（六判定器：`DG_pure` / `DG_dropin` / `H5_lit` / `H5_gov` / `R12` / `R12_lit`）

下表 `exp` = 应判；`理由` 摘要自 `CASES[*].why`（完整理由见 `文件:行`）；六列实跑来自 `_dgaw_verify_stdout.txt:38-78`，与 `_dga_adversarial_stdout.txt:21-61` 逐条一致。★ = 该条命中误判面。

| id | 应判 | 理由（摘要，逐条全本见 `_dga_adversarial.py:68-165`） | DG_pure | DG_dropin | H5_lit | H5_gov | R12 | R12_lit |
|---|---|---|---|---|---|---|---|---|
| P01 | PASS | 逗号切断，¬承认(旧稿) ∧ ¬宣告(本件)，非 ¬(¬P) | PASS | PASS | PASS | PASS | PASS | PASS |
| P02 | PASS | 顿号并列两项独立否定 | PASS | PASS | PASS | PASS | PASS | PASS |
| P03 | PASS | 三项独立否定递进两重逗号，无 ¬¬P 链 | PASS | PASS | PASS | PASS | PASS | PASS |
| P04 | PASS | 无标点但两否定间隔实词「母本后段」 | PASS | PASS | PASS | PASS | PASS | PASS |
| P05 | PASS | 「不核不录」并列动作，两次独立否定 | PASS | PASS | PASS | PASS | PASS | PASS |
| P06 ★ | PASS | 「其实」未登记为转折词（攻①），前段 DN 与后段独立否定被搭桥 | **CATCH** | CATCH | CATCH | CATCH | PASS | PASS |
| P07 ★ | PASS | 「说到底」未登记（攻①） | **CATCH** | CATCH | CATCH | CATCH | PASS | PASS |
| P08 ★ | PASS | 「尽管」未登记 + 「并不否认」完整否定谓语另起主语（攻①④） | **CATCH** | CATCH | CATCH | CATCH | PASS | PASS |
| P09 ★ | PASS | 「监理方」第二主语不在 `_SECOND`；NEG2 完整否定谓语零隔拼接（攻③④） | **CATCH** | CATCH | CATCH | CATCH | PASS | PASS |
| P10 ★ | PASS | 「或」在 `DG_COORD_RE` 内但二次 veto 只查 `hit_text`（攻⑤） | **CATCH** | CATCH | CATCH | CATCH | PASS | PASS |
| P11 ★ | PASS | ASCII 双引号未登记，DN 只是引文（攻②） | **CATCH** | CATCH | CATCH | CATCH | CATCH | CATCH |
| P12 ★ | PASS | 书名号《》未登记（攻②） | **CATCH** | CATCH | CATCH | CATCH | PASS | PASS |
| P13 | PASS | 「既…也…」关联并列两项独立否定 | PASS | PASS | PASS | PASS | PASS | PASS |
| P14 | PASS | 无标点两次独立否定，中间「亦」非 MID 合法项 | PASS | PASS | PASS | PASS | PASS | PASS |
| P15 | PASS | 转折后仍是单重否定，两处都只有 ¬ | PASS | PASS | PASS | PASS | PASS | PASS |
| P16 | PASS | 前句「莫不」周遍 DN 被逗号切断，token 落在后句 | PASS | PASS | CATCH | PASS | PASS | PASS |
| P17 | PASS | 「」内置空格，`_mask_quotes` 正确 PASS；但 dropin/R12/H5_lit 误命中 | PASS | CATCH | CATCH | PASS | CATCH | CATCH |
| C01 ★ | CATCH | 不容(不宣告)=必须宣告；MID「容」不在 23 项表（攻③） | **PASS** | PASS | PASS | PASS | PASS | PASS |
| C02 ★ | CATCH | 未许(不宣告)；MID「许」未登记（攻③） | **PASS** | PASS | PASS | PASS | PASS | PASS |
| C03 ★ | CATCH | 别想(不登记)；MID「想」未登记（攻③） | **PASS** | PASS | PASS | PASS | PASS | PASS |
| C04 ★ | CATCH | 甭想(不承认)；MID「想」未登记（攻③） | **PASS** | PASS | PASS | PASS | PASS | PASS |
| C05 ★ | CATCH | 没准(不承认)；MID「准」未登记（攻③） | **PASS** | PASS | PASS | PASS | PASS | PASS |
| C06 | CATCH | 「非…不可」分离式，COMP='五份原件' 恰 4 字落边界内 | CATCH | CATCH | PASS | PASS | PASS | PASS |
| C07 ★ | CATCH | 同一构式 COMP='五份原始件' 5 字 ⇒ `{0,4}?` 越界（攻③） | **PASS** | PASS | PASS | PASS | PASS | PASS |
| C08 ★ | CATCH | 「非…不可」真 DN；COMP 含「或」触发并列 veto 被误否决（攻⑤） | **PASS** | CATCH | PASS | PASS | PASS | PASS |
| C09 ★ | CATCH | 「非…不可」真 DN；COMP 含 `_SECOND` 项「本件」被负向前瞻排除（攻④） | **PASS** | PASS | PASS | PASS | PASS | PASS |
| C10 ★ | CATCH | 「本件」是「不宣告」主语但「并非」管辖整个命题 = 真 DN（攻④） | **PASS** | PASS | CATCH | CATCH | PASS | PASS |
| C11 ★ | CATCH | 「非不承认」= 并非不承认 = 承认，被 `PSEUDO_DN` 词首 veto 误杀（攻⑥） | **PASS** | PASS | CATCH | CATCH | PASS | PASS |
| C12 ★ | CATCH | 「非不认可」同上被 veto 误杀（攻⑥） | **PASS** | PASS | PASS | PASS | PASS | PASS |
| C13 | CATCH | 「何尝不」反问型真 DN，19 式与 H5 均未登记 | CATCH | CATCH | PASS | PASS | PASS | PASS |
| C14 | CATCH | 「不见得」+ NEG2「不」构成 ¬(¬认为) | CATCH | CATCH | PASS | PASS | PASS | PASS |
| C15 | CATCH | 「岂敢不」反问型真 DN | CATCH | CATCH | PASS | PASS | PASS | PASS |
| C16 | CATCH | 「不由得不」= 忍不住要承认，真 DN | CATCH | CATCH | PASS | PASS | PASS | PASS |
| C17 | CATCH | 转折后微句内才是真 DN | CATCH | CATCH | CATCH | CATCH | CATCH | CATCH |
| C18 | CATCH | 「然而」后「亦非不」= ¬(¬宣告) | CATCH | CATCH | CATCH | CATCH | PASS | PASS |
| C19 | CATCH | 三否定词（未/非/不），奇偶会误豁免 | CATCH | CATCH | CATCH | CATCH | CATCH | CATCH |
| C20 | AMBIG | 「莫不是」反问副词 + 内层「不是不承认」；真值需裁定（攻⑥位置局部性） | CATCH | CATCH | CATCH | CATCH | CATCH | CATCH |
| A01 | AMBIG | 「非但不 + 否认」两解；保守应 PASS/NEEDS_HUMAN | CATCH | CATCH | PASS | PASS | PASS | PASS |
| A02 | AMBIG | 「莫非」疑问副词 + 「并不否认」真 DN；保守应 PASS | CATCH | CATCH | CATCH | CATCH | PASS | PASS |
| A03 | AMBIG | 「不无」弱化肯定作状语，不是对 token 的 ¬¬P；保守应 PASS | CATCH | CATCH | CATCH | CATCH | CATCH | CATCH |
| A04 | AMBIG | 「没不承认」口语是否成词有争议；保守应 CATCH | PASS | PASS | PASS | PASS | PASS | PASS |

### 3.3 fp / fn 对比（严格口径 36 条 = 41 − 5 AMBIG；forced 41 条全计）

`_dgaw_verify_stdout.txt:80-93` 独立重算（与申报数字逐项一致）：

| 判定器 | strict fp | strict fn | forced fp | forced fn | P 组 fp (17) | C 组 fn (19) |
|---|---|---|---|---|---|---|
| **DG_pure**（声称「不误判」的纯函数） | **7** `P06,P07,P08,P09,P10,P11,P12` | **11** `C01..C05,C07,C08,C09,C10,C11,C12` | 10 | 12 | **7/17** | **11/19** |
| DG_dropin（一行替换交付形态） | 8（+P17） | 10（−C08） | 11 | 11 | 8/17 | 10/19 |
| H5_lit（字面超集，30 支） | 9 | 14 | 11 | 15 | 9/17 | 14/19 |
| H5_gov（带 G1–G4） | 7 | 14 | 9 | 15 | 7/17 | 14/19 |
| R12（既有十式） | 2 `P11,P17` | 17 | 3 | 18 | 2/17 | 17/19 |
| R12_lit | 2 | 17 | 3 | 18 | 2/17 | 17/19 |

`_dgaw_verify_stdout.txt:94-95`：`P 组 n=17 应 PASS ; DG_pure fp = 7/17`、`C 组 n=19 应 CATCH ; DG_pure fn = 11/19`。

**误判面拆解（DG_pure）**：
- **fp 7 条**：未登记转折/让步词 P06「其实」/P07「说到底」/P08「尽管」；第二主语 P09「与监理方不宣告」；并列项 P10「或并不否认」；未登记引号 P11 ASCII `""` / P12《》。
- **fn 11 条**：MID 未登记 C01–C05（不容/未许/别想/甭想/没准）；COMP=5 字 C07；并列 veto 误杀 C08；第二主语 C09/C10；`PSEUDO_DN` 误杀 C11/C12。
- **交付形态额外差异 2 条**：P17 引证屏蔽只纯函数生效（pure PASS / dropin CATCH）；C08 并列 veto 只纯函数生效（pure 误 PASS / dropin 恰 CATCH）——见 `_dga_delivery_probe_stdout.txt:12-14`。

**结论**：DG 声称的「**不误判**」在本对抗集上**不成立**。严格口径 36 条错 18 条 = fp 7 + fn 11；只看「两个独立否定」P 组 17 条 → `fp=7/17`；只看真 DN 的 C 组 19 条 → `fn=11/19`。作者训练集 `fp=0` 是集内 + 纯函数口径结论（§2.5）。severity = **high**：这是门禁谓词的误判面，且既定口径 `fp` 优先于 `fn`，7 条误拦不能接受。

---

## 4 七条不变式攻击（逐条给绕过尝试 + 实跑 + 边界结论）

全部实跑输出：`_dgaw_verify_stdout.txt:101-169`（本会话）、`_dga_adversarial_stdout.txt:79-185`（同源复核）、`_dgav_verify_stdout.txt:108-197`（复核员独立重跑）。代码依据：`lead/dneg_generative_20261109/_dg_core.py:85-92`（边界/引号/第二主语/并列常量）、`:116`（veto 词首负向前瞻）、`:118`（`comp {0,4}?` 且排除 `_SECOND`）、`:125`（`govern ≤24`）、`:128-139`（1 条 pattern + `DG_STATS`）、`:148-158`（`_mask_quotes` 4 类引号）、`:161-165`（`_scope` 只在纯函数）、`:167-186`（`dg_double_neg`：第二主语 veto `:179-181`、并列 veto `:182-184` 仅查 `hit_text`）。

### ① 按句界/逗号/冒号/转折切断 —— **被绕过**

- 尝试：`DG_BREAK_RE` 只登记 10 词（`_dg_core.py:89`：但/但是/然而/不过/却/只是/反之/相反/另外/另）。用 14 个未登记转折/让步/追补词构造 `前稿不敢不承认{词}本件不宣告已生效`（应 PASS）。
- 实跑：`_dgaw_verify_stdout.txt:102-116` → 14/14 上 `BREAK=False`、`DG_pure=CATCH`、`DG_dropin=CATCH`。词表：`其实/说到底/尽管/换言之/与此同时/反倒/可/反倒说/结果/终究/总而言之/归根结底/话说回来/退一步说`。
- 反向对照 `:117`：已登记 10 词上 `DG_pure=PASS 10/10`，但 `DG_dropin=CATCH 10/10` —— 切断**只在纯函数 `_scope` 里执行**。
- 结论：`_BREAK`（`:85`）与 `_BQ`（`:86`）只含标点，转折词靠 `DG_BREAK_RE` 纯函数切断；词表未穷尽 + 交付形态不执行 ⇒ 绕过成立。

### ② 引证跨度屏蔽（`_mask_quotes`）—— **点名形态正确，但另 4 类未登记 ⇒ 绕过**

- 任务书点名的「引号内置空格」形态 DG **反而正确**：P17 `「 并非不宣告已生效 」只是引文…` → `DG_pure=PASS`（`_dgaw_verify_stdout.txt:118`），因 `_mask_quotes` 把跨度内部置等长空格；`R12=CATCH`、`H5_lit=CATCH`、`DG_dropin=CATCH` 全误命中。
- 但 `DG_QUOTE_RE`（`_dg_core.py:92`）只认 4 类：`「」『』“”`` `。实跑 `:119-123`：ASCII 双引号 `"…"`、书名号《》、ASCII 括号 `(…)`、ASCII 单引号 `'…'` 四类**全部 `DG_pure=CATCH`（应 PASS）**。
- 结论：② 的屏蔽是「4 类引号 + 纯函数」双限定；未登记引号 + 交付形态两处均可绕过。

### ③ T12 零通配 + `MID` 闭合表 + `COMP ≤4` —— **被双向绕过**（★ 特别攻 MID / COMP）

- **MID**：`MID` 23 项（`_dg_core.py:55-61`）刻意不收实词。扫描 30 个候选，本会话独立重跑 9 个未登记项：`:124-133` → `容/许/想/愿/甘/料/要/需/欲` 全 `在表内=False`、`DG_pure=PASS`（真 DN 应 CATCH）。对照 `:118-120` 之类 `得/能/可/敢` 全 CATCH。`_dga_adversarial_stdout.txt:103-133` 给 30 项全表。
- **COMP**：`comp = (?:(?!_SECOND)[^BQ]){0,4}?`（`:118`）。本会话 n=0..7 扫描 `:134-142`：`n≤4 全 CATCH = True ; ≥5 全 PASS = True`，边界恰在 4→5。C07「非登记五份原始件不可」COMP=5 字 ⇒ 真 DN 漏判。
- **NEG2 反噬**：`NEG2` 含 5 个完整否定谓语 `否认/不承认/不认为/不宣告/不出现`（`_dg_core.py:63-67`）；`:143` → `NEG2 含完整否定谓语 = ['否认','不承认','不认为','不宣告','不出现']`，`'并不否认与监理方不宣告已生效' → DG_pure = CATCH`（跨主语零隔拼接，应 PASS）。「T12 零通配」≠「不误判」。
- 结论：闭合表未穷尽（漏 9 个 MID）、COMP 硬界 4 字、NEG2 完整谓语三处均可被具体构造绕过。

### ④ 第二主语负向前瞻 + 二次 veto —— **被绕过且结构性不可达**（★ 特别攻）

- 静态证明：`_SECOND` 14 个词（`_dg_core.py:88`）在 `NEG1/MID/NEG2/GAP/SCOPE_VERB/SPLIT_TAIL/PSEUDO_DN` 全部条目里出现 0 次 → `_dgaw_verify_stdout.txt:144`：`_SECOND 任一项出现在任何闭合表条目内 = {} （全空 ⇒ 结构性不可达）`。且 `comp` 的负向前瞻已排除 `_SECOND`，故 `dg_double_neg:179-181` 的 veto 对 T12/T3 均不可达。
- 双向反例：`:145` `并非本件不宣告已生效`（「本件」是「不宣告」主语但「并非」管辖整命题 = **真 DN 应 CATCH**）→ `DG_pure=PASS`（fn）、`H5_lit=CATCH`（靠过宽通配蒙对）；`:146` `并不否认甲方不宣告已生效`（第二主语「甲方」未登记，**应 PASS**）→ `DG_pure=CATCH`（fp）。
- 二次 veto 实际触发：`_dga_delivery_probe_stdout.txt:3` → 41 条上仅 1 次（C08），且是把**真 DN 误否决**。
- 结论：④ 结构性不可达 + 词表未穷尽，双向都被绕过。

### ⑤ 并列项否决 —— **被绕过**

`DG_COORD_RE`（`:91`）只查 `hit_text`（`:182-184`）。实跑 `_dgaw_verify_stdout.txt:147-149`：
- P10 `本件不承认或并不否认已生效`：「或」在 `hit_text='并不否认'` **之外** ⇒ 不否决，`DG_pure=CATCH`（应 PASS，fp）。
- C08 `非登记一或二不可才算本件已生效`：「或」在 `hit_text` **之内** ⇒ 否决掉「非…不可」真 DN，`DG_pure=PASS`（fn）；`DG_dropin=CATCH`（不跑 veto 反而对）。
- 对照 `非登记原件不可` → 两口径都 CATCH。
- 结论：只查命中串、不查全句 ⇒ 双向后果，绕过成立。

### ⑥ `PSEUDO_DN` 12 项 —— **被绕过**（★ 特别攻）

- veto 是**词首**负向前瞻（`_dg_core.py:116`）。12 项逐项实跑 `_dgaw_verify_stdout.txt:150-162`：6 项 `raw_regex=False`（无非/莫非/不非/没没/非非/不没），6 项 `raw_regex=True`（莫不是/无无/没不/非不/没没不/不不不）——后 6 项因后缀「不承认」另起匹配仍 CATCH，即**位置迁移拦不住**。
- 词表既误杀真 DN：C11「非不承认」/C12「非不认可」`DG_pure=PASS`（fn）；又拦不住 C20「莫不是不承认」、A01「非但不否认」、A02「莫非并不否认」（`_dga_adversarial_stdout.txt:57-59` 全 CATCH）。A04「没不承认」是否成词/是否真 DN 需人工裁定。
- 结论：词表 12 项 + 词首局部 veto 两端都漏，绕过成立。

### ⑦ 全程不做否定词奇偶计数 —— **是设计选择，不是可绕过的 guard；但不构成「不误判」保证**

四象限 `G1–G4` 实跑 `_dgaw_verify_stdout.txt:163-166`：

| 象限 | 语料 | neg_count | 应判 | 奇偶法 | DG_pure |
|---|---|---|---|---|---|
| G1 | 不查不验本件已生效 | 2 | PASS | CATCH（错） | PASS（对） |
| G2 | 未漏核，并非不宣告本件已生效 | 3 | CATCH | PASS（错） | CATCH（对） |
| G3 | 非登记五份原始件不可才算本件已生效 | 2 | CATCH | CATCH（对） | PASS（**错**） |
| G4 | 前稿不敢不承认其实本件不宣告已生效 | 3 | PASS | PASS（对） | CATCH（**错**） |

「不做奇偶」避开 G1/G2 两类错（`_g7_predicates.py:74-75` 亦同口径），但防不住 G3（COMP 越界）/G4（未登记转折）两类。**⑦ 不是「不误判」的充分条件**。

### 4.8 边界结论（7 条不变式的适用域）

这 7 条是「给定 **7 张闭合表 + 2 条模板 + 纯函数 guard**」下的结构不变式，**不是自然语言完备性保证**。本会话实跑证明 ①②③④⑤⑥ 均可被具体构造绕过，⑦ 只是避免两类错、不防另两类错。边界量化：边界词仅 10 个（本会话实跑漏 14 个）、引号仅 4 类（漏 4 类）、`MID` 23 项（漏 9 候选）、`COMP ≤4`、`GOVERN ≤24`、`SPLIT_TAIL` 5、`PSEUDO` 12、`_SECOND` 14；guard 只在纯函数（交付形态 8 个 `co_names` 全 False，`:167-168`）；对语义歧义无裁定路径。

---

## 5 三者取舍（DG vs H5 vs R12）

### 5.1 fp / fn 表（本会话独立重算，严格 36 条 / forced 41 条）

见 §3.3 完整表。要点：`DG_pure 7/11`、`DG_dropin 8/10`、`H5_lit 9/14`、`H5_gov 7/14`、`R12 2/17`。逐条独对（`_dgaw_verify_stdout.txt:96-99`）：
`DG_pure vs H5_lit → DG 独对 7 ['P16','P17','C06','C13','C14','C15','C16']，H5 独对 2 ['C10','C11']`；
`vs H5_gov → 5/2`；`vs R12 → DG 独对 7、R12 独对 6 ['P06'..'P10','P12']`（R12 因词表窄而少误报，代价 fn 17）；`vs DG_dropin → 1/1`（P17 / C08）。

### 5.2 生成式 vs 字面条：口径对齐（105,492 串 vs 30 支）

- DG `105,492` = **笛卡尔积可生成串数**，不是 105,492 个已验证构式：`lead/dneg_generative_20261109/_dg_core.py:129-136` → `59*23*21=28,497` + `59*9*29*5=76,995` = 105,492；`_dgaw_verify_stdout.txt:19` `DG_STATS` 逐项一致。pattern 836 字符、2 条模板、1 处通配。
- H5 = `H5_DN_EXTRA` **20 支**（19 纯字面 + 1 带通配）+ `H5_R12_TEN` 10 支 = **30 支**，pattern 162 字符（`_dgaw_verify_stdout.txt:22-28`）。编排方原写 28/38 系朴素按 `|` 切的口径错误（§2.4）。
- **优势（生成式）**：① 可泛化到未登记构式——本集 C13–C16 四条 H5 全漏、DG 全中；`DNEG_GENERATIVE.md:346` 的 `16/17 vs 0/17` 本会话已独立重跑为已验（`_dgaw_extra_stdout.txt:27`）。② 规则条数恒为 2，不随词表增长。
- **劣势（生成式）**：① 105,492 串**未逐串验证**，闭合表任一项改动都放大扰动（`_dgaw_verify_stdout.txt:169`：加 1 项 MID = +1,239 串、NEG1 = +1,788、NEG2 = +1,357、SPLIT_TAIL = +15,399、GAP = +8,555、SCOPE_VERB = +2,655）。② 安全约束（`_mask_quotes`/`_scope`/第二主语/并列 veto）**只存在于纯函数**，申报的「一行替换」交付形态下 `r10_context`/`r12_scan` 的 8 个 guard `co_names` 全 False（`:167-168`、`_dga_delivery_probe_stdout.txt:7-9`）。③ 过宽风险实证：N14「非但不」上 H5 字面误命中、DG 靠 `PSEUDO_DN` 避开，但 DG 又在 P06–P12 上过宽（fp 7）。④ 两者对分离型 post 整句**共同 0/4**（`_dgaw_extra_stdout.txt:34`，已验）。
- **劣势（字面）**：枚举不穷尽（19 式之外全漏）、通配支 `非[^，,。；;]{0,4}不(宣告|…)` 过宽反而在 C10/C11 上「蒙对」；但每条可逐条人工核对，加 1 项 = 精确 1 个新串。

### 5.3 维护成本

| | DG 生成式 | H5 字面超集 |
|---|---|---|
| 表数 | **7 张闭合表**（NEG1 59 / MID 23 / NEG2 21 / GAP 9 / SCOPE_VERB 29 / SPLIT_TAIL 5 / PSEUDO_DN 12）+ 5 组作用域常量（`_BREAK`/`_BQ`/`_SECOND`/`DG_COORD_RE`/`DG_BREAK_RE`/`DG_QUOTE_RE`）；AST 实查 `_dgaw_extra_stdout.txt:3-10` | 2 张 DN 字面表（10 + 20 支）+ 若干作用域正则（`_h5_pasteable.py:44-65`） |
| 加 1 个构式 | 至少改 1 张表，可能连带 veto 表/边界表/作用域表；扰动面按笛卡尔积放大 1,239–15,399 串（`_dga_adversarial_stdout.txt:187-194`） | `H5_DN_EXTRA` 加 1 个字面选择支 = 精确 1 个新串，可逐条核对 |
| 可核对性 | 836 字符正则 + 105,492 未逐串验证的积 | 162 字符 + 30 支可逐条读 |
| 单元断言 | `_dg_DESIGN.md:306` 承诺的「MID 不得含实词 / COMP ≤4 / GOVERN ≤24」断言**未实现**（`DNEG_GENERATIVE.md:175` 自记 `含 assert=False`） | 无此承诺 |

### 5.4 该用哪个（条件化建议，不给「基本成立」式概括）

1. **目标是「最小、可逐条核对、fp 优先、维护窗口短」** → 用 **H5 字面超集（30 支）+ 明确 `NEEDS_HUMAN` 兜底**，接受 fn 偏高（本集 14/19）。理由：每条改动可人工核对，不加 guard 也能审计。
2. **目标是「覆盖率 + 未来构式泛化」且能承担改造调用点** → 才考虑 **DG 生成式**：须把 `_mask_quotes`/`_scope`/`DG_SECOND_SUBJ_RE`/`DG_COORD_RE` 并入 `r10_context` 的 `dbl`（至少改 `lead/gate_fp7_20261108/_g7_predicates.py:92`）、补转折/让步词到 `CLAUSE_BREAK` 或 `_BQ`、T12 增 N2 前后向第二主语/并列检查、补单元断言，并**先过独立 held-out 对抗集**。当前「一行替换」形态不可落地（§6.3）。
3. **「宁可放过不可误拦」的低风险只读场景** → **R12 十式现状**：本集 `fp 2/17` 最低，但 `fn 17/19`，**不能用于宣称覆盖**。
4. 任何方案对 5 条 AMBIG（C20/A01–A04）都应降 `NEEDS_HUMAN`，不得直接 CATCH。

---

## 6 复核回件 + 结论 + 边界 + 落地前置条件 + 判不了什么 + 未验项

### 6.1 复核回件绑定行（本会话 `hashlib` 独立重算，`ALL_MATCH = True`）

格式严格按铁律：「被核对象 SHA256 = 」紧跟完整 64 位十六进制，中间不插路径/括号/星号/反引号/空格；随后「，字节数 = 」再写数字。九行逐一对应编排方【编排方指纹】九件，顺序一致。

被核对象 SHA256 = 7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1，字节数 = 12322
被核对象 SHA256 = 7b8ac203a8bb1a68b35c15c129cb2d3de676e70104eed0e9663763b91cfafad1，字节数 = 10688
被核对象 SHA256 = 94eb2a5ef2528b34659e2e7277914917e2176de08dd17fdd9ae5cd17e50af0d4，字节数 = 46334
被核对象 SHA256 = d99dd9f1bb90d062ae24e00bdf5d579c1e7830f29d36102544a5b1d44a7bf520，字节数 = 13854
被核对象 SHA256 = 5453edfa189a16b1295ee979777beab4e7eede15f1011566f170d5100e679167，字节数 = 2042
被核对象 SHA256 = b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c，字节数 = 8540
被核对象 SHA256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120，字节数 = 11743
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

### 6.2 复核 verdict 如实登记

编排方【复核】`verdict = partial`（`ranCommands=12`，`severity` 未改上游）。按交付规则：**partial → 相关结论标 `unconfirmed`**，不写「通过」。复核回件 `whatBreaksIt` 给的 2 处可证伪数字/口径错误 + 1 处新破口 + 3 处「未验」已验成，本件已逐项处理：

| 复核指出的项 | 本件处理 | 本会话实跑证据 |
|---|---|---|
| ① H5 支数 28/38/27 错 | 改 **20/30/19**（§2.4、§5.2） | `_dgaw_verify_stdout.txt:22-26` sre_parse BRANCH arity=20 |
| ② `fp=0` 应升级「集内 + 纯函数」 | §2.5 登记 N20 在 dropin/base 下 `fp=1` | `_dgaw_verify_stdout.txt:31-33` |
| ③ 新破口：交付形态连作者 20 条都守不住 | §2.5 已写入 | 同上 |
| ④ 3 项「未验」其实已验 | 16/17、0/4、真实一行替换 31→31 升**已验**（§2.7） | `_dgaw_extra_stdout.txt:27,34`；`_dgaw_regress_stdout.txt:19-21` |
| ⑤ 未登记边界词不止 10 / 引号不止 2 | 实跑 14 个词、4 类引号（§4①②） | `_dgaw_verify_stdout.txt:102-123` |
| ⑥ 闭合表 7 张（DG 文档写 6 张） | §2.7 采用 7 张 | `_dgaw_extra_stdout.txt:3-10` |

复核回件明确「主线结论全部复现、无 refuted 项、不报 refuted」，故本件不把复核升级为 confirmed，也不把 partial 淡化。凡上游 `DNEG_GENERATIVE.md` 的「不误判独立否定」「一行替换 + 调用点零改动」一般性断言，一律标 **unconfirmed**（该文档 `:5`、`:184`、`:418` 亦自标 unconfirmed）。

### 6.3 结论

1. **「不误判」是否成立**：**不成立**（在本 41 条独立自造集上）。严格口径 36 条错 18 条（fp 7 + fn 11）；P 组「两个**独立否定**」`DG_pure fp=7/17`；C 组真 DN `fn=11/19`；forced 41 条 `fp=10/fn=12`。作者 `fp=0` 是「20 条 + 纯函数」双限定的集内结论，交付形态下同集即 `fp=1`。`H5 超集` 与 DG 同为 **19-19**（R12 0/19），故 19/19 不是 DG 独特价值；DG 的独特价值只能靠「不误判 + 集外泛化」证明，前者被证伪，后者（C13–C16 泛化）虽成立但不足以抵消 fp。
2. **7 条不变式**：**6 条可被具体构造绕过**（①②③④⑤⑥），⑦ 是设计选择不构成保证；边界 = 7 张闭合表未穷尽 + `COMP ≤4` + `GOVERN ≤24` + guard 只在纯函数 + 语义歧义无裁定。逐处攻击见 §4，特别攻了 **MID**（漏 9）、**COMP**（4→5 断）、**第二主语**（结构性不可达 + 双向反例）、**PSEUDO_DN**（6/6 分裂）。
3. **边界是否诚实**：方向诚实（`DNEG_GENERATIVE.md:184` 自述「结构不变式，不是自然语言完备性定理」，`:173` 自记 co_names 全 False，`:336` 自记 fp=0 只在 20 条成立，`:418` 自标 unconfirmed），**但不够**：还应写入 ① 41 条独立集 `fp=7/17`、`fn=11/19`；② 交付形态 4 条 guard 不执行、安全证明不覆盖交付形态；③ 每张闭合表未穷尽性逐张量化；④ veto 只查 `hit_text` 且二次 veto 结构性不可达（41 条只触发 1 次且在真 DN 上）；⑤ 105,492 是笛卡尔积可生成串数、非已验证构式；⑥ 语义歧义应降 `NEEDS_HUMAN`；⑦ 无 BCC/CCL 语料、无繁体/英文/跨行/>24 字距覆盖、无真实门禁落地。
4. **落地建议**：**不落地为「一行替换」**。若落地须满足 §6.4 全部前置条件。severity = high（fp 优先口径下 7 条误拦不可接受）。

### 6.4 落地前置条件（全部满足才准上线）

① 与 DG 训练集零重合、由第三方构造、≥ 本集规模（41 条，建议扩到 ≥200 条并按构式族分层）的 held-out 对抗集，每条真值由所有者/语言学裁定（AMBIG 显式标 `NEEDS_HUMAN` 而非二值）；② `fp` 优先验收门槛：P 组 `fp=0` 才准上线；③ 把 `_mask_quotes`/`_scope`/`DG_SECOND_SUBJ_RE`/`DG_COORD_RE` 并入 `r10_context` 的 `dbl` 判定（至少改 `_g7_predicates.py:92`），转折/让步/追加连词补进 `CLAUSE_BREAK` 或 `_BQ`，T12 增 N2 前后向第二主语/并列检查；④ 补 `_dg_DESIGN.md:306` 承诺未实现的单元断言（MID 不得含实词、COMP ≤4 且排除 BQ/第二主语、GOVERN ≤24 非通配），随 7 张表一起验；⑤ 每次表改动跑全量生成串的 fp 扰动审计（本会话给出加项放大倍数 1,239–15,399）；⑥ 真实门禁（非内存 Shim）全量回归 + 层间冲突三口径（base / Shim / 一行替换）对齐；⑦ 明确退化路径：拿不准时降 `NEEDS_HUMAN`，不得直接 CATCH。

### 6.5 判不了什么（如实列）

1. 中文双重否定全域真值 / token 级频次（无 BCC/CCL 语料）；
2. 真实门禁落地效果（保护件绝对只读，`DG_dropin` 为内存第二模块实例模拟）；
3. 繁体 / 英文 / 被动 / 跨行 / >24 字距 / 多语种混合；
4. 5 条 AMBIG 的最终真值（保守应判仅作敏感性分析）；
5. 「不容不 / 未许不 / 非不认可 / 没不承认」是否属规范汉语真 DN（人工裁定）；
6. GP-A2/A3 同义完成词族、证据不独立、分离型 post 整句（不在双重否定方案射程）；
7. H5 补丁其它维度（G1–G4 全域），本工作只比双重否定一维；
8. 外部文献 132 构式等数字（来自任务书【设计】回件，本会话未重跑 WebSearch）。

### 6.6 未验项（逐项，不补造）

- **未验**：真实门禁落地（§6.5.2）；41 条以外语料 fp（§6.5.3）；AMBIG 五条真值（§6.5.4）；「不容不」等是否规范真 DN（§6.5.5）；BCC/CCL token 级加权频次与外部文献 132 构式（未重跑 WebSearch）；H5 补丁 G1–G4 其它维度；单元断言补齐后的效果；语义歧义裁定路径。
- **已由本会话升为已验**（原回件标未验）：`16/17 vs 0/17`（`_dgaw_extra_stdout.txt:27`）、分离型 `0/4`（`:34`）、真实一行替换层间冲突 `31→31`（`_dgaw_regress_stdout.txt:21`）、H5 支数 20/30/19（`_dgaw_verify_stdout.txt:22-24`）、闭合表 7 张（`_dgaw_extra_stdout.txt:10`）。
- **本会话未重跑的既有产物**：`_dga_step1_repro.py` / `_dga_compare.py` / `_dga_delivery_probe.py` / `_dgav_verify.py` 四个脚本及其 stdout 我**实读**并逐项引 `文件:行`，但用我自己写的 `_dgaw_verify.py` / `_dgaw_regress.py` / `_dgaw_extra.py` **独立重算了全部数字**（41 条六判定器、7 条不变式、74 条回归、9 件指纹），不把这些脚本的输出当作本会话的实跑。原回件自报「33 条 Bash 命令 / 12 条 Bash 命令」我未核实，不引用为事实。

### 6.7 本会话实跑命令与输出（全部 `python -I -X utf8` + 绝对路径）

| # | 命令 | 输出 / 关键行 |
|---|---|---|
| C0 | `cd D:/Project/ra2-campaign-forge && git status --porcelain -- <7 保护路径> && git log --oneline -1` | 保护件为会话前既有 `MM`/`??`，HEAD `2657458` |
| C1 | `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dg_adversarial_20261109/_dgaw_verify.py > .../lead/dg_adversarial_20261109/_dgaw_verify_stdout.txt 2>&1` | `PYTHON_EXIT=0`，184 行；`:3-13` 9/9 MATCH、`:16-19` 19/19+十式+DG_STATS、`:22-26` H5 20/30、`:31-34` fp=0/1/1、`:37` 零重合、`:38-99` 41 条逐条 + fp/fn + 独对、`:101-169` 7 条不变式、`:171-182` 末次 9/9 MATCH |
| C2 | `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dg_adversarial_20261109/_dgaw_regress.py > .../lead/dg_adversarial_20261109/_dgaw_regress_stdout.txt 2>&1` | `PYTHON_EXIT=0`；`:2` 写盘被拦截；`:6-15` 三层 39→40 / 71→72 / 69→70、冲突 31→32、变更仅 GP-A1；`:19-21` 真实一行替换 31→31；`:26-30` GP-A2/A3 `spans=0` + 同义词 `in_vocab` 全 False |
| C3 | `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dg_adversarial_20261109/_dgaw_extra.py > .../lead/dg_adversarial_20261109/_dgaw_extra_stdout.txt 2>&1` | `PYTHON_EXIT=0`；`:3-10` 7 张闭合表、`:27` 16/17 vs 0/17、`:34` 分离型 0/4 |
| C4 | `cd D:/Project/ra2-campaign-forge && git status --porcelain -- <7 保护路径> && git log --oneline -1 && ls -1 lead/dg_adversarial_20261109/ && stat -c '%n %s %y' lead/gate_pipeline_20261109/_gp_regression_out.json` | 保护件状态与 C0 全同、HEAD 仍 `2657458`；写域仅 `_dga_*`/`_dgav_*`/`_dgaw_*` + 本件；`_gp_regression_out.json` 仍 38575 字节、mtime `2026-11-09 13:53:57`（会话前既有，未被写） |

**代码行证据汇总**：`lead/dneg_generative_20261109/_dg_core.py:37-50`（NEG1 59）、`:55-61`（MID 23）、`:63-67`（NEG2 21 含 5 完整谓语）、`:69`（GAP 9）、`:71-75`（SCOPE_VERB 29）、`:77`（SPLIT_TAIL 5）、`:81-82`（PSEUDO_DN 12）、`:85-92`（`_BREAK`/`_BQ`/`_SECOND`/`DG_BREAK_RE` 10 词/`DG_SECOND_SUBJ_RE`/`DG_COORD_RE`/`DG_QUOTE_RE` 4 类）、`:116`（veto 词首负向前瞻）、`:118`（`comp {0,4}?` 排除 `_SECOND`）、`:125`（`govern ≤24`）、`:128-139`（1 pattern + `DG_STATS` 105492/836/2/1）、`:148-158`（`_mask_quotes` 4 类）、`:161-165`（`_scope` 纯函数）、`:167-186`（`dg_double_neg`；第二主语 `:179-181`、并列 `:182-184` 仅查 `hit_text`）、`:189-200`（`dg_scan`）。`lead/gate_fp7_20261108/_g7_predicates.py:76`（R12 十式）、`:92`（`dbl = bool(DOUBLE_NEG_RE.search(pre))`）、`:144`（`r12_scan` 复用 `r10_context`）。`lead/h5_governance_20261109/_h5_pasteable.py:28-40`（H5_R12_TEN 10 + H5_DN_EXTRA 20 支含 1 通配）、`:44-52`（`H5_BRIDGE_RE`）、`:55`（`H5_MICRO_BREAK_RE`）、`:102-151`（`h5_govern` G1–G5）。`lead/dneg_generative_20261109/DNEG_GENERATIVE.md:5`（自标 partial→unconfirmed）、`:163`（6 张表，与实现不符）、`:167`（7 条不变式）、`:173`（co_names 全 False）、`:184`（结构不变式非完备性定理）、`:334`（N20 自记）、`:336`（fp=0 仅 20 条）、`:346`（16/17）、`:347`（0/4）、`:393`（31→31）、`:418`（unconfirmed）、`:428`（控制项）、`:454-470`（判不了什么）。`lead/gate_pipeline_20261109/_gp_regression.py:50`（BAD_BAN）、`:125-130`（GP-A1/A2/A3）、`:133-150`（judge_one）、`:222`（写盘行）。`lead/gate_pipeline_20261109/_gp_pipeline.py:58-70`（`extract_spans` 用 DEFAULT_TOKENS 三词）。

### 6.8 纪律核验

零真机、零采样代码；未改 DG 生成式 / H5 / 任何既有件；唯一写域 `lead/dg_adversarial_20261109/`（本件 + 3 个 `_dgaw_*` 脚本/stdout/out.json，只读引用既有 `_dga_*`/`_dgav_*`）；会话首/末保护件 git status 与 HEAD 一致；`_gp_regression_out.json` 未落盘（38575 字节、mtime 未变）；不 commit、不 push；9 件指纹会话首/末两次 `ALL_MATCH = True`。

**最终 verdict：本件对抗验证结论 = 不误判不成立（severity high）；上游复核 `partial` → 相关一般性断言标 `unconfirmed`；建议不落地为「一行替换」，前置条件 §6.4 未满足前不得上线。**
