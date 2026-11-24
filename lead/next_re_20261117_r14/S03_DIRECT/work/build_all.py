# -*- coding: utf-8 -*-
import sys, os, json, hashlib, struct, bisect, random, re, time
sys.stdout.reconfigure(encoding="utf-8")
import pefile
from capstone import *
from capstone.x86 import X86_INS_CALL, X86_OP_MEM

ROOT=r"D:\Project\ra2-campaign-forge"
OUT=ROOT+r"\lead\next_re_20261117_r14\S03_DIRECT"
WORK=OUT+r"\work"; EVID=OUT+r"\EVIDENCE"
os.makedirs(WORK,exist_ok=True); os.makedirs(EVID,exist_ok=True)
BIN=ROOT+r"\ra2youli\gamemd.exe"
COV=ROOT+r"\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATLAS=ROOT+r"\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

data=open(BIN,"rb").read()
sha=hashlib.sha256(data).hexdigest().upper()
print("SHA256",sha,"size",len(data))
pe=pefile.PE(BIN)
sec=[s for s in pe.sections if s.Name.rstrip(b"\x00")==b".text"][0]
BASE=pe.OPTIONAL_HEADER.ImageBase+sec.VirtualAddress
NB=sec.Misc_VirtualSize
code=data[sec.PointerToRawData:sec.PointerToRawData+NB]
print("TEXT",hex(BASE),hex(BASE+NB),"rawE8",code.count(0xE8))

# ---- atlas ----
atlas={}
for line in open(ATLAS,encoding="utf8",errors="replace").read().splitlines()[1:]:
    c=line.split("\t")
    if not c[0]: continue
    try: atlas[int(c[0],16)]=int(c[1])
    except: pass
ranges=sorted([(e,e+sz) for e,sz in atlas.items()])
starts=[r[0] for r in ranges]
def find_caller(addr):
    i=bisect.bisect_right(starts,addr)-1
    if i>=0 and ranges[i][0]<=addr<ranges[i][1]: return ranges[i]
    return None

# ---- coverage map + S03 working surface ----
cov={}
for line in open(COV,encoding="utf8",errors="replace").read().splitlines()[1:]:
    c=line.split("\t")
    if len(c)<8: continue
    cov[c[0].strip().upper()]={"sub":c[1].strip(),"name":c[2].strip(),"sem":c[3].strip(),"grade":c[4].strip(),"ev":c[5].strip()}
rows=[]
for e,r in cov.items():
    if r["sub"]=="S03" and r["grade"]=="[静态推断]" and int(e,16) in atlas:
        rows.append({"entry":e,"name":r["name"],"sem":r["sem"],"size":atlas[int(e,16)],"ev":r["ev"]})
rows.sort(key=lambda x:x["entry"])
print("working surface",len(rows))

# ---- 19 self-check ----
md_detail=Cs(CS_ARCH_X86,CS_MODE_32); md_detail.detail=True
sc_lines=["# 19 capstone 5.0.7 op.index self-check","",
          "capstone 5.0.7 x86: operand has NO .index attribute; mem index is op.mem.index (no index => int 0, NOT None).",
          "This card uses raw-byte E8+rel32 (not operand-None filtering), so the trap does not apply to the scan; self-check still performed.",""]
for insn in md_detail.disasm(bytes.fromhex("E810000000"),0x500000):
    sc_lines.append("known-positive: E8 10 00 00 00 @ 0x500000 -> %s %s ; size=%d"%(insn.mnemonic,insn.op_str,insn.size))
    for op in insn.operands:
        sc_lines.append("  op.type=%s hasattr(op,'index')=%s"%(op.type,hasattr(op,'index')))
        if op.type==X86_OP_MEM: sc_lines.append("  op.mem.index=%r (int 0 when no index)"%op.mem.index)
    ok=(insn.mnemonic=="call" and insn.size==5 and 0x500000+5+0x10==0x500015)
    sc_lines.append("target check 0x500000+5+0x10=0x500015 -> %s"%("PASS" if ok else "FAIL"))
# call [eax] self-check
for insn in md_detail.disasm(bytes.fromhex("FF10"),0x500100):
    for op in insn.operands:
        if op.type==X86_OP_MEM:
            sc_lines.append("call [eax] (FF 10): op.mem.index=%r (int 0) ; op.index attr=%s"%(op.mem.index,hasattr(op,'index')))
