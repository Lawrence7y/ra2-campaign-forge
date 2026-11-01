# -*- coding: utf-8 -*-
"""OOF audit: does any frame take the ADDRESS of the param-slot it passes as
`this` (i.e. `lea reg,[esp+slot]` naming the same absolute slot)?

The C report (§3) claims 0/55 for this. A naive esp-offset comparison is wrong
because push/sub esp shifts the frame; so this script tracks the esp delta
instruction by instruction and compares ABSOLUTE offsets relative to the esp at
function entry.
"""
import re
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM, CS_OP_REG

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
        S.append(dict(va=I.address, sz=I.size, mn=I.mnemonic, op=I.op_str, insn=I,
                      bs=I.bytes.hex()))
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


src = open(GATE62, "r", encoding="utf-8").read()
chain = re.search(r"^CHAIN = \{(.*?)^\}", src, re.S | re.M).group(1)
rows = [(int(m.group(1), 16), m.group(2), m.group(3))
        for m in re.finditer(r'0x([0-9a-f]+): \("([a-z0-9\-]+)", "([^"]*)"\)', chain)]


def insn_at_bytes(lo, hi, hexs):
    """find last instruction in [lo,hi) whose bytes == hexs"""
    out = None
    for q in range(lo, hi):
        if S[q]["bs"] == hexs:
            out = q
    return out


print("== esp-delta tracked address-of-slot audit ==")
aud = 0
hits = []
for c, verdict, ch in rows:
    if verdict not in ("param-slot", "local-slot"):
        continue
    i = IX[c]
    lo = flo(i)
    last = ch.split(";")[-1]
    q = insn_at_bytes(lo, i, last)
    if q is None:
        print("  ?? writer bytes %s not found in frame of %08X" % (last, c))
        continue
    m = re.search(r"\[esp \+ (0x[0-9a-f]+)\]", S[q]["op"])
    if not m:
        continue
    slot_w = int(m.group(1), 16)
    aud += 1
    # ---- compute esp delta before each instruction in the frame ----
    esp = 0
    abs_of = {}
    deffs = {}
    for r in range(lo, i):
        R = S[r]
        deffs[R["va"]] = esp
        mn, op = R["mn"], R["op"]
        # effects: only account instructions that change esp deterministically
        if mn == "push":
            esp -= 4
        elif mn == "pop":
            esp += 4
        elif mn in ("sub", "add") and op.startswith("esp, "):
            try:
                v = int(op.split(", ")[1], 0)
            except ValueError:
                v = None
            if v is not None:
                esp += v if mn == "add" else -v
        elif mn == "lea" and op.startswith("esp, [esp + "):
            try:
                esp += int(op.split("[esp + ")[1].rstrip("]"), 16)
            except ValueError:
                pass
        elif mn == "mov" and op.startswith("esp, "):
            # mov esp,ebp / mov esp,imm -- frame restore; reset
            esp = None
        elif mn == "call":
            pass  # cdecl: caller restores; assume balanced
    abs_w = None if deffs.get(S[q]["va"]) is None else deffs[S[q]["va"]] + slot_w
    leas = []
    for r in range(lo, i):
        R = S[r]
        if R["mn"] != "lea":
            continue
        mm = re.search(r"\[esp \+ (0x[0-9a-f]+)\]", R["op"].split(", ", 1)[-1])
        if not mm:
            continue
        off = int(mm.group(1), 16)
        d = deffs.get(R["va"])
        if d is None:
            continue
        if abs_w is not None and d + off == abs_w:
            leas.append((R["va"], R["op"]))
    if leas:
        hits.append((c, verdict, slot_w, abs_w, leas))
print("param-slot/local-slot rows audited:", aud)
print("rows where the SAME absolute slot is addressed by a frame lea:", len(hits))
for h in hits:
    print("   %08X (%s) slot=esp+0x%X abs=%s" % (h[0], h[1], h[2], h[3]))
    for x in h[4]:
        print("        lea @%08X %s" % x)
