# -*- coding: utf-8 -*-
# Independent binary analysis for S13-K11. Self-written; does not import K8/K10 work code.
import sys, os, json, struct, hashlib
import pefile
from capstone import *
from capstone.x86 import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
TARGETS = {
  "0040B820": {"slot":4,"kind":"FindItemIndex"},
  "0040F5E0": {"slot":3,"kind":"Clear"},
  "0040F760": {"slot":4,"kind":"FindItemIndex"},
  "0040FD30": {"slot":4,"kind":"FindItemIndex"},
  "0046B780": {"slot":4,"kind":"FindItemIndex"},
  "0048AE90": {"slot":4,"kind":"FindItemIndex"},
  "0054EA10": {"slot":4,"kind":"FindItemIndex"},
  "0062B1F0": {"slot":4,"kind":"FindItemIndex"},
  "0065C070": {"slot":4,"kind":"FindItemIndex"},
}

pe = pefile.PE(EXE, fast_load=True)
IMAGEBASE = pe.OPTIONAL_HEADER.ImageBase
raw = open(EXE,'rb').read()
sha = hashlib.sha256(raw).hexdigest()

# sections: list of (name, VA_start, VA_end, raw_ptr, raw_size, vsize)
secs=[]
for s in pe.sections:
    name = s.Name.rstrip(bytes([0])).decode('ascii','replace')
    va = IMAGEBASE + s.VirtualAddress
    secs.append((name, va, va+s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData, s.Misc_VirtualSize))
textsec = next(s for s in secs if s[0]=='.text')

def va2off(va):
    for n,a,b,pr,rs,vs in secs:
        if a <= va < b:
            off = pr + (va-a)
            if off < len(raw): return off
    return None

def read_bytes(va,n):
    o=va2off(va)
    if o is None: return None
    return raw[o:o+n]

def read_dword(va):
    b=read_bytes(va,4)
    if b is None or len(b)<4: return None
    return struct.unpack('<I',b)[0]

def read_cstr(va,maxn=300):
    o=va2off(va)
    if o is None: return None
    end=raw.find(bytes([0]),o,o+maxn)
    if end<0: end=o+maxn
    return raw[o:end].decode('ascii','replace')

# capstone disassembler (skipdata mandatory per discipline 2)
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

def disasm(entry, maxins=60, maxbytes=260):
    code = read_bytes(entry, maxbytes)
    out=[]
    for insn in md.disasm(code, entry):
        out.append({"addr":insn.address,"bytes":insn.bytes.hex(),"mn":insn.mnemonic,"op":insn.op_str})
        if len(out)>=maxins: break
        if insn.mnemonic.startswith('ret'): break
    return out

def collect_operands(insn):
    # list of (type, value) for immediate / displacement operands
    vals=[]
    for op in insn.operands:
        if op.type == X86_OP_IMM:
            vals.append(('imm', op.imm & 0xffffffff))
        elif op.type == X86_OP_MEM:
            if op.mem.base==0 and op.mem.index==0:
                vals.append(('disp', op.mem.disp & 0xffffffff))
    return vals

# Pre-disassemble .text linearly to know instruction boundaries and direct calls
# (linear sweep over .text; skipdata handles non-code). We collect E8 rel32 targets.
text_va = textsec[1]; text_end = textsec[2]
text_bytes = raw[textsec[3]:textsec[3]+textsec[4]]
direct_call_targets = {}  # target VA -> list of call insn VA
imm32_sites = {}           # imm value -> list of (insn_va, mnemonic, op_n)
insn_starts = set()
for insn in md.disasm(text_bytes, text_va):
    if insn.mnemonic.startswith('.'):  # skipdata placeholder
        continue
    insn_starts.add(insn.address)
    if insn.mnemonic == 'call' and insn.op_str.startswith('0x'):
        try:
            t=int(insn.op_str,16)
            direct_call_targets.setdefault(t,[]).append(insn.address)
        except: pass
    for typ,val in collect_operands(insn):
        if typ=='imm' or typ=='disp':
            imm32_sites.setdefault(val,[]).append((insn.address,insn.mnemonic,insn.op_str[:90]))

