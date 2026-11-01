# E12_CANDIDATE_SELFTEST_20261029.md — E1+E2 合批候选驱动件离线自证报告

**日期**：2026-10-29 · **来源**：GOAL-3T X 退出线（候选件离线制作轮）
**性质**：离线制作+自证。本轮**零真机、零发射、零游戏启动、零扩 Hook、零状态写、零网络**。
发射永远等用户对 D-11 的批准（裁决权=用户）；本件 `--live` 无 `--approved` 恒 rc=3（实测在盘）。
**写域纪律**：本轮新建且仅新建本报告涉及的三件（两个驱动/自检件+本稿）；
两个终钉件（v2 / earlyclose）、TRIP_INDEX、台账、设计件、游戏目录、冻结母本=**零字节触碰**
（运行前后哈希复验在盘，见 §2/附录 G 组）。

---

## 1. 交付件与哈希（sha256，本轮终值）

| 件 | 绝对路径 | sha256 | 尺寸 |
|---|---|---|---|
| E12 候选驱动 | `D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\_drive_c2_x_e12.py` | `f9d3f36a543d995ffd36d1305afb2b9c0336b6a40111e9a37e168b725d9e89be` | 31,492 B |
| 离线自检套件 | `D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\_drive_c2_x_e12_selftest.py` | `731dedfc2c09c11e9265aa9a7280fb9395e3da8831d3949f57c56d4d24bfcfb8` | 44,061 B |
| 本自证报告 | `D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\E12_CANDIDATE_SELFTEST_20261029.md` | （交付后由 Leader 复算登记） | — |

**复用母版（只读 import，发射前须复验）**：

| 母版 | sha256 钉值 | 本轮实测 |
|---|---|---|
| `_drive_c2_x_earlyclose.py` | `2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1` | 命中（自检 H-00/G 组双点复验） |
| `_drive_c2_x_probe_v2.py` | `6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9` | 命中（同上） |

**import 前置哈希门**：E12 件在模块级（任何 `import _drive_c2_x_probe_v2/_drive_c2_x_earlyclose` 语句之前）
执行 `verify_frozen_masters()`——两母版实读 sha256 对钉，不符/不可读⇒`RuntimeError` 拒载；
自检件同样先验再 import（不符⇒rc=4）。新件不 import 任何未验哈希的旧件。

## 2. 验收条件逐项回执

| 验收项 | 结果 | 证据 |
|---|---|---|
| 自检套件全绿且输出落报告 | **82/82 红=0 ALL-PASS**（rc=0） | 附录 A 全文 |
| live 无授权 rc=3 实测 | **rc=3** | 附录 B；自检 E-06 子进程复测 |
| `--selftest` rc=0 实测 | **rc=0** | 经驱动件 `--selftest` 委托入口与直接运行双测（E-07 另证 `--live --selftest` 亦走自检、自检优先于 live 闸） |
| 不 import 未验哈希旧件 | 通过（模块级前置门+自检件门+子进程加载链） | §1；自检 E-02/E-03（钉值不符/不可读⇒RuntimeError） |
| E2 轴语义=B 线 §9 A4 判读规则 | 通过：spin×在位⇒P1 第一候选 / spin×不在位⇒丁 / ≈0⇒阻塞族（E3 另裁侧） / 不可读·混合·读败⇒不冒充 | 自检 A-06/A-12/B-01/B-05/D-01..D-10 |
| git 足迹仅三新文件 | 通过（`??` 仅三件；他线 M 件 mtime=10-25 非本轮操作；临时 pyc/趟目录已清理） | 附录 C |
| 附加：`--preflight` 真 OS 只读 | **rc=0 全过 10 项**（v2 预检 7 项+终钉复验+源 ini 钉+BOOT 读数） | 附录 B |

## 3. 设计→实现映射（协议母版纪律的复用面）

- **E1 协议=终钉 import 复用**：`HOLD_AFTER_WINDOW=E.HOLD_AFTER_WINDOW(6.0)`、`WATCH_S=E.WATCH_S(120.0)`
  （单一来源=早窗件常量）；载体目录/命名、`carrier_identity_ok`、路径长闸、建后断言空、
  `_precheck_shas`、`apply_bail_mode(1,"explicit1")`（Guard=1+Bail=1 全同 P3e）、
  hold 期 `phase_sentinels`、PostMessageW 唯一投递（不点确认）、`screenshot_best_effort`、
  `finalize` 两阶段、三态读 `tri_read_u32`——**全部 import 冻结件函数/OPS seam，零复制改动**。
