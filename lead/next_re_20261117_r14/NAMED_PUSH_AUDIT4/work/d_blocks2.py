"""Pattern-based: find (push N; call opnew; ... mov ecx,eax; call CTOR) then next CRC call w/ CLSID."""
import sys, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt
img = Img()
IDX = json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work\index.json"))

def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None

HOST = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x6BB9A0
LIMIT = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x1A00
seq = []
a = HOST
while a < HOST + LIMIT:
    i = ins_at(a)
    if not i:
        break
    seq.append(i)
    a += i.size

print("host %08X, %d insns" % (HOST, len(seq)))
print("\n-- first 40 insns (prologue / esi source) --")
for i in seq[:40]:
    print("  " + fmt(i))

print("\n-- blocks --")
n = 0
while n < len(seq):
    i = seq[n]
    if i.mnemonic == 'push' and i.op_str.startswith('0x') and i.op_str in ('0x8', '0x4', '0xc', '0x10'):
        nxt = seq[n + 1] if n + 1 < len(seq) else None
        if nxt and nxt.mnemonic == 'call' and nxt.op_str == '0x7c8e17':
            # scan forward for mov ecx,eax ; call X
            ctor = None; ctor_at = None
            for k in range(n + 1, min(n + 12, len(seq))):
                j = seq[k]
                if j.mnemonic == 'call' and j.op_str.startswith('0x') and j.op_str != '0x7c8e17':
                    ctor = int(j.op_str, 16); ctor_at = j.address
                    break
            clsid = None; crc_at = None
            for k in range(([x for x in range(n, len(seq)) if seq[x].address == ctor_at][0] if ctor_at else n), min(n + 24, len(seq))):
                j = seq[k]
                if j.mnemonic == 'call' and j.op_str in ('esi', 'dword ptr [0x7e15d8]'):
                    crc_at = j.address
                    for m in range(k - 1, max(k - 8, 0), -1):
                        p = seq[m]
                        if p.mnemonic == 'push' and p.op_str.startswith('0x'):
                            v = int(p.op_str, 16)
                            if 0x7E1000 <= v < 0x812000:
                                clsid = v
                                break
                    break
            print("  new %-4s @%08X  ctor %s @%s  CRC %s  clsid %s" % (
                i.op_str, i.address,
                '%08X' % ctor if ctor else '????',
                '%08X' % ctor_at if ctor_at else '????',
                '%08X' % crc_at if crc_at else '????',
                '%08X' % clsid if clsid else 'None'))
            n += 10
            continue
    n += 1
