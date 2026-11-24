# 双重否定构式生成方案（只出设计，不改任何既有件）

**写域**：`lead/dneg_generative_20261109/`，全部产出前缀 `_dg_`。
**铁律遵守**：零真机、零采样、绝对只读保护件、不 commit / 不 push；`python -I -X utf8` + 绝对路径；指纹 `hashlib`。
**改前改后对照**：本文只给【改前 = 现状实跑】与【改后 = 生成式替身实跑】两张表；**`_g7_predicates.py`（sha256 `02c17e49…`/11743 B）与任何既有件一律未改**。

---

## 0 复核回件绑定行与指纹核对

被核对象 SHA256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120，字节数 = 11743
（对象：`lead/gate_fp7_20261108/_g7_predicates.py`，本任务的核心被核只读件）

被核对象 SHA256 = ffd552207039b220e2a3e649af32aea25bbcd923fe6f9742a8bdb634cb837dc6，字节数 = 5056
（对象：`lead/h5_governance_20261109/_h5_r12_gap_out.json`）

被核对象 SHA256 = b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c，字节数 = 8540
（对象：`lead/h5_governance_20261109/_h5_pasteable.py`）

编排方给的 8 件指纹全部独立重算 **8/8 MATCH**：
`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dg_fingerprint.py`
→ `_dg_fingerprint_out.json`，输出 `ALL_MATCH = True`（含 `_gp_regression_out.json` `d3543657…`/38575、`PENDING_DECISIONS.md` `3765eddb…`/52419、`GOAL_THREE_TARGETS_20261018.md` `2baa0de4…`/759518、H5 两份、台账两件、`lead/gate_n13_20261109/_n13_predicates.py` `e1195b3b…`/16649）。全部任务结束后再次重跑仍 `ALL_MATCH = True`（保护件零漂移）。
`_g7_predicates.py:76` 实读：`DOUBLE_NEG_RE = re.compile(r"(不得不|并非不|并不是不|不是不|无不|没有不|不无|不能不|不可不|未曾不)")`（十式纯枚举、相邻连写）。

---

## 第一步 复核漏判面

### (a) 19 式逐条复核（独立实跑）

