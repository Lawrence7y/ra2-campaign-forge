from pathlib import Path
import pefile
ROOT = Path(r'D:\Project\ra2-campaign-forge')
BIN = ROOT / 'ra2youli' / 'gamemd.exe'
PE = pefile.PE(str(BIN), fast_load=False)
IMAGE_BASE = PE.OPTIONAL_HEADER.ImageBase

def va_to_off(va):
    for s in PE.sections:
        start = IMAGE_BASE + s.VirtualAddress
        if start <= va < start + max(s.Misc_VirtualSize, s.SizeOfRawData):
            delta = va - start
            if delta < s.SizeOfRawData:
                return s.PointerToRawData + delta, s.Name.rstrip(b'\x00').decode('ascii','replace')
    return None, None

def off_to_va(off):
    for s in PE.sections:
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            return IMAGE_BASE + s.VirtualAddress + (off - s.PointerToRawData), s.Name.rstrip(b'\x00').decode('ascii','replace')
    return None, None

def section_of(va):
    for s in PE.sections:
        start = IMAGE_BASE + s.VirtualAddress
        if start <= va < start + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.Name.rstrip(b'\x00').decode('ascii','replace')
    return None

def read_va(va, n):
    off, sec = va_to_off(va)
    if off is None: return None
    return PE.__data__[off:off+n]

def atlas_entries():
    import re
    p = ROOT / 'lead' / 'next_re_20261112_r10' / 'W130_atlas' / 'function_atlas.tsv'
    out={}
    with p.open('r', encoding='utf-8-sig', errors='replace') as f:
        for ln in f:
            r=ln.rstrip('\r\n').split('\t')
            if r and re.fullmatch(r'[0-9a-fA-F]{8}', r[0].strip()):
                out[int(r[0],16)] = int(r[1])
    return out

def containing_func(va):
    for e,sz in atlas_entries().items():
        if e <= va < e+sz: return (e,sz)
    return None
