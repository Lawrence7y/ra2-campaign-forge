# -*- coding: utf-8 -*-
"""S13-PUSH Step 2: 两通道基础率筛选（诚实报数）。
对 work/pool.json 每个候选跑通道A(③b②)与通道B(③b①)，输出 work/screen.json：
每行 entry / grade / name / channelA(p1,p2,p3,sites) / channelB(tables) / 命中标志。
基础率 = 池大小 / 通道A命中 / 通道B命中 / 两通道合计可辩护行数(去重)。
"""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

WORK = os.path.dirname(os.path.abspath(__file__))
pool = json.load(open(os.path.join(WORK, "pool.json"), encoding="utf-8"))

results = []
for p in pool:
    ea = int(p["entry"], 16)
    insns = R.disasm_body(ea, p["atlas_size"])
    A = R.channel_screen_A(insns)
    B = R.channel_screen_B(insns)
    results.append({
        "entry": p["entry"], "grade": p["grade"], "name": p["name"],
        "semantics": p["semantics"], "atlas_size": p["atlas_size"],
        "n_insn": len(insns),
        "A_hit": A["p3"] > 0, "A_p1": A["p1"], "A_p2": A["p2"], "A_p3": A["p3"],
        "A_sites": A["sites"],
        "B_hit": any(len(t["targets"]) >= 2 for t in B),
        "B_tables": B,
    })

json.dump(results, open(os.path.join(WORK, "screen.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

pool_n = len(results)
a_hit = [r for r in results if r["A_hit"]]
b_hit = [r for r in results if r["B_hit"]]
union = [r for r in results if r["A_hit"] or r["B_hit"]]
both = [r for r in results if r["A_hit"] and r["B_hit"]]

print("POOL =", pool_n)
print("CHANNEL A (③b② falsifiable return) hits =", len(a_hit), "rate=%.4f" % (len(a_hit)/pool_n))
print("CHANNEL B (③b① jump table) hits =", len(b_hit), "rate=%.4f" % (len(b_hit)/pool_n))
print("UNION (A or B) =", len(union), "rate=%.4f" % (len(union)/pool_n))
print("BOTH =", len(both))
print("")
print("A hits:", " ".join(r["entry"] for r in a_hit))
print("B hits:", " ".join(r["entry"] for r in b_hit))
print("")
print("A hit by grade:", dict(collections.Counter(r["grade"] for r in a_hit)))
print("B hit by grade:", dict(collections.Counter(r["grade"] for r in b_hit)))
