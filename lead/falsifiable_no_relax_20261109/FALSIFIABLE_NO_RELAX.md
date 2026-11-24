# FALSIFIABLE_NO_RELAX —— 「不放松」可证伪检验的设计、反例复核与三结论影响评估

> 本件由「可证伪检验撰写员」在唯一写域 `lead/falsifiable_no_relax_20261109/` 内产出。
> 全部实跑命令均为 `python -I -X utf8 <绝对路径>`；指纹一律 `hashlib.sha256`。
> 零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）。
> 只读域与两件台账一律未改、未追加、未覆盖；未 commit、未 push。

---

## 1 目的与边界

### 1.1 目的

把「R9 → R9S 升级**没有放松判据**」这句断言，从「看上去通过了回归」推进到「存在一个输入使它报警」的可证伪地位；并给出三层检验设计、决定性元检验模板、三结论影响评估、项目内同类断言清单与必做清单。

本任务的铁律原文（编排方交付）：**「『不放松』这个断言必须能被证伪。若一个检验在『全部结论都错』时仍报 PASS，它就不是检验，是装饰。」**

### 1.2 边界（本件不做什么）

- **只做检验设计与评估，不改任何谓词、回归脚本、白名单**。未修改 `lead/gate_r9sem_20261109/_r9s_predicates.py`、`_r9s_regress.py`、`lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md`、白名单集合 `WHITELIST`（`_r9s_regress.py:113-119`）、`lead/gate_n13_20261109/_n13_regression.py`、`lead/gate_pipeline_20261109/` 任何文件。
- 要做的实验用**本任务写域脚本**：已有的 `_fnr_*.py` / `_fnrv_*.py`，以及本会话新建的 `_fnrd_verify.py`、`_fnrd_*_stdout.txt`。所有变体在 `copy.deepcopy` / 内存字典里生成，不写盘、不落只读域。
- **不跑会写回只读域的本体**：`_r9s_regress.py:235-236` 有 `(WDIR / "_r9s_regress_out.json").write_text(...)`，`WDIR` 指向绝对只读域 → 本会话不执行，改由 `_fnr_replay.py` 逐行复刻其公式（`_fnr_replay.py:1-9` 自述、`:204-215` 逐字复刻 `:204-206` 与 `:223-229`）。同理未跑 `_gp_regression.py` 本体（`CHAIN_VS_SINGLE.md:288` 自记理由）。
- **不重判 5 份主件的人工语义裁决**：`WHITELIST_AUDIT.md:467/:498/:516` 记 5/5 独立人工判「语义在场」，本会话沿用、未重新裁决，标「沿用上游，未重判」。
- **不做统计显著性、不做泛化点估计**（见 §6 未验项）。

### 1.3 复核 verdict 与本件立场

编排方【复核】回件给的是 **`verdict = partial`**（证据层面 confirmed、核心方法论层面 refuted）。按任务「refuted 或 partial 标 unconfirmed」的要求：

> **本件对「已把『不放松』做成可证伪检验」这一主张登记为 `unconfirmed`（且在决定性反例下判 `refuted`）；对「旧 R9S 的 `no_relaxation` 是装饰性检验」登记为 `confirmed`。**

本会话独立复跑复核方的决定性反例（`_fnrd_verify.py`，输出 `_fnrd_verify_out.json`），逐项确认新 L1/L2/L3 检验在「全部结论都错」时**仍 PASS**，故如实记 `partial / unconfirmed`，不护短、不把 `what` 里的「已做成可证伪检验并实测」当作已证实。详见 §2(d) 与 §6。

---

## 2 上游指纹 + 自证反例复核

### 2(a) 九件上游指纹（本会话实跑）

命令（本会话执行）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnr_fingerprints.py
```

输出：`EXIT=0`，`_fnr_fingerprints_out.json` 逐件 `sha_match: true` / `bytes_match: true`，9/9 与编排方【编排方指纹】逐位一致。另以独立一行命令重算核对（同一 `hashlib.sha256`）：

```
python -I -X utf8 -c "<逐件 open(...,'rb').read() 后 sha256 + len>"
```

逐项输出（`path | sha256 | bytes | 与编排方一致`）：

| # | path | SHA256 | 字节数 | 一致 |
|---|---|---|---|---|
| 1 | `lead/gate_r9sem_20261109/_r9s_regress.py` | `16612625a7a5b11aba8b19c895a612f319bd4421c9c095b2ff8285be9214c4b4` | 11258 | True |
| 2 | `lead/gate_r9sem_20261109/_r9s_regress_out.json` | `5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25` | 75673 | True |
| 3 | `lead/gate_r9sem_20261109/_r9s_predicates.py` | `b0265fc57ef4facd06d92b4852344a80d983f14560a8521525ba18e533ae7034` | 23111 | True |
| 4 | `lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md` | `f9d00b7c9a12a996bac9d89b0bf5a948dfe026e21f472bd825d7924d35a47adc` | 52705 | True |
| 5 | `lead/whitelist_audit_20261109/_wl_selfproof_out.json` | `e389f262e6b54d537f75c50621afa05d76200353de0fa59965adcd3031a92e72` | 880 | True |
| 6 | `lead/whitelist_audit_20261109/_wl_step3_struct_out.json` | `3efc6172228bf1e0ff0f098b63987d214c7009850beeb3a6f6d7b83e8311126c` | 4269 | True |
| 7 | `lead/gate_pipeline_20261109/_gp_regression_out.json` | `d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe` | 38575 | True |
| 8 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 | True |
| 9 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 | True |

`git log -1 --oneline` 输出 `2657458 GOAL-3T: 台账 §400→§508 与 D-07..D-11 裁决登记入账`；`git status --short` 中两件台账为会话前既有 `MM`，只读域无 `_fnr*`/`_fnrv*`/`_fnrd*` 新件。

### 2(b) 语义空仍 PASS：逐项输出

**语义空语料来源**：`lead/whitelist_audit_20261109/_wl_selfproof.py:21-32` 的 5 条逐字片段，被 `_fnr_replay.py:93-106` 原样抄入 `EMPTY`。上游独立实跑 `lead/whitelist_audit_20261109/_wl_selfproof_out.json:2-40` 的记录：`all_5_semantically_empty: true`、`n_flips: 5`、`outside_whitelist: 0`、`no_relaxation: true`、`verdict_simulation: "PASS"`（本会话用 `python -I -X utf8 -c` 完整打印该 JSON 复核）。

命令（本会话执行）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnr_replay.py > D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnrd_replay_stdout.txt
```

