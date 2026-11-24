# -*- coding: utf-8 -*-
# N4 gate reviewer: independent reference-surface scan (careful, explicit).
# Scans explicit file lists (not rglob over the huge out/ tree) for:
#   - full 64-hex hash of CANDIDATE_RESIGN_YES_V2.md
#   - short prefixes 1950d3f3 / 1950d3f31048 / 1950d3f31048b9a0
#   - filename CANDIDATE_RESIGN / CANDIDATE_RESIGN_YES_V2
# Classifies: full-hash, short-hash-only, sandbox, mjs-by-name.
# Also writes a per-line grep-like hit list for the 41 claimed reference files.
import json, hashlib, re
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
OUT = ROOT / "lead/n4_gate_verdict_20261109/_n4gv_refs_out.json"
FULL = "1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b"
SHORTS = ["1950d3f3", "1950d3f31048", "1950d3f31048b9a0"]
NAMES = ["CANDIDATE_RESIGN_YES_V2", "CANDIDATE_RESIGN"]

# explicit roots to walk (bounded). `out/` is deliberately NOT rglob'd here —
# previous attempt hung on the huge out/ tree; it is scanned separately below
# with shell `find -maxdepth` + grep, and results merged by the caller.
roots = [ROOT / "lead", ROOT / ".zcode/workflow-runs"]
skip_dirs = {".git", ".tmp", "node_modules", "__pycache__"}
max_bytes = 2_000_000

def iter_files():
    for r in roots:
        if not r.exists():
            continue
        for p in r.rglob("*"):
            if not p.is_file():
                continue
            if any(part in skip_dirs for part in p.parts):
                continue
            try:
                if p.stat().st_size > max_bytes:
                    continue
                b = p.read_bytes()
            except (OSError, PermissionError):
                continue
            yield p, b

full_hits, short_only, name_only, both = [], [], [], []
for p, b in iter_files():
    try:
        s = b.decode("utf-8")
    except UnicodeDecodeError:
        continue
    rel = str(p.relative_to(ROOT)).replace("\\", "/")
    has_full = FULL in s
    has_short = any(x in s for x in SHORTS)
    has_name = any(x in s for x in NAMES)
    if has_full:
        full_hits.append(rel)
    elif has_short:
        short_only.append(rel)
    if has_name and not has_full:
        name_only.append(rel)
    if has_full and has_name:
        both.append(rel)

full_hits.sort(); short_only.sort(); name_only.sort(); both.sort()
sandbox = [x for x in full_hits if "_dnv_sandbox" in x or "_dnw_sandbox" in x]
nonsandbox_full = [x for x in full_hits if x not in sandbox]
verdict_dir = [x for x in nonsandbox_full if x.startswith("lead/n4_gate_verdict_20261109/")]
nonsandbox_excl_verdict = [x for x in nonsandbox_full if not x.startswith("lead/n4_gate_verdict_20261109/")]
mjs_name = [x for x in name_only if x.endswith(".mjs")]
mjs_full = [x for x in full_hits if x.endswith(".mjs")]

# two ledgers: no ref?
ledgers = {}
for rel in ["lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md"]:
    s = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
    ledgers[rel] = {"full_hash": FULL in s, "short": any(x in s for x in SHORTS),
                    "name": any(x in s for x in NAMES)}

# per-line hit detail for the author's 41 (39 nonsandbox + 2 sandbox copies + short 2)
detail = {}
for rel in sorted(set(full_hits + short_only)):
    p = ROOT / rel
    lines = p.read_text(encoding="utf-8", errors="replace").split("\n")
    hits = []
    for i, L in enumerate(lines, 1):
        if FULL in L or any(x in L for x in SHORTS):
            hits.append({"line": i, "text": L.strip()[:240]})
    detail[rel] = hits

res = {
    "full_hash_count": len(full_hits),
    "full_hash_nonsandbox_count": len(nonsandbox_full),
    "full_hash_nonsandbox_excl_verdict_count": len(nonsandbox_excl_verdict),
    "full_hash_nonsandbox_excl_verdict_files": nonsandbox_excl_verdict,
    "sandbox_copies_with_full_hash": sandbox,
    "verdict_dir_full_hash_files": verdict_dir,
    "short_hash_only_count": len(short_only),
    "short_hash_only_files": short_only,
    "mjs_with_full_hash_count": len(mjs_full), "mjs_with_full_hash": mjs_full,
    "mjs_with_name_only_count": len(mjs_name), "mjs_with_name_only": mjs_name,
    "name_only_non_mjs_count": len([x for x in name_only if not x.endswith(".mjs")]),
    "ledgers": ledgers,
    "detail_line_hits": detail,
}
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k != "detail_line_hits"}, ensure_ascii=False, indent=2))
