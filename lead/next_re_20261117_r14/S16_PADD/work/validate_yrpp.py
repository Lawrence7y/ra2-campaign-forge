import os, re
ROOT = r"D:\Project\ra2-campaign-forge"
YRPP = ROOT + r"\YRpp"
allfiles = []
for dp, dirs, files in os.walk(YRPP):
    for fn in files:
        allfiles.append(os.path.join(dp, fn))
print("TOTAL YRpp files (all ext):", len(allfiles))
from collections import Counter
print("Ext counts:", Counter(os.path.splitext(f)[1].lower() for f in allfiles))

# Validate known positives from S16_N1 audit
KNOWN = ["53A0E0", "53AE50", "6CE270", "6CE2C0", "53AF40", "595740"]
for hx in KNOWN:
    pat = re.compile(re.escape(hx), re.I)
    n = 0
    sample = []
    for fp in allfiles:
        try:
            with open(fp, encoding="utf-8", errors="replace") as f:
                for ln, line in enumerate(f, 1):
                    if pat.search(line):
                        n += 1
                        if len(sample) < 3:
                            sample.append((os.path.relpath(fp, ROOT), ln, line.strip()[:140]))
        except Exception:
            pass
    print("\nKNOWN %s : %d hits" % (hx, n))
    for s in sample:
        print("   %s:%d: %s" % s)
