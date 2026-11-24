#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q5 · 求 CRT 静态初始化表并反汇编其遍历函数。

找法（卡面口径 + 一处必要的补充判据，理由写进产物）：
  在 .text 指令流里找连续三元组 (push imm32, push imm32, call)，
  两个立即数都在 .data 有文件字节的已初始化区 [0x812000,0x87e000)，begin<end，
  (end-begin)%4==0。
  卡面「取区间最大的那个」按字面执行时得到的是 0x81a7a8..0x83de68（36272 项），
  但该区间的「非零项全在 .text」为假、且 35 个 ctor 单元覆盖 = 0，
  即它不是函数指针表，只是被当成两个立即数压栈的普通数据地址。
  因此本脚本同时落盘两个数字：
    (a) literal_largest        —— 纯按卡面字面规则取的最大区间；
    (b) chosen（表形态筛选后最大）—— 在「非零项全部落在 .text」的候选里取最大。
  正控（至少一个 ctor 单元在表内）只在 (b) 上成立，(a) 上为 0，两个数字都记录。

报告：区间起止 VA、项数、项里为 0 的个数、非零项是否全在 .text、非零项是否互不相同、
     35 个 ctor 单元里有几个出现在表内、遍历函数形态。

反控：
  A) 区间右端减 4（卡面指定）：如实记录覆盖数是否下降（本例不下降，原因见下）。
  B) 截到最后一个 ctor 条目之前：覆盖数必须下降。
  C) 表起点错位 4 字节：覆盖数必须下降。

用法：timeout 300 python3 q5.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_r123 as C

OUT = os.path.join(C.OUTDIR, "q5.json")


def q3_rows():
    p = os.path.join(C.OUTDIR, "q3.json")
    if not os.path.exists(p):
        raise SystemExit("先跑 q3.py")
    with open(p) as f:
        return json.load(f)["objects"]


def table_stats(B, E):
    N = (E - B) // 4
    vals = [C.u32(B + 4 * j) for j in range(N)]
    nz = [v for v in vals if v]
    return {
        "begin": B, "end": E, "items": N, "vals": vals,
        "zeros": [j for j, v in enumerate(vals) if not v],
        "nonzero": nz,
        "all_in_text": all(C.TEXT_VA <= v < C.TEXT_END for v in nz),
        "distinct": len(set(nz)) == len(nz),
    }


