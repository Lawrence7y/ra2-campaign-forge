# -*- coding: utf-8 -*-
"""OOF independent check of the "5 with in-frame vptr store / 12 bare" split,
the lea-adjacency count, and the 6 global [+8] zeroing stores.
Self-written scan; does not import the gates.
"""
import re
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
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
        S.append(dict(va=insn.address, sz=insn.size, mn=insn.mnemonic,
                      op=insn.op_str, tgt=tgt))
        va += insn.size
        hit = True
        break
    if not hit:
        va += 1
IX = {r["va"]: i for i, r in enumerate(S)}

callers = {}
for r in S:
    if r["mn"] == "call" and r["tgt"] and TLO <= r["tgt"] < THI:
        callers.setdefault(r["tgt"], []).append(r["va"])

# the 17 stack-object rows for host 0x528C00, taken from --dump-equivalent set
STACK_ROWS = [0x5cefc9, 0x5cf10e, 0x5cf162, 0x5cf284, 0x5cf2e0, 0x5cf42c,
              0x5cf4c7, 0x5d76a9, 0x76c555, 0x77884f, 0x77890c, 0x778956,
              0x778bcf, 0x778dd1, 0x778e24, 0x779c3d, 0x779ebd]
print("stack rows listed:", len(STACK_ROWS))
print("all are callers of 0x528C00:", all(r in callers.get(0x528c00, []) for r in STACK_ROWS))


def frame_lo(i):
    j = i - 1
    while j >= 0 and S[j]["mn"] != "ret":
        j -= 1
    return j + 1


print("\n== per-row: lea slot, in-frame writes to that slot ==")
n_lea_adj = 0
n_with_vptr = 0
n_bare = 0
for r in STACK_ROWS:
    i = IX[r]
    prev = S[i - 1]
    m = re.match(r"^ecx, \[esp \+ (0x[0-9a-f]+)\]$", prev["op"])
    slot = m.group(1) if m else None
    adj = prev["mn"] == "lea" and slot is not None
    n_lea_adj += adj
    lo = frame_lo(i)
    pat = re.compile(r"^dword ptr \[esp \+ %s\], " % re.escape(slot))
    writes = [(S[q]["va"], S[q]["op"]) for q in range(lo, i) if S[q]["mn"] == "mov" and pat.match(S[q]["op"])]
    vptr = [w for w in writes if "0x7e1b04" in w[1]]
    if vptr:
        n_with_vptr += 1
    else:
        n_bare += 1
    print("  %08X lea_adj=%s slot=%s in-frame writes=%d vptrstore=%s %s"
          % (r, adj, slot, len(writes), bool(vptr),
             ["%08X:%s" % w for w in writes][:3]))
print("\nlea-adjacent:", n_lea_adj, "/", len(STACK_ROWS))
print("with in-frame vptr store:", n_with_vptr)
print("bare (zero in-frame dword writes to slot):", n_bare)

# ---- 6 global [+8] direct stores: mov [imm32], reg  (opcode 89 /r with modrm 05)
print("\n== global [+8] direct mov [imm32],reg stores (scan all sections) ==")
G8 = {0x887188, 0x887210, 0x887130, 0x887060, 0x8870C8, 0x89F520}
hits = []
for k in range(len(tb) - 6):
    if tb[k] == 0x89 and tb[k + 1] == 0x05:
        imm = struct.unpack_from("<I", tb, k + 2)[0]
        if imm in G8:
            hits.append((TLO + k, imm))
print("  mov [imm32],reg hits on G+8:", len(hits), [("%08X->%08X" % h) for h in hits])
for a, imm in hits:
    for insn in md.disasm(tb[a - TLO:a - TLO + 6], a, count=1):
        print("     %08X %s %s" % (a, insn.mnemonic, insn.op_str))
# also c7 05 form
hits2 = []
for k in range(len(tb) - 10):
    if tb[k] == 0xC7 and tb[k + 1] == 0x05:
        imm = struct.unpack_from("<I", tb, k + 2)[0]
        if imm in G8:
            hits2.append((TLO + k, imm))
print("  mov dword [imm32],imm32 hits on G+8:", len(hits2))