命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dg_step1.py`
输出：`_dg_step1_out.json`。做法：不采信 `_h5_r12_gap_out.json` 的结论，从 `_h5_r12_gap.py:27-47` 逐字重列 19 式，直接调只读加载的 `g7.DOUBLE_NEG_RE` / `g7.r10_context` / `g7.r12_scan`。

| # | 构式 | regex_hit | r10_kind | r10_dbl | neg_count | r12_problems | 结论 |
|---|---|---|---|---|---|---|---|
|1|亦非不|false|negation|false|2|0|漏判确认|
|2|未尝不|false|negation|false|2|0|漏判确认|
|3|未始不|false|negation|false|2|0|漏判确认|
|4|未有不|false|negation|false|2|0|漏判确认|
|5|莫不|false|negation|false|1|0|漏判确认|
|6|不敢不|false|negation|false|2|0|漏判确认|
|7|不会不|false|negation|false|2|0|漏判确认|
|8|不可能不|false|negation|false|2|0|漏判确认|
|9|未必不|false|negation|false|2|0|漏判确认|
|10|未免不|false|negation|false|2|0|漏判确认|
|11|岂能不|false|negation|false|1|0|漏判确认|
|12|焉能不|false|negation|false|1|0|漏判确认|
|13|哪能不|false|negation|false|1|0|漏判确认|
|14|不可谓不|false|negation|false|2|0|漏判确认|
|15|不为不|false|negation|false|2|0|漏判确认|
|16|并非没有|false|negation|false|1|0|漏判确认|
|17|并非毫无|false|negation|false|2|0|漏判确认|
|18|不是没有|false|negation|false|1|0|漏判确认|
|19|并不否认|false|negation|false|1|0|漏判确认|

**19/19 全部 `regex_hit=false` 且 `r12_problems=0`** → 编排方与 H5 的漏判面属实。注意 `neg_count` 并不都等于 2（`莫不`/`岂能不`/`焉能不`/`哪能不`/`并非没有`/`不是没有`/`并不否认` 为 1）——这正是「否定词奇偶/计数法不可用」的直接实证：`莫不` 只有 `NEG_RE` 一个否定词命中（`莫` 不在 `NEG_RE` 词表，`_g7_predicates.py:69`），但语义是全称否定 + 谓语否定。

对照（编排方背景 6 条）实跑复现：`亦非不/未尝不/莫不/不敢不` → `r10kind=negation r12=0 PASS(漏)`；`并非不宣告已生效`/`不得不承认本件已生效` → `r10kind=double_neg r12=1 CATCH`。

### (b) 共同结构 / 分类

答案：**不是「否定词 + 情态/程度词 + 否定词」一种，而是同一个骨架的 8 个子类**。统一骨架是
`[加强/反问副词] + 否定算子 N1 + 中缀 M(情态|能愿|时体|程度|系词|述谓桥|ε) + 否定 N2`
其中 N2 既可以是单字「不」，也可以是**否定谓语**（没有/毫无/否认/未/无/非）。`_dg_step1_out.json:categories`：

| 类别 | n | 构式 |
|---|---|---|
|COP_NEG 系词判断否定|2|亦非不 / 不为不|
|ASP_NEG 时体经验否定|2|未尝不 / 未始不|
|EXIST_NEG 存在否定|1|未有不|
|UNIV_NEG 周遍全称否定|1|莫不|
|MOD_NEG 能愿/情态否定|4|不敢不 / 不会不 / 不可能不 / 不可谓不|
|EPIST_NEG 认识/缓和否定|2|未必不 / 未免不|
|RHET_NEG 反问否定|3|岂能不 / 焉能不 / 哪能不|
|NEG_PRED 系否 + 否定谓语|4|并非没有 / 并非毫无 / 不是没有 / 并不否认|

R12 十式只覆盖了这个骨架里 **MID∈{ε,得,能,可,曾}、N1∈{不,并,没有,无}、N2=不/无** 的一小块（十式逐字复核见 `_dg_step1.py` 输出：R12 全 `True`）。

### (c) 十式覆盖了中文双重否定的多少 —— 粗略比例（**明确标为粗略/未直接测**）

先说清「拿得到什么」：
- **项目内语料（可实测）**：`_h5_r12_gap_out.json` + `_h5v_full.py:88-96` 独立枚举的 49 条候选构式 → `H5_GOVERNANCE_FIX.md:314` 记「R12 漏式共 39 条；R12 与 H5 超集都漏 27 条」。按这个**项目内候选集**口径，十式命中 10/49 ≈ **20.4%**；若只数「真双重否定候选」（49 条里扣掉十式对照 10 条 ⇒ 39 条漏式 + 10 = 49），比例同为 10/49。这是本项目自己造的候选集，**不是自然语言语料**，只能当量级感。
- **真实语料（外部文献，WebSearch 实检）**：
  - 王昱《基于规则的双重否定识别——以"不V₁不V₂"为例》（CCL 2020，[ACL Anthology](https://aclanthology.org/2020.ccl-1.1/)）：28,033 句语料，正确率 97.87%、召回率 ≈93.10%；评述王勇(2014) 的双重否定词典仅收 `绝非不/并非不/不是不/不能不/不会不/不可不/不要不/不得不/没有不/无不/不无` 11 式，并**明确指出词典收录不全**，缺 `不应不/不准不/不该不/非…不可/无一不/没有…不…` 等（[CIPS-CL PDF](https://www.cips-cl.org/static/anthology/CCL-2020/CCL-20-001.pdf)）。
  - 《中文信息学报》2024（[澳门大学 PDF](https://linguistics.fah.um.edu.mo/wp-content/uploads/2025/11/unnamed-file-29.pdf)）：以 ¬¬P⇒P 遍历「否定词+否定词」结构，分 **3 大类、25 小类、132 个常用双重否定结构/构式**（[CCL 2020 目录](https://aclanthology.org/volumes/2020.ccl-1/)）。
  - 词频侧：`不能不` 在《现代汉语语料库词频表》列第 2125 位、频次 559（[Scribd 词频表](https://www.scribd.com/document/464717228/)）；`不得不`/`不能不` 多语料库排名见 [Chinese Frequency Dictionary](https://chinesefrequencydictionary.com/index.php?searchTermChi=%E4%B8%8D)（本次 WebFetch 该站超时，**未取到页面原文数字，标未验**）。

**粗估**：以 132 个常用构式为分母，十式 ≈ **10/132 ≈ 7.6%**；以更窄的「11 式词典」为分母，十式 ≈ **10/11 ≈ 91%**，但该词典本身被 CCL 2020 判为不完备。二者差异极大，故**不给单一确定百分比**，只给区间：**量级在 8%–20% 之间（按构式类型数），且高频 token 覆盖率远高于此**（`不得不`/`不能不`/`无不` 属高频，`不能不` 559 次即一例）。**未做的事**：没有在 BCC/CCL/国家语委语料库上跑 token 级加权频次，也没有本项目的真实中文语料库——任务书要的「真实语料出现频次粗略比例」只能给上述**类型数比例的粗估**，token 加权比例标 **未验**，不补造数字。

### (d) 「看起来像双重否定但其实不是」

实跑与分析（`_dg_step34.py` 的 20 条负样本 + 既有件）：
1. **两个独立否定短语**（`_g7_predicates.py:74-75` docstring 点名）：`无越权断言：本件不出现「可应用母本…」` = ¬P ∧ ¬Q，不是 ¬(¬P)。`GATE_FALSE_POSITIVE_5_6_7.md:159` 实跑：奇偶法会把它判成违规（新误报），R10 判违规 0 处。
2. **三否定词**：`复核方并未漏看，本件并非不宣告已生效`（`_g7_tv3_double_negation.md:8` 逐字）——3 个否定词里只有 2 个构成 ¬¬P，奇偶法会误豁免。
3. **词汇化伪构式**：`无非`（= 仅仅）、`莫非`（= 难道）、`不闻不问 / 不卑不亢 / 不打不成交`（并列否定成语）、`不但不 / 非但不`（关联连词「不但/非但」+「不」，只一个有效否定）、`不见得`（认识副词）。这些都是形式上有两个「不」而真值不是 ¬¬P。
4. **「不能不」是否只是强调**：语义上 `不能不 V` = 必须 V，仍是 ¬(¬P) ⇒ 真断言，**应 CATCH**；但语气强弱（委婉/强制）不影响极性。`_g7_tv3_double_negation.md:12` 的 `不得不承认本候选已生效` 与 `H5_GOVERNANCE_FIX.md:65` 的 REGRESS2 都把 `不得不` 当双重否定真违规。真正需要小心的是 **`不无`**：`不无关系` = 「有些关系」，是弱化肯定，**仍属 ¬¬P**（本方案保留 CATCH），但语用上不是强断言；这是「过宽误判」的主要残余，见第五步(b)。
5. **引证跨度里的双重否定**：`「并非不宣告已生效」只是引文，本件不采信该说法` —— 构式在引文里，正文是独立否定；必须屏蔽引文（本方案 N20 实测 `dg=PASS`）。

---

## 第二步 构式生成方案（本任务核心）

实现：`_dg_core.py`（核心 + 形式化注释）、`_dg_pasteable.py`（可粘贴片段，从核心机械抽取，实编译验证通过）。

### (a) 形式化：拆成可生成部件

```
NEG1   ∈ 闭合表（59 项）：前段否定/反问/周遍算子
        单字 不/没/无/非/未/莫/勿/别/甭/岂/焉/安 …
        判断 并非/并不是/不是/亦非/绝不/从不/从未 …
        时体 未尝/未曾/未始/未有/何尝/未免/未必 …
        能愿 不能/不可/不得/没有/不敢/不会/不可能/不该/不应/没法/无法/不由得 …
        反问 岂能/焉能/哪能/安能/岂敢/莫不 …
