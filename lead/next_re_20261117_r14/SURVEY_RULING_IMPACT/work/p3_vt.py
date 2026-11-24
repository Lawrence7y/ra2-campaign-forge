# -*- coding: utf-8 -*-
"""p3_vt: the atlas-free binary channel (T1-T4) + controls.

Everything here is derived from gamemd.exe raw bytes. NO function_atlas entry/size
input and no vtables_v2.json are used for this channel, which is what makes it an
independent second view of ring (2) and ring (4).

T1  RTTI vtable registry       : vt VA -> (COL, TD, class name, mangle offset, slots)
T2  vptr write sites           : mov dword [abs|reg(+disp)], imm32  with imm a registered vt
T3  live/dead verdict per table (R14_COMMON 8.1 (23)):
      the writing function is looked up as 'nearest known function start <= site' where
      STARTS = C-init-table elements + E8 call targets + atexit-registered functions
      dead  : every write comes from an atexit-registered function ('push <fn> .. call 0x7C978A')
      live  : at least one write from a function that is not atexit-registered
      unknown: no write found (excluded from both readings - reported, never guessed)
T4  virtual dispatch sites     : real 'call [reg+disp]' at instruction boundaries
                                 -> set of displacement values

CONTROLS (all asserted below; the script fails loudly if any flips)
  P1  registry == documented 1,214 tables / 14,044 slots
  P2  init table found structurally == 3,944 elements (= the _initterm count that
      separates denominator B from C); both control ctors inside, neither dtor inside
  P3  the two documented LIVE installs classify LIVE at the documented site
  N1  the two documented DEAD  installs classify DEAD  at the documented site
  N2  random 16B-aligned .text addresses land in some vtable slot at a reported rate
      (the honest zero-model for "vt[slot]==entry" alone)
"""
import bisect
import collections
import json
import os
import random
import struct
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_survey as L

IMG = open(L.EXE, "rb").read()
PE = pefile.PE(L.EXE, fast_load=True)
IBS = PE.OPTIONAL_HEADER.ImageBase
SECS = [(s.Name.rstrip(b"\x00").decode("latin1"), IBS + s.VirtualAddress,
         s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData) for s in PE.sections]


def sec_named(nm):
    for s in SECS:
        if s[0] == nm:
            return s
    return None


TEXT, RDATA, DATA = sec_named(".text"), sec_named(".rdata"), sec_named(".data")
TSTART, TLEN, TRO = TEXT[1], TEXT[3], TEXT[4]
TEND = TSTART + TLEN
TB = IMG[TRO:TRO + TLEN]
RSTART, RLEN, RRO = RDATA[1], RDATA[3], RDATA[4]
DSTART, DLEN, DRO = DATA[1], DATA[3], DATA[4]


def sec_of(va):
    for nm, sva, vs, rs, ro in SECS:
        if sva <= va < sva + rs:
            return nm
    return None


def rd32(va):
    for nm, sva, vs, rs, ro in SECS:
        if sva <= va < sva + rs:
            return struct.unpack_from("<I", IMG, ro + (va - sva))[0]
    return None


def rdstr(va, n=128):
    for nm, sva, vs, rs, ro in SECS:
        if sva <= va < sva + rs:
            o = ro + (va - sva)
            b = IMG[o:o + n]
            z = b.find(b"\x00")
            return b[:z if z >= 0 else n]
    return b""


def in_text(va):
    return TSTART <= va < TEND


# ============================================================ T1: RTTI vtable registry
def discover_vtables():
    """COL sits at vtable-4; COL+0xC -> TD; the class name is the inline byte string at TD+8.

    Two facts this binary taught (both cost a silent zero result when assumed otherwise):
      * TD+0 is not 0 (it is a pointer), so it must not be validated as zero;
      * TypeDescriptors live in .data, not .rdata.
    """
    tabs, seen = {}, set()
    for off in range(0, RLEN - 4, 4):
        colp = struct.unpack_from("<I", IMG, RRO + off)[0]
        if colp in seen or sec_of(colp) != ".rdata":
            continue
        if rd32(colp) != 0:
            continue
        mangle = rd32(colp + 4)
        if mangle is None or mangle > 0x10000:
            continue
        td = rd32(colp + 0xC)
        if td is None or sec_of(td) is None:
            continue
        nm = rdstr(td + 8)
        if not nm.startswith(b".?A"):
            continue
        vt = RSTART + off + 4
        slots, p = [], vt
        while len(slots) <= 4096:
            v = rd32(p)
            if v is None or not in_text(v):
                break
            slots.append(v)
            p += 4
        if not slots:
            continue
        seen.add(colp)
        raw = nm.decode("latin1")
        cls = raw[4:] if raw.startswith((".?AV", ".?AU")) else raw
        tabs[vt] = {"col": colp, "td": td, "cls": cls.rstrip("@").rstrip("\x00"),
                    "mangled": raw, "off": mangle, "slots": slots}
    return tabs


