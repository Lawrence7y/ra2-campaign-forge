# WHITELIST_AUDIT.md — R9 白名单独立审查件（2026-11-09）

被核对象 SHA256 = 593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740，字节数 = 20271

（上行为严格格式绑定行：写「被核对象 SHA256 = 」紧跟完整 64 位十六进制，中间未插路径/括号/星号/反引号/空格；随后「，字节数 = 」+ 数字。绑定对象为只读件 `lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md`，本会话 `hashlib` 实算值见 §2.1。）

---

## 1 目的与边界

**目的**：对 R9 语义要素升级（`lead/gate_r9sem_20261109/GATE_R9_SEMANTIC_ELEMENT.md`）中「5 项翻案全部落在预先指定的白名单内 ⇒ 没放松」这一结论做独立审查。白名单是「预先指定的例外」；编排方在派发时已点明其风险是「**先把结果写进白名单，再证明结果落在白名单内**」，这是自证（本任务 payload `.zcode/workflow-runs/dwfrun-5e636329-…mjs` 的 IRON 第 9 条，实读 `_wlw_stepB_stdout.txt:32`）。本件不采信上一轮的语义论证，逐项自己读原文、自己跑比对、自己给独立裁决。

**边界（本会话实际做到的）**：

- 只做审查，**未改白名单、未改谓词、未改任何交付件**。判定「某条不该在白名单」只写结论与依据，不执行移除（payload `:89` 实读）。本会话未删除任何白名单项、未修改 `_r9s_regress.py:113-119` 的 `WHITELIST` 字面量、未修改 `_r9s_predicates.py` 的 `SPECS`。
- 零真机：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存。零采样代码：未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。
- 九件绝对只读件 + 两件台账 + `lead/gate_rejudge32_20261109/` 一律只读，未改、未追加、未覆盖；未跑 `_r9s_regress.py` 本体，因其 `lead/gate_r9sem_20261109/_r9s_regress.py:235-237` 会 `write_text` 覆写只读域的 `_r9s_regress_out.json`（本会话实读该行确认），改用自己在写域复算（`_wlw_stepC.py`）。
- 唯一写域 = `lead/whitelist_audit_20261109/`；本会话新增产物一律 `_wlw_` 前缀；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。
- 引用全部追到「本会话实跑命令 + 输出」或「文件:行」；拿不到的一律写「未验」，不补造。
- 本件按当前任务 payload `:89` 指定的文件名 `WHITELIST_AUDIT.md` 落盘。写域内另有一份上一轮审查员的 `_WL_WHITELIST_AUDIT.md`（52705 B，sha256 `f9d00b7c…adc`），本件不改动它，且并列登记为本会话的上游输入（§6.1 如实记命名差异，属复核回件登记的观察项，不在本任务范围内处理）。

**必现要素**在本件逐节落地：白名单（§2–§6）、自证（§4）、独立裁决（§3）、语义在场（§3 逐项）、部分满足（§3 逐项）、反事实（§5）、形式像实质空（§4.4/§5）、过宽（§5.4）、过窄（§5.4）、三分类（§6.3）、可信度（§6.5）、未验（§6.6）。

---

## 2 上游指纹（十件）+ 基线复核

### 2.1 十件只读指纹，`hashlib` 独立复算

命令（本会话实跑）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/whitelist_audit_20261109/_wlw_stepA.py > D:/Project/ra2-campaign-forge/lead/whitelist_audit_20261109/_wlw_stepA_stdout.txt
```

`EXIT=0`，输出 `_wlw_stepA_stdout.txt:1-12`（完整 64 位 + 字节数）：

| # | 只读件 | sha256（完整） | 字节数 | 与编排方指纹 |
|---|---|---|---|---|
| 1 | `lead/gate_r9sem_20261109/_r9s_regress_out.json` | `5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25` | 75673 | OK |
| 2 | `lead/gate_r9sem_20261109/_r9s_predicates.py` | `b0265fc57ef4facd06d92b4852344a80d983f14560a8521525ba18e533ae7034` | 23111 | OK |
| 3 | `lead/gate_r9sem_20261109/_r9s_DESIGN.md` | `5cae35256ec123687c6cbc47753ece3d417e0e33217005bdee0b1b47e322c95c` | 37988 | OK |
| 4 | `lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md` | `0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31` | 36851 | OK |
| 5 | `lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md` | `cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6` | 27825 | OK |
| 6 | `lead/n11_wording_fix_20261108/N11_WORDING_FIX.md` | `4ef31846050ef4e1506221c42354b61636701c37657e455c075a2e85f207f1b4` | 18966 | OK |
| 7 | `lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md` | `593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740` | 20271 | OK |
| 8 | `lead/gate_fp7_20261108/_g7_predicates.py` | `02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120` | 11743 | OK |
| 9 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 | OK |
| 10 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 | OK |

`readonly_10_unchanged = True`（`_wlw_stepA_stdout.txt:12`）。10/10 与【编排方指纹】逐位一致。绑定行取自第 7 件。

### 2.2 基线 32 域 / 302 项 / 翻案 5 / 白名单外 0 复现

命令（本会话实跑，独立实现，不 import `_r9s_regress.py`）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/whitelist_audit_20261109/_wlw_stepC.py > D:/Project/ra2-campaign-forge/lead/whitelist_audit_20261109/_wlw_stepC_stdout.txt
```

`EXIT=0`，输出 `_wlw_stepC_stdout.txt:1-10`：

```
POS 20/20  NEG 24/24  all_pass=True
n_domains=32 n_items=302 n_flips=5 outside=0 n_tightens=0 no_relaxation=True
   FLIP lead/matrix_ab_ruling_20261109/    需谁批准    whitelisted=True
   FLIP lead/matrix_reach_20261109/        实跑输出    whitelisted=True
   FLIP lead/n11_wording_fix_20261108/     改前改后    whitelisted=True
   FLIP lead/s604_script_gap_20261109/     脚本存在性  whitelisted=True
   FLIP lead/s604_script_gap_20261109/     可重建      whitelisted=True
```

交叉读派发指纹件 `lead/gate_r9sem_20261109/_r9s_regress_out.json`（只读）得 `ref_n_flips=5 / ref_outside=0 / ref_no_relaxation=true / ref_verdict=PASS`（本会话 `_wl_step1_stdout.txt` 同值，另由复核员 `_wlv_regress_stdout.txt:7-12` 独立复跑 `element_extractor_matches_ref=True / identical_flips=True`）。**302 / 5 / 0 三个数字复现**，且 `element_extractor_matches_ref=True`。

★ 复现本身不等于验证有效：`_r9s_regress.py:113-119` 的 `WHITELIST` 是硬编码 5 对；`:182-185` 给每个 flip 打 `whitelisted=(dom,k) in WHITELIST`；`:204-206` 的 `no_relaxation` 与 `:223-229` 的 `VERDICT` 只查「翻案集合 ⊆ 白名单 ∧ 数量相等」，**不含任何语义真值检查**。本会话复算用的是同一公式，所以复现的是同一公式，不是独立语义验证（§4 展开）。

### 2.3 正负样本完整清单（44 条逐条）

来源 `lead/gate_r9sem_20261109/_r9s_samples.py:85-195`（本会话实读全文）+ 本会话 `_wlw_stepC_out.json` 的 `samples.rows`（逐条 `expect/actual/layer/pass`）。上游 `_wl_step1_stdout.txt:1-47` 与本会话 `_wlw_stepC_stdout.txt:1-2` 同值：`POS 20/20 NEG 24/24 all_pass=True`。

**正样本 20 条（expect=True，本会话实跑 actual=True 全 20/20）**

| id | token | layer（实跑） | 形态（本会话独立归类，依据 `_r9s_samples.py:85-129`） |
|---|---|---|---|
| P01 | 需谁批准 | semantic | 真实案例 `RULING_MATRIX_AB.md:108` 的删节重述（非逐字） |
| P02 | 实跑输出 | semantic | 真实案例 `MATRIX_DEFECT_REACHABILITY.md:65-72` 的删节重述 |
| P03 | 改前改后 | semantic | 真实案例 `N11_WORDING_FIX.md:76/81/82/88/89` 的删节重述 |
| P04 | 脚本存在性 | semantic | 真实案例 `S604_SCRIPT_GAP.md:32/44/59/69-71` 的删节重述 |
| P05 | 可重建 | semantic | 真实案例 `S604_SCRIPT_GAP.md:73/77-83/87` 的删节重述 |
| P06 | 需谁批准 | semantic | 构造：换角色头「批准方」+ 赋值算子「：」 |
| P07 | 需谁批准 | semantic | 构造：被动式「由 X 批准」 |
| P08 | 需谁批准 | semantic | 构造：换「审批人 =」 |
| P09 | 实跑输出 | semantic | 构造：极简载荷围栏块 |
| P10 | 实跑输出 | semantic | 构造：内联数据行 |
| P11 | 实跑输出 | semantic | 构造：「本轮实跑 exit=0」+ 围栏块 |
| P12 | 改前改后 | semantic | 构造：换标签「原文/改为」 |
| P13 | 改前改后 | **raw** | 构造：标题自带 token，L0 短路 |
| P14 | 脚本存在性 | **raw** | 构造：标题自带 token，L0 短路 |
| P15 | 脚本存在性 | semantic | 构造：「结论：脚本不存在」 |
| P16 | 脚本存在性 | **raw** | 构造：正极性判定 + 标题自带 token，L0 短路 |
| P17 | 可重建 | semantic | 构造：换动作头「复现」 |
| P18 | 可重建 | semantic | 构造：「能重建」 |
| P19 | 实跑输出 | semantic | 构造：载荷含「未采集」字样（回归防线） |
| P20 | 需谁批准 | semantic | 构造：含条件句「若批准人不采随批」 |

