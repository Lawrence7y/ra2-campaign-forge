# -*- coding: utf-8 -*-
"""_auditprobe_a2v_capture.py — 审计件：v2 真实 capture_screen 与探针 capture_desktop 同屏差分。

零游戏（仅 GDI 屏 DC BitBlt，与被审件 --preflight 同性质）。
流程：
  1) 用 v2 的 bind_real_ops() 取 OPS["capture_screen"]（即 v2:_capture 真实现，
     经 H7.write_png_no_filter）截同一桌面 → v2.png
  2) 用被审件 capture_desktop 截同一桌面 → probe.png
  3) 用**本审计件自写解码器**（_auditprobe_a3_png.my_decode）分别解两张；
     比较结构合法度 + 逐像素差 ⇒ 判定「S1/S2 双绿但内容是否一致」。
纪律：不 import 被审件的 png_parse 作判据（仅在末尾做口径对照打印）。
"""
import importlib.util
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
V2_PATH = ROOT / "lead/qc161_u0400_trip/_drive_c2_x_probe_v2.py"
PROBE_PATH = ROOT / "lead/qc161_u0400_trip/_x_channel_probe_20261027.py"
OUT = Path(r"C:\Users\Administrator\AppData\Local\Temp\auditprobe_a3")
OUT.mkdir(parents=True, exist_ok=True)
SIG = b"\x89PNG\r\n\x1a\n"


def my_decode(path: Path):
    data = Path(path).read_bytes()
    if data[:8] != SIG:
        raise ValueError("magic 不符: %r" % data[:8])
    pos, ihdr, idat, order, iend_ok = 8, None, bytearray(), [], False
    while pos + 12 <= len(data):
        (ln,) = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        if pos + 12 + ln > len(data):
            raise ValueError("chunk %s 越界" % typ)
        body = data[pos + 8:pos + 8 + ln]
        (crc,) = struct.unpack(">I", data[pos + 8 + ln:pos + 12 + ln])
        if crc != (zlib.crc32(typ + body) & 0xFFFFFFFF):
            raise ValueError("chunk %s CRC 不符" % typ)
        order.append("%s(%d)" % (typ.decode("ascii", "replace"), ln))
        if typ == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            iend_ok = True
            break
        pos += 12 + ln
    if ihdr is None or not iend_ok:
        raise ValueError("缺 IHDR 或 IEND")
    w, h, depth, ctype, cm, fm, il = ihdr
    if (depth, ctype, cm, fm, il) != (8, 2, 0, 0, 0):
        raise ValueError("IHDR 非 (8,2,0,0,0): %s" % (ihdr,))
    rows = zlib.decompress(bytes(idat))
    exp = h * (1 + w * 3)
    note_len = "IDAT=%d 期望=%d %s" % (len(rows), exp, "OK" if len(rows) == exp else "MISMATCH")
    if len(rows) != exp:
        return {"w": w, "h": h, "rgb": None, "order": order, "note": note_len,
                "err": "idat_len"}
    stride = 1 + w * 3
    badf = [y for y in range(h) if rows[y * stride] != 0]
    if badf:
        return {"w": w, "h": h, "rgb": None, "order": order,
                "note": note_len + " filter非0行=%s" % badf[:5], "err": "filter"}
    px = bytearray(w * h * 3)
    for y in range(h):
        px[y * w * 3:(y + 1) * w * 3] = rows[y * stride + 1:(y + 1) * stride]
    return {"w": w, "h": h, "rgb": bytes(px), "order": order, "note": note_len + " filter全0", "err": None}


def load(name, p):
    spec = importlib.util.spec_from_file_location(name, str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    V = load("__aud_v2", V2_PATH)
    V.bind_real_ops()
    v2png = OUT / "desktop_via_v2_capture.png"
    V.OPS["capture_screen"](v2png)
    print("[1] v2 真 _capture 落盘 %s size=%d" % (v2png, v2png.stat().st_size))

    P = load("__aud_probe2", PROBE_PATH)
    ppng = OUT / "desktop_via_probe_capture.png"
    w, h = P.capture_desktop(ppng)
    print("[2] 探针 capture_desktop 落盘 %s size=%d (%dx%d)" % (ppng, ppng.stat().st_size, w, h))

    dv = my_decode(v2png)
    dp = my_decode(ppng)
    print("[3] 独立解码 v2  : err=%s w=%s h=%s chunks=%s :: %s"
          % (dv["err"], dv["w"], dv["h"], dv["order"], dv["note"]))
    print("[3] 独立解码 probe: err=%s w=%s h=%s chunks=%s :: %s"
          % (dp["err"], dp["w"], dp["h"], dp["order"], dp["note"]))

    # 探针 png_parse 口径（第二口径，非判据来源）
    try:
        P.png_parse(v2png)
        print("[4] 探针 png_parse(v2产物) ⇒ 接受（S1 会绿）")
    except Exception as e:
        print("[4] 探针 png_parse(v2产物) ⇒ 拒绝: %r" % e)

    if dv["rgb"] and dp["rgb"] and (dv["w"], dv["h"]) == (dp["w"], dp["h"]):
        a, b = dv["rgb"], dp["rgb"]
        W, H = dp["w"], dp["h"]
        diff_px = sum(1 for i in range(0, len(a), 3) if a[i:i + 3] != b[i:i + 3])
        tot = len(a) // 3
        print("[5] 同屏双路径逐像素：不同像素=%d/%d (%.4f)" % (diff_px, tot, diff_px / tot))
        # 行级：v2 行 y 是否 = probe 的「按 4 步长缓冲以 3 步长切片」产物
        drift = []
        for y in range(min(H, 8)):
            pv = a[y * W * 3:y * W * 3 + 6]
            pp = b[y * W * 3:y * W * 3 + 6]
            drift.append((y, pv.hex(), pp.hex()))
        for row in drift:
            print("    行%d v2=%s probe=%s" % row)
        # 位移验证：v2 行 y 应≈ probe 行 floor(3Wy/4w?) —— 用相关法找水平位移
        y = H // 2
        prow = b[y * W * 3:(y + 1) * W * 3]
        vrow = a[y * W * 3:(y + 1) * W * 3]
        best = None
        for sh in range(-8, 9):
            score = sum(1 for x in range(50, W - 50)
                        if vrow[(x + sh) * 3:(x + sh) * 3 + 3] == prow[x * 3:x * 3 + 3])
            if best is None or score > best[1]:
                best = (sh, score)
        print("    中部行水平位移最佳匹配 sh=%d 命中=%d/100（0=无错位）" % best)
        rb = sum(1 for x in range(W) if vrow[x * 3:x * 3 + 3] == bytes((prow[x * 3 + 2], prow[x * 3 + 1], prow[x * 3])))
        print("    v2 行按 R/B 互换后与 probe 命中=%d/%d" % (rb, W))
    return 0


if __name__ == "__main__":
    sys.exit(main())
