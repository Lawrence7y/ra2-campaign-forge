# -*- coding: utf-8 -*-
# N4 gate reviewer: independent fingerprint computation (read-only over all inputs).
# Write domain only: lead/n4_gate_verdict_20261109/, prefix _n4gv_.
import hashlib, json, os, sys
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")

BASELINE = {
 "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md": ("1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b", 23129, 174),
 "lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md": ("c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801", 28897, 211),
 "lead/n4_yi_final_20261108/B_EXECUTION_SPEC_V2_YI.md": ("27f31bf560e9a71c5e9603d81a860233e7fc7b19e504eed4a15ea24a2077b067", 35486, 238),
 "lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md": ("ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e", 11948, 85),
 "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py": ("517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508, 7292),
 "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py": ("ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759, 7534),
 "lead/b2b_design_20261106/STATE_MATRIX.json": ("1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558, 17),
 "lead/direction_ruling_20261108/RULING_DIRECTION.md": ("0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653", 16514, 97),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419, 382),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518, 9758),
}

out = {}
all_ok = True
for rel, (sha, nbytes, nlines) in BASELINE.items():
    p = ROOT / rel
    rec = {"path": rel, "exists": p.exists()}
    if p.exists():
        b = p.read_bytes()
        got_sha = hashlib.sha256(b).hexdigest()
        got_bytes = len(b)
        # several line-count conventions
        sl = len(b.splitlines())
        nl = b.count(b"\n")
        txt = b.decode("utf-8", errors="replace")
        sl_txt = len(txt.splitlines())
        rec.update({
            "sha256": got_sha, "bytes": got_bytes,
            "splitlines_bytes": sl, "newline_count": nl, "newline_plus1": nl + 1,
            "splitlines_text": sl_txt, "ends_with_newline": b.endswith(b"\n"),
        })
        rec["sha_match"] = got_sha == sha
        rec["bytes_match"] = got_bytes == nbytes
        rec["lines_match_splitlines"] = sl == nlines
        rec["lines_match_nlplus1"] = (nl + 1) == nlines
        rec["baseline"] = {"sha256": sha, "bytes": nbytes, "lines": nlines}
        if not (rec["sha_match"] and rec["bytes_match"]):
            all_ok = False
    else:
        all_ok = False
    out[rel] = rec

print(json.dumps({"all_sha_and_bytes_match": all_ok, "files": out}, ensure_ascii=False, indent=2))
