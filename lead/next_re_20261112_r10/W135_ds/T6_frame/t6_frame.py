# -*- coding: utf-8 -*-
"""
T6_frame.py -- static decomposition of gamemd.exe's state dispatcher
0x006DD8B0, focused on the "in game" case.

Deterministic, offline, re-runnable.  Reads only:
  D:\\Project\\ra2-campaign-forge\\ra2youli\\gamemd.exe
  ..\\..\\W130_atlas\\function_atlas.tsv
  ..\\..\\W130_atlas\\vtables_canonical.json
Writes only inside this directory.

PROXY, NOT TIME
---------------
proxy_score = per_frame_multiplicity x size(function, bytes).
Function size is a structural static quantity.  It is NOT observed cost, NOT a
count of instructions executed, NOT cycles.  Nothing here runs the game.
"""

import os
import csv
import json
import struct
import bisect

import pefile
import capstone

# --------------------------------------------------------------------------
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.abspath(os.path.join(HERE, "..", "..", "W130_atlas"))
FUNC_ATLAS = os.path.join(ATLAS, "function_atlas.tsv")
VTABLES = os.path.join(ATLAS, "vtables_canonical.json")

DISPATCH = 0x006DD8B0
DISPATCH_SIZE = 9530
SWITCH_TABLE = 0x006DFDEC
SWITCH_N = 0x91

# Per-type instance arrays (DynamicVectorClass<T*>): base, Items=base+4,
# Count=base+0x10.  The first ten come from the task brief; the last two were
# discovered by this analysis in case block 0x006DF5D1 and are *not* in the
# brief's table (see report.md, "newly found vector").
VECTORS = [
    ("TriggerClass",        0x00A8EAE8, 0x00A8EAEC, 0x00A8EAF8),
    ("FootClass",           0x008B3DC0, 0x008B3DC4, 0x008B3DD0),
    ("UnitClass",           0x008B4108, 0x008B410C, 0x008B4118),
    ("InfantryClass",       0x00A83DE8, 0x00A83DEC, 0x00A83DF8),
    ("AircraftClass",       0x00A8E390, 0x00A8E394, 0x00A8E3A0),
    ("BuildingClass",       0x00A8EB40, 0x00A8EB44, 0x00A8EB50),
    ("TechnoClass",         0x00A8EC78, 0x00A8EC7C, 0x00A8EC88),
    ("HouseClass",          0x00A80228, 0x00A8022C, 0x00A80238),
    ("ParticleSystemClass", 0x00A80208, 0x00A8020C, 0x00A80218),
    ("AbstractClass",       0x00B0F720, 0x00B0F724, 0x00B0F730),
    ("UNKNOWN@0xA8EB00",    0x00A8EB00, 0x00A8EB04, 0x00A8EB10),
]
ADDR2VEC = {}
for _n, _b, _i, _c in VECTORS:
    ADDR2VEC[_b] = _n
    ADDR2VEC[_i] = _n
    ADDR2VEC[_c] = _n


# --------------------------------------------------------------------------
def load():
    pe = pefile.PE(EXE, fast_load=True)
    img = pe.get_memory_mapped_image()
    base = pe.OPTIONAL_HEADER.ImageBase
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    md.skipdata = True
    return img, base, md


def decode(md, img, base, va, n):
    out = []
    for i in md.disasm(img[va - base:va - base + n], va):
        if i.id == 0:
            continue
        out.append(i)
    return out


def u32(img, base, va):
    b = img[va - base:va - base + 4]
    if len(b) < 4:
        return 0
    return struct.unpack("<I", b)[0]


def is_ret(i):
    return i.mnemonic.startswith("ret")


def is_cond(i):
    return i.mnemonic.startswith("j") and i.mnemonic != "jmp"


def imm(i):
    if i.operands and i.operands[0].type == capstone.x86.X86_OP_IMM:
        return int(i.operands[0].imm)
    return None


def insns_in(by, order, lo, hi):
    return [by[x] for x in order[bisect.bisect_left(order, lo):bisect.bisect_left(order, hi)]]


def vec_refs(insns):
    out = {}
    for i in insns:
        for op in i.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0:
                d = int(op.mem.disp) & 0xFFFFFFFF
                if d in ADDR2VEC:
                    out.setdefault(ADDR2VEC[d], []).append(i.address)
    return out


