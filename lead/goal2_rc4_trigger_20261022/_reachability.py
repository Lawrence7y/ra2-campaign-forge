# -*- coding: utf-8 -*-
"""从 0x6930A0（窗口过程的消息派发目标）做有界可达性分析，看能否到达崩溃链宿主 0x4A8960。

为什么做这件事：§344 证明了「窗口消息派发目标」与「崩溃链 this」是同一个静态对象
0x87F7E8，但没证明前者会触发后者。本脚本沿**直接 E8 调用**做 BFS 给出可证伪的下界。

★ 口径限制（必须如实声明）：
  - 只跟 E8 rel32 直调，**不跟** call [reg+x] 虚调用、不跟 jmp 表、不跟间接分发。
  - 因此「找不到」只意味着「不经虚派发不可达」，不等于不可达。
  - 深度与访问上限写死；达到上限记 TRUNCATED，不冒充 NOT_FOUND。

★ 实现要点（前版踩过的坑）：
  - **不能**从 site-0x800 这类任意偏移起解 capstone —— 会错位（§342 坑 2）。
    正确做法：**单遍线性解码**，边解边记每个指令地址所属函数，存成按偏移索引的数组。
  - 前版 68253 条 E8 边只映射出 1447 条函数级边，就是错位导致 func_start 大面积返回 None。

只读磁盘，零真机。
"""
import io
import struct
import sys
from array import array
from collections import deque

import capstone

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

ROOT = 0x006930A0        # 窗口过程的消息派发目标
TARGET = 0x004A8960      # 崩溃链宿主
MAX_DEPTH = 5
MAX_VISIT = 20000


def load():
    data = io.open(GAMEMD, "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    img_base = struct.unpack_from("<I", data, pe + 0x34)[0]
    sec_off = pe + 24 + opt_size
    secs = []
    for i in range(nsec):
        o = sec_off + i * 40
        name = data[o:o + 8].rstrip(b"\x00").decode("ascii", "replace")
        vsize, rva, rsize, roff = struct.unpack_from("<IIII", data, o + 8)
        secs.append({"name": name, "va": img_base + rva, "vsize": vsize,
                     "rsize": rsize, "roff": roff})
    return data, img_base, secs, pe


def scan(data, secs):
    """单遍线性解码：返回 (func_of, edges)。

    func_of[off] = 该偏移所属函数头 VA（数组，按 .text 偏移索引，未覆盖处为 0）
    edges = {callsite_va: target_va}
    """
    text = [s for s in secs if s["name"] == ".text"][0]
    tb = data[text["roff"]:text["roff"] + text["rsize"]]
    tva = text["va"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False

    func_of = array("I", bytes(4 * len(tb)))
    edges = {}

    cur = None            # 当前函数头
    pending_head = True   # 下一条实质指令即函数头
    off = 0
    while off < len(tb):
        hit = False
        for ins in md.disasm(tb[off:off + 15], tva + off):
            if ins.address - tva != off:
                break
            mn = ins.mnemonic
            if pending_head and mn not in ("nop", "int3"):
                cur = ins.address
                pending_head = False
            if cur is not None:
                func_of[off] = cur
            if mn == "call" and ins.op_str.startswith("0x"):
                try:
                    edges[ins.address] = int(ins.op_str, 16)
                except ValueError:
                    pass
            if mn in ("ret", "retf", "int3"):
                pending_head = True
            off += ins.size
            hit = True
            break
        if not hit:
            off += 1     # 可续解码：跳过 1 字节
    return func_of, edges, tva, len(tb)


def fn_of(func_of, tva, n, va):
    off = va - tva
    if 0 <= off < n:
        f = func_of[off]
        return f if f else None
    return None


def main():
    data, img_base, secs, pe = load()
    print("镜像基数 0x%08X" % img_base)
    print("单遍线性解码 .text ...")
    func_of, edges, tva, ntext = scan(data, secs)
    print("E8 边数 = %d" % len(edges))

    fg = {}
    unresolved = 0
    for site, tgt in edges.items():
        hs = fn_of(func_of, tva, ntext, site)
        ht = fn_of(func_of, tva, ntext, tgt)
        if hs is None or ht is None:
            unresolved += 1
            continue
        fg.setdefault(hs, {})[ht] = site     # 保留一条代表 callsite
    nedges = sum(len(v) for v in fg.values())
    print("函数级边数 = %d，涉及函数 %d 个，未解析 %d"
          % (nedges, len(fg), unresolved))
    print()

    root = fn_of(func_of, tva, ntext, ROOT)
    tgt = fn_of(func_of, tva, ntext, TARGET)
    print("ROOT   0x%08X -> 函数 0x%08X" % (ROOT, root or 0))
    print("TARGET 0x%08X -> 函数 0x%08X" % (TARGET, tgt or 0))
    print()
    if root is None or tgt is None:
        print("★ 端点无法定界")
        return 2

    prev = {root: (None, None)}
    q = deque([(root, 0)])
    found = None
    truncated = False
    visited = 0
    while q:
        fn, d = q.popleft()
        visited += 1
        if visited > MAX_VISIT:
            truncated = True
            break
        if d >= MAX_DEPTH:
            continue
        for nxt, site in sorted(fg.get(fn, {}).items()):
            if nxt in prev:
                continue
            prev[nxt] = (fn, site)
            if nxt == tgt:
                found = nxt
                q.clear()
                break
            q.append((nxt, d + 1))

    print("访问函数 %d 个（上限 %d），最大深度 %d" % (visited, MAX_VISIT, MAX_DEPTH))
    if found:
        path = []
        cur = found
        while cur is not None:
            par, site = prev[cur]
            path.append((cur, site))
            cur = par
        path.reverse()
        print()
        print("★ 在 depth<=%d 内**可达** 0x%08X：" % (MAX_DEPTH, TARGET))
        for i, (f, site) in enumerate(path):
            if site is None:
                print("   [%d] 函数 0x%08X" % (i, f))
            else:
                print("   [%d] 函数 0x%08X   ← call @0x%08X" % (i, f, site))
        return 0

    if truncated:
        print("★ TRUNCATED：达到访问上限，无法断言可达或不可达")
        return 3

    print()
    print("★ 在 depth<=%d、仅跟 E8 直调的口径下**不可达**" % MAX_DEPTH)
    print("  （这不等于不可达：虚调用 [reg+x] 与 jmp 表未纳入）")
    n1 = sorted(fg.get(root, {}).items())
    print()
    print("ROOT 的直接 callee（%d 个）：" % len(n1))
    for f, site in n1:
        print("   0x%08X  ← call @0x%08X" % (f, site))
    return 1


if __name__ == "__main__":
    sys.exit(main())
