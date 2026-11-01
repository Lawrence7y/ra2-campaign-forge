# -*- coding: utf-8 -*-
"""R-061 · witness `this` upward-trace contract gate (C26-04 main task).

Scope: gamemd.exe sha256 73201cc0...f67476, READ-ONLY. Every literal below was
machine-dumped by out/_probe_r061*_*.py BEFORE assertion (G-65). Function
boundaries come from the BRANCH GRAPH (backward predecessor reach over aligned
fallthrough/jcc/jmp edges; `ret` does NOT create a fallthrough edge; entries =
aligned-E8 call targets), not first-ret, not nop fill (this region has zero nop
padding; the R-059 window method spilled across function boundaries --
corrected in section C).

CONCLUSIONS PINNED HERE
  A. each near-rebase site's containing aligned-head set == the probed singleton
     (0x5293e3: cold head 0x529394 is not an E8 target; bytes pinned instead).
  B. ONE rebase protocol at all 13 sites: mov ecx,[esi+0x30]; add esi,0x2c;
     mov ecx,esi; push; call 0x52B4F0.
  C. ★ correction to R-059: with true heads, the esi feeding each site flows
     from the `[this+8]` cached-CCINIClass load (8b7308/8b7508) or the
     stack-arg form 8b742420 (host 0x52A760).  The `mov esi,ecx` writers R-059
     reported at 4 sites are byte-pinned as PREVIOUS-function prologues below
     the head AND proven to have no branch-graph path into the site (negative
     control for the correction).
  D. registry fallback pair 0xB7882C/0xB78830: per-host loads, [reg+8] self-
     cache fills, walker heads 0x52B430/0x52B210 carry them; walker-return
     imm32 form appears exactly twice each.
  E. caller->`this` histograms: global-direct counts pinned exactly against
     caller totals (757/650/651/306/5); seven small hosts have NO global-direct
     caller (this = forwarded param; attribution stops one hop short = UNKNOWN).
  F. heap factory 0x52CB90: new(0x58) x2, vptr stamp 0x7E1AF4, 4 pinned
     callers; the global ctors stamp all six globals with that vptr.
  G. +0x10 hit-cache cmp/fill pair present in every host (embedded-container
     signature).

Static only: nothing here declares a site runtime-mandatory or safely
rewritable (C26-04).

CLI:  python re_atlas/tools/r061_witness_this_contract.py   -> exit 0 iff all PASS
Lib:  load(); run_case(mut_dict) -> (results, n_pass)       (mutate_r061_gate.py)
"""
import hashlib
import re
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

GLOBALS = {0x887180, 0x887208, 0x887128, 0x887058, 0x8870C0, 0x89F518}
TWINA = 0x52B4F0
HOST_OF = {0x527750: 0x5276d0, 0x5279bd: 0x527920, 0x527d5b: 0x527cc0,
           0x527fd1: 0x527f20, 0x5282a0: 0x528220, 0x528450: 0x5283d0,
           0x528aa7: 0x528a10, 0x528cb7: 0x528c00, 0x528f97: 0x528f00,
           0x5291f3: 0x529160, 0x5293e3: 0x529394, 0x52966e: 0x5295f0,
           0x52a7de: 0x52a760}