# Scan data sections for aligned dword occurrences of each target (vtable slot hits)
def scan_dword_hits(val):
    hits=[]
    for n,a,b,pr,rs,vs in secs:
        if n in ('.text',): continue
        # aligned dword scan across section raw range
        start=pr; end=pr+rs
        for off in range(start,end-3,4):
            v=struct.unpack_from('<I',raw,off)[0]
            if v==val:
                va=a+(off-pr)
                hits.append(va)
    return hits

def valid_rtti_vtable(vt):
    # returns (class_name, td_va, col_va) or None
    col=read_dword(vt-4)
    if col is None: return None
    sig=read_dword(col)
    if sig!=0: return None
    td=read_dword(col+0xC)
    if td is None: return None
    name=read_cstr(td+8)
    if not name or not name.startswith('.?A'): return None
    # td+0 should be a code ptr (vftable of TD) - sanity
    return (name, td, col)

result = {"exe":EXE,"exe_sha256":sha,"imagebase":hex(IMAGEBASE),"sections":[(s[0],hex(s[1]),hex(s[2])) for s in secs], "rows":{}}

for e,info in TARGETS.items():
    va=int(e,16)
    body=disasm(va)
    slot=info['slot']
    # vtable base candidates: hit_va - slot*4
    occ=scan_dword_hits(va)
    vtables=[]
    for hv in occ:
        vt=hv-slot*4
        r=valid_rtti_vtable(vt)
        if r:
            vtables.append({"slot_hit_va":hex(hv),"vt":hex(vt),"name":r[0],"td":hex(r[1]),"col":hex(r[2])})
    # dedupe by vt
    seen=set(); vt2=[]
    for v in vtables:
        if v['vt'] not in seen:
            seen.add(v['vt']); vt2.append(v)
    # live vptr installs: any instruction with an imm operand == any vt, pattern mov [disp32],imm32
    installs=[]
    for v in vt2:
        vtv=int(v['vt'],16)
        for (iva,mn,op) in imm32_sites.get(vtv,[]):
            installs.append({"vt":v['vt'],"insn":hex(iva),"mn":mn,"op":op})
    # direct calls to entry (E8 rel32), instruction-boundary counted
    dcalls = direct_call_targets.get(va,[])
    # raw byte scan for E8 with rel32 to entry (for cross-check)
    rawrel=[]
    for i in range(len(text_bytes)-4):
        if text_bytes[i]==0xE8:
            t=text_va+i+5+struct.unpack_from('<i',text_bytes,i+1)[0]
            if t==va: rawrel.append(hex(text_va+i))
    result['rows'][e]={
       "slot":slot,"kind":info['kind'],
       "body":body,
       "occurrences": [hex(x) for x in occ],
       "vtables":vt2,
       "installs":installs,
       "direct_calls":[hex(x) for x in dcalls],
       "direct_call_count":len(dcalls),
       "raw_e8_hits":rawrel,
    }

outp = os.path.join(os.path.dirname(os.path.abspath(__file__)),'ANALYSIS.json')
open(outp,'w',encoding='utf-8').write(json.dumps(result,ensure_ascii=False,indent=2))
print('WROTE',outp)
print('SHA256',sha,'size',len(raw))
for e,info in TARGETS.items():
    r=result['rows'][e]
    print('==',e,'slot',r['slot'],r['kind'],'dcall',r['direct_call_count'])
    for b in r['body'][:14]: print('   ',hex(b['addr']),b['mn'],b['op'],';',b['bytes'])
    for v in r['vtables']: print('   VT',v['vt'],'slot_hit',v['slot_hit_va'],'RTTI',v['name'])
    for ins in r['installs'][:6]: print('   INSTALL',ins['insn'],ins['mn'],ins['op'])
