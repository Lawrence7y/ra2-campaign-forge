# R9S 语义要素匹配 — 设计回件（R9 语义要素设计员）

- 日期：2026-11-09。写域：`lead/gate_r9sem_20261109/`（本任务唯一新写域，全部产物前缀 `_r9s_`）。
- 纪律：零真机、零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；未改任何已交付件、未改 `_g7_predicates.py`；不 commit、不 push。
- Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib.sha256`。
- **绝对只读复核结论**：本会话开头与收尾两次实算 9 件派发指纹，全部与编排方派发值逐字节一致（`all 9 unchanged = True`），详见 §0。

被核对象 SHA256 = 593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740，字节数 = 20271

（上行为只读件 `lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md` 的绑定行；其值取自编排方派发，本会话 `hashlib` 实算复验；该件 :142 另有它自己的绑定行 `ba376358…/8211`，两者不冲突。）

---

## 0 实跑命令与指纹台账

### 0.1 编排方 9 件派发指纹的自算复核（本会话实跑）

命令（`python -I -X utf8 -c` 内联，读 9 件字节后 `hashlib.sha256`）：

```
python -I -X utf8 -c "import hashlib,pathlib,json; root=pathlib.Path(r'D:\Project\ra2-campaign-forge'); ..."
```

输出（9/9 与派发值一致）：

| 文件 | sha256 | bytes |
|---|---|---:|
| gate_rejudge32_20261109/GATE_REJUDGE_32.md | ed7e326d38a967308acf0e276c262300abf8d68c98aad2d53b8e9f2a3def6528 | 51156 |
| matrix_ab_ruling_20261109/RULING_MATRIX_AB.md | 0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31 | 36851 |
| matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md | cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6 | 27825 |
| n11_wording_fix_20261108/N11_WORDING_FIX.md | 4ef31846050ef4e1506221c42354b61636701c37657e455c075a2e85f207f1b4 | 18966 |
| s604_script_gap_20261109/S604_SCRIPT_GAP.md | 593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740 | 20271 |
| gate_fp7_20261108/_g7_predicates.py | 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120 | 11743 |
| gate_r9r12_20261109/_g9_gate.py | a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6 | 11623 |
| PENDING_DECISIONS.md | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 52419 |
| GOAL_THREE_TARGETS_20261018.md | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759518 |

收尾复跑命令（同一 `-c` 逻辑）：输出 `all 9 unchanged = True mismatches = []`。

### 0.2 本任务实跑清单

| # | 命令（均为 `python -I -X utf8` + 绝对路径） | 输出件 | exit |
|---|---|---|:--:|
| C1 | `…\_r9s_step1_verify.py > …\_r9s_step1_stdout.txt` | `_r9s_step1_out.json` / `_r9s_step1_stdout.txt` | 0 |
| C2 | `…\_r9s_regress.py > …\_r9s_regress_stdout.txt` | `_r9s_regress_out.json` / `_r9s_regress_stdout.txt` | 0 |
| C3 | `…\_r9s_minpatch.py > …\_r9s_minpatch_stdout.txt` | `_r9s_g9_candidate.py` / `_r9s_minpatch_out.json` / `_r9s_minpatch_stdout.txt` | 0 |
| C4 | `… -c`（9 件指纹初算 / 收尾复算 / 5 处 R9 自跑 / R10 复核 / 角色消融 / 302 项统计） | 本会话 stdout（逐段引于下文） | 0 |

`_g7_predicates.py` 在 `_r9s_predicates.py:38-51` 以 `importlib` **只读加载**，加载前 `hashlib` 验 `02c17e49…51120/11743`，失配抛 `RuntimeError`（沿用 `_g9_gate.py:40-52` 范式）。

---

## 1 第一步：5 处独立复核（a/b/c）

### 1.1 (a) 自跑 `r9_element_present` 与编排方逐位比对

命令 C1（`_r9s_step1_verify.py`）与另一次 C4 内联自跑，两者结论一致；下表为 C1 输出（`_r9s_step1_stdout.txt`）：

| 域 / 行 | token | literal_present | r9_present | r9_layer | r9s_present | r9s_layer |
|---|---|:--:|:--:|:--:|:--:|:--:|
| RULING_MATRIX_AB.md:108 | 需谁批准 | False | False | `""` | True | `semantic` |
| MATRIX_DEFECT_REACHABILITY.md:65 | 实跑输出 | False | False | `""` | True | `semantic` |
| N11_WORDING_FIX.md:76 | 改前改后 | False | False | `""` | True | `semantic` |
| S604_SCRIPT_GAP.md:32 | 脚本存在性 | False | False | `""` | True | `semantic` |
| S604_SCRIPT_GAP.md:87 | 可重建 | False | False | `""` | True | `semantic` |

**与编排方派发的 `literal_present / r9_present / r9_layer / 原句` 逐位一致**（原句亦逐字比对，见 `_r9s_step1_out.json` 的 `lineText`）。5 处都是「raw 与包裹归一化双缺」。

### 1.2 (b)(c) 逐处语义在场判定 —— 结论：**5/5 语义在场，0 处真缺失**

| # | 要素 | 语义在场 | 形式化依据（原句 + 上下文） | 是否「看起来像、语义也不在场」 |
|:--:|---|:--:|---|---|
| 1 | 需谁批准 | **是** | `RULING_MATRIX_AB.md:108`「批准人一律 = **乙设计责任人**，pf2:200」；:138「若批准人不采随批」佐证该角色在治理链上真实生效。`需谁批准` 是 wh-问句，指称其真答案集合；赋值句把 wh-变量约束为可指认施事，且「一律」额外断言唯一性。**回答了「谁」**。 | 否。不是「只提到批准」——有具体施事值。 |
| 2 | 实跑输出 | **是（有条件）** | `MATRIX_DEFECT_REACHABILITY.md:65`「构造输入 → 实跑返回……16/16 格实跑：」只**命名事件**；:67-72 围栏块逐字给出 `verdict='post_read_error' conf='none' is_new=None pre_state='unknown'` 等**带具体值的返回数据行**（:69/:70/:71 三行不同 pre 变体）；:74「16/16，out:159-174」复核输出索引；:26 列出实跑命令与 239 行 `PROBE_DONE`；:80-87 §3.2 复现同一形态。**Run(e) ∧ Output(e,o) ∧ Present(o) 三半齐备。** | 否，但见下方「★ 特别判定」。 |
| 3 | 改前改后 | **是** | `N11_WORDING_FIX.md:76`「## 4 订正草案（改前/改后逐处对照）」；:81【改前】完整原句、:82【改后】完整改句；:88/:89 方案 B 再给一对；:97 收口。同一 `## 4` 小节内 Before(t) ∧ After(t) ∧ Compare(t) 齐备。 | 否。两半都带实值文本，不是只提术语。 |
| 4 | 脚本存在性 | **是** | `S604_SCRIPT_GAP.md:10` 提出「生成脚本是否在盘」；:32 §3「脚本搜索全结果与存在性判定」；:34-67 四路逐路结论（:44「均无 §604 生成器」/:51「无一生成器」/:59「明载脚本未落盘」/:67「脚本从未写入台账」）；:69-71 §3.5「存在性判定」下判「【不存在且从未落盘】」。 | 否。**要素问的是「判定」而非「存在」**，判不存在也是已交付的判定。 |
| 5 | 可重建 | **是** | `S604_SCRIPT_GAP.md:73` §4「重建可行性」；:77-83 五项口径唯一性表；:87「判定：正确算法【可唯一重建】。已有四重独立实现逐位一致……max\|Δ\|=0.000000」。「可」= ◇ 情态头、「重建」= 动作头均保留，「唯一」只强化确定性；同小节有确定性证据。 | 否。不是「只写已分析」。 |

