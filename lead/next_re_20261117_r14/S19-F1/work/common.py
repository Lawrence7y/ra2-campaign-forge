"""S19-F1 reusable RE helper (read-only target).
Self-contained: derives all paths from __file__, uses pefile + capstone(skipdata=True).
Never writes outside the S19-F1 card directory.
"""
import os, sys, json, struct, bisect
import pefile, capstone

HERE = os.path.dirname(os.path.abspath(__file__))
CARD = os.path.dirname(HERE)                 # .../S19-F1
R14 = os.path.dirname(CARD)                  # .../next_re_20261117_r14
LEAD = os.path.dirname(R14)                  # .../lead
ROOT = os.path.dirname(LEAD)                 # project root
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(LEAD, "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
CACHE = os.path.join(HERE, "_cache.json")


class Bin:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path, fast_load=False)
        self.image_base = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = []
        for s in self.pe.sections:
            name = s.Name.decode(errors="replace").rstrip("\x00")
            self.sections.append(dict(
                name=name,
                va=self.image_base + s.VirtualAddress,
                rva=s.VirtualAddress,
                vsize=s.Misc_VirtualSize,
                raw=s.PointerToRawData,
                rawsize=s.SizeOfRawData,
                chars=s.Characteristics,
            ))
        self.by_name = {s["name"]: s for s in self.sections}

    def sec_of_va(self, va):
        for s in self.sections:
            if s["va"] <= va < s["va"] + max(s["rawsize"], s["vsize"]):
                return s
        return None

    def off(self, va):
        s = self.sec_of_va(va)
        if s is None:
            raise ValueError("VA %08X not in any section" % va)
        return s["raw"] + (va - s["va"])

    def read(self, va, n):
        s = self.sec_of_va(va)
        if s is None or va + n > s["va"] + s["rawsize"]:
            raise ValueError("VA %08X+%d outside raw range" % (va, n))
        o = s["raw"] + (va - s["va"])
        return self.pe.__data__[o:o + n]

    def u8(self, va):  return self.read(va, 1)[0]
    def u16(self, va): return struct.unpack("<H", self.read(va, 2))[0]
    def u32(self, va): return struct.unpack("<I", self.read(va, 4))[0]
    def i32(self, va): return struct.unpack("<i", self.read(va, 4))[0]

    def text(self):
        return self.by_name[".text"]

    def imports(self):
        """Yield (dll, name, iat_va)."""
        for e in getattr(self.pe, "DIRECTORY_ENTRY_IMPORT", []):
            dll = e.dll.decode(errors="replace")
            for imp in e.imports:
                nm = imp.name.decode(errors="replace") if imp.name else ("#%d" % imp.ordinal)
                # pefile imp.address is already a VA (ImageBase + FirstThunk RVA)
                yield dll, nm, imp.address


def md32(skipdata=True, detail=True):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = detail
    m.skipdata = skipdata
    return m


def disasm(bin_, start, max_bytes=None, stop_at=None, skipdata=True):
    """Linear disasm from VA start. Yields real instructions (id != 0)."""
    if max_bytes is None:
        s = bin_.sec_of_va(start)
        max_bytes = (s["va"] + s["rawsize"]) - start
    data = bin_.read(start, max_bytes)
    m = md32(skipdata=skipdata)
    for insn in m.disasm(data, start):
        if insn.id == 0:
            continue
        if stop_at is not None and insn.address >= stop_at:
            break
        yield insn


def one(bin_, va):
    """Decode exactly one instruction at VA (skipdata)."""
    for insn in disasm(bin_, va, 16):
        return insn
    return None


def fmt(insn):
    return "%08X  %-24s %s %s" % (insn.address, insn.bytes.hex(), insn.mnemonic, insn.op_str)


def dump(bin_, start, max_bytes, path, stop_at=None):
    lines = []
    for insn in disasm(bin_, start, max_bytes, stop_at=stop_at):
        lines.append(fmt(insn))
    with open(path, "w", encoding="utf-8") as f:
        f.write("; start=%08X max_bytes=%X stop_at=%s\n" % (start, max_bytes, stop_at))
        f.write("\n".join(lines) + "\n")
    return lines


class Atlas:
    def __init__(self, path=ATLAS):
        self.rows = []
        self.hdr = []
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            self.hdr = f.readline().rstrip("\n").split("\t")
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) < 2 or not p[0]:
                    continue
                try:
                    ent = int(p[0], 16)
                except ValueError:
                    continue
                rec = dict(zip(self.hdr, p))
                try:
                    rec["_size"] = int(p[1], 10)
                except ValueError:
                    rec["_size"] = 0
                self.rows.append((ent, rec))
        self.rows.sort(key=lambda t: t[0])
        self.entries = [r[0] for r in self.rows]

    def containing(self, va):
        """Interval containment: entry <= va < entry+size. NOT entry_at_or_before."""
        i = bisect.bisect_right(self.entries, va) - 1
        while i >= 0:
            ent, rec = self.rows[i]
            if ent + rec["_size"] > va:
                return ent, rec
            i -= 1
        return None, None

    def get(self, va):
        i = bisect.bisect_left(self.entries, va)
        if i < len(self.rows) and self.rows[i][0] == va:
            return self.rows[i][1]
        return None

    def nearest_before(self, va):
        i = bisect.bisect_right(self.entries, va) - 1
        return self.rows[i] if i >= 0 else (None, None)


