# -*- coding: utf-8 -*-
"""_civ_final.py — 复核 §3(c)3 与 §3(d) 最强保证的可达边界。"""
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
FRESH = pathlib.Path(r"C:\Users\Administrator\AppData\Local\Temp\_ci_merged_r8prxhqj\merged_projection.json")
PY, FLAGS = sys.executable, ["-I", "-X", "utf8"]


def load(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


ci = load("_ci_checks", W / "_ci_checks.py")
gate = load("_ci_gate", W / "_ci_gate.py")
lib = load("_civ_lib", W / "_civ_lib.py")
BASE = json.loads(SRC.read_text(encoding="utf-8"))
PROJ = json.loads(FRESH.read_text(encoding="utf-8"))
TMP = pathlib.Path(tempfile.mkdtemp(prefix="_civ_final_"))

# === ③(c)3：构造 plus_match - plus_path == 1，但有 2 条 merged 标、且 merged_present=True ===
d = copy.deepcopy(BASE)
nonpath = [(i, k) for i, r in enumerate(d["results"])
           for k, b in enumerate(r["plus"]["bindings"])
           if b.get("path") is None and b.get("match") is None]
(a, b), (c, e), (f, g) = nonpath[0], nonpath[1], nonpath[2]
for (i, k) in ((a, b), (c, e)):
    d["results"][i]["plus"]["bindings"][k]["match"] = True
    d["results"][i]["plus"]["bindings"][k]["tier"] = "SAMEDOC_LINK_EQ"
    d["results"][i]["plus"]["bindings"][k]["members"] = [{"path": "x", "sha": "s", "bytes": 1},
                                                          {"path": "y", "sha": "s", "bytes": 1}]
    d["results"][i]["plus"]["bindings"][k]["decl_lines"] = [1]
# 第三条：给 path 但不给 match ⇒ +1 pp, +0 pm（抵消 1 个差值）
d["results"][f]["plus"]["bindings"][g]["path"] = "compensating.md"
d["results"][f]["plus"]["bindings"][g]["match"] = False
rows = [x for r in d["results"] for x in r["plus"]["bindings"]]
d["totals"]["plus_path"] = sum(1 for x in rows if x.get("path"))
d["totals"]["plus_match"] = sum(1 for x in rows if x.get("match") is True)
p = TMP / "diff1_with_2_merged.json"
p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
v, facts = lib.evaluate(d)
print("=== ③(c)3 差 1 但 2 条 merged ===")
print("plus_path=%r plus_match=%r diff=%d" %
      (d["totals"]["plus_path"], d["totals"]["plus_match"],
       d["totals"]["plus_match"] - d["totals"]["plus_path"]))
print("E(merged_tier)=%d  M=%d  merged_present=%s" % (facts["E"], facts["M"], facts["merged_present"]))
print("INDEPENDENT alerts =", v)
r = subprocess.run([PY] + FLAGS + [str(W / "_ci_gate.py"), str(p), "--expect-merged"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print("_ci_gate.py --expect-merged rc=%d %r" % (r.returncode,
      [l.strip() for l in ((r.stdout or "").splitlines()) if "OK " in l or "ALERT" in l or l.strip().startswith("- ")]))

# === ③(d) 「任何 merged 出现必触发至少一条报警」的作用域 ===
print()
print("=== ③(d) 最强保证的作用域 ===")
v1, f1 = ci.evaluate(PROJ)
v2 = gate.gate(PROJ, expect_merged=True)
v3 = gate.gate(PROJ, expect_merged=False)
print("真实 merged 投影：_ci_checks.py violations=%d %r" % (len(v1), v1))
print("真实 merged 投影：_ci_gate.py --expect-merged violations=%d %r" % (len(v2), v2))
print("真实 merged 投影：_ci_gate.py (baseline 态) violations=%d %r" % (len(v3), v3))
print("=> §3(d)「任何 merged 出现必触发至少一条报警」在 --expect-merged 态不成立（0 报警）")

# 畸形 merged 行（match=None、无 members）+ M==E 凑平
d2 = copy.deepcopy(BASE)
(ra, ka), (rb, kb) = nonpath[0], nonpath[1]
d2["results"][ra]["plus"]["bindings"][ka]["match"] = True
d2["results"][ra]["plus"]["bindings"][ka]["tier"] = "T2"
d2["results"][rb]["plus"]["bindings"][kb]["tier"] = "SAMEDOC_LINK_EQ"
rows2 = [x for r in d2["results"] for x in r["plus"]["bindings"]]
d2["totals"]["plus_path"] = sum(1 for x in rows2 if x.get("path"))
d2["totals"]["plus_match"] = sum(1 for x in rows2 if x.get("match") is True)
p2 = TMP / "malformed_merged.json"
p2.write_text(json.dumps(d2, ensure_ascii=False), encoding="utf-8")
wv, wf = ci.evaluate(d2)
gv = gate.gate(d2, expect_merged=True)
iv, ifc = lib.evaluate(d2)
print()
print("畸形 merged 行（match=None、无 members、M==E==1）：")
print("  merged-tier row =", [(i, k, {x: b.get(x) for x in ("path", "match", "members", "tier")})
                             for i, r in enumerate(d2["results"])
                             for k, b in enumerate(r["plus"]["bindings"])
                             if b.get("tier") == "SAMEDOC_LINK_EQ"])
print("  _ci_checks.py violations=%d %r" % (len(wv), wv))
print("  _ci_gate.py --expect-merged violations=%d %r" % (len(gv), gv))
print("  INDEPENDENT violations=%d %r" % (len(iv), iv))
print("=> §3(d) 全称量词（∀ merged 行形状合规）在 _ci_gate.py / §4(d) 可粘贴代码里完全缺失")
print("TEMP:", TMP)
