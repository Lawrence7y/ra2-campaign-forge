"""Generate per-row RING evidence for the final 8 S09-KPROVED6 rows.
Verifies: 2 all holding RTTI tables (from survey index), 4 direct sites
(E8 @ boundary, site+5+rel32==entry, out of body, non-self) or livevt,
and dumps disassembly with entry-relative offsets for 3b anchors.
"""
import json
from pathlib import Path
import pefile, capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

ROOT = Path(r'D:\Project\ra2-campaign-forge')
OUT = ROOT/'lead/next_re_20261117_r14/S09_KPROVED6'
raw = (ROOT/'ra2youli'/'gamemd.exe').read_bytes()
pe = pefile.PE(data=raw, fast_load=True); ib = pe.OPTIONAL_HEADER.ImageBase
secs = [dict(name=s.Name.rstrip(b'\0').decode('latin1'), va=ib+s.VirtualAddress,
             vs=s.Misc_VirtualSize, rs=s.SizeOfRawData, ptr=s.PointerToRawData) for s in pe.sections]
by = {s['name']:s for s in secs}
def va2off(va):
    for s in secs:
        if s['va'] <= va < s['va']+s['rs']:
            o=s['ptr']+va-s['va']
            if o+4<=len(raw): return o
    return None
def u32(va):
    o=va2off(va); return int.from_bytes(raw[o:o+4],'little') if o is not None else None
text=by['.text']; tva=text['va']; tlen=text['vs']; code=raw[text['ptr']:text['ptr']+tlen]
def in_text(v): return v is not None and tva<=v<tva+tlen
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
JCCS={'je','jne','jz','jnz','jg','jge','jl','jle','ja','jae','jb','jbe','js','jns','jo','jno','jp','jnp','jecxz','jcxz'}
sz=bytearray(tlen+16); kind=bytearray(tlen+16); tgt={}; insmap={}; bytes_at={}
RET=1;JMP=2;JCC=3;CALL=4
for ins in md.disasm(code,tva):
    o=ins.address-tva
    if o>=len(sz): break
    sz[o]=ins.size; insmap[o]=ins; bytes_at[o]=ins.bytes
    mn=ins.mnemonic
    if mn=='ret' or mn.startswith('ret'): kind[o]=RET
    elif mn=='jmp':
        kind[o]=JMP
        if ins.operands and ins.operands[0].type==X86_OP_IMM: tgt[o]=int(ins.operands[0].imm)&0xffffffff
    elif mn in JCCS:
        kind[o]=JCC
        if ins.operands and ins.operands[0].type==X86_OP_IMM: tgt[o]=int(ins.operands[0].imm)&0xffffffff
    elif mn=='call': kind[o]=CALL

def extent(entry,cap=8000):
    seen=set(); stack=[entry]; addrs=[]; lo=hi=entry; n=0
    while stack:
        a=stack.pop()
        while True:
            if not in_text(a) or a in seen: break
            o=a-tva; s=sz[o]
            if s==0: break
            seen.add(a); addrs.append(a); n+=1
            if n>cap: stack=[]; break
            if a<lo: lo=a
            if a+s>hi: hi=a+s
            k=kind[o]
            if k==RET: break
            if k==JMP:
                t=tgt.get(o)
                if t: stack.append(t)
                break
            if k==JCC:
                t=tgt.get(o)
                if t: stack.append(t)
                a=a+s; continue
            a=a+s
    return lo,hi,sorted(addrs)

idx=json.load(open(ROOT/'lead/next_re_20261117_r14/SURVEY_RING24/work/index.json'))
e2s={int(k,16):v for k,v in idx['entry2slots'].items()}
direct={int(k,16):v for k,v in idx['direct'].items()}
livevt={int(k,16):v for k,v in idx['livevt'].items()}
vtables={int(k,16):v for k,v in idx['vtables'].items()}

