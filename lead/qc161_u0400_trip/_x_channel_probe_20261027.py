# -*- coding: utf-8 -*-
"""_x_channel_probe_20261027.py — X 观测通道探针（加性件；永不启动游戏）。

存在性理由：v2 故障注入把 capture_screen/timeline/_rec 存成 stub（b"PNG"、合成行），
故「截图非全黑、时间线可解析、投递记录完备」这三类主张从未在**真实工件形态**上证过
（judge-real-artifact-form-preview 三层判据的第一层）。本件：
  --selftest   离线：对合成工件跑判定系列 C1–C10/S1/S2 + 负控 N1–N6（变异必红）。
  --preflight  真 OS 无游戏：哈希钉实核 / 真 carrier_identity_ok / 真 GDI 桌面截屏
               走同一判定器 / ini 三模式写读回 / 残留进程检查。全绿 rc=0。
  --live       rc=3 永久拒（游戏发射归 v2 --live 硬闸，本件无任何 popen 游戏路径）。
零改动 v2/设计件/历史台账；异族复核前只作本线候选。判定纯函数，selftest/preflight 共用。
"""
import ctypes
import ctypes.wintypes as wt
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from ctypes import wintypes as _w
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
V2_PATH = ROOT / "lead/qc161_u0400_trip/_drive_c2_x_probe_v2.py"
MYCARD = ROOT / "lead/qc161_u0400_trip/c2ab_x"
GAME_SRC = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L1_sf8_20261020"
GUARD_DIR = ROOT / "lead/goal2_rc4_fixv5_20261022/src"
C2_DIR = ROOT / "lead/qc161_u0400_trip/d09a_c2_candidate"
H7_PATH = ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py"
PROBE_PATH = ROOT / "lead/goal2_rc4_fixv5_20261022/_rc4_ab_probe.py"

GAMEMD_SHA16 = "73201cc021497c95"   # 与 v2:58–62 同值（v2 哈希钉 b66466… 冻结，字面复制安全）
LOADER_SHA16 = "ebddf6a61273c874"
H7_SHA16 = "d019e8beecfb5fd8"
PROBE_SHA16 = "b063052cd02df28c"
C2_DLL_SHA256 = "edb9a0cde129c105e087db61f6661b4722a80787e5b5949bd0b0890e0354f2de"
NONBLACK_MIN = 0.001               # 与全黑参考不同像素占比下限

gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)


# ---------------------------------------------------------------- PNG 写/读（规范格式，per harness7 D-114/115 语义）
def _chunk(typ: bytes, data: bytes) -> bytes:
    return (struct.pack(">I", len(data)) + typ + data
            + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))


def png_write(path: Path, w: int, h: int, rgb: bytes) -> None:
    rows = bytearray()
    for y in range(h):
        rows.append(0)                              # filter type 0（D-114）
        seg = rgb[y * w * 3:(y + 1) * w * 3]
        rows += seg
    blob = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(bytes(rows), 6)) + _chunk(b"IEND", b""))
    Path(path).write_bytes(blob)


