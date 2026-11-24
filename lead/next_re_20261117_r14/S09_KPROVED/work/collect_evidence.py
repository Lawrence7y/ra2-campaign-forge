#!/usr/bin/env python3
"""S09-KPROVED full evidence collector. Read-only on target; writes only EVIDENCE/.
- Full .text linear sweep (skipdata=True) -> E8 calls at instruction boundaries.
- For 8 entries: independent direct-call site discovery + verification.
- Full disassembly dump per entry (for ③b), RTTI chain dump per entry.
"""
import csv, struct, os
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
CLASS = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv'
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED'
EV = os.path.join(BASE, 'EVIDENCE')
os.makedirs(EV, exist_ok=True)

ENTRIES = ['004AAE90','005BDF70','006A5310','004AB9B0','0063FEA0','006A7780','004ACE70','006ABD30']

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
D = pe.__data__
SEC = [(s.Name.rstrip(b'\x00').decode(), s.VirtualAddress, max(s.Misc_VirtualSize,s.SizeOfRawData), s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
def va2off(va):
    rva = va - IB
    for nm,v,sz,p,raw in SEC:
        if v <= rva < v+sz:
            off = p + (rva-v)
            if off < len(D): return off
    return None
def u32(va):
    o=va2off(va)
    return None if o is None or o+4>len(D) else struct.unpack_from('<I',D,o)[0]
def i32(va):
    x=u32(va); return None if x is None else (x-0x100000000 if x>=0x80000000 else x)
def u8(va):
    o=va2off(va); return None if o is None else D[o]
def cstr(va,n=120):
    o=va2off(va)
    if o is None: return '<UNMAPPED>'
    e=D.find(b'\x00',o,o+n)
    if e<0: return '<NO-NUL>'
    try: return D[o:e].decode('ascii')
    except: return '<NONASCII>'

# ---- locate .text ----
txt = [s for s in SEC if s[0]=='.text'][0]
txt_va = IB + txt[1]; txt_sz = txt[2]
txt_off = txt[3]
print('.text', hex(txt_va), 'size', txt_sz)

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True
code = D[txt_off:txt_off+txt_sz]

# full linear sweep -> all E8 call sites at instruction boundaries
call_targets = {}  # target VA -> list of site VA
n_insn = 0; n_e8 = 0
with open(os.path.join(EV,'text_e8_sites.tsv'),'w',encoding='utf-8') as fe8:
    fe8.write('site_hex\tbyte\ttarget_hex\n')
    for ins in md.disasm(code, txt_va):
        n_insn += 1
        if ins.mnemonic=='call' and len(ins.bytes)>=5 and ins.bytes[0]==0xE8:
            rel = struct.unpack_from('<i', ins.bytes,1)[0]
            tgt = ins.address + 5 + rel
            n_e8 += 1
            call_targets.setdefault(tgt, []).append(ins.address)
            fe8.write('%08X\tE8\t%08X\n' % (ins.address, tgt))
print('insn', n_insn, 'E8@boundary', n_e8)

# ---- classification lookup ----
crows={}
with open(CLASS, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        crows[r['entry']]=r

# per-entry evidence
summary=[]
for e in ENTRIES:
    entry=int(e,16); r=crows[e]
    vt=int(r['rtti_vt'],16); slot=int(r['rtti_slot'])
    eline=[]
    eline.append('=== entry %s (%s) ===' % (e, r['name']))
    # --- ② chain ---
    col=u32(vt-4); td=u32(col+0xC) if col else None; nm=cstr(td+8) if td else None
    sv=u32(vt+slot*4)
    eline.append('② vt=0x%08X slot=%d' % (vt,slot))
    eline.append('  [vt-4]=[0x%08X]=0x%08X (COL)' % (vt-4, col or 0))
    eline.append('  [COL+0xC]=[0x%08X]=0x%08X (TD)' % ((col or 0)+0xC, td or 0))
    eline.append('  [TD+8]=[0x%08X]="%s"' % ((td or 0)+8, nm))
    eline.append('  vt[slot]=[0x%08X]=0x%08X ; ==entry? %s' % (vt+slot*4, sv or 0, sv==entry))
    LOG2 = bool(col and td and nm and nm.startswith(('.?AV','.?AU')) and sv==entry)
    # --- ④ direct sites (independent) ---
    sites = call_targets.get(entry, [])
    ext_lo=int(r['ext_lo'],16); ext_hi=int(r['ext_hi'],16)
    eline.append('④ independent E8 sites at boundary targeting entry: %d' % len(sites))
    ok4=[]
    for s in sites:
        b=u8(s); rel=i32(s+1); tgt=s+5+rel
        inbody = ext_lo <= s < ext_hi
        selflp = (s>=entry and s<max(ext_hi,entry+1))
        good = (b==0xE8 and tgt==entry and not inbody and not selflp)
        eline.append('  site 0x%08X byte=%02X rel=%d tgt=0x%08X inbody=%s non-self=%s => %s' %
                     (s, b or 0, rel or 0, tgt, inbody, not selflp, 'OK' if good else 'REJECT'))
        if good: ok4.append(s)
    # classification-declared sites for cross-check
    decl = r['ring4_direct_sites'].split(';') if r['ring4_direct_sites'] else []
    eline.append('  classification-declared sites: %s' % (','.join(decl) if decl else '(none)'))
    LOG4 = len(ok4)>0
    # --- full disassembly dump ---
    o=va2off(entry)
    hi=ext_hi if ext_hi>entry else entry+64
    dis_code=D[o:o+(hi-entry)]
    with open(os.path.join(EV,'dis_%s.txt'%e),'w',encoding='utf-8') as fd:
        fd.write('; entry %s  %s  extent 0x%08X..0x%08X\n'%(e,r['name'],entry,hi))
        for ins in md.disasm(dis_code, entry):
            fd.write('%08X  %-20s %-8s %s\n' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    eline.append('  disasm -> EVIDENCE/dis_%s.txt (%d bytes body)'%(e,hi-entry))
    with open(os.path.join(EV,'rtti_%s.txt'%e),'w',encoding='utf-8') as fr:
        fr.write('\n'.join(eline)+'\n')
    summary.append((e,LOG2,LOG4,len(sites),len(ok4),nm,ext_lo,ext_hi))

print('=== SUMMARY ===')
for e,l2,l4,ns,nok,nm,lo,hi in summary:
    print('%s  ②=%s ④=%s sites=%d ok=%d  name=%s extent=%08X..%08X'%(e,l2,l4,ns,nok,nm,lo,hi))
