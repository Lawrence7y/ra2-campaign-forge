# -*- coding: utf-8 -*-
"""_append_500.py - append S500 (bistable sharp-switch finding) to shared ledgers. Additive only."""


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


S500 = """

# §500　切换锐度判定（窗内逐秒停滞占比剖面 ×8 窗，Leader 亲算，tee `stall_timeseries_20261101.txt`）：
#        **快态↔滞态=离散双稳状态机，转移时间 ≤1s**；v3-b w1 单秒翻转 0%→81%；v3-a 跨窗边界
#        （frame 1075→1076）单帧翻转；episode 持续 10-30s+ 可复现往返

- **数字**：v3-b w1 逐秒 0%×13 → 81/94/85/91/87/95/80/74/96/84/98/83（切换@frame≈940-990）；
  v3-a w1 末秒 35% → w2 首秒 56/93/85/74/92/99…（窗边界连续）；hb w2 79-97% → 中段锐退 32→0→55…
  （退出@frame≈840-870）；v3-a w0 与 v3-b w2=混合振荡型（疑似第三态或频繁往复，待长观测判别）。
- **①机制图景（假设级，归因需 E3/RE）**：双稳状态机——快态（泵正常：均匀 ~32ms 帧沿、零停滞）↔
  滞态（**~5Hz 泵动签名**：~175-250ms 停滞+爆发释放交替，§499）；episode 10-30s+；切换锐利 ≤1s。
  与 ②线 R-063a「泵」假说同族（工作态/退化工态），跨线线索维持登记。
- **A' 终版设计输入**：观测目标=**切换时刻的高分辨轨迹 + 切换前后上下文**（帧轴/墙钟/units/事件）——
  现有 500Hz 窗样本已够定位切换帧（±13-25 帧），但 episode 全景（含等待期与窗间）需 v4 候选
  「等待环逐拍轨迹落盘 --h8-wait-trace」（增量小：环形缓冲+JSON 落盘）+ 长观测趟。卡片待用户批准 A'。
- 趟数 37 不变；输出 tee 在 LEADER_battle/；句态按 §496+§498-500 形态学。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S500)
b = append_lines(GOAL, S500)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
