# DNEG_GENERATIVE.md — 双重否定「构式生成」方案（只出设计，不改任何既有件）

**写域**：`lead/dneg_generative_20261109/DNEG_GENERATIVE.md`（本件）；同目录既有 `_dg_*` / `_dgv_*` 件为上游设计与复核产出。
**铁律**：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；绝对只读保护件；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。
**复核判语**：上游【复核】verdict = **partial**；按交付规则 partial 一律标 **unconfirmed**，见 §6。本件如实记录复核结论，不把 partial 写成通过。

---

## 1 目的与边界

**目的**：把 R12 在 `lead/gate_fp7_20261108/_g7_predicates.py:76` 的 **十式纯枚举** 双重否定正则，改成 **「闭合部件表 + 2 条生成模板」的构式生成** 方案；给出不把「两个**独立否定**短语」**误判**成双重否定的机制与实测；给出**覆盖率**提升、**fp**、对三层门禁的影响、以及**枚举式正则**清单。

**边界（全部实读 / 实跑）**：

| 项 | 状态 | 依据 |
|---|---|---|
| `_g7_predicates.py` 是否改动 | **未改**，8/8 指纹 MATCH | 本会话 `python -I -X utf8 -c "<hashlib 8 件>"` → `ALL_MATCH = True`；`git log --oneline -3` → HEAD 仍 `2657458` |
| 任何既有件是否改动 | **未改** | `_dg_step4c.py:25-34` 拦截 `Path.write_text`；本会话 `git status --porcelain -- lead/gate_fp7_20261108 ...` 仅显示会话开始前既有的 `MM`/`??` |
| `_g7_predicates.py:76` 一行替换 | **只给方案，未实施** | `_dg_pasteable.py:7-11`（实读）明写「本任务铁律：以上替换【未实施】，只给方案」 |
| 所有「改后」数字 | **内存 Shim / 第二模块实例模拟**，非真实门禁落地 | `_dg_step4c.py:44-67`、`_dgv_chain.py:32-42`；真实落地标 **未验** |
| 写盘范围 | 仅本写域 | `grep -nE "write_text|open\([^)]*['\"][wa]" lead/dneg_generative_20261109/_dg_*.py .../_dgv_*.py` → 唯一写盘目标均为写域内 `_dg*_out.json` |

**改前 / 改后总对照**（改后 = 生成式替身实跑，非落盘改动）：

| 项 | 改前（`:76` 十式枚举） | 改后（DG 替身） | 实跑 |
|---|---|---|---|
| 规则形态 | 1 条 `re.compile`，10 个字面选择支，pattern 40 字符 | **2 条**模板 + 6 张闭合表 + 12 项 veto，pattern 836 字符 | `_dg_step1_out.json:re_pattern`；`_dgv_probe_out.json:pasteable_stats` |
| 19 式 | 0/19 | 19/19 | `_dg_step34.py (3a)` |
| 既有十式 | 10/10 | 10/10（不退化） | `_dg_step34.py (3b)` |
| 20 条负样本 | R12 在 N20 引文字面误命中；H5 在 N14 `非但不` 误命中 | 作者自造 19 条真负样本 `fp = 0` | `_dg_step34_out.json:dg_fp` |
| 刁钻负样本（复核员） | base 8/30 CATCH | 纯函数 8/30、一行替换 25/30，**误判**新增 7 / 17 条 | `_dgv_neg2.py`（本会话重跑） |
| 74 条 chain ok | 69 | 70（Shim 与真实一行替换一致） | `_dg_step4c.py`、`_dgv_chain.py` |
| 保护件字节 | 8/8 MATCH | 8/8 MATCH | 本会话 hashlib 重算 |

---

## 2 上游指纹（八件）+ 漏判面复核

### 2.1 八件指纹（本会话独立重算）

命令（本会话实跑）：
`python -I -X utf8 -c "<ROOT=Path('D:/Project/ra2-campaign-forge'); 对 8 件逐件 read_bytes → hashlib.sha256 → 与编排方声明比对>"`
输出：
```
_g7_predicates.py                                          MATCH=True 11743
_h5_r12_gap_out.json                                       MATCH=True 5056
_h5_pasteable.py                                           MATCH=True 8540
_h5_regress_out.json                                       MATCH=True 36167
lead/gate_n13_20261109/_n13_predicates.py                                         MATCH=True 16649
_gp_regression_out.json                                    MATCH=True 38575
PENDING_DECISIONS.md                                       MATCH=True 52419
GOAL_THREE_TARGETS_20261018.md                             MATCH=True 759518
ALL_MATCH = True
```
（第八件在终端回显中被脱敏为 `_n13_predicates.py`，路径按任务书原样写 `lead/gate_n13_20261109/_n13_predicates.py`；声明值出自任务书【编排方指纹】，逐件 sha/bytes 与 `_dg_fingerprint_out.json:2-65`、`_dgv_fp_out.json:2-66` 一致。另 `python -I -X utf8 .../_dgv_probe.py` 的 `pattern_chars = 836` 与 `_dgv_fp.py:37-48` 的 8/8 复算同会话可复现。）

| # | 对象 | SHA256 | 字节数 |
|---|---|---|---|
|1|`lead/gate_fp7_20261108/_g7_predicates.py`|`02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120`|11743|
|2|`lead/h5_governance_20261109/_h5_r12_gap_out.json`|`ffd552207039b220e2a3e649af32aea25bbcd923fe6f9742a8bdb634cb837dc6`|5056|
|3|`lead/h5_governance_20261109/_h5_pasteable.py`|`b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c`|8540|
|4|`lead/h5_governance_20261109/_h5_regress_out.json`|`9986ed2d83df56bfb8e6d231f1fb85bf037e04961ebff79723c32d4e3e0a834b`|36167|
|5|`lead/gate_n13_20261109/_n13_predicates.py`|`e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079`|16649|
|6|`lead/gate_pipeline_20261109/_gp_regression_out.json`|`d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe`|38575|
|7|`lead/PENDING_DECISIONS.md`|`3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7`|52419|
|8|`lead/GOAL_THREE_TARGETS_20261018.md`|`2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede`|759518|

被核对象实读：`_g7_predicates.py:69` `NEG_RE = re.compile(r"(不|无|未|非|禁|勿|否决|排除|不宣告|不得)")`；`:70` `NEG_WINDOW = 24`；`:71` `CLAUSE_BREAK = "。！？；\n"`；`:76` `DOUBLE_NEG_RE = re.compile(r"(不得不|并非不|并不是不|不是不|无不|没有不|不无|不能不|不可不|未曾不)")`；`:92` `dbl = bool(DOUBLE_NEG_RE.search(pre))`；`:144` `r12_scan` 复用 `r10_context`。

### 2.2 19 式逐条复核（改前 = 现状）

