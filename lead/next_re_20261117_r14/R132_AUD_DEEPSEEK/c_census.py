#!/usr/bin/env python3
"""R132 task C: template instantiation census via immediate-byte mask."""
import json
import re
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
t = [s for s in pe.sections if s.Name.rstrip(b"\x00") == b".text"][0]
TEXT_VA = IB + t.VirtualAddress
TEXT_SZ = min(t.Misc_VirtualSize, t.SizeOfRawData)
raw = open(EXE, "rb").read()
CODE = raw[t.PointerToRawData:t.PointerToRawData + TEXT_SZ]
TEXT_END = TEXT_VA + TEXT_SZ
print("text va=%#x size=%#x end=%#x" % (TEXT_VA, TEXT_SZ, TEXT_END))

A = 0x6BEDB0
L = 136
body = bytes(CODE[A - TEXT_VA: A - TEXT_VA + L])
print("body A len", len(body), "md5", __import__("hashlib").md5(body).hexdigest())

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False


def parse_imm(s):
    s = s.strip()
    try:
        if s.startswith("0x") or s.startswith("-0x") or s.startswith("0X"):
            return int(s, 16)
        return int(s, 10)
    except ValueError:
        return None


# ---- C1: push imm > 0x400000 inside body A
pushed = []
for ins in md.disasm(body, A):
    if ins.mnemonic != "push":
        continue
    v = parse_imm(ins.op_str)
    if v is None:
        continue
    if v > 0x400000:
        imm_off = ins.address - A + ins.size - 4
        pushed.append({"insn_va": hex(ins.address), "off": ins.address - A,
                       "op": ins.op_str, "imm": hex(v),
                       "imm_off": imm_off, "imm_bytes": body[imm_off:imm_off + 4].hex(" ")})
print("C1 push imm >0x400000 count =", len(pushed))
for p in pushed:
    print("  ", p)

mask_offs = []
for p in pushed:
    mask_offs += [p["imm_off"] + k for k in range(4)]
mask_set = set(mask_offs)
print("mask offsets:", sorted(mask_set))


def masked_scan(pat, name):
    parts = []
    i = 0
    while i < len(pat):
        if i in mask_set:
            j = i
            while j < len(pat) and j in mask_set:
                j += 1
            parts.append(b".{%d}" % (j - i))
            i = j
        else:
            j = i
            while j < len(pat) and j not in mask_set:
                j += 1
            parts.append(re.escape(pat[i:j]))
            i = j
    rx = re.compile(b"(?=(" + b"".join(parts) + b"))", re.DOTALL)
    hits = [TEXT_VA + m.start() for m in rx.finditer(CODE)]
    print("C2 masked scan [%s]: hits=%d" % (name, len(hits)), [hex(h) for h in hits])
    return hits


def plain_scan(pat, name):
    hits = []
    i = CODE.find(pat)
    while i >= 0:
        hits.append(TEXT_VA + i)
        i = CODE.find(pat, i + 1)
    print("plain scan [%s]: hits=%d" % (name, len(hits)), [hex(h) for h in hits])
    return hits


hits = masked_scan(body, "body A mask")
assert A in hits, "self-match missing"

# ---- C3: read back immediates at each hit
print("C3 immediates per hit:")
per_hit = {}
for h in hits:
    o = h - TEXT_VA
    vals = [int.from_bytes(CODE[o + p["imm_off"]: o + p["imm_off"] + 4], "little") for p in pushed]
    per_hit[hex(h)] = [hex(v) for v in vals]
    print("  %#x -> %s  bytes=%s" % (h, [hex(v) for v in vals],
                                     " | ".join(CODE[o + p["imm_off"]:o + p["imm_off"] + 4].hex(" ") for p in pushed)))

# ---- C4: E8 call sites (raw byte method)
print("C4 E8 call sites:")
calls = {}
for h in hits:
    lst = []
    i = CODE.find(b"\xe8")
    while i >= 0:
        if i + 5 <= len(CODE):
            rel = int.from_bytes(CODE[i + 1:i + 5], "little", signed=True)
            src = TEXT_VA + i
            if (src + 5 + rel) == h:
                lst.append(hex(src))
        i = CODE.find(b"\xe8", i + 1)
    calls[hex(h)] = lst
    print("  %#x <- %s (n=%d)" % (h, lst, len(lst)))

# ---- C5 reverse controls
print("C5 controls:")
ctrl1 = bytearray(body)
ctrl1[5] = 0xFF
h1 = masked_scan(bytes(ctrl1), "off5=0xff")
ctrl2 = bytearray(body)
first_mask = min(mask_set)
ctrl2[first_mask] ^= 0xFF
h2 = masked_scan(bytes(ctrl2), "first mask byte flipped (off=%d)" % first_mask)
h3 = plain_scan(body, "unmasked body A")

json.dump({"pushed": pushed, "mask_offsets": sorted(mask_set),
           "masked_hits": [hex(h) for h in hits], "imms_per_hit": per_hit,
           "call_sites": calls,
           "control_off5_ff_hits": len(h1), "control_first_mask_flip_hits": len(h2),
           "control_unmasked_hits": len(h3),
           "control_unmasked_list": [hex(h) for h in h3],
           "control_first_mask_off": first_mask},
          open("c_census.json", "w"), indent=1)
