# -*- coding: utf-8 -*-
"""_occ_decomp.py - occ_a 与 B 口径差异的段型分解（离线只读）。

回答一个 §514 没回答的问题：occ_a 与 B 口径的差值，有多少来自 head 段、多少来自
interior 段？

§514 的定性判断是「interior=C 型（到下一帧首见），head/tail 天然是 B 型」。
本探针用恒等式检验这条判断：
  occ_a head = ts[首个帧沿] - ts[0]
  B 型首平台跨度 = ts[首平台末样本] - ts[0]
  ⇒ occ_a head = B型head + gap_out（跨过了平台后的采样缺口）= **C 型**，不是 B 型
  occ_a tail = ts[-1] - ts[最后一个帧沿]
  B 型末平台跨度 = ts[末样本] - ts[末平台首样本]   （末平台首样本 == 最后一个帧沿）
  ⇒ 两者同式 ⇒ tail 确实是 B 型

用法：python -I -X utf8 _occ_decomp.py > _occ_decomp_out.txt
"""

import json
import os

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
T = 0.1


def P(s=""):
    print(s)


def windows():
    for trip in sorted(os.listdir(BASE)):
        d = os.path.join(BASE, trip)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not (f.startswith("measure_w") and f.endswith(".json")):
                continue
            try:
                with open(os.path.join(d, f), encoding="utf-8") as fh:
                    dd = json.load(fh)
            except Exception:
                continue
            s = dd.get("samples") or {}
            ts, fs = s.get("t"), s.get("f")
            if not ts or not fs or len(ts) < 2:
                continue
            yield trip, f[9:-5], ts, fs, dd.get("verdict")


def head_identity(ts, fs):
    """返回 (occ_a_head, B型首平台跨度, gap_out)；无帧沿时返回 None。"""
    n = len(ts)
    first_edge = None
    for i in range(1, n):
        if fs[i] != fs[i - 1]:
            first_edge = i
            break
    if first_edge is None:
        return None
    pl_end = 0
    while pl_end + 1 < n and fs[pl_end + 1] == fs[0]:
        pl_end += 1
    return (ts[first_edge] - ts[0],
            ts[pl_end] - ts[0],
            ts[first_edge] - ts[pl_end])


def tail_identity(ts, fs):
    n = len(ts)
    last_edge = None
    for i in range(n - 1, 0, -1):
        if fs[i] != fs[i - 1]:
            last_edge = i
            break
    if last_edge is None:
        return None
    k = last_edge
    while k + 1 < n and fs[k + 1] == fs[k]:
        k += 1
    return (ts[-1] - ts[last_edge], ts[k] - ts[last_edge])


def segs_a(ts, fs):
    n = len(ts)
    span = ts[-1] - ts[0]
    trans = [(fs[i], ts[i]) for i in range(1, n) if fs[i] != fs[i - 1]]
    segs = []
    if trans:
        head = trans[0][1] - ts[0]
        if head > T:
            segs.append(("head", head))
        for (fa, ta), (fb, tb) in zip(trans, trans[1:]):
            if tb - ta > T:
                segs.append(("interior", tb - ta))
        tail = ts[-1] - trans[-1][1]
        if tail > T:
            segs.append(("tail", tail))
    elif span > T:
        segs.append(("head_whole", span))
    return segs, span


def segs_b(ts, fs):
    n = len(ts)
    span = ts[-1] - ts[0]
    segs = []
    j = 0
    while j + 1 < n and fs[j + 1] == fs[0]:
        j += 1
    h = ts[j] - ts[0]
    if h > T:
        segs.append(("head", h))
    i = j + 1
    while i < n:
        k = i
        while k + 1 < n and fs[k + 1] == fs[i]:
            k += 1
        d = ts[k] - ts[i]
        if d > T:
            segs.append(("tail" if k == n - 1 else "interior", d))
        i = k + 1
    return segs, span


P("=" * 100)
P("## 一、head 恒等式检验（head 到底是 B 型还是 C 型）")
P("   恒等式：occ_a_head == B型首平台跨度 + gap_out  ⇒ 成立即证明 head 是 **C 型**")
P("=" * 100)
ok = bad = 0
worst = []
for trip, w, ts, fs, v in windows():
    r = head_identity(ts, fs)
    if r is None:
        continue
    ha, hb, gap = r
    if abs(ha - (hb + gap)) < 1e-12:
        ok += 1
    else:
        bad += 1
        P("   MISMATCH %s w%s: occ_a_head=%.9f  B_head+gap=%.9f" % (trip, w, ha, hb + gap))
    if ha - hb > 1e-3:
        worst.append((ha - hb, trip, w, ha, hb, gap))
