"""s9: ㉓ check (RULING-R15 条 1) for all 35 vectors.

Each .bss vector gets TWO `mov dword [vec], vt` writes: the live one from the
static initializer and a second one that may live inside an atexit-registered
destructor (`push <dtor>; call 0x7C978A`), i.e. a DEAD table install.

For each write site this script
  1. finds the enclosing function entry by walking back for a ret + padding,
  2. asks whether that entry VA is passed to 0x7C978A somewhere in .text
     (the `_onexit`/atexit registration shape),
  3. resolves the RTTI name of the table installed there.
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
VEC = {
    "0067FDF0": 0x00A83E30, "0067FE70": 0x00A8EB28, "0067FEF0": 0x00887388,
    "0067FF70": 0x008874C0, "0067FFF0": 0x00887568, "00680070": 0x00A83D98,
    "006800F0": 0x00A83DC8, "00680170": 0x00A83D68, "006801F0": 0x00A80208,
    "00680270": 0x00A83C80, "006802F0": 0x00A8ED40, "00680370": 0x00B72608,
    "006803F0": 0x00A8EC18, "00680470": 0x00A83D80, "006804F0": 0x00ABCA10,
    "00680570": 0x008B4190, "006805F0": 0x008B4120, "00680670": 0x00B0F4E8,
    "006806F0": 0x008A3870, "00680770": 0x00A8E330, "006807F0": 0x00A83CB8,
    "00680870": 0x00A8E318, "006808F0": 0x00A8E988, "00680970": 0x008B3D10,
    "006809F0": 0x0088A0F0, "00680A70": 0x00A8EC38, "00680AF0": 0x0089E0F0,
    "00680B70": 0x008A0208, "00680BF0": 0x00AC4910, "00680C70": 0x00B0EC60,
    "00680CF0": 0x00889FB8, "00680D70": 0x00B0B880, "00680DF0": 0x00B0B5F0,
    "00680E70": 0x0089C668, "00680EF0": 0x00B04BD0,
}
ONEXIT = 0x007C978A


def writes_to(p, vec):
    t = p.text()
    start = t["vstart"]
    data = p.raw(start, t["vsz"])
    needle = b"\xC7\x05" + vec.to_bytes(4, "little")
    out, i = [], 0
    while True:
        i = data.find(needle, i)
        if i < 0:
            break
        out.append((start + i, int.from_bytes(data[i + 6:i + 10], "little")))
        i += 1
    return out


def func_entry(p, site):
    """Walk back to the nearest `ret` followed by padding; entry = next insn."""
    t = p.text()
    lo = t["vstart"]
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.skipdata = True
    # scan a 0x60 window backwards in 1-byte steps would be slow; instead look
    # for the last `c3` (ret) or `c2 xx xx` (ret imm16) whose next byte is 0x90
    # or 0xCC, between site-0x800 and site.
    win = p.raw(max(lo, site - 0x800), site - max(lo, site - 0x800))
    i = len(win) - 1
    while i >= 0:
        if win[i] == 0xC3 and i + 1 < len(win) and win[i + 1] in (0x90, 0xCC, 0x00):
            return max(lo, site - 0x800) + i + 1
        if win[i] in (0x90, 0xCC) and i + 1 < len(win) and win[i + 1] not in (0x90, 0xCC):
            # first non-pad after a pad run: the entry
            j = i
            while j >= 0 and win[j] in (0x90, 0xCC):
                j -= 1
            if j >= 0 and win[j] == 0xC3:
                return max(lo, site - 0x800) + i + 1
        i -= 1
    return None


def atexit_registered(p, entry):
    """Does `push <entry>; call 0x7C978A` exist?"""
    t = p.text()
    start = t["vstart"]
    data = p.raw(start, t["vsz"])
    needle = b"\x68" + entry.to_bytes(4, "little")
    hits, i = [], 0
    while True:
        i = data.find(needle, i)
        if i < 0:
            break
        hits.append(start + i)
        i += 1
    for h in hits:
        m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        m.detail = True
        for ins in m.disasm(p.raw(h, 0x40), h):
            if ins.mnemonic == "call" and ins.operands and \
                    ins.operands[0].type == capstone.x86.X86_OP_IMM and \
                    ins.operands[0].imm == ONEXIT:
                return h
            if ins.mnemonic in ("ret", "jmp"):
                break
    return None


def main():
    p = pe.open_pe()
    print(f"{'slot':<10} {'vec':<11} {'write site':<11} {'entry':<11} "
          f"atexit?  vt        RTTI")
    live = dead = 0
    for s in SLOTS:
        v = VEC[s]
        for site, vt in writes_to(p, v):
            e = func_entry(p, site)
            ax = atexit_registered(p, e) if e else None
            r = p.rtti(vt)
            tag = "DEAD(dtor)" if ax else "live"
            if ax:
                dead += 1
            else:
                live += 1
            print(f"{s:<10} 0x{v:08X}  0x{site:08X}  0x{e:08X}  {tag:<9} "
                  f"0x{vt:08X}  {r.get('name')}"
                  + (f"   [onexit reg @0x{ax:08X}]" if ax else ""))
    print(f"\nlive installs: {live}   dead(dtor) installs: {dead}")


if __name__ == "__main__":
    main()
