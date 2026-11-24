#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S05-K2 T2/T3: independent .text scan of [reg+disp] accesses.
Splits DATA READS from VIRTUAL-SLOT CALLS (call/jmp [reg+disp]).
Attributes each access to enclosing function (interval containment) and class.
No import of S05-K1 work. capstone skipdata=True, detail=True.
"""
import pefile, os, json, bisect, collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM

ROOT = r"D:\Project\ra2-campaign-forge"
P = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
SJ = os.path.join(ROOT, "re_atlas", "evidence", "rtti", "symbols.json")
CHAIN = os.path.join(ROOT, "lead", "next_re_20261117_r14", "S05-K1", "EVIDENCE", "class_chain_core.json")
OUTDIR = os.path.join(ROOT, "lead", "next_re_20261117_r14", "S05-K2")
EVID = os.path.join(OUTDIR, "EVIDENCE")

pe = pefile.PE(P)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = []
for s in pe.sections:
    SECS.append((s.Name.rstrip(b"\0").decode(), s.VirtualAddress + IB, s.Misc_VirtualSize,
                 s.PointerToRawData, s.SizeOfRawData))
SM = {s[0]: s for s in SECS}
TEXT = SM[".text"]
DATA = open(P, "rb").read()

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.skipdata = True
MD.detail = True

# --- function intervals from atlas (for enclosing) ---
funcs = []
with open(ATLAS, encoding="utf-8") as f:
    f.readline()
    for line in f:
        p = line.rstrip("\n").split("\t")
        try:
            funcs.append((int(p[0], 16), int(p[1])))
        except Exception:
            pass
funcs.sort()
starts = [e for e, _ in funcs]
def enclosing(va):
    i = bisect.bisect_right(starts, va) - 1
    if i >= 0:
        e, sz = funcs[i]
        if e <= va < e + max(sz, 1):
            return e
    return None

# --- class attribution: symbols.json vfuncs + ctor_map (same audited source as S05-K1) ---
sj = json.load(open(SJ, encoding="utf-8", errors="replace"))
func_class = collections.defaultdict(set)
for nm, c in sj.get("classes", {}).items():
    short = nm
    if short.startswith("?"):
        continue
    for vf in c.get("vfuncs", []):
        try:
            func_class[int(vf, 16)].add(short)
        except Exception:
            pass
ctor_map = {
    0x410170: {'AbstractClass'}, 0x4101C0: {'AbstractClass'}, 0x4101F0: {'AbstractClass'}, 0x4105A0: {'AbstractClass'},
    0x5F3900: {'ObjectClass'}, 0x5F3B50: {'ObjectClass'}, 0x5F3B80: {'ObjectClass'},
    0x6F2B40: {'TechnoClass'}, 0x6F4300: {'TechnoClass'}, 0x6F4500: {'TechnoClass'},
    0x4D31E0: {'FootClass'}, 0x4D3540: {'FootClass'}, 0x4D3590: {'FootClass'},
    0x43B680: {'BuildingClass'}, 0x43B740: {'BuildingClass'}, 0x43BCF0: {'BuildingClass'},
    0x7353C0: {'UnitClass'}, 0x735780: {'UnitClass'}, 0x744470: {'UnitClass'},
    0x517A50: {'InfantryClass'}, 0x517D90: {'InfantryClass'}, 0x521960: {'InfantryClass'},
    0x413D20: {'AircraftClass'}, 0x414080: {'AircraftClass'}, 0x41B430: {'AircraftClass'},
}
for f, cs in ctor_map.items():
    func_class[f] |= cs

WRITE_MN = {'mov', 'movzx', 'movsx', 'add', 'sub', 'inc', 'dec', 'or', 'and', 'xor', 'adc', 'sbb',
            'neg', 'not', 'shl', 'shr', 'sar', 'imul', 'sete', 'setne', 'setz', 'setnz', 'seta', 'setb', 'setg', 'setl'}

# target disps: T2 five + references
TARGET = [0x10, 0x20, 0x74, 0x80, 0x81, 0x94, 0x21C, 0x1AC]
tset = set(TARGET)
access = {d: [] for d in TARGET}

n_insn = 0
n_skip = 0
base = DATA[TEXT[3]:TEXT[3] + TEXT[4]]
for ins in MD.disasm(base, TEXT[1]):
    n_insn += 1
    if ins.mnemonic == ".byte":
        n_skip += 1
    try:
        ops = ins.operands
    except Exception:
        continue
    if not ops:
        continue
    mn = ins.mnemonic
    # virtual-slot dispatch mnemonic (call/jmp through memory)
    for oi, op in enumerate(ops):
        if op.type != X86_OP_MEM:
            continue
        disp = int(op.mem.disp)
        if disp not in tset:
            continue
        has_index = op.mem.index != 0
        base_reg = ins.reg_name(op.mem.base) if op.mem.base else None
        index_reg = ins.reg_name(op.mem.index) if op.mem.index else None
        is_target = (mn in ("call", "jmp") and oi == 0)
        if is_target:
            kind = "vcall"      # virtual slot call/jmp -- NOT a data read
        elif mn == "lea":
            kind = "lea"        # address computation, no memory read
        elif oi == 0 and mn in WRITE_MN:
            kind = "write"
        else:
            kind = "read"
        f = enclosing(ins.address)
        access[disp].append({
            "va": ins.address, "mn": mn, "op": ins.op_str, "bytes": ins.bytes.hex(),
            "oi": oi, "base": base_reg, "index": index_reg, "disp": disp,
            "has_index": has_index, "kind": kind, "func": f,
            "classes": sorted(func_class.get(f, set())) if f else [],
        })

print("scanned insns", n_insn, "skipped(.byte)", n_skip)

FOCUS = {0x10: "AbstractClass", 0x20: "AbstractClass", 0x74: "ObjectClass",
         0x80: "ObjectClass", 0x81: "ObjectClass", 0x94: "ObjectClass",
         0x21C: "TechnoClass", 0x1AC: "TechnoClass"}

result = {
    "sha256": "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476",
    "scanned_insns": n_insn, "skipped": n_skip,
    "atlas_funcs": len(funcs),
    "method": "capstone5.0.7 skipdata=True detail=True; vcall=call/jmp mem-target; write=op0 mem & mnemon in WRITE_MN; read=other mem operand; lea separated; not-index filter applied to match S05-K1 caliber",
    "fields": {},
}
for d in TARGET:
    all_recs = access[d]
    # S05-K1 caliber: exclude index (scaled-index array) accesses from counts
    recs = [r for r in all_recs if not r["has_index"]]
    index_recs = [r for r in all_recs if r["has_index"]]
    vcalls = [r for r in recs if r["kind"] == "vcall"]
    reads = [r for r in recs if r["kind"] == "read"]
    writes = [r for r in recs if r["kind"] == "write"]
    leas = [r for r in recs if r["kind"] == "lea"]
    focus = FOCUS[d]
    def on_focus(r):
        return focus in r["classes"]
    fr = [r for r in reads if on_focus(r)]
    fw = [r for r in writes if on_focus(r)]
    fv = [r for r in vcalls if on_focus(r)]
    # "旧口径读点" = S05-K1: all non-write (incl vcall+lea)  -> for reconciliation
    old_reads = [r for r in recs if r["kind"] != "write"]
    result["fields"]["0x%X" % d] = {
        "focus": focus,
        "total_noidx": len(recs), "total_index_accesses": len(index_recs),
        "W": len(writes), "R_data": len(reads), "R_lea": len(leas),
        "vcall_excluded": len(vcalls),
        "old_readcount_S05K1": len(old_reads),  # data+lea+vcall (what S05-K1 called reads)
        "focus_W": len(fw), "focus_R_data": len(fr), "focus_vcall": len(fv),
        "focus_write_addrs": [("%08X" % r["va"], "%08X" % r["func"] if r["func"] else None, r["mn"], r["op"], r["base"]) for r in fw],
        "focus_read_addrs": [("%08X" % r["va"], "%08X" % r["func"] if r["func"] else None, r["mn"], r["op"], r["base"]) for r in fr],
        "focus_read_all_classes_detail": [
            {"va": "%08X" % r["va"], "func": "%08X" % r["func"] if r["func"] else None,
             "mn": r["mn"], "op": r["op"], "classes": r["classes"]}
            for r in reads
        ],
        "vcall_addrs": [("%08X" % r["va"], r["mn"], r["op"]) for r in vcalls],
        "class_read_hist": collections.Counter(c for r in reads for c in r["classes"]).most_common(),
        "class_write_hist": collections.Counter(c for r in writes for c in r["classes"]).most_common(),
    }
    print("field +0x%-4X %-14s W=%d R_data=%d R_lea=%d vcall_excl=%d (old_reads=%d) | focus %s W=%d R_data=%d vcall=%d" % (
        d, focus, len(writes), len(reads), len(leas), len(vcalls), len(old_reads), focus, len(fw), len(fr), len(fv)))

os.makedirs(EVID, exist_ok=True)
outp = os.path.join(EVID, "t2_field_rescan.json")
with open(outp, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=1, ensure_ascii=False)
print("WROTE", outp)
