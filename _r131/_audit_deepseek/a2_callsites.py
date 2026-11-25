#!/usr/bin/env python3
# Task A: call-site census by three independent methods.
import struct, sys, re
import capstone

PATH = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
IMGBASE = 0x400000
data = open(PATH, "rb").read()

def u16(o): return struct.unpack_from("<H", data, o)[0]
def u32(o): return struct.unpack_from("<I", data, o)[0]

e_lfanew = u32(0x3C)
coff = e_lfanew + 4
nsec = u16(coff + 2)
optsz = u16(coff + 16)
opt = coff + 20
sectab = opt + optsz
secs = []
for i in range(nsec):
    o = sectab + i * 40
    name = data[o:o+8].rstrip(b"\0").decode("latin1")
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o+8)
    secs.append(dict(name=name, vsize=vsize, vaddr=vaddr, rawsize=rawsize, rawptr=rawptr))

text = [s for s in secs if s["name"] == ".text"][0]
TEXT_VA = IMGBASE + text["vaddr"]
TEXT_END = TEXT_VA + text["rawsize"]
blob = data[text["rawptr"]:text["rawptr"] + text["rawsize"]]
print(f".text VA={TEXT_VA:#x} END={TEXT_END:#x} rawlen={len(blob)}")

TARGETS = (0x6bedb0, 0x41c250)

# ---------- Method 1/2: capstone linear disasm, disasm_lite (streaming) ----------
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False   # keep memory flat: no per-insn operand objects retained

imm_re = re.compile(r"^(0x[0-9a-fA-F]+|-?[0-9]+)$")

def parse_imm(s):
    """Accept both capstone hex form (0x...) and plain decimal."""
    s = s.strip()
    if not imm_re.match(s):
        return None
    try:
        return int(s, 16) if s.lower().startswith(("0x", "-0x")) else int(s, 10)
    except ValueError:
        return None

calls = {t: [] for t in TARGETS}
total_insn = 0
nondis = 0
last = TEXT_VA
for (addr, size, mnem, op_str) in md.disasm_lite(blob, TEXT_VA):
    total_insn += 1
    last = addr + size
    if mnem == "call":
        v = parse_imm(op_str)
        if v in calls:
            calls[v].append((addr, op_str))

print("total_insn", total_insn, "max_end", hex(last), "gap_to_end", TEXT_END - last)
for t in TARGETS:
    print(f"[capstone] target {t:#x} count={len(calls[t])}")
    for a, os_ in calls[t]:
        print(f"   site {a:#x}  op_str={os_!r}")

# sanity: confirm parser really handles both notations on the same data
sample = {}
cnt = 0
for (addr, size, mnem, op_str) in md.disasm_lite(blob, TEXT_VA):
    if mnem == "call" and op_str.startswith("0x"):
        sample.setdefault("hexform", op_str)
        cnt += 1
print("call-with-0x-form sample:", sample.get("hexform"), "count", cnt)

# ---------- Method 3: raw 0xE8 scan ----------
raw_hits = {t: [] for t in TARGETS}
all_e8 = 0
for i in range(len(blob) - 4):
    if blob[i] == 0xE8:
        all_e8 += 1
        rel = struct.unpack_from("<i", blob, i + 1)[0]
        site = TEXT_VA + i
        tgt = (site + 5 + rel) & 0xFFFFFFFF
        if tgt in raw_hits:
            raw_hits[tgt].append(site)
print("raw 0xE8 occurrences in .text:", all_e8)
for t in TARGETS:
    print(f"[raw-E8] target {t:#x} count={len(raw_hits[t])}")
    for a in raw_hits[t]:
        print(f"   site {a:#x}")

# ---------- diff ----------
for t in TARGETS:
    cs = sorted(a for a, _ in calls[t])
    rw = sorted(raw_hits[t])
    print(f"target {t:#x}: capstone={len(cs)} raw={len(rw)} equal_sets={cs == rw}")
    if cs != rw:
        print("  only-capstone", [hex(x) for x in set(cs) - set(rw)])
        print("  only-raw", [hex(x) for x in set(rw) - set(cs)])
