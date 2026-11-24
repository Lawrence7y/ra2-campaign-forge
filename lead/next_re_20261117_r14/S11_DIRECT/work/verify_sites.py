import capstone, pefile, struct, bisect
P=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
COV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATLAS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11_DIRECT\work"
pe=pefile.PE(P); data=open(P,"rb").read()
sec=[s for s in pe.sections if s.Name.rstrip(b"\x00")==b".text"][0]
BASE=pe.OPTIONAL_HEADER.ImageBase+sec.VirtualAddress; NB=sec.Misc_VirtualSize
code=data[sec.PointerToRawData:sec.PointerToRawData+NB]
grade={}; name={}
for line in open(COV,encoding="utf8").read().splitlines()[1:]:
    if not line.strip(): continue
    c=line.split("\t")
    if len(c)<8: continue
    grade[c[0].strip().upper()]=c[4].strip(); name[c[0].strip().upper()]=c[2].strip()
at={}
for line in open(ATLAS,encoding="utf8").read().splitlines()[1:]:
    if not line.strip(): continue
    c=line.split("\t"); at[c[0].strip().upper()]=(int(c[1]),int(c[0],16))
s11rows=[]
for line in open(COV,encoding="utf8").read().splitlines()[1:]:
    if not line.strip(): continue
    c=line.split("\t")
    if len(c)<8: continue
    e=c[0].strip().upper()
    if c[1].strip().upper()=="S11" and e in at:
        s11rows.append((e,c[4].strip(),c[2].strip()))
targets=set(e for e,g,n in s11rows if g in ("[静态推断]","[未证]"))
from collections import defaultdict
tmap=defaultdict(list)
for l in open(OUT+r"\all_e8_calls.tsv",encoding="utf8").read().splitlines()[1:]:
    s,t=l.split("\t"); tmap[t].append(int(s,16))
print("targets(static+unproven)=",len(targets))
cnt=0
for e in sorted(targets):
    eiv=int(e,16)
    for s in tmap.get(e,[]):
        off=s-BASE
        if not (0<=off<len(code)-5): continue
        raw=code[off:off+5].hex().upper()
        rel=struct.unpack_from("<i",code,off+1)[0]
        computed=s+5+rel
        cnt+=1
        print("\t".join([e,grade.get(e,"?"),f"{s:08X}",raw,str(rel),f"{computed:08X}","OK" if computed==eiv else "MISMATCH"]))
print("total sites",cnt)
fn_list=sorted([(eiv,sz,e) for e,(sz,eiv) in at.items()]); fne=[x[0] for x in fn_list]
print("=== caller grade for 8 passing ===")
for e in ["0040B270","00415C60","00442D90","0055A910","0055A930","0055ABA0","0055ABB0","0055AD00"]:
    for s in tmap.get(e,[]):
        i=bisect.bisect_right(fne,s)-1; caller=None
        for j in range(i,max(-1,i-40),-1):
            eiv2,sz,eh=fn_list[j]
            if s<eiv2+sz: caller=eh; break
        print(e,f"{s:08X}",caller or "?", grade.get(caller,"?") if caller else "?")