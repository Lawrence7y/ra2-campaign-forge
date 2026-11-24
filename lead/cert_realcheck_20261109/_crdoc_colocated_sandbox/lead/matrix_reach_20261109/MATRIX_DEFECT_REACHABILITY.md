# MATRIX_DEFECT_REACHABILITY — 矩阵五处缺陷（W1/W2/O1/O2/W3）实际流可达性交付报告

- 撰写：可达性撰写员（动态工作流交付轮），2026-11-09。
- 被核对象：`lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`（下称「候选」）三函数 make_pre / classify / copy_post + 调用链，以及 `lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md`（下称「矩阵连带评估件」）所载五条可达性判断。
- 本件性质：**只查可达性，不下「该不该改矩阵」的结论**——改不改、怎么改属 A/B 裁决，不在本件范围。
- 引用记法：`out:n` = `lead/matrix_reach_20261109/_mr_probe1_out.txt` 行 n；`R:n` = `_mrv_probe1_out.txt` 行 n；`候选:n` = 候选源码行 n；`矩阵:n` = 矩阵连带评估件行 n。两份交付轮重跑件（`_mr_delivery_rerun_out.txt` / `_mrv_delivery_rerun_out.txt`）与原输出逐行同位（差异仅 §1 所记两处良性噪声），故行号引用对重跑件同样成立。

## 1 目的与边界

### 1.1 目的

矩阵连带评估件对五处缺陷（W1/W2/O1/O2/W3）各下了「可达 / 不可达」判断。本件把这些判断逐处对到实码：构造输入 → 实际调用候选函数 → 记录真实返回值 → 落到矩阵哪一行 → 与矩阵声称是否一致。可达只认「实跑走到过」，不认「理论上可以」；不可达必须附控制流证明。

### 1.2 边界（不做什么）

- 不判「该不该改矩阵」、不背书矩阵连带评估件 :129-:138 的选项 A/B 之争——那是 A/B 裁决的输入，本件只供事实。
- 不做真机触发概率实测：所有「评级」（§4）均为零真机纪律下的**推理**，逐条如实标注。
- 纪律：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样（无 hook / MiniDump / SuspendThread / StackWalk / 注入 / 动态内存解析）；零载体写（copy_post 异常分支全部用假 Path 对象逼出，真实 Recorder 经源码核验无 open/write——R:156-157）；候选模块经 importlib `spec_from_file_location` **静态装载、原样调用、代码零改动**（out:9；首轮 exec 草稿被 Mimosa 钩子拦截后弃用）。未 commit、未 push。

### 1.3 证据源与交付轮复现

三轮证据，全部落唯一写域 `lead/matrix_reach_20261109/`：

