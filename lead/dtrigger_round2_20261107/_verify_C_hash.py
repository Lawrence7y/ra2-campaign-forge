import hashlib, os

ROOT = r"D:/Project/ra2-campaign-forge"
UPSTREAM = {
    "lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md": ("4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726", 48343),
    "lead/dtrigger_compare_20261107/CRITERIA_METRICS.json": ("7e2533eabf795e8aa0063a16ee875d95742880dcefab55d596cfc5aa6e7f958b", 17926),
    "lead/dtrigger_compare_20261107/_cost_quota_data.json": ("e6c26896319acb0387f06384665d5db3668e0f15e29f7328cac97f4931c03cac", 111044),
    "lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt": ("f0177d2cbafdb4dbd388d6b38b97d14ae73688f36f58df4f0fff7edc31a59b66", 5088),
    "lead/d30_ruling_20261106/RULING_D30.md": ("d5afc90c50bbf57be1e58bf9000b1940392337b6c57a444e3b084fe57983d04f", 13197),
    "lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md": ("ed8951e72bd61cd322b1687c4496ec9fc0e8a362c1425d4020901228d885a001", 27271),
    "lead/dstart_observable_20261107/S_OBSERVABILITY.md": ("1d90325ca899c0611ac03dd49a6fb07ede4e21cde2062a5a793a7ea694c9da29", 20133),
}
DELIVERABLES = {
    "lead/dtrigger_round2_20261107/_dC_recompute.py": ("ec64adac558e87e5cdf53563368c7aacea712222e70f303ca85deb83eb08ee3a", 23115),
    "lead/dtrigger_round2_20261107/_dC_out.txt": ("a0deb34a4aed83efe3d0b80dfff4f05eb28eeec5fac5613ff49316fd8081337a", 13473),
    "lead/dtrigger_round2_20261107/_dC_cells.txt": ("8e05b65e8d4bface4e80b5df5bc246a41ea1800c808bf5b69b4a7587c747e6f1", 25324),
}

def fp(rel):
    p = os.path.join(ROOT, rel)
    b = open(p, "rb").read()
    return hashlib.sha256(b).hexdigest(), len(b)

print("=== UPSTREAM (7) ===")
for rel, (sha, size) in UPSTREAM.items():
    got_sha, got_size = fp(rel)
    print("%s SHA256 = %s bytes = %d  %s" % (rel, got_sha, got_size,
          "MATCH" if (got_sha == sha and got_size == size) else "MISMATCH expected %s/%d" % (sha, size)))

print("=== _dC_* files in write domain ===")
d = os.path.join(ROOT, "lead/dtrigger_round2_20261107")
for name in sorted(os.listdir(d)):
    if name.startswith("_dC_"):
        rel = "lead/dtrigger_round2_20261107/" + name
        got_sha, got_size = fp(rel)
        exp = DELIVERABLES.get(rel)
        tag = ""
        if exp:
            tag = "  " + ("MATCH" if (got_sha == exp[0] and got_size == exp[1]) else "MISMATCH expected %s/%d" % exp)
        print("%s SHA256 = %s bytes = %d%s" % (rel, got_sha, got_size, tag))
