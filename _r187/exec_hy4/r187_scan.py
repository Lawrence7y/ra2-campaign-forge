#!/usr/bin/env python3
"""R187-EXEC: independent byte-level relocation-shape audit of 10 vtables."""
import json, struct, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
OUT = "/home/t628/projects/ra2-campaign-forge/_r187/exec_hy4"

CLASSES = [
    "?$DynamicVectorClass@PAE",
    "?$DynamicVectorClass@PAUWinsockBufferType@WinsockInterfaceClass@@",
    "?$DynamicVectorClass@PAU_DDSURFACEDESC@@",
    "?$DynamicVectorClass@PBVToolTip@@",
    "?$DynamicVectorClass@V?$DistributionObject@PAVCellClass@@@?$DiscreteDistributionClass@VCellClass@@@@",
    "CarryoverClass",
    "Dial8Class",
    "PKPipe",
    "TextButtonClass",
    "TriColorGaugeClass",
]

pe = pefile.PE(EXE, fast_load=True)
IMAGE_BASE = pe.OPTIONAL_HEADER.ImageBase
SECTS = []
for s in pe.sections:
    name = s.Name.rstrip(b"\0").decode("latin1")
    va = IMAGE_BASE + s.VirtualAddress
    SECTS.append({
        "name": name, "va": va, "vsize": s.Misc_VirtualSize,
        "raw": s.PointerToRawData, "rawsize": s.SizeOfRawData,
    })
DATA_SECTS = [s for s in SECTS if s["name"] in (".data", ".rdata")]
FILE_SIZE = len(open(EXE, "rb").read())

def sect_of_va(va):
    for s in SECTS:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["rawsize"]):
            return s["name"]
    return "?"

def sect_of_off(off):
    for s in SECTS:
        if s["raw"] <= off < s["raw"] + s["rawsize"]:
            return s["name"]
    return "?"

def off2va(off):
    for s in SECTS:
        if s["raw"] <= off < s["raw"] + s["rawsize"]:
            return s["va"] + (off - s["raw"])
    return None

def va2off(va):
    for s in SECTS:
        if s["va"] <= va < s["va"] + s["rawsize"]:
            return s["raw"] + (va - s["va"])
    return None

data = open(EXE, "rb").read()

def rd32_off(off):
    if 0 <= off + 4 <= FILE_SIZE:
        return struct.unpack_from("<I", data, off)[0]
    return None

def rd32_va(va):
    o = va2off(va)
    return rd32_off(o) if o is not None else None

# --- TypeDescriptors: locate inline type names matching '.?A'+class+'@@' ---
def find_tds():
    """Map class-name bytes to list of (TD VA, off, decoded name)."""
    result = {}
    for cls in CLASSES:
        needle = (".?AV" + cls + "@@").encode("latin1")
        positions = []
        start = 0
        while True:
            i = data.find(needle, start)
            if i < 0:
                break
            positions.append(i)
            start = i + 1
        tds = []
        for off in positions:
            # TD layout: +0 vftable, +4 spare, +8 name '.?AVClass@@'
            # (TD name is at TD+8 here, not TD+12 as in newer MSVC).
            td_off = off - 8
            td_va = off2va(td_off)
            # read full name until NUL to confirm
            end = data.find(b"\0", off, min(off + 512, FILE_SIZE))
            full = data[off:end].decode("latin1", "replace") if end > 0 else ""
            tds.append({"td_va": td_va, "td_off": td_off,
                        "name_off": off, "full_name": full})
        result[cls] = tds
    return result

TDS = find_tds()

# --- COLs: vtable-4 points to COL; COL fields: [0] in {0,1}, [8]==0,
#     [12]->TypeDescriptor, [16]->ClassHierarchyDescriptor ---
def valid_col(va):
    if va is None or va % 4:
        return None
    f0 = rd32_va(va)
    f8 = rd32_va(va + 8)
    f12 = rd32_va(va + 12)
    f16 = rd32_va(va + 16)
    if f0 in (0, 1) and f8 == 0 and f12 is not None and f16 is not None:
        return {"col_va": va, "td_va": f12, "chd_va": f16}
    return None

