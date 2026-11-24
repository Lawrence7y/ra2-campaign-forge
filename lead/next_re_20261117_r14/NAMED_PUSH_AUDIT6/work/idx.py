"""Function-boundary + reference index built from sweep.pkl."""
import core, pickle, bisect

D = pickle.load(open('sweep.pkl', 'rb'))
CALL_T = D['call_targets']
PUSH_I = D['push_imms']
IMM32 = D['imm32_refs']
STARTS = sorted(CALL_T.keys())


def func_range(va):
    """Approximate function extent: to the next known callee entry above va."""
    i = bisect.bisect_right(STARTS, va)
    nxt = STARTS[i] if i < len(STARTS) else core.TEXT_HI
    return va, nxt


def body(va, maxn=3000):
    """Disassemble within the function's known extent."""
    lo, hi = func_range(va)
    o = core.va2off(lo)
    out = []
    for insn in core.md.disasm(core.DATA[o:core.va2off(hi)], lo):
        out.append({'a': insn.address, 'b': insn.bytes.hex(),
                    't': insn.mnemonic + (' ' + insn.op_str if insn.op_str else ''),
                    'i': insn, 'skip': insn.id == 0})
        if len(out) >= maxn:
            break
    return out


def callers(va):
    return CALL_T.get(va, [])


def push_sites(va):
    return PUSH_I.get(va, [])


def refs(va):
    return IMM32.get(va, [])


def atexit_registered(fn):
    """push fn immediately followed by call 0x7C978A (MSVC atexit)."""
    res = []
    for s in push_sites(fn):
        for insn in core.md.disasm(core.DATA[core.va2off(s):core.va2off(s) + 12], s):
            if insn.mnemonic == 'call' and insn.operands and insn.operands[0].type == 2:
                if insn.operands[0].imm == 0x7C978A:
                    res.append((s, insn.address))
                break
    return res


def dis_at(va, n=60):
    out = []
    o = core.va2off(va)
    for insn in core.md.disasm(core.DATA[o:o + 400], va):
        out.append('%08X %-18s %s' % (insn.address, insn.bytes.hex(), insn.mnemonic + (' ' + insn.op_str if insn.op_str else '')))
        if len(out) >= n:
            break
    return out


WRITERS = {'mov', 'lea', 'xor', 'sub', 'add', 'and', 'or', 'pop', 'inc', 'dec',
           'movzx', 'movsx', 'neg', 'not', 'shl', 'shr', 'imul', 'xchg'}


def last_writer_of_reg(insns, reg, before=None):
    """Scan backwards for the last instruction that really writes `reg`."""
    cands = [x for x in insns if before is None or x['a'] < before]
    for x in reversed(cands):
        i = x['i']
        if i.id == 0:
            continue
        if i.mnemonic not in WRITERS:
            continue
        ops = i.operands
        if not ops:
            continue
        d = ops[0]
        if d.type == 1 and i.reg_name(d.reg) == reg:
            return x
    return None


if __name__ == '__main__':
    print('starts:', len(STARTS))
    for t in (0x006BB9A0, 0x006C0F40, 0x00629210):
        print('%08X range=%s callers=%s' % (t, ['%08X' % x for x in func_range(t)],
                                          ['%08X' % c for c in callers(t)][:6]))
