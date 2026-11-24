"""Master .text sweep: one linear disasm pass, collect all needed evidence.
Produces EVIDENCE/sweep_global_refs.tsv, sweep_0x80_writes.tsv, sweep_0x94_writes.tsv,
and JSON summary. Uses skipdata=True, both absolute + imm-base+[reg+off] forms.
"""
import sys, os, json, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
from audit_lib import Bin, md32, load_func_atlas
import capstone, bisect

ROOT = r"D:\Project\ra2-campaign-forge"
OUTDIR = os.path.join(ROOT, r"lead\next_re_20261117_r14\S07-K2\EVIDENCE")

b = Bin()
t = b.text
data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
m = md32(skipdata=True)

# atlas for func-range tagging
atlas_rows, _ = load_func_atlas()
atlas_entries = [va for va, _ in atlas_rows]
atlas_map = {va: rec for va, rec in atlas_rows}
def func_of(va):
    i = bisect.bisect_right(atlas_entries, va) - 1
    if i < 0:
        return None
    e = atlas_entries[i]
    rec = atlas_map[e]
    try:
        sz = int(rec.get("size", "0"))
    except Exception:
        sz = 0
    if sz and va < e + sz:
        return e
    return None

# global addresses of interest
GLOBALS = {
    0x8A0360: "layer_base", 0x8A0364: "layer0_items?",
    0x8A0368: "layer0_items", 0x8A0370: "layer0_count",
    0x8A0378: "layer1_base", 0x8A037C: "layer1_items", 0x8A0388: "layer1_count",
    0x8A0390: "layer2_base", 0x8A0394: "layer2_items", 0x8A03A0: "layer2_count",
    0x8A03A4: "layer2_field+14", 0x8A03A8: "layer3_base", 0x8A03AC: "layer3_items",
    0x8A03B8: "layer3_count", 0x8A03C0: "layer4_base", 0x8A03C4: "layer4_items",
    0x8A03D0: "layer4_count", 0x8A03D8: "array_end",
    0x886FA0: "scrollX", 0x886FA4: "scrollY",
    0x8871E0: "gameobj", 
}

insns = []
for insn in m.disasm(data, t["va"]):
    if insn.id == 0:
        continue
    insns.append(insn)
print("total real insns:", len(insns))

# ---- Pass 1: collect absolute refs and mov reg,imm base loads ----
abs_refs = []  # (va, insn_text, target, kind)
base_loads = []  # (va, reg, imm) for mov reg, imm32 (op1 reg, op2 imm)

for insn in insns:
    for op in insn.operands:
        if op.type == capstone.x86.X86_OP_MEM:
            mem = op.mem
            if mem.base == 0 and mem.index == 0:
                disp = mem.disp & 0xFFFFFFFF
                if disp in GLOBALS:
                    abs_refs.append((insn.address, "%s %s" % (insn.mnemonic, insn.op_str), disp, GLOBALS[disp], func_of(insn.address)))
    # mov reg, imm32 (loads a global base address)
    if insn.mnemonic in ("mov", "lea") and len(insn.operands) == 2:
        op0, op1 = insn.operands
        if op0.type == capstone.x86.X86_OP_REG and op1.type == capstone.x86.X86_OP_IMM:
            imm = op1.imm & 0xFFFFFFFF
            if imm in GLOBALS:
                base_loads.append((insn.address, insn.reg_name(op0.reg), imm, GLOBALS[imm], func_of(insn.address)))

# ---- Pass 2: for each base_load, find [reg+off] refs in the following window (same func) ----
base_refs = []  # (load_va, reg, base, ref_va, off, insn_text)
load_by_reg = {}
for va, reg, imm, name, fn in base_loads:
    load_by_reg.setdefault((fn, reg), []).append((va, imm, name))

# index insns by address for window scanning
addrs = [i.address for i in insns]
for (fn, reg), loads in load_by_reg.items():
    for loadva, imm, name in loads:
        i = bisect.bisect_right(addrs, loadva)
        # scan next 60 insns (or until func changes)
        for j in range(i, min(i+80, len(insns))):
            insn = insns[j]
            # stop if we've left the function
            if fn is not None and func_of(insn.address) != fn:
                break
            if insn.address - loadva > 0x200:
                break
            for op in insn.operands:
                if op.type == capstone.x86.X86_OP_MEM:
                    mem = op.mem
                    if mem.base == 0 and mem.index == 0:
                        continue
                    regname = insn.reg_name(mem.base) if mem.base else None
                    if regname == reg and mem.index == 0:
                        base_refs.append((loadva, reg, imm, name, insn.address, mem.disp, "%s %s" % (insn.mnemonic, insn.op_str)))

