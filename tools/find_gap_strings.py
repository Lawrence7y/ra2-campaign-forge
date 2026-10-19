import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\tools")
from re_gap_spysat_deep import image, base

targets = [b"GapGenerator", b"GapRadiusInCells", b"SuperGapRadiusInCells", b"SpySat", b"PsychicReveal"]
for t in targets:
    idx = 0
    while True:
        pos = image.find(t, idx)
        if pos == -1:
            break
        va = base + pos
        print(f"Found {t.decode()} at 0x{va:08X}")
        idx = pos + 1
