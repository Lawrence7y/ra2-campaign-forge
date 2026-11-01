new-provider-3/qoder-cn:qfmodel

# XVERIFY — GOAL-3T 线 C26-01 ② 真机 A/B 与 L1 回归 · 独立核验判定书

核验员模型身份：new-provider-3 / qoder-cn:qfmodel（异族于执行者 qoder-cn:dfmodel；从 host 会话模型与 provider_config.json 的 new-provider-3 目录读回确认，ListModels 报 model_catalog_unavailable，故身份取自会话运行上下文与 ZCODE 配置，非猜测）。
核验时间：2026-10-26（UTC ~11:54 起）。核验方式：只读 + 重跑离线门禁 + 自算哈希 + 自写布局算术 + 只读事件日志查询；未发射任何真机趟、未启动游戏/进程、未做 git 写、除本判定书外零写入。

---

## V1 工件门禁重跑 — CONFIRMED

- 亲自执行：`cd d09a_c2_candidate && python _verify_c2_candidate.py`（先读源码确认仅做 文件读+哈希+needle+capstone 反汇编，无 spawn、无写盘）。
- 结果：**14/14 PASS，进程返回码 RC=0**（`echo RC=$?` 捕获 = 0；grep `[PASS]`=14、`[FAIL]`=0）。候选目录内未产生 `__pycache__`。
- 旧输出 `_gate_rerun_20261026.out` 与我重跑逐行一致（同样 14/14）。
- 自算候选 DLL 完整 sha256：
  `sha256sum ra2rc4guard_c2.dll` = `edb9a0cde129c105e087db61f6661b4722a80787e5b5949bd0b0890e0354f2de`
  == 申报值 == `dll_sha256.txt` 钉值（117760 字节）。
- 关键 PASS 项语义复核（新鲜眼）：S1 k_sites 8 头表逐字段==母本规格（证明 8 头路径未被本副本改动，file off 0x13980）；S2 结构性针值在候选=1、母本=0（c″ 是候选独有）；S3 镜像 cave 在 test_base 0x10001000 == 规格字节、capstone 7 指令序列 mov/test/je/cmp/jne/jmp/jmp 且目标 0x6be0e9/0x6be0dc；N1–N3 负控证明比对非恒真。

## V2 A/B 逐趟核读四份 _rec.json — CONFIRMED

逐字段实测（全部四趟 gamemd_sha16=73201cc021497c95、c2_dll sha256=edb9a0cd…、carrier_files=88、dry_run=0、attach_debugger=false、wait_failed_rows=0）：

CTRL #1 (133324)：guard_enable=1 ✓ exitbail_enable=0 ✓ exited_within_watch=False ✓ except_before==except_after (6694b75e46a6e773) ✓ a8_verdict=PASS ✓ layout_pre_close.ok=True（requested=false，site_untouched+orig_je_kept）✓ killed_on_cleanup 含 gamemd.exe(6364)（=僵尸被清扫，装置阳性）。
CTRL #2 (134240)：同上全 ✓（PID 45600，except 不变，a8=PASS）。
MAIN #1 (133604)：guard=1 exitbail=1 ✓ exited_within_watch=True ✓ **exit_after_close_s=15.52 ≤20.0** ✓ final_exitcode=0 ✓ except 不变 ✓ carrier_deleted=True ✓ layout_pre_close.ok=True 且 checks {hook_win:true, cave_36b:true, dead_je_kept:true} ✓。
MAIN #2 (134519)：同上，**exit_after_close_s=15.71 ≤20.0** ✓ final_exitcode=0 ✓ checks 三真 ✓。
- 两臂 layout_pre_close.ok 全 True ✓；MAIN 臂三检查全真 ✓。
- 新鲜眼关键佐证：MAIN 两趟记录**不含 `killed_on_cleanup` 字段**，而 CTRL 两趟含之 ⇒ MAIN 臂 cleanup 时载体下已无存活 gamemd，即进程系自然退出、非 TerminateProcess 强杀。sample_tail 末行 `wait_res=0(WAIT_OBJECT_0)+exitcode=0` 亦印证退出码可读。

## V3 布局算术独立重演 — CONFIRMED

自写 Python（未 import `_verify_c2_candidate.py` 任何函数）：
- hook6 `e91a1f941790`：opcode E9 ✓，rel32（LE signed）= 0x17941F1A（无符号）；next_ip = 0x6BE0E1+5 = 0x6BE0E6；(0x6BE0E6 + 0x17941F1A) & 0xFFFFFFFF = **0x18000000**（== 申报 True）。尾字节 0x90=nop ✓。
- 36B cave 以 patchspec 构造规则在**实际基址 0x18000000** 重算 = `a15035b70085c00f84dce06be8833dd8eda800010f85cfe06be8e9bde06be8e9c5e06be8`，与 MAIN 两趟 `cave_36b_hex`/`cave_expect_hex` 完全一致（36B，len=36）✓。
- 同一构造在 test_base 0x10001000 重算 = patchspec `bytes_at_test_base_hex` ✓（跨基址自洽）。
- dead_je：orig_win `393dd8eda80074f3` 中 cmp 占前 6B、je=`74f3` 为后 2B；E9(5B)+90(1B) 覆盖前 6B，`74f3` 落在 0x6BE0E7 未被覆盖 ⇒ 死代码保留、字节仍可读，与记录 dead_je_hex=74f3 一致 ✓。

