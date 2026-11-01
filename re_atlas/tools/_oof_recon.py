# -*- coding: utf-8 -*-
"""OOF recon (out-of-family reviewer, 2026-10-29). Self-written PE parse +
self-written linear decode + self-written pred/succ BFS. Does NOT import any
gate module: every number below is derived from gamemd.exe bytes on disk.
Only the CHAIN literal is regex-extracted from gate SOURCE TEXT (not executed).
"""
import hashlib
import re
import struct
import subprocess
import sys
from collections import Counter

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
GATE62 = r"D:\Project\ra2-campaign-forge\re_atlas\tools\r062_upward_trace_contract.py"
SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

raw = open(EXE, "rb").read()
b0 = hashlib.sha256(raw).hexdigest()
print("image sha256 =", b0, "MATCH" if b0 == SHA else "!!DRIFT!!")
if b0 != SHA:
    sys.exit(1)

e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]
optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", raw, opt + 28)[0]
ENTRY = IB + struct.unpack_from("<I", raw, opt + 16)[0]
tab = opt + optsz
SEC = []
for i in range(nsec):
    name = raw[tab + i * 40: tab + i * 40 + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i * 40 + 8)
    SEC.append(dict(name=name, va=IB + va, vsz=vsz, rp=rp, rsz=rsz))
print("ImageBase=%08X ENTRY=%08X" % (IB, ENTRY))
for s in SEC:
    print("  sec %-8s va=[%08X,%08X) vsz=%X raw=[%06X,%06X) rsz=%X" %
          (s["name"], s["va"], s["va"] + s["vsz"], s["vsz"], s["rp"],
           s["rp"] + s["rsz"], s["rsz"]))

TEXT = next(s for s in SEC if s["name"] == ".text")
TLO = TEXT["va"]
THI = TEXT["va"] + TEXT["rsz"]
tb = raw[TEXT["rp"]:TEXT["rp"] + TEXT["rsz"]]
print("text va=[%08X,%08X)" % (TLO, THI))


def rd(va, n):
    for s in SEC:
        if s["va"] <= va < s["va"] + s["vsz"]:
            off = s["rp"] + (va - s["va"])
            if off + n <= s["rp"] + s["rsz"]:
                return raw[off:off + n]
            return None
    return None


def fileoff(va):
    for s in SEC:
        if s["va"] <= va < s["va"] + s["vsz"]:
            return s["rp"] + (va - s["va"]), s["rp"] + s["rsz"], s["name"]
    return None, None, None


# ---------------- self-written linear decode of .text ----------------------
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM  # noqa

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
stream = []
va = TLO
while va < THI:
    off = va - TLO
    got = False
    for insn in md.disasm(tb[off:off + 16], va, count=1):
        tgt = None
        for o in insn.operands:
            if o.type == CS_OP_IMM:
                tgt = o.imm
        stream.append((insn.address, insn.size, insn.bytes.hex(),
                       insn.mnemonic, insn.op_str, tgt))
        va += insn.size
        got = True
        break
    if not got:
        va += 1
insns = {insn[0]: k for k, insn in enumerate(stream)}
print("decoded instructions:", len(stream))

heads = set()
callers = {}
for a, sz, bs, mn, op, tgt in stream:
    if mn == "call" and tgt is not None and TLO <= tgt < THI:
        heads.add(tgt)
        callers.setdefault(tgt, []).append(a)
heads.add(ENTRY)
print("aligned E8 heads (call targets in .text + entry):", len(heads))

# ---- graph in index space ----
succ = [[] for _ in range(len(stream))]
pred = [[] for _ in range(len(stream))]
for k, (a, sz, bs, mn, op, tgt) in enumerate(stream):
    nxt = a + sz
    outs = []
    if mn == "ret":
        outs = []
    elif mn == "jmp" and tgt is not None and TLO <= tgt < THI:
        outs = [tgt]
    elif mn.startswith("j") and tgt is not None and TLO <= tgt < THI:
        outs = [tgt, nxt]
    elif mn == "jmp":
        outs = []
    else:
        outs = [nxt]
    for t in outs:
        if t in insns:
            succ[k].append(insns[t])
            pred[insns[t]].append(k)


