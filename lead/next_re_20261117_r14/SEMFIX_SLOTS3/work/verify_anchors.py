# SEMFIX-SLOTS3 anchor verification — read-only disasm from gamemd.exe.
# Opens the target PE read-only, maps VA->file offset via pefile, disassembles
# each function body with capstone(skipdata) and checks declared anchors are
# real instruction starts whose text matches the audit card claims.
import sys, json, os
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE, fast_load=True)
IMAGE_BASE = pe.OPTIONAL_HEADER.ImageBase
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

def va2off(va):
    rva = va - IMAGE_BASE
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    raise ValueError("VA outside sections: %08X" % va)

data = open(EXE, "rb").read()

def insn_text(insn):
    return (insn.mnemonic + " " + insn.op_str).strip()

def disasm_window(entry, length):
    off = va2off(entry)
    blob = data[off:off+length]
    out = {}
    for insn in md.disasm(blob, entry):
        rel = insn.address - entry
        out[rel] = insn_text(insn)
    return out

# anchors: (entry, rel, must_contain_substring_or_none, label)
# We disassemble a generous window per entry and assert each rel is an
# instruction start; where a token is given, assert it appears in the text.
ROWS = {
 "006F3330": (0x500, [
   (0x00BD, "cmp dword ptr [eax + 0xd50], -1", "audit: +0xBD gate"),
   (0x00C4, "je ", "gate target"),
   (0x00E0, "mov cl, byte ptr [edi + 0x14]", "+0xBD je landing = object-selection continuation"),
   (0x0478, "cmp eax, -1", "-1 return gate"),
   (0x047B, "jne ", "-1 return jne"),
   (0x047D, "xor eax, eax", "-1->0 return"),
 ]),
 "006F8DF0": (0x1000, [
   (0x03FC, None, "loop head"),
   (0x050B, None, "audit: +0x50B claim (expansion size calc)"),
   (0x0522, None, "real advance/ element write"),
   (0x0525, None, "element write"),
   (0x0552, None, "audit: +0x552 claim (expansion size calc)"),
   (0x057B, "cmp eax, ecx", "bound"),
   (0x0595, None, "backedge"),
 ]),
 "006FC0B0": (0x0D00, [
   (0x0717, "cmp eax, -1", "-1 sentinel 1"),
   (0x087C, "cmp edx, -1", "-1 sentinel 2"),
   (0x0887, "cmp eax, -1", "-1 sentinel 3"),
   (0x08AB, "cmp edx, -1", "-1 sentinel 4"),
 ]),
 "006FFEC0": (0x0800, [
   (0x01F9, None, "loop region"),
   (0x03D3, None, "audit: +0x3D3 claim (timestamp -1)"),
   (0x03D6, None, "je"),
   (0x03E6, None, "landing"),
 ]),
 "0070BF50": (0x0400, [
   (0x000C, "call ", "helper call"),
   (0x0011, None, "xor ebx,ebx"),
   (0x0013, None, "cmp eax,ebx"),
   (0x0015, None, "jl"),
   (0x003F, None, "loop"),
   (0x02F9, None, "ret site"),
 ]),
 "00712170": (0x4000, [
   (0x076C, None, "loop head"),
   (0x07DA, "mov dword ptr [edi - 0x1fc], eax", "explicit write 1"),
   (0x0811, "mov dword ptr [edi], eax", "explicit write 2"),
   (0x081D, None, "advance inc eax"),
   (0x0822, None, "advance add edi"),
   (0x0826, "cmp eax, ecx", "bound"),
   (0x0CC2, None, "-1 sentinel sample"),
 ]),
 "00716150": (0x0200, [
   (0x005E, None, "0x7fff sentinel 1"),
   (0x0065, None, "0x7fff sentinel 2"),
   (0x0077, None, "advance add esi,4"),
   (0x0085, None, "acc write"),
   (0x008A, None, "acc write"),
   (0x0095, None, "acc write"),
   (0x0104, None, "backedge"),
 ]),
 "006D0270": (0x0100, [
   (0x000E, None, "loop head"),
   (0x0016, None, "je skip"),
   (0x002A, None, "dword[esi]=0 at merge"),
   (0x0033, None, "advance add esi,4"),
   (0x0034, None, "cmp bound"),
   (0x003A, None, "jl backedge"),
 ]),
 "006D04F0": (0x0200, [
   (0x0015, None, "gate1 je tail"),
   (0x0023, None, "audit: +0x23 claim (actually mov al,[esi+0x5544])"),
   (0x0029, None, "audit: +0x29 je gate2 (corrected)"),
   (0x00E6, None, "loop1 call"),
   (0x00E9, None, "loop1 advance"),
   (0x00EC, None, "loop1 bound"),
   (0x0105, None, "loop2 read"),
   (0x012E, None, "loop2 advance"),
   (0x0131, None, "loop2 bound"),
 ]),
 "00653850": (0x0200, [
   (0x0038, None, "coord gate"),
   (0x0064, None, "call 0x5bdc80"),
   (0x00AE, None, "WhatAmI gate"),
   (0x00EA, None, "write 8"),
   (0x00F6, None, "write 9"),
   (0x0109, None, "write 1"),
   (0x0138, None, "call 0x656cb0"),
   (0x0152, None, "call 0x6578f0"),
 ]),
 "004F4480": (0x0200, [
   (0x002F, None, "setne/sete"),
   (0x0049, None, "gate1 jne"),
   (0x005F, None, "0x6d3d10 arg0"),
   (0x0074, None, "0x6d3d10 arg1"),
   (0x0095, None, "0x6d3d10 arg2"),
   (0x00BD, None, "virtual call [edx+0x40]"),
   (0x00C0, None, "flag clear"),
   (0x00FE, None, "call 0x55f1e0"),
 ]),
 "004A8960": (0x0200, [
   (0x0027, None, "scroll origin write 1"),
   (0x005D, None, "call 0x6d5f60"),
   (0x007A, None, "release old"),
   (0x00A4, None, "alloc result"),
   (0x00DA, None, "construct 0x7bc970"),
   (0x00E8, None, "write 0x8000"),
   (0x012B, None, "call 0x410e50"),
 ]),
 "006C6680": (0x0200, [
   (0x000A, None, "gate1 [esi+0x30]"),
   (0x000F, None, "free 0x7c8b3d"),
   (0x0031, None, "alloc 0x7c8e17"),
   (0x003C, None, "test (corrected)"),
   (0x003E, None, "je (corrected)"),
   (0x0042, None, "copy call (corrected)"),
   (0x004E, None, "virtual call [edx+0x48]"),
   (0x0064, None, "virtual call [eax+0x88]"),
 ]),
 "004F4320": (0x0200, [
   (0x0010, None, "virtual call 1"),
   (0x0031, None, "gate [0xa8ef54]"),
   (0x0037, None, "true-domain call [edx+0x5c]"),
   (0x0044, None, "true-domain virtual [eax+0x38]"),
   (0x007A, None, "false-domain call 0x54f000"),
   (0x0092, None, "false-domain call 0x54f050"),
   (0x00B9, None, "merge virtual [eax+0x28]"),
 ]),
 "006AC210": (0x0200, [
   (0x000A, None, "first gate call 0x640450"),
   (0x0019, None, "case 0xc8"),
   (0x0072, None, "call 0x7ca564"),
   (0x0085, None, "case 0xc9"),
   (0x00AC, None, "range [0xcb,0xcf)"),
   (0x00C8, None, "sub-case 0"),
   (0x0110, None, "sub-case 3"),
 ]),
}

results = {}
all_ok = True
for entry, (length, anchors) in ROWS.items():
    e = int(entry, 16)
    d = disasm_window(e, length)
    rec = {"count_insns": len(d), "anchors": []}
    for rel, token, label in anchors:
        txt = d.get(rel)
        ok = txt is not None and (token is None or token in txt)
        if not ok:
            all_ok = False
        rec["anchors"].append({"rel": "0x%03X" % rel, "label": label, "ok": ok,
                               "text": txt, "expect_token": token})
    results[entry] = rec

print(json.dumps({"all_ok": all_ok, "rows": results}, ensure_ascii=False, indent=1))
