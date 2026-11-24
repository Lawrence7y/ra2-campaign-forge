# 掩蔽效应审计件 — MASKING_EFFECT_AUDIT.md

> 唯一写域 `lead/masking_effect_20261109/`。本文件为**交付主件**；同域既有 `_me_*` / `_mev_*` 为撰写人/复核人前序产出，本件新增核验脚本统一前缀 `_me_auditcheck_*`。
> 零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；不改 `_rs_carrier_scan.py` 或**任何既有脚本**；绝对只读件零改动；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。
> **复核 verdict = partial（见 §6.1），故本件整体标 `unconfirmed`**；凡 `refuted` / `partial` 涉及项均按「未坐实」处理，不冒充已验。
> 写域纪律例外（如实申报）：工具/钩子在本写域内自动建了 `.mimosa/hook-state/`（2 个会话状态 JSON，共约 1099 B），**非本任务产出、非 `_me_` 前缀、未由我创建或修改**；本任务自己写出的文件一律 `MASKING_EFFECT_AUDIT.md` 或 `_me_auditcheck_*` 前缀（收尾 `python -I -X utf8 "…/_me_auditcheck_final.py"` 的 `os.listdir` / `os.walk` 实查）。

---

## 1 目的与边界

**目的**：对 `_rs_carrier_scan.py` 的「双 needle 并集 + 单一 `SELF_TEST` 布尔」交付口径做**掩蔽效应**审计——独立复现掩蔽、量化掩蔽面、构造反向掩蔽验证、设计并实跑「可区分的通过」方案、全库（有界）排查同类多输入测试、给出事件定性与报 PASS/FAIL 前清单。

**边界（只审计与设计）**：

| 项 | 本件做了 | 本件没做 |
|---|---|---|
| `_rs_carrier_scan.py` / `_me_design.py` / 任何既有脚本 | 只读、只通过 subprocess 调用**未修改的原版** | **未改一行** |
| 实验 | 全部用本任务写域的**独立新脚本** `_me_auditcheck_*.py` | 不写 hook、不改判定逻辑 |
| 绝对只读件（`lead/refsync_scope_20261109/`、`needle_norm_20261109/`、`gate_n13_20261109/`、`gate_pipeline_20261109/`、`gate_fp7_20261108/`、两件台账、`_rs_carrier_scan.py` 本身） | `hashlib` 复算指纹 | 不修改/追加/覆盖 |
| 台账注记 | **建议**（§6.3） | **未执行**（属只读件，非本件写域） |
| 真机 / 采样 | 无 | 无 |

**本会话实跑命令（全部可复核）**：
1. `python -I -X utf8 -c "…hashlib 8 件…"`（会话开头，输出见 §2.1）→ 8/8 OK
2. `python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/masking_effect_20261109/_me_auditcheck.py" > "…/_me_auditcheck_stdout.txt"` → `_me_auditcheck_out.txt`（C1–C6，EXIT=0）
3. `python -I -X utf8 "…/_me_auditcheck_plan2.py" > "…/_me_auditcheck_plan2_stdout.txt"` → `_me_auditcheck_plan2_out.txt`（EXIT=0，`ALL_SCENARIOS_MATCH_EXPECTATION = True`）
4. `python -I -X utf8 "…/_me_auditcheck_pair.py"`（探针，stdout 落本会话记录）
5. `python -I -X utf8 "…/_me_auditcheck_search.py" > "…/_me_auditcheck_search_stdout.txt"` → `_me_auditcheck_search_out.txt`（EXIT=0，耗时 244.3 s，后台完成）
6. 另有 `python -I -X utf8 -c "…"` 直读源码/文档行、最小复现（见各处引用）。

**未执行的检查（如实申报）**：未跑撰写人原 `_me_repro.py` / `_me_analyze.py` / `_me_design.py` / `_me_search_git.py` / `_me_reverse*.py`；它们的输出是**本会话直读在盘文件**后引用（文件:行），按编排方口径计入「实跑命令+输出」但**不冒充本件本次实跑**。本件自己实跑的是上述 1–6。复核人 `_mev_*` 输出同样为直读引用。

---

## 2 上游指纹 + 掩蔽复现 + 四道门机制 + 定性

### 2.1 八件上游指纹（`hashlib`，本会话开头实跑）

命令：`python -I -X utf8 -c "…hashlib.sha256(open(f,'rb').read())…"`（8 件逐一，含字节数比对）。输出（`_me_auditcheck_out.txt` C1 段再次复算，同为 8/8 OK）：

| # | 文件 | SHA256 | 字节数 | 结果 |
|---|---|---|---|---|
| 1 | `lead/refsync_scope_20261109/_rs_carrier_scan.py` | `9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57` | 16053 | OK |
| 2 | `lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md` | `83b215ccbbf2c3e221c247e7bd9c7c221fddcf9472977d2df8902bf1b94ec65e` | 49958 | OK |
| 3 | `lead/refsync_scope_20261109/_rs_CARRIER_MAP.md` | `aa2dbe945c9d8fdc6aebde849701393f6f8766c51b372329d588616781c2f83f` | 35782 | OK |
| 4 | `lead/needle_norm_20261109/_nn_REPORT.md` | `820db1eb93a630344623fb055449dfbd888cb46294dba3f462d9891a1d91e041` | 40549 | OK |
| 5 | `lead/needle_norm_20261109/NEEDLE_NORMALIZATION.md` | `c0e716ec2baaab0082d0c7af83a351b9aa12eb01a4bf2ba6a223c8b81c5de8e6` | 41618 | OK |
| 6 | `lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md` | `058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec` | 18980 | OK |
| 7 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 | OK |
| 8 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 | OK |

`ALL_8_OK = True`（会话开头独立一次 + `_me_auditcheck_out.txt` C1 一次；复核人 `_mev_final_out.txt:17-25` 收尾再 8/8）。绝对只读件零改动。

### 2.2 五数字复现（单 needle / 双 needle / SELF_TEST / not-scanned）

**编排方五数字**（ask 给出/撰写人 `_me_repro_summary.txt:8-11,16-19`）：单 `EXIT=1 / SELF_TEST=FAIL / scanned=637 / occurrences=79 / :22 got=<not-scanned>`；双 `EXIT=0 / SELF_TEST=PASS / scanned=637 / occurrences=122 / :22 got=REFUTING_QUOTE`。口径 `--include-refuting --max-depth 2 --ext .md`（`_me_repro.py` 源码，撰写人称由 8 组 sweep 定位）。

**本会话独立实跑（`_me_auditcheck.py` C2，未修改扫描器，4 配置）**，输出 `_me_auditcheck_out.txt` C2 段：

