"""s7: ② channel, done from bytes only.

Scan all of .text for `C7 05 <dst32> <imm32>` (= mov dword [dst], imm32) and
index the results by destination.  For each of the 35 .bss vectors this yields
the constructor-install site and the vtable that is installed, from which the
RTTI name is read through COL -> TD -> TD+8.

No audited artefact is read; the ctor sites quoted by the audited party are
compared afterwards, not used as input.
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
# the edx argument each slot receives in the 0x67D300 chain (s6 output)
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


def scan_mov_imm_to_abs(p):
    """{dst_va: [(site, imm), ...]} from `C7 05 dst32 imm32` byte patterns,
    corroborated by disassembling at each hit."""
    t = p.text()
    start, end = t["vstart"], t["vstart"] + t["vsz"]
    data = p.raw(start, end - start)
    idx = {}
    i = 0
    while True:
        i = data.find(b"\xC7\x05", i)
        if i < 0 or i + 10 > len(data):
            break
        dst = int.from_bytes(data[i + 2:i + 6], "little")
        imm = int.from_bytes(data[i + 6:i + 10], "little")
        idx.setdefault(dst, []).append((start + i, imm))
        i += 1
    return idx


def check_disasm(p, site, dst, imm):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    ins = next(m.disasm(p.raw(site, 10), site))
    ok = (ins.mnemonic == "mov"
          and ins.operands[0].type == capstone.x86.X86_OP_MEM
          and ins.operands[0].mem.disp == dst
          and ins.operands[1].type == capstone.x86.X86_OP_IMM
          and ins.operands[1].imm == imm)
    return ok, ins


def main():
    p = pe.open_pe()
    idx = scan_mov_imm_to_abs(p)
    print(f"`C7 05 dst imm` destinations found in .text: {len(idx)}")
    print("\nslot      edx=.bss vector   ctor site    vt installed  RTTI class")
    rows = []
    for s in SLOTS:
        v = VEC[s]
        hits = idx.get(v, [])
        if not hits:
            print(f"{s}  0x{v:08X}  NO ctor write found")
            continue
        for site, imm in hits:
            ok, ins = check_disasm(p, site, v, imm)
            r = p.rtti(imm)
            print(f"{s}  0x{v:08X}  0x{site:08X}  0x{imm:08X}  "
                  f"{r.get('name')}   [COL 0x{r['col']:08X} TD 0x{r['td']:08X} "
                  f"ok={ok}]")
            rows.append(dict(slot=s, vec=v, site=site, vt=imm, ok=ok,
                             col=r["col"], td=r["td"], name=r.get("name")))
    import json
    with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
              r"\TIEBREAK_ENGFAM\EVIDENCE\rtti35.json", "w") as f:
        json.dump(rows, f, indent=1, default=str)


if __name__ == "__main__":
    main()
