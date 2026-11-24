"""S09-F1 analysis library — independent capstone/pefile toolkit.
纪律: capstone skipdata=True; boundary_check 超限返回 'unknown' 而非 False;
站点归属用函数区间包含.
"""
import struct, bisect, os, json
import pefile
import capstone
from capstone import x86

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
IMAGE_BASE = 0x400000

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
        self.text = self.sec(".text"); self.rdata = self.sec(".rdata")
    def sec(self, name):
        for s in self.sections:
            if s["name"] == name: return s
        raise KeyError(name)
    def sec_for_va(self, va):
        for s in self.sections:
            if s["va"] <= va < s["va"] + max(s["rawsize"], s["vsize"]): return s
        return None
    def read(self, va, n):
        for s in self.sections:
            if s["va"] <= va and va + n <= s["va"] + s["rawsize"]:
                off = s["raw"] + (va - s["va"])
                return self.pe.__data__[off:off + n]
        raise ValueError("VA %08X+%d not in raw range" % (va, n))
    def u8(self, va): return self.read(va, 1)[0]
    def u16(self, va): return struct.unpack("<H", self.read(va, 2))[0]
    def u32(self, va): return struct.unpack("<I", self.read(va, 4))[0]
    def i32(self, va): return struct.unpack("<i", self.read(va, 4))[0]
    def f32(self, va): return struct.unpack("<f", self.read(va, 4))[0]

def md(skipdata=True, detail=True):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = detail; m.skipdata = skipdata; return m

def disasm(bin_, start_va, nbytes, stop_at=None, skipdata=True):
    data = bin_.read(start_va, nbytes); out = []
    for insn in md(skipdata=skipdata).disasm(data, start_va):
        out.append(insn)
        if stop_at is not None and insn.address >= stop_at: break
    return out

def fmt_insn(insn):
    return "%08X  %-24s %-8s %s" % (insn.address, insn.bytes.hex(), insn.mnemonic, insn.op_str)

def dump(bin_, start, nbytes=256, skipdata=True):
    return "\n".join(fmt_insn(i) for i in disasm(bin_, start, nbytes, skipdata=skipdata))

def load_atlas(path=ATLAS):
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            p = line.rstrip("\n").split("\t")
            if not p or not p[0]: continue
            rec = dict(zip(header, p))
            try:
                va = int(p[0], 16); size = int(rec.get("size", "0"))
            except Exception: continue
            rows.append((va, size, rec))
    rows.sort(); return rows

class Atlas:
    def __init__(self, path=ATLAS):
        rows = load_atlas(path); self.starts = [r[0] for r in rows]; self.rows = rows
        self.by_entry = {r[0]: r for r in rows}
    def contains(self, va):
        i = bisect.bisect_right(self.starts, va) - 1
        if i < 0: return None
        entry, size, rec = self.rows[i]
        return (entry, size, rec) if entry <= va < entry + size else None
    def entry_before(self, va):
        i = bisect.bisect_right(self.starts, va) - 1
        return self.rows[i] if i >= 0 else None

def boundary_check(bin_, entry_va, target_va, max_bytes=0x20000):
    if target_va < entry_va: return (False, None, "target<entry")
    span = target_va - entry_va
    if span >= max_bytes: return ('unknown', None, "span>=max_bytes (NOT判定)")
    data = bin_.read(entry_va, span + 32); m = md(skipdata=True)
    for insn in m.disasm(data, entry_va):
        if insn.id == 0: continue
        if insn.address == target_va: return (True, insn, "ok")
        if insn.address > target_va: break
    for insn in m.disasm(data, entry_va):
        if insn.id == 0: continue
        if insn.address < target_va < insn.address + insn.size:
            return (False, insn, "inside %s %s" % (insn.mnemonic, insn.op_str))
        if insn.address > target_va: break
    return ('unknown', None, "linear disasm did not reach target")

def sweep_calls(bin_):
    t = bin_.text; data = bin_.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    calls, jmps = {}, {}; nins = 0
    for insn in md(skipdata=True).disasm(data, t["va"]):
        if insn.id == 0: continue
        nins += 1
        if insn.mnemonic in ("call", "jmp") and insn.operands:
            op = insn.operands[0]
            if op.type == x86.X86_OP_IMM:
                d = calls if insn.mnemonic == "call" else jmps
                d.setdefault(op.imm & 0xFFFFFFFF, []).append(insn.address)
    return calls, jmps, nins

def sweep_disps(bin_, target_va):
    t = bin_.text; data = bin_.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    found = []
    for insn in md(skipdata=True).disasm(data, t["va"]):
        if insn.id == 0: continue
        for op in insn.operands:
            if op.type == x86.X86_OP_MEM:
                m = op.mem
                if m.base == 0 and m.index == 0 and (m.disp & 0xFFFFFFFF) == target_va:
                    found.append(dict(va=insn.address, insn="%s %s" % (insn.mnemonic, insn.op_str), kind="abs"))
                elif m.base != 0 and (m.disp & 0xFFFFFFFF) == target_va:
                    found.append(dict(va=insn.address, insn="%s %s" % (insn.mnemonic, insn.op_str), kind="reg+disp"))
    return found

def sweep_imm(bin_, value):
    t = bin_.text; data = bin_.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    found = []
    for insn in md(skipdata=True).disasm(data, t["va"]):
        if insn.id == 0: continue
        for op in insn.operands:
            if op.type == x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) == value:
                found.append(dict(va=insn.address, insn="%s %s" % (insn.mnemonic, insn.op_str))); break
    return found

def dump_vtable(bin_, vt_va, n=20):
    return "\n".join("v[%d] @%08X = %08X" % (i, vt_va + i * 4, bin_.u32(vt_va + i * 4)) for i in range(n))

def find_rtti_name(bin_, clsname):
    s = bin_.rdata; buf = bin_.pe.__data__[s["raw"]:s["raw"] + s["rawsize"]]
    pat = b".?AV" + clsname.encode() + b"@@"; hits = []; start = 0
    while True:
        i = buf.find(pat, start)
        if i < 0: break
        hits.append(s["va"] + i); start = i + 1
    return hits

def dump_td(bin_, td_va):
    pvf = bin_.u32(td_va); spare = bin_.u32(td_va + 4); name_va = td_va + 8
    name = bin_.read(name_va, 64).split(b"\x00")[0].decode(errors="replace")
    return "TD=%08X pVF=%08X spare=%08X name='%s' (@%08X)" % (td_va, pvf, spare, name, name_va)

def iat_lookup(bin_, names):
    pe = bin_.pe; pe.parse_data_directories(); res = {}
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in entry.imports:
            n = imp.name.decode(errors="replace") if imp.name else ("#%d" % imp.ordinal)
            if n in names: res[n] = imp.address
    return res

if __name__ == "__main__":
    b = Bin()
    print("ImageBase", hex(b.image_base))
    for s in b.sections:
        print("  %-8s va=%08X vsize=%08X raw=%08X rawsize=%08X" % (s["name"], s["va"], s["vsize"], s["raw"], s["rawsize"]))
