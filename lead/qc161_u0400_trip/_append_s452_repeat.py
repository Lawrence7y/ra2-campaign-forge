# -*- coding: utf-8 -*-
# §452: repeat batch (P0r/P1r/P3mr) execution + index amendment + gate restore.
LEDGER = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
BLOCK = (
    "\r\n# §452　同场景重复批三趟落地（P0r/P1r/P3mr，2/2 支持三关键读数）；异族判读在途\r\n"
    "\r\n"
    "- 授权=用户 10-28 续办令「真机继续」；发射前复测全绿（BOOT 未变 07:52:14、进程=0、\r\n"
    "  ini 16,496 B/27c9a60c 命中、驱动终钉 6afe2711）。闸翻 613f2429…批毕**逐字节还原**\r\n"
    "  （注释原行原文）⇒ sha256sum=6afe2711136c…复验命中、FT 17/17、--live rc=3。\r\n"
    "- **P0r**（19:20:13, 40 s 窗）：row0 hwnd≠0→**row1 归零**、frame **398/398 全程推进\r\n"
    "  至 3610**⇒隐形僵尸 **2/2**。注意修正首批措辞：首批「首行即归零」系采样恰落链后\r\n"
    "  （本趟 row0 仍非零）⇒ 合法表述=「WM_DESTROY 链在关窗后 ~0.1–1 s 内走完、\r\n"
    "  原版全局同样归零」——链走到≠宿主进入（exitstate 恒 {0} 两趟同）。\r\n"
    "- **P1r**（19:28:30, 120 s 窗）：frame 停转行 **1129≈+112.9 s**（首批 472≈+47.2 s）\r\n"
    "  ⇒ 「守卫臂 frame 终停」复现 2/2，但**停点两趟漂移 47→113 s 不定**；停后 frame>0\r\n"
    "  行数=0 ⇒ 不可逆 2/2。停点漂移=新形态细节（非确定时延，或场景/加载态相关）。\r\n"
    "- **P3mr**（19:37:22, 40 s 窗）：menu_ready×3(3.0 s)、closed_at 44.5 s（首批 44.8）、\r\n"
    "  不退、exitstate 恒 {0}⇒**菜单就绪态不退 2/2**。⇒ 与旧会话 MAIN（6.6 s 关窗、\r\n"
    "  15.5 s 自然退+闩 1）的矛盾=**稳定行为差**（两新会话趟 vs 一两旧会话趟），差异变量\r\n"
    "  候选=关窗时机 6.6 vs 44.5 s（加载深度）；正式定性归异族 XVERIFY_BATCH6（在途，\r\n"
    "  派发时已声明重复未在盘，到盘后按其判定书对本节三趟对账）。\r\n"
    "- 通道面：三趟 judge_artifacts **11/11×3 全绿**、a8=PASS、载体删、except 恒 6694b75e…；\r\n"
    "  证据=TRIP_INDEX_20261028.md 增补「同场景重复批」节（rec/tl 全哈希\r\n"
    "  fd2f63ab…/44dc43e6…/1cc6a12f…；索引现 sha 前缀 c4a3cd87…）。趟数账 13→**16**。\r\n"
    "- 三目标态：②=关键三读数各获同会话 2/2，零正常退×9（全批累计）⇒ 断点候选收窄为\r\n"
    "  「守卫在场时引擎泵约 1 分钟级内终停且不可逆、原版泵永不停」；①=≈31 档 9 趟同会话\r\n"
    "  无卡顿事件（仍未复现）；③=保持（外层钩子未碰）。下一动作=等 BATCH6 判定书+其红项处理。\r\n"
)
with open(LEDGER, "ab") as f:
    f.write(BLOCK.encode("utf-8"))
print("APPENDED §452")