`EXIT=0`。`_fnr_replay_out.json` 逐项输出（`k` = 5 条白名单项中被换成语义空的条数）：

| scenario | n_items | n_flips | outside | n_tightens | samples_all_pass | no_relaxation | VERDICT |
|---|---|---|---|---|---|---|---|
| `k0_baseline` | 302 | 5 | 0 | 0 | True | True | **PASS** |
| `k1_empty` | 302 | 5 | 0 | 0 | True | True | **PASS** |
| `k2_empty` | 302 | 5 | 0 | 0 | True | True | **PASS** |
| `k3_empty` | 302 | 5 | 0 | 0 | True | True | **PASS** |
| `k4_empty` | 302 | 5 | 0 | 0 | True | True | **PASS** |
| `k5_empty` | 302 | 5 | 0 | 0 | True | True | **PASS** |

- `fidelity_all_match = True`，`fidelity_vs_recorded` 共 **12** 字段与 `_r9s_regress_out.json` 逐位一致（含 `flip_pairs_identical`）——证明复刻公式不是另一个检验。
- **3 条 / 4 条语义空的结果**：`k3_empty`（3/5 条语义空）、`k4_empty`（4/5 条语义空）与 k5 完全相同：仍是 `no_relaxation=True / VERDICT=PASS`。即**局部全错照样放行**。
- `k5_empty` 是决定性反例：**5 条全错、全部结论都错，仍 PASS**。复核回件亦独立复跑 `_fnrv_replay.py` 得到 `n_wrong_conclusions = 3` 时 `old no_relaxation=True old VERDICT=PASS`。

### 2(c) `no_relaxation` 逐行追（为什么对语义失明）

`lead/gate_r9sem_20261109/_r9s_regress.py`：

- `:113-119` — `WHITELIST` 硬编码 5 对 `(域, token)`；`:120` `FOUR = {d for d, _ in WHITELIST}`。
- `:178-179` — `ok0, lay0 = R9S.R9.r9_element_present(text, k)`；`ok1, lay1, _d = R9S.r9s_element_present(text, k)`。注意第三返回值 `_d`（**语义 detail**）被 `_` 丢弃。
- `:182-185` — 翻案只存 `{"domain", "token", "whitelisted", "main"}`，**不存任何语义内容**；`:180-181` 的 `per_element` 也只存 `token / r9_present / r9_layer / r9s_present / r9s_layer`。
- `:204-206` — 逐字：

```python
OUT["no_relaxation"] = (len([f for f in flips if not f["whitelisted"]]) == 0
                        and len(flips) == len(WHITELIST)
                        and all(f["whitelisted"] for f in flips))
```

三项全是**集合包含 / 基数相等 / 全成员**：`flips` 集合 ⊆ `WHITELIST`、两者数量相等、每个 flip 都带 `whitelisted=True`。全文没有任何一条读取 `text` 语义内容来判真值。

- `:223-229` — `OUT["verdict"] = ("PASS" if (OUT["samples"]["all_pass"] and OUT["no_relaxation"] and all(...four_rows...)) else "FAIL")`，纯布尔合取，无 ORACLE、无覆盖分母、无敏感度。
- `:235-236` — `write_text` 回只读域（`WDIR`），故本会话不跑本体。
- `lead/gate_r9sem_20261109/_r9s_predicates.py:371-402` — `SPECS` 恰好 5 个键；`:426-428` — 未登记 token 时 `R9S ≡ R9`（结构性不动）。`_fnr_check.py` 的 L1 实跑给出 `n_items=302`、`n_structurally_untested=292`、`coverage_ratio=0.0331`（`_fnr_check_out.json`）；**292/302 项在结构上不可能翻案**，却从未被单列为 UNTESTED 从而影响结论。
- 同源证据：`WHITELIST_AUDIT.md:517` 记「`no_relaxation` 只查集合包含（`:204-206`）；292 项结构性不可能翻案；5 条全换『形式像而实质空』仍 `VERDICT=PASS`」；`:522` 记「白名单验证机制 `invalid`（自证循环已用可执行反例证明）」、`升级本身 unconfirmed`。

### 2(d) 反向假阳性构造（真值正确却 FAIL，证明对基数过敏）

同一 `_fnr_replay.py` 的三个 `fp_*` 场景，逐项输出：

| scenario | 构造 | n_flips | outside | no_relaxation | VERDICT |
|---|---|---|---|---|---|
| `fp_extra_true_flip` | 追加第 6 条**真·语义等价翻案**（`_fnr_replay.py:110`、`TRUE_EQUIV = "## 5 附：批准人复核\n审批人 = 丙复核责任人。\n"`，`:193-202`） | 6 | 1 | False | **FAIL** |
| `fp_literal_insert` | 给 ① 补上字面 token（`_fnr_replay.py:115` `LITERAL_INSERT`，真值**变好**、flip 消失） | 4 | 0 | False | **FAIL** |
| `fp_drop_one_whitelist_pair` | 删 1 对白名单（`:275-278`），5 条原文语义全不动 | 5 | 1 | False | **FAIL** |

`WHITELIST_AUDIT.md:500` 独立佐证：「**FAIL 的理由是集合不等，不是发现语义错**」。⇒ 旧检验**对真值失明、对集合基数过敏**；它测的是「两个同源集合是否相等」，不是「有没有放松」。

### 2(e) 决定性复核反例：新 L1/L2/L3 在「全部结论都错」时仍 PASS

编排方【复核】`verdict=partial` 的核心证据是：**新检验同样没满足铁律**。本会话用新建 `_fnrd_verify.py` 独立复现（写域内、纯内存、`importlib` 载入 `_fnr_check.py`）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnrd_verify.py
```

`EXIT=0`，`checker_sha256 = 94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2`，逐项输出：

```
=== (A) exact signature ===
  params = ['items','flips','whitelist','registered_tokens','spec_keys','certificates',
            'spec_roles','predicate','adversarial_corpus','predicate_author',
            'whitelist_author','whitelist_sealed','mutation_payload']
  has exact artifact/text parameter? = False
  BASELINE good_world VERDICT = PASS

=== (B) all 5 artifacts semantically empty, certs untouched ===
  n_artifacts_replaced = 5
  VERDICT = PASS  L1/L2/L3 = True True True

=== (C) fabricated anchors/quotes + self-declared independence ===
  VERDICT = PASS  L2_ok = True  L2_problems = []
  certificate_ok resolves anchor against a real file? = False
  L1/L2/L3 implementation computes a seal hash? = False

=== (D) bounded-tightening (B) and coverage (C) ===
  'tighten' in non-comment L1/L2/L3 code = 0
  coverage is ever a FAIL condition? = False
  ORACLE applies to 5 flips out of 302 items