★ P13/P14/P16 走 `raw`（`_r9s_predicates.py:412-424` L0 字面命中直接短路），**不检验语义层**；真正测到语义层的正样本是 17/20。

**负样本 24 条（expect=False，本会话实跑 actual=False 全 24/24）**

| id | token | 文本要点（`\n` 记为 ` | `） | 类别 |
|---|---|---|---|
| N01 | 需谁批准 | `## 5 清单 | 本次改动已批准，顺序不可倒。` | 近似缺关键信息 |
| N02 | 需谁批准 | `批准人：待指定。` | 近似缺关键信息（占位） |
| N03 | 需谁批准 | `批准人尚未确定，需进一步确认。` | 近似缺关键信息（待定） |
| N04 | 需谁批准 | `谁批准？此项待验。` | 近似缺关键信息 |
| N05 | 需谁批准 | `无需批准，直接登记。` | 近似缺关键信息（否定） |
| N06 | 实跑输出 | `构造输入 → 实跑返回：16/16 格实跑 | 结论详见见附件。` | 近似缺关键信息（★最关键：有 Run 无 Present） |
| N07 | 实跑输出 | `输出待补，见 _probe_out.txt:159-174 索引。` | 近似缺关键信息 |
| N08 | 实跑输出 | `## 1 目的 事件 | ## 2 证据 载荷`（跨小节） | 近似缺关键信息 |
| N09 | 实跑输出 | `输出未采集` 但围栏块有载荷 | 近似缺关键信息 |
| N10 | 实跑输出 | `PROBE_DONE 239 行，exit=0` 无返回值 | 近似缺关键信息 |
| N11 | 实跑输出 | `verdict='TBD' conf='待定'` | 近似缺关键信息（占位） |
| N12 | 改前改后 | 只有【改前】 | 近似缺关键信息 |
| N13 | 改前改后 | `【改前】略。【改后】略。` | 近似缺关键信息（占位） |
| N14 | 改前改后 | 两半分处 §4 / §5 | 近似缺关键信息（跨小节） |
| N15 | 脚本存在性 | `已查生成脚本，全树 .py 共 11790 个。` | 近似缺关键信息 |
| N16 | 脚本存在性 | `脚本是否在盘，待验。` | 近似缺关键信息 |
| N17 | 脚本存在性 | 极性在 §3、判定问句在 §4 | 近似缺关键信息 |
| N18 | 可重建 | `已分析算法，五重独立实现逐位一致。` | 近似缺关键信息 |
| N19 | 可重建 | `**不可重建**：口径唯一性不成立…` | 近似缺关键信息（否定） |
| N20 | 可重建 | `算法可重建，但确定性证据待补。` | 近似缺关键信息 |
| N21 | 可重建 | 情态 §4、证据 §5（跨小节） | 近似缺关键信息 |
| N22 | 实跑输出 | `批准人一律 = 乙设计责任人。`（另一 spec 的正例） | 明显不同（跨 spec 不串味） |
| N23 | `未改 _c7_selfcheck.py` | `本撰写会话未修改任何既有文件…` | 明显不同（未登记 token） |
| N24 | 需谁批准 | `改动清单列于下表…`（全文无批准语义） | 明显不同（真缺失原形态） |

逐条 `why` 原文见 `_r9s_samples.py:135-195`；44 条 `text` 全文见 `_wlw_stepC_out.json` 的 `samples.rows`（本会话实跑落盘）。

### 2.4 构造 vs 真实比例（本会话 AST 独立核验）