| 配置 | 命令（节选，`python -I -X utf8` + 绝对路径） | EXIT | SELF_TEST | scanned / occurrences | `:22` |
|---|---|---|---|---|---|
| 单 needle | `…_rs_carrier_scan.py --needle 只能判「不可复现」 --include-refuting --max-depth 2 --ext .md` | 1 | **FAIL** | 646 / 87 | `FAIL … got=<not-scanned>` |
| 双 needle | 同上 + `--needle 不能定位当年错误步骤` | 0 | **PASS** | 646 / 136 | `PASS … got=REFUTING_QUOTE` |
| 坏针 | `--needle 不能定位当年错误步骤 --needle TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ` | 0 | **PASS** | 646 / 93 | `PASS … got=REFUTING_QUOTE` |
| 三针（反向） | 双针 + `--needle 登记效力说明` | 1 | **FAIL** | 646 / 137 | `FAIL … got=ANALYSIS_MENTION` |

原始 stdout 落盘并算 sha256：`_me_auditcheck_single_out.txt` `8212af3c…`、`_me_auditcheck_double_out.txt` `ea9c9d50…`、`_me_auditcheck_broken_out.txt` `2fd35fd6…`、`_me_auditcheck_triple_out.txt` `2456fe22…`（完整 64 位见 `_me_auditcheck_out.txt`）。

**数字差异如实登记，不补造**：撰写时点 637/79/122，复核人时点 643/87/136（`_mev_forensics_out.txt:2-4`），本会话 646/87/136。原因是并行任务与本写域自身持续新建 `.md`（`_me_REPORT.md` 14:46 自身即 n1=8/n2=8/un=14，见 `_mev_forensics_out.txt:29`）。**本会话按 mtime CUT=2026-11-09 14:15 实算**（`_me_auditcheck_out.txt` C4）：`md files=637 |U1|=79 |U2|=84 |only1|=38 |only2|=43 |both|=41 |union|=122` —— 与撰写人五数字**逐项精确吻合**，差值全部来自 CUT 之后新建件。结构与结论不受语料漂移影响；本件三个数字一律采用 **CUT 口径 79 / 84 / 122**（见 §3）。

### 2.3 `:22` 两 needle 位置（逐字实跑）

`_me_auditcheck_out.txt` C3（`python -I -X utf8 …/_me_auditcheck.py`，直读 `_ve_DRAFT_S609.md:22`）：

```
line22 len = 711
N1 '只能判「不可复现」' find = -1
N2 '不能定位当年错误步骤' find = 172
variant '只能判『不可复现』' find = 162
N3 '登记效力说明' find = 17
CONTAINS_BOTH_VERBATIM = False
outer fragment '「只能判『不可复现』、不能定位当年错误步骤」' find = 161
CJK punctuation codepoints present = U+3001, U+3002, U+300C, U+300D, U+300E, U+300F
```

**纠正 ask 的一处表述**：`:22` **并不「同时逐字含两个 needle」**——N1 的直角引号 `「」`(U+300C/D) 与原文内层弯引号 `『』`(U+300E/F) 不一致，`find=-1`；只有 N2 在 pos=172 命中。编排方 given `hasN1=false, hasN2=true, posN1=-1, posN2=172, len=711` 正确，ask 叙述按实跑纠正为「只含第二 needle」。`:111-124 / :123 / :138` 三个行号引号码位为 ASCII 冒号+数字，不构成 needle 差异（复核人 `_mev_forensics_out.txt:37-45` 独立同结论；撰写人 `_me_analyze_out.txt:4-10` 同结论）。

### 2.4 四道门（追到 `file:line`）

源码 `lead/refsync_scope_20261109/_rs_carrier_scan.py`（本会话 `Read` 全文）：

| 门 | 行 | 原文 | 作用 |
|---|---|---|---|
| 门1 文件级 | `:229` | `if not any(n in txt for n in a.needle): continue` | 整件无任一 needle ⇒ 整件跳过，`splitlines()` / `:232` 都不跑 |
| 门2 行级 argmin | `:165` | `pos = min((line.find(n) for n in needles if n in line), default=-1)` | 取命中 needle 的**最小位置**；全不命中 ⇒ `-1` |
| 门3 硬丢弃 | `:166-167` / `:238-239` | `if pos < 0: return None` / `c = classify_line(...); if not c: continue` | `None` ⇒ 该行**根本不进 `carriers`** |
| 门4 负控查表 + 单布尔 | `:327-331` / `:324,:343,:346,:349` | `role_of()` 按 `(rel,line)` 在 carriers 找，找不到返回 `"<not-scanned>"`；`ok &= good` → `SELF_TEST = PASS/FAIL` → `return 0 if ok else 1` | 自检只查「在不在 carriers」，不查「哪根 needle 命中」；k 输入压成 **1 bit** |

追通（撰写人 `_me_analyze_out.txt:12-19` + 本会话 C2/C3）：
- 单 needle：`:22` 无 N1 ⇒ 门2 `pos=-1` ⇒ `:166-167 return None` ⇒ 门3 `continue` ⇒ 门4 `got=<not-scanned>`（**不是判错角色，是根本没被扫描**）。
- 双 needle：N2 在 pos 172 命中 ⇒ 门2 `pos=172` ⇒ `:168 q = quoted_containing(line,172)` 命中引号跨度 `(161,183,'「')` ⇒ `:173 q and negs`（同行 11 个否定词：`不再成立/过时/已定谳/…`）⇒ `role=REFUTING_QUOTE` ⇒ 门4 `PASS`。**该判对与 N1 是否工作无关**；N1 从未参与 `:22` 判定。

**决定性反证（本会话实跑）**：`--needle 不能定位当年错误步骤 --needle TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ` → `_me_auditcheck_out.txt` C2 `[broken]`：`EXIT=0`、`SELF_TEST = PASS`、6 条负控全 `PASS`（撰写人 `_me_broken_needle_out.txt:546-552` 同）。即**一根 needle 完全坏掉，自检仍 6/6 PASS**。单 N2 一根亦 6/6 PASS（`_me_n2only_out.txt:546-552`）——6 条负控里 5 条 `hit_set={N1,N2}`、`:22` 为 `{N2}` 独占（本会话 `_me_auditcheck_out.txt` C4 六行逐条实算：`hits=[0,1]`×5 + `hits=[1]`×1，与 `_me_analyze_out.txt:47-53` 一致）。

### 2.5 正确行为 vs 测试设计缺陷（定性）

- **脚本行为符合自身规格**：`any` 并集 + `min(pos)` + 负控查表，代码与文档 `_rs_carrier_scan.py:10-27`（R1–R6）、`:207-216`、`:312-322` 一致，**无实现 bug**。
- **但测试设计有缺陷**：`SELF_TEST = PASS` 被当成「载体扫描口径已修正、6 条负控都覆盖」的交付证据（`REFSYNC_SCOPE_FIX.md:243` R6 描述、`:251` 登记双 needle 命令 + `SELF_TEST = PASS`(6/6)、`:252-253` 另两条 PASS）。该 PASS 只证明「**N1∪N2 并集**覆盖这 6 行」，不证明「**每根 needle 独立工作**」。观测（∃i 命中）**弱于**待证命题（∀i 有效），且无命中溯源、无逐针独占见证。
- 按【铁律】「掩蔽不是眼下的 bug，是**测试设计缺陷**；若某处通过是被掩蔽的，即使结果碰巧正确，也必须标为不可信」：**判测试设计缺陷，上一轮 `SELF_TEST = PASS` 不可信**（严重度 high）。不是「脚本的正确行为」，也不是「部分可信」。

