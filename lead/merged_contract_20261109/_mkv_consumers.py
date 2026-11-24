# -*- coding: utf-8 -*-
"""独立复核⑤：全仓 grep 消费者（totals / plus_path / plus_match / 机读件 / 直调 plus）。
用 git ls-files 枚举（有界，含 tracked；另补 untracked 的 lead/ 子树），逐文件只读文本。
不做任何动态导入/执行；不写既有件。"""
import json
import os
import re
import subprocess
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
PAT = {
    "totals_lit": re.compile(r"\btotals\b"),
    "d_totals": re.compile(r"""\[["']totals["']\]|\.get\(["']totals["']"""),
    "d_results": re.compile(r"""\[["']results["']\]|\.get\(["']results["']"""),
    "plus_path": re.compile(r"\bplus_path\b"),
    "plus_match": re.compile(r"\bplus_match\b"),
    "plus_collected": re.compile(r"\bplus_collected\b"),
    "cmp_json": re.compile(r"_f2_compare_out\.json"),
    "run_json": re.compile(r"_f2v_run_out\.json"),
    "r11plus_call": re.compile(r"r11_scan_plus\s*\("),
    "g7_call": re.compile(r"\br11_scan\s*\("),
    "sha_cmp": re.compile(r"148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1"),
    "sha_plus": re.compile(r"83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75"),
}

SKIP_SUBSTR = ("/.git/", "/__pycache__/", "/node_modules/", "/_dnv_sandbox36/",
               "/_dnw_sandbox/", "/.tmp/", "/GLM/", "/Qwen/")

def enum_files():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True).stdout
    rels = [x.decode("utf-8", "replace") for x in out.split(b"\0") if x]
    # untracked under lead/ only (bounded)
    oth = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "-z", "lead/"],
                         cwd=ROOT, capture_output=True).stdout
    rels += [x.decode("utf-8", "replace") for x in oth.split(b"\0") if x]
    seen = set()
    for r in rels:
        r = r.replace("\\", "/")
        if r in seen:
            continue
        seen.add(r)
        if any(s in "/" + r for s in SKIP_SUBSTR):
            continue
        if not r.endswith((".py", ".md", ".txt", ".json")):
            continue
        p = os.path.join(ROOT, r.replace("/", os.sep))
        if os.path.isfile(p):
            yield r, p

FILES = list(enum_files())
PYS = [(r, p) for r, p in FILES if r.endswith(".py")]
print("ENUM_FILES=%d  PY=%d  MD/TXT/JSON=%d" % (len(FILES), len(PYS), len(FILES) - len(PYS)))
print("(skipped: .git/__pycache__/node_modules/_dnv_sandbox36/_dnw_sandbox/.tmp/GLM/Qwen)")
print()

def read(p):
    try:
        return open(p, "r", encoding="utf-8", errors="replace").read()
    except Exception as e:
        return ""

texts = {}
for r, p in FILES:
    texts[r] = read(p)

print("=== A) 全仓 .py 读 totals 下标/get（排除别件同名键，逐行列） ===")
for r, p in sorted(PYS):
    hits = [(i + 1, l.strip()) for i, l in enumerate(texts[r].splitlines())
            if PAT["d_totals"].search(l)]
    if hits:
        print("  %s" % r)
        for n, l in hits:
            print("      %d | %s" % (n, l[:170]))
print()
print("=== B) 全仓 .py 出现 plus_path / plus_match / plus_collected（按文件聚合） ===")
for r, p in sorted(PYS):
    hits = [(i + 1, l.strip()) for i, l in enumerate(texts[r].splitlines())
            if PAT["plus_path"].search(l) or PAT["plus_match"].search(l)
            or PAT["plus_collected"].search(l)]
    if hits:
        tag = ("WRITE_DOMAIN" if r.startswith("lead/merged_contract_20261109/") else
               "PRIOR_ROUND" if ("merged_safety" in r or "merged_consumer_audit" in r) else
               "R11_PROD" if r.startswith("lead/r11_f2_fix_20261109/") else "OTHER")
        print("  [%-13s] %s  (%d)" % (tag, r, len(hits)))
        for n, l in hits[:5]:
            print("      %d | %s" % (n, l[:170]))
