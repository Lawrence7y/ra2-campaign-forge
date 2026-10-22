#!/usr/bin/env python
"""待办 6 · RC4_RECONCILE：从进程级 dump 反推崩溃线程的**完整**栈。

★ 为什么要做
  §361/§369 只定谳了**五环**（崩溃点 → One_Time）。但待办 6 的四个问题需要
  **线程级的完整因果**：
    Q1 One_Time（0x652CF0）的全部调用者与运行时机
    Q2 退出期析构链里是否会调到它
    Q3 [0x887368] 清零（0x777803）与 One_Time 谁先谁后
    Q4 H1（退出期析构 / atexit 序列）/ H2（加载未完成时 WM_CLOSE）/ H3（其他）
  dump 里有**整个线程栈**（不是游戏自己截断的 40 行），可以直接把五环之外
  的祖先帧全部读出来，并判定线程起点是不是 WndProc。

★ 方法（全部可证伪）
  1. 从 ThreadList 找 `Exception` 流里记录的崩溃线程（或按栈内容匹配）；
  2. 沿 `[esp]` 链走：每个 4 字节值 V，若 `V-5` 处是 `E8 rel32` 且目标落在
     `.text` 内 ⇒ V 是某帧的返回地址 ⇒ 前进到 `[esp+4k]` 继续；
  3. 对每个候选返回地址，反查它属于哪个函数（用 §346/§361 已定的函数表 + 邻近）；
  4. 判定是否出现 `0x7775C0`（WndProc）的返回地址 ⇒ 线程是否从窗口消息进来。

★ 判据
  R1  崩溃线程可定位（Exception 流 or 栈匹配）
  R2  五环全中（与 §369 一致）
  R3  至少再读出 1 个五环之上的祖先帧
  R4  判定该祖先帧是否 = WndProc 路径（0x7775C0 家族）
  R5  报告 `[0x887368]` 在崩溃瞬间的值（应为 0）
  R6  报告线程栈上是否出现 `0x777803` 之后才会有的标记

★ 用法
  python _rc4_reconcile.py
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
CARD = ROOT / "lead" / "goal2_rc4_trigger_20261022"
DUMP_DIR = Path(r"D:\ra2dumps")
GAMEMD = ROOT / "ra2youli/gamemd.exe"

IMAGE_BASE = 0x00400000
# .text 段（由 §342/§369 的模块记录：base 0x400000 size 0x796000）
TEXT_LO = 0x00401000
TEXT_HI = 0x00B96000

# §361/§369 已定谳的五环
FRAMES = [
    (0x00920358, 0x00654418, "0x724730 ← 0x654413"),
    (0x00920388, 0x006403A8, "0x654320 ← 0x6403A3"),
    (0x009203AC, 0x006ABD3E, "0x6403A0 ← 0x6ABD39"),
    (0x009203E4, 0x004A8B18, "0x6ABD30 ← 0x4A8B13"),
    (0x0092043C, 0x00652D51, "0x4A8850 ← 0x652D4C"),
]
REAL_STACK = 0x00920300

# 已知函数边界（来自 §342/§349/§361/§369 的定谳）
KNOWN_FUNCS = {
    0x007775C0: "WndProc(\"Yuri's Revenge\")",
    0x00777A80: "WndProc 消息跳表基",
    0x00652CF0: "RadarClass::One_Time()",
    0x00724730: "崩溃函数（本卡 FN_A）",
    0x00724580: "崩溃函数姊妹（同 Access=0x250）",
    0x00654320: "宿主 0x654320",
    0x006403A0: "宿主 0x6403A0",
    0x006ABD30: "宿主 0x6ABD30",
    0x004A8960: "L3 视口矩形重设（v[42]）",
    0x004A8850: "L3 内层 0x4A8850",
    0x006BE0CF: "引擎退出路径（PostMessageA WM_DESTROY）",
    0x006BE0DC: "引擎退出等待环",
    0x005D4D50: "消息泵",
    0x00720770: "0x720770（退出序列调用）",
    0x00406D40: "0x406D40（退出序列调用）",
}

CHECKS = []


def chk(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print("  [%s] %-56s %s" % ("PASS" if ok else "FAIL", name, detail))


# ---------------------------------------------------------------------------
# PE：读 .text 原始字节用于 E8 反查
# ---------------------------------------------------------------------------
def load_text() -> tuple[bytes, int, int]:
    b = GAMEMD.read_bytes()
    e_lfanew = struct.unpack("<I", b[0x3C:0x40])[0]
    nsec = struct.unpack("<H", b[e_lfanew + 6:e_lfanew + 8])[0]
    optsz = struct.unpack("<H", b[e_lfanew + 0x14:e_lfanew + 0x16])[0]
    opt = e_lfanew + 0x18
    image_base = struct.unpack("<I", b[opt + 0x1C:opt + 0x20])[0]
    sec = opt + optsz
    for i in range(nsec):
        o = sec + i * 40
        name = b[o:o + 8].rstrip(b"\0").decode("latin1")
        if name != ".text":
            continue
        vsize = struct.unpack("<I", b[o + 8:o + 12])[0]
        va = struct.unpack("<I", b[o + 12:o + 16])[0]
        rawsz = struct.unpack("<I", b[o + 16:o + 20])[0]
        rawptr = struct.unpack("<I", b[o + 20:o + 24])[0]
        return b[rawptr:rawptr + min(vsize, rawsz)], image_base + va, vsize
    raise RuntimeError(".text not found")


class Text:
    def __init__(self):
        self.data, self.va, self.size = load_text()
        self.image_base = IMAGE_BASE

    def bytes_at(self, va: int, n: int):
        off = va - self.va
        if off < 0 or off + n > len(self.data):
            return None
        return self.data[off:off + n]

    def is_e8_call_to_text(self, insn_va: int):
        """若 insn_va 处是 `E8 rel32` 且目标在 .text 内 ⇒ 返回目标，否则 None。"""
        raw = self.bytes_at(insn_va, 5)
        if raw is None or raw[0] != 0xE8:
            return None
        rel = struct.unpack("<i", raw[1:5])[0]
        tgt = insn_va + 5 + rel
        if TEXT_LO <= tgt < TEXT_HI:
            return tgt
        return None


# ---------------------------------------------------------------------------
# dump 读取
# ---------------------------------------------------------------------------
class Dump:
    def __init__(self, path: Path):
        self.path = path
        self.f = open(path, "rb")
        hdr = self.f.read(32)
        sig, ver, ns, dir_rva, ck, ts, flags = struct.unpack("<IIIIIIQ", hdr)
        if sig != 0x504D444D:
            raise ValueError("bad MDMP signature %08X" % sig)
        self.f.seek(dir_rva)
        self.dirs = {}
        for _ in range(ns):
            t, sz, r = struct.unpack("<III", self.f.read(12))
            if t:
                self.dirs[t] = (sz, r)
        msz, mrva = self.dirs[9]
        self.f.seek(mrva)
        nr = struct.unpack("<Q", self.f.read(8))[0]
        self.base_rva = struct.unpack("<Q", self.f.read(8))[0]
        self.ranges = [struct.unpack("<QQ", self.f.read(16))
                       for _ in range(nr)]
        self.first_start = self.ranges[0][0]

    def read_va(self, va: int, n: int):
        for start, rsize in self.ranges:
            if start <= va and va + n <= start + rsize:
                self.f.seek(self.base_rva + (va - self.first_start))
                return self.f.read(n)
        return None

    def u32(self, va: int):
        raw = self.read_va(va, 4)
        return struct.unpack("<I", raw)[0] if raw else None

    def threads(self):
        """返回 [(tid, rsp, stack_start, stack_size, teb)]"""
        if 3 not in self.dirs:
            return []
        sz, rva = self.dirs[3]
        self.f.seek(rva)
        n = struct.unpack("<I", self.f.read(4))[0]
        out = []
        for _ in range(n):
            rec = self.f.read(48)
            if len(rec) < 48:
                break
            tid = struct.unpack("<I", rec[0:4])[0]
            teb = struct.unpack("<Q", rec[16:24])[0]
            start = struct.unpack("<Q", rec[24:32])[0]
            ssz = struct.unpack("<I", rec[32:36])[0]
            rsp = struct.unpack("<Q", rec[48 - 24:48 - 16])[0]
            out.append((tid, rsp, start, ssz, teb))
        return out

    def exception_thread(self):
        """EXCEPTION 流里的线程 id 与异常地址（若无该流返回 None）。"""
        if 6 not in self.dirs:
            return None
        sz, rva = self.dirs[6]
        self.f.seek(rva)
        blob = self.f.read(sz)
        if len(blob) < 168:
            return None
        tid = struct.unpack("<I", blob[0:4])[0]
        code = struct.unpack("<I", blob[8:12])[0]
        addr = struct.unpack("<Q", blob[24:32])[0]
        return {"thread": tid, "code": code, "address": addr}

    def close(self):
        self.f.close()


# ---------------------------------------------------------------------------
# 栈走查
# ---------------------------------------------------------------------------
def walk_stack(d: Dump, rsp: int, text: Text, max_frames=40):
    """沿栈找「返回地址」候选：值 V 满足 V-5 处是 E8 → .text。

    ★ 这是 §361 用过的同一判据（`V-5` 是 `E8 rel32` 且目标在 .text 内）。
      推广到整条栈，可读出五环之外的祖先帧。
    """
    frames = []
    seen = set()
    # 在 [rsp, rsp+0x4000) 内扫
    for off in range(0, 0x4000, 4):
        va = rsp + off
        v = d.u32(va)
        if v is None:
            break
        if not (TEXT_LO <= v < TEXT_HI):
            continue
        if v in seen:
            continue
        tgt = text.is_e8_call_to_text(v - 5)
        if tgt is None:
            continue
        seen.add(v)
        frames.append({"slot": va, "retaddr": v, "call_insn": v - 5,
                       "callee": tgt})
        if len(frames) >= max_frames:
            break
    return frames


def nearest_known(va: int, limit=0x400):
    """若 va 落在已知函数头 +limit 内，返回函数名。"""
    best = None
    for fva, name in KNOWN_FUNCS.items():
        if 0 <= va - fva < limit:
            if best is None or (va - fva) < (va - best[0]):
                best = (fva, name)
    return best


def main() -> int:
    print("=" * 78)
    print("待办 6 · RC4_RECONCILE：崩溃线程完整栈反推")
    print("=" * 78)

    dumps = sorted(DUMP_DIR.glob("rc4dbg_*.dmp"))
    print("发现 %d 份 debugger 版 dump" % len(dumps))
    if not dumps:
        print("!! 无 dump")
        return 2

    text = Text()
    print("gamemd .text: VA=%08X size=%X image_base=%08X"
          % (text.va, text.size, text.image_base))
    print()

    reports = []
    for dp in dumps:
        print("=" * 78)
        print("dump:", dp.name, "(%.1f MB)" % (dp.stat().st_size / 1048576))
        d = Dump(dp)
        try:
            # ---- R1：定位崩溃线程 ----
            ex = d.exception_thread()
            ths = d.threads()
            print("  threads=%d  exception_stream=%s"
                  % (len(ths), ex))
            # 崩溃线程：栈区间覆盖 REAL_STACK 的那条
            crash_th = None
            for tid, rsp, start, ssz, teb in ths:
                if start <= REAL_STACK < start + ssz:
                    crash_th = (tid, rsp, start, ssz)
                    break
            chk("R1 %s 崩溃线程可定位（栈区间覆盖 0x920300）"
                % dp.name, crash_th is not None,
                "tid=%s rsp=%s" % (crash_th[0], hex(crash_th[1]))
                if crash_th else "not found")

            # ---- R2：五环 ----
            ok5 = True
            for va, want, lbl in FRAMES:
                v = d.u32(va)
                if v != want:
                    ok5 = False
                    print("      MISMATCH %s: got %s want %08X"
                          % (lbl, ("%08X" % v) if v else "NONE", want))
            chk("R2 %s 五环全中" % dp.name, ok5)

            # ---- R3：五环之上还有祖先帧 ----
            rsp = crash_th[1] if crash_th else REAL_STACK
            frames = walk_stack(d, rsp, text)
            print("  栈走查：从 rsp=%08X 起，找到 %d 个返回地址候选"
                  % (rsp, len(frames)))
            above = [f for f in frames if f["slot"] >= 0x00920440]
            chk("R3 %s 五环之上至少 1 个祖先帧" % dp.name, len(above) >= 1,
                "%d 个" % len(above))

            print("  完整帧表（前 24 条）：")
            for f in frames[:24]:
                kn = nearest_known(f["callee"], 0x2000)
                mark = ""
                if kn:
                    mark = "  ★ %s+0x%X" % (kn[1], f["callee"] - kn[0])
                print("    slot=%08X  ret=%08X  call@%08X -> callee=%08X%s"
                      % (f["slot"], f["retaddr"], f["call_insn"],
                         f["callee"], mark))

            # ---- R4：是否 WndProc 路径 ----
            wnd_ret = 0x007775C0
            is_wnd = any(f["callee"] == wnd_ret for f in frames) or \
                any(0x007775C0 <= f["callee"] < 0x00777D00 for f in frames)
            chk("R4 %s 祖先帧是否 WndProc 路径" % dp.name, True,
                "WndProc=%s" % is_wnd)

            # ---- R5：singleton ----
            sing = d.u32(0x00887368)
            chk("R5 %s 崩溃瞬间 [0x887368] == 0" % dp.name, sing == 0,
                "got %s" % (("0x%X" % sing) if sing is not None else "NONE"))

            # ---- R6：栈上是否出现退出路径标记 ----
            markers = {
                0x006BE0CF: "引擎退出路径",
                0x006BE0DC: "退出等待环",
                0x005D4D50: "消息泵",
                0x00777A80: "WndProc 跳表基",
            }
            hits = {}
            for va, lbl in markers.items():
                # 找该地址 ±0x40 内的返回地址
                got = [f for f in frames
                       if va <= f["retaddr"] <= va + 0x40
                       or va <= f["callee"] <= va + 0x40]
                if got:
                    hits[lbl] = [hex(f["retaddr"]) for f in got]
            print("  退出路径标记命中：", hits if hits else "无")

            reports.append({"dump": dp.name, "threads": len(ths),
                            "exception": ex, "crash_thread": crash_th,
                            "frames": frames, "singleton": sing,
                            "markers": hits, "is_wndproc": is_wnd})
        finally:
            d.close()

    print()
    n = len(CHECKS)
    ok = sum(1 for _, v, _ in CHECKS if v)
    print("-" * 78)
    print("结果：%d/%d PASS" % (ok, n))

    out = CARD / "RC4_RECONCILE_STACKS.json"
    out.write_text(json.dumps(reports, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("明细:", out)
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
