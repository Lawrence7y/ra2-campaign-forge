# R33E_MERGE.md — J4 等价类判据并入报告

日期：2026-11-09　写域：`lead/r33e_merge_20261109/`（唯一写域）
交付实现：`lead/r33e_merge_20261109/_re_linked.py`（新件；SHA256 = `7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52`，19481 B，本会话 `hashlib` 全字节实算）
本报告所有「实读」= 本会话工具读到的 `文件:行`；所有「实跑」= 本会话执行 `python -I -B -X utf8` 命令后所见输出（`-B` 防只读目录 `__pycache__`）。上游【并入】【复核】材料由编排方随任务给出，本报告引用其内容时标注「任务给定材料」。

## 1 目的与边界

**目的**：把 J4「同文档声明背书级等价类」判据并入同文档指纹-路径联查谓词，产出**可用实现** `lead/r33e_merge_20261109/_re_linked.py`。原实现在「≥2 个不同现盘文件同 hash」时无条件 `multi`（放弃采集）；J4 允许在且仅在**三条件同时满足**时改判 `merged`（同一内容的声明背书副本群），其余形态零改动。

**边界（铁律，任务给定 + 本会话核实）**：

1. **未改 `_sl_link.py`** —— 必现要素「未改 _sl_link.py」在此明确声明：`lead/samedoc_link_20261109/_sl_link.py` 及 `lead/equiv_class_20261109/`、`lead/f2d_rootcause_20261109/`、`lead/r11_f2_fix_20261109/`、两件台账全程绝对只读。本会话前后两次 `hashlib` 十件全字节复算均 `10/10 ALL_MATCH`，会话末 `ALL_MATCH_POST_RUN = True`；`lead/equiv_class_20261109/__pycache__` 与写域 `__pycache__` 均 `ABSENT`（实跑命令见 §2、§5）。
2. **封闭集禁扩**：溯源声明词只有 `复制自 | 复制为 | COPY_IDENTICAL\s*=\s*True`（`_re_linked.py:81`，与 `_eq_proto.py:47` 逐字符一致；`_eq_criteria.md:89` 的 `/.../` 同形）。**不得为提高闭合率扩词**，尤其禁收「逐字节同一/相同」等**纯等同词**——`_eq_proto.py:16-17` 与 `_eq_criteria.md:147` 实读明写理由；漏词只会漏闭合（安全方向）。
3. **零真机、零采样代码**：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存；无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。未 `commit`、未 `push`（`git log -1 --format='%H %s'` 实跑 = `26574589aa8401e8f3f2934680a1ea7109bafa2d GOAL-3T: 台账 §400→§508 与 D-07..D-11 裁决登记入账`，与会话开始一致）。
4. **只做同文档联查，不做全仓反查**（`_re_linked.py:46` 实读）；`problems` 恒为空列表，任何分支（含 `merged`）一律 warning 级（`_re_linked.py:47`、`:177-179`）。
5. **本报告不自行上线**：`merged` 是新增形态，尚未接入 `r11_scan_plus` 生产路径（适配需求见 §5）；`未验` 项见 §5 末。

## 2 上游指纹 + 两实现的分支定位与并入点

### 2.1 十件只读基线（本会话实跑）

命令：`python -I -X utf8 -c "import hashlib,os ..."`（对十件逐件 `hashlib.sha256(open(p,'rb').read()).hexdigest()` 与 `len(b)`），输出 `READONLY_BASELINE 10 / 10 ALL_MATCH= True`；重跑 `_re_fp_check.py` 亦输出十行 `OK ...` + `ALL_MATCH`，`EXIT=0`。

