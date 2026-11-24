# C07_GATE_G1_G5_FIX.md — C07 门禁 G1–G5 修补报告

- 角色：G1G5 报告撰写员（本工作流撰写轮）
- 日期：2026-11-09
- 被核交付件：`lead/c07_gate_fix_20261109/_f3_c7check.py`（增强版校验器，33118 字节）
- 报告输出件：`lead/c07_gate_fix_20261109/C07_GATE_G1_G5_FIX.md`（本件，唯一写域内）
- 环境约束：零真机（未启动任何游戏进程）、零采样代码、不 commit 不 push、原门禁与全部保护件绝对只读。本报告全部结论来自本次会话亲手实跑（命令与输出随文引用）或实读文件（`文件:行` 引用）。

---

## 1 目的与边界

**目的**：审计件 `lead/c07_gate_audit_20261109/C07_SELFCHECK_AUDIT.md` 登记了 C07 填写门禁 `_c7_selfcheck.py` 的 15 项缺口（G1–G15），其中 G1–G5 为 high 级冒签通道。本任务在不改原门禁一字的前提下，在唯一写域 `lead/c07_gate_fix_20261109/` 产出增强版校验器 `_f3_c7check.py`，修补 G1–G5 全部 high 缺口，并顺手修掉 G6–G15 中可离线收紧的部分（G13 除外，见 §3 末尾）；对同一批 36 个攻样本双器实跑重测，如实登记拦截率变化与剩余边界。

**修补方向只收紧不放松**：增强版把原 15 项 H 系列判据逐字镜像（对比器实测 H 系列逐行零漂移，见 §4），新增 N01–N21 只加拦不减拦。若某样本原版拦住而增强版放过，即属退化——实测退化 0 个（§4）。

**边界（事先声明）**：
1. 这是**离线文书门禁**，只验格式、一致性、值域与冒用面；**真值**（sessionId 是否真是该来源会话的 ID、reviewerRole 是否真是该会话签发角色、sourceTaskId 是否真是其任务号）门禁无法也不应代证，须由来源会话自证（原门禁 `_c7_selfcheck.py:5` 自述；增强版 `_f3_c7check.py:14-15` 同口径，N07 输出注记逐字写明「只验形制，不验真值；真值须来源会话自证」，`_f3_c7check.py:185`）。§5 用 V1 证明件实证了这一固有边界。
2. 原门禁 `lead/c07_slot_20261109/_c7_selfcheck.py`、模板 `_c7_record_template.json`、审计件 `lead/c07_gate_audit_20261109/` 全部件（含 36 个样本目录）、`lead/pending_factpack_20261108/`、两台账均为保护件，**未改原门禁**、未改任何保护件——会话首末两轮 hashlib 实算指纹逐一相符（§2、§5）。
3. G5 形制正则未收紧到 UUID v4/variant 位（依据仅 1 个真实已登 ID，强收有误伤真实运行态 ID 之险，如实不修）；G6 对照集基数=1 是登记侧事实，离线不能补造（§5）。

---

## 2 上游指纹与原门禁判据基线

### 2.1 保护件指纹（本次会话亲手实算）

实跑命令：`python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/c07_gate_fix_20261109/_g1g5_fp.py"`（核验脚本为本会话新写于写域，`_g1g5_fp.py`，用 hashlib 对 8 件实算并与编排方任务书指纹逐一比对），输出 `保护件指纹相符=8/8`、`样本字节数相符=36/36`、exit=0。指纹如下（完整值见文件内容）：

