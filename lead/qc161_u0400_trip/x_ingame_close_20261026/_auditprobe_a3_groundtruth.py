# -*- coding: utf-8 -*-
"""_auditprobe_a3_groundtruth.py — A3 第三锚：屏幕真值像素 vs 两份 PNG。

同一 DPI-aware 进程内：先加载 harness7（模块级 SetProcessDPIAware ⇒ 物理像素坐标），
再 user32.GetPixel(屏DC) 采若干真值点，与 (a) 探针 capture_desktop 产物、
(b) v2 OPS capture_screen 产物 同坐标比对。
附加：v2 文件在该点是否 = 真值的 R/B 互换 ⇒ 证「二次 B/R 交换」。
"""
import ctypes
import ctypes.wintypes as wt
import importlib.util
import struct
import zlib
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
V2 = ROOT / "lead/qc161_u0400_trip/_drive_c2_x_probe_v2.py"
PROBE = ROOT / "lead/qc161_u0400_trip/_x_channel_probe_20261027.py"
OUT = Path(r"C:\Users\Administrator\AppData\Local\Temp\auditprobe_a3")
SIG = b"\x89PNG\r\n\x1a\n"
gdi = ctypes.WinDLL("gdi32")
u32 = ctypes.WinDLL("user32")


def load(name, p):
    spec = importlib.util.spec_from_file_location(name, str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def decode_rgb(path):
    data = Path(path).read_bytes()
    pos, ihdr, idat = 8, None, bytearray()
    while pos + 12 <= len(data):
        (ln,) = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    w, h = ihdr[0], ihdr[1]
    rows = zlib.decompress(bytes(idat))
    stride = 1 + w * 3
    px = bytearray(w * h * 3)
    for y in range(h):
        px[y * w * 3:(y + 1) * w * 3] = rows[y * stride + 1:(y + 1) * stride]
    return w, h, bytes(px)


def main():
    V = load("_gt_v2", V2)
    V.bind_real_ops()            # ⇒ 加载 harness7 ⇒ SetProcessDPIAware
    P = load("_gt_probe", PROBE)
    p2 = OUT / "gt_probe.png"
    w, h = P.capture_desktop(p2)
    v2p = OUT / "gt_v2.png"
    V.OPS["capture_screen"](v2p)
    print("metrics: probe=%dx%d  v2 IHDR=%dx%d" % ((w, h) + decode_rgb(v2p)[:2]))

    wp, hp, rp = decode_rgb(p2)
    wv, hv, rv = decode_rgb(v2p)
    hdc = u32.GetDC(None)
    gdi.GetPixel.restype = wt.DWORD
    pts = []
    for (x, y) in [(100, 100), (640, 360), (1280, 200), (2000, 700), (300, 1200), (5000, 400), (4000, 1300)]:
        if x < wp and y < hp:
            pts.append((x, y))
    agree_p = agree_v = swap_v = 0
    for (x, y) in pts:
        c = gdi.GetPixel(hdc, x, y)
        if c == 0xFFFFFFFF:
            print("   (%4d,%4d) GetPixel=CLR_INVALID（点落虚拟框非监视器区）" % (x, y))
            continue
        # COLORREF = 0x00BBGGRR ⇒ 屏幕真值 (R,G,B)：
        truth = (c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF)
        gp = rp[(y * wp + x) * 3:y * wp * 3 + 3] if False else rp[(y * wp + x) * 3:(y * wp + x) * 3 + 3]
        gv = rv[(y * wv + x) * 3:(y * wv + x) * 3 + 3]
        okp = tuple(gp) == truth
        okv = tuple(gv) == truth
        swp = tuple(gv) == (truth[2], truth[1], truth[0])
        agree_p += okp; agree_v += okv; swap_v += swp
        print("   (%4d,%4d) 屏幕=%s probe=%s%s v2=%s%s%s"
              % (x, y, truth, tuple(gp), "✓" if okp else "✗",
                 tuple(gv), "✓" if okv else "✗", "(=R/B互换)" if swp else ""))
    u32.ReleaseDC(None, hdc)
    n = len(pts)
    print("结论：探针与屏幕真值一致 %d/%d ；v2 产物一致 %d/%d ；v2=R/B互换 %d/%d"
          % (agree_p, n, agree_v, n, swap_v, n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
