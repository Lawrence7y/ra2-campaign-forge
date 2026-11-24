#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W55b - CFB named-stream comparator (W54 §5.3 preconditions 3 & 4).

Reuses W54 EVIDENCE/step2_cfb.py's `CFB` class WITHOUT executing its driver:
the source is truncated at `def hx(` and exec'd into an isolated namespace.

Outputs (all inside W55b_equivalence_rerun/out/):
  cfb_compare.json        full per-save / per-pair stream data
  stream_matrix.json      per-save per-stream sha256 + diff-vs-reference
  contents_structure.json CONTENTS structural-parse attempt (W54 §5.3-3)
  CFB_COMPARE_TABLE.md    human-readable table for the report
  whitelist_crosscheck.json  reproduction of W54's 4-reference validation

COORDINATE SYSTEM (task-mandated correction): .SAV is OLE2 / MS-CFB, NOT a
flat byte stream.  FAT/DIFAT/miniFAT allocation tables are EXCLUDED by
construction; comparison is by NAMED STREAM.  The metadata plane is masked
with W54's a priori whitelist in CFB-logical coordinates (stream+offset+len),
exactly as W54 EVIDENCE/step6_whitelist.py build_view/mask_view.
"""
from __future__ import annotations

import hashlib
import json
import struct
from itertools import combinations
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
R02 = ROOT / "lead" / "next_re_20261112_r02"
CARD = R02 / "W55b_equivalence_rerun"
OUT = CARD / "out"
STEP2 = R02 / "W54_save_determinism" / "EVIDENCE" / "step2_cfb.py"
WL = OUT / "whitelist_applied.json"
W45_REF = OUT / "w45_ref"

# ---------------------------------------------------------------- load CFB class
_src = STEP2.read_text(encoding="utf-8")
_head = _src.split("def hx(")[0]          # everything before the driver
_ns = {"__name__": "w55b_step2_cfb"}
exec(compile(_head, str(STEP2), "exec"), _ns)
CFB = _ns["CFB"]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def hx(b: bytes, n: int = 24) -> str:
    return " ".join("%02x" % x for x in b[:n])


# ---------------------------------------------------------------- whitelist
wl = json.loads(WL.read_text(encoding="utf-8"))
REGIONS = wl["regions"]
ABS_MASK = set()
for a, n in wl["abs_mask_regions"]:
    ABS_MASK.update(range(a, a + n))


def stream_mask_positions(name: str):
    return [(r["offset"], r["length"]) for r in REGIONS if r["stream"] == name]


def mask_named_stream(name: str, data: bytes) -> bytes:
    b = bytearray(data)
    for off, ln in stream_mask_positions(name):
        for i in range(off, min(off + ln, len(b))):
            b[i] = 0
    return bytes(b)


def build_view(c):
    """W54 step6_whitelist.py:39-48 - flat 'metadata plane' view."""
    parts = [("header", c.b[:512]), ("directory", c.dir_bytes),
             ("minifat", b"".join(c.sector(s) for s in [c.first_minifat]))]
    st = c.streams()
    for e in c.entries:
        if e["type"] == 2 and e["name"] != "CONTENTS":
            parts.append((e["name"], st[e["name"]]["data"]))
    flat = bytearray()
    bases = {}
    for name, data in parts:
        bases[name] = len(flat)
        flat.extend(data)
    return bytes(flat), bases, parts


def mask_view(c):
    flat, bases, _ = build_view(c)
    b = bytearray(flat)
    for r in REGIONS:
        base = bases.get(r["stream"])
        if base is None:
            continue
        for o in range(r["offset"], r["offset"] + r["length"]):
            if base + o < len(b):
                b[base + o] = 0
    return bytes(b)


def mask_raw(b: bytes) -> bytes:
    x = bytearray(b)
    for o in ABS_MASK:
        if o < len(x):
            x[o] = 0
    return bytes(x)


def diff_bytes(a: bytes, b: bytes):
    n = min(len(a), len(b))
    d = sum(1 for i in range(n) if a[i] != b[i])
    first = next((i for i in range(n) if a[i] != b[i]), None)
    return d, first


def lcp_lcs(a: bytes, b: bytes):
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    j = 0
    while j < n - i and a[len(a) - 1 - j] == b[len(b) - 1 - j]:
        j += 1
    return i, j


# ---------------------------------------------------------------- CONTENTS structure
def try_contents_structure(data: bytes):
    """W54 §5.3-3 / §4.4: try to walk CONTENTS as compressed/chunked blocks.
    W54 already found these walks fail at block 2-3; we repeat the attempt
    honestly and record the result instead of assuming success."""
    attempts = []
    for start in (0, 4, 8, 0x3C, 0x40):
        # (A) (u16 uncompressed_len, u16 compressed_len) LCW/LZO-style
        off, blocks, reason = start, [], None
        while off + 4 <= len(data):
            unc, cmp = struct.unpack_from("<HH", data, off)
            if cmp == 0 or unc == 0 or cmp > 0x8000 or off + 4 + cmp > len(data):
                reason = "bad_block_header unc=%d cmp=%d @off=%d" % (unc, cmp, off)
                break
            blocks.append({"off": off, "unc": unc, "cmp": cmp})
            off += 4 + cmp
            if len(blocks) > 200000:
                reason = "block_count_cap"
                break
        consumed = off - start
        attempts.append({"scheme": "u16_unc_u16_cmp_LCW_LZO", "start": start,
                         "n_blocks": len(blocks), "consumed": consumed,
                         "total": len(data),
                         "coverage": round(consumed / len(data), 6) if data else 0,
                         "first_blocks": blocks[:6], "failure": reason,
                         "success": reason is None and consumed >= len(data) * 0.95})
        # (B) (u32 length + payload) chunk walk
        off, blocks, reason = start, [], None
        while off + 4 <= len(data):
            ln = struct.unpack_from("<I", data, off)[0]
            if ln == 0 or ln > 0x100000 or off + 4 + ln > len(data):
                reason = "bad_u32_length ln=%d @off=%d" % (ln, off)
                break
            blocks.append({"off": off, "len": ln})
            off += 4 + ln
            if len(blocks) > 200000:
                reason = "block_count_cap"
                break
        consumed = off - start
        attempts.append({"scheme": "u32_len_payload", "start": start,
                         "n_blocks": len(blocks), "consumed": consumed,
                         "total": len(data),
                         "coverage": round(consumed / len(data), 6) if data else 0,
                         "first_blocks": blocks[:6], "failure": reason,
                         "success": reason is None and consumed >= len(data) * 0.95})
    parsed = next((a for a in attempts if a["success"]), None)
    return {"structure_parsed": parsed is not None,
            "parsed_scheme": parsed["scheme"] if parsed else None,
            "parsed_start": parsed["start"] if parsed else None,
            "attempts": attempts,
            "fallback": ("rectified whole-stream sha256 after frame alignment"
                         if parsed is None else "block-sequence comparison"),
            "note": ("W54 §4.4 already reported these walks fail at block 2-3 "
                     "and that LZO/LCW was NOT confirmed. If all attempts fail "
                     "here, the fallback is used and stated explicitly.")}


# ---------------------------------------------------------------- inventory
def load_saves():
    """Return list of save records. W55b saves are the PRIMARY evidence;
    W45 refs are included ONLY for the W54 cross-check."""
    runs = json.loads((OUT / "dual_track_results.json").read_text(encoding="utf-8")) \
        if (OUT / "dual_track_results.json").is_file() else {}
    # dual_track_results.json is rewritten by EACH --phase run invocation, so
    # the last invocation only holds its own tags.  Merge in every
    # <tag>_result.json so earlier trips (e.g. the A1 pilot) keep their
    # alignment metadata.
    for rp in sorted(OUT.glob("*_result.json")):
        if rp.name == "dual_track_results.json":
            continue
        try:
            runs.setdefault(rp.stem.replace("_result", ""),
                            json.loads(rp.read_text(encoding="utf-8")))
        except Exception:
            pass
    # index by save copy basename
    meta = {}
    for tag, rec in runs.items():
        for s in (rec.get("saves") or []):
            meta[Path(s["copy"]).name] = {
                "tag": tag, "arm": rec.get("arm"),
                "attempt": s.get("attempt"),
                "frame_frozen": s.get("frame_frozen"),
                "alignment_key": s.get("alignment_key"),
                "frame_before_dialog": s.get("frame_before_dialog"),
                "frame_after_save": s.get("frame_after_save"),
                "aligned_to_first": s.get("aligned_to_first"),
            }
        if rec.get("save"):
            s = rec["save"]
            meta.setdefault(Path(s["copy"]).name, {
                "tag": tag, "arm": rec.get("arm"), "attempt": 0,
                "frame_frozen": (rec.get("alignment") or {}).get("frame_frozen"),
                "alignment_key": (rec.get("alignment") or {}).get("frame_frozen"),
                "frame_before_dialog": None, "frame_after_save": None,
                "aligned_to_first": True})
    out = []
    for p in sorted(OUT.glob("save_*.SAV")):
        m = meta.get(p.name, {})
        out.append({"id": p.stem, "path": p, "kind": "w55b", **m})

    # ---- HONESTY DEDUP -------------------------------------------------
    # Each trip attempted TWO saves inside the same frozen menu.  The engine
    # reused the SAME generated filename and emitted byte-identical bytes for
    # both attempts (verified by sha256).  Those are NOT independent samples:
    # counting them twice would manufacture a fake "N=0" noise baseline.
    # Keep only the FIRST occurrence of each distinct file sha256, and record
    # every duplicate path in out/save_dedup.json for the Lead to re-check.
    seen, dedup, kept = {}, [], []
    for r in out:
        h = sha(r["path"].read_bytes())
        if h in seen:
            dedup.append({"duplicate_path": str(r["path"]),
                          "kept_path": str(seen[h]["path"]),
                          "sha256": h,
                          "reason": "byte-identical second save in same frozen menu; "
                                    "NOT an independent sample"})
        else:
            seen[h] = r
            kept.append(r)
    (OUT / "save_dedup.json").write_text(
        json.dumps({"kind": "w55b_save_dedup",
                    "w55b_sav_files_on_disk": len(out),
                    "distinct_sha256": len(kept),
                    "duplicates_removed": len(dedup),
                    "kept": [{"id": r["id"], "path": str(r["path"]),
                              "sha256": sha(r["path"].read_bytes())}
                             for r in kept],
                    "duplicates": dedup},
                   ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")
    out = kept

    for p in sorted(W45_REF.glob("*.SAV")):
        out.append({"id": "W45REF_" + p.stem, "path": p, "kind": "w45_ref",
                    "tag": p.stem.split("_")[1], "arm": p.stem.split("_")[1][0],
                    "attempt": 0, "frame_frozen": None,
                    "alignment_key": None, "aligned_to_first": None})
    return out


def parse_save(rec):
    p = rec["path"]
    c = CFB(str(p))
    st = c.streams()
    streams = {}
    for name, s in st.items():
        d = s["data"]
        md = mask_named_stream(name, d)
        streams[name] = {
            "len": len(d), "sha256_raw": sha(d), "sha256_masked": sha(md),
            "head_hex": hx(d), "loc": s["loc"],
            "mask_positions": stream_mask_positions(name),
        }
    raw = p.read_bytes()
    contents = st.get("CONTENTS", {}).get("data", b"")
    return {
        "id": rec["id"], "kind": rec["kind"], "tag": rec.get("tag"),
        "arm": rec.get("arm"), "attempt": rec.get("attempt"),
        "path": str(p),
        "frame_frozen": rec.get("frame_frozen"),
        "alignment_key": rec.get("alignment_key"),
        "frame_before_dialog": rec.get("frame_before_dialog"),
        "frame_after_save": rec.get("frame_after_save"),
        "aligned_to_first": rec.get("aligned_to_first"),
        "file_size": len(raw), "file_sha256": sha(raw),
        "file_sha256_8": sha(raw)[:8],
        "contents_len": len(contents),
        "n_streams": len(st),
        "stream_names": sorted(st.keys()),
        "streams": streams,
        "metadata_view_sha256_raw": sha(build_view(c)[0]),
        "metadata_view_sha256_masked": sha(mask_view(c)),
        "metadata_view_len": len(build_view(c)[0]),
        "raw_masked_sha256": sha(mask_raw(raw)),
        "_c": c, "_streams_raw": {k: v["data"] for k, v in st.items()},
    }


# ---------------------------------------------------------------- pair compare
def compare_pair(A, B):
    res = {"x": A["id"], "y": B["id"], "streams": {}, "metadata_plane": {},
           "raw_file_masked": {}, "contents": {}}
    names = sorted(set(A["streams"]) | set(B["streams"]))
    for name in names:
        ax = A["_streams_raw"].get(name)
        by = B["_streams_raw"].get(name)
        if ax is None or by is None:
            res["streams"][name] = {"present_in_both": False,
                                    "len_x": len(ax) if ax is not None else None,
                                    "len_y": len(by) if by is not None else None}
            continue
        am, bm = mask_named_stream(name, ax), mask_named_stream(name, by)
        d_raw, f_raw = diff_bytes(ax, by)
        d_mask, f_mask = diff_bytes(am, bm)
        res["streams"][name] = {
            "present_in_both": True,
            "len_x": len(ax), "len_y": len(by), "same_len": len(ax) == len(by),
            "sha256_raw_x": sha(ax), "sha256_raw_y": sha(by),
            "sha256_masked_x": sha(am), "sha256_masked_y": sha(bm),
            "diff_bytes_raw": d_raw, "first_diff_raw": f_raw,
            "diff_bytes_masked": d_mask, "first_diff_masked": f_mask,
            "equal_raw": ax == by, "equal_masked": am == bm,
        }
    av, bv = build_view(A["_c"])[0], build_view(B["_c"])[0]
    amv, bmv = mask_view(A["_c"]), mask_view(B["_c"])
    dr, fr = diff_bytes(av, bv)
    dm, fm = diff_bytes(amv, bmv)
    res["metadata_plane"] = {
        "len_x": len(av), "len_y": len(bv),
        "diff_bytes_raw": dr, "first_diff_raw": fr,
        "diff_bytes_masked": dm, "first_diff_masked": fm,
        "equal_raw": av == bv, "equal_masked": amv == bmv,
        "sha256_raw_x": sha(av), "sha256_raw_y": sha(bv),
        "sha256_masked_x": sha(amv), "sha256_masked_y": sha(bmv),
    }
    ax = mask_raw(Path(A["path"]).read_bytes())
    by = mask_raw(Path(B["path"]).read_bytes())
    dr, fr = diff_bytes(ax, by)
    res["raw_file_masked"] = {
        "len_x": len(ax), "len_y": len(by), "compared": min(len(ax), len(by)),
        "diff_bytes": dr, "first_diff": fr,
        "equal_in_compared_window": dr == 0,
        "full_files_equal": ax == by,
        "sha256_masked_x": sha(ax), "sha256_masked_y": sha(by),
    }
    cx, cy = A["_streams_raw"].get("CONTENTS", b""), B["_streams_raw"].get("CONTENTS", b"")
    d, f = diff_bytes(cx, cy)
    lp, ls = lcp_lcs(cx, cy)
    res["contents"] = {
        "len_x": len(cx), "len_y": len(cy), "same_len": len(cx) == len(cy),
        "sha256_x": sha(cx), "sha256_y": sha(cy),
        "equal": cx == cy, "diff_bytes": d, "first_diff": f,
        "lcp": lp, "lcs": ls,
    }
    return res


# ---------------------------------------------------------------- main
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    recs = load_saves()
    if not recs:
        print("NO SAVES FOUND")
        return 3
    parsed = [parse_save(r) for r in recs]
    for p in parsed:
        p["contents_structure"] = try_contents_structure(
            p["_streams_raw"].get("CONTENTS", b""))

    # W54 cross-check: reproduce the 4-reference metadata-plane validation
    refs = [p for p in parsed if p["kind"] == "w45_ref"]
    xcheck = {"whitelist_sha256": sha(WL.read_bytes()),
              "whitelist_regions": len(REGIONS),
              "whitelist_abs_mask_bytes": len(ABS_MASK),
              "metadata_plane_pairs": {},
              "raw_file_masked_pairs": {}}
    refmap = {p["tag"]: p for p in refs}
    for a, b in (("A1", "A2"), ("B1", "B2"), ("A1", "B1"), ("A2", "B2")):
        if a in refmap and b in refmap:
            cp = compare_pair(refmap[a], refmap[b])
            xcheck["metadata_plane_pairs"]["%s_vs_%s" % (a, b)] = cp["metadata_plane"]
            xcheck["raw_file_masked_pairs"]["%s_vs_%s" % (a, b)] = cp["raw_file_masked"]
    (OUT / "whitelist_crosscheck.json").write_text(
        json.dumps(xcheck, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")

    # all-pairs comparison (W55b primary + W45 refs)
    pairs = {}
    for A, B in combinations(parsed, 2):
        key = "%s__%s" % (A["id"], B["id"])
        pairs[key] = compare_pair(A, B)

    # stream matrix: per-save per-stream sha + diff vs a common reference
    prim = [p for p in parsed if p["kind"] == "w55b"]
    reference = prim[0] if prim else parsed[0]
    matrix = {"reference": reference["id"], "saves": []}
    for p in parsed:
        row = {"id": p["id"], "kind": p["kind"], "arm": p["arm"],
               "tag": p["tag"], "attempt": p["attempt"],
               "frame_frozen": p["frame_frozen"],
               "alignment_key": p["alignment_key"],
               "aligned_to_first": p["aligned_to_first"],
               "file_size": p["file_size"],
               "file_sha256_8": p["file_sha256_8"],
               "contents_len": p["contents_len"],
               "metadata_view_len": p["metadata_view_len"],
               "n_streams": p["n_streams"],
               "streams": {}}
        for name, s in p["streams"].items():
            row["streams"][name] = {
                "len": s["len"], "sha256_raw": s["sha256_raw"],
                "sha256_masked": s["sha256_masked"],
                "diff_bytes_masked_vs_ref": None}
            r = pairs.get("%s__%s" % (reference["id"], p["id"])) or \
                pairs.get("%s__%s" % (p["id"], reference["id"]))
            if r and name in r["streams"] and r["streams"][name].get("present_in_both"):
                row["streams"][name]["diff_bytes_masked_vs_ref"] = \
                    r["streams"][name]["diff_bytes_masked"]
        matrix["saves"].append(row)

    payload = {
        "kind": "w55b_cfb_compare",
        "coordinate_space": "cfb_named_stream",
        "container_excluded": ["FAT", "DIFAT", "miniFAT"],
        "whitelist": {"path": str(WL), "sha256": sha(WL.read_bytes()),
                      "regions": len(REGIONS), "abs_mask_bytes": len(ABS_MASK),
                      "coordinate_space": wl.get("coordinate_space")},
        "contents_structure_summary": {
            "any_structure_parsed": any(p["contents_structure"]["structure_parsed"]
                                        for p in parsed),
            "fallback": parsed[0]["contents_structure"]["fallback"] if parsed else None,
            "note": parsed[0]["contents_structure"]["note"] if parsed else None},
        "saves": [{k: v for k, v in p.items() if not k.startswith("_")}
                  for p in parsed],
        "pairs": pairs,
    }
    (OUT / "cfb_compare.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")
    (OUT / "stream_matrix.json").write_text(
        json.dumps(matrix, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")
    (OUT / "contents_structure.json").write_text(
        json.dumps([{"id": p["id"], **p["contents_structure"]} for p in parsed],
                   ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")

    # ---- human-readable table ----
    L = []
    L.append("# W55b · CFB 逐 stream 比较表")
    L.append("")
    L.append("坐标系：MS-CFB 具名 stream（FAT/DIFAT/miniFAT 按构造排除）。"
             "掩码 = W54 白名单 %d region / %d 绝对字节（sha256 `%s`）。"
             % (len(REGIONS), len(ABS_MASK), sha(WL.read_bytes())[:8]))
    L.append("CONTENTS 结构解析：%s；口径：%s。"
             % (payload["contents_structure_summary"]["any_structure_parsed"],
                payload["contents_structure_summary"]["fallback"]))
    L.append("")
    L.append("## 每份存档")
    L.append("")
    L.append("| id | arm | tag | frame_frozen | size | sha256[:8] | CONTENTS len | metadata_view len | #streams |")
    L.append("|---|---|---|---|---:|---|---:|---:|---:|")
    for p in parsed:
        L.append("| %s | %s | %s | %s | %d | %s | %d | %d | %d |"
                 % (p["id"], p["arm"], p["tag"], p["frame_frozen"],
                    p["file_size"], p["file_sha256_8"], p["contents_len"],
                    p["metadata_view_len"], p["n_streams"]))
    L.append("")
    L.append("## 逐 stream 差异字节数（掩码后，vs 参考 `%s`）" % reference["id"])
    L.append("")
    names = sorted({n for p in parsed for n in p["streams"]})
    L.append("| stream | " + " | ".join(p["id"] for p in parsed) + " |")
    L.append("|---|" + "---|" * len(parsed))
    for n in names:
        cells = []
        for p in parsed:
            r = pairs.get("%s__%s" % (reference["id"], p["id"])) or \
                pairs.get("%s__%s" % (p["id"], reference["id"]))
            v = (r["streams"][n].get("diff_bytes_masked")
                 if r and n in r["streams"] and r["streams"][n].get("present_in_both")
                 else None)
            cells.append(str(v) if v is not None else "-")
        L.append("| `%s` | %s |" % (n.replace("|", "\\|"), " | ".join(cells)))
    L.append("")
    L.append("## 配对：元数据平面（掩码后）与 CONTENTS 整流")
    L.append("")
    L.append("| pair | meta diff_raw | meta diff_masked | meta equal_masked | CONTENTS len x/y | CONTENTS sha equal | CONTENTS diff_bytes |")
    L.append("|---|---:|---:|---|---|---|---:|")
    for k, r in sorted(pairs.items()):
        m, c = r["metadata_plane"], r["contents"]
        L.append("| %s | %d | %d | %s | %d/%d | %s | %d |"
                 % (k, m["diff_bytes_raw"], m["diff_bytes_masked"],
                    m["equal_masked"], c["len_x"], c["len_y"],
                    c["equal"], c["diff_bytes"]))
    (OUT / "CFB_COMPARE_TABLE.md").write_text("\n".join(L) + "\n",
                                              encoding="utf-8")
    print(json.dumps({
        "saves": len(parsed), "w55b_saves": len(prim), "w45_refs": len(refs),
        "w55b_sav_files_on_disk": len(list(OUT.glob("save_*.SAV"))),
        "w55b_distinct_sha256": len(prim),
        "pairs": len(pairs), "streams": len(names),
        "contents_structure_parsed": payload["contents_structure_summary"]["any_structure_parsed"],
        "fallback": payload["contents_structure_summary"]["fallback"],
        "crosscheck_metadata_pairs": {k: v["equal_masked"] for k, v in
                                      xcheck["metadata_plane_pairs"].items()},
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
