# -*- coding: utf-8 -*-
import sys, os, json, struct, pefile
sys.stdout.reconfigure(encoding="utf-8")
ROOT=r"D:\Project\ra2-campaign-forge"
OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","S11_DIRECT")
WORK=os.path.join(OUT,"work")
COV=os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE","coverage.tsv")
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
P=os.path.join(ROOT,"ra2youli","gamemd.exe")
pe=pefile.PE(P); data=open(P,"rb").read()
sec=[s for s in pe.sections if s.Name.rstrip(b"\x00")==b".text"][0]
BASE=pe.OPTIONAL_HEADER.ImageBase+sec.VirtualAddress; NB=sec.Misc_VirtualSize
TEXT_END=BASE+NB; code=data[sec.PointerToRawData:sec.PointerToRawData+NB]
# verify clean sites
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
boundary=set()
for ins in md.disasm(code,BASE): boundary.add(ins.address)
ok=0; bad=[]
for line in open(os.path.join(OUT,"EVIDENCE","direct_call_sites_clean.tsv"),encoding="utf8").read().splitlines():
    if line.startswith("#") or not line.strip(): continue
    c=line.split("\t")
    site=int(c[0],16); b=c[3]; rel=int(c[4]); tgt=int(c[5],16); entry=c[6]; status=c[7]
    off=site-BASE
    if not(0<=off<len(code)-5): bad.append((line,"off out")); continue
    if code[off:off+5].hex().upper()!=b: bad.append((line,"bytes mismatch")); continue
    if site not in boundary: bad.append((line,"not boundary")); continue
    if not(BASE<=site<TEXT_END): bad.append((line,"out of coverage")); continue
    if site+5+rel!=tgt or tgt!=int(entry,16): bad.append((line,"target mismatch")); continue
    if status!="OK": bad.append((line,"status")); continue
    ok+=1
print("clean sites verified OK",ok,"bad",len(bad))
for b in bad[:5]: print("BAD",b)
# verify delta format
delta=open(os.path.join(OUT,"coverage_delta.tsv"),encoding="utf8").read().splitlines()
print("delta header",delta[0])
print("delta rows",len(delta)-1)
for l in delta[1:]:
    c=l.split("\t")
    if len(c)!=8: print("BAD COLS",len(c),l[:100])
# simulate merge: apply delta grades to S11 coverage
atlas=set()
for line in open(ATLAS,encoding="utf8").read().splitlines()[1:]:
    if not line.strip(): continue
    atlas.add(line.split("\t")[0].strip().upper())
grades={}
for line in open(COV,encoding="utf8").read().splitlines()[1:]:
    if not line.strip(): continue
    c=line.split("\t")
    if len(c)>=8: grades[c[0].strip().upper()]={"sub":c[1].strip(),"grade":c[4].strip()}
for l in delta[1:]:
    e=l.split("\t")[0]
    grades[e]["grade"]="[已证]"
n=sum(1 for e,v in grades.items() if v["sub"]=="S11" and e in atlas)
proved=sum(1 for e,v in grades.items() if v["sub"]=="S11" and e in atlas and v["grade"]=="[已证]")
static=sum(1 for e,v in grades.items() if v["sub"]=="S11" and e in atlas and v["grade"]=="[静态推断]")
unproven=sum(1 for e,v in grades.items() if v["sub"]=="S11" and e in atlas and v["grade"]=="[未证]")
print("AFTER MERGE: n",n,"proved",proved,"static",static,"unproven",unproven,"threshold",__import__("math").ceil(n/2))
# verify virtual skipped count
vs=open(os.path.join(OUT,"VIRTUAL_SKIPPED.tsv"),encoding="utf8").read().splitlines()
print("VIRTUAL_SKIPPED rows",len(vs)-1)