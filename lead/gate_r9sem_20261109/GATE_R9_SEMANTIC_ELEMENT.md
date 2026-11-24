# GATE_R9_SEMANTIC_ELEMENT.md — R9 语义要素匹配：设计、证据、边界与复核处置

- 日期：2026-11-09。本件落唯一写域 `lead/gate_r9sem_20261109/`，前缀 `_r9sd_` 为本交付会话新增产物；前序设计/复核产物为 `_r9s_*`（撰写轮）与 `_r9sv_*`（独立复核轮）。
- 纪律：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；九件绝对只读件 + 两台账一律未改、未追加、未覆盖；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib.sha256`。
- 本件为**判据设计件**，不是「已升级、已施行」的宣告：升级对象是 R9 的**判定方式**（从字面匹配扩到语义要素匹配），交付件与 `_g7_predicates.py` 都不改。逐处形式化依据与负样本见 §3 / §4；不得用「已升级」概括。

被核对象 SHA256 = 593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740，字节数 = 20271

（上行为只读件 `lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md` 的绑定行；本会话 `hashlib` 实算复验：`_r9sd_final_stdout.txt:12` 输出 `sha256 = 593c7a3e…740 bytes = 20271`。严格格式自检见 §6。）

---

## 1 目的与边界

**目的**：把 R9 从**字面匹配**升级为**语义要素匹配**，用于消解「交付件按语义要求写对了、门禁只认任务书那个裸 token」这一类误报，同时**不得放松对真正缺失要素的 FAIL**。本任务点名的五处：

| token | 所在交付件 | 门禁原判 |
|---|---|---|
| 需谁批准 | `RULING_MATRIX_AB.md:108` | 缺要素 |
| 实跑输出 | `MATRIX_DEFECT_REACHABILITY.md:65` | 缺要素 |
| 改前改后 | `N11_WORDING_FIX.md:76` | 缺要素 |
| 脚本存在性 | `S604_SCRIPT_GAP.md:32` | 缺要素 |
| 可重建 | `S604_SCRIPT_GAP.md:87` | 缺要素 |

这五条原判的依据在 `GATE_REJUDGE_32.md:105/:107/:109/:114/:115` 逐条实读可查；同件 `:145` 把它们归为「5 条字面措辞变体」真问题（相对**字面判据**成立），`:148` 明写「若再扩同义词/语义要素层（R9-R12 库外新写）→ 真问题 0；但那是新写判据，不在本轮『复用 R9-R12』范围内，标『未验』」。本件即承接该「新写判据」的设计与实证，并如实承接其**复核 verdict = partial**（§6）。

**边界（本件做什么 / 不做什么）**：

1. **不改交付件**：四件主件与 `GATE_REJUDGE_32.md` / `MATRIX_DEFECT_REACHABILITY.md` / `N11_WORDING_FIX.md` / `S604_SCRIPT_GAP.md` 及两台账全部绝对只读。改交付件的代价对比见 §6。
2. **不改 `_g7_predicates.py`**：R9 本体 `r9_normalize` / `r9_element_present` / `r9_check`（`_g7_predicates.py:31-65`）保持零改动；语义层作为**新加一层** `r9s_element_present` / `r9s_check`（`_r9s_predicates.py:405-452`），理由与调用方证据见 §5。
3. **不碰 R10/R11/R12**：`matrix_ab_ruling` 升级后仍剩 3 条「含越界断言」问题，是 `GATE_REJUDGE_32.md:106` #18 已定的 R10 否定语境误报，不是要素类问题（§4 实跑 R10 `problems=[]`）；3 条严格格式绑定行偏离归 R11（`GATE_REJUDGE_32.md:145/:292`），本层不碰。
4. **不宣称语义判据完备**：判不了的情况逐条列 §6。
5. **不放宽**：升级后的 R9 必须**同时**认出五个语义等价、且对真缺失仍 FAIL。两边都要有样本（§4）。不许为了让门禁通过而放宽判据——本设计的承诺守卫只会把 True 改 False（`_r9s_predicates.py:115-125/:415-423`）。
6. **上游责任**：任务书把语义要求写成裸字面 token 是主因（`GATE_REJUDGE_32.md:293` 第 ⑤ 条实读）；本层是**有界补偿**，不是替代上游修复。

**本会话实跑支撑**（命令与输出逐条可复核）：

| 命令（`python -I -X utf8` + 绝对路径） | 输出件 | exit |
|---|---|:--:|
| `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_r9sem_20261109\_r9sd_final_verify.py > …\_r9sd_final_stdout.txt` | `_r9sd_final_stdout.txt` / `_r9sd_final_out.json` | 0（首跑 EXIT=1、次跑超时，均已修，见 §6「未验/失误如实登记」） |
| `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_r9sem_20261109\_r9sd_extra.py > …\_r9sd_extra_stdout.txt` | `_r9sd_extra_stdout.txt` | 0 |
| `python -I -X utf8 -c`（绑定对象实算 / 严格格式 / 调用方计数 / pin 数 / 诊断串比较 / 角色消融口径） | 本会话 stdout，逐段引于下文 | 0 |

---

## 2 上游指纹（九件）+ 5 处字面变体独立复核

### 2.1 九件派发指纹自算

命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_r9sem_20261109\_r9sd_final_verify.py > D:\Project\ra2-campaign-forge\lead\gate_r9sem_20261109\_r9sd_final_stdout.txt`（本会话，exit=0）。输出 `_r9sd_final_stdout.txt:2-11`：

```
  MATCH lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md              ed7e326d38a96730 51156
  MATCH lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md           0e817ebb8087141d 36851
  MATCH lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md     cd03a91aac610cd0 27825
  MATCH lead/n11_wording_fix_20261108/N11_WORDING_FIX.md             4ef31846050ef4e1 18966
  MATCH lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md             593c7a3ed3b1d1d4 20271
  MATCH lead/gate_fp7_20261108/_g7_predicates.py                     02c17e49764a6f87 11743
  MATCH lead/gate_r9r12_20261109/_g9_gate.py                         a83081eeffc56e83 11623
  MATCH lead/PENDING_DECISIONS.md                                    3765eddbe96deeb6 52419
  MATCH lead/GOAL_THREE_TARGETS_20261018.md                          2baa0de45d412554 759518
  all_match = True
```

9/9 与任务【编排方指纹】派发值逐位一致；收尾复跑 `_r9sd_final_stdout.txt:65` 输出 `readonly_9_unchanged = True`。设计主件 `_r9s_DESIGN.md` 的派发记录为 `5cae35256ec123687c6cbc47753ece3d417e0e33217005bdee0b1b47e322c95c / 37988 B`（`_r9sv_verify_stdout.txt:12` 实读），本件不改动它。

### 2.2 5 处独立复核：literal / r9_present / layer / 原句 / 语义是否真在场

**自跑方式**：本会话按实读 `_g7_predicates.py:31-53` 独立重写 `my_norm` / `my_r9`（`_r9sd_final_verify.py:78-96`），再与只读加载的 `g7.r9_element_present` 交叉校验。输出 `_r9sd_final_stdout.txt:15-25`：

