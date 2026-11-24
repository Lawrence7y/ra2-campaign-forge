#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q5 · VectorClass 族 BSS 目标数（raw 与 clean 各一）

类名一律由 .rdata 的 RTTI 链（[vt-4]=COL → COL+0xc=TD → TD+8=名串）
从二进制字节独立反解，不读 symbols.json 的计数。
同时报 DynamicVectorClass 与 VectorClass 两个族的分项数，便于审计。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "q5.json")
BM_CACHE = os.path.join(HERE, "_boundary_bitmap.bin")


def get_bitmap(text):
    import hashlib
    key = hashlib.sha256(text).hexdigest()
    meta_path = BM_CACHE + ".meta"
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["key"] == key and len(open(BM_CACHE, "rb").read()) == len(text)
    with open(BM_CACHE, "rb") as f:
        bm = bytearray(f.read())
    return bm, meta["n_insn"], meta["n_byte"], meta["last_end"]


def main():
    ck = C.Checks()
    data = C.load_file()
    sha = C.sha256_of(data)
    print("sha256 =", sha)
    ck.check("sha256 与卡面一致", sha == C.EXPECT_SHA, sha)

    text = C.load_text(data)
    img = C.Image(data)

    raw_hits = C.scan_c705(text)
    raw_bss = C.bss_writes(raw_hits)
    bm, _n_insn, n_byte, last_end = get_bitmap(text)
    clean_bss = C.bss_writes(C.filter_by_boundary(raw_hits, bm))

    # 名字反解
    def name_of(imm):
        return img.rtti_name(imm)

    def tally(sites, fam_filter=None):
        """返回 (目标集, 站点数)。按族过滤时，只有写过该族 vptr 的目标才算。"""
        targets = set()
        n_sites = 0
        for site, tgt, imm in sites:
            nm = name_of(imm)
            fam = C.family_of(nm)
            if fam_filter is None or fam == fam_filter:
                targets.add(tgt)
                n_sites += 1
        return targets, n_sites

    # 全族（DynamicVectorClass + VectorClass 两族并集，即"VectorClass 族"）
    def family_union_targets(sites):
        t = set()
        for _s, tgt, imm in sites:
            if C.family_of(name_of(imm)) in ("dvc", "vc"):
                t.add(tgt)
        return t

    raw_fam = family_union_targets(raw_bss)
    clean_fam = family_union_targets(clean_bss)
    raw_dvc, raw_dvc_sites = tally(raw_bss, "dvc")
    raw_vc, raw_vc_sites = tally(raw_bss, "vc")
    clean_dvc, clean_dvc_sites = tally(clean_bss, "dvc")
    clean_vc, clean_vc_sites = tally(clean_bss, "vc")
    raw_cursor = family_union_targets(
        [(s, t, i) for s, t, i in raw_bss if C.family_of(name_of(i)) == "vcursor"])

    n_unresolved_raw = len({h[1] for h in raw_bss}) - len(
        {h[1] for h in raw_bss if name_of(h[2]) is not None})

    print("\n== Q5 VectorClass 族 BSS 目标数 ==")
    print("raw   口径：VectorClass 族目标数 = %d" % len(raw_fam))
    print("       其中 DynamicVectorClass  = %d（站点 %d）" % (len(raw_dvc), raw_dvc_sites))
    print("       其中 VectorClass         = %d（站点 %d）" % (len(raw_vc), raw_vc_sites))
    print("clean 口径：VectorClass 族目标数 = %d" % len(clean_fam))
    print("       其中 DynamicVectorClass  = %d（站点 %d）" % (len(clean_dvc), clean_dvc_sites))
    print("       其中 VectorClass         = %d（站点 %d）" % (len(clean_vc), clean_vc_sites))
    print("旁证：VectorCursor 族目标数（raw） = %d" % len(raw_cursor))
    print("未解析出类名的 BSS 目标数（raw）   = %d" % n_unresolved_raw)

    # ---------------- 自测 ----------------
    print("\n== 自测 ==")
    ck.check("raw 族目标集 ⊇ clean 族目标集", clean_fam <= raw_fam,
             "|raw|=%d |clean|=%d" % (len(raw_fam), len(clean_fam)))
    ck.check("raw 族目标集 ⊆ raw 全部 BSS 目标集",
             raw_fam <= {h[1] for h in raw_bss})
    # 子族集合关系：两子族**必然**相交（双形态对象同时写过两种 vptr），
    # 故这里断言的是集合恒等式而不是互斥——互斥断言是本脚本首版写错的地方。
    ck.check("族目标集 == dvc ∪ vc",
             raw_fam == (raw_dvc | raw_vc),
             "|fam|=%d |dvc∪vc|=%d" % (len(raw_fam), len(raw_dvc | raw_vc)))
    ck.check("|dvc| + |vc| - |dvc∩vc| == |族|（集合算术自洽）",
             len(raw_dvc) + len(raw_vc) - len(raw_dvc & raw_vc) == len(raw_fam),
             "%d + %d - %d == %d" % (len(raw_dvc), len(raw_vc),
                                     len(raw_dvc & raw_vc), len(raw_fam)))
    ck.check("dvc∩vc 非空（证明存在同时写过两族 vptr 的对象）",
             len(raw_dvc & raw_vc) > 0,
             "交集=%d" % len(raw_dvc & raw_vc))

    # 正控：35 个容器必须全部在 clean 族目标里（它们被证明写过 VectorClass vptr）
    d35 = C.derive_35_containers(text)
    edx35 = d35["edx"]
    ck.check("35 个容器地址互不相同", len(set(edx35)) == 35,
             "distinct=%d" % len(set(edx35)))
    ck.check("35 个容器全部落在 clean 族目标集内",
             set(edx35) <= clean_fam,
             "缺少 %d 个" % len(set(edx35) - clean_fam))

    # RTTI 反解器正控/负控
    nm_ok = img.rtti_name(0x7E9FA4)
    ck.check("RTTI 正控 0x7e9fa4 解出 DynamicVectorClass 名",
             nm_ok is not None and C.family_of(nm_ok) == "dvc", str(nm_ok))
    nm_bad = img.rtti_name(0x7E9FA8)   # vtable 内部槽位，非 vtable 起点
    ck.check("RTTI 负控 0x7e9fa8（vtable+4）解不出族名",
             C.family_of(nm_bad) is None, str(nm_bad))
    nm_zero = img.rtti_name(0)
    ck.check("RTTI 负控 0 解不出族名", C.family_of(nm_zero) is None, str(nm_zero))
    nm_bss = img.rtti_name(C.BSS_LO)
    ck.check("RTTI 负控 BSS 地址(无文件字节) 解不出族名",
             C.family_of(nm_bss) is None, str(nm_bss))

    # 族名口径自检：每个族目标至少有一个写入的 imm 能解出该族名
    ok_fam = True
    for tgt in list(raw_fam)[:200]:
        ws = [name_of(i) for s, t, i in raw_bss if t == tgt]
        if not any(C.family_of(n) in ("dvc", "vc") for n in ws):
            ok_fam = False
            break
    ck.check("每个族目标至少一个写入解出 VectorClass 族名（抽 200）", ok_fam)

    summ = ck.summary()

    res = {
        "q": "Q5",
        "vault": "VectorClass 族 BSS 目标数（raw 与 clean）",
        "sha256": sha,
        "family_definition": "名字匹配 .?AV?$DynamicVectorClass@ 或 .?AV?$VectorClass@（排除 VectorCursor 族）",
        "raw_family_targets": len(raw_fam),
        "clean_family_targets": len(clean_fam),
        "raw_dvc_targets": len(raw_dvc), "raw_dvc_sites": raw_dvc_sites,
        "raw_vc_targets": len(raw_vc), "raw_vc_sites": raw_vc_sites,
        "clean_dvc_targets": len(clean_dvc), "clean_dvc_sites": clean_dvc_sites,
        "clean_vc_targets": len(clean_vc), "clean_vc_sites": clean_vc_sites,
        "raw_vcursor_targets_sideinfo": len(raw_cursor),
        "raw_unresolved_bss_targets": n_unresolved_raw,
        "readme_35_in_clean_family": len(set(edx35) & clean_fam),
        "family_raw_addrs": [hex(a) for a in sorted(raw_fam)],
        "family_clean_addrs": [hex(a) for a in sorted(clean_fam)],
        "family_dropped_by_boundary": [hex(a) for a in sorted(raw_fam - clean_fam)],
        "selftest": summ,
        "checks": [{"name": n, "pass": c, "detail": d} for n, c, d in ck.rows],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("\n写出:", OUT)
    return 0 if summ["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
