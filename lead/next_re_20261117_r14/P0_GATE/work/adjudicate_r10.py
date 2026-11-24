#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-GATE R14-R10 · 按发现通道分轨重算 A(vt_direct) / B(true_entry)。

A 轨：vftable 槽值即函数；判 A1..A4，取代 c1..c6。
B 轨：分支/前向反推入口；保留 c1..c6，c4b 体长门槛改为 >=2B 且以 ret/jmp 终结。
写域仅 P0_GATE；gamemd.exe 与所有输入只读；capstone skipdata=True。
"""
import os
import sys
import csv
import json
import re
import hashlib
import collections
import bisect

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adjudicate import (PE, Sweep, Atlas, md_new, predecessor, trailing_pad,
                        read_tsv, first_col_set, leaf_pattern, build_rel32_targets,
                        clean)

ROOT = r"D:\Project\ra2-campaign-forge"
R14 = os.path.join(ROOT, r"lead\next_re_20261117_r14")
OUT = os.path.join(R14, "P0_GATE")
EVID = os.path.join(OUT, "EVIDENCE")
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
OUTSIDE = os.path.join(R14, r"COVERAGE\coverage_outside_atlas.tsv")
COVERAGE = os.path.join(R14, r"COVERAGE\coverage.tsv")
PROBE = os.path.join(R14, r"COVERAGE\probe_and_data_entries.tsv")
TRUE_UNIFIED = os.path.join(R14, r"P0_CLOSE\TRUE_ENTRY_UNIFIED.tsv")
VT_ENTRIES = os.path.join(R14, r"P0_CLOSE\VT_DIRECT_ENTRIES.tsv")
VT_TABLES = os.path.join(R14, r"P0_CLOSE\vt_tables.tsv")
SHA_EXPECT = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
ITEMS_RANGES = [(0xA8EC7C, 0xA8EC80), (0xA8ECBC, 0xA8ECC0), (0xB0F4EC, 0xB0F4F0)]
DWORD_PROBE_N = 6
JT_SPAN = 0x1000
BODY_LIMIT = 4096
TERM_MN = {"ret", "retn", "retf", "jmp"}


def fmt_insn(i):
    text = (i.mnemonic + (" " + i.op_str if i.op_str else "")).strip() if i.id else ".byte 0x%02x" % i.bytes[0]
    return dict(addr=i.address, size=i.size, text=text,
                mnemonic=(i.mnemonic or ".byte"), op=i.op_str or "")


def disasm_head(pe, T, span=64, n=6):
    objs = list(md_new().disasm(pe.read(T, span), T))
    return [fmt_insn(i) for i in objs[:n]], objs


def body_termination(pe, T, limit=BODY_LIMIT):
    """从 T 线性解码，找首个 ret/jmp；返回 (found, end_addr, length, desc)。"""
    data = pe.read(T, min(limit, 65536))
    for i in md_new().disasm(data, T):
        if i.mnemonic in TERM_MN:
            f = fmt_insn(i)
            return True, i.address + i.size, (i.address + i.size - T), f["text"]
    return False, None, None, "no-ret/jmp-within-%d" % limit


def resync_boundary(pe, sw, T):
    md = md_new()
    for s in range(T - 15, T):
        if s < sw.lo:
            continue
        for i in md.disasm(pe.read(s, 16), s):
            if i.id and i.address + i.size == T and sw.index_of(s) >= 0:
                return True, "resync: %s @%08X+%d" % (i.mnemonic, s, i.size)
            break
    return False, "no-insn-ends-at-T"


def pointer_table_at(pe, T):
    ds = []
    for k in range(DWORD_PROBE_N):
        try:
            ds.append(pe.u32(T + 4 * k))
        except ValueError:
            return False, []
    n = sum(1 for d in ds if pe.in_text(d))
    span = max(ds) - min(ds) if n == len(ds) else -1
    dense = n == len(ds) and len(set(ds)) >= 5 and 0 <= span <= JT_SPAN
    return dense, ds


def col_valid(pe, col):
    d = pe.read(col, 16)
    if len(d) < 16:
        return False, "unreadable"
    sig, off, cd, tdp = struct_unpack("<IIII", d)
    if sig not in (0, 1):
        return False, "sig=%d" % sig
    if not (pe.imagebase <= tdp < pe.imagebase + pe.sizeofimage):
        return False, "td-out-of-image"
    td = pe.read(tdp + 8, 256)
    z = td.find(b"\0")
    nm = td[:z] if z > 0 else b""
    if not nm.startswith((b".?AV", b".?AU")):
        return False, "td-name=%r" % nm[:16]
    return True, "COL sig=%d TD=%s" % (sig, nm.decode("latin1", "replace"))


def struct_unpack(fmt, data):
    import struct
    return struct.unpack(fmt, data)


def a3_check_vtable(pe, T, slots, vt_tables, vt_starts):
    """slots: [(vt_addr, slot_idx)]。任一条通过即 A3=Y。"""
    if not slots:
        return False, "no-vt-slot-record", ""
    details = []
    for vt, idx in slots:
        rec = vt_tables.get(vt)
        if rec is None:
            details.append("%08X/%d:table-not-in-vt_tables" % (vt, idx))
            continue
        n = rec["n"]
        end = rec["end"]
        col = rec["col"]
        try:
            col_at_vt_minus_4 = pe.u32(vt - 4)
        except ValueError:
            details.append("%08X/%d:vt-4-unreadable" % (vt, idx))
            continue
        if col_at_vt_minus_4 != col:
            details.append("%08X/%d:vt-4=%08X != col=%08X" % (vt, idx, col_at_vt_minus_4, col))
            continue
        ok, why = col_valid(pe, col)
        if not ok:
            details.append("%08X/%d:bad-col(%s)" % (vt, idx, why))
            continue
        if end != vt + 4 * n:
            details.append("%08X/%d:end-mismatch" % (vt, idx))
            continue
        if not (0 <= idx < n):
            details.append("%08X/%d:slot-out-of-range" % (vt, idx))
            continue
        try:
            val = pe.u32(vt + 4 * idx)
        except ValueError:
            details.append("%08X/%d:slot-unreadable" % (vt, idx))
            continue
        if val != T:
            details.append("%08X/%d:slot-value=%08X" % (vt, idx, val))
            continue
        i = bisect.bisect_right(vt_starts, vt)
        nxt = vt_starts[i] if i < len(vt_starts) else None
        if nxt is not None and end > nxt - 4:
            details.append("%08X/%d:crosses-next-table-col-%08X" % (vt, idx, nxt - 4))
            continue
        try:
            after = pe.u32(end)
            if pe.in_text(after):
                details.append("%08X/%d:run-not-maximal-after=%08X" % (vt, idx, after))
                continue
        except ValueError:
            pass
        return True, "%08X/%d:%s" % (vt, idx, why), "%08X/%d" % (vt, idx)
    return False, ";".join(details), ""


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(EVID, exist_ok=True)
    pe = PE(EXE)
    if pe.sha256 != SHA_EXPECT or pe.imagebase != 0x400000:
        raise SystemExit("EXE identity mismatch")
    tlo, thi = pe.text_range()
    atlas = Atlas(ATLAS)
    sw = Sweep(pe, tlo, thi)
    outside = read_tsv(OUTSIDE)
    if len(outside) != 476:
        raise SystemExit("outside rows !=476")
    coverage = first_col_set(COVERAGE)
    probe = first_col_set(PROBE)
    rel32_targets = build_rel32_targets(pe, atlas, tlo, thi)

    vt_slots_by_target = collections.defaultdict(list)
    for r in read_tsv(VT_ENTRIES):
        vt_slots_by_target[int(r["target"], 16)].append((int(r["vt_addr"], 16), int(r["slot_idx"])))
    vt_tables = {}
    for r in read_tsv(VT_TABLES):
        vt_tables[int(r["vt_addr"], 16)] = dict(
            n=int(r["n_slots"]), end=int(r["end"], 16), col=int(r["col"], 16), cls=r["cls"])
    vt_starts = sorted(vt_tables)
    true_rows = read_tsv(TRUE_UNIFIED)
    true_set = {int(r["address"], 16) for r in true_rows if r.get("verdict") == "TRUE"}
    coverage_rows = read_tsv(COVERAGE)
    coverage_info = {r.get("entry", "").upper(): r for r in coverage_rows}
    all_vt_targets = set(vt_slots_by_target)
    outside_vt = {int(r["entry"], 16) for r in outside if r["source"] == "VT_DIRECT"}
    outside_true = {int(r["entry"], 16) for r in outside if r["source"] == "TRUE_ENTRY_UNIFIED"}
    already_targets = sorted(all_vt_targets - outside_vt)
    upstream_false = sorted(outside_true - true_set)
    upstream_false_rows = {int(r["address"], 16): r for r in true_rows if r.get("verdict") == "FALSE"}

    records = []
    for r in outside:
        addr_s = r["entry"].upper()
        T = int(addr_s, 16)
        source = "vt_direct" if r["source"] == "VT_DIRECT" else "true_entry"
        rail = "A" if source == "vt_direct" else "B"
        data = pe.read(T, 64)
        insns, objs = disasm_head(pe, T, 64, 6)
        first_text = "; ".join("%08X: %s" % (i["addr"], i["text"]) for i in insns)
        owner = atlas.owner(T)
        owner_s = ("%08X" % owner) if owner is not None else "none"
        hole_m = re.search(r"hole=([0-9A-Fa-f]{8})-([0-9A-Fa-f]{8})", r.get("note", ""))
        hole_s = ("%s-%s" % (hole_m.group(1).upper(), hole_m.group(2).upper())) if hole_m else "none"
        bt_found, bt_end, bt_len, bt_desc = body_termination(pe, T)
        tiny = "Y" if (bt_len is not None and bt_len < 16) else "N"
        first_e8eb = "Y" if data[0] in (0xE8, 0xE9, 0xEB) else "N"
        pad, pad_fill = trailing_pad(pe, T)
        pr = predecessor(pe, sw, T)
        jt, dwords = pointer_table_at(pe, T)
        in_probe = addr_s in probe
        in_vt = any(a <= T < b for a, b in [(int(x["vt_addr"], 16), int(x["end"], 16)) for x in read_tsv(VT_TABLES)]) if False else False
        # vtable 表体在 .rdata，T 在 .text；保留字段以明示未命中。
        in_items = any(a <= T < b for a, b in ITEMS_RANGES)
        data_cross = bool(jt or in_probe or in_items or in_vt)

        a1 = a2 = a3 = a4 = None
        a2_via = a3_detail = chosen_slot = ""
        b_baseline = "NA"
        if rail == "A":
            a1 = pe.in_text(T)
            # R14-R10-FIX：撤下 linear-sweep-start，改用有区分力的前驱形态。
            a2 = pr["kind"] in ("nop", "int3", "ret", "jmp")
            a2_via = "pred=%s(%s); sweep-start-not-evidence" % (pr["kind"], pr["desc"])
            if data_cross:
                a2 = False
                a2_via += "+DATA_CROSS(jump_table=%s,probe=%s,items=%s)" % (jt, in_probe, in_items)
            a3, a3_detail, chosen_slot = a3_check_vtable(
                pe, T, vt_slots_by_target.get(T, []), vt_tables, vt_starts)
            a4 = addr_s not in coverage
            all_ok = a1 and a2 and a3 and a4
            verdict = "FUNC" if all_ok else "NOT_FUNC"
            if not all_ok:
                if not a4:
                    subkind = "ALREADY_IN_COVERAGE"
                elif not a2:
                    subkind = "mid_instruction"
                elif not a3:
                    subkind = "bad_vtable_parse"
                else:
                    subkind = "bad_vtable_parse"  # A1 失败在当前输入下不可能
            else:
                subkind = ""
            c1 = c2 = c3 = c4 = c5 = c6 = "NA"
            sem1 = "Y" if T in vt_slots_by_target else "N"
            sem2 = "Y" if T in rel32_targets else "N"
            sem3 = "Y" if leaf_pattern(data) else "N"
            c4a = ("Y" if (data[0] == 0x55 or data[:2] in (b"\x83\xec", b"\x81\xec")) else "N")
            c4b = "NA"
            evidence = " | ".join([
                "rail=A", "A1=%s" % ("Y" if a1 else "N"),
                "A2=%s(%s)" % ("Y" if a2 else "N", a2_via),
                "A2_baseline=sweep-start-34.7pct-4B/36.5pct-16B/midprev-78.6pct-NOT-USED",
                "A3=%s(%s)" % ("Y" if a3 else "N", a3_detail),
                "A4=%s" % ("Y" if a4 else "N"),
                "grade_slot=[已证] slot value", "grade_pred=[已证] predecessor-form",
                "grade_A3=[已证] table-boundary-input-restatement",
                "grade_semantic=[静态推断] slot-value-as-function-entry",
                "slot=%s" % (chosen_slot or "none"),
                "tiny=%s" % tiny, "first_byte_E8_E9_EB=%s" % first_e8eb,
                "body_len=%s" % (bt_len if bt_len is not None else "none"),
                "body_end=%s" % bt_desc,
                "dwords=%s" % ",".join("%08X" % d for d in dwords),
                "pointer_table=%s" % ("Y" if jt else "N"),
                "data_cross=%s" % ("Y" if data_cross else "N"),
                "atlas_owner=%s" % owner_s, "atlas_hole=%s" % hole_s,
                "prev=%s(%s,via=%s)" % (pr["kind"], pr["desc"], pr["via"]),
                "source_note=%s" % clean(r.get("note", "")),
            ])
        else:
            c1 = (T % 16 == 0)
            c2 = data[0] not in (0xE8, 0xE9, 0xEB)
            c3 = pr["kind"] in ("nop", "ret", "jmp", "int3")
            c4a_bool = (data[0] == 0x55 or data[:2] in (b"\x83\xec", b"\x81\xec"))
            sem1 = "Y" if T in vt_slots_by_target else "N"
            sem2 = "Y" if T in rel32_targets else "N"
            sem3 = "Y" if leaf_pattern(data) else "N"
            sem_any = sem1 == "Y" or sem2 == "Y" or sem3 == "Y"
            body_ok = bool(bt_found and bt_len is not None and bt_len >= 2)
            c4b_bool = bool(c1 and c2 and c3 and body_ok and sem_any)
            c4_bool = c4a_bool or c4b_bool
            c5_bool = not (jt or in_probe)
            c6_bool = pe.in_text(T) and not in_items and not in_probe and not in_vt
            c1_s = "Y" if c1 else "N"
            c2_s = "Y" if c2 else "N"
            c3_s = "Y" if c3 else "N"
            c4_s = "Y" if c4_bool else "N"
            c5_s = "Y" if c5_bool else "N"
            c6_s = "Y" if c6_bool else "N"
            c4a = "Y" if c4a_bool else "N"
            c4b = "Y" if c4b_bool else "N"
            all_ok = all((c1, c2, c3, c4_bool, c5_bool, c6_bool))
            verdict = "FUNC" if all_ok else "NOT_FUNC"
            if all_ok:
                subkind = ""
            elif not c2:
                subkind = "call_site" if data[0] == 0xE8 else "jump_target"
            elif not c5_bool:
                subkind = "jump_table"
            elif not c6_bool:
                subkind = "data"
            elif not c1 or not c3:
                subkind = "internal_label"
            elif not c4_bool:
                subkind = "stub" if not body_ok else "data"
            else:
                subkind = ""
            if verdict == "NOT_FUNC" and not subkind:
                verdict = "UNDECIDABLE"
            b_baseline = "UPSTREAM_C5_FALSE" if T in upstream_false else "R14R10_B_TRUE"
            evidence = " | ".join([
                "rail=B", "T%%16=%d" % (T % 16), "op=%02X" % data[0],
                "B_baseline=%s" % b_baseline,
                "grade_byte=[已证] direct-bytes/capstone",
                "grade_c4b_semantic=[静态推断] semantic-pattern",
                "pad=%d*%s" % (pad, pad_fill),
                "prev=%s(%s,via=%s)" % (pr["kind"], pr["desc"], pr["via"]),
                "c4a=%s" % c4a, "c4b=%s" % c4b,
                "c4b_sem=%s" % "+".join(x for x, v in (("1", sem1), ("2", sem2), ("3", sem3)) if v == "Y"),
                "body_len=%s" % (bt_len if bt_len is not None else "none"),
                "body_end=%s" % bt_desc,
                "tiny=%s" % tiny,
                "dwords=%s" % ",".join("%08X" % d for d in dwords),
                "atlas_owner=%s" % owner_s, "atlas_hole=%s" % hole_s,
                "probe_exact_hit=%s" % ("Y" if in_probe else "N"),
                "rel32_from_fn=%s" % sem2,
                "source_note=%s" % clean(r.get("note", "")),
            ])
            c1, c2, c3, c4, c5, c6 = c1_s, c2_s, c3_s, c4_s, c5_s, c6_s

        records.append(dict(
            addr=addr_s, source=source, c1=c1, c2=c2, c3=c3, c4=c4, c5=c5, c6=c6,
            verdict=verdict, subkind=subkind, first_insn=first_text,
            prev_byte=("%02X" % pe.read(T - 1, 1)[0]) if T > tlo else "?",
            inside_atlas_owner=owner_s, evidence=evidence,
            rail=rail, a1="Y" if a1 else ("N" if a1 is False else "NA"),
            a2="Y" if a2 else ("N" if a2 is False else "NA"),
            a3="Y" if a3 else ("N" if a3 is False else "NA"),
            a4="Y" if a4 else ("N" if a4 is False else "NA"),
            a2_via=a2_via, a3_detail=a3_detail, chosen_slot=chosen_slot,
            tiny=tiny, first_e8eb=first_e8eb, body_len=(bt_len if bt_len is not None else "none"),
            body_end=bt_desc, c4a=c4a, c4b=c4b,
            c4b_sem="+".join(x for x, v in (("1", sem1), ("2", sem2), ("3", sem3)) if v == "Y"),
            sem1=sem1, sem2=sem2, sem3=sem3,
            dwords=",".join("%08X" % d for d in dwords),
            pointer_table="Y" if jt else "N", data_cross="Y" if data_cross else "N",
            atlas_hole=hole_s, prev_desc=pr["desc"], note=clean(r.get("note", "")),
            grade_slot=("[已证] slot value" if rail == "A" else "NA"),
            grade_pred=("[已证] predecessor-form" if rail == "A" else "NA"),
            grade_A3=("[已证] table-boundary-input-restatement" if rail == "A" else "NA"),
            grade_semantic=("[静态推断] slot-value-as-function-entry" if rail == "A" else "NA"),
            grade_byte=("[已证] direct-bytes/capstone" if rail == "B" else "NA"),
            grade_c4b_semantic=("[静态推断] semantic-pattern" if rail == "B" else "NA"),
            b_baseline=b_baseline,
        ))

    # ---- outputs ----
    cols = ["addr", "source", "c1", "c2", "c3", "c4", "c5", "c6", "verdict",
            "subkind", "first_insn", "prev_byte", "inside_atlas_owner", "evidence"]
    with open(os.path.join(OUT, "ENTRY_ADJUDICATION.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for rec in records:
            w.writerow({k: rec[k] for k in cols})
    full_cols = cols + ["rail", "a1", "a2", "a3", "a4", "a2_via", "a3_detail",
                        "chosen_slot", "tiny", "first_e8eb", "body_len", "body_end",
                        "c4a", "c4b", "c4b_sem", "sem1", "sem2", "sem3",
                        "grade_slot", "grade_pred", "grade_A3", "grade_semantic",
                        "grade_byte", "grade_c4b_semantic", "b_baseline",
                        "dwords", "pointer_table", "data_cross", "atlas_hole",
                        "prev_desc", "note"]
    with open(os.path.join(EVID, "ENTRY_ADJUDICATION_FULL.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=full_cols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for rec in records:
            w.writerow({k: rec[k] for k in full_cols})
    with open(os.path.join(EVID, "A_RAIL_DETAILS.tsv"), "w", encoding="utf-8", newline="") as f:
        acols = ["addr", "source", "a1", "a2", "a3", "a4", "a2_via", "a3_detail",
                 "chosen_slot", "tiny", "first_e8eb", "body_len", "verdict", "subkind",
                 "grade_slot", "grade_pred", "grade_A3", "grade_semantic", "evidence"]
        w = csv.DictWriter(f, fieldnames=acols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for rec in records:
            if rec["rail"] == "A":
                w.writerow({k: rec[k] for k in acols})

    rail = collections.defaultdict(collections.Counter)
    subkinds = collections.defaultdict(collections.Counter)
    for rec in records:
        rail[rec["rail"]][rec["verdict"]] += 1
        if rec["verdict"] == "NOT_FUNC":
            subkinds[rec["rail"]][rec["subkind"]] += 1
    verdicts = collections.Counter(rec["verdict"] for rec in records)
    a_rows = [r for r in records if r["rail"] == "A"]
    b_rows = [r for r in records if r["rail"] == "B"]
    already = len(already_targets)
    a_data_cross = sum(1 for r in a_rows if r["data_cross"] == "Y")
    a_tiny = sum(1 for r in a_rows if r["tiny"] == "Y")
    a_e8eb = sum(1 for r in a_rows if r["first_e8eb"] == "Y")
    a2_pred_kinds = collections.Counter(
        r["a2_via"].split("pred=", 1)[1].split("(", 1)[0] if "pred=" in r["a2_via"] else "unknown"
        for r in a_rows)
    b_baseline_func = len(outside_true & true_set)
    b_baseline_not = len(upstream_false)
    b_c_pass = {c: sum(1 for r in b_rows if r[c] == "Y") for c in ("c1", "c2", "c3", "c4", "c5", "c6")}
    b_c4a = sum(1 for r in b_rows if r["c4a"] == "Y")
    b_c4b = sum(1 for r in b_rows if r["c4b"] == "Y")
    b_both = sum(1 for r in b_rows if r["c4a"] == "Y" and r["c4b"] == "Y")
    sem_buckets = collections.Counter()
    for r in b_rows:
        if r["c4b"] == "Y":
            sem_buckets[r["c4b_sem"] or "none"] += 1
    addrs = {r["addr"] for r in records}
    inter_cov = len(addrs & coverage)
    inter_probe = len(addrs & probe)
    atlas_hits = sum(1 for r in records if r["inside_atlas_owner"] != "none")

    stale = os.path.join(EVID, "c2_fail_details.txt")
    if os.path.exists(stale):
        os.remove(stale)
    with open(os.path.join(EVID, "ALREADY_IN_COVERAGE.tsv"), "w", encoding="utf-8", newline="") as f:
        cols = ["addr", "source_pool", "reason", "coverage_subsystem", "coverage_name", "vt_slots"]
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for T in already_targets:
            a = "%08X" % T
            ci = coverage_info.get(a, {})
            w.writerow(dict(addr=a, source_pool="VT_DIRECT_ENTRIES.tsv",
                            reason="A4 fail: already in coverage.tsv; 413-2=411",
                            coverage_subsystem=ci.get("subsystem", ""),
                            coverage_name=ci.get("name", ""),
                            vt_slots=",".join("%s/%s" % x for x in vt_slots_by_target.get(T, []))))
    with open(os.path.join(EVID, "B_RAIL_C5_EXCLUDED.tsv"), "w", encoding="utf-8", newline="") as f:
        cols = ["addr", "baseline", "upstream_verdict", "suppressed_by", "main_verdict_note"]
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for T in upstream_false:
            ur = upstream_false_rows.get(T, {})
            ev = ur.get("evidence", "")
            m = re.search(r"c5-suppressed-by=([0-9A-Fa-f]{8})(?:\(d=(\d+)\))?", ev)
            w.writerow(dict(addr="%08X" % T, baseline="R14-R10 B NOT_FUNC",
                            upstream_verdict=ur.get("verdict", "FALSE"),
                            suppressed_by=("%s/d=%s" % m.groups()) if m else "unknown",
                            main_verdict_note="main TSV keeps FUNC per audit; not counted in B=60 baseline"))
    with open(os.path.join(EVID, "R14_R10_NOT_FUNC_DETAILS.txt"), "w", encoding="utf-8") as f:
        f.write("# R14-R10 NOT_FUNC / ALREADY_IN_COVERAGE 明细\n")
        for r in records:
            if r["verdict"] != "FUNC":
                f.write("%s\t%s\t%s\t%s\t%s\n" %
                        (r["addr"], r["rail"], r["verdict"], r["subkind"], r["evidence"]))
        f.write("A轨 NOT_FUNC=%d；B轨 NOT_FUNC=%d\n" %
                (rail["A"].get("NOT_FUNC", 0), rail["B"].get("NOT_FUNC", 0)))
    with open(os.path.join(EVID, "semantic_buckets.tsv"), "w", encoding="utf-8") as f:
        f.write("rail\tbucket\tcount\n")
        for k, v in sorted(sem_buckets.items()):
            f.write("B\t%s\t%d\n" % (k, v))
    with open(os.path.join(EVID, "inputs.sha256.txt"), "w", encoding="utf-8") as f:
        for p in (EXE, OUTSIDE, COVERAGE, PROBE, TRUE_UNIFIED, VT_ENTRIES, VT_TABLES, ATLAS):
            f.write("%s  %s\n" % (hashlib.sha256(open(p, "rb").read()).hexdigest().upper(),
                                  os.path.relpath(p, ROOT)))
    stdout = [
        "R14-R10 rail=%s" % json.dumps({k: dict(v) for k, v in rail.items()}, sort_keys=True),
        "subkinds=%s" % json.dumps({k: dict(v) for k, v in subkinds.items()}, sort_keys=True),
        "verdicts=%s" % json.dumps(dict(verdicts), sort_keys=True),
        "ALREADY_IN_COVERAGE=%d %s" % (already, ",".join("%08X" % x for x in already_targets)),
        "A_data_cross=%d A_tiny=%d A_first_E8_E9_EB=%d" % (a_data_cross, a_tiny, a_e8eb),
        "A2_pred_kinds=%s (sweep-start removed)" % json.dumps(dict(a2_pred_kinds), sort_keys=True),
        "B_baseline_FUNC=%d B_baseline_NOT_FUNC=%d (upstream FALSE: %s)" %
        (b_baseline_func, b_baseline_not, ",".join("%08X" % x for x in upstream_false)),
        "B_c_pass=%s B_c4a=%d B_c4b=%d B_both=%d" %
        (json.dumps(b_c_pass, sort_keys=True), b_c4a, b_c4b, b_both),
        "B_sem_buckets=%s" % json.dumps(dict(sem_buckets), sort_keys=True),
        "intersection_coverage=%d intersection_probe=%d atlas_owner_hits=%d" %
        (inter_cov, inter_probe, atlas_hits),
        "capstone=%s skipdata=True .text=[%08X,%08X)" % (__import__("capstone").__version__, tlo, thi),
        "vt_tables=%d vt_targets=%d rel32_from_fn_targets=%d" %
        (len(vt_tables), len(vt_slots_by_target), len(rel32_targets)),
    ]
    open(os.path.join(EVID, "RECOMPUTE_STDOUT.txt"), "w", encoding="utf-8").write("\n".join(stdout) + "\n")
    counts = dict(
        rail={k: dict(v) for k, v in rail.items()}, subkinds={k: dict(v) for k, v in subkinds.items()},
        verdicts=dict(verdicts), already_in_coverage=already,
        already_in_coverage_addrs=["%08X" % x for x in already_targets],
        A_data_cross=a_data_cross, A_tiny=a_tiny, A_first_E8_E9_EB=a_e8eb,
        A2_pred_kinds=dict(a2_pred_kinds), A2_sweep_start_used=False,
        B_baseline_FUNC=b_baseline_func, B_baseline_NOT_FUNC=b_baseline_not,
        B_c5_excluded=["%08X" % x for x in upstream_false],
        B_c_pass=b_c_pass, B_c4a=b_c4a, B_c4b=b_c4b, B_both=b_both,
        B_sem_buckets=dict(sem_buckets), intersection_coverage=inter_cov,
        intersection_probe=inter_probe, atlas_owner_hits=atlas_hits,
        capstone_version=__import__("capstone").__version__,
        text_lo="%08X" % tlo, text_hi="%08X" % thi, exe_sha256=pe.sha256,
        vt_tables=len(vt_tables), vt_distinct_targets=len(vt_slots_by_target),
        rel32_from_fn_targets=len(rel32_targets), true_rows_in_unified=len(true_set),
    )
    json.dump(counts, open(os.path.join(EVID, "counts.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("\n".join(stdout))


if __name__ == "__main__":
    main()