=== (E) novel empties with NO author guard word ===
  N-EMPTY-1  author_guard_hit=False R9S=True  repaired=True  caught? False
  N-EMPTY-2  author_guard_hit=False R9S=True  repaired=True  caught? False
  N-EMPTY-3  author_guard_hit=False R9S=False repaired=False caught? True
  'good world' + 3 novel empties: VERDICT=ALARM caught=14/16
```

逐行归因（全部落到 `lead/falsifiable_no_relax_20261109/_fnr_check.py`）：

- `:227-231` — `no_relaxation_check(...)` 的 13 个参数**没有任何交付件正文 / artifact / text 槽位**（`adversarial_corpus` 是 13 条对抗语料 `:291-305`，不是 5 份真实主件）。把 5 份真实主件全换成语义空、证书原样不动 ⇒ **(B) 仍 PASS**。这正是铁律所指「全部结论都错却 PASS」。
- `:95-124` — `certificate_ok()` 只用正则 `^.+:\d+$` 验锚点是否存在格式（`:100`），**从不解析文件**（我的探针：`certificate_ok resolves anchor against a real file? = False`）；独立性只比两个作者字符串（`:120-121`）与一个布尔（`:122-123`），**从不校验封印 hash**（`L1/L2/L3 implementation computes a seal hash? = False`）。把 5 份证书的 `anchor` 改成 `nowhere/FAKE_i.md:999`、`quote` 明写「凭空编造」、角色实值保留、`oracle_author='independent_blind_adjudicator'` / `oracle_sealed=True` 全部由我键入 ⇒ **(C) 仍 PASS，`L2_problems=[]`**。ORACLE 异源是可自证的装饰字段。
- `:70-92` 声明的 (A)(B)(C)(E)：**(B) bounded tightening 未实现**（非注释实现代码中 `tighten` 出现 0 次）；**(C) 覆盖只报告不门禁**（`check_l1` 的 5 条 `problems.append` 在 `:140-150`，无一条与 `coverage_ratio` 相关，我的探针确认 `coverage is ever a FAIL condition? = False`；ORACLE 只作用于 5 个 flip、不覆盖 302 项）；**(E)** 靠 `:486` 往 `spec_keys` 塞一个 V1 里不存在的 `{"额外预留要素"}`、`whitelist_author` 默认 `"independent"`（`:230`）、`whitelist_sealed` 默认 `True`（`:230`）均由调用方自填。
- `:471-483` — 「已知-好世界」的 `repaired_predicate` 守卫词表与 13 条对抗语料是同一批短语（故 `synthetic_predicate_adversarial_catch = 13/13`，`_fnr_check_out.json`）。我另造 3 条不含任何守卫词的语义空（N-EMPTY-1/2/3）：前两条 `R9S=True / repaired=True / caught=False` ⇒ **基线部分循环**；把它们追加进对抗语料后「好世界」才变 `ALARM caught=14/16`。复核方亦独立造 RV-E1/E2/E3 得同样结论（`_fnrv_adversarial_out.json` 的 `my_corpus_full_check: 7/16`）。
- `:309-313` 与 `_fnr_REPORT.md:427` 自认 `CERTS` 是「本会话自造、非第三方盲标注的真实 ORACLE」，检验只是「设计与可行性验证，不构成重新认证」；`_fnr_check.py:385-393` 的 `w_all5_empty` 名为「all 5 conclusions wrong」，实际只改 `certificates` 的角色值/标志位，**未改交付件文本**。故 9/9 注入报警真实但**作用域错位**。

> **结论（如实登记）**：旧 `no_relaxation` = 装饰（confirmed）；新 L1/L2/L3 = 设计蓝图，但按本任务铁律**同样不是检验**（在「全部结论都错」时仍 PASS），故 `what` 的「已做成可证伪检验并实测」标 **`refuted` / `unconfirmed`**，复核 `verdict = partial` 如实照记。

---

## 3 可证伪检验设计

### 3(a) 「不放松」的可操作定义（非循环）

设 `V0` 为旧谓词、`V1` 为新谓词、`I` 为有限可枚举项全集、`ORACLE: I → {0,1,UNVERIFIABLE}` 由**未参与 V1 设计与派发的独立方在 V1 运行前盲标注**并以 `hashlib.sha256` 封印预注册（`truth=1` 表示「该交付件中确实逐角色交付了所需语义内容」）。

```
NO_RELAXATION :=
  (A) SOUNDNESS            ∀i∈I: V0(i)=0 ∧ V1(i)=1  ⇒ ORACLE(i)=1
  (B) BOUNDED TIGHTENING   ∀i∈I: V0(i)=1 ∧ V1(i)=0 ⇒ ORACLE(i)=0
  (C) ORACLE COVERAGE      |{i : ORACLE(i)≠UNVERIFIABLE}| = |I|
                           结构性不可能翻案的项单列 UNTESTED，绝不计作证据
  (D) SENSITIVITY          ∃ 已知错误注入 e: ORACLE(e)=0 ∧ V1(e)=1
                           且 CHECK(e)=ALARM   【由元检验实跑证明，不是声称】
  (E) WHITELIST PROVENANCE 白名单先封印预注册，且
                           set(白名单 token) ≠ set(V1.spec_keys)