| 件 | SHA256 前 8 位 | 字节数 | 相符 |
|---|---|---|---|
| lead/c07_slot_20261109/_c7_selfcheck.py（原门禁） | 74bec4d4 | 9961 | ✓ |
| lead/c07_slot_20261109/_c7_record_template.json（模板） | 3d763a8b | 3812 | ✓ |
| lead/c07_gate_audit_20261109/C07_SELFCHECK_AUDIT.md | e45fa323 | 33459 | ✓ |
| lead/c07_gate_audit_20261109/_c7a_independent.py | 53082d91 | 17998 | ✓ |
| lead/c07_gate_audit_20261109/_c7a_attack_results.txt | 3a1b3b9a | 137772 | ✓ |
| lead/PENDING_DECISIONS.md | 3765eddb | 52419 | ✓ |
| lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de4 | 759518 | ✓ |
| lead/c07_gate_fix_20261109/_f3_c7check.py（被核交付件） | 3ddddc60 | 33118 | ✓ |

36 个攻样本目录 `lead/c07_gate_audit_20261109/_c7a_samples/` 实测 36 件 JSON，字节数与任务书清点 36/36 逐一相符（同一脚本输出）。会话末轮复算见 §5.4。

### 2.2 原门禁 15 项判据逐条记录（实读 `_c7_selfcheck.py`，218 行，行号为本会话实读行号）

| # | 判据名 | 行号 | 判据要点 |
|---|---|---|---|
| H01 | JSON 可解析 | :91-95 | `json.loads(raw.decode("utf-8"))`，异常即 FAIL |
| H02 | 容器 13 键齐（N-1/2 形制） | :97-99（键表 :18-20） | 只查 CONTAINER13 缺失，**不查多余键**（多余键放行——G9 缺口） |
| H03 | schema 精确串 | :100-101 | `obj.get("schema") == "N-1-ACCEPTANCE-RECORDS/2"` 精确比对 |
| H04 | records 恰 1 条 | :102-105 | `isinstance(recs, list) and len(recs) == 1` |
| H05 | 9 字段名与顺序 | :107-108（FIELDS9 :16-17） | `list(rec.keys()) == FIELDS9`，顺序敏感 |
| H06×3 | 三身份字段非空非拒填 | :109-112（BAD_VALUES :32） | reviewerRole / reviewerSessionId / sourceTaskId 各打一行；`strip().lower()` 不在 BAD_VALUES 集合即 PASS |
| H07 | 记录内无占位符残留 | :113-114（PLACEHOLDER_PAT :31） | 正则 `<[^>]*>`（仅半角角括号）扫记录层全部字符串 |
| H08 | 记录内无 unknown/TODO 等拒填值 | :115-116 | `s.strip().lower() in BAD_VALUES` **整值精确匹配**（组合词如「暂无」不命中） |
| H09 | sessionId 不冒用他件已登 ID | :117-120（对照源 :27-30） | 与 a_residual_20261106 / a_residual_n1_20261108 两件 ACCEPTANCE_RECORDS.json 的 reviewerSessionId **精确集合比对**；对照源缺失时静默跳过（`os.path.exists` 不成立即 continue，:66-67）——G6 fail-open 缺口 |
| H10 | 裸计划号时 unresolved 必非空 | :121-128 | `re.fullmatch(r"N-\d+", stid.strip())` 触发；unresolved 须为非空列表 |
| H11 | inputHashes 四必绑件实算复核 | :129-156（REQUIRED_INPUTS :21-26） | 四件必绑，值须 `64hex/字节数` 串或 dict，对文件实算 sha256+字节数复核 |
| H12 | timestamp ISO8601 可解析 | :157-165 | `datetime.fromisoformat(ts.replace("Z","+00:00"))`，可解析即 PASS（任意年代合法——G12 缺口） |
| H13 | 容器层无占位符残留 | :169-171 | 半角角括号正则扫容器层（records 键除外） |

H06 打 3 行，合计打印 **15 项**。rec 缺失分支对 H05–H12 打 8 个占位 FAIL（:166-168），故该分支实打 13 个 H 项——T08a/T08b 双器均如此（本会话转录实测），系原判据固有结构，非漂移。绑定行形制含反引号（:181 `` print("被核对象 SHA256 = `%s`，字节数 = %d" ...) ``）——即 G13 所指；原文件一字不改，只在增强版输出侧修正。

