#!/usr/bin/env python3
# W61 recon: PE layout, resource directory inventory, RT_DIALOG 148 extraction,
# capstone disassembly of WndProc 0x52EC00 region, and .data string dump.
# OFFLINE / READ-ONLY on the source exe. All outputs go to stdout (captured).
import sys, struct, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = sys.argv[1] if len(sys.argv) > 1 else r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe"

pe = pefile.PE(EXE, fast_load=False)
IB = pe.OPTIONAL_HEADER.ImageBase
print("=== PE HEADER ===")
print("ImageBase      : 0x%08X" % IB)
print("SizeOfImage    : 0x%08X" % pe.OPTIONAL_HEADER.SizeOfImage)
print("SizeOfHeaders  : 0x%08X" % pe.OPTIONAL_HEADER.SizeOfHeaders)
print("CheckSum       : 0x%08X" % pe.OPTIONAL_HEADER.CheckSum)
print("FileAlignment  : 0x%X" % pe.OPTIONAL_HEADER.FileAlignment)
print("SectionAlignment: 0x%X" % pe.OPTIONAL_HEADER.SectionAlignment)
print("NumberOfSections: %d" % pe.FILE_HEADER.NumberOfSections)
print("Machine        : 0x%X" % pe.FILE_HEADER.Machine)
print("Characteristics: 0x%X" % pe.FILE_HEADER.Characteristics)
print("--- sections (Name VA RVA(VirtAddr) VirtualSize RawSize PtrRaw) ---")
for s in pe.sections:
    nm = s.Name.rstrip(b"\x00").decode("latin1")
    print("  %-8s VA=0x%08X RVA=0x%08X VS=0x%08X RS=0x%08X PTR=0x%08X  char=0x%08X" %
          (nm, IB + s.VirtualAddress, s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData,
           s.PointerToRawData, s.Characteristics))

data = open(EXE, "rb").read()
print("FileLength     : %d (0x%X)" % (len(data), len(data)))
print("SHA256         : %s" % hashlib.sha256(data).hexdigest())

def rva2off(rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None

def va2off(va):
    return rva2off(va - IB)

# ---- resource directory inventory ----
print("\n=== RESOURCE TYPES ===")
RT = {1:"RT_CURSOR",2:"RT_BITMAP",3:"RT_ICON",4:"RT_MENU",5:"RT_DIALOG",6:"RT_STRING",
      7:"RT_FONTDIR",8:"RT_FONT",9:"RT_ACCELERATOR",10:"RT_RCDATA",11:"RT_MESSAGETABLE",
      12:"RT_GROUP_CURSOR",14:"RT_GROUP_ICON",16:"RT_VERSION",24:"RT_MANIFEST"}
# resource dir at DataDirectory[IMAGE_DIRECTORY_ENTRY_RESOURCE]
RES_RVA = pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].VirtualAddress
RES_SIZE = pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].Size
print("Resource Dir RVA=0x%08X Size=0x%X (file off 0x%X)" % (RES_RVA, RES_SIZE, rva2off(RES_RVA)))
RES_OFF = rva2off(RES_RVA)

def read_u16(o): return struct.unpack_from("<H", data, o)[0]
def read_u32(o): return struct.unpack_from("<I", data, o)[0]

def parse_level(off, depth, path, out):
    # off points to IMAGE_RESOURCE_DIRECTORY (16 bytes header + N entries)
    named = read_u16(off+12); idc = read_u16(off+14)
    n = named + idc
    base = off + 16
    for i in range(n):
        e = base + i*8
        name_val = read_u32(e); off_to_data = read_u32(e+4)
        is_dir = bool(off_to_data & 0x80000000)
        sub = RES_OFF + (off_to_data & 0x7FFFFFFF)
        if name_val & 0x80000000:
            # named
            noff = RES_OFF + (name_val & 0x7FFFFFFF)
            ln = read_u16(noff)
            nm = data[noff+2:noff+2+ln*2].decode("utf-16-le")
            label = "NAME:%s" % nm
        else:
            label = str(name_val & 0xFFFF)
        if is_dir:
            parse_level(sub, depth+1, path+[label], out)
        else:
            # IMAGE_RESOURCE_DATA_ENTRY
            de = sub
            data_rva = read_u32(de); size = read_u32(de+4); cp = read_u32(de+8)
            doff = rva2off(data_rva)
            out.append((path+[label], data_rva, size, cp, doff))

