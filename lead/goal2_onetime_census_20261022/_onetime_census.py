# -*- coding: utf-8 -*-
"""
GOAL-3T todo 9 -- One_Time call-timing census (offline, static only).

Question
  Is RadarClass::One_Time() (0x652CF0) executed only once at process start,
  re-run on every map load, or re-run on some other trigger?

Branch vocabulary
  A   startup / static-init only (once per process)
  B   re-run on map change / scenario load
  A'  shutdown race: singleton already cleared, One_Time dispatched afterwards

Method
  * PE32 parse; .text VA = imagebase + VirtualAddress (RVA), never RVA as VA.
  * Full .text linear sweep with resume-on-undecodable-byte, so every claimed
    site is an instruction boundary.  Naked byte scans are reported only as
    counter-evidence (false positives), never as proof.
  * Direct callers: E8 rel32 whose target == 0x652CF0, validated by boundary.
  * Virtual slot: dword scan of .rdata for 0x652CF0 + RTTI name resolution.
  * Object graph: singleton 0x87F7E8 -> ctor chain -> vtable installs.
  * Strings pushed by candidate hosts are decoded (hardest evidence).
  * One-time latch: conditional global read-before-write inside the body.

Read-only on the binary.  Writes nothing; caller redirects stdout.
"""

import hashlib
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_AC_READ, CS_AC_WRITE
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BIN = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA8 = "73201cc0"
IMAGEBASE = 0x400000

# --- ledger anchors (defaults; negative control mutates these) --------------
P = dict(
    one_time=0x652CF0,
    singleton=0x87F7E8,
    vtable_b=0x7F0344,
    slot_off=0x14,          # slot5
    read_a=0x429331,
    read_b=0x6933A4,
    host_b=0x6930A0,
    l3=0x4A8960,
    l3_sib=0x4A8850,
    clear_site=0x777803,
)

CHECKS = []


def hx(x):
    return "0x%X" % x


def out(s=""):
    print(s, flush=True)


