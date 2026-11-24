# _eq_criteria.md — 条3 等价类判据设计（lead/equiv_class_20261109/）

**日期**：2026-11-09　**撰写**：等价类判据设计员（独立上下文，只设计判据、不改任何既有件）
**被设计对象**：同文档联查（lead/samedoc_link_20261109/）条3 的「multi 放弃」形态——`_integ_INTEGRATION_REPORT.md:5` 绑定行 hex `ca23c116…` 在同文档内有两个现盘同 hash 文件
**方法声明**：全部数字与行为取自本会话亲自实跑（`python -I -B -X utf8` + 绝对路径，指纹 hashlib）或本次实读「文件:行」。零真机、零采样代码、不 commit、不 push。**唯一写域** = `lead/equiv_class_20261109/`；`lead/samedoc_link_20261109/`、`lead/f2d_rootcause_20261109/`、`lead/r11_f2_fix_20261109/`、`lead/gate_fp7_20261108/` 及全部真实件零改动（只读 + `-B` 防止 import 落 `__pycache__`）。

---

## 0 结论先行

**主推荐：引入严格等价类，严格维度取 J4（「同文档溯源声明背书的字节同一副本群」），不取 J1/J2/J3。** 闭合率 8/10 → **9/10**（条3 恢复，条1 按 R3-2 保留）。

- J1（字节同即同类）：**拒**——在本库真实语料上有已复现的误并形态（§2.2 反例 1–4）。
- J2（字节同且同名）：**拒**——既不恢复条3（两件文件名不同），又有同名跨轮反例（§2.2 反例 2）。
- J3（字节同且角色标注相同）：**按字面拒**——条3 两 token 的行内角色不同（隔离副本 vs 候选，`复制自` 定向），字面下不恢复；其可实施变体（按绑定行角色括注选锚）是**角色消歧机制**而非等价类，属新启发式采集面，本轮不自动化（§2.1 J3 行）。
- 若编排方限定在题面字面三选一（A=不引入 / B=J2 或 J3 / C=J1）：**答 A**——字面 B 是空集（不恢复条3）、字面 C 有实证误并；8/10 是字面判据下的真值（SAMEDOC_LINK.md:133 已如实登记「两个口径的差异是判据差异」），不引入等价类同样自洽。J4 是第三条路，需显式登记（§5.2）。

## 1 第一步：条3 的两个路径到底是什么关系（实跑证据）

**(a) 什么关系：隔离副本是从候选逐字节复制而来的一份忠实副本。**
- 本会话 hashlib 实算（命令见 §6-1）：两文件 sha256 均 = `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2`、412,759 B、`byte_identical = True`。
- 复制记录在案：`lead/b2b_isolated_20261107/_integ_make_isolated_out.txt:1-7`（本会话实读）：「源(候选，只读) = …qc151_trip.candidate_lf.py」「隔离副本(写域) = …qc151_trip.isolated.py」「**COPY_IDENTICAL = True**」。
- 文档自述一致：`_integ_INTEGRATION_REPORT.md:13`「**隔离副本与候选逐字节同一**：`qc151_trip.isolated.py` 复制自 `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`」；`:4` 任务定义「把候选 LF 重物化版复制为隔离副本」。

**(b) 什么角色：同一文档内两个角色对立的物。**
- `:5` 绑定行自注「被核对象（**隔离副本**）」→ 绑定意图指向隔离副本。
- 隔离副本 = D-25 第 6 步「隔离副本离线集成」演练写域件（`_integ_INTEGRATION_REPORT.md:3-4/:53`）；候选 = 上游任务（B_EXECUTION_SPEC 条5/8、_n4 条10）的「正式候选」，与本件角色不同。
- 两者分处**授权边界两侧**：`:17`「本轮是隔离副本集成演练，不构成放行」；`:59` 实读引 `RULING_D25.md:26`「不得把隔离副本离线集成扩大为正式母本应用」。

**(c) 从「绑定行想指向哪个」看：内容上同一对象，角色上不同对象。**
- 绑定行格式本身无路径要求、绑的是「复核时刻现盘值」（F2D_ROOT_CAUSE.md:167 本会话实读 grep 定位）；故**内容维度**：两件验证等价。
- 但 RULING_D25 授权面与文档角色标注都表明**角色维度**：两件是不同对象。条3 的歧义只在「锚到哪个路径」，不在「内容是否验证」。

