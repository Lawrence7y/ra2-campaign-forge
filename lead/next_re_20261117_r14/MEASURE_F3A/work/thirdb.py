# -*- coding: utf-8 -*-
"""MEASURE-F3A · ③b detector, calibrated against controls (see PROGRESS.md §3).

R14_COMMON §8.6 条 3 defines the ③b tier (the only tier [已证] accepts) as any of:
  ③b①  jump table / switch, every arm checkable
  ③b②  falsifiable error-code / return convention
  ③b③  memory-shape assertion (member ctors + vt + object size)
  ③b④  complete loop I/O (read -> test -> write -> advance, with bounds check)
Card rule: the ③b④ write must be a NON-STACK write or a falsifiable return code;
a stack accumulator or a register advance alone does not count.

Every predicate below is computed from the bytes of [entry, entry+size) only.
"""
import capstone
from pelib import _MD, OP_MEM, OP_IMM, OP_REG

CS_AC_WRITE = capstone.CS_AC_WRITE
IMAGE_LO, IMAGE_HI = 0x400000, 0x7D9000


def _obj_write_op(ins):
    """True when operand 0 is a memory destination not based on esp/ebp."""
    if not ins.operands:
        return False
    d = ins.operands[0]
    if d.type != OP_MEM or not (d.access & CS_AC_WRITE):
        return False
    base = ins.reg_name(d.mem.base) if d.mem.base else ""
    idx = ins.reg_name(d.mem.index) if d.mem.index else ""
    return base not in ("esp", "ebp") and idx not in ("esp", "ebp")


def _reg_names(ins):
    return {ins.reg_name(o.reg) for o in ins.operands if o.type == OP_REG}


