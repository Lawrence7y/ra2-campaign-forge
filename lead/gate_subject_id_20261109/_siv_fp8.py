# -*- coding: utf-8 -*-
# _siv_fp8.py — 复核①：实算八件编排方指纹 + 被核对象绑定件（hashlib，只读）
import hashlib, json, sys, time

BASE = r"D:\Project\ra2-campaign-forge"
BASELINE = [
    ("lead/counterpart_fix_20261109/COUNTERPART_FIX.md", "e291f5a8f8b2c303b31e7f06989233e122460d9838817271fa425cae066ff416", 32830),
    ("lead/counterpart_fix_20261109/_cf_counterpart_vs_tighten_20261109.md", "9878bb7ec170599dd8d74eacfa0a7be0806294d91d8be994a456ad6ed864ddb4", 32840),
    ("lead/strict_exposure_20261109/STRICT_EXPOSURE.md", "3a4b1bb7cf7f0bd501b3e99d575c4907dd0e17f5557dd0b8826e5fb07fe2bdc8", 23798),
    ("lead/u5u6_mirror_20261109/U5U6_MIRROR_TEXTS.md", "f320a80110806e6b57281988085d40776b43e719123db29cdb6564fe68c6c545", 24897),
    ("lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md", "823476680c4c7aab7ead279a3f47724dbd1b2fed977087ae86c35a4eef36258c", 30536),
    ("lead/text_fix_unified_20261109/UNIFIED_TEXT_FIX.md", "ec0fb8ec47cfb71be5b28bc8a76f9152a6cbd377e741e7be1902a0958fbba154", 42172),
    ("lead/PENDING_DECISIONS.md", "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md", "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]
SUBJECT = [
    ("lead/gate_subject_id_20261109/GATE_SUBJECT_ID_FIX.md", "8c67dc3fc950baf16e4e39b650ca25210e24e3512307a09eaf30cc9cecd6f4dc", 23441),
    ("lead/gate_subject_id_20261109/_si_SUBJECT_ID_DEFECT.md", "8c67dc3fc950baf16e4e39b650ca25210e24e3512307a09eaf30cc9cecd6f4dc", 23441),
]

def fp(rel):
    p = BASE + "\\" + rel.replace("/", "\\")
    b = open(p, "rb").read()
    return hashlib.sha256(b).hexdigest(), len(b), p

t0 = time.perf_counter()
out = []
ok_all = True
for rel, exp_sha, exp_bytes in BASELINE:
    sha, n, p = fp(rel)
    ok = (sha == exp_sha and n == exp_bytes)
    ok_all = ok_all and ok
    out.append({"file": rel, "sha256": sha, "bytes": n, "expected_sha": exp_sha, "expected_bytes": exp_bytes, "ok": ok})
    print(("OK " if ok else "MISMATCH ") + rel + "  sha256=" + sha + "  bytes=" + str(n))

print("---subject binding---")
for rel, exp_sha, exp_bytes in SUBJECT:
    sha, n, p = fp(rel)
    ok = (sha == exp_sha and n == exp_bytes)
    same = SUBJECT[0]
    print(rel + "  sha256=" + sha + "  bytes=" + str(n) + ("  OK" if ok else "  MISMATCH"))
out.append({"subject_binding": SUBJECT[0][0], "sha256": fp(SUBJECT[0][0])[0], "bytes": fp(SUBJECT[0][0])[1]})
out.append({"twin_same_bytes": fp(SUBJECT[1][0])[0] == fp(SUBJECT[0][0])[0]})
out.append({"ALL_OK": ok_all})
out.append({"elapsedSec": round(time.perf_counter() - t0, 4)})
w = BASE + r"\lead\gate_subject_id_20261109\_siv_fp8_out.json"
open(w, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print("ALL_OK=" + str(ok_all) + " elapsedSec=" + str(round(time.perf_counter() - t0, 4)))
print("written=" + w)
