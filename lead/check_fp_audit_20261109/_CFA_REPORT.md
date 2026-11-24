# _CFA_REPORT —— 新检验（L1/L2/L3）假阳性审计

> 检验假阳性审计员，唯一写域 `lead/check_fp_audit_20261109/`，前缀 `_cfa_`。
> 零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）。
> 只读域与两件台账一律未改、未追加、未覆盖；不改新检验、不改任何既有件；未 commit、未 push。
> 全部 Python 均为 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib.sha256`。

## 0 绑定行与实跑命令

被核对象 SHA256 = 94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2，字节数 = 28811

被核对象 = `lead/falsifiable_no_relax_20261109/_fnr_check.py`（新检验的 L1/L2/L3 + meta_test 实现）。
上述指纹与编排方【实跑指纹】一致，本会话用 `python -I -X utf8 -c "import hashlib..."` 独立重算 8/8 全 OK；另对本会话实际读取的 11 个只读件做了指纹登记，见 `_cfa_out.json` 的 `input_fingerprints`。收尾复查 11/11 `ALL_UNCHANGED = True`。

**本会话主实跑命令**（唯一一次完整执行，输出落 `_cfa_stdout.txt` / `_cfa_out.json`）：

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_fp_audit_20261109/_cfa_probe.py
```

另跑：指纹核对 `python -I -X utf8 -c "..."`（8 件 + 11 件复查）、重算 L1 数字 `python -I -X utf8 -c "..."`、Wilson 区间 `python -I -X utf8 -c "..."`、只读件未改复查 `python -I -X utf8 -c "..."`、只读域文件清点 `find ... -type f`。

**执行方式如实登记**：`_fnr_check.py:354-554` 的 `main()` 在 `:548-549` 会 `write_text` 回绝对只读域，故**未执行其本体**。本会话用 `importlib.util.spec_from_file_location` 把它作为模块加载（`_cfa_probe.py:37-41`），直接调用 `no_relaxation_check()` / `check_l1()` / `meta_test()`，所有世界均为 `copy.deepcopy` 内存字典。这是**替代执行**，不是跑检验本体。同理未跑 `_r9s_regress.py` 本体（`_fnr_REPORT.md:22` 已记其会覆写只读域）。

---

## 1 第一步：复核三层结果

### 1(a) 逐层 ok 与 problems

| 层 | ok | problems | 出处 |
|---|---|---|---|
| L1 | `false` | 1 条：`L1: SELF_CERTIFIED -- whitelist token multiset == predicate spec keys; 'outside=0' is a design consequence, not evidence` | `_fnr_check_out.json:10-24` |
| L2 | `true` | `[]`（5 行 `rows[].ok` 全 true） | `_fnr_check_out.json:25-70` |
| L3 | `false` | 6 条 `L3i: adversarial ... judged PRESENT -- semantic leak`（CF3/CF5/WCF5/V2/V3/V6） | `_fnr_check_out.json:71-80` |
| 总 | `VERDICT=ALARM`, `no_relaxation=false` | — | `_fnr_check_out.json:8-9`；合成规则 `_fnr_check.py:238-239` `ok = l1_ok and l2_ok and l3_ok` |

补充：L3 的 `(ii)` 变异注入 15/15 全 alarm（`_fnr_check_out.json:286-288`），`sensitivity_proved=true`；L3 的 fail 完全来自 `(i)` 对**真实 R9S 谓词**的 6 条泄漏，不是 L2 证书检验失效。

### 1(b) SELF_CERTIFIED 的依据与算法

算法在 `_fnr_check.py:137-138`：

```python
wl_tokens = {k for _, k in wl}
self_certified = (wl_tokens == set(predicate_spec_keys))
```

`:148-150` 在 `self_certified` 为真时把该字符串 append 进 `problems`。`main():366-368` 传入 `registered_tokens=set(R9S.SPECS.keys())`、`spec_keys=set(R9S.SPECS.keys())`，白名单 `wl` 来自 `_r9s_regress_out.json` 的 `domains32.whitelist`。

本会话独立重算（`_cfa_stdout.txt` 的 `=== L1 RECOMPUTE ===`）：

```
wl_tokens  = ['可重建','实跑输出','改前改后','脚本存在性','需谁批准']
spec_keys  = ['可重建','实跑输出','改前改后','脚本存在性','需谁批准']
wl_tokens_eq_spec_keys = true
n_spec_keys = 5,  n_whitelist = 5
```

