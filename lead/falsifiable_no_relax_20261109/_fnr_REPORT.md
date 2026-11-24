# _fnr_REPORT.md — 把「不放松」做成可证伪的（检验设计与评估）

唯一写域 `lead/falsifiable_no_relax_20261109/`。零真机、零采样代码；不改任何谓词、回归脚本、白名单；不 commit、不 push。Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。

被核对象 SHA256 = 5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25，字节数 = 75673

（严格格式绑定行，绑定对象 = 只读件 `lead/gate_r9sem_20261109/_r9s_regress_out.json`；本会话 `hashlib` 实算值。）

---

## 0 指纹独立复核（本会话实跑）

命令：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnr_fingerprints.py
```
输出（完整保存 `_fnr_fingerprints_out.json`）：`"all_match": true`，9/9 件 SHA256 与字节数均与【编排方实跑指纹】逐位一致。逐件值见该 JSON 的 `rows[*].binding`。

另有本次实读但未列入派发指纹的 6 件（本会话 `hashlib` 实算）：
`WHITELIST_AUDIT.md` = `2498a51d793bf13831ee5fedd0395bf8f18c12d9e98a7391af3c65965b6ec70c` / 62858 B；`_r9s_samples.py` = `5c103ddfa2c1548210de466f7a89266cafcb9773dcbba19ea9a783206e0f20bc` / 17721 B；`GATE_PIPELINE_COMPOSE.md` = `5d9cdf00cfd7d628f6e99ee1e5b5022f4614c8befae743ebc08fac8169e87211` / 57759 B；`CHAIN_VS_SINGLE.md` = `efde3e8e13084d840d08ad9243c91ac1f83c3b445a71f525cc4d2335402dc4ed` / 39558 B；`GATE_N13_QUOTED_ASSERTION.md` = `7b3fddb7d3484c76fecfe25fb352f081a1391b14b1d87684c719adf3df06e90b` / 39906 B；`_n13_regression.py` = `72de5a36d4abb2860510299e54200af7bb1b15054f0a15a056dab2fbce3ec5f2` / 14353 B。

**为什么没有跑 `_r9s_regress.py` 本体**：`lead/gate_r9sem_20261109/_r9s_regress.py:235-236` 执行 `(WDIR / "_r9s_regress_out.json").write_text(...)`，`WDIR` 在 `:29` 定义为绝对只读域。跑它会违反「绝对只读」。本会话改为在写域内**内存中复刻同一公式**（`_fnr_replay.py`），并先做保真校验：k0 基线与只读 JSON 的 12 个字段全 `match=true`（`_fnr_replay_stdout.txt` 的 `fidelity_all_match: true`，含 `flip_pairs_identical`）。**这是替代实现，不是跑回归本体，如实登记。**

---

## 1 第一步：复核自证反例

### 1(a) 5 条全换语义空后，回归的实际输出（逐项）

命令：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnr_replay.py
```
输出（完整：`_fnr_replay_stdout.txt` / `_fnr_replay_out.json` 的 `k5_empty`）：

```
n_items=302  n_flips=5  outside_whitelist=0  n_tightens=0
samples: positive=20 positive_pass=20  negative=24 negative_pass=24  all_pass=True
four_domains_total_remaining=3   no_relaxation=True   VERDICT=PASS
```

5 条 FLIP 逐项（全部 `whitelisted=True`、`semantically_empty=True`）：

| # | domain | token | R9→R9S | 替换片段关键值 | 语义空理由 |
|---|---|---|---|---|---|
| 1 | `lead/matrix_ab_ruling_20261109/` | `需谁批准` | False→True | `批准人一律 = **见台账登记**` | 赋值对象是「见台账登记」指针，无具体施事 |
| 2 | `lead/matrix_reach_20261109/` | `实跑输出` | False→True | `verdict='详见台账' conf='none'` | 载荷值是「详见台账」，不是返回对象 |
| 3 | `lead/n11_wording_fix_20261108/` | `改前改后` | False→True | `【改后】改后句见方案 B 的对应行，本件不重录` | After(t) 是指针 + 不重录 |
| 4 | `lead/s604_script_gap_20261109/` | `脚本存在性` | False→True | `【不存在且从未落盘】（以台账记载为准，本件不另下结论）` | 判定权外包给台账，本件未决断 |
| 5 | `lead/s604_script_gap_20261109/` | `可重建` | False→True | `**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。**` | 未决问句里的肯定情态被当成断言 |

片段逐字照录 `lead/whitelist_audit_20261109/_wl_selfproof.py:21-32`（本会话实读）与 `_wlw_stepC.py:192-202`；上游独立实跑件 `_wl_selfproof_out.json:2-40` 同值、`_wlw_stepC_stdout.txt:34-40` 亦同值。**即：5 条语义内容全部不在场，`no_relaxation=True`、`VERDICT=PASS`。**

四域剩余缺要素：本会话复算 `r9s_missing` 在 4 个域全为 `[]`（`_fnr_replay_out.json` 的 `k5_empty.four_domains`）；`matrix_ab_ruling` 仍剩 3 条**非要素类**基线问题「含越界断言 已改矩阵 / 已收紧 / 已施行」，`_r9s_regress.py:225-228` 只要求这些落在 `non_element_baseline_problems` 内即放行，故不影响 PASS。**这 3 条与语义无关。**

### 1(b) 逐行追 `no_relaxation` 的计算：它为什么不检查语义

源码（`_r9s_regress.py`，本会话实读全文）：

- `:166` `for r in ROWS:` → `:174` `text = mp.read_text(...)` 读主件文本；`:175` `elems = elements_of(r)` 取必现要素 token。
- `:178-179` `ok0, lay0 = R9.r9_element_present(text, k)` / `ok1, lay1, _d = R9S.r9s_element_present(text, k)`：这里**确实**把文本送进了语义谓词。
- `:182-185` `if (not ok0) and ok1: flips.append({"domain": dom, "token": k, "whitelisted": (dom, k) in WHITELIST, "main": r["main"]})` —— ★ **写入 `flips` 的只有 4 个字段：域、token、布尔白名单标记、主件名。`ok1` 的 `detail`（角色证据、logic、命中行）被显式丢弃（变量名 `_d`）。此后 `flips` 里再没有任何来自文本的内容。**
- `:204-206`
  ```python
  OUT["no_relaxation"] = (len([f for f in flips if not f["whitelisted"]]) == 0
                          and len(flips) == len(WHITELIST)
                          and all(f["whitelisted"] for f in flips))
  ```
  三个合取项纯粹是**集合基数与成员资格**：①白名单外翻案数=0；②翻案数=白名单大小；③每条 `whitelisted` 为真。③ 在 ① 成立时恒真，是冗余项。**没有任何一项读 `f` 之外的文本、`detail`、`evidence` 或独立真值。** 因此 `text` 的语义真值在这三行里不可观测——把它换成任何仍能让 `ok0=False, ok1=True` 的字符串，三行输出不变。
