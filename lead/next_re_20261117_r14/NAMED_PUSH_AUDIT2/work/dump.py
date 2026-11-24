import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

ENTRIES = ["00691EE0", "00691FA0", "006A48A0", "006A4930", "006E87F0", "006E9140",
           "00410C30", "00414290", "0041CFE0", "00524D70", "005F9950"]
out = os.path.dirname(os.path.abspath(__file__))
for e in ENTRIES:
    va = int(e, 16)
    fa = C.fn_at(va)
    lo, hi = fa[0], fa[0] + fa[1]
    txt = C.show_range(lo, hi, f"BODY {e} fn {lo:08X} size {fa[1]}")
    if "006E9140" in e:
        txt = "\n".join(txt.splitlines()[:140])
    open(os.path.join(out, f"body_{e}.txt"), "w", encoding="utf-8").write(txt + "\n")
    print(e, fa[0], fa[1], len(txt.splitlines()))