### 1.3 ★ 对 matrix_reach「实跑输出」的特别判定

**判定：等价，但等价性不来自「实跑返回」，也不来自「16/16 格实跑」，而来自 :69-71 的输出载荷本身。**

形式化：`实跑输出` = ∃e Run(e) ∧ ∃o[Output(e,o) ∧ Present(o)]。

- `:65`「构造输入 → 实跑返回」只给 Run(e)；「16/16 格实跑」是计数，`out:159-174` 是**索引/指针**，都不构成 `Present(o)`。若只有这些，本设计判 **FAIL**（负样本 N06/N07/N10 实跑证实）。
- `:67-72` 围栏块内 `verdict='post_read_error' conf='none' is_new=None pre_state='unknown'` 是**输出对象 o 的具值文本**在盘；:26 的 239 行 PROBE_DONE 与 :80-87 的 §3.2 二次复现，证明 o 不是孤例。
- 因此「如果只是有实跑而没有输出，那就不算」这一条**已被当作硬判据实现**：`_r9s_predicates.py` 的 `_datum_ok()` 只认带具体值的 `key=value` 数据行，且排除 `exit / n / lines / PROBE_DONE` 等**元信息键**（这些只描述「跑过」，不是被测函数的输出对象）。

C1 输出结论行：`结论：5 处中语义也不在场的真缺失 = []；语义在场 = 5/5`。即**没有哪一处是真缺失、不该进语义规格注册表**。

---

## 2 第二步：语义要素判定方法

### 2.1 (a) 「语义要素」与「同义词」的区别 —— 为什么不是把词表变长

- **同义词表**：`token → {surface₁, surface₂, …}`，判定是 `∃s ∈ Set : s in text`。这是**析取 (∨) 的字面匹配**。每来一个新措辞就要加一个词，词表随语料线性膨胀；也无法区分「已批准」和「批准人 = 乙」——前者也会被加进词表然后误放行。
- **语义要素规格**：`token → ⟨Roles, Structure, Commitment, ¬Cancel⟩`，判定是**必选角色的合取 (∧)** 加结构约束。一个 spec 是一个**真值条件**，不是一串词面：

| 维度 | 同义词表 | 语义要素规格（本设计） |
|---|---|---|
| 逻辑 | ∨（任一词面命中即过） | ∧（所有必选角色齐备才过） |
| 命中证据 | 无（只知道匹配了哪个词） | 每个角色的 `match / line / value`，可审计 |
| 缺一半 | 可能仍过（只要有别的词） | 必 FAIL（角色消融实测，见 §3.4） |
| 否定/待定 | 无区分（「不可重建」含「可重建」） | 承诺守卫取消（`_commitment_ok`） |
| 跨小节拼词 | 无区分 | `SameSection` / `Gap≤8` / 同子句约束拦下 |
| 新措辞 | 要加词条 | **不加词条**：只要真值条件不变，自动覆盖（P06–P12/P15/P17/P18 实跑） |
| 规模 | 随语料增长 | 固定 = 已登记要素数（本设计 **5** 条，见 §2.4） |

