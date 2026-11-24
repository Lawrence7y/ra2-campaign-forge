import json
from pathlib import Path

base = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r08\W98_clean\out")
rows = {}
for d in sorted([p for p in base.glob("trip_*") if p.is_dir()]):
    f = d / "run.ndjson"
    if not f.exists():
        continue
    smp = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
    smp = [x for x in smp if x.get("kind") == "sample" and isinstance(x.get("elapsed_ingame_s"), (int, float))]
    if len(smp) < 2:
        continue
    wall = (smp[-1]["t_perf_ns"] - smp[0]["t_perf_ns"]) / 1e9
    cpu = smp[-1]["win_cpu_ms"] - smp[0]["win_cpu_ms"]
    rate = cpu / (wall * 1000) * 100
    fg = [x.get("win_foreground") for x in smp if x.get("win_foreground") is not None]
    fg_true = sum(1 for v in fg if v)
    a8 = [x.get("A8ED50") or 0 for x in smp]
    first = next((i for i, v in enumerate(a8) if v), None)
    t_first = smp[first]["elapsed_ingame_s"] if first is not None else None
    rows[d.name] = dict(n=len(smp), wall=wall, cpu=cpu, rate=rate,
                        fg_n=len(fg), fg_true=fg_true,
                        fg_loss_pct=round(100.0 * (len(fg) - fg_true) / len(fg), 1) if fg else None,
                        a8_first=first, a8_t=t_first)

print("%-26s %6s %7s %9s %8s %8s" % ("trip", "n", "wall_s", "rate%", "fg_loss%", "a8_t"))
for k, v in rows.items():
    print("%-26s %6d %7.1f %8.3f %8s %8s" % (k, v["n"], v["wall"], v["rate"],
                                             v["fg_loss_pct"], ("%.2f" % v["a8_t"]) if v["a8_t"] is not None else "-"))

def group(cell):
    vals = [v["rate"] for k, v in rows.items() if k.startswith("trip_" + cell)]
    return vals

print()
res = {}
for cell in ("g_idle", "g_near", "g_far"):
    vals = group(cell)
    if vals:
        res[cell] = sum(vals) / len(vals)
        print("  %-8s n=%d  rates=%s  mean=%.4f  spread=%.4f" %
              (cell, len(vals), ["%.3f" % v for v in vals], res[cell],
               (max(vals) - min(vals)) if len(vals) > 1 else 0.0))

if len(res) == 3:
    idle, near, far = res["g_idle"], res["g_near"], res["g_far"]
    combat = near - idle
    march = far - near
    total = far - idle
    print("\n  交战 = R(near)-R(idle) = %.4f pp" % combat)
    print("  行军 = R(far)-R(near)  = %.4f pp" % march)
    print("  合计                    = %.4f pp  (R(far)-R(idle)=%.4f)" % (combat + march, total))
    print("  恒等式自洽差            = %.6f pp" % ((combat + march) - total))
    if total > 0:
        print("  构成：交战 %.1f %%   行军 %.1f %%" % (100 * combat / total, 100 * march / total))
    print("  参照带 R(far)/R(idle)   = %.4f" % (far / idle))
