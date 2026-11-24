import hashlib, os

ROOT = "D:/Project/ra2-campaign-forge"

# 编排方基线（九件），来自本任务 ask 的【编排方指纹】
BASE = {
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    "lead/check_masking_20261109/CHECK_MASKING_INJECT.md": ("99131e8aa03717c555a56b7cee75cf747b4127287e2cc1ec9b6bef5656da3c6c", 56575),
    "lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md": ("2f55283ef3380c6cb5915b2e8654a5506061ccb667a986d397b45a10a2f9119f", 45536),
    "lead/d27_ruling_20261106/check_d27.py": ("3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c", 3764),
    "lead/d29_ruling_20261106/check_d29.py": ("2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14", 3906),
    "lead/d30_ruling_20261106/check_d30.py": ("6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd", 3926),
    "lead/refsync_scope_20261109/_rs_carrier_scan.py": ("9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57", 16053),
    "lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md": ("83b215ccbbf2c3e221c247e7bd9c7c221fddcf9472977d2df8902bf1b94ec65e", 49958),
}


def digest(rel):
    p = os.path.join(ROOT, rel)
    with open(p, "rb") as f:
        b = f.read()
    return hashlib.sha256(b).hexdigest(), len(b)


print("=== ① 九件指纹实算 vs 编排方基线 ===")
all_ok = True
for rel, (sha0, n0) in BASE.items():
    h, n = digest(rel)
    ok = (h == sha0 and n == n0)
    all_ok = all_ok and ok
    flag = "OK" if ok else "MISMATCH"
    print(f"{flag} {rel}  sha={h}  bytes={n}  base_sha={sha0}  base_bytes={n0}")
print("NINE_ALL_MATCH =", all_ok)

print("=== 绑定行对象：被核报告本体 ===")
rel = "lead/stale_pass_20261109/_sp_STALE_PASS_CENSUS.md"
h, n = digest(rel)
txt = open(os.path.join(ROOT, rel), "rb").read().decode("utf-8")
lines = len(txt.splitlines())
print("REPORT sha256 =", h)
print("REPORT bytes =", n)
print("REPORT lines =", lines)
print("被核对象 SHA256 =", h, "，字节数 =", n)
