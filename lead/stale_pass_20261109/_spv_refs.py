"""独立复核：抽取被核报告全部 file:line 引用，回读真实文件对应行原文。
只读；输出仅落 lead/stale_pass_20261109/_spv_refs_out.txt。
"""
import os, re, hashlib, json

ROOT = "D:/Project/ra2-campaign-forge"
REPORT = ROOT + "/lead/stale_pass_20261109/_sp_STALE_PASS_CENSUS.md"
W = ROOT + "/lead/stale_pass_20261109/"

ALIAS = {
    "PENDING": "lead/PENDING_DECISIONS.md",
    "GOAL": "lead/GOAL_THREE_TARGETS_20261018.md",
    "REFSYNC_SCOPE_FIX.md": "lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md",
    "CHECK_MASKING_INJECT.md": "lead/check_masking_20261109/CHECK_MASKING_INJECT.md",
    "MASKING_EFFECT_AUDIT.md": "lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md",
    "RULING_D27.md": "lead/d27_ruling_20261106/RULING_D27.md",
    "RULING_D28.md": "lead/d28_ruling_20261106/RULING_D28.md",
    "RULING_D29.md": "lead/d29_ruling_20261106/RULING_D29.md",
    "RULING_D30.md": "lead/d30_ruling_20261106/RULING_D30.md",
    "RULING_D26.md": "lead/d26_ruling_20261106/RULING_D26.md",
    "RULING_D25.md": "lead/d25_ruling_20261106/RULING_D25.md",
    "check_d27.py": "lead/d27_ruling_20261106/check_d27.py",
    "check_d28.py": "lead/d28_ruling_20261106/check_d28.py",
    "check_d29.py": "lead/d29_ruling_20261106/check_d29.py",
    "check_d30.py": "lead/d30_ruling_20261106/check_d30.py",
    "check_d26.py": "lead/d26_ruling_20261106/check_d26.py",
    "check_d25.py": "lead/d25_ruling_20261106/check_d25.py",
    "_rs_carrier_scan.py": "lead/refsync_scope_20261109/_rs_carrier_scan.py",
    "_d27_facts.py": "lead/d27_ruling_20261106/_d27_facts.py",
    "_d29_facts.py": "lead/d29_ruling_20261106/_d29_facts.py",
    "_d30_facts.py": "lead/d30_ruling_20261106/_d30_facts.py",
    "_d27_facts_out.txt": "lead/d27_ruling_20261106/_d27_facts_out.txt",
    "_cm_AUDIT.md": "lead/check_masking_20261109/_cm_AUDIT.md",
    "_me_design.py": "lead/masking_effect_20261109/_me_design.py",
    "_mev_final_out.txt": "lead/masking_effect_20261109/_mev_final_out.txt",
    "_nn_REPORT.md": "lead/refsync_scope_20261109/_nn_REPORT.md",
    "NEEDLE_NORMALIZATION.md": "lead/refsync_scope_20261109/NEEDLE_NORMALIZATION.md",
    "_stall_probe.py": "lead/a_residual_20261106/_stall_probe.py",
    "BUDGET_MODEL.json": "lead/d28_ruling_20261106/BUDGET_MODEL.json",
    "EARLY_TRIGGER_FEASIBILITY.md": "lead/d30_ruling_20261106/EARLY_TRIGGER_FEASIBILITY.md",
    "STALL_EVENTS.json": "lead/d27_ruling_20261106/STALL_EVENTS.json",
}

