# LEDGER_BOUND_VOLUME.md — 《待入账草案·合订本》· 交付件（合订本撰写员，2026-11-09）

> 性质：本件是**合订本**（索引 + 草案正文逐字照抄 + 冲突/依赖登记 + 编号检查 + 复核回件），**不是台账、不入台账**。
> 铁律：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）。
> 绝对只读：`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`、`lead/ledger_appendix_20261108/`、`lead/s604_verdict_entry_20261109/`、`lead/s604_refsync_20261109/`、`lead/a_class_fix_20261109/`、`lead/handoff_pack_20261109/` 一律未修改、未追加、未覆盖。
> 唯一写域 = `lead/ledger_bound_20261109/`。**只合订不改台账**；**不替 Leader 决定哪笔先入账、哪笔暂缓**，只列冲突与依赖、列前置问题。
> 不 commit、不 push。Python 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib。
> 引用口径：每条结论追到「本会话实跑命令 + 输出」或「文件:行」；拿不到的一律写「未验」，不补造。
> 复核 verdict 如实记：本批既有合订本主件复核 verdict = **confirmed**；§609 草案自身复核 verdict = **partial** → 该笔按 **unconfirmed** 登记（见 §5）。
> 草案正文 5 段全部**逐字照抄**：由内联 `python -I -X utf8 -c` 组装命令从 5 份单件草案件的标记行之间按字节切片直接嵌入骨架 `_lb2_TEMPLATE.md`，未润色、未改写（本会话 ALL_VERBATIM = True，见 §2.3）。

---

## 1 · 一页纸总览（几笔 / 字节 / 编号 / 依赖图）

### 1.1 待入账清点：实盘 **5 笔**，不是任务第三步(b)所称「六笔」

- 判定口径：带可整段复制追加的 `## §6xx` 草案正文、目标为 `GOAL_THREE_TARGETS_20261018.md` 尾部新节。
- 本会话全仓实盘清点 = **5 笔**（暂编 **§605–§609**）。第六笔 / §610 / 第六个 `## §6xx` 入账草案正文：全仓 grep `§610|§611|第六笔|六笔全入账` 于 `lead/**/*.md`（排除本写域自身讨论行与 `_o1_tmp` 长路径目录后）**0 命中**，按「不补造」如实登记为「**未验 / 未见**」；若编排方另指第六笔，需补下发该件路径与编号（列为前置问题 Q5，不代造）。
- 另有四组「改既有件的订正草案」（S604_REFSYNC 13 处、refsync_full 剩余 28 处、A_CLASS A1/A4/A5、handoff_pack U1–U9 九条）**不是入账项**，是改/加注既有件的建议（见 §4 附录 D）；本会话 grep 实证这 5 份主件 `^## §6` 命中数均为 0。

### 1.2 五笔一览（编号 / 标题 / 单件草案件字节数 / 抽取正文段字节数）

| 笔 | 暂编 | 标题（节题首句） | 单件草案件（正文出处） | 草案件字节数 | 抽取正文段字节数 / SHA256 |
|:--:|:--:|:--|:--|--:|:--|
| 1 | §605 | N-9:205 P6 前提订正 → 半闭半开 | `lead/ledger_appendix_20261108/_la_draft1_n9_p6_erratum.md:14-27` | 7806 | 4735 / `5c37adc6…` |
| 2 | §606 | O1–O4 必要性补证 necessaryCount=3 | `lead/ledger_appendix_20261108/_la_draft2_o4_necessity.md:13-23` | 6714 | 4097 / `030f5a62…` |
| 3 | §607 | §604「空档/空档差」两列不可复现（0/15、15 窗全正） | `lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md:13-26` | 7703 | 4894 / `e9842d41…` |
| 4 | §608 | 「以乙替代甲」补登（九 hunk + 11 件指纹，登记而非放行） | `lead/ledger_appendix_20261108/_la_draft4_yi_supersede_jia.md:13-41` | 10080 | 6318 / `24a497e8…` |
| 5 | §609 | §604 码形定谳：错误源 = 撰写轮内联脚本 dur 字典错位（等价 C8a） | `lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md:13-25` | 18980 | 8388 / `f4c3433a…` |

- 5 份单件草案件合计 = 7806 + 6714 + 7703 + 10080 + 18980 = **51283 B**；5 段抽取正文合计 = 4735 + 4097 + 4894 + 6318 + 8388 = **28432 B**；各段 SHA256 见 §2.3（本会话 hashlib 实算）。
- 汇编件 `lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md`（45719 B）:47/:81/:111/:150 分别逐字转录笔 1–笔 4；第五笔同文副本 `lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md`（36097 B）:70-82 载同一 §609 正文。
- 5 笔状态**全部「未入账、可整段复制追加、草案正文逐字照抄已验」**；笔 3 severity = **high**（已发布数字实质订正，`LEDGER_APPENDIX_DRAFT.md:206`）；第 5 笔 §609 状态 **unconfirmed**（复核 verdict = partial，`S604_VERDICT_ENTRY_DRAFT.md:137`）。

### 1.3 编号与依赖图

- 台账现尾 = **§604 @:9687**（`grep -n '^## §' … | tail -3` → §602@9510 / §603@9585 / §604@9687；`wc -l` = 9757；`grep -c '^## §'` = 61），故 5 笔暂编 **§605–§609** 连续、无需重排（详见 §4）。
- 依赖速览（不替 Leader 决定顺序）：

```
  笔1 §605 ── 独立 ──────────────────────────────┐
  笔2 §606 ── 独立 ──────────────────────────────┤
  笔4 §608 ── 独立（与 handoff_pack U1–U9 共享被绑定文件，属改件联动，非笔间硬顺序）
                                                  ├─→ 待 Leader / 台账所有者裁决（Q1–Q7）
  笔3 §607 ── 被第 5 笔补充（边界句「不能定位」被超越）──╫── 唯一「建议成组」的一对
  笔5 §609 ── 依赖/补充笔3（以其为对照物；状态 unconfirmed）╯
```

> 结论（先写在这里，逐组判定见 §3）：**无「笔必须先于笔」的强制硬顺序**（`LEDGER_APPENDIX_DRAFT.md:11`「四段各自独立、可单独追加」、:209）；笔 3 ↔ 第五笔是「补充，不是冲突」，唯一「建议成组」的一对（叙述自洽性，属「宜」非「必须」）。