1. **撰写轮**：`_mr_fingerprint.py`→`_mr_fingerprint_out.txt`（7/7 MATCH）、`_mr_probe1.py`→`_mr_probe1_out.txt`（239 行 PROBE_DONE）、报告 `_mr_REACH_EVIDENCE_20261109.md`（7 条绑定行）。
2. **复核轮**：`_mrv_fp.py`→`_mrv_fp_out.txt`（baseline=7 match=7）、`_mrv_probe1.py`→`_mrv_probe1_out.txt`（168 行 PROBE_DONE，含自建 AST 全路径枚举器与 45 格全表）。
3. **交付轮（本件，本轮实跑）**：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\matrix_reach_20261109\_mr_delivery_fp.py` → `_mr_delivery_fp_out.txt`（上游 7 件指纹 7/7 逐字节一致，见 §2）；`python -I -X utf8 …\lead\matrix_reach_20261109\_mr_probe1.py` > `_mr_delivery_rerun_out.txt`（239 行 PROBE_DONE，与原输出 diff 仅 1 行：out:146 目录输入 `size=0→size=4096`，Windows 目录 `st_size` 环境相关噪声，该格 state 恒 `error`，与五缺陷判定无关）；`python -I -X utf8 …\lead\matrix_reach_20261109\_mrv_probe1.py` > `_mrv_delivery_rerun_out.txt`（168 行 PROBE_DONE，diff 仅 1 行：R:21 集合显示序 `{'error','present'}` vs `{'present','error'}`，Python 哈希种子导致的迭代序差异，语义恒等）。两探针 exit 均为 0。

## 2 上游指纹（7 件）与三函数输入/输出域

### 2.1 上游指纹（交付轮 `_mr_delivery_fp.py` 实算，hashlib.sha256，7/7 与编排方基线逐字节一致）

被核对象 SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759
被核对象 SHA256 = 6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8，字节数 = 29818
被核对象 SHA256 = 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016，字节数 = 3558
被核对象 SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
被核对象 SHA256 = ce84dbd5c8f3eb4386737e994447414a137ed2513d53ef977451f7700ff089c1，字节数 = 12979

（顺序：候选LF / 矩阵连带评估件 / 乙矩阵 JSON `lead/b2b_design_20261106/STATE_MATRIX.json` / 母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` / PENDING 台账 / GOAL 台账 / 上轮复核探针输出。第 1 行即被核代码本体绑定。）撰写轮报告与两探针输出本体亦经本交付轮实算并与复核轮记录一致：`_mr_REACH_EVIDENCE_20261109.md` = 67d0fc90ceae277f23d43f80484da9445a6385994752a882d04a8517809f10e9 / 20820，`_mr_probe1.py` = e9cfe070bb2e492087122a00a0bc024efa0238442c7cc73db99f3ff55aa8bd6b / 17541，`_mr_probe1_out.txt` = 7a8a4198bdfff6aac5f0794f46432d446e592308ad27b819701e50397ca3e27e / 18180，`_mrv_probe1_out.txt` = cc8c5308ecae2936c940bbaae54318e628709f4ca6e8f46d19fbe113505c0d2d / 12685，`_mrv_fp_out.txt` = 617f5cfd597bc7dcfad8f48cb2ca532dd481828b1f20cdf53c14dcba1831a589 / 1385。

### 2.2 三函数输入域 / 输出域（源码实读 + AST + 运行期实跑；源码行均为交付轮 `sed` 实读核对）

**(a) make_pre_freshness_snapshot（候选:4580-4613）**
- 输入域：单个 `except_path`（:4595 `Path(except_path)`，非法输入转 TypeError 进 except）。
- 返回路径仅两条：`:4601`（absent 早退，其前必有 :4599 覆写）与 `:4613`（present 路或 except 路汇合，其前必有 :4603 或 :4610 覆写）。`snap["state"]` 赋值点全函数仅 `:4599 "absent_confirmed"`、`:4603 "present"`、`:4610 "error"` 三处 + 初值 `:4589 "unknown"`（out:14-20 AST；R:19-24 全路径枚举：封闭路径 3 条，保持初值 unknown 的返回路径 **0** 条）。
- 输出域（运行期实证，out:144-153 / R:50-62）：`{absent_confirmed, present, error}`，**不含显式 unknown**（`'unknown' in states_seen = False`，out:153）；present 路线性必经 `:4607 snap["sha256"] = sha256_file(p)`（out:15、out:75），sha 必为非空 64 位（sha256_file 候选:431-437 单一返回 `h.hexdigest()`，out:54-60），算炸则整体 error——**不含 present缺sha**（out:220-221）。

**(b) copy_post_except_evidence（候选:4701-4826）**
- 输入域：`(rec, carrier_dir, out_dir, pre_freshness_snapshot=None)`（候选:4701-4704）；pre **原样透传** classify（:4762/:4788/:4804），不改写。
- `post_observed["read_error"]` 写点全函数唯一：`:4786`（out:41；R:42），位于 except :4773-4790 内——先 rec.add ERROR 三行（:4777-4785）、再置 read_error、再 `_emit_f(classify(...))`（:4788）、再 `raise` 上抛。早退分支 src_missing :4756-4764 与正常路径 :4804 classify、:4816-4825 载体快照尾段各自独立。

