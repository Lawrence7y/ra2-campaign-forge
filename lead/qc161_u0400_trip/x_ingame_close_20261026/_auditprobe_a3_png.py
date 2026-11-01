# -*- coding: utf-8 -*-
"""_auditprobe_a3_png.py — 独立审计件（A3）。

纪律：自写最小 PNG 解码器，只用 zlib + struct + zlib.crc32，
**不调用被审件（_x_channel_probe_20261027.py）的任何函数**（仅在 (1) 末做
交叉口径比对时读取其 png_parse，作为第二口径，不作为结构判据来源）。

(1) 独立解 c2ab_x/_preflight/20261027T125912/desktop.png：
    magic / chunk 顺序 / 逐 chunk CRC / IHDR=(w,h,8,2,0,0,0) /
    IDAT zlib 解压长度 = h*(1+w*3) / 每行 filter=0 / IEND。
(2) harness7 write_png_no_filter(:2680) 写侧对合：按 harness7 自身
    capture_frame 口径（biBitCount=24，stride=pad4(w*3)，DIB 内存序 B,G,R）
    造已知像素图，验「文件色=屏幕色」(D-115) 且我的解码器 / probe.png_parse
    双方互解一致。
(3) 复现 v2:_capture(:257-289) 真实调用序（32bpp GetDIBits ⇒ 逐像素 R,G,B
    写入 4 字节步长缓冲，再以 stride=w*3 传 write_png_no_filter），
    检验其产物是「结构合法但内容错位」还是「结构即坏」。
"""
import importlib.util
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
DESKTOP = ROOT / "lead/qc161_u0400_trip/c2ab_x/_preflight/20261027T125912/desktop.png"
H7_PATH = ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py"
PROBE_PATH = ROOT / "lead/qc161_u0400_trip/_x_channel_probe_20261027.py"

SIG = b"\x89PNG\r\n\x1a\n"


def my_decode(path: Path):
    """独立解码器；返回 dict(w,h,rgb,notes)；任何违规 raise ValueError。"""
    data = Path(path).read_bytes()
    notes = []
    if data[:8] != SIG:
        raise ValueError("magic 不符: %r" % data[:8])
    notes.append("magic OK, file=%d bytes" % len(data))
    pos = 8
    ihdr = None
    idat = bytearray()
    order = []
    iend_ok = False
    while pos + 12 <= len(data):
        (ln,) = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        if pos + 12 + ln > len(data):
            raise ValueError("chunk %s 越界 (len=%d, 剩余=%d)" % (typ, ln, len(data) - pos - 12))
        body = data[pos + 8:pos + 8 + ln]
        (crc,) = struct.unpack(">I", data[pos + 8 + ln:pos + 12 + ln])
        mine = zlib.crc32(typ + body) & 0xFFFFFFFF
        if crc != mine:
            raise ValueError("chunk %s CRC 不符 file=%08x calc=%08x" % (typ, crc, mine))
        order.append("%s(%d)" % (typ.decode("ascii", "replace"), ln))
        if typ == b"IHDR":
            if ln != 13:
                raise ValueError("IHDR 长度 %d≠13" % ln)
            ihdr = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            if ln != 0:
                raise ValueError("IEND 非空 len=%d" % ln)
            iend_ok = True
            if pos + 12 != len(data):
                notes.append("IEND 后拖尾 %d 字节" % (len(data) - pos - 12))
            break
        pos += 12 + ln
    if ihdr is None or not iend_ok:
        raise ValueError("缺 IHDR 或 IEND")
    w, h, depth, ctype, cm, fm, il = ihdr
    if (depth, ctype, cm, fm, il) != (8, 2, 0, 0, 0):
        raise ValueError("IHDR 非 (8,2,0,0,0): %s" % (ihdr,))
    rows = zlib.decompress(bytes(idat))
    if len(rows) != h * (1 + w * 3):
        raise ValueError("IDAT 解压 %d ≠ h*(1+w*3)=%d" % (len(rows), h * (1 + w * 3)))
    stride = 1 + w * 3
    bad = [y for y in range(h) if rows[y * stride] != 0]
    if bad:
        raise ValueError("行 filter 非 0：%s" % bad[:5])
    px = bytearray(w * h * 3)
    for y in range(h):
        px[y * w * 3:(y + 1) * w * 3] = rows[y * stride + 1:(y + 1) * stride]
    notes.append("chunks=%s" % order)
    notes.append("IHDR=(w=%d,h=%d,depth=8,ctype=2,cm=0,fm=0,il=0)" % (w, h))
    notes.append("IDAT zlib 解压=%d = %d*(1+%d*3) ；%d 行 filter 全 0；IEND 存在且 CRC 全过"
                 % (len(rows), h, w, h))
    return {"w": w, "h": h, "rgb": bytes(px), "notes": notes}


