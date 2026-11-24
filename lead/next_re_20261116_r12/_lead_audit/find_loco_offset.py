"""静态确定「对象 → LocomotionClass*」的成员偏移。

思路：每帧更新槽是 Locomotion `col_offset=4` 子表的槽16（+0x40）。
既然偏移 4 的子对象，vptr 在 [loco+4]，调用形态应是：
    mov reg, [obj + OFF]      ; reg = loco  (或 loco+4)
    mov vptr, [reg + 4]
    ...
    call [vptr + 0x40]
所以我们扫全镜像的 `call [reg+0x40]`，再回溯找 `[对象基址 + OFF]` 的装载，统计 OFF。
"""
import capstone
import audit_lib as A


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    m = A.md32(skipdata=True)
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]

    # 先收集全部指令（便于按地址回溯）
    insns = {}
    order = []
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0:
            continue
        insns[insn.address] = insn
        order.append(insn.address)
    order.sort()
    import bisect

    hits = []
    for va in order:
        insn = insns[va]
        if insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != capstone.x86.X86_OP_MEM:
            continue
        if (op.mem.disp & 0xFFFFFFFF) != 0x40:
            continue
        hits.append((insn, op.mem))

    print("全镜像 `call [<mem>+0x40]` 站点数 = %d" % len(hits))
    print()

    # 对每个站点回溯：找最后一个 "mov X, [Y + disp]" 且其后有 "mov Z,[X+4]"
    off_hist = {}
    shown = 0
    for insn, mem in hits:
        i = bisect.bisect_left(order, insn.address)
        window = [insns[a] for a in order[max(0, i - 14):i]]
        # 找 mov dst,[base+disp] 形态
        cand = []
        for w in window:
            if w.mnemonic != "mov" or len(w.operands) != 2:
                continue
            d, s = w.operands
            if s.type == capstone.x86.X86_OP_MEM and d.type == capstone.x86.X86_OP_REG:
                if s.mem.index == 0 and s.mem.base != 0 and s.mem.disp != 0:
                    cand.append((w.address, d.reg, s.mem.base, s.mem.disp))
        # 取最后一个候选
        tag = ""
        if cand:
            a, dreg, base, disp = cand[-1]
            off_hist[disp] = off_hist.get(disp, 0) + 1
            tag = "← [%s+0x%X]" % (insns[a].reg_name(base), disp)
        if shown < 25:
            e = A.entry_at_or_before(rows, insn.address)
            print("  %08X  call [%s+0x40]  fn=%08X  %s"
                  % (insn.address, insns[insn.address].reg_name(mem.base), e[0], tag))
            shown += 1

    print()
    print("=== 回溯到的 disp 直方图（候选的对象→loco 偏移）===")
    for disp, n in sorted(off_hist.items(), key=lambda kv: -kv[1])[:15]:
        print("   disp=0x%-6X  x%d" % (disp, n))


if __name__ == "__main__":
    main()
