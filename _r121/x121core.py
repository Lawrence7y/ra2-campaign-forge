"""x121core.py -- shared decoding helpers for R121 (self-written, no repo libs)."""
import sys, struct, hashlib
sys.path.insert(0, '_r121')
from x121lib import PE, find_cc_func_start
import capstone

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True
MD_LITE = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

PE_PATH = 'ra2bench/gamemd.exe'


def load():
    return PE(PE_PATH)


def decode(pe, va, maxbytes=0x100, maxn=300, md=None):
    """linear disasm of a small window; detail kept only for the window."""
    md = md or MD
    o = pe.off_va(va)
    if o is None:
        return []
    code = pe.buf[o:o + maxbytes]
    out = []
    for ins in md.disasm(code, va):
        out.append(ins)
        if ins.address + ins.size - va >= maxbytes or len(out) >= maxn:
            break
    return out


def decode_n(pe, va, n=1):
    return decode(pe, va, maxbytes=16 * n + 15, maxn=n)


def is_call(ins):
    return ins.mnemonic == 'call'


def is_ret(ins):
    return ins.mnemonic.startswith('ret')


X86_REG_INVALID = capstone.x86.X86_REG_INVALID
X86_OP_MEM = capstone.x86.X86_OP_MEM
X86_OP_REG = capstone.x86.X86_OP_REG
X86_OP_IMM = capstone.x86.X86_OP_IMM


def regname(ins, r):
    return ins.reg_name(r)


def find_insn_at(pe, va, maxback=0x100, maxn=16):
    """Backward-exact alignment: find a decode chain that lands exactly on va.

    Returns (chain, depth_used) with chain ordered oldest->newest, chain[-1]
    ending exactly at va.  Falls back to None.  This is a heuristic used only
    to recover pre-site context; uncertainty is reported.
    """
    best = None
    starts = []
    lo = max(va - maxback, 0x401000)
    for s in range(va - 1, lo - 1, -1):
        starts.append(s)
    for s in starts:
        o = pe.off_va(s)
        if o is None:
            continue
        code = pe.buf[o:o + min((va - s) + 16, 0x120)]
        chain = []
        ok = False
        for ins in MD.disasm(code, s):
            if ins.address + ins.size > va:
                break
            chain.append(ins)
            if len(chain) > maxn:
                break
            if ins.address + ins.size == va:
                ok = True
                break
        if ok and (best is None or len(chain) > len(best)):
            best = chain
            if len(best) >= maxn:
                break
    return best


def call_class(pe, ins):
    """classify a call instruction per card rules."""
    ops = ins.operands
    if not ops:
        return dict(kind='C_OTHER', raw=raw(ins))
    op = ops[0]
    if op.type == X86_OP_MEM:
        base = op.mem.base
        idx = op.mem.index
        disp = op.mem.disp
        if base == X86_REG_INVALID and idx == X86_REG_INVALID:
            va = disp & 0xffffffff
            nm = pe.iat_name(va)
            if nm:
                return dict(kind='A', reg=None, disp=None, abs=va,
                            api=nm, dll=pe.iat[va][0], raw=raw(ins))
            return dict(kind='A_NOT_IAT', reg=None, disp=None, abs=va, raw=raw(ins))
        b = ins.reg_name(base) if base != X86_REG_INVALID else None
        i = ins.reg_name(idx) if idx != X86_REG_INVALID else None
        return dict(kind='B', reg=b, index=i, disp=disp, scale=op.mem.scale, raw=raw(ins))
    if op.type == X86_OP_IMM:
        return dict(kind='C', target=op.imm & 0xffffffff, raw=raw(ins))
    if op.type == X86_OP_REG:
        return dict(kind='C', target=None, reg=ins.reg_name(op.reg), raw=raw(ins))
    return dict(kind='C_OTHER', raw=raw(ins))


def raw(ins):
    return '%s %s' % (ins.mnemonic, ins.op_str)


def first_call_after(pe, va, span=64):
    for ins in decode(pe, va, maxbytes=span):
        if ins.address >= va and is_call(ins):
            return ins
    return None


def last_write_to(pe, reg, va, maxback=0x100, maxn=16):
    """last instruction writing REG strictly before VA, via exact-landing chain."""
    chain = find_insn_at(pe, va, maxback=maxback, maxn=maxn)
    if not chain:
        return None, None
    for ins in reversed(chain):
        try:
            _, w = ins.regs_access()
        except Exception:
            _, w = [], [capstone.x86.X86_REG_INVALID]
        if reg in w:
            return ins, chain
    return None, chain