**联查现状（本会话用被核谓词 CLI 原样复现，命令见 §6-2）**：verdict=**multi**、anchors=2（隔离副本 token `qc151_trip.isolated.py` :13/:85，doc_dir 解析；候选全路径 token `lead/…/qc151_trip.candidate_lf.py` :13，root 解析），warning「……按「唯一命中才采」规则不采任何一者」。

## 2 第二步：等价类判据评估

### 2.1 J1–J4 逐判据

| 判据 | 恢复条3？ | 误并风险（真实反例） | 判 |
|:--|:--|:--|:--|
| **J1** 字节相同即同一对象 | ✓ 恢复 | **已复现的误并**：① Q4_RELATION.md 同文档 6 个同 hash（6694b75e…/26405）转储件锚定 multi（本会话被核谓词实跑，6 文件分属 l1b/l1c/l1d/l1e/l3/q161 **六个不同真机趟**）——J1 会把六趟证据并为一对象，抹掉「哪一趟」这一证据的全部价值；② `b2b_candidate_review_20261106/TASK.md` vs `b2b_candidate_review2_20261106/TASK.md`（63336d05…）两轮 TASK.md 跨轮同字节；③ ca23 同 hash 全库类 ≥4 成员（候选/隔离副本/门禁夹具 `caseB/qc151_trip.derived_same.py`、`v2_newedge/qc151_trip.same.py`），J1 全局并类会连门禁夹具一起并；④ `_sl_run10_out.json` vs `_slv_run10copy_out.json`（ed031e01…/36749，本会话实算 identical=True）——原始记档 vs 复核重放副本，角色不同 | **拒** |
| **J2** 字节同且去目录同名 | ✗ **不恢复**（qc151_trip.isolated.py ≠ qc151_trip.candidate_lf.py） | 仍有真实同名跨轮反例（反例②两轮 TASK.md 同名同字节）→ 并了就错 | **拒** |
| **J3** 字节同且角色标注相同 | ✗ 按字面不恢复：:13 同行给 isolated 配「隔离副本」、给 candidate 配「候选」，`复制自` 定向 → token 级角色不同 | 若改造成「绑定行角色括注匹配成员邻接角色文本则选锚」= 角色消歧机制（M2），不是等价类；属启发式文本匹配，`_sl_link.py:177-178` 的 declared_but_mismatched 前例已示「同行多声明表格行仍可能跨对象误联」，新采集面需独立设计+误绑分析，本轮不自动化 | **拒**（字面）；M2 列为后续独立课题 |
| **J4** 字节同 + 同文档溯源声明可追 | ✓ 恢复（:13 `复制自` + 双 token 同行同现，字节同由谓词现场重算自证） | 见 §2.2/§2.3：无声明即弃权（Q4 实跑弃权、F3 部分覆盖弃权、F2D/_m_CHAIN_VERIFY 实跑弃权）；F4 unique 不降级；声明存在但字节不同→不触发 | **采纳** |

### 2.2 什么**不算**同一对象（真实反例清单，全部本会话实跑/实读）

| # | 反例 | 关系 | J1 会并？ | J4 会并？ |
|:--|:--|:--|:--|:--|
| 1 | **六个不同真机趟的 except 转储**：`lead/qc161_u0400_trip/l1b|l1c|l1d|l1e|l3_20261021/except_post_*.txt`（5 件）+ `out/…/q161/except_post_20261017T230724883941.txt`（+ `l1_u0800_20261020/evidence_r2/except_carrier_6694b75e.txt`，全库同 hash ≥7 件，6694b75e…/26405） | 同哈希、**不同趟次**的证据件——「哪一趟」是证据价值本体 | **并（错）** | **弃**（Q4 文档 decl_lines=[]，本会话实跑弃权） |
| 2 | `b2b_candidate_review_20261106/TASK.md` vs `b2b_candidate_review2_20261106/TASK.md`（63336d05…，同名同字节） | 两轮任务书（跨轮次） | 并（错） | 弃（无声明） |
| 3 | ca23 类的第 3/4 成员：`lead/gate_validate_20261108/_gv_fixtures/caseB/qc151_trip.derived_same.py`、`_verify_vectors/v2_newedge/qc151_trip.same.py`（普查同 hash） | 候选的门禁验证夹具（另一角色/另一测试用例的输入） | 全局并类（错） | 弃（无 .md 引用 → 不进同文档采集面；脚本 `_gv_build_fixtures.py`/`_verify_hy4_build_vectors.py` 引用，grep 实证） |
| 4 | `_sl_run10_out.json` vs `_slv_run10copy_out.json`（ed031e01…/36749，identical=True 本会话实算） | 原始记档 vs 复核会话逐字节重放副本 | 并（错） | 弃（无声明） |
| 5 | 母本 517889c6…/399508 vs 候选 ca23c116…/412759 | 角色对立（授权边界两侧），字节**不同**（今日实况） | 不触发（hash 不同） | 不触发 |
| 6 | 假想：未来零 diff 候选 == 母本同 hash | 角色对立且字节同 | 并（错——抹掉授权边界） | 并——**残余风险**：内容为真、角色边界靠「禁止授权推论」纪律保护（§2.3-③） |

