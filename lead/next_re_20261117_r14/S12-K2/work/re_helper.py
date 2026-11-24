"""S12-K2 RE helper. Read-only access to gamemd.exe. capstone skipdata=True.
All paths relative to project root; run from anywhere via ROOT.
"""
import os, struct
import pefile
import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
CARD = os.path.join(ROOT, "lead", "next_re_20261117_r14", "S12-K2")
EVID = os.path.join(CARD, "EVIDENCE")
WORK = os.path.join(CARD, "work")
WORK2 = os.path.join(ROOT, "lead", "next_re_20261116_r12", "_lead_audit")

class Bin:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path, fast_load=True)
        self.image_base = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = []
        for s in self.pe.sections:
            name = s.Name.decode(errors="replace").rstrip("\x00")
            va = self.image_base + s.VirtualAddress
            self.sections.append(dict(name=name, va=va, vsize=s.Misc_VirtualSize,
                                      raw=s.PointerToRawData, rawsize=s.SizeOfRawData,
                                      flags=s.Characteristics))
    def sec(self, name):
        for s in self.sections:
            if s["name"] == name:
                return s
        raise KeyError(name)
    def read(self, va, n):
        for s in self.sections:
            if s["va"] <= va and va + n <= s["va"] + s["rawsize"]:
                off = s["raw"] + (va - s["va"])
                return self.pe.__data__[off:off+n]
        raise ValueError("VA %08X+%d not in any section raw range" % (va, n))
    def u32(self, va): return struct.unpack("<I", self.read(va, 4))[0]
    def u16(self, va): return struct.unpack("<H", self.read(va, 2))[0]
    def u8(self, va): return self.read(va, 1)[0]
    def i32(self, va): return struct.unpack("<i", self.read(va, 4))[0]

def md(skipdata=True, detail=True):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = detail
    m.skipdata = skipdata
    return m

def disasm_range(bin_, start, end, skipdata=True):
    """Linear disasm [start, end). Returns list of capstone insns (id 0 = skipdata .byte)."""
    data = bin_.read(start, end - start)
    m = md(skipdata=skipdata)
    return list(m.disasm(data, start))

def fmt_insn(insn, bin_=None):
    if insn.id == 0:
        return "%08X: .byte %s" % (insn.address, insn.bytes.hex())
    return "%08X: %-8s %s" % (insn.address, insn.mnemonic, insn.op_str)

def load_atlas(path=None):
    if path is None:
        path = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            line = line.rstrip("\n")
            if not line: continue
            parts = line.split("\t")
            rec = dict(zip(header, parts))
            try:
                va = int(rec.get("entry"), 16)
            except Exception:
                continue
            rec["_va"] = va
            rec["_size"] = int(rec.get("size", "0"))
            rows.append(rec)
    return rows, header

def atlas_lookup(rows, va):
    """Return exact entry row if va is an atlas entry, else None."""
    for r in rows:
        if r["_va"] == va: return r
    return None

def atlas_containing(rows, va):
    """Return (entry,row) whose [entry, entry+size) contains va; else None.
    Uses interval containment (NOT entry_at_or_before)."""
    for r in rows:
        if r["_va"] <= va < r["_va"] + r["_size"]:
            return r
    return None

def sweep_calls(bin_):
    """Byte-channel reference model: all direct call/jmp rel32 targets in .text.
    skipdata=True mandatory. Returns (calls, jmps, stat)."""
    m = md(skipdata=True)
    t = bin_.sec(".text")
    data = bin_.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    calls, jmps = {}, {}
    n = 0; nskip = 0
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0:
            nskip += insn.size
            continue
        n += 1
        op = insn.op_str.lower()
        if insn.mnemonic == "call" and op.startswith("0x"):
            tgt = int(op, 16)
            calls.setdefault(tgt, []).append(insn.address)
        elif insn.mnemonic == "jmp" and op.startswith("0x"):
            tgt = int(op, 16)
            jmps.setdefault(tgt, []).append(insn.address)
    return calls, jmps, dict(insns=n, skipped_bytes=nskip, text_bytes=len(data))

def sweep_disps(bin_, target_va):
    """All instructions referencing target_va via [abs] or [reg+disp]."""
    m = md(skipdata=True)
    t = bin_.sec(".text")
    data = bin_.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    found = []
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0: continue
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM:
                mem = op.mem
                if mem.base == 0 and mem.index == 0 and (mem.disp & 0xFFFFFFFF) == target_va:
                    found.append((insn.address, insn.mnemonic, insn.op_str, "abs"))
                elif mem.base != 0 and mem.disp == target_va:
                    found.append((insn.address, insn.mnemonic, insn.op_str, "reg+disp"))
    return found