def png_parse(path: Path):
    """返回 (w, h, rgb_bytes)；任何布局/长度/CRC/filter 违规⇒raise（不返回 None）。"""
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("bad_signature")
    pos = 8
    idat = bytearray()
    ihdr = None
    seen_end = False
    while pos + 8 <= len(data):
        (ln,) = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if len(body) != ln:
            raise ValueError("truncated_chunk:%s" % typ)
        (crc,) = struct.unpack(">I", data[pos + 8 + ln:pos + 12 + ln])
        if crc != (zlib.crc32(typ + body) & 0xFFFFFFFF):
            raise ValueError("bad_crc:%s" % typ)
        if typ == b"IHDR":
            w, h, depth, ctype, cm, fm, il = struct.unpack(">IIBBBBB", body)
            if (depth, ctype, cm, fm, il) != (8, 2, 0, 0, 0):
                raise ValueError("unexpected_ihdr:%s" % ((depth, ctype, cm, fm, il),))
            ihdr = (w, h)
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            seen_end = True
            break
        pos += 12 + ln
    if ihdr is None or not seen_end:
        raise ValueError("missing_ihdr_or_iend")
    w, h = ihdr
    try:
        rows = zlib.decompress(bytes(idat))
    except zlib.error as e:
        raise ValueError("idat_decompress:%r" % e)
    if len(rows) != h * (1 + w * 3):
        raise ValueError("idat_len:%d≠%d" % (len(rows), h * (1 + w * 3)))
    out = bytearray(w * h * 3)
    stride = 1 + w * 3
    for y in range(h):
        if rows[y * stride] != 0:
            raise ValueError("nonzero_filter_at_row:%d" % y)
        out[y * w * 3:(y + 1) * w * 3] = rows[y * stride + 1:(y + 1) * stride]
    return w, h, bytes(out)


def nonblack_frac(rgb: bytes, step: int = 7) -> float:
    """与首像素不同占比（step 采样，>70K px 图亦 <0.1 s）。"""
    ref = bytes(rgb[0:3])
    n = len(rgb) // 3
    hits = tot = 0
    for i in range(0, n, step):
        tot += 1
        if rgb[i * 3:i * 3 + 3] != ref:
            hits += 1
    return hits / max(tot, 1)


# ---------------------------------------------------------------- 真 GDI 桌面截屏（与 v2:_capture 同语义，独立实现）
class BIH(ctypes.Structure):
    _fields_ = [("biSize", ctypes.c_uint), ("biWidth", ctypes.c_int), ("biHeight", ctypes.c_int),
                ("biPlanes", ctypes.c_ushort), ("biBitCount", ctypes.c_ushort), ("biCompression", ctypes.c_uint),
                ("biSizeImage", ctypes.c_uint), ("biXPelsPerMeter", ctypes.c_int),
                ("biYPelsPerMeter", ctypes.c_int), ("biClrUsed", ctypes.c_uint),
                ("biClrImportant", ctypes.c_uint)]


def _bind_gdi():
    u32.GetSystemMetrics.restype = ctypes.c_int
    u32.GetSystemMetrics.argtypes = [ctypes.c_int]
    u32.GetDC.restype = wt.HDC
    u32.GetDC.argtypes = [wt.HWND]
    u32.ReleaseDC.argtypes = [wt.HDC, wt.HDC]
    u32.ReleaseDC.restype = ctypes.c_int
    gdi32.CreateCompatibleDC.restype = wt.HDC
    gdi32.CreateCompatibleDC.argtypes = [wt.HDC]
    gdi32.CreateCompatibleBitmap.restype = wt.HBITMAP
    gdi32.CreateCompatibleBitmap.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int]
    gdi32.SelectObject.restype = wt.HGDIOBJ
    gdi32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
    gdi32.BitBlt.restype = wt.BOOL
    gdi32.BitBlt.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                             wt.HDC, ctypes.c_int, ctypes.c_int, wt.DWORD]
    gdi32.GetDIBits.restype = ctypes.c_int
    gdi32.GetDIBits.argtypes = [wt.HDC, wt.HBITMAP, ctypes.c_uint, ctypes.c_uint,
                                ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]


