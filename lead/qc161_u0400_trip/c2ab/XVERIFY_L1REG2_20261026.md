new-provider-3/qoder-cn:qfmodel

# XVERIFY-L1REG2 — GOAL-3T C26 · L1REG 第二趟（20261026T200938）+ 全轮 trip 索引一致性 · 独立补充核验判定书

核验员模型身份：**new-provider-3 / qoder-cn:qfmodel**（异族于执行者 dfmodel；本会话运行上下文读回，ListModels 报 `model_catalog_unavailable`，与首份判定书 XVERIFY_C2AB 同一核验族）。身份注记：本趟与首份判定书为同族（qfmodel），执行者为另一族（dfmodel），满足 C26-05「执行与核验异族」，不满足「两本核验书异族」（该条 REVIEW 未要求）。
核验时间：2026-10-26（~20:26 起）。方式：**只读**复演 + 离线重算 + 只读事件日志查询 + 生成器重跑重定向到临时文件比对（零覆写索引原件）；零真机趟、零游戏进程、零 git。唯一写入=本件。

---

## W1 200938 逐字段复演 — CONFIRMED（两处口径修正，见注①②）

亲读 `c2ab/20261026T200938_L1REG/_rec.json`（4420 B）全部 30 键。独立重算：
- 帧率 = 1792 / 58.04 = **30.875 ≈ 30.9** ✓（申报口径成立）。
- 帧推进自证：head[0].frame=270 → tail[-1].frame=2062，**2062−270=1792** ✓；tail 逐对 Δt≈2.00s、Δf∈{63,62,62} ⇒ 瞬时 fps 30.97–31.47，全程无停滞样本 ✓。
- play_wall_s 自证：tail[-1].t − head[0].t = 58.041 → round=58.04 ✓；closed_at_s=137.103 与末样本间隙 2.28 s（关窗发生在采样窗尾后 ~2 s，驱动 sleep 序自洽）✓。
- 时间轴重建：反推 t0（发射）= 20:09:40.8 ≈ 目录戳 20:09:38 + 88 文件复制耗时；close 时刻 ≈20:11:57.9，末行 20:14:27.6，观察窗实测 149.7 s = 1495 行 × 0.1002 s 节拍 ✓（watch=150 s 上限内未退）。
- close_rows_tail 六行：exitstate **恒 0** ✓、wait_res 恒 258（WAIT_TIMEOUT，进程活着未退出）✓、frame 恒 0（注③：局内帧钟 2062 → 关窗后读回 0，机制未解释，见剩余缺口）。
- hook6 六样本恒 `e91a1f941790`；**独立反汇编算术**：E9 rel32=0x17941F1A，next_ip=0x6BE0E6，目标 (0x6BE0E6+0x17941F1A)&0xFFFFFFFF = **0x18000000 == cave_base** ✓（c″ 在位且指向申报 cave）；singleton 恒 17493184≠0 ✓、可见窗仅 ("Yuri's Revenge","Yuri's Revenge") ✓。
- exitstate_during_play=[0]、new_windows_during_play=[]、exited_within_watch=False、exit_after_close_s/final_exitcode=null、exited_within_20s=False ✓ 全对。
- guard_lines 九行与 161412 逐行相等（PID 归一）；cave 池 0x20000000 + exitbail cave 0x18000000 ✓；ra2render.log 与 guard_lines 一致 ✓。
- gamemd_sha16=73201cc021497c95（我实测 GAME_SRC 原件相等）✓；except_before=6694b75e46a6e773（**我实测 GAME_SRC/except.txt sha256[:16] 相等**——载体复制自该源，基线哈希独立复现）✓。
- a8_verdict=PASS、a8_remaining=[]、carrier_deleted=True ✓。
注①：任务书要求核 `layout_pre_close.ok` 三检查——**L1REG rec 根本不含 layout_pre_close 键**（layout_pre_close 仅存在于 A/B 四趟；MAIN 趟我实测 ok=True 且 checks{hook_win,cave_36b,dead_je_kept}=true，CTRL ok=True checks{site_untouched,orig_je_kept}）。L1REG 的布局证据=上面 hook6→0x18000000 算术 + 日志回读，本项按此替代口径判 CONFIRMED。
注②：play_shots 仅存 head2+tail4（共 6/30 样本），exitstate_during_play/hook_live 为 rec 内聚合字段（驱动 415–417 行对全 30 样本算得）⇒ 聚合字段与留存样本自洽，但**逐 30 样本不可外部复验**（证据留存设计限制，两趟相同，非申报矛盾）。
注③：close 后 frame=0 而 exitstate=0、wait_res=258 ⇒ 进程存活、帧全局归零。按 REVIEW 口径不得据此单推「主循环卡死」或「已 reset」，仅登记为观察。