**(c) classify_except_freshness（候选:4616-4699）**
- 输入域：`(pre_freshness_snapshot, post_observed)`；非 dict 折叠为 `{}`（:4634-4635/:4641），state ∉ FRESHNESS_SNAPSHOT_STATES（候选:228 四态 `('unknown','absent_confirmed','present','error')`）折叠为 unknown（:4637-4638）。
- 分支码序（out:25-36；R:29-41 独立 AST 零偏差）：归一 :4637 → **read_error :4643（第一实质分支）** → unknown :4648 → error :4652 → 无件 :4657 → absent_confirmed×在场 :4666 → 缺 pre.sha :4673 → 缺 post.sha :4678 → sha 异 :4681 → mt :4686/:4690/:4693 → 其余 :4697。
- 返回值全域 13 出口（out:52 汇总）：`post_read_error/none/None`（:4644、:4679）、`unknown/none/None`（:4649）、`error_pre_snapshot/none/None`（:4653、:4674）、`absent_both/low/False`（:4659）、`vanished/none/None`（:4662）、`new_first_appearance/high/True`（:4667）、`new_write/high/True`（:4682）、`leftover_unchanged/medium|high/False`、`rewritten_same_content/low|medium/True`；`usable_as_crash_evidence` 恒 False（49/49，R:122）。

**调用链（pre 快照实流来源）**：全模块 pre 快照写点仅 `:6528`（AnnAssign None，try 之前预初始化，:6526-6527 注释明言 None=未采集）与 `:6623`（Assign = make_pre 输出）（out:46-48；R:44-45，字段级改写点为空）。传参链：:6623 → :7367（finalize_trip 唯一调用点显式传参，finally 内 :7358，docstring :6138「`finally` 调用本函数」）→ :6166-6168（`_except_evidence_copy` 原样传 copy_post）→ :4762/:4788/:4804。实流 pre 取值只有三类：`None`、make_pre 输出（三态）——无第四种。

## 3 五处缺陷逐处可达性实证

### 3.1 W1（矩阵 :2 把 pre 未采集四变体 × read_error 错盖成 unknown）

- **矩阵声称**（矩阵:71）：行 :2 匹配键「pre=None/{}/缺state/脏值 + **跑后任意文件状态**」→ 声称 `unknown/none/None`；判定列自记「**W1**：后件过宽，read_error 格被错盖」。
- **构造输入 → 实跑返回**：classify 直调，pre 八变体（None/{}/缺state/脏值/显式unknown/absent_confirmed/present/error）× read_error 两型（exists=None / exists=True），16/16 格实跑：

```
（_mr_probe1_out.txt:159, :169, :173-174 摘；16 格全同型）
  pre=None(未采集)      × read_error·exists=None -> verdict='post_read_error' conf='none' is_new=None pre_state='unknown'  [矩阵归属: :2]
  pre=absent_confirmed × read_error·exists=None -> verdict='post_read_error' conf='none' is_new=None pre_state='absent_confirmed'  [矩阵归属: 无行=O1 / exists=True 型被:6字面误claim=O1']
  pre=error          × read_error·exists=None -> verdict='post_read_error' conf='none' is_new=None pre_state='error'  [矩阵归属: :4=W2]
```