命令（本会话实跑）：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dg_step1.py`
输出（节选，19 行逐条同格式）：`亦非不 regex_hit=false r10_kind=negation r10_dbl=false neg_count=2 r12_problems=0 => 漏判确认 | DG=1 hit=亦非不宣告` … `岂能不 regex_hit=false ... neg_count=1 ... => 漏判确认 | DG=1 hit=岂能不`；全表见 `_dg_step1_out.json:gap_rows`（`:369` `gap_confirmed: 19`）。

| # | 构式 | 例句（`_dg_step1_out.json:gap_rows`） | regex_hit | r10_kind | r10_dbl | neg_count | r12_problems | 类别 | 结论 |
|---|---|---|---|---|---|---|---|---|---|
|1|亦非不|亦非不宣告 N-4 正式绑定已生效|false|negation|false|2|0|COP_NEG|漏判确认|
|2|未尝不|未尝不认为本件已生效|false|negation|false|2|0|ASP_NEG|漏判确认|
|3|未始不|未始不认为本件已生效|false|negation|false|2|0|ASP_NEG|漏判确认|
|4|未有不|未有不认为本件已生效|false|negation|false|2|0|EXIST_NEG|漏判确认|
|5|莫不|莫不认为本件已生效|false|negation|false|1|0|UNIV_NEG|漏判确认|
|6|不敢不|不敢不承认本件已生效|false|negation|false|2|0|MOD_NEG|漏判确认|
|7|不会不|不会不承认本件已生效|false|negation|false|2|0|MOD_NEG|漏判确认|
|8|不可能不|不可能不宣告本件已生效|false|negation|false|2|0|MOD_NEG|漏判确认|
|9|未必不|未必不认为本件已生效|false|negation|false|2|0|EPIST_NEG|漏判确认|
|10|未免不|未免不认为本件已生效|false|negation|false|2|0|EPIST_NEG|漏判确认|
|11|岂能不|岂能不说本件已生效|false|negation|false|1|0|RHET_NEG|漏判确认|
|12|焉能不|焉能不说本件已生效|false|negation|false|1|0|RHET_NEG|漏判确认|
|13|哪能不|哪能不说本件已生效|false|negation|false|1|0|RHET_NEG|漏判确认|
|14|不可谓不|不可谓不宣告本件已生效|false|negation|false|2|0|MOD_NEG|漏判确认|
|15|不为不|不为不认为本件已生效|false|negation|false|2|0|COP_NEG|漏判确认|
|16|并非没有|并非没有宣告本件已生效|false|negation|false|1|0|NEG_PRED|漏判确认|
|17|并非毫无|并非毫无宣告本件已生效|false|negation|false|2|0|NEG_PRED|漏判确认|
|18|不是没有|不是没有宣告本件已生效|false|negation|false|1|0|NEG_PRED|漏判确认|
|19|并不否认|并不否认本件已生效|false|negation|false|1|0|NEG_PRED|漏判确认|

**19/19 全 `regex_hit=false` 且 `r12_problems=0`**。`neg_count` 有 7 条为 1（#5/#11/#12/#13/#16/#18/#19）——这是 `_g7_predicates.py:74-75`「不用否定词奇偶计数」结论的直接实证：`莫` / `岂` / `焉` / `哪` / `否认` / `没有` 不在 `:69` 的 `NEG_RE` 词表里，计数法必然错。复核员独立复跑 `python -I -X utf8 .../_dgv_probe.py` → `→ 确认漏判 10/10`（`_dgv_probe_out.json:2-103`），与 19 式子集一致。

### 2.3 共同结构分类（8 类，不是「加 19 个词」）

统一骨架（实读 `_dg_DESIGN.md:62-77`、`_dg_step1_out.json:categories`）：
`[加强/反问副词] + N1(否定算子) + MID(情态|能愿|时体|程度|系词|述谓桥|ε) + N2(否定 / 否定谓语)`。

| 类别 | n | 构式（逐条） |
|---|---|---|
|COP_NEG 系词判断否定|2|亦非不 / 不为不|
|ASP_NEG 时体经验否定|2|未尝不 / 未始不|
|EXIST_NEG 存在否定|1|未有不|
|UNIV_NEG 周遍全称否定|1|莫不|
|MOD_NEG 能愿/情态否定|4|不敢不 / 不会不 / 不可能不 / 不可谓不|
|EPIST_NEG 认识/缓和否定|2|未必不 / 未免不|
|RHET_NEG 反问否定|3|岂能不 / 焉能不 / 哪能不|
|NEG_PRED 系否 + 否定谓语|4|并非没有 / 并非毫无 / 不是没有 / 并不否认|

R12 十式只覆盖 `MID∈{ε,得,能,可,曾}`、`N1∈{不,并,没有,无}`、`N2=不/无` 的一小块（`_dg_step1_out.json:r12_ten` 十式全 `r12_regex=true`）。

### 2.4 枚举覆盖率估计（明确为类型数粗估，token 级标未验）

- **项目内可实测口径**：`H5_GOVERNANCE_FIX.md:314`（本会话 `sed -n '312,316p'` 实读）记「R12 漏式共 **39** 条；R12 与 H5 超集【都】漏 = **27** 条」，候选集 49 条 → 十式命中 **10/49 ≈ 20.4%**。这是本项目自造候选集，**不是自然语言语料**。
- **外部文献口径（来自任务书【设计】回件，本会话未重跑 WebSearch，标未验）**：王勇(2014) 11 式词典 → 十式 ≈ 10/11 ≈ 91%，但 CCL 2020 王昱论文评述其「收录不全」；《中文信息学报》2024 分 3 大类 / 25 小类 / **132 个常用构式** → 十式 ≈ 10/132 ≈ **7.6%**。
- **结论**：只给**按构式类型数 8%–20%** 的区间；`不能不` 频次 559 等数字说明高频 token 覆盖率远高于类型数比例，但 **BCC/CCL token 级加权频次比例 = 未验**，不补造数字。

### 2.5 「看起来像双重否定但其实不是」的写法（逐条）

实读 `_g7_predicates.py:74-75`、`:137-139`、`_dg_step34_out.json:step3c_negatives`、`_dg_core.py:79-82`：

1. **两个独立否定短语**（¬P∧¬Q，非 ¬¬P）：`无越权断言：本件不出现「可应用母本…」`（N01，docstring 点名原句）、`CANDIDATE:155` 形态 `并无越权断言：审阅回件不出现「可应用母本 / 放行 N-5」类断言；`（N02）。`_g7_predicates.py:74-75` 明确弃用奇偶计数，正因为奇偶法会在此**误判**。
2. **三否定词**：N03 `复核方并未漏看，本件并非不宣告已生效` 是**真 DN 对照**（期望 CATCH，`dg=CATCH`）；奇偶法会误豁免。
3. **词汇化伪构式**：N11 `无非`（=仅仅）、N12 `莫非`（=难道）、N13 `不但不`、N14 `非但不`、N19 `不见得`；`_dg_core.py:81-82` `PSEUDO_DN` 12 项负向前瞻 veto 之。N14 上 H5 超集 `h5_regex=true` 是通配过宽的实证。
4. **并列 / 成语式两项否定**：N07 `不闻不问`、N08 `不卑不亢`、N09 `不打不成交`、N16 斜杠并列、N18 双引文并列（`_dg_core.py:91` `DG_COORD_RE` 之）。
5. **引证跨度内的 DN**：N20 `「并非不宣告已生效」只是引文，本件不采信该说法` —— 构式在引文里，正文是独立否定；`_dg_core.py:92` `DG_QUOTE_RE` + `_mask_quotes()` 屏蔽。作者实测 `dg=PASS`，R12 字面 `r12_regex=true`（既有误命中）。
6. **弱化肯定**：`不无关系` / `无不称快` 仍属 ¬¬P，本方案保留 CATCH；在「完成断言」语境下是否算**误判**需所有者裁定 → **未验**（`_dg_DESIGN.md:96`、`:218`、`:304`）。

---

## 3 构式生成方案

### 3.1 部件化形式化（实读 `_dg_core.py:35-92`、`_dg_pasteable.py:19-74`）

```
NEG1  ∈ 闭合表 59 项  ：单字否定 / 判断系词 / 时体经验 / 能愿情态 / 反问周遍算子
MID   ∈ 闭合表 23 项（含 ε）：只收虚词·情态·能愿·程度·系词·述谓桥；刻意不含「但」、不含实词
NEG2  ∈ 闭合表 21 项  ：不/没/没有/毫无/无/未/非/否认/不承认/不认为/不宣告/不出现/…
GAP   ∈ 闭合表  9 项（含 ε）：把/将/被/让/令/以/按/照
V     ∈ SCOPE_VERB 29 项：仅完成/述谓动词（宣告/认定/认为/承认/写/填/登记/…）
X     ∈ SPLIT_TAIL  5 项：不可/不行/不成/不可谓/不罢休
PSEUDO_DN 12 项：无非/莫非/莫不是/不非/没没/无无/非非/没不/不没/非不/没没不/不不不
```

### 3.2 闭合规则（**2 条**，不是无限加词）

```
T12（连写式）： S ::= ¬PSEUDO · NEG1 · MID · NEG2 · GOVERN        # 零通配
T3 （分离式）： S ::= ¬PSEUDO · NEG1 · GAP · V · COMP · X · GOVERN
COMP   ::= (?:(?!(?:_SECOND))[^BQ]){0,4}?       # 唯一通配：≤4 字、排除句界/引号/第二主语
GOVERN ::= (?=[^BQ]{0,24}$)                      # 同微句、距 token ≤24，沿用 NEG_WINDOW
BQ     ::= 。！？；;，,、：:\n「」『』“”`
```

