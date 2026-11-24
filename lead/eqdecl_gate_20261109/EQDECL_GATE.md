# EQDECL_GATE.md — 「两段式等式声明」门禁：判据形式、实现、三关验收、全量结果与上线结论

本件是 `lead/eqdecl_gate_20261109/` 的**成件总成**：把实现员第一步–第五步的判据形式（`_eq_DESIGN.md`）、实现（`_eq_detector.py`）、正负控自检（`_eq_selftest_out.json`）、三关矩阵（`_eq_three_gates_out.json`）、全量结果（`_eq_full_out.json`）、结论边界（`_eq_CONCLUSION.md`）与【复核】回件（verdict = partial）整合为六节。**本任务链只做检测器，未修改任何被检文档的措辞**（零漂移证据见 §1.2/§6.2）。

【复核】verdict = **partial** ⇒ 按交付规则标 **unconfirmed**（§6.2）。本件对复核员点名的三处缺陷逐条复验，并对实现员回件中新发现的两处文档-代码漂移（形态合计 22 vs 代码 24；DESIGN §1 M2d 注记）如实登记（§2.1、§6.2⑤）。

本件撰写会话（2026-11-10）纪律：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）、零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）、绝对只读（两件台账与七个只读审计目录零改动）、唯一写域 = `lead/eqdecl_gate_20261109/`、Python 一律 `python -I -X utf8` + 绝对路径、指纹用 `hashlib.sha256`、不 commit / 不 push（`git -C D:/Project/ra2-campaign-forge log -1 --oneline` 前后两次均 = `2657458 GOAL-3T: 台账 §400→§508 与 D-07..D-11 裁决登记入账`；`git status --porcelain -- lead/eqdecl_gate_20261109/` = `?? lead/eqdecl_gate_20261109/`，全目录 untracked）。

本件撰写会话实跑命令 **19 组**（指纹核验 ×2、计数复算、引用行批量摘录、自检复跑、三关联跑、全量联跑、争议行旗标提取、G2a 形态取证、台账行数统计、`_li:146` 落桶取证、F2 落点清点、复核员量测脚本复跑等），每条结论可追到下文标注的「命令 + 输出」或「文件:行」。

写域现状清单（`python -I -X utf8 _eqg_fp.py` 实跑输出 `EXTRA_FILES`，收尾轮）：

| 文件 | SHA256 | 字节 | 归属 |
|---|---|---|---|
| `_eq_detector.py` | f29a34b516c14a1320c5bd28a9788801e2c577ff8ae34eea0f41b3d035363472 | 29795 | 实现员（绑定行对象） |
| `_eq_DESIGN.md` | 08736dab1f2851cfc18633b5f4ccc14a5d07a3c45e35660f70a5c5f9977c08f5 | 23097 | 实现员 |
| `_eq_CONCLUSION.md` | 75ccfa0eae876eed9f8a8c9abe8557928623974c1cffbb212372d4a669c8439c | 18297 | 实现员 |
| `_eq_three_gates.py` | 63d498b6c60fd3480ef51578b23385e451f37cf6974c5dfef84e7c52a8c8c3d0 | 8330 | 实现员 |
| `_eq_three_gates_out.json` | 2c9c4fe995f6164e66e251ab903a73c480f03f80321c5d833ea7ce321d2b64be | 33009 | 实现员（本会话联跑复现同哈希） |
| `_eq_full_run.py` | 1477d5455c2a2cdc31217aca05306de155d6dad480090e550efac925c91b05e0 | 16429 | 实现员 |
| `_eq_full_out.json` | efb6542717e99bf57ab821e1eb759ce3f12f8b1b84fd5ef2bb1253a9aaed2919 | 3293219 | 实现员（本会话联跑复现同哈希） |
| `_eq_selftest_out.json` | 42b5d7f3acd3260eb4601d91eb865abf18be505b614d58e44c04671df6fbe21f | 10222 | 实现员（本会话复跑同哈希） |
| `EQDECL_GATE.md` | （本件；按 `TAUTOLOGY_AUDIT.md:567-571` 约定不写自哈希，避免自指悖论） | — | 本件 |
| `_eqg_fp.py` / `_eqg_counts.py` / `_eqg_lines.py` / `_eqg_lines_out.txt` / `_eqg_selftest_rerun.json` | 见 `_eqg_fp.py` 收尾输出 | — | 本件核验工件（`_eqg_selftest_rerun.json` 与 `_eq_selftest_out.json` 字节全同） |
| `_eqv_detector.py` 等 7 件 `_eqv_*` | 见 `_eqg_fp.py` 收尾输出 | — | 复核员工件 |
| `__pycache__/*.pyc` ×2 | — | — | 副产品，非交付件（复核员 §5 已记） |

---

## 1 目的与边界（只做检测器，不改任何被检文档措辞）

### 1.1 目的

把 `lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md:730-731` 自认未实装的缺口——「**负例哨兵机检是否实装**：`LAYER_IDENTITY.md:400`、`METRIC_CONVENTION_AUDIT.md:283` 均自记『仍是提案、未实装』⇒ 本任务**未实装**，只给可粘贴清单（§3.4）」——实装为**可跑的「两段式等式声明」门禁**：对一份 `.md` 逐行识别恒等类断言（§2.1），按「合格两段式声明」四条件（§2.2）判合格/失败（F1/F2/F3，§2.3），判不了就报 SKIP / UNDECIDABLE（§3.3），绝不猜。

上游范式（判据的唯一来源，逐字）：

- `TAUTOLOGY_AUDIT.md:314-316`（§3.3 第 5 条「强制报告格式」）：
  > 5. **强制报告格式**：
  >    `A=B ⟺ [重言半：定义式 + 8 格穷举] ∧ [实质半：禁止格为空，依据=…/仅 N 行]`，
  >    并附「破坏它的输入」（`LAYER_IDENTITY.md:393` 第 5 条已是此格式）。
- `lead/layer_identity_20261109/LAYER_IDENTITY.md:393`（范式原文，实读核验）：
  > 5. **集合恒等只能作描述**：任何 `A==B` 必须声明「本批语料 / 本谓词 SHA / 本 tokens / 本换行口径」，并给「什么输入会破」的构造或实跑反例；**且必须写对等价式** `A=B ⟺ P(r12|r10&r13)=1`（§3.0 修正①）。
- `TAUTOLOGY_AUDIT.md:254-271`（§3.1 五问 + 一句话判据）：其中第 4 问给出依据四值分类（`:263-266` 逐字「(i) 纯逻辑/定义 ⇒ **重言式**；(ii) 代码级不变量（`file:line` + 全称证明）⇒ **实质条件·全称已证**；(iii) 本批语料统计（给 N、SHA、CI）⇒ **实质条件·仅 N 行观测**；(iv) 什么都没有 ⇒ **未验**」），是本门禁 Q3 的直接来源。
- `TAUTOLOGY_AUDIT.md:437-461`（§4.3 S1–S16 判定表）：三关 9 案例的期望全部取自该表（S1 `:446` / S2 `:447` / S3 `:448` / S4 `:449` / S5 `:450` / S7 `:452` / S8 `:453` / S10 `:455` / S12 `:457`）。

### 1.2 边界：只检测、不改写

- **不改写**：实现员与本件均未写任何被检 `.md`。证据：编排方【编排方指纹】11 件（含两件台账、六个审计目录的代表件、`_gp_regression_out.json`、两个谓词脚本）在本会话开头与收尾两轮 `python -I -X utf8 _eqg_fp.py` 实跑均 `INSPECTED_ALL_MATCH = True` / `FINAL_MATCH = True`（每件逐字 `OK <path> <sha256> <bytes>`，11/11 与编排方基线全等）。注意 11 件基线中属「扫描 15 件 `.md`」的只有 6 件（§1.3）；其余 9 件被扫 `.md` 无外部基线，其未变性只有检测器两轮实跑自记 SHA 一致的**弱证据**（如实记，见 §6.6）。
- **不拒件**：输出只落写域 `_eq_*_out.json` 供人工复核，不接任何自动拒绝动作（理由见 §6.3）。
- **不是生成时断言**：`TAUTOLOGY_AUDIT.md:547-549` §5.4 第 6 条的「负例哨兵（生成时禁用串断言）」**仍未实装**（逐字「**如实：两处均记『仍是提案、未实装』**，本任务不改脚本」）；本门禁实装的是其**成件后**的互补环节（§6.3）。
- **零真机零采样**：全部脚本只 `hashlib` / `re` / `json` / `pathlib` / `statistics` 纯文本处理；逐文件可查（8 件 `_eq_*` + 5 件 `_eqg_*`）。
- **不 commit / push**：HEAD 前后两查均 `2657458`，写域 untracked。

### 1.3 扫描范围（含复核更正，本件代码级复验）

`_eq_full_run.py:35-44` 的 `READ_DIRS` = 8 个只读目录，`python -I -X utf8 _eqg_counts.py` 实跑输出 `scope.md_files` = **15 件 `.md`**（逐字）：

```
lead/comparability_20261109/_cmp_AUDIT_20261109.md
lead/comparability_20261109/COMPARABILITY_AUDIT.md
lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md
lead/gate_pipeline_20261109/_gp_DESIGN.md
lead/gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md
lead/keff_calc_20261109/_ke_REPORT.md
lead/keff_calc_20261109/KEFF_CALC.md
lead/layer_identity_20261109/_li_LAYER_IDENTITY_PROOF_20261109.md
lead/layer_identity_20261109/LAYER_IDENTITY.md
lead/metric_audit_20261109/_ma_METRIC_AUDIT.md
lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md
lead/score_decomp_20261109/_sd_report.md
lead/score_decomp_20261109/SCORE_DECOMP.md
lead/tautology_audit_20261109/_ta_TAUTOLOGY_AUDIT_20261109.md
lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md
```

★ **复核员缺陷①的更正（本件实跑坐实）**：实现员 `_eq_CONCLUSION.md:168-169`（边界清单第 10 条）称两件台账措辞「K2 一律跳过」——**失实**。台账 `lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md` 不在 `READ_DIRS`（`_eq_full_run.py:35-44` 实读），也不在 15 件清单（我方复算 `PENDING in md_files? False / GOAL_THREE in md_files? False`）；即**台账从未被扫描，K2 从未在台账上运行**。正确表述是「不在扫描范围、从未被检测」。我方实测词频：`count[恒等] in lead/PENDING_DECISIONS.md = 0`、`in lead/GOAL_THREE_TARGETS_20261018.md = 49`（出现次数；按行计为 **46 行**，与 `TAUTOLOGY_AUDIT.md:609` 逐字「`GOAL` 含 `恒等` 的行 46 行经逐行核属别论域」一致——49 为次数、46 为行数，两者不矛盾）。若纳入扫描会得到什么结论，**未验**（从未运行，见 §6.6）。

---

## 2 ★ 判据形式（恒等类断言的可识别形态清单、合格两段式定义、F1/F2/F3）

### 2.0 总注：形态是触发条件，不是违规判定

命中 M1–M5 只使一行成为**候选断言锚点**；违规与否由 §2.2/§2.3 在窗口上判定；判不了就 SKIP/UNDECIDABLE（§3.3）。检测器只读**字面形态与作者显式标签**，不替作者推断语义——依据是 `TAUTOLOGY_AUDIT.md:270-271` 的一句话判据（「*把等号两边定义展开后，若其中一半能在不读任何数据、不读任何代码的情况下只靠逻辑连接词就证明，那一半是重言式*」）检测器无法自行执行证明，故只认作者写下的标签。

### 2.1 形态清单 M1–M5（代码实况：24 个子形态）

★ **计数仲裁（本件新发现，复核员未点名）**：`python -I -X utf8 _eqg_counts.py` 实跑 `importlib` 载入检测器后输出 `M1 n_sub = 4 / M2 n_sub = 5 / M3 n_sub = 4 / M4 n_sub = 7 / M5 n_sub = 4 / ALL_M_total = 24`。而 `_eq_DESIGN.md:87` 逐字写「**形态合计**：M1(4 子) + M2(5 子) + M3(4 子) + M4(5 子) + M5(4 子) = 22 个逐字匹配串族」，实现员回件亦写「= 22 个逐字匹配族」但其分组（M4 集合断言 7 子）求和实为 24。根因：`_eq_detector.py:59-62` 注释标明 `M4f_恒真兜底`（「S12 真实形态：SCORE_DECOMP.md:233,235 逐字」）与 `M4g_取等`（「S7 真实形态：KEFF_CALC.md:262 逐字」）是三关修正时**补入**的，DESIGN §1 的 M4 表（只有 M4a–M4e 五行）与合计行未同步更新。**代码真值 = 24**；22 是文档滞留值。此为文档-代码漂移，无功能影响，登记不改文档。

各子形态与真实 file:line（原文行均为本会话 `_eqg_lines.py` 实读，逐字；下表「原文行」节选）：

**M1 显式等式 / 等价符号**（`_eq_detector.py:31-36`）

