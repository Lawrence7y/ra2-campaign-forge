# -*- coding: utf-8 -*-
"""R-062 gate: `this` upward attribution for the 7 small witness hosts.

Closes R-061 悬项「上行再一跳仍可查」: every aligned caller of each SMALL host
is walked one hop up (ret-framed, call-boundary aware), with an INDEPENDENT
walker; per-caller verdicts must equal the frozen table (machine-generated from
`--dump` on 2026-10-27 and cross-checked against out/_probe_r062f/g -- G-65).

Verdicts:
  param-slot    : ecx <- [esp+X] (direct or via saved reg), frame writes X zero
                  times => X is an INCOMING cdecl argument slot (threaded).
  local-slot    : same but the frame DOES write the slot.
  stack-object  : ecx <- lea [esp+X] => caller-local object; 0x528c00 rows
                  carry the GenericList vptr-store evidence (RTTI-named).
  param1-forward: ecx <- saved reg <- mov reg,[ebp+0x8] (caller's own arg1).
  caller-self   : ecx <- reg written by `mov reg,ecx` before any ecx clobber.
  global-load   : ecx <- imm32 that is one of the six INI globals (positive
                  control only; expected ZERO across SMALL hosts = theorem of
                  the pinned hist).
  unknown-reg   : saved-reg chain dead-ends at the incoming value (threaded,
                  identity still UNKNOWN -- honest).
  unknown-thunk : no ecx writer in caller frame (thunk tail).

Honest boundary: param-slot/param1-forward/unknown-* are identity-THREADING
statements one hop up -- they do NOT name the instance; R-061's UNKNOWN
instance ledger STANDS. Static only; no runtime/rewritable claims (C26-04).

CLI:  python re_atlas/tools/r062_upward_trace_contract.py [--dump]
Exit: 0 iff all PASS.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r061_witness_this_contract as G  # noqa: E402

GLOBALS = G.GLOBALS
SMALL = G.SMALL
REGS = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp")
SAVED = ("ebx", "edi", "esi", "ebp")
CTX_ASM = 0x6E4DE0  # TagClass ctor (R-052), NOT a CCINIClass host

# ---- frozen verdict histograms per SMALL host (measured 2026-10-27) --------
VERD_HIST = {
    0x527920: {"param-slot": 2},
    0x527cc0: {"param-slot": 5},
    0x527f20: {"param-slot": 5, "unknown-reg": 2},
    0x528220: {"unknown-thunk": 1},
    0x528c00: {"param-slot": 39, "local-slot": 1, "stack-object": 17,
               "unknown-reg": 10},
    0x529160: {"param-slot": 3},
    0x52a760: {"param1-forward": 3},
}
# ---- frozen per-caller chain table (machine-generated via gate --dump on 2026-10-27;
# cross-verified against out/_probe_r062f.json independent walker: 88/88 rows agree)
CHAIN = {
    0x46cd7b: ("param-slot", "8bcf;8bbc240c040000"),
    0x474a5f: ("unknown-thunk", ""),
    0x4acec7: ("param-slot", "8bcf;8bbc2438010000"),
    0x4ad77a: ("param-slot", "8bcf;8bbc2438010000"),
    0x4f1d7b: ("param-slot", "8b4c2428"),
    0x4f1fe1: ("param-slot", "8bcd;8b6c2420"),
    0x4f208e: ("param-slot", "8bce;8b742420"),
    0x4f2ced: ("unknown-reg", "8bce"),
    0x4f2d5c: ("unknown-reg", "8bce"),
    0x4f2e30: ("unknown-reg", "8bce"),
    0x4f3219: ("unknown-reg", "8bce"),
    0x4f32a4: ("unknown-reg", "8bce"),
    0x4f32e9: ("unknown-reg", "8bce"),
    0x4f332e: ("unknown-reg", "8bce"),
    0x4f337c: ("unknown-reg", "8bce"),
    0x4f33ca: ("unknown-reg", "8bce"),
    0x4f38f9: ("unknown-reg", "8bce;8bf2"),
    0x4f39c1: ("unknown-reg", "8bce;8bf2"),
    0x4f3bf3: ("unknown-reg", "8bce"),
    0x5cefc9: ("stack-object", "8d4c2438"),
    0x5cf10e: ("stack-object", "8d4c2438"),
    0x5cf162: ("stack-object", "8d4c2438"),
    0x5cf284: ("stack-object", "8d4c2438"),
    0x5cf2e0: ("stack-object", "8d4c2438"),
    0x5cf42c: ("stack-object", "8d4c2438"),
    0x5cf4c7: ("stack-object", "8d4c2438"),
    0x5cf9f0: ("param-slot", "8b4c2450"),
    0x5cfa65: ("param-slot", "8b4c2444"),
    0x5cfaf0: ("param-slot", "8b4c244c"),
    0x5cfb63: ("param-slot", "8b4c2444"),
    0x5cfbef: ("param-slot", "8b4c244c"),
    0x5cfcf4: ("param-slot", "8b4c2450"),
    0x5cfd69: ("param-slot", "8b4c2448"),
    0x5cfe50: ("param-slot", "8b4c2448"),
    0x5cffb5: ("param-slot", "8b4c2450"),
    0x5d76a9: ("stack-object", "8d8c2488000000"),
    0x641b3c: ("param-slot", "8bcf;8b7c2470"),
    0x6874a9: ("param-slot", "8bcd;8b6c2418"),
    0x687516: ("param-slot", "8bcd;8b6c2418"),
    0x68a754: ("param1-forward", "8bcf;8b7d08"),
    0x68a772: ("param1-forward", "8bcf;8b7d08"),
    0x68a790: ("param1-forward", "8bcf;8b7d08"),
    0x69a53a: ("param-slot", "8bcf;8bbc2418020000"),
    0x69a659: ("param-slot", "8bcf;8bbc2418020000"),
    0x71241d: ("param-slot", "8bce;8bb4247c030000"),
    0x720577: ("param-slot", "8bcd;8b6c240c"),
    0x75d8b2: ("param-slot", "8bcf;8bbc2450010000"),
    0x768236: ("param-slot", "8bcd;8bac24e0000000"),
    0x768287: ("param-slot", "8bcd;8bac24e0000000"),
    0x7682dc: ("param-slot", "8bcd;8bac24e0000000"),
    0x768343: ("param-slot", "8bcd;8bac24e0000000"),
    0x7684b2: ("param-slot", "8bcd;8bac24e0000000"),
    0x768511: ("param-slot", "8bcd;8bac24e0000000"),
    0x768570: ("param-slot", "8bcd;8bac24e0000000"),
    0x7685cf: ("param-slot", "8bcd;8bac24e0000000"),
    0x768643: ("param-slot", "8bcd;8bac24e0000000"),
    0x768713: ("param-slot", "8bcd;8bac24e0000000"),
    0x7687a0: ("param-slot", "8bcd;8bac24e0000000"),
    0x76881a: ("param-slot", "8bcd;8bac24e0000000"),
    0x7688d8: ("param-slot", "8bcd;8bac24e0000000"),
    0x768955: ("param-slot", "8bcd;8bac24e0000000"),
    0x768a21: ("param-slot", "8bcd;8bac24e0000000"),
    0x768ae1: ("param-slot", "8bcd;8bac24e0000000"),
    0x768b84: ("param-slot", "8bcd;8bac24e0000000"),
    0x768bc9: ("param-slot", "8bcd;8bac24e0000000"),
    0x768c0f: ("param-slot", "8bcd;8bac24e0000000"),
    0x768c7e: ("param-slot", "8bcd;8bac24e0000000"),
    0x768cc3: ("param-slot", "8bcd;8bac24e0000000"),
    0x768dd9: ("param-slot", "8bcd;8bac24e0000000"),
    0x768f91: ("param-slot", "8b8c24a4000000"),
    0x76c555: ("stack-object", "8d4c2438"),
    0x76cae0: ("param-slot", "8bcf;8b7c2428"),
    0x76cc4b: ("param-slot", "8bcd;8b6c242c"),
    0x76ccbb: ("param-slot", "8bcd;8b6c242c"),
    0x76cd0d: ("param-slot", "8bcd;8b6c242c"),
    0x770655: ("param-slot", "8bcd;8b6c241c"),
    0x770774: ("local-slot", "8bcd;8b6c241c"),
    0x77089d: ("param-slot", "8b4c2424"),
    0x771114: ("param-slot", "8b4c2420"),
    0x7711fd: ("param-slot", "8b4c2424"),
    0x77884f: ("stack-object", "8d4c2438"),
    0x77890c: ("stack-object", "8d4c2438"),
    0x778956: ("stack-object", "8d4c2438"),
    0x778bcf: ("stack-object", "8d4c2438"),
    0x778dd1: ("stack-object", "8d4c2438"),
    0x778e24: ("stack-object", "8d4c2438"),
    0x779c3d: ("stack-object", "8d4c2424"),
    0x779ebd: ("stack-object", "8d4c2424"),
}
# ---- positive control: walker global-load over the 5 direct hosts ---------
GL_CONTROL = {0x5276d0: 164, 0x528a10: 90, 0x5295f0: 118, 0x5283d0: 3,
              0x528f00: 2}
VPTR_STORES = {0x7787c0: "c7442438041b7e00", 0x779bb3: "c7442424041b7e00",
               0x779e33: "c7442424041b7e00"}
GENERICLIST_VT = 0x7E1B04
CONSTR_LEA_ADJ = 17
P1F = {"edi_w_va": 0x689E9C, "edi_w_bytes": "8b7d08",
       "G_edi_w_va": 0x687744, "G_edi_w_bytes": "8b7c2418",
       "slot18_writers": 0, "F_e8_callers": [0x687853],
       "F_head": 0x689E90, "F_head_bytes": "558bec83e4f883ec3453"}

# frozen walked-set per host (base run 2026-10-27; a caller NOP'd or re-targeted
# by mutation vanishes from the walked set -> U-set flips RED; set membership
# is judged against this LITERAL, never against the live CHAIN mapping).
HOST_ROWS = {
    0x527920: frozenset({0x71241D, 0x75D8B2}),
    0x527CC0: frozenset({0x4ACEC7, 0x4AD77A, 0x641B3C, 0x6874A9, 0x687516}),
    0x527F20: frozenset({0x4F2E30, 0x4F3219, 0x7684B2, 0x768511, 0x768570, 0x7685CF, 0x768955}),
    0x528220: frozenset({0x474A5F}),
    0x528C00: frozenset({0x4F1D7B, 0x4F1FE1, 0x4F208E, 0x4F2CED, 0x4F2D5C, 0x4F32A4, 0x4F32E9, 0x4F332E, 0x4F337C, 0x4F33CA, 0x4F38F9, 0x4F39C1, 0x4F3BF3, 0x5CEFC9, 0x5CF10E, 0x5CF162, 0x5CF284, 0x5CF2E0, 0x5CF42C, 0x5CF4C7, 0x5CF9F0, 0x5CFA65, 0x5CFAF0, 0x5CFB63, 0x5CFBEF, 0x5CFCF4, 0x5CFD69, 0x5CFE50, 0x5CFFB5, 0x5D76A9, 0x69A659, 0x768236, 0x768287, 0x7682DC, 0x768343, 0x768643, 0x768713, 0x7687A0, 0x76881A, 0x7688D8, 0x768A21, 0x768AE1, 0x768B84, 0x768BC9, 0x768C0F, 0x768C7E, 0x768CC3, 0x768DD9, 0x768F91, 0x76C555, 0x76CAE0, 0x76CC4B, 0x76CCBB, 0x76CD0D, 0x770655, 0x770774, 0x77089D, 0x771114, 0x7711FD, 0x77884F, 0x77890C, 0x778956, 0x778BCF, 0x778DD1, 0x778E24, 0x779C3D, 0x779EBD}),
    0x529160: frozenset({0x46CD7B, 0x69A53A, 0x720577}),
    0x52A760: frozenset({0x68A754, 0x68A772, 0x68A790}),
}
_ctx = {}


def load():
    import struct
    G.load()
    mut = {}
    for _it in os.environ.get("R062_MUTATE", "").split(","):
        if "=" in _it:
            _k, _v = _it.split("=", 1)
            mut[int(_k, 0)] = int(_v, 0) & 0xFF
    TLO, THI = G._ctx["TLO"], G._ctx["THI"]
    # .text bytes reach the decode stream via G.build; .rdata bytes (RTTI,
    # vtables, data windows) only reach rb()/blob. Feeding .rdata VAs to
    # G.build would index the .text buffer out of range.
    text_mut = {a: v for a, v in mut.items() if TLO <= a < THI}
    stream, callers, idx, pred, buf = G.build(text_mut)
    blob = bytearray(open(G.EXE, "rb").read())

    def _fo(va, bb):
        e_ = struct.unpack_from("<I", bb, 0x3C)[0]
        n_ = struct.unpack_from("<H", bb, e_ + 6)[0]
        oz_ = struct.unpack_from("<H", bb, e_ + 20)[0]
        ib_ = struct.unpack_from("<I", bb, e_ + 24 + 28)[0]
        tb_ = e_ + 24 + oz_
        rva = va - ib_
        for i in range(n_):
            vs, va_, rs, rp = struct.unpack_from("<IIII", bb, tb_ + i * 40 + 8)
            if va_ <= rva < va_ + vs:
                f = rp + (rva - va_)
                return f if f < rp + rs else None
        return None
    for a, v in mut.items():
        f = _fo(a, blob)
        if f is None:
            raise SystemExit("R062_MUTATE target %08X not disk-backed" % a)
        blob[f] = v
    blob = bytes(blob)
    e = struct.unpack_from("<I", blob, 0x3C)[0]
    nsec = struct.unpack_from("<H", blob, e + 6)[0]
    optsz = struct.unpack_from("<H", blob, e + 20)[0]
    opt = e + 24
    ib = struct.unpack_from("<I", blob, opt + 28)[0]
    tab = opt + optsz
    secs = []
    for i in range(nsec):
        vs, va, rs, rp = struct.unpack_from("<IIII", blob, tab + i * 40 + 8)
        secs.append((va, vs, rp, rs))
    _ctx.update(stream=stream, callers=callers, idx=idx, pred=pred, buf=buf,
                TLO=G._ctx["TLO"], BLOB=blob, IB=ib, SECS=secs)


def rb(va, n):
    """whole-image read via PE section table: .text addresses route through the
    stream buffer; RTTI/vtables live in .rdata beyond that window (r058 recipe;
    R-062 lesson: a .text-only rb silently returns zeros past the section)."""
    secs = _ctx["SECS"]
    rva = va - _ctx["IB"]
    for s, vs, rp, rs in secs:
        if s <= rva < s + vs:
            fo = rp + (rva - s)
            if fo < rp + rs:
                return bytes(_ctx["BLOB"][fo:fo + n])
            return bytes(n)  # BSS-ish: beyond raw range reads as zeros
    return b""


def frame_lo(call_va):
    stream, idx = _ctx["stream"], _ctx["idx"]
    j = idx[call_va] - 1
    while j >= 0 and stream[j][3] != "ret":
        j -= 1
    return stream[j + 1][0]


def nearest_writer(reg, from_va, saved_cross, lo):
    """first backward mov/lea writing reg; saved regs cross calls, volatile
    stop at a call (conservative: the call may clobber)."""
    stream, idx = _ctx["stream"], _ctx["idx"]
    j = idx[from_va] - 1
    while j >= 0 and stream[j][0] >= lo:
        a, s, bs, mn, op, t = stream[j]
        if mn in ("mov", "lea") and op.startswith(reg + ", "):
            return a, bs, mn, op.split(", ", 1)[1]
        if mn == "call" and not (saved_cross and reg in SAVED):
            return None
        if mn == "x87-boundary":
            return None
        j -= 1
    return None


def esp_slot(src):
    m = re.search(r"esp \+ (0x[0-9a-f]+)", src)
    return m.group(1) if m else None


def ebp_disp(src):
    """[ebp+disp] signed parse: capstone renders small disps DECIMAL (8) and
    larger hex -- both shapes must be read (probe#6 lesson)."""
    m = re.search(r"ebp \+ (0x[0-9a-f]+|\d+)", src)
    if not m:
        return None
    s = m.group(1)
    return int(s, 16) if s.startswith("0x") else int(s)


def slot_writers(slot, call_va):
    stream, idx = _ctx["stream"], _ctx["idx"]
    pat = re.compile(r"^dword ptr \[esp \+ %s\], (\w+)$" % re.escape(slot))
    out = []
    for q in range(idx[frame_lo(call_va)], idx[call_va]):
        a, s, bs, mn, op, t = stream[q]
        if mn == "mov":
            m = pat.match(op)
            if m:
                out.append((a, bs, m.group(1)))
    return out


def classify_call(call_va):
    """returns (verdict, chain_bytes)."""
    lo = frame_lo(call_va)
    w = nearest_writer("ecx", call_va, False, lo)
    if w is None:
        return "unknown-thunk", []
    a, bs, mn, src = w
    chain = [bs]
    m = re.match(r"^0x([0-9a-f]+)$", src)
    if m:
        return ("global-load" if int(m.group(1), 16) in GLOBALS
                else "imm"), chain
    mem = src.endswith("]") and "[" in src
    if not mem and src in REGS and src != "ecx":
        w2 = nearest_writer(src, a, True, lo)
        if w2 is None:
            return "unknown-reg", chain
        a2, bs2, mn2, src2 = w2
        chain.append(bs2)
        m2 = re.match(r"^0x([0-9a-f]+)$", src2)
        if m2:
            return ("global-load" if int(m2.group(1), 16) in GLOBALS
                    else "imm"), chain
        if ebp_disp(src2) is not None and ebp_disp(src2) >= 8:
            return "param1-forward", chain
        slot = esp_slot(src2)
        if slot:
            if mn2 == "lea":
                return "stack-object", chain
            return ("param-slot" if not slot_writers(slot, call_va)
                    else "local-slot"), chain
        if src2 == "ecx":
            # CALLER-THIS iff no ecx writer between frame entry and a2 AND no
            # intervening call clobbers ecx (ecx is caller-clobberable).
            stream, idx = _ctx["stream"], _ctx["idx"]
            jj = idx[a2] - 1
            clean = True
            while jj >= 0 and stream[jj][0] >= lo:
                _, _, _, mn3, op3, _ = stream[jj]
                if mn3 == "call":
                    clean = False
                    break
                if mn3 in ("mov", "lea") and op3.startswith("ecx, "):
                    clean = False
                    break
                jj -= 1
            return ("caller-self" if clean else "unknown-reg"), chain
        return "unknown-reg", chain
    if mem:
        slot = esp_slot(src)
        if slot:
            if mn == "lea":
                return "stack-object", chain
            return ("param-slot" if not slot_writers(slot, call_va)
                    else "local-slot"), chain
        if re.match(r"^\[dword ptr 0x([0-9a-f]+)\]$", src):
            v = int(re.match(r"^\[dword ptr 0x([0-9a-f]+)\]$", src).group(1), 16)
            return ("global-load" if v in GLOBALS else "other"), chain
        return "other", chain
    if src == "ecx":
        return "caller-self", chain
    return "other", chain


def dump_table():
    load()
    callers = _ctx["callers"]
    out = []
    for host in SMALL:
        for c_ in sorted(callers.get(host, [])):
            v, chain = classify_call(c_)
            out.append('    0x%x: ("%s", "%s"),' % (c_, v, ";".join(chain)))
    print("CHAIN = {")
    print("\n".join(out))
    print("}")


def run_case():
    load()
    return check_body()


def check_body():
    R = []

    def ok(label, cond, msg=""):
        R.append((label, bool(cond), msg))
    callers = _ctx["callers"]

    for host in sorted(VERD_HIST):
        got, rowsv = {}, {}
        hs = sorted(callers.get(host, []))
        for c_ in hs:
            v, ch = classify_call(c_)
            got[v] = got.get(v, 0) + 1
            rowsv[c_] = (v, ";".join(ch))
        # walked set vs the FROZEN host rows (a NOP'd/re-targeted caller ->
        # set-diff RED against a literal, never the live CHAIN mapping).
        ok("U-set-%06x" % host, set(hs) == HOST_ROWS[host],
           "walked set != pinned (%d vs %d; miss %s extra %s)" % (
               len(hs), len(HOST_ROWS[host]),
               sorted(hex(x) for x in HOST_ROWS[host] - set(hs)),
               sorted(hex(x) for x in set(hs) - HOST_ROWS[host])))
        ok("U-hist-%06x" % host, got == VERD_HIST[host],
           "verdict hist %s got %s" % (sorted(VERD_HIST[host].items()),
                                       sorted(got.items())))
        ok("U-tot-%06x" % host, sum(got.values()) == G.SMALL_TOT[host],
           "caller total %d==%d" % (sum(got.values()), G.SMALL_TOT[host]))
        for c_, (v, ch) in rowsv.items():
            if c_ in CHAIN:
                pv, pch = CHAIN[c_]
                ok("U-chain-%06x" % c_, (v, ch) == (pv, pch),
                   "chain %s got (%s,%s)" % ((pv, pch), v, ch))
            else:
                ok("U-known-%06x" % c_, False, "unpinned caller walked")

    for hv, exp in sorted(GL_CONTROL.items()):
        n = sum(1 for c_ in callers.get(hv, [])
                if classify_call(c_)[0] == "global-load")
        ok("U-ctl-%06x" % hv, n == exp,
           "walker global-load==%d got %d" % (exp, n))

    for va, pat in sorted(VPTR_STORES.items()):
        ok("U-vptrstore-%06x" % va, rb(va, 8) == bytes.fromhex(pat),
           "GenericList vptr store pinned @%s" % hex(va))
    col = int.from_bytes(rb(GENERICLIST_VT - 4, 4), "little")
    td = int.from_bytes(rb(col + 0xC, 4), "little")
    nm = rb(td + 8, 32).split(b"\0")[0].decode("latin1")
    ok("U-rtti-name", nm == ".?AVGenericList@@", "RTTI name=%r" % nm)
    ok("U-rtti-ctl", rb(0x8174C8, 4) == bytes.fromhex("94957f00"),
       "RTTI layout control: CCINIClass TD vfp 0x7F9594")

    idx, stream = _ctx["idx"], _ctx["stream"]
    adj = sum(1 for c_ in callers.get(0x528c00, [])
              if classify_call(c_)[0] == "stack-object"
              and stream[idx[c_] - 1][3] == "lea")
    ok("U-lea-adj", adj == CONSTR_LEA_ADJ,
       "lea-before-call over stack-object rows==%d got %d" % (CONSTR_LEA_ADJ, adj))

    ok("U-p1f-edi", rb(P1F["edi_w_va"], 3) == bytes.fromhex(P1F["edi_w_bytes"]),
       "caller G-frame mov edi,[ebp+8] @0x689E9C")
    ok("U-p1f-G", rb(P1F["G_edi_w_va"], 4) == bytes.fromhex(P1F["G_edi_w_bytes"]),
       "F-frame mov edi,[esp+0x18] @0x687744")
    ok("U-p1f-slot0", len(slot_writers("0x18", 0x687853)) ==
       P1F["slot18_writers"], "[esp+0x18] writers in F frame==0")
    ok("U-p1f-Fcallers", sorted(callers.get(P1F["F_head"], [])) ==
       P1F["F_e8_callers"], "aligned callers of F==[0x687853]")
    ok("U-p1f-Fhead", rb(P1F["F_head"], 10) ==
       bytes.fromhex(P1F["F_head_bytes"]), "F head prologue pinned")

    # CTX_ASM never appears as a verdict (it is not a CCINIClass host)
    allv = set()
    for host in VERD_HIST:
        for c_ in callers.get(host, []):
            allv.add(classify_call(c_)[0])
    ok("U-noverdict-drift", "imm" not in allv, "no imm verdict across SMALL: %s"
       % sorted(allv))

    n_pass = sum(1 for _, c_, _ in R if c_)
    return R, n_pass


def main():
    if "--dump" in sys.argv:
        dump_table()
        sys.exit(0)
    R, n_pass = run_case()
    for label, cond, msg in R:
        print(("PASS " if cond else "FAIL ") + label + ": " + msg)
    print("== %d/%d PASS ==" % (n_pass, len(R)))
    sys.exit(0 if n_pass == len(R) else 1)


if __name__ == "__main__":
    main()
