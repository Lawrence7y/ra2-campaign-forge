#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B4 / 收尾交叉核对：
- fields.tsv 的 sieve_audit_file/line 与 sieve_all.tsv 一致
- delta 的 subsystem/name 与 coverage(基线 pin) 一致
- evidence_path 首段可解析
- sieve verdict_polarity / overlap 标志
- REPORT §8 样例 ④ 是否与 delta.tsv 逐字一致
- 每行 ④ 出现次数（防重复追加）
"""
import os, io, re, json, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
B4 = os.path.join(R14, "R16_D1_WIDE_B4")
PIN = os.path.join(R14, "R16_MERGE_D1_WIDE_B1", "_pin_coverage.tsv")
SIEVE = os.path.join(R14, "R16_SIEVE_D1_WIDE", "sieve_all.tsv")

def load(p, enc="utf-8-sig"):
    t = io.open(p, encoding=enc, newline="").read()
    lines = t.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    hdr = lines[0].split("\t")
    return hdr, [dict(zip(hdr, l.split("\t"))) for l in lines[1:] if l.strip()], lines

_, DROWS, DLINE = load(os.path.join(B4, "delta.tsv"))
_, FROWS, _ = load(os.path.join(B4, "fields.tsv"))
_, SROWS, _ = load(SIEVE, "utf-8")
# pin / coverage 的表头是逗号分隔但行是 TAB 分隔 —— 用固定列名
PINH = ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path", "n_sources", "conflict"]
_pin_lines = io.open(PIN, encoding="utf-8-sig", newline="").read().split("\n")
PROWS = [dict(zip(PINH, l.split("\t"))) for l in _pin_lines[1:] if l.strip()]
SV = {r["entry"]: r for r in SROWS}
PV = {r["entry"]: r for r in PROWS}
rep = {}

# 1 fields vs sieve
bad = []
for f in FROWS:
    e = f["entry"]; s = SV.get(e)
    if not s:
        bad.append((e, "sieve 缺行")); continue
    if f["sieve_audit_file"] != s["audit_file"]:
        bad.append((e, "audit_file %r != %r" % (f["sieve_audit_file"], s["audit_file"])))
    if f["sieve_audit_line"] != s["audit_line"]:
        bad.append((e, "audit_line %r != %r" % (f["sieve_audit_line"], s["audit_line"])))
    if f["name"] != s["name"]:
        bad.append((e, "name 与 sieve 不符"))
    if f["subsystem"] != s["subsystem"]:
        bad.append((e, "subsystem 与 sieve 不符"))
rep["fields_vs_sieve_bad"] = bad

# 2 delta vs 基线 coverage
bad2 = []
for d in DROWS:
    e = d["entry"]; p = PV.get(e)
    if not p:
        bad2.append((e, "基线缺行")); continue
    for col in ("subsystem", "name", "grade", "evidence_path", "n_sources", "conflict"):
        if d[col] != p[col]:
            bad2.append((e, "%s 与盘上不符: %r vs %r" % (col, d[col], p[col])))
rep["delta_vs_baseline_bad"] = bad2

# 3 evidence_path 首段可解析（相对 R14）
ev_bad = []
for d in DROWS:
    ev = d["evidence_path"]
    first = re.split(r"[;,]", ev)[0].strip()
    first = first.split("#")[0].strip()
    cands = [os.path.join(R14, first), os.path.join(R14, d["subsystem"] + "_" + first)]
    ok = any(os.path.exists(c) for c in cands)
    if not ok:
        ev_bad.append((d["entry"], first))
rep["evidence_unresolved"] = ev_bad

# 4 sieve 极性/overlap
pol = {}
for d in DROWS:
    s = SV[d["entry"]]
    pol[d["entry"]] = dict(polarity=s.get("verdict_polarity"),
                           overlap17=s.get("overlap_with_17(是/否)"),
                           overlap5=s.get("overlap_with_5(是/否)"),
                           has4=s.get("has_ring4_on_disk(是/否)"),
                           n_artifacts=s.get("n_supporting_artifacts"))
rep["sieve_flags"] = pol

# 5 每行 ④ 次数 & 结构
occ = {}
for d in DROWS:
    c4 = d["one_line_semantics"]
    occ[d["entry"]] = dict(n_ring4_witness=c4.count("④ 活表槽位见证"),
                           n_upgrade=c4.count("④升级句"),
                           n_d47=c4.count("D-47(A)"),
                           n_126=c4.count("§12.6"),
                           n_panel=c4.count("PANEL"),
                           n_123_yield=c4.count("§12.3 对该形态让位"),
                           n_bad_yiguo=c4.count("已过 §12.3"),
                           n_124=c4.count("§12.4"),
                           ends_with_disc=c4.rstrip().endswith("对应披露）"))
rep["col4_structure"] = occ

# 6 REPORT 样例 ④ 与 delta 逐字一致
rep_txt = io.open(os.path.join(B4, "REPORT.md"), encoding="utf-8").read()
dmap = {d["entry"]: d["one_line_semantics"] for d in DROWS}
samples = {}
for e in ("006CF430", "006C6680"):
    # 抓 REPORT 代码块里以「④ 活表槽位见证」开头的那一行
    m = re.search(r"```\s*\n(④ 活表槽位见证：.*?)\n\s*```", rep_txt, re.S)
    # 逐个样例块单独找
    blocks = re.findall(r"```\s*\n(④ 活表槽位见证：.*?)\n\s*```", rep_txt, re.S)
    samples[e] = None
allblocks = re.findall(r"```\s*\n(④ 活表槽位见证：.*?)\n\s*```", rep_txt, re.S)
rep["report_sample_blocks"] = len(allblocks)
rep["report_sample_matches"] = {}
for b in allblocks:
    hit = [e for e, c4 in dmap.items() if c4.endswith(b.strip()) or b.strip() in c4]
    rep["report_sample_matches"][b[:60]] = hit

# 7 REPORT 关键数字 vs 实测
rep["report_claims"] = {
    "says_cov_sha_412ED7E3": "412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1" in rep_txt,
    "says_cov_bytes_4097787": "4097787" in rep_txt or "4,097,787" in rep_txt,
    "says_005F4B10_minus_1": "005F4B10 剔除" in rep_txt,
    "says_lowest_addr_006F450D": "非最低地址命中 006F450D" in rep_txt or "非最低地址析构器 006F450D" in rep_txt,
}

json.dump(rep, io.open(os.path.join(HERE, "_final_cross.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(json.dumps(rep, ensure_ascii=False, indent=1)[:5000])