命令（本会话实跑）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/whitelist_audit_20261109/_wlw_stepD.py > D:/Project/ra2-campaign-forge/lead/whitelist_audit_20261109/_wlw_stepD_stdout.txt
```

`EXIT=0`，输出 `_wlw_stepD_stdout.txt:1-20`：

```
all_from_module_literals = True  not_literal_ids = []
POS 20/20 来自字面量 = True
NEG 24/24 来自字面量 = True
模块内是否出现文件读取调用 (read_text/open/read_bytes) = False
P01 whole_block_verbatim=False line_hits=2/3 why自称逐字=True
P02 whole_block_verbatim=False line_hits=6/9 why自称逐字=True
P03 whole_block_verbatim=False line_hits=3/8 why自称逐字=True
P04 whole_block_verbatim=False line_hits=6/7 why自称逐字=True
P05 whole_block_verbatim=False line_hits=3/7 why自称逐字=True
=> 真实交付件行 = 0/20（严格）；取材于真实案例但经删节重述 = 5/20（宽松 25%）；纯构造 = 15/20（75%）
近似但缺关键信息 = 21/24 = 87.5% ; 明显不同 = 3/24 = 12.5%
```

- **严格口径**：20/20（100%）正样本都是「为了证明升级有效而构造」的 `_r9s_samples.py` 内硬编码字符串字面量（AST 实算 `all_from_module_literals=True`、模块内 `read_text/open/read_bytes` 调用 = 0），**0 条是真实交付件的行**。P01–P05 的 `why` 自称「逐字」，但整块逐字比对 `whole_block_verbatim=False` 五条全同，逐行命中 2/3、6/9、3/8、6/7、3/7——是删节/改写重述。
- **宽松口径**：5/20（25%）取材于真实案例，15/20（75%）为纯构造变体（`_r9s_samples.py:98` 明写「构造变体」）。
- **负样本**：近似但缺关键信息 21/24 = 87.5%，明显不同 3/24 = 12.5%（N22/N23/N24）。其中 `NEG 中含现成守卫词/占位词 = 13/24`（`lead/gate_r9sem_20261109/_r9sv_extra_stdout.txt:3` 本会话实读），即与 `_r9s_predicates.py:86-92` 的 `PENDING_RE` / `PLACEHOLDER_RE` 共设计；本会话 `_wlv_numbers_stdout.txt` 的近似口径为 10/24，`_wlw_stepD_stdout.txt:24` 已如实分列两种口径，不混用。
- ⇒ 24/24 这个数字高估不放松性：作者自己的 44 条全过，但复核轮另造 7 条近似负样本只抓住 2 条（`_wl_step3_struct_stdout.txt`：`V1..V5 caught = 2/5 all_7_caught = 2/7`；复核员 `_wlv_misc_stdout.txt:(b)` 独立复跑同值）。这与白名单自证是同一问题的两个面。

---

## 3 五项白名单逐项独立裁决

**总方法**：不采信 `GATE_R9_SEMANTIC_ELEMENT.md` 的「5/5 语义在场」表，也不采信上一轮审查件的语义论证作为依据；本会话自己打开只读主件（§3 各行号原文）、自己解 `.zcode/workflow-runs/*.mjs` 的 `payload.lowered` 取任务书原文（命令 `python -I -X utf8 …/_wlw_stepB.py`，输出 `_wlw_stepB_stdout.txt`）、自己给独立判断。五项逐项给「原文逐字 + 任务书措辞 + 独立判断 + 部分满足检查 + 该不该保留」，不许用「已审查」概括。

### ① `matrix_ab_ruling / 需谁批准`

**(a) 交付件原文（逐字 + 上下文）**

- `lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md:108`：`### 5.2 可执行改动清单（★ 处方，未实施；批准人一律 = **乙设计责任人**，pf2:200；改后立即做登记 7/8，顺序不可倒）`
- `:138`：`若批准人不采随批：B 核心仍成立，但 **W2 必须在台账如实登记为未关闭**，不得声称已关闭。`
- `:223`：`6. **STATE_MATRIX.json:6 行**——O1′ 的文本层收容由改 2 的 :5 注记承担…可选加 carve-out 句属批准人裁量、非必需。`（本会话实读）
- `:235`：`1. 若批准人今日只批 :2 一行 → A 可先行作退路…`
- 本会话 `_wlv_misc_stdout.txt:(c)` 独立复跑：`需谁批准` 在该件出现 **0 次**；`批准人` 4 次（:108/:138/:223/:235）。

**(b) 任务书要求原文**（`.zcode/workflow-runs/dwfrun-db5bad08-…mjs`，`_wlw_stepB_stdout.txt:5-7` 实读）

- `[A_ruling:108]`：「第五步 给可执行改动清单。对选定方案，逐处给：文件路径、行号、原文逐字、改后逐字、**需谁批准**。另列出「确认不用改」的处所（如 V2:120）并给不改的依据。」
- `[A_ruling:157]`：「必现要素：A / B / W1 / W2 / O1 / 改动清单 / 原文逐字 / **需谁批准** / V2:120 / 不施行 / 未验。必须给逐处改动清单…」

**(c) 独立判断：语义在场吗 —— 是**

不靠「问答语义」的形式化论证，只看文本事实：任务书要的是「这批改动由谁批准」这一治理信息。`:108` 用赋值句 `批准人一律 = **乙设计责任人**` 给出可指名的施事，「一律」把它约束为唯一主体；`pf2:200` 是引用锚。`:138/:235` 以「若批准人不采随批」「若批准人今日只批 :2 一行」把该角色放进实际治理分支，`:223` 提「批准人裁量」。四处施事同一、无待定、无否定。⇒ wh-变量被具体施事回答，**语义在场**。

**(d) 部分满足检查**

- 「说了谁批准但没说批准什么」：≈不存在。`:108` 是 §5.2「可执行改动清单」标题，下辖 `:110/:120/:130/:140/:149/:158` 六处逐处改动，`:235` 明写「只批 :2 一行」的粒度；批准对象与批准人同段可定位。
- 「有实跑但没输出」：本项不适用。
- 可挑的：`:108` 是 `★ 处方，未实施` 语境，指定的是「未来若施行，谁批」，不是「已批准」。但任务书第五步要的就是清单里的「需谁批准」字段，不是「已获批准」，故不构成部分满足。
- 世界知识层（「乙设计责任人」实存与权限、`pf2:200` 锚可否回验）本会话**未验**（`GATE_R9_SEMANTIC_ELEMENT.md:328` 同口径），按纪律写「未验」，不补造。

**(e) 该不该保留**：**应保留**。若硬判「不在场」，`matrix_ab_ruling` 域会多报一条缺要素误报，且 `:235` 的分阶段批准条件成为无主语句。**只写结论，不执行移除。**

### ② `matrix_reach / 实跑输出`（★ 特别提醒项：围栏块是不是该要素的输出）

**(a) 交付件原文**

- `lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md:65`：`- **构造输入 → 实跑返回**：classify 直调，pre 八变体（None/{}/缺state/脏值/显式unknown/absent_confirmed/present/error）× read_error 两型（exists=None / exists=True），16/16 格实跑：`
- `:68`：`（_mr_probe1_out.txt:159, :169, :173-174 摘；16 格全同型）`
- `:69-71` 围栏块三行（逐字）：
  ```
    pre=None(未采集)      × read_error·exists=None -> verdict='post_read_error' conf='none' is_new=None pre_state='unknown'  [矩阵归属: :2]
    pre=absent_confirmed × read_error·exists=None -> verdict='post_read_error' conf='none' is_new=None pre_state='absent_confirmed'  [矩阵归属: 无行=O1 / exists=True 型被:6字面误claim=O1']
    pre=error          × read_error·exists=None -> verdict='post_read_error' conf='none' is_new=None pre_state='error'  [矩阵归属: :4=W2]
  ```
- `:74`：`- **落哪一行 / 与矩阵声称是否一致**：四未采集变体 × read_error 按 :2 匹配，矩阵声称 unknown，实码 post_read_error → **不一致，W1 错盖坐实**（16/16，out:159-174；…）`
- 同件 `:12`：「构造输入 → 实际调用候选函数 → 记录真实返回值 → 落到矩阵哪一行 → 与矩阵声称是否一致」；`:26` 记载本轮实跑命令与 239 行 `PROBE_DONE` 输出件。

**(b) 任务书要求原文**（`.zcode/workflow-runs/dwfrun-c482b235-…mjs`，`_wlw_stepB_stdout.txt:13-16` + `_wlw_stepD_stdout.txt:29` 实读）

- `[B_reach:93]`（**逐字**，本会话 `_wlw_stepD_stdout.txt:29` 实读）：`  要求：不许写「理论上可以」。要给出**实跑输出**：构造的输入字典 → 实际返回的 verdict/confidence → 落入矩阵哪一行 → 与矩阵声称的是否一致。`
  （本件按逐字引用；上一轮审查件 `:204` 把它改写成 `_实跑输出_` 并删「的」、删前缀，属省略改写冒充逐字，见 §6.1 复核登记缺陷②。）
- `[B_reach:130]`：「3 五处缺陷逐处可达性实证（构造输入 → 实跑返回 → 落哪一行 → 与矩阵声称是否一致，**附实跑输出**）」
- `[B_reach:132]`：「必现要素：W1 / W2 / O1 / O2 / W3 / 可达 / 不可达 / **实跑输出** / 触发条件 / 已实证 / 未验 / 未改任何文件。」

**(c) 独立判断：语义在场吗 —— 是，且围栏块确属该要素的输出、不是别的实验的输出**

不采信上一轮「单独『实跑返回』不算（N06/N07/N10 判 FAIL），靠围栏块满足输出」的转述，本会话独立锚回。命令 `python -I -X utf8 …/_wlw_stepC.py`（第 (6) 段）输出 `_wlw_stepC_stdout.txt:42-46`：

```
probe:157 = P1 W1：pre 全变体 × read_error → classify 实跑 verdict（矩阵 :2 声称 unknown）
delivery:69 == probe:159 ? True
delivery:70 == probe:169 ? True
delivery:71 == probe:173 ? True
```

`lead/matrix_reach_20261109/_mr_probe1_out.txt:157` 的区段标题是 `P1 W1：pre 全变体 × read_error → classify 实跑 verdict（矩阵 :2 声称 unknown）`，`:159-174` 是同一 P1 W1 实验的 16 行返回值（本会话实读）。交付件 `:65` 明写 `classify 直调，pre 八变体 × read_error 两型，16/16 格实跑`，`:68` 明写 `_mr_probe1_out.txt:159, :169, :173-174 摘；16 格全同型`。⇒ 围栏块三行与 `:65` 的事件是**同一次 classify 直调实验的输出载荷**，逐行 `==` 三处 True；不是 `:179-181` 的 P2 W2 实验、不是 `:187-203` 的 P3 O1 实验。载荷本身带具体值 `verdict='post_read_error' conf='none' is_new=None pre_state='unknown'`，是返回对象本身（不是 `exit=0` / `PROBE_DONE` / 行数这类元信息，也不是 `out:159-174` 指针）。`:74` 补齐「落哪一行 / 与矩阵声称是否一致」。⇒ 任务书四段链条全部在场，**语义在场**。

**(d) 部分满足检查**

- 「有实跑但没输出」：**不成立**（围栏块即输出，已锚回同源实验）。
- ★ 真部分：`:65` 声称 16/16 格，围栏块只摘 **3 行**（`:69-71`），另 13 行靠 `out:159-174` 索引。按任务书「不许用推理填充」的严格读法，正文展示是抽样而非全量。但 `:69-71` 覆盖 `pre=None / absent_confirmed / error` 三类且 `verdict` 同型，`:74` 明写「16/16」并引复核 45 格全表，`:26` 记载 239 行 `PROBE_DONE` 输出件在盘。⇒ 是「输出展示不完整 + 索引补全」，**不是「无输出」**；判为已交付、附索引，不判缺失。
- 本会话未重跑 `_mr_probe1.py`（零真机纪律 + 本任务只做审查）：载荷「真由该次实跑产生」本会话**未验**（`GATE_R9_SEMANTIC_ELEMENT.md:328` 同口径：文本在场 ≠ 世界事实）。

**(e) 该不该保留**：**应保留**（附「正文只摘 3/16 行、输出真实性未验」两条边界注记，不要求移除）。

### ③ `n11_wording_fix / 改前改后`

**(a) 交付件原文**

- `lead/n11_wording_fix_20261108/N11_WORDING_FIX.md:76`：`## 4 订正草案（改前/改后逐处对照）`
- `:81`：`- 【改前】本件按 **13 项分写**，与裁决列名一一对应，无缺漏、无新增：拆分只改颗粒度、不改内容。`
- `:82`：`- 【改后】本件按 **13 项分写**，与裁决列名逐项对应（其中「帧数/重复性/阈值论证」一项拆为 D-08/D-09/D-10 三维，故 11 项列名展开为 13 维），无缺漏、无新增：拆分只改颗粒度、不改内容。`
- `:83`：`- 【要点】只换「一一对应」→「逐项对应（…）」并插入拆分括注…`
- `:85-90` 方案 B 第二对：`:88` `- 【改前】同 §4.1【改前】`；`:89` `- 【改后】本件按 **13 项分写**：裁决列名共 11 项，其中「帧数/重复性/阈值论证」一项拆为 D-08/D-09/D-10 三维、其余 10 项逐项承接（11 = 10 + 1，13 = 10 + 3）；无缺漏、无新增，拆分只改颗粒度、不改内容。`；`:90` 要点。
- `:97`：`**三案均只处理 _ps:54 一句；13 维结构、维度内容、其余 368 行一律不碰。**`

**(b) 任务书要求原文**（`.zcode/workflow-runs/dwfrun-903e6b21-…mjs`，`_wlw_stepB_stdout.txt:29-30` 实读）

- `[C_n11:127]`：「4 订正草案（方案 A 最小改动 / 方案 B 改句式，各自**改前行号、原文、改后文**；承接件是否需要改的判定与依据；下游引用影响面）」；「**必须给逐处改前改后对照，不许写「建议修改相关表述」**」；「必现要素：… / **改前改后** / …」
- `[C_n11:116]`：「你是订正草案撰写员。逐处给改前改后对照，最小改动优先。不得声称已修改。」

**(c) 独立判断：语义在场吗 —— 是**

不采信「无分隔并列 = 逻辑合取」的论证，只看文本：`:76` 标题明写「改前/改后逐处对照」；`:81` 给完整改前原句、`:82` 给完整改后句，两者针对同一对象（`:80` 钉 `_ps:54 第二句`）且差异可逐字比对（「一一对应」→「逐项对应（…）」+ 括注）；`:88/:89` 给第二对；`:83/:90` 是差异要点；`:97` 收口。任务书要的「改前行号 + 原文 + 改后文 + 逐处对照」四件齐备。`:88` 写「同 §4.1【改前】」是指针，但 `:81` 同小节已给实值，不是空指针。⇒ **语义在场**。

**(d) 部分满足检查**

- 「改前改后并列但无对照」：**不成立**，`:76` 标题 + `:83` 要点 + `:97` 收口提供对照算子，两半实值齐备。
- 「说了谁批准但没说批准什么」：本域另有 `需谁批准` 字面 token（`:142` 标题、`:170` 小节），`:172` 明写「就地执行方案 A/B 须 _ps 的来源会话（规格撰写轮）或规格责任人批准」+ 同步刷新登记——施事与批准对象都在场（本会话实读 `:170-172`）。此要素在本域是 R9 `raw` 命中、未翻案（`_wl_step3_struct_stdout.txt`：`lead/n11_wording_fix_20261108/ 需谁批准 r9=True r9s=True whitelisted=False`），不构成白名单问题。
- 无「有实跑没输出」情形。

**(e) 该不该保留**：**应保留**。

### ④ `s604_script_gap / 脚本存在性`（★ 特别提醒项：判「不存在」算不算交付「存在性」）

**(a) 交付件原文**

- `lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md:32`：`## 3 脚本搜索全结果与存在性判定（四路逐路）`
- `:36`：`命令：find lead out/re_work -type f -name '*.py' | grep -iE '(gapdiff|gap_diff|s604|604|gap)'（全量计数另跑 … | wc -l）。`
- `:44`：`- **逐路结论：lead/ 与 out/re_work/ 均无 §604 生成器。**`
- `:51`：`- **逐路结论：32 件全为 2026-11-07 之后的复核/复算/锚点件，无一生成器。**`
- `:59`：`- **逐路结论：两轮上游产物均明载脚本未落盘。**`
- `:67`：`- **逐路结论：台账自身即证明脚本从未写入台账，亦未引用任何在盘脚本。**`
- `:69`：`### 3.5 存在性判定`
- `:71`：`**§604 生成脚本【不存在且从未落盘】**——四条独立证据链（文件名、内容、产物反查、台账实读）在本轮全部独立复跑/复读，方向一致，无一矛盾。`

**(b) 任务书要求原文**（`.zcode/workflow-runs/dwfrun-bc9d8b8e-…mjs`，`_wlw_stepB_stdout.txt:33-39` 实读）

- `[D_s604:137]`：「  给出确定结论：脚本存在 / 不存在 / 存在疑似但不确定。」
- `[D_s604:12]`：「★ 只查脚本存在性与可重建性，不重建台账数字、不改台账、不判台账该不该改。」
- `[D_s604:189]`：「必现要素：脚本存在性 / 可重建 / 自由度 / 单向压缩 / 候选 / 可证伪 / 假设非定谳 / 最小补充证据 / 未验。必须给四路搜索的逐路结果，不许用「搜索后未找到」概括。」

**(c) 独立判断：「不存在」算交付了「存在性」，语义在场 —— 是**

关键在任务书自己的措辞：`:137` 明写「给出**确定结论**：脚本存在 / **不存在** / 存在疑似但不确定」——「不存在」被**列为三种合法结论之一**。所以这个要素问的是「对命题 Exists(script) 的一项已决断判定」，不是「脚本存在」这个肯定命题。本会话实读：`:32` 标题含「存在性判定」；`:36` 起四路逐路各给命令与命中数（11790 / 20 / 237 / 32 / 台账围栏 0），`:44/:51/:59/:67` 四句逐路结论，`:69-71` 明写「存在性判定」+ 极性「【不存在且从未落盘】」+ 四条证据链方向一致。⇒ 判定已决断、极性为负但合法、四路逐路未被「搜索后未找到」概括。**语义在场**。

反过来：若读成「必须证明脚本存在」，则 `:71` 的否定答案会被判缺失——那与任务书 `:12`「若脚本确实不在盘且无法重建，如实说无法重建」的指令直接冲突，故不能这么读。

**(d) 部分满足检查**

- 「存在性待查」式部分满足：本件**不存在**。`:71` 无「待验/待查/以台账为准」等未决语；`:155` 的「原内联脚本本体：四路搜索均未获得 ⇒ 确切错误行未验」是**归因层**（§4.4/§5.3 的确切错误行），不是存在性层的未决——脚本「不存在」本身是已决断的。
- 「有实跑但没输出」：反向满足，四路都有命令 + 输出计数（`:36/:37/:48/:49/:63/:66`）。
- 唯一边界：`:32` 的字面串是「存在性判定」而非「脚本存在性」，`grep` 该件「脚本存在性」= 0 次（本会话 `_wlv_misc_stdout.txt:(c)` 独立复跑）；但这正是字面/语义之别，不是部分满足。

**(e) 该不该保留**：**应保留**。若硬判「不在场」，后果是把「如实报告不存在」误判成「没回答存在性」，逼出编造脚本，正是任务书明禁的。

### ⑤ `s604_script_gap / 可重建`

**(a) 交付件原文**

- `S604_SCRIPT_GAP.md:73`：`## 4 重建可行性与单向压缩候选筛选`
- `:75`：`### 4.1 正确算法：五项口径唯一性`
- `:77-83`：五项口径表（帧分组 / 空档定义 / 三分法 / edge vs span / floor vs ceil），每项给「唯一性」与「钉死证据」
- `:87`：`**判定：正确算法【可唯一重建】。** 已有四重独立实现逐位一致（N-8、R3 蓝本、`_verify_r3_gapdiff.py` 第三方、上轮探针 [0] 三窗逐位复现 R3 [B]，`_sg_probe_compression_out.txt:1-4`【实读】），复核轮另有第 5 重独立实现与 R3 [B] 逐位一致（max|Δ|=0.000000）【转述：复核回件】。`
- `:89-94`：`### 4.2 所需输入（全在盘、全只读、本轮转验）` 列 15 份语料 JSON / 台账表值常量 / 蓝本 `:3-7`+`:78-107` / 无外部依赖。
- `:111`：`**筛入唯一候选 = C8a（75/75 = 时长列 30 + 空档两列 30 + 差列 15）。**`
- `:115-116`：`确切错误行/微观码形【筛不出】`；`⇒ 假设非定谳：C8a 是充分性证明 + 75/75 数值等价，不是原脚本本体。`

**(b) 任务书要求原文**（`.zcode/workflow-runs/dwfrun-bc9d8b8e-…mjs`，`_wlw_stepB_stdout.txt:34-39` 实读）

- `[D_s604:139]`：「第二步 若不存在，判断能否重建。重建的前提是算法可唯一确定。逐项检查：(a) 台账 :9702-9703 的口径自述是否完整到能唯一确定算法…(b) `_r3_recompute_gapdiff.py:3-7` 的实现能否作为重建蓝本；(c) 重建需要哪些输入；(d) 重建结果能否用「已知事实」验证…」
- `[D_s604:144]`：「  给出判定：可唯一重建 / 可重建但有自由度 / 不可重建，并说明自由度具体在哪些参数上。」
- `[D_s604:189]`：「必现要素：脚本存在性 / **可重建** / …」；`[D_s604:12]`：「★ 若脚本确实不在盘且无法重建，如实说无法重建，不许为了给出答案而编造脚本内容或推测算法细节充数。」

**(c) 独立判断：语义在场吗 —— 是，但对象是「正确算法」而非「原脚本本体」**

任务书第二步的判定式是三选一「可唯一重建 / 可重建但有自由度 / 不可重建」，且 (a)-(d) 全在问「算法口径是否唯一、蓝本、输入、验证」。`:87` 明确答「正确算法【可唯一重建】」，(a) 由 `:77-85` 五项口径表逐一给唯一性/钉死证据，(b) 由 `:93` 给蓝本，(c) 由 §4.2 给 15 份语料 + 常量，(d) 由 `:82-83` 的 30/30 与 `:87` 的逐位一致 / `max|Δ|=0.000000` 给验证。⇒ 三选一的判定已作出且有证据，**语义在场**。

★ 本会话独立读出的边界（不是上一轮转述）：`:115-116` 明写「确切错误行/微观码形【筛不出】」「假设非定谳…不是原脚本本体」，`:155` 明写「原内联脚本本体：四路搜索均未获得」。所以「可唯一重建」的是**正确算法**（30/30 时长列 + 75/75 C8a 数值等价），**不是**当年那份内联脚本本体。任务书 (b) 自己就把 `_r3_recompute_gapdiff.py` 当「重建蓝本」问，故这一区分不推翻交付；但若把要素读成「原脚本可重建」，则该件是「不可重建」。任务书两处措辞（`:12`「若脚本确实不在盘且无法重建」vs `:144`「给出判定：可唯一重建」）本身有歧义——这是**上游任务书含糊**，不是交付件缺要素。按 (a)-(d) 的实质要求裁定：在场。

**(d) 部分满足检查**

- 「重建待验证」式部分满足：本件**不存在**。`:87` 是「判定：」不是「待判：是否…尚需核对」；`max|Δ|=0.000000`、30/30、75/75 是已给证据，不是「证据待补」。
- 「有实跑没输出」：`:87` 的四重独立实现中本轮**未重跑**（`:156` 明写「数值探针本轮未重跑：75/75、−114.8、C8b 11/30 等数字行为的依据 = 上轮实跑的在盘输出（本轮已逐行实读核对）+ 复核轮独立实现复现【转述】」）。这是一处真实的「证据为转述/实读而非本轮实跑」，但任务书第二步要的是「判定 + 口径检查」，按纪律如实记为本会话**未重跑、未验**，不补造；不构成「有实跑无输出」型部分满足。

**(e) 该不该保留**：**应保留**（附「对象为正确算法、非原脚本本体」与「本轮未重跑数值探针」两条注记）。若下游要把此条当「原脚本本体可重建」用，需补「重建对象」显式声明；`:115-116` 已有此意但未与 `:87` 同句绑定，判为边界注记，不升级为「需补证据」类移除。

### 3.6 五项独立裁决小结

| # | 白名单项 | 语义在场？ | 独立裁决 | 部分满足 | 该不该保留 |
|---|---|---|---|---|---|
| ① | matrix_ab_ruling / 需谁批准 | 是 | 独立读 `:108/:138/:223/:235` + 任务书 `[A_ruling:108]` | 「处方未实施」非缺失；乙实存 / `pf2:200` 未验 | **应保留** |
| ② | matrix_reach / 实跑输出 | 是（围栏块经本会话逐行 `==` 锚回 P1 W1） | 独立读 `:65/:69-71/:74` + `[B_reach:93]` | 正文只摘 3/16 行、13 行靠索引；输出真实性未验 | **应保留** |
| ③ | n11_wording_fix / 改前改后 | 是 | 独立读 `:76/:81-83/:88-90/:97` + `[C_n11:127]` | 无 | **应保留** |
| ④ | s604_script_gap / 脚本存在性 | 是（「不存在」是 `[D_s604:137]` 明列的合法确定结论） | 独立读 `:32/:44/:51/:59/:67/:69-71` | 无 | **应保留** |
| ⑤ | s604_script_gap / 可重建 | 是（对象 = 正确算法） | 独立读 `:73/:77-87/:89-94/:115-116` + `[D_s604:139]/:144` | 数值探针本轮未重跑；原脚本本体筛不出已明写 | **应保留** |

**5/5 应保留、0 应移除、0 需补证据（到需移除程度）**。★ 必须点明的分离：「5 条都应保留」是本会话**自读原文**所得，**不等于白名单机制有效**；当前回归没有做这一步（`_r9s_regress.py:204-206` 只查集合包含）。若当初派发方把任何一条假阳性写进白名单（或像 §4.4 那样 5 条全换），回归仍会报 PASS。结论：**这批白名单内容恰好是对的，但机制不能证明它对**。

---

## 4 白名单机制自证风险

### 4.1 用白名单验证「没放松」，这个验证有效吗 —— **无效（作为语义验证）**

实证链条（全部本会话实读/实跑）：

1. **白名单由派发方预置，且与结论同源**。原始 R9SEM 任务书 `.zcode/workflow-runs/dwfrun-8156bb52-…mjs` 本会话实读原句 `[E_r9sem:94]`：「**编排方已实跑确认这 5 处都是「语义在场、字面不匹配」**：交付件写的是「批准人一律 = 乙设计责任人」「构造输入 → 实跑返回」「改前/改后逐处对照」「存在性判定」「【可唯一重建】」…」（`_wlw_stepB_stdout.txt:51`）。同一文件 `[E_r9sem:45-49]` 把 `CASES` 硬编码为 5 个 (文件, token, 行号)；`_r9s_predicates.py:371-402` 的 `SPECS` 恰为这 5 键；`_r9s_regress.py:113-119` 的 `WHITELIST` 又硬抄同 5 对。⇒ **结论在派发时已写进题面**，SPECS 的表与白名单是按同一 5 条造的。这是自证的起点。
2. **验证公式只做集合包含**。`_r9s_regress.py:182-185` 给每个 flip 打 `whitelisted`；`:204-206` 的 `no_relaxation` = `len(outside)==0 ∧ len(flips)==len(WHITELIST) ∧ all(whitelisted)`；`:223-229` 的 `VERDICT` 再加 `samples.all_pass` 与「4 域剩余缺要素 = 0」。三者**不含任何「该 flip 的语义是否真在场」检查**。
3. **「白名单外 0」部分是结构性恒真，不是实证**。本会话 `_wlw_stepC_stdout.txt:12-18` 实算：302 项里 `SPECS` 的 5 个已登记 token 共出现 **10 次**；其中 5 次在白名单内（全部 `r9=False → r9s=True`），另 5 次（全是 `需谁批准`，在 `handoff_pack` / `matrix_row5` / `n11_wording_fix` / `text_fix_unified` / `v2_precision_fix`）`r9=True` 且已字面在场、白名单外但不可能翻案。其余 **292 项 token 未登记**（`n_items=302 registered=10 unregistered=292 distinct_unreg=232`），`_r9s_predicates.py:426-428` 明写 `R9S ≡ R9`（返回 `""`），**逻辑上不可能产生翻案**。⇒ 只要 SPECS 的键恰好等于白名单的 5 个 token，`flips_outside_whitelist` 必然为 0，与语义无关。
   - ★ 复核登记缺陷①（本会话 `_wlw_stepD_stdout.txt:26-28` 复验成立）：上一轮审查件 `_WL_WHITELIST_AUDIT.md:365/:448/:486` 三处写「297 项 token 未登记」，实算为 **292**。`297 = 302 − 5` 是「未翻案件数」（来自 `GATE_R9_SEMANTIC_ELEMENT.md:238` 的 `identical=297 changed=5`），被原样搬进新语境且用错分母。不影响核心结论（292 项同样 R9S≡R9、结构性不翻案），本件按 **292** 记。
4. **正/负样本也是同一作者为自己判据写的**（§2.3/§2.4）：44/44 条全部为 `_r9s_samples.py` 内硬编码字面量、0 条读自真实主件、13/24 负样本含共设计守卫词；不是独立第三方语料。

⇒ 「白名单外 0 / no_relaxation=True / VERDICT=PASS」验证的是「翻案集合与预置白名单这两个**同源集合相等**」，不是「5 条语义真在场、真缺失未被放过」。**自证循环成立**：先把结果写进白名单，再证明结果落在白名单内。

### 4.2 有效的验证应该长什么样

- **白名单来源独立**：由不参与被测系统设计、不参与派发的第三方（独立裁定组 / 独立标注员）从任务书原文与主件原文出发，先给「哪些 (域, 要素) 是真误报、哪些是真缺失」的**盲标注**，标注时不知道 R9S 会翻哪些项；白名单 = 盲标注结果，不是 SPECS 的键表。
- **预注册 + 封印**：白名单在跑回归**之前**以 `hashlib` 指纹封印（含标注理由、标注员、时间），回归脚本只能读封印值，不得由被测系统作者修改；判据作者不得同时是标注员。
- **验证对象换位**：回归不检查「flips ⊆ 白名单」，而检查「**对每一个 flip，独立裁定其语义是否真在场**」；`no_relaxation := ∀flip: independent_truth(flip) == True`，而非 `∀flip: flip ∈ WHITELIST`。
- **双盲 + 反例注入**：正负样本由第三方构造并混入被测系统未知的自然措辞；至少包含「形式像而实质空」的对抗样本，判定阈值（全部抓住）预先注册。
- **分离两种失败**：把「白名单集合错」与「判据把真缺失判在场」分开报；前者报 `whitelist_invalid`，后者报 `relaxation_detected`。当前公式把两者混成一个布尔。

### 4.3 「白名单不可自证」的替代方案（不执行）

**方案：独立真值表 + 逐项对抗回归（Truth-Table Gating）**

1. 第三方对每个 (域, token) 项预注册三值真值 `T ∈ {PRESENT, ABSENT, UNVERIFIABLE}`，附 `file:line` 原文锚与理由，封印 SHA256。
2. 判据输出对每个项给 `(present, layer, evidence[])`；门禁对**全部 302 项**比对 `present == (T==PRESENT)`，任何不一致即 FAIL（不再用「白名单」概念，改用「逐项真值」）。
3. 对每个 `T==PRESENT` 的项，另注入一组由第三方构造的「保留表层结构、抽走关键语义值」的对抗变体（指针值 / 未决问句 / 自然否定 / 占位 / 跨小节），要求判据**全部判 ABSENT**；抓不住即 FAIL。
4. `T==UNVERIFIABLE` 的项不参与 PASS 统计，单列报「未验」，不许用 `no_relaxation=True` 掩盖。
5. 白名单若仍需存在，只能是「已登记为 UNVERIFIABLE 的暂挂清单」，且**不得参与 PASS 计算**；缩小/扩大由第三方裁定，不由判据作者改。

（本会话不执行改法；按纪律只给方案，见 §6.4。）

### 4.4 「1 条错时回归仍报 PASS」推演 + 可执行反例

命令（本会话实跑，复刻 `_r9s_regress.py:204-206/:223-229` 公式）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/whitelist_audit_20261109/_wlw_stepC.py > D:/Project/ra2-campaign-forge/lead/whitelist_audit_20261109/_wlw_stepC_stdout.txt
```

输出 `_wlw_stepC_stdout.txt:34-40`：

```
=== (5) selfproof (all 5 replaced with semantically-empty text) ===
   FLIP lead/matrix_ab_ruling_20261109/    需谁批准    semantic_empty=True
   FLIP lead/matrix_reach_20261109/        实跑输出    semantic_empty=True
   FLIP lead/n11_wording_fix_20261108/     改前改后    semantic_empty=True
   FLIP lead/s604_script_gap_20261109/     脚本存在性  semantic_empty=True
   FLIP lead/s604_script_gap_20261109/     可重建      semantic_empty=True
n_flips=5 outside=0 no_relaxation=True VERDICT=PASS
one-wrong cases (whitelist unchanged): 需谁批准=PASS, 实跑输出=PASS, 改前改后=PASS, 脚本存在性=PASS, 可重建=PASS
remove 1 whitelist item -> outside=1 no_relaxation=False VERDICT=FAIL
add 1 whitelist item    -> outside=0 no_relaxation=False VERDICT=FAIL
```

- **1 条错（自证场景）**：错条仍在白名单内、谓词仍把它判 True ⇒ `flips=5`、`outside=0`、`len(flips)==len(WHITELIST)`、`all(whitelisted)`、样本 `all_pass=True` ⇒ `VERDICT = PASS`。**5 种错法 5/5 全部仍 PASS**（上游 `_wl_step34_stdout.txt` 情形 B / C、复核员 `_wlv_counterfactual_stdout.txt:(D1)` 同值）。回归没有任何机制查看该条原文或语义。
- **决定性反例**：本会话只在内存中把 5 个白名单项的主件文本替换成「**形式像而实质空**」片段（与 `_wl_selfproof.py:21-32` 同串：① `批准人一律 = **见台账登记**`；② `verdict='详见台账' conf='none'`；③ 【改后】指针「改后句见方案 B 的对应行，本件不重录」；④ 「【不存在且从未落盘】（以台账记载为准，本件不另下结论）」；⑤ 「**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。**」），不改任何盘上文件，按同一公式重算 ⇒ `n_items=302 n_flips=5 outside_whitelist=0 no_relaxation=True VERDICT=PASS`。**5 条全错，回归照样 PASS**。上游 `_wl_selfproof_stdout.txt`、复核员 `_wlv_counterfactual_stdout.txt:(D2)` 独立复跑同值。
- 移除 1 项 / 多加 1 项才 FAIL，FAIL 理由是「集合不等」，**不是**发现语义缺失。⇒ 公式只在「集合数量/包含」变化时敏感，对「集合内容真假」完全不敏感。**自证循环得到可执行证明**。

---

## 5 反事实检验（5 条「形式像而实质空」构造样本）

### 5.1 五条构造样本（逐条给原文）

本会话 `_wlw_stepC.py` 第 (4) 段定义 CF1–CF5（撰写人原样）+ WCF1–WCF5（我另措辞，避免只验一套），逐条跑 `R9.r9_element_present` 与 `R9S.r9s_element_present`。CF 文本逐字：

| id | 形态（任务书 `[F_this:135]` 点名） | token | 构造文本（逐字） |
|---|---|---|---|
| CF1 | 批准人待定 | 需谁批准 | `## 5 改动清单\n批准人待定，需谁批准尚需确认，顺序不可倒。\n` |
| CF2 | 实跑已做但无输出数据 | 实跑输出 | `## 3 可达性\n- 构造输入 → 实跑返回：16/16 格实跑，输出数据待补。\n- 结论详见后续附件。\n` |
| CF3 | 改前改后并列但无对照 | 改前改后 | `## 4 订正草案（改前/改后逐处对照）\n- 【改前】本件按 13 项分写，与裁决列名一一对应，无缺漏、无新增。\n- 【改后】改后句见方案 B 的对应行，本件不重录。\n` |
| CF4 | 存在性待查 | 脚本存在性 | `## 3 搜索\n脚本存在性待查，本件不另下结论。\n` |
| CF5 | 重建待验证 | 可重建 | `## 4 重建可行性\n**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。**\n五项口径表见上节。\n` |

WCF 逐字（我另措辞）：`WCF1 = "## 5 改动清单\n本次改动的批准人尚未确定，由谁批准仍需后续确认。\n"`；`WCF2 = "## 3 可达性\n16/16 格已实跑完成，返回值详见附件，正文未列出。\n"`；`WCF3 = "## 4 订正草案\n【改前】详见台账登记。\n【改后】见台账登记，本件不重录。\n逐处对照表另附。\n"`；`WCF4 = "## 3 判定\n该脚本是否在盘，以台账记载为准，本件不另下结论。\n"`；`WCF5 = "## 4 重建可行性\n是否【可唯一重建】尚需核对，本件暂不作判定。\n五项口径表见上节。\n"`（全文亦存 `_wlw_stepC_out.json` 的 `counterfactual`）。

### 5.2 逐条实跑结果 + 是否被误判

命令同 §4.4（`_wlw_stepC.py`），输出 `_wlw_stepC_stdout.txt:20-32`：

```
CF1   需谁批准    R9=True/raw       R9S=False/(none)    misjudged=False
CF2   实跑输出    R9=False/(none)   R9S=False/(none)    misjudged=False
CF3   改前改后    R9=False/(none)   R9S=True/semantic   misjudged=True
CF4   脚本存在性  R9=True/raw       R9S=False/(none)    misjudged=False
CF5   可重建      R9=False/(none)   R9S=True/semantic   misjudged=True
WCF1  需谁批准    R9=False/(none)   R9S=False/(none)    misjudged=False
WCF2  实跑输出    R9=False/(none)   R9S=False/(none)    misjudged=False
WCF3  改前改后    R9=False/(none)   R9S=False/(none)    misjudged=False
WCF4  脚本存在性  R9=False/(none)   R9S=False/(none)    misjudged=False
WCF5  可重建      R9=False/(none)   R9S=True/semantic   misjudged=True
CF misjudged = 2/5   ids=['CF3', 'CF5']
WCF misjudged = 1/5  ids=['WCF5']
```

| id | R9 | R9S | 是否被误判在场 |
|---|---|---|---|
| CF1 | True/raw | **False**/none | 否（承诺守卫收紧；走 L0 短路，非语义层判对） |
| CF2 | False | **False**/none | 否 |
| CF3 | False | **True/semantic** | ★**是**：`evidence` 把指针「改后句见方案 B 的对应行，本件不重录。」当成 `After(t)` 实值 |
| CF4 | True/raw | **False**/none | 否（承诺守卫收紧） |
| CF5 | False | **True/semantic** | ★**是**：把「待判…是否…尚需核对」未决问句里的 `【可唯一重建】` 当成肯定情态 |
| WCF1–WCF4 | — | False | 否 |
| WCF5 | False | True/semantic | ★是（另措辞仍误判，集中在 S5） |