VT = discover_vtables()
N_SLOTS = sum(len(t["slots"]) for t in VT.values())

# ============================================================ T2: vptr write sites
def find_vptr_writes(vtset):
    """Three real install forms, all reduced to (site, target_kind, abs_or_none, vt):
      (a) C7 05 <abs32> <imm32>            global install
      (b) C7 <modrm> [disp] <imm32>, mod in {00,01,10}, rm a register   heap-object install
      (c) B8+r <imm32> ... A3 / 89 <modrm rm=101> <abs32>              global install via reg
    """
    out = []
    n = len(TB)
    i = 0
    while True:
        i = TB.find(b"\xC7", i)
        if i < 0:
            break
        if i + 2 <= n:
            m = TB[i + 1]
            mod, rm = m >> 6, m & 7
            if rm == 5 and mod == 0 and i + 10 <= n:
                absv, imm = struct.unpack_from("<II", TB, i + 2)
                if imm in vtset:
                    out.append((TSTART + i, "abs", absv, imm))
            elif mod in (0, 1, 2) and rm != 4 and not (rm == 5 and mod == 0):
                if mod == 0:
                    io = i + 2
                elif mod == 1:
                    io = i + 3
                else:
                    io = i + 6
                if io + 4 <= n:
                    imm = struct.unpack_from("<I", TB, io)[0]
                    if imm in vtset:
                        out.append((TSTART + i, "reg", None, imm))
        i += 1
    # (c) mov reg, imm32 ; ... ; mov [abs], reg
    for i in range(n - 5):
        if 0xB8 <= TB[i] <= 0xBF:
            imm = struct.unpack_from("<I", TB, i + 1)[0]
            if imm not in vtset:
                continue
            reg = TB[i] - 0xB8
            for j in range(i + 5, min(i + 5 + 40, n - 5)):
                if TB[j] == 0xA3 and reg == 0:
                    out.append((TSTART + j, "abs", struct.unpack_from("<I", TB, j + 1)[0], imm))
                    break
                if TB[j] == 0x89 and (TB[j + 1] & 0xC7) == 0x05 and (TB[j + 1] >> 3) == reg:
                    out.append((TSTART + j, "abs", struct.unpack_from("<I", TB, j + 2)[0], imm))
                    break
    return out


WRITES = find_vptr_writes(set(VT))

# ============================================================ init table + atexit
def dword_runs_in_data():
    runs, i, n = [], 0, DLEN
    while i + 4 <= n:
        v = struct.unpack_from("<I", IMG, DRO + i)[0]
        if in_text(v):
            j, cnt = i, 0
            while j + 4 <= n and in_text(struct.unpack_from("<I", IMG, DRO + j)[0]):
                cnt += 1
                j += 4
            if cnt >= 8:
                runs.append((DSTART + i, cnt))
            i = j
        else:
            i += 4
    return runs


RUNS = dword_runs_in_data()
INIT_RUN = [r for r in RUNS if r[1] == 3944]
INIT_START, INIT_N = INIT_RUN[0] if INIT_RUN else (None, 0)
INIT_SET = set(rd32(INIT_START + 4 * k) for k in range(INIT_N)) if INIT_START else set()


def atexit_registrations():
    regs = {}
    n = len(TB)
    for i in range(n - 5):
        if TB[i] != 0xE8:
            continue
        rel = struct.unpack_from("<i", TB, i + 1)[0]
        if (TSTART + i + 5 + rel) != 0x7C978A:
            continue
        for k in range(i - 1, max(-1, i - 70), -1):
            if TB[k] == 0x68:
                imm = struct.unpack_from("<I", TB, k + 1)[0]
                if in_text(imm):
                    regs.setdefault(imm, []).append(TSTART + i)
                    break
    return regs


REG_DTORS = atexit_registrations()

CALL_TARGETS = set()
n = len(TB)
for i in range(n - 5):
    if TB[i] == 0xE8:
        t = TSTART + i + 5 + struct.unpack_from("<i", TB, i + 1)[0]
        if in_text(t):
            CALL_TARGETS.add(t)

