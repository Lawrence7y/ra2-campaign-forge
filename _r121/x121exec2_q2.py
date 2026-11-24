#!/usr/bin/env python3
"""Q2: ppv stack slot recovery, QI-consumer call classification, ppv slot
consumption buckets. Writes x121exec2_q2.json.

Pipeline per site S (S = the `push imm32` instruction):
  A. look back for `push R` and, within 10 instructions before that push,
     a `lea R, [esp + K]`
  B. locate the QI call: first `call` in (S, S+64]
  C. after that call, scan up to 22 instructions for the first
     `mov P, dword ptr [esp + K]` where K matches exactly
  D. classify the first call after the QI call
"""
import json
import sys

import capstone

import x121exec2_core as C

X86 = capstone.x86
OUT = "/home/t628/projects/ra2-campaign-forge/_r121/x121exec2_q2.json"
BACK_WINDOW = 64        # bytes of context before a site we decode
BEFORE_PUSH_INSNS = 10  # lea must be within this many insns before the push
AFTER_SCAN_INSNS = 22   # ppv slot load search window
AFTER_CALL_WINDOW = 64  # first-call-after-QI search window


def ctx_before(binobj, site_va, nbytes=BACK_WINDOW, limit=64):
    """Decode the block ending exactly at site_va, newest last.

    Decoding backwards from a fixed earlier point is unreliable, so instead we
    decode a span that ends at the site and require the site to land exactly
    on an instruction boundary; the caller reports if it does not.
    """
    lo = site_va - nbytes
    recs = C.decode_flat(binobj, lo, nbytes + 16, limit=limit)
    idx = None
    for i, r in enumerate(recs):
        if r["va"] == site_va:
            idx = i
            break
    if idx is None:
        return None, recs
    return recs[max(0, idx - limit):idx], recs


def find_lea_esp(rec, reg):
    """`lea R, [esp + K]` (no index reg, scale 1) -> K or None."""
    if rec["mn"] != "lea":
        return None
    ops = rec["ops"]
    if len(ops) < 2:
        return None
    dst, src = ops[0], ops[1]
    if dst["type"] != X86.X86_OP_REG or dst.get("reg") != reg:
        return None
    if src["type"] != X86.X86_OP_MEM:
        return None
    if C.m_base(src) != X86.X86_REG_ESP:
        return None
    if C.m_index(src):
        return None
    return src["disp"] & 0xFFFFFFFF


def find_ppv_register(before, site_va):
    """Apply criterion A. Returns dict."""
    res = {"found": False, "reg": None, "K": None, "push_va": None,
           "lea_va": None, "lea_text": None, "push_text": None,
           "distance_insns": None, "note": None}
    if not before:
        res["note"] = "no decodable context ending at site"
        return res
    # The instruction immediately before the site must be `push R` to be the
    # ppv argument (ppv is pushed first, this last). We also allow any push R
    # in the last 3 instructions, taking the nearest one, and report which.
    for back in range(1, min(len(before), 4) + 1):
        cand = before[-back]
        if cand["mn"] == "push":
            ops = cand["ops"]
            if ops and ops[0]["type"] == X86.X86_OP_REG:
                reg = ops[0]["reg"]
                window = before[:-back]
                for dist, prev in enumerate(reversed(window), start=1):
                    if dist > BEFORE_PUSH_INSNS:
                        break
                    k = find_lea_esp(prev, reg)
                    if k is not None:
                        res.update({
                            "found": True, "reg": C.REG_NAME32.get(reg),
                            "K": k, "push_va": cand["va"],
                            "lea_va": prev["va"],
                            "lea_text": "%s %s" % (prev["mn"], prev["op"]),
                            "push_text": "%s %s" % (cand["mn"], cand["op"]),
                            "distance_insns": dist,
                            "push_back_index": back,
                        })
                        return res
                if res["note"] is None:
                    res["note"] = ("push %s at 0x%x but no lea %s,[esp+K] "
                                   "within %d insns before it"
                                   % (C.REG_NAME32.get(reg), cand["va"],
                                      C.REG_NAME32.get(reg), BEFORE_PUSH_INSNS))
    if res["note"] is None:
        res["note"] = "no push reg immediately before site"
    return res


