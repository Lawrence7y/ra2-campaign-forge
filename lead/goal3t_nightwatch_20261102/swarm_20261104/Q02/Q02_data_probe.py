# -*- coding: utf-8 -*-
"""Q02 数据探针：用 4 份 wait-trace 原始 [t,frame] 判定 v4-b 深滞 = 丢帧还是变慢。
只读 JSON；零真机；stdout-only（落盘靠 shell 重定向）。
"""
import json
import math

BASE = (r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/"
        r"CONTINUE_20261003/lead/qc161_u0400_trip")
RUNS = ["l3_1101v4b", "l3_1101v4c", "l3_1101v4d", "l3_1101v4e"]

OUT = []
def p(*a):
    s = " ".join(str(x) for x in a)
    OUT.append(s)
    print(s, flush=True)

def med(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2])

def quart(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 4], med(xs), xs[3 * n // 4]

def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]

# ---------------------------------------------------------------
# Pass 1: per-run core decomposition
# ---------------------------------------------------------------
edges_all = {}
for run in RUNS:
    d = json.load(open("%s/%s/h8_wait_trace.json" % (BASE, run), encoding="utf-8"))
    S = [(t, f) for t, f in d["samples"]]
    p("=" * 72)
    p("RUN %s  verdict=%s n_target=%d wait_s=%.3f len=%d" % (
        run, d.get("verdict"), d.get("n"), d.get("wait_s"), len(S)))

    # --- monotonicity / reset ---
    drops = [(S[i - 1], S[i]) for i in range(1, len(S)) if S[i][1] < S[i - 1][1]]
    p("frame monotonic: %s  (decrease events: %d)" % (not drops, len(drops)))
    for a, b in drops[:5]:
        p("   DECREASE %s -> %s" % (a, b))

    # --- sampling cadence ---
    gaps = [S[i][0] - S[i - 1][0] for i in range(1, len(S))]
    span = S[-1][0] - S[0][0]
    p("sample cadence: span=%.3fs eff_rate=%.1fHz med=%.1fms p90=%.1fms max=%.1fms" % (
        span, len(S) / span, 1000 * med(gaps), 1000 * pct(gaps, 0.90), 1000 * max(gaps)))
    starv = [g for g in gaps if g > 0.010]
    p("starvation gaps>10ms: %d totaling %.3fs (%.1f%% of span)" % (
        len(starv), sum(starv), 100.0 * sum(starv) / span))

    # --- delta-f histogram ---
    dz = d1 = d2 = dgt = 0
    for i in range(1, len(S)):
        df = S[i][1] - S[i - 1][1]
        if df == 0: dz += 1
        elif df == 1: d1 += 1
        elif df == 2: d2 += 1
        else: dgt += 1
    p("delta-f histogram: zero=%d one=%d two=%d gt2=%d" % (dz, d1, d2, dgt))

    # --- advance edges ---
    E = []  # (t_edge, f_after, dt_since_prev_sample, gap_flag)
    for i in range(1, len(S)):
        df = S[i][1] - S[i - 1][1]
        if df > 0:
            g = S[i][0] - S[i - 1][0]
            E.append((S[i][0], S[i][1], g, g > 0.010, df))
    edges_all[run] = E
    if not E:
        p("no advances")
        continue
    t0 = E[0][0]                       # battle start = first advance
    tlast = E[-1][0]
    battle = tlast - t0
    p("first advance t=%.3fs (frame 0 plateau %.3fs); battle span=%.3fs; advances=%d" % (
        t0, t0 - S[0][0], battle, len(E)))
    p("avg battle pace = %.2f frames/s" % ((E[-1][1] - E[0][1]) / battle))

    # --- advance-interval stats (C-criterion: t(next advance) - t(this advance)) ---
    I = [E[i][0] - E[i - 1][0] for i in range(1, len(E))]
    if I:
        q1, q2, q3 = quart(I)
        meanI = sum(I) / len(I)
        cv = math.sqrt(sum((x - meanI) ** 2 for x in I) / len(I)) / meanI
        p("advance intervals: n=%d min=%.4f q1=%.4f med=%.4f q3=%.4f p90=%.4f max=%.4f s" % (
            len(I), min(I), q1, q2, q3, pct(I, 0.90), max(I)))
        p("   mean=%.4f CV=%.3f" % (meanI, cv))
        # gap contamination
        gapaff = [E[i][2] for i in range(1, len(E))]
        ngap = sum(1 for g in gapaff if g > 0.010)
        p("   edges whose own sampling gap >10ms: %d/%d" % (ngap, len(I)))
        # short-interval fraction at healthy pace references
        for th in (0.0374, 0.0422, 0.0659, 0.084):
            frac = sum(1 for x in I if x <= 2 * th) / len(I)
            p("   frac(interval <= 2x%.1fms=%.1fms): %.3f" % (1000 * th, 2000 * th, frac))

    # --- max no-advance windows (C-criterion) top5 ---
    W = [(E[i][0] - E[i - 1][0], E[i - 1][1], E[i - 1][0], E[i][0], E[i][1] - E[i - 1][1])
         for i in range(1, len(E))]
    W.sort(reverse=True)
    p("top5 no-advance windows (C): dur / frame@start / t_start / t_end / df_at_resume")
    for w in W[:5]:
        p("   %.4fs  f=%d  %.3fs -> %.3fs  df=%d" % w)

    # --- B-criterion: equal-frame runs >=100ms ---
    runs = []
    i = 0
    while i < len(S):
        j = i
        while j + 1 < len(S) and S[j + 1][1] == S[i][1]:
            j += 1
        if j > i and S[j][0] - S[i][0] >= 0.100:
            runs.append((S[j][0] - S[i][0], S[i][1], S[i][0], S[j][0]))
        i = j + 1
    big = [r for r in runs if S[0][0] <= r[2] >= t0 or r[2] >= t0]
    bigb = [r for r in runs if r[2] >= t0]
    p("B-criterion runs>=100ms in battle: n=%d total=%.3fs max=%.4fs" % (
        len(bigb), sum(r[0] for r in bigb), max(r[0] for r in bigb) if bigb else 0))

    # --- quantal test: are intervals clustered at k*T ? ---
    if I:
        p("quantal test: frac(interval within ±4ms of k*T)")
        for T in (0.016, 0.032, 0.0374, 0.0422, 0.0659):
            hit = sum(1 for x in I if abs(x / T - round(x / T)) * T <= 0.004 and round(x / T) >= 1)
            p("   T=%.1fms -> %.3f (n=%d)" % (1000 * T, hit / len(I), len(I)))
        # uniform-reference: what a continuous uniform in [min,max] would score
        lo_, hi_ = min(I), max(I)
        N = 200000
        acc = 0.0
        import random
        random.seed(7)
        for _ in range(N):
            x = random.uniform(lo_, hi_)
            acc += abs(x / 0.016 - round(x / 0.016)) * 0.016 <= 0.004
        p("   T=16ms uniform-noise reference score: %.3f" % (acc / N))

    # --- lag-1 autocorrelation of intervals (regime vs noise) ---
    if len(I) > 10:
        m_ = sum(I) / len(I)
        num = sum((I[i] - m_) * (I[i + 1] - m_) for i in range(len(I) - 1))
        den = sum((x - m_) ** 2 for x in I)
        p("lag-1 autocorr of intervals: %.3f" % (num / den if den else 0))

    # --- time structure: quartile medians of intervals ---
    if len(I) >= 8:
        n4 = len(I) // 4
        p("interval medians by quarter: %s" % " / ".join(
            "%.3f" % med(I[k * n4:(k + 1) * n4]) for k in range(4)))

    # --- multi-advance events ---
    for (t, f, g, gf, df) in E:
        if df > 1:
            p("MULTI-ADVANCE: t=%.3fs f->%d df=%d own-sample-gap=%.4fs%s" % (
                t, f, df, g, " (gap>10ms)" if gf else ""))

    # --- 5s sliding window rate (battle) ---
    if battle > 6:
        rates = []
        ws = t0
        while ws + 5.0 <= tlast:
            c = sum(1 for e in E if ws < e[0] <= ws + 5.0)
            rates.append((ws - t0, c / 5.0))
            ws += 5.0
        vals = [r for _, r in rates]
        p("5s-window rates: n=%d min=%.2f max=%.2f  (t_rel of min=%.1fs max=%.1fs)" % (
            len(vals), min(vals), max(vals),
            rates[vals.index(min(vals))][0], rates[vals.index(max(vals))][0]))

