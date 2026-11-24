# _gp_DESIGN.md — 三层谓词合成链：顺序、冲突消解、分层回归

- 日期：2026-11-09；唯一写域 `lead/gate_pipeline_20261109/`，前缀 `_gp_`。
- 零真机、零采样代码；Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib`。
- **本任务只做合成设计与冲突消解**：未改任何既有谓词模块、未改任何交付件、未 commit/push。
- 编排方派发的 10 件指纹逐件重算全 MATCH（实跑命令与输出见 §0）。

---

## 0 实跑命令、输出与零漂移核对

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_probe.py       > lead/gate_pipeline_20261109/_gp_probe_out.txt
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_pipeline.py
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_regression.py  > lead/gate_pipeline_20261109/_gp_regression_out.txt
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_n13_20261109/_n13_regression.py
```

`_gp_probe.py` 输出（逐字，`_gp_probe_out.txt` 开头）：

```
== 指纹 ==
  lead\gate_fp7_20261108\_g7_predicates.py ['02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120', 11743]
  lead\gate_n13_20261109\_n13_predicates.py ['e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079', 16649]
```

零漂移核对（本会话末次实跑，10 件只读件 + 两件台账逐件 `hashlib.sha256`）：`ALL_ZERO_DRIFT= True`。
`lead/gate_v1v2_20261109/` 目录存在（编排方清单 11 件逐字对齐），`lead/gate_r9sem_20261109/` **不存在**
（`ls` 报 `No such file or directory`）——语义要素升级件尚未落盘，本任务不依赖它，如实记「未验」。

**复核回件绑定行（格式固定，逐字）**：

被核对象 SHA256 = 05ecdfca451476bb80d84281068fcd9c59d1364b2247cb5482943de6417781fc，字节数 = 20651
被核对象 SHA256 = 5102beae1ecf4952862d4ff1319283df816c53a49bdc81bae38d9709bef974e3，字节数 = 38232
被核对象 SHA256 = 47bb594b90e1c49cbbd83086468cbadb4bda05458d82cb7808661f975daf0b70，字节数 = 70587

---

## 1 第一步：三层现状复核

### 1(a) 输入/输出契约（自己 `import` 两模块实跑）

`_gp_probe.py` 用 `inspect.signature` + 真实返回值容器实测（`_gp_probe_out.json` 的 `contracts` 段）：

| 谓词 | 输入契约 | 输出契约 | 代码位置 |
|---|---|---|---|
| 提取器（现状） | `text` + 正则（从 GATE_CODE 源码 `ast.literal_eval` 提取词表/正则） | `ast.literal_eval` 结果 / `P` 问题列表；**`BANNED_RE.search`、`LOOP_RE.finditer`、`BIND_RE.search` 只取首个 match** | `lead/gate_doc_name_fix_20261109/_dn_regate_domains.py:19-22,65,70,76` |
| R9 `r9_check(text,tokens)` | 文本 + 必需要素词表 | `(problems:list, warnings:list)`；`r9_element_present` 返回 `(bool, "raw"|"normalized"|"")` | `_g7_predicates.py:46-65` |
| R10 `r10_scan(text,assert_tokens)` | 文本 + 越权词表 | `(problems:list, warnings:list, hits:list[dict])`，`hits` 含 `token/pos/kind/neg_count/in_span` | `_g7_predicates.py:113-130` |
| R12 `r12_scan(text,assert_tokens)` | 文本 + 越权词表（**内部再调 `r10_context`**） | `(problems:list, hits:list[dict])` | `_g7_predicates.py:134-148` |
| R11 `r11_scan(text,doc_dir,root=None,recompute=None)` | 文本 + **写域/文档目录** + 仓库根（要读盘回验 hash） | `(problems, warnings, bindings[dict])` | `_g7_predicates.py:157-222` |
| N13 `r13_scan(text,tokens,r10_scan=None,r12_scan=None)` | 文本 + 自带三词 `DEFAULT_TOKENS` + **两个可注入的函数**（R10/R12） | `(has_ab:bool, details:list[dict])`；`details` 含 `token/pos/line/quote/kind∈{A,B,C,D}/exempt/rule/r10_kind/degraded` | `_n13_predicates.py:183-304` |
| N13 `r13_assertions(...)` | 同上 | `(problems:list, details:list)`，problems 只含 D 类 | `_n13_predicates.py:307-313` |

实测返回容器（`_gp_probe_out.txt`）：

```
_return_container_types_demo => {"naive_gate": ["list"], "r9_check": ["list", "list"],
 "r10_scan": ["list", "list", "list"], "r12_scan": ["list", "list"],
 "r11_scan": ["list", "list", "list"], "r13_scan": ["bool", "list"],
 "r13_assertions": ["list", "list"]}
```

**契约不对齐的三处硬事实**（后面全部冲突几乎都来自这里）：
1. **词表不对齐**：N13 默认只认 `('已入账','已追加','已生效')`（`_n13_predicates.py:25`）；R10/R12 认调用方给的词表，本会话真件用的是 C07 域 `['已补登','已填入','已填','已代填']` / `['已填','已代填','已提交']`（`lead/gate_v1v2_20261109/_v12_probe.py:15-18`）与 BAD_BAN 五词（`_g7_reverse_validate.py:26`）。R10 报的 `已填` 在 N13 眼里**根本不是 span**，`ABSENT ≠ PASS`。
2. **位置口径不对齐**：R10 `pos` 是原文本下标；N13 `gpos` 按 `splitlines()` 累加 `len(line)+1`（`_n13_predicates.py:207,225,293`）。实跑 LF/CRLF 对照：`前一行说明\n本笔已入账…` 时两层 `pos=8` 对齐；换成 CRLF 时 R10 `pos=9`、N13 `pos=8`，`r10_kind` 从 `assertion` 变成 `None`（`(token,pos)` 键失配）。三件真件均为 LF（`_gp_probe_out.json` 记 `crlf=0`），故本次对齐成立；**这是条件，不是保证**。
3. **语义要素升级件缺席**：`lead/gate_r9sem_20261109/` 不存在；R9 仍是字面匹配 + 包裹归一化（`_g7_predicates.py:31-44`），「结构在场、字面不在场」判不了（`lead/gate_r9r12_20261109/_g9_regression.md:171`）。

