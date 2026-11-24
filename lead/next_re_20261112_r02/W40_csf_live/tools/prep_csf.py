#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W40 · offline preparation of the two loose ra2md.csf variants.

Uses W30's ra2forge_patched_v10 (csf.py + mixlib.py):
  * locate the OFFICIAL ra2md.csf inside the real MIX archives via ts_crc_hash
    (id 0xBD835079, 332,973 B) and byte-compare with W30's extracted copy
  * strictly parse the official CSF (5,211 labels)
  * variant A: a MINIMAL but structurally VALID CSF with 1 label only
  * variant B: full official clone + one appended RA2F:W40TEST label (5,212)
  * write SHA-256 / label counts / roundtrip verdicts to out/csf_variants.json

Pure offline: no game launched, no writes outside W40_csf_live/.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import struct
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
RUN = ROOT / "lead" / "next_re_20261112_r02"
W40 = RUN / "W40_csf_live"
OUT = W40 / "out"
GAME = RUN / "W35_mapselmd_live" / "sandbox_game"
REAL = ROOT / "ra2youli"
V10 = RUN / "W30_csf_capability" / "ra2forge_patched_v10"
W30_EXTRACTED = RUN / "W30_csf_capability" / "sandbox" / "extracted" / "ra2md.csf"

sys.path.insert(0, str(V10))
from ra2forge import csf as C  # noqa: E402
from ra2forge import mixlib as M  # noqa: E402

LABEL_A = "RA2F:TEST0001"
TEXT_A = "W40A_MINIMAL_CSF_SINGLE_LABEL"
LABEL_B = "RA2F:W40TEST"
TEXT_B = "W40_CSF_LIVE_OK_20261113"