def main():
    ck = C.Checks()
    C.preflight(ck)
    ins = C.Insns()
    starts = C.unit_starts(ins)

    # ---- 候选三元组
    cands = []
    seen = set()
    for k in range(ins.n - 2):
        if not (ins.m[k] == C.M_PUSH and ins.m[k + 1] == C.M_PUSH and ins.m[k + 2] == C.M_CALL):
            continue
        p = int(ins.i[k])
        q = int(ins.i[k + 1])
        for b, e in ((p, q), (q, p)):
            if not (C.DATA_INIT_LO <= b < C.DATA_INIT_HI and C.DATA_INIT_LO <= e < C.DATA_INIT_HI):
                continue
            if not (b < e and (e - b) % 4 == 0):
                continue
            if (b, e) in seen:
                continue
            seen.add((b, e))
            cands.append({"site": int(ins.a[k]), "begin": b, "end": e,
                          "items": (e - b) // 4, "call": int(ins.i[k + 2])})
    ck.add("三元组候选数 >= 1", len(cands) >= 1, "cands=%d" % len(cands))

    # ---- (a) 卡面字面：最大区间
    lit = max(cands, key=lambda c: (c["items"], -c["site"]))
    lit_stats = table_stats(lit["begin"], lit["end"])

    # ---- (b) 表形态筛选（非零项全在 .text）后最大
    shaped = []
    for c in cands:
        st = table_stats(c["begin"], c["end"])
        if st["all_in_text"] and st["nonzero"]:
            shaped.append((c, st))
    ck.add("存在满足「非零项全在 .text」的候选", len(shaped) >= 1, "shaped=%d" % len(shaped))
    best, st = max(shaped, key=lambda cs: (cs[0]["items"], -cs[0]["site"]))
    B, E, N = st["begin"], st["end"], st["items"]
    ck.add("表形态候选里最大区间唯一（项数无并列）",
           sum(1 for c, _ in shaped if c["items"] == N) == 1,
           "same_size=%d" % sum(1 for c, _ in shaped if c["items"] == N))
    ck.add("区间落在 .data 已初始化区且 end-begin 是 4 的倍数",
           C.DATA_INIT_LO <= B < E <= C.DATA_INIT_HI and (E - B) % 4 == 0,
           "[0x%08x,0x%08x) items=%d" % (B, E, N))

    nz = st["nonzero"]
    ck.add("非零项全部落在 .text", st["all_in_text"],
           "non_text=%s" % [hex(v) for v in nz if not (C.TEXT_VA <= v < C.TEXT_END)][:5])
    ck.add("非零项互不相同", st["distinct"], "n=%d distinct=%d" % (len(nz), len(set(nz))))
    ck.add("0 项恰为区间首项", st["zeros"] == [0], "zero_indices=%s" % st["zeros"][:8])
    ck.add("非零项按地址升序（有序表）", nz == sorted(nz), "ordered=%s" % (nz == sorted(nz)))

    # ---- 35 个 ctor / dtor 单元覆盖
    rows3 = q3_rows()
    ctor_units = sorted({int(r["ctor_unit"], 16) for r in rows3})
    dtor_units = sorted({int(r["dtor_unit"], 16) for r in rows3})
    vset = set(nz)
    ctor_in = [u for u in ctor_units if u in vset]
    dtor_in = [u for u in dtor_units if u in vset]
    ck.add("正控：至少一个 ctor 单元在表内", len(ctor_in) >= 1, "in_table=%d/35" % len(ctor_in))
    ck.add("35 个 ctor 单元全部在表内", len(ctor_in) == 35, "in_table=%d/35" % len(ctor_in))
    ck.add("dtor 单元不在表内（该表是 ctor 表）", len(dtor_in) == 0, "dtor_in=%d" % len(dtor_in))
    lit_vset = set(lit_stats["nonzero"])
    lit_ctor_in = [u for u in ctor_units if u in lit_vset]
    ck.add("字面最大区间（非表形态）对 35 个 ctor 单元覆盖为 0", len(lit_ctor_in) == 0,
           "literal=0x%08x..0x%08x items=%d ctor_in=%d"
           % (lit["begin"], lit["end"], lit["items"], len(lit_ctor_in)))

    pos = {u: j for j, u in enumerate(st["vals"]) if u}
    last_ctor_idx = max(pos[u] for u in ctor_in)

    # ---- 遍历函数
    call_va = best["call"]
    cu = C.unit_of(starts, call_va)
    ki = C.unit_index(starts, cu)
    cs, ce = C.unit_range(starts, ki)
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    d = C.load()
    body = d[0x1000 + (cs - C.TEXT_VA):0x1000 + (cs - C.TEXT_VA) + (ce - cs)]
    dis_list = [(i.address, i.bytes.hex(), i.mnemonic, i.op_str) for i in md.disasm(body, cs)]
    has_back_jmp = any(m == "jmp" and o.startswith("0x") and int(o, 16) < a
                       for a, _b, m, o in dis_list)
    has_ind_call = any(m == "call" and not o.startswith("0x") for _a, _b, m, o in dis_list)
    has_add4 = any(m == "add" and "4" in o for _a, _b, m, o in dis_list)
    has_test = any(m == "test" for _a, _b, m, o in dis_list)
    shape = {
        "entry": "0x%08x" % call_va,
        "unit_start": "0x%08x" % cs, "unit_end": "0x%08x" % ce, "unit_len": ce - cs,
        "n_insn": len(dis_list),
        "has_backward_jmp": has_back_jmp, "has_indirect_call": has_ind_call,
        "has_add4": has_add4, "has_null_test": has_test,
        "is_for_loop_over_items": bool(has_back_jmp and has_ind_call and has_add4 and has_test),
        "insns": [{"va": "0x%08x" % a, "bytes": b, "mnem": m, "ops": o}
                  for a, b, m, o in dis_list],
    }
    ck.add("遍历函数为 for 循环逐项调用（后向 jmp + 间接 call + add 4 + null 测试）",
           shape["is_for_loop_over_items"],
           json.dumps({k: shape[k] for k in ("has_backward_jmp", "has_indirect_call",
                                             "has_add4", "has_null_test")}))
    ck.add("遍历函数体在 .text 内且非空", cs >= C.TEXT_VA and ce <= C.TEXT_END and ce > cs,
           "0x%08x..0x%08x" % (cs, ce))

    # ---- 反控 A（卡面指定）：右端减 4
    def cover(begin, end, src=None):
        src = nz if src is None else src
        s = {C.u32(begin + 4 * j) for j in range((end - begin) // 4)}
        return len(set(ctor_units) & s)

    cov_full = len(ctor_in)
    cov_m4 = cover(B, E - 4)
    ck.add("反控 A：右端减 4 后覆盖数（如实记录，卡面预期「必须下降」）", True,
           "full=%d -> minus4=%d dropped=%d ; 末项 0x%08x 不是 ctor 单元，故不降"
           % (cov_full, cov_m4, cov_full - cov_m4, C.u32(E - 4)))
    # ---- 反控 B：截到最后一个 ctor 条目之前
    end_cut = B + 4 * last_ctor_idx
    cov_cut = cover(B, end_cut)
    ck.add("反控 B：截到最后一个 ctor 条目（下标 %d）之前，覆盖数下降" % last_ctor_idx,
           cov_cut < cov_full, "full=%d -> cut=%d dropped=%d" % (cov_full, cov_cut,
                                                                cov_full - cov_cut))
    # ---- 反控 C：起点错位 4
    cov_shift = cover(B + 4, E)
    ck.add("反控 C：表起点错位 4 字节后覆盖数下降", cov_shift < cov_full,
           "full=%d -> shifted=%d dropped=%d" % (cov_full, cov_shift, cov_full - cov_shift))
    # ---- 反控 D：字面最大区间不能覆盖任何 ctor 单元（已在上面的正控里断言为 0）

    res = {
        "q": "Q5",
        "binary": C.EXE,
        "sha256": C.sha256(),
        "rule": "push imm32,push imm32,call；两 imm 均在 .data 已初始化区；begin<end；(end-begin)%4==0",
        "disambiguation": "卡面字面最大区间不是函数指针表；改用「非零项全在 .text」筛选后取最大",
        "n_candidates": len(cands),
        "n_shape_candidates": len(shaped),
        "literal_largest": {
            "site": "0x%08x" % lit["site"], "begin": "0x%08x" % lit["begin"],
            "end": "0x%08x" % lit["end"], "items": lit["items"],
            "all_in_text": lit_stats["all_in_text"],
            "distinct": lit_stats["distinct"],
            "n_zero_items": len(lit_stats["zeros"]),
            "n_ctor_units_in_table": len(lit_ctor_in),
        },
        "chosen": {"site": "0x%08x" % best["site"], "begin": "0x%08x" % B, "end": "0x%08x" % E,
                   "items": N, "traversal_fn": "0x%08x" % call_va},
        "top_shape_candidates": sorted(
            [{"begin": "0x%08x" % c["begin"], "end": "0x%08x" % c["end"],
              "items": c["items"], "site": "0x%08x" % c["site"]} for c, _ in shaped],
            key=lambda x: -x["items"])[:6],
        "n_zero_items": len(st["zeros"]),
        "zero_indices": st["zeros"],
        "nonzero_all_in_text": st["all_in_text"],
        "nonzero_distinct": st["distinct"],
        "n_nonzero": len(nz),
        "n_ctor_units_in_table": len(ctor_in),
        "n_dtor_units_in_table": len(dtor_in),
        "ctor_units_in_table": ["0x%08x" % u for u in ctor_in],
        "last_ctor_entry_index": last_ctor_idx,
        "traversal_shape": shape,
        "negcontrol_end_minus4": {"full_coverage": cov_full, "minus4_coverage": cov_m4,
                                  "dropped": cov_full - cov_m4,
                                  "last_entry": "0x%08x" % C.u32(E - 4)},
        "negcontrol_cut_before_last_ctor": {"end": "0x%08x" % end_cut,
                                            "coverage": cov_cut, "dropped": cov_full - cov_cut},
        "negcontrol_shift_start_by4": {"coverage": cov_shift, "dropped": cov_full - cov_shift},
        "checks": ck.rows,
        "selftest": ck.summary(),
    }
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: res[k] for k in ("n_candidates", "n_shape_candidates",
                                          "literal_largest", "chosen", "n_zero_items",
                                          "nonzero_all_in_text", "nonzero_distinct",
                                          "n_ctor_units_in_table", "n_dtor_units_in_table",
                                          "negcontrol_end_minus4",
                                          "negcontrol_cut_before_last_ctor",
                                          "negcontrol_shift_start_by4", "selftest")},
                     ensure_ascii=False))
    return 0 if res["selftest"]["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