def read_atlas():
    sizes = {}
    if not os.path.isfile(FUNC_ATLAS):
        return sizes
    with open(FUNC_ATLAS, "r", encoding="utf-8", errors="replace") as fh:
        r = csv.reader(fh, delimiter="\t")
        next(r)
        for row in r:
            if len(row) < 2:
                continue
            try:
                sizes[int(row[0], 16)] = int(row[1])
            except ValueError:
                continue
    return sizes


def demangle(rtti):
    s = rtti
    if s.startswith(".?AV"):
        s = s[4:]
    return s.replace("@@", "")


def is_plain_class(name):
    """true for `FooClass` / `FooTypeClass`, false for templates/containers"""
    return "?$" not in name and name.endswith("Class") and "VectorClass" not in name


# --------------------------------------------------------------------------
def main():
    img, base, md = load()
    log = open(os.path.join(HERE, "run.log"), "w", encoding="utf-8")

    def L(*a):
        s = " ".join(str(x) for x in a)
        log.write(s + "\n")
        print(s)

    insns = decode(md, img, base, DISPATCH, DISPATCH_SIZE)
    order = sorted(i.address for i in insns)
    by = {i.address: i for i in insns}
    L("binary       :", EXE)
    L("function     : 0x%08X (atlas size %d)" % (DISPATCH, DISPATCH_SIZE))
    L("instructions : %d, span 0x%08X..0x%08X"
      % (len(insns), order[0], order[-1] + len(by[order[-1]].bytes)))
    L("dispatch gate (bytes at 0x006DD8D7):")
    for i in insns_in(by, order, 0x006DD8D7, 0x006DD8EE):
        L("   0x%08X  %-8s %s" % (i.address, i.mnemonic, i.op_str))

    tbl = [u32(img, base, SWITCH_TABLE + 4 * k) for k in range(SWITCH_N)]

    # each case block: switch target -> first ret
    def block_end(start, budget=4000):
        a = start
        while budget:
            i = by.get(a)
            if i is None:
                return None
            if is_ret(i):
                return a + len(i.bytes)
            a += len(i.bytes)
            budget -= 1
        return None

    blocks = []
    seen = set()
    for k, t in enumerate(tbl):
        if t in seen:
            continue
        seen.add(t)
        e = block_end(t)
        if e:
            blocks.append({"start": t, "end": e})
    for b in blocks:
        b["cases"] = [k for k, v in enumerate(tbl) if v == b["start"]]
    blocks.sort(key=lambda b: b["start"])
    L("switch table : 0x%08X, %d entries, %d distinct case blocks"
      % (SWITCH_TABLE, SWITCH_N, len(blocks)))

    case1_block = tbl[0]
    L("case 1 (state==1) -> block 0x%08X" % case1_block)

    # ---- case table ------------------------------------------------------
    with open(os.path.join(HERE, "switch_cases.tsv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["case_index", "state_value", "block_start", "block_end",
                    "n_insns", "vectors_touched", "n_backward_branches"])
        for b in blocks:
            body = insns_in(by, order, b["start"], b["end"])
            backs = [i for i in body if is_cond(i) and imm(i) is not None
                     and imm(i) < i.address and imm(i) >= b["start"]]
            for k in b["cases"]:
                w.writerow([k, k + 1, "0x%08X" % b["start"], "0x%08X" % b["end"],
                            len(body), ",".join(sorted(vec_refs(body))), len(backs)])

    # ---- loops -----------------------------------------------------------
    raw = []
    for b in blocks:
        for i in insns_in(by, order, b["start"], b["end"]):
            if not is_cond(i):
                continue
            t = imm(i)
            if t is None or t >= i.address or t < b["start"]:
                continue
            raw.append({"head": t, "backedge": i.address, "block": b["start"],
                        "cases": b["cases"]})

    loops = []
    for lp in sorted(raw, key=lambda x: (x["block"], x["head"])):
        if loops and loops[-1]["head"] == lp["head"] and loops[-1]["block"] == lp["block"]:
            loops[-1]["backedges"].append(lp["backedge"])
        else:
            loops.append({"head": lp["head"], "block": lp["block"],
                          "cases": lp["cases"], "backedges": [lp["backedge"]]})

    for lp in loops:
        end = max(lp["backedges"]) + 8
        lp["body"] = insns_in(by, order, lp["head"], end)
        vr = vec_refs(lp["body"])
        lp["vectors"] = vr
        # iterated list = the vector whose Count/Items read is nearest the head
        best, bestd = None, None
        for nm, vas in vr.items():
            d = min(abs(v - lp["head"]) for v in vas)
            if bestd is None or d < bestd:
                best, bestd = nm, d
        lp["iterates"] = best
        # inline byte-compare (strcmp) loops are NOT array iteration
        lp["note"] = ""
        if best is None:
            ops = [i.mnemonic for i in lp["body"]]
            if ops.count("mov") > 6 and any(
                    i.mnemonic == "mov" and "byte ptr" in i.op_str for i in lp["body"]):
                lp["note"] = "inline byte-compare (strcmp-like), not an array walk"
        depth = 1
        for o in loops:
            if o is lp or o["block"] != lp["block"] or o["head"] == lp["head"]:
                continue
            if o["head"] <= lp["head"] <= max(o["backedges"]) + 8:
                depth += 1
        lp["depth"] = depth

    sizes = read_atlas()
    L("atlas        : %d functions" % len(sizes))

    def direct_calls(lo, hi):
        return [(i.address, int(i.operands[0].imm))
                for i in insns_in(by, order, lo, hi)
                if i.mnemonic == "call" and i.operands
                and i.operands[0].type == capstone.x86.X86_OP_IMM]

    # ---- virtual calls ---------------------------------------------------
    vt_rows = resolve_virtuals(img, base, insns_in, by, order, loops)

    # ---- cost centres ----------------------------------------------------
    per = {}
    for lp in loops:
        end = max(lp["backedges"]) + 8
        for site, tgt in direct_calls(lp["head"], end):
            e = per.setdefault(tgt, {"why": [], "loops": set()})
            e["why"].append("direct 0x%08X" % site)
            e["loops"].add(lp["head"])
        for row in vt_rows:
            if row["loop_head"] != lp["head"]:
                continue
            for cls, fn in row["targets"]:
                e = per.setdefault(fn, {"why": [], "loops": set()})
                e["why"].append("vcall 0x%08X [%s+0x%X]" % (row["site"], cls, row["disp"]))
                e["loops"].add(lp["head"])

    rows = []
    for tgt, e in per.items():
        sz = sizes.get(tgt, 0)
        kinds = set()
        for w in e["why"]:
            kinds.add("direct" if w.startswith("direct") else "vcall-candidate")
        rows.append({"fn": tgt, "size": sz, "score": sz, "n_loops": len(e["loops"]),
                     "kind": "direct" if kinds == {"direct"} else
                             ("mixed" if "direct" in kinds else "vcall-candidate"),
                     "why": ",".join("0x%08X" % x for x in sorted(e["loops"]))})
    rows.sort(key=lambda r: (-r["score"], r["fn"]))

    with open(os.path.join(HERE, "cost_centres.tsv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["rank", "function", "per_frame_multiplicity", "size",
                    "proxy_score_N_times_size", "loop_heads", "n_loops",
                    "reach_kind", "certain_to_run"])
        for n, r in enumerate(rows, 1):
            w.writerow([n, "0x%08X" % r["fn"], "N", r["size"], r["score"],
                        r["why"], r["n_loops"], r["kind"],
                        "yes" if r["kind"] == "direct" else "no"])

    with open(os.path.join(HERE, "loops.tsv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["loop_head", "loop_backedge", "owner_case_block", "state_values",
                    "iterates_global", "direct_calls_in_body", "nesting_depth", "note"])
        for lp in loops:
            end = max(lp["backedges"]) + 8
            w.writerow(["0x%08X" % lp["head"],
                        ",".join("0x%08X" % b for b in lp["backedges"]),
                        "0x%08X" % lp["block"],
                        ",".join(str(c + 1) for c in lp["cases"]),
                        lp["iterates"] or "UNRESOLVED",
                        ";".join("0x%08X" % t for _s, t in direct_calls(lp["head"], end)) or "-",
                        lp["depth"], lp["note"]])

    L("")
    L("=== loops in the dispatcher (%d) ===" % len(loops))
    for lp in loops:
        L("  head 0x%08X  backedge %s  block 0x%08X  iterates %-22s depth %d %s"
          % (lp["head"], ",".join("0x%08X" % x for x in lp["backedges"]),
             lp["block"], lp["iterates"], lp["depth"], lp["note"]))
    L("")
    L("=== top 15 cost centres (N x size) ===")
    for n, r in enumerate(rows[:15], 1):
        L("  %2d 0x%08X size=%-6d score=%-6d loops %s"
          % (n, r["fn"], r["size"], r["score"], r["why"]))
    log.close()