# Enumerate COLs in data sections by field pattern.
COLS = []
TD_TO_COLS = {}
for s in DATA_SECTS:
    for off in range(s["raw"], s["raw"] + s["rawsize"] - 20, 4):
        f0 = rd32_off(off)
        if f0 not in (0, 1):
            continue
        f8 = rd32_off(off + 8)
        if f8 != 0:
            continue
        va = off2va(off)
        col = valid_col(va)
        if col:
            COLS.append(col)
            TD_TO_COLS.setdefault(col["td_va"], []).append(col)
            # need: COL first dword is 0/1; +4 nonzero? not required by card.

# Enumerate vtables: for every 4-byte-aligned VA in data sections, check if
# the preceding dword points to a valid COL. A vtable begins there.
VTABLES_BY_TD = {}
for s in DATA_SECTS:
    for off in range(s["raw"] + 4, s["raw"] + s["rawsize"] - 4, 4):
        prev = rd32_off(off - 4)
        if prev is None:
            continue
        col = valid_col(prev)
        if not col:
            continue
        vt_va = off2va(off)
        if vt_va is None:
            continue
        VTABLES_BY_TD.setdefault(col["td_va"], []).append(vt_va)

# --- locate all byte-level occurrences of each vtable address (any alignment) ---
def find_all_occurrences(needle):
    pat = struct.pack("<I", needle)
    hits = []
    start = 0
    while True:
        i = data.find(pat, start)
        if i < 0:
            break
        hits.append(i)
        start = i + 1
    return hits

# --- local disassembly window around a hit (max 64 bytes) ---
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
md.skipdata = True

def disasm_window(off):
    lo = max(0, off - 24)
    hi = min(FILE_SIZE, off + 28)
    win = data[lo:hi]
    insns = []
    for ins in md.disasm(win, off2va(lo) or 0):
        insns.append({"va": ins.address, "off": lo + (ins.address - (off2va(lo) or 0)),
                      "bytes": ins.bytes.hex(), "mnem": ins.mnemonic, "op": ins.op_str,
                      "size": ins.size})
    # locate instruction containing off
    va_off = off2va(off)
    containing = None
    for ins in insns:
        if ins["off"] <= off < ins["off"] + ins["size"]:
            containing = ins
            break
    return {"lo": lo, "hi": hi, "insns": insns, "containing": containing}

REG32 = {"eax","ecx","edx","ebx","esp","ebp","esi","edi"}

def classify(off, vt_va, insns, containing):
    if containing is None:
        return {"form": "D", "detail": "no instruction spans the hit (data region or misaligned)",
                "ins": None, "register_flow": None}
    ins = containing
    m, o = ins["mnem"], ins["op"]
    # A: mov dword ptr [base+disp], imm32  (C7 /0)
    if m == "mov" and o.startswith("dword ptr [") and ", " in o:
        lhs, rhs = o.rsplit(", ", 1)
        if rhs == hex(vt_va) or rhs.lstrip("0x").lower() == format(vt_va, "x").lower():
            base = lhs.split("[", 1)[1].rstrip("]")
            stack = any(r in base for r in ("esp", "ebp"))
            idx = "]" in base and any(x in base for x in ("*", "eax+", "ecx+", "edx+", "ebx+", "esi+", "edi+"))
            if stack:
                return {"form": "C", "detail": "stack-base store", "ins": ins, "register_flow": None}
            return {"form": "A", "detail": "direct C7 mov store", "ins": ins, "register_flow": None}
    # B: mov r32, imm32 then store same reg (scan up to 64 bytes forward)
    if m == "mov" and o.count(",") == 1:
        dst, src = [x.strip() for x in o.split(",", 1)]
        if dst in REG32 and (src == hex(vt_va) or src.lower().lstrip("0x") == format(vt_va, "x").lower()):
            reg = dst
            fw_hi = min(FILE_SIZE, off + 64)
            fw = data[off:fw_hi]
            flows = []
            for nxt in md.disasm(fw, off2va(off) or 0):
                if nxt.address == ins["va"]:
                    continue
                nm, no = nxt.mnemonic, nxt.op_str
                if nm in ("mov", "movzx", "movsx") and no.startswith("dword ptr [") and no.endswith(", " + reg):
                    base = no[no.index("[") + 1:no.rindex("]")]
                    stack = any(r in base for r in ("esp", "ebp"))
                    f = {"va": nxt.address, "mnem": nm, "op": no,
                         "bytes": nxt.bytes.hex(), "stack": stack}
                    flows.append(f)
                    if stack:
                        return {"form": "C", "detail": "register loaded then stored to stack-base operand",
                                "ins": ins, "register_flow": flows}
                    return {"form": "B", "detail": "imm32 loaded to reg then stored to memory",
                            "ins": ins, "register_flow": flows}
            return {"form": "B", "detail": "imm32 loaded to reg (no store found in 64-byte forward window)",
                    "ins": ins, "register_flow": flows}
    # push imm32
    if m == "push" and (o == hex(vt_va) or o.lower().lstrip("0x") == format(vt_va, "x").lower()):
        return {"form": "D", "detail": "push imm32 (function argument)", "ins": ins, "register_flow": None}
    return {"form": "D", "detail": "other: " + m + " " + o, "ins": ins, "register_flow": None}