resources = []
# top-level: type dir
named = read_u16(RES_OFF+12); idc = read_u16(RES_OFF+14)
n = named+idc
for i in range(n):
    e = RES_OFF+16+i*8
    name_val = read_u32(e); off_to_data = read_u32(e+4)
    sub = RES_OFF + (off_to_data & 0x7FFFFFFF)
    if name_val & 0x80000000:
        noff = RES_OFF + (name_val & 0x7FFFFFFF); ln = read_u16(noff)
        tname = data[noff+2:noff+2+ln*2].decode("utf-16-le")
    else:
        tid = name_val & 0xFFFF
        tname = RT.get(tid, "TYPE_%d" % tid)
    print("  TYPE %-16s (id=%s) -> dirOff=0x%X" % (tname, name_val & 0xFFFF if not (name_val & 0x80000000) else "named", sub))
    if off_to_data & 0x80000000:
        parse_level(sub, 1, [tname], resources)

from collections import Counter
cnt = Counter(r[0][0] for r in resources)
print("--- per-type leaf counts ---")
for k,v in sorted(cnt.items()):
    print("  %-16s %d" % (k, v))
print("TOTAL resource leaves: %d" % len(resources))

# ---- RT_DIALOG 148 ----
print("\n=== RT_DIALOG 148 ===")
dlg = [r for r in resources if r[0][0]=="RT_DIALOG" and r[0][-1]=="148"]
for r in dlg:
    path, data_rva, size, cp, doff = r
    print("  path=%s dataRVA=0x%08X size=%d cp=%d fileOff=0x%X" % ("/".join(path), data_rva, size, cp, doff))
    blob = data[doff:doff+size]
    print("  first 64 bytes: %s" % blob[:64].hex(" "))
    open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W61_third_badge_route\work\dlg148_orig.bin","wb").write(blob)
    print("  [written] work/dlg148_orig.bin (%d bytes)" % len(blob))

# ---- RT_BITMAP / RT_RCDATA inventory (candidate badge art) ----
print("\n=== candidate image resource types (first 40 leaves each) ===")
for typ in ["RT_BITMAP","RT_RCDATA","RT_ICON","RT_GROUP_ICON","RT_MANIFEST"]:
    rs = [r for r in resources if r[0][0]==typ]
    print("  %s: %d leaves" % (typ, len(rs)))
    for r in rs[:40]:
        print("     id=%-8s size=%-8d dataRVA=0x%08X fileOff=0x%X" % ("/".join(r[0][1:]), r[2], r[1], r[4]))

# ---- .data strings near 0x825C90 ----
print("\n=== .data strings around 0x825C68..0x825CC0 ===")
for va in range(0x825C60, 0x825CC0, 4):
    o = va2off(va)
    if o is None: continue
    w = read_u32(o)
    if 0x800000 <= w < 0x900000:
        so = va2off(w)
        if so:
            s = data[so:so+40].split(b"\x00")[0]
            print("  [0x%08X] -> 0x%08X : %r" % (va, w, s))
# raw string bytes region
o = va2off(0x825C80)
if o:
    print("  RAW 0x825C80..0x825CC0: %s" % data[o:o+64].hex(" "))
    print("  ASCII: %r" % data[o:o+64])

# ---- disassembly WndProc ----
print("\n=== DISASM 0x52EC00 .. 0x52F3E8 ===")
start_va = 0x52EC00; end_va = 0x52F3E8
o = va2off(start_va)
code = data[o:o+(end_va-start_va)]
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
for ins in md.disasm(code, start_va):
    print("  0x%08X  %-22s %s" % (ins.address, ins.bytes.hex(" "), ins.mnemonic+" "+ins.op_str))
print("=== END DISASM ===")
