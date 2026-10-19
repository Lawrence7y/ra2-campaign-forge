#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H1 bench-map fingerprint + cell-uniqueness verifier (M-track, H1-FANOUT M5/M1).

Fingerprint scheme H1FP1:
    H1FP1|<tier>|<load_hash12>
  - tier      : U0050 / U0200 / U0800 (4-digit zero-padded target load)
  - load_hash12: first 12 hex chars of sha256 over a canonical form of the
                 pre-placed object rows ([Units]/[Infantry]/[Structures]/[Aircraft]).
                 Row ids are stripped and bodies are sorted so renumbering
                 does not change the hash. The fingerprint fields themselves
                 are NOT part of the hashed payload (no circularity).

Embedded in the map at write time:
  [Basic] Name=... fp:<load_hash12>          (short tag, human/UI visible)
  [Basic] H1Tier=U0050
  [Basic] H1Fingerprint=H1FP1|U0050|<load_hash12>

Usage:
  python tools/h1_map_fingerprint.py verify            # default: pristine/H1
  python tools/h1_map_fingerprint.py verify PATH...
  python tools/h1_map_fingerprint.py compute PATH...
  python tools/h1_map_fingerprint.py verify --expect-dir DIR --json OUT.json

Exit code 0 = all checks PASS, 1 = any FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _ra2_paths import resolve_root  # noqa: E402

ROOT = resolve_root(__file__)
DEFAULT_MAP_DIR = ROOT / "out" / "loadbench" / "pristine" / "H1"
DEFAULT_REPORT = ROOT / "out" / "re_work" / "h1_map_fix" / "fingerprint_report.json"

SCHEME = "H1FP1"
HASH_LEN = 12
OBJECT_SECTIONS = ("Units", "Infantry", "Structures", "Aircraft")
TIER_RE = re.compile(r"U(\d{4})")
FP_RE = re.compile(r"^(?P<scheme>H1FP\d+)\|(?P<tier>U\d{4})\|(?P<hash>[0-9a-fA-F]{6,64})$")


# ---------------------------------------------------------------------------
# canonical load hash
# ---------------------------------------------------------------------------
def split_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    cur: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        if line.startswith("[") and line.endswith("]") and len(line) > 2:
            if cur is not None:
                sections[cur] = buf
            cur = line[1:-1].strip()
            buf = []
        else:
            if cur is not None:
                buf.append(line)
    if cur is not None:
        sections[cur] = buf
    return sections


def object_rows(sections: dict[str, list[str]]) -> list[str]:
    """Canonical object-row strings: 'Section|Body' with row-id stripped."""
    out: list[str] = []
    for sec in OBJECT_SECTIONS:
        for line in sections.get(sec, []):
            if "=" not in line or line.strip().startswith(";"):
                continue
            _id, body = line.split("=", 1)
            out.append(f"{sec}|{body.strip()}")
    return out


def load_hash(text: str) -> str:
    rows = sorted(object_rows(split_sections(text)))
    payload = "\n".join(rows).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:HASH_LEN]


