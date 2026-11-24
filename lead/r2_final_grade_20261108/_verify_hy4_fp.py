import hashlib, pathlib
root = pathlib.Path(r"D:/Project/ra2-campaign-forge")
EXPECT = {
    "lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md": ("bf426786db82c34dd6b6d21e3022678285e3e22f52dbdaa5085d85c3b6f8fbde", 22351),
    "lead/r2_unclosed_b_20261108/B_BREAKPOINTS_2_6.md": ("3aad3bddda087e171d9add1977849b70c01f7ddb5dff23b575186dfb517403ae", 19527),
    "lead/r2_unclosed_cd_20261108/CD_BREAKPOINTS.md": ("affaeae091178c13935caa283f861799b33358e4a162ece130671bb0ea3468dd", 24904),
    "lead/dtrigger_round2_20261107/CRITERIA_ROUND2.md": ("bcd7c8e53f6987a899f78fd1bd8ae90247193f1897aadf15cc58daa45211982a", 49968),
    "lead/dtrigger_round2_20261107/_dA_out.txt": ("8825e115f92bdf407cf20dde724e5633adc4e08e3f97bcee58299b95a8cb6d43", 29813),
    "lead/dtrigger_round2_20261107/_dA_design.md": ("d5d487a7792da6ce89e143faa05727a4fe484cb66b400622c02511230770e0df", 20819),
}
print("=== 6 fingerprinted upstream files (vs 编排方指纹) ===")
allok = True
for rel, (eh, eb) in EXPECT.items():
    p = root / rel
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    ok = (h == eh and len(b) == eb)
    allok = allok and ok
    print(("MATCH" if ok else "MISMATCH"), rel.split("/")[-1], "bytes=%d" % len(b), h)
print("ALL6_MATCH =", allok)

print()
print("=== on-disk 终评 deliverable (binding candidate) ===")
for rel in ["lead/r2_final_grade_20261108/_fg_VERDICT_20261108.md",
            "lead/r2_final_grade_20261108/_fg_hashcheck.py",
            "lead/r2_final_grade_20261108/_fg_recheck.py"]:
    p = root / rel
    if p.is_file():
        b = p.read_bytes()
        print(rel.split("/")[-1], "bytes=%d" % len(b), hashlib.sha256(b).hexdigest())
    else:
        print("MISSING", rel)