| # | 只读件（相对仓库根） | SHA256（编排方指纹，本会话实算全等） | 字节数 |
|--:|:--|:--|--:|
| 1 | `lead/samedoc_link_20261109/_sl_link.py` | `a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5` | 12475 |
| 2 | `lead/samedoc_link_20261109/SAMEDOC_LINK.md` | `7e55c03861ea5eeff0adf9c02f74e2286134af2c52e507eae2216921d5b9b340` | 27995 |
| 3 | `lead/samedoc_link_20261109/_sl_run10_out.json` | `ed031e01e90e004dab43552085f5f6e5b5d184e7d1efa6f5699d6f76b5da454c` | 36749 |
| 4 | `lead/equiv_class_20261109/_eq_criteria.md` | `30355f3764242e6ad684db8ccb5c11d20fd42a8ad24d3cbf0ae7f0640f0e9a64` | 19143 |
| 5 | `lead/equiv_class_20261109/_eq_proto.py` | `dcb01858955f9b236f0a430430f8172bd5539a82b0aeb7014932c42c4fda4458` | 7645 |
| 6 | `lead/equiv_class_20261109/_eq_proto_out.json` | `c5e19d798c46ee53e5fccafbb1e082ed38f22d1aaa508061d6e617c6d30959f7` | 7519 |
| 7 | `lead/f2d_rootcause_20261109/_f2d_ROOTCAUSE.md` | `d12efd856c0aebe5dc8a882cb7cbd486154c7bb8602028e83a6f3ef290668b05` | 21424 |
| 8 | `lead/r11_f2_fix_20261109/_f2_r11plus.py` | `83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75` | 15723 |
| 9 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 |
| 10 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 |

### 2.2 原实现 `_sl_link.py` 的分支定位（实读）

- `link()` 主入口与 `invalid_hex` 早退：`_sl_link.py:138-149`（`:146-149` 非 64 位 hex 直接 `return out`）。
- **unique**：`_sl_link.py:195-203`（`len(matches)==1` → `reverify` 单对象回验 + MATCH warning）。
- **multi**：`_sl_link.py:204-210`（`>=2` → 放弃采集、`anchors=matches[:max_detail]`、warning「唯一命中才采」）。
- **zero**：`_sl_link.py:211-220`（零命中 → 保留 R3-3b 警告）。
- `link_triple()` 契约：`_sl_link.py:224-238`（`problems` 恒 `[]`；`tier="SAMEDOC_LINK"` 仅 unique/multi；unique 才写 `path/verified_path/recomputed/bytes`）。
- 上游规则原文：`SAMEDOC_LINK.md:20` ★4「唯一命中才采」；`:21` warning 级；`:22` 未接回调用链。J4 是对 ★4 的**显式修订**（multi 不再无条件放弃），见 §5 适配第 6 条。

### 2.3 J4 原型 `eq_merge` 的定位（实读）

`lead/equiv_class_20261109/_eq_proto.py:50-92`，判据原文 `:10-17`，机器口径 `_eq_criteria.md:86-98` §5.1：

- **仅 multi 介入守卫**：`_eq_proto.py:52-53`（`res.get("verdict") != "multi"` 原样返回）；`:15` 与 `_eq_criteria.md:91` 明写 unique/zero 不介入。
- **封闭集**：`_eq_proto.py:47` `DECL_RE`；`:16-17` 排除纯等同词的 Q4 反例理由；`_eq_criteria.md:147` 禁扩。
- **条件 (i)**：`:63` `DECL_RE.search(ln)` 命中溯源声明行。
- **条件 (ii)**：`:56-60` 由成员 token 行号建覆盖图，`:65` `len(ck) >= 2`（同一声明行同现 ≥2 成员）。
- **条件 (iii)**：`:71-74` 命中行覆盖并集 `group != kset` 则维持 multi（全或无，不部分合并）。
- 改判：`:78-91` `verdict="merged"`、`eq{members,decl_lines,decl_hits}`、新 warning（`:89` 已含「未做单一对象主张（path=None）」）。
- `_eq_criteria.md:94-97` 的伪代码 `:96` 明写 `tier="SAMEDOC_LINK_EQ", path=None, match=True, members=[…]`；`:143` 明写「eq_merge 未并入 `_sl_link.py` 实件」，即本任务要补的缺口。

### 2.4 并入点（本会话实跑结构核验）

`_re_linked.py` = `_sl_link.py` 逐行拷贝 + 3 处并入改动（`_re_linked.py:4-14` 模块 docstring 自述）。

