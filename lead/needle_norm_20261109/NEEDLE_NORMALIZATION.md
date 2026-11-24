# NEEDLE 归一化设计 · FAIL 复现 · 漏检率量化 · 边界反例 · 两段式评估 · 修正自检

- 日期 2026-11-09；执行角色：归一化件撰写员（本轮）。唯一写域 `lead/needle_norm_20261109/`，本件文件名 `NEEDLE_NORMALIZATION.md`；本轮新增辅助件统一前缀 `_nd_`。
- 纪律：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；绝对只读域与两件台账一律未改、未追加、未覆盖；未 commit、未 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib。
- 本件**不改**上一轮交付的 `_rs_carrier_scan.py`，也**不改任何既有件**。改进一律以「应当怎么改」给出；可粘贴片段是本写域原型 `_nd_l1fix.py` 的实跑代码，未集成到真实脚本。

---

## 1 目的与边界

**目的**（本轮 ask）：① 独立复现单 needle 的 `SELF_TEST = FAIL`（必现要素字面串：`SELF_TEST FAIL`）；② 逐种量化六变体的漏检率；③ 给出归一化方案 + 可粘贴片段 + 位置可回溯 + 归一化边界 + ≥3 个**过渡归一化**反例；④ 评估「精确 needle + 角色后判」的**两段式**；⑤ 给出**宽泛捞候选**方案与质量评估；⑥ 如实登记复核回件 verdict，并给出修正后的负控自检方案与未验项。

**边界（硬约束）**：
1. 只做归一化设计与漏检率量化。**不改** `_rs_carrier_scan.py`、不改任何既有件；`_nd_l1fix.py` 是独立原型，只在写域内新建。`_rs_carrier_scan.py` 末态指纹仍为 `9ccca808…/16053`（本会话实跑，见 §2 绑定行）。
2. 只读域清单（一律不得修改/追加/覆盖）：`lead/refsync_scope_20261109/` 全部件、`lead/s604_refsync_full_20261109/`、`lead/s604_verdict_entry_20261109/`、`lead/ledger_appendix_20261108/`、`lead/ledger_bound_20261109/`、两件台账 `lead/PENDING_DECISIONS.md` / `lead/GOAL_THREE_TARGETS_20261018.md`。
3. 归一化**不能过度**：把不同意思的句子并成同一句即引入新错误。物理边界见 §4.4；复核回件已判定上一轮 L1 存在真实误合并（§6.1，`verdict = partial`），本件给出修正版 L1 并标 `unconfirmed`（见 §6.1）。
4. 归一串**只用于召回**：角色判定、`verbatim_cmp()`、指纹、台账证据一律在原文/原始字节上做（`_rs_carrier_scan.py:130-140` 的 R3、`_rs_carrier_scan.py:183-189` 的 R5）。

---

## 2 上游指纹（九件）+ FAIL 独立复现

### 2.1 九件绑定行（本会话 `python -I -X utf8 -c` + hashlib 自算，9/9 MATCH 编排方指纹）

实跑命令（本轮）：

```
cd /d/Project/ra2-campaign-forge && python -I -X utf8 -c "
import hashlib, os
pairs = [ ('lead/refsync_scope_20261109/_rs_carrier_scan.py','9ccca808...',16053), ... 共 9 件 ... ]
for p,h,b in pairs:
    d=open(p,'rb').read(); h2=hashlib.sha256(d).hexdigest(); b2=len(d)
    print(('MATCH' if (h2==h and b2==b) else 'MISMATCH'), p, h2, b2)
"
```

输出：`MATCH` × 9，`TOTAL MATCH = 9 /9`（写件前末态复算同样 9/9 MATCH）。以下 9 行严格按「复核回件必须含绑定行」格式，顺序同【编排方指纹】块：

被核对象 SHA256 = 9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57，字节数 = 16053
被核对象 SHA256 = aa2dbe945c9d8fdc6aebde849701393f6f8766c51b372329d588616781c2f83f，字节数 = 35782
被核对象 SHA256 = 83b215ccbbf2c3e221c247e7bd9c7c221fddcf9472977d2df8902bf1b94ec65e，字节数 = 49958
被核对象 SHA256 = 058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec，字节数 = 18980
被核对象 SHA256 = 1e4ceb37187cd12601ad03cdc02f0cf2ee624d1f6870c03c0e35d84cbcb40cfc，字节数 = 36097
被核对象 SHA256 = 8ccf9866ebd7860f03d71e939960e018fd0cfbbe6b94add04dd50f7004c11ac5，字节数 = 61819
被核对象 SHA256 = 724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e，字节数 = 45719
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

对应顺序：`_rs_carrier_scan.py` / `_rs_CARRIER_MAP.md` / `REFSYNC_SCOPE_FIX.md` / `_ve_DRAFT_S609.md` / `S604_VERDICT_ENTRY_DRAFT.md` / `S604_REFSYNC_FULL.md` / `LEDGER_APPENDIX_DRAFT.md` / `PENDING_DECISIONS.md` / `GOAL_THREE_TARGETS_20261018.md`。

### 2.2 FAIL 独立复现（本轮实跑，不是采信上一轮输出）

命令（单 needle，含 `--include-refuting`，输出落本写域 `_nd_repro_single_out.txt`）：

```
cd /d/Project/ra2-campaign-forge && python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py" --needle "只能判「不可复现」" --include-refuting --max-depth 2 --ext .md > "D:/Project/ra2-campaign-forge/lead/needle_norm_20261109/_nd_repro_single_out.txt" 2>&1; echo "EXIT=$?"
```

输出：`EXIT=1`；`_nd_repro_single_out.txt:10` = `scanned files = 636 ; carrier occurrences = 65 ; distinct files = 19`（现盘语料已含上一轮 15 件 `_nn_` 产物及本轮新增件，故与上一轮 `631 / 48 / 18` 不同，如实登记漂移；结论不受影响，见 §3.1）；关键行：

```
_nd_repro_single_out.txt:303  FILE s604_verdict_entry_20261109/_ve_DRAFT_S609.md  ... hits=2
_nd_repro_single_out.txt:404     s604_verdict_entry_20261109/_ve_DRAFT_S609.md:69 role=REFUTING_QUOTE neg=原句
_nd_repro_single_out.txt:405     s604_verdict_entry_20261109/_ve_DRAFT_S609.md:70 role=REFUTING_QUOTE neg=不再成立,已定谳,改为,更新：
_nd_repro_single_out.txt:428  FAIL  s604_verdict_entry_20261109/_ve_DRAFT_S609.md:22 want=REFUTING_QUOTE   got=<not-scanned>
_nd_repro_single_out.txt:430  SELF_TEST = FAIL
```