**同源的实证**：`_r9s_regress.py:112-119` 的 `WHITELIST` 是「本次任务书指名要求改判的 5 处（域 + token）」；`_r9s_predicates.py:368` 自述「闭合注册表：key = 门禁必现要素的精确字面串」，`:371-402` 的 `SPECS` 恰好是这 5 个 token 的逐角色展开。`WHITELIST_AUDIT.md:517` 上游判「白名单由派发方预置且与 SPECS 同源」。

★ **措辞与实现不符**：错误消息说 "token **multiset**"，但 `:137-138` 用的是 `set` 相等，丢失了重数。本会话核对 `Counter(k for _,k in wl)` 恰为 5 个 token 各 1 次，两种判定在本例结果相同，但实现是 set 而非 multiset（`_cfa_out.json` 的 `l1_recompute.code_uses_set_not_multiset = true`）。

### 1(c) 292 与 0.0331 的算法

`_fnr_check.py:133-135`、`151-154`：

```
items    = [每个 domains32.rows[].per_element[].token]  (跳过 main_missing)
untested = [i for i in items if i["token"] not in registered_tokens]
coverage_ratio = round((len(items)-len(untested)) / max(len(items),1), 4)
```

本会话独立重算（`_cfa_stdout.txt` 的 `=== L1 RECOMPUTE ===`）：`rows=32`、`skipped_main_missing=0`、`n_items=302`；`registered_tokens` 只有 5 个 SPECS key；命中的 10 项为 `需谁批准×6 + 实跑输出×1 + 改前改后×1 + 脚本存在性×1 + 可重建×1`；故 `n_untested = 302 − 10 = 292`，`coverage_ratio = 10/302 = 0.03311258… → 0.0331`。与 `_fnr_check_out.json:18-20` 完全一致。

★ **关键补充（P11 实跑）**：`coverage_ratio` 只是 `detail` 里的报告项，**不是 FAIL 条件**。把 `registered_tokens` 清空使 `coverage_ratio=0.0`，`check_l1()` 的 `problems=[]`、`L1_ok=true`、总 `VERDICT=PASS`（`_cfa_stdout.txt` `P11 coverage 0.0`）。所以 292/UNTESTED 被诚实报告了，但检验并不因它报警 —— 它是装饰性指标，`_fnrd_verify_out.json:41-48` 上游复核亦已记 `coverage_is_fail_condition=false`。

### 1(d) 7/13 caught 的含义与 6 条漏网

本会话 P6 独立实跑 `R9S.r9s_element_present(txt, tok)` 对 13 条 ADVERSARIAL：

```
7/13 caught, leaked = ['CF3','CF5','WCF5','V2','V3','V6']
```

逐条（`_fnr_check_out.json:82-161`）：

| id | token | present | caught |
|---|---|---|---|
| CF3 | 改前改后 | true | false |
| CF5 | 可重建 | true | false |
| WCF5 | 可重建 | true | false |
| V2 | 需谁批准 | true | false |
| V3 | 改前改后 | true | false |
| V6 | 可重建 | true | false |

含义：**当前在盘 R9S 谓词把 6 条「形式像而实质空」的载荷判为「语义在场」**，即被测对象真有语义泄漏。`_fnr_check_out.json:422-426` 的 `adversarial_baseline.note` 自己写明「R9S itself FAILS this adversarial corpus; the checker reports the leak instead of hiding it」，`_fnr_REPORT.md:254` 与 `WHITELIST_AUDIT.md:517/:522`（机制 `invalid`）同向。⇒ **这一部分的 ALARM 是现状真缺陷，不是新检验误报**。这与 L1 的 SELF_CERTIFIED 必须分开判定（见 §5(a)）。

---

## 2 第二步：量化假阳性（核心）

### 2(a)(b) 10 个「本该 PASS」的良性场景与逐场景 VERDICT

全部由 `_cfa_probe.py:145-236` 构造，均基于作者自己的 known-good `good_base`（`_fnr_check.py:485-488`：`repaired_predicate` 13/13 全抓、`spec_keys` 多一个预留键、whitelist sealed + independent），因此除 S01 外任何 ALARM 都无歧义地是误报。输出：`_cfa_stdout.txt` 的 `=== 10 BENIGN SCENARIOS ===`。

