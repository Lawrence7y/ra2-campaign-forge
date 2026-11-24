# -*- coding: utf-8 -*-
"""Independent re-run of the score decomposition, paired stats, and GP-A1 tracing.
Verification-only: reads protected directories, writes nothing outside this file.
Run: python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/score_decomp_20261109/_sdv_recheck.py
"""
import os, json, math, random
from fractions import Fraction
from collections import Counter
import importlib.util

R = r"D:\Project\ra2-campaign-forge"
GP = os.path.join(R, "lead", "gate_pipeline_20261109")
V12 = os.path.join(R, "lead", "gate_v1v2_20261109")

A = json.load(open(os.path.join(GP, "_gp_regression_out.json"), encoding="utf-8"))
B = json.load(open(os.path.join(GP, "_gp_regression_v1_union_out.json"), encoding="utf-8"))
ra = {r["id"]: r for r in A["rows"]}
rb = {r["id"]: r for r in B["rows"]}
idsA, idsB = set(ra), set(rb)
common = idsA & idsB
onlyA, onlyB = idsA - idsB, idsB - idsA

def s(rows, ids, key="chain"):
    return sum(1 for i in ids if rows[i][key] == rows[i]["expect"])

print("== PART 1: id sets / total ==")
print("nA", len(idsA), "nB", len(idsB), "common", len(common))
print("onlyA", sorted(onlyA), "onlyB", sorted(onlyB))
print("chainA", s(ra, idsA), "/", len(idsA), " chainB", s(rb, idsB), "/", len(idsB))
print("total delta", s(ra, idsA) - s(rb, idsB))

print("== PART 2: flips & frozen ==")
flips = sorted(i for i in common if ra[i]["expect"] != rb[i]["expect"])
print("flips", len(flips), [(i, rb[i]["expect"], ra[i]["expect"]) for i in flips])
F = common - set(flips)
print("n_frozen", len(F))
print("frozen: chain72", s(rb, F), "chain74", s(ra, F), "delta", s(ra, F) - s(rb, F))
print("flips: chain72", s(rb, set(flips)), "chain74", s(ra, set(flips)), "delta", s(ra, set(flips)) - s(rb, set(flips)))
print("new3: s74", s(ra, onlyA), "deleted1: s72", s(rb, onlyB))
print("check", (s(ra, F)-s(rb, F)) + (s(ra,set(flips))-s(rb,set(flips))) + s(ra,onlyA) + (-s(rb,onlyB)))

print("== PART 3: per-row +1 attribution ==")
gains = sorted(i for i in F if (ra[i]["chain"] == ra[i]["expect"]) and (rb[i]["chain"] != rb[i]["expect"]))
losses = sorted(i for i in F if (rb[i]["chain"] == rb[i]["expect"]) and (ra[i]["chain"] != ra[i]["expect"]))
print("gains", len(gains), gains)
print("losses", len(losses), losses)
for i in gains:
    assert rb[i]["chain"] == "CATCH" and rb[i]["expect"] == "PASS"
    assert ra[i]["chain"] == "PASS" and ra[i]["expect"] == "PASS"
print("all gains 72:CATCH/expect=PASS -> 74:PASS/expect=PASS? True")
for i in flips:
    print("flip row", i, "72", rb[i]["expect"], rb[i]["chain"], "-> 74", ra[i]["expect"], ra[i]["chain"])
judge_cols = ["naive","r10","r12","n13","chain","layer_conflicts","layer_unresolved"]
print("flip judge cols identical both versions?", all(all(rb[i][c]==ra[i][c] for c in judge_cols) for i in flips))
for i in sorted(onlyA):
    print("new", i, "expect", ra[i]["expect"], "chain", ra[i]["chain"], "correct", ra[i]["chain"]==ra[i]["expect"], "|", ra[i]["text_head"])
for i in sorted(onlyB):
    print("deleted", i, "expect", rb[i]["expect"], "chain", rb[i]["chain"], "correct", rb[i]["chain"]==rb[i]["expect"], "|", rb[i]["text_head"])
print("GP-C03 vs GP-A1 text_head equal?", rb["GP-C03"]["text_head"] == ra["GP-A1"]["text_head"])
ka = {k:v for k,v in ra["GP-A1"].items() if k not in ("id","family","note")}
kb = {k:v for k,v in rb["GP-C03"].items() if k not in ("id","family","note")}
print("GP-C03 vs GP-A1 except id/family/note identical?", ka == kb)
print("family", rb["GP-C03"]["family"], "->", ra["GP-A1"]["family"])

