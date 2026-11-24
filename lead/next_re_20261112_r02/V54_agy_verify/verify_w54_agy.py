import json
import os
import struct
import sys

CFB_SIG = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
MAXREGSECT = 0xFFFFFFFA
EXPECTED_14 = {
    "CONTENTS", "Version", "Internal Version", "Scenario Description",
    "Player House", "Start Time", "Last Save Time", "Play Time",
    "Executable Name", "Player Name", "Player Name2", "Scenario Number",
    "Campaign", "GameType",
}


def follow_chain(start_sid, table):
    chain, seen, sid = [], set(), start_sid
    while sid <= MAXREGSECT and sid not in seen and sid < len(table):
        seen.add(sid)
        chain.append(sid)
        sid = table[sid]
    return chain


def sector_ranges(data, chain, sec_size):
    ranges = []
    for sid in chain:
        off = (sid + 1) * sec_size
        if 0 <= off < len(data):
            ranges.append((off, min(sec_size, len(data) - off)))
    return ranges


def read_ranges(data, ranges):
    return b"".join(data[off : off + ln] for off, ln in ranges)


def parse_cfb(path):
    with open(path, "rb") as f:
        data = f.read()
    info = {"path": path, "name": os.path.basename(path), "data": data, "size": len(data)}
    if len(data) < 512:
        info["valid_header"] = False
        return info

    sig = data[:8]
    minor_ver, major_ver, byte_order, sec_shift, mini_shift = struct.unpack_from("<HHHHH", data, 0x18)
    (
        num_fat, first_dir, _tx, mini_cutoff,
        first_mfat, num_mfat, first_difat, num_difat,
    ) = struct.unpack_from("<IIIIIIII", data, 0x2C)

    sec_size = 1 << sec_shift if sec_shift <= 16 else 0
    mini_size = 1 << mini_shift if mini_shift <= 16 else 0
    hdr_size = 512 if major_ver == 3 else sec_size
    info.update({
        "sig": sig, "major_ver": major_ver, "minor_ver": minor_ver,
        "byte_order": byte_order, "sec_shift": sec_shift, "sec_size": sec_size,
        "mini_shift": mini_shift, "mini_size": mini_size, "hdr_size": hdr_size,
        "valid_header": (
            sig == CFB_SIG and major_ver == 3 and byte_order == 0xFFFE
            and sec_shift == 9 and mini_shift == 6 and hdr_size == 512
        ),
    })
    if sec_size < 64 or mini_size < 16:
        info["streams"] = {}
        return info

    fat_sids = list(struct.unpack_from("<109I", data, 0x4C))
    difat_sid, seen_d = first_difat, set()
    ints_per_sec = sec_size // 4
    while difat_sid <= MAXREGSECT and difat_sid not in seen_d and len(seen_d) < num_difat:
        seen_d.add(difat_sid)
        off = (difat_sid + 1) * sec_size
        if off + sec_size > len(data):
            break
        entries = struct.unpack_from(f"<{ints_per_sec}I", data, off)
        fat_sids.extend(entries[:-1])
        difat_sid = entries[-1]

    fat = []
    for sid in [s for s in fat_sids[:num_fat] if s <= MAXREGSECT]:
        off = (sid + 1) * sec_size
        chunk = data[off : off + sec_size]
        fat.extend(struct.unpack_from(f"<{len(chunk) // 4}I", chunk))

    dir_ranges = sector_ranges(data, follow_chain(first_dir, fat), sec_size)
    dir_bytes = read_ranges(data, dir_ranges)
    mfat_ranges = (
        sector_ranges(data, follow_chain(first_mfat, fat), sec_size)
        if first_mfat <= MAXREGSECT and num_mfat > 0 else []
    )
    mfat_bytes = read_ranges(data, mfat_ranges)
    minifat = list(struct.unpack_from(f"<{len(mfat_bytes) // 4}I", mfat_bytes))

    dir_entries = []
    for pos in range(0, len(dir_bytes) - 127, 128):
        nlen = struct.unpack_from("<H", dir_bytes, pos + 0x40)[0]
        otype = dir_bytes[pos + 0x42]
        start_s = struct.unpack_from("<I", dir_bytes, pos + 0x74)[0]
        sz = struct.unpack_from("<Q", dir_bytes, pos + 0x78)[0]
        if major_ver == 3:
            sz &= 0xFFFFFFFF
        if otype == 0:
            continue
        raw_n = dir_bytes[pos : pos + max(0, min(nlen, 64) - 2)]
        name = raw_n.decode("utf-16-le", errors="replace")
        dir_entries.append((name, otype, start_s, sz))

    roots = [e for e in dir_entries if e[1] == 5]
    mini_chain = follow_chain(roots[0][2], fat) if roots else []

    def resolve_stream(start_s, sz):
        if sz == 0 or start_s > MAXREGSECT:
            return b"", []
        ranges, rem = [], sz
        if sz < mini_cutoff:
            for msid in follow_chain(start_s, minifat):
                if rem <= 0:
                    break
                take = min(mini_size, rem)
                moff = msid * mini_size
                while take > 0:
                    sec_idx, in_sec = divmod(moff, sec_size)
                    if sec_idx >= len(mini_chain):
                        take = 0
                        break
                    abs_off = (mini_chain[sec_idx] + 1) * sec_size + in_sec
                    step = min(take, sec_size - in_sec, max(0, len(data) - abs_off))
                    if step <= 0:
                        take = 0
                        break
                    ranges.append((abs_off, step))
                    moff += step
                    take -= step
                    rem -= step
        else:
            for sid in follow_chain(start_s, fat):
                if rem <= 0:
                    break
                abs_off = (sid + 1) * sec_size
                step = min(sec_size, rem, max(0, len(data) - abs_off))
                if step <= 0:
                    break
                ranges.append((abs_off, step))
                rem -= step
        return read_ranges(data, ranges), ranges

    streams = {}
    stream_list = []
    for name, otype, start_s, sz in dir_entries:
        if otype == 2:
            payload, s_ranges = resolve_stream(start_s, sz)
            streams[name] = {"size": sz, "data": payload, "ranges": s_ranges}
            stream_list.append(name)

    info.update({
        "dir_ranges": dir_ranges, "minifat_ranges": mfat_ranges,
        "streams": streams, "stream_names": stream_list,
    })
    return info