### 1(b) 三件真件逐件结果（自己实跑，非二手转录）

`_gp_probe.py` 三条词表口径都跑。下表引号内数字均为实跑输出，见 `_gp_probe_out.txt` / `_gp_probe_out.json`。

**C07_SLOT**（`lead/c07_slot_20261109/C07_IDENTITY_SLOT.md`，20651 B，指纹 MATCH）
- 编排方 C07 词表 `['已补登','已填入','已填','已代填']`：**R9 0 / R10 problems=5（assertion 5 + negation 1，occurrences=6）/ R12 0 / R11 0（bindings=5，全 path=null→仅警告）/ N13 0（A/B/C/D 全 0）**。
- N13 三词与 BAD_BAN 五词口径：四层全 0——**因为该件不含这三个词**。编排方给的三层组合实跑 `r10_problems: 5` 复现无误。
- N13 对该 6 处 `已填` 的逐处记录：**0 条**（`conflicts_C07_task.only_r10=6`）。

**TRUTH**（`C07_TRUTH_SELF_PROOF.md`，38232 B，指纹 MATCH）
- C07 词表 `['已填','已代填','已提交']`：**R9 0 / R10 problems=2（assertion 2 + negation 1，occurrences=3）/ R12 0 / R11 0（bindings=15，全 path=null）/ N13 0**。编排方 `r10_problems: 2` 复现。
- `only_r10=3`：N13 对这 3 处无逐处记录。

**BOUND**（`LEDGER_BOUND_VOLUME.md`，70587 B，指纹 MATCH）
- N13 三词 / BAD_BAN 五词两条口径相同：**R9 0 / R10 problems=5（assertion 5 + negation 2，occurrences=7）/ R12 0 / R11 problems=1（"引用锚指向不在盘对象 sha256Line（R11/R3-3c）"，bindings=11）/ N13 problems=0，details 分布 A=2 B=3 C=2 D=0**。
- 逐 span 对齐 7 处，`differ=5`（详见 1(c)）。

补充：N13 若被强行喂 C07 词表，三真件会报 **SLOT 6 条 D / TRUTH 3 条 D / BOUND 0 条**（实跑，见 §4 的 REAL3 行）——N13 的 A/B/C 是围绕「已入账/已追加/已生效」设计的，`已填/已代填` 的疑问式/表头/禁止管辖它一个都不认。这是**词表契约冲突**，不是判据对错。

### 1(c) 冲突面：逐处列

**BOUND 的 5 处「R10 抓住 / N13 放过」**（同一 `(token,pos)` 上两层真值相反；`_gp_probe_out.txt` 逐行）：

| pos | 行 | token | R10 | R12 | N13 | 原文（截断） |
|---|---|---|---|---|---|---|
| 3672 | 54 | 已入账 | `assertion` CATCH | 0 | `B` 放过 | `## 2 · 上游指纹（十一件）… + 已入账 grep 结果` |
| 5867 | 77 | 已入账 | `assertion` CATCH | 0 | `B` 放过 | `### 2.2 待入账清点 + 已入账 grep 结果` |
| 5882 | 79 | 已入账 | `assertion` CATCH | 0 | `A` 放过 | `**已入账核查实跑命令**：` |
| 6305 | 87 | 已入账 | `assertion` CATCH | 0 | `B` 放过 | `| 笔 | 暂编 | … | 已入账? |` |
| 35513 | 338 | 已入账 | `assertion` CATCH | 0 | `A` 放过 | `本交付件按任务要求改为「## 1」到「## 5」五节：§1 总览 / §2 … + 已入账 grep / §3 …` |

另 2 处（pos=19877 L209、pos=24534 L242）R10=`negation` 放过、N13=`C` 放过，**一致，非冲突**。

**反向「N13 抓住 / R10 放过」**：三件真件里 **0 处**；但 N13 自带回归里有，实跑 `_n13_regression.py` §5（本会话实跑）：

```
TEXT: 不宣告 X 已生效，但 Y 已入账
   R10 kinds: [('已入账','negation'), ('已生效','negation')] problems: []
   R12 problems: []
   N13: FAIL [('D','同句混用：行内另有肯定断言…'), ('D','同句混用…')]
TEXT: 并非不宣告已生效
   R10 kinds: [('已生效','double_neg')] problems: []
   R12 problems: ['越权断言 已生效（R12：回看窗含双重否定构式=肯定）']
   N13: FAIL [('D','R12 双重否定构式=肯定')]
```

**第三类冲突（词表外）**：SLOT 6 处 / TRUTH 3 处 `已填`，R10 有明确 `assertion/negation` 判定，N13 **完全无 span**（`ABSENT`）。这不是「另一层说放过」，是「另一层没参与」；绝不能当作一致。

**结论**：三件真件的冲突面共 **5 处真值相反 + 9 处词表外无答案**，全部如实登记，不靠调顺序抹平。

---

## 2 第二步：合成顺序

### 2(a) 建议判定链（逐层理由）

