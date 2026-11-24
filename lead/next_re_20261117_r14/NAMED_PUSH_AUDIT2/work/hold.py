import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

ENTRIES = ["00691EE0", "00691FA0", "006A48A0", "006A4930", "006E87F0", "006E9140",
           "00410C30", "00414290", "0041CFE0", "00524D70", "005F9950"]

for e in ENTRIES:
    va = int(e, 16)
    fa = C.fn_at(va)
    print(f"=== {e}  fn_at={fa[0]:08X}+{fa[1]} " if fa else f"=== {e} fn_at=None")
    hs = C.holdings(va)
    if not hs:
        print("   holdings: NONE")
    for h in hs:
        print(f"   vt={h['vt']:08X} slot={h['slot']} +{h['off']:#04x} sect={h['sect']} "
              f"cls={h['cls']} COL={h['col']:08X} TD={h['td']:08X}")
