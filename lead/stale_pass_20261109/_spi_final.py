import hashlib, os, re
ROOT = "D:/Project/ra2-campaign-forge"
REL = "lead/stale_pass_20261109/STALE_PASS_INVENTORY.md"
p = os.path.join(ROOT, REL)
b = open(p, "rb").read()
sha = hashlib.sha256(b).hexdigest()
n = len(b)
lines = b.decode("utf-8").splitlines()
print("DELIVERABLE =", REL)
print("SHA256 =", sha)
print("BYTES =", n)
print("LINES(splitlines) =", len(lines))

# strict binding line mechanical check
pat = re.compile(r"^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$")
bs = [(i+1, m.group(1), m.group(2)) for i, l in enumerate(lines) if (m := pat.match(l))]
print("STRICT_BINDING_LINES =", len(bs))
print("ALL_64HEX =", all(re.fullmatch(r"[0-9a-f]{64}", x[1]) for x in bs))
EXPECT = [
    ("f2d8fb32d196af4a2f143be8652d513437b60b3b885c862051a60a9f37dcb391", "52161"),
    ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", "52419"),
    ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", "759518"),
    ("99131e8aa03717c555a56b7cee75cf747b4127287e2cc1ec9b6bef5656da3c6c", "56575"),
    ("2f55283ef3380c6cb5915b2e8654a5506061ccb667a986d397b45a10a2f9119f", "45536"),
    ("3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c", "3764"),
    ("2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14", "3906"),
    ("6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd", "3926"),
    ("9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57", "16053"),
    ("83b215ccbbf2c3e221c247e7bd9c7c221fddcf9472977d2df8902bf1b94ec65e", "49958"),
]
print("BINDINGS_MATCH_BASE =", [(x[1], x[2]) for x in bs] == EXPECT)

# six sections
secs = [(i+1, l) for i, l in enumerate(lines) if re.match(r"^## [1-6] ", l)]
print("SECTIONS =", [x[1][:40] for x in secs])

# required tokens
req = ["A 级", "B 级", "C 级", "已证明不可信", "输入已变", "需复核", "影响面",
       "实质结论", "形式要件", "重跑方案", "登记模板", "制度", "未验",
       "partial", "unconfirmed", "file:line"]
txt = "\n".join(lines)
for t in req:
    print("REQUIRED %-14s = %s (count=%d)" % (t, t in txt, txt.count(t)))

# verdict honest check
print("VERDICT_PARTIAL_PRESENT =", "verdict = **partial**" in txt)
print("UNCONFIRMED_PRESENT =", "unconfirmed" in txt)
# no modifications to ledgers: recheck 9 fingerprints
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
ok = True
for rel, (s, z) in BASE.items():
    bb = open(os.path.join(ROOT, rel), "rb").read()
    ok &= (hashlib.sha256(bb).hexdigest() == s and len(bb) == z)
print("NINE_ALL_MATCH_END =", ok)
