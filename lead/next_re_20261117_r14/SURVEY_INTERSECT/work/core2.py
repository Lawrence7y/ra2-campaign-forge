"""SURVEY-THIRDB core: PE loader + self-written CFG extent + decode helpers.
Read-only on gamemd.exe. NO atlas dependency in extent or classification.
"""
import json, re, hashlib
from pathlib import Path
import pefile, capstone
from capstone.x86 import (X86_OP_IMM, X86_OP_MEM, X86_OP_REG,
                          X86_REG_EAX, X86_REG_AX, X86_REG_AL, X86_REG_AH,
                          X86_REG_ESP, X86_REG_EBP, X86_REG_EBX, X86_REG_ECX,
                          X86_REG_EDX, X86_REG_ESI, X86_REG_EDI)

ROOT = Path(r'D:\Project\ra2-campaign-forge')
EXE  = ROOT/'ra2youli'/'gamemd.exe'
OUT  = ROOT/'lead'/'next_re_20261117_r14'/'SURVEY_INTERSECT'

raw = EXE.read_bytes()
SHA = hashlib.sha256(raw).hexdigest().upper()
pe = pefile.PE(data=raw, fast_load=True)
pe.parse_data_directories()
IB = pe.OPTIONAL_HEADER.ImageBase

SECS = []
for s in pe.sections:
    SECS.append(dict(name=s.Name.rstrip(b'\0').decode('latin1'),
                     va=IB+s.VirtualAddress, vs=s.Misc_VirtualSize,
                     rs=s.SizeOfRawData, ptr=s.PointerToRawData))
BY = {s['name']: s for s in SECS}

def va2off(va):
    for s in SECS:
        if s['va'] <= va < s['va']+s['rs']:
            o = s['ptr'] + va - s['va']
            if o+4 <= len(raw):
                return o
    return None

def u32(va):
    o = va2off(va)
    if o is None: return None
    return int.from_bytes(raw[o:o+4], 'little')

def cstr(va, lim=200):
    o = va2off(va)
    if o is None: return ''
    b = raw[o:o+lim]; z = b.find(b'\0')
    if z >= 0: b = b[:z]
    try: return b.decode('ascii')
    except Exception: return ''

TEXT = BY['.text']; TVA = TEXT['va']; TLEN = TEXT['vs']; TEND = TVA+TLEN
CODE = raw[TEXT['ptr']:TEXT['ptr']+TLEN]
def in_text(v): return v is not None and TVA <= v < TEND

# ---------- imports (for ③b② error-code channel) ----------
IMPORTS = {}   # name -> [iat_va ...]
try:
    for e in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in e.imports:
            if imp.name:
                IMPORTS.setdefault(imp.name.decode('latin1'), []).append(imp.address)
except Exception:
    pass

def import_of(va):
    """which imported symbol sits at absolute address va (exact IAT slot)"""
    for n, lst in IMPORTS.items():
        if va in lst: return n
    return None

# ---------- full .text linear sweep: size / kind / branch target ----------
NN = TLEN + 16
SZ = bytearray(NN); KIND = bytearray(NN); TGT = {}
RET, JMP, JCC, CALL, OTHER = 1, 2, 3, 4, 0
JCCS = {'je','jne','jz','jnz','jg','jge','jl','jle','ja','jae','jb','jbe',
        'js','jns','jo','jno','jp','jnp','jcxz','jecxz','jecxz','loop','loope','loopne'}
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True; MD.skipdata = True

NINSN = 0
for ins in MD.disasm(CODE, TVA):
    NINSN += 1
    o = ins.address - TVA
    SZ[o] = ins.size
    mn = ins.mnemonic
    if mn.startswith('ret'): KIND[o] = RET
    elif mn == 'jmp':
        KIND[o] = JMP
        ops = ins.operands
        if len(ops) == 1 and ops[0].type == X86_OP_IMM:
            TGT[o] = int(ops[0].imm) & 0xffffffff
    elif mn in JCCS:
        KIND[o] = JCC
        ops = ins.operands
        if len(ops) == 1 and ops[0].type == X86_OP_IMM:
            TGT[o] = int(ops[0].imm) & 0xffffffff
    elif mn == 'call':
        KIND[o] = CALL

# ---------- jump-table resolution (atlas-independent) ----------
def jt_targets(ins):
    """resolve jmp dword ptr [reg*4 + disp] style tables -> list of targets"""
    ops = ins.operands
    if not ops: return []
    o = ops[0]
    if o.type != X86_OP_MEM: return []
    m = o.mem
    if m.index == 0 or m.scale != 4: return []
    if m.base != 0: return []
    base = int(m.disp) & 0xffffffff
    if m.disp < 0: return []
    out = []
    for k in range(0, 512):
        v = u32(base + 4*k)
        if v is None or not in_text(v):
            if k == 0: return []
            break
        out.append(v)
    return out