即：**`:22` 扫不到；即使加了 `--include-refuting`，C 段也不出现 `:22`**（只列 `:69` / `:70`），A 段该件 `hits=2`。`got=<not-scanned>` 不是判错角色，是根本没进 `carriers`。`_rs_carrier_scan.py:317-319` 的 D 段文字却宣称「§609 :22 is KEPT in section A with risk=HIGH」——设计与单 needle 实现脱节。

**直角引号 / 弯引号的码位事实**（本轮 `python -I -X utf8 -c` 直读）：`_ve_DRAFT_S609.md:22` 含 `只能判『不可复现』`（U+300E/U+300F，弯/直角双层语义中的『』），`angle = False curly = True`；`:69`/`:70` 恰相反，只含 `只能判「不可复现」`（U+300C/U+300D，直角引号）。`:22` 原文（本轮直读全文）为：

```
其边界句「只能判『不可复现』、不能定位当年错误步骤」（:123）**自本节起不再成立**——错误步骤已定位…
```

### 2.3 脚本实现层面的原因（直读源码，非采信）

`_rs_carrier_scan.py` 的两道 needle 闸都是**精确子串**，角色判定在闸之后：

| 位置 | 代码 | 后果 |
|---|---|---|
| `_rs_carrier_scan.py:229` | `if not any(n in txt for n in a.needle): continue` | 文件级预过滤：整件无直角引号 needle ⇒ 整件跳过，`splitlines()` / `blocks_of()` / `classify_line()` 都不执行 |
| `_rs_carrier_scan.py:165-167` | `pos = min((line.find(n) for n in needles if n in line), default=-1)` / `if pos < 0: return None` | 行级闸：行内无 needle ⇒ 返回 `None`；`_rs_carrier_scan.py:239` `if not c: continue` ⇒ 该行不进 `carriers` |
| `_rs_carrier_scan.py:168-189` | `quoted_containing()` / `NEG_LEX` / 各 role 分支 | **角色判定在两闸之后**：needle 一漏，R4 区块与 R5 角色根本没机会跑 |
| `_rs_carrier_scan.py:327-331` | `role_of()` 只在 `carriers` 里找，找不到返回 `<not-scanned>` | 负控期望项返回 `<not-scanned>` ⇒ `EXIT=1` |
| `_rs_carrier_scan.py:257-258` | `needs_fix = assertion and risk.startswith("HIGH")` | 无载体 ⇒ 交集为空，漏检不可观测 |

`PAIRS = [("「","」"),("『","』"),("`","`"),("“","”")]` 在 `_rs_carrier_scan.py:79`，`spans_of_quotes()` 在 `:90-108`，`quoted_containing()` 在 `:110-114`。注意：字母表**不含**单弯引号 `‘’`，也不认交叉错配 `『…」`；这是 §4.4 归一化边界与 §6.1 partial 的来源。

**掩盖效应（本轮复跑）**：按 `REFSYNC_SCOPE_FIX.md:251` 登记的双 needle 命令实跑 `_nd_repro_twoneedle_out.txt` → `EXIT=0`、`:673` `PASS ... :22 want=REFUTING_QUOTE got=REFUTING_QUOTE`、`:675` `SELF_TEST = PASS`。原因：`:22` 逐字含第二 needle `不能定位当年错误步骤`，靠另一条 needle 被捞回。**交付自检 6/6 PASS 证明不了直角引号 needle 覆盖 `:22`**，只证明两条 needle 的并集覆盖。单 needle 才暴露真漏检。

---

## 3 漏检率量化

### 3.1 口径与逐种数字（本轮 `_nd_verify.py` 实跑）

命令：

```
cd /d/Project/ra2-campaign-forge && python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/needle_norm_20261109/_nd_verify.py" > "D:/Project/ra2-campaign-forge/lead/needle_norm_20261109/_nd_verify_out.txt" 2>&1; echo "EXIT=$?"
```

输出 `EXIT=0`；`_nd_verify_out.txt:1` = `scanned files (excl entire needle_norm_20261109/ write domain) = 635`（本轮现盘 `lead/` depth≤2 全部 `.md` = 636，排除本写域后 635；编排方起始为 631，上一轮复核为 633/634，差异来自并行写域新增 2 件：`count_invariant_20261109/_ci_INVARIANTS.md`、`gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md`，均零命中六变体，故下列数字与 631 口径一致）。单位 `(file, line)`，符合 `_rs_carrier_scan.py:15-17` 的 R2「occurrence」。

| 变体 | needle（逐字） | 命中文件数 | 命中行数 | 出处 |
|---|---|---:|---:|---|
| `angle_corner` | `只能判「不可复现」` | **18** | **48** | `_nd_verify_out.txt:2` |
| `curly_corner` | `只能判『不可复现』` | **16** | **34** | `_nd_verify_out.txt:3` |
| `curly_double` | `只能判“不可复现”` | **0** | **0** | `_nd_verify_out.txt:4` |
| `no_quote` | `只能判不可复现` | **7** | **9** | `_nd_verify_out.txt:5` |
| `half_paren` | `只能判(不可复现)` | **0** | **0** | `_nd_verify_out.txt:6` |
| `no_punct` | `只能判 不可复现` | **0** | **0** | `_nd_verify_out.txt:7` |

与【六变体实跑】编排方给的 18/16/0/7/0/0 逐种 MATCH；行级 48/34/0/9/0/0 与上一轮 `_nnv_verify_out.txt:8-13` 一致。

**只扫直角引号 vs 全扫的差**（`_nd_verify_out.txt:8-13`）：

```
angle only : files=18 lines=48
union(6)   : files=22 lines=88
missed     : files= 4 (18.18%) lines=40 (45.45%)
baseline recall lines=54.55% files=81.82%
variant-line pairs sum=91 ; distinct union lines=88 ; overlap=3
```

