#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p08：Δ 二分轴的样本边界检验——把同目录全部 22 趟（含 10-28 旧代）纳入，
   检验「Δ<0.15 ⇒ 闩」在 P3e 早窗菜单族之外的成立性。族判定一律用盘上 exitstate==1 行数（原始行）。
"""
import json, io, sys, os, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CB = "lead/qc161_u0400_trip/c2ab_x"

print("{:<42} {:>7} {:>6} {:>8} {:>7} {:>7} {:>5} {:>5} {:>10}  {}".format(
      "trip", "mode", "watch", "closed", "Δ_A", "hz0", "n(1)", "sing0", "exit_kind", "family/config"))
rows_all = []
for p in sorted(glob.glob(f"{CB}/2*")):
    if not os.path.isdir(p):
        continue
    tj, rj = f"{p}/timeline.json", f"{p}/_rec.json"
    if not (os.path.isfile(tj) and os.path.isfile(rj)):
        print(f"  {os.path.basename(p):<42} 缺 timeline/rec（仅 _rec 或空）→ 本轴不可算")
        continue
    r = json.load(open(rj, encoding="utf-8"))
    rows = json.load(open(tj, encoding="utf-8")).get("close_rows") or []
    if not rows:
        print(f"  {os.path.basename(p):<42} close_rows 空"); continue
    hz = next((i for i, x in enumerate(rows) if x.get("hwnd") == 0), None)
    sg = next((i for i, x in enumerate(rows) if x.get("singleton") == 0), None)
    n1 = sum(1 for x in rows if x.get("exitstate") == 1)
    dA = round(rows[hz]["t"] - rows[0]["t"], 3) if hz is not None else None
    ev = sorted({str(x.get("exitstate")) for x in rows})
    fam = "闩" if n1 > 0 else "不闩"
    gen = "P3e早窗菜单族" if str(r.get("trip_tag", "")).startswith("P3e") else "旧代(10-28 其他协议)"
    print("{:<42} {:>7} {:>6} {:>8} {:>7} {:>7} {:>5} {:>5} {:>10}  {} / {}".format(
        os.path.basename(p)[:42], r.get("mode"), r.get("watch_s"), r.get("closed_at_s"),
        str(dA), str(hz), n1, str(sg), str(r.get("exit_kind"))[:10], fam, gen))
    rows_all.append(dict(dir=os.path.basename(p), dA=dA, n1=n1, fam=fam, gen=gen,
                         closed=r.get("closed_at_s"), tag=r.get("trip_tag"), mode=r.get("mode"),
                         ev=ev, note=r.get("note", "")[:60]))

print("\n== 判据违反检验 ==")
def viol(sel):
    bad = []
    for x in sel:
        if x["dA"] is None:
            continue
        if x["dA"] < 0.15 and x["fam"] != "闩":
            bad.append(("Δ<0.15 却不闩", x))
        if x["dA"] > 0.35 and x["fam"] != "不闩":
            bad.append(("Δ>0.35 却闩", x))
    return bad

p3e = [x for x in rows_all if x["gen"].startswith("P3e")]
old = [x for x in rows_all if not x["gen"].startswith("P3e")]
print(f"  P3e 族内 n={len(p3e)}  违反数={len(viol(p3e))}  ⇒ §481「n=13 零例外」={len(viol(p3e)) == 0}")
print(f"  旧代 n={len(old)}  违反数={len(viol(old))}")
for kind, x in viol(old):
    print(f"    ✗ {kind}: {x['dir']} Δ={x['dA']} n(1)={x['n1']} closed={x['closed']} tag={x['tag']} mode={x['mode']}")
print("\n  旧代各趟 exitstate 值域（核对 exitstate 读数在这些趟里是否可用）:")
for x in old:
    print(f"    {x['dir'][:42]:<44} ev={x['ev'][:3]}  note={x['note']}")
print(f"\n  ⇒ 结论：n=13 零例外在 **P3e 早窗菜单族（{len(p3e)} 趟）** 内成立；"
      f"同目录旧代 {len(old)} 趟中 {len(viol(old))} 趟呈「Δ<0.15 却不闩」（其中 Guard=1+Bail=1 同配置的 "
      f"{sum(1 for k, y in viol(old) if y['tag'] == 'P3_G1B1')} 趟）⇒ 「Δ<0.15 ⇒ 闩」不可作为族外判别式外推。")
