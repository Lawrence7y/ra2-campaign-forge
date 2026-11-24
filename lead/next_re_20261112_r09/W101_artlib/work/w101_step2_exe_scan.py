# -*- coding: utf-8 -*-
"""W101 step2: gamemd.exe strings + code xrefs + imm32 census (read-only)."""
import hashlib, json, os, re, struct, zlib, sys

sys.path.insert(0, r"D:\Project\ra2-campaign-forge\ra2forge")
import mixlib  # for classic_hash

GAME = r"D:\Project\ra2-campaign-forge\ra2youli"
EXE  = os.path.join(GAME, "gamemd.exe")
OUTD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W101_artlib\EVIDENCE"

data = open(EXE, "rb").read()
buf = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); buf.append(s)

# --- section map (VA <-> file offset). Deep-doc rule: .text/.rdata/.data FileOffset = VA-0x400000
import pefile
pe = pefile.PE(EXE, fast_load=True)
IMAGEBASE = pe.OPTIONAL_HEADER.ImageBase
secs = []
for s in pe.sections:
    name = s.Name.rstrip(b"\x00").decode("ascii", "replace")
    secs.append((name, s.VirtualAddress + IMAGEBASE, s.Misc_VirtualSize,
                 s.PointerToRawData, s.SizeOfRawData))
    P(f"sec {name:8s} VA={s.VirtualAddress+IMAGEBASE:08X} vsize={s.Misc_VirtualSize:08X} "
      f"raw={s.PointerToRawData:08X} rawsize={s.SizeOfRawData:08X}")

def va2off(va):
    for name, vstart, vsz, raw, rsz in secs:
        if vstart <= va < vstart + max(vsz, rsz):
            o = raw + (va - vstart)
            if o < len(data):
                return o
    return None

def off2va(off):
    for name, vstart, vsz, raw, rsz in secs:
        if raw <= off < raw + rsz:
            return vstart + (off - raw)
    return None

# --- baseline .text hash (fs_mix_load_chain_deep.md 9.2: raw SizeOfRawData=0x3E0000)
text = [s for s in secs if s[0] == ".text"][0]
traw = data[text[3]: text[3] + text[4]]
P("")
P(".text raw sha256 =", hashlib.sha256(traw).hexdigest())
P("baseline expect  = c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (fs_mix_deep 9.2)")
P("match:", hashlib.sha256(traw).hexdigest() ==
  "c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738")

# --- ASCII strings across whole image
strings = []  # (va, s)
for m in re.finditer(rb"[\x20-\x7E]{4,64}", data):
    off = m.start()
    va = off2va(off)
    if va is not None:
        strings.append((va, m.group().decode("ascii")))
P("")
P("total ascii strings in mapped sections:", len(strings))
json.dump([{"va": va, "s": s} for va, s in strings],
          open(os.path.join(OUTD, "step2_strings.json"), "w", encoding="utf-8"),
          ensure_ascii=False)

KEY = re.compile(r"(ART|RULE|RULEMD|INI$|\.INI|\.MIX|EXPAND|LOCAL|CACHE|ISO|CAMEO|CONQ|GENERIC|"
                 r"EVA|SOUND|THEME|BATTLE|MAPS|MOV|ECACHE|ELOCAL|%02d|Failed to load|SUBDIR|SHP$)", re.I)
sel = [(va, s) for va, s in strings if KEY.search(s) and len(s) <= 48]
P("")
P(f"== filename-ish strings (filtered {len(sel)} of {len(strings)}) ==")
seen = set()
for va, s in sorted(sel):
    k = s
    if k in seen: continue
    seen.add(k)
    P(f"VA {va:08X}  {s!r}")
json.dump([{"va": va, "s": s} for va, s in sel],
          open(os.path.join(OUTD, "step2_strings_selected.json"), "w", encoding="utf-8"),
          ensure_ascii=False)

# --- exact literals of interest: find ALL occurrences (any case)
P("")
P("== exact literal occurrences (bytes search, whole image) ==")
LITS = [b"ARTMD.INI", b"artmd.ini", b"ArtMd.Ini", b"RULESMD.INI", b"rulesmd.ini",
        b"ART.INI", b"art.ini", b"RULES.INI", b"rules.ini",
        b"Failed to load ARTMD.INI", b"RULEMD*.INI", b"BATTLEMD*.INI",
        b"ARTMD*.INI", b"ART01.INI", b"ARTMD", b"RULESMD",
        b"LOCAL.MIX", b"LOCALMD.MIX", b"local.mix", b"localmd.mix",
        b"ARTMD.MIX", b"ART01.MIX", b"ART.MIX"]