- **漏检率**：行级 40/88 = **45.45%**，文件级 4/22 = **18.18%**。
- 漏掉的 4 个文件（`_nd_verify_out.txt:11`）：`ledger_bound_20261109/_lb2_TEMPLATE.md`、`s604_attribution_20261108/S604_ATTRIBUTION.md`、`s604_script_gap_20261109/S604_SCRIPT_GAP.md`、`s604_script_gap_20261109/_sg_FINDINGS.md`。
- 40 条漏行按类：`curly_corner` 新增 31 行 + `no_quote` 新增 9 行（`_nnv_verify_out.txt:26-30`）。其中 4 件整件被 `:229` 文件闸跳过（6 行），另 34 行通过文件闸但被 `:165` 行闸跳过，`:22` 在行闸集合内（`_nnv_verify_out.txt:80-85`）；6+34=40 与 |U−B| 对上。

### 3.2 引号变体 vs 其他变体（分类，不许混为一谈）

| 类 | 变体 | 性质 | 占 union | 归一能否解决 |
|---|---|---|---:|---|
| **引号变体（严格 3 类）** | `angle_corner` / `curly_corner` / `curly_double` | 仅包裹符**字符类别**不同（U+300C/D ↔ U+300E/F ↔ U+201C/D），核心汉字 `只能判…不可复现` 与「有引号」结构不变 | **79 行 / 22 件 = 89.8%** | **能**：L1 引号类归一覆盖 3/3（`_nd_verify_out.txt:13-17`），`curly_double` 语料 0 命中，属合成 fixture 常驻负控类 |
| 结构变体·去引号 | `no_quote` | 引号 span 消失，不是换字符；R5 `quoted_containing()` 依赖成对跨度，去引号直接改变 role 语义 | 9 行 / 7 件 = 10.2% | **不能**由引号归一解决；走显式补充轨 `r"只能判[「『“(]?不可复现[」』”)]?"` 单独召回并**强制重新判角色** |
| 结构变体·换括注 | `half_paren` | 半角括号，语料 0 命中 | 0 | 不能；只作合成负控 |
| 结构变体·插空白 | `no_punct` | 空白插入 + 无引号 | 0 | 不能；空白归一属 L2，项目按码位比对（`lead/gate_postmortem_20261109/GATE_LITERAL_MATCH_POSTMORTEM.md:70`，本轮直读确为「反引号/换行拆断标识符 raw=False→归一化 True」必须区分） |

把 `no_quote` 塞进归一键就是**过渡归一化**：`只能判不可复现`（裸断言）与 `只能判「不可复现」`（引文）会成同一句（§4.5 反例 CE1/CE5）。

### 3.3 重复计数去重规则（必须写死）

1. **单位 = `(file, line)` 集合**，不是「每个 needle 各计一次」。`48+34+0+9+0+0 = 91` 个「变体-行」对，去重后 **88 行**（差 3，`_nd_verify_out.txt:12`）。
2. **行级共现 3 处**（`_nn_variants_out.txt:143-152`）：`REFSYNC_SCOPE_FIX.md:17`、`_rs_CARRIER_MAP.md:60`、`_rs_CARRIER_MAP.md:188` 同时中 `angle_corner` + `curly_corner`。这 3 行各只记 **1 个 occurrence**。
3. **文件级共现 14 件**（`_nn_variants_out.txt:128-142`），故 `18+16+7=41 ≫ 22`；文件数由 `(file,line)` 集合派生，**禁止相加**。
4. **同一行同变体多次出现**仍只记 1 个 occurrence，但**每个命中偏移单独保留**（`REFSYNC_SCOPE_FIX.md:17` 的 angle×2 / curly×2，`_nn_variants_out.txt:145-146,153-156`），以便用 `orig_start/orig_end` 回溯原文位置；`_nd_verify_out.txt:17` 实跑 `mapped hits=85 ; length-preserving/orig-slice bad=0`。

### 3.4 L1 后的漏检率变化

| 方案 | 召回行 / 件 | 行级漏检率 | 文件级漏检率 | 出处 |
|---|---:|---:|---:|---|
| 只扫直角引号（基线） | 48 / 18 | **45.45%** | 18.18% | `_nd_verify_out.txt:8-11` |
| L1 只归一引号（修正版，§4） | 79 / 22 | **10.23%**（余 9 行 `no_quote`） | **0%** | `_nd_verify_out.txt:13-17`、`_nd_l1fix_out.txt:16-19` |
| L1 + 显式补充轨 | **88 / 22** | **0%**（零 FN / 零 FP） | **0%** | `_nd_verify_out.txt:23` |

L1 增益 +31 行（+35.23% vs union），L1 == 三引号变体精确并集（`FP=0 FN=0`，`_nd_verify_out.txt:16`）；补充轨 `SUPP = 88 行/22 件`、`L1|SUPP == U`（`:22-23`）。

---

## 4 归一化方案（层次 + 可粘贴片段 + 位置回溯 + 边界 + 反例）

### 4.1 层次（逐层给可否，不许用「已归一化」概括）

| 层 | 内容 | 采用 | 理由 |
|---|---|---|---|
| L0 | 人工列 needle 变体 | 否 | 正是 FAIL 根因；`REFSYNC_SCOPE_FIX.md:227` 自陈「变体短语靠人工列 + 无负控…漏了哪一类自己不知道」 |
| **L1（采用，但必须修正）** | **只归一 `PAIRS` 收录的引号类字符**：`「『“`→左哨兵、`」』”`→右哨兵、成对反引号交替→左/右哨兵；1:1 保长；其它码位原样；**召回后强制原文包裹符复验** | **是** | 覆盖 3/3 引号变体；不增删字符 ⇒ 位置恒等映射；保留「有引号」结构 ⇒ R5 可在原文上判。修正点见 §4.2 / §6.1 |
| L2 | 空白归一 / 删空格 / 换行折叠 | 否 | `GATE_LITERAL_MATCH_POSTMORTEM.md:70` 要求区分被反引号/换行拆断的标识符；`no_punct` 语料 0 命中，无收益有风险 |
| L3 | NFKC 全半角 / 兼容字符 | 否 | 会把 `ＡＰＰＲＯＶＥ＿ＳＣＯＰＥ` 并成 `APPROVE_SCOPE`（`_nn_norm_out.txt:75-79` `MERGED=True`） |
| L4 | 去标点 / 删引号 / 顿号逗号统一 | 否 | 改变引号跨度与句子边界，直接毁掉 R5 的 `ASSERTION` vs `REFUTING_QUOTE` 判据 |
| L5 | 近义 / 模糊 / 编辑距离 | 否 | `不可复现` ≠ `不可复原`（真实语料 5 行，`_nn_norm_out.txt:81-86`），不同命题 |
| 显式补充轨（**不归一**） | `no_quote` / `half_paren` / `no_punct` 用独立正则召回并重新判角色 | 是 | 结构变体不是引号变体；硬塞进 L1 即过渡归一化 |

