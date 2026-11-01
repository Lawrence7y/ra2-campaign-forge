# -*- coding: utf-8 -*-
"""_append_497.py - append S497 (burst-stall structure finding) to shared ledgers. Additive only."""


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


S497 = """

# §497　①现象重定义（v3-a/b 产物离线深挖，Leader 亲算）：**「慢相」实为「爆发-停滞」结构**——
#        推进帧时中位 2.5ms（≈400fps 突发能力）+ 帧钟停滞占比 ~96-98%（0.1-3.8s 长停滞交替）；
#        内存列平坦（ws 134MB/pf 零增长）⇒ 无内存压力信号；「均匀低 fps」旧解读作废

- **方法**：v3-a/b 六窗 JSON samples（500Hz (t,frame) 对）逐对重算——「推进对」(f[i+1]>f[i]) 的
  间隔中位 vs 窗均 fps vs 停滞占比（帧数×2.5ms/窗长 反推）。输出 tee `offline_v3ab_mining.txt`。
- **数字**：六窗推进帧时中位 **2.5ms**（v3-a w2=4.9ms）；≤45ms 占比 89-100%；>100ms 停滞段每窗
  1-2 个（max 0.10-0.12s 短停滞 + 长停滞以帧沿间隔形式存在）；算术核验 v3-a w0：290 帧全速需 0.73s
  /窗长 25s ⇒ **停滞占比 ≈97%**。六窗帧沿数 147-418 与窗均 fps 一致。
- **口径澄清（判定书须并列）**：harness stats frame_ms_p50（82.5 等）=帧沿间隔中位**含停滞段**；
  本挖 2.5ms=**爆发群内推进节律**——两口径分母不同、各自成立。
- **①现象重定义**：用户主诉「卡顿」的微观形态=**突发快帧 + 百毫秒级冻结交替**（爆发-停滞），
  非「均匀低 fps」——病灶指向逻辑/同步/泵送阻塞类，而非每帧渲染工作量。fps-units 非单调（§496）
  与此自洽：停滞段时长受交火事件驱动，与瞬时单位量弱相关。
- **对 A'/C 的设计影响**：下一判别实验的目标量=**停滞段时长谱/频次/触发相关性**（沿帧轴与 units 轴
  分布），非「均匀 fps」；受控重演批的对齐轴=停滞谱而非均值 fps。E3 栈采样（未授权）的采点时机
  =停滞段内（其方案 §1.1 触发条件与此吻合，若获批价值更高）。
- 内存列（ws/pf）平坦如实登记；趟数 37 不变；句态按 §496 维持。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

a = append_lines(LOG, S497)
b = append_lines(GOAL, S497)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
