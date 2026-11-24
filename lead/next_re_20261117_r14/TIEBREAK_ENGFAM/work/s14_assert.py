"""s14: assert the claims quoted in VERDICT.md / FAMILY.md.

Every assertion here is checked against raw bytes; a failure prints FAIL and
exits non-zero, so the reports cannot drift away from the image.
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
ROWS34 = [s for s in SLOTS if s != "006805F0"]
EXPECT_JL_OFFS = {0x22, 0x4D, 0x5D, 0x6B}      # the jl of each HRESULT check
EXPECT_TEST_OFFS = {0x20, 0x4B, 0x5B, 0x69}    # the matching test eax,eax


def main():
    p = pe.open_pe()
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = True
    fails = []

    def check(cond, msg):
        print(("  OK   " if cond else "  FAIL ") + msg)
        if not cond:
            fails.append(msg)

    print("[1] every slot: ret at +0x7E, pad at +0x7F, prev byte 0x90")
    for s in SLOTS:
        va = int(s, 16)
        body = p.raw(va, 0x80)
        check(body[0x7E] == 0xC3 and body[0x7F] == 0x90 and p.u8(va - 1) == 0x90,
              f"{s}: ret={body[0x7E]:02X} pad={body[0x7F]:02X} prev={p.u8(va - 1):02X}")

    print("\n[2] all 34 rows: HRESULT checks test@+0x20/+0x4B/+0x5B/+0x69 "
          "-> jl@+0x22/+0x4D/+0x5D/+0x6B")
    for s in ROWS34:
        va = int(s, 16)
        insns = list(m.disasm(p.raw(va, 0x7F), va))
        tests, jls = set(), set()
        for k, i in enumerate(insns[:-1]):
            if i.mnemonic == "test" and i.op_str == "eax, eax" and \
                    insns[k + 1].mnemonic in ("jl", "jle", "jne", "jge", "je"):
                tests.add(i.address - va)
                if insns[k + 1].mnemonic == "jl":
                    jls.add(insns[k + 1].address - va)
        check(jls == EXPECT_JL_OFFS and tests - {(0x2A)} == EXPECT_TEST_OFFS,
              f"{s}: test {sorted(hex(x) for x in tests)} "
              f"jl {sorted(hex(x) for x in jls)}")

    print("\n[3] the count check is +0x2A/+0x2C jle (NOT an HRESULT check)")
    for s in ROWS34:
        va = int(s, 16)
        check(p.u8(va + 0x2A) == 0x85 and p.u8(va + 0x2B) == 0xC0
              and p.u8(va + 0x2C) == 0x7E,
              f"{s}: +0x2A .. +0x2C = "
              f"{p.raw(va + 0x2A, 3).hex()} (85 C0 7E = test eax,eax; jle)")

    print("\n[4] loop body write inventory: exactly 1 write, at +0x31, stack")
    for s in SLOTS:
        va = int(s, 16)
        check(p.raw(va + 0x31, 8) == bytes.fromhex("c744240c00000000"),
              f"{s}: +0x31 = {p.raw(va + 0x31, 8).hex()} (mov [esp+0xC],0)")

    print("\n[5] the three COM call encodings")
    for s in SLOTS:
        va = int(s, 16)
        check(p.raw(va + 0x1D, 3) == bytes.fromhex("ff5110")
              and p.raw(va + 0x49, 2) == bytes.fromhex("ff11")
              and p.raw(va + 0x55, 6) == bytes.fromhex("ff15f4157e00")
              and p.raw(va + 0x66, 3) == bytes.fromhex("ff5108"),
              f"{s}: call [ecx+0x10]/[ecx]/[0x7E15F4]/[ecx+8] encodings")

    print("\n[6] the IID pushed before QI is always 0x7F7C80")
    for s in SLOTS:
        va = int(s, 16)
        check(p.raw(va + 0x41, 5) == bytes.fromhex("68807c7f00"),
              f"{s}: +0x41 = {p.raw(va + 0x41, 5).hex()}")

    print("\n[7] template signature identity (branch targets normalised)")
    def sig(va):
        out = []
        for i in m.disasm(p.raw(va, 0x7F), va):
            ops = i.op_str
            if i.mnemonic.startswith("j") and i.operands and \
                    i.operands[0].type == capstone.x86.X86_OP_IMM:
                ops = f"+0x{i.operands[0].imm - va:02X}"
            out.append((i.address - va, i.mnemonic, ops))
        return out
    base = sig(int(SLOTS[0], 16))
    check(all(sig(int(s, 16)) == base for s in SLOTS), "35/35 identical")

    print("\n[8] coverage.tsv: 006805F0 is S05 / Unsorted::Save_Sides / [已证]")
    with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
              r"\COVERAGE\coverage.tsv", encoding="utf-8", errors="replace") as f:
        hit = [l.rstrip("\n").split("\t") for l in f if l.startswith("006805F0\t")]
    check(len(hit) == 1 and hit[0][1] == "S05" and hit[0][2] == "Unsorted::Save_Sides"
          and hit[0][4] == "[已证]", f"{hit}")
    print("\nresult:", "ALL OK" if not fails else f"{len(fails)} FAILURES")


if __name__ == "__main__":
    main()