- **E2 轴**（B 线 §4-E2 + §9 A4）：主循环（0.1 s 节律，close_rows 行形态与早窗批逐键同形）检测
  `exitstate==1` 后切 1 Hz 慢采样，逐秒落四轴：
  1. **CPU**：`GetProcessTimes`（kernel+user，100 ns 单位差分⇒核秒），句柄权沿用
     `0x0400|0x0010|0x100000`（=PROCESS_QUERY_LIMITED_INFORMATION|QUERY|VM_READ 组合，**未申请新权**；
     Win10+ 该权覆盖 GetProcessTimes，与 B 线 §4-E2「既有句柄权内完成」一致）；
  2. **hook6**：`BAIL_SITE=0x6BE0E1` 六字节现读 vs 锚 `e91a1f941790`（早窗趟 hold_tl 实测×3 同值；
     台账 §453「hook 实况×3」；B 线稿 §9 BAIL_SITE 六字节）；三态=present/absent/read_fail（读败带
     rpm/vquery 细节，**不吞、不冒充不在位**）；
  3. **ws_kb**：`GetProcessMemoryInfo` 既有通道；
  4. **可见窗口枚举**：逐秒在录（补 A 线 R1 挂死期窗面盲区），并以闩时刻窗集为基线判「新窗」；
  闩+30 s 加一张截图（tag=`latch_plus_30`）。
  hook6 只读既有字节=**非新 Hook 点、零写入游戏内存**。
- **schema**：`_rec.json` 增 E2 段（`latch_detected/latch_row_index/latch_after_close_s/
  slow_sample_rows/slow_rows_n/hook6_state/hook6_state_counts/cpu_delta_median_s/ws_delta_kb/
  e2_fork_label/e2_summary/stop_triggered/trip_index/boot_ms_at_start/e2_params`）；
  `timeline.json`=`{hold_tl, close_rows, _e2}`——`close_rows` 保持原形态兼容（行键集同早窗批，tick 恒
  int 保 C8 可跑），`_e2` 附加段含 params/latch/slow_sample_rows/summary/stop_triggered。
  每轴读失败态显式落记录（`{"state":"read_fail"/"api_exception",...}`）。
- **通用停止条件**：慢采样期新可见窗（#32770/确认/保存/网络类关键字命中⇒定性交互；任何新窗⇒保守停）
  ⇒ 只留证据（stop_evidence 截图+行记录）停升级动作（不点确认/不丢存档/不断网）；
  `except.txt` 哈希中途变化（30 s 巡检节拍）⇒ 停；跨趟 BOOT（GetTickCount64）变化⇒停；
  预检 fail⇒停；趟非 OK 或触停⇒批次停后续。
- **授权硬闸**：`--live` 无 `--approved` 恒 rc=3（纯函数 `gate_decision` 可分臂测）；`--approved` 单给
  仅透传闸值不自动跑；`--live --approved` 仍须 v2.preflight+E12 附加预检全过才发射；
  `--selftest`/`--preflight` 内置。

## 4. 通道覆盖声明（吸取 A 线 R2 教训：逐通道，禁用「通道面全绿」口径）

E12 趟产物对既有判器 `_judge_batch_arm.py`→`_x_channel_probe_20261027.judge_artifacts` 的
C1–C10/S1/S2 逐通道适用性声明（发射后判读**只可按通道报，不可汇总成「全绿」**）：

