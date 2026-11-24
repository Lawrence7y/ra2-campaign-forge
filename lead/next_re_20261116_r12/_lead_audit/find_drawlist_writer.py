"""找绘制列表 `0x8A0394`(Items)/`0x8A03A0`(Count) 的**写入路径**。

已知：直接 `mov [0x8A0394], reg` / `mov [0x8A03A0], reg` 形式**0 处**
     ⇒ 只能通过间接方式写入。三条候选通道：
  C1 结构体整体拷贝（`rep movs` / `movsd`），源或目标是含该数组的静态对象
  C2 通过指针间接写（`mov reg,<base>` 后再 `mov [reg+off]`）—— 需要找谁把 `0x8A0394` 当基址
  C3 该数组是某静态对象 `X` 的成员，写入用的是 `mov [X+off]`，需先定 X 的基址

本脚本做：
  A) 列出所有**读** `0x8A0394`/`0x8A03A0` 的站点，用「函数区间包含」判归属（纪律 17）
  B) 找 `0x8A0394` 之前若干 dword 内是否有可识别的 vftable（判定该数组的容器基址 X）
  C) 若找到 X，则扫所有 `[reg+off]` 且 off 对应 Count 位置的写点
"""
import capstone
import json

import audit_lib as A

VTJSON = (r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10"
          r"\W130_atlas\vtables_canonical.json")

ITEMS = 0x008A0394
COUNT = 0x008A03A0


def owner_by_range(rows, site):
    for v, r in rows:
        size = int(r["size"])
        if v <= site < v + size:
            return v, size
    return None


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    rec = dict(rows)
    vtmap = {}
    d = json.load(open(VTJSON, encoding="utf-8"))
    for v in d["vtables"]:
        vtmap.setdefault(v["vt"], []).append((v["class"], v["col_offset"]))

    # ---------- A) 读点及其归属（区间包含通道） ----------
    m = A.md32(skipdata=True)
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    print("=" * 96)
    print("A) 所有引用 0x8A0394 / 0x8A03A0 的站点（区间包含判归属）")
    print("=" * 96)
    sites = []
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0 or not insn.operands:
            continue
        for k, op in enumerate(insn.operands):
            if (op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0
                    and op.mem.index == 0 and (op.mem.disp & 0xFFFFFFFF) in (ITEMS, COUNT)):
                sites.append((insn.address, op.mem.disp & 0xFFFFFFFF, k, insn.mnemonic, insn.op_str))
                break
    print("%-10s %-10s %-3s %-6s %-30s %s" % ("site", "global", "op#", "mn", "operands", "owner(区间)"))
    for a, g, k, mn, os_ in sites:
        ow = owner_by_range(rows, a)
        owt = ("fn %08X" % ow[0]) if ow else "NOT IN ATLAS"
        print("%08X %08X %-3d %-6s %-30s %s" % (a, g, k, mn, os_[:30], owt))
    print()
    print("写形式（op0 且 mnemonic==mov）数量：%d"
          % sum(1 for a, g, k, mn, os_ in sites if k == 0 and mn == "mov"))

    # ---------- B) 找容器基址：ITEMS 之前有哪些 dword 像 vftable ----------
    print()
    print("=" * 96)
    print("B) ITEMS(0x8A0394) 之前 0x40 字节内的 dword，检查是否像 vftable")
    print("=" * 96)
    for off in range(0x40, 0, -4):
        va = ITEMS - off
        try:
            val = b.u32(va)
        except Exception:
            continue
        cand = vtmap.get(val)
        mark = ""
        if cand:
            mark = "  <== vftable: %s" % cand[0][0]
        print("  %08X = %08X%s" % (va, val, mark))
    print()
    print("  同理 COUNT(0x8A03A0) 之前：")
    for off in range(0x20, 0, -4):
        va = COUNT - off
        try:
            val = b.u32(va)
        except Exception:
            continue
        cand = vtmap.get(val)
        print("  %08X = %08X%s" % (va, val, ("  <== vftable: %s" % cand[0][0]) if cand else ""))


if __name__ == "__main__":
    main()
