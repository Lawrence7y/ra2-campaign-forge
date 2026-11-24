# -*- coding: utf-8 -*-
"""_svv_review.py — seal-v2 复核员独立探针（只读；写域内仅建/删一次性探针文件）
运行: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/seal_v2_feasibility_20261109/_svv_review.py
"""
import ast
import hashlib
import json
import os
import re
import sqlite3
import time
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "seal_v2_feasibility_20261109"


def H(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


FILES12 = [
    ("lead/PENDING_DECISIONS.md", "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md", "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    ("lead/ordering_evidence_20261109/ORDERING_EVIDENCE.md", "04217b1321f7b9fc576fae39be43c5718e0ced65ee4212b5cfc11807dbb99da0", 47952),
    ("lead/cert_realcheck_20261109/_cr_seal.json", "63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23", 4395),
    ("lead/cert_realcheck_20261109/_cr_build_seal.py", "2e539d392b0aca54cb8cd2c83bd20e1d87ba9ce5cbc8f15ea5ea279ef0b86574", 5376),
    ("lead/cert_realcheck_20261109/_cr_real_verify.py", "3d8ab1092ebf85efe3cc84e22c1eeb98b867a16f44d07cf877f1e2b4eb5c30fa", 21178),
    ("lead/falsifiable_no_relax_20261109/_fnr_check.py", "94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2", 28811),
    ("lead/seal_chronology_20261109/SEAL_CHRONOLOGY.md", "6b5eda3e58c439c576d3e6e6f8c91220e9b36201280f7672eb4c9ca9140b55ea", 55693),
    ("lead/oracle_spec_20261109/ORACLE_SPEC.md", "7f9316ddfa33f405281bd2d33b0e22be7f7cc60c7d00dd070901b1392993a4a0", 49318),
    ("lead/oracle_spec_20261109/_os_ORACLE_SPEC.md", "5417fb06fc5ad7b6e2c520b9c83e3bb08c7a4a1bf65c339e1d0048bf695a2156", 52542),
    ("lead/cert_realcheck_20261109/CERT_REAL_CHECK.md", "fa3a45b7fd96ea8c3130a02227f6b6748bf4f196a5f714a51d3850e6d98ef014", 53782),
    ("lead/falsifiable_no_relax_20261109/FALSIFIABLE_NO_RELAX.md", "c54694849bb2ad84126c86d692f53ca3ba7362e33ede3a4c45dffebf275de0da", 45824),
]

print("=== S1. 12 fingerprints (baseline 7 + supplement 5) ===")
all_ok = True
for rel, want, nb in FILES12:
    p = ROOT / rel
    got = H(p)
    n = p.stat().st_size
    ok = (got == want and n == nb)
    all_ok = all_ok and ok
    print(("MATCH " if ok else "DIFF  ") + rel)
    print("  被核对象 SHA256 = " + got + "，字节数 = " + str(n))
print("ALL_12_MATCH =", all_ok)

print()
print("=== S2. write-domain artifacts (_sv_*) ===")
for p in sorted(WD.glob("_sv_*")):
    if p.is_file():
        print("  被核对象 SHA256 = " + H(p) + "，字节数 = " + str(p.stat().st_size) + "  " + p.name)
bad_ext = [p.name for p in WD.glob("*") if p.suffix.lower() in
           {".asc", ".sig", ".p7s", ".key", ".tsr", ".tsq", ".pem", ".gpg"}]
print("  signing_artifacts_in_write_domain =", bad_ext)

print()
print("=== S3. ctime probe (independent rerun) ===")
for rel in [r"lead\cert_realcheck_20261109\_cr_seal.json",
            r"lead\cert_realcheck_20261109\_cr_build_seal.py"]:
    s = (ROOT / rel).stat()
    print("  %s: st_ctime=%.6f st_mtime=%.6f mtime-ctime=%.6f" %
          (rel, s.st_ctime, s.st_mtime, s.st_mtime - s.st_ctime))
seal_s = (ROOT / r"lead\cert_realcheck_20261109\_cr_seal.json").stat()
bld_s = (ROOT / r"lead\cert_realcheck_20261109\_cr_build_seal.py").stat()
print("  builder.mtime - seal.ctime = %.6f -> int %d" % (bld_s.st_mtime - seal_s.st_ctime, int(bld_s.st_mtime - seal_s.st_ctime)))
probe = WD / "_svv_ctime_probe.bin"
probe.write_bytes(b"A")
s1 = probe.stat()
time.sleep(1.2)
probe.write_bytes(b"BBBBBBBB")
s2 = probe.stat()
probe.unlink()
print("  overwrite probe: ctime_delta=%.3f mtime_delta=%.3f mtime>ctime=%s" %
      (s2.st_ctime - s1.st_ctime, s2.st_mtime - s1.st_mtime, s2.st_mtime > s2.st_ctime))
total = 0
hits = 0
best = 0.0
bestp = ""
for dirpath, dirnames, filenames in os.walk(ROOT / "lead"):
    for fn in filenames:
        total += 1
        try:
            st = os.stat(os.path.join(dirpath, fn))
            d = st.st_mtime - st.st_ctime
            if d > 328.7:
                hits += 1
                if d > best:
                    best, bestp = d, fn
        except OSError:
            pass
print("  lead/ scan: total=%d mtime-ctime>328.7s count=%d max_sample=%.1fs %s" %
      (total, hits, best, bestp))

print()
print("=== S4. schema content checks ===")
sch_path = WD / "_sv_seal_v2.schema.json"
raw = sch_path.read_text(encoding="utf-8")
lits = re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", raw)
pats = raw.count("^[0-9a-f]{64}$")
print("  64hex_literal_count =", len(lits), lits[:3])
print("  pattern_string_count =", pats)
sch = json.loads(raw)
print("  $schema =", sch.get("$schema"))
print("  top_keys =", sorted(sch.keys()))
prov = sch["properties"]["provenance"]["properties"]
print("  cognitive_independence_is_provable =", prov.get("cognitive_independence_is_provable"))
print("  fs_times_used_for_ordering =", prov.get("fs_times_used_for_ordering"))
print("  key_generated_by_this_run =", sch["properties"]["signers"]["items"]["properties"].get("key_generated_by_this_run"))
ta = sch["properties"]["time_anchors"]
print("  time_anchors.minItems =", ta.get("minItems"), " has_contains_clause =", "contains" in ta)
pra = sch["properties"]["predicate_run_anchor"]
print("  predicate_run_anchor.required =", pra.get("required"))
print("  IS_SEAL_INSTANCE =", (len(lits) > 0))

print()
print("=== S5. skeleton static analysis ===")
for name in ["_sv_build_skeleton.py", "_sv_verify_skeleton.py"]:
    t = (WD / name).read_text(encoding="utf-8")
    tree = ast.parse(t)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
    net_bad = sorted(imports & {"socket", "urllib", "urllib.request", "requests", "http",
                                "http.client", "ftplib"})
    kg, net_in_code = [], []
    for i, line in enumerate(t.splitlines(), 1):
        if re.search(r"quick-generate-key|--gen-key|full-generate-key|generate-key", line):
            kg.append((i, line.strip()[:80]))
        if re.search(r"\bsocket\b|urllib|requests\.|http\.client", line):
            net_in_code.append((i, line.strip()[:80]))
    print("  %s: ast_parse=OK net_imports=%s main_guard=%s network_flag_present=%s" %
          (name, net_bad, "__main__" in t, "--allow-network" in t))
    print("    keygen_strings =", kg)
    print("    net_code_hits =", net_in_code)

print()
print("=== S6. gpg homedir file-level check ===")
gp = Path.home() / ".gnupg"
pk = gp / "private-keys-v1.d"
print("  private-keys-v1.d exists =", pk.exists(),
      " key_files =", len(list(pk.glob("*.key"))) if pk.exists() else "n/a")
print("  gnupg files =", [str(p.relative_to(gp)) for p in gp.rglob("*") if p.is_file()])

print()
print("=== S7. CLI session DB (mode=ro over live WAL; point values drift) ===")
db = r"C:\Users\Administrator\.zcode\cli\db\db.sqlite"
try:
    con = sqlite3.connect("file:" + db.replace("\\", "/") + "?mode=ro", uri=True, timeout=20)
    cur = con.cursor()
    cols = [r[1] for r in cur.execute("PRAGMA table_info(part)").fetchall()]
    n = cur.execute("SELECT count(*) FROM part").fetchone()[0]
    mx = cur.execute("SELECT max(rowid) FROM part").fetchone()[0]
    rows = cur.execute(
        "SELECT rowid, time_created FROM part WHERE rowid>=635000 AND rowid<=636000 ORDER BY rowid"
    ).fetchall()
    numeric = rows and all(isinstance(r[1], (int, float)) for r in rows)
    less = (lambda a, b: b[1] < a[1]) if numeric else (lambda a, b: str(b[1]) < str(a[1]))
    reg = sum(1 for a, b in zip(rows, rows[1:]) if less(a, b))
    print("  part_cols =", cols)
    print("  count(*) =", n, " max(rowid) =", mx, " gap =", mx - n)
    print("  window 635000..636000 rows =", len(rows), " adjacent time_created regressions =", reg)
    print("  time_updated_in_cols =", "time_updated" in cols)
    con.close()
except Exception as e:
    print("  DB_CHECK_ERROR:", type(e).__name__, str(e)[:200])

print()
print("=== S8. evaluator report byte-size claim vs disk ===")
rep = WD / "_sv_FEASIBILITY.md"
st = rep.stat()
print("  _sv_FEASIBILITY.md on disk: bytes =", st.st_size, " claimed_in_reply = 62443",
      " delta =", st.st_size - 62443)
