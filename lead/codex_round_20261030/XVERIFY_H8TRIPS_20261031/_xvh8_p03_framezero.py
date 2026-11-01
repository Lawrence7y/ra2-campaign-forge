#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 对账探针 p03：frame 计数器起点语义 + q/r 早相 fps 张力定量。

要回答（ask 任务 3）：
 (a) 起点语义：MAP 加载后从 0 计（battle 起点）还是自进程起累计？
     证据面：① E12 菜单趟（同 VA 0x00A8ED84）frame 恒 0；② ha/hb 的 H8 绑帧路径
     （入口读数若 >400 必触发 first_read 越界拒采 ⇒ 入口 frame≤400 是硬上界）；
     ③ nav_end→w0 墙钟 vs w0 首帧数；④ 全库趟 f[0] 与「等待墙钟 × 本趟窗内 fps」的一致性。
 (b) 若从 battle 起计：q/r 从 battle 起到 w0 的实际墙钟与隐含早相平均 fps。
 (c) 张力消解判定。

口径：ts 字段（ISO，秒级）给粗锚；BUDGET stage_* 是 time.monotonic 秒（相对趟起点）；
 measure_w*.json 的 t_abs0 是 time.time()、samples.t 是 time.perf_counter()；
 NAV 行 h7_nav_end_t 是 perf_counter。跨量纲处一律显式标注，不假装同轴。