## W2 与首趟 161412 差分 — CONFIRMED（限「R3 不复退 = 2/2」与配置同源性；不得外延）

- 键集合差 = **恰好 {except_after, except_changed}**（200938 有、161412 无），其余键名相同。
- 19 个静态/判据字段逐一相等：tag/guard_enable/exitbail_enable/dry_run/carrier_files/gamemd_sha16/except_before/in_battle/cave_base/play_shots_n/play_wall_s/hook_live/exitstate_during_play/new_windows/exited_within_watch/exit_after_close_s/final_exitcode/exited_within_20s/a8_verdict/carrier_deleted ✓；nav 坐标三连 (700,218)→(700,304)→(700,262) 相等 ✓；guard_lines 相等 ✓ ⇒ 同驱动（`_drive_c2_l1_regress.py`）、同 MAIN 配置（1/1/0）、同判据。
- 复演结果同形：帧推进 1770 vs 1792（fps 30.50 vs 30.88）、close_rows_n 1494 vs 1495、两趟 exited_within_watch **均 False** ⇒ 「局内 WM_CLOSE 后 150 s 观察窗内不自然退出」**2/2 可重复** ✓（R3 判据不成立，两趟同账）。
- 边界（按 REVIEW 第 2 条）：两趟 in_battle=True 仅证「帧钟推进 + c″ 未被摘走」，**不证**完整行为无副作用；本件不宣布「无副作用/无回归」，只登记「不退现象 2/2 复现」。R3 失败原因未定：候选回归 / 既有缺陷 / 正常确认交互等待 / 消息未处理，四假设未分离（C26-06 对照设计未完成前不得归因）。

## W3 except 直接通道闭合 — CONFIRMED（200938 闭合成立；161412 UNVERIFIABLE 维持不追溯）

- 200938：`except_before`=`except_after`=`6694b75e46a6e773`（键在、值等、`except_changed=false`）✓；驱动现码 326–330 行「except 取证先于 rmtree」（331–335）+ 注释「★ 20261026 修」在位，且 200938 rec 含该二键（161412 不含）⇒ 补跑确由修序后代码产生，**直接通道闭合成立**。live 日志旁证：`c2l1reg_live_20261026.log`（首趟）汇总行 `except_changed None`，`_fix.log`（二趟）`except_changed False` ✓ 两本账各自在盘。
- 161412：rec 仍**缺键**（非 null，键不存在）⇒ 首趟 except 直接通道 **UNVERIFIABLE 维持**；补跑不追溯改绿（REVIEW 第 15 行执行到位）。两本账并存：首趟=事件日志旁证过渡、直接通道缺；二趟=直接通道闭合、旁证另计。

## W4 事件日志通道 — CONFIRMED（含口径审读）

自查（只读 Get-WinEvent，Application Id=1000/1001）：
- 一趟窗 16:14–16:26：**0 条**，gamemd 命中 0；
- 二趟窗 20:09–20:26：**0 条**，gamemd 命中 0；
- 全天 00:00–23:59：21 条 Id=1000/1001（首书时点 19 条，增量系当日后续非 gamemd 事件），**提及 gamemd = 0 条**；查询机制阳性验证（能返回其它来源事件）。
- 索引备注 21–22 行口径如实：「零命中=查询时窗内未观察到登记事件，**不**证明无 AV」✓ 与 REVIEW 第 16 行一致。二趟另有 W3 直接通道补足，首趟仍仅旁证。

