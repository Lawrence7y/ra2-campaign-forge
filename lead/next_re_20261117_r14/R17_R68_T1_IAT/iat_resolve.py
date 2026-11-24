#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R37-T1 · 纯 PE 结构解析器，用来判定某个 VA 是否落在导入表(FirstThunk)槽上，
并解析该槽对应的 IMAGE_IMPORT_BY_NAME(Hint + 完整函数名字符串)。
只读 gamemd.exe，不写 exe。

用法:
    python iat_resolve.py <target_va> [<control_va> ...]
    target_va 可写 0x7E11C8 或 7E11C8
默认: 0x7E11C8 0x7E11CC
"""
import struct, sys, os

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
buf = open(EXE, "rb").read()

def u16(o): return struct.unpack_from("<H", buf, o)[0]
def u32(o): return struct.unpack_from("<I", buf, o)[0]
def s32(o): return struct.unpack_from("<i", buf, o)[0]

# ---------- PE 头 ----------
e_lfanew = u32(0x3C)
assert buf[e_lfanew:e_lfanew+4] == b"PE\0\0", "not PE"
coff = e_lfanew + 4
machine      = u16(coff)
nsec         = u16(coff + 2)
SizeOfOptHdr = u16(coff + 16)
opt          = coff + 20
magic        = u16(opt)
is64         = (magic == 0x20B)
ImageBase    = struct.unpack_from("<Q", buf, opt + 24)[0] if is64 else u32(opt + 28)
NumRvaAndSizes = u32(opt + (108 if is64 else 92))
dd_off       = opt + (112 if is64 else 96)

def dd(i):
    return (u32(dd_off + 8*i), u32(dd_off + 8*i + 4))

sec_tab = opt + SizeOfOptHdr
secs = []
for i in range(nsec):
    b = sec_tab + 40*i
    name = buf[b:b+8].rstrip(b"\0").decode("latin1")
    vsize = u32(b+8); vaddr = u32(b+12); rsize = u32(b+16); raddr = u32(b+20)
    secs.append(dict(name=name, vsize=vsize, vaddr=vaddr, rsize=rsize, raddr=raddr))

def rva2off(rva):
    for s in secs:
        lo = s["vaddr"]; hi = lo + max(s["vsize"], s["rsize"])
        if lo <= rva < hi:
            off = rva - lo + s["raddr"]
            if off >= len(buf):
                return None
            return off
    if rva < s0hdr if False else False:
        pass
    # headers
    if rva < secs[0]["vaddr"]:
        return rva
    return None

def sec_of(rva):
    for s in secs:
        if s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rsize"]):
            return s
    return None

def cstr(off):
    end = buf.index(b"\0", off)
    return buf[off:end].decode("latin1")

print("=== PE 摘要 ===")
print("file            :", EXE)
print("size            :", len(buf))
print("e_lfanew        : 0x%X" % e_lfanew)
print("Machine         : 0x%04X (%s)" % (machine, "I386" if machine == 0x14C else "x64" if machine == 0x8664 else "?"))
print("Magic           : 0x%03X (%s)" % (magic, "PE32+" if is64 else "PE32"))
print("ImageBase       : 0x%X" % ImageBase)
print("NumRvaAndSizes  : %d" % NumRvaAndSizes)
print()
print("=== 节表 ===")
for s in secs:
    print("  %-8s VA=0x%08X VSize=0x%08X RawPtr=0x%08X RawSize=0x%08X" %
          (s["name"], s["vaddr"], s["vsize"], s["raddr"], s["rsize"]))
print()

IMP_RVA, IMP_SZ = dd(1)
print("=== 导入表目录 (DataDirectory[1] IMPORT) ===")
print("  RVA=0x%08X Size=0x%X  => 文件偏移=0x%X" % (IMP_RVA, IMP_SZ, rva2off(IMP_RVA) or 0))
print()

# ---------- 解析导入描述符 ----------
descs = []
p = rva2off(IMP_RVA)
i = 0
while True:
    o = p + 20*i
    oft = u32(o); tds = u32(o+4); fc = u32(o+8); name_rva = u32(o+12); ft = u32(o+16)
    if (oft, tds, fc, name_rva, ft) == (0,0,0,0,0):
        break
    dll = cstr(rva2off(name_rva))
    descs.append(dict(idx=i, oft=oft, tds=tds, fc=fc, name_rva=name_rva, ft=ft, dll=dll,
                      off=o, firstthunk_rva=ft if ft else oft))
    i += 1

print("=== 导入描述符 (共 %d 个 DLL) ===" % len(descs))
for d in descs:
    print("  [%2d] off=0x%X  DLL=%-20s OriginalFirstThunk=0x%08X FirstThunk=0x%08X NameRVA=0x%08X" %
          (d["idx"], d["off"], d["dll"], d["oft"], d["ft"], d["name_rva"]))
print()

# ---------- 构建 FirstThunk 槽 -> 函数 的映射 ----------
slots = {}   # slot_rva -> dict
for d in descs:
    o_oft = rva2off(d["oft"]) if d["oft"] else rva2off(d["ft"])
    o_ft  = rva2off(d["ft"])
    k = 0
    while True:
        pin = u32(o_oft + 4*k) if d["oft"] else u32(o_ft + 4*k)
        val = u32(o_ft + 4*k)
        if pin == 0:
            break
        slot_rva = d["ft"] + 4*k
        ent = dict(dll=d["dll"], slot_rva=slot_rva, slot_off=o_ft + 4*k,
                   index=k, pin=pin, cur_val=val, kind=None, hint=None, name=None,
                   name_rva=None, name_off=None, ordinal=None, raw=b"")
        if pin & 0x80000000:
            ent["kind"] = "ordinal"
            ent["ordinal"] = pin & 0xFFFF
            ent["raw"] = buf[o_oft + 4*k: o_oft + 4*k + 4]
        else:
            ent["kind"] = "name"
            ent["name_rva"] = pin
            no = rva2off(pin)
            ent["name_off"] = no
            ent["hint"] = u16(no)
            ent["raw"] = buf[no: no+2+64]
            ent["name"] = cstr(no + 2)
        slots[slot_rva] = ent
        k += 1

print("=== 全部 IAT 槽 (按 RVA 排序，共 %d 项) ===" % len(slots))
for rva in sorted(slots):
    e = slots[rva]
    label = ("#%d" % e["ordinal"]) if e["kind"] == "ordinal" else ("%s (hint %d)" % (e["name"], e["hint"]))
    print("  0x%08X  %-20s idx=%-4d %s   [值=0x%08X]" % (rva, e["dll"], e["index"], label, e["cur_val"]))
print()

# ---------- 目标查询 ----------
def query(va):
    print("=" * 72)
    print("查询 VA = 0x%08X" % va)
    rva = va - ImageBase
    print("  RVA = 0x%08X - 0x%08X = 0x%08X" % (va, ImageBase, rva))
    s = sec_of(rva)
    off = rva2off(rva)
    print("  所属节 = %s   节内偏移 = 0x%X   文件偏移 = 0x%X" % (s["name"] if s else "?", rva - s["vaddr"] if s else -1, off if off else -1))
    if off is None:
        print("  => 未取得（RVA 不落在任何节内）")
        return
    print("  该处原始 16 字节: %s" % " ".join("%02X" % b for b in buf[off:off+16]))
    if rva in slots:
        e = slots[rva]
        print("  => 命中 FirstThunk 槽")
        print("     所属 DLL            : %s" % e["dll"])
        print("     槽在 FirstThunk 内序号: idx=%d  (FirstThunk项偏移 = %d*4 = 0x%X)" % (e["index"], e["index"], e["index"]*4))
        print("     槽 VA/RVA/文件偏移   : 0x%08X / 0x%08X / 0x%X" % (ImageBase + e["slot_rva"], e["slot_rva"], e["slot_off"]))
        print("     槽当前值(已绑定)     : 0x%08X" % e["cur_val"])
        print("     IAT 指针原始字节     : %s" % " ".join("%02X" % b for b in e["raw"] if True))
        if e["kind"] == "name":
            print("     INT 条目 RVA        : 0x%08X (IMAGE_IMPORT_BY_NAME)" % e["name_rva"])
            print("     Hint/Name 文件偏移   : 0x%X" % e["name_off"])
            print("     Hint                : %d (0x%X)" % (e["hint"], e["hint"]))
            print("     原始字节(Hint+名字)  : %s" % " ".join("%02X" % b for b in buf[e["name_off"]: e["name_off"]+2+len(e["name"])+1]))
            print("     导入名(逐字)         : \"%s\"" % e["name"])
        else:
            print("     按序号导入 Ordinal   : %d" % e["ordinal"])
    else:
        # 相邻槽，帮助定位
        near = [r for r in slots if abs(r - rva) <= 0x10]
        if near:
            print("  => 不属于任何 FirstThunk 槽；附近槽 RVA: %s" % ", ".join("0x%08X" % r for r in sorted(near)))
        else:
            print("  => 不属于任何 FirstThunk 槽（不是 IAT 项）")

args = sys.argv[1:]
if not args:
    args = ["0x7E11C8", "0x7E11CC"]
for a in args:
    query(int(a, 16))
