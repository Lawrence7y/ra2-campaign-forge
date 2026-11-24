# MERGED_CONSUMER_AUDIT.md — merged 形态消费方审计（只审计不改）

日期：2026-11-09　撰写：消费方审计撰写员（动态工作流独立上下文）
唯一写域：`lead/merged_consumer_audit_20261109/`（本件为该域内新增件；`_mcf_scan.py` / `_mcf_scan_out.txt` 亦为本会话该域内新增）
被核对象：`lead/r33e_merge_20261109/_re_linked.py`（产出 `merged` 的并入版实现，绝对只读）
上游材料 = 任务给定【编排方指纹】【扫描】【审计】【复核】四段；本会话对其关键结论做了独立实跑/实读复核，凡本会话未跑者一律标「未验」。

**复核 verdict 如实登记：任务给定【复核】`verdict = partial`（`ranCommands = 42`），非 confirmed，故本报告整体结论标 `unconfirmed`（不允许写成 fully-confirmed）。** `partial` 的五项打破理由见 §5 复核回件与 §2/§3 的修正列。

必现要素落点：`merged` / `path=None` / `match=True` / `KeyError` / `消费方` / `已存在` / `未来` / `六条适配` / `最小安全集` / `未改任何件` / `未验` —— 全文均有，且逐件给出「遇 merged 会怎样」。

---

## 1 目的与边界（只审计不改）

**目的**：以 `merged` 形态（`tier=SAMEDOC_LINK_EQ`、`match=True`、`path=None`、缺 `verified_path/recomputed/bytes`、单对象信息只在 `members`）为输入，核实六条适配要求、独立重扫潜在消费方、逐件判「崩 / 误读 / 正常」、严格区分「已存在的消费方」与「未来的消费方」、评六条落地难度，并给出接入建议与最小安全集。

**边界（铁律，本会话遵守）**：
- **只审计不改**：未改 `_re_linked.py`、未改 `r11_scan_plus`（`_f2_r11plus.py`）、未改任何消费方、未改两件台账；编排方指定的五个绝对只读目录（`r33e_merge_20261109/`、`samedoc_link_20261109/`、`r11_f2_fix_20261109/`、`gate_fp7_20261108/`、`gate_r9r12_20261109/`）及「本任务扫描的全部件」一律只读。证据：本会话首/末两次 `python -I -X utf8 -B -c` 用 `hashlib` 对九件全字节复算均输出 `ALL_NINE_MATCH True` / `ALL_READONLY_UNCHANGED True`（§2、§5）。
- **零真机**：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存。**零采样代码**：未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。
- **不 commit、不 push**：本会话 `git log -1 --format='%H %s'` = `26574589aa8401e8f3f2934680a1ea7109bafa2d GOAL-3T: 台账 §400→§508 与 D-07..D-11 裁决登记入账`（与会话开始一致）；`git status --porcelain -- lead/merged_consumer_audit_20261109/` = `?? lead/merged_consumer_audit_20261109/`。
- Python 一律 `python -I -X utf8 -B` + 绝对路径（`-B` 阻只读目录生成 `__pycache__`，本会话脚本内亦设 `sys.dont_write_bytecode=True`）；指纹用 `hashlib.sha256`。全部遍历带剪枝与深度上限（§3 实跑 `_mcf_scan.py`：`prunedItems=389 depthCap=6`，另有 §5 无深度上限的 `--exclude-dir` 剪枝交叉）。
- **未改任何件声明**：见 §5 末节，含九件指纹、`find -newermt` 新增 `.pyc` = 0、`r33e/__pycache__` = `ABSENT`、HEAD 未变。

**「已存在的消费方」与「未来的消费方」的定义（本任务铁律）**：前者 = 现盘真的在调 `link()` / `link_triple()` 并读其返回值的件，会真的遇到 `merged`；后者 = 只有把 `merged` 接进 `_f2_r11plus.py:303-305` 之后才会收到 `merged rec` 的下游 r11 消费件，今天只是「应该知道」。**前者 severity 高**（若会崩）**；后者 severity 低一档**。本会话实查：已存在 16 件全为测试/复核/探针且无一崩；唯一实证会崩的 `_f2v_verify9.py` 属未来接入面 ⇒ 最终 `severity = medium`（与【审计】一致，【复核】未推翻）。

---

## 2 上游指纹（九件）+ 六条适配要求复核

### 2.1 九件指纹（本会话实跑）

命令（会话首与会话末各一次，均为 `python -I -X utf8 -B -c "import hashlib,os; ... hashlib.sha256(open(...,'rb').read()).hexdigest() ..."` 逐件对比任务给定【编排方指纹】）：
输出（首次）：9 行 `MATCH <path> <sha256> <bytes>` + `ALL_NINE_MATCH True`；末次：`ALL_READONLY_UNCHANGED True` / `COUNT 9`（§5 复录）。九件逐一全等：

| # | 件 | SHA256（本会话 hashlib 实算 = 编排方给定） | 字节数 |
|--:|:--|:--|--:|
| 1 | `lead/r33e_merge_20261109/_re_linked.py` | `7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52` | 19481 |
| 2 | `lead/r33e_merge_20261109/_re_NOTES.md` | `388fe53e7636c61bbd981133229f6b4239ff9e771e4e2d69a54925edaa27d7c2` | 7804 |
| 3 | `lead/r33e_merge_20261109/R33E_MERGE.md` | `7f204882c0985e2708bd01110d720dec4aeaea47da37590462f15934d44a79c9` | 26435 |
| 4 | `lead/samedoc_link_20261109/_sl_link.py` | `a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5` | 12475 |
| 5 | `lead/r11_f2_fix_20261109/_f2_r11plus.py` | `83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75` | 15723 |
| 6 | `lead/gate_fp7_20261108/_g7_predicates.py` | `02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120` | 11743 |
| 7 | `lead/gate_r9r12_20261109/_g9_gate.py` | `a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6` | 11623 |
| 8 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 |
| 9 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 |

绑定行（固定格式，见 §5）：被核对象 SHA256 = 7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52，字节数 = 19481

### 2.2 六条适配要求复核（来源与归类）

