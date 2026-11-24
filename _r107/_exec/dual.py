#!/usr/bin/env python3
"""R107: dual-decoder listing (capstone + iced_x86) for one address range.

Usage: python3 _r107/_exec/dual.py <start_hex> <nbytes_hex|dec>
Prints address, bytes, mnemonic/op_str from capstone, and the same from iced_x86, and flags any
disagreement so every quoted instruction in the report can be re-checked with a second decoder.

Run: python3 _r107/_exec/dual.py 4c6cb0 0x50
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r104/vendor')
from r107_lib import DATA, va2off
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import iced_x86

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = False
ICED = iced_x86.Decoder(32, b'', ip=0, options=iced_x86.DecoderOptions.NONE)


def iced_decode(va, n):
    code = DATA[va2off(va):va2off(va) + n]
    dec = iced_x86.Decoder(32, code, ip=va)
    fmt = iced_x86.Formatter(iced_x86.FormatterSyntax.INTEL)
    out = []
    while dec.can_decode:
        ins = dec.decode()
        out.append((ins.ip, ins)
                   )
        if len(out) > 100000:
            break
    return out


def listing(va, n):
    rows = []
    cap = {x.address: x for x in MD.disasm(DATA[va2off(va):va2off(va) + n], va)}
    fmt = iced_x86.Formatter(iced_x86.FormatterSyntax.INTEL)
    dec = iced_x86.Decoder(32, DATA[va2off(va):va2off(va) + n], ip=va)
    while dec.can_decode:
        ins = dec.decode()
        if ins.is_invalid:
            break
        b = DATA[va2off(ins.ip):va2off(ins.ip) + ins.len]
        c = cap.get(ins.ip)
        ctext = ('%s %s' % (c.mnemonic, c.op_str)) if c else '<capstone mismatch>'
        itext = fmt.format(ins)
        rows.append((ins.ip, b.hex(), ins.len, ctext, itext,
                     c is not None and c.size == ins.len))
    return rows


if __name__ == '__main__':
    va = int(sys.argv[1], 16)
    n = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x60
    for ip, b, ln, ctext, itext, ok in listing(va, n):
        flag = '' if ok else '  <<LEN-DIFF'
        print('%08x %-22s %-34s | %s%s' % (ip, b, ctext, itext, flag))
