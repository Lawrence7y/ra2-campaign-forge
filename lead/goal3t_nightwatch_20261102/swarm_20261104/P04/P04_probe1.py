# -*- coding: utf-8 -*-
"""P04 probe1 —— 既有真机数据 c2ab_x/*/timeline.json（23 份）：tick(=[0xA8ED80] 采样) × Δf==0 相邻行对
对 A02 焦点旗标假说的可判定性检验。纯离线数据分析，零真机、零启动。

口径：
- tick/frame 仅取 int；{"state": ...}（进程死后 tri_read_u32 读失败件）计为 unreadable，不进分布。
- 相邻行对在「按 t 排序后的全行合并序列」上取（任务口径），同时按段（battle/hold/pre5/close）
  分解；跨段边界对单独标 X(a>b)。
- singleton 值变化处切分运行段：跨 singleton 的对一律剔除（不同实例/全局清零，frame 不可比）。
- hwnd==0 或 singleton==0 的行记 zeroed（游戏已清全局，frame/tick 为残值），对单独归类。
- menu-idle 混杂：mode=menu 或 frame==0 的 battle/hold/pre5 段停帧是 MainLogicFrame 头部
  [0xA8E9A0]==0 早退（0x55D360: a0a0e9a800 / 0x55D371 je 0x55DECF）的设计行为，
  与焦点无关，Δf==0 对归类 menu_idle，不算 A02 证据。
"""
import sys, os, json, glob, statistics
from collections import Counter

BASE = r"D:/Project/ra2-campaign-forge/lead/qc161_u0400_trip/c2ab_x"

def iv(x):
    """int/float 且非 bool 才算有效读数（t 本就是 float；读失败件是 dict 被拒）"""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    return x

def med(xs):
    return statistics.median(xs) if xs else None

def load_rows(path):
    d = json.load(open(path, encoding="utf-8"))
    rows = []
    if "battle_tl" in d:                      # schema A（probe_v2 直产，12 份）
        schema = "A{battle_tl,pre5,close_rows}"
    else:
        schema = "B{hold_tl,close_rows,_e2}"  # schema B（e12 驱动，11 份）
    for r in (d.get("battle_tl") or d.get("hold_tl") or []):
        rows.append(["battle" if "battle_tl" in d else "hold", r])
    for r in (d.get("pre5") or []):
        s = dict(r.get("sent") or {})
        s.setdefault("t", r.get("t"))
        rows.append(["pre5", s])
    for r in (d.get("close_rows") or []):
        rows.append(["close", r])
    rows.sort(key=lambda x: x[1].get("t", 0.0))
    return d, schema, rows

def tick_runs(seq):
    """[(value, n), ...] 压缩"""
    out = []
    for v in seq:
        if out and out[-1][0] == v:
            out[-1][1] += 1
        else:
            out.append([v, 1])
    return [tuple(x) for x in out]

