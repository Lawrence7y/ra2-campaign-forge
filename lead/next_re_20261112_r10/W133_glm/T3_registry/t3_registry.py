# -*- coding: utf-8 -*-
"""
T3_registry.py -- static-evidence analysis of the global
DynamicVectorClass<AbstractClass*> at 0xB0F720 in gamemd.exe.

Deterministic + re-runnable.  Reads gamemd.exe and the W130/W131 artifacts.
Writes ONLY inside W133_glm/T3_registry\\.

Run:  python -X utf8 t3_registry.py
"""
import bisect
import csv
import json
import os
import re
import struct
import traceback

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10"
FN_ATLAS = os.path.join(ROOT, "W130_atlas", "function_atlas.tsv")
CLS_ATLAS = os.path.join(ROOT, "W130_atlas", "class_atlas_v2.tsv")
EDGE_LOG = os.path.join(ROOT, "W131_subsystems", "calledges.raw.log")
OUT = os.path.join(ROOT, "W133_glm", "T3_registry")
DUMPS = os.path.join(OUT, "dumps")

IMG = 0x400000
G_VEC, G_ITEMS, G_CAP, G_COUNT = 0xB0F720, 0xB0F724, 0xB0F72C, 0xB0F730
TNAME = {G_VEC: "VEC", G_ITEMS: "ITEMS", G_CAP: "CAP", G_COUNT: "COUNT"}
RDATA_LO, RDATA_HI = 0x7E1000, 0x811074  # .rdata VA range (vftables live here)

CS_AC_WRITE = 2  # capstone op.access flag (hard-code to avoid binding-version issues)

KNOWN14 = [0x420960, 0x420AF0, 0x421730, 0x4C98B0, 0x4CA770, 0x4F54A0,
           0x5F3900, 0x5F3B80, 0x62DC50, 0x62DF20, 0x62E070, 0x6E8A90,
           0x6E8DE0, 0x7258D0]
STRAYS = [0x420D06, 0x420D13, 0x420D1B, 0x420D29,
          0x4C9AAD, 0x4C9ABA, 0x4C9AC2, 0x4C9AD0,
          0x7252D8, 0x725302, 0x725311, 0x725339]

CLASSES_OF_INTEREST = {
    "AbstractClass": [0x7E1F24, 0x7E1F2C, 0x7E1F34, 0x7E1F50],
    "ObjectClass":   [0x7EF034, 0x7EF03C, 0x7EF044, 0x7EF060],
    "TechnoClass":   [0x7F4934, 0x7F493C, 0x7F4944, 0x7F4960],
    "BuildingClass": [0x7E3E90, 0x7E3E98, 0x7E3EA0, 0x7E3EBC],
    "InfantryClass": [0x7EB02C, 0x7EB034, 0x7EB03C, 0x7EB058],
    "UnitClass":     [0x7F5C44, 0x7F5C4C, 0x7F5C54, 0x7F5C70],
    "AircraftClass": [0x7E2250, 0x7E2278, 0x7E2280, 0x7E2288, 0x7E22A4],
}

blob = None
secs = []
atlas = {}
entries_sorted = []
vft2cls = {}
callers_of = {}
callees_of = {}
iat = {}
md = None


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------
def load_binary():
    global blob, secs
    blob = open(EXE, "rb").read()
    pe = pefile.PE(data=blob, fast_load=True)
    pe.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
    for s in pe.sections:
        name = s.Name.rstrip(b"\x00").decode(errors="replace")
        va = IMG + s.VirtualAddress
        raw = s.SizeOfRawData
        secs.append(dict(name=name, va=va, raw_end=va + raw,
                         virt_end=va + max(raw, s.Misc_VirtualSize),
                         ptr=s.PointerToRawData))
    for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
        dll = entry.dll.decode(errors="replace")
        for imp in entry.imports:
            if imp.address:
                nm = imp.name.decode(errors="replace") if imp.name else ("ord#%d" % imp.ordinal)
                iat[imp.address] = dll + "!" + nm


