# -*- coding: utf-8 -*-
# _lv_fp_core.py — 独立复核员指纹实算（只读，不写任何既有件）
import hashlib, os, sys

base = r"D:\Project\ra2-campaign-forge"
rels = [
    r"lead\PENDING_DECISIONS.md",
    r"lead\GOAL_THREE_TARGETS_20261018.md",
    r"lead\NEXT_STEPS_20261106.md",
    r"lead\nextstep_plan_20261106\NEXT_STEPS_20261106.md",
    r"lead\static_spec_n9_20261107\STATIC_COUNT_SPEC.md",
    r"lead\n9_erratum_20261108\N9_SPEC_ERRATUM.md",
    r"lead\d_o1o4_necessity_20261108\O1_O4_NECESSITY.md",
    r"lead\slowframe_r3_20261108\S604_GAP_RECHECK.md",
    r"lead\b2b_yi_supersede_20261108\YI_SUPERSEDE_JIA_BINDING.md",
    r"lead\r2_final_grade_20261108\R2_FINAL_GRADE.md",
    r"lead\matrix_binding_20261108\MATRIX_BINDING_FACTS.md",
]
for rel in rels:
    p = os.path.join(base, rel)
    if not os.path.exists(p):
        print("MISSING", rel)
        continue
    b = open(p, "rb").read()
    h = hashlib.sha256(b).hexdigest()
    t = b.decode("utf-8", errors="replace")
    n_split = len(t.split("\n"))          # 含末尾空段口径
    n_lines = len(t.splitlines())          # 不含末尾空段口径
    print("SHA256=%s BYTES=%d LINES_SPLITLINES=%d LINES_WITH_TAILBLANK=%d FILE=%s"
          % (h, len(b), n_lines, n_split, rel))

print("---- write-domain _la_ inventory ----")
wd = os.path.join(base, r"lead\ledger_appendix_20261108")
names = sorted(n for n in os.listdir(wd) if n.startswith("_la_"))
print("count(_la_*) =", len(names))
for n in names:
    b = open(os.path.join(wd, n), "rb").read()
    print("SHA256=%s BYTES=%d FILE=%s" % (hashlib.sha256(b).hexdigest(), len(b), n))
