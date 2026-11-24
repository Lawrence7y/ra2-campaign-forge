# _mr_REACH_EVIDENCE_20261109 — 矩阵四处缺陷（W1/W2/O1/O2/W3）实际流可达性实证报告

- 撰写：可达性实证员（动态工作流子代理），2026-11-09。性质：**只查可达性、不下「该不该改矩阵」的结论**（A/B 裁决不在本件范围）。
- 被核对象：`lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` 三函数（make_pre :4580-4613 / classify :4616-4699 / copy_post :4701-4826）+ 调用链（:6137/:6166-6168/:6528/:6623-6629/:7358-7367）+ `lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md` 所载五条可达性判断。
- 实跑命令（本轮全部实跑）：
  1. `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\matrix_reach_20261109\_mr_fingerprint.py` → `_mr_fingerprint_out.txt`（7/7 MATCH）
  2. `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\matrix_reach_20261109\_mr_probe1.py` → `_mr_probe1_out.txt`（239 行，PROBE_DONE）
- 下列所有「实跑输出」引用均指 `_mr_probe1_out.txt` 行号（记作 out:行）；候选源码引用记作 候选:行。

## 0 绑定行（本轮 `_mr_fingerprint.py` 实算，与编排方下发基线逐字节一致，7/7 MATCH）

被核对象 SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759
被核对象 SHA256 = 6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8，字节数 = 29818
被核对象 SHA256 = 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016，字节数 = 3558
被核对象 SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
被核对象 SHA256 = ce84dbd5c8f3eb4386737e994447414a137ed2513d53ef977451f7700ff089c1，字节数 = 12979

（顺序：候选LF / 矩阵连带评估件 / 乙矩阵 JSON / 母本 / PENDING 台账 / GOAL 台账 / 上轮复核探针输出 `_r5v_probe_out.txt`。第 1 行即被核代码本体绑定。）

## 1 方法与纪律声明

- **装载方式**：importlib 静态装载候选模块（`spec_from_file_location`，out:9），候选函数**原样调用、代码零改动**。首轮探针草稿用 AST 抽取源码 + `exec` 执行，被 Mimosa 安全钩子判「代码注入」拦截（高危，写入被拒）——已改为零 `exec` 的静态 import 方案（任务规则明列允许「静态 import 候选模块」）。装载前模块顶层经 AST 全量扫描（本轮实跑）：仅 import / 常量赋值 / 函数类定义 / 一处 `ctypes.windll.user32.SetProcessDPIAware()`（候选:182，探针进程本地图标缩放设置，无文件系统与外部进程副作用）/ `if __name__ == "__main__"` 门（候选:7532）⇒ 装载无载体写、无进程操作。
- **观察点**：classify 仅在模块属性层挂日志包装（记录 classify 实收 pre/post 与返回值；实码 `real_classify` 原样执行并返回其原结果，out:239 汇总调用次数）。copy_post 的异常分支用假 Path 对象（FakeDir/FakeLeaf）逼出，**零真实文件写**；make_pre 只做真实只读检查（`exists()`/`stat()`/`open(...,'rb')` 读）。
- **零真机**：未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存。**零采样**：无 hook / MiniDump / SuspendThread / StackWalk / 注入 / 动态内存解析。
- **写域**：本件与三件探针件全部落唯一写域 `lead/matrix_reach_20261109/`；被核九件+母本+两台账零改动（指纹 7/7 MATCH 即为本轮零改动的实算凭证）。未 commit、未 push。
- Python 3.12.10；`python -I -X utf8` + 绝对路径。

## 2 第一步：三函数输入域 / 输出域（实读 + AST 实证）

### (a) make_pre_freshness_snapshot（候选:4580-4613）

