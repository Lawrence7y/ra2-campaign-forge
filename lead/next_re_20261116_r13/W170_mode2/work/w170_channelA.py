"""W170 mode 2 + [+0x81] analysis — channel A: pure capstone/pefile byte-level.
Independent implementation (does NOT import audit_lib.py, does NOT use function_atlas
entry+size for the exhaustive Q2 scan).  capstone skipdata=True everywhere.
ImageBase 0x400000.  All addresses are VA.
"""
import struct, sys, os, bisect
import pefile, capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r13\W170_mode2\EVIDENCE"
IMAGE_BASE = 0x400000


class Bin:
    def __init__(self):
        self.pe = pefile.PE(EXE, fast_load=True)
        self.ib = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = []
        for s in self.pe.sections:
            name = s.Name.decode(errors="replace").rstrip("\x00")
            va = self.ib + s.VirtualAddress
            self.sections.append(dict(name=name, va=va, vsize=s.Misc_VirtualSize,
                                      raw=s.PointerToRawData, rawsize=s.SizeOfRawData))
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
        raise ValueError("VA %08X+%d not in raw" % (va, n))
    def u32(self, va): return struct.unpack("<I", self.read(va, 4))[0]
    def u8(self, va): return self.read(va, 1)[0]


def md(skipdata=True):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = skipdata
    return m


def load_atlas():
    rows = []
    with open(ATLAS, "r", encoding="utf-8", errors="replace") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            p = line.rstrip("\n").split("\t")
            if not p or not p[0]: continue
            try: entry = int(p[0], 16)
            except: continue
            rows.append((entry, dict(zip(hdr, p))))
    rows.sort(key=lambda t: t[0])
    return rows


def atlas_lookup(rows, va):
    i = bisect.bisect_right([r[0] for r in rows], va) - 1
    if i >= 0 and va < rows[i][0] + int(rows[i][1].get("size", "0")):
        return rows[i][1]
    return None


def disasm_range(b, start, nbytes, maxins=None):
    m = md(skipdata=True)
    data = b.read(start, nbytes)
    out = []
    for ins in m.disasm(data, start):
        if ins.id == 0:
            continue
        out.append(ins)
        if maxins and len(out) >= maxins:
            break
    return out


def fmt(ins):
    return "  %08X  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str)


def dump(title, lines, fn):
    path = os.path.join(OUT, fn)
    with open(path, "w", encoding="utf-8") as f:
        f.write(title + "\n")
        f.write("=" * len(title) + "\n")
        for ln in lines:
            f.write(ln + "\n")
    print("WROTE", path, "(%d lines)" % len(lines))


def q1_mode2(b, rows):
    lines = []
    lines.append("MODE2 · BuildingClass slot73 mode=2 branch 0x43F9A6")
    lines.append("(linear disasm from 0x43F9A6 until 0x43FB0C jump table; skipdata=True)")
    lines.append("")
    # 0x43F9A6 .. before jump table 0x43FB0C = 0x166 bytes; dump 0x170 to be safe
    insns = disasm_range(b, 0x43F9A6, 0x168)
    for ins in insns:
        if ins.address >= 0x43FB0C:
            break
        lines.append(fmt(ins))
    lines.append("")
    lines.append("total instructions dumped: %d" % len([i for i in insns if i.address < 0x43FB0C]))
    dump("Q1 mode2 branch full disasm (no truncation)", lines, "Q1_mode2_branch.txt")

    # resolve 4 virtual slots on BuildingClass main table vt=0x7E3EBC col_off=0
    vt = 0x7E3EBC
    slots = [(0x1E4, "call [vptr+0x1E4]"), (0x1BC, "call [vptr+0x1BC]"),
             (0x464, "call [vptr+0x464]"), (0x160, "call [vptr+0x160]")]
    lines2 = []
    lines2.append("BuildingClass main table vt=0x7E3EBC col_off=0; slot targets")
    lines2.append("")
    resolved = {}
    for off, label in slots:
        addr_va = vt + off
        target = b.u32(addr_va)
        resolved[off] = target
        a = atlas_lookup(rows, target)
        lines2.append("%s : [vt+0x%X]=@%08X -> %08X  atlas=%s" % (
            label, off, addr_va, target,
            ("entry=%s size=%s n_instr=%s n_callers=%s is_fnptr=%s" %
             (a["entry"], a["size"], a["n_instr"], a["n_callers"], a["is_fnptr"])) if a else "NONE"))
    lines2.append("")
    for off, label in slots:
        target = resolved[off]
        lines2.append("--- first 16 instructions of %s -> %08X ---" % (label, target))
        a = atlas_lookup(rows, target)
        nbytes = int(a["size"]) if a else 0x80
        try:
            insns = disasm_range(b, target, min(nbytes, 0x200), maxins=16)
            for ins in insns: lines2.append(fmt(ins))
        except Exception as e:
            lines2.append("  ERR %s" % e)
        lines2.append("")
    dump("Q1 virtual slot resolution + callee heads", lines2, "Q1_vt_slots.txt")
    return resolved


