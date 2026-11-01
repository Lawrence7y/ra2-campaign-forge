# -*- coding: utf-8 -*-
"""_auditprobe_a3_pillow.py — 第三口径解码：Pillow 12.2（与 probe/harness7/审计解码器均无关）。

验：
 (1) 真桌面帧 desktop.png 能否被 Pillow（规范解码器）完整解出 + 尺寸；
 (2) v2 真实 capture 产物（同屏差分文件）——重点：Pillow 严格模式下是否报错
     还是「静默接受坏几何」；
 (3) v2_capture_sim.png；
 (4) probe 自身 capture 产物。
 (5) 像素级：Pillow(desktop) vs 我的 my_decode(desktop) vs probe.png_parse 三方一致性。
"""
import struct
import sys
import zlib
from pathlib import Path

from PIL import Image

OUT = Path(r"C:\Users\Administrator\AppData\Local\Temp\auditprobe_a3")
DESKTOP = Path(r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x\_preflight\20261027T125912\desktop.png")
PROBE = Path(r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\_x_channel_probe_20261027.py")
SIG = b"\x89PNG\r\n\x1a\n"


def my_decode(path):
    data = Path(path).read_bytes()
    assert data[:8] == SIG
    pos, ihdr, idat, iend = 8, None, bytearray(), False
    while pos + 12 <= len(data):
        (ln,) = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        (crc,) = struct.unpack(">I", data[pos + 8 + ln:pos + 12 + ln])
        assert crc == (zlib.crc32(typ + body) & 0xFFFFFFFF), typ
        if typ == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            iend = True
            break
        pos += 12 + ln
    w, h = ihdr[0], ihdr[1]
    rows = zlib.decompress(bytes(idat))
    exp = h * (1 + w * 3)
    if len(rows) != exp:
        return w, h, ("LEN %d≠%d" % (len(rows), exp)), None
    stride = 1 + w * 3
    px = bytearray(w * h * 3)
    for y in range(h):
        if rows[y * stride] != 0:
            return w, h, "FILTER row %d" % y, None
        px[y * w * 3:(y + 1) * w * 3] = rows[y * stride + 1:(y + 1) * stride]
    return w, h, "OK", bytes(px)


def pil_check(p, label):
    try:
        im = Image.open(p)
        im.load()          # 强制完整解码
        mode, size = im.mode, im.size
        rgb = im.convert("RGB")
        corners = [rgb.getpixel(xy) for xy in
                   [(0, 0), (size[0] - 1, 0), (0, size[1] - 1), (size[0] - 1, size[1] - 1)]]
        print("[%s] Pillow 完整解码 OK size=%s mode=%s 角=%s" % (label, size, mode, corners[:4]))
        return size, rgb.tobytes()
    except Exception as e:
        print("[%s] Pillow 拒绝: %r" % (label, e))
        return None, None


def main():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_p", str(PROBE))
    P = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(P)

    for p, label in ((DESKTOP, "desktop(探针生成)"),
                     (OUT / "desktop_via_v2_capture.png", "v2真实capture产物"),
                     (OUT / "desktop_via_probe_capture.png", "probe真实capture产物"),
                     (OUT / "v2_capture_sim.png", "v2路径仿真"),
                     (OUT / "h7_roundtrip.png", "h7往返")):
        if not Path(p).exists():
            print("[%s] 不存在 %s" % (label, p))
            continue
        pil_check(p, label)

    print()
    print("== 三方像素一致（desktop 文件）==")
    wmy, hmy, stmy, rgbmy = my_decode(DESKTOP)
    sizep, pilrgb = pil_check(DESKTOP, "desktop-for-pixels")
    wp, hp, rgbpb = P.png_parse(DESKTOP)
    print("   my_decode: %dx%d %s len=%s" % (wmy, hmy, stmy, len(rgbmy) if rgbmy else None))
    print("   probe.png_parse: %dx%d len=%s" % (wp, hp, len(rgbpb)))
    if pilrgb and rgbmy:
        same_mp = pilrgb == rgbmy
        print("   Pillow vs my_decode 逐字节一致=%s" % same_mp)
        print("   Pillow vs probe.png_parse 逐字节一致=%s" % (pilrgb == rgbpb))
        if not same_mp:
            diff = sum(1 for i in range(0, min(len(pilrgb), len(rgbmy)), 3)
                       if pilrgb[i:i + 3] != rgbmy[i:i + 3])
            print("   不同像素=%d" % diff)

    print()
    print("== v2 真实 capture 产物：Pillow 严格性 vs 探针 png_parse ==")
    v2p = OUT / "desktop_via_v2_capture.png"
    size2, pil2 = pil_check(v2p, "v2-capture-Pillow")
    try:
        w2, h2, rgb2 = P.png_parse(v2p)
        print("   探针 png_parse ⇒ 接受 %dx%d（S1 视角=合法）" % (w2, h2))
        if pil2 and rgb2:
            d = sum(1 for i in range(0, len(rgb2), 3) if pil2[i:i + 3] != rgb2[i:i + 3])
            print("   Pillow 解出的像素 vs 探针解出的像素：不同=%d/%d（若相同⇒两者按同一（坏）几何切，内容皆剪切）" %
                  (d, len(rgb2) // 3))
    except Exception as e:
        print("   探针 png_parse ⇒ 拒绝: %r" % e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
