"""AUDIT5 facts pass 1: for each entry, find vtables containing it, RTTI names,
ctor install sites, and direct call sites. Own code."""
import json, sys, struct
from lib import Img, IMAGEBASE

img = Img()
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
secs = img.sections

def sec_name(va):
    return img.sec_of(va)[0]

def scan_imm32(value, lo, hi):
    out = []
    base, praw = None, None
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

def rtti_name(vt):
    col = img.u32(vt - 4)
    if col is None or not (0x400000 <= col < 0x900000):
        return None
    sig = img.u32(col)
    td = img.u32(col + 0xC)
    if sig != 0 or td is None or not (0x400000 <= td < 0x900000):
        return None
    nptr = img.u32(td + 0xC)
    name = img.cstr(nptr) if nptr else None
    return dict(col=col, td=td, name=name)

def is_txt(v):
    return v is not None and TEXT_LO <= v < TEXT_HI

def vt_start_of(slot_ref):
    i = 0
    while i < 400 and is_txt(img.u32(slot_ref - 4 * (i + 1))):
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

# pre-disassemble whole .text once for call-site scanning
b = img.read(TEXT_LO, TEXT_HI - TEXT_LO)
md = img.md
direct_calls = {}
call_idx = {}
for ins in md.disasm(b, TEXT_LO):
    if ins.mnemonic == 'call' and ins.op_str.startswith('0x'):
        t = int(ins.op_str, 16)
        direct_calls.setdefault(t, []).append(ins.address)

entries = [int(x, 16) for x in sys.argv[1:]]
res = {}
for e in entries:
    rec = dict(entry=e)
    vts = []
    for c in scan_imm32(e, 0x7E0400, 0x900000):
        vt, idx = vt_start_of(c)
        slots = vt_slots(vt)
        vts.append(dict(slot_ref=c, sec=sec_name(c), vt=vt, slot_index=idx,
                        nslots=len(slots), rtti=rtti_name(vt)))
    rec['vts'] = vts
    rec['direct_calls'] = direct_calls.get(e, [])
    res['%08X' % e] = rec

for k, rec in res.items():
    for v in rec['vts']:
        vt = v['vt']
        sites = []
        for hit in scan_imm32(vt, TEXT_LO, TEXT_HI):
            ctx = img.dis(max(TEXT_LO, hit - 12), 24, detail=True)
            for ins in ctx:
                if ins.address <= hit < ins.address + ins.size:
                    sites.append(dict(imm_at=hit, ins="%08X %s %s" % (ins.address, ins.mnemonic, ins.op_str)))
                    break
        v['text_writes'] = sites

print(json.dumps(res, indent=1, default=str))