**关键反证**：负样本 N04「谁批准？此项待验」**字面出现了要素的问句形态**；任何同义词表都会放行，本设计判 FAIL。负样本 N19「不可重建」含 `可重建` 子串，`g7.r9_element_present` 会判 raw 命中（`_g7_predicates.py:49-50` 的裸 `in`），本设计的承诺守卫判 FAIL。这证明本层不是「更长词表」，而是**收紧 + 结构判据**。

### 2.2 (b) 可执行的判定机制：三层组合

```
r9s_element_present(text, token) → (present, layer, detail)
  L0 raw        : token in text                       ← 原样 g7.r9_element_present
  L1 normalized : token in g7.r9_normalize(text)     ← 原样，解决反引号/引号包裹拆断
  L2 semantic   : 仅当 L0/L1 双缺 AND token ∈ SPECS 才进入
                  spec.judge(text) = ∀role ∈ Roles : Evidence(role, text)
                                  ∧ SameSection / Gap≤8 / 同子句
                                  ∧ ¬Pending ∧ ¬NegCancel ∧ Value∉Placeholder
  否则 layer = ""（三层全缺 → FAIL）
```

| 层 | 解决什么问题 | 生效范围 | 为何不放松 |
|---|---|---|---|
| **L0/L1 字面 ∪ 包裹归一化** | 第 5 类反引号/引号包裹符误报（32 域中 c07_gate_audit / n4_yi_final 两处） | 全量 token | 直接复用只读 R9 本体，不改其返回；`raw`/`normalized` 标签原样透传 |
| **L2 结构证据 + 邻近共现** | 5 处「语义在场、字面不匹配」 | **仅 SPECS 的 5 个精确 token** | 未登记 token 直接返回 `""` ⇒ R9S ≡ R9；302 项中 297 项逐位一致（§3.4） |
| **承诺守卫 `_commitment_ok`** | 「字面在场 ≠ 已交付」：否定构式、待定/占位符、跨小节拼词 | 仅 5 个已登记 token | 只会把 True 改 False（**收紧**）；32 域 `n_tightens=0`，即无一现盘域被误收紧 |

`detail` 内含 `spec / logic / evidence[]`（每处角色的命中串、行号、取值），供人工复核；`r9s_check` 把 semantic 命中登记为 **warning 而非静默 PASS**（`_r9s_predicates.py` 的 `r9s_check`）。

### 2.3 (c) 5 处逐处的**形式化依据**（不是「我觉得」）

| # | token | spec id | 真值条件 | 逐处代入 | 5 个真实域的 `r9s` 证据（`_r9s_step1_out.json`） |
|:--:|---|---|---|---|---|
| 1 | 需谁批准 | `S1_WHO_APPROVER` | `∃x[批准人(x) ∧ Bind(x,agent)] ∧ agent∉Placeholder ∧ ¬Pending ∧ ¬NegCancel` | 「需谁批准」= λx.批准(x) 的 wh-问句，其指称 = 真答案集合（Hamblin/Karttunen 问答语义）。赋值句「批准人**一律 =** 乙设计责任人」把变量约束成集合中的一员且更强（附加唯一性 **∀y 批准人(y) → y=乙**）。问答语义下 **答案句 ⊨ 问句**，故等价。 | `match="批准人一律 = **乙设计责任人"`, `agent="乙设计责任人"`, `line=108` |
| 2 | 实跑输出 | `S2_EXEC_OUTPUT` | `∃e Run(e) ∧ ∃o[Output(e,o) ∧ Present(o)] ∧ SameSection ∧ Gap≤8 ∧ ¬Pending` | 合取名词 N₁N₂ = 「实跑」(事件) ∧ 「输出」(对象)。`实跑返回` 只满足 Run(e)（返回是事件的**命名**，不是对象）；`verdict='…' conf='…'` 是 o 的具值文本，满足 Output∧Present。两者同处 `## 3`，围栏块距 EXEC 行 2 行 ≤ 8。`out:159-174` 只是索引，不计载荷。 | `layer=fenced`, `exec_line=65`, `fence_line=67`, `gap_lines=2`, `datum=["pre=None(未采集)","exists=None","verdict='post_read_error'"]` |
| 3 | 改前改后 | `S3_BEFORE_AFTER_PAIR` | `∃t[Before(t) ∧ After(t) ∧ Compare(t)] ∧ SameSection ∧ Value∉Placeholder` | 无分隔并列 = 逻辑合取（交换律）。`/` 是并列分隔符，`【改前】…【改后】` 是同一合取的两个带标签槽位，标签变化不改合取式。对照算子「逐处对照」在 §4 标题中显式给出。 | `section="## 4 订正草案（改前/改后逐处对照）"`, `n_before=2`, `n_after=2`, before/after 各带完整实值 |
| 4 | 脚本存在性 | `S4_SCRIPT_EXISTENCE_DETERMINATION` | `∃d[Determination(d) ∧ Subject(d,script) ∧ Q(d,Exists(script)) ∧ Resolved(d)] ∧ SameSection` | 定摹状词「X 存在性」= 对命题 `Exists(X)` 的一项**判定** d（弗雷格：摹状词指称满足条件的唯一对象）。`Resolved(d)` 要求极性已决断，**极性正负均可**（判「不存在」与判「存在」同为已交付）。`存在性判定` / `是否在盘` / `【不存在且从未落盘】` 分别是 Q 与 Resolved 的表层。 | `section="## 3 脚本搜索全结果与存在性判定（四路逐路）"`, `polarity="不存在且从未落盘"`, `line=71` |
| 5 | 可重建 | `S5_RECONSTRUCTIBILITY` | `◇Reconstruct(algo) ∧ ∃e Evidence(e,determinacy) ∧ ¬NegModal ∧ ¬Pending ∧ SameSection` | 「可」= 情态算子 ◇，「重建」= 动作谓词 Reconstruct，`◇Reconstruct` 是核心式。「可**唯一**重建」在 ◇ 与 Reconstruct 之间插入程度副词，只断言算法确定性（`∃!algo`），**不换情态头、不换动作头、不否定**，故核心式成立且更强。同小节「口径唯一性 / 逐位一致 / max\|Δ\|=0.000000」是 determinacy 证据。 | `modal="【可唯一重建】"`, `evidence="五项口径"`, `line=87`, `clause="**判定：正确算法【可唯一重建】"` |