```
L0 提取器（全量 finditer + 行号 + eol 类型 + 指纹）
 ├─→ L1 R9 要素在场 ────────────────────────────────┐
 ├─→ L5 R11 绑定回验 ───────────────────────────────┤  独立项，可并行
 └─→ L2 R10 语境分类（宽进）                        │
        ├─→ L3 R12 双重否定（消费 r10_context 的 dbl）│  断言面主链
        └─→ L4 N13 A/B/C/D（消费 L2 hits + L3 hits） │
                    ↓                                │
        L6 逐 span 冲突消解（不覆盖，只裁决 + 登记）←─┘
                    ↓
        L7 结论（problems / conflicts[] / NEEDS_HUMAN）
```

- **L0 提取器在最前**：修 `_dn_regate_domains.py:65/:76` 只取首个 `search` 的提取器假象（编排方背景点名 3 条误报即由此来）。用 `finditer` 全量，产出 `(token,pos,end,line,eol)`，后续所有层共享这一个 span 集合；同时记录 `CRLF/LF`，因为 1(a) 实测 CRLF 会让 N13 的 `gpos` 与 R10 的 `pos` 错位。
- **L1 R9 第二**：它是「要素在场」的独立门槛，与越权断言面正交；先跑可在后续层之前把「缺要素」类问题独立定案，不被断言层结果污染。`r9_check` 只需 `text+tokens`。
- **L2 R10 第三**：宽进层，对每个字面命中都产 `kind`（`_g7_predicates.py:118-122`）。它不判断「该不该扫」，只判断「这一处是什么语境」，所以必须尽早拿到全量 span。
- **L3 R12 第四**：`r12_scan` 内部直接调 `r10_context(text,pos)`（`_g7_predicates.py:144`），是 R10 分类的**消费者**；放在 R10 之后是数据依赖，不是优先级。R12 只处理 `kind=='double_neg'`，把它从 R10 的「不报」升级为「报」。
- **L4 N13 第五**：`r13_scan` 的签名里 `r10_scan`/`r12_scan` 是注入参数（`_n13_predicates.py:183,195-202`），它按 `(token,pos)` 查 R10 的 kind、按集合查 R12 命中，**是两层的消费者，不是替代者**。它做精筛：微段边界比 R10 的 `CLAUSE_BREAK` 更细（`:32`）、加行级同句混用守卫（`:163-177`）、加词表拆分裂缝（`:147-160`）。必须拿到 L2/L3 的完整 hits 才能跑。
- **L5 R11 与 L1–L4 并行**：它要 `doc_dir` + 读盘重算 sha256（`_g7_predicates.py:169-174,192-215`），是所有层里唯一有 I/O 与写域依赖的；与断言面无数据往来。`_g9_gate.py:24` 现有顺序把 R11 放最后只是收尾习惯，非依赖。
- **L6/L7 最后**：裁决与结论必须在所有层的返回齐了之后做；**位置靠后不代表它的意见更高级**。

### 2(b) 宽进 / 精筛的依据

- **宽进（宁可多报）**：提取器（全量 finditer）、R10（每命中必产 kind，`assertion` 即 FAIL）、R12（双否定一律报）、朴素门禁（字面子串即报）。实测：naive 在 74 条合成语料上 **FP=33**（`_gp_regression_out.txt`）；R10 **FP=20 / FN=19**；R12 单跑 **FN=35**（它本来就不是全量判据）。
- **精筛（只保留真断言）**：N13（A/B/C 放过、D 才 FAIL）、R9（包裹归一化只对「raw+normalized 双缺」判 FAIL）、R11（放宽绑定行匹配但只对失配/不在盘判 FAIL）。实测 N13 单跑 **71/74 正确、FP=0、FN=3**，其自带回归 **正 16/16 放过、负 26/26 抓住、真件 0 D、ALL_PASS=True**（本会话实跑 `_n13_regression.py`）。
- **宽进必须在精筛之前**：不是因为「谁更严」，而是因为精筛层的**输入就是宽进层的输出**。`_n13_predicates.py:195-202` 明确要求传入 `r10_scan`/`r12_scan`；没有 R10 的 hits，N13 的 C 类会降级成「无 R10 → 默认 FAIL」（`:257-259`），反而把 16 条正样本误拦。**反过来放不行**：R10 之后只剩 `problems/warnings/hits`，`quote_mention` 与 `assertion` 的语境信息已在 `problems` 里丢失（`lead/gate_v1v2_20261109/_v12_REPORT.md:263` 也独立得出同一结论）。
- **但宽进的 `problems` 绝不能直接并进最终结论**：这是本任务实跑抓到的头号陷阱，见 §4(d)。

### 2(c) 并行层与合并规则

可并行：**L1(R9) / L5(R11) / 断言面主链(L2→L3→L4)** 三路；L2 与 L3 也可并行（两者都只依赖 text+tokens，R12 内部自己重算 `r10_context`，不消费 R10 的返回对象）——`_g7_predicates.py:141-148` 与 `:113-130` 无相互赋值。

实跑验证（本会话，5 线程 `ThreadPoolExecutor` 对 BOUND 件）：

```
PARALLEL_VS_SERIAL: {"R9_equal": true, "R10_equal": true, "R12_equal": true,
                     "N13_equal": true, "R11_equal": true} ALL_EQUAL= True
```

合并规则（三条，全部可执行）：
1. **按 `(token,pos)` 做 outer join**，键取 L0 提取器的全量 span；某层没有该键记 `ABSENT`，**不得记 `PASS`**。
2. **独立项（R9/R11）取并**：它们的 `problems` 与断言面正交，直接并入最终 problems，rule_id 保留。
3. **断言面（R10/R12/N13）不做并集**：逐 span 走 §3 的 K1–K9 裁决表，产出 `ADJUDICATED` problem；每个分歧另记 `conflicts[]`（无论裁决结果）。
4. 合并前必须校验 `eol`：若 `CRLF`，把 N13 的 `gpos` 按行号偏移归一到 R10 的 `pos` 口径，否则 `(token,pos)` join 会大面积失配（实测见 1(a)）。