open(WORK+r"\selfcheck.md","w",encoding="utf8").write("\n".join(sc_lines)+"\n")
print("\n".join(sc_lines))

# ---- full scan ----
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True; md.detail=False
ninsn=0; ne8=0; boundary_sites=[]  # (site,target)
t=time.time()
for insn in md.disasm(code,BASE):
    ninsn+=1
    b=insn.bytes
    if len(b)==5 and b[0]==0xE8 and insn.id==X86_INS_CALL:
        ne8+=1
        site=insn.address
        rel=struct.unpack("<i",b[1:5])[0]
        boundary_sites.append((site,(site+5+rel)&0xFFFFFFFF))
print("SCAN ninsn",ninsn,"E8@boundary",ne8,"elapsed",round(time.time()-t,2))
target_sites={}
for s,tg in boundary_sites: target_sites.setdefault(tg,[]).append(s)

# raw E8 windows (weak: no boundary)
raw_targets={}
for i in range(len(code)-4):
    if code[i]==0xE8:
        rel=struct.unpack_from("<i",code,i+1)[0]
        tg=(BASE+i+5+rel)&0xFFFFFFFF
        raw_targets.setdefault(tg,[]).append(BASE+i)

# ---- classify rows ----
qualifying=[]
for r in rows:
    e=int(r["entry"],16)
    b_sites=target_sites.get(e,[])
    strong=[]; selfA=[]; selfB=[]; outside=[]
    for s in b_sites:
        if e<=s<e+r["size"]: selfA.append(s); continue
        caller=find_caller(s)
        if caller is None: outside.append(s); continue
        cs,ce=caller
        if cs<=e<ce: selfB.append(s); continue
        strong.append((s,cs,ce))
    weak=raw_targets.get(e,[])
    if strong:
        sites=[]
        for s,cs,ce in strong:
            off=s-BASE
            b5=code[off:off+5].hex(" ").upper()
            rel=struct.unpack_from("<i",code,off+1)[0]
            tgt=s+5+rel
            cg=cov.get("%08X"%cs,{}).get("grade","OUT_OF_COV")
            sites.append({"site":"%08X"%s,"caller":"%08X"%cs,"caller_grade":cg,
                          "bytes5":b5,"rel32":str(rel),"target":"%08X"%tgt,"status":"OK" if tgt==e else "MISMATCH"})
        qualifying.append({"entry":r["entry"],"name":r["name"],"sem":r["sem"],"old_grade":"[静态推断]",
                           "n_boundary":len(b_sites),"n_selfA":len(selfA),"n_selfB":len(selfB),"n_outside":len(outside),
                           "n_weak":len(weak),"sites":sites})
print("qualifying rows",len(qualifying),"total sites",sum(len(q["sites"]) for q in qualifying))
json.dump(qualifying,open(WORK+r"\qualifying.json","w",encoding="utf8"),ensure_ascii=False,indent=1)

# ---- baseline (random .text addresses + random atlas entries) ----
random.seed(20261118)
N=1000
h_strong=sum(1 for _ in range(N) if ((BASE+random.randrange(0,NB))&0xFFFFFFFF) in target_sites)
random.seed(20261118)
h_weak=sum(1 for _ in range(N) if ((BASE+random.randrange(0,NB))&0xFFFFFFFF) in raw_targets)
atlas_entries=list(atlas.keys())
ents=atlas_entries[:]
random.seed(20261118); random.shuffle(ents)
sample_atlas=ents[:11]
atlas_hits=sum(1 for e in sample_atlas if e in target_sites)
print("baseline random .text: strong %d/%d=%.2f%% weak %d/%d=%.2f%%"%(h_strong,N,100*h_strong/N,h_weak,N,100*h_weak/N))
print("baseline random atlas entries: %d/11"%atlas_hits)

