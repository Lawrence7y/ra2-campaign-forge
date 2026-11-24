# -*- coding: utf-8 -*-
"""W101 step3: full MIX census of ra2youli (read-only).

Own parser on top of ra2forge/mixlib.py primitives (Blowfish + RSA key block +
crc/classic hash). Adds: nesting recursion at any depth, content sniffing for
INI-like entries, six-scheme id->name resolution, presence check of key ids.
Writes only into W101_artlib\\EVIDENCE.
"""
import csv, hashlib, json, os, struct, sys, zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\ra2forge")
import mixlib
from mixlib import Blowfish, westwood_decrypt_key_block, crc_hash, classic_hash

def engine_hash(name: str) -> int:
    """Exact replication of gamemd.exe 0x4A1DE0 (see step6/step7 evidence)."""
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

GAME = r"D:\Project\ra2-campaign-forge\ra2youli"
OUTD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W101_artlib\EVIDENCE"
W97_ART = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r07\W97_artmd\EVIDENCE\cand_ra2md_0xFBE0D09D_0x5B47D8D5.ini"
STRJSON = os.path.join(OUTD, "step2_strings.json")

MAX_DEPTH = 5
HEAD = 8192

# ---------------------------------------------------------------- name tables
def load_candidate_names():
    names = set()
    for f in os.listdir(GAME):
        names.add(f.upper())
    try:
        for rec in json.load(open(STRJSON, encoding="utf-8")):
            s = rec["s"]
            if re_nameok(s):
                names.add(s.upper())
    except Exception as e:
        print("WARN strings json:", e)
    # hardcoded westwood universe (loader lists from fs_mix_load_chain_deep.md + inis)
    bases = ["ART", "RULES", "RULE", "AI", "EVA", "SOUND", "THEME", "BATTLE", "KEYBOARD",
             "MPMODES", "COOPCAMP", "RMGMD", "MAPSELMD", "MISSION", "WDTMAP", "WDTCHOICE",
             "LOCAL", "CACHE", "ECACHE", "ELOCAL", "CONQ", "CONQUER", "GENER", "GENERIC",
             "ISOGEN", "CAMEO", "MAPS", "MULTI", "MOVIES", "MOVMD", "RA2", "LANGRULE",
             "SPAWN", "BOOT", "MAIN", "NEUTRAL", "NTRL", "AUD", "AUDIO", "LOAD", "WDT",
             "SIDE1", "SIDE2", "SIDE3", "SIDE4", "SIDE5", "SIDE6", "SIDE7", "SIDE8",
             "TEMPERAT", "SNOW", "URBAN", "DESERT", "LUNAR", "UBN"]
    for b in bases:
        names.add(b)
        names.add(b + ".INI")
        names.add(b + "MD.INI")
        names.add(b + ".MIX")
        names.add(b + "MD.MIX")
        for n in range(100):
            names.add(f"{b}{n:02d}.INI"); names.add(f"{b}MD{n:02d}.INI")
            names.add(f"{b}{n:02d}.MIX"); names.add(f"{b}MD{n:02d}.MIX")
    for th in ["TEMPERAT", "SNOW", "URBAN", "DESERT", "LUNAR", "UBN"]:
        names.add(th + "MD.INI")
    names.update({"ART01.INI","ARTMD98.INI","RULESMD98.INI","RULES01.INI","AIMD.INI",
                  "LANGRULE.INI","EXPANDMD98.MIX","EXPANDMD01.MIX","LOCAL MIX DATABASE.DAT",
                  "LOCAL MIX DATABASE","XCC LOCAL MIX DATABASE.DAT"})
    return {n for n in names if 1 <= len(n) <= 64 and n.isascii()}

import re
def re_nameok(s):
    return bool(re.fullmatch(r"[A-Za-z0-9_%\$\.\*\\\-\(\) ]{2,64}", s)) and \
           re.search(r"(\.INI|\.MIX|\.MAP|\.SHP|\.VXL|\.HVA|\.CSF|\.PAL|\.AUD|\.TXT|\.DAT|\.MMP|\.MMX|\.YRM|\.PRM|\.EGA|\.SNO|\.TEM|\.UBN|\.DES|\.LUN|\.URB|\.FNT|\.EVA|\.TGA|\.PCX|\.BMP|\.VQA|\.WAV|\.DLL|\.EXE|\.INI$|^)", s, re.I)

