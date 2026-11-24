"""Lead 抽验 W155 的 LEAD_AUDIT 项。全部用本目录自己的工具，不 import W155 的代码。

覆盖 A1-A8 / B1-B2 / C1-C2 / D1。
回边定义（写死，便于复核）：在函数体 [entry, entry+size) 内，所有相对跳转
（jmp/jcc/jcxz，含 short 与 near）中 target <= site 的那些，记一条回边。
"""
import struct
import audit_lib as A

PASS, FAIL = "PASS", "**FAIL**"


def be(b, va, n):
    return b.read(va, n).hex(" ")


def count_backedges(b, entry, size):
    """返回 (backedges, insn_count)。只用线性反汇编 + 相对跳转解析。"""
    insns = A.linear_from(b, entry, size)
    backs = []
    for insn in insns:
        if insn.mnemonic in ("jmp", "jcc", "jcxz", "jecxz", "loop"):
            pass
        if insn.op_str.startswith("0x") and insn.mnemonic.startswith("j"):
            tgt = int(insn.op_str, 16)
            if tgt <= insn.address:
                backs.append((insn.address, tgt, "%s %s" % (insn.mnemonic, insn.op_str)))
    return backs, len(insns)


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    rec = dict((v, r) for v, r in rows)

    print("=" * 92)
    print("A · 0x55B8F0 边界与阶梯（A1-A8）")
    print("=" * 92)

    def chk(label, got, want):
        ok = (got == want)
        print("  [%s] %-52s got=%s want=%s" % (PASS if ok else FAIL, label, got, want))
        return ok

    chk("A1 0x55B8DE bytes", be(b, 0x55B8DE, 3), "c2 08 00")
    chk("A2 0x55B8E1..EF is 15x 90", be(b, 0x55B8E1, 15), " ".join(["90"] * 15))
    chk("A3 0x55B8F0 bytes", be(b, 0x55B8F0, 5), "a1 b8 e9 a8 00")
    chk("A5 0x55B960 bytes", be(b, 0x55B960, 3), "ff 52 5c")
    chk("A8 +0x98 gate bytes at 0x55B9F0", be(b, 0x55B9F0, 6), "8a 81 98 00 00 00")

    # A4: 0x55B8C3 是否边界
    e = A.entry_at_or_before(rows, 0x55B8C3)
    ok, insn, why = A.boundary_check(b, e[0], 0x55B8C3)
    print("  [%s] A4 0x55B8C3 boundary=%s (%s) covering=%s"
          % (PASS if not ok else FAIL, ok, why,
             ("%08X %s %s" % (insn.address, insn.mnemonic, insn.op_str)) if insn else None))
    print("       raw: 0x55B8C0 = %s" % be(b, 0x55B8C0, 16))

    # A6: 68 00 00 01 00 在 [0x55B000,0x55C000)
    t = b.text
    buf = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    pat = bytes.fromhex("6800000100")
    lo = 0x55B000 - t["va"]
    hi = 0x55C000 - t["va"]
    n = 0
    i = lo
    while True:
        i = buf.find(pat, i, hi)
        if i < 0:
            break
        n += 1
        i += 1
    chk("A6 '68 00 00 01 00' hits in [0x55B000,0x55C000)", n, 0)

    # A7: 11 个 call 站点 + 39 字节块长
    want_sites = [0x55B912, 0x55B939, 0x55B960, 0x55B987, 0x55B9AE,
                  0x55B9D5, 0x55B9FC, 0x55BA23, 0x55BA4A, 0x55BA71, 0x55BA98]
    got = []
    for insn in A.linear_from(b, 0x55B8F0, 0x1B0):
        if insn.mnemonic == "call" and "+ 0x5c]" in insn.op_str:
            got.append(insn.address)
    chk("A7 11 slot-5C call sites", got, want_sites)
    starts = [0x55B8F0, 0x55B918, 0x55B93F, 0x55B966, 0x55B98D,
              0x55B9B4, 0x55B9DB, 0x55BA02, 0x55BA29, 0x55BA50, 0x55BA77]
    diffs = [starts[i + 1] - starts[i] for i in range(10)]
    chk("A7 block strides (first 0x28, rest 0x27)",
        ["0x%X" % d for d in diffs], ["0x28"] + ["0x27"] * 9)

    print()
    print("=" * 92)
    print("B · 0x55AFB0 与调用链（B1-B2）")
    print("=" * 92)
    chk("B1 0x55DC9E bytes", be(b, 0x55DC9E, 5), "e8 0d d3 ff ff")
    # rel32 解析
    insns = {i.address: i for i in A.linear_from(b, 0x55DC90, 0x20)}
    ins = insns.get(0x55DC9E)
    print("     0x55DC9E decoded: %s %s" % (ins.mnemonic, ins.op_str) if ins else "     not decoded")

    sites = []
    for insn in A.linear_from(b, 0x55AFB0, 1901):
        if insn.mnemonic == "call" and "+ 0x5c]" in insn.op_str:
            sites.append((insn.address, insn.op_str))
    print("     B2 0x55AFB0 slot-5C sites = %d" % len(sites))
    for a, o in sites:
        print("        %08X  call %s   bytes=%s" % (a, o, be(b, a, 3)))
    n52 = sum(1 for a, o in sites if "[edx" in o)
    n50 = sum(1 for a, o in sites if "[eax" in o)
    print("     [%s] B2 expect 7x edx + 1x eax -> got edx=%d eax=%d"
          % (PASS if (n52 == 7 and n50 == 1) else FAIL, n52, n50))

    print()
    print("=" * 92)
    print("C/D · BulletClass::AI 0x4666E0 回边，与 0x55AFB0 / 0x55D360 回边数")
    print("=" * 92)
    for entry, label in ((0x4666E0, "C1 BulletClass::AI"),
                         (0x55AFB0, "D1 0x55AFB0"),
                         (0x55D360, "D1 0x55D360")):
        r = rec.get(entry)
        if not r:
            print("  %s: not in atlas" % label)
            continue
        size = int(r["size"])
        backs, ninsn = count_backedges(b, entry, size)
        print("  %s entry=%08X size=%d(decimal) insns=%d  backedges=%d"
              % (label, entry, size, ninsn, len(backs)))
        for site, tgt, txt in backs:
            print("       %08X -> %08X   %s" % (site, tgt, txt))


if __name__ == "__main__":
    main()
