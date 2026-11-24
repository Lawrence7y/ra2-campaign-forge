# -*- coding: utf-8 -*-
"""R16-AUDIT-D1-WIDE-B2 step 2: aligned disassembly from a VERIFIED function start,
`this` provenance for every ctor_body row, host identity (ctor/factory vs scalar
deleting destructor), and the 5 CLASS_FIX re-derivations.

Read-only. Writes only into this audit directory.
"""
import io, os, sys, json, re, collections

sys.dont_write_bytecode = True
import capstone
from capstone import x86 as X

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_b2 as A          # own PE reader / rtti / tables / store index

pe = A.pe
IB = A.IB
md = A.md
PADB = (0xCC, 0x90)
HERE = A.HERE


# ---------------------------------------------------------------- verified start
def decode_from(start, end):
    insns = [i for i in md.disasm(pe.code(start, end - start), start)]
    return insns


def verified_start(site, reach=0x600):
    """Largest p < site such that p is preceded by >=2 padding bytes and a clean
    decode from p lands exactly on `site` (no .byte / invalid)."""
    cands = []
    for p in range(site - 1, max(site - reach, IB), -1):
        if pe.buf[p - IB] in PADB:
            continue
        if p - IB < 2:
            break
        if pe.buf[p - 1 - IB] in PADB and pe.buf[p - 2 - IB] in PADB:
            cands.append(p)
    for p in cands:
        insns = decode_from(p, site + 32)
        if not insns:
            continue
        ok = False
        clean = True
        for i in insns:
            if i.id == 0:
                clean = False
                break
            if i.address == site:
                ok = True
                break
        if ok and clean:
            return p, insns
    return None, None


def reg_n(insn, regid):
    try:
        return insn.reg_name(regid)
    except Exception:
        return "?"


def written(insn):
    try:
        _r, w = insn.regs_access()
        return set(w)
    except Exception:
        return set()


def find_def(insns, upto, reg):
    """nearest instruction before index `upto` writing reg -> (idx, insn)"""
    for j in range(upto - 1, -1, -1):
        if reg in written(insns[j]):
            return j, insns[j]
    return None, None


def classify_target(insns, site_idx, host_start):
    """Return dict describing where the store writes."""
    cur = insns[site_idx]
    a = cur.operands[0]
    m = a.mem
    out = dict(insn="%s %s" % (cur.mnemonic, cur.op_str),
               n_insn_from_host=site_idx + 1)
    if m.base == 0 and m.index == 0:
        out["kind"] = "abs"
        out["abs"] = "%08X" % (m.disp & 0xFFFFFFFF)
        return out
    base = cur.reg_name(m.base) if m.base else None
    out["base"] = base
    out["disp"] = m.disp
    out["kind"] = "stack" if base in ("esp", "ebp") else "reg"
    j, d = find_def(insns, site_idx, m.base)
    out["def"] = ("%08X: %s %s" % (d.address, d.mnemonic, d.op_str)) if d else None
    out["def_idx"] = j
    # expand one more hop for mov reg, reg / mov reg, [mem]
    if d is not None and len(d.operands) == 2:
        src = d.operands[1]
        if src.type == X.X86_OP_REG:
            k, d2 = find_def(insns, j, src.reg)
            out["def2"] = ("%08X: %s %s" % (d2.address, d2.mnemonic, d2.op_str)) if d2 else None
        elif src.type == X.X86_OP_MEM:
            # base of that memory operand
            mb = src.mem.base
            if mb:
                k, d2 = find_def(insns, j, mb)
                out["def_mem_base"] = ("%08X: %s %s" % (d2.address, d2.mnemonic, d2.op_str)) if d2 else None
            out["def_mem"] = "%s%s" % (
                (src.mem.base and d.reg_name(src.mem.base) or ""),
                "{:+d}".format(src.mem.disp) if src.mem.disp else "")
    # entry-level provenance: is base a callee-saved reg pushed at entry and then
    # loaded from ecx (thiscall this) or [esp+K] (stack arg 1 = this)?
    out["prologue"] = ["%08X: %s %s" % (i.address, i.mnemonic, i.op_str) for i in insns[:8]]
    # search: any `mov base, ecx` or `mov base, [esp+4]` / `[ebp+8]` in prologue..site
    ev = []
    for j2 in range(site_idx):
        i2 = insns[j2]
        if i2.mnemonic == "mov" and len(i2.operands) == 2 and i2.operands[0].type == X.X86_OP_REG \
                and i2.operands[0].reg == m.base:
            s = i2.operands[1]
            if s.type == X.X86_OP_REG and i2.reg_name(s.reg) == "ecx":
                ev.append(("this_ecx", "%08X: %s %s" % (i2.address, i2.mnemonic, i2.op_str)))
            elif s.type == X.X86_OP_MEM and s.mem.base and i2.reg_name(s.mem.base) in ("esp", "ebp"):
                dsp = s.mem.disp
                bn = i2.reg_name(s.mem.base)
                # this is arg1: [ebp+8] or [esp+4] at entry; if regs pushed, esp+N
                ev.append(("stack_load", "%08X: %s %s" % (i2.address, i2.mnemonic, i2.op_str),
                           bn, dsp))
        if i2.mnemonic == "lea" and len(i2.operands) == 2 and i2.operands[0].type == X.X86_OP_REG \
                and i2.operands[0].reg == m.base and i2.operands[1].type == X.X86_OP_MEM:
            ev.append(("lea_stack", "%08X: %s %s" % (i2.address, i2.mnemonic, i2.op_str)))
    out["prov_events"] = ev
    return out


