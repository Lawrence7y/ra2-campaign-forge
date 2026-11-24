# -*- coding: utf-8 -*-
# _svw_fingerprints.py — seal_v2 成件撰写员的自证脚本（只读，零网络，零真机）
# 作用：对本任务引用的全部 14 件实算 sha256+bytes，与编排方基线 7 件、
#       评估员补算 5 件、复核员绑定 2 件逐一比对。只读，不写任何被核对象。
import hashlib
import os

BASE = r"D:\Project\ra2-campaign-forge"

# (相对路径, 期望 sha256, 期望 bytes, 来源)
TARGETS = [
    ("lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419, "编排方基线"),
    ("lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518, "编排方基线"),
    ("lead/ordering_evidence_20261109/ORDERING_EVIDENCE.md",
     "04217b1321f7b9fc576fae39be43c5718e0ced65ee4212b5cfc11807dbb99da0", 47952, "编排方基线"),
    ("lead/cert_realcheck_20261109/_cr_seal.json",
     "63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23", 4395, "编排方基线"),
    ("lead/cert_realcheck_20261109/_cr_build_seal.py",
     "2e539d392b0aca54cb8cd2c83bd20e1d87ba9ce5cbc8f15ea5ea279ef0b86574", 5376, "编排方基线"),
    ("lead/cert_realcheck_20261109/_cr_real_verify.py",
     "3d8ab1092ebf85efe3cc84e22c1eeb98b867a16f44d07cf877f1e2b4eb5c30fa", 21178, "编排方基线"),
    ("lead/falsifiable_no_relax_20261109/_fnr_check.py",
     "94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2", 28811, "编排方基线"),
    ("lead/seal_chronology_20261109/SEAL_CHRONOLOGY.md",
     "6b5eda3e58c439c576d3e6e6f8c91220e9b36201280f7672eb4c9ca9140b55ea", 55693, "评估员补算"),
    ("lead/oracle_spec_20261109/ORACLE_SPEC.md",
     "7f9316ddfa33f405281bd2d33b0e22be7f7cc60c7d00dd070901b1392993a4a0", 49318, "评估员补算"),
    ("lead/oracle_spec_20261109/_os_ORACLE_SPEC.md",
     "5417fb06fc5ad7b6e2c520b9c83e3bb08c7a4a1bf65c339e1d0048bf695a2156", 52542, "评估员补算"),
    ("lead/cert_realcheck_20261109/CERT_REAL_CHECK.md",
     "fa3a45b7fd96ea8c3130a02227f6b6748bf4f196a5f714a51d3850e6d98ef014", 53782, "评估员补算"),
    ("lead/falsifiable_no_relax_20261109/FALSIFIABLE_NO_RELAX.md",
     "c54694849bb2ad84126c86d692f53ca3ba7362e33ede3a4c45dffebf275de0da", 45824, "评估员补算"),
    ("lead/seal_v2_feasibility_20261109/_sv_FEASIBILITY.md",
     "68c3debd4f6617a604829c570f887ec2afc61ffc3d7fe90aaa6da3ef54d92586", 63478, "复核员第二绑定"),
    ("lead/seal_v2_feasibility_20261109/_svv_evaluator_reply.json",
     "d589eff19655c7c3efebe9c7789e279fd15b1ed9094a800a889167140bdd118c", 26788, "复核员第一绑定"),
]

results = []
for rel, exp_sha, exp_bytes, src in TARGETS:
    p = os.path.join(BASE, rel)
    try:
        with open(p, "rb") as f:
            data = f.read()
        got_sha = hashlib.sha256(data).hexdigest()
        got_bytes = len(data)
        ok = (got_sha == exp_sha) and (got_bytes == exp_bytes)
        results.append((rel, src, ok, got_sha, got_bytes, exp_sha, exp_bytes))
    except OSError as e:
        results.append((rel, src, False, "READ_ERROR:%s" % e.errno, -1, exp_sha, exp_bytes))

n_ok = sum(1 for r in results if r[2])
for rel, src, ok, got_sha, got_bytes, exp_sha, exp_bytes in results:
    tag = "MATCH" if ok else "MISMATCH"
    print("%s [%s/%s] %s bytes=%d" % (tag, src, tag, rel, got_bytes))
    if not ok:
        print("    got sha=%s bytes=%d  exp sha=%s bytes=%d" % (got_sha, got_bytes, exp_sha, exp_bytes))
print("TOTAL=%d MATCH=%d MISMATCH=%d" % (len(results), n_ok, len(results) - n_ok))