| 域 / 行 | token | literal_present | r9（自实现） | r9（g7 本体） | r9_layer | r9s |
|---|---|:--:|:--:|:--:|:--:|:--:|
| `RULING_MATRIX_AB.md:108` | 需谁批准 | False | (False, "") | (False, "") | "" | (True, semantic) |
| `MATRIX_DEFECT_REACHABILITY.md:65` | 实跑输出 | False | (False, "") | (False, "") | "" | (True, semantic) |
| `N11_WORDING_FIX.md:76` | 改前改后 | False | (False, "") | (False, "") | "" | (True, semantic) |
| `S604_SCRIPT_GAP.md:32` | 脚本存在性 | False | (False, "") | (False, "") | "" | (True, semantic) |
| `S604_SCRIPT_GAP.md:87` | 可重建 | False | (False, "") | (False, "") | "" | (True, semantic) |

`all_false = True`（`_r9sd_final_stdout.txt:25`）——与任务【五处实跑】派发的 `literal_present=false, r9_present=false, r9_layer=""` 逐位一致，也与复核回件 `_r9sv_verify_stdout.txt:16-26` 的独立实现一致。原句逐字（`_r9sd_final_stdout.txt:16/:18/:20/:22/:24`，完整版另见 `_r9sv_callers_stdout.txt:65-93`）：

1. `RULING_MATRIX_AB.md:108`：`### 5.2 可执行改动清单（★ 处方，未实施；批准人一律 = **乙设计责任人**，pf2:200；改后立即做登记 7/8，顺序不可倒）`
2. `MATRIX_DEFECT_REACHABILITY.md:65`：`- **构造输入 → 实跑返回**：classify 直调，pre 八变体（…）× read_error 两型（exists=None / exists=True），16/16 格实跑：`
3. `N11_WORDING_FIX.md:76`：`## 4 订正草案（改前/改后逐处对照）`
4. `S604_SCRIPT_GAP.md:32`：`## 3 脚本搜索全结果与存在性判定（四路逐路）`
5. `S604_SCRIPT_GAP.md:87`：`**判定：正确算法【可唯一重建】。** 已有四重独立实现逐位一致（…），复核轮另有第 5 重独立实现与 R3 [B] 逐位一致（max|Δ|=0.000000）【转述：复核回件】。`

**语义是否真在场（逐处，不是「看起来像」）**：

| # | 语义在场 | 关键上下文（行号实读） | 真缺失？ |
|:--:|:--:|---|:--:|
| 1 | 是 | `:108` 赋值句给出可指认施事「乙设计责任人」；`:138`「若批准人不采随批」佐证该角色在治理链真实生效（`_r9sv_callers_stdout.txt:65-66`） | 否 |
| 2 | 是（有条件） | `:65` 只命名事件；`:67-72` 围栏块给出 `verdict='post_read_error' conf='none' is_new=None pre_state='unknown'`（`:69/:70/:71` 三 pre 变体）；`:74`「16/16，out:159-174」只是索引；`:26` 实跑命令 + 239 行 PROBE_DONE；`:80-87` §3.2 二次复现（`_r9sv_callers_stdout.txt:68-76/:80-84`）。复核轮另实读 `_mr_probe1_out.txt:159-174` 16 行带值返回数据（`_r9sv_verify_stdout.txt` §③ 转述） | 否，见下方★ |
| 3 | 是 | `:76` 标题带对照算子「逐处对照」；`:81`【改前】完整原句、`:82`【改后】完整改句；`:88/:89` 方案 B 再给一对；`:97` 收口（`_r9sv_callers_stdout.txt:77-82`） | 否 |
| 4 | 是 | `:10` 提出问题；`:32` §3 标题；`:44/:51/:59/:67` 四路逐路结论；`:69-71` §3.5 判「【不存在且从未落盘】」（`_r9sv_callers_stdout.txt:83-90`） | 否 |
| 5 | 是 | `:73` §4 标题；`:77-83` 五项口径唯一性表；`:87` 肯定 ◇ 结论 + 五重逐位一致证据（`_r9sv_callers_stdout.txt:91-93`） | 否 |

★ **`实跑输出` 特别判定**：等价性**不来自**「实跑返回」「16/16 格实跑」或 `out:159-174`，而来自 `:69-71` 的**输出载荷本身**在盘。形式化 `∃e Run(e) ∧ ∃o[Output(e,o) ∧ Present(o)]`：只有 Run(e) 而没有 Present(o) 时本设计判 FAIL（负样本 N06 / N07 / N10 与复核 V1 实跑证实，§4）。**5/5 语义在场、0 处真缺失**（`_r9s_step1_stdout.txt:41` 的结论行；复核回件 §③ 亦不触发 refuted：「逐处语义在场 PASS」）。

---

## 3 语义要素判定方法

### 3.1 与「同义词表」的本质区别

- **同义词表**：`token → {surface₁, surface₂, …}`，判定 `∃s ∈ Set : s in text`，是**析取 (∨) 的字面匹配**。每来一个新措辞加一个词，词表随语料线性膨胀；且无法区分「已批准」与「批准人 = 乙」——前者也会被加进词表然后误放行。
- **语义要素规格**：`token → ⟨Roles, Structure, Commitment, ¬Cancel⟩`，判定是**必选角色的合取 (∧)** + 结构约束 + 承诺守卫。一个 spec 是**真值条件式**，不是一串词面（`_r9s_DESIGN.md:95-110` 实读）。

| 维度 | 同义词表 | 语义要素规格 |
|---|---|---|
| 逻辑 | ∨（任一词面命中即过） | ∧（所有必选角色齐备才过） |
| 命中证据 | 无 | 每角色 `match / line / value` 可审计（`_r9s_predicates.py:157-158/:214-217/:279-281/:316-319/:357-360`） |
| 缺一半 | 可能仍过 | 必 FAIL（本会话角色消融 7/7 FAIL，`_r9sd_extra_stdout.txt:9-16`） |
| 否定 / 待定 | 无区分 | 承诺守卫取消（`_r9s_predicates.py:115-125`） |
| 新措辞 | 加词条 | 不加词条：真值条件不变即自动覆盖（P06–P08/P10/P12/P15/P17/P18，`_r9s_regress_stdout.txt:6-21`） |
| 规模 | 随语料增长 | 固定 = 已登记要素数 = **5**（本会话 `spec_inventory size=5`，见 `_r9sd_final_stdout.txt` §(5) 同源输出与 `-c` 独立实跑） |

关键反证：负样本 N04「谁批准？此项待验」**字面出现要素的问句形态**，任何同义词表都会放行，本设计判 FAIL；N19「不可重建」含 `可重建` 子串，`g7.r9_element_present` 的裸 `in`（`_g7_predicates.py:49-50`）会判 raw 命中，本设计的承诺守卫判 FAIL（`_r9s_regress_stdout.txt:27/:40`）。这证明本层是**收紧 + 结构判据**，不是更长的词表。

### 3.2 三层判定机制（L0 / L1 / L2）

