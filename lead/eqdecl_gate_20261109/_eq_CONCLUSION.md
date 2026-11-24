# _eq_CONCLUSION.md — 结论与边界（第五步）

本件是 `lead/eqdecl_gate_20261109/` 的结论件。判据形式见 `_eq_DESIGN.md`；
实现见 `_eq_detector.py`；正/负控实跑输出见 `_eq_selftest_out.json`；
三关 × 9 案例矩阵见 `_eq_three_gates_out.json`；全量跑见 `_eq_full_out.json`。
**本任务只做检测器，未执行任何被检文档改写。**

---

## 0. 交付物与实跑命令（本会话实跑，逐字）

| 产物 | 实跑命令 | 输出要点 |
|---|---|---|
| 基线指纹核对 | `python -I -X utf8 -c "<11 件 read_bytes + hashlib.sha256 + len>"` | 11/11 与编排方【基线指纹】全等 |
| 8 格穷举 | `python -I -X utf8 -c "<itertools.product 8 格；F(A⊆B)/F(B⊆A)/F(P)>"` | `F(AsubB)= []` / `F(BsubA)= [('PASS','CATCH','PASS')]` / `F(P)= [('PASS','CATCH','PASS'),('CATCH','CATCH','PASS')]` / `strict_superset= True` / `fork cells = [('CATCH','CATCH','PASS')]` / `taut_AsubB= True` |
| 74 行复核 | `python -I -X utf8 -c "<读 _gp_regression_out.json:rows>"` | `N= 74 A_n= 18 B_n= 18 sets_equal= True den= 38 num= 38 cells_r10C_n13P_r12C= 0` |
| 窗口半径量测 | `python -I -X utf8 -c "<8 目录全 .md 分块；量测两半标记最小行距>"` | `n_blocks 958 / max_block_len 76 / median 3.0`；两半同块 42 个，距离分布 `[(0,32),(1,4),(2,2),(5,3),(8,1)]`，**最大 8** |
| 局部半径量测 | `python -I -X utf8 -c "<全 lead 树 .md；强度标签行→最近范围词距离>"` | `0:288 / 1:90 / 2:86 / 3:61 / 4:22 / 5:3 / 6:7 / 7:3 / none:929` ⇒ 85% 在 ±2 行内 |
| 正/负控 | `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/eqdecl_gate_20261109/_eq_detector.py --selftest > D:/Project/ra2-campaign-forge/lead/eqdecl_gate_20261109/_eq_selftest_out.json` | `EXIT=0`，`n_controls 10 / n_passed 10 / n_failed 0`，`N6_category TAUTOLOGY` |
| 三关 × 9 | `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/eqdecl_gate_20261109/_eq_three_gates.py` | `三关 × 9 案例：9/9 通过`；关一 3/3、关二 3/3、关三 3/3 |
| 全量跑 | `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/eqdecl_gate_20261109/_eq_full_run.py` | 15 件 .md / 918 锚点 / 212 findings（F1 57、F2 5、F3 150）/ 27 tautology_ok / 188 passes / 346 skips / 145 undecidables |
| 只读零漂移 | `python -I -X utf8 -c "<11 件收尾 hashlib 对照>"` | `READ_ONLY_FINAL_MATCH = True n= 11` |
| 未 commit | `git log -1 --oneline` | `2657458`（与会话开始一致） |

★ 开发过程中检测器曾 3 次未通过自测（N1 分类、F3 范围判据、S2/S7 误报 F1），
均**如实保留在修正记录里**：最终 `n_passed 10/10` 是修正后**重跑**的结果，不是首次结果。

---

## 1. 三关 × 9 案例完整矩阵（逐格）

期望列来自编排方【任务】第三步 (a)(b)(c)；实际列来自
`_eq_three_gates_out.json`（本会话实跑）。`TAUTOLOGY_OK` = 判「重言式」；
`SUBSTANTIVE_OK` / `PASS_QUALIFIED` = 判「实质条件」且不报 F1/F2/F3。

