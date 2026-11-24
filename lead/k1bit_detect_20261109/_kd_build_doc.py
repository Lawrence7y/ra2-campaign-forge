# -*- coding: utf-8 -*-
"""_kd_build_doc.py -- assemble K1BIT_DETECTOR.md in the sole write domain.

The pasteable code block is inserted verbatim from the VALIDATED file
_kd_pasteable.py (sha256 daceeed... / 20425 bytes), so the document cannot
drift from the implementation that was actually run.
"""
from pathlib import Path

WD = Path(__file__).resolve().parent
CODE = (WD / "_kd_pasteable.py").read_text(encoding="utf-8")

DOC = r"""# K1BIT_DETECTOR.md — k→1bit 检测器（语义级）设计与验证

写域：`lead/k1bit_detect_20261109/`；本件路径：`lead/k1bit_detect_20261109/K1BIT_DETECTOR.md`。
零真机（未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 taskkill，未读活进程内存）；
零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；
未改任何被检脚本、未 commit、未 push。Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib.sha256`。

---

## 1 目的与边界

**目的**：为「自检把 k≥2 个同类输入压成 1 bit」这一类缺陷设计并验证一个**语义判据（AST + 数据流）**检测器，量化字面筛的漏检与误报，给出合法聚合区分判据、可通用化方案与工具化建议。

**边界**：

1. 只做**检测器设计与验证**；不改任何被检脚本。被检件 173 件来自只读清单 `lead/check_family_20261109/_cf_filelist.txt`（本会话实跑 `find . -type f -name 'check_*.py' | wc -l` → `173`；清单 `lines=173 unique=173 live=173 missing=0`）。绝对只读域（`lead/check_family_20261109/`、`lead/check_masking_20261109/`、`lead/d27_ruling_20261106/`..`d30_ruling_20261106/`、`lead/refsync_scope_20261109/_rs_carrier_scan.py`、全库其余 `check_*.py`、两件台账）一律未修改；唯一写域为本目录。
2. 检测器本身**只读**被检件，输出逐件 `sha256 + bytes`；所有正负控 fixture 都在内存里（`_kd_selftest.py:3-6`、`_kdv_semantic_probe.py:3-6` 的注释明示），不落盘到写域外、不执行被检脚本。
3. 本任务是**静态候选器**：不做动态坏针注入、不跑被检门禁 ⇒ 不能确诊「坏针仍 PASS」（`CHECK_MASKING_INJECT.md:457` 第 4 步；`CHECK_FAMILY_LINEAGE.md:439,546` 亦标未验）。所有 `CONFIRMED_K1BIT` 只表示静态结构命中。
4. ★ **复核 verdict 如实记**：编排方【复核】字段给出 `verdict="partial"`（ranCommands=42），理由是「③④ 的实现层、⑤ 的独立负控发现实质破口，属『形式/名字/模板判据冒充语义判据』」。按交付要求 **`partial` 标 `unconfirmed`**：本件不把「`_kd_detect.py` 已具备纯语义判据」写成通过结论，只把它作为**被复核为 partial 的既有实现**引用；本件另给一份针对这些破口修正并实跑验证的实现（§3、§4）。同理，`CHECK_FAMILY_LINEAGE.md:336` 把「字面筛必然漏 d28/d27」标 `unconfirmed`，本件不改写该结论。
5. 材料来源：编排方【编排方指纹】【AST 形态】【设计】【复核】四个字段为本任务的输入材料；凡本件给出的数字，除明确标「编排方自报」外，均为**本会话实跑命令 + 输出**或**文件:行**。

---

## 2 上游指纹（十件）+ 漏检复核

### 2.1 十件指纹（本会话逐件实算）

命令：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/k1bit_detect_20261109/_kdv_check.py D:/Project/ra2-campaign-forge fp
```
输出（逐行）：
```
OK   lead/check_family_20261109/CHECK_FAMILY_LINEAGE.md e5098b23732141df0fcb48631cab5642cb4ec054f47564a2a0233fa6e10539f8 82856
OK   lead/check_family_20261109/_cf_detect_out.json 17e83a81ecf0cca951825d3191bb0772011de1af3269d793922a8db068e5c3c2 130498
OK   lead/check_family_20261109/_cf_census_out.json e5edea52c3f1959796c8132e7f4d04418c9704f992a59df84ec189d564b800fa 149737
OK   lead/check_family_20261109/_cf_detect.py 832355993a2b0f50bbc77c85f52531862d62fc01eab511cd29d78d06c860ffc1 7587
OK   lead/d27_ruling_20261106/check_d27.py 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c 3764
OK   lead/d28_ruling_20261106/check_d28.py 5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268 4539
OK   lead/d29_ruling_20261106/check_d29.py 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14 3906
OK   lead/d30_ruling_20261106/check_d30.py 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd 3926
OK   lead/PENDING_DECISIONS.md 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 52419
OK   lead/GOAL_THREE_TARGETS_20261018.md 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede 759518
FP_RESULT n=10 mismatches=0 []
```
`_kdv_verify.py` 跑前/跑后重核：`"before_mismatches": [], "after_mismatches": []`；273 行保护快照 `"protected_snapshot": {"n": 273, "mismatches": []}`。
设计回件两件另用 `python -I -X utf8 -c "import hashlib; ..."` 实算：`_kd_REPORT.md` `c7da08f0...b06 / 30517 True`、`_kd_detect.py` `42d8ff33...71d / 24378 True`（与编排方【复核】第一行、第二行一致）。

### 2.2 四件 `any()` 的 AST 参数类型（逐件实跑）

命令：
```
python -I -X utf8 .../_kdv_check.py D:/Project/ra2-campaign-forge ast
```
输出（摘要，完整见 `_kdv_ast_out.json`）：
```
check_d27.py regex_hits=1 ; line=86 arg=GeneratorExp :: (keyword in body for body in bodies.get(title, []) for keyword in keywords)
check_d28.py regex_hits=0 ; line=97 arg=Name        :: present
check_d29.py regex_hits=1 ; line=87 arg=Name        :: matches ; line=84 arg=GeneratorExp :: (word in body for word in words)
check_d30.py regex_hits=1 ; line=87 arg=Name        :: matches ; line=84 arg=GeneratorExp :: (word in body for word in words)
AST_RESULT four_files=4
```
与编排方【四件 any 的 AST 形态】逐项一致。文件:行直读：

- `check_d27.py:86-88`：`any(keyword in body for body in bodies.get(title, []) for keyword in keywords)` 是 **`ast.GeneratorExp`**；`:100` 是 `print(f"PASS: ...")`、`:101 return 0`。
- `check_d28.py:96`：`present = [word in body for word in words]` 是 **`ast.ListComp`**；`:97` 是 `all(present) if require_all else any(present)` —— 即 **any-present**（`any()` 实参是 `ast.Name`，不是生成器），`:115` 单行 PASS、`:116 return 0`。
- `check_d29.py:82-86`：`matches = [ all(word in body for word in words) if require_all else any(word in body for word in words) for body in bodies ]` 是 **`ast.ListComp`**，其元素为 **`ast.IfExp` 三元式**（内层 `:84` `ast.GeneratorExp`）；`:87 any(matches)` 是 `ast.Name`；`:105` PASS、`:106 return 0`。`check_d30.py:82-87`、`:105-106` 逐行同构。
- `_rs_carrier_scan.py:165` `min(...)` 生成器、`:194 --needle action="append"`、`:229 any(n in txt for n in a.needle)`、`:343 ok &= good`、`:346 SELF_TEST = PASS`、`:349 return 0 if ok else 1`（本会话 `grep -n` 实跑行号一致）。

**这就是字面筛漏检的机械原因**：`any\([^)]*for[^)]*in` 只能匹配生成器式；`any(present)` / `any(matches)` 的实参是 `Name`，`d28` 的 `:97` 还嵌在 `IfExp` 里，正则 `regex_hits=0`。

### 2.3 字面筛捞到几件 / 语义筛几件 / 漏检率（本会话独立复算）

真值取**编排方** `_cf_detect_out.json:confirmed`（40 件），不从新器输出取，避免循环论证；命令：
```
python -I -X utf8 .../_kdv_recompute.py D:/Project/ra2-campaign-forge
```
输出：
```
n=173 truth=40
L1             hits=49  TP=36  FN=4   FP=13  TN=120 fn_rate=0.1  fp_rate=0.2653061224489796
L2             hits=48  TP=36  FN=4   FP=12  TN=121 fn_rate=0.1  fp_rate=0.25
L3             hits=54  TP=40  FN=0   FP=14  TN=119 fn_rate=0.0  fp_rate=0.25925925925925924
combo_census   hits=28  TP=25  FN=15  FP=3   TN=130 fn_rate=0.375 fp_rate=0.10714285714285714
combo_own      hits=28  TP=25  FN=15  FP=3   TN=130 fn_rate=0.375 fp_rate=0.10714285714285714
combo_own_vs_census_diff= []
four_hits L1=3 L2=3 L3=4 combo=2
```
另跑 `python -I -X utf8 .../_kd_literal_vs_semantic.py D:/Project/ra2-campaign-forge` → `screens.L1_GENERATOR_FORM.n_hits=49 / L2=48 / L3=54`，`census_combos.n_combo_orchany_passliteral=28, n_combo_orchany_passprint=46, n_combo_wordor_passprint=40, n_orch_any=48, n_any_gen=53, n_any_word_or=40, n_pass_print=64`；与 `_cf_census_out.json:summary` 一致。

| 口径 | 四件命中 | 漏检率（四件） | 173 件命中 | 对 40 真值漏检率 |
|---|---|---|---|---|
| L1 生成器式 `any\([^)]*for[^)]*in` | **3/4** | `(4-3)/4 = 25%` | 49 | `FN=4 → 4/40 = 10%` |
| L2 `orch_any_line`（`_cf_census.py:55-59`） | **3/4** | `25%` | 48 | `4/40 = 10%` |
| L3 宽口径 `\bany\s*\(` + `^\s*print\(.*PASS` | **4/4** | `0%` | 54 | `0/40 = 0%` |
| 严格字面组合（`_cf_census.py:55-59` + `:80-81` `print("PASS` 立即开头） | **2/4**（仅 d29/d30） | `(4-2)/4 = 50%` | 28 | `FN=15 → 15/40 = 37.5%` |
| **语义级（AST + 数据流）** `_kd_detect.py` | **4/4** | `0%` | **40** + 6 `SUSPECT` + 80 `LEGAL_AGGREGATE` + 47 `NO_SELFTEST` | 与编排方 40 件集合 `identical=True` |

- 四件 `2/4` 的成因：d27 漏因 `:100` 是 f-string PASS（`print(f"PASS: ...")`），d28 漏因 `:97 any(present)`；`CHECK_FAMILY_LINEAGE.md:327-329,336` 已列三种口径并把「字面筛必然漏 d28/d27」标 **unconfirmed**（宽口径 54 件四件全命中、零漏判）。本件三个口径并列，不改写编排方结论。
- L1/L2 的 4 个 FN 全是 d28 模板（含 3 件沙箱副本）：`check_d28.py`、`_sp_sandbox/d28/check_d28_baseline.py`、`_sp_sandbox/d28x/a/b/check_d28_baseline.py`、`_sp_sandbox/d28x/a/b/check_d28_injected.py`（`_kdv_recompute.py` 的 `MISS L1` / `MISS L2` 输出）。**假阴成族出现**：一处写法变化，整支模板消失。
- 字面筛同时有**假阳**：L1 `FP=13`、L2 `FP=12`、L3 `FP=14`、严格组合 `FP=3`；含 `check_d26.py`（跨 body 存在性）、`check_feasibility.py`（逐项 `[PASS] 检查项 N`）、带 `hits` 归因的合法件。详见 §5。

---

## 3 语义级检测器（语义定义 + 六形态 + 可粘贴实现 + 合法聚合判据）

### 3.1 ★ 语义定义（不是「用了 `any()`」）

据 `CHECK_MASKING_INJECT.md:447-450`（本会话直读 `:445-450`）：

> 自检有 **k≥2 个同类输入**（needle / keyword / pattern / case / token），待证命题是
> `∀i: 输入_i 有效`（`DISTINGUISHABLE_PASS = AND_k(真实逐输入自检)`，`:450`）；
> 代码却用**存在量词**合成 `covered(x) = ∃i: match(input_i, x)`，再把 k 个输入的存活情况
> **压成 1 bit**（`if not any(...)` / `ok &= good` / `min(pos)` 只留位置 / 单行 `PASS` / 单个
> `SELF_TEST = PASS`），且**不保留** `hits=[命中下标]` 之类逐输入溯源、没有逐输入打印（`:447-449`）。
> ⇒ 「输入_1 全死、但每个样本都被输入_{j≠1} 命中」与「k 根全正常」**观测等价**；**逐输入可归因 = 否**。

**可操作四信号**（`_kd_detect.py:17-35` 的文档定义）：

| 信号 | 语义内容 | 数据流判定 |
|---|---|---|
| **S1 KSOURCE** | 存在 k≥2 同类输入 | 字面字符串集合 / 需求表行 / `argparse action="append"`；经 `Assign`、`for` 解包、形参→实参两轮传播 |
| **S2 COLLAPSE** | ∃ 塌缩到 1 bit 且量词变量**恰遍历 S1 的 k 输入** | `any(GeneratorExp/ListComp)`、`any(Name)` 回溯绑定、`IfExp` 三元 OR/AND、`min/max` argmin、`ok &= good` / `ok = ok and good` |
| **S3 ONEBIT** | 聚合出口、无逐输入输出 | 单行 `PASS`/`SELF_TEST` + `return 0/1` / `0 if ok else 1`；无逐 token 打印、无 `hits[]` |
| **S4 LEGAL** | 合法聚合排除 | `all()` = `AND_k`；`any()` 遍历**样本/正文**且谓词是单个固定字面；`sum/len/sorted` 保基数；有归因 |

关键：判据看的是**「量词遍历什么 + 元素在测谁 + 结果留了几 bit + 归因是否保留」**，不是 `any` 这个 token，也不是变量名。

### 3.2 六种形态：逐形态给出落点、AST 节点与实跑命中（不用「已覆盖」概括）

| # | 形态 | AST 节点 | 文件:行 实证 | 实跑命中 |
|---|---|---|---|---|
| 1 | **`GeneratorExp`** `any(x in y for ...)` | `ast.GeneratorExp` 作为 `any()` 首参 | `check_d27.py:86`（`for keyword in keywords`）、`check_d29.py:84` / `check_d30.py:84`（`for word in words`）、`_rs_carrier_scan.py:229`（`for n in a.needle`） | `_kdv_verify.py` `ones` → d27 `[[86,"OR_COLLAPSE_gen"]]`、d29/d30 `[[84,"OR_COLLAPSE_gen"],[87,"OR_COLLAPSE_ternary_list"]]`、carrier `[[229,"OR_COLLAPSE_gen"]]`；`_kd_detect_out.json` 全库 `OR_COLLAPSE_gen` **44 处**（本会话 `python -I -X utf8 -c` 统计 `collapse_kinds`；其中 **36 件** `CONFIRMED_K1BIT` 文件各含 ≥1 处，另 8 处散在 `SUSPECT`/`LEGAL_AGGREGATE` 件 —— 编排方【设计】的「36 处」按「确诊文件数」读法成立，本件两个口径都列出） |
| 2 | **`ListComp` + any-present** | `present`/`matches` 绑定到 `ast.ListComp`，`any()` 首参是 `ast.Name` | `check_d28.py:96-97`（`present = [word in body for word in words]` → `any(present)`）、`check_d29.py:82-87` / `check_d30.py:82-87`（`matches = [IfExp(...) for body in bodies]` → `any(matches)`） | d28 `[[97,"TERNARY_OR_BRANCH"],[97,"OR_COLLAPSE_bound_list"]]`；d29/d30 `[[87,"OR_COLLAPSE_ternary_list"]]`；全库 `OR_COLLAPSE_bound_list` **4 处**、`OR_COLLAPSE_ternary_list` **25 处** |
| 3 | **三元式** OR/AND 混合 | `ast.IfExp`；`all(...) if require_all else any(...)` | `check_d28.py:97`、`check_d29.py:82-86`、`check_d30.py:82-86` | `TERNARY_OR_BRANCH` **4 处**（`_kd_detect_out.json` collapse_kinds）；四件 `--one` 全见 |
| 4 | **ok-and-eq**（`ok &= good` / `ok = ok and good`） | `ast.AugAssign(op=ast.BitAnd)` / `ast.Assign(value=ast.BoolOp(op=ast.And))` | `_rs_carrier_scan.py:343 ok &= good`；`out/re_work/qc/W3_20261001/scripts/check_gate.py` 的 `BIT_ACCUM_bool_and`（`_kdv_quant.py` `accum_only.rows`，本会话实跑 `confirmed_n=0`） | carrier `[[343,"BIT_ACCUM_AugAssign_BitAnd"]]`；`_kd_selftest.py` P4 正控 `CONFIRMED_K1BIT` |
| 5 | **min-argmin** 反向掩蔽 | `ast.Call(func=Name("min"), args[0]=GeneratorExp)` | `_rs_carrier_scan.py:165 pos = min((line.find(n) for n in needles if n in line), default=-1)`；`CHECK_MASKING_INJECT.md:441` 同列 | carrier `[[165,"ARGMIN_REVERSE_MASK"]]`；`_kdp_validate.py` V11 正控 `CONFIRMED_K1BIT` |
| 6 | 单行 PASS / 1-bit 出口且无逐输入打印 | `ast.Return` 常量 0/1 或 `IfExp` `0 if ok else 1`；`ast.Call(print)` 含 `PASS` | `check_d27.py:100-101`（f-string PASS）、`check_d28.py:115-116`、`check_d29.py:105-106`、`check_d30.py:105-106`、`_rs_carrier_scan.py:346 SELF_TEST = PASS` / `:349 return 0 if ok else 1` | `_kdv_verify.py` 五件 `onebit=true, attribution=false`；carrier `agg_pass=[346]`、`onebit=[{"line":349,"expr":"0 if ok else 1"}]` |

补充：`_cf_detect.py:8-18` 的 P1–P4 是**模板级**判据（`_cf_detect.py:54-55` 的 P4 甚至靠 `n.name in ("sections","section_bodies",...)` 名字匹配），`CHECK_FAMILY_LINEAGE.md:449` 已指出名字级判据会被函数改名绕过；本件的语义判据不依赖函数名。

### 3.3 ★ 可粘贴实现（本会话实跑验证过的完整代码）

下面代码块**逐字**取自 `lead/k1bit_detect_20261109/_kd_pasteable.py`（`sha256=daceeed14175850bf36d231842c5fca1ce2ed4a6d6736f69914be5ded0f6277a`、`bytes=20425`，本会话 `hashlib` 实算）。它是针对【复核】`partial` 四个破口的**修正版**；原 `_kd_detect.py` 保持原样、未改一字。

修正点（与 §3.4 的破口编号对应）：① `build_bindings` 存 `(lineno, expr)` 二元组，`collect_ksources` 显式解包，直接赋值分支不再是死代码；② `is_token_source` 只用数据流推导出的 token 集合，**删除 `TOKENISH` 名字正则**，并做**角色推断**（字面字符串集合只有当其循环变量被当作「变化探针」——`token in sample` 的左操作数、`find/search` 的实参——才算 k 源，`cases=["doc1","doc2"]` 配 `"FIXED" in case` 是样本不是 token）；成员测试**有方向**（`token in body` 是探针，`"FIXED" in body` 是样本存在性）；③ `has_k` 对**所有**判档生效，`&=` 不再绕过 k≥2；④ 归因必须是「探针循环变量作下标的真实 `hits[token] = ...` 存储」或逐输入 PASS 打印，一个叫 `hits` 的标量不算；⑤ 额外补上 `present[0] or present[1]`（`ast.BoolOp(Or)`，无 `any` 字面）形态。

跑法：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/k1bit_detect_20261109/_kd_pasteable.py D:/Project/ra2-campaign-forge
python -I -X utf8 .../_kd_pasteable.py D:/Project/ra2-campaign-forge --one lead/d28_ruling_20261106/check_d28.py
```

```python
<<<CODE>>>
```

验证该实现本身的命令与输出（§4 详列）：
```
python -I -X utf8 .../_kdp_validate.py D:/Project/ra2-campaign-forge
→ {"n_fixtures": 16, "passed": 16, "failed": [], "n_files": 7, "files_passed": 7, "files_failed": []}
```

### 3.4 ★ 真缺陷 vs 合法聚合的区分判据（三件事，不是见 `all()` 就不报）

判据 = **① 量词遍历的对象 + ② 是否保基数 + ③ 是否保归因**：

1. `all(word in body for word in words)` **合法**：`all()` 要求 k 根全真，死掉任一根 `PASS→FAIL`，等价 `AND_k`（`_kd_detect.py:347-351` 记 `AND_aggregate`）。四件里的 `all()` 都在**同一表达式的 `else any(...)` 分支**旁：`check_d28.py:97`、`check_d29.py:83`、`check_d30.py:83`。故「有 `any()` 就报 / 见 `all()` 就不报」都错。实跑 `python -I -X utf8 .../_kdv_quant.py D:/Project/ra2-campaign-forge` → `n_all=31 n_any=57 n_both=30 n_all_only=1`，`all_only=["out/re_work/agy_patchhex/bytes/check_bytes.py"]` 且其 `verdict=LEGAL_AGGREGATE`；30 件 both 中 29 件 `CONFIRMED_K1BIT`，且 `both_confirmed_and_has_AND_legal=29/29`。
2. `any("本次不授权" in body for body in bodies)` **合法**：量词遍历的是**样本/正文**，谓词是**一个固定字面**，k=1，无从掩蔽。`check_d26.py:85,87,90` 三个 `any()` 全属此类（`CHECK_FAMILY_LINEAGE.md:345` 确定判断）；本会话 `_kd_detect_out.json` 判 `LEGAL_AGGREGATE`。
3. `any(word in body for word in words)` **缺陷**：量词遍历 **k≥2 词表本身**，谓词随词变 ⇒ `∃i` 覆盖 `∀i`。
4. `len(hits)` / `sum(...)` / `sorted(...)` **合法**：保基数或保序（`_kd_detect.py:364-367` `count_preserving`）。`check_feasibility.py` 的逐项 `[PASS] 检查项 N`（`CHECK_FAMILY_LINEAGE.md:349` 列 `:119,149,164,176,197,206,214,223,259,333`）亦 `LEGAL_AGGREGATE` — 本会话实跑确认。
5. 有 `hits=[...]` / 逐输入 `print` **合法**：逐输入归因保留；`_kd_selftest.py:65-77` N5、`_kdp_validate.py` N3 均判 `LEGAL_AGGREGATE`。
6. `min(pos)` **缺陷（反向掩蔽）**：只留一个位置，丢掉「哪个 needle 命中」；`ok &= good` 把多条负控压成一个 bit，同理（`CHECK_MASKING_INJECT.md:441,443`）。

**一句话**：合法 = `AND_k` / 单输入存在性 / 保基数 / 保归因；缺陷 = 对 k≥2 输入做 `∃` 塌缩且丢归因。

★ **复核 `partial` 的四个实质破口（本会话逐项复现，均不得当作已修复于原器）**：

| 破口 | 原器位置 | 本会话实跑命令 → 输出 |
|---|---|---|
| (a) 直接赋值 S1 分支是死代码；40 件 k 源 100% 来自「for 解包需求表行」模板 | `_kd_detect.py:148-160`、`build_bindings:112-129` | `python -I -X utf8 -c`（`zzz=("aa","bb")`）→ `literal_str_collection=['aa','bb']` 但 `collect_ksources={}`，`is_token_source zzz=(False,None)`、`words=(True,'words')`、`SAMPLEISH used=False`；`_kdv_quant.py` → `dead_branch_files=64`、`token_reason_counts={"for_unpack_token_row":40}`、`confirmed_with_empty_tokens=[]` ⇒ `identical=True` 不是独立语义复核，与 `_cf_detect.py:59-74` 的 P1 共享模板级前提 |
| (b) 名字启发式冒充数据流 | `_kd_detect.py:49-53,226-229` | `_kdv_probe2.py` → `n=8 passed=3 failed=5`：`words` 名 k=2 真缺陷=`SUSPECT`、`zzz` 名=`LEGAL_AGGREGATE`；`words` 名 k=1 合法件=`SUSPECT`；`hits` 名抑制=`LEGAL_AGGREGATE` 而中性名=`SUSPECT`。同一语义仅改名字即翻盘 |
| (c) 独立 12 fixture 四个漏/降级 | `_kd_detect.py:431-434,385-388,469-487` | `_kdv_semantic_probe.py` → `n=12 passed=8 failed=4`：V7 改名真缺陷→`LEGAL_AGGREGATE`、V8 无 `any` 的 `present[0] or present[1]`→`LEGAL_AGGREGATE`、V10 名为 `hits` 的标量→`LEGAL_AGGREGATE`、V11 `min` argmin→`SUSPECT` |
| (d) `has_k` 被 `&=` 绕过 ⇒ 实测**假阳** | `_kd_detect.py:385-388,484` | `_kdv_probe3.py` → `{"verdict":"CONFIRMED_K1BIT","want":"LEGAL_AGGREGATE","ok":false,"has_k":false,"n_accum":1}`；本会话 `-c` 复跑同得 `verdict=CONFIRMED_K1BIT has_k=False n_accum=1` |

⇒ 按交付要求：`partial` **标 `unconfirmed`**。上表是「原实现不能宣称零误报的语义判据」的证据；§3.3 的修正版仅对上述 fixture 与 173 件静态集合做过验证（§4），**仍不是动态确诊器**。

---

## 4 检测器验证（四件全中 + carrier_scan + 全库 173 件 vs 40 件 + 误报验证）

### 4.1 四件生产门禁逐件

命令（由 `_kdv_verify.py` 以 `subprocess` 发出，日志 `_kdv_reruns.txt`）：
```
python -I -X utf8 .../_kd_detect.py D:/Project/ra2-campaign-forge --one <f>
```
`_kdv_verify.py` 汇总输出：
```
"ones": [
 {"rel":".../check_d27.py","verdict":"CONFIRMED_K1BIT","collapse":[[86,"OR_COLLAPSE_gen"]],"has_k":true,"onebit":true,"attribution":false},
 {"rel":".../check_d28.py","verdict":"CONFIRMED_K1BIT","collapse":[[97,"TERNARY_OR_BRANCH"],[97,"OR_COLLAPSE_bound_list"]],...},
 {"rel":".../check_d29.py","verdict":"CONFIRMED_K1BIT","collapse":[[87,"OR_COLLAPSE_ternary_list"],[84,"OR_COLLAPSE_gen"]],...},
 {"rel":".../check_d30.py","verdict":"CONFIRMED_K1BIT","collapse":[[87,"OR_COLLAPSE_ternary_list"],[84,"OR_COLLAPSE_gen"]],...}
]
```
逐件 `tokens` / `agg_pass` / `onebit`（本会话 `python -I -X utf8 -c` 读 `_kd_detect_out.json`）：
- d27 `keywords=(for_unpack_token_row,k=2,line=81)`，`collapse=[(86,OR_COLLAPSE_gen,2)]`，`agg_pass=[100]`；
- d28 `words=(...,k=2,line=94)`，`collapse=[(97,TERNARY_OR_BRANCH,2),(97,OR_COLLAPSE_bound_list,2)]`，`agg_pass=[115]`；
- d29 `words=(...,k=3,line=80)`，`collapse=[(87,OR_COLLAPSE_ternary_list,3),(84,OR_COLLAPSE_gen,3)]`，`agg_pass=[105]`；d30 同构（k=2）。
四件 `4/4 CONFIRMED_K1BIT`，零漏。

### 4.2 `_rs_carrier_scan.py` 逐处

命令：
```
python -I -X utf8 .../_kd_detect.py D:/Project/ra2-campaign-forge --one lead/refsync_scope_20261109/_rs_carrier_scan.py
```
输出（摘要）：`"verdict":"CONFIRMED_K1BIT"`，`sha256=9ccca808...a57 / bytes=16053`，`tokens={"needle":{k:"runtime",why:"argparse_action_append",line:194},"needles":{k:"runtime",why:"param_from_argparse_action_append",line:238}}`，三处塌缩 `[(165,ARGMIN_REVERSE_MASK),(343,BIT_ACCUM_AugAssign_BitAnd),(229,OR_COLLAPSE_gen)]`，`agg_pass=[346]`、`onebit=[{"line":349,"expr":"0 if ok else 1"}]`、`attribution=false`。与 `CHECK_MASKING_INJECT.md:441`、`CHECK_FAMILY_LINEAGE.md:352` 的 `:165/:194/:229/:343/:346/:349` 锚点逐处一致。

### 4.3 ★ 全库 173 件，与编排方 40 件比对

命令：
```
python -I -X utf8 .../_kd_detect.py D:/Project/ra2-campaign-forge
```
`_kdv_verify.py` 输出：
```
"counts": {"NO_SELFTEST":47,"LEGAL_AGGREGATE":80,"CONFIRMED_K1BIT":40,"SUSPECT":6}, "n":173
"confirmed_comparison": {"kd_confirmed":40,"cf_confirmed":40,"identical":true,"cf_only":[],"kd_only":[]}
```
`_cf_detect_out.json` 本会话实读：`n=173 n_confirmed=40 n_suspect=3`，`four` 四件全 `CONFIRMED`。口径差：`_cf_detect.py` 报 `CONFIRMED 40 / SUSPECT 3 / NOT_FAMILY 130`；`_kd_detect.py` 把 `check_d26.py` 判 `LEGAL_AGGREGATE`（§3.4 第 2 条），另列 6 件 `SUSPECT`（3×`check_windows_cmds.py`、2×`check_fileoffset_axiom*.py`、`check_134_inc.py`，见 `_kd_detect_out.json:suspect` 本会话打印）。

**修正版 `_kd_pasteable.py` 的独立结果（如实并列，不冒充 40）**：
```
python -I -X utf8 .../_kd_pasteable.py D:/Project/ra2-campaign-forge
→ n=173 counts={'NO_SELFTEST':52,'LEGAL_AGGREGATE':78,'CONFIRMED_K1BIT':42,'SUSPECT':1}
→ cf40_subset=True, extra=['out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.py',
                           '.../check_fileoffset_axiom.template.py']
```
这 2 件在 `CHECK_FAMILY_LINEAGE.md:351` 被定级为 `SUSPECT_ANTI_MASKING`（有 `GOLDEN_POS/NAIVE_FLOOR/EXIT=3` 反掩蔽硬闸，`:35,:203,:214,:254-255,:316-317`）；修正版在 `:301 any(w in low for w in OFFSET_WORDS)` 记 `OR_COLLAPSE_gen` 而报静态候选。**这 2 件是否真属本缺陷 = 未验**，不据此改编排方 40 件结论。修正版唯一 `SUSPECT` 为 `out/re_work/re_sprint/S1/check_134_inc.py`（`:8 OR_COLLAPSE_gen`，`has_k=false`、`onebit=false`）。

### 4.4 ★ 误报验证（逐项实跑）

| 验证 | 命令 | 输出 |
|---|---|---|
| 自带 10 个内存 fixture | `python -I -X utf8 .../_kd_selftest.py` | `n=10 passed=10 failed=0 all_negatives_correct=true all_positives_correct=true`；N1 `all(GenExp)`、N2 `all(bound)`、N3 跨样本单字面、N4 `len(hits)`、N5 逐输入打印+`hits[]`、N6 无 `any()` 六负控全 `LEGAL_AGGREGATE`；P1–P4 四正控全 `CONFIRMED_K1BIT` |
| **可跑的合法 `all()` 脚本** | `python -I -X utf8 -c`（`subprocess` 跑 `_kdv_legal_all.py`，再调 `kd.analyse`） | 全活输入 `exit=0 stdout=PASS: all 3 inputs verified`；死一根 `exit=1 stdout=FAIL: at least one of the k inputs is dead`；检测器 `verdict=LEGAL_AGGREGATE collapse=[] legal=['AND_aggregate','count_preserving','count_preserving']` ⇒ 语义确实合法且 0 误报 |
| 全库 `all()` 件 | `python -I -X utf8 .../_kdv_quant.py ...` | `n_all=31 n_all_only=1`，`check_bytes.py` 判 `LEGAL_AGGREGATE`；`all()` 自身从未触发报警 |
| 真实合法件 | `python -I -X utf8 -c`（读 `_kd_detect_out.json`） | `check_d26.py` / `check_bytes.py` / `check_feasibility.py` 均 `LEGAL_AGGREGATE` |
| ★ 独立负控发现的**实测假阳** | `python -I -X utf8 .../_kdv_probe3.py` | 合法 k=1 跨样本存在性 + 无关 `ok &= good` → 原器 `CONFIRMED_K1BIT`（`has_k=false`），即**假阳**；自带「0 件误报」只在自带选择性负控与全库 `all()` 件范围内成立 |
| ★ 修正版对同一批破口 | `python -I -X utf8 .../_kdp_validate.py ...` | `16/16` fixture + `7/7` 文件全 PASS：V7 改名真缺陷、V8 无 `any` 的 OR、V10 标量 `hits`、V11 argmin 全 `CONFIRMED_K1BIT`；probe3 合法件、A–H 名字不变性、N1–N3 负控、四件门禁、carrier、`d26`、可跑 `all()` 件全部符合预期 |
| 边界 | `git diff --name-only HEAD -- '*check_*.py' \| wc -l`；`git rev-parse HEAD`；`_kdv_verify.py` | `0`；`26574589aa8401e8f3f2934680a1ea7109bafa2d`（与会话开始 `2657458` 相同）；`before_mismatches=[] after_mismatches=[] protected_snapshot n=273 mismatches=[]` ⇒ 未改被检脚本、未 commit/push |

---

## 5 字面 vs 语义（命中数、假阴假阳、审计含义、何时用哪种）

### 5.1 命中数（同一 173 件 bytes / 同一 40 件真值）

| 筛法 | 173 件命中 | 四件命中 | TP | **FN（假阴）** | **FP（假阳）** | TN | 漏检率 | 误报率 |
|---|---|---|---|---|---|---|---|---|
| L1 生成器式 `any\([^)]*for[^)]*in` | **49** | 3/4 | 36 | **4** | **13** | 120 | `4/40=10%` | `13/49=26.5%` |
| L2 `orch_any_line` | **48** | 3/4 | 36 | **4** | **12** | 121 | `10%` | `25%` |
| L3 宽口径 `any\(` + `PASS` | **54** | 4/4 | 40 | **0** | **14** | 119 | `0%` | `25.9%` |
| 严格字面组合 | **28** | 2/4 | 25 | **15** | **3** | 130 | `15/40=37.5%` | `3/28=10.7%` |
| 语义级 `_kd_detect.py` | **40**（+6 SUSPECT / 80 LEGAL / 47 NO_SELFTEST） | **4/4** | 40 | 0 | 0（对编排方 40 真值） | 133 | `0%` | `0%` |
| 修正版 `_kd_pasteable.py` | **42**（+1 SUSPECT / 78 LEGAL / 52 NO_SELFTEST） | **4/4** | 40 | 0 | 2（相对编排方 40 真值，见 §4.3，标**未验**） | 131 | `0%` | `2/42=4.8%`（未验） |

`_cf_census_out.json:summary` 本会话实读：`n_combo_orchany_passliteral=28, n_orch_any=48, n_any_gen=53, n_pass_print=64`；`CHECK_FAMILY_LINEAGE.md:327-330` 的 28 / 46 / 54 / 40 四个数字与之一致。

### 5.2 ★ 假阴 / 假阳的成因与对代码审计的含义

1. **假阴成族**：L1/L2 的 4 个 FN 全是 d28 模板（`check_d28.py` + 3 件 `_sp_sandbox` 副本）；`any(present)` 的 `ast.Name` 参数与 `IfExp` 三元式让生成器式正则整支失效。严格组合的 15 个 FN 还包含 `check_d27.py` 的 f-string PASS 与 8+ 件 `_cm_tmp/d27/*` 副本。**一处写法变化 ⇒ 一族消失**，grep 审计会系统性看不见换过写法的分支。
2. **假阳把合法件当缺陷**：L1 的 13 件 FP = 6 件 `SUSPECT` + 7 件 `LEGAL_AGGREGATE`，含跨 body 存在性（`check_d26.py:85,87,90`）、逐项 `[PASS]` 打印（`check_feasibility.py`）、带 `hits` 归因的 `check_semantic_review*.py`；L3 的 14 件 FP = 5 `SUSPECT` + 9 `LEGAL_AGGREGATE`。25–26% 误报率意味着每 4 件里约 1 件是 `all()` / 存在性 / 逐输入打印的合法件；据此批量替换会改动无辜脚本（`CHECK_FAMILY_LINEAGE.md:418` 已警告会连带改动证据生产副本）。
3. **口径决定结论且不可证成**：同一个「字面筛」在四件上可以是 `2/4`（严格组合）、`3/4`（生成器式）、`4/4`（宽口径）；把 L1 放宽到 L3，`FN 4→0` 但 `FP 13→14` 不降反升。`any` 这个字面 token 与「∃ 塌缩 k 个输入」没有必然联系。`CHECK_FAMILY_LINEAGE.md:336` 已把「字面筛必然漏 d28/d27」标 `unconfirmed`；本件不改写。
4. **审计含义**：grep / 字面筛只能当**召回用的候选枚举**（先圈范围、给行号；要求零遗漏须用最宽口径并接受高 FP），**不能当判据、不能当确诊、不能当计数结论**。判据必须落在 **AST / 数据流**层（量词变量、绑定来源、成员测试方向、保基数、保归因）；确诊还需动态坏针注入 + `AND_k`（`CHECK_MASKING_INJECT.md:450,457`；`CHECK_FAMILY_LINEAGE.md:450`），本任务按纪律**未做**。
5. **`identical=True` 不是独立复核**：`_kdv_quant.py` 证明 `_kd_detect.py` 的 40 件 k 源 100% 来自与 `_cf_detect.py:59-74` P1 相同的「元组表行 ≥2 字符串」模板（§3.4(a)）；两器共享模板前提，故集合相等只能说明口径一致，不能证明语义判据独立成立。这也是【复核】判 `partial` 的核心理由之一。

### 5.3 何时用哪种

| 用字面筛（且只当候选） | 必须用语义筛 |
|---|---|
| 找**固定字面量**：API 名、错误串、路径、commit hash、常量值；文本层可判定 | 判据涉及**同一语义的不同写法**（`GeneratorExp` / `ListComp` / `any-present` / 三元式 / `ok-and-eq` / min-argmin） |
| 枚举**不受语法结构影响**的锚点：文件清单、行号、import、台账原文 | 判据是**量词 / 绑定 / 作用域 / 数据流**（`∃` 遍历谁、`Name` 绑到什么、是否保归因） |
| 快速定位后**人工逐件复核**，明确标「候选，非结论」 | 需要**精确计数 / 出确诊清单 / 批量改动前的影响面** |
| 目标「宁滥勿漏」的初筛，且后续有语义或动态步骤兜底 | 需要**区分合法聚合与缺陷**（`all()` vs `any()`、跨样本存在性 vs k 词 OR） |
| 输入只有**非代码文本**（md/txt/json 字段） | 代码会被重构 / 改名 / 复制成沙箱变体（40 件里 27 件与生产门禁字节相同、13 件为注入变体，`CHECK_FAMILY_LINEAGE.md:331,338`） |

判据一句话：**只要「同一语义能否换写法」的答案是「能」，就必须用语义筛。**

---

## 6 复核回件（绑定行）+ 结论 + 未验项

### 6.1 ★ 复核 verdict 与 `unconfirmed` 标记

- 编排方【复核】`verdict = "partial"`，`ranCommands=42`（自报、无日志，本会话**未验**其条数）；`sha256Line` 首行 `c7da08f0...b06 / 30517`。本会话独立复跑 `_kdv_check.py fp` / `ast`、`_kdv_recompute.py`、`_kdv_verify.py`、`_kdv_quant.py`、`_kdv_semantic_probe.py`、`_kdv_probe2.py`、`_kdv_probe3.py`、`_kd_selftest.py`、`_kd_literal_vs_semantic.py`，**①②⑥⑦ 复现通过，③④⑤ 的破口全部复现**（§3.4、§4.4）。
- ⇒ 按交付要求：**`partial` 标 `unconfirmed`**。具体标 unconfirmed 的命题：①「`_kd_detect.py` 已是纯语义判据 / 零误报」；②「`identical=True` 构成独立语义复核」；③「字面筛必然漏 d28/d27」（`CHECK_FAMILY_LINEAGE.md:336`）；④ 修正版多出的 2 件 `check_fileoffset_axiom*.py` 是否真属本缺陷。凡 `refuted` 项亦按 `unconfirmed` 处理，不写成通过。
- 本会话输出的新件只落唯一写域：`K1BIT_DETECTOR.md`、`_kd_pasteable.py`、`_kd_pasteable_out.json`、`_kdp_validate.py`、`_kdp_validate_out.json`、`_kd_build_doc.py`；原有 `_kd_*` / `_kdv_*` 产物除复跑重写写域内 `_kd_*_out.json`（设计回件产物、非只读域）外未改。

### 6.2 绑定行（格式固定；本会话 `hashlib.sha256` 读 bytes 实算）

行序对应：① `_kd_REPORT.md`；② `_kd_detect.py`；③–⑫ 编排方十件指纹；⑬ `_kd_pasteable.py`；⑭ `_kdp_validate.py`。每行均为「被核对象 SHA256 = 」+ 完整 64 位十六进制 +「，字节数 = 」+ 数字，行内不插路径、括号、星号、反引号或空格。

被核对象 SHA256 = c7da08f018cae238f571bf8025c92acf2cf82f3c49a98e7c1abb18b4a3df0b06，字节数 = 30517
被核对象 SHA256 = 42d8ff33cc190e9ce446fb3ed7f5d8ec9f8cff9e37f7f3f1aab98b1972c6971d，字节数 = 24378
被核对象 SHA256 = e5098b23732141df0fcb48631cab5642cb4ec054f47564a2a0233fa6e10539f8，字节数 = 82856
被核对象 SHA256 = 17e83a81ecf0cca951825d3191bb0772011de1af3269d793922a8db068e5c3c2，字节数 = 130498
被核对象 SHA256 = e5edea52c3f1959796c8132e7f4d04418c9704f992a59df84ec189d564b800fa，字节数 = 149737
被核对象 SHA256 = 832355993a2b0f50bbc77c85f52531862d62fc01eab511cd29d78d06c860ffc1，字节数 = 7587
被核对象 SHA256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c，字节数 = 3764
被核对象 SHA256 = 5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268，字节数 = 4539
被核对象 SHA256 = 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14，字节数 = 3906
被核对象 SHA256 = 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd，字节数 = 3926
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
被核对象 SHA256 = daceeed14175850bf36d231842c5fca1ce2ed4a6d6736f69914be5ded0f6277a，字节数 = 20425
被核对象 SHA256 = 0abc4c61ed5f670d982fda832358e64875196f92a50af42acd5e16efaebb3d00，字节数 = 7375

### 6.3 结论

**(a) 最小可用版本（MVDet）**：`ast.parse` → `build_bindings`（赋值/解包数据流）→ `collect_ksources`（k 源 + 角色推断）→ `token_clauses` / `elt_matches_token`（方向性成员测试）→ `analyse_calls`（六形态塌缩 + 三类合法聚合）→ `analyse_output`（1-bit 出口 + 归因）→ 四信号合成 `CONFIRMED_K1BIT / SUSPECT / LEGAL_AGGREGATE / NO_SELFTEST`。标准库 `ast/hashlib/json/re`、只读、逐件 `sha256+bytes`、173 件秒级；§3.3 代码块即完整可粘贴版本。**它是静态候选器，不是确诊器**。

**(b) 能否通用化：能，方案（设计，未实现/未验证）**：把「S1 多输入源 → S2 有损归约 → S3 单 bit 出口 → S4 归因」抽象成**信息损失格**：`CARDINALITY_K → VEC_BOOL[k] → SCALAR_BOOL / SCALAR_POS → EXIT_CODE`，任何 `VEC→SCALAR` 的边记一次 `lossy edge`，边由算子语义表驱动（`any/all/sum/len/min/max/&=|=/and/or/first/next/count`）而不硬编码函数名。三张可插拔表：`SOURCE_RULES`（字面集合、`action=append`、glob、`parametrize`、文件清单）、`REDUCER_RULES`（保基数/保归因 vs 丢）、`ATTRIBUTION_RULES`（`hits[i]`、逐项 print、结构化 dict）。缺陷族 = profile：k→1bit 只是「lossy edge 上无 attribution」的一个配置；换配置可覆盖 `CHECK_FAMILY_LINEAGE.md:458-461` 的 `0==0` 空真 PASS、CWD 相对路径漂移、PASS 不绑定输入语料指纹、`require_all=True` AND 项不可归因。输出契约：`(rel, sha256, bytes, lossy_edge@line, source@line, exit@line, attribution=none)` + 负控自检，对齐 `_rs_carrier_scan.py:207-216` 的 R1–R6。**两阶段**：静态 lossy-edge 图给候选 → 动态「每根输入单独跑 + 坏针注入 + `AND_k`」给确诊；本任务按纪律只实现第一阶段。

**(c) 写检测器的准则**：
1. 先给**语义定义**并写成「可观测等价世界」反例（一根输入死掉仍能 PASS），不是「出现了某 token」。
2. 判据落在 **AST / 数据流**：量词变量、绑定来源、成员测试方向、保基数性、归因保留；禁止只靠正则下结论，禁止名字级判据（`CHECK_FAMILY_LINEAGE.md:449`）。
3. **必须带独立负控与正控**：`all()`、跨样本存在性、逐输入打印、保基数、无 `any()` 五类负控 + 六形态正控；负控要覆盖**改名 / 换写法 / 标量同名**变体，否则会重演 §3.4 的 `partial`。
4. **`has_k` 是硬门槛**：任何 `&=` / argmin / 三元分支都不得绕过 k≥2；否则产生实测假阳（`_kdv_probe3.py`）。
5. **输出分级**：`CONFIRMED / SUSPECT / LEGAL / NO_SELFTEST`，`SUSPECT` 不得冒充确诊（`CHECK_FAMILY_LINEAGE.md:338,440`）。
6. **可复核**：逐件 `sha256+bytes`、结果落 JSON、写域外只读、跑前跑后重核指纹（本会话 10/10 `mismatches=0`）、273 行保护快照 `mismatches=[]`。
7. **口径显式化**：任何计数写清「口径 + 全集 + 真值来源」；本件四件上 2/3/4、全库 28/40/46/48/49/54/40/42 全部标出处，不合并成一个数。
8. **不动被检脚本**：本会话 `git diff --name-only HEAD -- '*check_*.py' | wc -l = 0`。

**(d) 判不了什么 / 未验项（如实列）**：
1. **未做动态坏针注入、未跑被检门禁** ⇒ 不能确诊「坏针仍 PASS」；40 件 / 42 件都只是静态候选（`CHECK_FAMILY_LINEAGE.md:439,546` 亦标未验）。
2. **不能给「全库究竟多少件真缺陷」**：`CHECK_FAMILY_LINEAGE.md:331,338,440` 明示 40 件含 27 件字节相同副本 + 13 件已注入坏针的沙箱变体，「40 件全带同一缺陷」标 `unconfirmed`。
3. **SUSPECT 未逐件通读/未注入**：原器 6 件（3×`check_windows_cmds.py`、2×`check_fileoffset_axiom*.py`、`check_134_inc.py`）、修正版 1 件 `check_134_inc.py`，均标**未验**；`check_fileoffset_axiom*.py` 在 `:351` 有反掩蔽硬闸，修正版把它判静态候选这一结论标 **unconfirmed**。
4. **严格字面组合 28 件的完整 FP 名单与逐件成因未逐件复核**（只核了与 40 真值集合的交集 `TP=25/FP=3/FN=15` 及四件中 2 件 FN），标**部分未验**。
5. **不能判 D-27..D-30 裁决实质与制度层根因**（`CHECK_FAMILY_LINEAGE.md:462`「台账裸 exit=0 无状态字段」属制度层，非代码族）。
6. **不能覆盖别名 / 闭包 / `eval` / 跨模块常量 / `globals()` 注入等运行时 k 源**：`build_bindings` 是模块内、源码序、两轮传播；修正版的角色推断也只对静态可见的成员/探针调用生效。
7. **清单边界**：`.git/` 内部与符号链接目标未纳入（`:39,554` 标未验）。本会话实跑 `find . -type f -name 'check_*.py' | wc -l = 173`、`_cf_filelist.txt lines=173 live=173 missing=0 unique=173`；**未**用 `Path.rglob` 全树比对独立复算「173 是否等于当前活树全集」（编排方【设计】称 120 s 未完成被中止，本会话未重跑该检查）。
8. **通用信息损失格工具 (b) 仅设计，未实现、未验证**；修正版 `_kd_pasteable.py` 只对 §4.4 的 16 fixture + 7 文件 + 173 件静态集合验证过，未做动态阶段，不宣称零误报。
9. 编排方【设计】自报 `ranCommands=33`、【复核】自报 `ranCommands=42`，均无日志，本会话**未验**条数；本会话实跑命令与输出已逐条写在 §2、§4，可复核。
"""

out = DOC.replace("<<<CODE>>>", CODE.rstrip("\n"))
raw = out.encode("utf-8")
(WD / "K1BIT_DETECTOR.md").write_bytes(raw)  # exact LF bytes, no Windows newline translation
print("WROTE", (WD / "K1BIT_DETECTOR.md").as_posix(), "bytes=", len(raw))