_extra = {
    "_sp_STALE_PASS_CENSUS.md": "lead/stale_pass_20261109/_sp_STALE_PASS_CENSUS.md",
    "_sp_hashcheck.py": "lead/stale_pass_20261109/_sp_hashcheck.py",
    "_sp_scan.py": "lead/stale_pass_20261109/_sp_scan.py",
    "_sp_broad.py": "lead/stale_pass_20261109/_sp_broad.py",
    "_sp_tally.py": "lead/stale_pass_20261109/_sp_tally.py",
    "_sp_classify.py": "lead/stale_pass_20261109/_sp_classify.py",
    "_sp_dist.py": "lead/stale_pass_20261109/_sp_dist.py",
    "_sp_final_checks.py": "lead/stale_pass_20261109/_sp_final_checks.py",
    "_sp_4gate_compare.py": "lead/stale_pass_20261109/_sp_4gate_compare.py",
    "_sp_4gate_compare_out.txt": "lead/stale_pass_20261109/_sp_4gate_compare_out.txt",
    "_sp_andk.py": "lead/stale_pass_20261109/_sp_andk.py",
    "_sp_andk_out.txt": "lead/stale_pass_20261109/_sp_andk_out.txt",
    "_sp_rs_broken_out.txt": "lead/stale_pass_20261109/_sp_rs_broken_out.txt",
    "_sp_agg_87196b.txt": "lead/stale_pass_20261109/_sp_agg_87196b.txt",
    "_sp_agg_f0b7c1.txt": "lead/stale_pass_20261109/_sp_agg_f0b7c1.txt",
    "_sp_report.txt": "lead/stale_pass_20261109/_sp_report.txt",
    "_sp_scan_raw.json": "lead/stale_pass_20261109/_sp_scan_raw.json",
    "_sp_tally_raw.json": "lead/stale_pass_20261109/_sp_tally_raw.json",
}
ALIAS.update(_extra)

# 匹配 NAME:line 或 NAME:line-line 或 NAME:line,line
PAT = re.compile(r"(?<![\w/])([A-Za-z_][A-Za-z0-9_.\-]*?)(?:\.md|\.py|\.txt|\.json)?\s*:\s*(\d+)(?:\s*[-–]\s*(\d+))?")

text = open(REPORT, "rb").read().decode("utf-8")
lines_cache = {}


def get_lines(rel):
    if rel not in lines_cache:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            lines_cache[rel] = None
        else:
            lines_cache[rel] = open(p, "rb").read().decode("utf-8", "replace").split("\n")
    return lines_cache[rel]


def resolve(name):
    if name in ALIAS:
        return ALIAS[name]
    # 报告里带扩展名的全名
    for k, v in ALIAS.items():
        if k == name or k.lower() == name.lower():
            return v
    return None


refs = {}
for no, ln in enumerate(text.split("\n"), 1):
    for m in PAT.finditer(ln):
        name, a, b = m.group(1), int(m.group(2)), m.group(3)
        # 过滤明显不是文件名的情况（例如 EXIT=0、N/N、k=2）
        rel = resolve(name)
        if rel is None:
            continue
        key = (rel, a, int(b) if b else a)
        refs.setdefault(key, []).append(no)

out = []
out.append("=== ② 报告 file:line 引用逐条回读（去重后 %d 个） ===" % len(refs))
out.append("口径：1-based，按文件字节 split('\\n')；报告自身扫描脚本可能用 readlines/splitlines，末尾换行差 1 行已单列核对。")
missing = []
for (rel, a, b), srclns in sorted(refs.items()):
    ls = get_lines(rel)
    if ls is None:
        missing.append((rel, a, b, srclns))
        out.append(f"[MISSING FILE] {rel}:{a}-{b}  (report lines {sorted(set(srclns))})")
        continue
    tag = "OK" if 1 <= a <= len(ls) and 1 <= b <= len(ls) else "OUT_OF_RANGE"
    out.append(f"--- [{tag}] {rel}:{a}" + (f"-{b}" if b != a else "") + f"   (report lines {sorted(set(srclns))}) ---")
    for n in range(a, min(b, a + 4) + 1):
        if 1 <= n <= len(ls):
            s = ls[n - 1]
            if len(s) > 300:
                s = s[:300] + "…[TRUNC]"
            out.append(f"  L{n}: {s}")
    if b > a + 4:
        out.append(f"  ... ({b-a-4} lines omitted) ...")
        for n in range(max(a + 5, b - 1), b + 1):
            if 1 <= n <= len(ls):
                s = ls[n - 1]
                if len(s) > 300:
                    s = s[:300] + "…[TRUNC]"
                out.append(f"  L{n}: {s}")

out.append("")
out.append("=== 摘要 ===")
out.append("MISSING_OR_UNRESOLVED = %d" % len(missing))
for x in missing:
    out.append("  " + repr(x))
open(W + "_spv_refs_out.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("WROTE", W + "_spv_refs_out.txt")
print("REF_GROUPS =", len(refs), "MISSING =", len(missing))