```

与 `_fnr_check.py:70-92` 的声明相比，本定义把 (C) 明确为**硬门禁**而非报告字段、把 (D) 的注入对象明确为**交付件文本本身**（不是证书字典），并要求 (A)(B) 在**全部 `I`** 上而非只在 5 个 flip 上成立。

### 3(b) L1 结构 / L2 语义 / L3 对抗

| 层 | 要判什么 | 必须报警的条件 | 现盘实跑 |
|---|---|---|---|
| **L1 结构** | 集合包含 + 数量 + 覆盖分母 + 同源检测 | `outside≠0` / `len(flips)≠len(WL)` / `self_certified=True` / `coverage_ratio` 低于预注册阈值 / 白名单未封印 / 白名单作者=谓词作者 | `_fnr_check_out.json`：`n_items=302`、`n_flips=5`、`outside_whitelist=0`、`n_structurally_untested=292`、`coverage_ratio=0.0331`、`self_certified=True` ⇒ `VERDICT=ALARM` |
| **L2 语义** | 每翻案项须交 `file:line` 锚 + 引文 + **每个必选角色的正面实值** + 指针/占位/未决/否定守卫 + 独立封印 ORACLE 一致 | 缺证书 / 任一角色非实值 / `oracle_author==predicate_author` / `oracle_sealed=False` / **锚点在真实文件里解析不到或引文与 `file:line` 不符** / 封印 hash 不匹配 | `_fnr_check.py:95-124` 现实现只做前 4 项；后 2 项缺失 ⇒ §2(e) 反例 (C) |
| **L3 对抗** | (i) 预注册「形式像而实质空」语料**全部判 ABSENT**；(ii) 变异注入——逐个角色值换成「见台账登记，本件不重录」必须报警；0 报警即判检验 INVALID | 任一空语料判 PRESENT / 任一变异未报警 / **注入交付件正文为语义空时未报警** | 现盘 `7/13 caught`（泄漏 CF3/CF5/WCF5/V2/V3/V6）、`15/15` 变异报警（`_fnr_check_out.json`）；新增 3 条无守卫词空项后 `caught=14/16`（`_fnrd_verify_out.json`） |

**关键修正（本件相对 `_fnr_check.py` 的设计增量，仅作为规格，不实装改动）**：`no_relaxation_check` 必须新增 `artifacts: dict[(domain,token), str]` 参数，L2 必须把 `cert.anchor` 解析到真实文件、把 `cert.quote` 与该文件该行逐字比对、把 `cert.oracle_*` 与预注册封印表按 `hashlib.sha256` 验证；L3 的敏感度注入必须**同时**注入 `artifacts` 文本，而不只是 `certificates`。

### 3(c) 可粘贴片段

以下为**可直接粘贴**的核心片段（来自 `_fnr_check.py:62-67, 95-124, 127-158, 179-224, 227-242, 249-284`，本件按 §3(b) 的增量补了 `artifact_text` 校验；片段本身只在本文件与写域脚本内使用，不改任何只读域文件）。

**片段 1 —— 非实值守卫与 operative definition 的可执行骨架**

```python
import re, hashlib, json, copy

NON_VALUE_RE = re.compile(
    r"见台账|详见|参见|见附件|见上|见下表|以.{0,6}记载为准|不另下结论|不重录|"
    r"不予判定|暂不作判定|待判|待定|待补|待验|待查|待确认|尚需|尚未|需进一步|"
    r"是否|并非|不可重建|无法重建|未能重建|未验|未采集|无输出|"
    r"^(?:TBD|N/?A|待定|待指定|未定|未知|略|\.{2,}|…+)$"
)

# NO_RELAXATION := (A)..(E)；每个量词跑在有限 I 上，ORACLE 是具体 JSON 表
def no_relaxation(items, v0, v1, oracle, oracle_seal_sha256,
                  whitelist, spec_keys, artifacts, certificates, checker):
    I = list(items)
    A = all(oracle[i] == 1 for i in I if not v0(i) and v1(i))
    B = all(oracle[i] == 0 for i in I if v0(i) and not v1(i))
    C = sum(1 for i in I if oracle.get(i) is not None) == len(I)
    D = checker.sensitivity_proved            # 由 meta_test 实跑置位
    E = (whitelist.sealed and
         set(whitelist.tokens()) != set(spec_keys))
    return A and B and C and D and E
```

**片段 2 —— L2 必须解析真实文件与封印（补上现实现缺的两项）**

```python
def certificate_ok_v2(cert, required_roles, root, oracle_table, seal_sha256):
    problems = []
    # (a) 锚点：格式 + 真实文件 + 引文逐字比对（现实现只有格式）
    anchor = cert.get("anchor", "")
    if not re.search(r"^.+:\d+$", anchor):
        problems.append("L2a: no file:line anchor"); return (False, problems)
    path, lineno = anchor.rsplit(":", 1)
    f = root / path
    if not f.is_file():
        problems.append("L2a: anchor file does not exist: %s" % path)
    else:
        lines = f.read_text(encoding="utf-8", errors="replace").split("\n")
        if cert.get("quote", "") not in "\n".join(lines[max(0,int(lineno)-3):int(lineno)+3]):
            problems.append("L2a: quote not found near %s" % anchor)
    # (b)(c) 逐角色正面实值，拒绝指针/占位/未决/否定
    for r in required_roles:
        v = str(cert.get("roles", {}).get(r, ""))
        if not v or len(v) < 2 or NON_VALUE_RE.search(v):
            problems.append("L2c: role %s is not a delivered value: %r" % (r, v[:40]))
    # (d) ORACLE 异源：不能靠自填字符串，必须与预注册封印表 hash 一致
    key = cert["item_key"]
    if hashlib.sha256(json.dumps(oracle_table, ensure_ascii=False,
                                 sort_keys=True).encode()).hexdigest() != seal_sha256:
        problems.append("L2d: oracle table does not match pre-registered seal")
    if oracle_table.get(key) is not True:
        problems.append("L2d: pre-registered ORACLE says content NOT delivered")
    return (len(problems) == 0, problems)
```

**片段 3 —— 元检验（注入错误必须报警；基线必须是已知-好世界）**

```python
def meta_test(checker, good_world, error_injections, benign_variations):
    assert checker(**good_world)["VERDICT"] == "PASS"       # 0. 已知-好世界
    caught = [e["id"] for e in error_injections
              if checker(**e.apply(copy.deepcopy(good_world)))["VERDICT"] == "ALARM"]
    false_alarms = [b["id"] for b in benign_variations
                    if checker(**b.apply(copy.deepcopy(good_world)))["VERDICT"] == "ALARM"]
    valid = (len(caught) == len(error_injections) and not false_alarms)
    for e in error_injections:                              # 4. 未抓到的逐层定位
        if e["id"] not in caught:
            print("UNCAUGHT", e["id"], "-> inspect L1/L2/L3 separately")
    return {"n_errors": len(error_injections), "n_caught": len(caught),
            "n_benign": len(benign_variations), "n_false_alarms": len(false_alarms),
            "CHECKER_VALID": valid}