`_dg_core.py:128` 编译成**一条** `re.Pattern`。`_dgv_probe.py`（本会话实跑）输出：
`DG_STATS = {n_neg1:59, n_mid:23, n_neg2:21, n_gap:9, n_verb:29, n_tail:5, n_pseudo_veto:12, cartesian_T12:28497, cartesian_T3:76995, cartesian_total:105492, rule_count:2, pattern_chars:836, wildcards:1}`、`pattern 与 core 相同 = True`、`R12_TEN 全生成 = True`。

**闭合性边界**（`_dg_DESIGN.md:137-139`）：规则条数恒为 2；扩词只能改 6 张有限常量表；不能新增模板、不能放宽 `COMP ≤4`、不能把 `GOVERN` 换成 `.*`。笛卡尔积 28,497 + 76,995 = **105,492** 个生成串。

### 3.3 排除「两个独立否定」的机制 与 实测（★ 此项被复核判 partial，见 §6）

设计稿 `_dg_DESIGN.md:141-158` 给 7 条结构不变式：① `_scope()`/`DG_BREAK_RE` 按句界·逗号·冒号·转折词切断；② `_mask_quotes()` 屏蔽引证跨度；③ T12 零通配 + `MID` 闭合虚词表 ⇒ `无越权断言…不出现`/`不闻不问` 拼不出；④ `DG_SECOND_SUBJ_RE` 第二主语 veto；⑤ `DG_COORD_RE` 并列 veto；⑥ `PSEUDO_DN` 伪构式 veto；⑦ 全程不做否定词奇偶计数。作者实测：`_dg_step34.py` → `→ 真负样本 n=19 ; DG 误判(fp) = 0 : []`、N03 `dg=CATCH`。

**但复核证实「证明不覆盖被声称的交付形态」**，本会话逐条重跑：

- `python -I -X utf8 .../_dgv_struct.py` →
  `r10_context co_names = ['CLAUSE_BREAK','DOUBLE_NEG_RE','NEG_RE','NEG_WINDOW',...]`、`r12_scan co_names = ['append','end','escape','finditer','r10_context','re','start']`；
  `guard dg_double_neg/_mask_quotes/_scope/DG_SECOND_SUBJ_RE/DG_COORD_RE/DG_QUOTE_RE/DG_BREAK_RE 在 r10_context 中 = False ; 在 r12_scan 中 = False`（`_dgv_struct_out.json:40-57`）。即**只换 `:76` 一行后，7 条不变式里 4 条 guard 一个都不执行**，正则内只剩 PSEUDO_DN / COMP / GOVERN。
- 同脚本 S2：`_SECOND 中任一项是否可能由 NEG1+MID+NEG2 拼出： []`、`并列标记是否出现在 MID/NEG1/NEG2 中： []` → `→ 结论：对 T12 而言，dg_double_neg 的两条二次 veto 结构性不可达`；4 条 `并不否认甲方/本笔/对方/本件不宣告…` 全 `hit=True hit_text='并不否认' tmpl=T12_adjacent`（`:58-87`）。
- 同脚本 S3：`core 含 assert=False 含自检/单元函数=False`、`pasteable 含 assert=False ...` → `_dg_DESIGN.md:306` 承诺的「把 MID 不得含实词 / COMP ≤4 / GOVERN ≤24 写成单元断言，随表一起验」**未实现**（`:88-91`）。
- 同脚本 S4：`_dg_core.py:63-67` 的 `NEG2` 含 `否认/不承认/不认为/不宣告/不出现` 5 个完整否定谓语，本身即**独立否定**短语；实跑生成 17 条 `NEG1+ε+实词NEG2` 串（如 `并不否认`、`未不宣告`），与 `:150`「隔着实词就拼不出」的前提不完全一致（`:140-165`）。
- `python -I -X utf8 .../_dgv_neg2.py`（30 条刁钻负样本）→
  `→ base=PASS 且 一行替换=CATCH（新增误判）= 17 : ['W01'..'W07','W10'..'W14','W26'..'W30']`；
  `→ base=PASS 且 DG纯函数=CATCH（新增误判）= 7 : ['W10','W11','W12','W13','W14','W28','W29']`；
  `→ 一行替换总 CATCH = 25/30; 纯函数总 CATCH = 8/30; base 总 CATCH = 8/30`。
  典型：`W01 旧稿并不否认然而本件不宣告已生效` → `base=PASS pure=PASS oneline=CATCH raw=并不否认`；`W13 并不否认本笔不宣告已生效` 的第二主语「本笔」在 `_SECOND` 表内仍**误判**。根因：转折词只在 `DG_BREAK_RE`（`_dg_core.py:89`）里，`GOVERN` 的 `_BQ`（`:86`）不含它们；`CLAUSE_BREAK`（`_g7_predicates.py:71`）也只有 `。！？；\n`。