- `:223-229` `VERDICT` = `samples.all_pass` ∧ `no_relaxation` ∧ 四域剩余条件。`samples` 来自 `:52-68` 的 `_r9s_samples.SAMPLES`（44 条构造静态串，与主件文本**不同源**，见 `:54-55`），四域剩余条件只比字符串集合。故 VERDICT 也不接触被替换的主件语义。
- `:113-119` `WHITELIST` 硬编码同 5 对；`:371-402` 的 `SPECS` 恰为同 5 键（`_r9s_predicates.py`，实读）。`_r9s_predicates.py:426-428` 明写未登记 token → `R9S ≡ R9`。**302 项中 292 项 token 未登记、结构性不可能翻案**（本会话 `_fnr_check.py` 实算 `n_structurally_untested=292`, `coverage_ratio=0.0331`；上游 `_wl_step3_struct_out.json:74` 记 `n_registered_occurrences=10`、5 个在白名单外但 `r9=True` 已字面在场）。⇒「白名单外 0」主要是**设计后果**，不是独立实证。

**结论**：这是「两个同源集合相等」的自证，不是不放松检验。它与「是否放松」的因果关系被 `:183-185` 的字段丢弃切断。

### 1(c) 只有 3 条语义空 / 4 条语义空：回归报什么

同一命令 `_fnr_replay.py`，场景 `k3_empty` / `k4_empty`（替换按 `EMPTY` 字典顺序取前 k 项，逐项内容见 `_fnr_replay_out.json` 的 `subs`）：

| 场景 | 语义空数 | n_items | n_flips | outside | n_tightens | samples_all_pass | 四域剩余 | no_relaxation | **VERDICT** |
|---|---|---|---|---|---|---|---|---|---|
| k0 基线 | 0 | 302 | 5 | 0 | 0 | True | 3 | True | **PASS** |
| k1 | 1 | 302 | 5 | 0 | 0 | True | 3 | True | **PASS** |
| k2 | 2 | 302 | 5 | 0 | 0 | True | 3 | True | **PASS** |
| **k3** | **3** | 302 | 5 | 0 | 0 | True | 3 | **True** | **PASS** |
| **k4** | **4** | 302 | 5 | 0 | 0 | True | 3 | **True** | **PASS** |
| k5 | 5 | 302 | 5 | 0 | 0 | True | 3 | True | **PASS** |

逐项 FLIP：`k3` 前 3 条 `semantically_empty=True`、后 2 条 False；`k4` 前 4 条 True、第 5 条 False；其余字段与 k0 完全相同。**任意 1..5 条结论错，检验一律 PASS。** 这直接证明该检验对「结论错」的敏感度恒为 0。上游 `_wlw_stepC_stdout.txt:41` 的「1 条错 5/5 全 PASS」与本会话 k1 一致。

### 1(d) 反向假阳性：`no_relaxation=False` 但语义其实正确

有，三种构造，全部在同一命令实跑：

| 场景 | 构造 | 语义真值 | n_flips | outside | no_relaxation | **VERDICT** |
|---|---|---|---|---|---|---|
| `fp_extra_true_flip` | 追加第 6 条翻案：`lead/handoff_pack_20261109/` × `需谁批准`，文本 `审批人 = 丙复核责任人。`，实跑 `r9=False / r9s=True / layer=semantic`（`_fnr_replay_out.json` 该条 `injected=true`） | **真·语义等价**，内容正确 | 6 | 1 | **False** | **FAIL** |
| `fp_literal_insert` | 在 `RULING_MATRIX_AB.md` 文本尾部追加 `需谁批准：见本件第 5 节，批准人一律 = 乙设计责任人。`（内存中），使该要素**字面也到场**，R9 直接判 True，翻案消失 | 内容**更真**（既有语义又补字面） | 4 | 0 | **False** | **FAIL** |
| `fp_drop_one_whitelist_pair` | 白名单删去 1 对，5 条翻案的**原文与语义完全不动** | 全部正确 | 5 | 1 | **False** | **FAIL** |

三者 FAIL 的理由都是「集合不等（数量 / 包含）」，**不是发现语义错**。上游 `_wl_step34_stdout.txt` 情形 A、`WHITELIST_AUDIT.md:500` 亦记「移除 1 项 ⇒ FAIL，FAIL 理由是集合不等，不是语义错」。⇒ 该谓词**同时对真值不敏感、对集合基数过敏**，是双向失配：既漏报全部真错误，又误报全部良性变化。

---

## 2 第二步：可证伪的「不放松」检验（核心产出）

### 2(a) 什么才算「不放松」——可操作定义（非循环）

不用「没变得更松」这种自指说法。设 `V0` 旧谓词、`V1` 新谓词、`I` 有限可枚举的项全集（本例 302 项 `(domain, token)`）。设 `ORACLE: I → {0,1,UNVERIFIABLE}` 是**在 V1 运行之前**、由未参与 V1 设计与派发的独立裁定方，按逐角色正面证据给出的真值表；`ORACLE(i)=1` 意为「该要素所需的语义内容在此交付件中确已交付」。真值表先 `hashlib.sha256` 封印并预注册。

```
NO_RELAXATION :=
 (A) 可靠性   ∀i∈I: V0(i)=0 ∧ V1(i)=1  ⇒  ORACLE(i)=1
 (B) 有界收紧 ∀i∈I: V0(i)=1 ∧ V1(i)=0  ⇒  ORACLE(i)=0
 (C) 真值覆盖 |{i : ORACLE(i) ≠ UNVERIFIABLE}| = |I|
     （结构性不可能翻案的项也必须登记，且记 UNTESTED，绝不计作「没放松」的证据）
 (D) 敏感度   ∃ 已知错误注入 e，使 ORACLE(e)=0 ∧ V1(e)=1，且 CHECK(e)=ALARM
     —— 由 2(e) 的元检验**实跑证明**，明文写为成立条件，不是信念
 (E) 白名单来源 白名单先封印预注册，且 `set(白名单token) ≠ set(V1.spec_keys)`
```

