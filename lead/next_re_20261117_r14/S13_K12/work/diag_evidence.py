import bisect,json
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_IMM,X86_OP_MEM
ROOT=Path(r'D:\Project\ra2-campaign-forge'); OUT=ROOT/'lead/next_re_20261117_r14/S13_K12'
raw=(ROOT/'ra2youli/gamemd.exe').read_bytes()
pe=pefile.PE(data=raw,fast_load=True); ib=int(pe.OPTIONAL_HEADER.ImageBase)
secs=[{'n':s.Name.rstrip(b'\0').decode('latin1'),'v':ib+int(s.VirtualAddress),'rs':int(s.SizeOfRawData),'p':int(s.PointerToRawData)} for s in pe.sections]
def va2off(va):
    va&=0xffffffff
    for s in secs:
        if s['v']<=va<s['v']+s['rs']: return s['p']+va-s['v']
    return None
def u32(va):
    o=va2off(va)
    return int.from_bytes(raw[o:o+4],'little') if o is not None else 0
tx=[s for s in secs if s['n']=='.text'][0]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
insns=list(md.disasm(raw[tx['p']:tx['p']+tx['rs']],tx['v'])); addrs=[i.address for i in insns]; byaddr={i.address:i for i in insns}
rows=json.loads((OUT/'work/reverify_core.json').read_text(encoding='utf-8'))['rows']
STOP={'ret','jmp','hlt','ud2','int3'}
print('=== RING1 predecessor ===')
for r in rows:
    e=r['entry']; va=int(e,16); off=va2off(va)
    idx=bisect.bisect_left(addrs,va)-1; I=insns[idx] if idx>=0 else None
    prev=raw[off-16:off]
    falls=bool(I and I.address+I.size==va and I.mnemonic not in STOP)
    pi=('%s %s @%06X sz%d'%(I.mnemonic,I.op_str,I.address,I.size)) if I else 'NA'
    term=[hex(b) for b in prev[-8:] if b in (0xC3,0xC2,0xEB,0xE9,0xCC,0x90,0xC9)]
    print('%s falls=%s prev=%s hx=%s term=%s'%(e,falls,pi,prev.hex(),term))
print('=== RING4 install verify ===')
for r in rows:
    for s in r['ring4']['sites']:
        I=byaddr.get(s['install_site']); d='NA'; ok=False
        if I:
            d=I.mnemonic+' '+I.op_str
            if I.mnemonic=='mov' and len(I.operands)==2 and I.operands[0].type==X86_OP_MEM and I.operands[1].type==X86_OP_IMM:
                m=I.operands[0].mem
                ok=(m.base==0 and m.index==0 and m.disp==s['global'] and (int(I.operands[1].imm)&0xffffffff)==s['vt'])
        sv=u32(s['vt']+s['slot']*4)
        print('%s S%06X g%06X vt%06X sl%d I%06X ok=%s sv=%06X %s'%(r['entry'],s['site'],s['global'],s['vt'],s['slot'],s['install_site'],ok,sv,d))
print('=== BODY 0054E890 / 0054E9E0 ===')
for e in ['0054E890','0054E9E0']:
    va=int(e,16); off=va2off(va); print('---',e,'---')
    for x in md.disasm(raw[off:off+0xC0],va):
        print('%06X %-18s %s %s'%(x.address,x.bytes.hex(),x.mnemonic,x.op_str))