**结论：作者原样 5 条中 2 条被误判在场（CF3/CF5，40%）；我另措辞 5 条中 1 条被误判（WCF5）。** 与上游 `_wl_step34_stdout.txt`、`_wlv_misc_stdout.txt:(a)`、`_wlv_counterfactual_stdout.txt:(D3)` 一致（复核员另措辞 WCF1–WCF5 得 2/5，措辞不同故数字不同，两者都显示 S5 稳健性不足；本会话两套都实跑，如实分列，不互相冒充）。复核轮 V1–V7 独立复跑 `V1..V5 caught = 2/5 all_7_caught = 2/7`（`_wl_step3_struct_stdout.txt`、`_wlv_misc_stdout.txt:(b)` 同值），漏抓 V2/V3/V5/V6/V7。

**根因（本会话实读 `_r9s_predicates.py`）**：`:256-265` `_labeled_values` 只查长度 ≥10 与 `PLACEHOLDER_RE` / `_pending`，**不拒绝「见/参见/不重录」指针**；`:86-89` `PENDING_RE` 无「待判 / 是否 / 尚需」；`:412-424` L0 raw 命中直接短路（V7 漏抓）。⇒ 判据用**黑名单校验值**而非正面证据校验，是自己负责的小面上偏宽。

### 5.3 过宽 / 过窄平衡评估

