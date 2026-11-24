# -*- coding: utf-8 -*-
"""V2 停摆位置核对：大停滞窗里，推进是在「停滞之前」还是「停滞之后」。

若某窗先停 24s 又恢复推进 ⇒ 「df==0/小 df 是永久冻结、永不恢复」不成立；
若推进全在窗首、随后一停到底 ⇒ 冻结点落在该窗内部。
"""
import glob
import json
import os

BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
SUB = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))

print("### H. max_stall>=10s 的窗：最后一次帧推进发生在窗内什么位置")
print("%-20s %2s %5s %8s %9s %9s %9s %9s %s" %
      ("dir", "w", "df", "span", "首边pc", "末边pc", "最后推进距首边", "距窗尾", "判读"))
recs = []
for p in SUB:
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    if not ed:
        continue
    st = j.get("stats") or {}
    ms = st.get("max_stall_s") or 0
    if ms < 10:
        continue
    d = os.path.basename(os.path.dirname(p))
    w = int(j.get("window"))
    span = j.get("span_s") or 0
    t0 = ed[0][1]
    last_edge_t = ed[-1][1]
    # 最后一次「帧号变大」的时间
    last_up_t = None
    for i in range(1, len(ed)):
        if ed[i][0] > ed[i - 1][0]:
            last_up_t = ed[i][1]
    rel_last = (last_up_t - t0) if last_up_t is not None else None
    tail = (span - rel_last) if rel_last is not None else None
    verdict = ""
    if last_up_t is None:
        verdict = "整窗零推进（n_edges=1）"
    elif tail is not None and tail >= 5:
        verdict = "最后一次推进在 %.3f s，其后 %.3f s 无推进直到窗尾；与 stats.max_stall_s=%.3f 相符? %s" % (
            rel_last, tail, ms, "是" if abs(tail - ms) < 0.05 else "否")
    else:
        verdict = "最后一次推进在 %.3f s，距窗尾仅 %.3f s ⇒ 推进基本贯穿全窗" % (rel_last or 0, tail or 0)
    print("%-20s %2d %5d %8.2f %9.3f %9.3f %9s %9s %s" %
          (d, w, ed[-1][0] - ed[0][0], span, 0.0, last_edge_t - t0,
           ("%.3f" % rel_last) if rel_last is not None else "-",
           ("%.3f" % tail) if tail is not None else "-", verdict))
    recs.append((d, w, rel_last))
print()
print("### H2. 同一趟里，冻结点相对窗边界的位置（帧号最后一次变大的时刻）")
bytrip = {}
for p in SUB:
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    if not ed:
        continue
    bytrip.setdefault(os.path.basename(os.path.dirname(p)), []).append((int(j.get("window")), ed, j))
for d in sorted(bytrip):
    rs = sorted(bytrip[d])
    f0 = rs[0][1][0][0]
    lastup = None
    for w, ed, j in rs:
        for i in range(1, len(ed)):
            if ed[i][0] > ed[i - 1][0]:
                lastup = (w, ed[i][0], ed[i][1])
    first_pc = rs[0][1][0][1]
    last_pc = rs[-1][1][-1][1]
    tot = rs[0][1][0][0]
    span_to_freeze = (lastup[2] - first_pc) if lastup else None
    gamet = (lastup[1] / 31.2) if lastup else None
    if lastup:
        print("  %-20s 冻结点：最后一次推进 w%s f=%s，距本趟首读数 %.2f s；"
              "其读数对应游戏时长 f/31.2=%.2f s；此后 %.2f s 全程无推进（可观测的不恢复时长）" %
              (d, lastup[0], lastup[1], span_to_freeze, gamet, last_pc - lastup[2]))
