"""Find immediate operands equal to Locomotion vtable addresses in .text (constructor stores).
Byte-level channel: scan .text for 4-byte LE immediates of main/off4 vtables, then report the
surrounding instruction context via capstone."""
from pehelp import *
import struct
vt_names={0x7E7F7C:'Drive main',0x7E7EB0:'Drive off4',0x7E7E8C:'Drive off24',
          0x7F6AC4:'Walk main',0x7EAEC0:'LocoClass main',0x7EADF4:'LocoClass off4'}
with open(EXE,'rb') as f: blob=f.read()
text=[s for s in PE.sections if s.Name.rstrip(b'\0').decode().lower()=='.text'][0]
lo=text.PointerToRawData; hi=lo+text.SizeOfRawData
for va,name in vt_names.items():
    pat=struct.pack('<I',va)
    off=lo; cnt=0
    positions=[]
    while True:
        i=blob.find(pat,off,hi)
        if i<0: break
        # map file offset back to VA
        v=IMAGE_BASE+text.VirtualAddress+(i-lo)
        positions.append(v); off=i+1; cnt+=1
        if cnt>15: break
    print('%08X %-18s imm-hits=%d: %s'%(va,name,cnt,' '.join('0x%X'%p for p in positions[:12])))