MID    ∈ 闭合表（23 项，含 ε）：情态/能愿/程度/系词/述谓桥
        ε | 得/能/可/谓/为/是/会/敢/必/免/始/尝/曾/有/可能/一定/见得/由得/住/得不/说不/说
NEG2   ∈ 闭合表（21 项）：否定 / 否定谓语
        不/没/没有/毫无/无/未/非/莫/别/勿/不是/否认/…/不可/不行/不成
GAP    ∈ 闭合表（9 项，含 ε）：把/将/被/让/令/以/按/照
V      ∈ SCOPE_VERB（29 项）：宣告/认定/认为/承认/写/填/登记/… （仅完成/述谓动词）
X      ∈ SPLIT_TAIL（5 项）：不可/不行/不成/不可谓/不罢休
```

**关键设计决定**：`MID` **只收虚词/情态/能愿/系词/述谓桥，一个实词都不收**。这条是后面「不误判两个独立否定」的证明支点。

### (b) 闭合生成规则（有限 **2 条**，不是无限加词）

```
T12（连写式）：  S ::= ¬PSEUDO · NEG1 · MID · NEG2 · GOVERN
T3 （分离式）：  S ::= ¬PSEUDO · NEG1 · GAP · V · COMP · X · GOVERN

COMP     ::= (?:(?!SECOND_SUBJ)[^BQ]){0,4}?     # 唯一通配：≤4 字、排除句界/引号/第二主语
GOVERN   ::= (?=[^BQ]{0,24}$)                   # 同微句、距 token ≤24（沿用 NEG_WINDOW）
BQ       ::= 。！？；;，,、：:\n「」『』“”`      # 句界 + 逗号 + 冒号 + 引号
PSEUDO   ::= 无非|莫非|莫不是|没不|不没|非不|…   # 词汇化伪构式 veto（12 项）
```

- **规则条数恒定 = 2**，词表扩大只改变笛卡尔积规模，不增加规则；这就是「闭合」的严格含义。
- 由部件表编译期生成**一条** `re.Pattern`（`DG_PATTERN`，836 字符）：`cartesian_T12 = 59×23×21 = 28,497`，`cartesian_T3 = 59×9×29×5 = 76,995`，合计 105,492 个可生成串；`wildcards = 1`（只有 T3 的 `COMP`），T12 **零通配**。实跑：`_dg_core.py` → `DG_STATS`。
- 「无限加词」的边界：扩展只能往 6 张闭合表加**词条**，且必须满足 (c) 的约束；不能新增模板、不能放宽 `COMP` 的上限、不能把 `GOVERN` 的 `[^BQ]` 换成 `.*`。词表本身是有限常量，规模上限由门禁所有者裁定（建议 `NEG1≤80 / MID≤40 / NEG2≤30`）。

### (c) ★ 证明：不会把「两个独立否定短语」误判成双重否定

被核对象：`_g7_predicates.py:69-75` docstring 与 `:137-139` 明确警告的两个反例。

**命题**：设 `t = N_a … N_b` 是两个独立否定短语（¬P ∧ ¬Q），中间存在至少一项 `sep ∈ {句界/逗号/冒号/引号/转折连词/第二主语/并列标记/实词谓语}`。则 `DG_DROPIN_RE.search(pre(t))` 不产生跨 `sep` 的匹配。

