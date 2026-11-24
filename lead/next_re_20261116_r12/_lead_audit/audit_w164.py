"""Lead 抽验 W164 的三条 LEAD_AUDIT。

A1 0x736204 = 8b 8e 78 02 00 00 85 c9 74 05 8b 01 ff 50 5c  （call [eax+0x5C]，带 NULL 门）
A2 移动/寻路门控 @0x4B055A：+0x54 dword == -1 或 byte[+0x5F]==0 ⇒ 跳过寻路；
   原始字节 rd(0x4B056A,10) 应为 38 5e 5f 0f 84 f9 00 00 00
A3 每帧更新槽是 Locomotion offset=4 子表 槽16 (+0x40)，不是 +0x5C；
   并核对 +0x5C 目标 0x55A910 是不是 stdcall `ret 4`
   另：SearchCore 0x429D6D = 544 条指令；轮数上限 0xFFF7
"""
import capstone
import audit_lib as A


def check_bytes(b, va, n, want):
    got = b.read(va, n).hex(" ").replace(" ", "")
    w = want.replace(" ", "")
    return got, (got == w)


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    rec = dict(rows)

    print("=" * 92)
    print("A1 · 0x736204 的 call [eax+0x5C] + NULL 门")
    print("=" * 92)
    want = "8b8e780200 0085c974058b01ff505c".replace(" ", "")
    got, ok = check_bytes(b, 0x736204, 15, want)
    print("  bytes = %s" % got)
    print("  want  = %s   %s" % (want, "PASS" if ok else "**DIFF**"))
    print("  解码（从 0x7361F0 起，skipdata）:")
    for insn in A.linear_from(b, 0x7361F0, 0x30):
        if 0x7361F0 <= insn.address <= 0x736214:
            mark = "  <== " if insn.address == 0x736204 else ""
            print("     %08X  %-8s %-34s %s" % (insn.address, insn.mnemonic, insn.op_str, mark))

    print()
    print("=" * 92)
    print("A2 · 寻路门控 @0x4B055A")
    print("=" * 92)
    print("  原始字节 @0x4B055A (16B) = %s" % b.read(0x4B055A, 16).hex(" "))
    print("  原始字节 @0x4B056A (10B) = %s   (W164 报 385e5f0f84f9000000…)" % b.read(0x4B056A, 10).hex(" "))
    print("  解码 0x4B0540..0x4B0580:")
    for insn in A.linear_from(b, 0x4B0500, 0x90):
        if 0x4B0540 <= insn.address <= 0x4B0580:
            print("     %08X  %-8s %-36s" % (insn.address, insn.mnemonic, insn.op_str))
    print()
    print("  0x4B0500 atlas: %s" % rec.get(0x4B0500))

    print()
    print("=" * 92)
    print("A3 · 更新槽 +0x40 vs +0x5C；+0x5C 目标是否 stdcall ret 4")
    print("=" * 92)
    # 0x55A910 的末尾
    print("  0x55A910 tail bytes: %s" % b.read(0x55A910 + 0x20, 16).hex(" "))
    print("  0x55A910 atlas: %s" % rec.get(0x55A910))
    if 0x55A910 in rec:
        size = int(rec[0x55A910]["size"])
        ins = list(A.linear_from(b, 0x55A910, size))
        print("  last 5 insns of 0x55A910:")
        for i in ins[-5:]:
            print("     %08X  %-8s %-30s %s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex(" ")))

    print()
    print("--- SearchCore 0x429D6D ---")
    r = rec.get(0x429D6D)
    print("  atlas: %s" % r)
    if r:
        ins = list(A.linear_from(b, 0x429D6D, int(r["size"])))
        print("  instructions in atlas size = %d" % len(ins))
        backs = [(i.address, int(i.op_str, 16), i.mnemonic) for i in ins
                 if i.mnemonic.startswith("j") and i.op_str.startswith("0x")
                 and int(i.op_str, 16) <= i.address]
        print("  backedges = %d : %s" % (len(backs), [(hex(a), hex(t)) for a, t, _ in backs]))
        # 找 0xFFF7 常量
        for i in ins:
            if "0xfff7" in i.op_str.lower():
                print("  const 0xFFF7 at %08X : %s %s" % (i.address, i.mnemonic, i.op_str))

    print()
    print("--- Locomotion offset=4 子表：槽 16(+0x40) 与 槽 23(+0x5C) 的值 ---")
    import json
    d = json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json",
                       encoding="utf-8"))
    loco = [v for v in d["vtables"] if "LocomotionClass" in v["class"]]
    print("  LocomotionClass vtables: %d" % len(loco))
    for v in loco[:4]:
        vt = v["vt"]
        vals = []
        for slot in (16, 23):
            try:
                vals.append((slot, b.u32(vt + 4 * slot)))
            except Exception:
                vals.append((slot, None))
        print("     vt=%08X col_off=%-3d %-46s  slot16=%s slot23=%s"
              % (vt, v["col_offset"], v["class"][:46],
                 hex(vals[0][1]) if vals[0][1] else "?",
                 hex(vals[1][1]) if vals[1][1] else "?"))


if __name__ == "__main__":
    main()