| 关 | 案例 | 锚点 file:line | 期望判定 | 实际判定 | 通过 |
|---|---|---|---|---|---|
| 关一 | S1 半 `A⊆B` | `lead/layer_identity_20261109/LAYER_IDENTITY.md:104` | 重言式，不报 F | `TAUTOLOGY_OK` / 无 F / `TAUTOLOGY` | ✅ |
| 关一 | S3 `:125` 去掉合取项的逻辑重言式 | `lead/layer_identity_20261109/_li_LAYER_IDENTITY_PROOF_20261109.md:125` | 重言式，不报 F | `TAUTOLOGY_OK` / 无 F / `TAUTOLOGY` | ✅ |
| 关一 | S12 S3 DEFAULT 恒真兜底 | `lead/score_decomp_20261109/SCORE_DECOMP.md:235` | 重言式，不报 F | `TAUTOLOGY_OK` / 无 F / `TAUTOLOGY` | ✅ |
| 关二 | S2 `:104` 依赖图（正确否定句） | `lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md:104` | 实质条件，不报 F | `SUBSTANTIVE_OK` / 无 F / `SUBSTANTIVE` | ✅ |
| 关二 | S4 正确等价式 | `lead/layer_identity_20261109/LAYER_IDENTITY.md:128` | 实质条件，不报 F | `PASS_QUALIFIED` / 无 F / `SUBSTANTIVE` | ✅ |
| 关二 | S7 Fréchet `min q_i` 恰取等 | `lead/keff_calc_20261109/KEFF_CALC.md:262` | 实质条件，不报 F | `SUBSTANTIVE_OK` / 无 F / `SUBSTANTIVE` | ✅ |
| 关三 | S1「决定性集合等式」标签 | `lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md:108` | 报 F3 | `FAIL / F3 / SUBSTANTIVE` | ✅ |
| 关三 | S5「R12 增量 0 bit」全称 | `lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md:149` | 报 F3 | `FAIL / F3 / SUBSTANTIVE` | ✅ |
| 关三 | S8「38/38」 | `lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md:107` | 报 F3 | `FAIL / F3 / SUBSTANTIVE` | ✅ |

**9/9 全通过，无「期望问题」格。** 三处曾出现的实际不符（G1a/G1b 被误报 F2、
G1c 被 skip、G2a/G2c 被误报 F1、G3b 被 skip）全部是**检测器的问题**，
已按「只读形态、不猜语义」的原则修正：
- Q3 依据只对「确实写了两段式（T∧S）」的声明追究，不施加于单一命题；
- F1 义务只施加于 `E_EQ_STRICT`（严格 A=B / ⟺ / 集合断言），不施加于
  「正确否定句」与 Fréchet 不等式；
- `恒真兜底` / `取等` / `≤ min q_i` 补进 M4 形态后才能成为锚点；
- F3 的强度侧补 `UNIVERSAL_CLAIM`（`= 0 bit` / `= 1.000` / `38/38=1`），
  使无显式强度标签但「全称口吻 + 观测数值」的 S5 也能命中；
- F3 的范围 `R_same_line` 只看**锚点行自身**（「中间无范围声明」= 同行），
  避免邻行/8 行外的「反事实 / 未验」把真 F3 洗掉。

---

## 2. 全量跑（第四步，如实）

- 范围：8 个只读目录全部 `.md` = **15 件**；编排方【恒等类断言清点】45 行
  **45/45 全部被 M1–M5 命中成为锚点**（`n_not_anchored = 0`）。
- 总 findings = **212**；按失败型 `F1 57 / F2 5 / F3 150`。
- 按文件（前 6）：`TAUTOLOGY_AUDIT.md 77`（F3 62/F1 12/F2 3）、
  `_ta_TAUTOLOGY_AUDIT_20261109.md 59`（F3 47/F1 10/F2 2）、
  `LAYER_IDENTITY.md 14`（F1 7/F3 7）、`EVIDENCE_INDEPENDENCE.md 11`（F3 8/F1 3）、
  `METRIC_CONVENTION_AUDIT.md 10`（F3 8/F1 2）、
  `_li_LAYER_IDENTITY_PROOF_20261109.md 9`（F3 7/F1 2）。完整 15 件见 `_eq_full_out.json:by_file`。
- 45 行中判 FAIL 的 5 行：`LAYER_IDENTITY.md:13`(F1) / `:223`(F3) / `:242`(F1) /
  `:338`(F3) / `COMPARABILITY_AUDIT.md:158`(F1)；其余为
  `SKIP 19 / UNDECIDABLE 9 / CORRECTLY_SCOPED 8 / TAUTOLOGY_OK 2 / PASS_QUALIFIED 2`。
- skip 计数（15 件合计 491）：`K1 267 / K6 145 / K3_question 35 /
  K3_intensity 25 / K2 19`。其中 `K6_structure_unclassifiable = 145` 是
  「窗口结构齐全但无法归类」的**无法判定**桶 —— 门禁按铁律「宁可报无法判定
  也不许猜」不产 finding，全部保留 `file:line` 与原文行。
- (d) 漏检核对：**S1 那种「决定性集合等式」没有漏检**。全量命中该串 10 行，
  含 `METRIC_CONVENTION_AUDIT.md:108`（本次要害）与 `_ma_METRIC_AUDIT.md:77`
  （`TAUTOLOGY_AUDIT.md:446` 列的 S1 另一落点），均报 F3。
  45 行 `n_not_anchored = 0` 亦证明无形态层漏检。