### 2.3 G1–G5 缺口定位（本次会话亲手基线实跑，不采信转述）

实跑命令：`python -I -X utf8 _f3_rerun.py <原门禁> _g1g5_orig_transcript.txt _g1g5_orig_summary.json`（37 目标 = 36 攻样本 + 未填模板，逐样本 exit 全录）。实测：**原门禁拦 17 / 放 19**（模板基线拦）。放行枚举：T05（合法）、T13（合法）、T06a/T06b/T06c、T09b、T14、T16、T17、T18a/T18b、T19、T20、T22、T23、T24、T26、T27（16 个攻样本）、T29（边界样本）。

据此 G1–G5 均为**真缺口**：T06a/b/c 原版放行 → G1（内部角色冒签）真；T14/T27 原版放行 → G2/G3（decision/grade 值域缺失）真；T16 原版放行 → G4（六固定字段可掉包）真；T18a/b/T29 原版放行 → G5（sessionId 形制不验）真。

**任务书背景数字勘误**：任务书背景称「原本放行 14 个/拦 18 个」。本会话亲手实测为攻样本放行 16 + 合法 2 + 边界 1 = **放 19 / 拦 17**，与审计 §3.2/§4.2 勘误一致；「14/18」与实测不符，以本报告实测为准。

---

## 3 G1–G5 五条修补实现（实读 `_f3_c7check.py`，行号为本会话实读行号）

接口与原版兼容（同单参 JSON 路径、`--selftest`、无参 exit=2、目标不存在 exit=2；两个 selftest 本会话实跑均 PASS exit=0，对照基数=1）。原 H01–H13 判据逐字镜像（:241-319 与原 :91-171 同构）。

### G1（high·冒签）→ N01/N02/N03 内部角色黑名单

- 黑名单常量（`_f3_c7check.py:49`）：
  `INTERNAL_ROLE_STEMS = ["卡顿分流员", "分流报告撰写员", "独立复核员"]`
- 出处：`lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md:151` 实读原文「动态工作流子代理『卡顿分流员·GLM』……撰写 = 分流报告撰写员……独立复核责任 = 独立复核员」；:152 引 NEXT_STEPS:119 身份落实原则「不能由计划作者冒签」。
- 匹配算法（`role_stem_hits`，:163-168）：**NFKC 归一后做词干子串匹配**——「卡顿分流员·GLM（代签）」命中「卡顿分流员」。记录层 N01（:333-338）、容器层 N02（:339-341）、两层 role 一致 N03（:336，`r_role == c_role` 精确相等）。
- **黑名单刻意只收三个词干**，不收「GLM」「撰写员」等宽子串：实测合法签发角色面是「C07 身份补登签发员·GLM」（36 样本公共底），宽子串会误伤合法值；selftest 有反向断言 `role_stem_hits("C07 身份补登签发员·GLM") == []`（:556），本会话 selftest 实跑 PASS。

### G2（high·冒签）→ N04 decision 值域

- 值域（:51）：`DECISION_DOMAIN = {"REGISTERED", "PARTIAL"}`；禁签署语汇（:53）：`SIGN_WORDS = ["approve", "放行", "签署"]`。
- 出处：`lead/d13d14_cards_20261108/DECISION_QUESTIONS.md:121` 实读「**非技术裁决**——来源会话身份补登（行政动作）」；模板 grade/decision 占位口径（`_c7_record_template.json:5,31`）。
- 判据（:344-349）：`decision` 须 ∈ 值域 **且** `sign_word_hits(decision)` 为空。**SIGN_WORDS 只作用于 decision/grade 值、不做全文扫描**——固定字段 natureNote 合法含「不构成 APPROVE_SCOPE 签署」字样（模板 :4），宽扫会误伤固定值。

