"""Lead 抽验 W161 的三条 LEAD_AUDIT。

A1 虚表槽字节：[0x7E46E4 + 4*69] = [0x7E47F8] = 0x468090；槽23=0x4666E0；槽11=0x46B550；槽65=0x5F4B10
A2 0x5F4CFD 字节 = ff 90 14 01 00 00 = call [eax+0x114]，边界有效；
   全镜像 call[reg+0x114] 6 处、call[reg+0x104] 7 处，均边界有效
A3 BulletClass::AI 0x4666E0：1794 指令 / 816 内存操作数 / 115 call / 2 回边
"""
import capstone
import audit_lib as A


def insn_stats(b, entry, size):
    n = 0
    mem = 0
    calls = 0
    backs = []
    for insn in A.linear_from(b, entry, size):
        n += 1
        if insn.mnemonic == "call":
            calls += 1
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM:
                mem += 1
        if insn.mnemonic.startswith("j") and insn.op_str.startswith("0x"):
            t = int(insn.op_str, 16)
            if t <= insn.address:
                backs.append((insn.address, t))
    return n, mem, calls, len(backs), backs


def calls_with_disp_general(b, disp):
    """扫 `call [<mem> + disp]`，任何 base/index 组合。"""
    m = A.md32(skipdata=True)
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    out = []
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0 or insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type == capstone.x86.X86_OP_MEM and (op.mem.disp & 0xFFFFFFFF) == disp:
            out.append(dict(va=insn.address, text="%s %s" % (insn.mnemonic, insn.op_str),
                            bytes=insn.bytes.hex(" ")))
    return out


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    rec = dict(rows)

    print("=" * 92)
    print("A1 · BulletClass 主表槽字节（vt = 0x7E46E4）")
    print("=" * 92)
    vt = 0x7E46E4
    for slot, want in ((69, 0x468090), (23, 0x4666E0), (11, 0x46B550), (65, 0x5F4B10)):
        va = vt + 4 * slot
        got = b.u32(va)
        print("  slot %3d  [%08X] = %08X  want %08X  %s"
              % (slot, va, got, want, "PASS" if got == want else "**FAIL**"))

    print()
    print("=" * 92)
    print("A2 · Draw 调用点与两种槽调用的全镜像计数")
    print("=" * 92)
    print("  0x5F4CFD bytes = %s   (want ff 90 14 01 00 00)" % b.read(0x5F4CFD, 6).hex(" "))
    ok, insn, why = A.boundary_check(b, 0x5F4B10, 0x5F4CFD)
    print("  boundary from 0x5F4B10 : %s (%s) insn=%s"
          % (ok, why, ("%s %s" % (insn.mnemonic, insn.op_str)) if insn else None))
    for disp, want_n in ((0x114, 6), (0x104, 7)):
        hits = calls_with_disp_general(b, disp)
        print("  call [<mem>+0x%03X] : %d sites (want %d) %s"
              % (disp, len(hits), want_n, "PASS" if len(hits) == want_n else "**CHECK**"))
        for h in hits:
            e = A.entry_at_or_before(rows, h["va"])
            onc, i2, _ = A.boundary_check(b, e[0], h["va"])
            print("      %08X  %-30s bytes=%-20s fn=%08X on_boundary=%s"
                  % (h["va"], h["text"], h["bytes"], e[0], onc))

    print()
    print("=" * 92)
    print("A3 · BulletClass::AI 0x4666E0 统计")
    print("=" * 92)
    size = int(rec[0x4666E0]["size"])
    n, mem, calls, nb, backs = insn_stats(b, 0x4666E0, size)
    print("  atlas size = %d (decimal)" % size)
    print("  instructions=%d  mem_operands=%d  calls=%d  backedges=%d" % (n, mem, calls, nb))
    print("  want: 1794 / 816 / 115 / 2")
    print("  %s" % ("PASS" if (n, mem, calls, nb) == (1794, 816, 115, 2) else "**DIFF**"))
    for s, t in backs:
        print("     backedge %08X -> %08X" % (s, t))


if __name__ == "__main__":
    main()
