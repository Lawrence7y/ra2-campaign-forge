# -*- coding: utf-8 -*-
"""探查 RTTI 结构：以已知 LayerClass vftable 0x7E6060 与若干类为样本，
dump vft[-1] (COL) / COL+0xC (TD) / TD+8 (name)；并列出 slot+0x78 返回 0..4 的实现
中那些确实是 ObjectClass 派生（其虚表中槽 +0x94 附近/构造链可辨）的候选。
"""
from __future__ import annotations
import os
import sys
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w173_common as C

E = C.EVID
b = C.B()


def u32(va):
    try:
        return b.u32(va)
    except Exception:
        return None


def show_rtti(vft):
    out = []
    col = u32(vft - 4)
    out.append("vft=%08X  vft[-1]=%s" % (vft, ("%08X" % col) if col else "NONE"))
    if col and 0x400000 <= col < 0x900000:
        out.append("  COL[0..5]: %s" % " ".join(
            ("%08X" % u32(col + i * 4)) if u32(col + i * 4) is not None else "??"
            for i in range(6)))
        td = u32(col + 0xC)
        out.append("  COL+0xC(TD)=%s" % (("%08X" % td) if td else "NONE"))
        if td and 0x400000 <= td < 0x900000:
            raw = b.read(td, 40)
            out.append("  TD[0..9] hex: %s" % raw.hex(" "))
            name_raw = b.read(td + 8, 40).split(b"\x00")[0]
            out.append("  TD+8 name raw: %r" % name_raw)
    return "\n".join(out)


def main():
    L = ["=" * 95, "RTTI 结构探查"]
    samples = [0x7E6060, 0x7E192C, 0x7E4F64, 0x7E3EBC]
    for s in samples:
        L.append("-" * 90)
        L.append(show_rtti(s))

    # 扫 vft-4 指向有效 COL 的虚表数量与名字样本
    L.append("")
    L.append("=" * 95)
    L.append("可解析 RTTI 名的虚表样本（前 80 个）")
    # 复用 layer_class 的 find_vftables
    import w173_layer_class as LC
    vfts = LC.find_vftables(b)
    named = 0
    names = []
    for vft in vfts:
        nm = LC.rtti_name(b, vft)
        if nm:
            named += 1
            names.append((vft, nm))
    L.append("总虚表=%d  RTTI可解析名=%d" % (len(vfts), named))
    for vft, nm in names[:80]:
        L.append("  %08X -> %s" % (vft, nm))
    C.write_text(os.path.join(E, "w173_rtti_probe.txt"), L)
    print("rtti probe written: named=%d/%d" % (named, len(vfts)))


if __name__ == "__main__":
    main()