def sweep_calls(bin_, use_cache=True):
    """Full .text linear sweep, skipdata=True -> (calls, jmps, stats).
    calls: target_va -> sorted list of call-site VAs (direct rel32/rel8 only).
    Independent of function_atlas entry+size.
    """
    cache = None
    if use_cache and os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE, "r", encoding="utf-8"))
        except Exception:
            cache = None
    if cache and "sweep" in cache:
        c = cache["sweep"]
        return ({int(k, 16): v for k, v in c["calls"].items()},
                {int(k, 16): v for k, v in c["jmps"].items()}, c["stats"])
    t = bin_.text()
    data = bin_.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    m = md32(skipdata=True)
    calls, jmps = {}, {}
    nins = nskip = 0
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0:
            nskip += insn.size
            continue
        nins += 1
        op = insn.op_str
        if insn.mnemonic == "call" and op.startswith("0x"):
            tgt = int(op, 16)
            calls.setdefault(tgt, []).append(insn.address)
        elif insn.mnemonic == "jmp" and op.startswith("0x"):
            tgt = int(op, 16)
            jmps.setdefault(tgt, []).append(insn.address)
    stats = dict(insns=nins, skipped_bytes=nskip, text_bytes=len(data))
    if cache is None:
        cache = {}
    cache["sweep"] = dict(calls={("%08X" % k): v for k, v in calls.items()},
                          jmps={("%08X" % k): v for k, v in jmps.items()}, stats=stats)
    json.dump(cache, open(CACHE, "w", encoding="utf-8"))
    return calls, jmps, stats


def abs_xrefs(bin_, target_va, use_cache=False):
    """Find instructions with an absolute memory operand == target_va.
    Not cached by default (target-specific)."""
    t = bin_.text()
    data = bin_.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    m = md32(skipdata=True)
    out = []
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0:
            continue
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM:
                mem = op.mem
                if mem.base == 0 and mem.index == 0 and (mem.disp & 0xFFFFFFFF) == target_va:
                    out.append(dict(va=insn.address, insn="%s %s" % (insn.mnemonic, insn.op_str)))
                    break
    return out


def sweep_abs(bin_, use_cache=True):
    """One pass over .text: target_va -> list of {site, insn} for absolute
    memory operands. Cached. Used for finding string/global xrefs."""
    cache = None
    if use_cache and os.path.exists(CACHE):
        try: cache = json.load(open(CACHE, "r", encoding="utf-8"))
        except Exception: cache = None
    if cache and "abs" in cache:
        return {int(k, 16): v for k, v in cache["abs"].items()}
    t = bin_.text()
    data = bin_.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    m = md32(skipdata=True)
    out = {}
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0: continue
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM:
                mem = op.mem
                if mem.base == 0 and mem.index == 0:
                    va = mem.disp & 0xFFFFFFFF
                    out.setdefault(va, []).append(dict(
                        site="%08X" % insn.address,
                        insn="%s %s" % (insn.mnemonic, insn.op_str)))
                    break
    if cache is None: cache = {}
    cache["abs"] = {("%08X" % k): v for k, v in out.items()}
    json.dump(cache, open(CACHE, "w", encoding="utf-8"))
    return out


def sweep_imm(bin_, use_cache=True):
    """One pass over .text: imm_value -> list of {site, insn} for immediate operands.
    Cached. Needed because MSVC string refs are `push <imm32>` / `mov reg,<imm32>`."""
    cache = None
    if use_cache and os.path.exists(CACHE):
        try: cache = json.load(open(CACHE, "r", encoding="utf-8"))
        except Exception: cache = None
    if cache and "imm" in cache:
        return {int(k, 16): v for k, v in cache["imm"].items()}
    t = bin_.text()
    data = bin_.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    m = md32(skipdata=True)
    out = {}
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0: continue
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_IMM:
                v = op.imm & 0xFFFFFFFF
                out.setdefault(v, []).append(dict(
                    site="%08X" % insn.address,
                    insn="%s %s" % (insn.mnemonic, insn.op_str)))
    if cache is None: cache = {}
    cache["imm"] = {("%08X" % k): v for k, v in out.items()}
    json.dump(cache, open(CACHE, "w", encoding="utf-8"))
    return out


def find_strings(bin_, needles, section=".rdata"):
    """Find ASCII substrings; yield (va, text). needles = list of bytes/str."""
    s = bin_.by_name[section]
    data = bin_.pe.__data__[s["raw"]:s["raw"] + s["rawsize"]]
    out = []
    for needle in needles:
        nb = needle.encode() if isinstance(needle, str) else needle
        start = 0
        while True:
            i = data.find(nb, start)
            if i < 0: break
            # extract null-terminated string around hit
            j = i
            while j > 0 and 32 <= data[j-1] < 127: j -= 1
            k = i
            while k < len(data) and 32 <= data[k] < 127: k += 1
            out.append((s["va"] + i, data[j:k].decode(errors="replace")))
            start = i + 1
    return out


if __name__ == "__main__":
    b = Bin()
    print("ImageBase %08X" % b.image_base)
    for s in b.sections:
        print("  %-8s va=%08X vsize=%08X raw=%08X rawsize=%08X"
              % (s["name"], s["va"], s["vsize"], s["raw"], s["rawsize"]))
    print("--- dsound.dll imports ---")
    for dll, nm, iat in b.imports():
        if "sound" in dll.lower() or "dsound" in nm.lower():
            print("  %-12s %-28s IAT=%08X" % (dll, nm, iat))
