#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s04：① W1/W2 终局帧冻结定性 —— 冻结起点是否恰为 units 停变点；有无战斗期内冻结被误归终局。
   并把 W0/W1/W2 三窗按绝对时间轴排布，检查 W0 之后 units 走势。
"""
import json, io, sys, os, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = r"D:\Project\ra2-campaign-forge"
T = ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
DIRS = ["l3_20261023q", "l3_20261023r"]

def runs(t, f):
    out, i, n = [], 0, len(t)
    while i < n:
        j = i
        while j + 1 < n and f[j+1] == f[i]:
            j += 1
        out.append((f[i], t[i], t[j], t[j]-t[i])); i = j+1
    return out

for d in DIRS:
    print("="*72); print("###", d)
    wins = {}
    for w in ("w0", "w1", "w2"):
        p = f"{T}\\{d}\\measure_{w}.json"
        if not os.path.isfile(p):
            print(f"  measure_{w}: 文件不存在"); continue
        x = json.load(open(p, encoding="utf-8"))
        wins[w] = x
    for w, x in wins.items():
        t, f = x["samples"]["t"], x["samples"]["f"]
        R = runs(t, f)
        segs = [r for r in R if r[3] >= 0.5]
        st = x.get("stats") or {}
        print(f"  --- {w}: verdict={x.get('verdict')} win_span={round(t[-1]-t[0],3)}s t_abs0={x.get('t_abs0')} "
              f"samples={len(t)} frame {f[0]}->{f[-1]} runs={len(R)} ≥0.5s冻结run={len(segs)}")
        if segs:
            for s in segs:
                print(f"      冻结 frame={s[0]} 起于窗内 t_rel={round(s[1]-t[0],4)}s 持续={round(s[3],4)}s")
        # 尾部持续（frame 恒等于末值的时间）
        tailhold = R[-1][3]
        print(f"      末 run frame={R[-1][0]} 持续={round(tailhold,4)}s 占窗比例={round(tailhold/(t[-1]-t[0]),4)}")
        cs = x.get("counters") or []
        if cs:
            u = [c["units"] for c in cs]; b = [c.get("b") for c in cs]; g = [c.get("g") for c in cs]
            print(f"      counters units={u}")
            print(f"      counters g={g}")
            print(f"      counters b={b}")
            eqi = [i for i in range(1, len(u)) if u[i] == u[i-1]]
            print(f"      units 持平步 idx={eqi} 末 units={u[-1]}")
        print(f"      stats: fps_avg={st.get('fps_avg')} frame_ms_max={st.get('frame_ms_max')} max_stall_s={st.get('max_stall_s')} logic_frames={st.get('logic_frames')} tick_miss={st.get('tick_miss')} note={st.get('note')!r}")
    # 三窗绝对时间轴
    if len(wins) == 3:
        print("  三窗绝对时序（t_abs0 各窗独立基准，需用 samples.t 首值差核对）:")
        for w, x in wins.items():
            print(f"    {w}: t_abs0={x['t_abs0']} samples.t[0]={x['samples']['t'][0]} samples.t[-1]={x['samples']['t'][-1]}")

print("\n### qc151_fields.json 回读（终局/胜负/单位计数据）")
for d in DIRS:
    x = json.load(open(f"{T}\\{d}\\qc151_fields.json", encoding="utf-8"))
    print("---", d, "type", type(x).__name__, "len", len(x) if hasattr(x, "__len__") else "")
    if isinstance(x, list):
        ks = set()
        for r in x:
            if isinstance(r, dict): ks |= set(r.keys())
        print("   字段名=", sorted(ks))
        for r in x[:4]: print("   ", json.dumps(r, ensure_ascii=False)[:260])
        for r in x[-4:]: print("   TAIL", json.dumps(r, ensure_ascii=False)[:260])

print("\n### _launch_result / carrier 残留 / 命令行长回读")
for d in DIRS:
    lr = json.load(open(f"{T}\\{d}\\_launch_result.json", encoding="utf-8"))
    print("---", d, "rc=", lr.get("rc"), "duration_s=", lr.get("duration_s"), "carriers_deleted=", lr.get("carriers_deleted"),
          "leftover_procs=", lr.get("leftover_procs"), "harness_sha16=", lr.get("harness_sha16"))
    print("   argv=", " ".join(lr.get("argv", []))[:700])
    cps = f"{T}\\{d}\\carrier_post_state.json"
    if os.path.isfile(cps):
        print("   carrier_post_state=", json.dumps(json.load(open(cps, encoding="utf-8")), ensure_ascii=False)[:400])
    cdr = f"{T}\\{d}\\carrier_delete_result.json"
    if os.path.isfile(cdr):
        print("   carrier_delete_result=", json.dumps(json.load(open(cdr, encoding="utf-8")), ensure_ascii=False)[:400])