### 2(d) 可粘贴 pipeline 骨架

完整可执行实现落 `lead/gate_pipeline_20261109/_gp_pipeline.py`（本任务写域，本会话实跑通过）。核心片段：

```python
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\gate_pipeline_20261109")
import _gp_pipeline as P
g7, n13, T = P.load_predicates()          # hashlib 先验指纹，失配拒绝

text   = open(path, encoding="utf-8").read()
tokens = ["已入账", "已追加", "已生效"]   # ★ 必须与 N13.DEFAULT_TOKENS 对齐
spans  = P.extract_spans(text, tokens)    # L0：finditer 全量 + eol

# L1..L5：各层返回容器原样转发，绝不互相覆盖
layers = P.run_layers(g7, n13, T, text, tokens, doc_dir)
#   layers["R9"]  = {problems, warnings}        ← r9_check 的二元组
#   layers["R10"] = {problems, warnings, hits}  ← r10_scan 的三元组（hits 带 pos/kind）
#   layers["R12"] = {problems, hits}            ← r12_scan 的二元组
#   layers["N13"] = {problems, details}         ← r13_assertions 的二元组
#   layers["R11"] = {problems, warnings, bindings}  ← r11_scan 的三元组（需 doc_dir）

rows, conflicts, summary = P.resolve_conflicts(text, tokens, layers, T)  # L6
res = P.gate_check(text, tokens, doc_dir, g7, n13, T)                    # L7
#   res["verdict"], res["problems"], res["conflicts"], res["summary"]
```

返回值怎么传下去（逐层显式）：
- L0 `spans` → L6 的 join 主键；`spans["eol"]` → 位置归一开关。
- L2 `hits`（`token/pos/kind`）→ L4 的 `r10_map`，同时 → L6 的 `r10_v`。
- L3 `hits`（`token/pos`）→ L4 的 `r12_pos` 集合，同时 → L6 的 `r12_v`。
- L4 `details`（`kind/exempt/rule/line`）→ L6 的 `n13_v` 与 `n13_veto`。
- L1/L5 `problems` → L7 直接并入（不进裁决）。
- L6 `rows` → L7 生成 `ADJUDICATED`；`conflicts` → L7 只登记，不改变裁决。

---

## 3 第三步：冲突消解规则（本任务核心）

### 3(a) 逐类冲突形态与「谁说了算」

**形态 C1 — 同一 span，R10 CATCH / N13 PASS**（BOUND 5 处，§1(c) 表）
根因：R10 的 `assertion` 判据是「24 字符回看窗无否定词、且不在 `「…」` 短引证跨度内」（`_g7_predicates.py:86-109`），它**看不见** `#` 标题、`| …? |` 表头、`grep/核查` 检索标签；N13 的 A/B 判据是「token 之后同一微段内有 A/B 标记 + 行级无肯定断言」（`_n13_predicates.py:273-286`）。
**裁决**：N13 的 A/B 是**精筛**，有该 span 自身的局部正向证据（标记落在 token 自己的微段里）；R10 的 assertion 是**宽进的默认值**（拿不准就报）。故 **PASS，适用 K9**；但分歧仍登记 `conflicts[]`，并附 `rule_id=R10_ASSERTION_OVERRULED`。不能说「R10 错了」——只是它这一层没有足够信息。

**形态 C2 — 同一 span，R10 PASS（negation）/ N13 CATCH（D）**（`不宣告 X 已生效，但 Y 已入账`、`未验：本笔已入账`）
根因：R10 的 `CLAUSE_BREAK` 不含逗号（`:71`），逗号前后的肯定段被同窗否定词污染；N13 的 `_line_positive` 用「微段内主语 + 完成词」抓到肯定段（`:163-177`）。
**裁决**：**CATCH，K2**。N13 提供的是 R10 看不到的局部证据，不是「更严」；R10 的放行不构成反证。

**形态 C3 — 同一 span，R10 PASS / R12 CATCH / N13 CATCH**（`并非不宣告已生效`）
**裁决**：**CATCH，K1**。双重否定=肯定是语义事实（R12 用相邻构式而非奇偶计数，`_g7_predicates.py:75,135-139`），N13 自身也消费 R12 命中（`:241-245`）。三层一致，非冲突。

**形态 C4 — 同一 span，R10 PASS / R12 ABSENT / N13 C（转发 R10）**（`亦非不宣告 N-4 正式绑定已生效`）
N13 的 C 类只是「R10 说 negation」的**转发**（`:247-263`），不是独立证据。实跑 `r10_context` 得 `neg_count=2, dbl=False, kind=negation`——R12 的 `DOUBLE_NEG_RE` 不含「亦非不」这种分离型。
**裁决**：三层都放过 ⇒ 合成链也放过，**判错**。这不是冲突（无相反意见），是**共同盲区**，见 3(d)。不许用「以最严为准」假装兜住——最严的一层在这里也没报。

**形态 C5 — 点名的 F03：`grep 结果：已生效，可应用母本`**
本会话实跑（`_gp_pipeline.py` demo 与 `_f3` 探针）：

```
R10 kinds: [('已生效','assertion')] problems=1   # 抓住
R12 problems: 0                                  # 未参与（ABSENT，不是放过）
N13: [('D','同句混用：行内另有肯定断言（完成词+可应用/放行：已生效，可应用）')]  # 抓住
chain verdict = FAIL ; rows: 已生效 pos=8 r10=CATCH r12=ABSENT n13=CATCH => CATCH ['K4']
```

