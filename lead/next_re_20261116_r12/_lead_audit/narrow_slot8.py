"""②-b 静态收窄：从 358 个 `call [reg+0x20]` 站点里筛出**可能摧毁 BuildingClass**的那些。

思路（不要求完整指向分析，只做保守收窄）：
  一个 BuildingClass 指针的来源只有三种：
    (a) BuildingClass::Array  (Items 0xA8EB44 / Count 0xA8EB50)
    (b) 新建（call 构造器 / new）
    (c) 从 AbstractClass::Array(0xB0F730) 或 FootClass::Array 等按 vtable 过滤得到
  因此：**函数体内完全不引用 (a) 也不引用 (c) 的容器、且不调用 BuildingClass 构造器**
  的站点，**不可能**接收一个 BuildingClass ⇒ 可以排除。

对被保留的站点，额外报告它是否引用 `0x5687F0`（摘链）——这是 ②-b 的核心判据
（"先摘链再摧毁" vs "不摘链直接摧毁"）。
"""
import capstone
import audit_lib as A

BUILDING = {0x00A8EB44: "BuildingClass::Array.Items",
            0x00A8EB50: "BuildingClass::Array.Count"}
OTHER_CONTAINERS = {0x00B0F730: "AbstractClass::Array.Count",
                    0x008B4118: "UnitClass::Array.Count",
                    0x00A83DF8: "InfantryClass::Array.Count",
                    0x00A8E3A0: "AircraftClass::Array.Count",
                    0x00A8ED50: "BulletClass::Array.Count"}
UNLINK = 0x005687F0
CTOR = 0x0043B740   # 台账 §890-7 / §892：BuildingClass 构造器


def abs_refs_in(b, entry, size, watch):
    """返回该函数体内对 watch 集合中各绝对地址的引用次数。"""
    out = {}
    if size <= 0 or size > 40000:
        return out
    try:
        insns = A.linear_from(b, entry, size)
    except Exception:
        return out
    for insn in insns:
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
                d = op.mem.disp & 0xFFFFFFFF
                if d in watch:
                    out[d] = out.get(d, 0) + 1
    return out


def calls_in(b, entry, size):
    """该函数体内的直接 call 目标集合。"""
    out = set()
    if size <= 0 or size > 40000:
        return out
    try:
        for insn in A.linear_from(b, entry, size):
            if insn.mnemonic == "call" and insn.op_str.startswith("0x"):
                out.add(int(insn.op_str, 16))
    except Exception:
        pass
    return out


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    rec = dict(rows)

    # 1) 收集 358 个 slot8 站点
    m = A.md32(skipdata=True)
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    sites = []
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0 or insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != capstone.x86.X86_OP_MEM or (op.mem.disp & 0xFFFFFFFF) != 0x20:
            continue
        if op.mem.base == 0 and op.mem.index == 0:
            continue
        e = A.entry_at_or_before(rows, insn.address)
        ok, _, _ = A.boundary_check(b, e[0], insn.address)
        if ok:
            sites.append((insn.address, e[0]))

    # 2) 按函数聚合
    by_fn = {}
    for site, fn in sites:
        by_fn.setdefault(fn, []).append(site)
    print("slot8 站点 %d 个，分布在 %d 个函数" % (len(sites), len(by_fn)))

    # 3) 收窄：函数体引用建筑数组 / 或抽象注册表 / 或调用建筑构造器
    watch = dict(BUILDING)
    watch.update(OTHER_CONTAINERS)
    cand = []
    for fn in sorted(by_fn):
        r = rec.get(fn)
        size = int(r["size"]) if r else 0
        refs = abs_refs_in(b, fn, size, watch)
        cl = calls_in(b, fn, size)
        hits_b = [k for k in refs if k in BUILDING]
        hits_o = [k for k in refs if k in OTHER_CONTAINERS]
        ctor = CTOR in cl
        if hits_b or hits_o or ctor:
            cand.append((fn, by_fn[fn], hits_b, hits_o, ctor, refs, cl))

    print("收窄后候选函数 = %d（含 %d 个站点）"
          % (len(cand), sum(len(c[1]) for c in cand)))
    print()
    print("%-10s %5s %-26s %-30s %-6s %s"
          % ("fn", "n站", "引用建筑数组", "引用其它容器", "调构造", "引用摘链0x5687F0"))
    for fn, ss, hb, ho, ctor, refs, cl in cand:
        bnames = ",".join(BUILDING[k].split("::")[1] for k in hb)
        onames = ",".join(OTHER_CONTAINERS[k].split("::")[0] for k in ho)
        print("%08X %5d %-26s %-30s %-6s %s"
              % (fn, len(ss), bnames or "-", onames or "-",
                 "YES" if ctor else "-", "YES" if UNLINK in cl else "-"))

    print()
    print("=== 关键：引用了建筑数组 + 调 slot8，但**不**引用 0x5687F0 的函数 ===")
    n = 0
    for fn, ss, hb, ho, ctor, refs, cl in cand:
        if hb and UNLINK not in cl:
            n += 1
            print("  fn %08X  站点=%s  建筑数组引用=%s  调构造=%s"
                  % (fn, [hex(x) for x in ss], {hex(k): v for k, v in refs.items() if k in BUILDING},
                     ctor))
    if not n:
        print("  （无）")
    print()
    print("=== 对照：引用了建筑数组 **且** 引用 0x5687F0 的函数 ===")
    for fn, ss, hb, ho, ctor, refs, cl in cand:
        if hb and UNLINK in cl:
            print("  fn %08X  站点=%s" % (fn, [hex(x) for x in ss]))


if __name__ == "__main__":
    main()