def resolve_reg_cache(pe, reg, va, maxback=0x400):
    """If last write to REG is `mov REG, dword ptr [abs]` and abs in IAT -> name."""
    ins, chain = last_write_to(pe, reg, va, maxback=maxback, maxn=24)
    if ins is None:
        return dict(found=False, why='no-write-in-window')
    info = dict(found=True, ins_raw=raw(ins), addr=hex(ins.address),
                mnem=ins.mnemonic, ops=ins.op_str)
    if ins.mnemonic == 'mov' and len(ins.operands) == 2:
        d, s = ins.operands
        if s.type == X86_OP_MEM and s.mem.base == X86_REG_INVALID and s.mem.index == X86_REG_INVALID:
            ava = s.mem.disp & 0xffffffff
            info['abs'] = hex(ava)
            nm = pe.iat_name(ava)
            if nm:
                info['api'] = nm
                info['dll'] = pe.iat[ava][0]
                return info
            info['not_iat'] = True
    return info


def find_ppv_slot(pe, site, maxback=0x40):
    """last (lea R,[esp+K]; push R) adjacent pair before SITE."""
    chain = find_insn_at(pe, site, maxback=maxback, maxn=24)
    if not chain:
        return None
    hit = None
    for i in range(len(chain) - 1):
        a, b = chain[i], chain[i + 1]
        if a.mnemonic != 'lea' or b.mnemonic != 'push':
            continue
        if len(a.operands) != 2 or len(b.operands) != 1:
            continue
        d, s = a.operands
        if d.type != X86_OP_REG or s.type != X86_OP_MEM:
            continue
        if s.mem.base != capstone.x86.X86_REG_ESP or s.mem.index != X86_REG_INVALID:
            continue
        if b.operands[0].type != X86_OP_REG or b.operands[0].reg != d.reg:
            continue
        hit = dict(addr=hex(a.address), reg=a.reg_name(d.reg), K=s.mem.disp,
                   raw='%s ; %s' % (raw(a), raw(b)))
    return hit


def find_slot_read(pe, va, K, maxn=20):
    """first `mov REG, dword ptr [esp+K]` in the window of maxn insns after VA."""
    seq = decode(pe, va, maxbytes=0x100, maxn=maxn)
    for ins in seq:
        if ins.mnemonic != 'mov' or len(ins.operands) != 2:
            continue
        d, s = ins.operands
        if d.type != X86_OP_REG or s.type != X86_OP_MEM:
            continue
        if s.mem.base != capstone.x86.X86_REG_ESP or s.mem.index != X86_REG_INVALID:
            continue
        if s.mem.disp != K:
            continue
        return dict(addr=ins.address, reg=d.reg, regname=ins.reg_name(d.reg),
                    raw=raw(ins), seq=seq)
    return None


def consume_after(pe, va_start, K, maxn=20):
    """Q2 steps 2)-3): find slot read then first call/ret, classify consumption."""
    r = find_slot_read(pe, va_start, K, maxn=maxn)
    if r is None:
        return dict(slot_read=None, consume='NO-SLOT-READ')
    seq = r['seq']
    started = False
    for ins in seq:
        if not started:
            if ins.address == r['addr']:
                started = True
            continue
        if is_call(ins):
            c = call_class(pe, ins)
            if c['kind'] == 'A':
                return dict(slot_read=r, consume='API:%s' % c['api'], call=c, at=hex(ins.address))
            if c['kind'] == 'B':
                if c['disp']:
                    return dict(slot_read=r, consume='VTABLE:%d' % c['disp'], call=c, at=hex(ins.address))
                ext = resolve_reg_cache(pe, capstone.x86.X86_REG_EBP if False else reg_id(pe, ins, c['reg']), ins.address)
                return dict(slot_read=r, consume='OTHER:%s' % c['raw'], call=c,
                            at=hex(ins.address), reg_path=ext)
            return dict(slot_read=r, consume='OTHER:%s' % c['raw'], call=c, at=hex(ins.address))
        if is_ret(ins):
            return dict(slot_read=r, consume='RET-NO-CONSUME', at=hex(ins.address))
    return dict(slot_read=r, consume='WINDOW-END-NO-CONSUME', at=None)


def reg_id(pe, ins, name):
    for r in range(capstone.x86.X86_REG_ENDING):
        try:
            if ins.reg_name(r) == name:
                return r
        except Exception:
            pass
    return capstone.x86.X86_REG_INVALID


def find_push_imm_sites(pe, imm, secname='.text'):
    s = next(x for x in pe.sections if x['name'] == secname)
    pat = b'\x68' + struct.pack('<I', imm & 0xffffffff)
    start = s['raw']
    end = s['raw'] + s['vsize']
    out = []
    i = start
    while True:
        j = pe.buf.find(pat, i, end)
        if j < 0:
            break
        out.append(pe.image_base + s['va'] + (j - s['raw']))
        i = j + 1
    return out


def hexs(v):
    return '0x%08x' % v if isinstance(v, int) else v
