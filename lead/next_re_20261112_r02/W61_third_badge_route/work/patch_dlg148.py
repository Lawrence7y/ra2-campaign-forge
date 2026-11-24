#!/usr/bin/env python3
# W61 EMPIRICAL PATCH (on a COPY only).
# Insert DLGITEMTEMPLATEEX id=1771 into RT_DIALOG 148, cDlgItems 13->14.
# Strategy: in-place byte insertion in .rsrc, shift all following resource
# data by +0x20, fix up every affected IMAGE_RESOURCE_DATA_ENTRY.OffsetToData,
# grow .rsrc VirtualSize + Resource DataDirectory Size by 0x20, keep file
# length / .detour offset / CheckSum unchanged by consuming 32 bytes of the
# zero padding at the end of .rsrc raw data.
import sys, os, struct, hashlib, shutil
import pefile

ROOT = r"D:\Project\ra2-campaign-forge"
SRC  = os.path.join(ROOT, "ra2bench", "gamemd.exe")
CARD = os.path.join(ROOT, "lead", "next_re_20261112_r02", "W61_third_badge_route")
WORK = os.path.join(CARD, "work")
DST  = os.path.join(WORK, "gamemd_v14r.exe")
os.makedirs(WORK, exist_ok=True)

orig = open(SRC, "rb").read()
pe   = pefile.PE(SRC, fast_load=False)
IB   = pe.OPTIONAL_HEADER.ImageBase
def rva2off(rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None
def u16(o): return struct.unpack_from("<H", orig, o)[0]
def u32(o): return struct.unpack_from("<I", orig, o)[0]

RES_RVA = pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].VirtualAddress
RES_SIZE = pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].Size
RES_OFF  = rva2off(RES_RVA)
RSRC = [s for s in pe.sections if s.Name.rstrip(b"\x00") == b".rsrc"][0]
RSRC_RAW_END = RSRC.PointerToRawData + RSRC.SizeOfRawData
RSRC_USED_END = RSRC.PointerToRawData + RSRC.Misc_VirtualSize
SECTHDR_OFF = pe.FILE_HEADER.SizeOfOptionalHeader + 0x18  # after PE sig (4) + COFF(20); pefile gives dos header
# section header table start: e_lfanew + 4 + sizeof(COFF)=20 + SizeOfOptionalHeader
SECT_START = pe.DOS_HEADER.e_lfanew + 4 + 20 + pe.FILE_HEADER.SizeOfOptionalHeader

print("=== W61 patch: RT_DIALOG 148 insert id=1771 ===")
print("src            = %s" % SRC)
print("orig len       = %d (0x%X)" % (len(orig), len(orig)))
print("orig SHA256    = %s" % hashlib.sha256(orig).hexdigest())
print(".rsrc          RVA=0x%08X fileOff=0x%X VirtSize=0x%X RawSize=0x%X rawEnd=0x%X" %
      (RES_RVA, RES_OFF, RSRC.Misc_VirtualSize, RSRC.SizeOfRawData, RSRC_RAW_END))
print("resource dir   Size=0x%X ; CheckSum=0x%X" % (RES_SIZE, pe.OPTIONAL_HEADER.CheckSum))
print("slack          file 0x%X..0x%X = %d bytes" %
      (RSRC_USED_END, RSRC_RAW_END, RSRC_RAW_END - RSRC_USED_END))
assert all(b == 0 for b in orig[RSRC_USED_END:RSRC_RAW_END]), ".rsrc tail padding is not zero!"
assert all(b == 0 for b in orig[RSRC_RAW_END-32:RSRC_RAW_END]), "last 32 bytes of .rsrc not zero"

# ---- walk resource directory, collect every IMAGE_RESOURCE_DATA_ENTRY ----
data_entries = []   # (path, data_rva, size, cp, data_entry_file_off)
def parse_level(off, depth, path):
    named = u16(off+12); idc = u16(off+14)
    n = named + idc
    for i in range(n):
        e = off + 16 + i*8
        name_val = u32(e); od = u32(e+4)
        is_dir = bool(od & 0x80000000)
        sub = RES_OFF + (od & 0x7FFFFFFF)
        if name_val & 0x80000000:
            noff = RES_OFF + (name_val & 0x7FFFFFFF); ln = u16(noff)
            label = "NAME:" + orig[noff+2:noff+2+ln*2].decode("utf-16-le")
        else:
            label = str(name_val & 0xFFFF)
        if is_dir:
            parse_level(sub, depth+1, path+[label])
        else:
            de = sub
            data_entries.append(dict(path=path+[label], data_rva=u32(de), size=u32(de+4),
                                     cp=u32(de+8), de_off=de))