```

`_fnr_check.py:249-284` 的 `meta_test` 实跑（本会话命令 `python -I -X utf8 .../_fnr_check.py`，`EXIT=0`）：`synthetic_baseline_VERDICT=PASS`、`n_wrong=9 n_wrong_caught=9`、`n_good=2 n_false_alarms=0`、`CHECKER_VALID=true`、`synthetic_predicate_adversarial_catch=13/13`；`old_check_on_ALL_5_WRONG = {'no_relaxation': True, 'VERDICT': 'PASS'}`（`_fnr_check_out.json`）。**但这 9 种注入全部只改证书、不改交付件文本**，其「已证伪」范围仅限「已证伪旧检验的装饰性」，不构成重新认证（§2(e)）。报告 §2(e) 另如实记录中间态：第一次把现盘（本身有缺陷）当基线得 `CHECKER_VALID=false`、2 个良性变化被误记误报，改用合成 `repaired_predicate` 世界后才 PASS。

---

## 4 三结论影响评估

三个结论逐个重评，不护任何一个。

### 4.1 ① R9 升级 —— 分两件事判，必须分开

| 子命题 | 评级 | 依据 |
|---|---|---|
| 「5 处是语义在场的误报判定」 | **可信，但来自人工独立读原文，不是机制证明** | `WHITELIST_AUDIT.md:498`（应保留 5 / 应移除 0）、`:516`（自读 4 主件原文 + 解 payload + 逐行 `==`，5/5）、`:467`（「来自**人工独立读原文**，不是机制证明」）。本会话**沿用、未重判** |
| 「没放松」的证明 | **不可信 / 机制 invalid** | `_r9s_regress.py:182-185`（丢弃语义 `_d`）、`:204-206`（纯集合包含/基数）、`:223-229`（纯布尔）；292/302 项结构性不翻案；k1–k5 全 PASS；`WHITELIST_AUDIT.md:517/:522` 记 `invalid` / `unconfirmed`；本会话另补 k1–k5 梯度 + 3 个反向假阳性实跑 |

附带证据（样本层也不能当作泛化证明）：`_fnr_replay.py` k0 保真复算 `samples_all_pass=True`（44 样本确实全过），但 `_r9s_samples.py:2-9` 自述「构造语料，全部纯文本」、`WHITELIST_AUDIT.md:106` 记 3/20 走 `raw` 短路（真测语义层只 **17/20**）、`_wl_step3_struct_out.json:211-212` 记第三方近似负样本 `v1_v5_caught=2` / `all7_caught=2`（2/5、2/7）、`WHITELIST_AUDIT.md:465` 记 CF 5 条对抗 2 条误判、WCF 1/5 误判。本会话 `_fnr_check_out.json` 的 `adversarial_baseline`：`caught_by_CURRENT_R9S = 7 / 13`（13 条里漏 6 条）。

**修复需要什么**（不是「需加强检验」）：① 第三方盲标注 302 项真值表，封 `hashlib.sha256` 预注册，且标注方未参与 V1 设计/派发；② 白名单与 `SPECS` 解同源（现 `:113-119` 的 5 对恰是 `_r9s_predicates.py:371-402` 的 5 键）；③ 每翻案项交逐角色正面证据证书，且锚点/引文/封印由检验器**实际解析校验**；④ CF/WCF/V 全族纳入必跑回归并预注册；⑤ **元检验不过不得写 PASS**，且元检验的注入必须覆盖「交付件正文被换成语义空」这一类。

### 4.2 ② 合成链「69/74，无新漏报」—— 是同一类缺陷，且更重

**检验是不是同类？是。** 它用的「没有引入新漏报」判据，是同一份 74 行语料上 `FN(chain) == FN(n13)` 且 FN 集合相同。本会话独立重算：

```
python -I -X utf8 -c "<读 _gp_regression_out.json，按 expect=='CATCH' 且 n13/chain=='PASS' 取 id>"
```

输出：`n13 fn= 3 ids= ['GP-A1','GP-A2','GP-A3']`、`chain fn= 3 ids= ['GP-A1','GP-A2','GP-A3']`、`IDENTICAL SET: True`、`corpus_n= 74`。`GATE_PIPELINE_COMPOSE.md:417` 与 `_gp_DESIGN.md:353` 逐字写「合成链**没有引入新漏报**」。⇒ **这是内部两考生的分差，不是相对独立真值没新增漏报**：缺 (C) ORACLE 异源、(A) 对 `I` 的健全性、(D) 注入已知 FN 看是否报警。

叠加缺陷（均实读 `file:line`）：

- `CHAIN_VS_SINGLE.md:282` —「本次最大方法论缺陷」：`_gp_regression.py:143` 让 N13 恒用固定三词 `T`、`:145` 让 chain 用该行 `tokens`，19 行里 N13 在不含待判 token 的词表上被记「PASS 且判对」（**免考卷**），对齐后反转为 **66 vs 69**。⇒ **训练集 = 测试集 + 标注可变 + 输入契约不对齐**。
- `CHAIN_VS_SINGLE.md:129` — 明写 `_n13_regression.py:104-112` 的 N19–N26 按探针 `V1..V5 / X1..X3` 造出并同步补谓词；`CHAIN_VS_SINGLE.md:151` 自认「0 条新增 FN」。
- `GATE_PIPELINE_COMPOSE.md:410` — 3 条「三层无分歧地一起判错」**根本不进 `conflicts[]`**；`CHAIN_VS_SINGLE.md:263` —「三层全 PASS 18 行里 3 行真断言（16.7%）；**有效独立层数 ≈1**」。⇒ 三层不是三个独立证人。
- `CHAIN_VS_SINGLE.md:291` — 正式盲留出集未做，`_cs_holdout.py` 20 条里 3 条与回归逐字重复，80%/94.1% 标「未验」。

**评级**：数字可复现（FN 集合确实相同），但「没退步 / 没放松」的推论**不可信**；`CHAIN_VS_SINGLE.md:282` 自评亦承认不能用来下取舍结论。

**修复需要什么**（逐条照 `CHAIN_VS_SINGLE.md:278-280`）：① 按域 × expect 分层抽样定抽样框；② `train`/`dev`/`test` 物理隔离，`test` 一次性封 SHA 盲评，N19–N26、GP-A 整族归 `train` / `adversarial`，**不得进 test**；③ GroupKFold 按形态族分组避免同形泄漏；④ 每行写 `(id, tokens_sha, text_sha, predicate_sha)`，输入契约列为硬性前提；⑤ bootstrap CI 报区间而非点估计；⑥ 把命题改写为可证伪形式「相对独立 ORACLE 的 `FN(chain) ⊆ FN(n13)` **且**注入一条已知 FN 时 `CHECK=ALARM`」。

### 4.3 ③ N13「正 16/16 负 26/26」

命令（本会话执行；先确认脚本无写 API）：

```
grep -nE "write_text|open\(.*['\"]w|mkdir|rename|unlink|\.write\(" lead/gate_n13_20261109/_n13_regression.py   → NONE
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_n13_20261109/_n13_regression.py > D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnrd_n13_replay.txt
```

`EXIT=0`，输出：`正样本小计：放过 16 / 误拦 0 / 合计 16`、`负样本小计：抓住 26 / 漏网 0 / 合计 26`、`ALL_PASS = True`。脚本 `:236-259` 无 `write_text`（实读），故在只读域安全运行，输出重定向到写域。⇒ 作为「**作者自建语料上跑通**」**可信**。

**样本构成**（`_n13_regression.py:46-113` 实读）：正 16 = `P01–P10` 十条真件逐字摘录（`:48-67`，逐条注明 `:28/:275/:54/:77/:79/:87-88/:338/:209/:242/:174`）+ `P11–P16` 六条构造（`:68-79`）；负 26 = `N01–N18` 构造（`:86-103`）+ **`N19–N26` 八条由探针漏网形态回灌**（`:104-112` 明写「第二轮：复核 verdict=partial 的 ④，5 条样本外真断言（曾 5/5 漏网）」，逐条标 `复核 _n13v_final_probe.py V1..V5` / `复核 X1..X3`）。

**训练集 = 测试集问题：有，且三重**：

1. `N19–N26` 来自探针暴露的漏网形态，与修复后的谓词补强同步构造（`GATE_N13_QUOTED_ASSERTION.md:255`、`:373`；`CHAIN_VS_SINGLE.md:129` 同判）⇒ 回灌样本同作**设计依据与验收依据**。
2. `GATE_N13_QUOTED_ASSERTION.md:21` / `:373` 以「负样本 18 → 26 条」「**判据未放宽**：正样本数量仍 16、真件仍 0 D」自证未放宽 ⇒ 正是用同一批样本同时当设计依据和验收依据；且「数量不变」本身是集合基数论据，与 §2(c) 同源。
3. `CHAIN_VS_SINGLE.md:291` 记所谓 holdout 20 条中 3 条与回归逐字重复 ⇒ 80%/94.1% 标「**未验**」，留出集也不干净。

`GATE_N13_QUOTED_ASSERTION.md:480` 自记 `verdict = partial ⇒ unconfirmed`（本轮修订未经复核方重签）；`:442/:465/:472` 自记分离型双重否定、英文完成词仍漏判、封闭词表 + 逐行微段正则「不宣称完备」。

**评级**：作为「判据稳健 / 未放宽」**可信度偏低**（`unconfirmed`）。

**修复需要什么**：① `N19–N26`、GP-A 整族标 `source=probe_failure_of:<probe_id>` 归 `train`，**报告必须同时给「不含回灌样本的 test 成绩」**；② 由未参与者按同义改写 / 换主语 / 换否定构式 / CRLF 变体批量造，封 `SHA256` 一次性 `test`；③ 预注册 `fp/fn` 口径与规则变更/语料变更分账；④ `unconfirmed` 需复核方重签才升 confirmed。

### 4.4 共同病灶

**验收集与被验收对象同源，且都缺「注入已知错误看是否报警」这一步。** 三件共享的结构病名即 **训练集测试集** 重叠（`train=test`：回灌样本同作设计依据与验收依据、留出集逐字重复、expect 可随谓词补强改写），且三件都没有敏感度注入。 `WHITELIST_AUDIT.md:500` 另证：移除 1 项白名单时 FAIL 的理由是集合不等而非发现语义错 —— 与 §2(d) 的 `fp_drop_one_whitelist_pair` 完全一致。② 的 `FN(chain)==FN(n13)`、③ 的「16/16 + 26/26」、① 的 `flips==WHITELIST` 是同一个结构：**两个同源量的相等性被当成真值**。

---

## 5 通用判据、元检验模板、自动化方案、同类断言清单

### 5(a) 传任何「X 没有 Y」断言的判据（五问，任一答不出即判检验无效）

1. **真值异源否**：判据用的标准集合（白名单 / 基线 / expect 表 / 指纹快照）是不是由被测方或派发方预置、且与被测量同源？若 `set(标准) == set(被测规格)`，答案必然是设计后果。本例：`_r9s_regress.py:113-119` 的 5 对 ≡ `_r9s_predicates.py:371-402` 的 5 键。
2. **覆盖分母否**：有多少项**结构性不可能违反**？单列 `UNTESTED`，禁止计入「通过」。本例 292/302，`coverage_ratio=0.0331`（`_fnr_check_out.json`）。
3. **敏感度否（决定性）**：能否构造「结论为假」的输入使检验 ALARM？**必须实跑，不是声称**。`k5_empty` 与 §2(e) 的 (B) 是决定性反例。
4. **反向误报否**：能否构造「结论为真」的输入使检验 FAIL？`fp_extra_true_flip` / `fp_literal_insert` / `fp_drop_one_whitelist_pair` 全部 FAIL ⇒ 对集合基数过敏、对真值失明。有效检验应只在真值违例时报警。
5. **输入契约对齐否**：比较双方是否同一 `tokens` / 同一语料 / 同一标注 / 同一算法版本？`CHAIN_VS_SINGLE.md:282` 的「免考卷」是反例。

一句话判据（任务铁律）：**「把结论全改成错的，检验是否报警？」不报警的，不是检验，是装饰。** 并且 —— 本件补一条，来自 §2(e) —— **「把交付件正文全改成错的（证书一字不动），检验是否报警？」不报警的，同样不是检验。**

### 5(b) 元检验模板（可粘贴）

```
META_CHECK(checker, good_world, error_injections, benign_variations):
  0. assert checker(**good_world).VERDICT == PASS        # 已知-好世界必须通过
  1. for e in error_injections:                          # 每个已知错误
         assert checker(**e.apply(deepcopy(good_world))).VERDICT == ALARM
  2. for b in benign_variations:                         # 每个良性变化
         assert checker(**b.apply(deepcopy(good_world))).VERDICT == PASS
  3. 输出 (n_errors, n_caught, n_benign, n_false_alarms)
     有效 ⟺ n_caught == n_errors 且 n_false_alarms == 0
  4. 对每个未抓到的错误，逐层定位 L1/L2/L3 哪一层失效并写进报告