print("== PART 4: paired b/c + exact binomial + CP/Wilson CI ==")
b = sum(1 for i in F if rb[i]["chain"]!=rb[i]["expect"] and ra[i]["chain"]==ra[i]["expect"])
c = sum(1 for i in F if rb[i]["chain"]==rb[i]["expect"] and ra[i]["chain"]!=ra[i]["expect"])
n = b+c
print("frozen n=",len(F),"b=",b,"c=",c,"n_discordant=",n)
p_two = float(2*sum(Fraction(math.comb(n,k),2**n) for k in range(0,min(b,c)+1)))
print("p_two_sided_exact (small-p method) =", p_two, "= 2*2^-18 =", 2*2**-18)
print("p_one_sided =", 2**-18)
# Clopper-Pearson lower: find p_low such that P(X>=b | p_low) = alpha/2
import math as _m
def sf(k, n_, p):
    return sum(_m.comb(n_,j)*p**j*(1-p)**(n_-j) for j in range(k,n_+1))
lo, hi = 0.0, 1.0
for _ in range(200):
    mid=(lo+hi)/2
    if sf(b,n,mid) < 0.025: lo=mid
    else: hi=mid
cp_lo=(lo+hi)/2
print("Clopper-Pearson 95% CI lower =", cp_lo, "upper = 1.0", "sf(b,p_low)=", sf(b,n,cp_lo))
z=1.959963984540054
p_hat=b/n
wil_lo=(p_hat+z*z/(2*n)-z*_m.sqrt(p_hat*(1-p_hat)/n+z*z/(4*n*n)))/(1+z*z/n)
print("Wilson 95% CI =", wil_lo, 1.0)
print("paired acc diff =", b/len(F))
# bootstrap 200000 pairs, seed=20261109 (paired resample of 68 rows of per-row deltas)
deltas=[]
for i in F:
    deltas.append((1 if ra[i]["chain"]==ra[i]["expect"] else 0)-(1 if rb[i]["chain"]==rb[i]["expect"] else 0))
rng=random.Random(20261109)
N=200000
means=[]
for _ in range(N):
    tot=0
    for _ in range(len(F)):
        tot+=deltas[rng.randrange(len(F))]
    means.append(tot/len(F))
means.sort()
print("bootstrap 200000 percentile 95% CI =", means[int(0.025*N)], means[int(0.975*N)-1])
print("normal SE =", _m.sqrt((sum(1 for i in F if deltas[list(F).index(i)]!=0)- (b/len(F))**2*len(F))/(len(F)-1)/len(F)) if False else "see below")
# exact SE of paired difference: var of delta / n ; delta in {-1,0,1}, 18 ones, 50 zeros
var = ((b*1 + (len(F)-b)*0) - 0)/len(F)  # placeholder
mean_d = b/len(F)
ss = sum((d-mean_d)**2 for d in deltas)
se = _m.sqrt(ss/(len(F)-1)/len(F))
print("normal SE (empirical) =", se)

print("== PART 5: pp decomposition & corrected baseline ==")
pp = 100*(s(ra,idsA)/len(idsA) - s(rb,idsB)/len(idsB))
num_eff = 100*(s(ra,idsA)-s(rb,idsB))/len(idsB)
dil = 100*s(ra,idsA)*(len(idsA)-len(idsB))/(len(idsB)*len(idsA))
print("pp delta", pp, "=", num_eff, "-", dil, "=", num_eff-dil)
print("72 corrected", s(rb,idsB)+3,"/",len(idsB),"=",100*(s(rb,idsB)+3)/len(idsB),"%")
print("74", s(ra,idsA),"/",len(idsA),"=",100*s(ra,idsA)/len(idsA),"%")
print("corrected raw delta", s(ra,idsA)-(s(rb,idsB)+3), "pp=", 100*(s(ra,idsA)/len(idsA)-(s(rb,idsB)+3)/len(idsB)))

