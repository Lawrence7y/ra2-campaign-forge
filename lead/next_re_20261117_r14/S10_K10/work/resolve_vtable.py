from pathlib import Path
import sys,struct
sys.path.insert(0,str(Path(__file__).parent))
from scan_candidates import load
cov,atl,names,pe,data,image,off,string_at,md,dis=load()
def u32va(va):
 o=off(va)
 return struct.unpack_from('<I',data,o)[0] if o is not None else 0
def classname(vt):
 col=u32va(vt-4) or u32va(vt-8); td=u32va(col+0xc) if col else 0
 if not td:return ('','','')
 o=off(td+8)
 if o is None:return ('',format(col,'08X'),format(td,'08X'))
 raw=data[o:o+100]; z=raw.find(b'\0')
 s=raw[:z].decode('ascii','replace') if 0<z<100 else ''
 return (s,format(col,'08X'),format(td,'08X'))
slotoffs=[int(x,16) for x in sys.argv[2:]] or [0x5c]
for entry in sys.argv[1:2]:
 va=int(entry,16); pat=struct.pack('<I',va)
 print('\nENTRY',entry)
 poss=[]; start=0
 while True:
  i=data.find(pat,start)
  if i<0:break
  start=i+1
  rva=None
  for s in pe.sections:
   if s.PointerToRawData<=i<s.PointerToRawData+s.SizeOfRawData:
    rva=s.VirtualAddress+(i-s.PointerToRawData);break
  if rva is None:continue
  cur=image+rva
  for slotoff in slotoffs:
   if cur<slotoff:continue
   base=cur-slotoff
   cn,col,td=classname(base)
   if True:
    print(' vref %08X base %08X slotoff 0x%X class %s COL %s TD %s slot342=%08X slot320=%08X' % (cur,base,slotoff,cn,col,td,u32va(base+0x558),u32va(base+0x500)))
