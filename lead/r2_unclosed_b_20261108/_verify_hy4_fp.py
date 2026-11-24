import hashlib, os, sys

ROOT = r"D:\Project\ra2-campaign-forge"

CLAIMED = {
    r"lead\dtrigger_round2_20261107\_dB_anchor_recompute.py": ("44b10371cdc258e7db5c232f53d9d64dfdf4f34cb084115d0bb8c7a05a5a382b", 27324),
    r"lead\dtrigger_round2_20261107\_dB_anchor_recompute_out.txt": ("3e9588ce1def2ebc5b9ad77a3ce242b47bcada4ae1ab1bc4ea606775edd40807", 14479),
    r"lead\dtrigger_round2_20261107\_verify_B_out.txt": ("4ee6a6b78d80a336c3431a6f71d9f5a77fec93ef65b7a4c642a49b669368c107", 7229),
    r"lead\dtrigger_round2_20261107\_dB_anchor_recompute_data.json": ("8fb149f21e9b41d7c808e8f8c2e1cb35ca62b881ebe65bfba7029b6f95763794", 42910),
    r"lead\criteria_r3_verify_20261108\R2_BREAKPOINTS_CLOSURE.md": ("bf426786db82c34dd6b6d21e3022678285e3e22f52dbdaa5085d85c3b6f8fbde", 22351),
    r"lead\dtrigger_compare_20261107\CRITERIA_COMPARE.md": ("4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726", 48343),
}

def fp(path):
    with open(path, "rb") as f:
        b = f.read()
    return hashlib.sha256(b).hexdigest(), len(b)

print("=== A. 编排方 6 件指纹独立实算 ===")
for rel, (sha, n) in CLAIMED.items():
    p = os.path.join(ROOT, rel)
    got_sha, got_n = fp(p)
    print(f"{rel}\n  sha256={got_sha}\n  bytes={got_n}\n  MATCH_SHA={got_sha == sha} MATCH_BYTES={got_n == n}")

print()
print("=== B. 补证回件自身文本（来自被核对象 what 字段转述）对照 ===")
# 被核对象 what 中声明的 hashlib 实算值
own = {
    "_dB_anchor_recompute.py": ("44b10371…382b", 27324),
    "_dB_anchor_recompute_out.txt": ("3e9588ce…40807", 14479),
    "_dB_anchor_recompute_data.json": ("8fb149f2…763794", 42910),
}
print("  what 字段缩写值 -> 与 A 段全值前缀/后缀对照（人工判读）")
for rel, (sha, n) in CLAIMED.items():
    base = os.path.basename(rel)
    if base in own:
        abbr, on = own[base]
        pre, suf = abbr.split("…")
        s, b = fp(os.path.join(ROOT, rel))
        print(f"  {base}: abbr={abbr}  prefix_ok={s.startswith(pre)}  suffix_ok={s.endswith(suf)}  bytes_ok={b==on}")

print()
print("=== C. 指纹尾串归属独立实算 ===")
tails = ["26f3fb61829756dfeecf", "b6f95763794"]
for rel, (sha, n) in CLAIMED.items():
    s, b = fp(os.path.join(ROOT, rel))
    for t in tails:
        if t in s:
            print(f"  tail {t} IN {os.path.basename(rel)} sha: pos={s.find(t)} endswith={s.endswith(t)}")
print("  -- data.json sha 末 11/12 位 --")
p = os.path.join(ROOT, r"lead\dtrigger_round2_20261107\_dB_anchor_recompute_data.json")
s, b = fp(p)
print(f"  data.json sha256={s}")
print(f"  sha[-11:]={s[-11:]}  sha[-12:]={s[-12:]}")
print(f"  b6f95763794 == sha[-11:] ? {s[-11:] == 'b6f95763794'}")
print(f"  b6f95763794 == sha[-12:] ? {s[-12:] == 'b6f95763794'}")
print(f"  sha.find('b6f95763794')={s.find('b6f95763794')}")

print()
print("=== D. 写域文件清单（只读检查） ===")
wd = os.path.join(ROOT, r"lead\r2_unclosed_b_20261108")
for fn in sorted(os.listdir(wd)):
    p = os.path.join(wd, fn)
    if os.path.isfile(p):
        s, b = fp(p)
        print(f"  {fn}: sha256={s} bytes={b}")
