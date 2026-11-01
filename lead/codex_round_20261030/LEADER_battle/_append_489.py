# -*- coding: utf-8 -*-
"""_append_489.py - append S489 (RR typed receipt adoption) to shared ledgers. Additive only."""


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


S489 = """

# §489　RR typed 回执回收（聚焦复审正式版，XVERIFY_H8_RR_20261031.md）：v2 红项 0 ⇒ GO-WITH-CONDITIONS
#        维持；**最强加性证明新增**（H8 标记切块余量与 harness7 逐字节相等 383,018 字符）；条件精化
#        C-R1..C-R6 全处置；**唯一 REFUTED=「≈410Hz 实测」表述**（C-R3，文档级）；时序如实：typed 后于①批发射

- **结论**：与盘面判定书同构（红项 0/GO-WITH-CONDITIONS），另增三件承重新证：
  ① **加性证明升级**——按 `>>> H8-BEGIN/<<< H8-END` 四对标记切块后剩余源码与 harness7 **逐字节相等**
  （383,018 字符 True）；② **R-1 修复全正控**——fail-closed A8 实测（假 gamemd 进程 ⇒ rc=2 不发射、
  零目录创建）、kill_under 合成 pid 桩零误伤（unrelated 不进 OpenProcess）、三轮枚举 499/499/499 稳定、
  last error=18 正常耗尽；③ **判档器零回归**——副本 vs 母本对历史真机趟（l1_20261023/e4/l3_20261021）
  EXIT 全等（3/1/1）。审查员本轮零 __pycache__（-B+内存 compile）、零删除、夹具独立（rr_fx_*）。
- **时序如实**：typed 回执晚于①批发射；发射依据=盘面判定书（N-1..N-6，全采纳 §486）。精化条件中
  **C-R2（六位 pid 门禁边界）与 C-R3（410Hz REFUTED）为 typed 版新增**——C-R2 未兑现（ha/hb carrier
  实测 130=五位 pid；风险转 v3）；C-R3 属文档级（410Hz 非承重，逐趟真节律由 poll_count/wait_s 留痕：
  **ha 346.6Hz / hb 284.5Hz**），处置=选项 (b)。
- **条件处置**：C-R1 ✓（两趟 META=400 ∧ h7_frame_wait 在场双证）；C-R2 登记（后续趟发前验 pid 位数，
  被拒=「门禁拒发非故障」；根治→v3）；**C-R3 采 (b)**——卡片判读纪律段已改注「284-347Hz 真机实测、
  410Hz=裸机对照值」（不改 harness8 字节，C-R5 冻结维持）；C-R4 ✓（自检文件追加宽口径标注）；
  C-R5 ✓（v2 冻结维持、A11 两趟实得 dd5459fe）；C-R6 ✓（frozen_recheck_h8_pre.txt 追加作废标注，
  历史留痕）。新增 Y-R1（声明穷尽性瑕疵，low，v3 文案）、Y-R3=N-1（武装断言缺失，medium，v3 积压
  维持）、Y-R5（超时支缺 overrun_kind，low，v3 积压维持）。
- **hb 判档 EXIT=1 复核**：RR 亲跑判档器对真机 hb ⇒ EXIT=1（V11-a min=6.676<25 FAIL）——与 §487
  「判据设计失配」登记一致（窗 verdict=ok 但 V11-a 档位门按原口径 FAIL），互证无矛盾。
- **卡片轻项**：list_procs 条数 499 系当时值（随负载浮动 499/543/558）——已按 C-R3 处置同批改注口径。
- 在飞：B2 对账（p05 后判定书撰写中）。句态不变；趟数 34。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S489)
b = append_lines(GOAL, S489)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
