"""Lead 抽验：交叉核对「含 call [reg+0x5C] 的函数」与「引用 ObjectClass 类型数组的函数」。

回答 ① 的核心缺口：到底有没有一个可达函数在遍历对象数组并调 AI（槽 0x5C）。

槽 0x5C = AI 已由虚表校准证明：
  BulletClass@@ vt=0x007E46E4 [+0x5C]=0x4666E0
  UnitClass@@   vt=0x007F5C70 [+0x5C]=0x007360C0
  AircraftClass@@ vt=0x007E22A4 [+0x5C]=0x00414BB0
  InfantryClass@@ vt=0x007EB058 [+0x5C]=0x0051BAB0
  BuildingClass@@ vt=0x007E3EBC [+0x5C]=0x0043FB20
（+0x2C 的 WhatAmI 返回值 8/1/2/15/6/61 与 §3.1 一致，校准通过。）
"""
import capstone
import audit_lib as A
import probe_slot5c as S

WATCH = {
    0x00B0F730: "AbstractClass::Array.Count",
    0x008B4118: "UnitClass::Array.Count",
    0x008B410C: "UnitClass::Array.Items",
    0x00A83DF8: "InfantryClass::Array.Count",
    0x00A83DEC: "InfantryClass::Array.Items",
    0x00A8EB50: "BuildingClass::Array.Count",
    0x00A8EB44: "BuildingClass::Array.Items",
    0x00A8E3A0: "AircraftClass::Array.Count",
    0x00A8E394: "AircraftClass::Array.Items",
    0x00A8ED50: "BulletClass::Array.Count",
    0x00A8ED44: "BulletClass::Array.Items",
    0x008B41A0: "?0x8B41A0.Count",
    0x008B4194: "?0x8B4194.Items",
}


def refs_in_fn(b, entry, size):
    """返回该函数体内所有绝对 .data 引用（mem base=0 index=0）。"""
    out = set()
    for insn in A.linear_from(b, entry, size):
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM:
                m = op.mem
                if m.base == 0 and m.index == 0:
                    out.add(m.disp & 0xFFFFFFFF)
    return out


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    rec = dict(rows)
    entries = [v for v, _ in rows]

    raw, good, bad = S.scan_call_5c(b, rows)
    by_fn = {}
    for h in good:
        by_fn.setdefault(h["from_entry"], []).append(h["va"])

    print("functions with a boundary-verified call [reg+0x5C] : %d" % len(by_fn))
    print()
    print("=" * 100)
    print("Which of them reference an ObjectClass type array?")
    print("=" * 100)
    found_any = False
    for fn in sorted(by_fn):
        r = rec.get(fn)
        if not r:
            continue
        size = int(r["size"])
        addrs = refs_in_fn(b, fn, size)
        hit = sorted(a for a in addrs if a in WATCH)
        if hit:
            found_any = True
            print("  fn %08X (size=%d, sites=%d)" % (fn, size, len(by_fn[fn])))
            for a in hit:
                print("      ref %08X  %s" % (a, WATCH[a]))
    if not found_any:
        print("  （无）")

    print()
    print("=" * 100)
    print("Who references the object arrays AT ALL (regardless of slot-5C), top by count")
    print("=" * 100)
    for addr, label in sorted(WATCH.items(), key=lambda t: t[1]):
        homes = []
        for fn in sorted(rec):
            r = rec[fn]
            if int(r["size"]) > 20000:
                continue
            if addr in refs_in_fn(b, fn, int(r["size"])):
                homes.append(fn)
        print("  %08X %-28s referenced by %d functions: %s"
              % (addr, label, len(homes), [hex(x) for x in homes[:14]]
                 + (["..."] if len(homes) > 14 else [])))


if __name__ == "__main__":
    main()
