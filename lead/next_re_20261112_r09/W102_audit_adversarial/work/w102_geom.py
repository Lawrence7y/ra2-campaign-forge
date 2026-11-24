#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
W102 §A-7 · 用三份 design json 量化 g_near vs g_far 的几何差（§634 攻击点 2 要用）

只做几何，不碰游戏。坐标取自 .MAP 构建前的 design json（installed_inputs 里的原件，
与 .MAP 同批 sha256 归档，见 TRIP_RESULT.inputs_archive）。
"""
import json, os, hashlib

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r08\W98_clean\out"
DES = {
    "g_idle": ("trip_g_idle_r1", "trip_g_idle_r2", "w94_design_g_idle.json"),
    "g_near": ("trip_g_near_r1", "trip_g_near_r2", "w94_design_g_near.json"),
    "g_far":  ("trip_g_far_r1",  "trip_g_far_r2",  "w94_design_g_far.json"),
}


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def main():
    print("=" * 104)
    print("W102 §A-7-0 · design json 的 sha 与 r1/r2 一致性（证明同 cell 两趟输入同一）")
    print("=" * 104)
    D = {}
    for cell, (r1, r2, fn) in DES.items():
        p1, p2 = os.path.join(OUT, r1, "installed_inputs", fn), os.path.join(OUT, r2, "installed_inputs", fn)
        h1 = hashlib.sha256(open(p1, "rb").read()).hexdigest()
        h2 = hashlib.sha256(open(p2, "rb").read()).hexdigest()
        print("  {:<8} r1={} r2={}  identical={}".format(cell, h1[:16], h2[:16], h1 == h2))
        D[cell] = json.load(open(p1, encoding="utf-8"))

    print()
    print("=" * 104)
    print("W102 §A-7-1 · 每格构型（units by owner/type/mission）")
    print("=" * 104)
    summ = {}
    for cell, d in D.items():
        m = d["missions"][0]
        print("  [{}] map size={}  player={}  structures={}  units={}  infantry={}".format(
            cell, m["size"], m["player"], len(m["structures"]), len(m["units"]), len(m["infantry"])))
        agg = {}
        for u in m["units"]:
            k = (u["owner"], u["type"], u.get("mission"))
            agg[k] = agg.get(k, 0) + 1
        for k in sorted(agg):
            print("      {:<16} {:<8} {:<8} x{}".format(k[0], k[1], str(k[2]), agg[k]))
        sagg = {}
        for s in m["structures"]:
            k = (s["owner"], s["type"])
            sagg[k] = sagg.get(k, 0) + 1
        for k in sorted(sagg):
            print("      [STRUCT] {:<12} {:<10} x{}".format(k[0], k[1], sagg[k]))

    print()
    print("=" * 104)
    print("W102 §A-7-2 · 敌方 MTNK → 最近玩家对象 的 Chebyshev 距离分布")
    print("=" * 104)
    for cell, d in D.items():
        m = d["missions"][0]
        owners = sorted({u["owner"] for u in m["units"]})
        # 玩家侧 = player 键里的 house（Americans），敌方 = 其余（Hunt）
        pl = m["player"]
        powner = pl.get("house") or pl.get("side") or "Americans"
        player = [u for u in m["units"] if u["owner"] == powner]
        enemy = [u for u in m["units"] if u["owner"] != powner]
        pcell = [(u["row"], u["col"]) for u in player]
        pcell += [(s["row"], s["col"]) for s in m["structures"] if s["owner"] == powner]
        dst = sorted(min(cheb((e["row"], e["col"]), c) for c in pcell) for e in enemy)
        n = len(dst)
        q = lambda p: dst[min(n - 1, int(p * n))]
        s = dict(n=n, n_player=len(pcell), dmin=dst[0], dmax=dst[-1],
                 dmean=sum(dst) / n, med=q(0.5), p10=q(0.10), p25=q(0.25),
                 p75=q(0.75), p90=q(0.90),
                 n_le3=sum(1 for x in dst if x <= 3),
                 n_le13=sum(1 for x in dst if x <= 13),
                 n_gt50=sum(1 for x in dst if x > 50),
                 sumd=int(sum(dst)))
        summ[cell] = s
        print("  [{}] 敌 {} 辆  玩家格 {} 个".format(cell, s["n"], s["n_player"]))
        print("       min={} max={} mean={:.4f} median={} p10={} p25={} p75={} p90={}".format(
            s["dmin"], s["dmax"], s["dmean"], s["med"], s["p10"], s["p25"], s["p75"], s["p90"]))
        print("       <=3格 {} 辆 | <=13格 {} 辆 | >50格 {} 辆 | Σd={}".format(
            s["n_le3"], s["n_le13"], s["n_gt50"], s["sumd"]))

    print()
    print("=" * 104)
    print("W102 §A-7-3 · g_near vs g_far：几何差即唯一因果旋钮")
    print("=" * 104)
    rn, rf = summ["g_near"], summ["g_far"]
    print("  Σd  g_near = {} 格·辆    g_far = {} 格·辆    比值 = {:.3f}".format(
        rn["sumd"], rf["sumd"], rf["sumd"] / rn["sumd"]))
    print("  mean g_near = {:.3f} 格   g_far = {:.3f} 格   差 = {:.3f} 格/辆".format(
        rn["dmean"], rf["dmean"], rf["dmean"] - rn["dmean"]))
    print()
    print("  ⇒ g_near 的\"行军\"不是 0，是 Σd={} 格·辆 ⇒ 若 g_far 的 Σd 全部计入\"行军\"，".format(rn["sumd"]))
    print("    则 g_near 里被归到\"交战\"的那部分实际含有 Σd_near/Σd_far = {:.1%} 的行军量。".format(
        rn["sumd"] / rf["sumd"]))
    print("    **这是该混杂的\"几何占比\"一阶界**（假设 CPU 与 Σd 线性）；下界估算见 ATTACK_634 §2。")

    print()
    print("=" * 104)
    print("W102 §A-7-4 · A8ED50 首非零时刻（接触时刻的可观察代理）")
    print("=" * 104)
    for cell, (r1, r2, _fn) in DES.items():
        for trip in (r1, r2):
            rows = []
            with open(os.path.join(OUT, trip, "run.ndjson"), encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
            s = [r for r in rows if r.get("kind") == "sample" and r.get("elapsed_ingame_s") is not None]
            first = None
            for i, r in enumerate(s):
                if (r.get("A8ED50") or 0) != 0:
                    first = (i, r["elapsed_ingame_s"])
                    break
            nz = sum(1 for r in s if (r.get("A8ED50") or 0) != 0)
            # 最后一次非零
            last = None
            for r in reversed(s):
                if (r.get("A8ED50") or 0) != 0:
                    last = r["elapsed_ingame_s"]
                    break
            print("  {:<18} 首非零 {}  末非零 {}  非零比 {:.4f}".format(
                trip,
                ("idx {} / {:.4f} s".format(first[0], first[1]) if first else "从未"),
                ("{:.3f} s".format(last) if last is not None else "-"),
                nz / max(1, len(s))))

    json.dump(summ, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "w102_geom.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
