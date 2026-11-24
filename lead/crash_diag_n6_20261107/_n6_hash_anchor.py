# -*- coding: utf-8 -*-
"""N-6 指纹锚复算脚本（只读；零真机、零采样、零母本写入）。
用法：python -I -X utf8 _n6_hash_anchor.py
输出：stdout（同内容由调用方重定向到 _n6_hash_anchor_out.txt）。
本脚本只做 open(rb)+hashlib.sha256，不枚举全仓、不写任何被核对象。
"""
import hashlib

ITEMS = [
    # (标签, 绝对路径, 期望 sha256 或 None, 期望字节数或 None)
    ("NEXT_STEPS(上游)", "D:/Project/ra2-campaign-forge/lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
     "c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225),
    ("RULING_D24(上游)", "D:/Project/ra2-campaign-forge/lead/re_line_20261105/D24_RULING/RULING_D24.md",
     "56167a5e869540d7e14a7f13d29a2ed9d780d0c6352635e6e12b36cd633dcdf5", 15301),
    ("GOAL3T(上游)", "D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    ("A34_CRASH_FINAL(上游)", "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/a34_crash_final/A34_CRASH_FINAL.md",
     "c79a1988cb0ffcaad6e252507965f23cae4eaad878a32a44875c08498087833d", 46222),
    ("REPRO_ATTEMPT_RECEIPT(上游)", "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/goal2_dump_20261021/REPRO_ATTEMPT_RECEIPT.md",
     "12f96d2dc48a0f56610c82e1a35ccc2a494a4f73cbc4a1f9a4fc45730bfff1a0", 4860),
    ("R3_REVIEW(上游)", "D:/Project/ra2-campaign-forge/lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md",
     "96071dd9d58e30a54966a2a1e16f4af918c2f8dd5825363510e8ced8bc6a8fea", 24661),
    # 关键语料件（无上游期望值，登记现值）
    ("gamemd.exe[ra2youli]", "D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe", None, None),
    ("gamemd.exe[ra2bench]", "D:/Project/ra2-campaign-forge/ra2bench/gamemd.exe", None, None),
    ("ra2youli/except.txt(现势崩溃)", "D:/Project/ra2-campaign-forge/ra2youli/except.txt", None, None),
    ("qc135_objloc.py(现值,P1仪器)", "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc135_objloc/qc135_objloc.py", None, None),
    ("qc135_readings.json(现值,A5)", "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc163_a5_objloc_trip/qc135_readings.json", None, None),
    ("qc135_readings.json(evidence_preserved)", "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc163_a5_objloc_trip/evidence_preserved/outdir/qc135_readings.json", None, None),
    ("except.txt(evidence_preserved/carrier)", "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc163_a5_objloc_trip/evidence_preserved/carrier/except.txt", None, None),
]

QC205_ANCHOR = "1355deadf87b85df3f481cc338a2c3757501f1ac7d2509bb9b77115a4597e77e"
L3_CITED_READINGS = "9fd5ea8a"  # L3_DISAMBIG_ANALYSIS.md:4 引用版前缀


def main():
    for tag, path, exp, expn in ITEMS:
        with open(path, "rb") as f:
            b = f.read()
        h = hashlib.sha256(b).hexdigest()
        marks = []
        if exp is not None:
            marks.append("UPSTREAM-MATCH" if (h == exp and len(b) == expn) else "UPSTREAM-MISMATCH")
        if tag.startswith("qc135_objloc.py"):
            marks.append("EQ-QC205-ANCHOR" if h == QC205_ANCHOR else "NE-QC205-ANCHOR(漂移)")
        if h.startswith(L3_CITED_READINGS):
            marks.append("EQ-L3-CITED-9fd5ea8a")
        print("%s\n  path=%s\n  sha256=%s\n  bytes=%d %s"
              % (tag, path, h, len(b), ("[" + "; ".join(marks) + "]") if marks else ""))
    print("被核对象 SHA256 = 见上各行；字节数 = 见上各行（本行仅索引，不承载指纹）")


if __name__ == "__main__":
    main()
