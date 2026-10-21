"""把 frame_target_01.png 降采样成 48x36 的亮度字符图，直观看画面结构。

只读，不写文件。
"""
import struct
import zlib
from pathlib import Path

TRIP = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip")
RAMP = " .:-=+*#%@"


def decode_png(path):
    d = path.read_bytes()
    i = 8
    idat = b""
    w = h = None
    while i < len(d):
        ln = struct.unpack(">I", d[i:i + 4])[0]
        typ = d[i + 4:i + 8]
        dat = d[i + 8:i + 8 + ln]
        if typ == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", dat[:10])
        elif typ == b"IDAT":
            idat += dat
        elif typ == b"IEND":
            break
        i += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * 3
    out = bytearray(h * stride)
    prev = bytearray(stride)
    pos = 0
    for y in range(h):
        ft = raw[pos]
        pos += 1
        line = bytearray(raw[pos:pos + stride])
        pos += stride
        if ft == 1:
            for x in range(3, stride):
                line[x] = (line[x] + line[x - 3]) & 0xFF
        elif ft == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 0xFF
        elif ft == 3:
            for x in range(stride):
                a = line[x - 3] if x >= 3 else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 0xFF
        elif ft == 4:
            for x in range(stride):
                a = line[x - 3] if x >= 3 else 0
                b = prev[x]
                c = prev[x - 3] if x >= 3 else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, out


def ascii_map(path, cols=48, rows=30):
    w, h, px = decode_png(path)
    stride = w * 3
    lines = []
    for ry in range(rows):
        y0 = ry * h // rows
        y1 = max(y0 + 1, (ry + 1) * h // rows)
        row = []
        for rx in range(cols):
            x0 = rx * w // cols
            x1 = max(x0 + 1, (rx + 1) * w // cols)
            tot = 0
            cnt = 0
            for y in range(y0, y1, 3):
                base = y * stride
                for x in range(x0, x1, 3):
                    o = base + x * 3
                    tot += (px[o] * 299 + px[o + 1] * 587 + px[o + 2] * 114) // 1000
                    cnt += 1
            l = tot // max(1, cnt)
            row.append(RAMP[min(9, l * 10 // 256)])
        lines.append("".join(row))
    return lines


for d in ("l1a_20261020", "l1c_20261021", "t55k_20261020"):
    p = TRIP / d / "frame_target_01.png"
    print("=" * 60)
    print(d)
    print("=" * 60)
    for ln in ascii_map(p):
        print(ln)