def capture_desktop(path: Path) -> tuple:
    _bind_gdi()
    w, hh = u32.GetSystemMetrics(78), u32.GetSystemMetrics(79)      # 虚拟屏幕
    hdc = u32.GetDC(None)
    if not hdc:
        raise RuntimeError("GetDC(None) failed err=%d" % ctypes.get_last_error())
    try:
        memdc = gdi32.CreateCompatibleDC(hdc)
        bmp = gdi32.CreateCompatibleBitmap(hdc, w, hh)
        gdi32.SelectObject(memdc, bmp)
        ctypes.set_last_error(0)
        if not gdi32.BitBlt(memdc, 0, 0, w, hh, hdc, 0, 0, 0x00CC0020):
            raise RuntimeError("BitBlt err=%d" % ctypes.get_last_error())
        bih = BIH(40, w, -hh, 1, 32, 0, 0, 0, 0, 0, 0)
        buf = ctypes.create_string_buffer(w * hh * 4)
        if gdi32.GetDIBits(memdc, bmp, 0, hh, buf, ctypes.byref(bih), 0) == 0:
            raise RuntimeError("GetDIBits failed")
        raw = buf.raw
        rgb = bytearray(w * hh * 3)
        for i in range(0, w * hh * 4, 4):
            j = i // 4 * 3
            rgb[j] = raw[i + 2]; rgb[j + 1] = raw[i + 1]; rgb[j + 2] = raw[i]
        png_write(path, w, hh, bytes(rgb))
    finally:
        u32.ReleaseDC(None, hdc)
    return w, hh


# ---------------------------------------------------------------- 判定器（纯函数，selftest/preflight 共用）
def judge_artifacts(out_dir: Path, rec: dict) -> list:
    """返回 [(id, name, pass, ev)]；工件面主张全部落在这里。"""
    res = []

    def chk(cid, name, cond, ev=""):
        res.append((cid, name, bool(cond), str(ev)[:120]))

    need = ("verdict", "close_delivery", "gamemd_pid", "closed_at_s", "close_rows_n",
            "battle_tl_n", "except_before", "exit_kind")
    missing = [k for k in need if k not in rec]
    chk("C1", "_rec 必备键齐", not missing, "miss=%s" % missing)

    cd = rec.get("close_delivery") or {}
    chk("C2", "verdict∈{OK,PARTIAL}", rec.get("verdict") in ("OK", "PARTIAL"), rec.get("verdict"))
    chk("C3", "投递 post_ok=True∧err=0", cd.get("post_ok") is True and cd.get("post_err") == 0,
        "%s/%s" % (cd.get("post_ok"), cd.get("post_err")))
    chk("C4", "win_pid==gamemd_pid", cd.get("win_pid") == rec.get("gamemd_pid"),
        "%s/%s" % (cd.get("win_pid"), rec.get("gamemd_pid")))

    rows = None
    tl = None
    try:
        tl = json.loads((out_dir / "timeline.json").read_text(encoding="utf-8"))
        rows = tl.get("close_rows")
    except Exception as e:
        chk("C5", "timeline 解析", False, repr(e)[:60])
    if tl is not None:
        ok5 = (isinstance(rows, list) and len(rows) == rec.get("close_rows_n")
               and (rec.get("exit_kind", "").startswith("natural")
                    or len(rows) >= 6))
        chk("C5", "close_rows 全量落盘(非尾6)", ok5,
            "n=%s rec=%s kind=%s" % (None if rows is None else len(rows),
                                     rec.get("close_rows_n"), rec.get("exit_kind", "")[:20]))
        # C8 时间轴互校（BS-2 修法）：单调 + 衔接 + 窗跨度——同步截断(计数同改)必破其一
        bt0 = tl.get("battle_tl") or []
        pre0 = tl.get("pre5") or []
        ts_r = [r["t"] for r in (rows or []) if isinstance(r, dict) and "t" in r]
        ts_b = [b["t"] for b in bt0 if isinstance(b, dict) and "t" in b]
        ts_p = [p["t"] for p in pre0 if isinstance(p, dict) and "t" in p]
        mono = (ts_r == sorted(ts_r)) and (ts_b == sorted(ts_b)) and (ts_p == sorted(ts_p))
        order = ((not ts_b or not ts_p or max(ts_b) <= max(ts_p))
                 and (not ts_p or not ts_r or max(ts_p) <= min(ts_r))
                 and (not ts_p or not ts_r or abs((min(ts_r) - min(ts_p)) - 5.0) < 3.0))
        span_ok = True
        ws = rec.get("watch_s")
        if (ws and ts_r and not rec.get("exit_kind", "").startswith("natural")
                and rec.get("exit_kind", "")):
            span_ok = (ts_r[-1] - ts_r[0]) >= ws - 4.0
        chk("C8", "时间轴单调+衔接+窗跨度", mono and order and span_ok,
            "mono=%s order=%s span=%s (n_r=%d ws=%s)" % (mono, order, span_ok, len(ts_r), ws))
        bt = tl.get("battle_tl")
        pre5 = tl.get("pre5")
        ok6 = (isinstance(bt, list) and len(bt) == rec.get("battle_tl_n")
               and isinstance(pre5, list) and len(pre5) == 5)
        chk("C6", "battle_tl 数吻合∧pre5=5", ok6,
            "bt=%s rec=%s pre5=%s" % (None if not isinstance(bt, list) else len(bt),
                                      rec.get("battle_tl_n"),
                                      None if not isinstance(pre5, list) else len(pre5)))
        if rows:
            r0 = rows[0]
            ok7 = all(k in r0 for k in ("t", "wait", "code", "exitstate", "frame",
                                        "hwnd", "singleton", "tick"))
            chk("C7", "行含五哨兵轴+wait/code", ok7, sorted(r0.keys())[:8])

    shots = rec.get("shots") or []
    want_tags = {"pre_close", "post_close_end"}
    got_tags = {s.get("tag") for s in shots}
    chk("C9", "截图段 pre_close+post_close_end 在录", want_tags <= got_tags, got_tags)

    if rec.get("exit_kind", "").startswith("natural"):
        chk("C10", "自然退⇒final_exitcode 为 int", isinstance(rec.get("final_exitcode"), int),
            rec.get("final_exitcode"))
    else:
        res.append(("C10", "自然退码适用", True, "n/a(非自然退)"))

    s1 = s2 = True
    evs = []
    for s in shots:
        p = Path(s["path"])
        try:
            w, h, rgb = png_parse(p)
            f = nonblack_frac(rgb)
            if f < NONBLACK_MIN:
                s2 = False
            evs.append("%s:%dx%d frac=%.4f" % (s.get("tag"), w, h, f))
        except Exception as e:
            s1 = s2 = False
            evs.append("%s:%r" % (s.get("tag"), e))
    chk("S1", "PNG 规范可解(magic/IHDR/IDAT/CRC/filter)", s1 and bool(shots), evs)
    chk("S2", "截图非全黑(≥%.3f)" % NONBLACK_MIN, s2 and bool(shots), evs)
    return res


