# -*- coding: utf-8 -*-
"""查 004E6B20 的 atexit 注册字节形态（检测器为何未命中）。"""
import io, os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify as V

img = V.Image(V.EXE)
code = V.Code(img)
target = 0x004E6B20
pat = target.to_bytes(4, 'little')
n = 0
for s in img.sec_named('.text'):
    d = s['data']
    i = d.find(pat)
    while i >= 0:
        va = s['va'] + i
        ctx = bytes(img.buf[va - 6 - V.IMAGE_BASE: va + 10 - V.IMAGE_BASE])
        print('ref at %08X  ctx=%s' % (va, ctx.hex(' ')))
        n += 1
        i = d.find(pat, i + 1)
print('total refs=%d' % n)

# 7C978A 的 call 形态
print()
print('call sites to 7C978A (first 10):')
for cs in code.calls.get(0x7C978A, [])[:10]:
    b = bytes(img.buf[cs - V.IMAGE_BASE: cs - V.IMAGE_BASE + 5])
    prev = bytes(img.buf[cs - 6 - V.IMAGE_BASE: cs - V.IMAGE_BASE])
    print('  %08X bytes=%s prev6=%s' % (cs, b.hex(' '), prev.hex(' ')))