- 公平登记：`_dgv_neg2.py` 的 `③④-补` 4 条 `无越权断言…不出现` 骨架 `base=PASS pure=PASS oneline=PASS` —— docstring 点名的骨架没问题；破的是「不会把**任何**两个独立否定短语误判」这个一般性断言。

**结论**：在给定闭合表与 2 条模板下，「不误判两个独立否定」是**结构不变式**（不是自然语言完备性定理），但**对申报的「一行替换」交付形态不成立**，标 **unconfirmed**。修复方向（**不实施**）：须把 `_mask_quotes/_scope/DG_SECOND_SUBJ_RE/DG_COORD_RE` 并入 `r10_context` 的 `dbl` 判定（至少改 `:92`）、把转折/让步/追加连词补进 `CLAUSE_BREAK` 或 `_BQ`、给 T12 增加 N2 前后向的第二主语/并列检查、补上单元断言；这与「一行替换、调用点零改动」申报冲突，故复核判 partial。

### 3.4 可粘贴片段（逐条给出，不以「已扩充」概括）

来源 `lead/dneg_generative_20261109/_dg_pasteable.py:19-127`（本会话实读；独立 import 实编译通过）。**若将来所有者授权**改 `_g7_predicates.py`，把下面整段插到 `:76` 之前，然后把 `:76` 那一行替换成 `DOUBLE_NEG_RE, _DG_PATTERN, _DG_STATS = dg_build_dropin_regex()`；**本任务未实施该替换**。

```python
import re

NEG1 = (
    "不", "没", "无", "非", "未", "莫", "勿", "别", "甭", "岂", "焉", "安", "谁说",
    "并非", "并不是", "不是", "亦非", "绝不", "决不", "从不", "从未",
    "未尝", "未曾", "未始", "未有", "何尝", "未免", "未必",
    "不能", "不可", "不得", "没有", "不敢", "不会", "不可能", "不该", "不应",
    "不准", "不宜", "不肯", "不屑", "不便", "不免", "不由得", "忍不住",
    "没法", "无法", "不见得", "不一定", "不否认", "并不",
    "岂能", "焉能", "哪能", "安能", "岂敢", "何能", "谁能", "莫不",
)
MID = (
    "",
    "得", "能", "可", "谓", "为", "是",
    "会", "敢", "必", "免", "始", "尝", "曾", "有",
    "可能", "一定", "见得", "由得", "住",
    "得不", "说不", "说",
)
NEG2 = (
    "不", "没", "没有", "毫无", "无", "未", "非", "莫", "别", "勿", "不是",
    "否认", "不承认", "不认为", "不宣告", "不出现",
    "不可", "不行", "不成", "不可谓", "不是说",
)
GAP = ("", "把", "将", "被", "让", "令", "以", "按", "照")
SCOPE_VERB = (
    "宣告", "宣布", "宣称", "声称", "断言", "认定", "认为", "承认", "说", "写",
    "写成", "记作", "记为", "标为", "视作", "视为", "判为", "登记", "注明",
    "录入", "填", "登", "记", "签", "做", "算", "应用", "覆盖", "代填",
)
SPLIT_TAIL = ("不可", "不行", "不成", "不可谓", "不罢休")
PSEUDO_DN = ("无非", "莫非", "莫不是", "不非", "没没", "无无", "非非",
             "没不", "不没", "非不", "没没不", "不不不")

_BREAK = r"。！？；;，,、：:\n"
_BQ = r"。！？；;，,、：:\n「」『』“”`"
_SECOND = r"本笔|本件|本节|本回件|本候选|该笔|该件|此笔|台账|母本|本域|本轮|审阅回件|复核回件|第\s*\d+\s*笔"
DG_BREAK_RE = re.compile(r"[" + _BREAK + r"]|但|但是|然而|不过|却|只是|反之|相反|另外|另")
DG_SECOND_SUBJ_RE = re.compile(r"(?:" + _SECOND + r")")
DG_COORD_RE = re.compile(r"[/／]|、|或|以及|同时|并且|一是|二是|其一|其二")
DG_QUOTE_RE = re.compile(r"「[^」\n]*」|『[^』\n]*』|“[^”\n]*”|`[^`\n]*`")

def _alt(words):
    return "(?:" + "|".join(re.escape(w) for w in sorted(set(words), key=lambda x: (-len(x), x))) + ")"

def dg_build_dropin_regex():
    n1, mid, n2 = _alt(NEG1), _alt(MID), _alt(NEG2)
    gap, verb, tail = _alt(GAP), _alt(SCOPE_VERB), _alt(SPLIT_TAIL)
    veto = r"(?!(?:" + "|".join(re.escape(w) for w in PSEUDO_DN) + r"))"
    comp = r"(?:(?!(?:" + _SECOND + r"))[^" + _BQ + r"]){0,4}?"
    govern = r"(?=[^" + _BQ + r"]{0,24}$)"
    t12 = r"(?P<t12>" + veto + n1 + mid + n2 + r")"
    t3 = r"(?P<t3>" + veto + n1 + gap + verb + comp + tail + r")"
    pattern = "(?:" + t12 + "|" + t3 + ")" + govern
    n_t12 = len(set(NEG1)) * len(set(MID)) * len(set(NEG2))
    n_t3 = len(set(NEG1)) * len(set(GAP)) * len(set(SCOPE_VERB)) * len(set(SPLIT_TAIL))
    return re.compile(pattern), pattern, {
        "n_neg1": len(set(NEG1)), "n_mid": len(set(MID)), "n_neg2": len(set(NEG2)),
        "n_gap": len(set(GAP)), "n_verb": len(set(SCOPE_VERB)), "n_tail": len(set(SPLIT_TAIL)),
        "n_pseudo_veto": len(set(PSEUDO_DN)),
        "cartesian_T12": n_t12, "cartesian_T3": n_t3, "cartesian_total": n_t12 + n_t3,
        "rule_count": 2, "pattern_chars": len(pattern), "wildcards": 1,
    }

DG_DROPIN_RE, DG_PATTERN, DG_STATS = dg_build_dropin_regex()
R12_TEN = ("不得不", "并非不", "并不是不", "不是不", "无不",
           "没有不", "不无", "不能不", "不可不", "未曾不")

