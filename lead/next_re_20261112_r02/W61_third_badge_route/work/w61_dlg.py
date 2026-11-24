#!/usr/bin/env python3
# W61 DLGTEMPLATEEX parser for RT_DIALOG 148 (and generic).
# Usage: python w61_dlg.py <exe> [outprefix]
# Prints full header + every item with byte offset, id, class, style, x,y,cx,cy, title, extra.
import sys, struct, hashlib
import pefile

EXE = sys.argv[1]
PREFIX = sys.argv[2] if len(sys.argv) > 2 else None
data = open(EXE, "rb").read()
pe = pefile.PE(EXE, fast_load=False)
IB = pe.OPTIONAL_HEADER.ImageBase

def rva2off(rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None

RES_RVA = pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].VirtualAddress
RES_OFF = rva2off(RES_RVA)
def u16(o): return struct.unpack_from("<H", data, o)[0]
def u32(o): return struct.unpack_from("<I", data, o)[0]

def find_resource(type_id, res_id, lang=None):
    # walk top-level dir -> type/name/lang -> data entry
    n = u16(RES_OFF+12)+u16(RES_OFF+14)
    for i in range(n):
        e = RES_OFF+16+i*8
        nv = u32(e); od = u32(e+4)
        tid = nv & 0xFFFF if not (nv & 0x80000000) else None
        if tid != type_id or not (od & 0x80000000): continue
        d2 = RES_OFF + (od & 0x7FFFFFFF)
        n2 = u16(d2+12)+u16(d2+14)
        for j in range(n2):
            e2 = d2+16+j*8
            nv2 = u32(e2); od2 = u32(e2+4)
            rid = nv2 & 0xFFFF if not (nv2 & 0x80000000) else None
            if rid != res_id or not (od2 & 0x80000000): continue
            d3 = RES_OFF + (od2 & 0x7FFFFFFF)
            n3 = u16(d3+12)+u16(d3+14)
            for k in range(n3):
                e3 = d3+16+k*8
                nv3 = u32(e3); od3 = u32(e3+4)
                lid = nv3 & 0xFFFF if not (nv3 & 0x80000000) else None
                if lang is not None and lid != lang: continue
                if od3 & 0x80000000:  # not a dir
                    continue
                de = RES_OFF + (od3 & 0x7FFFFFFF)
                drva = u32(de); sz = u32(de+4); cp = u32(de+8)
                return dict(type=type_id, id=res_id, lang=lid, data_rva=drva,
                            size=sz, cp=cp, file_off=rva2off(drva),
                            dir_off=d3, dir_entry_off=e3, data_entry_off=de,
                            name_dir_off=d2, name_entry_off=e2, type_entry_off=e)
    return None

def align4(o): return (o+3) & ~3

class R:
    def __init__(self, blob, base=0):
        self.b = blob; self.o = base
    def u16(self):
        v = struct.unpack_from("<H", self.b, self.o)[0]; self.o += 2; return v
    def u32(self):
        v = struct.unpack_from("<I", self.b, self.o)[0]; self.o += 4; return v
    def i16(self):
        v = struct.unpack_from("<h", self.b, self.o)[0]; self.o += 2; return v
    def sz(self):
        # ordinal or string
        first = u16_at(self.b, self.o)
        if first == 0x0000:
            self.o += 2; return ("ordinal", 0)
        if first == 0xFFFF:
            self.o += 2
            v = u16_at(self.b, self.o); self.o += 2
            return ("ordinal", v)
        # UTF-16 string
        chars = []
        while True:
            c = u16_at(self.b, self.o); self.o += 2
            if c == 0: break
            chars.append(chr(c))
        return ("string", "".join(chars))
    def align(self): self.o = align4(self.o)
    def skip(self, n): self.o += n

def u16_at(b,o): return struct.unpack_from("<H", b, o)[0]

def parse_dlg(blob, verbose=True):
    r = R(blob, 0)
    dlgVer = r.u16(); signature = r.u16(); helpID = r.u32()
    exStyle = r.u32(); style = r.u32(); cDlgItems = r.u16()
    x = r.i16(); y = r.i16(); cx = r.i16(); cy = r.i16()
    hdr = dict(dlgVer=dlgVer, signature=signature, helpID=helpID, exStyle=exStyle,
               style=style, cDlgItems=cDlgItems, x=x, y=y, cx=cx, cy=cy)
    if verbose:
        print("DLGTEMPLATEEX header: dlgVer=0x%04X signature=0x%04X helpID=%d exStyle=0x%08X style=0x%08X cDlgItems=%d box=(%d,%d,%d,%d)" %
              (dlgVer,signature,helpID,exStyle,style,cDlgItems,x,y,cx,cy))
    menu = r.sz(); wclass = r.sz(); title = r.sz()
    if verbose: print("  menu=%r windowClass=%r title=%r" % (menu, wclass, title))
    if style & 0x40:  # DS_SETFONT
        pointsize = r.u16(); weight = r.u16(); italic = r.u8() if False else struct.unpack_from("<B",blob,r.o)[0]; r.o+=1
        charset = struct.unpack_from("<B",blob,r.o)[0]; r.o+=1
        face = r.sz()
        if verbose: print("  font: pointsize=%d weight=%d italic=%d charset=%d typeface=%r" % (pointsize,weight,italic,charset,face))
    hdr["font_end_off"] = r.o
    items = []
    for i in range(cDlgItems):
        r.align()
        start = r.o
        ihelp = r.u32(); iex = r.u32(); istyle = r.u32()
        ix = r.i16(); iy = r.i16(); icx = r.i16(); icy = r.i16()
        iid = r.u32()
        icls = r.sz(); ititle = r.sz()
        extra = r.u16()
        extra_bytes = blob[r.o:r.o+extra]
        r.skip(extra)
        end = r.o
        items.append(dict(idx=i, start=start, end=end, helpID=ihelp, exStyle=iex,
                          style=istyle, x=ix,y=iy,cx=icx,cy=icy,id=iid,
                          cls=icls, title=ititle, extra=extra, extra_bytes=extra_bytes))
        if verbose:
            print("  [%2d] off=0x%03X..0x%03X id=%-6d cls=%-22r style=0x%08X pos=(%3d,%3d) size=(%3d,%3d) exStyle=0x%08X title=%r extra=%d%s" %
                  (i, start, end, iid, icls, istyle, ix,iy,icx,icy, iex, ititle, extra,
                   (" extra_bytes="+extra_bytes.hex()) if extra else ""))
    r.align()
    trailing = len(blob)-r.o
    if verbose:
        print("  parsed_end_off=0x%X  blob_len=0x%X  trailing=%d" % (r.o, len(blob), trailing))
    hdr["parsed_end"] = r.o
    hdr["trailing"] = trailing
    return hdr, items

r = find_resource(5, 148, 1033)
print("=== RT_DIALOG 148 DATA ENTRY ===")
print(r)
blob = data[r["file_off"]:r["file_off"]+r["size"]]
print("blob_len=%d sha256=%s" % (len(blob), hashlib.sha256(blob).hexdigest()))
if PREFIX:
    open(PREFIX+"_dialog.bin","wb").write(blob)
print("=== PARSE ===")
hdr, items = parse_dlg(blob)
print("=== SUMMARY ===")
print("cDlgItems=%d  items=%d  trailing=%d" % (hdr["cDlgItems"], len(items), hdr["trailing"]))
print("ids=%s" % [it["id"] for it in items])
print("1770=%s 1771=%s 1772=%s" % (any(i["id"]==1770 for i in items), any(i["id"]==1771 for i in items), any(i["id"]==1772 for i in items)))
