# -*- coding: utf-8 -*-
"""P04 VERIFY data-side —— 独立复算 P04 报告全部数据侧 keyFacts。
不复用 P04_probe1.py 的逻辑：从 JSON 原始字节重新实现全部口径。
零真机、零启动、只读。
"""
import json, glob, os, statistics
from collections import Counter

BASE = r"D:/Project/ra2-campaign-forge/lead/qc161_u0400_trip/c2ab_x"

def iv(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    return x

def pct(sorted_xs, p):
    if not sorted_xs:
        return None
    k = max(0, min(len(sorted_xs) - 1, int(p * len(sorted_xs))))
    return sorted_xs[k]

files = sorted(glob.glob(os.path.join(BASE, "*", "timeline.json")))
print("[F1] timeline.json 文件数 =", len(files))
sa = sb = 0
rows_total = 0
tick_dist = Counter()          # 全批 tick 值分布（repr 键）
readfail_rows = []             # (trip, seg, idx, is_last, exit_kind)
per_seg_rows = Counter()

recs = {}   # trip -> dict(rows=[(seg,row)], rec=_rec.json)
for path in files:
    trip = os.path.basename(os.path.dirname(path))
    d = json.load(open(path, encoding="utf-8"))
    rp = os.path.join(os.path.dirname(path), "_rec.json")
    rec = json.load(open(rp, encoding="utf-8")) if os.path.exists(rp) else {}
    rows = []
    if "battle_tl" in d:
        schema = "A"; sa += 1
        for r in (d.get("battle_tl") or []):
            rows.append(("battle", r))
    else:
        schema = "B"; sb += 1
        for r in (d.get("hold_tl") or []):
            rows.append(("hold", r))
    for r in (d.get("pre5") or []):
        s = dict(r.get("sent", r))
        s.setdefault("t", r.get("t"))
        rows.append(("pre5", s))
    for r in (d.get("close_rows") or []):
        rows.append(("close", r))
    rows.sort(key=lambda x: (iv(x[1].get("t")) is None, iv(x[1].get("t")) or 0.0))
    recs[trip] = dict(rows=rows, rec=rec, schema=schema)
    rows_total += len(rows)
    for seg, r in rows:
        per_seg_rows[seg] += 1
        tv = iv(r.get("tick"))
        if tv is None:
            readfail_rows.append((trip, seg, r.get("tick"), rec.get("exit_kind", "?")))
        else:
            tick_dist[int(tv)] += 1

print("[F1] schema-A=%d schema-B=%d" % (sa, sb))
print("[F2] 总行数 =", rows_total, "| 分段:", dict(per_seg_rows))
print("[F3] tick 值分布 =", dict(tick_dist), "| tick==0 出现", tick_dist.get(0, 0), "次")
print("[F4] read_fail 行数 =", len(readfail_rows))
for trip, seg, raw, ek in readfail_rows:
    rows = recs[trip]["rows"]
    idx = next(i for i, (sg, r) in enumerate(rows) if sg == seg and r.get("tick") is raw)
    is_last = (idx == len(rows) - 1)
    print("     %s seg=%s exit=%s 行号=%d/%d 末行=%s" % (trip, seg, ek, idx, len(rows) - 1, is_last))

# ============ 相邻对：全序列口径（每文件 t 排序后全行） ============
pair_full = Counter()          # (class_df, tickpat) -> n
neg_pairs = []
skip_unread = 0
cross_singleton_df0 = []
for trip, info in recs.items():
    rows = info["rows"]
    for (sa_, ra), (sb_, rb) in zip(rows, rows[1:]):
        fa, fb = iv(ra.get("frame")), iv(rb.get("frame"))
        ka, kb = iv(ra.get("tick")), iv(rb.get("tick"))
        ta, tb = iv(ra.get("t")), iv(rb.get("t"))
        sina, sinb = iv(ra.get("singleton")), iv(rb.get("singleton"))
        if None in (fa, fb, ka, kb, ta, tb):
            skip_unread += 1
            continue
        fa, fb, ka, kb = int(fa), int(fb), int(ka), int(kb)
        df = fb - fa
        tp = (ka, kb)
        cross_sin = (sina is not None and sinb is not None and sina != sinb)
        if df == 0:
            pair_full[("df0", tp)] += 1
            if cross_sin:
                cross_singleton_df0.append((trip, sa_, sb_, tp))
        elif df > 0:
            pair_full[("dfpos", tp)] += 1
        else:
            pair_full[("dfneg", tp)] += 1
            neg_pairs.append((trip, df, tp, sa_, sina, sinb,
                              ra.get("hwnd"), rb.get("hwnd"), ta, tb))

print("\n[F5] 全序列口径：可读对合计 =", sum(pair_full.values()),
      "(rows", rows_total, "- files", len(files), "- skip_unread", skip_unread, ")")
df0 = sum(v for (c, t), v in pair_full.items() if c == "df0")
dfp = sum(v for (c, t), v in pair_full.items() if c == "dfpos")
dfn = sum(v for (c, t), v in pair_full.items() if c == "dfneg")
print("[F5] Δf==0 对 =", df0, "| Δf>0 对 =", dfp, "| Δf<0 对 =", dfn)
print("[F5] Δf==0 对的 tick 模式 =", {str(k): v for (c, k), v in pair_full.items() if c == "df0"})
print("[F5] Δf>0  对的 tick 模式 =", {str(k): v for (c, k), v in pair_full.items() if c == "dfpos"})
print("[F5] Δf<0  对的 tick 模式 =", {str(k): v for (c, k), v in pair_full.items() if c == "dfneg"})
from collections import Counter as _C
_pat = _C(str(t) for _, _, _, t in cross_singleton_df0)
print("[F5] 跨 singleton 变界的 Δf==0 对 =", len(cross_singleton_df0),
      "→ 剔除后 =", df0 - len(cross_singleton_df0),
      "| 这些对的 tick 模式 =", dict(_pat))
for x in cross_singleton_df0:
    print("       ", x[0], x[1], "->", x[2], "tick=", x[3])

print("\n[F6] Δf<0 对明细（应为 4 个清零跌落）：")
for trip, df, tp, seg, sina, sinb, ha, hb, ta, tb in neg_pairs:
    print("     %s seg=%s Δf=%d tick=%s singleton %s->%s hwnd %s->%s" %
          (trip, seg, df, tp, sina, sinb, ha, hb))

# ============ 段内（剔除跨 singleton）口径 + 三分类 ============
cls_cnt = Counter()
seg_cls = Counter()
zeroed_nonzero_hwndsin = 0
relevant_detail = []
df0_inrun = 0
for trip, info in recs.items():
    mode = info["rec"].get("mode", "?")
    rows = info["rows"]
    # 运行段切分：singleton 值变化处
    runs, cur, prev = [], [], "NA"
    for seg, r in rows:
        sin = iv(r.get("singleton"))
        if cur and sin is not None and prev is not None and sin != prev:
            runs.append(cur); cur = []
        cur.append((seg, r))
        if sin is not None:
            prev = sin
    if cur:
        runs.append(cur)
    for run in runs:
        for (sa_, ra), (sb_, rb) in zip(run, run[1:]):
            fa, fb = iv(ra.get("frame")), iv(rb.get("frame"))
            ka, kb = iv(ra.get("tick")), iv(rb.get("tick"))
            if None in (fa, fb, ka, kb):
                continue
            fa, fb, ka, kb = int(fa), int(fb), int(ka), int(kb)
            if fb - fa != 0:
                continue
            df0_inrun += 1
            segtag = sa_ if sa_ == sb_ else "X(%s>%s)" % (sa_, sb_)
            ha, hb = iv(ra.get("hwnd")), iv(rb.get("hwnd"))
            sina = iv(rb.get("singleton"))
            zeroed = (ha == 0 or hb == 0 or sina == 0)
            menu_idle = (fa == 0 and fb == 0 and (mode == "menu" or segtag in ("battle", "hold", "pre5")))
            cls = "menu_idle" if menu_idle else ("zeroed" if zeroed else "RELEVANT")
            cls_cnt[(cls, segtag, (ka, kb))] += 1
            if cls == "zeroed" and not (ha == 0 or hb == 0 or sina == 0):
                zeroed_nonzero_hwndsin += 1
            if cls == "RELEVANT":
                relevant_detail.append((trip, mode, segtag, fa, fb, (ka, kb), ha, hb, sina))

print("\n[F7] 段内口径 Δf==0 对 =", df0_inrun)
mi = sum(v for (c, s, t), v in cls_cnt.items() if c == "menu_idle")
ze = sum(v for (c, s, t), v in cls_cnt.items() if c == "zeroed")
re_ = sum(v for (c, s, t), v in cls_cnt.items() if c == "RELEVANT")
print("[F7] menu_idle=%d zeroed=%d RELEVANT=%d" % (mi, ze, re_))
for (c, s, t), v in sorted(cls_cnt.items()):
    print("      %-10s %-16s tick=%-8s x %d" % (c, s, str(t), v))
print("[F7] zeroed 类中 hwnd/singleton 不为 0 的对 =", zeroed_nonzero_hwndsin, "（应为 0）")
if relevant_detail:
    print("[F7] RELEVANT 明细：")
    for x in relevant_detail:
        print("      ", x)

# 独立严格口径：不依赖 menu_idle 规则——「活游戏停帧」候选 =
# Δf==0 且 frame 两端均 >0 且 hwnd 两端均>0 且 singleton 两端均>0 且 tick 两端==1
live_stall = 0
live_stall_list = []
for trip, info in recs.items():
    rows = info["rows"]
    for (sa_, ra), (sb_, rb) in zip(rows, rows[1:]):
        fa, fb = iv(ra.get("frame")), iv(rb.get("frame"))
        ka, kb = iv(ra.get("tick")), iv(rb.get("tick"))
        ha, hb = iv(ra.get("hwnd")), iv(rb.get("hwnd"))
        sina, sinb = iv(ra.get("singleton")), iv(rb.get("singleton"))
        if None in (fa, fb, ka, kb, ha, hb, sina, sinb):
            continue
        if int(fb) - int(fa) == 0 and fa > 0 and ka == 1 and kb == 1 and ha > 0 and hb > 0 and sina != 0 and sinb != 0:
            live_stall += 1
            if len(live_stall_list) < 10:
                live_stall_list.append((trip, sa_, fa, (ka, kb), ha, sina))
print("\n[F8] 严格口径「活游戏停帧候选」对（frame>0,hwnd>0,singleton>0,tick=1,Δf==0）=", live_stall)
if live_stall_list:
    for x in live_stall_list:
        print("      ", x)

# ============ 清零跌落上下文（P1 085640） ============
print("\n[F9] 清零跌落上下文 20261028T085640_0001_P1_G1B0exp close 段：")
info = recs["20261028T085640_0001_P1_G1B0exp"]
cl = [(i, r) for i, (sg, r) in enumerate(info["rows"]) if sg == "close"]
drop_idx = None
for j in range(1, len(cl)):
    f0, f1 = iv(cl[j-1][1].get("frame")), iv(cl[j][1].get("frame"))
    if f0 is not None and f1 is not None and f1 < f0:
        drop_idx = j
        break
if drop_idx is not None:
    for j in range(max(0, drop_idx - 3), min(len(cl), drop_idx + 3)):
        i, r = cl[j]
        print("      close[%d] t=%.2f wait=%s hwnd=%s singleton=%s frame=%s tick=%s exitstate=%s" %
              (i, r.get("t", -1), r.get("wait"), r.get("hwnd"), r.get("singleton"),
               r.get("frame"), r.get("tick"), r.get("exitstate")))

# ============ 采样间隔（段内，按文件内同段相邻行） ============
seg_dts = {s: [] for s in ("battle", "hold", "pre5", "close")}
for trip, info in recs.items():
    by_seg = {}
    for seg, r in info["rows"]:
        t = iv(r.get("t"))
        if t is not None:
            by_seg.setdefault(seg, []).append(t)
    for seg, ts in by_seg.items():
        ts.sort()
        seg_dts[seg] += [b - a for a, b in zip(ts, ts[1:])]
print("\n[F10] 各段采样间隔：")
for seg in ("battle", "hold", "pre5", "close"):
    xs = sorted(seg_dts[seg])
    if xs:
        print("      seg=%-7s n=%-5d 中位=%.3f p10=%.3f p90=%.3f" %
              (seg, len(xs), statistics.median(xs), pct(xs, 0.10), pct(xs, 0.90)))

# ============ 战斗趟 close 帧率 ============
print("\n[F11] 战斗趟 close 段帧率：")
for trip, info in recs.items():
    if info["rec"].get("mode") != "battle":
        continue
    ts = [iv(r.get("t")) for sg, r in info["rows"] if sg == "close"]
    fs = [iv(r.get("frame")) for sg, r in info["rows"] if sg == "close"]
    pairs = [(a, b, int(fb) - int(fa)) for a, b, fa, fb in zip(ts, ts[1:], fs, fs[1:])
             if None not in (a, b, fa, fb)]
    if not pairs:
        print("      %-42s 无有效 close 对" % trip)
        continue
    dts = [b - a for a, b, _ in pairs]
    dfs = [d for _, _, d in pairs]
    dur = pairs[-1][1] - pairs[0][0]
    print("      %-42s dur=%.1fs Δframe=%+d fps=%.2f minΔf=%d df0对=%d" %
          (trip, dur, fs[-1] - fs[0], (fs[-1] - fs[0]) / dur if dur else 0, min(dfs),
           sum(1 for d in dfs if d == 0)))

# ============ 菜单趟 close/hold profile ============
print("\n[F12] 菜单趟各段 frame/tick 值集（抽样核对设计停帧）：")
for trip, info in recs.items():
    if info["rec"].get("mode") != "menu":
        continue
    for seg in ("battle", "hold", "pre5", "close"):
        fr = sorted(set(int(r["frame"]) for sg, r in info["rows"] if sg == seg and iv(r.get("frame")) is not None))
        tk = sorted(set(int(r["tick"]) for sg, r in info["rows"] if sg == seg and iv(r.get("tick")) is not None))
        n = sum(1 for sg, r in info["rows"] if sg == seg)
        if n:
            print("      %-42s %-6s n=%-4d frame集=%s tick集=%s" % (trip, seg, n, fr, tk))
print("\n[VERIFY_DATA DONE]")