| 判器通道 | 对 E12 schema | 声明 |
|---|---|---|
| C1 `_rec 必备键` | **不适用**（要求 `battle_tl_n`——六臂 v2 战斗 schema；早窗协议无 battle_tl，早窗批 P3e×3 当时亦按「单趟协议手工核验」处置，台账 §450 惯例） | 若跑判器 C1 必红，属 schema 代际差非质量问题 |
| C2 verdict | 适用 | E12 verdict∈{OK,PARTIAL,FAIL} 同纪律 |
| C3 投递 post_ok∧err=0 | 适用 | `close_delivery` 行形态逐键同早窗批 |
| C4 win_pid==gamemd_pid | 适用 | 同左 |
| C5 close_rows 全量落盘 | 适用 | `timeline.close_rows` 全量+`close_rows_n` 同值（自检 A-09/F:rhythm 反证同计数形态） |
| C6 battle_tl 数∧pre5=5 | **不适用**（早窗/E12 无 battle_tl/pre5；对应物=hold_tl，计数在 `hold_tl_n`） | 手工核验按 A-09 口径 |
| C7 行含五哨兵轴+wait/code | 适用 | 行键集逐键同形（自检 schema_check 断言） |
| C8 时间轴单调+衔接+跨度 | **部分适用**（单调+跨度有效；pre5/battle_tl 衔接断言因段缺失自然跳过） | E12 另以慢行 t 严格单调+pair_close_row_index 配对自证（自检 A-02/A-09） |
| C9 截图段 pre_close+post_close_end | **适用（E12 起）**——早窗件仅 pre_close（其批 C9 必红）；E12 补 `post_close_end`，另加 `latch_plus_30`/`stop_evidence`（条件） | 有意与终钉件的差异面，见 §6 偏离 1 |
| C10 自然退⇒code int | 适用 | 自检 B-16 |
| S1/S2 PNG 规范/非全黑 | 适用（实现复用 v2 `capture_screen`/h7 写侧口径，未改） | 发射后按判器实跑逐张报 |
| **E2 新四轴（CPU/hook6 三态/慢采样 ws/逐秒窗枚举）+ _e2 段 + stop_triggered** | **既有判器不覆盖（未覆盖声明）** | 覆盖=本自检 82 项（附录 A）；建议发射后判读用 E12 专用手工通道表或另制判器增补（本线不造判器，越写域） |
| Wait 三态（含 WAIT_FAILED） | E12 已补 `wait_error:%d`（早窗件缺该分支） | 见 §6 偏离 2；自检 B-20 |

**覆盖/未覆盖小结**：判器可直接复用的通道=C2/C3/C4/C5/C7/C8(部分)/C9/E12 起/C10/S1/S2；
结构性不适用=C1/C6（早窗 schema 代际）；判器未覆盖的新通道=E2 四轴+闩/慢行/停止/分叉标签面，
仅由本套件自检背书。

## 5. 发射前置清单（D-11 一旦批准⇒预检→发射逐项核对）

1. **D-11 闸值**：用户批准文本在手（本件 `--live --approved` 的 `--approved` 为闸值透传，绝不自动跑）；
2. **两终钉件复验**：`sha256=6afe2711…`/`2e970eec…` 命中（E12 件 import 前已内置自验）；
3. **BOOT 断言**：同开机会话——preflight 读 GetTickCount64（本轮实测读数 107,597,421 ms 仅为记录样例，
   发射时以当场值为准），跨趟比对不等⇒停；
4. **进程零残留**：gamemd.exe/rc4_loader.exe=0（v2.preflight+趟前再核，自检 B-12 反证）；
5. **载体源**：`ra2render.ini` sha16=`27c9a60c55a8a1b4`∧16,496 B 命中（本轮实测命中；趟前复验）；
   gamemd `73201cc021497c95`/loader `ebddf6a61273c874`/c2 DLL `edb9a0cd…`/h7 `d019e8be…`/探针 `b063052c…`/88 件=
   v2._precheck_shas+preflight 七项（本轮 rc=0 全过）；
6. **载体纪律**：批准根内+路径长≤130（本轮实测趟目录载体长=104）+建后断言空+身份闸；
7. **时段预算**：每趟≈137 s 前段+120 s watch+收尾 ⇒ ≈4.3 min；2 趟串行间歇合计预留 15–20 min（D-11 ②）；
8. **串行、单实例、趟目录独立**（命名 `_T1/_T2` 后缀防同秒撞名，见 §6 偏离 4）。

**停止条件**：#32770/确认/保存/网络交互窗或任何新可见窗 ⇒ 只留证据即停；except 哈希中途变化 ⇒ 停；
预检 fail ⇒ 停；闩后出现三类终态之外的新形态 ⇒ 停并单项归档另立（Leader 处置）。
**回退**：配置回滚=零成本（Guard/Bail 只写在载体副本 ini，源母本只读，趟毕载体树 finalize 删除）；
终钉恢复=哈希复验 6afe2711/2e970eec（两母版本轮零触碰，异常时直接重验即用）；
清理=finalize 两阶段（证据先于清扫、异常不吞、残留⇒保留载体报 delete_reason）；
进程清理=终钉 terminate 路径，不新增清理面。
**判读纪律**（沿 D-11/B 线 §4）：只报盘面并趟计数（挂 x/7），禁百分比、禁真率表述；
E2 分叉标签是**首候选提示**，裁决权在 Leader；「CPU≈1 核×hook6 在位」⇒ P1 第一候选可不经 E3 定谳
（§9 A4/9.4），E3 触发面收窄至阻塞族（CPU≈0 侧）。

