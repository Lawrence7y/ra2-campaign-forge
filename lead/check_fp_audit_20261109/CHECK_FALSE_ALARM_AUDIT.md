# CHECK_FALSE_ALARM_AUDIT.md — 新检验假阳性审计件（复核后定稿）

被核对象：`lead/falsifiable_no_relax_20261109/_fnr_check.py` 的 L1/L2/L3 + `meta_test()`
唯一写域：`lead/check_fp_audit_20261109/`
本会话日期：2026-11-09
复核 verdict = **partial**（【复核】字段原值）→ 按任务铁律「refuted 或 partial 标 unconfirmed」，凡复核未确认的上游结论一律登记为 **unconfirmed**。

---

## 1 目的与边界

**目的**：独立复核【三层结果】、量化新检验在良性场景上的假阳性、判定 L1/L2/L3 的独立性、审查元检验局限，并给出「现状有问题 vs 检验过严」「能否用于生产」「最小改法」「判不了什么」「检验的检验清单」。**只做审计**：不改新检验（`_fnr_check.py`）、不改任何既有件、不实装任何修复方案，所有实验只在本任务写域内新脚本中做。

**边界（铁律，逐条遵守）**：

- 零真机：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存。
- 零采样代码：未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入，未写动态内存解析。
- 绝对只读：`lead/falsifiable_no_relax_20261109/` 全部件、`lead/whitelist_audit_20261109/`、`lead/gate_r9sem_20261109/`、`lead/gate_pipeline_20261109/`、`lead/gate_n13_20261109/`，以及两件台账 `lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`，一律未修改、未追加、未覆盖。
- 唯一写域 = `lead/check_fp_audit_20261109/`。本会话新建 5 件（`_cfaa_verify.py` / `_cfaa_out.json` / `_cfaa_stdout.txt` / `_cfaa_probe2_rerun.txt` / 本件 `CHECK_FALSE_ALARM_AUDIT.md`）。C4 重跑既有写域脚本 `_cfav_probe2.py` 时会按 `:322-323` 回写同域 `_cfav_out2.json`，本会话如实登记：该文件被重写但内容字节不变（复现 stdout `_cfaa_probe2_rerun.txt` 与原 `_cfav_stdout2.txt` 的 SHA256 前缀同为 `966ba21e57e71389`，脚本确定性）；**只读域内 0 件被改写**，既有 `_cfa_*` 件未覆盖。
- 不 commit、不 push。Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib.sha256`。
- 引用追到「实跑命令+输出」或「文件:行」；拿不到写「未验」，不补造。

**未跑本体，如实登记**：`_fnr_check.py:548-549` 的 `main()` 会 `(WDIR / "_fnr_check_out.json").write_text(...)` 回写绝对只读域（本会话读 `lead/falsifiable_no_relax_20261109/_fnr_check.py:41` = `(WDIR / "_fnr_check_out.json").write_text(` 已确认），跑它会违反「绝对只读」；`_r9s_regress.py` 本体亦未跑（`lead/falsifiable_no_relax_20261109/_fnr_REPORT.md:22` 自记同因）。本会话改用 `importlib.util.spec_from_file_location` 把 `_fnr_check.py` 当**模块**加载（`sys.dont_write_bytecode = True`），直接调 `no_relaxation_check()` / `check_l1()` / `meta_test()`；这是**替代执行**，不是跑本体，不计为「跑了 `_fnr_check.py`」。

**本会话实跑命令与输出**（全部在唯一写域内）：

| # | 命令 | 输出 / 落盘 |
|---|---|---|
| C1 | `python -I -X utf8 -c "<8 件 hashlib 独立重算>"` | 8 行 `OK ... sha256=... bytes=...`，`ALL_EIGHT_MATCH = True` |
| C2 | `python -I -X utf8 -c "<读 21 条争议行>"` | 输出 `WHITELIST_AUDIT.md:506` 等逐行原文，见 §2 / §3 |
| C3 | `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_fp_audit_20261109/_cfaa_verify.py > D:/Project/ra2-campaign-forge/lead/check_fp_audit_20261109/_cfaa_stdout.txt 2>&1` | `EXIT=0`；`_cfaa_stdout.txt`（13469 字节）/ `_cfaa_out.json`；§2–§6 全部数值来源 |
| C4 | `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_fp_audit_20261109/_cfav_probe2.py > D:/Project/ra2-campaign-forge/lead/check_fp_audit_20261109/_cfaa_probe2_rerun.txt 2>&1` | `EXIT=0`；复核用 64 世界全因子在本会话复现：`same_source_5 = 32/32 ALARM`、`plus_dummy_6 = 0/32 ALARM` |
| C5 | `python -I -X utf8 -c "<诊断 _cfaa_ 首版 64 世界差异>"` | `N_FAIL= 40`，其中 `adversarial_16` 分支 `caught=14/16`、`L3p=["...N-EMPTY-1...judged PRESENT"]`；据此把 §3 的 64 世界语料对齐为复核的 `EXTRA3`（见 §3 脚注）后重跑 C3 |
| C6 | `git log -1 --oneline` | `2657458 GOAL-3T: 台账 §400→§508 与 D-07..D-11 裁决登记入账`（未 commit/未 push） |
| C7 | `git status --short -- <8 条+3 只读目录>` | `MM lead/GOAL_THREE_TARGETS_20261018.md`、`MM lead/PENDING_DECISIONS.md`（会话开始快照即如此）、5 个 `??` 只读目录、`?? lead/check_fp_audit_20261109/`；只读域内无新增改动件 |
| C8 | `find <5 个只读目录> -type f -newermt "2026-11-09 17:50"` | 空输出 = 会话期间只读域无新文件；`__pycache__` 内 4 件 `.pyc` 时间早于 17:50 |
| C9 | `grep -rl -E "8 个良性\|8个良性\|8 场景\|八个良性\|点名的 8" lead/` | 仅 1 命中：`lead/check_fp_audit_20261109/_CFA_REPORT.md` ⇒ 全库找不到「任务点名的 8 个场景」原始任务书，来源不可核（复核 §【复核】⑥ 同结论，本会话确认） |

---

## 2 上游指纹（八件）+ 三层结果复核

### 2(a) 八件指纹（编排方指纹字段，本会话独立重算）

命令 C1 输出逐行为 `OK <path> sha256=<64hex> bytes=<n> expect_bytes=<n>`，末行 `ALL_EIGHT_MATCH = True`；命令 C3 的 `_cfaa_stdout.txt:2-10` 与 `_cfaa_out.json:A_fingerprints` 再记一遍，收尾 `_cfaa_stdout.txt:111-143`（`G. READ-ONLY 8 RECHECK (post-run)`）八件哈希与字节数**全部不变**。

| 文件 | SHA256 | 字节数 | 本会话 |
|---|---|---|---|
| `lead/falsifiable_no_relax_20261109/_fnr_check.py` | `94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2` | 28811 | OK |
| `lead/falsifiable_no_relax_20261109/_fnr_check_out.json` | `f3112b225b1de35183ad4604554cb25689ed252b6a5a95d96d17fce53c8c140e` | 8733 | OK |
| `lead/falsifiable_no_relax_20261109/_fnr_REPORT.md` | `80641e7dcc0cc3ebc61c2c39afe6757814fc6eb694a9559c4903ab9241ee6f06` | 43390 | OK |
| `lead/falsifiable_no_relax_20261109/_fnr_replay_out.json` | `877f4ced0ab99562f776faa82015f742588c76fa9a63ee23b735f2fed61bd9fd` | 27535 | OK |
| `lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md` | `f9d00b7c9a12a996bac9d89b0bf5a948dfe026e21f472bd825d7924d35a47adc` | 52705 | OK |
| `lead/gate_r9sem_20261109/_r9s_regress_out.json` | `5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25` | 75673 | OK |
| `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 | OK |
| `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 | OK |

### 2(b) 三层逐层 ok 与 problems

命令 C3 → `_cfaa_stdout.txt:13-18`：`VERDICT=ALARM L1_ok=False L2_ok=True L3_ok=False`，与【三层结果】及 `lead/falsifiable_no_relax_20261109/_fnr_check_out.json:8-9` 一致。

- **L1 ok=false**，problems 唯一 1 条（`_fnr_check_out.json:12-14` 与 `_cfaa_stdout.txt:14` 逐字相同）：
  `L1: SELF_CERTIFIED -- whitelist token multiset == predicate spec keys; 'outside=0' is a design consequence, not evidence`。
  detail（`_fnr_check_out.json:15-23`）：`n_items=302, n_flips=5, outside_whitelist=0, n_structurally_untested=292, coverage_ratio=0.0331, self_certified=true`，`verdict_note` 为 `L1 alone can only ALARM on set changes; it can never validate semantic truth. L2+L3 are mandatory.`（代码 `lead/falsifiable_no_relax_20261109/_fnr_check.py:156-157`）。
- **L2 ok=true**：`_fnr_check_out.json:25-69` 共 5 行 `rows`，`_cfaa_stdout.txt:16` 实跑 `L2 n_rows=5 all_ok=True`，`problems=[]`（`:26`）。
- **L3 ok=false**：6 条 problems（`_fnr_check_out.json:73-80`）：`CF3(改前改后) / CF5(可重建) / WCF5(可重建) / V2(需谁批准) / V3(改前改后) / V6(可重建)` 全部 `judged PRESENT -- semantic leak`。`n_adversarial_caught=7`（`:163`）、`n_adversarial=13`（`:162`）、`n_mutations=15 / n_mutation_alarms=15 / sensitivity_proved=true`（`:286-288`）。`_cfaa_stdout.txt:17` 实跑 `L3 caught=7/13 leaked=['CF3','CF5','WCF5','V2','V3','V6'] mutations=15/15`。

### 2(c) SELF_CERTIFIED 判定怎么算

代码 `lead/falsifiable_no_relax_20261109/_fnr_check.py:130-138`：

```
wl = {tuple(x) for x in whitelist}
wl_tokens = {k for _, k in wl}                       # :137  ← 集合推导，去重
self_certified = (wl_tokens == set(predicate_spec_keys))   # :138
```

→ 判据是 **set 相等**（不是 multiset；`:149-150` 的报错文案写「token multiset」属措辞瑕疵，本会话 `_cfaa_stdout.txt:37` 与 `_cfaa_out.json:C_prohibition_lines` 已核对 `:137` / `:149` 原文）。触发后 `:148-150` 无条件 `problems.append(...)`，`:158` 由 `len(problems)==0` 得 `ok=false`。本会话 `_cfaa_stdout.txt:18` 实跑 `wl_tokens_eq_spec_keys: true`（两侧同为 `可重建/实跑输出/改前改后/脚本存在性/需谁批准` 5 键，`_cfa_stdout.txt:30-43` 亦同）。

**这是规格指定的判据，不是临时加的过严条件**：`_fnr_check.py:85-86` 的 (E) 条把「WHITELIST PROVENANCE」操作化为 `token multiset is NOT identical to the new predicate's spec keys`；`lead/whitelist_audit_20261109/WHITELIST_AUDIT.md:506` 明写 ``WHITELIST 不得与 SPECS 同源``；`lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md:476` 同句；`lead/falsifiable_no_relax_20261109/FALSIFIABLE_NO_RELAX.md:458` 明写「**解同源**：白名单 token 集合 ≠ `V1.spec_keys`」；`lead/falsifiable_no_relax_20261109/_fnr_REPORT.md:256` 把「②白名单与 `SPECS` 解同源」列为修复需要。以上 5 行由命令 C2 与 `_cfaa_stdout.txt:21-26` 逐字读出。**⇒【审计】里「合规同源」是自造范畴，被【复核】① 推翻；此项标 unconfirmed。**

### 2(d) 292 与 0.0331 怎么算

代码 `_fnr_check.py:133-135`：`untested = [i for i in items if i["token"] not in registered_tokens]`；`:154`：`coverage_ratio = round((len(items) - len(untested)) / max(len(items), 1), 4)`。命令 C3 → `_cfaa_stdout.txt:18` 实跑：

```
rows=32, n_items=302, n_flips=5, n_whitelist=5, n_spec_keys=5,
tested_token_counts={"需谁批准":6,"实跑输出":1,"改前改后":1,"脚本存在性":1,"可重建":1},
n_tested=10, n_structurally_untested=292, coverage_ratio=0.0331
```

即 `302 - 10 = 292`，`10/302 = 0.033112… → 0.0331`。`_cfav_stdout.txt:42` / `_cfa_stdout.txt:15-46` 同值。复核【复核】⑦ 确认 292 / 0.0331 成立。

### 2(e) L3 的 7-13（7/13）与 6 条未抓

`_fnr_check_out.json:422-426` 自记 `{"n":13,"caught_by_CURRENT_R9S":7,"note":"R9S itself FAILS this adversarial corpus; the checker reports the leak instead of hiding it."}`；`:163` `n_adversarial_caught=7`。6 条未抓 id = `CF3, CF5, WCF5, V2, V3, V6`（`:98-99, :110-111, :140-141, :146-147, :152-153, :158-159` 各 `caught:false`）。本会话命令 C3 独立调 `R9S.r9s_element_present` 得同 7/13（`_cfaa_stdout.txt:17`）；`_cfa_stdout.txt:72` 的 P6 与 `_cfav_stdout.txt:70` 的 P6 亦同。**13 条语料定义见 `_fnr_check.py:291-305`**（`ADVERSARIAL` 常量）。

---

## 3 假阳性量化（≥8 个良性场景 + 逐场景 VERDICT + 触发层 + ★ L1 合规设计上是否永远 ALARM）

铁律：「总在报警的检验与总不报警的检验同样是坏检验」。本节给三套**逐场景**实测，不用「假阳性低」概括。

### 3(a) 本会话 11 个良性场景（命令 C3 → `_cfaa_stdout.txt:44-57`）

「良性」定义：5 份证书齐备、`oracle_truth=True` / `oracle_author` 独立 / `oracle_sealed=True`、白名单独立且封印、谓词拒掉全部对抗载荷；`B*` 为**满足项目规格 (E) 的合规世界**，`S05/S06/S07` 为上游自造的「合规同源」变体（规格上不合规，单列以对照）。

| id | 良性场景 | VERDICT | 触发层 | L1 | L2 | L3 | coverage |
|---|---|---|---|---|---|---|---|
| B1 | 理想世界：满足 (E) 且有第 6 个**真实**注册要素「交付清单」 | **PASS** | — | true | true | true | 0.0331 |
| B3 | 全覆盖：`registered_tokens` = 全部 item token | **PASS** | — | true | true | true | 1.0 |
| B4 | 第三方 ORACLE 真值表（旁路真 sha256 封印） | **PASS** | — | true | true | true | 0.0331 |
| B5 | 对抗样本含 3 条 novel 全抓（16/16） | **PASS** | — | true | true | true | 0.0331 |
| B6 | 追加 1 条真语义等价翻案 | **PASS** | — | true | true | true | 0.0331 |
| B7 | 良性引文改写 | **PASS** | — | true | true | true | 0.0331 |
| B8 | 删 1 对白名单并同步删 flip/证书 | **PASS** | — | true | true | true | 0.0331 |
| B9 | 真第 6 要素 + 全覆盖 + 16 条对抗 + 全独立标志 | **PASS** | — | true | true | true | 1.0 |
| S05 | 「合规同源」：SPECS 是白名单展开 | **ALARM** | **L1** | false | true | true | 0.0331 |
| S06 | 同源 + 全覆盖 + 自声明第三方封印 | **ALARM** | **L1** | false | true | true | 1.0 |
| S07 | 同源 + 白名单第三方封印且作者独立 | **ALARM** | **L1** | false | true | true | 1.0 |

11 个中 3 个 ALARM，`L1_problems` 逐字同为 §2(c) 那条 SELF_CERTIFIED，`L2/L3` 全 true。

### 3(b) 上游【审计】10 个良性场景（`lead/check_fp_audit_20261109/_cfa_stdout.txt:49-62`，本会话读取；未重跑其 `_cfa_probe.py` 本体，标为「读到的既有实跑输出」）

| id | 良性场景 | VERDICT | 触发层 | 上游记 FP |
|---|---|---|---|---|
| S01 | 现状假设成立（白名单 5 项内容正确且语义在场） | **ALARM** | **L1, L3** | True |
| S02 | 谓词覆盖全部 token（无结构性未测） | **PASS** | — | False |
| S03 | 有第三方盲标注真值表（真 sha256 封印） | **PASS** | — | False |
| S04 | 对抗样本全被抓（16/16） | **PASS** | — | False |
| S05 | 「合规同源」：SPECS 是白名单展开 | **ALARM** | **L1** | True |
| S06 | 同源 + 全覆盖 + 真第三方封印 | **ALARM** | **L1** | True |
| S07 | 同源 + 白名单第三方封印且作者独立 | **ALARM** | **L1** | True |
| S08 | 追加 1 条真语义等价翻案 | **PASS** | — | False |
| S09 | 良性引文改写 | **PASS** | — | False |
| S10 | 删 1 对白名单并同步删 flip | **PASS** | — | False |

### 3(c) 【复核】自造 11 个良性/ harder 世界（`lead/check_fp_audit_20261109/_cfav_stdout.txt:45-55`，本会话读取；并见 `_cfaa_probe2_rerun.txt` 的 64 世界复现）

| id | 场景 | VERDICT | 触发层 |
|---|---|---|---|
| B1 | 理想世界：满足检验自身 (E) 条件（第 6 个真实注册要素） | **PASS** | — |
| B2 | 「合规同源」：第三方封印独立白名单，token 集 = SPECS 键 | **ALARM** | **L1** |
| B3 | 全覆盖 | **PASS** | — |
| B4 | 第三方 ORACLE 真值表（真 sha256 封印） | **PASS** | — |
| B5 | 对抗样本全抓（13+3=16） | **PASS** | — |
| B6 | 追加 1 条真语义等价翻案 | **PASS** | — |
| B7 | 良性引文改写 | **PASS** | — |
| B8 | 删 1 对白名单并同步删 flip/证书 | **PASS** | — |
| H1 | 现盘真缺陷全修好且不加 padding | **ALARM** | **L1** |
| H2 | 最大合规（真封印 + 全覆盖 + 独立 ORACLE）仅余同源 | **ALARM** | **L1** |
| H3 | 已知错：5 份证书全伪造锚点/引文（检验端不可见） | **PASS** | — |

### 3(d) 假阳性率（多口径，全部列出，不挑好看的）

| 口径 | FP | Wilson95 | 来源 |
|---|---|---|---|
| 上游「任务点名的 8 个」 | 4/8 = **50.00%** | [0.215216, 0.784784] | `_cfa_stdout.txt:60` / 【审计】falseAlarms |
| 上游全部 10 个 | 4/10 = **40.00%** | [0.16818, 0.687326] | `_cfa_stdout.txt:60` |
| 上游剔除混杂 S01 的 9 个 | 3/9 = **33.33%** | [0.120584, 0.645798] | `_cfa_stdout.txt:61` |
| 上游纯良性 6 个 | 0/6 | — | 【审计】falseAlarms |
| 复核自造 8 个 | 1/8 = **12.50%** | [0.022417, 0.470888] | `_cfav_stdout.txt:56` |
| 复核规格一致 7 个 | 0/7 | [0.0, 0.35433] | `_cfav_stdout.txt:57` |
| **本会话规格一致 8 个** | **0/8 = 0.00%** | [0.0, 0.324408] | `_cfaa_stdout.txt:56` |
| 本会话若把 3 个同源变体计入 11 个 | 3/11 = **27.27%** | [0.097461, 0.565645] | `_cfaa_stdout.txt:57` |

**为什么 50% 与 0% 不矛盾（复核②，本会话确认）**：命令 C4 复现的 64 世界 7 轴全因子（`_cfaa_stdout.txt:55` / `_cfaa_probe2_rerun.txt`）：

```
n_axes=7, n_worlds=64
same_source_5 : n=32, n_ALARM=32, ALARM_rate=1.0, n_L1_false=32, n_non_L1_false=0
plus_dummy_6  : n=32, n_ALARM= 0, ALARM_rate=0.0, n_L1_false= 0, n_non_L1_false=0
```

其余 6 轴（registered_tokens / predicate / corpus / certs / whitelist_author / whitelist_sealed）零影响，`n_non_L1_false=0`。⇒ 假阳性由**一个二元开关确定性决定**（同源 100% / 不同源 0%），不是可套 Wilson 的随机率；50% 是「3 个相关同源变体 + 1 个含 6 条真泄漏的 S01」被塞进 8 个样位产生的**选择效应**。〔脚注：本会话 `_cfaa_verify.py` 首版在 `adversarial_16` 轴误用了 3 条**不含 guard 词的** novel empties，命令 C5 诊断出 `caught=14/16` 且 `N-EMPTY-1` 泄漏，导致 `plus_dummy_6` 有 8 个世界因 L3 真缺陷而 ALARM；这些世界**不是良性世界**，已对齐为复核 `_cfav_probe2.py:88-92` 的 `EXTRA3`（含 guard 词）后重跑 C3，得 0/32。此差异如实登记，不隐藏。〕

**双向检验（避免「总在报警」误判）**：`B1` 及全部 8 个规格一致世界 `PASS`（`_cfaa_stdout.txt:44-51`）；`_cfav_stdout2.txt:97` 的 F 段 `wrong1_all_certs_emptied=ALARM`、`wrong2_all_anchors_forged=PASS`、`wrong3_predicate_leaks=ALARM`。⇒ 新检验**不是**总在报警，也**不是**总不报警；真正的结构病是**交付件级错误恒不报警**（§4 P5/H3）。上游「总 ALARM 被 L3 偶然救对」与自身 P8 冲突：`_cfa_stdout.txt:74` 的 P8 与 `_cfav_stdout.txt:53-54` 的 H1/H2 都证明修好 L3 全部真缺陷后 L1 仍 ALARM ⇒ 真实状态是 **L1 + L3 双重决定**，非偶然救对（复核③，标 unconfirmed 的上游原结论）。

### 3(e) ★ L1 在合规设计上是否永远 ALARM

**答：不会；「合规同源」不是合规设计。**

- 项目明文禁止同源：`WHITELIST_AUDIT.md:506`、`_WL_WHITELIST_AUDIT.md:476`、`FALSIFIABLE_NO_RELAX.md:458`、`_fnr_REPORT.md:256`、`_fnr_check.py:85-86`（命令 C2 输出，`_cfaa_stdout.txt:21-26`）。所以「合规设计」的定义是 **白名单 token 集 ≠ SPECS keys**（外加第三方盲标注 + SHA256 预注册封印 + 回归端先验封印再读）。
- 在合规设计上 L1 的 SELF_CERTIFIED **不触发**：本会话 8/8 规格一致良性世界全部 `PASS`（`_cfaa_stdout.txt:44-51`），64 世界 `plus_dummy_6` 为 `0/32 ALARM`（`:55`）。
- 只有**违反项目规格的同源世界**才 L1 恒 false 且 `:238` 的 `and` 使总 `VERDICT` 恒 ALARM：`same_source_5` = `32/32 ALARM`（`:55`）。这一报警是 (E) 条规格指定判据的**正确报警**，不是假阳性。⇒【审计】「L1 分支过严误报 / 合规同源项目 L1 会永远 ALARM」被【复核】① 推翻，标 **unconfirmed**。
- **但判据强度确有真实缺陷（未被复核推翻、本会话确认）**：`_fnr_check.py:137-138` 只算 `set(wl tokens) == set(spec_keys)`，不读 `whitelist_author` / `whitelist_sealed` / 任何封印；P9（`_cfaa_stdout.txt:98-100`）实跑 `with_dummy_key=PASS` / `without_dummy_key=ALARM`，dummy 为 `:486` 的「额外预留要素」。⇒ 判据量的是**集合不相等**，不是**来源独立**，可被一个无关预留键 padding 绕过（`_cfav_stdout.txt:61` 的 P9 同值，`_cfa_stdout.txt:75` 的 P9 同值）。把 `outside=0 是设计后果` 写进 `detail` 作 witness 是对的；做成 `:148-150` 的硬 FAIL 依规格也是对的；**缺的是「padding 检测 + 真封印实读」**。
- 上游 reply 的 S03/S06/P8「真第三方封印」名不副实（复核④）：sha256 只算在审计脚本旁路字典；`_cfav_stdout.txt:16-21` 的 AST 审计显示全部 check 函数 `opens_file=False computes_hash=False`，`_cfav_stdout2.txt:65-93`（本会话读取）传 `artifact_text` 得 `TypeError: no_relaxation_check() got an unexpected keyword argument 'artifact_text'`；本会话 C3 亦得同错（`_cfaa_stdout.txt:69`）。标 unconfirmed 的上游「真第三方封印」措辞。

**对照（旧检验踩过的三个基数坑，新检验已修好）**：`S08` 加真翻案 / `S09` 引文改写 / `S10` 删一对（3(b) 表）全部正确 `PASS`；本会话 B6/B7/B8 亦 `PASS`。⇒「对基数过敏」已修，但换上了「对同源敏感」的确定性开关；两者都不是随机误报率。

---

## 4 三层独立性（L1 单独能力 + L2 依赖 ORACLE 存在性 + L3 出题者同源性 + 哪几层真独立）

**结论：本次实跑中真正独立于被测对象的层数 = 0。** 三层都不独立，且 `:238` 的 `ok = l1_ok and l2_ok and l3_ok` 把三个**相关**失效叠加，容易被误读成「三层独立互证」。

### 4(a) L1 单独能力

- 代码自认：`_fnr_check.py:156-157` 的 `verdict_note` = `L1 alone can only ALARM on set changes; it can never validate semantic truth. L2+L3 are mandatory.` ⇒ L1 单独**不能**判「没放松」。
- 签名：`_cfaa_stdout.txt:67` 实跑 `check_l1` 仅 7 参数（`items, flips, whitelist, registered_tokens, predicate_spec_keys, whitelist_sealed, whitelist_author`），无 `certificates` / `artifact_text` / ORACLE 槽；`no_relaxation_check` 13 参数亦无交付件原文槽（复核⑤ P5）。
- 召回：P10（`_cfaa_stdout.txt:70`）9 个已知错注入，逐层报警计数 `L1=3, L2=6, L3=1`（`_cfa_stdout.txt:76` / `_cfav_stdout.txt:71` 同值）⇒ L1 单独 3/9 = 0.3333。
- 覆盖率是装饰性指标：P11（`_cfaa_stdout.txt:71`）把 `registered_tokens=set()` 得 `ok=true, coverage=0.0, problems=[]`（`_cfa_stdout.txt:77` / `_cfav_stdout.txt:62` 同值）。292 / 0.0331 只被写进 `detail`，从不参与 `ok` 判定。
- 同源实证：`WHITELIST_AUDIT.md:517` 记「白名单由派发方预置且与 SPECS 同源」；`lead/gate_r9sem_20261109/_r9s_regress.py:112-119` 与 `lead/gate_r9sem_20261109/_r9s_predicates.py:368-402` 为标准集/被测 SPECS 同源出处（【审计】evidence §1 引；本会话未重读该两处全文，标**未验**）。

### 4(b) L2 依赖 ORACLE 存在性

- `certificate_ok`（`_fnr_check.py:95-124`）只验：anchor 正则 `^.+:\d+$`（`:100`）、`len(quote)>=10`（`:103`）、roles 长度/`NON_VALUE_RE`（`:106-114`）、以及**调用方自声明**的 `oracle_truth` / `oracle_author` / `oracle_sealed` 三个布尔/字符串（`:116-123`）。**从不 `open()` 任何 `file:line`，从不重算 SHA256。**
- 命令 C3 的 AST I/O 审计（`_cfaa_stdout.txt:60-66`）：`certificate_ok / check_l1 / check_l2 / check_l3 / no_relaxation_check / meta_test` 全部 `opens=False hash=False`；只有 `main`（`:354`）`opens=True writes=True`。`_cfav_stdout.txt:16-22` 同结论。
- 三目录 `find` 无 `*oracle*` / `*seal*` 文件（`_cfaa_stdout.txt:74` 输出 `oracle/seal files= []`）。
- 作者自认：`_fnr_check.py:309-313` 明写 5 份 `CERTS` 是「HYPOTHETICAL inputs…deliberately constructed here by THIS session…explicitly flagged as such」；`_fnr_REPORT.md:427` 明写「**演示性假设输入**…不是第三方盲标注的真实 ORACLE…**设计与可行性验证**，不构成对现盘 R9 升级的重新认证」。
- 决定性实跑 P1（命令 C3，`_cfaa_stdout.txt:68`）：把 5 份证书锚点全改成 `cfaa/NO_SUCH_i.md:999999`、引文全改成本会话凭空编造的句子，`VERDICT=PASS, L1_ok/L2_ok/L3_ok=true, anchor_files_exist=[false,false,false,false,false]`。`_cfa_stdout.txt:65` 与 `_cfav_stdout.txt:66` 的 P1 同值；`_cfav_stdout2.txt:97` 的 `wrong2_all_anchors_forged=PASS` 亦同。

⇒ **独立封印 ORACLE 不存在时，L2 必然退化为自证**。仅当「第三方盲标注 + 预注册 SHA256 封印 + 检验端实际 `open` 并重算 hash」三者齐备，L2 才独立。项目唯一真正异源的真值：`WHITELIST_AUDIT.md:467` 的「这一结论来自**人工独立读原文**，不是机制证明」与 `:516` 的「自读 4 主件原文 + 解 4 份任务书 payload + 自跑逐行 `==`，5/5 独立判语义在场」（命令 C2 输出，`_cfaa_stdout.txt:27,29`）；`:498` 记「应保留 5 / 应移除 0」。**它没有进入检验的 ORACLE 输入槽**（§4(a) P5 `TypeError`）。〔引用瑕疵，复核⑤ 成立并标 unconfirmed 的上游原句：上游称 `:467` 是「5/5 人工独立读原文」，`:467` 实为「整体窄、局部宽…自证循环」段，精确行是 `:498`/`:516`；`:517`/`:522` 只在 558 行的 `WHITELIST_AUDIT.md` 有效，在 516 行且指纹在册的 `_WL_WHITELIST_AUDIT.md` 越界（`_cfaa_stdout.txt:32` 实测 `<OUT OF RANGE>`）。〕

### 4(c) L3 出题者同源性

- 13 条 `ADVERSARIAL` 定义在 `_fnr_check.py:291-305`；`repaired_predicate` 的 `AUTHOR_GUARD` 词表在 `:478-480`（同文件）。命令 C3（`_cfaa_stdout.txt:72`）：13/13 语料逐字含 ≥1 个 guard 词（拟合）。
- 盲留出即失效：3 条不含作者 guard 词的 novel empties（`N-EMPTY-1/2/3`），作者 guard 得 `14/16`，`N-EMPTY-1`、`N-EMPTY-2` 漏（`_cfaa_stdout.txt:72-73`；`_cfav_stdout2.txt:30` 同值）。⇒ `13/13` 是**出题者与被测者同源的自证**，不是独立验证。L3(ii) 的 15/15 变异注入是真机制自检，但只测 `certificate_ok` 对指针词的反应，不接触真实交付件（`_fnr_check_out.json:286-288`）。
- **但「13 条同文件同作者」的作者归属过头（复核⑤，标 unconfirmed 的上游原句）**：`_cfav_stdout2.txt:32-46` 的 provenance 实证 13/13  payload 的**特征片段**早见于上游 `lead/whitelist_audit_20261109/_wlw_stepC.py`、`_wl_step3_struct.py`、`WHITELIST_AUDIT.md`、`_WL_WHITELIST_AUDIT.md`，`verbatim_full_payload_upstream=0 / fragment_upstream=13`；本会话 C3 独立算 `P2_upstream_fragment_hits = 13/13`（`_cfaa_stdout.txt:72`）。⇒ **拟合为真，作者归属未证**；准确表述是「语料与 guard 词表在同一文件被组装并被逐字拟合」，而非「全部由 `_fnr_check.py` 作者原创」。
- 复核自曝（`_cfav_stdout.txt:68-69`）：本会话/复核自造的宽 guard 虽得 16/16，但词表亦经 novel 拟合，**不作独立 guard 证据**；本会话 `_cfaa_verify.py` 的 `MY_GUARD` 同理，仅用于对照，不作独立性证据。

### 4(d) 哪几层真独立 / 桥接方案

| 层 | 名义 | 本会话实测 | 真独立 |
|---|---|---|---|
| L1 | 结构/覆盖 | 同源标准集、7 参数、3/9 召回、`coverage=0.0` 仍 PASS | **否** |
| L2 | 语义证书 | 无 `open`/无 hash、三目录无 oracle/seal 文件、伪造 5 锚点仍 PASS | **否**（仅当真封印 ORACLE 实读才可能独立） |
| L3 | 对抗 + 变异 | 13/13 逐字拟合作者词表、盲留出 14/16、15/15 变异只测自身 | **否** |

桥接真实数据（方案，本会话**未实装未实跑，标未验**）：①第三方盲标 302 项 ORACLE 真值表 + 预注册 SHA256 封印，检验端 `open()` 后重算并比对；②≥30 条不含作者词表的**一次性封 SHA 盲留出**对抗语料；③给 `no_relaxation_check` 增 `artifact_text` 槽并实读 4/5 主件原文；④把 `WHITELIST_AUDIT.md:467/:498/:516` 的人工独立 5/5 真值接入 ORACLE 槽；⑤双基线元检验并公开「本检验在以下情形不报警」清单。

---

## 5 元检验局限（9/2 规模 + 基线敏感 + 合成世界 ≠ 理想情况 + 桥接方案）

### 5(a) 9/2 规模够不够

`_fnr_check_out.json:390-420`：`n_wrong=9, n_wrong_caught=9, n_good=2, n_false_alarms=0, CHECKER_VALID=true, synthetic_baseline_VERDICT=PASS, synthetic_predicate_adversarial_catch=13/13`。命令 C3（`_cfaa_stdout.txt:89-95`）复算 P7：

```
sensitivity_lower_95 = 0.05^(1/9) = 0.716871
fp_upper_95          = 1 - 0.05^(1/2) = 0.776393
```

⇒ 9/9 全抓**仅支持「敏感度 ≥ 71.7%」**；0/2 **无力排除 77.6% 的假阳性率**。而本次三套实测给出 50% / 12.5% / 0%（§3(d)），恰好证明 2 个 good variation 无法估计总体假阳性。更根本的：9 个注入全部作用在检验**已有**槽位（`certificates` / `whitelist_sealed` / `flips` / `predicate` / `spec_keys`，`_fnr_check.py:490-501`），而「真实交付件原文」槽根本不存在（§4 P5），故漏掉整个错误类不会使元检验失败（`_cfav_stdout2.txt:97` 的 `wrong2` 即反例）。

### 5(b) 基线敏感（新发现 P3，本会话确认）

`_fnr_check.py:280` 的 `CHECKER_VALID = (n_caught == len(wrong_rows) and n_false == 0)` **不含 `baseline_VERDICT`**。命令 C3（`_cfaa_stdout.txt:78-83`）：

```
P3_empty_lists_on_ALARM_baseline: baseline_VERDICT=ALARM, n_wrong=0, n_good=0, CHECKER_VALID=true
```

即**空注入 + 空良性清单在 ALARM 基线上直接得 `CHECKER_VALID=true`**，与 `_fnr_REPORT.md:338` 模板第 0 步 `assert checker(good_world) == PASS  # 已知-好世界必须通过` 矛盾（模板写了，代码未实现；`_cfaa_stdout.txt:33` 实读该行）。P4（`_cfaa_stdout.txt:84-88`）复现 `_fnr_REPORT.md:239` 记的首次实跑中间态：`baseline=ALARM, n_false_alarms=2, CHECKER_VALID=false`；`_fnr_check.py:465-467` 自己写明「现盘 R9S 状态 NOT a good world（有真实缺陷），拿它当基线会让每个 good variation 继承 ALARM」。⇒ **基线敏感**是实存缺陷，且 `_fnr_REPORT.md:239` 明写「检验有效的证明本身也需要一个可证伪的基线」。

### 5(c) 合成世界等于理想情况吗

**不等于。** `good_base`（`_fnr_check.py:485-488`）靠 `good_base["spec_keys"] = set(R9S.SPECS.keys()) | {"额外预留要素"}`（`:486`）这一**无关预留键**才消除 self-certification；P9（`_cfaa_stdout.txt:97-100`）实跑 `with_dummy_key=PASS` / `without_dummy_key=ALARM`。`repaired_predicate`（`:471-483`）是内存中的演示性修补，作者自注 `Demonstration only; NOT a change to any on-disk predicate`（`:473-474`），`_fnr_REPORT.md:427` 再确认不构成重新认证。⇒ 元检验的 `PASS` 基线是**作者自己拼出来并通过作者自己判据**的合成世界，与「理想情况」之间有 `padding` 这一人为自由度；`_fnr_REPORT.md:239` 甚至把「`spec_keys` 多一个预留键以消除 self-certification」明写为做法。

### 5(d) 桥接真实数据的方案（未实装，标未验）

1. 双基线：同时断言 `checker(good_world)==PASS` **与** `checker(real_state)` 的期望值，并把 `baseline_VERDICT=="PASS"` 纳入 `CHECKER_VALID`（修 `_fnr_check.py:280`）。
2. 规模下限：`n_wrong ≥ 30`、`n_good ≥ 30`，good 世界必须来自**一次性封 SHA 的盲留出**，且逐场景公布 `VERDICT` 与触发层；报告 Wilson 区间而非点估计。
3. 覆盖错误类：注入必须包含「交付件原文级」错误（伪造 `file:line`、删主件段落、改引文），并给 `no_relaxation_check` 增 `artifact_text`/`seal_path` 槽 + 实 `open` + `hashlib` 重算。
4. 真 ORACLE：第三方盲标 302 项、预注册 SHA256 封印、检验端先验封印再读（`WHITELIST_AUDIT.md:506` 原话）。
5. 强制公开「本检验在以下情形不报警」清单，把 P5 / H3 这类**结构性不可表达的错误**写进文档，禁止用 `CHECKER_VALID=true` 覆盖。

---

## 6 复核回件 + 结论 + 未验项

### 6(a) 绑定行（固定格式，本行不加粗、不反引号、不插路径/括号/星号/空格）

被核对象 SHA256 = 94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2，字节数 = 28811

出处：命令 C1 与 `_cfaa_stdout.txt:2`；与【编排方指纹】`_fnr_check.py` 的 sha256/bytes 完全一致。C3 收尾复查（`_cfaa_stdout.txt:112-115`）值不变。

### 6(b) 复核 verdict 如实登记

**复核 verdict = `partial`**（【复核】字段原值；`ranCommands=32`，`sha256Line` 为本节 6(a) 同串）。按任务铁律「refuted 或 partial 标 unconfirmed」：

- **被推翻 / 标 unconfirmed 的上游结论**：①「合规同源是合规设计、L1 在合规设计上永远 ALARM、L1 过严误报、50% 是随机假阳性率」——`WHITELIST_AUDIT.md:506` / `_WL_WHITELIST_AUDIT.md:476` / `FALSIFIABLE_NO_RELAX.md:458` / `_fnr_REPORT.md:256` / `_fnr_check.py:85-86` 明禁同源，64 世界证明是确定性开关；②「总 ALARM 被 L3 偶然救对」——P8/H1/H2 证明 L1+L3 双重决定；③「真第三方封印」名不副实（无槽、AST 无 open/hash、传 `artifact_text` 得 `TypeError`）；④「L3 13 条同文件同作者」作者归属过头（上游片段 13/13）；⑤`WHITELIST_AUDIT.md:467` 的引用瑕疵、`:517/:522` 在 516 行 `_WL_WHITELIST_AUDIT.md` 越界；⑥「任务点名的 8 个场景」原始任务书全库不可核（命令 C9 仅命中 `_CFA_REPORT.md` 自身 1 件）。
- **复核确认成立、本会话亦确认**：8/8 指纹 `ALL_EIGHT_MATCH=True`；绑定行格式 1 次且合规；`292` / `0.0331`；L2 自证（伪造证书 `PASS`）；作者精确 guard 13/13 拟合 + 盲留出 `14/16` 漏 `N-EMPTY-1/2`；`meta_test:280` 缺 baseline 致空清单在 ALARM 基线上 `CHECKER_VALID=true`；P4 2 误报；P7 `0.716871` / `0.776393`；P9 padding；P11 `coverage=0.0` 仍 `PASS`；P5 无交付件槽；P10 `3/9-6/9-1/9`；三目录无 oracle/seal 文件；无越界（命令 C6/C7/C8：只读域 17:50 后无新文件、无写域外 `_cfa_`/`_cfav_`/`_cfaa_` 件、`git log -1` 仍 `2657458`、未 commit/未 push）。
- **本会话新增**：把上游 reply 的 10 场景、复核的 11 场景、本会话 11 场景全部列出逐场景 `VERDICT` 与触发层（§3(a)(b)(c)）；把 64 世界全因子在本会话复现（C4）并诊断首版语料差异（C5）；读实 5 条明禁同源行（C2）。

### 6(c) 结论

1. **现状有问题，不是「检验过严」单点。** 真缺陷清单：L3 的 7-13（7/13）与 6 条泄漏（`_fnr_check_out.json:422-426`）；L1 的 292 / 0.0331 覆盖率只是 `detail` 装饰、0.0 仍 `PASS`；L2 无 `open`/无 hash、伪造 5 锚点仍 `PASS`；`meta_test:280` 缺 baseline；交付件原文槽不存在。「检验过严」的 50% 假阳性结论已被复核 `partial` 推翻并标 unconfirmed。
2. **但 L1 的判据强度确有真缺陷**：SELF_CERTIFIED 依 (E) 条规格是正确报警，却只比较集合相等、可被 `:486` 的「额外预留要素」padding 绕过（P9 实跑 `PASS`↔`ALARM`），量不到「来源独立」。这是**设计规格与其操作化之间的落差**，不是误报。
3. **能否用于生产：不能。判「需改后再插」。** 总 `VERDICT=ALARM` 方向正确，但由 L1 + L3 双重决定且三层零独立（§4），不能采信为「三层独立互证」；`_fnr_REPORT.md:427` 自己也只把它定位为「设计与可行性验证，不构成对现盘 R9 升级的重新认证」。
4. **最小改法（方案，未实装未实跑，标未验）**：①`_fnr_check.py:116-123` 的独立性改为对真实 SHA256 封印文件 `open()` + `hashlib` 重算校验，并加 padding 检测使无关预留键不能凭空绕过；②给 `no_relaxation_check` 增 `artifact_text` / `seal_path` 槽并实读 5 主件；③`:280` 的 `CHECKER_VALID` 纳入 `baseline_VERDICT=="PASS"` 并前置 `n_wrong/n_good` 规模下限；④`:148-150` 的 `multiset` → `set` 措辞校正，`:154` 的 `coverage` 阈值改为真 FAIL 条件；⑤≥30 条一次性封 SHA 盲留出语料接入 L3；⑥双基线元检验 + Wilson 区间 + 强制公开「本检验在以下情形不报警」。**本会话不改新检验、不改任何既有件，以上仅为审计建议。**
5. **判不了什么**：真实交付件原文的语义在场；302 项 ORACLE 真值；第三方盲标封印是否真实存在（三目录无文件，但**全库未穷举**）；5 主件语义裁决未独立重判（沿用 `WHITELIST_AUDIT.md:498/:516`）；随机总体假阳性率（三套场景均非随机抽样，且 64 世界为确定性开关）；改动方案效果（未实装）；`_fnr_check.py` 的 `main()` 与 `_r9s_regress.py` 本体结果（替代执行，见 §1）；零真机条件下的一切运行时行为。

### 6(d) 「检验的检验」清单（逐条可用命令/行复核）

| # | 检查项 | 本会话执行 | 结果 |
|---|---|---|---|
| 1 | 上游 8 件指纹 `hashlib` 独立重算 + 收尾复查 | C1 + C3 §A/§G | `ALL_EIGHT_MATCH=True`，收尾 8 件不变 |
| 2 | 绑定行格式（64 hex 连写 + `，字节数 = `） | C1 / §6(a) | 1 次出现，无插入字符 |
| 3 | 三层逐层 `ok`/`problems`/`detail` 重算 | C3 §B | `ALARM / L1 false / L2 true / L3 false` |
| 4 | `SELF_CERTIFIED` 公式溯源（set vs multiset） | C2 读 `:137/:138/:149` | set 相等；文案措辞瑕疵 |
| 5 | 292 / 0.0331 重算 | C3 §B `l1_recompute` | `302-10=292`，`10/302=0.0331` |
| 6 | 7-13（7/13）与 6 条泄漏 id 独立复现 | C3 §B | `7/13`，`CF3,CF5,WCF5,V2,V3,V6` |
| 7 | 项目是否明文禁止同源（决定 FP 判定） | C2 读 5 行 | 明禁 ⇒ 上游「合规同源」unconfirmed |
| 8 | ≥8 个良性场景逐场景 `VERDICT` + 触发层 | C3 §D（11 个）+ 读 `_cfa_stdout.txt`/`_cfav_stdout.txt` | §3(a)(b)(c) 三张表 |
| 9 | 假阳性率多口径 + Wilson | C3 §D | 0/8、3/11、1/8、4/8…全部列出 |
| 10 | 64 世界全因子：FP 是随机率还是确定性开关 | C4 + C3 §D + C5 差异诊断 | `32/32` vs `0/32`，其余 6 轴零影响 |
| 11 | 「总在报警 / 总不报警」双向反例 | C3 §D + 读 `_cfav_stdout2.txt:97` | 两者皆否，交付件级错误恒 `PASS` |
| 12 | 「L1 合规设计上永远 ALARM」真伪 | §3(e) | **否**；仅违规同源世界恒 ALARM |
| 13 | AST I/O：check 函数是否 `open`/`hash` | C3 §E | 全部 `opens=False hash=False` |
| 14 | 签名 / 交付件槽 / ORACLE 封印文件存在性 | C3 §E | 13/7/2 参数无槽；`TypeError`；`oracle/seal files=[]` |
| 15 | L2 自证反例（伪造锚点 + 编造引文） | C3 §E P1 | `PASS`，5 个锚点文件全不存在 |
| 16 | L3 拟合 + 盲留出 | C3 §E P2 | `13/13` 拟合；`14/16`，漏 `N-EMPTY-1/2` |
| 17 | L3 语料作者归属（上游片段） | C3 §E + 读 `_cfav_stdout2.txt:32-46` | 片段 `13/13` 上游 ⇒ 拟合真、作者归属未证 |
| 18 | `coverage=0.0` 是否仍 PASS | C3 §E P11 | `ok=true, problems=[]` |
| 19 | 逐层召回（9 注入） | C3 §E P10 | `L1=3, L2=6, L3=1` |
| 20 | 元检验空清单 + 基线敏感 | C3 §F P3/P4 | `ALARM` 基线得 `CHECKER_VALID=true`；P4 `2 误报/false` |
| 21 | 9/2 规模统计功效 | C3 §F P7 | `0.716871` / `0.776393` |
| 22 | 合成世界 = 理想情况？ | C3 §F P9 + 读 `_fnr_REPORT.md:427` | 否，靠 `:486` padding |
| 23 | 原始 8 场景任务书可核性 | C9 | 全库仅命中 `_CFA_REPORT.md` 自身 ⇒ 不可核 |
| 24 | 只读域零改动 / 未 commit / 未 push | C6+C7+C8 | 只读域 17:50 后无新文件；`2657458`；状态同会话快照 |

### 6(e) 未验项（逐条，不补造）

1. **未跑本体**：`_fnr_check.py` 的 `main()`（`:548-549` 回写只读域）与 `_r9s_regress.py` 本体（`_fnr_REPORT.md:22`）；本会话用 `importlib.util.spec_from_file_location` 模块加载 + `sys.dont_write_bytecode=True` 作替代执行，`no_relaxation_check()`/`check_l1()`/`meta_test()` 均为函数级调用，非 CLI 本体实跑。
2. **未重跑上游脚本本体**：`_cfa_probe.py` / `_cfav_probe.py` 的既有输出为「读到的既有实跑输出」，本会话未重跑；仅 `_cfav_probe2.py` 由 C4 重跑（并回写同域 `_cfav_out2.json`，见 §1）。
3. **未独立重判 5 主件语义裁决**：沿用 `WHITELIST_AUDIT.md:498`（应保留 5 / 应移除 0）与 `:516`（5/5 独立判语义在场），本会话未打开 4 主件全文逐条重判。
4. **未全库穷举 ORACLE/封印**：三目录（`falsifiable_no_relax` / `whitelist_audit` / `gate_r9sem`）`rglob` 未找到 `*oracle*`/`*seal*` 文件；仓库其余位置未穷举。
5. **未重读同源实证两处全文**：`_r9s_regress.py:112-119`、`_r9s_predicates.py:368-402` 仅按【审计】evidence 引，本会话未逐字复核。
6. **改动方案未实装、未实跑**：§5(d) / §6(c)-4 的全部桥接与最小改法均为审计建议。
7. **非随机抽样**：三套良性场景均为定向构造，50% / 12.5% / 0% 皆非无偏总体估计；64 世界为全因子确定性设计，Wilson 区间仅作对照、不作总体推断。
8. **零真机**：未启动任何游戏进程，未采样，未读活内存；「实跑」一律指离线 Python 脚本与只读文件读取。
9. **任务点名的 8 个场景原始任务书不可核**：命令 C9 全库仅命中 `lead/check_fp_audit_20261109/_CFA_REPORT.md` 自身，来源标未验。