REBASE = {
    0x527750: (0x52772c, "8b4e30", 0x52772f, "83c62c"),
    0x5279bd: (0x527999, "8b4e30", 0x52799c, "83c62c"),
    0x527d5b: (0x527d31, "8b4e30", 0x527d34, "83c62c"),
    0x527fd1: (None, None, 0x527fa8, "83c62c"),
    0x5282a0: (0x52827c, "8b4e30", 0x52827f, "83c62c"),
    0x528450: (0x52842c, "8b4e30", 0x52842f, "83c62c"),
    0x528aa7: (0x528a83, "8b4e30", 0x528a86, "83c62c"),
    0x528cb7: (0x528c93, "8b4e30", 0x528c96, "83c62c"),
    0x528f97: (0x528f73, "8b4e30", 0x528f76, "83c62c"),
    0x5291f3: (0x5291cf, "8b4e30", 0x5291d2, "83c62c"),
    0x5293e3: (0x5293bf, "8b4e30", 0x5293c2, "83c62c"),
    0x52966e: (0x52964a, "8b4e30", 0x52964d, "83c62c"),
    0x52a7de: (0x52a7ba, "8b4e30", 0x52a7bd, "83c62c"),
}
CACHE = {
    0x527750: (0x5276fe, "8b7308"), 0x5279bd: (0x52796b, "8b7508"),
    0x527d5b: (0x527d03, "8b7508"), 0x527fd1: (0x527f78, "8b7508"),
    0x5282a0: (0x52824e, "8b7308"), 0x528450: (0x5283fe, "8b7308"),
    0x528aa7: (0x528a55, "8b7508"), 0x528cb7: (0x528c63, "8b7508"),
    0x528f97: (0x528f45, "8b7508"), 0x5291f3: (0x5291a1, "8b7508"),
    0x5293e3: (0x529391, "8b7508"), 0x52966e: (0x52961c, "8b7308"),
    0x52a7de: (0x52a766, "8b742420"),
}
# head signature: first 6 bytes of every host (A-sig pins; kills head-scratch)
HEAD_SIG = {
    0x5276d0: "83ec0c33c053", 0x527920: "81ecac010000", 0x527cc0: "83ec64538d44",
    0x527f20: "83ec7853558b", 0x528220: "83ec0c33c053", 0x5283d0: "83ec0c33c053",
    0x528a10: "83ec0c33c053", 0x528c00: "81ec18040000", 0x528f00: "b814500000e8",
    0x529160: "81ec14040000", 0x529394: "33c03bf00f84", 0x5295f0: "83ec0c33c053",
    0x52a760: "83ec10535556",
}
# registry fallback loads at EXACT addresses per host (census bounded by the
# next host head -- the old [host,+0x500) window let a SIBLING host's load
# satisfy the claim; 0x527F20 genuinely has no 2C load in its own window).
REG2C = {
    0x5276d0: 0x527809, 0x527920: 0x527a5e, 0x527cc0: 0x527dff,
    0x527f20: None, 0x528220: 0x528359, 0x5283d0: 0x528509,
    0x528a10: 0x528b60, 0x528c00: 0x528d58, 0x528f00: 0x529038,
    0x529160: 0x529294, 0x529394: 0x529484, 0x5295f0: 0x529727,
    0x52a760: 0x52a893,
}
REG30 = {
    0x5276d0: 0x52783b, 0x527920: 0x527a87, 0x527cc0: 0x527e28,
    0x527f20: 0x528087, 0x528220: 0x52838b, 0x5283d0: 0x52853b,
    0x528a10: 0x528b92, 0x528c00: 0x528d7c, 0x528f00: 0x529065,
    0x529160: 0x5292c4, 0x529394: 0x5294af, 0x5295f0: 0x529759,
    0x52a760: 0x52a8c5,
}
SPILL = {0x527750: 0x5275cc, 0x527d5b: 0x527b97, 0x528f97: 0x528df2,
         0x52a7de: 0x52a623}
FILL_BYTES = {0x527818: "897308", 0x52782c: "894308", 0x528070: "897508",
              0x52904a: "897508", 0x52a8a2: "897508", 0x52a8b4: "895d08",
              0x528368: "897308", 0x528b73: "897508"}
TRIO = [0x5276d0, 0x527920, 0x527cc0, 0x527f20, 0x528220, 0x5283d0,
        0x528a10, 0x528c00, 0x528f00, 0x529160, 0x529394, 0x5295f0, 0x52a760]
HIST_EXPECT = {0x5276d0: ({0x887180: 119, 0x8870c0: 45}, 757),
               0x528a10: ({0x887180: 80, 0x8870c0: 10}, 650),
               0x5295f0: ({0x887180: 95, 0x8870c0: 23}, 651),
               0x5283d0: ({0x8870c0: 3}, 306),
               0x528f00: ({0x8870c0: 2}, 5)}
SMALL = (0x527920, 0x527cc0, 0x527f20, 0x528220, 0x528c00, 0x529160, 0x52a760)
SMALL_TOT = {0x527920: 2, 0x527cc0: 5, 0x527f20: 7, 0x528220: 1,
             0x528c00: 67, 0x529160: 3, 0x52a760: 3}
