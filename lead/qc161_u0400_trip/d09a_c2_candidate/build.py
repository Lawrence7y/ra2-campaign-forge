#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""c″ 候选副本构建脚本：直调 cl.exe（铁律 1：不跑 build.bat；无 shell、参数全字面量）。
旗标与母本构建一致（台账：/O2 /W3 /EHsc /arch:SSE2 /LD，MSVC 14.44.35207 x86）。
vcvars 不用——INCLUDE/LIB 显式构造（vcvars 的引号路径经 cmd 会被二次拆坏）。
产物 = 本目录 ra2rc4guard_c2.dll（候选件；进载体时由趟脚本改名 ra2rc4guard.dll）。
"""
import subprocess
import hashlib
import io
import sys
import os
import glob
from pathlib import Path

HERE = Path(__file__).parent

MSVC_ROOT = r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207"
CL_EXE = MSVC_ROOT + r"\bin\Hostx64\x86\cl.exe"
assert os.path.isfile(CL_EXE), "cl.exe not found: " + CL_EXE

kit_inc_root = sorted(glob.glob(r"C:\Program Files (x86)\Windows Kits\10\Include\*"))[-1]
kit_lib_root = sorted(glob.glob(r"C:\Program Files (x86)\Windows Kits\10\Lib\*"))[-1]
assert os.path.isdir(kit_inc_root) and os.path.isdir(kit_lib_root)

env = dict(os.environ)
env["INCLUDE"] = ";".join([
    MSVC_ROOT + r"\include",
    kit_inc_root + r"\ucrt",
    kit_inc_root + r"\um",
    kit_inc_root + r"\shared",
    kit_inc_root + r"\winrt",
])
env["LIB"] = ";".join([
    MSVC_ROOT + r"\lib\x86",
    kit_lib_root + r"\ucrt\x86",
    kit_lib_root + r"\um\x86",
])

r = subprocess.run([
    CL_EXE,
    "/O2", "/W3", "/EHsc", "/arch:SSE2", "/utf-8", "/LD",
    "src\\rc4_guard.cpp", "/Fe:ra2rc4guard_c2.dll", "/Fo:ra2rc4guard_c2.obj",
], cwd=str(HERE), capture_output=True, env=env)

out = (r.stdout or b"").decode("gbk", errors="replace")
err = (r.stderr or b"").decode("gbk", errors="replace")
io.open(HERE / "build_log.txt", "w", encoding="utf-8", errors="replace").write(
    CL_EXE + "\n\n---stdout---\n" + out + "\n---stderr---\n" + err)
print("cl exit =", r.returncode)
for ln in out.splitlines()[-8:]:
    print("  |", ln)
for ln in err.splitlines()[-4:]:
    print("  E|", ln)
if r.returncode != 0:
    print("BUILD FAILED —— 详见 build_log.txt")
    sys.exit(1)

dll = HERE / "ra2rc4guard_c2.dll"
assert dll.exists(), "DLL missing"
h = hashlib.sha256(dll.read_bytes()).hexdigest()
print("DLL: %d bytes, sha256 %s" % (dll.stat().st_size, h))
(HERE / "dll_sha256.txt").write_text(h)
print("BUILD OK")
