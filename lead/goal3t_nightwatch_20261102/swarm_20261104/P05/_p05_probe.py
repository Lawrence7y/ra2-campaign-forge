# -*- coding: utf-8 -*-
"""P05 补针探针（只读，stdout-only）：
1) 平台规范枚举（直扫 bfs，含长度=1 平台）——对齐 _cal_probe.py 口径，核 237/224/251 等；
2) v4-b C 口径 244→251 分歧分解（尾平台 + 单样本平台）；
3) 「起始间隔中位 0.393/0.154」候选统计量搜索；
4) v4-b 两处 Δf>1 跳帧法医（局部拍间隔/邻域推进间隔）；
5) 四分位推进速率（ regime 概览）。
"""
import json
import statistics as st
from pathlib import Path

BASE = Path(r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
TRIPS = {"b": "l3_1101v4b", "c": "l3_1101v4c", "d": "l3_1101v4d", "e": "l3_1101v4e"}
T = 0.1


def load(tag):
    d = json.load(open(BASE / TRIPS[tag] / "h8_wait_trace.json", encoding="utf-8"))
    ts = [s[0] for s in d["samples"]]
    fs = [s[1] for s in d["samples"]]
    first = next(i for i in range(1, len(fs)) if fs[i] > fs[i - 1])
    return d, ts, fs, first


def plateaus(ts, fs, first):
    bts, bfs = ts[first:], fs[first:]
    out = []
    i, n = 0, len(bfs)
    while i < n:
        j = i
        while j + 1 < n and bfs[j + 1] == bfs[i]:
            j += 1
        b = bts[j] - bts[i]
        d_in = bts[i + 1] - bts[i] if i + 1 < n else None
        gap_out = bts[j + 1] - bts[j] if j + 1 < n else None
        if d_in is None:
            a, kind = None, "head"
        elif gap_out is None:
            a, kind = b - d_in, "tail"
        else:
            a, kind = b + gap_out - d_in, "interior"
        out.append({"i": i, "j": j, "frame": bfs[i], "t0": bts[i], "t1": bts[j],
                    "B": b, "d_in": d_in, "gap_out": gap_out, "A": a, "A_kind": kind,
                    "C": None if gap_out is None else b + gap_out,
                    "len1": j == i})
        i = j + 1
    return bts, bfs, out


def cnt(rows, key, thr=T):
    sel = [r for r in rows if r[key] is not None and r[key] >= thr]
    return len(sel), sum(r[key] for r in sel)


print("=" * 78)
print("## 1) 规范平台枚举（含长度=1）三口径核对")
for tag in TRIPS:
    d, ts, fs, first = load(tag)
    bts, bfs, rows = plateaus(ts, fs, first)
    span = bts[-1] - bts[0]
    nA, tA = cnt(rows, "A")
    nB, tB = cnt(rows, "B")
    nC, tC = cnt(rows, "C")
    len1 = [r for r in rows if r["len1"]]
    len1C = [r for r in len1 if r["C"] is not None and r["C"] >= T]
    print(f"v4-{tag}: 平台总数={len(rows)} (单样本平台={len(len1)}, 其中C>=100ms的={len(len1C)})  "
          f"A={nA}/{tA:.4f}s  B={nB}/{tB:.4f}s  C={nC}/{tC:.4f}s  span={span:.4f}s")

print()
print("=" * 78)
print("## 2) v4-b C 口径分歧分解")
d, ts, fs, first = load("b")
bts, bfs, rows = plateaus(ts, fs, first)
# 我的旧枚举：deltas[first:] 零游程（漏单样本平台）
deltas = [b - a for a, b in zip(fs, fs[1:])]
dl = deltas[first:]
old_runs = 0
start = None
oldB = []
for i in range(len(dl) + 1):
    hit = i < len(dl) and dl[i] == 0
    if hit and start is None:
        start = i
    elif not hit and start is not None:
        old_runs += 1
        oldB.append((start, i))
        start = None
tail = [r for r in rows if r["A_kind"] == "tail"]
len1_all = [r for r in rows if r["len1"]]
len1C = [r for r in len1_all if r["C"] is not None and r["C"] >= T]
print(f"旧枚举零游程数={old_runs}（=我报的255；单样本平台无零游程边被漏）")
print(f"规范平台数={len(rows)}；差={len(rows)-old_runs} 个单样本平台")
print(f"我的C=244 的构成: 零游程C>=100ms={244} （含尾平台裁剪 1 个）")
print(f"他们的C=251 = 零游程C>=100ms(不含尾) {244-1} + 单样本平台C>=100ms {len(len1C)} = {244-1+len(len1C)}")
print(f"单样本平台清单（v4-b，共{len(len1_all)}个）:")
for r in len1_all:
    mark = "  ←C计入" if (r["C"] is not None and r["C"] >= T) else ""
    print(f"  t={r['t0']:.3f}s frame={r['frame']} B={r['B']*1000:.1f}ms C={None if r['C'] is None else f'{r[chr(67)]*1000:.1f}ms'}{mark}")

print()
print("=" * 78)
print("## 3) 「起始间隔中位」候选统计量（v4-b 目标 0.393s / v4-c 目标 0.154s）")
for tag, target in (("b", 0.393), ("c", 0.154)):
    d, ts, fs, first = load(tag)
    bts, bfs, rows = plateaus(ts, fs, first)
    Aep = [r["A"] for r in rows if r["A"] is not None and r["A"] >= T]
    Bep = [r["B"] for r in rows if r["B"] >= T]
    Cep = [r["C"] for r in rows if r["C"] is not None and r["C"] >= T]
    # 推进时刻序列
    adv = [bts[i] for i in range(1, len(bfs)) if bfs[i] > bfs[i - 1]]
    aiv = [b - a for a, b in zip(adv, adv[1:])]
    print(f"v4-{tag} (目标 {target}):")
    print(f"  med(A段)={st.median(Aep):.4f}  med(B段)={st.median(Bep):.4f}  med(C段)={st.median(Cep):.4f}")
    print(f"  mean(A段)={st.mean(Aep):.4f}  mean(B段)={st.mean(Bep):.4f}  mean(C段)={st.mean(Cep):.4f}")
    print(f"  med(推进间隔)={st.median(aiv):.4f}  前10个推进间隔med={st.median(aiv[:10]):.4f}")

print()
print("=" * 78)
print("## 4) v4-b 跳帧法医")
d, ts, fs, first = load("b")
n = len(fs)
adv_idx = [i + 1 for i in range(n - 1) if fs[i + 1] > fs[i]]
for jid, ai in enumerate([i for i in adv_idx if fs[i] - fs[i - 1] > 1], 1):
    iv = ts[ai] - ts[ai - 1]
    # 邻域推进间隔：该跳前后各 3 个推进间隔
    k = adv_idx.index(ai)
    lo = max(0, k - 3)
    nb = [(adv_idx[m] - adv_idx[m - 1] and round(ts[adv_idx[m]] - ts[adv_idx[m - 1]], 3))
          for m in range(max(1, k - 2), min(len(adv_idx), k + 3))]
    print(f"跳帧{jid}: t={ts[ai]:.3f}s {fs[ai-1]}→{fs[ai]} (Δf={fs[ai]-fs[ai-1]})  "
          f"该边拍间隔={iv*1000:.1f}ms  邻域推进间隔={nb}")

print()
print("=" * 78)
print("## 5) 四分位推进速率（战斗段均分 4 段，净推进/时长）")
for tag in TRIPS:
    d, ts, fs, first = load(tag)
    bts, bfs = ts[first:], fs[first:]
    span = bts[-1] - bts[0]
    qs = []
    for q in range(4):
        lo = bts[0] + q * span / 4
        hi = lo + span / 4
        f_lo = bfs[0] + sum(1 for i in range(1, len(bfs)) if lo < bts[i] <= lo + 0)  # 占位
        # 用帧值插值
        import bisect as bi
        i0 = bi.bisect_right(bts, lo) - 1
        i1 = bi.bisect_right(bts, hi) - 1
        f0, f1 = bfs[max(i0, 0)], bfs[i1]
        qs.append((f1 - f0) / (hi - lo))
    print(f"v4-{tag}: Q1={qs[0]:.2f} Q2={qs[1]:.2f} Q3={qs[2]:.2f} Q4={qs[3]:.2f} 帧/s  "
          f"(战斗段 {span:.1f}s)")
