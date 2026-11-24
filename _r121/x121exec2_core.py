#!/usr/bin/env python3
"""R121 exec2 self-contained PE/x86 helpers.

No repo library is imported. Everything here is written from scratch:
  * PE headers / section table / ImageBase
  * import descriptors (OFT / FT) -> IAT slot VA -> (dll, name|ordinal)
  * streaming instruction sweep (disasm_lite, no detail, generator based)
  * forward decode from a function start (0xCC padding criterion) to a site
"""
import bisect
import struct
import sys

import capstone
import pefile

PATH = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
QI_ARG_VA = 0x7F7C80          # control / primary immediate
CTRL_ARG_VA = 0x7F7C81        # 3a immediate control
ALT_ARG_VA = 0x7F7C90         # 3d paired constant

M32 = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
M32.detail = False

REGNAME = {}
for _r in (capstone.x86.X86_REG_EAX, capstone.x86.X86_REG_ECX,
           capstone.x86.X86_REG_EDX, capstone.x86.X86_REG_EBX,
           capstone.x86.X86_REG_ESP, capstone.x86.X86_REG_EBP,
           capstone.x86.X86_REG_ESI, capstone.x86.X86_REG_EDI):
    REGNAME[_r] = M32.reg_name(_r)


class Bin:
    def __init__(self, path=PATH):
        self.path = path
        with open(path, "rb") as fh:
            self.buf = fh.read()
        self.pe = pefile.PE(data=self.buf, fast_load=False)
        self.image_base = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = []
        for s in self.pe.sections:
            self.sections.append({
                "name": s.Name.rstrip(b"\x00").decode("latin1"),
                "va": s.VirtualAddress,
                "vsize": s.Misc_VirtualSize,
                "raw": s.PointerToRawData,
                "rawsize": s.SizeOfRawData,
                "chars": s.Characteristics,
            })
        self.text = self._find(".text")
        self.rdata = self._find(".rdata")
        self.iat = self._build_iat()

    def _find(self, name):
        for s in self.sections:
            if s["name"] == name:
                return s
        raise KeyError(name)

    # ---- VA <-> file offset -------------------------------------------
    def off(self, va):
        rva = va - self.image_base
        for s in self.sections:
            hi = s["va"] + max(s["vsize"], s["rawsize"])
            if s["va"] <= rva < hi:
                return s["raw"] + (rva - s["va"])
        raise ValueError("unmapped va 0x%x" % va)

    def sec_of(self, va):
        rva = va - self.image_base
        for s in self.sections:
            hi = s["va"] + max(s["vsize"], s["rawsize"])
            if s["va"] <= rva < hi:
                return s
        return None

    def text_bytes(self):
        s = self.text
        return self.buf[s["raw"]:s["raw"] + s["vsize"]]

    def text_va(self):
        return self.image_base + self.text["va"]

    # ---- imports -------------------------------------------------------
    def _build_iat(self):
        """Manual import walk: IMAGE_IMPORT_DESCRIPTOR -> OFT/FT -> IAT VA.

        pefile is used only for headers; the IAT map is built here so the
        slot VA semantics (FT VirtualAddress + ImageBase) are explicit.
        """
        iat = {}
        pe = self.pe
        ddir = pe.OPTIONAL_HEADER.DATA_DIRECTORY[1]
        if ddir.VirtualAddress == 0:
            return iat
        base_off = self.off(self.image_base + ddir.VirtualAddress)
        self.import_descriptors = []
        for i in range(256):
            o = base_off + 20 * i
            oft, tds, fwd, namerva, ftrva = struct.unpack("<5I", self.buf[o:o + 20])
            if not (oft or tds or fwd or namerva or ftrva):
                break
            no = self.off(self.image_base + namerva)
            end = self.buf.index(b"\x00", no)
            dname = self.buf[no:end].decode("latin1")
            self.import_descriptors.append({
                "dll": dname, "oft_rva": oft, "ft_rva": ftrva,
                "name_rva": namerva,
            })
            thunk_rva = oft or ftrva
            ftrva_eff = ftrva
            j = 0
            while True:
                to = self.off(self.image_base + thunk_rva + 4 * j)
                val = struct.unpack("<I", self.buf[to:to + 4])[0]
                if val == 0:
                    break
                slot_va = self.image_base + ftrva_eff + 4 * j
                if val & 0x80000000:
                    ordinal = val & 0xFFFF
                    fname = "ord_%d" % ordinal
                else:
                    ordinal = None
                    hno = self.off(self.image_base + val)
                    # name entry: 2 byte hint then ASCII name
                    e = self.buf.index(b"\x00", hno + 2)
                    fname = self.buf[hno + 2:e].decode("latin1")
                iat[slot_va] = {"dll": dname, "func": fname, "ordinal": ordinal}
                j += 1
                if j > 4096:
                    break
        return iat

    def iat_lookup(self, va):
        return self.iat.get(va)

    # ---- streaming linear sweep ---------------------------------------
    def sweep_starts(self):
        """Return sorted array of instruction start VAs (disasm_lite, streamed).

        Only integer addresses are retained; instruction objects are dropped
        per iteration so RSS stays flat.
        """
        from array import array
        base = self.text_va()
        starts = array("I")
        gen = M32.disasm_lite(self.text_bytes(), base)
        for addr, size, _mn, _op in gen:
            starts.append(addr)
        return starts