def first_call_after(binobj, start_va, window=AFTER_CALL_WINDOW):
    recs = C.decode_flat(binobj, start_va, window + 16, limit=40)
    for r in recs:
        if r["va"] > start_va + window:
            return None, []
        if r["mn"] == "call":
            return r, recs
    return None, recs


def classify_call_site(rec, binobj):
    d = {"va": rec["va"], "text": "%s %s" % (rec["mn"], rec["op"]),
         "bytes": rec["bytes"]}
    ops = rec["ops"]
    if not ops:
        d["kind"] = "no-operand"
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
        d.update({"base": op["base_name"], "index": op["index_name"],
                  "disp": disp})
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
        if base in (X86.X86_REG_ESP, X86.X86_REG_EBP):
            d["kind"] = "stack-indirect"
            return d
        d["kind"] = "vtable"
        return d
    d["kind"] = "other"
    return d


def find_slot_load(recs_after, K, max_insns=AFTER_SCAN_INSNS):
    """First `mov P, [esp + K]` with K exactly equal, within max_insns."""
    scanned = 0
    seen = []
    for r in recs_after:
        if r["mn"] == "call":
            continue
        if scanned >= max_insns:
            break
        scanned += 1
        if r["mn"] in ("mov", "movzx", "movsx"):
            ops = r["ops"]
            if len(ops) == 2 and ops[0]["type"] == X86.X86_OP_REG \
                    and ops[1]["type"] == X86.X86_OP_MEM:
                m = ops[1]
                if C.m_base(m) == X86.X86_REG_ESP and not C.m_index(m) \
                        and (m["disp"] & 0xFFFFFFFF) == K:
                    return {"va": r["va"],
                            "text": "%s %s" % (r["mn"], r["op"]),
                            "dst": ops[0]["regname"], "K": K,
                            "insn_index": scanned}, scanned, seen
        seen.append("%08x %s %s" % (r["va"], r["mn"], r["op"]))
    return None, scanned, seen


def analyse_site(binobj, site, k_shift=0, trace=None):
    """One site's full Q2 analysis. k_shift shifts K for control 3c."""
    before, raw = ctx_before(binobj, site)
    out = {"site": site, "k_shift": k_shift}
    if before is None:
        out["context"] = "site not on a decodable boundary within window"
        return out
    out["insn"] = {"va": site, "bytes": raw[[r["va"] for r in raw].index(site)]["bytes"],
                   "mn": raw[[r["va"] for r in raw].index(site)]["mn"],
                   "op": raw[[r["va"] for r in raw].index(site)]["op"]}
    out["push_prev_3"] = ["%08x %s %s" % (r["va"], r["mn"], r["op"])
                          for r in before[-3:]]

    # ---- Q2.1 -------------------------------------------------------
    pp = find_ppv_register(before, site)
    out["ppv_reg"] = pp

    # ---- Q1.2 / Q2.3: the QI call ------------------------------------
    qi_call, after = first_call_after(binobj, site + 5)
    if qi_call is None:
        out["qi_call"] = None
        out["consumer"] = None
        out["bucket"] = "no-qi-call"
        return out
    out["qi_call"] = classify_call_site(qi_call, binobj)

    # ---- Q2.2: ppv slot consumer -------------------------------------
    if pp["found"]:
        K = (pp["K"] + k_shift) & 0xFFFFFFFF
        load, scanned, seen = find_slot_load(after, K)
        out["slot_K_used"] = K
        out["slot_load"] = load
        out["slot_load_scanned"] = scanned
        out["slot_load_seen"] = seen
    else:
        out["slot_K_used"] = None
        out["slot_load"] = None
        out["slot_load_scanned"] = 0
        out["slot_load_seen"] = []

    # ---- Q2.3: first call after the QI call --------------------------
    qi_end = qi_call["va"] + qi_call["size"]
    cons, cons_recs = first_call_after(binobj, qi_end)
    if cons is None:
        out["consumer"] = None
        out["bucket"] = "no-call-after-qi"
        out["consumer_plus8"] = None
        return out
    ci = classify_call_site(cons, binobj)
    out["consumer"] = ci
    out["consumer_gap_bytes"] = cons["va"] - qi_end
    out["bucket"] = ci["kind"]

    # ---- Q2.5: `call dword ptr [reg + 8]` within 8 insns after --------
    cons_end = cons["va"] + cons["size"]
    tail = C.decode_flat(binobj, cons_end, AFTER_CALL_WINDOW, limit=40)
    seen = 0
    hit = None
    for r in tail:
        if seen >= 8:
            break
        seen += 1
        if r["mn"] == "call" and len(r["ops"]) == 1 and \
                r["ops"][0]["type"] == X86.X86_OP_MEM:
            op = r["ops"][0]
            if C.m_base(op) and not C.m_index(op) and op["disp"] == 8:
                hit = {"va": r["va"], "text": "%s %s" % (r["mn"], r["op"]),
                       "insn_index": seen, "base": op["base_name"]}
                break
    out["consumer_plus8"] = hit
    return out


