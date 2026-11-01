# -*- coding: utf-8 -*-
"""brev_probe_d.py — 本线独立发现检验：R-064 的「无配对」是否过强？

帧 A 里三条落格（本线 brev_probe_b 的独立 D 记账）：
  -0x8C ← mov [esp+0x38],0x7E1B04  @0x7787C0 (D=0xC4)
  -0x8C ← mov [esp+0x34],0x7E1AFC  @0x7787D1 (D=0xC0)
  -0x98 ← mov [esp+0x30],0x7EA5F4  @0x7787F7 (D=0xC8)   且 -0x98 = witness 槽 W
若 witness 对象=this=−0x98 的 INIClass 栈件，则 −0x8C = this+0xC 恰是 0x5256F0 里
`mov [esi+0xC],0x7E1B04` 的那个内嵌成员偏移；−0x88/−0x7C = this+0x10/+0x1C 恰是
0x5256F0 里两处 `mov [eax],0x7E1B0C`（GenericNode 头件）的偏移。
⇒ 若成立，R-062 的 0x7E1B04 落格**不是无配对的杂散临时件**，而是被传对象自身
   +0xC 子对象的构造写（List<INISection*> 的 GenericList 基类 vptr 先置、再升为派生 vptr）。

检验手段（全静态字节）：
 1) 帧 A 的 thiscall 序列：0x40E320/0x40E340/0x525A10 各自的 ecx 落格与 0x5256F0 偏移对照；
 2) 读 0x40E320 / 0x40E340 / 0x525A10 体（看写哪些偏移、置哪些 vptr）；
 3) 读 List<INISection*> / GenericList 的 RTTI 继承方向（CHD 基类数组，本线正确版式）；
 4) 同法在帧 B/C 的 this 落格上复算（可复现性）。
"""
import struct, hashlib, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

raw = open(r"D:\Project\ra2-campaign-forge\ra2youli/gamemd.exe", "rb").read()
assert hashlib.sha256(raw).hexdigest() == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e+6)[0]; optsz = struct.unpack_from("<H", raw, e+20)[0]
opt = e+24; ib = struct.unpack_from("<I", raw, opt+28)[0]; tab = opt+optsz
secs = []
for i in range(nsec):
    nm = raw[tab+i*40:tab+i*40+8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab+i*40+8)
    secs.append((nm, ib+va, vsz, rp, rsz))
def rb(va, n):
    rva = va - ib
    for nm, sva, vsz, rp, rsz in secs:
        if sva-ib <= rva < sva-ib+vsz:
            fo = rp + (rva-(sva-ib)); return raw[fo:fo+n] if fo < rp+rsz else bytes(n)
    return b""
def rd(va):
    b = rb(va, 4); return int.from_bytes(b, "little") if len(b) == 4 else None
def cstr(va, mx=90):
    o = bytearray()
    for i in range(mx):
        c = rb(va+i, 1)
        if not c or c == b"\0": break
        o += c
    return o.decode("latin1")
md = Cs(CS_ARCH_X86, CS_MODE_32)

print("=== 1) 0x5256F0（INIClass 复位/析构体）写入偏移全列（本线亲读） ===")
for ins in md.disasm(rb(0x5256F0, 0x140), 0x5256F0):
    b = ins.bytes.hex(); o = ins.op_str
    tag = ""
    if ins.mnemonic == "mov" and re.match(r"^dword ptr \[e(ax|si|di|bp)( ?\+ 0x[0-9a-f]+)?\], 0x7e", o):
        tag = "   <== VPTR STAMP"
    if ins.mnemonic == "lea" and re.match(r"^eax, \[esi \+ 0x", o):
        tag = "   <== member addr"
    print("  %06X %-22s %-5s %-30s%s" % (ins.address, b, ins.mnemonic, o, tag))

print("\n=== 2) 帧 A：thiscall this(=ecx) 与 arg 的本线落格（D 由 brev_probe_b 独立记账） ===")
# 本线独立 D（brev_b 输出）：0x7787A9 D=0xC0 / 0x7787B2 D=0xC0 / 0x7787C8 D=0xC4
#                                  0x7787DB D=0xC8 / 0x7787F7 D=0xC8 / 0x7787FF D=0xC8
#                                  0x77884B D=0xD0 (W-lea)
TH = [(0x77879D, 0x38, 0xC0, "lea ecx this → 0x40E320@7787A9"),
      (0x7787AE, 0x44, 0xC0, "lea ecx this → 0x40E320@7787B2"),
      (0x7787B7, 0x44, 0xC0, "lea eax arg"),
      (0x7787BB, 0x38, 0xC0, "lea ecx this → 0x40E340@7787C8"),
      (0x7787DB, 0x30, 0xC8, "lea ecx this → 0x525A10@7787FF"),
      (0x77884B, 0x38, 0xD0, "lea ecx this → 0x528C00@77884F (WITNESS)")]