| 子形态 | 匹配串（正则族） | 真实 file:line | 命中原文行（节选） |
|---|---|---|---|
| M1a `A=B` | `A\s*=\s*B`、`A==B` | `LAYER_IDENTITY.md:128` | 「**正确等价式**：`A = B ⟺ P(r12=PASS \| r10=PASS & n13=PASS) = 1`。`A=B` 与 `P(r12=PASS\|n13=PASS)=1` **不是同一命题**；二者在 74 行上同真，靠的正是 `cells_r10C_n13P_r12C = 0` 这一额外巧合」 |
| M1b `⟺` | `⟺` | `LAYER_IDENTITY.md:126` | 「`A ⊆ B` 重言式；`B ⊆ A` ⟺ 不存在格 `(r10=P & n13=P & r12=C)` ⟺ **`P(r12=PASS \| r10=PASS & n13=PASS) = 1`**」 |
| M1c `⇔` | `⇔` | `GOAL_THREE_TARGETS_20261018.md:9200` | 「⇒ **「except_post 与基线不同 ⇔ 本趟新写」隐式成立**（这才是原设计能工作的原因）；」（台账行，别论域，由 K 系判据处置） |
| M1d `⊆` | `A\s*⊆\s*B`、`B\s*⊆\s*A`、`⊆` | `LAYER_IDENTITY.md:104` | 「`A ⊆ B` 是去掉一个合取项的重言式；非平凡方向 `B ⊆ A` 只排除 `(r10=PASS & n13=PASS & r12=CATCH)`」 |

**M2 中文等价式**（`_eq_detector.py:38-44`）