| id | 良性场景 | VERDICT | 触发层 | 误报 |
|---|---|---|---|---|
| S01 | 现状假设成立：白名单 5 项内容正确且语义在场（沿用 `WHITELIST_AUDIT.md:498/:516` 5/5） | **ALARM** | **L1 + L3** | 是（混杂，见下） |
| S02 | 谓词覆盖全部 token，`coverage_ratio=1.0` | PASS | — | 否 |
| S03 | 有第三方盲标注真值表（本会话真算 `hashlib.sha256` 封印） | PASS | — | 否 |
| S04 | 对抗样本全被抓（扩到 16/16） | PASS | — | 否 |
| S05 | **合规同源**：SPECS 就是白名单 5 项的逐角色展开 | **ALARM** | **L1** | 是 |
| S06 | 合规同源 + 全覆盖 + 真第三方封印 | **ALARM** | **L1** | 是 |
| S07 | 合规同源 + 白名单第三方封印且作者独立 | **ALARM** | **L1** | 是 |
| S08 | 追加 1 条真·语义等价翻案（旧检验 `fp_extra_true_flip` 的良性坑） | PASS | — | 否 |
| S09 | 良性引文改写（作者自己的 `g_reworded_quote`） | PASS | — | 否 |
| S10 | 删 1 对白名单并同步删 flip/证书（旧检验 `fp_drop_one_whitelist_pair` 的良性坑） | PASS | — | 否 |

S01 需单独说明：它用**真实在盘** R9S 谓词，故 L3 的 6 条泄漏是**真缺陷**（§1(d)），L1 的 SELF_CERTIFIED 是**误报**。判它「误报」是因为任务前提是「现状假设成立、本该 PASS」；但为避免把真缺陷混淆成误报，下面同时给出剔除 S01 的严格口径。

### 2(c) 假阳性率（本会话实跑，`_cfa_out.json` 的 `fp_rate`）

| 口径 | 良性数 | 误报数 | 假阳性率 | Wilson 95% CI |
|---|---|---|---|---|
| ★ **任务点名的 8 个（S01–S08）** | **8** | **4** | **4/8 = 50.00%** | **[0.215, 0.785]** |
| 全部 10 个（S01–S10） | 10 | 4 | 4/10 = 40.00% | [0.168, 0.687] |
| 严格 9 个（剔除混杂的 S01） | 9 | 3 | 3/9 = 33.33% | [0.121, 0.646] |
| 纯良性 6 个（S02/S03/S04/S08/S09/S10，不含同源与现盘） | 6 | 0 | 0/6 = 0% | [0, 0.390] |

`false_alarm_ids = ['S01','S05','S06','S07']`；S05/S06/S07 的 `L1_problems` 逐字相同，只有那一条 SELF_CERTIFIED。

**★ 结论**：在任务要求的 8 个良性场景里，**4 个被误报（50%）**。误报不是随机的，而是集中于一个判据：合规同源。旧检验踩过的三个基数坑（S08/S09/S10）新检验都正确 PASS，说明它确实修好了「对基数过敏」；但它换上了新的「对同源过敏」。

### 2(d) 「同源即 SELF_CERTIFIED」是缺陷还是设计？

**判：缺陷（过度泛化的硬 FAIL），不是可接受的设计。若项目合规地让两者同源，L1 会永远 ALARM。**

证据链（全部本会话实跑）：

