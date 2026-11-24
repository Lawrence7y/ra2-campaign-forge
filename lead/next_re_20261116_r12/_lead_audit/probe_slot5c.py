"""Lead 抽验：全镜像 `call dword ptr [reg+0x5C]` 站点普查（带指令边界校验）。

R12_FACTS §3-2 的教训：`FF 5x 5C` 原始字节命中含假阳性（有的其实是别的指令的子串）。
所以本脚本对每个字节命中都做：
  1) 从该地址所属函数的入口线性反汇编，判定命中地址是否恰好是指令边界；
  2) 只在边界成立时，才把"该地址的指令"当作证据。
输出 site / 指令 / 所属函数 entry / 该函数是否在 atlas 里。
"""
import re
import audit_lib as A

NUM = re.compile(r"0x[0-9a-fA-F]+")

# call r/m32, modrm=mod 10 (disp32? no) —— 这里 disp8=0x5c
# FF /2 = call r/m32. modrm: mod=01 (disp8), reg=010, rm=r  => 01 010 rrr = 0x50|r
MODRM = {0x50: "eax", 0x51: "ecx", 0x52: "edx", 0x53: "ebx",
         0x55: "ebp", 0x56: "esi", 0x57: "edi"}


def scan_call_5c(b, entries):
    t = b.text
    buf = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    raw = []
    i = 0
    while True:
        i = buf.find(b"\xff", i)
        if i < 0:
            break
        if i + 3 <= len(buf) and buf[i + 1] in MODRM and buf[i + 2] == 0x5C:
            raw.append(dict(va=t["va"] + i, reg=MODRM[buf[i + 1]],
                            bytes="ff%02x5c" % buf[i + 1]))
        i += 1

    good, bad = [], []
    for h in raw:
        e = A.entry_at_or_before(entries, h["va"])
        ok, insn, why = A.boundary_check(b, e[0], h["va"])
        h["from_entry"] = e[0]
        h["why"] = why
        if ok and insn.mnemonic == "call" and "+ 0x5c]" in "%s %s" % (insn.mnemonic, insn.op_str):
            h["insn"] = "%s %s" % (insn.mnemonic, insn.op_str)
            h["boundary"] = True
            good.append(h)
        else:
            h["boundary"] = False
            h["cover"] = ("%s %s" % (insn.mnemonic, insn.op_str)) if insn else None
            bad.append(h)
    return raw, good, bad


if __name__ == "__main__":
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    entries = [v for v, _ in rows]
    atlas = set(entries)

    raw, good, bad = scan_call_5c(b, rows)
    print("=" * 88)
    print("raw byte hits for FF 5x 5C : %d" % len(raw))
    print("boundary-verified  call [reg+0x5C] : %d" % len(good))
    print("rejected (not a real instruction boundary) : %d" % len(bad))
    print("=" * 88)
    print()
    print("REJECTED samples (first 12) -- 这些就是 R12_FACTS §3-2 说的假阳性")
    for h in bad[:12]:
        print("   %08X  %s  covered_by=%s" % (h["va"], h["bytes"], h["cover"]))
    print()
    print("VERIFIED call [reg+0x5C] sites, grouped by containing function:")
    by_fn = {}
    for h in good:
        by_fn.setdefault(h["from_entry"], []).append(h)
    for fn in sorted(by_fn):
        sites = sorted(x["va"] for x in by_fn[fn])
        print("  fn %08X  %d site(s): %s   inAtlas=%s"
              % (fn, len(sites), [hex(x) for x in sites], fn in atlas))
    print()
    print("total verified sites = %d in %d functions" % (len(good), len(by_fn)))