print("== PART 6: duplicate texts / families / FP breakdown ==")
texts=[ra[i]["text_head"] for i in gains]
print("unique text_head among 18 =", len(set(texts)), "of", len(gains))
print("family Counter =", dict(Counter(ra[i]["family"] for i in gains)))
fp72=[i for i in F if rb[i]["chain"]=="CATCH" and rb[i]["expect"]=="PASS"]
print("72 FP in frozen =", len(fp72), "repaired by 74 =", sum(1 for i in fp72 if ra[i]["chain"]=="PASS"), "still FP =", sum(1 for i in fp72 if ra[i]["chain"]!="PASS"))
print("still-FP ids", sorted(i for i in fp72 if ra[i]["chain"]!="PASS"))
print("74 layer_unresolved on gains total =", sum(ra[i]["layer_unresolved"] for i in gains), "max =", max(ra[i]["layer_unresolved"] for i in gains))
print("72 layer_unresolved on gains total =", sum(rb[i]["layer_unresolved"] for i in gains))
print("74 rows with layer_unresolved>0 =", [r["id"] for r in A["rows"] if r["layer_unresolved"]>0])
print("72 rows with layer_unresolved>0 count =", sum(1 for r in B["rows"] if r["layer_unresolved"]>0))
print("74 chain_conflicts_total =", A["chain_conflicts_total"], "72 =", B["chain_conflicts_total"])
print("74 chain_unresolved_total =", A["chain_unresolved_total"], "72 =", B["chain_unresolved_total"])
print("CATCH recall frozen 72 =", sum(1 for i in F if rb[i]["expect"]=="CATCH" and rb[i]["chain"]=="CATCH"), "/", sum(1 for i in F if rb[i]["expect"]=="CATCH"))
print("CATCH recall frozen 74 =", sum(1 for i in F if ra[i]["expect"]=="CATCH" and ra[i]["chain"]=="CATCH"), "/", sum(1 for i in F if ra[i]["expect"]=="CATCH"))
print("n13 correct frozen 74 =", sum(1 for i in F if ra[i]["n13"]==ra[i]["expect"]), "chain =", s(ra,F))
print("n13 correct frozen 72 =", sum(1 for i in F if rb[i]["n13"]==rb[i]["expect"]), "chain =", s(rb,F))

print("== PART 7: GP-A1 / GP-C03 source tracing ==")
for tag,rows,i in [("74 GP-A1",ra,"GP-A1"),("72 GP-C03",rb,"GP-C03")]:
    r=rows[i]
    print(tag, "expect",r["expect"],"chain",r["chain"],"naive",r["naive"],"r10",r["r10"],"r12",r["r12"],"n13",r["n13"],"|", r["text_head"])

# --- load _v12_rule.py and classify_v12 ---
def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
v12=load(os.path.join(V12,"_v12_rule.py"), "_sdv_v12")
text=ra["GP-A1"]["text_head"]
tok="已生效"
pos=text.find(tok)
print("classify_v12 args text=",repr(text),"start=",pos,"end=",pos+len(tok),"token=",repr(tok))
print("classify_v12 output =", json.dumps(v12.classify_v12(text,pos,pos+len(tok),tok),ensure_ascii=False))

# --- load pipeline and replay GP-A1 chain (74) ---
P=load(os.path.join(GP,"_gp_pipeline.py"), "_sdv_gp_pipe")
g7,n13,n13_tokens=P.load_predicates()
print("n13_tokens =", n13_tokens)
print("g7.r10_context =", g7.r10_context(text,ra["GP-A1"]["tokens"]))
print("g7.r12_scan =", g7.r12_scan(text,ra["GP-A1"]["tokens"]))
print("n13.r13_assertions =", n13.r13_assertions(text,n13_tokens,r10_context=g7.r10_context,r12_scan=g7.r12_scan))
print("P.gate_check =", json.dumps(P.gate_check(text,ra["GP-A1"]["tokens"],os.path.join(GP,"."),g7,n13,n13_tokens),ensure_ascii=False,default=str)[:4000])
rows,conflicts,summary=P.resolve_conflicts(text,ra["GP-A1"]["tokens"],P.run_layers(g7,n13,n13_tokens,text,ra["GP-A1"]["tokens"],os.path.join(GP,".")),n13_tokens)
print("resolve_conflicts rows =", json.dumps(rows,ensure_ascii=False))
print("resolve_conflicts summary =", summary)

# --- replay 3 gain rows to locate K3+K9 ---
for gid in ["N13-P01","R10-CTX-07","REAL-BOUND"]:
    r=ra[gid]
    layers=P.run_layers(g7,n13,n13_tokens,r["text_head"],r["tokens"],os.path.join(GP,"."))
    rr,cc,ss=P.resolve_conflicts(r["text_head"],r["tokens"],layers,n13_tokens)
    print("GAIN",gid,"text=",r["text_head"],"rules=",[(x["token"],x["rules"],x["verdict"],x.get("n13_kind"),x.get("n13_veto")) for x in rr],"summary=",ss)

print("== PART 8: 3-family sign test / design effect ==")
print("p 3-family sign test =", 2*2**-3)
print("p 16 independent texts =", 2*2**-16)
for rho in [0,0.3,0.5,0.8,0.9,1.0]:
    print("rho",rho,"n_eff",18/(1+(18-1)*rho))
print("Bonferroni 0.05/p =", 0.05/p_two)
print("DONE")