每个量词都在有限表上可跑；`ORACLE` 是具体 JSON；`D` 是可执行测试。**结论错了（A 被违反 / ORACLE 被伪造 / 对抗样本被放过）就必须报警**——这就是可证伪性。关键在 `ORACLE` 与 `V1` 不同源；若同源，`A` 退化为本次的 self-certified 集合相等。

### 2(b) 检验必须能在「结论错了」时报警：设计

三条硬约束，缺一不可：

1. **异源真值**：`ORACLE` 与白名单由独立方盲标注、封 SHA；`V1` 作者不得写白名单。`_fnr_check.py:95-125` 的 `certificate_ok` 强制 `oracle_author != predicate_author` 且 `oracle_sealed=True`。
2. **逐项正面证据**：每个翻案项必须提交 (a) `file:line` 锚 + 原文引文；(b) **每个**必选语义角色的实值（不接受「见台账」「待判」「不重录」「以…为准」指针）；(c) 指针/占位/未决/否定守卫；(d) 与预注册 ORACLE 一致。缺任一即 ALARM。
3. **注入式敏感度证明**：把任一角色的实值替换为指针，检验**必须**报警；若 0 次报警，直接判该检验 `INVALID`（装饰），不看它是否 PASS。★ 这一条把「检验本身有效」变成被检验对象。

本会话实跑结果（`_fnr_check_stdout.txt`）：把同一检验放到**现盘真实状态**上，`VERDICT=ALARM`（L1 报 `SELF_CERTIFIED`、L3 报 6 条对抗样本泄漏）；放到「5 条结论全错」上，`VERDICT=ALARM`。**旧检验在两种情况下都是 PASS。** 这就是「能在结论错时报警」的实测差异。

### 2(c) 三层覆盖

| 层 | 检查什么 | 本会话实现 | 在现盘实状态的结果 |
|---|---|---|---|
| **L1 结构** | 翻案集合 ⊆ 白名单、数量相等；**并显式报告覆盖率**（未登记 token 记 UNTESTED 而非证据）；检测 `set(WL token)==set(SPECS keys)` 的 SELF_CERTIFIED；白名单须封印且作者独立 | `check_l1` (`_fnr_check.py:127-159`) | `ok=false`：`n_items=302`、`n_flips=5`、`outside=0`、*`n_structurally_untested=292`*、`coverage_ratio=0.0331`、`self_certified=true` → ALARM |
| **L2 语义** | 每个翻案项的独立真值证书：锚点 + 逐角色正面实值 + 非值守卫 + 独立封印 ORACLE 一致 | `certificate_ok` / `check_l2` (`:95-125`, `:161-177`) | `ok=true`（本会话 5 份演示证书全通过，15/15 角色有实值）；注入 1 条 `oracle_truth=False` 即 ALARM |
| **L3 对抗** | (i) 预注册「形式像而实质空」语料必须全部判 ABSENT；(ii) **变异注入**：逐个角色值换成指针，必须报警；0 报警即判检验无效 | `check_l3` (`:179-225`) | (i) `7/13 caught` → 6 条泄漏（CF3/CF5/WCF5/V2/V3/V6）；(ii) `15/15` 次变异全部报警，`sensitivity_proved=true` |

★ L3(i) 的 6 条泄漏是**现盘 R9S 谓词真实存在的过宽**，不是本检验的缺陷；本检验如实把它报成 ALARM。这与旧 `no_relaxation` 把 44/44 样本全过当成稳健性证明形成对照。

### 2(d) 可粘贴实现片段

完整可粘贴模块 = `lead/falsifiable_no_relax_20261109/_fnr_check.py`（核心段 `:62-289`，具体实例化 `:291-352`）。最小可粘贴核心（无项目依赖，只依赖 `re`/`json`）：

```python
import re, json

NON_VALUE_RE = re.compile(
    r"见台账|详见|参见|见附件|见上|见下表|以.{0,6}记载为准|不另下结论|不重录|"
    r"不予判定|暂不作判定|待判|待定|待补|待验|待查|待确认|尚需|尚未|需进一步|"
    r"是否|并非|不可重建|无法重建|未能重建|未验|未采集|无输出|"
    r"^(?:TBD|N/?A|待定|待指定|未定|未知|略|\.{2,}|…+)$")

def certificate_ok(cert, required_roles):
    bad = []
    if not re.search(r"^.+:\d+$", cert.get("anchor", "")):
        bad.append("L2a: no file:line anchor")
    if len(cert.get("quote", "")) < 10:
        bad.append("L2a: quote too short")
    roles = cert.get("roles", {})
    for r in required_roles:
        v = str(roles.get(r, ""))
        if len(v) < 2:
            bad.append("L2b: missing role " + r)
        elif NON_VALUE_RE.search(v):
            bad.append("L2c: role %s is a non-value: %r" % (r, v[:40]))
    if cert.get("oracle_truth") is not True:
        bad.append("L2d: oracle says NOT delivered")
    if not cert.get("oracle_sealed"):
        bad.append("L2d: oracle not sealed")
    if cert.get("oracle_author") == cert.get("predicate_author"):
        bad.append("L2d: oracle not independent")
    return (not bad), bad

def no_relaxation_falsifiable(items, flips, whitelist, spec_keys, certs,
                              spec_roles, V1, adversarial, registered):
    # L1
    wl = {tuple(x) for x in whitelist}
    fk = [(f["domain"], f["token"]) for f in flips]
    untested = [i for i in items if i["token"] not in registered]
    l1 = (all(k in wl for k in fk) and len(fk) == len(wl)
          and {k for _, k in wl} != set(spec_keys))   # reject self-certification
    # L2
    l2 = all(certificate_ok(certs[k], spec_roles.get(k[1], []))[0]
             if k in certs else False for k in fk)
    # L3(i) adversarial corpus must all be judged ABSENT
    l3i = all(V1(t, tok)[0] is False for _cid, tok, t in adversarial)
    # L3(ii) MUTATION INJECTION: checker MUST alarm on a known-wrong world
    alarms = 0
    for k in fk:
        if k not in certs: continue
        for role in spec_roles.get(k[1], []):
            m = json.loads(json.dumps(certs[k]))
            m["roles"][role] = "见台账登记，本件不重录"
            alarms += (not certificate_ok(m, spec_roles.get(k[1], []))[0])
    l3ii = alarms > 0
    return {"VERDICT": "PASS" if (l1 and l2 and l3i and l3ii) else "ALARM",
            "L1": l1, "L2": l2, "L3_adversarial": l3i,
            "L3_sensitivity_proved": l3ii, "n_untested": len(untested),
            "n_mutation_alarms": alarms}
```

