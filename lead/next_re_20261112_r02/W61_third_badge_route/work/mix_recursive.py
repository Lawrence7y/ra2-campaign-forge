#!/usr/bin/env python3
# W61: RECURSIVE MIX enumeration (in-memory) + CRC membership test for
# third-badge art. Q2: does any shipped MIX contain a BootCamp/Tutorial icon?
import sys, os, glob, zlib, re, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge")
from ra2forge.mixlib import westwood_decrypt_key_block, Blowfish, crc_hash

BENCH = r"D:\Project\ra2-campaign-forge\ra2bench"

def parse_mix(buf):
    """Return (entries, data_start) or None. entries = list of (id, off, size)."""
    if len(buf) < 10: return None
    if struct.unpack_from("<H", buf, 0)[0] != 0: return None
    flags = struct.unpack_from("<H", buf, 2)[0]
    if flags & 0x2:
        if len(buf) < 92: return None
        key = westwood_decrypt_key_block(buf[4:84])
        fish = Blowfish(key)
        first_block = fish.decrypt_block(buf[84:92])
        num_files = struct.unpack("<H", first_block[:2])[0]
        block_count = (13 + num_files*12)//8
        if 84 + block_count*8 > len(buf): return None
        header = fish.decrypt(buf[84:84+block_count*8])
        raw = header[6:]
        data_start = 84 + block_count*8
    else:
        num_files = struct.unpack_from("<H", buf, 4)[0]
        raw = buf[10:10+num_files*12]
        data_start = 10 + num_files*12
    out=[]
    for i in range(num_files):
        if 12*i+12 > len(raw): break
        hid,off,size = struct.unpack_from("<III", raw, i*12)
        out.append((hid,off,size))
    return out, data_start

# global id -> list of (container, size)
ALL = {}
seen_containers = set()
def walk(buf, label, depth=0):
    r = parse_mix(buf)
    if r is None: return
    ents, ds = r
    for hid,off,size in ents:
        ALL.setdefault(hid, []).append((label, size))
        # recurse into nested MIX
        if size >= 10 and size <= 400_000_000 and ds+off+10 <= len(buf):
            head = buf[ds+off:ds+off+10]
            if struct.unpack_from("<H", head, 0)[0] == 0:
                sub = buf[ds+off:ds+off+size]
                key = (label, hid)
                if key not in seen_containers:
                    seen_containers.add(key)
                    walk(sub, label+"/%08X"%hid, depth+1)

print("=== recursive MIX walk ===")
for mp in sorted(glob.glob(os.path.join(BENCH, "*.mix"))):
    try:
        buf = open(mp, "rb").read()
    except Exception as ex:
        print("  %-22s read ERROR %s" % (os.path.basename(mp), ex)); continue
    r = parse_mix(buf)
    if r is None:
        print("  %-22s not TS/RA2 MIX (skipped)" % os.path.basename(mp)); continue
    print("  %-22s top entries=%d" % (os.path.basename(mp), len(r[0])))
    walk(buf, os.path.basename(mp))
print("  TOTAL distinct ids after recursion: %d" % len(ALL))
print("  TOTAL nested containers walked: %d" % len(seen_containers))

EXE = os.path.join(BENCH, "gamemd.exe")
raw = open(EXE, "rb").read()
pat = re.compile(rb"[ -~]{3,60}\.(?:PCX|SHP|BMP|VQA|BIK|PAL)\b", re.I)
known = set(m.group().decode("latin1") for m in pat.finditer(raw))

def crc(n): return zlib.crc32(n.upper().encode("latin1")) & 0xFFFFFFFF
hits = [(n, ALL[crc(n)]) for n in sorted(known) if crc(n) in ALL]
print("\n=== sanity: known exe art filenames found in MIX after recursion (%d/%d) ===" % (len(hits),len(known)))
for n,loc in hits[:40]:
    print("  %-28s crc=0x%08X %s" % (n, crc(n), loc[0]))

# broad third-badge candidates
bases = ["TUT1","TUT","TUTORIAL","BOOTCAMP","BOOT","BOOTCAMP1","CAMP3","CAMPAIGN3",
         "ALLIEDCAMP","SOVIETCAMP","BADGE","BADGE3","EMBLEM","EMBLEM3","CAMPAIGN",
         "CAMPSEL","CAMPSEL3","CAMP","CAMPICON","THIRDCAMP","TUTORIALICON","BOOTCAMPIcon",
         "TUT1ICON","SIDE3","SIDE4","YURI1","YURICAMP","ALL1","SOV1","ALLIED","SOVIET",
         "CAMPAIGNICON","CAMPAIGNICON3","CAMPICON3","NEWCAMPAIGN","BOOTCAMPSELECT"]
exts = [".SHP",".PCX",".BMP",".VQA",".BIK",".PAL",""]
cands=set()
for b in bases:
    for e in exts: cands.add(b+e)
for pfx in ["CAMP","CAMPSEL","BADGE","EMBLEM","SIDE","SEL","MENU","BOOT","TUT","BTN"]:
    for i in range(0,10):
        for e in [".SHP",".PCX"]:
            cands.add("%s%02d%s"%(pfx,i,e)); cands.add("%s%d%s"%(pfx,i,e))
kw = re.compile(r"(?i)tut|boot|camp|badge|emblem|side3|yuri")
print("\n=== third-badge candidate names present in any MIX (keyword-filtered) ===")
fhits = [(n,ALL[crc(n)]) for n in sorted(cands) if crc(n) in ALL and kw.search(n)]
for n,loc in fhits: print("  %-28s crc=0x%08X %s" % (n,crc(n),loc[:2]))
print("  total keyword hits: %d" % len(fhits))
print("\n=== ALL candidate names present in any MIX (any keyword) ===")
ahits = [(n,ALL[crc(n)]) for n in sorted(cands) if crc(n) in ALL]
for n,loc in ahits: print("  %-28s crc=0x%08X %s" % (n,crc(n),loc[:2]))
print("  total all-candidate hits: %d" % len(ahits))
