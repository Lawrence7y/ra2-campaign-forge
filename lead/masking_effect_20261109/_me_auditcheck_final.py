# -*- coding: utf-8 -*-
"""_me_auditcheck_final.py — structural validation of MASKING_EFFECT_AUDIT.md
plus final discipline/fingerprint checks. NEW file, sole write domain."""
import io, os, re, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DOC = os.path.join(HERE, "MASKING_EFFECT_AUDIT.md")
b = io.open(DOC, "rb").read()
t = b.decode("utf-8")
ls = t.splitlines()
print("FILE = %s" % DOC)
print("bytes = %d ; sha256 = %s ; lines = %d" % (len(b), hashlib.sha256(b).hexdigest(), len(ls)))
print()
print("=== required six sections (## 1 .. ## 6) ===")
secs = [(i, l) for i, l in enumerate(ls, 1) if re.match(r"^## [1-6]\b", l)]
for i, l in secs:
    print("  %4d: %s" % (i, l))
print("  section count = %d" % len(secs))
print()
print("=== required elements (count) ===")
els = ["掩蔽", "单 needle", "双 needle", "SELF_TEST", "not-scanned", "四道门",
       "反向掩蔽", "可区分", "逐 needle 自检", "掩蔽检测判据", "通用形态",
       "报 PASS", "未验"]
for e in els:
    print("  %-18s %d" % (e, t.count(e)))
print()
print("=== three numbers present ===")
for n in ["79", "84", "122", "43", "38", "41"]:
    print("  %-4s : %d occurrences" % (n, t.count(n)))
print()
print("=== binding line (exact format) ===")
m = re.search(r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)", t)
if m:
    print("  FOUND: hash=%s bytes=%s" % (m.group(1), m.group(2)))
    print("  hash matches scanner = %s" %
          (m.group(1) == "9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57"))
else:
    print("  MISSING or WRONG FORMAT")
print()
print("=== verdict / unconfirmed ===")
print("  'partial' = %d ; 'unconfirmed' = %d" % (t.count("partial"), t.count("unconfirmed")))
print()
print("=== pasteable code blocks ===")
print("  ```python count = %d" % t.count("```python"))
print()
print("=== .mimosa artifact in write domain ===")
mim = os.path.join(HERE, ".mimosa")
if os.path.isdir(mim):
    for dp, dn, fn in os.walk(mim):
        for f in fn:
            p = os.path.join(dp, f)
            print("  %s bytes=%d mtime=%s" %
                  (os.path.relpath(p, HERE), os.path.getsize(p), os.path.getmtime(p)))
else:
    print("  (none)")
print()
print("=== closing 8/8 fingerprint recheck ===")
FP = {
 "lead/refsync_scope_20261109/_rs_carrier_scan.py": ("9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57", 16053),
 "lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md": ("83b215ccbbf2c3e221c247e7bd9c7c221fddcf9472977d2df8902bf1b94ec65e", 49958),
 "lead/refsync_scope_20261109/_rs_CARRIER_MAP.md": ("aa2dbe945c9d8fdc6aebde849701393f6f8766c51b372329d588616781c2f83f", 35782),
 "lead/needle_norm_20261109/_nn_REPORT.md": ("820db1eb93a630344623fb055449dfbd888cb46294dba3f462d9891a1d91e041", 40549),
 "lead/needle_norm_20261109/NEEDLE_NORMALIZATION.md": ("c0e716ec2baaab0082d0c7af83a351b9aa12eb01a4bf2ba6a223c8b81c5de8e6", 41618),
 "lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md": ("058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec", 18980),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
ok = 0
for rel, (w, wn) in FP.items():
    bb = io.open(os.path.join(ROOT, rel), "rb").read()
    good = (hashlib.sha256(bb).hexdigest() == w and len(bb) == wn)
    ok += good
    print("  %s %s" % ("OK" if good else "MISMATCH", rel))
print("  CLOSING = %d/8 OK" % ok)
