# -*- coding: utf-8 -*-
"""OOF independent re-implementation of the 88-row `this` upward walk.

Deliberately a DIFFERENT implementation from the gate: this one
  * re-decodes .text itself (does not import r061/r062 gate),
  * frames a caller by scanning backwards for the previous `ret` (same rule the
    doc states: ret-framed),
  * resolves ecx -> writer -> source register -> writer ... with a 2-step cap,
  * reports the writer VAs and the raw bytes at those VAs so the chain hex can
    be compared to the disk.
It does not aim to reproduce every gate nuance; it aims to say, for each of the
88 rows, whether an independent walk finds the SAME verdict and the SAME writer
bytes.
"""
import re
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
GATE62 = r"D:\Project\ra2-campaign-forge\re_atlas\tools\r062_upward_trace_contract.py"

raw = open(EXE, "rb").read()
e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]
optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", raw, opt + 28)[0]
tab = opt + optsz
SEC = []
for i in range(nsec):
    nm = raw[tab + i * 40: tab + i * 40 + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i * 40 + 8)
    SEC.append(dict(name=nm, va=IB + va, vsz=vsz, rp=rp, rsz=rsz))
TEXT = next(s for s in SEC if s["name"] == ".text")
TLO, THI = TEXT["va"], TEXT["va"] + TEXT["rsz"]
tb = raw[TEXT["rp"]:TEXT["rp"] + TEXT["rsz"]]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
S = []
va = TLO
while va < THI:
    off = va - TLO
    hit = False
    for insn in md.disasm(tb[off:off + 16], va, count=1):
        tgt = None
        for o in insn.operands:
            if o.type == CS_OP_IMM:
                tgt = o.imm
        S.append(dict(va=insn.address, sz=insn.size, bs=insn.bytes.hex(),
                      mn=insn.mnemonic, op=insn.op_str, tgt=tgt))
        va += insn.size
        hit = True
        break
    if not hit:
        va += 1
IX = {r["va"]: i for i, r in enumerate(S)}

GLOBALS = {0x887180, 0x887208, 0x887128, 0x887058, 0x8870C0, 0x89F518}
REGS = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp")
SAVED = ("ebx", "esi", "edi", "ebp")


def frame_lo(call_i):
    j = call_i - 1
    while j >= 0 and S[j]["mn"] != "ret":
        j -= 1
    return j + 1


def writers_of(reg, stop_i, lo_i, cross_calls):
    """yield (index, row) of mov/lea writing `reg` scanning backwards from stop_i-1 down to lo_i"""
    j = stop_i - 1
    while j >= lo_i:
        r = S[j]
        if r["mn"] == "call" and not (cross_calls and reg in SAVED):
            return
        if r["mn"] in ("mov", "lea") and r["op"].startswith(reg + ", "):
            yield j, r
        j -= 1


def first_writer(reg, stop_i, lo_i, cross_calls):
    for j, r in writers_of(reg, stop_i, lo_i, cross_calls):
        return j, r
    return None, None


def slot(expr):
    m = re.search(r"\[esp \+ (0x[0-9a-f]+)\]", expr)
    return m.group(1) if m else None


def ebp_disp(expr):
    m = re.search(r"\[ebp \+ (0x[0-9a-f]+|\d+)\]", expr)
    if not m:
        return None
    s = m.group(1)
    return int(s, 16) if s.startswith("0x") else int(s)


def slot_written(expr_slot, lo_i, call_i):
    pat = re.compile(r"^dword ptr \[esp \+ %s\], " % re.escape(expr_slot))
    n = 0
    for q in range(lo_i, call_i):
        r = S[q]
        if r["mn"] == "mov" and pat.match(r["op"]):
            n += 1
    return n


