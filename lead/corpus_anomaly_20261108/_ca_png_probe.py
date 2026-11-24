# -*- coding: utf-8 -*-
"""_ca_png_probe.py — 只读解码 PNG 的平均色/主色分布，判定截图内容形态。
零真机、零采样：仅读语料 PNG 文件（stdlib zlib 解码）。
"""
import zlib, struct, sys, hashlib, collections

def decode_png(path):
    b = open(path, 'rb').read()
    assert b[:8] == b'\x89PNG\r\n\x1a\n'
    pos = 8
    idat = b''
    ihdr = None
    plte = None
    while pos < len(b):
        ln = struct.unpack('>I', b[pos:pos+4])[0]
        typ = b[pos+4:pos+8]
        data = b[pos+8:pos+8+ln]
        if typ == b'IHDR':
            ihdr = struct.unpack('>IIBBBBB', data)
        elif typ == b'IDAT':
            idat += data
        elif typ == b'PLTE':
            plte = data
        pos += 12 + ln
        if typ == b'IEND':
            break
    w, h, depth, ctype, comp, filt, inter = ihdr
    raw = zlib.decompress(idat)
    if ctype != 2 or depth != 8:
        return (w, h, depth, ctype, 'unsupported-ctype-%d-depth-%d' % (ctype, depth))
    stride = w * 3
    out = bytearray()
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        ft = raw[p]; p += 1
        line = bytearray(raw[p:p+stride]); p += stride
        if ft == 1:
            for i in range(3, stride):
                line[i] = (line[i] + line[i-3]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i-3] if i >= 3 else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i-3] if i >= 3 else 0
                c = prev[i-3] if i >= 3 else 0
                bb = prev[i]
                pa = abs(bb - c); pb = abs(a - c); pc = abs(a + bb - 2*c)
                pr = a if (pa <= pb and pa <= pc) else (bb if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out += line
        prev = line
    n = w * h
    sr = sg = sb = 0
    cnt = collections.Counter()
    for i in range(0, len(out), 3):
        r, g, bl = out[i], out[i+1], out[i+2]
        sr += r; sg += g; sb += bl
        cnt[(r >> 4, g >> 4, bl >> 4)] += 1
    top = cnt.most_common(6)
    return (w, h, depth, ctype,
            'avg=(%d,%d,%d)' % (sr//n, sg//n, sb//n),
            'top16bins=%s' % [(c, round(k/n*100,1)) for c, k in top])

if __name__ == '__main__':
    for path in sys.argv[1:]:
        b = open(path, 'rb').read()
        print(path)
        print('  sha256 =', hashlib.sha256(b).hexdigest())
        print('  bytes  =', len(b))
        print('  ', decode_png(path))
