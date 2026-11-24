#!/usr/bin/env python3
# S21-DIRECT final: baseline+differential, 18 conflicts, analysis json.
import os,sys,io,json,struct,re,random
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8",errors="replace")
import pefile
ROOT=r"D:\Project\ra2-campaign-forge"
OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","S21_DIRECT")
WK=os.path.join(OUT,"work");EV=os.path.join(OUT,"EVIDENCE");EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
def norm(a):return a.upper().replace("0X","")
V=json.load(open(os.path.join(EV,"verify_direct.json"),encoding="utf-8"))["verified"]
entries=[r["entry"] for r in V]
data=open(EXE,"rb").read();pe=pefile.PE(EXE,fast_load=True);ib=pe.OPTIONAL_HEADER.ImageBase
sec=[s for s in pe.sections if s.Name.rstrip(b"\x00").decode()==".text"][0]
va=ib+sec.VirtualAddress;code=data[sec.PointerToRawData:sec.PointerToRawData+sec.SizeOfRawData]
TEXT_VA=va;TEXT_SIZE=len(code)
targets=set();strong_by_target={};ntot=0
for l in open(os.path.join(WK,"all_direct_call_sites.tsv"),encoding="utf-8").read().splitlines()[1:]:
    f=l.split("\t");targets.add(int(f[2],16));strong_by_target.setdefault(f[2],[]).append(f[0]);ntot+=1
print("distinct direct-call targets:",len(targets),"of",ntot,"calls")
N=len(entries)
baseline_random={};baseline_aligned={}
for seed in range(10):
    rng=random.Random(20261118+seed)
    samp=[TEXT_VA+rng.randrange(TEXT_SIZE) for _ in range(N)]
    baseline_random[seed]=sum(1 for s in samp if s in targets)
    rng2=random.Random(700+seed)
    samp2=[TEXT_VA+(rng2.randrange(TEXT_SIZE//16)*16) for _ in range(N)]
    baseline_aligned[seed]=sum(1 for s in samp2 if s in targets)
br=list(baseline_random.values());ba=list(baseline_aligned.values())
print("random baseline N=%d 10 seeds:"%N,br,"mean=",sum(br)/10)
print("aligned16 baseline N=%d 10 seeds:"%N,ba,"mean=",sum(ba)/10)
weak_by_target={}
for i in range(len(code)-4):
    if code[i]==0xE8:
        rel=struct.unpack_from("<i",code,i+1)[0]
        tgt=(TEXT_VA+i+5+rel)&0xFFFFFFFF
        weak_by_target.setdefault(f"{tgt:08X}",[]).append(f"{TEXT_VA+i:08X}")
diff={}
for e in entries:
    strong=set(strong_by_target.get(e,[]));weak=set(weak_by_target.get(e,[]))
    diff[e]=dict(strong=len(strong),weak=len(weak),weak_only=len(weak-strong),strong_only=len(strong-weak),weak_only_sites=sorted(weak-strong)[:8])
wo=sum(d["weak_only"] for d in diff.values());so=sum(d["strong_only"] for d in diff.values())
print("differential weak_only total:",wo,"strong_only total:",so)
virt=json.load(open(os.path.join(EV,"virtual_reachable_rows.json"),encoding="utf-8"))
vset=set(x["entry"] for x in virt["virtual_all"])
wp=0;sp=0;wonly=[]
for r in V:
    wp+=1
    guards=(r["align16"] and r["pred_tail"]=="90" and r["n_ok"]>=1 and not r["any_atexit"] and r["entry"] not in vset)
    if guards:sp+=1
    else:wonly.append(r["entry"])
print("discriminating differential weak=%d strong=%d weak_only=%d %s"%(wp,sp,len(wonly),wonly))
roots=[os.path.join(ROOT,"docs","re"),os.path.join(ROOT,"re_atlas","kb"),os.path.join(ROOT,"re_atlas","evidence"),os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE"),os.path.join(ROOT,"lead")]
rgx={e:re.compile(r"(?i)(?<![0-9A-F])0?x?"+e.lower()+r"(?![0-9A-F])") for e in entries}
hits18={e:[] for e in entries};scanned=0
for base in roots:
    if not os.path.isdir(base):continue
    for dp,dn,fn in os.walk(base):
        for n in fn:
            if not n.lower().endswith((".md",".tsv",".txt",".json")):continue
            p=os.path.join(dp,n)
            try:txt=open(p,encoding="utf-8",errors="ignore").read().splitlines()
            except:continue
            scanned+=1
            for i,l in enumerate(txt,1):
                low=l.lower()
                for e in entries:
                    if rgx[e].search(low) and len(hits18[e])<6:
                        hits18[e].append(p.replace(ROOT+os.sep,"")+":"+str(i)+":"+l[:150])
LEDGER=os.path.join(ROOT,"lead","GOAL_THREE_TARGETS_20261018.md")
if os.path.exists(LEDGER):
    for i,l in enumerate(open(LEDGER,encoding="utf-8",errors="ignore").read().splitlines(),1):
        low=l.lower()
        for e in entries:
            if rgx[e].search(low) and len(hits18[e])<6:
                hits18[e].append("GOAL_THREE_TARGETS_20261018.md:"+str(i)+":"+l[:150])
print("18 scanned files:",scanned)
for e in entries:
    print("  18",e,"hits:",len(hits18[e]))
json.dump(dict(distinct_targets=len(targets),total_calls=ntot,baseline_random=baseline_random,baseline_aligned=baseline_aligned,
    baseline_mean=sum(br)/10,baseline_aligned_mean=sum(ba)/10,differential=diff,discriminating=dict(weak=wp,strong=sp,weak_only=wonly),
    conflicts18=hits18,scanned_files18=scanned),open(os.path.join(EV,"baseline_conflicts_final.json"),"w",encoding="utf-8"),indent=2,ensure_ascii=False)
print("wrote baseline_conflicts_final.json")