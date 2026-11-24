#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S01-V1 静态最小定位：WinMain / 主循环体 / 预期每帧调用点。
纪律：capstone 必须 skipdata=True；站点归属用「函数区间包含」，不用 entry_at_or_before。
只读 gamemd.exe，不写任何目标文件。
"""
import sys, json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000
pe = pefile.PE(EXE)
SECS = pe.sections

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True  # 纪律 2
md.detail = True

def va2off(va):
    rva = va - IB
    for s in SECS:
        lo = s.VirtualAddress
        hi = lo + max(s.Misc_VirtualSize, s.SizeOfRawData)
        if lo <= rva < hi:
            return s.PointerToRawData + (rva - lo)
    return None

def read(va, n):
    o = va2off(va)
    if o is None:
        return b""
    with open(EXE, "rb") as f:
        f.seek(o)
        return f.read(n)

def disasm(va, n):
    code = read(va, n)
    return list(md.disasm(code, va))

# ---------- 1) CRT startup -> WinMain ----------
ep = IB + pe.OPTIONAL_HEADER.AddressOfEntryPoint
print("=== PE EntryPoint VA=%08X ===" % ep)
print("--- first 120 instructions at entry (skipdata=True) ---")
ent_ins = disasm(ep, 0x400)
for i in ent_ins[:120]:
    print("  %08X  %-8s %s" % (i.address, i.mnemonic, i.op_str))
# find direct calls in startup window, especially ones whose target is in .text and looks like WinMain
print("--- direct call/jmp targets in first 0x400 bytes of startup ---")
for i in ent_ins:
    if i.mnemonic in ("call", "jmp") and i.operands and i.operands[0].type == X86_OP_IMM:
        print("  %08X  %-5s -> %08X" % (i.address, i.mnemonic, i.operands[0].imm))

# ---------- 2) main loop body 0x48CCC0 .. 0x48D05C ----------
MAIN_LOOP = 0x48CCC0
MAIN_END  = 0x48D05C  # 780 B
print("\n=== MAIN LOOP 0x48CCC0..0x48D05C (780 B), skipdata=True ===")
ins = disasm(MAIN_LOOP, MAIN_END - MAIN_LOOP)
print("decoded instructions:", len(ins))
# call sites in order
NAMES = {
    0x7241A0: "crash_guard_7241A0 (②-a victim, ledger §881)",
    0x69BAB0: "sub_69BAB0",
    0x55D360: "perframe_update_55D360 (每帧更新, ledger §881)",
    0x55CFD0: "predicate_55CFD0",
    0x48C8B0: "Conquer_48C8B0 (Conquer.CPP, ledger §881)",
    0x52BA60: "Init_52BA60 (Init.CPP boot)",
    0x52D9A0: "Init_52D9A0 (Init.CPP)",
}
calls = []
print("--- all direct call sites in order ---")
for i in ins:
    if i.mnemonic == "call" and i.operands and i.operands[0].type == X86_OP_IMM:
        t = i.operands[0].imm
        calls.append((i.address, t))
        print("  call@%08X -> %08X  %s" % (i.address, t, NAMES.get(t, "")))
print("--- full disassembly saved to EVIDENCE ---")
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S01-V1\EVIDENCE\static_mainloop_disasm.txt", "w", encoding="utf-8") as f:
    for i in ins:
        f.write("  %08X  %-8s %s\n" % (i.address, i.mnemonic, i.op_str))

# ---------- 3) dump startup disasm too ----------
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S01-V1\EVIDENCE\static_entry_disasm.txt", "w", encoding="utf-8") as f:
    for i in ent_ins:
        f.write("  %08X  %-8s %s\n" % (i.address, i.mnemonic, i.op_str))

# ---------- summary json ----------
out = {
    "entry_va": "0x%08X" % ep,
    "main_loop": "0x48CCC0",
    "main_loop_end": "0x48D05C",
    "expected_perframe_calls": [
        {"site": "0x%08X" % s, "target": "0x%08X" % t, "name": NAMES.get(t, "sub_%08X" % t)}
        for s, t in calls
    ],
}
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S01-V1\EVIDENCE\static_summary.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print("\nwrote static_summary.json (%d call sites)" % len(calls))
