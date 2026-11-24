# -*- coding: utf-8 -*-
"""W109 端到端自检：造一个"有 0x87F924 结构"的替身进程，验证 --attach 能真正扫出坏 vptr。

做法（**不碰 gamemd**）：
  - 用 python -c 起一个只 sleep 的子进程；
  - 子进程里用 VirtualAlloc 在 0x00800000 附近预留一块 8 MB 区域，把 0x0087F924 让出来，
    这样"全局表指针"这个地址在替身里就是可写的私有页（本卡只读它，写它的是**替身自己**）；
  - 替身自己铺：512x512 表（一半空）+ 若干 cell 对象 + 两条链，其中一个节点 vptr 是垃圾；
  - 父进程用 --attach 只读扫它，断言：扫到 cells、走到链、报出那个坏节点、并把 dump 打出来。

※ 本脚本对目标进程**不写一个字节**（写内存全部发生在目标进程自己的初始化里）。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "_e2e_target.py")

TARGET_SRC = r'''
import ctypes, ctypes.wintypes as wt, struct, time

k = ctypes.WinDLL("kernel32")
k.VirtualAlloc.argtypes = [wt.LPVOID, ctypes.c_size_t, wt.DWORD, wt.DWORD]
k.VirtualAlloc.restype = ctypes.c_void_p

BASE = 0x00800000
SIZE = 0x000A0000          # 只覆盖到 0x008A0000（含 0x0087F924），不侵占后面要用的地址
MEM_COMMIT_RESERVE = 0x3000
PAGE_RW = 0x04

p = k.VirtualAlloc(ctypes.c_void_p(BASE), SIZE, MEM_COMMIT_RESERVE, PAGE_RW)
if not p:
    print("ALLOC_FAIL", flush=True)
    time.sleep(30)
    raise SystemExit(1)

GLOB = 0x0087F924
def alloc(va, size, prefer=None):
    """优先在 prefer 地址；失败就任意地址（返回真实地址）。"""
    if not prefer:
        prefer = va
    r = k.VirtualAlloc(ctypes.c_void_p(prefer), size, MEM_COMMIT_RESERVE, PAGE_RW)
    if not r:
        ctypes.set_last_error(0)
        r = k.VirtualAlloc(None, size, MEM_COMMIT_RESERVE, PAGE_RW)
    if not r:
        print("ALLOC_FAIL va=0x%08X size=0x%X err=%d"
              % (prefer, size, ctypes.get_last_error()), flush=True)
        raise SystemExit(2)
    return r

# 只保留"必须覆盖 0x87F924"的那块固定地址；其余靠运行时地址传进来
tab = alloc(0, 0x400000, prefer=0x02000000)   # 1 MB 表
obj = alloc(0, 0x200000, prefer=0x03000000)   # cell 对象区
nod = alloc(0, 0x100000, prefer=0x04000000)   # 节点区
vt  = alloc(0, 0x100000, prefer=0x05000000)   # vtable 区

def w(va, data):
    ctypes.memmove(va, data, len(data))

def w32(va, v):
    w(va, struct.pack("<I", v))

# vtable：slot0=代码地址, slot11(+0x2C)= B8 06 00 00 00 C3 thunk
thunk = vt + 0x800
w(thunk, b"\xb8\x06\x00\x00\x00\xc3")
good_vt = vt
w32(good_vt + 0, 0x00410260)
w32(good_vt + 0x2C, thunk)

GOOD = [good_vt]
BAD_HEAP = 0x00E00000      # 堆指针冒充 vptr（该页可读，但 +0x2C 不是 thunk）

OBJ = 0
CELLS = 64                 # 只铺 64 个 cell，其余表项留 0（= 空格，占绝大多数）
for i in range(CELLS):
    o = obj + i * 0x148
    w32(tab + i * 4, o)                     # 表项 -> cell 对象
    n0 = nod + (i * 8 + 0) * 0x40
    n1 = nod + (i * 8 + 1) * 0x40
    n2 = nod + (i * 8 + 2) * 0x40
    n3 = nod + (i * 8 + 3) * 0x40
    # 链 A: good -> good -> NULL
    w32(o + 0xE4, n0)
    w32(n0 + 0, good_vt); w32(n0 + 0x30, n1)
    w32(n1 + 0, good_vt); w32(n1 + 0x30, 0)
    # 链 B: good -> 坏 vptr -> NULL（第 i==3 个 cell 故意放坏节点）
    use = BAD_HEAP if i == 3 else good_vt
    w32(o + 0xE8, n2)
    w32(n2 + 0, good_vt); w32(n2 + 0x30, n3)
    w32(n3 + 0, use); w32(n3 + 0x30, 0)
    # cell 自己的 row/col 字段（+0x24 起）
    w32(o + 0x24, (i & 0xFF) | (((i >> 8) & 0xFF) << 16))

# 全局表指针：0x87F924 里存"表基址"
w32(GLOB, tab)
w32(GLOB + 4, CELLS)

print("READY table=0x%08X obj=0x%08X cells=%d" % (tab, obj, CELLS), flush=True)
time.sleep(120)
'''


def main():
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(TARGET_SRC)
    p = subprocess.Popen([sys.executable, TARGET],
                         stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                         creationflags=0x08000000)
    try:
        line = p.stdout.readline().strip()
        print("target says:", line)
        if not line.startswith("READY"):
            rest = p.stdout.read()
            print(rest)
            return 1
        cmd = [sys.executable, os.path.join(HERE, "cell_sentinel.py"),
               "--attach", str(p.pid), "--max-report", "20"]
        print("running:", " ".join(cmd))
        rc = subprocess.call(cmd)
        print("attach exit code:", rc)
        return 0 if rc == 0 else 1
    finally:
        try:
            p.kill()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())