# --- build report ---
report = {
    "meta": {
        "exe": EXE, "sha256": "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476",
        "image_base": hex(IMAGE_BASE), "file_size": FILE_SIZE,
        "sections": SECTS, "total_cols_found": len(COLS),
    },
    "classes": [],
}
counts = {"checks": 0, "fails": 0}

for cls in CLASSES:
    tds = TDS.get(cls, [])
    vt_set = set()
    for td in tds:
        for vt in VTABLES_BY_TD.get(td["td_va"], []):
            vt_set.add(vt)
    entry = {"class": cls, "tds": tds, "vtables": [], "has_A_or_B": False}
    for vt in sorted(vt_set):
        occ = find_all_occurrences(vt)
        ventry = {"vt_va": hex(vt), "vt_off": va2off(vt), "occurrences": []}
        for off in occ:
            d = disasm_window(off)
            cls_d = classify(off, vt, d["insns"], d["containing"])
            ventry["occurrences"].append({
                "file_off": off, "va": off2va(off), "section": sect_of_off(off),
                "alignment": "4" if off % 4 == 0 else str(off % 4),
                "form": cls_d["form"], "detail": cls_d["detail"],
                "containing_ins": cls_d["ins"], "register_flow": cls_d["register_flow"],
                "window": d,
            })
            if cls_d["form"] in ("A", "B"):
                entry["has_A_or_B"] = True
        entry["vtables"].append(ventry)
    report["classes"].append(entry)
    counts["checks"] += 1
    if not tds or not vt_set:
        counts["fails"] += 1

report["counts"] = counts

with open(OUT + "/r187_report.json", "w") as f:
    json.dump(report, f, indent=2)

# --- compact human-readable summary ---
print("=== R187-EXEC RESULT ===")
print("exe sha256:", report["meta"]["sha256"])
print("sections:", ", ".join(s["name"] + hex(s["va"]) for s in SECTS))
print("COLs enumerated:", len(COLS))
print()
for e in report["classes"]:
    tds = e["tds"]
    print("CLASS", e["class"])
    print("  TDs:", ", ".join(hex(t["td_va"]) for t in tds) or "NONE")
    for v in e["vtables"]:
        print("  VT", v["vt_va"], "off", v["vt_off"], "occurrences", len(v["occurrences"]))
        for o in v["occurrences"]:
            ci = o["containing_ins"]
            s = "  off=%s va=%s sec=%s align=%s form=%s" % (
                hex(o["file_off"]), hex(o["va"] or 0), o["section"], o["alignment"], o["form"])
            if ci:
                s += " ins=%s %s" % (ci["mnem"], ci["op"])
            print(s + " | " + o["detail"])
    print("  => has_A_or_B:", e["has_A_or_B"])
print()
print("checks:", counts["checks"], "fails:", counts["fails"])
print("report:", OUT + "/r187_report.json")