每一条都可在 `_r9s_predicates.py` 的 `SPECS` 中读到 `basis` 原文（`spec_inventory()` 导出，C2 输出 `_r9s_regress_out.json.spec_inventory`）。

### 2.4 (d) 防止词表无限膨胀：加词准入标准

**注册表规模 = 5，且不是「词表」：`SPECS` 的 key 是 5 个门禁必现要素的精确字面串，value 是真值条件规格。措辞变体不进表。** 实跑 `spec_inventory size=5`（C4），`ids = [S1_WHO_APPROVER, S2_EXEC_OUTPUT, S3_BEFORE_AFTER_PAIR, S4_SCRIPT_EXISTENCE_DETERMINATION, S5_RECONSTRUCTIBILITY]`。

新增一个 spec 必须**同时**满足以下 7 条（缺一不批）：

1. **任务书要素**：key 必须是任务书【交付】里已写明的必现要素字面串；不得为「让某个交付件通过」临时造 key。
2. **真值条件可写**：能写成一阶式（∀/∃/◇/¬/合取），并给出该式与 token 语义的等价论证（如 §2.3 的问答语义 / 摹状词 / 情态逻辑）。**「看起来像」不构成依据**。
3. **角色 ≥2 且可独立观测**：每个角色是文本中可定位的结构证据（角色头 / 算子 / 具值 / 载荷 / 极性），不得只有一个词面。
4. **最小消融必 FAIL**：删掉任一角色构造的样本必须判缺失（角色消融，§3.4 实跑 7/7 FAIL）。
5. **负样本 ≥ 正样本数**：每条 spec 至少配「只给一半 / 否定 / 待定 / 占位符 / 跨小节」五类负样本，全部仍 FAIL。
6. **闭合边界**：不得使用模糊匹配、通配、编辑距离或 embedding；`SPECS.get(token)` 是精确字典查表，未登记 token 一律 R9S ≡ R9。
7. **全量不放松回归**：新 spec 必须重跑 §3.4 的 32 域白名单检查，`flips_outside_whitelist` 必须为空，且 `n_flips` 恰等于白名单数。

**为什么这能止住膨胀**：新措辞（「批准方」「原文/改为」「能重建」「可唯一复现」）不产生新条目，因为它们满足**同一个真值条件**——P06/P07/P08/P10/P12/P15/P17/P18 共 8 条构造变体实跑全部 `semantic` 命中，而 `SPECS` 仍是 5 条。反过来，若有人想为「已批准」「已分析」「已实跑」加词，第 4/5 条会直接拒绝（它们是负样本 N01/N18/N06）。**词表增长的上界 = 任务书里「语义型必现要素」的个数，而不是语料里的措辞数。**

---

## 3 第三步：正负样本集与回归

### 3.1 (a) 正样本 20 条（≥15）

`_r9s_samples.py` 的 `POS`：

- **P01–P05** = 5 处真实案例的逐字/最小必要上下文摘录（原句同 `_r9s_step1_out.json.lineText` 与 `context_lines`）。
- **P06–P20** = 构造变体：换角色头 / 换赋值算子 / 被动式 / 内联载荷 / 极简载荷 / 换标签 / 换情态 / 负极性 / 正极性 / 含「未采集」字样的载荷回归 / 含条件句的赋值句。
- C2 实跑：`POS 20/20`，全部 `expect=True / actual=True`；其中 P13/P14/P16 走 `raw`（L0 短路，证明 L2 不介入已字面命中的情形），其余 17 条走 `semantic`。

### 3.2 (b) ★ 负样本 24 条（≥15，最关键部分）

`_r9s_samples.py` 的 `NEG`，每条 `why` 写明「为什么不该被认出」。C2 实跑：`NEG 24/24` 全判 `False`。按类列（完整逐条见 `_r9s_regress_stdout.txt` 与 `_r9s_samples.py`）：

