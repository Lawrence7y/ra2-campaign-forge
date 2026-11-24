"""W161 static cost attribution library (capstone 5.0.7 + pefile only).

Written independently for card W161. Did NOT import or copy code from _lead_audit;
only observed the general approach (VA addressing, skipdata, boundary check).

Design decisions (respect R12_FACTS §6.2 discipline):
  - All addressing by VA (ImageBase 0x400000).
  - capstone disasm ALWAYS skipdata=True for full-section sweeps (else silently stops).
  - Byte channel: full .text linear sweep (independent of function_atlas entry+size).
  - Atlas channel: linear disasm from function entries (function_atlas.tsv; size is DECIMAL).
  - boundary_check: from a known function entry, linear-disasm to target, see if an
    instruction starts exactly at target.
"""
import struct
import pefile
import capstone

IMAGE_BASE = 0x400000
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
CALLEDGES = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W131_subsystems\calledges.raw.log"
VTMEM = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W131_subsystems\vtable_members.tsv"
VTABLES_CANON = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json"

class Bin:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path, fast_load=True)
        self.image_base = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = []
        for s in self.pe.sections:
            name = s.Name.decode(errors="replace").rstrip("\x00")
            va = self.image_base + s.VirtualAddress
            self.sections.append(dict(name=name, va=va, vsize=s.Misc_VirtualSize,
                                      raw=s.PointerToRawData, rawsize=s.SizeOfRawData))
        self.text = self.sec(".text")

    def sec(self, name):
        for s in self.sections:
            if s["name"] == name:
                return s
        raise KeyError(name)

    def read(self, va, n):
        for s in self.sections:
            if s["va"] <= va and va + n <= s["va"] + s["rawsize"]:
                off = s["raw"] + (va - s["va"])
                return self.pe.__data__[off:off + n]
        raise ValueError("VA %08X+%d not in any raw section range" % (va, n))

    def u32(self, va):
        return struct.unpack("<I", self.read(va, 4))[0]

    def section_bytes(self, name):
        s = self.sec(name)
        return self.pe.__data__[s["raw"]:s["raw"] + s["rawsize"]]

    def sec_of(self, va):
        for s in self.sections:
            if s["va"] <= va < s["va"] + s["vsize"]:
                return s
        return None


def md32(skipdata=True):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = skipdata
    return m


def linear_from(b, start_va, max_bytes, stop_at=None, skipdata=False):
    m = md32(skipdata=skipdata)
    data = b.read(start_va, max_bytes)
    out = []
    for insn in m.disasm(data, start_va):
        out.append(insn)
        if stop_at is not None and insn.address >= stop_at:
            break
    return out


def boundary_check(b, entry_va, target_va, max_bytes=0x4000):
    """(is_boundary, insn_or_None, reason). Linear disasm from entry; no jump following."""
    if target_va < entry_va:
        return (False, None, "target<entry")
    span = target_va - entry_va
    if span >= max_bytes:
        return (False, None, "span>=max_bytes")
    insns = linear_from(b, entry_va, span + 32, skipdata=False)
    for insn in insns:
        if insn.address == target_va:
            return (True, insn, "ok")
    for insn in insns:
        if insn.address < target_va < insn.address + insn.size:
            return (False, insn, "inside insn @%08X sz%d %s %s" %
                    (insn.address, insn.size, insn.mnemonic, insn.op_str))
    return (False, None, "linear disasm did not reach target")


def load_atlas(path=ATLAS):
    rows = []
    header = None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split("\t")
            rec = dict(zip(header, parts))
            try:
                va = int(rec["entry"], 16)
            except Exception:
                continue
            rows.append((va, rec))
    rows.sort(key=lambda t: t[0])
    return rows, header


def entry_at_or_before(rows, va):
    lo, hi = 0, len(rows) - 1
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if rows[mid][0] <= va:
            best = rows[mid]
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def load_calledges(path=CALLEDGES):
    """caller->set(callee), plus list of (caller,callee,site)."""
    by_caller = {}
    edges = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if "CallEdges.java>" not in line:
                continue
            seg = line.split("CallEdges.java>", 1)[1].strip()
            parts = seg.split()
            if len(parts) < 3:
                continue
            try:
                c = int(parts[0], 16); cal = int(parts[1], 16); site = int(parts[2], 16)
            except Exception:
                continue
            by_caller.setdefault(c, set()).add(cal)
            edges.append((c, cal, site))
    return by_caller, edges


