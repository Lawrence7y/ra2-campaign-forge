"""Parse host 006BB9A0: all (operator new size, ctor, CLSID) registration blocks."""
import sys, json, struct, bisect
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt
img = Img()
IDX = json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work\index.json"))
CALLS = {(a, t) for a, t in IDX['calls']}
IATC = {(a, t) for a, t in IDX['iat']}

def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None

HOST = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x6BB9A0
# linear sweep host up to next known function start; use 0x1000 window
end = HOST + 0x1800
a = HOST
seq = []
while a < end:
    i = ins_at(a)
    if not i: break
    seq.append(i)
    a += i.size
    if i.mnemonic == 'ret' and i.address > HOST + 0x100:
        break

print("host %08X sweeping %d insns" % (HOST, len(seq)))
# find esi load
for i in seq[:80]:
    if 'esi' in i.op_str and i.address < HOST + 0x100:
        print("  prologue: " + fmt(i))

blocks = []
for n, i in enumerate(seq):
    if i.mnemonic == 'call' and i.op_str == 'dword ptr [0x7e15d8]' or (i.mnemonic == 'call' and i.op_str == 'esi'):
        # look back for push <clsid imm>
        clsid = None
        for k in range(n - 1, max(n - 8, 0), -1):
            j = seq[k]
            if j.mnemonic == 'push' and j.op_str.startswith('0x'):
                v = int(j.op_str, 16)
                if 0x7E1000 <= v < 0x812000:
                    clsid = v
                    break
        # find preceding ctor call (nearest direct call before)
        ctor = None
        ctor_at = None
        for k in range(n - 1, max(n - 14, 0), -1):
            j = seq[k]
            if j.mnemonic == 'call' and j.op_str.startswith('0x'):
                t = int(j.op_str, 16)
                if t != 0x7c8e17:
                    ctor = t
                    ctor_at = j.address
                    break
        blocks.append((i.address, clsid, ctor_at, ctor))

print("\nregistration blocks (call -> clsid -> ctor):")
for addr, clsid, ctor_at, ctor in blocks:
    tag = ''
    print("  callCRC=%08X  clsid=%s  ctor@%s -> %s" % (
        addr, '%08X' % clsid if clsid else 'None',
        '%08X' % ctor_at if ctor_at else '????',
        '%08X' % ctor if ctor else 'None'))
