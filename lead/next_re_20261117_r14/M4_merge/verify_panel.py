# M4 — independent verification: parse final PANEL.md and check per-S arithmetic recomputable
import os, re
R14=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PANEL=os.path.join(R14,"COVERAGE","PANEL.md")
with open(PANEL,"r",encoding="utf-8",newline="") as f: txt=f.read()
lines=[l[:-1] if l.endswith("\r") else l for l in txt.split("\n")]

rows=[]
for l in lines:
    fs=[x.strip() for x in l.split("|")]
    if len(fs)>=10 and fs[1] in [f"S{i:02d}" for i in range(1,23)]:
        def num(s): return int(re.sub(r"[^0-9]","",s)) if re.sub(r"[^0-9]","",s) else 0
        def flt(s): return float(re.sub(r"[^0-9.]","",s)) if re.sub(r"[^0-9.]","",s) else 0.0
        rows.append((fs[1],num(fs[2]),num(fs[3]),flt(fs[4]),flt(fs[5]),num(fs[6]),flt(fs[7]),num(fs[8])))
print("parsed rows:",len(rows))
assert len(rows)==22

# classsub counts derived independently from documented note (S05 1 / S06 1 / S19 6 = 8 total)
classsub={"S05":1,"S06":1,"S19":6}
ok=0; bad=[]
print("S\tatlas_n\tnamed_n\tproved_n\tpctL_calc\tpctL_tbl\tpctS_calc\tpctS_tbl\tpctP_calc\tpctP_tbl")
for s,aN,nN,pL,pS,pN,pP,dN in rows:
    calcL=round(nN/aN*100,2)
    calcS=round((nN-classsub.get(s,0))/aN*100,2)
    calcP=round(pN/aN*100,2)
    good=(calcL==pL and calcS==pS and calcP==pP)
    if good: ok+=1
    else: bad.append((s,calcL,pL,calcS,pS,calcP,pP))
    print(f"{s}\t{aN}\t{nN}\t{pN}\t{calcL}\t{pL}\t{calcS}\t{pS}\t{calcP}\t{pP}\t{'OK' if good else 'BAD'}")
print(f"\nrecompute OK: {ok}/22; bad: {bad}")
assert ok==22
# totals
tN=sum(r[1] for r in rows); tNamed=sum(r[2] for r in rows); tProv=sum(r[5] for r in rows)
print(f"TOTAL atlas_n={tN} named_n={tNamed} proved_n={tProv} | pctL={tNamed/tN*100:.2f} pctP={tProv/tN*100:.2f}")
assert tN==12916
print("\nALL PANEL PERCENTAGES RECOMPUTABLE FROM TABLE.")
