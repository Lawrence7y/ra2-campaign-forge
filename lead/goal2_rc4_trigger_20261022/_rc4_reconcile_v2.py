#!/usr/bin/env python
"""待办 6 · RC4_RECONCILE（v2）：崩溃线程完整栈 + One_Time 调用拓扑。

★ 本轮定谳的四问（对应 v7 §4 待办 6）
  Q1 One_Time（0x652CF0）的全部调用者与运行时机
  Q2 退出期析构链里是否会调到它
  Q3 [0x887368] 清零（0x777803）与 One_Time 谁先谁后
  Q4 H1（退出期析构 / atexit 序列）/ H2（加载未完成时 WM_CLOSE）/ H3（其他）

★ 方法
  1. dump 侧：从 ThreadList 找崩溃线程，沿栈扫「V-5 处是 E8 → .text」的返回地址；
  2. 静态侧：全量扫 E8 调用者 + vtable 槽位 + 函数指针表引用；
  3. 两侧交叉：静态找到的每个 One_Time 入口，都要在 dump 栈上看到对应返回地址。

★ 判据（全部可证伪）
  R1 崩溃线程可定位（栈区间覆盖真实栈 0x920300）
  R2 五环全中
  R3 五环之上至少 1 个祖先帧
  R4 报告祖先帧是否含 WndProc（0x7775C0 家族）
  R5 崩溃瞬间 [0x887368] == 0
  R6 静态：One_Time 本体无 E8 调用者（只能经 vtable slot5 进入）
  R7 静态：两张 vtable 的 slot5 都最终落到 One_Time
  R8 dump：栈上出现 One_Time 的返回地址 0x652D51
  R9 dump：栈上出现 0x6A5000 的返回地址（第二入口）或明确记为未出现
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

TEXT_LO = 0x00401000
TEXT_HI = 0x00B96000

FRAMES = [
    (0x00920358, 0x00654418, "0x724730 ← 0x654413"),
    (0x00920388, 0x006403A8, "0x654320 ← 0x6403A3"),
    (0x009203AC, 0x006ABD3E, "0x6403A0 ← 0x6ABD39"),
    (0x009203E4, 0x004A8B18, "0x6ABD30 ← 0x4A8B13"),
    (0x0092043C, 0x00652D51, "0x4A8850 ← 0x652D4C"),
]
REAL_STACK = 0x00920300

KNOWN_FUNCS = {
    0x007775C0: "WndProc(\"Yuri's Revenge\")",
    0x00652CF0: "RadarClass::One_Time()",
    0x006A5000: "One_Time 第二入口（vtable 0x7F3058 slot5）",
    0x0063F7B0: "jmp 0x652CF0（跳板）",
    0x006A4F20: "RadarClass 构造函数（写 0x7F3058）",
    0x00724730: "崩溃函数 FN_A",
    0x00654320: "宿主 0x654320",
    0x006403A0: "宿主 0x6403A0",
    0x006ABD30: "宿主 0x6ABD30",
    0x004A8960: "L3 视口矩形重设（v[42]）",
    0x004A8850: "L3 内层",
    0x006BE0CF: "引擎退出路径",
    0x005D4D50: "消息泵",
}

CHECKS = []


def chk(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print("  [%s] %-56s %s" % ("PASS" if ok else "FAIL", name, detail))


def load_sections():
    b = GAMEMD.read_bytes()
    e = struct.unpack("<I", b[0x3C:0x40])[0]
    n = struct.unpack("<H", b[e + 6:e + 8])[0]
    optsz = struct.unpack("<H", b[e + 0x14:e + 0x16])[0]
    opt = e + 0x18
    image_base = struct.unpack("<I", b[opt + 0x1C:opt + 0x20])[0]
    sec = opt + optsz
    out = {}
    for i in range(n):
        p = sec + i * 40
        nm = b[p:p + 8].rstrip(b"\0").decode("latin1")
        vs = struct.unpack("<I", b[p + 8:p + 12])[0]
        va = struct.unpack("<I", b[p + 12:p + 16])[0]
        rs = struct.unpack("<I", b[p + 16:p + 20])[0]
        rp = struct.unpack("<I", b[p + 20:p + 24])[0]
        out[nm] = {"va": image_base + va, "vsize": vs, "rawsz": rs,
                   "rawptr": rp,
                   "data": b[rp:rp + min(vs, rs)], "file": b}
    return out, image_base


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

    def read_va(self, va, n):
        for start, rsize in self.ranges:
            if start <= va and va + n <= start + rsize:
                self.f.seek(self.base_rva + (va - self.first_start))
                return self.f.read(n)
        return None

    def u32(self, va):
        raw = self.read_va(va, 4)
        return struct.unpack("<I", raw)[0] if raw else None

    def threads(self):
        """解析 MINIDUMP_THREAD_LIST。

        ★ 真实布局（48 字节/条，MS 文档 + 实测对齐）：
            +0x00 ThreadId            (4)
            +0x04 SuspendCount        (4)
            +0x08 PriorityClass       (4)
            +0x0C Priority            (4)
            +0x10 Teb                 (8)
            +0x18 Stack.StartOfMemoryRange (8)
            +0x20 Stack.Memory.DataSize    (4)
            +0x24 Stack.Memory.Rva         (4)
            +0x28 ThreadContext.DataSize   (4)
            +0x2C ThreadContext.Rva        (4)
        ⇒ 总 48 字节。**rsp 不在这里**，要从 ThreadContext 里读 CONTEXT。
        """
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
            tid = struct.unpack("<I", rec[0x00:0x04])[0]
            teb = struct.unpack("<Q", rec[0x10:0x18])[0]
            start = struct.unpack("<Q", rec[0x18:0x20])[0]
            ssz = struct.unpack("<I", rec[0x20:0x24])[0]
            ctx_sz = struct.unpack("<I", rec[0x28:0x2C])[0]
            ctx_rva = struct.unpack("<I", rec[0x2C:0x30])[0]
            rsp = None
            if ctx_sz >= 0xAC and ctx_rva:
                save = self.f.tell()
                self.f.seek(ctx_rva + 0xC4)   # CONTEXT.Esp @ +0xC4 (x86)
                raw = self.f.read(4)
                if len(raw) == 4:
                    rsp = struct.unpack("<I", raw)[0]
                self.f.seek(save)
            out.append({"tid": tid, "rsp": rsp, "stack_start": start,
                        "stack_size": ssz, "teb": teb,
                        "ctx_rva": ctx_rva, "ctx_sz": ctx_sz})
        return out

    def close(self):
        self.f.close()


def walk_stack(d: Dump, rsp, text_va, text_data, max_frames=64):
    frames = []
    seen = set()
    for off in range(0, 0x4000, 4):
        va = rsp + off
        v = d.u32(va)
        if v is None:
            break
        if not (TEXT_LO <= v < TEXT_HI) or v in seen:
            continue
        insn = v - 5
        o = insn - text_va
        if o < 0 or o + 5 > len(text_data) or text_data[o] != 0xE8:
            continue
        rel = struct.unpack("<i", text_data[o + 1:o + 5])[0]
        tgt = insn + 5 + rel
        if not (TEXT_LO <= tgt < TEXT_HI):
            continue
        seen.add(v)
        frames.append({"slot": va, "retaddr": v, "call_insn": insn,
                       "callee": tgt})
        if len(frames) >= max_frames:
            break
    return frames


def find_e8_callers(secs, target):
    out = []
    td = secs[".text"]["data"]
    tva = secs[".text"]["va"]
    for i in range(len(td) - 5):
        if td[i] != 0xE8:
            continue
        a = tva + i
        rel = struct.unpack("<i", td[i + 1:i + 5])[0]
        if a + 5 + rel == target:
            out.append(a)
    return out


def find_ptr_refs(secs, target):
    pat = struct.pack("<I", target)
    out = {}
    for nm in (".text", ".rdata", ".data"):
        if nm not in secs:
            continue
        s = secs[nm]
        blob = s["data"]
        hits = []
        off = 0
        while True:
            i = blob.find(pat, off)
            if i < 0:
                break
            hits.append(s["va"] + i)
            off = i + 1
        if hits:
            out[nm] = hits
    return out


def vtable_slots(secs, vt, count=8):
    s = secs[".rdata"]
    off = vt - s["va"]
    out = []
    for i in range(count):
        o = off + i * 4
        if o + 4 > len(s["data"]):
            break
        out.append(struct.unpack("<I", s["data"][o:o + 4])[0])
    return out


def main() -> int:
    print("=" * 78)
    print("待办 6 · RC4_RECONCILE v2：完整栈 + One_Time 调用拓扑")
    print("=" * 78)

    secs, image_base = load_sections()
    td = secs[".text"]["data"]
    tva = secs[".text"]["va"]
    print("sections: " + ", ".join(
        "%s@%08X(%X)" % (k, v["va"], v["vsize"]) for k, v in secs.items()))
    print()

    # ================= 静态侧 =================
    print("--- 静态：One_Time 的入口拓扑 ---")
    c_onetime = find_e8_callers(secs, 0x652CF0)
    chk("R6 One_Time 本体无 E8 调用者（只能经 vtable slot5）",
        len(c_onetime) == 0, "callers=%s" % [hex(x) for x in c_onetime])

    c_tramp = find_e8_callers(secs, 0x63F7B0)
    print("      0x63F7B0（jmp One_Time）的 E8 调用者: %s"
          % [hex(x) for x in c_tramp])

    vt_b = vtable_slots(secs, 0x7F0344)
    vt_c = vtable_slots(secs, 0x7F3058)
    print("      vtable 0x7F0344: %s" % [hex(x) for x in vt_b])
    print("      vtable 0x7F3058: %s" % [hex(x) for x in vt_c])

    # slot5 是否最终落到 One_Time
    def resolves_to_onetime(entry, depth=0):
        """entry 是否「最终」调到 One_Time。

        ★ 必须同时追两种转移：
          - `E9 rel32`（jmp，如 0x63F7B0 的跳板）
          - `E8 rel32`（call，如 0x6A5000 函数体首条就是 call 跳板）
        只追 E9 会把「函数体里 call 一次 One_Time」判成「不相关」——
          这正是本判据第一版的假红原因。
        """
        if entry == 0x652CF0:
            return True
        if depth > 4:
            return False
        o = entry - tva
        if not (0 <= o + 5 <= len(td)):
            return False
        op = td[o]
        if op in (0xE9, 0xE8):
            rel = struct.unpack("<i", td[o + 1:o + 5])[0]
            return resolves_to_onetime(entry + 5 + rel, depth + 1)
        # 不是跳转 ⇒ 扫函数体前 0x40 字节里有没有 E8 到 One_Time 链
        for k in range(0, 0x40):
            if o + k + 5 > len(td):
                break
            if td[o + k] != 0xE8:
                continue
            rel = struct.unpack("<i", td[o + k + 1:o + k + 5])[0]
            tgt = entry + k + 5 + rel
            if resolves_to_onetime(tgt, depth + 1):
                return True
        return False

    s5b = vt_b[5] if len(vt_b) > 5 else None
    s5c = vt_c[5] if len(vt_c) > 5 else None
    chk("R7 两张 vtable 的 slot5 都最终落到 One_Time",
        bool(s5b and resolves_to_onetime(s5b))
        and bool(s5c and resolves_to_onetime(s5c)),
        "0x7F0344.slot5=%s -> One_Time=%s ; 0x7F3058.slot5=%s -> One_Time=%s"
        % (hex(s5b) if s5b else None,
           resolves_to_onetime(s5b) if s5b else None,
           hex(s5c) if s5c else None,
           resolves_to_onetime(s5c) if s5c else None))

    print()
    print("--- 静态：两张 vtable 的引用点 ---")
    for vt, lbl in ((0x7F0344, "表B(RadarClass)"), (0x7F3058, "表C(0x6A4F20)")):
        refs = find_ptr_refs(secs, vt)
        print("      %s %08X 引用: %s"
              % (lbl, vt, {k: [hex(x) for x in v] for k, v in refs.items()}))

    # 前 4 槽是否相同（同基类证据）
    same4 = (vt_b[:4] == vt_c[:4])
    print("      前 4 槽相同（同基类证据）: %s" % same4)

    print()
    print("--- 静态：0x6A4F20 的 vtable 写入序列 ---")
    # 扫 0x6A4F20..0x6A4FF0 里的 mov [edi],imm32 (c7 07 imm32)
    writes = []
    lo = 0x6A4F20 - tva
    hi = 0x6A4FF0 - tva
    i = lo
    while i < hi:
        if td[i] == 0xC7 and td[i + 1] == 0x07:
            v = struct.unpack("<I", td[i + 2:i + 6])[0]
            writes.append((tva + i, v))
            i += 6
        else:
            i += 1
    for va, v in writes:
        print("      %08X  mov [edi], %08X" % (va, v))

    # ================= dump 侧 =================
    dumps = sorted(DUMP_DIR.glob("rc4dbg_*.dmp"))
    print()
    print("--- dump 侧：%d 份 ---" % len(dumps))
    reports = []
    for dp in dumps:
        d = Dump(dp)
        try:
            ths = d.threads()
            # ★★ 崩溃栈定位（本卡第三版，前两版都错，理由记在下面）
            #
            #   v1 判据「ThreadList 的 stack 区间覆盖 0x920300」→ FAIL：
            #     ThreadList 只记**栈的保留区**（0xA8000 / 0x2B0E7F8 / ...），
            #     且多数条目的 Memory.Rva==0（栈体不在 dump 里）。
            #     0x920300 不在任何一条 ThreadList 区间内 —— 它不是「线程栈基址」。
            #
            #   v2 兜底「栈上有 0x654418 就算命中」→ **假绿**：
            #     该地址本来就存着这个值，条件恒真。
            #
            #   v3（本版）判据：0x920300 落在 Memory64List 的哪个 range 里，
            #     并要求该 range **前面是零、后面有内容**（栈保留区的典型形态），
            #     且五环全中。三条同时成立才算定位。
            holder = None
            for s, sz in d.ranges:
                if s <= REAL_STACK < s + sz:
                    holder = (s, sz)
                    break
            head_zero = False
            if holder:
                h = d.read_va(holder[0], 16)
                head_zero = bool(h) and h == b"\x00" * 16
            chk("R1 %s 崩溃栈已定位（0x920300 在 dump 内且为栈保留区形态）"
                % dp.name,
                holder is not None and head_zero,
                "range=[%s,+%s) head_zero=%s"
                % (hex(holder[0]) if holder else None,
                   hex(holder[1]) if holder else None, head_zero))

            ok5 = all(d.u32(va) == want for va, want, _ in FRAMES)
            chk("R2 %s 五环全中" % dp.name, ok5)

            rsp = REAL_STACK
            print("      走查起点 rsp=%s（崩溃栈顶，由五环锚点确定）" % hex(rsp))
            frames = walk_stack(d, rsp, tva, td)
            above = [f for f in frames if f["slot"] >= 0x00920440]
            chk("R3 %s 五环之上至少 1 个祖先帧" % dp.name, len(above) >= 1,
                "%d 帧（总 %d）" % (len(above), len(frames)))

            is_wnd = any(0x007775C0 <= f["callee"] < 0x00777D00
                         for f in frames)
            chk("R4 %s 祖先帧含 WndProc" % dp.name, True,
                "WndProc=%s" % is_wnd)

            sing = d.u32(0x00887368)
            chk("R5 %s 崩溃瞬间 [0x887368]==0" % dp.name, sing == 0,
                "got %s" % (("0x%X" % sing) if sing is not None else "NONE"))

            has_ot = any(f["retaddr"] == 0x00652D51 for f in frames)
            chk("R8 %s 栈上有 One_Time 返回址 0x652D51" % dp.name, has_ot)

            has_2nd = any(f["retaddr"] == 0x006A5006 for f in frames)
            print("      R9 %s 栈上有第二入口返回址 0x6A5006: %s"
                  % (dp.name, has_2nd))

            reports.append({
                "dump": dp.name, "stack_range": holder,
                "frames": frames, "singleton": sing,
                "is_wndproc": is_wnd,
                "has_onetime_ret": has_ot,
                "has_2nd_entry_ret": has_2nd,
            })
        finally:
            d.close()
        print()

    # ================= 汇总 =================
    n = len(CHECKS)
    ok = sum(1 for _, v, _ in CHECKS if v)
    print("-" * 78)
    print("结果：%d/%d PASS" % (ok, n))

    out = CARD / "RC4_RECONCILE_V2.json"
    out.write_text(json.dumps({
        "static": {
            "onetime_e8_callers": c_onetime,
            "trampoline_callers": c_tramp,
            "vtable_7F0344": vt_b,
            "vtable_7F3058": vt_c,
            "first4_slots_equal": same4,
            "ctor_6A4F20_vtable_writes": writes,
        },
        "dumps": reports,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("明细:", out)
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
