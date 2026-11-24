#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-E T1/T2：高频采样 + 在步兵格放置建筑。
 - ≥5000/s 紧循环（无 sleep），持续 ≥1.5s
 - 每样本：frame(0xA8ED84)、0xA8E7AC、0xA8E9A0、目标格 headA(+0xE4)/headB(+0xE8)、
   链长(沿+0x30防环)、链上每节点 this+vptr+RTTI(COL+0xC->TD+8，读不到记 [未证])
 - JSONL 全量落盘（热循环只入内存，循环后一次写出，避免 I/O 拖慢采样）
 - 在采样窗内 t≈0.35s 触发放置点击（裸 mouse_event，无夺焦），记录 click_t
全部只读内存 + 合成输入；不写进程内存/不注入。
"""
import sys, os, time, json, ctypes, struct
from ctypes import wintypes as wt
import w177_core as W
import wb_probe as P

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
u32 = ctypes.windll.user32
u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.mouse_event.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_size_t]
LEFTDOWN, LEFTUP = 0x0002, 0x0004
k32 = ctypes.windll.kernel32

VA_LO, VA_HI = 0x00400000, 0x00900000
def dok(obj): return bool(obj) and (obj & 3) == 0 and 0x00100000 <= obj <= 0x7FFFFFFF
def dva(v): return bool(v) and VA_LO <= v <= VA_HI

class FastMem:
    def __init__(self, h):
        self.h = h
        self.b4 = ctypes.create_string_buffer(4)
        self.b1 = ctypes.create_string_buffer(1)
        self.b32 = ctypes.create_string_buffer(32)
        self.got = ctypes.c_size_t(0)
    def rd(self, va, buf, n):
        if k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), buf, n, ctypes.byref(self.got)) and self.got.value == n:
            return buf.raw[:n]
        return None
    def u32(self, va):
        b = self.rd(va, self.b4, 4)
        return struct.unpack("<I", b)[0] if b else None
    def u8(self, va):
        b = self.rd(va, self.b1, 1)
        return b[0] if b else None
    def name(self, td):
        b = self.rd(td + 8, self.b32, 32)
        if not b: return None
        z = b.find(b"\x00")
        s = b if z < 0 else b[:z]
        try: s = s.decode("latin-1")
        except Exception: return None
        return s if s.startswith(".?A") else (s or None)

def rtti(fm, obj):
    """返回 (name, vptr, col, td)；任一步失败 name=None([未证])"""
    vptr = fm.u32(obj) if dok(obj) else None
    if not dva(vptr): return None, vptr, None, None
    col = fm.u32(vptr - 4)
    if not dva(col): return None, vptr, col, None
    td = fm.u32(col + 0xC)
    if not dva(td): return None, vptr, col, td
    return fm.name(td), vptr, col, td

def main():
    cx = int(sys.argv[1]); cy = int(sys.argv[2])
    sx = int(sys.argv[3]); sy = int(sys.argv[4])
    dur = float(sys.argv[5]) if len(sys.argv) > 5 else 2.0
    tag = sys.argv[6] if len(sys.argv) > 6 else "place"
    click_at = float(sys.argv[7]) if len(sys.argv) > 7 else 0.35

    pid = W.pid_of()
    m = W.Mem(pid)
    fm = FastMem(m.h)
    ph = P.player_house(m)
    cellbase = fm.u32(P.CELL_ARRAY)
    idx = (cy << 9) + cx
    cell = fm.u32(cellbase + idx * 4)
    credit_before = fm.u32(ph + 0x30C)
    print("pid=%d ph=%s cellbase=%s cell(%d,%d)=%s credit=%d" % (
        pid, hex(ph), hex(cellbase), cx, cy, hex(cell) if cell else None, credit_before))

    # 预置光标到目标
    u32.SetCursorPos(sx, sy)
    time.sleep(0.25)

    rows = []
    meta = {"tag": tag, "pid": pid, "cx": cx, "cy": cy, "screen": [sx, sy],
            "cell": hex(cell) if cell else None, "dur_target_s": dur,
            "click_at_s": click_at, "credit_before": credit_before,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "columns": ["t", "frame", "a8e7ac", "a8e9a0", "headA", "headB",
                        "lenA", "lenB", "nodesA", "nodesB", "click"]}
    t0 = time.perf_counter()
    clicked = False
    click_t = None
    while True:
        t = time.perf_counter() - t0
        if not clicked and t >= click_at:
            u32.mouse_event(LEFTDOWN, 0, 0, 0, 0)
            u32.mouse_event(LEFTUP, 0, 0, 0, 0)
            click_t = t
            clicked = True
        frame = fm.u32(W.A_FRAME)
        a7 = fm.u32(0xA8E7AC)
        a9 = fm.u8(0xA8E9A0)
        # cell chains
        if cell:
            hA = fm.u32(cell + 0xE4)
            hB = fm.u32(cell + 0xE8)
        else:
            hA = hB = None
        def walk(head, maxn=12):
            nodes = []
            seen = set()
            p = head
            while p and len(nodes) < maxn and dok(p):
                if p in seen:
                    nodes.append({"this": hex(p), "rtti": "[CYCLE]"})
                    break
                seen.add(p)
                nm, vp, col, td = rtti(fm, p)
                nodes.append({"this": hex(p), "vptr": hex(vp) if vp else None,
                              "rtti": nm if nm else "[未证]",
                              "layer94": W.s32 if False else None})
                p = fm.u32(p + 0x30)
            return nodes
        nodesA = walk(hA)
        nodesB = walk(hB)
        rows.append([round(t, 6), frame, a7, a9,
                     hex(hA) if hA else None, hex(hB) if hB else None,
                     len(nodesA), len(nodesB), nodesA, nodesB,
                     1 if (click_t is not None and abs(t - click_t) < 0.001) else 0])
        if t >= dur:
            break
    wall = time.perf_counter() - t0
    meta["n"] = len(rows)
    meta["wall_s"] = wall
    meta["rate_per_s"] = len(rows) / wall
    meta["click_t"] = click_t

    out = os.path.join(EVID, tag + ".jsonl")
    with open(out, "w", encoding="utf-8") as f:
        f.write(json.dumps(meta, ensure_ascii=False) + "\n")
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("SAVED", out)
    print("n=%d wall=%.3fs rate=%.0f/s click_t=%s" % (len(rows), wall, len(rows)/wall, click_t))
    # 关键摘要：click 前后各 5 帧 + 链长/RTTI 变化
    print("--- around click ---")
    ci = min(range(len(rows)), key=lambda i: abs(rows[i][0] - (click_t or 0)))
    for r in rows[max(0,ci-4):ci+6]:
        print("t=%.4f frame=%s a7=%s a9=%s lenA=%d lenB=%d A=%s B=%s" % (
            r[0], r[1], r[2], r[3], r[6], r[7],
            [n["rtti"].replace(".?AV","").replace("@@","") for n in r[8]],
            [n["rtti"].replace(".?AV","").replace("@@","") for n in r[9]]))
    m.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