# ---- Pass 3: field writes [reg+0x80] byte and [reg+0x94] ----
w80 = []  # (va, insn_text, value or None, is_write, fn)
r80 = []
w94 = []
for insn in insns:
    for oi, op in enumerate(insn.operands):
        if op.type != capstone.x86.X86_OP_MEM:
            continue
        mem = op.mem
        if mem.base == 0:
            continue
        # +0x80 byte access
        if mem.disp == 0x80 and (mem.index == 0 or True):
            # operand width lives on the operand (op.size), not mem
            if op.size == 1:
                is_write = (oi == 0 and insn.mnemonic in ("mov", "and", "or", "xor", "inc", "dec", "add", "sub", "test", "cmp"))
                # be conservative: for mov, op0 is dest=write
                if insn.mnemonic == "mov":
                    is_write = (oi == 0)
                # capture value
                val = None
                valstr = ""
                if is_write and len(insn.operands) == 2 and insn.operands[1].type == capstone.x86.X86_OP_IMM:
                    val = insn.operands[1].imm
                    valstr = hex(val)
                elif is_write:
                    valstr = "REG/OTHER"
                rec = (insn.address, "%s %s" % (insn.mnemonic, insn.op_str), val, valstr, func_of(insn.address))
                if is_write:
                    w80.append(rec)
                else:
                    r80.append(rec)
        # +0x94 dword access
        if mem.disp == 0x94 and op.size == 4:
            val = None
            valstr = ""
            if len(insn.operands) == 2 and insn.operands[1].type == capstone.x86.X86_OP_IMM:
                val = insn.operands[1].imm
                valstr = hex(val)
            else:
                valstr = "REG/OTHER"
            is_write = (oi == 0 and insn.mnemonic in ("mov", "and", "or", "xor", "add", "sub", "inc", "dec"))
            if insn.mnemonic == "mov":
                is_write = (oi == 0)
            w94.append((insn.address, "%s %s" % (insn.mnemonic, insn.op_str), val, valstr, is_write, func_of(insn.address)))

# ---- write outputs ----
def w(rel, lines):
    p = os.path.join(OUTDIR, rel)
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", p, len(lines), "lines")

w("sweep_global_abs_refs.tsv",
  ["va\thins\t\tglobal\tglobal_name\tfunc"] )
# fix header
with open(os.path.join(OUTDIR, "sweep_global_abs_refs.tsv"), "w", encoding="utf-8") as f:
    f.write("va\thins\tglobal\tglobal_name\tfunc\n")
    for va, hins, g, name, fn in abs_refs:
        f.write("%08X\t%s\t%08X\t%s\t%s\n" % (va, hins, g, name, ("%08X" % fn) if fn else "-"))
print("abs_refs:", len(abs_refs))

with open(os.path.join(OUTDIR, "sweep_global_base_refs.tsv"), "w", encoding="utf-8") as f:
    f.write("load_va\treg\tbase\tbase_name\tref_va\toff\thins\n")
    for lv, reg, imm, name, rv, off, hins in base_refs:
        f.write("%08X\t%s\t%08X\t%s\t%08X\t%08X\t%s\n" % (lv, reg, imm, name, rv, off & 0xFFFFFFFF, hins))
print("base_refs:", len(base_refs))

with open(os.path.join(OUTDIR, "sweep_0x80_access.tsv"), "w", encoding="utf-8") as f:
    f.write("kind\tva\thins\tvalue\tvalstr\tfunc\n")
    for va, hins, val, valstr, fn in w80:
        f.write("WRITE\t%08X\t%s\t%s\t%s\t%s\n" % (va, hins, ("" if val is None else str(val)), valstr, ("%08X" % fn) if fn else "-"))
    for va, hins, val, valstr, fn in r80:
        f.write("READ\t%08X\t%s\t%s\t%s\t%s\n" % (va, hins, ("" if val is None else str(val)), valstr, ("%08X" % fn) if fn else "-"))
print("w80 writes:", len(w80), "r80 reads:", len(r80))

with open(os.path.join(OUTDIR, "sweep_0x94_access.tsv"), "w", encoding="utf-8") as f:
    f.write("va\thins\tvalue\tvalstr\tis_write\tfunc\n")
    for va, hins, val, valstr, iw, fn in w94:
        f.write("%08X\t%s\t%s\t%s\t%d\t%s\n" % (va, hins, ("" if val is None else str(val)), valstr, iw, ("%08X" % fn) if fn else "-"))
print("0x94 access:", len(w94))

# summary json
summary = {
    "total_insns": len(insns),
    "abs_refs_count": len(abs_refs),
    "base_refs_count": len(base_refs),
    "w80_count": len(w80), "r80_count": len(r80),
    "w80_funcs": len(set(x[4] for x in w80 if x[4])),
    "w94_count": len(w94),
}
with open(os.path.join(OUTDIR, "sweep_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
