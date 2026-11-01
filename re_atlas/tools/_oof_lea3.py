# -*- coding: utf-8 -*-
"""Exact esp tracking with callee stack-cleanup resolved from the callee's `ret imm16`.

For each param-slot/local-slot row:
  * walk the frame from the previous `ret` to the call site;
  * maintain esp exactly: push/pop/sub/add esp, lea esp; `call T` adds back the
    callee's `ret N` cleanup (N bytes) -- read from the callee's ret sites;
  * if a callee has mixed/unknown cleanup or is an indirect call, mark the row
    AMBIGUOUS and stop tracking there;
  * compare the absolute offset of the slot the `this` value is read from with
    every `lea reg,[esp+K]` in the frame.

Output: exact rows, ambiguous rows, and rows with a genuine address-taken hit.
"""
import re
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM

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
    """bytes popped by the callee on return, or None if not uniform/decidable"""
    if target not in IX:
        return None
    i = IX[target]
    # scan forward up to 0x2000 bytes / next 40 rets for `ret`/`ret imm`
    sizes = set()
    n = 0
    j = i
    while j < len(S) and S[j]["va"] < target + 0x2000 and n < 40:
        if S[j]["mn"] == "ret":
            n += 1
            op = S[j]["op"]
            sizes.add(0 if not op.strip() else int(op, 0))
            # continue scanning (other exits)
        j += 1
    if not sizes:
        return None
    if len(sizes) == 1:
        return sizes.pop()
    # mixed: accept only if the *first* ret is the dominant one
    return None


src = open(GATE62, "r", encoding="utf-8").read()
ch = re.search(r"^CHAIN = \{(.*?)^\}", src, re.S | re.M).group(1)
rows = [(int(m.group(1), 16), m.group(2), m.group(3))
        for m in re.finditer(r'0x([0-9a-f]+): \("([a-z0-9\-]+)", "([^"]*)"\)', ch)]

n_exact = n_amb = 0
taken = []
checked = 0
for c, verdict, chain in rows:
    if verdict not in ("param-slot", "local-slot"):
        continue
    i = IX[c]
    lo = flo(i)
    steps = chain.split(";")
    wq = None
    for q in range(i - 1, lo - 1, -1):
        if S[q]["bs"] == steps[-1]:
            wq = q
            break
    if wq is None:
        continue
    m = re.search(r"\[esp \+ (0x[0-9a-f]+)\]", S[wq]["op"])
    if not m:
        continue
    K = int(m.group(1), 16)
    checked += 1
    esp = 0
    offs = {}
    ok = True
    for q in range(lo, i + 1):
        R = S[q]
        offs[R["va"]] = esp
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
                ok = False
                break
        elif mn == "lea" and op.startswith("esp, [esp + "):
            mm = re.match(r"esp, \[esp \+ (0x[0-9a-f]+|\d+)\]$", op)
            if mm:
                esp += int(mm.group(1), 0)
            else:
                ok = False
                break
        elif mn in ("mov", "leave", "and", "or", "xor") and op.startswith("esp"):
            ok = False
            break
        elif mn == "call":
            o = R["insn"].operands
            if not o or o[0].type != CS_OP_IMM:
                ok = False
                break
            cl = cleanup_of(o[0].imm)
            if cl is None:
                ok = False
                break
            esp += cl
    if not ok:
        n_amb += 1
        continue
    n_exact += 1
    abs_slot = offs[S[wq]["va"]] + K
    hits = []
    for q in range(lo, i):
        R = S[q]
        if R["mn"] != "lea":
            continue
        mm = re.search(r"\[esp \+ (0x[0-9a-f]+)\]", R["op"].split(", ", 1)[-1])
        if not mm:
            continue
        if offs.get(R["va"]) is None:
            continue
        if offs[R["va"]] + int(mm.group(1), 16) == abs_slot:
            hits.append((R["va"], R["op"]))
    if hits:
        taken.append((c, verdict, S[wq]["va"], K, abs_slot, hits))

print("param/local rows:", checked)
print("exactly tracked:", n_exact, " ambiguous (indirect/mixed-cleanup call):", n_amb)
print("rows whose slot ADDRESS IS TAKEN by a frame lea:", len(taken))
for c, v, wva, K, ab, hits in taken:
    print("  %08X (%s) read@%08X [esp+0x%X] abs=%+d" % (c, v, wva, K, ab))
    for x in hits:
        print("        lea @%08X  %s" % x)
