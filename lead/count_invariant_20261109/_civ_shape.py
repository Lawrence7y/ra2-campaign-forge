# -*- coding: utf-8 -*-
"""_civ_shape.py — 专查 §3(d) 判别式的全称量词在实现里有没有落地。

§3(d) 写：∀ b with tier=="SAMEDOC_LINK_EQ": b.path is None ∧ b.match is True
          ∧ "members" in b ∧ len>=2 ∧ 无单对象三键。
_ci_checks.py:143-149 的循环条件是
    (not b.get("path")) and b.get("match") is True and b.get("tier") == MERGED_TIER
即「只对同时满足 match is True 的行做形状检查」；若畸形 merged 行 match=None，
形状检查被跳过。而 M==E 等式又可被另一行凑平 ⇒ 整套 _ci_checks 零报警。
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
BASE = json.loads(SRC.read_text(encoding="utf-8"))
TMP = pathlib.Path(tempfile.mkdtemp(prefix="_civ_shape_"))

# 找两条 (path=None, match=None) 的行
cands = [(i, k) for i, r in enumerate(BASE["results"])
         for k, b in enumerate(r["plus"]["bindings"])
         if b.get("path") is None and b.get("match") is None]
print("candidate rows (path=None,match=None):", cands)
(ra, ka), (rb, kb) = cands[0], cands[1]
print("using A=(%d,%d) B=(%d,%d)" % (ra, ka, rb, kb))

d = copy.deepcopy(BASE)
# A: 制造 M=1（无 path 的 match=True，标成普通 T2，绝无 merged 语义）
d["results"][ra]["plus"]["bindings"][ka]["match"] = True
d["results"][ra]["plus"]["bindings"][ka]["tier"] = "T2"
# B: 制造 E=1（打了 merged 标，但 shape 全坏：match=None、无 members）
d["results"][rb]["plus"]["bindings"][kb]["tier"] = "SAMEDOC_LINK_EQ"
rec = lib.recompute(d["results"])
d["totals"]["plus_path"] = rec["plus_path"]
d["totals"]["plus_match"] = rec["plus_match"]
print("totals after =", d["totals"])
p = TMP / "shape_gap.json"
p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

plus_rows = [(i, k, b) for i, r in enumerate(d["results"])
             for k, b in enumerate(r["plus"]["bindings"])]
M = sum(1 for _, _, b in plus_rows if not b.get("path") and b.get("match") is True)
E = sum(1 for _, _, b in plus_rows if b.get("tier") == "SAMEDOC_LINK_EQ")
print("M=%d E=%d  => M==E 等式成立=%s" % (M, E, M == E))
print("merged-tier rows =",
      [(i, k, {x: b.get(x) for x in ("path", "match", "members", "tier")})
       for i, k, b in plus_rows if b.get("tier") == "SAMEDOC_LINK_EQ"])

wv, wf = ci.evaluate(d)
iv, ifc = lib.evaluate(d)
print()
print("WRITER _ci_checks violations =", wv)
print("WRITER facts M=%d E=%d merged_present=%s" %
      (wf["M_match_no_path"], wf["E_merged_tier"], wf["merged_present"]))
print("INDEPENDENT violations =", iv)
for label, exe in [("_ci_checks.py", W / "_ci_checks.py"),
                   ("_civ_checks_cli.py", W / "_civ_checks_cli.py")]:
    r = subprocess.run([PY] + FLAGS + [str(exe), str(p)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    o = ((r.stdout or "") + (r.stderr or "")).splitlines()
    print("CLI %-20s rc=%d %r" % (label, r.returncode,
          [l.strip() for l in o if l.strip().startswith("- ") or "ALERT" in l or "OK " in l]))
print("TEMP:", TMP)
