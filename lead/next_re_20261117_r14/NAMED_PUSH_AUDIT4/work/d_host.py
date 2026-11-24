import sys, json, struct, bisect
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt
img = Img()
IDX = json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work\index.json"))
CALLS = [(a, t) for a, t in IDX['calls']]
IATC = [(a, t) for a, t in IDX['iat']]
REFS = {int(k, 16): v for k, v in IDX['refs'].items()}
STARTS = IDX['starts']
def fstart(a):
    i = bisect.bisect_right(STARTS, a) - 1
    return STARTS[i] if i >= 0 else None
def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None
def win(start, lo, hi, label):
    print("--- %s [%08X..%08X] in func %08X" % (label, lo, hi, start or 0))
    a = lo
    while a < hi:
        i = ins_at(a)
        if not i: break
        print("  " + fmt(i))
        a += i.size

ctor = int(sys.argv[1], 16)
callers = [(a, t) for a, t in CALLS if t == ctor]
print("callers of ctor %08X: %s" % (ctor, ["%08X" % a for a, _ in callers]))
for a, _ in callers:
    h = fstart(a)
    print("\ncaller @%08X in func %08X" % (a, h or 0))
    win(h, max(h, a - 0x60), a + 0x60, "alloc window")
    # CRC calls in the host function
    crc = [(x, t) for x, t in IATC if t == 0x7E15D8 and h and h <= x < h + 0x400]
    for x, t in crc:
        print("\n  CoRegisterClassObject call @%08X in func %08X" % (x, h))
        win(h, max(h, x - 0x50), x + 0x18, "CRC window")
