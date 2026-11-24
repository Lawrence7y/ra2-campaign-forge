#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T1: 按 R14-R14 的 S 口径精确计算 S17 的 named(S) 分子/分母。
分母 = atlas 内 subsystem==S17 的行数。
named(S): name 非空 且 不以 'sub_' 开头 且 不是 'Class::sub_XXXXXXXX' 形式。
同时输出 L 口径 (name 非空 且 不以 'sub_' 开头) 便于对照。
数据来源只读；不写台账。
"""
import csv, sys, io, os

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
CARD = os.path.join(ROOT, r"lead\next_re_20261117_r14\S17-K3")

def load_tsv(path):
    with io.open(path, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        return list(r)

cov = load_tsv(COV)
atlas = load_tsv(ATLAS)

atlas_entries = set(row["entry"].lower() for row in atlas)

# S17 coverage rows that are in atlas
s17 = [r for r in cov if r.get("subsystem") == "S17" and r["entry"].lower() in atlas_entries]

import re
# Class::sub_XXXXXXXX 形式：包含 "::sub_" 后跟 8 位十六进制（可能更多字符）
CLASS_SUB_RE = re.compile(r"::sub_[0-9A-Fa-f]{8}\b")
def is_class_sub(name):
    return bool(CLASS_SUB_RE.search(name))

def named_L(name):
    n = (name or "").strip()
    return n != "" and not n.startswith("sub_")

def named_S(name):
    return named_L(name) and not is_class_sub(name)

den = len(s17)
named_l_n = sum(1 for r in s17 if named_L(r.get("name","")))
named_s_n = sum(1 for r in s17 if named_S(r.get("name","")))
proved_n  = sum(1 for r in s17 if r.get("grade") == "[已证]")

out = []
out.append("=== T1 S17 named(S) 口径精算 ===")
out.append(f"coverage.tsv 数据行: {len(cov)}")
out.append(f"atlas 数据行: {len(atlas)}")
out.append(f"atlas entry 去重: {len(atlas_entries)}")
out.append(f"S17 全表行数(subsystem==S17): {sum(1 for r in cov if r.get('subsystem')=='S17')}")
out.append("")
out.append(f"分母 (S17 ∩ atlas): {den}")
out.append(f"named_L 分子: {named_l_n} ({100*named_l_n/den:.2f}%)")
out.append(f"named_S 分子: {named_s_n} ({100*named_s_n/den:.2f}%)")
out.append(f"proved 分子: {proved_n} ({100*proved_n/den:.2f}%)")
out.append(f"门槛: named>=90% => 需 {(-(-90*den//100))} 个; 当前 named_S={named_s_n}, 差 {(-(-90*den//100))-named_s_n} 个")
out.append("")
out.append("=== 所有当前 NOT named(S) 的行 (即 sub_ 占位 / 空名 / Class::sub_) ===")
out.append("entry\tsubsystem\tname\tgrade\tsemantics\tevidence_path\treason")
not_named = [r for r in s17 if not named_S(r.get("name",""))]
for r in sorted(not_named, key=lambda x: x["entry"]):
    name = r.get("name","")
    reasons = []
    if not name.strip(): reasons.append("EMPTY")
    if name.strip().startswith("sub_"): reasons.append("SUB_PREFIX")
    if is_class_sub(name): reasons.append("CLASS_SUB")
    out.append("\t".join([r["entry"], r.get("subsystem",""), name, r.get("grade",""),
                          r.get("one_line_semantics",""), r.get("evidence_path",""), ",".join(reasons)]))
out.append("")
out.append(f"NOT named(S) 行数: {len(not_named)}")
out.append("")
out.append("=== 所有 name 含 '::sub_' 的行(全 S17) ===")
for r in s17:
    if "::sub_" in r.get("name",""):
        out.append("\t".join([r["entry"], r.get("name",""), r.get("grade","")]))

txt = "\n".join(out) + "\n"
with io.open(os.path.join(CARD, "EVIDENCE", "t1_named_count.txt"), "w", encoding="utf-8") as f:
    f.write(txt)
sys.stdout.write(txt)
