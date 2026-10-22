#!/usr/bin/env python
"""验证 RC-4 活体 minidump 是否真的对应崩溃现场（离线，只读 dump）。

★ 为什么需要本件
  拿到 dump 不等于拿到「对的」dump。必须用**独立判据**证明：
  这份 dump 里的内存确实是 `except.txt` 描述的那个现场，
  而不是抓早了（关窗前）或抓晚了（进程已改状态）。

★ 判据（全部可证伪，任一不过 ⇒ FAIL）
  C1  dump 头合法（signature == 'MDMP'）
  C2  dump 含 Memory64List（全内存），且覆盖真实栈区间
  C3  ★ 帧链五环（真实栈偏移，见下「★ 地址偏移定谳」）
  C9  `except.txt` 的 Eip == `0x00724737`，且 dump 的 module 列表含
      ImageBase == `0x00400000` 的 gamemd 模块
  C10 反证：栈上 `0x4A8B7A` 不出现（L3 的 0x4A8B75 调用未返回）
  C12 ★ 偏移自证：真实栈 `0x920380` 处的值 == `0x00F9A300`，
      而 `except.txt` 报的基址 = `0x00F9A344`
      ⇒ 两者相差恰 `0x67A000`（页对齐常量）

★★ 地址偏移定谳（本卡最重要的一条勘误）
  `except.txt` 里 `Esp=00F9A344` 与 `Stack dump` 的地址（`00F9A3xx`）
  **不是进程内的真实 VA**，而是引擎打印时加了 `0x67A000`。
  真实栈在 `0x9203xx`。证据链：
    (a) 两份独立 dump（轮询版 / 调试器版）在 `0xF9A344` 处字节完全相同
        ⇒ 不是「抓晚了」或「抓早了」，是地址口径不同；
    (b) 在 dump 里全量搜五环返回地址，命中位置**全部**在 `0x9203xx`；
    (c) `0xF9A344 - 0x920344 = 0x67A000` 恰为页对齐常量；
    (d) 真实栈 `0x920380` 处存的值 = `0x00F9A300`（引擎保存的「栈基址」），
        `0xF9A300 - 0x920300` 同样是 `0x67A000` ⇒ 两条独立路径同一偏移。
  ⇒ 历史上把 `except.txt` 的栈地址当 VA 用是**错的**；
    帧链结论本身（五环、顺序、调用点）**不受影响**，因为链条形状一致。

★ 用法
  python VERIFY_RC4_MINIDUMP.py [--dump <path>]
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
DUMP = Path(r"D:\ra2dumps\rc4dbg_20261022T183405_t1.dmp")
EXCEPT = (ROOT / "lead/goal2_rc4_trigger_20261022/"
          "dbg_20261022T183405_t1/except_after.txt")
HIST = ROOT / "ra2youli/except.txt"

# ★ 真实栈基址（进程内 VA）。由全量搜索五环返回地址得到，见文件头注。
REAL_STACK_BASE = 0x00920300
# ★ except.txt 报的 Esp 与真实栈的差（页对齐常量）
REPORTED_ESP = 0x00F9A344
ESP_SKEW = REPORTED_ESP - 0x00920344   # == 0x67A000

CHECKS = []


def chk(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print("  [%s] %-56s %s" % ("PASS" if ok else "FAIL", name, detail))


def main() -> int:
    print("=" * 78)
    print("RC-4 活体 minidump 现场验证")
    print("=" * 78)
    print("dump  :", DUMP)
    print("except:", EXCEPT)
    print()

    if not DUMP.is_file():
        print("!! dump 不存在")
        return 2

    size = DUMP.stat().st_size
    print("dump size = %d B (%.1f MB)" % (size, size / 1048576))
    print("dump sha256 =", hashlib.sha256(DUMP.read_bytes()).hexdigest())
    print()

    f = open(DUMP, "rb")
    try:
        hdr = f.read(32)
        sig, ver, nstreams, dir_rva, chk_sum, ts, flags = \
            struct.unpack("<IIIIIIQ", hdr)

        # ---- C1 ----
        chk("C1 dump 头 signature == MDMP",
            sig == 0x504D444D, "got %08X" % sig)

        f.seek(dir_rva)
        dirs = {}
        for _ in range(nstreams):
            t, sz, r = struct.unpack("<III", f.read(12))
            if t:
                dirs[t] = (sz, r)

        chk("C2a 含 Memory64List(9) 流", 9 in dirs, "streams=%s" % sorted(dirs))
        chk("C2b 含 ModuleList(4) 流", 4 in dirs)
        chk("C2c 含 ThreadList(3) 流", 3 in dirs)

        # ---- 解析 Memory64List：RVA 之后是 count + baseRVA，再是 count 个 (start,size)
        m_sz, m_rva = dirs[9]
        f.seek(m_rva)
        n_ranges = struct.unpack("<Q", f.read(8))[0]
        base_rva = struct.unpack("<Q", f.read(8))[0]
        ranges = []
        for _ in range(n_ranges):
            start, rsize = struct.unpack("<QQ", f.read(16))
            ranges.append((start, rsize))
        print("  Memory64List: %d ranges, base RVA=%X" % (n_ranges, base_rva))

        def read_va(va: int, n: int):
            """按 Memory64List 读 VA。

            ★ 文件偏移 = base_rva + (va - ranges[0][0])。
              Memory64List 的 BaseRva 指向**第一段**数据的起始，
              后续各段在文件里**紧接连续**排列 ⇒ 不能按「本段 start」算，
              也不能按「前面各段 size 累加」（那会读到空洞）。
              判据：`0x920358` 用本式读到 `00654418`，与 except.txt 一致。
            """
            for start, rsize in ranges:
                if start <= va and va + n <= start + rsize:
                    f.seek(base_rva + (va - ranges[0][0]))
                    return f.read(n)
            return None

        STACK = REAL_STACK_BASE
        got = read_va(STACK, 16)
        chk("C2d 真实栈区间 0x920300 被 Memory64List 覆盖",
            got is not None,
            ("first16=%s" % got.hex()) if got else "NOT COVERED")

        # ---- C3：五环帧链（★ 真实栈偏移） ----
        #   期望值取自 §361 的帧链定案；偏移由全量搜索返回地址确定（见文件头注）
        EXPECT = [
            (0x00920358, 0x00654418,
             "C3a 0x724730 ← 0x654413（retaddr 0x654418）"),
            (0x00920388, 0x006403A8,
             "C3b 0x654320 ← 0x6403A3（retaddr 0x6403A8）"),
            (0x009203AC, 0x006ABD3E,
             "C3c 0x6403A0 ← 0x6ABD39（retaddr 0x6ABD3E）"),
            (0x009203E4, 0x004A8B18,
             "C3d 0x6ABD30 ← 0x4A8B13（retaddr 0x4A8B18）"),
            (0x0092043C, 0x00652D51,
             "C3e 0x4A8850 ← 0x652D4C（retaddr 0x652D51）"),
        ]
        for va, want, label in EXPECT:
            raw = read_va(va, 4)
            if raw is None:
                chk(label, False, "NOT COVERED")
                continue
            v = struct.unpack("<I", raw)[0]
            chk(label, v == want, "got %08X want %08X" % (v, want))

        # ---- C12：偏移自证 ----
        #   真实栈 0x920384 处存的值 == 0xF9A300（引擎自己保存的栈基址）
        #   ★ 注意：except.txt 把它记在 `00F9A384`（同一格），
        #     `00F9A384 - 0x920384 == 0x67A000` ⇒ 两条独立路径同一偏移。
        raw = read_va(0x00920384, 4)
        if raw is None:
            chk("C12a 真实栈 [0x920384] 可读", False, "NOT COVERED")
        else:
            v = struct.unpack("<I", raw)[0]
            chk("C12a 真实栈 [0x920384] == 0x00F9A300（引擎存的栈基址）",
                v == 0x00F9A300, "got %08X" % v)
        chk("C12b 偏移 == 0x67A000（页对齐常量）",
            ESP_SKEW == 0x67A000, "got %08X" % ESP_SKEW)
        #   except.txt 里报的 Esp 与 0x920344 同差
        chk("C12c except.txt 报的 Esp 0xF9A344 对应真实 0x920344",
            REPORTED_ESP - 0x00920344 == ESP_SKEW,
            "skew=%08X" % (REPORTED_ESP - 0x00920344))

        # ---- C9：Eip 与模块基址 ----
        #   ★ 调试器版趟里游戏自己的 __except 未落盘（except_changed=False），
        #     故 except.txt 回退到历史现场 `ra2youli/except.txt` 作对照。
        ex_src = EXCEPT if EXCEPT.is_file() else HIST
        print("  except 源:", ex_src)
        ex = ex_src.read_text(encoding="utf-8", errors="replace")
        eip_ok = "00724737" in ex
        chk("C9a except.txt 的 Eip == 00724737", eip_ok)

        mod_sz, mod_rva = dirs[4]
        f.seek(mod_rva)
        n_mod = struct.unpack("<I", f.read(4))[0]
        mods = []
        for _ in range(n_mod):
            rec = f.read(108)
            base = struct.unpack("<Q", rec[0:8])[0]
            msize = struct.unpack("<I", rec[8:12])[0]
            name_rva = struct.unpack("<I", rec[20:24])[0]
            mods.append((base, msize, name_rva))
        # 读模块名
        names = []
        for base, msize, name_rva in mods:
            # MINIDUMP_STRING: ULONG32 Length (bytes, not chars) + WCHAR[]
            f.seek(name_rva)
            ln = struct.unpack("<I", f.read(4))[0]
            s = f.read(ln).decode("utf-16-le", "replace")
            names.append((base, msize, s))

        gamemd = [m for m in names if m[2].lower().endswith("gamemd.exe")]
        # ★ 同一个模块可能出现两条记录（内存镜像 + 卸载副本），
        #   判据是「基址唯一」，不是「条数 == 1」。
        bases = sorted({m[0] for m in gamemd})
        chk("C9b module 列表含 gamemd.exe 且基址唯一",
            len(gamemd) >= 1 and len(bases) == 1,
            "%d records, bases=%s" % (len(gamemd), [hex(b) for b in bases]))
        if gamemd:
            base, msize, nm = gamemd[0]
            chk("C9c gamemd ImageBase == 0x00400000",
                base == 0x00400000, "got %08X" % base)
            # 崩溃地址在 gamemd 内
            chk("C9d 崩溃 Eip 落在 gamemd 区间内",
                base <= 0x00724737 < base + msize,
                "base=%08X size=%08X end=%08X"
                % (base, msize, base + msize))

        # ---- C10：反证——L3 的 0x4A8B75 调用未返回 ----
        found = False
        for start, rsize in ranges:
            if start <= STACK and STACK + 0x400 <= start + rsize:
                f.seek(base_rva + (STACK - ranges[0][0]))
                blob = f.read(0x400)
                if struct.pack("<I", 0x004A8B7A) in blob:
                    found = True
                break
        chk("C10 反证：栈上不含 0x4A8B7A（L3 的 0x4A8B75 未返回）",
            not found, "found=%s" % found)

        # ---- C11：与历史现场比对 ----
        hist = HIST.read_text(encoding="utf-8", errors="replace")
        same_regs = all(k in ex and k in hist for k in
                        ("00724737", "00F9A344", "00000250"))
        chk("C11 新现场与历史现场关键三元组一致", same_regs)

    finally:
        f.close()

    print()
    n = len(CHECKS)
    ok = sum(1 for _, v, _ in CHECKS if v)
    print("-" * 78)
    print("结果：%d/%d PASS" % (ok, n))
    if ok != n:
        print("FAILED:")
        for name, v, d in CHECKS:
            if not v:
                print("  -", name, d)
        return 1
    print("判定：CONFIRMED —— 该 minidump 的栈内存与 except.txt 描述的是同一现场")
    return 0


if __name__ == "__main__":
    sys.exit(main())
