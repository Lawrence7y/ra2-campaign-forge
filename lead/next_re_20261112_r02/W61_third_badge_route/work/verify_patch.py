#!/usr/bin/env python3
# W61 READBACK VALIDATION of the patched COPY (own PE resource walker + own
# DLGTEMPLATEEX parser). Also verifies the source exe was NOT modified.
import sys, os, struct, hashlib
import pefile

ROOT = r"D:\Project\ra2-campaign-forge"
SRC  = os.path.join(ROOT,"ra2bench","gamemd.exe")
DST  = os.path.join(ROOT,"lead","next_re_20261112_r02","W61_third_badge_route","work","gamemd_v14r.exe")
ORIG_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

for path in (SRC, DST):
    assert os.path.exists(path), path
src = open(SRC,"rb").read(); dst = open(DST,"rb").read()
print("=== W61 READBACK ===")
print("source  %s" % SRC)
print("  len=%d sha256=%s" % (len(src), hashlib.sha256(src).hexdigest()))
assert hashlib.sha256(src).hexdigest()==ORIG_SHA, "SOURCE EXE WAS MODIFIED!"
print("  [OK] source exe SHA256 unchanged (read-only respected)")
print("patched %s" % DST)
print("  len=%d sha256=%s" % (len(dst), hashlib.sha256(dst).hexdigest()))
assert len(dst)==len(src), "file length changed"

pe = pefile.PE(DST, fast_load=False)
IB = pe.OPTIONAL_HEADER.ImageBase
print("\n=== PE header sanity (pefile) ===")
print("  ImageBase=0x%08X SizeOfImage=0x%X CheckSum=0x%X sections=%d" %
      (IB, pe.OPTIONAL_HEADER.SizeOfImage, pe.OPTIONAL_HEADER.CheckSum, pe.FILE_HEADER.NumberOfSections))
rs=[s for s in pe.sections if s.Name.rstrip(b"\x00")==b".rsrc"][0]
print("  .rsrc VirtSize=0x%X RawSize=0x%X PtrRaw=0x%X" %
      (rs.Misc_VirtualSize, rs.SizeOfRawData, rs.PointerToRawData))
print("  Resource DataDirectory RVA=0x%X Size=0x%X" %
      (pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].VirtualAddress, pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].Size))
assert rs.Misc_VirtualSize==0x18148
assert pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].Size==0x18148
assert pe.OPTIONAL_HEADER.CheckSum==0
print("  [OK] PE header fields consistent")

def rva2off(rva):
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(rva-s.VirtualAddress)
    return None
def u16(o): return struct.unpack_from("<H",dst,o)[0]
def u32(o): return struct.unpack_from("<I",dst,o)[0]

RES_RVA = pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].VirtualAddress
RES_OFF = rva2off(RES_RVA)

# ---- OWN resource directory walker ----
leaves=[]
def walk_dir(off,path):
    n=u16(off+12)+u16(off+14)
    for i in range(n):
        e=off+16+i*8
        nv=u32(e); od=u32(e+4)
        sub=RES_OFF+(od&0x7FFFFFFF)
        if nv&0x80000000:
            no=RES_OFF+(nv&0x7FFFFFFF); ln=u16(no)
            lab="N:"+dst[no+2:no+2+ln*2].decode("utf-16-le")
        else: lab=str(nv&0xFFFF)
        if od&0x80000000:
            walk_dir(sub,path+[lab])
        else:
            leaves.append(dict(path=path+[lab], rva=u32(sub), size=u32(sub+4), cp=u32(sub+8), de=sub))
n=u16(RES_OFF+12)+u16(RES_OFF+14)
for i in range(n):
    e=RES_OFF+16+i*8
    nv=u32(e); od=u32(e+4)
    if od&0x80000000:
        walk_dir(RES_OFF+(od&0x7FFFFFFF),[str(nv&0xFFFF)])
print("\n=== OWN resource directory walk ===")
print("  leaves=%d" % len(leaves))
tgt=[l for l in leaves if l["path"][0]=="5" and l["path"][1]=="148"]
assert len(tgt)==1, "RT_DIALOG 148 not found by own walker"
t=tgt[0]
fo=rva2off(t["rva"])
print("  RT_DIALOG 148: dataRVA=0x%08X fileOff=0x%X size=%d cp=%d dataEntryOff=0x%X" %
      (t["rva"],fo,t["size"],t["cp"],t["de"]))
