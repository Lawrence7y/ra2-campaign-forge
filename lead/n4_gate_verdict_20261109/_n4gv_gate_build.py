# -*- coding: utf-8 -*-
# N4 gate reviewer: INDEPENDENT re-run of the domain gate (safe variant, v2).
# Reads historical payload .mjs READ ONLY; extracts `lowered`; locates the
# `const GATE_CODE = [ ... ].join("\n")` array; parses each JS array element:
#   - plain double-quoted string literal  -> json.loads
#   - concatenation  "PRE_X='" + varSha + "'"  -> substitute live hashlib value
# No eval, no exec of external strings. Writes reconstructed Python to
# _n4gv_gate_verbatim.py, to be run via explicit `python -I -X utf8 <abs>`.
import json, hashlib
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
PAYLOAD = ROOT / ".zcode/workflow-runs/dwfrun-af6f3c87-7d72-4587-8e0d-07c4b878337c.mjs"
WD = ROOT / "lead/n4_gate_verdict_20261109"
OUT_PY = WD / "_n4gv_gate_verbatim.py"
OUT_META = WD / "_n4gv_gate_meta.json"

payload_text = PAYLOAD.read_text(encoding="utf-8")

# --- Step 1: parse exactly ONE JSON object after `export const payload = ` ---
prefix = "export const payload = "
p0 = payload_text.find(prefix)
assert p0 >= 0, "payload prefix not found"
payload, _ = json.JSONDecoder().raw_decode(payload_text[p0 + len(prefix):])
lowered = payload["lowered"]

# --- Step 2: locate GATE_CODE array ---
anchor = "const GATE_CODE = ["
start = lowered.find(anchor)
end = lowered.find('].join("\\n");', start)
assert start >= 0 and end >= 0
arr_body = lowered[start + len(anchor):end]

# --- Step 3: line-based element parser (each element is on its own line) ---
# Strip indentation & trailing comma; handle plain literals and the 6
# concatenation expressions `"PRE_X='" + varSha + "'"`.
live = {
    "motherSha": "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py",
    "candSha":   "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py",
    "v2Sha":     "lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md",
    "matSha":    "lead/b2b_design_20261106/STATE_MATRIX.json",
    "headSha":   "lead/PENDING_DECISIONS.md",
    "goalSha":   "lead/GOAL_THREE_TARGETS_20261018.md",
}
live_vals = {k: hashlib.sha256((ROOT / v).read_bytes()).hexdigest() for k, v in live.items()}

concat_map = {
    'motherSha': 'PRE_M', 'candSha': 'PRE_C', 'v2Sha': 'PRE_V',
    'matSha': 'PRE_MAT', 'headSha': 'PRE_H', 'goalSha': 'PRE_G',
}

gate_lines, substitutions = [], []
for raw in arr_body.split("\n"):
    s = raw.strip()
    if not s:
        continue
    assert s.endswith(","), f"unexpected element (no trailing comma): {s!r}"
    s = s[:-1].rstrip()
    if s.startswith('"PRE_') and " + " in s:
        # e.g.  "PRE_M='" + motherSha + "'"
        parts = [p.strip() for p in s.split(" + ")]
        assert len(parts) == 3, f"unexpected concat: {s!r}"
        first = json.loads(parts[0])          # "PRE_M='"
        var = parts[1]
        last = json.loads(parts[2])            # "'"
        assert var in concat_map and last == "'", f"unknown concat var {var!r}"
        new_ln = first + live_vals[var] + last
        substitutions.append({"orig": s, "rebuilt": new_ln, "value": live_vals[var]})
        gate_lines.append(new_ln)
    else:
        # plain JS string literal -> decode with json.loads (string only)
        gate_lines.append(json.loads(s))

assert len(substitutions) == 6, f"expected 6 substitutions, got {len(substitutions)}"
gate_py = "\n".join(gate_lines) + "\n"
assert " + " not in gate_py, "unreplaced JS concatenation remains"

# --- Step 4: write reconstructed gate python ---
OUT_PY.write_text(gate_py, encoding="utf-8", newline="")

# --- Step 5: independently compute candidate set ---
wd = ROOT / "lead/n4_yi_final_20261108"
cands = sorted([p for p in wd.glob("*.md") if p.name.startswith("CANDIDATE_RESIGN")]) if wd.is_dir() else []
cand_info = [{"name": p.name, "bytes": p.stat().st_size,
              "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in cands]
all_md = [{"name": p.name, "bytes": p.stat().st_size} for p in sorted(wd.glob("*.md"))]

meta = {
    "payload_file": str(PAYLOAD.relative_to(ROOT)), "payload_line": 9,
    "lowered_len": len(lowered), "gate_array_items": len(gate_lines),
    "gate_py_sha256": hashlib.sha256(gate_py.encode("utf-8")).hexdigest(),
    "gate_py_bytes": len(gate_py.encode("utf-8")),
    "substitutions": substitutions,
    "candidate_set": cand_info, "candidate_count": len(cand_info),
    "all_md_in_wd": all_md, "gate_lines": gate_lines,
}
OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "wrote_py": str(OUT_PY), "wrote_meta": str(OUT_META),
    "gate_array_items": len(gate_lines), "substitutions": len(substitutions),
    "candidate_count": len(cand_info), "candidate_set": cand_info,
    "all_md_in_wd": all_md,
}, ensure_ascii=False, indent=2))
