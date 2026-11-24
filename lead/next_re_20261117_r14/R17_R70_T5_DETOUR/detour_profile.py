#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R38-T5-DETOUR 复算脚本（只读 gamemd.exe；不写 exe；不写任何受保护文件）。

口径声明（与 REPORT.md 一致）：
  - 地址（VA/RVA/节头 VirtualAddress 字段）一律 0x + 大写十六进制。
  - 文件偏移（offset）一律 0x + 大写十六进制（与地址同风格，已统一）。
  - 节头 VirtualAddress 字段存的是 RVA；真实 VA = ImageBase + RVA。
    本任务卡沿用的 "VA=0x793000" 即该字段值（RVA），真 VA=0xB93000。
  - "可读 ASCII 串" = 连续可打印 ASCII 字节(0x20..0x7E)的极大游程，长度 >= 6。
  - 函数序言/ret 字节模式仅作"结构画像"计数，**不作为函数入口判据**
    （纪律：禁止按字节扫 E8/C3/C2 当函数入口判据）。
  - 取不到的量打印 UNKNOWN，不臆造；不对"谁改的/为什么改"做任何定性推断。

用法:  python detour_profile.py > detour_profile_out.txt
"""
import struct, os, hashlib, sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
HEX = lambda b: " ".join("%02X" % x for x in b)

buf = open(EXE, "rb").read()

def u16(o): return struct.unpack_from("<H", buf, o)[0]
def u32(o): return struct.unpack_from("<I", buf, o)[0]

print("=== 文件身份 ===")
print("path   :", EXE)
print("size   : 0x%X (%d)" % (len(buf), len(buf)))
print("sha256 :", hashlib.sha256(buf).hexdigest().upper())

# ---------- DOS / PE 头 ----------
print("\n=== DOS / PE 头 ===")
e_lfanew = u32(0x3C)
assert buf[e_lfanew:e_lfanew+4] == b"PE\0\0", "not PE"
coff = e_lfanew + 4
machine = u16(coff)
nsec = u16(coff + 2)
TimeDateStamp = u32(coff + 4)
SizeOfOptHdr = u16(coff + 16)
COFFChar = u16(coff + 18)
opt = coff + 20
magic = u16(opt)
is64 = (magic == 0x20B)
ImageBase = struct.unpack_from("<Q", buf, opt+24)[0] if is64 else u32(opt + 28)
SectionAlignment = u32(opt + 32)
FileAlignment = u32(opt + 36)
SizeOfImage = u32(opt + 56)
SizeOfHeaders = u32(opt + 60)
CheckSum = u32(opt + 64)
NumRvaAndSizes = u32(opt + (108 if is64 else 92))
dd_off = opt + (112 if is64 else 96)

def dd(i): return (u32(dd_off + 8*i), u32(dd_off + 8*i + 4))

print("e_lfanew=0x%X Machine=0x%04X Magic=0x%03X ImageBase=0x%X" %
      (e_lfanew, machine, magic, ImageBase))
print("NumberOfSections=%d SizeOfOptHdr=0x%X COFFChar=0x%04X" % (nsec, SizeOfOptHdr, COFFChar))
print("TimeDateStamp=0x%08X CheckSum(header)=0x%08X" % (TimeDateStamp, CheckSum))
print("SectionAlign=0x%X FileAlign=0x%X SizeOfImage=0x%X SizeOfHeaders=0x%X NumRvaAndSizes=%d" %
      (SectionAlignment, FileAlignment, SizeOfImage, SizeOfHeaders, NumRvaAndSizes))

# ---------- 节表（全字段） ----------
CHAR_BITS = [(0x00000020,"CNT_CODE"),(0x00000040,"CNT_INITIALIZED_DATA"),
             (0x00000080,"CNT_UNINITIALIZED_DATA"),(0x00000200,"INFO"),
             (0x00000100,"LNK_NRELOC_OVFL"),(0x00080000,"MEM_EXECUTE"),
             (0x40000000,"MEM_READ"),(0x80000000,"MEM_WRITE"),
             (0x10000000,"MEM_SHARED"),(0x20000000,"MEM_DISCARDABLE")]
def decode_char(c): return "|".join(n for b,n in CHAR_BITS if c & b)

sec_tab = opt + SizeOfOptHdr
secs = []
print("\n=== 节表（全字段；VirtualAddress 字段是 RVA，真 VA=ImageBase+RVA）===")
for i in range(nsec):
    b = sec_tab + 40*i
    name = buf[b:b+8].rstrip(b"\0").decode("latin1")
    vsize = u32(b+8); rva = u32(b+12); rsize = u32(b+16); raddr = u32(b+20)
    char = u32(b+36)
    secs.append(dict(i=i, name=name, vsize=vsize, rva=rva, va=rva+ImageBase,
                     rsize=rsize, raddr=raddr, char=char))
    print("  [%d] %-8s VirtualSize=0x%08X VirtualAddress(RVA)=0x%08X (真VA=0x%08X) "
          "SizeOfRawData=0x%08X PointerToRawData=0x%08X Characteristics=0x%08X (%s)" %
          (i, name, vsize, rva, rva+ImageBase, rsize, raddr, char, decode_char(char)))

def rva2sec(rva):
    for s in secs:
        if s["rva"] <= rva < s["rva"] + max(s["vsize"], s["rsize"]):
            return s
    return None

def rva2off(rva):
    for s in secs:
        if s["rva"] <= rva < s["rva"] + max(s["vsize"], s["rsize"]):
            off = rva - s["rva"] + s["raddr"]
            return off if off < len(buf) else None
    return None

# ---------- 节画像 ----------
def profile_section(name, tag):
    s = next((x for x in secs if x["name"] == name), None)
    print("\n=== %s · 节画像: %s ===" % (tag, name))
    if s is None:
        print("  UNKNOWN: 节不存在"); return
    print("  节头: VirtualSize=0x%X VirtualAddress(RVA)=0x%X 真VA=0x%X "
          "SizeOfRawData=0x%X PointerToRawData=0x%X Characteristics=0x%X(%s)" %
          (s["vsize"], s["rva"], s["va"], s["rsize"], s["raddr"], s["char"], decode_char(s["char"])))
    file_backed = min(s["rsize"], len(buf) - s["raddr"])
    if s["vsize"] > s["rsize"]:
        print("  注: vsize(0x%X) > rsize(0x%X)，文件支撑仅 0x%X 字节" %
              (s["vsize"], s["rsize"], file_backed))
    elif s["rsize"] > s["vsize"]:
        print("  注: rsize(0x%X) > vsize(0x%X)，超出 vsize 的 0x%X 字节为零填充；按卡要求画像取 vsize" %
              (s["rsize"], s["vsize"], s["rsize"]-s["vsize"]))
    n = min(s["vsize"], file_backed)
    raw = buf[s["raddr"]:s["raddr"]+n]
    nonzero_v = sum(1 for x in raw if x != 0)
    print("  画像字节数(取 min(vsize,文件支撑))=0x%X (%d)" % (n, n))
    print("  非零字节=%d/%d ; 零字节=%d/%d" % (nonzero_v, n, n-nonzero_v, n))
    if s["rsize"] > s["vsize"]:
        tail = buf[s["raddr"]+s["vsize"]:s["raddr"]+s["rsize"]]
        print("  vsize..rsize 尾段 0x%X 字节非零数=%d(应全零)" % (len(tail), sum(1 for x in tail if x)))
    print("  前 64 字节 @off 0x%X: %s" % (s["raddr"], HEX(raw[:64])))

    strings = []; start = None
    for idx, x in enumerate(raw):
        if 0x20 <= x <= 0x7E:
            if start is None: start = idx
        else:
            if start is not None and idx-start >= 6:
                strings.append((start, idx, raw[start:idx].decode("latin1")))
            start = None
    if start is not None and n-start >= 6:
        strings.append((start, n, raw[start:n].decode("latin1")))
    print("  可读ASCII串(>=6) 共 %d 条:" % len(strings))
    for a, b, t in strings:
        print("    +0x%05X (off 0x%X, len=%d): \"%s\"" % (a, s["raddr"]+a, b-a, t))

    cnt_558BEC = sum(1 for k in range(len(raw)-2) if raw[k:k+3] == b"\x55\x8b\xec")
    cnt_83EC   = sum(1 for k in range(len(raw)-1) if raw[k:k+2] == b"\x83\xec")
    cnt_C3 = sum(1 for x in raw if x == 0xC3)
    cnt_C2 = sum(1 for x in raw if x == 0xC2)
    print("  字节模式画像(结构画像, 非函数入口判据): 55 8B EC=%d ; 83 EC=%d ; 0xC3字节=%d ; 0xC2字节=%d" %
          (cnt_558BEC, cnt_83EC, cnt_C3, cnt_C2))

    mz = [k for k in range(len(raw)-1) if raw[k:k+2] == b"MZ"]
    print("  'MZ'(0x4D5A) 出现位置(节内相对) 共 %d 处: %s" %
          (len(mz), ", ".join("0x%X" % x for x in mz[:40]) + (" ..." if len(mz)>40 else "")))

    # 画像对象恰为 .detour 时，展开 MZ blob 的机械事实
    if name == ".detour" and mz:
        m = mz[0]; mzoff = s["raddr"] + m
        e = u32(mzoff + 0x3C)
        print("  MZ blob @节内+0x%X(off 0x%X): 前16字节=%s" % (m, mzoff, HEX(buf[mzoff:mzoff+16])))
        print("    MZ+0x40..MZ+0x70 原始字节: %s" % HEX(buf[mzoff+0x40:mzoff+0x70]))
        # DOS 桩串取自本画像已算出的 ASCII 串（落在 MZ blob 范围内的第一条）
        for a, b, t in strings:
            abs_a = s["raddr"] + a
            if mzoff <= abs_a < mzoff + 0x100 and "This program" in t:
                print("    DOS桩串 @节内+0x%X(off 0x%X): \"%s\"" % (a, abs_a, t))
        print("    e_lfanew(MZ+0x3C)=0x%X -> abs off 0x%X ; 该处8字节=%s (是否 PE\\0\\0: %s)" %
              (e, mzoff+e, HEX(buf[mzoff+e:mzoff+e+8]), buf[mzoff+e:mzoff+e+4] == b"PE\0\0"))
    return s

det = profile_section(".detour", "Q1")
dat = profile_section(".data", "Q5-正控")

# ---------- Q2 导入表节归属 ----------
print("\n=== Q2 · 导入表三项节归属（逐项节名） ===")
IMP_RVA, IMP_SZ = dd(1)
print("DataDirectory[1] IMPORT RVA=0x%08X Size=0x%X off=0x%X" %
      (IMP_RVA, IMP_SZ, rva2off(IMP_RVA) if rva2off(IMP_RVA) is not None else 0))
def sn(rva):
    s = rva2sec(rva); return s["name"] if s else "UNKNOWN"
for label, rva in [("Import Directory", 0x7955C0),
                   ("KERNEL32 FirstThunk", 0x3E10D0),
                   ("IBN(InterlockedIncrement)", 0x7941F0)]:
    s = rva2sec(rva); off = rva2off(rva)
    print("  %-28s RVA=0x%08X -> 节=%-10s 节内偏移=0x%X 文件偏移=0x%X" %
          (label, rva, s["name"] if s else "UNKNOWN",
           (rva-s["rva"]) if s else -1, off if off is not None else 0))

p = rva2off(IMP_RVA)
print("  --- 全部 IMAGE_IMPORT_DESCRIPTOR 的 OFT/FirstThunk/NameRVA 节归属 ---")
i = 0
while p is not None and (p+20*i+20) <= len(buf):
    o = p+20*i
    oft,tds,fc,nr,ft = u32(o),u32(o+4),u32(o+8),u32(o+12),u32(o+16)
    if (oft,tds,fc,nr,ft)==(0,0,0,0,0): break
    no = rva2off(nr)
    dll = buf[no:buf.index(b"\0",no)].decode("latin1") if no is not None else "UNKNOWN"
    print("    [%2d] %-20s OFT=0x%08X(%s) FirstThunk=0x%08X(%s) NameRVA=0x%08X(%s)" %
          (i,dll,oft,sn(oft) if oft else "-",ft,sn(ft) if ft else "-",nr,sn(nr)))
    i += 1

# IBN 逐字复算（独立于 T1）
print("  --- IBN@0x7941F0 逐字复算 ---")
no = rva2off(0x7941F0)
raw24 = buf[no:no+24]
hint = u16(no)
name = buf[no+2:buf.index(b"\0",no+2)].decode("latin1")
print("    off=0x%X raw=%s ; Hint=0x%X(%d) ; name=\"%s\"" % (no, HEX(raw24), hint, hint, name))

# ---------- Q3 机械非标准迹象 ----------
print("\n=== Q3 · 可机械判定的非标准迹象 ===")
print("  节数=%d ; 节名=%s ; 标准4节基线=.text/.rdata/.data/.rsrc" % (nsec,[s["name"] for s in secs]))
print("  '.detour' 是否为标准 MSVC 链接产物命名: UNKNOWN(单文件无法判定链接器常规命名，不下定性结论)")
print("  TimeDateStamp=0x%08X ; CheckSum(header)=0x%08X" % (TimeDateStamp, CheckSum))
rvas=[s["rva"] for s in secs]
print("  节表按 VirtualAddress(RVA) 升序? %s ; 序列=%s" %
      ("是" if rvas==sorted(rvas) else "否", ["0x%X"%v for v in rvas]))
print("  --- 虚拟区间(RVA..RVA+max(vsize,rsize)) ---")
for s in secs: print("    %-8s 0x%08X..0x%08X" % (s["name"],s["rva"],s["rva"]+max(s["vsize"],s["rsize"])))
print("  --- 原始区间(raw..raw+rsize) ---")
for s in secs: print("    %-8s raw 0x%08X..0x%08X" % (s["name"],s["raddr"],s["raddr"]+s["rsize"]))
def ov(lo,hi):
    return [(secs[x]["name"],secs[y]["name"]) for x in range(len(secs)) for y in range(x+1,len(secs))
            if lo(secs[x])<hi(secs[y]) and lo(secs[y])<hi(secs[x])]
print("  虚拟区间重叠对: %s" % (ov(lambda s:s["rva"],lambda s:s["rva"]+max(s["vsize"],s["rsize"])) or "无"))
print("  原始区间重叠对: %s" % (ov(lambda s:s["raddr"],lambda s:s["raddr"]+s["rsize"]) or "无"))
last=max(secs,key=lambda s:s["rva"]+max(s["vsize"],s["rsize"]))
end_rva=((last["rva"]+max(last["vsize"],last["rsize"])+SectionAlignment-1)//SectionAlignment)*SectionAlignment
print("  SizeOfImage=0x%X ; 末节(%s)对齐末RVA=0x%X ; 相等? %s" %
      (SizeOfImage,last["name"],end_rva,SizeOfImage==end_rva))
