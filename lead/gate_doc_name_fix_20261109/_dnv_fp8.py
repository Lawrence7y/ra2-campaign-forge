# 独立复核员脚本 ①：八件上游指纹 + 被核主报告指纹，全部 hashlib 实算
# 只读；产出仅打印到 stdout（快照另写 _dnv_fp8_out.json）
import json, hashlib, pathlib

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
BASE = {
    "lead/gate_subject_id_20261109/GATE_SUBJECT_ID_FIX.md": ("302a45644359f14d4f420225ac56784579a658cb852a0b0df0ddde6532adf63c", 31692),
    "lead/gate_subject_id_20261109/_si_SUBJECT_ID_DEFECT.md": ("8c67dc3fc950baf16e4e39b650ca25210e24e3512307a09eaf30cc9cecd6f4dc", 23441),
    "lead/gate_subject_id_20261109/_si_fix_lib.py": ("54751e9a10bca4becfae3449d4a19155dc7744dff77a8a22d7d70d9a7fd70eee", 2850),
    "lead/gate_subject_id_20261109/_si_gatescan_out.json": ("c8024cb7e538dfbc3766acc08d231789b80d601d7cc4bba4e05ed89d8ff87d94", 611043),
    "lead/gate_subject_id_20261109/_si_wfscan_out.json": ("e326df6b4040dc9e5471f891c8db55d8ede1681434336de5e5626c43e2029f52", 180256),
    "lead/gate_subject_id_20261109/_si_exploit_out.txt": ("151f4f94b890403ba4785a7d570ad11abbe68a4aa12363967682729167e2c587", 5717),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
rows = []
for rel, (exp_sha, exp_n) in BASE.items():
    p = ROOT / rel
    if not p.is_file():
        rows.append({"file": rel, "sha256": "MISSING", "bytes": 0, "match": False, "expected": exp_sha})
        continue
    b = p.read_bytes()
    sha = hashlib.sha256(b).hexdigest()
    rows.append({"file": rel, "sha256": sha, "bytes": len(b),
                 "expected_sha256": exp_sha, "expected_bytes": exp_n,
                 "match": (sha == exp_sha and len(b) == exp_n)})

# 被核对象：设计回件主报告
rep = ROOT / "lead/gate_doc_name_fix_20261109/_dn_glm_final.md"
rb = rep.read_bytes() if rep.is_file() else b""
report = {"file": "lead/gate_doc_name_fix_20261109/_dn_glm_final.md",
          "sha256": hashlib.sha256(rb).hexdigest() if rb else "MISSING",
          "bytes": len(rb),
          "expected_sha256": "c977e3ca88f7963e751087811fc37409a7497d136b30a7686ff35b7160224d05",
          "expected_bytes": 31453}
report["match"] = (report["sha256"] == report["expected_sha256"] and report["bytes"] == report["expected_bytes"])

out = {"upstream": rows, "upstream_matches": sum(1 for r in rows if r["match"]), "upstream_total": len(rows),
       "reviewed_report": report}
pathlib.Path("D:/Project/ra2-campaign-forge/lead/gate_doc_name_fix_20261109/_dnv_fp8_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
