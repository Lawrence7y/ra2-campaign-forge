# needle 变体归一化设计 · 漏检率量化 · 边界反例

- 日期 2026-11-09；角色：needle 变体归一化设计员。唯一写域 `lead/needle_norm_20261109/`，全部产出前缀 `_nn_`。
- 纪律：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；只读件一律未改；未 commit、未 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib。
- 本件**不改** `_rs_carrier_scan.py`、不改任何既有件；改进一律以「应当怎么改」给出，并给出可粘贴的替代实现片段（`_nn_norm.py` 中的 `normalize_line` / `find_norm` 已实跑验证）。

---

## 绑定行（被核对象复核，本会话 `python -I -X utf8 -c` + hashlib 全量自算，9/9 MATCH 编排方指纹）

被核对象 SHA256 = 9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57，字节数 = 16053
被核对象 SHA256 = aa2dbe945c9d8fdc6aebde849701393f6f8766c51b372329d588616781c2f83f，字节数 = 35782
被核对象 SHA256 = 83b215ccbbf2c3e221c247e7bd9c7c221fddcf9472977d2df8902bf1b94ec65e，字节数 = 49958
被核对象 SHA256 = 058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec，字节数 = 18980
被核对象 SHA256 = 1e4ceb37187cd12601ad03cdc02f0cf2ee624d1f6870c03c0e35d84cbcb40cfc，字节数 = 36097
被核对象 SHA256 = 8ccf9866ebd7860f03d71e939960e018fd0cfbbe6b94add04dd50f7004c11ac5，字节数 = 61819
被核对象 SHA256 = 724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e，字节数 = 45719
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

（顺序同编排方指纹块：`_rs_carrier_scan.py` / `_rs_CARRIER_MAP.md` / `REFSYNC_SCOPE_FIX.md` / `_ve_DRAFT_S609.md` / `S604_VERDICT_ENTRY_DRAFT.md` / `S604_REFSYNC_FULL.md` / `LEDGER_APPENDIX_DRAFT.md` / `PENDING_DECISIONS.md` / `GOAL_THREE_TARGETS_20261018.md`。）

---

## 第一步 · 复现 FAIL

### (a)(b) 实跑复现

命令（单 needle，含 `--include-refuting`；输出落 `lead/needle_norm_20261109/_nn_repro_single_out.txt`）：

```
cd D:/Project/ra2-campaign-forge && python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py" --needle "只能判「不可复现」" --include-refuting --max-depth 2 --ext .md > "D:/Project/ra2-campaign-forge/lead/needle_norm_20261109/_nn_repro_single_out.txt" 2>&1
```

输出（`EXIT=1`）：

```
R1 root = D:\Project\ra2-campaign-forge\lead ; max-depth = 2 ; exts = .md
needles = ['只能判「不可复现」']
scanned files = 631 ; carrier occurrences = 48 ; distinct files = 18
=== E. NEGATIVE-CONTROL SELF-TEST (R6) ===
  PASS  ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md:123 want=ASSERTION        got=ASSERTION
  PASS  ledger_appendix_20261108/_la_draft3_s604_gapdiff.md:25 want=ASSERTION        got=ASSERTION
  PASS  ledger_bound_20261109/LEDGER_BOUND_VOLUME.md:196 want=ASSERTION        got=ASSERTION
  PASS  ledger_bound_20261109/_lb_BOUND_VOLUME.md:129 want=ASSERTION        got=ASSERTION
  FAIL  s604_verdict_entry_20261109/_ve_DRAFT_S609.md:22 want=REFUTING_QUOTE   got=<not-scanned>
  PASS  ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md:215 want=ASSERTION        got=ASSERTION
SELF_TEST = FAIL
```

`--include-refuting` 的 C 段（`_nn_repro_single_out.txt` 第 316-317 行）只列 `:69` / `:70`：

```
   s604_verdict_entry_20261109/_ve_DRAFT_S609.md:69 role=REFUTING_QUOTE neg=原句
   s604_verdict_entry_20261109/_ve_DRAFT_S609.md:70 role=REFUTING_QUOTE neg=不再成立,已定谳,改为,更新：
```

`_ve_DRAFT_S609.md` 在整个输出里 `hits=2`（第 232 行 `FILE ... hits=2`），`:22` 仅作为「负控期望值」和 D 段说明文字出现，A/B/C 段均无该行 —— **不是判错角色，是根本没扫到**（`<not-scanned>`）。本会话 `python -I -X utf8 -c` 直读码位：`_ve_DRAFT_S609.md:22` 含 `只能判『不可复现』`（U+300E/U+300F），不含 `只能判「不可复现」`（U+300C/U+300D）；`:69`/`:70` 恰相反。

### (c) 为什么扫不到：是 needle 精确匹配，且**双重失效**

`_rs_carrier_scan.py` 有两道 needle 闸，都是**精确子串**：

1. **文件级预过滤** `_rs_carrier_scan.py:229`：
   ```
   if not any(n in txt for n in a.needle):
       continue
   ```
   整件无直角引号 needle ⇒ 整件跳过，连 `splitlines()` / `blocks_of()` / `classify_line()` 都不执行。
2. **行级闸** `classify_line()` `_rs_carrier_scan.py:165`：
   ```
   pos = min((line.find(n) for n in needles if n in line), default=-1)
   if pos < 0:
       return None
   ```
   行内无 needle ⇒ 直接返回 `None`，`main():239` `if not c: continue` ⇒ 该行不进 `carriers`。
3. **角色判定在闸之后** `_rs_carrier_scan.py:168-189`（`quoted_containing` / `NEG_LEX` / 各 role 分支）。`main():327-331` 的 `role_of()` 只在 `carriers` 里找，找不到就返回 `<not-scanned>`。

结论：**属后者，双重失效**。needle 一漏，R4 区块判定（`blocks_of`，:232）、R5 角色判定（`classify_line`，:238）、`needs_fix` 交集（:257-258）全部没有机会跑。`_rs_carrier_scan.py:317-319` 的文档甚至明写「§609 :22 是 KEPT in section A with risk=HIGH」，但实际在单 needle 下它连 A 段都进不去 —— 设计与实现脱节。