---

## 3 掩蔽面量化

### 3.1 三个数字（CUT=14:15 口径，本会话 `_me_auditcheck_out.txt` C4 实算）

| 量 | 值 | 来源 |
|---|---|---|
| `\|U1\|` N1 命中行 | **79** | 本会话 C4；= 扫描器单 needle `carrier occurrences` 79（`_me_repro_summary.txt:9`） |
| `\|U2\|` N2 命中行 | **84** | 本会话 C4；= 单 N2 84（`_me_n2only_out.txt:10`） |
| `\|union\|` 双 needle 并集行 | **122** | 本会话 C4；= 扫描器双 needle `carrier occurrences` 122（`_me_repro_summary.txt:17`） |

配套：`|only1|=38`、`|only2|=43`（= **被掩蔽行数**，只被 N2 命中、不被 N1 命中；`:22 ∈ only2`，`_me_analyze_out.txt:40`）、`|both|=41`（两根同命中，**这 41 行任一根失效都零信号**，`_me_design_out.txt:27` 给 41/122=33.6% 为「本次 PASS 里被掩蔽的行数」）。交叉校验 `79 = 38+41`、`84 = 43+41`、`122 = 38+43+41`（`_me_analyze_out.txt:35-38` 两项 `match=True`）。

**单/双/合并三个漏检数字**（相对双 needle 并集）：**只用 N1 漏 43 行**（=|only2|）；**只用 N2 漏 38 行**（=|only1|）；**两个都用漏 0 行**（并集按定义完备）。本会话 C4 输出 `MISSED vs union: N1-only misses=43 ; N2-only misses=38 ; both misses=0`。**差值 43 = |only2|** 即第二 needle 恰好补回 43 行；正式口径与「去掉一根输入」对照 79 vs 122 的差异由此可解释。

> 语料漂移后的当前值（本会话 C2/C4，646 文件）为 87 / 92 / 136，撰写人/复核人/本件三方均如实登记；**审定数字以 CUT 口径 79/84/122 为准**，不拿漂移值冒充交付数字。

### 3.2 needle 数增加的推演（N=2→3→4，撰写人 `_me_analyze_out.txt:74-85` 实跑）

| N | union 行数 | 各针命中行数 | 实际 hit-set 型 | 2^k−1 |
|---|---|---|---|---|
| 2 | 122 | [79, 84] | 3 | 3 |
| 3 | 122 | [79, 84, 4] | 4 | 7 |
| 4 | 125 | [79, 84, 4, 7] | 5 | 15 |

1. **并集单调不减**：门1 `any` / 门2 `min(find)` 对「是否进 carriers」单调，加 needle 只增行不减行（122→122→125）。本会话 C2 三针 `occurrences=137`（当前语料）> 双针 136，同向。
2. **可归因性单调下降**：k 根命中型有 2^k−1 种，输出仍只有 6 条负控 + 1 个 `SELF_TEST` 布尔（`:332-346`）——**证明 1 bit，却声称 k bit**（`_me_analyze_out.txt:82-85`）。
3. **负控被「并集化」概率上升**：本例 6 条负控中 5 条 `{N1,N2}`、仅 `:22` 为 `{N2}` 独占；正因有这 1 条独占负控，单 needle 才暴露 N1 漏检。若再加一根把这唯一独占行也变共现，6/6 负控全部可由任意一根活针满足 ⇒ **完全不可分辨**。
4. **反向掩蔽概率上升**：每多一根就多一次 `min(pos)` 抢占机会（下节）。

### 3.3 反向掩蔽（加输入让「判对」变「判错」）

- 「加 needle 让本来能扫到的行变成扫不到」：**不可能**（门1/门2 单调）。实测 N=3 时 union 仍 122，未减少。
- 「加 needle 让本来判对的行改判 / 从修复清单消失」：**可能且已端到端实跑**。机制：`:165` 取 `min(pos)`，`:168` 用该 pos 求 `quoted_containing`，`:173-182` 角色全依赖这个 `q`。新增针若命中更靠前且落在引号内/外，`q` 改变。

**真实语料端到端（未修改扫描器，本会话 C2 `[triple]`）**：`--needle N1 --needle N2 --needle 登记效力说明` → `EXIT=1`、`SELF_TEST = FAIL`、`FAIL … :22 want=REFUTING_QUOTE got=ANALYSIS_MENTION`、`carrier occurrences` 不变（行**仍在 carriers**，只是角色被改）。`登记效力说明` 在 `:22` pos=17、引号外，`min` 把 pos 从 172 拉到 17，`q` 变 `None` ⇒ 从 `REFUTING_QUOTE` 掉到 `ANALYSIS_MENTION`（`_me_analyze_out.txt:58-72`；撰写人 `_me_reverse3_out.txt:759,761` 同结论，换 `与既有草案`(pos=4) 见 `_me_reverse3b_out.txt`）。**「加一根 needle 让原本 PASS 的自检变 FAIL」即反向掩蔽的对称形态；若无负控这条线，它会静默改判而不报错。**

**构造验证**（`_me_reverse_synthetic_out.txt:5-13`，用未修改 `classify_line`）：`「核对」 只能判「不可复现」` 在 `[N]` 下 `ASSERTION`(pos=5,q=None)、在 `[N,'核对']` 下 `QUOTED`(pos=1,q=`「核对」`) ⇒ **`needs_fix True→False`，真载体从修复清单静默消失**；另有 `ANALYSIS_MENTION→REFUTING_QUOTE` 翻转。**诚实阴性**：真实语料 24 条 `ASSERTION` × 9 个候选额外针的搜索 `flip count = 0`（`_me_reverse_assertion_out.txt:3`），即构造上成立、本语料**未实证**，不夸大。

**结论**：`scanned` 单调，`role / needs_fix` **不单调**。多输入不仅掩盖漏检，还能主动制造改判。

---

## 4 可区分通过方案（≥2 方案 + 改动量 + 破坏性 + 判据 + 可粘贴片段）

### 4.1 复核 `partial` 的硬约束（必须先讲，否则方案会重犯）