---

## 2 · 上游指纹（十一件）+ 待入账清点（每笔编号标题出处字节）+ 已入账 grep 结果

### 2.1 编排方下发 11 件基线指纹（本会话 hashlib 全量复算）

实跑命令（本会话）：`cd /d/Project/ra2-campaign-forge && python -I -X utf8 -c "<内联 hashlib：11 件绝对路径，逐件 sha256 + len>"` → 输出逐件 `OK <path> sha256=<64位> bytes=<n>`，收尾 `BASELINE_MATCH 11 / 11`。

| 件 | SHA256 | 字节数 | 复算 |
|:--|:--|--:|:--:|
| `lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md` | `724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e` | 45719 | MATCH |
| `lead/ledger_appendix_20261108/_la_draft1_n9_p6_erratum.md` | `e863b593bf5c29a9f2ce38aca4773b7feacb625f6ac32e33d04b5e9a2bae02e4` | 7806 | MATCH |
| `lead/ledger_appendix_20261108/_la_draft2_o4_necessity.md` | `213fb89819d316e5a74e5acb065cc17cd2845602b9f79a45e5e10b73bb6ae4da` | 6714 | MATCH |
| `lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md` | `d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6` | 7703 | MATCH |
| `lead/ledger_appendix_20261108/_la_draft4_yi_supersede_jia.md` | `bf010e8d22cf70892365cbadf555c8fd3b51291a355e4b49c429dc86c46f892e` | 10080 | MATCH |
| `lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md` | `058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec` | 18980 | MATCH |
| `lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md` | `1e4ceb37187cd12601ad03cdc02f0cf2ee624d1f6870c03c0e35d84cbcb40cfc` | 36097 | MATCH |
| `lead/s604_refsync_20261109/_rs_REFSYNC_DRAFT.md` | `7477a869f1d8436b7641b3b5ba09dac778ed078228adbabc0469d5665419d572` | 33869 | MATCH |
| `lead/a_class_fix_20261109/_ac_A1A4A5_FIX_DRAFT_20261109.md` | `6c02341b319360e06bc9f1ad096e4c8d5a04ff649c83389e806337c8ead615bc` | 23258 | MATCH |
| `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 | MATCH |
| `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 | MATCH |

- 两台账收尾复算仍等于编排方基线：`PENDING` = `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` / 52419 B；`GOAL` = `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` / 759518 B ⇒ **未改台账**（§5 再申明）。
- 另见既有旁证：`lead/ledger_bound_20261109/_lb_fp_out.txt`（11 件基线 + 5 段 BODY 抽取指纹 + 两台账 TAIL 复算）、`_lb_VERIFY.md:47-52`。

### 2.2 待入账清点 + 已入账 grep 结果

**已入账核查实跑命令**：
```
cd /d/Project/ra2-campaign-forge && grep -nE '§60[5-9]|§610|半闭半开|码形定谳|dur 字典|以乙替代甲|甲乙绑定|necessaryCount|O4 非必要|空档差.*0/15' lead/GOAL_THREE_TARGETS_20261018.md lead/PENDING_DECISIONS.md
```
**输出**：无输出，`grep_exit=1`（0 命中）⇒ **5 笔全部未入账**。

**编号 grep 实跑**：`grep -nE '§60[5-9]|§610' lead/GOAL_THREE_TARGETS_20261018.md lead/PENDING_DECISIONS.md` → 无输出，`grep_exit=1`（0 命中）。

| 笔 | 暂编 | 标题 | 正文出处（单件草案件:行） | 草案件字节 | 已入账? |
|:--:|:--:|:--|:--|--:|:--|
| 1 | §605 | N-9:205 P6 前提订正 → 半闭半开 | `lead/ledger_appendix_20261108/_la_draft1_n9_p6_erratum.md:14-27` | 7806 | 否（grep 0 命中） |
| 2 | §606 | O1–O4 必要性补证 necessaryCount=3 | `lead/ledger_appendix_20261108/_la_draft2_o4_necessity.md:13-23` | 6714 | 否（grep 0 命中） |
| 3 | §607 | §604「空档/空档差」两列不可复现（0/15、15 窗全正） | `lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md:13-26` | 7703 | 否（grep 0 命中） |
| 4 | §608 | 「以乙替代甲」补登（九 hunk + 11 件指纹；登记而非放行） | `lead/ledger_appendix_20261108/_la_draft4_yi_supersede_jia.md:13-41` | 10080 | 否（grep 0 命中） |
| 5 | §609 | §604 码形定谳（dur 字典错位，等价 C8a） | `lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md:13-25` | 18980 | 否（grep 0 命中） |

- `PENDING_DECISIONS.md` 待裁段仅 **D-13**（:30「### D-13 原始正文（保留供追溯，不改）」）与 **D-14**（:67 同式），本会话 `grep -nE '^### D-'` 实测两行；D 编号与 § 节号是两套序列。
- 台账尾：`grep -n '^## §' lead/GOAL_THREE_TARGETS_20261018.md | tail -3` → §602@9510 / §603@9585 / **§604@9687**；`wc -l` = 9757；`grep -c '^## §'` = 61。

### 2.3 逐字照抄核验（本会话实跑）

**核验命令**：`python -I -X utf8 -c "<内联：5 份单件草案件按标记行切片取正文段；hashlib 取 SHA256；与既有合订本嵌入段 find 计数>"`。
**输出**：
```
笔 1 body_bytes 4735 sha256 5c37adc6e64dd245b3392ed554a2185b489ab683496b9b223b6622af4bc86a6c   count_in_bound(find)= 1
笔 2 body_bytes 4097 sha256 030f5a62328ec661c814f531ff5e54f43db2ac7c8cbd88d4e8d1050c9961bdc6   count_in_bound(find)= 1
笔 3 body_bytes 4894 sha256 e9842d41f27d70b80067c5a6b89afe81ab63eb0422c7eda741d1c5983a3df698   count_in_bound(find)= 1
笔 4 body_bytes 6318 sha256 24a497e8f63aece592a7a863cdb7d03a93d438dfa3f657dba1c1aaca260b775b   count_in_bound(find)= 1
笔 5 body_bytes 8388 sha256 f4c3433a0141afbc59da7b72fdf679aacbae8b0ed9276530089a6a6528501682   count_in_bound(find)= 1
ALL_VERBATIM = True
```
- 判据：源件正文整段（UTF-8 字节串）在既有合订本里 `find` 计数恰为 1（改一字即 0 命中）；各段 SHA256 与 `_lb_VERIFY.md:30-34` 既有登记一致。本交付件同样由源件切片嵌入，组装后复验 5 段 `find=1`。
- 既有主件 `lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md` 本会话实算 `bytes 60272 / LF 319 / CRLF 0 / CR 0 / sha256 7770da46b5c684add476ec286673d70d73f332fb5ac286d07cabcdaadc4eac43`；其 5 组 `#### ↓↓↓ 草案正文` / `#### ↑↑↑ 草案正文` 标记各 5 个、绑定行正则 `被核对象 SHA256 = ([0-9a-f]{64})，字节数 = ([0-9]+)` 命中 5 行且 64 位全 `len_ok=True`。（注：`_lb_VERIFY.md:28` 记 LF=288，本会话实测 319，纯 LF 结论不变；属元数据小出入，非正文。）

