import csv, json, hashlib, pathlib, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86_const import X86_OP_IMM, X86_OP_MEM
ROOT=pathlib.Path(r"D:\Project\ra2-campaign-forge")
OUT=ROOT/"lead"/"next_re_20261117_r14"/"S13_C4B"
TARGET=ROOT/"ra2youli"/"gamemd.exe"
CLS=ROOT/"lead"/"next_re_20261117_r14"/"SURVEY_D39"/"EVIDENCE"/"classification.tsv"
ATLAS=ROOT/"lead"/"next_re_20261112_r10"/"W130_atlas"/"function_atlas.tsv"
COV=ROOT/"lead"/"next_re_20261117_r14"/"COVERAGE"/"coverage.tsv"
def sha(p):
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest().upper()
def rows(p,delim=None):
 if delim is None: delim=chr(9)
 raw=p.read_text(encoding="utf-8",errors="replace").splitlines()
 rdr=(ln.split(delim) for ln in raw if ln.strip())
 hdr=next(r for r in rdr if len(r)>1)
 hdr=[x.strip().lstrip("\ufeff") for x in hdr]
 return hdr,[dict(zip(hdr,r)) for r in rdr if len(r)==len(hdr)]
pe=pefile.PE(str(TARGET),fast_load=False)
ib=pe.OPTIONAL_HEADER.ImageBase
text=next(s for s in pe.sections if s.Name.rstrip(b"\x00")==b".text")
data=pe.__data__
def rva2off(rva,size=4):
 sec=next((s for s in pe.sections if s.VirtualAddress<=rva<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData)),None)
 if sec is None or rva+size>sec.VirtualAddress+sec.SizeOfRawData: return None
 return sec.PointerToRawData+(rva-sec.VirtualAddress)
def u32va(va):
 o=rva2off(va-ib,4)
 return None if o is None else struct.unpack_from("<I",data,o)[0]
def cstr(va,maxlen=120):
 o=rva2off(va-ib,1)
 if o is None: return None
 b=data[o:o+maxlen]; z=b.find(b"\x00")
 if z<0: return None
 try: return b[:z].decode("ascii")
 except UnicodeDecodeError: return None
def dis_range(va,size):
 off=rva2off(va-ib,size)
 if off is None: return []
 md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
 return list(md.disasm(data[off:off+size],va))
ch,c4all=rows(CLS); c4=[r for r in c4all if r["subsystem"]=="S13" and r["class"]=="C4"]
ah,atlas=rows(ATLAS); amap={int(r["entry"],16):int(r["size"]) for r in atlas}
covh,cov=rows(COV); proved={int(r["entry"],16) for r in cov if r.get("grade","")=="[\u5df2\u8bc1]"}
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
direct={}; scan_n=0
for ins in md.disasm(data[text.PointerToRawData:text.PointerToRawData+min(text.SizeOfRawData,text.Misc_VirtualSize)],ib+text.VirtualAddress):
 scan_n+=1
 if ins.mnemonic=="call" and len(ins.operands)==1 and ins.operands[0].type==X86_OP_IMM: direct.setdefault(ins.operands[0].imm,[]).append(ins.address)
vtrefs={}
for sec in pe.sections:
 if sec.Name.rstrip(b"\x00")==b".text": continue
 off=sec.PointerToRawData
 for p in range(off,off+sec.SizeOfRawData-3,4):
  v=struct.unpack_from("<I",data,p)[0]
  if v in amap:
   va=ib+sec.VirtualAddress+(p-off); vtrefs.setdefault(v,[]).append(va)
report=[]
for r in c4:
 e=int(r["entry"],16); size=amap.get(e); body=dis_range(e,size) if size else []
 imm=[]; memabs=[]; calls=[]; strings=[]
 for ins in body:
  for op in ins.operands:
   if op.type==X86_OP_IMM and 0x400000<=op.imm<0x810000:
    imm.append((ins.address,ins.mnemonic,hex(op.imm)))
    s=cstr(op.imm)
    if s and len(s)>=3: strings.append((hex(ins.address),s))
   if op.type==X86_OP_MEM and op.mem.base==0 and op.mem.index==0 and op.mem.disp>=0x400000:
    memabs.append((ins.address,ins.mnemonic,hex(op.mem.disp)))
  if ins.mnemonic=="call" and ins.operands:
   op=ins.operands[0]
   calls.append((hex(ins.address),"direct" if op.type==X86_OP_IMM else "indirect",op.imm if op.type==X86_OP_IMM else (hex(op.mem.disp) if op.type==X86_OP_MEM else "")))
 rtti="-"
 for va in vtrefs.get(e,[]):
  td=u32va(va-4+0xC)
  if td:
   s=cstr(td+8)
   if s and s.startswith(".?AV"): rtti=s
 report.append(dict(entry=r["entry"],name=r["name"],size=size,rtti=rtti,imm=imm[:30],memabs=memabs[:30],calls=calls[:40],strings=strings[:30],direct_sites=[hex(x) for x in direct.get(e,[])],vrefs=[hex(x) for x in vtrefs.get(e,[])][:20]))
(OUT/"work"/"scan_raw.json").write_text(json.dumps(dict(target=str(TARGET),sha256=sha(TARGET),text_insns=scan_n,direct_call_targets=len(direct),c4_count=len(c4),rows=report),indent=2),encoding="utf-8")
rank=[]
for d in report:
 g=sorted(set(x[2] for x in d["memabs"]))
 pr=sum(1 for a,k,t in d["calls"] if k=="direct" and isinstance(t,int) and t in proved)
 rank.append((pr,len(d["strings"]),len(g),d["entry"],d["name"],g[:10],d["strings"][:8],d["calls"][:8]))
rank.sort(key=lambda x:(-x[0],-x[1],-x[2]))
with (OUT/"work"/"candidate_rank.tsv").open("w",encoding="utf-8",newline="") as f:
 w=csv.writer(f,delimiter=chr(9)); w.writerow(["proved_calls","strings","globals","entry","name","globals_sample","strings_sample","calls_sample"])
 for x in rank: w.writerow([x[0],x[1],x[2],x[3],x[4],";".join(x[5]),";".join(a+"@"+b for a,b in x[6]),";".join(":".join(map(str,c)) for c in x[7])])
print("target",sha(TARGET),"text_insns",scan_n,"direct_call_targets",len(direct),"c4",len(c4))
for x in rank[:20]: print(x[:7])
x=next(i for i in dis_range(0x4386AB,8) if i.address==0x4386AB)
print("capstone selfcheck",x.mnemonic,x.op_str,"mem.index",x.operands[0].mem.index,"has op.index",hasattr(x.operands[0],"index"))
