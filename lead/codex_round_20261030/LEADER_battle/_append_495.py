# -*- coding: utf-8 -*-
"""_append_495.py - append S495 (v3 review adoption + batch launch) to shared ledgers. Additive only."""


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


S495 = """

# §495　v3 同族标注复核回收（XVERIFY_V3_20261101.md，GLM 族属声明在场）：**红项 0 ⇒ GO-WITH-CONDITIONS**；
#        C-1/C-2 即时闭合；v3-a 发射（会话 #3）

- **复核结论**（4 大项+others 全 CONFIRMED）：H8-5 闸分档（位置/armed 唯一性/降级语义/pre_fps15 转数据/
  **非武装零改动 AST 证明**；桩测 armed+ha 型 ⇒ gate_ok=True 三窗应开；探针 8/8 PASS）；H8-6 旋钮
  （缺省=0.002 与 v2 逐值一致/≥20 拒发/doze 帽边界 50→0.02、20→0.05/装订时序正确）；发射器 v3
  （投影 a/b/c×L3/L1 全 127≤130——**C-R2 六位 pid 边界消除实证**；R-1 承继 sizeof 568/506 进程实测；
  头部枚举 5 hunks 全落枚举类）；判档器 v3（armed 三态亲跑+五趟回归 3/1/1/3/3 零回归；N-1 如实：
  短路 rc=3 覆盖 FAIL 码→C-2 判读纪律）；加性证明（0删/208增 vs 母本；v2 冻结复算 dd5459fe 未破）；
  C-R3 全物件零「410Hz 实测」残留。
- **条件闭合**：**C-1**（批卡 L5/L18 轮询判读口径矛盾）——卡与设计件 §2.2 已改**分流式**：
  v3-a 慢帧再现∧差≥2× ⇒ 轮询实锤；再现∧差<2× ⇒ 轮询非主因（归因闭合：会话方差主导）；
  **v3-a 未再现 ⇒ 对照前提缺失、归因维持开放**（初版无条件「无差=会话方差主导」由复核纠正）。
  **C-2**：armed 断言以判档 FAIL 行为准（不以 rc 单判）；fields 缺失趟按未验——已入批卡。
- **发射门**：双锚哈希（v2 dd5459fe + v3 37a7c9cd）+五件冻结件复验；procs=0。
- **v3-a 发射**：`_launch_h8v3_20261101.py --suffix a --extra-argv "--h7-measure-start-frame 400"`
  （N=400，500Hz 名义；判别目标=闸修正后三窗全开+会话 #3 慢帧再现性）。v3-b/c 依 v3-a 结果按卡发射。
- 句态不变；趟数 34+a。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
TRIPIDX = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x\TRIP_INDEX_20261028.md"

IDX = """

### §495 批节 · ①批 v3（早相位判据修正+轮询对照 · 2026-11-01）
- 复核：XVERIFY_V3_20261101.md（同族标注版）红 0/GO-WITH-CONDITIONS；C-1 分流式口径/C-2 判读纪律闭合。
- 三趟：v3-a（N=400,500Hz）/v3-b（N=400,50Hz）/v3-c（N=1200,500Hz）——发射器 _launch_h8v3_20261101.py、
  判档 _judge_h8v3_20261101.py（C-R1 武装断言工具化）。结果见 §496。
"""

a = append_lines(LOG, S495)
b = append_lines(GOAL, S495)
c = append_lines(TRIPIDX, IDX)
print("APPENDED LOG +%d, GOAL +%d, TRIPIDX +%d" % (a, b, c))