## 6. 偏离与发现（对 Leader/D-11 判读可能相关）

1. **E12 相对终钉早窗件的三处有意差异**（均不改 E1 盘面读数）：
   (a) 新增 `post_close_end` 截图（使 C9 通道自 E12 批起可适用——早窗批该通道结构性红）；
   (b) watch 循环加闩检测与 1 Hz 慢采样（close_rows 行形态仍逐键同形，仅闩后 sleep 变 1 s ⇒
       闩后 close_rows 行数从 ~1170 降至 ~120+闩前 ~150；**若 Leader 要 close_rows 密度与 P3e×3
       严格可并排，读 _e2 的 pair_close_row_index 配对行即可，闩前段逐行同密度**）；
   (c) exit_kind 补 `wait_error` 三态分支（早窗件缺，v2 有；防 WAIT_FAILED 误标「仍活」）。
2. **CPU 分叉带常量为本件提议**：spin 侧 `median≥0.7 s/s`、block 侧 `≤0.2`，中间带⇒`cpu_ambiguous`
   不硬判。带界可在判读时重算（`_e2.slow_sample_rows[].cpu.delta_s` 逐秒核秒原值全量在盘），
   件不锁死裁决口径。核秒语义=**进程级**（全线程和），P1 单线程满旋≈1.0/秒是其签名形态。
3. **hook6 聚合态词表**（present_stable/absent_persistently/mixed_lost_at_some_row/all_read_fail/
   present_with_read_fail_rows）使「P1 vs 丁」可区分且读败不冒充：混合/读败一律 `undetermined`。
4. **趟目录命名带 `_T{n}` 后缀**（`…_P3e_E12_T1`）——同秒两趟防撞名；TRIP_INDEX 登记面注意。
5. **发现（判器侧，越本线写域不改）**：`_judge_batch_arm` 对早窗 schema 的 C1/C6 恒红源于
   `battle_tl_n/pre5` 键（六臂代际）；台账 §450 已按「早窗 3 趟单趟协议手工核验」处置。E12 批建议
   同法，或由 Leader 授权另制 E12 判器增补（本线未造）。
6. **自检对慢采样节律的定义**：慢行 t 与配对 close_row 同刻（同一主循环 iter 落两笔账），首个慢行
   起于闩行后 1 s ⇒ 闩→首慢行的 CPU 增量覆盖真实 1 s 区间（无假零增量；自检 A-05 基线断言）。
7. **D-11 文本无需改动**：本件参数（窗现+6 s/watch=120 s/Guard=1+Bail=1/四轴+闩+30 s 截图/
   纯被动读既有句柄权/合批 2 趟）与 D-11 ①②及判读增补逐条对齐；唯一提示=§5 时段预算与 `_T{n}` 命名。

## 7. 局限（如实）

1. 自检全替身（虚拟时钟/mock API）：真机节律偏差、h7/GDI 真实截图质量、真实 OpenProcess 权内
   GetProcessTimes 行为，由 `--preflight` 通道只能部分覆盖（截屏/哈希/identity/残留），最终待发射趟产物按 §4 逐通道核。
2. 闩+30 s 截图、except 30 s 巡检在自检中以 2 s/0.5 s 节拍模拟（同一分支不同参数）；真实 30 s 路径未做时长性演练。
3. 交互关键字定性依赖窗标题/类名字面（#32770/确认/保存/confirm/save/网络/network）；措辞遮挡可漏定性——
   但「任何新可见窗⇒保守停」兜底，漏定性不致漏停（自检 C-04/C-08）。
4. CPU 中位数带界（0.7/0.2）是先验设计，非从 P3e 挂死趟推得（该趟无 CPU 轴）；真实读数分布未知。
5. E2 轴仅在闩后激活；未闩趟（边界重开情形）只保留 close_rows/hold_tl（早窗形态），无慢采样——
   与 §4-E2「E2 挂死后置」预案一致。
6. 本件不做臂内自动重试；停即出趟，回退靠 finalize+终钉复验（设计如此，避免升级动作）。

---

