# -*- coding: utf-8 -*-
"""_w2_probe2.py — 目录级继承 deny 能否跨「文件被重建」持续（T0→T1 桥接条件）。"""
import os
import subprocess
from pathlib import Path

W2DIR = Path(r"D:\Project\ra2-campaign-forge\lead\w2_samecause_20261109")
CASE2 = W2DIR / "_w2_case2"
USER = os.environ.get("USERNAME", "Administrator")


def icacls(*args):
    r = subprocess.run(["icacls", *args], capture_output=True,
                       encoding="mbcs", errors="replace")
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()


def try_read(p, tag):
    try:
        with open(p, "rb") as f:
            f.read(1)
        print(f"  [{tag}] open 读 = ok")
        return True
    except OSError as e:
        print(f"  [{tag}] open 读 = OSError winerror={getattr(e,'winerror',None)} {type(e).__name__}")
        return False


CASE2.mkdir(parents=True, exist_ok=True)
f1 = CASE2 / "except.txt"
f1.write_bytes(b"gen0\n")

print("== 目录级 (OI)(CI) deny-RD，模拟「游戏跑中重建 except.txt」后 ACE 是否仍在 ==")
rc, out = icacls(str(CASE2), "/deny", f"{USER}:(OI)(CI)(RD)")
print(f"  icacls /deny {USER}:(OI)(CI)(RD) on dir -> rc={rc}")
try_read(f1, "T0 原件")
f1.unlink()                      # 模拟游戏删除旧件
f2 = CASE2 / "except.txt"        # 模拟游戏重建同名件
f2.write_bytes(b"gen1 crash info\n")
try_read(f2, "T1 重建件")
print("  → 目录继承 deny 在重建后仍拒读 =", not try_read(f2, "T1 重建件复核"))

rc, out = icacls(str(CASE2), "/remove:d", USER)
print(f"  icacls /remove:d on dir -> rc={rc}")
try_read(f2, "还原后")
f2.unlink()
CASE2.rmdir()
print("PROBE2_DONE")
