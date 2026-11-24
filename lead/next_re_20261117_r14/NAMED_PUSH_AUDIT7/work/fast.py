"""AUDIT7 fast index: precomputed maps from the linear .text sweep."""
import sys, os, pickle
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work")
from core import *

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work"
CACHE = os.path.join(OUT, 'fast.pkl')


def build():
    addrs = []
    recs = {}
    immmap = {}
    calls = {}
    memmap = {}
    o = va2off(TEXT_LO)
    end = va2off(TEXT_HI)
    for insn in md.disasm(DATA[o:end], TEXT_LO):
        imms = ()
        if insn.id != 0:
            lst = []
            for op in insn.operands:
                if op.type == 2:
                    lst.append(op.imm)
                    immmap.setdefault(op.imm, []).append(insn.address)
                elif op.type == 3 and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp != 0:
                    memmap.setdefault(op.mem.disp, []).append(insn.address)
            imms = tuple(lst)
            if insn.mnemonic in ('call', 'jmp') and imms:
                calls.setdefault(imms[0], []).append(insn.address)
        recs[insn.address] = (insn.mnemonic, insn.op_str, insn.bytes.hex(), imms)
        addrs.append(insn.address)
    # func boundaries: address just after each ret-with-padding
    bounds = []
    for a in addrs:
        mn, opstr, bh, imms = recs[a]
        if mn.startswith('ret'):
            sz = len(bh) // 2
            nxt = DATA[va2off(a + sz):va2off(a + sz) + 4]
            if all(x in (0xCC, 0x90, 0x00) for x in nxt) or len(nxt) < 4:
                bounds.append(a + sz)
    data = {'addrs': addrs, 'recs': recs, 'immmap': immmap, 'calls': calls, 'bounds': bounds, 'memmap': memmap}
    pickle.dump(data, open(CACHE, 'wb'))
    return data


DB = None


def db():
    global DB
    if DB is None:
        DB = pickle.load(open(CACHE, 'rb')) if os.path.exists(CACHE) else build()
    return DB


def func_start(site):
    import bisect
    b = db()['bounds']
    i = bisect.bisect_right(b, site) - 1
    return b[i] if i >= 0 else TEXT_LO


def body(fstart, limit=2000):
    """linear instructions from fstart until ret-with-padding."""
    d = db()
    recs = d['recs']
    out = []
    a = fstart
    steps = 0
    while a in recs and steps < limit:
        mn, opstr, bh, imms = recs[a]
        sz = len(bh) // 2
        if mn == 'data' or mn == '.byte':
            out.append((a, mn, opstr, bh, imms))
            a += sz
            steps += 1
            continue
        out.append((a, mn, opstr, bh, imms))
        if mn.startswith('ret'):
            nxt = DATA[va2off(a + sz):va2off(a + sz) + 4]
            if all(x in (0xCC, 0x90, 0x00) for x in nxt) or len(nxt) < 4:
                break
        a += sz
        steps += 1
    return out


def refs_imm(val):
    return sorted(db()['immmap'].get(val, []))


def calls_to(val):
    return sorted(db()['calls'].get(val, []))


def atexit_sites_for(f):
    """call 0x7C978A sites where f was pushed within the preceding 4 instructions"""
    d = db()
    out = []
    for csite in calls_to(0x7C978A):
        b = body(func_start(csite), limit=400)
        idxs = [i for i, r in enumerate(b) if r[0] == csite]
        if not idxs:
            continue
        i = idxs[0]
        for r in b[max(0, i - 4):i]:
            if f in r[4]:
                out.append(csite)
                break
    return out


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'build':
        d = build()
        print('insns', len(d['addrs']), 'immkeys', len(d['immmap']), 'calls', len(d['calls']), 'bounds', len(d['bounds']))
    else:
        print('insns', len(db()['addrs']))
