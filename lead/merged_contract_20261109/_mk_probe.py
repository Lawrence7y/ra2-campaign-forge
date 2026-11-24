# -*- coding: utf-8 -*-
"""_mk_probe.py — 接入合并契约 / 机读件计数口径方案的可复核探针（只读）。

零真机、零采样代码；只 import 标准库；不改任何既有件；输出只到 stdout
（调用方重定向到本写域 _mk_probe_out.txt）。运行：
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/merged_contract_20261109/_mk_probe.py"
"""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
R11 = REPO / "lead" / "r11_f2_fix_20261109"
REL = REPO / "lead" / "r33e_merge_20261109"


def say(*a):
    print(*a)


def sha(path):
    b = Path(path).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


# ---------- 1 指纹 ----------
say("== 1 编排方指纹独立复核（hashlib）==")
FILES = [
    "lead/r11_f2_fix_20261109/_f2_r11plus.py",
    "lead/r11_f2_fix_20261109/_f2_compare.py",
    "lead/r11_f2_fix_20261109/_f2_compare_out.json",
    "lead/r11_f2_fix_20261109/_f2w_checks.py",
    "lead/r11_f2_fix_20261109/_f2w_extract.py",
    "lead/r11_f2_fix_20261109/_f2_selftest.py",
    "lead/r33e_merge_20261109/_re_linked.py",
    "lead/merged_consumer_audit_20261109/_mc_AUDIT.md",
    "lead/merged_safety_20261109/_ms_DESIGN.md",
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
]
EXPECT = {
    "lead/r11_f2_fix_20261109/_f2_r11plus.py": ("83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75", 15723),
    "lead/r11_f2_fix_20261109/_f2_compare.py": ("12e55acf42441aca846986a2447abffef77d774ee694cedf56a012c1c8907106", 4821),
    "lead/r11_f2_fix_20261109/_f2_compare_out.json": ("148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1", 44958),
    "lead/r11_f2_fix_20261109/_f2w_checks.py": ("23c5eebb77b43e9e187be6b4736fe1f0b3f5d8eb7f46a9ee2f8af1bbbce53514", 2189),
    "lead/r11_f2_fix_20261109/_f2w_extract.py": ("1eb22164c78330e825d053f665934e9ef1e4eba14e2b101c884de68a91aad701", 1564),
    "lead/r11_f2_fix_20261109/_f2_selftest.py": ("625704697e412c30a278c616cf8be594b8b870a2734df2219aa0607aa74a19bd", 8579),
    "lead/r33e_merge_20261109/_re_linked.py": ("7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52", 19481),
    "lead/merged_consumer_audit_20261109/_mc_AUDIT.md": ("8b0be4a59bd3e88ffd908a234e9c8382a724478d93409fddf3814d5bb5aa3367", 33762),
    "lead/merged_safety_20261109/_ms_DESIGN.md": ("bc5eb5d0d13e1fbe8a67451141476c7f077ec49e0d8e9a6bbab34bc569110c44", 34299),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
all_ok = True
for rel in FILES:
    h, n = sha(REPO / rel)
    ok = (h, n) == EXPECT[rel]
    all_ok = all_ok and ok
    say("  %s %s %d %s" % ("MATCH" if ok else "DRIFT", h, n, rel))
say("  ALL_ELEVEN_MATCH =", all_ok)

# ---------- 2 接入点原文与 link 家族计数 ----------
say()
say("== 2 接入点 _f2_r11plus.py:298-306 逐字 ==")
rp = R11 / "_f2_r11plus.py"
src = rp.read_text(encoding="utf-8")
rlines = src.splitlines()
for n in range(298, 307):
    say("%3d | %s" % (n, rlines[n - 1]))
say()
say("== 3 link 家族字面计数（整文件）==")
for tok in ["link_triple", "_re_linked", "samedoc", "verified_path", "recomputed"]:
    say("  %-16s = %d" % (tok, src.count(tok)))
pat = re.compile(r"link_triple|_re_linked|samedoc|\bsl_link\b|import .*link|\blink\(")
say("  _mc_AUDIT.md:170 grep pattern 命中行 =", sum(1 for l in rlines if pat.search(l)))
say("  verified_path 命中行 =", [i + 1 for i, l in enumerate(rlines) if "verified_path" in l])
say("  import/装载语句 =", [(i + 1, l.strip()) for i, l in enumerate(rlines)
                            if re.search(r"^import |^from |spec_from_file_location|exec_module|sys\.path", l)])

# ---------- 4 _re_linked.py problems 纪律 ----------
say()
say("== 4 _re_linked.py 中写入 problems 的语句 ==")
rlsrc = (REL / "_re_linked.py").read_text(encoding="utf-8")
hits = [(i + 1, l.strip()) for i, l in enumerate(rlsrc.splitlines())
        if re.search(r"problems\.append|problems\.extend|out\[[\"']problems[\"']\]\s*=|\[[\"']problems[\"']\]\s*\+", l)]
say("  count =", len(hits), hits)
say("  docstring :47 =", rlsrc.splitlines()[46].strip())

# ---------- 5 link_triple 三元组与 rec 形态 ----------
say()
say("== 5 link_triple 实跑（6 个 fixture）==")
spec = importlib.util.spec_from_file_location("_mk_rel", REL / "_re_linked.py")
relmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(relmod)
FX = REL / "_re_fixtures"
for name in ["Pu_unique_with_decl", "Ffull_merged", "Fp1_decl_covers_one",
             "Pz_zero_with_decl", "Pi_invalid_hex_with_decl", "Fd_equiv_words"]:
    doc = FX / name / "doc.md"
    text = doc.read_text(encoding="utf-8")
    hm = re.search(r"SHA256\s*=\s*([0-9a-fA-F]{64})", text)
    bm = re.search(r"字节数\s*=\s*([\d,]+)", text)
    h = hm.group(1) if hm else None
    bd = int(bm.group(1).replace(",", "")) if bm else None
    prob, warn, rec = relmod.link_triple(text, doc.parent, h, bd, root=REPO)
    say("  --- %s verdict=%s ---" % (name, rec["samedoc_link"]["verdict"]))
    say("      problems=%r  warnings_n=%d  rec_keys=%s" % (prob, len(warn), sorted(rec.keys())))
    say("      tier=%r path=%r match=%r" % (rec.get("tier"), rec.get("path"), rec.get("match")))
    say("      single_obj_keys=%s  members=%s  decl_lines=%r  reverify=%r" % (
        {k: (k in rec) for k in ["verified_path", "recomputed", "bytes"]},
        len(rec["members"]) if "members" in rec else "ABSENT",
        rec.get("decl_lines", "ABSENT"),
        rec["samedoc_link"].get("reverify")))

# ---------- 6 机读件 totals / schema ----------
say()
say("== 6 _f2_compare_out.json totals 与 schema ==")
d = json.loads((R11 / "_f2_compare_out.json").read_text(encoding="utf-8"))
say("  top_keys =", list(d.keys()))
say("  totals =", json.dumps(d["totals"], ensure_ascii=False, sort_keys=True))
say("  n_results =", len(d["results"]))
say("  result_keys =", list(d["results"][0].keys()))
say("  orig_keys =", sorted(d["results"][0]["orig"].keys()))
say("  plus_keys =", sorted(d["results"][0]["plus"].keys()))
calc = {
    "bindings": sum(len(x["orig"]["bindings"]) for x in d["results"]),
    "orig_path": sum(1 for x in d["results"] for b in x["orig"]["bindings"] if b["path"]),
    "plus_path": sum(1 for x in d["results"] for b in x["plus"]["bindings"] if b.get("path")),
    "orig_match": sum(1 for x in d["results"] for b in x["orig"]["bindings"] if b["match"] is True),
    "plus_match": sum(1 for x in d["results"] for b in x["plus"]["bindings"] if b.get("match") is True),
    "orig_problems": sum(len(x["orig"]["problems"]) for x in d["results"]),
    "plus_problems": sum(len(x["plus"]["problems"]) for x in d["results"]),
}
say("  totals 由 results[] 重算 =", json.dumps(calc, ensure_ascii=False, sort_keys=True))
say("  RECOMPUTED_EQUALS_STORED =", calc == d["totals"])
all_plus_keys = sorted({k for x in d["results"] for b in x["plus"]["bindings"] for k in b})
say("  plus.bindings 全量键集 =", all_plus_keys)
say("  含 merged 字段 =", {k: (k in all_plus_keys) for k in
                          ["members", "decl_lines", "samedoc_link", "SAMEDOC_LINK_EQ"]})
from collections import Counter
ct = Counter(b.get("tier") for x in d["results"] for b in x["plus"]["bindings"])
say("  plus tier 分布 =", dict(ct))
say("  tier=None（:303-305 else 分支）条数 =", ct[None])

# ---------- 7 消费者面 ----------
say()
say("== 7 消费者面（逐件实读）==")
readers = ["_f2w_checks.py", "_f2w_extract.py", "_f2w_pass.py", "_f2w_final.py"]
say("  -- 读 _f2_compare_out.json 的 4 件：是否出现 'totals' --")
for f in readers:
    say("     %-20s totals=%s" % (f, "totals" in (R11 / f).read_text(encoding="utf-8")))
say("  -- 直调 r11_scan_plus 的件 --")
for f in sorted(R11.glob("*.py")):
    t = f.read_text(encoding="utf-8")
    n = t.count("r11_scan_plus(")
    if n and "def r11_scan_plus" not in t:
        say("     %-24s calls=%d" % (f.name, n))
say("  -- _g9_gate.py 是否调 r11_scan_plus --")
gg = (REPO / "lead" / "gate_r9r12_20261109" / "_g9_gate.py").read_text(encoding="utf-8")
say("     has_r11_scan_plus =", "r11_scan_plus" in gg, " :155 =", gg.splitlines()[154].strip())
say("  -- 硬编码 _f2_compare_out.json 指纹的脚本 --")
for p in sorted((REPO / "lead").rglob("_f2*d*fpcheck.py")):
    t = p.read_text(encoding="utf-8")
    if "148ea8d689eaaf582af05ea1bf4650605e104d6d74f8c7765e75a6eec662c7b1" in t:
        say("     ", str(p.relative_to(REPO)))
say()
say("== END ==")