## W5 TRIP_INDEX 一致性 — CONFIRMED（十行逐行复算；e2/e3 登记项无盘面原件另注）

- **生成器重跑**：将 `_gen_trip_index_20261026.py` 目标路径重定向至临时文件（原件零触碰）再生 ⇒ 与在盘 `TRIP_INDEX_20261026.md` **字节级相同**（4035 B，10 行，末行计数一致）。
- 六趟 ② 行逐列对 `_rec.json` 原件复验：CTRL 133324/134240（exited=False、bail=0、layout ok、except 不变、a8 PASS、carrier_del ✓）；MAIN 133604/134519（15.52/15.71 s 退出、exitcode=0、checks 三真 ✓）；L1REG 161412（帧+1770/58.04、键缺失(161412) ✓）与 200938（帧+1792/58.04、前后哈希相等 6694b75e… ✓）全部相符。
- ① 两行对 `l1_20261023{e1,e4}/measure_w0.json` + `_launch_result.json` 原件（`out/re_work/.../qc161_u0400_trip/` 在盘）：e1 pre_fps15=5.342→5.3 / units0=0 / ok=False / p50 27.8 / p99 3520.5 / max 3780.8 / mf=8 ✓；e4 30.692→30.7 / units0=702 / ok=True / p50 32.6 / p99 61.0 / max 69.6 / mf=736 ✓；harness_sha16 均 d019e8be ✓；rc=0 ✓；trip_id 唯一 ✓。**转录相符**≠百分位自原始帧样本复算——该缺口索引备注 28 行已如实自标（「未逐项异族复算」），维持。
- 总数账独立复算：**有效 7** = c2ab A/B 4 + L1REG 2 + e4 1 ✓；**作废 1** = e1（units0=0）✓；**非趟 3** = e2、e3、gate_rerun ✓。
- 有无第 8 个有效趟：全盘扫 `qc161_u0400_trip/**/_rec.json`——20261026 戳的仅 c2ab 六趟；ab24/、d09b/ 均为 10-24/25 前轮趟次不属本账；当日发射目录扫描仅 e1/e4 含 _launch_result.json ⇒ **无第 8 个有效趟，账目不虚报** ✓。gate_rerun 行实测 `_gate_rerun_20261026.out` = 14/14 PASS/0 FAIL ✓。
- e2/e3 登记行：盘面**无**对应目录或 rc=2 日志工件（与「预检前拒收、零副作用、无载体」自洽——失败在创建目录前，故无目录是预期形态，非反证）；该两行仅由账目证据支撑（GOAL_THREE_TARGETS 732 行、ROUND log 18746/18810 行「argparse 拒收空格形 --extra-argv」）。判：**账目一致性 CONFIRMED；盘面工件级直接证据 UNVERIFIABLE（按口径登记为非趟，未见矛盾）**。

## W6 装置有效性缺口如实性 — CONFIRMED

- 两趟 rec 均无 post_ok/post_err/hwnd 投递返回键；驱动现码 423–424 行 `u32.PostMessageW(...)` 返回值**确未记录** ✓（缺口真实存在）。
- 索引备注 25–26 行如实标「投递≠处理，装置有效性未闭合」✓；指向的观测候选 `_drive_c2_x_probe.py`（现码 230–239 行 `record_close_delivery`：post_ok/post_err(GetLastError)/target_hwnd/target_pid/target_tid，278 行 shape 断言）**在盘且在码** ✓。注：该候选系 C26-06 离线件，**未跑过真机趟**，「已补记」指代码口径，非两 L1REG 趟已补记——索引措辞可再收紧半步（本件点名，不判 REFUTED，因备注主句「未入 161412/200938 记录」完全如实）。
- except 取证顺序修复在位（W3 已证），且未借此要求补跑改首账 ✓。

## W7 判据边界审读 — MIXED（索引=CONFIRMED；首书两处过度主张=REFUTED，历史文本不追溯改写）

