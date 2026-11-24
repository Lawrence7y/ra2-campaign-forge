# _mc_AUDIT.md — merged 形态消费方审计（只读审计，不改任何消费方）

日期：2026-11-09　审计员：消费方审计员·hy4
写域：`lead/merged_consumer_audit_20261109/`（唯一写域，全部产出前缀 `_mc_`）
纪律：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（无 hook/MiniDump/SuspendThread/StackWalk/探针注入/动态内存解析）；只读审计（未改 `_re_linked.py`、未改 `r11_scan_plus`、未改任何消费方、未改任何只读件）；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。

被核对象 SHA256 = 7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52，字节数 = 19481

（上行为本会话 `python -I -X utf8 -c` 用 `hashlib.sha256(open(p,'rb').read())` 对 `lead/r33e_merge_20261109/_re_linked.py` 全字节实算的绑定行；命令与输出见 §0。被核对象 = 产出 merged 形态的并入版实现。）

---

## 0 编排方指纹复核（本会话实跑）

命令：`python -I -X utf8 -c "import hashlib,os; base='D:/Project/ra2-campaign-forge/'; [print(p, hashlib.sha256(open(base+p,'rb').read()).hexdigest(), len(open(base+p,'rb').read())) for p in [...9 件...]]"`

输出（9 件全等编排方实跑指纹）：

```
lead/r33e_merge_20261109/_re_linked.py      7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52 19481
lead/r33e_merge_20261109/_re_NOTES.md       388fe53e7636c61bbd981133229f6b4239ff9e771e4e2d69a54925edaa27d7c2 7804
lead/r33e_merge_20261109/R33E_MERGE.md      7f204882c0985e2708bd01110d720dec4aeaea47da37590462f15934d44a79c9 26435
lead/samedoc_link_20261109/_sl_link.py      a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5 12475
lead/r11_f2_fix_20261109/_f2_r11plus.py    83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75 15723
lead/gate_fp7_20261108/_g7_predicates.py   02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120 11743
lead/gate_r9r12_20261109/_g9_gate.py       a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6 11623
lead/PENDING_DECISIONS.md                  3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 52419
lead/GOAL_THREE_TARGETS_20261018.md        2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede 759518
```

结论：9/9 全等。被核对象绑定行 = 上述 `_re_linked.py` 行。

---

## 1 第一步：六条适配要求逐条核实

来源：`lead/r33e_merge_20261109/_re_NOTES.md:59-76`（本会话 Read 全文实读）、`lead/r33e_merge_20261109/R33E_MERGE.md:162-171`（本会话 Read 全文实读，§5.3 照录同一清单）。两件一致，与任务给定材料「tier 枚举加分支 / 不假设 match⇒path / problems 契约 / recompute 注入 / run 快照 / 显式修订声明」一一对应。

| # | 六条原文（引自 `_re_NOTES.md`） | 落点 | 归类 |
|--:|:--|:--|:--|
| 1 | **tier 枚举扩展**：新值 `SAMEDOC_LINK_EQ`（merged 专用）。下游若对 tier 值集封闭（None/T1/T2/T2N/T3/SAMEDOC_LINK）必须显式加分支；`tier=SAMEDOC_LINK_EQ` 且 `path=None` 是合法组合，不得当异常。 | `:63-65` | **消费方必须遵守**（下游加分支）；前半「产新 tier 值」已由实现方做（`_re_linked.py:311-312,326`） |
| 2 | **path=None 形态适配**：merged rec 无 `verified_path`/`recomputed`/`bytes`——消费方若假设「match=True ⇒ 有单一 path」会 KeyError/误读；**必须走 members**。 | `:66-67` | **消费方必须遵守**（最核心、最危险） |
| 3 | **problems 契约不变**：联查恒不产 problem，只需把返回 warnings 并入 r11 的 warnings。 | `:68` | **消费方必须遵守**（只并 warnings，不碰 problems）；前半「恒 []」已由实现方做（`_re_linked.py:177-179,330`） |
| 4 | **hash 重算复用（可选）**：link() 内部自读盘算 sha256；r11 已有 `recompute` 闭包，如要避免重复 IO 需给 link() 加 recompute 注入参数——语义不变，纯优化。 | `:69-70` | **实现方需要做**（改 `link()` 签名 + 闭包），可选 |
| 5 | **merged 事件逐次记档**（判据 §5.2）：每次 merged 落 run 机读件 `{binding_hex, bytes_decl, members, decl_lines, decl_text}`——等价类是联查时刻快照（TOCTOU 同限），事后审计需要当时成员与声明行。 | `:71-73` | **实现/接入方需要做**（新增落盘件） |
| 6 | **判定书登记**（判据 §5.2）：J4 是对 `SAMEDOC_LINK.md:20` ★4「唯一命中才采」的显式修订（multi 不再无条件放弃，改「声明解析 → merged｜multi」），并入台账时必须写明修订关系，不能无声替换。 | `:74-76` | **实现/治理方需要做**（文档/台账登记，文字说明） |