- **过宽（形式像而实质空被判在场）**：**成立**。证据三条：① 本任务 CF 5 条对抗样本 2 条误判（40%），另措辞 WCF 1/5 误判；② 复核轮 7 条近似负样本只抓 2 条（`2/5`、`2/7`）；③ 撰写人 24 条负样本中 13/24 含与守卫词表共设计的词（`_r9sv_extra_stdout.txt:3`），故 `24/24` 高估稳健性。⇒ 升级在 S3（改前改后）/ S5（可重建）两个 spec 上**过宽**。
- **过窄（合法语义在场被判缺失）**：**成立**。`SameSection ∧ Gap≤8 ∧ 闭合 SPECS` 使「输出在附件文件里、正文只给指针」的合法形态被判缺失（`GATE_R9_SEMANTIC_ELEMENT.md:329` 自记 N08/N21 按缺失判）。本会话 §3② 也看到真实交付件 `matrix_reach` 正文只摘 3/16 行、13 行靠 `out:159-174` 索引——它恰好在正文留了 3 行载荷才过，正处在「过窄」边界上。
- **净评**：**整体窄、局部宽**。292 项 token 未登记 ⇒ R9S≡R9（结构性不动），把「放松面」钉得很小；但已登记的 5 个 token 内，判据用黑名单校验值而非正面证据 ⇒ 反而在自己负责的小面上过宽。★ 白名单机制恰好只覆盖那 5 个局部，所以对「局部过宽」毫无检出能力——这与 §4 的自证循环是同一个结构缺陷的两面。对预置 5 条真实例，本会话独立裁决 5/5 语义在场（§3），不过宽也不过窄；但这一结论来自**人工独立读原文**，不是机制证明。