## V4 日志交叉 — CONFIRMED

`c2ab\20261026T134519_MAIN_c2\ra2render.log` 逐条命中：
- `EnableRC4Guard=1 EnableRC4ExitBail=1 DryRun=0 (ra2rc4exitbail/v1 d09a_c2 …)` ✓
- `守卫已装 8/8 站点（cave 池 0x20000000）` ✓
- `[ra2rc4exitbail] 已装 1/1（cave 0x18000000 …` ✓
- 卸载段 `[ra2rc4guard] 卸载恢复：memcmp 8/8 一致 …` ✓ + 两事务 FNV 相等 PASS：guard 758FF6705D117993 前/后相等 ✓、exitbail 9113B9A2A59FAE12 前/后相等 ✓。
另一 MAIN 趟 (133604) 同样含 exitbail 已装行 ✓。
- CTRL #1 (133324) 与 CTRL #2 (134240) 日志均含 `EnableRC4ExitBail=0 DryRun=0`，且**均无 `[ra2rc4exitbail] 已装` 行** ✓（双臂差异由 ini 读回实证，非申报）。

## V5 他线件四 sha16 — CONFIRMED

`sha256sum … | cut -c1-16` 实测：
- `_rc4_ab_probe.py` = b063052cd02df28c ✓
- `_src_L1_sf8_20261020/gamemd.exe` = 73201cc021497c95 ✓
- `goal2…/src/ra2rc4guard.dll`（母本）= 0e2a9995ad71184c ✓
- `goal1…/qc151_trip.harness7.py` = d019e8beecfb5fd8 ✓
四件零改动申报成立。

## V6 L1REG _rec.json — CONFIRMED（except_after 直接通道缺失，由事件日志旁证补齐）

`c2ab\20261026T161412_L1REG\_rec.json`：
- in_battle=True ✓ frame_advance_total=1770 ✓ play_wall_s=58.04 ✓
- 自算 fps = 1770/58.04 = **30.496 ≈ 30.5** ✓
- exitstate_during_play=[0] ✓ hook_live_during_play=True（play_shots 中 hook6 恒 =e91a1f941790）✓ new_windows_during_play=[] ✓
- **exited_within_watch=False** ✓（close_rows_n=1494，末行 t≈16:19:01，局内关窗观察至上限未退；且 killed_on_cleanup 含 gamemd(32752)/loader(7412) ⇒ 被强杀清扫）
- close_rows_tail 六行 exitstate 恒 0 ✓ a8_verdict=PASS ✓ carrier_deleted=True ✓
- except_after：记录**根本不含 `except_after`/`except_changed` 键**（比“=None”更甚）——与执行者自认的采证顺序缺陷一致：`_drive_c2_l1_regress.py` 现码 326–330 行注释显示 161412 趟把 except 检查放在了删载体之后，故未捕获。驱动文件当前顺序已修（except 检查在 rmtree 前），但本 rec 由旧序产生 ⇒ 直接通道 UNVERIFIABLE。
- **替代通道（自查 Get-WinEvent，只读）**：Application 日志 Id=1000/1001，趟窗 16:10–16:30 → **0 条**（该窗仅 3 条其它事件：Chrome/SPP，与 gamemd 无关）；全天 00:00–23:59 Id=1000/1001 共 19 条，**提及 gamemd = 0 条**；趟窗 Application Error provider = 0 条。查询机制经验证有效（同窗能读到非 AV 事件）。⇒ L1REG 趟无 gamemd 崩溃/AV，V6 安全结论成立，唯 except.txt 字面哈希前后比对无法直接复核。

## V7 判据口径审读 — CONFIRMED（申报口径符合 RULINGS C26-01）

