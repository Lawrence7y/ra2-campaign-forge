"""AUDIT7: build my own .text instruction index + find vtable install sites.

- full linear sweep with skipdata=True
- func_start(site): nearest preceding ret-with-padding boundary
- install sites for a vtable base: instructions whose imm32 == vt
"""
import sys, os, pickle, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work")
from core import *

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work"
CACHE = os.path.join(OUT, 'insns.pkl')


def build():
    recs = []          # (addr, size, mnem, opstr, bytes_hex, tuple(imm va operands))
    immmap = {}        # imm value -> [insn addr]
    calls = {}         # target -> [site addr]
    o = va2off(TEXT_LO)
    end = va2off(TEXT_HI)
    for insn in md.disasm(DATA[o:end], TEXT_LO):
        imms = []
        if insn.id != 0:  # real instruction (skipdata 'data' raises on .operands)
            for op in insn.operands:
                if op.type == 2:  # IMM
                    imms.append(op.imm)
                    immmap.setdefault(op.imm, []).append(insn.address)
            if insn.mnemonic in ('call', 'jmp') and imms:
                calls.setdefault(imms[0], []).append(insn.address)
        recs.append((insn.address, insn.size, insn.mnemonic,
                     insn.op_str, insn.bytes.hex(), tuple(imms), insn.id == 0))
    pickle.dump({'recs': recs, 'immmap': immmap, 'calls': calls}, open(CACHE, 'wb'))
    return {'recs': recs, 'immmap': immmap, 'calls': calls}


def load():
    if os.path.exists(CACHE):
        return pickle.load(open(CACHE, 'rb'))
    return build()


DB = None


def db():
    global DB
    if DB is None:
        DB = load()
    return DB


def func_start(site):
    """nearest preceding ret-with-padding boundary, walking the linear record list."""
    recs = db()['recs']
    lo, hi = 0, len(recs) - 1
    idx = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if recs[mid][0] <= site:
            idx = mid
            lo = mid + 1
        else:
            hi = mid - 1
    # walk backwards for a ret whose next bytes are padding
    for k in range(idx, -1, -1):
        a, sz, mn = recs[k][0], recs[k][1], recs[k][2]
        if mn.startswith('ret'):
            nxt = DATA[va2off(a + sz):va2off(a + sz) + 4]
            if all(x in (0xCC, 0x90, 0x00) for x in nxt) or len(nxt) < 4:
                return recs[k + 1][0] if k + 1 < len(recs) else None
    return TEXT_LO


def fmt(a):
    for r in db()['recs']:
        if r[0] == a:
            return f"{a:08X}  {r[4]:<24} {r[2]} {r[3]}"
    return f"{a:08X}  <not decoded>"


def dis_range(lo, hi):
    return [r for r in db()['recs'] if lo <= r[0] < hi]


def vt_installs(vt, sites_only=False):
    """all .text instructions with an imm32 operand == vt"""
    out = []
    for a in db()['immmap'].get(vt, []):
        for r in db()['recs']:
            if r[0] == a:
                out.append(r)
                break
    return out


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'build':
        build()
        print('built', len(db()['recs']), 'insns;', len(db()['immmap']), 'imm keys;', len(db()['calls']), 'call targets')
    else:
        print('insns', len(db()['recs']))
