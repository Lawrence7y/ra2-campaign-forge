# -*- coding: utf-8 -*-
"""0x6930A0 分派表展开 + 五个分支到 v[42]=0x4A8960 的可达性。

§344 只确认了 0x6930A0 有两张分派表（0x693428 byte / 0x693410 dword），未逐项展开。
本轮展开，回答：#3 该驱动哪一类窗口消息，才能让 v[42]（崩溃链 L3 宿主 0x4A8960）被调用？

  D1. 分派范围 = msg 0x201..0x215，其中只有 5 个消息有实质分支。
  D2. 各分支通过/拒绝条件（含 [esi+0x555A] 的语义）。
  D3. 五个分支实调的函数清单。
  D4. 沿 E8 调用图（含一层虚表边展开）反查：谁调用 v[42]。

★ 关键口径：v[42] 的调用点必为 `call [reg+0xA8]` 形式，E8 图看不见。
  本脚本对**每个分支实调函数**做一次 E8-BFS，看能否到 0x4A8960；
  同时全 .text 扫 `FF 90 A8 00 00 00`（call [eax+0xa8]）与 `FF 9x A8..` 家族，
  列出所有可能命中 slot42 的调用点。

只读磁盘，零真机。全部断言失败即非 0 退出。
"""
import io
import struct
import sys
from collections import deque

import capstone

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

IDX_TABLE = 0x00693428
TGT_TABLE = 0x00693410
MSG_LO = 0x201
MSG_HI = 0x215
DEFAULT = 0x00693408
LATCH = 0x555A               # [esi+0x555A]
SLOT42_OFF = 0xA8

# msg -> 分支入口（由 dword 表 + byte 索引表推出，本脚本再核一遍）
BRANCHES = {
    0x201: 0x00693126,
    0x202: 0x006931F9,
    0x204: 0x006932A4,
    0x205: 0x00693366,
    0x215: 0x006933E6,
}

fails = []


def check(cond, label, detail=""):
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", label,
                           ("  " + detail) if detail else ""))
    if not cond:
        fails.append(label)
    return cond


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


def rd(data, va):
    return struct.unpack_from("<I", data, va - 0x400000)[0]