```

注入清单最少覆盖 5 类：**全量错 / 局部错 / 标准集合被污染 / 独立性被破坏 / 谓词放过已知负样本**；本件追加**第 6 类（必须）**：**交付件正文被换成语义空而证书不变**。少了第 6 类，元检验本身就是 §2(e) 那种装饰。

**基线的硬要求**：`good_world` 必须是**独立构造的已知-好世界**，且其守卫词表不得与对抗语料同源。`_fnr_REPORT.md` §2(e) 如实记录第一次误把现盘（本身有真实缺陷）当基线得 `CHECKER_VALID=false`；`_fnr_check.py:471-483` 的 `repaired_predicate` 与 13 条对抗语料共用守卫词，`_fnrd_verify.py` 的 N-EMPTY-1/2 证明它对无守卫词的新空项仍漏 ⇒ **基线本身部分循环，标 `unconfirmed`**。

### 5(c) 自动化方案

`_fnr_meta.py` 包装器规格（**本会话给出规格，未实装为独立通用包**；可执行等价物是 `_fnr_check.py:249-284` 的 `meta_test`）：

- 输入：声明式 `spec.json`，含 `checker_import`（模块路径 + 函数名）、`good_world`（参数字典或 JSON 路径 + SHA256）、`injections[]`（每项 `type` ∈ `replace_value / drop_item / flip_oracle / unseal / add_outlier / predicate_patch / replace_artifact_text`，加 `target` 与 `payload`）、`benign[]`、`expected_alarm_layers[]`。
- 执行：`python -I -X utf8 <abs>/_fnr_meta.py <abs>/spec.json`；`importlib.util.spec_from_file_location` 加载 checker；每个注入用 `copy.deepcopy` 生成内存副本（不写盘、不动只读域），调用 checker，收集 `VERDICT` 与逐层布尔。
- 封印：对 `good_world`、注入清单、checker 源码三者各算 `hashlib.sha256` 写进输出 JSON，使「元检验跑的是哪一版」可复核。
- 门禁：`n_caught == n_errors && n_false_alarms == 0` 才 `exit(0)`，否则 `exit(1)` 并打印未抓到的注入 id。
- 变体自动生成：`replace_value` 的 payload 从 `["见台账","详见附件","待判","尚需核对","不另下结论","本件不重录","TBD"]` 轮换；`add_outlier` 从语料外域取；`predicate_patch` 用 wrapper 强制对含「待判/不另下结论」的文本返回 `True`；**`replace_artifact_text` 必须存在**，否则不门禁。
- 边界：只能注入**规格里声明的**错误类，不能自动发明新的语义错法；**自动化不能替代 ORACLE 异源**（第三方盲标注 + 封印预注册仍是人/组织流程）。

### 5(d) 项目内同类断言清单与搜索命令

脚本 `_fnr_survey.py:12-14` 的正则：

```python
PAT = re.compile(r"no_relaxation|no_regression|没有引入新漏报|无新漏报|没放松|"
                 r"未放宽|不放宽|不扩散|unchanged|零改动|未变|训练集\s*=\s*测试集|"
                 r"结构性恒|白名单外\s*0|不另下结论(?!.*样本)")
