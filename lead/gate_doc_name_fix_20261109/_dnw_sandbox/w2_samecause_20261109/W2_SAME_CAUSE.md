# W2 双时点同源检验报告（交付轮）

- 交付件：lead/w2_samecause_20261109/W2_SAME_CAUSE.md（本轮新建，唯一写域内）
- 受核假设：lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md §4.2 条 2（:154）W2 最短触发链中的「同一持续根因横跨 pre/post 两时点可一次造成」，及 :146 表行评级「罕见（同根因双时点；评级为推理）」
- 证据链：撰写轮探针 _w2_probe.py/_w2_probe2.py（实跑输出 _w2_probe_out.txt/_w2_probe2_out.txt、结论件 _w2_conclusion.md）→ 复核轮独立实现复核（verdict=confirmed）→ 本交付轮指纹与行号引用逐条亲验后成文
- 三选一结论（见 §4）：**部分同源**

## 1 目的与边界

**目的（只此一项）**：检验 W2 触发链所依赖的双时点同源假设是否成立——载体 `except.txt` 在 T0（跑前快照 `make_pre_freshness_snapshot`）与 T1（收尾证据副本 `copy_post_except_evidence`）两处读**同一文件**时，能否由**同一个持续根因一次造成两处失败**。结论只允许「同源 / 不同源 / 部分同源」三选一，不许含糊。

**边界（不做什么）**：
- 不判该不该改矩阵（STATE_MATRIX.json 的 A/B 取舍不在本件范围）；
- 不重估其他缺陷（W1/O1/O2/W3 仅作对照引证，不另行裁决）；
- 零真机：不启动 gamemd.exe / ra2loader / YURI.exe，不 taskkill，不读活进程内存；
- 零采样代码：无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析；
- 只读域（b2b_candidate_lf_20261107 / b2b_design_20261106 / matrix_reach_20261109 / matrix_ab_ruling_20261109 / 母本 / 两台账 / STATE_MATRIX.json）一律只读不写；
- 唯一写域 = lead/w2_samecause_20261109/；不 commit、不 push。

**方法**：受控文件操作实验全部落唯一写域（icacls deny-ACE、share-mode=0 独占句柄、临时件建删，用后清理——_w2_probe_out.txt §I 收尾清理记录）；被测函数经 importlib 静态装载真代码（零改动，_w2_probe_out.txt:24-27 `module loaded: _qc151_cand_w2check`），构造字典输入调用；候选模块顶层仅 `if __name__ == "__main__":` 守卫（:7532-7533 本轮实读），静态装载零文件 IO。

## 2 上游指纹（九件）与两时点操作对象、依赖项清单

### 2.1 九件指纹（本轮独立实算）

