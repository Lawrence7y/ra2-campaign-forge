# -*- coding: utf-8 -*-
"""_oev_5.py -- final independent checks: C(302,5) two ways, reviewed-MD hash,
earliest task-book mention of the 5 whitelist tokens, and binding-line set.
Writes _oev_5_out.json only."""
from __future__ import annotations
import hashlib, json, math, sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "ordering_evidence_20261109"
TZ = timezone(timedelta(hours=8))
def loc(ms): return datetime.fromtimestamp(ms / 1000, TZ).isoformat()
OUT = {}
# C(302,5) three independent ways
n, k = 302, 5
c1 = math.comb(n, k)
c2 = math.factorial(n) // (math.factorial(k) * math.factorial(n - k))
c3 = 1
for i in range(k):
    c3 = c3 * (n - i) // (i + 1)
OUT["C_302_5"] = {"math_comb": c1, "factorial": c2, "iterative": c3,
                  "all_equal": c1 == c2 == c3,
                  "p_3way": 1.0 / c1**2, "p_pair": 1.0 / c1,
                  "C_10_5": math.comb(10, 5)}
# reviewed deliverable hash for the binding line
md = (WDIR / "_oe_ORDERING_EVIDENCE.md").read_bytes()
OUT["reviewed_md"] = {"sha256": hashlib.sha256(md).hexdigest(), "bytes": len(md)}
# all 8 orchestrator-baseline files (recompute) as binding-line sources
BASE = {
 "lead/seal_chronology_20261109/_sc_SEAL_CHRONOLOGY.md": ("5af2b304a71ec4c13bea14d1034ef0de12d306a62f769a41bec3891c6392cc5f", 45423),
 "lead/seal_chronology_20261109/_sc_probe_out.json": ("09548c9ad258270fc7dbf80150437e868e45c6b8f5220214cbfd8aa20b1ec6d7", 9590),
 "lead/seal_chronology_20261109/_sc_ctime.py": ("e49151caef129b8925fcb02bcd23c36060cd411102e05350bad7839b8d769657", 1126),
 "lead/oracle_spec_20261109/_os_ORACLE_SPEC.md": ("5417fb06fc5ad7b6e2c520b9c83e3bb08c7a4a1bf65c339e1d0048bf695a2156", 52542),
 "lead/cert_realcheck_20261109/_cr_seal.json": ("63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23", 4395),
 "lead/cert_realcheck_20261109/_cr_build_seal.py": ("2e539d392b0aca54cb8cd2c83bd20e1d87ba9ce5cbc8f15ea5ea279ef0b86574", 5376),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
lines = []
for rel, (h0, n0) in BASE.items():
    b = (ROOT / rel).read_bytes()
    h = hashlib.sha256(b).hexdigest()
    lines.append({"rel": rel, "sha256": h, "bytes": len(b),
                  "match_baseline": (h == h0 and len(b) == n0),
                  "binding_line": "被核对象 SHA256 = %s，字节数 = %d" % (h, len(b))})
OUT["baseline_binding_lines"] = lines
# earliest DB row containing any of the 5 whitelist tokens (task-book pre-registration)
DB = "C:/Users/Administrator/.zcode/cli/db/db.sqlite"
con = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=10)
toks = ["需谁批准", "实跑输出", "改前改后", "脚本存在性", "可重建"]
earliest = {}
for t in toks:
    r = con.execute("select rowid,time_created from part where data like ? order by rowid limit 1",
                    ("%" + t + "%",)).fetchone()
    earliest[t] = ({"rowid": r[0], "local": loc(r[1])} if r else None)
OUT["earliest_whitelist_token_mentions"] = earliest
con.close()
OUT["V1_output_mtimes_local"] = [
    "2026-11-09 12:51:07 (_gp_regression_v1_union_out.json)",
    "2026-11-09 12:52:54 (_gp_regression.py)",
    "2026-11-09 13:53:57 (_gp_regression_out.json)",
    "2026-11-09 14:32:26 (_r9s_regress_out.json)"]
with (WDIR / "_oev_5_out.json").open("w", encoding="utf-8") as f:
    json.dump(OUT, f, ensure_ascii=False, indent=2)
print("=== _oev_5.py FINAL CHECKS ===")
print(json.dumps(OUT, ensure_ascii=False, indent=1))
print("WROTE _oev_5_out.json")