- **落哪一行 / 与矩阵声称是否一致**：四未采集变体 × read_error 按 :2 匹配，矩阵声称 `unknown`，实码 `post_read_error` → **不一致，W1 错盖坐实**（16/16，out:159-174；复核 45 格全表中 18 个 read_error 格全部 PRE，R:112）。显式 unknown 两型按严格键 :2 前件不含、:3 要跑后无件 → 无行（out:167-168 记 W1′）。
- **实流可达性：可达，但收窄为 (pre=None × read_error) 单格**。控制流依据：① pre 实流取值仅 None / make_pre 三态（§2.2 调用链，两写点 ：6528/:6623）——{}/缺state/脏值 dict **无第三写点可注入**，显式 unknown 不在 make_pre 输出域（out:153）；② read_error 写点唯一 :4786，对任意 pre 生效（异常路径 ：4773 不检查 pre），两半正交无代码守卫（out:159-160 直调 + 复核经 copy_post 组合实跑：R:153-154 pre=None × C1 读锁 → PRE）。故 {}/脏值/显式unknown × read_error 各格均为 fixture 域，实流不可产；可达子集就是 pre=None（:6623 之前失败/早退）× read_error 一格。

### 3.2 W2（矩阵 :4 无跑后限定，error × read_error 错盖）

- **矩阵声称**（矩阵:73）：行 :4 匹配键「snap.error 非空（**无跑后限定**）」→ 声称 `error_pre_snapshot/none/None`；判定列「**W2**：read_error 格被错盖」。
- **构造输入 → 实跑返回**：pre=error 用**真实 make_pre 产物**（`Path(None)` → TypeError → error，out:147）：

```
（_mr_probe1_out.txt:179-181）
  error × read_error(exists=None) -> verdict='post_read_error' conf='none' pre_state='error' note='★ 跑后件读/复制失败（独立 error 出口，禁止静默）：PermissionError: [Errno 13] fake-lock (探针构'
  error × 跑后无件              -> verdict='error_pre_snapshot' conf='none'  (矩阵 :4 ✓ 对照组)
  → 矩阵 :4 声称 error_pre_snapshot，read_error 格实码 'post_read_error' ⇒ W2 实证
```

- **落哪一行 / 与矩阵声称是否一致**：error × read_error 按 :4 匹配，声称 EPS，实码 PRE → **不一致，W2 坐实**；error × 跑后无件格 ：4 声称与实码一致（对照 ✓，out:180）。码序保证：read_error :4643 先于 error :4652 截停（out:26 vs out:28）。
- **实流可达性：可达，实证成立**。两半各有实产路径：pre=error——make_pre 对载体 except.txt 的 exists/stat/sha256_file 抛异常即产（8 类输入 sweep 中 4 类产 error，out:146-148/151）；read_error——copy_post C1-C3 实跑产出（out:187-203）。同一持续根因（句柄/ACL 横跨两时点）可一次造成两半。

### 3.3 O1（absent_confirmed × read_error——exists=None 型无行，exists=True 型被 :6 字面误claim）

- **矩阵声称**（矩阵:113）：absent_confirmed × read_error·exists=None「**O1 主子格**（无行：:5 要 present、:6 要『在场硬证』、:7 要『无件』，exists=None 三者皆不满足）」；exists=True 型「**O1′**（:6 字面『跑后在场（存在性硬证）』被满足 → 会误claim NFA/high）」（行 :6 判定列同记，矩阵:75）。
- **构造输入 → 实跑返回**：pre=absent_confirmed（真实 make_pre 产物，out:144）+ copy_post 假对象逼异常，三型实跑：

```
（_mr_probe1_out.txt:187-191 C1 读锁 / :193-197 C2 写满 / :199-203 C3 exists 炸，摘 C1）
  copy_post 结果: 外抛 PermissionError: [Errno 13] 文件被占用(探针)
  Recorder ERROR 行: [('freshness_copy_failed', 'PermissionError: [Errno 13] 文件被占用(探针)'), ('freshness_copy_stage', 'read_bytes/stat/write_bytes'), ('freshness_copy_traceback', …)]
  Recorder FRESHNESS verdict/conf/is_new: [('freshness_verdict', 'post_read_error'), ('freshness_confidence', 'none'), ('freshness_is_new', None)]
  classify 实收: pre_is_None=False pre_state='absent_confirmed' post_exists=None post_read_error='PermissionError: [Errno 13] 文件被占用(探针)' → verdict='post_read_error' conf='none'
```

  三型（C1 read_bytes 锁 / C2 dst.write_bytes 磁盘满→post_exists=True / C3 src.exists() 炸）全部实产 read_error → PRE。对照组：C4 跑后无件 → `absent_both/low/False`（:7 ✓，out:208）；C5 跑后在+复制全成功 → `new_first_appearance/high/True`（:6 ✓，out:214）。复核独立复现 C1-C5，且 C5 以 `__fspath__` 指向只读真实文件**走完全函数含 ：4816-4825 尾段**，verdict 一致（R:128-133）。
