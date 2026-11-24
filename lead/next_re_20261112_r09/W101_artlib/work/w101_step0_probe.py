# -*- coding: utf-8 -*-
"""W101 step0 probe: hashes + CRC variants + MIX headers (read-only)."""
import hashlib, zlib, struct, os, glob, sys

GAME = r"D:\Project\ra2-campaign-forge\ra2youli"
EXE  = os.path.join(GAME, "gamemd.exe")
W97_ART_MD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r07\W97_artmd\EVIDENCE\cand_ra2md_0xFBE0D09D_0x5B47D8D5.ini"
W97_ART_RA2= r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r07\W97_artmd\EVIDENCE\cand_ra2_0xA8548FD9_0xF91B2C8B.ini"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W101_artlib\EVIDENCE\step0_probe.txt"

buf = []
def P(*a):
    s = " ".join(str(x) for x in a)
    print(s); buf.append(s)

P("== sha256 / size ==")
for p in (EXE, W97_ART_MD, W97_ART_RA2):
    h = hashlib.sha256(open(p, "rb").read()).hexdigest().upper()
    P(os.path.basename(p), os.path.getsize(p), h)

P("")
P("== crc32 variants (unpadded vs NUL-padded-to-multiple-of-4, UPPER) ==")
NAMES = ["ARTMD.INI","RULESMD.INI","ART.INI","RULES.INI","AI.INI","LOCAL.MIX","LOCALMD.MIX",
         "ARTMD","RULESMD","BATTLEMD.INI","ECH01.MAP","TEMPERAT.MIX","ISOTEMMD.MIX","LOAD.MIX",
         "ARTMD.MIX","ART01.INI","EXPANDMD01.MIX","RA2MD.MIX","RA2.MIX","SOUND.MIX","EVA.MIX"]
for n in NAMES:
    b = n.upper().encode("ascii")
    unp = zlib.crc32(b) & 0xFFFFFFFF
    pad = b + b"\x00" * ((-len(b)) % 4)
    pd  = zlib.crc32(pad) & 0xFFFFFFFF
    P(f"{n:16s} len={len(b):2d} unpadded={unp:08X} padded={pd:08X}")

P("")
P("== targets ==")
P("claim: crc32('ARTMD.INI')  = 0xAF902833")
P("claim: crc32('RULESMD.INI')= 0x1F674573")
P("W97 art entry: nested-mix id 0xFBE0D09D -> inner id 0x5B47D8D5 (336535 B)")
P("W97 rules entry: expandmd01.mix id 0x8218F9F4 (743215 B)")

P("")
P("== MIX headers (first 8 bytes) ==")
for f in sorted(glob.glob(os.path.join(GAME, "*.mix"))):
    with open(f, "rb") as fh:
        head = fh.read(8)
    h0 = struct.unpack("<I", head[:4])[0]
    P(f"{os.path.basename(f):16s} size={os.path.getsize(f):>12d} head={head.hex(' ')} dword={h0:08X}"
      f" enc_bit31={bool(h0 & 0x80000000)} low16={h0 & 0xFFFF} high16={(h0>>16)&0xFFFF}")

open(OUT, "w", encoding="utf-8").write("\n".join(buf) + "\n")
P("")
P("saved ->", OUT)