**证明（结构性，逐条对正则不变式）**：
1. `r10_context`（`:86-91`）把 `pre` 截到 `NEG_WINDOW=24` 且子句边界 `CLAUSE_BREAK` 之后；`dg_double_neg` 再 `_scope()` 按 `DG_BREAK_RE` 取最后一个微句边界之后的片段。所有 `sep` 里的 `。！？；\n，,、：:` 与 `但/然而/不过/却/只是/反之/相反/另外/另` 都会**切断** `scope`，`N_a` 落在切点左边 ⇒ 不参与匹配。（对应 `GATE_POSTMORTEM:100` 的跨句污染、`H5_DESIGN.md §3.4 C 组` 的「，但」污染。）
2. 若 `sep` 是引号：`_mask_quotes()` 把 `「…」/『…』/“…”/反引号` 内部置等长空格；`BQ` 又含所有引号字符 ⇒ 引文里的 `N_a` 既被屏蔽又不可跨越。实测 N20（`「并非不宣告已生效」只是引文…`）`dg=PASS`。
3. 若两个否定之间隔着**实词**（`无越权断言…不出现`、`不闻不问`、`不卑不亢`）：T12 要求 `NEG1·MID·NEG2` 三段**连续、零通配**，`MID` 是闭合虚词表，不含任何实词 ⇒ `无`+`越权断言`+`不` 拼不出合法串；T3 的 `COMP` 只允许 ≤4 个非 BQ 字符且 `V` 必须是闭合的完成动词表 ⇒ 也拼不出。实测 N01/N02/N07/N08/N09/N16/N18 全 `PASS`。
4. 若 `sep` 是第二主语：`DG_SECOND_SUBJ_RE` 在 `COMP` 里做负向前瞻、在 `dg_double_neg` 里对命中链做二次 veto；命中链内出现 `本件/本笔/台账/母本/审阅回件/…` 即作废。
5. 若是并列（`或/、/、以及/同时/一是…二是…/斜杠`）：`DG_COORD_RE` 对命中链否决。实测 N16（`无越权断言 / 不出现…`）`PASS`。
6. 词汇化伪构式（`无非/莫非/不但不/非但不/不见得/没不/不没/非不`）：`PSEUDO_DN` 负向前瞻 + `MID` 不含「但」 ⇒ 实测 N11/N12/N13/N14/N19 全 `PASS`（注意 N14 的 `非但不` 让 **H5 超集字面命中 `h5_regex=True`**，正是 H5 通配 `非[^，,。；;]{0,4}不(?:宣告|…)` 的过宽实例；DG 不命中）。
7. **全程不做否定词奇偶计数**（`_g7_predicates.py:74-75` 的结论原样保留）：`neg_count` 只作信息位。`莫不` 只有 1 个 `NEG_RE` 命中、`三否定词` 有 3 个，两者都由构式链而非计数裁决。

**实跑证据**（`python -I -X utf8 .../_dg_step34.py` → `_dg_step34_out.json`）：20 条负样本中 19 条真负样本 **DG 误判 fp = 0**；第 20 条 N03 是已知真 DN 对照（三否定词），`dg=CATCH` 正确。另：`g7.r10_context` 实跑 `无越权断言：本件不出现「可应用母本…」` 的 `neg_count=2`，而 `复核方并未漏看，本件并非不宣告已生效` 的 `neg_count=3`——奇偶法在这两句上方向相反地错，构式法两句都对。

**证明的边界（如实写）**：这是**在给定闭合部件表与 2 条模板下的结构不变式**，不是自然语言完备性定理。若有人往 `MID` 加实词、放宽 `COMP`、或去掉 `GOVERN`，不变式即失效；若出现表外的「两个独立否定」恰好由合法 `NEG1·MID·NEG2` 连写（例如生造 `没不承认`，已被 `PSEUDO_DN` veto 但同类未穷尽），仍可能 FP。故第五步(b) 给运行时控制措施。

### (d) 可粘贴实现片段

文件：`_dg_pasteable.py`（独立可 `import`、实编译通过，`pattern_chars=836`、`R12_TEN all generated=True`）。
**若将来所有者授权改 `_g7_predicates.py`**，只需两处：
```
① 把 _dg_pasteable.py 的部件表 + dg_build_dropin_regex() 整段插到 :76 之前；
② :76  DOUBLE_NEG_RE = re.compile(r"(不得不|…|未曾不)")
   改为  DOUBLE_NEG_RE, _DG_PATTERN, _DG_STATS = dg_build_dropin_regex()
```
`:69-75` docstring、`:78-111 r10_context` 的 `dbl = bool(DOUBLE_NEG_RE.search(pre))`、`:134-148 r12_scan` 的 `ctx["kind"]=="double_neg"` 分支、`:144` 调用点 **全部零改动**——因为生成结果就是一个 `re.Pattern`，`.search()` 语义完全兼容。**本任务未实施这两处替换**（铁律：绝对只读）。

### (e) 与 R12 既有十式的关系：**真超集 + 兼容**

- 十式逐字复核：`_dg_step1.py` → `R12 全 True / DG 全 True`；`_dg_step34.py (3b)` 十式成句 `r12=1 / dg=1` 全 10/10。`_dg_core.py:R12_TEN` 保留原十式字面表作**对账锚**（可选，不参与生成）。
- 关系：`L(R12十式) ⊊ L(DG)`；DG 另含 19 式、17 条复核员「都漏」中的 16 条（`_dg_step34.py (3d)`）、分离型构式串（字面级）。
- 兼容方式：**替代而非并存**（一行替换）；若并存（把十式当快速通道 OR 上），语义相同但失去对账价值，无必要。

---

## 第三步 量化覆盖率提升

