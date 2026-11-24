"""Independent audit library for NAMED_PUSH_AUDIT19.
Self-written from scratch; does not reuse executor code.
"""
import struct, sys
import capstone
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGEBASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D


class Bin:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path, fast_load=False)
        self.data = open(path, "rb").read()
        self.imagebase = self.pe.OPTIONAL_HEADER.ImageBase
        assert self.imagebase == IMAGEBASE, hex(self.imagebase)
        self.secs = []
        for s in self.pe.sections:
            self.secs.append((
                s.Name.rstrip(b"\0").decode("latin1"),
                s.VirtualAddress + IMAGEBASE,
                s.VirtualAddress + IMAGEBASE + max(s.Misc_VirtualSize, s.SizeOfRawData),
                s.PointerToRawData,
                s.SizeOfRawData,
            ))
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        self.md.skipdata = True
        self.md.detail = True

    def off(self, va):
        for name, lo, hi, praw, rawsz in self.secs:
            if lo <= va < hi:
                delta = va - lo
                if delta >= rawsz:
                    return None
                return praw + delta
        return None

    def secname(self, va):
        for name, lo, hi, praw, rawsz in self.secs:
            if lo <= va < hi:
                return name
        return None

    def u8(self, va):
        o = self.off(va)
        return None if o is None else self.data[o]

    def u16(self, va):
        o = self.off(va)
        if o is None or o + 2 > len(self.data):
            return None
        return struct.unpack_from("<H", self.data, o)[0]

    def u32(self, va):
        o = self.off(va)
        if o is None or o + 4 > len(self.data):
            return None
        return struct.unpack_from("<I", self.data, o)[0]

    def i32(self, va):
        v = self.u32(va)
        return None if v is None else struct.unpack("<i", struct.pack("<I", v))[0]

    def cstr(self, va, maxlen=200):
        o = self.off(va)
        if o is None:
            return None
        end = self.data.find(b"\0", o, o + maxlen)
        if end < 0:
            return None
        return self.data[o:end].decode("latin1")

    def dis(self, va, count=1, maxbytes=None):
        o = self.off(va)
        if o is None:
            return []
        if maxbytes:
            blob = self.data[o:o + maxbytes]
        else:
            blob = self.data[o:o + 16 * count + 32]
        out = []
        for ins in self.md.disasm(blob, va):
            out.append(ins)
            if len(out) >= count:
                break
        return out

    def dis_range(self, lo, hi):
        """Disassemble [lo,hi) linearly with skipdata."""
        o = self.off(lo)
        if o is None:
            return []
        blob = self.data[o:o + (hi - lo)]
        return list(self.md.disasm(blob, lo))

    def func(self, entry, size=4096, stop_on_ret=False):
        """Linear disassembly of `size` bytes from entry."""
        o = self.off(entry)
        if o is None:
            return []
        blob = self.data[o:o + size]
        return list(self.md.disasm(blob, entry))

    def bytes_at(self, va, n):
        o = self.off(va)
        if o is None:
            return b""
        return self.data[o:o + n]

    def hexat(self, va, n):
        return self.bytes_at(va, n).hex(" ")

    # ---------- scans ----------
    def find_imm32(self, value, secfilter=None):
        """All VA locations whose 4-byte dword == value."""
        hits = []
        needle = struct.pack("<I", value)
        for name, lo, hi, praw, rawsz in self.secs:
            if secfilter and name != secfilter:
                continue
            blob = self.data[praw:praw + rawsz]
            start = 0
            while True:
                i = blob.find(needle, start)
                if i < 0:
                    break
                hits.append(lo + i)
                start = i + 1
        return hits

    def find_imm32_in_text(self, value):
        return self.find_imm32(value, secfilter=".text")

    def instr_at(self, va):
        """Instruction whose bytes start exactly at va."""
        ins = self.dis(va, 1, maxbytes=15)
        if ins and ins[0].address == va:
            return ins[0]
        return None

    def containing_instr(self, va):
        """Find the instruction that CONTAINS address va (start within 15 bytes before)."""
        for back in range(1, 16):
            ins = self.instr_at(va - back)
            if ins and ins.address + ins.size > va:
                return ins
        return None

    def imm_writers(self, value, secfilter=".text"):
        """All .text instructions that carry `value` as an immediate, resolved via the
        linear text sweep (authoritative instruction boundaries)."""
        res = []
        for va in self.find_imm32(value, secfilter=secfilter):
            ins = self.instr_containing(va)
            res.append((va, ins))
        return res

    def vt_writers(self, vt):
        """All instructions writing vtable VA `vt` as an immediate, with mnemonic + target."""
        out = []
        for va, ins in self.imm_writers(vt):
            if ins is None:
                out.append({"imm_at": va, "ins_va": None, "text": "<undecodable>", "bytes": self.hexat(va - 4, 8)})
                continue
            out.append({
                "imm_at": va,
                "ins_va": ins.address,
                "mnemonic": ins.mnemonic,
                "op_str": ins.op_str,
                "text": f"{ins.mnemonic} {ins.op_str}",
                "bytes": ins.bytes.hex(" "),
                "delta": va - ins.address,
            })
        return out

    def sweep(self):
        """One linear sweep over .text (skipdata=True). Cached.
        Returns (instr_list, by_va dict, call_map: target->[site], jmp_map)"""
        if getattr(self, "_sweep", None):
            return self._sweep
        o = self.off(TEXT_LO)
        blob = self.data[o:TEXT_LO - TEXT_LO + (TEXT_HI - TEXT_LO)]
        instrs = []
        by_va = {}
        call_map = {}
        jmp_map = {}
        for ins in self.md.disasm(blob, TEXT_LO):
            instrs.append(ins)
            by_va[ins.address] = ins
            if ins.mnemonic in ("call", "jmp") and ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
                tgt = ins.operands[0].imm & 0xFFFFFFFF
                m = call_map if ins.mnemonic == "call" else jmp_map
                m.setdefault(tgt, []).append(ins.address)
        self._sweep = (instrs, by_va, call_map, jmp_map)
        return self._sweep

    def callers_direct(self, target):
        """Direct call sites whose rel32 target == target (from the .text sweep)."""
        _, _, call_map, _ = self.sweep()
        return sorted(call_map.get(target, []))

    def jmps_to(self, target):
        _, _, _, jmp_map = self.sweep()
        return sorted(jmp_map.get(target, []))

    def push_of(self, target):
        """All `push imm32` sites whose imm == target (68 xx xx xx xx)."""
        out = []
        for va in self.find_imm32_in_text(target):
            o = self.off(va - 1)
            if o is None or o < 0:
                continue
            if self.data[o] == 0x68:
                out.append(va - 1)
        return sorted(out)

    # ---------- RTTI ----------
    def rtti_from_vt(self, vt):
        """[vt-4]=COL -> COL+0xC=pTD (absolute VA) -> pTD+8 inline decorated name."""
        col = self.u32(vt - 4)
        info = {"vt": vt, "col": col, "pchd": None, "pTD": None, "name": None, "notes": []}
        if col is None:
            info["notes"].append("vtable COL 读不到")
            return info
        if col < IMAGEBASE:
            info["notes"].append(f"COL={col:#x} < ImageBase ⇒ 非绝对 VA")
        sig = self.u32(col)
        pchd = self.u32(col + 0x10)
        ptd = self.u32(col + 0xC)
        info["sig"] = sig
        info["pchd"] = pchd
        info["pTD"] = ptd
        if ptd and ptd >= IMAGEBASE:
            nm = self.cstr(ptd + 8)
            info["name"] = nm
            info["td_u32_at_8"] = self.u32(ptd + 8)
            info["notes"].append("TD+8 first4 u32=%#x (inline string not pointer; .?AV = 0x56413F2E)" % self.u32(ptd + 8))
            if ptd + 8 < IMAGEBASE:
                info["notes"].append("TD+8 低于 ImageBase ⇒ 非内联")
        else:
            info["notes"].append(f"pTD={ptd} 不是绝对 VA（RVA 误读会越界）")
        if pchd and pchd < IMAGEBASE:
            info["notes"].append(f"pCHD={pchd:#x} < ImageBase")
        return info

    def slot_of(self, vt, entry, nslots=200):
        """Return list of slot indices where vt[slot]==entry."""
        res = []
        for i in range(nslots):
            v = self.u32(vt + 4 * i)
            if v is None:
                break
            if v == entry:
                res.append(i)
        return res

    def vt_dump(self, vt, n=20):
        out = []
        for i in range(n):
            v = self.u32(vt + 4 * i)
            if v is None:
                out.append((i, None))
                continue
            out.append((i, v))
            if v == 0:
                break
        return out

    # ---------- vtable registry ----------
    def build_col_set(self):
        """Set of plausible Complete Object Locator addresses in .rdata/.data.
        COL layout x86: +0 sig(0), +4 offset, +8 cdOffset, +0xC pTD, +0x10 pCHD.
        """
        cols = {}
        for name, lo, hi, praw, rawsz in self.secs:
            if name not in (".rdata", ".data"):
                continue
            for va in range(lo, lo + rawsz - 0x14, 4):
                if self.u32(va) != 0:
                    continue
                ptd = self.u32(va + 0xC)
                if not (0x7E1000 <= (ptd or 0) < 0xC00000):
                    continue
                s = self.cstr((ptd or 0) + 8, 120)
                if s and s.startswith(".?A"):
                    cols[va] = s
        return cols

    def build_vtables(self):
        """Structural vtable registry (cached).
        MSVC x86 layout in this image is CONTIGUOUS:  [COL ptr][slots...][COL ptr][slots...]
        so a vtable's base = (location holding the COL ptr) + 4, and it ends at the next
        such location. Returns (vts: base->col, cols: col_va->name, spans: base->next_base)
        """
        if getattr(self, "_vts", None) is not None:
            return self._vts
        cols = self.build_col_set()
        cset = set(cols)
        locs = []
        for name, lo, hi, praw, rawsz in self.secs:
            if name not in (".rdata", ".data"):
                continue
            for va in range(lo, lo + rawsz - 4, 4):
                v = self.u32(va)
                if v is not None and v in cset:
                    locs.append((va, v))
        locs.sort()
        vts = {}
        spans = {}
        for i, (va, col) in enumerate(locs):
            base = va + 4
            end = locs[i + 1][0] if i + 1 < len(locs) else None
            vts[base] = col
            spans[base] = end
        self._vts = (vts, cols, spans)
        return self._vts

    def table_slots(self, base, end, maxslots=1024):
        """Slots of a vtable bounded by `end`, stopping at first non-.text value."""
        out = []
        va = base
        while (end is None or va < end) and len(out) < maxslots:
            v = self.u32(va)
            if v is None or v == 0:
                break
            if not (TEXT_LO <= v < TEXT_HI):
                break
            out.append(v)
            va += 4
        return out

    def tables_holding(self, entry, vts=None, spans=None):
        """All (vt_base, slot_index, col, name) where vt[slot]==entry, bounded per-table."""
        if vts is None:
            vts, _, spans = self.build_vtables()
        res = []
        for vt, col in vts.items():
            slots = self.table_slots(vt, spans.get(vt))
            for i, v in enumerate(slots):
                if v == entry:
                    ptd = self.u32(col + 0xC)
                    res.append((vt, i, col, self.cstr((ptd or 0) + 8), len(slots)))
        return res

    def is_atexit_dtor(self, fn):
        """True if `fn` is registered via `push fn; call 0x7C978A` (atexit).
        From each push site, walk forward to the FIRST call within 0x60 bytes."""
        for p in self.push_of(fn):
            for ins in self.dis(p, 40):
                if ins.address - p > 0x60:
                    break
                if ins.mnemonic == "call":
                    if ins.op_str.replace("0x", "").lower() == "7c978a":
                        return True, p, [fmt_ins(x) for x in self.dis(p, 8)]
                    break
        return False, None, []

    def fn_instrs(self, fn, maxbytes=0x400):
        """Instructions of the function starting at fn, up to (and including) first ret."""
        _, by_va, _, _ = self.sweep()
        import bisect as _b
        if not hasattr(self, "_addrs"):
            self._addrs = [i.address for i in self.sweep()[0]]
        i = _b.bisect_right(self._addrs, fn) - 1
        out = []
        n = 0
        while i < len(self._addrs) and n < 4000:
            ins = by_va.get(self._addrs[i])
            if ins is None:
                break
            out.append(ins)
            if ins.mnemonic == "ret":
                break
            if ins.address - fn > maxbytes:
                break
            i += 1
            n += 1
        return out

    def is_delete_dtor(self, fn):
        """Delete-destructor signature, bounded to THIS function's extent:
        `test byte ptr [esp+X],1` + `call 0x7C8B3D` + `ret 4`."""
        ins = self.fn_instrs(fn)
        has_test = False
        test_at = None
        call_free = None
        for x in ins:
            if x.mnemonic == "test" and "byte ptr [esp" in x.op_str and x.op_str.rstrip().endswith(", 1"):
                has_test = True
                test_at = x.address
            if x.mnemonic == "call" and x.op_str.replace("0x", "").lower() in ("7c8b3d", "7c8b3c"):
                call_free = x.address
        has_ret4 = any(y.mnemonic == "ret" and y.op_str.strip() == "4" for y in ins)
        return (has_test and call_free is not None and has_ret4), {
            "test_byte_esp_1_at": test_at, "call_free_at": call_free, "ret_4": has_ret4,
            "n_instr": len(ins), "end": hex(ins[-1].address) if ins else None,
        }

    def instr_containing(self, va):
        """Instruction (from the sweep) whose extent covers va."""
        instrs, by_va, _, _ = self.sweep()
        import bisect as _b
        if not hasattr(self, "_addrs"):
            self._addrs = [i.address for i in instrs]
        i = _b.bisect_right(self._addrs, va) - 1
        if i < 0:
            return None
        ins = instrs[i]
        if ins.address <= va < ins.address + ins.size:
            return ins
        return None

    def func_start_of(self, va):
        """Independent function-start resolution: walk back to previous ret/jmp and skip padding."""
        instrs, by_va, _, _ = self.sweep()
        import bisect as _b
        if not hasattr(self, "_addrs"):
            self._addrs = [i.address for i in instrs]
        i = _b.bisect_right(self._addrs, va) - 1
        if i < 0:
            return None
        # walk back to a terminator
        k = i
        while k >= 0:
            m = instrs[k].mnemonic
            if m in ("ret", "jmp") or (m == "int3") or (m == "hlt"):
                break
            k -= 1
        # now step forward past padding
        j = k + 1
        while j < len(instrs):
            m = instrs[j].mnemonic
            if m in ("nop", "int3", "hlt"):
                j += 1
                continue
            break
        if j >= len(instrs):
            return None
        return instrs[j].address

    def func_extent_of(self, va):
        """Return (start_va, end_va) using func_start_of on va and on the next function."""
        st = self.func_start_of(va)
        if st is None:
            return None
        instrs, by_va, _, _ = self.sweep()
        import bisect as _b
        if not hasattr(self, "_addrs"):
            self._addrs = [i.address for i in instrs]
        i = _b.bisect_right(self._addrs, st) - 1
        # find this function's terminator
        while i < len(instrs):
            if instrs[i].mnemonic == "ret":
                return (st, instrs[i].address + instrs[i].size)
            i += 1
        return (st, None)


def fmt_ins(ins):
    if ins is None:
        return "<none>"
    return f"{ins.address:08X}  {ins.bytes.hex(' '):<24} {ins.mnemonic} {ins.op_str}"


if __name__ == "__main__":
    b = Bin()
    print("sections:")
    for s in b.secs:
        print(f"  {s[0]:8s} {s[1]:08X}-{s[2]:08X} raw@{s[3]:08X} sz={s[4]:X}")
