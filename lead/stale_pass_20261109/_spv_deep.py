"""⑤ 重跑方案可执行性 + ③ 裁决不依赖的机械证据 + ⑥ 根因引用件有界定位。"""
import os, re, subprocess, sys, hashlib

ROOT = "D:/Project/ra2-campaign-forge"
W = ROOT + "/lead/stale_pass_20261109/"

print("=== ③ 三件裁决正文里是否出现 check_d*.py / exit=0 / 门禁 PASS 字样 ===")
for k, p in [("R27","lead/d27_ruling_20261106/RULING_D27.md"),
             ("R28","lead/d28_ruling_20261106/RULING_D28.md"),
             ("R29","lead/d29_ruling_20261106/RULING_D29.md"),
             ("R30","lead/d30_ruling_20261106/RULING_D30.md")]:
    t = open(os.path.join(ROOT,p),"rb").read().decode("utf-8","replace")
    L = t.split("\n")
    print(f"-- {k} lines={len(L)} --")
    for term in ["check_d27.py","check_d28.py","check_d29.py","check_d30.py",
                 "check_stall_def.py","check_feasibility.py","exit=0","门禁","PASS","实跑"]:
        hits=[i+1 for i,s in enumerate(L) if term in s]
        print(f"   {term!r:24s} count={len(hits):3d} lines={hits[:25]}")
    for i,s in enumerate(L):
        if "门禁" in s or "exit=0" in s:
            print(f"      L{i+1}: {s.strip()[:230]}")

print()
print("=== ③ 定谳行与依据行（逐字） ===")
for k,p,ns in [("R27","lead/d27_ruling_20261106/RULING_D27.md",[3,6,12,58,69,75,77]),
               ("R29","lead/d29_ruling_20261106/RULING_D29.md",[4,6,10,14,18,67,71]),
               ("R30","lead/d30_ruling_20261106/RULING_D30.md",[4,6,20,62,76])]:
    L=open(os.path.join(ROOT,p),"rb").read().decode("utf-8","replace").split("\n")
    print(f"-- {k} --")
    for n in ns:
        print(f"   L{n}: {L[n-1].strip()[:260]}")

print()
print("=== ⑥ 根因引用件有界定位（只在 lead/ 下按目录名找，不做全库 glob） ===")
targets = ["_nn_REPORT.md","NEEDLE_NORMALIZATION.md","_cm_AUDIT.md","_me_design.py",
           "_mev_final_out.txt","_me_auditcheck_plan2.py","_cm_AUDIT.md"]
found = {}
for dp, dn, fs in os.walk(ROOT + "/lead"):
    # 有界：跳过明显大目录 / 深度>4
    rel = dp[len(ROOT):].replace("\\","/")
    if rel.count("/") > 4:
        dn[:] = []
        continue
    for t in targets:
        if t in fs and t not in found:
            found[t] = os.path.join(dp, t)
for t in targets:
    print(f"   {t}: {found.get(t,'NOT FOUND in bounded walk')}")
    p = found.get(t)
    if p and t.endswith(".md"):
        L = open(p,"rb").read().decode("utf-8","replace").split("\n")
        for n in [364,365,402]:
            if n <= len(L):
                print(f"      {t}:{n}: {L[n-1].strip()[:200]}")

print()
print("=== ⑤ 报告所引 scanner 单跑输出行号核对 ===")
for fn, rng in [("_sp_agg_f0b7c1.txt",(570,585)),("_sp_agg_87196b.txt",(650,665)),
                ("_sp_rs_broken_out.txt",(1,12)),("_sp_rs_broken_out.txt",(715,728))]:
    p = os.path.join(W,fn)
    L = open(p,"rb").read().decode("utf-8","replace").split("\n")
    print(f"-- {fn} L{rng[0]}-{rng[1]} (total={len(L)}) --")
    for n in range(rng[0], min(rng[1],len(L))+1):
        s=L[n-1]
        print(f"   L{n}: {s.strip()[:230]}")