**上一轮 L1 的缺陷（复核 verdict=partial 的主因，必须写清）**：`_nn_norm.py:23-25` 把 `‘’` 收进 `QUOTE_OPEN/CLOSE`、把 `` ` `` 收进 `SYMMETRIC`，与 `_rs_carrier_scan.py:79` 的 `PAIRS` 字母表不一致；且用 `\x01/\x02/\x03` 作哨兵，而语料确含 U+0001（`lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:3465`，本轮 `_nd_collision_out.txt:1-7` 实读）。结果：`只能判『不可复现」`（半错配）与 `只能判‘不可复现’`（未收录引号）被归到与 canon 相同的键 `只能判\x01不可复现\x02` 并召回，原文 `spans_of_quotes()` 却是 `[]`、`classify_line()` 掉到 `ASSERTION`（`_nd_verify_out.txt:39-45`、`_nnv_counterexamples_out.txt:38-58`）——**把「不成对/未知包裹符、语义应报 UNKNOWN」的句子当成规范带引号边界句**，即真实误合并。这 5 类合成变体在现盘 633 件 0 命中（`_nnv_synthetic_in_corpus_out.txt:1-6`），故当前零假阳，但「把不同意思的句子当成同一句」成立，裁定 partial。

### 4.2 可粘贴片段（修正版 L1，本轮实跑 `FIXTURE_SELF_TEST = PASS`）

完整可运行原型在 `lead/needle_norm_20261109/_nd_l1fix.py`；实跑命令与输出：

```
cd /d/Project/ra2-campaign-forge && python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/needle_norm_20261109/_nd_l1fix.py" > "D:/Project/ra2-campaign-forge/lead/needle_norm_20261109/_nd_l1fix_out.txt" 2>&1; echo "EXIT=$?"
```

`_nd_l1fix_out.txt:1-19`：`canon key = '只能判\ue000不可复现\ue001'`；9 条 fixture 全 PASS（`:4-13`）；`FIXTURE_SELF_TEST = PASS`（`:13`）；语料 `three quote-variant truth: lines=79 files=22`、`corrected L1 OK: lines=79 files=22`、`L1 == truth ? True ; FP=0 FN=0`（`:16-18`）；`mapped hits=85 ; orig_slice/norm bad=0`（`:19`）。

```python
# ---- 修正版 L1：字母表对齐 PAIRS、PUA 哨兵、召回后原文复验 ----
# 应当怎么改：把 _rs_carrier_scan.py:229 的文件闸与 :165 的行闸换成下面两个函数；
# 角色判定仍用原始 line（quoted_containing / NEG_LEX / UPDATED_SAMPLE 一字不改）。
import importlib.util, re

CANON = "只能判「不可复现」"
PAIRS = [("「", "」"), ("『", "』"), ("`", "`"), ("“", "”")]  # 同 _rs_carrier_scan.py:79
LQ, RQ, SQ = "\ue000", "\ue001", "\ue002"        # PUA 私用区：本轮实跑语料 PUA 冲突 = 0
SENTINELS = {LQ, RQ, SQ}

def norm(s):
    """1:1 保长：只归一 PAIRS 收录的引号类字符；其它码位（含 ‘’ 与控制符）逐字原样。
    反引号是对称对：按出现次序交替映射 LQ/RQ，仍 1 字符→1 字符。"""
    out, tick = [], 0
    for c in s:
        if   c in "「『“": out.append(LQ)
        elif c in "」』”": out.append(RQ)
        elif c == "`":
            out.append(LQ if tick % 2 == 0 else RQ)
            tick += 1
        else: out.append(c)
    return "".join(out)

QN = norm(CANON)     # '只能判\ue000不可复现\ue001'

def find_norm_candidates(line, spans_of_quotes):
    """返回 [(orig_start, orig_end, raw_text, status)]；status=OK 才允许并入 canon 身份。
    norm[j] 恒对应 line[j]（1:1 保长）⇒ orig_start/orig_end 直接是原文行内偏移。"""
    if SENTINELS & set(line):
        return []                          # 哨兵冲突：报 UNKNOWN，绝不猜
    n, res, pos = norm(line), [], 0
    while True:
        k = n.find(QN, pos)
        if k < 0: break
        a, b = k, k + len(QN)
        raw = line[a:b]
        # ★ 原文复验：命中片段的首尾包裹符必须构成 PAIRS 合法对，
        #   且 R5 spans_of_quotes(line) 恰有 (a+3, b) 这一跨度。
        #   半错配 『…」、未收录 ‘’、反配 』…『 一律 UNKNOWN / 不召回。
        exact = (len(raw) >= 3 and (raw[3], raw[-1]) in PAIRS
                 and any((x, y) == (a + 3, b) for x, y, _ in spans_of_quotes(line)))
        res.append((a, b, raw, "OK" if exact else "UNKNOWN"))
        pos = k + 1
    return res

# ---- 用法（应当怎么改，本件不改 _rs_carrier_scan.py） ----
# 文件级：删掉 :229 的 `if not any(n in txt for n in a.needle): continue`，
#         改为逐行调用下面的候选器；不得因「整件无直角 needle」跳过整件。
for lineno, L in enumerate(txt.splitlines(), 1):
    for (a, b, raw, status) in find_norm_candidates(L, spans_of_quotes):
        assert L[a:b] == raw and norm(L[a:b]) == QN      # 位置映射自检
        if status != "OK":
            role = "UNKNOWN: 需人工复核"                  # 对齐 R4 :248-250「绝不猜」
        else:
            role = classify_line_on_original(L, pos=a)     # R5 一律读原文，不读归一串
        print(file_rel, lineno, a, b, repr(raw), status, role)
    # 显式补充轨（结构变体，不并入归一键，单独召回 + 重新判角色）：
    # re.search(r"只能判[「『“(]?不可复现[」』”)]?", L)