本会话实跑 `python -I -B -X utf8 D:\Project\ra2-campaign-forge\lead\r33e_merge_20261109\_re_struct_diff.py` → `STRUCT_OK: True`、`HUNKS:` 11 个（`replace/insert` 全在白名单：模块 docstring、`link()` docstring、`link_triple()` docstring、DECL_RE 插入、J4 块插入、tier 三元、merged elif、usage 行）、`GUARD: a4ae4dc1d87d / 12475 | RE: 7ca339c6beb7 / 19481`、`EXIT=0`。11 hunk 中关键三项：

| 并入点 | 原件位置 | 并入版位置 | 内容 |
|:--|:--|:--|:--|
| (1) 封闭集 | 原件 `:48` 后插入 | `_re_linked.py:77-81` | `DECL_RE`（与 `_eq_proto.py:47` 逐字符一致） |
| (2) J4 块 | 原 multi warning 赋值 `:210` 之后、`:211` 的 `else` 之前 | `_re_linked.py:246-289` | 三条件判定 + `merged` 产出 |
| (3) triple 映射 | `:229` tier 三元 + `:236` 后插入 | `_re_linked.py:311-312`、`:320-329` | `SAMEDOC_LINK_EQ` 与 merged rec |

**绝不放进 unique / zero / invalid_hex**：J4 块位于 `elif len(matches) >= 2:` 分支内（`_re_linked.py:239-245` 原 multi 输出之后、`:290` 的 `else:` 之前）；`DECL_RE.search` 全文件仅 `:265` 一处，在 `:246-289` 内（任务给定【复核】② 独立 difflib 亦证实；本会话实读 `_re_linked.py:230-300` 同见）。

## 3 并入版实现（`_re_linked.py`）

### 3.1 结构与接口

- `link()` 返回 `verdict ∈ {unique, multi, merged, zero, invalid_hex}`（`_re_linked.py:171-176`）；`problems` 恒 `[]`（`:47`、`:177-179`）；`reverify` 只在 unique 写（`:234-235`），merged 时恒 `None`。
- 未触发 J4 的 multi：J4 块对 `out` **零改动**，保持原 multi 的 `verdict/anchors/warning`（`:246-249` 注释、`:270` 的 `if _decl_hits:` 与 `:274` 的 `if _group == _kset:` 双守卫）。
- `link_triple()`（`:303-331`）：`unique/multi/zero/invalid_hex` 的 rec 与原实现全等（本会话 `_rev_core.py` 92/92 中 `triple_eq=True` 逐条核实）；merged 走新增 `elif`（`:320-329`）。

### 3.2 J4 三条件的实现（逐行）

| 条件 | 实现 | 说明 |
|:--|:--|:--|
| (i) 封闭集命中 | `_re_linked.py:81` 定义 `DECL_RE`；`:264-265` 对 `text.splitlines()` 每行 `DECL_RE.search` | `:78-80` 注释禁扩；`:269` 记录命中行原文 `strip()` 全文（条3 实测 256 字，无 `[:160]` 截断） |
| (ii) ≥2 成员同现 | `:257-262` 由**全量 `matches`** 建 `_cov: 行号 → {成员 key}`；`:266-267` `len(_ck) >= 2` 才收 `_decl_hits` | token 行号沿用原实现 `rec["tokens"][].lines[:4]`（`:204-206`），同 `_eq_proto.py:56-60` 口径 |
| (iii) 全或无 | `:270-274` 取各命中行 `covers` 并集 `_group`，仅当 `_group == _kset`（`:257` 全体成员）才改判 | 部分覆盖 / 无声明行 / 无同现行 → 维持 multi 原样 |

与原型的一处**已披露分叉**（任务给定【复核】②-2，本会话 `_rev_edge25.py` 实跑 7/7）：原型 `eq_merge` 用 `res["anchors"]`（`_eq_proto.py:54`，≤12 成员），并入版用全量 `matches`（`:257-262`、`:280-281`）。25 成员夹具下原型语义保持 `multi`，并入版 `merged`（`members=25`、`anchors=12`、`decl_lines=[4..16]`）；方向是纪律 (c)「members 全列」的强化，非三条件理解变化。