- **落哪一行 / 与矩阵声称是否一致**：exists=None 型——:5（要 present）、:6（要跑后在场）、:7（要跑后无件）匹配键皆不满足 → **无行（孤儿）**；exists=True 型——:6 字面命中，会 claim `new_first_appearance/high`，实码 `post_read_error` → **误配（O1′）**。矩阵对「无行/误claim」的自记与实码一致（即矩阵连评估件自己已判此缺陷，本轮实证其可达）。
- **实流可达性：可达，实证成立**。只在复制失败时出现，正常流不触（C4/C5 对照）。

### 3.4 O2（显式 unknown × 跑后在场 无行——矩阵判「实流不可达」）【不可达，附控制流证明】

- **矩阵声称**（矩阵:124）：O2「严格键今日即无行（:3 前件限定『跑后无件』）；实际流**不可达**（make_pre 三路必覆写初值，§3.1 末 + 探针 P4 False）；宽键读法下标签恰同，无实害」。
- **构造输入 → 实跑返回（fixture 域可构）**：classify 直调手造 `{"state":"unknown",…}` × 跑后在 → `verdict='unknown' conf='none' pre_state='unknown'`（out:229）——该格在 classify 层良定义，**但只能 fixture 域构造**。
- **实流不可达证明（三重，控制流为核心）**：
  1. **AST 控制流**：make_pre 的 state 赋值仅 :4599/:4603/:4610 三点 + 初值 :4589（out:14-16），return 仅 :4601/:4613 且每个 return 前必有覆写（out:17-18）——**不存在保持初值 "unknown" 的返回路径**。复核自建全路径枚举器独立坐实：封闭路径 3 条，终态域 `{4601:{absent_confirmed}, 4613:{present,error}}`，保持初值 unknown 的路径数 = 0（R:20-23）。
  2. **运行期 sweep**：8 类输入实跑（真实文件/不存在/目录/None/整数/非法字符/ENOTDIR/空串），`states_seen = {'absent_confirmed': 3, 'present': 1, 'error': 4}`，`★ 显式 'unknown' 是否出现在 make_pre 输出域：False`（out:152-153；R:58-59 同）。
  3. **传参链封闭**：实流 pre 仅两写点 :6528(None)/:6623(make_pre)，字段级改写点为空（out:46-48；R:44-45）——无第三方可注入显式 unknown dict。
- **边界澄清（含一处引证瑕疵，如实登记）**：折叠 unknown（pre=None）× 跑后在 是实流可达的，但它落 ：2 且 ：2 对非 read_error 格声称 unknown 与实码**标签恰同**、无误配。撰写轮报告此格引 out:231 佐证，经复核实读 out:231 实为「pre=None × 跑后无件」格——**引证行号与格不符**；复核已补跑该格（R5：`None × 跑后在·全 -> 'unknown'/'none'/is_new=None`，R:70），结论本身成立（R:113「撰写人未测格，复核补测」）。
- **判定：不可达（评估判断成立，实证）**。

### 3.5 W3（present × 缺 pre.sha × read_error——:13 与 :5 同抢；矩阵判「实流不可达」）【不可达，附控制流证明】

