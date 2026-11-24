import os, hashlib, json

ROOT = r"D:\Project\ra2-campaign-forge"

BASE = {
 "15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0": 9148,
 "10a90814d09f49b88fa378943960e137c20a426a47785de4dea22c55c3324100": 30098,
 "994e36a2bf6b977cff2eb3887607e6f2682966e19008389cd9391c0c78435bfb": 10484,
 "e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079": 16649,
 "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120": 11743,
 "a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6": 11623,
 "0d129e409ca5ab744891abccd85a0c0ca0c164ddea8620de634de5079fa8f096": 22133,
 "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7": 52419,
 "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede": 759518,
}

# Recursively map sha256 -> list of (relpath, size)
found = {}
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "node_modules")]
    for f in files:
        p = os.path.join(root, f)
        try:
            with open(p, "rb") as fh:
                b = fh.read()
        except OSError:
            continue
        h = hashlib.sha256(b).hexdigest()
        if h in BASE:
            rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
            found.setdefault(h, []).append((rel, len(b)))

print("=== A. independent resolution of the 9 baseline hashes ===")
for h, sz in BASE.items():
    hits = found.get(h, [])
    print(h[:16], "expect_bytes=%d" % sz, "->", hits if hits else "NOT FOUND")

# Explicit named paths (as far as they can be resolved) - recompute directly
explicit = [
 "lead/gate_v1v2_20261109/_v12_rule.py",
 "lead/gate_v1v2_20261109/_v12_REPORT.md",
 "lead/gate_v1v2_20261109/_v12_regression.json",
 "lead/gate_n13_20261109/_n13_predicates.py",
 "lead/gate_fp7_20261108/_g7_predicates.py",
 "lead/gate_r9r12_20261109/_g9_gate.py",
 "lead/gate_doc_name_fix_20261109/_dn_regate_out.json",
 "lead/PENDING_DECISIONS.md",
 "lead/GOAL_THREE_TARGETS_20261018.md",
]
print()
print("=== B. direct path recompute (hashlib, raw bytes) ===")
ok = 0
for rel in explicit:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    try:
        with open(p, "rb") as fh:
            b = fh.read()
    except OSError as e:
        print("MISSING", rel, e)
        continue
    h = hashlib.sha256(b).hexdigest()
    match = (h in BASE and BASE[h] == len(b))
    if match:
        ok += 1
    print("%-62s bytes=%-8d sha256=%s  baseline_match=%s" % (rel, len(b), h, match))
print("direct_path_match = %d/%d" % (ok, len(explicit)))
