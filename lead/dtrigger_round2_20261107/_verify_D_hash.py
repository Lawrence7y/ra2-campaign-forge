import hashlib, os

base = "D:/Project/ra2-campaign-forge/"

upstream = {
    "lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md": ("4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726", 48343),
    "lead/dtrigger_compare_20261107/CRITERIA_METRICS.json": ("7e2533eabf795e8aa0063a16ee875d95742880dcefab55d596cfc5aa6e7f958b", 17926),
    "lead/dtrigger_compare_20261107/_cost_quota_data.json": ("e6c26896319acb0387f06384665d5db3668e0f15e29f7328cac97f4931c03cac", 111044),
    "lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt": ("f0177d2cbafdb4dbd388d6b38b97d14ae73688f36f58df4f0fff7edc31a59b66", 5088),
    "lead/d30_ruling_20261106/RULING_D30.md": ("d5afc90c50bbf57be1e58bf9000b1940392337b6c57a444e3b084fe57983d04f", 13197),
    "lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md": ("ed8951e72bd61cd322b1687c4496ec9fc0e8a362c1425d4020901228d885a001", 27271),
    "lead/dstart_observable_20261107/S_OBSERVABILITY.md": ("1d90325ca899c0611ac03dd49a6fb07ede4e21cde2062a5a793a7ea694c9da29", 20133),
}

dD = [
    "lead/dtrigger_round2_20261107/_dD_PHYSICAL_S_ALIGNMENT.md",
    "lead/dtrigger_round2_20261107/_dD_align.py",
    "lead/dtrigger_round2_20261107/_dD_align_out.txt",
    "lead/dtrigger_round2_20261107/_dD_check.py",
    "lead/dtrigger_round2_20261107/_dD_check_out.txt",
]

def h(p):
    with open(p, "rb") as f:
        b = f.read()
    return hashlib.sha256(b).hexdigest(), len(b)

print("=== UPSTREAM (claimed vs actual) ===")
for rel, (sha, n) in upstream.items():
    s, l = h(base + rel)
    ok = (s == sha and l == n)
    print(f"OK={ok} {rel}\n   claimed sha={sha} bytes={n}\n   actual  sha={s} bytes={l}")

print("\n=== DELIVERABLE _dD_ (declared in reply) ===")
decl = {
    "_dD_PHYSICAL_S_ALIGNMENT.md": ("bb61eedbddea61e9ffcb1ac8981dadd8b3ee0fb12c715ccb3e600ca78c50fac1", 18262),
    "_dD_align.py": (None, 18733),
    "_dD_align_out.txt": (None, 9088),
    "_dD_check.py": (None, 7909),
    "_dD_check_out.txt": (None, 5117),
}
for rel in dD:
    s, l = h(base + rel)
    key = rel.split("/")[-1]
    sha_c, n_c = decl[key]
    print(f"{key}: sha={s} bytes={l} | declared_sha={sha_c} declared_bytes={n_c}")