def walk(call_va):
    ci = IX[call_va]
    lo = frame_lo(ci)
    out = {"verdict": None, "chain": [], "writer_vas": []}
    j, r = first_writer("ecx", ci, lo, False)
    if r is None:
        out["verdict"] = "unknown-thunk"
        return out
    out["chain"].append(r["bs"])
    out["writer_vas"].append(r["va"])
    src = r["op"].split(", ", 1)[1]
    if re.match(r"^0x[0-9a-f]+$", src):
        out["verdict"] = "global-load" if int(src, 16) in GLOBALS else "imm"
        return out
    is_mem = src.endswith("]")
    if not is_mem and src in REGS and src != "ecx":
        j2, r2 = first_writer(src, j, lo, True)
        if r2 is None:
            out["verdict"] = "unknown-reg"
            return out
        out["chain"].append(r2["bs"])
        out["writer_vas"].append(r2["va"])
        src2 = r2["op"].split(", ", 1)[1]
        if re.match(r"^0x[0-9a-f]+$", src2):
            out["verdict"] = "global-load" if int(src2, 16) in GLOBALS else "imm"
            return out
        d = ebp_disp(src2)
        if d is not None and d >= 8:
            out["verdict"] = "param1-forward"
            return out
        s2 = slot(src2)
        if s2:
            if r2["mn"] == "lea":
                out["verdict"] = "stack-object"
            else:
                out["verdict"] = "param-slot" if slot_written(s2, lo, ci) == 0 else "local-slot"
            return out
        if src2 == "ecx":
            # caller-self iff no ecx writer / call in between
            clean = True
            for q in range(lo, j2):
                rr = S[q]
                if rr["mn"] == "call":
                    clean = False
                    break
                if rr["mn"] in ("mov", "lea") and rr["op"].startswith("ecx, "):
                    clean = False
                    break
            out["verdict"] = "caller-self" if clean else "unknown-reg"
            return out
        out["verdict"] = "unknown-reg"
        return out
    if is_mem:
        s = slot(src)
        if s:
            if r["mn"] == "lea":
                out["verdict"] = "stack-object"
            else:
                out["verdict"] = "param-slot" if slot_written(s, lo, ci) == 0 else "local-slot"
            return out
        m = re.match(r"^\[dword ptr 0x([0-9a-f]+)\]$", src)
        if m:
            v = int(m.group(1), 16)
            out["verdict"] = "global-load" if v in GLOBALS else "other"
            return out
        out["verdict"] = "other"
        return out
    out["verdict"] = "caller-self" if src == "ecx" else "other"
    return out


src = open(GATE62, "r", encoding="utf-8").read()
m = re.search(r"^CHAIN = \{(.*?)^\}", src, re.S | re.M)
lit = {}
for mm in re.finditer(r'0x([0-9a-f]+): \("([a-z0-9\-]+)", "([^"]*)"\)', m.group(1)):
    lit[int(mm.group(1), 16)] = (mm.group(2), mm.group(3))

print("== 88-row independent walk vs frozen CHAIN literal ==")
bad = []
for k in sorted(lit):
    w = walk(k)
    exp_v, exp_ch = lit[k]
    got_ch = ";".join(w["chain"])
    okv = w["verdict"] == exp_v
    okc = got_ch == exp_ch
    if not (okv and okc):
        bad.append((k, exp_v, exp_ch, w["verdict"], got_ch, w["writer_vas"]))
print("rows:", len(lit), " mismatches:", len(bad))
for b in bad[:10]:
    print("  MISMATCH %08X exp=(%s,%s) got=(%s,%s) writer_vas=%s"
          % (b[0], b[1], b[2], b[3], b[4], ["%08X" % x for x in b[5]]))

# byte-vs-disk: for each row, the chain hex must be literally present at the
# writer VAs the walk reported
print("\n== chain hex vs disk bytes at reported writer VAs ==")
nb = 0
for k in sorted(lit):
    w = walk(k)
    exp = lit[k][1].split(";") if lit[k][1] else []
    for i, (bv, ch) in enumerate(zip(w["writer_vas"], exp)):
        off = None
        for s in SEC:
            if s["va"] <= bv < s["va"] + s["vsz"]:
                off = s["rp"] + (bv - s["va"])
                break
        disk = raw[off:off + len(ch) // 2].hex() if off is not None else "OOB"
        if disk != ch:
            nb += 1
            print("  BYTEDIFF %08X idx%d disk=%s chain=%s" % (bv, i, disk, ch))
print("byte diffs:", nb)

# negative controls (same as gate's, re-derived here)
print("\n== negative controls on MY walker ==")
import subprocess
callers = {}
for r in S:
    if r["mn"] == "call" and r["tgt"] and TLO <= r["tgt"] < THI:
        callers.setdefault(r["tgt"], []).append(r["va"])
tot = 0
for hv in (0x5276d0, 0x528a10, 0x5295f0, 0x5283d0, 0x528f00):
    c = [walk(x)["verdict"] for x in callers.get(hv, [])]
    cs = sum(1 for v in c if v == "caller-self")
    gl = sum(1 for v in c if v == "global-load")
    tot += cs
    print("  host %08X callers=%d caller-self=%d global-load=%d" % (hv, len(c), cs, gl))
print("  caller-self total over 5 direct hosts:", tot, "(book: 51)")
sm = 0
for hv in (0x527920, 0x527cc0, 0x527f20, 0x528220, 0x528c00, 0x529160, 0x52a760):
    cs = sum(1 for x in callers.get(hv, []) if walk(x)["verdict"] == "caller-self")
    gl = sum(1 for x in callers.get(hv, []) if walk(x)["verdict"] == "global-load")
    sm += cs
    print("  SMALL host %08X callers=%d caller-self=%d global-load=%d" % (hv, len(callers.get(hv, [])), cs, gl))
print("  SMALL caller-self total:", sm, "(book: 0/88)")