def build_scheme_maps(names):
    maps = {k: {} for k in ("engine", "crc_upper", "crc_upper_pad", "crc_lower",
                            "crc_lower_pad", "classic")}
    for n in names:
        bu = n.upper().encode("ascii", "replace")
        bl = n.lower().encode("ascii", "replace")
        nm = n.upper()
        maps["engine"].setdefault(engine_hash(nm), nm)
        maps["crc_upper"].setdefault(zlib.crc32(bu) & 0xFFFFFFFF, nm)
        maps["crc_upper_pad"].setdefault(zlib.crc32(bu + b"\x00" * ((-len(bu)) % 4)) & 0xFFFFFFFF, nm)
        maps["classic"].setdefault(classic_hash(nm), nm)
        maps["crc_lower"].setdefault(zlib.crc32(bl) & 0xFFFFFFFF, nm)
        maps["crc_lower_pad"].setdefault(zlib.crc32(bl + b"\x00" * ((-len(bl)) % 4)) & 0xFFFFFFFF, nm)
    return maps

SMAPS = build_scheme_maps(load_candidate_names())
PBUF = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); PBUF.append(s)

# ---------------------------------------------------------------- index parse
def parse_ts_plain(buf, total):
    """TS/RA2 plain index. buf: index region (from byte 0 of the mix image)."""
    if len(buf) < 10: return None
    fmt, flags, count = struct.unpack_from("<HHH", buf, 0)
    if fmt != 0: return None
    body = struct.unpack_from("<I", buf, 6)[0]
    need = 10 + count * 12
    if count <= 0 or need > len(buf): return None
    ents = [struct.unpack_from("<III", buf, 10 + i * 12) for i in range(count)]
    for _eid, off, size in ents:
        if off < 0 or size < 0 or off + size > total: return None
    ds_flags = 10 + count * 12 + (4 if flags & 1 else 0)
    ds_plain = 10 + count * 12
    return {"kind": "ts_plain", "flags": flags, "count": count, "body": body,
            "entries": ents, "data_start_candidates": (ds_plain, ds_flags)}

def parse_ts_encrypted(buf):
    """TS/RA2 encrypted index (80-byte RSA key block + blowfish index)."""
    if len(buf) < 92: return None
    fmt, flags = struct.unpack_from("<HH", buf, 0)
    if fmt != 0 or not (flags & 2): return None
    try:
        key = westwood_decrypt_key_block(buf[4:84])
        fish = Blowfish(key)
    except Exception:
        return None
    first = fish.decrypt_block(buf[84:92])
    count = struct.unpack_from("<H", first, 0)[0]
    if count <= 0 or count > 500000: return None
    nblocks = (13 + count * 12) // 8   # ceil((6+12N)/8), same as mixlib
    if 84 + nblocks * 8 > len(buf): return None
    plain = fish.decrypt(buf[84:84 + nblocks * 8])
    ents_raw = plain[6:6 + count * 12]
    if len(ents_raw) < count * 12: return None
    ents = [struct.unpack_from("<III", ents_raw, i * 12) for i in range(count)]
    ds = 84 + nblocks * 8
    # entry-fit validation: garbage RSA output is rejected here
    for _eid, eoff, esz in ents:
        if eoff + esz > buf_len_hint - ds or eoff < 0 or esz < 0:
            return None
    return {"kind": "ts_encrypted", "flags": flags, "count": count,
            "entries": ents, "data_start_candidates": (ds,)}

def parse_td(buf, total):
    """TD/RA1 style: u16 count, u16 body, entries @4. STRICT: real archives only."""
    if len(buf) < 4: return None
    count, body = struct.unpack_from("<HH", buf, 0)
    if count < 2 or 4 + count * 12 > len(buf): return None
    ents = [struct.unpack_from("<III", buf, 4 + i * 12) for i in range(count)]
    ds = 4 + count * 12
    prev = -1
    for _eid, off, size in ents:
        if off < 0 or size < 0 or off + size > total - ds: return None
        if off < prev: return None          # offsets must be non-decreasing
        prev = off
    if sum(size for _, _, size in ents) > total - ds: return None
    return {"kind": "td", "flags": body, "count": count, "entries": ents,
            "data_start_candidates": (ds,)}

def parse_mix_image(buf, total):
    """Try TS-encrypted, TS-plain, TD. Returns meta dict or None."""
    global buf_len_hint
    buf_len_hint = total
    m = parse_ts_encrypted(buf)
    if m: return m
    m = parse_ts_plain(buf, total)
    if m: return m
    m = parse_td(buf, total)
    if m: return m
    return None

buf_len_hint = 0

# ---------------------------------------------------------------- content
def printable_ratio(b):
    if not b: return 0.0
    ok = sum(1 for c in b if 0x20 <= c <= 0x7E or c in (9, 10, 13))
    return ok / len(b)

INI_MARKERS = [b"Foundation=", b"Image=", b"Cameo=", b"BuildCat=", b"Voxel=",
               b"[General]", b"[CombatDamage]", b"[AudioVisual]", b"[DMAudio]",
               b"[Themes]", b"[Battles]", b"[NAPOWR]", b"[NATSLA]", b"[TESLA]",
               b"[TaskForce]", b"[Scripts]", b"[TeamTypes]", b"[Basic]"]

