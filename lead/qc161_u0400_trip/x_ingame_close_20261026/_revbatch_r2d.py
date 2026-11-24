# _revbatch_r2d.py — crop center 1000x600 of selected shots to small PNGs for visual inspection
import os, zlib, struct

ROOT = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x"
OUT = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\x_ingame_close_20261026"
MAGIC = b"\x89PNG\r\n\x1a\n"

def rgb_raw(path):
    b = open(path, "rb").read(); assert b[:8] == MAGIC
    pos = 8; idat = b""
    while pos < len(b):
        ln = struct.unpack(">I", b[pos:pos+4])[0]; typ = b[pos+4:pos+8]; data = b[pos+8:pos+8+ln]
        if typ == b"IHDR": w, h = struct.unpack(">II", data[:8])
        elif typ == b"IDAT": idat += data
        elif typ == b"IEND": break
        pos += 12 + ln
    return zlib.decompress(idat), w, h

def chunk(typ, data):
    return struct.pack(">I", len(data)) + typ + data + struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff)

def write_png(path, w, h, rows):
    body = zlib.compress(b"".join(rows), 6)
    with open(path, "wb") as f:
        f.write(MAGIC)
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", body))
        f.write(chunk(b"IEND", b""))

CW, CH = 1000, 600
for tag, d, fn in [("P0post","20261028T084855_0001_P0_ORIG","post_close_end.png"),
                   ("P3post","20261028T091330_0001_P3_G1B1","post_close_end.png"),
                   ("P3mpre","20261028T092052_0001_P3m_MENU","menu_ready.png"),
                   ("P3mpost","20261028T092052_0001_P3m_MENU","post_close_end.png"),
                   ("P3battle","20261028T091330_0001_P3_G1B1","battle_end.png"),
                   ("P2post","20261028T090813_0001_P2_G1B0def","post_close_end.png")]:
    raw, w, h = rgb_raw(os.path.join(ROOT, d, "shots", fn))
    stride = 1 + w * 3
    x0, y0 = (w - CW) // 2, (h - CH) // 2
    rows = []
    for y in range(CH):
        src = (y0 + y) * stride + 1 + x0 * 3
        rows.append(b"\x00" + raw[src:src + CW * 3])
    write_png(os.path.join(OUT, "_revbatch_crop_%s.png" % tag), CW, CH, rows)
    print(tag, "cropped from", w, h)