本会话直导 `classify_line()` 验证（`python -I -X utf8 -c`，`importlib` 加载脚本）：

```
['只能判「不可复现」'] -> None pos= -1
['只能判『不可复现』'] -> REFUTING_QUOTE pos= 162
['不能定位当年错误步骤'] -> REFUTING_QUOTE pos= 172
['只能判「不可复现」','不能定位当年错误步骤'] -> REFUTING_QUOTE pos= 172
```

### ★ 一处必须如实登记的「掩盖效应」（本会话额外发现）

编排方给的 FAIL 是**单 needle** 跑法；但 `REFSYNC_SCOPE_FIX.md:251` 登记的交付命令是**双 needle**（`--needle "只能判「不可复现」" --needle "不能定位当年错误步骤"`）。本会话按文档命令实跑（`_nn_repro_twoneedle_out.txt`）：

```
EXIT=0
  PASS  s604_verdict_entry_20261109/_ve_DRAFT_S609.md:22 want=REFUTING_QUOTE   got=REFUTING_QUOTE
SELF_TEST = PASS
```

原因：`:22` 含第二 needle `不能定位当年错误步骤`（`_ve_DRAFT_S609.md:22` 逐字含「不能定位当年错误步骤」），靠**另一条 needle** 被捞回，角色判定仍判对 `REFUTING_QUOTE`（输出第 413 / 547 行）。在盘交付件 `_fix_d2_out.txt` 的 E 段同样是 6/6 PASS。即：**交付自检 6/6 PASS 并不能证明「直角引号 needle 覆盖了 :22」**；它证明的是「两条 needle 的并集覆盖了 :22」。这正是「负控覆盖不足」的隐蔽形态 —— 单 needle 才暴露真漏检。此发现不改变 FAIL 成立，反而加重了第五步「自检必要性」的论据。

---

## 第二步 · 漏检率量化（六变体全量独立核对）

脚本 `_nn_variants.py`；命令：

```
cd D:/Project/ra2-campaign-forge && python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/needle_norm_20261109/_nn_variants.py" > "D:/Project/ra2-campaign-forge/lead/needle_norm_20261109/_nn_variants_out.txt" 2>&1
```

输出 `scanned files = 631`，与编排方 `files: 631` 一致；`ORCH_VERIFY_ALL = MATCH`（各变体文件数 + detail 中每个 `(file,line)` 锚点全数在我方命中集合内）。

### (a) 六写法命中文件数（逐种，附行数）

| 变体 | needle | 命中文件数 | 命中行数 | 与编排方 |
|---|---|---:|---:|---|
| angle_corner | `只能判「不可复现」` | **18** | 48 | MATCH |
| curly_corner | `只能判『不可复现』` | **16** | 34 | MATCH |
| curly_double | `只能判“不可复现”` | **0** | 0 | MATCH |
| no_quote | `只能判不可复现` | **7** | 9 | MATCH |
| half_paren | `只能判(不可复现)` | **0** | 0 | MATCH |
| no_punct | `只能判 不可复现` | **0** | 0 | MATCH |

逐变体的**全量文件/行明细**见 `_nn_variants_out.txt:13-65`（编排方只给了 8 个文件的 detail 片段，我方补全了 18/16/7 件的全部行号）。

### (b) 漏检率

按 `(file,line)` 为单位（符合 R2 `occurrence`，`_rs_carrier_scan.py:15-17`）：

```
angle_corner only: files=18 lines=48
union(all 6)     : files=22 lines=88
missed files     : 4 (= 18.18% of union)
missed lines     : 40 (= 45.45% of union)
```

- 只扫直角引号：**漏 4 个文件 / 40 行**；文件级漏检率 18.18%（4/22），行级漏检率 **45.45%**（40/88）。基线召回率仅 54.55%（行）/ 81.82%（文件）。
- 漏掉的 4 个文件（`_nn_variants_out.txt:73-77`）：`ledger_bound_20261109/_lb2_TEMPLATE.md`（:152/:202）、`s604_attribution_20261108/S604_ATTRIBUTION.md`（:138）、`s604_script_gap_20261109/S604_SCRIPT_GAP.md`（:55/:56）、`s604_script_gap_20261109/_sg_FINDINGS.md`（:21）。
- 40 条漏检行的逐行清单 `file:line <- 变体` 见 `_nn_variants_out.txt:78-118`；其中 31 行来自 `curly_corner`、9 行来自 `no_quote`（`:119-125`）。
- **注意 18/16 不是 34**：`curly_corner` 的 16 个文件里只有 0 个是直角引号完全没碰过的独立文件？不对 —— 是 4 个（见上），因为 `curly_corner` 与 `angle_corner` 在 12 个文件上共现，另 4 个文件是纯弯引号/无引号。按行算则是 31 行新增（34 行里有 3 行与直角引号同行共现，见 (d)）。

### (c) 分类：引号变体 vs 超出口径

| 类 | 变体 | 性质 | 归一化能否解决 |
|---|---|---|---|
| **引号变体（3 类）** | `angle_corner` / `curly_corner` / `curly_double` | 仅包裹符的**字符类别**不同（`「」` U+300C/D ↔ `『』` U+300E/F ↔ `“”` U+201C/D），核心文字 `只能判…不可复现` 与「有引号」这一结构不变 | **能**：L1 引号类归一覆盖 3/3（`_nn_norm_out.txt:5-11`），其中 `curly_double` 语料中 0 命中，属「应有但当前为零」的负控类 |
| **去引号（1 类）** | `no_quote` `只能判不可复现` | **引号 span 消失**，不是换字符；R5 的 `quoted_containing()`（`:110-114`）依赖成对引号跨度判角色，去引号直接改变 role 语义 | **不能**由引号归一解决；需单独的「无引号裸串」规则，且必须重新判角色 |
| **换括注（1 类）** | `half_paren` `只能判(不可复现)` | 半角括号，语料 0 命中；属另一种包裹符体系 | 不能（且无实据表明项目需要） |
| **插空白（1 类）** | `no_punct` `只能判 不可复现` | 空白插入 + 无引号；属分词/排版差异 | 不能；空白归一属 L2，本项目按码位逐字比对（见 `GATE_LITERAL_MATCH_POSTMORTEM.md:70`） |

