"""④ 影响面具体化：扫 PENDING/GOAL 里所有 RULING_DNN.md 引用行；⑤ agg 单跑口径核对。"""
import os, re

ROOT = "D:/Project/ra2-campaign-forge"
W = ROOT + "/lead/stale_pass_20261109/"
P = open(os.path.join(ROOT,"lead/PENDING_DECISIONS.md"),"rb").read().decode("utf-8","replace").split("\n")
G = open(os.path.join(ROOT,"lead/GOAL_THREE_TARGETS_20261018.md"),"rb").read().decode("utf-8","replace").split("\n")

print("=== ④ PENDING/GOAL 中 D-27/D-28/D-29/D-30 与 RULING_DNN 的逐行引用 ===")
for tag, L in [("PENDING",P),("GOAL",G)]:
    print(f"-- {tag} lines={len(L)} --")
    for term in ["D-27","D-28","D-29","D-30","RULING_D27.md","RULING_D28.md",
                 "RULING_D29.md","RULING_D30.md","GOAL mentions"]:
        hits=[(i+1, s.strip()[:200]) for i,s in enumerate(L) if term in s]
        print(f"   {term!r:20s} count={len(hits)}")
        for n,s in hits[:12]:
            print(f"      L{n}: {s}")
    print()

print("=== ④ 关键：PENDING:90-101（D-30 条目）与 PENDING:103-113（D-29）证据行逐字 ===")
for n in list(range(90,102))+list(range(103,114)):
    if n<=len(P): print(f"   PENDING:{n}: {P[n-1].strip()[:260]}")

print()
print("=== ④ RULING_D30.md 里所有引用 RULING_D29.md / RULING_D28.md 的行 ===")
r30=open(os.path.join(ROOT,"lead/d30_ruling_20261106/RULING_D30.md"),"rb").read().decode("utf-8","replace").split("\n")
for i,s in enumerate(r30):
    if "RULING_D29.md" in s or "RULING_D28.md" in s:
        print(f"   R30:{i+1}: {s.strip()[:280]}")
print("=== ④ RULING_D29.md 里所有引用 RULING_D28.md 的行 ===")
r29=open(os.path.join(ROOT,"lead/d29_ruling_20261106/RULING_D29.md"),"rb").read().decode("utf-8","replace").split("\n")
for i,s in enumerate(r29):
    if "RULING_D28.md" in s:
        print(f"   R29:{i+1}: {s.strip()[:300]}")

print()
print("=== ⑤ agg 单跑 / 坏针输出头部口径（逐字） ===")
for fn in ["_sp_agg_f0b7c1.txt","_sp_agg_87196b.txt","_sp_rs_broken_out.txt"]:
    L=open(os.path.join(W,fn),"rb").read().decode("utf-8","replace").split("\n")
    print(f"-- {fn} L1-12 --")
    for n in range(1,13):
        if n<=len(L): print(f"   L{n}: {L[n-1].strip()[:230]}")
print()
print("=== ⑤ MASKING_EFFECT_AUDIT.md:229-231 可粘贴片段实际参数 ===")
M=open(os.path.join(ROOT,"lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md"),"rb").read().decode("utf-8","replace").split("\n")
for n in range(229,232): print(f"   MEA:{n}: {M[n-1]}")
print("=== REFSYNC_SCOPE_FIX.md:251 登记命令（口径） ===")
F=open(os.path.join(ROOT,"lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md"),"rb").read().decode("utf-8","replace").split("\n")
print("   FIX:251:",F[250].strip()[:400])
