# -*- coding: utf-8 -*-
"""M71 final verification: intersection, verbatim disclosure, panel numbers, coverage counts, no flip."""
import csv, os, re, sys, math, collections, hashlib
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PROJ = r"D:\Project\ra2-campaign-forge"
COV  = os.path.join(ROOT,"COVERAGE","coverage.tsv")
PANEL= os.path.join(ROOT,"COVERAGE","PANEL.md")
CARD = os.path.join(ROOT,"_cards","M71-MERGE.md")
ATLAS= os.path.join(PROJ,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
VERD = os.path.join(ROOT,"NAMED_PUSH_AUDIT12","verdict.tsv")
DELTA= os.path.join(ROOT,"NAMED_PUSH_S22_B4","delta.tsv")
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

EXPECT=["006C5210","006C5390","006C5510","006C5690","006C5810",
        "006C5990","006C5B10","006C5C90","006C5E10","006C5F90","006C6110"]

# 0. intersection == 11 and all PASS, B5 empty
vd=[r for r in list(csv.reader(open(VERD,encoding="utf-8-sig",newline=""),delimiter="\t"))[1:] if r and any(c.strip() for c in r)]
dl=[r for r in list(csv.reader(open(DELTA,encoding="utf-8-sig",newline=""),delimiter="\t"))[1:] if r and any(c.strip() for c in r)]
a_set=set(ne(r[0]) for r in vd); d_set=set(ne(r[0]) for r in dl)
chk(len(a_set)==11 and len(d_set)==11, "audit 11 + delta 11 rows")
chk(a_set==d_set==set(EXPECT), "intersection exactly 11 expected entries")
chk(all(r[2].strip()=="PASS" for r in vd), "all 11 audit verdicts PASS")
b5=os.path.join(ROOT,"NAMED_PUSH_S22_B5","delta.tsv")
b5rows=[r for r in list(csv.reader(open(b5,encoding="utf-8-sig",newline=""),delimiter="\t"))[1:] if r and any(c.strip() for c in r)]
chk(len(b5rows)==0, "B5 delta empty (0 data rows)")

# 1. verbatim disclosure + placement after M70
card=open(CARD,"rb").read().decode("utf-8").split("\n")
h=next(i for i,l in enumerate(card) if "必须追加的第三条披露" in l)
f1=next(i for i in range(h,len(card)) if card[i].strip()=="```")
f2=next(i for i in range(f1+1,len(card)) if card[i].strip()=="```")
disc=card[f1+1:f2]
pan=open(PANEL,"rb").read().decode("utf-8").split("\n")
idx=[i for i,l in enumerate(pan) if l.startswith("> ⚠️ **M71 披露：")]
chk(len(idx)==1, "PANEL has exactly one M71 disclosure start line")
i0=idx[0]
block=pan[i0:i0+len(disc)]
chk(block==disc, "M71 disclosure block verbatim-identical to card fenced lines")
m70_last="> ⇒ 引用这批行时，不得表述为「该工厂函数被外部调用并检查其返回码」。"
chk(i0>0 and pan[i0-1]==m70_last, "M71 disclosure immediately after M70 disclosure last line")
print("M71 disclosure 1-based start line:", i0+1, "end line:", i0+len(disc), "count:", len(disc))

# 2. panel numeric/remark edits
ptext="\n".join(pan)
for s in ["| **1,602 / 1,596** |",
          "M71 并表 NAMED_PUSH_AUDIT12 PASS 11 行（S22_B4 工厂族）；S22 named 池至此清空（B1 18 + B2 18 + B3 13 + B4 13 + B5 9 = 71 = 全池），B5 的 9 行 vector 族四环齐全 0（③b 全败于 {0,1} AL 布尔）",
          "| S22 | 4851 | 1759 | 36.26 | 1759 | 36.26 | 34 | 0.70 | 109 | 2.25 |",
          "| **TOTAL** | **12,916** | **7210** | **55.82** | **7203** | **55.77** | **1372** | **10.62** | **1596** | **12.36** |",
          "| S22 | 4851 | 109 | 2.25 | **66** | **1.36** | 2426 | — | — |",
          "| **TOTAL** | **12916** | **1596** | **12.36** | **1279** | **9.90** | — | **3/22** | **1/22** |"]:
    chk(ptext.count(s)>=1, "PANEL contains: "+s[:55])
chk("| **1,591 / 1,585** |" not in ptext, "old 全表/atlas cell gone")
chk("| S22 | 4851 | 98 | 2.02 | **55** | **1.13** | 2426" not in ptext, "old S22 strict row gone")
chk("| **TOTAL** | **12916** | **1585** | **12.27** | **1268** | **9.82**" not in ptext, "old TOTAL strict row gone")

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
chk(full==1602, "full [已证] = 1602")
chk(ain==1596, "atlas-in [已证] = 1596")
chk(aout==6, "atlas-out [已证] = 6")

# 11 rows check cols
sem={}
with open(DELTA,encoding="utf-8-sig",newline="") as f:
    for r in list(csv.reader(f,delimiter="\t"))[1:]:
        sem[ne(r[0])]=r[3]
byent=collections.defaultdict(list)
for r in data: byent[ne(r[0])].append(r)
all_ok=True
for e in EXPECT:
    rows=byent.get(e,[])
    if len(rows)!=1: all_ok=False; continue
    r=rows[0]
    if not (r[3]==sem[e] and r[4].strip()=="[已证]" and r[5].strip()=="NAMED_PUSH_AUDIT12/VERDICT.md"):
        all_ok=False
    if ne(r[0]) not in atlas: all_ok=False
chk(all_ok, "11 entries: col4=delta verbatim, col5=[已证], col6=NAMED_PUSH_AUDIT12/VERDICT.md, all atlas-in")

# 4. no flip (strict口径 = 带方括号字面 [未证])
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
chk(d["S22"]["proved"]==109 and d["S22"]["strict"]==66, "S22 proved=109 strict=66")
tot=collections.Counter()
for s in d:
    for k in ("proved","strict"): tot[k]+=d[s][k]
chk(tot["proved"]==1596 and tot["strict"]==1279, "TOTAL atlas-in proved=1596 strict=1279")

print("\nOVERALL:", "ALL PASS" if ok else "SOME FAILED")