即：**6 类里只有 3 类是引号变体**（占 union 79/88 行 = 89.8%），`no_quote` 的 9 行（10.2%）是另一性问题，`half_paren`/`no_punct` 在语料中为 0。把它们混为一谈去「一刀切归一」就是过度归一（第四步反例 CE1/CE6/CE7）。

### (d) 共现与去重（必须想清楚）

- **文件级共现**：14 个文件被 >1 变体命中（`_nn_variants_out.txt:128-142`），例如 `s604_verdict_entry_20261109/_ve_DRAFT_S609.md` 同时中 `angle_corner`(69,70) / `curly_corner`(22,46,53) / `no_quote`(54)。**文件数不可相加**：18+16+7=41 ≫ 真实并集 22。
- **行级共现（真正会重复计数）**：3 个 `(file,line)` 同时中两种变体（`_nn_variants_out.txt:143-150`）：
  - `REFSYNC_SCOPE_FIX.md:17` ← angle+curly（且各自出现 2 次，共 4 个字面串，`:145-146`）
  - `_rs_CARRIER_MAP.md:60` ← angle+curly（angle 出现 2 次）
  - `_rs_CARRIER_MAP.md:188` ← angle+curly
- **同一行同变体多次出现**：3 处（`:154-156`），如 `REFSYNC_SCOPE_FIX.md:17` 的 angle 与 curly 各 x2。
- **去重规则**：单位必须是 `(file, line)` 的**集合**，不是「每个 needle 各计一次」；`48+34+0+9+0+0 = 91` 个「变体-行」对，去重后 **88 行**（差 3 = 上述 3 个行级共现）。归一化后同一行内多个字面串命中仍只记 1 个 occurrence，但**每个命中偏移要单独保留**以便回溯原文位置（`_nn_norm_out.txt:33-37` 实跑 85 个映射命中，`all(orig_slice == reported_text) = True`）。这也与 R2「one sentence copied into N compilations = N carriers，per-line preserves block membership」一致：行内重复不新增 carrier，但行内不同句子若分属不同区块（本语料无此例）需按偏移再分。

---

## 第三步 · 归一化方案

### (a) 归一到什么层次（逐层给理由）

| 层 | 内容 | 是否采用 | 理由 |
|---|---|---|---|
| **L0** | 不做归一，人工列 needle 变体 | 否 | 正是本次 FAIL 的根因；`REFSYNC_SCOPE_FIX.md:227` 自己写过「变体短语靠人工列且无负控，漏了哪类自己不知道」，结果自己仍栽在此处 |
| **L1（采用）** | **只归一「引号类字符」**：`「『“‘` → 左引号哨兵；`」』”’` → 右引号哨兵；`` ` " ' `` → 成对哨兵。1:1 保长替换，其它码位原样 | **是** | 覆盖 3/3 引号变体；不增删字符 ⇒ 位置恒等映射；保留「有引号」这一结构 ⇒ R5 角色判定仍可在原文上跑；不触碰核心文字 ⇒ 不会把不同命题并成一句 |
| **L2** | 空白归一（删空格 / 全半角空格 / 换行折行） | 否 | 项目按码位逐字比对，`GATE_LITERAL_MATCH_POSTMORTEM.md:70` 专列「反引号/换行拆断标识符」为必须区分的形态；`no_punct` 在语料 0 命中，无收益有风险（反例 CE6） |
| **L3** | NFKC 全半角 / 兼容字符归一 | 否 | 会把全角 `ＡＰＰＲＯＶＥ＿ＳＣＯＰＥ` 并成半角 `APPROVE_SCOPE`（`_nn_counterexamples_out.txt:37-45` 实跑 MERGED=True），项目门禁按字面量区分，属实质错误 |
| **L4** | 去标点 / 删引号 / 顿号逗号统一 | 否 | 改变引号跨度和句子边界，直接毁掉 R5 的 `ASSERTION` vs `REFUTING_QUOTE` 判据（CE1/CE2/CE5/CE7） |
| **L5** | 近义词 / 模糊匹配 / 编辑距离 | 否 | `不可复现` ≠ `不可复原`，真实语料有 5 行「不可复原」（`_nn_norm_out.txt:81-86`），是不同命题（CE3） |
| **补充轨（不归一，显式列举）** | 对 `no_quote` 这类「结构变体」，用一个**独立的、显式的**正则族 `只能判[「『“(]?不可复现[」』”)]?` 单独召回，并**强制重新判角色** | 是（作为召回，不是归一键） | 9 行真实存在；它们不是引号变体，硬塞进 L1 会让 `只能判不可复现` 与 `只能判「不可复现」` 同键 ⇒ 裸断言与引文混淆 |

**结论：归一化层次 = L1 只归一引号字符；空白/全半角/标点/近义词一律不归一；`no_quote` 走显式召回轨并保留独立角色判定。** L1 实跑召回 79 行 / 22 文件（`_nn_norm_out.txt:17-20`），= `angle+curly+curly_double` 三变体精确并集（`L1 == raw(angle+curly+curlydouble) union ? True`），**零假阳**；相对六变体全集仍余 9 行（10.23%）由补充轨处理，明细见 `_nn_norm_out.txt:22-31`。

漏检率变化（量化）：**基线的行级漏检率 45.45%（40/88）→ L1 后 10.23%（9/88）→ L1+补充轨 0%（0/88）**；文件级 18.18%（4/22）→ 0%（0/22）。

### (b) 可粘贴实现片段（归一化函数 + 用法，位置可回溯）

已在 `_nn_norm.py` 实跑（`FIXTURE_SELF_TEST = PASS`，`_nn_norm_out.txt:98-109`；85 个映射命中全部 `orig_slice == reported_text`，`:33-37`）。关键设计：**每个原文码位替换为恰好一个归一码位**，故 `norm[j]` 恒对应 `line[j]`，`idx_map` 是恒等映射 —— 命中偏移无需任何重算即可回溯原文行号与原文片段。

```python
# ---- L1：只归一引号类字符，1:1 保长，带位置映射 ----
OPEN_Q, CLOSE_Q, SYM_Q = "\x01", "\x02", "\x03"   # 私有哨兵，不与正文冲突
QUOTE_OPEN  = "「『“‘"
QUOTE_CLOSE = "」』”’"
SYMMETRIC   = "`\"'"

