import sys, json, os, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt
img = Img()
W = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work"
IDX = json.load(open(os.path.join(W, "index.json")))
CALLS = [(a, t) for a, t in IDX['calls']]
REFS = {int(k, 16): v for k, v in IDX['refs'].items()}
chain = json.load(open(os.path.join(W, "chain4.json")))
rows = list(chain.keys())
print("%-9s %-10s %-8s %-40s" % ("entry","directCall","vtRefs","vt ref sites"))
for r in rows:
    e = int(r, 16)
    dc = [a for a, t in CALLS if t == e]
    fv = int(chain[r]['factory_vt'], 16)
    rs = REFS.get(fv, [])
    print("%-9s %-10s %-8d %s" % (r, ['%08X' % a for a in dc] or '0', len(rs), ['%08X' % x for x in rs]))
print()
# host caller / nature
def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None
print("host 006BB9A0 caller 007CD8EA context:")
a = 0x7CD8EA - 0x30
for _ in range(14):
    i = ins_at(a)
    print("  " + fmt(i))
    a += i.size
print()
# atexit import sites
for mod in img.pe.DIRECTORY_ENTRY_IMPORT:
    for imp in mod.imports:
        nm = (imp.name or b'').decode('latin1')
        if nm in ('_onexit', 'atexit'):
            print("IAT %s = %08X" % (nm, imp.address))
            print("  refs in .text:", ['%08X' % x for x in REFS.get(imp.address, [])][:10])
