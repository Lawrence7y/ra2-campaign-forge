#!/usr/bin/env python3
"""S06-K4 behavior-level proof for 0x00483710 (ore growth gate) and delta append."""
from pathlib import Path
import pefile,struct,csv,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r"D:\Project\ra2-campaign-forge"); EXE=ROOT/"ra2youli/gamemd.exe"
COV=ROOT/"lead/next_re_20261117_r14/COVERAGE/coverage.tsv"; ATL=ROOT/"lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv"
CARD=ROOT/"lead/next_re_20261117_r14/S06_K4"; EVID=CARD/"EVIDENCE"
data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections: secs.append((IB+s.VirtualAddress,IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData,s.SizeOfRawData))
def off(va):
 for a,b,p,r in secs:
  if a<=va<b:
   d=va-a
   return p+d if d<r else None
 return None
def at(va,n):
 o=off(va); return None if o is None or o+n>len(data) else data[o:o+n]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def dis(va,n,c=400):
 b=at(va,n); return [] if b is None else list(md.disasm(b,va,count=c))
def norm(x): return x.strip().lower()
cov=[r for r in csv.DictReader(COV.open('r',encoding='utf-8',newline=''),delimiter='\t') if r['subsystem']=='S06']
atl={norm(r['entry']) for r in csv.DictReader(ATL.open('r',encoding='utf-8',newline=''),delimiter='\t')}
row=next(r for r in cov if norm(r['entry'])==norm('00483710'))
if row['grade'].strip()=='[已证]': raise SystemExit('baseline already proved')
if norm(row['entry']) not in atl: raise SystemExit('entry not in atlas')
f=dis(0x483710,112)
assert any(i.mnemonic=='call' and i.op_str=='0x5fdd20' for i in f)
assert any(i.mnemonic=='call' and i.op_str=='0x487190' for i in f)
assert any(i.address==0x48375b and i.mnemonic=='fcomp' and i.op_str=='qword ptr [0x7e3810]' for i in f)
assert any(i.address==0x483770 and i.bytes.hex()=='6a01' for i in f)
assert all(not re.search(r'slot\d+',row['name']) for re in [__import__('re')])
# Callee argument-order proof: after sub esp,0x84 + four pushes, [esp+0x90] maps to arg2 then arg1.
inc=dis(0x487190,64)
assert any(i.address==0x48719c and 'esp + 0x90' in i.op_str for i in inc)
assert any(i.address==0x4871a4 and 'esp + 0x90' in i.op_str for i in inc)
assert any(i.address==0x4872a0 and i.mnemonic=='mov' and 'esi + 0x11e' in i.op_str and i.op_str.endswith(', bl') for i in dis(0x487190,320,200))
const=struct.unpack_from('<d',data,off(0x7E3810))[0]
assert const==1e-5,const
sem=("CellClass::GrowTiberiumIfAllowed: if rules flag set, cell type resolves via 0x5FDD20, cell-state +0x11C==0, "
     "density +0x11E < type growth limit +0xE4, and type growth chance at +0xB0 >= 1e-05, then call IncreaseTiberium(typeIndex,1) and return true; else false")
delta=[]
p=CARD/'coverage_delta.tsv'
with p.open('r',encoding='utf-8',newline='') as fh:
    delta=list(csv.reader(fh,delimiter='\t'))
if not any(r and r[0].upper()=='00483710' for r in delta):
    delta.append(['00483710','S06','CellClass::GrowTiberiumIfAllowed',sem,'[已证]','EVIDENCE/growth_behavior.txt'])
delta=sorted(delta,key=lambda r:r[0].upper())
with p.open('w',encoding='utf-8',newline='') as fh:
    for r in delta: fh.write('\t'.join(r)+'\n')
lines=["S06-K4 BEHAVIOR-LEVEL PROOF: 00483710","SHA256="+hashlib.sha256(data).hexdigest().upper()]
lines.append("BASELINE grade="+row['grade'].strip()+" name="+row['name'].strip()+" old_semantics="+row['one_line_semantics'].strip())
lines.append("PROOF_TYPE=3 behavior-level; this=CellClass* (carries +0x44 overlay/tiberium type ID and +0x11E density from S06-K2/K3 audited field table)")
lines.append("KW1 rules gate: 0x483718 A134A60000 mov al,[0xA8B230+0x34A6]; test al,al; je 0x48377C(xor al,al;ret)")
lines.append("KW2 type lookup: 0x483722 mov ecx,[esi+0x44]; 0x483725 call 0x5FDD20 (OverlayTypeIndex -> DVC<TiberiumClass*> index); cmp eax,-1 -> false")
lines.append("KW3 cell gate: 0x483738 mov cl,[esi+0x11C]; test cl,cl; jne false; 0x48374A mov dl,[esi+0x11E]; 0x483750 cmp [type+0xE4]; jge false")
lines.append("KW4 growth chance: 0x483755 fld qword [type+0xB0]; 0x48375B fcomp qword [0x7E3810]; fnstsw; test ah,1; jne false; constant bytes="+at(0x7E3810,8).hex()+" = 1e-05")
lines.append("KW5 success call: 0x483768 mov ecx,[esi+0x44]; call 0x5FDD20; 0x483770 push 1; 0x483772 push eax(typeIndex); 0x483775 call 0x487190")
lines.append("CALLEE_ARG_ORDER: 0x48719C/0x4871A4 both read [esp+0x90] after sub esp,0x84 and four pushes; first is arg2=amount (ebx), second arg1=typeIndex (ebp); 0x4872A0 writes [esi+0x11E]=bl")
lines.append("FIELD_CROSSCHECK: +0x44 and +0x11E are [已证] in S06-K2 EVIDENCE/t1_FINAL.txt and S06-K3 EVIDENCE/k3_fieldscan2.tsv; +0x11C has W2/R4 double support in S06-K3 but semantics only [静态推断], so this row states raw gate byte == 0 rather than inventing occupancy semantics")
lines.append("CONCLUSION: byte-level behavior itself proves the gate-and-increase semantics; not inferred from a vtable slot.")
lines.append("")
lines.append("DISASM 00483710..0048377F")
lines += [f"{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}" for i in f]
lines.append("")
lines.append("DISASM callee 0x487190 prologue/arg reads")
lines += [f"{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}" for i in inc]
(EVID/'growth_behavior.txt').write_text("\n".join(lines)+"\n",encoding='utf-8')
print("growth proof appended; delta rows",len(delta))
