"""④ chain, corrected: factory object ctor = function storing the factory vt."""
import sys, json, struct, bisect, re, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt
img = Img()
W = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work"
IDX = json.load(open(os.path.join(W, "index.json")))
CALLS = [(a, t) for a, t in IDX['calls']]
REFS = {int(k, 16): v for k, v in IDX['refs'].items()}
STARTS = IDX['starts']

def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None
def num(s):
    s = s.strip()
    if re.fullmatch(r'-?0x[0-9a-f]+', s): return int(s, 16)
    if re.fullmatch(r'-?\d+', s): return int(s, 10)
    return None

HOST = 0x6BB9A0
seq = []
a = HOST
while a < HOST + 0x2000:
    i = ins_at(a)
    if not i: break
    seq.append(i); a += i.size
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
        blocks.append(dict(alloc=i.address, ctor=ctor, crc=crc_at, clsid=clsid))
byctor = {b['ctor']: b for b in blocks}

ROWS = ['006BF810','006BF990','006BFB10','006BFC90','006BFE10','006BFF90','006C0110',
        '006C0290','006C0410','006C0590','006C0710','006C0890','006C0A10','006C0B90',
        '006C0D10','006C0E90']
res = {}
print("%-9s %-9s %-9s %-9s %-9s %-9s %-9s" % ("entry","facVt","facCtor","vtStore","alloc","CRCcall","CLSID"))
for r in ROWS:
    d = json.load(open(os.path.join(W, "f3_%s.json" % r)))
    fv = int(d['factory']['vt'], 16)
    rs = [x for x in REFS.get(fv, [])]
    ctor = None; store = None
    for x in rs:
        i = ins_at(x)
        if i.mnemonic == 'mov' and i.op_str.startswith('dword ptr [') and ', 0x' in i.op_str:
            ctor = STARTS[bisect.bisect_right(STARTS, x) - 1]; store = x; break
    b = byctor.get(ctor)
    print("%-9s %-9s %-9s %-9s %-9s %-9s %-9s" % (
        r, '%08X' % fv, '%08X' % ctor if ctor else '??', '%08X' % store if store else '??',
        '%08X' % b['alloc'] if b else '??', '%08X' % b['crc'] if b else '??',
        '%08X' % b['clsid'] if b else '??'))
    res[r] = dict(factory_vt='%08X' % fv,
                  factory_vt_refs=['%08X' % x for x in rs],
                  factory_ctor='%08X' % ctor if ctor else None,
                  vt_store='%08X' % store if store else None,
                  alloc='%08X' % b['alloc'] if b else None,
                  crc='%08X' % b['crc'] if b else None,
                  clsid='%08X' % b['clsid'] if b else None)
json.dump(res, open(os.path.join(W, "chain4.json"), 'w'), indent=1)

print("\n=== CLSID consumers (imm32 refs to clsid addr in .text) ===")
for r in ROWS:
    cl = res[r]['clsid']
    if not cl: continue
    v = int(cl, 16)
    rs = REFS.get(v, [])
    print("%s clsid=%s  refs=%s" % (r, cl, ['%08X' % x for x in rs]))