def load_vtable_members(path=VTMEM):
    """dict vt(int)-> list of (slot:int, fn:int, is_code:int)."""
    out = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline()
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 5:
                continue
            try:
                vt = int(parts[0], 16); slot = int(parts[2]); fn = int(parts[3], 16)
                is_code = int(parts[4])
            except Exception:
                continue
            out.setdefault(vt, []).append((slot, fn, is_code))
    for vt in out:
        out[vt].sort()
    return out


def sweep_full_text(b):
    """Full .text linear disasm with skipdata=True. Independent of atlas.
    Returns dicts: call_targets[tgt]->[site...], jmp_targets[tgt]->[site...],
    stats dict(insns, skipped_bytes, text_bytes, n_call_insns, n_mem_insns)."""
    m = md32(skipdata=True)
    t = b.text
    data = b.section_bytes(".text")
    calls, jmps = {}, {}
    n = 0; n_skip = 0; n_call = 0; n_mem = 0
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0:
            n_skip += insn.size
            continue
        n += 1
        if any(op.type == capstone.x86.X86_OP_MEM for op in insn.operands):
            n_mem += 1
        if insn.mnemonic == "call":
            n_call += 1
            op = insn.operands[0] if insn.operands else None
            if op is not None and op.type == capstone.x86.X86_OP_IMM:
                calls.setdefault(op.imm, []).append(insn.address)
        elif insn.mnemonic == "jmp":
            op = insn.operands[0] if insn.operands else None
            if op is not None and op.type == capstone.x86.X86_OP_IMM:
                jmps.setdefault(op.imm, []).append(insn.address)
    return calls, jmps, dict(insns=n, skipped_bytes=n_skip, text_bytes=len(data),
                              n_call_insns=n_call, n_mem_insns=n_mem)


def sweep_disps_to(b, target_va):
    """Find instructions referencing target_va as absolute disp ([0xTARGET]) in .text.
    skipdata=True; returns list of dict(va, insn, kind)."""
    m = md32(skipdata=True)
    data = b.section_bytes(".text")
    found = []
    for insn in m.disasm(data, b.text["va"]):
        if insn.id == 0:
            continue
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM:
                mem = op.mem
                if mem.base == 0 and mem.index == 0 and (mem.disp & 0xFFFFFFFF) == target_va:
                    found.append(dict(va=insn.address, insn="%s %s" % (insn.mnemonic, insn.op_str), kind="abs"))
    return found


def insn_stats(b, va, size):
    """Linear disasm one function body (skipdata=False for clean count within known fn).
    Returns (n_insn, n_mem, n_call, n_backedge, n_backedge_origin, list_of_insns, n_skipdata)."""
    m = md32(skipdata=False)
    data = b.read(va, size)
    out = []
    n_skip = 0
    for insn in m.disasm(data, va):
        out.append(insn)
    if len(out) == 0 or (out[-1].address + out[-1].size) < va + size:
        m2 = md32(skipdata=True)
        out2 = []
        for insn in m2.disasm(data, va):
            if insn.id == 0:
                n_skip += insn.size
            else:
                out2.append(insn)
        out = out2
    n_insn = len(out)
    n_mem = sum(1 for i in out if any(op.type == capstone.x86.X86_OP_MEM for op in i.operands))
    n_call = sum(1 for i in out if i.mnemonic == "call")
    origins = []
    JCC = {"jmp","je","jne","jz","jnz","ja","jae","jb","jbe","jg","jge","jl","jle",
           "jc","jnc","jo","jno","js","jns","jp","jnp","loop","loope","loopne"}
    for i in out:
        if i.mnemonic in JCC:
            for op in i.operands:
                if op.type == capstone.x86.X86_OP_IMM and op.imm <= i.address:
                    origins.append((i.address, op.imm, i.mnemonic))
    return n_insn, n_mem, n_call, len(origins), origins, out, n_skip


if __name__ == "__main__":
    b = Bin()
    print("ImageBase", hex(b.image_base))
    for s in b.sections:
        print("  %-8s va=%08X vsize=%08X raw=%08X rawsize=%08X" %
              (s["name"], s["va"], s["vsize"], s["raw"], s["rawsize"]))