def sniff(head):
    if len(head) >= 4 and head[:4] == b" FSC": return "csf"
    if head[:4] == b"RIFF": return "wav"
    if head[:6].startswith(b"VQAV"): return "vqa"
    if head[:2] == b"BM": return "bmp"
    if printable_ratio(head[:48]) > 0.9 and (b"[" in head[:64] or head[:1] == b";"):
        return "ini"
    if printable_ratio(head[:32]) > 0.95: return "text?"
    return "bin"

# ---------------------------------------------------------------- census walk
rows = []          # csv rows
summary = []       # per-mix summary lines
found_key_ids = {} # id -> [locations]
KEY_IDS = {0xAF902833: "ARTMD.INI:crc_upper", 0x1F674573: "RULESMD.INI:crc_upper",
           0x743EBF9A: "ARTMD.INI:crc_upper_pad", 0x1B11A84E: "RULESMD.INI:crc_upper_pad",
           0x5B47D8D5: "W97_art_inner", 0xFBE0D09D: "W97_art_submix",
           0xA8548FD9: "W97_ra2_art_submix", 0xF91B2C8B: "W97_ra2_art_inner",
           0x8218F9F4: "W97_rules_exp01"}
W97_SHA = None
try:
    W97_SHA = hashlib.sha256(open(W97_ART, "rb").read()).hexdigest()
except Exception as e:
    P("WARN cannot read W97 art:", e)

def name_of(eid):
    hits = []
    for scheme, m in SMAPS.items():
        if eid in m:
            hits.append(f"{m[eid]}({scheme})")
    return "|".join(hits[:4])

def check_key(eid, loc):
    if eid in KEY_IDS:
        found_key_ids.setdefault(eid, []).append(loc)

def walk(fh, base, off, size, depth, path, mixlabel):
    """Parse and walk a MIX image located at file offset `off` length `size`."""
    fh.seek(off)
    head = fh.read(min(size, max(HEAD, 4096)))
    meta = parse_mix_image(head, size)
    if meta is None and len(head) < size:
        fh.seek(off); head = fh.read(size); meta = parse_mix_image(head, size)
    if meta is None:
        P(f"{'  '*depth}[unparseable] {path} size={size} head={head[:16].hex(' ')}")
        if depth == 0 and size > 10_000_000:  # theme-like TD debug
            count, body = struct.unpack_from("<HH", head, 0)
            P(f"    TD-guess: count={count} body={body:#x}")
            for i in range(min(count, 8)):
                e = head[4 + i*12: 16 + i*12]
                eid, eoff, esz = struct.unpack("<III", e)
                P(f"    entry[{i}] id={eid:08X} off={eoff} size={esz}")
            ds = 4 + count * 12
            fits = 0
            for i in range(count):
                eid, eoff, esz = struct.unpack_from("<III", head, 4 + i*12)
                if eoff + esz <= size - ds: fits += 1
            P(f"    entries fitting file (ds={ds}): {fits}/{count}")
        return None
    ents = meta["entries"]
    # choose data_start by content sanity across first few entries
    cands = meta["data_start_candidates"]
    if len(cands) == 1:
        ds_choice = cands[0]
    else:
        best, bestscore = cands[0], -1
        for ds in cands:
            score = 0
            for eid, eoff, esz in ents[:6]:
                if eoff + 8 > size: continue
                fh.seek(off + ds + eoff); probe = fh.read(8)
                if sniff(probe) != "bin": score += 1
            if score > bestscore:
                best, bestscore = ds, score
        ds_choice = best
    P(f"{'  '*depth}[mix] {path}: kind={meta['kind']} flags={meta['flags']:#06x} "
      f"count={meta['count']} data_start={ds_choice}")
    for eid, eoff, esz in ents:
        loc = f"{mixlabel}:{'/'.join(path + [f'{eid:08X}'])}"
        check_key(eid, loc)
        nm = name_of(eid)
        fh.seek(off + ds_choice + eoff)
        ehead = fh.read(min(esz, 64))
        kind = sniff(ehead)
        sub = None
        if depth < MAX_DEPTH and esz >= 10:
            fh.seek(off + ds_choice + eoff)
            ebig = fh.read(min(esz, max(HEAD, 4096)))
            emeta = parse_mix_image(ebig, esz)
            if emeta is None and len(ebig) < esz:
                fh.seek(off + ds_choice + eoff); ebig = fh.read(esz)
                emeta = parse_mix_image(ebig, esz)
            if emeta is not None:
                kind = "mix"
                sub = (off + ds_choice + eoff, esz)
        rows.append({"mix": mixlabel, "depth": depth, "path": "/".join(path), "id": f"{eid:08X}",
                     "offset": eoff, "size": esz, "kind": kind, "names": nm})
        if kind in ("ini", "text?") and esz >= 512:
            fh.seek(off + ds_choice + eoff)
            blob = fh.read(min(esz, 4_000_000))
            marks = {m.decode(): blob.count(m) for m in INI_MARKERS if m in blob}
            if marks or kind == "ini":
                first = blob.split(b"\n", 1)[0][:80]
                P(f"{'  '*depth}  [INI] {loc} size={esz} kind={kind} names={nm or '-'}")
                P(f"{'  '*depth}        first80: {first.hex(' ')} | {first.decode('ascii','replace')!r}")
                P(f"{'  '*depth}        markers: {marks}")
                rows[-1].update({"first_line_hex": first.hex(" "), "markers": json.dumps(marks)})
        if sub:
            walk(fh, base, sub[0], sub[1], depth + 1, path + [f"{eid:08X}"], mixlabel)
    return meta

