import sys, json, struct, bisect
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt
img = Img()
IDX = json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work\index.json"))
REFS = {int(k, 16): v for k, v in IDX['refs'].items()}
CALLS = [(a, t) for a, t in IDX['calls']]
STARTS = IDX['starts']
def fstart(a):
    i = bisect.bisect_right(STARTS, a) - 1
    return STARTS[i] if i >= 0 else None
def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None

vt = int(sys.argv[1], 16)
print("refs to vt %08X:" % vt)
for a in REFS.get(vt, []):
    print("  %08X  %-18s %s   [func %08X]" % (a, ins_at(a).bytes.hex(' '), fmt(ins_at(a))[24:], fstart(a) or 0))
print()
print("refs to entry? (self) skipped")
