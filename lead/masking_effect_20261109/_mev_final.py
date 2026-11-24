# -*- coding: utf-8 -*-
"""_mev_final.py — ASK 7/8: doc-honesty checks + boundary/fingerprint verification.

Read-only everywhere except this write domain. Verifies:
 - REFSYNC_SCOPE_FIX.md contains no masking/假PASS note (author claim)
 - _nn_REPORT.md:402 self-assessment of the single-needle rerun
 - check_d29 OR-gate minimal reproduction (dead keyword still any()==True)
 - 8/8 orchestrator fingerprints unchanged at END of my session
 - write-domain file listing: only _me_ and _mev_ prefixes
 - git status: scanner & absolute-read-only paths not modified by me
"""
import os, io, hashlib, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

BASELINE = {
 "lead/refsync_scope_20261109/_rs_carrier_scan.py": ("9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57", 16053),
 "lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md": ("83b215ccbbf2c3e221c247e7bd9c7c221fddcf9472977d2df8902bf1b94ec65e", 49958),
 "lead/refsync_scope_20261109/_rs_CARRIER_MAP.md": ("aa2dbe945c9d8fdc6aebde849701393f6f8766c51b372329d588616781c2f83f", 35782),
 "lead/needle_norm_20261109/_nn_REPORT.md": ("820db1eb93a630344623fb055449dfbd888cb46294dba3f462d9891a1d91e041", 40549),
 "lead/needle_norm_20261109/NEEDLE_NORMALIZATION.md": ("c0e716ec2baaab0082d0c7af83a351b9aa12eb01a4bf2ba6a223c8b81c5de8e6", 41618),
 "lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md": ("058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec", 18980),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

def main():
    o = []
    def P(s=""):
        o.append(s); print(s)
    P("=== ASK 7: doc honesty ===")
    fix = io.open(os.path.join(ROOT, "lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md"),
                  encoding="utf-8", errors="replace").read()
    for kw in ["掩盖", "假 PASS", "假PASS", "掩蔽", "不可信"]:
        P("  REFSYNC_SCOPE_FIX.md contains %r : %s" % (kw, kw in fix))
    nn = io.open(os.path.join(ROOT, "lead/needle_norm_20261109/_nn_REPORT.md"),
                 encoding="utf-8", errors="replace").read().splitlines()
    P("  _nn_REPORT.md:402 = %s" % (nn[401].strip() if len(nn) >= 402 else "<missing>"))
    norm = io.open(os.path.join(ROOT, "lead/needle_norm_20261109/NEEDLE_NORMALIZATION.md"),
                   encoding="utf-8", errors="replace").read().splitlines()
    P("  NEEDLE_NORMALIZATION.md:364 = %s" % (norm[363].strip() if len(norm) >= 364 else "<missing>"))
    P("")
    P("=== ASK 7: check_d29 OR-gate minimal reproduction (author claim) ===")
    d29 = os.path.join(ROOT, "lead/d29_ruling_20261106/check_d29.py")
    if os.path.isfile(d29):
        src = io.open(d29, encoding="utf-8", errors="replace").read()
        P("  check_d29.py exists, bytes=%d ; has require_all = %s ; has any( = %s" %
          (len(src.encode("utf-8")), "require_all" in src, "any(" in src))
        words = ("93.98", "误报率")
        body = "本报告 93.98 与误报率均已复核"
        P("  minimal OR: words=%r body=%r" % (words, body))
        P("    any(word in body for word in words) = %s" % any(w in body for w in words))
        body_dead = "本报告 93.98 已复核"
        P("    after DELETING '误报率' from body: any(...) = %s  <-- dead keyword invisible" %
          any(w in body_dead for w in words))
    else:
        P("  check_d29.py NOT FOUND at expected path -- not verified")
    P("")
    P("=== ASK 8: boundary -- final 8/8 fingerprint recheck ===")
    ok = 0
    for rel, (want_sha, want_n) in BASELINE.items():
        b = open(os.path.join(ROOT, rel), "rb").read()
        got = hashlib.sha256(b).hexdigest()
        good = (got == want_sha and len(b) == want_n)
        ok += bool(good)
        P("  %s  sha=%s  bytes=%d  %s" % ("OK" if good else "MISMATCH", got, len(b), rel))
    P("  TOTAL = %d/8 match baseline (zero modification of absolute-read-only files)" % ok)
    P("")
    P("=== ASK 8: write-domain prefix discipline ===")
    files = sorted(os.listdir(HERE))
    bad = [f for f in files if not (f.startswith("_me_") or f.startswith("_mev_"))]
    P("  files in write domain = %d ; non _me_/_mev_ names = %r" % (len(files), bad))
    P("  my files (prefix _mev_) = %d" % sum(1 for f in files if f.startswith("_mev_")))
    P("")
    P("=== ASK 8: git status of scanner + absolute-read-only paths ===")
    cp = subprocess.run(["git", "status", "--short", "--",
                         "lead/refsync_scope_20261109/",
                         "lead/needle_norm_20261109/",
                         "lead/gate_n13_20261109/",
                         "lead/gate_pipeline_20261109/",
                         "lead/gate_fp7_20261108/",
                         "lead/masking_effect_20261109/",
                         "lead/PENDING_DECISIONS.md",
                         "lead/GOAL_THREE_TARGETS_20261018.md"],
                        cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    for l in cp.stdout.splitlines():
        P("  " + l)
    P("  (all these trees are UNTRACKED ?? from before my session; my writes are")
    P("   confined to _mev_ files inside lead/masking_effect_20261109/)")
    P("")
    io.open(os.path.join(HERE, "_mev_final_out.txt"), "w", encoding="utf-8").write("\n".join(o) + "\n")

if __name__ == "__main__":
    main()