```
r9s_element_present(text, token) → (present, layer, detail)        # _r9s_predicates.py:405-434
  L0 raw        : token in text                                     ← 原样 g7.r9_element_present
  L1 normalized : token in g7.r9_normalize(text)                     ← 原样，解反引号/引号包裹拆断
  L2 semantic   : 仅当 L0/L1 双缺 AND token ∈ SPECS（精确 dict 查表 :425）才进入
                  spec.judge(text) = ∀role ∈ Roles : Evidence(role, text)
                                  ∧ SameSection / Gap≤8 / 同子句
                                  ∧ ¬Pending ∧ ¬NegCancel ∧ Value∉Placeholder
  承诺守卫 _commitment_ok(:115-125) 只作用：字面命中但被否定/待定吞掉 → True 改 False（收紧）
  否则 layer = ""（三层全缺 → FAIL）
```

| 层 | 解决的问题 | 生效范围 | 为何不放松 |
|---|---|---|---|
| L0/L1 字面 ∪ 包裹归一化 | 第 5 类反引号/引号包裹符误报（32 域中 `c07_gate_audit` / `n4_yi_final` 两处） | 全量 token | 直接复用只读 R9 本体，不改其返回；`raw`/`normalized` 标签原样透传 |
| L2 结构证据 + 邻近共现 | 5 处「语义在场、字面缺」 | **仅 SPECS 的 5 个精确 token** | 未登记 token 直接返回 `""` ⇒ R9S ≡ R9；302 项中 297 项逐位一致（§4） |
| 承诺守卫 | 「字面在场 ≠ 已交付」：否定构式、待定/占位符 | 仅 5 个已登记 token | 只会把 True 改 False；32 域 `n_tightens=0`（§4） |

`detail` 内含 `spec / logic / evidence[]`；`r9s_check` 把 semantic 命中登记为 **warning 而非静默 PASS**（`_r9s_predicates.py:437-452`）。**注意一处已知缺口**（复核发现）：L0 命中后 `_commitment_ok` 只按 `NEG_CANCEL` / `PENDING_RE` 两张窄词表遍历 token 字面出现处，不重跑结构判据，故 V7「脚本存在性…本件不另下结论」由 L0 raw 短路放行（§6）。

### 3.3 五处逐处形式化依据（不是「我觉得」，全部给真值条件式）

| # | token / spec id | 真值条件 | 等价论证（为什么等价，不是看起来像） | 5 个真实域的 r9s 证据 |
|:--:|---|---|---|---|
| 1 | 需谁批准 / `S1_WHO_APPROVER` | `∃x[批准人(x) ∧ Bind(x,agent)] ∧ agent∉Placeholder ∧ ¬Pending ∧ ¬NegCancel` | **Hamblin / Karttunen 问答语义**：wh-问句指称其**真答案集合**；赋值句「批准人**一律 =** 乙设计责任人」把变量约束成集合中的一员，且「一律」附加 `∀y 批准人(y) → y=乙`（更强）。**答案句 ⊨ 问句**，故等价。R1 角色头「批准人」/ R2 赋值算子「一律 =」/ R3 施事值「乙设计责任人」同子句齐备；`:138` 佐证角色生效（`_r9s_predicates.py:128-161` / `SPECS:372-377`） | `match="批准人一律 = **乙设计责任人"`, `agent="乙设计责任人"`, `line=108`（`_r9s_step1_stdout.txt:4-7`） |
| 2 | 实跑输出 / `S2_EXEC_OUTPUT` | `∃e Run(e) ∧ ∃o[Output(e,o) ∧ Present(o)] ∧ SameSection ∧ Gap≤8 ∧ ¬Pending` | **合取名词** N₁N₂ = 事件 ∧ 对象。「实跑返回」只满足 Run(e)（返回是事件的**命名**）；`verdict='…' conf='…'` 是 o 的具值文本，满足 Output ∧ Present；两者同处 `## 3`、围栏块距 EXEC 行 2 行 ≤8。`out:159-174` 只是索引，不计载荷；`exit=0 / PROBE_DONE / n / lines` 是**元信息键**（描述「跑过」而非被测函数返回对象），由 `_datum_ok` 的 `_META_KEY_RE` 排除（`_r9s_predicates.py:164-241`） | `layer=fenced, exec_line=65, fence_line=67, gap_lines=2, datum 含 verdict='post_read_error'`（`_r9s_step1_stdout.txt:11-15`） |
| 3 | 改前改后 / `S3_BEFORE_AFTER_PAIR` | `∃t[Before(t) ∧ After(t) ∧ Compare(t)] ∧ SameSection ∧ Value∉Placeholder` | 无分隔并列 = **逻辑合取**（交换律）；`/` 与【】只是并列分隔符与槽位标记，标签变化不改合取式。对照算子「逐处对照」在 §4 标题显式给出。两半都带实值文本，不是只提术语（`_r9s_predicates.py:244-284` / `SPECS:384-389`） | `section="## 4 订正草案（改前/改后逐处对照）", n_before=2, n_after=2`（`_r9s_step1_stdout.txt:18-23`） |
| 4 | 脚本存在性 / `S4_SCRIPT_EXISTENCE_DETERMINATION` | `∃d[Determination(d) ∧ Subject(d,script) ∧ Q(d,Exists(script)) ∧ Resolved(d)] ∧ SameSection` | **定摹状词**「X 存在性」= 对命题 `Exists(X)` 的一项判定 d（弗雷格：摹状词指称满足条件的唯一对象）。`Resolved(d)` 要求极性**已决断**，正负皆可（判「不存在」与判「存在」同为已交付）。「查过」≠「判定过」（N15）。四路独立证据 + 明确极性闭环（`_r9s_predicates.py:287-323` / `SPECS:390-395`） | `section="## 3 脚本搜索全结果与存在性判定（四路逐路）", polarity="不存在且从未落盘", line=71`（`_r9s_step1_stdout.txt:26-31`） |
| 5 | 可重建 / `S5_RECONSTRUCTIBILITY` | `◇Reconstruct(algo) ∧ ∃e Evidence(e,determinacy) ∧ ¬NegModal ∧ ¬Pending ∧ SameSection` | 「可」= 情态算子 ◇，「重建」= 动作谓词；「可**唯一**重建」只在 ◇ 与 Reconstruct 之间插入程度副词，断言算法确定性（`∃!algo`），**不换情态头、不换动作头、不否定**，故核心式成立且更强。同小节「口径唯一性 / 逐位一致 / max\|Δ\|=0.000000」为 determinacy 证据（`_r9s_predicates.py:326-364` / `SPECS:396-401`） | `modal="【可唯一重建】", evidence="五项口径", line=87`（`_r9s_step1_stdout.txt:34-39`） |

**逐处负样本**（每处至少给「只给一半 / 否定 / 待定 / 占位 / 跨小节」中的若干类，全部判 FAIL，实跑见 §4）：