def conds(pe, entry, size):
    code = pe.read(entry, size)
    if code is None:
        return None
    insns = list(_MD.disasm(code, entry))
    n = len(insns)

    # ---------- collect structure
    jcc, back_edges, jumptables = [], [], []
    for i, ins in enumerate(insns):
        mn = ins.mnemonic
        if mn.startswith("j") and mn != "jmp":
            if ins.operands and ins.operands[0].type == OP_IMM:
                t = ins.operands[0].imm
                jcc.append((i, ins, t))
                if t < ins.address:
                    back_edges.append((i, ins, t))
        elif mn == "jmp" and ins.operands and ins.operands[0].type == OP_MEM:
            m = ins.operands[0].mem
            if m.index and m.scale in (1, 2, 4, 8):
                jumptables.append(ins)

    # ---------- ③b①  dispatch table with readable in-image targets
    jt_ok, jt_n, jt_arms = False, 0, []
    for ins in jumptables:
        m = ins.operands[0].mem
        base = ins.reg_name(m.base) if m.base else ""
        # table address = disp (+ base register value unknown => require base-less or known global)
        tab = m.disp
        if not (IMAGE_LO <= tab < IMAGE_HI):
            continue
        arms = []
        for k in range(64):
            v = pe.u32(tab + 4 * k)
            if v is None or not (IMAGE_LO <= v < IMAGE_HI):
                break
            arms.append(v)
        jt_n += 1
        if len(arms) >= 4:
            jt_ok = True
            jt_arms = arms[:16]

    # ---------- ③b①'  multi-way arms that are individually checkable
    # D-42 ③b① is "跳表 / switch 多路分支且每路可核". A dispatch table is only its
    # canonical form; the other observable form is a set of mutually exclusive arms
    # each performing a DIFFERENT object write or a DIFFERENT call target, which a
    # reader can re-check arm by arm. Register-only differences (mov al,1 vs xor al,al)
    # do NOT count - that is what keeps 0045A640 (pure compare loop) at ③b=False.
    arms_sig = []
    for (i, ins, tgt) in jcc:
        lo, hi = (ins.address + ins.size, tgt) if tgt > ins.address else (tgt, ins.address)
        acts = []
        for x in insns:
            if not (lo <= x.address < hi):
                continue
            if _obj_write_op(x):
                d = x.operands[0]
                acts.append(("W", d.mem.disp & 0xFFFFFFFF))
            if x.mnemonic == "call":
                if x.operands and x.operands[0].type == OP_IMM:
                    acts.append(("C", x.operands[0].imm & 0xFFFFFFFF))
                elif x.operands and x.operands[0].type == OP_MEM:
                    acts.append(("V", x.operands[0].mem.disp & 0xFFFFFFFF))
        if acts:
            arms_sig.append((ins.address, tuple(sorted(set(acts)))))
    distinct = {sig for (_, sig) in arms_sig}
    b1v2 = len(arms_sig) >= 2 and len(distinct) >= 2 and len(jcc) >= 2

    jt_ok = jt_ok or b1v2
    # fallback: jmp [reg*4 + base] with base register -> still a dispatch if arms readable via
    # the literal disp seen in the instruction stream (only when disp is an absolute VA)

    # ---------- ③b②  falsifiable return / error convention
    sentinel = False
    for i, ins in enumerate(insns):
        if ins.mnemonic == "cmp" and len(ins.operands) >= 2:
            a, b = ins.operands[0], ins.operands[1]
            # cmp reg, -1  /  cmp dword [mem], -1
            if b.type == OP_IMM and (b.imm & 0xFFFFFFFF) in (0xFFFFFFFF,):
                for j in range(i + 1, min(i + 5, n)):
                    if insns[j].mnemonic.startswith("set"):
                        sentinel = True
                    if insns[j].mnemonic.startswith("j"):
                        sentinel = True
            if a.type == OP_IMM and (a.imm & 0xFFFFFFFF) in (0xFFFFFFFF,):
                for j in range(i + 1, min(i + 5, n)):
                    if insns[j].mnemonic.startswith(("j", "set")):
                        sentinel = True
    # dual constant returns  (incl. xor al,al / mov al,1 / setCC)
    rconsts = set()
    for i, ins in enumerate(insns):
        mn = ins.mnemonic
        if mn.startswith("mov") and len(ins.operands) == 2:
            d, s = ins.operands
            if d.type == OP_REG and ins.reg_name(d.reg) in ("al", "ax", "eax") and s.type == OP_IMM:
                rconsts.add(s.imm & 0xFFFFFFFF)
        if mn in ("xor", "sub") and len(ins.operands) == 2:
            d, s = ins.operands
            if d.type == OP_REG and s.type == OP_REG and d.reg == s.reg:
                if ins.reg_name(d.reg) in ("al", "ax", "eax"):
                    rconsts.add(0)
    val_consts = {c for c in rconsts if isinstance(c, int)}
    # NOTE (calibration, see PROGRESS §3): a plain boolean return (0/1 on two paths) is
    # ③a "单次比较+返回", NOT ③b②. The card's own negative control 0045A640 is exactly a
    # bool-returning compare loop and must FAIL ③b, so the boolean shape is excluded here.
    # Accepted error-code shapes: a -1 sentinel comparison that drives a branch/setcc, or a
    # literal -1 error return in eax immediately before ret.
    err_ret = False
    for i, ins in enumerate(insns):
        if ins.mnemonic.startswith("mov") and len(ins.operands) == 2:
            d, s = ins.operands
            if (d.type == OP_REG and ins.reg_name(d.reg) in ("al", "ax", "eax")
                    and s.type == OP_IMM and (s.imm & 0xFFFFFFFF) == 0xFFFFFFFF):
                for j in range(i + 1, min(i + 4, n)):
                    if insns[j].mnemonic.startswith("ret"):
                        err_ret = True
    b2 = bool(sentinel or err_ret)

    # ---------- ③b③  memory shape: vtable install (+ real object writes)
    vt_installs = []
    for ins in insns:
        if ins.mnemonic.startswith("mov") and len(ins.operands) == 2:
            d, s = ins.operands
            if d.type == OP_MEM and s.type == OP_IMM:
                base = ins.reg_name(d.mem.base) if d.mem.base else ""
                if base in ("esp", "ebp"):
                    continue
                if IMAGE_LO <= (s.imm & 0xFFFFFFFF) < IMAGE_HI:
                    vt_installs.append(ins.address)
    obj_writes = [ins.address for ins in insns if _obj_write_op(ins)]
    b3 = bool(len(vt_installs) >= 1 and len(obj_writes) >= 2)

    # ---------- ③b④  loop: body must contain a non-stack write + a bound test + a back edge
    b4, loops_detail = False, []
    for (i, ins, tgt) in back_edges:
        body = [x for x in insns if tgt <= x.address <= ins.address]
        w = [x.address for x in body if _obj_write_op(x)]
        # bound test = cmp/test inside body followed within 3 insns by a conditional branch
        bound = False
        for k, x in enumerate(body):
            if x.mnemonic in ("cmp", "test"):
                for y in body[k + 1:k + 4]:
                    if y.mnemonic.startswith("j"):
                        bound = True
        if w and bound:
            b4 = True
            loops_detail.append({"target": tgt, "backedge": ins.address,
                                 "writes": w[:6], "bound": bound})
    return {
        "3b1_jumptable": jt_ok, "jt_count": jt_n, "jt_arms": jt_arms[:6],
        "3b2_errcode": b2, "sentinel": sentinel, "const_returns": sorted(val_consts),
        "3b3_memshape": b3, "vt_installs": len(vt_installs), "obj_writes": len(obj_writes),
        "3b4_loopio": b4, "loops": loops_detail,
        "n_instr": n, "n_jcc": len(jcc), "n_backedge": len(back_edges),
        "n_call": sum(1 for x in insns if x.mnemonic == "call"),
        "n_ret": sum(1 for x in insns if x.mnemonic.startswith("ret")),
    }


def thirdb(c):
    return bool(c and (c["3b1_jumptable"] or c["3b2_errcode"]
                       or c["3b3_memshape"] or c["3b4_loopio"]))


def which(c):
    if not c:
        return "-"
    out = []
    for k, lab in (("3b1_jumptable", "①"), ("3b2_errcode", "②"),
                   ("3b3_memshape", "③"), ("3b4_loopio", "④")):
        if c[k]:
            out.append(lab)
    return "".join(out) or "-"