# ---------- on-demand decode for addresses the linear sweep desynced ----------
def ensure(a):
    """Make SZ/KIND/TGT valid at address a (linear sweep may have desynced on inline data)."""
    o = a - TVA
    if not (0 <= o < TLEN): return False
    if SZ[o]: return True
    for ins in MD.disasm(CODE[o:o+16], a):
        oo = ins.address - TVA
        SZ[oo] = ins.size
        mn = ins.mnemonic
        if mn.startswith('ret'): KIND[oo] = RET
        elif mn == 'jmp':
            KIND[oo] = JMP
            if len(ins.operands) == 1 and ins.operands[0].type == X86_OP_IMM:
                TGT[oo] = int(ins.operands[0].imm) & 0xffffffff
        elif mn in JCCS:
            KIND[oo] = JCC
            if len(ins.operands) == 1 and ins.operands[0].type == X86_OP_IMM:
                TGT[oo] = int(ins.operands[0].imm) & 0xffffffff
        elif mn == 'call':
            KIND[oo] = CALL
        return SZ[o] > 0
    return False


def extent(entry, cap=6000):
    """Self-written CFG extent. Returns (lo, hi, sorted addrs, blocks).

    Two byte-derived guards keep the closure inside one function (no atlas involved):
      (a) a *tail jmp* — if the first terminator reached linearly from the entry is an
          unconditional `jmp`, the whole body is that straight-line段: 这是纯转发/尾跳桩
          (e.g. adjustor thunk `sub [esp+4],4; jmp X`), 不跟随。
      (b) never follow an unconditional `jmp` into another byte-derived function entry
          (all E8 targets + all jump-table targets harvested from .text).
    """
    if not _entries_ready: build_jt()
    if not in_text(entry): return (entry, entry, [], [])
    ensure(entry)
    # guard (a): tail-jmp thunk probe
    a = entry; n = 0; tail = False
    while in_text(a) and n < cap:
        if not ensure(a): break
        o = a - TVA; s = SZ[o]
        if s == 0: break
        k = KIND[o]
        if k == JMP:
            t = TGT.get(o)
            if t is None or t != entry:
                tail = True
            break
        if k in (JCC, RET): break
        a = a + s; n += 1
    if tail:
        lo = entry; hi = entry
        addrs = []
        a = entry
        while in_text(a) and len(addrs) < cap:
            o = a - TVA; s = SZ[o]
            if s == 0: break
            addrs.append(a); hi = a+s; a = a+s
            if KIND[o] in (JMP, RET): break
        return (lo, hi, addrs, [(lo, hi)] if addrs else [])
    seen = set(); stack = [entry]; addrs = []
    lo = hi = entry; n = 0
    while stack:
        a = stack.pop()
        while True:
            if not in_text(a): break
            if a in seen: break
            if not ensure(a): break
            o = a - TVA
            s = SZ[o]
            if s == 0: break
            seen.add(a); addrs.append(a); n += 1
            if n > cap: stack = []; break
            if a < lo: lo = a
            if a+s > hi: hi = a+s
            k = KIND[o]
            if k == RET: break
            if k == JMP:
                t = TGT.get(o)
                if t is not None:
                    # tail-call guard: do NOT follow an unconditional jmp into another known
                    # function entry (thunks / tail calls), else the closure swallows the callee.
                    if t != entry and t in FUNC_ENTRIES: break
                    stack.append(t); break
                # possibly a jump table
                jt = TGT_JT.get(o)
                if jt:
                    stack.extend(jt); break
                break
            if k == JCC:
                t = TGT.get(o)
                if t is not None: stack.append(t)
                a = a+s
                continue
            a = a+s
    addrs.sort()
    blocks = []
    if addrs:
        st = prev = addrs[0]
        for a in addrs[1:]:
            if a != prev + SZ[prev-TVA]:
                blocks.append((st, prev+SZ[prev-TVA])); st = a
            prev = a
        blocks.append((st, prev+SZ[prev-TVA]))
    return (lo, hi, addrs, blocks)

# jump tables must be resolved lazily (needs disasm of the jmp insn)
TGT_JT = {}
_jt_ready = False
FUNC_ENTRIES = set()      # atlas-INDEPENDENT entry set: all E8 targets + all jump-table targets
_entries_ready = False