| # | 负样本 | 为什么语义也不在场 |
|:--:|---|---|
| 1 | N01「本次改动已批准」 | 事件断言 ≠ wh-变量答案；R3 具体施事值缺失 |
| 1 | N02「批准人：待指定」/ N03「尚未确定」/ N04「谁批准？此项待验」/ N05「无需批准」 | 占位 / 待定 / 问句未答 / 否定极性取消批准人角色 |
| 2 | N06「已实跑 16/16」无输出 / N07 只有 `out:159-174` 指针 / N10 `PROBE_DONE 239 行` / N11 值全 `TBD` / N08 跨小节 / N09「输出未采集」 | 有 Run(e) 无 Present(o)；指针、计数、元信息键都不是输出载荷 |
| 3 | N12 只有【改前】/ N13 两值皆「略」/ N14 两半分处 §4 与 §5 | After(t) 缺失 / 值占位 / SameSection ∧ Compare 不成立 |
| 4 | N15「已查生成脚本」/ N16「待验」/ N17 极性跨小节 | 「查过」≠「判定过」；Resolved(d) 未成立 |
| 5 | N18「已分析算法，五重逐位一致」/ N19「不可重建」/ N20「证据待补」/ N21 跨小节 | 有证据无 ◇Reconstruct 结论 / 否定情态 / 待定 / SameSection 失 |
| 全 | N22 跨 spec 不串味 / N23 未登记 token `R9S ≡ R9` / N24 全文无要素 | 精确查表闭合，不因「有任一结构」放行 |

### 3.4 加词准入标准（防止词表无限膨胀）

实跑 `spec_inventory size=5`，`ids=[S1_WHO_APPROVER, S2_EXEC_OUTPUT, S3_BEFORE_AFTER_PAIR, S4_SCRIPT_EXISTENCE_DETERMINATION, S5_RECONSTRUCTIBILITY]`（本会话 `-c` 独立实跑；`_r9sv_verify_stdout.txt:27` 同值）。**SPECS 的 key 是 5 个门禁必现要素的精确字面串，value 是真值条件规格；措辞变体不进表**（`_r9s_DESIGN.md:145-159` 实读）。新增一个 spec 必须**同时**满足 7 条：

1. **任务书要素**：key 必须是任务书【交付】已写明的必现要素字面串，不得为「让某件过门禁」临时造 key。
2. **真值条件可写**：能写成一阶式（∀/∃/◇/¬/合取）并给等价论证（§3.3 的问答语义 / 摹状词 / 情态逻辑）；**「看起来像」不构成依据**。
3. **角色 ≥2 且可独立观测**：每个角色是文本中可定位的结构证据，不得只有一个词面。
4. **最小消融必 FAIL**：删任一角色的样本必须判缺失（本会话 `_r9sd_extra_stdout.txt:9-16` 实跑 7/7 FAIL）。
5. **负样本 ≥ 正样本数**：每条 spec 配「只给一半 / 否定 / 待定 / 占位 / 跨小节」五类负样本全部仍 FAIL。
6. **闭合边界**：禁模糊匹配 / 通配 / 编辑距离 / embedding；`SPECS.get(token)` 精确字典查表（`_r9s_predicates.py:414/:425`），未登记 token 一律 R9S ≡ R9。本会话 `-c` 实读 `imports = ['__future__', 'hashlib', 'importlib.util', 're', 'pathlib']`、`fuzzy_library_calls = []`（复核 `_r9sv_extra_stdout.txt:23-28` 同值）。
7. **全量不放松回归**：新 spec 必须重跑 §4 的 32 域白名单检查，`flips_outside_whitelist` 为空且 `n_flips` 恰等于白名单数（`_r9s_regress.py:204-206`）。

**可执行性如实登记**：第 6、7 条有代码实证（精确查表、32 域回归脚本），但本会话与复核轮均实跑 `has_admission_validator = False`（`_r9sv_extra_stdout.txt:25`；本会话 `-c` 同值）——`_r9s_predicates.py` 中无任何 `admit/validate_spec/check_spec/register_spec` 函数，**第 1–5 条纯文书要求，无「加第 6 条时自动跑」的门禁**。这是设计缺口，不是「已可执行」；优于「谨慎加词」空话，但不宣称全自动。

**为什么能止住膨胀**：新措辞（「批准方」「原文/改为」「能重建」「可唯一复现」）满足**同一个真值条件**，P06/P07/P08/P10/P12/P15/P17/P18 共 8 条构造变体实跑全部 `semantic` 命中而 SPECS 仍 5 条（`_r9s_regress_stdout.txt:6-21`）。若有人想为「已批准 / 已分析 / 已实跑」加词，第 4/5 条直接拒绝（N01/N18/N06）。词表增长上界 = 任务书里语义型必现要素的个数，不是语料措辞数。

---

## 4 正负样本与回归

### 4.1 正样本 20 条（≥15）

`_r9s_samples.py` 的 `POS`：P01–P05 = 5 处真实案例逐字/最小必要上下文摘录；P06–P20 = 构造变体（换角色头 / 赋值算子 / 被动式 / 内联载荷 / 极简载荷 / 换标签 / 换情态 / 负极性 / 正极性 / 含「未采集」字样载荷 / 含条件句赋值句）。本会话自跑 `_r9sd_final_stdout.txt:43`：`POS 20/20  NEG 24/24  all_pass=True`；原撰写轮 `_r9s_regress_stdout.txt:2-21` 逐条列 `expect=True actual=True`，其中 P13/P14/P16 走 `raw`（L0 短路），其余 17 条走 `semantic`。复核轮独立复跑 `_r9sv_extra_stdout.txt:2`：`POS 20/20  NEG 24/24 all_pass=True failed=[]`。

### 4.2 负样本 24 条（≥15）+ 本会话补跑

撰写人 `NEG` 24 条逐条 `why` 见 `_r9s_regress_stdout.txt:22-45`；本会话自跑全数 FAIL（`_r9sd_final_stdout.txt:43`）。按类（★为任务点名形态）：

| 类 | 样本 | 为什么不该被认出 |
|---|---|---|
| ★ 只写已实跑没有输出 | **N06** | 「构造输入 → 实跑返回……16/16 格实跑」无带值数据行；有 Run(e) 无 Present(o) |
| 只有指针 / 占位 / 元信息 | **N07 / N10 / N11** | `输出待补，见 _probe_out.txt:159-174` / `PROBE_DONE 239 行 / exit=0` / `verdict='TBD' conf='待定'` |
| 跨小节 / 显式否定 | **N08 / N09** | 事件与载荷分处 §1/§2 / 「输出未采集」 |
| ★ 只写已批准没说谁 | **N01** | 事件断言不回答 wh-变量；R3 施事值缺失 |
| 占位 / 待定 / 问句未答 / 否定 | **N02–N05** | `批准人：待指定` / `尚未确定` / `谁批准？此项待验` / `无需批准` |
| ★ 只写已分析 | **N18** | 有证据无 ◇Reconstruct 结论 |
| 否定情态 / 证据待补 / 跨小节 | **N19 / N20 / N21** | 「不可重建」⊃「可重建」子串仍 FAIL |
| 改前改后 / 脚本存在性缺角色 | **N12–N17** | 缺一半 / 占位 / 跨小节 / 「查过≠判定过」/ 未决 / 极性跨小节 |
| 跨 spec / 未登记 / 真缺失 | **N22 / N23 / N24** | 不串味 / `R9S ≡ R9` / 全文无要素 |

