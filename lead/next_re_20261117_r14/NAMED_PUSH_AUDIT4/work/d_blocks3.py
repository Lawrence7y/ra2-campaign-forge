"""Robust block parse: push 8; call opnew; ... mov ecx,eax; call CTOR ... call CRC w/ clsid."""
import sys, json, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt
img = Img()
IDX = json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work\index.json"))

def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None

def num(s):
    s = s.strip()
    if re.fullmatch(r'-?0x[0-9a-f]+', s):
        return int(s, 16)
    if re.fullmatch(r'-?\d+', s):
        return int(s, 10)
    return None

HOST = int(sys.argv[1], 16)
LIMIT = int(sys.argv[2], 16)
seq = []
a = HOST
while a < HOST + LIMIT:
    i = ins_at(a)
    if not i:
        break
    seq.append(i)
    a += i.size

print("host %08X, %d insns, last=%08X" % (HOST, len(seq), seq[-1].address))

# where does esi get CoRegisterClassObject?
for i in seq:
    if i.mnemonic == 'mov' and i.op_str.startswith('esi,') and '0x7e15d8' in i.op_str:
        print("  esi = CRC: " + fmt(i))

out = []
for n, i in enumerate(seq):
    if i.mnemonic == 'push' and num(i.op_str) == 8:
        nx = seq[n + 1] if n + 1 < len(seq) else None
        if not (nx and nx.mnemonic == 'call' and nx.op_str == '0x7c8e17'):
            continue
        ctor = ctor_at = None
        for k in range(n + 1, min(n + 10, len(seq))):
            j = seq[k]
            if j.mnemonic == 'call' and j.op_str.startswith('0x') and num(j.op_str) != 0x7C8E17:
                ctor = num(j.op_str); ctor_at = j.address
                break
        if ctor is None:
            continue
        crc_at = clsid = None
        base_k = [k for k in range(len(seq)) if seq[k].address == ctor_at][0]
        for k in range(base_k, min(base_k + 20, len(seq))):
            j = seq[k]
            if j.mnemonic == 'call' and (j.op_str == 'esi' or '0x7e15d8' in j.op_str):
                crc_at = j.address
                for m in range(k - 1, max(k - 8, 0), -1):
                    p = seq[m]
                    if p.mnemonic == 'push':
                        v = num(p.op_str)
                        if v and 0x7E1000 <= v < 0x812000:
                            clsid = v
                            break
                break
        out.append((i.address, ctor_at, ctor, crc_at, clsid))

print("\nblocks (%d):" % len(out))
for alloc, ctor_at, ctor, crc_at, clsid in out:
    print("  push8 @%08X  ctor@%s=%s  CRC=%-8s clsid=%s" % (
        alloc, '%08X' % ctor_at if ctor_at else '????', '%08X' % ctor,
        '%08X' % crc_at if crc_at else 'None', '%08X' % clsid if clsid else 'None'))