def va_to_off(va):
    for sec in secs:
        if sec["va"] <= va < sec["raw_end"]:
            return sec["ptr"] + (va - sec["va"])
    return None


def read_va(va, n):
    off = va_to_off(va)
    if off is None:
        return None
    return blob[off:off + n]


def read32(va):
    b = read_va(va, 4)
    if b is None or len(b) < 4:
        return None
    return struct.unpack("<I", b)[0]


def cstr(va, maxlen=256):
    off = va_to_off(va)
    if off is None:
        return None
    end = blob.find(b"\x00", off, off + maxlen)
    if end < 0:
        end = off + maxlen
    return blob[off:end].decode("latin1")


def load_fn_atlas():
    global atlas, entries_sorted
    with open(FN_ATLAS, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f, delimiter="\t")
        for row in rdr:
            e = int(row["entry"], 16)
            atlas[e] = dict(size=int(row["size"], 16),
                            n_instr=int(row["n_instr"] or 0),
                            n_callers=int(row["n_callers"] or 0),
                            n_callees=int(row["n_callees"] or 0),
                            is_fnptr=int(row["is_fnptr"] or 0))
    entries_sorted = sorted(atlas)


def containing_fn(addr):
    i = bisect.bisect_right(entries_sorted, addr) - 1
    if i < 0:
        return None
    e = entries_sorted[i]
    if e <= addr < e + atlas[e]["size"]:
        return e
    return None


def load_cls_atlas():
    global vft2cls
    with open(CLS_ATLAS, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f, delimiter="\t")
        for row in rdr:
            nm = row["class"]
            prim = (row.get("primary") or "").strip()
            if prim:
                vft2cls[int(prim, 16)] = nm
            for t in (row.get("vtables") or "").split():
                vft2cls.setdefault(int(t, 16), nm)


def load_edges():
    global callers_of, callees_of
    pat = re.compile(r"CallEdges\.java>\s+([0-9a-fA-F]{8})\s+([0-9a-fA-F]{8})\s+([0-9a-fA-F]{8})")
    with open(EDGE_LOG, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = pat.search(line)
            if not m:
                continue
            caller, callee, site = (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16))
            callers_of.setdefault(callee, set()).add((caller, site))
            callees_of.setdefault(caller, set()).add((callee, site))


# --------------------------------------------------------------------------
# RTTI
# --------------------------------------------------------------------------
def rtti_name_for_vft(vft):
    c1 = read32(vft - 4)
    if c1 is None:
        return None
    for base1 in (IMG, 0):
        colva = c1 + base1
        if read_va(colva, 0x14) is None:
            continue
        c2 = read32(colva + 0x0C)
        if c2 is None:
            continue
        for base2 in (IMG, 0):
            tdva = c2 + base2
            nm = cstr(tdva + 8, 128)
            if nm and nm.startswith(".?A"):
                return nm
    return None


def demangle(nm):
    if not nm:
        return "?"
    if nm.startswith(".?A") and len(nm) > 5:
        body = nm[4:]
        if body.endswith("@@"):
            body = body[:-2]
        parts = [p for p in body.split("@") if p]
        if parts:
            return "::".join(reversed(parts))
    return nm


def ancestors_of_vft(vft):
    """All base-class RTTI names of the class owning this vftable, via its COL's
    ClassHierarchyDescriptor -> BaseClassArray.  None if RTTI unusable."""
    col = read32(vft - 4)
    if col is None:
        return None
    colva = col + IMG
    if read_va(colva, 0x14) is None:
        colva = col
        if read_va(colva, 0x14) is None:
            return None
    chd = read32(colva + 0x10)
    if chd is None:
        return None
    chdva = chd + IMG
    if read_va(chdva, 0x10) is None:
        chdva = chd
        if read_va(chdva, 0x10) is None:
            return None
    nbases = read32(chdva + 8)
    bcarr = read32(chdva + 0x0C)
    if bcarr is None or nbases is None:
        return None
    bcarrva = bcarr + IMG
    if read_va(bcarrva, 4) is None:
        bcarrva = bcarr
    out = []
    for i in range(nbases):
        bcd = read32(bcarrva + 4 * i)
        if bcd is None:
            continue
        tdr = read32(bcd + IMG if read_va(bcd + IMG, 4) else bcd)
        if tdr is None:
            continue
        nm = cstr(tdr + IMG + 8, 128)
        if nm:
            out.append(nm)
    return out


