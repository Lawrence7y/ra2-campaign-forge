#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import re_lib as R
from capstone.x86 import X86_REG_ESP, X86_REG_EBP
for s in sys.argv[1:]:
 a=int(s,16); ins=list(R.MD.disasm(R.read(a,8000),a)); out=[]
 for i in ins:
  if i.id==0 or not i.operands: continue
  dst=i.operands[0]
  if i.mnemonic in ('mov','movzx','movsx','add','sub','and','or','xor','inc','dec','sete','setne') and dst.type==R.X86_OP_MEM:
   m=dst.mem
   if m.base in (X86_REG_ESP,X86_REG_EBP): continue
   if m.disp>=0x20:
    out.append(f'{i.address:08X} {i.mnemonic} {i.op_str}')
 print('\n==',s,'writes',len(out),'==')
 print('\n'.join(out[:60]))