## 附录 A：自检套件全文输出（82 项全绿，rc=0）

```text
[OK] H-00     母版哈希自验通过方可 import（早窗件/v2 实读对钉）                             ec=2e970eec43fe… v2=6afe2711136c… hold=6.0 watch=120.0
== E12 候选驱动件离线自检（零真机·零发射·零游戏启动）==
驱动件 sha256=f9d3f36a543d995ffd36d1305afb2b9c0336b6a40111e9a37e168b725d9e89be
[OK] A-01     闩检测切换（exitstate==1⇒latch_detected+行号+相对关窗时刻）
[OK] A-02     慢采样节律=1 Hz（慢行 t 差分≈1.000；闩前 0.1 s 主循环节律在录）
[OK] A-03     闩后慢行≈观察秒数（1 Hz）且明显少于总行数
[OK] A-04     hook6 与锚比对：现读==e91a1f941790⇒present_stable（闩时刻亦录）
[OK] A-05     CPU 增量计算：自旋侧每慢秒=+10^7·100ns=1.0 s；基线=闩时刻读数
[OK] A-06     分叉标签=P1 第一候选（CPU≈1 核×hook6 在位，§9 A4）
[OK] A-07     闩+30 s 加一张截图（tag=latch_plus_30 在录；自检节拍=闩+2 s 模拟）
[OK] A-08     finalize 全套仍跑（a8 清扫 PASS+载体删+双时点证据）
[OK] A-09     输出 schema（_rec E2 段齐全/timeline 三段/close_rows 原形态兼容）
[OK] A-10     窗口枚举通道逐秒独立在跑（补 A 线 R1 挂死期窗面盲区）
[OK] A-11     hold 期沿用早窗件 phase_sentinels（hook6/ws/可见窗随早窗纪律入 hold_tl）
[OK] A-12     spin×hook6 不在位 ⇒ 丁第一候选（§9 A4 分叉二）
[OK] A-13     spin_absent 趟 schema 同形
[OK] B-01     CPU≈0 ⇒ 阻塞族标签（甲/乙-1尾/CRT/丙-阻塞 ⇒ E3 另裁；不冒充自旋）
[OK] B-02     哨兵全读败 ⇒ 三态 read_fail 显式落行、不误判闩
[OK] B-03     hook6 随 hold 期 phase_sentinels 亦显式 read_fail（不吞）
[OK] B-04     hook6 轴单独读败 ⇒ all_read_fail+detail(rpm/vquery)，CPU 轴不受染
[OK] B-05     hook6 三态未决时分叉=undetermined（读败绝不冒充 P1/丁）
[OK] B-06     GetProcessTimes 返回 None（句柄权不足形）⇒ read_fail 显式+cpu_axis_unreadable
[OK] B-07     GetProcessTimes 抛异常 ⇒ api_exception 留痕且趟不崩（异常不吞）
[OK] B-08     CPU 基线读取即败 ⇒ latch.cpu_baseline_state=read_fail（不虚构基线）
[OK] B-09     ws_kb 轴读败 ⇒ 显式 read_fail；hook6/CPU 轴不受染、分叉仍 P1 候选
[OK] B-10     枚举轴异常 ⇒ read_fail 留痕；其余轴照常；不冒充「无新窗」
[OK] B-11     watch 句柄 OpenProcess=0（权限缺失形）⇒ OpenProcess_watch 硬停
[OK] B-12     预检残留进程 ⇒ 停（precheck_residual_procs）
[OK] B-13     WM_CLOSE 投递失败 ⇒ FAIL 且 finalize 清扫仍跑（G-5/G-9 纪律）
[OK] B-14     载体创建失败 ⇒ FAIL@mkdir（无泄漏、不删他树）
[OK] B-15     载体身份不符 ⇒ 前置拦 carrier_identity
[OK] B-16     兑现趟（自然退）⇒ 短慢行、exit_kind=natural、final code=int
[OK] B-17     零 close 样本 ⇒ FAIL（承 v2 G-9）
[OK] B-18     跨趟 BOOT 读数变化 ⇒ 停（stop_condition:boot_changed_between_trips）
[OK] B-19     boot_change 形态同样被拦（读数≠参考即停，无方向假设）
[OK] B-20     Wait 三态补全：WAIT_FAILED ⇒ exit_kind=wait_error（不冒充「仍活/挂死」）
[OK] C-01     #32770 新窗 ⇒ stop_triggered=interaction_window（命中证据入 stop.evidence）
[OK] C-02     停止=只留证据不升级（stop_evidence 截图+exit_kind 标注+verdict 不 FAIL）
[OK] C-03     停止即退出慢采样（命中行完整落记录后停）
[OK] C-04     非交互关键字新可见窗 ⇒ 保守停 new_visible_window（E2「新窗即停」）
[OK] C-05     except.txt 哈希中途变化 ⇒ stop=except_changed（before/now 俱在录）
[OK] C-06     停止趟 finalize 仍跑（证据双时点+清扫+载体删）
[OK] C-07     交互关键字命中 ×6（#32770/确认/保存/confirm/save/网络，纯函数臂）
[OK] C-08     同名新句柄 ⇒ 记新窗但不定性交互（关键字零命中）
[OK] D-01..D-10 分叉标签机 §9 A4 全臂（P1/丁/阻塞/中间带/CPU 不可读/读败未决/混合/ws 增长/闩后零行/未闩不虚构）
[OK] D-11     阈值常量与 §9 A4 语义一致（spin≥0.7 > block≤0.2，中间带存在）
[OK] D-12     禁比率表述纪律：件内零「成功率/兑现率/百分比/概率」文案
[OK] E-01     gate_decision 四组合 [0, 0, 3, -1]
[OK] E-02     母版哈希自验：钉值不符⇒RuntimeError
[OK] E-03     母版哈希自验：文件不可读⇒RuntimeError
[OK] E-04     实测 无参离线 rc=0（不发射、零 ops 绑定）
[OK] E-05     实测 --approved 单给 rc=0 且明示「透传不自动跑」
[OK] E-06     实测 --live 无授权 rc=3 恒拒
[OK] E-07     实测 --live --selftest：自检分支优先于 live 闸（rc=0）且零发射
[OK] F:×13    变异全部被抓出（闩常量/节律/哨兵吞值/hook6 吞读败/CPU 分母/慢行旁路/停止旁路/
              finalize 跳过/BOOT 断言旁路/live 闸篡改/E2 段删/交互关键字清空/闩+30 截图旁路）
[OK] G:×3     运行前后 v2/earlyclose/e12 三件哈希不变
== E12 SELFTEST: 82 项，红=0 ⇒ ALL-PASS ==
件 sha256: e12=f9d3f36a543d995ffd36d1305afb2b9c0336b6a40111e9a37e168b725d9e89be
           earlyclose=2e970eec43fe37ff02cab98e71bce9c764d11d758ab2a7b31b495100d109c2e1
           v2=6afe2711136c3b52344cd435f6dbd64508378a1e019c552228ff4f5e653d13b9
```

