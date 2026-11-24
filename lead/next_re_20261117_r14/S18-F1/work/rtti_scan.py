"""S18-F1: RTTI class-name scan for Event classes + vftable attribution.
Independent PE parsing; no atlas. capstone skipdata=True.
"""
import sys, struct, re
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-F1\work')
from pe_util import read, u32, sections

sec_ranges = []
for name, va_base, vsize, praw, rawsize, ch in sections():
    if rawsize > 0:
        sec_ranges.append((name, va_base, rawsize))

def scan_ascii(pattern):
    out = []
    rx = re.compile(pattern)
    for name, va_base, rawsize in sec_ranges:
        data = read(va_base, rawsize)
        if not data: continue
        for m in rx.finditer(data):
            out.append((va_base + m.start(), name, m.group(0)))
    return out

print("===== RTTI names containing 'event' (case-insensitive) =====")
hits = scan_ascii(rb'\x2e\x3f\x41\x56[\x20-\x7e]{0,80}')
for va, sec, raw in hits:
    s = raw.decode('latin1')
    if 'event' in s.lower():
        print(f"  @0x{va:08X} [{sec}] {s}")

print("\n===== vftable RTTI decode =====")
for vt in [0x7F550C, 0x7F554C, 0x7F5554, 0x7F555C, 0x7F5578]:
    rtti = u32(vt-4)
    nm = None
    if rtti and 0x400000 < rtti < 0xC00000:
        nameva = u32(rtti+8)
        if nameva and 0x400000 < nameva < 0xC00000:
            b = read(nameva, 120)
            if b:
                nm = b.split(b'\x00')[0].decode('latin1')
    print(f"  vftable 0x{vt:08X}: [vt-4]=0x{rtti or 0:08X} name={nm}")

print("\n===== total AV names + EventClass/TEvent exact =====")
print(f"  total AV names scanned = {len(hits)}")
for va, sec, raw in hits:
    s = raw.decode('latin1')
    if 'EventClass' in s or 'TEvent' in s:
        print(f"  @0x{va:08X} {s}")