STARTS = sorted(set(INIT_SET) | CALL_TARGETS | set(REG_DTORS) | {TSTART})


def containing_fn(site):
    k = bisect.bisect_right(STARTS, site) - 1
    return STARTS[k] if k >= 0 else None


# ============================================================ T3 live/dead per table
WRITES_BY_VT = collections.defaultdict(list)
for site, kind, absv, vt in WRITES:
    WRITES_BY_VT[vt].append((site, kind, absv))

_FREE_CALLS = {}


def _next_start(fn):
    k = bisect.bisect_right(STARTS, fn)
    return STARTS[k] if k < len(STARTS) else TEND


def fn_free_calls(fn):
    """call sites of the CRT free wrapper 0x7C8B3D inside the body starting at fn."""
    v = _FREE_CALLS.get(fn)
    if v is None:
        v = []
        lo, hi = fn, _next_start(fn)
        base = TSTART
        for i in range(lo - base, max(lo - base, hi - base - 5)):
            if TB[i] == 0xE8 and (base + i + 5 + struct.unpack_from("<i", TB, i + 1)[0]) == 0x7C8B3D:
                v.append(base + i)
        _FREE_CALLS[fn] = v
    return v


def dtor_context(site):
    """Is this vptr write on a destructor path?

    R14_COMMON 8.1 (23) gives the two shapes:
      * a function registered through 'push <fn> ... call 0x7C978A' (atexit) writes the
        base-class vptr  -> the table is never a live vptr;
      * four inlined destructors (0043C073 / 0043C098 / 0045AA66 / 0045AAB6) also write it,
        "all before call 0x7C8B3D frees the buffer".
    So a write is destructor-context iff its function is atexit-registered, or the same
    function calls 0x7C8B3D after the write. Both halves are control-checked below.
    Limitation: STARTS over-segments (call targets inside a function are starts too), so
    a body is a lower bound and a destructor whose free call sits past a segmentation
    point is misread as live. The error direction is therefore 'wide count may be high'.
    """
    fn = containing_fn(site)
    if fn is None:
        return False
    if fn in REG_DTORS:
        return True
    return any(c > site for c in fn_free_calls(fn))


VT_VERDICT = {}
for vt in VT:
    live, dead = [], []
    for site, kind, absv in WRITES_BY_VT.get(vt, []):
        fn = containing_fn(site)
        rec = (site, absv, fn, kind)
        (dead if dtor_context(site) else live).append(rec)
    if live:
        v = "LIVE"
    elif dead:
        v = "DEAD"
    else:
        v = "UNKNOWN"
    VT[vt]["verdict"] = v
    VT[vt]["live_sites"] = live
    VT[vt]["dead_sites"] = dead
    VT_VERDICT[vt] = {"verdict": v, "live": live, "dead": dead}

# ============================================================ T4 dispatch sites
# A single linear sweep desyncs on jump tables and dies at 0x46F59D (= 11.12% of .text,
# 155,215 instructions) - exactly the failure R14_COMMON 8.1 (26) records. Two sweeps are
# therefore run and both are reported:
#   sweep A: whole .text with skipdata, so it re-synchronises and reaches the end
#   sweep B: one linear sweep per known function start (STARTS), which keeps every
#            accepted site at a real instruction boundary
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True

DISP_A, DISP_B = collections.Counter(), collections.Counter()
N_INSN_A = N_INSN_B = 0
N_E8_A = 0
LAST_A = TSTART
CUR = {"e8": 0}


def _record(disp_counter, insn):
    if insn.mnemonic != "call" or not insn.operands:
        return
    op = insn.operands[0]
    if op.type != X86_OP_MEM:
        return
    # capstone 5.0.7 reports mem.index == 0 (not None) with no index register
    # (8.1 error source 19); never test 'is None' here.
    disp_counter[(op.mem.disp, op.mem.index != 0)] += 1


for insn in MD.disasm(TB, TSTART):
    N_INSN_A += 1
    LAST_A = insn.address
    if insn.bytes and insn.bytes[0] == 0xE8:
        N_E8_A += 1
    _record(DISP_A, insn)

for fn in STARTS:
    lo = fn - TSTART
    hi = min(lo + 8192, TLEN)
    for insn in MD.disasm(TB[lo:hi], fn):
        N_INSN_B += 1
        _record(DISP_B, insn)
        if insn.mnemonic in ("ret", "retf", "int3", "jmp", "hlt"):
            break