def print_results(res) -> int:
    bad = 0
    for cid, name, ok, ev in res:
        print("[%s] %-4s %-34s %s" % ("OK" if ok else "RED", cid, name, ev))
        if not ok:
            bad += 1
    return bad


# ---------------------------------------------------------------- selftest（合成工件 + 负控变异）
def _fixture(tmp: Path):
    out = tmp / "arm"
    (out / "shots").mkdir(parents=True, exist_ok=True)
    rows = [{"t": 1000.0 + i, "wait": 258, "code": None, "code_read_ok": True,
             "exitstate": 0, "frame": 0, "hwnd": 999, "singleton": 12345, "tick": 7}
            for i in range(41)]
    bt = [{"t": 900.0 + i * 2, "frame": 200 + i, "exitstate": 0} for i in range(30)]
    (out / "timeline.json").write_text(
        json.dumps({"battle_tl": bt,
                    "pre5": [{"t": 995.0 + i, "sent": {"frame": 2062}} for i in range(5)],
                    "close_rows": rows}), encoding="utf-8")
    shots = []
    for tag in ("battle_end", "pre_close", "post_close_end"):
        p = out / "shots" / (tag + ".png")
        w, hh = 120, 80
        rgb = bytearray(b"\x10\x20\x30" * w * hh)
        for y in range(4, hh, 6):                 # 非全黑：周期性变色行
            rgb[y * w * 3 + 3] = 0xEE
        png_write(p, w, hh, bytes(rgb))
        shots.append({"tag": tag, "path": str(p), "t": 1000.0})
    rec = {"verdict": "OK", "gamemd_pid": 4242, "closed_at_s": 120.5, "close_rows_n": len(rows),
           "battle_tl_n": len(bt), "except_before": "abc123def456ab77",
           "exit_kind": "still_running_at_watch_end", "watch_s": 40,
           "close_delivery": {"post_ok": True, "post_err": 0, "target_hwnd": 0x1234,
                              "win_pid": 4242, "win_tid": 99, "t": 1000.0},
           "shots": shots}
    return out, rec


