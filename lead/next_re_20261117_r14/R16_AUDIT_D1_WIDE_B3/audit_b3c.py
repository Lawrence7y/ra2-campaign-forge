#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B3 step C: hardening evidence dump (the three 加严 items).

Reuses audit_b3a.py's loader (paste of the pre-row-loop section) so every fact
here is re-derived from the binary, not read from the executor's artefacts.
Writes _hardening.txt
"""
import os
import sys
import json
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, "audit_b3a.py"), encoding="utf-8").read()
HEAD = SRC.split("# ------------------------------------------------------------------- inputs")[0]
g = {"__file__": os.path.join(HERE, "audit_b3a.py"), "__name__": "harden"}
exec(compile(HEAD, os.path.join(HERE, "audit_b3a.py"), "exec"), g)
pe = g["pe"]
dis = g["disasm_from"]
H = g["H"]
ATL = g["ATL"]
func_extent = g["func_extent"]
host_of = g["host_of"]
classify_ip = g["classify_ip"]
install_points = g["install_points"]
is_dtor_shaped_range = g["is_dtor_shaped_range"]
CALLS = g["CALLS"]
DATA_LO, DATA_HI = g["DATA_LO"], g["DATA_HI"]

FACTS = json.load(open(os.path.join(HERE, "_facts.json"), encoding="utf-8"))
ROWS = {r["entry"]: r for r in FACTS["rows"]}
OUT = []


def w(s=""):
    OUT.append(s)


def dump(start, end, tag="", limit=80, tail=0):
    ins = [x for x in dis(start, end + 8) if x[0] < end]
    if tail:
        ins = ins[-tail:]
    w("    %s disasm [%s..%s) %d instr" % (tag, H(start), H(end), len(ins)))
    for (a, sz, mn, os_) in ins[:limit]:
        w("      %08X  %-8s %s" % (a, mn, os_))


# =========================================================== sections / .data
w("=" * 100)
w("SECTION TABLE (own PE parse; VirtualSize AND raw size both shown)")
for s in pe.secs:
    w("  %-9s va=%08X vsize=%08X rsize=%08X end(vs)=%08X ch=%08X" % (
        s["name"], s["va"], s["vsize"], s["rsize"],
        s["va"] + max(s["vsize"], s["rsize"]), s["ch"]))
w("  .data value range by VirtualSize: %08X .. %08X" % (DATA_LO, DATA_HI))
w("  (0x812000..0xB79BE4 expected per task: %s)" % (
    "MATCH" if (DATA_LO == 0x812000 and DATA_HI == 0xB79BE4) else "DIFFER"))

# ============================================== ① install form / host identity
w("")
w("=" * 100)
w("① INSTALL FORM + HOST IDENTITY — every one of the 18 rows")
for e, r in ROWS.items():
    sc = r["site_cls"]
    w("")
    w("-" * 96)
    w("ENTRY %s   %s" % (e, r["delta"]["name"]))
    w("  vt=%s slot=%s   fields install_form=%s   my form=%s" % (
        r["vt_h"], r["slot"], r["fields"].get("install_form(ctor_body|mov_abs|reg|other)"),
        sc.get("form")))
    w("  site=%s bytes=%s" % (r["site_h"], r.get("site_bytes")))
    w("  instruction: mov %s" % sc.get("op"))
    w("  target: base=%s index=%s disp=%s kind=%s" % (
        sc.get("base"), sc.get("index"), sc.get("disp"), sc.get("target_kind")))
    if sc.get("form") == "mov_abs":
        w("  abs=%s sec=%s in_.data=%s" % (sc.get("abs"), sc.get("abs_sec"),
                                           sc.get("abs_in_data")))
        w("  host=%s (%s) atlas=%s end=%s" % (sc.get("host"), sc.get("host_method"),
                                              sc.get("host_atlas"), sc.get("host_end")))
        for ln in sc.get("host_prologue", []):
            w("      %s" % ln)
        continue
    w("  this_trace=%s" % (sc.get("this_trace"),))
    w("  host=%s method=%s atlas_size=%s end=%s ret=%s" % (
        sc.get("host"), sc.get("host_method"), sc.get("host_atlas"),
        sc.get("host_end"), sc.get("host_ret")))
    di = sc.get("dtor_inline") or {}
    w("  dtor signature INSIDE host: shaped=%s test=%s delete=%s ret=%s" % (
        di.get("shaped"), H(di["test"][0]) if di.get("test") else None,
        H(di["delcall"][0]) if di.get("delcall") else None, di.get("ret")))
    dw = sc.get("deleting_wrapper_of_host") or []
    for x in dw:
        w("  host CALLED BY scalar-deleting wrapper %s (call@%s): test@%s delete@%s ret=%s" % (
            x["wrapper"], x["call_site"], x["sig_test"], x["sig_del"], x["sig_ret"]))
    w("  -> is_dtor(host) = %s" % sc.get("is_dtor"))
    w("  calls-base-ctor(first call in host): %s   returns_this=%s" % (
        sc.get("calls_base_ctor_first"), sc.get("returns_this")))
    hs, he, _r1, _r2 = func_extent(int(sc["host"], 16) if sc.get("host") else None)
    if hs:
        dump(hs, min(he, hs + 0x60), "host head", limit=24)

# ================================================== ② SITE_FIX (6 rows, 2 families)
w("")
w("=" * 100)
w("② SITE_FIX — 6 rows / 2 families: old decisive point vs new point")
SITE_FIX = {
    "0065CAC0": ("0065CA03", "0065CAA8"),
    "0065CDD0": ("0065CA03", "0065CAA8"),
    "0065CF00": ("0065CA03", "0065CAA8"),
    "0065D0D0": ("0065CA03", "0065CAA8"),
    "0065D150": ("004014C4", "0047AA3C"),
    "0065D190": ("004014C4", "0047AA3C"),
}
for e, (old, new) in SITE_FIX.items():
    r = ROWS[e]
    vt = r["vt"]
    w("")
    w("-" * 96)
    w("ROW %s (vt=%s slot=%s)  old=%s  new=%s" % (e, r["vt_h"], r["slot"], old, new))
    # find both in the vt's full install-point list
    ips = {H(d["site"]): d for d in install_points(vt, primary_only=False)}
    for tag, a in (("OLD", old), ("NEW", new)):
        d = ips.get(a)
        if d is None:
            w("  %s %s : NOT an install point of vt %s  <-- claim false" % (tag, a, r["vt_h"]))
            continue
        c = classify_ip(d, deep=True)
        w("  %s %s : mov %s" % (tag, a, c["op"]))
        w("     form=%s target=%s base=%s disp=%s host=%s atlas=%s end=%s" % (
            c["form"], c.get("target_kind"), c.get("base"), c.get("disp"),
            c.get("host"), c.get("host_atlas"), c.get("host_end")))
        w("     this_trace=%s" % (c.get("this_trace"),))
        di = c.get("dtor_inline") or {}
        w("     dtor_inline=%s wrapper_calls=%s is_dtor=%s" % (
            di.get("shaped"),
            [x["wrapper"] for x in (c.get("deleting_wrapper_of_host") or [])],
            c.get("is_dtor")))
        if c.get("calls_base_ctor_first") or c.get("returns_this"):
            w("     ctor signals: base_ctor=%s returns_this=%s" % (
                c.get("calls_base_ctor_first"), c.get("returns_this")))
    # full list of the vt's install points for completeness
    w("  ALL install points of vt %s:" % r["vt_h"])
    for a in sorted(ips, key=lambda x: int(x, 16)):
        d = ips[a]
        c = classify_ip(d, deep=True)
        w("     %s %-10s host=%s op=%s" % (a, c["form"], c.get("host"), c["op"]))
    # byte-level dump of the old host + new host
    dold = ips.get(old)
    if dold is not None:
        c = classify_ip(dold, deep=True)
        if c.get("host"):
            hs, he, _r1, _r2 = func_extent(int(c["host"], 16))
            dump(hs, min(he, hs + 0x80), "OLD host", limit=30)
    dnew = ips.get(new)
    if dnew is not None:
        c = classify_ip(dnew, deep=True)
        if c.get("host"):
            hs, he, _r1, _r2 = func_extent(int(c["host"], 16))
            dump(hs, min(he, hs + 0x80), "NEW host", limit=30)

# ============================================== ③ CLASS_FIX (5 total, 2 here)
w("")
w("=" * 100)
w("③ CLASS_FIX — new table class == row-name class? entry in that slot? why old mismatched?")
CLASS_FIX = {
    "005F4B10": dict(row_class="ObjectClass", old_vt=0x7E22A4, new_vt=0x7EF060,
                     extra=[0x7E3AD0]),
    "00631CC0": dict(row_class="FilePipe", old_vt=0x7E4D78, new_vt=0x7E4DA0, extra=[]),
}
for e, cfg in CLASS_FIX.items():
    r = ROWS[e]
    entry_va = int(e, 16)
    slot = r["slot"]
    w("")
    w("-" * 96)
    w("ROW %s  row-name class=%s  slot=%s" % (e, cfg["row_class"], slot))
    for tag, vt in [("OLD(final.tsv)", cfg["old_vt"]), ("NEW(chosen)", cfg["new_vt"])] + \
                   [("ALSO", v) for v in cfg["extra"]]:
        rt = g["rtti"](vt)
        sv = pe.u32(vt + slot * 4)
        w("  %s vt=%08X rtti=%s sec=%s" % (tag, vt, (rt or {}).get("mangled"), pe.sec_of(vt)))
        w("     slotvalue[%d]=%s  entry_in_slot=%s" % (slot, H(sv), sv == entry_va))
        ips = install_points(vt, primary_only=False)
        forms = []
        for d in ips:
            c = classify_ip(d, deep=True)
            forms.append((H(d["site"]), c["form"], c.get("host"), c["op"]))
        w("     install points (%d):" % len(forms))
        for x in forms:
            w("        %s %-10s host=%s  %s" % x)
    # tables that hold this entry at this slot
    w("  ALL tables holding entry at slot %d:" % slot)
    for t in r.get("tables", []):
        w("     %s %s" % (t["vt_h"], t["mangled"]))

# ================================================== dossier: raw entry function
w("")
w("=" * 100)
w("ENTRY FUNCTION SHAPES (site must be OUTSIDE; entry dtor signature recorded)")
for e, r in ROWS.items():
    ee = r["entry_ext"]
    w("  %s ext=%s..%s atlas=%s  site=%s outside=%s  entry_is_scalar_dtor=%s" % (
        e, ee["start"], ee["end"], ee["atlas"], r["site_h"], r.get("chk5"),
        (r.get("entry_is_dtor") or {}).get("shaped")))

with open(os.path.join(HERE, "_hardening.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(OUT))
print("wrote _hardening.txt  (%d lines)" % len(OUT))
