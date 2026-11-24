#!/usr/bin/env python3
# Determine vtable-reachability of S21 rows via .rdata aligned dword scan.
import os,sys,io,struct,json
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8",errors="replace")
import pefile
ROOT=r"D:\Project\ra2-campaign-forge";OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","S21_DIRECT")
WK=os.path.join(OUT,"work");EV=os.path.join(OUT,"EVIDENCE");EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
COV=os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE","coverage.tsv")
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
def norm(a):return a.upper().replace("0X","")
data=open(EXE,"rb").read();pe=pefile.PE(EXE,fast_load=True);ib=pe.OPTIONAL_HEADER.ImageBase
sections={}
for s in pe.sections:
    nm=s.Name.rstrip(b"\x00").decode(errors="replace")
    sections[nm]=(ib+s.VirtualAddress,data[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData])
print("sections:",[(k,hex(v[0]),hex(len(v[1]))) for k,v in sections.items()])
dword_set={}
for secname in (".rdata",):
    if secname not in sections:continue
    base,raw=sections[secname]
    for off in range(0,len(raw)-3,4):
        v=struct.unpack_from("<I",raw,off)[0]
        dword_set.setdefault(v,[]).append(base+off)
al=set()
for l in open(ATLAS,encoding="utf-8").read().splitlines()[1:]:
    if not l.strip():continue
    al.add(norm(l.split("\t")[0]))
rows=[]
for l in open(COV,encoding="utf-8").read().splitlines()[1:]:
    if not l.strip():continue
    f=l.split("\t")
    if f[1]=="S21" and norm(f[0]) in al:rows.append(dict(entry=f[0],name=f[2],sem=f[3],grade=f[4]))
upgraded=set()
for l in open(os.path.join(WK,"s21_direct_hits.tsv"),encoding="utf-8").read().splitlines()[1:]:
    f=l.split("\t")
    if int(f[3])>0 and f[1]!="[已证]":upgraded.add(f[0])
print("S21 rows:",len(rows),"to-upgrade(direct):",len(upgraded))
virt=[]
for r in rows:
    e=int(r["entry"],16)
    locs=dword_set.get(e,[])
    if locs:virt.append(dict(entry=r["entry"],name=r["name"],sem=r["sem"],grade=r["grade"],
        vrefs=[f"{x:08X}" for x in locs[:8]],nvrefs=len(locs)))
vset=set(v["entry"] for v in virt)
print("S21 rows .rdata-dword-reachable:",len(virt))
ov=upgraded & vset
print("OVERLAP direct-upgrade ∩ virtual-reachable:",len(ov),sorted(ov))
onlyvirt=[v for v in virt if v["entry"] not in upgraded and v["grade"]!="[已证]"]
print("virtual-reachable non-proved non-upgraded (-> VIRTUAL_SKIPPED):",len(onlyvirt))
json.dump(dict(virtual_all=virt,only_virtual_skipped=onlyvirt,overlap=sorted(ov)),
    open(os.path.join(EV,"virtual_reachable_rows.json"),"w",encoding="utf-8"),indent=2,ensure_ascii=False)
print("wrote virtual_reachable_rows.json")