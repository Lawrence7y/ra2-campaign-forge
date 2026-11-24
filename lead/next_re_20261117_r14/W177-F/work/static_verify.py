#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-E 静态复核（只读 gamemd.exe，用 capstone+pefile）：
 - 0x47C620 can-place 逐格占用扫描：确认 WhatAmI 拒绝集 {6,0x24}，绕过门 A8E7AC/A8E9A0
 - 0x47E8A0 挂链 worker：确认 WhatAmI==6 链尾 append 分支
 - RTTI: BuildingClass/InfantryClass/UnitClass vt -> COL+0xC -> TD+8 -> name
不启动游戏，不读写进程内存。输出落盘 EVIDENCE/static_verify.txt。
"""
import pefile, json, os, time
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

GAME = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-E\EVIDENCE\static_verify.txt"
pe = pefile.PE(GAME)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b"\x00").decode("latin1")
    secs[nm] = (IB + s.VirtualAddress, s.PointerToRawData, s.SizeOfRawData, s.Misc_VirtualSize)
data = open(GAME, "rb").read()

def rd(va, n):
    for nm, (v0, r0, sz, vsz) in secs.items():
        if v0 <= va < v0 + max(sz, vsz):
            off = r0 + (va - v0)
            if off + n <= len(data):
                return data[off:off+n]
    return None

def u32(va):
    b = rd(va, 4)
    return int.from_bytes(b, "little") if b and len(b) == 4 else None

def cstr(va, n=120):
    b = rd(va, n)
    if not b: return None
    return b.split(b"\x00")[0].decode("latin1", "replace")

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
lines = []
def P(s=""):
    lines.append(str(s))

TV = secs[".text"][0]; TR = secs[".text"][1]; TS = secs[".text"][2]
traw = data[TR:TR+TS]

def dis(va, n, label):
    P("\n===== %s @ 0x%08X (%d bytes) =====" % (label, va, n))
    for i in md.disasm(traw[va-TV:va-TV+n], va):
        P("0x%08X  %-22s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))

P("W177-E static verify ts=%s" % time.strftime("%Y-%m-%dT%H:%M:%S%z"))
P("gamemd ImageBase=0x%X .text VA=0x%X" % (IB, TV))

# --- can-place 0x47C620: scan first 0x260 bytes for cmp reg,imm / global refs ---
dis(0x47C620, 0x270, "0x47C620 can-place occupancy scanner")
# --- 0x47CA70 bypass target ---
dis(0x47CA60, 0x30, "0x47CA70 reentrancy bypass (mov al,1; ret 0xc)")
# --- 0x47E8A0 attach-chain worker ---
dis(0x47E8A0, 0x90, "0x47E8A0 attach-to-cell worker (WhatAmI==6 append branch)")

# --- WhatAmI of key classes via vtable slot +0x2C (from audit b3 method) ---
P("\n===== WhatAmI (vtable slot +0x2C) + RTTI for key vtables =====")
VTS = {
    "BuildingClass": 0x7E3EBC,
    "InfantryClass": 0x7EB058,
}
def whatami(fn):
    b = rd(fn, 8)
    if not b: return None
    if b[0] == 0xB8 and b[5] == 0xC3:
        return int.from_bytes(b[1:5], "little")
    if b[0:2] in (b"\x33\xc0", b"\x31\xc0") and b[2] == 0xC3:
        return 0
    return None
for nm, vt in VTS.items():
    col = u32(vt - 4)
    td = u32(col + 0xC) if col else None
    np_ = u32(td + 8) if td else None
    name = cstr(np_) if np_ else None
    wfn = u32(vt + 0x2C)
    w = whatami(wfn) if wfn else None
    P("%-14s vt=0x%08X COL=0x%08X TD=0x%08X name=%s WhatAmI_fn=0x%08X WhatAmI=%s" % (
        nm, vt, col or 0, td or 0, name, wfn or 0, w))
# UnitClass vtable is unknown here; find via RTTI TD name search
P("\n===== locate UnitClass COL via TD name scan in .rdata =====")
# scan .rdata for TD name strings '.?AVUnitClass@@'
rdva, rraw, rsz, rvsz = secs[".rdata"]
rdata = data[rraw:rraw+rsz]
for needle in (b".?AVUnitClass@@", b".?AVInfantryClass@@", b".?AVBuildingClass@@"):
    idx = rdata.find(needle)
    if idx < 0:
        P("%s -> not found in .rdata" % needle.decode("latin1")); continue
    name_va = rdva + idx
    # TD+8 = name_va => TD = name_va-8
    td = name_va - 8
    # find COL with COL+0xC == td: scan .rdata dwords
    col = None
    for off in range(0, rsz-3, 4):
        if int.from_bytes(rdata[off:off+4], "little") == td:
            col = rdva + off; break
    # vtable = dword before COL is not enough; scan all vtables with [vt-4]==col
    vt = None
    for off in range(0, rsz-3, 4):
        if int.from_bytes(rdata[off:off+4], "little") == col and col:
            # candidate vt-4 location == col means vt = rdva+off+4
            cand = rdva + off + 4
            wfn = u32(cand+0x2C)
            if wfn and whatami(wfn) is not None:
                vt = cand; break
    P("%-22s nameVA=0x%08X TD=0x%08X COL=%s vt=%s WhatAmI=%s" % (
        needle.decode("latin1"), name_va, td, hex(col) if col else None,
        hex(vt) if vt else None, whatami(u32(vt+0x2C)) if vt else None))

os.makedirs(os.path.dirname(EV), exist_ok=True)
open(EV, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("wrote", EV, "lines", len(lines))