**本会话补跑的两组独立负样本**：

- **角色消融 7 条**（`_r9sd_extra_stdout.txt:9-16`）：A1 drop agent、A2 drop assign、A3 drop payload、A4 drop after、A5 drop compare、A6 drop polarity、A7 drop evidence → `present=False` **7/7**，`all_fail=True`。证明每个 spec 的必选角色不可省。
- **复核回件 7 条近似负样本逐字复跑**（`_r9sd_final_stdout.txt:28-40`，定义照录 `_r9sv_verify.py:150-225`）：V1（仿 :65-74 全段，有实跑有指针无带值输出）`caught=True`；V2（「批准人一律 = **见台账登记**」指针值）`caught=False`；V3（【改后】=「见方案 B 的对应行，本件不重录」）`caught=False`；V4（极性「以台账记载为准，本件不另下结论」）`caught=True`；V5（「待判…是否…尚需核对」未决问句）`caught=False`；补充 V6（「并非【可唯一重建】」）`caught=False`、V7（token 字面串裸命中而语义未交付）`caught=False`。输出 `V1..V5 caught = 2/5  all_7_caught = False`。

★ **这组是复核 verdict = partial 的决定性依据，必须如实记，不能写成「升级后就抓住了」**：5 条近似负样本只抓住 2 条、漏 3 条，补充 2 条亦漏。按任务书「抓不住即报 partial」。复核 `_r9sv_verify_stdout.txt:29-43` 得同值 `near_miss: 2/5 caught, all_caught=False`。根因实读 `_r9s_predicates.py`：

- `:137-157` `_s1_who_approver` 只查 `PLACEHOLDER_RE`，接受任意 2–24 字串为 agent ⇒ 指针「见台账登记」通过；
- `:256-265` `_labeled_values` 只查长度≥10 与占位/待定 ⇒ 指针「改后句见方案 B…本件不重录」通过；
- `:86-89` `PENDING_RE` 无「待判 / 是否 / 尚需」；`:105-112/:339` `NEG_CANCEL` / `_NEG_MODAL_RE` 只列「不可重建 / 无法重建…」无「并非」；
- `:412-424` L0 raw 命中直接短路（V7）。

即「**真实值角色用黑名单校验**」而非「正面证据校验」，任何不在黑名单内的措辞都把未交付判成在场。修补方向只能**收紧**：为 agent / before / after 值要求「可指认施事 / 实际引文」的**正面证据**（拒绝 见/参见/详见/以…为准/不重录 指针），把 待判/是否/尚需/并非/不另下结论 收入非承诺，并给 7 条准入补可执行校验器。**本件不实施该修补**（属后续轮次），故 §6 标 unconfirmed。

复核另指出：撰写人 24 条负样本中 13 条含现成守卫词/占位词（与守卫词表共设计），不含守卫词的 11 条见 `_r9sv_extra_stdout.txt:3-14`。这不推翻 24/24 FAIL，但说明样本覆盖不足以证明对自然措辞攻击的稳健性。

### 4.3 4 个真实域跑数

本会话 `_r9sd_final_stdout.txt:44-48`（撰写轮 `_r9s_regress_stdout.txt:48-68`、复核轮 `_r9sv_extra_stdout.txt:30-35` 同值）：

| 域 | R9 缺要素 | R9S 缺要素 | 升级后 gateProblems 剩余 |
|---|---|---|---|
| `lead/matrix_ab_ruling_20261109/` | 1（需谁批准） | **0** | **3 条**：`含越界断言 已改矩阵` / `已收紧` / `已施行` |
| `lead/matrix_reach_20261109/` | 1（实跑输出） | **0** | **0 条** |
| `lead/n11_wording_fix_20261108/` | 1（改前改后） | **0** | **0 条** |
| `lead/s604_script_gap_20261109/` | 2（脚本存在性、可重建） | **0** | **0 条** |
| **合计** | **5 条缺要素** | **0** | **3 条（均非要素类）** |

**4 域剩余缺要素 = 0**（`_r9sd_final_stdout.txt:48`）。那 3 条不是 R9S 造成、也不是真缺失：本会话 `_r9sd_extra_stdout.txt:2-6` 对 `RULING_MATRIX_AB.md` 原样跑 `g7.r10_scan`，输出 `problems = []`、三处 `kind=negation, in_span=true, neg_count=1`，`all_negation_or_quote = True`；与 `GATE_REJUDGE_32.md:106` #18「**误报 ×3**」逐字一致，复核 `_r9sv_final_stdout.txt:6-10` 同值。它们来自 32 域基线里朴素门禁的越权词裸计数，归 R10 语境类管。按 `GATE_REJUDGE_32.md:159`「补 A/B/E 语境类后真正剩下 4 域」口径，4 域全部消解、剩 0 条。

### 4.4 32 域不放松证明

方法：从各域 `.mjs` 的 `GATE_CODE` 用严格 `LOOP_RE`（`_r9s_regress.py:75-77`）提取必现要素，对**全部 32 域 / 302 个 (域, 要素) 项**逐项比对 `g7.r9_element_present` 与 `r9s_element_present` 的 `(present, layer)`。本会话独立重算 `_r9sd_final_stdout.txt:49-55`：

```
  n_domains=32 n_items=302 identical=297 changed=5 main_missing=[]
  n_flips=5 outside_whitelist=0 n_tightens=0 no_relaxation=True
     FLIP lead/matrix_ab_ruling_20261109/                需谁批准       whitelisted=True
     FLIP lead/matrix_reach_20261109/                    实跑输出       whitelisted=True
     FLIP lead/n11_wording_fix_20261108/                 改前改后       whitelisted=True
     FLIP lead/s604_script_gap_20261109/                 脚本存在性      whitelisted=True
     FLIP lead/s604_script_gap_20261109/                 可重建          whitelisted=True
```

撰写轮 `_r9s_regress_stdout.txt:104-112` 输出 `VERDICT = PASS`、`samples all_pass=True no_relaxation=True 4域剩余缺要素=0`；复核轮独立重跑 `_r9sv_verify_stdout.txt:86-93`：`n_domains=32 with_main=32 n_items=302 identical=297 changed=5 main_drift=0`、`n_flips=5 outside_whitelist=0 n_tightens=0`、`cross_check … flips_match: true`；`_r9sv_final_stdout.txt:12-13` 32 主件对基线 `drift = []`。

- **原本 FAIL 现在 PASS 的恰 4 域 / 5 项**，逐条定性全为「要求了、交付件做到了、门禁认不出」的真误报（§2.2 与 `GATE_REJUDGE_32.md:105/:107/:109/:114/:115`），无「语义也不在场」的项被放行。
- **白名单外翻案 = 0**：其余 297 项（含 `c07_gate_audit` / `n4_yi_final` 两处靠 `normalized` 层判在场的反引号包裹符误报）逐位不变。
- **`n_tightens = 0`**：承诺守卫在现盘 32 域上没把任何原本 PASS 的项改成 FAIL。
- **两边都灵**：正 20/20、负 24/24、角色消融 7/7、4 域剩 0 条缺要素；但**复核的 5 条近似负样本只抓住 2 条**（§4.2），故「对真缺失仍 FAIL」这一边在**自然措辞攻击下未被完全证明**，不得写成无条件成立。`GATE_REJUDGE_32.md:145` 的另 3 条真问题（严格格式绑定行偏离）归 R11，本层不碰。