复核人 `_mev_step5_out.txt:8-15,24-36` 实跑（`_mev_step5.py` 用 `ast` 只读抽取撰写人原样 `PLAN_A/B/C`）：**撰写人原方案乙/丙（含被标「推荐」的丙）在「交付的双 needle 掩蔽 PASS」上仍报 `COVERAGE_GATE=PASS`，在字面 `NEEDLES=[N1]` 单针 FAIL 上仍报 `COVERAGE_GATE=PASS` / `PER_NEEDLE_SELFTEST={0:'PASS'}`**，而同一时刻未修改扫描器单跑 N1 是 `SELF_TEST=FAIL / EXIT=1`。`PLAN_C` 的 `PER_NEEDLE_SELFTEST` 是**误称**：`_me_design.py:159-160` 显示它只由语料独占行数推出，从不跑自检。根因：报告 §3(a) 判据②写「≥1 条负控落在该独占集」，复核人独立实算 6 条负控独占集为 `[0,1]`（`_mev_step5_out.txt:18-19`），按判据②本应 UNPROVEN/FAIL；实现的乙/丙门禁却是较弱的「|exclusive 语料行|>0 = 38/43」，且判据②在 k=1 时给 `[5]` 同样抓不出（`:20-22`）。`_me_faultinject_out.txt` 只验证「整根针全死」这一弱故障，未覆盖本案单针 FAIL。**故「三方案均能区分真通过与掩蔽通过」不成立 → verdict=partial，标 `unconfirmed`。**

本会话独立复核（`_me_auditcheck_out.txt` C5，`ast` 只读抽取 `PLAN_B/PLAN_C` 换成 `NEEDLES=[N1]` 实跑）：

```
PLAN_B with NEEDLES=[N1] : EXIT=0  | COVERAGE_GATE = PASS
PLAN_C with NEEDLES=[N1] : EXIT=0  | MASKED_LINES = 0 / 87 (0.0%)
                                   | COVERAGE_GATE = PASS
                                   | PER_NEEDLE_SELFTEST = {0: 'PASS'}
GROUND TRUTH: N1-alone scanner = EXIT=1 ; SELF_TEST = FAIL ; :22 got=<not-scanned>
```

与复核人一致。**结论**：唯一被复核确认能抓的核心 = **甲（逐 needle 独立跑自检 + `AND_k`）**；乙/丙必须重写，不能沿用「语料独占行数即门禁」，也不能把 `HITSET`/`EXCLUSIVE` 当门禁（它们只是**诊断量**）。

### 4.2 修正后的三方案（本会话实跑 `_me_auditcheck_plan2.py`，EXIT=0，`ALL_SCENARIOS_MATCH_EXPECTATION = True`）

**统一 GATE（三方案共用）**：`AGGREGATE = AND_k( REAL per-needle self-test )`，其中每根 needle k **单独**跑未修改扫描器，要求 `EXIT=0 AND 6 条负控逐条匹配 WANT`；`HITSET / MASKED_LINES / EXCLUSIVE(k) / EXCLUSIVE_CONTROLS(k)` 一律**只报告、不门禁**（避免复核人指出的 k=1 平凡通过 / 语料漂移误判）。`PER_NEEDLE_SELFTEST` 必须来自**真实 k 次运行**，不得由语料推断。

| 方案 | 做法 | 改动量（对 `_rs_carrier_scan.py`） | 破坏性（对既有输出格式） |
|---|---|---|---|
| **甲'（推荐、零侵入）** | 逐 needle 独立跑自检，k 次完整扫描各出 `EXIT/SELF_TEST/6-controls`，`AGGREGATE=AND_k` | **0 行**（外部新外壳 ~15–25 行，本写域 `_me_auditcheck_plan2.py:plan_a`） | **完全不破坏**：每次输出仍是原格式，只多一层汇总；既有 `_fix_*.txt` 解析不变 |
| **乙'** | 同上，但把门禁写成「逐针负控表」：每根单独 6 条 `want/got` 逐条比对，任一 mismatch 即 FAIL | 0 行（外部预计算）或内嵌 ~20–30 行 | **弱破坏**：新增 `PER_NEEDLE` 行，A–E 段不变 |
| **丙'（溯源台账）** | 一次扫描补 `hits=[命中针下标]`，打印 `HITSET` 直方图 + `MASKED_LINES` + **REAL** `PER_NEEDLE_SELFTEST`（由 k 次独立自检得出），`PASS` 仅在 `AND_k` 成立时给出 | ~30–50 行（`:238` 补 hits、`:282` 多打一行、新增 F 段、`:324` 把 AND 并入 ok） | **中等破坏**：A 段每 carrier 多一行 `hits=`、新增 F 段；`SELF_TEST` 语义扩为「负控全过 ∧ 逐针自检全过」，旧 PASS 可能变 FAIL（这正是目的） |

三者都**不需改 `:165/:229` 判定逻辑本身**。数量级：甲 10 行级（零侵入）、乙 10–30 行级、丙 30–50 行级。

**四场景验证矩阵**（`_me_auditcheck_plan2_out.txt`，未修改扫描器，`scanned files=647` 为当前语料）：

| 场景 | needles | 期望 | 甲' | 乙' | 丙' | 关键输出 |
|---|---|---|---|---|---|---|
| S1 交付的双针掩蔽 PASS | `[N1,N2]` | FAIL | **FAIL** | **FAIL** | **FAIL** | 逐针 `SELF_TEST=[FAIL,PASS]`，`PER_NEEDLE_SELFTEST={0:'FAIL',1:'PASS'}` |
| S2 字面单针 FAIL | `[N1]` | FAIL | **FAIL** | **FAIL** | **FAIL** | `:22 got=<not-scanned>` |
| S3 真通过 | `["只能判","不能定位当年"]` | PASS | **PASS** | **PASS** | **PASS** | 两根各自 `EXIT=0 SELF_TEST=PASS 6/6`，`AND_k=True` |
| S4 坏针注入 | `["不能定位当年", 哨兵]` | FAIL | **FAIL** | **FAIL** | **FAIL** | 哨兵单跑 `EXIT=1 SELF_TEST=FAIL` |

`ALL_SCENARIOS_MATCH_EXPECTATION = True`（4/4）。**这才是「可区分」**：既能拒绝被掩蔽的 PASS（S1/S2/S4），也能放过真通过（S3）。S3 的 `EXCLUSIVE_CONTROLS=[0,0]` 却仍判 PASS，正说明「独占负控」不该当硬门禁——复核人已证它在 k=1 平凡通过、且本案 N1 为 0 时会误伤真通过。

### 4.3 掩蔽检测判据（从输出直接算出，本会话 CUT 口径）

下列为**判据公式/记号**（非可运行 Python，故用 text 围栏；可粘贴代码在 §4.4）：

```text
# 判据（本件审定版；HITSET/EXCLUSIVE 为诊断量，AND_k 才是门禁）
EXCLUSIVE(k)       = |{ line : hits(line) == {k} }|        # 独占语料行 = 38 / 43
MASKED_LINES       = |{ line : |hits(line)| >= 2 }| = 41   # 41/122 = 33.6%
MASKED_NEEDLES     = |{ k : EXCLUSIVE(k) == 0 }|    = 0
EXCLUSIVE_CONTROLS = [0, 1]   # 6 条负控的逐针独占数（本会话 C4 实算）
AGGREGATE          = AND_k( per_needle_SELF_TEST_k )       # = FAIL（N1 单跑 FAIL）
DISTINGUISHABLE_PASS = (AGGREGATE == PASS) AND (SELF_TEST == PASS) AND (每针 6/6 逐条匹配)
```