### 2.3 判错了会怎样（后果分级）

1. **内容层：无影响。** 等价类只在「机器现场重算 hash 同值」上建立，错并**不可能产生内容假 MATCH**（hash 同即字节同，碰撞假设排除）。
2. **角色层：损失「哪一趟/哪一轮/哪一角色」的机器主张。** 现消费方只有 warning 文本（人工读）→ 后果 = 人工需从成员列表自行辨认；**若未来自动化消费 `rec.path` 做角色/授权主张 → 错误放行风险**。故判据硬性规定：merged 时 `rec.path=None`（不做单一对象主张）、members 全列、**禁止从 merged 推导角色/授权结论**（RULING_D25:26 边界，`_integ_INTEGRATION_REPORT.md:59` 实读在案）。
3. **伪造面：无增量。** 攻击者要伪造 unique 命中，本来就只需在同文档写一个同 hash 路径（`_sl_link.py` §5.3-1 张冠李戴残余风险）；J4 需要额外的第二同 hash 盘上件 + 声明行，门槛更高不是更低；采集面（只取同文档 token）不变。
4. **证据链层：不与 R3-2 相触。** J4 不改写任何绑定行、只读现盘（R3-2「绑复核时刻现盘值」F2D:167 实读在案）。

## 3 第三步：收益与冲突检查

**(a) 闭合率：8/10 → 9/10。** 条3 由「multi 放弃」变为「merged 闭合」（原型实跑 real_item3：multi → merged，声明行 13，全 2 成员覆盖）；其余 9 条不受影响（unique/zero 一律不介入——条2 文档虽共现双 token 但裸名候选解析不到，实测仍 unique；条1 zero 无类可并）。9/10 与 F2D:160 的对象口径（「9/10 对象在盘且哈希逐一 MATCH」）重新对齐——SAMEDOC_LINK.md:133 登记的「判据差异」由此弥合。

**(b) 值不值：值。** 触发面极窄（multi 且溯源声明行覆盖全体成员——已知真实触发实例仅条3 一处；F2D、_m_CHAIN_VERIFY、Q4 实跑全部弃权），收益是把锚口径与对象口径对齐（F2D:160 vs SAMEDOC_LINK.md:133 的 9 vs 8 差异弥合），失败模式安全（path=None + 成员全列 + warning 级，错误方向是「少闭合」而非「错闭合」）。

**(c) 冲突检查：零冲突。**
1. **R3-2 历史锚豁免（条1）**：zero 分支，无盘上件可并——零交集。
2. **R3-3b（无路径警告）**：zero 分支不动。✓
3. **★「唯一命中才采 / multi 放弃」**（SAMEDOC_LINK.md:20 ★4）：J4 是对该 ★ 规则的**显式修订**（multi → 声明解析 → merged｜multi），登记时必须写明修订关系，不能无声替换。
4. **30 件回归语料 / gate 判档面**：联查未接回 r11_scan_plus（SAMEDOC_LINK.md:22 / §1.2-6 未接回声明），本轮判据 gate 面 = 0。✓
5. **warning 级纪律**（problems 恒空 `_sl_link.py:142/:225-226`）：merged 仍 warning 级。✓

## 4 第四步：三选一的回答

**选 B 方向的「严格等价类」，但严格维度修正为 J4（同文档溯源声明 + 机器字节自证），而非题面 B 所写的 J2/J3。** 理由：题面 B（文件名/角色标注相同才并）按字面是**空集**——条3 两件文件名不同、token 级角色不同，字面 B 连条3 都不恢复，引入无意义；题面 C（J1）在真实语料上有已复现的误并形态（Q4 六锚、跨轮 TASK.md、门禁夹具、sl_run10 对）。**若编排方只接受字面 A/B/C：答 A**——8/10 是字面判据下的真值，条3 保留 multi 放弃同样自洽；等价类的正确严格维度（声明背书）不在题面选项内，作为第三条路显式登记后另行裁决。