def build_jt():
    """Populate jump tables AND the byte-derived function-entry set (no atlas involved)."""
    global _jt_ready, _entries_ready
    if _jt_ready and _entries_ready: return
    entries = set()
    for ins in MD.disasm(CODE, TVA):
        if ins.mnemonic == 'jmp' and len(ins.operands) == 1 and ins.operands[0].type == X86_OP_MEM:
            t = jt_targets(ins)
            if t:
                TGT_JT[ins.address - TVA] = t
                entries.update(t)
        if ins.mnemonic == 'call' and ins.size == 5 and ins.bytes[0] == 0xE8:
            entries.add((ins.address + 5 + int.from_bytes(ins.bytes[1:5], 'little', signed=True)) & 0xffffffff)
    FUNC_ENTRIES.update(x for x in entries if in_text(x))
    _jt_ready = True; _entries_ready = True

# ---------- decode a function body into instruction records ----------
def decode_fn(blocks):
    """Decode each contiguous block; return list of (addr, mnemonic, ops, ins)."""
    out = []
    for (a0, a1) in blocks:
        if a1 <= a0: continue
        o0 = a0 - TVA; o1 = a1 - TVA
        chunk = CODE[o0:o1]
        cur = a0
        for ins in MD.disasm(chunk, a0):
            out.append(ins)
            cur = ins.address + ins.size
            if cur >= a1: break
    return out

# ---------- RTTI: is <vt> a vtable pointer? ----------
def rtti_class_of_vt(vt):
    """vt-4 = COL, [COL+0xC] = TD, TD+8 inline name starting .?AV/.?AU"""
    col = u32(vt-4) if vt and vt >= 4 else None
    if col is None: return None
    td = u32(col+0xC)
    if td is None: return None
    nm = cstr(td+8)
    if nm.startswith(('.?AV', '.?AU')): return nm
    return None

def is_code_va(v): return in_text(v)

# =====================================================================
# ②/④ global byte index (self-contained; NO atlas involvement)
#   ②-a RTTI      : vt tables [vt-4]=COL -> [COL+0xC]=TD -> TD+8 .?AV/.?AU ; vt[slot]==entry
#   ④-a direct    : E8 at instruction boundary, site+5+rel32==entry, site outside body, non-self
#   ④-b livevt    : install `mov [g],vt` (site1) + `call [reg+disp]` on g (site2),
#                   u32(vt+disp)==entry, site1!=site2, slot value identical across ALL vt on g
# =====================================================================
import collections as _col

VT_TABLES = {}                       # vt -> class name
ENTRY2SLOTS = _col.defaultdict(list)  # entry -> [[vt,slot,cls], ...]
DIRECT = _col.defaultdict(list)       # entry -> [site, ...]
INSTALLS = _col.defaultdict(list)     # global -> [[vt,site], ...]
DISPATCHES = _col.defaultdict(list)   # global -> [[disp,site], ...]
GLOBAL_VTS = _col.defaultdict(set)    # global -> {vt, ...}
LIVEVT = _col.defaultdict(list)       # entry -> [[g,vt,slot,site1,site2], ...]

_idx_ready = False

def _rtti_of_col(col):
    td = u32(col + 0xC)
    if td is None: return None
    nm = cstr(td + 8)
    if nm.startswith(('.?AV', '.?AU')): return (td, nm)
    return None

