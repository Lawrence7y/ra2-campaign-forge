# -*- coding: utf-8 -*-
# _sc_probe.py : 只读取盘、算 mtime/bytes/sha256；不改任何既有件、不生成 seal。
import os, sys, hashlib, json, datetime, time

ROOT = r"D:\Project\ra2-campaign-forge"

# 10 个关键件（编排方给的表） + 9 个指纹件
FILES = [
    ("seal",          r"lead\cert_realcheck_20261109\_cr_seal.json"),
    ("seal_builder",  r"lead\cert_realcheck_20261109\_cr_build_seal.py"),
    ("real_verify",   r"lead\cert_realcheck_20261109\_cr_real_verify.py"),
    ("V1_reg_out",    r"lead\gate_pipeline_20261109\_gp_regression_out.json"),
    ("V1_reg_py",     r"lead\gate_pipeline_20261109\_gp_regression.py"),
    ("V1_union_out",  r"lead\gate_pipeline_20261109\_gp_regression_v1_union_out.json"),
    ("r9s_pred",      r"lead\gate_r9sem_20261109\_r9s_predicates.py"),
    ("r9s_reg_out",   r"lead\gate_r9sem_20261109\_r9s_regress_out.json"),
    ("fnr_check",     r"lead\falsifiable_no_relax_20261109\_fnr_check.py"),
    ("wl_audit",      r"lead\whitelist_audit_20261109\_WL_WHITELIST_AUDIT.md"),
    ("FP_ORACLE_SPEC",r"lead\oracle_spec_20261109\_os_ORACLE_SPEC.md"),
    ("FP_OS_AUDIT_OUT",r"lead\oracle_spec_20261109\_os_audit_out.json"),
    ("FP_CERT_MD",    r"lead\cert_realcheck_20261109\CERT_REAL_CHECK.md"),
    ("FP_PENDING",    r"lead\PENDING_DECISIONS.md"),
    ("FP_GOAL3T",     r"lead\GOAL_THREE_TARGETS_20261018.md"),
    ("FP_GP_COMPOSE", r"lead\gate_pipeline_20261109\GATE_PIPELINE_COMPOSE.md"),
    ("FP_ORACLE_SPEC_MAIN", r"lead\oracle_spec_20261109\ORACLE_SPEC.md"),
    ("FP_FNR_REPORT", r"lead\falsifiable_no_relax_20261109\FALSIFIABLE_NO_RELAX.md"),
    ("FP_WL_AUDIT",   r"lead\whitelist_audit_20261109\WHITELIST_AUDIT.md"),
]

def h(p):
    d = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            d.update(c)
    return d.hexdigest()

print("PYTHON", sys.version.split()[0])
print("TZ name=%s  time.tzname=%r  time.timezone=%d  time.altzone=%d  daylight=%d"
      % (datetime.datetime.now().astimezone().tzname(), time.tzname,
         time.timezone, time.altzone, time.daylight))
print("NOW local=%s  now utc=%s  epoch=%.3f"
      % (datetime.datetime.now().isoformat(sep=" ", timespec="seconds"),
         datetime.datetime.utcnow().isoformat(sep=" ", timespec="seconds"),
         time.time()))
print()
rows = []
for tag, rel in FILES:
    p = os.path.join(ROOT, rel)
    st = os.stat(p)
    mt = st.st_mtime
    loc = datetime.datetime.fromtimestamp(mt)
    utc = datetime.datetime.utcfromtimestamp(mt)
    row = dict(tag=tag, rel=rel.replace("\\", "/"),
               mtime_epoch_int=int(mt), mtime_epoch_float=round(mt, 3),
               mtime_local=loc.isoformat(sep=" ", timespec="seconds"),
               mtime_utc=utc.isoformat(sep=" ", timespec="seconds"),
               bytes=st.st_size, sha256=h(p),
               ctime_local=datetime.datetime.fromtimestamp(st.st_ctime).isoformat(sep=" ", timespec="seconds"),
               atime_local=datetime.datetime.fromtimestamp(st.st_atime).isoformat(sep=" ", timespec="seconds"))
    rows.append(row)
    print("%-22s local=%s utc=%s epoch=%d bytes=%d sha256=%s"
          % (tag, row["mtime_local"], row["mtime_utc"], row["mtime_epoch_int"],
             row["bytes"], row["sha256"]))

by = {r["tag"]: r for r in rows}
print()
print("=== 时序差（seal - X），单位秒 ===")
for t in ["V1_reg_out", "V1_reg_py", "V1_union_out", "r9s_pred", "r9s_reg_out",
          "fnr_check", "wl_audit", "seal_builder", "real_verify"]:
    d = by["seal"]["mtime_epoch_int"] - by[t]["mtime_epoch_int"]
    s = abs(d)
    hh, rem = divmod(s, 3600)
    mm, ss = divmod(rem, 60)
    print("seal - %-16s = %+7d s = %s%dh %dm %ds" %
          (t, d, "-" if d < 0 else "", hh, mm, ss))

print()
print("=== 9 个编排方指纹逐项比对 ===")
ORCH = {
 r"lead/oracle_spec_20261109/_os_ORACLE_SPEC.md": ("5417fb06fc5ad7b6e2c520b9c83e3bb08c7a4a1bf65c339e1d0048bf695a2156", 52542),
 r"lead/oracle_spec_20261109/_os_audit_out.json": ("c791716862caaa55974adfa1b206c4a4d098d092b11bdf60c99e5cb517ef8b7c", 80300),
 r"lead/cert_realcheck_20261109/_cr_seal.json": ("63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23", 4395),
 r"lead/cert_realcheck_20261109/_cr_real_verify.py": ("3d8ab1092ebf85efe3cc84e22c1eeb98b867a16f44d07cf877f1e2b4eb5c30fa", 21178),
 r"lead/cert_realcheck_20261109/CERT_REAL_CHECK.md": ("fa3a45b7fd96ea8c3130a02227f6b6748bf4f196a5f714a51d3850e6d98ef014", 53782),
 r"lead/falsifiable_no_relax_20261109/_fnr_check.py": ("94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2", 28811),
 r"lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
 r"lead/gate_r9sem_20261109/_r9s_regress_out.json": ("5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25", 75673),
 r"lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
 r"lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
look = {r["rel"]: r for r in rows}
for rel, (sha, nb) in ORCH.items():
    p = os.path.join(ROOT, rel.replace("/", "\\"))
    if not os.path.exists(p):
        print("MISSING", rel); continue
    st = os.stat(p); got = h(p)
    print("%-62s sha=%s bytes=%s  (%d/%d)" %
          (rel, "MATCH" if got == sha else "MISMATCH " + got,
           "MATCH" if st.st_size == nb else "MISMATCH %d" % st.st_size,
           st.st_size, nb))

with open(os.path.join(ROOT, r"lead\seal_chronology_20261109\_sc_probe_out.json"), "w", encoding="utf-8") as f:
    json.dump(dict(rows=rows, orch_fingerprints=list(ORCH.keys())), f, ensure_ascii=False, indent=2)
print("\nWROTE _sc_probe_out.json")