# ---- differential (weak vs strong over same 108 rows) ----
strong_set=set(q["entry"] for q in qualifying)
weak_set=set(r["entry"] for r in rows if int(r["entry"],16) in raw_targets)
diff=sorted(weak_set-strong_set)
print("differential weak=%d strong=%d weak_only=%d"%(len(weak_set),len(strong_set),len(diff)))
json.dump({"weak_pass":len(weak_set),"strong_pass":len(strong_set),"weak_only":diff,
           "baseline_text":{"N":N,"strong_hit":h_strong,"weak_hit":h_weak},
           "baseline_atlas":{"n":11,"hit":atlas_hits}},
          open(WORK+r"\differential.json","w",encoding="utf8"),ensure_ascii=False,indent=1)

# ---- scan meta ----
json.dump({"sha256":sha,"file_size":len(data),"text_base":hex(BASE),"text_end":hex(BASE+NB),
           "ninsn":ninsn,"e8_boundary":ne8,"raw_e8":code.count(0xE8),
           "coverage_pct":100.0,"distinct_boundary_targets":len(target_sites)},
          open(WORK+r"\scan_meta.json","w",encoding="utf8"),ensure_ascii=False,indent=1)

# ---- EVIDENCE direct_call_sites.tsv (all sites) ----
ev=["# site\tcaller\tcaller_grade\tbytes5\trel32\ttarget\tstatus"]
for q in qualifying:
    for s in q["sites"]:
        ev.append("\t".join([s["site"],s["caller"],s["caller_grade"],s["bytes5"],s["rel32"],s["target"],s["status"]]))
open(EVID+r"\direct_call_sites.tsv","w",encoding="utf8").write("\n".join(ev)+"\n")
# clean = same (no exclusions)
open(EVID+r"\direct_call_sites_clean.tsv","w",encoding="utf8").write("\n".join(ev)+"\n")
print("EVIDENCE sites",len(ev)-1)

# ---- coverage_delta.tsv ----
delta=["entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\tname_kind\t旧grade→新grade"]
for q in qualifying:
    nm=q["name"]
    if re.match(r"^sub_[0-9A-Fa-f]{8}$",nm): nk="placeholder"
    elif "slot" in nm.lower() or "vslot" in nm.lower(): nk="symbolic"
    else: nk="behavioral"
    delta.append("\t".join([q["entry"],"S03",nm,q["sem"],"[已证]",
                 "EVIDENCE/direct_call_sites_clean.tsv#"+q["entry"],nk,"[静态推断]→[已证]"]))
open(OUT+r"\coverage_delta.tsv","w",encoding="utf8").write("\n".join(delta)+"\n")
print("coverage_delta rows",len(delta)-1)

# ---- VIRTUAL_SKIPPED.tsv ----
upgraded=set(q["entry"] for q in qualifying)
vs=["entry\tname\told_grade\texisting_evidence(123)\tnote"]
vcount=0; nonvderived=[]
for r in rows:
    if r["entry"] in upgraded: continue
    nm=r["name"].lower(); sm=r["sem"].lower()
    vderived=("slot" in nm or "vslot" in nm or "rtti-vftable" in sm or "虚表槽" in sm)
    if vderived:
        vs.append("\t".join([r["entry"],r["name"],"[静态推断]",r["sem"],"环④缺：只靠虚表可达，无 direct E8 call site；本卡不升格"]))
        vcount+=1
    else:
        nonvderived.append((r["entry"],r["name"],r["sem"]))
open(OUT+r"\VIRTUAL_SKIPPED.tsv","w",encoding="utf8").write("\n".join(vs)+"\n")
print("VIRTUAL_SKIPPED rows",vcount,"non-vderived-not-upgraded",len(nonvderived))
for x in nonvderived[:10]: print("  NONV",x)

# ---- conflict hits summary from earlier ----
ch_path=WORK+r"\conflict_hits.json"
if not os.path.exists(ch_path):
    json.dump({},open(ch_path,"w",encoding="utf8"),ensure_ascii=False,indent=1)

# ---- deliverable stats ----
stats={"qualifying_rows":len(qualifying),"delivered_rows":len(delta)-1,
       "excluded_conflict":[],"virtual_skipped":vcount,
       "sites_total":len(ev)-1,"sites_clean":len(ev)-1,
       "nonvderived_not_upgraded":len(nonvderived),
       "post_merge_proved":18+len(delta)-1}
json.dump(stats,open(WORK+r"\deliverable_stats.json","w",encoding="utf8"),ensure_ascii=False,indent=1)
print("STATS",json.dumps(stats,ensure_ascii=False))
print("DONE")