# ---------------------------------------------------------------- per-mix loop
import glob
mixfiles = sorted(glob.glob(os.path.join(GAME, "*.mix")))
P("== census over", len(mixfiles), "top-level mixes ==")
for mf in mixfiles:
    label = os.path.basename(mf)
    fh = open(mf, "rb")
    size = os.path.getsize(mf)
    P("")
    P(f"### {label}  ({size} B)")
    try:
        meta = walk(fh, GAME, 0, size, 0, [], label)
        if meta is None:
            P(f"### {label}: NO INDEX PARSED")
    except Exception as e:
        import traceback; traceback.print_exc()
        P(f"### {label}: EXC {e}")
    fh.close()

# W97 art self-check: re-extract ra2md.mix -> FBE0D09D -> 5B47D8D5 and hash
P("")
P("== W97 art re-extraction self-check ==")
try:
    fh = open(os.path.join(GAME, "ra2md.mix"), "rb")
    size = os.path.getsize(os.path.join(GAME, "ra2md.mix"))
    fh.seek(0); head = fh.read(HEAD)
    m0 = parse_mix_image(head, size)
    ents0 = dict((e[0], e) for e in m0["entries"])
    ds0 = m0["data_start_candidates"][0]
    sid, soff, ssz = ents0[0xFBE0D09D]
    fh.seek(ds0 + soff); shead = fh.read(ssz)
    m1 = parse_mix_image(shead, ssz)
    ents1 = dict((e[0], e) for e in m1["entries"])
    ds1 = m1["data_start_candidates"][0]
    aid, aoff, asz = ents1[0x5B47D8D5]
    fh.seek(ds0 + soff + ds1 + aoff)
    art = fh.read(asz)
    sha = hashlib.sha256(art).hexdigest()
    P(f"submix 0xFBE0D09D: kind={m1['kind']} count={m1['count']}")
    P(f"all submix entries: " + ", ".join(f"{e[0]:08X}/{e[2]}B[{name_of(e[0]) or '-'}]" for e in m1["entries"]))
    P(f"inner 0x5B47D8D5 size={asz} sha256={sha}")
    P(f"W97 file  sha256={W97_SHA}")
    P(f"MATCH: {sha == W97_SHA}")
    # also dump the other INI-like entries of this submix fully for markers
    for eid, eoff, esz in m1["entries"]:
        if eid == 0x5B47D8D5: continue
        fh.seek(ds0 + soff + ds1 + eoff)
        blob = fh.read(min(esz, 4_000_000))
        marks = {m.decode(): blob.count(m) for m in INI_MARKERS if m in blob}
        first = blob.split(b"\n", 1)[0][:80]
        P(f"  submix entry {eid:08X} size={esz} names={name_of(eid) or '-'}")
        P(f"    first80: {first.hex(' ')} | {first.decode('ascii','replace')!r}")
        P(f"    markers: {marks}")
    fh.close()
except Exception as e:
    import traceback; traceback.print_exc()

P("")
P("== key id presence across ALL mixes/depths ==")
if not found_key_ids:
    P("(none of the key ids appear in any parsed mix index)")
for eid, locs in sorted(found_key_ids.items()):
    P(f"{eid:08X} {KEY_IDS[eid]}: {len(locs)} hit(s)")
    for l in locs[:20]:
        P("   ", l)

P("")
P("== totals ==")
P("rows (entries incl. nested):", len(rows))
kinds = {}
for r in rows: kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
P("kinds:", kinds)

with open(os.path.join(OUTD, "mix_census_entries.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["mix", "depth", "path", "id", "offset", "size", "kind",
                                      "names", "first_line_hex", "markers"])
    w.writeheader()
    for r in rows:
        w.writerow(r)
json.dump(rows, open(os.path.join(OUTD, "mix_census.json"), "w", encoding="utf-8"), indent=1)
open(os.path.join(OUTD, "step3_mix_census.txt"), "w", encoding="utf-8").write("\n".join(PBUF) + "\n")
print("\nsaved census outputs ->", OUTD)