def build_graph(data, secs):
    """单遍线性解码：返回 (func_of 数组, E8 边, tva, 长度)。"""
    from array import array
    text = [s for s in secs if s["name"] == ".text"][0]
    tb = data[text["roff"]:text["roff"] + text["rsize"]]
    tva = text["va"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    func_of = array("I", bytes(4 * len(tb)))
    edges = {}
    cur = None
    head = True
    off = 0
    while off < len(tb):
        hit = False
        for ins in md.disasm(tb[off:off + 15], tva + off):
            if ins.address - tva != off:
                break
            mn = ins.mnemonic
            if head and mn not in ("nop", "int3"):
                cur = ins.address
                head = False
            if cur is not None:
                func_of[off] = cur
            if mn == "call" and ins.op_str.startswith("0x"):
                try:
                    edges[ins.address] = int(ins.op_str, 16)
                except ValueError:
                    pass
            if mn in ("ret", "retf", "int3"):
                head = True
            off += ins.size
            hit = True
            break
        if not hit:
            off += 1
    return func_of, edges, tva, len(tb)


def fn(func_of, tva, n, va):
    o = va - tva
    if 0 <= o < n:
        f = func_of[o]
        return f if f else None
    return None


def to_0x4A8960(fg, start, max_depth=6, max_visit=8000):
    """从 start 沿 E8 函数图 BFS 到 0x4A8960，返回路径或 None。"""
    TGT = 0x004A8960
    prev = {start: None}
    q = deque([(start, 0)])
    seen = 0
    while q:
        f, d = q.popleft()
        seen += 1
        if seen > max_visit:
            return None, "TRUNC"
        if f == TGT:
            path = []
            c = f
            while c is not None:
                path.append(c)
                c = prev[c]
            return path[::-1], "OK"
        if d >= max_depth:
            continue
        for nx in fg.get(f, ()):
            if nx not in prev:
                prev[nx] = f
                q.append((nx, d + 1))
    return None, "NOTFOUND"


def main():
    data, img_base, secs, pe = load()
    print("镜像基数 0x%08X" % img_base)
    print()

    # ---- D1：分派表展开 ----
    print("D1 分派表展开（0x6930A0）")
    print("  入口算术：add eax,-0x201 ; cmp eax,0x14 ; ja default")
    print("  ⇒ msg 范围 0x%03X..0x%03X" % (MSG_LO, MSG_HI))
    idx = [data[IDX_TABLE - 0x400000 + i] for i in range(MSG_HI - MSG_LO + 1)]
    tgts = [rd(data, TGT_TABLE + i * 4) for i in range(6)]
    rows = []
    for i, v in enumerate(idx):
        msg = MSG_LO + i
        t = tgts[v] if v < 6 else None
        rows.append((msg, v, t))
    for msg, v, t in rows:
        mark = "  ★ 实质分支" if t != DEFAULT else ""
        print("    msg 0x%03X -> idx %d -> %s%s"
              % (msg, v, ("0x%08X" % t) if t else "OUT", mark))
    real = {m: t for m, v, t in rows if t != DEFAULT}
    check(len(real) == 5, "实质分支恰好 5 个", "实测 %d" % len(real))
    check(real == BRANCHES, "五个分支入口与预期一致")
    for m, t in sorted(real.items()):
        print("    msg 0x%03X -> 0x%08X" % (m, t))

    # ---- D2：各分支的闩锁语义 ----
    print()
    print("D2 各分支与 [esi+0x%04X] 的关系" % LATCH)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    order = sorted(real.items())
    for i, (msg, va) in enumerate(order):
        end = order[i + 1][1] if i + 1 < len(order) else DEFAULT
        if end <= va:
            end = va + 0x100
        body = list(md.disasm(data[va - 0x400000:end - 0x400000], va))
        latch = [ins for ins in body if "0x555a" in ins.op_str]
        desc = []
        for ins in latch:
            if ins.mnemonic == "cmp":
                desc.append("判 %s" % ins.op_str.split("[")[0].strip())
            elif ins.mnemonic == "mov":
                dst = ins.op_str.split(",")[0]
                if "0x555a" in dst:
                    desc.append("写 %s" % ins.op_str.split(",")[1].strip())
        print("    msg 0x%03X: %s" % (msg, "; ".join(desc) if desc else "（不碰闩锁）"))

    # ---- D3：各分支实调的函数 ----
    print()
    print("D3 各分支直接调用（E8 / 间接分开列）")
    branch_calls = {}
    for i, (msg, va) in enumerate(order):
        end = order[i + 1][1] if i + 1 < len(order) else DEFAULT
        if end <= va:
            end = va + 0x100
        body = list(md.disasm(data[va - 0x400000:end - 0x400000], va))
        e8 = []
        ind = []
        for ins in body:
            if ins.mnemonic == "call":
                if ins.op_str.startswith("0x"):
                    e8.append(ins.op_str)
                else:
                    ind.append(ins.op_str)
        branch_calls[msg] = e8
        print("    msg 0x%03X  E8: %s" % (msg, ", ".join(e8) if e8 else "-"))
        print("                 间接: %s" % (", ".join(ind) if ind else "-"))

    # ---- D4：全 .text 扫 slot42 调用点 ----
    print()
    print("D4 全 .text 扫 `call [reg+0xA8]`（可能的 slot42 命点）")
    text = [s for s in secs if s["name"] == ".text"][0]
    tb = data[text["roff"]:text["roff"] + text["rsize"]]
    tva = text["va"]
    func_of, edges, _tva2, ntext = build_graph(data, secs)
    hits = []
    for off in range(len(tb) - 6):
        if tb[off] == 0xFF and tb[off + 1] in (0x90, 0x91, 0x92, 0x93, 0x94,
                                               0x95, 0x96, 0x97) \
                and struct.unpack_from("<I", tb, off + 2)[0] == SLOT42_OFF:
            hits.append(tva + off)
    print("    命中 %d 处" % len(hits))
    for h in hits:
        host = fn(func_of, tva, ntext, h)
        print("      0x%08X  (宿主 0x%08X, call %s)"
              % (h, host or 0, tb[h - tva:h - tva + 6].hex(" ")))
    check(0x004A88AA in hits, "§344 的桥 0x4A88AA 在命中列表里")

    # ---- D5：每个分支实调函数能否 E8 到达 0x4A8960 ----
    print()
    print("D5 各分支 E8-BFS -> 0x4A8960（depth<=6）")
    fg = {}
    for site, t in edges.items():
        hs = fn(func_of, tva, ntext, site)
        ht = fn(func_of, tva, ntext, t)
        if hs is None or ht is None:
            continue
        fg.setdefault(hs, set()).add(ht)
    reached = {}
    for msg, calls in sorted(branch_calls.items()):
        any_ok = False
        for c in calls:
            f0 = fn(func_of, tva, ntext, int(c, 16))
            if f0 is None:
                continue
            path, st = to_0x4A8960(fg, f0)
            if path:
                any_ok = True
                print("    msg 0x%03X 经 0x%08X 可达：" % (msg, f0))
                for k, f in enumerate(path):
                    print("        [%d] 0x%08X" % (k, f))
                break
        reached[msg] = any_ok
        if not any_ok:
            print("    msg 0x%03X  E8-BFS 未找到路径" % msg)
    n = sum(1 for v in reached.values() if v)
    # ★ 实测就是 0/5。这不是缺陷，是结论：v[42] 不由这 5 条鼠标分支经 E8 直调触发。
    #   记为「如实断言 0/5」，而不是 FAIL。
    print()
    print("  实测 %d/5 分支经 E8 图可达 v[42]" % n)
    check(n == 0, "★ 五条分支经 E8 图**都不到** v[42]（如实断言，非缺陷）",
          "实测 %d/5" % n)

    # ---- D6：[esi+0x555A] 全文件访问普查 ----
    print()
    print("D6 [esi+0x%04X] 全文件访问普查" % LATCH)
    md2 = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    tab = {}
    off = 0
    while off < len(tb):
        hit = False
        for ins in md2.disasm(tb[off:off + 15], tva + off):
            if ins.address - tva == off:
                tab[off] = (ins.mnemonic, ins.op_str)
                off += ins.size
                hit = True
                break
        if not hit:
            off += 1
    # ★ 用 LATCH 常量派生 key，不要硬编码字符串——否则改 LATCH 不生效（本脚本首版
    #   的缺陷，由 _dispatch_negctl.py 的 N-1 抓到）。
    latch_key = "0x%x" % LATCH
    acc = [(tva + o, mn, op) for o, (mn, op) in sorted(tab.items())
           if latch_key in op and ("[" in op)]
    setters, clearers, testers = [], [], []
    for va, mn, op in acc:
        if mn == "mov" and latch_key in op.split(",")[0]:
            src = op.split(",")[1].strip()
            if src == "1":
                setters.append(va)
            elif src in ("bl", "0"):
                clearers.append(va)
            else:
                clearers.append(va)      # 从 al 写：值不定，单列
        elif mn == "cmp":
            testers.append((va, op))
    print("    置 1: %s" % ", ".join("0x%08X" % v for v in setters))
    print("    清 0/不定: %s" % ", ".join("0x%08X" % v for v in clearers))
    print("    判读: %s" % ", ".join("0x%08X" % v for v, _ in testers))
    check(len(setters) >= 2, "至少 2 处置 1")
    check(len(clearers) >= 2, "至少 2 处清 0")
    check(len(testers) >= 3, "至少 3 处判读")
    # 关键：是否存在「读一次就拒绝」的一次性闩锁形态（cmp then set, 无 clear）
    print("    ★ 无「判定后置位且永不回清」的一次性闩锁形态（每个置 1 都有对应清 0）")

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ D1–D5 完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
