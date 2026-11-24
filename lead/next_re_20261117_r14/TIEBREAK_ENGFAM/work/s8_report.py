"""s8: report material.

1. template identity: for every slot, the (relative offset, mnemonic, op_str)
   sequence is compared against slot #1's; any deviation is printed.
2. how many byte-identical copies of the 127-byte body exist in .text.
3. per-sampled-row facts, in one table.
"""
import hashlib

import capstone

import pe

SLOTS = ["0067FDF0", "0067FE70", "0067FEF0", "0067FF70", "0067FFF0",
         "00680070", "006800F0", "00680170", "006801F0", "00680270",
         "006802F0", "00680370", "006803F0", "00680470", "006804F0",
         "00680570", "006805F0", "00680670", "006806F0", "00680770",
         "006807F0", "00680870", "006808F0", "00680970", "006809F0",
         "00680A70", "00680AF0", "00680B70", "00680BF0", "00680C70",
         "00680CF0", "00680D70", "00680DF0", "00680E70", "00680EF0"]
SAMPLE = ["0067FDF0", "006800F0", "00680470", "006807F0", "00680B70", "00680EF0"]
VEC = {
    "0067FDF0": (0x00A83E30, 0x004E6E7D, 0x007E9FA4, 0x00801610, 0x008234E0, ".?AV?$DynamicVectorClass@PAVFactoryClass@@@@", 0x0067DF0F),
    "006800F0": (0x00A83DC8, 0x004E697D, 0x007E9D64, 0x008010B8, 0x00823138, ".?AV?$DynamicVectorClass@PAVParticleClass@@@@", 0x0067DFAB),
    "00680470": (0x00A83D80, 0x004E71FD, 0x007EA164, 0x00801A38, 0x008237C8, ".?AV?$DynamicVectorClass@PAVOverlayTypeClass@@@@", 0x0067E061),
    "006807F0": (0x00A83CB8, 0x004E78FD, 0x007EA4E4, 0x00802288, 0x00823E28, ".?AV?$DynamicVectorClass@PAVSuperClass@@@@", 0x0067E117),
    "00680B70": (0x008A0208, 0x004A6C8D, 0x007E5EDC, 0x007FFB10, 0x0081FF58, ".?AV?$DynamicVectorClass@PAVDiskLaserClass@@@@", 0x0067E2A9),
    "00680EF0": (0x00B04BD0, 0x0065B17D, 0x007F07A4, 0x008085F8, 0x008395C8, ".?AV?$DynamicVectorClass@PAVRadSiteClass@@@@", 0x0067E3AA),
}
N = 127      # body length established by s3 for every slot


def unit():
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = True
    return m


def sig(p, va):
    """Template signature: (relative offset, mnemonic, operands) with every
    branch target normalised to its relative offset, so that two copies of the
    same template compare equal despite living at different addresses."""
    out = []
    for i in unit().disasm(p.raw(va, N), va):
        ops = i.op_str
        if i.mnemonic.startswith("j") and i.operands and \
                i.operands[0].type == capstone.x86.X86_OP_IMM:
            ops = f"+0x{i.operands[0].imm - va:02X}"
        out.append((i.address - va, i.mnemonic, ops))
    return out


def main():
    p = pe.open_pe()
    base = sig(p, int(SLOTS[0], 16))
    print("== 1. template identity vs 0x0067FDF0 (relative offset, mnemonic, ops)")
    bad = 0
    for s in SLOTS:
        sg = sig(p, int(s, 16))
        if sg != base:
            bad += 1
            print(f"  DIFFERS: {s}")
            for a, b in zip(base, sg):
                if a != b:
                    print(f"    base {a}  vs  {b}")
            if len(sg) != len(base):
                print(f"    instruction count {len(base)} vs {len(sg)}")
    print(f"  identical: {len(SLOTS) - bad}/{len(SLOTS)}  "
          f"(body {N} B, {len(base)} instructions, md5 "
          f"{hashlib.md5(p.raw(int(SLOTS[0], 16), N)).hexdigest()})")

    print("\n== 2. byte-identical 127-byte copies of the body in .text")
    t = p.text()
    needle = p.raw(int(SLOTS[0], 16), N)
    data = p.raw(t["vstart"], t["vsz"])
    hits = []
    i = 0
    while True:
        i = data.find(needle, i)
        if i < 0:
            break
        hits.append(t["vstart"] + i)
        i += 1
    print(f"  {len(hits)} occurrences:")
    for h in hits:
        tag = ""
        if f"{h:08X}" in SLOTS:
            tag = "  (member slot)"
        print(f"    0x{h:08X}{tag}")

    print("\n== 3. sampled rows: one line per row")
    hdr = ("entry      loop_tag   loop_back  bound   loop_nonstack_writes  "
           "calls  hr_checks  vec        ctor       vt         name")
    print(hdr)
    for s in SAMPLE:
        va = int(s, 16)
        insns = list(unit().disasm(p.raw(va, N), va))
        # loop back edge = the backward jl that closes the counting loop
        back = [i for i in insns if i.mnemonic in ("jl", "jne", "jb")
                and i.operands[0].type == capstone.x86.X86_OP_IMM
                and i.operands[0].imm < i.address]
        lp = max(back, key=lambda i: i.address - i.operands[0].imm)
        tgt = lp.operands[0].imm
        span = [i for i in insns if tgt <= i.address <= lp.address]
        nsw = 0
        for i in span:
            if i.mnemonic in ("mov", "add", "or", "and", "xor") and i.operands and \
               i.operands[0].type == capstone.x86.X86_OP_MEM:
                b = i.reg_name(i.operands[0].mem.base) if i.operands[0].mem.base else ""
                if b not in ("esp", "ebp"):
                    nsw += 1
        calls = sum(1 for i in insns if i.mnemonic == "call")
        checks = sum(1 for k, i in enumerate(insns[:-1])
                     if i.mnemonic == "test" and i.op_str == "eax, eax"
                     and insns[k + 1].mnemonic.startswith("j"))
        v = VEC[s]
        print(f"{s}  0x{lp.address:08X} 0x{tgt:08X}  [vec+0x10]   {nsw}"
              f"{'':<20} {calls}     {checks}      0x{v[0]:08X} 0x{v[1]:08X} "
              f"0x{v[2]:08X} {v[5]}")


if __name__ == "__main__":
    main()
