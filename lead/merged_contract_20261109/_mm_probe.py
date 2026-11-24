# -*- coding: utf-8 -*-
"""_mm_probe.py — 本会话独立复核探针（只读；标准库 hashlib/importlib/re/json/os）。
复核【复核】verdict=partial 指出的 3 处清单问题 + S4 误判，以及 ④ totals 现状。
零真机、零采样代码；只装载写域候选副本与只读原件做表达式级对跑，不写任何既有件。
"""
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "merged_contract_20261109"
R11 = REPO / "lead" / "r11_f2_fix_20261109"
R33 = REPO / "lead" / "r33e_merge_20261109"
G7 = REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

print("== §S4 真实路径对跑（_f2_selftest.py:105-111 原用例，orig vs candidate）==")
g7 = load(G7, "_mm_g7")
orig = load(R11 / "_f2_r11plus.py", "_mm_orig")
cand = load(W / "_mk_r11plus_candidate.py", "_mm_cand")
plus_sha, plus_bytes = (lambda b: (hashlib.sha256(b).hexdigest(), len(b)))(
    (R11 / "_f2_r11plus.py").read_bytes())
anchor = "lead/r11_f2_fix_20261109/_f2_r11plus.py"
t = "被核对象 SHA256 = %s，字节数 = %d（见 `lead/r11_f2_fix_20261109/_f2_repro.py` 与 `%s`）" % (
    plus_sha, plus_bytes, anchor)
for tag, mod in [("ORIG", orig), ("CAND", cand)]:
    n_p, n_w, nb = mod.r11_scan_plus(t, REPO / "lead", root=REPO)
    s4 = (not n_p and nb[0]["match"] is True
          and str(nb[0].get("verified_path", "")).endswith("_f2_r11plus.py"))
    print("  %s tier=%r match=%r verified=%r problems_n=%d warnings_n=%d S4_assert=%s"
          % (tag, nb[0].get("tier"), nb[0].get("match"),
             nb[0].get("verified_path"), len(n_p), len(n_w), s4))
    # 是否走到 :303-305 的 else（tier=None 且 R3-3b warning）
    r33_warn = any("需人工锚定" in x for x in n_w)
    print("  %s reached_303_305_else=%s" % (tag, r33_warn))
print("  [复核口径] C8 是把单条 merged rec M 手工喂进 :110 的表达式，不是 S4 路径；"
      " _mk_project.py:105-106 实读为 M.get('verified_path','').endswith(...)")

print()
print("== §FP r11plus 指纹锁 19 件分类（全仓 --include='*.py' 实 grep 结果）==")
locks = {
    "lead/equiv_class_20261109/_eqv_fp.py": "PROD/AUDIT",
    "lead/f2d_rootcause_20261109/_f2d_fpcheck.py": "PROD/AUDIT(同时锁 compare_out)",
    "lead/f2d_rootcause_20261109/_f2dv_fpcheck.py": "PROD/AUDIT(同时锁 compare_out)",
    "lead/f2d_rootcause_20261109/_f2dw_fpcheck.py": "PROD/AUDIT(同时锁 compare_out)",
    "lead/gate_doc_name_fix_20261109/_dnv_hardened/dwfrun-5ad91c91-308a.py": "SANDBOX/HARDENED",
    "lead/gate_doc_name_fix_20261109/_dnv_hardened/dwfrun-cd88a9f5-f5aa.py": "SANDBOX/HARDENED",
    "lead/gate_doc_name_fix_20261109/_dnv_sandbox36/f2d_rootcause_20261109/_dnv_gate.py": "SANDBOX",
    "lead/gate_doc_name_fix_20261109/_dnv_sandbox36/samedoc_link_20261109/_dnv_gate.py": "SANDBOX",
    "lead/gate_doc_name_fix_20261109/_dnw_sandbox/f2d_rootcause_20261109/_dnw_gate.py": "SANDBOX",
    "lead/gate_doc_name_fix_20261109/_dnw_sandbox/samedoc_link_20261109/_dnw_gate.py": "SANDBOX",
    "lead/merged_consumer_audit_20261109/_mcv_fp.py": "PRIOR_ROUND_AUDIT",
    "lead/merged_contract_20261109/_mk_probe.py": "WRITE_DOMAIN_PROBE",
    "lead/merged_contract_20261109/_mkv_consumers.py": "WRITE_DOMAIN_PROBE",
    "lead/merged_contract_20261109/_mkv_fp.py": "WRITE_DOMAIN_PROBE",
    "lead/merged_contract_20261109/_mm_fp.py": "WRITE_DOMAIN_PROBE(this session)",
    "lead/r11_f2_fix_20261109/_f2v_fp.py": "PROD/AUDIT",
    "lead/r33e_merge_20261109/_re_fp_check.py": "PROD/AUDIT",
    "lead/r33e_merge_20261109/_rev_core.py": "PROD/AUDIT",
    "lead/samedoc_link_20261109/_slw_hashes.py": "PROD/AUDIT",
}
prod = [k for k, v in locks.items() if v.startswith("PROD")]
print("  enumerate=19  PROD/AUDIT=%d  (其余=沙箱/上轮审计/写域探针)" % len(prod))
for k in prod:
    print("    ", k)