def main():
    files = sorted(glob.glob(os.path.join(BASE, "*", "timeline.json")))
    print("=" * 100)
    print("P04 probe1 —— c2ab_x timeline.json 全量枚举（A02 焦点旗标假说可判定性）")
    print("=" * 100)
    print("枚举到 timeline.json：%d 份" % len(files))

    g = Counter()                      # 全局计数
    pair_recs = []                     # 所有 Δf==0 对
    stall_runs = []                    # Δf==0 连续链
    per_file_tick = []                 # (file, mode, exit_kind, c0, c1, cother, cunread, nrows)

    for path in files:
        trip = os.path.basename(os.path.dirname(path))
        rec = {}
        recp = os.path.join(os.path.dirname(path), "_rec.json")
        if os.path.exists(recp):
            rec = json.load(open(recp, encoding="utf-8"))
        mode = rec.get("mode", "?")
        exit_kind = rec.get("exit_kind", "?")
        d, schema, rows = load_rows(path)

        # ---- 覆盖度：行数 / tick 有效数 / tick 分布 ----
        n = len(rows)
        ticks, tss, frames = [], [], []
        c_unread = 0
        for seg, r in rows:
            t = iv(r.get("t"))
            if t is None:
                continue
            tss.append(t)
            tv = iv(r.get("tick"))
            if tv is None:
                c_unread += 1
            else:
                ticks.append(int(tv))
            fv = iv(r.get("frame"))
            if fv is not None:
                frames.append(int(fv))
        span = (max(tss) - min(tss)) if tss else 0.0
        ct = Counter(ticks)
        per_file_tick.append((trip, mode, exit_kind, ct.get(0, 0), ct.get(1, 0),
                              sum(v for k, v in ct.items() if k not in (0, 1)),
                              c_unread, n))

        # ---- 每段：中位采样间隔 ----
        seg_med = {}
        for seg in ("battle", "hold", "pre5", "close"):
            ts = [iv(r.get("t")) for s, r in rows if s == seg]
            ts = [t for t in ts if t is not None]
            dts = [b - a for a, b in zip(ts, ts[1:])]
            seg_med[seg] = med(dts)

        # ---- 相邻行对（合并序列，t 已排序）----
        # 运行段切分：singleton 值变化处
        runs = []
        cur = []
        prev_sin = "NA"
        for seg, r in rows:
            sin = iv(r.get("singleton"))
            if cur and sin is not None and prev_sin is not None and sin != prev_sin:
                runs.append(cur)
                cur = []
            cur.append((seg, r))
            if sin is not None:
                prev_sin = sin
        if cur:
            runs.append(cur)

        file_pairs = Counter()
        file_dt0 = []
        for run in runs:
            for (sa, ra), (sb, rb) in zip(run, run[1:]):
                ta, tb = iv(ra.get("t")), iv(rb.get("t"))
                fa, fb = iv(ra.get("frame")), iv(rb.get("frame"))
                ka, kb = iv(ra.get("tick")), iv(rb.get("tick"))
                if None not in (fa, fb):
                    fa, fb = int(fa), int(fb)
                if None not in (ka, kb):
                    ka, kb = int(ka), int(kb)
                ha, hb = iv(ra.get("hwnd")), iv(rb.get("hwnd"))
                if None in (ta, tb, fa, fb, ka, kb):
                    g["pair_skip_unreadable"] += 1
                    continue
                dt = tb - ta
                segtag = sa if sa == sb else "X(%s>%s)" % (sa, sb)
                if fb - fa == 0:
                    zeroed = (ha == 0 or hb == 0 or iv(rb.get("singleton")) == 0)
                    # 菜单趟全程 frame==0（0xA8E9A0==0 早退设计停帧）；battle/hold/pre5 段的
                    # frame==0 对同理。这些对与焦点无关，不算 A02 证据。
                    menu_idle = (fa == 0 and fb == 0 and
                                 (mode == "menu" or segtag in ("battle", "hold", "pre5")))
                    cls = "menu_idle" if menu_idle else ("zeroed" if zeroed else "RELEVANT")
                    key = (cls, segtag, (ka, kb))
                    file_pairs[key] += 1
                    pair_recs.append(dict(trip=trip, mode=mode, exit_kind=exit_kind,
                                          seg=segtag, ta=ta, tb=tb, dt=dt,
                                          tick=(ka, kb), cls=cls, frame=fa))
                    file_dt0.append(dt)
                    g["pair_df0_total"] += 1
                else:
                    file_pairs[("ADV", segtag, fa < fb)] += 1
                    g["pair_adv"] += 1

        # ---- Δf==0 连续链（停帧时长下界）----
        for run in runs:
            chain = []
            for seg, r in run:
                f = iv(r.get("frame"))
                t = iv(r.get("t"))
                k = iv(r.get("tick"))
                if f is not None: f = int(f)
                if k is not None: k = int(k)
                if f is None or t is None:
                    if chain:
                        stall_runs.append(dict(trip=trip, mode=mode, exit_kind=exit_kind,
                                               seg=chain[0][0], n=len(chain),
                                               dur=chain[-1][1] - chain[0][1],
                                               ticks=tuple(sorted(set(x[2] for x in chain))),
                                               f0=chain[0][3]))
                        chain = []
                    continue
                if chain and (f != chain[-1][3]):
                    stall_runs.append(dict(trip=trip, mode=mode, exit_kind=exit_kind,
                                           seg=chain[0][0], n=len(chain),
                                           dur=chain[-1][1] - chain[0][1],
                                           ticks=tuple(sorted(set(x[2] for x in chain))),
                                           f0=chain[0][3]))
                    chain = []
                chain.append((seg, t, k, f))
            if len(chain) >= 2:
                stall_runs.append(dict(trip=trip, mode=mode, exit_kind=exit_kind,
                                       seg=chain[0][0], n=len(chain),
                                       dur=chain[-1][1] - chain[0][1],
                                       ticks=tuple(sorted(set(x[2] for x in chain))),
                                       f0=chain[0][3]))

        # ---- 逐份打印 ----
        medstr = " ".join("%s=%s" % (s, ("%.2f" % seg_med[s]) if seg_med[s] else "-")
                          for s in ("battle", "hold", "pre5", "close") if seg_med.get(s) is not None)
        print("\n--- %s  schema=%s mode=%s exit=%s" % (trip, schema, mode, exit_kind))
        print("    行数=%d 含int tick=%d tick0=%d tick1=%d tick其它=%d unread=%d 跨度=%.1fs 中位Δt[%s]"
              % (n, len(ticks), ct.get(0, 0), ct.get(1, 0),
                 sum(v for k, v in ct.items() if k not in (0, 1)), c_unread, span, medstr))
        fp = sum(v for (c, s, k), v in file_pairs.items() if c == "RELEVANT")
        mi = sum(v for (c, s, k), v in file_pairs.items() if c == "menu_idle")
        adv = sum(v for (c, s, k), v in file_pairs.items() if c == "ADV")
        print("    对：Δf==0 RELEVANT=%d menu_idle=%d | Δf>0=%d" % (fp, mi, adv))
        for (c, s, k), v in sorted(file_pairs.items()):
            if c == "RELEVANT":
                print("      Δf==0 %s tick=%s × %d" % (s, k, v))
        for (c, s, k), v in sorted(file_pairs.items()):
            if c == "menu_idle":
                print("      menu_idle %s tick=%s × %d" % (s, k, v))

    # ================= 汇总 =================
    print("\n" + "=" * 100)
    print("== 汇总 1：tick 取值分布（逐份）")
    print("=" * 100)
    print("%-42s %-6s %-26s %5s %5s %5s %6s %5s" % ("trip", "mode", "exit_kind", "tk0", "tk1", "tkoth", "unread", "rows"))
    for trip, mode, ek, c0, c1, co, cu, n in per_file_tick:
        print("%-42s %-6s %-26s %5d %5d %5d %6d %5d" % (trip, mode, ek, c0, c1, co, cu, n))
    t0 = sum(x[3] for x in per_file_tick)
    t1 = sum(x[4] for x in per_file_tick)
    to = sum(x[5] for x in per_file_tick)
    tu = sum(x[6] for x in per_file_tick)
    tn = sum(x[7] for x in per_file_tick)
    print("合计：tick==0 共 %d，tick==1 共 %d，其它 int %d，unreadable %d，总行 %d" % (t0, t1, to, tu, tn))

    print("\n" + "=" * 100)
    print("== 汇总 2：Δf==0 相邻对 —— 类别 × 段 × tick 模式")
    print("=" * 100)
    agg = Counter()
    for p in pair_recs:
        agg[(p["cls"], p["seg"], p["tick"])] += 1
    for (c, s, k), v in sorted(agg.items()):
        print("  %-10s %-16s tick=%-8s × %d" % (c, s, str(k), v))
    rel = [p for p in pair_recs if p["cls"] == "RELEVANT"]
    print("  RELEVANT 对总数=%d；其中 tick 双端==1：%d，双端==0：%d，一端==0：%d"
          % (len(rel),
             sum(1 for p in rel if p["tick"] == (1, 1)),
             sum(1 for p in rel if p["tick"] == (0, 0)),
             sum(1 for p in rel if 0 in p["tick"] and p["tick"] != (0, 0))))

    print("\n== 汇总 3：Δf==0 连续链（停帧时长下界，秒）—— 只列 n>=2 的链")
    for s in sorted(stall_runs, key=lambda x: -x["dur"]):
        print("  %-42s %-6s %-26s seg=%-6s n=%-3d dur>=%.2fs frame0=%s ticks=%s"
              % (s["trip"], s["mode"], s["exit_kind"], s["seg"], s["n"], s["dur"], s["f0"], s["ticks"]))

    print("\n== 汇总 3.5：战斗趟 close 段帧率（hang 期间游戏是否全速）")
    for path in files:
        trip = os.path.basename(os.path.dirname(path))
        rec = json.load(open(os.path.join(os.path.dirname(path), "_rec.json"), encoding="utf-8")) \
            if os.path.exists(os.path.join(os.path.dirname(path), "_rec.json")) else {}
        if rec.get("mode") != "battle":
            continue
        d, schema, rows = load_rows(path)
        ts = [iv(r.get("t")) for s, r in rows if s == "close"]
        fs = [iv(r.get("frame")) for s, r in rows if s == "close"]
        pairs = [(a, b, fb - fa) for a, b, fa, fb in zip(ts, ts[1:], fs, fs[1:])
                 if a is not None and b is not None and fa is not None and fb is not None]
        if not pairs:
            print("  %-42s close 无有效对" % trip)
            continue
        dts = [b - a for a, b, _ in pairs]
        dfs = [df for _, _, df in pairs]
        t0, t1 = pairs[0][0], pairs[-1][1]
        f0, f1 = fs[0], fs[len(dfs)]
        print("  %-42s close %.1fs frame %+d → %.2f fps | 每对Δf min=%d 中位=%.0f | Δf==0 对=%d"
              % (trip, t1 - t0, f1 - f0, (f1 - f0) / (t1 - t0), min(dfs), med(dfs),
                 sum(1 for x in dfs if x == 0)))

    print("\n== 汇总 3.6：菜单趟 close 段 profile（frame 是否全程 0、tick 是否全程 1）")
    for path in files:
        trip = os.path.basename(os.path.dirname(path))
        recp = os.path.join(os.path.dirname(path), "_rec.json")
        rec = json.load(open(recp, encoding="utf-8")) if os.path.exists(recp) else {}
        if rec.get("mode") != "menu":
            continue
        d, schema, rows = load_rows(path)
        cs = [r for s, r in rows if s == "close"]
        fvals = set(int(r["frame"]) for _, r in [(0, x) for x in cs] if iv(r.get("frame")) is not None)
        kvals = set(int(x["tick"]) for x in cs if iv(x.get("tick")) is not None)
        nunread = sum(1 for x in cs if iv(x.get("tick")) is None)
        print("  %-42s %-26s close行=%-4d frame值集=%s tick值集=%s unread=%d"
              % (trip, rec.get("exit_kind", "?"), len(cs), sorted(fvals), sorted(kvals), nunread))

    print("\n== 汇总 4：功率对照（采样间隔 vs 可捕捉停帧时长下限）")
    all_dt = {}
    for seg in ("battle", "hold", "pre5", "close"):
        dts = [p["dt"] for p in pair_recs if p["seg"] == seg]
        dts += [p["dt"] for p in pair_recs if p["seg"].startswith("X") and seg in p["seg"]]
    # 重算：直接按段收间隔
    seg_dts = {s: [] for s in ("battle", "hold", "pre5", "close")}
    for path in files:
        d, schema, rows = load_rows(path)
        for seg in seg_dts:
            ts = [iv(r.get("t")) for s2, r in rows if s2 == seg]
            ts = [t for t in ts if t is not None]
            seg_dts[seg] += [b - a for a, b in zip(ts, ts[1:])]
    for seg, dts in seg_dts.items():
        if dts:
            print("  seg=%-7s n_int=%-5d 中位Δt=%.3fs p10=%.3fs p90=%.3fs → 可捕捉停帧下限≈中位Δt"
                  % (seg, len(dts), med(dts), sorted(dts)[max(0, int(0.1 * len(dts)) - 1)],
                     sorted(dts)[min(len(dts) - 1, int(0.9 * len(dts)))]))
        else:
            print("  seg=%-7s 无数据" % seg)

    print("\n== 判定输入")
    print("  A02 假说（操作化）：frame 停进（Δf==0）应伴随 tick==0（失焦）；"
          "若 RELEVANT 对大量 tick==1，则假说在这批数据上被反证。")
    print("  menu_idle 对（frame==0 设计停帧）与 zeroed 对（全局清零残值）均不构成 A02 证据。")

if __name__ == "__main__":
    main()
