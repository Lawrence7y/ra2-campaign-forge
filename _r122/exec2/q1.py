#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q1 · raw 口径：纯字节扫 c7 05（不判指令边界）

回答：BSS 目标数、站点数。
同时给出全部 c7 05 命中数与非 BSS 命中数，便于审计口径。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "q1.json")


def main():
    ck = C.Checks()
    data = C.load_file()
    sha = C.sha256_of(data)
    print("sha256 =", sha)
    ck.check("sha256 与卡面一致", sha == C.EXPECT_SHA, sha)

    base, rows = C.verify_pe(data)
    ck.check("ImageBase == 0x400000", base == C.IMAGE_BASE, hex(base))
    txt = [r for r in rows if r[0] == ".text"][0]
    ck.check(".text VA/raw/rawsize 实测与卡面一致",
             txt[1] == C.TEXT_VA and txt[2] == C.TEXT_RAW and txt[3] == C.TEXT_SIZE,
             "%s %s %s" % (hex(txt[1]), hex(txt[2]), hex(txt[3])))

    text = C.load_text(data)
    hits = C.scan_c705(text)
    bss = C.bss_writes(hits)

    n_all_sites = len(hits)
    n_all_targets = len({h[1] for h in hits})
    n_bss_sites = len(bss)
    bss_targets = {h[1] for h in bss}
    n_bss_targets = len(bss_targets)
    n_nonbss = n_all_sites - n_bss_sites

    print("\n== Q1 raw 口径（纯字节扫 c7 05，不判边界） ==")
    print("全部 c7 05 站点数            = %d" % n_all_sites)
    print("全部 c7 05 目标数            = %d" % n_all_targets)
    print("BSS 内 站点数 (Q1 站点数)    = %d" % n_bss_sites)
    print("BSS 内 目标数 (Q1 目标数)    = %d" % n_bss_targets)
    print("非 BSS 站点数                = %d" % n_nonbss)

    # ---------------- 自测 ----------------
    print("\n== 自测 ==")
    # 正控：手工构造一条 c7 05 字节流，必须命中
    pos = bytes.fromhex("c70534128700a49f7e00")
    pos_hits = C.scan_c705(pos, 0x401000)
    ck.check("正控 c7 05 构造流命中",
             len(pos_hits) == 1 and pos_hits[0][1] == 0x871234
             and pos_hits[0][2] == 0x7e9fa4,
             str([(hex(a), hex(t), hex(i)) for a, t, i in pos_hits]))

    # 负控 1：modrm 0x45（disp8 形态）不得被当成 c7 05
    neg = bytes.fromhex("c745ff34128700")
    neg_hits = C.scan_c705(neg, 0x401000)
    ck.check("负控1 modrm=0x45 disp8 形态不命中", len(neg_hits) == 0,
             "hits=%d" % len(neg_hits))

    # 附加形态控制：c7 04 25 (SIB+disp32)、c7 05 之外的 /1.. /7
    neg2 = bytes.fromhex("c70d34128700a49f7e00")   # /1 = 0x0d
    ck.check("负控1b modrm=0x0d(/1) 不命中", len(C.scan_c705(neg2, 0x401000)) == 0)
    neg3 = bytes.fromhex("c7042534128700a49f7e00")  # SIB 形态
    ck.check("负控1c modrm=0x04(SIB) 不命中", len(C.scan_c705(neg3, 0x401000)) == 0)

    # 结构自检
    ck.check("所有 BSS 命中目标落在 [0x87e000,0xb79be4)",
             all(C.BSS_LO <= t < C.BSS_HI for t in bss_targets),
             "min=%s max=%s" % (hex(min(bss_targets)), hex(max(bss_targets))))
    ck.check("BSS 站点数 >= BSS 目标数", n_bss_sites >= n_bss_targets,
             "%d >= %d" % (n_bss_sites, n_bss_targets))
    ck.check("BSS 目标数是 BSS 站点数的真子集关系（多写）",
             n_bss_sites > n_bss_targets,
             "sites=%d targets=%d" % (n_bss_sites, n_bss_targets))
    # 分块一致性：把 .text 切成 4 段分别扫，总数必须与整段一致（防流式漏检）
    step = len(text) // 4
    chunked = []
    for k in range(4):
        a = k * step
        b = len(text) if k == 3 else (k + 1) * step
        seg = text[a:b]
        # 边界处可能跨越，故左边界回退 9 字节
        pre = 9 if a > 0 else 0
        for site, tgt, imm in C.scan_c705(text[a - pre:b], C.TEXT_VA + a - pre):
            if site >= C.TEXT_VA + a:
                chunked.append((site, tgt, imm))
    ck.check("分块扫描结果与整段扫描一致", len(chunked) == n_all_sites,
             "chunked=%d whole=%d" % (len(chunked), n_all_sites))

    summ = ck.summary()

    res = {
        "q": "Q1",
        "vault": "raw（纯字节扫 c7 05，不判指令边界）",
        "sha256": sha,
        "sha256_ok": sha == C.EXPECT_SHA,
        "bss_range": [hex(C.BSS_LO), hex(C.BSS_HI)],
        "text_range": [hex(C.TEXT_VA), hex(C.TEXT_END)],
        "q1_bss_targets": n_bss_targets,
        "q1_bss_sites": n_bss_sites,
        "all_c705_sites": n_all_sites,
        "all_c705_targets": n_all_targets,
        "non_bss_sites": n_nonbss,
        "selftest": summ,
        "checks": [{"name": n, "pass": c, "detail": d} for n, c, d in ck.rows],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("\n写出:", OUT)
    return 0 if summ["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