代入交付口径：**`DISTINGUISHABLE_PASS = FALSE`**——现行 `SELF_TEST` 不是由 `AND_k` 得出（`_me_design_out.txt:31-35`：E 段零 per-needle 行、零 hit-set 字段，「有几根被掩蔽」**UNKNOWABLE**，不是 0 也不是 1，是未报告）。**结果碰巧对（N1 在别处确实命中 79 行），这次 PASS 依然不可信。** 本会话当前语料下同一判据给 `MASKED_LINES=43/136`、`EXCLUSIVE_CONTROLS=[0,1]`（`_me_auditcheck_plan2_out.txt` 末段），结论不变。

### 4.4 可粘贴片段（方案甲' 核心，直接可跑；完整三方案见 `_me_auditcheck_plan2.py`）

```python
# 甲'：逐 needle 独立跑自检 + AND_k + 坏针注入。零改动上游脚本。
import subprocess, sys
SCANNER = r"D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py"
NEEDLES = ["只能判「不可复现」", "不能定位当年错误步骤"]
WANTS   = ["ASSERTION"] * 4 + ["REFUTING_QUOTE", "ASSERTION"]
CONTROLS = [
    ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123),
    ("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25),
    ("ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 196),
    ("ledger_bound_20261109/_lb_BOUND_VOLUME.md", 129),
    ("s604_verdict_entry_20261109/_ve_DRAFT_S609.md", 22),
    ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215),
]
def one(n):
    cmd = [sys.executable, "-I", "-X", "utf8", SCANNER,
           "--needle", n, "--include-refuting", "--max-depth", "2", "--ext", ".md"]
    cp = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    ls = cp.stdout.splitlines()
    st = next((l.split("=",1)[1].strip() for l in ls if l.startswith("SELF_TEST")), "<missing>")
    got = []
    for rel, no in CONTROLS:                       # 逐条负控比对，不只看总布尔
        key = "%s:%d want=" % (rel, no)
        L = next((l for l in ls if key in l), "")
        got.append(L.split("got=")[-1].strip() if "got=" in L else "<missing>")
    ok6 = all(g == w for g, w in zip(got, WANTS))
    return cp.returncode, st, ok6
rows = [(n, *one(n)) for n in NEEDLES]
for n, ec, st, ok6 in rows:
    print("NEEDLE %-24r EXIT=%d SELF_TEST=%-4s controls6=%s" % (n, ec, st, ok6))
AGGREGATE = all(ec == 0 and st == "PASS" and ok6 for _, ec, st, ok6 in rows)
print("AGGREGATE = %s  (AND_k over %d REAL per-needle self-tests)" %
      ("PASS" if AGGREGATE else "FAIL", len(rows)))
print("DISTINGUISHABLE_PASS = %s" % AGGREGATE)
sys.exit(0 if AGGREGATE else 1)
# 代入 N1/N2 => AGGREGATE=FAIL（N1 SELF_TEST=FAIL, :22 <not-scanned>）
# 代入 ["只能判","不能定位当年"] => AGGREGATE=PASS（真通过）
# 把 N1 换成保证零命中的哨兵 => AGGREGATE=FAIL（坏针被捕获）
```

方案丙' 的溯源核心（把 `hits` 补进每个 carrier 后打印，**仅诊断，不门禁**）：

```python
from collections import Counter
NEEDLES = ["只能判「不可复现」", "不能定位当年错误步骤"]
pat, excl, total = Counter(), Counter(), 0
for rel, txt in corpus():                 # 与扫描器同口径 (文件, 行) 迭代
    for L in txt.splitlines():
        hs = tuple(i for i, n in enumerate(NEEDLES) if n in L)
        if not hs: continue
        total += 1; pat[hs] += 1
        if len(hs) == 1: excl[hs[0]] += 1
print("HITSET", dict(pat))                          # {(0,):38,(0,1):41,(1,):43}
print("EXCLUSIVE", [excl[k] for k in range(len(NEEDLES))])   # [38,43]
print("MASKED_LINES = %d / %d" % (total-sum(excl.values()), total))  # 41/122
print("MASKED_NEEDLES = %d" % sum(1 for k in range(len(NEEDLES)) if not excl[k]))
# 注意：PER_NEEDLE_SELFTEST 必须来自甲' 的 k 次真实自检，不能用本段推断
```

**验证**：上述甲' 片段逻辑即 `_me_auditcheck_plan2.py:plan_a/gate`，本会话实跑输出 `_me_auditcheck_plan2_out.txt` S1–S4 四行；撰写人原片段在 `_me_design.py:PLAN_A/B/C`（**乙/丙已被复核判 partial，勿直接沿用**）。

---

## 5 全库同类风险

### 5.1 搜索命令与结果（如实申报「有界」，不冒充全库）

**撰写人原搜索**（直读在盘输出，非本件本次实跑）：`python -I -X utf8 "…/_me_search_git.py" > "…/_me_search_stdout.txt"` → `_me_search_out.txt`（819 行）。三条正则见 `_me_search_out.txt:7-9`。范围 `git ls-files`(3293) + `lead/` 深度≤3 未跟踪：`universe=5847`、`scanned=4962`、A=**11** / B=**194** / C=**130** / D=**492**（`:11-17,27,223,326`）。`:4-6` 已如实申报 `lead/o1prime_reach_20261109/_o1_tmp/long_B3_longpath/` 超长路径树停滞、非无界全库走查。**但摘要与 §6:322 仍称「全库」，复核人 `_mev_search_out.txt:1-9,19-26` 判为措辞夸大。**

**复核人更广有界扫描**（直读 `_mev_search_out.txt`，depth≤6 全仓）：`31418` 路径 / `19616` 实读 / A=**54** / B=**795** / C=**669** / D=**1769**。

**本会话独立更广有界扫描**（实跑命令 5，`_me_auditcheck_search.py`，输出 `_me_auditcheck_search_out.txt`）：

```
git ls-files entries = 3293 ; unique tracked paths = 3293
  LONG-PATH SKIP (len=278, depth=8): lead/o1prime_reach_20261109/_o1_tmp/long_B3_longpath/dddd…/dddd…
bounded untracked sweep (whole repo, depth<=8, long-path guard 240) added = 88066
skipped: depth-cap dirs=2458 ; long-path dirs=1 ; excluded-name dirs=485
universe paths = 91359
scanned text files = 52108
A (CLI action=append / needle-like defs) = 65
B (any()/min() over multiple inputs) = 1436
C (>=2 needle-like flags on one line) = 724
D (files mentioning self-test/negative control) = 4110
elapsed = 244.3 s
```