**谁说了算**：原版 F03 里 R10 与 N13 **都抓住**，只有「A 标记」语义上想放过——但 A 标记本身不是一层谓词，它是 N13 内部的一条分支，而 N13 的行级肯定守卫（`:163-177,233-239`）已把它作废。故**没有真值冲突，判 CATCH**。
把 F03 变形成 `grep 结果：已生效 0 命中` 才出现三答案：R10=`assertion` CATCH / R12=0 / N13=`A` PASS。此时按 **K9 判 PASS**（并登记冲突）；再变形成 `未核 grep 结果：已生效，可应用母本` 则 R10=`negation` PASS / N13=`D` CATCH ⇒ **K2 判 CATCH**。三条形态给三个不同答案，说明**冲突必须按 span 逐处判，不能按「整行看起来像什么」判**。

**形态 C6 — 不同 span、同一行**：`不宣告 X 已生效，但 grep 结果：已入账 0 命中` 实跑 N13 给出 `A`（已入账）与 `C`（已生效）两种放过。**规则 K4**：同一行只要任一层在该行另判 D/CATCH，整行 CATCH（N13 的 `_line_positive` 已实装，合成层只复述不重算）；但本例 N13 未判 D，故合成链按各行 span 分别放过——**如实记为「本链兜不住」，见 3(d)**。

**形态 C7 — 不同行、同一小节**：`## 2 上游指纹 … 已入账 grep 结果`（标题，B 放过）与下一行 `本笔已入账`（D 抓住）。**规则 K5**：不传播。小节内任何放过/抓住都不外溢到别行；`line` 只用于定位与 K4 的同行聚合。理由：跨行传播正是 `lead/gate_v1v2_20261109/_v12_REPORT.md:239` 列的「跨行支配判不了」面，传播会制造新的假阴性/假阳性。

**形态 C8 — 词表外 span**：SLOT/TRUTH 的 `已填`。**规则 K6**：该 span 只有 R10 有答案 ⇒ 直接采用 R10 结论，**并显式登记 `OUT_OF_N13_VOCAB`**；绝不因为 N13 返回空就当 PASS。本会话实跑：SLOT 5 处 / TRUTH 2 处被 K6 判 CATCH，构成 §4 的 2 条误报——**这是如实报告，不掩饰**。

### 3(b) 可执行消解规则（K1–K9，实装于 `_gp_pipeline.py:resolve_conflicts`）

统一把每层 verdict 归一为 `CATCH / PASS / ABSENT`，**`ABSENT` 不等于 `PASS`**：

| 规则 | 条件（同一 `(token,pos)` span，除注明外） | 结论 | 依据 |
|---|---|---|---|
| **K1** | R12 命中 `double_neg` | `CATCH` | 双重否定=肯定；非严格度偏好 |
| **K2** | N13=`D` 且 R10=`negation/quote_mention` | `CATCH`，标 `MIXED_CLAUSE` | 同句混用 / 微段主语是 R10 看不到的局部证据 |
| **K3** | N13=`A/B/C` 放过 且 R10=`assertion` | 交 K4/K8/K9 细分 | 两者输入契约不同，不能互相否定，先登记分歧 |
| **K4** | 不同 span 同一行，且该行有 N13 的 D | 整行 `CATCH` | N13 `_line_positive` 既有守卫 |
| **K5** | 不同行同一小节；或三层全 PASS 且无 R12 | 不传播；`PASS` | 跨行传播无依据；只记 section 供定位 |
| **K6** | token 不在 `N13.DEFAULT_TOKENS` 内 | 采用 R10 结论，标 `OUT_OF_N13_VOCAB`；无 R10 答案则 `RAISE` | 词表契约不对齐，ABSENT 不得当 PASS |
| **K7** | 任何层 `ABSENT` 且无其他层答案 | `RAISE / NEEDS_HUMAN`，不放过 | 零覆盖不等于通过 |
| **K8** | K3 且无行级 D、无 A/B 局部证据 | `FAIL_CLOSED` + `CONFLICT_UNRESOLVED`，**不假装已判对** | 真值冲突不可裁决 |
| **K9** | K3 且 N13=`A/B`、该 span 有微段内标记、该行无 D | `PASS`（精筛覆盖宽进） | 局部正向证据 > 宽进默认值 |

附加不变量：
- **同一 span**：三值归一后只出**一个** `final`，但 `conflicts[]` 同时保留双方原意见与 `rules[]`；裁决不删除任何一方。
- **不同 span 同一行**：以 `line` 为键做 K4 聚合；聚合结果只提升为 CATCH，**从不把 CATCH 降级为 PASS**。
- **不同行同一小节**：只记 `section`，不传播；`conflicts[]` 按行分组输出。
- **CRLF**：join 前先按 `spans["eol"]` 归一 N13 `gpos`，否则 A/B/C/D 全部落到 `ABSENT`。

### 3(c) 「顺序决定谁先报」与「谁对」是两件事

- 顺序只决定**数据依赖与报告次序**：R12/N13 必须等 R10 的 hits；R9/R11 可并行；`conflicts[]` 的打印顺序按 `pos` 升序。
- 谁对由 **K1–K9 的 span 级证据**决定，与先后无关。本会话实跑反证：若把「先后顺序」当消解手段，取「最后跑的层说了算」，则 BOUND 的 5 处 A/B 会被 N13 放过（对），但 `亦非不宣告…` 也会被 N13 放过（错），且 `grep 结果：已生效 0 命中` 会因 R10 先报而永远 CATCH（对错取决于人工真值，不由顺序决定）。
- 更直接的实跑反证：把三层 `problems` 做朴素并集（等价于「任一层先报即算」），合成链从 N13 单层 **71/74** 掉到 **48/72**（FP 从 0 涨到 20）——证据留盘 `_gp_regression_v1_union_out.txt` / `.json`。**顺序与并集都不能消解真值冲突，只会把宽进层的噪音直接灌进结论**。
- 因此合成层的 `verdict` 由 §3(b) 的裁决结果生成；`conflicts[]` 无论裁决与否都完整登记；未消解的标 `NEEDS_HUMAN`，**不放过、也不冒充已判对**。