### G3（high·冒签）→ N05 grade 值域

- 值域（:52）：`GRADE_DOMAIN = {"REGISTERED", "PARTIAL"}`，禁语同 SIGN_WORDS；判据（:350-353）作用于容器层 `grade`。与 N04 同口径、同出处。

### G4（high·冒签）→ N06 六固定字段与模板逐字一致

- 固定字段表（:59）：`FIXED6 = ["schemaNote", "natureNote", "replacementNote", "sourceTask", "hashMethod", "decisionSemantics"]`。
- 出处：模板中标注「（固定格式值，照抄）」的恰这六个字段（`_c7_record_template.json:3,4,8,14,16,17` 实读确认）。
- 判据（:356-365）：对六字段**运行时实读模板**（`load_template` :145-150）后逐字段 `obj[f6] != tpl.get(f6)` 即 FAIL（缺失或值漂移都拦）。**模板不可读则 fail-closed**（:149 注释、:357 FAIL「模板不可读」）。

### G5（high·冒签）→ N07/N08/N09 sessionId 运行态形制

形制正则全文（`_f3_c7check.py:55-56`）：

```python
SESSION_RE = re.compile(
    r"sess_dwf-dwfrun-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}-actor_\d+_\d+")
```

- 口径出处：a_residual_n1_20261108 已登 ID `sess_dwf-dwfrun-324c613e-fb0e-42f5-9883-805fef5b80de-actor_3_1` 实文形制（对照基数=1，见 §5.3——**依据仅此 1 个真实 ID，故未收紧到 v4/variant 位**，如实声明）。
- `session_shape`（:176-185）：`SESSION_RE.fullmatch(sid)` + **拒 nil UUID**（:57 `NIL_UUID="0"*32`；:182-184 提取 32 位 hex 比对全零即拒「非运行态可生成值」）。记录层 N07（:372-373）、容器层 N08（:379-380）、两层一致 N09（:374-378，精确相等）。
- PASS 注记明写「形制相符（只验形制，不验真值；真值须来源会话自证）」（:185）；输出尾注同口径（:535）。

### 顺手修掉（方向只收紧）

| 缺口 | 修补 | 行号 | 要点 |
|---|---|---|---|
| G6 | N10 | :382-393 | 冒用面比对改【归一化】（`normalize_id` :153-156：NFKC+去空白+去零宽 Cf+casefold），记录层+容器层双验；**对照源 0 件装载即 FAIL**（fail-closed :384-385）——该分支属代码审查确认，未实跑（不能移动只读登记件），见 §6 |
| G7 | N11 | :395-408 | 计划号触发从 fullmatch 放宽为 **NFKC 归一后子串** `re.search(r"N-\d+", nfkc(stid))`（:402）——T20 装饰绕过拦 |
| G8 | N12 | :409-412 | 触发时 unresolved 必含登记语「正式任务书编号未落实」（REGISTRATION_PHRASE :61）——T23 假登记语拦，T05 合规登记语放 |
| G9 | N13+N21 | :414-417, :495-501 | 容器键集合与 13 键【精确相等】缺+多都拦；writeDomain 不得指向 8 个既有只读域（READONLY_DOMAIN_PREFIXES :70-75；c07_slot 不在列，模板建议就地填用） |
| G10 | N14 | :419-421 | 占位符扩展面：`BRACKET_PAT = re.compile(r"[<>＜＞]")`（:63）拦全角＜＞与裸角字符 |
| G11 | N15/N16 | :423-444 | inputHashes/artifactHashes **全键**实算复核（`verify_binding` :205-224），键路径限仓库内（`resolve_repo_path` :188-202 拒绝对路径与 `..` 越界） |
| G12 | N18/N19 | :460-488 | timestamp 须含时间成分+年份 2020–2040（:65-66）；unresolved 须为字符串列表 |
| G14 | N08/N09/N20 | :379-380, :374-378, :490-494 | 容器 sessionId 形制/两层一致/reviewer 形制 |
| G15 | N17 | :446-458 | itemId 与模板 `records[0].itemId` 一致（模板 :20 `N10-C07-Q6-identity`） |
| G13 | BINDING_FMT | :68, :534 | 本器绑定行无反引号（selftest 断言 :587）；原门禁 :181 的反引号属原文件、绝对不改，只在本器输出侧修正 |