---

## 5 与 R9 现有实现的关系

### 5.1 结论：新加一层，不并进 `r9_element_present`

R9 现状 = 包裹归一化（`_g7_predicates.py:31-65`）：`r9_element_present(text, token) → (present, layer)`，`layer ∈ {raw, normalized, ""}`；`r9_check` 在 `:60` 解包两个值，`:63` 对 `layer == "normalized"` 发 warning；`_g9_gate.py:107/:110` 同样解包两个值并按 `layer == "raw"` 计数（本会话实读）。

**并进既有函数会破的理由（实读 / 实跑）**：

1. **返回元组长度是 ABI**：`_g9_gate.py:107`、`_n4g_writer_verify.py:124`（`list(g7.r9_element_present(t,k))`）、`_n4gv_predicates.py:42` 都按 2 元组消费；改 3 元组或给 `layer` 赋新语义会破既有调用方（`_r9s_DESIGN.md:246` 实读）。
2. **指纹绑定面**：`_g9_gate.py:40-52` 明确「`_g7_predicates.py` 失配即拒绝运行」；本任务【铁律】又规定该文件绝对只读。撰写人称 `grep -rl … | wc -l = 46`（`_r9s_DESIGN.md:245`），复核 `_r9sv_final_stdout.txt:2` 实跑同口径 = **55**，本会话实跑**精确 grep 命令** `grep -rl "02c17e49…51120" --include='*.py' --include='*.mjs' lead .zcode 2>/dev/null | wc -l` = **62**（其中写域自身 5 件；排除写域 57；`.zcode` 0）。三值互不相同，方向不变（绑定面很大），**46 与 55 在本会话均不可复现，现值 62 记此，不补造**。
3. **既有回归是「双缺即 FAIL」契约**：`GATE_REJUDGE_32.md:231` 逐字 `if not g7.r9_element_present(t, k)[0]: P.append('缺要素 ' + k + '（R9 双缺）')`；`_r9s_DESIGN.md:247` 另引 `_g7_reverse_validate.py:99` / `_gv_pred_check.py:111`。若在 R9 内加第三层，`r9_layer` 值域扩大，所有按 `layer == "raw"/"normalized"/""` 分支的调用方都要改。
4. **可回滚、可审计**：新层把「哪些要素被语义判据改判」登记为 warning，旧层零改动。

**新层契约**：`r9s_element_present` 返回 3 元组 `(present, layer, detail)`，`layer` 复用 R9 的 `raw`/`normalized`、新增 `semantic` 只在新层出现；`r9s_check` 保持 `(problems, warnings)` 双列表签名与 R9 一致，故对 `check_deliverable` 即插即用。未登记 token 一律 `R9S ≡ R9`（本会话复核 `_r9sv_extra_stdout.txt:17-20` 四组 token 逐位相同）。

### 5.2 调用方排查

本会话按复核口径（`_r9sv_verify.py:426-451`，排除本写域、正则 `函数名\s*\(`）独立计数，输出 `_r9sd_final_stdout.txt:59`：`(reviewer口径, 排除写域) r9_element_present=14 r9_check=21 check_deliverable=43`，与复核 `_r9sv_verify_stdout.txt:102` `counts = {'r9_element_present': 14, 'r9_check': 21, 'check_deliverable': 43}` 逐位一致；复核回件另给「`r9_element_present` 外部调用 12 处、`r9_check` 21 处、`check_deliverable` 43 处」（【复核】⑦，含 `_gpv_probe.py:96` / `_gpv_order.py:36` 两处补正）。

| 调用方类别 | 逐处（文件:行，实读 `_r9sv_verify_stdout.txt:103-117` / `_r9s_DESIGN.md:256-260`） | 并进 R9 会不会破 |
|---|---|---|
| `r9_element_present` 直接调用 | `_g9_gate.py:107`、`_rjv_step3.py:106`、`_rjv_step4.py:101`、`_rjv_step5.py:37`、`_rj_delivery_verify.py:119`、`_rj_r9r11_check.py:79`、`_msv_g9_own.py:107`、`_ms_g9_candidate.py:107`、`_n4gv_predicates.py:42`、`_n4g_predicates.py:14`、`_n4g_writer_verify.py:124`、`lead/gate_fp7_20261108/_g7_reverse_validate.py:151`、`_g7_predicates.py:60`（内部） | **会**：全按 2 元组消费 |
| `r9_check(text, tokens)` | `_g7_predicates.py:60`、`_gv_pred_check.py:41/:111/:114/:116`、`_gp_pipeline.py:77`、`_gp_probe.py:80/:94`、`_g9_gate.py:104`、`_rj_final_checks.py:85`、`_msv_g9_own.py:104`、`_ms_g9_candidate.py:104`、`_n4gv_predicates.py:21`、`_n4g_predicates.py:13`、`_n4g_writer_verify.py:123` 等 21 处 | **会**：`:60` 按 2 元组解包、`:63` 按 layer 分支 |
| `check_deliverable(...)` | 43 处（17 个文件，逐处见 `_r9sv_callers_stdout.txt:22-44`） | **不会破（走新层）**：`r9s_check` 同签名；未登记 token 三组对照 `identical=True`（`_r9s_minpatch_stdout.txt:37-39`） |

**诊断串差异的静态补查（本会话实跑）**：`r9s_check` 对「三层全缺」的措辞由 `（R9：raw 与包裹归一化文本双缺）` 改为 `（R9：raw 与归一化文本双缺；R9S 语义层亦缺）`（`_r9s_predicates.py:447` vs `_g7_predicates.py:62`）。本会话 `-c` 实跑输出：`startswith preserved = True token unchanged = True`、`exact full string identical = False`。写域外全树扫描 `startswith("缺要素")` 消费者恰 **3 处**：`_g9v_corpus.py:97`、`_rjv_step4.py:99`（`startswith("缺要素 ")`）、`_rjv_step5.py:35`（同），与复核【复核】⑦ 一致；另有 4 处 `"缺要素" in m` 子串判断（非全文相等）。**这 3 处不破；43 处 `check_deliverable` 下游逐一执行仍标未验**（§6）。

### 5.3 最小改动可粘贴片段

只作用于**调用层**（`_g9_gate.py` 的一份副本 / 后续新版本），`_g7_predicates.py` 一字不动。完整源码 `_r9s_minpatch.py:26-48`，自动生成候选件 `_r9s_g9_candidate.py`（11710 B，`_r9s_minpatch_stdout.txt:1`）。

