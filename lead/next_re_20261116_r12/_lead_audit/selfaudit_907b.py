"""§907 更强的检验：**不按窗口切**，直接按 moving 取值分桶统计 CPU/帧。

为什么要这么做：窗口划分是任意的（ws=5/10/15/20/30 结果差异不小）。
按 moving 取值直接分桶，避免了窗口长度这个自由参数。

口径：把相邻两个样本的 (Δframe, Δcpu) 当作一次瞬时估计 cpu/帧 = Δcpu/Δframe，
然后按"该样本处的 moving 读数"分桶。要求 Δframe>0。
"""
import json
import statistics as st

PATH = r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W165_live\EVIDENCE\ingame_cpu_120s.ndjson"

rows = [json.loads(l) for l in open(PATH, encoding="utf-8")]
rows = [r for r in rows if r.get("cpu_ms") is not None and r.get("frame") is not None]

samples = []
for p, q in zip(rows, rows[1:]):
    df = q["frame"] - p["frame"]
    dcpu = q["cpu_ms"] - p["cpu_ms"]
    dt = (q["t"] - p["t"]) * 1000.0
    if df <= 0 or dt <= 0:
        continue
    samples.append(dict(cpu=dcpu / df, ms=dt / df, moving=p["moving"],
                        objects=p["objects"], tgt=p["has_target"]))

print("相邻样本对 = %d" % len(samples))


def bucket_by(key, label):
    groups = {}
    for s in samples:
        groups.setdefault(s[key], []).append(s)
    print()
    print("=" * 88)
    print("按 %s 分桶（%s）" % (key, label))
    print("=" * 88)
    print("%-8s %7s %12s %12s %12s %12s" % (key, "n", "cpu中位", "cpu均值", "cpu/该值", "ms中位"))
    keys = sorted(groups)
    prev = None
    mono = True
    for k in keys:
        g = groups[k]
        if len(g) < 20:
            continue
        cpu = [x["cpu"] for x in g]
        med = st.median(cpu)
        ratio = st.median(cpu) / k if k else float("nan")
        print("%-8s %7d %12.4f %12.4f %12.5f %12.4f"
              % (k, len(g), med, st.mean(cpu), ratio, st.median(x["ms"] for x in g)))
        if prev is not None and med < prev:
            mono = False
        prev = med
    print("  ⇒ 中位 CPU 随 %s 单调不降: %s" % (key, mono))


bucket_by("moving", "移动中对象数")
bucket_by("objects", "总对象数")
bucket_by("tgt", "有目标的对象数")

# 控制 objects 看 moving 的偏效应：在 objects 相同的子集里比较 moving
print()
print("=" * 88)
print("控制总对象数：在 objects 取值固定的子集内，看 moving 是否仍与 cpu 同向")
print("=" * 88)
by_ob = {}
for s in samples:
    by_ob.setdefault(s["objects"], []).append(s)
for ob in sorted(by_ob):
    g = by_ob[ob]
    if len(g) < 200:
        continue
    sub = {}
    for s in g:
        sub.setdefault(s["moving"], []).append(s["cpu"])
    row = []
    for mv in sorted(sub):
        if len(sub[mv]) >= 30:
            row.append("mv=%d:%.3f(n=%d)" % (mv, st.median(sub[mv]), len(sub[mv])))
    if len(row) >= 2:
        print("  objects=%-4d  %s" % (ob, "  ".join(row)))