# top level = type
n = u16(RES_OFF+12) + u16(RES_OFF+14)
for i in range(n):
    e = RES_OFF + 16 + i*8
    nv = u32(e); od = u32(e+4)
    if not (od & 0x80000000): continue
    parse_level(RES_OFF + (od & 0x7FFFFFFF), 1, [str(nv & 0xFFFF)])
print("resource leaves enumerated: %d" % len(data_entries))
assert all(de["de_off"] < 0x487270 for de in data_entries), "a data-entry table lies after dialog data!"
max_rva = max(de["data_rva"] for de in data_entries)
last_end = max(de["data_rva"]+de["size"] for de in data_entries) - RES_RVA
print("max resource data RVA=0x%08X ; last used end (rel)=0x%X (declared 0x%X)" %
      (max_rva, last_end, RES_SIZE))

# ---- locate RT_DIALOG 148 ----
tgt = [de for de in data_entries if de["path"][0]=="5" and de["path"][1]=="148"]
assert len(tgt)==1, "RT_DIALOG 148 not uniquely found"
tgt = tgt[0]
dlg_file_off = rva2off(tgt["data_rva"])
print("RT_DIALOG 148  dataRVA=0x%08X size=%d fileOff=0x%X de_off=0x%X lang=%s" %
      (tgt["data_rva"], tgt["size"], dlg_file_off, tgt["de_off"], tgt["path"][-1]))
assert tgt["size"] == 664
blob = orig[dlg_file_off:dlg_file_off+664]
assert u16(dlg_file_off+16) == 13, "cDlgItems != 13"
open(os.path.join(WORK,"dlg148_orig.bin"),"wb").write(blob)

# ---- build the new DLGITEMTEMPLATEEX (id=1771) ----
# Layout scheme 1 (no other control moved): x=310,y=34, 110x87, beside badge 1770.
NEW_X, NEW_Y, NEW_CX, NEW_CY = 310, 34, 110, 87
item = b"".join([
    struct.pack("<I", 0),            # helpID
    struct.pack("<I", 0x00000020),   # exStyle WS_EX_TRANSPARENT
    struct.pack("<I", 0x50000007),   # style WS_CHILD|WS_VISIBLE|0x07 (same as 1770/1772)
    struct.pack("<hhhh", NEW_X, NEW_Y, NEW_CX, NEW_CY),
    struct.pack("<I", 1771),         # id 0x6EB
    struct.pack("<HH", 0xFFFF, 130), # windowClass ordinal 130 = STATIC
    struct.pack("<H", 0x0000),       # title ordinal 0 = empty
    struct.pack("<H", 0),            # extraCount
])
assert len(item) == 32, item
# verify it mirrors the 1770 item byte-for-byte except geometry+id
ref = blob[0x1C4:0x1E4]
assert item[:12] == ref[:12] and item[24:] == ref[24:] and len(item)==len(ref), "item shape mismatch vs 1770"

NEW_SIZE = 664 + 32
INS_OFF  = dlg_file_off + 664                  # 0x487508
INS_RVA  = RES_RVA + (INS_OFF - RES_OFF)       # 0x783508
DELTA    = 32
print("new item bytes: %s" % item.hex(" "))
print("insert at file 0x%X (RVA 0x%X); new dialog size 664 -> %d" % (INS_OFF, INS_RVA, NEW_SIZE))

# ---- build patched file (length preserved) ----
buf = bytearray(orig)
buf[dlg_file_off+16:dlg_file_off+18] = struct.pack("<H", 14)   # cDlgItems 13 -> 14
patched = (bytes(buf[:INS_OFF]) + item +
           bytes(buf[INS_OFF:RSRC_RAW_END-DELTA]) +
           bytes(buf[RSRC_RAW_END:]))
assert len(patched) == len(orig), "file length changed: %d vs %d" % (len(patched), len(orig))
pbuf = bytearray(patched)

# ---- fix up resource data entries whose data moved by +DELTA ----
nshift = 0
for de in data_entries:
    off = de["de_off"]
    old = struct.unpack_from("<I", pbuf, off)[0]
    if old >= INS_RVA:
        struct.pack_into("<I", pbuf, off, old + DELTA)
        nshift += 1