---

## 4 36 攻样本双器重跑逐样本结果与统计

### 4.1 实跑命令

```
python -I -X utf8 _f3_rerun.py <原门禁绝对路径> _g1g5_orig_transcript.txt _g1g5_orig_summary.json
python -I -X utf8 _f3_rerun.py _f3_c7check.py               _g1g5_enh_transcript.txt  _g1g5_enh_summary.json
python -I -X utf8 _f3_compare.py _g1g5_orig_transcript.txt _g1g5_enh_transcript.txt _g1g5_orig_summary.json _g1g5_enh_summary.json _g1g5_compare.txt
```

三件均为本写域既有脚手架（`_f3_rerun.py:33-35` 以 `[sys.executable, "-I", "-X", "utf8", gate, t]` 子进程逐样本实跑并录 exit；`_f3_compare.py:44-60` 做 H 系列逐行等价核验）。37 目标 = 36 攻样本 + 未填模板。

### 4.2 逐样本表（exit：1=拦住，0=放行；来源 `_g1g5_compare.txt` 本会话实跑输出）

| 样本 | 原门禁 | 增强版 | 是否改善 | 增强版拦截主因（N 系 FAIL） |
|---|---|---|---|---|
| T01_empty_trio.json | 1 拦 | 1 拦 | 保持拦 | N03; N07; N09（H 系：H06×3+H08 仍在拦） |
| T02a_sid_unknown.json | 1 拦 | 1 拦 | 保持拦 | N07; N09 |
| T02b_sid_todo.json | 1 拦 | 1 拦 | 保持拦 | N07; N09 |
| T02c_sid_na.json | 1 拦 | 1 拦 | 保持拦 | N07; N09 |
| T03_sid_copied_n1r2.json | 1 拦 | 1 拦 | 保持拦 | N09; N10（归一化命中已登 ID） |
| T04_n11_no_registration.json | 1 拦 | 1 拦 | 保持拦 | N11; N12 |
| T05_n11_registered_gap.json | 0 放 | 0 放 | 保持放 | ——合法正样本（checks=36 failed=0），应放，**非误放** |
| T06a_role_kadun.json | 0 放 | 1 拦 | **转拦** | N01; N03（G1 生效） |
| T06b_role_fenliu.json | 0 放 | 1 拦 | **转拦** | N01; N03 |
| T06c_role_fuhe.json | 0 放 | 1 拦 | **转拦** | N01; N03 |
| T07_sid_placeholder.json | 1 拦 | 1 拦 | 保持拦 | N07; N09; N14 |
| T08a_records_zero.json | 1 拦 | 1 拦 | 保持拦 | N01; N03; N04; N07; N09; N11; N12; N15; N16; N17; N18; N19 |
| T08b_records_two.json | 1 拦 | 1 拦 | 保持拦 | 同 T08a 十二项 |
| T09a_container_missing_grade.json | 1 拦 | 1 拦 | 保持拦 | N05; N13 |
| T09b_container_extra_key.json | 0 放 | 1 拦 | **转拦** | N13（夹带键拦） |
| T10_field_order.json | 1 拦 | 1 拦 | 保持拦 | （N 系无 FAIL，由 H05 字段顺序拦住） |
| T11a_ts_bad.json | 1 拦 | 1 拦 | 保持拦 | N18 |
| T11b_ts_int.json | 1 拦 | 1 拦 | 保持拦 | N18 |
| T11c_ts_text.json | 1 拦 | 1 拦 | 保持拦 | N18 |
| T12a_hash_wrong_hex.json | 1 拦 | 1 拦 | 保持拦 | N15 |
| T12b_hash_wrong_bytes.json | 1 拦 | 1 拦 | 保持拦 | N15 |
| T12c_hash_missing_binding.json | 1 拦 | 1 拦 | 保持拦 | （N 系无 FAIL，由 H11 缺必绑件拦住） |
| T13_positive.json | 0 放 | 0 放 | 保持放 | ——合法正样本（checks=36 failed=0），应放，**非误放** |
| T14_decision_approve_scope.json | 0 放 | 1 拦 | **转拦** | N04（G2 生效） |
| T16_decisionsemantics_tampered.json | 0 放 | 1 拦 | **转拦** | N06（G4 生效） |
| T17_artifacthash_fake.json | 0 放 | 1 拦 | **转拦** | N16（假 artifact 指纹实算不符） |
| T18a_sid_dash.json | 0 放 | 1 拦 | **转拦** | N07; N09（G5 生效） |
| T18b_sid_digits.json | 0 放 | 1 拦 | **转拦** | N07; N09 |
| T19_sid_nearcopy.json | 0 放 | 1 拦 | **转拦** | N07; N09; N10（已登 ID+尾随空格，归一化命中） |
| T20_n11_decorated.json | 0 放 | 1 拦 | **转拦** | N11; N12（装饰绕过仍触发登记规则） |
| T22_fullwidth_placeholder.json | 0 放 | 1 拦 | **转拦** | N07; N09; N14（全角占位符） |
| T23_unresolved_wrong_phrase.json | 0 放 | 1 拦 | **转拦** | N12（假登记语拦） |
| T24_inputhash_extra_fake.json | 0 放 | 1 拦 | **转拦** | N15（伪造额外键实算不符） |
| T26_container_role_fuhe.json | 0 放 | 1 拦 | **转拦** | N02; N03（G1 容器层生效） |
| T27_grade_approve_scope.json | 0 放 | 1 拦 | **转拦** | N05（G3 生效） |
| T29_sid_fabricated_shape.json | 0 放 | 1 拦 | **转拦** | N07; N09（nil UUID + 两层不一致两个增量信号，非真值验证） |

