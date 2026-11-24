#!/usr/bin/env python3
"""Q1: locate push-imm32 sites for the QI riid constant and classify the
first call within 64 bytes after each site.

Output: x121exec2_q1.json
"""
import json
import struct
import sys

import capstone

import x121exec2_core as C

OUT = "/home/t628/projects/ra2-campaign-forge/_r121/x121exec2_q1.json"
X86 = capstone.x86


def classify_call(rec, binobj):
    """Classify a flattened call record into the Q1 buckets."""
    d = {"va": rec["va"], "text": "%s %s" % (rec["mn"], rec["op"]),
         "bytes": rec["bytes"]}
    ops = rec["ops"]
    if rec["mn"] != "call" or not ops:
        d["kind"] = "not-call"
        return d
    op = ops[0]
    if op["type"] == X86.X86_OP_IMM:
        d["kind"] = "rel"
        d["target"] = op["imm"]
        return d
    if op["type"] == X86.X86_OP_REG:
        d["kind"] = "reg"
        d["reg"] = op["regname"]
        return d
    if op["type"] == X86.X86_OP_MEM:
        base, idx, disp = C.m_base(op), C.m_index(op), op["disp"]
        d["base"] = op["base_name"]
        d["index"] = op["index_name"]
        d["disp"] = disp
        if C.m_is_abs(op):
            va = disp & 0xFFFFFFFF
            d["abs"] = va
            hit = binobj.iat_lookup(va)
            if hit:
                d["kind"] = "iat"
                d["dll"] = hit["dll"]
                d["func"] = hit["func"]
            else:
                d["kind"] = "not-iat"
                sec = binobj.sec_of(va)
                d["not_iat_section"] = sec["name"] if sec else None
            return d
        d["kind"] = "mem"
        return d
    d["kind"] = "other"
    return d


def first_call_within(binobj, site_va, window=64):
    """First call whose start lies in (site_va, site_va+window]."""
    recs = C.decode_flat(binobj, site_va + 5, window)
    for r in recs:
        if r["va"] > site_va + window:
            return None
        if r["mn"] == "call":
            return r
    return None


def run_scan(binobj, imm, window=64, min_off=0):
    sites = C.find_insn_sites(binobj, imm, min_offset=min_off)
    rows = []
    for s in sites:
        one = C.decode_flat(binobj, s, 16, limit=1)
        row = {"site": s, "insn": one[0] if one else None}
        call = first_call_within(binobj, s, window)
        if call is None:
            row["call"] = None
            row["bucket"] = "no-call-in-64B"
        else:
            info = classify_call(call, binobj)
            row["call"] = info
            row["bucket"] = info["kind"]
        rows.append(row)
    buckets = {}
    for r in rows:
        buckets[r["bucket"]] = buckets.get(r["bucket"], 0) + 1
    return sites, rows, buckets


def main():
    b = C.Bin()
    sites, rows, buckets = run_scan(b, C.QI_ARG_VA)

    # alignment: is each 0x68 offset a real instruction start?
    from array import array
    starts = b.sweep_starts()
    start_set = set(starts)
    aligned = [s for s in sites if s in start_set]
    unaligned = [s for s in sites if s not in start_set]

    # controls
    sites_ctrl, _rc, buck_ctrl = run_scan(b, C.CTRL_ARG_VA)
    sites_alt, rows_alt, buck_alt = run_scan(b, C.ALT_ARG_VA)
    # 3b: same criteria starting from site+1
    sites_plus1, _rp1, buck_plus1 = run_scan(b, C.QI_ARG_VA, min_off=1)

    n_le_anywhere = b.buf.count(struct.pack("<I", C.QI_ARG_VA))

    res = {
        "binary": b.path,
        "image_base": b.image_base,
        "sections_measured": b.sections,
        "iat_slot_count": len(b.iat),
        "q1": {
            "imm": C.QI_ARG_VA,
            "site_count": len(sites),
            "sites": [hex(x) for x in sites],
            "instruction_aligned_sites": [hex(x) for x in aligned],
            "not_instruction_start_sites": [hex(x) for x in unaligned],
            "buckets": buckets,
            "bucket_sum": sum(buckets.values()),
            "rows": rows,
        },
        "controls": {
            "pos_imm": C.QI_ARG_VA, "pos_site_count": len(sites),
            "3a_imm_7f7c81_site_count": len(sites_ctrl),
            "3a_sites": [hex(x) for x in sites_ctrl],
            "3a_buckets": buck_ctrl,
            "3b_from_site_plus1_site_count": len(sites_plus1),
            "3b_sites": [hex(x) for x in sites_plus1],
            "3d_imm_7f7c90_site_count": len(sites_alt),
            "3d_sites": [hex(x) for x in sites_alt],
            "3d_buckets": buck_alt,
            "3d_rows": rows_alt,
            "le32_of_imm_in_whole_file": n_le_anywhere,
        },
    }
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)

    print("Q1 imm=0x%x sites=%d aligned=%d unaligned=%d"
          % (C.QI_ARG_VA, len(sites), len(aligned), len(unaligned)))
    print("Q1 buckets:", json.dumps(buckets, sort_keys=True))
    print("3a 0x7f7c81 -> %d ; 3b site+1 pattern -> %d ; 3d 0x7f7c90 -> %d"
          % (len(sites_ctrl), len(sites_plus1), len(sites_alt)))
    print("3d buckets:", json.dumps(buck_alt, sort_keys=True))
    print("le32 of imm anywhere in file:", n_le_anywhere)
    for r in rows:
        print("  0x%08x %-9s %s" % (r["site"], r["bucket"],
                                    r["call"]["text"] if r["call"] else "-"),
              flush=True)


if __name__ == "__main__":
    sys.exit(main())
