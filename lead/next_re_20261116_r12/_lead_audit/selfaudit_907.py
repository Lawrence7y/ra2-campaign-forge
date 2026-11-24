"""§907 自审：把"cpu ∝ moving"这条结论往死里压。

检查项：
 A. `objects` 与 `moving` 在本数据里是否共线？若不共线（甚至反号），则
    r(cpu,moving)=+0.76 与 r(cpu,objects)=-0.55 的"分离"才有意义。
 B. 窗口长度敏感性：5 / 10 / 15 / 20 / 30 秒。
 C. 去掉开头 N 个窗（开局瞬态）后是否仍成立。
 D. 秩相关（Spearman 风格，只报系数不报 p 值）。
 E. 每移动对象成本的 CV 在不同口径下是否仍显著小于"每对象成本"的 CV。
 F. 最小样本阈值敏感性。
"""
import json
import statistics as st

PATH = r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W165_live\EVIDENCE\ingame_cpu_120s.ndjson"

rows = [json.loads(l) for l in open(PATH, encoding="utf-8")]
rows = [r for r in rows if r.get("cpu_ms") is not None and r.get("frame") is not None]


def corr(a, b):
    n = len(a)
    if n < 3:
        return float("nan")
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else float("nan")


def rank(v):
    idx = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and v[idx[j + 1]] == v[idx[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            r[idx[k]] = avg
        i = j + 1
    return r


def spearman(a, b):
    return corr(rank(a), rank(b))


def windows(ws, minn=10, skip_first=0):
    t0 = rows[0]["t"]
    out = []
    i, n = 0, len(rows)
    while i < n:
        j = i
        base = rows[i]["t"]
        while j < n and rows[j]["t"] - base < ws:
            j += 1
        c = rows[i:j]
        i = j if j > i else i + 1
        if len(c) < minn:
            continue
        df = c[-1]["frame"] - c[0]["frame"]
        dt = (c[-1]["t"] - c[0]["t"]) * 1000.0
        dcpu = c[-1]["cpu_ms"] - c[0]["cpu_ms"]
        if df <= 0 or dt <= 0:
            continue
        out.append(dict(
            ms=dt / df, cpu=dcpu / df, duty=dcpu / dt,
            objects=st.median(x["objects"] for x in c),
            lc=st.median(x["lc_count"] for x in c),
            loco=st.median(x["with_loco"] for x in c),
            tgt=st.median(x["has_target"] for x in c),
            moving=st.median(x["moving"] for x in c)))
    return out[skip_first:]


def report(w, label):
    if len(w) < 3:
        print("  %-28s n=%d 样本不足" % (label, len(w)))
        return
    cpu = [x["cpu"] for x in w]
    mv = [x["moving"] for x in w]
    ob = [x["objects"] for x in w]
    tg = [x["tgt"] for x in w]
    pm = [x["cpu"] / x["moving"] for x in w if x["moving"]]
    po = [x["cpu"] / x["objects"] for x in w if x["objects"]]
    cv_m = st.pstdev(pm) / st.mean(pm)
    cv_o = st.pstdev(po) / st.mean(po)
    print("  %-28s n=%-3d r(cpu,mv)=%+.3f r_s(cpu,mv)=%+.3f | r(cpu,ob)=%+.3f r_s(cpu,ob)=%+.3f"
          " | r(mv,ob)=%+.3f | CV(mv)=%.3f CV(ob)=%.3f | %s"
          % (label, len(w), corr(cpu, mv), spearman(cpu, mv), corr(cpu, ob), spearman(cpu, ob),
             corr(mv, ob), cv_m, cv_o, "mv 更优" if cv_m < cv_o else "**ob 更优**"))


def main():
    print("samples = %d" % len(rows))
    print()
    print("=" * 130)
    print("A · objects 与 moving 是否共线（若共线，则 r 的分离无意义）")
    print("=" * 130)
    for ws in (10.0,):
        w = windows(ws)
        mv = [x["moving"] for x in w]
        ob = [x["objects"] for x in w]
        print("  ws=10s n=%d" % len(w))
        print("    moving 序列 : %s" % [int(v) for v in mv])
        print("    objects 序列: %s" % [int(v) for v in ob])
        print("    r(moving, objects) = %+.4f   秩相关 = %+.4f" % (corr(mv, ob), spearman(mv, ob)))
        print("    ⇒ %s" % ("**反相关/不共线，分离有效**" if corr(mv, ob) < 0.3
                            else "**共线，分离无效**"))

    print()
    print("=" * 130)
    print("B/C/F · 口径敏感性")
    print("=" * 130)
    for ws in (5.0, 10.0, 15.0, 20.0, 30.0):
        report(windows(ws), "ws=%.0fs minn=10" % ws)
    print()
    for mn in (5, 20, 40, 80):
        report(windows(10.0, minn=mn), "ws=10s minn=%d" % mn)
    print()
    for sk in (1, 2, 3):
        report(windows(10.0, skip_first=sk), "ws=10s skip_first=%d" % sk)


if __name__ == "__main__":
    main()
