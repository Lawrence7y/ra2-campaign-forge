# -*- coding: utf-8 -*-
# F2-d 报告撰写会话指纹核验（只读；python -I -X utf8 本脚本绝对路径运行）
import hashlib, pathlib, sys

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")

def fp(rel):
    p = ROOT / rel
    if not p.is_file():
        return ("MISSING", 0, "")
    b = p.read_bytes()
    return ("OK", len(b), hashlib.sha256(b).hexdigest())

FULL = [
    ("lead/r11_f2_fix_20261109/R11_F2_COVERAGE_FIX.md",
     "99ba9f979018df66f39a996859e24ed207b566b15f6bcdec7055b85a1f379435", 25282),
    ("lead/r11_f2_fix_20261109/_f2_r11plus.py",
     "83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75", 15723),
    ("lead/r11_f2_fix_20261109/_f2_repro_out.json",
     "3bc0ed8b26f90e235888ed1c386ee0f3179cdcc54bf9092b6ca167dda2ecfa72", 28386),
    ("lead/r11_f2_fix_20261109/_f2_compare_out.json",
     "148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1", 44958),
    ("lead/r11_f2_fix_20261109/_f2_context_probe_out.txt",
     "e48e15469c28508303c4eb2c733e44d0129191107a5700a7beeed36e7cc89580", 44054),
    ("lead/gate_fp7_20261108/_g7_predicates.py",
     "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    ("lead/gate_r9r12_20261109/GATE_R9R12_REGRESSION.md",
     "dc222c2409db9a63c1e2cd95b979069a16b5067585bd8a46d7a9d40657fe27c0", 37578),
    ("lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]

PREFIX5 = [
    ("lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md", "1209ca4c", 33431),
    ("lead/b2b_isolated_20261107/INTEGRATION_REPORT.md", "65463431", 24022),
    ("lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md", "9742f2cc", 15179),
    ("lead/bexec_n4_20261108/B_EXECUTION_SPEC.md", "be733335", 32183),
    ("lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md", "cb4f3011", 22136),
]

MISC = [
    ("lead/f2d_rootcause_20261109/_f2d_ROOTCAUSE.md",
     "d12efd856c0aebe5dc8a882cb7cbd486154c7bb8602028e83a6f3ef290668b05", 21424),
    ("lead/b2b_isolated_20261107/qc151_trip.isolated.py",
     "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    ("out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py",
     "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    ("lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md", "746b66d4", 28384),
]

bad = 0
print("== A. 编排方上游指纹九件（全哈希比对） ==")
for rel, exp, nb in FULL:
    st, n, h = fp(rel)
    ok = st == "OK" and n == nb and h == exp
    if not ok: bad += 1
    print("%s %s %d %s" % ("MATCH " if ok else "DRIFT ", rel, n, h))

print("== B. 10 条所在五证据件（前缀+字节比对） ==")
for rel, pref, nb in PREFIX5:
    st, n, h = fp(rel)
    ok = st == "OK" and n == nb and h.startswith(pref)
    if not ok: bad += 1
    print("%s %s %d %s" % ("MATCH " if ok else "DRIFT ", rel, n, h))

print("== C. 复核绑定对象/隔离副本/母本/r1 同名件 ==")
for rel, exp, nb in MISC:
    st, n, h = fp(rel)
    ok = st == "OK" and n == nb and h.startswith(exp)
    if not ok: bad += 1
    print("%s %s %d %s" % ("MATCH " if ok else "DRIFT ", rel, n, h))

print("== D. 编排方上下文勘误：两处 MISSINIG 路径探针 ==")
for rel in ["lead/b4_exec_20261106/_integ.md", "lead/n4_spec_20261106/_n4_SPEC.md"]:
    p = ROOT / rel
    st, n, h = fp(rel)
    ok = st == "MISSING"
    if not ok: bad += 1
    print("%s %s" % ("MISSING(预期) " if ok else "IN-盘(异常) ", rel))

print("== E. r1（3343cfbe…/26435）是否在盘：全 lead/ 同名件 + 同字节件 ==")
r1 = "3343cfbe467d38f442cd9e422e691d0123fc046938c4d242f57c629bd41d4125"
hits = []
for p in (ROOT / "lead").rglob("*"):
    if not p.is_file():
        continue
    try:
        sz = p.stat().st_size
    except OSError:
        continue
    if p.name == "A_RESIDUAL_REFERENCES.md" or sz == 26435:
        try:
            h = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:
            continue
        tag = "r1-FOUND" if h == r1 else "other"
        hits.append("%s %s %s" % (p.relative_to(ROOT), sz, h))
for line in sorted(hits):
    print(" ", line)
if not any("r1-FOUND" in x for x in hits):
    print("  r1 = 不在盘（无任何文件命中 3343cfbe…）")

print("== RESULT bad=%d ==" % bad)