def nearest_run_end_before(binobj, site_va, min_run=1, floor_va=None):
    """Function-start criterion: end of the nearest preceding run of 0xCC.

    Scans backwards from site_va-1. Returns (fstart_va, run_len, run_hi_va)
    where fstart = run_hi + 1, or None if no run of min_run 0xCC found.
    """
    floor = binobj.text_va() if floor_va is None else floor_va
    va = site_va - 1
    while va >= floor:
        if binobj.buf[binobj.off(va)] == 0xCC:
            hi = va
            n = 0
            while va >= floor and binobj.buf[binobj.off(va)] == 0xCC:
                n += 1
                va -= 1
            if n >= min_run:
                return (hi + 1, n, hi)
            # run too short: keep looking further back
            continue
        va -= 1
    return None


def decode_block(binobj, start_va, end_va, max_insn=4000):
    """Linear decode [start_va, end_va] inclusive. Returns list of dicts.

    Used only on small spans (function-head .. site), never whole .text.
    """
    if start_va > end_va:
        return []
    size = end_va - start_va + 16
    off = binobj.off(start_va)
    data = binobj.buf[off:off + size]
    out = []
    for insn in M32.disasm(data, start_va, count=max_insn):
        out.append({
            "va": insn.address,
            "bytes": insn.bytes.hex(),
            "mn": insn.mnemonic,
            "op": insn.op_str,
            "size": insn.size,
        })
        if insn.address + insn.size > end_va + 1:
            break
    return out


def decode_one(binobj, va, detail=True):
    md = M32
    old = md.detail
    md.detail = detail
    try:
        off = binobj.off(va)
        data = binobj.buf[off:off + 16]
        for insn in md.disasm(data, va, count=1):
            return insn
    finally:
        md.detail = old
    return None


def flatten(insn):
    """Plain-dict copy of a capstone insn taken while detail=True.

    Capstone 5 exposes operands lazily through the Cs instance, so anything
    kept beyond the detail window must be flattened first.
    """
    rec = {
        "va": insn.address,
        "size": insn.size,
        "bytes": insn.bytes.hex(),
        "mn": insn.mnemonic,
        "op": insn.op_str,
        "ops": [],
    }
    for op in insn.operands:
        d = {"type": op.type, "size": op.size}
        if op.type == capstone.x86.X86_OP_IMM:
            d["imm"] = op.imm
        elif op.type == capstone.x86.X86_OP_REG:
            d["reg"] = op.reg
            d["regname"] = M32.reg_name(op.reg)
        elif op.type == capstone.x86.X86_OP_MEM:
            d["base"] = op.mem.base
            d["base_name"] = M32.reg_name(op.mem.base) if op.mem.base else None
            d["index"] = op.mem.index
            d["index_name"] = M32.reg_name(op.mem.index) if op.mem.index else None
            d["scale"] = op.mem.scale
            d["disp"] = op.mem.disp
        rec["ops"].append(d)
    return rec


def decode_flat(binobj, va, nbytes, limit=2000):
    """Decode nbytes from va (must be an instruction boundary). Flattened."""
    old = M32.detail
    M32.detail = True
    out = []
    try:
        off = binobj.off(va)
        data = binobj.buf[off:off + nbytes]
        for insn in M32.disasm(data, va, count=limit):
            out.append(flatten(insn))
    finally:
        M32.detail = old
    return out


def is_call(rec):
    return rec["mn"] in ("call", "lcall")


def m_is_abs(op):
    """True iff a MEM operand has neither base nor index (absolute disp32).

    Capstone encodes 'no base' as register id 0 (== X86_REG_INVALID), not
    None, for memory operands, so both must be treated as absent.
    """
    return not op.get("base") and not op.get("index")


def m_base(op):
    return op.get("base") or None


def m_index(op):
    return op.get("index") or None


JCC_PREFIX = ("j",)