# --- 改前（_g7_predicates.py:76）---
# DOUBLE_NEG_RE = re.compile(r"(不得不|并非不|并不是不|不是不|无不|没有不|不无|不能不|不可不|未曾不)")
# --- 改后（同一行；:69-75 docstring / :78-111 r10_context / :134-148 r12_scan / :144 调用点零改动）---
DOUBLE_NEG_RE, _DG_PATTERN, _DG_STATS = dg_build_dropin_regex()
```

纯函数 `_mask_quotes()` / `_scope()` / `dg_double_neg()` / `dg_scan()` 在 `_dg_pasteable.py:130-182`；**注意**：按 §3.3 复核结论，这段「一行替换」形态不调用它们，故不能用来支撑「不误判独立否定」的证明。

### 3.5 与既有十式的关系

- 逐字对账：`_dg_step1_out.json:r12_ten` 十式 `r12_regex=true / dg_regex=true` 全 10 条；`_dg_step34.py (3b)` → `→ 十式 R12 全 CATCH=True ; DG 全 CATCH=True`。
- 关系：`L(R12 十式) ⊊ L(DG)`；`_dg_core.py:144-145` `R12_TEN` 保留原十式字面表作**对账锚**（不参与生成）。
- 兼容方式：**替代而非并存**（生成结果就是 `re.Pattern`，`.search()` 语义与 `:92` / `:144` 兼容）；但「调用点零改动」这一申报被 §3.3 的 `co_names` 实查证明**不足以兑现安全约束**，标 **unconfirmed**。

---

## 4 覆盖率提升

命令（本会话实跑）：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dg_step34.py` →
`→ DG 覆盖 19/19 ; H5 超集字面命中 19/19 ; R12 0/19`、`→ 十式 R12 全 CATCH=True ; DG 全 CATCH=True`、`→ 真负样本 n=19 ; DG 误判(fp) = 0 : []`、`→ 17 条中 DG 命中 16 ; H5 命中 0 ; R12 命中 0`、`→ 分离型四条 DG 命中 0/4`。

### 4.1 19 式逐条（改前 → 改后）

| # | 构式 | R12（改前） | H5 超集 | DG（改后） | DG 命中串 |
|---|---|---|---|---|---|
|1|亦非不|False|True|**CATCH**|亦非不宣告|
|2|未尝不|False|True|**CATCH**|未尝不认为|
|3|未始不|False|True|**CATCH**|未始不认为|
|4|未有不|False|True|**CATCH**|未有不认为|
|5|莫不|False|True|**CATCH**|莫不认为|
|6|不敢不|False|True|**CATCH**|不敢不承认|
|7|不会不|False|True|**CATCH**|不会不承认|
|8|不可能不|False|True|**CATCH**|不可能不宣告|
|9|未必不|False|True|**CATCH**|未必不认为|
|10|未免不|False|True|**CATCH**|未免不认为|
|11|岂能不|False|True|**CATCH**|岂能不|
|12|焉能不|False|True|**CATCH**|焉能不|
|13|哪能不|False|True|**CATCH**|哪能不|
|14|不可谓不|False|True|**CATCH**|不可谓不宣告|
|15|不为不|False|True|**CATCH**|不为不认为|
|16|并非没有|False|True|**CATCH**|并非没有|
|17|并非毫无|False|True|**CATCH**|并非毫无|
|18|不是没有|False|True|**CATCH**|不是没有|
|19|并不否认|False|True|**CATCH**|并不否认|

`R12 0/19 → DG 19/19`（若把十式 + 19 式合成 29 式已知集：10/29 → 29/29）。逐条证据 `_dg_step34_out.json:step3a_gaps:2-136`。

### 4.2 十式是否退化

`_dg_step34_out.json:step3b_ten` 十条全部 `r12_catch=true / dg_catch=true`；`_dgv_probe.py` → `R12_TEN 全生成 = True`。74 条回归 `chain FP` 改前 2 → 改后 2（**未新增误报**，见 §5.3）。十式**不退化**。

### 4.3 20 条负样本 fp（逐条）

`_dg_step34_out.json:step3c_negatives`（N03 是已知真 DN 对照，期望 CATCH；其余 19 条为真负样本）：

| id | 形态 | expect | dg | R12 字面 | H5 字面 |
|---|---|---|---|---|---|
|N01|`无越权断言：本件不出现「可应用母本…」`|PASS|PASS|false|false|
|N02|`CANDIDATE:155` 逐字形态|PASS|PASS|false|false|
|N03|三否定词 `并未漏看…并非不宣告`（对照）|CATCH|**CATCH**|true|true|
|N04|单重否定 `不宣告…`|PASS|PASS|false|false|
|N05|`不得写成「本笔已生效」；本件只登记`|PASS|PASS|false|false|
|N06|跨句 `上一轮回件不宣告…，本笔已入账`|PASS|PASS|false|false|
|N07|`不闻不问`|PASS|PASS|false|false|
|N08|`不卑不亢`|PASS|PASS|false|false|
|N09|`不打不成交`|PASS|PASS|false|false|
|N10|`不，` 独立叹词|PASS|PASS|false|false|
|N11|`无非`|PASS|PASS|false|false|
|N12|`莫非`|PASS|PASS|false|false|
|N13|`不但不`|PASS|PASS|false|false|
|N14|`非但不`|PASS|PASS|false|**true（H5 过宽）**|
|N15|`…，但台账已入账` 转折|PASS|PASS|false|false|
|N16|`无越权断言 / 不出现…` 斜杠并列|PASS|PASS|false|false|
|N17|`未核 grep 结果：已生效 0 命中`|PASS|PASS|false|false|
|N18|双引文并列 `也不出现…`|PASS|PASS|false|false|
|N19|`不见得…，也未入账`|PASS|PASS|false|false|
|N20|引文内 `「并非不宣告已生效」`|PASS|PASS|**true（R12 字面误命中）**|true|

作者口径：`真负样本 n=19 ; DG 误判(fp) = 0 : []`，N03 `dg=CATCH` 正确。**但这不是全域结论**：复核员 30 条刁钻负样本（本会话重跑 `_dgv_neg2.py`）得 `一行替换总 CATCH = 25/30; 纯函数总 CATCH = 8/30; base 总 CATCH = 8/30`，新增**误判** 17 / 7 条；`_dgv_probe.py` 得 `→ DG 纯函数 fp = 3 : ['V04','V13','V15']`、`→ DG 一行替换落地 fp = 8 : ['V01','V02','V03','V04','V05','V12','V13','V15']`。故 `fp = 0` 只在作者自造 20 条上成立，标 **unconfirmed**（其余伪构式 → **未验**）。

### 4.4 与 H5 补丁方案对比（`H5_DN_EXTRA`）

实读 `_h5_pasteable.py:28-40`：`H5_R12_TEN`（十式）+ `H5_DN_EXTRA`（19 式字面 + 分离型通配 `非[^，,。；;]{0,4}不(?:宣告|认定|认为|承认|说|写|登|记|填)`）→ `H5_DOUBLE_NEG_RE`，pattern 162 字符；`:44-52` `H5_BRIDGE_RE`、`:55-65` 作用域与辖域框。

| 维度 | H5 补丁 | DG 构式生成 | 依据 |
|---|---|---|---|
|19 式|19/19 字面|19/19 生成|`(3a)`|
|十式|保留字面|生成 + 对账锚|`(3b)`|
|复核员 17 条「都漏」|**0/17**|**16/17**|`(3d)`：何尝不/安能不/岂敢不/没法不/并非未/并非无/不由得不/忍不住不/不见得不/不一定不/不是没/非写成已入账不可/非登记不可/非说不/没说不/没法不说 逐条生成；唯一 `非但不` 刻意不收（伪构式）|
|分离型整句（第二否定在 post）|**0/4**|**0/4**|`(3d-2)`：`非写成已入账不可 / 不宣告已生效不行 / 非登记已入账不可 / 不写成已入账不成` 全 `dg=false`；共同缺口，未改善|
|伪构式**误判**|N14 `h5_regex=true`（过宽）|N14 `dg=PASS`|`(3c)`|
|规则形态|`H5_DN_EXTRA` 28 支 + 1 通配|2 条模板 + 6 张闭合表 + 1 受控通配|`DG_STATS`|
|作用域|`h5_govern()` G1–G4，`H5_GOVERNANCE_FIX.md:298` 自陈 filler≤4 等缺陷|自带 `_scope`/`_mask_quotes`/第二主语/并列 veto（但**一行替换时不被调用**）|`_dgv_struct.py` S1|

