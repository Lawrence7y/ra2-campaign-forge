import hashlib

FILES = [
    r"D:\Project\ra2-campaign-forge\lead\criteria_r3_verify_20261108\R2_BREAKPOINTS_CLOSURE.md",
    r"D:\Project\ra2-campaign-forge\lead\r2_unclosed_b_20261108\B_BREAKPOINTS_2_6.md",
    r"D:\Project\ra2-campaign-forge\lead\r2_unclosed_cd_20261108\CD_BREAKPOINTS.md",
    r"D:\Project\ra2-campaign-forge\lead\dtrigger_round2_20261107\CRITERIA_ROUND2.md",
    r"D:\Project\ra2-campaign-forge\lead\dtrigger_round2_20261107\_dA_out.txt",
    r"D:\Project\ra2-campaign-forge\lead\dtrigger_round2_20261107\_dA_design.md",
    # 抽查引用目标（见 _fg_citecheck 输出）
    r"D:\Project\ra2-campaign-forge\lead\r2_unclosed_cd_20261108\_cd_verdict.md",
]

EXPECT = {
    "R2_BREAKPOINTS_CLOSURE.md": ("bf426786db82c34dd6b6d21e3022678285e3e22f52dbdaa5085d85c3b6f8fbde", 22351),
    "B_BREAKPOINTS_2_6.md": ("3aad3bddda087e171d9add1977849b70c01f7ddb5dff23b575186dfb517403ae", 19527),
    "CD_BREAKPOINTS.md": ("affaeae091178c13935caa283f861799b33358e4a162ece130671bb0ea3468dd", 24904),
    "CRITERIA_ROUND2.md": ("bcd7c8e53f6987a899f78fd1bd8ae90247193f1897aadf15cc58daa45211982a", 49968),
    "_dA_out.txt": ("8825e115f92bdf407cf20dde724e5633adc4e08e3f97bcee58299b95a8cb6d43", 29813),
    "_dA_design.md": ("d5d487a7792da6ce89e143faa05727a4fe484cb66b400622c02511230770e0df", 20819),
}

for p in FILES:
    with open(p, "rb") as f:
        b = f.read()
    h = hashlib.sha256(b).hexdigest()
    name = p.replace("\\", "/").split("/")[-1]
    if name in EXPECT:
        eh, eb = EXPECT[name]
        ok = (h == eh and len(b) == eb)
        print("MATCH" if ok else "MISMATCH", name, "bytes=%d" % len(b), h)
        if not ok:
            print("  expect bytes=%d %s" % (eb, eh))
    else:
        print("REF    ", name, "bytes=%d" % len(b), h)
