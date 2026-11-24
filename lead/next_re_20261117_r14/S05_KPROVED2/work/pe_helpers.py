"""PE/VA helpers for gamemd.exe (read-only). Card S05-KPROVED2."""
import pefile, struct

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE)
BASE = pe.OPTIONAL_HEADER.ImageBase

SECS = []
for s in pe.sections:
    name = s.Name.decode('latin1').rstrip('\x00')
    SECS.append((name, BASE + s.VirtualAddress, s.Misc_VirtualSize,
                 s.PointerToRawData, s.SizeOfRawData))

TEXT_LO = BASE + pe.sections[0].VirtualAddress
TEXT_HI = TEXT_LO + pe.sections[0].Misc_VirtualSize
RDATA_LO = BASE + pe.sections[1].VirtualAddress
RDATA_HI = RDATA_LO + pe.sections[1].Misc_VirtualSize

def sec_of(va):
    for name, vlo, vsz, praw, rsz in SECS:
        if vlo <= va < vlo + vsz:
            return name, vlo, vsz, praw, rsz
    return None

def va2off(va):
    x = sec_of(va)
    if x is None:
        return None
    name, vlo, vsz, praw, rsz = x
    d = va - vlo
    if d >= rsz:
        return None
    return praw + d

def u32(va):
    o = va2off(va)
    if o is None:
        return None
    return struct.unpack_from('<I', pe.__data__, o)[0]

def u8(va):
    o = va2off(va)
    if o is None:
        return None
    return pe.__data__[o]

def bytes_at(va, n):
    o = va2off(va)
    if o is None:
        return None
    return pe.__data__[o:o+n]

def cstr(va, maxn=200):
    o = va2off(va)
    if o is None:
        return None
    end = pe.__data__.find(b'\x00', o, o+maxn)
    if end < 0:
        end = o+maxn
    raw = pe.__data__[o:end]
    try:
        return raw.decode('ascii')
    except Exception:
        return raw.decode('latin1')

def is_text(va):
    return va is not None and TEXT_LO <= va < TEXT_HI

def is_rdata(va):
    return va is not None and RDATA_LO <= va < RDATA_HI