| 子形态 | 匹配串 | 真实 file:line | 命中原文行（节选） |
|---|---|---|---|
| M2a `等价于` | `等价于` | `TAUTOLOGY_AUDIT.md:617` | 「`A = B∩{r12=PASS}` 的**定义重言式、零信息量**；非平凡半 `B⊆A` 等价于」 |
| M2b `同一个命题` | `同一个命题` | `_li_LAYER_IDENTITY_PROOF_20261109.md:146` | 「`B ⊆ A` **当且仅当**不存在 `n13=PASS & r12=CATCH` 的行 —— 这与「`P(r12=PASS\|n13=PASS)=1`」是**同一个命题**的两写法」（该等价性断言已被上游判错，`LAYER_IDENTITY.md:122` 修正①） |
| M2c `同一命题` | `同一命题` | `LAYER_IDENTITY.md:122` | 「**修正①（要害）：「`B⊆A ⟺ 无 n13=PASS&r12=CATCH 行 ⟺ P(r12=PASS\|n13=PASS)=1 是同一命题的重写」不成立。**」 |
| M2d `不是近似` | `不是近似`、`近似省一层` | `METRIC_CONVENTION_AUDIT.md:104` | 「根因不是「R12 数值接近 1 所以近似省一层」，而是 **R12 不是独立证据根**：」 |
| M2e `恰好等于` 等 | `恰好等于`、`完全相同`、`逐一相同`、`逐 id` | `METRIC_CONVENTION_AUDIT.md:108` | 「`{r10=PASS 且 n13=PASS}` 的 18 个 id **恰好等于** `{r10=r12=n13=PASS}` 的 18 个 id」 |

★ M2d 注记（复核员缺陷⑤，本件代码级复验）：`_eq_DESIGN.md:43-49` 称「检测器按字面串 `不是近似` 匹配，故 `:104` 本身不会被 M2d 触发」——**与代码不符**：代码 M2d = `['不是近似', '近似省一层']`（`python -I -X utf8 _eqg_counts.py` 输出 `M2d_patterns = ['不是近似', '近似省一层']`），而 `:104` 逐字含「近似省一层」，故**会**被锚定。我方取证：三关存盘件 G2a 行 `matched_strings = ['近似省一层']`（`_eq_three_gates_out.json` 复算输出）。终判无功能影响（`:104` 实际 `SUBSTANTIVE_OK`，见 §4 G2a），属文档-代码不一致，登记不改文档。

**M3 强度标签**（`_eq_detector.py:46-51`；本门禁核心风险信号）

| 子形态 | 匹配串 | 真实 file:line | 命中原文行（节选） |
|---|---|---|---|
| M3a `决定性` | `决定性` | `METRIC_CONVENTION_AUDIT.md:108` | 「3. **决定性集合等式**：实跑命令 2 输出 `all3PASS= 18 expect=CATCH= 3`、`2layerPASS= 18 set equal? True`，即 …」 |
| M3b `定理` | `定理` | `KEFF_CALC.md:314` | 「⇒ `P(r12=PASS\|n13=PASS)=38/38=1.000` 是**本 74 行上的观测值，不是精确 1.000、不是定理**。」 |
| M3c `已证` | `已证` | `TAUTOLOGY_AUDIT.md:447` | 「\| S2 \| `METRIC_CONVENTION_AUDIT.md:104` \| … \| **实质条件·全称已证（正确否定句）** \| …」 |
| M3d `恒等` | `恒等` | `COMPARABILITY_AUDIT.md:158` | 「chain_changed=18 \| unresolved_changed=18 \| 集合恒等? True」 |

★ `恒等` 是最宽形态：`TAUTOLOGY_AUDIT.md:609` 自记 GOAL 台账 46 行属别论域（本件实测 46 行/49 次，§1.3）。故 M3d 单独命中不作断言升级，须与观测证据/等式标记共同成立或走 K2/K1 跳过（`_eq_DESIGN.md:59-61` 同义注明）。

**M4 集合断言**（`_eq_detector.py:53-63`，7 子）

| 子形态 | 匹配串 | 真实 file:line | 命中原文行（节选） |
|---|---|---|---|
| M4a `18 个 id` | `18 个 id`、`18个id` | `METRIC_CONVENTION_AUDIT.md:108` | （同 M2e 行） |
| M4b `only_A/only_B` | `only_A`、`only_B` | `LAYER_IDENTITY.md:52` | 「输出：`A_n 18 B_n 18 A==B True only_A [] only_B []`；字段定义见 …」（实跑输出回显行） |
| M4c `set equal? True` | `set equal\? True`、`sets equal\? True`、`A==B True` | `METRIC_CONVENTION_AUDIT.md:108` | （逐字 `2layerPASS= 18 set equal? True`；被检文档为单数 `set`，检测器含单复数变体） |
| M4d `集合恒等? True` | `集合恒等\? True`、`集合恒等` | `COMPARABILITY_AUDIT.md:158` | （同 M3d 行） |
| M4e `完全相同/逐 id` | `完全相同`、`逐 id 比对通过` | `_li_LAYER_IDENTITY_PROOF_20261109.md:78` | 「### (a) 两个集合真的完全相同，逐 id 比对通过」 |
| M4f `恒真兜底` | `恒真兜底`、`恒真`、`恒 CATCH 兜底`、`必然命中` | `SCORE_DECOMP.md:235` | 「是**恒真兜底在正类样本上的必然命中，信息量 = 0**，不算算法改进」（S12 正面样板，`TAUTOLOGY_AUDIT.md:457`） |
| M4g `取等` | `≤\s*min q_i`、`取等`、`恰取`、`Fréchet`、`Frechet` | `KEFF_CALC.md:262` | 「`P(allPASS|E) ≤ min q_i = min(0.487179, 0.897436, 0.076923) = 0.076923`」（S7 数学定理 + 实测取等，`TAUTOLOGY_AUDIT.md:452`） |

**M5 观测数值 / 统计形态**（`_eq_detector.py:65-73`；F3 的「仅 N 行观测」侧）

| 子形态 | 匹配串 | 真实 file:line | 命中原文行（节选） |
|---|---|---|---|
| M5a `38/38` | `38/38` | `METRIC_CONVENTION_AUDIT.md:107` | 「实跑命令 2 输出 `n13=PASS n= 38 r12=CATCH among them= 0` ⇒ `P(r12=PASS\|n13=PASS)=38/38=1`（`CHAIN_VS_SINGLE.md:206` 亦记 38/38=1.000）」 |
| M5b `0 bit` | `0 bit`、`0\.0 bit` | `EVIDENCE_INDEPENDENCE.md:149` | 「- **R12 增量判别力 = 0 bit**：`P(r12=PASS \| n13=PASS) = 38/38 = 1.000`（`_ei_07_final_out.json:95`），加 R12 后 `n_pass=18 → 18`…」 |
| M5c `本 N 行` 等 | `本 74 行`、`本批语料`、`观测`、`样本巧合`、`train=test`、`95%` 等 | `KEFF_CALC.md:340` | 「`n13=PASS` 共存。本 74 行内 0 行，但**机制存在 ⇒ 1.000 是样本巧合 + 契约巧合，不是恒等式**。」 |
| M5d `实跑输出` | `实跑命令`、`输出`、`set equal\? True`、`38/74`、`22→0`、`chain_changed=18` 等 | `METRIC_CONVENTION_AUDIT.md:108` | （逐字 `实跑命令 2 输出`） |

### 2.2 合格两段式声明的定义（Q1–Q4；重言半 / 实质半 / forbidden 格）

设 `W` = 断言锚点所在段落窗口（定义见 §3.2）。**合格 = Q1 ∧ Q2 ∧ Q3 ∧ Q4(条件性)**，任一不满足落入 §2.3 失败型（实现：`_eq_detector.py:342-396`）。

**Q1 重言半写清了**——窗口同时出现（i）重言标签（`Q1_LABEL`：`重言式/重言半/定义重言式/逻辑重言式/零信息量/恒真兜底/恒真`，`_eq_detector.py:80-81`）与（ii）结构展开（`Q1_STRUCT`：`A = B∩ / 去掉一个合取项 / 合取项 / A ⊆ B / 定义式 / X=X / 代回 / 8 格 / 穷举 / 合取消去 / 恒 CATCH 兜底 / 必然命中`，`:84-86`）。类别判定则**只认锚点行自身**的显式标签（`TAUT_LABEL_ON_LINE`，`:83`；`taut_line = 锚点行有标签 ∧ 窗内有结构展开`，`:292`）——「类别只认作者在锚点行写下的显式重言标签」，不猜语义。真实合格例：`LAYER_IDENTITY.md:104`（标签「重言式」+ 展开「`A ⊆ B`…合取项」同现）、`_li_LAYER_IDENTITY_PROOF_20261109.md:125`（「`A ⊆ B` 是**去掉一个合取项的逻辑重言式**」）。只写「重言式」三个字而无展开不算 Q1 通过（`_eq_DESIGN.md:118`：「★ 只写 `重言式` 三个字而不给展开，不算 Q1 通过：检测器须能自证，宁可报『无法判定』」）。

**Q2 实质半写清了**——窗口出现 `Q2` 标记任一（`_eq_detector.py:89-91`）：`B ⊆ A / 实质半 / 非平凡 / forbidden / 禁止格 / 不存在格 / 额外排除 / 破口 / 反例 / 构造 / 什么输入会破 / 分叉格 / 破坏它的输入 / X1/X2/X3`。真实合格例：`LAYER_IDENTITY.md:104` 后半逐字「非平凡方向 `B ⊆ A` 只排除 `(r10=PASS & n13=PASS & r12=CATCH)`」；`TAUTOLOGY_AUDIT.md:617-618` 逐字「非平凡半 `B⊆A` 等价于 `(r10=P, n13=P, r12=C)` 格为空，74 行上该格为 0，但 X1/X2/X3 已构造出落在该格的输入」。

**forbidden 格**：指非平凡方向 `B ⊆ A` 的否定格。本库实例即 `(r10=PASS & n13=PASS & r12=CATCH)`（`LAYER_IDENTITY.md:104/126` 逐字「不存在格 `(r10=P & n13=P & r12=C)`」）；`P(r12=PASS|n13=PASS)=1` 额外排除的 `(r10=C & n13=P & r12=C)` 是**另一个**格（`LAYER_IDENTITY.md:127` 逐字「它**还额外排除** `(r10=C & n13=P & r12=C)`。该格与 `B⊆A` 无关」）——检测器**判不了方向对错**：`TAUTOLOGY_AUDIT.md:590` 逐字记上游曾把 `F(A⊆B) = B∧¬A` 与 `F(B⊆A)` 写成同一个集合（★2），本门禁只查「有没有 forbidden 标记」，不验方向（`_eq_DESIGN.md:277-278` 同义自认）。

**Q3 依据属四类之一且被显式写出**——依据分类逐字来自 `TAUTOLOGY_AUDIT.md:263-266`（§2.0 已引）。实现三组串：`BASIS_LOGIC`（纯逻辑/定义式/合取消去/重言式/恒真兜底等）、`BASIS_CODE`（依赖图/代码级/`_g7_predicates.py`/`_gp_pipeline.py`/`file:line`/数学定理/Fréchet/源码蕴含等）、`BASIS_OBS`（本 74 行/本批语料/train=test/SHA256/95%/观测/样本巧合/实跑等）（`_eq_detector.py:94-103`）。★ 窗口里若只有数值而无任一标记，判「依据缺失」（F2），**绝不按数值反推类别**（`_eq_DESIGN.md:137-139`）。

**Q4 范围声明在了**——`SCOPE` 串表（`_eq_detector.py:106-111`）：`本 74 行 / 本批 74 行 / 本批语料 / 仅 N 行 / 仅 74 行 / 样本内 / train=test / 观测值 / 观测等式 / 反事实 / 条件行 / 未验 / 本谓词 SHA / 本 tokens / 换行口径 / 契约 / 样本巧合 / 不是定理 / 不是恒等式 / 不是逻辑恒等式 / 描述性 / 95% / 上界 / CI / 受限 / 在 74 行上 / 74 行上 / 巧合 / 同真` 等 30 形态（`python -I -X utf8 _eqg_counts.py` 输出 `SCOPE_n = 30`）。依据为 (iii)「本批 N 行」时 Q4 **强制**；依据为 (i)(ii) 时可省，但强度标签不得裸接数值（F3 同行判据，§2.3）。真实合格例：`LAYER_IDENTITY.md:365` 逐字「但这**只是本批语料的观测等式**」+ 契约三项 + X1/X2/X3；`KEFF_CALC.md:314` 逐字「是**本 74 行上的观测值，不是精确 1.000、不是定理**」。

### 2.3 三种失败型（优先级 F3 > F2 > F1）+ 类别 + skip

记 `E`＝显式等式/集合断言标记（整窗）、`E_eq`＝**严格等式声明**（F1 专用串表 `E_EQ_STRICT`，`_eq_detector.py:144-148`，20 形态）、`I`＝强度（`INTENSITY` 8 形态 + `UNIVERSAL_CLAIM` 7 形态，经锚点行纠偏语境 `CORRECTION` 否定后熄灭，`:123-128/157-160/267-270`）、`O`＝观测证据（`OBS_EVIDENCE`，`:114-118`）、`R_same_line`＝**锚点行自身**的范围声明、`T/S/B` ＝重言半/实质半/依据（整窗）。检出优先级 **F3 > F2 > F1**，一条断言只报最重的失败型，`all_missing` 保留全部缺失项（`:342-396`）。

**F1 只写等式、两半全缺**：`E_eq ∧ ¬T ∧ ¬S`（`:362`）。缺什么：「Q1 重言半 + Q2 实质半两半全缺；无 A⊆B / B⊆A 拆分」。★ 只施加于**严格等式声明**形态——排除两类真实质条件：(1) S2「不是近似省一层」是正确否定句（`TAUTOLOGY_AUDIT.md:447` 逐字「**该句本身正确，不列入撤回对象**」），(2) S7 Fréchet `≤ min q_i` 是数学不等式 + 实测取等（`KEFF_CALC.md:262`）——代码注释 `:137-143` 逐字登记此设计。真实锚点：`COMPARABILITY_AUDIT.md:158` 逐字「chain_changed=18 | unresolved_changed=18 | 集合恒等? True」（裸集合等式；`TAUTOLOGY_AUDIT.md:455` S10 判「措辞未升级为定理，风险低」与 F1 格式缺失不矛盾，§6.3 P4）。存盘全量 F1 = 57 条（§5.1）。

**F2 两半齐全但实质半缺依据、或依据是本批 N 行却无范围**：`declares_two_stage (T∧S) ∧ ¬logic_self_based ∧ (¬B ∨ (B_obs ∧ ¬R))`（`:346-361`）。★ 只追究「确实写了两段式」的声明：真重言式/正确等价式/Fréchet 定理等**单一命题**依据自足，不因窗口无「依据=」而报 F2（否则关一 G1a/G1b、关二 G2b 误报——实现员自记的修正，`_eq_CONCLUSION.md:51`）。缺什么：按子型记「Q2 实质半缺失 / Q3 依据缺失 / Q4 仅 N 行观测缺范围声明」。存盘全量 F2 = 5 条，落点（本件 `_eq_full_out.json` 复算逐条）：`_ta_TAUTOLOGY_AUDIT_20261109.md:517,520`（missing= Q3 依据缺失；表格行）、`TAUTOLOGY_AUDIT.md:278,280,281`（missing= Q4 仅 N 行观测缺范围声明；§3.1 五问的 N1/N3/N4 示例表行——这三条同样呈「清单/示例行」形态，属 §6.3 P1 白名单议题，抽样未覆盖，如实记）。★ DESIGN §3 引作 F2「真实锚点」的 `_li_LAYER_IDENTITY_PROOF_20261109.md:146` 实际存盘落桶为 **tautology_ok / TAUTOLOGY_OK**（本件 `python -I -X utf8 -c "<in-memory scan_file>"` 实跑输出：`bucket= tautology_ok verdict= TAUTOLOGY_OK T= True S= True B= True B_obs= True R= True`——其窗口含指向上游正确范围的引文），即 DESIGN §3 该处引例与存盘结果不符，登记不改文档；F2 的真实落点以上面 5 条存盘 finding 为准。

**F3 观测直接接强度标签、中间无范围声明**：`I ∧ O ∧ ¬R_same_line`（`:359`）。强度侧含显式标签（`决定性/定理/已证/恒成立/恒等式/逻辑恒等/结构性定理/必相等`）与全称口吻（`= 0 bit / = 1.000 / 38/38=1 / 增量判别力 / 不提供任何新信息 / 恒 PASS`）；范围 R **只看锚点行自身**——「中间」= 同一行，理由：用整窗/±2 取 R 会把 8 行外或邻行的无关「反事实/未验」误当范围，把真 F3 洗掉（代码注释 `:259-263` 逐字记 `METRIC_CONVENTION_AUDIT.md:110` 的「反事实基线期望」险些洗掉 `:108` 的实例）。真实锚点三处（关三）：`METRIC_CONVENTION_AUDIT.md:108`（S1）、`EVIDENCE_INDEPENDENCE.md:149`（S5）、`METRIC_CONVENTION_AUDIT.md:107`（S8）。负控：`KEFF_CALC.md:314` 同行有范围 + 明确否定 ⇒ `CORRECTLY_SCOPED` 不报（§3.4 N1）。存盘全量 F3 = 150 条（§5.1）。

**类别与 skip**：每条锚点另产类别 `TAUTOLOGY`（锚点行显式重言标签 + 窗内结构展开）/ `SUBSTANTIVE` / `UNDECIDABLE`（`:288-298`）；skip 判据 K1–K6 见 §3.3。**宁可报「无法判定」也不许猜**是全程铁律：145 条 UNDECIDABLE + 346 条 SKIP 均不产 finding、全部保留 `file:line` + 原文行（§5.1）。

---

## 3 ★ 实现（检测器代码可粘贴、段落窗口/状态机、「无法判定」判据、自检实跑输出）

### 3.1 检测器代码（`_eq_detector.py` 全文粘贴，SHA256 = f29a34b5…472 / 29795 字节，581 行；收尾指纹实算全等）

```python
# -*- coding: utf-8 -*-
"""
_eq_detector.py — 「两段式等式声明」门禁检测器（只读、零真机、零采样代码）

输入：一份 .md（绝对路径）；输出：findings 列表（JSON 可序列化）。
每条 finding 含：file:line / 原文行 / 失败型 F1|F2|F3 / 缺什么（missing + all_missing）。
另给 category（TAUTOLOGY / SUBSTANTIVE / UNDECIDABLE）与 skip 计数。
任何一条命中都附 file:line 与命中的原文行（evidence_lines / evidence_matches）。

判据形式定义见同目录 _eq_DESIGN.md。
运行： python -I -X utf8 <本文件> --selftest
       python -I -X utf8 <本文件> --scan <绝对 .md 路径> [--out <绝对 json 路径>]
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
from typing import Any

# ---------------------------------------------------------------------------
# 常量：全部为逐字串，来源于本会话实读的真实 file:line（见 _eq_DESIGN.md §1）
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
WINDOW_RADIUS = 8   # 见 _eq_DESIGN.md §4：本语料实测最大跨行距离 = 8
LOCAL_RADIUS = 2    # 锚点局部半径，见 classify_window 注释（强度/范围邻接判据）

# M1 显式等式 / 等价符号
M1 = {
    "M1a_A=B": [r"A\s*=\s*B", r"A==B"],
    "M1b_⟺": [r"⟺"],
    "M1c_⇔": [r"⇔"],
    "M1d_⊆": [r"A\s*⊆\s*B", r"B\s*⊆\s*A", r"⊆"],
}
# M2 中文等价式
M2 = {
    "M2a_等价于": [r"等价于"],
    "M2b_同一个命题": [r"同一个命题"],
    "M2c_同一命题": [r"同一命题"],
    "M2d_不是近似": [r"不是近似", r"近似省一层"],
    "M2e_恰好等于": [r"恰好等于", r"完全相同", r"逐一相同", r"逐 id"],
}
# M3 强度标签
M3 = {
    "M3a_决定性": [r"决定性"],
    "M3b_定理": [r"定理"],
    "M3c_已证": [r"已证"],
    "M3d_恒等": [r"恒等"],
}
# M4 集合断言（按逐字形态，含单复数变体；见 _eq_DESIGN.md §1 注）
M4 = {
    "M4a_18个id": [r"18 个 id", r"18个id"],
    "M4b_only_A_B": [r"only_A", r"only_B"],
    "M4c_set_equal": [r"set equal\? True", r"sets equal\? True", r"A==B True"],
    "M4d_集合恒等": [r"集合恒等\? True", r"集合恒等"],
    "M4e_完全相同": [r"完全相同", r"逐 id 比对通过"],
    # S12 真实形态：SCORE_DECOMP.md:233,235 逐字「恒真兜底」
    "M4f_恒真兜底": [r"恒真兜底", r"恒真", r"恒 CATCH 兜底", r"必然命中"],
    # S7 真实形态：KEFF_CALC.md:262 逐字「≤ min q_i」/「取等」
    "M4g_取等": [r"≤\s*min q_i", r"取等", r"恰取", r"Fréchet", r"Frechet"],
}
# M5 观测数值 / 统计形态
M5 = {
    "M5a_38/38": [r"38/38"],
    "M5b_0bit": [r"0 bit", r"0\.0 bit"],
    "M5c_本N行": [r"本 74 行", r"本批 74 行", r"本批语料", r"仅 N 行", r"仅 74 行",
                r"N 74", r"74 行", r"观测", r"样本巧合", r"train=test", r"95%"],
    "M5d_实跑输出": [r"实跑命令", r"输出", r"sets equal\? True", r"set equal\? True",
                 r"集合恒等\? True", r"n13=PASS n= 38", r"38/74", r"22→0",
                 r"chain_changed=18", r"unresolved_changed=18", r"一致性?率"],
}

ALL_M: dict[str, list[str]] = {}
for _d in (M1, M2, M3, M4, M5):
    ALL_M.update(_d)

# Q1 重言半：标签（须在锚点行或窗内）+ 结构展开
Q1_LABEL = [r"重言式", r"重言半", r"定义重言式", r"逻辑重言式", r"零信息量",
            r"恒真兜底", r"恒真", r"重言"]
# ★ 锚点行自身的重言标签：类别判定的唯一依据（只读作者显式标签，不猜语义）
TAUT_LABEL_ON_LINE = [r"重言式", r"重言半", r"恒真兜底", r"零信息量", r"恒真"]
Q1_STRUCT = [r"A\s*=\s*B∩", r"A=B∩", r"去掉一个合取项", r"合取项", r"A\s*⊆\s*B",
             r"定义式", r"X=X", r"代回", r"8 格", r"8 种真值格局", r"穷举",
             r"合取消去", r"恒 CATCH 兜底", r"必然命中"]

# Q2 实质半
Q2 = [r"B\s*⊆\s*A", r"实质半", r"非平凡", r"forbidden", r"禁止格", r"不存在格",
      r"额外排除", r"破口", r"反例", r"构造", r"什么输入会破", r"分叉格",
      r"破坏它的输入", r"X1/X2/X3", r"X1", r"forbidden sets"]

# Q3 依据四类（TAUTOLOGY_AUDIT.md:263-266）
BASIS_LOGIC = [r"纯逻辑", r"定义式", r"代回 X=X", r"合取消去", r"逻辑连接词",
               r"重言式", r"逻辑重言式", r"定义重言式", r"零信息量",
               r"恒真兜底", r"合取项"]           # 纯逻辑重言式自身即依据
BASIS_CODE = [r"依赖图", r"代码级", r"_g7_predicates\.py", r"_gp_pipeline\.py",
              r"_ei_n13_predicates_src\.py", r"file:line", r"数学定理", r"Fréchet",
              r"Frechet", r"源码蕴含", r"因果图", r"_v12_rule\.py", r"定理"]
BASIS_OBS = [r"本 74 行", r"本批语料", r"本批 74 行", r"仅 N 行", r"仅 74 行",
             r"N 74", r"74 行", r"train=test", r"SHA256", r"95%", r"观测",
             r"样本巧合", r"实跑", r"实测", r"样本内", r"本会话实跑"]
BASIS_ANY = BASIS_LOGIC + BASIS_CODE + BASIS_OBS

# Q4 范围声明（含本会话实读补入的逐字形态：LAYER_IDENTITY.md:128「在 74 行上同真」「额外巧合」）
SCOPE = [r"本 74 行", r"本批 74 行", r"本批语料", r"仅 N 行", r"仅 74 行", r"样本内",
         r"train=test", r"观测值", r"观测等式", r"反事实", r"条件行", r"未验",
         r"本谓词 SHA", r"本 tokens", r"换行口径", r"契约", r"样本巧合",
         r"不是定理", r"不是恒等式", r"不是逻辑恒等式", r"描述性", r"95%",
         r"上界", r"CI", r"受限", r"在 74 行上", r"74 行上", r"巧合", r"同真",
         r"样本巧合 \+ 契约巧合"]

# 观测证据标记 O（F3 用）：M5 观测数值 + 显式集合相等输出
OBS_EVIDENCE = [r"38/38", r"0 bit", r"0\.0 bit", r"1\.000", r"set equal\? True",
                r"sets equal\? True", r"集合恒等\? True", r"18 个 id", r"only_A",
                r"only_B", r"实跑命令", r"n13=PASS n= 38", r"38/74", r"22→0",
                r"chain_changed=18", r"unresolved_changed=18", r"一致性?率",
                r"取等", r"实测"]

# 强度标签 I（F3 用）。★ 不含泛化「必然 / 全称」：
# SCORE_DECOMP.md:235 逐字「恒真兜底在正类样本上的必然命中」里的「必然」是
# 对兜底行为的描述，不是把观测等式升级为定理；把它当 I 会误报 S12（关一）。
INTENSITY = [r"决定性", r"定理", r"已证", r"恒成立", r"恒等式",
             r"逻辑恒等", r"结构性定理", r"必相等"]
# 全称口吻（S5「R12 增量判别力 = 0 bit」全称、S8「38/38」全称）：
# 数值/零增量断言本身若无「本 N 行」限定即隐含全称，视作强度侧信号。
UNIVERSAL_CLAIM = [r"=\s*0 bit", r"0 bit", r"=\s*1\.000", r"38/38=1",
                   r"增量判别力", r"不提供任何新信息", r"恒 PASS"]

# 显式等式 / 等价 / 集合断言 E（F1 / skip 用）
E_MARKERS = [r"A\s*=\s*B", r"A==B", r"⟺", r"⇔", r"⊆", r"等价于", r"同一个命题",
             r"同一命题", r"不是近似", r"近似省一层", r"恰好等于", r"完全相同",
             r"逐一相同", r"逐 id", r"only_A", r"only_B", r"set equal\? True",
             r"sets equal\? True", r"集合恒等\? True", r"A==B True", r"18 个 id",
             r"恒真兜底", r"取等", r"≤\s*min q_i"]

# ★ F1 专用的「严格等式声明」：只有这些形态才触发「两段式声明」义务。
#   排除两类真实质条件（关二要求不误报）：
#   (1) S2「不是近似省一层」是**正确否定句**（TAUTOLOGY_AUDIT.md:447 逐字
#       「本身正确，不列入撤回对象」），它没有断言等式，不需拆两半；
#   (2) S7「P(allPASS|E) ≤ min q_i」是 Fréchet 不等式 + 数值取等
#       （KEFF_CALC.md:262），是数学定理，不是 A=B 型集合恒等。
#   检测器只读形态，不替作者推断「这算不算等式」⇒ 宁可少报也不猜。
E_EQ_STRICT = [r"A\s*=\s*B", r"A==B", r"⟺", r"⇔", r"⊆", r"等价于",
               r"同一个命题", r"同一命题", r"恰好等于", r"完全相同",
               r"逐一相同", r"逐 id", r"only_A", r"only_B",
               r"set equal\? True", r"sets equal\? True", r"集合恒等\? True",
               r"A==B True", r"18 个 id", r"恒真兜底"]

# 整改意见 / 纯转述（skip K5）
QUOTE_OR_REVIEW = [r"→\s*改", r"须撤回", r"判错置", r"须修正措辞", r"应改为",
                   r"改「", r"撤回", r"须降级", r"须删除", r"删除「"]

# 「纠偏语境」：强度标签被明确否定（不是定理 / 不是恒等式 / 未验 / 须撤回 等）。
# ★ 不含泛化「不是 / 不成立」：S2 的「不是近似省一层」是**正确否定句**
#   （TAUTOLOGY_AUDIT.md:447 逐字判「本身正确，不列入撤回对象」）。
CORRECTION = [r"不是定理", r"不是恒等式", r"不是逻辑恒等式", r"不是精确 1\.000",
              r"是否定理", r"⇒\s*未验", r"未验", r"须撤回", r"须降级",
              r"须修正措辞", r"强度夸大", r"判错置", r"不得读作",
              r"仍是提案", r"现状：未实装", r"不是结构性定理"]
# 提问句（「是否定理：未验」）不是断言，按 K3 跳过，不作「正确限定」
QUESTION = [r"是否", r"是否定理", r"\?\s*$", r"？\s*$"]

HARD_BOUNDARY = re.compile(r"^\s*$|^#{1,6}\s|^-{3,}\s*$|^\s*```")


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------
def _hits(text: str, pats: list[str]) -> list[str]:
    out: list[str] = []
    for p in pats:
        m = re.search(p, text)
        if m and m.group(0) not in out:
            out.append(m.group(0))
    return out


def _has(text: str, pats: list[str]) -> bool:
    return any(re.search(p, text) for p in pats)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read_lines(path: pathlib.Path) -> tuple[list[str], str | None, int, str]:
    try:
        b = path.read_bytes()
        return b.decode("utf-8", errors="replace").split("\n"), None, len(b), sha256_bytes(b)
    except OSError as e:
        return [], f"read_error:{type(e).__name__}:{e}", 0, ""


def rel(path: pathlib.Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


# ---------------------------------------------------------------------------
# 段落窗口（状态机 SCAN → IN_WINDOW → EMIT/SKIP，见 _eq_DESIGN.md §4）
# ---------------------------------------------------------------------------
def build_segments(lines: list[str]) -> list[tuple[int, int]]:
    """硬边界：空行 / ^#{1,6}\\s / ^---+$ / 代码围栏。返回 1-based 闭区间。"""
    segs: list[tuple[int, int]] = []
    start = None
    for i, l in enumerate(lines, 1):
        if HARD_BOUNDARY.match(l):
            if start is not None:
                segs.append((start, i - 1))
                start = None
        else:
            if start is None:
                start = i
    if start is not None:
        segs.append((start, len(lines)))
    return [s for s in segs if s[0] <= s[1]]


