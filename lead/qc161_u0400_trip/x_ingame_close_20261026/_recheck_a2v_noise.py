# -*- coding: utf-8 -*-
"""_recheck_a2v_noise.py — 拆 0.2538 差分：环境噪声地板 vs 跨方法系统差。
背靠背三采：v2(修复后) → probe → probe。
  diff(v2,probe1) = 跨方法 + 噪声
  diff(probe1,probe2) = 纯噪声地板
若 噪声地板 ≈ 跨方法 ⇒ 修复对合成立（桌面内容本身在变）。零游戏，仅屏幕 DC BitBlt。
"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip")
import importlib.util
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
OUT = Path(r"C:\Users\Administrator\AppData\Local\Temp\auditprobe_a3")
OUT.mkdir(parents=True, exist_ok=True)


def load(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# 复用审计件自带的独立解码器（非探针、非 h7 家族）
spec = importlib.util.spec_from_file_location(
    "_aud_a2v", ROOT / "lead/qc161_u0400_trip/x_ingame_close_20261026/_auditprobe_a2v_capture.py")
a2v = importlib.util.module_from_spec(spec)
sys.modules["_aud_a2v"] = a2v
spec.loader.exec_module(a2v)  # 导入 main 不执行（__main__ 门）

V = load("__nv2", ROOT / "lead/qc161_u0400_trip/_drive_c2_x_probe_v2.py")
V.bind_real_ops()
P = load("__np", ROOT / "lead/qc161_u0400_trip/_x_channel_probe_20261027.py")

p_v2 = OUT / "n_v2.png"
p_p1 = OUT / "n_p1.png"
p_p2 = OUT / "n_p2.png"
p_v2b = OUT / "n_v2b.png"
V.OPS["capture_screen"](p_v2)
P.capture_desktop(p_p1)
P.capture_desktop(p_p2)
V.OPS["capture_screen"](p_v2b)


def rgb_of(p):
    d = a2v.my_decode(p)
    assert d["err"] is None, d["err"]
    return d["w"], d["h"], d["rgb"]


def diff(a, b):
    tot = len(a) // 3
    n = sum(1 for i in range(0, len(a), 3) if a[i:i+3] != b[i:i+3])
    return n, tot, n / tot


w1, h1, A = rgb_of(p_v2)
_, _, B = rgb_of(p_p1)
_, _, C = rgb_of(p_p2)
_, _, D = rgb_of(p_v2b)
print("size=%dx%d" % (w1, h1))
n, t, f = diff(A, B); print("v2   vs probe1 (跨方法+噪声): %d/%d = %.4f" % (n, t, f))
n, t, f = diff(B, C); print("probe1 vs probe2 (纯噪声)   : %d/%d = %.4f" % (n, t, f))
n, t, f = diff(A, D); print("v2   vs v2b (同法噪声)      : %d/%d = %.4f" % (n, t, f))
n, t, f = diff(A, C); print("v2   vs probe2            : %d/%d = %.4f" % (n, t, f))