for a, disp, D, what in TH:
    p = disp - D
    print("  %06X disp=0x%-4X D=0x%-4X → 物理格 %s   %s" % (a, disp, D, hex(p), what))
print("  INIClass this = -0x98；成员偏移对照：+0xC→-0x8C，+0x10→-0x88，+0x1C→-0x7C")
print("  ⇒ 落格是否为对象内部成员？")
obj = -0x98
for name, off in [("+0x0 vptr", 0), ("+0x8", 8), ("+0xC", 0xC), ("+0x10", 0x10), ("+0x1C", 0x1C)]:
    print("     this%s = 0x%X" % (name, obj + off))
print("  观察：0x7787C0 的 GL stamp 落 -0x8C = this+0xC；0x7787D1 的 List stamp 落 -0x8C = this+0xC；")
print("        0x40E320 的两次 this 落 -0x88(this+0x10) 与 -0x7C(this+0x1C)；0x7787A5 的清零落 -0x90(this+8)")

print("\n=== 3) 被调方体（0x40E320 / 0x40E340 / 0x525A10）写哪些偏移、置哪些 vptr ===")
for h, nm in [(0x40E320, "0x40E320"), (0x40E340, "0x40E340"), (0x525A10, "0x525A10(claim: INIClass ctor)")]:
    print("  -- %s --" % nm)
    n = 0
    for ins in md.disasm(rb(h, 0x80), h):
        b = ins.bytes.hex(); m = ins.mnemonic; o = ins.op_str
        tag = ""
        mm = re.search(r", (0x7e[0-9a-f]{4})$", o)
        if m == "mov" and mm:
            V = int(mm.group(1), 16)
            col = rd(V-4); td = rd(col+0xC) if col else None
            tag = "   <== STAMP vtable %06X -> %r" % (V, cstr(td+8) if td else "?")
        print("    %06X %-20s %-5s %s%s" % (ins.address, b, m, o, tag))
        n += 1
        if m == "ret" and n > 3: break


print("\n=== 4) RTTI 继承方向（本线正确版式：CHD+8=numBases，CHD+0xC=BaseClassArray，元素=BCD*，BCD+0=基类TD*） ===")
def chain(V):
    col = rd(V-4); td = rd(col+0xC); chd = rd(col+0x10); nb = rd(chd+8); arr = rd(chd+0xC)
    out = []
    for i in range(nb or 0):
        bcd = rd(arr + i*8) if False else rd(chd+0xC+i*4)
        out.append((bcd, cstr(rd(bcd)+8) if bcd and rd(bcd) else "?"))
    return col, td, cstr(td+8), chd, nb, out
for label, V in [("GenericList", 0x7E1B04), ("List<INISection*>", 0x7E1AFC), ("INIClass", 0x7EA5F4), ("GenericNode", 0x7E1B0C)]:
    col, td, tdn, chd, nb, bs = chain(V)
    print("  %-18s V=%06X COL=%06X TD=%06X '%s' numBases=%s bases=%s" % (label, V, col, td, tdn, nb, bs))
print("  （注：元素数组按 4 字节步进取 BCD*；若 numBases>1 需按 8 字节步进复核，见下）")
for label, V in [("List<INISection*>", 0x7E1AFC), ("CDFileClass", 0x7E1668)]:
    col = rd(V-4); chd = rd(col+0x10); nb = rd(chd+8); arr = rd(chd+0xC)
    print("  %s arr=%06X raw=%s" % (label, arr, rb(arr, 4*(nb or 1)).hex()))
    for i in range(nb or 0):
        ptr = rd(arr+i*4)
        print("      [%d] @arr+0x%X = %06X -> BCD[+0]=%06X 名=%r numOffsets=%s" % (
            i, i*4, ptr, rd(ptr) if ptr else 0, cstr(rd(ptr)+8) if ptr and rd(ptr) else "?",
            rd(ptr+4) if ptr else None))