def anchor_lines(lines: list[str]) -> dict[int, list[str]]:
    """{行号: 命中的 M 子形态名}；仅命中 M1–M5 的行成为候选断言锚点。"""
    out: dict[int, list[str]] = {}
    for i, l in enumerate(lines, 1):
        ms = [k for k, pats in ALL_M.items() if _has(l, pats)]
        if ms:
            out[i] = ms
    return out


def window_for(anchor: int, seg: tuple[int, int], lines: list[str]) -> tuple[int, int, list[str]]:
    """W = [anchor-R, anchor+R] ∩ 当前硬边界段落。"""
    lo = max(seg[0], anchor - WINDOW_RADIUS)
    hi = min(seg[1], anchor + WINDOW_RADIUS)
    return lo, hi, [lines[n - 1] for n in range(lo, hi + 1)]


# ---------------------------------------------------------------------------
# 核心判定
# ---------------------------------------------------------------------------
def classify_window(anchor: int, anchor_morphs: list[str], lo: int, hi: int,
                    wlines: list[str], lines: list[str]) -> dict[str, Any]:
    """对单个窗口产一条判定记录（finding / pass / tautology_ok / skip / undecidable）。"""
    wtext = "\n".join(wlines)
    atext = lines[anchor - 1]

    # 锚点局部窗口 ±LOCAL_RADIUS 行。本会话实跑量测「强度标签行 → 最近范围词」
    # 距离分布 0:288 / 1:90 / 2:86 / 3:61 / 4:22 ⇒ 85% 的真实已限定断言把范围
    # 写在 ±2 行内。强度 I 用局部窗口；F3 的范围 R 用**锚点行自身**（见下）。
    l_lo = max(lo, anchor - LOCAL_RADIUS)
    l_hi = min(hi, anchor + LOCAL_RADIUS)
    local_text = "\n".join(lines[n - 1] for n in range(l_lo, l_hi + 1))

    E = _has(wtext, E_MARKERS)
    E_eq = _has(wtext, E_EQ_STRICT)   # F1 义务只施加于严格等式声明
    O = _has(wtext, OBS_EVIDENCE)
    R = _has(wtext, SCOPE)
    # ★ F3 的「范围声明」必须在锚点行自身：任务 F3 定义是「把仅 N 行观测
    #   **直接接**强度标签，中间无范围声明」。「中间」= 同一行两者之间。
    #   用整窗/±2 取 R 会把 8 行之外或邻行的无关「反事实 / 未验」误当范围
    #   （本会话实跑：METRIC_CONVENTION_AUDIT.md:110 的「反事实基线期望」
    #   会让 :108 的 F3 被错误洗掉）。同行判据是可复核的字面判据，不是猜测。
    R_same_line = _has(atext, SCOPE)
    R_local = _has(local_text, SCOPE)

    I_raw = _has(local_text, INTENSITY)
    U_local = _has(local_text, UNIVERSAL_CLAIM)
    denial = _has(atext, CORRECTION)          # 纠偏语境只在锚点行自身判定
    I = (I_raw or U_local) and not denial
    I_hits = (_hits(atext, INTENSITY) or _hits(local_text, INTENSITY) or
              _hits(atext, UNIVERSAL_CLAIM))

    B = _has(wtext, BASIS_ANY)
    B_logic = _has(wtext, BASIS_LOGIC)
    B_code = _has(wtext, BASIS_CODE)
    B_obs = _has(wtext, BASIS_OBS)
    T = _has(wtext, Q1_LABEL) and _has(wtext, Q1_STRUCT)
    S = _has(wtext, Q2)

    non_obs_morphs = [k for k in anchor_morphs if not k.startswith("M5")]
    assertion_object = E or O or I_raw or U_local or bool(non_obs_morphs)
    # 纠偏语境（强度标签被明确否定/撤回）也是一条「断言对象」：
    # 它是关于该等式强度的正确限定，不是无关文本，不能按 K1/K3 跳过。
    if denial and R_same_line:
        assertion_object = True

    # ---- 类别判定：只读作者在该行写下的显式重言标签，不猜语义 ----
    # 上游一句话判据（TAUTOLOGY_AUDIT.md:270-271）：「能在不读任何数据、
    # 不读任何代码的情况下只靠逻辑连接词就证明，那一半是重言式」。
    # 检测器无法自行证明，故以作者显式标签为准；标签 + 结构展开同现才判 TAUTOLOGY。
    taut_line = _has(atext, TAUT_LABEL_ON_LINE) and _has(wtext, Q1_STRUCT)
    if taut_line:
        category = "TAUTOLOGY"
    elif assertion_object or I or O:
        category = "SUBSTANTIVE"
    else:
        category = "UNDECIDABLE"

    # ---- skip 判据 K1–K5（宁可报无法判定也不许猜）----
    skip_reason = None
    if _has(atext, QUESTION):
        skip_reason = "K3_question_not_assertion"
    elif denial and R_same_line:
        # 「不是定理 / 未验 / 须撤回」+ 同行范围 = 正确限定，不跳过、不报 F3
        skip_reason = None
    elif _has(atext, [r"恒等"]) and not E and not O and not I:
        skip_reason = "K2_ident_word_other_domain"
    elif I_raw and not E and not O:
        skip_reason = "K3_intensity_without_assertion_object"
    elif T and S and B_obs and _has(wtext, [r"全称定理", r"逻辑必然 = 是"]) and not R:
        skip_reason = "K4_conflict_scope_basis"
    elif _has(atext, QUOTE_OR_REVIEW) and not E and not O:
        skip_reason = "K5_pure_quotation"
    elif (not I) and (not E):
        # 任务 (c)：既无明显强度标签、又无显式等式 ⇒ 跳过而不是猜
        skip_reason = "K1_no_equality_no_intensity"

    base: dict[str, Any] = {
        "file": "",
        "file:line": f"FILE:{anchor}",
        "line": anchor,
        "text": atext,
        "window": [lo, hi],
        "window_lines": [f"FILE:{n}" for n in range(lo, hi + 1)],
        "morphs": anchor_morphs,
        "matched_strings": _hits(atext, [p for k in anchor_morphs for p in ALL_M[k]]),
        "flags": {
            "E": E, "E_eq": E_eq, "I_raw": I_raw, "I": I, "U_local": U_local, "O": O,
            "R": R, "R_local": R_local, "R_same_line": R_same_line,
            "B": B, "B_logic": B_logic, "B_code": B_code, "B_obs": B_obs,
            "T": T, "S": S, "taut_line": taut_line,
            "correction_context": denial, "assertion_object": assertion_object,
        },
        "category": category,
    }
    if skip_reason:
        base.update({"verdict": "SKIP", "skip_reason": skip_reason,
                     "failure_type": None, "missing": None, "all_missing": []})
        return base

    # ---- 失败型，优先级 F3 > F2 > F1 ----
    # ★ F2 只追究「本件确实写了两段式声明」的情形：真重言式 / 正确等价式 /
    #   Fréchet 定理等**单一命题**不是两段式声明，其依据自足，不因窗口里
    #   没写「依据=」而报 F2（否则关一 S1/S3、关二 S4 会被误报，已实跑证实）。
    declares_two_stage = T and S
    logic_self_based = T and B_logic and not B_obs

    all_missing: list[str] = []
    if not T and not S:
        all_missing.append("Q1 重言半缺失")
    if T and not S:
        all_missing.append("Q2 实质半缺失")
    if declares_two_stage and not B:
        all_missing.append("Q3 依据缺失")
    if declares_two_stage and B_obs and not R:
        all_missing.append("Q4 仅 N 行观测缺范围声明")

    f3 = I and O and not R_same_line
    f2 = (declares_two_stage and not logic_self_based and
          ((not B) or (B_obs and not R)))
    f1 = E_eq and (not T) and (not S)
    corrected_scope = denial and R_same_line and not f3

    if f3:
        ftype, verdict = "F3", "FAIL"
        missing = ("强度标签 " + "/".join(I_hits[:3]) +
                   " 与观测证据在同一断言上共现，中间无范围声明；缺 Q4 范围声明")
    elif corrected_scope:
        # 强度标签被明确否定且带范围：正确限定/撤回，不报 F1/F2/F3
        ftype, verdict, missing = None, "CORRECTLY_SCOPED", None
    elif f2:
        ftype, verdict = "F2", "FAIL"
        missing = "；".join(x for x in all_missing if "Q1 重言半" not in x) or "Q3 依据缺失"
    elif f1:
        ftype, verdict = "F1", "FAIL"
        missing = "Q1 重言半 + Q2 实质半两半全缺；无 A⊆B / B⊆A 拆分"
    elif category == "TAUTOLOGY":
        # 真重言式：显式报出（关一「必须报」），不猜为实质条件
        ftype, verdict, missing = None, "TAUTOLOGY_OK", None
    elif T and S and B and (not B_obs or R):
        ftype, verdict, missing = None, "PASS_QUALIFIED", None
    elif not E_eq and category == "SUBSTANTIVE" and not I:
        # 真实质条件（非 A=B 型等式声明）：不施加两段式义务，
        # 也不报 F1/F2/F3。关二 S2/S7 即此类（只读形态，不猜语义）。
        ftype, verdict, missing = None, "SUBSTANTIVE_OK", None
    else:
        base.update({"verdict": "UNDECIDABLE", "failure_type": None,
                     "missing": "窗口结构齐全但无法归类（不猜）",
                     "all_missing": all_missing,
                     "skip_reason": "K6_structure_unclassifiable"})
        return base

    base.update({"verdict": verdict, "failure_type": ftype, "missing": missing,
                 "all_missing": all_missing, "skip_reason": None})
    return base


