# -*- coding: utf-8 -*-
"""RC-4 复现率归因：反查 0x00654320 / 0x00724730 的 E8 调用者。

问题：RC-4 只在 WM_CLOSE 后的尾部窗口里、且再命中一次 GUI 记录更新时才崩，
实测命中率约 18%（2/11）。要知道这个 18% 是「结构性上限」还是「可提高」，
必须先弄清 0x724730 到底由谁、以什么方式调用。

本脚本只读磁盘二进制，零注入、零真机。

口径注意（本件两次踩坑的教训）：
  - SectionHeader.VirtualAddress 是 **RVA**，必须加镜像基数才是真实 VA。
    本镜像 .text RVA=0x1000 + Base=0x400000 => VA 0x401000。
    第一版直接拿 0x1000 当 VA，E8 命中 0 处。
  - 裸扫 E8 字节会有假阳性（操作码出现在立即数里）⇒ 必须做指令边界回验。
  - 回验时「解码到命中即停」，不能第一轮就 break（否则永远走不到目标）。
"""
import io
import struct
import sys

import capstone

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

TARGET_GUEST = 0x00724730    # RC-4 崩溃函数
TARGET_CALLER = 0x00654320   # 直接 call 0x724730 的宿主
OUTERMOST = 0x00652CF0       # 调用链最外层（预期无直接 E8 调用者）


def load_text():
    data = io.open(GAMEMD, "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    img_base = struct.unpack_from("<I", data, pe + 0x34)[0]
    sec_off = pe + 24 + opt_size
    sections = []
    for i in range(nsec):
        o = sec_off + i * 40
        name = data[o:o + 8].rstrip(b"\x00").decode("ascii", "replace")
        vsize, va, rsize, roff = struct.unpack_from("<IIII", data, o + 8)
        sections.append({"name": name, "vsize": vsize, "va": va,
                         "rsize": rsize, "roff": roff})
    return data, img_base, sections


def read_va(data, sections, va, n):
    for s in sections:
        start = s["va"]
        end = start + max(s["vsize"], s["rsize"])
        if start <= va < end:
            off = s["roff"] + (va - start)
            return data[off:off + n]
    return None


def read_va_slice(text_bytes, text_va, va, n):
    off = va - text_va
    return text_bytes[off:off + n]


def find_e8_callers(text_bytes, text_va, target):
    """扫 .text 里所有 E8 rel32，算目标 == target 的调用点，并做边界回验。"""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    hits = []
    n = len(text_bytes)
    i = 0
    while True:
        j = text_bytes.find(b"\xe8", i)
        if j < 0 or j + 5 > n:
            break
        rel = struct.unpack_from("<i", text_bytes, j + 1)[0]
        va = text_va + j
        if (va + 5 + rel) & 0xFFFFFFFF == target:
            hits.append(va)
        i = j + 1

    # 回验：从候选前 0..15 字节的每个位置起线性解码，若恰好某条指令
    # 的地址 == va 且是 call，则 va 处在指令边界上。
    verified = []
    for va in hits:
        ok = False
        for back in range(0, 16):
            start = va - back
            if start < text_va:
                continue
            chunk = read_va_slice(text_bytes, text_va, start, back + 8)
            for ins in md.disasm(chunk, start):
                if ins.address == va:
                    ok = (ins.mnemonic == "call")
                    break
            if ok:
                break
        verified.append((va, ok))
    return verified


def main():
    data, img_base, sections = load_text()
    print("镜像基数 = 0x%08X" % img_base)
    for s in sections:
        print("  %-10s RVA=0x%08X vsize=0x%08X rsize=0x%08X roff=0x%08X"
              % (s["name"], s["va"], s["vsize"], s["rsize"], s["roff"]))

    text = next(s for s in sections if s["name"] == ".text")
    text_bytes = data[text["roff"]:text["roff"] + text["rsize"]]
    # ★ VirtualAddress 是 RVA，必须加镜像基数
    text_va = img_base + text["va"]
    print()
    print("=== .text VA=0x%08X (RVA 0x%08X + Base) size=%d ==="
          % (text_va, text["va"], len(text_bytes)))

    for name, target in (("0x00724730 (崩溃函数)", TARGET_GUEST),
                         ("0x00654320 (直接宿主)", TARGET_CALLER),
                         ("0x00652CF0 (最外层)", OUTERMOST)):
        hits = find_e8_callers(text_bytes, text_va, target)
        n_ok = sum(1 for _, ok in hits if ok)
        print()
        print("--- 谁 E8 call %s ---" % name)
        print("    E8 命中 %d 处，指令边界回验通过 %d 处" % (len(hits), n_ok))
        for va, ok in hits:
            mark = "OK " if ok else "?? "
            print("      %s0x%08X" % (mark, va))


if __name__ == "__main__":
    sys.exit(main())