### 3.3 `merged` 输出字段（本会话实跑形状）

直接导入并入版实跑条3（`python -I -B -X utf8 -c "...importlib... m.link(...)/m.link_triple(...)"`）输出：

```
MERGED_SHAPE = {"verdict": "merged", "problems": [], "reverify": null, "anchors_n": 2, "eq_keys": ["decl_hits", "decl_lines", "decl_vocab", "members", "rule"], "members_n": 2, "decl_lines": [13], "warning_has_path_none": true, "warning_has_ban": true}
TRIPLE_SHAPE = {"tier": "SAMEDOC_LINK_EQ", "match": true, "path": null, "keys": ["decl_lines", "declared", "match", "members", "path", "samedoc_link", "tier"], "members_n": 2, "decl_lines": [13]}
SINGLE_OBJECT_FIELDS = []
```

- `out["eq"]`（`:276-281`）= `{rule, decl_vocab, decl_lines, decl_hits[{line, covers, text}], members}`；`out["warning"]`（`:282-289`）含「未做单一对象主张（path=None）」「禁止由 merged 推导任何授权结论」并列出全部成员路径。
- `members` 格式 = `[{"path": <现盘解析绝对路径>, "sha": <64 位小写 hex 全量>, "bytes": <int>}, ...]`；`out["eq"]["members"]` 与 `rec["members"]` 同形，取**全量 `matches` 不截断**（`anchors` 仍按原实现 `max_detail=12` 截断显示）。
- `link_triple` 的 merged rec（`:326-329`）：`tier="SAMEDOC_LINK_EQ"`、`match=True`（仅指声明 hex 与全体成员现盘重算逐位一致）、`path=None`、`members` 全列、`decl_lines`；**不写** `verified_path` / `recomputed` / `bytes` / `reverify`（`:322-325` 注释）。

## 4 全量回归逐条表 + 四例 J4 验证

### 4.1 十条逐条回归（原版 vs 并入版，本会话亲自重跑）

命令：`python -I -B -X utf8 D:\Project\ra2-campaign-forge\lead\r33e_merge_20261109\_re_run10_diff.py`
输出逐条 10 行 + `SUMMARY: {"ten_counts": {"zero->zero": 1, "unique->unique": 8, "multi->merged": 1}, ... "unique_count_orig": 8, "unique_count_merged": 8, "zero_count_orig": 1, "zero_count_merged": 1, "multi_to_merged": ["t3"], "multi_kept_multi": [], "identical_rows": [12 行], "changed_rows": ["t3"]}`、`HISTORY: t1:zero|zero->zero ... t10:unique|unique->unique`、`ASSERTIONS: 20 / 20 passed`、`EXIT=0`。文档/行号/字节声明取自 `_re_run10_out.json` 的 `ten[]` 与 `history_cross_check[]`（本会话 `python -I -B -X utf8 -c` 打印）。

| 条 | 文档（相对 `lead/`）:行 | 声明字节数 | 原版→并入版 | 规范化 JSON 全等 |
|:--|:--|--:|:--|:--|
| t1 | `a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md:130` | 26435 | zero→zero | True |
| t2 | `b2b_isolated_20261107/INTEGRATION_REPORT.md:31` | — (`None`) | unique→unique | True |
| t3 | `b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md:5` | 412759 | **multi→merged**（members=2, decl=[13]） | **False（唯一预期变化）** |
| t4 | `bexec_n4_20261108/B_EXECUTION_SPEC.md:51` | 399508 | unique→unique | True |
| t5 | `bexec_n4_20261108/B_EXECUTION_SPEC.md:52` | 412759 | unique→unique | True |
| t6 | `bexec_n4_20261108/B_EXECUTION_SPEC.md:53` | 22136 | unique→unique | True |
| t7 | `bexec_n4_20261108/B_EXECUTION_SPEC.md:228` | 399508 | unique→unique | True |
| t8 | `bexec_n4_20261108/B_EXECUTION_SPEC.md:229` | 412759 | unique→unique | True |
| t9 | `bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md:28` | 399508 | unique→unique | True |
| t10 | `bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md:29` | 412759 | unique→unique | True |