def run_selftest() -> int:
    print("== selftest: 判定器对真实形态合成工件 ==")
    tmp = Path(tempfile.mkdtemp(prefix="xchan_st_"))
    try:
        out, rec = _fixture(tmp)
        res = judge_artifacts(out, rec)
        bad = print_results(res)
        ids = {c for c, _, _, _ in res}
        expect = {"C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "S1", "S2"}
        print("== 负控变异（每项必把指定 ID 打红）==")
        neg_bad = 0

        def mutate(name, fn, cid):
            nonlocal neg_bad
            o2, r2 = _fixture(tmp / ("m_%s" % name))
            fn(o2, r2)
            rr = {c: ok for c, _, ok, _ in judge_artifacts(o2, r2)}
            caught = rr.get(cid) is False
            print("[%s] N:%-22s ⇒ %s red=%s" % ("OK" if caught else "RED", name, cid, caught))
            if not caught:
                neg_bad += 1

        mutate("post_fail", lambda o, r: r["close_delivery"].update(post_ok=False), "C3")
        mutate("stub_PNG", lambda o, r: (o / "shots" / "pre_close.png").write_bytes(b"PNG"), "S1")
        mutate("all_black", lambda o, r: png_write(Path(r["shots"][1]["path"]), 120, 80,
                                                   b"\x00" * 120 * 80 * 3), "S2")
        def _trunc(o, r):
            p = Path(r["shots"][2]["path"]); d = p.read_bytes()
            p.write_bytes(d[:-100] + b"\x00" * 50)     # 破坏 CRC 尾块
        mutate("truncated_png", _trunc, "S1")
        mutate("tail6_only", lambda o, r: _rewrite_rows(o, r, 3), "C5")
        mutate("bt_dropped", lambda o, r: _shrink_battle_tl(o, r), "C6")
        mutate("missing_keys", lambda o, r: r.pop("closed_at_s"), "C1")
        mutate("sync_truncation", lambda o, r: _rewrite_rows(o, r, 10), "C8")
        mutate("winpid_mismatch", lambda o, r: r["close_delivery"].update(win_pid=4243), "C4")
        mutate("drop_post_shot", lambda o, r: r.__setitem__(
            "shots", [s for s in r["shots"] if s["tag"] != "post_close_end"]), "C9")

        total = bad + neg_bad + (0 if expect <= ids else 1)
        print("selftest: 主判定红=%d 负控漏抓=%d 缺ID=%s ⇒ %s"
              % (bad, neg_bad, sorted(expect - ids), "ALL-PASS" if total == 0 else "RED"))
        return 0 if total == 0 else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _rewrite_rows(o, r, keep):
    tl = json.loads((o / "timeline.json").read_text(encoding="utf-8"))
    tl["close_rows"] = tl["close_rows"][-keep:]
    (o / "timeline.json").write_text(json.dumps(tl), encoding="utf-8")
    r["close_rows_n"] = keep


def _shrink_battle_tl(o, r):
    tl = json.loads((o / "timeline.json").read_text(encoding="utf-8"))
    tl["battle_tl"] = tl["battle_tl"][:-2]
    (o / "timeline.json").write_text(json.dumps(tl), encoding="utf-8")


# ---------------------------------------------------------------- preflight（真 OS、零游戏）
def run_preflight() -> int:
    stamp = time.strftime("%Y%m%dT%H%M%S")
    pf = MYCARD / "_preflight" / stamp
    pf.mkdir(parents=True, exist_ok=False)
    checks = []

    def add(cid, name, ok, ev):
        checks.append((cid, name, bool(ok), str(ev)[:160]))
        print("[%s] %-6s %-30s %s" % ("OK" if ok else "RED", cid, name, str(ev)[:120]))

    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location("__xv2", V2_PATH)
        V = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(V)
    except Exception as e:
        add("H0", "v2 模块导入(仅常量/ctypes 级)", False, repr(e))
        V = None

    def sha16(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]

    # H 哈希钉实核
    for nm, p, want in (("gamemd", GAME_SRC / "gamemd.exe", GAMEMD_SHA16),
                        ("loader", GUARD_DIR / "rc4_loader.exe", LOADER_SHA16),
                        ("h7", H7_PATH, H7_SHA16), ("probe", PROBE_PATH, PROBE_SHA16)):
        try:
            add("H1", "sha16:" + nm, sha16(p) == want, sha16(p))
        except Exception as e:
            add("H1", "sha16:" + nm, False, repr(e))
    try:
        dll_sha = hashlib.sha256((C2_DIR / "ra2rc4guard_c2.dll").read_bytes()).hexdigest()
        add("H2", "sha256:c2_dll", dll_sha == C2_DLL_SHA256, dll_sha[:16])
    except Exception as e:
        add("H2", "sha256:c2_dll", False, repr(e))

    # carrier identity（v2 真函数）
    if V:
        good = V.MYCARD / "_preflight" / stamp / ("c" + "0" * 9)
        ok, det = V._r_carrier_identity_ok(good)
        add("I1", "identity:批准根内⇒True", ok, det)
        bad = ROOT / "out/re_work/work_chain/CONTINUE_20261003/ra2youli/RA2"
        ok2, det2 = V._r_carrier_identity_ok(bad)
        add("I2", "identity:批准根外⇒False", (not ok2) and "outside" in det2, det2)

    # 真 GDI 桌面截屏走同一判定器
    shot = pf / "desktop.png"
    try:
        w, h = capture_desktop(shot)
        rec_stub = {"verdict": "OK", "gamemd_pid": 4242, "closed_at_s": 0.0,
                    "close_rows_n": 0, "battle_tl_n": 0, "except_before": "n/a",
                    "exit_kind": "n/a_preflight",
                    "close_delivery": {"post_ok": True, "post_err": 0, "win_pid": 4242},
                    "shots": [{"tag": "pre_close", "path": str(shot), "t": 0.0},
                              {"tag": "post_close_end", "path": str(shot), "t": 0.0}]}
        res = judge_artifacts(pf, rec_stub)
        s = {c: (ok3, ev) for c, _, ok3, ev in res if c in ("S1", "S2")}
        add("S1", "桌面截屏规范可解", s["S1"][0], s["S1"][1] + " %dx%d" % (w, h))
        add("S2", "桌面截屏非全黑", s["S2"][0], s["S2"][1])
    except Exception as e:
        add("S1", "桌面截屏", False, repr(e))

    # S3（审计 BS-1 修法）：v2 发射器写侧与探针写侧**同屏对合**。
    # ★ 发现：h7 导入设进程 DPI-aware ⇒ 之前截图=逻辑 3584×967、之后=物理 5376×1451（×1.5）。
    #   真实发射中 v2 总是先 bind_real_ops(载 h7) 后截屏 ⇒ 物理尺寸；故对合必须在
    #   **同一 awareness 态**下背靠背两采（先 v2 后探针各截一张再比）。
    try:
        import importlib.util as _il
        spec = _il.spec_from_file_location("__v2_s3", V2_PATH)
        V2m = _il.module_from_spec(spec)
        spec.loader.exec_module(V2m)
        V2m.bind_real_ops()
        v2shot = pf / "desktop_via_v2.png"
        V2m.OPS["capture_screen"](v2shot)
        pshot = pf / "desktop_probe_after.png"
        P_self_w, P_self_h = capture_desktop(pshot)
        w2, h2, rgb2 = png_parse(v2shot)
        wp, hp, rgbp = png_parse(pshot)
        f2 = nonblack_frac(rgb2)
        if (w2, h2) != (wp, hp):
            add("S3", "v2写侧×判器对合", False,
                "同态尺寸仍不等 v2=%dx%d probe=%dx%d" % (w2, h2, wp, hp))
        else:
            tot = len(rgbp) // 3
            nd = sum(1 for i in range(0, len(rgbp), 3) if rgbp[i:i+3] != rgb2[i:i+3])
            frac = nd / tot
            ok3 = frac < 0.5 and f2 >= NONBLACK_MIN
            add("S3", "v2写侧×判器对合(同屏背靠背)", ok3,
                "diff=%.4f(噪声地板≈0.3,损坏签名0.9057) v2非黑frac=%.4f %dx%d" % (frac, f2, w2, h2))
    except Exception as e:
        add("S3", "v2 写侧对合", False, repr(e))

    # ini 三模式写读回（v2 真函数）
    if V:
        try:
            for guard, mode in ((1, "explicit1"), (1, "explicit0"), (1, "default"), (0, "default")):
                ini = pf / ("ini_%d_%s.ini" % (guard, mode))
                ini.write_text("[General]\nA=1\n[Logic]\nX=2\n", encoding="utf-8", newline="")
                V.apply_bail_mode(ini, guard, mode)
                body = ini.read_text(encoding="utf-8")
                key_ok = ("EnableRC4Guard=%d" % guard) in body
                bail_ok = (("EnableRC4ExitBail=1" in body) if mode == "explicit1" else
                           ("EnableRC4ExitBail=0" in body) if mode == "explicit0" else
                           ("EnableRC4ExitBail" not in body))
                add("N1", "ini:g%d/%s" % (guard, mode), key_ok and bail_ok,
                    "guard_ok=%s bail_ok=%s" % (key_ok, bail_ok))
        except Exception as e:
            add("N1", "ini 写读回", False, repr(e))

    # 残留进程检查（真实 tasklist；argv 列表免 MSYS 转义坑；BS-5 修：bytes 捕获+replace 解码，
    # 码页差异只影响中文标题不影响 ASCII 进程名 ⇒ 匹配鲁棒）
    try:
        cp = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, timeout=20)
        out = cp.stdout.decode("utf-8", errors="replace")
        hits = [ln.split(",")[0].strip('"') for ln in out.splitlines()
                if ln.lower().startswith('"gamemd.exe') or ln.lower().startswith('"rc4_loader.exe')]
        add("R1", "无 gamemd/loader 残留", not hits, hits)
    except Exception as e:
        add("R1", "tasklist", False, repr(e))

    red = sum(1 for _, _, ok, _ in checks if not ok)
    (pf / "_pf.json").write_text(json.dumps(
        {"stamp": stamp, "checks": [[c, n, o, e] for c, n, o, e in checks],
         "red": red, "probe_sha256_at_run": None}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("preflight: 红=%d ⇒ %s（记录 %s）" % (red, "GO-READY" if red == 0 else "NOT-READY", pf))
    return 0 if red == 0 else 1


def main() -> int:
    a = sys.argv[1] if len(sys.argv) > 1 else "--selftest"
    if a == "--selftest":
        return run_selftest()
    if a == "--preflight":
        return run_preflight()
    if a == "--live":
        print("!! 永久拒：本探针永不启动游戏；发射走 v2 --live（其 APPROVED_THIS_ROUND 硬闸 rc=3）")
        return 3
    print("用法: --selftest | --preflight | (--live=永久拒)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
