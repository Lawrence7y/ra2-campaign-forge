# -*- coding: utf-8 -*-
"""_append_504.py - append S504 (pre-reboot baseline: hour-scale oscillation) to ledgers."""


def append_lines(path, text):
    raw = open(path, "rb").read()
    crlf = raw.count(b"\r\n"); lf = raw.count(b"\n") - crlf
    nl = b"\r\n" if crlf > lf else b"\n"
    body = text.replace("\r\n", "\n").strip("\n")
    out = nl + nl.join(x.encode("utf-8") for x in body.split("\n")) + nl
    fh = open(path, "ab")
    try:
        fh.write(out)
    finally:
        fh.close()
    return len(out)


S504 = """

# §504　重启前基线 v4-c 回收（A'' 卡首趟）：**同一 BOOT 小时尺度振荡实锤——滞态非 BOOT 内单调**；
#        重启实验判别力下修（待用户交回决策）；趟数 40

- **v4-c**（同协议 v4，N=800+trace，重启前基线）：rc=0；**轨迹 ok**（62.0s 达 800 帧/24712 样本；
  **推进间隔中位 0.003s——爆发节律等待段全分辨直接可见，§497 独立证实**）；三窗全开：
  w0(869-1332) fps 18.5/p50 50.5/stall 0.104、w1(1333-2043) **28.4**/33.1/0.063、w2(2044-2811)
  **30.7（近帽）**/32.4/0.066；units 1211→1092→1019→985；判档 EXIT=1（V11-a min 15.3 数据级）。
- **核心观察：同一 BOOT 小时尺度振荡**——06:50 v3-a 慢(11.6) → 09:0x v4-b 深滞(2.7/超时) →
  09:41 v4-c **大部分快**（w2 近帽零-低停滞）。§502「BOOT 决定」需再细化：**BOOT 内滞态可逆、
  小时尺度振荡**；「停滞与 BOOT 显著相关」（§503 勘误口径）维持，但「BOOT 内单调深化」被否。
- **重启实验判别力下修（如实）**：重启前基线已「改善」⇒ 新 BOOT 快/慢都将难以归因于重启本身
  （时间振荡混淆）；实验仍可跑（任何结果都有数据价值）但判别力=低——**交回用户决策**（§503：
  用户重启=用户机器动作）。
- **附带新数据**：v4-c w2（units~1016）fps 30.7 近帽零-低停滞——与 q/r 晚相（811-953u@31fps）一致，
  支撑「晚相/低单位=快态」；v4-c 轨迹 3ms 推进节律=§497 爆发 cadence 的等待段复现。
- 批后冻结复验待批闭；趟数 **39→40**。句态（§503 勘误口径）：①周期性停滞与 BOOT 显著相关、
  **BOOT 内小时尺度振荡**、单位量单独不足、机制未闭合；②RC-4 不收口；③保持态+回归义务。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
TRIPIDX = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x\TRIP_INDEX_20261028.md"

IDX = """
- 趟 `l3_1101v4c`（…V4-20261101C）：harness8 v4／N=800+trace／**重启前基线**／轨迹 ok（62.0s 达 800，
  推进间隔中位 3ms）／三窗全开 fps 18.5/28.4/**30.7**（近帽）／units 1211→985／判档 EXIT=1／rc=0。
  **同一 BOOT 小时尺度振荡实锤**（滞态可逆）——重启实验判别力下修，交回用户决策。
"""

a = append_lines(LOG, S504)
b = append_lines(GOAL, S504)
c = append_lines(TRIPIDX, IDX)
print("APPENDED LOG +%d, GOAL +%d, TRIPIDX +%d" % (a, b, c))