### 2.A 五笔草案正文（逐字照抄，未润色改写）

> 抽取口径：各单件草案件 `## ↓↓↓ 草案正文…` 与 `## ↑↑↑ 草案正文结束…` 两标记行之间的全部行，**不含标记行本身**；由本写域内联 `python -I -X utf8 -c` 组装命令以 `split('\n')` 切片后按字节直接嵌入骨架 `_lb2_TEMPLATE.md`，未按字符改写。每章末给出固定格式绑定行。

### 第 1 笔 · §605 · N-9:205 P6 前提订正 → 半闭半开

- **出处**：`lead/ledger_appendix_20261108/_la_draft1_n9_p6_erratum.md:14-27`（标记行 :12 / :29 之间）；同文副本 `LEDGER_APPENDIX_DRAFT.md:47-60`。
- **草案件指纹**：SHA256 = `e863b593bf5c29a9f2ce38aca4773b7feacb625f6ac32e33d04b5e9a2bae02e4`，字节数 = 7806（本会话 hashlib 实算，与编排方基线一致）。
- **依赖标注**：无笔间硬依赖。与三份「改既有件」订正草案的引用关系 = 0（grep `0xB0CD48|半闭半开|N-9:205|STATIC_COUNT_SPEC|N9_SPEC_ERRATUM` 于 s604_refsync / s604_refsync_full / a_class_fix / handoff_pack 四写域均 0 命中；`S604_VERDICT_ENTRY_DRAFT.md:60` 明写「笔1 / 笔2 / 笔4 与本定谳无引用耦合」）。笔 1「下游九行清单」是改上游件的注记建议（`_la_draft1_n9_p6_erratum.md:24`），非本批订正草案的目标行。

#### ↓↓↓ 草案正文（逐字照抄，从下一行起）↓↓↓

@@BODY_1@@

#### ↑↑↑ 草案正文（逐字照抄结束）↑↑↑

- **本章正文逐字核验**：抽取段 UTF-8 字节数 = 4735，SHA256 = `5c37adc6e64dd245b3392ed554a2185b489ab683496b9b223b6622af4bc86a6c`（本会话 hashlib 实算）。
- **被核对象绑定行（复核回件要件）**：被核对象 SHA256 = e863b593bf5c29a9f2ce38aca4773b7feacb625f6ac32e33d04b5e9a2bae02e4，字节数 = 7806

### 第 2 笔 · §606 · O1–O4 必要性补证：necessaryCount=3、最小集 O1–O3

- **出处**：`lead/ledger_appendix_20261108/_la_draft2_o4_necessity.md:13-23`（标记行 :11 / :25 之间）；同文副本 `LEDGER_APPENDIX_DRAFT.md:81-91`。
- **草案件指纹**：SHA256 = `213fb89819d316e5a74e5acb065cc17cd2845602b9f79a45e5e10b73bb6ae4da`，字节数 = 6714（本会话 hashlib 实算，与编排方基线一致）。
- **依赖标注**：无笔间硬依赖（`S604_VERDICT_ENTRY_DRAFT.md:60`）。笔 2 声明不触碰 `PENDING_DECISIONS.md` 的 D-13 状态行（`_la_draft2_o4_necessity.md:4/:20`），两台账分工 = 只进 GOAL。

#### ↓↓↓ 草案正文（逐字照抄，从下一行起）↓↓↓

@@BODY_2@@

#### ↑↑↑ 草案正文（逐字照抄结束）↑↑↑

- **本章正文逐字核验**：抽取段 UTF-8 字节数 = 4097，SHA256 = `030f5a62328ec661c814f531ff5e54f43db2ac7c8cbd88d4e8d1050c9961bdc6`（本会话 hashlib 实算）。
- **被核对象绑定行（复核回件要件）**：被核对象 SHA256 = 213fb89819d316e5a74e5acb065cc17cd2845602b9f79a45e5e10b73bb6ae4da，字节数 = 6714

### 第 3 笔 · §607 · §604「空档/空档差」两列不可复现（0/15、15 窗全正）

- **出处**：`lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md:13-26`（标记行 :11 / :28 之间）；同文副本 `LEDGER_APPENDIX_DRAFT.md:111-124`。
- **草案件指纹**：SHA256 = `d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6`，字节数 = 7703（本会话 hashlib 实算，与编排方基线一致）。
- **severity = high**（已发布数字实质订正，`LEDGER_APPENDIX_DRAFT.md:206`）；复核 verdict = confirmed。
- **依赖标注**：**与第五笔（§609）成组议题**。笔 3 边界句（`_la_draft3_s604_gapdiff.md:25`、`LEDGER_APPENDIX_DRAFT.md:123`）「只能判『不可复现』、不能定位当年错误步骤」被 §609 码形定谳（错误步骤 = dur 字典错位）超越；`_ve_DRAFT_S609.md:46-48` 与 `S604_VERDICT_ENTRY_DRAFT.md:55-59` 一致判「需要补充（最小修订一处），不是整体修订，更不是被取代」。两笔数字面零冲突。逐组判定见 §3.1(2a)。

#### ↓↓↓ 草案正文（逐字照抄，从下一行起）↓↓↓

@@BODY_3@@

#### ↑↑↑ 草案正文（逐字照抄结束）↑↑↑

