"""重新检测 `0x8A0394`/`0x8A03A0` 的写入，**不限定 mnemonic**。

上一轮的教训：只统计 `mnemonic=='mov'` 且 op0 是内存的写入，
会漏掉 `inc dword [glob]` / `add dword [glob],1` / `or` / `and` / `xchg` / `lea`+store 等形态。
本轮改为：**op0 是 `[disp]` 绝对内存寻址的所有指令**（不限 mnemonic），逐个分类读/写。
"""
import capstone

import audit_lib as A

GLOBALS = {
    0x008A0390: "容器A +0 (vftable?)",
    0x008A0394: "容器A +4 (Items)",
    0x008A03A0: "容器A +0x10 (Count)",
    0x008A0364: "容器B +0 (Items)",
    0x008A0370: "容器B +0xC (Count)",
}

# 明确会写目的操作数的 mnemonic
WRITE_MN = {
    "mov", "movzx", "movsx", "add", "sub", "and", "or", "xor", "inc", "dec",
    "not", "neg", "shl", "shr", "sar", "sal", "xchg", "adc", "sbb", "imul",
    "bts", "btr", "btc", "setne", "sete",
}


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    m = A.md32(skipdata=True)
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]

    reads = {g: [] for g in GLOBALS}
    writes = {g: [] for g in GLOBALS}

    for insn in m.disasm(data, t["va"]):
        if insn.id == 0 or not insn.operands:
            continue
        # 遍历**所有**操作数找绝对内存寻址（不能只看 op0：
        # `mov eax,[glob]` 的内存操作数是 op1，只看 op0 会全部漏掉 —— 已踩两次）
        hit_k = None
        hit_d = None
        for k, op in enumerate(insn.operands):
            if (op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0
                    and op.mem.index == 0 and (op.mem.disp & 0xFFFFFFFF) in GLOBALS):
                hit_k = k
                hit_d = op.mem.disp & 0xFFFFFFFF
                break
        if hit_d is None:
            continue
        e = A.entry_at_or_before(rows, insn.address)
        is_write = (hit_k == 0) and (insn.mnemonic in WRITE_MN)
        if is_write:
            writes[hit_d].append((insn.address, e[0], insn.mnemonic, insn.op_str))
        else:
            reads[hit_d].append((insn.address, e[0], insn.mnemonic, insn.op_str))

    print("=" * 100)
    print("按 GLBAL 逐个统计（不限 mnemonic；op0 为绝对内存寻址）")
    print("=" * 100)
    for g, name in GLOBALS.items():
        print("%08X %-24s 写=%d  读=%d" % (g, name, len(writes[g]), len(reads[g])))
    print()

    for g, name in GLOBALS.items():
        if not writes[g]:
            continue
        print("=" * 100)
        print("写点明细：%08X  %s" % (g, name))
        print("=" * 100)
        for a, fn, mn, os_ in writes[g]:
            print("  %08X  fn=%08X  %-6s %s" % (a, fn, mn, os_))
        print()

    print("=" * 100)
    print("容器B 的 Items/Count 组合（0x8A0364 / 0x8A0370）上下文抽样")
    print("=" * 100)
    for g in (0x008A0370,):
        for a, fn, mn, os_ in (writes[g] + reads[g])[:12]:
            print("  %08X  fn=%08X  %-6s %s" % (a, fn, mn, os_))


if __name__ == "__main__":
    main()
