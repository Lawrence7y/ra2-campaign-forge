# -*- coding: utf-8 -*-
"""Look at the code neighbourhood of each install site, find true function start."""
import io, os, sys, json, bisect
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

def u32(va):
    o = va - IB
    return int.from_bytes(buf[o:o + 4], "little") if 0 <= o <= len(buf) - 4 else None

starts_json = json.load(io.open(os.path.join(HERE, "starts.json"), encoding="utf-8"))
targets = set(starts_json["targets"])
atlas = {int(k, 16): v for k, v in starts_json["atlas"].items()}
all_starts = sorted(set(atlas) | targets)

# where is a dword == given VA anywhere in image?
def refs_to(va):
    pat = va.to_bytes(4, "little")
    out = []
    i = buf.find(pat)
    while i >= 0 and len(out) < 12:
        out.append(IB + i)
        i = buf.find(pat, i + 1)
    return out

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

def dis(va, n=60):
    o = va - IB
    return list(md.disasm(bytes(buf[o:o + n]), va))

def prologue_ok(va, n=60):
    """linear disasm from va must hit site later; report first insns."""
    ins = dis(va, n)
    return ins

SITES = [
 ('0040B880','0040B563','0040B540'),
 ('0040B930','0040B563','0040B540'),
 ('0040F7C0','0040F4AD','0040F490'),
 ('0040F870','0040F4AD','0040F490'),
 ('0040FD90','0040FB4D','0040FB30'),
 ('0040FE40','0040FB4D','0040FB30'),
 ('00410260','00410198','00410170'),
 ('00413F80','00413D87','00413D20'),
 ('0041C180','00413D87','00413D20'),
 ('00431E80','00431A8A','00431A30'),
 ('00431F70','00431A8A','00431A30'),
 ('004322A0','004014C4','004011C0'),
 ('004324B0','004014C4','004011C0'),
 ('004393D0','004385E1','004385D0'),
 ('004393F0','004385E1','004385D0'),
 ('00459EC0','0043B71F','0043B680'),
 ('0046B7E0','004662FD','004662E0'),
 ('0046B890','004662FD','004662E0'),
]
seen = set()
for (e, site, host) in SITES:
    if site in seen:
        continue
    seen.add(site)
    sv, hv = int(site, 16), int(host, 16)
    print("=" * 110)
    print("SITE %s  claimed_host %s" % (site, host))
    print("  claimed_host in atlas:", hv in atlas, " size:", atlas.get(hv))
    print("  claimed_host is call/jmp target:", hv in targets)
    print("  refs to claimed_host:", ["%08X" % r for r in refs_to(hv)])
    # candidate starts <= site from union
    i = bisect.bisect_right(all_starts, sv) - 1
    cands = []
    for j in range(max(0, i - 4), i + 1):
        s = all_starts[j]
        # does linear disasm from s land exactly on sv?
        ins = dis(s, sv - s + 16)
        land = any(x.address == sv for x in ins)
        clean = all(x.mnemonic not in ("ret", "retf") for x in ins if x.address < sv)
        cands.append((s, land, clean, len(ins)))
    print("  candidate starts (from atlas|call targets) <= site:")
    for c in cands:
        print("     %08X atlas=%s tgt=%s lands_on_site=%s no_ret_between=%s n=%d" % (
            c[0], c[0] in atlas, c[0] in targets, c[1], c[2], c[3]))
    print("  --- disasm window ---")
    base = sv - 0x40
    for ins in dis(base, 0x60):
        mark = ""
        if ins.address == sv:
            mark = "  <=== SITE"
        if ins.address == hv:
            mark = "  <=== CLAIMED HOST"
        print("     %08X: %-10s %s%s" % (ins.address, ins.mnemonic, ins.op_str, mark))