**不放松声明**：J4 不比 J1 松（多一个可审计的声明条件），对真实反例弃权；条3 恰好满足严格条件，不是把判据削足适履。J4 的额外条件（溯源声明）独立成立：它区分「声明为副本的忠实复制」与「不同趟次证据件恰好同哈希」——后者是 Q4_RELATION.md:85/:168 里的真实语用（「与 113 份 except_post_*.txt 逐字节相同」是**发现**不是复制关系），因此声明词组**刻意排除**「逐字节同一/相同」这类纯等同词，只收溯源动词（复制自/复制为/COPY_IDENTICAL=True）。

## 5 第五步：可执行判据实现（若引入）

### 5.1 判据伪代码（= `_eq_proto.py` `eq_merge` 实跑行为，机器记录 `_eq_proto_out.json`）

```text
常量  DECL_RE = /复制自|复制为|COPY_IDENTICAL\s*=\s*True/     # 溯源词组（封闭集，刻意排除纯等同词）
输入  text(文档全文), res = link(text, doc_dir, binding_hex, bytes_decl)   # 被核谓词 _sl_link.py:138
规则  仅当 res.verdict == "multi" 时介入；unique/zero 一律原样返回（unique 不因类降级）:
      1. 对每个 multi 成员 m，取其锚定 token 行号集 L(m)（res.anchors[].tokens[].lines）
      2. D = {行号 L : text 第 L 行匹配 DECL_RE 且 |{m : L ∈ L(m)}| >= 2}
      3. 若 D 非空且 ∪_{L∈D} covered(L) == 全体成员:  → verdict = "merged"
         warning 列全部成员路径 + 声明行号 + 声明原文；reverify 对每成员记录 path/sha/bytes
         rec: tier="SAMEDOC_LINK_EQ", path=None（不做单一对象主张）, match=True, members=[…]
      4. 否则（无声明行 / 覆盖不全）: 维持 multi 放弃（全或无，不部分合并）
```

原型实跑记录（6+3 案，driver 指纹守卫 a4ae4dc1…/12475 MATCH）：real_item3 multi→merged（声明行 13，2 成员）；real_q4_dumps multi→multi（6 锚，decl_lines=[]）；F1 无声明双件 multi→multi；F3 声明仅覆盖一件 multi→multi（全或无）；F4 unique→unique；F2D_ROOT_CAUSE multi→multi（decl_lines=[]）；M_CHAIN_VERIFY multi→multi（decl_lines=[]）；GATE_TEMPLATE_REGRESSION unique→unique（不介入）。辅查脚本 `_eq_surface_probe.py`，输出以会话 stdout 为准（该探针只读不写盘）。

### 5.2 需要登记什么

**一次性（台账 PENDING_DECISIONS.md / GOAL_THREE_TARGETS_20261018.md）：**
- 判据 ID：建议 **R3-3e「同文档声明背书等价类」**（与 R3-3b 警告通道、R3-2 历史锚并列成文）。
- 判据全文 + 适用范围：仅同文档联查谓词的 multi 分支；仅 warning 级；仅溯源词组（封闭集，排除纯等同词）；仅全或无覆盖；unique/zero 不介入。
- 对 ★ 规则（SAMEDOC_LINK.md:20 ★4「唯一命中才采」）的**显式修订声明**：multi 不再无条件放弃，改为「声明解析 → merged｜multi」。
- 契约变更：新 verdict `merged`、tier `SAMEDOC_LINK_EQ`、rec 形态 `path=None + match=True + members`——消费方（若未来接入 r11_scan_plus）必须先适配 path=None 形态。

**每次运行时（合并事件逐次记档）：** 合并事件全部落 run 机读件（`_sl_run10_out.json` 同款模式）：`{binding_hex, bytes_decl, members:[{path, sha, bytes}], decl_lines, decl_text}`。要记——每次合并都记，因为等价类是「联查时刻快照」（TOCTOU 同限，SAMEDOC_LINK §5.3-6），事后审计需要当时的成员与声明行。

### 5.3 合并后的人工复核要求（机器合并，人核四项）