### 3(d) 「三层全说放过但实际有真断言」构造样本 —— 兜不住，如实说

三条构造样本（实装于 `_gp_regression.py` 的 `GP_ALLPASS_TRUE_ASSERTION` 族，本会话实跑 `_gp_regression_out.txt`：`chain_ok=0/3, FN=3`）：

| id | 文本 | R10 | R12 | N13 | 合成链 | 人工真值 |
|---|---|---|---|---|---|---|
| GP-A1 | `亦非不宣告 N-4 正式绑定已生效` | `negation` PASS（`neg_count=2, dbl=False`） | 0 命中 | `C` 放过（转发 R10） | **PASS，漏报** | 双重否定=宣告了，真断言 |
| GP-A2 | `本件登记闭合，母本即日起适用` | 0 命中 | 0 | `details=[]`（无 span） | **PASS，漏报** | 同义完成断言 |
| GP-A3 | `三值填毕，见证已由编排方签字` | 0 命中 | 0 | `details=[]`（无 span） | **PASS，漏报** | C07 域同义完成断言 |

**兜不住，明确说兜不住。** 三类根因都在本链能力之外：
1. **A1 是共同盲区，不是冲突**：三层给的是同一个（错的）答案，K1–K9 里没有任何一条规则能凭空造出相反意见。R12 的 `DOUBLE_NEG_RE` 是**枚举构式**（`_g7_predicates.py:76`），「亦非不」这种 GV-L 分离型不在表内；N13 的 C 类又只是转发 R10。要修必须扩谓词词表——本任务铁律**不改既有谓词模块**，故只能在 `conflicts[]` 之外另立人工复核项。
2. **A2/A3 是词表外同义改写**：L0 提取器按字面 token 扫，全量 `finditer` 也扫不到没有字面命中的句子。`spans=0` 时 K7 的 `RAISE` 循环体根本不执行（没有 span 可判）。这是**语义要素升级层（R9-sem，`lead/gate_r9sem_20261109/` 不存在）**的职责，不是合成层能补的。
3. **K9 的代价**：为了让 N13 的 A/B 精筛压过 R10 的宽进（消掉 20 条 FP），合成层必须接受「N13 说放过就放过」的风险。A1 正是这个代价的兑现。**这是可复核的取舍，不是漏洞被掩盖**。

可执行的缓解（不改谓词模块，落在编排层）：
- 对 `span` 集合做一次「无 span 但含完成语义词族」的旁路扫描，命中即 `NEEDS_HUMAN`（本任务**未实装**，如实标「未实装/未验」）。
- 对 `neg_count ≥ 2 且 dbl=False` 的 span 一律标 `NEEDS_HUMAN`（A1 会命中此条；同样**未实装**）。
- 在上述两条落地前，人工复核是唯一兜底；**不得输出「合成链已全覆盖」**。

---

## 4 第四步：分层回归对比

### 4(a) 合成语料构成（74 条，实装 `_gp_regression.py`，输出 `_gp_regression_out.json`）

| 族 | 条数 | 来源 |
|---|---|---|
| `N13_NEG` | 26 | `lead/gate_n13_20261109/_n13_regression.py:85-113` **逐字导入** |
| `N13_POS` | 16 | 同文件 `:46-80` **逐字导入** |
| `R10_TV` | 2 | `_g7_tv2_overreach_positive.md` / `_g7_tv3_double_negation.md` 逐字读盘 |
| `R10_REAL` | 4 | `_g7_reverse_validate.py:20-25` 四真实件逐字读盘（g7 S1 口径） |
| `R10_CTX` | 11 | `_g7_patch.md:106-108` + N13 P08–P10 的断言词语境形态（**构造，如实标注**） |
| `REAL3` | 3 | c07_slot / c07_truth_protocol / ledger_bound 三真件逐字读盘，按各自任务书词表 |
| `GP_CONFLICT` | 9 | 本任务构造的冲突形态（F03 / 同句混用 / 双重否定 / A 标记劫持） |
| `GP_ALLPASS_TRUE_ASSERTION` | 3 | 3(d) 的三条样本 |

**未纳入、如实说明**：`_g9_regression.py:26-57` 的 30 件历史语料未作为单句语料塞入（其门禁项含 R9/R11，与越权断言面不同口径）；`_g7_tv1/tv4/tv5/tv6/tv7/tv7b` 是 R9/R11 的违规样本，不含越权断言面，只收 TV2/TV3。本会话另在 `_gp_regression.py` 的 `R10_REAL` 族对四真实件做了 R10/N13 复跑。

### 4(b) 每条最终判定

全 74 条逐条 `naive / r10 / r12 / n13 / chain` 五列 + 层间冲突数，落 `_gp_regression_out.json` 的 `rows[]` 与 `_gp_regression_out.txt` 的「全表（每条最终判定）」段。此处不重抄 74 行，只列关键分歧行（逐字摘自输出）：

```
  N13-N07  expect=CATCH naive=CATCH r10=PASS  r12=PASS n13=CATCH chain=CATCH conflict=2  | 不宣告 X 已生效，但 Y 已入账
  N13-P01  expect=PASS  naive=CATCH r10=CATCH r12=PASS n13=PASS  chain=PASS  conflict=1  | ### 1(c) 有没有已入账的？
  REAL-SLOT expect=PASS naive=CATCH r10=CATCH r12=PASS n13=PASS  chain=CATCH conflict=0 MISMATCH
  GP-A1    expect=CATCH … chain=PASS  MISMATCH  | 亦非不宣告 N-4 正式绑定已生效
```

### 4(c) 统计：误报 / 漏报 / 层间冲突

`_gp_regression_out.txt` 逐字：