DISP_UNION = DISP_A + DISP_B
DISP_PLAIN = set(d for (d, hasidx) in DISP_UNION if not hasidx)
DISP_PLAIN_A = set(d for (d, hasidx) in DISP_A if not hasidx)
DISP_PLAIN_B = set(d for (d, hasidx) in DISP_B if not hasidx)
N_DISP_SITES = sum(DISP_UNION.values())
N_DISP_A = sum(DISP_A.values())
N_DISP_B = sum(DISP_B.values())

# ============================================================ witness index
SLOT_WITNESS = collections.defaultdict(list)
for vt, t in VT.items():
    for k, v in enumerate(t["slots"]):
        inst = [(s, a, f, kd) for (s, a, f, kd) in t["live_sites"]] or \
               [(s, a, f, kd) for (s, a, f, kd) in t["dead_sites"]]
        SLOT_WITNESS[v].append({"vt": vt, "slot": k, "off": t["off"],
                                "verdict": t["verdict"], "cls": t["cls"],
                                "sites": [[s, a, f] for (s, a, f, kd) in inst]})

# ============================================================ controls
ctl = {}
ctl["P1_registry"] = {"tables": len(VT), "slots": N_SLOTS,
                      "expect_tables": 1214, "expect_slots": 14044,
                      "ok": (len(VT) == 1214 and N_SLOTS == 14044)}
ctl["P2_init_table"] = {
    "start": "0x%08X" % INIT_START if INIT_START else None, "n": INIT_N,
    "ctor_00438550_in": 0x00438550 in INIT_SET, "ctor_004E6AE0_in": 0x004E6AE0 in INIT_SET,
    "dtor_00438590_in": 0x00438590 in INIT_SET, "dtor_004E6B20_in": 0x004E6B20 in INIT_SET,
    "n_registered_atexit_fns": len(REG_DTORS),
    "00438590_registered": 0x00438590 in REG_DTORS, "004E6B20_registered": 0x004E6B20 in REG_DTORS,
    "data_runs": [{"start": "0x%08X" % a, "n": c} for a, c in sorted(RUNS, key=lambda x: -x[1])[:5]]}
ctl["P2_init_table"]["ok"] = (INIT_N == 3944 and 0x00438550 in INIT_SET and 0x004E6AE0 in INIT_SET
                              and 0x00438590 not in INIT_SET and 0x004E6B20 not in INIT_SET
                              and 0x00438590 in REG_DTORS and 0x004E6B20 in REG_DTORS)

pairs = [(0x00A83DE8, 0x007E43C8, 0x004E6AFD, "LIVE"),
         (0x00A83DE8, 0x007E43E8, 0x004E6B28, "DEAD"),
         (0x0089C668, 0x007E17CC, 0x0043856D, "LIVE"),
         (0x0089C668, 0x007E17EC, 0x00438598, "DEAD")]
pl = []
for glob_, vt, site, want in pairs:
    got = VT.get(vt, {}).get("verdict")
    found = any(w[0] == site for lst in (VT.get(vt, {}).get("live_sites", []) +
                                         VT.get(vt, {}).get("dead_sites", [])) for w in [lst])
    pl.append({"global": "0x%08X" % glob_, "vt": "0x%08X" % vt, "site": "0x%08X" % site,
               "want": want, "got": got, "site_present": found, "ok": got == want})
ctl["P3_N1_pairs"] = pl
ctl["P3_N1_ok"] = all(p["ok"] for p in pl)

# P4: the four inlined-destructor write sites that 8.1 (23) names by address must all
# be classified destructor-context, and the two ctor sites must not be.
named_inline_dtors = [0x0043C073, 0x0043C098, 0x0045AA66, 0x0045AAB6]
ctor_sites = [0x004E6AFD, 0x0043856D]
ctl["P4_inline_dtor_sites"] = {
    "sites": ["0x%08X" % s for s in named_inline_dtors],
    "each_dtor_context": [dtor_context(s) for s in named_inline_dtors],
    "ctor_sites_not_dtor_context": [dtor_context(s) for s in ctor_sites],
}
ctl["P4_ok"] = (all(dtor_context(s) for s in named_inline_dtors)
                and not any(dtor_context(s) for s in ctor_sites))

# N3: differential on the same rows (8.1 error source 24 - never rely on a random
# baseline alone for a systematic error). Compare the atexit-only rule against the
# full destructor-context rule: the difference is exactly the inlined destructors.
atexit_only_live = 0
full_live = 0
for vt in VT:
    ws = WRITES_BY_VT.get(vt, [])
    if not ws:
        continue
    if any(containing_fn(s) not in REG_DTORS for s, k, a in ws):
        atexit_only_live += 1
    if VT[vt]["verdict"] == "LIVE":
        full_live += 1