注：`spec_keys != 白名单token集` 是 L1 的新增拒绝项，专门堵住本次 self-certification；`n_untested` 必须随结果一起报告，禁止把「结构性不翻案」当实证。

### 2(e) 元检验：怎么证明检验本身有效

命令：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnr_check.py
```
输出（`_fnr_check_stdout.txt`，完整 `_fnr_check_out.json`）：

```
synthetic_baseline_VERDICT = PASS          （已知-好世界，13/13 对抗样本被抓）
n_wrong = 9    n_wrong_caught = 9
n_good  = 2    n_false_alarms = 0
CHECKER_VALID = true
old_check_on_ALL_5_WRONG: no_relaxation=true  VERDICT=PASS
```

9 种**已知错误注入**全部触发 ALARM（逐条在 `_fnr_check_out.json` 的 `new_check_meta_test.wrong_injections`）：

| 注入 | 报警层 |
|---|---|
| `all_5_conclusions_wrong__semantic_empty`（5 条全语义空） | L2 |
| `3_of_5_semantically_empty` | L2 |
| `1_oracle_says_absent` | L2 |
| `1_certificate_missing` | L2 |
| `oracle_author_not_independent` | L2 |
| `whitelist_not_sealed` | L1 |
| `6th_flip_outside_whitelist` | L1 + L2 |
| `V1_accepts_undecided_payload`（谓词放过未决载荷） | L3 |
| `whitelist_becomes_self_certified` | L1 |

2 种**已知良性变化**全部不报警（`reworded_quote_still_true`、`extra_adversarial_case_caught`）。

元检验的基线必须是**已知-好世界**，不能拿现盘当基线：现盘本身有真实缺陷，第一次实跑时把现盘当基线，2 个「良性变化」被误记为 `false_alarm`、`CHECKER_VALID=false`（`_fnr_check_stdout.txt` 已被第二次实跑覆盖，该中间态如实记于此）。改用写域内构造的 `repaired_predicate` 世界（13/13 对抗全抓、`spec_keys` 多一个预留键以消除 self-certification）后得 `PASS`。**「检验有效」的证明本身也需要一个可证伪的基线，这一点是本次设计的一个实测教训。**

对照：旧检验在 `all_5_wrong` 上是 `PASS`（`_fnr_replay_out.json` 的 `k5_empty`）。⇒ 新检验有敏感度，旧检验没有。

---

## 3 第三步：三个既有结论受影响程度

### 3(a) R9 升级：两个判定必须分开

| 判定 | 评级 | 依据 |
|---|---|---|
| **「5 处语义在场」的误报判定** | **可信（但来自人工独立读原文，不是机制证明）** | `lead/whitelist_audit_20261109/WHITELIST_AUDIT.md:498` 记「应保留 5 / 应移除 0 / 需补证据 0」，`:516` 记「5/5 独立判语义在场」；`:484` 另记一处引文保真瑕疵（报告 `:204` 改写冒充逐字）但不推翻裁决。本会话**未重做 5 份主件的人工逐项裁决**，只核其结论与机制脱钩，故标「沿用上游独立结论，本会话未独立重判」。 |
| **「没放松」的证明** | **不可信（机制无效，已用可执行反例证明）** | 本会话 `_fnr_replay.py` k1..k5 全 PASS；`_r9s_regress.py:182-185` 丢弃语义 detail、`:204-206` 纯集合、`:223-229` 纯布尔；`_r9s_predicates.py:426-428` + `SPECS` 5 键 ⇒ 292/302 项结构性不翻案。上游 `WHITELIST_AUDIT.md:517` 同判「不可信」、`:522` 记「白名单验证机制 `invalid`」。 |

补充：正负样本集 `20/20 + 24/24` 在本会话保真复算中确实全过（`_fnr_replay_stdout.txt` k0），但 `_r9s_samples.py:2-9` 自述「构造语料」、`WHITELIST_AUDIT.md:106` 指出 20 条正样本中 3 条走 `raw` 短路、**真正测到语义层只 17/20**，`_wl_step3_struct_out.json:211-212` 记第三方 7 条近似负样本只抓 `2/5`、`2/7`。⇒ 样本集**不能**替代 L2/L3。本会话 L3 实跑 13 条对抗样本，R9S 只抓 7 条（6 条泄漏：CF3/CF5/WCF5/V2/V3/V6，`_fnr_check_out.json` 的 `adversarial_baseline`）。

**修复需要**：①第三方盲标注 302 项真值表并封 SHA 预注册；②白名单与 `SPECS` 解同源；③每个翻案项交逐角色正面证据证书（拒绝指针/未决值）；④把 CF/WCF/V 系列纳入必跑回归；⑤按 2(e) 跑元检验，元检验不过则不得声称「没放松」。**本会话只给方案，未实施、未改任何谓词。**

### 3(b) 合成链「69/74，无新漏报」

**它用什么检验证明「无新漏报」**：`lead/gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md:417` 与 `_gp_DESIGN.md:353` 的原句是「3 条漏报（GP-A1/A2/A3）N13 单层也全漏，**合成链没有引入新漏报**」。即：在同一份 74 行语料上，比较 `chain` 与 `n13` 的 **FN 计数**。本会话实跑核对（`python -I -X utf8 -c` 读 `_gp_regression_out.json`）：

```
single_layer_vs_chain.n13   = {ok:71, fp:0, fn:3}
single_layer_vs_chain.chain = {ok:69, fp:2, fn:3}
n13 FN ids  = ['GP-A1','GP-A2','GP-A3']
chain FN ids= ['GP-A1','GP-A2','GP-A3']
IDENTICAL SET: True
```

所以检验是「`FN(chain) == FN(n13)` 且 `FN 集合相同`」——**这是同一场考试内部两个考生的分差比较，不是「相对独立真值没有新增漏报」**。

**是否同类缺陷**：是，且更严重，有三层同源问题（均有本会话实读依据）：

1. **比较双方输入契约不对齐**：`lead/chain_vs_single_20261109/CHAIN_VS_SINGLE.md:282` 实读——`_gp_regression.py:143` 让 N13 单层恒用固定三词 `T`，`:145` 让 chain 用该行 `tokens`，19 行里 N13 是「免考卷」；对齐后反转成 66 vs 69（`:282`）。⇒ `FN(n13)=3` 这个基准本身不可作分母。
2. **训练集 = 测试集 + 标注可变**：`CHAIN_VS_SINGLE.md:129` / `:276` / `:282` 实读——`_n13_regression.py:104-112` 把探针漏网的 5 条形态**回灌**成 N19–N26 并同步改谓词；72→74 翻 3 条 `expect`、换 4 条样本、换整套算法。本会话实读 `_n13_regression.py:104-112` 原文确认 N19–N26 的「复核 _n13v_final_probe.py V1..V5」「复核 X1..X3」来源标注。
3. **共同盲区被当成「无新增」**：`CHAIN_VS_SINGLE.md:147-149` / `:261` / `:272` 实读——GP-A1/A2/A3 是三层**一起判错**的真断言（K5 放行 + K7 死分支），不进 `conflicts[]`，`GATE_PIPELINE_COMPOSE.md:410` 明写「3 条『三层无分歧地一起判错』根本不进 `conflicts[]`」。「无新漏报」在结构上等价于「两个有同一盲区的系统漏了同 3 条」，`CHAIN_VS_SINGLE.md:263` 自记「三层全 PASS 18 行里 3 行真断言（16.7%）；有效独立层数 ≈1」。

⇒ **「无新漏报」这一句在 74 行语料内部是可复现的真陈述（FN 集合确实相同），但它不是「合成链没放松/没退步」的证明**。它缺少独立 ORACLE、缺盲留出、缺输入契约对齐、缺敏感度注入——正是 2(a) 的 (A)(C)(D)(E) 全缺。`CHAIN_VS_SINGLE.md:282` 自评已到位：「本次评测只能用来定位代码缺陷…不能用来下『合成链 vs 单层』的取舍结论」。

**修复需要**（`CHAIN_VS_SINGLE.md:278-280` 已列，本会话照录评估）：真实件全集定抽样框、train/dev/test 物理隔离且 test 封 SHA 盲评、探针回灌样本归 train 不进 test、GroupKFold 按形态族分组、每行登记 `(id, tokens_sha, text_sha, predicate_sha)` 所有层同一 `tokens`、独立真值双盲 + κ、bootstrap CI；再把「无新 FN」改写为「相对独立 ORACLE 的 `FN(chain) ⊆ FN(n13)` 且注入已知 FN 时报警」。

### 3(c) N13「正 16/16 负 26/26」样本构成与训练集=测试集

本会话实跑：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_n13_20261109/_n13_regression.py > D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnr_n13_replay.txt
EXIT=0
```
输出（`_fnr_n13_replay.txt`）：
```
正样本小计：放过 16 / 误拦 0 / 合计 16
负样本小计：抓住 26 / 漏网 0 / 合计 26
正样本 0 误拦 = True (16/16)   负样本 0 漏网 = True (26/26)
真件 0 命中 D = True   ALL_PASS = True
```
（`_n13_regression.py` 无 `write_text`，本会话实读 `:236-259` 确认仅打印 + `sys.exit`，故可在只读域安全运行；输出重定向到写域。）