1. **无条件触发**：`_fnr_check.py:137-138` 只比较 `wl_tokens == set(predicate_spec_keys)`，完全不读 `whitelist_author` / `whitelist_sealed` / 任何 ORACLE 或封印。S07 已附真实 `hashlib.sha256` 白名单封印且 `whitelist_author="independent"`，仍 `L1_ok=false`（`_cfa_out.json` `scenario_side_data.S07`）。`:238` 的 `and` 合成使 L1 一票否决总 VERDICT。
2. **修完全部真实缺陷仍报警（P8，决定性）**：`repaired_predicate`（13/13 全抓）+ `registered_tokens=全部 token`（`coverage_ratio=1.0`）+ 第三方封印 ORACLE + sealed 独立白名单，唯一保留「SPECS 同源」。结果 `VERDICT=ALARM`、`L1_ok=false`、`L2_ok=true`、`L3_ok=true`、`L3_caught=13/13`、`L1_coverage_ratio=1.0`，`L1_problems` 仍只有 SELF_CERTIFIED（`_cfa_stdout.txt` `P8 all-repaired`）。⇒ 报警与「现状是否有缺陷」无因果关系。
3. **加一个无关键就翻转（P9）**：作者自己的 `good_base` 只因在 `spec_keys` 里塞了 `"额外预留要素"`（`_fnr_check.py:486`）而 PASS；去掉即 ALARM。`with_dummy_key_VERDICT=PASS` / `without_dummy_key_VERDICT=ALARM`（`_cfa_stdout.txt` `P9 padding trick`）。⇒ 判据量的是「集合不相等」，不是「来源独立」；一个对象可以靠加无关 padding 通过独立性检查。
4. **合规同源在本项目确实存在**：`_r9s_regress.py:112-119` 白名单是任务书指名的 5 处；`_r9s_predicates.py:368-402` 的 SPECS 是「闭合注册表」，正是这 5 个 token 的角色规格展开。把「SPECS 是白名单的展开」当作架构是自然的。上游 `WHITELIST_AUDIT.md:517/:522` 判 invalid 的是「`no_relaxation` 只查集合包含 ⇒ 白名单外 0 不能推出没放松」这条**推论**，不等于「同源本身违规」。
5. **正确定位**：把「`outside=0` 是设计后果」写进 `detail` 作为 **witness / UNTESTED 声明**是合理且必要的（报告项）；把它做成 `problems` 里的硬 FAIL 且 ANY 层 false 即 ALARM，才是过严。独立性应由 L2 对真实封印/作者的**校验**判定，而不是由 L1 的 token 集合相等判定。

⇒ 直接回答任务问题：**会**。只要白名单 token 集恰好等于 `spec_keys`，无论第三方封印、独立作者、全覆盖、ORACLE 齐备与否，L1 恒 `false`、总 `VERDICT` 恒 `ALARM` —— 这正是「总在报警的检验也是坏检验」在本例的具体形态。

---

## 3 第三步：三层的独立有效性

### 3(a) L1 单独能不能判「没放松」？——不能

- 它自己的 `detail.verdict_note` 已承认：`_fnr_check.py:156-157`「L1 alone can only ALARM on set changes; it can never validate semantic truth. L2+L3 are mandatory.」
- **P5 签名实跑**：`no_relaxation_check` 的 13 个参数里 `has_artifact_text_param=false`；`check_l1` 只有 7 个参数（items/flips/whitelist/registered_tokens/predicate_spec_keys/whitelist_sealed/whitelist_author），**没有证书、没有交付件原文、没有 ORACLE**。它只能看集合结构。
- **P10 实跑**：9 个已知-错注入中 L1 只抓 3/9（33.3%），L2 抓 6/9，L3 抓 1/9。
- **P11 实跑**：coverage 从 0.0331 降到 0.0 仍 PASS，说明连「覆盖分母」都不是它的判据。
- 它唯一稳定能做的事是「集合漂移 / 封印标志 / 作者字段」检查；这些是**完整性检查**，不是语义「没放松」的判定。而且 §2(d) 证明它的 SELF_CERTIFIED 分支会误报。

### 3(b) L2 依赖什么？独立封印 ORACLE 不存在时会不会退化成自证？——会，且本例已经退化

`certificate_ok()`（`_fnr_check.py:95-124`）只读调用方传入的字典字段：`anchor` 用正则 `^.+:\d+$`（`:99-101`）、`quote` 只查长度（`:102-104`）、`roles` 只查长度与 `NON_VALUE_RE`（`:105-114`）、`oracle_truth is True`（`:118`）、`oracle_author != predicate_author`（`:120`）、`oracle_sealed` 真值（`:122`）。**它不 `open()` 任何 `file:line`，不重算任何 SHA256 封印。**

- **本次 `find` 实跑**：在 `lead/gate_r9sem_20261109`、`lead/falsifiable_no_relax_20261109`、`lead/whitelist_audit_20261109` 三个目录下无 `*oracle*` / `*seal*` 文件（输出为空）。
- **作者自述**：`_fnr_check.py:309-313` 明写 CERTS 是「HYPOTHETICAL inputs … deliberately constructed here by THIS session」；`_fnr_REPORT.md:427` 明写「`repaired_predicate` 与 5 份 `CERTS` 是演示性假设输入…**不是第三方盲标注的真实 ORACLE**」。
- **P1 实跑（决定性）**：把 5 份证书的锚全改成 `nowhere/FAKE_i.md:999`、引文改成凭空编造的中文、独立性标志照旧自声明为真 ⇒ `VERDICT=PASS`、`L2_ok=true`、`L2_problems=[]`（`_cfa_stdout.txt` `P1 forged certs`）。上游 `_fnrd_verify_out.json:31-39` 同结论（`certificate_ok_resolves_file=false`、`impl_verifies_seal_hash=false`）。

