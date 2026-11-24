"""自审计：用「函数区间包含」通道复核本轮的归属判断，
并与 `entry_at_or_before` 通道对比，量化后者在 atlas 空洞处的错归率。
"""
import capstone

import audit_lib as A

SITES = [
    # (站点, 预期归属说明)
    (0x482854, "列表 Count 读"),
    (0x48286C, "列表 Items 读"),
    (0x48299E, "列表 Items 读"),
    (0x482D82, "列表 Count 读"),
    (0x483151, "列表 Items 读"),
    (0x4ADFF0, "列表 Count 读"),
    (0x4AE0B0, "列表 Count 读"),
    (0x6D9800, "遍历器 0x6D97D0 内"),
    (0x6D994D, "遍历器 0x6D9920 内"),
    (0x6D9A58, "遍历器 0x6D9A50 内"),
]


def owner_by_range(rows, site):
    """通道 A：函数 [entry, entry+size) 区间包含。"""
    for v, r in rows:
        size = int(r["size"])
        if v <= site < v + size:
            return v, size
    return None


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    rec = dict(rows)

    print("=" * 92)
    print("通道 A（区间包含） vs 通道 B（entry_at_or_before）")
    print("=" * 92)
    print("%-10s %-22s %-22s %s" % ("site", "区间包含", "entry_at_or_before", "是否一致"))
    mismatch = 0
    for site, desc in SITES:
        a = owner_by_range(rows, site)
        eb = A.entry_at_or_before(rows, site)
        bn = eb[0]
        same = (a is not None and a[0] == bn)
        if not same:
            mismatch += 1
        print("%08X %-22s %-22s %s   %s"
              % (site,
                 ("fn %08X(size %d)" % a) if a else "NOT IN ATLAS",
                 "fn %08X" % bn,
                 "一致" if same else "**不一致**",
                 desc))
    print()
    print("不一致 = %d / %d" % (mismatch, len(SITES)))

    print()
    print("=" * 92)
    print("复算 1：0x4824D4 解码能否覆盖到 0x482854（区间包含通道）")
    print("=" * 92)
    span = 0x482854 - 0x4824D4
    ins = list(A.linear_from(b, 0x4824D4, span + 0x60))
    print("  从 0x4824D4 解码 %d 条，末址 %08X" % (len(ins), ins[-1].address))
    hit = [i.address for i in ins
           if i.mnemonic == "mov" and "0x8a03" in i.op_str.lower()]
    print("  其中引用 0x8A03xx 的指令: %s" % [hex(x) for x in hit])
    print("  预期含 0x482854 / 0x48286C / 0x48295A ⇒ %s"
          % ("PASS" if {0x482854, 0x48286C, 0x48295A} <= set(hit) else "FAIL"))

    print()
    print("=" * 92)
    print("复算 2：0x4824D4 之前最近的 call/jmp 目标（确认它是真入口而非中间位置）")
    print("=" * 92)
    m = A.md32(skipdata=True)
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    tgts = set()
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0 or insn.mnemonic not in ("call", "jmp"):
            continue
        if insn.op_str.startswith("0x"):
            v = int(insn.op_str, 16)
            if 0x482000 <= v <= 0x483400:
                tgts.add(v)
    st = sorted(tgts)
    print("  该段 call/jmp 目标: %s" % [hex(x) for x in st])
    before = [v for v in st if v <= 0x482854]
    print("  0x482854 之前最近 = %08X" % before[-1] if before else "  none")
    print("  ⇒ 0x4824D4 是与 0x482854 同函数的最可能入口（前一个是 %s）"
          % (hex(before[-2]) if len(before) > 1 else "无"))

    print()
    print("=" * 92)
    print("复算 3：三个遍历器的遍历方向（比较首尾初值与更新方向）")
    print("=" * 92)
    for fn, label in ((0x6D97D0, "倒序"), (0x6D9920, "正序")):
        r = rec.get(fn)
        if not r:
            continue
        ins2 = list(A.linear_from(b, fn, int(r["size"])))
        init = [(i.address, i.mnemonic, i.op_str) for i in ins2
                if ("0x8a03a0" in i.op_str.lower() and i.mnemonic == "mov")
                or (i.mnemonic in ("dec", "inc") and "eax" in i.op_str)]
        print("  fn %08X (%s): %s" % (fn, label, [(hex(a), m2, o) for a, m2, o in init][:5]))


if __name__ == "__main__":
    main()
