# -*- coding: utf-8 -*-
"""_civ_step34.py — 复核员独立验证第三步(b)(c)(d) 与第四步(c)(d)。

③(b) 逐条 diff baseline vs merged 投影，逐条算 (Δplus_path, Δplus_match) 并归类；
③(c) 计数差不能判 merged 的实证；③(d) 判别式两向；
④(c) 硬编码 9 的现有消费者能否发现（独立沙箱实跑）；
④(d) _ci_gate.py 三态实跑。
"""
import copy
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
from collections import Counter

REPO = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "count_invariant_20261109"
R11 = REPO / "lead" / "r11_f2_fix_20261109"
SRC = R11 / "_f2_compare_out.json"
FRESH = pathlib.Path(r"C:\Users\Administrator\AppData\Local\Temp\_ci_merged_r8prxhqj\merged_projection.json")
OLD = pathlib.Path(r"C:\Users\Administrator\AppData\Local\Temp\_ci_merged_dcdxi1lv\merged_projection.json")


def load(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


lib = load("_civ_lib", W / "_civ_lib.py")
ci = load("_ci_checks", W / "_ci_checks.py")
PY = sys.executable
FLAGS = ["-I", "-X", "utf8"]
base = json.loads(SRC.read_text(encoding="utf-8"))
proj = json.loads(FRESH.read_text(encoding="utf-8"))

print("=== ③(b) 独立逐条 diff：19 条绑定，逐条 (Δpp, Δpm) ===")
nb = [(i, k, b) for i, r in enumerate(base["results"]) for k, b in enumerate(r["plus"]["bindings"])]
np = [(i, k, b) for i, r in enumerate(proj["results"]) for k, b in enumerate(r["plus"]["bindings"])]
assert [(i, k) for i, k, _ in nb] == [(i, k) for i, k, _ in np], "编址不一致"


def pair(b):
    return (1 if b.get("path") else 0, 1 if b.get("match") is True else 0)


deltas = Counter()
changed = []
for (i, k, a), (_, _, b) in zip(nb, np):
    if a == b:
        continue
    d = (pair(b)[0] - pair(a)[0], pair(b)[1] - pair(a)[1])
    deltas[d] += 1
    changed.append((i, k, d, a, b))
print("changed_bindings =", len(changed), " changed_docs =",
      len({i for i, k, d, a, b in changed}))
print("DELTA histogram", dict(deltas))
print("TOTAL Δ(plus_path, plus_match) =",
      (sum(d[0] for _, _, d, _, _ in changed), sum(d[1] for _, _, d, _, _ in changed)))
print("base pp/pm =", (base["totals"]["plus_path"], base["totals"]["plus_match"]),
      " proj pp/pm =", (proj["totals"]["plus_path"], proj["totals"]["plus_match"]))
for i, k, d, a, b in changed:
    print("  (%2d,%d) Δ=%s  tier %r->%r  path %r->%r  match %r->%r  keys_added=%r" %
          (i, k, d, a.get("tier"), b.get("tier"),
           bool(a.get("path")), bool(b.get("path")), a.get("match"), b.get("match"),
           sorted(set(b) - set(a))))
merged_rows = [(i, k, b) for i, k, b in np
               if b.get("tier") == "SAMEDOC_LINK_EQ"]
print("MERGED-TIER rows in projection =", len(merged_rows))
for i, k, b in merged_rows:
    print("  MERGED ROW (%d,%d): file=%s" % (i, k, proj["results"][i]["file"]))
    print("    keys=%r" % sorted(b.keys()))
    print("    path=%r match=%r tier=%r members_n=%s decl_lines=%r" %
          (b.get("path"), b.get("match"), b.get("tier"),
           len(b.get("members", [])), b.get("decl_lines")))
    print("    has single-object keys:",
          {x: (x in b) for x in ("verified_path", "recomputed", "bytes")})
    print("    contribution to (pp,pm) =", pair(b))
    print("    is one of the 10 changed?", any(i == ci_ and k == ck for ci_, ck, _, _, _ in changed))
    print("    delta of that row =", [d for ci_, ck, d, _, _ in changed
                                      if ci_ == i and ck == k])
    print("    members sha equal:",
          len({m.get("sha") for m in b.get("members", [])}) == 1,
          [m.get("sha") for m in b.get("members", [])])
print("ALL Δ(0,+1) rows =", [(i, k) for i, k, d, a, b in changed if d == (0, 1)])
print("UNIQUE(Δ(+1,+1)) rows =", [(i, k) for i, k, d, a, b in changed if d == (1, 1)])
print("ZERO(Δ(0,0)) rows =", [(i, k) for i, k, d, a, b in changed if d == (0, 0)])

print()
print("=== ③(a) 对投影跑撰写员 checker 与复核员 checker ===")
wv, wf = ci.evaluate(proj)
print("WRITER _ci_checks violations=%d %r" % (len(wv), wv))
cv, cf = lib.evaluate(proj)
print("INDEPENDENT violations=%d %r" % (len(cv), cv))
print("facts writer M=%d E=%d merged_present=%s" %
      (wf["M_match_no_path"], wf["E_merged_tier"], wf["merged_present"]))
print("facts indep  M=%d E=%d merged_present=%s" %
      (cf["M"], cf["E"], cf["merged_present"]))

print()
print("=== ④(d) _ci_gate.py 三态实跑 ===")
for args, label in [(["--selftest"], "selftest"),
                    ([str(SRC)], "baseline"),
                    ([str(FRESH), "--expect-merged"], "merged --expect-merged")]:
    p = subprocess.run([PY] + FLAGS + [str(W / "_ci_gate.py")] + args,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("  %-24s rc=%d" % (label, p.returncode))
    for line in ((p.stdout or "") + (p.stderr or "")).splitlines():
        print("     ", line.strip())

print()
print("=== ④(c) 独立沙箱：硬编码 totals.plus_match=9 到 merged 投影 ===")
tmp = pathlib.Path(tempfile.mkdtemp(prefix="_civ_hard_"))
sbox = tmp / "B_hard9"
sbox.mkdir(parents=True)
doc = copy.deepcopy(proj)
doc["totals"]["plus_match"] = 9
(sbox / "_f2_compare_out.json").write_text(
    json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
shutil.copy2(R11 / "_f2_repro_out.json", sbox / "_f2_repro_out.json")
consumers = ["_f2w_checks.py", "_f2w_pass.py", "_f2w_extract.py", "_f2w_final.py"]
for c in consumers:
    t = (R11 / c).read_text(encoding="utf-8")
    t = t.replace(str(R11), str(sbox))
    t = t.replace(str(R11).replace("\\", "\\\\"), str(sbox).replace("\\", "\\\\"))
    (sbox / c).write_text(t, encoding="utf-8")
for c in consumers:
    p = subprocess.run([PY] + FLAGS + [str(sbox / c)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    print("  %-18s rc=%d output_has_totals=%s notable=%r" %
          (c, p.returncode, "totals" in out,
           [l.strip() for l in out.splitlines()
            if "PASS:" in l or "一致条数" in l or "rows=" in l][:2]))
for name, script, args in [("WRITER _ci_checks", W / "_ci_checks.py", [str(sbox / "_f2_compare_out.json")]),
                          ("INDEPENDENT _civ_checks", W / "_civ_checks_cli.py", [str(sbox / "_f2_compare_out.json")])]:
    p = subprocess.run([PY] + FLAGS + [str(script)] + args, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    out = ((p.stdout or "") + (p.stderr or "")).splitlines()
    print("  %-24s rc=%d" % (name, p.returncode))
    for l in out:
        if l.strip().startswith("-") or "ALERT" in l or "OK " in l or "violations" in l:
            print("     ", l.strip())

print()
print("=== 边界：三个指纹锁对原件实跑（CASE A 情形） ===")
for f in ["lead/f2d_rootcause_20261109/_f2d_fpcheck.py",
          "lead/f2d_rootcause_20261109/_f2dw_fpcheck.py",
          "lead/f2d_rootcause_20261109/_f2dv_fpcheck.py"]:
    p = subprocess.run([PY] + FLAGS + [str(REPO / f)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    out = ((p.stdout or "") + (p.stderr or "")).splitlines()
    hit = [l for l in out if "_f2_compare_out.json" in l and
           ("MATCH" in l or "DRIFT" in l or "MISMATCH" in l)]
    print("  %-20s rc=%d line=%r" % (pathlib.Path(f).name, p.returncode, hit[:1]))
print("TEMP:", tmp)
