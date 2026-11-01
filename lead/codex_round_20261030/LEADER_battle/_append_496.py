# -*- coding: utf-8 -*-
"""_append_496.py - append S496 (v3 batch closure) to shared ledgers. Additive only."""


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


S496 = """

# §496　v3 三趟批收口（l3_1101v3a/b/c，≤3 趟批内 ≈10min）：H8-5 闸分档真机生效（三窗全开）；
#        **C-1 分流判定=轮询非主因**（混合 0.89-1.90×、无一致 ≥2×、p50 重叠）；会话计票 **3/4 慢**；
#        v3-c 超时拒采（overrun_kind=timeout 生产实证，Y-R5）；fps-units 非单调新观察；趟数 37

- **发射面**：v3 发射器三趟全 rc=0（218.7/182.7/200.6s）；out-dir 实测 127≤130（C-R2 真机实证）；
  A8/A11 全 OK（A11=37a7c9cd）；载体清、procs=0；批后冻结 h7/gamemd/v2/v3 四件逐位（双锚维持）。
- **v3-a（N=400，500Hz 名义）**：武装 reached=400/offset=0（wait 65.5s/20332 拍≈310Hz）；
  **H8-5 闸分档真机生效**（h7_gate_override：frames_advanced=True ⇒ gate_ok=True，pre_fps15=8.689
  转数据）⇒ **三窗全开**（ha 型短路消除——判据失配修正实证）；w0(434-724) fps 11.6/p50 82.5/
  stall 0.202、w1(724-1075) fps 14.0/p50 70.3/stall 0.129、w2(1075-1222) fps 5.9/p50 166.8/stall 0.309；
  units 窗首/末：1336→1265｜1262→1147｜1145→1107；判档 EXIT=1（V11-a min 8.689<25——本批为数据不设门）。
- **v3-b（N=400，--h8-wait-hz 50）**：旋钮真机生效（h8_wait_hz=50；wait 40.0s/1932 拍=**48.3Hz** 实折）；
  武装 offset=0；三窗全开：w0(454-872) fps 16.7/p50 55.3/stall 0.141、w1(873-1182) fps 12.4/p50 55.7/
  stall 0.307、w2(1182-1462) fps 11.2/p50 76.1/stall 0.262；units：1338→1215｜1211→1117｜1114→1066；
  判档 EXIT=1。
- **C-1 分流判定（轮询归因）**：v3-a 再现慢帧（前提成立）；v3-b vs v3-a 同会话同 N 配对：
  fps 比 1.44/0.89/1.90（**混合、无一致 ≥2×**）、p50 区间重叠（55-76 vs 70-167ms）⇒
  **轮询非主因（慢帧非 500Hz 轮询伪影；归因闭合主项=趟间/会话方差）**。诚实限：配对窗相位未完全
  对齐（帧域不同）、w2 比值 1.90 接近 2——判定书须带此限；主因定位=会话/趟级因素（装载+早相墙钟
  方差旁证：同会话绑帧等待 65.5 vs 40.0s）。
- **v3-c（N=1200）**：**frame_wait_timeout 拒采**——120.05s 帽内 reached=1058（≈8.8fps 均值，含装载），
  overrun_kind='timeout' 生产可见（Y-R5 实证）；判档 EXIT=3；阈定位无结论（v3-b w2 部分覆盖
  1182-1462@11.2fps——units≈1100 仍慢）；**旁证=本会话慢相延续 ≥1058 帧**（非仅 400-1000 窄带）。
- **会话计票（Y-11 口径）**：满员早相慢帧 **3/4 会话**（10-21 慢 7.4fps / 10-30 快 ≥23.7 / 10-31 慢
  3-11 / 11-01 慢 5.9-14.0）——会话强方差维持；**fps-units 非单调**新观察（v3-a w2 单位量最低而 fps
  最低）⇒ 单位量单独不决定帧率（交火强度/事件密度候选）。
- **判读纪律落地**：窗数按实落（v3-a/b=3 窗、v3-c=0 窗）；units 链窗首/窗末并列；units0=窗级 counters
  首行（1336/1338，gate 值 1347 并列沿用 Y-9）；收尾=无中途强杀+缺省 terminate（Y-10）；「再现」带
  会话分母（Y-11）。
- 批判定：≤3 趟帽内收口；无弹框/交互；载体清；趟数 **34→37**。句态：**①满员早相慢帧再现于 3/4 会话
  （会话强方差；轮询非主因已判别；fps-units 非单调）**；②硬门槛未达成、RC-4 不收口；③保持态
  （v2/v3 双锚冻结维持、五件冻结件零字节）。
- **下一最小动作（待用户裁）**：A'=慢因定位下一层（会话方差内：装载顺序/驱动状态/驻留内存？或
  跨会话受控重演批）；C=热点定位（E3 未授权）；D=维持。判定书建议：v3 数据足供设计下一轮判别实验。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
TRIPIDX = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x\TRIP_INDEX_20261028.md"

IDX = """
- 趟 `l3_1101v3a`（…V3-20261101A）：harness8 v3 37a7c9cd／N=400/500Hz／H8-5 闸分档生效三窗全开／
  units0=1336／fps 11.6/14.0/5.9／p50 82.5/70.3/166.8ms／stall 0.202/0.129/0.309／判档 EXIT=1（V11-a
  数据不设门）／rc=0。
- 趟 `l3_1101v3b`（…B）：--h8-wait-hz 50（实折 48.3Hz）／units0=1338／fps 16.7/12.4/11.2／p50 55.3/
  55.7/76.1／stall 0.141/0.307/0.262／判档 EXIT=1／rc=0。**C-1 判定=轮询非主因**。
- 趟 `l3_1101v3c`（…C）：N=1200 ⇒ frame_wait_timeout（reached=1058/120s，overrun_kind=timeout——
  Y-R5 实证）／判档 EXIT=3／阈定位无结论（v3-b w2 部分覆盖）。rc=0。
- 批判定：慢帧 3/4 会话+轮询非主因+fps-units 非单调；冻结四件+procs=0 复验过；趟数 37。
"""

a = append_lines(LOG, S496)
b = append_lines(GOAL, S496)
c = append_lines(TRIPIDX, IDX)
print("APPENDED LOG +%d, GOAL +%d, TRIPIDX +%d" % (a, b, c))
