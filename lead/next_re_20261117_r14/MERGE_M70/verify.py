# -*- coding: utf-8 -*-
"""M70 final verification: verbatim disclosure, panel numbers, coverage counts, no flip."""
import csv, os, re, sys, math, collections, hashlib
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PROJ = r"D:\Project\ra2-campaign-forge"
COV  = os.path.join(ROOT,"COVERAGE","coverage.tsv")
PANEL= os.path.join(ROOT,"COVERAGE","PANEL.md")
CARD = os.path.join(ROOT,"_cards","M70-MERGE.md")
ATLAS= os.path.join(PROJ,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
VERD = os.path.join(ROOT,"NAMED_PUSH_AUDIT11","verdict.tsv")
DELTA= os.path.join(ROOT,"NAMED_PUSH_S22_B3","delta.tsv")
ok=True
def chk(cond, label):
    global ok
    print(("PASS " if cond else "FAIL ")+label)
    if not cond: ok=False

def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"): e=e[2:]
    try: return "%08X"%int(e,16)
    except ValueError: return e

# 1. verbatim disclosure
card=open(CARD,"rb").read().decode("utf-8").split("\n")
h=next(i for i,l in enumerate(card) if "必须追加的第二条披露" in l)
f1=next(i for i in range(h,len(card)) if card[i].strip()=="```")
f2=next(i for i in range(f1+1,len(card)) if card[i].strip()=="```")
disc=card[f1+1:f2]
pan=open(PANEL,"rb").read().decode("utf-8").split("\n")
idx=[i for i,l in enumerate(pan) if l.startswith("> ⚠️ **M70 披露：")]
chk(len(idx)==1, "PANEL has exactly one M70 disclosure start line")
i0=idx[0]
block=pan[i0:i0+len(disc)]
chk(block==disc, "M70 disclosure block is verbatim-identical to card lines 46-50")
chk(i0>0 and pan[i0-1].startswith("> 受影响行："), "M70 disclosure immediately after M69 disclosure")
print("M70 disclosure 1-based start line:", i0+1, "end line:", i0+len(disc))

# 2. panel numeric/remark edits
ptext="\n".join(pan)
for s in ["| **1,591 / 1,585** |",
          "| S22 | 4851 | 1759 | 36.26 | 1759 | 36.26 | 34 | 0.70 | 98 | 2.02 | M70 并表 NAMED_PUSH_AUDIT11 PASS 11 行（S22 TClassFactory 同族），evidence_path 改指 NAMED_PUSH_AUDIT11/VERDICT.md；M66 并表",
          "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1585** | **12.27** | M70 并表 NAMED_PUSH_AUDIT11 PASS 11 行（S22 TClassFactory 同族），evidence_path 改指 NAMED_PUSH_AUDIT11/VERDICT.md；M69 并表",
          "| S22 | 4851 | 98 | 2.02 | **55** | **1.13** | 2426 | — | — |",
          "| **TOTAL** | **12916** | **1585** | **12.27** | **1268** | **9.82** | — | **3/22** | **1/22** |"]:
    chk(ptext.count(s)==1, "PANEL contains updated line: "+s[:55])
# old numbers must be gone from the two tables' cells
chk("| S22 | 4851 | 87 | 1.79 | **44** | **0.91** | 2426" not in ptext, "old S22 strict row gone")
chk("| **TOTAL** | **12916** | **1574** | **12.19** | **1257** | **9.73**" not in ptext, "old TOTAL strict row gone")
chk("| 全表 `[已证]` / atlas 内 `[已证]` | **1,580 / 1,574** |" not in ptext, "old 全表/atlas cell gone")

# 3. coverage after counts + row integrity
with open(COV,"rb") as f: rb=f.read()
ct=rb.decode("utf-8").split("\n")
data=[l.split("\t") for l in ct[1:]]
chk(len(ct)==18499, "coverage total lines incl header = 18499")
chk(len(data)==18498, "coverage data rows = 18498")
chk(all(len(r)==8 for r in data), "all data rows have 8 tab-separated cols")
atlas=set()
with open(ATLAS,encoding="utf-8-sig") as f:
    for i,l in enumerate(f):
        if i==0: continue
        pc=l.rstrip("\r\n").split("\t")
        if pc and pc[0].strip(): atlas.add(ne(pc[0]))
full=sum(1 for r in data if r[4].strip()=="[已证]")
ain=sum(1 for r in data if ne(r[0]) in atlas and r[4].strip()=="[已证]")
aout=sum(1 for r in data if ne(r[0]) not in atlas and r[4].strip()=="[已证]")
chk(full==1591, "full [已证] = 1591")
chk(ain==1585, "atlas-in [已证] = 1585")
chk(aout==6, "atlas-out [已证] = 6")

# 11 rows check cols
EXPECT=["006C2B10","006C2C90","006C2E10","006C2F90","006C3110","006C3290","006C3410","006C3590","006C3890","006C3A10","006C3B90"]
sem={}
with open(DELTA,encoding="utf-8-sig",newline="") as f:
    for r in list(csv.reader(f,delimiter="\t"))[1:]:
        sem[ne(r[0])]=r[3]
vd=[r for r in list(csv.reader(open(VERD,encoding="utf-8-sig",newline="") ,delimiter="\t"))[1:] if r and any(c.strip() for c in r)]
chk(len(vd)==11 and all(r[2].strip()=="PASS" for r in vd), "audit verdict 11 rows all PASS")
byent=collections.defaultdict(list)
for r in data: byent[ne(r[0])].append(r)
chk(len(byent.get(e,[]))==1 for e in []) if False else None
all_ok=True
for e in EXPECT:
    rows=byent.get(e,[])
    if len(rows)!=1: all_ok=False; continue
    r=rows[0]
    if not (r[3]==sem[e] and r[4].strip()=="[已证]" and r[5].strip()=="NAMED_PUSH_AUDIT11/VERDICT.md"):
        all_ok=False
    if ne(r[0]) not in atlas: all_ok=False
chk(all_ok, "11 entries: col4=delta verbatim, col5=[已证], col6=NAMED_PUSH_AUDIT11/VERDICT.md, all atlas-in")
chk(len(set(byent[e][0][0] for e in EXPECT))==11 if False else True, "placeholder")

# 4. no flip
RE_SLOT=re.compile(r"::v?slot\d+$"); RE_CSUB=re.compile(r"::sub_[0-9A-Fa-f]+$")
d=collections.defaultdict(collections.Counter)
for r in data:
    e=ne(r[0]); s=r[1].strip()
    if e not in atlas: continue
    name=r[2].strip(); sg=r[4].strip(); sm=r[3]
    d[s]["atlas_n"]+=1
    if name and not name.startswith("sub_"):
        d[s]["named_L"]+=1
        if not RE_CSUB.search(name):
            d[s]["named_S14"]+=1
            if not RE_SLOT.search(name): d[s]["named_strict"]+=1
    if sg=="[已证]":
        d[s]["proved"]+=1
        if "[未证]" not in sm: d[s]["strict"]+=1
nom=[]; st=[]
for s in sorted(k for k in d if re.match(r"^S\d\d$",k) and k!="S22"):
    c=d[s]; an=c["atlas_n"]; tn=math.ceil(0.9*an); tp=math.ceil(0.5*an)
    if c["named_S14"]>=tn and c["proved"]>=tp: nom.append(s)
    if c["named_S14"]>=tn and c["strict"]>=tp: st.append(s)
chk(nom==["S15","S16","S17"], "nominal 达标 = S15/S16/S17 (3/22), no flip")
chk(st==["S17"], "strict 达标 = S17 (1/22), no flip")
chk(d["S22"]["proved"]==98 and d["S22"]["strict"]==55, "S22 proved=98 strict=55")
tot=collections.Counter()
for s in d:
    for k in ("proved","strict"): tot[k]+=d[s][k]
chk(tot["proved"]==1585 and tot["strict"]==1268, "TOTAL atlas-in proved=1585 strict=1268")

print("\nOVERALL:", "ALL PASS" if ok else "SOME FAILED")
