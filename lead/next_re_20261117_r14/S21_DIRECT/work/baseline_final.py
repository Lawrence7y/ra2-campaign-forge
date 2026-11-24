#!/usr/bin/env python3
import os,sys,io,json,struct,random
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8",errors="replace")
import pefile
ROOT=r"D:\Project\ra2-campaign-forge"
OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","S21_DIRECT")
WK=os.path.join(OUT,"work");EV=os.path.join(OUT,"EVIDENCE");EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
V=json.load(open(os.path.join(EV,"verify_direct.json"),encoding="utf-8"))["verified"]
entries=[r["entry"] for r in V]
data=open(EXE,"rb").read();pe=pefile.PE(EXE,fast_load=True);ib=pe.OPTIONAL_HEADER.ImageBase
sec=[s for s in pe.sections if s.Name.rstrip(b"\x00").decode()==".text"][0]
va=ib+sec.VirtualAddress;code=data[sec.PointerToRawData:sec.PointerToRawData+sec.SizeOfRawData]
TEXT_VA=va;TEXT_SIZE=len(code);print("text size",TEXT_SIZE,flush=True)
targets=set();strong_by_target={};ntot=0
for l in open(os.path.join(WK,"all_direct_call_sites.tsv"),encoding="utf-8").read().splitlines()[1:]:
    f=l.split("\t");targets.add(int(f[2],16));strong_by_target.setdefault(f[2],[]).append(f[0]);ntot+=1
print("distinct targets",len(targets),"of",ntot,flush=True)
N=len(entries);baseline_random={};baseline_aligned={}
for seed in range(10):
    rng=random.Random(20261118+seed)
    baseline_random[seed]=sum(1 for _ in range(N) if (TEXT_VA+rng.randrange(TEXT_SIZE)) in targets)
    rng2=random.Random(700+seed)
    baseline_aligned[seed]=sum(1 for _ in range(N) if (TEXT_VA+(rng2.randrange(TEXT_SIZE//16)*16)) in targets)
br=list(baseline_random.values());ba=list(baseline_aligned.values())
print("random baseline",br,"mean",sum(br)/10,flush=True)
print("aligned baseline",ba,"mean",sum(ba)/10,flush=True)
print("doing weak raw-E8 scan...",flush=True)
weak_by_target={}
for i in range(len(code)-4):
    if code[i]==0xE8:
        rel=struct.unpack_from("<i",code,i+1)[0]
        tgt=(TEXT_VA+i+5+rel)&0xFFFFFFFF
        weak_by_target.setdefault(f"{tgt:08X}",[]).append(f"{TEXT_VA+i:08X}")
print("weak scan done",flush=True)
diff={}
for e in entries:
    strong=set(strong_by_target.get(e,[]));weak=set(weak_by_target.get(e,[]))
    diff[e]=dict(strong=len(strong),weak=len(weak),weak_only=len(weak-strong),strong_only=len(strong-weak))
wo=sum(d["weak_only"] for d in diff.values());so=sum(d["strong_only"] for d in diff.values())
print("diff weak_only",wo,"strong_only",so,flush=True)
virt=json.load(open(os.path.join(EV,"virtual_reachable_rows.json"),encoding="utf-8"))
vset=set(x["entry"] for x in virt["virtual_all"])
wp=0;sp=0;wonly=[]
for r in V:
    wp+=1
    guards=(r["align16"] and r["pred_tail"]=="90" and r["n_ok"]>=1 and not r["any_atexit"] and r["entry"] not in vset)
    if guards:sp+=1
    else:wonly.append(r["entry"])
print("discriminating weak",wp,"strong",sp,"weak_only",wonly,flush=True)
json.dump(dict(distinct_targets=len(targets),total_calls=ntot,baseline_random=baseline_random,baseline_aligned=baseline_aligned,
    baseline_mean=sum(br)/10,baseline_aligned_mean=sum(ba)/10,differential=diff,discriminating=dict(weak=wp,strong=sp,weak_only=wonly)),
    open(os.path.join(EV,"baseline_final.json"),"w",encoding="utf-8"),indent=2,ensure_ascii=False)
print("wrote baseline_final.json",flush=True)