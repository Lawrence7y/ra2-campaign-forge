import os,sys
sys.path.insert(0,r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S13_N1/work")
from re_lib import *
ROOT=r"D:\Project\ra2-campaign-forge"
def src_lines(rel,a,b):
    p=os.path.join(ROOT,rel)
    L=open(p,encoding="utf-8",errors="replace").read().splitlines()
    return "\n".join(f"{i+1}: {L[i]}" for i in range(a-1,min(b,len(L))))
with open(os.path.join(EVID,"N65_proof.txt"),"w",encoding="utf-8") as f:
    f.write("S13-N1 naming proof: 0065B1E0 -> RadSiteClass::RadSiteClass()\n")
    f.write("SHA256 "+sha()+"\n\n")
    f.write("[A1 binary ctor body, direct PE bytes/capstone; not atlas-size dependent]\n")
    for i in fn_ins(0x65B1E0,186): f.write(fmt(i)+"\n")
    f.write("\n[A2 RTTI/vt ownership: COL at vt-4, TD+8 inline name]\n")
    for vt in [0x7F0810,0x7F07F4,0x7F07EC,0x7F07E4]:
        col=u32(vt-4); td=u32(col+12)
        f.write(f"vt={vt:08X} COL={col:08X} TD={td:08X} TD+8={cstr(td+8,64)!r} cls={rtti_name_from_vt(vt)}\n")
    f.write("\n[A3 factory: push size 0x74 -> new -> ctor]\n")
    for i in dis(0x4691A8,0x28): f.write(fmt(i)+"\n")
    f.write("\n[B1 source mapping (independent of binary)]\n")
    f.write("YRpp/RadSiteClass.h:18,93-95,106\n")
    f.write(src_lines("YRpp/RadSiteClass.h",16,20)+"\n")
    f.write(src_lines("YRpp/RadSiteClass.h",92,96)+"\n")
    f.write(src_lines("YRpp/RadSiteClass.h",104,108)+"\n")
    f.write("\n[B2 existing address-indexed correction in repo (no conflicting name)]\n")
    f.write(src_lines("lead/next_re_20261117_r14/N_FIX/NOINIT_CENSUS.tsv",65,65)+"\n")
with open(os.path.join(EVID,"W773030_proof.txt"),"w",encoding="utf-8") as f:
    f.write("S13-N1 naming proof: 00773030 -> WeaponTypeClass::FindIndex\n")
    f.write("SHA256 "+sha()+"\n\n")
    f.write("[A1 binary body: name-in-ECX -> array index; direct PE bytes/capstone]\n")
    for i in fn_ins(0x773030,61): f.write(fmt(i)+"\n")
    f.write("\n[A2 direct callers pass weapon ID strings then index the same array]\n")
    for lo,n in [(0x46B36B,0x2C),(0x6E39C3,0x22)]:
        f.write(f"-- caller window {lo:08X} --\n")
        for i in dis(lo,n): f.write(fmt(i)+"\n")
    f.write(f"string@81AFA0={cstr(0x81AFA0,64)!r}\n")
    f.write(f"string@842C2C={cstr(0x842C2C,64)!r}\n")
    f.write("\n[A3 array ownership: proven WeaponTypeClass ctor appends to 0x887568/0x88756C/0x887578]\n")
    for i in dis(0x771E9B,0x53):
        s=fmt(i).lower()
        if '887568' in s or '88756c' in s or '887578' in s or '7f73b8' in s: f.write(fmt(i)+"\n")
    f.write("\n[B1 source mapping (independent of binary)]\n")
    f.write("YRpp/AbstractTypeClass.h:12-40 defines ABSTRACTTYPE_ARRAY::FindIndex(pID) as strcmpi(Array->Items[i]->ID,pID) -> index/-1; YRpp/WeaponTypeClass.h maps WeaponTypeClass Array to 0x887568.\n")
    f.write(src_lines("YRpp/AbstractTypeClass.h",12,40)+"\n")
    f.write(src_lines("YRpp/WeaponTypeClass.h",12,22)+"\n")
    f.write("\n[Verdict]\n")
    f.write("A and B are independent channels: binary body/callers/ctor vs YRpp source contract. Name_kind=symbolic (FindIndex is a real source-level static method in the macro).\n")
print("proofs written")