来源 = 本会话 Read 全文实读 `_re_NOTES.md:59-76` 与 `R33E_MERGE.md:162-171`（§5.3 照录同一清单），与任务给定【审计】`adaptations` 六项一一对应。两件一致。归类按「**消费方须遵守** vs **实现方要做**」分开：

| # | 六条（原文要旨，落点 `:行`） | 归类 | 实现侧现状（本会话实读） |
|--:|:--|:--|:--|
| 1 | **tier 枚举扩展**：新值 `SAMEDOC_LINK_EQ`；下游若对 tier 值集封闭须显式加分支，`tier=SAMEDOC_LINK_EQ` + `path=None` 是合法组合，不得当异常（`_re_NOTES.md:63-65`） | **消费方须遵守**（下游加分支）；前半产新值由实现方做 | 已做：`_re_linked.py:311-312` 三元 + `:326` merged 重赋 |
| 2 | **不假设 `match=True ⇒ 有单一 path`**：merged rec 无 `verified_path/recomputed/bytes`，假设者会 `KeyError`/误读，**必须走 `members`**（`:66-67`） | **消费方须遵守**（最核心、最危险） | 已做：`_re_linked.py:320-329` merged 分支不写三键、只赋 `members`/`decl_lines` |
| 3 | **problems 契约不变**：联查恒不产 problem，只把返回 warnings 并入 r11 的 warnings（`:68`） | **消费方须遵守**（只并 warnings，不碰 problems） | 已做：`_re_linked.py:47` docstring、`:177-179` `problems: []`、`:330` 返回 `r["problems"]` 恒空 |
| 4 | **hash 重算复用（可选）**：给 `link()` 加 recompute 注入，复用 r11 的 `recompute` 闭包，避免重复 IO（`:69-70`） | **实现方要做**（改 `link()` 签名 + 闭包），可选纯优化 | 未做且无需做：`_re_linked.py:171` 签名无该参数、`:198` 自读盘；`_f2_r11plus.py:144-147` 已有闭包 |
| 5 | **merged 事件逐次记档**：每次 merged 落 run 机读件 `{binding_hex, bytes_decl, members, decl_lines, decl_text}`，等价类是联查时刻快照（TOCTOU 同限）（`:71-73`） | **实现/接入方要做**（新增落盘件） | 数据源现成：`_re_linked.py:276-281` `out["eq"]` 已含 `members`/`decl_lines`/`decl_hits`；`main()` `:334-348` 只 `print`，不落盘 |
| 6 | **判定书登记**：J4 是对 `SAMEDOC_LINK.md:20` ★4「唯一命中才采」的显式修订，并入台账须写明修订关系，不能无声替换（`:74-76`） | **治理方要做**（文字/台账登记，不可省） | 本会话 `SAMEDOC_LINK.md:20` 实读仍为「≥2 个不同现盘文件同 hash → 放弃采集，不任选其一」；两件台账本任务绝对只读，未改 |

**接入点（本会话实读）**：`_f2_r11plus.py:303-305` 的 `else` 分支 = `rec["tier"] = None` + `warnings.append("绑定行缺显式路径，需人工锚定（R11/R3-3b）")`，`:306 bindings.append(rec)`；`_f2_r11plus.py:139` 是 `def r11_scan_plus(...)` 定义行、`:143-147` 装 `_g7_predicates.py` 并自造 `recompute` 闭包。命令 `grep -nE "link_triple|_re_linked|_sl_link|import" lead/r11_f2_fix_20261109/_f2_r11plus.py` 输出仅 `:45-48` 标准库 + `:70,72` 装载 `_g7_predicates.py`，**无任何 link 家族调用**。`R33E_MERGE.md:17,180` 明写「未接入生产」。

**tier 封闭白名单实查（本会话实跑）**：`grep -rnE "tier.*(not in|in \(|in \[|in \{)|assert.*tier|bad.*tier|unknown.*tier|ALLOWED_TIER|TIERS\s*=" lead/r11_f2_fix_20261109/ lead/gate_r9r12_20261109/ lead/gate_fp7_20261108/ --include="*.py"` → 仅 2 处非校验命中（`_f2_r11plus.py:213` 列表构造、`:260` `if tier not in first_resolved` 是内部 dict 去重），**无封闭 tier 白名单**；开放 dict 见 `_f2v_final.py:55-58`、`_f2w_dogfood.py:27-30`。故第 1 条此刻无实害。

---

## 3 潜在消费方逐件表（文件 / 读什么字段 / 遇 merged 会崩、误读、正常）

### 3.1 独立重扫（本会话实跑，带剪枝 + 深度上限）

命令：`python -I -X utf8 -B "D:/Project/ra2-campaign-forge/lead/merged_consumer_audit_20261109/_mcf_scan.py" > ".../_mcf_scan_out.txt"`（脚本内 `PRUNE={__pycache__,.git,.mimosa,node_modules,.tmp,.venv,venv,site-packages,.pytest_cache,dist,build}`、`DEPTH_CAP=6`、`MAX_BYTES=400000`、`sys.dont_write_bytecode=True`）。首跑因我脚本 §(d) 把 `bytessub`（int 列表）误当元组解包，`EXIT=1` 并打印 49 行；修正一行后复跑 `EXIT=0`，254 行（如实登记，笔误不影响 (a)-(c) 结论）。

输出（`_mcf_scan_out.txt:1-42`）：`SCAN_STATS dirsVisited=2862 scannedPy=5568 prunedItems=389 depthCap=6 maxBytes=400000`、`CANDIDATE_ROWS=396`、**`COUNT(a)=16`**、**`COUNT(r11plus_callers)=8`**、**`COUNT(r11_scan_only)=7`**。