```

### 4.3 位置可回溯

1:1 保长 ⇒ `norm[j]` 恒对应 `line[j]`，`idx_map` 是恒等映射；`find_norm_candidates` 返回的 `(orig_start, orig_end, raw_text)` 直接是原文行内偏移与原文逐字片段，`file:line` 由 `enumerate(lines, 1)` 给出，无需 span 对齐表。本轮实跑断言：`_nd_l1fix_out.txt:19` `mapped hits=85 ; orig_slice/norm bad=0`；`_nd_verify_out.txt:17` `mapped hits=85 ; length-preserving/orig-slice bad=0`；`_nn_norm_out.txt:34-37` `mapped hits checked = 85 ; all(orig_slice == reported_text) = True`，样例 `LEDGER_APPENDIX_DRAFT.md:123 orig[47:56] = '只能判「不可复现」'`。`orig_start` 可直接喂 `quoted_containing(line, pos)`（`_rs_carrier_scan.py:110-114`）。

### 4.4 ★ 归一化边界（哪些不能归一；过渡归一化即新错误）

1. **核心汉字一码不改**：`不可复现` ≠ `不可复原`（真实 5 行，`_nn_norm_out.txt:81-86`）/ `不可重复` / `不可再现`。L1 不碰汉字；`_nd_l1fix_out.txt:9` `只能判「不可复原」 -> NOT-RECALLED`。
2. **归一字母表必须等于 R5 `PAIRS`**（`_rs_carrier_scan.py:79`）：只认 `「」『』``“”`。`‘’` 不收录 ⇒ 不归一、不召回；`『…」` 交叉错配、`』…『` 反配 ⇒ `spans_of_quotes()` 无跨度，报 `UNKNOWN: 需人工复核`，绝不补造成 `ASSERTION`（`_nd_l1fix_out.txt:7-8,12`）。
3. **引号内 vs 引号外语义不同**：`spans_of_quotes()` / `quoted_containing()` 靠成对跨度决定 `REFUTING_QUOTE` / `QUOTED` / `ASSERTION`。归一只能**换**引号字符，**不能删**引号、不能把「有无引号」归一掉；`needs_fix`（`:257-258`）必错。
4. **不得删标点 / 改句子边界**：顿号 `、` 分隔的两条并列结论 vs 整句被一对引号罩住，span 不同、role 不同。
5. **不得删空白 / NFKC**：`| 只能判 | 不可复现 |` 是表格两列，不是一句话；全角标识符不是半角标识符（`GATE_LITERAL_MATCH_POSTMORTEM.md:70`）。
6. **不得把 `no_quote` 并入归一键**：只能作并列召回轨，各自保留角色判定结果。
7. **哨兵码位不得与语料冲突**：旧 `\x01` 在 `ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:3465` 真实出现（`_nd_collision_out.txt:1-3,6` 该行含 U+0001、不含锚词、`old-L1 norm(line).find(canon_key) = -1`，当前不致误召，但不能当「全语料无冲突」）；改用 PUA 并逐行预检，本轮实跑 PUA 冲突 = 0（`_nd_l1fix_out.txt:15`）。
8. **归一串只用于召回、不用于定谳**：`verbatim_cmp()`（`:130-140`）与 SHA256 一律在原始字节/原文；归一后的串不得写入台账、不得作为「同一句」的证据。

### 4.5 反例：过渡归一化导致误合并（≥3，逐条实跑）

`_nn_counterexamples_out.txt:81` `TOTAL: 7/7` 过度规则确实误合并且旧 L1 未合并；本轮 `_nd_verify_out.txt:38-45` 又独立复现了**旧 L1 自身**的两条误合并。下表「旧 L1 误合并」列即复核 partial 的依据；「修正版」列来自 `_nd_l1fix_out.txt:4-13`。

| ID | 过度规则 / 变体 | A（语义 1） | B（语义 2） | 误合并后果 | 修正版 L1 |
|---|---|---|---|---|---|
| CE1 | 删所有引号 | `只能判「不可复现」、不能定位当年错误步骤` | `只能判不可复现、不能定位当年错误步骤` | 裸断言与引文同键 | `NOT-RECALLED`（`_nd_l1fix_out.txt:10`） |
| CE2 | 删引号+删标点 | `只能判「不可复现」、不能定位当年错误步骤`（span 只罩 4 字） | `只能判「不可复现、不能定位当年错误步骤」`（span 罩整句） | `MERGED=True`（`_nn_norm_out.txt:60-62`），role 必错 | 键不同，不合并 |
| CE3 | 近义 / NFKC | `只能判「不可复现」` | `只能判「不可复原」` / `ＡＰＰＲＯＶＥ＿ＳＣＯＰＥ` | 不同命题当同一句；NFKC `MERGED=True`（`_nn_norm_out.txt:78`） | `NOT-RECALLED`（`:9`） |
| CE5 | 只比核心串（丢语境） | `**只能判「不可复现」…**`（§607 裸断言 `ASSERTION`） | `其边界句「只能判『不可复现』…」自本节起不再成立`（§609 `REFUTING_QUOTE`） | 把「否定该句」误当「断言该句」——本次 FAIL 的语义核心 | 全行键不同，role 在原文上分别判（`_nnv_counterexamples_out.txt:16-25`） |
| CE7 | 删引号 / 反配 | `只能判「不可复现」` | `只能判』不可复现『` | 反配引号被当成规范句 | `NOT-RECALLED`（`_nd_l1fix_out.txt:12`） |
| **V4（partial 主因）** | 旧 L1 收 `『`+`」` 交叉错配 | `只能判「不可复现」` span=`[(3,9,'「')]` | `只能判『不可复现」` span=`[]` | 两者 `FULL_KEY_MERGED=True`、`find_norm(B)=True`，B 被 canon 召回却 `classify_line=ASSERTION`，应报 UNKNOWN | `UNKNOWN`（`_nd_l1fix_out.txt:7`） |
| **V5（partial 主因）** | 旧 L1 收未收录的 `‘’` | `只能判「不可复现」` | `只能判‘不可复现’` | 同上 `FULL_KEY_MERGED=True`，R5 判不出 span 掉到 `ASSERTION` | `NOT-RECALLED`（`_nd_l1fix_out.txt:8`） |

---

## 5 两段式设计评估（needle 精确匹配 + 角色后判）

### 5.1 失效链（needle 漏 → 角色判定没机会跑）

```
:229 文件级 needle 精确闸 ─┐
                          ├─ 任一漏 ⇒ 该 (file,line) 不进 carriers
