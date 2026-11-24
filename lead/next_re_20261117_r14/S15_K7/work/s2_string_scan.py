# -*- coding: utf-8 -*-
import sys,re
sys.path.insert(0, __import__('os').path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
from capstone.x86 import X86_OP_IMM, X86_OP_MEM
TARGETS=['006D0F00','006D6070','006E1830','006E4790','006E47C0','006E6310','006EA3E0','006F1920','0070F120','00721270','00727AA0','0072DDB0','0072DEF0','00751590','00752460','00763610','00763690']
def getstr(imm):
    try:s=p.cstr(imm,160)
    except Exception:return b''
    if len(s)>=2 and all(32<=c<127 for c in s):return s
    return b''
print('entry\tsite\tinsn\timm\tstring\twithin_first_ret')
for hx in TARGETS:
    va=int(hx,16); body=p.dis(va,0x1000,True); fr=body[-1][0]
    win=p.dis(va,0x600)
    for a,bb,s,i in win:
        imms=[]
        try:
            for op in i.operands:
                if op.type==X86_OP_IMM: imms.append(op.imm)
                elif op.type==X86_OP_MEM and op.mem.disp: imms.append(op.mem.disp)
        except Exception: pass
        seen=[]
        for imm in imms:
            if imm in seen: continue
            seen.append(imm)
            st=getstr(imm)
            if st:
                print(f'{hx}\t{a:08X}\t{s}\t{imm:#x}\t{st.decode("latin1")}\t{a<=fr}')
