"""§914 的独立复验：用**与写作时完全不同的方法**再判一次 0x43F180 的 mode 语义。

不复用之前的思路。这里用三条互相独立的判据：
  P1 穷举：该函数内到底有几处 grid 操作调用（0x5683C0 / 0x5687F0）？分别在哪个可达分支？
  P2 分支归属：从函数入口按跳表逐个 mode 走一遍**不跟随循环**的近似路径，看每条路径能否到达
     0x43F1D5（摘链）/ 0x43F691（挂链）。
  P3 寄存器：ebp 在 0x43F658 处的值，回溯所有写入点，判断它是否可能等于入口 mode。

判据 P2 用"可达性闭包"而不是人工跟读：把函数体切成指令图（顺序 + 相对跳转 + 跳表目标），
从每个 mode 的跳表目标做 BFS，看能否到达两个 grid 调用点。这样不依赖我对某段代码的肉眼理解。
"""
import capstone
import audit_lib as A

TARGETS = {0x5683C0: "LINK(挂链)", 0x5687F0: "UNLINK(摘链)"}


def build_graph(b, entry, size):
    """建立地址 -> 后继地址 的图：(a) 顺序下一条 (b) 相对跳转目标 (c) ret 无后继。"""
    ins = list(A.linear_from(b, entry, size))
    by_va = {i.address: i for i in ins}
    order = sorted(by_va)
    import bisect
    succ = {}
    for k, va in enumerate(order):
        i = by_va[va]
        nxt = []
        if i.mnemonic == "ret":
            succ[va] = []
            continue
        # 顺序后继
        if k + 1 < len(order):
            nxt.append(order[k + 1])
        # 跳转目标
        if i.mnemonic.startswith("j") and i.op_str.startswith("0x"):
            t = int(i.op_str, 16)
            if t in by_va:
                nxt.append(t)
        succ[va] = nxt
    return succ, by_va, order


def reachable(succ, starts):
    seen = set()
    stack = list(starts)
    while stack:
        x = stack.pop()
        if x in seen or x not in succ:
            continue
        seen.add(x)
        stack.extend(succ[x])
    return seen


def main():
    b = A.Bin()
    ins = list(A.linear_from(b, 0x43F180, 2443))
    by_va = {i.address: i for i in ins}
    succ, _, order = build_graph(b, 0x43F180, 2443)

    print("=" * 86)
    print("P1 · 穷举该函数内所有 grid 操作调用")
    print("=" * 86)
    grid = []
    for i in ins:
        if i.mnemonic == "call" and i.op_str.startswith("0x"):
            t = int(i.op_str, 16)
            if t in TARGETS:
                grid.append((i.address, t))
    for a, t in grid:
        print("   %08X  call %08X  %s" % (a, t, TARGETS[t]))
    print("   共 %d 处" % len(grid))
    assert len(grid) == 2, "预期恰好 2 处 grid 调用"

    print()
    print("=" * 86)
    print("P2 · 从每个 mode 的跳表目标做可达性 BFS")
    print("=" * 86)
    # 跳表
    tbl = {}
    for n in range(4):
        tbl[n] = b.u32(0x43FB0C + 4 * n)
    print("   跳表 0x43FB0C: %s" % {k: hex(v) for k, v in tbl.items()})
    unlink_site = grid[0][0] if grid[0][1] == 0x5687F0 else grid[1][0]
    link_site = grid[0][0] if grid[0][1] == 0x5683C0 else grid[1][0]
    for mode in range(4):
        start = tbl[mode]
        r = reachable(succ, [start])
        print("   mode %d -> start %08X : 可达 %4d 条；%s  %s"
              % (mode, start, len(r),
                 "能到摘链(%08X)" % unlink_site if unlink_site in r else "到不了摘链",
                 "能到挂链(%08X)" % link_site if link_site in r else "到不了挂链"))

    print()
    print("=" * 86)
    print("P3 · ebp 在 0x43F658 处的值来源（回溯全部写入点）")
    print("=" * 86)
    idx = {a: k for k, a in enumerate(order)}
    k = idx[0x43F658]
    writes = []
    for j in range(k - 1, -1, -1):
        i = by_va[order[j]]
        dst = i.op_str.split(",")[0].strip() if "," in i.op_str else ""
        if dst == "ebp" or (i.mnemonic == "pop" and i.op_str == "ebp"):
            writes.append((i.address, "%s %s" % (i.mnemonic, i.op_str)))
        if len(writes) >= 4:
            break
    print("   入口: 0x43F188 mov ebp,[esp+0xBC]  (ebp = mode 参数)")
    print("   跳表分派后第一处清零/覆写:")
    for j, va in enumerate(order):
        i = by_va[va]
        if 0x43F1C3 <= va <= 0x43F250:
            dst = i.op_str.split(",")[0].strip() if "," in i.op_str else ""
            if dst == "ebp":
                print("      %08X  %s %s   <== ebp 被覆写" % (i.address, i.mnemonic, i.op_str))
    print("   0x43F658 之前最近的 ebp 写入（倒序）:")
    for a, t in writes:
        print("      %08X  %s" % (a, t))
    print()
    print("   ⇒ 若 0x43F658 之前存在 xor ebp,ebp / lea ebp,[...]，则 cmp ebp,3 的 ebp 不是 mode。")


if __name__ == "__main__":
    main()