def bfs(start_k, adj):
    seen = {start_k}
    stack = [start_k]
    while stack:
        k = stack.pop()
        for p in adj[k]:
            if p not in seen:
                seen.add(p)
                stack.append(p)
    return seen


def back_reach(site):
    if site not in insns:
        return set()
    return {stream[k][0] for k in bfs(insns[site], pred)}


def fwd_closure(head):
    if head not in insns:
        return set()
    return {stream[k][0] for k in bfs(insns[head], succ)}


HOST_OF = {0x527750: 0x5276d0, 0x5279bd: 0x527920, 0x527d5b: 0x527cc0,
           0x527fd1: 0x527f20, 0x5282a0: 0x528220, 0x528450: 0x5283d0,
           0x528aa7: 0x528a10, 0x528cb7: 0x528c00, 0x528f97: 0x528f00,
           0x5291f3: 0x529160, 0x5293e3: 0x529394, 0x52966e: 0x5295f0,
           0x52a7de: 0x52a760}
EXPECT_CNT = {0x5276d0: 757, 0x527920: 2, 0x527cc0: 5, 0x527f20: 7,
              0x528220: 1, 0x5283d0: 306, 0x528a10: 650, 0x528c00: 67,
              0x528f00: 5, 0x529160: 3, 0x529394: 0, 0x5295f0: 651,
              0x52a760: 3}

print("\n== 13 hosts: back_reach(site) INTERSECT heads ; fwd_closure(host) contains site ; caller totals ==")
allok = True
for site in sorted(HOST_OF):
    host = HOST_OF[site]
    br = back_reach(site)
    inter = br & heads
    fwd = fwd_closure(host)
    cnt = len(callers.get(host, []))
    okc = cnt == EXPECT_CNT[host]
    # 0x529394 is the COLD non-E8 head: book/pin say the E8-head set is EMPTY
    # there (that is the point of the cold-entry row), all others singleton.
    okh = (inter == set()) if host == 0x529394 else (inter == {host})
    okf = site in fwd
    allok &= okc and okh and okf
    print("  site %08X host %08X | heads_in_backreach=%s %s | callers=%d/%d %s | site_in_fwd=%s | |br|=%d |fwd|=%d"
          % (site, host, sorted("%08X" % x for x in inter), "OK" if okh else "MISMATCH",
             cnt, EXPECT_CNT[host], "OK" if okc else "MISMATCH", okf, len(br), len(fwd)))

# --- C1
print("\n== C1  0x5283D0 ==")
br = back_reach(0x528450)
inter = br & heads
print("   back_reach(0x528450) INTERSECT E8heads =", sorted("%08X" % x for x in inter))
print("   == {0x5283D0}:", inter == {0x5283d0})
print("   callers via decode stream:", len(callers.get(0x5283d0, [])))
print("   head 6 bytes:", rd(0x5283d0, 6).hex())
n = 0
hits = []
for k in range(0, len(tb) - 5):
    if tb[k] == 0xE8:
        rel = struct.unpack_from("<i", tb, k + 1)[0]
        a = TLO + k
        if a + 5 + rel == 0x5283d0:
            n += 1
            hits.append(a)
print("   raw E8 byte-scan resolving to 0x5283D0:", n)
print("   decode-stream caller count equals raw scan:", n == len(callers.get(0x5283d0, [])))

# --- C2
print("\n== C2  0x5275CC ==")
print("   bytes@0x5275CC =", rd(0x5275cc, 4).hex(), " == 8bf1:", rd(0x5275cc, 2).hex() == "8bf1")
for insn in md.disasm(rd(0x5275cc, 2), 0x5275cc, count=1):
    print("   disasm:", insn.mnemonic, insn.op_str)
br2 = back_reach(0x527750)
print("   in back_reach(0x527750):", 0x5275cc in br2)
print("   0x5275CC < host head 0x5276D0:", 0x5275cc < 0x5276d0)
for sp, st in ((0x527b97, 0x527d5b), (0x528df2, 0x528f97), (0x52a623, 0x52a7de)):
    print("   spill %08X bytes=%s in back_reach(%08X)=%s" % (sp, rd(sp, 2).hex(), st, sp in back_reach(st)))

