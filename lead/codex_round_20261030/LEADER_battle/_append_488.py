# -*- coding: utf-8 -*-
"""_append_488.py - append S488 (B1 typed receipt adoption) to shared ledgers. Additive only."""


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


S488 = """

# §488　B1 typed 回执回收（审查员终版合并结论）：v2 红项 0 ⇒ GO-WITH-CONDITIONS 与盘面判定书一致；
#        条件 C-0..C-6 与 §486 采纳逐条对上；**趟执行反向闭合审查员多项 UNVERIFIED**；v3 积压 +2 小项

- **终版结论**（typed 回执 = 判定书增写版，XVERIFY_H8_20261031.md 29,782B）：对盘上 v2
  （harness8 dd5459fe + 发射器 9a1a795b + 判档器副本）**红项 0 ⇒ GO-WITH-CONDITIONS**；
  ask 点名 v1（e29a9a07）程序性 NO-GO（R-1），v1 字节已被修复包替换（18:48，§486 在案）。
- **审查员亲历字节替换的程序性发现（high/verified）**：被审件在审查中 v1→v2——处置=该发现由
  C-0 冻结声明 + RR 对 v2 复审 + §486 修复包登记三重闭合；后续任何 v2 再改动 ⇒ 判定书作废重审（C-0 原文）。
- **条件逐条对账（发射前采纳 vs 终版条件）**：C-0 ✓（frozen_recheck_h8_v2.txt 六行+v2 冻结声明；
  A11 实得 dd5459fe 两趟核验）；C-1 ✓（显式 extra-argv + 两趟 META=400 ∧ h7_frame_wait 在场均核验）；
  C-2 采 (b) ✓（jump=引擎停顿证据预登记；本批两趟 offset=0 未触发）；C-3 ✓（离线自检全过 tee）；
  C-4 ✓（tee 2>&1 处置）；C-5/C-6 ✓（卡片 v2 即其内容）。**其 C-1 建议项（400 钉发射器缺省 /
  判档器补 h7_frame_wait 断言）未采**——理由=C-0 冻结下避免发后漂移，靠人工双核验兜住（两趟实证）；
  转 v3 候选积压。
- **趟执行反向闭合审查员 UNVERIFIED（其 §5 列明的真机侧项）**：「N=400 与真机帧钟相容性」
  「units0≥1200 能否达到」「等待/达标路径真机行为」——ha/hb 实测已达（reached=400/offset=0×2、
  units0=1342/1341）；「真实 poll 节律」=347Hz（ha 25349 拍/73.1s）、超时支合成实测 ≈442Hz、
  裸 _doze 407-411Hz；「跳帧误拒发生率」本批=0（offset 全 0）。
- **v3 积压 +2（小项，不阻断）**：① 超时支 h7_frame_wait dict 缺 overrun_kind 键（:5072-5076，
  与另两支不对称）；② C-1 建议项（发射器缺省 400 / 判档器武装断言）。另登记台账口径：
  **「exit 2 + 趟目录无产物 = 参数非法拒发」（N<1 路径不落 qc151_fields.json，勿误读为产物丢失）**。
- **C-2 证据增补（其真机复算）**：75 窗相邻拍 maxΔ 分布 74×1 + l1_20261023k w0 maxΔ=3
  （n_multi_advance=4，verdict=no_advance）+ l1_20261023e4 w2 RPM 失败 6190 次 ⇒ 真机确有
  Δ≥3 与读败；容差=2 的误拒风险为真（fail-closed 方向），C-2(b) 预登记已覆盖其解释路径。
- 在飞：RR typed 回执、B2 对账（dwfrun-453c97dc）。句态不变；趟数 34。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S488)
b = append_lines(GOAL, S488)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