def scan_file(path: pathlib.Path) -> dict[str, Any]:
    """输入一份 .md，输出 findings / passes / tautology_ok / skips / undecidables。"""
    lines, err, nbytes, sha = read_lines(path)
    rec: dict[str, Any] = {
        "file": rel(path), "abs": str(path), "sha256": sha, "bytes": nbytes,
        "n_lines": len(lines), "window_radius": WINDOW_RADIUS,
        "local_radius": LOCAL_RADIUS,
    }
    if err:
        rec.update({"read_error": err, "findings": [], "passes": [], "tautology_ok": [],
                    "skips": [], "undecidables": [], "error": err})
        return rec

    segs = build_segments(lines)
    anchors = anchor_lines(lines)
    findings, passes, taut_ok, skips, undec = [], [], [], [], []

    for a in sorted(anchors):
        seg = next((s for s in segs if s[0] <= a <= s[1]), (a, a))
        lo, hi, wlines = window_for(a, seg, lines)
        r = classify_window(a, anchors[a], lo, hi, wlines, lines)
        f = rec["file"]
        r["file"] = f
        r["file:line"] = f"{f}:{a}"
        r["window_lines"] = [f"{f}:{n}" for n in range(lo, hi + 1)]
        # 任何一条命中都必须附 file:line 与命中的原文行
        r["evidence_lines"] = [
            {"file:line": f"{f}:{n}", "text": lines[n - 1]}
            for n in range(lo, hi + 1)
        ]
        r["evidence_matches"] = [
            {"kind": k, "file:line": f"{f}:{n}", "text": lines[n - 1],
             "matched": _hits(lines[n - 1], pats)}
            for n in range(lo, hi + 1)
            for k, pats in (("E", E_MARKERS), ("I", INTENSITY + UNIVERSAL_CLAIM),
                            ("O", OBS_EVIDENCE), ("R", SCOPE))
            if _hits(lines[n - 1], pats)
        ]
        v = r["verdict"]
        if v == "FAIL":
            findings.append(r)
        elif v in ("PASS_QUALIFIED", "CORRECTLY_SCOPED", "SUBSTANTIVE_OK"):
            passes.append(r)
        elif v == "TAUTOLOGY_OK":
            taut_ok.append(r)
        elif v == "SKIP":
            skips.append(r)
        else:
            undec.append(r)

    skip_by_reason: dict[str, int] = {}
    for s in skips + undec:
        k = s.get("skip_reason") or "UNSET"
        skip_by_reason[k] = skip_by_reason.get(k, 0) + 1
    by_ftype: dict[str, int] = {}
    for x in findings:
        by_ftype[x["failure_type"]] = by_ftype.get(x["failure_type"], 0) + 1

    rec.update({
        "n_segments": len(segs), "n_anchors": len(anchors),
        "n_findings": len(findings), "n_passes": len(passes),
        "n_tautology_ok": len(taut_ok), "n_skips": len(skips),
        "n_undecidables": len(undec),
        "skipped_total": len(skips) + len(undec),
        "skip_by_reason": skip_by_reason, "findings_by_type": by_ftype,
        "findings": findings, "passes": passes, "tautology_ok": taut_ok,
        "skips": skips, "undecidables": undec,
    })
    return rec