# --------------------------------------------------------------------------
# disassembly
# --------------------------------------------------------------------------
def disasm(va, n):
    off = va_to_off(va)
    if off is None:
        return []
    return list(md.disasm(blob[off:off + n], va))


def writes_reg(ins, reg):
    if ins.id == 0 or not ins.operands:
        return False
    op0 = ins.operands[0]
    if op0.type == X86_OP_REG:
        acc = getattr(op0, "access", 0) or 0
        if op0.reg == reg:
            if acc & CS_AC_WRITE or acc == 0:
                return True
    return False


def last_write_text(insns, idx, reg, maxback=30):
    for j in range(idx - 1, max(-1, idx - 1 - maxback), -1):
        ins = insns[j]
        if ins.id == 0:
            continue
        if writes_reg(ins, reg):
            return "%08X: %s %s" % (ins.address, ins.mnemonic, ins.op_str)
    return "?"


def trace_reg_delta(insns, idx, reg, maxback=14):
    """Infer +-1 delta of the value written into `reg` most recently before idx."""
    for j in range(idx - 1, max(-1, idx - 1 - maxback), -1):
        ins = insns[j]
        if ins.id == 0 or not ins.operands:
            continue
        if not writes_reg(ins, reg):
            continue
        m, ops = ins.mnemonic, ins.operands
        if m == "lea" and len(ops) == 2 and ops[1].type == X86_OP_MEM:
            mem = ops[1].mem
            if mem.scale == 1 and mem.index == 0 and mem.base != 0:
                if mem.disp == 1:
                    return 1, "lea [%s+1]" % ins.reg_name(mem.base)
                if mem.disp in (-1, 0xFFFFFFFF):
                    return -1, "lea [%s-1]" % ins.reg_name(mem.base)
            return None, "lea " + ins.op_str
        if m == "xor" and len(ops) == 2 and ops[1].type == X86_OP_REG and ops[0].reg == ops[1].reg:
            return 0, "xor reg,reg (clear)"
        if m == "inc":
            return 1, "inc reg"
        if m == "dec":
            return -1, "dec reg"
        if m == "add" and len(ops) > 1 and ops[1].type == X86_OP_IMM:
            return (ops[1].imm if ops[1].imm < 0x80000000 else ops[1].imm - 0x100000000), "add imm"
        if m == "sub" and len(ops) > 1 and ops[1].type == X86_OP_IMM:
            v = ops[1].imm if ops[1].imm < 0x80000000 else ops[1].imm - 0x100000000
            return -v, "sub imm"
        if m == "mov" and len(ops) > 1 and ops[1].type == X86_OP_MEM and ops[1].mem.disp == G_COUNT:
            return None, "load COUNT"
        return None, ins.mnemonic + " " + ins.op_str
    return None, "no-write-found"