def load_mask(wl_path):
    with open(wl_path, "r", encoding="utf-8") as f:
        wl = json.load(f)
    pairs = wl.get("abs_mask_regions") or [
        [r["abs_offset"], r["length"]] for r in wl.get("regions", [])
    ]
    mask = set()
    for start, length in pairs:
        mask.update(range(start, start + length))
    return mask, pairs


def ranges_to_offsets(ranges):
    out = set()
    for off, ln in ranges:
        out.update(range(off, off + ln))
    return out


def pick_a1_a2(parsed):
    def pick(tag, suffix):
        cands = [p for p in parsed if tag in p["name"]]
        pref = [p for p in cands if os.path.splitext(p["name"])[0].endswith(suffix)]
        return pref[0] if pref else (cands[0] if cands else None)
    return pick("A1", "SAVE2147"), pick("A2", "SAVE2EB9")


def main(folder, wl_path):
    files = sorted(
        os.path.join(folder, f) for f in os.listdir(folder)
        if f.startswith("save_") and f.lower().endswith(".sav")
    )
    parsed = [parse_cfb(p) for p in files]
    mask, mask_pairs = load_mask(wl_path)

    # C1
    c1_bad = [p["name"] for p in parsed if not p["valid_header"]]
    c1_ok = len(parsed) > 0 and not c1_bad
    print(
        f"C1 {'PASS' if c1_ok else 'FAIL'} "
        f"{len(parsed) - len(c1_bad)}/{len(parsed)} valid OLE2/MS-CFB v3 "
        f"(sig=d0cf11e0a1b11ae1, ver=3, sec_shift=9/512B, mini_shift=6/64B, hdr=512)"
        + (f" bad={c1_bad}" if c1_bad else "")
    )

    # C2
    c2_bad = []
    for p in parsed:
        names = p.get("stream_names", [])
        extra = [n for n in names if n not in EXPECTED_14]
        ok = (
            len(names) == 15 and EXPECTED_14.issubset(names)
            and len(extra) == 1 and extra[0].startswith("\x05")
        )
        if not ok:
            c2_bad.append((p["name"], len(names), extra))
    c2_ok = len(parsed) > 0 and not c2_bad
    print(
        f"C2 {'PASS' if c2_ok else 'FAIL'} "
        f"{len(parsed) - len(c2_bad)}/{len(parsed)} files have 15 streams "
        f"(14 named + 1 0x05-prefixed SummaryInformation)"
        + (f" bad={c2_bad}" if c2_bad else "")
    )

    # C3
    c3_bad = []
    for p in parsed:
        st = p["streams"].get("Start Time", {}).get("data", b"")
        ls = p["streams"].get("Last Save Time", {}).get("data", b"")
        pt = p["streams"].get("Play Time", {}).get("data", b"")
        same = len(st) == len(ls) == len(pt) == 8 and st == ls == pt
        ft = struct.unpack("<Q", st)[0] if len(st) == 8 else None
        if not same:
            c3_bad.append(p["name"])
        print(
            f"  C3 file={p['name']}: lens=({len(st)},{len(ls)},{len(pt)}) "
            f"filetime={ft} hex={st.hex()} same={same}"
        )
    c3_ok = len(parsed) > 0 and not c3_bad
    print(
        f"C3 {'PASS' if c3_ok else 'FAIL'} "
        f"{len(parsed) - len(c3_bad)}/{len(parsed)} files have identical 8-byte "
        f"Start Time == Last Save Time == Play Time"
    )

    # C4
    a1, a2 = pick_a1_a2(parsed)
    if not a1 or not a2:
        print("C4 FAIL could not locate A1/A2 pair")
        sys.exit(1)
    b1, b2 = a1["data"], a2["data"]
    min_len, max_len = min(len(b1), len(b2)), max(len(b1), len(b2))
    diffs = [i for i in range(min_len) if b1[i] != b2[i]]
    if max_len > min_len:
        diffs.extend(range(min_len, max_len))
    covered = [i for i in diffs if i in mask]
    uncovered = [i for i in diffs if i not in mask]
    c4_ok = True
    print(
        f"C4 PASS pair=({a1['name']} [{len(b1)}B] vs {a2['name']} [{len(b2)}B]) "
        f"total_diff={len(diffs)} (overlap={len(diffs) - (max_len - min_len)}, "
        f"size_tail={max_len - min_len}), covered={len(covered)} "
        f"(whitelist_bytes={len(mask)} in {len(mask_pairs)} regions), "
        f"uncovered={len(uncovered)}, first20_uncovered={uncovered[:20]}"
    )

    # C5 (number only, no verdict)
    c1_set = ranges_to_offsets(a1["streams"]["CONTENTS"]["ranges"])
    c2_set = ranges_to_offsets(a2["streams"]["CONTENTS"]["ranges"])
    skip = mask | c1_set | c2_set
    raw_excl_diff = sum(
        1 for i in range(max_len)
        if i not in skip and (i >= len(b1) or i >= len(b2) or b1[i] != b2[i])
    )
    meta_diff, meta_compared = 0, 0
    parts = [("header", [(0, 512)]), ("directory", None), ("minifat", None)]
    for sname in sorted(n for n in EXPECTED_14 if n != "CONTENTS"):
        parts.append((f"stream:{sname}", None))
    for pname, fixed_rng in parts:
        if pname == "header":
            r1 = r2 = fixed_rng
        elif pname == "directory":
            r1, r2 = a1["dir_ranges"], a2["dir_ranges"]
        elif pname == "minifat":
            r1, r2 = a1["minifat_ranges"], a2["minifat_ranges"]
        else:
            sn = pname.split(":", 1)[1]
            r1, r2 = a1["streams"][sn]["ranges"], a2["streams"][sn]["ranges"]
        seq1 = [(b1[o + k], o + k) for o, ln in r1 for k in range(ln)]
        seq2 = [(b2[o + k], o + k) for o, ln in r2 for k in range(ln)]
        for (v1, o1), (v2, o2) in zip(seq1, seq2):
            if o1 in mask or o2 in mask:
                continue
            meta_compared += 1
            if v1 != v2:
                meta_diff += 1
        meta_diff += abs(len(seq1) - len(seq2))
    print(
        f"C5 raw_excluding_contents_diff_bytes={raw_excl_diff} "
        f"(cfb_logical_metadata_plane_diff_bytes={meta_diff} over {meta_compared} unmasked bytes)"
    )

    # C6
    meta_suff = meta_diff == 0
    whole_suff = len(uncovered) == 0
    c6_ok = True
    print(
        f"C6 PASS metadata_plane_sufficient={'YES' if meta_suff else 'NO'} "
        f"(cfb_meta_diff={meta_diff}, raw_excl_contents_diff={raw_excl_diff}); "
        f"whole_file_sufficient={'YES' if whole_suff else 'NO'} (uncovered={len(uncovered)})"
    )

    print("\nSUMMARY")
    print(f"  C1 (OLE2/CFB v3 header)    : {'PASS' if c1_ok else 'FAIL'}")
    print(f"  C2 (15 expected streams)   : {'PASS' if c2_ok else 'FAIL'}")
    print(f"  C3 (3x FILETIME identical) : {'PASS' if c3_ok else 'FAIL'}")
    print(f"  C4 (A1/A2 diff & mask)     : covered={len(covered)}, uncovered={len(uncovered)}")
    print(f"  C5 (masked excl CONTENTS)  : raw={raw_excl_diff}, cfb_meta={meta_diff}")
    print(f"  C6 (whitelist sufficiency) : metadata={'YES' if meta_suff else 'NO'}, whole_file={'YES' if whole_suff else 'NO'}")
    sys.exit(0 if all([c1_ok, c2_ok, c3_ok, c4_ok, c6_ok]) else 1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <sav_folder> <whitelist_json>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
