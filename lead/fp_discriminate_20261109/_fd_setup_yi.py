# -*- coding: utf-8 -*-
r"""_fd_setup_yi.py — 构造 (乙) 只删构式 两个改版（写域内副本）。
两个口径：
  乙_min：只删「唯一分解」用到的最小表项集合 —— NEG1{并不,并非} + NEG2{否认,不宣告}
          （不改 NEG1{不,不敢} / MID{敢} / NEG2{不承认}）
  乙_full：删 7 条 fp hit 所有分解的部件并集 —— NEG1{不,不敢,并不,并非} + MID{敢}
          + NEG2{不宣告,不承认,否认}
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_discriminate_20261109/_fd_setup_yi.py
"""
import sys, pathlib, hashlib
sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "fp_discriminate_20261109"
SRC_DG = ROOT / "lead" / "dneg_generative_20261109" / "_dg_core.py"
dg_src = SRC_DG.read_text(encoding="utf-8")
print("src sha256 =", hashlib.sha256(SRC_DG.read_bytes()).hexdigest(), "bytes =", SRC_DG.stat().st_size)

REM_MIN = {"NEG1": ("并不", "并非"), "MID": (), "NEG2": ("否认", "不宣告")}
REM_FULL = {"NEG1": ("不", "不敢", "并不", "并非"), "MID": ("敢",),
            "NEG2": ("不宣告", "不承认", "否认")}


def build(name, rem, label):
    L = [
        "# ===== _fd_ OVERRIDE (" + label + ") : 只删构式表项，然后重建 DG_DROPIN_RE =====",
        "import re as _fd_re",
        "_FD_REM = " + repr(rem),
        "NEG1 = tuple(w for w in NEG1 if w not in _FD_REM['NEG1'])",
        "MID = tuple(w for w in MID if w not in _FD_REM['MID'])",
        "NEG2 = tuple(w for w in NEG2 if w not in _FD_REM['NEG2'])",
        "DG_DROPIN_RE, DG_PATTERN, DG_STATS = dg_build_dropin_regex()",
        "print('[" + label + "] DG_STATS =', DG_STATS)  # 只在被实跑加载时打印",
    ]
    body = dg_src + "\n# --- " + label + " ---\n" + "\n".join(L) + "\n"
    (WD / name).write_text(body, encoding="utf-8")
    print("  WROTE", name, "chars=", len(body))


build("_fd_dg_core_yi_min.py", REM_MIN, "乙_min = 只删唯一分解所需最小表项")
build("_fd_dg_core_yi_full.py", REM_FULL, "乙_full = 删 7 fp hit 全部分解部件并集")
print("=== (乙) 两个改版建立完成 ===")
