"""S10-KPROVED3 own toolkit (core): PE load, RTTI vtable census, direct-call sweep,
CFG extent, ③b structural detector. Built independently from raw bytes.
No import from any other card. 2026-11-19.
"""
import struct, re
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_ESP, X86_REG_EBP

EXE = r'ra2youli\gamemd.exe'

class PE:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path)
        self.image = self.pe.get_memory_mapped_image()
        self.imgbase = self.pe.OPTIONAL_HEADER.ImageBase
        self.sects = []
        for s in self.pe.sections:
            nm = s.Name.decode('latin1').rstrip('\x00')
            self.sects.append((nm, self.imgbase + s.VirtualAddress,
                               self.imgbase + s.VirtualAddress + s.Misc_VirtualSize,
                               s.PointerToRawData, s.SizeOfRawData))
    def rva2off(self, rva):
        for nm, va0, va1, praw, sz in self.sects:
            v0 = va0 - self.imgbase
            if v0 <= rva < v0 + sz:
                return praw + (rva - v0)
        return None
    def va2off(self, va):
        return self.rva2off(va - self.imgbase)
    def u32va(self, va):
        o = self.va2off(va)
        if o is None or o + 4 > len(self.image):
            return None
        return struct.unpack_from('<I', self.image, o)[0]
    def bytesva(self, va, n):
        o = self.va2off(va)
        if o is None:
            return None
        return self.image[o:o + n]
    def sec_of_va(self, va):
        for nm, va0, va1, praw, sz in self.sects:
            if va0 <= va < va1:
                return nm
        return None
    def in_text(self, va):
        return self.sec_of_va(va) == '.text'
    def text_range(self):
        for nm, va0, va1, praw, sz in self.sects:
            if nm == '.text':
                return va0, va1
        return None


def rtti_name(pe, td):
    """TD+8 is inline mangled name string (tech⑦). Fail closed."""
    b = pe.bytesva(td + 8, 128)
    if not b:
        return None
    end = b.find(b'\x00')
    if end < 0:
        return None
    try:
        name = b[:end].decode('ascii')
    except UnicodeDecodeError:
        return None
    if name.startswith('.?AV') or name.startswith('.?AU'):
        return name
    return None


def parse_col(pe, col_va):
    sig = pe.u32va(col_va)
    td = pe.u32va(col_va + 0xC)
    if td is None or pe.va2off(td) is None:
        return None
    name = rtti_name(pe, td)
    if name is None:
        return None
    return {'col': col_va, 'td': td, 'name': name, 'sig': sig}


def census_vtables(pe):
    """Scan 4-aligned .rdata positions as vt-4 COL pointers; walk slots while .text."""
    rdata = [s for s in pe.sects if s[0] == '.rdata'][0]
    _, va0, va1, praw, sz = rdata
    vts = []
    entry_map = {}
    va = va0
    while va + 4 <= va1:
        col = pe.u32va(va)
        if col is not None and pe.va2off(col) is not None:
            parsed = parse_col(pe, col)
            if parsed:
                vt = va + 4
                slots = []
                s = 0
                while s <= 2000:
                    val = pe.u32va(vt + 4 * s)
                    if val is None or not pe.in_text(val):
                        break
                    slots.append(val)
                    entry_map.setdefault(val, []).append({
                        'vt': vt, 'slot': s, 'name': parsed['name'],
                        'col': parsed['col'], 'td': parsed['td'], 'byte_off': 4 * s})
                    s += 1
                vts.append({'vt': vt, 'col': col, 'td': parsed['td'],
                            'name': parsed['name'], 'nslots': len(slots)})
        va += 4
    return vts, entry_map


def disasm(pe, start, end, skipdata=True):
    code = pe.bytesva(start, max(1, end - start))
    if code is None:
        return []
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = skipdata
    return list(md.disasm(code, start))


def linear_extent(pe, entry, cap=6000):
    """Self-written linear disasm extent from entry until first ret/jmp-uncond chain stop.
    cap instructions. Used only as an independent cross-check on classification ext_hi."""
    ins = disasm(pe, entry, entry + cap * 8)
    out = []
    for i in ins:
        out.append(i)
        if i.mnemonic.startswith('ret') or (i.mnemonic == 'jmp' and i.op_str.startswith('0x')):
            break
    return out


