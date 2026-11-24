#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q3 · 指令边界总数与 .byte 伪指令条数

以 capstone CS_MODE_32 + disasm_lite + md.skipdata=True 全段一次扫完。
.byte 伪指令不计入「指令边界」，但单独计数。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "q3.json")
BM_CACHE = os.path.join(HERE, "_boundary_bitmap.bin")


def get_bitmap(text, skipdata=True):
    import hashlib
    key = hashlib.sha256(text).hexdigest()
    meta_path = BM_CACHE + ".meta"
    if skipdata and os.path.exists(BM_CACHE) and os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        if meta.get("key") == key and meta.get("skipdata") is True:
            with open(BM_CACHE, "rb") as f:
                bm = bytearray(f.read())
            if len(bm) == len(text):
                print("[cache] 复用边界位图")
                return (bm, meta["n_insn"], meta["n_byte"], meta["last_end"])
    bm, n_insn, n_byte, last_end = C.build_boundary_bitmap(text, C.TEXT_VA,
                                                           skipdata=skipdata)
    if skipdata:
        with open(BM_CACHE, "wb") as f:
            f.write(bytes(bm))
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({"key": key, "skipdata": True, "n_insn": n_insn,
                       "n_byte": n_byte, "last_end": last_end}, f)
    return bm, n_insn, n_byte, last_end


def main():
    ck = C.Checks()
    data = C.load_file()
    sha = C.sha256_of(data)
    print("sha256 =", sha)
    ck.check("sha256 与卡面一致", sha == C.EXPECT_SHA, sha)

    text = C.load_text(data)
    print("正在全段 disasm_lite（CS_MODE_32, skipdata=True, detail=False）…")
    bm, n_insn_total, n_byte, last_end = get_bitmap(text, skipdata=True)
    n_bounds = sum(bm)

    print("\n== Q3 指令边界与 .byte 伪指令 ==")
    print("capstone 迭代总条数（含 .byte） = %d" % n_insn_total)
    print(".byte 伪指令条数                = %d" % n_byte)
    print("指令边界总数（真实指令）        = %d" % n_bounds)
    print("覆盖末址                        = %s" % hex(last_end))

    # ---------------- 自测 ----------------
    print("\n== 自测 ==")
    ck.check("真实指令数 + .byte 数 == 迭代总条数",
             n_bounds + n_byte == n_insn_total,
             "%d + %d == %d" % (n_bounds, n_byte, n_insn_total))
    ck.check("覆盖到 .text 末地址 0x7e1000", last_end == C.TEXT_END,
             "last_end=%s" % hex(last_end))
    ck.check("位图 1 的个数等于真实指令数", n_bounds == sum(1 for v in bm if v),
             "%d" % sum(1 for v in bm if v))
    ck.check(".byte 条数为正（证明 skipdata 真的被触发过）", n_byte > 0,
             "n_byte=%d" % n_byte)
    ck.check("指令边界数在合理量级（1e5..1e7）",
             100000 < n_bounds < 10000000, "%d" % n_bounds)

    # .byte 位置抽样：确认这些偏移在位图上确实是 0
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    byte_sites = []
    for addr, size, mnem, _o in md.disasm_lite(text, C.TEXT_VA):
        if mnem == ".byte":
            byte_sites.append(addr)
    del md
    ck.check(".byte 位置复扫条数一致", len(byte_sites) == n_byte,
             "%d vs %d" % (len(byte_sites), n_byte))
    ck.check("所有 .byte 起始偏移在位图上为 0",
             all(bm[a - C.TEXT_VA] == 0 for a in byte_sites),
             "抽样 %s" % [hex(a) for a in byte_sites[:5]])

    # 边界单调性：相邻边界的地址差 == 上一条指令长度（抽样用 capstone 复验）
    md2 = Cs(CS_ARCH_X86, CS_MODE_32)
    md2.skipdata = True
    sample_bad = 0
    checked = 0
    for addr, size, mnem, _o in md2.disasm_lite(text, C.TEXT_VA):
        if checked >= 20000:
            break
        if mnem != ".byte":
            nxt = addr + size
            if nxt - C.TEXT_VA < len(bm) and bm[nxt - C.TEXT_VA] == 0:
                sample_bad += 1
        checked += 1
    del md2
    ck.check("采样 2 万条：非 .byte 指令的后继地址均在边界位图上（除末条）",
             sample_bad <= 1, "bad=%d of %d" % (sample_bad, checked))

    summ = ck.summary()

    res = {
        "q": "Q3",
        "vault": "指令边界总数与 .byte 伪指令条数",
        "sha256": sha,
        "capstone_version": __import__("capstone").__version__,
        "mode": "CS_MODE_32, disasm_lite, skipdata=True, detail=False",
        "iter_total_insns_including_byte": n_insn_total,
        "byte_pseudo_insns": n_byte,
        "instruction_boundary_total": n_bounds,
        "coverage_last_end": hex(last_end),
        "text_end": hex(C.TEXT_END),
        "reached_text_end": last_end == C.TEXT_END,
        "byte_site_sample": [hex(a) for a in byte_sites[:20]],
        "selftest": summ,
        "checks": [{"name": n, "pass": c, "detail": d} for n, c, d in ck.rows],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("\n写出:", OUT)
    return 0 if summ["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