⇒ L2 检验的是「输入字典里写了 True」，不是「第三方封印真值表说了 True」。独立 ORACLE 不存在时 L2 就是自证。

### 3(c) L3 的对抗样本谁出的？——与被测者同源，同样自证

- **出题人**：13 条 `ADVERSARIAL` 硬编码在 `_fnr_check.py:291-305`，与新检验同一文件、同一作者。
- **答案也同源**：known-good 世界的 `repaired_predicate`（`:471-483`）用 `AUTHOR_GUARD` 正则拒答；**P2 实跑 13/13 条语料都含 ≥1 个 guard 词**（`_cfa_stdout.txt` `P2 guard fit`），即词表与语料逐字拟合。这就是「13/13 全抓」的来源。
- **盲留出即退化（P2）**：用上游复核员 `_fnrd_verify.py:164-168` 的 3 条不含 guard 词的 novel empties，N-EMPTY-1 / N-EMPTY-2 被 `repaired_predicate` 判 PRESENT（漏），good world + 3 条 novel ⇒ `ALARM, caught=14/16`（`_cfa_stdout.txt` `P2 good+novel`；`_fnrd_verify_out.json:50-73` 上游已记同样结果）。
- L3(ii) 的 15/15 变异注入是唯一真正的机制自检，但它测的只是 `certificate_ok()` 对指针词的反应，仍不接触真实交付件原文。

⇒ L3 的「13/13」是「出题人用自己的词表出卷、再用自己的词表做答案」，同源自证；出题者换成未参与者即失效。

### 3(d) ★ 哪几层真正独立于被测对象？——本次实跑中，零层

| 层 | 独立性 | 理由（实跑/出处） |
|---|---|---|
| L1 | **不独立** | 标准集 = 白名单，与被测 `SPECS` 同一份数据；`check_l1` 只做集合比较（P5）；同源判据本身还是误报源（§2(d)）。 |
| L2 | **名义独立、实测不独立** | ORACLE 是作者自造的假设输入（`_fnr_check.py:309-313`、`_fnr_REPORT.md:427`），布尔自声明、无封印校验（P1）。**仅当**存在「第三方盲标注 + 预注册 SHA256 封印 + 检验端实际 open 并重算 hash」时才独立；本例不存在。 |
| L3 | **不独立** | 语料（`:291-305`）与 guard 词表（`:478-480`）同作者，P2 拟合 13/13、novel 漏 2/3。 |
| 三层合成 | **不独立** | `:238` 的 `and` 把 3 个相关失效叠加，容易被误读成「三层独立互证」。`_fnr_REPORT.md:427` 已自评「设计与可行性验证，不构成对现盘 R9 升级的重新认证」，本次审计确认该限定必要。 |

补充：`WHITELIST_AUDIT.md:467` 记 5/5 语义在场来自「人工独立读原文」，那是**项目里唯一真正异源的真值**；但它没有进入 `_fnr_check.py` 的 ORACLE 输入槽（进槽的是 CERTS），因此没有被三层检验机制化。

---

## 4 第四步：元检验本身的局限

### 4(a) 9 wrong / 2 good 规模够吗？——不够

- **统计功效（P7 实跑）**：9/9 全抓只能支持单侧 95% 敏感度下界 `0.05^(1/9) = 0.716871`（即「≥71.7%」）；0/2 误报的单侧 95% 上界 `1−0.05^(1/2) = 0.776393`，**完全不能排除 77.6% 的假阳性率**。
- **覆盖面**：9 个注入全是作者自己写的 mutate 函数（`_fnr_check.py:385-500`），且都作用在检验**已有的输入槽位**（证书字段、seal 布尔、flips 列表、predicate wrapper）。`_fnrd_verify.py:69-81` 与本次 P5 证明「真实交付件原文」这个槽根本不存在 ⇒ 「把 5 份主件全换成语义空」这类错误**无法被注入**，元检验自然不会因为漏掉它而失败（`_fnrd_verify_out.json:22-30`：B 场景 `VERDICT=PASS`）。
- **直接反证**：本次 §2 的 10 个良性世界实跑出 4 个误报，说明 0/2 的「无假阳性」结论不能外推。⇒ 9 个注入只能证明「对作者列出的 9 种错误敏感」，不能证明「对任何错误敏感」，更不能证明「在良性输入上不误报」。