- (b) 抽样 **19 条**（≥15，含两边）：真命中 13 / 误报 6，逐条 file:line、原文、
  误报原因见 `_eq_full_out.json:sampling.samples`。6 条误报逐条说明：
  1. `METRIC_CONVENTION_AUDIT.md:126` — 评审判定表讨论 `38/38` 口径，非本件升级为定理；
     `QUOTE_OR_REVIEW` 未覆盖「错置 / 降级存疑」语气。
  2. `TAUTOLOGY_AUDIT.md:356` — §3.4 检查清单的**禁用串清单**；`TAUTOLOGY_AUDIT.md:760-763`
     自记同类门禁自触发先例。
  3. `TAUTOLOGY_AUDIT.md:366` — 强模式扫描的**串清单回显**。
  4. `LAYER_IDENTITY.md:384` — 整改意见表（`→ 改`），K5 豁免要求 `not E and not O` 太严。
  5. `METRIC_CONVENTION_AUDIT.md:21` — 空表头行，被 ±8 窗口内邻行观测数值连坐报 F1；
     F1 用整窗 T/S 而非锚点局部。
  6. `LAYER_IDENTITY.md:267` — 「决定性」是**方法名**（依赖图源节点数），非定理标签。
- (c) **精确率估计 = 0.6842**（13/19，来自抽样；明确标注**这是估计不是测量**）。
  **召回率不给数值**：无人工全量标注，真值总数未知。可见下界只有
  「三关 9/9」+「45 行中 5 行 FAIL」，不是召回率分母。
  `TAUTOLOGY_AUDIT.md:370` 自记「未做全仓逐文件人工通读」，本任务同样未做
  15 件 `.md` 全量人工逐行标注 ⇒ 不得冒充精确率/召回率实测。

---

## 3. (a) 能不能上线？——判断与前置条件

**判断：不能作为「拒件门禁」上线；可以作为「只报不拒」的成件后 lint 上线（有条件）。**

理由（全部落在本会话实跑输出）：
1. 三关 9/9、正/负控 10/10、45/45 锚点覆盖 ⇒ **核心判据自证成立**，能抓到
   `TAUTOLOGY_AUDIT.md:730-731` 自认「仍是提案、未实装」的那个缺口。
2. 但全量 212 findings、抽样精确率估计仅 0.6842、误报 6/19 ⇒ **直接拒件会淹没人**。
   误报根因是字面门禁的结构性限制（清单回显 / 整改意见 / 方法名 / 空表头连坐），
   `TAUTOLOGY_AUDIT.md:760-763` 已实跑证明「门禁查的是字面而非语义」。
3. `K6 无法判定 = 145` 条被跳过不报，符合「宁可报无法判定也不许猜」，
   但也意味着**静默漏报可能存在且未被量化**（见 §5）。

**上线前置条件（缺一不可）**：
- P1 把 §2 的 6 类误报形态做成 `EXEMPT` 白名单（清单回显行 / 整改意见行 /
  `→ 改` 表 / 空表头 / 方法名「决定性」），并**重跑正/负控 + 三关 9 案例**
  确认不回归；本任务未做（只登记，不实装）。
- P2 人工全量标注至少一份 `.md`（建议 `METRIC_CONVENTION_AUDIT.md`，10 findings）
  给出精确率/召回率**测量值**，替换现在的估计。
- P3 把 `R_same_line` / `LOCAL_RADIUS=2` / `WINDOW_RADIUS=8` 三个经验常数
  在新语料上重量测（本任务只在 8 个只读目录的 15 件 `.md` 上量测过）。
- P4 明确「F1 格式缺失 ≠ 语义错误」的处置：如 `COMPARABILITY_AUDIT.md:158`
  （S10）被报 F1，而 `TAUTOLOGY_AUDIT.md:455` 判它「措辞未升级为定理，风险低」；
  两者不矛盾但运维上必须写明 F1 只是「建议补两段式」。
- P5 复核回件按【铁律】绑定行格式登记本件产物 SHA256 + 字节数。

---

## 4. (b) 挂哪个环节：建议

**建议：挂在「成件后」，只报不拒（report-only lint）；不挂「派发前」。**

- **不挂派发前**：派发前输入是任务书/口头措辞，形态 M1–M5 尚未成形；
  且 `TAUTOLOGY_AUDIT.md:461` S16 记三句旧措辞是**口头措辞**、在两件台账 0 命中
  ⇒ 派发前跑本门禁没有可检对象。