def build_index():
    global _idx_ready
    if _idx_ready: return
    RD = BY['.rdata']; DT = BY['.data']
    lo = RD['va']; hi = DT['va'] + DT['rs']
    for s in (RD, DT):
        base = (s['va'] + 3)//4*4; end = s['va'] + s['rs'] - 4
        for p in range(base, end, 4):
            col = u32(p)
            if col is None or col < lo or col > hi: continue
            r = _rtti_of_col(col)
            if r: VT_TABLES[p+4] = r[1]
    for vt, cls in VT_TABLES.items():
        k = 0
        while k < 700:
            v = u32(vt + 4*k)
            if v is None or v == 0 or not in_text(v): break
            ENTRY2SLOTS[v].append([vt, k, cls])
            k += 1
    win = _col.deque(maxlen=24)
    def rec_of(ins):
        a0 = a1 = None
        try: ops = ins.operands
        except Exception: return None
        if len(ops) > 0:
            o = ops[0]
            if o.type == X86_OP_MEM: a0 = ('M', None, (o.mem.base, o.mem.index, o.mem.disp, o.size))
            elif o.type == X86_OP_REG: a0 = ('R', o.reg, None)
            else: a0 = ('I', None, (int(o.imm) & 0xffffffff,))
        if len(ops) > 1:
            o = ops[1]
            if o.type == X86_OP_IMM: a1 = ('I', None, (int(o.imm) & 0xffffffff,))
            elif o.type == X86_OP_REG: a1 = ('R', o.reg, None)
            elif o.type == X86_OP_MEM: a1 = ('M', None, (o.mem.base, o.mem.index, o.mem.disp, o.size))
        return a0, a1
    for ins in MD.disasm(CODE, TVA):
        mn = ins.mnemonic
        r = rec_of(ins)
        if r is None:
            win.append((ins.address, '.byte', None, None)); continue
        a0, a1 = r
        if mn == 'call' and ins.size == 5 and ins.bytes[0] == 0xE8:
            tgt = (ins.address + 5 + int.from_bytes(ins.bytes[1:5], 'little', signed=True)) & 0xffffffff
            DIRECT[tgt].append(ins.address)
        if mn == 'mov' and a0 and a0[0] == 'M' and a1 and a1[0] == 'I':
            b, i, disp, sz = a0[2]
            if b == 0 and i == 0 and disp and sz == 4:
                v = a1[2][0]
                if not in_text(v) and v > 0x700000:
                    INSTALLS[disp & 0xffffffff].append([v, ins.address])
        if mn == 'mov' and a0 and a0[0] == 'M' and a1 and a1[0] == 'R':
            b, i, disp, sz = a0[2]
            if b == 0 and i == 0 and disp and sz == 4:
                g = disp & 0xffffffff; reg = a1[1]
                for (pa, pm, pa0, pa1) in reversed(win):
                    if pm == 'mov' and pa1 and pa0 and pa0[0] == 'R' and pa0[1] == reg:
                        if pa1[0] == 'I':
                            v = pa1[2][0]
                            if not in_text(v) and v > 0x700000:
                                INSTALLS[g].append([v, ins.address])
                        break
                    if pa1 and pa0 and pa0[0] == 'R' and pa0[1] == reg: break
        if mn == 'call' and a0 and a0[0] == 'M':
            b, i, disp, sz = a0[2]
            if b != 0 and i == 0 and disp >= 0 and disp % 4 == 0:
                g = None
                for (pa, pm, pa0, pa1) in reversed(win):
                    if pm == 'mov' and pa0 and pa0[0] == 'R' and pa0[1] == b and pa1 and pa1[0] == 'M':
                        mb, mi, md2, msz = pa1[2]
                        if mb == 0 and mi == 0 and md2: g = md2 & 0xffffffff
                        break
                    if pa1 and pa0 and pa0[0] == 'R' and pa0[1] == b and pa1[0] == 'I': break
                if g: DISPATCHES[g].append([disp, ins.address])
        win.append((ins.address, mn, a0, a1))
    for g, lst in INSTALLS.items():
        GLOBAL_VTS[g] = {v for v, s in lst}
        dl = DISPATCHES.get(g)
        if not dl: continue
        for vt, site1 in lst:
            for disp, site2 in dl:
                if site1 == site2: continue
                v = u32(vt + disp)
                if v is None or not in_text(v): continue
                LIVEVT[v].append([g, vt, disp // 4, site1, site2])
    _idx_ready = True

def slot_unanimous(g, vt, slot):
    """literal D-40 ④-b: this slot must take the SAME value across every table installed on g."""
    ref = u32(vt + 4*slot)
    for v2 in GLOBAL_VTS.get(g, ()):
        if u32(v2 + 4*slot) != ref: return False
    return True

def global_single_vt(g):
    return len(GLOBAL_VTS.get(g, ())) == 1

# =====================================================================
# ㉓ exclusion (R14_COMMON §8.6 条1 / §8.1 错源 ㉓)
#   `push <dtor>; call 0x7C978A`  =>  dtor is atexit-registered
#   a vtable installed INSIDE such a dtor is NOT a live vptr
# =====================================================================
ATEXIT_CALL = 0x7C978A
ATEXIT_DTORS = set()
_DTOR_BODIES = []
_atexit_ready = False

def build_atexit(cap=3000):
    """one streaming pass: collect `push <text-imm>` ..8 insns.. `call ATEXIT_CALL` pairs."""
    global _atexit_ready
    if _atexit_ready: return
    win = _col.deque(maxlen=9)
    for ins in MD.disasm(CODE, TVA):
        if ins.mnemonic == 'call' and ins.size == 5 and ins.bytes[0] == 0xE8:
            tgt = (ins.address + 5 + int.from_bytes(ins.bytes[1:5], 'little', signed=True)) & 0xffffffff
            if tgt == ATEXIT_CALL:
                for (pa, pm, pv) in win:
                    if pm == 'push' and pv is not None and in_text(pv):
                        ATEXIT_DTORS.add(pv)
        pv = None
        if ins.mnemonic == 'push' and len(ins.operands) == 1 and ins.operands[0].type == X86_OP_IMM:
            v = int(ins.operands[0].imm) & 0xffffffff
            if in_text(v): pv = v
        win.append((ins.address, ins.mnemonic, pv))
    for v in sorted(ATEXIT_DTORS):
        lo, hi, addrs, blocks = extent(v, cap=cap)
        _DTOR_BODIES.append((lo, hi, v))
    _atexit_ready = True

def in_atexit_dtor(site):
    build_atexit()
    return any(lo <= site < hi for lo, hi, v in _DTOR_BODIES)
