# -*- coding: utf-8 -*-
"""Focused: find function start for given sites by scanning backwards for ret/nop padding,
then dump the full function; check 'returns this' + delete signature. Read-only."""
import io, os, sys
import capstone
HERE=os.path.dirname(os.path.abspath(__file__)); R14=os.path.dirname(HERE)
ROOT=os.path.dirname(os.path.dirname(R14))
EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
PROBE=os.path.join(R14,"R16_PROBE_4FINAL")
sys.path.insert(0,PROBE); sys.dont_write_bytecode=True
import final as F
IB=F.IMAGE_BASE; img=F.Image(EXE); buf=img.buf
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
def dis(va,n):
    o=va-IB
    if o<0 or o>=len(buf): return []
    return list(md.disasm(bytes(buf[o:o+n]),va))
def find_start(site, back=0x200):
    best=None
    for off in range(back,0,-1):
        p=site-off-IB
        if p<0 or p>=len(buf): continue
        b=buf[p]
        if b in (0xC3,0xC2):
            q=p+(3 if b==0xC2 else 1)
            npad=0
            while q<len(buf) and buf[q] in (0x90,0xCC): npad+=1; q+=1
            if npad>=1:
                cand=IB+q
                if cand<site and (best is None or cand>best): best=cand
    return best
SITES={
 "006C6588":0x006C6588, "006C65FE":0x006C65FE, "007BA596":0x007BA596,
 "006F3130":0x006F3130, "006F4413":0x006F4413, "006F450D":0x006F450D,
 "00413D87":0x00413D87, "0041408A":0x0041408A,
 "00771E77":0x00771E77, "00771F28":0x00771F28,
}
out=[]
for tag,site in SITES.items():
    st=find_start(site)
    out.append('===== site %s : inferred start=%s ====='%(tag, ('%08X'%st) if st else 'NONE'))
    if st:
        ins=dis(st,(site-st)+0x40)
        for x in ins:
            mark=''
            if x.address==site: mark=' <<< SITE'
            if x.mnemonic in ('ret','retf'): mark+=' <<< RET'
            lo=x.op_str.lower()
            if '0x7f' in lo or '0x7e' in lo: mark+=' [vptr?]'
            if '0x7c8b3d' in lo: mark+=' [DELETE]'
            if 'test' in x.mnemonic and '[esp' in lo: mark+=' [test esp]'
            if x.mnemonic=='mov' and lo.startswith('eax,'): mark+=' [eax=]'
            out.append('  %08X: %-18s %s %s'%(x.address,x.bytes.hex(),'%s %s'%(x.mnemonic,x.op_str),mark))
    out.append('')
io.open(os.path.join(HERE,'func_dump.txt'),'w',encoding='utf-8').write('\n'.join(out))
print('written',len(out),'lines')