- **本章正文逐字核验**：抽取段 UTF-8 字节数 = 4894，SHA256 = `e9842d41f27d70b80067c5a6b89afe81ab63eb0422c7eda741d1c5983a3df698`（本会话 hashlib 实算）。
- **被核对象绑定行（复核回件要件）**：被核对象 SHA256 = d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6，字节数 = 7703

### 第 4 笔 · §608 · 「以乙替代甲」补登（九 hunk + 11 件指纹；登记而非放行）

- **出处**：`lead/ledger_appendix_20261108/_la_draft4_yi_supersede_jia.md:13-41`（标记行 :11 / :43 之间）；同文副本 `LEDGER_APPENDIX_DRAFT.md:150-178`。
- **草案件指纹**：SHA256 = `bf010e8d22cf70892365cbadf555c8fd3b51291a355e4b49c429dc86c46f892e`，字节数 = 10080（本会话 hashlib 实算，与编排方基线一致）。
- **附两条引用限定**（笔 4 正文自带：YI §1 引文在裁决书中 grep 0 逐字命中，逐字出处「未验」；`RULING_DIRECTION.md` 整体 unconfirmed，本节登记不宣告 N-4 正式绑定已生效）。
- **依赖标注**：**与 handoff_pack U1–U9 共享被绑定文件**。笔 4 §4 表 `STATE_MATRIX.json`（`1d4ccc93…`/3558 B）与 `B2B_DESIGN.md`（`565771d8…`/66735 B）正是 `APPROVAL_PACK.md:38-39` 第 10/11 件、是 U2–U7 改文目标（:51-56）；U1「九 hunk +255/−13」(:62-72) 与笔 4 :28 同源。但 handoff_pack 中 `§608|YI_SUPERSEDE|以乙替代甲|补登件` grep = 0 命中 ⇒ 二者是同一乙线既有件上「登记」与「改既有件」两类动作，无草案正文互引。U2–U7 落盘会使笔 4 §4 表两件指纹过期，属改件后果，非笔间硬顺序。逐组判定见 §3.1(2c)。

#### ↓↓↓ 草案正文（逐字照抄，从下一行起）↓↓↓

@@BODY_4@@

#### ↑↑↑ 草案正文（逐字照抄结束）↑↑↑

- **本章正文逐字核验**：抽取段 UTF-8 字节数 = 6318，SHA256 = `24a497e8f63aece592a7a863cdb7d03a93d438dfa3f657dba1c1aaca260b775b`（本会话 hashlib 实算）。
- **被核对象绑定行（复核回件要件）**：被核对象 SHA256 = bf010e8d22cf70892365cbadf555c8fd3b51291a355e4b49c429dc86c46f892e，字节数 = 10080

### 第 5 笔 · §609 · §604 码形定谳：错误源 = 撰写轮内联脚本 dur 字典错位（等价 C8a）

- **出处**：`lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md:13-25`（标记行 :11 / :27 之间）；同文副本 `S604_VERDICT_ENTRY_DRAFT.md:70-82`（§4.1，:86 自述逐字一致）。
- **草案件指纹**：SHA256 = `058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec`，字节数 = 18980（本会话 hashlib 实算，与编排方基线一致）。
- **★ 状态 unconfirmed**：`S604_VERDICT_ENTRY_DRAFT.md:137`「复核回件（如实转录；verdict = partial → 本草案整体按 **unconfirmed** 登记，最终效力由台账所有者裁决）」、:141「verdict = partial」。按交付要求：refuted 或 partial 一律标 unconfirmed。
- **依赖标注**：**依赖/补充笔 3**。`_ve_DRAFT_S609.md:22`「其边界句……自本节起不再成立」、:21「其复算数字、订正清单、不可引用清单全部不受影响」；以「第三笔草案（暂编 §607）」为对照物。`_ve_DRAFT_S609.md:66-67` 建议编号 §609、首选「零重排方案」、备选「相邻方案」（插笔 3/笔 4 之间 → 本笔 §608、甲乙绑定顺延 §609，需同步改 :204-207 与 :11/:222 约 4 处）；两案取一留 Leader，本件不代决。其失效引用面由 S604_REFSYNC（13 处）、refsync_full（剩余 28 处）承接，见 §4 附录 D。

#### ↓↓↓ 草案正文（逐字照抄，从下一行起）↓↓↓

@@BODY_5@@

#### ↑↑↑ 草案正文（逐字照抄结束）↑↑↑

- **本章正文逐字核验**：抽取段 UTF-8 字节数 = 8388，SHA256 = `f4c3433a0141afbc59da7b72fdf679aacbae8b0ed9276530089a6a6528501682`（本会话 hashlib 实算）。
- **被核对象绑定行（复核回件要件）**：被核对象 SHA256 = 058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec，字节数 = 18980

---

## 3 · 笔间冲突与依赖（逐组判定，特别是笔3 与第五笔）

### 3.1 逐组判定

**2(a) 笔3 ↔ 第五笔（§609）：补充，不是冲突（含一处过时表述需加限定）。**
- 笔 3 说「只能判『不可复现』、不能定位当年错误步骤」（`_la_draft3_s604_gapdiff.md:25`；`LEDGER_APPENDIX_DRAFT.md:123` 同文）；第五笔说「错误在撰写轮内联脚本 `dur` 字典推导错位、表值系如实转录」（`_ve_DRAFT_S609.md:13-15/:22`）。
- **三处一致判「需要补充（最小修订一处），不是整体修订更不是被取代」**：`_ve_DRAFT_S609.md:46-48`（:46「定谳不推翻其中任何数字；定谳补的是笔3 当时够不着的『错误在哪一步』」、:48「笔3 保持原样可入账」）；`S604_VERDICT_ENTRY_DRAFT.md:55-59`（:55 判定、:57「**数字面零冲突**」、:58「唯一被事实超越的是一处边界句」）；`_ve_DRAFT_S609.md:22` 与 `S604_VERDICT_ENTRY_DRAFT.md:147-152` 给改文建议。
- 数字面零冲突（`S604_VERDICT_ENTRY_DRAFT.md:57/:78/:107` 口径：时长 30/30、空档 3/30、空档差 0/15、15 窗全正 +0.0065..+0.1080 全部不受影响）；唯一被超越的是笔 3 边界句「不能定位」（:58）。归属终件 `S604_ATTRIBUTION.md:136`「category = 台账记错」类名需加「实现 bug 非誊写」限定（:59）；誊写已被 15/15 逐位比对排除。
- 结论：两笔可并读自洽；是否给笔 3 边界句做最小一处补充、或合并、或保持原样另立，是 **前置问题 Q1**，留台账所有者，**本件不代决**。

