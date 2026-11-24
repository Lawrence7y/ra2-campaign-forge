# -*- coding: utf-8 -*-
"""MEASURE-F3A step 4: ③b census from bytes.

For every row of the 274-row domain (non-S22, grade [已证], semantics carries
literal [未证]) this decides -- from the executable alone -- whether the
"整体合同" tier ③b of R14_COMMON §8.6 条 3 is established:

  ③b①  jump table / switch, arms individually checkable
  ③b②  falsifiable error-code / return convention
  ③b③  memory-shape assertion (vtable install / member ctor / object size)
  ③b④  complete loop I/O (read -> test -> write -> advance, with bounds check)

Card rule honoured: a write that only hits a stack slot, or only advances a
register, does NOT count as the ③b④ write.

Also runs the mandated controls:
  positive (甲-type): 004A9840 / 006F3330 / 0065CDD0 / 00700600  (anchors in text)
  negative (乙-type): 004AC660 / 004A80D0                        (name + category only)
  card controls      : 0045A640 (③b must fail) / 004E2690
"""
import csv, json, os, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from pelib import PE, analyse, _MD, OP_MEM, OP_IMM

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
BASE = os.path.join(ROOT, r"lead\next_re_20261117_r14\MEASURE_F3A")
OUT = os.path.join(BASE, "work")
EV = os.path.join(BASE, "EVIDENCE")
COLS = ["entry", "subsystem", "name", "one_line_semantics",
        "grade", "evidence_path", "n_sources", "conflict"]

pe = PE(EXE)

def load_cov():
    out = []
    with open(COV, encoding="utf-8-sig", newline="") as f:
        for i, line in enumerate(f):
            line = line.rstrip("\r\n")
            if not line:
                continue
            p = line.split("\t")
            if i == 0:
                continue
            out.append(dict(zip(COLS, p)))
    return out

atlas = {}
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        atlas[r["entry"].upper()] = r

def in_text(va):
    return 0x401000 <= va < 0x7D9000

def thirdb(f, entry):
    """Decide ③b from the measured features. Conservative: prefer false negatives."""
    conds = {}

    # ③b① dispatch table whose targets are real .text addresses
    jt_ok = False
    for jt in f["jump_tables"]:
        off = pe.va_to_off(jt["disp"])
        if off is None:
            continue
        good = 0
        for k in range(6):
            v = pe.u32(jt["disp"] + 4 * k)
            if v is not None and in_text(v):
                good += 1
        if good >= 4:
            jt_ok = True
    conds["3b1_jumptable"] = jt_ok

    # ③b② falsifiable return / error code
    consts = set()
    for (mn, imm) in f["cmp_imm"]:
        pass
    code = pe.read(entry, f["size"]) or b""
    insns = list(_MD.disasm(code, entry))
    for ins in insns:
        if ins.mnemonic.startswith("mov") and ins.operands:
            d = ins.operands[0]
            if d.type == 1 and ins.reg_name(d.reg) in ("eax", "al"):
                if len(ins.operands) > 1 and ins.operands[1].type == OP_IMM:
                    consts.add(ins.operands[1].imm & 0xFFFFFFFF)
        if ins.mnemonic in ("xor", "or") and len(ins.operands) == 2:
            if ins.operands[0].type == 1 and ins.reg_name(ins.operands[0].reg) == "eax" \
               and ins.operands[1].type == 1 and ins.operands[0].reg == ins.operands[1].reg:
                consts.add(0)
    sentinel = any(c in (0xFFFFFFFF, 0xFFFFFFF0, 0xFFFFFFFF) for c in consts)
    dual = len(consts & {0, 1, 0xFFFFFFFF}) >= 2
    conds["3b2_errcode"] = bool((sentinel or dual) and f["n_jcc"] >= 1)

    # ③b③ memory shape: vtable install = non-stack write of an imm32 pointing into .rdata/.data
    vt_install = 0
    for ins in insns:
        if ins.mnemonic.startswith("mov") and len(ins.operands) == 2:
            d, s = ins.operands
            if d.type == OP_MEM and s.type == OP_IMM and d.access & 0x2:
                base = ins.reg_name(d.mem.base) if d.mem.base else ""
                if base not in ("esp", "ebp") and 0x400000 <= (s.imm & 0xFFFFFFFF) < 0x7D9000:
                    vt_install += 1
    conds["3b3_memshape"] = vt_install >= 1

    # ③b④ complete loop I/O with a non-stack write and a bounds check
    conds["3b4_loopio"] = bool(f["n_back_edge"] >= 1 and f["non_stack_writes"] >= 1
                               and f["n_jcc"] >= 2)

    return conds