| 类 | 样本 | 为什么不该被认出 |
|---|---|---|
| ★ 要素是「实跑输出」，只写已实跑没有输出 | **N06** | 「构造输入 → 实跑返回……16/16 格实跑」，无带值数据行；有 Run(e) 无 Present(o) |
| 同上，只有指针/占位 | **N07** | 围栏块只有 `输出待补，见 _probe_out.txt:159-174 索引`，指针不是输出 |
| 同上，只有元信息 | **N10** | `PROBE_DONE 239 行 / exit=0` 是计数与运行标记，不是被测函数的返回对象；`_datum_ok` 排除 `_META_KEY_RE` |
| 同上，值全占位符 | **N11** | `verdict='TBD' conf='待定'`，`Present(o)` 要求具值 |
| 同上，跨小节 / 显式否定 | **N08 / N09** | 事件与载荷分处 §1/§2（`SameSection` 失）；「输出未采集」显式否定 |
| ★ 要素是「需谁批准」，只写已批准没说谁 | **N01** | 「本次改动已批准」是事件断言，不回答 wh-变量；R3 施事值缺失 |
| 同上，占位/待定/问句未答/否定 | **N02–N05** | `批准人：待指定` / `尚未确定` / `谁批准？此项待验` / `无需批准` |
| ★ 要素是「可重建」，只写已分析 | **N18** | 「已分析算法，五重独立实现逐位一致」有证据无 ◇Reconstruct 结论 |
| 同上 | **N19 / N20 / N21** | 「不可重建」否定情态（⊃ `可重建` 子串）/「证据待补」/ 情态与证据跨小节 |
| 改前改后缺一半 / 占位 / 跨小节 | **N12 / N13 / N14** | 只有 Before / 两值皆「略」/ 两半分处 §4 与 §5 且无对照 |
| 脚本存在性缺判定 / 未决 / 跨小节 | **N15 / N16 / N17** | 「查过」≠「判定过」/「待验」/ 极性与判定算子跨小节 |
| 跨 spec / 未登记 / 真缺失 | **N22 / N23 / N24** | 另一 spec 的正例文本不串味 / 未登记 token R9S ≡ R9 / 全文完全不含要素 |

补充：C4 另实跑 **7 条角色消融**（`S1 drop R3 agent`、`S2 drop R2 payload`、`S3 drop R2 after`、`S3 drop R3 compare`、`S4 drop R4 polarity`、`S5 drop R3 evidence` 等），输出 `present=False layer=(none)` **7/7** —— 证明每个 spec 的必选角色都不可省。

### 3.3 (c) 4 个真实域上跑：升级后 gateProblems 还剩几条

C2 的 (B) 段（`_r9s_regress_stdout.txt`），逐条列出：

| 域 | R9 缺要素 | R9S 缺要素 | 升级后 gateProblems 剩余 |
|---|---|---|---|
| matrix_ab_ruling_20261109 | 缺要素 需谁批准 | **0** | **3 条**：`含越界断言 已改矩阵` / `含越界断言 已收紧` / `含越界断言 已施行` |
| matrix_reach_20261109 | 缺要素 实跑输出 | **0** | **0 条** |
| n11_wording_fix_20261108 | 缺要素 改前改后 | **0** | **0 条** |
| s604_script_gap_20261109 | 缺要素 脚本存在性、缺要素 可重建 | **0** | **0 条** |
| **合计** | **5 条缺要素** | **0** | **3 条（均非要素类）** |

**这 3 条不是 R9S 造成、也不是真缺失**：C4 对 `RULING_MATRIX_AB.md` 原样跑 `g7.r10_scan(t, ["已改矩阵","已收紧","已施行","已改设计"])`，输出 `problems=[]`，三处 `kind=negation, in_span=true, neg_count=1` —— 即 R10 本来就豁免它们。它们来自 32 域基线里**朴素门禁的越权词裸计数**（`GATE_REJUDGE_32.md:106` #18 把同一行三词判为「误报 ×3」）。R9S 的职责是要素层，不处理 R10；这 3 条按 `GATE_REJUDGE_32.md:146` 早已归入「11 条断言词语境误报」，与本次 5 处字面措辞变体是不同问题。若采用 `GATE_REJUDGE_32.md:159` 的「补 A/B/E 语境类后真正剩下 4 域」口径，则 4 域全部消解、剩 **0 条**。

### 3.4 (d) 证明「不放松」：跑回既有 32 域

C2 的 (C) 段：从各域 `.mjs` 的 `GATE_CODE` 提取必现要素（与 `_rj_final_checks.py:40,74-78` 同法），对**全部 32 域 / 302 个 (域, 要素) 项**逐项比对 `g7.r9_element_present` 与 `r9s_element_present` 的 `(present, layer)`。

实跑结果（`_r9s_regress_out.json` / stdout）：

```
n_elements = 302   identical = 297   changed = 5
n_flips=5  whitelist=5  outside_whitelist=0  n_tightens=0  no_relaxation=True
VERDICT = PASS
```

- 32 域主件全部在盘（`main_missing=[]`）；31 域有要素清单（`o1prime_reach_20261109` 提取到 0 个要素，如实登记，不计入 302）。
- **原本 FAIL 现在 PASS 的域：恰 4 个**（`matrix_ab_ruling` / `matrix_reach` / `n11_wording_fix` / `s604_script_gap`），涉及 5 个 (域, token) 翻案，逐条定性：

| 域 | token | 定性 |
|---|---|---|
| matrix_ab_ruling_20261109 | 需谁批准 | **真误报**（§1.2 #1 语义在场，字面缺） |
| matrix_reach_20261109 | 实跑输出 | **真误报**（§1.3 载荷在场） |
| n11_wording_fix_20261108 | 改前改后 | **真误报**（§1.2 #3） |
| s604_script_gap_20261109 | 脚本存在性 | **真误报**（§1.2 #4） |
| s604_script_gap_20261109 | 可重建 | **真误报**（§1.2 #5） |

- **白名单外翻案 = 0**：其余 297 项（含 32 域里所有原本 PASS 的域、以及 `c07_gate_audit` / `n4_yi_final` 两处靠 `normalized` 层判在场的反引号包裹符误报）逐位不变。
- **`n_tightens = 0`**：承诺守卫（§2.2，只会收紧）在现盘 32 域上没有把任何原本 PASS 的项改成 FAIL。
- **没有任何真问题被放过**：`GATE_REJUDGE_32.md:145` 的 8 条真问题中，3 条严格格式绑定行偏离归 R11 管（本层不碰），5 条措辞变体全部是「要求了、交付件做到了、门禁认不出」的误报；本层没有把「语义也不在场」的项放行 —— 24 条负样本全 FAIL，7 条角色消融全 FAIL。