```

`SCAN_DIRS`（`:17-25`）= 13 个近期审计域。命令与输出（本会话执行）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnr_survey.py > D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnrd_survey_stdout.txt
```

`EXIT=0`，`TOTAL MATCH LINES = 348`，按域分布：

| 域 | 行数 | 域 | 行数 |
|---|---|---|---|
| `lead/whitelist_audit_20261109` | 213 | `lead/gate_v1v2_20261109` | 16 |
| `lead/gate_r9sem_20261109` | 64 | `lead/count_invariant_20261109` | 9 |
| `lead/gate_n13_20261109` | 9 | `lead/c07_hardening_20261109` | 8 |
| `lead/gate_pipeline_20261109` | 3 | `lead/chain_vs_single_20261109` | 6 |
| `lead/gate_postmortem_20261109` | 6 | `lead/c07_protocol_attacks_20261109` | 4 |
| `lead/check_masking_20261109` | 4 | `lead/evidence_indep_20261109` | 4 |
| `lead/gate_fp7_20261108` | 2 | | |

**诚实登记的两点偏差**（复核回件 ⑤ 已指出，本会话复跑确认）：① 撰写人报告为 `347`（`_fnr_survey_stdout.txt:1`），本会话复跑为 `348`，差异由另一并行 subagent 于 16:21:19 落 `lead/check_masking_20261109/_cmv_repro.py:148`（撰写人报告 16:16:06 已完成）造成，非撰写人失误；② `_fnr_survey.py:16` 注释称「+ the two ledgers」，但 `SCAN_DIRS` 实为 13 目录且**不含两件台账** ⇒ 348 未覆盖 `PENDING_DECISIONS.md` / `GOAL_THREE_TARGETS_20261018.md`，标**未验**。`_fnr_REPORT.md:371-386` 的 12 条待查清单标「待查未逐件跑」，`:430` 自认不得当作已证伪。

**清单用法**：这 348 行只是「同类断言的候选位置」，**不是 348 个已证伪项**；逐件要按 §5(a) 五问 + §5(b) 元检验跑过才能下结论，本会话未逐件跑（未验）。

---

## 6 复核回件（绑定行）+ 结论 + 必做清单 + 判不了什么 + 未验项

### 6(a) 复核回件绑定行（格式固定）

被核对象 SHA256 = 5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25，字节数 = 75673

复核 `verdict` 如实照记：**`partial`**（证据层面 confirmed；核心方法论层面 refuted）。按任务铁律，**`refuted` 或 `partial` 一律标 `unconfirmed`**：本件对「已把『不放松』做成可证伪检验并实测」标 `unconfirmed`（决定性反例下 `refuted`），对「旧 `no_relaxation` 是装饰」标 `confirmed`。绑定对象为 `lead/gate_r9sem_20261109/_r9s_regress_out.json`，本会话以 `python -I -X utf8 -c` 重算得同一 SHA256 与 75673 字节（§2(a) 第 2 行）。

### 6(b) R9 整体评级

**部分可信；「不放松」单条不可信（`invalid` / `unconfirmed`）。** 与 `WHITELIST_AUDIT.md:522` 一致：可采信的是「5 处确是语义在场、字面缺的真误报」和「升级在预置语料上数字可复现」；不可采信的是「白名单外 0 ⇒ 没放松」这一推论，以及「24/24 负样本 ⇒ 对真缺失仍 FAIL 无条件成立」。本会话另补 k1–k5 梯度、3 个反向假阳性、以及 §2(e) 的新检验反例。

### 6(c) 内容对 vs 机制能证（两条真值独立）

| | 5 条白名单内容判对了 | 5 条白名单内容全错 |
|---|---|---|
| **机制能证明「没放松」吗** | **不能**。即使 5/5 全对，`flips==WHITELIST` 也只是同源集合相等，`no_relaxation` 仍未被证明（`_r9s_regress.py:204-206`） | **不能**。即使 5/5 全错，旧检验照样 PASS（§2(b) k5）；新检验在交付件全空、证书不动时也照样 PASS（§2(e) B） |