```
== 单层 vs 合成（全语料 74 条）==
  naive  正确=34  误报(FP)=33  漏报(FN)=7
  r10    正确=35  误报(FP)=20  漏报(FN)=19
  r12    正确=39  误报(FP)=0   漏报(FN)=35
  n13    正确=71  误报(FP)=0   漏报(FN)=3
  chain  正确=69  误报(FP)=2   漏报(FN)=3
  合成链层间冲突总数 = 31  其中未消解 = 0
```

逐族（`by_family`）：`N13_NEG 26/26`、`N13_POS 16/16`、`R10_TV 2/2`、`R10_REAL 4/4`、`R10_CTX 11/11`、`GP_CONFLICT 9/9` 全对；`REAL3 1/3（FP=2）`；`GP_ALLPASS_TRUE_ASSERTION 0/3（FN=3）`。**层间冲突 31 处全部登记并给出裁决规则，未消解 0**——但要强调：未消解 0 不等于判对 0 错，3(d) 的 3 条是「三层无分歧地一起判错」，不进 `conflicts[]`。

### 4(d) 与单层对比：合成后是变好还是变差 —— **如实说：比最优单层略差**

- 相对 **naive(34/74) / R10(35/74) / R12(39/74)**：合成链 **69/74 明显变好**（FP 33→2，FN 7→3）。
- 相对 **N13 单层 71/74（FP=0, FN=3）**：合成链 **69/74，变差 2 条**。根因实跑定位：SLOT/TRUTH 两件真件用的是 C07 域词表（`已填` 等），N13 完全不认这些 span，K6 只能采用 R10 的 5+2 条 assertion ⇒ 产出 2 条文件级误报（实跑 `_gp_pipeline.gate_check`：SLOT `ADJ CATCH=5`、TRUTH `ADJ CATCH=2`，全部 `rules=['K6'] n13=ABSENT`）。**这是词表契约冲突，不是合成逻辑错**；修法是把 C07 词表纳入 N13 的 A/B 语境训练（等于改既有谓词，本任务禁止），或在编排层对 C07 域显式挂 V1/V2 前置分类（`lead/gate_v1v2_20261109/_v12_REPORT.md:248-264` 已给出该设计，本任务不实施）。
- **「每层都修好了，串起来反而更差」确实出现过，且被本会话抓到并留证**：第一版合成链把三层 `problems` 做朴素并集，输出 `_gp_regression_v1_union_out.txt`：

```
== 单层 vs 合成（全语料 72 条）==   ← 第一版语料 72 条
  n13    正确=68  误报(FP)=0   漏报(FN)=4
  chain  正确=48  误报(FP)=20  漏报(FN)=4
```

  20 条新增误报全部来自「N13 已判 A/B 放过、R10 宽进仍报 assertion」，即 §2(b) 说的宽进噪音灌进结论。第二版改为逐 span 裁决后 FP 降到 2。**这条失败证据保留不删**，它是「顺序/并集不能当消解手段」的实测支撑。
- 仍存在的 3 条漏报（GP-A1/A2/A3）N13 单层也全漏，合成链**没有引入新漏报**。

---

## 5 第五步：落地建议与边界

### 5(a) 谁维护

**编排层单一脚本调用多个只读谓词模块**，不要合进单一模块。理由（均有实跑/代码支撑）：
- 三层谓词分属三个写域且被本任务铁律列为绝对只读：`lead/gate_fp7_20261108/_g7_predicates.py`、`lead/gate_n13_20261109/_n13_predicates.py`、`lead/gate_r9r12_20261109/_g9_gate.py`。合并成一个模块必然要改它们或复制粘贴，两者都会破坏指纹锚（`_g9_gate.py:36-51` 加载前先验 sha256，复制件会立刻失配拒绝运行）。
- 词表随任务书变（C07 域、BAD_BAN 五词、N13 三词三套并存），应由编排层按域装配，而不是烧进谓词本体。
- 现有 `_g9_gate.py:70-203` 已经是「编排层」形态（`check_deliverable` 逐层调用 + 合并视图 + `rule_id`），把它扩展成接 N13 的版本是最小侵入；`_n13_predicates.py:316-336` 也给出了「迁移配方」把 `r13_assertions` 挂到调用方的 5 行改法。
- 本任务交付的 `_gp_pipeline.py` 就是这个编排层骨架（只读 import + hashlib 先验 + 逐 span 裁决），可直接作为落点；**不替换**任何既有模块。

### 5(b) 加新层的回归门槛

1. **指纹不漂移**：新层上线前后，10 件只读件 + 两件台账逐件 `hashlib.sha256` 比对（本会话末次实跑 `ALL_ZERO_DRIFT=True`）；旧谓词模块一字不改。
2. **契约显式登记**：新层必须声明 `输入(text? + 词表? + 写域?)`、`输出(problems/warnings/hits? bool? 三元组?)`、`position 口径`（原文本下标 vs `splitlines` 累加），以及 `词表是否与 N13.DEFAULT_TOKENS 对齐`。CRLF 必须过一遍 1(a) 的对齐对照。
3. **回归门槛（数值，可在 `_gp_regression.py` 上加断言）**：
   - 现有 74 条合成语料上，新链 `FP ≤ 2 且 FN ≤ 3`（即不得劣于本会话基线 69/74）；
   - N13 自带回归 `正 16/16 放过、负 26/26 抓住、真件 0 D、ALL_PASS=True` 必须保持（本会话实跑通过）；
   - g7 反向验证 `verdict total=46 pass=46 fail=0`（`lead/gate_fp7_20261108/_g7_reverse_validate_out.txt:72` 本会话读取该落盘输出，`GATE_FALSE_POSITIVE_5_6_7.md:224` 同值；**脚本本身本会话未重跑**，如实标「未验」）；
   - `conflicts[]` 条数只增不减（新层若让冲突「消失」，必须给出逐 span 的新证据规则，否则视为放宽判据）；
   - 并行等价：新层加入后重跑 2(c) 的 `PARALLEL_VS_SERIAL ALL_EQUAL=True`。