def normalize_line(s):
    """返回 (norm, idx_map, orig_delims)。norm 与 s 等长；idx_map[j] = 原文下标 j。
    orig_delims[j] = 原引号字符（非引号为 None），供 R5 角色判定回查原始包裹符。"""
    out, idx, dels = [], [], []
    for j, c in enumerate(s):
        if   c in QUOTE_OPEN:  out.append(OPEN_Q);  dels.append(c)
        elif c in QUOTE_CLOSE: out.append(CLOSE_Q); dels.append(c)
        elif c in SYMMETRIC:   out.append(SYM_Q);   dels.append(c)
        else:                  out.append(c);        dels.append(None)
        idx.append(j)
    return "".join(out), idx, dels

def norm_needle(nd):
    return normalize_line(nd)[0]

def find_norm(line, nd):
    """返回 [(orig_start, orig_end, matched_original_text, norm_offset)]。
    orig_start/orig_end 直接是原文行内偏移；matched_original_text 是原文逐字片段。"""
    n, idx, _ = normalize_line(line)
    q = norm_needle(nd)
    res, pos = [], 0
    while True:
        k = n.find(q, pos)
        if k < 0:
            break
        a, b = idx[k], idx[k + len(q) - 1] + 1
        res.append((a, b, line[a:b], k))
        pos = k + 1
    return res

# ---- 用法：替换 _rs_carrier_scan.py 的两道精确闸（应当怎么改，本件不改） ----
# 应当把 :229 的文件级 prefilter 从 `if not any(n in txt for n in needles)` 改成
# 「按归一化/宽泛模式预筛」，把 :165 的 line.find(n) 改成 find_norm(L, n)，
# 并且 classify_line 的角色判定一律用**原始 line**（不是 norm）跑：
CANON = "只能判「不可复现」"
for lineno, L in enumerate(lines, 1):                 # lineno 即原文行号，天然可回溯
    hits = find_norm(L, CANON)                        # L1 引号变体
    #   + 显式补充轨（结构变体，单独召回，不并入归一键）：
    #     re.search(r"只能判[「『“(]?不可复现[」』”)]?", L)
    for (a, b, raw_text, k) in hits:
        pos = a                                       # 原文偏移 → quoted_containing(L, pos) 可直接使用
        assert L[a:b] == raw_text                     # 位置映射自检
        # role = classify_line_on_original(L, needles=..., pos=pos)   ← R5 仍在原文上判
        print(file_rel, lineno, a, b, repr(raw_text)) # 输出原始行号 + 原始偏移 + 原文片段
