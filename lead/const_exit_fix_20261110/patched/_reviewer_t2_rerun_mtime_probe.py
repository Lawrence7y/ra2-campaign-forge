# -*- coding: utf-8 -*-
"""W11/T2 只读探针：在临时目录里实测 mtime / sha256 判定新鲜性的四个陷阱。

零真机、零注入：只操作本脚本自建的临时目录，不碰任何真实趟目录。
输出写到同目录 _w11_t2_mtime_probe_out.txt。
"""
import ctypes
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "_w11_t2_mtime_probe_out.txt"
lines = []


def say(s=""):
    lines.append(s)
    print(s)


say(f"probe run at {datetime.now().isoformat()}")
tmp = Path(tempfile.mkdtemp(prefix="w11_t2_mtime_", dir=str(HERE)))
say(f"tmp = {tmp}")

# ---- 0. 卷文件系统类型（离线 ctypes，不需要管理员） ----
try:
    k32 = ctypes.windll.kernel32
    root = str(tmp.drive + "\\")
    name = ctypes.create_unicode_buffer(64)
    fs = ctypes.create_unicode_buffer(64)
    serial = ctypes.wintypes.DWORD() if hasattr(ctypes, "wintypes") else None
    import ctypes.wintypes as wt
    serial = wt.DWORD()
    flags = wt.DWORD()
    maxlen = wt.DWORD()
    ok = k32.GetVolumeInformationW(ctypes.c_wchar_p(root), name, 64,
                                   ctypes.byref(serial), ctypes.byref(maxlen),
                                   ctypes.byref(flags), fs, 64)
    say(f"[0] volume {root} fs={fs.value!r} ok={bool(ok)}")
except Exception as e:  # noqa: BLE001
    say(f"[0] volume info FAILED: {type(e).__name__}: {e}")

SRC = tmp / "src.txt"
SRC.write_bytes(b"line-A\n" * 3)
say(f"\n[1] 源件 mtime0 = {SRC.stat().st_mtime!r} ({datetime.fromtimestamp(SRC.stat().st_mtime)})")

# ---- 1. write_bytes 复制：mtime 不保留（harness :4958 的方式） ----
time.sleep(0.05)
D1 = tmp / "dst_writebytes.txt"
D1.write_bytes(SRC.read_bytes())
say(f"[1] write_bytes 复制件 mtime = {D1.stat().st_mtime!r}  != 源 {SRC.stat().st_mtime!r} ⇒ 不保留（新 mtime=复制时刻）")

# ---- 2. shutil.copy2 复制：mtime 保留（陷阱） ----
time.sleep(0.05)
D2 = tmp / "dst_copy2.txt"
shutil.copy2(SRC, D2)
same = (D2.stat().st_mtime == SRC.stat().st_mtime)
say(f"[2] copy2 复制件 mtime = {D2.stat().st_mtime!r}  == 源 ⇒ mtime 保留：{'陷阱成立' if same else '本机未复现'}")

# ---- 3. os.utime 伪造 mtime（mtime 可以被随意改写） ----
old = 946684800.0  # 2000-01-01
D2_ut = tmp / "dst_forged.txt"
D2_ut.write_bytes(SRC.read_bytes())
os.utime(D2_ut, (old, old))
st = D2_ut.stat()
say(f"[3] utime 伪造后 mtime = {st.st_mtime!r} ({datetime.fromtimestamp(st.st_mtime)}) ⇒ 文件刚写的，mtime 却是 2000 年 ⇒ mtime 可被主动伪造")

# ---- 4. 同内容重写：sha256 不变、mtime 变（B 方案的盲区 = A 方案的可见区） ----
P = tmp / "same_content.txt"
P.write_bytes(b"Exception occurred at X\n")
sha1 = __import__("hashlib").sha256(P.read_bytes()).hexdigest()
m1 = P.stat().st_mtime
time.sleep(0.05)
P.write_bytes(b"Exception occurred at X\n")   # 游戏重写同一内容
sha2 = __import__("hashlib").sha256(P.read_bytes()).hexdigest()
m2 = P.stat().st_mtime
say(f"[4] 同内容重写：sha {sha1[:12]}→{sha2[:12]}（相同={sha1 == sha2}）；mtime {m1!r}→{m2!r}（变化={m1 != m2}）")
say("    ⇒ B 方案（哈希）对「同内容重写」失明；mtime 反而看得见")

# ---- 5. 内容变了但 mtime 被 utime 拉回（A 方案的盲区） ----
Q = tmp / "changed_but_forged.txt"
Q.write_bytes(b"old\n")
mq = Q.stat().st_mtime
time.sleep(0.05)
Q.write_bytes(b"NEW-CONTENT\n")               # 内容真变了
os.utime(Q, (mq, mq))                          # mtime 拉回旧值
sha1q = __import__("hashlib").sha256(b"old\n").hexdigest()
sha2q = __import__("hashlib").sha256(Q.read_bytes()).hexdigest()
say(f"[5] 内容变更+utime 拉回：sha {sha1q[:12]}→{sha2q[:12]}（变化={sha1q != sha2q}）；mtime {mq!r}→{Q.stat().st_mtime!r}（相同={Q.stat().st_mtime == mq}）")
say("    ⇒ A 方案对「改内容+伪造 mtime」失明；哈希看得见")

# ---- 6. 同 tick 多次写：mtime 分辨率实测 ----
R = tmp / "tick.txt"
seen = []
for _ in range(200):
    R.write_bytes(b"x")
    seen.append(R.stat().st_mtime)
distinct = len(set(seen))
say(f"[6] 连写 200 次立即 stat：{distinct} 个不同 mtime ⇒ 观测分辨率内同 tick 多次写{'可分辨' if distinct > 1 else '不可分辨'}（NTFS 名义 100ns，FAT 系 2s）")

# ---- 7. 时钟回拨：无权限实测 ⇒ 只列原理，不造数 ----
say("[7] 时钟回拨：需要改系统时间权限，本探针不实测（零风险约束）⇒ 判据设计按原理处理：回拨使 写入时刻的 mtime < 跑前锚点 ⇒ A 方案假阴性")

say(f"\ncleanup tmp={tmp}")
shutil.rmtree(tmp, ignore_errors=True)
say(f"probe done, PASS (exit 0)")
OUT.write_text("\n".join(lines), encoding="utf-8")
sys.exit(0)
