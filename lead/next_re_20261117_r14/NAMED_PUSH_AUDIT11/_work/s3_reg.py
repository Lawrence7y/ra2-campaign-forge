import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

print("### 0x7e95b0 area (.rdata ids)")
for va in range(0x7E9580, 0x7E9600, 0x10):
    print(f"  {va:08X}: {hexs(va,16)}  ascii={cstr(va,16)!r}")

print()
print("### 0x6c6400 (registry Add?)")
for i in dis(0x6C6400, 160):
    print("  " + fmt(i))

print()
print("### readers of 0xb0bc88")
name, sva, vsz, rawsz, raw = sec_of(0x401000)
blob = DATA[raw:raw + rawsz]
needle = (0xB0BC88).to_bytes(4, "little")
hits = []
pos = blob.find(needle)
while pos >= 0:
    hits.append(sva + pos)
    pos = blob.find(needle, pos + 1)
print("count =", len(hits))
for h in hits:
    print(f"  {h:08X} bytes={hexs(h-4,12)}")
