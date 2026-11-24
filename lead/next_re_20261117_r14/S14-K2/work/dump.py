#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dump.py — 反汇编指定区间到 stdout / 文件, 带原始字节, 便于逐字符核对。"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import wbase as W

def dump(va, nbytes, path=None):
    lines = []
    for addr, mnem, ops, insn in W.disasm(va, nbytes, stop_ret=False):
        b = W.bytes_at(addr, insn.size).hex()
        lines.append("0x%08X  %-20s %-8s %s" % (addr, b, mnem, ops))
    txt = "\n".join(lines) + "\n"
    if path:
        open(path, "w", encoding="utf-8").write(txt)
        print("wrote", path, len(lines), "insns")
    else:
        print(txt)

if __name__ == "__main__":
    va = int(sys.argv[1], 16)
    n = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x100
    path = sys.argv[3] if len(sys.argv) > 3 else None
    dump(va, n, path)