def main():
    b = C.Bin()
    sites = C.find_insn_sites(b, C.QI_ARG_VA)
    rows = [analyse_site(b, s) for s in sites]

    buckets = {}
    for r in rows:
        buckets[r.get("bucket")] = buckets.get(r.get("bucket"), 0) + 1
    found_reg = [r["site"] for r in rows if r["ppv_reg"]["found"]]
    no_reg = [{"site": r["site"], "why": r["ppv_reg"]["note"]}
              for r in rows if not r["ppv_reg"]["found"]]
    with_load = [r for r in rows if r.get("slot_load")]
    no_load = [{"site": r["site"], "K": r.get("slot_K_used"),
                "scanned": r.get("slot_load_scanned"),
                "seen": r.get("slot_load_seen")}
               for r in rows if r.get("slot_K_used") is not None
               and not r.get("slot_load")]

    iat_funcs = {}
    for r in rows:
        c = r.get("consumer") or {}
        if c.get("kind") == "iat":
            key = "%s!%s" % (c["dll"], c["func"])
            iat_funcs[key] = iat_funcs.get(key, 0) + 1

    res = {
        "image_base": b.image_base,
        "site_count": len(sites),
        "q2_1": {
            "ppv_reg_found": len(found_reg),
            "ppv_reg_not_found": len(no_reg),
            "not_found_detail": no_reg,
            "K_distribution": {},
        },
        "q2_2": {
            "slot_load_found": len(with_load),
            "slot_load_not_found": len(no_load),
            "not_found_detail": no_load,
            "dst_distribution": {},
        },
        "q2_3": {
            "bucket_distribution": buckets,
            "bucket_sum": sum(buckets.values()),
            "iat_consumer_functions": iat_funcs,
        },
        "rows": rows,
    }
    for r in rows:
        if r["ppv_reg"]["found"]:
            k = str(r["ppv_reg"]["K"])
            res["q2_1"]["K_distribution"][k] = \
                res["q2_1"]["K_distribution"].get(k, 0) + 1
        if r.get("slot_load"):
            d = r["slot_load"]["dst"]
            res["q2_2"]["dst_distribution"][d] = \
                res["q2_2"]["dst_distribution"].get(d, 0) + 1

    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)

    print("sites", len(sites))
    print("Q2.1 ppv reg found %d / %d" % (len(found_reg), len(sites)))
    print("     K dist:", json.dumps(res["q2_1"]["K_distribution"]))
    print("Q2.2 slot load found %d / %d" % (len(with_load), len(found_reg)))
    print("     dst dist:", json.dumps(res["q2_2"]["dst_distribution"]))
    print("Q2.3 consumer buckets:", json.dumps(buckets, sort_keys=True))
    print("     iat consumers:", json.dumps(iat_funcs, sort_keys=True))
    for r in no_reg:
        print("  no-reg 0x%08x %s" % (r["site"], r["why"]), flush=True)


if __name__ == "__main__":
    sys.exit(main())
