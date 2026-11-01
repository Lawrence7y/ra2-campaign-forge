# -*- coding: utf-8 -*-
"""Address-taken audit, computed as a RELATIVE esp delta between the lea point
and the point where the `this` value is read -- this needs no callee-cleanup
knowledge as long as no call sits between the two points. Rows with an
intervening call are reported separately (UNRESOLVED-REL), and the absolute
variant is only attempted when every intervening callee has a single uniform
`ret imm16`.

Purpose: decide whether the C report's "0/55 lea address-taken" is a real zero
or a vacuous one (its code skips the comparison when capstone renders the
memory operand as `dword ptr [esp + X]`, i.e. always).
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


def flo(i):
    j = i - 1
    while j >= 0 and S[j]["mn"] != "ret":
        j -= 1
    return j + 1


def cleanup_of(target):
    if target not in IX:
        return None
    sizes = set()
    j = IX[target]
    n = 0
    while j < len(S) and S[j]["va"] < target + 0x1000 and n < 8:
        if S[j]["mn"] == "ret":
            n += 1
            sizes.add(0 if not S[j]["op"].strip() else int(S[j]["op"], 0))
        j += 1
    return sizes.pop() if len(sizes) == 1 else None


def delta_between(lo, a, b):
    """net esp change from instruction index a to b (exclusive), or None"""
    esp = 0
    calls = []
    poison = False
    for q in range(a, b):
        R = S[q]
        mn, op = R["mn"], R["op"]
        if mn == "push":
            esp -= 4
        elif mn == "pop":
            esp += 4
        elif mn in ("sub", "add") and op.startswith("esp, "):
            t = op.split(", ", 1)[1]
            if re.match(r"^(0x[0-9a-f]+|\d+)$", t):
                v = int(t, 0)
                esp += v if mn == "add" else -v
            else:
                poison = True
        elif mn == "lea" and op.startswith("esp, [esp + "):
            mm = re.match(r"esp, \[esp \+ (0x[0-9a-f]+|\d+)\]$", op)
            if mm:
                esp += int(mm.group(1), 0)
            else:
                poison = True
        elif mn in ("mov", "leave", "and", "or", "xor") and op.startswith("esp"):
            poison = True
        elif mn == "call":
            calls.append(R["va"])
    return esp, poison, calls


src = open(GATE62, "r", encoding="utf-8").read()
ch = re.search(r"^CHAIN = \{(.*?)^\}", src, re.S | re.M).group(1)
rows = [(int(m.group(1), 16), m.group(2), m.group(3))
        for m in re.finditer(r'0x([0-9a-f]+): \("([a-z0-9\-]+)", "([^"]*)"\)', ch)]

rel_hits, rel_clean, unresolved = [], 0, []
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
    for q in range(lo, wq):
        R = S[q]
        if R["mn"] != "lea":
            continue
        mm = re.search(r"\[esp \+ (0x[0-9a-f]+)\]", R["op"].split(", ", 1)[-1])
        if not mm:
            continue
        Kl = int(mm.group(1), 16)
        d, poison, calls = delta_between(lo, q, wq)
        if poison or calls:
            # try to resolve callee cleanup
            resolvable = (not poison)
            for cv in calls:
                o = S[IX[cv]]["insn"].operands
                if not o or o[0].type != CS_OP_IMM:
                    resolvable = False
                    break
                cl = cleanup_of(o[0].imm)
                if cl is None:
                    resolvable = False
                    break
                d += cl
            if not resolvable:
                unresolved.append((c, R["va"]))
                continue
        # same absolute slot iff (esp_lea + Kl) == (esp_w + K)  where esp_w = esp_lea + d
        if (Kl - K) == d:
            rel_hits.append((c, verdict, R["va"], R["op"], S[wq]["va"], K, Kl, d))

print("param/local rows: 55")
print("lea-vs-read comparisons resolved:", len(rel_hits) and None)
print("unresolved (intervening call with non-uniform cleanup):", len(unresolved))
print("SAME-SLOT address-taken hits:", len(rel_hits))
for h in rel_hits:
    print("  %08X (%s) lea@%08X %r -> read@%08X [esp+0x%X] leaK=0x%X delta=%d"
          % (h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7]))
