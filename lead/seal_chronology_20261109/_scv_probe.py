# -*- coding: utf-8 -*-
# _scv_probe.py : INDEPENDENT re-implementation. Read-only over all forbidden domains.
# Writes ONLY into lead/seal_chronology_20261109/ (prefix _scv_).
import os, sys, json, hashlib, time, datetime, re
ROOT = r"D:\Project\ra2-campaign-forge"

# (rel path, orchestrator sha256, orchestrator bytes) -- copied verbatim from the ask's 【编排方指纹】
ORCH = {
 "lead/oracle_spec_20261109/_os_ORACLE_SPEC.md": ("5417fb06fc5ad7b6e2c520b9c83e3bb08c7a4a1bf65c339e1d0048bf695a2156", 52542),
 "lead/oracle_spec_20261109/_os_audit_out.json": ("c791716862caaa55974adfa1b206c4a4d098d092b11bdf60c99e5cb517ef8b7c", 80300),
 "lead/cert_realcheck_20261109/_cr_seal.json": ("63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23", 4395),
 "lead/cert_realcheck_20261109/_cr_real_verify.py": ("3d8ab1092ebf85efe3cc84e22c1eeb98b867a16f44d07cf877f1e2b4eb5c30fa", 21178),
 "lead/cert_realcheck_20261109/CERT_REAL_CHECK.md": ("fa3a45b7fd96ea8c3130a02227f6b6748bf4f196a5f714a51d3850e6d98ef014", 53782),
 "lead/falsifiable_no_relax_20261109/_fnr_check.py": ("94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2", 28811),
 "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
 "lead/gate_r9sem_20261109/_r9s_regress_out.json": ("5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25", 75673),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
# extra mtime-only rows from the writer's own table (§1(a))
EXTRA = [
 "lead/cert_realcheck_20261109/_cr_build_seal.py",
 "lead/gate_pipeline_20261109/_gp_regression.py",
 "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json",
 "lead/gate_r9sem_20261109/_r9s_predicates.py",
 "lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md",
]

def digest(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest(), os.path.getsize(p)

def loc(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

print("PYTHON", sys.version.split()[0], "TZ", time.tzname, "timezone", time.timezone)
print("NOW", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print()
print("=== A. 10 orchestrator fingerprints: independent sha256 + size ===")
allok = True
for rel, (want_sha, want_n) in ORCH.items():
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    got_sha, got_n = digest(p)
    ok = (got_sha == want_sha and got_n == want_n)
    allok &= ok
    print("%-64s sha=%s bytes=%s got_n=%d want_n=%d" %
          (rel, "MATCH" if got_sha == want_sha else "MISMATCH:" + got_sha,
           "MATCH" if got_n == want_n else "MISMATCH", got_n, want_n))
print("ALL_TEN_MATCH_ORCH =", allok)

print()
print("=== B. independent mtime / ctime / atime of 15 files (epoch + local + UTC) ===")
stat = {}
for rel in list(ORCH.keys()) + EXTRA:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    st = os.stat(p)
    stat[rel] = dict(mtime=st.st_mtime, ctime=st.st_ctime, atime=st.st_atime,
                     size=st.st_size, sha256=digest(p)[0])
    r = stat[rel]
    print("%-64s mtime=%s (epoch=%d) ctime=%s atime=%s bytes=%d" %
          (rel, loc(r["mtime"]), int(r["mtime"]), loc(r["ctime"]), loc(r["atime"]), r["size"]))
print()
SEAL = "lead/cert_realcheck_20261109/_cr_seal.json"
V1   = "lead/gate_pipeline_20261109/_gp_regression_out.json"
d = stat[SEAL]["mtime"] - stat[V1]["mtime"]
print("=== C. deltas: seal.mtime minus each X.mtime (seconds) ===")
for rel in EXTRA + [V1, "lead/cert_realcheck_20261109/_cr_real_verify.py"]:
    dd = stat[SEAL]["mtime"] - stat[rel]["mtime"]
    print("seal - %-64s = %+8d s" % (rel, dd))
print("SEAL_MINUS_V1_INT =", int(d), " h:m:s =", "%dh%dm%ds" % (int(d)//3600, (int(d)%3600)//60, int(d)%60))
print("SEAL_CTIME_MINUS_V1_CTIME =", int(stat[SEAL]["ctime"] - stat[V1]["ctime"]), "s")
print("SEAL_MTIME_MINUS_SEAL_CTIME =", int(stat[SEAL]["mtime"] - stat[SEAL]["ctime"]), "s")
print("SEAL_BUILDER_MTIME_MINUS_SEAL_CTIME =",
      int(stat["lead/cert_realcheck_20261109/_cr_build_seal.py"]["mtime"] - stat[SEAL]["ctime"]), "s")

print()
print("=== D. binding-line regex on the reply's evidence field (ask material) ===")
line = "被核对象 SHA256 = 63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23，字节数 = 4395"
m = re.search(r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)", line)
print("BINDING_LINE_MATCH =", bool(m), " is64hex =", bool(m and len(m.group(1)) == 64), " bytes =", m.group(2) if m else None)
print("BINDING_SHA_EQUALS_SEAL_ON_DISK =", bool(m and m.group(1) == stat[SEAL]["sha256"]))

print()
print("=== E. document self-declared size / sha / binding line ===")
doc = os.path.join(ROOT, "lead", "seal_chronology_20261109", "_sc_SEAL_CHRONOLOGY.md")
txt = open(doc, "r", encoding="utf-8").read()
doc_sha, doc_n = digest(doc)
print("DOC bytes =", doc_n, " sha256 =", doc_sha)
print("DOC declared 45423 B ? ", doc_n == 45423)
print("DOC declared sha 5af2b304...f5 ?", doc_sha == "5af2b304a71ec4c13bea14d1034ef0de12d306a62f769a41bec3891c6392cc5f")
mm = re.findall(r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)", txt)
print("DOC binding lines =", mm, " count =", len(mm))

with open(os.path.join(ROOT, "lead", "seal_chronology_20261109", "_scv_probe_out.json"), "w", encoding="utf-8") as f:
    json.dump(dict(orch_ok=allok, stat=stat, delta_seal_v1=d,
                   doc_bytes=doc_n, doc_sha=doc_sha, doc_binding=mm), f, ensure_ascii=False, indent=2)
print("\nWROTE _scv_probe_out.json")