**结论**：撰写人的 11/194/130/492 是**下界**，不是全库总量；本会话 65/1436/724/4110 亦为**有界扫描**（depth≤8、路径长≤240、跳过 `.git/.mimosa/.tmp/__pycache__/node_modules`、1 个超长路径树被显式跳过并打印），**仍非无界全库**，且 A/B/C/D 是**正则命中计数**、不是逐文件执行审计。逐脚本风险只对下表直读/实跑过的对象给判断，其余一律**未验**。

### 5.2 逐脚本风险清单（源码 `file:line` + 实跑）

| 对象 | 行 | 形态 | 风险 | 依据（本会话直读/实跑） |
|---|---|---|---|---|
| `lead/refsync_scope_20261109/_rs_carrier_scan.py` | `:165/:229/:238-239/:327-331/:324/:346/:349` | 双 needle 并集 + 1 布尔自检 | **已实证 HIGH** | 本会话 C2 坏针仍 `EXIT=0/SELF_TEST=PASS`；§2.4 |
| `lead/d27_ruling_20261106/check_d27.py` | `:81-88,:100` | `for (num,title,keywords)` 第 6 项 `("外推","卡顿不存在")` 二选一 OR：`if not any(keyword in body for body in bodies… for keyword in keywords)` | **HIGH 同类**：任一词失效，另一词命中即 `PASS` | 本会话直读 `check_d27.py:81-88` |
| `lead/d29_ruling_20261106/check_d29.py` | `:76-89,:105` | `require_all=False` 时 `any(word in body for word in words)`，外层再 `if not any(matches)`（双层 OR）；词表 `("互斥","前提")` | **HIGH 同类** | 本会话直读 `check_d29.py:76-89`；最小复现见下 |
| `lead/d30_ruling_20261106/check_d30.py` | `:76-89,:105` | 与 d29 同构，词表 `("93.98","误报率")` | **HIGH 同类** | 本会话直读 `check_d30.py:76-89` |
| `lead/gate_pipeline_20261109/_gp_regression.py` | `:137` | `return "CATCH" if any(t in text for t in toks) else "PASS"`（naive 基线） | **MEDIUM**：多 token 并集，坏 token 无感；但它是**被比较的基线**，`:139-145` 另有 r10/r12/n13/chain 对照 | 本会话直读 `_gp_regression.py:134-147` |
| `lead/gate_fp7_20261108/_g7_predicates.py` | `:98,:101` | `marked = in_span and any(mk in span for mk in SELF_MARKERS)` | **MEDIUM**：多 marker 并集判「自指标记」，坏 marker 被其它掩盖 | 本会话直读 `_g7_predicates.py:94-104` |
| `lead/gate_n13_20261109/_n13v_independent.py` | `:69,:73,:83-84,:91,:103,:109` | 6 组多 token `any()` 组合守卫（`TOKENS/NEG/SUBJ/SEARCH/TOC/ACTION`） | **MEDIUM**：同类 OR 掩盖，组合后语义随位置变 | 本会话直读 `_n13v_independent.py:66-112` |
| `lead/gate_v1v2_20261109/_v12_rule.py` | `:116-140` | 11 处 `any(k in U for k in PROHIBIT/H1_QUESTION/H2_QUOTE/…)` | **MEDIUM–HIGH**：词表最长，最易有死词 | 本会话直读 `_v12_rule.py:114-142`；**未逐词做存活率实跑 → 未验** |
| `tools/verify_kit/boundary_scan.py` | `:104,:113,:143-151` | `--wordlist` 多 token；`for tok, rx in pats` 逐 token 记录 `HIT … token=%s` | **LOW（相对最好）**：**有 per-token 溯源**（`:145,:149` 打印 `tok`）+ `--no-self-exclude` 正控开关（`:108`）⇒ 坏 token 可从「某 token 零 HIT」直接看出；但**无 per-token 覆盖度门禁**，死串仍不自动 FAIL | 本会话直读 `boundary_scan.py:100-116,140-153` |
| `tools/verify_kit/snapshot.py` | `:35-37,:63` | `--exclude action=append` + `any(c in pat for c in "*?[")` | **LOW–MEDIUM**：多 pattern 并集（跳过更多文件），坏 pattern 让快照少排除文件但仍成功；`:150` `snapshot: %d files` 可间接察觉 | 本会话直读 `snapshot.py:33-39,60-66` |
| `ra2opt/cli.py` | `:78,:102` | `--exe action=append` | **LOW**：多 exe 路径，非自检/非判定门禁 | `_me_search_out.txt:17-18` |
| `tools/atlas_apply_patches.py` | `:140` | 单个 `--pattern` 默认 `R*.md` | **LOW**：非多输入 | `_me_search_out.txt:20` |
| 本会话新发现的 CLI 多输入（A 段新增） | `out/re_work/asm_fix/probe.py:248`(`--pat append`)、`out/re_work/qc/w3_20261001/scripts/m8_e8_scan.py:95`(`--exe append`「可重复；每个都扫一遍」)、`out/re_work/work_chain/continue_20261003/lead/gate_seg/run_case.py:33-34`(`--forbid/--require append`)、`…/ddraw_id/scan_strings.py:92`(`--needles` 逗号串)、`…/qc152_launch_sites/qc152_launch_scan.py:166`(`--root append`)、`out/re_work/work_chain/exp001/step5_review/audit_pe_independent.py:577`(`--va append`) 等 | 各类可重复参数 | **未验**：仅正则命中，未读源码/未实跑，**不补造风险等级** | `_me_auditcheck_search_out.txt` A 段全 65 条 |

**最小复现（本会话 `_me_auditcheck_out.txt` C6，纯 python -I -X utf8）**：
```
words=('93.98', '误报率') body='本报告 93.98 与误报率均已复核' any=True
after DELETING '误报率': body='本报告 93.98 与均已复核' any=True  <-- dead keyword invisible
```
（复核人 `_mev_final_out.txt:10-14` 独立同结论。）即 `check_d29/d30` 的 OR 词表里删掉一个词，`any` 仍 True ⇒ **坏词不可见**，与本例「坏针仍 PASS」同构。

### 5.3 通用形态（抽象）