命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dg_step34.py` → `_dg_step34_out.json`。

### (a) 19 式漏判逐条（**19/19 全覆盖**）

| 构式 | R12 | H5 | DG | DG 命中串 |
|---|---|---|---|---|
|亦非不|False|True|**CATCH**|亦非不宣告|
|未尝不|False|True|**CATCH**|未尝不认为|
|未始不|False|True|**CATCH**|未始不认为|
|未有不|False|True|**CATCH**|未有不认为|
|莫不|False|True|**CATCH**|莫不认为|
|不敢不|False|True|**CATCH**|不敢不承认|
|不会不|False|True|**CATCH**|不会不承认|
|不可能不|False|True|**CATCH**|不可能不宣告|
|未必不|False|True|**CATCH**|未必不认为|
|未免不|False|True|**CATCH**|未免不认为|
|岂能不|False|True|**CATCH**|岂能不|
|焉能不|False|True|**CATCH**|焉能不|
|哪能不|False|True|**CATCH**|哪能不|
|不可谓不|False|True|**CATCH**|不可谓不宣告|
|不为不|False|True|**CATCH**|不为不认为|
|并非没有|False|True|**CATCH**|并非没有|
|并非毫无|False|True|**CATCH**|并非毫无|
|不是没有|False|True|**CATCH**|不是没有|
|并不否认|False|True|**CATCH**|并不否认|

`R12 0/19 → DG 19/19`（+19 式，+19/29 的类型覆盖：若把十式+19 式合成 29 式已知集，R12 10/29→DG 29/29）。H5 超集字面也 19/19，见 (d) 的取舍。

### (b) 十式不退化

十式成句 `r12=1 / dg=1` **10/10**（`_dg_step34.py (3b)`）；十式裸串 `DG_DROPIN_RE.search` 全 `True`（`_dg_core.py` 自检）。全量 74 条回归里 `chain FP` 改前 2 → 改后 2（**未新增误报**），见第四步(c)。

### (c) ★ 20 条「形式相近但非双重否定」负样本：**fp = 0**

`_dg_step34.py` 的 `NEG20`：N01/N02 两个独立否定（含 `CANDIDATE:155` 逐字形态）、N04 单重否定、N05 禁止+引证、N06 跨句、N07/N08/N09 并列成语、N10 独立叹词「不，」、N11 无非、N12 莫非、N13 不但不、N14 非但不、N15 转折、N16 并列斜杠、N17 未核 grep、N18 两项并列否定、N19 不见得、N20 引证内双重否定；**N03 为已知真 DN 对照**（三否定词，期望 CATCH）。
结果：`真负样本 n=19 ; DG 误判(fp) = 0 : []`；N03 `dg=CATCH`（正确）。
对照：R12 字面在 N03/N20 上 `True`（N20 是把引文里的双重否定误当命中，属于 R12 既有形态）；**H5 超集在 N14「非但不宣告」上 `h5_regex=True`**（误命中伪构式）——这是 H5 那条 `非[^，,。；;]{0,4}不(?:宣告|…)` 通配的过宽实证。
**残余风险（如实）**：负样本是本项目自造的 20 条，不是全域中文；`不无关系` / `无不称快` 这类弱化肯定仍被 DG 判 CATCH（`DG_DROPIN_RE` 会命中），在「完成断言」语境下是否算误报需所有者定夺，标**未验**。

### (d) 与 H5 补丁（H5_DN_EXTRA 19 式 + 分离型通配）对比

`_h5_pasteable.py:28-40` 实读：`H5_R12_TEN`（十式）+ `H5_DN_EXTRA`（28 个选择支 = 19 式 + 分离型通配 `非[^，,。；;]{0,4}不(?:宣告|认定|认为|承认|说|写|登|记|填)`）→ `H5_DOUBLE_NEG_RE`，pattern 仅 162 字符；作用域由 `h5_govern()` 的 G2 `_h5_last_micro` 提供。

| 维度 | H5 补丁 | 本方案（DG） | 实跑依据 |
|---|---|---|---|
|19 式|19/19 字面|19/19 生成|`(3a)`|
|十式|保留字面|生成+对账锚|`(3b)`|
|复核员 27 条「都漏」中的 17 条|**0/17**|**16/17**|`(3d)`：何尝不/安能不/岂敢不/没法不/并非未/并非无/不由得不/忍不住不/不见得不/不一定不/不是没/非写成已入账不可/非登记不可/非说不/没说不/没法不说 全由部件表生成；唯一漏 `非但不`（**刻意不收**，它是伪构式）|
|分离型整句（第二否定在 post）|**0/4**|**0/4**|`(3d-2)`：`非写成已入账不可` 等四条全 `dg=False`；`H5_GOVERNANCE_FIX.md:314` 亦记 H5 `NEW=PASS`。原因：T3 的 `X` 必须在 `pre` 内闭合，而 token 在 `X` 之前 ⇒ 本方案【同样漏】，不掩盖|
|伪构式误命中|N14 `h5_regex=True`（过宽）|N14 `dg=PASS`|`(3c)`|
|规则形态|字面枚举 28 支 + 1 通配|2 条模板 + 6 张闭合表 + 1 个受控通配|`DG_STATS`|
|作用域|依赖 `h5_govern()` 的 G1/G2/G3/G4（另有 `H5_GOVERNANCE_FIX.md:298` 自陈的 filler≤4、形状 a 用整段 p、形状 c 误当谓语否定等缺陷）|自带 `_scope`/`_mask_quotes`/第二主语/并列 veto；`r10_context` 的 24 字窗与 `CLAUSE_BREAK` 原样复用|`_dg_core.py`|

**哪个更彻底**：按「构式覆盖面」**DG 更彻底**（16/17 vs 0/17，且泛化到 105,492 个生成串）；按「分离型整句」**两者都不彻底**（0/4），这是共同缺口，需要把第二个否定词的查找扩到 `post`（会引入跨 token 管辖的新 FP 风险，本任务只登记不实施）。**取舍**：H5 是「窄、可核对、162 字符、与 V12 单文件同域」的最小补丁，代价是枚举不穷尽 + 通配过宽；DG 是「生成、可泛化、836 字符」的结构补丁，代价是部件表本身要维护、闭合性靠约束不变式而非人工逐条核对、且同样漏 post 分离型。两者都不改 `_g7_predicates.py`。

---

## 第四步 对三层判断的影响

### (a) ★ GP-A1 能否被兜住 —— **能，实跑确认**

命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dg_step34.py`（`(4)/(4a)`）与 `_dg_step4c.py`。
做法：不改任何既有件，在**内存**里造 `_Shim`，把 `g7.r12_scan` 指向 `DG.dg_scan`、`DOUBLE_NEG_RE` 指向 `DG_DROPIN_RE`、`r10_context.dbl` 用生成式重算，再调 `_gp_pipeline.gate_check`（`:223`）。这模拟「只改 :76 一行」的传播。