```

**位置回溯保证**（`_nn_norm_out.txt:33-37`）：`mapped hits checked = 85 ; all(orig_slice == reported_text) = True`；样例 `LEDGER_APPENDIX_DRAFT.md:123 orig[47:56] = '只能判「不可复现」'`。因为 1:1 保长，`norm` 的下标 == 原文下标，`file:line` 由 `enumerate(lines, 1)` 直接给出，无需 span 对齐表。

### (c) ★ 归一化边界（哪些不能归一）

1. **核心文字一码不改**：`不可复现` ≠ `不可复原` / `不可重复` / `不可再现`。真实语料 `不可复原` 5 行（`_nn_norm_out.txt:81-86`，如 `gate_doc_name_fix_20261109/GATE_DOC_NAME_FIX.md:316`），语义是「历史现场无法还原」，与「数值复算不出」不同命题。L1 不碰汉字。
2. **引号内 vs 引号外语义不同**：`spans_of_quotes()`（`_rs_carrier_scan.py:90-108`）与 `quoted_containing()`（`:110-114`）靠成对引号跨度决定 `REFUTING_QUOTE` / `QUOTED` / `ASSERTION`。归一只能**换**引号字符，不能**删**引号、不能把「有无引号」归一掉 —— 否则 `needs_fix`（`:257-258`）必错。L1 用左右不同的哨兵（`\x01`/`\x02`）保留开闭与嵌套信息。
3. **不得删标点 / 不得改句子边界**：顿号 `、` 分隔的两条并列结论 vs 整句被一对引号罩住，是不同 role（CE2）。
4. **不得删空白 / 不得 NFKC**：`| 只能判 | 不可复现 |` 是表格两列，不是一句话（CE6）；全角标识符不是半角标识符（CE4，参 `GATE_LITERAL_MATCH_POSTMORTEM.md:70`）。
5. **不得把「无引号变体」并入归一键**：`只能判不可复现` 与 `只能判「不可复现」` 若同键，裸断言与引述否定即混淆（CE1/CE5）。它们只能作为**并列召回轨**，各自保留自己的角色判定结果。
6. **反配/不成对引号不得猜**：`只能判』不可复现『` 在 L1 下 key 为 `只能判\x02不可复现\x01`，不与 canon 合并；`spans_of_quotes` 找不到成对跨度应报 `UNKNOWN: 需人工复核`（对齐 R4 `:248-250` 的「unpaired markers = ERROR，绝不猜」），不得补造成 `ASSERTION`。
7. **归一化只用于召回，不用于定谳**：`verbatim_cmp()`（`_rs_carrier_scan.py:130-140`，R3「EQUAL/NOT-EQUAL + 首个差异码位」）与指纹一律在**原始字节/原文**上做；归一后的字符串不得写入台账、不得作为「同一句」的证据。

### (d) 反例：≥3 个「归一化过度导致误合并」的构造样本

脚本 `_nn_counterexamples.py` → `_nn_counterexamples_out.txt`。`TOTAL: 7/7 个过度规则确实造成误合并；L1 对其中 7 个保持不合并`（实跑 `:81`）。逐条：

| ID | 过度规则 | A（语义 1） | B（语义 2） | OVER_MERGED | L1_MERGED |
|---|---|---|---|---|---|
| CE1 | 删所有引号 | `只能判「不可复现」、不能定位当年错误步骤` | `只能判不可复现、不能定位当年错误步骤` | **True** | False |
| CE2 | 删引号+删标点 | `只能判「不可复现」、不能定位当年错误步骤` | `只能判「不可复现、不能定位当年错误步骤」` | **True** | False |
| CE3 | 近义替换 | `只能判「不可复现」` | `只能判「不可复原」` | **True** | False |
| CE4 | NFKC | `规则 APPROVE_SCOPE 已生效` | `规则 ＡＰＰＲＯＶＥ＿ＳＣＯＰＥ 已生效` | **True** | False |
| CE5 | 只比核心串（丢语境） | `**只能判「不可复现」、不能定位当年错误步骤**`（笔3 裸断言） | `其边界句「只能判『不可复现』、不能定位当年错误步骤」自本节起不再成立`（§609 引述否定） | **True** | False |
| CE6 | 删标点+空格 | `\| 只能判 \| 不可复现 \|`（表格两列） | `只能判不可复现`（散文断言） | **True** | False |
| CE7 | 删引号 | `只能判「不可复现」` | `只能判』不可复现『`（反配引号） | **True** | False |

CE2 尤其致命：A 的引号跨度只罩住 `不可复现`，B 的引号跨度罩住整句；`quoted_containing()` 拿到不同 span ⇒ role 不同，但删标点后两句同键，会被当成同一句计数。CE5 是本次 FAIL 的语义核心：A 是 `ASSERTION`（needs_fix 候选），B 是 `REFUTING_QUOTE`（`_ve_DRAFT_S609.md:22`），合并即把「否定该句」误当「断言该句」。

---

## 第四步 · 两段式设计（needle 精确匹配 + 角色后判）对不对

### (a) 失效链与改法

现状链：`needle 精确子串（file gate :229 → line gate :165）` → `R4 区块` → `R5 角色` → `needs_fix`。**前置闸是硬丢弃**：任一闸漏，`carriers` 里就没有该行，`role_of()` 返回 `<not-scanned>`（`_rs_carrier_scan.py:327-331`），后面全不跑。本会话量化（`_nn_norm_out.txt:39-48`）：

```
file-level prefilter (line 229) 会整件跳过的「含变体但无直角引号」文件 = 4
     ledger_bound_20261109/_lb2_TEMPLATE.md (union lines=[152, 202])
     s604_attribution_20261108/S604_ATTRIBUTION.md (union lines=[138])
     s604_script_gap_20261109/S604_SCRIPT_GAP.md (union lines=[55, 56])
     s604_script_gap_20261109/_sg_FINDINGS.md (union lines=[21])
这些件里的漏检行数 = 6
通过 file gate 但被 line-level gate (classify_line line 165) 跳过的行 = 34
其中 :22 是否在内 = True
```

即 **4 件整件被跳过 + 34 行行级被跳过 = 40 行漏检**（与第二步 (b) 完全对上），包括 `:22`。改成「先按宽泛模式捞候选，再判角色」后：候选阶段不丢弃任何含锚词的行，`:22` 与那 4 件都会进入 `carriers`；角色判定在**原文行**上跑，`REFUTING_QUOTE` 仍能被 `NEG_LEX`（`不再成立` / `过时` / `已定谳` 等，`_rs_carrier_scan.py:80-86`）正确判出（本会话直导 `classify_line` 已验证：`['只能判『不可复现』'] -> REFUTING_QUOTE pos= 162`）。**召回问题被消解，角色判定不受影响** —— 前提是角色判定必须读原文，不读归一串。

### (b) 宽泛捞候选会不会引入大量噪声：量与质

脚本 `_nn_widenet.py` / `_nn_crosscheck.py`，实跑 `_nn_widenet_out.txt:4-13`、`_nn_crosscheck_out.txt:1-7`：

| 候选口径 | 行数 | 文件数 | 与六变体真值 U(88 行/22 件) 的关系 |
|---|---:|---:|---|
| W1 单词 `不可复现` | 187 | 44 | **+99 行 FP（52.9% of W1）** |
| W2 锚词 `只能判` | 94 | 28 | +? |
| **W3 双锚共现（W1∩W2）** | **88** | **22** | **`W3 == U`，差 0 行** |
| **W4 正则 `只能判.{0,3}不可复现`** | **88** | **22** | **`W4 == U`，差 0 行** |
| U 六变体精确并集 | 88 | 22 | 真值基线 |

- **量**：最宽的单词口径 W1 = 187 行，比真值多 99 行；收窄到「双锚共现」或「锚词 + 3 字间隙正则」后恰好 88 行，**零 FP、零 FN**（`U-W3 = 0`、`W3-U = 0`、`U-W4 = 0`、`W4-U = 0`，`_nn_crosscheck_out.txt:2`）。噪声可从 187 压到 88（缩 47.1%），且不需人工逐行筛。
- **质**：99 行 W1-U 中，83 行（83.8%）含引号（引述候选）、44 行（44.4%）是 §604/空档主题、22 行（22.2%）含否定/更新信号、9 行（9.1%）是门禁/载体/标识符主题（`_nn_widenet_out.txt:18-21`）；**含锚词 `只能判` 的行 = 0**（`_nn_crosscheck_out.txt:5`）—— 即这 99 行全是「提到『不可复现』这个词但不在说这句边界句」的其他命题，如 `GOAL_THREE_TARGETS_20261018.md:245` 的「载体清单反向复原、设计件『不可复现』登记撤回」、`RULING_DIRECTION.md:17` 的「§604 空档差旧口径不可复现」、以及 5 行「不可复原」。**它们是真噪声，不是漏检**：把它们并入会污染载体图，正是「不许过度归一化」要挡的。
- 因此「宽泛」不是单词泛化，而是**双锚 / 短间隙正则 + 角色判定收窄**：候选 88 行全部是真变体或真引述，R5 再按 role 把它们分成 ASSERTION / REFUTING_QUOTE / QUOTED / …，`needs_fix` 仍只取 `ASSERTION ∧ HIGH`（`:257-258`）。

### (c) 「宁可多捞、由角色判定收窄」的设计方案（应当怎么改，与现行对比）

```
阶段 0  召回（宽、不丢）：对每个文件不再用 needle 精确串做 file gate。
        候选 = 含双锚 / 短间隙正则的行：re.search(r"只能判.{0,3}不可复现", L)
        或对 needle 先做 L1 归一后 find_norm()；两者本语料等价（都 = 88 行）。
        附加显式补充轨：r"只能判[「『“(]?不可复现[」』”)]?"（覆盖 no_quote 9 行）。
        原则：候选只 ADD 到 carriers，绝不因「不像 needle」而 DELETE。