**无退化结论**：unique 8→8、zero 1→1，唯一变化 t3 `multi→merged`；12 行（10 真件中除 t3 的 9 行 + `exA` unique / `exB` zero / `invalid_hex`）`identical=True`，`reverify`/`anchors`/`link_triple rec` 全等；`HISTORY` 与只读件 `_sl_run10_out.json` 十条历史 verdict 逐条一致。附加补充回归（本会话 `_re_parity_extra.py`，`21/21 passed`，EXIT=0）：unique 6/6、zero 3/3、invalid_hex 1/1 输出与 triple rec 全等且无 `eq` 键；**带声明行且同现 ≥2 token 的 unique/zero/invalid_hex 三正控制均不介入 J4**；原 `_sl_selftest.py` 8 个调用面双跑全等；15 成员夹具 `multi→merged` 时 `anchors=12` 而 `eq.members=15`（15 条不同路径、warning 列全 15 成员），证明 members 不截断。

三个独立复核脚本本会话亦全部重跑（命令同为 `python -I -B -X utf8` + 绝对路径）：`_rev_core.py` → `FINGERPRINTS: ALL_MATCH`、`92 / 92 passed`、EXIT=0；`_rev_cases.py` → 自建 36 B blob（`760e9b6c…`）、`69 / 69 passed`、`D1 WOULD_MERGE_IF_VOCAB_EXPANDED: True`、`E2 DISCIPLINES: reverify=None triple.path=None ... anchors=12 members=15`、EXIT=0；`_rev_edge25.py` → `ORIG: multi anchors=12` / `PROTO-REIMPL(anchors-limited): multi` / `IMPL(full matches): merged ... members=25 anchors=12`、`7 / 7 passed`、EXIT=0。

### 4.2 四例 J4 验证（本会话实跑 `_re_j4_cases.py`，`19/19 passed`，EXIT=0）

命令：`python -I -B -X utf8 D:\Project\ra2-campaign-forge\lead\r33e_merge_20261109\_re_j4_cases.py`；逐案明细取自 `_re_j4_out.json`（本会话 `python -I -B -X utf8 -c` 打印 `results` 字典）。

| 例 | 样本 | 原→并 | 实跑关键输出 | 判定依据 |
|:--|:--|:--|:--|:--|
| ① 条3 合并 | `_integ_INTEGRATION_REPORT.md:5` 真件（`ca23c116…` / 412759） | **multi→merged** | `decl=[13] members=2`；`kset_n=2`、`cover_ge2_lines=[13]`、`covers_all=True`；`decl_hits[0].text` 256 字全文（本会话实测 `ITEM3_DECL_TEXT_LEN = 256`、`HAS_ELLIPSIS = False`） | 声明行 `_integ_INTEGRATION_REPORT.md:13` 实读含「复制自」与 `COPY_IDENTICAL = True`，且同现 2 成员 → 三条件全满足。两成员 = `qc151_trip.isolated.py` / `qc151_trip.candidate_lf.py`（`_re_j4_out.json.results.a_real_item3.members`） |
| ② 六趟不合并 | `Q4_RELATION.md`（6 个不同真机趟同 hash 转储件；bytes=26405 与 bytes=None 两种喂入） | multi→multi | 两次均 `identical=True anchors=6 decl_words=[]`；复核脚本亦 `Q4 bytes_26405 multi -> multi anchors=6 decl_word_lines=[]` | 文件 `:85`「逐字节相同」、`:168`「逐字节相同」为**纯等同词**（本会话实读），封闭集 `DECL_RE` 不收 → 条件 (i) 无命中 |
| ③ 部分覆盖不合并 | 夹具 `Fp1_decl_covers_one`（声明行覆盖 1/2）、`Fp2_partial_two_of_three`（覆盖 2/3） | multi→multi | `Fp1 decl=None covers_n=1 covers_all=false`；`Fp2 decl=None covers_n=2 covers_all=false`；均 `identical=True` | 条件 (iii) 全或无：命中行覆盖并集 ≠ 全体成员 → 对 `out` 零改动，维持 multi 原 warning |
| ④ 纯等同词不合并 | 夹具 `Fd_equiv_words`（「二者逐字节同一」行同现 2 成员） | multi→multi | `decl=None`；`cover_ge2_lines=[3]` 但 `decl_word_lines=[]`；`identical=True` | 条件 (i) 封闭集未命中。复核 `_rev_cases.py` 的 `d1/d2/d3` 三形态亦全 multi→multi，且 `D1 WOULD_MERGE_IF_VOCAB_EXPANDED: True` 证明唯一拦点就是封闭集，**扩词会误合并** |