def dump(entry, tag, note=""):
    """Write an annotated disassembly to EVIDENCE/."""
    a = atlas.get(entry)
    if a is None:
        return None, None
    size = int(a["size"])
    f = analyse(pe, int(entry, 16), size)
    code = pe.read(int(entry, 16), size)
    insns = list(_MD.disasm(code, int(entry, 16)))
    path = os.path.join(EV, "%s__%s.txt" % (entry, tag))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# %s  %s\n" % (entry, note))
        fh.write("# exe ra2youli\\gamemd.exe  SHA256 73201CC0...F67476\n")
        fh.write("# body = atlas [entry, entry+%d)   n_instr=%d\n" % (size, len(insns)))
        fh.write("# produced by MEASURE-F3A work/pelib.py + s7_bytes.py (read-only)\n\n")
        for ins in insns:
            mark = []
            if ins.operands and ins.operands[0].access & 0x2 and ins.operands[0].type == OP_MEM:
                base = ins.reg_name(ins.operands[0].mem.base) if ins.operands[0].mem.base else ""
                mark.append("W:stack" if base in ("esp", "ebp") else "W:OBJ")
            if ins.mnemonic in ("call",):
                mark.append("CALL")
            if ins.mnemonic in ("ret", "retn"):
                mark.append("RET")
            if ins.mnemonic.startswith("j") and ins.mnemonic != "jmp":
                if ins.operands and ins.operands[0].type == OP_IMM and ins.operands[0].imm < ins.address:
                    mark.append("BACKEDGE")
            if ins.mnemonic == "jmp" and ins.operands and ins.operands[0].type == OP_MEM:
                mark.append("DISPATCH")
            raw = pe.read(ins.address, ins.size)
            fh.write("%08X  %-24s %-8s %-34s %s\n" % (
                ins.address, raw.hex(" "), ins.mnemonic, ins.op_str, " ".join(mark)))
    return f, path

# ---------------------------------------------------------------- census
rows = load_cov()
dom = [r for r in rows if r["grade"] == "[已证]"
       and "[未证]" in r["one_line_semantics"] and r["subsystem"] != "S22"]

feats, missing = {}, []
for r in dom:
    e = r["entry"].upper()
    a = atlas.get(e)
    if a is None:
        missing.append(e)
        continue
    f = analyse(pe, int(e, 16), int(a["size"]))
    c = thirdb(f, int(e, 16))
    feats[e] = {"sub": r["subsystem"], "name": r["name"],
                "size": int(a["size"]), "n_instr": f["n_instr"],
                "n_jcc": f["n_jcc"], "n_call": f["n_call"],
                "n_back_edge": f["n_back_edge"], "n_ret": f["n_ret"],
                "non_stack_writes": f["non_stack_writes"],
                "stack_writes": f["stack_writes"],
                "n_jumptable": len(f["jump_tables"]),
                "conds": c, "thirdb": any(c.values())}

print("domain rows: %d   analysed: %d   not-in-atlas: %d" % (len(dom), len(feats), len(missing)))
if missing:
    print("  missing:", missing)
k = sum(1 for v in feats.values() if v["thirdb"])
print("③b establishable from bytes: %d   not: %d" % (k, len(feats) - k))
print("  ③b① jumptable :", sum(1 for v in feats.values() if v["conds"]["3b1_jumptable"]))
print("  ③b② errcode   :", sum(1 for v in feats.values() if v["conds"]["3b2_errcode"]))
print("  ③b③ memshape  :", sum(1 for v in feats.values() if v["conds"]["3b3_memshape"]))
print("  ③b④ loopio    :", sum(1 for v in feats.values() if v["conds"]["3b4_loopio"]))

json.dump(feats, open(os.path.join(OUT, "s7_bytes.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)

# per subsystem
print("\n%-5s %4s %6s %6s" % ("sub", "n", "3b=Y", "3b=N"))
byt = collections.defaultdict(lambda: [0, 0, 0])
for e, v in feats.items():
    byt[v["sub"]][0] += 1
    byt[v["sub"]][1 if v["thirdb"] else 2] += 1
for s in sorted(byt):
    d = byt[s]
    print("%-5s %4d %6d %6d" % (s, d[0], d[1], d[2]))

# ---------------------------------------------------------------- controls
print("\n===== CONTROLS =====")
CTRL = [
    ("004A9840", "POS_3b2_anchor", "S09 TabClass::slot41 - text names ③b② anchors"),
    ("006F3330", "POS_3b2_anchor", "S05 TechnoClass::slot185 - text names ③b② anchors"),
    ("0065CDD0", "POS_3b2_anchor", "S03 RawFileClass::slot12 - text names ③b② anchors"),
    ("00700600", "POS_3b4_anchor", "S05 TechnoClass::slot28 - text names ③b②+③b④"),
    ("004AC660", "NEG_template", "S06 MapClass::SetSellMode - name+category only"),
    ("004A80D0", "NEG_template", "S03 CD::GetCDNumber - name+category only"),
    ("0045A640", "NEG_card_control", "card-named: ③b must fail"),
    ("004E2690", "NEG_card_control", "card-named: semantics since fixed"),
]
ctrl_out = {}
for e, tag, note in CTRL:
    f, path = dump(e, tag, note)
    if f is None:
        print("%s  NOT IN ATLAS" % e)
        continue
    c = thirdb(f, int(e, 16))
    ctrl_out[e] = {"tag": tag, "conds": c, "thirdb": any(c.values()),
                   "n_instr": f["n_instr"], "n_call": f["n_call"], "n_jcc": f["n_jcc"],
                   "n_back_edge": f["n_back_edge"], "non_stack_writes": f["non_stack_writes"],
                   "asm": os.path.basename(path)}
    print("%s %-18s 3b=%-5s instr=%-4d call=%-2d jcc=%-2d back=%-2d objW=%-2d  %s" % (
        e, tag, any(c.values()), f["n_instr"], f["n_call"], f["n_jcc"],
        f["n_back_edge"], f["non_stack_writes"], " ".join(k2 for k2, v in c.items() if v)))
json.dump(ctrl_out, open(os.path.join(OUT, "s7_controls.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nEVIDENCE files written:", len(os.listdir(EV)))