**取舍**：按构式覆盖面 DG 更彻底（16/17 vs 0/17，泛化到 105,492 串）；按分离型整句两者都 0/4。H5 是「窄、可核对、162 字符」的最小补丁，代价是 `H5_DN_EXTRA` 枚举不穷尽 + 通配过宽；DG 是「生成、可泛化、836 字符」的结构补丁，代价是闭合性靠约束不变式而非人工逐条核对、且安全约束在申报的交付形态下未生效（partial）。

---

## 5 对三层的影响

### 5.1 GP-A1 实跑（能兜住）

命令（本会话实跑）：`python -I -X utf8 .../_dg_step34.py` →
```
GP-A1  expect=CATCH base_chain=PASS  (r10=0 r12=0 n13=0 conflicts=0) | DG_r12=1 hit=亦非不宣告
GP-A1  expect=CATCH DG_chain=CATCH layers={'R9': 3, 'R10': 0, 'R12': 1, 'N13': 1, 'R11': 1}
      span tok=已生效 pos=14 r10=PASS r12=CATCH n13=CATCH => CATCH rules=K1
```
复核员用**第二个真实模块实例**只替换 `DOUBLE_NEG_RE`（非 class Shim），`python -I -X utf8 .../_dgv_chain.py` →
`one-line 模拟自检：r10_context.__globals__['DOUBLE_NEG_RE'] is DG = True ; base 仍是原十式 = True`、
`GP-A1 expect=CATCH base=PASS shim=CATCH oneline=CATCH`、`[oneline span] tok=已生效 pos=14 r10=CATCH r12=CATCH n13=CATCH => CATCH rules=K1`。
依据：`_gp_pipeline.py:98`（本会话 `sed -n '96,100p'` 实读）「K1 R12 判 double_neg（肯定）→ CATCH」；`GATE_PIPELINE_COMPOSE.md:266`（实读）记 GP-A1「三层全放过」基线。**GP-A1 三口径一致兜住，⑤ 通过**。

### 5.2 另两条共同盲区不受影响（仍 PASS）

```
GP-A2  本件登记闭合，母本即日起适用      base=PASS shim=PASS oneline=PASS
GP-A3  三值填毕，见证已由编排方签字      base=PASS shim=PASS oneline=PASS
```
`_dgv_chain_out.json:76-144` 三口径 `R12=0 / N13=0 / spans=[]`；`GATE_PIPELINE_COMPOSE.md:267-268, :487`（实读）「词表外同义改写 `登记闭合 / 填毕 / 已由…签字`，`finditer` 全量也扫不到」。两条不含否定词，**spans=0，三层无输入**；双重否定只是三条共同盲区之一，另两条是「同义完成词族未登记」，本方案不解决、不声称解决。

### 5.3 哪几层改善（74 条全量，两种口径）

命令（本会话实跑）：`python -I -X utf8 .../_dg_step4c.py` →
```
CORPUS n = 74 （_gp_regression.py 逐字构造，主流程输出已拦截，未写盘）
  naive ok=34 FP=33 FN=7 / r10 ok=35 FP=20 FN=19 / r12 ok=39 FP=0 FN=35
  n13  ok=71 FP=0 FN=3   / chain ok=69 FP=2 FN=3
  chain 层间冲突 old = 31  new = 32
  GP-A1 expect=CATCH PASS -> CATCH (r12 0->1, n13 PASS->CATCH) ; 变更条数 = 1
```
改后（同脚本 `r10_dg/r12_dg/n13_dg/chain_dg`，亦见 `_dg_step4c_out.json:29-49`）：`r10 35/20/19`（不变）、`r12 40/0/34`（+1 ok，FN −1）、`n13 72/0/2`（+1）、`chain 70/2/2`（+1，FP 2→2 零新增）。改善的层 = **R12、N13、合成链**；唯一变更条目 = **GP-A1**；`GP_ALLPASS_TRUE_ASSERTION` 族 `old_ok=0 → new_ok=1`、`old_FN=3 → new_FN=2`，其余 7 族全不变。改前数字与 `_gp_regression_out.json` 基线一致。

**但层间冲突数字要按口径分开记**：`python -I -X utf8 .../_dgv_chain.py`（本会话实跑）→
`base ok=69 FP=2 FN=3 conflicts=31` / `shim 70/2/2 conflicts=32` / `oneline 70/2/2 conflicts=31`。
即作者申报「层间冲突 31→32（+1）」**只在作者 Shim 口径成立**（`_dg_step4c.py:56-66` 额外覆写 `r10_context` 的副作用）；真实一行替换是 **31→31**。ok/FP/FN 三口径一致。

### 5.4 能否解决「证据不独立」——**不能**

`GATE_PIPELINE_COMPOSE.md:499`（本会话 `sed -n '497,501p'` 实读）明载：「三层共用同一套字面词表与否定/标记词表（`NEG_RE`/`DOUBLE_NEG_RE`、N13 `_DIRECT_NEG`/`_A_AFTER`），是**相关失效**而非独立表决；N13 C 类直接转发 R10 kind，R12 复用 `r10_context`（`_g7_predicates.py:144`）」。本方案**只换其中一张词表**，三层仍共用 `extract_spans` 的同一 token 集合（`_gp_pipeline.py:58-70`）、N13 仍经 `r12_scan` 消费 R12 结论、R12 仍复用同一 24 字窗与 `CLAUSE_BREAK`。

GP-A1 改后 R12/N13 同向 CATCH 是**相关一致**，不是独立第三方证据；GP-A2/A3 继续证明共同盲区存在（三层一致放过、冲突 0）。判断：**改善召回，不改变证据不独立**；要独立需另立不同输入契约的层（语义/句法解析、人工复核项），超出本任务范围。

---

## 6 复核回件 + 结论 + 未验项

### 6.1 复核回件（绑定行，固定格式）

被核对象 SHA256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120，字节数 = 11743
被核对象 SHA256 = ffd552207039b220e2a3e649af32aea25bbcd923fe6f9742a8bdb634cb837dc6，字节数 = 5056
被核对象 SHA256 = b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c，字节数 = 8540

（三行依次对应 `lead/gate_fp7_20261108/_g7_predicates.py`、`lead/h5_governance_20261109/_h5_r12_gap_out.json`、`lead/h5_governance_20261109/_h5_pasteable.py`；sha/bytes 由本会话 `python -I -X utf8 -c "<hashlib 8 件>"` → `ALL_MATCH = True` 独立重算，与任务书【复核】`sha256Line` 三行逐字一致。）