**样本构成**（`_n13_regression.py:46-113`，本会话实读逐条）：
- 正样本 16：`P01–P10` 是**真件逐字行**（`_lb_BOUND_VOLUME.md:28/275/174`、`LEDGER_BOUND_VOLUME.md:54/77/79/87-88/338/209/242`），`P11–P16` 是作者构造（`_n13_regression.py:68-79`）。即 10 条真件摘录 + 6 条构造。
- 负样本 26：`N01–N18` 构造（`_n13_regression.py:86-103`）；**`N19–N26` 这 8 条是 `:104-112` 明写的「复核 verdict=partial 的 ④，5 条样本外真断言（曾 5/5 漏网）」回灌**，逐条标注来源 `复核 _n13v_final_probe.py V1..V5` / `复核 X1..X3`。

**有无训练集 = 测试集问题**：**有，且是三重**。① `N19–N26` 来自探针暴露的漏网形态，与修复后的谓词 `_n13_predicates.py:76-86,147-177` 的 `_SPLIT_ASSERT`/`_line_positive`/`_prefix_is_subject` 同步构造（`GATE_N13_QUOTED_ASSERTION.md:255`、`:286` 实读；`CHAIN_VS_SINGLE.md:129` 同判）；② `GATE_N13_QUOTED_ASSERTION.md:21` / `:373` 自述「负样本 18 → 26 条」「**判据未放宽**：正样本数量仍 16、真件仍 0 D」——这正是**用同一批样本同时当设计依据和验收依据**；③ `GATE_N13_QUOTED_ASSERTION.md:480` 自记 `verdict = partial ⇒ unconfirmed`（本轮修订未经复核方重签），`:442/:465-467` 自记英文完成词、分离型双重否定仍漏判，`:472` 自记「封闭词表 + 逐行微段正则的固有边界，不宣称完备」。

⇒ `16/16 + 26/26` 是**在同一份作者自建语料上的自测通过**，不是泛化点估计。`CHAIN_VS_SINGLE.md:291` 另记 `_cs_holdout.py` 的 20 条示例性扰动中 3 条与回归语料逐字重复，其 80%/94.1% **不是泛化点估计，标「未验」**——所谓留出集也不干净。

**修复需要**：把 `N19–N26`、GP-A 整族标 `source=probe_failure_of:<probe_id>` 归 train；由未参与者另造同义改写/换主语/换否定构式/CRLF 变体作为封 SHA 的一次性 test；预注册 `fp/fn` 口径；报告「不含回灌样本的 test 成绩」。

### 3(d) 逐个「还剩多少可信」

