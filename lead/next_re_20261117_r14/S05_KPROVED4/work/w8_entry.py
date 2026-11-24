# -*- coding: utf-8 -*-
"""① 入口形态核验：16B 对齐 + 前驱字节 + 入口首指令。"""
import ax_lib
ROWS=["00704350","006FFBE0","00703860","005F9950","006F3F40","006F6CA0","005F9720","007171A0"]
pe=ax_lib.load()
for r in ROWS:
    e=int(r,16)
    prev=pe.bytes_at(e-16,16)
    first=pe.bytes_at(e,12)
    print('%s align=%s prev16=%s first=%s' % (
        r, 'OK' if e%16==0 else 'BAD',
        ' '.join('%02X'%b for b in (prev or b'')),
        ' '.join('%02X'%b for b in (first or b''))))