- 「内容对」的来源是**人工独立读原文**（`WHITELIST_AUDIT.md:467/:498/:516`），本会话沿用、未重判。
- 「机制能证」要求 (A)–(E) 全成立，其中 (D) 敏感度必须**实跑**证明存在「结论为假且 ALARM」的输入；新旧两版都没满足（旧：k5；新：§2(e) B）。
- `WHITELIST_AUDIT.md:500` 的「FAIL 理由是集合不等不是发现语义错」是这一区分的最直接证据。

### 6(d) 写「不放松」检验的必做清单（逐条可勾，不许用「需加强检验」概括）

1. **预注册 ORACLE**：由未参与 V1 设计/派发的独立方，在 V1 运行前对**有限全集 `I`（本例 302 项）**盲标注真值表，`hashlib.sha256` 封印；`UNVERIFIABLE` 项单列。
2. **解同源**：白名单 token 集合 ≠ `V1.spec_keys`；白名单作者 ≠ 谓词作者；`:113-119` 的 5 对与 `_r9s_predicates.py:371-402` 的 5 键必须解耦。
3. **覆盖分母硬门禁**：`n_structurally_untested / n_items`（本例 292/302、`coverage_ratio=0.0331`）低于预注册阈值即 FAIL，不许只报告。
4. **L1 结构**：集合包含 + 数量 + `self_certified` + 封印校验，全部作为 FAIL 条件。
5. **L2 语义**：每个翻案项交 `file:line` 锚 + 引文 + **每个必选角色的正面实值** + 指针/占位/未决/否定守卫 + 与封印 ORACLE 一致；**锚点必须解析到真实文件、引文必须逐字比对、封印 hash 必须计算**。
6. **L3 对抗**：(i) 预注册「形式像而实质空」语料全部判 ABSENT（现盘 7/13，漏 CF3/CF5/WCF5/V2/V3/V6 必须清零）；(ii) 变异注入逐个角色换「见台账登记，本件不重录」必须报警（现 15/15）；(iii) **新增**：把 5 份交付件正文换成语义空、证书一字不动，必须 ALARM。
7. **元检验**：`META_CHECK` 的 `n_caught == n_errors` 且 `n_false_alarms == 0`；注入至少 6 类（全量错/局部错/标准集合污染/独立性破坏/谓词放过已知负样本/**交付件正文错**）；基线是独立构造的已知-好世界且守卫词表不与对抗语料同源；未抓到的错误逐层定位。
8. **反向假阳性门禁**：`fp_extra_true_flip` / `fp_literal_insert` / `fp_drop_one_whitelist_pair` 三类真值正确输入必须 **PASS**；任一 FAIL 即判检验对基数过敏、无效。
9. **训练/测试隔离**：`N19–N26`、GP-A、CF/WCF/V 标 `source=probe_failure_of:<probe_id>` 归 train；`test` 一次性封 SHA 盲评；报告同时给「不含回灌样本的 test 成绩」。
10. **输入契约对齐**：每行 `(id, tokens_sha, text_sha, predicate_sha)`；`CHAIN_VS_SINGLE.md:282` 的免考卷不得复现。
11. **不许自升 confirmed**：`partial` / `refuted` 一律标 `unconfirmed`，需复核方重签（`GATE_N13_QUOTED_ASSERTION.md:480` 已示范）。
12. **元检验不过不得写 PASS**，且报告必须列出未验项。

### 6(e) 本件判不了什么（诚实边界）

- 判不了「5 条白名单的语义裁决本身对不对」——本会话沿用上游人工裁决，未重判（`WHITELIST_AUDIT.md:498`）。
- 判不了「R9S 在真实全量交付件上到底放没放松」——缺第三方 ORACLE，只能判「现有证明不成立」。
- 判不了「合成链相对独立真值是否真的没新增漏报」——只有内部两考生分差。
- 判不了「N13 判据的泛化性能」——`CHAIN_VS_SINGLE.md:291` 的 holdout 3 条逐字重复，80%/94.1% 已标未验。
- 判不了「348 行同类断言里哪几行已被证伪」——只给了位置清单，未逐件跑。
- 判不了任何统计显著性与置信区间——未做 bootstrap / GroupKFold / Cohen's κ。

### 6(f) 未验项（逐条如实列）

1. **未跑 `_r9s_regress.py` 本体**：`:235-236` 会写回绝对只读域；本会话与撰写人均以 `_fnr_replay.py` 内存复刻（12 字段 `fidelity_all_match=True`），未重跑本体。
2. **未跑 `_gp_regression.py` 本体**：只读域且会写回（`CHAIN_VS_SINGLE.md:288`）；只从 `_gp_regression_out.json` 独立重算 FN 集合。
3. **未重判 5 份主件的人工语义裁决**，沿用 `WHITELIST_AUDIT.md` §3。
4. **未做统计显著性 / 盲留出 / 交叉验证 / GroupKFold / bootstrap CI**；`_fnr_meta.py` **未实装为独立通用包**（只给规格）。
5. **未逐件跑 348 行同类断言清单**；两件台账不在 `_fnr_survey.py:17-25` 的 `SCAN_DIRS` 内（`:16` 注释与实现不符），标未验。
6. **未验证 ORACLE 异源**：`_fnr_check.py:309-313` 自认 `CERTS` 为本会话自造、非第三方盲标注；§2(e) 的伪造证书反例证明该字段可自证。
7. **未做真机 / 采样代码**（按铁律一律未做，非遗漏）。
8. **本会话新建的 `_fnrd_verify.py` 只复现复核方的决定性反例**，未实装 §3(b) 的 `certificate_ok_v2` 为独立包，也未修改 `_fnr_check.py`。

### 6(g) 收尾核对（本会话实跑）

```
git log -1 --oneline                     → 2657458 GOAL-3T: 台账 §400→§508 与 D-07..D-11 裁决登记入账
git status --short | grep <相关域>       → 只读域均为 ?? (会话前既有)，两件台账 MM (会话前既有)
```

本会话新增件全部落在唯一写域 `lead/falsifiable_no_relax_20261109/`：`_fnrd_verify.py`、`_fnrd_verify_out.json`、`_fnrd_replay_stdout.txt`、`_fnrd_check_stdout.txt`、`_fnrd_adversarial_stdout.txt`、`_fnrd_n13_replay.txt`、`_fnrd_survey_stdout.txt`，以及本件 `FALSIFIABLE_NO_RELAX.md`。所有脚本禁用 API 扫描（无 `gamemd.exe` / `ra2loader` / `YURI.exe` / `taskkill` / `MiniDump` / `SuspendThread` / `StackWalk` / `ctypes` / `OpenProcess` / `ReadProcessMemory`）。未 commit、未 push。