阶段 1  角色（严、在原文）：classify_line(原始 L, pos=原文偏移)。
        quoted_containing(L, pos) / NEG_LEX / UPDATED_SAMPLE 全部读原文；
        归一串只用来算 pos，不参与 role。
阶段 2  区块与风险（不变）：blocks_of() / APPENDABLE_BLOCK / needs_fix 保持 R4/R5 原样。
阶段 3  输出：每个 carrier 附 (file, line, orig_start, orig_end, raw_text, 命中的变体类, role)。
        「变体类」是元数据，不是新 carrier：同一 (file,line) 多变体命中只记 1 行，
        但在 variants 字段列出全部，供审计回溯。
```

| 维度 | 现行（needle 精确 + 角色后判） | 建议（宽候选 + 角色收窄） |
|---|---|---|
| 漏检 | 45.45% 行 / 18.18% 文件（单 needle） | 0%（本语料，W3/W4 = U） |
| 假阳 | 0（但靠「命中的才算」掩盖了漏） | 0（W3/W4 恰等于 U）；单词口径 W1 才有 99 行 FP，不采用 |
| 角色判定 | 有，但 needle 漏时**根本不执行** | 必执行，且在原文上执行 |
| 对变体新类 | 需要人工列，漏了不知道 | 双锚/正则天然覆盖新包裹符；配合第五步自动发现 |
| 代价 | 低（但结论不可信） | 候选行从 48 → 88（+40 行）需过 R5；人工复核增量 = 40 行，不是 99 行 |
| 风险 | 硬丢弃不可观测 | 需防「候选口径过宽」（用双锚而非单词）+ 保留原文判角色 |

**「宁可多捞」的边界**：多捞的是**候选**，不是**结论**。`needs_fix` 的门槛（ASSERTION ∧ HIGH）一字不放宽；多出来的行若 `role != ASSERTION` 或 `risk != HIGH`，进 C 段审计而不进 B 段施工数 —— 与 `REFSYNC_SCOPE_FIX.md:260` 的 R5 排除逻辑、`:264` 对 `NEG_LEX` 假阴性路径的如实登记兼容。

### (d) 哪种更适合本项目

**建议方案（宽候选 + 角色收窄）更适合**，理由基于本会话实测规模：

- 语料规模小：`lead/` depth≤2 共 **631 个 .md**（`_nn_variants_out.txt:2`），全量无深度上限 .md 为 947（`REFSYNC_SCOPE_FIX.md:171`），全扩展名 5500（`:253`，仅为审计不作施工数）。88 行候选 / 22 件，人工逐行复核完全可行。
- 句数少且高度重复：同一句被复制进多个草案/模板/沙箱（R2 的「N carriers」），88 行里大量是逐字副本；角色判定一次写对即可批量复用。
- 人工复核成本：增量 40 行（不是 99 行），且这 40 行全是漏检的真载体（如 `S604_ATTRIBUTION.md:138`、`_lb2_TEMPLATE.md:152/:202`），正是台账风险面；而现行方案的「0 假阳」是建立在「没扫到就不报」上的，成本被隐藏到结论错误里。
- 该项目的实际风险是**漏**（一台账内 §607 与 §609 互相矛盾，`_ve_DRAFT_S609.md:22` 明写「自本节起不再成立」却可能不被发现），不是 FP 淹没。`REFSYNC_SCOPE_FIX.md:227` 自己给的教训就是「漏了哪类自己不知道」。
- 反过来说，**不建议**用单词级 W1（187 行 / 99 行 FP）：那 99 行是别主题，人工复核成本翻倍且无收益。取 W3/W4 双锚即可。

---

## 第五步 · 修正后的自检方案

### (a) 负控自检应当包含哪些项才算合格

现行 6 项（`_rs_carrier_scan.py:332-339`）= 5×`ASSERTION`（全 `angle_corner`）+ 1×`REFUTING_QUOTE`（`:22`，`curly_corner`）。本会话类目覆盖矩阵（`_nn_crosscheck_out.txt:9-15`）：

```
  angle_corner   corpus_lines=48 controls=5 covered=YES
  curly_corner   corpus_lines=34 controls=1 covered=YES
  curly_double   corpus_lines= 0 controls=0 covered=NO(零负控)
  no_quote       corpus_lines= 9 controls=0 covered=NO(零负控)
  half_paren     corpus_lines= 0 controls=0 covered=NO(零负控)
  no_punct       corpus_lines= 0 controls=0 covered=NO(零负控)