def resolve_virtuals(img, base, insns_in, by, order, loops):
    vts = []
    if os.path.isfile(VTABLES):
        with open(VTABLES, "r", encoding="utf-8") as fh:
            vts = json.load(fh).get("vtables", [])

    # only real class vtables (skip containers / factories / templates)
    by_class = {}
    for v in vts:
        nm = demangle(v["class"])
        if is_plain_class(nm):
            by_class.setdefault(nm, []).append(int(v["vt"]))

    # containment: InfantryClass is-a FootClass is-a TechnoClass is-a ObjectClass
    def related(cls, target):
        return cls == target or cls.endswith(target) or target.endswith(cls)

    rows = []
    for lp in loops:
        cls = lp["iterates"] or ""
        if not cls.startswith(("Foot", "Infantry", "Unit", "Aircraft", "Building",
                               "Techno", "House", "Particle", "Trigger", "Abstract")):
            cls_cands = []
        else:
            cls_cands = [c for c in by_class if related(c, cls)]
        for n, i in enumerate(lp["body"]):
            if i.mnemonic != "call" or not i.operands:
                continue
            op = i.operands[0]
            if op.type != capstone.x86.X86_OP_MEM:
                continue
            disp = int(op.mem.disp) & 0xFFFFFFFF
            reg = i.reg_name(op.mem.base)
            src, off = None, None
            for j in range(n - 1, max(-1, n - 8), -1):
                p = lp["body"][j]
                if p.mnemonic == "mov" and len(p.operands) == 2 \
                        and p.operands[0].type == capstone.x86.X86_OP_REG \
                        and p.reg_name(p.operands[0].reg) == reg \
                        and p.operands[1].type == capstone.x86.X86_OP_MEM:
                    src = p.reg_name(p.operands[1].mem.base)
                    off = int(p.operands[1].mem.disp) & 0xFFFFFFFF
                    break
            targets = []
            if src is not None and off == 0 and cls_cands:
                seenf = set()
                for c in cls_cands:
                    for vt in by_class[c]:
                        t = u32(img, base, vt + disp)
                        if t and 0x401000 <= t < 0x7E038D and t not in seenf:
                            seenf.add(t)
                            targets.append((c, t))
            rows.append({"site": i.address, "loop_head": lp["head"],
                         "disp": disp, "iterates": cls, "form": i.op_str,
                         "targets": targets, "src": src})
    with open(os.path.join(HERE, "virtual_calls.tsv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["call_site", "loop_head", "iterates_global", "form",
                    "displacement", "vtable_ptr", "resolved_class", "resolved_target"])
        for r in rows:
            if r["targets"]:
                for c, t in r["targets"]:
                    w.writerow(["0x%08X" % r["site"], "0x%08X" % r["loop_head"],
                                r["iterates"], r["form"], "0x%X" % r["disp"],
                                "[%s+0]" % (r["src"] or "?"), c, "0x%08X" % t])
            else:
                w.writerow(["0x%08X" % r["site"], "0x%08X" % r["loop_head"],
                            r["iterates"], r["form"], "0x%X" % r["disp"],
                            "[%s+0]" % (r["src"] or "?"), "UNRESOLVED", ""])

    # Every site whose target cannot be pinned to ONE address.  Two distinct
    # reasons, kept separate so neither is silently folded into the other.
    with open(os.path.join(HERE, "unresolved_virtuals.tsv"), "w",
              encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["call_site", "loop_head", "displacement", "reason",
                    "candidate_count", "candidates"])
        for r in rows:
            if not r["targets"]:
                w.writerow(["0x%08X" % r["site"], "0x%08X" % r["loop_head"],
                            "0x%X" % r["disp"],
                            "object not loaded from a typed instance array "
                            "(loaded from a global); concrete class not inferable",
                            0, ""])
                continue
            cands = sorted(set("0x%08X" % t for _c, t in r["targets"]))
            if len(cands) > 1:
                w.writerow(["0x%08X" % r["site"], "0x%08X" % r["loop_head"],
                            "0x%X" % r["disp"],
                            "base-class vtable slot only; derived overrides not "
                            "enumerated in vtables_canonical.json",
                            len(cands), ",".join(cands)])
    return rows


if __name__ == "__main__":
    main()