- **输入域**：单个 `except_path`（约束为 Path，实际任意对象——`Path(except_path)` 在 :4595 会把非法输入转成 TypeError）。
- **输出域（out:14-20 AST 控制流图）**：`snap["state"]` 全模块仅 3 个覆写点——`:4599 "absent_confirmed"`、`:4603 "present"`、`:4610 "error"`（初值 `"unknown"` :4589）；return 仅 `:4601`（absent 早退，其前必有 :4599 覆写）与 `:4613`（present 路或 except 路汇合点，其前必有 :4603 或 :4610 覆写）。except 处理器 :4608-4612 恒置 `state="error"`。
- **答问**：
  - absent_confirmed 条件 = `not p.exists()`（:4598）；**error 条件** = try 体 :4595-4607 任何一步抛异常（Path 构造 / exists / stat / time / now_iso / sha256_file）。
  - **不会产出显式 `'unknown'`**（P4 运行期 sweep 实证，out:144-153：8 类输入 → states_seen={'absent_confirmed':3,'present':1,'error':4}，`'unknown' in states_seen = False`，out:153）。
  - **不会产出「present 但缺 sha」**：present 路 :4603→:4613 线性必经 :4607 `snap["sha256"] = sha256_file(p)`；sha256_file（候选:431-437，out:54-60 逐行）单一返回 `h.hexdigest()`（非空 64 位），任何读异常上抛进 except ⇒ 整体 `error`。运行期交叉验证：真实在场文件 → present + 64 位 sha，且与 hashlib 直算逐字节一致（out:145、out:154、out:220）。
  - 副作用观察（与五缺陷无关，如实记录）：Windows py3.12 下 `Path.exists()` 把「非法字符路径」「ENOTDIR 子路径」吞为 False ⇒ 这两类输入落 `absent_confirmed` 而非 error（out:149-150）——即 absent_confirmed 含少量「根本不可能存在」的路径，不只代表「确认无件」。

### (b) copy_post_except_evidence（候选:4701-4826）

- **输入域**：`(rec, carrier_dir, out_dir, pre_freshness_snapshot=None)`（:4701-4704）；pre 原样透传给 classify（:4762/:4788/:4804），不修改。
- **read_error 条件**：唯一写点 `:4786`（P0a3 实证，out:41——try 体 :4755-4772 内 `src.exists()`/`read_bytes()`/`stat()`/`dst.write_bytes()` 任一抛异常 ⇒ except :4773-4790 先 rec.add ERROR 三行（:4777-4785）、再置 read_error、再 `_emit_f(classify(...))`（:4788）、再 `raise` 上抛）。**设了 read_error 之后不再算 post sha**（异常直接跳离 try），故 read_error 与 post.sha256 互斥于两条路：读失败型 `exists=None`（:4769 update 未达）；写失败型 `exists=True` 且 sha 已置（:4769 先 update、:4772 才可能炸）——两型均由 P3 实跑产出（C1/C3 vs C2，out:187-203）。
- **正常路径**（:4773 无异常）：:4804 classify（copied）→ :4813 rec.add → :4815 `_emit_f(fresh,"copied")` → :4817-4825 载体件快照（本件不展开，矩阵连带评估 §5.5-4 同口径）。

### (c) classify_except_freshness（候选:4616-4699）

- **输入域**：`(pre_freshness_snapshot, post_observed)`；非 dict 一律折叠（:4634-4635/:4641），state ∉ FRESHNESS_SNAPSHOT_STATES（候选:228 四态）折叠为 unknown（:4637-4638）。
- **分支码序（out:25-36 AST 实证，12 个顶层 if）**：归一 :4637 → **read_error :4643（第一实质分支）** → unknown :4648 → error :4652 → 无件 :4657 → absent_confirmed×在场 :4666 → 缺 pre.sha :4673 → 缺 post.sha :4678 → sha 异 :4681 → mt 侧缺 :4686 → mt 同 :4690 → mt 降 :4693 → 其余 :4697。
- **返回值全域（13 出口）**：`post_read_error/none/None`（:4644、:4679）、`unknown/none/None`（:4649）、`error_pre_snapshot/none/None`（:4653、:4674）、`absent_both/low/False`（:4659）、`vanished/none/None`（:4662）、`new_first_appearance/high/True`（:4667）、`new_write/high/True`（:4682）、`leftover_unchanged/medium|high/False`（:4687/:4691）、`rewritten_same_content/low|medium/True`（:4694/:4697）。`usable_as_crash_evidence` 恒 False（:4625/:4631）。

### 调用链（pre 快照的实流来源）

- 全模块 `_pre_freshness_snapshot`/`pre_freshness_snapshot` **写点仅两个**（P0a4 AST 实证，out:46-48）：`:6528`（AnnAssign，try 之前预初始化 `None`，:6526-6527 注释明言 None=未采集）与 `:6623`（Assign，= make_pre 输出）。传参链：:6623 赋值 → :7367 原样传 `finalize_trip`（唯一调用点，finally 内，:7358；docstring :6138「本函数在 finally 内执行」）→ :6167-6168 原样传 `copy_post_except_evidence` → :4762/:4788/:4804 原样传 classify。
- **实流 pre 取值只有三类**：`None`（:6623 之前异常/早退）、make_pre 输出（absent_confirmed/present/error 三态）、——没有第四种。finalize_trip 形参默认 None（:6137）但唯一调用点显式传参（:7367），不产生额外 None 路。