### 4(b) 基线敏感：风险怎么控

- **上游登记**：`_fnr_REPORT.md:239`「第一次实跑时把现盘当基线，2 个『良性变化』被误记为 `false_alarm`、`CHECKER_VALID=false`」。
- **P4 本会话独立复现**：以真实在盘为 baseline → `baseline_VERDICT=ALARM`、两个良性变化 `false_alarm=true`、`n_false_alarms=2`、`CHECKER_VALID=false`。
- **★ P3 发现更严重的漏洞（本会话新发现）**：`meta_test()` 的判定式在 `_fnr_check.py:280` 是
  `CHECKER_VALID = (n_caught == len(wrong_rows) and n_false == 0)`，
  **完全不含 `baseline_VERDICT`**。本会话以真实现盘为基线、传 `wrong_variants=[]`、`good_variants=[]` 实跑 ⇒ `baseline_VERDICT="ALARM"`、`n_wrong=0`、`n_good=0`、`CHECKER_VALID=true`（空清单 vacuous truth，`_cfa_stdout.txt` `P3 meta baseline`）。而这恰恰与 `_fnr_REPORT.md:338` 模板第 0 步 `assert checker(good_world) == PASS` 矛盾 —— 规格写了，代码没实现。
- **控制方案**：① 把 `and baseline["VERDICT"] == "PASS"` 写进 `CHECKER_VALID`；② 前置 `len(wrong)>=5类` 且 `len(good)>=8`，空/退化清单直接 `INVALID`；③ 基线世界、注入清单、checker 源码三者各算 `hashlib.sha256` 写进输出（`_fnr_REPORT.md:356` 有规格，`_fnr_check.py` 未实装）；④ 基线「已知-好」由第三方盲标注并预注册，不许检验作者自声明；⑤ 逐层单独输出 recall / FP，别只给一个总布尔。

### 4(c) 合成世界 `repaired_predicate` 当基线 = 用理想情况证明检验有效？——是，且更弱

- 是「存在一个参数组合使检验 PASS 且 9 个注入能被抓」的**可行性与设计验证**，不是真实数据上的有效性证明。
- 更弱的三点实跑证据：**P9** —— PASS 靠在 `spec_keys` 塞一个无关的 `"额外预留要素"` 才得到；**P2** —— 13/13 全抓靠 `AUTHOR_GUARD` 词表与语料 13/13 逐字拟合；**P1** —— 好世界里连伪造锚点/编造引文都照收。⇒ 这是「把检验调到恰好通过自己出的卷子」，循环拟合。
- `_fnr_REPORT.md:427` 已自标「设计与可行性验证，不构成对现盘 R9 升级的重新认证」；本次审计确认这个限定是准确的，且 §2 的 50% 假阳性率给出了它的量化代价。

### 4(d) 桥接「元检验通过」与「真实数据有效」的方案

1. **真 ORACLE**：由未参与谓词/白名单/对抗语料编写的一方，对 302 项（至少 5 个 flip + 20 条留出负样本）逐项盲标 `truth∈{0,1}`，先 `hashlib.sha256` 封印预注册；检验端必须 `open()` 该封印文件、重算 hash、比对作者字段 —— 不接受调用方传入的 `oracle_sealed: True` 布尔（对应修 `_fnr_check.py:116-123`）。
2. **盲留出对抗语料**：第三方另造 ≥30 条 form-like-but-empty 且明确**不含作者 guard 词表**的样本，一次性封 SHA 后交付；阈值「全抓」在跑之前注册。P2 已证 3 条 novel 里 2 条即漏。
3. **真实件入参**：给 `no_relaxation_check` 增加 `artifact_text` 槽（当前 13 参数里没有，P5），把 5 份主件原文传入并逐行比对 `anchor`/`quote`；P1 的伪造锚点必须被 L2 拒绝。零真机纪律下只做静态文本比对即可。
4. **双基线元检验**：一组已知-好**真实**世界 + 一组已知-错**真实**世界，分别报告 `(n_caught, n_false_alarms, per-layer recall/FP)` 与 Wilson 区间；`n_good≥8`、`n_wrong` 覆盖 5 类；`CHECKER_VALID` 纳入 `baseline=="PASS"`。
5. **显式边界**：按 `_fnr_REPORT.md:420` 第 10 条强制写「本检验在以下情形下不报警：______」，把不可证伪边界公开。

