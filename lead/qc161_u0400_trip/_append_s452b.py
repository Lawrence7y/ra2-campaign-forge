# -*- coding: utf-8 -*-
# §452补: one-line caliber fix for the fps trip count claim.
LEDGER = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
BLOCK = (
    "\r\n# §452补（口径勘正·自察）：「≈31 档 9 趟」应为「战斗帧钟读数 7 趟 30.97–31.47\r\n"
    "#   （P0/P0N/P1/P2/P3+P0r/P1r），菜单臂 P3m×2 恒 frame=0 不适用 fps」；『窗内无卡顿\r\n"
    "#   事件』主张的趟数=全批 9 趟属实。重复两趟实测 fps_med=30.98/30.97 已补核在案。\r\n"
)
with open(LEDGER, "ab") as f:
    f.write(BLOCK.encode("utf-8"))
print("APPENDED §452补")