逐条对照 `lead/codex_handoff_20261026/RULINGS.md` C26-01（19–21 行）：
- 「CTRL 僵尸不作为通过修复」：CTRL 双臂 exited_within_20s=False、被 killed_on_cleanup，装置阳性；汇总与判定均未把 CTRL 充当修复通过 ✓。
- 「MAIN 20s 内自然退出，TerminateProcess 不算正常退出」：MAIN exit_after_close_s=15.52/15.71 ≤20、final_exitcode=0、记录无 killed_on_cleanup（自然退出）、sample_tail 末行 wait_res=WAIT_OBJECT_0(0) ✓。
- 「exitstate 允许 0→1 恒 1、不要求 1→2」：MAIN traj_exitstate first=0/last=1/distinct_n=2，退出前行=1，未强求 2；bail 语义「不写任何状态值」与「0→1 由原生 teardown 闩」自洽 ✓。
- 「干跑字样拒作布局放行」：全臂 dry_run=0；布局证据来自独立进程 ReadProcessMemory 旁路读真实 .text（capture_layout 读 hook 窗 6B + cave 36B + dead_je），非凭日志 DryRun 字样 ✓。
- 「串行 CTRL→MAIN、同臂复跑证明可重复性」：两 CTRL + 两 MAIN，MAIN 双臂 exit 值相近（15.52/15.71）⇒ 可重复性成立 ✓。

结论口径：
1. **A/B 可记「RC-4 退出场景（菜单态关窗）候选修复通过」**——成立。A/B 关窗发生在进局前的菜单/空闲态（驱动 hold 6s 后即 WM_CLOSE），此时退出等待泵环真实运行且 exitstate 闩 1，正是 c″ 靶点覆盖的场景；MAIN 双臂在 20s 内自然退出、退出码 0、无新增 #32770、except 不变、布局实证、回滚 8/8+FNV 相等，均达标。
2. **L1REG「局内关窗不退」构成「范围限定」，非「推翻」**。事实链：局内臂 close 后 close_rows 全程 exitstate 恒 0 ⇒ 原生退出状态机从未闩到 1 ⇒ 控制流卡在 c″ 靶点（仅当 exitstate==1 且泵环等待时才被命中）之前的阶段，与 A/B 菜单态场景不同形。c″ 钩子在该局面 hook_live 全程在位且 exitstate_during_play=[0]（局内非干扰、无 #32770、无 AV），说明它被正确装而未触发；局内关窗不退属**另一条退出路径**（战斗内关窗走确认/存档流程，非菜单态即时 teardown），C26-01 从未宣称覆盖该场景。故 L1REG 不否定 A/B，而是把「修复通过」的适用边界锁定为**菜单态关窗**，且不得据此宣布 ② 全闭或部署现役（RULINGS 21 行明文）。

---

## 总判定

**成立（CONFIRMED）**：V1 门禁重跑 14/14+RC0+DLL 完整 sha256 全等；V2 四趟逐字段达标（CTRL 阳性/MAIN 15.5–15.7s 自然退出码 0/布局两臂 ok/MAIN 三检查全真/except 不变/carrier_deleted）；V3 hook6→0x18000000、36B cave 实基址重算、dead_je 保留全部自证；V4 MAIN 日志五关键行+回滚双 FNV 相等、CTRL 双臂无 exitbail 已装行；V5 他线四件 sha16 实测全等；V6 L1REG 除 except_after 直接通道外全部达标、fps≈30.5、局内不退+恒 exitstate 0 经事件日志旁证无 AV；V7 申报口径与 RULINGS C26-01 一致，A/B 通过属菜单态关窗场景，L1REG 属范围限定。

**不成立 / 无法直接复核（透明登记）**：
- V6 `except_after`/`except_changed` 字段在 L1REG 记录中缺失（非 None，是键不存在）；执行者已自认此为采证顺序缺陷。直接通道 UNVERIFIABLE，安全替代通道（事件日志 Id=1000/1001 零 gamemd 命中）补齐「无崩溃」结论，故不据此判 REFUTED，但该趟 except.txt 前后哈希比对未真正完成，属证据缺口。
- RULINGS 49 行自陈「本轮 Codex 未重跑门禁」，与本独立核验互补：本核验已独立重跑门禁（V1）并独立重算布局（V3），补上了该缺口。

**边界声明建议**：
1. 「RC-4 退出场景候选修复通过」应显式限定为**菜单态/空闲态关窗**，附注 L1REG 局内关窗未覆盖且属不同退出路径。
2. 不宣布 ② 全闭、不部署现役环境（母本/ra2youli 现役安装未动，仅候选件+临时载体）；其它崩溃类型不被覆盖。
3. 候选件 D-09 边界保持：独立 EnableRC4ExitBail 默认 0、独立候选副本、未并入母本 k_sites（S1 已证 8 头未改）。
4. L1REG 若需正式归档，建议按已修驱动序补跑一趟（except 取证在 rmtree 前）以闭合 except_after 直接通道；当前以事件日志旁证为过渡。
5. 本核验身份为异族（qfmodel vs 执行者 dfmodel），满足 C26-05「执行与独立核验不同模型家族并读回实际身份」。

— 独立核验员 new-provider-3/qoder-cn:qfmodel，仅写本判定书，零其它改动。