def analyze_function(entry):
    meta = atlas.get(entry)
    size = meta["size"] if meta else 0
    insns = disasm(entry, size)
    rec = dict(entry=entry, size=size,
               n_callers=meta["n_callers"] if meta else None,
               is_fnptr=meta["is_fnptr"] if meta else None,
               n_instr_atlas=meta["n_instr"] if meta else None,
               glob_refs=[], count_writes=[], rdata_imms=[],
               array_stores=[], calls=[], jmps=[], iat_calls=[], rep_ops=[],
               callers=sorted("%08X@%08X" % (c, s) for (c, s) in callers_of.get(entry, ())),
               callees=sorted("%08X@%08X" % (c, s) for (c, s) in callees_of.get(entry, ())))
    n = len(insns)
    for idx, ins in enumerate(insns):
        if ins.id == 0:
            continue
        ops = ins.operands
        # global-vector memory refs
        for op in ops:
            if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 \
                    and op.mem.disp in TNAME:
                acc = getattr(op, "access", 0) or 0
                rec["glob_refs"].append(dict(
                    addr=ins.address, text="%s %s" % (ins.mnemonic, ins.op_str),
                    target=TNAME[op.mem.disp], rw=("W" if acc & CS_AC_WRITE else "R")))
        # rdata-range immediates (vftable candidates)
        if ins.mnemonic in ("mov", "push", "lea") or True:
            for op in ops:
                if op.type == X86_OP_IMM and RDATA_LO <= op.imm < RDATA_HI:
                    rec["rdata_imms"].append(dict(addr=ins.address,
                                                  text="%s %s" % (ins.mnemonic, ins.op_str),
                                                  imm=op.imm))
        # array element store: mov [base + idx*4], reg
        if ins.mnemonic == "mov" and len(ops) == 2 and \
                ops[0].type == X86_OP_MEM and ops[0].mem.scale == 4 and \
                ops[0].mem.index != 0 and ops[1].type == X86_OP_REG:
            rec["array_stores"].append(dict(
                addr=ins.address, text=ins.op_str,
                value_reg=ins.reg_name(ops[1].reg),
                value_origin=last_write_text(insns, idx, ops[1].reg)))
        # control flow
        if ins.mnemonic == "call" and ops and ops[0].type == X86_OP_IMM:
            tgt = ops[0].imm & 0xFFFFFFFF
            rec["calls"].append(dict(site=ins.address, target=tgt,
                                     in_atlas=bool(atlas.get(tgt))))
        elif ins.mnemonic == "call" and ops and ops[0].type == X86_OP_MEM \
                and ops[0].mem.base == 0 and ops[0].mem.disp in iat:
            rec["iat_calls"].append(dict(site=ins.address, what=iat[ops[0].mem.disp]))
        elif ins.mnemonic in ("call", "jmp") and ops and ops[0].type == X86_OP_IMM:
            rec["jmps"].append(dict(site=ins.address, target=ops[0].imm & 0xFFFFFFFF))
        if ins.bytes and ins.bytes[0] in (0xF2, 0xF3) and ins.mnemonic in ("movsd", "movsb", "stosd", "stosb"):
            rec["rep_ops"].append(dict(addr=ins.address, text=ins.mnemonic))
    # Count writes
    for idx, ins in enumerate(insns):
        if ins.id == 0 or not ins.operands:
            continue
        op0 = ins.operands[0]
        if op0.type != X86_OP_MEM or op0.mem.base != 0 or op0.mem.index != 0 \
                or op0.mem.disp != G_COUNT:
            continue
        acc = getattr(op0, "access", 0) or 0
        if not (acc & CS_AC_WRITE) and ins.mnemonic not in ("inc", "dec", "add", "sub", "mov"):
            continue
        m = ins.mnemonic
        if m == "inc":
            rec["count_writes"].append(dict(addr=ins.address, text=ins.op_str, delta=1, how="inc-mem"))
        elif m == "dec":
            rec["count_writes"].append(dict(addr=ins.address, text=ins.op_str, delta=-1, how="dec-mem"))
        elif m in ("add", "sub") and len(ins.operands) > 1 and ins.operands[1].type == X86_OP_IMM:
            v = ins.operands[1].imm if ins.operands[1].imm < 0x80000000 else ins.operands[1].imm - 0x100000000
            rec["count_writes"].append(dict(addr=ins.address, text=ins.op_str,
                                            delta=(v if m == "add" else -v), how=m + "-mem-imm"))
        elif m == "mov" and len(ins.operands) > 1:
            src = ins.operands[1]
            if src.type == X86_OP_REG:
                delta, how = trace_reg_delta(insns, idx, src.reg)
                rec["count_writes"].append(dict(addr=ins.address, text=ins.op_str,
                                                delta=delta, how="mov-reg:" + how))
            elif src.type == X86_OP_IMM:
                rec["count_writes"].append(dict(addr=ins.address, text=ins.op_str,
                                                delta="IMM=%d" % src.imm, how="mov-imm"))
    # classification
    deltas = [w["delta"] for w in rec["count_writes"] if isinstance(w["delta"], int)]
    if any(d > 0 for d in deltas) and not any(d < 0 for d in deltas):
        rec["classification"] = "push"
        rec["count_delta"] = "+1"
    elif any(d < 0 for d in deltas) and not any(d > 0 for d in deltas):
        rec["classification"] = "pop"
        rec["count_delta"] = "-1"
    elif any(d > 0 for d in deltas) and any(d < 0 for d in deltas):
        rec["classification"] = "mixed"
        rec["count_delta"] = "mixed(+1/-1)"
    else:
        rec["classification"] = "other"
        rec["count_delta"] = "none"
    # owning-class candidates: first rdata imm that is a known vftable
    vfts = []
    for imm in rec["rdata_imms"]:
        if imm["imm"] in vft2cls:
            vfts.append(dict(vft=imm["imm"], cls=vft2cls[imm["imm"]],
                             rtti=rtti_name_for_vft(imm["imm"]), addr=imm["addr"]))
    rec["vft_stores"] = vfts
    rec["owning_class"] = (demangle(vfts[0]["cls"]) if vfts else None)
    rec["owning_class_raw"] = (vfts[0]["cls"] if vfts else None)
    # items/count ref counts (verification of the established shape)
    rec["n_items_refs"] = sum(1 for g in rec["glob_refs"] if g["target"] == "ITEMS")
    rec["n_count_refs"] = sum(1 for g in rec["glob_refs"] if g["target"] == "COUNT")
    rec["n_vec_refs"] = sum(1 for g in rec["glob_refs"] if g["target"] == "VEC")
    rec["n_cap_refs"] = sum(1 for g in rec["glob_refs"] if g["target"] == "CAP")
    # site address = first decisive count write, else first glob ref
    if rec["count_writes"]:
        rec["site_addr"] = rec["count_writes"][0]["addr"]
    elif rec["glob_refs"]:
        rec["site_addr"] = rec["glob_refs"][0]["addr"]
    else:
        rec["site_addr"] = None
    return rec, insns