### 4.3 统计（全部来自本会话实跑）

- **原门禁：拦 17 / 放 19**（36 样本；模板基线拦）。
- **增强版：拦 34 / 放 2**（拦截率 47.2% → 94.4%）。
- **转拦（原放→增强拦）17 个**：T06a/T06b/T06c、T09b、T14、T16、T17、T18a、T18b、T19、T20、T22、T23、T24、T26、T27、T29。其中 16 个为攻样本（**原放行的 16 个攻样本 16/16 全部拦下**），T29 为边界样本（靠 nil-UUID 与两层不一致拦下）。
- **退化（原拦→增强放）0 个**：原拦 17 个增强版全部仍 exit=1，**无误放**。
- 增强版仍放行仅 T05、T13，均为合法正样本（本会话实跑 `GATE PASS checks=36 failed=0`，T13 指纹 3a6b74e6…/3232B、T05 指纹 8a3bfad6…/3325B）。
- **H 系列逐行漂移数 = 0**（`_g1g5_compare.txt` 「漂移数=0（零漂移：原15项判定与原门禁逐一相同）」）——所有新增拦截全部来自 N 系列新增项，原判据一字未松，双证非退化（exit 层零退化 + H 层零漂移）。
- 未填模板基线：原 failed=4（H07/H11/H12/H13）→ 增强 failed=11（新增 N04/N05/N07/N08/N14/N15/N18，本会话转录逐行核对）。

### 4.4 任务书口径勘误

任务书背景「原本放行 14 个/拦 18 个」与实测不符：实测放 19 / 拦 17（§2.3）。对应地，§4.3 统计以实测数为准：原放行 19 个中拦下 17 个，原拦住的 17 个**无一误放**（0 退化）。

