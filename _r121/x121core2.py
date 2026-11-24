"""x121core2.py -- analysis helpers on top of an exact linear sweep.

Backward walking uses the sweep's instruction boundaries (no frame guessing).
capstone detail is enabled only for single instructions / small windows.
"""
import sys, struct, hashlib
sys.path.insert(0, '_r121')
import x121lib, x121sweep
import capstone

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True

XI = capstone.x86
REG_INVALID = XI.X86_REG_INVALID
OP_REG = XI.X86_OP_REG
OP_MEM = XI.X86_OP_MEM
OP_IMM = XI.X86_OP_IMM
ESP = XI.X86_REG_ESP

PE_PATH = 'ra2bench/gamemd.exe'


def load():
    return x121lib.PE(PE_PATH)


def raw(ins):
    return '%s %s' % (ins.mnemonic, ins.op_str)


def one(pe, va):
    """decode exactly one instruction at va (detail on)."""
    o = pe.off_va(va)
    if o is None:
        return None
    for ins in MD.disasm(pe.buf[o:o + 16], va, count=1):
        return ins
    return None


def back(sw, pe, va, n=12):
    """exact instruction chain ending exactly at va, oldest->newest, len<=n."""
    j = sw.index(va)
    if j < 0:
        return None
    chain = []
    cur = va
    k = j
    while len(chain) < n:
        ins = one(pe, cur)
        if ins is None or ins.address != cur:
            break
        chain.append(ins)
        prev_end = cur
        # find instruction whose end == cur
        if k == 0 or sw.va[k - 1] + sw.sz[k - 1] != prev_end:
            break
        k -= 1
        cur = sw.va[k]
    chain.reverse()
    return chain


def fwd(sw, pe, va, n=20):
    """exact chain starting at va."""
    j = sw.index(va)
    if j < 0:
        return None
    out = []
    k = j
    while len(out) < n and k < len(sw.va):
        ins = one(pe, sw.va[k])
        if ins is None:
            break
        out.append(ins)
        k += 1
    return out


def find_push_imm_sites(pe, imm, secname='.text'):
    s = next(x for x in pe.sections if x['name'] == secname)
    pat = b'\x68' + struct.pack('<I', imm & 0xffffffff)
    out = []
    i = s['raw']
    end = s['raw'] + s['vsize']
    while True:
        j = pe.buf.find(pat, i, end)
        if j < 0:
            break
        out.append(pe.image_base + s['va'] + (j - s['raw']))
        i = j + 1
    return out


def cc_func_start(pe, va, max_back=0x40000):
    return x121lib.find_cc_func_start(pe, va, max_back=max_back)


def call_class(pe, ins):
    ops = ins.operands
    if not ops:
        return dict(kind='C_OTHER', raw=raw(ins))
    op = ops[0]
    if op.type == OP_MEM:
        if op.mem.base == REG_INVALID and op.mem.index == REG_INVALID:
            ava = op.mem.disp & 0xffffffff
            nm = pe.iat_name(ava)
            d = dict(kind='A', abs=ava, raw=raw(ins))
            if nm:
                d['api'] = nm
                d['dll'] = pe.iat[ava][0]
            else:
                d['kind'] = 'A_NOT_IAT'
            return d
        return dict(kind='B',
                    base=ins.reg_name(op.mem.base) if op.mem.base != REG_INVALID else None,
                    index=ins.reg_name(op.mem.index) if op.mem.index != REG_INVALID else None,
                    disp=op.mem.disp, scale=op.mem.scale, raw=raw(ins))
    if op.type == OP_IMM:
        return dict(kind='C', target=op.imm & 0xffffffff, raw=raw(ins))
    if op.type == OP_REG:
        return dict(kind='C', reg=ins.reg_name(op.reg), target=None, raw=raw(ins))
    return dict(kind='C_OTHER', raw=raw(ins))


def regs_written(ins):
    try:
        _, w = ins.regs_access()
        return list(w)
    except Exception:
        return []


def nearest_write(pe, sw, va, regid, maxn=64):
    """nearest instruction before va that writes REGID (exact boundaries)."""
    j = sw.index(va)
    if j < 0:
        return None, 0
    k = j - 1
    walked = 0
    while k >= 0 and walked < maxn:
        ins = one(pe, sw.va[k])
        if ins is None:
            break
        walked += 1
        if regid in regs_written(ins):
            return ins, walked
        if sw.va[k] + sw.sz[k] != (sw.va[k + 1] if k + 1 < len(sw.va) else va):
            # boundary chain broken (resync point) -> stop
            if sw.va[k] + sw.sz[k] != va and k + 1 >= j:
                break
        k -= 1
    return None, walked


