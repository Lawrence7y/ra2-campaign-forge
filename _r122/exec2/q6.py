#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q6 · 双形态对象数：严格与宽松两种定义

严格：该对象全部写入中恰 2 次，且恰 1 个 DynamicVectorClass 名 + 恰 1 个
      VectorClass 名，元素类型相同。
宽松：该对象全部写入中至少 1 个 DynamicVectorClass 名 + 至少 1 个
      VectorClass 名，元素类型相同。

分别给总数、35 内、35 外，并给出两种定义的集合差集
（逐个地址 + 该地址的写入次数 + 全部类名）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "q6.json")
BM_CACHE = os.path.join(HERE, "_boundary_bitmap.bin")


def get_bitmap(text):
    import hashlib
    key = hashlib.sha256(text).hexdigest()
    with open(BM_CACHE + ".meta", "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["key"] == key
    with open(BM_CACHE, "rb") as f:
        bm = bytearray(f.read())
    assert len(bm) == len(text)
    return bm


def describe(tbl, tgt):
    w = tbl[tgt]
    return {
        "addr": hex(tgt),
        "writes": len(w),
        "names": [x[2] for x in w],
        "sites": [hex(x[0]) for x in w],
        "imms": [hex(x[1]) for x in w],
        "elem": (C.elem_tail(next((x[2] for x in w
                                   if C.family_of(x[2]) == "dvc"), None))
                 or C.elem_tail(next((x[2] for x in w
                                      if C.family_of(x[2]) == "vc"), None))),
    }


def main():
    ck = C.Checks()
    data = C.load_file()
    sha = C.sha256_of(data)
    print("sha256 =", sha)
    ck.check("sha256 与卡面一致", sha == C.EXPECT_SHA, sha)

    text = C.load_text(data)
    img = C.Image(data)
    bm = get_bitmap(text)

    raw_hits = C.scan_c705(text)
    clean_bss = C.bss_writes(C.filter_by_boundary(raw_hits, bm))
    tbl = C.build_write_table(clean_bss, img)

    # 35 容器地址（自己重算）
    d35 = C.derive_35_containers(text)
    edx35 = set(d35["edx"])
    ck.check("35 容器地址互不相同", len(edx35) == 35,
             "distinct=%d" % len(edx35))

    strict = C.dual_form_report(tbl, edx35, strict=True)
    loose = C.dual_form_report(tbl, edx35, strict=False)

    s_total, s_in, s_out = len(strict), len(set(strict) & edx35), len(set(strict) - edx35)
    l_total, l_in, l_out = len(loose), len(set(loose) & edx35), len(set(loose) - edx35)

    print("\n== Q6 双形态对象数 ==")
    print("严格定义：总数 = %d ; 35 内 = %d ; 35 外 = %d" % (s_total, s_in, s_out))
    print("宽松定义：总数 = %d ; 35 内 = %d ; 35 外 = %d" % (l_total, l_in, l_out))

    # 严格集是一类特例，必然被宽松集包含（先验证，后用于差集解读）
    strict_only = sorted(set(strict) - set(loose))
    loose_only = sorted(set(loose) - set(strict))

    print("\n-- 集合关系 --")
    print("严格 ⊂ 宽松 ? %s" % (set(strict) <= set(loose)))
    print("严格独有（严格为真但宽松为假） = %d" % len(strict_only))
    print("宽松独有（宽松为真但严格为假） = %d" % len(loose_only))

    print("\n-- 差集明细：严格有、宽松无（%d 个） --" % len(strict_only))
    strict_only_rows = []
    for t in strict_only:
        r = describe(tbl, t)
        in35 = t in edx35
        r["in_35"] = in35
        strict_only_rows.append(r)
        print("  %s  writes=%d  in35=%s  names=%s"
              % (r["addr"], r["writes"], in35, r["names"]))

    print("\n-- 差集明细：宽松有、严格无（%d 个） --" % len(loose_only))
    loose_only_rows = []
    for t in loose_only:
        r = describe(tbl, t)
        in35 = t in edx35
        r["in_35"] = in35
        loose_only_rows.append(r)
        print("  %s  writes=%d  in35=%s  names=%s"
              % (r["addr"], r["writes"], in35, r["names"]))

    # 宽松独有按写入次数分桶——这是"103 与 104 差异"的归属依据
    import collections
    bucket = collections.Counter(r["writes"] for r in loose_only_rows)
    print("\n宽松独有对象按写入次数分桶: %s" % dict(sorted(bucket.items())))
    bucket35 = collections.Counter(r["writes"] for r in loose_only_rows if r["in_35"])
    bucketout = collections.Counter(r["writes"] for r in loose_only_rows if not r["in_35"])
    print("  其中 35 内: %s" % dict(sorted(bucket35.items())))
    print("  其中 35 外: %s" % dict(sorted(bucketout.items())))

    # ---------------- 自测 ----------------
    print("\n== 自测 ==")
    ck.check("严格集 ⊆ 宽松集（定义蕴含关系成立）",
             set(strict) <= set(loose),
             "严格独有=%d" % len(strict_only))
    ck.check("严格对象写入次数恒为 2",
             all(v["writes"] == 2 for v in strict.values()),
             "写入次数集合=%s" % sorted({v["writes"] for v in strict.values()}))
    ck.check("严格对象各族恰好 1 个",
             all(v["n_dvc"] == 1 and v["n_vc"] == 1 for v in strict.values()))
    ck.check("宽松对象各族至少 1 个",
             all(v["n_dvc"] >= 1 and v["n_vc"] >= 1 for v in loose.values()))
    ck.check("所有双形态对象元素类型非空且唯一",
             all(v["elem"] for v in list(strict.values()) + list(loose.values())))
    ck.check("35 个容器全部是宽松双形态",
             edx35 <= set(loose),
             "35 内宽松=%d" % len(edx35 & set(loose)))
    ck.check("35 个容器全部是严格双形态",
             edx35 <= set(strict),
             "35 内严格=%d" % len(edx35 & set(strict)))
    ck.check("严格内 + 严格外 == 严格总数", s_in + s_out == s_total,
             "%d + %d == %d" % (s_in, s_out, s_total))
    ck.check("宽松内 + 宽松外 == 宽松总数", l_in + l_out == l_total,
             "%d + %d == %d" % (l_in, l_out, l_total))
    ck.check("严格外 ⊆ 宽松外（严格比宽松更窄，故差集只可能在严格外一侧）",
             (set(strict) - edx35) <= (set(loose) - edx35),
             "严格外=%d 宽松外=%d" % (s_out, l_out))
    ck.check("宽松外 - 严格外 == 宽松独有集合（两条路径的差集互相印证）",
             (set(loose) - edx35) - (set(strict) - edx35) == set(loose_only),
             "差集大小=%d vs 宽松独有=%d" % (len((set(loose) - edx35) - (set(strict) - edx35)),
                                            len(loose_only)))
    ck.check("35 内的严格数 == 35 内的宽松数（35 全为严格，故两定义在 35 内无差）",
             s_in == l_in, "严格内=%d 宽松内=%d" % (s_in, l_in))
    ck.check("宽松独有对象写入次数都 >= 3（严格失败的机制）",
             all(r["writes"] >= 3 for r in loose_only_rows) if loose_only_rows else True,
             "次数集合=%s" % sorted({r["writes"] for r in loose_only_rows}))

    # 负控：破坏"元素类型相同"判据。
    # 关键：必须让**同一对象内的两个名字尾串不同**才有破坏力。
    # 首版对每个对象的所有名字追加同一个 "X"，对象内尾串仍一致 => 判据没被破坏，
    # 断言 138->138 真 FAIL，暴露的是负控写错而不是数据错。
    # 现在改成：只给 DynamicVectorClass 那一支追加 "X"，使两个尾串必然不同。
    import copy
    broken = copy.deepcopy(tbl)
    for tgt, ws in broken.items():
        broken[tgt] = [(s, i,
                        (nm + "X" if (nm and C.family_of(nm) == "dvc") else nm))
                       for s, i, nm in ws]
    strict_broken = C.dual_form_report(broken, edx35, strict=True)
    loose_broken = C.dual_form_report(broken, edx35, strict=False)
    ck.check("负控：破坏元素类型判据后严格集缩小/变空",
             len(strict_broken) < s_total,
             "%d -> %d" % (s_total, len(strict_broken)))
    ck.check("负控：破坏元素类型判据后宽松集缩小/变空",
             len(loose_broken) < l_total,
             "%d -> %d" % (l_total, len(loose_broken)))
    # 更强的负控：只打破一个已知对象，其余不动，观察严格集恰好少 1
    one = sorted(set(strict))[0]
    broken1 = copy.deepcopy(tbl)
    broken1[one] = [(s, i, (nm + "X" if (nm and C.family_of(nm) == "dvc") else nm))
                    for s, i, nm in broken1[one]]
    s1 = C.dual_form_report(broken1, edx35, strict=True)
    ck.check("负控：只破坏一个对象 => 严格集恰少 1 且该地址消失",
             len(s1) == s_total - 1 and one not in s1,
             "%d -> %d, %s 移除=%s" % (s_total, len(s1), hex(one), one not in s1))
    # 反控：把族名改成非 VectorClass 名，双形态集必须为空
    nonvec = {}
    for tgt, ws in tbl.items():
        nonvec[tgt] = [(s, i, ".?AVSomeOtherClass@@") for s, i, _nm in ws]
    ck.check("负控：所有名字换成非 VectorClass 族 => 严格集为空",
             len(C.dual_form_report(nonvec, edx35, strict=True)) == 0)
    ck.check("负控：所有名字换成非 VectorClass 族 => 宽松集为空",
             len(C.dual_form_report(nonvec, edx35, strict=False)) == 0)

    summ = ck.summary()

    res = {
        "q": "Q6",
        "vault": "双形态对象数（严格/宽松两种定义）",
        "sha256": sha,
        "definitions": {
            "strict": "全部写入恰 2 次，且恰 1 个 DynamicVectorClass 名 + 恰 1 个 VectorClass 名，元素类型相同",
            "loose": "全部写入中至少 1 个 DynamicVectorClass 名 + 至少 1 个 VectorClass 名，元素类型相同",
            "elem_same_rule": "该对象所有 VectorClass 族名字剥前缀后的尾串去重恰 1 个",
        },
        "vault_used_for_q6": "clean（站点落在 skipdata 边界集合上）",
        "strict_total": s_total, "strict_in35": s_in, "strict_out35": s_out,
        "loose_total": l_total, "loose_in35": l_in, "loose_out35": l_out,
        "strict_subset_of_loose": set(strict) <= set(loose),
        "strict_only_count": len(strict_only),
        "loose_only_count": len(loose_only),
        "strict_only": strict_only_rows,
        "loose_only": loose_only_rows,
        "loose_only_write_count_histogram": {str(k): v for k, v in sorted(bucket.items())},
        "loose_only_hist_in35": {str(k): v for k, v in sorted(bucket35.items())},
        "loose_only_hist_out35": {str(k): v for k, v in sorted(bucketout.items())},
        "selftest": summ,
        "checks": [{"name": n, "pass": c, "detail": d} for n, c, d in ck.rows],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("\n写出:", OUT)
    return 0 if summ["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
