# -*- coding: utf-8 -*-
"""_append_494.py - append S494 (user A-approval, v3 implemented, review dispatched) to ledgers."""


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


S494 = """

# §494　用户「继续」=A 批准 ⇒ harness8 v3 全流程启动：候选实现（37a7c9cdf2ca97e3）+发射器/判档器 v3
#        副本+设计件+批卡——离线验证全绿；同族标注复核已派（dwfrun-d5694bbc）；三趟批待 GO

- **授权链**：用户「继续」（2026-11-01，接续多轮 A/C/D 待裁报告）=对 A=v3 的批准；依据=本轮指令
  「有复现再定位热点与做修复对照」+§493 判定书输入齐备。C/D 未获指示维持待裁。
- **v3 实现（Leader 亲办，全离线）**：
  - `qc151_trip.harness8_v3.py` = v2（dd5459fe 冻结维持）逐字节复制+8 处补丁：
    **H8-5 在局闸分档降级**（armed 时 gate_ok=「settle 内帧推进≥1 ∧ units0>0」，pre_fps15 转数据不设门、
    gate_block 照常留痕、V11-a 照旧输出不触发跳窗；非武装零改动）/**H8-6 --h8-wait-hz 旋钮**
    （缺省 None=500 ⇒ _doze(0.002)=v2 逐字节一致；≥20 拒发；doze 帽 0.05s；H8_FRAME_WAIT_HZ 转为
    缺省源=Y-5 清偿）/超时支 overrun_kind=timeout（Y-R5 清偿）/C-R3 措辞修正（410Hz→284-347Hz）/const
    H8_WAIT_HZ。**vs 母本 0删/208增（纯加性）；vs v2 6删/54增且删行全在我方 H8 块内（母本代码零触碰）**。
  - 发射器 v3 `_launch_h8v3_20261101.py`：白名单+v3、缺省 v3、**OUT_DIR 模板 l%s_1101v3%s**
    （planned 97/六位 pid 98≤130——C-R2 根治实证）、TRIP_ID -V3-20261101、R-1 承继（sizeof 568/
    枚举 491 实测）。
  - 判档器 v3 `_judge_h8v3_20261101.py`：白名单+v3、**C-R1 武装断言工具化**（armed ⇒ 须 h7_frame_wait
    在场否则 FAIL；非 armed 零影响）；回归实测 synth 3/3+真机 ha=3/hb=1。
  - 设计件 `HARNESS8_V3_DESIGN_20261101.md`+批卡 `GOAL1_BATCH_V3_20261101.md`（三趟对照表）落盘。
- **三趟批设计**（≤3 趟或 20min；GO 后串行）：v3-a（N=400,500Hz——闸修正验证+会话 #3 慢帧样本）/
  v3-b（N=400,**50Hz**——轮询影响判别=B2 归因开放项闭合实验）/v3-c（N=1200,500Hz——单位量阈定位）。
- **在飞**：同族标注复核 dwfrun-d5694bbc（GLM；族属披露强制；写域 XVERIFY_V3_20261101/）。
  GO ⇒ 预检 tee+冻结件复验（v2 dd5459fe+v3 37a7c9cd 双锚）⇒ 串行三趟 ⇒ 判档 ⇒ §495。
- 句态不变（按 §493 Y-11 收紧口径）；趟数 34。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S494)
b = append_lines(GOAL, S494)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