本轮实跑命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/w2_samecause_20261109/_w2w_fp9.py`（exit=0，输出 TOTAL 9/9 MATCH），与编排方基线、撰写轮 _w2_probe_out.txt:12-21（B 节 9/9 MATCH）、复核轮 _w2v_fp.py 三方一致：

| # | 文件 | SHA256 | 字节 |
|---|------|--------|------|
| 1 | lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py | ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2 | 412759 |
| 2 | lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md | cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6 | 27825 |
| 3 | lead/matrix_reach_20261109/_mr_REACH_EVIDENCE_20261109.md | 67d0fc90ceae277f23d43f80484da9445a6385994752a882d04a8517809f10e9 | 20820 |
| 4 | lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md | 0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31 | 36851 |
| 5 | lead/b2b_design_20261106/STATE_MATRIX.json | 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016 | 3558 |
| 6 | lead/b2b_design_20261106/B2B_DESIGN.md | 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf | 66735 |
| 7 | out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py | 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636 | 399508 |
| 8 | lead/PENDING_DECISIONS.md | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 52419 |
| 9 | lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759518 |

### 2.2 两时点操作对象（行号均本轮实读核验）

**T0 = make_pre_freshness_snapshot（:4580-4613，调用点 :6623-6624）**
- 源对象：`carrier_dir / "except.txt"`（:6624）；**纯只读零写**：`exists()`（:4598）→ `stat()`（:4602-4606）→ `sha256_file`（:4607 → :431-437 `open(p, "rb")` 流式读）；
- 时序：backup（:6619）之后、launch（:6701 `launch_direct` → :1114 `Popen(..., cwd=str(carrier_dir))`）**之前**——T0 时游戏进程**未启动**；
- 异常出口：:4608-4612 捕获 ⇒ `state="error"`（`error`/`traceback` 留痕，不降级）；
- 载体目录 = 本趟 create_isolated_carrier **排他新建**：:5153 `carrier_dir = trip_root / f"c_{stamp}_{os.getpid()}"`、:5154 `os.mkdir`（已存在即抛 ⇒ 不复用旧件），:5163 登记 `TRIP_CARRIER["dir"]`；载体根 = `WORKDIR / "ct"`（:6555-6557）。

**T1 = copy_post_except_evidence（:4701-4826，finalize 第 1 项 :6166-6168 调用，先于 restore_carrier）**
- 源对象：`src = carrier_dir / "except.txt"`（:4716）——finalize 传入的 carrier = `fin_carrier = Path(TRIP_CARRIER["dir"])`（:7325，:7358-7367 传入）＝ **T0 读的同一新建载体**；
- 读侧：`src.exists()`（:4756）、`read_bytes`（:4766）、`stat`（:4767）；写侧：`dst = out_dir / except_post_*.txt`（:4771-4772，out_dir=WORKDIR，:7359）——读与写**同在 :4755-4772 一个 try 内**，任一异常 → ERROR×3（:4777-4785）→ `read_error`（:4786）→ classify（:4788）→ `raise`（:4790）；
- 时序：T1 前游戏已被 terminate_owned_process 终止并确认（:7307 → :1181-1235；:1199「返回值 = **进程退出是否已由本趟句柄确认**」）；仅 term_ok=False（:7311/:7314-7318 记收尾失败）时 finalize 照跑（:7358 在 finally 内）。

### 2.3 同一文件判定

**同一文件：是。** 同一路径串（carrier_dir/"except.txt"）、同一目录（:7325 从 TRIP_CARRIER["dir"] 取回 :5163 登记的同一目录）、同卷同树（载体在 WORKDIR/"ct" :6556，out_dir=WORKDIR :7359）；游戏 cwd=carrier_dir（:1114），except.txt ∈ CARRIER_FILES（:213-214）。**同一句柄：否**——两时点是两次独立 open，仅共享该路径串上的读面依赖。

### 2.4 依赖项清单（两时点对照）

| 依赖项 | T0 make_pre | T1 copy_post |
|---|---|---|
| 源路径串合法 / 存在性 stat | ✓（:4598/:4602） | ✓（:4756/:4767，同串同对象） |
| 源读数据 ACL | ✓（sha256_file open，:4607→:434） | ✓（read_bytes，:4766）——同一条 |
| 源共享模式（他方独占拒读） | ✓ | ✓ |
| AV 对该路径的扫描策略 | ✓（新建载体件） | ✓（崩溃写后件）——策略持续同源，锁事件两次独立 |
| 载体卷可用 | ✓ | ✓（同卷） |
| 游戏进程句柄 | ✗（未启动，:6623<:6701） | △ 仅 term_ok=False 分支（:7314-7318，finalize 照跑 :7358） |
| out_dir 存在 / 写 ACL / 磁盘空间 / 新建副本 AV 扫描 | ✗（零写） | ✓（:4771-4772，**T1-only 整块**） |

## 3 六类根因逐项判定（R1–R6）

探针证据均出自唯一写域实跑（撰写轮 `_w2_probe_out.txt`，python -I -X utf8，exit=0；复核轮 `_w2v_probe1.py` 14/14 PASS、`_w2v_probe2.py` PASS 独立复现）。异常属性口径如实记：实测均为 **PermissionError，errno 13**；`winerror` 属性随异常形态呈 13（_w2_probe_out.txt:50/:52）或 None（_w2_probe2_out.txt:3-5；复核轮同），两探针对「读被拒」的判定一致。

- **R1 游戏进程独占句柄：只能致 T1，不能致两处。** T0 调用点 :6623 先于 launch :6701（本轮实读 main 顺序），且载体每趟 :5153-5154 排他 mkdir 新建 ⇒ T0 时无任何游戏进程、无旧句柄可指；T1 侧游戏句柄仅在 term_ok=False 分支成立（:7304-7318，finalize 照跑 :7358）。探针 G 机理演示：share-mode=0 独占句柄持有期间 exists/stat 通过、open 被拒（_w2_probe_out.txt:77-81，两时点同拦机理成立）——但现实时序上结构性只能命中 T1。
- **R2 ACL 拒读：能同时致两处——唯一完整桥接根因（探针实锤）。** 探针 E：deny-(RD) ACE 下 T0 真 make_pre → `state="error"`（exists=True，sha256_file open PermissionError，_w2_probe_out.txt:51）；同一 ACE 持续到 T1 真 copy_post → PermissionError → ERROR×3 → FRESHNESS verdict=`post_read_error`/conf=`none`/is_new=None（:52-54）＝ **一因双时点命中 W2 格**（pre=error × read_error）。探针 F：deny-R（拒全部读含属性）同结果（:66-70），py3.12.10 对该形态 exists() 不吞（exists=True）。探针 2（_w2_probe2_out.txt:1-8）：目录级 (OI)(CI) deny-RD 下文件删除重建后新件仍拒读 ⇒ **继承型 ACE 跨「游戏重建 except.txt」持续**；icacls /remove:d 后恢复可读（:7-8）。文件级 deny 是否跨重建取决于游戏对 except.txt 是追加还是重建——未验（零真机）。
- **R3 AV 实时扫描：部分同源形态，非完整同源。** 对该路径的扫描**策略**（配置）持续 ⇒ 形式上同源；但**锁事件**是两次独立瞬时竞态（T0 新建载体件扫描窗口 × T1 崩溃写后扫描窗口），不是同一持续根因一次造成。零真机下无法实证 AV 行为——未验。
- **R4 磁盘满：只能致 T1。** make_pre :4589-4607 无任何写调用（本轮实读，纯只读）；磁盘满是写侧资源。探针 H 实证写侧失败独立落 read_error：out_dir 指向普通文件 → dst 写 FileNotFoundError → verdict=`post_read_error`（_w2_probe_out.txt:87-90）——T1-only 源足以独立致 T1，但碰不到 T0。
- **R5 路径过长 / 非法字符：不能触发 W2 链（两条腿都点不着）。** 路径串虽同（形式上同源），但探针 D 实测 py3.12.10 下非法字符（winerror 123）/ ENOTDIR（winerror 3）/ 超长>260（winerror 123）三类 `Path.exists` 全吞为 False → 真 make_pre 全落 `absent_confirmed`，**不产 error 态**（_w2_probe_out.txt:32-39）；T1 侧对应走 src_missing 早退 :4756-4764（连 read_error 都不落，F 字段 verdict=src_missing 分支 :4762-4763）。连评件括号内「路径异常」应剔除。与连评件自身记录同口径：MATRIX_DEFECT_REACHABILITY.md:115（8 类 sweep，absent_confirmed 含非法字符/ENOTDIR）、:184（未验登记：仅 py3.12.10 实测，其他版本未验）；分支序旁证 _mr_probe1_out.txt:25-28（read_error :4643 先于 error :4652，与本轮实读 :4643/:4652 一致）。
- **R6 进程退出句柄未释放：不能致两处。** Windows 进程终止即内核关闭其全部句柄（OS 语义）；:1199 明示「返回值 = 进程退出是否已由本趟句柄确认」——term 成功后 T1 读侧已无本趟进程句柄可残留；T0 时本趟进程未启动。复核轮活体实验独立佐证：独占句柄由子进程持有、两时点同拦，持有进程自退出后文件即恢复可读（`_w2v_probe2.py` PASS）。残余形态 = 游戏僵死未退 ⇒ 并入 R1 的 term_ok=False 分支，仍 T1-only。

## 4 同源性三选一结论与依据 + 概率重估

### 4.1 三选一结论：**部分同源**

（三选一限定：同源 / 不同源 / 部分同源。不是「可能同源」。）

**判「同源」不成立的依据**——两时点依赖项清单不对等（§2.4）：①T1 的 try 块另含整块写侧依赖（out_dir 存在/写 ACL/磁盘空间/新建副本 AV 扫描，:4771-4772），make_pre 零写完全不经——探针 H 实证写侧失败同样落 read_error，属 T1-only 源；②连评件示例成因「文件被游戏进程独占句柄」（R1）在 T0 结构性不成立；③R4/R6 均只能致 T1。若判全同源，等于宣称 T1 写侧与游戏暴露依赖也由「同一持续根因」覆盖——与代码事实不符。

**判「不同源」不成立的依据**——存在实锤桥接子集：两时点对**同一源路径串**各做一次独立 open 读，源读面依赖（路径串、存在性 stat、读数据 ACL、共享模式、AV 对该路径策略、载体卷）完全重叠；其中「源读面**持续阻断**」类根因（目录继承 deny-ACE、AV 对该路径持续拦截、持续性独占句柄）确实一因双时点命中——探针 E/F 用真 make_pre + 真 copy_post 复现成功（同一 deny ACE 横跨两时点：T0 state=error × T1 read_error=post_read_error），探针 2 证明目录继承形态跨文件重建持续。判不同源等于否认已复现的桥接——与实跑证据不符。

**⇒ 部分同源**：同源面 = 同一源读面上的持续阻断；不同源面 = T1 写侧、游戏暴露、两次独立的 AV 瞬时锁事件、以及两腿都点不着的路径异常（R5）。

### 4.2 概率重估

任务规则「若不同源则概率重估」的触发条件核对本轮**不成立**（结论为部分同源，非不同源），故不做全面概率重估。但 :146 评级「罕见（同根因双时点；评级为推理）」按其现措辞（括号内含「AV 瞬时锁/ACL/路径异常」）**偏高**，需随 §5 修正措辞收窄后方可维持。分层量级（**全部为量级推理，零真机未实测——未验**）：

1. 桥接子集「源读面持续阻断」：目录继承 deny-ACE 属**环境常量**——载体每趟由脚本新建、默认继承 ACL，出现 deny 即每趟必现而非随机罕见事件；台账仅 GOAL_THREE_TARGETS_20261018.md:9173-9174 以测试覆盖枚举命中 `post_read_error`/`error_pre_snapshot`，未见真机趟记录（**未验硬证明**）⇒ 现环境大概率 = 0。AV 对该路径持续拦截 ~1e-5–1e-3/趟。「罕见」仅对此子集成立。
2. 「AV 瞬时锁」双击（连评件括号内成因之一，非持续根因）：需 T0/T1 两次独立竞态，单时点 p~1e-3–1e-2 ⇒ 双击 ~1e-6–1e-4/趟，低于「罕见」1–2 个量级（极罕见档）。
3. 不同源反事实（两个独立罕见因，如 T0 AV 瞬时锁 × T1 磁盘满/句柄残留）：~1e-7–1e-5/趟（极罕见档）。

**对 W2 本体的影响**：W2 是文档标签误配——STATE_MATRIX.json:4 的 condition「跑前采集抛异常（snap.error 非空）」无跑后限定 ⇒ error × read_error 格被 :4 声称 `error_pre_snapshot`，实码 classify 返回 `post_read_error`（read_error 先截 :4643，error 后截 :4652）；RULING_MATRIX_AB.md:50/:60 已判「两出口独立可同现、机制正交、活性误配、取值层无损」。探针 E 的 S1 组独立复现该误配成立。**频率修正影响触发优先级，不推翻误配成立性**——本件不改判 W2 是否成立，也不改判 A/B 取舍。

## 5 复核回件、W2 链描述修正建议、未改任何文件声明、未验项

### 5.1 复核回件（verdict 如实转录）

复核轮以独立实现复核本检验：指纹 9/9 MATCH（其 `_w2v_fp.py` 实算，与编排方基线及撰写轮绑定行逐字节一致）；依赖清单实读无误；六类根因独立探针 `_w2v_probe1.py` 14/14 PASS、`_w2v_probe2.py` PASS（E：文件级 deny-(RD) 下真 make_pre=error + 真 copy_post 抛 PermissionError→FRESHNESS verdict=post_read_error/pre_snapshot_state=error——正是 W2 格一因双时点；E2：目录继承 deny 跨删除重建持续；探针2：活体独占句柄双时点同拦且持有进程自退出后恢复可读 ⇒ R6 不能桥接；R5 exists() 全吞；R4 T1-only；R1 T0 结构性不成立）；量级段全标注推理/未验；台账 grep 旁证其已复跑（post_read_error/error_pre_snapshot 仅 GOAL :9173-9174 两行命中）。两处**非实质瑕疵**（不改变判定，本轮如实记并已在 §3/§2.2 相应位置更正口径）：(a) 撰写轮回件写「winerror 13」，复核实测 PermissionError errno=13、winerror=None——数字对、属性名随异常形态有二义（本报告 §3 已如实记两种形态）；(b) 撰写轮回件所引 out:26/28、out:144-153、out:187-203 系可达性轮 `_mr_probe1_out.txt` 行号（非撰写轮自身探针件），复核逐一实读相符——本报告引用时已标注归属（如 :154 链文内「out:26 vs out:28」经本轮亲读核验即 _mr_probe1_out.txt:26/:28 的 classify 分支序）。

复核 verdict = **confirmed**（按规则仅 refuted/partial 才标 unconfirmed；本件不适用）。

**复核绑定行（本轮 _w2w_fp9.py hashlib 实算，三方一致）**：

两时点代码本体 lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py：
被核对象 SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759

W2 链载体（受核对象）lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md：
被核对象 SHA256 = cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6，字节数 = 27825

### 5.2 对 MATRIX_DEFECT_REACHABILITY.md W2 链描述的修正建议（只描述，不改那件）

W2 链（:154）需把「同一持续根因」收窄为「**源读面（载体 except.txt 的同一路径读面）上的持续阻断**」，并修正/剔除括号内两个成因。措辞提案：

> make_pre 在 :6623 对载体 except.txt 采集抛异常（源读面持续阻断：ACL 拒读〔目录继承 deny-ACE，跨文件重建仍持续——写域探针实证〕/AV 对该路径持续拦截 → error 态；AV 瞬时锁非持续根因，双时点命中需两次独立竞态；路径异常在 py3.12.10 实测〔非法字符/ENOTDIR/超长〕均被 exists() 吞为 absent_confirmed，不产 error 态）+ 同趟收尾复制对同一源路径再失败（同一 ACE/拦截持续 ⇒ 一因双时点；游戏句柄〔T0 未启动、term 成功即句柄随进程终止被内核关闭〕与磁盘满〔仅写侧〕均只在收尾时点成立，不能单独桥接）→ read_error 先截（out:26 vs out:28）→ :4 声称 error_pre_snapshot 与实码 PRE 不符。

:146 评级格建议注记：「罕见」仅限**源读面持续阻断**子集（deny-ACE 为环境常量、台账可证伪；AV 持续拦截 ~1e-5–1e-3）；AV 瞬时锁双击 ~1e-6–1e-4、两独立因 ~1e-7–1e-5（均极罕见档；全部为推理、未验）。

### 5.3 未改任何文件声明

本轮（交付轮）未修改、未追加、未覆盖任何既有文件：只读域四目录 + 母本 + 两台账 + STATE_MATRIX.json 零改动——凭证①九件指纹本轮实算 9/9 逐字节一致（_w2w_fp9.py，§2.1）；凭证②`git log -1` HEAD 仍为 26574589aa8401e8f3f2934680a1ea7109bafa2d，`git status --porcelain` 对四个只读目录仅显示未跟踪（??）无修改标记；两台账的 MM 状态系本会话开始前既有（相对 HEAD 的既有改动），与指纹对编排方基线 9/9 一致并读即证本轮未触碰。本轮仅新增写域件：_w2w_fp9.py（指纹探针）与本件 W2_SAME_CAUSE.md。未 commit、未 push。

### 5.4 未验项（如实登记，不补造）

1. 游戏对载体 except.txt 是**追加**还是**删除重建**——零真机不允许验证；目录继承 deny-ACE 已实证跨重建持续（_w2_probe2_out.txt），文件级 deny 仅在追加/不重建场景可证实持续。
2. AV / ACL / 磁盘满在本环境的**真实触发频率**——零真机未实测，§4.2 所有量级均为推理。
3. 「本机现环境无 deny-ACE」仅有台账 grep 旁证（GOAL :9173-9174 仅测试覆盖枚举命中），未对现环境 ACL 做全量枚举。
4. py3.12.10 之外的 Python 版本 exists() 对非法字符/ENOTDIR 的吞异常行为（MATRIX_DEFECT_REACHABILITY.md:184 自记同此未验）。
5. AV 对纯文本崩溃件的真实拦截行为与策略持续性（零真机下无法实证）。
