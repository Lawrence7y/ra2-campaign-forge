# -*- coding: utf-8 -*-
"""按 entry 打印函数体反汇编（带字节），并把 [sel_va] 附近高亮。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))


def show_body(entry, n=None):
    e = int(norm(entry), 16)
    info = ATLAS.get(norm(entry))
    size = n or (info["size"] if info else 256)
    body = disasm(e, size)
    print("=== %s  atlas_size=%s insns=%d ===" % (norm(entry), size, len(body)))
    for ins in body:
        b = va_read(ins.address, ins.size).hex(" ")
        print("  %08X  %-22s %-10s %s" % (ins.address, b, ins.mnemonic, ins.op_str))
    return body


def show_fn(va, size=None):
    info = ATLAS.get(hx(va))
    sz = size or (info["size"] if info else 128)
    print("=== callee %08X  size=%s ===" % (va, sz))
    body = disasm(va, sz)
    for ins in body:
        b = va_read(ins.address, ins.size).hex(" ")
        print("  %08X  %-22s %-10s %s" % (ins.address, b, ins.mnemonic, ins.op_str))
    return body


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "body":
        out = []
        for a in sys.argv[2:]:
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                show_body(a)
            out.append("%s\n" % buf.getvalue())
        p = os.path.join(HERE, "body_%s.txt" % norm(sys.argv[2]))
        open(p, "w", encoding="utf-8").write("\n".join(out))
        print("->", p)
    else:
        for a in sys.argv[2:]:
            show_fn(int(norm(a), 16))
