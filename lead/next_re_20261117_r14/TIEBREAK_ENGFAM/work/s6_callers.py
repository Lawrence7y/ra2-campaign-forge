"""s6: independent ④ pass -- scan the whole .text for every reference to each
of the 35 slots, and for the in-function chain that calls them record the
`mov edx,<.bss vector>` argument that precedes each call.

Channels:
  A) literal E8 rel32 arithmetic over raw bytes (no disassembly)
  B) capstone linear sweep of the calling region, tracking `mov edx,imm32`
"""
import capstone

import pe

SLOTS = ["0067FDF0", "0067FE70", "0067FEF0", "0067FF70", "0067FFF0",
         "00680070", "006800F0", "00680170", "006801F0", "00680270",
         "006802F0", "00680370", "006803F0", "00680470", "006804F0",
         "00680570", "006805F0", "00680670", "006806F0", "00680770",
         "006807F0", "00680870", "006808F0", "00680970", "006809F0",
         "00680A70", "00680AF0", "00680B70", "00680BF0", "00680C70",
         "00680CF0", "00680D70", "00680DF0", "00680E70", "00680EF0"]
CHAIN = (0x0067D300, 0x0067E500)


def chan_a(p, targets):
    """Every E8 rel32 in .text whose computed target is one of `targets`."""
    t = p.text()
    start, end = t["vstart"], t["vstart"] + t["vsz"]
    hits = {tt: [] for tt in targets}
    data = p.raw(start, end - start)
    for i, b in enumerate(data):
        if b != 0xE8 or i + 5 > len(data):
            continue
        rel = int.from_bytes(data[i + 1:i + 5], "little", signed=True)
        site = start + i
        tgt = site + 5 + rel
        if tgt in hits:
            hits[tgt].append(site)
    return hits


def chan_a2(p, targets):
    """4-byte VA appearing literally anywhere in .text (data form / mov imm32)."""
    t = p.text()
    start, end = t["vstart"], t["vstart"] + t["vsz"]
    data = p.raw(start, end - start)
    out = {tt: [] for tt in targets}
    for tt in targets:
        needle = tt.to_bytes(4, "little")
        i = 0
        while True:
            i = data.find(needle, i)
            if i < 0:
                break
            out[tt].append(start + i)
            i += 1
    return out


def main():
    p = pe.open_pe()
    tg = {int(s, 16): s for s in SLOTS}
    A = chan_a(p, set(tg))
    B = chan_a2(p, set(tg))
    print("slot            E8-call sites                       literal-VA sites")
    for va, name in tg.items():
        a = " ".join(f"0x{x:08X}" for x in A[va]) or "-"
        b = " ".join(f"0x{x:08X}" for x in B[va]) or "-"
        print(f"{name}   {a:<36} {b}")
    print("\n--- chain in 0x67D300.. with edx tracking")
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = True
    insns = list(m.disasm(p.raw(CHAIN[0], CHAIN[1] - CHAIN[0]), CHAIN[0]))
    last_edx = None
    n = 0
    for i, ins in enumerate(insns):
        if ins.mnemonic == "mov" and ins.op_str.startswith("edx,"):
            v = ins.operands[1]
            if v.type == capstone.x86.X86_OP_IMM:
                last_edx = (v.imm, ins.address, ins.bytes.hex())
        elif ins.mnemonic == "call":
            tgt = ins.operands[0]
            if tgt.type == capstone.x86.X86_OP_IMM and tgt.imm in tg:
                n += 1
                e = last_edx
                print(f"#{n:02d} {tg[tgt.imm]}  site 0x{ins.address:08X}  "
                      f"edx=0x{e[0]:08X} @0x{e[1]:08X} [{e[2]}]")
    print("total slot calls in chain:", n)


if __name__ == "__main__":
    main()