```
改前：GP-A1 expect=CATCH base_chain=PASS (r10=0 r12=0 n13=0 conflicts=0)
改后：GP-A1 expect=CATCH DG_chain=CATCH
      layers={'R9':3,'R10':0,'R12':1,'N13':1,'R11':1}
      span tok=已生效 pos=14 r10=PASS r12=CATCH n13=CATCH => CATCH rules=K1
```
`亦非不宣告` 命中 T12 → R12 报 1 → N13 的 `:130` `(tok,pos) in r12` 分支把它判 D → 合成链按 **K1**（`_gp_pipeline.py:98`「R12 判 double_neg → CATCH」）兜住。与编排方给的 `GATE_PIPELINE_COMPOSE.md:266`「三层全放过」对照一致。

### (b) GP-A2 / GP-A3 受影响吗 —— **不受影响，仍漏**

```
GP-A2  本件登记闭合，母本即日起适用      DG_chain=PASS (R12=0, N13=0)
GP-A3  三值填毕，见证已由编排方签字      DG_chain=PASS (R12=0, N13=0)
```
两条不含任何否定词，`BAD_BAN` 五词与 N13 三词（`_gp_regression.py:50`、`:48-50`）都无字面命中 ⇒ 提取器 `spans=0`，三层无输入。依据 `GATE_PIPELINE_COMPOSE.md:267-268`、`:487`「词表外同义改写 `登记闭合/填毕/已由…签字`，`finditer` 全量也扫不到」。**结论：双重否定只是三条共同盲区中的一条**；另两条是「同义完成词族未登记」，属词表/语义问题，本方案不解决、也不声称解决。`_gpv_lazy_out.txt:4-5` 记两条需 P1 同义完成词族规则（`would_catch=True`）才兜得住。

### (c) ★ 三层里哪几层改善 —— 给数字（74 条全量实跑）