# caller ecx-kind histograms (measured 2026-10-26 via the hist scan of THIS
# file -- out/_probe_r061h).  'no GLOBAL key present' is the theorem that
# replaces R-059's negative `E-noglob` claim: positive pin, every entry
# killable (mutate a caller's ecx-writer opcode byte).
SMALL_KINDS = {
    0x527920: {"reg:esi": 1, "reg:edi": 1},
    0x527cc0: {"reg:edi": 3, "reg:ebp": 2},
    0x527f20: {"reg:esi": 2, "reg:ebp": 5},
    0x528220: {"none-in-window": 1},
    0x528c00: {"other:dword ptr [esp + 0x28]": 1, "reg:ebp": 23, "reg:esi": 11,
               "lea-stack": 17, "other:dword ptr [esp + 0x50]": 3,
               "other:dword ptr [esp + 0x44]": 2, "other:dword ptr [esp + 0x4c]": 2,
               "other:dword ptr [esp + 0x48]": 2, "reg:edi": 2,
               "other:dword ptr [esp + 0xa4]": 1, "other:dword ptr [esp + 0x24]": 2,
               "other:dword ptr [esp + 0x20]": 1},
    0x529160: {"reg:edi": 2, "reg:ebp": 1},
    0x52a760: {"reg:edi": 3},
}
STAMPS = {0x887180: 0x40e031, 0x887208: 0x40e0e1, 0x887128: 0x40e191,
          0x887058: 0x40e241, 0x8870c0: 0x40e2f1, 0x89f518: 0x49b405}
COLD_HEAD_BYTES = "33c03bf00f84"  # xor eax,eax; cmp esi,eax; je rel32
SPILL_BYTES = "8bf1"              # mov esi,ecx (NOT 8bce -- that is mov ecx,esi)

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
_ctx = {}


def load():
    raw = open(EXE, "rb").read()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise SystemExit("!! fingerprint drift -- refusing")
    e = struct.unpack_from("<I", raw, 0x3C)[0]
    nsec = struct.unpack_from("<H", raw, e + 6)[0]
    optsz = struct.unpack_from("<H", raw, e + 20)[0]
    opt = e + 24
    IB = struct.unpack_from("<I", raw, opt + 28)[0]
    ENTRY = IB + struct.unpack_from("<I", raw, opt + 16)[0]
    tab = opt + optsz
    SEC = []
    for i in range(nsec):
        name = raw[tab + i * 40: tab + i * 40 + 8].rstrip(b"\0").decode()
        vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i * 40 + 8)
        SEC.append((name, IB + va, vsz, rp, rsz))
    TEXT = next(s for s in SEC if s[0] == ".text")
    assert TEXT[2] == 0x3DF38D, "section drift"
    TLO, THI = TEXT[1], TEXT[1] + TEXT[4]
    _ctx.update(dict(TLO=TLO, THI=THI, ENTRY=ENTRY,
                     buf=bytearray(raw[TEXT[3]: TEXT[3] + TEXT[4]])))
    return _ctx


def _decode(buf, TLO, va):
    end = va - TLO + 15
    code = bytes(buf[max(0, va - TLO):end])
    for insn in MD.disasm(code, va):
        tgt = None
        if insn.operands and insn.operands[0].type == X86_OP_IMM:
            tgt = insn.operands[0].imm
        return (insn.address, insn.size, insn.bytes.hex(), insn.mnemonic,
                insn.op_str, tgt)
    return None