---

## 5 第五步：结论与建议

### 5(a) 现状确有问题，还是检验过严？——**必须分层判：L3 分支是真缺陷，L1 分支是过严；总 ALARM 偶然正确但不可采信**

| 分支 | 判定 | 依据 |
|---|---|---|
| L3 的 6 条泄漏 | **现状确有问题，ALARM 正确** | P6 独立复跑 7/13、`leaked=['CF3','CF5','WCF5','V2','V3','V6']`；`_fnr_check_out.json:422-426`；`WHITELIST_AUDIT.md:517/:522` 已判机制 invalid。 |
| L1 的 SELF_CERTIFIED | **检验过严，误报** | P8 修完全部真实缺陷（coverage=1.0、13/13 全抓、第三方封印）仍 ALARM，唯一问题就是它；P9 加无关键即翻转；S05/S06/S07 三个合规良性世界全被误报。 |

综合：由于 `:238` 是 `l1 and l2 and l3` 的 ANY-false 合成，**总 VERDICT=ALARM 恰好被 L3 的真缺陷「救对」了**，但这不能证明检验有效 —— 同一个检验在 4/8 个本该 PASS 的良性世界上也报 ALARM。⇒ 结论：**新检验同时存在「过严（L1 恒报警于合规同源）」与「有效检出（L3 抓到真泄漏）」两面；作为「没放松」的判定工具，它目前不可信，需改后再用。**

### 5(b) 能否直接用于生产？——**不能直接插；判「需改后再插」**

理由：50% 的良性误报率（§2(c)）、三层零独立（§3(d)）、L2 接受伪造证据（P1）、L3 换盲留出即漏（P2）、元检验 `CHECKER_VALID` 可被空清单骗成 true（P3）、基线选错即反转结论（P4）。任何一条单独都足以拦下生产插入。

### 5(c) 最小改法（**只给方案，本任务不动手改任何件**）

1. `_fnr_check.py:148-150`：把 `if self_certified: problems.append(...)` 从硬 FAIL **降级**为 `detail` 里的 witness 声明（保留 `self_certified` 布尔与 `coverage_ratio` 报告，但不进 `problems`）。这一条直接消掉 S05/S06/S07 三个误报与 P8 的恒报警。
2. `_fnr_check.py:116-123`：独立性改为 L2 对**真实 `hashlib.sha256` 封印文件**的 `open` + 重算 + 作者字段校验，不再接受调用方自声明的 `oracle_sealed=True` / `oracle_author` 布尔。
3. `_fnr_check.py:280`：`CHECKER_VALID` 加入 `and baseline["VERDICT"] == "PASS"`，并前置 `len(wrong_rows) >= 5` 且 `len(good_rows) >= 8`，空清单直接 INVALID；良性清单须含「合规同源 / 全覆盖 / 第三方封印 / 对抗全抓 / 加真翻案 / 删一对」类别。
4. 附（准确性）：把 `:149` 错误消息里的 "multiset" 改成 "set"，与 `:137-138` 的实现一致。
5. 附（覆盖）：让 `coverage_ratio` 低于预注册阈值时成为 FAIL 条件（P11 证明现在是装饰）；并把对抗语料换成第三方盲留出并先封 SHA。

最小闭环 = 前 3 条；第 4/5 条是同批校正。

### 5(d) 本条工作判不了什么（如实列）

1. **未跑 `_fnr_check.py` 本体**（`:548-549` 会写回只读域），也未跑 `_r9s_regress.py` 本体。本会话是把 `_fnr_check.py` 作为模块 import 后调用其函数（替代执行），所有世界在内存字典中构造 —— 不是跑检验本体，如实登记。
2. **未独立重判 5 份主件的人工语义裁决**：S01 的「本该 PASS」前提沿用 `WHITELIST_AUDIT.md:498/:516` 的 5/5 独立裁决，本会话未重读 4 主件全文逐项重判。
3. **未穷举证明「不存在真实第三方 ORACLE」**：只在 3 个相关目录 `find -iname "*oracle*" -o -iname "*seal*"`（输出为空），且作者自己在 `_fnr_REPORT.md:427` 声明 CERTS 是自造假设输入；全库穷举未做。
4. **未验证 novel empties 的语义标注**：沿用上游复核员 `_fnrd_verify.py:164-168` 的 3 条，只测谓词反应，未独立裁其是否真「实质空」。
5. **未做统计显著性 / 泛化点估计**：Wilson 区间是描述性的；10 个场景非随机抽样，50% 不能当作总体 FP 率的无偏估计；未做 bootstrap / 功效曲线。
6. **未验证「合规同源」在其它项目是否真的合规**：结论基于本项目 `_r9s_regress.py:112-119`、`_r9s_predicates.py:368-402` 的设计陈述及任务书明确列出的场景；跨项目推广未验。
7. **未验证真机 / 运行时行为**：零真机纪律；所有结论限于静态文本与内存复算。
8. **未验证改法本身有效**：§5(c) 是纸面最小改法，本任务「只做审计」，未实现、未实跑改动后的版本。
9. **未改任何既有件、未 commit、未 push**；收尾复查 11 个只读件指纹 `ALL_UNCHANGED = True`。