def reg_id(ins, name):
    for r in range(1, XI.X86_REG_ENDING):
        try:
            if ins.reg_name(r) == name:
                return r
        except Exception:
            pass
    return REG_INVALID


def iat_if_abs_mov(pe, ins):
    """if ins is `mov REG, dword ptr [abs]` -> return abs; else None."""
    if ins.mnemonic != 'mov' or len(ins.operands) != 2:
        return None
    d, s = ins.operands
    if d.type != OP_REG or s.type != OP_MEM:
        return None
    if s.mem.base != REG_INVALID or s.mem.index != REG_INVALID:
        return None
    return s.mem.disp & 0xffffffff


def find_ppv_pair(pe, sw, site, maxn=10):
    """(lea R,[esp+K] ... push R) before SITE; K is the ppv slot."""
    chain = back(sw, pe, site, n=maxn)
    if not chain or len(chain) < 2:
        return None
    # immediate predecessor must be push R (ppv push)
    prev = chain[-2]
    if prev.mnemonic != 'push' or len(prev.operands) != 1 or prev.operands[0].type != OP_REG:
        return None
    push_reg = prev.operands[0].reg
    for idx in range(len(chain) - 2, -1, -1):
        ins = chain[idx]
        if ins.mnemonic == 'lea' and len(ins.operands) == 2:
            d, s = ins.operands
            if d.type == OP_REG and d.reg == push_reg and s.type == OP_MEM \
                    and s.mem.base == ESP and s.mem.index == REG_INVALID:
                return dict(lea_addr=ins.address, push_addr=prev.address,
                            reg=ins.reg_name(push_reg), K=s.mem.disp,
                            adjacent=(prev.address == ins.address + ins.size),
                            raw='%s ... %s' % (raw(ins), raw(prev)),
                            nback=len(chain) - idx)
    return None


def first_slot_read(pe, sw, after_va, K, maxn=20):
    """first `mov REG, dword ptr [esp+K]` in maxn insns starting at after_va."""
    seq = fwd(sw, pe, after_va, n=maxn)
    if seq is None:
        return None
    for ins in seq:
        if ins.mnemonic != 'mov' or len(ins.operands) != 2:
            continue
        d, s = ins.operands
        if d.type != OP_REG or s.type != OP_MEM:
            continue
        if s.mem.base != ESP or s.mem.index != REG_INVALID or s.mem.disp != K:
            continue
        return dict(addr=ins.address, regname=ins.reg_name(d.reg), reg=d.reg,
                    raw=raw(ins), seq=seq)
    return None


def first_call_or_ret(pe, sw, va, maxn=20):
    seq = fwd(sw, pe, va, n=maxn)
    if seq is None:
        return None, seq
    for ins in seq:
        if ins.mnemonic == 'call':
            return ins, seq
        if ins.mnemonic.startswith('ret'):
            return ins, seq
    return None, seq


def consume_class(pe, ins):
    c = call_class(pe, ins)
    if ins.mnemonic.startswith('ret'):
        return dict(consume='RET-NO-CONSUME', call=c, raw=raw(ins))
    if c['kind'] == 'A':
        return dict(consume='API:%s' % c['api'], call=c, raw=raw(ins), dll=c['dll'])
    if c['kind'] == 'A_NOT_IAT':
        return dict(consume='NOT-IAT:%s' % hex(c['abs']), call=c, raw=raw(ins))
    if c['kind'] == 'B':
        return dict(consume='VTABLE:%d' % c['disp'], call=c, raw=raw(ins),
                    vt_base=c['base'], vt_index=c['index'])
    return dict(consume='OTHER:%s' % raw(ins), call=c, raw=raw(ins))


def resolve_base_reg_iat(pe, sw, call_ins, base_name, maxn=64):
    """supplementary: was the [base] register loaded from an IAT slot nearby?"""
    if not base_name:
        return None
    rid = reg_id(call_ins, base_name)
    if rid == REG_INVALID:
        return None
    ins, walked = nearest_write(pe, sw, call_ins.address, rid, maxn=maxn)
    if ins is None:
        return None
    ava = iat_if_abs_mov(pe, ins)
    info = dict(ins_raw=raw(ins), addr=hex(ins.address), walked=walked)
    if ava is not None:
        nm = pe.iat_name(ava)
        info['abs'] = hex(ava)
        if nm:
            info['api'] = nm
            info['dll'] = pe.iat[ava][0]
    return info


def sha(b):
    return hashlib.sha256(b).hexdigest()


def groups_by_hash(items):
    g = {}
    for addr, h in items:
        g.setdefault(h, []).append(addr)
    return g