# ---- ③b detector (four sufficient conditions + D-42 detail#1 guards) ----
HRESULT = {0x80004001, 0x80004002, 0x80004003, 0x80004005, 0x80070057, 0x8007000E}

def _is_stack(mem):
    return mem.base in (X86_REG_ESP, X86_REG_EBP)

def _switch_targets(pe, ins):
    """ins is ff /4 jmp [reg*4+table]. Return distinct .text targets."""
    ops = ins.operands
    if not ops or ops[0].type != X86_OP_MEM:
        return []
    m = ops[0].mem
    # table base = disp (absolute) since index*scale + disp, base typically none
    tbl = m.disp & 0xFFFFFFFF
    if not pe.va2off(tbl):
        return []
    tgts = []
    for k in range(0, 256):
        v = pe.u32va(tbl + 4 * k)
        if v is None or not pe.in_text(v):
            break
        tgts.append(v)
    return tgts

def has_complete_loop(ins_by_addr, branch_addr, target):
    addrs = sorted(ins_by_addr)
    span = [a for a in addrs if target <= a <= branch_addr]
    if not span or len(span) > 64:
        return False, 'span empty/too long'
    load = store = adv = False
    stores = []
    for a in span:
        i = ins_by_addr[a]
        ops = i.operands
        mems = [o for o in ops if o.type == X86_OP_MEM]
        if i.mnemonic in ('cmp', 'test', 'push') and mems:
            load = True
        if len(ops) >= 2 and ops[0].type == X86_OP_REG and mems:
            load = True
        if ops and ops[0].type == X86_OP_MEM and i.mnemonic in ('mov',) and not _is_stack(ops[0].mem):
            store = True
            stores.append((a, i.mnemonic, ops[0].mem.base, ops[0].mem.disp))
        if i.mnemonic in ('inc', 'dec') or (i.mnemonic in ('add', 'sub') and len(ops) == 2
                and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_IMM):
            adv = True
    return (load and store and adv), 'load=%s store=%s adv=%s ns=%d' % (load, store, adv, len(stores))

