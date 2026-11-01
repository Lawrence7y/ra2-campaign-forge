# -*- coding: utf-8 -*-
"""_append_499.py - append S499 (stall periodicity ~5Hz pump signature) to shared ledgers."""


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


S499 = """

# §499　停滞节律检验（四重窗停滞起始间隔分布，Leader 亲算，tee `stall_periodicity_20261101.txt`）：
#        **近周期 ~175-250ms（≈5Hz）泵动签名**——v3-a w2 CV=0.29 紧周期；hb 窗松调制（CV 0.56-0.90）

- **数字**：v3-a w2 停滞起始间隔中位 0.175s/IQR[0.144,0.205]/CV 0.29（135 段，最紧）；
  hb w0 0.206s/CV 0.90、hb w1 0.253s/CV 0.56、v3-b w1 0.182s/CV 1.82（含 2.875s 长隙）。
- **判读**：重停滞窗呈**近周期 ~5Hz 振荡**（停滞 ~175-250ms → 爆发释放 → 再停滞）；松窗=节律存在但被
  长隙调制。**假设（非结论，机制归因需 E3/RE 线）**：慢态=某 ~5Hz 周期门控使帧钟反复停摆、每周期
  放行一簇逻辑帧；快态（q/r 零停滞+均匀 ~32ms 帧沿）=门控不生效。与 ②线 R-063a「泵」概念同族
  （泵动节律 vs 泵亡——同一机构的工作/失效两态？），**跨线线索登记**。
- **对 A' 的设计约束（终版）**：观测目标=「~5Hz 门控的出现/消失条件」——需要**跨状态切换的连续
  长观测**（现有 25s 窗<2 个切换周期不够；全趟帧轴连采/加长窗为候选）；对 E3 方案的影响如实登记：
  停滞段 ~175-250ms 短于方案假设的挂死场景，SuspendThread 采点风险升高（若获批须按短停滞重设计）。
- 趟数 37 不变；输出 tee 在 LEADER_battle/。A'/C/D 仍待用户裁。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S499)
b = append_lines(GOAL, S499)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