> 设测试有 k 个输入（needle / pattern / keyword / token / case），内部用**存在量词**把它们合成一个布尔：
> `covered(x) = ∃i: match(input_i, x)`，而自检把 `∀ sample s: covered(s)` 压成**单一比特** `PASS`。
> 于是 `PASS` 的所有可能世界中，包含「`input_1` 完全失效、但每个 sample 都被某个 `input_{j≠1}` 命中」这一世界，且与「全部 k 根正常」**观测等价**。
> 缺陷不在 `match` 实现，而在**从 k 个输入到 1 个布尔的有损压缩**：证明目标（∀i 有效）强于观测量（∃i 命中），且未保留 `i` 的溯源。
> 两个附加形态：① **min/argmin 位置依赖**——若判定还依赖 `argmin_i pos_i`（`_rs_carrier_scan.py:165`），加输入会改变 `argmin`，使「已扫到」集合单调而「已判对」集合**不单调**（反向掩蔽，§3.3）；② **无独占见证 / 独占见证被误用**——`exclusive(i)=U_i \ ∪_{j≠i}U_j` 可作**诊断**，但复核人已证把「≥1 条独占负控」当**硬门禁**会在 k=1 平凡通过、并在真通过场景误伤（`_mev_step5_out.txt:20-22`；本会话 S3 `EXCLUSIVE_CONTROLS=[0,0]` 却两针都 6/6 PASS）。**唯一可靠的门禁是 `AND_k` 真实逐输入自检。**

### 5.4 一般性防掩蔽设计原则

1. **逐输入出结果**：输出 k 行 `input_i: PASS/FAIL`（含逐条负控 `want/got`），总判定 = `AND_k`；禁止把并集结果直接叫 `PASS`。
2. **门禁与诊断分离**：`EXCLUSIVE(k)` / `MASKED_LINES` / `MASKED_NEEDLES` / `HITSET` 只用于量化，**不得**替代 `AND_k` 门禁（复核 `partial` 的直接教训）。
3. **保留溯源**：每个命中记录 `hits=[...]`，使「并集覆盖」与「逐根覆盖」可分开计算。
4. **坏输入注入自检**：每根依次换成保证零命中的哨兵，要求 `AGGREGATE` 变 FAIL（本会话 S4 实证捕获）；现行脚本通不过（`_me_broken_needle_out.txt` 仍 PASS）。
5. **OR 改逐项报告**：词表型检查（`check_d27/d29/d30`）把 `any(word…)` 改为逐词打印命中数，`require_all=False` 也要打印每词存活状态。
6. **单调性声明**：明确区分「scanned 单调」与「role/needs_fix 非单调」；对依赖 `min(pos)` 的判定，改为**每根 needle 独立求角色**再按明确规则合并，而不是先取 `min` 再判一次。
7. **固定语料指纹**：报 PASS/FAIL 绑定语料 SHA256 + 文件数，防并行写入让 `scanned files` 漂移被误读为「测试变好」（本会话亲历 637→638→646）。
8. **口径逐字一致**：命令与登记口径（含每个 `--needle/--ext/--max-depth/--include-refuting`）逐字核对，不一致即标「非登记口径」。

---

## 6 复核回件 + 事件定性 + 报 PASS 前清单 + 未验项

### 6.1 复核 verdict 如实登记（标 unconfirmed）

```
复核 verdict = partial  →  本件整体标注 unconfirmed
```

复核人结论（`_mev_step5_out.txt:24-36`、`_mev_final_out.txt:16-29`、`_mev_search_out.txt:19-26`、`_mev_forensics_out.txt:31-35`）：

- **confirmed 部分**：① 八件指纹开头+收尾各 `hashlib` 8/8 一致；③ 四道门机制逐行吻合、坏针注入仍 `EXIT=0/SELF_TEST=PASS`；④ 反向掩蔽真实 `:22` `REFUTING_QUOTE→ANALYSIS_MENTION`、合成 `ASSERTION→QUOTED`、真实语料 flip=0 均独立复现；⑦ 上一轮 PASS 判「不可信」与编排方单针 FAIL「口径偏差」自评诚实到位；⑧ 未改既有脚本、未 commit/push、写域仅 `_me_`/`_mev_` 前缀（本件新增 `_me_auditcheck_*` 同域同纪律）。
- **partial 的决定性缺陷**：把单 needle FAIL 场景套进三方案，**只有甲抓得出**；乙与被标「推荐」的丙在掩蔽 PASS 与字面单针 FAIL 上都报 `COVERAGE_GATE=PASS`，`PLAN_C` 的 `PER_NEEDLE_SELFTEST` 是误称（`_me_design.py:159-160` 只由语料独占行数推出）。`_me_faultinject_out.txt` 只覆盖「整根针全死」弱故障。
- **次要问题**：①「全库」系受限扫描（已如实申报，但摘要/§6 措辞夸大）——本会话更广有界扫描证实清单是下界；② 语料 637/79/122 → 643/87/136 属已如实登记的漂移，**不报 refuted**；③ 撰写人自己的「双针正式口径」比 `REFSYNC_SCOPE_FIX.md:251` 多传 `--include-refuting`（仅影响 C 段展开，不改五数字），该对称口径差未标注。
- **本件的处置**：§4 已按复核意见**重写乙/丙**、把 `AND_k` 设为唯一门禁、`EXCLUSIVE_*` 降为诊断，并实跑 4 场景 4/4 匹配；但**这不改变复核 verdict**——原交付件 `_me_REPORT.md` 的结论仍为 `partial` / `unconfirmed`，本件不冒充「已把复核翻案」。

### 6.2 复核回件绑定行（格式固定）

被核对象 SHA256 = 9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57，字节数 = 16053

（被核对象 = `lead/refsync_scope_20261109/_rs_carrier_scan.py`；本会话开头 `python -I -X utf8 -c "…hashlib…"` 与 `_me_auditcheck_out.txt` C1 各复算一次，均 8/8 一致；复核人 `_mev_final_out.txt:17-25` 收尾再 8/8。）

### 6.3 事件定性

**`SELF_TEST = PASS` 可信度 = 不可信（not `unconfirmed` 的「待定」，是明确判废）**。依据（本会话实跑 + 直读）：
1. 坏针配置 `--needle N2 --needle TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ` 仍 `EXIT=0 / SELF_TEST = PASS`（`_me_auditcheck_out.txt` C2 `[broken]`；`_me_broken_needle_out.txt:546-552`）⇒ 该 PASS 与「N1 是否工作」逻辑无关。
2. 6 条负控 5 条 `{N1,N2}`、`:22` 为 `{N2}`（本会话 C4）⇒ N2 一根即可 6/6（`_me_n2only_out.txt:546-552`）。
3. N1 的客观缺陷（直角/弯引号不归一）存在：单 needle 下 `:22 got=<not-scanned>`、79 vs 122 漏 43 行。
4. 【铁律】：被掩蔽的通过即使结果碰巧正确（N1 别处命中 79 行）也**必须标不可信**。