def detect_3b(pe, entry, ext_hi):
    """Return (strict, core, loose, hits, detail). core=only ①②③④; strict=incl guard#1."""
    insns = disasm(pe, entry, ext_hi)
    ins = {i.address: i for i in insns}
    addrs = sorted(ins)
    hits = dict(s1_switch=False, s2_errcode=False, s3_shape=False, s4_loop=False, s1b_guards=False)
    detail = {}
    # ③b① switch table
    for a in addrs:
        i = ins[a]
        if i.mnemonic == 'jmp' and i.bytes and i.bytes[0] == 0xFF:
            tg = _switch_targets(pe, i)
            if len(set(tg)) >= 3:
                hits['s1_switch'] = True
                detail['switch'] = dict(at=a - entry, n=len(set(tg)))
                break
    # ③b② falsifiable error/return convention (HRESULT compare in cmp)
    for a in addrs:
        i = ins[a]
        if i.mnemonic == 'cmp' and len(i.operands) == 2 and i.operands[1].type == X86_OP_IMM:
            imm = i.operands[1].imm & 0xFFFFFFFF
            if imm in HRESULT:
                hits['s2_errcode'] = True
                detail['errcode'] = dict(at=a - entry, imm='%08X' % imm)
                break
    # ③b③ memory shape: >=10 distinct field stores OR >=2 vt installs
    field_stores = set(); vt_installs = set()
    for a in addrs:
        i = ins[a]
        if i.mnemonic == 'mov' and len(i.operands) == 2 and i.operands[0].type == X86_OP_MEM \
                and i.operands[1].type == X86_OP_IMM and not _is_stack(i.operands[0].mem):
            field_stores.add((i.operands[0].mem.base, i.operands[0].mem.disp))
            imm = i.operands[1].imm & 0xFFFFFFFF
            if pe.va2off(imm):
                vt_installs.add(imm)
    if len(field_stores) >= 10 or len(vt_installs) >= 2:
        hits['s3_shape'] = True
        detail['shape'] = dict(fields=len(field_stores), vt=len(vt_installs))
    # ③b④ complete I/O loop (backward branch with load+store+advance)
    for a in addrs:
        i = ins[a]
        if i.mnemonic.startswith('j') and i.operands and i.operands[0].type == X86_OP_IMM:
            t = i.operands[0].imm & 0xFFFFFFFF
            if t < a and t >= entry:
                ok, why = has_complete_loop(ins, a, t)
                if ok:
                    hits['s4_loop'] = True
                    detail['loop'] = dict(branch=a - entry, target=t - entry, why=why)
                    break
    # ③b①' D-42 detail#1 guard chain (≥3 mutually exclusive gates, distinct actions,
    # no single common call target)
    for idx, a in enumerate(addrs):
        gates = []
        for b in addrs[idx:]:
            if b - a > 64 or len(gates) >= 4:
                break
            j = ins[b]
            if j.mnemonic.startswith('j') and j.operands and j.operands[0].type == X86_OP_IMM:
                gates.append(j)
        if len(gates) < 3:
            continue
        sigs = []; callsets = []
        for g in gates:
            t = g.operands[0].imm & 0xFFFFFFFF
            blk = [ins[x] for x in addrs if t <= x < t + 80][:14]
            calls = tuple(ins[x].operands[0].imm & 0xFFFFFFFF for x in [y.address for y in blk]
                          if ins[x].mnemonic == 'call' and ins[x].operands
                          and ins[x].operands[0].type == X86_OP_IMM)
            stores = tuple((ins[x].operands[0].mem.base, ins[x].operands[0].mem.disp)
                           for x in [y.address for y in blk]
                           if ins[x].mnemonic == 'mov' and ins[x].operands
                           and ins[x].operands[0].type == X86_OP_MEM
                           and not _is_stack(ins[x].operands[0].mem))
            mnems = tuple(y.mnemonic for y in blk if y.mnemonic not in ('push', 'jmp', 'ret'))
            real = bool(calls) or bool(stores) or any(y.mnemonic == 'ret' for y in blk)
            if not real:
                break
            sigs.append((calls, stores, mnems)); callsets.append(calls)
        if len(sigs) >= 3 and len(set(sigs)) >= 3:
            common = set(callsets[0])
            for c in callsets[1:]:
                common &= set(c)
            if not common:
                hits['s1b_guards'] = True
                detail['guards'] = dict(at=a - entry, n=len(gates), distinct=len(set(sigs)))
                break
    core_keys = ('s1_switch', 's2_errcode', 's3_shape', 's4_loop')
    core = any(hits[k] for k in core_keys)
    strict = core or hits['s1b_guards']
    # loose: D-42(A) outbound call + branch + >=2 field writes
    call = branch = False; fields = set()
    for a, i in ins.items():
        if i.mnemonic == 'call':
            call = True
        if i.mnemonic.startswith('j'):
            branch = True
        if i.mnemonic == 'mov' and len(i.operands) == 2 and i.operands[0].type == X86_OP_MEM \
                and not _is_stack(i.operands[0].mem):
            fields.add((i.operands[0].mem.base, i.operands[0].mem.disp))
    loose = call and branch and len(fields) >= 2
    return strict, core, loose, hits, detail


def full_text_sweep_calls(pe):
    """Sweep 100% .text for E8 at instruction boundary; return dict target -> [site,...].
    Use capstone linear sweep from section start with skipdata to get boundaries."""
    va0, va1 = pe.text_range()
    code = pe.bytesva(va0, va1 - va0)
    md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True
    targets = {}
    n_ins = 0; n_e8 = 0
    for i in md.disasm(code, va0):
        n_ins += 1
        if i.mnemonic == 'call' and i.bytes and i.bytes[0] == 0xE8 and len(i.bytes) == 5:
            n_e8 += 1
            rel = struct.unpack_from('<i', i.bytes, 1)[0]
            tgt = (i.address + 5 + rel) & 0xFFFFFFFF
            targets.setdefault(tgt, []).append(i.address)
    return targets, n_ins, n_e8
