import hashlib, os, sys

ROOT = r"D:/Project/ra2-campaign-forge"
WD = os.path.join(ROOT, "lead", "perf_repair_n11_20261108")

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest(), os.path.getsize(path)

print("=== deliverables in write domain ===")
for name in sorted(os.listdir(WD)):
    p = os.path.join(WD, name)
    if os.path.isfile(p):
        d, n = sha256_of(p)
        print(f"{name}\tSHA256={d}\tbytes={n}")

print()
print("=== upstream fingerprint verification ===")
upstream = {
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md": ("c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225),
    "lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md": ("e7c29e06f48b2380d5bec3f99e08ac2a4ce90d94da27b48b98d5eb2113a75d60", 23707),
    "lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md": ("5b933fe2fcb3cc35c5026cb57b45f29da29c90b67a618346af248744ed3ccdb9", 32281),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
allmatch = True
for rel, (exp_sha, exp_bytes) in upstream.items():
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        print(f"{rel}\tMISSING")
        allmatch = False
        continue
    got_sha, got_bytes = sha256_of(p)
    m = (got_sha == exp_sha and got_bytes == exp_bytes)
    allmatch = allmatch and m
    print(f"{rel}\tsha_match={got_sha==exp_sha}\tbytes_match={got_bytes==exp_bytes}\tgot_sha={got_sha}\tgot_bytes={got_bytes}\tMATCH={m}")
print(f"ALL_UPSTREAM_MATCH={allmatch}")
