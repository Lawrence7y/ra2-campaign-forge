#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q2 · clean 口径：站点必须落在 skipdata 指令边界集合上

回答：BSS 目标数、站点数、被丢弃目标数。
含负控 2（边界集合换成空集 => clean 目标数必须为 0）
与负控 3（关掉 skipdata 重扫 => 必须观察到扫描提前中断，记录中断地址）。
含口径自检：Q1 目标集必须包含 Q2 目标集。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "q2.json")
BM_CACHE = os.path.join(HERE, "_boundary_bitmap.bin")


def get_bitmap(text, skipdata=True, cache_path=BM_CACHE):
    """全段一次 disasm_lite 扫完；结果落盘缓存，避免多次重跑重复 30s 反汇编。

    缓存只在 (text sha256, skipdata) 匹配时复用；skipdata=False 一律现算。
    """
    import hashlib
    key = hashlib.sha256(text).hexdigest()
    meta_path = cache_path + ".meta"
    if skipdata and os.path.exists(cache_path) and os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        if meta.get("key") == key and meta.get("skipdata") is True:
            with open(cache_path, "rb") as f:
                bm = bytearray(f.read())
            if len(bm) == len(text):
                print("[cache] 复用边界位图 %s" % cache_path)
                return (bm, meta["n_insn"], meta["n_byte"], meta["last_end"])
    bm, n_insn, n_byte, last_end = C.build_boundary_bitmap(text, C.TEXT_VA,
                                                           skipdata=skipdata)
    if skipdata:
        with open(cache_path, "wb") as f:
            f.write(bytes(bm))
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({"key": key, "skipdata": True, "n_insn": n_insn,
                       "n_byte": n_byte, "last_end": last_end}, f)
    return bm, n_insn, n_byte, last_end


def no_skipdata_scan(text):
    """关掉 skipdata 做流式扫描，检测是否提前中断。

    返回 (scan_insns, last_end, stopped_early, stop_va, error)。
    不用 disasm_lite 的生成器抛错来判断——capstone 在无 skipdata 时遇到
    非法字节会直接停止迭代（生成器提前 return），所以「迭代自然结束但
    last_end < 段末」就是提前中断的证据。
    """
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = False
    text_end = C.TEXT_VA + len(text)
    n = 0
    last_end = C.TEXT_VA
    err = None
    try:
        for addr, size, _mnem, _ops in md.disasm_lite(text, C.TEXT_VA):
            n += 1
            last_end = addr + size
    except Exception as e:      # pragma: no cover - 防御性
        err = repr(e)
    del md
    stopped_early = last_end < text_end
    return n, last_end, stopped_early, last_end, err