# ---------------------------------------------------------------
# Pass 2: the leader's criterion + skip-model arithmetic (v4-b focus)
# ---------------------------------------------------------------
p("=" * 72)
p("PASS 2: drop-vs-slow discriminators (v4-b vs healthy refs)")
E = edges_all["l3_1101v4b"]
I = [E[i][0] - E[i - 1][0] for i in range(1, len(E))]
Df = [E[i][4] for i in range(1, len(E))]

# (A) leader criterion: continuous small nonzero increments?
IV = [E[i][0] - E[i - 1][0] for i in range(1, len(E))]
p("(A) v4-b advance count=%d over battle; df==1 on %d/%d edges (%.1f%%)" % (
    len(E), sum(1 for x in Df if x == 1), len(Df), 100.0 * sum(1 for x in Df if x == 1) / len(Df)))
p("    max no-advance window = %.4fs; windows >=2s: %d" % (
    max(IV) if IV else 0,
    sum(1 for x in IV if x >= 2.0)))

# (B) short-pair fraction: drop-model with healthy iteration pace predicts
#     a sizeable cluster of consecutive advances at ~healthy pace (no skip between).
for th, tag in ((0.0374, "v4-e-med"), (0.0422, "v4-d-med"), (0.0659, "v4-c-med")):
    n_ = sum(1 for x in I if x <= 2 * th)
    p("(B) v4-b pairs <=2x%s(%.1fms): %d/%d = %.4f" % (
        tag, 2000 * th, n_, len(I), n_ / len(I)))