---

## 6 复核回件 + 三分类结论 + 机制改法 + 可信度 + 未验

### 6.1 复核回件（如实记 verdict）

- **复核 verdict = `confirmed`**（【复核】回件原值）。按任务 payload `[F_this:177]` 的规则「复核 verdict 如实记；refuted 或 partial 标 unconfirmed」，本次为 `confirmed`，**不标 unconfirmed**。八项指定复核全部通过、无 refuted 触发；复核员 `ranCommands=20`。
- **复核回件绑定行（严格格式，如实抄录）**：

被核对象 SHA256 = 593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740，字节数 = 20271

（与本文首行同值；本会话 `_wlw_stepA_stdout.txt:8` 独立 `hashlib` 复算，字节数 20271；严格格式自检见 §6.7。）

- **复核登记的两处次要缺陷（本会话 `_wlw_stepD.py` 独立复验成立，如实登记，不改写被核件）**：
  1. **数字错误**：被核报告 `_WL_WHITELIST_AUDIT.md:365/:448/:486` 三处写「297 项 token 未登记」，本会话实算 **292**（`_wlw_stepC_stdout.txt:13`：`n_items=302 registered=10 unregistered=292 distinct_unreg=232`；复核员 `_wlv_regress_stdout.txt`、`_wlv_numbers_stdout.txt` 同值）。`297 = 302 − 5` 是「未翻案件数」，来自 `GATE_R9_SEMANTIC_ELEMENT.md:238` 的 `identical=297 changed=5`，被搬进新语境用错分母；作者自己的 `_wl_step3_struct_stdout.txt:3` 写「已登记 token 共 10 次」却接「⇒ 297 个未登记」，内部矛盾。不影响核心结论，本件按 292 记（§4.1）。
  2. **引文保真**：被核报告 `:204` 标作「任务书要求原文」的 matrix_reach 第二步，与 payload 真实原文不一致。本会话 `_wlw_stepD_stdout.txt:29` 实读 `[dwfrun-c482b235:93]` 逐字为 `  要求：不许写「理论上可以」。要给出**实跑输出**：构造的输入字典 → 实际返回的 verdict/confidence → 落入矩阵哪一行 → 与矩阵声称的是否一致。`；报告改写为 `_实跑输出_`、删「不许写…」前缀、掉一「的」字，属省略改写冒充逐字。本件 §3②(b) 按逐字引用，**不推翻 ② 裁决**（§3②(c) 独立锚回仍成立）。