- **修正 1（采纳【复核】）**：真实 `link()`/`link_triple()` 调用方 = **16 件**，不是【审计】的 17 件。`_re_struct_diff.py` 全文实读 `:3,12,31,32,51`：只对 `_re_linked.py` 与 `_sl_link.py` 做 `difflib` 文本白名单比对，无任何 `link()`/`link_triple()` 调用、不读返回值 ⇒ 不是消费方。
- **修正 2（采纳【复核】）**：`_g9_gate.py:155` 实读 = `g7.r11_scan(text, d_dir, root=root)`；命令 `grep -n "r11_scan_plus" lead/gate_r9r12_20261109/_g9_gate.py` → `GREP_EXIT=1`（NO_MATCH）。其余 `r11_scan`-only 件同理（`:86` `_g9v_verify.py`、`_gv_pred_check.py:44,103,107`、`_g7_reverse_validate.py:69,104,107,110`、`_f2v_context.py:24`、`_f2_repro.py:46`）。**把 `link_triple` 接进 `r11_scan_plus` 不改 `g7.r11_scan`，merged rec 永不流入这些门禁件**；【审计】把 `_g9_gate.py` 列为「次高·静默误读·安全语义最危险」不可达，撤下。
- **修正 3（采纳【复核】）**：【审计】漏掉 3 个真正读 `r11_scan_plus` 产出 JSON 的下游件：`_f2_compare.py:100` 写 `_f2_compare_out.json` 的 `plus.bindings`，随后 `_f2w_checks.py:27-35`、`_f2w_pass.py:15,17`、`_f2w_final.py:31-33` 读它。本会话 `grep -rn "_f2_compare_out.json" lead/r11_f2_fix_20261109/*.py` 证实写者=`:17`、读者=这 3 件（加 `_f2w_extract.py:13`）。
- **修正 4（采纳【复核】）**：「0 件读 `rec['verified_path']`」须加限定——字符串在 4 个 RE+SL 件出现，逐行实读全是**缺席断言**而非字段读：`_re_parity_extra.py:181`、`_re_run10_diff.py:137`、`_rev_cases.py:263,311,336`、`_rev_edge25.py:108` 均为 `not ({"verified_path","recomputed","bytes"} & set(rec))`。结论实质正确，措辞修正为「0 件读取该字段，4 件做缺席断言」。
- **交叉（无深度上限、带 `--exclude-dir` 剪枝）**：`grep -rln --include="*.py" "r11_scan_plus(" . --exclude-dir=...` → 8 件，与 `_mcf_scan.py` §(b) 完全一致；`grep -rn --include="*.py" "link_triple(" . ...` → 17 个命中行（比 depthCap 更宽，只会多不会少）。**说明**：`depthCap=6` 的具体数字（`dirsVisited=2862 scannedPy=5568`）是本会话自己的口径，与【审计】的 `762/1902`、【复核】的 `7040/10955`（`_mcv_danger2.py`，depthCap=8）不同，三者均如实登记，不互相冒充。

### 3.2 真实 merged rec 形状（本会话实跑）

命令：`python -I -X utf8 -B "D:/Project/ra2-campaign-forge/lead/merged_consumer_audit_20261109/_mcv_empirical.py"`（复核件，本会话重跑；脚本 `:17-25` 只读载入 `_re_linked.py`、在既有 `Ffull_merged` 夹具上产真 rec）。输出：`link verdict = merged`、`tier = SAMEDOC_LINK_EQ`、`match = True`、`path = None`、`keys = ['decl_lines','declared','match','members','path','samedoc_link','tier']`、`has verified_path/recomputed/bytes = False/False/False`、`members_n = 2`、`decl_lines = [4]`、`problems = []`；`TOTAL_TRIALS=11 CRASH_COUNT=3`：`[A _f2v_verify9.py:21-29] CRASH -> TypeError: ... not 'NoneType'`、`[A2 :24] CRASH -> TypeError`、**`[A3 :29 src['bytes']] CRASH -> KeyError: 'bytes'`**；`[Z walk members] OK -> [(True,True),(True,True)]`。即「走 `members` = 正常」有实证。

### 3.3 A 表：**已存在的消费方**（现盘真调 `link()`/`link_triple()`，会真的遇到 `merged`）

`COUNT(a)=16`。7 件装 `_re_linked.py`（今天就能收到 `merged`）；9 件装 `_sl_link.py` 原件（结构上不产 `merged`，`_sl_link.py:224-238`）；1 件间接。**逐件「遇 merged 会怎样」**：

| # | 文件（相对仓库根） | 读什么字段 | 遇 merged 会怎样 | 依据（本会话实读/实跑） |
|--:|:--|:--|:--|:--|
| A1 | `r33e/_re_j4_cases.py` | `recm["tier"]/["match"]/["path"]`、`members`、`decl_lines`、warning | **正常**——正是六条第 2 条的正确落地范例：断言 `tier=="SAMEDOC_LINK_EQ" and match is True and path is None and len(members)==2` | `:111-114` 实读 |
| A2 | `r33e/_re_parity_extra.py` | `recm["tier"]/["match"]/["path"]`、`members_n`、`:181` 三键缺席断言 | **正常**——形状核验 + members 全列 + 缺席断言 | `:84-90`、`:181` 实读 |
| A3 | `r33e/_re_run10_diff.py` | `trip["t3"]["merged"]["tier"/"match"/"path"]`、`members_n`、`:137` 缺席断言 | **正常**——`triple_t3_merged_shape` 显式断言 `path is None` | `:130-146` 实读 |
| A4 | `r33e/_rev_cases.py` | `rec3["tier"]/["match"]/["path"]`、`sorted(keys)`、`:336` 缺席断言 | **正常**——`item3_members2_disciplines` 断言 `path is None` 且三键不在 rec | `:326-339`、`:263,311,336` 实读 |
| A5 | `r33e/_rev_core.py` | `recm["tier"]`、`recm["path"]`、`members_n`、`decl_lines`、`reverify` | **正常**——只做形状记录/双跑比对，`.get` 取值不假设单一 path | `:190-197` 实读 |
| A6 | `r33e/_rev_edge25.py` | `recm["tier"]/["path"]/["match"]`、`sorted(keys)`、`:108` 缺席断言 | **正常**——25 成员夹具下 `path is None` 断言成立 | `:92-100`、`:108` 实读 |
| A7 | `equiv/_eq_proto.py` | `res["verdict"]`、`anchors[].path`、自产 `eq.members`（`:79` 把 verdict 改 `"merged"`） | **正常**——J4 原型自己造 merged 形状，`eq_merge` 有 `verdict!="multi"` 守卫（`:77` 区）；不消费 `link_triple` 的 rec | `:77-103` 实读 |
| A8 | `equiv/_eq_surface_probe.py` | `_r["verdict"]`、`_m["verdict"]`（间接 `P.SL.link`） | **正常**——同上，只数 verdict；若换装载版最多计数变化 = 误读但不崩 | `_mcv_linkcalls.txt:4-6`、`:15,24,33` |
| A9 | `equiv/_eqv_adv.py` | `res["verdict"]`、`.get("anchors")` | **正常（现状）**——装 SL 原件，不产 merged；若换装载版则 `=="multi"` 断言失败 = **误读但不崩**（全 `.get`/字符串） | `_mcv_linkcalls.txt:7`、`:76` |
| A10 | `equiv/_eqv_close.py` | 同 A9 | **正常（现状）**；换装载版 = 误读不崩 | `:79` |
| A11 | `equiv/_eqv_j1.py` | `res["verdict"]` | **正常（现状）**；换装载版 = 误读不崩 | `:39` |
| A12 | `samedoc/_sl_run10.py` | `r["verdict"]`、`anchors[].path`、`reverify["path"/"bytes"]`（带 `if rec["reverify"]` 守卫） | **正常**——SL 原件不产 merged；守卫在 merged（`reverify=None`）时跳过，不崩 | `:83`、`:85,118-122`（本会话借【审计】§2(b) 实读记录；未逐行重读，标「据回件」） |
| A13 | `samedoc/_slv_run10copy.py` | 同 A12 | **正常**——同上 | `:83`、`:85,118-122`（据回件） |
| A14 | `samedoc/_sl_selftest.py` | `r["verdict"]`、`anchors[].path`、`reverify["path"]`（带守卫） | **正常**——同上 | `_mcv_linkcalls.txt:47-54`（8 个调用） |
| A15 | `samedoc/_slv_multitest.py` | `r["verdict"]`、`anchors[].path`、`rec.get("path"/"match"/"tier")` | **正常（现状）**——`:66` 是原 multi 的 `rec.get("path") is None and rec.get("match") is None` 正确断言；换装载版 merged 时该断言失败 = **误读但不崩**（全 `.get`） | `:60-70` 实读 |
| A16 | `samedoc/_slw_fix4.py` | `r["verdict"]`、`anchors[0]["path"]`、`reverify["sha"/"bytes"]`（`verdict=="unique"` 守卫） | **正常**——`reverify` 只在 unique 分支读，merged 不进 | `_mcv_linkcalls.txt:65-70`、`:104-110`（据回件 `:112-117`） |