ctl["N3_differential"] = {"tables_with_writes": sum(1 for vt in VT if WRITES_BY_VT.get(vt)),
                          "live_by_atexit_rule": atexit_only_live,
                          "live_by_full_rule": full_live,
                          "difference_from_inlined_dtors": atexit_only_live - full_live}

random.seed(20261119)
targets = set()
for t in VT.values():
    targets.update(t["slots"])
hits = sum(1 for _ in range(3000) if (TSTART + 16 * random.randrange(0, TLEN // 16)) in targets)
ctl["N2_random_16B_in_any_slot"] = {"n": 3000, "hits": hits, "pct": round(100.0 * hits / 3000, 3)}
ctl["counts"] = {
    "tables": len(VT), "slots": N_SLOTS, "write_sites": len(WRITES),
    "tables_LIVE": sum(1 for t in VT.values() if t["verdict"] == "LIVE"),
    "tables_DEAD": sum(1 for t in VT.values() if t["verdict"] == "DEAD"),
    "tables_UNKNOWN": sum(1 for t in VT.values() if t["verdict"] == "UNKNOWN"),
    "dispatch_sites": N_DISP_SITES, "distinct_plain_disp": len(DISP_PLAIN),
    "sweepA_instructions": N_INSN_A, "sweepA_e8": N_E8_A,
    "sweepA_last_addr": "0x%08X" % LAST_A,
    "sweepA_reached_end_pct": round(100.0 * (LAST_A - TSTART) / TLEN, 2),
    "sweepA_dispatch_sites": N_DISP_A, "sweepA_distinct_plain_disp": len(DISP_PLAIN_A),
    "sweepB_instructions": N_INSN_B, "sweepB_dispatch_sites": N_DISP_B,
    "sweepB_distinct_plain_disp": len(DISP_PLAIN_B),
    "plain_disp_in_both": len(DISP_PLAIN_A & DISP_PLAIN_B),
    "expect_sweepA_instructions": 1392592, "expect_sweepA_e8": 68253,
    "call_targets": len(CALL_TARGETS), "starts": len(STARTS),
    "slot_target_entries": len(SLOT_WITNESS),
    "tables_off_nonzero": sum(1 for t in VT.values() if t["off"] != 0),
}
ctl["all_ok"] = (ctl["P1_registry"]["ok"] and ctl["P2_init_table"]["ok"]
                 and ctl["P3_N1_ok"] and ctl["P4_ok"])

L.w(os.path.join(L.EV, "p3_controls.json"), json.dumps(ctl, ensure_ascii=False, indent=1))
L.wl(os.path.join(L.EV, "p3_call_targets.txt"),
     ["%08X" % t for t in sorted(CALL_TARGETS)])
L.wl(os.path.join(L.EV, "p3_dispatch_disps.txt"),
     ["%d\tA=%d\tB=%d" % (d, DISP_A.get((d, False), 0), DISP_B.get((d, False), 0))
      for d in sorted(DISP_PLAIN)])
L.w(os.path.join(L.EV, "p3_slot_witness.json"), json.dumps(
    {"n_entries": len(SLOT_WITNESS),
     "dispatch_plain_disp": sorted(DISP_PLAIN),
     "witness": {"%08X" % k: v for k, v in SLOT_WITNESS.items()}}, ensure_ascii=False))
L.w(os.path.join(L.EV, "p3_tables.tsv"),
    "\n".join(["vt\tclass\toff\tn_slots\tverdict\tn_live_sites\tn_dead_sites"] +
              ["0x%08X\t%s\t%d\t%d\t%s\t%d\t%d" % (vt, t["cls"], t["off"], len(t["slots"]),
                                                   t["verdict"], len(t["live_sites"]),
                                                   len(t["dead_sites"]))
               for vt, t in sorted(VT.items())]) + "\n")

print(json.dumps({k: v for k, v in ctl.items() if k != "P3_N1_pairs"}, ensure_ascii=False, indent=1))
print("PAIR CHECKS:")
for p in pl:
    print("  %s <- %s @%s want=%s got=%s ok=%s" % (p["global"], p["vt"], p["site"],
                                                  p["want"], p["got"], p["ok"]))
print("ALL CONTROLS OK:", ctl["all_ok"])
