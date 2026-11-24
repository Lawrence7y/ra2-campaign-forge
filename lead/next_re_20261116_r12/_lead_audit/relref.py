"""Lead 抽验：无对齐假设的相对地址引用搜索。

为什么需要这一层：
  - `sweep_calls`（线性反汇编）在 .text 内嵌跳转表/数据处会失步，产生**假阴性**（漏报调用点）。
  - 直接搜绝对 dword 只能覆盖 `mov reg, imm32` / 指针表，覆盖不到 `call rel32`（相对编码）。
本模块按**字节级 rel32 算术**扫 `E8/E9/0F 8x`，与指令对齐无关；命中后再单独验指令边界。

这是与 Ghidra 引用模型、与线性扫描都相互独立的第三条通道。
"""
import struct
import audit_lib as A


def scan_rel_targets(bin_, target_va, kinds=("call", "jmp", "jcc", "short")):
    """扫 rel 形式，与指令对齐无关。

    覆盖：
      E8 rel32      call
      E9 rel32      jmp near
      0F 8x rel32   jcc near (x=0..F)
      EB rel8       jmp short          (只能到达 ±127)
      70..7F rel8   jcc short
      E3 rel8       jecxz
    返回命中列表。"""
    t = bin_.text
    buf = bin_.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    out = []
    n = len(buf)
    for i in range(n - 6):
        op = buf[i]
        site = t["va"] + i
        if op == 0xE8:
            if "call" not in kinds:
                continue
            disp = struct.unpack("<i", buf[i + 1:i + 5])[0]
            if site + 5 + disp == target_va:
                out.append(dict(site=site, kind="call rel32"))
        elif op == 0xE9:
            if "jmp" not in kinds:
                continue
            disp = struct.unpack("<i", buf[i + 1:i + 5])[0]
            if site + 5 + disp == target_va:
                out.append(dict(site=site, kind="jmp rel32"))
        elif op == 0x0F and 0x80 <= buf[i + 1] <= 0x8F:
            if "jcc" not in kinds:
                continue
            disp = struct.unpack("<i", buf[i + 2:i + 6])[0]
            if site + 6 + disp == target_va:
                out.append(dict(site=site, kind="jcc rel32 0F%02X" % buf[i + 1]))
        elif op == 0xEB:
            if "short" not in kinds:
                continue
            disp = struct.unpack("<b", buf[i + 1:i + 2])[0]
            if site + 2 + disp == target_va:
                out.append(dict(site=site, kind="jmp short"))
        elif 0x70 <= op <= 0x7F or op == 0xE3:
            if "short" not in kinds:
                continue
            disp = struct.unpack("<b", buf[i + 1:i + 2])[0]
            if site + 2 + disp == target_va:
                out.append(dict(site=site, kind=("jcc short %02X" % op) if op != 0xE3 else "jecxz"))
    return out


def scan_rel_targets_report(bin_, rows, target_va, kinds=("call", "jmp")):
    hits = scan_rel_targets(bin_, target_va, kinds)
    for h in hits:
        e = A.entry_at_or_before(rows, h["site"])
        ok, insn, why = A.boundary_check(bin_, e[0], h["site"])
        h["from_entry"] = e[0]
        h["boundary"] = ok
        h["why"] = why
        h["insn"] = ("%s %s" % (insn.mnemonic, insn.op_str)) if ok and insn else None
    return hits


def coverage_check(bin_):
    """报告三通道的覆盖率，用于判断"零命中"是否可信。"""
    calls, jmps, st = A.sweep_calls(bin_)
    # 统计有多少 call rel32 的 site 能被线性扫描看到
    t = bin_.text
    buf = bin_.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    total_e8 = sum(1 for i in range(len(buf) - 5) if buf[i] == 0xE8)
    return dict(linear_insns=st["insns"], linear_skipped=st["skipped_bytes"],
                linear_text_bytes=st["text_bytes"],
                linear_unique_call_targets=len(calls),
                raw_E8_bytes=total_e8)


if __name__ == "__main__":
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    print("=== coverage ===")
    print(coverage_check(b))
    print()
    for tgt in (0x55B8F0, 0x55B880, 0x55BAA0, 0x55BAE0):
        hits = scan_rel_targets_report(b, rows, tgt)
        print("--- target %08X : %d rel hits" % (tgt, len(hits)))
        for h in hits:
            print("    %s @ %08X  boundary=%s (%s)  from_entry=%08X  insn=%s"
                  % (h["kind"], h["site"], h["boundary"], h["why"], h["from_entry"], h["insn"]))