**A 表结论**：16 件全部是测试/复核/探针，**没有一件遇 `merged` 会崩**；7 件 RE+SL 恰恰是六条第 2 条的正确落地范例。按任务铁律「已存在的消费方会真的崩 ⇒ severity 高」，此处无 high 触发条件。

**非消费方（如实排除）**：`r33e/_re_struct_diff.py`（`:12,26-28,49-54` 只做 `difflib` 文本比对，不调 `link`）、`r33e/_re_fp_check.py`、`equiv/_eqv_fp.py`、`samedoc/_slw_hashes.py`、`_slv_hashes.py`、`_slv_count10.py` —— 仅指纹/哈希/计数，不读 `link_triple` 返回的 binding rec ⇒ 不计入 (a)。

### 3.4 B 表：**未来的消费方**（接入 `r11_scan_plus` 后才新增的消费面）

`_mcf_scan_out.txt:23-32`：**8 件直接调 `r11_scan_plus`**（`_f2_compare.py:42`、`_f2_selftest.py:64,75,117,126,130,141`、`_f2v_edge.py:36,43,48,77`、`_f2v_final.py:24,50`、`_f2v_run.py:35`、`_f2v_verify9.py:19`、`_f2w_dogfood.py:21`，加 `def` 自身 `_f2_r11plus.py:139`）。另 4 件读 `_f2_compare.py:100` 写出的 `_f2_compare_out.json`（`_f2w_checks.py:14`、`_f2w_pass.py:6`、`_f2w_final.py:31`、`_f2w_extract.py:13`）。**逐件「遇 merged 会怎样」**（`_mcv_empirical.py` 本会话重跑给出 trial 值）：

