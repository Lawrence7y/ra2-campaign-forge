# -*- coding: utf-8 -*-
import sys, os, json, hashlib, struct, pefile, bisect
sys.stdout.reconfigure(encoding="utf-8")
ROOT=r"D:\Project\ra2-campaign-forge"
OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","S11_DIRECT")
WORK=os.path.join(OUT,"work")
EVID=os.path.join(OUT,"EVIDENCE")
os.makedirs(EVID,exist_ok=True)
# config
P=os.path.join(ROOT,"ra2youli","gamemd.exe")
COV=os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE","coverage.tsv")
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
pe=pefile.PE(P); data=open(P,"rb").read()
sec=[s for s in pe.sections if s.Name.rstrip(b"\x00")==b".text"][0]
BASE=pe.OPTIONAL_HEADER.ImageBase+sec.VirtualAddress; NB=sec.Misc_VirtualSize
code=data[sec.PointerToRawData:sec.PointerToRawData+NB]
# load qualifying.json
q=json.load(open(os.path.join(WORK,"qualifying.json"),encoding="utf8"))
# conflicting unproven rows excluded (documented in DISAGREE.md)
EXCLUDE={"005AE860","005AF1A0","007559B0"}
clean=[r for r in q if r["entry"] not in EXCLUDE]
print("clean rows",len(clean))
# Build EVIDENCE/direct_call_sites.tsv
ev_lines=["# site\tcaller\tcaller_grade\tbytes5\trel32\ttarget\tentry\tstatus"]
import re
for r in q:
    e=r["entry"]; eiv=int(e,16)
    for srec in r["sites"]:
        site=int(srec["site"],16); off=site-BASE
        b=code[off:off+5].hex().upper()
        rel=struct.unpack_from("<i",code,off+1)[0]
        tgt=site+5+rel
        status="OK" if tgt==eiv else "MISMATCH"
        ev_lines.append("\t".join([srec["site"],srec["caller"],srec["caller_grade"],b,str(rel),f"{tgt:08X}",e,status]))
open(os.path.join(EVID,"direct_call_sites.tsv"),"w",encoding="utf8").write("\n".join(ev_lines)+"\n")
print("wrote EVIDENCE/direct_call_sites.tsv",len(ev_lines)-1,"sites")
# Build EVIDENCE/direct_call_sites_clean.tsv (only clean rows)
clean_entries=set(r["entry"] for r in clean)
ev2=[l for l in ev_lines if l.startswith("#") or l.split("\t")[6] in clean_entries]
open(os.path.join(EVID,"direct_call_sites_clean.tsv"),"w",encoding="utf8").write("\n".join(ev2)+"\n")
# Build coverage_delta.tsv (8 rows, 8 columns per card)
delta=["entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\tname_kind\t旧grade→新grade"]
for r in clean:
    e=r["entry"]
    nm=r["name"]
    # name_kind
    if re.match(r"^sub_[0-9A-Fa-f]{8}$",nm): nk="placeholder"
    elif "slot" in nm or "vslot" in nm: nk="symbolic"
    else: nk="behavioral"
    grade="[已证]"
    evpath="EVIDENCE/direct_call_sites_clean.tsv#"+e
    trans=r["old_grade"]+"→[已证]"
    delta.append("\t".join([e,"S11",nm,r["sem"],grade,evpath,nk,trans]))
open(os.path.join(OUT,"coverage_delta.tsv"),"w",encoding="utf8").write("\n".join(delta)+"\n")
print("wrote coverage_delta.tsv",len(delta)-1,"rows")
# Build VIRTUAL_SKIPPED.tsv
# S11 non-proven rows not upgraded: categorize vtable-derived by name/semantics
cov={}
for line in open(COV,encoding="utf8").read().splitlines()[1:]:
    if not line.strip(): continue
    c=line.split("\t")
    if len(c)>=8: cov[c[0].strip().upper()]={"sub":c[1].strip(),"name":c[2].strip(),"sem":c[3].strip(),"grade":c[4].strip(),"ev":c[5].strip()}
atlas=set()
for line in open(ATLAS,encoding="utf8").read().splitlines()[1:]:
    if not line.strip(): continue
    atlas.add(line.split("\t")[0].strip().upper())
upgraded=set(r["entry"] for r in clean)
vs=["entry\tname\told_grade\texisting_evidence(①②③)\tnote"]
skipped_all=[]
for e in sorted(atlas):
    if e not in cov: continue
    row=cov[e]
    if row["sub"]!="S11" or row["grade"] not in ("[静态推断]","[未证]"): continue
    if e in upgraded or e in EXCLUDE: continue
    nm=row["name"]; sm=row["sem"]
    # vtable-derived if slotN/vslotN name or rtti-vftable semantics
    vderived = ("slot" in nm.lower() or "vslot" in nm.lower() or "rtti-vftable" in sm.lower() or "虚表槽" in sm)
    if vderived:
        vs.append("\t".join([e,nm,row["grade"],sm,"环④缺：只靠虚表可达，无 direct E8 call site；本卡不升格"]))
        skipped_all.append(e)
open(os.path.join(OUT,"VIRTUAL_SKIPPED.tsv"),"w",encoding="utf8").write("\n".join(vs)+"\n")
print("wrote VIRTUAL_SKIPPED.tsv",len(vs)-1,"rows")
# stats json
stats={"clean_rows":len(clean),"excluded_conflict":sorted(EXCLUDE),"virtual_skipped":len(vs)-1,
       "sites_clean":len(ev2)-1,"sites_total":len(ev_lines)-1}
json.dump(stats,open(os.path.join(WORK,"deliverable_stats.json"),"w",encoding="utf8"),ensure_ascii=False,indent=1)
print(json.dumps(stats,ensure_ascii=False))