# -*- coding: utf-8 -*-
"""Precise esp-delta tracking for the param-slot 'address taken' question.

For every param-slot/local-slot row, compute:
  - the ABSOLUTE offset (relative to the esp at function entry) of the slot that
    the `this` value is read from;
  - every `lea reg,[esp+K]` in the frame whose ABSOLUTE offset equals it.
esp is tracked instruction by instruction; if any instruction makes esp
unknowable (mov esp,... / add esp,reg / leave) the rest of the frame is skipped.

Also recomputes the C report's stated audit exactly as written in _crev_engine.py
to show whether its 0/55 result is a real zero or a vacuous one.
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


def esp_deltas(lo, hi):
    """map va -> esp offset relative to frame entry, or None when unknown"""
    d = {}
    esp = 0
    for q in range(lo, hi + 1):
        R = S[q]
        d[R["va"]] = esp
        mn, op = R["mn"], R["op"]
        if esp is None:
            continue
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
                esp = None
        elif mn == "lea" and op.startswith("esp, [esp + "):
            m = re.match(r"esp, \[esp \+ (0x[0-9a-f]+|\d+)\]$", op)
            if m:
                esp += int(m.group(1), 0)
            else:
                esp = None
        elif mn == "mov" and op.startswith("esp, "):
            esp = None          # frame restore / mov esp,ebp
        elif mn == "leave":
            esp = None
        elif mn in ("and", "or", "xor") and op.startswith("esp, "):
            esp = None
        elif mn == "call":
            pass                # assume cdecl balance
    return d


src = open(GATE62, "r", encoding="utf-8").read()
ch = re.search(r"^CHAIN = \{(.*?)^\}", src, re.S | re.M).group(1)
rows = [(int(m.group(1), 16), m.group(2), m.group(3))
        for m in re.finditer(r'0x([0-9a-f]+): \("([a-z0-9\-]+)", "([^"]*)"\)', ch)]

print("== precise address-taken audit (esp tracked) ==")
n_aud = 0
taken = []
slot_none = 0
for c, verdict, chain in rows:
    if verdict not in ("param-slot", "local-slot"):
        continue
    i = IX[c]
    lo = flo(i)
    steps = chain.split(";")
    # last step is the writer of the slot value
    wq = None
    for q in range(i - 1, lo - 1, -1):
        if S[q]["bs"] == steps[-1]:
            wq = q
            break
    if wq is None:
        print("  ?? writer bytes not found", hex(c), steps[-1])
        continue
    m = re.search(r"\[esp \+ (0x[0-9a-f]+)\]", S[wq]["op"])
    if not m:
        slot_none += 1
        continue
    K = int(m.group(1), 16)
    d = esp_deltas(lo, i)
    dw = d.get(S[wq]["va"])
    if dw is None:
        continue
    n_aud += 1
    abs_slot = dw + K
    hits = []
    for q in range(lo, i):
        R = S[q]
        if R["mn"] != "lea":
            continue
        mm = re.search(r"\[esp \+ (0x[0-9a-f]+)\]", R["op"].split(", ", 1)[-1])
        if not mm:
            continue
        dd = d.get(R["va"])
        if dd is None:
            continue
        if dd + int(mm.group(1), 16) == abs_slot:
            hits.append((R["va"], R["op"]))
    if hits:
        taken.append((c, verdict, S[wq]["va"], K, abs_slot, hits))

print("rows audited (esp known):", n_aud, " rows with no esp-based slot:", slot_none)
print("rows whose slot address IS taken by a frame lea:", len(taken))
for c, v, wva, K, ab, hits in taken:
    print("  %08X (%s) read@%08X [esp+0x%X] abs=%+d" % (c, v, wva, K, ab))
    for x in hits:
        print("        lea @%08X  %s" % x)

# ---- reproduce the C engine's audit verbatim ----
print("\n== reproduction of _crev_engine.py's E8 audit (as written) ==")
cnt = 0
for c, verdict, chain in rows:
    if verdict not in ("param-slot", "local-slot"):
        continue
    w = chain.split(";")
    srcstr = None
    # engine: w1[3] is the op_str right-hand side object
    for q in range(IX[c] - 1, flo(IX[c]) - 1, -1):
        if S[q]["bs"] == w[-1]:
            srcstr = None
            break
    # emulate startswith("[esp") test on the DISASSEMBLY text
    q = None
    for q2 in range(IX[c] - 1, flo(IX[c]) - 1, -1):
        if S[q2]["bs"] == w[-1]:
            q = q2
            break
    if q is None:
        continue
    rhs = S[q]["op"].split(", ", 1)[1]
    if not rhs.startswith("[esp"):
        cnt += 1
print("rows where capstone rhs does NOT start with '[esp' (=> C's slot=None, audit vacuous):",
      cnt, "of", sum(1 for _, v, _ in rows if v in ("param-slot", "local-slot")))