| # | 文件 | 读什么字段 | 遇 merged 会怎样 | 依据 |
|--:|:--|:--|:--|:--|
| B1 | `r11/_f2v_verify9.py` | `:21` `if b.get("match") is not True: continue` → `:24` `Path(src.get("verified_path") or src.get("path"))` → `:29` `src["bytes"]`、`:34` | **崩**（唯一实证）：`match=True` 放行 → `Path(None)` `TypeError: argument should be a str or an os.PathLike object ... not 'NoneType'`（trial A/A2）；绕过 `Path` 后 `:29` **`KeyError: 'bytes'`**（trial A3）。**正是六条第 2 条点名的禁式** | `:21-34` 全文实读 + `_mcv_empirical.py` `CRASH_COUNT=3` |
| B2 | `r11/_f2w_checks.py` | `:28` `b.get("match") is True` → `:29` `(b.get("recomputed") or "").lower() == b["declared"].lower()`，缺 `recomputed` | **误读（静默）**：`sha_ok=False`（trial B = `False`），把合法的 `match=True` 记成「sha 逐字不一致」；不崩（全 `.get`） | `:24-38` 实读；【复核】指出【审计】漏列 |
| B3 | `r11/_f2w_pass.py` | `:15,17` `sum(1 for b in ... if b.get("match") is True)` 计数 | **误读（静默）**：merged 被计入 `plus match` 但非单一回验路径，`PASS`/`match` 统计口径混杂；不崩 | `:10-24` 实读；【复核】指出漏列 |
| B4 | `r11/_f2w_final.py` | `:31-33` 只数 `len(r["plus"]["warnings"])` | **正常**——只数 warnings，不读 binding 单对象字段 | `:30-34` 实读；【复核】判「正常」一致 |
| B5 | `r11/_f2_selftest.py` | `:110` `nb[0].get("verified_path","").endswith("_f2_r11plus.py")` | **误读**：返回 `False`（trial C），S4 断言失败；不崩（`.get` 默认 `""`） | `:105-111` 实读 |
| B6 | `r11/_f2_compare.py` | `:49-50` `ob["path"]` / `nb["path"]` 断言、`:67-69` `plus_path`/`plus_match` 计数、`:100` 写 JSON | **误读**：trial D = `(0,1)`（`plus_path=0` 但 `plus_match=1`）；`:50` 的 assert 仅当 orig 有 path 才触发，R3-3b 行不触发 ⇒ 不崩 | `:35-69`、`:100-103` 实读 |
| B7 | `r11/_f2v_final.py` | `:54` `collected=sum(1 if b.get("path"))`、`:57-58` 开放 `tiers[b.get("tier")]` | **误读**：trial F = `(0, 1, {'SAMEDOC_LINK_EQ': 1})`（collected=0 但 match=1）；tier dict 开放不崩 | `:45-59` 实读 |
| B8 | `r11/_f2v_run.py` | `:48-52` `plus_paths`/`plus_match`/`plus_tiers` 列表化 | **误读**：`plus_paths=[None]`、`plus_match=[True]`；不崩 | `:40-64` 实读 |
| B9 | `r11/_f2w_dogfood.py` | `:25-26` `collected`/`match` 计数、`:27-30` 开放 `tiers` | **误读**：同 B7；不崩 | `:20-33` 实读 |
| B10 | `r11/_f2w_extract.py` | `:26-33` 全 `.get("verified_path"/"recomputed"/"bytes"/"path"/"match")` | **误读（静默）**：trial G = `('', '', '-', None, 'SAMEDOC_LINK_EQ', True)`，`verified=`/`recomputed=`/`bytes=-` 报告静默空白；不崩 | `:1-33` 全文实读 |
| B11 | `r11/_f2v_edge.py` | `:38-39` `.get("tier")/.get("match")/.get("suffix_stripped")`、`:48-51` problems/warnings | **正常**——不假设单一 path，只用 `.get` 打印 | `:34-52` 实读 |
| B12 | `r11/_f2v_context.py` | `:24` 调 `g7.r11_scan`（**原版**，非 plus）、`:30` `b["path"]` 打印 | **正常 / 不可达**——属 `r11_scan`-only 组，plus 接入不流入；原版 rec 自带 `path` | `:20-34` 实读 |
| B13 | `r11/_f2_repro.py` | `:46` 调 `g7.r11_scan`（原版）、`:49` `b["declared"],b["path"],b["match"]` | **正常 / 不可达**——同上，原版 rec；trial H 手工喂 merged 仍返回 tuple 不崩（merged 含三键） | `:43-52` 实读 |
| B14 | `gate_r9r12/_g9_gate.py` | `:155` `g7.r11_scan`（原版）、`:157-160` `reverified`/`n_match`/`r11_verdict` | **不可达**（本次修正）：`grep -n "r11_scan_plus" _g9_gate.py` = `GREP_EXIT=1`；trial E 手工喂 merged 得 `(0,1,'PASS')` 只是**假设值**，非接入后真实流向。【审计】「门禁静默放过」撤下，改列「未来的消费方·不可达，但应知道：若将来把门禁改接 plus，则 `n_match=1/reverified=0/problems=[] ⇒ PASS` 会成为真实静默误读」 | `:150-166` 实读 + `GREP_EXIT=1` |
| B15 | `gate_r9r12/_g9v_verify.py`、`gate_fp7/_gv_pred_check.py`、`_g7_reverse_validate.py`、`_doc_ast_align_check.py` | 调 `g7.r11_scan`（原版）比对 problems/hits | **正常 / 不可达**——`r11_scan`-only 组（`_mcf_scan_out.txt:35-42`），不消费 plus 的 merged rec | `_mcf_scan_out.txt:35-42` |
| B16 | `gate_fp7/_g7_predicates.py` | 自产 `rec["match"]/["recomputed"]/["bytes"]`（`:192-218`） | **正常 / 不可达**——原版谓词，不产 merged；`problems` 契约不变 | `_mcf_scan_out.txt:35`（`:157` 调 r11_scan） |

**B 表计数（修正后）**：可达的「未来的消费方」= 8 件直接 `r11_scan_plus` 调用方（去掉 `def` 自身为 7 件）+ 4 件 JSON 读者（B2/B3/B4/B10，其中 B6 已计）⇒ **11 件可达件**：**1 崩**（B1）、**8 静默误读**（B2/B3/B5/B6/B7/B8/B9/B10）、**1 正常**（B4）、B11 正常。**不可达但应知道** = B12/B13/B14/B15/B16（7 件 `r11_scan`-only）。【审计】的「14+ 件、7 误读」计数**不可直接采信**（双向不准：塞入不可达件、漏 B2/B3/B4），本表已纠正。

### 3.5 已存在 vs 未来的区分与 severity

- **已存在的消费方 = 16 件**（§3.3）：全部测试/复核/探针，7 件正确断言 `path=None`、**无一崩** ⇒ 不触发 high。
- **未来的消费方 = 11 件可达 + 7 件不可达但应知道**（§3.4）：唯一实证会崩的 `B1 _f2v_verify9.py` 在这个面；今天它调的 `r11_scan_plus` **不产 merged**（`_f2_r11plus.py:303-305` 空置 + 无 link 装载），故 `merged` 收不到它。
- 生产核实（本会话实跑）：`grep -nE "link_triple|_re_linked|samedoc|\bsl_link\b|import .*link|\blink\(" lead/r11_f2_fix_20261109/_f2_r11plus.py` → 无 link 家族命中；`grep -nE "^import |^from |spec_from_file_location|exec_module|sys.path" ...` → 仅 `:45-48` 标准库 + `:70,72` 装 `_g7_predicates.py`。**当下零生产崩溃面**。
- ⇒ **severity = medium**（与【审计】一致，【复核】未推翻）。若编排方实施接入而未先修 §5 最小安全集，`B1` 立即变为「已存在的消费方会崩」⇒ 升 **high**。

---

## 4 六条适配逐条评估（改什么 / 难度 / 不改的后果）+ 最高风险消费方

### 4.1 六条逐条

