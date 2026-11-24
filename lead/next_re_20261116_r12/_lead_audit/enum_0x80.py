"""枚举所有 byte [reg+0x80] 的写入点，并按「写入函数所属类」分组。

目的：判定 `[+0x80]`（绘制剔除三重判据的第一个）到底是什么语义。
关键纪律（R13_COMMON 第 14 条）：不能只看偏移，必须确认**基址寄存器属于哪个类的实例**。
做法：对每个写入点，回溯该函数的入口，用 canonical 虚表反查它属于哪个类；
      若该函数不是虚表入口，则给出它的调用者链（最多 2 层）帮助定位。
"""
import json
import re

import audit_lib as A

VTJSON = (r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10"
          r"\W130_atlas\vtables_canonical.json")


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    rec = dict(rows)
    d = json.load(open(VTJSON, encoding="utf-8"))
    # vt -> (class, col_offset)
    vtmap = {}
    for v in d["vtables"]:
        vtmap.setdefault(v["vt"], []).append((v["class"], v["col_offset"]))

    import capstone
    m = A.md32(skipdata=True)
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]

    writes = []   # (site, fn, value_expr, mnemonics)
    reads = 0
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0 or not insn.operands:
            continue
        op0 = insn.operands[0]
        if op0.type != capstone.x86.X86_OP_MEM:
            continue
        if (op0.mem.disp & 0xFFFFFFFF) != 0x80 or op0.mem.base == 0 or op0.mem.index != 0:
            continue
        if op0.size != 1:          # 只关心 byte 访问
            continue
        e = A.entry_at_or_before(rows, insn.address)
        dst_is_mem = insn.op_str.split(",")[0].strip().startswith("byte ptr")
        is_write = dst_is_mem and insn.mnemonic in (
            "mov", "or", "and", "xor", "inc", "dec", "add", "sub", "not")
        if is_write:
            writes.append((insn.address, e[0], insn.op_str, insn.mnemonic))
        else:
            reads += 1

    print("byte [reg+0x80] : 写=%d  读=%d" % (len(writes), reads))
    print()

    # 按写入函数分组
    groups = {}
    for site, fn, txt, mn in writes:
        groups.setdefault(fn, []).append((site, txt, mn))

    print("写点分布在 %d 个函数" % len(groups))
    print()
    print("%-10s %4s %-34s %-26s %s" % ("fn", "n写", "所属类(虚表)", "写值", "strings"))
    for fn in sorted(groups, key=lambda f: -len(groups[f])):
        items = groups[fn]
        cls = vtmap.get(fn)
        clsname = ("%s(col%d)" % (cls[0][0], cls[0][1])) if cls else "(非虚表基址)"
        vals = sorted({txt.split(",")[-1].strip() for _, txt, _ in items})
        r = rec.get(fn)
        print("%08X %4d %-34s %-26s %s"
              % (fn, len(items), clsname[:34], ",".join(vals)[:26],
                 ((r.get("strings") or "")[:40] if r else "")))

    print()
    print("=== 写值分布 ===")
    from collections import Counter
    allv = Counter(txt.split(",")[-1].strip() for _, _, txt, _ in writes)
    for v, c in allv.most_common():
        print("   值 %-10s : %d 处" % (v, c))

    print()
    print("=== 写 0 的站点（可能是「清除标志」）===")
    for site, fn, txt, mn in writes:
        if txt.split(",")[-1].strip() == "0":
            print("   %08X  fn=%08X  %s" % (site, fn, txt))
    print()
    print("=== 写 1 的站点 ===")
    for site, fn, txt, mn in writes:
        if txt.split(",")[-1].strip() == "1":
            print("   %08X  fn=%08X  %s" % (site, fn, txt))


if __name__ == "__main__":
    main()