## 3 第二步：五处逐一实证（构造输入 → 实跑返回 → 矩阵归属）

### W1（矩阵 :2 后件过宽，把 pre任意态 × read_error 错盖成 unknown）

- **实码层（out:159-174，16 格实跑）**：pre 八变体（None/{}/缺state/脏值/显式unknown/absent/present/error）× read_error 两型（exists=None / exists=True）→ **16/16 全部 `verdict='post_read_error' conf='none' is_new=None`**。矩阵 :2 对「未采集四变体 × read_error」声称 unknown ⇒ 错盖实码坐实（out:159-166）。
- **输入可达性（实流）**：
  - post.read_error 可产：写点 :4786 唯一（out:41）；P3 C1/C2/C3 实跑 copy_post 逼出 read_error 并由 Recorder ERROR 行 + FRESHNESS 行落地（out:189-191 等）。
  - pre=None 可产：P0a4 证全模块仅两写点（out:46-48）；:6528 的 None 在 :6623 之前的任何异常/早退下保留，finalize 在 finally 仍被调（:7358）⇒ copy_post 收 None。
  - **精化（对评估口径的收窄）**：{}/缺state/脏值 dict 实流**不可产**（无第三写点、make_pre 输出 state 恒四态之一）；显式 unknown 亦不可产（P4 out:153）。故 W1 的**实流可达子集 = (pre=None × read_error)**——「只要 post 读失败」对 classify 输入域成立，但对实流还需 pre=None 这一半。
  - **组合无代码守卫**：pre=None 与 read_error 两半正交（copy_post 不检查 pre 是否 None 才允许失败——C 型异常路径 :4773 对任意 pre 生效；P1 out:159-160 直调证实）。
- **判定：可达（实码错盖成立）**，但实流触发是三条件叠加（见 §4）。

### W2（矩阵 :4 无跑后限定，error × read_error 错盖）

- **实码层（out:179-181）**：pre=error（**真实 make_pre 产物**，Path(None)→TypeError→error，out:147）× read_error → `verdict='post_read_error' conf='none' pre_state='error'`；对照组 error × 跑后无件 → `error_pre_snapshot`（out:180，矩阵 :4 在该格 ✓）。矩阵 :4 对 read_error 格声称 error_pre_snapshot ⇒ 错盖坐实（out:181）。
- **输入可达性（实流）**：两半各有实产路径——pre=error：make_pre 在 :6623 对载体 except.txt 的 exists/stat/sha256_file 抛异常（P4 实跑 4 类输入产 error，out:146-148/151）；read_error：P3 C1-C3 实跑产出。classify 分支序保证两态同现时 read_error 先截（out:26-28）。
- **判定：可达（实码错盖成立）**。

### O1（absent_confirmed × read_error 完全无行）

- **实码层（out:169-170 直调 + out:187-203 经 copy_post 实跑）**：pre=absent_confirmed（真实 make_pre 产物，out:144）+ 复制异常三型——
  - C1 read_bytes 被锁 PermissionError：copy_post 外抛、ERROR 三行落地、classify 实收 `post_exists=None + read_error` → `post_read_error`（out:187-191）；
  - C2 读成功 + dst.write_bytes 磁盘满：classify 实收 `post_exists=True + read_error` → `post_read_error`（out:193-197）；
  - C3 src.exists() 自身炸：→ `post_read_error`（out:199-203）。
- **矩阵归属（静态实读 MATRIX_ROW5_COUPLING.md §3.2 :74-84 匹配键）**：exists=None 型——:5 要 present、:6 要「跑后在场」、:7 要「跑后无件」，三者皆不满足 ⇒ **无行（孤儿）**；exists=True 型——:6 字面「跑前确认无件 + 跑后在场（存在性硬证）」被满足 ⇒ 会 claim new_first_appearance/high，实码 post_read_error ⇒ **误配（O1′）**。
- 对照组：C4（跑后无件）→ absent_both/low/False（:7 ✓，out:205-209）；C5（跑后在+复制全成功）→ new_first_appearance/high/True（:6 ✓，out:211-215）。⇒ O1 只在**复制失败**时出现，正常流不触。
- **判定：可达（孤儿/误配格实流可产）**。C5 注：其 F 字段落盘观测点（:4804-4815）完整跑完之后，:4821 `sha256_file(假叶对象)` 外抛 TypeError 属脚手架边界（真实 sha256_file 哈希不了假对象），不影响 C5 结论（out:211-215 已记录 verdict/conf/is_new）。

### O2（显式 unknown × 跑后在 无行——评估说实流不可达）

