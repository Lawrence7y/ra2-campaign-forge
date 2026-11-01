# -*- coding: utf-8 -*-
"""Final, exact address-taken audit.

Absolute esp tracking that RESOLVES callee cleanup from the callee's `ret imm16`
when uniform. Tracking stops (row marked partial) at the first instruction whose
esp effect cannot be resolved; leas located BEFORE that point remain comparable,
so the row is still usable (a hit before the poison point is valid evidence).

Reports:
  * rows fully tracked to the read point
  * rows partially tracked (poison point), with how many lea comparisons remain valid
  * same-slot (address-taken) hits
"""
import re
import struct

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
T = next(s for s in SEC if s["name"] == ".text")
TLO, THI = T["va"], T["va"] + T["rsz"]
tb = raw[T["rp"]:T["rp"] + T["rsz"]]
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
S = []
va = TLO
while va < THI:
    off = va - TLO
    hit = False
    for I in md.disasm(tb[off:off + 16], va, count=1):
        S.append(dict(va=I.address, sz=I.size, mn=I.mnemonic, op=I.op_str,
                      insn=I, bs=I.bytes.hex()))
        va += I.size
        hit = True
        break
    if not hit:
        va += 1
IX = {r["va"]: i for i, r in enumerate(S)}
CL = {}


def cleanup_of(target):
    if target in CL:
        return CL[target]
    if target not in IX:
        CL[target] = None
        return None
    sizes = set()
    j = IX[target]
    n = 0
    while j < len(S) and S[j]["va"] < target + 0x2000 and n < 12:
        if S[j]["mn"] == "ret":
            n += 1
            sizes.add(0 if not S[j]["op"].strip() else int(S[j]["op"], 0))
        j += 1
    CL[target] = sizes.pop() if len(sizes) == 1 else None
    return CL[target]


def flo(i):
    j = i - 1
    while j >= 0 and S[j]["mn"] != "ret":
        j -= 1
    return j + 1


src = open(GATE62, "r", encoding="utf-8").read()
ch = re.search(r"^CHAIN = \{(.*?)^\}", src, re.S | re.M).group(1)
rows = [(int(m.group(1), 16), m.group(2), m.group(3))
        for m in re.finditer(r'0x([0-9a-f]+): \("([a-z0-9\-]+)", "([^"]*)"\)', ch)]

full = part = 0
hits = []
pair_total = pair_valid = 0
for c, verdict, chain in rows:
    if verdict not in ("param-slot", "local-slot"):
        continue
    i = IX[c]
    lo = flo(i)
    wq = None
    for q in range(i - 1, lo - 1, -1):
        if S[q]["bs"] == chain.split(";")[-1]:
            wq = q
            break
    if wq is None:
        continue
    m = re.search(r"\[esp \+ (0x[0-9a-f]+)\]", S[wq]["op"])
    if not m:
        continue
    K = int(m.group(1), 16)
    esp = 0
    offs = {}
    valid_until = None      # instruction index after which esp is unknown
    for q in range(lo, i + 1):
        if valid_until is not None and q > valid_until:
            offs[S[q]["va"]] = None
            continue
        offs[S[q]["va"]] = esp
        R = S[q]
        mn, op = R["mn"], R["op"]
        if mn == "push":
            esp -= 4
        elif mn == "pop":
            esp += 4
        elif mn in ("sub", "add") and op.startswith("esp, "):
            t = op.split(", ", 1)[1]
            mm = re.match(r"^(0x[0-9a-f]+|\d+)$", t)
            if mm:
                v = int(mm.group(1), 0)
                esp += v if mn == "add" else -v
            else:
                valid_until = q
        elif mn == "lea" and op.startswith("esp, [esp + "):
            mm = re.match(r"esp, \[esp \+ (0x[0-9a-f]+|\d+)\]$", op)
            if mm:
                esp += int(mm.group(1), 0)
            else:
                valid_until = q
        elif mn in ("mov", "leave", "and", "or", "xor") and op.startswith("esp"):
            valid_until = q
        elif mn == "call":
            o = R["insn"].operands
            if o and o[0].type == CS_OP_IMM:
                cl = cleanup_of(o[0].imm)
                if cl is None:
                    valid_until = q
                else:
                    esp += cl
            else:
                valid_until = q
    if offs[S[wq]["va"]] is not None:
        full += 1
    else:
        part += 1
    abs_slot = None if offs[S[wq]["va"]] is None else offs[S[wq]["va"]] + K
    for q in range(lo, wq):
        R = S[q]
        if R["mn"] != "lea":
            continue
        mm = re.search(r"\[esp \+ (0x[0-9a-f]+)\]", R["op"].split(", ", 1)[-1])
        if not mm:
            continue
        pair_total += 1
        d = offs[R["va"]]
        if d is None or abs_slot is None:
            continue
        pair_valid += 1
        if d + int(mm.group(1), 16) == abs_slot:
            hits.append((c, verdict, R["va"], R["op"], S[wq]["va"], K))

print("param/local rows: 55")
print("  fully esp-tracked to the read point:", full)
print("  partially tracked (esp poisoned by an unresolved call):", part)
print("lea-before-read pairs found:", pair_total, " pairs with usable abs offset:", pair_valid)
print("same-slot address-taken hits:", len(hits))
for h in hits:
    print("   %08X (%s) lea@%08X %r -> read@%08X [esp+0x%X]" % h)