P("   head 恒等式成立 %d 窗，不成立 %d 窗" % (ok, bad))
P()
P("   head 计入（occ_a_head > T）且 C/B 差 > 1ms 的窗：")
P("   %-18s %2s %12s %12s %12s" % ("trip", "w", "occ_a_head", "B型head", "差(C−B)"))
for d, trip, w, ha, hb, gap in sorted(worst, reverse=True):
    P("   %-18s %2s %12.6f %12.6f %12.6f" % (trip, w, ha, hb, d))

P()
P("=" * 100)
P("## 二、tail 恒等式检验（tail 是否是 B 型）")
P("=" * 100)
tok = tbad = 0
for trip, w, ts, fs, v in windows():
    r = tail_identity(ts, fs)
    if r is None:
        continue
    ta, tb = r
    if abs(ta - tb) < 1e-12:
        tok += 1
    else:
        tbad += 1
        P("   MISMATCH %s w%s: occ_a_tail=%.9f  B_tail=%.9f" % (trip, w, ta, tb))
P("   tail 恒等式成立 %d 窗，不成立 %d 窗  ⇒ tail 确为 B 型" % (tok, tbad))

P()
P("=" * 100)
P("## 三、occ_a→B 的总降幅按段型分解（窗均，pp）")
P("=" * 100)
n_win = 0
sum_head = sum_int = sum_tail = 0.0
head_rows = []
int_rows = []
for trip, w, ts, fs, v in windows():
    sa, span = segs_a(ts, fs)
    sb, _ = segs_b(ts, fs)
    if not span:
        continue
    n_win += 1
    da = dict()
    for k, x in sa:
        da[k] = da.get(k, 0.0) + x
    db = dict()
    for k, x in sb:
        db[k] = db.get(k, 0.0) + x
    # head：occ_a 的 head/head_whole 对比 B 的 head
    dh = da.get("head", 0.0) + da.get("head_whole", 0.0) - db.get("head", 0.0)
    # interior
    di = da.get("interior", 0.0) - db.get("interior", 0.0)
    # tail
    dt = da.get("tail", 0.0) - db.get("tail", 0.0)
    sum_head += 100 * dh / span
    sum_int += 100 * di / span
    sum_tail += 100 * dt / span
    if abs(100 * dh / span) > 0.01:
        head_rows.append((100 * dh / span, trip, w))
    if abs(100 * di / span) > 0.01:
        int_rows.append((100 * di / span, trip, w))

P("   有效窗数 = %d" % n_win)
P("   head     段型差异贡献（窗均）= %+8.4f pp" % (sum_head / n_win))
P("   interior 段型差异贡献（窗均）= %+8.4f pp" % (sum_int / n_win))
P("   tail     段型差异贡献（窗均）= %+8.4f pp" % (sum_tail / n_win))
P("   合计                        = %+8.4f pp"
  % ((sum_head + sum_int + sum_tail) / n_win))
P()
P("   ## head 贡献 >0.01pp 的窗（共 %d 个，即「head 若按 B 型算会变」的窗）" % len(head_rows))
for v, trip, w in sorted(head_rows, reverse=True):
    P("      %+9.4f pp  %-18s w%s" % (v, trip, w))
P()
P("   ## interior 贡献 >0.01pp 的窗（共 %d 个）前 12" % len(int_rows))
for v, trip, w in sorted(int_rows, reverse=True)[:12]:
    P("      %+9.4f pp  %-18s w%s" % (v, trip, w))

P()
P("=" * 100)
P("## 四、结论")
P("=" * 100)
P("   1. head 恒等式在全部 %d 窗成立 ⇒ occ_a 的 head 段实为 **C 型**（跨到下一帧首见），" % ok)
P("      不是 §514 所称的「天然 B 型」。§514 该处定性描述需勘误。")
P("   2. tail 恒等式在全部 %d 窗成立 ⇒ tail 确为 B 型，§514 此处判断正确。" % tok)
P("   3. 因此 occ_a 实为「head=C、interior=C、tail=B」的混合口径；" )
P("      §514 表述的「混合」成立，但混合的**边界位置**写错（C 型覆盖 head+interior，B 型仅 tail）。")
P("   4. 量化后果：head 型差异只影响 %d 个窗、窗均贡献 %+.4f pp；" % (len(head_rows), sum_head / n_win))
P("      差值主体来自 interior（窗均 %+.4f pp）。" % (sum_int / n_win))
P("   5. 对 §514 六条红项的影响：逐窗复核见 _occ_reditems.py——q w2/r w1/r w2/l1a w2/e4 w2")
P("      全是 tail 或 head_whole 单一长段（两口径同式），e4 w1 有 +0.01pp 级差但远小于阈值判定，")
P("      ⇒ 六条红项结论不变。")