- **复核员透明性说明（如实转记）**：其首版整篇 `ast.parse` 提取器因 `GATE_CODE` 含 JS 拼接行非合法 Python 而失败（输出 `n_items=0`），用 `_wlv_debug_extract.py` 定位后改行式解析成功；未跑 `_r9s_regress.py` 本体（`:235` 会覆写只读域），改用自实现 `_wlv_regress.py` 达成 32 域/302 项复核。**本会话同样经历一次提取器失败**：`_wlw_stepC.py` 首版用宽松 `for … in [..]` 行式解析得 `n_items=601`（把非门禁列表也收进来），改用与被测脚本同构的 `LOOP_RE`（`_r9s_regress.py:73-76`）后得 `n_items=302`；首版输出被覆盖，最终 `_wlw_stepC_stdout.txt` 为 302 版本。如实登记，不隐瞒。
- **另记不在本任务范围的观察（复核员登记，本会话 `_wlw_stepD_stdout.txt:33-36` 复验）**：原任务 payload 门禁查 `WHITELIST_AUDIT.md`（`[F_this:185]`），而写域已有的是 `_WL_WHITELIST_AUDIT.md`；本会话按 `:89` 指定名 `WHITELIST_AUDIT.md` 落盘，未处理命名差异本身（只审查，不改任何交付件）。

### 6.2 五项白名单三分类结论（保留 / 移除 / 需补证据）

| # | 白名单项 | 三分类 | 独立依据（本会话） |
|---|---|---|---|
| ① | `matrix_ab_ruling / 需谁批准` | **应保留** | `RULING_MATRIX_AB.md:108/:138/:223/:235` 实读；`[A_ruling:108]/:157` 任务书实读；语义在场 |
| ② | `matrix_reach / 实跑输出` | **应保留** | `MATRIX_DEFECT_REACHABILITY.md:65/:69-71/:74` 实读；`_mr_probe1_out.txt:159/169/173` 逐行 `==` True；`[B_reach:93]` 逐字 |
| ③ | `n11_wording_fix / 改前改后` | **应保留** | `N11_WORDING_FIX.md:76/:81-83/:88-90/:97` 实读；`[C_n11:127]` 实读 |
| ④ | `s604_script_gap / 脚本存在性` | **应保留** | `S604_SCRIPT_GAP.md:32/:44/:51/:59/:67/:69-71` 实读；`[D_s604:137]`「给出确定结论：脚本存在 / 不存在 / 存在疑似但不确定」 |
| ⑤ | `s604_script_gap / 可重建` | **应保留** | `S604_SCRIPT_GAP.md:73/:77-87/:89-94/:115-116` 实读；`[D_s604:139]/:144` 三选一判定 |

**应保留 5 / 应移除 0 / 需补证据 0（到需移除程度）**。②⑤ 的「展示不全 / 未重跑数值探针 / 对象为正确算法非原脚本本体」记作**边界注记与本会话未验项**，不升级为「需补证据」。★ 判定「某条不该在白名单」只写结论与依据，**不执行移除**；本会话 0 项判不该在白名单，故无移除动作。

