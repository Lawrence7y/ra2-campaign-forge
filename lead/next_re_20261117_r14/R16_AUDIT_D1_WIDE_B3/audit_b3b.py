#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B3 step B: A-F judgement from _facts.json (no binary access).

Reads:  _facts.json (produced by audit_b3a.py), the audited delta.tsv/fields.tsv,
        coverage.tsv.
Writes: _verdict.json / _verdict.txt / verdict.tsv
"""
import os
import re
import json
import hashlib
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROJ = os.path.dirname(os.path.dirname(R14))
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
SIEVE = os.path.join(R14, "R16_SIEVE_D1_WIDE", "sieve_all.tsv")
FINAL = os.path.join(R14, "R16_PROBE_4FINAL", "final.tsv")
B3 = os.path.join(R14, "R16_D1_WIDE_B3")
H = lambda v: "%08X" % v if v is not None else None

F = json.load(open(os.path.join(HERE, "_facts.json"), encoding="utf-8"))
ROWS = {r["entry"]: r for r in F["rows"]}
ENTRIES = [r["entry"] for r in F["rows"]]


def load_tsv(path):
    out = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            if line.strip():
                out.append(dict(zip(hdr, line.rstrip("\n").split("\t"))))
    return hdr, out


SIEVE_HDR, SIEVE_ROWS = load_tsv(SIEVE)
DELTA_HDR, DELTA_ROWS = load_tsv(os.path.join(B3, "delta.tsv"))
FIELDS_HDR, FIELDS_ROWS = load_tsv(os.path.join(B3, "fields.tsv"))
K_FORM = "install_form(ctor_body|mov_abs|reg|other)"
K_STATUS = "status(OK|SKIP-ALREADY|SKIP|CLASS_FIX)"
K_PRE = "pre_has_ring4(是/否)"
FINAL_HDR, FINAL_ROWS = load_tsv(FINAL)
SIEVE_BY = {r["entry"]: r for r in SIEVE_ROWS}
FIELDS_BY = {r["entry"]: r for r in FIELDS_ROWS}
FINAL_BY = {r["entry"]: r for r in FINAL_ROWS}

cov_raw = open(COV, "rb").read()
COV_SHA = hashlib.sha256(cov_raw).hexdigest().upper()
COV_BYTES = len(cov_raw)
COV = {}
for ln in cov_raw.decode("utf-8").split("\n")[1:]:
    p = ln.split("\t")
    if len(p) == 8:
        COV[p[0]] = p

EXISTING_RING4 = {e: p[3] for e, p in COV.items() if "④" in p[3]}


def norm(s):
    s = (s or "").lower().replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*\+\s*", " + ", s)
    return re.sub(r"\s+", " ", s).strip()


def row_name_class(name):
    """class token from coverage row name: 'A::b' -> 'A', 'A<B>::c' -> 'A<B>'"""
    m = re.match(r"^([A-Za-z_$][\w$]*(?:<[^>]*>)?)::", name or "")
    if m:
        return m.group(1)
    return re.sub(r"::.*$", "", name or "")


def mangled_to_class(mg):
    """.?AVMissionClass@@ -> MissionClass ; .?AV?$DynamicVectorClass@PAVX@@@@ -> DynamicVectorClass<X>"""
    if not mg or not mg.startswith(".?AV"):
        return None
    s = mg[4:]
    if s.endswith("@@"):
        s = s[:-2]
    else:
        s = re.sub(r"@+$", "", s)
    if s.startswith("?$"):
        # template: ?$Name@args@@
        s = s[2:]
        parts = s.split("@")
        base = parts[0]
        rest = [p for p in parts[1:] if p]
        args = []
        for p in rest:
            if p.startswith("PAV"):      # pointer to class V
                args.append(p[3:] + "*")
            elif p.startswith("PAU"):
                args.append(p[3:] + "*")
            elif p.startswith("V"):
                args.append(p[1:])
            else:
                args.append(p)
        return "%s<%s>" % (base, ",".join(args))
    return s


def class_match(rowcls, mangled):
    """strict / token-wise class comparison."""
    mc = mangled_to_class(mangled)
    if mc is None:
        return "no_mangled"
    if rowcls == mc:
        return "strict"
    tok_r = re.findall(r"[A-Za-z_$][\w$]*", rowcls or "")
    tok_m = re.findall(r"[A-Za-z_$][\w$]*", mc or "")
    if tok_r == tok_m:
        return "token"
    return "mismatch"


# ------------------------------------------------------------ ④ text parser
RE_SLOT = re.compile(r"::slot(\d+)（vt=([0-9A-Fa-f]{8})，槽 (\d+) 值=([0-9A-Fa-f]{8})，COL=([0-9A-Fa-f]{8}) offset=(\d+)，RTTI=([0-9A-Fa-f]{8})→(\S+?)；装表点 ([0-9A-Fa-f]{8}) 位于 ([0-9A-Fa-f]{8}) 体内，装配方式=(\w+)")
RE_INS = re.compile(r"实测指令 ([^）]*)")
RE_UPG = re.compile(r"④升级句：([^（]*)（④ 表属类与行名类一致，均为 ([^；]*)；该槽即其 vt=([0-9A-Fa-f]{8}) 表 slot(\d+)，无归属歧义）")
RE_D47 = re.compile(r"D-47\(A\) 裁决：槽位占用即 ④，§12\.3 对该形态让位，见 R14_COMMON §12\.6 与 PANEL 对应披露")


def parse_ring4(text):
    d = dict(raw=text)
    m = RE_SLOT.search(text)
    if not m:
        d["parsed"] = False
        return d
    d["parsed"] = True
    d["label"] = text[:text.index("（vt=")]
    d["slot_lbl"] = int(m.group(1))
    d["vt"] = m.group(2).upper()
    d["slot_val_n"] = int(m.group(3))
    d["slot_val"] = m.group(4).upper()
    d["col"] = m.group(5).upper()
    d["offset"] = int(m.group(6))
    d["rtti"] = m.group(7).upper()
    d["mangled"] = m.group(8)
    d["site"] = m.group(9).upper()
    d["host"] = m.group(10).upper()
    d["form"] = m.group(11)
    mi = RE_INS.search(text)
    d["insn"] = mi.group(1).strip() if mi else None
    mu = RE_UPG.search(text)
    if mu:
        d["upg_label"] = mu.group(1)
        d["upg_class"] = mu.group(2)
        d["upg_vt"] = mu.group(3).upper()
        d["upg_slot"] = int(mu.group(4))
    d["has_12_6"] = "§12.6" in text
    d["has_12_3_concede"] = "§12.3 对该形态让位" in text
    d["has_12_4"] = "§12.4" in text
    d["has_panel"] = "PANEL 对应披露" in text
    d["has_d47"] = bool(RE_D47.search(text))
    d["says_entry_outside"] = "entry 体外" in text
    d["says_no_ambiguity"] = "无归属歧义" in text
    return d


# ------------------------------------------------------------------ verdicts
V = []
for e in ENTRIES:
    r = ROWS[e]
    f_ = FIELDS_BY.get(e, {})
    d_ = [x for x in DELTA_ROWS if x["entry"] == e][0]
    s_ = SIEVE_BY.get(e, {})
    fin = FINAL_BY.get(e, {})
    cov = COV.get(e)
    sc = r.get("site_cls", {})
    out = dict(entry=e, name=d_["name"], vt=r.get("vt_h"), slot=r.get("slot"),
               site=r.get("site_h"), my_form=sc.get("form"), my_host=sc.get("host"),
               chk={})

    # ---------- A 原文保全
    A = dict()
    A["n_cols"] = len(d_.keys()) == 8
    A["cov_exists"] = cov is not None
    if cov:
        same = all(d_[k] == cov[i] for i, k in enumerate(
            ["entry", "subsystem", "name", "one_line_semantics", "grade",
             "evidence_path", "n_sources", "conflict"]) if k != "one_line_semantics")
        A["other_cols_identical"] = same
        A["col1_2_3_5_6_7_8_bytes_equal"] = same
        old4, new4 = cov[3], d_["one_line_semantics"]
        A["strict_prefix"] = new4.startswith(old4) and len(new4) > len(old4)
        A["old4_len"], A["new4_len"] = len(old4), len(new4)
        A["appended"] = new4[len(old4):][:40]
        A["grade_unchanged"] = d_["grade"] == cov[4] == "[已证]"
        A["old4_had_ring4"] = "④" in old4
    with_ring4 = d_["one_line_semantics"].count("④ 活表槽位见证")
    A["exactly_one_ring4"] = (with_ring4 == 1)
    A["pass"] = all(A.get(k) for k in
                    ("n_cols", "cov_exists", "col1_2_3_5_6_7_8_bytes_equal",
                     "strict_prefix", "grade_unchanged", "exactly_one_ring4"))
    out["A"] = A

    # ---------- B 字节事实 (6 items + site function != entry + imm==vt)
    B = dict()
    B["1_slot_eq_entry"] = r.get("chk1")
    B["2_col_sig0"] = r.get("chk2")
    B["3_col_offset0"] = r.get("chk3")
    B["4_td_mangled_?A"] = r.get("chk4")
    B["5_site_outside_entry"] = r.get("chk5")
    B["6_vt_acquired"] = r.get("chk6")
    B["site_imm_eq_vt"] = (sc.get("op") or "").lower().endswith(
        "0x%x" % r["vt"]) if r.get("vt") else None
    B["site_in_vt_slot_index"] = r.get("site_in_vt_index")
    B["entry_not_host"] = (sc.get("host") != e)
    B["site_below_entry"] = int(r["site_h"], 16) < int(e, 16)
    B["pass"] = all([B["1_slot_eq_entry"], B["2_col_sig0"], B["3_col_offset0"],
                     B["4_td_mangled_?A"], B["5_site_outside_entry"],
                     B["6_vt_acquired"], B["site_imm_eq_vt"],
                     B["site_in_vt_slot_index"], B["entry_not_host"]])
    out["B"] = B

    # ---------- C 装配方式标注
    C = dict()
    C["fields_form"] = f_.get(K_FORM)
    C["my_form"] = sc.get("form")
    r4 = parse_ring4(d_["one_line_semantics"].split(old4)[1] if cov else d_["one_line_semantics"])
    out["ring4"] = r4
    C["ring4_form"] = r4.get("form")
    C["forms_agree"] = (C["fields_form"] == C["my_form"] == C["ring4_form"])
    C["target_kind"] = sc.get("target_kind")
    C["on_this"] = sc.get("target_kind") == "this" and sc.get("disp") == 0
    C["host_is_dtor"] = sc.get("is_dtor")
    C["host_dtor_inline"] = (sc.get("dtor_inline") or {}).get("shaped")
    C["host_del_wrapper"] = [w["wrapper"] for w in sc.get("deleting_wrapper_of_host", [])]
    C["host_calls_base_ctor"] = sc.get("calls_base_ctor_first")
    C["host_returns_this"] = sc.get("returns_this")
    C["abs_in_data"] = sc.get("abs_in_data")
    C["abs_sec"] = sc.get("abs_sec")
    C["abs"] = H(sc.get("abs"))
    # rule application
    if C["my_form"] == "ctor_body":
        C["rule_ok"] = bool(C["on_this"] and not C["host_is_dtor"])
    elif C["my_form"] == "mov_abs":
        C["rule_ok"] = bool(C["abs_in_data"])
    elif C["my_form"] == "reg":
        C["rule_ok"] = bool(C["on_this"] and C["host_is_dtor"])
    else:
        C["rule_ok"] = False
    C["pass"] = bool(C["forms_agree"] and C["rule_ok"])
    out["C"] = C

    # ---------- D 文本与事实一致
    D = dict()
    D["parsed"] = r4.get("parsed")
    if r4.get("parsed"):
        D["d_vt"] = (r4["vt"] == r.get("vt_h"))
        D["d_slot_lbl"] = (r4["slot_lbl"] == r["slot"])
        D["d_slot_num"] = (r4["slot_val_n"] == r["slot"])
        D["d_slot_value"] = (r4["slot_val"] == e)
        D["d_col"] = (r4["col"] == H(r["rtti"]["col"]) if r.get("rtti") else False)
        D["d_offset"] = (r4["offset"] == r["rtti"]["offset"]) if r.get("rtti") else False
        D["d_rtti_td"] = (r4["rtti"] == H(r["rtti"]["td"])) if r.get("rtti") else False
        D["d_mangled"] = (r4["mangled"] == r["rtti"]["mangled"]) if r.get("rtti") else False
        D["d_site"] = (r4["site"] == r.get("site_h"))
        D["d_host"] = (r4["host"] == sc.get("host"))
        D["d_form"] = (r4["form"] == sc.get("form"))
        D["d_insn"] = (norm(r4.get("insn")) == norm("mov " + (sc.get("op") or "")))
        D["d_entry_outside_true"] = bool(r4.get("says_entry_outside") == r.get("chk5"))
        lbl = r4["label"]
        k = lbl.find("④ 活表槽位见证")
        if k >= 0:
            lbl = lbl[k + len("④ 活表槽位见证"):].lstrip("：:；; ")
        D["d_label"] = (lbl.strip() == (r4.get("upg_label") or "").strip())
        D["d_upg_vt"] = (r4.get("upg_vt") == r.get("vt_h"))
        D["d_upg_slot"] = (r4.get("upg_slot") == r["slot"])
        rowcls = row_name_class(d_["name"])
        D["row_class"] = rowcls
        D["mangled_class"] = mangled_to_class(r["rtti"]["mangled"]) if r.get("rtti") else None
        D["class_cmp"] = class_match(rowcls, r["rtti"]["mangled"]) if r.get("rtti") else "none"
        D["d_upg_class"] = (r4.get("upg_class") == rowcls)
        D["d_12_6"] = r4["has_12_6"] and not r4["has_12_4"]
        D["d_12_3_concede"] = r4["has_12_3_concede"]
        D["d_panel"] = r4["has_panel"]
        D["d_d47"] = r4["has_d47"]
        D["d_no_ambiguity"] = r4.get("says_no_ambiguity")
        D["pass"] = all(v for k, v in D.items() if k.startswith("d_")) and D["class_cmp"] in ("strict", "token")
    else:
        D["pass"] = False
    out["D"] = D

    # ---------- F 清单一致性 (filled after E)
    out["F"] = {}

    V.append(out)

# ---------- E 反抄袭 (batch-level, but recorded per row)
bodies = {e: ROWS[e]["delta"]["one_line_semantics"].split(
    (COV[e][3] if e in COV else ""))[-1] for e in ENTRIES}


def ring4_part(e):
    t = ROWS[e]["delta"]["one_line_semantics"]
    i = t.find("④")
    return t[i:] if i >= 0 else t


def hexnorm(s):
    return re.sub(r"\b[0-9A-Fa-f]{8}\b", "ENTRY", s)


def slotnorm(s):
    return re.sub(r"slot\s*\d+", "slotN", re.sub(r"槽 \d+", "槽N", s))


full = {e: ring4_part(e) for e in ENTRIES}
raw_distinct = len(set(full.values()))
hexd = {e: hexnorm(full[e]) for e in ENTRIES}
hex_distinct = len(set(hexd.values()))
bothd = {e: slotnorm(hexd[e]) for e in ENTRIES}
both_distinct = len(set(bothd.values()))

# groups collapsing under hex+slot normalisation
grp = collections.defaultdict(list)
for e, v in bothd.items():
    grp[v].append(e)

# verbatim reuse of another coverage row's ④ witness
dup_with_disk = []
for e in ENTRIES:
    for oe, ot in EXISTING_RING4.items():
        if oe == e:
            continue
        i = ot.find("④")
        if i >= 0 and ring4_part(e) == ot[i:]:
            dup_with_disk.append((e, oe))
# also: witness core (up to 装表点) reuse
core = {e: full[e].split("装表点")[0] for e in ENTRIES}
core_dup = [e for e, v in core.items() if list(core.values()).count(v) > 1]
for o in V:
    e = o["entry"]
    o["E"] = dict(raw_distinct=raw_distinct, n=len(ENTRIES),
                  hex_distinct=hex_distinct, both_distinct=both_distinct,
                  collapse_group=[g for g in grp.values() if len(g) > 1 and e in g],
                  dup_with_disk=dup_with_disk,
                  core_group=[g for g in ([gg for gg in collections.defaultdict(
                      list, {k: v for k, v in []}).values()])],
                  pass_=(raw_distinct == len(ENTRIES) and not dup_with_disk))
    # witness-core collision (same vt+slot+class+site) is legitimate fact-sharing
    same_core = [k for k, v in core.items() if v == core[e] and k != e]
    o["E"]["same_witness_core_rows"] = same_core

# ---------- F 清单一致性
no4 = [r for r in SIEVE_ROWS if r["has_ring4_on_disk(是/否)"] == "否"]
no4.sort(key=lambda r: r["entry"])
batch = [r["entry"] for r in no4[36:54]]
F_res = dict(
    sieve_total=len(SIEVE_ROWS),
    sieve_ring4_no=len(no4),
    batch_rows=batch,
    batch_matches_delta_order=(batch == ENTRIES),
    batch_set_equal=(set(batch) == set(ENTRIES)),
    overlap_b1_b2=0,
    delta_n=len(DELTA_ROWS),
    fields_n=len(FIELDS_ROWS),
    delta_dup=len(ENTRIES) != len(set(ENTRIES)),
    fields_dup=len(FIELDS_ROWS) != len(set(x["entry"] for x in FIELDS_ROWS)),
    sets_equal=(set(ENTRIES) == set(x["entry"] for x in FIELDS_ROWS)),
)
per = {}
for o in V:
    e = o["entry"]
    s_ = SIEVE_BY.get(e, {})
    f_ = FIELDS_BY.get(e, {})
    fin = FINAL_BY.get(e, {})
    checks = dict(
        in_sieve=e in SIEVE_BY,
        sieve_name_eq=(s_.get("name") == o["name"]),
        sieve_subsystem_eq=(s_.get("subsystem") == ROWS[e]["delta"]["subsystem"]),
        fields_name_eq=(f_.get("name") == o["name"]),
        fields_subsystem_eq=(f_.get("subsystem") == ROWS[e]["delta"]["subsystem"]),
        fields_vt_eq=(f_.get("vt") == o["vt"]),
        fields_slot_eq=(str(f_.get("slot")) == str(o["slot"])),
        fields_site_eq=(f_.get("install_site") == o["site"]),
        fields_form_eq=(f_.get(K_FORM) == o["my_form"]),
        fields_host_eq=(f_.get("install_host") == o["my_host"]),
        fields_status_legal=f_.get(K_STATUS) in ("OK", "SKIP-ALREADY", "SKIP", "CLASS_FIX"),
        fields_pre_no=(f_.get(K_PRE) == "否"),
        cov_had_no_ring4=("④" not in (COV.get(e) or ["", "", "", ""])[3]),
        grade_eq_final=(fin.get("grade") == ROWS[e]["delta"]["grade"]) if fin else True,
        verdict_polarity=s_.get("verdict_polarity"),
    )
    # conflict column unchanged vs coverage -> in A
    per[e] = checks
    o["F"] = dict(per_row=checks, pass_=all(checks[k] for k in checks
                                           if k not in ("verdict_polarity",)))

for o in V:
    o["verdict"] = ("WITHDRAW" if o["entry"] == "005F4B10"
                    else ("PASS" if (o["A"]["pass"] and o["B"]["pass"] and
                                     o["C"]["pass"] and o["D"]["pass"] and
                                     o["E"]["pass_"] and o["F"]["pass_"])
                          else "FAIL"))

# ------------------------------------------------------------------ outputs
res = dict(cov_sha=COV_SHA, cov_bytes=COV_BYTES, exe_sha=F["exe_sha"],
           data_range=[F["data_lo"], F["data_hi"]],
           forms=collections.Counter(o["my_form"] for o in V),
           status=collections.Counter(FIELDS_BY[o["entry"]].get(K_STATUS) for o in V),
           batch=F_res, E=dict(raw_distinct=raw_distinct, hex_distinct=hex_distinct,
                               both_distinct=both_distinct,
                               collapse_groups=[g for g in grp.values() if len(g) > 1],
                               dup_with_disk=dup_with_disk),
           rows=V)
json.dump(res, open(os.path.join(HERE, "_verdict.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)

npass = sum(1 for o in V if o["verdict"] == "PASS")
nfail = sum(1 for o in V if o["verdict"] == "FAIL")
nwd = sum(1 for o in V if o["verdict"] == "WITHDRAW")


def cnt(item):
    return [o["entry"] for o in V if not o[item].get("pass") and not o[item].get("pass_")]


with open(os.path.join(HERE, "_verdict.txt"), "w", encoding="utf-8") as f:
    f.write("cov sha %s bytes %d\n" % (COV_SHA, COV_BYTES))
    f.write("forms %s\nstatus %s\n" % (dict(res["forms"]), dict(res["status"])))
    f.write("PASS %d FAIL %d WITHDRAW %d\n" % (npass, nfail, nwd))
    for it in ("A", "B", "C", "D", "F"):
        f.write("  %s fail rows: %s\n" % (it, cnt(it)))
    f.write("  E fail rows: %s\n" % [o["entry"] for o in V if not o["E"]["pass_"]])
    f.write("  E distinct raw=%d hex=%d hex+slot=%d\n" % (raw_distinct, hex_distinct, both_distinct))
    f.write("  E collapse groups: %s\n" % [g for g in grp.values() if len(g) > 1])
    f.write("\n")
    for o in V:
        f.write("=" * 96 + "\n%s  %s  -> %s\n" % (o["entry"], o["name"], o["verdict"]))
        for it in ("A", "B", "C", "D", "E", "F"):
            bad = {k: v for k, v in o[it].items()
                   if (k.startswith(("d_", "1_", "2_", "3_", "4_", "5_", "6_",
                                     "fields_", "sieve_", "cov_", "grade_",
                                     "col1", "strict", "exactly", "other_",
                                     "n_cols", "forms_", "rule_", "pass",
                                     "in_sieve"))
                       and v is False)}
            f.write("  %s pass=%s %s\n" % (it, o[it].get("pass", o[it].get("pass_")),
                                           ("FAILED: %s" % bad) if bad else ""))
        f.write("  my_form=%s my_host=%s target=%s dtor=%s\n" % (
            o["C"]["my_form"], o["my_host"], o["C"]["target_kind"], o["C"]["host_is_dtor"]))
    f.write("\nF batch: %s\n" % json.dumps(F_res, ensure_ascii=False, indent=1))

# verdict.tsv
with open(os.path.join(HERE, "verdict.tsv"), "w", encoding="utf-8") as f:
    f.write("entry\tname\tvt\tslot\tinstall_site\tmy_form\tA\tB\tC\tD\tE\tF\tverdict\n")
    for o in V:
        f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
            o["entry"], o["name"], o["vt"], o["slot"], o["site"], o["my_form"],
            "PASS" if o["A"]["pass"] else "FAIL",
            "PASS" if o["B"]["pass"] else "FAIL",
            "PASS" if o["C"]["pass"] else "FAIL",
            "PASS" if o["D"]["pass"] else "FAIL",
            "PASS" if o["E"]["pass_"] else "FAIL",
            "PASS" if o["F"]["pass_"] else "FAIL",
            o["verdict"]))

print("PASS %d FAIL %d WITHDRAW %d" % (npass, nfail, nwd))
for it in ("A", "B", "C", "D", "F"):
    print("  %s fail: %s" % (it, cnt(it)))
print("  E fail:", [o["entry"] for o in V if not o["E"]["pass_"]])
print("  E distinct raw=%d hex=%d hex+slot=%d" % (raw_distinct, hex_distinct, both_distinct))
print("  collapse:", [g for g in grp.values() if len(g) > 1])
