"""Lead 自查：我的 `call [reg+0x5C]` 普查是否漏掉了 SIB 编码形态？

我 §891-3/§891-5 的普查只认 modrm = 0x50..0x57（mod=01, reg=010, rm≠100/101），
即 `call [reg+disp8]` 且 rm 是普通寄存器。

漏掉的形态：
  * modrm = 0x54 : mod=01, rm=100(SIB) ⇒ `call [ -- ][index][base] + disp8`  例：FF 54 XX 5C
  * modrm = 0x94 : mod=10, rm=100(SIB) ⇒ `call [ ... ] + disp32`             例：FF 94 XX XX XX XX 5C(?) 不对
  * modrm = 0x95 : mod=10, rm=101 ⇒ `call [ebp+disp32]`
  * modrm = 0x55 : mod=01, rm=101 ⇒ `call [ebp+disp8]`   ← 我**有**覆盖(0x55 在字典里)

本脚本用「**先反汇编、再看操作数**」的方式重做一遍：不依赖手工 modrm 表，
把所有 `call` 的内存操作数里 disp == 0x5C 的**全部**列出来（含 SIB / base+index）。
"""
import capstone
import audit_lib as A


def calls_with_disp(b, disp=0x5C):
    m = A.md32(skipdata=True)
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    out = []
    for insn in m.disasm(data, t["va"]):
        if insn.id == 0 or insn.mnemonic != "call":
            continue
        if not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != capstone.x86.X86_OP_MEM:
            continue
        mem = op.mem
        if (mem.disp & 0xFFFFFFFF) != disp:
            continue
        out.append(dict(va=insn.address, text="%s %s" % (insn.mnemonic, insn.op_str),
                        base=mem.base, index=mem.index, scale=mem.scale,
                        disp=mem.disp, bytes=insn.bytes.hex(" ")))
    return out


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    hits = calls_with_disp(b, 0x5C)
    print("total `call [<mem>+0x5C]` by operand analysis = %d" % len(hits))
    names = {capstone.x86.X86_REG_EAX: "eax", capstone.x86.X86_REG_ECX: "ecx",
             capstone.x86.X86_REG_EDX: "edx", capstone.x86.X86_REG_EBX: "ebx",
             capstone.x86.X86_REG_ESP: "esp", capstone.x86.X86_REG_EBP: "ebp",
             capstone.x86.X86_REG_ESI: "esi", capstone.x86.X86_REG_EDI: "edi"}
    kinds = {}
    for h in hits:
        has_index = h["index"] != 0
        k = "index*scale" if has_index else "plain"
        kinds[k] = kinds.get(k, 0) + 1
    print("by form: %s" % kinds)
    print()
    # 与旧普查（只认 modrm 0x50..0x57）对比
    import probe_slot5c as S
    raw, good, bad = S.scan_call_5c(b, rows)
    old = {h["va"] for h in good}
    new = {h["va"] for h in hits}
    print("old census (modrm 0x50..0x57, boundary-verified) = %d" % len(old))
    print("new census (operand-based)                        = %d" % len(new))
    print()
    print("MISSED by old census (in new, not in old):")
    for h in sorted([x for x in hits if x["va"] not in old], key=lambda x: x["va"]):
        e = A.entry_at_or_before(rows, h["va"])
        onb, insn, why = A.boundary_check(b, e[0], h["va"])
        bn = names.get(h["base"], "?") + ("+" + names.get(h["index"], "?") + "*%d" % h["scale"]
                                          if h["index"] else "")
        print("   %08X  %-30s base/index=%-12s on_boundary=%s fn=%08X  bytes=%s"
              % (h["va"], h["text"], bn, onb, e[0], h["bytes"]))
    print()
    print("EXTRA in old census (in old, not in new) -- 说明旧的字节表有假阳性/或 operand 解析差异:")
    for va in sorted(old - new):
        r, g, _ = S.scan_call_5c(b, rows)
        print("   %08X" % va)


if __name__ == "__main__":
    main()
