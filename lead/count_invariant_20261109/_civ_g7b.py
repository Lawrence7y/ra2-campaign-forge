# -*- coding: utf-8 -*-
"""_civ_g7b.py — 复核员专攻「恒等掩盖维度缺失」的最强构造。

目标：构造一份输入，7 键 totals 一字未改、所有恒等式成立、M=E=0（merged 判别式双零），
但 P(set of path rows) != S(set of match rows)，且没有任何 SAMEDOC_LINK_EQ 维度。
即：两个计数轴被压成同一根的同时，集合已被换坏，而判别式看不见。
"""
import copy
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile

REPO = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "count_invariant_20261109"
SRC = REPO / "lead" / "r11_f2_fix_20261109" / "_f2_compare_out.json"
PY, FLAGS = sys.executable, ["-I", "-X", "utf8"]


def load(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


lib = load("_civ_lib", W / "_civ_lib.py")
ci = load("_ci_checks", W / "_ci_checks.py")
gate = load("_ci_gate", W / "_ci_gate.py")
BASE = json.loads(SRC.read_text(encoding="utf-8"))
TMP = pathlib.Path(tempfile.mkdtemp(prefix="_civ_g7b_"))

# 构造：取基线里一条 (path=A, match=True) 行与一条 (path=None, match=None) 行；
# 只互换 path 字段，match 一律不动。
# A 行：path=None, match=True  ⇒ 计入 match，不计入 path
# B 行：path=真值, match=None ⇒ 计入 path，不计入 match
# totals pp=9 pm=9 不变；M=E=0（A 行 tier 仍 T2N，不是 merged；B 行无 match）；
# 但 P 丢了 A 多了 B，S 不变 ⇒ P != S。
d = copy.deepcopy(BASE)
rows = [(i, k, b) for i, r in enumerate(d["results"])
        for k, b in enumerate(r["plus"]["bindings"])]
pr = [(i, k, b) for i, k, b in rows if b.get("path") and b.get("match") is True]
nr = [(i, k, b) for i, k, b in rows if not b.get("path") and b.get("match") is None]
iA, kA, bA = pr[0]
iB, kB, bB = nr[0]
oldpath = d["results"][iA]["plus"]["bindings"][kA]["path"]
d["results"][iA]["plus"]["bindings"][kA]["path"] = None
d["results"][iB]["plus"]["bindings"][kB]["path"] = oldpath
p = TMP / "G7b_path_only_swap.json"
p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

print("swapped: A=(%d,%d) path %r -> None ; B=(%d,%d) path None -> %r" %
      (iA, kA, oldpath, iB, kB, oldpath))
rec = lib.recompute(d["results"])
print("totals unchanged        =", d["totals"] == BASE["totals"])
print("recomputed==stored(7)   =", rec == d["totals"])
plus_rows = [(i, k, b) for i, r in enumerate(d["results"])
             for k, b in enumerate(r["plus"]["bindings"])]
P = {(i, k) for i, k, b in plus_rows if bool(b.get("path"))}
S = {(i, k) for i, k, b in plus_rows if b.get("match") is True}
M = sum(1 for _, _, b in plus_rows if not b.get("path") and b.get("match") is True)
E = sum(1 for _, _, b in plus_rows if b.get("tier") == "SAMEDOC_LINK_EQ")
print("P size=%d S size=%d P==S=%s  path\\match=%r match\\path=%r" %
      (len(P), len(S), P == S, sorted(P - S), sorted(S - P)))
print("M=%d E=%d merged_present(M>0&E>0&M==E)=%s" % (M, E, M > 0 and E > 0 and M == E))
print("has SAMEDOC_LINK_EQ tier =", E > 0)
print()
for label, exe, args in [("_ci_checks.py", W / "_ci_checks.py", [str(p)]),
                         ("_ci_gate.py", W / "_ci_gate.py", [str(p)]),
                         ("_civ_checks_cli.py", W / "_civ_checks_cli.py", [str(p)])]:
    r = subprocess.run([PY] + FLAGS + [str(exe)] + args, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    o = ((r.stdout or "") + (r.stderr or "")).splitlines()
    print("  %-20s rc=%d  %r" % (label, r.returncode,
          [l.strip() for l in o if l.strip().startswith("- ") or "ALERT" in l or "OK " in l]))
wv, wf = ci.evaluate(d)
gv = gate.gate(d)
iv, ifc = lib.evaluate(d)
print("  in-process: writer=%r gate=%r indep=%r" % (wv, gv, iv))
print("  writer facts M=%d E=%d set_equal=%s merged_present=%s" %
      (wf["M_match_no_path"], wf["E_merged_tier"], wf["set_equal"], wf["merged_present"]))
