import sys, json, os, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt
img = Img()
W = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work"
IDX = json.load(open(os.path.join(W, "index.json")))
REFS = {int(k, 16): v for k, v in IDX['refs'].items()}
def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None
def rtti(vt):
    col = img.u32(vt - 4)
    if not col: return None
    td = img.u32(col + 0xC)
    return img.cstr(td + 8) if td else None

print("== primary vt slot0 spot-check ==")
for vt in (0x7F5728, 0x7F3650, 0x7F37F8):
    print("  vt %08X slot0=%08X  rtti=%s" % (vt, img.u32(vt), rtti(vt)))

print("\n== who owns CLSID 007E9580 (row1 exec value)? ==")
for x in REFS.get(0x7E9580, []):
    print("  ref @%08X: %s" % (x, fmt(ins_at(x))))
# the factory ctor that leads to that registration block
print("  block ctor was 006BF5C0; its factory vt:")
for vt_ref in REFS.items():
    pass
for x in range(0x7F37A0, 0x7F3820, 4):
    v = img.u32(x)
    if v and img.is_text(v):
        nm = rtti(x)
        if nm:
            print("   vt %08X  slot0=%08X rtti=%s" % (x, v, nm))

print("\n== full dump of shared QI shim 00410260 ==")
a = 0x410260
for _ in range(40):
    i = ins_at(a)
    print("  " + fmt(i))
    a += i.size
    if i.mnemonic.startswith('ret') and a > 0x4102F0:
        break