---

## 5 复核回件、剩余边界与未改声明

### 5.1 复核回件（独立复核员，verdict 如实登记）

独立复核回件 verdict = **confirmed**（非 refuted/partial，不标 unconfirmed）。复核回件结论要点：指纹两轮实算全符、H 清单逐条实读全对、G1–G5 经基线自跑证实均为真缺口、增强版自跑拦 35/放 2（37 目标口径，含模板）、17 个转拦的 N 项归因 17/17 相符、非退化双证明复现（4 个自造原拦变体仍拦 + H 系列漂移=0）、G5 形制正则不松不严实测相符、真值边界独立构造 TV1 实测两器均 exit=0。复核残留（不破坏）：修补叙述中 4 处行号引用偏移 2–10 行（实质断言已独立证实，属笔误级）；T08a/T08b 双器均打 13 个 H 项系原判据记录缺失分支固有结构；N10 对照集 0 件 fail-closed 分支双方均未实跑；G6 基数=1 与 G5 只验形制属明示固有边界。复核回件绑定行（照录）：

被核对象 SHA256 = 74bec4d48498903df08dbf3a56ba942e74b58f5b4a7940c094eafdeb03adbf2e，字节数 = 9961

（上一行为原门禁 lead/c07_slot_20261109/_c7_selfcheck.py，复核会话首末两轮实算一致，未改一字）

被核对象 SHA256 = 3ddddc60fca034fe2b6434e0d8baf38c7bc79966342cf287e8521070b2553600，字节数 = 33118

（上一行为被核交付件 lead/c07_gate_fix_20261109/_f3_c7check.py）

### 5.2 本报告撰写员的绑定行（会话内 hashlib 实算，`_g1g5_fp.py` 输出）

被核对象 SHA256 = 74bec4d48498903df08dbf3a56ba942e74b58f5b4a7940c094eafdeb03adbf2e，字节数 = 9961

（上一行为原门禁 lead/c07_slot_20261109/_c7_selfcheck.py，本会话实算，与编排方指纹一致）

被核对象 SHA256 = 3ddddc60fca034fe2b6434e0d8baf38c7bc79966342cf287e8521070b2553600，字节数 = 33118

（上一行为本任务被核交付件 lead/c07_gate_fix_20261109/_f3_c7check.py，本会话实算）

### 5.3 剩余边界（如实登记，含真值边界）

1. **真值边界（根本边界，本会话亲测实证）**：证明件 `_f3_V1_t29variant_consistent.json`（写域内合成）——两层放**同一个**合成形制合规 sessionId（sess_dwf-dwfrun-deadbeef-1234-4abc-8def-0123456789ab-actor_1_1）、其余全合法。本会话实跑：原门禁 `GATE PASS checks=15 failed=0` exit=0、增强版 `GATE PASS checks=36 failed=0` exit=0。即：编造一个「形制合规、两层一致、不在对照集」的 sessionId，任何离线文书门禁（原门禁、审计两套独立器、本增强版）都无法证伪——**ID 真值真伪必须由来源会话自证**。同理 reviewerRole/sourceTaskId 的真值，门禁只能验非冒用面，不能验真。T29 按交付形态被拦靠的是 nil-UUID 与两层不一致两个增量信号，不改变此边界。
2. **G5 形制未收紧到 UUID v4/variant 位**：形制口径依据仅 1 个真实已登 ID（对照基数=1，双器 selftest 实跑均打印「对照已登ID基数=1」），依据不足，强收会冒误伤真实运行态 ID 之险，如实不修。
3. **G6 对照集基数=1**：冒用面对照仅 a_residual_n1 一个 ID（20261106 件旧 schema 无该键），扩对照集需要「哪些文件是权威登记册」的外部事实，离线不能补造。增强版只做归一化比对 + 对照集 0 件 fail-closed；**该 fail-closed 分支未实跑**（不能移动只读登记件来构造 0 件装载场景），属代码审查确认（:384-385），记为未验。
4. **H08 组合词面未修**：BAD_VALUES 整值精确匹配（原判据），「暂无」等组合词不命中；本器未加词级扫描（避免对合法长文本误伤，独立器 I08 口径未照搬），如实留作未修。timestamp 任意年代面已由 N18 收紧（2020–2040+须含时间成分），已修。
5. **守门人定位**：能当【**必要条件**】守门人——相对原门禁严格更强（拦截超集 + 零退化 + H 系列零漂移），exit=0 的含义比原版强得多。不能当【充分条件】守门人——V1 已证一致伪造可过闸，入账前必须叠加来源会话身份自证（含 run ID 出处核），这一步是程序事实，不是文书校验能替代的。残余评级 medium：五个 high 冒签通道已在文书层闭合，剩余为固有真值边界 + 对照集覆盖面，须靠流程叠加而非本器修补。