def scan_mem81(b, read_or_write):
    """Full .text linear disasm, skipdata=True.  Return list of (site, insn_text, kind, disp_value, base_reg, access).
    Detect X86_OP_MEM with disp == 0x81 (or absolute == 0x81), op.size == 1 (byte).
    base_reg: name of op.mem.base (None if absolute)."""
    m = md(skipdata=True)
    t = b.sec(".text")
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    hits = []
    nins = 0
    nskip = 0
    for ins in m.disasm(data, t["va"]):
        if ins.id == 0:
            nskip += ins.size
            continue
        nins += 1
        for op in ins.operands:
            if op.type != capstone.x86.X86_OP_MEM:
                continue
            if op.size != 1:
                continue
            mem = op.mem
            disp = mem.disp & 0xFFFFFFFF
            if mem.base == 0 and mem.index == 0:
                if disp != 0x81:
                    continue
                kind = "abs"
                base = "ABS"
            else:
                if disp != 0x81:
                    continue
                kind = "reg+disp"
                base = ins.reg_name(mem.base) if mem.base else "?"
                if mem.index:
                    base += "+" + (ins.reg_name(mem.index) or "?")
                    if mem.scale != 1:
                        base += "*%d" % mem.scale
            acc = op.access
            isread = bool(acc & capstone.CS_AC_READ)
            iswrite = bool(acc & capstone.CS_AC_WRITE)
            hits.append(dict(va=ins.address, text="%s %s" % (ins.mnemonic, ins.op_str),
                             kind=kind, base=base, read=isread, write=iswrite, access=acc))
            break  # one hit per insn is enough
    return hits, dict(insns=nins, skipped_bytes=nskip, text_bytes=len(data))


def q2_plus81(b, rows):
    lines = []
    hits, stats = scan_mem81(b, None)
    lines.append("Q2 · all .text instructions with byte-size [mem+0x81] operand (capstone skipdata=True)")
    lines.append("scan stats: %s" % stats)
    lines.append("total hits: %d" % len(hits))
    lines.append("")
    writes = [h for h in hits if h["write"]]
    reads = [h for h in hits if h["read"]]
    lines.append("=== WRITES (RMW included) : %d ===" % len(writes))
    for h in writes:
        a = atlas_lookup(rows, h["va"])
        fn = ("entry=%s size=%s" % (a["entry"], a["size"])) if a else "NO_ATLASFN"
        lines.append("  %08X  %-52s base=%-8s acc=%d  [%s]" %
                     (h["va"], h["text"], h["base"], h["access"], fn))
    lines.append("")
    lines.append("=== READS (RMW included) : %d ===" % len(reads))
    for h in reads:
        a = atlas_lookup(rows, h["va"])
        fn = ("entry=%s size=%s" % (a["entry"], a["size"])) if a else "NO_ATLASFN"
        lines.append("  %08X  %-52s base=%-8s acc=%d  [%s]" %
                     (h["va"], h["text"], h["base"], h["access"], fn))
    lines.append("")
    lines.append("=== ALL (incl. stack-base ebp/esp, for completeness) ===")
    for h in hits:
        lines.append("  %08X  %s" % (h["va"], h["text"]))
    dump("Q2 [+0x81] byte operands full census (channel A, no atlas boundary dependence)", lines, "Q2_plus81_census.txt")
    return hits


def q2_predicate(b):
    lines = []
    lines.append("0x5F5850 predicate (atlas size=212) full disasm, skipdata=True")
    insns = disasm_range(b, 0x5F5850, 212)
    for ins in insns:
        lines.append(fmt(ins))
    lines.append("total: %d" % len(insns))
    dump("Q2 predicate 0x5F5850", lines, "Q2_predicate_5F5850.txt")


def q3_7014a0(b):
    lines = []
    lines.append("0x7014A0 (TechnoClass slot245 +0x3D4) full disasm (atlas size=1014), skipdata=True")
    insns = disasm_range(b, 0x7014A0, 1014)
    for ins in insns:
        lines.append(fmt(ins))
    lines.append("total: %d" % len(insns))
    dump("Q3 0x7014A0 full", lines, "Q3_7014A0_full.txt")


def q1_call_sites(b):
    """Find all call [reg+0x124] sites and classify mode by the push immediately before (channel A)."""
    m = md(skipdata=True)
    t = b.sec(".text")
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    hits = []
    for ins in m.disasm(data, t["va"]):
        if ins.id == 0: continue
        if ins.mnemonic != "call": continue
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.disp == 0x124 and op.size == 4:
                hits.append(ins.address)
                break
    lines = []
    lines.append("all call [reg+0x124] (slot 73) sites: %d" % len(hits))
    for va in hits:
        lines.append("  %08X" % va)
    dump("Q1 slot73 call sites (channel A)", lines, "Q1_slot73_sites.txt")
    return hits


def main():
    b = Bin()
    rows = load_atlas()
    print("sections:", [(s["name"], hex(s["va"]), s["rawsize"]) for s in b.sections])
    print(".text rawsize=%d (0x%X)" % (b.sec(".text")["rawsize"], b.sec(".text")["rawsize"]))
    q1_mode2(b, rows)
    q1_call_sites(b)
    q2_plus81(b, rows)
    q2_predicate(b)
    q3_7014a0(b)
    print("DONE")


if __name__ == "__main__":
    main()