- 索引备注 23–24 行：「exitstate 恒 0=采样未观察到闩 1，**不能**据此定位断点、不能推出 c″ 未触发或『必在 0x6BE0B6 之前』」✓ 与 REVIEW 17 行逐条对表收紧到位。
- 索引备注 27 行：「缺省 0 未验证——CTRL 是显式写 0」✓ 与 REVIEW 19 行一致；两本判定书与索引均无「默认 0 已实证」主张。
- **首书 REFUTED 两处**（`XVERIFY_C2AB_20261026.md`，20:08 落笔，早于 REVIEW 20:19，REVIEW 已点名、本件独立复认，按其要求不改写原件、于本件记过账）：
  1. V7 边界段「原生退出状态机从未闩到 1 ⇒ **控制流卡在 c″ 靶点之前的阶段**」「局内关窗**走确认/存档流程**，非菜单态即时 teardown……不同形」——两者均由 exitstate 恒 0 单通道外推断点/路径，REVIEW 明文禁止（不能推「必在 0x6BE0B6 之前」、不能推「必为另一条确认/存档路径」）⇒ 作为**主张** REFUTED；合法残留=「采样未观察到闩 1，路径未定」。
  2. V6「⇒ L1REG 趟**无** gamemd 崩溃/AV」（事件日志通道作安全结论）——零命中只能证「窗内未见登记事件」⇒ 作为**结论**措辞 REFUTED；对 200938 现由 W3 直接通道闭合取代该旁证角色，对 161412 该通道结论降级为「未见登记，未闭合」。
- 关窗后新窗口：复核 close 观察循环（427–443 行）确**不采**窗口枚举；`new_windows_during_play` 全为空且只属关窗前 ⇒ REVIEW 17 行「关窗后新窗口观察不能被关窗前替代」在两趟中**均未闭合**——索引备注未列此项，本件补登为开放缺口（不判索引 REFUTED，因其未主张该项成立）。局内确认 UI 可能为游戏内绘制（非 #32770），仅检 #32770 的判据覆盖不足，同样登记开放。

---

## 总判定

**200938 成立（CONFIRMED）**：全部申报字段复演相符（1792/58.04=30.875≈30.9；exitstate 采样恒 0；hook6→0x18000000 独立算术自证；timeline 反推自洽；except 直接通道闭合 before==after==6694b75e46a6e773 且基线哈希被我实测复现；a8=PASS；carrier_deleted=True；exited=False）。R3「局内关窗 20 s 自然退出」两趟 2/2 不成立（不复退可重复）。TRIP_INDEX 与原件字节级再生一致，7/1/3 账目可独立复算，无第 8 有效趟。事件日志两窗零命中、口径如实。

**并存账（不合并、不追溯）**：161412 except 直接通道维持 UNVERIFIABLE（首书 V6 + 索引备注 13 行为准）；首书 V7 两处过度主张由本件记过账（REFUTED-as-claim），历史文本保留。

**剩余开放缺口清单**：
1. PostMessageW 返回值/错误两趟未入 rec——WM_CLOSE「投递≠处理」，装置有效性未闭合（x_probe 候选在码未跑）。
2. 关窗后窗口/UI 证据零采集（close 循环不枚举窗口；游戏内绘制确认 UI 未被 #32770 判据覆盖）。
3. R3 失败归因未定（候选回归/既有缺陷/确认交互等待/消息未处理四假设未分离；待 C26-06 对照设计）。
4. close 后 frame=0 机制未解释（不得单推主循环卡死或 reset）。
5. 逐 30 样本仅存 6，聚合字段（exitstate_during_play/hook_live/无新窗）外部不可复验（留存设计限制，两趟同）。
6. e2/e3 非趟登记仅有账目证据、无盘面工件；e4 W0 百分位未自原始样本复算（索引已自标）。
7. 161412 的 except_after 永久不可恢复（首趟旧序代码产物）。

— 独立核验员 new-provider-3/qoder-cn:qfmodel；除本件外零写入；零真机、零游戏进程、零 git。