def main():
    ck = C.Checks()
    data = C.load_file()
    sha = C.sha256_of(data)
    print("sha256 =", sha)
    ck.check("sha256 与卡面一致", sha == C.EXPECT_SHA, sha)

    text = C.load_text(data)

    # ---- Q1 口径重算（不读 q1.json，独立算）
    raw_hits = C.scan_c705(text)
    raw_bss = C.bss_writes(raw_hits)
    raw_targets = {h[1] for h in raw_bss}

    # ---- 边界集合
    print("\n正在全段 disasm_lite 建立边界集合（skipdata=True）…")
    bm, n_insn, n_byte, last_end = get_bitmap(text, skipdata=True)
    n_bounds = sum(bm)
    print("指令边界总数(真实指令) = %d ; .byte 伪指令 = %d ; 覆盖末址 = %s"
          % (n_bounds, n_byte, hex(last_end)))

    # ---- clean 口径
    clean_hits = C.filter_by_boundary(raw_hits, bm)
    clean_bss = C.bss_writes(clean_hits)
    clean_targets = {h[1] for h in clean_bss}
    dropped_hits = len(raw_bss) - len(clean_bss)
    dropped_targets = len(raw_targets - clean_targets)

    print("\n== Q2 clean 口径（站点落在 skipdata 边界集合上） ==")
    print("BSS 站点数（raw）   = %d" % len(raw_bss))
    print("BSS 站点数（clean） = %d" % len(clean_bss))
    print("BSS 目标数（raw）   = %d" % len(raw_targets))
    print("BSS 目标数（clean） = %d" % len(clean_targets))
    print("被丢弃站点数        = %d" % dropped_hits)
    print("被丢弃目标数        = %d" % dropped_targets)
    dropped = sorted(raw_targets - clean_targets)
    print("被丢弃目标地址      = %s" % [hex(a) for a in dropped])
    # 这些被丢弃目标是被"非边界站点"唯一支撑，还是有其他 clean 站点支撑？
    only_bad = []
    for t in dropped:
        sup = [h for h in clean_bss if h[1] == t]
        if not sup:
            only_bad.append(t)
    print("其中无任何 clean 站点支撑的目标 = %d" % len(only_bad))

    # ---------------- 自测 ----------------
    print("\n== 自测 ==")
    # 口径自检：Q1 目标集必须包含 Q2 目标集
    ck.check("口径自检 Q1目标集 ⊇ Q2目标集",
             clean_targets <= raw_targets,
             "|Q1|=%d |Q2|=%d diff=%d" % (len(raw_targets), len(clean_targets),
                                          len(raw_targets - clean_targets)))
    ck.check("口径自检 Q2 站点集 ⊆ Q1 站点集",
             {(s) for s, _t, _i in clean_bss} <= {(s) for s, _t, _i in raw_bss})

    # 负控 2：边界集合换成空集，clean 目标数必须为 0
    empty_bm = bytearray(len(text))
    empty_clean = C.bss_writes(C.filter_by_boundary(raw_hits, empty_bm))
    ck.check("负控2 空边界集合 => clean 目标数为 0",
             len({h[1] for h in empty_clean}) == 0,
             "targets=%d" % len({h[1] for h in empty_clean}))
    ck.check("负控2 空边界集合 => clean 站点数为 0", len(empty_clean) == 0,
             "sites=%d" % len(empty_clean))

    # 负控 2b：只保留一条无关边界，clean 目标数仍应为 0（证明不是"空集特例"）
    one_bm = bytearray(len(text))
    one_bm[0] = 1
    one_clean = C.bss_writes(C.filter_by_boundary(raw_hits, one_bm))
    ck.check("负控2b 单一边界(段首) => clean 目标数为 0",
             len({h[1] for h in one_clean}) == 0,
             "targets=%d" % len({h[1] for h in one_clean}))

    # 负控 3：关掉 skipdata 重扫，必须观察到提前中断
    print("\n正在关掉 skipdata 重扫以验证其必要性…")
    n0, last0, early, stop_va, err = no_skipdata_scan(text)
    print("skipdata=False 扫描条数 = %d ; 末址 = %s ; 段末 = %s"
          % (n0, hex(last0), hex(C.TEXT_END)))
    ck.check("负控3 关 skipdata => 扫描提前中断", early,
             "last_end=%s < text_end=%s" % (hex(last0), hex(C.TEXT_END)))
    ck.check("负控3 中断地址被记录", stop_va is not None, hex(stop_va))
    ck.check("负控3 中断地址落在 .text 内部",
             C.TEXT_VA <= stop_va < C.TEXT_END,
             "%s in [%s,%s)" % (hex(stop_va), hex(C.TEXT_VA), hex(C.TEXT_END)))
    ck.check("负控3 无 skipdata 的扫描条数远少于有 skipdata",
             n0 < n_insn,
             "no_skipdata=%d < skipdata=%d" % (n0, n_insn))
    ck.check("负控3 有 skipdata 时覆盖到段末（证明 skipdata 修复了中断）",
             last_end == C.TEXT_END,
             "last_end=%s text_end=%s" % (hex(last_end), hex(C.TEXT_END)))

    # 边界集合自检：clean 站点必须都在位图上
    ok_bounds = all(0 <= s - C.TEXT_VA < len(bm) and bm[s - C.TEXT_VA]
                    for s, _t, _i in clean_bss)
    ck.check("所有 clean 站点在边界位图上", ok_bounds, "n=%d" % len(clean_bss))
    # .byte 不计入边界：确认位图里 .byte 的位置不是 1
    ck.check(".byte 伪指令未被计入边界", n_byte > 0 and n_bounds == n_insn - n_byte,
             "bounds=%d insn=%d byte=%d" % (n_bounds, n_insn, n_byte))

    summ = ck.summary()

    res = {
        "q": "Q2",
        "vault": "clean（站点必须落在 skipdata 指令边界集合上）",
        "sha256": sha,
        "bss_targets_clean": len(clean_targets),
        "bss_sites_clean": len(clean_bss),
        "bss_targets_raw": len(raw_targets),
        "bss_sites_raw": len(raw_bss),
        "dropped_sites": dropped_hits,
        "dropped_targets": dropped_targets,
        "dropped_target_addrs": [hex(a) for a in dropped],
        "dropped_targets_without_clean_support": [hex(a) for a in only_bad],
        "boundary_count": n_bounds,
        "byte_pseudo_count": n_byte,
        "disasm_insn_total": n_insn,
        "text_last_end": hex(last_end),
        "negctl3": {
            "no_skipdata_insns": n0,
            "no_skipdata_last_end": hex(last0),
            "stopped_early": early,
            "interrupt_va": hex(stop_va),
            "error": err,
        },
        "selftest": summ,
        "checks": [{"name": n, "pass": c, "detail": d} for n, c, d in ck.rows],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("\n写出:", OUT)
    return 0 if summ["verdict"] == "PASS" else 1


C_no_skipdata = no_skipdata_scan

if __name__ == "__main__":
    sys.exit(main())
