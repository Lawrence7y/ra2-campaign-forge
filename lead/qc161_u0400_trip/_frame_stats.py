"""对三趟的 frame_target_01.png 做像素统计，判定是否同一类画面。

只读：解 PNG（colortype=2, bitdepth=8），统计亮度分布、唯一色数、
暗像素占比、以及顶部/底部条带特征。不写任何文件。
"""
import struct
import zlib
from pathlib import Path

TRIP = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip")


def decode_png(path):
    d = path.read_bytes()
    assert d[:8] == b"\x89PNG\r\n\x1a\n"
    i = 8
    idat = b""
    w = h = None
    while i < len(d):
        ln = struct.unpack(">I", d[i:i + 4])[0]
        typ = d[i + 4:i + 8]
        dat = d[i + 8:i + 8 + ln]
        if typ == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", dat[:10])
            assert bd == 8 and ct == 2, (bd, ct)
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


def stats(path):
    w, h, px = decode_png(path)
    stride = w * 3
    lum = []
    colors = set()
    dark = 0
    for y in range(0, h, 2):
        base = y * stride
        for x in range(0, w, 2):
            o = base + x * 3
            r, g, b = px[o], px[o + 1], px[o + 2]
            colors.add((r >> 3, g >> 3, b >> 3))
            l = (r * 299 + g * 587 + b * 114) // 1000
            lum.append(l)
            if l < 16:
                dark += 1
    n = len(lum)
    lum.sort()
    return {
        "wh": (w, h),
        "n": n,
        "lum_mean": round(sum(lum) / n, 2),
        "lum_p10": lum[int(n * 0.10)],
        "lum_p50": lum[n // 2],
        "lum_p90": lum[int(n * 0.90)],
        "dark_frac": round(dark / n, 4),
        "uniq_colors_5bit": len(colors),
    }


for d in ("l1a_20261020", "l1c_20261021", "t55k_20261020"):
    for fn in ("frame_target_01.png", "frame_early_01.png"):
        p = TRIP / d / fn
        if not p.is_file():
            print(d, fn, "MISSING")
            continue
        s = stats(p)
        print(f"{d:18s} {fn:20s} lum_mean={s['lum_mean']:7.2f} "
              f"p10={s['lum_p10']:3d} p50={s['lum_p50']:3d} p90={s['lum_p90']:3d} "
              f"dark={s['dark_frac']:.3f} colors={s['uniq_colors_5bit']}")