# --- C3
print("\n== C3  0x7787C0 ==")
got = rd(0x7787c0, 8).hex()
print("   bytes@0x7787C0 =", got, " == c7442438041b7e00:", got == "c7442438041b7e00")
for insn in md.disasm(rd(0x7787c0, 8), 0x7787c0, count=1):
    print("   disasm:", insn.mnemonic, insn.op_str)
for a in (0x779bb3, 0x779e33):
    print("   %08X =" % a, rd(a, 8).hex())
    for insn in md.disasm(rd(a, 8), a, count=1):
        print("      disasm:", insn.mnemonic, insn.op_str)

# --- C4
print("\n== C4  RTTI walk [0x7E1B00] ==")
vft = rd(0x7E1B00, 4)
print("   [0x7E1B00] =", vft.hex() if vft else None)
col = struct.unpack("<I", vft)[0]
print("   COL  = %08X" % col)
td = struct.unpack("<I", rd(col + 0xC, 4))[0]
print("   TD   = %08X ([COL+0xC])" % td)
nm = rd(td + 8, 32).split(b"\0")[0].decode("latin1")
print("   name = %r == '.?AVGenericList@@': %s" % (nm, nm == ".?AVGenericList@@"))
ti = struct.unpack("<I", rd(td + 4, 4))[0]
print("   TD+4 = %08X (type_info ptr or 0)" % ti)
tin = rd(ti + 8, 24) if ti else None
if tin:
    print("   type_info name = %r" % tin.split(b"\0")[0].decode("latin1"))
ctl = rd(0x8174C8, 4)
print("   [0x8174C8] =", ctl.hex() if ctl else None, "expect 94957f00(dword 0x7F9594)")
print("   0x8174D0 name =", rd(0x8174D0, 32).split(b"\0")[0].decode("latin1"))

# --- C5
print("\n== C5  0xB7882C disk-backed? ==")
fo, rawend, sname = fileoff(0xB7882C)
print("   fileoff =", hex(fo) if fo is not None else None, "raw end of section =",
      hex(rawend) if rawend else None, "section =", sname)
print("   beyond raw:", (fo is None) or (fo >= rawend))
print("   rd(0xB7882C,4) is None:", rd(0xB7882C, 4) is None)
print("   file size = %d (0x%X)" % (len(raw), len(raw)))

# --- C6
print("\n== C6  88-row histogram + CHAIN vs --dump ==")
p = subprocess.run([sys.executable, GATE62, "--dump"], capture_output=True, text=True)
print("   --dump exit:", p.returncode)
dump = {}
for line in p.stdout.splitlines():
    line = line.strip()
    if line.startswith("0x") and ': (' in line:
        k, rest = line.split(":", 1)
        v = rest.strip().rstrip(",").strip()
        verdict, chain = v[1:-1].split(", ")
        dump[int(k, 16)] = (verdict.strip('"'), chain.strip('"'))
print("   dump rows:", len(dump))
hist = Counter(v for v, _ in dump.values())
print("   histogram:", dict(sorted(hist.items())))
print("   sum =", sum(hist.values()))
src = open(GATE62, "r", encoding="utf-8").read()
m = re.search(r"^CHAIN = \{(.*?)^\}", src, re.S | re.M)
chainlit = {}
for mm in re.finditer(r'0x([0-9a-f]+): \("([a-z0-9\-]+)", "([^"]*)"\)', m.group(1)):
    chainlit[int(mm.group(1), 16)] = (mm.group(2), mm.group(3))
print("   CHAIN literal rows (regex from source text):", len(chainlit))
print("   key sets equal:", set(chainlit) == set(dump))
diff = [(k, chainlit[k], dump[k]) for k in sorted(set(chainlit) & set(dump)) if chainlit[k] != dump[k]]
print("   row-by-row diffs:", len(diff), diff[:3])

print("\n   chain step-1 bytes present in [call-16, call):")
bad = 0
for k, (v, ch) in sorted(dump.items()):
    if not ch:
        continue
    win = rd(k - 16, 16)
    if win is None or bytes.fromhex(ch.split(";")[0]) not in win:
        bad += 1
        print("     MISS", hex(k), ch)
print("   misses:", bad, "/", len(dump))
print("\n   stack-object rows:", hist.get("stack-object"))
print("ALL-13-OK:", allok)