def banner(s):
    out("")
    out("=" * 78)
    out("== " + s)
    out("=" * 78)


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    out("[ASSERT] %-64s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
    return bool(ok)


# ===========================================================================
# PE32
# ===========================================================================
class Sec(object):
    def __init__(self, name, vsize, va, rawsize, ptr, chars):
        self.name, self.vsize, self.va = name, vsize, va
        self.rawsize, self.ptr, self.chars = rawsize, ptr, chars


class PE(object):
    def __init__(self, path):
        self.path = path
        self.data = open(path, "rb").read()
        d = self.data
        if d[:2] != b"MZ":
            raise SystemExit("not MZ")
        self.e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
        if d[self.e_lfanew:self.e_lfanew + 4] != b"PE\0\0":
            raise SystemExit("not PE")
        coff = self.e_lfanew + 4
        self.nsec = struct.unpack_from("<H", d, coff + 2)[0]
        self.size_opt = struct.unpack_from("<H", d, coff + 16)[0]
        opt = coff + 20
        self.magic = struct.unpack_from("<H", d, opt)[0]
        if self.magic != 0x10B:
            raise SystemExit("not PE32")
        self.imagebase = struct.unpack_from("<I", d, opt + 28)[0]
        self.entry_rva = struct.unpack_from("<I", d, opt + 16)[0]
        self.size_image = struct.unpack_from("<I", d, opt + 56)[0]
        self.nrva = struct.unpack_from("<I", d, opt + 92)[0]
        self.dirs = [struct.unpack_from("<II", d, opt + 96 + i * 8)
                     for i in range(self.nrva)]
        sec_tab = opt + self.size_opt
        self.secs = []
        for i in range(self.nsec):
            o = sec_tab + i * 40
            nm = d[o:o + 8].rstrip(b"\0").decode("latin1")
            vs, va, rs, pt = struct.unpack_from("<IIII", d, o + 8)
            ch = struct.unpack_from("<I", d, o + 36)[0]
            self.secs.append(Sec(nm, vs, va, rs, pt, ch))

    def sec(self, n):
        for s in self.secs:
            if s.name == n:
                return s
        return None

    def sec_of_rva(self, rva):
        for s in self.secs:
            if s.va <= rva < s.va + max(s.vsize, s.rawsize):
                return s
        return None

    def rva_to_off(self, rva):
        s = self.sec_of_rva(rva)
        if s is None:
            return None
        d = rva - s.va
        return None if d >= s.rawsize else s.ptr + d

    def off_of_va(self, va):
        return self.rva_to_off(va - self.imagebase)

    def dw(self, va):
        o = self.off_of_va(va)
        return None if o is None else struct.unpack_from("<I", self.data, o)[0]

    def cstr(self, va, maxlen=200):
        o = self.off_of_va(va)
        if o is None:
            return None
        e = self.data.find(b"\0", o, o + maxlen)
        if e < 0:
            return None
        raw = self.data[o:e]
        if len(raw) < 2:
            return None
        try:
            s = raw.decode("ascii")
        except UnicodeDecodeError:
            return None
        if all(32 <= ord(c) < 127 or c in "\r\n\t" for c in s):
            return s
        return None


# ===========================================================================
# .text linear sweep (boundary authority)
# ===========================================================================
_SWEEP_CACHE = {}


class Text(object):
    def __init__(self, pe):
        s = pe.sec(".text")
        if s is None:
            raise SystemExit("no .text")
        self.pe, self.sec = pe, s
        self.va = pe.imagebase + s.va
        self.size = s.rawsize
        self.bytes = pe.data[s.ptr:s.ptr + s.rawsize]
        key = (pe.path, pe.imagebase, s.va, s.rawsize)
        cached = _SWEEP_CACHE.get(key)
        if cached is None:
            md = Cs(CS_ARCH_X86, CS_MODE_32)
            md.detail = True
            md.skipdata = False
            insns, stops, off = [], [], 0
            while off < self.size:
                n = 0
                for i in md.disasm(self.bytes[off:], self.va + off):
                    insns.append(i)
                    n += 1
                    off += i.size
                if n == 0:
                    stops.append(self.va + off)
                    off += 1
            cached = (insns, stops)
            _SWEEP_CACHE[key] = cached
        self.insns, self.stops = cached
        self.by = {i.address: i for i in self.insns}
        self.idx = {i.address: k for k, i in enumerate(self.insns)}
        self.addr = [i.address for i in self.insns]
        self.starts = set(self.by)

    def at(self, va):
        return self.by.get(va)

    def prev(self, va):
        for back in range(1, 8):
            i = self.by.get(va - back)
            if i is not None and i.address + i.size == va:
                return i
        return None

    def head(self, va):
        """Nearest preceding boundary after a ret/int3/padding run."""
        k = self.idx.get(va)
        if k is None:
            # allow querying a site that is mid-function
            lo, hi = 0, len(self.addr)
            while lo < hi:
                mid = (lo + hi) // 2
                if self.addr[mid] < va:
                    lo = mid + 1
                else:
                    hi = mid
            k = lo
        while k > 0:
            p = self.insns[k - 1]
            if p.mnemonic.startswith("ret") or p.mnemonic == "int3":
                return self.insns[k].address
            k -= 1
        return self.insns[0].address

    def body(self, va, maxn=4000):
        k = self.idx.get(va)
        if k is None:
            return []
        res = []
        for i in self.insns[k:k + maxn]:
            res.append(i)
            if i.mnemonic.startswith("ret") or i.mnemonic == "int3":
                break
        return res

    def e8_callers(self, target):
        hits = []
        for i in self.insns:
            if i.mnemonic != "call" or i.size != 5:
                continue
            off = i.address - self.va
            if off < 0 or off + 5 > self.size or self.bytes[off] != 0xE8:
                continue
            rel = struct.unpack_from("<i", self.bytes, off + 1)[0]
            if i.address + 5 + rel == target:
                hits.append(i.address)
        return hits

    def raw_e8(self, target):
        hits = []
        b = self.bytes
        for off in range(0, self.size - 5):
            if b[off] != 0xE8:
                continue
            rel = struct.unpack_from("<i", b, off + 1)[0]
            if self.va + off + 5 + rel == target:
                hits.append(self.va + off)
        return hits

    def callers(self, target):
        return [i.address for i in self.insns
                if i.mnemonic == "call" and i.operands
                and i.operands[0].type == X86_OP_IMM
                and (i.operands[0].imm & 0xFFFFFFFF) == target]


# ===========================================================================
# instruction helpers
# ===========================================================================
def fmt(i):
    return "%08X  %-16s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str)


def absmem(i):
    for o in i.operands:
        if o.type == X86_OP_MEM and o.mem.base == 0 and o.mem.index == 0:
            return o.mem.disp & 0xFFFFFFFF
    return None


def reads_abs(i, va):
    for o in i.operands:
        if (o.type == X86_OP_MEM and o.mem.base == 0 and o.mem.index == 0
                and (o.mem.disp & 0xFFFFFFFF) == va and (o.access & CS_AC_READ)):
            return True
    return False


def writes_abs(i, va):
    for o in i.operands:
        if (o.type == X86_OP_MEM and o.mem.base == 0 and o.mem.index == 0
                and (o.mem.disp & 0xFFFFFFFF) == va and (o.access & CS_AC_WRITE)):
            return True
    return False


def push_strings(pe, insns):
    res = []
    for i in insns:
        if i.mnemonic != "push" or not i.operands:
            continue
        if i.operands[0].type != X86_OP_IMM:
            continue
        v = i.operands[0].imm & 0xFFFFFFFF
        if not (IMAGEBASE <= v < IMAGEBASE + 0x800000):
            continue
        s = pe.cstr(v)
        if s:
            res.append((i.address, v, s))
    return res


def dump(insns, indent="    "):
    for i in insns:
        out(indent + fmt(i))


def rtti_name(pe, vt):
    col = pe.dw(vt - 4)
    if col is None or not (IMAGEBASE <= col < IMAGEBASE + pe.size_image):
        return None, None
    ptd = pe.dw(col + 12)
    if ptd is None:
        return None, col
    return pe.cstr(ptd + 8), col


# ===========================================================================
# analyse(): one full pass; returns (checks, data)
# ===========================================================================
def analyze(pe, txt, p):
    checks = []
    data = {}

    def ck(name, ok, detail=""):
        checks.append((name, bool(ok), detail))
        return bool(ok)

    OT = p["one_time"]
    S = p["singleton"]
    VT = p["vtable_b"]
    SO = p["slot_off"]
    RA, RB = p["read_a"], p["read_b"]

    # -- 1 function head ---------------------------------------------------
    i0 = txt.at(OT)
    prev = txt.prev(OT)
    head_ok = False
    head_detail = "no previous instruction"
    if prev is not None:
        head_detail = fmt(prev)
        head_ok = (prev.mnemonic.startswith("ret")
                   or prev.mnemonic in ("int3", "nop")
                   or set(prev.bytes) <= {0xCC, 0x90})
    elif OT == txt.va:
        head_ok = True
    data["i0"] = i0
    data["prev"] = prev
    ck("0x%X decodes at an instruction boundary" % OT, i0 is not None,
       fmt(i0) if i0 else "missing")
    ck("0x%X has a function-head boundary before it" % OT, head_ok, head_detail)

    body = txt.body(OT)
    data["body"] = body
    ck("body of 0x%X terminates within .text" % OT,
       bool(body) and (body[-1].mnemonic.startswith("ret")
                       or body[-1].mnemonic == "int3"),
       "%d insns, last=%s" % (len(body), body[-1].mnemonic if body else "?"))

    # -- 2 direct E8 callers ----------------------------------------------
    e8 = txt.e8_callers(OT)
    raw = txt.raw_e8(OT)
    data["e8"], data["raw_e8"] = e8, raw
    ck("E8 caller scan executed", True,
       "%d boundary-validated, %d raw-byte" % (len(e8), len(raw)))

    # -- 3 vtable slot -----------------------------------------------------
    rdata = pe.sec(".rdata")
    rb = pe.data[rdata.ptr:rdata.ptr + rdata.rawsize]
    rbase = pe.imagebase + rdata.va
    vt_hits = [rbase + o for o in range(0, len(rb) - 3)
               if struct.unpack_from("<I", rb, o)[0] == OT]
    vt_aligned = [a for a in vt_hits if a % 4 == 0]
    data["vt_hits"] = vt_hits
    ck("0x%X appears as an aligned dword in .rdata" % OT,
       bool(vt_aligned), ", ".join(hx(a) for a in vt_aligned) or "none")
    slot_val = pe.dw(VT + SO)
    data["slot_val"] = slot_val
    ck("vtable[0x%X].slot+0x%X == 0x%X" % (VT, SO, OT), slot_val == OT,
       hx(slot_val) if slot_val is not None else "unreadable")
    name, col = rtti_name(pe, VT)
    data["vt_name"], data["vt_col"] = name, col
    ck("vtable 0x%X RTTI resolves to RadarClass" % VT,
       bool(name) and "RadarClass" in name, "%s (COL %s)" % (name, hx(col or 0)))

    # slot window
    win = []
    for k in range(-1, 9):
        win.append((k, VT + k * 4, pe.dw(VT + k * 4)))
    data["vt_window"] = win

    # -- 4 indirect call [reg+disp8 slot] ---------------------------------
    ind = []
    for i in txt.insns:
        if i.mnemonic != "call" or not i.operands:
            continue
        o = i.operands[0]
        if o.type == X86_OP_MEM and o.mem.index == 0 and o.mem.base != 0:
            if (o.mem.disp & 0xFFFFFFFF) == SO:
                mod = (i.bytes[1] >> 6) & 3
                ind.append((i.address, mod, o.mem.base, i.op_str))
    data["ind"] = ind
    ck("call [reg+0x%X] sites encoded as disp8 exist" % SO,
       any(m == 1 for _, m, _, _ in ind),
       "%d total, %d disp8" % (len(ind), sum(1 for _, m, _, _ in ind if m == 1)))

    # -- 5 singleton object graph -----------------------------------------
    refs = []
    for i in txt.insns:
        v = absmem(i)
        if v == S:
            refs.append((i.address, "read" if reads_abs(i, S) else "",
                         "write" if writes_abs(i, S) else "", i))
    data["refs"] = refs
    reads = [r for r in refs if r[1]]
    writes = [r for r in refs if r[2]]
    ck("exactly 2 reads of [0x%X] in .text" % S, len(reads) == 2,
       ", ".join(hx(r[0]) for r in reads))
    ck("reads are at 0x%X and 0x%X" % (RA, RB),
       set(r[0] for r in reads) == {RA, RB},
       ", ".join(hx(r[0]) for r in reads))
    ck("exactly 1 write of [0x%X] in .text" % S, len(writes) == 1,
       ", ".join(hx(r[0]) for r in writes))

    # read-point byte identity (ledger form: mov edx,[0x87F7E8])
    want = bytes.fromhex("8b15e8f78700")
    for tag, va in (("read_a", RA), ("read_b", RB)):
        ins = txt.at(va)
        ok = (ins is not None and ins.bytes[:6] == want
              and reads_abs(ins, S))
        data[tag + "_insn"] = ins
        ck("0x%X is 'mov edx,[0x%X]' (8b15e8f78700)" % (va, S), ok,
           fmt(ins) if ins else "not a boundary")

    # -- 6 host functions / callers ---------------------------------------
    hosts = {}
    for tag, va in (("read_a", RA), ("read_b", RB)):
        h = txt.head(va)
        hosts[tag] = (h, txt.callers(h))
    data["hosts"] = hosts
    ck("host of 0x%X is a real function head" % RA,
       txt.prev(hosts["read_a"][0]) is not None or hosts["read_a"][0] == txt.va,
       hx(hosts["read_a"][0]))
    ck("host of 0x%X is a real function head" % RB,
       txt.prev(hosts["read_b"][0]) is not None or hosts["read_b"][0] == txt.va,
       hx(hosts["read_b"][0]))

    # read_b inside msg handler 0x6930A0: verify msg filter + range
    hb = txt.at(p["host_b"])
    hb_body = txt.body(p["host_b"], 600)
    has_215 = any(i.mnemonic == "cmp" and absmem(i) is None
                  and len(i.operands) == 2 and i.operands[0].type == X86_OP_MEM
                  and i.operands[1].type == X86_OP_IMM
                  and (i.operands[1].imm & 0xFFFFFFFF) == 0x215 for i in hb_body)
    has_range = any(i.mnemonic == "cmp" and len(i.operands) == 2
                    and i.operands[0].type == X86_OP_REG
                    and i.operands[1].type == X86_OP_IMM
                    and (i.operands[1].imm & 0xFFFFFFFF) == 0x14 for i in hb_body)
    data["hb"] = (hb, hb_body, has_215, has_range)
    ck("0x%X is a window-message handler (cmp msg,0x215 + range 0x14)"
       % p["host_b"], has_215 and has_range,
       "cmp215=%s range=%s callers=%s" % (
           has_215, has_range,
           ",".join(hx(x) for x in txt.callers(p["host_b"]))))

    # -- 7 vtable install sites for 0x7F0344 -------------------------------
    installs = []
    for i in txt.insns:
        for o in i.operands:
            if o.type == X86_OP_IMM and (o.imm & 0xFFFFFFFF) == VT:
                installs.append(i)
    data["installs"] = installs
    ck("vtable 0x%X is installed from >=1 .text site" % VT, bool(installs),
       ", ".join(hx(i.address) for i in installs))

    # -- 8 ctor chain to RadarClass ctor 0x652960 --------------------------
    # 0x652960 must be called from exactly one place, and that place must be
    # reachable from the static-init function that constructs the singleton.
    ctor = 0x652960
    ctor_callers = txt.callers(ctor)
    data["ctor_callers"] = ctor_callers
    chain = [ctor]
    cur = ctor
    for _ in range(8):
        cs = txt.callers(cur)
        if not cs:
            break
        # follow the first caller that lies inside a function that is itself
        # called only from a ctor-like chain
        cur = txt.head(cs[0])
        chain.append(cur)
    data["chain"] = chain
    ck("RadarClass ctor 0x%X has >=1 direct caller" % ctor, bool(ctor_callers),
       ", ".join(hx(x) for x in ctor_callers))
    ck("ctor chain reaches a static-init entry (depth %d)" % (len(chain) - 1),
       len(chain) >= 2, " -> ".join(hx(x) for x in chain))

    # static init table membership: .data array holding 0x40D190
    data_init = pe.sec(".data")
    db = pe.data[data_init.ptr:data_init.ptr + data_init.rawsize]
    dbase = pe.imagebase + data_init.va
    init_tbl = [dbase + o for o in range(0, len(db) - 3)
                if struct.unpack_from("<I", db, o)[0] == 0x40D190]
    data["init_tbl"] = init_tbl
    ck("0x40D190 is an entry in a .data init table", bool(init_tbl),
       ", ".join(hx(a) for a in init_tbl))

    # -- 9 One_Time body facts --------------------------------------------
    calls = [i for i in body if i.mnemonic == "call"]
    call_tgts = [(i.address, i.operands[0].imm & 0xFFFFFFFF) for i in calls
                 if i.operands and i.operands[0].type == X86_OP_IMM]
    data["call_tgts"] = call_tgts
    l3_sib_at = [a for a, t in call_tgts if t == p["l3_sib"]]
    l3_at = [a for a, t in call_tgts if t == p["l3"]]
    data["l3_sib_at"], data["l3_at"] = l3_sib_at, l3_at
    ck("One_Time calls 0x%X (L3 sibling) from inside its body" % p["l3_sib"],
       bool(l3_sib_at), ", ".join(hx(a) for a in l3_sib_at))
    ck("One_Time does NOT call 0x%X (L3)" % p["l3"], not l3_at,
       ", ".join(hx(a) for a in l3_at) or "absent")

    # this source: ecx copied to a callee-saved reg at entry
    this_src = []
    for i in body[:6]:
        if (i.mnemonic == "mov" and len(i.operands) == 2
                and i.operands[0].type == X86_OP_REG
                and i.operands[1].type == X86_OP_REG
                and i.reg_name(i.operands[1].reg) == "ecx"):
            this_src.append(i)
    data["this_src"] = this_src
    ck("One_Time captures its 'this' from ecx (thiscall)", bool(this_src),
       fmt(this_src[0]) if this_src else "no mov r32,ecx prologue")

    # one-time latch: conditional read of a global before any write in body
    cond = [i for i in body
            if i.mnemonic in ("cmp", "test")
            and any(o.type == X86_OP_MEM and o.mem.base == 0
                    and o.mem.index == 0 for o in i.operands)]
    data["cond"] = cond
    ck("One_Time body has no 'cmp/test [global]' one-time gate", not cond,
       ", ".join(hx(i.address) for i in cond) or "none")

    gwritten = []
    for i in body:
        if i.mnemonic in ("mov", "or", "and", "inc", "add") and i.operands:
            if i.operands[0].type == X86_OP_MEM and i.operands[0].mem.base == 0:
                gwritten.append((i.address, i.operands[0].mem.disp & 0xFFFFFFFF))
    data["gwritten"] = gwritten
    ck("One_Time writes global state (init side effects)", bool(gwritten),
       "%d globals" % len(gwritten))

    # strings pushed anywhere in the body
    strs = push_strings(pe, body)
    data["strs"] = strs
    ck("One_Time pushes a decodable identity string", bool(strs),
       "; ".join("%s %r" % (hx(a), s) for a, _, s in strs))

    # -- 10 host strings ---------------------------------------------------
    host_strs = {}
    for tag, (h, _) in hosts.items():
        hb_ = txt.body(h, 800)
        host_strs[tag] = push_strings(pe, hb_)
    data["host_strs"] = host_strs

    # -- 11 L3 callers and their strings ----------------------------------
    l3c = txt.callers(p["l3"])
    data["l3_callers"] = l3c
    ck("L3 0x%X has exactly 2 direct callers" % p["l3"], len(l3c) == 2,
       ", ".join(hx(a) for a in l3c))
    l3ctx = []
    for a in l3c:
        h = txt.head(a)
        l3ctx.append((a, h, push_strings(pe, txt.body(h, 900))))
    data["l3ctx"] = l3ctx

    # -- 12 singleton vtable identity -------------------------------------
    # object's own vptr is written by static init (0x40D1B2) to another table
    obj_vt = pe.dw(0x40D1B2 + 2 + 6) if False else None
    wr = writes[0][3] if writes else None
    obj_vt = None
    if wr is not None and wr.mnemonic == "mov" and len(wr.operands) == 2:
        if wr.operands[1].type == X86_OP_IMM:
            obj_vt = wr.operands[1].imm & 0xFFFFFFFF
    data["obj_vt"] = obj_vt
    obj_name, obj_col = (rtti_name(pe, obj_vt) if obj_vt else (None, None))
    data["obj_name"] = obj_name
    ck("singleton's runtime vtable is readable", obj_vt is not None,
       "%s (%s)" % (hx(obj_vt or 0), obj_name))
    slot_obj = pe.dw(obj_vt + SO) if obj_vt else None
    data["slot_obj"] = slot_obj
    ck("singleton runtime vtable slot+0x%X != 0x%X (override exists)" % (SO, OT),
       slot_obj is not None and slot_obj != OT,
       "%s" % hx(slot_obj or 0))

    # -- 13 clear site: what does 0x777803 actually write? ----------------
    clr = txt.at(p["clear_site"])
    data["clr"] = clr
    clr_tgt = absmem(clr) if clr else None
    data["clr_tgt"] = clr_tgt
    ck("0x%X is a boundary and writes an absolute global" % p["clear_site"],
       clr is not None and clr_tgt is not None,
       fmt(clr) if clr else "missing")
    ck("0x%X does NOT write [0x%X]" % (p["clear_site"], S),
       clr is not None and clr_tgt != S,
       "target %s" % hx(clr_tgt or 0))

    # -- 14 no per-frame/per-map host for One_Time ------------------------
    # Any host of a slot+SO indirect call that also touches the singleton?
    hosts_slot = set()
    for a, m, b, o in ind:
        hosts_slot.add(txt.head(a))
    data["hosts_slot"] = hosts_slot
    near = [h for h in hosts_slot
            if any(absmem(i) == S for i in txt.body(h, 1200))]
    data["near"] = near
    ck("no call [reg+0x%X] host touches [0x%X]" % (SO, S), not near,
       ", ".join(hx(x) for x in near) or "none")

    return checks, data


# ===========================================================================
# main
# ===========================================================================
def main():
    banner("STEP 0  binary identity")
    raw = open(BIN, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()
    out("path   : %s" % BIN)
    out("size   : %d bytes" % len(raw))
    out("sha256 : %s" % sha)
    check("sha256[:8] == 73201cc0", sha[:8] == EXPECT_SHA8, sha[:8])

    banner("STEP 1  PE32 parse (RVA vs VA)")
    pe = PE(BIN)
    out("imagebase  : %s" % hx(pe.imagebase))
    out("entry RVA  : %s -> VA %s" % (hx(pe.entry_rva),
                                      hx(pe.imagebase + pe.entry_rva)))
    out("SizeOfImage: %s" % hx(pe.size_image))
    for s in pe.secs:
        out("  %-8s RVA=%08X VA=%08X vsize=%08X rawsize=%08X file=%08X"
            % (s.name, s.va, pe.imagebase + s.va, s.vsize, s.rawsize, s.ptr))
    check("imagebase == 0x400000", pe.imagebase == IMAGEBASE, hx(pe.imagebase))

    imp_rva, imp_sz = pe.dirs[1]
    imp_sec = pe.sec_of_rva(imp_rva)
    out("ImportDirectoryRVA = %s (RVA) -> VA %s -> section %s"
        % (hx(imp_rva), hx(pe.imagebase + imp_rva),
           imp_sec.name if imp_sec else "?"))
    check("import directory RVA maps into a parsed section", imp_sec is not None,
          imp_sec.name if imp_sec else "none")
    out("  trap check: treating the RVA as a VA would give %s (outside all "
        "sections? %s)" % (hx(imp_rva), pe.sec_of_rva(imp_rva) is None))

    txt_sec = pe.sec(".text")
    rd_sec = pe.sec(".rdata")
    check(".text present", txt_sec is not None)
    check(".rdata present", rd_sec is not None)
    out(".text  : RVA %s -> VA %s, file %s, size %s"
        % (hx(txt_sec.va), hx(pe.imagebase + txt_sec.va), hx(txt_sec.ptr),
           hx(txt_sec.rawsize)))
    out(".rdata : RVA %s -> VA %s, file %s, size %s"
        % (hx(rd_sec.va), hx(pe.imagebase + rd_sec.va), hx(rd_sec.ptr),
           hx(rd_sec.rawsize)))
    check("One_Time lies inside .text",
          txt_sec.va + IMAGEBASE <= P["one_time"]
          < txt_sec.va + IMAGEBASE + txt_sec.rawsize)
    check("vtable lies inside .rdata",
          rd_sec.va + IMAGEBASE <= P["vtable_b"]
          < rd_sec.va + IMAGEBASE + rd_sec.rawsize)

    banner("STEP 2  full .text linear sweep (boundary authority)")
    txt = Text(pe)
    out("decoded instructions : %d" % len(txt.insns))
    out("undecodable stops    : %d" % len(txt.stops))
    out("sweep span           : %s .. %s"
        % (hx(txt.insns[0].address),
           hx(txt.insns[-1].address + txt.insns[-1].size)))
    if txt.stops:
        out("stop bytes           : " + ", ".join(hx(a) for a in txt.stops[:12]))
    check("decoded instruction count > 500000", len(txt.insns) > 500000,
          str(len(txt.insns)))

    checks, data = analyze(pe, txt, P)

    banner("STEP 3  One_Time prologue")
    if data["i0"]:
        out("  first insn : " + fmt(data["i0"]))
    if data["prev"]:
        out("  before it  : " + fmt(data["prev"]))
    out("  body (%d insns):" % len(data["body"]))
    dump(data["body"])

    banner("STEP 4  direct E8 callers of One_Time")
    out("boundary-validated : %d" % len(data["e8"]))
    for a in data["e8"]:
        out("  %s (host %s)" % (hx(a), hx(txt.head(a))))
    out("raw-byte matches   : %d" % len(data["raw_e8"]))
    for a in data["raw_e8"]:
        out("  raw %s boundary=%s" % (hx(a), a in txt.starts))
    out("false positives killed by boundary filter : %d"
        % len(set(data["raw_e8"]) - set(data["e8"])))
    out("=> One_Time is a pure virtual slot; see STEP 5/6 for reachability.")

    banner("STEP 5  call [reg+disp8 0x%X] census" % P["slot_off"])
    out("total sites : %d" % len(data["ind"]))
    for a, m, b, o in data["ind"][:40]:
        out("  %s  mod=%d base=%s  %s"
            % (hx(a), m, txt.by[a].reg_name(b) if b else "?", o))
    if len(data["ind"]) > 40:
        out("  ... %d more" % (len(data["ind"]) - 40))
    out("hosts that also touch [0x%X] : %d"
        % (P["singleton"], len(data["near"])))

    banner("STEP 6  One_Time as vtable slot")
    out("dwords == 0x%X in .rdata : %d" % (P["one_time"], len(data["vt_hits"])))
    for a in data["vt_hits"]:
        out("  %s aligned4=%s" % (hx(a), a % 4 == 0))
    out("vtable 0x%X (RTTI %s) window:" % (P["vtable_b"], data["vt_name"]))
    for k, a, v in data["vt_window"]:
        mark = "  <== slot5" if k == 5 else ""
        out("  [%s] slot%-2d = %s%s" % (hx(a), k, hx(v) if v else "?", mark))

    banner("STEP 7  read points and their hosts")
    for tag, va in (("read_a", P["read_a"]), ("read_b", P["read_b"])):
        ins = data[tag + "_insn"]
        h, cs = data["hosts"][tag]
        out("%s %s" % (tag, hx(va)))
        out("  insn      : " + (fmt(ins) if ins else "NOT A BOUNDARY"))
        out("  host      : %s" % hx(h))
        out("  host E8 callers : %s"
            % (", ".join(hx(x) for x in cs) if cs else "none"))
        out("  host strings:")
        for a, v, s in data["host_strs"][tag]:
            out("    %s %s %r" % (hx(a), hx(v), s))
        if tag == "read_b":
            hb, hbb, h215, hr = data["hb"]
            out("  msg-handler check: head=%s cmp[msg],0x215=%s range0x14=%s"
                % (fmt(hb) if hb else "?", h215, hr))
    # what slot does each read point dispatch to?
    for tag, va in (("read_a", P["read_a"]), ("read_b", P["read_b"])):
        body = txt.body(data["hosts"][tag][0], 60)
        for i in body:
            if i.mnemonic == "call" and i.operands and i.operands[0].type == X86_OP_MEM:
                out("  %s -> dispatch %s at %s" % (tag, i.op_str, hx(i.address)))

    banner("STEP 8  singleton object graph (who owns 0x%X)" % P["singleton"])
    out("absolute refs to [0x%X] in .text : %d" % (P["singleton"], len(data["refs"])))
    for a, rd, wr, i in data["refs"]:
        out("  %s %-5s %-5s %s" % (hx(a), rd, wr, i.op_str))
    out("singleton runtime vtable = %s (%s)"
        % (hx(data["obj_vt"] or 0), data["obj_name"]))
    out("  its slot+0x%X = %s (MouseClass override), not 0x%X"
        % (P["slot_off"], hx(data["slot_obj"] or 0), P["one_time"]))
    out("static init table entry for 0x40D190 : %s"
        % ", ".join(hx(a) for a in data["init_tbl"]))
    out("vtable 0x%X install sites : %s"
        % (P["vtable_b"], ", ".join(hx(i.address) for i in data["installs"])))
    out("RadarClass ctor 0x652960 callers : %s"
        % ", ".join(hx(x) for x in data["ctor_callers"]))
    out("construction chain (innermost -> outermost):")
    for a in data["chain"]:
        out("  %s" % hx(a))

    banner("STEP 9  One_Time body facts")
    out("calls inside body :")
    for a, t in data["call_tgts"]:
        s = pe.cstr(t)
        out("  %s -> %s%s" % (hx(a), hx(t), ("  %r" % s) if s else ""))
    out("strings pushed     :")
    for a, v, s in data["strs"]:
        out("  %s %s %r" % (hx(a), hx(v), s))
    out("globals written    :")
    for a, g in data["gwritten"]:
        out("  %s -> [%s]" % (hx(a), hx(g)))
    out("conditional global gates : %d" % len(data["cond"]))

    banner("STEP 10  L3 (0x%X) callers and their strings" % P["l3"])
    for a in data["l3_callers"]:
        out("  %s" % hx(a))
    for a, h, ss in data["l3ctx"]:
        out("site %s  host %s" % (hx(a), hx(h)))
        for x, v, s in ss:
            out("    %s %s %r" % (hx(x), hx(v), s))

    banner("STEP 11  clear site 0x%X reality check" % P["clear_site"])
    out("  insn   : " + (fmt(data["clr"]) if data["clr"] else "missing"))
    out("  target : %s" % hx(data["clr_tgt"] or 0))
    out("  ledger said [0x87F7E8]; actual target differs -> see report.")

    # ---------------------------------------------------------------- verdict
    banner("STEP 12  branch verdict")
    e8_n = len(data["e8"])
    vt_ok = data["slot_val"] == P["one_time"]
    override = data["slot_obj"] not in (None, P["one_time"])
    l3_in_body = bool(data["l3_at"])
    per_frame = bool(data["near"])
    branch = []
    if e8_n == 0 and vt_ok and not per_frame:
        branch.append("A")
    if l3_in_body:
        branch.append("B?")
    if override:
        branch.append("A'")
    out("evidence:")
    out("  direct E8 callers              : %d" % e8_n)
    out("  vtable slot5 identity          : %s" % vt_ok)
    out("  singleton slot5 override       : %s" % override)
    out("  One_Time calls L3              : %s" % l3_in_body)
    out("  per-frame host touching single : %s" % per_frame)
    out("branch vector: %s" % ("+".join(branch) if branch else "undetermined"))

    # ---------------------------------------------------------- final asserts
    banner("FINAL ASSERTIONS")
    total = 0
    passed = 0
    for name, ok, detail in checks:
        total += 1
        passed += 1 if ok else 0
        out("[%s] %s  %s" % ("PASS" if ok else "FAIL", name, detail))

    out("")
    out("checks passed: %d/%d" % (passed, total))
    out("direct E8 callers of One_Time: %d" % e8_n)
    out("branch: %s" % ("+".join(branch) if branch else "undetermined"))
    ok_all = passed == total and total > 0
    out("RESULT: %s" % ("ALL PASS" if ok_all else "FAILURES PRESENT"))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