| # | 改什么（文件:行） | 难度 | 不改的后果 |
|--:|:--|:--|:--|
| 1 tier 枚举加分支 | 实现侧已做（`_re_linked.py:311-312,326`）；**消费方待做**：接入时 `_f2_r11plus.py:303-305` 把 `rec["tier"]` 置 `SAMEDOC_LINK_EQ`（不得留 `None`），未来任何封闭枚举处加分支 | **加分支（低-中）** | 现盘无封闭白名单（§2.2 实跑）⇒ 当下无实害；未来下游若写封闭枚举 `(None/T1/T2/T2N/T3/SAMEDOC_LINK)`，新 tier 被当异常/丢弃 → 漏判或 KeyError |
| 2 不假设 `match⇒path` / 走 `members` | 修 `B1 _f2v_verify9.py:24`（`Path(...)`）、`:29/:34`（`src["bytes"]`）、`B5 _f2_selftest.py:110`、`B2 _f2w_checks.py:29`；接入合并处显式分支 `if tier=="SAMEDOC_LINK_EQ": 走 rec["members"]`，**不写** `verified_path/recomputed/bytes` | **加分支 + 改契约（中-高，六条最实质）** | **崩**（`TypeError: Path(None)` + **`KeyError` `'bytes'`，`_mcv_empirical.py` 实证）；或**误读**（B2/B3/B5/B6/B7/B8/B9/B10 的 `(0,1)` / `sha_ok=False` / `verified=-` 静默空白）；B14 式「匹配但无回验路径 ⇒ PASS」纪律风险（当前不可达） |
| 3 problems 契约不变 | 实现侧已做（`_re_linked.py:47,177-179,330`）；**消费方待做**：`_f2_r11plus.py:303-305` 只把 `link_triple` 的 `warnings` 并入 `warnings`，**不得**把 merged warning 塞进 `problems` | **加分支（低）** | merged warning 静默丢失（人工看不到副本群提示）；或误升级 problem → 门禁把合法 warning 判 FAIL（违反「一律 warning 级」`_re_NOTES.md:28`） |
| 4 recompute 注入 | `_re_linked.py:171` `link()` 签名加 `recompute=None`、`:198` `hit.read_bytes()` 改走闭包；复用 `_f2_r11plus.py:144-147` | **改契约（中，可选纯优化）** | 仅重复 IO（同文件被 r11 与 link 各读一次 sha256）；**语义零风险**，`_re_NOTES.md:70` 明写「语义不变，纯优化」 |
| 5 run 快照 | 接入方新增落盘：每次 merged 落 `{binding_hex, bytes_decl, members, decl_lines, decl_text}`；数据源现成 `_re_linked.py:276-281` | **加分支 + 新写件（中）** | 等价类是联查时刻快照，事后无法追溯「当时」成员与声明行原文；成员漂移/声明行被改后不可追溯（TOCTOU 同限，`_re_NOTES.md:72-73`） |
| 6 显式修订声明 | 治理方：`SAMEDOC_LINK.md:20` ★4「唯一命中才采」→「声明解析 → merged｜multi」的修订关系写入台账（两件台账本任务绝对只读，**只登记不改**） | **文字说明（低，但不可省）** | 判据来源不可追溯；未来复核会把 merged 误当原规则的自然推论，绕过 J4 三条件与封闭集禁扩纪律（`_re_NOTES.md:74-76,80`） |

### 4.2 最高风险消费方

- **第一（唯一实证会崩）**：`lead/r11_f2_fix_20261109/_f2v_verify9.py:21-29` —— 六条第 2 条点名的「`match=True ⇒ 有单一 path`」禁式。本会话 Read 全文 + `_mcv_empirical.py` 实跑：`TypeError: Path(None)` 与 `KeyError: 'bytes'`。**属未来的消费方**（调 `r11_scan_plus`，生产未接入）⇒ severity `medium` 而非 high；接入后立刻升 high。
- **第二（静默误读、可达面中最危险）**：`lead/r11_f2_fix_20261109/_f2w_checks.py:27-35` —— `sha_ok=False`（trial B），把合法 `match=True` 记成逐字不一致；且【审计】原表**漏列**，由【复核】补出。`lead/r11_f2_fix_20261109/_f2_compare.py:67-69` 的 `(0,1)` 与 `_f2v_final.py:54-58` / `_f2w_dogfood.py:25-30` 的 `collected=0,match=1` 同属静默误读簇。
- **撤下（不可达）**：`lead/gate_r9r12_20261109/_g9_gate.py:155-166` —— 【审计】称「次高·门禁静默 PASS」；本会话 `grep -n "r11_scan_plus" _g9_gate.py` = `GREP_EXIT=1`、`:155` 实读为 `g7.r11_scan`，**merged rec 不流入**。trial E 的 `(0,1,'PASS')` 是手工喂 rec 的假设值，非接入后真实流向。保留为「未来的消费方·不可达，但应知道」（若门禁将来改接 plus 则风险成立）。

---

## 5 复核回件 + 接入建议与最小安全集 + 未改任何件声明 + 未验项

### 5.1 复核回件（如实记 verdict，含绑定行）

任务给定【复核】：`verdict = partial`、`ranCommands = 42`、`sha256Line` = 下列绑定行。**因 `partial` 非 confirmed，本报告整体结论标 `unconfirmed`**（`refuted` 或 `partial` 标 `unconfirmed`）。复核独立通过项：九件指纹首/末两次 `ALL_NINE_MATCH = True`；危险模式（3 处静态粗筛命中逐行实读均为正确 `path is None` 断言 = 误报）；未把测试说成生产（`grep -rl "_re_linked"` = 8 件、`comm -12` 交集仅 producer 自身、`:303-305` 空置）；越界检查（5 个只读目录 `-newermt 10:11` 新增/改动 = 0、新增 `.pyc` = 0、`r33e/__pycache__` = ABSENT、两件台账 mtime 未变、`git log -1` 未变）；六条与封闭 tier 白名单实查。复核打破 fully-confirmed 的 5 项：① `_g9_gate.py` 数据流不可达；② 漏 3 个 `_f2_compare_out.json` 读者；③ `(a)=17` 应为 16；④ `verified_path` 是缺席断言须加限定；⑤ 「不接也能用」缺 owner/SOP（操作性缺口，非方案证伪）。本会话对 ①–④ 全部独立复核并采纳修正（§3.1、§3.4），对 ⑤ 补了本会话实跑（见 §5.3）。

绑定行（固定格式；本会话 `python -I -X utf8 -B -c` 用 `hashlib` 对 `_re_linked.py` 全字节实算，首/末两次全等）：

被核对象 SHA256 = 7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52，字节数 = 19481

### 5.2 接入建议与最小安全集

**最小安全集（最小改动）** = 下列 1–3（代码必做）+ 5–6（治理/审计必做）；第 4 条可选。接入点唯一：`lead/r11_f2_fix_20261109/_f2_r11plus.py:303-305` 的 `else`。

