# _la_fpcheck.py — 入账核对员·GLM：被核对象指纹盘点（只读，不改任何被核对象）
# 运行：python -I -X utf8 D:\Project\ra2-campaign-forge\lead\ledger_appendix_20261108\_la_fpcheck.py
import hashlib
import os

FILES = [
    r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md",
    r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md",
    r"D:\Project\ra2-campaign-forge\lead\NEXT_STEPS_20261106.md",
    r"D:\Project\ra2-campaign-forge\lead\n9_erratum_20261108\N9_SPEC_ERRATUM.md",
    r"D:\Project\ra2-campaign-forge\lead\n9_erratum_20261108\_er_N9_205_P6_B0CD48_ERRATUM.md",
    r"D:\Project\ra2-campaign-forge\lead\static_spec_n9_20261107\STATIC_COUNT_SPEC.md",
    r"D:\Project\ra2-campaign-forge\lead\d_o1o4_necessity_20261108\O1_O4_NECESSITY.md",
    r"D:\Project\ra2-campaign-forge\lead\d_o1o4_necessity_20261108\_d14_O1O4_NECESSITY.md",
    r"D:\Project\ra2-campaign-forge\lead\slowframe_r3_20261108\S604_GAP_RECHECK.md",
    r"D:\Project\ra2-campaign-forge\lead\slowframe_r3_20261108\_r3_GAPDIFF_RECHECK.md",
    r"D:\Project\ra2-campaign-forge\lead\b2b_yi_supersede_20261108\YI_SUPERSEDE_JIA_BINDING.md",
    r"D:\Project\ra2-campaign-forge\lead\r2_final_grade_20261108\R2_FINAL_GRADE.md",
]

for f in FILES:
    if not os.path.exists(f):
        print("MISSING\t0\t0\t0\t" + f)
        continue
    with open(f, "rb") as fh:
        data = fh.read()
    digest = hashlib.sha256(data).hexdigest()
    text = data.decode("utf-8", errors="replace")
    n_split = len(text.splitlines())
    n_nl = text.count("\n")
    print(f"{digest}\t{len(data)}\tsplitlines={n_split}\tnewlines={n_nl}\t{f}")
