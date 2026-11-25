#!/usr/bin/env python3
# Task A v2: linear sweep WITH resynchronisation.
# Why: md.disasm_lite() is a generator that stops permanently at the first
# undecodable byte. In v1 that happened at 0x46f5a0 (total_insn 155,215 only),
# so every call site above 0x46f5a0 was invisible -> 0x6bedb0 got 0 hits.
# Fix: on generator exhaustion, advance 1 byte past the last decoded address and
# restart. Record the skipped byte ranges so the report can state them.
import struct, re
import capstone

PATH = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
IMGBASE = 0x400000
data = open(PATH, "rb").read()
u16 = lambda o: struct.unpack_from("<H", data, o)[0]
u32 = lambda o: struct.unpack_from("<I", data, o)[0]

e_lfanew = u32(0x3C); coff = e_lfanew + 4
nsec = u16(coff + 2); optsz = u16(coff + 16); opt = coff + 20
sectab = opt + optsz
secs = []
for i in range(nsec):
    o = sectab + i * 40
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o+8)
    secs.append(dict(name=data[o:o+8].rstrip(b"\0").decode("latin1"),
                     vsize=vsize, vaddr=vaddr, rawsize=rawsize, rawptr=rawptr))
text = [s for s in secs if s["name"] == ".text"][0]
TEXT_VA = IMGBASE + text["vaddr"]
rawlen = text["rawsize"]
TEXT_END = TEXT_VA + rawlen
blob = data[text["rawptr"]:text["rawptr"]+rawlen]

TARGETS = (0x6bedb0, 0x41c250)
imm_re = re.compile(r"^(?:0[xX][0-9a-fA-F]+|[0-9]+)$")

def parse_imm(s):
    s = s.strip()
    if not imm_re.match(s):
        return None
    return int(s, 16) if s.lower().startswith("0x") else int(s, 10)

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False   # streaming only; never hold per-insn operand objects

calls = {t: [] for t in TARGETS}
total_insn = 0
skips = []          # (va, nbytes) of undecodable gaps
pos = 0
while pos < rawlen:
    progressed = False
    gen = md.disasm_lite(blob[pos:], TEXT_VA + pos)
    end_off = pos
    for (addr, size, mnem, op_str) in gen:
        progressed = True
        total_insn += 1
        end_off = addr - TEXT_VA + size
        if mnem == "call":
            v = parse_imm(op_str)
            if v in calls:
                calls[v].append((addr, size, op_str))
    if not progressed:
        # undecodable byte at pos: record single-byte skip and continue
        if skips and skips[-1][0] + skips[-1][1] == TEXT_VA + pos:
            skips[-1] = (skips[-1][0], skips[-1][1] + 1)
        else:
            skips.append((TEXT_VA + pos, 1))
        pos += 1
    else:
        if end_off <= pos:      # safety: no forward progress
            pos += 1
        else:
            pos = end_off

print("total_insn", total_insn)
print("skip_bytes_total", sum(n for _, n in skips), "skip_runs", len(skips))
print("skip_runs_first20", [(hex(a), n) for a, n in skips[:20]])
for t in TARGETS:
    print(f"[capstone-resync] target {t:#x} count={len(calls[t])}")
    for a, sz, os_ in calls[t]:
        print(f"   site {a:#x} len={sz} op_str={os_!r}")

# ---- raw 0xE8 scan ----
raw_hits = {t: [] for t in TARGETS}
all_e8 = 0
for i in range(rawlen - 4):
    if blob[i] == 0xE8:
        all_e8 += 1
        tgt = (TEXT_VA + i + 5 + struct.unpack_from("<i", blob, i+1)[0]) & 0xFFFFFFFF
        if tgt in raw_hits:
            raw_hits[tgt].append(TEXT_VA + i)
print("raw 0xE8 occurrences in .text:", all_e8)
for t in TARGETS:
    print(f"[raw-E8] target {t:#x} count={len(raw_hits[t])} sites={[hex(x) for x in raw_hits[t]]}")

for t in TARGETS:
    cs = sorted(a for a, _, _ in calls[t]); rw = sorted(raw_hits[t])
    print(f"target {t:#x}: capstone={len(cs)} raw={len(rw)} same_set={cs==rw}")
    if cs != rw:
        print("  only-capstone", [hex(x) for x in sorted(set(cs)-set(rw))])
        print("  only-raw     ", [hex(x) for x in sorted(set(rw)-set(cs))])