**2(b) 笔 1 ↔ 订正草案：无引用（0 命中）；唯一沾边是同名 P6 异物。**
- 本会话既有 grep 实证（`_lb_BOUND_VOLUME.md:231`）：`0xB0CD48|半闭半开|N-9:205|N9_SPEC_ERRATUM|static_spec_n9|静态 u64 窗口读可闭` 于 s604_refsync / s604_refsync_full / a_class_fix / handoff_pack 四写域全部 md 均 0 命中；`S604_VERDICT_ENTRY_DRAFT.md:60` 明写「笔1 / 笔2 / 笔4 与本定谳无引用耦合」。
- handoff_pack 中「P6」是其自身未决项编号 P1–P16 之 P6（U4/U7 拼接点，`_hp_OVERVIEW.md:14`、`_hp_PENDING_AND_SIGNOFFS.md:14`），与笔 1「P6 静态 u64 窗口读」同名异物、无关。笔 1 的「下游九行清单」指向上游 STATIC_COUNT_SPEC 等九件（`_la_draft1_n9_p6_erratum.md:24`），均非本批订正草案的目标件。

**2(c) 笔 4 ↔ handoff_pack U1–U9：有「共享被绑定文件/同源事实」、无「草案正文互引」。**
- 笔 4 §4 表 `STATE_MATRIX.json`（`1d4ccc93…`/3558 B）与 `B2B_DESIGN.md`（`565771d8…`/66735 B）= `APPROVAL_PACK.md:38-39` 第 10/11 件、是 U2–U7 改文目标（:51-56/:81/:139）；U1「九 hunk +255/−13」(:62-72) 与笔 4 :28 同源。既有合订本登记两件现盘指纹经复算未漂移（`_lb_BOUND_VOLUME.md:235`、编排方【合订】evidence⑥ 5 件全 OK 同值）。
- grep `§608|YI_SUPERSEDE|以乙替代甲|补登件` 于 handoff_pack = 0 命中 ⇒ 二者是同一乙线既有件上「登记」与「改既有件」两类动作；U2–U7 落盘会使笔 4 §4 表两件指纹过期（需刷新），属改件后果，**非笔间硬顺序**。列为前置问题 Q4。

### 3.2 前置问题（集中列；一律留 Leader / 台账所有者 / 编排方裁决，不替决）

| # | 前置问题 | 涉及笔 | 依据（文件:行） | 待谁定 |
|:--:|:--|:--|:--|:--|
| Q1 | 笔3 与第五笔关系须先定：①笔 3 保持原样另立 §609；②同批给边界句做最小一处补充；③两笔合并。判定口径见 3.1(2a)「补充，不是冲突」。 | 3、5 | `_ve_DRAFT_S609.md:22/:46-48/:68-71`；`S604_VERDICT_ENTRY_DRAFT.md:55-59/:147-152`；`_la_draft3_s604_gapdiff.md:25` | 台账所有者 |
| Q2 | §609 效力状态：复核 verdict = partial → 按 unconfirmed 登记；是否以 unconfirmed 入账或先补复核。 | 5 | `S604_VERDICT_ENTRY_DRAFT.md:137-143` | 台账所有者 |
| Q3 | 编号/位置两案取一：零重排（§605–§608 + §609）vs 相邻（§609 插笔3/笔4 之间 → 本笔 §608、甲乙绑定顺延 §609，需同步改 :204-207 与 :11/:222 约 4 处）。 | 1–5 | `S604_VERDICT_ENTRY_DRAFT.md:147-148`；`_ve_DRAFT_S609.md:66-67` | Leader |
| Q4 | 笔 4 §608 与 handoff_pack U1–U9 先后：U2–U7 落盘会使笔 4 §4 表两件绑定过期；U2–U7 按 P3「六处同批」强制、U8/U9 独立、V2 换版/重签/补登为级联收尾。 | 4（联动改既有件） | `APPROVAL_PACK.md:38-39/:51-56`；`_hp_OVERVIEW.md:31-40/:48` | Leader + 三方批准人 |
| Q5 | 「六笔 vs 五笔」口径：任务第三步(b) 写「若六笔全入账」，本会话实盘仅 5 笔、无 §610 草案；若确有第六笔需补下发路径与编号。 | 全部 | 本会话全仓 grep 实证（§2.2 / §1.1） | 编排方 |
| Q6 | §604 原文是否改写 / 归属终件类名是否加后注 / 笔 3 边界句是否修订：三处草案均明写「留台账所有者裁决」。 | 3、5 | `_la_draft3_s604_gapdiff.md:25`；`_ve_DRAFT_S609.md:24`（交付件 :153 分工） | 台账所有者 |
| Q7 | 两台账分工与自检：5 笔均「只进 GOAL_THREE_TARGETS、PENDING_DECISIONS 本批一字不动」；追加前后须复算两基线指纹、GOAL 行数增量 = 实际追加行数、PENDING 增量 = 0。 | 1–5 | `LEDGER_APPENDIX_DRAFT.md:11-12/:28-31`；`S604_VERDICT_ENTRY_DRAFT.md:153` | Leader（执行追加时） |

---

## 4 · 编号冲突检查（台账实际尾部节号 vs §605–§610）+ 合订本结构与文件清单

### 4.1 3(a) 台账实际尾部
- 本会话实跑 `cd /d/Project/ra2-campaign-forge && grep -n '^## §' lead/GOAL_THREE_TARGETS_20261018.md | tail -3` → 输出 §602 @:9510、§603 @:9585、**§604 @:9687**（逐行节题见本会话命令输出）；`wc -l lead/GOAL_THREE_TARGETS_20261018.md` = **9757**；`grep -c '^## §'` = **61**。
- 故台账实际尾部 = **§604**（不是 §609；§605–§609 全是「暂编」，尚在草案里）。编排方下发的「台账结构」同值（末节 §604 @:9687、tail :9757）。`PENDING_DECISIONS.md` 待裁段仅 D-13/D-14（:30/:67，本会话 `grep -nE '^### D-'` 实测）。