```python
# _g9_gate.py:104 原：r9_problems, r9_warnings = g7.r9_check(text, req)
# 替换为（调用层新增 1 行 sys.path + 2 行；R9 保持只读不改）：
    import sys
    sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\gate_r9sem_20261109")
    import _r9s_predicates as r9s   # 新增层：R9 保持只读不改
    r9_problems, r9_warnings = r9s.r9s_check(text, req)

# _g9_gate.py:107 原：ok, layer = g7.r9_element_present(text, k)
# 替换为（第三个返回值是审计 detail，弃用）：
        ok, layer, _ = r9s.r9s_element_present(text, k)

# _g9_gate.py:115 原："name": "包裹归一化要素匹配（第 5 类）",   （可选，纯展示）
        "name": "包裹归一化 + 语义要素匹配（R9 + R9S）",
```

**★ 与撰写轮 `_r9s_DESIGN.md:268-280` 的一处必要补正**：原片段只有 `import _r9s_predicates as r9s`，**未加 `sys.path`**。本会话实跑 `python -I -X utf8 -c`（cwd = 写域）输出 `sys.path[0] = 'C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python312.zip'`、`cwd in path? False`、`import failed ModuleNotFoundError: No module named '_r9s_predicates'` —— 在 `-I` 隔离模式下 cwd 不在 `sys.path`，裸 import 会失败。`_r9s_minpatch.py:20` 自身是靠 `sys.path.insert(0, str(WDIR))` 才成功的（实读）。故上片段补了 `import sys` + `sys.path.insert(0, …)` 两行；若调用层已保证写域在 `sys.path`，可省去这两行。**这是可粘贴性的修正，不是判据放宽。**

**实证**：`_r9s_minpatch_stdout.txt:3-39` → `self_test 3/3 all_pass=True`（U1 空跑防线 / U2 包裹符词表 / U3 谓词指纹）、4 域 `verdict=PASS problems=[]` 各带 semantic warning、未登记 token 三组 `old/new identical=True`。复核 `_r9sv_callers_stdout.txt:1-19` 的 `difflib` diff 为**恰 3 处替换**（`:104/:107/:115`）；本会话 `-c` 复算 `unified_diff lines=25 hunks=2`（`_r9sd_final_stdout.txt:61`），无写原件。补丁后完整模块 `_r9s_g9_candidate.py` 与只读 `_g9_gate.py` 的指纹在 `lead/gate_r9r12_20261109/_g9_gate.py:44-48` 范式下仍由原 `_g7_predicates.py` 指纹守卫（`_r9s_predicates.py:29-39` 先验后加载）。

---

## 6 复核回件、适用边界、代价对比与未验项

### 6.1 复核回件（绑定行格式）

被核对象 SHA256 = 593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740，字节数 = 20271

（严格格式自检：本会话 `_r9sd_final_stdout.txt:62` 输出 `design strict binding matches = 1 ['被核对象 SHA256 = 593c7a3e…740，字节数 = 20271']`；复核 `_r9sv_final_stdout.txt:60-61` `strict matches = 1` 同值。中间不插路径、括号、星号、反引号或空格；「，字节数 = 」后紧跟数字。）

**复核 verdict 如实记：`partial`（任务书规则：refuted 或 partial 标 unconfirmed）→ 本设计标 `unconfirmed`。**

- **不报 refuted**：复核【复核】③ 逐处语义在场 PASS（5/5 语义在场、0 真缺失），并另实读 `_mr_probe1_out.txt:159-174` 确认 `matrix_reach` 确有 16 行带值输出，未出现「只有实跑没有输出」。本会话 §2.2 独立复核同值。
- **必须报 partial**：复核【复核】④ 自造 5 条近似负样本只抓住 2 条、漏 3 条，按任务书「抓不住即报 partial」。本会话 `_r9sd_final_stdout.txt:40` 逐字复跑得 `V1..V5 caught = 2/5  all_7_caught = False`（§4.2），根因实读 `_r9s_predicates.py:137-157/:256-265/:86-89/:105-112/:339/:412-424`。
- **复核其余项**：① 九件指纹 PASS；② 自跑 r9 PASS；⑤ 32 域不放松 PASS（复核如实记自身首版宽松正则得 492 的失误，改用严格 LOOP_RE 后 302 对上）；⑥ 准入 7 条「半可执行」（`has_admission_validator=False`）；⑦ 调用方 PASS + 两处补正；⑧ 越界 PASS（`readonly_9_unchanged=True`、`stray=[]`、未 commit/push）。
- **一处数字不复现**：复核【复核】⑦ 与 `_r9sv_final_stdout.txt:2` 称 `grep -rl … | wc -l = 55/56`（撰写人称 46），本会话精确命令实跑 = 62（排除写域 57），方向不变；**46 / 55 现值均不可复现，记此不补造**。
- **本件未改被核设计件**：写域内仅新增 `_r9sd_*`；复核轮仅新增 `_r9sv_*`。git HEAD 本会话实跑 = `26574589aa8401e8f3f2934680a1ea7109bafa2d`（`_r9sv_final_stdout.txt:57` 同值），`git status -- lead/gate_r9sem_20261109` = `?? lead/gate_r9sem_20261109/`。

### 6.2 适用边界：判不了 / 不宣称完备（如实列）

1. **真值条件写不出来的要素**：「说明来龙去脉」「充分论证」「恰当处置」这类无明确语义角色的要求无规格可写，判不了，落回 R9 字面。
2. **世界知识 / 外部事实核验**：`批准人 = 乙设计责任人` 只证明「指认了谁」，不证明乙确有其人、确有权批准；`verdict='post_read_error'` 只证明文本里有输出载荷，不证明它真由某次实跑产生（需引用锚回验，属 R11）。
3. **跨文档 / 跨小节长程指代**：本层用 `SameSection` / `Gap≤8` 硬约束防误绑，代价是判不了「输出在附件文件里、正文只给指针」的合法形态（N08/N21 按缺失判）。刻意保守：宁可漏判也不把无关数据误绑成证据。
4. **否定、反讽、条件、引述的完备语用分类**：只有 `NEG_CANCEL` / `PENDING_RE` 两张窄守卫；`GATE_REJUDGE_32.md:137/:292` 已实证 R10 的 A/B/E 语用缺口，本层不解决、也不宣称解决。复核 V2/V3/V5/V6/V7 正是这一缺口的实证。
5. **极性语义**：`脚本存在性` 有意接受正负两种极性；若任务书其实只想收「脚本存在」的肯定结论，本层会误判 —— 需任务书把要素写清。
6. **R9 自身已有的洞**：`_g7_predicates.py:49-50` 的裸 `in` 会让「不可重建」含「可重建」而被 raw 命中；本层承诺守卫只对 5 个已登记 token 生效，其余 297 项同类洞仍在，属 R9/R10 既有职责。
7. **未登记 token**：一律 `R9S ≡ R9`，不放宽也不收紧；新要素必须走 §3.4 的 7 条准入（且目前无自动校验器）。
8. **复核暴露的具体破法**（收紧方向，未修补）：保持正例完整表层结构，只把关键语义值换成 ① 指针/引用（见台账登记 / 见方案 B 的对应行，本件不重录）、② 未决问句（待判…是否…尚需核对）、③ 黑名单外自然否定（并非【可唯一重建】），或 ④ 让 token 字面串裸命中而语义未交付（脚本存在性…本件不另下结论）——现三张窄词表与 L0 短路均放行。

