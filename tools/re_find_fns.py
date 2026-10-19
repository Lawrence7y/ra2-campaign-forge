import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\tools")
from xref_scan import classify_names, Scanner
import bisect

sc = Scanner()
sc.scan()
f2n = classify_names()[1]

addrs = [
    0x005B0D0B, 0x0075AFEE, 0x0075B2F1, 0x0075B9E7, 0x0075B9F9,
    0x004DE8A8, 0x004DEA48, 0x004A9CF4, 0x00577D21,
    0x006FB193, 0x0073DF27, 0x0073E113, 0x0073E237,
    0x004ADD93, 0x0044E29D, 0x00454A41, 0x004566CB, 0x004524D1
]
for a in addrs:
    i = bisect.bisect_right(sc.fstart_list, a) - 1
    fn = sc.fstart_list[i] if i >= 0 else 0
    print(f"0x{a:08X} in 0x{fn:08X} {f2n.get(fn, '')}")
