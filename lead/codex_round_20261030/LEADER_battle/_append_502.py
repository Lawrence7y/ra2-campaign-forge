# -*- coding: utf-8 -*-
"""_append_502.py - append S502 (boot-level discriminator census) to shared ledgers. Additive only."""


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


S502 = """

# §502　全库停滞占比普查（28 趟×全部窗，Leader 亲算，tee `stall_census_20261101.txt`）：
#        **①判别单元=BOOT**——单位量主因被排除（t55k 841u=0% vs l1c 879u=70%，差 38u 天壤）；
#        滞态 BOOT 2 个（10-21、10-31~11-01 同 BOOT）、健康 BOOT 3 个（10-20/23/30）

- **方法**：全部带窗趟（含 archive_T 小图系列）逐窗停滞占比（>0.1s 间隙合计/窗跨度）+units0 并表。
- **决定性对照**：① **t55k（10-20 BOOT）841u=0% 全窗 31fps vs l1c（10-21 BOOT）879u=70%**——同图
  （L1/sf8）、单位差 38、停滞天壤 ⇒ 单位量主因排除；② q/r（10-30）811-953u=0% vs l3_20261021（10-21）
  1184-1330u=39-71% ⇒ 跨图档一致；③ 10-31 BOOT（08:26 起）跨夜延续至 11-01（v3/v4 趟 06:50-09:10）
  ⇒ 10-31/11-01 为同一 BOOT。
- **BOOT 分档表**：健康={10-20、10-23、10-30}（全部窗 0-1.9% 停滞、31fps 或图档对应帧率）；滞态=
  {10-21、10-31~11-01}（25-100%）。会话方差=**BOOT 级属性**（Y-11 框架再细化：不是「会话」是「BOOT」）。
- **旁证/异常如实**：l3_20261023q w2（811u）fps=4.8 但停滞 0 段——均匀慢窗（无 >0.1s 间隙）形态待判
  （帧沿数少或第三态）；l1_20261023k（units0=0 空图）49% 停滞=非战斗停滞样本；archive_T 系列部分窗
  帧沿不足（verdict=ok 但样本稀）。
- **①完整因果链（当前证据支撑）**：BOOT 决定帧钟是否周期性停滞（滞态 BOOT：~5Hz 泵动签名、停滞占比
  6-100% 窗间切换、episode 10-30s+）→ 满员早期交火相位受停滞影响最重（fps 3-17 vs 帽 31）→ 用户主诉。
  **机制归因（什么让 BOOT 进入滞态）仍开放**——需跨 BOOT 对照（重启干预实验=用户动作）或 E3。
- **A'' 设计输入（终版）**：判别实验=**重启后单趟 v4 轨迹批**（若新 BOOT 零停滞 ⇒ BOOT 级瞬态实锤、
  且重启=可操作修复动作；若仍滞 ⇒ 持久软件态）。重启=用户机器动作，须用户执行。
- 趟数 39 不变；输出 tee 在 LEADER_battle/。句态按 §496+§498-500+本节。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S502)
b = append_lines(GOAL, S502)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