# ---------------------------------------------------------------------------
# 正控 / 负控（检测器自造文本，不触碰被检文档；落盘 _eq_selftest_out.json）
# ---------------------------------------------------------------------------
def controls() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    def add(cid: str, name: str, text: str, expect_verdict: str,
            expect_ftype: str | None, expect_category: str | None, note: str) -> None:
        lines = text.split("\n")
        segs = build_segments(lines)
        anchors = anchor_lines(lines)
        a = min(anchors) if anchors else 1
        seg = next((s for s in segs if s[0] <= a <= s[1]), (a, a))
        lo, hi, wlines = window_for(a, seg, lines)
        r = classify_window(a, anchors.get(a, []), lo, hi, wlines, lines)
        r["file"] = f"<control:{cid}>"
        r["file:line"] = f"<control:{cid}>:{a}"
        cases.append({
            "id": cid, "name": name, "input_text": text,
            "expect_verdict": expect_verdict, "expect_failure_type": expect_ftype,
            "expect_category": expect_category,
            "actual_verdict": r["verdict"], "actual_failure_type": r["failure_type"],
            "actual_category": r["category"], "flags": r["flags"],
            "missing": r["missing"], "skip_reason": r.get("skip_reason"),
            "passed": (r["verdict"] == expect_verdict and
                       r["failure_type"] == expect_ftype and
                       (expect_category is None or r["category"] == expect_category)),
            "note": note,
        })

    add("P1", "正控：裸集合等式、两半全缺 → F1",
        "chain_changed=18 | unresolved_changed=18 | 集合恒等? True",
        "FAIL", "F1", None, "复刻 COMPARABILITY_AUDIT.md:158 逐字形态（检测器自造）")
    add("P2", "正控：决定性 + 观测证据、无同行范围 → F3",
        "3. **决定性集合等式**：实跑命令 2 输出 2layerPASS= 18 set equal? True，即 18 个 id 恰好等于。",
        "FAIL", "F3", "SUBSTANTIVE", "复刻 METRIC_CONVENTION_AUDIT.md:108 逐字形态（检测器自造）")
    add("P3", "正控：两半齐全、依据为 N 行观测却无范围 → F2",
        "`A ⊆ B` 是去掉一个合取项的重言式；`B ⊆ A` 非平凡方向禁止格为空，实跑 74 行统计 cells=0 set equal? True。",
        "FAIL", "F2", None, "T=True S=True B_obs=True R=False ⇒ Q4 缺失（检测器自造）")
    add("P4", "正控：跨行两段式（重言半在第 1 行、实质半在第 3 行）→ F2",
        "`A ⊆ B` 是去掉一个合取项的重言式。\n- 数据：实跑 `cells_r10C_n13P_r12C = 0`、`set equal? True`。\n- `B ⊆ A` 非平凡方向禁止格为空。",
        "FAIL", "F2", None, "跨行窗口半径 8 覆盖；T@1 / S@3 距离 2（检测器自造）")
    add("N1", "负控：强度标签被否定 + 同行有范围 → 不报 F3",
        "⇒ `P(r12=PASS|n13=PASS)=38/38=1.000` 是**本 74 行上的观测值，不是精确 1.000、不是定理**。",
        "CORRECTLY_SCOPED", None, "SUBSTANTIVE", "复刻 KEFF_CALC.md:314 逐字形态（检测器自造）")
    add("N2", "负控：代码级依据 + 范围 → 合格",
        "根因不是近似省一层，而是 **R12 不是独立证据根**：依赖图为单一根 R10 → {R12, N13.C}；本 74 行观测。\n"
        "`A ⊆ B` 是去掉一个合取项的重言式，`B ⊆ A` 只排除 `(r10=P,n13=P,r12=C)` 格；依据=代码级依赖图 file:line。",
        "PASS_QUALIFIED", None, None, "复刻 METRIC_CONVENTION_AUDIT.md:104/106 与 LAYER_IDENTITY.md:104 组合（检测器自造）")
    add("N3", "负控：别论域「恒等」、无等式无观测 → skip",
        "本节讨论帧率恒等，与集合断言无关。",
        "SKIP", None, None, "K2（检测器自造）")
    add("N4", "负控：既无等式也无强度标签 → skip",
        "本行只是普通叙述，没有断言。",
        "SKIP", None, None, "K1（检测器自造）")
    add("N5", "负控：提问式「是否定理」 → skip",
        "`P(r12=PASS|n13=PASS)=1.000` 是否定理：未验。",
        "SKIP", None, None, "K1/K3（检测器自造）")
    add("N6", "负控：真重言式类别判定 TAUTOLOGY 且不报 F1/F2/F3",
        "`A ⊆ B` 是去掉一个合取项的逻辑重言式，`A = B∩{r12=PASS}`；8 格穷举 F(A⊆B)=[]，零信息量。\n"
        "`B ⊆ A` 非平凡方向禁止格 `(r10=P,n13=P,r12=C)`，依据=本批语料的观测等式，本 74 行。",
        "TAUTOLOGY_OK", None, "TAUTOLOGY", "关一形态（检测器自造）")
    return cases


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        cs = controls()
        out = {
            "n_controls": len(cs),
            "n_passed": sum(1 for c in cs if c["passed"]),
            "n_failed": sum(1 for c in cs if not c["passed"]),
            "controls": cs,
        }
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0 if out["n_failed"] == 0 else 1

    if "--scan" in argv:
        i = argv.index("--scan")
        rec = scan_file(pathlib.Path(argv[i + 1]))
        if "--out" in argv:
            j = argv.index("--out")
            op = pathlib.Path(argv[j + 1])
            op.parent.mkdir(parents=True, exist_ok=True)
            op.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            print(json.dumps({"written": str(op), "file": rec["file"],
                              "n_findings": rec.get("n_findings"),
                              "n_tautology_ok": rec.get("n_tautology_ok"),
                              "n_skips": rec.get("n_skips"),
                              "n_undecidables": rec.get("n_undecidables"),
                              "findings_by_type": rec.get("findings_by_type"),
                              "skip_by_reason": rec.get("skip_by_reason")},
                             ensure_ascii=False))
        else:
            print(json.dumps({k: v for k, v in rec.items()
                              if k not in ("findings", "passes", "tautology_ok",
                                           "skips", "undecidables")},
                             ensure_ascii=False, indent=1))
        return 0

    print(json.dumps({"usage": "--selftest | --scan <abs.md> [--out <abs.json>]",
                     "module": "_eq_detector", "window_radius": WINDOW_RADIUS,
                     "local_radius": LOCAL_RADIUS}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

### 3.2 段落窗口与状态机（含半径依据）

**状态机**（`_eq_DESIGN.md:222-231` → 实现 `build_segments` / `anchor_lines` / `window_for`，`_eq_detector.py:205-236`）：逐行扫描；命中 M1–M5 任一形态的行成为**锚点**；窗口 `W = [anchor−8, anchor+8] ∩ 当前硬边界段落`；**硬边界** = 空行 / `^#{1,6}\s` 标题 / `^---+$` 分隔线 / 行首三反引号代码围栏（正则 `_eq_detector.py:164`）；软边界（表格行/引用行/列表项）不切窗。对每锚点产一条判定记录（EMIT），skip 窗口只计数（SKIP）。

**R = 8 的依据（如实分级）**：
- 实现员申报的量测（`_eq_DESIGN.md:234-243`）：命令 `python -I -X utf8 -c "<扫 8 个只读目录全部 .md；按空行/标题分块；量测块内『重言半标记』与『实质半标记』的最小行距>"`，申报输出 `n_blocks 958 / max_block_len 76 / median 3.0`、两半同块 42 个、距离分布 `[(0,32),(1,4),(2,2),(5,3),(8,1)]`、最大 8；局部半径申报 `0:288/1:90/2:86/3:61/4:22 ⇒ 85% 在 ±2 行内`。★ **逐数未验**：无原始命令与输出留档（复核员 §6 实记；本件亦未找到留档工件），**未复现**。
- 本件实跑复核员独立量测脚本 `python -I -X utf8 _eqv_measure.py`（只读，本会话第一手输出）：`n_blocks = 1039  max_block_len = 76  median = 2`；两半同块 `36` 个，距离分布 `[(0, 22), (1, 5), (2, 2), (3, 3), (4, 1), (5, 1), (8, 2)]`，**max = 8**；强度标签行→最近范围词距离 `[0:55, 1:43, 2:26, 3:15, 4:12, 5:9, 6:5, 7:1] / none 14`，**±2 内占比 = 0.747**。与复核员回件数值逐项一致。
- **两级量测共同成立的结论**：已观测跨行两段式的最大距离 = 8（R=8 覆盖全部实测情形、且 ≪ 最大块长 76 不会吞整节）；多数已限定断言的范围词在 ±2 行内（85% vs 74.7%，口径不同都过半）。**R=8 / R_local=2 是本语料（15 件 `.md`）上的经验值，不是全称定理；换语料必须重测**（§6.3 P3）。

**F3 范围同行判据**：`R_same_line` 只看锚点行自身（`_eq_detector.py:259-264`，注释逐字给出设计理由与 `METRIC_CONVENTION_AUDIT.md:110`「反事实基线期望」实例）；强度 I 用 ±2 局部窗（`:251-253,267-268`）。

### 3.3 「无法判定」判据（K1–K6，宁可报无法判定也不许猜）

实现 `_eq_detector.py:300-317`（skip）与 `:387-392`（K6），计数落 `skip_by_reason`：

- **K1** `¬I ∧ ¬E`：既无明显强度、又无显式等式 ⇒ 非恒等类断言，跳过。
- **K2** 锚点行含 `恒等` 但窗内 `¬E ∧ ¬O ∧ ¬I`：别论域「恒等」措辞（如 GOAL 台账 46 行），跳过。
- **K3** 提问句（`是否…` / 行尾 `?`/`？`）不是断言 → `K3_question_not_assertion`；或 `I_raw ∧ ¬E ∧ ¬O` 强度无断言对象 → `K3_intensity_without_assertion_object`。
- **K4** 窗内 T∧S 但依据与范围矛盾（既写「本 74 行」又写「全称定理」且无消歧）→ `K4_conflict_scope_basis`，不猜哪边对。
- **K5** 整改意见/纯转述行（`→ 改 / 须撤回 / 判错置 / 改「` 等）且自身无 E∧O → `K5_pure_quotation`（只豁免纯转述）。
- **K6** 结构齐全但无法归类 → verdict = `UNDECIDABLE`、`skip_reason=K6_structure_unclassifiable`，**不产 finding、不猜**（`:387-392` 逐字 `"窗口结构齐全但无法归类（不猜）"`）。
- 读取失败 → `UNDECIDABLE` + `read_error`，绝不猜（`:407-410`）。

### 3.4 自检正控负控（本会话实跑输出）

命令与输出（本会话第一手）：

```
$ python -I -X utf8 D:/Project/ra2-campaign-forge/lead/eqdecl_gate_20261109/_eq_detector.py --selftest > _eqg_selftest_rerun.json
（EXIT=0）
$ python -I -X utf8 -c "<hashlib 两文件比对>"
_eq_selftest_out.json   42b5d7f3acd3260eb4601d91eb865abf18be505b614d58e44c04671df6fbe21f 10222
_eqg_selftest_rerun.json 42b5d7f3acd3260eb4601d91eb865abf18be505b614d58e44c04671df6fbe21f 10222
SELFTEST_RERUN_IDENTICAL = True
```

10 控例逐条（存盘件 `_eq_selftest_out.json` 复算输出，与复跑件字节全同；`n_controls 10 / n_passed 10 / n_failed 0`）：

| id | 控例（输入要点） | 期望 | 实际 | 通过 |
|---|---|---|---|---|
| P1 | 正控：裸集合等式「chain_changed=18 \| unresolved_changed=18 \| 集合恒等? True」（复刻 COMPARABILITY:158 形态） | FAIL/F1 | FAIL/F1 | ✅ |
| P2 | 正控：「决定性集合等式…set equal? True…18 个 id 恰好等于」（复刻 MC:108） | FAIL/F3 | FAIL/F3 | ✅ |
| P3 | 正控：两半齐全、依据 N 行观测无范围（T∧S∧B_obs∧¬R） | FAIL/F2 | FAIL/F2 | ✅ |
| P4 | 正控：跨行两段式（T@1 / S@3，距离 2） | FAIL/F2 | FAIL/F2 | ✅ |
| N1 | 负控：「38/38=1.000 是**本 74 行上的观测值，不是精确 1.000、不是定理**」（复刻 KEFF:314） | CORRECTLY_SCOPED | CORRECTLY_SCOPED | ✅ |
| N2 | 负控：代码级依赖图依据 + 范围 → 合格 | PASS_QUALIFIED | PASS_QUALIFIED | ✅ |
| N3 | 负控：别论域「帧率恒等」 | SKIP(K2) | SKIP/K2_ident_word_other_domain | ✅ |
| N4 | 负控：普通叙述无断言 | SKIP(K1) | SKIP/K1_no_equality_no_intensity | ✅ |
| N5 | 负控：提问式「是否定理：未验」 | SKIP(K1/K3) | SKIP/K3_question_not_assertion | ✅ |
| N6 | 负控：真重言式（标签+8 格穷举展开） | TAUTOLOGY_OK/TAUTOLOGY | TAUTOLOGY_OK/TAUTOLOGY | ✅ |

★ 如实记：实现员自述「开发中检测器 3 次自测失败（N1 分类、F3 范围判据、S2/S7 误报 F1）均如实修正后重跑」——该**历史过程无工件可验**（复核员 §6 同判），本件只验到**终态 10/10**（两轮字节全同）。同类先例见 `TAUTOLOGY_AUDIT.md:760-763`（上游门禁曾把禁用串写进输出示例而自触发，逐字「这正说明门禁查的是**字面**而非语义」）。

---

## 4 ★ 三关验收矩阵（9 案例 × 期望 × 实际 × 通过，逐格）

**关判据**（`_eq_three_gates.py:69-73` 逐字）：关一＝「真重言式必须报『重言式』而不是『实质条件』；不得报 F1/F2/F3」；关二＝「真实质条件必须不误报 F1/F2/F3」；关三＝「观测等式写成定理必须报 F3」。代码级判定（`:104-113`）：关一 `act_cat=="TAUTOLOGY" ∧ act_f is None ∧ act_v=="TAUTOLOGY_OK"`；关二 `act_f is None ∧ act_v ∈ {SUBSTANTIVE_OK, PASS_QUALIFIED, CORRECTLY_SCOPED, SKIP}`；关三 `act_v=="FAIL" ∧ act_f=="F3"`；并核对期望类别。

**本会话联跑命令与输出（第一手）**：

```
$ python -I -X utf8 D:/Project/ra2-campaign-forge/lead/eqdecl_gate_20261109/_eq_three_gates.py
三关 × 9 案例：9/9 通过
  关一: 3/3 all_passed=True
  关二: 3/3 all_passed=True
  关三: 3/3 all_passed=True
three_gates_exit=0
（重跑后 _eq_three_gates_out.json sha256 2c9c4fe9…64be / 33009 字节，与存盘件全同）
```

逐格矩阵（期望列 = 编排方【任务】第三步 + `TAUTOLOGY_AUDIT.md:437-461`；实际列 = 联跑输出；锚点原文均本会话实读核验）：

| 关 | 案例 | 锚点（实读原文要点） | 期望 | 实际 | 通过 | 逐格依据 |
|---|---|---|---|---|---|---|
| 关一 | G1a（S1 半 A⊆B） | `LAYER_IDENTITY.md:104`：「`A ⊆ B` 是去掉一个合取项的重言式；非平凡方向 `B ⊆ A` 只排除 (r10=PASS & n13=PASS & r12=CATCH)」 | 重言式，不报 F | TAUTOLOGY_OK / 无F / TAUTOLOGY | ✅ | `TAUTOLOGY_AUDIT.md:446` S1 行（复合判定：`A⊆B`=重言式）+ `:465` 真重言式清单；存盘 flags T=True taut_line=True |
| 关一 | G1b（S3 :125 逻辑重言式） | `_li_LAYER_IDENTITY_PROOF_20261109.md:125`：「`A ⊆ B` 是**去掉一个合取项的逻辑重言式**」 | 重言式，不报 F | TAUTOLOGY_OK / 无F / TAUTOLOGY | ✅ | `TAUTOLOGY_AUDIT.md:448` S3 行（「`:125`=**重言式（判对）**」） |
| 关一 | G1c（S12 恒真兜底） | `SCORE_DECOMP.md:235`：「是**恒真兜底在正类样本上的必然命中，信息量 = 0**，不算算法改进」 | 重言式，不报 F | TAUTOLOGY_OK / 无F / TAUTOLOGY | ✅ | `TAUTOLOGY_AUDIT.md:457` S12 行（「**重言式（真恒真，类型不同）·正面样板**」——本库唯一把恒真性正确标「零信息量」的落点） |
| 关二 | G2a（S2 依赖图正确否定句） | `METRIC_CONVENTION_AUDIT.md:104`：「根因不是「R12 数值接近 1 所以近似省一层」，而是 **R12 不是独立证据根**：」 | 实质条件，不报 F1/F2/F3 | SUBSTANTIVE_OK / 无F / SUBSTANTIVE | ✅ | `TAUTOLOGY_AUDIT.md:447` S2 行逐字「**该句本身正确，不列入撤回对象**」；存盘 flags E_eq=False（严格等式义务不施加于否定句）；锚定形态 = M2d 第二变体 `近似省一层`（matched_strings 实证） |
| 关二 | G2b（S4 正确等价式） | `LAYER_IDENTITY.md:128`：「**正确等价式**：`A = B ⟺ P(r12=PASS \| r10=PASS & n13=PASS) = 1`。…二者在 74 行上同真，靠的正是 `cells_r10C_n13P_r12C = 0` 这一额外巧合」 | 实质条件，不报 F | PASS_QUALIFIED / 无F / SUBSTANTIVE | ✅ | `TAUTOLOGY_AUDIT.md:449` S4 行；同行含范围词「在 74 行上…巧合」（SCOPE 表实读补入形态） |
| 关二 | G2c（S7 Fréchet 恰取等） | `KEFF_CALC.md:262`：「`P(allPASS\|E) ≤ min q_i = min(0.487179, 0.897436, 0.076923) = 0.076923`」 | 实质条件，不报 F | SUBSTANTIVE_OK / 无F / SUBSTANTIVE | ✅ | `TAUTOLOGY_AUDIT.md:452` S7 行（数学定理 + 实测取等）；F1 的 E_EQ_STRICT 不含 `≤ min q_i`（`:137-143` 注释逐字登记） |
| 关三 | G3a（S1「决定性集合等式」标签） | `METRIC_CONVENTION_AUDIT.md:108`：「3. **决定性集合等式**：实跑命令 2 输出 … `2layerPASS= 18 set equal? True`，即 …18 个 id **恰好等于** …」 | FAIL / F3 | FAIL / F3 / SUBSTANTIVE | ✅ | `TAUTOLOGY_AUDIT.md:446` S1 行 + `:474` 逐字「把实跑 `set equal? True` 直接接『决定性』标签，中间无范围声明」；锚点行无 SCOPE 词（R_same_line=False 实证） |
| 关三 | G3b（S5 R12 增量 0 bit 全称） | `EVIDENCE_INDEPENDENCE.md:149`：「- **R12 增量判别力 = 0 bit**：`P(r12=PASS \| n13=PASS) = 38/38 = 1.000`（`_ei_07_final_out.json:95`）…」 | FAIL / F3 | FAIL / F3 / SUBSTANTIVE | ✅ | `TAUTOLOGY_AUDIT.md:450` S5 行（「**实质条件·全称已构造性证伪**」）；无显式强度标签，靠 `UNIVERSAL_CLAIM`（`= 0 bit`）作强度侧信号命中 |
| 关三 | G3c（S8 38/38） | `METRIC_CONVENTION_AUDIT.md:107`：「…⇒ `P(r12=PASS\|n13=PASS)=38/38=1`（`CHAIN_VS_SINGLE.md:206` 亦记 38/38=1.000）」 | FAIL / F3 | FAIL / F3 / SUBSTANTIVE | ✅ | `TAUTOLOGY_AUDIT.md:453` S8 行；同窗 `:108` 决定性标签（I 经局部窗）+ 锚点行无范围词 |

**负控核对（关三的反向证明）**：`KEFF_CALC.md:314` 逐字「⇒ `P(r12=PASS\|n13=PASS)=38/38=1.000` 是**本 74 行上的观测值，不是精确 1.000、不是定理**。」——同行含范围词（本 74 行）+ 纠偏语境（不是定理）⇒ `CORRECTLY_SCOPED` 不报 F3（全量存盘实证 KEFF:314 落 passes 桶），证明**范围声明在起作用**，F3 不是「见 38/38 就报」。

**有没有「未过」的格：没有。** 9/9 全通过，且**无一格是「期望本身有问题」**——所有实现前的偏差都是检测器问题，已修正并留痕（`_eq_CONCLUSION.md:48-58` 逐条）：G1a/G1b 曾误报 F2（Q3 依据义务错施于单一命题）、G1c 曾被 skip（缺 M4f 形态）、G2a/G2c 曾误报 F1（E_EQ_STRICT 未区分否定句与不等式）、G2b 曾误报 F2（SCOPE 表缺「在 74 行上/巧合」逐字形态）、G3b 曾被 skip（缺 UNIVERSAL_CLAIM 强度侧信号）。这些修正痕迹与最终形态均在 `_eq_detector.py` 注释中逐字可查（`:59-62,120-128,137-148`）。**本会话联跑为修正后代码的重跑，9/9 与存盘件字节级全同（哈希比对见上）。**

---

## 5 ★ 全量结果

### 5.1 总量与分布（本会话两轮复算 + 联跑复现）

命令：`python -I -X utf8 _eqg_counts.py`（复算存盘件）+ `python -I -X utf8 _eq_full_run.py`（联跑，EXIT=0，重写后 `_eq_full_out.json` sha256 `efb65427…d2919` / 3293219 字节与存盘件**全同**）。两组输出一致：

- 范围：15 件 `.md`（§1.3 清单）；锚点 = **918**；findings = **212**（F1 **57** / F3 **150** / F2 **5**）；tautology_ok = **27**；passes = **188**；skips = **346**；undecidables = **145**；skipped_total = **491**。918 = 212+27+188+346+145（本件复算自洽）。
- 按文件分布（findings，联跑输出逐字）：

| 件 | findings | 分型 | 锚点 |
|---|---|---|---|
| `tautology_audit_20261109/TAUTOLOGY_AUDIT.md` | 77 | F3 62 / F1 12 / F2 3 | 230 |
| `tautology_audit_20261109/_ta_TAUTOLOGY_AUDIT_20261109.md` | 59 | F3 47 / F1 10 / F2 2 | 167 |
| `layer_identity_20261109/LAYER_IDENTITY.md` | 14 | F1 7 / F3 7 | 91 |
| `evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md` | 11 | F3 8 / F1 3 | 39 |
| `metric_audit_20261109/METRIC_CONVENTION_AUDIT.md` | 10 | F3 8 / F1 2 | 46 |
| `layer_identity_20261109/_li_LAYER_IDENTITY_PROOF_20261109.md` | 9 | F3 7 / F1 2 | 78 |
| `comparability_20261109/_cmp_AUDIT_20261109.md` | 8 | F1 8 | 28 |
| `metric_audit_20261109/_ma_METRIC_AUDIT.md` | 8 | F3 4 / F1 4 | 33 |
| `keff_calc_20261109/KEFF_CALC.md` | 6 | F3 6 | 45 |
| `comparability_20261109/COMPARABILITY_AUDIT.md` | 3 | F1 3 | 40 |
| `score_decomp_20261109/_sd_report.md` | 2 | F1 2 | 32 |
| `score_decomp_20261109/SCORE_DECOMP.md` | 2 | F1 2 | 27 |
| `gate_pipeline_20261109/_gp_DESIGN.md` | 1 | F1 1 | 18 |
| `gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md` | 1 | F1 1 | 21 |
| `keff_calc_20261109/_ke_REPORT.md` | 1 | F3 1 | 23 |

- skip 分桶（15 件合计，本件复算）：`K1_no_equality_no_intensity 267 / K3_question_not_assertion 35 / K3_intensity_without_assertion_object 25 / K6_structure_unclassifiable 145 / K2_ident_word_other_domain 19`，合计 491。★ F2 仅 5 条且全部落在审计件的表格/示例行上（§2.3 已逐条列出）——「两段式声明」在本库成件文本中几乎只以**错误等价式被引用/整改**的形态出现，成件正文极少裸写两段式。
- 命中附证：每条 finding 带 `file:line`、`text` 原文行、`evidence_lines`（窗内逐行 file:line+原文）、`evidence_matches`（命中串）（`_eq_detector.py:424-436`）；skip/undecidable 同样保留原文（`scan_file` 全桶落盘）。

### 5.2 编排方【恒等断言清点】45 行对账

复算输出（`_eqg_counts.py`）：`n_rows = 45 / n_anchored = 45（n_not_anchored = 0）/ n_findings = 5`；verdict 分布 `SKIP 19 / FAIL 5 / TAUTOLOGY_OK 2 / UNDECIDABLE 9 / PASS_QUALIFIED 2 / CORRECTLY_SCOPED 8`（5+19+9+8+2+2=45）。5 条 FAIL 逐条：

| file:line | F 型 | 该行原文（要点） | 复核员仲裁 |
|---|---|---|---|
| `LAYER_IDENTITY.md:13` | F1 | 目的段：「判定「{三层全 PASS} 与 {r10&r13 双 PASS} 逐 id 相等、P(r12=PASS\|n13=PASS)=38/38=1」这一恒等，究竟是**逻辑必然**还是…巧合」 | **疑似误报**（目的/疑问行，非断言；复核员判 CORRECTLY_SCOPED/疑问句更妥）。旗标：E_eq=True 全窗、T=S=False、R_same_line=True（matched 含「本批语料」） |
| `LAYER_IDENTITY.md:223` | F3 | 影响表行 12：「`k_eff=0.61`、`≈1～1.5 层，不是 3 层`…恒等破则数值破」 | **疑似误报**（行自身无强度标签；F3 经邻行 `:224`「R12 不提供任何新信息」——UNIVERSAL_CLAIM 串——经 ±2 局部窗连坐，U_local=True 实证；行内只有依赖陈述） |
| `LAYER_IDENTITY.md:242` | F1 | 结论行：「恒等把「n13=PASS&r12=CATCH 格为空」与「r10=C&n13=P&r12=C 格为空」两件**本批语料事实**打包成一个观察等式」 | **疑似误报**（E_eq 来自窗口 `:240` 的「`A=B`」，而 `:240` 本身逐字写「**不是** `A=B` 的等价式」——整窗 E_eq 连坐实证） |
| `LAYER_IDENTITY.md:338` | F3 | 复核转述行：「【复核】明确「主结论已独立复现、成立」：X1/X2/X3 三例均 r10=PASS r12=CATCH n13=PASS、∈B 且 ∉A，同时破集合恒等与 P(…)=1」 | **两检测器共同疑似误报**（该行是「恒等已被打破」的**正确报告**；F3 因同行无 SCOPE 词） |
| `COMPARABILITY_AUDIT.md:158` | F1 | 「chain_changed=18 \| unresolved_changed=18 \| 集合恒等? True」 | **合理命中**（按格式合规口径；与实现员 P4 披露一致，`TAUTOLOGY_AUDIT.md:455` 判「措辞未升级为定理，风险低」不矛盾——格式缺失 ≠ 语义错误） |

★ 复核员双检测器逐行仲裁（`_eqv_diffrows.py`，**本件未重跑、脚本在写域可复跑**）结论如实转录：实现员对的——`LI:228`（其 K3 提问跳过优于复核员 F3）、`LI:337 / LI:400 / SD:135 / SD:239`（其 K 跳过或 UNDECIDABLE 优于复核员 F3）；复核员对的——`LI:52 / LI:13 / LI:223 / LI:242`（连坐或回显误报）。`LI:52`（实跑输出回显行「输出：`A_n 18 B_n 18 A==B True only_A [] only_B []`」被报 F1）**不在** 45 行清点内、也未在抽样中披露——属「45 行 5 FAIL」覆盖呈现之外的疑似误报（§5.3 计入）。

### 5.3 真命中 / 误报抽样（19 条逐条）与精确率 / 召回率（**估计非测量**）

实现员抽样 19 条（≥15，存盘 `_eq_full_out.json:sampling`，本件复算一致；标签与理由见 `_eq_full_run.py:117-157` 逐字登记）。逐条判定：

| # | file:line | 实际 | 实现员标签 | 判定依据（一行） |
|---|---|---|---|---|
| 1 | `METRIC_CONVENTION_AUDIT.md:108` | FAIL/F3 | 真命中 | 「决定性集合等式…set equal? True…恰好等于」同行无范围；`TAUTOLOGY_AUDIT.md:474` 逐字点名此行 |
| 2 | `METRIC_CONVENTION_AUDIT.md:107` | FAIL/F3 | 真命中 | 「⇒ P(…)=38/38=1」+ 同窗 :108 决定性；S8（`:453`）全称已构造性证伪 |
| 3 | `EVIDENCE_INDEPENDENCE.md:149` | FAIL/F3 | 真命中 | 「R12 增量判别力 = 0 bit…38/38 = 1.000」全称口吻+观测；S5（`:450`） |
| 4 | `KEFF_CALC.md:432` | FAIL/F3 | 真命中 | 引 `EI:149` 错措辞的 §6.B 整改行（:433 有「→」改法）——**复核员改判误报**（见下） |
| 5 | `KEFF_CALC.md:434` | FAIL/F3 | 真命中 | 同上（引 `EI:294` 表格，:435 有「→」）——**复核员改判误报** |
| 6 | `KEFF_CALC.md:440` | FAIL/F3 | 真命中 | 同上（引 `_cs:334`，:441 有「→」）——**复核员改判误报** |
| 7 | `EVIDENCE_INDEPENDENCE.md:294` | FAIL/F3 | 真命中 | 本件自身表格断言「P(…)=1.000，增量 **0 bit**」；`TAUTOLOGY_AUDIT.md:450` 列 S5 落点含 :294（复核员认可可辩护） |
| 8 | `EVIDENCE_INDEPENDENCE.md:302` | FAIL/F3 | 真命中 | 「`R12` 增量信息 **0.0 bit**」同上（复核员认可） |
| 9 | `METRIC_CONVENTION_AUDIT.md:126` | FAIL/F3 | **误报** | 评审判定表（「**错置** \| **证据不足，降级存疑**」）在讨论 38/38 口径，非本件升级；QUOTE_OR_REVIEW 未覆盖该评审语气 |
| 10 | `TAUTOLOGY_AUDIT.md:356` | FAIL/F3 | **误报** | §3.4 检查清单的**禁用串清单**行（逐字「禁用串自检：…」）；`TAUTOLOGY_AUDIT.md:760-763` 自记同类自触发先例 |
| 11 | `TAUTOLOGY_AUDIT.md:366` | FAIL/F3 | **误报** | 强模式扫描的**串清单回显**行（29 串罗列），非断言 |
| 12 | `LAYER_IDENTITY.md:384` | FAIL/F3 | **误报** | 整改意见表行（「→ 改 …不能当自由度或独立层数的**决定性**论据」——「决定性」作定语）；K5 豁免要求 `not E and not O` 太严 |
| 13 | `METRIC_CONVENTION_AUDIT.md:21` | FAIL/F1 | **误报** | **空表头行**「\| # \| 命令 \| 输出要点 \|」，被 ±8 窗内邻行 `:24`（`set equal? True`/`n13=PASS n= 38`）连坐——F1 用整窗 T/S 而非锚点局部（flags 实证：锚点行 matched 仅「输出」） |
| 14 | `LAYER_IDENTITY.md:267` | FAIL/F3 | **误报** | 「**方法 A（决定性、结构性）—— 依赖图源节点数 + A1–A5 五检**」——「决定性」是**方法名**，非定理标签 |
| 15 | `KEFF_CALC.md:314` | CORRECTLY_SCOPED | 真命中（负向） | 同行范围+否定 ⇒ 不报 F3；负控生效（§4 末） |
| 16 | `LAYER_IDENTITY.md:104` | TAUTOLOGY_OK | 真命中（负向） | 关一 G1a |
| 17 | `SCORE_DECOMP.md:235` | TAUTOLOGY_OK | 真命中（负向） | 关一 G1c |
| 18 | `METRIC_CONVENTION_AUDIT.md:104` | SUBSTANTIVE_OK | 真命中（负向） | 关二 G2a（正确否定句） |
| 19 | `COMPARABILITY_AUDIT.md:158` | FAIL/F1 | 真命中 | 裸集合等式两半全缺；格式合规口径（§5.2 末行） |

**精确率（两级估计，均非测量）**：
- 实现员口径：真命中 13（含 4 条负向 + `COMPARABILITY:158`）/ 误报 6 ⇒ **13/19 = 0.6842**，存盘 `IS_MEASUREMENT = False`、`why_not_measured` 逐字「本任务未做 15 件 `.md` 全量人工逐行标注；`TAUTOLOGY_AUDIT.md:370` 自记『未做全仓逐文件人工通读』；故精确率/召回率只能是估计，不得冒充实测」。
- 复核员一致口径（缺陷②，本件按原文行复核成立）：#4/#5/#6（`KEFF:432/434/440`）是 §6.B 整改清单第 10/11/15 条——我方实读确认三行均属「引用错措辞 + `→` 改法」结构（`:432-433`「10. `EVIDENCE_INDEPENDENCE.md:149`『R12 增量判别力 = 0 bit…』/ → `1.000` 是**观测值非定理**…」），与判为误报的 `LI:384` 同族；按同一标准改判误报 ⇒ 真命中 10 / 误报 9 ⇒ **10/19 = 0.5263**。该值已自标估计非测量，属估计口径偏差而非造假；`EI:294/:302` 的真命中标签可辩护（`TAUTOLOGY_AUDIT.md:450` 明列 S5 落点含 `EVIDENCE_INDEPENDENCE.md:149,294,302`）。
- 另：复核员新增 5 条疑似误报（`LI:52/13/223/242/338`，§5.2）不在 19 条抽样内；若计入，精确率估计将进一步下降——**不给单一数字**（无原则化分母）。

**召回率：不给数值。** 无人工全量标注，真值总数未知。可见下界仅「三关 9/9 + 45 行中 5 行 FAIL」，**不是召回率分母**（存盘 `recall_estimate` 逐字「不可给数值（无人工全量标注，真值总数未知）」）。两条精确率数字与召回率「无数值」一律标注：**估计非测量**（IS_MEASUREMENT=False）。

### 5.4 漏检如实记

1. **「决定性集合等式」串的全库核对（本件实跑）**：15 件扫描范围内含该串的行共 **28 行**，其中检测器报 F3 的恰 **10 行**（含要害 `METRIC_CONVENTION_AUDIT.md:108` 与 `TAUTOLOGY_AUDIT.md:446` 列的 S1 另一落点 `_ma_METRIC_AUDIT.md:77`）；其余 18 行实读均为引述/整改/清单/判定表行（其中 `TAUTOLOGY_AUDIT.md:356` 报 F3 属已登记误报，`TAUTOLOGY_AUDIT.md:628` 报 F1）。**在「成件正文裸用该标签」这一断言层面无漏检**；18 行非 F3 是否全部应当豁免属 P1 白名单议题（未逐行裁决，如实记）。与复核员「28 行中 F3 恰 10 行」独立复算一致。
2. **台账不在扫描范围**（复核员缺陷①，§1.3）：两件台账从未被检测；GOAL 46 行含「恒等」若纳入会怎样——**未验**。
3. **K6 静默漏报**：145 条 UNDECIDABLE 不产 finding，其中是否含真违规**未逐条人工核**（`_eq_CONCLUSION.md:167` 自记「未量化」）。
4. **结构性抓不到的 11 类**（`_eq_CONCLUSION.md:147-171` 逐条，复核员未推翻）：① 无 M1–M5 字面形态的隐晦等价（K1 跳过 267 条）；② 跨文件/跨硬边界或距离 > 8 的两段式；③ 语义正确性（forbidden 格**方向**写反——`TAUTOLOGY_AUDIT.md:590` 记上游曾写反；「同一命题」是否真等价；`38/74` 与 `38/38=1` 同名不同分母混淆——`TAUTOLOGY_AUDIT.md:392` 逐字「★ 注意 `38/74` 与 `38/38=1` 是**同名不同分母**，勿混」）；④ 真值/定理的数学证明（只认显式重言标签，作者不写标签判不出 TAUTOLOGY）；⑤ 代码级依据不验证 file:line 真实性；⑥ 引用/转述/清单回显/整改意见与真断言的区分（6 条自报误报中 4 条属此类）；⑦「决定性」作方法名 vs 定理标签（`LI:267`）；⑧ 空表头/表格列被邻行连坐（`MC:21`）；⑨ K6 静默漏报未量化；⑩ 两件台账别论域措辞（**更正**：非「K2 一律跳过」，而是「不在扫描范围、从未被检测」，§1.3）；⑪ 换语料后的半径与串表（`A ≡ B`、`if and only if` 等新写法未覆盖）。
5. **f3 的「同行」判据自身的代价**：范围词写在前一行（如 `KEFF:313-314` 型）时 F3 会误响——`LI:223` 疑似误报即「范围/否定写在邻行」连坐的镜像情形；该代价与「防止 8 行外『反事实』洗掉真 F3」是一对权衡（`_eq_detector.py:259-263` 注释），未做系统调参，如实记。

---

## 6 复核回件（绑定行）+ 结论

### 6.1 绑定行（严格格式）

按 `TAUTOLOGY_AUDIT.md:567-571` 同款约定，绑定行指向**交付件本身**（门禁实现 `_eq_detector.py`）而非回件，避免「回件内含自身哈希」的自指悖论（该件 `:567-569` 逐字「【复核】`sha256Line` 所指被核对象 = 审计员交付件…本次会话 `hashlib` 现盘重算」）。复核员回件绑定行与实现员申报、与本件收尾 `python -I -X utf8 _eqg_fp.py` 实算三方全等：

被核对象 SHA256 = f29a34b516c14a1320c5bd28a9788801e2c577ff8ae34eea0f41b3d035363472，字节数 = 29795

（本件 `EQDECL_GATE.md` 自身不写自哈希，同一约定；其余 7 件交付件哈希见卷首表。）

### 6.2 复核 verdict 与本件复验（verdict = **partial** ⇒ 标 **unconfirmed**）

【复核】回件结论逐字要点：「**主结果全部复现为真，但边界清单有一处机制性失实、抽样标准有一处自相矛盾、另有未披露疑似误报——故 partial 而非 confirmed**」「三关判据在两套独立实现下均 9/9，矩阵、计数、误报自报、零漂移、纪律全部实跑复现为真…缺陷集中在边界清单第 10 条的机制失实、抽样标准不一致与覆盖呈现中未披露的疑似误报，均不动摇三关结果，故判 partial 而非 refuted」。按交付规则 **partial ⇒ unconfirmed**（`TAUTOLOGY_AUDIT.md:563-565` 同款先例：按【交付】「refuted 或 partial 标 unconfirmed」）。

**复核员证实项（本件复验状态逐条标注）**：

| # | 复核员证实项 | 本件复验 |
|---|---|---|
| 1 | 11 件基线 + 8 件交付件指纹零漂移；`_eq_detector.py = f29a34…/29795` 属实 | ✅ 本件 `_eqg_fp.py` 两轮实跑 `FINAL_MATCH = True` |
| 2 | 复核员独立检测器 `_eqv_detector.py` 9/9，逐案判定与实现员全同 | 复核员实跑；本件未重跑其脚本（脚本在写域可复跑）；本件以原检测器联跑 9/9 + 存盘件字节全同独立佐证 |
| 3 | 关二要害 `MC:104`：`E_eq=false`（否定句排除按设计生效），双检测器都不报 F3 | ✅ 本件取 G2a 存盘 flags：E_eq=False、verdict=SUBSTANTIVE_OK |
| 4 | 三关矩阵逐格内存复算 9/9、自检 10/10 复算一致、全量 212 findings 复算 0 mismatch（存盘件是现算产物非手改） | ✅ 本件复算 + **联跑字节级复现**（三关与全量重跑前后哈希全同） |
| 5 | 六条自报误报全部属实（机制由旗标+原文行核实） | ✅ 本件逐条旗标取证（§5.3 #9–#14） |
| 6 | 计数全对（45/45 锚定、212/918、F1 57/F3 150/F2 5、skip 491 分桶、抽样 19/13/6、R=8 复测成立、「决定性集合等式」28 行中 F3 恰 10 行） | ✅ 本件全部复算一致（§5.1/§5.2/§5.4） |
| 7 | 无越界（HEAD 全程 2657458、eqdecl 目录 untracked、11 件收尾指纹全对、零真机零采样、CONCLUSION 明写未执行改写） | ✅ 本件复验（§1.2） |

**复核员点名缺陷（本件逐条复验，全部成立）**：

1. **边界清单第 10 条机制性失实**：`_eq_CONCLUSION.md:168-169` 称台账「K2 一律跳过」，实际 `READ_DIRS`（`_eq_full_run.py:35-44`）不含台账、`scope.md_files` 15 件无 GOAL/PENDING ⇒ **台账从未被扫描**；正确表述「不在扫描范围、从未被检测」（本件代码级复验 + 词频实测 PENDING `恒等`=0 次 / GOAL=49 次/46 行，§1.3）。
2. **抽样标注标准自相矛盾**：`KEFF:432/434/440`（§6.B 整改清单第 10/11/15 条，引 `EI:149/:294/_cs:334` 错措辞并带 `→` 改法）标「真命中」，而同族整改行 `LI:384` 标「误报」；一致口径精确率应为 **10/19 = 0.5263** 而非 0.6842（本件实读三行确认「引用 + →改」结构，§5.3）。属估计偏差非造假（两口径均已标估计非测量）。
3. **未披露的额外疑似误报**：`LI:52`（实跑输出回显被 F1）、`LI:13`（目的/疑问行被 F1）、`LI:223`（F3 经邻行 `:224`「不提供任何新信息」±2 连坐）、`LI:242`（F1 经窗口 `:240` 的「A=B」连坐，而 `:240` 本身写「不是 A=B 的等价式」）、`LI:338`（两检测器共同报 F3，但该行是「恒等已被 X1/X2/X3 打破」的正确报告）；其中 `:13/:223/:242/:338` 正位于「45 行 5 FAIL」的覆盖呈现里，未按误报披露，令覆盖证据表面偏强（本件旗标级复验全部成立，§5.2 表）。
4. **45 行双检测器仲裁分歧**：转录见 §5.2 末（`_eqv_diffrows.py`，本件未重跑）。
5. **小节**：`_eq_DESIGN.md` §1 M2d 注记「`:104` 不会被 M2d 触发」与代码不符（本件以 G2a `matched_strings=['近似省一层']` 实证，§2.1）；`_eq_CONCLUSION.md:207` 称写域「共 7 件」与实际 8 件不符（本件实读 `:207` + 目录清点确认；现含本件与核验工件后更多）；写域含 `__pycache__` 副产品（本件清点确认）。
6. **未复现项**：实现员申报的窗口半径量测逐数（`n_blocks 958 / median 3.0 / [(0,32),(1,4),(2,2),(5,3),(8,1)] / ±2 85%`）**无原始命令留档，未复现**；本件实跑复核员口径量测得 `1039 / 2 / max 8 / ±2 74.7%`（§3.2）——关键结论（最大距离=8、±2 占多数、R 为语料经验值须重测）两级独立成立，逐数不定。实现员「开发中 3 次自测失败如实修正」的历史过程无工件可验，仅终态 10/10 已验（§3.4）。

### 6.3 结论：能否上线、挂哪个环节

**判断：不能作「拒件门禁」；可作「只报不拒（report-only）」的成件后 lint 有条件上线。**（实现员 `_eq_CONCLUSION.md:102-127` 判断，复核员未推翻，本件维持。）

理由（全部有实跑依据）：三关 9/9、正负控 10/10、45/45 锚点覆盖 ⇒ 核心判据自证成立，能抓 `TAUTOLOGY_AUDIT.md:730-731` 自认「仍是提案、未实装」的缺口；但 212 条 findings、抽样精确率估计仅 0.6842（一致口径 0.5263）、误报 6–9/19 ⇒ 直接拒件会淹没人；误报根因是字面门禁的结构性限制（`TAUTOLOGY_AUDIT.md:760-763` 同款先例：「门禁查的是**字面**而非语义」）。

**上线前置条件（缺一不可）**：
- **P1** 把误报形态做成 EXEMPT 白名单并重跑正负控 + 三关确认不回归：至少 7 类——清单回显行（`TAUTOLOGY:366`）、禁用串/检查清单行（`:356`）、整改意见行（`LI:384`、`KEFF:432/434/440`）、评审判定表（`MC:126`）、空表头连坐（`MC:21`，需把 F1 的 T/S 改锚点局部）、方法名「决定性」（`LI:267`）、实跑输出回显（`LI:52`）与复核转述行（`LI:338`）；F2 的 5 条落点（§2.3）亦呈表格/示例行形态，一并纳入。本任务未实装，只登记。
- **P2** 人工全量标注至少一份 `.md`（建议 `METRIC_CONVENTION_AUDIT.md`，10 findings）给出精确率/召回率**测量值**，替换估计。
- **P3** `WINDOW_RADIUS=8 / LOCAL_RADIUS=2 / R_same_line` 三经验常数在新语料重量测（§3.2）。
- **P4** 写明「F1 格式缺失 ≠ 语义错误」的处置口径：`COMPARABILITY_AUDIT.md:158` 被报 F1，而 `TAUTOLOGY_AUDIT.md:455` 判「措辞未升级为定理，风险低」——两者不矛盾，运维上 F1 只作「建议补两段式」。
- **P5** 复核回件按铁律绑定行格式登记 SHA256 + 字节数（§6.1 已照办）。

**挂哪个环节**：挂**成件后**、**只报不拒**；**不挂派发前**——派发前输入是任务书/口头措辞，M1–M5 形态未成形，且 `TAUTOLOGY_AUDIT.md:461` S16 记编排方三句旧措辞为**口头措辞**、两件台账 0 命中（`:607-608` 逐字「本次会话实跑在两件台账 **0 命中**」）；与 `TAUTOLOGY_AUDIT.md:547-549` §5.4 第 6 条「生成时禁用串断言」互补——那条**仍未实装**（`:549` 逐字「仍是提案、未实装」，本任务不改脚本），本门禁是其后的成件后 lint。

### 6.4 判不了什么（能力边界 + 工作边界）

- **能力边界**：§5.4 第 4 条的 11 类（字面门禁结构上限）+ F3 同行判据的邻行代价（§5.4 第 5 条）。
- **工作边界（本任务链判不了，逐条如实）**：
  - 真机运行态：铁律零真机 ⇒ `gamemd.exe`/`ra2loader`/`YURI.exe`、活进程内存一律**未验**（本件同：未启动、未 taskkill、未读内存、未写采样代码）。
  - X1 反例谓词直调：未重跑 `r12_scan` 对 `'已入账 grep 结果。不得不承认放行 N-5'` 的实跑；只复核 8 格穷举 + 74 行 JSON 并引用编排方【背景】与 `TAUTOLOGY_AUDIT.md:191-234` §2.5 ⇒ **未验（引用，未重跑）**。
  - 生产语料泛化与两条全称升级条件（`TAUTOLOGY_AUDIT.md:713,716-718` 逐字「① 代码级证明…② 证明 X1/X2/X3 类输入在生产契约下全部不可达 —— 本次会话**未做**」）⇒ **未验**；「恒等不是逻辑必然」不升格为「给定生产契约下是定理」。
  - `_gp_regression_out.json` 的生成过程：只以现盘 SHA `d3543657…` 对照，未重跑 `_gp_regression.py` ⇒ **未验**（`TAUTOLOGY_AUDIT.md:723-724` 同判）。
  - 两件台账其它论域措辞、k_eff 点值/bootstrap 重算（`TAUTOLOGY_AUDIT.md:721-722,728-729`）⇒ **未验**。
  - 精确率/召回率真值：无人工全量标注 ⇒ 只有估计（**估计非测量**）。
  - K6 145 条中是否含真违规 ⇒ **未验**。
  - 被检文档是否被改：本任务不改写；11 件编排方基线零漂移已验（`FINAL_MATCH = True`）；**其余 9 件被扫 `.md` 无外部基线**，未变性仅有检测器两轮实跑自记 SHA 一致的弱证据 ⇒ 对这 9 件**未验**（逐件外部对照缺基线）。
  - 实现员申报的量测逐数与「开发中 3 次自测失败」历史（§3.2/§3.4）⇒ **未验/无工件**。
  - 台账若纳入扫描的判定结果（GOAL 46 行「恒等」会否全走 K2）⇒ **未验**（从未运行）。

### 6.5 未验项清单（汇总）

1. 实现员窗口/局部半径量测逐数（958/3.0/42/[(0,32)…]/85%）——无留档，未复现；两级共同结论（max=8、±2 过半、经验值须重测）已验。
2. 「开发中 3 次自测失败」历史过程——无工件，仅终态 10/10 已验。
3. 复核员独立检测器 9/9 与 diffrows 45 行仲裁——复核员实跑，本件未重跑（脚本在写域，可复跑）。
4. 两件台账纳入扫描后的行为——从未运行。
5. 其余 9 件被扫 `.md` 的外部基线零漂移——无基线，弱证据。
6. X1/X2/X3 谓词直调、生产泛化、两条全称升级条件、`_gp_regression.py` 生成过程、k_eff 重算、两件台账其它论域——沿用上游未验记录（`TAUTOLOGY_AUDIT.md:711-729`）。
7. 精确率/召回率真值、K6 145 条内容、18 行「决定性集合等式」非 F3 行的逐行豁免裁决——未做。

---

*本件由撰写员（等式声明成件撰写员）于 2026-11-10 依【交付】六节要求写成；只读核验、唯一写域 `lead/eqdecl_gate_20261109/`、未 commit/push。复核 verdict = partial ⇒ 本件标 unconfirmed；本件自身未请求新一轮复核。*