| 结论 | 还剩多少可信 | 修复路径 |
|---|---|---|
| ① R9 升级「没放松」 | **0（作为证明）；「5 处是语义在场」仍可信但属另一命题** | 见 3(a) 五步；在 L1/L2/L3 + 元检验通过前，`no_relaxation` 不得写 PASS |
| ② 合成链「69/74，无新漏报」 | **数字可复现（本会话核对 FN 集合完全相同）；作为「没退步」的推论不可信** | 输入契约对齐 + 盲留出 + 独立 ORACLE + 注入敏感度；`69/74 < 71/74` 的比较按 `CHAIN_VS_SINGLE.md:222` 已标 `partial / unconfirmed` |
| ③ N13「正 16/16 负 26/26 全过」 | **作为「作者自建语料上跑通」可信（本会话 EXIT=0 复跑）；作为「判据稳健 / 未放宽」部分可信偏低** | 回灌样本隔离、第三方盲留出、verdict 重签；`GATE_N13_QUOTED_ASSERTION.md:480` 自身标 `unconfirmed` |

三者共同病灶：**验收集与被验收对象同源**，且都缺「注入已知错误看是否报警」这一步。

---

## 4 第四步：判别「检验是否有效」的一般方法

### 4(a) 通用判据（拿到任何「X 没有 Y」类断言）

五问，任一答不出即判检验无效（不是「结论错」，是「检验不成立」）：

1. **真值异源否**：判据用的「标准集合」（白名单 / 基线 / expect 表 / 指纹快照）是不是由被测方自己或派发方预置、且与被测量同源？若 `set(标准) == set(被测规格)`，答案必然是设计后果。
2. **覆盖分母否**：报告里有多少项是**结构性不可能违反**的？把它们单列 `UNTESTED`，禁止计入「通过」。本例 292/302，`coverage_ratio=0.0331`。
3. **敏感度否（决定性）**：能否构造一个「结论为假」的输入使检验 ALARM？**必须实跑，不是声称**。构造不出来 / 实跑仍 PASS ⇒ 装饰。本会话 `_fnr_replay.py` k5 就是决定性反例。
4. **反向误报否**：能否构造「结论为真」的输入使检验 FAIL？本会话 `fp_extra_true_flip` / `fp_literal_insert` / `fp_drop_one_whitelist_pair` 全部 FAIL ⇒ 检验对集合基数过敏、对真值失明。有效检验应只在真值违例时报警。
5. **输入契约对齐否**：比较双方是否同一 `tokens` / 同一语料 / 同一标注 / 同一算法版本？`CHAIN_VS_SINGLE.md:282` 的「免考卷」就是反例。

一句话判据：**「把结论全改成错的，检验是否报警？」不报警的，不是检验。**

### 4(b) 元检验模板（注入已知错误）

```
META_CHECK(checker, good_world, error_injections, benign_variations):
  0. assert checker(good_world) == PASS              # 已知-好世界必须通过
  1. for e in error_injections:                      # 每个已知错误
         assert checker(apply(e, good_world)) == ALARM
  2. for b in benign_variations:                     # 每个良性变化
         assert checker(apply(b, good_world)) == PASS
  3. 输出 (n_errors, n_caught, n_false_alarms)
     有效 ⟺ n_caught == n_errors 且 n_false_alarms == 0
  4. 对每个未抓到的错误，逐层定位是哪一层失效并写进报告
```

注入清单最少覆盖 5 类：**全量错 / 局部错 / 标准集合被污染 / 独立性被破坏 / 谓词放过已知负样本**。本会话 9 种注入 + 2 种良性变化即得 `CHECKER_VALID=true`（`_fnr_check_out.json`）。

### 4(c) 能否自动化：能

方案 = 写域内包装脚本 `_fnr_meta.py`（本会话给出规格，**未实装为独立通用包**；可执行的等价物已落在 `_fnr_check.py:meta_test`）：

- 输入：一个声明式清单 `spec.json`，含 `checker_import`（模块路径 + 函数名）、`good_world`（参数字典或其 JSON 路径 + SHA256）、`injections[]`（每项 `type` ∈ `replace_value / drop_item / flip_oracle / unseal / add_outlier / predicate_patch`，加 `target` 与 `payload`）、`benign[]`、`expected_alarm_layers[]`。
- 执行：`python -I -X utf8 <abs path>/_fnr_meta.py <abs path>/spec.json`；用 `importlib.util.spec_from_file_location` 加载 checker；对每个注入用 `copy.deepcopy` 生成内存副本（不写盘、不动只读域），调用 checker，收集 `VERDICT` 与逐层布尔。
- 封印：对 `good_world`、注入清单、checker 源码三者各算 `hashlib.sha256`，写进输出 JSON，使「元检验跑的是哪一版」可复核。
- 门禁：`n_caught == n_errors && n_false_alarms == 0` 才 `exit(0)`，否则 `exit(1)` 并打印未抓到的注入 id。
- 变体自动生成：`replace_value` 的 payload 从 `non_value_pool = ["见台账","详见附件","待判","尚需核对","不另下结论","本件不重录","TBD"]` 轮换；`add_outlier` 从语料外域随机取；`predicate_patch` 用 wrapper 强制对含「待判/不另下结论」的文本返回 `True`。
- 边界：包装脚本只能注入**规格里声明的**错误类，不能自动发明新的语义错法；这正是需要「独立方盲标注」补的洞，自动化不能替代 ORACLE 异源。

本会话已实跑的等价执行：`_fnr_check.py:249-289` 的 `meta_test()`（`_fnr_check_stdout.txt` 的 `meta_test` 段），9/9 抓、0/2 误报。

### 4(d) 项目里还有哪些「X 没有 Y」类断言可能同样无效（清单）

