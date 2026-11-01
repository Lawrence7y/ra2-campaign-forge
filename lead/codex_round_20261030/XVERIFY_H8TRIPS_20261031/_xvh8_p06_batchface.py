#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 对账探针 p06：§486/§487 批面主张复核（RR 75 窗相邻拍 / units 单调性 / 闩→退带全量 /
   拒采路径未触发 / 载体与进程残留 / except 行数 / T0-T1 零写 / harness8 v2 冻结维持）。
只读。
"""
import json, io, sys, os, glob, math, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
CB = "lead/qc161_u0400_trip/c2ab_x"

print("=" * 78)
print("(1) RR 主张「真机产物复算 75 窗相邻拍 maxΔ：74 窗=1、1 窗=3」独立复算（全库窗）")
print("=" * 78)
per = []
for p in sorted(glob.glob(f"{ROOT}/*/measure_w*.json") + glob.glob(f"{ROOT}/archive_*/*/measure_w*.json")):
    try:
        m = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    e = m.get("frame_edges")
    if not e:
        continue
    ds = [b[0] - a[0] for a, b in zip(e, e[1:])]
    if not ds:
        continue
    per.append((max(ds), len(ds), os.path.relpath(p, ROOT), (m.get("stats") or {}).get("n_multi_advance")))
print(f"  可测窗数（含 frame_edges 且有 ≥2 沿）= {len(per)}")
from collections import Counter
print("  maxΔ 分布 =", dict(Counter(x[0] for x in per)))
big = [x for x in per if x[0] > 1]
print(f"  maxΔ>1 的窗: {big}")
print("  ⇒ RR 的『74 窗=1、1 窗=3』口径核对：本探针为全库窗集合（口径更大），差异如实报")

print("\n" + "=" * 78)
print("(2) units 单调性（§487「units 持续下降=活动窗」逐窗判定）")
print("=" * 78)
for d in ("l3_20261031ha", "l3_20261031hb", "l3_20261023q", "l3_20261023r"):
    for wp in sorted(glob.glob(f"{ROOT}/{d}/measure_w*.json")):
        m = json.load(open(wp, encoding="utf-8"))
        u = [c.get("units") for c in (m.get("counters") or []) if c.get("units") is not None]
        if len(u) < 2:
            print(f"  {d}/{os.path.basename(wp)}: counters 不足"); continue
        inc = [(i, u[i], u[i+1]) for i in range(len(u)-1) if u[i+1] > u[i]]
        eq = sum(1 for i in range(len(u)-1) if u[i+1] == u[i])
        print(f"  {d}/{os.path.basename(wp)}: n={len(u)} {u[0]}→{u[-1]} 净Δ={u[-1]-u[0]} "
              f"上升步={len(inc)} 持平步={eq} 严格非增={len(inc)==0}")
        if inc:
            print(f"      上升步明细(前4): {inc[:4]}")

print("\n" + "=" * 78)
print("(3) 闩→退带全量（P3e 早窗菜单族，自然退出闩趟）—— §485「既往带 2.004~2.108」")
print("=" * 78)
fam = [("hold13", "20261030T211741_9001_P3e_E12_T1"), ("hold14", "20261030T212148_9001_P3e_E12_T1"),
       ("E5h10", "20261030T072242_9001_P3e_E12_T1"), ("E12-2228", "20261029T222811_9001_P3e_E12_T1"),
       ("E12-2316", "20261029T231621_9001_P3e_E12_T1"), ("204123(挂死)", "20261028T204123_9001_P3e_EARLY_MENU"),
       ("204921", "20261028T204921_9001_P3e_EARLY_MENU"), ("205108", "20261028T205108_9001_P3e_EARLY_MENU"),
       ("2C", "20261031T154139_9001_P3e_E12_T1")]
vals = []
for tag, dd in fam:
    r = json.load(open(f"{CB}/{dd}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{dd}/timeline.json", encoding="utf-8"))["close_rows"]
    ones = [i for i, x in enumerate(rows) if x.get("exitstate") == 1]
    l2e = round(rows[-1]["t"] - rows[ones[0]]["t"], 3) if ones else None
    print(f"  {tag:<12} exited={r.get('exited')!s:<6} n(1)={len(ones):<5} 闩→退={l2e} "
          f"exit_kind={r.get('exit_kind')} 末行wait={rows[-1]['wait']}")
    if ones and r.get("exited") is True:
        vals.append((tag, l2e))
print(f"  自然退闩趟带 = [{min(v for _t,v in vals):.3f}, {max(v for _t,v in vals):.3f}]  n={len(vals)}")
print(f"  成员 = {vals}")

print("\n" + "=" * 78)
print("(4) H8 拒采路径本批未触发（offset=0 全 0 / 无 overrun / 无 timeout / 无 jump）")
print("=" * 78)
for d in ("l3_20261031ha", "l3_20261031hb"):
    f = json.load(open(f"{ROOT}/{d}/qc151_fields.json", encoding="utf-8"))
    fw = [e["value"] for e in f if e.get("key") == "h7_frame_wait"]
    v = [e["value"] for e in f if e.get("group") == "MEASURE" and e.get("key") == "verdict"]
    hz = round(fw[-1]["poll_count"] / fw[-1]["wait_s"], 1)
    fps = round(fw[-1]["n"] / fw[-1]["wait_s"], 2)
    print(f"  {d}: h7_frame_wait 行数={len(fw)}（期望 1） reached={fw[-1]['reached_frame']} "
          f"offset={fw[-1]['offset_frames']} overrun={fw[-1]['overrun']} timed_out={fw[-1]['timed_out']} "
          f"verdict={v[-1]!r} 有效轮询={hz}Hz 等待期平均={fps}fps")

print("\n" + "=" * 78)
print("(5) 批面卫生：载体目录 / ct 空 / T0-T1 零写 / except 行数 / WER / S4")
print("=" * 78)
for d in ("l3_20261031ha", "l3_20261031hb"):
    base = f"{ROOT}/{d}"
    ct = os.path.join(base, "ct")
    lft = os.listdir(ct) if os.path.isdir(ct) else "<ct 不存在>"
    td = json.load(open(os.path.join(base, "T0_T1_diff.json"), encoding="utf-8"))
    esd = json.load(open(os.path.join(base, "except_set_diff.json"), encoding="utf-8"))
    f = json.load(open(os.path.join(base, "qc151_fields.json"), encoding="utf-8"))
    def gv(g, k):
        v = [e["value"] for e in f if e.get("group") == g and e.get("key") == k]
        return v[-1] if v else None
    print(f"  {d}: ct 残留={lft} T0_T1_diff={json.dumps(td)[:60]} "
          f"except pre/post={esd.get('pre_line_count')}/{esd.get('post_line_count')} new={esd.get('new_exception_count')} "
          f"wer={gv('WER','wer_verdict')} s4hit={gv('S4','hit_count')} iso={gv('ISOLATION','iso_verdict')} "
          f"final_manifest={gv('MANIFEST','final_verdict')} del={json.loads(json.dumps(gv('DELETE','carrier_delete')))['deleted'] if gv('DELETE','carrier_delete') else None}")

print("\n" + "=" * 78)
print("(6) harness8 v2 冻结维持 + 与 harness7 差异（§486「0删/160增」）")
print("=" * 78)
h7 = "lead/goal1_harness7_20261023/qc151_trip.harness7.py"
h8 = "lead/goal1_harness8_20261031/qc151_trip.harness8.py"
print(f"  h7 sha256={hashlib.sha256(open(h7,'rb').read()).hexdigest()[:16]}  h8 sha256={hashlib.sha256(open(h8,'rb').read()).hexdigest()[:16]}")
import difflib
a = open(h7, encoding="utf-8").read().splitlines()
b = open(h8, encoding="utf-8").read().splitlines()
add = dele = 0
for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
    if t == "insert": add += j2 - j1
    elif t == "delete": dele += i2 - i1
    elif t == "replace": add += j2 - j1; dele += i2 - i1
print(f"  行数 h7={len(a)} h8={len(b)}  增={add} 删={dele}（§486 主张 0删/160增）")

print("\n" + "=" * 78)
print("(7) 趟数账（§485 31→32、§487 32→34）盘上可证性")
print("=" * 78)
n_c2 = len([x for x in glob.glob(f"{CB}/*") if os.path.isdir(x)])
n_trip = len([x for x in glob.glob(f"{ROOT}/l*") if os.path.isdir(x)])
print(f"  c2ab_x 目录（含非趟件）= {n_c2}；qc161_u0400_trip 下 l* 目录 = {n_trip}")
print("  ⇒ 台账「趟数」为人工累计口径，盘上无单一权威清单可独立复算 → 该项标 UNVERIFIED（非不符）")