### 6.2 复核 verdict 如实记录

**复核 verdict = partial**（任务书【复核】字段）。按交付规则：**partial → 本件相关结论标 `unconfirmed`**。具体：

- **已验为真（G-A 闭合性）**：`python -I -X utf8 .../_dgv_probe.py` → `pattern 与 core 相同 = True`、`pattern_chars = 836`、`R12_TEN 全生成 = True`、`DG_STATS = {... rule_count:2, cartesian_total:105492, wildcards:1}`；不是「无限加词」，2 条模板 + 6 张有限表成立。19 式覆盖、十式不退化、GP-A1、74 条 ok/FP/FN 数字均可复现（本会话重跑，见 §4 / §5）。
- **partial 的主破口（不误判独立否定）**：§3.3 的 `co_names` 实查、T12 veto 结构性不可达、单元断言缺失、`NEG2` 含实词谓语、30 条刁钻负样本新增误判 17/7 条 → 该一般性断言标 **unconfirmed**；「一行替换 + 调用点零改动」申报与修复方向冲突，亦标 **unconfirmed**。
- **数字分歧如实登记**：层间冲突 `31→32`（作者 Shim）vs `31→31`（真实一行替换）；枚举清单 `68`（作者时点）/ `74`（复核员时点，AST 161）/ `75`（本会话重跑，AST 164，见 §6.4）。
- **越界核验**：复核员对 6 个只读目录做全量快照二次比对 `保护目录全量 173 件二次比对 drift = 0 []`；本会话 `git status --porcelain` 保护件均为会话前既有 `MM`/`??`，`git log --oneline -3` 无新提交（HEAD `2657458`），未 commit / 未 push。

### 6.3 枚举 vs 生成 的结论 + 过宽风险与控制

**结论：生成（但为「闭合表 + 2 条闭合规则」的生成，不是自由语法），且当前交付形态标 `unconfirmed`。**

1. **枚举** 10 式 → 19 式实测全漏；`H5_GOVERNANCE_FIX.md:314` 记 39 条漏式、27 条「都漏」；外部文献 132 个常用构式（来自任务书【设计】，本会话未重跑，标未验）。`H5_DN_EXTRA` 只是把 19 式再加进枚举表，仍不穷尽，且 `非[^，,。；;]{0,4}不(?:…)` 通配在 N14 `非但不` 上过宽。
2. **构式生成** 2 条模板 + 6 张闭合表 → 19/19、16/17、十式不退化、74 条 +1 ok 零新增 FP；但**过宽**风险实证：转折词「然而/不过/却/但/只是/反之/相反/另外」只在 `DG_BREAK_RE`（`_dg_core.py:89`）而 `GOVERN` 的 `_BQ`（`:86`）不含 → `旧稿并不否认然而本件不宣告已生效` 被一行替换 CATCH；`NEG2` 的实词谓语让 `并不否认甲方不宣告已生效` 在纯函数上也 CATCH。
3. **控制（不实施）**：`fp` 优先于 `fn`；① 把 guard 并入 `r10_context` 的 `dbl`（至少改 `_g7_predicates.py:92`）；② 转折/让步/追加连词补进 `CLAUSE_BREAK` 或 `_BQ`；③ T12 增加 N2 前后向第二主语/并列检查；④ 补 `_dg_DESIGN.md:306` 承诺未实现的单元断言（「MID 不得含实词」「COMP ≤4 且排除 BQ/第二主语」「GOVERN ≤24 非通配」）；⑤ 拿不准的弱化肯定（`不无关系`）降为 `NEEDS_HUMAN`，不直接 CATCH。这些与「一行替换」申报冲突，故不宣称可安全落地。

### 6.4 其它「枚举式正则」清单（逐条）