（逐项原始行见 `_drive_c2_x_e12_selftest.py` 运行 stdout；以上为定稿快照，计数=H 1 + A 13 + B 20 + C 13 + D 12 + E 7 + F 13 + G 3 = 82。）

## 附录 B：命令级实测记录

| 命令 | 实测 rc | 输出要点 |
|---|---|---|
| `python _drive_c2_x_e12.py` | 0 | 离线不发射 |
| `python _drive_c2_x_e12.py --approved` | 0 | 闸值透传不自动跑 |
| `python _drive_c2_x_e12.py --live` | **3** | 需 --approved 恒拒 |
| `python _drive_c2_x_e12.py --selftest` | **0** | 委托自检 82 全绿 |
| `python _drive_c2_x_e12.py --live --selftest` | 0 | 自检优先于 live 闸（无发射路径） |
| `python _drive_c2_x_e12.py --preflight` | **0** | 10 项全过（v2 预检 7+终钉复验+源 ini `27c9a60c55a8a1b4`/16,496 B 命中+BOOT 读数 107,597,421 ms） |

## 附录 C：足迹核对

`git status --porcelain` 本轮新增仅：
`?? lead/qc161_u0400_trip/_drive_c2_x_e12.py`
`?? lead/qc161_u0400_trip/_drive_c2_x_e12_selftest.py`
`?? lead/qc161_u0400_trip/E12_CANDIDATE_SELFTEST_20261029.md`（本稿落盘后）
他线足迹（M 状态件 mtime=2026-10-25，非本轮操作）与冻结件均未被写入；
自检沙箱=系统 tempdir（自动清除），`c2ab_x/` 下零新建，`__pycache__` 内本轮 pyc 已删。