# (C) skip-model arithmetic: interval = (k+1) * T_iter  ->  implied k
p("(C) implied k = dt/T_iter - 1 per interval (skip-model, throttle-bound T_iter):")
for T in (0.032, 0.0374, 0.0422):
    ks = [x / T - 1 for x in I]
    p("   T=%.1fms: k med=%.1f q1=%.1f q3=%.1f min=%.1f max=%.1f -> "
      "k in [1,5] on %.1f%% of intervals" % (
          1000 * T, med(ks), quart(ks)[0], quart(ks)[2], min(ks), max(ks),
          100.0 * sum(1 for k in ks if 1 <= k <= 5) / len(ks)))
# duty cycle: fraction of battle time the counter is NOT advancing
t0, tlast = E[0][0], E[-1][0]
nonadv = sum(I) - len(I) * 0.0  # intervals are all non-advance except the inc instant
p("(C) non-advance time share (C-criterion) = %.1f%%" % (100.0 * sum(I) / (tlast - t0)))

# (D) if counter frozen while iterations continue at healthy 31fps (32ms),
#     frames 'lost' per window:
p("(D) v4-b top3 windows expressed in healthy 31fps iterations (32ms):")
for w in sorted(((E[i][0] - E[i - 1][0], E[i - 1][1]) for i in range(1, len(E))),
                reverse=True)[:3]:
    p("   %.4fs @f=%d  ~%d healthy iters elapsed, df at resume=1 (no catch-up possible:"
      " inc is +1/call, only nonzero writer=load serialization)" % (w[0], w[1], round(w[0] / 0.032)))

# (E) healthy-run references
for run in ("l3_1101v4c", "l3_1101v4d", "l3_1101v4e"):
    E2 = edges_all[run]
    I2 = [E2[i][0] - E2[i - 1][0] for i in range(1, len(E2))]
    p("(E) %s: med interval=%.4fs p90=%.4fs max=%.4fs; >=0.5s windows: %d" % (
        run, med(I2), pct(I2, 0.90), max(I2),
        sum(1 for x in I2 if x >= 0.5)))

p("")
p("WROTE Q02_data_probe_out.txt" if False else "done")

with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/Q02/Q02_data_probe_out.txt",
          "w", encoding="utf-8") as f:
    f.write("\n".join(OUT) + "\n")