print("IMAGE_RESOURCE_DATA_ENTRY.OffsetToData shifted (+0x20): %d of %d" % (nshift, len(data_entries)))
# RT_DIALOG 148 size 664 -> 696 (its OffsetToData is before INS_RVA, unchanged)
struct.pack_into("<I", pbuf, tgt["de_off"]+4, NEW_SIZE)
assert struct.unpack_from("<I", pbuf, tgt["de_off"])[0] == tgt["data_rva"]

# ---- grow .rsrc VirtualSize and Resource DataDirectory Size by DELTA ----
rsrc_hdr = None
for i,s in enumerate(pe.sections):
    if s.Name.rstrip(b"\x00") == b".rsrc":
        rsrc_hdr = SECT_START + i*40
        break
assert rsrc_hdr is not None
old_vs = struct.unpack_from("<I", pbuf, rsrc_hdr+8)[0]
struct.pack_into("<I", pbuf, rsrc_hdr+8, old_vs + DELTA)
# OptionalHeader DataDirectory[2] (Resource) size: DOS e_lfanew + 4 + 20 + 96 (data dir offset within opt hdr) + 2*8 + 4
# Standard PE32: DataDirectory starts at OptionalHeader+96; entry 2 at +96+16=+112, Size at +116
opt_off = pe.DOS_HEADER.e_lfanew + 4 + 20
dd2_size_off = opt_off + 96 + 2*8 + 4
old_ds = struct.unpack_from("<I", pbuf, dd2_size_off)[0]
struct.pack_into("<I", pbuf, dd2_size_off, old_ds + DELTA)
# checksum: original is 0 -> leave as-is (loader does not validate for user-mode EXE)
cs_off = opt_off + 64
print("PE fields: rsrc.VirtualSize 0x%X -> 0x%X ; ResourceDir.Size 0x%X -> 0x%X ; CheckSum 0x%X (unchanged) ; SizeOfImage 0x%X (unchanged)" %
      (old_vs, old_vs+DELTA, old_ds, old_ds+DELTA,
       struct.unpack_from("<I", pbuf, cs_off)[0], pe.OPTIONAL_HEADER.SizeOfImage))
assert struct.unpack_from("<I", pbuf, cs_off)[0] == 0

patched_bytes = bytes(pbuf)
open(DST,"wb").write(patched_bytes)
print("\npatched exe     = %s" % DST)
print("patched len     = %d (0x%X)" % (len(patched_bytes), len(patched_bytes)))
print("patched SHA256  = %s" % hashlib.sha256(patched_bytes).hexdigest())

# ---- save patched dialog blob + byte diff ----
new_blob = bytes(buf[dlg_file_off:dlg_file_off+664]) + item
open(os.path.join(WORK,"dlg148_patched.bin"),"wb").write(new_blob)
difflines=[]
difflines.append("# W61 dialog byte diff: RT_DIALOG 148 before/after")
difflines.append("# before=%d bytes (work/dlg148_orig.bin)  after=%d bytes (work/dlg148_patched.bin)" % (664, NEW_SIZE))
difflines.append("# byte-level: N = unchanged, C = changed, + = inserted (new item)")
difflines.append("#")
for i in range(NEW_SIZE):
    b0 = blob[i] if i < 664 else None
    b1 = new_blob[i]
    if b0 is None:
        difflines.append("0x%03X  +   %02X        (new item byte %d/32)" % (i, b1, i-664+1))
    elif b0 != b1:
        difflines.append("0x%03X  C   %02X -> %02X  (cDlgItems 13 -> 14)" % (i, b0, b1))
    else:
        difflines.append("0x%03X  N   %02X" % (i, b1))
open(os.path.join(CARD,"EVIDENCE","dialog_bytes_diff.txt"),"w",encoding="utf-8").write("\n".join(difflines)+"\n")
print("dialog byte diff -> EVIDENCE/dialog_bytes_diff.txt (%d lines)" % len(difflines))

# ---- also emit a compact structural diff ----
compact=[]
compact.append("offset  before            after             note")
compact.append("0x000  0d 00             0e 00             cDlgItems 13 -> 14")
compact.append("0x298  <EOF 664>         +32 bytes         new DLGITEMTEMPLATEEX id=1771")
compact.append("       item = %s" % item.hex(" "))
compact.append("new item decode: helpID=0 exStyle=0x20 style=0x50000007 x=%d y=%d cx=%d cy=%d id=1771(0x6EB) class=#130 STATIC title=ord0 extra=0" % (NEW_X,NEW_Y,NEW_CX,NEW_CY))
open(os.path.join(CARD,"EVIDENCE","dialog_struct_diff.txt"),"w",encoding="utf-8").write("\n".join(compact)+"\n")
print("DONE patch. exit=0")
