# -*- coding: utf-8 -*-
"""_r064rev_probe1.py — 复核点 1/3 独立取证（异族复核员 R-064rev，全新实现）
- 自带 PE 解析（不调用门禁 rb()，不复用 _r064_probe*）
- RTTI walk：V → [V-4]=COL → COL+0xC=TD → TD+8=名；另读 COL sig/属性、COL+0x10=CHD numBases/基类数组
- 双链 + 语境家族（GenericNode / List<INISection*> / CDFileClass / CCFileClass / CCINIClass 控制位）
- 0x5256F0 体内双 stamp 亲验（[esi]=0x7EA5F4 与 [esi+0xC]=0x7E1B04）
只读。输出至 stdout。
"""
import struct, sys, hashlib

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

raw = open(EXE, "rb").read()
print("sha256:", hashlib.sha256(raw).hexdigest())
e_lfanew = struct.unpack_from("<I", raw, 0x3C)[0]
machine = struct.unpack_from("<H", raw, e_lfanew + 4)[0]
nsec = struct.unpack_from("<H", raw, e_lfanew + 6)[0]
optsz = struct.unpack_from("<H", raw, e_lfanew + 20)[0]   # coff+16，非 coff+2（R-064 诚实账①之坑）
opt = e_lfanew + 24
ib = struct.unpack_from("<I", raw, opt + 28)[0]
print("machine=%04x nsec=%d optsz=%d ImageBase=%08X" % (machine, nsec, optsz, ib))
tab = opt + optsz
secs = []
for i in range(nsec):
    name = raw[tab + i*40: tab + i*40 + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i*40 + 8)
    secs.append((name, ib + va, vsz, rp, rsz))
    print("  %-8s VA=%08X VSZ=%08X raw=%08X..%08X" % (name, ib + va, vsz, rp, rp + rsz))

def rb(va, n):
    rva = va - ib
    for name, sva, vsz, rp, rsz in secs:
        if sva - ib <= rva < sva - ib + vsz:
            fo = rp + (rva - (sva - ib))
            if fo < rp + rsz:
                return raw[fo:fo + n]
            return bytes(n)
    return b""

def rd(va):
    b = rb(va, 4)
    return int.from_bytes(b, "little") if len(b) == 4 else None

def cstr(va, mx=80):
    out = bytearray()
    for i in range(mx):
        c = rb(va + i, 1)
        if not c or c == b"\0":
            break
        out += c
    return out.decode("latin1")

def walk(V, label):
    print("\n== walk %s : V=0x%06X ==" % (label, V))
    col = rd(V - 4)
    print("  [V-4]=0x%06X bytes=%s -> COL=0x%06X" % (V - 4, rb(V - 4, 4).hex(), col))
    sig, off, cdoff = rd(col), rd(col + 4), rd(col + 8)
    print("  COL sig=%s off=%s cdOff=%s" % (sig, off, cdoff))
    td = rd(col + 0xC)
    print("  [COL+0xC]=0x%06X bytes=%s -> TD=0x%06X" % (col + 0xC, rb(col + 0xC, 4).hex(), td))
    vfp = rd(td)
    name = cstr(td + 8)
    print("  TD@0x%06X vfp=[TD]=0x%06X spare=%s name=%r" % (td, vfp, rd(td + 4), name))
    okname = all(32 <= b < 127 for b in name.encode("latin1"))
    print("  名可打印（非乱码）: %s" % okname)
    chd = rd(col + 0x10)
    numB = rd(chd + 8)
    print("  [COL+0x10]=0x%06X -> CHD; numBases=[CHD+8]=%s" % (col + 0x10, numB))
    bases = []
    if numB is not None and 0 < numB <= 16:
        for i in range(numB):
            btd = rd(chd + 0xC + i * 4)
            bases.append((hex(btd), cstr(btd + 8) if btd else "?"))
    print("  基类 TD 数组: %s" % bases)
    return dict(V=V, col=col, td=td, name=name, vfp=vfp, chd=chd, numBases=numB, bases=bases)

# --- 双链 ---
f1 = walk(0x7E1B04, "R-062 冻结 stamp（GenericList 家族）")
f2 = walk(0x7EA5F4, "R-063b/R-064 stamp（INIClass 家族）")

# --- 互不为基类 双向判定 ---
td1, td2 = f1["td"], f2["td"]
print("\n== 互不为对方基类 ==")
print("  GenericList 基类数组含 INIClass TD(0x%06X)? %s" % (td2, any(int(h,16)==td2 for h,_ in f1["bases"])))
print("  INIClass   基类数组含 GenericList TD(0x%06X)? %s" % (td1, any(int(h,16)==td1 for h,_ in f2["bases"])))

# --- 语境家族 ---
print("\n== 语境家族 ==")
walk(0x7E1B0C, "GenericNode?")
walk(0x7E1AFC, "List<INISection*>?")
walk(0x7E1668, "CDFileClass?")
walk(0x7E16B0, "CCFileClass?（R-064 §3 vtable 落实所用）")

# --- 控制位复现（R-062 §2 所载 CCINIClass TD 0x8174C8 vfp 0x7F9594）---
print("\n== 控制位 ==")
print("  [0x8174C8]=%s（期望 94957f00）" % rb(0x8174C8, 4).hex())
print("  [0x8174C8]=vfp -> 0x%06X；名@0x8174D0=%r" % (rd(0x8174C8), cstr(0x8174D0)))
print("  type_info vtable 锚：两 TD vfp 均=%s" % (hex(f1["vfp"]), ))

# --- 0x5256F0 体内双 stamp 亲验 ---
print("\n== 0x5256F0 复位/析构体双 stamp ==")
# 窗：0x5256F0..0x5256F0+0x120 线性反汇编，找 c7 06 f4 a5 7e 00（[esi],0x7EA5F4）与
# c7 46 0c f4… 或 041b7e00（[esi+0xC],imm）
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32)
start = 0x5256F0
code = rb(start, 0x120)
hits = []
for ins in md.disasm(code, start):
    b = ins.bytes.hex()
    line = "  %06X  %-22s %s %s" % (ins.address, b, ins.mnemonic, ins.op_str)
    if ins.mnemonic == "mov" and "esi" in ins.op_str and ("0x7ea5f4" in ins.op_str or "0x7e1b04" in ins.op_str or "0x7e1b0c" in ins.op_str):
        hits.append(line)
        print(line + "   <== STAMP")
    elif ins.mnemonic in ("push", "mov", "lea", "add", "ret", "call") and len(hits) < 20:
        pass
print("  stamp 命中行：")
for h in hits:
    print("   ", h)
# 逐字节 pin：期望 0x5256F8 处 c706f4a57e00（mov [esi],0x7EA5F4）
print("  rb(0x5256F8,6)=%s（期望 c706f4a57e00）" % rb(0x5256F8, 6).hex())
print("  rb(0x52571E,7)=%s（期望 c7460c041b7e00）" % rb(0x52571E, 7).hex())
print("  rb(0x525760,7)=%s / rb(0x52578D,7)=%s（GenericNode 头件候选）" % (rb(0x525760,7).hex(), rb(0x52578D,7).hex()))