```

**6 项里 4/6 变体类零负控**，且 6 项全部是「已命中」样本的 role 校验 —— 没有任何一项检验「本不该漏却漏了」。合格自检至少要含以下 6 组：

1. **每变体类 ≥1 正控**：`angle_corner` / `curly_corner` / `curly_double` / `no_quote` / `half_paren` / `no_punct` 各一条（0 命中的类用**合成 fixture 注入**，见 `_nn_norm_out.txt:98-109` 的 `POS-curlyDbl` / `NEG-halfparen` / `NEG-nopunct`；`FIXTURE_SELF_TEST = PASS`）。
2. **每变体类 ≥1 真实锚点负控**：`_nn_widenet_out.txt:55-65` 已给自动发现的 10 个类目各一条真实 `file:line`，可直接补入。特别是 `no_quote` 类必须补（`_lb_BOUND_VOLUME.md:226` 等 9 行），本次 FAIL 就是零负控类。
3. **每个 needle 单独跑一次自检**：禁止用多 needle 联合跑替代（第一步 ★ 的掩盖效应：文档双 needle 下 `SELF_TEST = PASS 6/6`，单 needle 才 `FAIL`）。
4. **role × 变体 交叉矩阵**：至少 `ASSERTION` / `REFUTING_QUOTE` / `QUOTED` / `UPDATED_SAMPLE` / `ANALYSIS_MENTION` 五类各 1 条 × 各类变体，防「归一后 role 漂移」。
5. **位置回溯断言**：每条命中必须有 `L[a:b] == raw_text`（`_nn_norm_out.txt:34` 的 85/85），并复核 `file:line` 与原文一致。
6. **过度归一反例断言**：CE1–CE7 必须全部 `L1_MERGED = False`（`_nn_counterexamples_out.txt:81`，7/7 保持不合并）；这是「不许过度归一化」的机器门禁。
7. **已知假阴性路径**：`REFSYNC_SCOPE_FIX.md:264` 自陈 `NEG_LEX` 整行子串会把裸断言翻成 `ANALYSIS_MENTION`（`_rsv_r5.py` 例 E/F），6 个负控未覆盖 —— 必须补 2 条合成 fixture 作负控。
8. **`<not-scanned>` 硬失败**：任何期望项返回 `<not-scanned>` 即 `EXIT=1`，且要区分「判错 role」与「根本没扫到」两种失败原因（本次 FAIL 是后者，输出 `got=<not-scanned>` 已区分）。
9. **指纹绑定**：跑自检时重算被核 9 件 SHA256/字节数并与编排方基线比对（本会话已 9/9 MATCH），防止语料漂移让负控「碰巧 PASS」。

### (b) 保证「漏了哪类自己不知道」不再发生：可执行的做法

**变体类自动发现 + 集合差门禁**（`_nn_widenet.py` C/D 段已实跑，`_nn_widenet_out.txt:37-65`）：

```
1. 不靠人工列举。用宽口径从语料自动枚举「锚词之间的包裹形态」：
   re.finditer(r"只能判(.{0,4}?)不可复现(.{0,2})", L) → (pre, post) 类目集合
   本会话实跑得到 10 类（_:38-48）：
     pre='『' post='』、'(21) / pre='「' post='」、'(20) / pre='「' post='」，'(14)
     pre=''  post='、不'(9)  ← 无引号类，现行 6 项负控零覆盖
     pre='『' post='』，'(9) / pre='「' post='」*'(6) / pre='「' post='」`'(5)
     pre='『' post='』`'(5) / pre='「' post='」；'(3) / pre='「' post='」"'(2)
2. 把「自检 fixture 覆盖的类目集合」与「自动发现的类目集合」做差：
   差集非空 ⇒ SELF_TEST = FAIL（而不是等某条角色判错才发现）。
   本会话：自动发现 10 类，现行负控只覆盖 2 类 ⇒ 未覆盖 8 类（_:52-54）。
3. 每个未覆盖类目自动给一条真实锚点（_:55-65），直接补成负控，无需人工想变体。
4. 每次语料变更后重跑发现器；新出现的 (pre, post) 即新变体类，门禁立刻报 FAIL。
5. 补充：对 0 命中的类（curly_double / half_paren / no_punct）用合成 fixture 常驻，
   防止「语料里没有 ⇒ 以为规则对」的假安全（_nn_norm_out.txt:98-109）。