ROWS=['004F4240','004E25A0','0056BBE0','00656AC0','006A5030','0069DE00','005BDC80','005576A0']
EDIR=OUT/'EVIDENCE'
allrows=[]
for k in ROWS:
    e=int(k,16); lo,hi,addrs=extent(e); rset=set(addrs)
    lines=[]
    lines.append('ENTRY %s  CFG body=[%08X,%08X) size=%d ins=%d'%(k,lo,hi,hi-lo,len(addrs)))
    lines.append('')
    # (2) all holding tables
    slots=e2s.get(e,[])
    lines.append('== (2) ALL holding RTTI tables (survey index.entry2slots, all 1219 tables enumerated) ==')
    seen={}
    for vt,slot,cls in slots:
        seen.setdefault((vt,cls),[]).append(slot)
    for (vt,cls),sl in sorted(seen.items()):
        lines.append('  vt=%08X  slots=%s  class=%s  [vt-4]=COL %08X  COL+0xC->TD %08X  TD+8="%s"'%(
            vt, ','.join(map(str,sorted(sl))), cls, u32(vt-4) or 0,
            (u32((u32(vt-4) or 0)+0xC) or 0),
            (lambda td: (raw[va2off(td+8):va2off(td+8)+40].split(b'\x00')[0].decode('latin1') if td and va2off(td+8) else '?'))(u32((u32(vt-4) or 0)+0xC))))
    lines.append('  n_tables=%d  distinct_classes=%d'%(len(seen),len(set(c for vt,c in seen))))
    lines.append('')
    # (4) direct sites verify
    dc=direct.get(e,[])
    lines.append('== (4) direct call sites (verify E8@boundary, site+5+rel32==entry, outside body, non-self) ==')
    okdc=[]
    for s in dc:
        o=s-tva
        b=raw[by['.text']['ptr']+o:by['.text']['ptr']+o+5]
        rel=int.from_bytes(b[1:5],'little',signed=True)
        hit = (b[0]==0xE8) and ((s+5+rel)&0xffffffff==e) and (o in insmap) and insmap[o].mnemonic=='call' and not (lo<=s<hi)
        if hit: okdc.append(s)
        lines.append('  site=%08X bytes=%s rel32=%+d ->%08X E8@boundary=%s body_contains=%s %s'%(
            s,b.hex(),rel,((s+5+rel)&0xffffffff), (o in insmap and insmap[o].mnemonic=='call'), (lo<=s<hi), 'OK' if hit else 'REJECT'))
    lines.append('  direct sites OK=%d/%d'%(len(okdc),len(dc)))
    lv=livevt.get(e,[])
    if lv:
        lines.append('== (4) livevt dispatch (survey strict; g/vt/slot/install_site/disp_site) ==')
        for row in lv[:8]:
            lines.append('  g=%08X vt=%08X slot=%d install_site=%08X disp_site=%08X'%tuple(row))
        lines.append('  n_livevt=%d'%len(lv))
    lines.append('')
    # (3) disassembly with relative offsets
    lines.append('== (3) function body disassembly (entry-relative +0xNN) ==')
    for a in addrs:
        o=a-tva; ins=insmap.get(o)
        if ins is None: continue
        lines.append('  +%04X  %08X  %-8s %s'%(a-e,a,ins.mnemonic,ins.op_str))
    (EDIR/('RINGS_%s.txt'%k)).write_text('\n'.join(lines),encoding='utf-8')
    allrows.append(dict(k=k,e=e,lo=lo,hi=hi,size=hi-lo,nins=len(addrs),slots=slots,
                        direct_ok=okdc,direct_n=len(dc),livevt=lv,dis=[l for l in lines if l.startswith('  +')]))
json.dump(allrows,open(OUT/'work'/'rings.json','w'),ensure_ascii=False,indent=1)
print('wrote EVIDENCE/RINGS_*.txt for',len(ROWS),'rows')
for r in allrows:
    print(r['k'],'directOK',len(r['direct_ok']),'/',r['direct_n'],'livevt',len(r['livevt']),'tables',len(seen) if False else len(set((v,c) for v,s,c in r['slots'])))
