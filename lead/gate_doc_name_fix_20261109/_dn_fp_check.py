# -*- coding: utf-8 -*-
"""复核编排方实跑指纹。零真机、只读。"""
import hashlib, json, os

ROOT = r"D:\Project\ra2-campaign-forge"
FILES = [
    ("lead/gate_subject_id_20261109/GATE_SUBJECT_ID_FIX.md", "302a45644359f14d4f420225ac56784579a658cb852a0b0df0ddde6532adf63c", 31692),
    ("lead/gate_subject_id_20261109/_si_SUBJECT_ID_DEFECT.md", "8c67dc3fc950baf16e4e39b650ca25210e24e3512307a09eaf30cc9cecd6f4dc", 23441),
    ("lead/gate_subject_id_20261109/_si_fix_lib.py", "54751e9a10bca4becfae3449d4a19155dc7744dff77a8a22d7d70d9a7fd70eee", 2850),
    ("lead/gate_subject_id_20261109/_si_gatescan_out.json", "c8024cb7e538dfbc3766acc08d231789b80d601d7cc4bba4e05ed89d8ff87d94", 611043),
    ("lead/gate_subject_id_20261109/_si_wfscan_out.json", "e326df6b4040dc9e5471f891c8db55d8ede1681434336de5e5626c43e2029f52", 180256),
    ("lead/gate_subject_id_20261109/_si_exploit_out.txt", "151f4f94b890403ba4785a7d570ad11abbe68a4aa12363967682729167e2c587", 5717),
    ("lead/PENDING_DECISIONS.md", "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md", "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]

out = []
ok = True
for rel, exp_sha, exp_bytes in FILES:
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        out.append({"rel": rel, "status": "MISSING"})
        ok = False
        continue
    data = open(p, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    n = len(data)
    match = (sha == exp_sha and n == exp_bytes)
    if not match:
        ok = False
    out.append({"rel": rel, "sha256": sha, "bytes": n, "match": match})

print(json.dumps({"all_match": ok, "files": out}, ensure_ascii=False, indent=1))