### 6.3 「改判据 vs 改交付件」代价对比

| 维度 | 改判据（本设计） | 改交付件（补 5 个字面串） |
|---|---|---|
| 改动件数 | 1 个新写域 + 调用层 3 处替换（+2 行 `sys.path`）；`_g7_predicates.py` 零改动 | **4 个只读交付件**：`RULING_MATRIX_AB.md` / `MATRIX_DEFECT_REACHABILITY.md` / `N11_WORDING_FIX.md` / `S604_SCRIPT_GAP.md`（本任务【铁律】明列绝对只读，**本会话无权改**） |
| 指纹链 | 9 件派发指纹全部不变（本会话收尾 `readonly_9_unchanged = True`） | 4 件主件 sha256 全部漂移 ⇒ 32 域基线 `mainSha256`/`mainBytes` 失配；`GATE_REJUDGE_32.md` 的 `L108`/`L65`/`L76`/`L32`/`L87` 行号引用、逐字原句摘录、复核回件绑定行、下游引用锚**全部要重算重签** |
| 治理风险 | 无（只读复核 + 新写域） | 违反「只裁决、不施行」（`RULING_MATRIX_AB.md:102` 转述）、「未改任何文件声明」、「零载体写/未改台账」；为过门禁而改**已交付且被复核绑过指纹**的件，等于篡改被核对象 |
| 语义质量 | 不变（交付件原样保留「批准人一律 =」「可唯一重建」等更精确表述） | **下降**：「可唯一重建」补成「可重建」丢掉唯一性断言；「批准人一律 = 乙设计责任人」补一句「需谁批准」是同义反复；「实跑输出」补字面串而不补输出载荷反而制造「有词无输出」假象 |
| 复发 | 同类措辞变体自动覆盖（P06–P20），规格表固定 5 条 | 每次换措辞都要再改一次交付件 + 再重签一轮指纹 |
| 可审计性 | 每条改判有 `spec / logic / evidence / line` + warning；32 域白名单回归 | 改了就是改了，无法区分「原本就写对」与「为过门禁补的」 |
| 成本 | 本会话 2 个脚本 + 若干 `-c` 实跑（exit 全 0，见 §1 表） | 4 件重签 + 所有下游引用锚 + 复核轮回件 + 台账登记，且**本任务纪律禁止** |

**判断**：改交付件在本任务里既不被允许，又会破坏指纹绑定链与语义精度；改判据是唯一可行且代价更低的路。但按 `GATE_REJUDGE_32.md:293` 第 ⑤ 条（本会话实读：「**任务书本身含糊（不是门禁的错）**」），最根本的修复仍在**任务书侧把要素写清**（写明是字面 token 还是语义要求、给出可判定真值条件、禁词表与交付要求先做一致性检查、绑定行格式全局统一）；门禁侧只负**有限**责任：在任务书已写明的要素上做可审计、闭合、可回滚的判据。本层是补偿措施，不是替代上游修复。

### 6.4 未验项（逐条如实，不补造）

1. **43 处 `check_deliverable` 调用方的下游消息全文消费逻辑未逐一实跑**：本会话只做静态扫描（3 处 `startswith("缺要素")`、4 处子串 `in`、0 处全文相等比较）+ 单条 `-c` 诊断串比较（`startswith preserved=True / token unchanged=True / exact full string identical=False`）。复核【复核】⑦ 同口径。下游**逐一执行**未做，标未验。
2. **36 处历史 payload 未落地任何改动**（【铁律】禁止；`GATE_REJUDGE_32.md:231` 同口径）；**35 处历史门禁当时的实跑输出不可复原**（`GATE_REJUDGE_32.md:290` 逐字实读：「不可复原…本轮只判现盘主件文本，不判当时是否误判」）。
3. **复核轮的 5 条近似负样本修补未实施**：V2/V3/V5/V6/V7 的收紧方案（正面证据校验、`待判/是否/尚需/并非/不另下结论` 收入非承诺、7 条准入补可执行校验器）只给方向，**未写代码、未跑回归**；故本设计 `verdict = unconfirmed`。
4. **真机 / 采样一律未做**：按【铁律】零真机、零采样代码；`verdict='post_read_error'` 等输出载荷只作**文本在场**判据，不证明其由真机/实跑产生。
5. **`grep -rl … | wc -l` 的 46 / 55 / 62 三值不一致未追平到历史时点**：本会话只实跑现值 62（含写域 5 件），未复原撰写轮/复核轮当时的目录状态，历史数值标不可复现、不作推断。
6. **本会话自身两次失败已修并如实登记**：① 首跑 `_r9sd_final_verify.py` EXIT=1，stdout 末行 `TypeError: unsupported operand type(s) for +: 'int' and 'list'`（该次输出未留存：后续成功重跑覆盖了同一 stdout 文件；此处按本会话当时实见记录，**无留存输出件可引**），系打印语句 `len(m9s) + other` 把 list 当 int 加，改为 `remaining = m9s + other; len(remaining)` 后通过；② 次跑因 `ROOT.rglob("_r9sd_*")` 遍历全库 566,505 文件（其中 `out/` 136,768 件，本会话 `find`-计数实跑）超过 120s 被移后台并停止，收窄为 `(ROOT/"lead").rglob` 后 `real 0m5.124s EXIT=0`。两次均为脚本工程问题，**不是判据被放宽或收紧**，修复后全量复跑输出即本件所引 `_r9sd_final_stdout.txt`。
7. **§5.3 的 `sys.path` 两行补丁只做了 `-c` 隔离模式实证**（`ModuleNotFoundError` → 补 `sys.path.insert`），**未把带这两行的完整候选模块再跑一遍 `self_test`**；3 处替换版的 `self_test` 实证来自 `_r9s_minpatch_stdout.txt`（不含 `sys.path` 两行，但该脚本自身在 `:20` 已 insert）。补两行后的完整回归标未验。

---

## 附：本交付会话新增产物（全部落 `lead/gate_r9sem_20261109/`）

| 文件 | 作用 |
|---|---|
| `GATE_R9_SEMANTIC_ELEMENT.md`（本件） | 六节交付件 |
| `_r9sd_final_verify.py` / `_r9sd_final_stdout.txt` / `_r9sd_final_out.json` | 九件指纹、5 处独立 R9、7 条近似负样本、POS/NEG、4 域、32 域/302 项、调用方、绑定行格式、越界 |
| `_r9sd_extra.py` / `_r9sd_extra_stdout.txt` | R10 三条豁免 + 7 条角色消融 |

前序产物 `_r9s_*`（撰写轮 13 件）与 `_r9sv_*`（复核轮 10 件）均**未修改**；九件绝对只读件、两台账、`_g7_predicates.py`、`_g9_gate.py` 全程零改动（收尾 `readonly_9_unchanged = True`、`stray_r9sd_files_outside_wdir = []`）。未 commit、未 push。
