from __future__ import annotations
import sys,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work')
import pe_util as pu
ATL=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
raw=open(ATL,'r',encoding='utf-8-sig').read().splitlines(); hdr=raw[0].split('\t'); meta={}; ints=[]
for ln in raw[1:]:
 p=ln.split('\t'); p+=['']*(len(hdr)-len(p)); d=dict(zip(hdr,p))
 try:a=int(d['entry'],16); b=a+int(d.get('size','0'))
 except:continue
 meta[a]=d; ints.append((a,b))
ints.sort()
def owner(va):
 for a,b in ints:
  if a<=va<b:return a
 return None
def td_name(td):
 b=pu.read(td+8,200) or b''; s=b.split(b'\0')[0]
 try:n=s.decode('ascii')
 except:return None
 return n if n.startswith('.?AV') and n.endswith('@@') else None
def class_of_func(entry):
 out=[]
 for name,vb,vs,pr,rs,ch in pu.sections():
  if ch & 0x20000000:continue
  data=pu.read(vb,rs) or b''; pat=struct.pack('<I',entry); pos=0
  while True:
   i=data.find(pat,pos)
   if i<0:break
   vt=vb+i; pos=i+1
   if i<4:continue
   col=struct.unpack_from('<I',data,i-4)[0]
   td=pu.u32(col+0xC)
   n=td_name(td) if td else None
   if n: out.append((vt,n,hex(col),hex(td)))
 return out
SITES=[
 (0x43AE50,0x4019A0,'CCFileClass::vslot0/destructor'),
 (0x43AE50,0x4AEC30,'BufferStraw::slot0'),
 (0x43AE50,0x4AECA0,'BufferPipe::slot0'),
 (0x43AE50,0x4A3890,'FileSystem::ReadWholeFile'),
 (0x43AE50,0x4A38D0,'FileSystem::LoadWholeFileEx'),
 (0x43AE50,0x4791F0,'CD::slot2'),
 (0x42E410,0x4BB0D0,'DSurface::slot3'),
 (0x42E410,0x552D60,'LoadProgressManager::Draw'),
 (0x42E410,0x7B9750,'WWMouseClass::ShowCursor'),
 (0x42E410,0x7B9A60,'WWMouseClass::CaptureMouse'),
 (0x4355B0,0x668BF0,'RulesClass::Read_File'),
 (0x4355B0,0x552D60,'LoadProgressManager::Draw'),
 (0x4355B0,0x52BA60,'sub_0052BA60'),
 (0x40E340,0x528660,'CCINIClass::WriteString'),
 (0x40E340,0x6686C0,'RulesClass::Init'),
 (0x433CF0,0x4A5EB0,'Surface::DrawText'),
 (0x433CF0,0x552D60,'LoadProgressManager::Draw'),
 (0x427940,0x4ACE70,'TabClass::slot32'),
 (0x427940,0x5BDF70,'MouseClass::slot30'),
]
lines=['S17-K6 caller-context recon']
for target,entry,desc in SITES:
 o=owner(entry) or entry
 lines.append('\n===== target %08X caller %08X owner %08X %s ====='%(target,entry,o,desc))
 lines.append('caller_vtable_classes='+repr(class_of_func(o)))
 d=meta.get(o,{}); st=entry-0x50; en=min(entry+0x70,(o+int(d.get('size','0')) if d else entry+0x100))
 for ins in pu.disasm(st,en-st):
  mark=' <<<CALL_TARGET' if ins.mnemonic=='call' and any(op.type==pu.X86_OP_IMM and (op.imm&0xffffffff)==target for op in ins.operands) else ''
  lines.append('0x%X: %-7s %s%s'%(ins.address,ins.mnemonic,ins.op_str,mark))
out=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17_K6\EVIDENCE\caller_context.txt'
open(out,'w',encoding='utf-8').write('\n'.join(lines)+'\n')
print('lines',len(lines))