- **不可达证明（三重）**：
  1. **AST 控制流（out:14-20）**：make_pre 的 state 赋值仅 :4599/:4603/:4610 三点 + 初值 :4589；return 仅 :4601/:4613，且每个 return 前必有覆写（:4601←:4599；:4613←:4603 或 :4610）——**不存在保持初值 "unknown" 的返回路径**。
  2. **运行期 sweep（out:144-153）**：8 类输入实跑，输出域 = {absent_confirmed, present, error}，显式 `'unknown'` 不在输出域（out:153 = False）。
  3. **传参链封闭（out:46-48）**：实流 pre 仅两写点（None / make_pre 输出），无第三方可注入显式 unknown dict。
- **classify 直调对照（out:229）**：手造 fixture `{"state":"unknown",...}` × 跑后在 → `verdict='unknown'`——该格在 classify 层良定义，但**只能 fixture 域构造，实流不可产**。
- **边界澄清**：折叠 unknown（pre=None）× 跑后在 是实流可达的（早退前失败 + 跑后在场），但它落 :2 行且 :2 对非 read_error 格声称 unknown 与实码一致（out:231 对照）→ 无误配；O2 专指**显式 unknown 态值**，其不可达性成立。
- **判定：不可达（评估判断成立，实证）**。

### W3（present × 缺 pre.sha × read_error——:13 与 :5 同抢；评估说实流不可达）

- **不可达证明（三重）**：
  1. **AST + 源码（out:14-20、out:62-81）**：present 路线性必经 `:4607 snap["sha256"] = sha256_file(p)`；sha256_file（候选:431-437，out:54-60）单一返回非空 hexdigest，任何读异常上抛 ⇒ 整体 `state="error"`（:4610）——**「present 且 sha 缺失」不在 make_pre 输出域**。
  2. **运行期（out:145、out:154、out:220-221）**：真实在场文件 → present + 64 位非空 sha（与 hashlib 直算一致）；sha 会炸的输入（Path(None) 等）→ 整体 error 而非 present缺sha。
  3. **传参链封闭（out:46-48）**：pre 原样透传，途中无人清空 sha 字段。
- **fixture 层同抢格实跑（out:222-224）**：手造 present缺sha × read_error → `post_read_error`（**:5 先截，:13 同抢落空**——码序 2 先于码序 7，out:26 vs out:31）；present缺sha × 无 read_error → `error_pre_snapshot`（:13 在 fixture 域内正确）。⇒ 「:13/:5 同抢」只在 fixture 域存在，且即便在该域实码也恒由 :5 的 verdict 赢；实流两格皆不可达。
- **判定：不可达（评估判断成立，实证）**。

## 4 第三步：可达缺陷的最短触发链（真机现实性评级——推理，零真机未实测，如实标注）

1. **O1（最现实的可达缺陷格）**：一趟真实 trip → 跑前快照确认无件（:4598-4601）→ 跑中游戏写出 except.txt → 收尾 copy_post 时该件**读/复制失败**。两个子型：
   - C1/C3 读侧：except.txt 仍被未死透的游戏进程握有句柄（`terminated_ok=False` 路径下 finalize 照跑，:7360）、AV/索引器瞬时锁、ACL 异常 ⇒ `read_bytes`/`exists` 抛 PermissionError/OSError；
   - C2 写侧：`out_dir`(=WORKDIR) 磁盘满或 AV 拦截新建副本文件 ⇒ `dst.write_bytes` 抛 OSError。
   **评级：罕见**。两半各自独立现实（进程句柄残留与磁盘满是 Windows 常见故障），但要求「本趟恰好新产 except.txt（即恰好是要保证据的崩溃趟）+ 恰好复制失败」双重小概率叠加。
2. **W2**：pre 侧 make_pre 在 :6623 对载体 except.txt 采集失败（AV 瞬时锁 / ACL / 路径异常 ⇒ P4 所证 error 态）+ 同趟收尾复制又失败。同一持续根因（句柄被占/ACL 损坏横跨 pre 与 post 两个时点）可一次造成两半。**评级：罕见**。
3. **W1**：需三条件叠加——:6623 之前异常/早退（pre 停在 :6528 的 None）→ finalize 仍在 finally 被调（:7358）→ 载体 except.txt 在场且读取失败（早退趟通常无新产 except.txt，需外来残留/外部投放 + 锁/ACL）。**评级：近乎不可能**（比评估口径「显然可达」收窄；W1 缺陷的实码错盖仍成立，但实流触发格就是最窄的那格）。
4. **O2 / W3**：不可达，无触发链。

