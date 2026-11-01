# -*- coding: utf-8 -*-
"""_auditprobe_a3_swaptest.py — 终判 v2:_capture 缺陷形态：纯 R/B 交换？还是含几何剪切？

同一进程内先后调用 v2 OPS["capture_screen"] 与探针 capture_desktop（间隔 <1s），
假说 H1：v2 文件像素 == 探针文件像素逐点 R/B 互换（几何正确，色序反）。
统计全像素命中率；若 ≥99%（扣除任务栏时钟等时变区）⇒ H1 成立（无剪切）。
"""
import importlib.util
import struct
import zlib
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
OUT = Path(r"C:\Users\Administrator\AppData\Local\Temp\auditprobe_a3")
SIG = b"\x89PNG\r\n\x1a\n"


def load(name, p):
    spec = importlib.util.spec_from_file_location(name, str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def decode(path):
    data = Path(path).read_bytes()
    assert data[:8] == SIG
    pos, ihdr, idat = 8, None, bytearray()
    while pos + 12 <= len(data):
        (ln,) = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        (crc,) = struct.unpack(">I", data[pos + 8 + ln:pos + 12 + ln])
        assert crc == (zlib.crc32(typ + body) & 0xFFFFFFFF), "CRC %s" % typ
        if typ == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    w, h = ihdr[0], ihdr[1]
    rows = zlib.decompress(bytes(idat))
    assert len(rows) == h * (1 + w * 3), "IDAT len"
    stride = 1 + w * 3
    for y in range(h):
        assert rows[y * stride] == 0, "filter row %d" % y
    px = bytearray(w * h * 3)
    for y in range(h):
        px[y * w * 3:(y + 1) * w * 3] = rows[y * stride + 1:(y + 1) * stride]
    return w, h, bytes(px)


def main():
    V = load("_sv", ROOT / "lead/qc161_u0400_trip/_drive_c2_x_probe_v2.py")
    V.bind_real_ops()
    P = load("_sp", ROOT / "lead/qc161_u0400_trip/_x_channel_probe_20261027.py")
    v2p, pp = OUT / "swap_v2.png", OUT / "swap_probe.png"
    V.OPS["capture_screen"](v2p)
    P.capture_desktop(pp)
    wv, hv, rv = decode(v2p)
    wp, hp, rp = decode(pp)
    print("v2=%dx%d probe=%dx%d" % (wv, hv, wp, hp))
    assert (wv, hv) == (wp, hp)
    n = wv * hv
    exact = swap = 0
    for i in range(0, len(rv), 3):
        a = rv[i:i + 3]; b = rp[i:i + 3]
        if a == b:
            exact += 1
        elif a == bytes((b[2], b[1], b[0])):
            swap += 1
    print("逐点：完全相同=%.4f  R/B互换=%.4f  其余=%.4f  （合计 %d px）"
          % (exact / n, swap / n, 1 - (exact + swap) / n, n))
    # 若 H1 成立：exact+swap ≈ 1，exact 主要来自灰/白区
    rows_bad = {}
    for y in range(hv):
        bad = 0
        base = y * wv * 3
        for x in range(0, wv, 9):
            i = base + x * 3
            a, b = rv[i:i + 3], rp[i:i + 3]
            if a != b and a != bytes((b[2], b[1], b[0])):
                bad += 1
        rows_bad[y] = bad
    worst = sorted(rows_bad.items(), key=lambda kv: -kv[1])[:6]
    print("采样错位最严重的 6 行（行号,采错数/600）:", worst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