def parse_rel_target(op_str):
    """Direct-branch target from capstone op_str, or None."""
    s = op_str.strip()
    if len(s) > 2 and s.startswith("0x"):
        try:
            return int(s, 16)
        except ValueError:
            return None
    return None


def sweep_code(binobj, chunk=0x10000):
    """Resyncing linear sweep over .text with disasm_lite (fast, low RSS).

    A resync advances exactly one byte past the last successfully decoded
    instruction end, which is where capstone gave up.
    Returns (starts array, branch list, bad_offset_count).
    """
    from array import array
    base = binobj.text_va()
    end = base + binobj.text["vsize"]
    starts = array("I")
    branches = []
    bad = 0
    va = base
    while va < end:
        hi = min(va + chunk, end)
        n = (hi - va) + 16
        data = binobj.buf[binobj.off(va):binobj.off(va) + n]
        last_end = va
        stopped_at_chunk = False
        for addr, size, mn, op in M32.disasm_lite(data, va):
            if addr >= hi:
                stopped_at_chunk = True
                break
            starts.append(addr)
            last_end = addr + size
            if mn.startswith(("call", "jmp", "j")) and not mn.startswith("jmp"):
                tgt = parse_rel_target(op)
                if tgt is not None:
                    kind = "call" if mn.startswith("call") else "jmp_or_jcc"
                    branches.append((addr, kind, tgt))
            elif mn.startswith("jmp"):
                tgt = parse_rel_target(op)
                if tgt is not None:
                    branches.append((addr, "jmp", tgt))
        if stopped_at_chunk:
            va = last_end
        elif last_end < hi:
            bad += 1
            va = last_end + 1
        else:
            va = last_end
        if va >= end:
            break
    return starts, branches, bad


def nearest_cc_run(binobj, site_va, floor=None):
    """Nearest preceding run of 0xCC; returns (start_after_run, run_len)."""
    floor = binobj.text_va() if floor is None else floor
    va = site_va - 1
    while va >= floor:
        if binobj.buf[binobj.off(va)] == 0xCC:
            hi = va
            n = 0
            while va >= floor and binobj.buf[binobj.off(va)] == 0xCC:
                n += 1
                va -= 1
            return (hi + 1, n)
        va -= 1
    return None


TERMINATORS = ("ret", "retn", "retf", "hlt", "iret", "iretd", "int3", "ud2",
               "jmp", "ljmp")


def validate_block_start(binobj, start_va, site_va, max_insn=6000):
    """Can a linear decode from start_va reach site_va exactly on a boundary?

    Rejects blocks that contain an instruction terminator (ret / unconditional
    jmp / hlt) before the site, because such a block cannot fall through into
    the site linearly.
    """
    n = site_va - start_va
    if n <= 0 or n > 0x8000:
        return {"ok": False, "reason": "span"}
    recs = decode_flat(binobj, start_va, n + 16, limit=max_insn)
    for r in recs:
        if r["va"] == site_va:
            return {"ok": True, "insn_count": len(recs[:recs.index(r) + 1]),
                    "reason": None}
        if r["va"] > site_va:
            return {"ok": False, "reason": "overrun at 0x%x" % r["va"]}
        if r["mn"] in TERMINATORS:
            return {"ok": False,
                    "reason": "terminator %s %s at 0x%x" %
                              (r["mn"], r["op"], r["va"])}
        if r["mn"] in ("(bad)", "invalid"):
            return {"ok": False, "reason": "bad insn at 0x%x" % r["va"]}
    return {"ok": False, "reason": "not reached"}


def find_function_start(binobj, site_va, back=0x4000):
    """Nearest cc-run end whose linear block reaches the site.

    Returns dict with the literal 'nearest cc run' answer and the validated
    one, so the report can show where the naive criterion drifts.
    """
    literal = nearest_cc_run(binobj, site_va)
    floor = max(binobj.text_va(), site_va - back)
    cands = []
    va = site_va - 1
    while va >= floor:
        if binobj.buf[binobj.off(va)] == 0xCC:
            hi = va
            while va >= floor and binobj.buf[binobj.off(va)] == 0xCC:
                va -= 1
            cands.append(hi + 1)
        else:
            va -= 1
    for c in cands:
        v = validate_block_start(binobj, c, site_va)
        if v["ok"]:
            return {"literal_cc_run_end": literal[0] if literal else None,
                    "literal_run_len": literal[1] if literal else None,
                    "validated_start": c,
                    "validated_insn_count": v["insn_count"],
                    "candidates_rejected": cands[:cands.index(c)]}
    return {"literal_cc_run_end": literal[0] if literal else None,
            "literal_run_len": literal[1] if literal else None,
            "validated_start": None,
            "validated_insn_count": None,
            "candidates_rejected": cands}


