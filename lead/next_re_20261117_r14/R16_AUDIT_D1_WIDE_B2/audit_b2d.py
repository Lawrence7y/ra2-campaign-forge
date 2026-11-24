# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B2 step 4: fragility audit + fix list.

Question 1 (the B1 root cause): for each row, is the chosen install site simply the
LOWEST-ADDRESS external store of that vt?  And did that choice lose a `this`-target
store that exists at a higher address?

Question 2: is any ctor_body host a scalar deleting destructor?

Read-only.
"""
import io, os, sys, json, re

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_b2 as A

pe, IB, md = A.pe, A.IB, A.md
HERE = A.HERE
V = json.load(io.open(os.path.join(HERE, "_verdict.json"), encoding="utf-8"))
FIELDS = A.FIELDS
rowmap = {r["entry"]: r for r in FIELDS}


def prov_class(site):
    """classify a store site: 'this' | 'stack' | 'abs' | 'other'"""
    insns = list(md.disasm(pe.code(site, 16), site))
    if not insns:
        return "?", None, None
    cur = insns[0]
    if cur.mnemonic != "mov" or len(cur.operands) != 2:
        return "?", None, None
    if cur.operands[0].type != 3:  # not MEM (X86_OP_MEM == 3)
        return "?", None, None
    m = cur.operands[0].mem
    if m.base == 0 and m.index == 0:
        return "abs", "%08X" % (m.disp & 0xFFFFFFFF), pe.sec_of(m.disp & 0xFFFFFFFF)
    bn = cur.reg_name(m.base)
    if bn in ("esp", "ebp"):
        return "stack", None, bn
    # find host start by padding scan
    hs = None
    for p in range(site - 1, max(site - 0x600, IB), -1):
        if pe.buf[p - IB] in (0xCC, 0x90):
            continue
        if pe.buf[p - 1 - IB] in (0xCC, 0x90) and pe.buf[p - 2 - IB] in (0xCC, 0x90):
            ins = [i for i in md.disasm(pe.code(p, site - p + 24), p)]
            hit = [k for k, i in enumerate(ins) if i.address == site]
            if hit and all(i.id != 0 for i in ins[:hit[0] + 1]):
                hs = p
                break
    if hs is None:
        return "other", None, bn
    ins = [i for i in md.disasm(pe.code(hs, site - hs + 16), hs)]
    k = [j for j, i in enumerate(ins) if i.address == site]
    if not k:
        return "other", None, bn
    for j in range(k[0] - 1, -1, -1):
        try:
            _r, w = ins[j].regs_access()
        except Exception:
            continue
        if m.base in w:
            d = ins[j]
            if d.mnemonic == "mov" and len(d.operands) == 2 and d.operands[1].type == 1 \
                    and d.reg_name(d.operands[1].reg) == "ecx":
                return "this", "%08X" % hs, "%08X: %s %s" % (d.address, d.mnemonic, d.op_str)
            return "other", "%08X" % hs, "%08X: %s %s" % (d.address, d.mnemonic, d.op_str)
    return "other", "%08X" % hs, None


def dtor_in(lo, hi):
    ins = [i for i in md.disasm(pe.code(lo, hi - lo), lo)]
    t = "\n".join("%s %s" % (i.mnemonic, i.op_str) for i in ins)
    a = bool(re.search(r"test byte ptr \[esp[^\]]*\], 1", t))
    b = bool(re.search(r"call 0x7c8b3d", t))
    c = bool(re.search(r"^ret [0-9a-fx]+$", t, re.M))
    return dict(test=a, call_del=b, ret_imm=c, triple=(a and b and c))


out = []
o = []
o.append("%-9s %-10s %-10s %-6s %-6s %-8s %-8s %-7s %s" % (
    "entry", "site_used", "site_min", "form", "host_dt", "chosen", "lowestOK", "lost", "note"))
fixes = []
for r in V["rows"]:
    e = r["entry"]
    vt = int(r["vt"], 16)
    site = int(r["site"], 16)
    f = rowmap[e]
    ei = int(e, 16)
    e_atlas = A.ATLAS.get(ei) or 0
    stores = [s["site"] for s in A.find_stores(vt)]
    ext = [s for s in stores if not (ei <= s < ei + e_atlas)]
    mn = min(ext) if ext else None
    is_lowest = (mn == site)
    # classify every external site
    cls = {}
    for s in ext:
        k, hs, det = prov_class(s)
        cls[s] = (k, hs, det)
    chosen_kind = cls.get(site, ("?", None, None))[0]
    # did the lowest-address choice lose a 'this' store?
    this_sites = [s for s in ext if cls[s][0] == "this"]
    lost = None
    if r["form_claimed"] == "ctor_body" and chosen_kind != "this" and this_sites:
        lost = ["%08X(host %s)" % (s, cls[s][1]) for s in sorted(this_sites)[:4]]
    # host dtor
    host = int(r["host_claimed"], 16)
    hx = host + (A.ATLAS.get(host) or 0x400)
    dt = dtor_in(host, hx) if A.ATLAS.get(host) else None
    dtxt = ("TRIPLE!!" if dt["triple"] else "no") if dt else "n/a(no atlas)"
    o.append("%-9s %08X   %-10s %-6s %-6s %-8s %-8s %-7s %s" % (
        e, site, ("%08X" % mn) if mn else "-", r["form_claimed"], dtxt,
        chosen_kind, is_lowest, bool(lost),
        ("vt stores=%d ext=%d this-sites=%d" % (len(stores), len(ext), len(this_sites)))))
    if lost:
        o.append("        LOST this-target store(s): %s" % lost)
    out.append(dict(entry=e, site="%08X" % site, site_min="%08X" % mn if mn else None,
                    is_lowest=is_lowest, chosen_kind=chosen_kind,
                    n_stores=len(stores), n_ext=len(ext), n_this=len(this_sites),
                    lost=lost, form=r["form_claimed"],
                    host_dtor_triple=(dt["triple"] if dt else None)))

o.append("")
o.append("== rows where the lowest-address choice produced a non-`this` store ==")
for x in out:
    if x["form"] == "ctor_body" and x["chosen_kind"] != "this":
        o.append("  %s site=%s kind=%s lowest=%s lost=%s" % (
            x["entry"], x["site"], x["chosen_kind"], x["is_lowest"], x["lost"]))

o.append("")
o.append("== any ctor_body host with scalar-deleting-dtor signature ==")
bad = [x["entry"] for x in out if x["form"] == "ctor_body" and x["host_dtor_triple"]]
o.append("  " + (", ".join(bad) if bad else "none"))

txt = "\n".join(o) + "\n"
io.open(os.path.join(HERE, "_fragility.txt"), "w", encoding="utf-8").write(txt)
io.open(os.path.join(HERE, "_fragility.json"), "w", encoding="utf-8").write(
    json.dumps(out, ensure_ascii=False, indent=1, default=str))
print(txt)