print("  _f2_selftest.py 用 sha_of(F2PLUS) 动态取值，不硬编码 → 不受 ③ 指纹重算影响"
      "（_f2_selftest.py:60 实读）")

print()
print("== §OW _ow_raw_hits.json fileMeta 四件快照（实读）==")
ow = json.loads((REPO / "lead" / "oldwording_sweep_20261109" / "_ow_raw_hits.json").read_text(encoding="utf-8"))
fm = ow.get("fileMeta", {})
for key in ("r11_f2_fix_20261109/_f2_compare_out.json",
            "r11_f2_fix_20261109/_f2_compare.py",
            "r11_f2_fix_20261109/_f2_r11plus.py",
            "r11_f2_fix_20261109/_f2v_run_out.json"):
    v = fm.get(key)
    print("  %s -> %r" % (key, ({"sha256": v.get("sha256"), "bytes": v.get("bytes")} if isinstance(v, dict) else v)))

print()
print("== §CMP ④ totals 现状（由 results[] 重算 7/7）+ results schema ==")
d = json.loads((R11 / "_f2_compare_out.json").read_text(encoding="utf-8"))
res = d["results"]
calc = {
    "bindings": sum(len(r["orig"]["bindings"]) for r in res),
    "orig_path": sum(1 for r in res for b in r["orig"]["bindings"] if b["path"]),
    "plus_path": sum(1 for r in res for b in r["plus"]["bindings"] if b.get("path")),
    "orig_match": sum(1 for r in res for b in r["orig"]["bindings"] if b["match"] is True),
    "plus_match": sum(1 for r in res for b in r["plus"]["bindings"] if b.get("match") is True),
    "orig_problems": sum(len(r["orig"]["problems"]) for r in res),
    "plus_problems": sum(len(r["plus"]["problems"]) for r in res),
}
print("  stored    =", json.dumps(d["totals"], ensure_ascii=False, sort_keys=True))
print("  recomputed=", json.dumps(calc, ensure_ascii=False, sort_keys=True))
print("  EQUALS    =", calc == d["totals"])
pp = [(r["file"], i) for r in res for i, b in enumerate(r["plus"]["bindings"]) if b.get("path")]
pm = [(r["file"], i) for r in res for i, b in enumerate(r["plus"]["bindings"]) if b.get("match") is True]
print("  plus_path_set == plus_match_set :", set(pp) == set(pm))
print("  plus_path tier分布 =", sorted({str(b.get("tier")) for r in res for b in r["plus"]["bindings"] if b.get("path")}))
print("  result_keys =", sorted(res[0].keys()))
print("  plus_keys   =", sorted(res[0]["plus"].keys()))
allkeys = sorted({k for r in res for b in r["plus"]["bindings"] for k in b})
print("  plus.bindings 全量键集 =", allkeys)
print("  含 merged 字段 =", {k: any(k in b for r in res for b in r["plus"]["bindings"])
                          for k in ("members", "decl_lines", "samedoc_link")})

print()
print("== §JSONREAD 4 个 JSON 读者 totals/results 字面 ==")
for name in ("_f2w_checks.py", "_f2w_extract.py", "_f2w_pass.py", "_f2w_final.py"):
    s = (R11 / name).read_text(encoding="utf-8")
    print("  %-20s totals_lit=%s d_results=%s" % (
        name, "totals" in s, '["results"]' in s or "['results']" in s))

print()
print("== §RUN 第二件带 totals 的机读件 ==")
r2 = json.loads((R11 / "_f2v_run_out.json").read_text(encoding="utf-8"))
print("  top_keys =", sorted(r2.keys()))
print("  totals   =", json.dumps(r2["totals"], ensure_ascii=False, sort_keys=True))

print()
print("== §PROB _re_linked.py problems 写入语句（grep 结构）==")
s = (R33 / "_re_linked.py").read_text(encoding="utf-8")
hits = [ln for ln, line in enumerate(s.splitlines(), 1)
        if re.search(r'problems\.(append|extend)|\["problems"\]\s*=', line)]
print("  write-statements count =", len(hits), hits)
print("  :177 init =", s.splitlines()[176].strip())
print("  :330 exit =", s.splitlines()[329].strip())

print()
print("== §END ==")
