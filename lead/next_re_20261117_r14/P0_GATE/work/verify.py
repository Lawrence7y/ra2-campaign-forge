#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R14-R10 自检：重读二进制、vftable、主表，确认 A/B 分轨结果。写域仅 P0_GATE。"""
import os
import sys
import csv
import json
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from adjudicate import PE, Sweep, first_col_set, predecessor  # noqa: E402
from adjudicate_r10 import a3_check_vtable  # noqa: E402

ROOT = r"D:\Project\ra2-campaign-forge"
R14 = os.path.join(ROOT, r"lead\next_re_20261117_r14")
OUT = os.path.join(R14, "P0_GATE")
EVID = os.path.join(OUT, "EVIDENCE")
MAIN = os.path.join(OUT, "ENTRY_ADJUDICATION.tsv")
FULL = os.path.join(EVID, "ENTRY_ADJUDICATION_FULL.tsv")
COUNTS = os.path.join(EVID, "counts.json")
COVERAGE = os.path.join(R14, r"COVERAGE\coverage.tsv")
PROBE = os.path.join(R14, r"COVERAGE\probe_and_data_entries.tsv")
VT_ENTRIES = os.path.join(R14, r"P0_CLOSE\VT_DIRECT_ENTRIES.tsv")
VT_TABLES = os.path.join(R14, r"P0_CLOSE\vt_tables.tsv")
SHA_EXPECT = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"


def rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_tsv(path):
    return rows(path)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    log = []
    errors = []

    def ck(cond, msg):
        if cond:
            log.append("PASS  " + msg)
        else:
            errors.append("FAIL  " + msg)

    c = json.load(open(COUNTS, encoding="utf-8"))
    main_rows = rows(MAIN)
    full_rows = rows(FULL)
    by = {r["addr"]: r for r in full_rows}

    ck(len(main_rows) == 476 and len(full_rows) == 476, "主表/FULL 均 476 行")
    ck(len({r["addr"] for r in main_rows}) == 476, "476 地址唯一")
    ck(collections.Counter(r["source"] for r in main_rows) ==
       collections.Counter({"vt_direct": 411, "true_entry": 65}), "source = A411 + B65")
    ck(set(by) == {r["addr"] for r in main_rows}, "MAIN/FULL 地址集合一致")

    pe = PE(pe_path := os.path.join(ROOT, r"ra2youli\gamemd.exe"))
    ck(pe.sha256 == SHA_EXPECT, "EXE SHA-256 未变")
    lo, hi = pe.text_range()
    sw = Sweep(pe, lo, hi)

    coverage = first_col_set(COVERAGE)
    probe = first_col_set(PROBE)
    ck(len({r["addr"] for r in main_rows} & coverage) == 0, "与 coverage.tsv 交集=0")
    ck(len({r["addr"] for r in main_rows} & probe) == 0, "与 probe_and_data_entries.tsv 交集=0")
    ck(all(r["inside_atlas_owner"] == "none" for r in main_rows), "atlas 函数区间包含命中=0")

    vt_slots = collections.defaultdict(list)
    for r in read_tsv(VT_ENTRIES):
        vt_slots[int(r["target"], 16)].append((int(r["vt_addr"], 16), int(r["slot_idx"])))
    vt_tables = {}
    for r in read_tsv(VT_TABLES):
        vt_tables[int(r["vt_addr"], 16)] = dict(n=int(r["n_slots"]), end=int(r["end"], 16),
                                                 col=int(r["col"], 16), cls=r["cls"])
    vt_starts = sorted(vt_tables)

    a_rows = [r for r in full_rows if r["rail"] == "A"]
    b_rows = [r for r in full_rows if r["rail"] == "B"]
    ck(len(a_rows) == 411 and len(b_rows) == 65, "A/B 行数 411/65")
    a_errors = []
    for r in a_rows:
        T = int(r["addr"], 16)
        a1 = lo <= T < hi
        pr = predecessor(pe, sw, T)
        a2 = pr["kind"] in ("nop", "int3", "ret", "jmp")
        a3, detail, slot = a3_check_vtable(pe, T, vt_slots.get(T, []), vt_tables, vt_starts)
        a4 = r["addr"] not in coverage
        if not (a1 and a2 and a3 and a4):
            a_errors.append("%s a1=%s a2=%s a3=%s(%s) a4=%s" % (r["addr"], a1, a2, a3, detail, a4))
        if any(r[k] != "Y" for k in ("a1", "a2", "a3", "a4")):
            a_errors.append("%s FULL A flags not all Y" % r["addr"])
        if r["data_cross"] != "N" or r["pointer_table"] != "N":
            a_errors.append("%s A data-like cross" % r["addr"])
        if r["subkind"] in ("stub", "call_site"):
            a_errors.append("%s old-rail subkind leaked" % r["addr"])
        if any(r[k] != "NA" for k in ("c1", "c2", "c3", "c4", "c5", "c6")):
            a_errors.append("%s c1..c6 not NA on A rail" % r["addr"])
        if "linear-sweep-start" in r["evidence"]:
            a_errors.append("%s sweep-start still used as evidence" % r["addr"])
        if (r["grade_slot"] != "[已证] slot value" or
                r["grade_pred"] != "[已证] predecessor-form" or
                r["grade_semantic"] != "[静态推断] slot-value-as-function-entry"):
            a_errors.append("%s grade mismatch" % r["addr"])
    ck(not a_errors, "A 轨 A1–A4 独立复算全过（前 %d 例：%s）" %
       (min(3, len(a_errors)), "; ".join(a_errors[:3])))

    b_errors = []
    for r in b_rows:
        if r["verdict"] != "FUNC" or any(r[k] != "Y" for k in ("c1", "c2", "c3", "c4", "c5", "c6")):
            b_errors.append(r["addr"])
        if r["grade_byte"] != "[已证] direct-bytes/capstone" or \
                r["grade_c4b_semantic"] != "[静态推断] semantic-pattern":
            b_errors.append("%s grade mismatch" % r["addr"])
    ck(not b_errors, "B 轨 65 条 c1–c6 全 Y 且 FUNC（失败 %d）" % len(b_errors))

    ck(all(r["verdict"] == "FUNC" for r in main_rows), "全池 verdict=FUNC")
    ck(not any(r["subkind"] in ("stub", "call_site") for r in main_rows), "stub/call_site 已消失")
    ck(c["already_in_coverage"] == 2 and c["already_in_coverage_addrs"] == ["004F8440", "00535E50"],
       "ALREADY_IN_COVERAGE=2 且点名 004F8440/00535E50")
    ck(c["B_baseline_FUNC"] == 60 and c["B_baseline_NOT_FUNC"] == 5,
       "B 轨口径 60 FUNC / 5 上游 c5 FALSE")
    ck(c["B_c5_excluded"] == ["00632A20", "00632B20", "00632B70", "00690AE0", "00796ED0"],
       "B 轨 5 条上游 FALSE 地址已登记")
    ck(c["A2_sweep_start_used"] is False and sum(c["A2_pred_kinds"].values()) == 411,
       "A2 已换成前驱形态且 sweep-start 不作为证据（nop %d / ret %d）" %
       (c["A2_pred_kinds"].get("nop", 0), c["A2_pred_kinds"].get("ret", 0)))
    ck(c["verdicts"].get("UNDECIDABLE", 0) == 0, "UNDECIDABLE=0")
    ck(c["rail"]["A"]["FUNC"] == 411 and c["rail"]["A"].get("NOT_FUNC", 0) == 0,
       "counts A轨 411 FUNC / 0 NOT_FUNC")
    ck(c["rail"]["B"]["FUNC"] == 65 and c["rail"]["B"].get("NOT_FUNC", 0) == 0,
       "counts B轨 65 FUNC / 0 NOT_FUNC")
    ck(c["B_c4a"] == 65 and c["B_c4b"] == 4, "B 轨 c4a=65 / c4b=4")
    ck(c["A_tiny"] == 144 and c["A_first_E8_E9_EB"] == 10, "A 轨 tiny=144 / E8-E9-EB=10（仅形态注记）")
    ck(c["vt_tables"] == 1214, "vftable 自定界表数=1214（未读 vtables_v2.json）")

    text = "\n".join(log + errors) + "\n"
    open(os.path.join(EVID, "VERIFY.txt"), "w", encoding="utf-8").write(text)
    print(text, end="")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