## 5 第四步：可达性汇总表

| 缺陷 | 评估口径 | 本轮实证 | 证据 | 触发条件现实性 |
|:--|:--|:--|:--|:--|
| W1 (:2 错盖) | 输入显然可达（只要 post 读失败） | **可达，收窄**：实流可达子集 = (pre=None × read_error)；{}/脏值/显式unknown 变体为 fixture 域 | 实码 16/16 格 PRE（out:159-174）；read_error 写点唯一 :4786（out:41）；pre 写点仅 :6528/:6623（out:46-48） | 近乎不可能（三条件叠加；评级为推理） |
| W2 (:4 错盖) | error × read_error 实码落 post_read_error，需验 | **可达，实证成立**：error×read_error → PRE（out:179），error×无件 → EPS 对照（out:180） | P2 + P4（4 类输入实产 error 态）+ P3（C1-C3 实产 read_error）+ 分支序 out:26-28 | 罕见（同根因双时点；评级为推理） |
| O1 (absent×read_error 无行) | 实流可达：make_pre absent → copy 异常 :4786 | **可达，实证成立**：C1/C2/C3 经 copy_post 实跑全产 read_error → PRE；exists=None 型孤儿、exists=True 型被 :6 字面误claim（O1′） | out:169-170、out:187-203；矩阵匹配键 MATRIX_ROW5_COUPLING.md:74-84 静态实读 | 罕见（句柄残留/AV 锁/磁盘满；评级为推理） |
| O2 (显式unknown×跑后在 无行) | 实流不可达：make_pre 永不产显式 unknown | **不可达，实证成立** | AST 控制流 out:14-20 + 运行期 sweep out:153（False）+ 传参链封闭 out:46-48 + fixture 直调对照 out:229 | 不适用 |
| W3 (present×缺pre.sha×read_error，:13/:5 同抢) | 实流不可达：make_pre 在场必算 sha | **不可达，实证成立**；且即便 fixture 域，:5 亦恒先截（同抢落空） | AST out:14-20 + sha256_file out:54-60 + 运行期 out:145/154/220-221 + fixture 同抢格 out:222-223 | 不适用 |

## 6 第五步：已实证 vs 未验

**已实证（本轮实跑/AST 实证）**：
- 三函数输入/输出域与分支码序（out:14-48、out:54-139）。
- make_pre 输出域不含显式 unknown、不含 present缺sha（out:144-154、out:220-221）。
- classify 对 pre 八变体 × read_error 两型 16/16 落 post_read_error（out:159-174）；error×read_error → PRE 而 error×无件 → EPS（out:179-180）。
- copy_post 三类异常（读锁/写满/exists 炸）实产 read_error 且 ERROR 行+F 字段落盘+上抛（out:187-203）；src_missing 与正常复制对照格 :7/:6 取值正确（out:205-215）。
- pre 快照全模块仅两写点、传参链原样透传（out:46-48）；指纹 7/7 MATCH（`_mr_fingerprint_out.txt`）。

**未验（如实登记，不补造）**：
1. 真机触发概率（§4 三条「评级」全部为**推理**——零真机纪律下未实测进程句柄残留/AV 锁/磁盘满的真实频率）。
2. (pre=None × read_error) 未做 main→finally **整链**实跑（main() 会触真机操作，禁跑）；实证形态 = 两半各自实产（out:159-160 直调 + out:46-48/:7358 链路）+ 组合无代码守卫的**组合论证**，非整链实跑。
3. `run_guarded_steps` 是否逐项必跑收尾步骤：仅静态实读 docstring（:6157「逐项独立、互不跳过」、:6142 执行序第 1 项）与 :6166-6175 定义，**未展开其实现**。
4. :4816-4825 载体件快照尾段与 `move_out_evidence_and_verify`（:6170）未展开（与五缺陷无涉；矩阵连带评估 §5.5-4 同口径）。
5. 9×9 全格矩阵未重跑（上轮已 72/81 格两轮实跑；本轮只跑五缺陷相关格 + 对照格）。
6. Windows py3.12 `Path.exists()` 把非法字符/ENOTDIR 路径吞为 False 的行为（out:149-150）仅在 py3.12.10 实测，其他 Python 版本未验。

## 7 写域清单（全部落 `lead/matrix_reach_20261109/`，未 commit 未 push）

`_mr_fingerprint.py`、`_mr_fingerprint_out.txt`、`_mr_probe1.py`、`_mr_probe1_out.txt`、`_mr_REACH_EVIDENCE_20261109.md`（本件）。被核九件+母本+两台账零改动。