---

## 4 第四步：与 R9 现有实现的关系

### 4.1 (a) 结论：**新加一层 `r9s_element_present`，不改 `r9_element_present` 的返回语义**

R9 现状 = 包裹归一化（`_g7_predicates.py:31-65`）：`r9_element_present(text, token) → (present, layer)`，`layer ∈ {raw, normalized, ""}`；`r9_check` 在 `:60` 解包两个值，`:63` 对 `layer == "normalized"` 发 warning；`_g9_gate.py:107/:110` 同样解包两个值并按 `layer == "raw"` 计数。

**理由（4 条，全部有实跑/实读依据）**：

1. **指纹绑定面 46 处**：C4 实跑 `grep -rl "02c17e49…51120" --include='*.py' --include='*.mjs' lead .zcode | wc -l` = **46**。改 `_g7_predicates.py` 会令这 46 处 `assert`/指纹比对全部失配，且 `_g9_gate.py:44-48` 明确「失配即拒绝运行」。本任务【铁律】又规定该文件绝对只读。
2. **返回元组长度是 ABI**：`_g9_gate.py:107`、`_n4g_writer_verify.py:124`（`list(g7.r9_element_present(t,k))`）、`_n4gv_predicates.py:42` 都按 2 元组消费；改成 3 元组或给 `layer` 赋新语义会破既有调用方。
3. **既有回归是「双缺即 FAIL」的契约**：`_g7_reverse_validate.py:99`、`_gv_pred_check.py:111` 显式断言「真缺要素 → R9 fail」；`GATE_R9R12_REGRESSION.md:38` 把 R9 定义为「raw 与归一化双缺 = 真缺」。若在 R9 内加入第三层，`r9_layer` 的可能值域扩大，所有按 `layer == "raw"/"normalized"/""` 分支的调用方都要改。
4. **可回滚、可审计**：新层把「哪些要素被语义判据改判」显式登记为 `warning`（`r9s_check`），旧层保持零改动；C3 的最小补丁就是 3 行替换，随时可退回。

**折中**：`r9s_element_present` 返回 3 元组 `(present, layer, detail)`，其中 `layer` 复用 R9 的 `raw`/`normalized` 标签，新增 `semantic` 只在新层里出现；`r9s_check` 保持 `(problems, warnings)` 双列表签名与 R9 一致，故对 `check_deliverable` 是**即插即用**。

### 4.2 (b) 逐处查既有调用方

C4 实跑三条 `grep -rn --include='*.py'`，逐处列（`grep` 输出见本会话 stdout）：

| 调用方类别 | 逐处（文件:行） | 若改 `r9_element_present` 语义会不会破 |
|---|---|---|
| `r9_check(text, tokens)` 直接调用 | `_g7_predicates.py:60`（内部）、`_gv_pred_check.py:41/:111/:114/:116`、`_g7_reverse_validate.py:66/:99/:142/:148`、`_gp_pipeline.py:77`、`_gp_probe.py:80/:94`、`_g9_gate.py:104`、`_rj_final_checks.py:85`、`_msv_g9_own.py:104`、`_ms_g9_candidate.py:104`、`_n4gv_predicates.py:21`、`_n4g_predicates.py:13`、`_n4g_writer_verify.py:123` | **会**：`r9_check` 内部 `:60` 按 2 元组解包；`:63` 按 layer 分支；这些脚本的期望值断言按「双缺即 FAIL」写死 |
| `r9_element_present` 直接调用 | `_g7_reverse_validate.py:151`、`_g9_gate.py:107`、`_rjv_step3.py:106`、`_rjv_step4.py:101`、`_rjv_step5.py:37`、`_rj_delivery_verify.py:119`、`_rj_r9r11_check.py:79`、`_msv_g9_own.py:107`、`_ms_g9_candidate.py:107`、`_n4gv_predicates.py:42`、`_n4g_predicates.py:14`、`_n4g_writer_verify.py:124` | **会**：全部按 2 元组消费（`ok, layer` / `ok, _` / `list(...)` / dict 值）；`_g9_gate.py:110` 另有 `if layer == "raw"` 计数 |
| `check_deliverable(...)` 调用 | C4 实跑计数 **43 处**（含 `merged_safety_*` / `gate_r9r12_*` / `gate_v1v2_*` 等） | **不会破**（若走新层）：`r9s_check` 与 `r9_check` 同签名；C3 实跑 `self_test all_pass=True`，4 域 `verdict=PASS problems=[]`；未登记 token 三组对照 `old=PASS/FAIL new=PASS/FAIL identical=True`（`_r9s_minpatch_stdout.txt` (iii)） |

**结论**：把语义层**并进** `r9_element_present` 会破至少 12 处直接调用 + 16 处 `r9_check` 调用 + 46 处指纹绑定；**新加一层**只需改 `check_deliverable` 的 2 行（外加 1 行展示名，可选）。

### 4.3 (c) 最小改动方案（可粘贴片段）

以下 3 处替换**只作用于调用层**（`_g9_gate.py` 的一份副本 / 后续新版本），`_g7_predicates.py` 一字不动。完整可粘贴源码见 `_r9s_minpatch.py`，自动生成的候选件见 `_r9s_g9_candidate.py`（11710 B）。