str_hits = {}
for lit in LITS:
    hits = []
    start = 0
    while True:
        i = data.find(lit, start)
        if i < 0: break
        va = off2va(i)
        hits.append((i, va))
        start = i + 1
    str_hits[lit.decode("ascii", "replace")] = hits
    P(f"{lit.decode('ascii'):28s} n={len(hits)}  " +
      "  ".join(f"@off={i:08X}/VA={va:08X}" if va else f"@off={i:08X}/VA=?" for i, va in hits[:8]))

# --- code xrefs: imm32 == string VA  (push/mov imm32)
P("")
P("== code xrefs to key string VAs (imm32 == VA anywhere in image) ==")
xrefs = {}
for lit, hits in str_hits.items():
    for i, va in hits:
        if va is None: continue
        pat = struct.pack("<I", va)
        start = 0; refs = []
        while True:
            j = data.find(pat, start)
            if j < 0: break
            rva = off2va(j)
            prev = data[j-1]
            refs.append((j, rva, prev))
            start = j + 1
        if refs:
            xrefs[f"{lit}@{va:08X}"] = refs
            P(f"{lit!r} VA={va:08X}: xrefs {len(refs)}")
            for j, rva, prev in refs[:16]:
                P(f"    ref@off={j:08X} VA={rva if rva else 0:08X} prevbyte={prev:02X}"
                  f" {'push' if prev==0x68 else 'mov-imm?' if 0xB8<=prev<=0xBF else ''}")
json.dump({k: [{"off": j, "va": rva, "prev": prev} for j, rva, prev in v] for k, v in xrefs.items()},
          open(os.path.join(OUTD, "step2_string_xrefs.json"), "w", encoding="utf-8"), indent=1)

# --- imm32 census for id constants + all hash variants
P("")
P("== id-constant imm32 census ==")
def variants(name):
    b_u = name.upper().encode("ascii"); b_l = name.lower().encode("ascii")
    out = {}
    out["crc_upper"] = zlib.crc32(b_u) & 0xFFFFFFFF
    out["crc_upper_pad"] = zlib.crc32(b_u + b"\x00" * ((-len(b_u)) % 4)) & 0xFFFFFFFF
    out["crc_lower"] = zlib.crc32(b_l) & 0xFFFFFFFF
    out["crc_lower_pad"] = zlib.crc32(b_l + b"\x00" * ((-len(b_l)) % 4)) & 0xFFFFFFFF
    out["classic_upper"] = mixlib.classic_hash(name)
    return out

NAMES = ["ARTMD.INI", "RULESMD.INI", "ART.INI", "RULES.INI", "ARTMD.MIX", "ART01.INI",
         "LOCAL.MIX", "LOCALMD.MIX", "ARTMD", "RULESMD"]
idtab = {}
for n in NAMES:
    for scheme, v in variants(n).items():
        idtab[f"{n}:{scheme}"] = v
idtab["W97_art_inner:0x5B47D8D5"] = 0x5B47D8D5
idtab["W97_art_submix:0xFBE0D09D"] = 0xFBE0D09D
idtab["W97_ra2_art_submix:0xA8548FD9"] = 0xA8548FD9
idtab["W97_ra2_art_inner:0xF91B2C8B"] = 0xF91B2C8B
idtab["W97_rules_exp01:0x8218F9F4"] = 0x8218F9F4

imm_hits = {}
for label, v in sorted(idtab.items(), key=lambda kv: kv[1]):
    pat = struct.pack("<I", v)
    hits = []
    start = 0
    while True:
        j = data.find(pat, start)
        if j < 0: break
        prev = data[j-1]
        rva = off2va(j)
        hits.append((j, rva, prev))
        start = j + 1
    imm_hits[label] = {"value": v, "hits": hits}
    tag = " <<<< HIT" if hits else ""
    P(f"{label:34s} {v:08X}  n={len(hits)}{tag}")
    for j, rva, prev in hits[:12]:
        P(f"    ref@off={j:08X} VA={rva if rva else 0:08X} prevbyte={prev:02X}"
          f" ctx={data[j-8:j+8].hex(' ')}")
json.dump({k: {"value": v["value"],
               "hits": [{"off": j, "va": rva, "prev": prev, "ctx": data[max(0,j-8):j+8].hex(" ")}
                        for j, rva, prev in v["hits"]]}
           for k, v in imm_hits.items()},
          open(os.path.join(OUTD, "step2_imm_census.json"), "w", encoding="utf-8"), indent=1)

open(os.path.join(OUTD, "step2_exe_scan.txt"), "w", encoding="utf-8").write("\n".join(buf) + "\n")
print("\nsaved ->", os.path.join(OUTD, "step2_exe_scan.txt"))