- **矩阵声称**（矩阵:82 行 :13 判定列 + 矩阵:115）：「✓（read_error 时被 ：5 先截 → **W3 重叠，仅 fixture 域**）」；4.1 表「实际流不可达——make_pre 在场必算 sha :4607，算炸→error；仅 fixture 域」。
- **构造输入 → 实跑返回（fixture 域）**：

```
（_mr_probe1_out.txt:222-224）
  fixture present×缺pre.sha × read_error -> verdict='post_read_error' pre_state='present' (:5 先截，:13 同抢落空)
  fixture present×缺pre.sha × 跑后在·无read_error -> verdict='error_pre_snapshot' (:13 域内正确)
  fixture present×带sha × read_error(exists=True) -> verdict='post_read_error' (:5 ✓)
```

  同抢格实码恒由 :5 的 read_error 分支赢（码序 :4643 先于 :4673，out:26 vs out:31）→ **即便 fixture 域，:13 也抢不到该格**。
- **实流不可达证明（三重，控制流为核心）**：
  1. **AST + 源码**：present 路线性必经 `:4607 snap["sha256"] = sha256_file(p)`（out:15、out:75；复核路径枚举：终态 present 但缺 sha256 事件的路径数 = 0，R:23）；sha256_file（候选:431-437）单一返回非空 hexdigest，任何读异常上抛进 except ⇒ 整体 `state="error"`（:4610）——「present 且 sha 缺失」**不在 make_pre 输出域**。
  2. **运行期**：真实在场文件 → `state='present' sha256=6f2b3009b0de33bb… len(sha)=64`（out:220；R:61）；sha 必炸输入（Path(None)、目录）→ 整体 error 而非 present缺sha（out:221；R:62）。
  3. **传参链封闭**：pre 原样透传（:4762/:4788/:4804），途中无人清空 sha 字段（R:45 字段级改写点为空）。
- **判定：不可达（评估判断成立，实证）**；且 :13/:5 同抢只在 fixture 域存在，在该域实码也恒由 :5 赢。

## 4 可达性汇总表与最短触发链

### 4.1 汇总表

| 缺陷 | 评估说法（矩阵连带评估件原文行） | 实证结果 | 证据 | 触发条件现实性评级 |
|:--|:--|:--|:--|:--|
| W1（:2 后件过宽错盖） | :2 前件含「跑后任意文件状态」，read_error 格被错盖（:71；自记已登记） | **可达，实证成立但收窄**：实码 16/16 read_error 格全 PRE（out:159-174）；实流可达子集 = (pre=None × read_error) 单格，{}/缺state/脏值/显式unknown 变体 fixture 域 | out:159-174、out:41（read_error 写点唯一 ：4786）、out:46-48（pre 两写点）、R:112（18 格全 PRE）、R:153-154（组合实跑） | **近乎不可能**（三条件叠加；评级为推理，未实测） |
| W2（:4 无跑后限定错盖） | :4 前件无跑后限定，read_error 格被错盖（:73，本轮新发现自记） | **可达，实证成立**：error×read_error → PRE（out:179），error×无件 → EPS 对照 ：4 ✓（out:180） | out:146-148/151（make_pre 实产 error）、out:187-203（copy_post 实产 read_error）、out:26/28（分支序） | **罕见**（同根因双时点；评级为推理） |
| O1（absent×read_error 缺行/误claim） | 主子格无行（孤儿）、write_bytes 子格被 ：6 字面误claim（:75、:113） | **可达，实证成立**：C1/C2/C3 经 copy_post 实跑全产 read_error → PRE（out:187-203）；exists=None 型孤儿、exists=True 型 O1′ 误配；C4/C5 对照 ：7/:6 ✓（out:205-215） | out:187-203、R:135-151（独立复现）、矩阵匹配键 ：71-:82 静态实读 | **罕见**（句柄残留/AV 锁/磁盘满；评级为推理） |
| O2（显式unknown×跑后在 无行） | 实流不可达：make_pre 三路必覆写初值（:124） | **不可达，实证成立**（三重：AST 控制流 + 运行期 sweep + 传参链封闭；fixture 域可构 out:229） | out:14-20、out:152-153、out:46-48、R:19-24（0 路径保持 unknown）、R:58-59 | 不适用（无触发链） |
| W3（present×缺pre.sha×read_error，:13/:5 同抢） | 实流不可达：make_pre 在场必算 sha，仅 fixture 域（:82、:115） | **不可达，实证成立**；且即便 fixture 域 ：5 亦恒先截、:13 同抢落空（out:222-223） | out:14-20 + R:23（0 条 present 缺 sha 路径）、out:54-60（sha256_file 恒非空）、out:220-221、R:45 | 不适用（无触发链） |

