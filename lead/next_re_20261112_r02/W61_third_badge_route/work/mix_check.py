#!/usr/bin/env python3
# W61: MIX CRC membership test for third-badge art.
# Q2: does any shipped MIX contain a "boot camp / tutorial / third badge" art asset?
import sys, os, glob, zlib, re, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge")
from ra2forge.mixlib import MixFile

BENCH = r"D:\Project\ra2-campaign-forge\ra2bench"
mixes = sorted(glob.glob(os.path.join(BENCH, "*.mix")))
EXE = os.path.join(BENCH, "gamemd.exe")
raw = open(EXE, "rb").read()

# 1) collect all .SHP/.PCX/.VQA/.BIK filename strings from the exe as known-good names
pat = re.compile(rb"[ -~]{3,60}\.(?:PCX|SHP|BMP|VQA|BIK|PAL)\b", re.I)
known = set()
for m in pat.finditer(raw):
    known.add(m.group().decode("latin1"))

# 2) candidate third-badge art names (broad, uppercase-tolerant)
bases = ["TUT1","TUT","TUTORIAL","BOOTCAMP","BOOT","BOOTCAMP1","CAMP3","CAMPAIGN3",
         "ALLIEDCAMP","SOVIETCAMP","BOOTCAMPCAMP","BADGE","BADGE3","EMBLEM","EMBLEM3",
         "CAMPAIGN","CAMPSEL","CAMPSEL3","CAMP","CAMPICON","THIRDCAMP","TUTORIALICON",
         "BOOTCAMPIcon","TUT1ICON","SIDE3","SIDE4","YURI1","YURICAMP","YURICAMPAIGN",
         "ALL1","SOV1","ALLIED","SOVIET","ALLIEDSEL","SOVIETSEL","BOOTCAMPSEL",
         "CAMPAIGNICON","CAMPAIGNICON3","CAMPICON3","CAMPSELMD","CAMPSELSM",
         "MENU","MENU3","MENUBADGE","NEWCAMPAIGN","BOOTCAMPSELECT"]
exts = [".SHP",".PCX",".BMP",".VQA",".BIK",".PAL",""]
cands = set()
for b in bases:
    for e in exts:
        cands.add(b+e)
# also 3-frame SHP naming conventions
for pfx in ["CAMP","CAMPSEL","BADGE","EMBLEM","SIDE","SEL","MENU","BOOT","TUT"]:
    for i in range(0,6):
        for e in [".SHP",".PCX"]:
            cands.add("%s%02d%s"%(pfx,i,e)); cands.add("%s%d%s"%(pfx,i,e))
# known names as sanity controls
cands |= known

def crc(name):
    return zlib.crc32(name.upper().encode("latin1")) & 0xFFFFFFFF

# 3) enumerate MIX entries and build a global id -> (mix, size) index
allids = {}
print("=== MIX inventory ===")
for mp in mixes:
    try:
        m = MixFile(mp)
        n = len(m.entries)
        print("  %-24s entries=%-6d data_start=0x%X" % (os.path.basename(mp), n, m.data_start))
        for e in m.entries:
            allids.setdefault(e.id, []).append((os.path.basename(mp), e.size))
        m.close()
    except Exception as ex:
        print("  %-24s ERROR %s" % (os.path.basename(mp), ex))
print("  TOTAL distinct entry ids: %d" % len(allids))

# 4) sanity: how many known exe filenames are actually present in MIXes?
hits = [(n, allids[crc(n)]) for n in sorted(known) if crc(n) in allids]
print("\n=== sanity: known exe filenames found in MIX (%d/%d) ===" % (len(hits), len(known)))
for n, loc in hits[:25]:
    print("  %-30s crc=0x%08X  %s" % (n, crc(n), loc[:2]))

# 5) candidate third-badge art hits
print("\n=== candidate third-badge art names present in MIX ===")
found = [(n, allids[crc(n)]) for n in sorted(cands) if crc(n) in allids and n not in known]
for n, loc in found:
    print("  %-30s crc=0x%08X  %s" % (n, crc(n), loc[:2]))
print("  candidate hits (excluding known exe names): %d" % len(found))

# 6) specifically: any name containing TUT/BOOT/CAMP/BADGE among all candidate hits
print("\n=== ANY hit whose name contains TUT/BOOT/CAMP/BADGE/EMBLEM ===")
kw = re.compile(r"(?i)tut|boot|camp|badge|emblem|side3|yuri")
allhits = [(n, allids[crc(n)]) for n in sorted(cands) if crc(n) in allids and kw.search(n)]
for n, loc in allhits:
    print("  %-30s crc=0x%08X  %s" % (n, crc(n), loc[:2]))
print("  total: %d" % len(allhits))