只读。
"""
import json, io, sys, os, glob, math, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
# (1) 同 VA 在菜单趟恒 0 的证据（E12/c2ab_x 族，读的是 probe_v2 G_FRAME=0x00A8ED84）
V2 = "lead/qc161_u0400_trip/codex_e12_e5_20261030/candidate/_drive_c2_x_probe_v2.py"
H8 = "lead/goal1_harness8_20261031/qc151_trip.harness8.py"
print("=" * 78)
print("(0) 同一读点 VA：驱动侧与 harness 侧是否同址")
print("=" * 78)
for p, pat in [(V2, r"^G_FRAME\s*=\s*(0x[0-9A-Fa-f]+)"), (H8, r"^MEASURE_CURRENT_FRAME_VA\s*=\s*(0x[0-9A-Fa-f]+)")]:
    lines = open(p, encoding="utf-8").read().splitlines()
    for i, ln in enumerate(lines, 1):
        if re.match(pat, ln.strip()):
            print(f"  {p}:{i}  {ln.strip()}")

print("\n" + "=" * 78)
print("(1) 菜单趟（未进 battle）frame 读数：是否恒 0")
print("=" * 78)
menu_trips = ["20261028T204123_9001_P3e_EARLY_MENU", "20261030T212233_9001_P3e_E12_T1",
              "20261031T154139_9001_P3e_E12_T1", "20261031T083340_9001_P3e_E12_T1"]
for d in menu_trips:
    p = f"lead/qc161_u0400_trip/c2ab_x/{d}/timeline.json"
    if not os.path.isfile(p):
        print(f"  {d}: 缺件"); continue
    tl = json.load(open(p, encoding="utf-8"))
    fr = [r.get("frame") for r in tl["hold_tl"]] + [r.get("frame") for r in tl["close_rows"]]
    setv = sorted(set(str(x) for x in fr))
    print(f"  {d[:22]}: hold_tl+close_rows 共 {len(fr)} 行，frame 取值集 = {setv}")

print("\n" + "=" * 78)
print("(2) 全库 measure 趟：f[0]（w0 首帧） vs nav_end→w0 墙钟 vs 本趟窗内 fps")
print("=" * 78)
hdr = "{:<20}{:>7}{:>9}{:>9}{:>8}{:>8}{:>9}{:>9}{:>10}{:>9}{:>9}"
print(hdr.format("trip", "w0f0", "w0flast", "窗fps", "fps15", "units0", "fr_s", "setl_s",
                 "nav→w0_s", "f0/时长", "h7/h8"))
rows = []
for base in sorted(glob.glob(f"{ROOT}/*/measure_w0.json")):
    d = os.path.basename(os.path.dirname(base))
    if d == "lead":
        continue
    try:
        m0 = json.load(open(base, encoding="utf-8"))
    except Exception as e:
        print(f"  {d}: w0 读取失败 {e!r}"); continue
    if not isinstance(m0.get("samples"), dict) or not m0["samples"].get("f"):
        print(f"  {d:<20}: samples 缺失/零样（短路趟）verdict={m0.get('verdict')}"); continue
    f0 = m0["samples"]["f"][0]; f1 = m0["samples"]["f"][-1]
    st = m0.get("stats") or {}
    fps = st.get("fps_avg"); g = m0.get("gate") or {}
    qf = os.path.join(os.path.dirname(base), "qc151_fields.json")
    gen = "h?"
    fr_s = None; setl = None; nav_end_wall = None; started = None; fw = None; net = None
    if os.path.isfile(qf):
        try:
            fld = json.load(open(qf, encoding="utf-8"))
        except Exception:
            fld = []
        def gv(grp, key):
            vals = [e["value"] for e in fld if isinstance(e, dict) and e.get("group") == grp and e.get("key") == key]
            return vals[-1] if vals else None
        fr_s = gv("BUDGET", "stage_seconds:frame")
        setl = gv("MEASURE", "settle_seconds")
        fw = gv("MEASURE", "h7_frame_wait")
        net = gv("NAV", "h7_nav_end_t")
        started = gv("META", "started")
        nv = [e for e in fld if isinstance(e, dict) and e.get("group") == "NAV" and e.get("key") == "verdict"]
        nav_end_wall = nv[0].get("ts") if nv else None
        gen = "H8" if fw is not None else ("H7" if net is not None or gv("META","h7_fs_rect_wait_skipped") is not None else "H6")
    # nav→w0 墙钟近似：frame 段 + settle（monotonic 口径，趟内自洽）
    n2w = round((fr_s or 0) + (setl or 0), 3) if (fr_s is not None and setl is not None) else None
    implied = round(f0 / n2w, 2) if (n2w and n2w > 0) else None
    print(hdr.format(d[:20], f0, f1, f"{fps:.1f}" if isinstance(fps,(int,float)) else str(fps),
                     g.get("pre_fps15"), g.get("units0"), fr_s, setl, n2w, implied, gen))
    rows.append(dict(d=d, f0=f0, f1=f1, fps=fps, units=g.get("units0"), fr_s=fr_s, setl=setl,
                     n2w=n2w, implied=implied, gen=gen, fw=fw, nav_end_wall=nav_end_wall, started=started))

print("\n" + "=" * 78)
print("(3) 承重三趟细算：q / r / hb（+ha）")
print("=" * 78)
for tag in ("l3_20261023q", "l3_20261023r", "l3_20261031ha", "l3_20261031hb", "l3_20261021"):
    rr = next((x for x in rows if x["d"] == tag), None)
    if rr is None:
        print(f"  {tag}: 不在表内（可能零样）"); continue
    print(f"\n  --- {tag} (gen={rr['gen']}) ---")
    print(f"    started(ts)          = {rr['started']}")
    print(f"    NAV.verdict ts       = {rr['nav_end_wall']}   (nav 收口墙钟，秒级)")
    print(f"    NAV.h7_nav_end_t     = {json.dumps(next((e['value'] for e in json.load(open(f'{ROOT}/{tag}/qc151_fields.json',encoding='utf-8')) if e.get('group')=='NAV' and e.get('key')=='h7_nav_end_t'), None), ensure_ascii=False)}")
    print(f"    stage_seconds:frame  = {rr['fr_s']}   settle={rr['setl']}   nav→w0≈{rr['n2w']} s")
    print(f"    h7_frame_wait(H8)    = {json.dumps(rr['fw'], ensure_ascii=False)}")
    print(f"    w0 首帧 f0={rr['f0']}  末帧={rr['f1']}  窗内 fps_avg={rr['fps']}  units0={rr['units']}")
    if rr["fw"]:
        w = rr["fw"]["wait_s"]; n = rr["fw"]["n"]
        print(f"    ★ H8 绑帧实测：入口 frame ≤ {n}（越界即拒采），0→{n} 用 {w} s ⇒ 平均 {n/w:.2f} fps")
    if rr["n2w"]:
        print(f"    ★ 若计数器 battle 起零：0→{rr['f0']} 用 ≤{rr['n2w']} s ⇒ 平均 ≥{rr['f0']/rr['n2w']:.2f} fps"
              f"（上界口径：nav→w0 墙钟含加载/短路等待，真实播放时长更短 ⇒ 真实平均只会更高）")

print("\n" + "=" * 78)
print("(4) 一致性检验：f0 与「等待墙钟 × 同趟窗内 fps」之比")
print("=" * 78)
print("    ratio = f0 / (n2w × w0窗内fps_avg)：≈1 ⇒ 等待期帧率与窗内同量级（自洽）；≫1 ⇒ 等待期比窗内快")
for x in rows:
    if x["n2w"] and isinstance(x["fps"], (int, float)) and x["fps"]:
        r = x["f0"] / (x["n2w"] * x["fps"])
        print(f"  {x['d']:<20} f0={x['f0']:<6} n2w={x['n2w']:<8} fps={x['fps']:<7.1f} ratio={r:6.2f}  gen={x['gen']} units0={x['units']}")