命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dg_step4c.py` → `_dg_step4c_out.json`。
做法：只读导入 `_gp_regression.py` 的 74 条 CORPUS（`Path.write_text` 被拦截，**未写任何既有输出文件**），改前用原 `g7`，改后用内存 Shim，逐条跑 naive / R10 / R12 / N13 / chain。

| 层 | 改前 ok/FP/FN | 改后 ok/FP/FN | Δ |
|---|---|---|---|
|naive|34/33/7|34/33/7|0（未动）|
|R10 单层|35/20/19|35/20/19|**0**|
|R12 单层|39/0/35|**40/0/34**|**+1 ok，FN −1**|
|N13 单层|71/0/3|**72/0/2**|**+1 ok，FN −1**|
|合成链 chain|69/2/3|**70/2/2**|**+1 ok，FN −1，FP 不变**|

- 改善的层：**R12（+1）、N13（+1）、合成链（+1）**；R10 单层数字不变（它仍把 `亦非不` 归 `negation`，但注意 Shim 的 `r10_context.dbl` 已变，`r10_scan` 的 problems 口径不变故数字不动）。
- 唯一变更条目：**GP-A1 一条**（`PASS → CATCH`），其余 73 条结论全不变；`chain 层间冲突 31 → 32`（+1，为 GP-A1 新增的 R12/N13 vs R10 分歧，按 K1 已裁决）。
- 按族：`GP_ALLPASS_TRUE_ASSERTION` 族 `old_ok=0 → new_ok=1`，`old_FN=3 → new_FN=2`；其余 7 族全不变。
- 编排方基线数字复核：`_gp_regression_out.json:single_layer_vs_chain` = `r12 39/0/35、n13 71/0/3、chain 69/2/3`，与本脚本改前实跑**逐项一致**（`_gp_regression_out.txt:12-16`），说明复现可信。

### (d) 能解决「证据不独立」吗 —— **不能**

`GATE_PIPELINE_COMPOSE.md:499` 实读：三层共用同一套字面词表与否定/标记词表（`NEG_RE`/`DOUBLE_NEG_RE`、N13 `_DIRECT_NEG`/`_A_AFTER`），是**相关失效而非独立表决**；N13 C 类直接转发 R10 kind，R12 复用 `r10_context`（`_g7_predicates.py:144`）。本方案**只把其中一张词表换成生成式**，三层仍：
- 共用 `extract_spans` 的同一 token 集合（`_gp_pipeline.py:58-70`）；
- N13 仍通过 `r12_scan` 参数消费 R12 结论（`_n13_pasteable.py:109-111`、`:130`）；
- R12 仍通过 `r10_context` 复用同一 24 字窗与 `CLAUSE_BREAK`（`:144`）。

GP-A1 改后仍是 `conflicts=0 → 1` 的相关一致（R12/N13 同向 CATCH），**不是独立第三方证据**；GP-A2/A3 继续证明共同盲区仍在（三层一致放过、冲突数 0）。判断：本方案**改善召回，不改变证据独立性**；要独立需另立不同输入契约的层（例如语义/句法解析、人工复核项），超出本任务范围。

---

## 第五步 结论与建议

### (a) 枚举还是生成 —— **结论：生成（但为「闭合表 + 2 条模板」的生成，不是自由语法）**

理由（全部有实测）：
1. 枚举 10 式 → 19 式实测全漏（`_dg_step1_out.json`），复核员另举 49 条候选中 R12 漏 39、R12 与 H5 超集都漏 27（`H5_GOVERNANCE_FIX.md:314`）；文献侧 132 个常用构式 / 25 小类（[2024 论文](https://linguistics.fah.um.edu.mo/wp-content/uploads/2025/11/unnamed-file-29.pdf)）。枚举必然要持续「无限加词」。
2. 生成式 2 条模板 + 6 张闭合表 → 19/19、16/17、十式不退化、20 条负样本 fp=0、74 条回归 +1 ok 零新 FP（`_dg_step34_out.json` / `_dg_step4c_out.json`）。
3. 与既有门禁**一行替换兼容**（`_dg_pasteable.py`），不改 `r10_context`/`r12_scan` 任何调用点。

### (b) 风险（过宽误判）与控制

| 风险 | 实证 | 控制 |
|---|---|---|
|部件表笛卡尔积生成非词串（`没不`/`不没`/`非不`）|adversarial probe 命中 `没不`/`不没`（首次），加 `PSEUDO_DN` 后全 veto|`PSEUDO_DN` 12 项负向前瞻；建议把生成串过一遍词表白名单或人工抽检|
|弱化肯定 `不无关系`/`无不称快` 被当强断言|`DG_DROPIN_RE.search('不无关系') → '不无'`|拿不准时降为 `NEEDS_HUMAN`（沿用 `_gp_pipeline.py:240-243`），不要直接 CATCH；语用强弱需所有者裁定，**未验**|
|分离型整句 0/4|`_dg_step34_out.json:step3d_split4`|本方案【未解决】；扩到 `post` 必须同时加「同微句 + 辖域动词」双约束，否则新 FP|
|部件表被后人加实词|破坏 (c) 的证明|把「MID 不得含实词」「COMP ≤4 且排除 BQ/第二主语」「GOVERN ≤24 且非通配」写成单元断言，随表一起验|
|跨语体/繁体/英文/被动|未测|标**未验**；本方案只覆盖任务书的简体书面断言语料|
|词表维护成本|59 项 NEG1 等|表是有限常量且可哈希核对（`hashlib`），比散落的枚举支更易审计|

**总体控制原则**：`fp` 优先于 `fn` —— 生成式只负责「把已知构式家族补全」，凡不在闭合表内、或落在引文/跨句/并列/第二主语、或属 `PSEUDO_DN` 的，一律**不判 CATCH**，交 `NEEDS_HUMAN`。`_dg_step34.py (3c)` 的 fp=0 是这一原则的结果。

### (c) ★ 其它「语言构式被枚举化」的清单

命令：`python -I -X utf8 …/_dg_step5c.py` → `_dg_step5c_out.json`（只读扫 `lead/**/*.py`，判据：单行正则字面串含 ≥4 个中文选择支；**共 68 处**，跨行/拼接式正则未纳入，标为扫描口径限制）。与否定/完成断言直接相关者（人工核对行号）：

| 文件:行 | 枚举内容 | 同类不完备风险 |
|---|---|---|
|`gate_fp7_20261108/_g7_predicates.py:69`|`NEG_RE` 9 支否定词|`莫/岂/焉/别/甭/毫无/否认` 不在表内（`_dg_step1.py` 实跑 `莫不` neg_count=1 即证）|
|`gate_fp7_20261108/_g7_predicates.py:76`|本任务对象，十式|已证 19/39 漏|
|`gate_n13_20261109/_n13_pasteable.py:23`|`_NEG` 含 `不得不/并非不/并不是不/不是不/…/亦非/未见/无越权/没有不`|与 R12 十式同源，19 式同样漏；且 `亦非` 单列但 `亦非不` 未成链|
|`gate_n13_20261109/_n13_pasteable.py:14,26-29`|`_AFTER` 检索动作、`_BAN` 禁止词、`_POSTAIL`、`_CONTRAST`|同义改写/新标记词必然漏|
|`gate_v1v2_20261109/_v12_rule.py:38,43,54,62`|`V2_OVERRIDE_RE` / `ADJ_NEG_RE` / `H4_NOUN_RE` / `W1_RE`|`H5_GOVERNANCE_FIX.md:65` 实跑 `不得不` 被 `ADJ_NEG_RE` 当普通禁止词 → 漏|
|`h5_governance_20261109/_h5_pasteable.py:40,44-65`|`H5_DN_EXTRA` 28 支 + 桥接动词表 + `SELF_SUBJ`/`FRAME_POST`|`H5_GOVERNANCE_FIX.md:298,475` 自陈 filler≤4、形状 a/c 缺陷、分离型未覆盖|
|`gate_r9sem_20261109/_r9s_predicates.py:105-108,182,297,334,339`|`_NEG_MODAL_ANY`/`S1_WHO_APPROVER`/`S2_EXEC_OUTPUT`/`_NO_OUTPUT_RE`/`_DETERM_RE`/`_MODAL_RE`|「可重建/不可重建」等构式全靠枚举，同义改写漏|
|`re_line_20261105/W7_W4_REVIEW/_w7_c.py:236-238`|`MARK` 36 支「未验」族 / `STRONG` 19 支「确证」族 / `LEDGER`|最大规模枚举，最典型「无限加词」候选|
|`refsync_scope_20261109/_rs_markers.py:30`|10 支转录边界标记|新标记词必漏|
|`gate_validate_20261108/_gv_fixed_rules.py:35,78,80`|就地覆盖/去聚合/实算来源三族|同上|

### (d) 这条工作判不了什么（如实列）

1. **判不了中文双重否定的全域真值**：无 BCC/CCL 语料库 token 级频次（(c) 只给类型数粗估 8%–20%，token 加权比例**未验**）；语用强弱（`不无` 弱化肯定）需语言学裁定。
2. **判不了分离型「非…不可」整句**：`_dg_step34_out.json:step3d_split4` 实跑 0/4，H5 也 0/4；这是共同缺口。
3. **判不了 GP-A2/A3**（同义完成词族 `登记闭合`/`填毕`/`已由…签字`），它们不是双重否定；`_dg_step34.py (4a)` 实跑仍 `PASS`。
4. **判不了「证据不独立」**：三层相关性由架构决定（`GATE_PIPELINE_COMPOSE.md:499`），换词表不改变。
5. **判不了未列举的伪构式**：20 条负样本是本项目自造，fp=0 只在这 20 条上成立；`PSEUDO_DN` 12 项未穷尽。
6. **判不了 74 条以外语料的 FP**：74 条全量回归只证明「零新增 FP」在该语料上成立；繁体/英文/被动/跨行/超 24 字距全部**未验**。
7. **判不了落地效果**：`_g7_predicates.py` 与所有既有件**绝对只读、未改**；`_dg_step34.py`/`_dg_step4c.py` 的结果全部来自内存 Shim 模拟「只改 :76 一行」，不是真实门禁运行。真实落地需所有者另行授权并跑完整门禁回归。
8. **判不了 H5 补丁其它缺陷**：`H5_GOVERNANCE_FIX.md:298,456` 自陈 `partial / unconfirmed`（V02/V03 误拦、V08/V09/V10/B5 放过），本方案只比「双重否定覆盖」一维，不代替 H5 的整体验收。
9. **本任务未跑**：任何真机/采样/hook、`git commit` / `push`、对保护件的写操作；`_dg_step5c.py` 的正则扫描是单行字面串口径，跨行 `re.compile("…" "…")` 未统计。

---

## 附：改前 / 改后对照总表

| 项 | 改前（`_g7_predicates.py:76` 十式枚举） | 改后（生成式替身，内存 Shim） |
|---|---|---|
|规则形态|10 条字面交替支|2 条模板 + 6 张闭合表（59/23/21/9/29/5 项）+ 12 项 veto|
|正则长度|`len(pattern)=40` 字符（`:76` 实读：`_dg_step1.py` 打印 `(不得不|并非不|并不是不|不是不|无不|没有不|不无|不能不|不可不|未曾不)`，实算 40）|836 字符（编译期生成，`DG_STATS.pattern_chars=836`）|
|19 式|0/19 CATCH|19/19 CATCH|
|既有十式|10/10|10/10|
|复核员 17 条|0/17（H5 亦 0/17）|16/17|
|分离型整句|0/4|0/4（未改善）|
|20 条负样本 fp|R12 在 N20 引文上字面误命中|0（真负样本 19 条）|
|GP-A1|`chain=PASS`（三层全漏）|`chain=CATCH`（K1）|
|GP-A2/A3|`PASS`/`PASS`|`PASS`/`PASS`（不变）|
|74 条 R12/N13/chain|39/71/69 ok|40/72/70 ok（FP 2→2）|
|层间冲突|31|32（+1，已裁决）|
|保护件字节|8/8 指纹 MATCH、零改动|8/8 指纹 MATCH、零改动（任务结束后复验）|

## 附：本写域产出清单（全部前缀 `_dg_`，均在 `lead/dneg_generative_20261109/`）

`_dg_fingerprint.py` / `_dg_fingerprint_out.json`（8 件指纹）
`_dg_step1.py` / `_dg_step1_out.json`（19 式逐条 + 分类 + 十式）
`_dg_core.py`（生成式核心 + 形式化注释）
`_dg_pasteable.py`（可粘贴片段，独立编译验过）
`_dg_step34.py` / `_dg_step34_out.json`（第三、四步量化 + 20 负样本 + GP-A1；Step4 段落已合并进主脚本，中间拼接文件已清理）
`_dg_step4c.py` / `_dg_step4c_out.json`（74 条全量改前改后）
`_dg_step5c.py` / `_dg_step5c_out.json`（68 处枚举化清单）
`_dg_DESIGN.md`（本文件）
