# -*- coding: utf-8 -*-
"""R16-FIX-B1-2ROWS : independent, read-only exploration of 0x7E1668 writes.
Only reads ra2youli/gamemd.exe (pefile fast_load + open rb) and audit starts.json.
Writes only stdout (captured to _explore_out.txt by caller).
"""
import io, os, sys, bisect, json
sys.dont_write_bytecode = True
IB = 0x400000
ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
STARTS = os.path.join(ROOT, "lead", "next_re_20261117_r14", "R16_AUDIT_D1_WIDE_B1", "starts.json")

import pefile, capstone

# ---- read-only PE image (same method as prior authoritative scripts) ----
with open(EXE, "rb") as fh:
    _ = fh.read(1)
pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    secs.append((IB + s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData,
                 s.get_data(), s.Name.rstrip(b"\x00").decode("latin-1")))
end = max(va + max(vs, rs) for va, vs, rs, _d, _n in secs)
buf = bytearray(end - IB + 16)
sec_of = {}
for va, vs, rs, d, nm in secs:
    buf[va - IB:va - IB + len(d)] = d
    for o in range(va - IB, va - IB + len(d)):
        sec_of[o] = nm
def u32(va):
    o = va - IB
    return int.from_bytes(buf[o:o+4], "little") if 0 <= o <= len(buf) - 4 else None
def cstr(va, n=256):
    o = va - IB
    if o < 0 or o >= len(buf): return None
    e = buf.find(b"\x00", o, min(o + n, len(buf)))
    return bytes(buf[o:e]).decode("latin-1", "replace") if e > 0 else None

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

def dis(va, n):
    return list(md.disasm(bytes(buf[va - IB:va - IB + n]), va))

def dis_one(va):
    r = list(md.disasm(bytes(buf[va - IB:va - IB + 16]), va, count=1))
    return r[0] if r else None

# ---- independent scan: find every 0x7E1668 imm32 write ----
# mov dword ptr [mem], imm32 => C7 /0 id ; imm little-endian = 68 16 7E 00
pat = bytes([0x68, 0x16, 0x7E, 0x00])
sites = []
for o in range(0, len(buf) - 4):
    if buf[o:o+4] != pat:
        continue
    va_end = IB + o + 4
    # try candidate starts 0..12 bytes before the immediate
    found = None
    for back in range(0, 13):
        s = IB + o - back
        if s < IB: continue
        ins = dis_one(s)
        if ins is None: continue
        if ins.address + ins.size != va_end: continue
        if ins.mnemonic != "mov": continue
        ops = ins.operands
        if len(ops) != 2: continue
        if ops[0].type != capstone.x86.X86_OP_MEM: continue
        if ops[1].type != capstone.x86.X86_OP_IMM: continue
        if ops[1].imm & 0xFFFFFFFF != 0x7E1668: continue
        found = (ins, s)
        break
    if found:
        ins, s = found
        mo = ins.operands[0].mem
        base = ins.reg_name(mo.base) if mo.base else ""
        idx = ins.reg_name(mo.index) if mo.index else ""
        sites.append(dict(site=s, bytes=ins.bytes.hex(), mnem=ins.mnemonic,
                          opstr=ins.op_str, base=base, index=idx, disp=mo.disp,
                          seg=(ins.reg_name(mo.segment) if mo.segment else ""),
                          sec=sec_of.get(s - IB, "?")))
    else:
        sites.append(dict(site=IB + o - 4, bytes="UNDECODED", mnem="?", opstr="?",
                          base="?", index="?", disp=0, seg="", sec=sec_of.get(o-4, "?")))

sites.sort(key=lambda x: x["site"])
from collections import Counter
print("SCAN total 0x7E1668 imm writes =", len(sites))
print("base breakdown =", dict(Counter(x["base"] for x in sites)))
print("section breakdown =", dict(Counter(x["sec"] for x in sites)))
nonstack = [x for x in sites if x["base"] not in ("esp", "ebp")]
print("NONSTACK count =", len(nonstack))
for x in nonstack:
    print("  %08X  %s  %s %s  base=%s idx=%s disp=0x%x sec=%s" %
          (x["site"], x["bytes"], x["mnem"], x["opstr"], x["base"], x["index"], x["disp"] & 0xFFFFFFFF, x["sec"]))

# ---- enclosing function using starts.json ----
sj = json.load(io.open(STARTS, encoding="utf-8"))
atlas = {int(k, 16): v for k, v in sj["atlas"].items()}
allst = sorted(set(atlas) | set(sj["targets"]))
def enclosing(va):
    i = bisect.bisect_right(allst, va) - 1
    for j in range(i, max(-1, i - 12), -1):
        s = allst[j]
        insn = dis(s, va - s + 16)
        if not insn or not any(x.address == va for x in insn): continue
        if any(x.mnemonic in ("ret", "retf") for x in insn if x.address < va): continue
        return s
    for back in range(1, 0x41):
        s = va - back
        p = s - 1
        npad = 0
        while p > 0x401000 and buf[p - IB] in (0x90, 0xCC):
            npad += 1; p -= 1
        if npad == 0 or buf[p - IB] not in (0xC3, 0xC2, 0xCC): continue
        insn = dis(s, va - s + 16)
        if insn and any(x.address == va for x in insn) and \
           not any(x.mnemonic in ("ret", "retf") for x in insn if x.address < va):
            return s
    return None

print("\n=== NONSTACK sites with enclosing host ===")
for x in nonstack:
    print("  site=%08X op=[%s] host=%s" %
          (x["site"], x["opstr"], ("%08X" % enclosing(x["site"])) if enclosing(x["site"]) else "None"))

# ---- dump key functions ----
def dump(start, label, lo=None, hi=None):
    print("\n=== %s @ %08X ===" % (label, start))
    insn = dis(start, 0x200)
    for x in insn:
        if lo is not None and x.address < lo: continue
        if hi is not None and x.address > hi: break
        print("   %08X: %-10s %-20s ; %s" % (x.address, x.mnemonic, x.op_str, x.bytes.hex()))

for st, lb in ((0x004011C0, "FAIL host 004011C0 head"),
               (0x00401480, "FAIL host 004011C0 tail around site"),
               (0x004019A0, "scalar deleting dtor 004019A0"),
               (0x0047A9D0, "ctor cand 0047A9D0"),
               (0x0047AA00, "ctor cand 0047AA00"),
               (0x0047AA30, "ctor cand 0047AA30"),
               (0x00535A60, "other site 00535A8A host region"),
               (0x00697A20, "other site 00697A47 host region"),
               (0x00759510, "other site 00759532 host region")):
    if lb.find("tail") >= 0:
        dump(st, lb, 0x00401480, 0x004014F0)
    else:
        dump(st, lb, st, st + 0x60)