### 5.4 未改任何文件声明

本会话对原门禁、模板、审计件（含 36 个样本目录）、pending_factpack、两台账**只读未改**：会话首轮 `python -I -X utf8 _g1g5_fp.py` 实算 8 件指纹 8/8 相符、36 样本字节数 36/36 相符（§2.1）；本报告写毕后将再跑末轮复算并入账（见 §6 末行）。本会话仅新建写域内文件：`_g1g5_fp.py`、`_g1g5_orig_transcript.txt`、`_g1g5_orig_summary.json`、`_g1g5_enh_transcript.txt`、`_g1g5_enh_summary.json`、`_g1g5_compare.txt`、本报告件。未 commit、未 push、零真机、零采样代码。

---

## 6 结论

1. **G1–G5 修补完成度：五个 high 冒签通道全部闭合**（文书校验层）。逐条实证：G1（T06a/b/c、T26 经 N01/N02/N03 拦下）、G2（T14 经 N04 拦下）、G3（T27 经 N05 拦下）、G4（T16 经 N06 拦下）、G5（T18a/T18b/T29 经 N07/N08/N09 拦下）；V2 变体（卡顿分流员·GLM（代签））与 V3 变体（已登 ID 夹零宽字符）在修补会话内实跑被拦（写域转录件在案），本会话未重复构造，标注为修补方实跑、复核方 confirmed。
2. **拦截率变化**：36 攻样本上原门禁拦 17（47.2%）→ 增强版拦 34（94.4%），转拦 17、退化 0、H 系列漂移 0；原放行 16 个攻样本 16/16 拦下，原拦住 17 个无一误放。仍放行 2 个（T05/T13）均为合法正样本，属应放。
3. **未改原门禁**：保护件指纹会话首末两轮实算逐一相符，未改一字。
4. **未验项（如实）**：N10 对照集 0 件 fail-closed 分支未实跑（不能移动只读登记件，代码审查确认）；G6 对照集基数=1 需外部事实才能扩；G5 形制未收紧到 v4/variant 位（依据不足）；H08 组合词面未加词级扫描（未修）；V2/V3 边界证明件本会话未重跑（修补会话实跑 + 复核 confirmed 在案）。
5. **守门人结论**：增强版可作入账前【必要条件】门禁；【充分条件】不成立——真值边界（§5.3 第 1 条）是文书门禁的固有极限，sessionId/reviewerRole/sourceTaskId 真值必须由来源会话自证，流程叠加不可省。

（会话末轮指纹复算：`python -I -X utf8 _g1g5_fp.py` 重跑于本报告写毕后，结果见下）

（末轮复算输出：保护件指纹相符=8/8、样本字节数相符=36/36、EXIT=0——8 件含原门禁 74bec4d4…/9961B 与交付件 3ddddc60…/33118B，与本报告 §5.2 绑定行一致。）