MIX_CANDIDATES = [
    ROOT / "ra2bench" / "ra2md.mix",          # named by the W40 card
    ROOT / "ra2bench" / "langmd.mix",         # W30's documented source
    REAL / "langmd.mix",                      # real install (read-only)
    GAME / "langmd.mix",                      # sandbox copy (read-only)
]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def label_snapshot(c: C.CsfFile):
    return [(l.name, [(v.kind, v.text, v.extra) for v in l.values]) for l in c.labels]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    r: dict = {"tool": "W30_csf_capability/ra2forge_patched_v10", "mix_probe": [],
               "checks": {}}

    # ---- 1. locate the official CSF inside MIX archives -------------------
    target_id = M.ts_crc_hash("ra2md.csf")
    r["ts_crc_hash_ra2md_csf"] = "0x%08X" % target_id
    r["crc_hash_ra2md_csf_plain"] = "0x%08X" % M.crc_hash("ra2md.csf")
    extracted_official: bytes | None = None
    for p in MIX_CANDIDATES:
        rec = {"path": str(p), "exists": p.is_file()}
        if p.is_file():
            rec["size"] = p.stat().st_size
            try:
                with M.MixFile(p) as mf:
                    rec["num_entries"] = len(mf.entries)
                    hit = [e for e in mf.entries if e.id == target_id]
                    rec["id_0xBD835079_present"] = bool(hit)
                    if hit:
                        rec["entry"] = {"id": "0x%08X" % hit[0].id,
                                        "offset": hit[0].offset,
                                        "size": hit[0].size}
                        data = mf.get("ra2md.csf")
                        rec["get_bytes"] = len(data) if data is not None else 0
                        rec["get_sha256"] = sha256_bytes(data) if data else None
                        if data and data[:4] == C.CSF_MAGIC:
                            extracted_official = data
                            rec["is_csf"] = True
            except Exception as e:
                rec["error"] = repr(e)
        r["mix_probe"].append(rec)

    # ---- 2. W30's already-extracted copy ---------------------------------
    w30 = W30_EXTRACTED.read_bytes() if W30_EXTRACTED.is_file() else None
    r["w30_extracted"] = {
        "path": str(W30_EXTRACTED), "exists": w30 is not None,
        "size": len(w30) if w30 else None,
        "sha256": sha256_bytes(w30) if w30 else None,
    }
    if extracted_official is not None and w30 is not None:
        r["checks"]["mix_extracted_equals_w30_copy"] = (extracted_official == w30)
    official = extracted_official if extracted_official is not None else w30
    if official is None:
        raise RuntimeError("no official ra2md.csf found in MIX or W30 copy")
    r["official_source"] = ("MIX" if extracted_official is not None else "W30_extracted_copy")
    (OUT / "official_ra2md.csf").write_bytes(official)

    # ---- 3. strictly parse the official file ------------------------------
    oc = C.parse_csf(official, strict=True)
    r["official"] = {
        "size": len(official), "sha256": sha256_bytes(official),
        "magic": official[:4].decode("latin-1"),
        "version": oc.version, "num_labels": oc.num_labels,
        "num_strings": oc.num_strings, "language": oc.language,
        "unused": oc.unused, "warnings": oc.warnings,
        "to_bytes_identical": oc.to_bytes() == official,
        "sample_DESC_ALL1": oc.get("DESC:ALL1"),
        "sample_DESC_SOV1": oc.get("DESC:SOV1"),
    }
    r["checks"]["official_5211_labels"] = (oc.num_labels == 5211)
    r["checks"]["official_5211_strings"] = (oc.num_strings == 5211)
    r["checks"]["official_byte_roundtrip"] = (oc.to_bytes() == official)
    r["checks"]["official_language_9"] = (oc.language == 9)

    # ---- 4. variant A: MINIMAL valid CSF, 1 label ------------------------
    pA = OUT / "ra2md.csf.minimal"
    mc = C.create_csf({LABEL_A: TEXT_A}, language=9)
    C.write_csf(pA, mc)
    backA = C.read_csf(pA, strict=True)
    r["variant_A"] = {
        "path": str(pA), "label": LABEL_A, "text": TEXT_A,
        "size": pA.stat().st_size, "sha256": sha256_file(pA),
        "magic": pA.read_bytes()[:4].decode("latin-1"),
        "num_labels": backA.num_labels, "num_strings": backA.num_strings,
        "language": backA.language, "version": backA.version,
        "labels": [l.name for l in backA.labels],
        "readback_text_matches": backA.get(LABEL_A) == TEXT_A,
        "valid_csf_magic": pA.read_bytes()[:4] == C.CSF_MAGIC,
    }
    r["checks"]["variant_A_is_valid_csf_1_label"] = (
        r["variant_A"]["valid_csf_magic"] and backA.num_labels == 1
        and backA.get(LABEL_A) == TEXT_A)

    # ---- 5. variant B: full clone + 1 appended label ---------------------
    pB = OUT / "ra2md.csf.full"
    shutil.copyfile(OUT / "official_ra2md.csf", pB)
    res = C.append_or_set_label(pB, LABEL_B, TEXT_B, verify=True)
    bc = C.read_csf(pB, strict=True)
    orig_snap = label_snapshot(oc)
    new_snap = label_snapshot(bc)
    r["variant_B"] = {
        "path": str(pB), "label": LABEL_B, "text": TEXT_B,
        "append_result": res,
        "size": pB.stat().st_size, "sha256": sha256_file(pB),
        "magic": pB.read_bytes()[:4].decode("latin-1"),
        "num_labels": bc.num_labels, "num_strings": bc.num_strings,
        "language": bc.language, "version": bc.version,
        "readback_text_matches": bc.get(LABEL_B) == TEXT_B,
        "official_labels_preserved": new_snap[:len(orig_snap)] == orig_snap,
        "new_label_is_last": bool(bc.labels) and bc.labels[-1].name == LABEL_B,
        "header_num_labels": struct.unpack_from("<I", pB.read_bytes(), 8)[0],
        "header_num_strings": struct.unpack_from("<I", pB.read_bytes(), 12)[0],
    }
    r["checks"]["variant_B_5212_labels"] = (bc.num_labels == 5212)
    r["checks"]["variant_B_5212_strings"] = (bc.num_strings == 5212)
    r["checks"]["variant_B_official_preserved"] = r["variant_B"]["official_labels_preserved"]
    r["checks"]["variant_B_readback"] = r["variant_B"]["readback_text_matches"]
    r["checks"]["variant_B_header_counts"] = (
        r["variant_B"]["header_num_labels"] == 5212
        and r["variant_B"]["header_num_strings"] == 5212)

    # ---- 6. sandbox/real-dir baseline facts (read-only) -------------------
    r["sandbox"] = {
        "path": str(GAME),
        "loose_ra2md_csf_present": (GAME / "ra2md.csf").is_file(),
        "MAPSELMD.INI_present": (GAME / "MAPSELMD.INI").is_file(),
        "MAPSELMD.INI_sha256": (sha256_file(GAME / "MAPSELMD.INI")
                                if (GAME / "MAPSELMD.INI").is_file() else None),
        "MAPSELMD.INI_size": ((GAME / "MAPSELMD.INI").stat().st_size
                              if (GAME / "MAPSELMD.INI").is_file() else None),
        "BATTLEMD98.INI_sha256": sha256_file(GAME / "BATTLEMD98.INI"),
        "BATTLEMD98.INI_bytes": (GAME / "BATTLEMD98.INI").read_bytes().decode("latin-1"),
    }
    # asbuilt copy for byte-exact restore in the live driver's finally block
    (OUT / "BATTLEMD98.INI.asbuilt").write_bytes((GAME / "BATTLEMD98.INI").read_bytes())
    r["real_dir_key_hashes"] = {
        n: sha256_file(REAL / n) for n in
        ("RA2MD.INI", "gamemd.exe", "ddraw.dll", "ra2forge_install.json")
    }
    r["all_pass"] = all(bool(v) for k, v in r["checks"].items()
                        if k != "mix_extracted_equals_w30_copy")
    (OUT / "csf_variants.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