- **挂成件后**：本门禁的输入是「一份 `.md`」，正对应成件后的审计/报告文本；
  `TAUTOLOGY_AUDIT.md:534-551` §5.4 八条防机制的定位也是「**报告里**防止的机制」。
- **只报不拒**：输出落 `_eq_*_out.json`，附 `file:line` + 原文行 + 失败型 + 缺什么，
  交人工复核；由 §3 的精确率估计 0.6842 决定不能自动拒件。
- 与 `TAUTOLOGY_AUDIT.md:547-549` §5.4 第 6 条「负例哨兵（生成时断言）」的差别：
  那条是**生成时**禁用串断言，本门禁是**成件后**两段式格式 lint；两者互补，
  本任务实装的是后者，前者仍按 `:549` 自记「未实装」（本任务不改脚本）。

---

## 5. (c) 检测能力边界：结构上抓不到的恒等类断言（清单）

1. **无 M1–M5 字面形态的隐晦等价**：如「两半其实一样」「这不增加信息」等 paraphrase；
   skip K1 直接跳过（`n_skips` 中 K1 = 267）。
2. **跨文件 / 跨硬边界段落的两段式**：重言半在 A 文件、实质半在 B 文件，
   或距离 > `WINDOW_RADIUS=8` ⇒ 窗口取不到；本语料实测最大距离 8，但这是经验值。
3. **语义正确性的任何判定**：判不了 forbidden 格**方向**写反
   （`TAUTOLOGY_AUDIT.md:590` 记上游曾把 `F(A⊆B)` 写成 `B∧¬A`）、判不了
   「同一命题」是否真的等价（`:292` 需比对 forbidden sets，本门禁只查字面）、
   判不了 `38/74` 与 `38/38=1` 同名不同分母混淆（`:392`）。
4. **真值/定理的数学证明**：`TAUTOLOGY_AUDIT.md:270-271` 的「不读任何数据只靠
   逻辑连接词证明」本门禁**不执行**，只认作者写下的显式重言标签
   （`TAUT_LABEL_ON_LINE`）；作者不写标签就判不出 `TAUTOLOGY`。
5. **代码级不变量是否真有全称证明**：`依赖图 / file:line` 出现即算 BASIS_CODE，
   不验证该 `file:line` 是否真的存在、是否真的证出全称。
6. **引用 / 转述 / 清单回显 / 整改意见与真断言的区分**：6 条误报中 4 条属此类
   （`:356`、`:366`、`LAYER_IDENTITY.md:384`、`METRIC_CONVENTION_AUDIT.md:126`），
   字面门禁结构上无法可靠区分。
7. **「决定性」作方法名/标题 vs 作定理标签**：`LAYER_IDENTITY.md:267` 误报即此因。
8. **空表头 / 表格列被邻行连坐**：F1 用整窗 T/S，`METRIC_CONVENTION_AUDIT.md:21` 误报。
9. **K6 静默漏报**：145 条 `UNDECIDABLE` 不产 finding，其中可能含真违规，未量化。
10. **两件台账的别论域措辞**：`GOAL_THREE_TARGETS_20261018.md` 含「恒等」46 行
    （`TAUTOLOGY_AUDIT.md:609` 自记），K2 一律跳过 ⇒ 未全仓逐行核属别论域（同 `:729` 自判未验）。
11. **换语料后的半径与串表**：`R=8 / R_local=2` 是 15 件 `.md` 上的经验值；
    M1–M5 逐字串表也是本库形态，新写法（如 `A ≡ B`、`if and only if`）未覆盖。

---

## 6. (d) 这条工作判不了什么（如实列）

- **真机运行态**：铁律零真机 ⇒ `gamemd.exe` / `ra2loader` / `YURI.exe`、活进程内存
  一律未验；本会话未启动、未 taskkill、未读活进程内存、未写任何 hook / MiniDump /
  SuspendThread / StackWalk / 注入 / 动态内存解析代码。
- **X1 反例的谓词直调**：本会话**未**重跑 `r12_scan` 对
  `'不得不承认放行 N-5'` 的实跑；只复核了 8 格穷举 + 74 行 JSON 统计，
  并引用编排方【背景】给的 X1 输出与 `TAUTOLOGY_AUDIT.md:191-234` §2.5 记录。
  ⇒ 该反例在本任务内标**未验（引用，未重跑）**。
- **生产语料泛化 / 两条全称升级条件**：`TAUTOLOGY_AUDIT.md:713,716-718` 自记未验，
  本任务未做 ⇒ 未验。