```python
# _g9_gate.py:104 原：r9_problems, r9_warnings = g7.r9_check(text, req)
# 替换为（新增 1 行 import + 换 1 行调用）：
    import _r9s_predicates as r9s   # 新增层：R9 保持只读不改
    r9_problems, r9_warnings = r9s.r9s_check(text, req)

# _g9_gate.py:107 原：ok, layer = g7.r9_element_present(text, k)
# 替换为（第三个返回值是审计 detail，弃用）：
        ok, layer, _ = r9s.r9s_element_present(text, k)

# _g9_gate.py:115 原："name": "包裹归一化要素匹配（第 5 类）",   （可选，纯展示）
        "name": "包裹归一化 + 语义要素匹配（R9 + R9S）",
```

前置条件：`_r9s_predicates.py` 与 `_g9_gate.py` 同目录可见（或 `sys.path` 含写域）；`_r9s_predicates.py` 自带 `_load_r9_readonly()` 指纹先验，失配拒绝运行。

**C3 实跑验证**（`_r9s_minpatch_stdout.txt`，exit=0）：
- `self_test`：U1 空跑防线 / U2 包裹符词表 / U3 谓词指纹 **3/3 ok，`all_pass=True`**；
- 4 个真实域经 patched `check_deliverable`（各用自己域的要素清单）：`verdict=PASS problems=[]` **4/4**，每条 `warnings` 明写「由语义要素层命中（raw 与归一化双缺，结构证据齐备）」；
- 未登记 token 三组对照：`["「被核对象」"]`、`["APPROVE_SCOPE"]`、`["被核对象","已生效"]` → old/new 的 verdict、present、raw_hits、缺失 token 集合**逐位相同**（`identical=True` 3/3）。

**一处如实登记的差异**：`r9s_check` 对「三层全缺」的诊断措辞由 `（R9：raw 与包裹归一化文本双缺）` 改为 `（R9：raw 与归一化文本双缺；R9S 语义层亦缺）`。所指要素与 FAIL 结论不变，但若有下游按**问题消息全文**做字符串比对（而非按 `rule_id`/token）会受影响 —— 本会话未发现此类调用方（C4 的 43 处 `check_deliverable` 调用方中未逐一实跑其下游消费逻辑，标 **未验**）。若要求逐字兼容，把 `r9s_check` 里那一行改回原措辞即可（一行）。

---

## 5 第五步：这条路的边界

### 5.1 (a) 语义要素匹配判不了哪些情况（如实列，不宣称完备）

1. **真值条件写不出来的要素**：本层要求每个 token 能写成一阶式（§2.4 第 2 条）。「说明来龙去脉」「充分论证」「恰当处置」这类无明确语义角色的要求无规格可写，判不了，会落回 R9 字面。
2. **世界知识 / 外部事实核验**：`批准人 = 乙设计责任人` 只证明「指认了谁」，不证明乙确有其人、确有权批准；`verdict='post_read_error'` 只证明文本里有输出载荷，不证明它真由某次实跑产生（要证明需引用锚回验，那是 R11 的职责）。
3. **跨文档/跨小节的长程指代**：本层用 `SameSection` / `Gap≤8` 硬约束防误绑，代价是判不了「输出在附件文件里、正文只给指针」的合法形态（N08/N21 即按缺失判）。这是**刻意保守**：宁可漏判也不把无关数据误绑成证据。
4. **否定、反讽、条件、引述的完备语用分类**：本层只有 `NEG_CANCEL` / `PENDING_RE` 两张窄守卫。`GATE_REJUDGE_32.md:137/:292` 已实证 R10 的 A/B/E 语用缺口（标题 / 表头 / 条件分支 / 自检清单格 / 先例引述 / 理由错结论对的假豁免），本层不解决这些，也不宣称解决。
5. **极性语义**：`脚本存在性` 有意接受正负两种极性（判不存在也算已交付）。若任务书其实只想收「脚本存在」的肯定结论，本层会误判 —— 需任务书把要素写清（见 §5.2）。
6. **R9 自身已有的洞**：`_g7_predicates.py:49-50` 的裸 `in` 会让「不可重建」含「可重建」而被 raw 命中。本层的承诺守卫只对 5 个已登记 token 生效；**其余 297 项的同类洞仍在**，本层不管（也不该管，属 R9/R10 既有职责）。
7. **未登记 token**：一律 R9S ≡ R9，不放宽也不收紧。新要素必须走 §2.4 的 7 条准入。
8. **标注「未验」的项**：本会话未逐一实跑 43 处 `check_deliverable` 调用方的下游消费逻辑（§4.3 末）；未对 36 处历史 payload 落地任何改动（【铁律】禁止，`GATE_REJUDGE_32.md:231` 同口径）；未复原 35 处历史门禁**当时**的实跑输出（`GATE_REJUDGE_32.md:290` 已标未验）。

### 5.2 (b) 与「任务书应当把要素写清楚」的上游问题：谁该负责

**判断：任务书方（编排/出题侧）负主要责任，门禁侧负次要的、有限的责任。**

依据（均为实读）：`GATE_REJUDGE_32.md:293` 第 ⑤ 条已明写「**任务书本身含糊（不是门禁的错）**：……⑤『必现要素』当字面 token 还是语义要求未写清（`s604_script_gap` 的 `脚本存在性` vs 交付件 `存在性判定`）」；:105/:107/:109/:114/:115 五处逐条记「属任务书把语义要求写成字面 token」。`GATE_REJUDGE_32.md:292` 另列 4 类任务书自相矛盾（禁词与交付要求冲突、绑定行格式跨任务书不统一）。

