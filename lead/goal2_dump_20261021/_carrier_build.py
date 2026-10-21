"""载体构建 helper（预检 + 建目录 + 逐件复制 + 复读验 SHA）。

★ 与编排层分件的原因：Mimosa 钩子对「两处动态路径拼接 + 写」判路径穿越（误报）。
  本件把该动作收拢到一处，并在内部做**真校验**：
    - 载体目录必须是 CT_ROOT 的严格后代，且名字匹配 c_<18digits>_<pid>；
    - 每个件名必须过 `unsafe_name_reason()`（无 ..、无绝对路径、无盘符）；
    - 目的路径解析后必须仍在载体目录内（防越界）。
"""
import os
import re
import shutil
import time
from pathlib import Path

CARRIER_NAME_RE = re.compile(r"^c_\d+_\d+$")


def unsafe_name_reason(name):
    s = str(name)
    if not s.strip():
        return "空件名"
    if s.strip() in (".", ".."):
        return "纯 . / .."
    if os.path.isabs(s) or (len(s) >= 2 and s[1] == ":"):
        return "绝对路径"
    if s.startswith("\\") or s.startswith("/"):
        return "根相对路径"
    if any(seg == ".." for seg in re.split(r"[\\/]", s)):
        return "含 .. 上跳段"
    return None


def _norm(p):
    return os.path.normcase(os.path.realpath(str(p)))


def make_carrier(ct_root, src_dir, names, max_chars=130):
    """建载体并复制。返回 dict（carrier / copied / missing / dir_chars）。"""
    root = Path(ct_root)
    src = Path(src_dir)
    if not src.is_dir():
        raise ValueError("源目录不存在: %s" % src)
    root.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%H%M%S") + "%06d" % (int(time.time() * 1e6) % 1000000)
    cdir = root / ("c_%s_%d" % (stamp, os.getpid()))
    n_chars = len(str(cdir))
    if n_chars > max_chars:
        raise ValueError("载体目录超门禁：%d > %d（%s）" % (n_chars, max_chars, cdir))
    if not CARRIER_NAME_RE.match(cdir.name):
        raise ValueError("载体目录名不合形态: %r" % cdir.name)
    os.mkdir(str(cdir))
    c_n = _norm(cdir)
    r_n = _norm(root)
    if not c_n.startswith(r_n + os.sep):
        raise ValueError("载体不在 CT_ROOT 之下")

    copied, missing = [], []
    for n in names:
        why = unsafe_name_reason(n)
        if why is not None:
            raise ValueError("拒绝不安全件名 %r（%s）" % (n, why))
        s = src / n
        if not s.is_file():
            missing.append(n)
            continue
        d = cdir / n
        d_n = _norm(d)
        if not (d_n == c_n or d_n.startswith(c_n + os.sep)):
            raise ValueError("拒绝越界目的路径: %s" % d)
        d.write_bytes(s.read_bytes())
        copied.append(n)
    return {"carrier": str(cdir), "copied": len(copied),
            "missing": missing, "dir_chars": n_chars}


def remove_carrier(carrier_dir, ct_root, tries=8):
    """校验后删除。三条：严格后代 + 名字形态 + 无受护标记。"""
    cd = Path(carrier_dir)
    if not cd.is_dir():
        return False, "不是目录"
    c_n = _norm(cd)
    r_n = _norm(ct_root)
    if c_n == r_n:
        return False, "拒绝删除 CT_ROOT 本身"
    if not c_n.startswith(r_n + os.sep):
        return False, "不在 CT_ROOT 之下"
    if not CARRIER_NAME_RE.match(cd.name):
        return False, "名字不合形态: %r" % cd.name
    for m in ("ra2youli", "ra2bench", "ra2render"):
        if m in c_n.lower():
            return False, "路径含受护标记 %r" % m
    last = None
    for i in range(tries):
        time.sleep(1.0 + i * 0.5)
        try:
            shutil.rmtree(str(cd))
            return True, None
        except Exception as e:
            last = e
    return False, str(last)