**正控制非空跑**：`e_Ffull_merged`（声明行全覆盖）`multi→merged decl=[4]`；复核脚本 `e1_full_3_merged`（3 成员）、`e2_full_15_merged`（15 成员）亦 `multi→merged`。`closed_vocab_unchanged` 断言 `DECL_RE.pattern` 与运行方独立正则逐字符相同；本会话 `_rev_core.py` 实跑输出 `DECL_RE: '复制自|复制为|COPY_IDENTICAL\\s*=\\s*True' | proto: '复制自|复制为|COPY_IDENTICAL\\s*=\\s*True'`。

## 5 复核回件 + 三条纪律 + 适配需求 + 未改声明 + 未验项

### 5.1 复核回件（verdict 如实记）

编排方【复核】给定 `verdict = confirmed`（`ranCommands = 15`；六项复核全部实跑通过，未触发任何 refuted 条件，未触发「理解错一处即 partial」条件）。**本会话按 `confirmed` 如实登记，未标 `unconfirmed`**。复核件（唯一写域内前缀 `_rev_`）：`_rev_core.py` / `_rev_cases.py` / `_rev_edge25.py` 与输出 `_rev_core_out.json` / `_rev_cases_out.json` / `_rev_edge25_out.json`、夹具 `_rev_fixtures/`；三脚本本会话均已重跑且 EXIT=0（§4.1）。复核回件**绑定行（固定格式）**：

被核对象 SHA256 = 7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52，字节数 = 19481

本会话 `python -I -B -X utf8 -c` 以 `hashlib` 重算 `_re_linked.py` 全字节并校验 `_re_NOTES.md` 绑定行，输出：`COMPUTED_BINDING_LINE: 被核对象 SHA256 = 7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52，字节数 = 19481`、`BINDING_LINE_PRESENT: True`、`BINDING_LINE_MATCH: True hex_ok= True bytes_ok= True`、`NOTES_LINE_NO: [6]`。即绑定行独立落在 `_re_NOTES.md:6`（任务给定【并入】写 `:5`、复核指出实为 `:6`，本会话实读确认为 `:6`；纯行号偏差，非内容错误）。

复核如实登记的观察（不改变 `confirmed`）：(a) 绑定行与禁授权段落在 `_re_NOTES.md` 实为 `:6` / `:40-48`（【并入】写 `:5` / `:38-46`）；(b) 25 成员分叉（§3.2）；(c) 原型 `decl_hits.text` 有 `[:160]` 截断（`_eq_proto.py:67`）而并入版 `:269` 为 strip 后全文（保真方向）。

### 5.2 三条纪律落地（merged 是新增形态，三条同时落地）

**(a) `path=None` 不做单一对象主张**。`_re_linked.py:26-29` 模块 docstring 纪律 1；J4 块 `:254-256` 注释不写任何单对象字段；`link()` 的 `reverify` 初始 `None`（`:177-179`），merged 分支不触碰；`link_triple` 的 `rec["path"]` 初始 None（`:310`）且 merged `elif`（`:320-329`）只赋 `tier/match/members/decl_lines`。本会话实跑 `MERGED_SHAPE` 的 `reverify: null`、`TRIPLE_SHAPE` 的 `path: null`、`SINGLE_OBJECT_FIELDS = []`；warning 含「未做单一对象主张（path=None）」。复核 15 成员 E2 亦 `triple_keys=['decl_lines','declared','match','members','path','samedoc_link','tier']`（无 `verified_path/recomputed/bytes`）。唯一单对象信息只出现在 `members`。