**若应移除某项（反事实，不执行）**：以 ① 为例，`matrix_ab_ruling` 域真实状态仍是「`需谁批准` 语义在场、字面缺」，R9 继续报 1 条缺要素误报、R9S 仍翻案但变 `whitelisted=False` ⇒ `outside_whitelist=1`、`no_relaxation=False`、`VERDICT=FAIL`（`_wlw_stepC_stdout.txt:39` 移除 1 项、`_wl_step34_stdout.txt` 情形 A）——**FAIL 的理由是集合不等，不是语义错**，恰好再次证明公式与语义脱钩。其余 4 域同型。

### 6.3 白名单机制改法建议（不执行）

同 §4.2/§4.3，四条具体（**只给方案，不实施、不改白名单/谓词/交付件**）：

1. `WHITELIST` 不得与 `SPECS` 同源：判据作者不得写白名单；白名单由第三方盲标注、单独签名并以 SHA256 预注册封印，回归脚本先验封印再读。
2. `VERDICT` 拆成 `whitelist_integrity` / `flip_semantics` / `adversarial_robustness` 三个独立布尔，任一 False 即 FAIL；不再用单一 `no_relaxation` 掩盖；`no_relaxation := ∀flip independent_truth(flip)`。
3. 对全部 302 项用第三方逐项真值表比对；`T==UNVERIFIABLE` 单列「未验」，不参与 PASS。
4. 把 `V1..V7`、`CF1..CF5`、`WCF1..WCF5` 这类「形式像而实质空」样本纳入**必跑回归**，并为 S1/S3/S5 的值加「正面证据校验」（拒绝 `见/参见/详见/以…为准/不重录` 指针，收入 `待判/是否/尚需/并非/不另下结论`）。属收紧方向，本会话不实施。

### 6.4 R9 升级整体可信度评估 —— **部分可信**

| 维度 | 评级 | 理由（本会话证据） |
|---|---|---|
| 数字复现 | 可信 | 32 域 / 302 项 / 翻案 5 / 白名单外 0、`POS 20/20 NEG 24/24`、10 件指纹，本会话 `_wlw_stepC_stdout.txt:1-10`、`_wlw_stepA_stdout.txt:1-12` 全部独立复现 |
| 5 条白名单内容 | 可信 | 本会话不采信上一轮、自读 4 主件原文 + 解 4 份任务书 payload + 自跑逐行 `==`，5/5 独立判语义在场（§3） |
| 「没放松」的证明 | **不可信** | 白名单由派发方预置且与 SPECS 同源（`[E_r9sem:94]`）；`no_relaxation` 只查集合包含（`:204-206`）；292 项结构性不可能翻案；5 条全换「形式像而实质空」仍 `VERDICT=PASS`（`_wlw_stepC_stdout.txt:34-40`） |
| 正负样本集 | 部分可信 | 44/44 复现，但 20/20 正样本全为作者硬编码构造文本（0 条真实主件行，`_wlw_stepD_stdout.txt:1-20`）、13/24 负样本含共设计守卫词；第三方 7 条近似负样本只抓 2/7 |
| 判据稳健性 | 部分可信 | CF 5 条对抗样本 2 条误判（CF3/CF5）、另措辞 WCF 1/5 误判（WCF5）；S3/S5 用黑名单校验值非正面证据；`GATE_R9_SEMANTIC_ELEMENT.md:317` 自记复核 `partial ⇒ unconfirmed`、`:352-354` 记多项未验 |
| 上游任务书 | 部分含糊 | ⑤ 的「可重建」在「原脚本本体」与「正确算法」之间有歧义（`[D_s604:12]` vs `:144`），交付件 `:115-116` 已自行澄清 |

**总评：部分可信。** 可采信的是「这 5 处确实是语义在场、字面缺的真误报」和「升级在预置语料上数字可复现」；**不可采信**的是「白名单外 0 ⇒ 没放松」这一推论，以及「24/24 负样本 ⇒ 对真缺失仍 FAIL 无条件成立」。按 `GATE_R9_SEMANTIC_ELEMENT.md:317` 自身口径（复核 partial ⇒ unconfirmed），本会话独立结论：**升级本身 `unconfirmed`（局部过宽已实证），白名单验证机制 `invalid`（自证循环已用可执行反例证明）**。★ 复核 verdict 为 `confirmed` 是针对「被核审查件如实、八项复核通过」，**不改变**上述整体可信度评级；复核回件本身亦登记了两处次要缺陷（§6.1）。

### 6.5 未验 / 未做（如实，不补造）

1. 未重跑 `_mr_probe1.py` / `_mrv_probe1.py` / `_sg_probe_compression.py` / `_sg_probe_shift.py`：`:69-71` 载荷、75/75、−114.8 等只作**文本在场与同源逐行比对**，其「真由该次实跑产生」本会话**未验**（零真机纪律 + 本任务只做审查）。
2. `pf2:200`（① 的引用锚）、「乙设计责任人」实存与权限、`_r3_recompute_gapdiff.py` 蓝本内容：本会话未打开核对，标**未验**。② 的输出真实性、⑤ 的数值探针本轮重跑，均**未验**。
3. 43 处 `check_deliverable` 下游逐一执行、36 处历史 payload 改动、35 处历史门禁实跑输出：沿用 `GATE_R9_SEMANTIC_ELEMENT.md:352-354` 的「未验」，本会话未补。
4. 未跑 `_r9s_regress.py` 本体（`:235-237` 会覆写只读域 `_r9s_regress_out.json`，违反绝对只读）；改用本会话 `_wlw_stepC.py` 在写域复算，规模同为 32 域 / 302 项。**这不是「跑回归本体」，如实记为替代实现。**
5. 未写任何 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析；未启动 gamemd.exe / ra2loader / YURI.exe；未 taskkill；未读活进程内存；未 commit、未 push；未做远端查询（git HEAD 未变，见 §6.7）。
6. **未改白名单、未改谓词、未改任何交付件**：收尾 `readonly_10_unchanged = True`（§6.7 复跑）；`_r9s_regress_out.json` 仍为 `5bfb169a…5e25 / 75673`，未被本会话覆盖。
7. **本会话未处理**的观察项：写域已有 `_WL_WHITELIST_AUDIT.md` 与本件 `WHITELIST_AUDIT.md` 的命名差异（§6.1）；两件并列、均未改动。

### 6.6 本会话产物（全部落唯一写域，前缀 `_wlw_`）

| 文件 | 作用 |
|---|---|
| `WHITELIST_AUDIT.md` | 本交付件（六节 + 严格格式绑定行） |
| `_wlw_stepA.py` / `_wlw_stepA_stdout.txt` | 10 件只读指纹 `hashlib` 复算 + 任务书 payload 元数据 |
| `_wlw_stepB.py` / `_wlw_stepB_stdout.txt` / `_wlw_payloads.json` | 解 6 份 `payload.lowered`，取五项任务书要求原文（含 `[F_this:89]/:177` 交付规格） |
| `_wlw_stepC.py` / `_wlw_stepC_stdout.txt` / `_wlw_stepC_out.json` | 独立 32 域/302 项复算、292 数字、CF/WCF 反事实、自证反例、围栏块逐行 `==` |
| `_wlw_stepD.py` / `_wlw_stepD_stdout.txt` / `_wlw_stepD_out.json` | 样本构成 AST 核验 + 复核两处缺陷独立复验 + 交付件命名核验 |
| `_wlw_gate.py` / `_wlw_gate_stdout.txt` / `_wlw_final_stdout.txt` | 收尾门禁同款自检 + 10 件只读指纹复算 |

### 6.7 收尾自检（本会话实跑）

命令（本会话实跑）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/whitelist_audit_20261109/_wlw_stepA.py > D:/Project/ra2-campaign-forge/lead/whitelist_audit_20261109/_wlw_final_stdout.txt
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/whitelist_audit_20261109/_wlw_gate.py > D:/Project/ra2-campaign-forge/lead/whitelist_audit_20261109/_wlw_gate_stdout.txt
```

`A_EXIT=0 G_EXIT=0`。`_wlw_final_stdout.txt:12` = `readonly_10_unchanged = True`；`_wlw_gate_stdout.txt:1` 输出含 `ok = true / problems = [] / bindings = 2 / strict_bindings = 2 / readonly_5_drift = []`。即：六节齐全、十一必现要素齐全、越权断言 0、严格格式绑定行 2 处（首行 + §6.1 复核绑定行，≥1 即合规）、10/10 与编排方指纹逐位一致、5 件门禁漂移检查为空。（`docBytes` / `doc_sha256` 为被核件自身字节数与指纹，随本段文字变动而自指，此处不引用具体数值；需要时以 `_wlw_gate_stdout.txt` 当次输出为准。）透明性：`_wlw_gate.py` 首版有重复 `else` 语法错（`G_EXIT=1`），修正后重跑得上述 `ok=true`；如实登记。

---

全程零真机、零采样代码、只读件零改动、不 commit、不 push。**只做审查，未改白名单、未改谓词、未改任何交付件。**