### 5(e) ★ 「检验的检验」清单：避免「总报警」与「总不报警」

1. **双向门禁**：`n_wrong_caught == n_wrong`（防总不报警）**AND** `n_false_alarms == 0` on **≥8 个预先封印的良性世界**（防总报警）。两个数字随结果一起输出，缺一即 `INVALID`。
2. **把基线纳入公式**：`CHECKER_VALID` 必须含 `checker(good_world) == PASS`（P3 证明缺它会 vacuous true）；空注入 / 空良性清单直接 `INVALID`。
3. **良性世界分类覆盖**：合规同源 / 全覆盖 / 第三方封印 / 对抗全抓 / 加真翻案 / 删一对 / 良性改写 / 现状假设成立；且由检验作者**以外**的人构造并封 SHA。
4. **恒真恒假扫描**：对每个判据各构造一个使其恒 true 与恒 false 的输入，确认两个方向都有可达输入；任一方向不可达即装饰。
5. **统计功效下限**：报告 Wilson / Clopper-Pearson 区间；明确 9/9 与 0/2 不足以宣称有效（P7：敏感度下界 71.7%、FP 上界 77.6%）。
6. **四源独立性审计**：标准集、ORACLE、对抗语料、guard 词表分别列作者 / SHA256 封印 / 是否预注册；任一与被测对象同源即标「不独立」，**不得计入互证层数**（本例计入了 3 层，实际 0 层）。
7. **一次性盲留出**：封 SHA 的 holdout（含不含已知 guard 词的 novel 形态），阈值跑前注册；P2 演示拟合会在留出上漏。
8. **覆盖分母双验**：UNTESTED 单列且不计入通过；同时验证 coverage 本身**是否真会触发 FAIL**（P11：本例 0.0 仍 PASS，是装饰）。
9. **反向误报回归**：把旧检验踩过的坑（`fp_extra_true_flip` / `fp_literal_insert` / `fp_drop_one_whitelist_pair`）列为必跑良性回归，逐版本重跑。
10. **显式边界**：强制写「本检验在以下情形不报警：______」与「本检验在以下情形一定报警：______」（`_fnr_REPORT.md:420` 第 10 条）。
11. **逐层单独报告 recall / FP**：禁止只用一个 `AND` 总布尔掩盖相关失效；本例 P10 给出 L1 3/9、L2 6/9、L3 1/9。
12. **改动后重跑同一批封印良/错世界并比对源码指纹**：防「改完检验就绕过测试」。

---

## 6 产物清单（全部在唯一写域）

| 文件 | SHA256 | 字节数 |
|---|---|---|
| `lead/check_fp_audit_20261109/_cfa_probe.py` | `d6dcedfbb6b5ac2b1c3d6aadf94b3e323d044866753cf73cf40a192b9e57b0c0` | 28762 |
| `lead/check_fp_audit_20261109/_cfa_out.json` | `a47ec95a2d3baed54cc903a765eadf31ee65f9e4a9e87c5f780148c0963dc64a` | 17830 |
| `lead/check_fp_audit_20261109/_cfa_stdout.txt` | `250d82154011a351c8f48cf1869da34e5887280872ebc08c3939cac87b75a2a2` | 7443 |
| `lead/check_fp_audit_20261109/_CFA_REPORT.md` | 本件（自查见提交回件） | — |

**严重性：high** —— 该检验若直接插生产，L1 会在任何合规同源实现上恒报警（总报警的坏检验），且 L2 接受伪造证据、L3 换盲留出即漏、元检验可被空清单骗成 `CHECKER_VALID=true`。