- **`_gp_regression_out.json` 生成过程**：只以现盘 SHA 读 `rows`，未重跑
  `_gp_regression.py`（只读）⇒ 生成过程未验（`:723-724` 同判）。
- **两条台账的其它论域措辞、k_eff 点值 / bootstrap 重算**：未全仓人工通读、未重算
  ⇒ 未验（`:722,729` 同判）。
- **精确率 / 召回率的真值**：无人工全量标注 ⇒ 只有估计，不是测量（§2(c)）。
- **K6 145 条无法判定中是否含真违规**：未逐条人工核 ⇒ 未验。
- **被检文档措辞是否被改**：本任务不执行任何改写；只以 11 件 hashlib 指纹
  前后对照证明零漂移（`READ_ONLY_FINAL_MATCH = True`）。两件台账与七个只读目录
  的**全部文件**未做逐件指纹（只核编排方给的 11 件），其余文件零漂移未逐件测量。
- **本件自身 verdict**：未请求第三方复核，不自行标 `confirmed`；上游
  `TAUTOLOGY_AUDIT.md:563-565` 按 `partial` 标 `unconfirmed`，本件不改动该 verdict。

---

## 7. 纪律核验

| 项 | 实跑 / 结果 |
|---|---|
| 零真机 | 未启动 gamemd.exe / ra2loader / YURI.exe；未 taskkill；未读活进程内存 |
| 零采样代码 | 全部脚本为 `hashlib` / `re` / `json` / `pathlib` 纯文本只读；无 hook、无注入、无动态内存解析 |
| 绝对只读 | 11 件基线指纹收尾 `READ_ONLY_FINAL_MATCH = True`；`lead/PENDING_DECISIONS.md`、`GOAL_THREE_TARGETS_20261018.md` 未改 |
| 唯一写域 | `lead/eqdecl_gate_20261109/` 共 7 件，全部 `_eq_` 前缀 |
| Python 纪律 | 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib.sha256` |
| 不 commit / push | `git log -1 --oneline` = `2657458`（与会话开始一致），未执行 git 写操作 |
| 不改被检文档措辞 | 本任务只产检测器与 JSON 结果，未写任何被检 `.md` |
| 命中附证 | 每条 finding 含 `file:line`、`text` 原文行、`evidence_lines`（窗内逐行 file:line + 原文）、`evidence_matches`（命中串） |
| 自证不猜 | `UNDECIDABLE` 145 条 + `SKIP` 346 条均不产 finding，保留原文与原因 |

---

## 8. 复核回件绑定行（严格格式）

被核对象 = 本任务主交付件（门禁实现）`lead/eqdecl_gate_20261109/_eq_detector.py`
—— 按 `TAUTOLOGY_AUDIT.md:567-571` 同款约定，绑定行指向**交付件本身**而非复核回件，
避免「回件内含自身哈希」的自指悖论。收尾 `python -I -X utf8 -c "<hashlib.sha256 + len>"` 实算：

被核对象 SHA256 = f29a34b516c14a1320c5bd28a9788801e2c577ff8ae34eea0f41b3d035363472，字节数 = 29795

其余 6 件本会话实跑指纹（`python -I -X utf8 -c "<hashlib.sha256 + len>"`）：

```
_eq_DESIGN.md           sha256=08736dab1f2851cfc18633b5f4ccc14a5d07a3c45e35660f70a5c5f9977c08f5 bytes=23097
_eq_detector.py         sha256=f29a34b516c14a1320c5bd28a9788801e2c577ff8ae34eea0f41b3d035363472 bytes=29795
_eq_full_out.json       sha256=efb6542717e99bf57ab821e1eb759ce3f12f8b1b84fd5ef2bb1253a9aaed2919 bytes=3293219
_eq_full_run.py         sha256=1477d5455c2a2cdc31217aca05306de155d6dad480090e550efac925c91b05e0 bytes=16429
_eq_selftest_out.json   sha256=42b5d7f3acd3260eb4601d91eb865abf18be505b614d58e44c04671df6fbe21f bytes=10222
_eq_three_gates.py      sha256=63d498b6c60fd3480ef51578b23385e451f37cf6974c5dfef84e7c52a8c8c3d0 bytes=8330
_eq_three_gates_out.json sha256=2c9c4fe995f6164e66e251ab903a73c480f03f80321c5d833ea7ce321d2b64be bytes=33009
```

★ 按【铁律】「复核回件必须含绑定行」，上方绑定行与 `submit_result` 的 `evidence`
字段均以严格格式 `被核对象 SHA256 = <64 hex>，字节数 = <数字>` 给出
`_eq_detector.py` 的 `hashlib` 实算值；中间不插路径、括号、星号、反引号或空格。
