"""Lead 抽验 W163 的三条 LEAD_AUDIT。

A1 容器 0xB0CE78：Items 0xB0CE7C / Count 0xB0CE88；各自引用计数（W163 报 25 / 27）
A2 0x6D2790 的回边（W163 报 2 条：0x6D2A15->0x6D27BF、0x6D29BE->0x6D29A0）
A3 子弹->脏矩形 Add 的深度 3 路径：
   0x4666E0 --0x4668B8/0x467F2D--> 0x421EA0 --0x4222E0/0x422433/0x4224E0--> 0x5F4EC0 --0x5F5146--> 0x6D2790
"""
import capstone
import audit_lib as A


def count_refs(b, disp):
    m = A.md32(skipdata=True)
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    n = 0
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0:
            continue
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
                if (op.mem.disp & 0xFFFFFFFF) == disp:
                    n += 1
                    break
    return n


def call_sites(b, target):
    """找出所有 call rel32 指向 target 的站点（无对齐假设）。"""
    import struct
    t = b.text
    buf = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    out = []
    for i in range(len(buf) - 5):
        if buf[i] != 0xE8:
            continue
        d = struct.unpack("<i", buf[i + 1:i + 5])[0]
        if t["va"] + i + 5 + d == target:
            out.append(t["va"] + i)
    return out


def backedges(b, entry, size):
    out = []
    n = 0
    for insn in A.linear_from(b, entry, size):
        n += 1
        if insn.mnemonic.startswith("j") and insn.op_str.startswith("0x"):
            t = int(insn.op_str, 16)
            if t <= insn.address:
                out.append((insn.address, t, insn.mnemonic))
    return out, n


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    rec = dict(rows)

    print("=" * 90)
    print("A1 · 脏矩形容器 0xB0CE78 的引用计数")
    print("=" * 90)
    for name, va, want in (("Items", 0xB0CE7C, 25), ("Count", 0xB0CE88, 27)):
        got = count_refs(b, va)
        print("  %-6s %08X refs=%d (W163: %d) %s"
              % (name, va, got, want, "PASS" if got == want else "**DIFF**"))
    # 也报 base 与 Cap
    for name, va in (("base(vptr)", 0xB0CE78), ("Capacity", 0xB0CE80), ("Increment", 0xB0CE8C)):
        print("  %-11s %08X refs=%d" % (name, va, count_refs(b, va)))

    print()
    print("=" * 90)
    print("A2 · 0x6D2790 的回边")
    print("=" * 90)
    r = rec.get(0x6D2790)
    size = int(r["size"])
    backs, n = backedges(b, 0x6D2790, size)
    print("  atlas: size=%d n_instr=%s n_callers=%s" % (size, r["n_instr"], r["n_callers"]))
    print("  linear insns=%d  backedges=%d" % (n, len(backs)))
    for s, t, m in backs:
        print("     %08X -> %08X  %s" % (s, t, m))
    want = {(0x6D2A15, 0x6D27BF), (0x6D29BE, 0x6D29A0)}
    got = {(s, t) for s, t, _ in backs}
    print("  W163 报的两条是否都在: %s" % (want <= got))
    print("  缺失: %s ; 多出: %s" % (sorted(want - got), sorted(got - want)))

    print()
    print("=" * 90)
    print("A3 · 深度 3 路径的每个调用点（无对齐假设 + 边界校验）")
    print("=" * 90)
    edges = [
        (0x4666E0, 0x421EA0, [0x4668B8, 0x467F2D]),
        (0x421EA0, 0x5F4EC0, [0x4222E0, 0x422433, 0x4224E0]),
        (0x5F4EC0, 0x6D2790, [0x5F5146]),
    ]
    for src, dst, want_sites in edges:
        sites = call_sites(b, dst)
        in_src = [s for s in sites if src <= s < src + int(rec[src]["size"])]
        print("  %08X -> %08X : 全镜像 %d 个调用点；src 内 %s"
              % (src, dst, len(sites), [hex(x) for x in in_src]))
        for s in in_src:
            ok, insn, why = A.boundary_check(b, src, s)
            print("       site %08X boundary=%s (%s) insn=%s"
                  % (s, ok, why, ("%s %s" % (insn.mnemonic, insn.op_str)) if insn else None))
        missing = set(want_sites) - set(in_src)
        if missing:
            print("       **W163 报的站点里缺这些**: %s" % sorted(hex(x) for x in missing))

    print()
    print("=" * 90)
    print("附 · 0x6D2790 的循环结构（判断 O(k)/O(k^2) 的关键）")
    print("=" * 90)
    for insn in A.linear_from(b, 0x6D2790, size):
        if 0x6D27B0 <= insn.address <= 0x6D27D8 or 0x6D2990 <= insn.address <= 0x6D29C8 \
                or 0x6D2A00 <= insn.address <= 0x6D2A20:
            print("   %08X  %-10s %s" % (insn.address, insn.mnemonic, insn.op_str))


if __name__ == "__main__":
    main()
