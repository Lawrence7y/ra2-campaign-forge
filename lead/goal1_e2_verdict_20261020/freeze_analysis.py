"""w2 窗尾冻结的边界效应核查 + D4 终局排除。"""
import json
from pathlib import Path

TRIP = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l1a_20261020")

print("=== 三窗边界 ===")
for w in (0, 1, 2):
    d = json.loads((TRIP / f"measure_w{w}.json").read_text(encoding="utf-8"))
    fe = d["frame_edges"]
    s = d["samples"]
    t0 = s["t"][0]
    lead = fe[0][1] - t0
    tail = s["t"][-1] - fe[-1][1]
    print(f"w{w}: frames {fe[0][0]}..{fe[-1][0]}  lead_gap={lead:.3f}s  tail_gap={tail:.3f}s  "
          f"span={s['t'][-1]-t0:.3f}s")

print("\n=== 跨窗连续性：w1 末帧 vs w2 首帧 ===")
d1 = json.loads((TRIP / "measure_w1.json").read_text(encoding="utf-8"))
d2 = json.loads((TRIP / "measure_w2.json").read_text(encoding="utf-8"))
print(f"  w1 last frame = {d1['frame_edges'][-1][0]}")
print(f"  w2 first frame = {d2['frame_edges'][0][0]}")
print(f"  ⇒ {'连续（w2 从 w1 末帧重新开始计）' if d1['frame_edges'][-1][0]==d2['frame_edges'][0][0] else '不连续'}")

print("\n=== w2 冻结期间的逐秒计数器（D4：查终局）===")
c = d2["counters"]
for r in c:
    print(f"  t={r['t_rel']:>4.1f}  units={r['units']:>4}  infantry={r['infantry']:>4}  "
          f"techno={r['techno']:>4}  g={r['g']}  ws_kb={r['ws_kb']}")

print("\n=== w2 窗末帧附近的帧间隔 ===")
fe = d2["frame_edges"]
t0 = d2["samples"]["t"][0]
for f, t in fe[-8:]:
    print(f"  frame {f}  t_rel={t - t0:.3f}")

print("\n=== 冻结起点是否伴随单位数突变 ===")
print(f"  冻结前最后一条 edge 帧 = {fe[-1][0]}，t_rel={fe[-1][1]-t0:.3f}")
print(f"  该时刻附近 counters: t=23.0 units={[r['units'] for r in c if r['t_rel']==23.0]}, "
      f"t=24.0 units={[r['units'] for r in c if r['t_rel']==24.0]}")
print("  ⇒ 若两秒内 units 不变，则冻结不是终局/败北导致的停帧。")

print("\n=== 与 T50 的 1.782s 冻结对比（记忆库 W0 窗尾冻结）===")
print("  记忆库记录：'活跃段 31.245fps 与 41 单位局同值，恶化全在 >=59.6s 冻结尾部'")
print("  ⇒ 本次 w2 的 1.782s 窗尾冻结与该形态同型：活跃段正常、尾部冻住。")