:165 行级 needle 精确闸 ──┘                ↓
                              :327-331 role_of() 返回 <not-scanned>
                                              ↓
              R4 blocks_of(:232) / R5 classify_line(:238) / needs_fix(:257-258) 全部没有机会跑
```

本轮量化（`_nnv_verify_out.txt:80-85`）：4 件整件被 `:229` 跳过（6 行）+ 34 行被 `:165` 跳过 = 40 行 = |U−B|，`:22` 在行级集合内。即**两段式的第一段是硬丢弃**，第二段的角色判定再正确也救不回没进集合的行。双 needle 的假 PASS（§2.3）只是把硬丢弃换成了「靠另一条 needle 侥幸捞回」，不是设计修好。

### 5.2 宽泛捞候选方案 + 质量评估（本轮 `_nd_verify.py` 实跑）

| 候选口径 | 行 / 件 | 与真值 U(88/22) 的关系 | 出处 |
|---|---:|---|---|
| W1 单词 `不可复现` | **188 / 45** | +100 行 FP（100/188 = 53.2%） | `_nd_verify_out.txt:18,24` |
| W2 锚词 `只能判` | 94 / 28 | — | `:19` |
| **W3 双锚共现 W1∩W2** | **88 / 22** | `U-W3=0 W3-U=0`，恰等于 U | `:20,24` |
| **W4 正则 `只能判.{0,3}不可复现`** | **88 / 22** | `U-W4=0 W4-U=0`，恰等于 U | `:21,24` |
| 显式补充轨 `SUPP` | 88 / 22 | `L1\|SUPP == U` | `:22-23` |

- **量**：单词级 W1 噪声 100 行（上一轮 99 行；本轮新增 1 行来自 `gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md:470`「74 条数字不可复现」，本轮实读确认不含 `只能判`）。收窄到双锚 / 短间隙正则后零 FP 零 FN。`W1-U 中含 只能判 的行数 = 0`（`:24`）——99/100 行全是「提到『不可复现』这个词但不在说这句边界句」的其他命题，是真噪声，不是漏检。
- **质**：`_nnv_noise_check_out.txt` 复核 W1−U 的 99 行中 83 行含引号、44 行是 §604 主题、9 行门禁/载体主题、5 行「不可复原」；把它们并入会污染载体图。
- **可执行盲区（复核回件 ⑦，如实登记）**：`_nnv_gate_probe_out.txt:12-16` 注入 `只能判 —— 不可复现`（间隙 4 字）→ 集合差门禁 FAIL，但 W4 与补充轨都召不回；`_nnv_gate_limits_out.txt:5-7` 注入间隙 >4 字 → 发现器窗口外、集合差 = 0、门禁**不报警**，仍存在「漏了哪类自己不知道」的残余盲区。故「发现 ≠ 召回」，§6.3 必须补第二道门禁。

### 5.3 修正设计：宽候选 + 原文角色收窄（应当怎么改）

```
阶段 0  召回（宽、不丢）：删除 :229 的整件 needle 预过滤。
        候选 = 修正版 L1 find_norm_candidates()   ∪   W4 双锚正则
               ∪   显式补充轨（no_quote 等结构变体）
        原则：候选只 ADD 到 carriers，绝不因「不像 needle」而 DELETE。
        每个候选带 (file,line,orig_start,orig_end,raw_text,status,变体类)。
阶段 1  角色（严、在原文）：classify_line(原始 L, pos=原文偏移)。
        quoted_containing() / NEG_LEX / UPDATED_SAMPLE 全部读原文；
        status=UNKNOWN（错配/未收录引号/哨兵冲突）→ 报 UNKNOWN，不猜。
阶段 2  区块与风险（不变）：blocks_of() / APPENDABLE_BLOCK / needs_fix 保持 R4/R5 原样。
阶段 3  输出：同一 (file,line) 多变体命中只记 1 行，variants 字段列全部类目。
        needs_fix 门槛（ASSERTION ∧ HIGH）一字不放宽。
