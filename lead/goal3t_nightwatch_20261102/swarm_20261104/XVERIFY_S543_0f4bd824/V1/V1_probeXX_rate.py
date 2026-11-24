"""V1 probe XX: which constant tick rate can explain the on-screen clock?

Two display models (the screen only shows whole seconds):
  floor  : elapsed = f/rate  with floor(elapsed) = sec  ->  rate in ( f/(sec+1), f/sec ]
  round  : round(elapsed)  = sec                        ->  rate in [ f/(sec+0.5), f/(sec-0.5) ]
Report the feasible rate interval per row and the intersection over subsets, and test the
document's claimed constant 31.2.
"""
rows = [("archive_T33/w1", 738, 24), ("archive_T34/w1", 302, 10), ("archive_T36/w1", 310, 10),
        ("archive_T39/w2", 945, 31), ("archive_T40/w1", 908, 30), ("archive_T41/w1", 860, 28),
        ("archive_T43/w1", 314, 10), ("archive_T44/w1", 883, 29), ("archive_T45/w1", 845, 28),
        ("archive_T49_u0800/w1", 448, 15), ("archive_T38/w2", 940, 32),
        ("root T55h/w1", 373, 13), ("l3_20261023r/w2", 4367, 176)]

for model in ("floor", "round"):
    print("=" * 76)
    print("display model =", model)
    ints = {}
    for n, f, s in rows:
        lo, hi = (f / (s + 1), f / s) if model == "floor" else (f / (s + 0.5), f / max(s - 0.5, 0.01))
        ints[n] = (lo, hi)
        print("  %-22s f=%-5d sec=%-4d rate in (%.3f, %.3f]   31.2 feasible=%s  30.0 feasible=%s" % (
            n, f, s, lo, hi, lo <= 31.2 <= hi, lo <= 30.0 <= hi))
    for subset_name, keys in [
            ("all 13", [n for n, _, _ in rows]),
            ("12 excl l3", [n for n, _, _ in rows if n != "l3_20261023r/w2"]),
            ("11 excl l3,T38w2", [n for n, _, _ in rows if n not in ("l3_20261023r/w2", "archive_T38/w2")]),
            ("10 excl l3,T38w2,root", [n for n, _, _ in rows if n not in ("l3_20261023r/w2", "archive_T38/w2", "root T55h/w1")]),
            ("9 = 10 minus T49", [n for n, _, _ in rows if n not in ("l3_20261023r/w2", "archive_T38/w2", "root T55h/w1", "archive_T49_u0800/w1")])]:
        lo = max(ints[k][0] for k in keys)
        hi = min(ints[k][1] for k in keys)
        print("  intersection %-20s (%.3f, %.3f] %s  | 31.2 in? %-5s | 30.0 in? %-5s | 29.7 in? %s" % (
            subset_name, lo, hi, "EMPTY" if lo >= hi else "non-empty",
            lo <= 31.2 <= hi, lo <= 30.0 <= hi, lo <= 29.7 <= hi))
    n_ok = sum(1 for n, f, s in rows if ints[n][0] <= 31.2 <= ints[n][1])
    print("  rows where 31.2 is feasible: %d/%d" % (n_ok, len(rows)))
    n_ok30 = sum(1 for n, f, s in rows if ints[n][0] <= 30.0 <= ints[n][1])
    print("  rows where 30.0 is feasible: %d/%d" % (n_ok30, len(rows)))