1. **调用与合并**（六条 1/3）：在该 else 分支调 `RE.link_triple(text, doc_dir, declared, bytes_decl, root)`；返回 `warnings` 并入 `warnings`、`problems`（恒 `[]`）丢弃；把 `tier="SAMEDOC_LINK_EQ"`、`match=True`、`path=None`、`members`、`decl_lines`、`samedoc_link` 合并进 `rec`，**绝不写** `verified_path/recomputed/bytes`。保留原 R3-3b warning 或替换为 merged warning，二选一须显式、不得两者都丢。
2. **消费方去假设**（六条 2，最关键）：修 `B1 _f2v_verify9.py:24,29,34`、`B2 _f2w_checks.py:29`、`B5 _f2_selftest.py:110`；统一约定 **`tier=="SAMEDOC_LINK_EQ"` 时走 `rec["members"]` 逐成员重算**（`_mcv_empirical.py` trial Z 实证 `[(True,True),(True,True)]`），不取 `rec["path"]`/`verified_path`/`bytes`。B3/B6/B7/B8/B9/B10 的 `match`/`path` 计数口径须显式区分「merged 匹配 ≠ 单一回验」。B14 `_g9_gate.py:157-158` 若将来改接 plus，须裁决「`match=True` 但 `reverified=0` 是否允许 PASS」，**不得默认放过**。
3. **tier 显式标注**（六条 1）：新增代码不得引入封闭枚举；现盘无封闭枚举（§2.2 实跑）。
4. （可选，六条 4）`_re_linked.py:171` 加 `recompute` 注入，复用 `_f2_r11plus.py:144-147` 闭包省一次 IO。
5. **run 快照落盘**（六条 5）：每次 merged 落机读件 `{binding_hex, bytes_decl, members, decl_lines, decl_text}`，取 `eq` 全量 —— 审计可追溯唯一凭据。
6. **判定书登记**（六条 6）：台账写明对 `SAMEDOC_LINK.md:20` ★4 的显式修订。

**接入前不可省略的护栏**：接入会改动 `_f2_r11plus.py`（本会话指纹 `83f8217f…/15723`），接入方须在自己写域内重算指纹并登记；`_re_linked.py` 保持只读（`7ca339c6…/19481`）。

**不接也能用的方式（及本会话核实的操作性缺口）**：
- 离线人工提示模式可行：本会话实跑 `python -I -X utf8 -B "D:/.../_re_linked.py" "D:/.../_re_fixtures/Ffull_merged/doc.md" <hex> <bytes>` → `CLI_verdict=merged`、`CLI_eq_members_n=2`、`CLI_reverify=None`、`CLI_problems=[]`、`CLI_warning_has_pathNone=True`、`CLI_warning_has_noAuthorization=True`。`_re_linked.py:334-348` 的 `main()` 只 `print(json.dumps(...))`，把 merged warning 与 `eq.members` 当人工提示，**不进自动判定、不推导授权**，与纪律 2（`_re_NOTES.md:40-48`）一致。`SAMEDOC_LINK.md:22`「是否接入由编排方裁决」、`R33E_MERGE.md:17`「本报告不自行上线」⇒ 暂不接入是合规现状；代价仅 F2-d 无路径绑定行继续走 R3-3b 人工锚定 warning。
- **但【复核】第 ⑤ 项成立**：本会话 `grep -rniE "负责人|谁看|谁负责|SOP|定期|触发|调度|owner|reviewer|scheduled" lead/r33e_merge_20261109/_re_NOTES.md lead/r33e_merge_20261109/R33E_MERGE.md lead/merged_consumer_audit_20261109/_mc_AUDIT.md` → 无指派复核人；`grep -rn "_re_linked\.py" lead/ --include="*.py" | grep -v r33e_merge_20261109` → 仅本审计写域 3 个脚本提及，全仓 0 个调度者/调用 CLI 的 SOP；`main()` 不落盘、不路由、不告警。**结论**：该模式是「有人手工敲命令才存在」的提示，无 owner / 触发条件 / sink；推荐现状可用，但**须由编排方补一名复核人与触发 SOP**，否则第 5 条 run 快照亦无人产生。此为操作性缺口，非方案证伪。

**接入前必做验证**：
1. 形状断言回归全绿：`_re_j4_cases.py`(19/19)、`_re_run10_diff.py`(20/20)、`_re_parity_extra.py`(21/21)、`_rev_core.py`(92/92)、`_rev_cases.py`(69/69)、`_rev_edge25.py`(7/7)、`_re_struct_diff.py`(STRUCT_OK) —— 记载见 `R33E_MERGE.md:190-204` / `_re_NOTES.md:85-96`。**本会话未重跑这 7 件，标「未验」**，接入方须自行复跑留 EXIT=0 输出。
2. 端到端联调（未验）：构造 F2-d 无路径绑定行，实跑接入后的 `r11_scan_plus`，断言 `tier=="SAMEDOC_LINK_EQ"`、`path is None`、`match is True`、`members` 全列、`problems == []`、warnings 含「禁止由 merged 推导任何授权结论」、unique/zero/invalid_hex/multi 输出与接入前逐字节全等。
3. 下游消费者全量回放：把 merged rec 喂给 §3.4 B 表每一件（尤其 11 件可达件），确认零 `TypeError` / 零 `KeyError` / 无误读计数。本会话 `_mcv_empirical.py` 实跑 11 trials、3 崩均来自 B1，**接入前必须先修 `B1:24` 与 `:29`**。
4. 门禁契约回归：若将来把 `_g9_gate.py` 改接 plus，裁决 `:157-158` 的 `reverified`/`n_match` 口径；`_f2_compare.py:44-46` 的 30 件 `declared` 序列与 `problems` 不得漂移。
5. 指纹护栏：接入前后对 `_re_linked.py`（只读）、`_f2_r11plus.py`（接入方改）、两件台账各算 `hashlib.sha256` 登记；本会话 9/9 全等基线见 §2.1。
6. 纪律复核：封闭集 `DECL_RE` 不得扩词（`_re_NOTES.md:80`）；三条纪律（path=None / 禁授权推论 / members 全列）逐条有断言。