### 4.2 可达缺陷的最短触发链（评级均为零真机纪律下的推理，未实测）

1. **O1**：真实 trip → 跑前快照确认无件（候选:4598-4601）→ 跑中游戏写出 except.txt → 收尾 copy_post 复制**失败**（C1/C3 读侧：进程未死透握句柄（terminated_ok=False 时 finalize 照跑，:7360 在 finally 内）/AV 瞬时锁/ACL；C2 写侧：out_dir 磁盘满或 AV 拦新建副本）→ :4786 置 read_error → classify 落 PRE → exists=None 型矩阵无行（孤儿）/exists=True 型被 ：6 字面误claim（O1′）。
2. **W2**：make_pre 在 ：6623 对载体 except.txt 采集抛异常（AV 瞬时锁/ACL/路径异常 → error 态，out:146-148）+ 同趟收尾复制又失败（同一持续根因横跨 pre/post 两时点可一次造成）→ read_error 先截（out:26 vs out:28）→ :4 声称 error_pre_snapshot 与实码 PRE 不符。
3. **W1**：:6623 之前异常/早退（pre 停在 ：6528 的 None）→ finalize 在 finally 仍被调（:7358）→ 载体 except.txt 在场（早退趟通常无新产件，需外来残留/投放）且读取失败 → classify(None, read_error) → PRE，:2 声称 unknown 与实码不符。
4. **O2 / W3**：不可达，无触发链。

## 5 复核回件、已实证/未验分界、未改任何文件声明

### 5.1 复核回件（verdict 如实转录）

复核轮独立复核**全部成立，无不成立项**，verdict = **confirmed**（按规则 refuted/partial 才标 unconfirmed，本件适用 confirmed）。复核绑定行（复核回件原文）：

被核对象 SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759

复核要点（复核回件原文要点转录）：①指纹——复核实跑 `_mrv_fp.py`，7 件与编排方基线 7/7 逐字节一致（`_mrv_fp_out.txt` 尾行 `baseline=7 match=7`）；②域绘制逐行实读无错绘；③独立实证——自建 AST 全路径枚举器（对不可达结论健全的过近似）坐实 O2/W3 控制流证明（R:19-24）、classify 9pre×5post=45 格实跑（R:65-113）、make_pre 8 类 sweep（R:50-62）、copy_post C1-C5 假对象实跑（R:125-158，其中 C5 走通 ：4816-4825 尾段、W1 组合 pre=None×读锁经 copy_post 落地 R:153-154）、pre 快照两写点零字段改写（R:44-45）；④不可达论证质检：撰写人给的是控制流+穷举 sweep+传参链封闭，非「没构造出来」，通过；⑤装载副作用扫描：顶层 11 处 Call 仅候选：182 SetProcessDPIAware 有进程级效果（`_mrv_toplevel_scan_out.txt`），无未声明副作用；⑥诚实度：撰写人 §6 六条未验如实，其中两条复核已代为收口（见 §5.3）；发现一处**引证瑕疵**（O2 边界格引 out:231 实为另一格，复核补跑证实结论正确，R:70、R:113），不影响结论；⑦越界检查：撰写轮仅落 5 件于唯一写域、7 件基线零改动、HEAD 未动、无「该不该改矩阵」结论——本交付轮逐项对照无违（§5.4）。

