# -*- coding: utf-8 -*-
"""Exploratory: atlas ranges around each install site, raw bytes, disasm."""
import io, os, sys, bisect
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
IB = 0x400000
import pefile, capstone

pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    secs.append((s.Name.rstrip(b"\x00").decode("latin-1"), IB + s.VirtualAddress,
                 s.Misc_VirtualSize, s.SizeOfRawData, s.get_data()))
end = max(va + max(vs, rs) for _nm, va, vs, rs, _d in secs)
buf = bytearray(end - IB + 16)
for nm, va, vs, rs, d in secs:
    buf[va - IB:va - IB + len(d)] = d
secinfo = [(nm, va, vs, rs) for nm, va, vs, rs, _d in secs]

def u32(va):
    o = va - IB
    return int.from_bytes(buf[o:o + 4], "little") if 0 <= o <= len(buf) - 4 else None

def cstr(va, n=300):
    o = va - IB
    if o < 0 or o >= len(buf):
        return None
    e = buf.find(b"\x00", o, min(o + n, len(buf)))
    return bytes(buf[o:e]).decode("latin-1", "replace") if e > 0 else None

atlas = {}
for i, ln in enumerate(io.open(ATLAS, encoding="utf-8-sig")):
    if i == 0:
        continue
    c = ln.rstrip("\r\n").split("\t")
    if len(c) < 2:
        continue
    try:
        atlas[int(c[0].strip(), 16)] = (int(c[1]), c)
    except ValueError:
        pass
starts = sorted(atlas)
sizes = [atlas[s][0] for s in starts]

def containing(va):
    i = bisect.bisect_right(starts, va) - 1
    if i >= 0 and starts[i] <= va < starts[i] + sizes[i]:
        return starts[i], sizes[i]
    return None, None

def nearest_starts(va, k=4):
    i = bisect.bisect_right(starts, va) - 1
    out = []
    for j in range(max(0, i - k + 1), min(len(starts), i + 1)):
        out.append((starts[j], atlas[starts[j]][0], starts[j] + atlas[starts[j]][0]))
    return out

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

ROWS = [
 ('0040B880','007E17CC',2,'0040B563','mov_abs','0040B540'),
 ('0040B930','007E17CC',4,'0040B563','mov_abs','0040B540'),
 ('0040F7C0','007E1E84',2,'0040F4AD','mov_abs','0040F490'),
 ('0040F870','007E1E84',4,'0040F4AD','mov_abs','0040F490'),
 ('0040FD90','007E1ED4',2,'0040FB4D','mov_abs','0040FB30'),
 ('0040FE40','007E1ED4',4,'0040FB4D','mov_abs','0040FB30'),
 ('00410260','007E1F50',0,'00410198','ctor_body','00410170'),
 ('00413F80','007E22A4',9,'00413D87','ctor_body','00413D20'),
 ('0041C180','007E22A4',11,'00413D87','ctor_body','00413D20'),
 ('00431E80','007E3A2C',2,'00431A8A','ctor_body','00431A30'),
 ('00431F70','007E3A2C',7,'00431A8A','ctor_body','00431A30'),
 ('004322A0','007E1668',9,'004014C4','ctor_body','004011C0'),
 ('004324B0','007E1668',10,'004014C4','ctor_body','004011C0'),
 ('004393D0','007E3D10',12,'004385E1','ctor_body','004385D0'),
 ('004393F0','007E3D10',8,'004385E1','ctor_body','004385D0'),
 ('00459EC0','007E3EBC',11,'0043B71F','ctor_body','0043B680'),
 ('0046B7E0','007E4678',2,'004662FD','mov_abs','004662E0'),
 ('0046B890','007E4678',4,'004662FD','mov_abs','004662E0'),
]

print("sections:", secinfo)
for (e, vt, slot, site, form, host) in ROWS:
    ev, vv, sv, hv = int(e,16), int(vt,16), int(site,16), int(host,16)
    ce, se = containing(ev)
    cs_, ss = containing(sv)
    csite, ssize = containing(sv)
    print("="*100)
    print("entry=%s vt=%s slot=%d site=%s form=%s claimed_host=%s" % (e, vt, slot, site, form, host))
    print("  entry containing: %s size=%s" % (("%08X" % ce) if ce else None, se))
    print("  site containing:  %s size=%s" % (("%08X" % csite) if csite else None, ssize))
    print("  claimed host in atlas: %s" % (("%08X size=%d" % (hv, atlas[hv][0])) if hv in atlas else "NO"))
    print("  site<entry: %s   site-host delta: 0x%X" % (sv < ev, sv - hv))
    print("  nearest atlas starts <= site:", [("%08X sz=%d end=%08X" % t) for t in nearest_starts(sv)])
    # bytes at site
    o = sv - IB
    print("  bytes@site:", bytes(buf[o:o+12]).hex())
    for ins in list(md.disasm(bytes(buf[o-16:o+16]), sv-16))[:6]:
        mark = " <== site" if ins.address == sv else ""
        print("     %08X: %-8s %s%s" % (ins.address, ins.mnemonic, ins.op_str, mark))
    # vt chain
    print("  u32(vt-4)=%08X  u32(COL)=%s  u32(COL+4)=%s  u32(COL+12)=%s  cstr(TD+8)=%s" % (
        u32(vv-4) or 0, u32(u32(vv-4) or 0), u32((u32(vv-4) or 0)+4), u32((u32(vv-4) or 0)+12),
        cstr((u32((u32(vv-4) or 0)+12) or 0)+8)))
    print("  slotval u32(vt+%d*4)=%s expected=%s" % (slot, ("%08X" % (u32(vv+slot*4) or 0)), e))