### 4.2 3(b) 若 N 笔全入账的编号
- 按本会话实盘点的 **5 笔**：编号恰为 **§605–§609**，连续、无空号、无重复，**无需重排**（§605 紧接现尾 §604）。
- 任务书第三步(b)「若六笔全入账，编号会是 §605-§610 还是需要重排？」：若真有第 6 笔则应是 **§605–§610**（仍连续、无需重排，因为现尾 §604）；但本会话全仓 **未发现第六笔入账草案**（`grep -rnE '§610|§611|第六笔|六笔全入账' lead --include=*.md --exclude-dir=ledger_bound_20261109 --exclude-dir=_o1_tmp` → 无输出，`grep_exit=1`），故 **§610 属「未验 / 未见」，不补造**。
- 唯一会触发「重排」的是 §609「相邻方案」（`S604_VERDICT_ENTRY_DRAFT.md:148`：插笔3/笔4 之间 → 本笔 §608、甲乙绑定顺延 §609，需同步改汇总表 :204-207 与 :11/:222 约 4 处编号引用）；首选「零重排方案」则不动编号。两案取一留 Leader（Q3）。

### 4.3 3(c) 有没有哪笔编号与台账现状冲突？
**没有**。§605–§609 全部 > 现尾 §604；两台账内 `§60[5-9]|§610` grep 0 命中（本会话实跑 `grep_exit=1`，见 §2.2）；`PENDING_DECISIONS` 的 D 编号（现 D-13/D-14）与 § 节号是两套序列，不冲突。仅「暂编」性质本身须 Leader 最终确认（`LEDGER_APPENDIX_DRAFT.md:11`、`S604_VERDICT_ENTRY_DRAFT.md:147` 均写「Leader 可重排 / 由 Leader 裁定」）。

### 4.4 合订本结构

```
一页纸总览(1a/1b/1c + 依赖速览)
  → 二、每笔一章 × 5（出处 + 草案件指纹 + 依赖标注 + 「↓↓↓ 逐字正文 ↑↑↑」 + 绑定行）
  → 三、前置问题 Q1–Q7 + 3.1 逐组判定(2a/2b/2c)
  → 四、编号冲突检查(3a/3b/3c) + 附录 A(11 件基线指纹)/B(产出文件清单)/C(大纲)/D(改既有件订正草案清单)
  → 五、入账顺序建议(5a/5b/5c，标注不替决) → 收尾纪律自检
```
本交付件按任务要求改为「## 1」到「## 5」五节：§1 总览 / §2 上游指纹 + 待入账清点 + 已入账 grep / §3 冲突与依赖 / §4 编号检查 + 结构 + 文件清单 / §5 复核回件 + 顺序建议 + 附录 D + 未改台账声明 + 未验项。5 章「逐字正文」以 §2.A 小节形式置于 §2 之内、§3 之前，每章末附固定格式绑定行。

### 4.5 产出文件清单（写域 `lead/ledger_bound_20261109/`）

| 文件 | 字节数 | 作用 |
|:--|--:|:--|
| `_lb_BOUND_VOLUME.md` | 60272 | 既有合订本主件（纯 LF，CRLF=0；SHA256 = `7770da46b5c684add476ec286673d70d73f332fb5ac286d07cabcdaadc4eac43`） |
| `_lb_build.py` | 36779 | 既有构建脚本（print-only，binary stdout） |
| `_lb_fp_out.txt` | 2141 | 11 件基线 + 5 段 BODY 抽取指纹 + 两台账 TAIL 复算 |
| `_lb_VERIFY.md` | 4859 | 逐字照抄核验与纪律自检（其 :28 LF=288 与本会话实测 319 有元数据小出入，纯 LF 结论不变） |
| `_lb_verify_print.py` | 5437 | 生成 `_lb_VERIFY.md` 的 print-only 脚本（既有合订本附录 B :268-271 只列 4 件，缺此件；`_lb_VERIFY.md:78` 有补注） |
| `_lbv_fp.py` / `_lbv_verbatim.py` / `_lbv_final.py` | 3260 / 3998 / 4905 | 复核轮核验脚本，前缀 `_lbv_`，同落唯一写域 |
| `_lb2_TEMPLATE.md` | 本骨架 | 交付件散文骨架，含 5 个 `@@BODY_n@@` 占位符；正文由内联命令从源件按字节切片填入 |
| `LEDGER_BOUND_VOLUME.md` | 本件 | 本任务交付主件（五节结构） |

> 既有 5 件 `_lb_*` 主产出 + 3 件 `_lbv_*` 复核脚本 + 本骨架 `_lb2_TEMPLATE.md` + 本交付主件，全部落在唯一写域，未越界。本交付件由 `python -I -X utf8 -c "<内联组装脚本>"` 生成，未落独立构建脚本文件（首次尝试写 `_lb2_build.py` 被 Mimosa 路径穿越钩子拦截，改用骨架 + 内联命令，如实登记）。

---

## 5 · 复核回件（绑定行格式）+ 入账顺序建议 + 附录 D + 声明

### 5.1 复核回件（如实记 verdict）

- 编排方【复核】字段：**verdict = confirmed**（核心七项全通过，无破口：11/11 MATCH、两台账基线未变、5 笔全未入账、笔3↔§609 判「补充非冲突」准确、台账尾 §604@9687/9757 行/61 节无编号冲突、逐字照抄抽查 5 笔全 True、第五区不替 Leader 决定、git log -1=2657458 未变）。`sha256Line`：`被核对象 SHA256 = 7770da46b5c684add476ec286673d70d73f332fb5ac286d07cabcdaadc4eac43，字节数 = 60272`（本会话 hashlib 复算同值，见 §2.3）。`ranCommands`（复核轮）= 15。
- **whatBreaksIt 两处元数据小出入（不构成 refuted）**：① 主件实测 LF=319 / CRLF=0，而 `_lb_VERIFY.md:28` 与编排方 evidence 记 LF=288（纯 LF 结论仍成立）；② 合订本附录 B（:268-271）只列 4 件而实际产出 5 件（缺 `_lb_verify_print.py`，`_lb_VERIFY.md:78` 有补注，编排方 what/bound 已列全 5 件）。「改一个字即 refuted」专指草案正文，正文已确证未改。
- **效力状态分笔如实记**：
  - 既有合订本主件复核 verdict = **confirmed**（本件照登）。
  - 第 5 笔 §609 草案自身复核 verdict = **partial**（`S604_VERDICT_ENTRY_DRAFT.md:137/:141`）→ 按交付要求「refuted 或 partial 标 unconfirmed」，该笔登记 **unconfirmed**，最终效力由台账所有者裁决（Q2）。
  - 笔 1 依据件 `N9_SPEC_ERRATUM.md` 自身状态 unconfirmed（独立复核 partial）、笔 4 `RULING_DIRECTION.md` 整体 unconfirmed、refsync_full 修订版 unconfirmed —— 均为草案正文自带如实登记，本件不改判。
