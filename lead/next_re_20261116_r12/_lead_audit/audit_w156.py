"""Lead 抽验 W156 的 LEAD_AUDIT 三项。用自己的工具，不 import W156 代码。

1) 写 [0xA8EB50] 的站点：字节通道应只有 0x43BB18（89 0d 50 eb a8 00），
   另有 NOFUNC 0x4E6B91（a3 50 eb a8 00）；并复核"8 个写者其实是读者"。
2) IAT 0x7E127C（HeapFree）的 call 站点数 = 3；对照 HeapAlloc call 站点数。
3) 注销原语 0x45AE10 的字节 + 调用站点；0x43BCF0 内对 0x5687F0 与 [reg+0x124] 的引用数 = 0。
"""
import capstone
import audit_lib as A

TARGET = 0xA8EB50
HEAPFREE_IAT = 0x7E127C


def abs_refs(b, target):
    """全 .text 找所有绝对引用 target 的指令，区分读/写。"""
    m = A.md32(skipdata=True)
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    out = []
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0:
            continue
        for idx, op in enumerate(insn.operands):
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
                if (op.mem.disp & 0xFFFFFFFF) == target:
                    write = (idx == 0 and insn.mnemonic in
                             ("mov", "movzx", "add", "sub", "inc", "dec", "or", "and", "xor", "neg", "not"))
                    out.append(dict(va=insn.address, mnem=insn.mnemonic,
                                    text="%s %s" % (insn.mnemonic, insn.op_str),
                                    write=write, bytes=insn.bytes.hex(" ")))
    return out


def iat_calls(b, iat_va):
    """找 `call dword ptr [iat_va]` 站点（ff 15 <iat>）。"""
    m = A.md32(skipdata=True)
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    out = []
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0 or insn.mnemonic != "call":
            continue
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
                if (op.mem.disp & 0xFFFFFFFF) == iat_va:
                    out.append(dict(va=insn.address, bytes=insn.bytes.hex(" ")))
    return out


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    rec = dict(rows)
    entries = [v for v, _ in rows]

    def owner(va):
        e = A.entry_at_or_before(rows, va)
        ok, _, _ = A.boundary_check(b, e[0], va)
        return e[0], ok

    print("=" * 96)
    print("1) all absolute references to 0xA8EB50 (BuildingClass::Array.Count)")
    print("=" * 96)
    refs = abs_refs(b, TARGET)
    print("total refs = %d" % len(refs))
    writes = [r for r in refs if r["write"]]
    reads = [r for r in refs if not r["write"]]
    print("  writes = %d, reads = %d" % (len(writes), len(reads)))
    for r in writes:
        fn, okb = owner(r["va"])
        print("    WRITE %08X  %-34s bytes=%-20s fn=%08X boundary=%s"
              % (r["va"], r["text"], r["bytes"], fn, okb))
    fns = {}
    for r in refs:
        fn, _ = owner(r["va"])
        fns.setdefault(fn, [0, 0])
        fns[fn][0 if r["write"] else 1] += 1
    print("  distinct functions = %d" % len(fns))
    for fn in sorted(fns):
        w, rd = fns[fn]
        print("    fn %08X  W=%d R=%d" % (fn, w, rd))

    print()
    print("=" * 96)
    print("2) HeapFree / HeapAlloc IAT call sites")
    print("=" * 96)
    hf = iat_calls(b, HEAPFREE_IAT)
    print("  HeapFree IAT %08X call sites = %d" % (HEAPFREE_IAT, len(hf)))
    for h in hf:
        print("    %08X  bytes=%s" % (h["va"], h["bytes"]))
    # 找 HeapAlloc 的 IAT：扫 IAT 区里相邻项，用导入名定位更稳，这里退化为列 IAT 附近
    print("  --- 用 pefile 取导入名核对 ---")
    pe = b.pe
    try:
        pe.parse_data_directories()
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            for imp in entry.imports:
                if imp.name and imp.name.decode(errors="replace") in ("HeapFree", "HeapAlloc", "HeapReAlloc"):
                    sites = iat_calls(b, imp.address)
                    print("    %-12s IAT=%08X  call sites=%d : %s"
                          % (imp.name.decode(), imp.address, len(sites),
                             [hex(s["va"]) for s in sites]))
    except Exception as e:
        print("    import parse failed:", e)

    print()
    print("=" * 96)
    print("3) 注销原语 0x45AE10 与 0x43BCF0")
    print("=" * 96)
    for va, n, label in ((0x45AE10, 24, "0x45AE10 head"), (0x43BCF0, 32, "0x43BCF0 head")):
        print("  %s:" % label)
        for insn in list(A.linear_from(b, va, n))[:8]:
            print("     %08X  %-8s %-34s %s" % (insn.address, insn.mnemonic, insn.op_str,
                                                insn.bytes.hex(" ")))
    # 0x43BCF0 内是否有 0x5687F0 引用 / [reg+0x124]
    r = rec.get(0x43BCF0)
    size = int(r["size"]) if r else 986
    print("  0x43BCF0 atlas size = %d" % size)
    has_5687 = 0
    has_124 = 0
    calls = []
    for insn in A.linear_from(b, 0x43BCF0, size):
        if insn.mnemonic == "call":
            calls.append((insn.address, insn.op_str))
            if insn.op_str == "0x5687f0":
                has_5687 += 1
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.disp == 0x124:
                has_124 += 1
    print("  refs to 0x5687F0 inside = %d ; mem [reg+0x124] = %d" % (has_5687, has_124))
    print("  calls of interest:")
    for a, o in calls:
        if o in ("0x45ae10", "0x45add0", "0x7c8b3d"):
            print("     %08X  call %s" % (a, o))
    # 0x45AE10 的字节
    print("  0x45AE10 bytes @ +0x0 = %s" % b.read(0x45AE10, 12).hex(" "))


if __name__ == "__main__":
    main()