# ---------------------------------------------------------------- host identity
def host_profile(start, site):
    insns = decode_from(start, start + 0x1200)
    end = start
    for i in insns:
        if i.id == 0:
            break
        end = i.address + i.size
    texts = ["%s %s" % (i.mnemonic, i.op_str) for i in insns]
    j = "\n".join(texts)
    prof = dict(n_insn=len(insns), end="%08X" % end,
                first=texts[:10], last=texts[-10:],
                has_test_esp1=bool(re.search(r"test byte ptr \[esp[^\]]*\], 1", j)),
                has_call_7c8b3d=bool(re.search(r"call 0x7c8b3d", j)),
                has_ret_imm=bool(re.search(r"^ret 0x[0-9a-f]+$", j, re.M) or re.search(r"^ret [1-9]", j, re.M)),
                returns_self=bool(re.search(r"^mov eax, (esi|edi|ebx)$", j, re.M)))
    prof["scalar_dtor"] = prof["has_test_esp1"] and prof["has_call_7c8b3d"] and prof["has_ret_imm"]
    return prof


# ---------------------------------------------------------------- main
FIELDS = {r["entry"]: r for r in A.FIELDS}
o = []
RES = {}
for d in A.DROWS:
    e = d[0]
    f = FIELDS[e]
    claimed_form = f["install_form(ctor_body|mov_abs|reg|other)"]
    claimed_host = f["install_host"]
    vt = int(f["vt"], 16)
    site = int(f["install_site"], 16)
    ei = int(e, 16)
    # host start: verified padding-based; cross-check with atlas
    hs, insns = verified_start(site)
    atlas_h = A.atlas_func(site)
    o.append("")
    o.append("=" * 108)
    o.append("%s  %s" % (e, A.COVM[e][2]))
    o.append("  claimed_form=%s  claimed_host=%s" % (claimed_form, claimed_host))
    o.append("  verified_start=%s   atlas_func=%s  claimed=%s" % (
        "%08X" % hs if hs else None, "%08X" % atlas_h if atlas_h else None, claimed_host))
    if insns is None:
        o.append("  !! no verified start found")
        RES[e] = dict(no_start=True)
        continue
    site_idx = next(k for k, i in enumerate(insns) if i.address == site)
    ct = classify_target(insns, site_idx, hs)
    hp = host_profile(hs, site)
    RES[e] = dict(verified_start="%08X" % hs, atlas="%08X" % atlas_h if atlas_h else None,
                  claimed_host=claimed_host, target=ct, host=hp,
                  host_is_entry=(hs == ei), site_idx=site_idx)
    o.append("  store: %08X  %s" % (site, ct["insn"]))
    o.append("  target kind=%s base=%s disp=%s abs=%s" % (
        ct["kind"], ct.get("base"), ct.get("disp"), ct.get("abs")))
    o.append("  target def=%s" % ct.get("def"))
    if ct.get("def2"):
        o.append("           def2=%s" % ct["def2"])
    if ct.get("def_mem"):
        o.append("           def_mem=%s   base_def=%s" % (ct["def_mem"], ct.get("def_mem_base")))
    for ev in ct.get("prov_events") or []:
        o.append("           prov=%s" % (ev,))
    o.append("  host prologue: %s" % " ; ".join(hp["first"][:8]))
    o.append("  host tail    : %s" % " ; ".join(hp["last"]))
    o.append("  host: n_insn=%d end=%s scalar_dtor=%s returns_self=%s" % (
        hp["n_insn"], hp["end"], hp["scalar_dtor"], hp["returns_self"]))
    o.append("  host_is_entry=%s" % (hs == ei))

io.open(os.path.join(HERE, "_facts2.txt"), "w", encoding="utf-8").write("\n".join(o) + "\n")
io.open(os.path.join(HERE, "_facts2.json"), "w", encoding="utf-8").write(
    json.dumps(RES, ensure_ascii=False, indent=1, default=str))
print("wrote _facts2.txt  rows=%d" % len(RES))
