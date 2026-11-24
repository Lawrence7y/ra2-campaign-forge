# -*- coding: utf-8 -*-
"""W101 step7: engine-exact hash (count-pad) + targeted id comparison (no mix IO)."""
import json, os, struct, sys, zlib
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\ra2forge")
from mixlib import classic_hash

OUTD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W101_artlib\EVIDENCE"
PBUF = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); PBUF.append(s)

def engine_hash(name: str) -> int:
    """Exact replication of gamemd.exe 0x4A1DE0 (CRC class w/ count-pad finalize).

    Verified against disasm:
      - table @0x81F7B4 == zlib table [已证 step6]
      - full 4-byte blocks streamed (not/table/not == zlib continuation)
      - leftover 1..3 bytes: buffered, then finalize pads:
          buf[L] = L ; then buf[k] = buf[0] for k=L+1..3 ; process block
      - returns finalized crc (== zlib form)
    """
    b = name.upper().encode("ascii", "replace")
    n = len(b)
    full = (n // 4) * 4
    crc = zlib.crc32(b[:full]) if full else 0
    left = b[full:]
    if left:
        L = len(left)
        blk = bytearray(left)
        blk.append(L & 0xFF)
        while len(blk) < 4:
            blk.append(left[0])
        crc = zlib.crc32(bytes(blk), crc)
    return crc & 0xFFFFFFFF

P("== engine-exact hashes ==")
targets = {}
for nm in ["ARTMD.INI", "RULESMD.INI", "ART.INI", "RULES.INI", "AI.INI", "AIMD.INI",
           "BATTLEMD.INI", "MAPSELMD.INI", "UIMD.INI", "DESERTMD.INI",
           "LOCAL.MIX", "LOCALMD.MIX", "CACHE.MIX", "CACHEMD.MIX", "CONQMD.MIX",
           "CONQUER.MIX", "ISOGEN.MIX", "ISOGENMD.MIX", "CAMEO.MIX", "CAMEOMD.MIX",
           "GENERMD.MIX", "GENERIC.MIX", "RA2.MIX", "RA2MD.MIX", "TEMPERAT.MIX",
           "AMAZON.MMX", "EXPANDMD01.MIX", "EXPANDMD98.MIX", "THEME.MIX", "THEMEMD.MIX"]:
    v = engine_hash(nm)
    targets[v] = nm
    P(f"engine_hash({nm!r}) = {v:08X}   (mixlib_crc={zlib.crc32(nm.upper().encode())&0xFFFFFFFF:08X}"
      f" classic={classic_hash(nm):08X})")

P("")
P("== compare with observed unknown ids ==")
KNOWN = {
    0xFBE0D09D: "ra2md.mix submix (187 entries: AIMD/BATTLEMD/MAPSELMD/UIMD/DESERTMD/RULES?/ART?)",
    0x5B47D8D5: "ra2md submix inner art (336535 B)",
    0x8218F9F4: "rules file (expandmd01 top 743215 B; ra2md submix 742958 B)",
    0xA8548FD9: "ra2.mix submix",
    0xF91B2C8B: "ra2.mix submix inner art (245825 B)",
}
for eid, desc in KNOWN.items():
    nm = targets.get(eid)
    P(f"{eid:08X}  {desc}")
    P(f"          -> engine-hash name match: {nm!r}" if nm else
      "          -> NO name in target list hashes to this id")

P("")
P("== brute force unknown ids over candidate universe (engine countpad scheme) ==")
names = set()
for f in os.listdir(r"D:\Project\ra2-campaign-forge\ra2youli"):
    names.add(f.upper())
import re
for rec in json.load(open(os.path.join(OUTD, "step2_strings.json"), encoding="utf-8")):
    s = rec["s"]
    if re.fullmatch(r"[A-Za-z0-9_%\$\.\*\\\-\(\) ]{2,64}", s):
        names.add(s.upper())
bases = ["ART", "RULES", "RULE", "AI", "EVA", "SOUND", "THEME", "BATTLE", "LOCAL", "CACHE",
         "CONQ", "CONQUER", "GENER", "GENERIC", "ISOGEN", "CAMEO", "MAPS", "MULTI", "RA2",
         "MOVIES", "MOVMD", "EXPANDMD", "SIDE", "LOAD", "MAIN", "NTRL", "NEUTRAL", "AUD",
         "AUDIO", "WDT", "KEYBOARD", "MISSION", "MPMODES", "COOPCAMP", "RMGMD", "SPAWN"]
for b in bases:
    for suf in [".INI", ".MIX", "MD.INI", "MD.MIX"]:
        names.add(b + suf)
    for n in range(100):
        names.add(f"{b}{n:02d}.INI"); names.add(f"{b}{n:02d}.MIX")
        names.add(f"{b}MD{n:02d}.INI"); names.add(f"{b}MD{n:02d}.MIX")
P("candidate names:", len(names))
rev = {}
for nm in names:
    try:
        rev.setdefault(engine_hash(nm), nm)
    except Exception:
        pass
for eid in KNOWN:
    nm = rev.get(eid)
    P(f"{eid:08X} -> {nm!r}" if nm else f"{eid:08X} -> (no candidate name matches)")

open(os.path.join(OUTD, "step7_engine_hash.txt"), "w", encoding="utf-8").write("\n".join(PBUF) + "\n")
print("\nsaved ->", os.path.join(OUTD, "step7_engine_hash.txt"))
