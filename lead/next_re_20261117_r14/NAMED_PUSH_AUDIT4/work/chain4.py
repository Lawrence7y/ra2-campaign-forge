"""④ chain for all 16 rows + host classification + atexit check + CLSID consumers."""
import sys, json, struct, bisect, re, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt
img = Img()
W = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work"
IDX = json.load(open(os.path.join(W, "index.json")))
CALLS = [(a, t) for a, t in IDX['calls']]
IATC = [(a, t) for a, t in IDX['iat']]
REFS = {int(k, 16): v for k, v in IDX['refs'].items()}
STARTS = IDX['starts']
IAT_CRC, IAT_CCI = 0x7E15D8, 0x7E15FC

def fstart(a):
    i = bisect.bisect_right(STARTS, a) - 1
    return STARTS[i] if i >= 0 else None
def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None

ROWS = ['006BF810','006BF990','006BFB10','006BFC90','006BFE10','006BFF90','006C0110',
        '006C0290','006C0410','006C0590','006C0710','006C0890','006C0A10','006C0B90',
        '006C0D10','006C0E90']

# ---- build per-host block table once (host 006BB9A0) ----
HOST = 0x6BB9A0
seq = []
a = HOST
while a < HOST + 0x2000:
    i = ins_at(a)
    if not i: break
    seq.append(i); a += i.size
def num(s):
    s = s.strip()
    if re.fullmatch(r'-?0x[0-9a-f]+', s): return int(s, 16)
    if re.fullmatch(r'-?\d+', s): return int(s, 10)
    return None
blocks = []
for n, i in enumerate(seq):
    if i.mnemonic == 'push' and num(i.op_str) == 8:
        nx = seq[n + 1] if n + 1 < len(seq) else None
        if not (nx and nx.mnemonic == 'call' and nx.op_str == '0x7c8e17'): continue
        ctor = ctor_at = None
        for k in range(n + 1, min(n + 10, len(seq))):
            j = seq[k]
            if j.mnemonic == 'call' and j.op_str.startswith('0x') and num(j.op_str) != 0x7C8E17:
                ctor = num(j.op_str); ctor_at = j.address; break
        if ctor is None: continue
        bk = [k for k in range(len(seq)) if seq[k].address == ctor_at][0]
        crc_at = clsid = None
        for k in range(bk, min(bk + 20, len(seq))):
            j = seq[k]
            if j.mnemonic == 'call' and (j.op_str == 'esi' or '0x7e15d8' in j.op_str):
                crc_at = j.address
                for m in range(k - 1, max(k - 8, 0), -1):
                    p = seq[m]
                    if p.mnemonic == 'push':
                        v = num(p.op_str)
                        if v and 0x7E1000 <= v < 0x812000:
                            clsid = v; break
                break
        blocks.append(dict(alloc='%08X' % i.address, ctor='%08X' % ctor,
                           crc='%08X' % crc_at if crc_at else None,
                           clsid='%08X' % clsid if clsid else None))
byctor = {b['ctor']: b for b in blocks}
print("blocks:", len(blocks))

print("\n%-9s %-9s %-9s %-9s %-9s %s" % ("entry", "ctor", "alloc", "CRCcall", "CLSID", "vt"))
out = {}
for r in ROWS:
    d = json.load(open(os.path.join(W, "f3_%s.json" % r)))
    ctor = d['obj_ctor']
    b = byctor.get(ctor)
    print("%-9s %-9s %-9s %-9s %-9s %s" % (r, ctor, b['alloc'] if b else '??',
          b['crc'] if b else '??', b['clsid'] if b else '??', d['main_vt']['vt']))
    out[r] = dict(ctor=ctor, block=b)

# ---- host classification: is 006BB9A0 atexit-registered / destructor? ----
print("\n=== host 006BB9A0 classification ===")
print("refs to host addr as imm32 in .text:", ['%08X' % x for x in REFS.get(HOST, [])])
# atexit import?
for mod in img.pe.DIRECTORY_ENTRY_IMPORT:
    for imp in mod.imports:
        nm = (imp.name or b'').decode('latin1')
        if nm in ('_onexit', 'atexit', 'ExitProcess', 'RegisterWaitForSingleObject'):
            print("  IAT %s = %08X" % (nm, imp.address))
# who calls the host?
callers = [(a, t) for a, t in CALLS if t == HOST]
print("  direct callers of host:", ['%08X' % a for a, _ in callers])

# scan .data/.rdata for host address (atexit table entries are pushed at runtime, but
# a static table could hold it)
for name, base, vsz, praw, rsz in img.sections:
    if name == '.text': continue
    b = img.read(base, max(vsz, rsz))
    hits = [base + i for i in range(0, len(b) - 3, 4)
            if struct.unpack_from('<I', b, i)[0] == HOST]
    if hits:
        print("  static data refs to host in %s: %s" % (name, ['%08X' % h for h in hits]))

# ---- do any .text sites consume the CLSIDs (CoCreateInstance) ? ----
print("\n=== CLSID consumers ===")
for r in ROWS:
    cl = out[r]['block']['clsid'] if out[r]['block'] else None
    if not cl: 
        print("%s  clsid=None" % r); continue
    v = int(cl, 16)
    rs = REFS.get(v, [])
    kinds = []
    for a0 in rs:
        i = ins_at(a0)
        nxt = []
        aa = a0
        for _ in range(6):
            i2 = ins_at(aa); aa += i2.size
            nxt.append('%08X %s' % (i2.address, i2.op_str))
            if i2.mnemonic == 'call': break
        kinds.append((a0, nxt))
    print("%s  clsid=%s refs=%s" % (r, cl, ['%08X' % a0 for a0 in rs]))
    for a0, nxt in kinds[:3]:
        print("    @%08X -> %s" % (a0, nxt))
json.dump(out, open(os.path.join(W, "chain4.json"), 'w'), indent=1)
