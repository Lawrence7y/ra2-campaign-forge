#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFY_V3.py -- independent re-verification of four technical claims about
                [0x887368] -> this -> first-deref family in gamemd.exe.

Self-contained: only `struct` + `capstone`. No repo modules, no binaries written.
Read-only. Run:  python VERIFY_V3.py   (redirect stdout for VERIFY_V3.txt)

Claims under test
 1. Sites of the form  mov ecx,[0x887368] ; call <target>  (call immediately
    follows) resolve to exactly {0x724730,0x724580,0x724530,0x724540} with
    call counts 1/4/1/1 (7 sites total).
 2. Each of the four functions has a first this-relative offset
    0x724730->0x250, 0x724580->0x24C, 0x724530->0x228, 0x724540->0x22C
    (alias tracking must follow `mov ebp,ecx` / `mov ebx,ecx`).
 3. No caller reads eax (the return value) of any of the four functions.
 4. Prologue bytes / first-ret operand match the stated table.
"""

import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_AC_WRITE
from capstone.x86 import (
    X86_OP_REG, X86_OP_MEM, X86_OP_IMM,
    X86_REG_ECX, X86_REG_EAX, X86_REG_ESP,
)

# --------------------------------------------------------------------------
# paths (no os import: derive from __file__)
# --------------------------------------------------------------------------
HERE = __file__.replace("\\", "/")
ROOT = HERE.rsplit("/", 3)[0]
EXE = ROOT + "/ra2youli/gamemd.exe"

GLOBAL_VA = 0x887368
TARGETS = [0x724730, 0x724580, 0x724530, 0x724540]
EXPECT_COUNTS = {0x724730: 1, 0x724580: 4, 0x724530: 1, 0x724540: 1}
EXPECT_FIRST = {0x724730: 0x250, 0x724580: 0x24C, 0x724530: 0x228, 0x724540: 0x22C}
EXPECT_PROLOGUE = {
    0x724730: (bytes.fromhex("83ec0c558be9"), 6),
    0x724580: (bytes.fromhex("53555657 8b7c2414".replace(" ", "")), 8),
    0x724530: (bytes.fromhex("8b8128020000"), 6),
    0x724540: (bytes.fromhex("8b812c020000"), 6),
}
EXPECT_RET = {0x724730: 4, 0x724580: 4, 0x724530: None, 0x724540: None}
EXPECT_CRASH = (0x724737, bytes.fromhex("8b8550020000"))

# --------------------------------------------------------------------------
# tiny SHA-256 (struct only)
# --------------------------------------------------------------------------
_K = [
    0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5, 0x3956C25B, 0x59F111F1,
    0x923F82A4, 0xAB1C5ED5, 0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3,
    0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174, 0xE49B69C1, 0xEFBE4786,
    0x0FC19DC6, 0x240CA1CC, 0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
    0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7, 0xC6E00BF3, 0xD5A79147,
    0x06CA6351, 0x14292967, 0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13,
    0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85, 0xA2BFE8A1, 0xA81A664B,
    0xC24B8B70, 0xC76C51A3, 0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
    0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5, 0x391C0CB3, 0x4ED8AA4A,
    0x5B9CCA4F, 0x682E6FF3, 0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208,
    0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2,
]


def _rotr(x, n):
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF


def sha256_hex(data):
    h = [0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
         0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19]
    ln = len(data)
    pad = (56 - (ln + 1) % 64) % 64
    data = data + b"\x80" + b"\x00" * pad + struct.pack(">Q", ln * 8)
    for off in range(0, len(data), 64):
        w = list(struct.unpack(">16I", data[off:off + 64])) + [0] * 48
        for i in range(16, 64):
            s0 = _rotr(w[i - 15], 7) ^ _rotr(w[i - 15], 18) ^ (w[i - 15] >> 3)
            s1 = _rotr(w[i - 2], 17) ^ _rotr(w[i - 2], 19) ^ (w[i - 2] >> 10)
            w[i] = (w[i - 16] + s0 + w[i - 7] + s1) & 0xFFFFFFFF
        a, b, c, d, e, f, g, hh = h
        for i in range(64):
            S1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)
            ch = (e & f) ^ ((~e & 0xFFFFFFFF) & g)
            t1 = (hh + S1 + ch + _K[i] + w[i]) & 0xFFFFFFFF
            S0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            t2 = (S0 + maj) & 0xFFFFFFFF
            hh, g, f, e, d, c, b, a = g, f, e, (d + t1) & 0xFFFFFFFF, c, b, a, (t1 + t2) & 0xFFFFFFFF
        h = [(x + y) & 0xFFFFFFFF for x, y in zip(h, [a, b, c, d, e, f, g, hh])]
    return "".join("%08x" % x for x in h)


# --------------------------------------------------------------------------
# check bookkeeping
# --------------------------------------------------------------------------
CHECKS = []


def check(name, ok, detail):
    CHECKS.append(bool(ok))
    print(("[PASS] " if ok else "[FAIL] ") + name + "  ::  " + detail)


def info(name, detail):
    print("[INFO] " + name + "  ::  " + detail)


# --------------------------------------------------------------------------
# PE parse  (ImageBase at e_lfanew+0x18+0x1C, section VA is RVA)
# --------------------------------------------------------------------------
raw = open(EXE, "rb").read()
info("binary", EXE + "  size=%d (0x%x)" % (len(raw), len(raw)))
digest = sha256_hex(raw)
info("sha256", digest)
check("sha256 prefix == 73201cc0", digest.startswith("73201cc0"), "prefix=" + digest[:8])

if raw[:2] != b"MZ":
    raise SystemExit("not an MZ image")
e_lfanew = struct.unpack_from("<I", raw, 0x3C)[0]
if raw[e_lfanew:e_lfanew + 4] != b"PE\x00\x00":
    raise SystemExit("bad PE signature")
image_base = struct.unpack_from("<I", raw, e_lfanew + 0x18 + 0x1C)[0]
nsec = struct.unpack_from("<H", raw, e_lfanew + 6)[0]
opt_size = struct.unpack_from("<H", raw, e_lfanew + 0x14)[0]
size_of_image = struct.unpack_from("<I", raw, e_lfanew + 0x18 + 0x38)[0]
sec_tab = e_lfanew + 0x18 + opt_size
info("PE", "e_lfanew=0x%x ImageBase=0x%x SizeOfImage=0x%x nsec=%d"
     % (e_lfanew, image_base, size_of_image, nsec))
check("ImageBase == 0x400000", image_base == 0x400000, "ImageBase=0x%x" % image_base)

sections = {}
for i in range(nsec):
    o = sec_tab + i * 40
    nm = raw[o:o + 8].rstrip(b"\x00").decode("latin-1")
    vs, va, rs, ra = struct.unpack_from("<IIII", raw, o + 8)
    sections[nm] = dict(va=va, vs=vs, ra=ra, rs=rs)
    info("section %-8s" % nm, "RVA=0x%x VS=0x%x RAW=0x%x RS=0x%x" % (va, vs, ra, rs))


def sec_bytes(nm):
    s = sections[nm]
    return raw[s["ra"]:s["ra"] + s["vs"]], image_base + s["va"]


text, text_base = sec_bytes(".text")
info(".text", "VA 0x%x .. 0x%x (%d bytes)" % (text_base, text_base + len(text), len(text)))

# --------------------------------------------------------------------------
# disassemble .text
#   NOTE: plain linear disasm stops early (0x46f59d) because it desyncs on
#   embedded data; skipdata is required for full coverage.
# --------------------------------------------------------------------------
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True
insns = list(md.disasm(text, text_base))
info("disasm", "instructions=%d (skipdata) last=0x%x" % (len(insns), insns[-1].address))
covered = insns[-1].address + insns[-1].size - text_base
check(".text fully covered by skipdata disasm", covered >= len(text) - 16,
      "covered=%d / %d" % (covered, len(text)))
idx_of = {ins.address: k for k, ins in enumerate(insns)}
md0 = Cs(CS_ARCH_X86, CS_MODE_32)
md0.detail = True
plain = list(md0.disasm(text, text_base))
info("disasm plain(no skipdata)",
     "stops at 0x%x after %d insns -> would MISS every hit above that"
     % (plain[-1].address, len(plain)))

# --------------------------------------------------------------------------
# CLAIM 1:  mov ecx,[0x887368] ; call <target>
# --------------------------------------------------------------------------
PAT = b"\x8b\x0d" + struct.pack("<I", GLOBAL_VA)      # mov ecx, dword ptr [0x887368]
raw_hits = []
p = 0
while True:
    j = text.find(PAT, p)
    if j < 0:
        break
    raw_hits.append(text_base + j)
    p = j + 1
info("raw byte hits of '8b 0d 68 73 88 00'", "%d" % len(raw_hits))
check("every raw hit is an instruction start",
      all(h in idx_of for h in raw_hits),
      "not-start=%d" % sum(1 for h in raw_hits if h not in idx_of))

adjacent = []        # call immediately follows the mov
loose = []           # call follows, but not adjacent (no ecx clobber in between)
no_call = []
for h in raw_hits:
    k = idx_of[h]
    gap = []
    call = None
    stop = None
    for n in range(1, 16):
        ins = insns[k + n]
        if ins.mnemonic == "call":
            call = ins
            break
        if ins.mnemonic in ("ret", "retf") or ins.mnemonic.startswith("j"):
            stop = ins
            break
        gap.append(ins)
    if call is None:
        no_call.append((h, stop))
        continue
    tgt = call.operands[0].imm if call.operands and call.operands[0].type == X86_OP_IMM else None
    rec = dict(site=h, call=call.address, tgt=tgt, gap=gap)
    (adjacent if not gap else loose).append(rec)

info("mov-sites", "total=%d  call-follows=%d  (adjacent=%d, non-adjacent=%d)  no-call=%d"
     % (len(raw_hits), len(adjacent) + len(loose), len(adjacent), len(loose), len(no_call)))

# 1a. adjacency reading
adj_targets = {}
for r in adjacent:
    adj_targets.setdefault(r["tgt"], []).append(r["site"])
check("claim1: adjacent-site count == 7", len(adjacent) == 7, "measured=%d" % len(adjacent))
check("claim1: adjacent target set == {0x724730,0x724580,0x724530,0x724540}",
      set(adj_targets) == set(TARGETS),
      "measured=" + str(sorted("0x%x" % t for t in adj_targets)))
cnt_ok = all(len(adj_targets.get(t, [])) == EXPECT_COUNTS[t] for t in TARGETS)
check("claim1: per-target counts 1/4/1/1",
      cnt_ok,
      "measured=" + " ".join("0x%x:%d" % (t, len(adj_targets.get(t, []))) for t in TARGETS))
info("claim1: the 7 adjacent sites", "")
for t in TARGETS:
    for s in sorted(adj_targets.get(t, [])):
        print("          site 0x%06x  mov ecx,[0x%x]  call 0x%x" % (s, GLOBAL_VA, t))

# 1b. indirect call after the load (would escape the E8 scan)
ind_count = 0
for h in raw_hits:
    k = idx_of[h]
    for n in range(1, 4):
        if insns[k + n].mnemonic == "call" and insns[k + n].operands[0].type != X86_OP_IMM:
            ind_count += 1
check("claim1: no indirect call directly after the load", ind_count == 0,
      "indirect=%d" % ind_count)

# 1c. guards: does anything between the load and the call change flags?
NO_FLAGS = set("""mov movzx movsx movsxd lea push pop nop xchg cdq cwde cbw cwd
movd movq movaps movups movss movsd movdqa movdqu fld fstp fst fild fistp
bswap setcc cmovcc prefetch bt bts btr btc lea""".split())


def changes_flags(ins):
    m = ins.mnemonic
    if m in NO_FLAGS:
        return False
    if m.startswith(("cmov", "set", "j")):
        return False
    return True


for r in adjacent:
    fl = [g for g in r["gap"] if changes_flags(g)]
    check("claim1: no test/cmp guard at site 0x%06x" % r["site"], len(fl) == 0,
          "flags-modifying insns between load and call=%d (gap insns=%d)"
          % (len(fl), len(r["gap"])))
# context of the 7 sites (upstream branch, informational)
for t in TARGETS:
    for s in sorted(adj_targets.get(t, [])):
        k = idx_of[s]
        ctx = ["0x%x:%s %s" % (insns[i].address, insns[i].mnemonic, insns[i].op_str)
               for i in range(max(0, k - 3), k)]
        info("context before site 0x%06x" % s, " | ".join(ctx))

# 1c-bis. the same pattern must not hide in the appended .detour section
det, det_base = sec_bytes(".detour")
det_hits = det.count(PAT)
check("claim1: no 'mov ecx,[0x887368]' in .detour", det_hits == 0, "measured=%d" % det_hits)
det_calls = 0
mdd = Cs(CS_ARCH_X86, CS_MODE_32)
mdd.detail = True
mdd.skipdata = True
for ins in mdd.disasm(det, det_base):
    if ins.id == 0:
        continue
    try:
        if ins.mnemonic == "call" and ins.operands[0].type == X86_OP_IMM \
                and ins.operands[0].imm in TARGETS:
            det_calls += 1
    except Exception:
        pass
check("claim1: no call to the 4 targets from .detour", det_calls == 0, "measured=%d" % det_calls)

# 1d. literal wording of the criterion ("no other mov ecx in between") -> broader set
loose_targets = {}
for r in loose:
    loose_targets.setdefault(r["tgt"], []).append(r["site"])
info("claim1 NOTE: under the literal wording (only 'no other mov ecx in between')",
     "sites=%d targets=%s"
     % (len(adjacent) + len(loose),
        sorted("0x%x" % t for t in set(list(adj_targets) + list(loose_targets)))))
for t, sites in sorted(loose_targets.items()):
    if t not in adj_targets:
        info("claim1 NOTE: extra target reachable only under the loose reading",
             "0x%x called from %s" % (t, ", ".join("0x%x" % s for s in sites)))
info("claim1 NOTE: no-call hits", "%d, all guarded before any call: %s"
     % (len(no_call),
        all(insns[idx_of[h] + 1].mnemonic in ("test", "cmp", "xor", "mov", "cmp", "add")
            for h, _ in no_call)))

# --------------------------------------------------------------------------
# CLAIM 2: first this-relative offset, with alias tracking
# --------------------------------------------------------------------------
def mem_off(op, taint):
    """this-relative offset of a memory operand, or None if not this-derived."""
    if op.type != X86_OP_MEM:
        return None
    m = op.mem
    if m.segment != 0:
        return None
    if m.base == 0 and m.index == 0:
        return None
    if m.index != 0:
        it = taint.get(m.index)
        if it is not None:          # tainted index arithmetic: not modelled
            return None
    if m.base == 0:
        return None
    bt = taint.get(m.base)
    if bt is None:
        return None
    return bt + m.disp


def first_this_touch(start, args=1, max_n=150):
    """
    Linear walk from `start`. ecx is this (offset 0). Tracks reg->offset aliases
    through mov reg,reg and lea, plus a small stack model for [esp+N] args.
    Returns (first_addr, first_mem, guards, touched_offsets).
    NOTE: ebp is NOT treated as a frame pointer -- 0x724730 does `mov ebp,ecx`.
    """
    taint = {X86_REG_ECX: 0}
    stack = ["ret"] + [("arg", i) for i in range(args)]
    first_addr = None
    first_mem = None
    guards = []
    touched = []
    for n in range(max_n):
        k = idx_of[start] + n
        if k >= len(insns):
            break
        ins = insns[k]
        m = ins.mnemonic
        ops = ins.operands

        # guard detection: test/cmp on a this-tainted register
        if m in ("test", "cmp"):
            for o in ops:
                if o.type == X86_OP_REG and taint.get(o.reg) is not None:
                    guards.append((ins.address, m, ins.op_str))

        # lea: address formation (recorded, but it is not a memory access)
        if m == "lea" and len(ops) == 2 and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_MEM:
            off = mem_off(ops[1], taint)
            if off is not None:
                touched.append((ins.address, off, "lea"))
                if first_addr is None:
                    first_addr = (ins.address, off, "lea")
                taint[ops[0].reg] = off
            else:
                taint[ops[0].reg] = None
            if first_mem is not None:
                break
            continue

        # memory access through this?
        for o in ops:
            off = mem_off(o, taint)
            if off is not None:
                kind = "write" if (o.access & CS_AC_WRITE) else "read"
                touched.append((ins.address, off, kind))
                if first_addr is None:
                    first_addr = (ins.address, off, kind)
                if first_mem is None:
                    first_mem = (ins.address, off, kind)

        # state update
        if m == "push" and ops:
            o = ops[0]
            stack.insert(0, taint.get(o.reg) if o.type == X86_OP_REG else None)
        elif m == "pop" and ops:
            taint[ops[0].reg] = stack.pop(0) if stack else None
        elif m in ("sub", "add") and len(ops) == 2 and ops[0].type == X86_OP_REG \
                and ops[0].reg == X86_REG_ESP and ops[1].type == X86_OP_IMM:
            nslot = abs(ops[1].imm) // 4
            if m == "sub":
                stack = [None] * nslot + stack
            else:
                stack = stack[nslot:] if nslot <= len(stack) else []
        elif m == "mov" and len(ops) == 2:
            if ops[0].type == X86_OP_REG:
                if ops[1].type == X86_OP_REG:
                    taint[ops[0].reg] = taint.get(ops[1].reg)
                else:
                    taint[ops[0].reg] = None    # loaded value != pointer to this
        elif m in ("xor", "sub", "and", "or", "sbb") and len(ops) == 2 \
                and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_REG \
                and ops[0].reg == ops[1].reg:
            taint[ops[0].reg] = None
        elif m in ("movzx", "movsx", "movsxd", "inc", "dec", "neg", "not"):
            if ops and ops[0].type == X86_OP_REG:
                taint[ops[0].reg] = None
        else:
            try:
                _, written = ins.regs_access()
            except Exception:
                written = []
            for r in written:
                if r != X86_REG_ESP:
                    taint[r] = None

        if first_mem is not None:
            break
    return first_addr, first_mem, guards, touched


print()
info("claim2: alias tracking begins", "ecx=this; mov reg,ecx and lea reg,[this+x] propagate")
first_addr_map = {}
first_mem_map = {}
for t in TARGETS:
    fa, fm, guards, touched = first_this_touch(t, args=1)
    first_addr_map[t] = fa
    first_mem_map[t] = fm
    info("fn 0x%x prologue" % t,
         " | ".join("%s %s" % (i.mnemonic, i.op_str)
                    for i in insns[idx_of[t]:idx_of[t] + 6]))
    info("fn 0x%x first this-relative address" % t,
         "0x%x: %s %s -> +0x%X (%s)"
         % (fa[0], insns[idx_of[fa[0]]].mnemonic, insns[idx_of[fa[0]]].op_str, fa[1], fa[2]))
    info("fn 0x%x first this MEMORY access" % t,
         "0x%x: %s %s -> +0x%X (%s)"
         % (fm[0], insns[idx_of[fm[0]]].mnemonic, insns[idx_of[fm[0]]].op_str, fm[1], fm[2]))
    info("fn 0x%x guards on this before first touch" % t,
         "none" if not guards else str([("0x%x" % g[0], g[1], g[2]) for g in guards]))
    info("fn 0x%x all this-relative offsets (first 6)" % t,
         ", ".join("+0x%X@0x%x(%s)" % (o[1], o[0], o[2]) for o in touched[:6]))

for t in TARGETS:
    got = first_addr_map[t][1]
    check("claim2: fn 0x%x first this-relative offset == 0x%X" % (t, EXPECT_FIRST[t]),
          got == EXPECT_FIRST[t], "measured=0x%X (at 0x%x, %s)"
          % (got, first_addr_map[t][0], first_addr_map[t][2]))

# the two extra targets reachable only under the loose reading also deref this
for t in sorted(set(loose_targets) - set(adj_targets)):
    fa, fm, _, _ = first_this_touch(t, args=1)
    info("claim1/2 NOTE: extra loose-reading target 0x%x first this-relative offset" % t,
         "+0x%X at 0x%x (%s %s, %s)"
         % (fa[1], fa[0], insns[idx_of[fa[0]]].mnemonic,
            insns[idx_of[fa[0]]].op_str, fa[2]))

# definitional caveat: for 0x724580 the expected value is a lea, not a dereference
for t in TARGETS:
    if first_mem_map[t][1] != EXPECT_FIRST[t]:
        info("claim2 NOTE: fn 0x%x expected 0x%X is formed by %s, not by a memory access"
             % (t, EXPECT_FIRST[t], first_addr_map[t][2]),
             "first real dereference = +0x%X at 0x%x (%s)"
             % (first_mem_map[t][1], first_mem_map[t][0], first_mem_map[t][2]))

# --------------------------------------------------------------------------
# CLAIM 3: no caller reads eax
# --------------------------------------------------------------------------
print()
EAX_ALIASES = set()
for r in (X86_REG_EAX,):
    for nm in ("eax", "ax", "al", "ah"):
        EAX_ALIASES.add(nm)


def eax_read(ins):
    try:
        ra, _ = ins.regs_access()
    except Exception:
        return False
    return any(md.reg_name(r) in EAX_ALIASES for r in ra)


def eax_written(ins):
    try:
        _, rw = ins.regs_access()
    except Exception:
        return False
    return any(md.reg_name(r) in EAX_ALIASES for r in rw)


callers = {t: [] for t in TARGETS}
for k, ins in enumerate(insns):
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_IMM:
        if ins.operands[0].imm in callers:
            callers[ins.operands[0].imm].append(k)

# raw E8 scan as an independent cross-check of the disasm-derived caller list
raw_e8 = {t: [] for t in TARGETS}
for p in range(len(text) - 4):
    if text[p] == 0xE8:
        rel = struct.unpack_from("<i", text, p + 1)[0]
        t = text_base + p + 5 + rel
        if t in raw_e8:
            raw_e8[t].append(text_base + p)
for t in TARGETS:
    check("claim3: caller list (disasm) == caller list (raw E8) for 0x%x" % t,
          [i.address for i in (insns[k] for k in callers[t])] == raw_e8[t],
          "disasm=%d rawE8=%d" % (len(callers[t]), len(raw_e8[t])))
    # completeness: no absolute dword reference to the target anywhere in the
    # file -> no vtable / function-pointer caller can exist, so E8 is exhaustive
    absrefs = raw.count(struct.pack("<I", t))
    check("claim3: fn 0x%x has no absolute dword reference in the file" % t,
          absrefs == 0, "occurrences=%d" % absrefs)
    # nuance: the callee does produce a value in AL, callers just ignore it.
    # For each ret, report the last instruction that wrote al/eax before it.
    body_end = {0x724730: 0x7248b1, 0x724580: 0x724730}.get(t, t + 0x10)
    alw = []
    for j in range(idx_of[t], idx_of[body_end]):
        ins = insns[j]
        if ins.mnemonic not in ("ret", "retf"):
            continue
        last = None
        for q in range(j - 1, max(idx_of[t] - 1, j - 40), -1):
            pv = insns[q]
            if pv.id == 0:
                continue
            try:
                _, rw = pv.regs_access()
            except Exception:
                continue
            if any(md.reg_name(r) in EAX_ALIASES for r in rw):
                last = pv
                break
        alw.append((ins.address, last.address if last else -1,
                    (last.mnemonic + " " + last.op_str) if last else "-"))
    if alw:
        info("claim3 NOTE: fn 0x%x last al/eax writer before each ret" % t,
             ", ".join("ret@0x%x <- 0x%x %s" % a for a in alw))

for t in TARGETS:
    print("  --- callers of 0x%x (%d) ---" % (t, len(callers[t])))
    nxt_reads = 0
    win_reads = 0
    for k in callers[t]:
        nx = insns[k + 1]
        nr = eax_read(nx)
        nxt_reads += nr
        # forward window: read before any write, stop at branch/call/ret
        win = False
        for j in range(k + 1, min(k + 16, len(insns))):
            ins = insns[j]
            if eax_read(ins):
                win = True
                break
            if eax_written(ins):
                break
            if ins.mnemonic.startswith("j") or ins.mnemonic in ("ret", "retf", "call"):
                break
        win_reads += win
        print("      0x%06x call 0x%x -> next 0x%06x %-8s %-28s eax:%s"
              % (insns[k].address, t, nx.address, nx.mnemonic, nx.op_str,
                 "READ" if nr else ("overwrite" if eax_written(nx) else "unused")))
    check("claim3: fn 0x%x immediate-next eax true reads == 0" % t, nxt_reads == 0,
          "measured=%d / %d callers" % (nxt_reads, len(callers[t])))
    check("claim3: fn 0x%x forward-window eax true reads == 0" % t, win_reads == 0,
          "measured=%d / %d callers" % (win_reads, len(callers[t])))

# --------------------------------------------------------------------------
# CLAIM 4: prologue bytes and first ret
# --------------------------------------------------------------------------
print()
for t in TARGETS:
    exp, n = EXPECT_PROLOGUE[t]
    off = t - text_base
    got = text[off:off + 8]
    check("claim4: fn 0x%x first %d prologue bytes" % (t, n),
          got[:n] == exp,
          "measured=%s expected=%s (first8=%s)"
          % (got[:n].hex(" "), exp.hex(" "), got.hex(" ")))
    print("      0x%06x %s  %s"
          % (t, got[:8].hex(" "),
             " ; ".join("%s %s" % (i.mnemonic, i.op_str)
                        for i in insns[idx_of[t]:idx_of[t] + 4])))
    k = idx_of[t]
    first_ret = None
    for j in range(k, min(k + 500, len(insns))):
        if insns[j].mnemonic in ("ret", "retf"):
            first_ret = insns[j]
            break
    exp_ret = EXPECT_RET[t]
    got_ret = None
    if first_ret is not None and first_ret.operands and first_ret.operands[0].type == X86_OP_IMM:
        got_ret = first_ret.operands[0].imm
    check("claim4: fn 0x%x first ret operand" % t, got_ret == exp_ret,
          "measured=%s at 0x%x (bytes %s) expected=%s"
          % ("ret" if got_ret is None else "ret %d" % got_ret,
             first_ret.address if first_ret else -1,
             first_ret.bytes.hex(" ") if first_ret else "-",
             "ret" if exp_ret is None else "ret %d" % exp_ret))
    # multiplicity of exits, informational only
    if t == 0x724730:
        end = 0x7248b1
    elif t == 0x724580:
        end = 0x724730
    else:
        end = t + 0x10
    rets = [(insns[j].address, insns[j].op_str)
            for j in range(idx_of[t], idx_of.get(end, idx_of[t] + 40))
            if insns[j].mnemonic in ("ret", "retf")]
    info("fn 0x%x all ret sites" % t,
         "%d -> %s" % (len(rets), ", ".join("0x%x ret %s" % (a, o) for a, o in rets)))

# background corroboration (not one of the four claims): the global has writers
print()
writers = []
refs = 0
for ins in insns:
    if ins.id == 0:
        continue
    try:
        ops = ins.operands
    except Exception:
        continue
    for o in ops:
        if o.type == X86_OP_MEM and o.mem.base == 0 and o.mem.index == 0 \
                and o.mem.disp == GLOBAL_VA:
            refs += 1
            if o.access & CS_AC_WRITE:
                writers.append((ins.address, ins.mnemonic, ins.op_str))
info("background: refs to [0x%x] in .text" % GLOBAL_VA, "%d" % refs)
info("background: writes to [0x%x]" % GLOBAL_VA,
     ", ".join("0x%x %s %s" % w for w in writers) if writers else "none")
check("background: the global does get written (zeroing is possible)",
      len(writers) > 0, "writers=%d" % len(writers))

# --------------------------------------------------------------------------
# crash-site corroboration
# --------------------------------------------------------------------------
print()
caddr, cbytes = EXPECT_CRASH
got = text[caddr - text_base:caddr - text_base + len(cbytes)]
check("crash site 0x%x bytes == mov eax,[ebp+0x250]" % caddr, got == cbytes,
      "measured=%s expected=%s" % (got.hex(" "), cbytes.hex(" ")))
check("crash instruction is the first this deref of 0x724730",
      first_mem_map[0x724730][0] == caddr and first_mem_map[0x724730][1] == 0x250,
      "first deref=0x%x +0x%X" % (first_mem_map[0x724730][0], first_mem_map[0x724730][1]))
check("0x724730 aliases this into ebp (mov ebp,ecx) before deref",
      insns[idx_of[0x724730] + 2].mnemonic == "mov"
      and insns[idx_of[0x724730] + 2].op_str.replace(" ", "") == "ebp,ecx",
      "insn@0x%x = %s %s" % (insns[idx_of[0x724730] + 2].address,
                             insns[idx_of[0x724730] + 2].mnemonic,
                             insns[idx_of[0x724730] + 2].op_str))

# except.txt stack dump lists 00654418 right after 006543B1, i.e. a return
# address of the frame that crashed. Check that it maps back onto one of the 7.
ret_addr = 0x654418
call_site = ret_addr - 5
is_caller = any(insns[k].address == call_site for k in callers[0x724730])
check("crash return address 0x%x - 5 is a call to 0x724730" % ret_addr, is_caller,
      "call site=0x%x" % call_site)
back = None
bucket = None
for r in adjacent + loose:
    if r["tgt"] == 0x724730 and r["call"] == call_site:
        back = r
        bucket = "adjacent" if r in adjacent else "non-adjacent"
check("that call site is fed by 'mov ecx,[0x887368]' with no intervening "
      "ecx-clobber and no flag guard", back is not None,
      "load site=0x%x, bucket=%s, gap=%d insns"
      % (back["site"] if back else -1, bucket,
         len(back["gap"]) if back else -1))
if back is not None:
    info("crash frame", "0x%x: mov ecx,[0x%x] ; %s ; 0x%x: call 0x724730 ; 0x%x: <return>"
         % (back["site"], GLOBAL_VA,
            " ; ".join("%s %s" % (g.mnemonic, g.op_str) for g in back["gap"]) or "(nothing)",
            call_site, ret_addr))
    info("crash frame NOTE",
         "this call site is NOT one of the 7 strictly-adjacent sites; the load "
         "and the call are separated by %d register-spill instruction(s)" % len(back["gap"]))

# --------------------------------------------------------------------------
# summary
# --------------------------------------------------------------------------
npass = sum(1 for c in CHECKS if c)
print()
print("checks passed: %d/%d" % (npass, len(CHECKS)))
if npass == len(CHECKS):
    print("RESULT: ALL PASS")
    raise SystemExit(0)
print("RESULT: HAS FAILURES")
for i, c in enumerate(CHECKS):
    if not c:
        print("  failed check #%d" % (i + 1))
raise SystemExit(1)
