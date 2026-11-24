"""Lead 抽验 W160 的 LEAD_AUDIT + 它改正的 8 站点表。

A1 0x55DC99 bytes = b9 78 f7 87 00 (mov ecx,0x87F778)；0x55DC9E = e8 0d d3 ff ff (call 0x55AFB0)
A2 0x55B608 = mov eax,[edi+4]；0x55B610 = ff 52 5c (call [edx+0x5C])
A3 0x40CBAC = mov [0x87F778],0x7E18FC；0x40CBC8 = mov [0x87F778],0x7E192C
A4 0x55AFB0 内 8 个 slot-5C 站点；孤儿 0x55B8F0 段 11 个
A5 每个 slot-5C 循环的 mode 门控：0x55B61B 的 [0xA8B238] test/je/cmp 5/je
A6 数组 0xA83E00 的身份：谁往 0xA83E00 写虚表？
"""
import capstone
import audit_lib as A


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    rec = dict(rows)

    print("=" * 92)
    print("A1/A2/A3 · 关键字节")
    print("=" * 92)
    checks = [
        ("0x55DC99", 0x55DC99, 5, "b9 78 f7 87 00"),
        ("0x55DC9E", 0x55DC9E, 5, "e8 0d d3 ff ff"),
        ("0x55B608", 0x55B608, 3, "8b 47 04"),
        ("0x55B610", 0x55B610, 3, "ff 52 5c"),
        ("0x40CBAC", 0x40CBAC, 10, "c7 05 78 f7 87 00 fc 18 7e 00"),
        ("0x40CBC8", 0x40CBC8, 10, "c7 05 78 f7 87 00 2c 19 7e 00"),
    ]
    for name, va, n, want in checks:
        got = b.read(va, n).hex(" ")
        print("  %-10s %s   want %s   %s" % (name, got, want, "PASS" if got == want else "**DIFF**"))

    # A2 语义确认
    for insn in A.linear_from(b, 0x55B600, 0x20):
        if insn.address in (0x55B608, 0x55B610):
            print("  decoded %08X : %s %s" % (insn.address, insn.mnemonic, insn.op_str))

    print()
    print("=" * 92)
    print("A4 · slot-5C 站点计数（0x55AFB0 vs 孤儿 0x55B8F0）")
    print("=" * 92)
    for label, start, size in (("0x55AFB0", 0x55AFB0, 1901), ("0x55B8F0", 0x55B8F0, 0x1B0)):
        sites = []
        for insn in A.linear_from(b, start, size):
            if insn.mnemonic == "call" and "+ 0x5c]" in insn.op_str:
                sites.append(insn.address)
        print("  %s : %d sites -> %s" % (label, len(sites), [hex(x) for x in sites]))

    print()
    print("=" * 92)
    print("A5 · 0x55AFB0 里的 mode 门控（[0xA8B238]）")
    print("=" * 92)
    for insn in A.linear_from(b, 0x55AFB0, 1901):
        if 0xA8B238 in [op.mem.disp for op in insn.operands
                        if op.type == capstone.x86.X86_OP_MEM]:
            print("   %08X  %-8s %s" % (insn.address, insn.mnemonic, insn.op_str))
            # 打印紧随的 6 条
            for j in A.linear_from(b, insn.address, 0x20):
                if insn.address < j.address <= insn.address + 0x14:
                    print("        %08X  %-8s %s" % (j.address, j.mnemonic, j.op_str))

    print()
    print("=" * 92)
    print("A6 · 谁往 0xA83E00 写虚表（判定该数组身份）")
    print("=" * 92)
    import struct
    tgt = 0xA83E00
    pat = struct.pack("<I", tgt)
    m = A.md32(skipdata=True)
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    found = 0
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0:
            continue
        if any(op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0
               and (op.mem.disp & 0xFFFFFFFF) == tgt for op in insn.operands):
            found += 1
            e = A.entry_at_or_before(rows, insn.address)
            print("   %08X  %-40s fn=%08X" % (insn.address, "%s %s" % (insn.mnemonic, insn.op_str), e[0]))
    if not found:
        print("   (no memory-operand reference; trying raw dword 0xA83E00 …)")
        pat = struct.pack("<I", tgt)
        i = 0
        cnt = 0
        while True:
            i = data.find(pat, i)
            if i < 0:
                break
            va = t["va"] + i
            for insn in m.disasm(data[max(0, i - 8):i + 12], va - min(8, i)):
                if insn.id == 0:
                    continue
                if insn.address <= va < insn.address + insn.size:
                    print("   dword@%08X in insn %08X %s %s"
                          % (va, insn.address, insn.mnemonic, insn.op_str))
                    cnt += 1
                    break
            i += 1
            if cnt > 8:
                break


if __name__ == "__main__":
    main()