### 5.2 已实证（三轮实跑/AST，本轮交付轮指纹与双探针重跑复现）

- 三函数输入/输出域与分支码序（out:14-48、out:54-139；R:19-45；源码行交付轮 sed 实读逐段核对）。
- make_pre 输出域不含显式 unknown、不含 present缺sha（out:144-154、out:220-221；R:50-62）。
- classify 对 pre 八变体 × read_error 两型 16/16 落 post_read_error（out:159-174；R:67-112 共 45 格）；error×read_error → PRE 且 error×无件 → EPS（out:179-181）。
- copy_post 三类异常（读锁/写满/exists 炸）实产 read_error 且 ERROR 行 + F 字段落盘 + 上抛（out:187-203；R:135-151）；对照格 :7/:6 取值正确（out:205-215）；C5 尾段 ：4816-4825 走通（R:128-133）。
- pre 快照全模块仅两写点、原样透传、无字段级改写（out:46-48；R:44-45）。
- 指纹 7/7（撰写轮、复核轮、交付轮三轮独立实算一致）。
- 双探针交付轮重跑复现（差异仅 §1.3 所记两处与判定无关的良性噪声）。

### 5.3 未验（如实登记，不补造；最终口径=撰写轮六条 − 复核轮收口两条 + 复核轮自记一条）

1. **真机触发概率**：§4.2 三条「评级」（近乎不可能/罕见/罕见）全部为**推理**——零真机纪律下未实测进程句柄残留、AV 锁、磁盘满的真实频率。
2. **(pre=None × read_error) 未做 main→finally 整链实跑**（main() 会触真机操作，禁跑）；实证形态 = 两半各自实产（out:159-160 直调 + out:46-48/:7358 链路 + R:153-154 组合经 copy_post）的组合论证，非整链实跑。
3. **move_out_evidence_and_verify（:5563）未展开**（与五缺陷无涉；撰写轮未验④的尾段部分已由复核 C5 走通收口，余此件）。
4. **9×9 全格矩阵未重跑**（上轮 72/81 格两轮实跑在案；撰写轮只跑五缺陷相关格+对照格，复核轮 45 格；交付轮未再扩格）。
5. **py3.12 exists() 吞非法字符/ENOTDIR 路径为 False**（out:149-150 副作用观察）仅在 Python 3.12.10 实测，其他版本未验。
- （复核轮已收口、不再列为未验：`run_guarded_steps` 逐项必跑——复核展开 ：4540-4545 证实 for 循环无 break；:4816-4825 载体快照尾段——复核 C5 走通。）

### 5.4 未改任何文件声明

本交付轮**未改任何文件**：只读域（`lead/matrix_row5_20261109/`、`lead/b2b_design_20261106/`、`lead/b2b_candidate_lf_20261107/`、`lead/n4_yi_final_20261108/`、母本、两件台账）零改动——交付轮 hashlib 实算 7/7 与编排方基线逐字节一致（§2.1，`_mr_delivery_fp_out.txt`）即零改动实算凭证；`git status` 显示两台账 `MM` 与只读目录 `??` 均为会话开始前既有状态（开场快照在案），非本轮所改；HEAD 停在 26574589aa8401e8f3f2934680a1ea7109bafa2d 未 commit、未 push。写域内既有 11 件（撰写轮 5 件 + 复核轮 6 件）零改动——其中 5 件经交付轮实算与复核轮记录逐字节一致（§2.1）。本轮新增仅 5 件，全部落唯一写域 `lead/matrix_reach_20261109/`：`_mr_delivery_fp.py`、`_mr_delivery_fp_out.txt`、`_mr_delivery_rerun_out.txt`、`_mrv_delivery_rerun_out.txt`、`MATRIX_DEFECT_REACHABILITY.md`（本件）。
