#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B3 step D: closing cross-checks (F list consistency, E reuse,
005F4B10 withdrawal dossier, REPORT.md numeric consistency).
Writes _final_checks.txt
"""
import os
import re
import json
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
B3 = os.path.join(R14, "R16_D1_WIDE_B3")
V = json.load(open(os.path.join(HERE, "_verdict.json"), encoding="utf-8"))
FACTS = json.load(open(os.path.join(HERE, "_facts.json"), encoding="utf-8"))
ROWS = {r["entry"]: r for r in FACTS["rows"]}


def load_tsv(path):
    out = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            if line.strip():
                out.append(dict(zip(hdr, line.rstrip("\n").split("\t"))))
    return hdr, out


OUT = []
w = OUT.append

# ---------------------------------------------------------------- F: B1/B2 disjoint
_, B1 = load_tsv(os.path.join(R14, "R16_AUDIT_D1_WIDE_B1", "check.tsv"))
_, B2 = load_tsv(os.path.join(R14, "R16_AUDIT_D1_WIDE_B2", "verdict.tsv"))
B1E = set(x["entry"] for x in B1)
B2E = set(x["entry"] for x in B2)
B3E = set(r["entry"] for r in FACTS["rows"])
w("F/LIST CONSISTENCY")
w("  B1 entries=%d  B2 entries=%d  B3 entries=%d" % (len(B1E), len(B2E), len(B3E)))
w("  B3 ∩ B1 = %s" % sorted(B3E & B1E))
w("  B3 ∩ B2 = %s" % sorted(B3E & B2E))
w("  B1 ∪ B2 ∪ B3 = %d" % len(B1E | B2E | B3E))

_, SIEVE = load_tsv(os.path.join(R14, "R16_SIEVE_D1_WIDE", "sieve_all.tsv"))
K = "has_ring4_on_disk(是/否)"
no4 = sorted([r for r in SIEVE if r[K] == "否"], key=lambda r: r["entry"])
w("  sieve total=%d  has_ring4=否 -> %d" % (len(SIEVE), len(no4)))
w("  batch = no4[36:54] : %s" % ("MATCHES delta order" if
                                 [r["entry"] for r in no4[36:54]] == list(
                                     r["entry"] for r in FACTS["rows"]) else "MISMATCH"))
w("  delta row count=%d   unique=%d" % (len(FACTS["rows"]), len(B3E)))

_, FIELDS = load_tsv(os.path.join(B3, "fields.tsv"))
KS = "status(OK|SKIP-ALREADY|SKIP|CLASS_FIX)"
KF = "install_form(ctor_body|mov_abs|reg|other)"
w("  fields status counts: %s" % dict(collections.Counter(x[KS] for x in FIELDS)))
w("  fields form counts  : %s" % dict(collections.Counter(x[KF] for x in FIELDS)))
w("  computed form counts: %s" % dict(V["forms"]))
w("  non-POS verdict_polarity rows in batch: %s" % [
    (r["entry"], r["sieve"].get("verdict_polarity")) for r in FACTS["rows"]
    if r["sieve"].get("verdict_polarity") != "POS"])

# -------------------------------------------------- D1: table multiplicity per row
w("")
w("TABLE MULTIPLICITY (how many live tables hold entry at that slot) — affects the")
w("④ claim 「该槽即其 vt=… 表 slotN，无归属歧义」")
for r in FACTS["rows"]:
    ts = r.get("tables", [])
    same = [t for t in ts if t["mangled"] == (r["rtti"] or {}).get("mangled")]
    w("  %s vt=%s slot=%-2s tables=%-2d same-class-tables=%d  chosen_is_only=%s" % (
        r["entry"], r["vt_h"], r["slot"], len(ts), len(same), len(same) == 1))
    if len(ts) > 1:
        w("      classes: %s" % ", ".join(t["mangled"] for t in ts))

# ------------------------------------------------------------- E: reuse evidence
w("")
w("E ANTI-PLAGIARISM")
w("  raw ④ bodies distinct: %d/%d" % (V["E"]["raw_distinct"], len(FACTS["rows"])))
w("  hex-normalised distinct: %d/%d" % (V["E"]["hex_distinct"], len(FACTS["rows"])))
w("  hex+slot-normalised distinct: %d/%d" % (V["E"]["both_distinct"], len(FACTS["rows"])))
w("  collapse groups under hex+slot normalisation (legit: same class+vt, differ in slot/entry):")
for gp in V["E"]["collapse_groups"]:
    w("      %s" % gp)
w("  verbatim reuse of an on-disk ④ body: %s" % (V["E"]["dup_with_disk"] or "none"))
w("  witness-core collisions (same class/vt/slot/site): %s" % [
    (o["entry"], o["E"]["same_witness_core_rows"]) for o in V["rows"]
    if o["E"]["same_witness_core_rows"]] or "none")

# ------------------------------------------------------- 005F4B10 withdrawal dossier
w("")
w("005F4B10 WITHDRAWAL DOSSIER")
r = ROWS["005F4B10"]
w("  sieve audit_file=%s line=%s" % (r["sieve"]["audit_file"], r["sieve"]["audit_line"]))
w("  sieve verdict_polarity=%s  n_supporting_artifacts=%s" % (
    r["sieve"]["verdict_polarity"], r["sieve"]["n_supporting_artifacts"]))
w("  sieve audit_quote (excerpt): %s" % r["sieve"]["audit_quote"][:300])
w("  quote names BuildingLightClass vt 007E3AD0 slot 65 : %s" % (
    "YES" if ("005F4B10" in r["sieve"]["audit_quote"] and
              "BuildingLightClass" in r["sieve"]["audit_quote"] and
              "007E3AD0" in r["sieve"]["audit_quote"]) else "NO"))
w("  quote names ObjectClass : %s" % ("YES" if "ObjectClass" in r["sieve"]["audit_quote"] else "NO"))
w("  row name class = %s ; chosen table RTTI = %s" % (
    r["delta"]["name"].split("::")[0], (r["rtti"] or {}).get("mangled")))
w("  tables holding entry at slot 65: %d  -> %s" % (
    len(r["tables"]), [t["mangled"] for t in r["tables"]][:20]))
w("  byte facts of the ④ (independent): vt %s slot %s value %s RTTI %s" % (
    r["vt_h"], r["slot"], "%08X" % r["slot_val"], (r["rtti"] or {}).get("mangled")))
w("  => ④ 本身字节真，但行名类的归属无 ② 链支持(② 原文归属 BuildingLightClass 且极性 NEG)")
w("     ⇒ 结论：随行一并撤回 ④（Lead 裁定一致）")

# ------------------------------------------------------------ REPORT.md consistency
w("")
w("REPORT.md NUMERIC CONSISTENCY (audited claims vs independent computation)")
rep = open(os.path.join(B3, "REPORT.md"), encoding="utf-8").read()


def has(pat):
    return bool(re.search(pat, rep))


checks = [
    ("§0/§4  OK=16", "OK" and "16" in rep and has(r"\|\s*OK\s*\|\s*16\s*\|")),
    ("§4  CLASS_FIX=2", has(r"CLASS_FIX\s*\|\s*2\s*\|")),
    ("§4  SKIP=0", has(r"\|\s*SKIP\s*\|\s*0\s*\|")),
    ("§3  ctor_body=13", has(r"ctor_body\s*\|\s*13\s*\|")),
    ("§3  mov_abs=4", has(r"mov_abs\s*\|\s*4\s*\|")),
    ("§3  reg=1", has(r"\|\s*reg\s*\|\s*1\s*\|")),
    ("§5  18/18 × 6 全 True", "18/18 × 6" in rep),
    ("§7  coverage sha", "412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1" in rep),
    ("§7  gamemd sha", "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476" in rep),
    ("§9  discloses 005F4B10 NEG", "NEG" in rep and "005F4B10" in rep),
    ("§5  all_hv=True claim", "all_hv=True" in rep),
]
for name, ok in checks:
    w("  %-28s %s" % (name, "consistent" if ok else "CHECK MANUALLY"))
w("  coverage sha recomputed: %s  (match=%s)" % (
    V["cov_sha"], V["cov_sha"] == "412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1"))
w("  gamemd sha recomputed : %s  (match=%s)" % (V["exe_sha"], V["exe_sha"] ==
                                                "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"))
w("  REPORT line 3 card id claim: %s" % [l for l in rep.split("\n")[:5] if "卡号" in l])

# --------------------------------------------------------- §12.6 pointer census
w("")
w("§12.6 DISCLOSURE POINTER CENSUS (18/18 required)")
n126 = n124 = npanel = nd47 = nconcede = 0
for o in V["rows"]:
    r4 = o["ring4"]
    n126 += bool(r4.get("has_12_6"))
    n124 += bool(r4.get("has_12_4"))
    npanel += bool(r4.get("has_panel"))
    nd47 += bool(r4.get("has_d47"))
    nconcede += bool(r4.get("has_12_3_concede"))
w("  §12.6 present      : %d/18" % n126)
w("  §12.4 present(wrong): %d/18" % n124)
w("  PANEL pointer      : %d/18" % npanel)
w("  D-47(A) clause     : %d/18" % nd47)
w("  §12.3 concession   : %d/18" % nconcede)
w("  '已过 §12.3' (forbidden wording) rows: %s" % [
    o["entry"] for o in V["rows"] if "已过 §12.3" in o["ring4"]["raw"]])

# -------------------------------------------------------- SITE_FIX / CLASS_FIX recap
w("")
w("SITE_FIX / CLASS_FIX RECAP")
for x in FIELDS:
    if x["entry"] in ("0065CAC0", "0065CDD0", "0065CF00", "0065D0D0",
                      "0065D150", "0065D190", "00631CC0", "005F4B10"):
        note = x["note"]
        w("  %s status=%s site=%s host=%s form=%s" % (
            x["entry"], x[KS], x["install_site"], x["install_host"], x[KF]))
        for tag in ("0065CA03", "004014C4", "007E22A4", "007E4D78", "00477790", "00432610"):
            if tag in note:
                w("      note cites %s : yes" % tag)

with open(os.path.join(HERE, "_final_checks.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(OUT))
print("\n".join(OUT))