```

这把「漏了哪类自己不知道」变成「漏了哪类，集合差会明确列出」。`REFSYNC_SCOPE_FIX.md:227` 的教训（「人工列 + 无负控」）由此有了可执行的闭环。

### (c) 这次 FAIL 的教训：如果自检不跑，会不会发现？

**不会**。证据链：

- 交付件 `REFSYNC_SCOPE_FIX.md:251` 与在盘 `_fix_d2_out.txt` 的 E 段都写着 `SELF_TEST = PASS`（6/6），`EXIT=0`，`verdict=confirmed`。本会话按文档命令复跑同样 `EXIT=0` / `PASS`（`_nn_repro_twoneedle_out.txt`）。也就是说**跑了自检、且 PASS，仍没发现** —— 因为自检的类目覆盖不足（4/6 类零负控）且用双 needle 联合跑掩盖了单 needle 的漏。
- 若连自检都不跑：单 needle 下 `:22` 是 `<not-scanned>`，输出里**没有任何报错**，A/B/C 段只是「少了 1 行、少了 4 件」，`scanned files = 631` 看似正常，`needs_fix` 计数也照常产出；交付件的 D 段（`:317-319`）甚至明文宣称「§609 :22 is KEPT in section A with risk=HIGH」—— 不跑自检、也不核 A 段，就会把「没扫到」当成「扫到了且已排除」。
- 反事实：本次 FAIL 之所以暴露，是**编排方用单 needle 重跑了负控自检**。即自检本身是唯一发现通道；而现行自检又因为覆盖不足，在交付口径下给了假 PASS。结论：**自检必须跑，且自检自身必须有「覆盖度门禁」** —— 只跑一个覆盖不足的自检，等于没跑。

---

## 实跑命令清单（本会话全部只读 / 仅写本写域）

| # | 命令 | 输出 / 结果 |
|---|---|---|
| 1 | `python -I -X utf8 -c` + hashlib 全量自算 9 件 | 9/9 MATCH 编排方指纹（本件绑定行） |
| 2 | `python -I -X utf8 -c` 直读 `_ve_DRAFT_S609.md:22/:69/:70` 码位 | U+300E/F vs U+300C/D 确认 |
| 3 | `python -I -X utf8 ".../_rs_carrier_scan.py" --needle "只能判「不可复现」" --include-refuting --max-depth 2 --ext .md > .../_nn_repro_single_out.txt` | `EXIT=1`，`SELF_TEST = FAIL`，`:22 got=<not-scanned>`，A/C 段只有 :69/:70 |
| 4 | 同上但双 needle（文档命令）`> .../_nn_repro_twoneedle_out.txt` | `EXIT=0`，`PASS 6/6`，`:22 got=REFUTING_QUOTE` |
| 5 | `python -I -X utf8 -c` importlib 直导 `classify_line()` | 4 组 needle 的 role/pos 矩阵 |
| 6 | `python -I -X utf8 ".../_nn_variants.py" > .../_nn_variants_out.txt` | `scanned files = 631`；`ORCH_VERIFY_ALL = MATCH`；六变体 18/16/0/7/0/0；union 22 件/88 行 |
| 7 | `python -I -X utf8 ".../_nn_norm.py" > .../_nn_norm_out.txt` | L1 79 行/22 件；映射 85/85；`FIXTURE_SELF_TEST = PASS` |
| 8 | `python -I -X utf8 ".../_nn_counterexamples.py" > .../_nn_counterexamples_out.txt` | `7/7 OVER_MERGED=True；L1 对 7 个保持不合并` |
| 9 | `python -I -X utf8 ".../_nn_widenet.py" > .../_nn_widenet_out.txt` | W3=W4=U=88 行/22 件；自动发现 10 类；未覆盖 8 类 |
| 10 | `python -I -X utf8 ".../_nn_crosscheck.py" > .../_nn_crosscheck_out.txt` | `U-W3=0 W3-U=0 U-W4=0 W4-U=0`；`W1-U=99` 中 0 行含锚词 |
| 11 | `grep -A 8 "NEGATIVE-CONTROL" lead/refsync_scope_20261109/_fix_d2_out.txt` | 交付件 E 段 `SELF_TEST = PASS` 6/6 |
| 12 | `python -I -X utf8 -c` 读 `GATE_LITERAL_MATCH_POSTMORTEM.md:70-72` | 确认「反引号/换行拆断标识符」按 raw=False→归一化 True 区分 |
| 13 | `python -I -X utf8 ".../_nn_corpus_check.py" > .../_nn_corpus_check_out.txt` | 现盘 633 件（排除写域）；六变体计数 18/16/0/7/0/0、union 22/88 与 631 口径一致 |
| 14 | 四个分析脚本加排除写域后全部重跑（`for s in _nn_variants _nn_norm _nn_widenet _nn_crosscheck; do python -I -X utf8 ...; done`） | 4/4 `EXIT=0`；关键数全部复原：L1 79 行/22 件、映射 85/85、`7/7` 反例、10 类自动发现 |

**未验 / 不补造**：本会话未改 `_rs_carrier_scan.py`、未改任何既有件，故「应当怎么改」的替代实现**未在真实脚本上集成实跑**，只在 `_nn_norm.py` 原型 + 合成 fixture 上验证（`FIXTURE_SELF_TEST = PASS`、85/85 位置映射）；集成后的全量回归、无深度上限 / 全扩展名口径（947 / 5500 件）的自检结果**未跑**，不宣称。L1 的哨兵字符 `\x01\x02\x03` 在本语料 631 件中未出现（未逐一扫描验证冲突，仅按「私有控制字符」约定采用；若语料含控制字符需改用具名占位串并配 span 映射表，此项标为未验）。`half_paren` / `no_punct` / `curly_double` 在语料 0 命中，其负控只能靠合成 fixture，不能靠真实锚点。

**★ 语料漂移如实登记（本会话末段发现）**：会话开始时 `lead/` depth≤2 `.md` = **631 件**（与编排方 `files: 631` 一致，第一批全部实跑基于此口径）；会话进行中并行写域新增 2 件 `.md`，末段现盘 = **633 件**（排除本任务写域 `needle_norm_20261109/_nn_REPORT.md` 后）。`_nn_corpus_check.py` / `_nn_corpus_check_out.txt` 实跑核对：排除写域后六变体计数仍为 18/16/0/7/0/0 件、48/34/0/9/0/0 行、union 22 件/88 行，**与 631 件口径完全一致**，故本报告全部量化结论不受漂移影响。为使证据件可复跑，四个分析脚本（`_nn_variants.py` / `_nn_norm.py` / `_nn_widenet.py` / `_nn_crosscheck.py`）已加「排除 `needle_norm_20261109/` 写域」并全部重跑，输出中的 `scanned files = 633` 即现盘排除写域后的口径；`_nn_repro_single_out.txt` / `_nn_repro_twoneedle_out.txt` 的 `scanned files = 631` 系第一批（漂移前）实跑，未重跑、如实保留。此差异不影响任何数值（新增 2 件均为并行件，零命中六变体）。

## 写域产出（全部前缀 `_nn_`，均在 `lead/needle_norm_20261109/`）

`_nn_repro_single_out.txt`、`_nn_repro_twoneedle_out.txt`、`_nn_variants.py` / `_nn_variants_out.txt`、`_nn_norm.py` / `_nn_norm_out.txt`、`_nn_counterexamples.py` / `_nn_counterexamples_out.txt`、`_nn_widenet.py` / `_nn_widenet_out.txt`、`_nn_crosscheck.py` / `_nn_crosscheck_out.txt`、`_nn_corpus_check.py` / `_nn_corpus_check_out.txt`、本件。共 15 件。