assert t["size"]==696, "size != 696"
blob=dst[fo:fo+t["size"]]
print("  blob sha256=%s" % hashlib.sha256(blob).hexdigest())

# ---- OWN DLGTEMPLATEEX parser ----
class R:
    def __init__(s,b): s.b=b; s.o=0
    def u16(s): v=struct.unpack_from("<H",s.b,s.o)[0]; s.o+=2; return v
    def u32(s): v=struct.unpack_from("<I",s.b,s.o)[0]; s.o+=4; return v
    def i16(s): v=struct.unpack_from("<h",s.b,s.o)[0]; s.o+=2; return v
def u16_at(b,o): return struct.unpack_from("<H",b,o)[0]
def sz_read(r):
    f=u16_at(r.b,r.o)
    if f==0: r.o+=2; return ("ordinal",0)
    if f==0xFFFF:
        r.o+=2; v=u16_at(r.b,r.o); r.o+=2; return ("ordinal",v)
    cs=[]
    while True:
        c=u16_at(r.b,r.o); r.o+=2
        if c==0: break
        cs.append(chr(c))
    return ("string","".join(cs))
r=R(blob)
dlgVer=r.u16(); sig=r.u16(); helpID=r.u32(); exStyle=r.u32(); style=r.u32()
cnt=r.u16(); x=r.i16(); y=r.i16(); cx=r.i16(); cy=r.i16()
print("\n=== OWN DLGTEMPLATEEX parse (patched) ===")
print("  dlgVer=0x%04X sig=0x%04X helpID=%d exStyle=0x%08X style=0x%08X cDlgItems=%d box=(%d,%d,%d,%d)" %
      (dlgVer,sig,helpID,exStyle,style,cnt,x,y,cx,cy))
menu=sz_read(r); wc=sz_read(r); title=sz_read(r)
print("  menu=%r class=%r title=%r" % (menu,wc,title))
if style&0x40:
    ps=r.u16(); w=r.u16(); it=blob[r.o]; r.o+=1; cs=blob[r.o]; r.o+=1
    face=sz_read(r)
    print("  font: pointsize=%d weight=%d italic=%d charset=%d face=%r" % (ps,w,it,cs,face))
items=[]
for i in range(cnt):
    r.o=(r.o+3)&~3
    st=r.o
    ih=r.u32(); ie=r.u32(); ist=r.u32()
    ix=r.i16(); iy=r.i16(); icx=r.i16(); icy=r.i16(); iid=r.u32()
    icls=sz_read(r); itit=sz_read(r); ex=r.u16(); r.o+=ex
    en=r.o
    items.append((i,st,en,iid,icls,ist,ix,iy,icx,icy,ie,itit,ex))
    print("  [%2d] off=0x%03X..0x%03X id=%-6d cls=%-22r style=0x%08X pos=(%3d,%3d) size=(%3d,%3d) exStyle=0x%08X title=%r extra=%d" %
          (i,st,en,iid,icls,ist,ix,iy,icx,icy,ie,itit,ex))
r.o=(r.o+3)&~3
print("  parsed_end=0x%X blob_len=0x%X trailing=%d" % (r.o,len(blob),len(blob)-r.o))
print("  ids=%s" % [it[3] for it in items])

assert cnt==14, "cDlgItems != 14"
assert len(items)==14
assert any(it[3]==1770 for it in items) and any(it[3]==1771 for it in items) and any(it[3]==1772 for it in items)
new=[it for it in items if it[3]==1771][0]
print("\n=== NEW ITEM VERIFY ===")
print("  id=1771 @off 0x%X..0x%X cls=%r style=0x%08X pos=(%d,%d) size=(%d,%d) exStyle=0x%08X" %
      (new[1],new[2],new[4],new[5],new[6],new[7],new[8],new[9],new[10]))
assert new[6]==310 and new[7]==34 and new[8]==110 and new[9]==87, "geometry mismatch"
assert new[4]==("ordinal",130) and new[5]==0x50000007 and new[10]==0x20
assert len(blob)-r.o==0, "trailing != 0"
print("  [OK] 14 items parsed, trailing=0, id=1771 present with expected geometry/class/style")
print("\n=== RESULT: READBACK PASS ===")
print("orig   SHA256 = %s" % ORIG_SHA)
print("patched SHA256 = %s" % hashlib.sha256(dst).hexdigest())