REG32 = {
    "eax": capstone.x86.X86_REG_EAX, "ecx": capstone.x86.X86_REG_ECX,
    "edx": capstone.x86.X86_REG_EDX, "ebx": capstone.x86.X86_REG_EBX,
    "esp": capstone.x86.X86_REG_ESP, "ebp": capstone.x86.X86_REG_EBP,
    "esi": capstone.x86.X86_REG_ESI, "edi": capstone.x86.X86_REG_EDI,
}
REG_NAME32 = {v: k for k, v in REG32.items()}


def writes_to(rec, reg):
    """Does this instruction write the full 32-bit reg?"""
    ops = rec["ops"]
    if not ops:
        return False
    d = ops[0]
    if d["type"] != capstone.x86.X86_OP_REG or d.get("reg") != reg:
        return False
    mn = rec["mn"]
    if mn in ("cmp", "test", "call", "jmp", "push", "nop"):
        return False
    if mn.startswith("j") or mn.startswith("set"):
        return False
    return True


def operand_reads(rec, reg):
    for d in rec["ops"]:
        if d["type"] == capstone.x86.X86_OP_REG and d.get("reg") == reg:
            return True
        if d["type"] == capstone.x86.X86_OP_MEM and (
                d.get("base") == reg or d.get("index") == reg):
            return True
    return False


def find_start_after_terminator(binobj, site_va, back=0x8000):
    """Alternative boundary criterion: nearest preceding ret/ret-n/hlt end.

    Returns (candidate_start, validated, rejected_list). A candidate is
    accepted when a linear decode from it reaches the site exactly on an
    instruction boundary.
    """
    floor = max(binobj.text_va(), site_va - back)
    recs = decode_flat(binobj, floor, (site_va - floor) + 16, limit=20000)
    cands = []
    for i, r in enumerate(recs):
        if r["va"] >= site_va:
            break
        if r["mn"] in ("ret", "retn", "retf", "hlt", "iret", "iretd", "ud2"):
            cands.append(r["va"] + r["size"])
    rejected = []
    for c in reversed(cands):
        v = validate_block_start(binobj, c, site_va)
        if v["ok"]:
            return c, v, rejected
        rejected.append({"start": c, "why": v["reason"]})
    return None, None, rejected


def trace_reg_writes(binobj, fstart, site_va, reg):
    """All full 32-bit writes to reg in [fstart, site_va), in order."""
    if fstart is None:
        return []
    recs = decode_flat(binobj, fstart, site_va - fstart, limit=8000)
    out = []
    for r in recs:
        if r["va"] >= site_va:
            break
        if writes_to(r, reg):
            out.append({"va": r["va"], "text": "%s %s" % (r["mn"], r["op"]),
                        "bytes": r["bytes"]})
    return out


def branch_targets_into(branches, lo, hi):
    """Direct call/jmp rel32 targets t with lo < t < hi (open interval)."""
    hits = []
    for va, kind, tgt in branches:
        if lo < tgt < hi:
            hits.append({"from": va, "kind": kind, "target": tgt})
    return hits


def insn_desc(insn):
    return {"va": insn.address, "bytes": insn.bytes.hex(),
            "mn": insn.mnemonic, "op": insn.op_str}


def find_insn_sites(binobj, imm_va, min_offset=0, limit=None):
    """All offsets in .text where byte 0x68 is followed by imm32 == imm_va."""
    tb = binobj.text_bytes()
    base = binobj.text_va()
    pat = b"\x68" + struct.pack("<I", imm_va)
    out = []
    i = tb.find(pat, min_offset)
    while i >= 0:
        out.append(base + i)
        if limit is not None and len(out) >= limit:
            break
        i = tb.find(pat, i + 1)
    return out


def disasm_forward_span(binobj, va, nbytes, want_detail=True):
    """Decode instructions covering [va, va+nbytes). Returns list (capped)."""
    old = M32.detail
    M32.detail = want_detail
    try:
        off = binobj.off(va)
        data = binobj.buf[off:off + nbytes]
        out = []
        for insn in M32.disasm(data, va):
            out.append(insn)
        return out
    finally:
        M32.detail = old


def push_mem_imm_sites(binobj, imm_va):
    """Same scan as find_insn_sites but also returns raw byte offset."""
    return find_insn_sites(binobj, imm_va)


if __name__ == "__main__":
    b = Bin()
    print("ImageBase 0x%x" % b.image_base)
    for s in b.sections:
        print("%-8s va 0x%08x vsize 0x%06x raw 0x%06x rawsize 0x%06x"
              % (s["name"], s["va"], s["vsize"], s["raw"], s["rawsize"]))
    print("iat slots:", len(b.iat))