4. **空跑防线**：沿用 `_g9_gate.py:13-18,121-122` 的 `items==0 ⇒ FAIL_EMPTY`；新层 0 项检查不得 PASS。
5. **降级不静默 PASS**：`_n13_predicates.py:325-333` 的迁移配方要求 `except (ImportError, OSError, AttributeError)` 时降级为字面全拦；新层也必须如此。

### 5(c) 这条链判不了什么（如实列）

1. **词表外同义改写**：`登记闭合 / 填毕 / 已由…签字` 等，`finditer` 全量也扫不到（3(d) A2/A3 实证）。R9 语义要素升级件 `lead/gate_r9sem_20261109/` **不存在**，语义在场判不了。
2. **分离型双重否定**：`亦非不宣告…`、`并非不…` 之外的 GV-L 形态（3(d) A1 实证；`DOUBLE_NEG_RE` 是枚举表，`_g7_predicates.py:76`）。
3. **跨行/跨段落支配关系**、**篇章级共指消解**、**反讽/转述他人断言**：`lead/gate_v1v2_20261109/_v12_REPORT.md:239-243` 列了 6 类，本链没有一层实现。
4. **词表契约不对齐的域**：C07 的 `已填/已代填/已补登` 在 N13 的 A/B/C 语境下无分类能力（§4(d) 2 条 FP 的根因），只能靠 K6 转采 R10 或另挂 V1/V2 前置分类。
5. **CRLF 文本的位置对齐**：本链只在 `spans["eol"]` 上做了标记与「须归一」的建议，**归一代码未实装**（1(a) 实测 CRLF 会让 R10/N13 的 `(token,pos)` 键失配）。三件真件均 LF，故本次结论不覆盖 CRLF 件。
6. **R11 现盘回验的覆盖面**：`_gp_probe_out.json` 记录三真件 bindings 分别 5/15/11 条，其中 SLOTS/TRUTH **全部 `path=null` 仅警告**；`lead/gate_r9r12_20261109/_g9_regression.md:147` 独立指出 30 件语料 18 条绑定中 17 条 `path=null`、现盘回验 0 次触发。链不能判「尾括注路径的哈希是否被伪造」。BOUND 另报 1 条 `引用锚指向不在盘对象 sha256Line`（`_gp_probe_out.json`），属 R11 路径采集误把变量名当路径，**本任务未改、如实记录**。
7. **真值真伪本身**：R11 只验指纹/字节数一致性；ID 真值自证、业务事实是否真的发生，静态文本谓词判不了（`lead/c07_slot_20261109/_c7_selfcheck.py:5`）。
8. **跨文件状态同步**、**运行期进程/内存**（本任务铁律零真机零采样，显式不在能力域内）。

### 5(d) 三层都过了但人工看仍有问题，说明什么

**结论：说明「一致」不是「正确」，且问题几乎一定落在 5(c) 的共同盲区，而不是某一层的 bug。** 判断依据：
- 三层都用**同一套字面词表**和**同一套否定/标记词表**（R10 的 `NEG_RE`/`DOUBLE_NEG_RE`、N13 的 `_DIRECT_NEG`/`_A_AFTER`），是**相关失效**而非独立表决；N13 的 C 类甚至直接转发 R10 的 kind（`_n13_predicates.py:247-263`），R12 又复用 `r10_context`（`:144`）。所谓「三层」在证据上不独立，一致通过不能当成三次独立确认。
- 3(d) 的 3 条就是活证：三层一致放过，人工一看全是真断言；`conflicts[]` 为 0 恰恰证明**冲突检测器在这里根本没被触发**。
- 因此处置顺序应为：①先查**词表覆盖**（是不是同义改写 / 未登记 token）；②再查**否定构式枚举**（`neg_count≥2 且 dbl=False`）；③再查**跨行/共指/转述**；④最后才怀疑某一层判错。**不得**因为「三层都过了」就给 PASS 结案，也不得靠加严任一层来「修」——那只会把 FP 重新灌回来（§4(d) 第一版 20 条 FP 的教训）。
- 在 5(c) 的缺口补齐前，人工复核是**必需的最后一道**，不是可选项；合成链的输出应写成 `PASS + coverage_note`，把「本链判不了什么」随结论一起交付。

---

## 6 产出清单（唯一写域，前缀 `_gp_`）

| 件 | 作用 |
|---|---|
| `_gp_probe.py` / `_gp_probe_out.txt` / `_gp_probe_out.json` | 第一步：三层契约、三真件逐件结果、逐 span 冲突面 |
| `_gp_pipeline.py` | 第二步/第三步：可粘贴的编排层骨架 + K1–K9 裁决实装（只读加载既有谓词） |
| `_gp_regression.py` / `_gp_regression_out.txt` / `_gp_regression_out.json` | 第四步：74 条合成语料逐条判定 + 单层对比 |
| `_gp_regression_v1_union_out.txt` / `.json` | 保留的**失败证据**：朴素并集版 48/72（串起来反而更差） |
| `_gp_DESIGN.md` | 本报告 |

**未做**：未改任何既有谓词模块、未改任何交付件、未 commit/push、未启动任何真机/采样代码。
**未验**：`lead/gate_r9sem_20261109/` 不存在（语义要素升级）；`_g7_reverse_validate.py` 全量 46 项本会话未重跑（只读件 `_g7_reverse_validate_out.txt:72` 记载 `total=46 pass=46 fail=0`，本会话只读取该落盘输出）；CRLF 位置归一代码未实装；3(d) 的两条人工复核旁路规则未实装。