### 5.3 本会话实跑命令与输出（摘录，全部 `python -I -X utf8 -B` / `hashlib`）

1. 九件指纹首/末两次：`ALL_NINE_MATCH True`（9 行 MATCH）；末次 `ALL_READONLY_UNCHANGED True` / `COUNT 9`。
2. `grep -n "r11_scan_plus" lead/gate_r9r12_20261109/_g9_gate.py` → `GREP_EXIT=1`（NO_MATCH）；`grep -n "r11_scan\|reverified\|n_match\|r11_verdict\|r11_problems" ...` → `:155 g7.r11_scan(...)`、`:157-160` 计数、`:166 verdict`。
3. `grep -nE "link_triple|_re_linked|_sl_link|import" lead/r11_f2_fix_20261109/_f2_r11plus.py` → 仅标准库 `:45-48` + 装载 `_g7_predicates.py` `:70,72`；`python -I -X utf8 -B -c`（打印 `:303-306`）→ `rec["tier"]=None` + R3-3b warning + `bindings.append(rec)`。
4. `python -I -X utf8 -B .../ _mcf_scan.py` → 首跑 `EXIT=1`（§(d) 解包笔误，49 行）；修正后 `EXIT=0`、254 行、`dirsVisited=2862 scannedPy=5568 prunedItems=389 depthCap=6 maxBytes=400000`、`COUNT(a)=16`、`COUNT(r11plus_callers)=8`、`COUNT(r11_scan_only)=7`。
5. `python -I -X utf8 -B .../_mcv_empirical.py` → `link verdict=merged`、`tier=SAMEDOC_LINK_EQ`、`match=True`、`path=None`、三键 `False`、`members_n=2`、`problems=[]`、`TOTAL_TRIALS=11 CRASH_COUNT=3`（2×`TypeError` + 1×`KeyError: 'bytes'`）、`Z OK -> [(True, True), (True, True)]`。
6. `grep -rnE "tier.*(not in|in \(|...)"` 三目录 → 仅 `_f2_r11plus.py:213,260` 两处非校验命中；`grep -rn "verified_path"` 于 RE+SL → 6 行全为 `not ({...} & set(rec))` 缺席断言。
7. 无深度上限剪枝交叉：`grep -rln "r11_scan_plus(" . --exclude-dir=...` → 8 件；`grep -rn "link_triple(" . ...` → 17 命中行；`grep -rn "_f2_compare_out.json" lead/r11_f2_fix_20261109/*.py` → 写者 `:17`、4 读者。
8. 离线 CLI：`CLI_verdict=merged`、`CLI_eq_members_n=2`、`CLI_reverify=None`、`CLI_problems=[]`、warning 两纪律 `True`。
9. owner/SOP grep → 无指派；`grep -rn "_re_linked\.py" lead/ | grep -v r33e` → 仅本写域 3 脚本，无调度者。
10. 末次 `git log -1` = `26574589…`；`git status --porcelain -- lead/merged_consumer_audit_20261109/` = `?? lead/merged_consumer_audit_20261109/`；`find <5 只读目录> -name "*.pyc" -newermt "2026-11-09 10:50"` = `0`；`ls -d lead/r33e_merge_20261109/__pycache__` = `ABSENT`。

### 5.4 未改任何件声明

本会话**未修改、未追加、未覆盖**：`_re_linked.py`、`_sl_link.py`、`_f2_r11plus.py`（`r11_scan_plus`）、`r11_scan_plus` 的任何消费方、`gate_fp7_20261108/`、`gate_r9r12_20261109/`、`r33e_merge_20261109/`、`samedoc_link_20261109/`、`PENDING_DECISIONS.md`、`GOAL_THREE_TARGETS_20261018.md`，以及任务给定【扫描】39 命中件。证据 = §2.1 九件首/末 `hashlib` 全等 + 5 只读目录新增/改动文件 0、新增 `.pyc` 0、`r33e/__pycache__` ABSENT、`git log -1` 未变。零真机、零采样代码（未写 hook/MiniDump/SuspendThread/StackWalk/探针注入/动态内存解析，未启动任何游戏进程、未 taskkill、未读活进程内存）。**不 commit、不 push**。唯一写域 `lead/merged_consumer_audit_20261109/`，本会话新增仅 `MERGED_CONSUMER_AUDIT.md`、`_mcf_scan.py`、`_mcf_scan_out.txt`；域内既有的 `_mc_*` / `_mcv_*` 件均为前置会话产物，本会话只读未改。

### 5.5 未验项（如实登记，不补造）

1. **未验**：本会话未重跑 7 个 r33e 回归脚本；只引用 `R33E_MERGE.md:190-204` / `_re_NOTES.md:85-96` 的回件记载。
2. **未验**：`merged` 接入 `r11_scan_plus` 的端到端联调未做（接入点 `:303-305` 仍空置）；`_mcv_empirical.py` 是「手工喂入真实 merged rec」，**不是**接入后的端到端运行。
3. **未验**：343 件全语料 multi 作用面未普查（`R33E_MERGE.md:179` 同限）；TOCTOU 漂移窗口不可实测（`:181`）。
4. **未验**：`depthCap=6` 遍历的具体数字为本会话口径，未独立复现【审计】`762/1902` 与【复核】`7040/10955`；【复核】自记其「全仓两遍遍历」三次 120s 超时被 kill、输出 0 字节，标「未验」。本会话以无深度上限 `--exclude-dir` 剪枝 grep 作交叉，二者不等价。
5. **未验**：B 表中标「据回件」的行（A12/A13/A14 部分字段、A16 内层字段）本会话未逐行重读，引用【审计】§2(b)/(d) 与 `_mcv_linkcalls.txt` 行号；B15/B16 的字段细节未逐行展开。
6. **未验**：`partial` 复核中「未来消费面 owner 缺失」的补正方案（指派谁、触发 SOP）属编排方裁决，本会话只登记缺口不代拟。
7. **如实登记**：`_mcf_scan.py` 首跑 `EXIT=1` 系我脚本 §(d) 解包笔误，修正复跑 `EXIT=0`；`_mc_AUDIT.md` 的 `COUNT(a)=17`、`_g9_gate.py` 门禁 PASS、漏列 3 个 JSON 读者等，均按【复核】`partial` 结论纠正，未冒充本会话新发现之外的独立成果。
