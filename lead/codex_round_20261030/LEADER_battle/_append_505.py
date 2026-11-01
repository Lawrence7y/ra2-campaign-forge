# -*- coding: utf-8 -*-
"""_append_505.py - append S505 (A audit adoption: census methodology erratum) to ledgers."""


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


S505 = """

# §505　A 停滞判据独立复算回收（XVERIFY_A_20261101/STALL_AUDIT_20261101.md，同族标注版）：
#        **对 §502 快查普查判出红项 6 条（口径缺陷实锤）——采纳 occ_a 为标准度量**；
#        BOOT 级结论经更严口径存活（活动战斗窗：10-20/23/30=0 停滞 vs 10-21/31/11-01=25-100%）

- **红项 6 条全采纳（§502 普查口径勘误）**：我的 census 用「帧沿间隙÷帧沿跨度」口径——**结构性排除
  首尾冻结与帧计数器回退事件**，六窗被漏判/错判：
  红1 q w2（census 0% vs occ_a **84.62%**——尾冻 21.156s@f4636 连分母被截）、红2 r w1（0% vs 37.75%，
  尾冻 9.436s）、**红3 r w2（census『帧沿不足』vs 实为全窗 24.998s 冻结@f4367——采样健康、units 恒 828，
  分类错误）**、红4 e4 w1（0% vs 60.20/85.22%——**窗内帧计数器回退 3668→0=战斗重启**，两侧 5.572s+
  尾冻 15.733s 被漏）、红5 e4 w2（『帧沿不足』vs 读失败主导：RPM 失败 6190 次/47.59% 覆盖段全冻）、
  红6 l1a w2（0% vs 7.13% 尾冻）。⇒ **标准度量改为 occ_a（绝对占比，含首尾）**；§502 普查数字作废
  （BOOT 分档的方向性结论另行复核如下）。
- **低 fps 零停滞谜题结案**：q w2 4.8fps=前 3.844s 全速 31.1fps+**尾冻 21.156s**（帧钟与 units 同停、
  读通道健康——疑似会话收尾/暂停类，机制需 E3）——「均匀慢窗」不存在；r w2=全窗冻结（接 r w1 尾冻，
  **跨窗连续冻结下界 34.4s/含窗间 59.5s**）；e4 w1=**窗内战斗重启**（帧钟回退+units 重置——场景事件）。
- **黄 7-9 采纳（我方分析可复现性教训）**：§499 CV 数字、§500 帧位标注、§500 逐秒剖面中段值——
  三处因**分桶/间隔集合脚本未随 tee 留存**无法逐位复现（秒位/定性排序均复现；v3a w2 CV 0.29 逐位
  复现）⇒ **教训入账：Leader 离线分析脚本必须连 tee 落盘**（本轮起执行）。
- **绿 10（核心结论存活）**：§498 停滞谱 10 窗 top4×40 段逐毫秒复现；§502 units0 全列一致、22/28 窗
  逐位一致；§500 双稳结构秒位复现（v3b w1 第 13→14 秒 1%→90%、hb w2 第 8→9 秒锐退）。
- **BOOT 级结论复核（按 occ_a 口径，活动战斗窗）**：10-20（l1a/t55k 6 窗）=0%、10-23（e4 w0）=0%、
  10-30（q w0/w1、r w0）=0% vs 10-21（l1c/d/e 9 窗）=61-73%、10-31/11-01（ha/hb/v3 8 窗）=5-100%
  ⇒ **「周期性停滞与 BOOT 显著相关」在 occ_a 口径下存活**（q/r 尾冻=独立终局现象不计入活动窗判据）；
  因果机制未闭合（§503 勘误口径维持）。
- **A'' 重启实验地位不变**：v4-c 基线（BOOT 内小时尺度振荡）+本审计（occ_a 标准化）——重启判别力
  下修维持，交用户决策；B（BOOT 证据表）在飞。
- 有界高估方向如实（census 与 occ_a 同担）：>10ms 采样洞并入停滞——v3a w2 上界 96.61%→≥88.0%
  （洞内推进除 hb w1 三处 +2 外全 +1，偏置毫秒级预期）。趟数 40 不变。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S505)
b = append_lines(GOAL, S505)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
