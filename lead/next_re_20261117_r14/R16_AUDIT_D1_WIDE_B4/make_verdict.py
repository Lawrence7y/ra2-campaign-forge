#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 verdict.tsv（11 行 × A–F）+ 汇总计数"""
import os, io, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
B4 = os.path.join(R14, "R16_D1_WIDE_B4")

D = json.load(io.open(os.path.join(HERE, "_d_e.json"), encoding="utf-8"))
dmap = {r["entry"]: r for r in D["d_rows"]}
BC = {r["entry"]: r for r in json.load(io.open(os.path.join(HERE, "_bc.json"), encoding="utf-8"))["rows"]}
AF = json.load(io.open(os.path.join(HERE, "a_f_result.json"), encoding="utf-8"))

def load(p):
    t = io.open(p, encoding="utf-8-sig", newline="").read()
    lines = t.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    hdr = lines[0].split("\t")
    return [dict(zip(hdr, l.split("\t"))) for l in lines[1:] if l.strip()]

FROWS = {r["entry"]: r for r in load(os.path.join(B4, "fields.tsv"))}
DROWS = {r["entry"]: r for r in load(os.path.join(B4, "delta.tsv"))}

hdr = ["entry", "name", "A_原文保全", "B_字节事实", "C_装配方式", "D_文本与事实", "E_反抄袭", "F_清单",
       "install_form_claim", "install_form_audit", "host_claim", "host_audit", "host_kind",
       "CLASS_FIX", "§12.6", "verdict", "note"]
rows = []
counts = collections.Counter()
for e in [r["entry"] for r in load(os.path.join(B4, "delta.tsv"))]:
    a = AF["A_vs_pin_b1"][e]
    bcr = BC[e]; b = bcr["b"]; c = bcr["site_cls"]; d = dmap[e]
    A = "PASS" if (a["col4_strict_prefix"] and a["grade_same"] and a["other_cols_identical"]) else "FAIL"
    B = "PASS" if all(b[k] for k in ("b1", "b2", "b3", "b4", "b5", "b6", "store_imm_eq_vt")) \
        and b["host_ne_entry"] and b["site_inside_host"] and b["host_is_fn_start"] else "FAIL"
    C = "PASS" if bcr["form_ok"] else "FAIL"
    Dd = "PASS" if d["d_ok"] else "FAIL"
    E = "PASS" if D["E"]["full_distinct"] and D["E"]["norm_hex_distinct"] else "FAIL"
    F = "PASS" if AF["F"]["delta_equals_residual_set"] else "FAIL"
    hk = c["host_kind"]["kind"] if c.get("host_kind") else ""
    note = []
    if FROWS[e]["status(OK|SKIP-ALREADY|SKIP|CLASS_FIX)"] == "CLASS_FIX":
        note.append("CLASS_FIX成立：原表%s≠%s；新表%s严格等于行名类；entry在槽；类内唯一" % (
            bcr["tables"][0]["mangled"] if bcr["tables"] else "?",
            d["entry"], b["mangled"]))
    if bcr["claim_form"] == "reg":
        note.append("reg成立：宿主%s为基类析构器、被scalar-deleting包装器调用" % c["host"])
    if bcr["claim_form"] == "mov_abs":
        note.append("mov_abs成立：abs=0x%X 在 .data(VirtualSize)" % c.get("disp"))
    if bcr["claim_form"] == "ctor_body":
        note.append("ctor_body成立：this←ecx、基类构造先于装表、返回this、无删除签名/包装器")
    rows.append([e, DROWS[e]["name"], A, B, C, Dd, E, F, bcr["claim_form"], bcr["form_audit"],
                 bcr["claim_host"], c["host"], hk,
                 FROWS[e]["status(OK|SKIP-ALREADY|SKIP|CLASS_FIX)"] == "CLASS_FIX",
                 ("§12.6" if "§12.6" in d.get("disc", "") else "缺"),
                 "PASS" if all(x == "PASS" for x in (A, B, C, Dd, E, F)) else "FAIL",
                 "；".join(note)])
    counts["verdict_" + rows[-1][15]] += 1
    for k, v in (("A", A), ("B", B), ("C", C), ("D", Dd), ("E", E), ("F", F)):
        if v != "PASS":
            counts["bad_" + k] += 1

with io.open(os.path.join(HERE, "verdict.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\t".join(hdr) + "\n")
    for r in rows:
        f.write("\t".join(str(x) for x in r) + "\n")

print("rows", len(rows))
print(json.dumps(dict(counts), ensure_ascii=False, indent=1))
print("forms:", collections.Counter(r[9] for r in rows))
print("hosts kinds:", collections.Counter(r[12] for r in rows))
print("status:", collections.Counter(r[13] for r in rows))