def parse_basic(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    in_basic = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("["):
            in_basic = s.lower() == "[basic]"
            continue
        if in_basic and "=" in s and not s.startswith(";"):
            k, v = s.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def parse_objects(text: str) -> list[dict]:
    """Return [{section, id, owner, type, x, y}] for every pre-placed object."""
    sections = split_sections(text)
    objs: list[dict] = []
    for sec in OBJECT_SECTIONS:
        for line in sections.get(sec, []):
            if "=" not in line or line.strip().startswith(";"):
                continue
            key, body = line.split("=", 1)
            parts = [p.strip() for p in body.split(",")]
            if len(parts) < 5:
                continue
            objs.append({
                "section": sec,
                "id": key.strip(),
                "owner": parts[0],
                "type": parts[1],
                "x": parts[3],
                "y": parts[4],
            })
    return objs


# ---------------------------------------------------------------------------
# verification
# ---------------------------------------------------------------------------
def tier_from_text(text: str, path: Path | None = None) -> str | None:
    basic = parse_basic(text)
    if basic.get("H1Tier"):
        return basic["H1Tier"]
    if basic.get("H1Fingerprint"):
        m = FP_RE.match(basic["H1Fingerprint"])
        if m:
            return m.group("tier")
    if basic.get("Name"):
        m = TIER_RE.search(basic["Name"].replace(" ", ""))
        if m:
            return f"U{m.group(1)}"
    if path is not None:
        m = TIER_RE.search(path.name)
        if m:
            return f"U{m.group(1)}"
    return None


def verify_map(path: Path, expect_tier: str | None = None) -> dict:
    raw = path.read_bytes()
    text = raw.decode("gbk", errors="replace")
    basic = parse_basic(text)
    objs = parse_objects(text)

    recomputed = load_hash(text)
    declared = basic.get("H1Fingerprint", "")
    declared_short = ""
    name = basic.get("Name", "")

    fp_match = FP_RE.match(declared) if declared else None
    fp_ok = False
    fp_tier = None
    fp_hash = None
    if fp_match:
        fp_tier = fp_match.group("tier")
        fp_hash = fp_match.group("hash").lower()[:HASH_LEN]
        fp_ok = (fp_match.group("scheme") == SCHEME
                 and fp_hash == recomputed
                 and basic.get("H1Tier") == fp_tier)

    # short tag in Name (fp:xxxxxxxxxxxx)
    tag_m = re.search(r"fp:([0-9a-fA-F]{6,64})", name)
    if tag_m:
        declared_short = tag_m.group(1).lower()[:HASH_LEN]
    name_tag_ok = (declared_short == recomputed) if declared_short else False

    cells = Counter((o["x"], o["y"]) for o in objs)
    unique = len(cells)
    total = len(objs)
    max_stack = max(cells.values()) if cells else 0
    owners = Counter(o["owner"] for o in objs)

    tier = basic.get("H1Tier") or fp_tier or tier_from_text(text, path)
    tier_ok = True
    if expect_tier is not None:
        tier_ok = (tier == expect_tier)
    if path is not None:
        fm = TIER_RE.search(path.name)
        if fm:
            tier_ok = tier_ok and (tier == f"U{fm.group(1)}")

    checks = {
        "fingerprint_scheme_ok": bool(fp_match and fp_match.group("scheme") == SCHEME),
        "fingerprint_hash_ok": bool(fp_match and fp_hash == recomputed),
        "fingerprint_tier_field_ok": bool(fp_match and basic.get("H1Tier") == fp_tier),
        "name_fp_tag_ok": name_tag_ok,
        "cell_unique_eq_total": unique == total,
        "max_cell_stack_1": max_stack <= 1,
        "tier_ok": tier_ok,
        "has_basic_fingerprint": bool(declared),
    }
    # name tag is informative when absent; if present it must match
    if not declared_short:
        checks.pop("name_fp_tag_ok")

    # hard requirements: fingerprint present + hash matches + cells disjoint
    hard = ["fingerprint_scheme_ok", "fingerprint_hash_ok",
            "fingerprint_tier_field_ok", "cell_unique_eq_total",
            "max_cell_stack_1", "tier_ok", "has_basic_fingerprint"]
    if declared_short:
        hard.append("name_fp_tag_ok")
    ok = all(checks.get(k, False) for k in hard)

    return {
        "path": str(path),
        "file_bytes": len(raw),
        "file_sha256": hashlib.sha256(raw).hexdigest(),
        "tier": tier,
        "name": name,
        "declared_fingerprint": declared,
        "recomputed_hash": recomputed,
        "declared_short": declared_short,
        "total_objects": total,
        "unique_cells_xy": unique,
        "max_cell_stack": max_stack,
        "owner_counts": dict(owners),
        "checks": checks,
        "ok": ok,
    }


def compute_map(path: Path) -> dict:
    text = path.read_bytes().decode("gbk", errors="replace")
    basic = parse_basic(text)
    h = load_hash(text)
    tier = tier_from_text(text, path) or "U????"
    return {
        "path": str(path),
        "tier": tier,
        "load_hash": h,
        "fingerprint": f"{SCHEME}|{tier}|{h}",
        "declared": basic.get("H1Fingerprint", ""),
        "name": basic.get("Name", ""),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _collect_paths(args: argparse.Namespace) -> list[Path]:
    if args.paths:
        out = []
        for p in args.paths:
            pp = Path(p)
            if pp.is_dir():
                out.extend(sorted(pp.glob("*.yrm")) + sorted(pp.glob("*.map")))
            else:
                out.append(pp)
        return out
    d = Path(args.expect_dir) if args.expect_dir else DEFAULT_MAP_DIR
    return sorted(d.glob("*_H1.yrm")) + sorted(d.glob("*_H1.map"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="H1 map fingerprint / cell-uniqueness verifier")
    ap.add_argument("cmd", choices=["verify", "compute"], nargs="?", default="verify")
    ap.add_argument("paths", nargs="*", help="map files or dirs (default: pristine/H1)")
    ap.add_argument("--expect-tier", default=None, help="require this tier (e.g. U0050)")
    ap.add_argument("--expect-dir", default=None, help="default dir when no paths given")
    ap.add_argument("--json", dest="json_out", default=None,
                    help="write report JSON (default: out/re_work/h1_map_fix/fingerprint_report.json)")
    args = ap.parse_args(argv)

    paths = _collect_paths(args)
    if not paths:
        print("no maps found", file=sys.stderr)
        return 1

    if args.cmd == "compute":
        rows = [compute_map(p) for p in paths]
        for r in rows:
            print(f"{Path(r['path']).name}: tier={r['tier']} hash={r['load_hash']} "
                  f"fp={r['fingerprint']} declared={r['declared'] or '(none)'}")
        return 0

    reports = []
    for p in paths:
        expect = args.expect_tier
        if expect is None:
            m = TIER_RE.search(p.name)
            if m:
                expect = f"U{m.group(1)}"
        reports.append(verify_map(p, expect_tier=expect))
        r = reports[-1]
        status = "PASS" if r["ok"] else "FAIL"
        print(f"[{status}] {p.name}  tier={r['tier']}  objects={r['total_objects']}  "
              f"unique_cells={r['unique_cells_xy']}  max_stack={r['max_cell_stack']}  "
              f"hash={r['recomputed_hash']}  fp={r['declared_fingerprint'] or '(none)'}")
        for k, v in r["checks"].items():
            if not v:
                print(f"       FAIL check: {k}")

    out_path = Path(args.json_out) if args.json_out else DEFAULT_REPORT
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "scheme": SCHEME,
        "hash_len": HASH_LEN,
        "canonical_payload": "sorted 'Section|Body' lines of [Units]/[Infantry]/[Structures]/[Aircraft]",
        "all_ok": all(r["ok"] for r in reports),
        "maps": reports,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out_path}")
    return 0 if payload["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
