"""Lead 抽验 W157 的 LEAD_AUDIT 三项 + 一条 W157 未覆盖但我必须查的事：

W157 的三项：
  A1 0x67D300 的 111 个回边（全 jl），双通道
  A2 IID_IPersistStream 字节 @0x7F7C80；0x67D342 / 0x67D386 的指令边界
  A3 门控字节 @0x55DBCD / 0x55DBE0 / 0x55DBEE / 0x55DC92；XREF 计数

Lead 额外要查的（直接关系到 §891-4 是否正确）：
  Q  0x55DC9E (call 0x55AFB0) 是否落在同一个 `[0xA8B238]==0` 门控区内？
     若是，则 0x55AFB0 只在 mode==0（主菜单）跑，§891-4 的"每帧路径"表述要改。
"""
import audit_lib as A
import relref


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    rec = dict(rows)

    print("=" * 96)
    print("A1 · 0x67D300 backedges")
    print("=" * 96)
    r = rec.get(0x67D300)
    size = int(r["size"])
    ins = list(A.linear_from(b, 0x67D300, size))
    backs = []
    for i in ins:
        if i.mnemonic.startswith("j") and i.op_str.startswith("0x"):
            t = int(i.op_str, 16)
            if t <= i.address:
                backs.append((i.address, t, i.mnemonic))
    print("  atlas size=%d (decimal), linear insns=%d" % (size, len(ins)))
    print("  backedges = %d" % len(backs))
    mnem = {}
    for _, _, m in backs:
        mnem[m] = mnem.get(m, 0) + 1
    print("  by mnemonic: %s" % mnem)
    print("  first 5: %s" % [("%08X->%08X %s" % (s, t, m)) for s, t, m in backs[:5]])

    print()
    print("=" * 96)
    print("A2 · IID_IPersistStream bytes + boundary at 0x67D342 / 0x67D386")
    print("=" * 96)
    print("  0x7F7C80 = %s" % b.read(0x7F7C80, 16).hex(" "))
    for va in (0x67D342, 0x67D386):
        ok, insn, why = A.boundary_check(b, 0x67D300, va)
        print("  %08X boundary=%s (%s) insn=%s bytes=%s"
              % (va, ok, why,
                 ("%s %s" % (insn.mnemonic, insn.op_str)) if insn else None,
                 b.read(va, insn.size).hex(" ") if insn else ""))

    print()
    print("=" * 96)
    print("A3 · gate bytes")
    print("=" * 96)
    for va, n in ((0x55DBCD, 6), (0x55DBE0, 6), (0x55DBEE, 7), (0x55DC92, 5)):
        print("  %08X = %s" % (va, b.read(va, n).hex(" ")))
    for tgt in (0x67D300, 0x67CEF0, 0x5F6250):
        h = relref.scan_rel_targets_report(b, rows, tgt)
        print("  XREF(call/jmp rel) -> %08X : %d  sites=%s"
              % (tgt, len(h), [hex(x["site"]) for x in h]))

    print()
    print("=" * 96)
    print("Q · 0x55DC9E 是否在 mode==0 门控区内？（Lead 自查，W157 未覆盖）")
    print("=" * 96)
    for insn in A.linear_from(b, 0x55DBA0, 0x180):
        if 0x55DBA0 <= insn.address <= 0x55DD00:
            mark = ""
            if insn.address in (0x55DBCD, 0x55DBE0, 0x55DBEE, 0x55DC92, 0x55DC9E):
                mark = "   <<<<<<"
            print("   %08X  %-8s %-36s %s" % (insn.address, insn.mnemonic, insn.op_str, mark))


if __name__ == "__main__":
    main()