def _maps(stream):
    TLO, THI = _ctx["TLO"], _ctx["THI"]
    callers = {}
    idx = {}
    pred = {}
    for k, (a, size, bs, mn, op, tgt) in enumerate(stream):
        idx[a] = k
        if mn == "call" and tgt is not None and TLO <= tgt < THI:
            callers.setdefault(tgt, []).append(a)
        # a jump lands on its target; fallthrough lands on the next insn -- but
        # only when the jump does NOT terminate the block. jcc fallthrough edge:
        if mn == "jmp" and tgt is not None:
            pred.setdefault(tgt, []).append(a)  # unconditional jump: taken edge
            if not (TLO <= tgt < THI):
                continue  # exits the image (IAT/external): dead end
            # jmp does NOT also fall through; do not add a size edge
            continue
        if mn[0] == "j" and mn != "jmp" and tgt is not None and TLO <= tgt < THI:
            pred.setdefault(tgt, []).append(a)  # conditional taken edge
        if mn in ("ret", "retf"):
            continue  # NO fallthrough across ret: function boundary guard
        if mn == "hlt" or mn == "ud2":
            continue
        nxt = a + size
        if nxt < THI:
            pred.setdefault(nxt, []).append(a)  # fallthrough / conditional not-taken
    return callers, idx, pred


def _full_stream(buf):
    TLO, THI = _ctx["TLO"], _ctx["THI"]
    stream = []
    cur = TLO
    while cur < THI:
        ins = _decode(buf, TLO, cur)
        if ins is None:
            cur += 1
            continue
        stream.append(ins)
        cur += ins[1]
    return stream


def _splice(base_stream, base_index, buf, mut):
    """Return a mutated stream by re-decoding only the windows around each
    mutated byte, or None if re-sync fails (caller falls back to full rebuild)."""
    import bisect
    TLO = _ctx["TLO"]
    base_addrs = sorted(base_index)
    out = list(base_stream)
    for ma in sorted(mut):
        # baseline instruction containing (or nearest at/after) ma
        pos = bisect.bisect_right(base_addrs, ma) - 1
        if pos < 0:
            return None
        k = base_index[base_addrs[pos]]
        start_a = base_addrs[pos]
        # re-decode from start_a; find resync = first decoded addr that is a
        # baseline addr strictly after start_a and equals a baseline boundary.
        cur = start_a
        repl = []
        resynced = False
        guard = 0
        while cur < start_a + 256 and guard < 60:
            ins = _decode(buf, TLO, cur)
            if ins is None:
                cur += 1
                continue
            if cur > start_a and ins[0] in base_index and ins[0] != start_a:
                resynced = True
                break
            repl.append(ins)
            cur = ins[0] + ins[1]
            guard += 1
        if not resynced:
            return None
        # replace base_stream[k : k+len_at_this_side] with repl; compute how many
        # baseline insns lie in [start_a, ins[0]) -- replace exactly those.
        j = k
        span = 0
        while j < len(out) and out[j][0] < ins[0]:
            span += 1
            j += 1
        out[k:k + span] = repl
    return out


def build(mut):
    """(stream, callers, idx, pred, buf) under an in-memory mutation map."""
    TLO = _ctx["TLO"]
    if not mut:
        if "base_stream" not in _ctx:
            _ctx["base_stream"] = _full_stream(_ctx["buf"])
            _ctx["base_index"] = {x[0]: i for i, x in enumerate(_ctx["base_stream"])}
        stream = _ctx["base_stream"]
        buf = _ctx["buf"]
    else:
        if "base_stream" not in _ctx:
            _ctx["base_stream"] = _full_stream(_ctx["buf"])
            _ctx["base_index"] = {x[0]: i for i, x in enumerate(_ctx["base_stream"])}
        buf = bytearray(_ctx["buf"])
        for a, v in mut.items():
            buf[a - TLO] = v
        stream = _splice(_ctx["base_stream"], _ctx["base_index"], buf, mut)
        if stream is None:  # re-sync failed -> honest full rebuild
            stream = _full_stream(buf)
    callers, idx, pred = _maps(stream)
    return stream, callers, idx, pred, buf


def breach(site, pred):
    """every aligned insn address with a branch-graph path INTO `site`."""
    seen = {site}
    work = [site]
    while work:
        a = work.pop()
        for p in pred.get(a, ()):
            if p not in seen:
                seen.add(p)
                work.append(p)
    seen.discard(site)
    return seen