1. **实读声明行原文**：确认声明主语就是成员文件本身，不是表格行误扫（`_sl_link.py:177-178` 已示同行多声明表格行的跨对象误联风险）。
2. **绑定行角色括注与成员集核对**：条3 = 「（隔离副本）」↔ 成员 `qc151_trip.isolated.py` 相符 ✓（本会话实读 :5/:13/:85）。
3. **禁止由 merged 推导角色/授权结论**：merged ≠ 放行；隔离副本集成通过 ≠ 母本可写（`RULING_D25.md:26`，`_integ_INTEGRATION_REPORT.md:59` 实读在案）。
4. **TOCTOU 抽查**：成员件 hash 现盘重算（与全家族回验同限）。

## 6 实跑命令与指纹（本会话全部亲自执行）

| # | 命令 | 关键输出 |
|:--|:--|:--|
| 1 | `python -I -X utf8 -c`（hashlib 双件实算+逐字节比较） | 两件 sha256 = ca23c116…/412759，`byte_identical = True` |
| 2 | `python -I -B -X utf8 …\samedoc_link_20261109\_sl_link.py …\_integ_INTEGRATION_REPORT.md ca23c116… 412759` | verdict=multi、anchors=2、放弃采集 warning 全文 |
| 3 | 实读 `_integ_make_isolated_out.txt:1-7` | 源=候选、隔离副本=写域件、COPY_IDENTICAL=True |
| 4 | `python -I -X utf8 -c`（lead/ + 母本目录全树普查，size 分桶+hashlib） | 7394 件、911 组重复（多为 1 B 夹具） |
| 5 | 同上（≥4096 B 过滤） | 3637 件、451 组重复（多为截图） |
| 6 | `python -I -X utf8 -c`（文本类跨任务重复组） | 12 组（含 ca23 类 4 成员、TASK.md 跨轮对、except 转储类、sl_run10 对） |
| 7 | grep/CLI：条2 文档 `INTEGRATION_REPORT.md` | 裸名候选不解析 → unique（多 token ≠ multi） |
| 8 | CLI：F2D_ROOT_CAUSE / _m_CHAIN_VERIFY / GATE_TEMPLATE_REGRESSION | multi / multi / unique |
| 9 | `python -I -B -X utf8 …\equiv_class_20261109\_eq_proto.py` | 6 案行为如 §5.1（guard a4ae4dc1…/12475 MATCH） |
| 10 | `python -I -B -X utf8 …\_eq_surface_probe.py` | F2D/m_CHAIN 弃权、GATE_TEMPLATE 不介入 |
| 11 | grep Q4_RELATION.md 上下文 | :55-59 五条转储全路径 + :12 hash 行（无「被核对象」前缀，非门禁绑定行）；:85/:168 含「逐字节相同」语义但无溯源动词 |

写域件指纹（本会话 hashlib 实算）：
- `_eq_proto.py` = dcb01858955f9b236f0a430430f8172bd5539a82b0aeb7014932c42c4fda4458 / 7645 B
- `_eq_proto_out.json` = c5e19d798c46ee53e5fccafbb1e082ed38f22d1aaa508061d6e617c6d30959f7 / 7519 B
- `_eq_surface_probe.py` = 920e3c89d8969496aa4d3503fb5009db02fba70378928f333001c84067e330e0 / 2052 B（修订后此值失效，以消费方实算为准）

## 7 未验项（单列，不补造）

1. 343 件全语料的 multi 作用面未普查（与 SAMEDOC_LINK §5.6-3 同限）——已知真实 multi 文档 = 条3 件、F2D_ROOT_CAUSE、_m_CHAIN_VERIFY 三份（ca23 hex 实测），其余未验。
2. eq_merge 未并入 `_sl_link.py` 实件（本任务禁改只读件；并入与否、词组终版由编排方裁决）。伪代码/原型行为 ≠ 已上线行为。
3. Q4 同 hash 转储类全库成员数未再普查（已知 ≥7 件：CLI 6 锚 + carrier 裸名未解析件）。
4. M2（绑定行角色括注消歧）机制未设计未验证——列为后续独立课题。
5. TOCTOU 漂移窗口不可实测（零真机 + 只读纪律），仅登记。
6. J4 声明词组是封闭集，漏词 = 漏闭合（安全方向）；不得为提升闭合率扩词组（纯等同词已实证会误触发语义，§4）。

---

（本件一次写成、无自嵌哈希——朴素自绑定密码学不可行；全件 SHA256/字节数由消费方 hashlib 实算。）