命令（本会话实跑）：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnr_survey.py
```
输出 `TOTAL MATCH LINES = 347`，按域分布见 `_fnr_survey_out.json` 与 `_fnr_survey_stdout.txt`。同一缺陷嫌疑的清单（**列的是「待查」，未逐件实跑其元检验，不得当作已证伪**）：

| # | 位置 | 断言 | 同类嫌疑 |
|---|---|---|---|
| 1 | `lead/gate_r9sem_20261109/GATE_R9_SEMANTIC_ELEMENT.md:239` / `_r9s_DESIGN.md:216` / `:303` | `outside_whitelist=0 no_relaxation=True` / 未登记 token `R9S ≡ R9，不放宽也不收紧` | **已证伪**（本会话 k1–k5） |
| 2 | `lead/gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md:417`、`_gp_DESIGN.md:353` | 「合成链没有引入新漏报」 | **已评估 3(b)**；同源于内部基准 |
| 3 | `lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md:143` / `CHAIN_VS_SINGLE.md:151` | 「0 条新增 FN」 | 同 2 |
| 4 | `lead/gate_n13_20261109/GATE_N13_QUOTED_ASSERTION.md:21` / `:255` / `:312` / `:373`；`_n13_migration_check.py:72`；`_n13v_migration.py:79` | 「不放宽判据」「判据未放宽」「真断言在改后仍被抓」 | 同 3(c)；用回灌样本自证 |
| 5 | `lead/evidence_indep_20261109/_ei_n13_predicates_src.py:9` | 「复核后收紧，不放宽」 | 疑；需查是否只比集合 |
| 6 | `lead/evidence_indep_20261109/_ei_05_admission.py:281` + `_ei_05_admission_out.json:103` | `otherwise chain verdict unchanged (V1V2 is a rescue layer, not a voter)` | 疑；「unchanged」是否只在 spans==0/全 PASS 时定义，需注入检查 |
| 7 | `lead/gate_postmortem_20261109/GATE_LITERAL_MATCH_POSTMORTEM.md:304` / `_pm_postmortem_20261109.md:262` | 「不引入漏报（只放宽修饰符/空白/分隔符，永不放宽 hex 与编号字符集本身）」 | 疑；「不会引入」是设计论证，未见注入反例 |
| 8 | `lead/count_invariant_20261109/COUNT_INVARIANTS.md:224` | `CE-08 totals unchanged = True recomputed==stored = True —— 即 INV-1 不报、7 键恒等式全成立` | **同类缺陷已被该件自己实证**：「没有任何一条只看两个标量相不相等的断言能发现它」——标量恒等式对集合级错误失明 |
| 9 | `lead/check_masking_20261109/_cm_inject.py:195` | `SOURCE FINGERPRINTS AFTER (must be unchanged)` | 指纹比对类：只对字节变化敏感，对语义漂移无感；但「零改动」命题恰好是字节命题，属**有效**检验的对照例 |
| 10 | `lead/c07_hardening_20261109/HARDENING_PLAN.md:15/:259`、`lead/c07_protocol_attacks_20261109/PROTOCOL_ATTACK_TEST.md:19/:151`、`lead/gate_fp7_20261108/GATE_FALSE_POSITIVE_5_6_7.md:14`、`_r9s_DESIGN.md:6/:38/:348` | 「9/9 MATCH 可证零漂移」「只读域零改动」 | 指纹 + mtime 对**字节级零改动**是合适的检验（对照例：有效）；但不得外推为「语义没变」 |
| 11 | `lead/gate_pipeline_20261109/_gpv_regress.py:5` | 「逐条 74 条不放宽、不缩小」 | 疑；逐条计数相等不等于内容不变 |
| 12 | `lead/gate_r9sem_20261109/_r9s_DESIGN.md:248` | 「旧层保持零改动」「可回滚」 | 指纹类，属有效对照；但「随时可退回」未实跑回滚，**未验** |

**判别要诀**：#9/#10/#12 是「字节没变」命题，用 SHA256 检验是**有效**的（错误 = 字节变，检验会报警）；#1/#2/#4/#6/#7/#8 是「语义 / 行为没变」命题，却用集合相等、标量恒等式、内部基准或设计论证来验，**同类无效嫌疑**。区分标准就是 4(a) 第 3 问。

---

## 5 第五步：结论与建议

### 5(a) 当前 R9 升级整体评级

**部分可信（就「升级本身」）；「不放松」这一条单独判 = 不可信 / 机制 invalid。**

- 可采信：5 处「语义在场、字面缺」的误报判定（上游 `WHITELIST_AUDIT.md:498/:516` 独立 5/5，本会话沿用未重判）；32 域/302 项/翻案 5/白名单外 0、POS 20/20 NEG 24/24 的数字可复现（本会话 `_fnr_replay.py` k0 的 `fidelity_all_match=true`，12/12 字段与只读 JSON 一致）。
- 不可采信：「白名单外 0 ⇒ 没放松」的推论（k1–k5 全 PASS）、「24/24 负样本 ⇒ 对真缺失仍 FAIL 无条件成立」（本会话 L3 实跑 13 条对抗只抓 7 条）。
- 上游 `WHITELIST_AUDIT.md:522` 按 `GATE_R9_SEMANTIC_ELEMENT.md:317` 自身口径判「升级本身 `unconfirmed`、白名单验证机制 `invalid`」。本会话独立结论与之**一致**，且补上两点上游未做的实跑：① 3/4/5 条语义空的梯度（k1–k5 全 PASS）；② 三种「语义正确却 FAIL」的反向假阳性构造。

### 5(b) 「5 条内容对不对」与「机制能否证明它」是两件事

| | 命题 | 判定方式 | 本会话结论 |
|---|---|---|---|
| 内容 | 5 个 `(域, token)` 是否真是「语义在场、字面缺」的误报 | 独立读 4 份主件原文 + 4 份任务书 payload + 逐行 `==` 比对 | **5/5 应保留**（`WHITELIST_AUDIT.md:496-498`）；本会话沿用，未重判 |
| 机制 | `no_relaxation` 能否证明这 5 条（或任何 5 条）没放松 | 注入反例 + 元检验 | **不能**：`_r9s_regress.py:182-185` 丢弃 detail，`:204-206` 只查集合；k5 全错仍 PASS |

**区分的实际后果**：即使 5 条全对，「没放松」依旧没被证明；即使 5 条全错，检验也照样 PASS。二者真值完全独立。`WHITELIST_AUDIT.md:467` 已指出这 5/5 来自「人工独立读原文，不是机制证明」；`:500` 更给出反证——移除 1 项时 `VERDICT=FAIL`，但 FAIL 理由是集合不等，**不是**发现语义错。⇒ 不能用「上一轮已裁定 5/5 保留」来给机制背书，也不能用机制无效来推翻 5/5 内容裁决。

### 5(c) 以后写「不放松」检验的必做清单

1. 先写**可操作定义**（本文 2(a) 的 A–E），禁止「没变得更松」式循环定义；把 `ORACLE` 写成有限真值表 JSON。
2. `ORACLE` 与白名单**异源**：第三方盲标注、先 `hashlib.sha256` 封印预注册、作者不得兼任标注员；检验先验封印再读。
3. 报告**覆盖分母**：结构性不可能违反的项单列 `UNTESTED`，不得计入通过证据（本例应写 292/302 UNTESTED，而不是「302 项全量证明」）。
4. 每个放宽项提交**逐角色正面证据证书**：`file:line` 锚 + 引文 + 每个必选角色的实值 + 指针/占位/未决/否定守卫；黑名单校验值不算正面证据。
5. `VERDICT` 拆成 `whitelist_integrity` / `flip_semantics` / `adversarial_robustness` / `sensitivity` 四个独立布尔，任一 False 即 FAIL；禁止用单一布尔掩盖（照录 `WHITELIST_AUDIT.md:507` 的三拆分并加第四项）。
6. **必跑元检验**：注入「全错 / 局部错 / 标准被污染 / 独立性被破坏 / 谓词放过已知负样本」至少 5 类已知错误，`n_caught == n_errors` 才允许输出 PASS；良性变化不得误报。元检验基线本身必须是**已知-好世界**并单独声明（本会话第一次实跑因基线选错得 `CHECKER_VALID=false`，是实测教训）。
7. 对抗语料（形式像而实质空、同义改写、换主语、换否定构式、词表外形态）由**未参与者**构造并纳入必跑回归，阈值（全部抓住）在跑之前注册。
8. 输入契约对齐：每行登记 `(id, tokens_sha, text_sha, predicate_sha)`；train/dev/test 物理隔离，探针漏网回灌样本只进 train；test 一次性封 SHA 盲评。
9. 同时验**反向误报**：真值正确时不得因集合数量/成员变化报错；本会话 `fp_literal_insert` 就是必须避免的模式。
10. 结论里**强制附一句**：「本检验在以下情形下不报警：______」——把不可证伪的边界显式写出来，而不是藏在 PASS 里。

### 5(d) 本条工作判不了什么（如实列）

1. **未重跑 `_r9s_regress.py` 本体**（`:235-236` 会覆写绝对只读域）。本会话用写域内 `_fnr_replay.py` 内存复刻同一公式，k0 与只读 JSON 12/12 字段保真；但这是**替代实现**，不是跑回归本体。
2. **未独立重判 5 份主件的人工语义裁决**。5/5「应保留」沿用 `WHITELIST_AUDIT.md:496-498` 的独立裁决，本会话只核其机制脱钩，未重读 4 主件全文逐项重判。
3. **未验证真机 / 运行时行为**。零真机纪律：未启动 `gamemd.exe`/`ra2loader`/`YURI.exe`，未 `taskkill`，未读活进程内存；未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。所有结论限于静态文本与内存复算。
4. **未改任何谓词、回归脚本、白名单**；`_fnr_check.py` 的 `repaired_predicate` 与 5 份 `CERTS` 是**演示性假设输入**，只在内存中构造，明确标注为本会话自造，不是第三方盲标注的真实 ORACLE。⇒ 本文 2 的检验是**设计与可行性验证**，不构成对现盘 R9 升级的重新认证。
5. **未跑 `_gp_regression.py` 本体**（`lead/gate_pipeline_20261109/_gp_regression.py:222` 会 `write_text` 回只读域），3(b) 的 FN 核对是读只读 `_gp_regression_out.json` 并独立重算集合；`_gp_regression_v1_union.py` 原脚本未留盘，`CHAIN_VS_SINGLE.md:76` / `:287` 已标「未验重跑」，本会话沿用该「未验」。
6. **未实装通用元检验包装器** `_fnr_meta.py`：4(c) 只给规格；可执行的等价物是 `_fnr_check.py:meta_test`，但它是本项目专用实例化，不是通用包。
7. **4(d) 的清单是「待查」不是「已证伪」**：只做了关键词扫描（347 行），除 #1/#2/#3/#8 外，其余条目**未逐件跑注入元检验**，不得当作已判无效。
8. **未做统计显著性 / 泛化估计**：74 行下差 2 条不显著（`CHAIN_VS_SINGLE.md:278` 已要求 bootstrap CI），本会话未算；`_cs_holdout.py` 示例扰动的 80%/94.1% 按 `CHAIN_VS_SINGLE.md:291` 标「未验」，本会话未补。
9. **未核对 `pf2:200`、批准人实存与权限、输出载荷的「真由该次实跑产生」**：沿用 `WHITELIST_AUDIT.md:526-528` 的「未验」，本会话未补。
10. **未 commit、未 push**；`git log -1` 未查（本任务不需），只读域与两件台账未改/未追加/未覆盖；全部新产物仅落 `lead/falsifiable_no_relax_20261109/`，前缀 `_fnr_`。

---

## 6 本会话实跑命令与产物清单

| 命令（`python -I -X utf8` + 绝对路径） | 输出 |
|---|---|
| `.../_fnr_fingerprints.py` | `_fnr_fingerprints_out.json`：`all_match=true`，9/9 |
| `.../_fnr_replay.py` | `_fnr_replay_stdout.txt` / `_fnr_replay_out.json`：`fidelity_all_match=true`、k0–k5、3 种反向假阳性 |
| `.../_fnr_check.py` | `_fnr_check_stdout.txt` / `_fnr_check_out.json`：L1/L2/L3 + `CHECKER_VALID=true` (9/9 抓, 0/2 误报) |
| `.../_fnr_survey.py` | `_fnr_survey_stdout.txt` / `_fnr_survey_out.json`：347 行同类断言 |
| `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_n13_20261109/_n13_regression.py > .../_fnr_n13_replay.txt` | `EXIT=0`；16/16、26/26、ALL_PASS=True |
| `python -I -X utf8 -c "..."` 读 `_gp_regression_out.json` / `_r9s_regress_out.json` | 见正文 3(b) / 1(a)，无落盘独立文件 |

源码：`_fnr_fingerprints.py` / `_fnr_replay.py` / `_fnr_check.py` / `_fnr_survey.py`。报告：`_fnr_REPORT.md`（本件）。