```

| 维度 | 现行两段式（精确 needle + 角色后判） | 建议（宽泛捞候选 + 原文角色收窄） |
|---|---|---|
| 漏检 | 45.45% 行 / 18.18% 件 | 0%（本语料 W3/W4 = U） |
| 假阳 | 0（靠「没扫到就不报」掩盖漏） | 0（W3/W4 恰等于 U）；单词 W1 才 100 行 FP，不采用 |
| 角色判定 | 有，但 needle 漏时**根本不执行** | 必执行，且在原文上执行 |
| 新变体类 | 需人工列，漏了不知道 | 双锚/正则天然覆盖新包裹符；配合 §6.3 集合差门禁 |
| 代价 | 低但结论不可信 | 候选 48→88（+40 行）需过 R5，人工复核增量 40 行而非 100 行 |

**哪种更适合本项目**：建议方案。依据（均实读/实跑）：语料规模小——`REFSYNC_SCOPE_FIX.md:171` 全量无深度上限 `.md` = 947、`:253` 全扩展名 = 5500（仅审计不作施工数）；88 行/22 件逐行复核可行；同一句被复制进多个草案（R2 的 N carriers），角色判定一次写对可批量复用；项目实际风险是**漏**（`_ve_DRAFT_S609.md:22` 明写「自本节起不再成立」却可能不被发现，`REFSYNC_SCOPE_FIX.md:227` 自陈教训），不是 FP 淹没。**不建议**单词级 W1（188 行 / 100 行 FP）。

---

## 6 复核回件 + 修正后的自检方案 + 未验项

### 6.1 复核回件（verdict 如实记）

【复核】块给出的裁定：**`verdict = partial`**（非 refuted）。按本轮 ask 的口径「refuted 或 partial 标 unconfirmed」，本件对上一轮 L1 归一化方案的结论标 **`unconfirmed`**——修正版 L1 已在本写域原型上实跑 `FIXTURE_SELF_TEST = PASS`、`L1 == truth FP=0 FN=0`（`_nd_l1fix_out.txt:13,18`），但**未在真实 `_rs_carrier_scan.py` 上集成实跑**，不得升格为 confirmed。

复核回件 8 项要点本轮核验：
- ① 指纹 9/9 MATCH、`git log -1` = `2657458`、未 commit/push —— 本轮复算通过（§2.1）。
- ② FAIL 复现 —— 本轮 `EXIT=1` / `SELF_TEST = FAIL` / `got=<not-scanned>` 通过（§2.2）；复核记「现盘 634 件、65 行、19 件」，本轮现盘已漂移为 636/65/19，`_nd_repro_single_out.txt:10` 如实登记。
- ③ 机制（`:229` / `:165` / `:168-189` / `:327-331`）—— 本轮直读通过（§2.3）。
- ④ 量化 —— 本轮 `_nd_verify_out.txt` 逐项一致（§3）。
- ⑤ **误合并（partial 主因）** —— 本轮 `_nd_verify_out.txt:39-45` 独立复现 V4/V5：`FULL_KEY_MERGED=True`、`find_norm(B)=True`、`spans=[]`、`classify_line(B)=ASSERTION`，与 `_nnv_counterexamples_out.txt:38-58,75-76` 一致。上一轮 `_nn_REPORT.md:250` 虽写「反配/不成对引号应报 UNKNOWN」，但无可执行规则。修正版见 §4.2。
- ⑥ 失效链非复述 —— `_nnv_verify_out.txt:80-85` 的 4+34=40 重算通过。
- ⑦ 集合差门禁非空话但有 4 项盲区 —— `_nnv_gate_probe_out.txt:12-16`、`_nnv_gate_limits_out.txt:5-7` 实跑见 §5.2；另复核指出 `_nn_widenet.py:114` 用「10 类 − 2 大类」混口径算出「未覆盖 8 类」，按同类目真实集合差应为 **7**（本轮 `_nd_verify_out.txt:36-38` `discovered=10 covered=3 DIFF=7 -> FAIL`，与 `_nnv_verify_out.txt:99-100` 一致），本件采用 7。
- ⑧ 越界：9/9 末态 MATCH、只读域无改动、`git log -1` 未变 —— 本轮通过（§2.1）。

复核回件要求的绑定行（格式固定，紧跟完整 64 位十六进制，随后「，字节数 = 」+数字）：

被核对象 SHA256 = 9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57，字节数 = 16053

（`_rs_carrier_scan.py`，本轮起末两次自算一致；其余 8 件的同格式绑定行见 §2.1。）

### 6.2 修正后的负控自检方案（负控该含哪些项）

现行 6 项在 `_rs_carrier_scan.py:332-339`：5×`ASSERTION`（全 `angle_corner`）+ 1×`REFUTING_QUOTE`（`:22`，`curly_corner`）。本轮类目覆盖矩阵（`_nd_verify_out.txt:36-38`）：自动发现 10 个 `(pre,post)` 类，6 负控只覆盖 3 类（`('「','」、')`、`('「','」，')`、`('『','』、')`），`DIFF=7` ⇒ 门禁应 FAIL。按六变体大类则是 4/6 类零负控（`curly_double` / `no_quote` / `half_paren` / `no_punct`）。合格自检至少含：

1. **每变体类 ≥1 正控 + ≥1 负控**：`angle_corner` / `curly_corner` / `curly_double` / `no_quote` / `half_paren` / `no_punct` 各一条；0 命中类用**合成 fixture 常驻**（`_nn_norm_out.txt:98-109` 的 `POS-curlyDbl` / `NEG-halfparen` / `NEG-nopunct`，`FIXTURE_SELF_TEST = PASS`）。`no_quote` 必须补真实锚点（`_lb_BOUND_VOLUME.md:226` 等 9 行）。
2. **每个 needle 单独跑一次自检**：禁止用双 needle 联合跑替代（§2.3 假 PASS 掩盖效应）。
3. **role × 变体交叉矩阵**：`ASSERTION` / `REFUTING_QUOTE` / `QUOTED` / `UPDATED_SAMPLE` / `ANALYSIS_MENTION` 各 1 条 × 各变体类，防归一后 role 漂移。
4. **旧 L1 自身边界负控（partial 直接补丁）**：V4 `只能判『不可复现」`、V5 `只能判‘不可复现’`、反配 `只能判』不可复现『`、反引号对 `只能判`不可复现`` 必须分别为 `UNKNOWN` / `NOT-RECALLED` / `NOT-RECALLED` / `OK`（`_nd_l1fix_out.txt:7-8,11-12`）；上一轮 7 条 CE 全只测「别的过度规则」，无一条测 L1 自身边界，必须补。
5. **哨兵冲突负控**：注入含 U+0001 与含 PUA 的行，断言旧哨兵方案报冲突/UNKNOWN、修正版不误召（`_nd_collision_out.txt:1-7`、`_nd_l1fix_out.txt:15`）。
6. **位置回溯断言**：每条命中 `L[a:b] == raw_text` 且 `norm(L[a:b]) == QN`（85/85，`_nd_l1fix_out.txt:19`）。
7. **过度归一反例断言**：CE1–CE7 全部 `L1_MERGED = False`（`_nn_counterexamples_out.txt:81` 7/7），这是「不许过渡归一化」的机器门禁。
8. **已知假阴性路径**：`REFSYNC_SCOPE_FIX.md:264` 自陈 `NEG_LEX` 整行子串会把裸断言翻成 `ANALYSIS_MENTION`，补 2 条合成 fixture。
9. **`<not-scanned>` 硬失败**：任何期望项返回 `<not-scanned>` 即 `EXIT=1`，并区分「判错 role」与「根本没扫到」。
10. **指纹绑定**：每次自检重算 9 件 SHA256/字节数比对编排方基线，防语料漂移让负控「碰巧 PASS」。

### 6.3 怎么保证不再「漏了哪类自己不知道」+ 自检必要性

**两道门禁（缺一不可）**：

```
门禁 A（发现）：不靠人工列举。用全语料 re.finditer(r"只能判(.{0,4}?)不可复现(.{0,2})", L)
                自动枚举 (pre,post) 类目；本轮实跑 10 类（_nd_verify_out.txt:25-35）。
                把「自检 fixture 覆盖类集合」与「自动发现类集合」做差，差集非空 ⇒ SELF_TEST = FAIL。
                本轮 discovered=10 covered=3 DIFF=7 -> FAIL（:36-38）。
                每个未覆盖类自动打印一条真实锚点（:26-35），直接补成负控。
