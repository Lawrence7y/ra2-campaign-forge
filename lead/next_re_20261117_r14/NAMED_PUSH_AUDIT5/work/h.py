"""AUDIT5 shared helpers (own code)."""
import struct
from lib import Img, IMAGEBASE
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

img = Img()
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
secs = img.sections

def sec_name(va):
    return img.sec_of(va)[0]

def scan_imm32(value, lo, hi):
    out = []
    base = praw = None
    for name, b, vsz, pr, rsz in secs:
        if b <= lo < b + max(vsz, rsz):
            base, praw = b, pr
    if base is None:
        return out
    start = praw + (lo - base)
    end = praw + (hi - base)
    blob = img.data[start:end]
    pat = struct.pack('<I', value)
    i = blob.find(pat)
    while i >= 0:
        out.append(lo + i)
        i = blob.find(pat, i + 1)
    return out

def is_txt(v):
    return v is not None and TEXT_LO <= v < TEXT_HI

def rtti(vt):
    """COL at vt-4. MSVC32: COL{sig,offset,cdOffset,pTD,pCHD}; TD{pVF,spare,name[]}"""
    if vt is None:
        return None
    col = img.u32(vt - 4)
    if col is None or not (0x400000 <= col < 0x900000):
        return None
    sig = img.u32(col)
    td = img.u32(col + 0xC)
    chd = img.u32(col + 0x10)
    if sig != 0 or td is None or not (0x400000 <= td < 0x900000):
        return None
    name = img.cstr(td + 8)
    return dict(col=col, sig=sig, td=td, chd=chd, name=name)

def vt_start_of(slot_ref, maxback=400):
    i = 0
    while i < maxback and is_txt(img.u32(slot_ref - 4 * (i + 1))):
        i += 1
    return slot_ref - 4 * i, i

def vt_slots(vt, maxn=400):
    out = []
    for i in range(maxn):
        v = img.u32(vt + 4 * i)
        if not is_txt(v):
            break
        out.append(v)
    return out

def slot_of(vt, entry):
    return [i for i, v in enumerate(vt_slots(vt)) if v == entry]

def anc(vt):
    """class hierarchy descriptor name (pCHD -> TypeDescriptor chain)"""
    r = rtti(vt)
    if not r or not r['chd']:
        return None
    # CHD sig=0, attrs, numBase, pTD[], pCHD[]
    n = img.u32(r['chd'] + 8)
    tds = []
    for i in range(min(n or 0, 8)):
        t = img.u32(r['chd'] + 0xC + 4 * i)
        if t and 0x400000 <= t < 0x900000:
            tds.append(img.cstr(t + 8))
    return tds

def func_start(va, back=0x1200):
    """heuristic: walk back to a prologue preceded by padding/ret/jmp."""
    a = va
    best = va
    limit = max(TEXT_LO, va - back)
    while a > limit:
        b = img.u8(a - 1)
        if b in (0xCC, 0xC3, 0x90):
            # candidate start = next byte after padding run
            s = a
            while s < va and img.u8(s) in (0xCC, 0x90):
                s += 1
            if is_txt(s) and '55 8b ec' in img.hexb(s, 3):
                return s
        a -= 1
    return None

def prologue_start(va, back=0x2000):
    """scan back for 55 8B EC (push ebp;mov ebp,esp) or 6A FF 68 (SEH)"""
    a = va
    while a > max(TEXT_LO, va - back):
        a -= 1
        if img.hexb(a, 3) == '55 8b ec':
            return a
        if img.hexb(a, 3) == '6a ff 68':
            return a
        if img.hexb(a, 2) == '8b ff':
            return a + 2
    return None

def dis(va, n=64):
    out = []
    for ins in img.dis(va, n, detail=True):
        out.append("%08X  %-24s %-8s %s" % (ins.address, ins.bytes.hex(' ').upper(), ins.mnemonic, ins.op_str))
    return out

def body(entry, limit=0x1800):
    return img.body(entry, limit=limit)

def calls_to(target):
    b = img.read(TEXT_LO, TEXT_HI - TEXT_LO)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    md.detail = False
    out = []
    for ins in md.disasm(b, TEXT_LO):
        if ins.mnemonic == 'call' and ins.op_str.startswith('0x') and int(ins.op_str, 16) == target:
            out.append(ins.address)
    return out

def refs_imm(target):
    """all imm32 references to target in .text"""
    return scan_imm32(target, TEXT_LO, TEXT_HI)

def data_refs(target):
    """all imm32 references in .data/.rdata"""
    out = []
    for name, b, vsz, pr, rsz in secs:
        if name in ('.data', '.rdata'):
            out += [(va, name) for va in scan_imm32(target, b, b + max(vsz, rsz))]
    return out