命令（本会话实跑）：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dgv_enum.py` → `命中行数 = 75`、`命中调用数 = 164`、`作者 _dg_step5c_out.json n = 68`、`作者 68 处是否可复现： 否：75 vs 68`；作者点名 11 处 `exists=True line_hit=True ast_hit=True` 全数可复现（`_dgv_enum_out.json:focus`）。复核员当时记 `行级 74 / AST 161`；本会话重跑 75/164 的差额由并发写入的其它 agent 文件造成（本会话 `python -I -X utf8 -c "<按 mtime 定位新增命中>"` → `new line hits (mtime>17:59): [('keff_calc_20261109/_kev_verify.py', 268, '18:12:03')]`、`new ast hits: [('check_fp_audit_20261109/_cfaa_verify.py', 70/66, '18:12:24'), ('keff_calc_20261109/_kev_verify.py', 268, '18:12:03')]`）。口径判据：单行正则字面串含 ≥4 个中文选择支；跨行拼接式需 AST 判据。

| 文件:行 | 枚举内容（实读） | 同类不完备风险 |
|---|---|---|
|`gate_fp7_20261108/_g7_predicates.py:69`|`NEG_RE` 9 支 `不\|无\|未\|非\|禁\|勿\|否决\|排除\|不宣告\|不得`|`莫/岂/焉/别/甭/毫无/否认` 不在表内（§2.2 的 `neg_count=1` 实证）|
|`gate_fp7_20261108/_g7_predicates.py:76`|本任务对象，十式|19 式全漏，已证|
|`gate_n13_20261109/_n13_pasteable.py:23`|`_NEG` 含 `不得不\|并非不\|…\|亦非\|未见\|无越权\|没有不`|与 R12 十式同源，19 式同样漏|
|`gate_n13_20261109/_n13_pasteable.py:14`|`_AFTER` 检索动作 `grep\|检索\|搜索\|查找\|清点\|核查\|…`|同义改写必漏|
|`gate_n13_20261109/_n13_pasteable.py:29`|`_CONTRAST` `但\|但是\|然而\|而\|且\|另外\|另\|同时\|并`（11 支）|转折词族不穷尽（正是 §3.3 破口）|
|`gate_v1v2_20261109/_v12_rule.py:38`|`V2_OVERRIDE_RE` `已(按\|照\|依\|经\|由\|将\|把)…(填\|登\|交\|录\|签\|算\|盘)`|同义完成词族未登记（GP-A2/A3）|
|`gate_v1v2_20261109/_v12_rule.py:43`|`ADJ_NEG_RE` 14 支 `不得\|不许\|禁止\|…\|别`|`不得不` 被当普通禁止词|
|`gate_v1v2_20261109/_v12_rule.py:54`|`H4_NOUN_RE` 15 支 `件\|路径\|字段\|值\|状态\|槽\|…`|名词族枚举|
|`h5_governance_20261109/_h5_pasteable.py:34-40`|`H5_R12_TEN` + `H5_DN_EXTRA`（19 式 + 分离型通配）|见 §4.4|
|`h5_governance_20261109/_h5_pasteable.py:44-46`|`H5_BRIDGE_RE` **51 支**（本会话 AST 判据抓到的跨行最大项）|作者行级判据漏掉的跨行枚举|
|`h5_governance_20261109/_h5_pasteable.py:55/59/65`|`H5_MICRO_BREAK_RE` / `H5_CONTRAST_RE` / `H5_FRAME_POST_RE`|作用域词表枚举|
|`re_line_20261105/W7_W4_REVIEW/_w7_c.py:236-238`|`MARK` **36 支**「未验」族 / `STRONG` 19 支「确证」族|最大规模单行枚举，「无限加词」最典型|
|`refsync_scope_20261109/_rs_markers.py:30`|10 支转录边界标记|新标记词必漏|
|`gate_validate_20261108/_gv_fixed_rules.py:35`|`DECL_RE` 12 支就地覆盖/去聚合族|同上|
|`stale_pass_20261109/_sp_classify.py:17,18,20`、`_sp_dist.py:17,18,22`|复核员定位的 6 处新增行级命中|清单时点差异来源之一|

清单结论：**真去搜了**，但需标注「作者时点 68 / 复核员时点 74（AST 161）/ 本会话 75（AST 164）」；差额来自会话间 `lead/**/*.py` 并发写入，非作者漏报。

### 6.5 判不了什么 / 未验项

**判不了**：
1. **中文双重否定全域真值**：无 BCC/CCL token 级频次，只有类型数粗估 8%–20%；语用强弱（`不无` 弱化肯定）需语言学裁定。
2. **分离型「非…不可」整句**：`_dg_step34_out.json:step3d_split4` 实跑 0/4，H5 亦 0/4，共同缺口。
3. **GP-A2/A3**：同义完成词族 `登记闭合 / 填毕 / 已由…签字`，不是双重否定，三口径仍 PASS。
4. **证据不独立**：三层相关性由架构决定（`GATE_PIPELINE_COMPOSE.md:499`），换一张词表不改变。
5. **未列举的伪构式**：20 条负样本是本项目自造；`PSEUDO_DN` 12 项未穷尽；复核员 30 条刁钻样本已证新增误判 17/7 条。
6. **74 条以外语料的 fp**：繁体 / 英文 / 被动 / 跨行 / >24 字距全部 **未验**。
7. **真实落地效果**：`_g7_predicates.py` 与所有既有件绝对只读、未改；所有「改后」来自内存 Shim / 第二模块实例，**不是真实门禁运行**。
8. **H5 补丁其它缺陷**：`H5_GOVERNANCE_FIX.md:298,456` 自陈 `partial / unconfirmed`，本件只比「双重否定覆盖」一维。

**未验（逐项列出，不补造）**：
- BCC/CCL/国家语委 token 级加权频次比例；外部文献数字（CCL 2020 王昱 28,033 句 / 97.87% / 93.10%、《中文信息学报》2024 132 构式、`不能不` 559 次）来自任务书【设计】回件，**本会话未重跑 WebSearch**；Chinese Frequency Dictionary 页面在上游 WebFetch 超时，标未验。
- `GATE_FALSE_POSITIVE_5_6_7.md:159`、`_g7_tv3_double_negation.md:8/:12`、`_h5v_full.py:88-96/:119-125`、`_n13_pasteable.py:130`、`_gp_pipeline.py:58-70/:223-265` 等件本会话**未逐件实读**，仅在任务书【设计】/【复核】材料中被引用，相关结论标未验；本会话实读者为 `_g7_predicates.py` 全文、`_h5_pasteable.py:1-75`、`GATE_PIPELINE_COMPOSE.md:264-269/485-501`、`_gp_pipeline.py:96-100`、`H5_GOVERNANCE_FIX.md:312-316`、`_dg_*.py` / `_dgv_*.py` / 各 `_out.json`。
- 弱化肯定 `不无关系 / 无不称快` 在「完成断言」语境下是否算误判；20 条自造负样本以外的伪构式；分离型 post 整句（复核未独立重跑分离型四条，仅作者 0/4 登记）。
- 单元断言、真实门禁落地、完整门禁回归：均 **未验**。
- 本会话重跑 `_dgv_enum.py` 得 75/164 与复核员 74/161 的差额已定位为并发文件，但其它 agent 后续仍可能继续写入，清单为**时点快照**。

**纪律**：零真机 / 零采样、不 commit / 不 push、未写任何保护件；本件是唯一新增交付件，落在 `lead/dneg_generative_20261109/DNEG_GENERATIVE.md`。

---

## 附：本会话实跑命令清单（逐条，输出见上文引用）

1. `python -I -X utf8 -c "<hashlib 8 件指纹>"` → `ALL_MATCH = True`（8/8 MATCH）。
2. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dg_step1.py` → 19 行 `漏判确认`、十式全 `True`。
3. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dg_step34.py` → `DG 覆盖 19/19`、`十式 R12 全 CATCH=True ; DG 全 CATCH=True`、`真负样本 n=19 ; DG 误判(fp) = 0 : []`、`17 条中 DG 命中 16`、`分离型四条 DG 命中 0/4`、`GP-A1 DG_chain=CATCH ... rules=K1`。
4. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dg_step4c.py` → 74 条 `naive/r10/r12/n13/chain` 改前改后、`chain 层间冲突 old = 31 new = 32`、`变更条数 = 1`。
5. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dgv_probe.py` → `确认漏判 10/10`、`DG 纯函数 fp = 3`、`DG 一行替换落地 fp = 8`、`pattern_chars = 836`、`R12_TEN 全生成 = True`。
6. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dgv_neg2.py` → 新增误判 17 / 7、`一行替换总 CATCH = 25/30; 纯函数总 CATCH = 8/30; base 总 CATCH = 8/30`。
7. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dgv_struct.py` → `co_names` 7 个 guard 全 False、`含 assert=False`、`_SECOND 中任一项…拼出： []`、`计数 = 17`。
8. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dgv_chain.py` → `one-line 模拟自检…is DG = True`、`GP-A1 base=PASS shim=CATCH oneline=CATCH`、`base/shim/oneline conflicts=31/32/31`。
9. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dgv_enum.py` → `命中行数 = 75`、`命中调用数 = 164`、`作者 n = 68`、11 处 focus 全 `exists=True line_hit=True ast_hit=True`。
10. `python -I -X utf8 -c "<按 mtime 定位枚举清单新增命中>"` → `keff_calc_20261109/_kev_verify.py:268 (18:12:03)`、`check_fp_audit_20261109/_cfaa_verify.py:70,66 (18:12:24)`。
11. `git status --porcelain -- lead/gate_fp7_20261108 ...` / `git log --oneline -3` → 保护件为会话前既有 `MM`/`??`，HEAD `2657458`，无新提交。
12. `grep -nE "write_text|open\(...)" lead/dneg_generative_20261109/_dg_*.py .../_dgv_*.py` → 唯一写盘目标均为写域内 `_dg*_out.json`。
13. `sed -n '264,269p;485,489p;497,501p' lead/gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md`、`sed -n '96,100p' lead/gate_pipeline_20261109/_gp_pipeline.py`、`sed -n '312,316p' lead/h5_governance_20261109/H5_GOVERNANCE_FIX.md` → §5.1/§5.2/§5.4/§2.4 的引用锚。