def run_case(mut=None):
    TLO, THI = _ctx["TLO"], _ctx["THI"]
    stream, callers, idx, pred, buf = build(mut)
    R = []

    def ok(label, cond, msg=""):
        R.append((label, bool(cond), msg))

    def at(va):
        k = idx.get(va)
        return stream[k] if k is not None else None

    # ---------- A: branch-graph containment ----------
    E8T = set(callers)
    for s, h in sorted(HOST_OF.items()):
        if s == 0x5293e3:
            b = bytes(buf[h - TLO: h - TLO + 6])
            ok("A-%06x" % s, h in breach(s, pred),
               "cold head 0x529394 reaches site via branch graph")
            ok("A-cold-%06x" % s, b == bytes.fromhex(COLD_HEAD_BYTES),
               "cold head bytes pinned (xor eax,eax; cmp esi,eax; je rel32)")
        else:
            rs = breach(s, pred) & E8T
            ok("A-%06x" % s, rs == {h},
               "containing aligned-E8 head set == {%s}" % hex(h))
    for h, sig in sorted(HEAD_SIG.items()):
        b = bytes(buf[h - TLO: h - TLO + 6])
        ok("A-sig-%06x" % h, b == bytes.fromhex(sig),
           "head signature pinned @%s" % hex(h))

    # ---------- B: rebase protocol ----------
    for s, (m30a, m30b, a2ca, a2cb) in sorted(REBASE.items()):
        if m30a is not None:
            x = at(m30a)
            ok("B1-%06x" % s, x and x[2] == m30b
               and x[3] == "mov" and x[4] == "ecx, dword ptr [esi + 0x30]",
               "mov ecx,[esi+0x30] @%s" % hex(m30a))
        x = at(a2ca)
        ok("B2-%06x" % s, x and x[2] == a2cb and x[3] == "add"
           and x[4] == "esi, 0x2c", "add esi,0x2c @%s" % hex(a2ca))
        x = at(s)
        ok("B3-%06x" % s, x and x[3] == "call" and x[5] == TWINA,
           "call 0x52B4F0 @%s" % hex(s))
        has_ce = False
        cur = s - 12
        while cur < s:
            x = at(cur)
            if x and x[0] == cur and x[3] == "mov" and x[4] == "ecx, esi":
                has_ce = True
                break
            cur += 1
        ok("B4-%06x" % s, has_ce, "mov ecx,esi within 12B before call @%s" % hex(s))

    # ---------- C: esi provenance at each site ----------
    for s, (ca, cb) in sorted(CACHE.items()):
        x = at(ca)
        reach = breach(s, pred)
        ok("C-%06x" % s, x and x[2] == cb and x[0] in reach,
           "cache load [reg+8] @%s reaches site %s (the true esi provider)"
           % (hex(ca), hex(s)))
    for s, wa in sorted(SPILL.items()):
        x = at(wa)
        ok("C-spill-%06x" % s, x and x[2] == SPILL_BYTES and x[4] == "esi, ecx"
           and wa < HOST_OF[s] and wa not in breach(s, pred),
           "R-059 'ecx' writer @%s: bytes pinned (mov esi,ecx), below head %s, "
           "and NO branch-graph path into the site (boundary spill proven, "
           "not assumed)" % (hex(wa), hex(HOST_OF[s])))

    # ---------- D: registry pair, fills, walkers (address-exact) ----------
    # The old [host,+0x500) OR-scan let a SIBLING host's load satisfy the claim
    # (0x527F20+0x500 reaches 0x528220/0x5283D0).  Each registry load is now
    # pinned at its exact instruction, with a bounded negative for 0x527F20-2C.
    HOST_END = {}
    _hs = sorted(set(HOST_OF.values()))
    for _i, _h in enumerate(_hs):
        HOST_END[_h] = _hs[_i + 1] if _i + 1 < len(_hs) else 0x52AD60
    for host in sorted(set(HOST_OF.values())):
        a2c = REG2C[host]
        if a2c is None:
            lo, hi = host, HOST_END[host]
            hit = any(x[3] == "mov" and x[4] == "esi, 0xb7882c"
                      for x in stream if lo <= x[0] < hi)
            ok("D-2C-%06x" % host, not hit,
               "registry-2C ABSENT in host %s's own window [%s,%s) -- cache via call only"
               % (hex(host), hex(lo), hex(hi)))
        else:
            x = at(a2c)
            ok("D-2C-%06x" % host, x and x[2] == "be2c88b700"
               and x[4] == "esi, 0xb7882c",
               "registry-2C imm32 load pinned @%s (host %s)" % (hex(a2c), hex(host)))
        a30 = REG30[host]
        x = at(a30)
        ok("D-30-%06x" % host, x and x[2] == "be3088b700"
           and x[4] == "esi, 0xb78830",
           "registry-30 imm32 load pinned @%s (host %s)" % (hex(a30), hex(host)))
    for fa, fb in sorted(FILL_BYTES.items()):
        x = at(fa)
        ok("D-fill-%06x" % fa, x and x[2] == fb and x[3] == "mov"
           and re.match(r"dword ptr \[(?:ebx|ebp) \+ 8\], (?:eax|esi|ebx)$", x[4]),
           "self-cache fill mov [reg+8],reg @%s" % hex(fa))
    x = at(0x52b4a8)
    ok("D-walk-2c", x and x[4] == "eax, 0xb7882c" and 0x52b430 in breach(0x52b4a8, pred),
       "walker 0x52B430 carries mov eax,0xB7882C @0x52B4A8")
    x = at(0x52b288)
    ok("D-walk-30", x and x[4] == "eax, 0xb78830" and 0x52b210 in breach(0x52b288, pred),
       "walker 0x52B210 carries mov eax,0xB78830 @0x52B288")
    # the ret-4 right after each walker imm32 (M14 targets this byte)
    x = at(0x52b4ae)
    ok("D-walk-2c-ret", x and x[2] == "c20400" and x[3] == "ret" and x[4] == "4",
       "walker 0x52B430 return ret 4 pinned @0x52B4AE")
    x = at(0x52b28e)
    ok("D-walk-30-ret", x and x[2] == "c20400" and x[3] == "ret" and x[4] == "4",
       "walker 0x52B210 return ret 4 pinned @0x52B28E")
    n2c = sum(1 for x in stream if x[3] == "mov" and x[4] == "eax, 0xb7882c")
    n30 = sum(1 for x in stream if x[3] == "mov" and x[4] == "eax, 0xb78830")
    ok("D-walk-count", n2c == 2 and n30 == 2,
       "walker-return imm32 form appears exactly twice each (measured %d/%d)" % (n2c, n30))

    # ---------- E: caller->this histograms (global phase: stream of this case) ----------
    def hist_global(host):
        h = {}
        for c_ in callers.get(host, []):
            k = idx.get(c_)
            if k is None:
                continue
            j = k - 1
            while j >= 0 and stream[j][0] >= c_ - 40:
                _, _, _, mn, op, _ = stream[j]
                if mn in ("call", "ret") or mn[0] == "j":
                    break
                if mn == "mov" and op.startswith("ecx, 0x"):
                    v = int(op.split(", ")[1], 16)
                    if v in GLOBALS:
                        h[v] = h.get(v, 0) + 1
                    break
                j -= 1
        return h

    for host, (exp, tot) in sorted(HIST_EXPECT.items()):
        got = hist_global(host)
        ok("E-hist-%06x" % host, got == exp, "global-direct hist @%s == pinned" % hex(host))
        ok("E-cnt-%06x" % host, len(callers.get(host, [])) == tot,
           "aligned caller count @%s == %d" % (hex(host), tot))

    def kinds(host):
        from collections import Counter
        c = Counter()
        for call_va in callers.get(host, []):
            k = idx.get(call_va)
            j = k - 1
            found = "none-in-window"
            while j >= 0 and stream[j][0] >= call_va - 40:
                _, _, _, mn, op, _t = stream[j]
                if mn in ("call", "ret") or mn[0] == "j":
                    break
                if (mn == "mov" or mn == "lea") and op.startswith("ecx, "):
                    src = op[5:]
                    if re.match(r"^0x[0-9a-f]+$", src):
                        v = int(src, 16)
                        found = "GLOBAL" if v in GLOBALS else ("imm:" + src)
                    elif src in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp"):
                        found = "reg:" + src
                    elif src.startswith("["):
                        found = "lea-stack" if mn == "lea" else "mem"
                    else:
                        found = "other:" + src
                    break
                j -= 1
            c[found] += 1
        return dict(c)

    # ★ E-kind replaces the old `E-noglob` negative claim (R-059 form '== {}').
    # Kind histograms are POSITIVE exact-set pins: 'no global-direct this' is
    # then a theorem of the pin (no GLOBAL key present), and every entry is
    # killable by flipping one caller's ecx-writer opcode byte.
    for host, exp in sorted(SMALL_KINDS.items()):
        got = kinds(host)
        ok("E-kind-%06x" % host, got == exp,
           "caller ecx-kind hist @%s == pinned" % hex(host))
        assert "GLOBAL" not in got or host in HIST_EXPECT
    for host, t in sorted(SMALL_TOT.items()):
        ok("E-scnt-%06x" % host, len(callers.get(host, [])) == t,
           "small host %s caller count == %d" % (hex(host), t))

    # ---------- F: heap factory + global stamps ----------
    def rb(va, n):
        return bytes(buf[va - TLO: va - TLO + n])

    ok("F1-new1", rb(0x52cbfb, 7) == bytes.fromhex("6a58e815c22900"),
       "push 0x58; call new @0x52CBFB")
    ok("F2-new2", rb(0x52ccdb, 7) == bytes.fromhex("6a58e835c12900"),
       "push 0x58; call new @0x52CCDD")
    ok("F3-vptr", rb(0x52cc36, 6) == bytes.fromhex("c706f41a7e00"),
       "factory stamps [esi]=0x7E1AF4 @0x52CC36")
    ok("F4-fcallers", sorted(callers.get(0x52cb90, [])) ==
       [0x52c605, 0x52df25, 0x52e0c4, 0x685609],
       "factory host 0x52CB90: exactly 4 pinned callers")
    for g, sa in sorted(STAMPS.items()):
        pat = bytes.fromhex("c705") + struct.pack("<I", g) + bytes.fromhex("f41a7e00")
        ok("F5-stamp-%06x" % g, rb(sa, 10) == pat,
           "global ctor stamps vptr into @%s" % hex(g))

    # ---------- G: container trio, address-exact (the old has_fill/has_cmp OR
    # inside [host,+0x500) was satisfiable by a sibling -- M24/M25 survived
    # because ANY of ~600 image-wide `894610`/`3901` could stand in) ----------
    # Uniform: cache fill mov [esi+0x10],eax at site+0xD (894610) at every site.
    # cmp dword ptr [ecx],eax (3901) at site-0xB, EXCEPT 0x527d5b (site-0xE) and
    # 0x527fd1 where the hit-cache check is a `call 0x52B4D0` helper at site-0x10.
    for s in sorted(HOST_OF):
        x = at(s + 0xd)
        ok("G-fill-%06x" % s, x and x[2] == "894610" and x[3] == "mov"
           and x[4] == "dword ptr [esi + 0x10], eax",
           "+0x10 hit-cache fill @site+0xd (site %s)" % hex(s))
    CMPD = {s: s - 0xb for s in HOST_OF if s != 0x527d5b}
    CMPD[0x527d5b] = 0x527d4d
    for s, ca in sorted(CMPD.items()):
        if s == 0x527fd1:
            x = at(s - 0x10)
            ok("G-cmp-%06x" % s, x and x[3] == "call" and x[5] == 0x52b4d0,
               "hit-cache check is call 0x52B4D0 helper @0x527FC1 (no inline cmp)")
        else:
            x = at(ca)
            ok("G-cmp-%06x" % s, x and x[2] == "3901" and x[3] == "cmp"
               and x[4] == "dword ptr [ecx], eax",
               "hit-cache cmp [ecx],eax pinned @%s" % hex(ca))

    n_pass = sum(1 for _, c_, _ in R if c_)
    return R, n_pass


def main():
    load()
    R, n_pass = run_case({})
    for label, cond, msg in R:
        print(("PASS " if cond else "FAIL ") + label + ": " + msg)
    print("== %d/%d PASS ==" % (n_pass, len(R)))
    sys.exit(0 if n_pass == len(R) else 1)


if __name__ == "__main__":
    main()