分工建议：

| 方 | 该做什么 | 不该做什么 |
|---|---|---|
| **任务书方（主要）** | 【交付】里的每个必现要素写明**是字面 token 还是语义要求**；若语义要求，给出可判定的真值条件（谁/什么输出/什么判定/什么极性）；禁词表与交付要求先做一致性检查；绑定行格式全局统一 | 把语义要求写成裸字面串再让门禁猜；用同一批词既当禁词又当必交付内容 |
| **门禁侧（有限）** | 在任务书已写明的要素上做**可审计、闭合、可回滚**的判据（本层 5 条 spec + 7 条准入 + 全量不放松回归）；把每次语义改判登记为 warning 供人复核 | 用模糊匹配/通配/embedding 去「猜」任务书；为让某件过门禁临时加词；宣称语义判据完备 |

**本层的定位是「补偿措施」而非「替代上游修复」**：`SPECS` 只有 5 条、每条都有形式化依据与负样本，正是为了把补偿面钉死，不让它膨胀成对任务书含糊的无边界兜底。

### 5.3 (c) 若这 5 处都不改判据而是改交付件：代价对比

| 维度 | 改判据（本设计） | 改交付件（补 5 个字面串） |
|---|---|---|
| 改动件数 | 1 个新写域 + 调用层 2 行；`_g7_predicates.py` 零改动 | **4 个只读交付件**：`RULING_MATRIX_AB.md` / `MATRIX_DEFECT_REACHABILITY.md` / `N11_WORDING_FIX.md` / `S604_SCRIPT_GAP.md`（本任务【铁律】明列前 3 件 + `s604_script_gap_20261109/` 为绝对只读，**本会话无权改**） |
| 指纹链 | 9 件派发指纹全部不变（收尾实跑 `all 9 unchanged = True`） | 4 件主件 sha256 全部漂移 ⇒ 32 域基线 `mainSha256`/`mainBytes` 失配；`GATE_REJUDGE_32.md` 的全部 `L108`/`L65`/`L76`/`L32`/`L87` 行号引用、逐字原句摘录、复核回件绑定行、下游引用锚（如 `S604_SCRIPT_GAP.md:21-28` 的 9 件 MATCH 表、`N11_WORDING_FIX.md:113` 的 11 件 grep 命中）**全部要重算重签** |
| 治理风险 | 无（只读复核 + 新写域） | 违反「只裁决、不施行」（`RULING_MATRIX_AB.md:102`）、「未改任何文件声明」（`N11_WORDING_FIX.md:142` 标题）、「零载体写/未改台账」（`S604_SCRIPT_GAP.md` §5）；为过门禁而改**已交付且被复核绑过指纹**的件，等于篡改被核对象 |
| 语义质量 | 不变（交付件原样保留「批准人一律 =」「可唯一重建」等更精确表述） | **下降**：「可唯一重建」补成「可重建」会丢掉唯一性断言；「批准人一律 = 乙设计责任人」补一句「需谁批准」是同义反复；「实跑输出」补字面串而不补输出载荷反而制造「有词无输出」的假象 |
| 复发 | 同类措辞变体自动覆盖（P06–P20 实跑），规格表固定 5 条 | 每次换措辞都要再改一次交付件 + 再重签一轮指纹；词表/语料持续增长 |
| 可审计性 | 每条改判有 `spec / logic / evidence / line` + warning；32 域白名单回归 | 改了就是改了，无法区分「原本就写对」与「为过门禁补的」 |
| 成本 | 本会话 3 个脚本 + 3 段实跑（C1/C2/C3，exit 全 0） | 4 件重签 + 所有下游引用锚 + 复核轮回件 + 台账登记，且**本任务纪律禁止** |

**判断**：改交付件在本任务里既**不被允许**（绝对只读 + 不 commit/push），又会破坏指纹绑定链与语义精度；改判据是唯一可行且代价更低的路。但按 §5.2，最根本的修复仍在任务书侧把要素写清 —— 本层只是把这一轮已发生的 5 处误报消解掉，且不放松对真缺失的判据。

---

## 6 产物清单（全部落 `lead/gate_r9sem_20261109/`，前缀 `_r9s_`）

| 文件 | 作用 |
|---|---|
| `_r9s_predicates.py` | R9S 语义要素层本体（5 条 SPECS + 三层判定 + 承诺守卫 + `r9s_check` / `r9s_element_present` / `spec_inventory`） |
| `_r9s_samples.py` | POS 20 条 / NEG 24 条，每条附 `why` |
| `_r9s_step1_verify.py` / `_r9s_step1_out.json` / `_r9s_step1_stdout.txt` | 第一步 (a)(b)(c) 独立复核 |
| `_r9s_regress.py` / `_r9s_regress_out.json` / `_r9s_regress_stdout.txt` | (A) 正负样本 (B) 4 真实域 (C) 32 域 / 302 项不放松回归 |
| `_r9s_minpatch.py` / `_r9s_g9_candidate.py` / `_r9s_minpatch_out.json` / `_r9s_minpatch_stdout.txt` | 最小改动方案实证（self_test + 4 域 + 未登记 token 对照） |
| `_r9s_DESIGN.md`（本文件） | 设计回件 |

**纪律核验**：未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存；未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析；9 件绝对只读件与两台账未修改/追加/覆盖（收尾 `hashlib` 实算 `all 9 unchanged = True`）；未 commit、未 push；所有 Python 均为 `python -I -X utf8` + 绝对路径。
