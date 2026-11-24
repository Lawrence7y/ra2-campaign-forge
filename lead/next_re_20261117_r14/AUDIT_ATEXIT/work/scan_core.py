
# -*- coding: utf-8 -*-
"""AUDIT-ATEXIT scan_core: single-pass .text linear disasm + data pointer census.
Self-contained; no atlas dependency for the core facts."""
import pefile, capstone, json, struct, sys, os
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT = os.path.dirname(os.path.abspath(__file__))
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = []
for s in pe.sections:
    secs.append(dict(name=s.Name.decode().rstrip('\x00'),
                     va=IB+s.VirtualAddress, vsize=s.Misc_VirtualSize,
                     rawsize=s.SizeOfRawData, rawptr=s.PointerToRawData,
                     char=s.Characteristics))
data = open(EXE,'rb').read()
def raw2va(r):
    for s in secs:
        if s['rawsize'] and s['rawptr'] <= r < s['rawptr']+s['rawsize']:
            return s['va'] + (r - s['rawptr'])
    return None
def va2raw(v):
    for s in secs:
        if s['va'] <= v < s['va']+s['rawsize']:
            return s['rawptr'] + (v - s['va'])
    return None
def read(v,n):
    r = va2raw(v)
    if r is None or r+n > len(data): return None
    return data[r:r+n]
def dword(v):
    b = read(v,4)
    return None if b is None else struct.unpack('<I', b)[0]

TEXT = next(s for s in secs if s['name']=='.text')
TEXT_LO, TEXT_HI = TEXT['va'], TEXT['va']+TEXT['vsize']
DATA_SECS = [s for s in secs if s['name'] in ('.rdata','.data')]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

# ---- operand-model self check (card ⑲) ----
_probe = list(md.disasm(b'\x8b\x04\x88\xc2\x04\x00', 0x1000))[0]
assert not hasattr(_probe.operands[0], 'index'), '⑲ FAIL: op.index exists'
assert _probe.operands[0].mem.index == 0, '⑲: mem.index absent should be 0'

code = read(TEXT_LO, TEXT['vsize'])
insns = list(md.disasm(code, TEXT_LO))
print('insn count', len(insns), file=sys.stderr)

direct = {}      # target -> [(site, kind)]
immref = {}      # imm value -> [(site, mnem)]
memabs = {}      # abs data addr -> [(site, mnem)]
stores = []      # (site, imm_value, dest_kind, dest_abs)
atexit_calls = []  # (site,) of call 0x7C978A
push_before_atexit = []  # (site_of_push, pushed fn)
prev = None
n_call = 0
ndata = 0
for ins in insns:
    if ins.id == 0:            # skipdata pseudo-instruction
        ndata += 1
        prev = None
        continue
    mn = ins.mnemonic
    ops = ins.operands
    b0 = ins.bytes[0] if ins.bytes else 0
    if mn in ('call','jmp') or (mn.startswith('j') and len(mn)<=4) or mn=='loop':
        if ops and ops[0].type == X86_OP_IMM:
            tgt = ops[0].imm
            kind = 'call' if mn=='call' else ('jmp' if mn=='jmp' else 'jcc/loop')
            direct.setdefault(tgt, []).append((ins.address, kind))
            if mn == 'call':
                n_call += 1
                if tgt == 0x7C978A:
                    atexit_calls.append(ins.address)
                    if prev is not None and prev.mnemonic=='push' and prev.operands and prev.operands[0].type==X86_OP_IMM:
                        push_before_atexit.append((prev.address, prev.operands[0].imm))
    for o in ops:
        if o.type == X86_OP_IMM:
            v = o.imm
            if 0x400000 <= v < 0xC00000:
                immref.setdefault(v, []).append((ins.address, mn))
        elif o.type == X86_OP_MEM:
            if o.mem.base == 0 and o.mem.index == 0:
                a = o.mem.disp
                if 0x400000 <= a < 0xC00000:
                    memabs.setdefault(a, []).append((ins.address, mn))
    # store imm32 into memory (vptr install candidates)
    if len(ops)==2 and ops[0].type==X86_OP_MEM and ops[1].type==X86_OP_IMM and mn.startswith('mov'):
        v = ops[1].imm
        if 0x400000 <= v < 0xC00000:
            if ops[0].mem.base == 0 and ops[0].mem.index == 0:
                stores.append((ins.address, v, 'abs', ops[0].mem.disp))
            else:
                stores.append((ins.address, v, 'reg', None))
    prev = ins
print('skipdata pseudo-insns', ndata, file=sys.stderr)
print('direct targets', len(direct), 'immref', len(immref), 'memabs', len(memabs),
      'stores', len(stores), 'atexit calls', len(atexit_calls), file=sys.stderr)

# ---- data section code-pointer census ----
codepos = {}   # value(code va) -> [positions]
allpos = []    # sorted list of (pos, value) for code pointers
for s in DATA_SECS:
    raw = read(s['va'], s['rawsize'])
    if raw is None: continue
    n = s['rawsize']//4
    for i in range(n):
        v = struct.unpack_from('<I', raw, i*4)[0]
        if TEXT_LO <= v < TEXT_HI:
            pos = s['va'] + i*4
            codepos.setdefault(v, []).append(pos)
            allpos.append((pos, v, s['name']))
allpos.sort()
print('code ptr slots', len(allpos), 'distinct targets', len(codepos), file=sys.stderr)

# ---- runs of consecutive code pointers (candidate tables) ----
runs = []
cur_start = None; last = None; cur = []
for pos, v, sn in allpos:
    if last is not None and pos == last+4 and sn == cur[0][2]:
        cur.append((pos,v,sn))
    else:
        if cur: runs.append(cur)
        cur = [(pos,v,sn)]
    last = pos
if cur: runs.append(cur)
print('runs', len(runs), file=sys.stderr)

# ---- COL anchors (strict RTTI) ----
def is_col(p):
    """p points to a RTTI CompleteObjectLocator: [+0xC]->TD, TD+8 inline mangled name"""
    td = dword(p+0xC)
    if td is None or td < 0x400000: return None
    nm = read(td+8, 4)
    if nm is None: return None
    if nm[:3] == b'?AV' or nm[:4] == b'.?AV':
        # read full name
        buf = read(td+8, 200)
        s = buf.split(b'\x00')[0]
        try: return s.decode('ascii')
        except: return None
    return None
col_at = {}
for pos, v, sn in allpos:
    if pos-4 < 0: continue
    c = dword(pos-4)
    if c is None or c < 0x400000: continue
    nm = is_col(c)
    if nm: col_at[pos] = (c, nm)
print('COL-anchored table starts', len(col_at), file=sys.stderr)

out = dict(secs=secs, text=[TEXT_LO, TEXT_HI],
           direct={str(k):v for k,v in direct.items()},
           immref={str(k):v for k,v in immref.items()},
           memabs={str(k):v for k,v in memabs.items()},
           stores=stores, atexit_calls=atexit_calls, push_before_atexit=push_before_atexit,
           codepos={str(k):v for k,v in codepos.items()},
           runs=[[(p,v,s) for p,v,s in r] for r in runs],
           col_at={str(k):v for k,v in col_at.items()})
with open(os.path.join(OUT,'scan_core.json'),'w',encoding='utf8') as f:
    json.dump(out, f)
print('WROTE scan_core.json', file=sys.stderr)