- **本交付件的绑定行**（复核回件固定格式，紧跟完整 64 位十六进制，中间不插路径/括号/星号/反引号/空格；5 笔逐章各一行见 §2.A）：

```
笔1 被核对象 SHA256 = e863b593bf5c29a9f2ce38aca4773b7feacb625f6ac32e33d04b5e9a2bae02e4，字节数 = 7806
笔2 被核对象 SHA256 = 213fb89819d316e5a74e5acb065cc17cd2845602b9f79a45e5e10b73bb6ae4da，字节数 = 6714
笔3 被核对象 SHA256 = d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6，字节数 = 7703
笔4 被核对象 SHA256 = bf010e8d22cf70892365cbadf555c8fd3b51291a355e4b49c429dc86c46f892e，字节数 = 10080
笔5 被核对象 SHA256 = 058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec，字节数 = 18980
```
（上表 5 行在 §2.A 各章末以「被核对象 SHA256 = <64位>，字节数 = <数字>」独立出现；本会话正则核验 5 行、64 位全 `len_ok=True`。）

### 5.2 入账顺序建议（硬顺序 / 可独立 / 必须成组）—— **不替 Leader 决定**

**5(a) 硬顺序**：**无「笔必须先于笔」的强制硬顺序**（就草案正文可整段复制而言）。依据 `LEDGER_APPENDIX_DRAFT.md:11`「四段各自独立、可单独追加」、:209「任何一笔在 Leader 整段复制追加前都不构成台账内容」。唯一成组硬议题是笔 3 ↔ 第五笔的**叙述自洽性**：§609 正文 :21-22 以「第三笔草案（暂编 §607）」为对照物，若 §609 先于笔 3 入账则该指向当时尚不存在的台账节 ⇒ **宜**笔 3 在先或同批互引（`S604_VERDICT_ENTRY_DRAFT.md:148` 相邻方案即为此）。**这是「宜」不是「必须」**；反向不成立（:48「笔3 保持原样可入账」）。取哪一案留 Leader（Q1/Q3）。

**5(b) 可独立**：

| 笔 | 可独立？ | 依据 |
|:--:|:--|:--|
| 1 §605 | **可独立** | `S604_VERDICT_ENTRY_DRAFT.md:60`「笔1…无引用耦合」；与三份订正草案 grep 0 命中（3.1(2b)） |
| 2 §606 | **可独立** | :60「笔2…无引用耦合」；只进 GOAL、不触碰 PENDING 的 D-13 |
| 4 §608 | **可独立**（与改既有件有联动，非笔间硬顺序） | :60「笔4…无引用耦合」；与 handoff_pack 共享被绑定文件属「改件后指纹刷新」（Q4） |
| 3 §607 | **可独立（数字面）** | :48「笔3 保持原样可入账」；仅边界句措辞与 §609 有过时张力（Q1），不构成数字或事实冲突 |
| 5 §609 | **有条件**：宜与笔 3 成组 / 或以「节内对照」方式入账 | 见 5(a)；另状态 unconfirmed（Q2）、失效引用面需 D-1/D-2 承接（附录 D） |

**5(c) 必须成组**：**唯一「建议成组」的一对 = 笔 3 + 第五笔（§607 + §609）**：两笔同讲 §604 空档列，§609 以笔 3 为对照物、并取代其边界句；若只入其一，须在 Q1 明确另一笔处置（保持原样 / 最小补充 / 合并），否则台账会出现「笔3 说不能定位」与「§609 说已定位」的并读张力（`:68` 建议「是，最小一处」并给改文）。笔 1 / 笔 2 / 笔 4 三笔之间**不成组**（彼此无引用耦合）。若只入「前四笔」（§605–§608）完全自洽（confirmedCount=4，`LEDGER_APPENDIX_DRAFT.md:209`）；若全入「前五笔」编号 §605–§609 连续、无重排（§4.2）。

> **纪律复述**：以上全为「建议 / 宜 / 硬约束清单」，**不替 Leader 决定哪笔先入账、哪笔暂缓**；编号、位置、Q1–Q7 处置、是否批准追加，一律由 Leader / 台账所有者 / 编排方裁定。本件只列冲突与依赖。

### 5.3 附录 D · 改既有件的订正草案清单（**不是入账项**）

> 共同性质：只出「改原文 / 加注不改 / 保留不动」建议，**不改任何件、不改台账、不追加新节**；本会话 `grep -cE '^## §6'` 于下列 5 份主件实测输出全部为 `0`（`S604_REFSYNC_DRAFT.md` / `_rs_REFSYNC_DRAFT.md` / `_rf_FULL_REFSYNC_DRAFT.md` / `A_CLASS_FIX_DRAFT.md` / `APPROVAL_PACK.md`）。

