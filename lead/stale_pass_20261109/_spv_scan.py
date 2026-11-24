"""独立核验：两台账独立扫描 + 报告关键字符串真实行号定位。
不采信被核报告的任何计数。"""
import os, re, hashlib

ROOT = "D:/Project/ra2-campaign-forge"
W = ROOT + "/lead/stale_pass_20261109/"
FILES = {
 "PENDING": "lead/PENDING_DECISIONS.md",
 "GOAL": "lead/GOAL_THREE_TARGETS_20261018.md",
 "FIX": "lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md",
 "R27": "lead/d27_ruling_20261106/RULING_D27.md",
 "R28": "lead/d28_ruling_20261106/RULING_D28.md",
 "R29": "lead/d29_ruling_20261106/RULING_D29.md",
 "R30": "lead/d30_ruling_20261106/RULING_D30.md",
 "C27": "lead/d27_ruling_20261106/check_d27.py",
 "C28": "lead/d28_ruling_20261106/check_d28.py",
 "C29": "lead/d29_ruling_20261106/check_d29.py",
 "C30": "lead/d30_ruling_20261106/check_d30.py",
 "SCAN": "lead/refsync_scope_20261109/_rs_carrier_scan.py",
 "MEA": "lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md",
 "CMI": "lead/check_masking_20261109/CHECK_MASKING_INJECT.md",
}
L = {}
for k, p in FILES.items():
    L[k] = open(os.path.join(ROOT, p), "rb").read().decode("utf-8", "replace").split("\n")

print("=== ② 独立扫两台账：四件 gate 名 + scanner 名 + 门禁 exit=0 句式 ===")
names = ["check_d27", "check_d28", "check_d29", "check_d30", "check_d26", "check_d25",
         "_rs_carrier_scan", "carrier_scan", "SELF_TEST", "REFSYNC_SCOPE_FIX",
         "验证通过", "机械检查通过", "逐项通过"]
for k in ("PENDING", "GOAL"):
    print(f"-- {k} lines={len(L[k])} --")
    for n in names:
        hits = [i+1 for i, s in enumerate(L[k]) if n in s]
        print(f"   {n!r:24s} count={len(hits):4d} lines={hits[:30]}")
    # 显式「门禁 ... exit=0」句式
    gate = [(i+1, s.strip()[:110]) for i, s in enumerate(L[k])
            if "门禁" in s and re.search(r"exit\s*=\s*0", s, re.I)]
    print(f"   GATE_RUN(门禁+exit=0) count={len(gate)}")
    for n, s in gate:
        print(f"      L{n}: {s}")
    e0 = [i+1 for i, s in enumerate(L[k]) if re.search(r"exit\s*=\s*0", s, re.I)]
    pas = [i+1 for i, s in enumerate(L[k]) if re.search(r"\bPASS\b", s)]
    print(f"   exit0_lines={len(e0)} PASS_token_lines={len(pas)}")

print()
print("=== ② 关键断言的 file:line 真实性（逐字回读） ===")
CHECKS = [
 ("PENDING", 92, "check_d30.py 实跑 exit=0"),
 ("PENDING", 105, "check_d29.py 实跑 exit=0"),
 ("PENDING", 117, "check_d28.py 实跑 exit=0"),
 ("PENDING", 129, "check_d27.py 实跑 exit=0"),
 ("PENDING", 101, "RULING_D29.md:6,:20,:28,:47  <- 报告§2(c)误写 RULING_D30.md"),
 ("PENDING", 113, "RULING_D28.md:30,:32,:34,:36"),
 ("PENDING", 125, "RULING_D27.md:12,:28,:32,:42,:48"),
 ("FIX", 251, "627 ; carrier occurrences = 80 ; distinct files = 19"),
 ("FIX", 251, "SELF_TEST = PASS"),
 ("FIX", 252, "SELF_TEST = PASS"),
 ("FIX", 253, "SELF_TEST = PASS"),
 ("FIX", 254, "脚本不硬编码结论"),
 ("FIX", 260, "classify_line"),
 ("R27", 3, "本阶段未重跑统计、原探针、合成反例或门禁"),
 ("R27", 58, "不得签为本阶段执行通过"),
 ("R27", 69, "不背书本阶段未执行的门禁"),
 ("R27", 77, "未运行check_stall_def.py或其他门禁"),
 ("R29", 67, "不是本撰写阶段门禁通过证明"),
 ("R29", 71, "不记通过"),
 ("R30", 76, "不把原探针、check_feasibility.py或原门禁计为通过"),
 ("R30", 62, "未改门禁"),
 ("C27", 84, '("外推", "卡顿不存在")'),
 ("C29", 76, '("互斥", "前提")'),
 ("C30", 76, '("93.98", "误报率")'),
 ("C28", 90, '("历史数字", "1681")'),
 ("SCAN", 165, "min("),
 ("SCAN", 229, "any(n in txt"),
 ("SCAN", 343, "ok &= good"),
 ("SCAN", 346, "SELF_TEST = %s"),
]
for k, n, needle in CHECKS:
    s = L[k][n-1] if 1 <= n <= len(L[k]) else "<OOR>"
    print(f"   {k}:{n:<5d} expect={needle!r} -> {'HIT ' if needle in s else 'MISS'}  actual={s.strip()[:150]}")

print()
print("=== ② RULING_D29.md 中 pureLogicalCounterexampleMs / _d29_facts.py 的真实行号 ===")
for term in ["pureLogicalCounterexampleMs", "_d29_facts.py", "退出码", "corpus"]:
    hits = [(i+1, s.strip()[:140]) for i, s in enumerate(L["R29"]) if term in s]
    print(f"   R29 {term!r}: {hits}")
for term in ["_d30_facts.py", "corpus", "All numeric assertions passed"]:
    hits = [(i+1, s.strip()[:140]) for i, s in enumerate(L["R30"]) if term in s]
    print(f"   R30 {term!r}: {hits}")
for term in ["_d27_facts_out.txt", "71", "本阶段未重算"]:
    hits = [(i+1, s.strip()[:140]) for i, s in enumerate(L["R27"]) if term in s]
    print(f"   R27 {term!r}: {hits[:10]}  (count={len(hits)})")

print()
print("=== ② 独立实算 RULING_D27.md 引用数（gate 用 REFERENCE，核报告称 71） ===")
r27 = "\n".join(L["R27"])
# check_d27.py 的 REFERENCE
c27 = "\n".join(L["C27"])
m = re.search(r"REFERENCE\s*=\s*re\.compile\((.+?)(?:\,\s*re\.)", c27, re.S)
print("   check_d27.py REFERENCE def line:", [i+1 for i,s in enumerate(L["C27"]) if "REFERENCE" in s])
for i,s in enumerate(L["C27"]):
    if "REFERENCE" in s:
        print(f"      L{i+1}: {s.strip()[:200]}")
for patname, pat in [("gate_like_A", r"[A-Za-z0-9_./-]+\.(?:md|py|json):\d+"),
                     ("gate_like_B", r"lead/[A-Za-z0-9_./-]+:\d+")]:
    print(f"   {patname} count = {len(re.findall(pat, r27))}")
