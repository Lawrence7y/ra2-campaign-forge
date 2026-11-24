# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B2 step 3: full A-F verdicts + CLASS_FIX re-derivation.

Read-only. Writes only into this audit directory.
"""
import io, os, sys, json, re, bisect, collections

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_b2 as A

pe, IB, md = A.pe, A.IB, A.md
HERE = A.HERE
EX = os.path.join(HERE, "..", "R16_D1_WIDE_B2")

COVM = A.COVM
DELTA, DH = A.DELTA, A.DH
DROWS = A.DROWS
FIELDS = {r["entry"]: r for r in A.FIELDS}
FIN = A.FIN
SIEVE = A.SIEVE_ROWS
STATUSF = "status(OK|SKIP-ALREADY|SKIP|CLASS_FIX)"
FORMF = "install_form(ctor_body|mov_abs|reg|other)"

# ---------------------------------------------------------------- F: sieve list
no = sorted([r for r in SIEVE if r["has_ring4_on_disk(是/否)"] == "否"],
            key=lambda x: int(x["entry"], 16))
b1 = [r["entry"] for r in no[:18]]
b2 = [r["entry"] for r in no[18:36]]
b3 = [r["entry"] for r in no[36:54]]
delta_entries = [d[0] for d in DROWS]
F_chk = dict(
    n_sieve=len(SIEVE),
    n_no_ring4=len(no),
    n_yes_ring4=len(SIEVE) - len(no),
    b2_list_ok=(delta_entries == b2),
    b2_equals_no_18_36=(sorted(delta_entries) == sorted(b2)),
    b1_disjoint=(set(b1) & set(b2) == set()),
    b3_disjoint=(set(b3) & set(b2) == set()),
    n_b2=len(b2), n_delta=len(delta_entries),
    b2_entries=b2, delta_entries=delta_entries,
)

# ---------------------------------------------------------------- A: preservation
A_chk = dict(rows=0, col4_prefix_fail=[], cols_fail=[], grade_fail=[],
             pre_has4=[], len_ok=[], not_in_cov=[])
for d in DROWS:
    e = d[0]
    A_chk["rows"] += 1
    if e not in COVM:
        A_chk["not_in_cov"].append(e)
        continue
    cr = COVM[e]
    if len(d) != 8:
        A_chk["cols_fail"].append((e, "ncols=%d" % len(d)))
        continue
    # cols 1,2,3,5,6,7,8 byte identical (0-based 0,1,2,4,5,6,7)
    for i in (0, 1, 2, 4, 5, 6, 7):
        if d[i] != cr[i]:
            A_chk["cols_fail"].append((e, i, repr(d[i])[:40], repr(cr[i])[:40]))
    # col4 strict prefix + strictly longer
    if not (d[3].startswith(cr[3]) and len(d[3]) > len(cr[3])):
        A_chk["col4_prefix_fail"].append(e)
    if "④" in cr[3]:
        A_chk["pre_has4"].append(e)
    # grade unchanged (col5 index 4)
    if d[4] != cr[4]:
        A_chk["grade_fail"].append((e, d[4], cr[4]))
A_chk["ok"] = not (A_chk["col4_prefix_fail"] or A_chk["cols_fail"] or
                   A_chk["grade_fail"] or A_chk["pre_has4"] or A_chk["not_in_cov"])

# ---------------------------------------------------------------- B: 6 byte facts
def six(entry, vt, slot):
    ei = int(entry, 16)
    r = A.rtti(vt)
    sv = pe.u32(vt + slot * 4)
    return dict(
        c1=(sv == ei),
        c2=bool(r and r["sig"] == 0),
        c3=bool(r and r["off"] == 0),
        c4=bool(r and r["name"].startswith(".?A")),
        c6=(vt is not None and r is not None),
    ), r, sv

# ---------------------------------------------------------------- C: install form
def host_extent(h):
    """Prefer atlas size (authoritative export). Else: end = start of the next
    padding run (>=2 pad bytes) after h, which bounds the function body."""
    sz = A.ATLAS.get(h)
    if sz:
        return h, h + sz, "atlas"
    end = h + 0x4000
    p = h
    while p < h + 0x4000:
        if pe.buf[p - IB] in (0xCC, 0x90) and pe.buf[p + 1 - IB] in (0xCC, 0x90):
            end = p
            break
        p += 1
    return h, end, "padscan"


def dtor_in(lo, hi):
    insns = [i for i in md.disasm(pe.code(lo, hi - lo), lo)]
    txt = "\n".join("%s %s" % (i.mnemonic, i.op_str) for i in insns)
    t = re.search(r"test byte ptr \[esp[^\]]*\], 1", txt)
    c = re.search(r"call 0x7c8b3d", txt)
    r = re.search(r"^ret [0-9a-fx]+$", txt, re.M)
    return dict(test=bool(t), call_del=bool(c), ret_imm=bool(r),
                triple=bool(t and c and r))


# ---------------------------------------------------------------- D: ④ text parse
RE4 = re.compile(
    r"④ 活表槽位见证：(?P<lab>[^（]+)（vt=(?P<vt>[0-9A-F]{8})，槽 (?P<slot>\d+) 值=(?P<val>[0-9A-F]{8})，"
    r"COL=(?P<col>[0-9A-F]{8}) offset=(?P<off>-?\d+)，RTTI=(?P<td>[0-9A-F]{8})→(?P<mg>[^；]+)；"
    r"装表点 (?P<site>[0-9A-F]{8}) 位于 (?P<host>[^\s]+) 体内，装配方式=(?P<form>\w+)"
    r"（(?P<formtxt>[^）]*)），entry 体外）"
    r" ④升级句：(?P<lab2>[^（]+)（④ 表属类与行名类一致，均为 (?P<cls>[^；]+)；[^）]*）")

DISC126 = "见 R14_COMMON §12.6"
results = []
for d in DROWS:
    e = d[0]
    cr = COVM[e]
    f = FIELDS[e]
    ei = int(e, 16)
    vt = int(f["vt"], 16)
    slot = int(f["slot"])
    site = int(f["install_site"], 16)
    host_claimed = f["install_host"]
    form_claimed = f[FORMF]
    status = f[STATUSF]
    sixd, r, sv = six(e, vt, slot)
    # 5: site outside entry body (own extent + atlas)
    e_own_end = A.func_extent(ei)
    e_atlas = A.ATLAS.get(ei)
    c5 = (not (ei <= site < e_own_end)) and not (e_atlas and (ei <= site < ei + e_atlas))
    sixd["c5"] = c5

    # --- target analysis
    hs, hsrc = None, None
    ah = A.atlas_func(site)
    if ah:
        hs, hsrc = ah, "atlas"
    else:
        # verified padding start: preceded by >=2 pad bytes, and a decode from it
        # reaches `site` cleanly (every instruction up to and including site valid)
        p = None
        for p2 in range(site - 1, max(site - 0x600, IB), -1):
            if pe.buf[p2 - IB] in (0xCC, 0x90):
                continue
            if pe.buf[p2 - 1 - IB] in (0xCC, 0x90) and pe.buf[p2 - 2 - IB] in (0xCC, 0x90):
                insns = [i for i in md.disasm(pe.code(p2, site - p2 + 24), p2)]
                hit = [k for k, i in enumerate(insns) if i.address == site]
                if hit and all(i.id != 0 for i in insns[:hit[0] + 1]):
                    p = p2
                    break
        hs, hsrc = p, "scan"
    insns = [i for i in md.disasm(pe.code(hs, site - hs + 32), hs)] if hs else []
    sidx = next((k for k, i in enumerate(insns) if i.address == site), None)
    if sidx is None:
        # fall back to decoding straight at the site (operand form is still exact)
        insns = [i for i in md.disasm(pe.code(site, 32), site)]
        sidx = 0
    cur = insns[sidx]
    m = cur.operands[0].mem
    tgt = dict(insn="%s %s" % (cur.mnemonic, cur.op_str))
    this_ok = None
    if m.base == 0 and m.index == 0:
        tgt["kind"] = "abs"
        tgt["abs"] = "%08X" % (m.disp & 0xFFFFFFFF)
        tgt["abs_sec"] = pe.sec_of(m.disp & 0xFFFFFFFF)
        form_true = "mov_abs"
        this_ok = (tgt["abs_sec"] == ".data")
    else:
        bn = cur.reg_name(m.base)
        tgt["kind"] = "stack" if bn in ("esp", "ebp") else "reg"
        tgt["base"] = bn
        tgt["disp"] = m.disp
        form_true = "reg"
        if tgt["kind"] == "stack":
            this_ok = False
            tgt["reason"] = "store target is a stack slot (%s+%d), not this" % (bn, m.disp)
        else:
            # find def of base reg within the host function
            found = None
            for j in range(sidx - 1, -1, -1):
                try:
                    _r, w = insns[j].regs_access()
                except Exception:
                    continue
                if m.base in w:
                    found = insns[j]
                    break
            tgt["def"] = ("%08X: %s %s" % (found.address, found.mnemonic, found.op_str)) if found else None
            if found is not None and found.mnemonic == "mov" and len(found.operands) == 2 \
                    and found.operands[1].type == 1 and found.reg_name(found.operands[1].reg) == "ecx":
                this_ok = True
                tgt["reason"] = "base reg <- ecx at %08X (thiscall this)" % found.address
            else:
                this_ok = None
    # host identity
    hx = host_extent(hs) if hs else None
    dtor = dtor_in(hx[0], hx[1]) if hx else None
    host_is_entry = (hs == ei)
    host_ok = (not host_is_entry) and (dtor is not None) and (not dtor["triple"])

    form_label_ok = None
    if form_claimed == "mov_abs":
        form_label_ok = (form_true == "mov_abs" and this_ok is True)
    elif form_claimed == "ctor_body":
        form_label_ok = (form_true == "reg" and this_ok is True and host_ok)
    else:
        form_label_ok = False

    # --- D: text parse
    new = d[3][len(cr[3]):]
    mm = RE4.search(new)
    dchk = dict(parsed=bool(mm), s126=(DISC126 in new), s124=("§12.4" in new))
    if mm:
        g = mm.groupdict()
        dchk.update(
            vt=(g["vt"] == f["vt"]),
            slot=(int(g["slot"]) == slot),
            val=(g["val"] == e),
            col=(r is not None and g["col"] == "%08X" % r["col"]),
            off=(int(g["off"]) == (r["off"] if r else 0)),
            td=(r is not None and g["td"] == "%08X" % r["td"]),
            mg=(r is not None and g["mg"] == r["name"]),
            site=(g["site"] == f["install_site"]),
            host=(g["host"] == host_claimed),
            form=(g["form"] == form_claimed),
            insn_in_text=(tgt["insn"] in g["formtxt"]),
            label=(g["lab"] == "%s::slot%d" % (cr[2].rsplit("::", 1)[0], slot)),
            lab2=(g["lab2"] == g["lab"]),
            cls=(g["cls"] == cr[2].rsplit("::", 1)[0]),
        )
    # host in text vs my verified host
    dchk["host_matches_mine"] = (hs is not None and host_claimed == "%08X" % hs)

    results.append(dict(
        entry=e, name=cr[2], status=status,
        vt="%08X" % vt, slot=slot, site=f["install_site"],
        six=sixd, six_all=all(sixd.values()), slot_val="%08X" % sv,
        rtti=r, form_claimed=form_claimed, form_true=form_true,
        target=tgt, this_ok=this_ok,
        host_claimed=host_claimed,
        host_mine="%08X" % hs if hs else None, host_src=hsrc,
        host_is_entry=host_is_entry, dtor=dtor, host_ok=host_ok,
        form_label_ok=form_label_ok, d=dchk, new=new,
    ))

# ---------------------------------------------------------------- CLASS_FIX
CF = []
for r in results:
    if r["status"] != "CLASS_FIX":
        continue
    e = r["entry"]
    ei = int(e, 16)
    namecls = r["name"].rsplit("::", 1)[0]
    fin = FIN.get(e)
    dec_vt = int(fin["vt"], 16) if fin else None
    dec_slot = int(fin["slot"]) if fin else None
    dec_rtti = A.rtti(dec_vt) if dec_vt else None
    # does the decisive table actually hold the entry at that slot?
    dec_holds = (pe.u32(dec_vt + dec_slot * 4) == ei) if dec_vt is not None else None
    # all tables holding the entry
    holds = []
    for vt, t in A.TABS.items():
        n = 0
        # bounded slot scan
        for k in range(0, 400):
            v = pe.u32(vt + k * 4)
            if v is None:
                break
            if v == ei:
                holds.append((vt, k, t["cls"]))
            if v == 0 or not (0x401000 <= v < 0x7E038D):
                if k > 0:
                    break
    exact = [h for h in holds if h[2] == ".?AV%s@@" % namecls]
    CF.append(dict(
        entry=e, namecls=namecls,
        final_vt="%08X" % dec_vt if dec_vt else None,
        final_slot=dec_slot,
        final_cls=dec_rtti["name"] if dec_rtti else None,
        final_matches_namecls=(dec_rtti["name"] if dec_rtti else None) == ".?AV%s@@" % namecls,
        final_holds_entry=dec_holds,
        chosen_vt=r["vt"], chosen_slot=r["slot"],
        chosen_cls=r["rtti"]["name"] if r["rtti"] else None,
        chosen_matches_namecls=(r["rtti"]["name"] if r["rtti"] else None) == ".?AV%s@@" % namecls,
        n_tables_holding=len(holds),
        n_exact_class_tables=len(exact),
        exact_tables=["%08X/slot%d" % (h[0], h[1]) for h in exact],
        holds=["%08X/slot%d/%s" % h for h in sorted(holds)][:14],
    ))

# ---------------------------------------------------------------- E: anti-plagiarism
bodies = [r["new"] for r in results]
norm = [re.sub(r"[0-9A-Fa-f]{8}", "ENTRY", b) for b in bodies]
norm2 = [re.sub(r"slot\d+", "SLOT", n) for n in norm]
E_chk = dict(n=len(bodies),
             full_distinct=len(set(bodies)),
             norm_distinct=len(set(norm)),
             norm2_distinct=len(set(norm2)))
# vs on-disk ④ rows already in coverage: is any body a near-copy of another row's?
ondisk = {}
for k, c in COVM.items():
    if "④" in c[3]:
        m2 = re.search(r"④ 活表槽位见证.*", c[3])
        if m2:
            ondisk[k] = re.sub(r"[0-9A-Fa-f]{8}", "ENTRY", m2.group(0))
dup = [r["entry"] for r in results if re.sub(r"[0-9A-Fa-f]{8}", "ENTRY", r["new"]) in ondisk.values()]
E_chk["copied_from_ondisk"] = dup

out = dict(F=F_chk, A=A_chk, E=E_chk,
           rows=results, classfix=CF)

def default(o):
    return str(o)
io.open(os.path.join(HERE, "_verdict.json"), "w", encoding="utf-8").write(
    json.dumps(out, ensure_ascii=False, indent=1, default=default))

# ---------------------------------------------------------------- console table
L = []
L.append("== F ==")
for k, v in F_chk.items():
    if k in ("b2_entries", "delta_entries"):
        continue
    L.append("  %-22s %s" % (k, v))
L.append("  b2_list_ok=%s" % F_chk["b2_list_ok"])
L.append("")
L.append("== A ==")
for k, v in A_chk.items():
    L.append("  %-22s %s" % (k, v))
L.append("")
L.append("== per row ==")
hdr = "%-9s %-6s %-6s %-9s %-10s %-9s %-6s %-6s %-6s %-5s %-5s" % (
    "entry", "six", "formC", "formTrue", "this_ok", "host_ok", "formOK", "dOK", "s126", "s124", "host")
L.append(hdr)
for r in results:
    d = r["d"]
    dkeys = ("vt", "slot", "val", "col", "off", "td", "mg", "site", "host", "form",
             "insn_in_text", "label", "lab2", "cls")
    dbad = [k for k in dkeys if d.get(k) is False]
    L.append("%-9s %-6s %-6s %-9s %-10s %-9s %-6s %-6s %-6s %-5s %-5s" % (
        r["entry"], "OK" if r["six_all"] else "FAIL", r["form_claimed"], r["form_true"],
        r["this_ok"], r["host_ok"], r["form_label_ok"],
        "OK" if not dbad and d["parsed"] else "BAD", d["s126"], d["s124"],
        "hostOK" if d["host_matches_mine"] else "hostDIFF"))
    if dbad:
        L.append("      D-mismatch: %s" % dbad)
    if r["target"].get("reason"):
        L.append("      target: %s" % r["target"]["reason"])
    if r["dtor"] and r["dtor"]["triple"]:
        L.append("      !! host has scalar-deleting-dtor signature")
    if not r["host_ok"] and (r["dtor"] is None or r["host_is_entry"]):
        L.append("      !! host extent unresolved / host==entry")
L.append("")
L.append("== CLASS_FIX ==")
for c in CF:
    L.append("  %s namecls=%s" % (c["entry"], c["namecls"]))
    L.append("    final vt=%s slot=%s cls=%s matches=%s holds=%s" % (
        c["final_vt"], c["final_slot"], c["final_cls"], c["final_matches_namecls"],
        c["final_holds_entry"]))
    L.append("    chosen vt=%s slot=%s cls=%s matches=%s  nTablesHolding=%d nExact=%d %s" % (
        c["chosen_vt"], c["chosen_slot"], c["chosen_cls"], c["chosen_matches_namecls"],
        c["n_tables_holding"], c["n_exact_class_tables"], c["exact_tables"]))
L.append("")
L.append("== E ==")
for k, v in E_chk.items():
    L.append("  %-22s %s" % (k, v))

txt = "\n".join(L) + "\n"
io.open(os.path.join(HERE, "_verdict.txt"), "w", encoding="utf-8", errors="replace").write(txt)
print(txt)