门禁 B（召回，新增，补复核 ⑦ 的盲区）：对每个已发现类目注入一条合成样本，
                断门「候选器必须召回该类」；召不回即 FAIL。
                依据：_nnv_gate_probe_out.txt:12-16 的 '只能判 —— 不可复现' 能被 A 发现，
                但 W4/补充轨都召不回；_nnv_gate_limits_out.txt:5-7 的超窗口变体连 A 都不报。
                再加一条「发现器窗口自检」：注入窗口外长间隙样本，断言 A 至少报「窗口外未覆盖」
                （当前实现做不到，标为未验/待设计，不补造）。
语料变更门禁：每次语料变更后重跑 A+B；新 (pre,post) 或新长间隙立刻报警。
```

**自检必要性**：不跑自检**不会**发现——单 needle 下 `:22` 是 `<not-scanned>`，A/B/C 段只是少了 1 行/4 件，`scanned files` 看似正常，`needs_fix` 照常产出，D 段还宣称「:22 is KEPT in section A」；跑了自检**也可能不发现**——`REFSYNC_SCOPE_FIX.md:251` 的双 needle 交付口径 `SELF_TEST = PASS 6/6`（本轮 `_nd_repro_twoneedle_out.txt:675` 复现）。本次 FAIL 之所以暴露，是编排方用**单 needle** 重跑了负控。结论：自检必须跑，且自检自身必须有「覆盖度门禁 + 单 needle 隔离 + 召回门禁」；只跑覆盖不足的自检等于没跑。

### 6.4 未验项（不补造）

1. **修正版 L1 未在真实 `_rs_carrier_scan.py` 集成实跑**：铁律禁止改它；只在 `_nd_l1fix.py` 原型 + 9 条 fixture + 635 件语料集合等价上验证（`_nd_l1fix_out.txt:13-19`）。标 `unconfirmed`（§6.1）。
2. **947 / 5500 件口径全量回归未跑**：`REFSYNC_SCOPE_FIX.md:171,253` 的数字仅为上游登记，本轮未在无深度上限/全扩展名口径重跑，不宣称。
3. **发现器窗口外变体的自动告警未实现**：`_nnv_gate_limits_out.txt:5-7` 证明「超 4 字间隙」既不被发现也不被召回、门禁不报警；§6.3 门禁 B 的「窗口自检」是设计建议，未落地实跑。
4. **PUA 哨兵只在本轮 635 件语料验证冲突 = 0**（`_nd_l1fix_out.txt:15`）；947/5500 件口径未扫，不宣称全语料无冲突。
5. **`curly_double` / `half_paren` / `no_punct` 及 V4/V5 等 5 类合成变体在现盘 0 命中**（`_nnv_synthetic_in_corpus_out.txt:1-6`），其负控只能靠 fixture，不能靠真实锚点；「当前零假阳」不等于「规则无边界错误」。
6. **语料漂移**：起始 631 → 上一轮 633/634 → 本轮 636（排除写域 635）。本件所有结论数字以本轮 `_nd_verify_out.txt` 实跑为准；`_nd_repro_single_out.txt:10` 的 `636 / 65 / 19` 含写域自引，不得再当作「精确 631/48/18」引用。新增 2 件对六变体零命中，union 仍为 22 件/88 行。

---

## 附：本轮实跑命令清单（全部只读 / 仅写本写域）

| # | 命令 | 输出 / 结果 |
|---|---|---|
| 1 | `python -I -X utf8 -c` + hashlib 自算 9 件（起、末各一次） | 9/9 MATCH，`TOTAL MATCH = 9 /9` |
| 2 | `python -I -X utf8 ".../_rs_carrier_scan.py" --needle "只能判「不可复现」" --include-refuting --max-depth 2 --ext .md > .../_nd_repro_single_out.txt` | `EXIT=1`、`:428 got=<not-scanned>`、`:430 SELF_TEST = FAIL`、C 段只 `:69/:70` |
| 3 | 同上双 needle（`REFSYNC_SCOPE_FIX.md:251` 口径）`> .../_nd_repro_twoneedle_out.txt` | `EXIT=0`、`:673 PASS :22`、`:675 SELF_TEST = PASS`（掩盖效应） |
| 4 | `python -I -X utf8 -c` 直读 `_ve_DRAFT_S609.md:22/:69/:70` 码位 | `:22 angle=False curly=True`；`:69/:70` 反之 |
| 5 | `python -I -X utf8 -c` 读 `GATE_LITERAL_MATCH_POSTMORTEM.md:70`、`REFSYNC_SCOPE_FIX.md:171/227/251/253/260/264` | 逐字引用见 §2/§4/§5 |
| 6 | `python -I -X utf8 ".../_nd_verify.py" > .../_nd_verify_out.txt` | 635 件；六变体 18/16/0/7/0/0；union 22/88；漏 4 件 40 行；L1 79/22；W1=188/45、W3=W4=U；DIFF=7 |
| 7 | `python -I -X utf8 ".../_nd_collision.py" > .../_nd_collision_out.txt` | `ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:3465` 含 U+0001、不含锚词、旧 L1 `find=-1` |
| 8 | `python -I -X utf8 ".../_nd_l1fix.py" > .../_nd_l1fix_out.txt` | `FIXTURE_SELF_TEST = PASS` 9/9；`L1 == truth FP=0 FN=0`；85/85 映射 |
| 9 | `python -I -X utf8 -c` 现盘语料计数 + PUA 扫描 + 2 件新增件定位 | 全部 636 / 排除写域 635；PUA 冲突 0；`GATE_PIPELINE_COMPOSE.md:470` 为新增 W1 噪声行 |
| 10 | `git log -1 --oneline`、`git status --short -- lead/needle_norm_20261109/` | `2657458` 未变；写域仍 `??`，无 commit/push |

**纪律复核**：本轮仅新建 `NEEDLE_NORMALIZATION.md`、`_nd_repro_single_out.txt`、`_nd_repro_twoneedle_out.txt`、`_nd_verify.py` / `_out.txt`、`_nd_collision.py` / `_out.txt`、`_nd_l1fix.py` / `_out.txt`，全部在 `lead/needle_norm_20261109/`；未改 `_nn_*` / `_nnv_*` 任何既有件，未改只读域与两件台账。零真机、零采样代码、未 commit/push。
