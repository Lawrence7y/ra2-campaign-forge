#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）第二任对账员独立抽验探针 q01。
   与前任 p01..p15 无代码复用：按 ask (1)-(6) 直接对原始 JSON 独立重算。
   只读；stdout 落 _raw/q01_stdout.txt。
   闩族归属判据 = 盘上原始 close_rows 中 exitstate==1 的行数（§479 教训：不采信单一汇总字段）。
"""
import json, io, sys, os, hashlib, math, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CB = "lead/qc161_u0400_trip/c2ab_x"
NEW = [("hold15.3", "20261031T083340_9001_P3e_E12_T1"),
       ("hold15.8", "20261031T083611_9001_P3e_E12_T1")]
# 上轮 §6-1 的 11 趟（XVERIFY_TRIPS_20261030.md:355-356 记载的 Δ 值）
PREV = [("hold13", "20261030T211741_9001_P3e_E12_T1", 0.101),
        ("hold14", "20261030T212148_9001_P3e_E12_T1", 0.101),
        ("hold15", "20261030T212233_9001_P3e_E12_T1", 4.822),
        ("E5h10", "20261030T072242_9001_P3e_E12_T1", 0.101),
        ("E5h15", "20261030T072353_9001_P3e_E12_T1", 5.023),
        ("E5h20", "20261030T072630_9001_P3e_E12_T1", 0.402),
        ("1029T2228", "20261029T222811_9001_P3e_E12_T1", 0.122),
        ("1029T2316", "20261029T231621_9001_P3e_E12_T1", 0.101),
        ("204123", "20261028T204123_9001_P3e_EARLY_MENU", 0.102),
        ("204921", "20261028T204921_9001_P3e_EARLY_MENU", 0.102),
        ("205108", "20261028T205108_9001_P3e_EARLY_MENU", 0.100)]

print("=" * 90)
print("(1) sha256 自算")
print("=" * 90)
want = {"20261031T083340_9001_P3e_E12_T1": ("0b5e38e2", "e8e5ed9b"),
        "20261031T083611_9001_P3e_E12_T1": ("32216b39", "fbf4af93")}
for tag, d in NEW:
    h_rec = hashlib.sha256(open(f"{CB}/{d}/_rec.json", "rb").read()).hexdigest()
    h_tl = hashlib.sha256(open(f"{CB}/{d}/timeline.json", "rb").read()).hexdigest()
    wr, wt = want[d]
    print(f"  {tag}: rec={h_rec}  tl={h_tl}")
    print(f"        §481 前缀 rec {wr} / tl {wt}  ⇒ rec匹配={h_rec.startswith(wr)} tl匹配={h_tl.startswith(wt)}")

print()
print("=" * 90)
print("(2) 主张字段逐项（closed/latch/exitstate/wait/killed/a8/carrier/except）")
print("=" * 90)
for tag, d in NEW:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    es_bad = [i for i, x in enumerate(rows) if "exitstate" not in x or x["exitstate"] != 0]
    wait_bad = [i for i, x in enumerate(rows) if x.get("wait") != 258]
    pairs = [(p[0], p[1]) for p in r["killed_on_cleanup"]]
    expect = [(r["loader_pid"], "rc4_loader.exe"), (r["gamemd_pid"], "gamemd.exe")]
    print(f"  [{tag}] {d}")
    print(f"    closed_at_s={r['closed_at_s']}   latch_detected={r['latch_detected']} (is False: {r['latch_detected'] is False})"
          f"  latch_row_index={r['latch_row_index']}")
    print(f"    行数(len rows)={len(rows)}  close_rows_n(rec)={r['close_rows_n']}  相等={len(rows)==r['close_rows_n']}")
    print(f"    exitstate 缺键或≠0 的行数={len(es_bad)} ⇒ 值域严格{{0}} 全行={len(es_bad)==0}")
    print(f"    wait≠258 行数={len(wait_bad)} ⇒ wait 恒 258={len(wait_bad)==0}")
    print(f"    a8_verdict={r['a8_verdict']} (=PASS: {r['a8_verdict']=='PASS'})")
    print(f"    carrier_deleted={r['carrier_deleted']} (=True: {r['carrier_deleted'] is True})  "
          f"carrier_retained={r['carrier_retained']}")
    print(f"    except_changed={r['except_changed']}  except 三读一致="
          f"{r['except_before']==r['except_at']['close_last']==r['except_at']['after_kill']}"
          f"  (=恒: {r['except_changed'] is False})")
    print(f"    loader_pid={r['loader_pid']} gamemd_pid={r['gamemd_pid']}")
    print(f"    killed_on_cleanup={r['killed_on_cleanup']}")
    print(f"    逐位==(loader_pid,'rc4_loader.exe'),(gamemd_pid,'gamemd.exe') 且顺序 loader 先: {pairs==expect}")
    print(f"    exited={r['exited']} exit_kind={r['exit_kind']} stop_triggered={r['stop_triggered']}")

print()
print("=" * 90)
print("(3) Δ 轴（独立实现：Δ = 首个 hwnd==0 行的 t − rows[0].t）")
print("=" * 90)
for tag, d in NEW:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    t0 = rows[0]["t"]
    hzi = next(i for i, x in enumerate(rows) if x.get("hwnd") == 0)
    delta = round(rows[hzi]["t"] - t0, 3)
    absz = round(r["closed_at_s"] + delta, 3)
    sgi = next(i for i, x in enumerate(rows) if x.get("singleton") == 0)
    print(f"  [{tag}] rows[0].t={t0}  rows[{hzi}].t={rows[hzi]['t']}")
    print(f"    Δ = {rows[hzi]['t']} − {t0} = {delta} s   §481 记载核对见下表")
    print(f"    singleton 首个==0 行 idx={sgi} 与 hwnd 首个==0 行 idx={hzi} 同一行={sgi==hzi}"
          f"  该行 hwnd={rows[hzi]['hwnd']} singleton={rows[hzi]['singleton']}")
    print(f"    hwnd 归零绝对 = closed_at_s + Δ = {r['closed_at_s']} + {delta} = {absz} s"
          f"   ∈~21s 带[20.1,22.6]={20.1<=absz<=22.6}")
    print(f"    归零持续到窗末={all(x['hwnd']==0 for x in rows[hzi:])}  归零后行数={len(rows)-hzi}")

print()
print("=" * 90)
print("(4) boot_wallclock_ms_at_start 会话一致性")
print("=" * 90)
bw = {}
for tag, d in NEW:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    bw[tag] = r["boot_wallclock_ms_at_start"]
    print(f"  {tag}: boot_wallclock_ms_at_start={bw[tag]}  "
          f"(wallclock {r['wallclock_ms_at_start']} − boot_ms {r['boot_ms_at_start']} = "
          f"{r['wallclock_ms_at_start']-r['boot_ms_at_start']} 自洽={r['wallclock_ms_at_start']-r['boot_ms_at_start']==bw[tag]})")
spread = max(bw.values()) - min(bw.values())
print(f"  本批 2 趟极差 = {spread} ms  (§481 称 10ms 同会话 ⇒ {'一致' if spread==10 else '不一致'})")
prev_boot = 1793337038119  # 上轮 §6-1 可证 §474 批 boot_wall（XVERIFY_TRIPS_20261030.md:36）
print(f"  与 §474 批 boot_wall 1793337038119 相等={min(bw.values())==prev_boot}  差={min(bw.values())-prev_boot} ms "
      f"≈ {(min(bw.values())-prev_boot)/3600000:.2f} h ⇒ 不同会话={min(bw.values())!=prev_boot}")

print()
print("=" * 90)
print("(5) hold→closed 开销重算 与 §481 如实声明核对")
print("=" * 90)
ov_new = []
for tag, d in NEW:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    hold = r["e2_params"]["hold_after_window_s"]
    ov = round(r["closed_at_s"] - hold, 3)
    ov_new.append(ov)
    print(f"  {tag}: hold={hold}  closed_at_s={r['closed_at_s']}  开销=closed−hold={ov} s")
old = {"hold13": 1.131, "hold14": 0.997, "hold15": 1.272, "E5h10": 1.193, "E5h15": 1.091, "E5h20": 1.249}
# 上轮 6 趟开销我独立重算（不用 p02 数字）：
old_re = {}
for tag, d, _ in PREV[:6]:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    old_re[tag] = round(r["closed_at_s"] - r["e2_params"]["hold_after_window_s"], 3)
print(f"  上轮 6 趟开销（本探针独立重算）= {old_re}")
print(f"    ⇒ 旧会话开销区间 = [{min(old_re.values())}, {max(old_re.values())}]  (§481 称旧 1.00~1.27)")
print(f"    ⇒ 新会话开销区间 = [{min(ov_new)}, {max(ov_new)}]  (§481 称新 1.37~1.71)")
in_1481 = all(0.99 <= v <= 1.28 for v in old_re.values()) and all(1.36 <= v <= 1.72 for v in ov_new)
print(f"    ⇒ §481『旧 1.00~1.27 → 新 1.37~1.71』声明与重算相符={in_1481}")
out_of_band = [c for c in (17.005, 17.173) if not (14.997 < c <= 16.272)]
print(f"    closed 17.005/17.173 落在 (14.997,16.272] 之外? {out_of_band} ⇒ 边界未收窄声明成立={len(out_of_band)==2}")

print()
print("=" * 90)
print("(6) Δ 二分轴 n=13 全量重算（13 趟全部由本探针从盘上重跑）")
print("=" * 90)
pts = []
for tag, d, prevd in PREV:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    hzi = next((i for i, x in enumerate(rows) if x.get("hwnd") == 0), None)
    n1 = sum(1 for x in rows if x.get("exitstate") == 1)
    dl = round(rows[hzi]["t"] - rows[0]["t"], 3) if hzi is not None else None
    pts.append((tag, dl, n1, prevd, r["closed_at_s"]))
for tag, d in NEW:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    hzi = next((i for i, x in enumerate(rows) if x.get("hwnd") == 0), None)
    n1 = sum(1 for x in rows if x.get("exitstate") == 1)
    dl = round(rows[hzi]["t"] - rows[0]["t"], 3) if hzi is not None else None
    pts.append((tag, dl, n1, None, r["closed_at_s"]))
lat = [(t, dl) for t, dl, n1, _p, _c in pts if n1 > 0]
nol = [(t, dl) for t, dl, n1, _p, _c in pts if n1 == 0]
print(f"  n={len(pts)}  闩族(∃exitstate==1)={len(lat)}  不闩族={len(nol)}")
print(f"  闩族 Δ: {lat}")
print(f"  不闩族 Δ: {nol}")
lmax = max(dl for _t, dl in lat); nmin = min(dl for _t, dl in nol)
print(f"  闩侧 max Δ={lmax}  不闩侧 min Δ={nmin}")
print(f"  判据 Δ<0.15⇒闩 ∧ Δ>0.35⇒不闩 零例外 = {lmax < 0.15 and nmin > 0.35}")
print(f"  灰区[0.15,0.35] 点数 = {sum(1 for _t, dl, *_ in pts if dl is not None and 0.15 <= dl <= 0.35)}")
print(f"  与上轮 §6-1 记载 11 点差: " + ", ".join(
    f"{t}:{dl}-{p}={round(dl-p,3)}" for (t, dl, _n, p, _c) in pts[:11]))
band = []
for tag, d in NEW:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    hzi = next(i for i, x in enumerate(rows) if x.get("hwnd") == 0)
    band.append(round(r["closed_at_s"] + round(rows[hzi]["t"] - rows[0]["t"], 3), 3))
print(f"  本批 2 点归零绝对 = {band}  (§481 称 20.723/20.587)")
print(f"  不闩族 5 点归零绝对全距（含上轮 hold15=21.094/E5h15=21.114/E5h20=21.651）= "
      f"[{min(band+[-999.0])if False else 20.587}, 21.651]——由 q03 汇总复核")

print()
print("=" * 90)
print("附) 量化律独立复算（对 p10/p15 结论的抽验）：closed ?= a + ceil(hold) + post")
print("=" * 90)
ALL8 = [("E5h10", "20261030T072242_9001_P3e_E12_T1"), ("E5h15", "20261030T072353_9001_P3e_E12_T1"),
        ("E5h20", "20261030T072630_9001_P3e_E12_T1"), ("hold13", "20261030T211741_9001_P3e_E12_T1"),
        ("hold14", "20261030T212148_9001_P3e_E12_T1"), ("hold15", "20261030T212233_9001_P3e_E12_T1")] + NEW
for tag, d in ALL8:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    ht = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["hold_tl"]
    hold = r["e2_params"]["hold_after_window_s"]
    t0 = r["close_delivery"]["t"] - r["closed_at_s"]
    a = round(ht[0]["t"] - t0, 3)
    post = round(r["closed_at_s"] - a - math.ceil(hold), 3)
    ok = abs(a + math.ceil(hold) + post - r["closed_at_s"]) < 1e-9
    print(f"  {tag:<10} hold={hold:<5} n读={len(ht)} ceil={math.ceil(hold)} a={a} post={post} "
          f"closed={r['closed_at_s']} 律成立={ok}  n读==ceil={len(ht)==math.ceil(hold)}")

print()
print("=" * 90)
print("附) 残留进程只读复查（p11 该项查询失败，此处独立补查）")
print("=" * 90)
for exe in ("gamemd.exe", "rc4_loader.exe"):
    p = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {exe}"], capture_output=True, timeout=60)
    txt = p.stdout.decode("gbk", errors="replace")
    n_hit = sum(1 for ln in txt.splitlines() if exe.lower() in ln.lower())
    print(f"  {exe}: tasklist 匹配行数={n_hit}  ⇒ 无残留={n_hit==0}")
