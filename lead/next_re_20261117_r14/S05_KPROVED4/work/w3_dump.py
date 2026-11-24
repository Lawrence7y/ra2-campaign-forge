# -*- coding: utf-8 -*-
"""S05-KPROVED4 · 逐函数反汇编 dump（入口相对偏移），供人工逐条核对。"""
import sys, capstone, ax_lib

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
md.detail = False

def dump(ent, maxbytes=0x4000):
    pe=ax_lib.load(); e=int(ent,16)
    code=pe.bytes_at(e,maxbytes)
    out=[]
    for i in md.disasm(code,e):
        off=i.address-e
        out.append('%08X  +0x%04X  %-8s %s' % (i.address,off,i.mnemonic,i.op_str))
        if i.mnemonic in ('ret','retf') and len(out)>3:
            nxt=i.address+i.size
            tail=pe.bytes_at(nxt,16) or b''
            if sum(1 for b in tail[:8] if b in (0xCC,0x90))>=5:
                break
    return out

if __name__=='__main__':
    for ent in sys.argv[1:]:
        lines=dump(ent)
        with open('DIS_%s.txt'%ent,'w',encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print('%s -> %d lines' % (ent,len(lines)))