**(b) 禁止从 merged 推导授权结论（= 禁止授权推论）**。落地于 `_re_linked.py:30-33`（模块 docstring）、`:254-256`（J4 块注释）、`:287-288`（每条 merged warning 自带「禁止由 merged 推导任何授权结论」）、`:306-308` / `:322-325`（link_triple docstring/分支注释）、`_re_NOTES.md:40-48`。语义依据本会话实读：`lead/d25_ruling_20261106/RULING_D25.md:26` = 「把隔离副本离线集成扩大为正式母本应用…不得回溯扩大本次权限」；`_integ_INTEGRATION_REPORT.md:17` = 「本轮是『隔离副本集成演练』，不构成『可应用到母本』的放行」、`:59` = 「本次不授权正式母本写入」。规则：merged 只证明内容层逐字节同值，**不构成锚定、放行或授权**；角色归属只能人工从 `members` 与声明行原文辨认，`rec` 无任何授权类字段。

**(c) `members` 全列**。`_re_linked.py:34-36`、`:280-281`、`:328`；格式 `[{"path": 现盘解析绝对路径, "sha": 64 位小写 hex 全量, "bytes": int}, ...]`，`eq.members` 与 `rec.members` 同形，取**全量 `matches`** 而非 `anchors[:max_detail]`。本会话实跑：`Pm_15_members_all_listed` → `anchors=12 / eq=True`；`_rev_cases.py` E2 → `anchors=12 members=15`；`_rev_edge25.py` → `members=25 anchors=12` 且 TRIPLE `members_n: 25`；warning 列全量路径（`:289`）。

### 5.3 接入 `r11_scan_plus` 的适配需求（尚未接入，登记）

接入点实读：`lead/r11_f2_fix_20261109/_f2_r11plus.py:303-305` 的 `else` 分支（T1/T2/T2N/T3 全落空、现产 R3-3b 警告）；`SAMEDOC_LINK.md:22` 明写「是否接入由编排方裁决」。适配清单（`_re_NOTES.md:59-76` 实读，本会话照录）：

1. **tier 枚举扩展**：新值 `SAMEDOC_LINK_EQ`（merged 专用）；下游若对 tier 值集封闭须显式加分支，`tier=SAMEDOC_LINK_EQ` 且 `path=None` 是合法组合，不得当异常。
2. **path=None 形态适配**：merged rec 无 `verified_path/recomputed/bytes`；消费方若假设「match=True ⇒ 有单一 path」会 KeyError/误读，**必须走 `members`**。
3. **problems 契约不变**：联查恒不产 problem，只把返回 warnings 并入 r11 的 warnings。
4. **hash 重算复用（可选）**：`link()` 自读盘算 sha256；r11 已有 `recompute` 闭包，如需避免重复 IO 可给 `link()` 加 recompute 注入（语义不变的纯优化）。
5. **merged 事件逐次记档**：每次 merged 落 run 机读件 `{binding_hex, bytes_decl, members, decl_lines, decl_text}`——等价类是联查时刻快照（TOCTOU 同限）。
6. **判定书登记**：J4 是对 `SAMEDOC_LINK.md:20` ★4「唯一命中才采」的**显式修订**（multi 改为「声明解析 → merged｜multi」），并入台账时必须写明修订关系，不能无声替换。

### 5.4 未改 `_sl_link.py` 声明

本会话**未修改、未追加、未覆盖** `lead/samedoc_link_20261109/_sl_link.py`、`lead/equiv_class_20261109/`、`lead/f2d_rootcause_20261109/`、`lead/r11_f2_fix_20261109/`、`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`。证据：会话首/末两次 `hashlib` 十件全字节实算 `10/10 ALL_MATCH`（末次 `ALL_MATCH_POST_RUN = True`），`_sl_link.py` 恒 `a4ae4dc1… / 12475`；`_re_fp_check.py` 重跑 `ALL_MATCH` EXIT=0；`git log -1` 未新增提交；`git status --porcelain` 对只读路径显示的两件台账 `MM` 与三个只读目录 `??` 为会话开始既有状态（指纹与编排方基线全等），写域仅 `?? lead/r33e_merge_20261109/`。唯一写域内本会话新增仅本报告 `R33E_MERGE.md`；其余 `_re_*` / `_rev_*` / `_re_fixtures/` / `_rev_fixtures/` 为前置产物。`equiv_class` 与写域 `__pycache__` 均 `ABSENT`。