print()
print("=== C) 4 个 JSON 读者：totals 字面 / d['totals'] / d['results'] ===")
for name in ("_f2w_checks.py", "_f2w_extract.py", "_f2w_pass.py", "_f2w_final.py"):
    r = "lead/r11_f2_fix_20261109/" + name
    t = texts.get(r, "")
    print("    %-20s totals_lit=%-5s d_totals=%-5s d_results=%-5s" % (
        name, bool(PAT["totals_lit"].search(t)), bool(PAT["d_totals"].search(t)),
        bool(PAT["d_results"].search(t))))
print()
print("=== D) 按名引用两件机读件的 .py（读者/写者/指纹锁） ===")
for label, key in (("COMPARE_JSON", "cmp_json"), ("RUN_JSON", "run_json")):
    print(" --", label)
    for r, p in sorted(FILES):
        if r.endswith(".py") and PAT[key].search(texts[r]):
            print("    %s" % r)
print()
print("=== E) 直调 r11_scan_plus( 的 .py（排除 def 与字符串探针，按文件计） ===")
for r, p in sorted(PYS):
    t = texts[r]
    n = len(PAT["r11plus_call"].findall(t))
    if n:
        print("    calls=%-3d %s" % (n, r))
print()
print("=== F) 硬编码指纹的 .py（compare_out sha / r11plus sha） ===")
for key in ("sha_cmp", "sha_plus"):
    print(" --", key)
    for r, p in sorted(PYS):
        if PAT[key].search(texts[r]):
            print("    %s" % r)
print()
print("=== G) 两件带 totals 的机读件真实结构 ===")
for rel in ("lead/r11_f2_fix_20261109/_f2_compare_out.json",
            "lead/r11_f2_fix_20261109/_f2v_run_out.json"):
    d = json.loads(open(os.path.join(ROOT, rel.replace("/", os.sep)), "r", encoding="utf-8").read())
    print("    %s" % rel)
    print("      top_keys  =", sorted(d.keys()))
    print("      totals    =", json.dumps(d["totals"], ensure_ascii=False, sort_keys=True))
    print("      results_n =", len(d.get("results", [])))
print()
print("=== H) 由 results[] 独立重算 compare totals ===")
d = json.loads(open(os.path.join(ROOT, "lead", "r11_f2_fix_20261109", "_f2_compare_out.json"),
                    "r", encoding="utf-8").read())
R = d["results"]
calc = {
    "bindings": sum(len(x["orig"]["bindings"]) for x in R),
    "orig_path": sum(1 for x in R for b in x["orig"]["bindings"] if b["path"]),
    "plus_path": sum(1 for x in R for b in x["plus"]["bindings"] if b.get("path")),
    "orig_match": sum(1 for x in R for b in x["orig"]["bindings"] if b["match"] is True),
    "plus_match": sum(1 for x in R for b in x["plus"]["bindings"] if b.get("match") is True),
    "orig_problems": sum(len(x["orig"]["problems"]) for x in R),
    "plus_problems": sum(len(x["plus"]["problems"]) for x in R),
}
print("  stored    =", json.dumps(d["totals"], ensure_ascii=False, sort_keys=True))
print("  recomputed=", json.dumps(calc, ensure_ascii=False, sort_keys=True))
print("  EQUALS    =", calc == d["totals"])
pp = [(i, j) for i, x in enumerate(R) for j, b in enumerate(x["plus"]["bindings"]) if b.get("path")]
mm = [(i, j) for i, x in enumerate(R) for j, b in enumerate(x["plus"]["bindings"]) if b.get("match") is True]
print("  plus_path_set == plus_match_set :", set(pp) == set(mm))
print("  plus_path tier分布 =", sorted({str(R[i]["plus"]["bindings"][j].get("tier")) for i, j in pp}))
print("  plus_match tier分布 =", sorted({str(R[i]["plus"]["bindings"][j].get("tier")) for i, j in mm}))
print()
print("=== END ===")