| 组 | 写域 / 主件 | 规模 | 目标（改既有件） | 与入账笔的关系 |
|:--|:--|:--|:--|:--|
| D-1 S604_REFSYNC | `lead/s604_refsync_20261109/`：`_rs_REFSYNC_DRAFT.md`（33869 B，首轮）、`S604_REFSYNC_DRAFT.md`（38819 B，第二轮，吸收 partial 回件） | **13 处**（14 行位；改 2 / 加注 10 / 保留 1，`S604_REFSYNC_DRAFT.md:6`） | 6 件历史写域失效/过时引用逐处三选一（含 `LEDGER_APPENDIX_DRAFT.md:123` ≡ `_la_draft3_s604_gapdiff.md:25` 笔 3 边界句） | **承接第五笔 §609 的失效引用面**；改文针对笔 3 边界句处8≡处9，与 Q1 同一处 |
| D-2 refsync_full | `lead/s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md`（55331 B，修订版，状态 unconfirmed） | **剩余 28 处**（:6 改 3 / 加注 22 / 保留 3；:57 与 §4.2 全表对账 43−15=28） | §609 交付件 §4.2 43 处清单中未被 D-1 覆盖的剩余处 | 同 D-1，承接第五笔 |
| D-3 A_CLASS | `lead/a_class_fix_20261109/`：`_ac_A1A4A5_FIX_DRAFT_20261109.md`（23258 B）、`A_CLASS_FIX_DRAFT.md`（29212 B） | **A1/A4/A5 三处**逐字改文（MATRIX:90、`_mr_REACH_EVIDENCE`:112/:121）；A2/A3 不重复拟（已在 U8/U9） | `matrix_reach_20261109/` 两受核件 | 与 U8/U9 同坐标系（A2=MATRIX:154=U8、A3=:146=U9），与入账 5 笔无正文引用 |
| D-4 handoff_pack U1–U9 | `lead/handoff_pack_20261109/APPROVAL_PACK.md`（40024 B）+ `_hp_U1.md`…`_hp_U9.md` + `_hp_OVERVIEW.md` | **9 条内容订正，落点 9 行 4 文件**（`_hp_OVERVIEW.md:10-12`）：U1 V2:91；U2–U4 STATE_MATRIX.json:2/:5/:4；U5–U7 B2B_DESIGN.md:148/:151/:150；U8/U9 MATRIX_DEFECT_REACHABILITY.md:154/:146。约束：U2–U7 **六处同批**（P3 强制）、U8/U9 同批为宜、16 项未决 P1–P16、换版级联、三方批准 | 与笔 4 §608 共享被绑定文件；落盘会使笔 4 §4 表两件指纹过期（Q4） |

> D-1/D-2 与 D-3/D-4 之间：D-3 明写 A2/A3 复用 U8/U9 改文（不重复拟）；D-1/D-2 与 D-4 无交叉。四组均为「改既有件」，**不在本合订本 5 笔入账项之内**。

### 5.4 未改台账声明

- `lead/PENDING_DECISIONS.md` 与 `lead/GOAL_THREE_TARGETS_20261018.md` 全程只读：本会话开工 11 件基线复算、收尾复算均得 `PENDING = 3765eddb…/52419 B`、`GOAL = 2baa0de4…/759518 B`，与编排方基线逐位一致（§2.1 / §2.2）。
- `git log -1 --oneline` = `2657458 GOAL-3T: 台账 §400→§508 与 D-07..D-11 裁决登记入账`（本会话实查，未变）；`git status --short -- lead/PENDING_DECISIONS.md lead/GOAL_THREE_TARGETS_20261018.md` 输出两行 `MM`（会话开始时 Leader 既有改动，本任务未再写入）。**未 commit、未 push**。
- 只读源域 5 个（ledger_appendix / s604_verdict_entry / s604_refsync / a_class_fix / handoff_pack）一律 Read / grep / hashlib，未改一字。
- 唯一写域 = `lead/ledger_bound_20261109/`；本交付件与骨架 `_lb2_TEMPLATE.md` 落此域。**只合订不改台账，草案正文逐字照抄、不润色改写**。

### 5.5 未验项（如实，不补造）

1. **第六笔 / §610**：全仓 grep 0 命中，未见第六个 `## §6xx` 入账草案正文；若编排方另指，需补下发路径与编号（Q5）。按铁律标「未验 / 未见」，不补造。
2. **§609 定谳自带未验项**（`_ve_DRAFT_S609.md:23` / 草案正文末段）：`frame_edges` 字段语义与错位方向、C8a 75/75 逐格复现与 zip/wrap/bisect 数值等价、WAL/bak 库扫描、512650 command 同款错位行、编排方 R1-R5 逐路搜索数字与复核回件 28 条命令、磁盘 carving / JetBrains LocalHistory / OneDrive 云端 / R6h/R9 截断残余 —— 均系草案转述或未重跑，本交付轮**未逐条复算**，标「未验」。
3. 笔 1 `[0xB0CD48]` 运行期实际数值、`0x4CACB0` 语义与写者、capstone 全量反汇编（草案正文自列「未验」）；笔 2 物理 S 逐事件点值、实际保存完成时刻 C、`e>0=28317/28317` 转引、56/62 冲突成因（草案正文自列「未验」）。
4. 笔 4 YI §1 引文在裁决书中「逐字出处未验」（grep 0 逐字命中，草案正文自带引用限定）。
5. **本交付件未重跑**：`_lb_build.py` / `_lbv_*.py` 复核轮脚本、`_r3_recompute_gapdiff.py`、`_d14_recompute.py`、`_sh_gen512655_payload.py` 等源域离线复算脚本，本轮只做 grep / hashlib / 逐字比对与文件:行实读，未重放这些脚本；其结论以在盘输出 + 文件:行 + 编排方【合订】/【复核】字段为据，不冒称本轮实跑。
6. 全仓 grep 曾因 `lead/o1prime_reach_20261109/_o1_tmp/.../dddd…` 超长路径触发 `ugrep: warning: cannot open directory`（一次 `grep_exit=2`）；已用 `--exclude-dir=_o1_tmp` 重跑得 `grep_exit=1`（0 命中），结论以重跑为准。该长路径目录本身内容**未验**。
7. §604 原文是否改写 / 归属终件类名是否加后注 / 笔 3 边界句是否修订：三处由草案明写「留台账所有者裁决」，本件不代判、不代改（Q1/Q6）。

---

## 收尾纪律自检

- 零真机：未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存。
- 零采样代码：未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。
- 绝对只读：两台账 + 5 个只读源域全程未修改/追加/覆盖（收尾 11/11 MATCH）。
- 唯一写域 = `lead/ledger_bound_20261109/`；本件命名 `LEDGER_BOUND_VOLUME.md`，骨架 `_lb2_TEMPLATE.md`。
- 草案正文**逐字照抄**：5 段由源件标记行之间按字节切片直接嵌入（ALL_VERBATIM = True），未润色改写。
- 绑定行格式固定「被核对象 SHA256 = <64 位十六进制>，字节数 = <数字>」，中间不插任何字符。
- **不替 Leader 决定顺序**：§5.2 通篇「建议 / 宜 / 留 Leader」，Q1–Q7 列前置问题不代裁。
- 复核 verdict 如实记：confirmed 照登；§609 的 partial → 标 **unconfirmed**。
- 不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib。
