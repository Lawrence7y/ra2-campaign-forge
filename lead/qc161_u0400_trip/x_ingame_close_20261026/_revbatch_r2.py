# _revbatch_r2.py — reviewer-owned minimal PNG decoder (zlib+struct only, no executor judge code)
import os, zlib, struct, json

ROOT = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x"
ARMS = [
    ("P0",  "20261028T084855_0001_P0_ORIG"),
    ("P0N", "20261028T085311_0001_P0N_INJ_OFF"),
    ("P1",  "20261028T085640_0001_P1_G1B0exp"),
    ("P2",  "20261028T090813_0001_P2_G1B0def"),
    ("P3",  "20261028T091330_0001_P3_G1B1"),
    ("P3m", "20261028T092052_0001_P3m_MENU"),
]
MAGIC = b"\x89PNG\r\n\x1a\n"

def parse(path):
    b = open(path, "rb").read()
    info = {"bytes": len(b)}
    assert b[:8] == MAGIC, "bad magic"
    info["magic"] = True
    pos = 8
    chunks = []
    w = h = bitdepth = ctype = None
    idat_parts = []
    first_chunk_type = None
    while pos < len(b):
        ln = struct.unpack(">I", b[pos:pos+4])[0]
        typ = b[pos+4:pos+8].decode("ascii")
        data = b[pos+8:pos+8+ln]
        crc = struct.unpack(">I", b[pos+8+ln:pos+12+ln])[0]
        calc = zlib.crc32(typ.encode("ascii") + data) & 0xffffffff
        chunks.append((typ, ln, crc == calc))
        if first_chunk_type is None:
            first_chunk_type = typ
        if typ == "IHDR":
            w, h, bitdepth, ctype, comp, filt, inter = struct.unpack(">IIBBBBB", data)
            info.update(IHDR=(w, h, bitdepth, ctype, comp, filt, inter))
        elif typ == "IDAT":
            idat_parts.append(data)
        elif typ == "IEND":
            break
        pos += 12 + ln
    info["first_chunk"] = first_chunk_type
    info["chunk_seq"] = "".join(c[0][0] for c in chunks)  # I I D... E
    info["crc_all_ok"] = all(c[2] for c in chunks)
    info["n_chunks"] = len(chunks)
    raw = zlib.decompress(b"".join(idat_parts))
    info["decomp_len"] = len(raw)
    expect = h * (1 + w * 3)
    info["expect_len"] = expect
    info["len_match"] = (len(raw) == expect)
    filters = set(raw[y * (1 + w * 3)] for y in range(h))
    info["filter_types"] = sorted(filters)
    info["bitdepth8_truecolor_noninter"] = (bitdepth == 8 and ctype == 2 and inter == 0)
    return info, raw, w, h

def frac_nonblack(raw, w, h, step=7):
    stride = 1 + w * 3
    # row 0 pixel 0 (filter byte skipped)
    ref = raw[1:4]
    n = w * h
    hits = tot = 0
    for i in range(0, n, step):
        x = i % w; y = i // w
        o = y * stride + 1 + x * 3
        px = raw[o:o+3]
        tot += 1
        if px != ref:
            hits += 1
    return hits / max(tot, 1), bytes(ref)

def mean_lum(raw, w, h):
    stride = 1 + w * 3
    tot = 0; cnt = 0
    for y in range(0, h, 3):
        base = y * stride + 1
        row = raw[base:base + w*3]
        for x in range(0, w*3, 30):   # every 10th pixel
            r, g, bl = row[x], row[x+1], row[x+2]
            tot += 0.299*r + 0.587*g + 0.114*bl
            cnt += 1
    return tot / max(cnt, 1)

results = {}
for tag, d in ARMS:
    sdir = os.path.join(ROOT, d, "shots")
    for fn in sorted(os.listdir(sdir)):
        if not fn.endswith(".png"):
            continue
        path = os.path.join(sdir, fn)
        info, raw, w, h = parse(path)
        f, ref = frac_nonblack(raw, w, h)
        info["frac_nonblack_ref0"] = round(f, 5)
        info["ref_pixel"] = list(ref)
        results["%s/%s" % (tag, fn)] = info
        print("%-4s %-18s %dx%d len=%d/%d match=%s filt=%s crc=%s frac=%.5f ref=%s" % (
            tag, fn, w, h, info["decomp_len"], info["expect_len"], info["len_match"],
            info["filter_types"], info["crc_all_ok"], f, list(ref)))
        del raw
# targeted quant checks
print("--- targeted: P3 post_close_end mean luminance")
for key in ("P3/post_close_end.png", "P0N/post_close_end.png", "P3m/menu_ready.png"):
    tag, fn = key.split("/")
    path = os.path.join(ROOT, dict(ARMS)[tag], "shots", fn)
    info, raw, w, h = parse(path)
    print(key, "meanlum=%.3f" % mean_lum(raw, w, h))
json.dump(results, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_revbatch_r2_out.json"), "w"), indent=1)
print("WROTE _revbatch_r2_out.json")