**是否需加注 = 建议加注，本任务未执行**（`REFSYNC_SCOPE_FIX.md` 属绝对只读件）：
- `REFSYNC_SCOPE_FIX.md:243`（R6 描述）、`:251`（登记双 needle 命令 + `SELF_TEST = PASS` 6/6）、`:252-253`（另两条 PASS）建议由台账所有者追加限定：「本 PASS 系 N1∪N2 并集口径，不构成逐 needle 有效性证据；`:22` 仅由第二 needle 命中；详见 `lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md`」。在盘 `_fix_d2_out.txt` 等建议加「口径限定」，不改写原数字。
- 本会话/复核人直读确认：`REFSYNC_SCOPE_FIX.md` 全文无「掩盖/掩蔽/假 PASS/不可信」（`_mev_final_out.txt:2-6`）；而 `_nn_REPORT.md:90-100,365,400-402` 与 `NEEDLE_NORMALIZATION.md:91,293,364,393` **已登记「掩盖效应」并建议「每个 needle 单独跑一次自检」**（`:365` / `:364` 原文），`_nn_REPORT.md:402` 自认「本次 FAIL 之所以暴露，是编排方用单 needle 重跑了负控自检」——即下一轮已发现，但**上一轮交付件本身未加注**。建议补的正是这个缺口。

**方法论问题 + 编排方只跑单 needle 的偏差（如实评估）**：
- 暴露的方法论问题：把「多输入并集 + 单一布尔自检」当成「每个输入都有效」的证明；负控样本未做**逐输入覆盖度**设计；PASS 未绑定语料指纹；命令口径（单 vs 双 needle）与交付登记不一致却未标注。
- 编排方「只跑单 needle 就报 FAIL」**算另一种偏差，但性质不同、不抵消原问题**：`REFSYNC_SCOPE_FIX.md:251` 登记正式命令是**双 needle**，编排方实跑**单 needle**（`--needle "只能判「不可复现」" --include-refuting`），差一个 `--needle`。按「报 FAIL 前须确认与登记口径一致」，该 FAIL **不能直接当交付件的验收结论**，应写「在单 needle 口径下 FAIL」。它**不是掩蔽**（没用另一输入掩盖失败），是**反向的口径错配**；但**碰巧是唯一发现通道**（`_nn_REPORT.md:402`）。如实评价：**结论方向对（N1 确有漏检），论证路径不严谨（口径与登记不符）**；若无本件的双/单对照 + 坏针注入，单靠那一条 FAIL 无法区分「N1 坏了」与「我少传了一个参数」。反过来说，「跑错口径反而暴露掩蔽」本身证明**正式口径的自检设计失效**——两边都有缺陷，类型不同，不护同僚也不过度自责。
- 另如实登记：撰写人自己的「双针正式口径」也比 `:251` 多传 `--include-refuting`（复核人次要问题③），仅影响 C 段展开，不改五数字；未标注，属同类口径差。

### 6.4 报 PASS/FAIL 前清单（必做，逐条可执行）

1. **核对命令与登记口径逐字一致**（每个 `--needle / --pattern / --ext / --max-depth / --include-refuting`），不一致即标「非登记口径」，不得据此下交付结论。
2. **绑定**被核对象 SHA256 + 字节数 + 语料文件数（本件 §6.2 格式），PASS/FAIL 与指纹同发。
3. **逐 needle 自检**：k 个输入出 k 个 `PASS/FAIL`（含 6 条 `want/got` 逐条比对），总判定 = `AND_k`；禁止只报一个 `SELF_TEST`。
4. **门禁/诊断分离**：`EXCLUSIVE(k)`、`EXCLUSIVE_CONTROLS(k)`、`MASKED_LINES`、`MASKED_NEEDLES`、`HITSET` 只报告；**不得**用「语料独占行>0」或「独占负控≥1」替代 `AND_k`（复核 `partial` 教训）。
5. **打印命中溯源**：`hits=[...]` / `HITSET` 直方图，算出 `MASKED_LINES` 与 `MASKED_NEEDLES`。
6. **坏针注入**：每根依次换保证零命中的哨兵，确认 `AGGREGATE` 变 FAIL；若注入坏针仍 PASS，原 PASS 作废（本例实证作废）。
7. **PASS/FAIL 双向对照**：既报正式口径，也报去掉一根输入的对照，差异可解释（本例 79 vs 122，差 43 = `|only2|`）。
8. **stdout 原文落盘并算 sha256**（本件 4 份 `_me_auditcheck_*_out.txt` 已做），正文只引「命令 + 输出文件:行」。
9. **单调性声明**：依赖 `min(pos)`/argmin 时额外跑「多加一根输入」对照，确认角色未改判（本例 `:22` 实测被改判为 `ANALYSIS_MENTION`）。
10. **未验项显式写「未验」**：搜不全、跑不动、没实跑的对象一律标注，不用 plausible 值填空。

### 6.5 未验项（不补造）

- **全库非全**：撰写人 5847/4962、复核人 31418/19616、本会话 91359/52108 三次均为**有界扫描**（各自深度/长路径/跳过目录不同）；超长路径树 `lead/o1prime_reach_20261109/_o1_tmp/long_B3_longpath/` 未无界下钻（本会话显式跳过并打印 `_me_auditcheck_search_out.txt`）。A/B/C/D 是正则计数，**不是逐文件执行审计**。
- **D 段 4110 个提及自检/负控的文件、B 段 1436 处 `any()/min()` 未逐个实跑**；§5.2 表内只对直读源码或做了最小复现的对象给判断，A 段本会话新发现的 `out/re_work/...` 多输入 CLI 一律**未验**，不补造风险等级。
- **`_v12_rule.py` 词表存活率、其它 HIGH/MEDIUM 脚本的坏针注入**：本次**未逐词/逐脚本实跑**，标未验。
- **真实语料反向掩蔽的 `ASSERTION→非ASSERTION` 翻转**：构造验证成立，真实语料 flip=0（`_me_reverse_assertion_out.txt:3`），**未实证**，不夸大。
- **撰写人 `_me_repro.py`/`_me_analyze.py`/`_me_design.py`/`_me_search_git.py`/`_me_reverse*.py` 本件未重跑**，其在盘输出按「文件:行」引用；本件自己实跑的是 §1 命令 1–6 及 `_me_auditcheck_*` 系列。
- **台账加注未执行**（§6.3 仅建议）；**未 commit / 未 push**（`git status --short lead/masking_effect_20261109/` = `??`，未跟踪）。
- **零真机 / 零采样代码**：本会话未启动任何真机进程、未写任何采样/注入代码（已执行，非未验）。

---

### 附：必现要素自检

掩蔽 ✓（§2.5/§3） · 单 needle ✓（§2.2/§3.1） · 双 needle ✓（§2.2/§3.1） · `SELF_TEST` ✓（§2.2/§6.3） · `not-scanned` ✓（§2.2/§2.4） · 四道门 ✓（§2.4） · 反向掩蔽 ✓（§3.3） · 可区分 ✓（§4.2 四场景 4/4） · 逐 needle 自检 ✓（§4.2/§4.4） · 掩蔽检测判据 ✓（§4.3） · 通用形态 ✓（§5.3） · 报 PASS 前清单 ✓（§6.4） · 未验 ✓（§6.5） · 三个数字 **79 / 84 / 122** ✓（§3.1） · 可粘贴片段 ✓（§4.4） · 复核 verdict `partial` → `unconfirmed` ✓（§6.1） · 绑定行 ✓（§6.2）。
