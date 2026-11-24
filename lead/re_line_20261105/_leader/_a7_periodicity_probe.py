# -*- coding: utf-8 -*-
"""A7 结案探针：帧时「8 帧一轮」周期性 —— 用 500 Hz 真实语料做置换检验。

零真机、零注入；只读 lead/ 下既有 measure_w*.json。
判定口径（先写死，避免事后挑）：
  H0：窗口内每帧时长与 frame % 8 无关（即不存在 8 帧周期）
  统计量：spread(k) = (max_k median - min_k median) / min_k median
  检验：把帧号序列随机重排 2000 次，看观测 spread 在零分布里的分位
  ⇒ p < 0.05 才能说「存在 k 帧周期」
"""
import collections
import io
import json
import os
import random
import statistics

random.seed(20261106)
ROOT = r"D:\Project\ra2-campaign-forge"
OUT = []


def P(*a):
    s = " ".join(str(x) for x in a)
    OUT.append(s)
    print(s)


def load(rel):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    return json.load(io.open(p, encoding="utf-8"))


def frame_durs(d):
    fe = d["frame_edges"]
    durs = [(fe[i][1] - fe[i - 1][1]) * 1000.0 for i in range(1, len(fe))]
    fr = [fe[i][0] for i in range(1, len(fe))]
    return fr, durs


def spread_for(frames, durs, k):
    g = collections.defaultdict(list)
    for f, dt in zip(frames, durs):
        g[f % k].append(dt)
    if len(g) < k:
        return None
    meds = [statistics.median(v) for v in g.values()]
    lo, hi = min(meds), max(meds)
    return (hi - lo) / lo if lo > 0 else None


def perm_p(frames, durs, k, n=2000):
    obs = spread_for(frames, durs, k)
    null = []
    work = frames[:]
    for _ in range(n):
        random.shuffle(work)
        s = spread_for(work, durs, k)
        if s is not None:
            null.append(s)
    null.sort()
    if not null:
        return obs, None, None, None
    p = sum(1 for v in null if v >= obs) / len(null)
    return obs, p, null[len(null) // 2], null[int(len(null) * 0.95)]


P("=" * 78)
P("A7 结案：帧时 8 帧周期性 —— 500 Hz 真实语料的置换检验")
P("=" * 78)

# 先自证语料：只有 hz_effective >= 100 的窗才有「每帧一个读数」的分辨率
CAND = []
for dp, dns, fns in os.walk(os.path.join(ROOT, "lead")):
    dns[:] = [x for x in dns if x not in ("__pycache__", ".git")]
    for fn in fns:
        if fn.startswith("measure_w") and fn.endswith(".json"):
            CAND.append(os.path.join(dp, fn).replace(ROOT + os.sep, "").replace(os.sep, "/"))

P("\n[0] 语料筛选")
rows = []
for rel in sorted(CAND):
    try:
        d = load(rel)
    except Exception:
        continue
    if d.get("verdict") != "ok":
        continue
    st = d.get("stats") or {}
    hz = st.get("hz_effective")
    if hz is None or hz < 100:
        continue
    rows.append((rel, hz, st.get("frame_ms_p50"), st.get("fps_avg"), len(d.get("frame_edges") or [])))
P("  lead/ 下 measure_w*.json 总数 = %d" % len(CAND))
P("  其中 verdict=ok 且 hz_effective>=100 的窗 = %d（只有这些有每帧分辨率）" % len(rows))
for r in rows:
    P("    hz=%-7s p50=%-8s fps=%-7s edges=%-4s  %s" % (
        r[1], round(r[2], 1) if r[2] else None, round(r[3], 2) if r[3] else None, r[4], r[0]))

# 分组：慢窗 vs 快窗
slow = [r for r in rows if r[2] and r[2] > 60]
fast = [r for r in rows if r[2] and r[2] <= 60]
P("\n  慢窗（frame_ms_p50 > 60ms）= %d；快窗（<=60ms）= %d" % (len(slow), len(fast)))

P("\n[1] 组间中位数极差（k = 8），慢窗 vs 快窗")
P("  %-46s %8s %8s %8s %8s" % ("window", "k=8", "k=4", "k=16", "k=3"))
for r in rows:
    d = load(r[0])
    fr, durs = frame_durs(d)
    vals = []
    for k in (8, 4, 16, 3):
        s = spread_for(fr, durs, k)
        vals.append(s)
    P("  %-46s %8.3f %8.3f %8.3f %8.3f" % (
        r[0][-46:], *[v if v is not None else float("nan") for v in vals]))

P("\n[2] 置换检验（k=8, n=2000 次随机重排）")
P("  %-46s %9s %9s %9s %9s" % ("window", "observed", "p-value", "null_p50", "null_p95"))
verdicts = []
for r in rows:
    d = load(r[0])
    fr, durs = frame_durs(d)
    obs, p, n50, n95 = perm_p(fr, durs, 8, 2000)
    if p is None:
        continue
    sig = p < 0.05
    verdicts.append((r[0], obs, p, sig))
    P("  %-46s %9.4f %9.4f %9.4f %9.4f  %s" % (
        r[0][-46:], obs, p, n50, n95, "★周期显著" if sig else "不显著"))

P("\n[3] 关键附加检：mod-8 图样在同进程连续窗之间是否复现")
P("  若「8 帧一轮」是引擎机制，图样应绑在帧号上 ⇒ 同进程连续三窗的 argmin/argmax 应一致")
group = collections.defaultdict(list)
for rel, *_ in rows:
    key = os.path.dirname(rel)
    group[key].append(rel)
for key, files in sorted(group.items()):
    if len(files) < 3:
        continue
    P("\n  --- %s ---" % key.replace("/", "\\")[-56:])
    for rel in sorted(files):
        d = load(rel)
        fr, durs = frame_durs(d)
        g = collections.defaultdict(list)
        for f, dt in zip(fr, durs):
            g[f % 8].append(dt)
        meds = {j: statistics.median(v) for j, v in g.items()}
        P("    %-12s frames %d..%d  argmin=%d argmax=%d  meds=%s" % (
            os.path.basename(rel)[:-5], fr[0], fr[-1],
            min(meds, key=meds.get), max(meds, key=meds.get),
            {k: round(v, 1) for k, v in sorted(meds.items())}))

P("\n" + "=" * 78)
P("判定")
P("=" * 78)
n_sig = sum(1 for _, _, _, s in verdicts if s)
P("  显著窗数 / 总窗数 = %d / %d" % (n_sig, len(verdicts)))
if n_sig == 0:
    P("  ⇒ **8 帧周期性 H0 未被拒绝**：所有窗的 p 都 > 0.05")
    P("  ⇒ 结论：**在现有 500 Hz 语料上，「帧时随 frame%8 周期变化」不成立**")
    P("    （注意：这是「未证伪 H0」，不等同于「证明绝对不存在」，但足以把 A7 从")
    P("     「探针失败、未查」升级为「已用合格探针查过、无信号」）")
else:
    P("  ⇒ 有 %d 个窗显著，需逐个复核是否同一 k" % n_sig)
P("\n  ★ 方法学要点：此前两次 ACF 探针失败的原因是「慢窗里 50 ms 固定分箱每箱不足 2 帧」")
P("    与「邻域样本极少时除以总体方差」。本探针**不用分箱、不用 ACF**，")
P("    直接按 frame % k 分组取中位数 + 随机重排零分布，在慢窗上同样有效。")

io.open(os.path.join(ROOT, r"lead\re_line_20261105\_leader\_a7_periodicity_probe_out.txt"),
        "w", encoding="utf-8").write("\n".join(OUT) + "\n")
P("\nDONE")