# --------------------------------------------------------------------------
# scanning
# --------------------------------------------------------------------------
def scan_text(pattern):
    hits = []
    for sec in secs:
        if sec["name"] != ".text":
            continue
        n = sec["raw_end"] - sec["va"]
        seg = blob[sec["ptr"]:sec["ptr"] + n]
        start = 0
        while True:
            i = seg.find(pattern, start)
            if i < 0:
                break
            hits.append(sec["va"] + i)
            start = i + 1
    return sorted(set(hits))


def insns_covering(insns, hit):
    for ins in insns:
        if ins.address <= hit < ins.address + ins.size:
            return ins
    return None


def dump_asm(entry, rec, insns, path, maxins=None):
    lines = ["; fn %08X  size=%X  n_callers=%s  is_fnptr=%s  classification=%s  owning=%s"
             % (entry, rec["size"], rec["n_callers"], rec["is_fnptr"],
                rec["classification"], rec["owning_class"])]
    if rec["vft_stores"]:
        lines.append("; vft stores: " + "; ".join(
            "%08X->%s(%s)@%08X" % (v["vft"], demangle(v["cls"]), v["rtti"], v["addr"])
            for v in rec["vft_stores"]))
    if rec["count_writes"]:
        lines.append("; count writes: " + "; ".join(
            "%08X %s delta=%s (%s)" % (w["addr"], w["text"], w["delta"], w["how"])
            for w in rec["count_writes"]))
    if rec["array_stores"]:
        lines.append("; array stores: " + "; ".join(
            "%08X %s <= %s (%s)" % (a["addr"], a["text"], a["value_reg"], a["value_origin"])
            for a in rec["array_stores"]))
    if rec["iat_calls"]:
        lines.append("; iat calls: " + "; ".join("%08X %s" % (c["site"], c["what"]) for c in rec["iat_calls"]))
    lines.append("")
    show = insns if maxins is None else insns[:maxins]
    for ins in show:
        if ins.id == 0:
            lines.append("%08X  %-20s .byte (skipdata)" % (ins.address, ins.bytes.hex()))
        else:
            lines.append("%08X  %-20s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    global md
    os.makedirs(DUMPS, exist_ok=True)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    md.detail = True

    load_binary()
    load_fn_atlas()
    load_cls_atlas()
    load_edges()

    evidence = dict(global_addr=dict(vec=G_VEC, items=G_ITEMS, cap=G_CAP, count=G_COUNT),
                    functions={}, sweep_hits={}, class_vft_scan={}, coverage=None,
                    strays={})

    _cache = {}

    def analyze(entry):
        if entry not in _cache:
            _cache[entry] = analyze_function(entry)
        return _cache[entry]

    # ------------------------------------------------------------------
    # 1) full sweep: every .text byte match for the four globals
    # ------------------------------------------------------------------
    all_fns_touched = set()
    gap_hits = {}
    for tgt, va in (("VEC", G_VEC), ("ITEMS", G_ITEMS), ("CAP", G_CAP), ("COUNT", G_COUNT)):
        pat = struct.pack("<I", va)
        hits = scan_text(pat)
        evidence["sweep_hits"][TNAME[va]] = dict(n_raw=len(hits),
                                                 addrs=["%08X" % h for h in hits])
        for h in hits:
            e = containing_fn(h)
            if e is None:
                gap_hits.setdefault(h & ~0x3F, []).append((h, TNAME[va]))
            else:
                all_fns_touched.add(e)

    print("=== sweep: functions touching the globals: %d" % len(all_fns_touched))
    extra = sorted(all_fns_touched - set(KNOWN14))
    missing = [f for f in KNOWN14 if f not in all_fns_touched]
    print("    known14 present: %d/14 ; extra fns: %s ; missing: %s"
          % (len(set(KNOWN14) & all_fns_touched),
             ", ".join("%08X" % e for e in extra) or "-", ", ".join("%08X" % e for e in missing) or "-"))

    # ------------------------------------------------------------------
    # 2) analyze + dump every function touching the globals
    # ------------------------------------------------------------------
    rows = []
    for e in sorted(all_fns_touched):
        rec, insns = analyze(e)
        evidence["functions"]["%08X" % e] = rec
        dump_asm(e, rec, insns, os.path.join(DUMPS, "fn_%08X.asm" % e),
                 maxins=None if rec["size"] <= 3000 else 400)
        rows.append(rec)

    # gap windows for stray hits
    gap_lines = []
    for base in sorted(gap_hits):
        lo, hi = base, base + 0x80
        gap_lines.append("; ---- gap window %08X..%08X, hits: %s"
                         % (lo, hi, ["%08X(%s)" % (h, t) for h, t in gap_hits[base]]))
        for ins in disasm(lo, hi - lo):
            if ins.id == 0:
                gap_lines.append("%08X  %-20s .byte" % (ins.address, ins.bytes.hex()))
            else:
                gap_lines.append("%08X  %-20s %s %s" % (ins.address, ins.bytes.hex(),
                                                        ins.mnemonic, ins.op_str))
        gap_lines.append("")
    with open(os.path.join(DUMPS, "stray_gap_windows.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(gap_lines) + "\n")
    for base, hits in sorted(gap_hits.items()):
        evidence["strays"]["%08X" % base] = ["%08X(%s)" % (h, t) for h, t in hits]

    # ------------------------------------------------------------------
    # 3) push/pop TSV (one row per function-direction)
    # ------------------------------------------------------------------
    with open(os.path.join(OUT, "push_sites.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["site_addr", "containing_fn", "push_or_pop", "count_delta",
                    "owning_class_if_known", "evidence"])
        for rec in sorted(rows, key=lambda r: r["entry"]):
            ev = []
            for g in rec["glob_refs"]:
                ev.append("%08X %s [%s]" % (g["addr"], g["text"], g["target"]))
            for a in rec["array_stores"]:
                ev.append("array-store %08X %s val=%s (%s)" % (a["addr"], a["text"],
                                                               a["value_reg"], a["value_origin"]))
            for v in rec["vft_stores"]:
                ev.append("vft-store %08X %s rtti=%s" % (v["addr"], v["cls"], v["rtti"]))
            if rec["iat_calls"]:
                ev += ["iat %08X %s" % (c["site"], c["what"]) for c in rec["iat_calls"]]
            if rec["rep_ops"]:
                ev += ["rep %08X %s" % (c["addr"], c["text"]) for c in rec["rep_ops"]]
            ev.append("refs: ITEMS=%d COUNT=%d CAP=%d VEC=%d" %
                      (rec["n_items_refs"], rec["n_count_refs"], rec["n_cap_refs"], rec["n_vec_refs"]))
            ev.append("callers: %s" % (", ".join(rec["callers"]) or "-"))
            dirs = [(rec["classification"], rec["count_delta"])]
            if rec["classification"] == "mixed":
                dirs = [("push", "+1"), ("pop", "-1")]
            for clsf, delta in dirs:
                w.writerow(["%08X" % (rec["site_addr"] or 0), "%08X" % rec["entry"],
                            clsf, delta, rec["owning_class"] or "?", " | ".join(ev)])
        # stray sites
        for base, hits in sorted(gap_hits.items()):
            for h, t in hits:
                w.writerow(["%08X" % h, "NO_IDENTIFIED_FN(gap@%08X)" % base,
                            "unknown(stray)", "n/a", "?", "global %s referenced in atlas gap; see dumps/stray_gap_windows.txt" % t])

    # ------------------------------------------------------------------
    # 4) class-of-interest vftable scans -> ctor/dtor candidates
    # ------------------------------------------------------------------
    for clsname, vfts in CLASSES_OF_INTEREST.items():
        fnmap = {}
        for v in vfts:
            for h in scan_text(struct.pack("<I", v)):
                e = containing_fn(h)
                if e is None:
                    fnmap.setdefault("GAP", {"vfts": set(), "hits": []})["vfts"].add(v)
                    fnmap["GAP"]["hits"].append((h, v))
                else:
                    fnmap.setdefault(e, {"vfts": set(), "hits": []})["vfts"].add(v)
                    fnmap[e]["hits"].append((h, v))
        cls_entry = dict(vfts=["%08X" % v for v in vfts], fns={})
        for e, info in sorted(fnmap.items()):
            if e == "GAP":
                cls_entry["fns"]["GAP"] = dict(vfts=["%08X" % v for v in sorted(info["vfts"])],
                                               hits=["%08X" % h for h, _ in info["hits"]])
                continue
            rec, insns = analyze(e)
            cls_entry["fns"]["%08X" % e] = dict(
                size=rec["size"], n_callers=rec["n_callers"],
                classification=rec["classification"], count_delta=rec["count_delta"],
                stores_these_vfts=["%08X" % v for v in sorted(info["vfts"])],
                all_vfts_stored=[dict(vft="%08X" % v["vft"], cls=v["cls"],
                                      rtti=v["rtti"]) for v in rec["vft_stores"]],
                glob_refs=[dict(addr="%08X" % g["addr"], target=g["target"], rw=g["rw"],
                                text=g["text"]) for g in rec["glob_refs"]],
                callers=rec["callers"][:12])
            evidence["functions"]["%08X" % e] = rec
            want_dump = (clsname == "AbstractClass") or (rec["classification"] in ("push", "pop")) \
                or (rec["size"] <= 400)
            if want_dump:
                dump_asm(e, rec, insns,
                         os.path.join(DUMPS, "vft_%s_%08X.asm" % (clsname, e)),
                         maxins=None if rec["size"] <= 3000 else 400)
        evidence["class_vft_scan"][clsname] = cls_entry
        print("=== %s vft scan: %d candidate functions" % (clsname, len(cls_entry["fns"])))

    # ------------------------------------------------------------------
    # 5) RTTI coverage: ancestors for all classes with a primary vftable
    # ------------------------------------------------------------------
    # registering classes = owning classes of push sites
    reg_classes = set()
    for rec in rows:
        if rec["classification"] in ("push", "mixed") and rec["owning_class_raw"]:
            reg_classes.add(rec["owning_class_raw"])
    coverage = dict(registering_classes=sorted(reg_classes), classes={}, uncovered=[])
    # also consider push helpers discovered later; re-run of script picks up manual add:
    extra_reg = os.path.join(OUT, "extra_registering_classes.txt")
    if os.path.exists(extra_reg):
        for line in open(extra_reg, encoding="utf-8"):
            line = line.strip()
            if line:
                reg_classes.add(line)
        coverage["registering_classes"] = sorted(reg_classes)
    ncls = 0
    for vft, clsname in sorted(vft2cls.items()):
        if vft < RDATA_LO or vft >= RDATA_HI:
            continue
        anc = ancestors_of_vft(vft)
        if anc is None:
            continue
        ncls += 1
        has_abstract = ".?AVAbstractClass@@" in anc
        covered = bool(reg_classes & set(anc))
        coverage["classes"].setdefault(clsname, dict(
            is_abstract_derived=has_abstract,
            covered_by_registration=covered,
            ancestors_sample=anc[:8]))
        if has_abstract and not covered:
            coverage["uncovered"].append(clsname)
    coverage["n_classes_with_rtti"] = ncls
    coverage["n_abstract_derived"] = sum(
        1 for c in coverage["classes"].values() if c["is_abstract_derived"])
    coverage["n_abstract_derived_uncovered"] = len(coverage["uncovered"])
    evidence["coverage"] = coverage
    print("=== RTTI coverage: %d classes with usable RTTI; abstract-derived=%d; uncovered=%d"
          % (ncls, coverage["n_abstract_derived"], coverage["n_abstract_derived_uncovered"]))
    if coverage["uncovered"]:
        print("    uncovered sample: " + ", ".join(sorted(coverage["uncovered"])[:20]))

    with open(os.path.join(OUT, "evidence.json"), "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=1, sort_keys=True)

    # ------------------------------------------------------------------
    # 6) console summary of the 14 known functions
    # ------------------------------------------------------------------
    print("\n=== KNOWN14 classification:")
    for e in KNOWN14:
        rec = evidence["functions"].get("%08X" % e)
        if not rec:
            print("  %08X  (no glob refs found!)" % e)
            continue
        print("  %08X size=%-5X cls=%-6s delta=%-11s own=%-16s callers=%d ITEMS=%d COUNT=%d vft=%s"
              % (e, rec["size"], rec["classification"], rec["count_delta"],
                 rec["owning_class"] or "?", rec["n_callers"] or 0,
                 rec["n_items_refs"], rec["n_count_refs"],
                 ",".join(demangle(v["cls"]) for v in rec["vft_stores"]) or "-"))

    # abstract class ctor candidates summary
    print("\n=== AbstractClass vft-store functions:")
    ac = evidence["class_vft_scan"]["AbstractClass"]
    for k, v in sorted(ac["fns"].items()):
        print("  %s size=%s cls=%s delta=%s vfts=%s glob=%s callers=%s"
              % (k, v.get("size"), v.get("classification"), v.get("count_delta"),
                 ",".join(demangle(x["cls"]) for x in v.get("all_vfts_stored", [])) or "-",
                 len(v.get("glob_refs", [])), v.get("callers", [])[:3]))

    print("\nDone. Artifacts in %s" % OUT)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        tb = traceback.format_exc()
        print(tb)
        try:
            with open(os.path.join(OUT, "error.log"), "w", encoding="utf-8") as f:
                f.write(tb)
        except Exception:
            pass
