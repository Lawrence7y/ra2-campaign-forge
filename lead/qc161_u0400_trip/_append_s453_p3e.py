# -*- coding: utf-8 -*-
# §453: early-close (timing) decisive micro-batch — 3 trips, P3m/MAIN contradiction resolved
# to close-timing variable; NEW finding: even latched, exit not guaranteed (1/3 hang).
LEDGER = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
BLOCK = (
    "\r\n# §453　早窗定因批三趟（P3e，_drive_c2_x_earlyclose）⇒ P3m/MAIN 矛盾归关窗时机；\r\n"
    "#        新读数：latch 后退出仍非必然（2/3 自然退、1/3 闩住挂死）\r\n"
    "\r\n"
    "- 件：`_drive_c2_x_earlyclose.py` sha256 前缀=`2e970eec…`（完整值见 TRIP_INDEX 增补节；\r\n"
    "  **import 终钉 v2 模块复用全部纪律**（bind_real_ops/_precheck_shas/载体/三态/finalize/\r\n"
    "  screenshot），协议改窗现+6 s 即关（无就绪闸）——单变量=关窗时机，其余全同 P3 配置\r\n"
    "  Guard=1+Bail=1+同 DLL+同游戏件。v2 本体零改动（6afe2711 复验命中）；本件自带 --live\r\n"
    "  --approved 闸（用户 10-28 真机继续令=P3m 定因微批范围），离线/拒闸实测 rc=0/3。\r\n"
    "- **三趟（同会话 BOOT 07:52:14，通道面全绿）**：\r\n"
    "  T204123：closed 7.2s，**latch@+15.4s 后不退出**（余 101.7 s 恒 wait=258、\r\n"
    "  hwnd/sing/frame 全 0、无新窗无 #32770）——闩后挂死\r\n"
    "  T204921：closed 7.0s，latch@+13.6s→**+15.7s 自然退 code0**（旧 MAIN 15.5s 形态复现）\r\n"
    "  T205108：closed 7.2s，latch@+13.0s→**+15.0s 自然退 code0**\r\n"
    "  hook 实况 e91a1f941790×3、守卫 8/8 装、cave 0x18000000 均同批。\r\n"
    "- **矛盾定性（候选方向，待 BATCH6 异族对账坐实）**：①exitstate 闩 1 **只出现在早窗**\r\n"
    "  （窗现~7 s，引擎尚处 boot→菜单过渡），就绪后 44.5 s 关窗×2 与战斗 137 s 关窗×5\r\n"
    "  全恒{0} ⇒ ②「菜单态有限通过」的旧结论真实边界=**早窗通过**（时机变量），与驱动\r\n"
    "  代际无关（P3e 用 v2 组件复现旧 MAIN 行为）⇒ c″ 机制解释在早窗路径上运行期成立\r\n"
    "  （latch=宿主 A 进入⇒hwnd==0 触发 bail⇒teardown code0）；③**新稳定性读数**：同一\r\n"
    "  早窗配置 3 趟仅 2/3 自然退——闩后 bail 未兑现（latched-hang 1/3）⇒「正常退硬门槛」\r\n"
    "  即使在最有利路径上也不是 100%，②收口前需重复加样（n≥5 判 2/3 是否本配置真率）。\r\n"
    "- latched-hang 假说候选（离线路，未测）：bail 依赖 teardown 后续段（消息泵残段/\r\n"
    "  渲染面释放）被别线程占住；或 latch 时刻在 bail 判定后（竞态）。区分实验=同协议\r\n"
    "  加长 watch 或加 hook6/栈侧证（涉侵入性，另裁）。暂不发射。\r\n"
    "- 异族判读线：BATCH6 代理曾 stopped(failed)，已带后到证据通知（六趟全目录+读数）\r\n"
    "  重新唤起在途；其 R6/M6 将含本三趟对账（未采执行线读法为结论）。\r\n"
    "- 趟数账 16→**19 有效**（+P3e×3）。0 弹框/0 交互/0 泄漏/0 部署/0 扩Hook；\r\n"
    "  三目标句态由收口⑦统一登记。\r\n"
)
with open(LEDGER, "ab") as f:
    f.write(BLOCK.encode("utf-8"))
print("APPENDED §453")