### 5.5 未验项（如实登记，不补造）

1. **未验**：343 件全语料的 multi 作用面未普查（`_eq_criteria.md:142` 同限；本会话未跑 `_eq_surface_probe.py` 全库普查）。
2. **未验**：`merged` 未接入真实 `r11_scan_plus` 生产路径；本会话只实读 `_f2_r11plus.py:303-305` 与给出适配清单，未做生产接入或端到端联调。
3. **未验**：TOCTOU 漂移窗口不可实测（零真机 + 只读纪律，仅登记，`_eq_criteria.md:146`）。
4. **未验**：J4 原型对 `F2D_ROOT_CAUSE` / `_m_CHAIN_VERIFY` / `GATE_TEMPLATE_REGRESSION` 的弃权面，本会话未复跑；`_eq_criteria.md:100` 的记载仅作引用，不冒充本会话实跑。
5. **未验**：Q4 同 hash 转储类全库成员数未再普查（`_eq_criteria.md:144`）；M2 绑定行角色括注消歧机制未设计未验证（`:145`）。
6. **已披露残余风险**：若未来出现「候选 == 母本同 hash」形态，J4 仍会合并，仅靠三条纪律保护（任务给定【并入】constraints §2；本会话未构造该形态实测）。声明词组封闭集**不得为提闭合率扩词**（§1、§4.2 例④ 已实跑证明扩词会误合并）。

---

**实跑命令总表（本会话，全部 `python -I -B -X utf8` + 绝对路径，指纹均 `hashlib`）**：

| 命令（脚本名省略公共前缀 `D:\Project\ra2-campaign-forge\lead\r33e_merge_20261109\`） | 输出摘要 | EXIT |
|:--|:--|--:|
| `python -I -X utf8 -c`（十件 hashlib） | `READONLY_BASELINE 10 / 10 ALL_MATCH= True`；`BINDING_OBJECT 7ca339c6… 19481` | 0 |
| `_re_fp_check.py` | 十行 `OK` + `ALL_MATCH` | 0 |
| `_re_struct_diff.py` | `STRUCT_OK: True`，11 hunk 全白名单，`GUARD … / RE …` | 0 |
| `_re_run10_diff.py` | 10 行逐条 + `SUMMARY unique 8=8 zero 1=1 changed_rows=[t3]` + `20 / 20 passed` | 0 |
| `_re_j4_cases.py` | 7 行四例 + 正控制 + `19 / 19 passed` | 0 |
| `_re_parity_extra.py` | 14 案 + `21 / 21 passed`，15 成员 members 全列 | 0 |
| `_rev_core.py` | `ALL_MATCH` + `92 / 92 passed` | 0 |
| `_rev_cases.py` | `69 / 69 passed`，`WOULD_MERGE_IF_VOCAB_EXPANDED: True`，`anchors=12 members=15` | 0 |
| `_rev_edge25.py` | `7 / 7 passed`，`members=25 anchors=12` | 0 |
| `python -I -B -X utf8 -c`（绑定行正则） | `BINDING_LINE_PRESENT: True`、`BINDING_LINE_MATCH: True`、`NOTES_LINE_NO: [6]` | 0 |
| `python -I -B -X utf8 -c`（会话末复算 + merged 形状） | `ALL_MATCH_POST_RUN = True`；`MERGED_SHAPE` / `TRIPLE_SHAPE` / `SINGLE_OBJECT_FIELDS = []` | 0 |
| `python -I -B -X utf8 -c`（J4/回归 JSON 明细、声明行、判据、r11 行） | 见 §2–§4 各引文 | 0 |
| `git log -1 --format='%H %s'` / `git status --porcelain -- …` | HEAD 未变；只读路径状态为会话开始既有 | 0 |
