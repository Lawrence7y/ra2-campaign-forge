# k→1bit 语义级检测器 — 设计与验证回件

写域：`lead/k1bit_detect_20261109/`（本任务唯一写域，前缀 `_kd_`）
零真机 / 零采样代码 / 未改任何被检脚本 / 未 commit / 未 push。
Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib.sha256`。

## 0. 被核对象绑定行（复核方指纹逐件核对）

编排方给的 10 件指纹，本会话用 `python -I -X utf8 -c`（`hashlib.sha256` 读 bytes）逐件核对：
10/10 `OK`，`mismatches=0`；全部跑完后又重核一次，仍 `mismatches=0 / UNCHANGED`。

被核对象 SHA256 = e5098b23732141df0fcb48631cab5642cb4ec054f47564a2a0233fa6e10539f8，字节数 = 82856
（`lead/check_family_20261109/CHECK_FAMILY_LINEAGE.md`）

被核对象 SHA256 = 17e83a81ecf0cca951825d3191bb0772011de1af3269d793922a8db068e5c3c2，字节数 = 130498
（`lead/check_family_20261109/_cf_detect_out.json`）

被核对象 SHA256 = e5edea52c3f1959796c8132e7f4d04418c9704f992a59df84ec189d564b800fa，字节数 = 149737
（`lead/check_family_20261109/_cf_census_out.json`）

被核对象 SHA256 = 832355993a2b0f50bbc77c85f52531862d62fc01eab511cd29d78d06c860ffc1，字节数 = 7587
（`lead/check_family_20261109/_cf_detect.py`）

被核对象 SHA256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c，字节数 = 3764
（`lead/d27_ruling_20261106/check_d27.py`）

被核对象 SHA256 = 5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268，字节数 = 4539
（`lead/d28_ruling_20261106/check_d28.py`）

被核对象 SHA256 = 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14，字节数 = 3906
（`lead/d29_ruling_20261106/check_d29.py`）

被核对象 SHA256 = 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd，字节数 = 3926
（`lead/d30_ruling_20261106/check_d30.py`）

被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
（`lead/PENDING_DECISIONS.md`）

被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
（`lead/GOAL_THREE_TARGETS_20261018.md`）

## 1. 第一步 — 复核漏检（独立实跑）

实跑命令（repo root）：
```
python -I -X utf8 -c "import ast,re,hashlib; ... LIT=re.compile(r'any\([^)]*for[^)]*in'); ..."
```

### (a) 四件 `any()` 的 AST 参数类型（逐件，与编排方【四件 any 的 AST 形态】完全一致）

| 件 | `any()` 调用 | 参数 AST 类型 | `ast.unparse` 实参 |
|---|---|---|---|
| `check_d27.py` | `:86` | **GeneratorExp** | `keyword in body for body in bodies.get(title, []) for keyword in keywords` |
| `check_d28.py` | `:97` | **Name** | `present` |
| `check_d29.py` | `:84` / `:87` | **GeneratorExp** / **Name** | `word in body for word in words` / `matches` |
| `check_d30.py` | `:84` / `:87` | **GeneratorExp** / **Name** | `word in body for word in words` / `matches` |

直读落点：`check_d27.py:86-87`；`check_d28.py:96-97`（`:96 present = [word in body for word in words]`、`:97 if not (all(present) if require_all else any(present)):`）；`check_d29.py:82-87`、`check_d30.py:82-87`。

### (b) 字面筛（生成器式 `any\([^)]*for[^)]*in`）实测

四件逐件命中数：d27=1、d28=**0**、d29=1、d30=1 ⇒ **3/4**（漏 d28）。
同一正则在 173 件上命中 **49** 件（`_kd_literal_vs_semantic_out.json:screens.L1_GENERATOR_FORM.n_hits`）。
另有 `_cf_census.py:55-59` 的窄口径 `orch_any_line`：四件同为 3/4，173 件命中 48（与 `_cf_census_out.json:summary.n_orch_any=48` 一致）。

### (c) 语义级（AST）能捞到几件

四件 **4/4**（零漏）。173 件：`CONFIRMED_K1BIT=40 / SUSPECT=6 / LEGAL_AGGREGATE=80 / NO_SELFTEST=47`。
40 件集合与 `_cf_detect_out.json:confirmed` **完全相等**（`identical=True`, `cf-only=[]`, `kd-only=[]`）。

### (d) 漏检率算式

- 任务背景所述「四件确诊同族只捞到 2 件」：那是**严格字面组合**（`orch_any` 且 `print("PASS` 立即开头，`_cf_census.py:80-81`）口径，`_cf_census_out.json:summary.n_combo_orchany_passliteral=28`，该 28 件清单（`:summary.combo_orchany_passliteral`）里四件只有 d29、d30 两件 ⇒ `2/4`，漏检率 `(4-2)/4 = 2/4 = 50%`。d27 漏因是 `:100` 为 f-string PASS（`print(f"PASS: ...")`），d28 漏因是 `:97` 为 `any(present)`。见 `CHECK_FAMILY_LINEAGE.md:336`。
- 本任务给出的生成器式正则单用：四件 `3/4` ⇒ 漏检率 `(4-3)/4 = 1/4 = 25%`。
- 173 件全库（L1 对 40 件真值）：`FN=4`（d28 + 3 件 d28 沙箱副本），`TP=36`，漏检率 `FN/(TP+FN) = 4/40 = 10%`。
- ★ 一般宽口径 `any\(` + `^\s*print\(.*PASS`：四件 `4/4`、173 件命中 54、`FN=0`（`CHECK_FAMILY_LINEAGE.md:329` 的 54 件，本会话独立复算一致）⇒ **「字面筛必然漏 d28」只在窄口径下成立，如实标注**：`CHECK_FAMILY_LINEAGE.md:336` 已把该叙事标 `unconfirmed`。本回件三个口径全部列出，不改写编排方结论。

## 2. 第二步 — 语义级检测器设计（核心）

### (a) ★ 语义定义（不是「用了 any()」）

`CHECK_MASKING_INJECT.md:447-450` 的抽象，操作化为：

> 自检有 **k≥2 个同类输入**（needle / keyword / pattern / case / token），待证命题是
> `∀i: 输入_i 有效`（`DISTINGUISHABLE_PASS = AND_k(真实逐输入自检)`）；
> 但代码内部用**存在量词**合成 `covered(x) = ∃i: match(input_i, x)`，
> 再把 k 个输入的存活情况**压成 1 bit**（`any()` / `if not any(...)` / `ok &= good` /
> `min(pos)` 只留位置 / 单行 `PASS` / 单个 `SELF_TEST = PASS`），
> **不保留** `hits=[命中下标]` 之类逐输入溯源，也没有逐输入打印。
> ⇒ 「输入_1 全死、但每个样本都被输入_{j≠1} 命中」与「k 根全正常」**观测等价**；
> **逐输入可归因 = 否**。

可操作判据 = 四个同时成立的**数据流**信号（`_kd_detect.py` 实现）：

| 信号 | 语义内容 | 数据流判定 |
|---|---|---|
| **S1 KSOURCE** | 存在 k≥2 个同类输入 | 字面字符串集合 / 需求表行（元组第 3 项）/ `argparse action="append"`；经 `Assign` / `for` 解包 / 形参→实参两轮传播（`build_bindings`、`collect_ksources`） |
| **S2 COLLAPSE** | ∃ 塌缩到 1 bit，且量词变量**恰好遍历 S1 的那 k 个输入** | `any(GeneratorExp/ListComp)` 元素为对 token 变量的成员测试；`any(Name)` 且 Name 绑定到该列表推导；`IfExp` 三元 OR/AND 分支；`min()/max()` argmin；`ok &= good` / `ok = ok and good` |
| **S3 ONEBIT** | 聚合出口、无逐输入输出 | `PASS` / `SELF_TEST` 单行 print + `return 0/1` / `0 if ok else 1` / `SystemExit(main())`；无「循环变量是 token 变量」的逐输入 print；无 `hits[]` 保留 |
| **S4 LEGAL** | 合法聚合排除 | `all()` ⇒ AND_k；`any()` 量词遍历**样本/正文**且谓词是单个固定字面 ⇒ 合法存在性；`sum/len/sorted` ⇒ 保基数；有 `hits[]` / 逐输入打印 ⇒ 有归因 |

**关键：** 判据看的是「量词遍历什么、元素在测谁、结果留了几 bit」，不是 `any` 这个 token，也不是函数名。

### (b) 六种形态覆盖（逐形态给实测落点）

| 形态 | 实现入口 | 实测命中 |
|---|---|---|
| 生成器式 `any(x in y for ...)` | `analyse_calls` → `OR_COLLAPSE_gen` | d27:86、d29:84、d30:84、_rs:229；173 件 `OR_COLLAPSE_gen` 共 36 处 |
| 列表绑定后 `any(present)` | `OR_COLLAPSE_bound_list`（`resolve(name,bindings)` 回溯 `ListComp`） | d28:97；4 处 |
| 三元式 OR/AND 混合 | `TERNARY_OR_BRANCH`（`ast.IfExp` 的 `any` 分支 + 回溯）+ `OR_COLLAPSE_ternary_list` | d28:97、d29:87、d30:87；4 + 25 处 |
| `ok &= good` 累积 | `BIT_ACCUM_AugAssign_BitAnd` | `_rs_carrier_scan.py:343` |
| `min(pos)` argmin 反向掩蔽 | `ARGMIN_REVERSE_MASK` | `_rs_carrier_scan.py:165` `min((line.find(n) for n in needles if n in line), default=-1)` |
| 单行 PASS 出口且无逐输入打印 | `analyse_output` | 四件 `:100/:115/:105/:105`；`_rs:346` 单 `SELF_TEST = PASS`、`:349 return 0 if ok else 1` |

### (c) 可粘贴实现

完整实现落 `lead/k1bit_detect_20261109/_kd_detect.py`（AST 遍历 + 数据流判断，标准库 `ast/hashlib/json/re`，无正则字面判缺陷）。最小骨架：

```python
import ast, re

def build_bindings(tree):                 # name -> [(lineno, value_expr)]
    b = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    b.setdefault(t.id, []).append((n.lineno, n.value))
    return b

def collect_ksources(tree, b):            # S1: 字面集合 / 需求表行 / action=append
    tok = {}
    for name, vals in b.items():
        for v in vals:
            if isinstance(v, (ast.Tuple, ast.List)):
                ss = [e.value for e in v.elts
                      if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                if len(ss) >= 2 and len(ss) == len(v.elts):
                    tok[name] = len(ss)
    for n in ast.walk(tree):              # for number,title,words,require_all in requirements
        if isinstance(n, ast.For) and isinstance(n.target, ast.Tuple):
            srcs = [n.iter] + (b.get(n.iter.id, []) if isinstance(n.iter, ast.Name) else [])
            for s in srcs:
                if isinstance(s, (ast.Tuple, ast.List)) and s.elts and all(
                        isinstance(r, (ast.Tuple, ast.List)) for r in s.elts):
                    for r in s.elts:
                        for e in r.elts:
                            if isinstance(e, (ast.Tuple, ast.List)) and len(e.elts) >= 2:
                                i = r.elts.index(e)
                                tok[n.target.elts[i].id] = len(e.elts)
    return tok

def is_token_match(elt, tvars):           # S2 元素在测 token 变量本身
    names = {x.id for x in ast.walk(elt) if isinstance(x, ast.Name)}
    return isinstance(elt, ast.Compare) and bool(names & tvars)

def collapses(tree, tok, b):              # S2 五种塌缩（含 Name 回溯 / IfExp / min / &=）
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "any":
            a = n.args[0] if n.args else None
            if isinstance(a, (ast.GeneratorExp, ast.ListComp)):
                for g in a.generators:
                    src = g.iter.id if isinstance(g.iter, ast.Name) else getattr(g.iter, "attr", "")
                    tv = {t.id for t in ast.walk(g.target) if isinstance(t, ast.Name)}
                    if src in tok and is_token_match(a.elt, tv):
                        out.append((n.lineno, "OR_COLLAPSE_gen", src, tok[src]))
            elif isinstance(a, ast.Name):           # any(present) / any(matches)
                for _, v in b.get(a.id, []):
                    if isinstance(v, ast.ListComp):
                        for g in v.generators:
                            src = g.iter.id if isinstance(g.iter, ast.Name) else ""
                            if src in tok:
                                out.append((n.lineno, "OR_COLLAPSE_bound_list", a.id, tok[src]))
        if isinstance(n, ast.IfExp):                # all(...) if require_all else any(...)
            for br in (n.body, n.orelse):
                if isinstance(br, ast.Call) and isinstance(br.func, ast.Name) and br.func.id == "any":
                    out.append((n.lineno, "TERNARY_OR_BRANCH", "", "?"))
        if isinstance(n, ast.AugAssign) and isinstance(n.op, ast.BitAnd):
            out.append((n.lineno, "BIT_ACCUM&=", "", "?"))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("min", "max"):
            if n.args and isinstance(n.args[0], ast.GeneratorExp):
                out.append((n.lineno, "ARGMIN_REVERSE_MASK", "", "?"))
    return out

def is_legal(n):                           # S4 合法聚合（不报）
    return (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and (n.func.id == "all"                       # AND_k，无 OR 损失
                 or n.func.id in ("sum", "len", "sorted")))  # 保基数
```

跑法：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/k1bit_detect_20261109/_kd_detect.py D:/Project/ra2-campaign-forge`

### (d) ★ 真 k→1bit vs 合法聚合的区分（这是判据的核心，不是 `all()` 一声了事）

判据是 **「量词遍历的对象」+「是否保基数」+「是否保归因」** 三件事：

1. `all(word in body for word in words)` **合法**：`all()` 要求 k 根全部为真，死掉任何一根都会让 `PASS` 变 `FAIL` ⇒ 观测可区分，等价 `AND_k`。四件里的 `all()` 全部记为 `legal: AND_aggregate`（`check_d28.py:97` `all(present)`、`check_d29.py:83` / `check_d30.py:83` `all(word in body for word in words)`）；缺陷来自**同一表达式里的 `else any(...)` 分支**，不是 `all()`。故「有 `any()` 就报、见 `all()` 就不报」都错：30 件同时含 `all()` 与 `any()`，其中 29 件仍 `CONFIRMED`（`_kd_detect_out.json` 逐件）。
2. `any("本次不授权" in body for body in bodies)` **合法**：量词遍历的是**样本/正文**（`body/bodies`），谓词是**一个固定字面**，语义是「是否存在某份文档含这个串」，k=1，无从掩蔽。`check_d26.py:85,87,90` 三个 `any()` 全属此类 ⇒ `LEGAL_AGGREGATE`（与 `CHECK_FAMILY_LINEAGE.md:345` 的确定判断一致，并修掉 `_cfv_census.py` 把 d26 误判 `CONFIRMED` 的破口，见 `:451`）。
3. `any(word in body for word in words)` **缺陷**：量词遍历的是 **k≥2 词表本身**，谓词随词变 ⇒ `∃i` 覆盖 `∀i`。
4. `len(hits)` / `sum(...)` / `sorted(...)` **合法**：保基数或保序，不是 1 bit。
5. 有 `hits=[...]` / `hitset` / 逐输入 `print` **合法**：逐输入归因保留。自测 N5 即此。
6. `min(pos)` **缺陷（反向掩蔽）**：只留一个位置，丢掉「哪个 needle 命中」；`ok &= good` 把 6 条负控压成一个 bit，同理。

即：**合法 = `AND_k` / 单输入存在性 / 保基数 / 保归因；缺陷 = 对 k≥2 输入做 `∃` 塌缩且丢归因。**

## 3. 第三步 — 验证检测器

### (a) 四件全中
实跑 `_kd_detect.py --one` 逐件：d27 / d28 / d29 / d30 全 `CONFIRMED_K1BIT`，四件 `has_k=True`、`onebit_exit=True`、`attribution=False`。四件逐件 `tokens`/`collapse` 见 `_kd_detect_out.json:rows`。

### (b) `_rs_carrier_scan.py` 识别
`python -I -X utf8 .../_kd_detect.py ... --one lead/refsync_scope_20261109/_rs_carrier_scan.py` ⇒
`CONFIRMED_K1BIT`，三处塌缩全抓：`:165 ARGMIN_REVERSE_MASK`（`min`）、`:229 OR_COLLAPSE_gen`（`any(n in txt for n in a.needle)`）、`:343 BIT_ACCUM_AugAssign_BitAnd`（`ok &= good`）；`tokens={"needle": argparse_action_append, "needles": param_from_argparse_action_append}`（`k=runtime`）；出口 `:346 SELF_TEST = PASS` / `:349 return 0 if ok else 1`。与 `CHECK_MASKING_INJECT.md:441`、`CHECK_FAMILY_LINEAGE.md:457` 的代码级锚点一致。

### (c) ★ 全库 173 件，与 40 件是否一致
`python -I -X utf8 .../_kd_detect.py D:/Project/ra2-campaign-forge` ⇒
`n=173, counts={NO_SELFTEST:47, LEGAL_AGGREGATE:80, CONFIRMED_K1BIT:40, SUSPECT:6}`。
与 `_cf_detect_out.json` 比对实跑：`cf confirmed=40, kd confirmed=40, identical=True, cf-only=[], kd-only=[]` ⇒ **完全一致（同一 40 件集合）**。
口径差：`_cf_detect.py` 报 `CONFIRMED 40 / SUSPECT 3 / NOT_FAMILY 130`；本器把 `check_d26.py` 判 `LEGAL_AGGREGATE`（依 §2(d) 第 2 条，排除），另把 3 件 `check_windows_cmds.py` 与 `check_134_inc.py` 列为 `SUSPECT`（有 k 词 `∃` 塌缩但 S1 的 k 未静态确证 / 无干净 1-bit 出口，不冒充确诊）。
`SUSPECT 6` 逐件列在 `_kd_detect_out.json:suspect`。

### (d) ★ 误报验证（`all()` 的件必须不报）
- 全库实跑：含 `all()` 的文件 31 件；其中**只含 `all()` 不含任何 `any()`** 的 1 件 = `out/re_work/agy_patchhex/bytes/check_bytes.py:88 is_hex_rep = all(c in '0123456789ABCDEFabcdef' for c in rep_clean)` ⇒ 判 `LEGAL_AGGREGATE`，**0 件被报 CONFIRMED / SUSPECT**。
- 30 件同时含 `all()` 与 `any()`：29 件 `CONFIRMED` 且逐件确认其 `legal` 含 `AND_aggregate`（缺陷来自 `any` 分支），1 件 `LEGAL_AGGREGATE`。即 `all()` 自身从未触发报警。
- 合成负控（`_kd_selftest.py`，10 个 fixture 全部在内存里、不落盘到写域外、不执行）：`n=10, passed=10, failed=0, all_negatives_correct=true, all_positives_correct=true`。六个负控：`N1 all(GenExp)`、`N2 all(bound_list)`、`N3 any over samples 单字面`、`N4 len(hits) 保基数`、`N5 逐输入打印 + hits[]`、`N6 d25 式无 any()` 全部 `LEGAL_AGGREGATE`；四个正控 P1 生成器 / P2 绑定列表 / P3 三元 / P4 `&=`+argmin+action=append 全部 `CONFIRMED_K1BIT`。
- 真实 `LEGAL_AGGREGATE` 校准件：`check_d25.py`（无 `any()`, `CHECK_FAMILY_LINEAGE.md:344`）、`check_d26.py`（跨 body 存在性, `:345`）、`check_feasibility.py`（逐项 `[PASS] 检查项 N`, `:349`、本会话直读 `:119,149,164,...`），均不报。

## 4. 第四步 — 量化「字面 vs 语义」一般差距

实跑：`python -I -X utf8 .../_kd_literal_vs_semantic.py D:/Project/ra2-campaign-forge`
（同一 173 件 bytes，以语义 `CONFIRMED_K1BIT` 40 件为真值）

### (a) 命中数

| 筛法 | 173 件命中 | 四件命中 |
|---|---|---|
| L1 生成器式 `any\([^)]*for[^)]*in` | **49** | 3/4 |
| L2 `orch_any_line`（`_cf_census.py:55-59`） | **48** | 3/4 |
| L3 宽口径 `any\(` + `print(.*PASS`（`CHECK_FAMILY_LINEAGE.md:329`） | **54** | 4/4 |
| 严格字面组合（census `n_combo_orchany_passliteral`） | **28** | 2/4 |
| **语义级（本器）** | **40**（+6 SUSPECT） | **4/4** |

L3 的 54 与 `CHECK_FAMILY_LINEAGE.md:329` 独立复算一致；L2 的 48 与 `_cf_census_out.json:summary.n_orch_any=48` 一致；28/46/40 三个 census 组合值同 `:327-329` 一致。

### (b) ★ 字面筛的假阴性（漏）与假阳性（误）

| 筛法 | TP | **FN（漏）** | **FP（误）** | TN | 漏检率 FN/(TP+FN) | 误报率 FP/(TP+FP) |
|---|---|---|---|---|---|---|
| L1 生成器式 | 36 | **4** | **13** | 120 | `4/40 = 10%` | `13/49 = 26.5%` |
| L2 orch_any_line | 36 | **4** | **12** | 121 | `4/40 = 10%` | `12/48 = 25%` |
| L3 宽口径 | 40 | **0** | **14** | 119 | `0/40 = 0%` | `14/54 = 25.9%` |
| 严格字面组合 28 | (见下) | | | | | |

- L1 的 4 件 FN 全部是 d28 形态：`check_d28.py` + 3 件 d28 沙箱副本（`_sp_sandbox/d28/...`、`_sp_sandbox/d28x/a/b/...` 的 baseline/injected），清单在 `_kd_literal_vs_semantic_out.json:screens.L1_GENERATOR_FORM.misses_confirmed`。
- L1 的 13 件 FP = 6 件 `SUSPECT` + 7 件 `LEGAL_AGGREGATE`，含 `check_d26.py`（跨 body 存在性）、`check_feasibility.py`（逐项打印）、`check_semantic_review.py` / `_r2.py`（带 `hits` 归因）等；L3 的 14 件 FP = 5 `SUSPECT` + 9 `LEGAL_AGGREGATE`。都是「写法像、语义不同」。
- 严格字面组合 28 件（`_cf_census_out.json:summary.combo_orchany_passliteral`，本会话逐件用 40 件真值集合复核）：**四件生产门禁口径**只含 d29、d30 ⇒ `FN=2/4 = 50%`（这正是背景所述「四件只捞到 2 件」）；**全库 40 件真值口径** `TP=25 / FN=15 / FP=3 / TN=130`，漏检率 `15/40 = 37.5%`、误报率 `3/28 = 10.7%`；3 件 FP 中 2 件落 `SUSPECT`。两个口径分母不同，都列出不合并。

### (c) 这个差距说明什么

1. **字面筛的口径决定结论，且口径不可证成。** 同一个「字面筛」在四件上可以是 `2/4`（严格组合）、`3/4`（生成器式）、`4/4`（宽口径）；`CHECK_FAMILY_LINEAGE.md:336` 已把「字面筛漏 d28/d27」标 `unconfirmed`，因为换一个宽口径零漏判。**靠挑正则来决定缺陷存在与否，本身不可复核。**
2. **漏与误不可同时靠调正则消掉。** 把 L1 放宽到 L3，`FN 4→0`，但 `FP 13→14` 不降反升；因为 `any` 这个字面 token 与「∃ 塌缩 k 个输入」没有必然联系。窄口径漏形态变体，宽口径把 `all()`/跨样本存在性/逐项打印件一起捞进来。
3. **假阴性是成族出现的。** L1 的 4 个 FN 全是同一个 d28 模板（含副本）；一处写法变化 ⇒ 该分支整族消失。grep 审计会系统性地看不见「换过写法的那一支」。
4. **假阳性会把合法件当缺陷。** 25–26% 的误报率意味着 4 件里约 1 件是 `all()` / 存在性检查 / 逐输入打印的合法件；若据此批量替换，会改动无辜脚本（`CHECK_FAMILY_LINEAGE.md:418` 已警告会连带改动证据生产副本）。
5. **对「以后用 grep 做代码审计」的含义**：grep 只能当**召回用的候选枚举**（先圈范围、给行号，要求零遗漏时须用最宽口径并接受高 FP），**不能当判据、不能当确诊、不能当计数结论**。判据必须在 AST / 数据流层做；确诊还需动态坏针注入（`CHECK_MASKING_INJECT.md:457` 第 4 步 / `CHECK_FAMILY_LINEAGE.md:450`），本任务按纪律**未做**（零真机、不改被检脚本）。

### (d) 什么时候可以用字面筛 / 什么时候必须用语义筛

| 用字面筛（且只当候选） | 必须用语义筛 |
|---|---|
| 找**固定字面量**：某个 API 名、错误串、路径、commit hash、常量值；文本层可判定 | 判据涉及**同一个值的不同写法**（`any(gen)` / `any(Name)` / 三元 / `&=` / argmin） |
| 枚举**不受语法结构影响**的锚点：文件清单、行号、import、某条台账原文 | 判据是**量词/绑定/作用域**（`∃` 遍历谁、`Name` 绑到什么、是否保归因） |
| 快速定位后**人工逐件复核**，且明确标注「候选，非结论」 | 需要**精确计数 / 出确诊清单 / 做批量改动前的影响面** |
| 目标是「宁滥勿漏」的初筛，且后续有语义或动态步骤兜底 | 需要**区分合法聚合与缺陷**（`all()` vs `any()`、跨样本存在性 vs k 词 OR） |
| 输入只有**非代码文本**（md/txt/json 字段） | 代码会被重构 / 改名 / 复制成沙箱变体（本库 40 件里 36 件是副本/注入变体） |

判据一句话：**只要「同一语义能否换写法」的答案是「能」，就必须用语义筛。** 本任务的四形态、以及 `CHECK_FAMILY_LINEAGE.md:449` 指出 `_cf_detect.py:54-55` 的 P4 名字级判据会被函数改名绕过，都是这条的实证。

## 5. 第五步 — 结论与建议

### (a) 最小可用版本（MVDet）

`_kd_detect.py` 的四个函数即可：`ast.parse` → `build_bindings`（赋值/解包数据流）→ `collect_ksources`（k 源：字面集合 / 需求表行 / `action=append` / 形参传播）→ `analyse_calls`（五种 ∃ 塌缩 + 三类合法聚合）→ `analyse_output`（1-bit 出口 + 归因检查）；四信号合成 `CONFIRMED_K1BIT / SUSPECT / LEGAL_AGGREGATE / NO_SELFTEST`。实测 173 件 ~1 秒级、标准库、只读、结果 JSON 带 `sha256+bytes` 可复核。**它是静态候选器，不是确诊器**（见 (d)）。

### (b) ★ 能不能做成通用工具（不只查 k→1bit）：能，方案

把「S1 多输入源 → S2 有损归约 → S3 单 bit 出口 → S4 归因是否保留」抽象成 **信息损失（information-loss）分析器**，用可插拔的 lattice 而不绑定 `any`：

- **值格**：`CARDINALITY_K`（k 个输入的集合/流）→ `VEC_BOOL[k]`（逐输入布尔）→ `SCALAR_BOOL`（1 bit）→ `SCALAR_POS`（argmin）→ `EXIT_CODE`。任何 `VEC→SCALAR` 的边记为一次 **lossy edge**，边由归约算子的语义表驱动（`any/all/sum/len/min/max/&=|=/and/or/first/next/count`），不硬编码函数名。
- **可插拔三张表**：① `SOURCE_RULES`（哪些 AST 形状产生多输入：字面集合、`action=append`、glob、`parametrize`、文件清单）；② `REDUCER_RULES`（哪些算子保基数/保归因，哪些丢）；③ `ATTRIBUTION_RULES`（哪些输出结构算保留逐输入：`hits[i]`、`per-item print`、结构化 dict）。
- **缺陷族 = 配置**：k→1bit 只是 `lossy edge 上没有 attribution` 的一个 profile；换配置即得别的族，例如 `CHECK_FAMILY_LINEAGE.md:458-461` 列的 `0==0` 空真 PASS、CWD 相对路径漂移、PASS 不绑定输入语料指纹、`require_all=True` AND 项不可归因。
- **输出契约**：每命中给 `(rel, sha256, bytes, lossy_edge@line, source@line, exit@line, attribution=none)` + 负控自检；与 `_rs_carrier_scan.py:10-27` 的 R1–R6 可复核性约定（内容寻址、逐出现计数、显式逐字比对、负控）对齐。
- **两阶段**：静态 lossy-edge 图给候选 → 动态「每根输入单独跑 + 坏针注入 + `AND_k`」给确诊（`CHECK_MASKING_INJECT.md:450`、`CHECK_FAMILY_LINEAGE.md:450`），绑定脚本 SHA256 与输入语料指纹。本任务按纪律**只实现第一阶段**。

### (c) 以后写检测器的准则

1. **先给语义定义再给实现**，定义必须能写成「可观测等价世界」的反例（一根输入死掉仍能 PASS），而不是「出现了某 token」。
2. **判据落在 AST/数据流**：量词变量、绑定来源、保基数性、归因保留；禁止只靠正则下结论。
3. **必须带负控与正控**：`all()`、跨样本存在性、逐输入打印、保基数、无 `any()` 五类负控 + 六形态正控（本器 `_kd_selftest.py` 10/10）。
4. **输出分级**：`CONFIRMED / SUSPECT / LEGAL / NO_SELFTEST`，`SUSPECT` 不得冒充确诊；静态命中不等于确诊（`CHECK_FAMILY_LINEAGE.md:338,440`）。
5. **可复核**：逐件 `sha256 + bytes`、结果落 JSON、写域外只读、跑后重核指纹（本会话 10/10 前后两次 `mismatches=0`）。
6. **口径显式化**：任何计数都写清「口径 + 全集 + 真值来源」；本任务四件上 2/3/4 三种字面结果、40/28/46/54 四个全库数字，全部标了出处，不合并成一个数。
7. **不要用名字级判据**（`CHECK_FAMILY_LINEAGE.md:449` 的 P4 破口）；不要动被检脚本（本任务 0 行改动）。

### (d) ★ 这条工作判不了什么（如实列）

1. **不能确诊「坏针仍 PASS」**：本任务是静态 AST/数据流，未做动态坏针注入、未跑被检脚本。四件「坏针仍 PASS」引自 `CHECK_MASKING_INJECT.md:183-365` 与 `STALE_PASS_INVENTORY.md:126-131` 的既有实跑，`CHECK_FAMILY_LINEAGE.md:439,546` 已标**未验**；本会话同样**未独立复现**。故 40 件只算静态候选，与 `_cf_detect.py` 的 40 件口径一致。
2. **不能给出「全库究竟有多少件真缺陷」的真实数字**：40 是 F1–F4 静态结构命中，`CHECK_FAMILY_LINEAGE.md:331,338,440` 明示含 27 件字节相同副本 + 13 件已注入坏针的沙箱变体，且「40 件全带同一缺陷」被标 `unconfirmed`。
3. **不能判 `SUSPECT 6` 的真伪**：6 件（3 件 `check_windows_cmds.py`、2 件 `check_fileoffset_axiom*.py`、`check_134_inc.py`）本会话未做哨兵注入、未逐件通读全部上下文，标**未验**，不冒充确诊也不排除。`check_fileoffset_axiom*.py` 在 `CHECK_FAMILY_LINEAGE.md:441` 同为 SUSPECT（带 GOLDEN/NAIVE_FLOOR/EXIT=3 反掩蔽硬闸）。
4. **严格字面组合 28 件的完整 FP 名单与逐件成因未逐件通读复核**（只复核了与 40 件真值集合的交集：TP=25/FP=3/FN=15，以及四件门禁中 2 件 FN），标**部分未验**。
5. **不能判 D-27..D-30 裁决的实质对错、也不能判制度层根因**（`CHECK_FAMILY_LINEAGE.md:462`「台账裸 exit=0 无状态字段」是制度层，非代码族）；四份裁决对自身 PASS 的零引用结论见 `:486-488`，本任务未复核。
6. **不能覆盖多文件 / 跨进程 / 运行时构造的输入源**：`build_bindings` 是模块内、源码序、两轮传播；别名、闭包、动态 `eval`/`getattr`、跨模块常量、`globals()` 注入的 k 源会漏。清单边界同 `_cf_filelist.txt`（173 件，含 `.dsh-watch/`、`.tmp/`、`.zcode-watch/`、`out/re_work/**` 自嵌套树；`.git/` 内部与符号链接目标未纳入，`CHECK_FAMILY_LINEAGE.md:39,554` 标未验）。本会话 `Path('.').rglob` 全树比对在 120 s 内未完成并被中止（win32 自嵌套树），故「173 是否等于当前活树全集」按编排方清单口径采用，**未用 rglob 独立复算**；只核了清单 173 条 `live=173 / missing=0`。
7. **不能替代人工复核合法聚合**：`is_token_source` 的 `TOKENISH` 命名启发式与 `SAMPLEISH` 分类在极少数命名不规范的件上可能误分；本器已用 S4 的 `all()` / 保基数 / 归因三条硬排除兜底，但不宣称零误报（合成负控 6/6、全库 `all()` 件 0 报是已验范围）。
8. **通用工具方案 (b) 只是设计，未实现、未验证**。

## 6. 产物清单（全部在写域）

| 文件 | 内容 |
|---|---|
| `lead/k1bit_detect_20261109/_kd_detect.py` | 语义级检测器（AST + 数据流），只读、写域外不改 |
| `lead/k1bit_detect_20261109/_kd_detect_out.json` | 173 件逐件 verdict + `sha256/bytes/tokens/collapse/legal/output` |
| `lead/k1bit_detect_20261109/_kd_selftest.py` | 10 个内存 fixture 正负控 |
| `lead/k1bit_detect_20261109/_kd_selftest_out.json` | `n=10 passed=10 failed=0` |
| `lead/k1bit_detect_20261109/_kd_literal_vs_semantic.py` | 三种字面筛复算 + 混淆矩阵 |
| `lead/k1bit_detect_20261109/_kd_literal_vs_semantic_out.json` | L1/L2/L3 的 TP/FN/FP/TN 与逐件清单 |
| `lead/k1bit_detect_20261109/_kd_REPORT.md` | 本回件（即本文件） |

## 7. 复核回件绑定行（本任务主被检对象的实跑指纹）

实跑：`python -I -X utf8 -c "import hashlib; print(hashlib.sha256(open(p,'rb').read()).hexdigest(), len(...))"`

被核对象 SHA256 = 5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268，字节数 = 4539
（`lead/d28_ruling_20261106/check_d28.py` — 字面筛漏检的那一件）

被核对象 SHA256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c，字节数 = 3764
（`lead/d27_ruling_20261106/check_d27.py` — 生成器式 + f-string PASS）

跑后重核：10 件编排方指纹 `mismatches=0 / UNCHANGED`；`git status --porcelain` 对绝对只读域仅显示目录为 `??`（会话开始即 `??`，未在本任务内产生新改动），无 commit / 无 push。
