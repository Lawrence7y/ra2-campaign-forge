# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
import capstone, pefile, struct, bisect, json, random
from collections import defaultdict
P=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
COV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATLAS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11_DIRECT\work"
pe=pefile.PE(P); data=open(P,"rb").read()
sec=[s for s in pe.sections if s.Name.rstrip(b"\x00")==b".text"][0]
BASE=pe.OPTIONAL_HEADER.ImageBase+sec.VirtualAddress; NB=sec.Misc_VirtualSize
code=data[sec.PointerToRawData:sec.PointerToRawData+NB]
TEXT_END=BASE+NB
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
boundary=set(); tmap=defaultdict(list)
for ins in md.disasm(code,BASE):
    boundary.add(ins.address)
    off=ins.address-BASE
    if 0<=off<len(code)-4 and code[off]==0xE8 and ins.mnemonic=="call" and ins.size==5:
        rel=struct.unpack_from("<i",code,off+1)[0]
        tmap[ins.address+5+rel].append(ins.address)
raw_e8=[]
for off in range(len(code)-4):
    if code[off]==0xE8:
        rel=struct.unpack_from("<i",code,off+1)[0]
        raw_e8.append((BASE+off, BASE+off+5+rel))
grade={}; name={}; sem={}; evid={}; conf={}; sub={}
for line in open(COV,encoding="utf8").read().splitlines()[1:]:
    if not line.strip(): continue
    c=line.split("\t")
    if len(c)<8: continue
    e=c[0].strip().upper()
    grade[e]=c[4].strip(); name[e]=c[2].strip(); sem[e]=c[3].strip(); evid[e]=c[5].strip(); conf[e]=c[7].strip(); sub[e]=c[1].strip().upper()
at={}
for line in open(ATLAS,encoding="utf8").read().splitlines()[1:]:
    if not line.strip(): continue
    c=line.split("\t"); at[c[0].strip().upper()]=(int(c[1]),int(c[0],16))
fn_list=sorted([(eiv,sz,e) for e,(sz,eiv) in at.items()]); fne=[x[0] for x in fn_list]
def caller_of(site):
    i=bisect.bisect_right(fne,site)-1
    best=None
    for j in range(i,max(-1,i-40),-1):
        eiv,sz,eh=fn_list[j]
        if site<eiv+sz:
            if best is None or sz<best[1]: best=(eh,sz,eiv)
    return best
s11_targets=[e for e in at if sub.get(e)=="S11" and grade.get(e) in ("[静态推断]","[未证]")]
print("s11 non-proven in atlas:",len(s11_targets))
results=[]
for e in s11_targets:
    eiv=int(e,16); sz=at[e][0]; body_end=eiv+sz
    sites=tmap.get(eiv,[])
    good=[]
    for s in sites:
        if s not in boundary: continue
        if not (BASE<=s<TEXT_END): continue
        caller=caller_of(s)
        if caller:
            ceh,csz,ceiv=caller
            if ceiv<=eiv<ceiv+csz: continue
            caller_desc=ceh; caller_grade=grade.get(ceh,"?")
        else:
            if eiv<=s<body_end: continue
            caller_desc="UNKNOWN"; caller_grade="?"
        good.append((s,caller_desc,caller_grade))
    if good:
        results.append((e,grade[e],name[e],sem[e],evid[e],conf[e],good))
results.sort()
print("QUALIFYING ROWS:",len(results))
for r in results:
    print(r[0],r[1],"nsites",len(r[6]),"caller_grades",sorted(set(x[2] for x in r[6])))
obj=[]
for e,g,nm,sm,ev,cf,good in results:
    obj.append({"entry":e,"old_grade":g,"name":nm,"sem":sm,"evidence":ev,"conflict":cf,
                "sites":[{"site":f"{s:08X}","caller":c,"caller_grade":cg} for s,c,cg in good]})
json.dump(obj,open(OUT+r"\qualifying.json","w",encoding="utf8"),ensure_ascii=False,indent=1)
N=len(results)
pool=[e for e in at if e not in set(r[0] for r in results)]
print("baseline N=",N,"pool",len(pool))
for seed in range(10):
    random.seed(seed)
    pick=random.sample(pool,min(N,len(pool)))
    hits=0
    for pe_entry in pick:
        eiv=int(pe_entry,16); sz=at[pe_entry][0]; body_end=eiv+sz
        for s in tmap.get(eiv,[]):
            if s not in boundary: continue
            if not(BASE<=s<TEXT_END): continue
            caller=caller_of(s)
            if caller:
                ceh,csz,ceiv=caller
                if ceiv<=eiv<ceiv+csz: continue
            else:
                if eiv<=s<body_end: continue
            hits+=1; break
    print("BASELINE seed",seed,"hits",hits,"/",N)
weak_hits=0; strong_hits=0; weak_only=[]
strong_set=set(r[0] for r in results)
for e in s11_targets:
    eiv=int(e,16)
    has_strong=(e in strong_set)
    has_weak=any(t==eiv for s,t in raw_e8)
    if has_weak: weak_hits+=1
    if has_strong: strong_hits+=1
    if has_weak and not has_strong: weak_only.append(e)
print("DIFF weak_hits",weak_hits,"strong_hits",strong_hits,"weak_only",len(weak_only))
json.dump({"weak_hits":weak_hits,"strong_hits":strong_hits,"weak_only":weak_only},open(OUT+r"\differential.json","w",encoding="utf8"))