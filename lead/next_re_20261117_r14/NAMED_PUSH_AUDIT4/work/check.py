"""Full independent per-row check. usage: python check.py 006BF810"""
import sys, json, struct, bisect, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt

img = Img()
IDX = json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work\index.json"))
CALLS = [(a, t) for a, t in IDX['calls']]
IAT = [(a, t) for a, t in IDX['iat']]
REFS = {int(k, 16): v for k, v in IDX['refs'].items()}
STARTS = IDX['starts']
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
IAT_CRC = 0x7E15D8
IAT_CCI = 0x7E15FC

def fstart(a):
    i = bisect.bisect_right(STARTS, a) - 1
    return STARTS[i] if i >= 0 else None

def ins_at(a):
    l = img.dis(a, 15)
    return l[0] if l else None

def scan_dword(val, lo, hi):
    out = []
    b = img.read(lo, hi - lo)
    if not b:
        return out
    for i in range(0, len(b) - 3, 4):
        if struct.unpack_from('<I', b, i)[0] == val:
            out.append(lo + i)
    return out

def rtti_of(vt):
    col = img.u32(vt - 4)
    if not col:
        return None
    sig = img.u32(col)
    td = img.u32(col + 0xC)
    return dict(col=col, sig=sig, offset=img.u32(col + 4), cd=img.u32(col + 8),
                td=td, name=img.cstr(td + 8) if td else None)

def vts_containing(entry):
    """All (vt, slot_index, slot_va) where a data section holds entry as dword and
    the preceding COL looks valid."""
    out = []
    for name, base, vsz, praw, rsz in img.sections:
        if name in ('.text',):
            continue
        hi = base + max(vsz, rsz)
        for va in scan_dword(entry, base, hi):
            col = img.u32(va - 4)
            # vt = va - 4*k ; require COL valid for some k
            for k in range(1, 9):
                vt = va - 4 * k
                c = img.u32(vt - 4)
                if c and img.u32(c) == 1:
                    out.append((vt, k, va, img.cstr(img.u32(c + 0xC) + 8)))
                    break
    return out

def body(entry, limit=0x500):
    seen = {}
    work = [entry]
    visited = set()
    while work:
        a = work.pop()
        while a not in visited and len(visited) < 3000:
            visited.add(a)
            ins = ins_at(a)
            if not ins:
                break
            seen[a] = ins
            mn = ins.mnemonic
            if mn.startswith('ret') or mn in ('hlt',):
                break
            if mn == 'jmp':
                if ins.op_str.startswith('0x'):
                    a = int(ins.op_str, 16); continue
                break
            if mn.startswith('j') and ins.op_str.startswith('0x'):
                work.append(int(ins.op_str, 16))
            a = ins.address + ins.size
            if a - entry > limit:
                break
    return [seen[k] for k in sorted(seen)]

entry = int(sys.argv[1], 16)
R = dict(entry='%08X' % entry)

print("=" * 70)
print("ENTRY %08X" % entry)
print("=" * 70)

# ---------- ② ----------
print("\n[②] vtable occurrences (data sections, slot value == entry):")
cands = vts_containing(entry)
for vt, k, va, name in cands:
    print("   vt=%08X slot#%d slot_va=%08X  RTTI name=%s" % (vt, k, va, name))
R['②_cands'] = [("%08X" % vt, k, "%08X" % va, name) for vt, k, va, name in cands]

# dump the vt fully
for vt, k, va, name in cands:
    print("   vt %08X full table (16 slots):" % vt)
    for i in range(16):
        v = img.u32(vt + 4 * i)
        if v is None:
            break
        mark = ' <== ENTRY' if v == entry else ''
        if v == 0:
            break
        print("     [%2d] +%02X  %08X%s" % (i, 4 * i, v, mark))
    rt = rtti_of(vt)
    print("   RTTI: COL=%08X sig=%s offset=%s TD=%08X name=%s" % (
        rt['col'], rt['sig'], rt['offset'], rt['td'], rt['name']))

# ---------- ③b ----------
print("\n[③b] body:")
bd = body(entry)
for i in bd:
    print("   " + fmt(i))
print("\n   imm 0x8xxxxxxx codes:", ["%08X:%s" % (i.address, i.op_str) for i in bd
                                    if i.mnemonic == 'mov' and i.op_str.startswith('eax, 0x8')])
print("   rets:", ["%08X %s %s" % (i.address, i.bytes.hex(' '), i.op_str)
                   for i in bd if i.mnemonic.startswith('ret')])
qi = [i for i in bd if i.mnemonic == 'call' and i.op_str == 'dword ptr [eax]']
print("   QI-ish 'call [eax]':", ["%08X %s" % (i.address, i.bytes.hex(' ')) for i in qi])
print("   direct calls:", ["%08X->%s" % (i.address, i.op_str) for i in bd
                           if i.mnemonic == 'call' and i.op_str.startswith('0x')])
print("   indirect calls:", ["%08X %s %s" % (i.address, i.bytes.hex(' '), i.op_str)
                             for i in bd if i.mnemonic == 'call' and not i.op_str.startswith('0x')])