**接入点**：`lead/r11_f2_fix_20261109/_f2_r11plus.py:303-305` 的 `else` 分支（`_re_NOTES.md:60-62`；本会话 `python -I -X utf8 -c` 打印 :303-310 核实，确为 `rec["tier"] = None` + R3-3b warning + `bindings.append(rec)`，无任何 link 调用）。

**回件明写「未接入生产」**：`R33E_MERGE.md:17`（§1-5「本报告不自行上线：merged 是新增形态，尚未接入 `r11_scan_plus` 生产路径」）、`R33E_MERGE.md:180`（§5.5-2「未验：merged 未接入真实 `r11_scan_plus` 生产路径；本会话只实读 `_f2_r11plus.py:303-305` 与给出适配清单」）。本会话独立核实见 §3。

---

## 2 第二步：潜在消费方扫描（本会话独立重扫）

编排方已扫出 39 命中件（`verified_path/link_triple/r11_scan/_sl_link` 引用，275 目录 / 1304 .py / 0.58s）。本会话**独立再扫一遍**，带剪枝（`__pycache__`/`.git`/`.mimosa`/`node_modules`/`.tmp`）+ 深度上限 6 + 单文件 400 KB 上限：

命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\merged_consumer_audit_20261109\_mc_scan.py`
输出：`dirsVisited=762 scannedPy=1902 prunedItems=177 depthCap=6 maxBytes=400000`（`_mc_count.py` 同口径 `scanned_files=1906`；差异来自两次遍历时本写域新增 `_mc_*.py` 件数）。

逐件明细：`_mc_detail.py` → `_mc_detail_out.txt`（635 行，29 件候选的装载语句/调用行/字段读行/危险窗口）；精确计数：`_mc_count.py`；交叉：`_mc_crosscheck.py`；实证：`_mc_empirical.py`。以上 5 件全部本会话实跑，EXIT=0（除 `_mc_scan.py` 首跑因我自己脚本的键名笔误 `imp_sl`→`imp_sl_link` 报错 1 次，修正后复跑 EXIT=0；笔误与本审计结论无关，如实登记）。

### 2(a) 现盘有多少件会读到 `link()` / `link_triple()` 的返回值？

**答：17 件**（排除 2 个 producer 模块 `_re_linked.py`/`_sl_link.py` 自身，及本审计写域 4 件 `_mc_*.py`；含调用行数 `rows_with_link_call=23`）。依据 `_mc_count.py` 输出 `COUNT(a) = 17`，逐件：

| 装载 | n | 文件 |
|:--|--:|:--|
| RE+SL（装 `_re_linked.py`，**能收到 merged**） | 7 | `lead/r33e_merge_20261109/_re_j4_cases.py`、`_re_parity_extra.py`、`_re_run10_diff.py`、`_re_struct_diff.py`、`_rev_cases.py`、`_rev_core.py`、`_rev_edge25.py` |
| SL-only（装 `_sl_link.py` 原件，**结构上永不产 merged**） | 9 | `lead/equiv_class_20261109/_eq_proto.py`、`_eqv_adv.py`、`_eqv_close.py`、`_eqv_j1.py`；`lead/samedoc_link_20261109/_sl_run10.py`、`_sl_selftest.py`、`_slv_multitest.py`、`_slv_run10copy.py`、`_slw_fix4.py` |
| 间接（经 `_eq_proto.SL.link` 调用） | 1 | `lead/equiv_class_20261109/_eq_surface_probe.py:15,24,33`（`_mc_detail_out.txt:23-35`） |

### 2(b) 其中有多少件会读 `rec['path']` 或 `rec['verified_path']`？

**答：12 件读 `path` 类字段，0 件读 `rec['verified_path']`**（`_mc_count.py` 输出 `COUNT(b)=12`，全部 `read_vp=False`）。但须细分字段归属，否则会高估风险：

- **真正读 `link_triple()` 的 `rec["path"]`（binding_rec 顶层）的 = 7 件**，全在 RE+SL 组，且**全部是正确断言 `path is None`**：
  - `_re_j4_cases.py:113` `recm["match"] is True and recm["path"] is None`（本会话实读 :110-116）
  - `_re_run10_diff.py:133-134,144` `trip["t3"]["merged"]["path"] is None`（本会话实读 :140-146）
  - `_rev_cases.py:193,328,334-336` `rec3["path"] is None`、`not ({"verified_path","recomputed","bytes"} & set(rec3))`（本会话实读 :330-339）
  - `_re_parity_extra.py:88`、`_rev_core.py:194`、`_rev_edge25.py:96`（`_mc_detail_out.txt:346,440,471`）
  - `_slv_multitest.py:66` `rec.get("path") is None`（SL 原件 multi 形态的正确断言）
- **其余 5 件的 `["path"]` 读的是 `out["anchors"][i]["path"]` / `out["reverify"]["path"]` / `members[i]["path"]`，不是 `rec["path"]`**：
  - `_eq_proto.py:83,91,101`（本会话实读 :77-101，`members` 列表与 `raw_anchor_paths`）
  - `_sl_run10.py:85,118-122`、`_slv_run10copy.py:85,118-122`、`_sl_selftest.py:85,117,129,143,149`（`reverify["path"]` 带 `if r["reverify"]` 守卫）
  - `_slw_fix4.py:112-117`（`anchors[0]["path"]`）
- **`rec['verified_path']` 在 (a) 17 件里 = 0 件**。该字段只在未来接入面（r11 消费件）出现，见 §3。

### 2(c) 有没有件在 `match=True` 时假设 path 非空？（最危险模式）

**答：现盘 (a) 17 件里没有；唯一确凿实例在未来接入面，且本会话实证会崩。**

- 静态粗筛（`_mc_count.py` §(c)）在 (a) 内命中 3 件：`_re_j4_cases.py`、`_re_run10_diff.py`、`_rev_cases.py`。**逐行实读确认为误报**——三处都是「`match is True` **且** `path is None`」的**正确断言**（`:113`、`:142-145`、`:334-336`），不是「假设 path 非空」。
- **真实危险模式 = `lead/r11_f2_fix_20261109/_f2v_verify9.py:21-29`**（本会话 Read 全文实读）：
  ```python
  for k, b in enumerate(pb):
      if b.get("match") is not True:      # :21  match=True 才继续
          continue
      src = b.get("alt") or b
      vp = Path(src.get("verified_path") or src.get("path"))   # :24  ← 假设有单一 path
      data = vp.read_bytes()                                     # :25
      ok_bytes = size == src["bytes"]                            # :29  ← 直接下标 bytes
  ```
  本会话 `_mc_empirical.py` 用 `_re_linked.link_triple()` 在既有 `Ffull_merged` 夹具上产出**真实 merged rec**（`tier=SAMEDOC_LINK_EQ, match=True, path=None, keys=['decl_lines','declared','match','members','path','samedoc_link','tier']`, `verified_path/recomputed/bytes` 三键全缺，`members_n=2`），把上式原样套入实跑：
  ```
  [EXCEPTION] A _f2v_verify9.py:21-29 | TypeError: argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'NoneType'
  [EXCEPTION] A' _f2v_verify9.py:24 only | TypeError: ... not 'NoneType'
  CRASH_COUNT=2 / 10
  ```
  即 `Path(None)` 崩；即便绕过 `Path`，`:29 src["bytes"]` 还会 `KeyError`。这是六条第 2 条点名的危险模式的**实证复现**。

### 2(d) 逐件 verdict（文件 / 读什么字段 / 遇 merged 会怎样）

**A. 现盘 (a) 17 件（读 link()/link_triple() 返回值）**

| 文件 | 读什么字段 | 遇 merged | 依据 |
|:--|:--|:--|:--|
| `r33e/_re_j4_cases.py` | `recm["tier"]/["match"]/["path"]`、`.get("members")`、`eq.members[].path` | **正常**（已断言 `tier=SAMEDOC_LINK_EQ`/`path is None`/`match True`/走 members） | `:111-114` 实读 |
| `r33e/_re_parity_extra.py` | `recm["tier"]/["match"]/["path"]`、`.get("members")` | **正常**（形状核验 + members 全列断言） | `_mc_detail_out.txt:333-346` |
| `r33e/_re_run10_diff.py` | `reco/recm["tier"]/["match"]/["path"]`、`eq.members` | **正常**（`triple_t3_merged_shape` 断言） | `:133-146` 实读 |
| `r33e/_rev_cases.py` | `recm["tier"]/["match"]/["path"]`、`sorted(recm.keys())`、`members` | **正常**（显式断言无单对象字段） | `:330-339` 实读 |
| `r33e/_rev_core.py` | `recm["tier"]`、`recm["path"]`、`rm.eq.members` | **正常**（形状记录） | `_mc_detail_out.txt:436-444` |
| `r33e/_rev_edge25.py` | `recm["tier"]/["path"]/["match"]`、`sorted(keys)`、`members` | **正常**（`impl_disciplines_hold` 断言 `path is None`） | `_mc_detail_out.txt:456-471` |
| `r33e/_re_struct_diff.py` | 仅 `guard["..."]` 指纹（不读 rec 字段） | **正常**（difflib 白名单，与 merged 输出无关） | `_mc_detail_out.txt:380-388` |
| `equiv/_eq_proto.py` | `res["verdict"]`、`anchors[].path`、`reverify`、自产 `eq.members` | **正常**（装载 SL 原件；`eq_merge` 有 `verdict != "multi"` 守卫，merged 若替换装载则原样返回、不误读） | `:77-101` 实读 + `R33E_MERGE.md:51` |
| `equiv/_eqv_adv.py`、`_eqv_close.py`、`_eqv_j1.py` | `res["verdict"]`、`.get("anchors")`、`reverify["ok"]` | **正常**（SL 原件不产 merged；若换装载版，`== "multi"` 断言会失败 = 误读，但不崩，因全用 `.get`/verdict 字符串） | `_mc_detail_out.txt:37-74` |
| `equiv/_eq_surface_probe.py` | `_r["verdict"]`、`_m["verdict"]` | **正常**（间接 `P.SL.link`，同上） | `_mc_detail_out.txt:23-35` |
| `samedoc/_sl_run10.py`、`_slv_run10copy.py` | `r["verdict"]`、`anchors[].path`、`reverify["path"]/["bytes"]`（带 `if rec["reverify"]` 守卫） | **正常**（SL 原件不产 merged；换装载版时守卫仍成立，最多 verdict 计数变化 = 误读，不崩） | `_mc_detail_out.txt:498-519,585-606` |
| `samedoc/_sl_selftest.py` | `r["verdict"]`、`anchors[].path`、`reverify["path"]`（带守卫） | **正常**（同上） | `_mc_detail_out.txt:521-549` |
| `samedoc/_slv_multitest.py` | `r["verdict"]`、`anchors[].path`、`rec.get("path"/"match"/"tier")` | **正常**（`rec.get("path") is None and rec.get("match") is None` 是原 multi 断言；换装载版 merged 时该断言失败 = 误读，不崩，全 `.get`） | `_mc_detail_out.txt:551-583` |
| `samedoc/_slw_fix4.py` | `r["verdict"]`、`anchors[0]["path"]`、`reverify["sha"/"bytes"]`（带 `verdict=="unique"` 守卫） | **正常**（同上，`reverify` 只在 unique 分支读） | `_mc_detail_out.txt:608-636` |

**B. 未来接入面：下游 r11 binding_rec 消费件（调 `r11_scan_plus` / `r11_scan`，本会话 `_mc_empirical.py` 实跑 10 个真实表达式 + `_mc_crosscheck.py` 静态扫描）**

| 文件 | 读什么字段 | 遇 merged | 依据 |
|:--|:--|:--|:--|
| `r11/_f2v_verify9.py` | `match`、`verified_path`/`path`、`["bytes"]` | **崩**（TypeError `Path(None)`，实证 `CRASH_COUNT` 之一） | `:21-29` 实读 + `_mc_empirical.py` |
| `r11/_f2_selftest.py` | `match`、`verified_path`（`.get(...,"")`）、`tier=="T1"` | **误读**（`.endswith` 返回 False → 断言失败；不崩） | `:110` 实读 + `_mc_empirical.py` trial B = `False` |
| `r11/_f2_compare.py` | `["path"]`（直接下标）、`["match"]`、`.get("tier")` | **误读**（`plus_path=0` 但 `plus_match=1`；`assert nb["path"]==ob["path"]` 仅 orig 有 path 时触发，R3-3b 行不触发，故不崩） | `:49-50,66-69` 实读 + `_mc_empirical.py` trial D = `(0,1)` |
| `r11/_f2v_final.py` | `["path"]`/`["match"]` 计数、`tiers[b.get("tier")]` | **误读**（`collected=0` 但 `match=1`；tier dict 开放，新增 `SAMEDOC_LINK_EQ` 不崩） | `:51-58` 实读 + trial C |
| `r11/_f2v_run.py` | `.get("path"/"match"/"tier")` 列表化 | **误读**（`plus_paths=[None]`、`plus_match=[True]`） | `:48-64` + trial E |
| `r11/_f2w_dogfood.py` | `["path"]`/`["match"]` 计数、`tiers[...]` | **误读**（同 `_f2v_final.py`） | `_mc_detail_out.txt:244-260` |
| `r11/_f2w_extract.py` | 全 `.get("verified_path"/"recomputed"/"bytes"/"path"/"match")` | **误读**（`verified= recomputed=- bytes=- path=None`，报告静默空白） | `:26-33` 实读 + trial F |
| `r11/_f2_repro.py` | `b["declared"]/["path"]/["match"]`（直接下标，仅 orig binding） | **正常**（merged rec 含 `declared/path/match` 三键，实测 trial H 返回 tuple 不崩） | `:49` 实读 + trial H |
| `r11/_f2v_edge.py`、`_f2v_context.py`、`_g9v_verify.py` | `.get("tier"/"match"/"path")`（打印/计数） | **正常**（不假设单一 path） | `_mc_detail_out.txt:175-188`；`_mc_crosscheck.py` 分类 |
| `gate_r9r12/_g9_gate.py` | `.get("path")`→`reverified`、`.get("match") is True`→`n_match`、`.get("verdict")` | **误读**（`reverified=0` 但 `n_match=1`，`r11_problems` 空 ⇒ `r11_verdict="PASS"`，「匹配但无回验路径」被静默放过） | `:155-166` 实读 + trial G = `(0,1)` |
| `gate_fp7/_g7_predicates.py` (`r11_scan`) | 自产 `rec["match"]/["recomputed"]/["bytes"]` | **正常**（不产 merged，`problems` 契约不变） | `:192-218` 实读 |
| `gate_fp7/_gv_pred_check.py`、`_g7_reverse_validate.py`、`_doc_ast_align_check.py` | 仅调 `r11_scan` 比对 problems/hits，不读 binding_rec 单对象字段 | **正常** | 本会话 `python -I -X utf8 -c` 分类（calls/fields 输出） |
| `equiv/_eqv_fp.py`、`r33e/_re_fp_check.py`、`samedoc/_slw_hashes.py`、`_slv_hashes.py`、`_slv_count10.py` | 仅指纹/哈希校验（`_slv_count10.py` 读一次 `["path"]` + `["verdict"]` 计数） | **正常**（不消费 link_triple 的 rec） | 本会话分类输出 + `_mc_crosscheck.py` §2 |

**C. 关于「tier 值集封闭」的实查**：本会话 `grep -rnE "tier.*(not in|in \(|in \[|in \{)|assert.*tier|bad.*tier|unknown.*tier"` 于 `r11_f2_fix_20261109/`、`gate_r9r12_20261109/`、`gate_fp7_20261108/` 全 .py，**未发现任何封闭 tier 白名单**。现盘 tier 处理全是开放 dict（`_f2v_final.py:58`、`_f2w_dogfood.py:30` `tiers[b.get("tier")] = ...`）或针对特定样本的 `== "T1"` 断言（`_f2_selftest.py:69,120`）。故「tier 枚举扩展」此刻无实害，但接入后新增下游若写封闭枚举即触发风险（六条第 1 条）。

**D. 关于 `rec['verified_path']` / `['recomputed']` / `['bytes']` 直接下标**：`_mc_crosscheck.py` §2 全 lead 扫描列出所有直接下标点。与 merged rec 相关的仅 `_f2v_verify9.py:29,34`（`src["bytes"]`）；其余命中件（`_g7_fp_check.py`、`_g9v_regress.py`、`_sl_run10.py:122` 等）读的是自身构造的 dict 或 `reverify` 内层，不消费 link_triple 返回的 binding_rec。生产 `_f2_r11plus.py:272,279,290,297` 的 `["bytes"]` 是 `verified`/`r` 内层（自身构造），非 binding_rec。

---

## 3 第三步：区分「已存在的消费方」与「未来的消费方」

### 3.1 已存在的消费方（现盘真的在调 `link()`/`link_triple()`）

**有，17 件**（§2(a) 表），其中 7 件装 `_re_linked.py`、`_re_linked.link_triple()` **今天就会返回 merged rec**（`_re_j4_cases.py:111`、`_re_parity_extra.py:78`、`_re_run10_diff.py:132`、`_rev_cases.py:182,320`、`_rev_core.py:185`、`_rev_edge25.py:87`）。

**是真风险还是测试/探针？—— 全部是测试/复核/探针，无一是生产判定路径**：
- 7 件 RE+SL：r33e 写域内的「并入回归/复核」脚本，专门**断言 merged 正确形态**（`path is None`、走 `members`、无单对象字段），§2(d) 表全部判「正常」。它们不但不崩，恰恰是六条第 2 条的正确落地范例。
- 9 件 SL-only + 1 件间接：samedoc 自测 / equiv_class 原型，装载 `_sl_link.py` 原件（原件 `verdict ∈ {unique,multi,zero,invalid_hex}`，`_sl_link.py:195-220` 实读 + `R33E_MERGE.md:40-44`），**结构上不可能收到 merged**；即便把并入版替换装载，也只会「`== "multi"` 断言失败」（误读），不崩（全用 `.get` / `verdict` 字符串 / `if reverify` 守卫）。
- **结论：没有任何已存在的真实调用方遇 merged 会崩。**

### 3.2 生产路径核实（决定性事实）

命令：`grep -nE "link_triple|_re_linked|samedoc|\bsl_link\b|import .*link|\blink\(" lead/r11_f2_fix_20261109/_f2_r11plus.py`
输出：`NO_MATCH (none of the link-family symbols appear in _f2_r11plus.py)`

命令：`grep -nE "^import |^from |spec_from_file_location|exec_module|sys.path" lead/r11_f2_fix_20261109/_f2_r11plus.py`
输出：仅 `:45-48` 标准库 + `:70,72` 装载 `_g7_predicates.py`（`_g7_predicates_f2plus`）。即 `r11_scan_plus` 只依赖原版谓词，**不装载任何 link 家族模块**。

命令：`python -I -X utf8 -c`（打印 :302-310）
输出：`:303-305` 仍是 `rec["tier"]=None` + `warnings.append("绑定行缺显式路径，需人工锚定（R11/R3-3b）")`，`:306 bindings.append(rec)` —— 接入点保持空置，与 `R33E_MERGE.md:17,180` 记载一致。

→ **生产 `r11_scan_plus` 今天不产 merged，也不消费 merged rec。** 回件「未接入 r11_scan_plus 生产路径（仅给出适配清单）」属实，本会话独立核实。

### 3.3 未来的消费方（接入 `r11_scan_plus` 时新增的消费面）

在 `_f2_r11plus.py:303-305` 的 else 分支调 `RE.link_triple(...)` 并合并 rec 后，merged rec 会流入**所有下游 r11 binding_rec 消费者**。新增消费面 = §2(d) B 表所列 14+ 件，按影响分：
- **会崩**：`_f2v_verify9.py`（实证 TypeError）。
- **会误读（静默，最需警惕）**：`_g9_gate.py`（门禁 PASS 但无回验路径）、`_f2_compare.py`、`_f2v_final.py`、`_f2v_run.py`、`_f2w_dogfood.py`、`_f2w_extract.py`、`_f2_selftest.py`。
- **正常**：`_f2_repro.py`、`_f2v_edge.py`、`_f2v_context.py`、`_g9v_verify.py`、`_g7_predicates.py`、`_gv_pred_check.py`、`_g7_reverse_validate.py`、`_doc_ast_align_check.py`。

### 3.4 severity 判定

按任务给定规则「已存在的真实调用方遇 merged 会崩 = high；未来才接入的 = medium」：

- 已存在的 17 件真实调用方：7 件正确断言（正常）、10 件结构上不可能或仅误读（不崩）→ **不构成 high**。
- 唯一实证会崩的 `_f2v_verify9.py` 收不到 merged（它调 `r11_scan_plus`，而生产未接入）→ **属未来接入面**。
- 因此本审计 **severity = medium**。理由：merged 尚未进入任何生产判定链，当下零崩溃面；风险全部集中在「决定接入时」一次性引入的新消费面，且其中 1 处已实证会崩、7 处会静默误读。（若编排方一旦实施接入而未先修 §5(a) 最小安全集，severity 立即升为 high。）

---

## 4 第四步：六条适配逐条落地难度

| # | (a) 改什么（文件:行） | (b) 难度 | (c) 不改的后果 |
|--:|:--|:--|:--|
| 1 tier 枚举加分支 | **实现已做**：`_re_linked.py:311-312`（tier 三元新增 `SAMEDOC_LINK_EQ`）、`:326`（merged 分支重赋）。**消费方待做**：接入时 `_f2_r11plus.py:303-305` 把 `rec["tier"]` 置为 `SAMEDOC_LINK_EQ`（不得写 `None`）；未来任何封闭 tier 枚举处加分支。实查现盘**无封闭白名单**（§2 C），故此刻无必改行。 | **加分支**（低-中；实现侧已完成） | 若未来下游写了封闭枚举（None/T1/T2/T2N/T3/SAMEDOC_LINK），`SAMEDOC_LINK_EQ` 被当异常/丢弃 → 漏判或 KeyError；`tier=SAMEDOC_LINK_EQ` + `path=None` 被当异常。当前现盘无实害。 |
| 2 不假设 match⇒path / 走 members | `_f2v_verify9.py:24`（`Path(src.get("verified_path") or src.get("path"))`）、`:29`（`src["bytes"]`）、`:34`；`_f2_selftest.py:110`；接入时 `_f2_r11plus.py:303-305` 合并 rec 处须显式分支：`if tier == "SAMEDOC_LINK_EQ": 走 rec["members"]`（逐成员 path/sha/bytes），不写 `verified_path/recomputed/bytes`。 | **加分支 + 改契约**（中-高，六条中最实质） | **崩**：`TypeError: Path(None)`（本会话 `_mc_empirical.py` 实证）；即便绕过 `Path`，`src["bytes"]` 仍 `KeyError`；或**误读**：把「无单一对象的副本群」当成「匹配但缺路径」，门禁静默放过（§3.3 `_g9_gate.py`）。 |
| 3 problems 契约 | **实现已做**：`_re_linked.py:177-179`（`problems: []`）、`:330`（返回 `r["problems"]` 恒空）、`:47` docstring。**消费方待做**：`_f2_r11plus.py:303-305` 只把 `link_triple` 的 `warnings` 并入 `warnings`，**不得**把 merged warning 塞进 `problems`。 | **加分支**（低） | merged warning 静默丢失（人工无法看到副本群提示）；或误升级为 problem → 门禁把合法 warning 判 FAIL（违反「一律 warning 级」纪律 `_re_NOTES.md:28`）。 |
| 4 recompute 注入 | `_re_linked.py:171` `link()` 签名加 `recompute=None`，`:198` `hit.read_bytes()` 改走注入闭包（`hashlib` 结果同形）；`_f2_r11plus.py:144-147` 已有 `recompute` 闭包，接入时传参。 | **改契约**（中，纯优化、可选） | 仅重复 IO（同一文件被 r11 与 link 各读一次 sha256）；**语义不变、无正确性风险**。`_re_NOTES.md:70` 明写「语义不变，纯优化」。 |
| 5 run 快照 | 新增落盘：接入方在 `_f2_r11plus.py:303-305` 分支内，每次 merged 落 run 机读件 `{binding_hex, bytes_decl, members, decl_lines, decl_text}`；数据源现成（`_re_linked.py:276-281` `out["eq"]` 已含 `members`/`decl_lines`/`decl_hits[].text` 全文）。 | **加分支 + 新写件**（中） | 等价类是联查时刻快照，事后无法审计「当时」成员与声明行原文；成员漂移/声明行被改后不可追溯（TOCTOU 同限，`_re_NOTES.md:72-73`）。 |
| 6 显式修订声明 | 治理/文档面：在 `SAMEDOC_LINK.md:20` ★4「唯一命中才采」的修订关系登记（写入 `PENDING_DECISIONS.md` / `GOAL_THREE_TARGETS_20261018.md` 台账时注明）。**两件台账本任务绝对只读，只能登记不能改**；本会话未改（指纹 9/9 全等为证）。 | **文字说明**（低，但不可省） | 「唯一命中才采」被无声替换成「声明解析 → merged｜multi」，判据来源不可追溯；未来复核会把 merged 误当原规则的自然推论，绕过 J4 三条件与封闭集禁扩纪律（`_re_NOTES.md:74-76,80`）。 |

---

## 5 第五步：接入建议与最小安全集

### 5(a) 把 `_re_linked.py` 接入 `r11_scan_plus` 的最小必要改动

接入点唯一：`lead/r11_f2_fix_20261109/_f2_r11plus.py:303-305` 的 `else`（T1/T2/T2N/T3 全落空、现产 R3-3b 警告处）。**最小安全集 = 下列 1–3（代码必做）+ 5–6（治理/审计必做）；第 4 条可选**：

1. **调用与合并**（六条 1/3）：在该 else 分支调 `RE.link_triple(text, doc_dir, declared, bytes_decl, root)`；把返回 `warnings` 并入 `warnings`、`problems`（恒 `[]`）丢弃；把返回 rec 的 `tier="SAMEDOC_LINK_EQ"`、`match=True`、`path=None`、`members`、`decl_lines`、`samedoc_link` 合并进当前 `rec`，**绝不写** `verified_path/recomputed/bytes`。保留原 R3-3b warning 或替换为 merged warning（二选一，须显式，不得两者都丢）。
2. **消费方去假设**（六条 2，最关键）：修 `_f2v_verify9.py:21-29`（`:24` `Path(...)`、`:29/:34` `src["bytes"]`）与 `_f2_selftest.py:110`；统一约定：**`tier=="SAMEDOC_LINK_EQ"` 时走 `rec["members"]` 逐成员重算，不取 `rec["path"]`/`verified_path`/`bytes`**。`_g9_gate.py:157-158` 的 `reverified`/`n_match` 计数口径须明确「match=True 但 reverified=0」是否允许 PASS（需编排方裁决，不得默认放过）。
3. **tier 显式标注**（六条 1）：确保下游任何封闭枚举处加 `SAMEDOC_LINK_EQ` 分支；现盘无封闭枚举，但新增代码不得引入。
4. （可选，六条 4）`_re_linked.py:171` 加 `recompute` 注入，复用 `_f2_r11plus.py:144-147` 闭包省一次 IO。
5. **run 快照落盘**（六条 5）：每次 merged 落机读件，取 `eq` 全量；这是审计可追溯的唯一凭据。
6. **判定书登记**（六条 6）：台账写明对 `SAMEDOC_LINK.md:20` ★4 的显式修订。

**接入前不可省略的护栏**：接入会改动 `_f2_r11plus.py`（本会话指纹 `83f8217f…/15723`），必须在接入方写域内重算指纹并登记；`_re_linked.py` 保持只读（本会话已实算 `7ca339c6…/19481`）。

### 5(b) 有没有「不接也能用」的方式？—— 有，且是本会话推荐现状

- **离线人工提示模式**：`_re_linked.py:334-348` 已带 `main()` CLI，可对单个文档离线跑 `link()`，把 `merged` 的 warning（`:282-289`，含「未做单一对象主张（path=None）」「禁止由 merged 推导任何授权结论」+ 全量成员路径）与 `eq.members` 当**人工提示**，供人工从 `members`/声明行原文辨认角色归属；**不进任何自动判定、不写 `rec["path"]`、不并入 `problems`、不推导授权**。这与纪律 2 完全一致（`_re_NOTES.md:40-48`）。
- **现盘已证明可用**：r33e 的 7 个复核测试件就是这种模式（离线双跑比对 + 形状断言），本会话 `_mc_empirical.py` 亦以只读方式载入 `_re_linked.py` 产出真实 merged rec 完成消费面实测，全程未改任何被扫件。
- **未接入是合规状态**：`SAMEDOC_LINK.md:22`「是否接入由编排方裁决」（`R33E_MERGE.md:45` 实读引用）；`R33E_MERGE.md:17` 明写「本报告不自行上线」。因此「只登记适配清单、暂不接入」完全可行，代价仅是 F2-d 无路径绑定行继续走 R3-3b 人工锚定 warning（`_f2_r11plus.py:303-305`）。

### 5(c) 接入前必须先做的验证

1. **形状断言回归全绿**：`_re_j4_cases.py`（19/19）、`_re_run10_diff.py`（20/20）、`_re_parity_extra.py`（21/21）、`_rev_core.py`（92/92）、`_rev_cases.py`（69/69）、`_rev_edge25.py`（7/7）、`_re_struct_diff.py`（STRUCT_OK 11 hunk 全白名单）—— 记载见 `R33E_MERGE.md:190-204`、`_re_NOTES.md:85-96`。**本会话未重跑这 7 个脚本（只审计不改、只引用回件记载），标「未验（本会话未重跑）」**；接入方须自行复跑并留存 EXIT=0 输出。
2. **端到端联调（本会话未做，标未验）**：构造一条 F2-d 无路径绑定行（即 `:303-305` 落空的那类），实跑接入后的 `r11_scan_plus`，断言 `tier=="SAMEDOC_LINK_EQ"`、`path is None`、`match is True`、`members` 全列且 `anchors` 仍按 `max_detail=12` 截断、`problems == []`、warnings 含「禁止由 merged 推导任何授权结论」、unique/zero/invalid_hex/multi 输出与接入前逐字节全等（参照 `_re_run10_out.json` 的 20/20 断言口径）。
3. **下游消费者全量回放**：把 merged rec 喂给 §2(d) B 表每一件，确认零 TypeError / 零 KeyError / 无误读计数。本会话已实跑 10 个真实表达式（`_mc_empirical.py`，`CRASH_COUNT=2/10`）—— **接入前必须先修掉这 2 处崩**（`_f2v_verify9.py:24` 与 `:29`），否则联调必失败。
4. **门禁契约回归**：`_g9_gate.py:155-166` 的 `r11_items`/`reverified`/`n_match` 口径裁决；`_f2_compare.py:42-69` 的 30 件回归逐件 `declared` 序列与 `problems` 不得漂移（现 `:44-46` assert）。
5. **指纹护栏**：接入前后对 `_re_linked.py`（只读）、`_f2_r11plus.py`（接入方改）、两件台账各算 `hashlib.sha256` 并登记；本会话 9/9 全等基线见 §0。
6. **纪律复核**：封闭集 `DECL_RE` 不得扩词（`_re_linked.py:81`，`_re_NOTES.md:80` 明写扩词 = 误并风险，`R33E_MERGE.md:138,184` 已实跑证明）；三条纪律（path=None / 禁授权推论 / members 全列）逐条有断言。

---

## 6 如实登记的「未验」项（不补造）

1. **未验（本会话未重跑）**：`_re_j4_cases.py` / `_re_run10_diff.py` / `_re_parity_extra.py` / `_rev_*.py` / `_re_struct_diff.py` 的回归脚本；只引用 `R33E_MERGE.md:190-204`、`_re_NOTES.md:85-96` 的回件记载，未冒充本会话实跑。
2. **未验（本会话未做）**：`merged` 接入真实 `r11_scan_plus` 的端到端联调——本会话只审计不改，生产路径 `:303-305` 仍为空置（§3.2 实跑核实）。
3. **未验**：343 件全语料 multi 作用面未普查（沿用 `R33E_MERGE.md:179` §5.5-1 同限）。
4. **未验**：TOCTOU 漂移窗口不可实测（零真机 + 只读纪律，仅登记，`R33E_MERGE.md:181`）。
5. **未验**：`_mc_empirical.py` 的 10 个 trial 是「把真实 merged rec 手工喂入消费方表达式」，**不是**把 merged 真正接入 `r11_scan_plus` 后的端到端运行；二者结论方向一致但不等价，如实区分。
6. **`_mc_scan.py` 首跑报错**：本会话自写脚本键名笔误（`imp_sl` vs `imp_sl_link`），首跑 EXIT=1，修正后复跑 EXIT=0；两次输出均如实登记，笔误不影响任何扫描结论。

---

## 7 本会话产出件（唯一写域，前缀 `_mc_`）

| 件 | 用途 | 实跑输出 |
|:--|:--|:--|
| `_mc_scan.py` | 独立普查（剪枝 + 深度上限 6）：调用面 / 字段读 / 危险粗筛 | `dirsVisited=762 scannedPy=1902 prunedItems=177 depthCap=6 maxBytes=400000`；EXIT=0（修正后） |
| `_mc_detail.py` → `_mc_detail_out.txt` | 29 件候选逐件装载/调用/字段读/危险窗口 | 635 行，EXIT=0 |
| `_mc_count.py` | (a)(b)(c) 精确计数 | `COUNT(a)=17 COUNT(b)=12`、`rows_with_link_call=23`、EXIT=0 |
| `_mc_crosscheck.py` | merged 产出方 vs r11 消费方交叉、直接下标 KeyError 点 | 10 件装 `_re_linked.py`；交叉 §3 空集；EXIT=0 |
| `_mc_empirical.py` | 真实 merged rec 喂入 10 个现盘消费方表达式 | `CRASH_COUNT=2/10`，`TypeError: Path(None)`；EXIT=0 |
| `_mc_AUDIT.md` | 本报告 | — |

**零真机 / 零采样 / 只审计不改 / 不 commit 不 push 声明**：本会话未启动任何游戏进程、未 taskkill、未读活进程内存；未写任何 hook/MiniDump/SuspendThread/StackWalk/探针注入/动态内存解析；未修改 `_re_linked.py`、`_sl_link.py`、`_f2_r11plus.py`（`r11_scan_plus`）、任何消费方、两件台账、任何只读目录——§0 的 9/9 指纹全等即为证；未执行 `git commit` / `git push`。唯一写域 `lead/merged_consumer_audit_20261109/` 内新增件全部前缀 `_mc_`。
