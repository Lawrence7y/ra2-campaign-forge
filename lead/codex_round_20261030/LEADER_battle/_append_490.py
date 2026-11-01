# -*- coding: utf-8 -*-
"""_append_490.py - append S490 (B2 provider stop, resume pending) to shared ledgers. Additive only."""


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


S490 = """

# §490　B2 对账被 provider 截停（new-provider-3 登录过期 auth_failed，5h18m 处）；**七探针+全 stdout 在盘、
#        journal 完整可续**；待用户重新登录后 ResumeWorkflowRun（不重建）；判定书未落盘

- **停止态**：run `dwfrun-453c97dc`（B2 异族对账）stop_reason=provider/auth_failed——**dfmodel 唯一异族通道
  登录过期**；§482 计 1 epoch；finished steps 全保留，Resume 即续（判定书撰写段重跑）。
- **已完成产物（写域 XVERIFY_H8TRIPS_20261031/）**：探针 7 支（p01_2c ②趟全重算 / p02_delta14 Δ轴 n=14 /
  p03_framezero frame 语义+全库对照表 / p04 张力（轨迹段除零崩溃）→p05 重写 / p06_batchface §485-487 审计 /
  p07_frozen 冻结件审计）+ _raw/（judge_ha/hb 亲跑判档、p01-p07 stdout）。
- **预读要点（正式以判定书为准）**：frame=0 ⇒ 战斗起点语义成立（菜单恒 0×4 趟）；q/r 张力为真难题
  （l3_20261021 同图 10 档同相位 ≈7.4fps 近帽 vs q/r 均值 23.7 含早相 vs hb 早相 5-10fps——候选=装载
  时长方差/会话方差）；p04 stats 复算与 _measure_stats 仅浮点尾差；**hb units0 口径差待裁（其表 1347 vs
  §487 记 1341，同行 counters 取行口径）**；ha/hb n2w=4.1s 系 nav→measure 入口（绑帧等待在其后），
  p03 ratio 列对 H8 趟混淆应会在判定书处理。
- **下一步**：用户重新登录 new-provider-3 ⇒ ResumeWorkflowRun `dwfrun-453c97dc` ⇒ 判定书落盘 ⇒ §491 回收。
  句态不变；趟数 34。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S490)
b = append_lines(GOAL, S490)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