def load_module(name, p):
    spec = importlib.util.spec_from_file_location(name, str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    tmp = Path(r"C:\Users\Administrator\AppData\Local\Temp\auditprobe_a3")
    tmp.mkdir(parents=True, exist_ok=True)

    print("== (1) 独立解码真桌面帧: %s" % DESKTOP)
    d = my_decode(DESKTOP)
    for n in d["notes"]:
        print("   " + n)
    w, h, rgb = d["w"], d["h"], d["rgb"]
    n_px = len(rgb) // 3
    ref = rgb[0:3]
    hits = sum(1 for i in range(n_px) if rgb[i * 3:i * 3 + 3] != ref)
    corners = {"TL": rgb[0:3], "TR": rgb[(w - 1) * 3:w * 3],
               "BL": rgb[(h - 1) * w * 3:(h - 1) * w * 3 + 3], "BR": rgb[-3:],
               "C": rgb[(h // 2) * w * 3 + (w // 2) * 3:][:3]}
    print("   pixels=%d  角/中=%s" % (n_px, corners))
    print("   全像素(非采样)异于首像素占比=%.4f (%d/%d)" % (hits / n_px, hits, n_px))

    probe = load_module("__audprobe", PROBE_PATH)
    pw, ph, prgb = probe.png_parse(DESKTOP)
    print("   [交叉] probe.png_parse=%dx%d 与我解码器逐字节一致=%s"
          % (pw, ph, (pw, ph, prgb) == (w, h, rgb)))

    print()
    print("== (2) harness7 write_png_no_filter 写侧对合（h7 自身 capture_frame 口径）")
    H7 = load_module("__audh7", H7_PATH)
    W, H = 41, 7                      # 非 4 对齐宽 ⇒ 考验 pad4 stride
    stride = ((W * 3 + 3) // 4) * 4
    raw = bytearray(stride * H)
    for y in range(H):
        for x in range(W):
            o = y * stride + x * 3
            raw[o] = (x * 7) % 256          # B
            raw[o + 1] = (y * 13) % 256     # G
            raw[o + 2] = (x + y) % 256      # R  （DIB 内存序 B,G,R）
    f2 = tmp / "h7_roundtrip.png"
    H7.write_png_no_filter(f2, W, H, bytes(raw), stride)
    dd = my_decode(f2)
    ok_px = True
    firstbad = None
    for y in range(H):
        for x in range(W):
            exp = bytes(((x + y) % 256, (y * 13) % 256, (x * 7) % 256))   # 文件内应=R,G,B
            got = dd["rgb"][y * W * 3 + x * 3: y * W * 3 + x * 3 + 3]
            if got != exp:
                ok_px, firstbad = False, (x, y, exp, got)
                break
        if not ok_px:
            break
    print("   " + " | ".join(dd["notes"][1:]))
    print("   D-115 屏幕色=文件色 逐像素对合=%s%s"
          % (ok_px, "" if ok_px else " 首例=%s" % (firstbad,)))
    p2 = probe.png_parse(f2)
    print("   [交叉] probe.png_parse(h7产物)=%dx%d 逐字节一致=%s"
          % (p2[0], p2[1], p2[2] == dd["rgb"]))

    print()
    print("== (3) 复现 v2:_capture 真实调用序（32bpp，rgb 缓冲步长 4，stride 传 w*3）")
    W3, H3 = 16, 8
    size = W3 * H3 * 4
    raw32 = bytearray(size)
    for i in range(0, size, 4):
        pxi = i // 4
        raw32[i] = pxi % 256                  # B
        raw32[i + 1] = (pxi // 3) % 256       # G
        raw32[i + 2] = (pxi // 7) % 256       # R
        raw32[i + 3] = 0                      # alpha 未用
    rgbv = bytearray(size)                    # v2:_capture:283-285 逐字节复现
    for i in range(0, size, 4):
        rgbv[i] = raw32[i + 2]; rgbv[i + 1] = raw32[i + 1]; rgbv[i + 2] = raw32[i]
    f3 = tmp / "v2_capture_sim.png"
    H7.write_png_no_filter(f3, W3, H3, bytes(rgbv), W3 * 3)   # v2:_capture:286 逐字复现
    d3 = my_decode(f3)
    print("   结构合法: %s" % " | ".join(d3["notes"][1:]))
    r3 = d3["rgb"]
    badrows = []
    for y in range(H3):
        want = bytearray(W3 * 3)
        for x in range(W3):                       # 若 v2 正确：文件应含真屏幕色 R,G,B
            pxi = y * W3 + x
            want[x * 3] = (pxi // 7) % 256
            want[x * 3 + 1] = (pxi // 3) % 256
            want[x * 3 + 2] = pxi % 256
        if r3[y * W3 * 3:(y + 1) * W3 * 3] != bytes(want):
            badrows.append(y)
    n = len(r3) // 3
    ref3 = r3[0:3]
    hits3 = sum(1 for i in range(n) if r3[i * 3:i * 3 + 3] != ref3)
    print("   逐行与真值比对：错行=%d/%d ；异于首像素占比=%.4f"
          % (len(badrows), H3, hits3 / n))
    print("   行0 文件前 6 字节=%r（真屏幕色前 2 像素应为 %r）"
          % (r3[:6], bytes([(0 // 7) % 256, 0, 0, (1 // 7) % 256, 0, 1])))
    print("   ⇒ 结论提示：若结构合法但错行=%s，则真实发射下 S1/S2 双绿而内容已剪切损坏"
          % (bool(badrows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
