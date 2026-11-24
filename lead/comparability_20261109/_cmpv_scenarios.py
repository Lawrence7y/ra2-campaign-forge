# -*- coding: utf-8 -*-
"""_cmpv_scenarios.py — 独立复核员自造单轴场景，套被核 _cmp_assert.py 看判对/判错。
全部产物落唯一写域且前缀 _cmpv_；调用被核断言时只读、--out 指向 _cmpv_ 文件。
Python: python -I -X utf8 <abs _cmpv_scenarios.py>
"""
import json
import pathlib
import subprocess
import sys

WD = pathlib.Path("D:/Project/ra2-campaign-forge/lead/comparability_20261109")
ASSERT = str(WD / "_cmp_assert.py")
JUDGE = ("naive", "r10", "r12", "n13", "chain")


def mk_rows():
    base = [
        ("X1", "CATCH", "PASS"),
        ("X2", "PASS", "CATCH"),
        ("X3", "PASS", "PASS"),
        ("X4", "CATCH", "PASS"),
    ]
    rows = []
    for i, (rid, expect, chain) in enumerate(base):
        rows.append({
            "id": rid, "family": "F%d" % (i % 2), "expect": expect,
            "tokens": ["已入账", "已生效"], "note": "固定标注手册 v1",
            "text_head": "样本句子 %d 号，含待判 token。" % i,
            "naive": "PASS", "r10": "PASS", "r12": "PASS", "n13": expect,
            "chain": chain, "layer_conflicts": 0, "layer_unresolved": 0,
        })
    return rows


def stats(rows):
    st = {}
    for m in JUDGE:
        ok = fp = fn = 0
        for r in rows:
            if r[m] == r["expect"]:
                ok += 1
            elif r["expect"] == "PASS":
                fp += 1
            else:
                fn += 1
        st[m] = {"ok": ok, "fp": fp, "fn": fn}
    return st


def mkdoc(rows):
    return {"corpus_n": len(rows), "rows": rows,
            "single_layer_vs_chain": stats(rows),
            "chain_conflicts_total": sum(r["layer_conflicts"] for r in rows),
            "chain_unresolved_total": sum(r["layer_unresolved"] for r in rows)}


def wj(name, obj):
    p = WD / name
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    return str(p)


def run(tag, A, B, man, expect_comment):
    pa = wj("_cmpv_s_%s_A.json" % tag, A)
    pb = wj("_cmpv_s_%s_B.json" % tag, B)
    pm = wj("_cmpv_s_%s_man.json" % tag, man)
    po = WD / ("_cmpv_s_%s_out.json" % tag)
    r = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", ASSERT, pa, pb,
         "--manifest", pm, "--label-a", "A", "--label-b", "B", "--out", str(po)],
        capture_output=True, text=True)
    d = json.loads(po.read_text(encoding="utf-8"))
    print("[%s] %s" % (tag, expect_comment))
    print("   EXIT=%d verdict=%s differing_axes=%s unknown_axes=%s" %
          (r.returncode, d["verdict"], d["differing_axes"], d["unknown_axes"]))
    print("   axes=%s" % {k: v["state"] for k, v in d["axes"].items()})
    print("   reason=%s" % d["reason"])
    print("   n_expect_changes=%d n_note_changes=%d strict_n=%d" %
          (d["n_expect_changes"], d["n_note_changes"], d["strict_subset"]["n"]))
    return d


def main():
    import copy
    I0 = "a" * 64
    I1 = "b" * 64
    E0 = "c" * 64
    E1 = "d" * 64

    # 场景 1：只改算法 I（rows 完全同，仅 chain 一列由算法产生差异；manifest 声明 I 变 / E 同）
    A = mkdoc(mk_rows())
    B = mkdoc(mk_rows())
    B["rows"][1]["chain"] = "PASS"           # X2 误拦 -> 放行
    B["single_layer_vs_chain"] = stats(B["rows"])
    run("1_only_I", A, B,
        {"a": {"implementation_sha256": I0, "eval_script_sha256": E0},
         "b": {"implementation_sha256": I1, "eval_script_sha256": E0},
         "crossed_design_cells_actually_executed": []},
        "只改算法 I：按判据应判 COMPARABLE")

    # 场景 2：只改真值 G（X4 expect CATCH->PASS，模型输出逐列不变；I/E 均相同）
    A = mkdoc(mk_rows())
    B = mkdoc(mk_rows())
    B["rows"][3]["expect"] = "PASS"
    B["single_layer_vs_chain"] = stats(B["rows"])
    run("2_only_G", A, B,
        {"a": {"implementation_sha256": I0, "eval_script_sha256": E0},
         "b": {"implementation_sha256": I0, "eval_script_sha256": E0},
         "crossed_design_cells_actually_executed": []},
        "只改真值 G：报告 §2(b) 判据明写『G 变=不可比(硬)』，§2(c) 要求 diff_axes==['I']")

    # 场景 3：只改评测脚本 E（chain 一列差异；manifest 声明 I 同 / E 不同）
    A = mkdoc(mk_rows())
    B = mkdoc(mk_rows())
    B["rows"][1]["chain"] = "PASS"
    B["single_layer_vs_chain"] = stats(B["rows"])
    run("3_only_E", A, B,
        {"a": {"implementation_sha256": I0, "eval_script_sha256": E0},
         "b": {"implementation_sha256": I0, "eval_script_sha256": E1},
         "crossed_design_cells_actually_executed": []},
        "只改评测脚本 E：报告 §2(b) 判据明写『E 变=不可比(硬)』")

    # 场景 4：只改样本集 S（新增 1 行；I/E/G 冻结）
    A = mkdoc(mk_rows())
    rowsB = mk_rows()
    rowsB.append({"id": "X5", "family": "F0", "expect": "CATCH",
                  "tokens": ["已入账", "已生效"], "note": "固定标注手册 v1",
                  "text_head": "样本句子 5 号，含待判 token。",
                  "naive": "PASS", "r10": "PASS", "r12": "PASS", "n13": "CATCH",
                  "chain": "CATCH", "layer_conflicts": 0, "layer_unresolved": 0})
    B = mkdoc(rowsB)
    run("4_only_S", A, B,
        {"a": {"implementation_sha256": I0, "eval_script_sha256": E0},
         "b": {"implementation_sha256": I0, "eval_script_sha256": E0},
         "crossed_design_cells_actually_executed": []},
        "只改样本 S：报告 §2(b) 判据明写『S 变=不可比(硬)』")

    # 场景 5：只改 note 判读本体（五轴都不含 note；看断言是否漏掉这第五样）
    A = mkdoc(mk_rows())
    B = mkdoc(mk_rows())
    B["rows"][2]["note"] = "改判读口径：人工判检索结果，非完成断言"
    run("5_only_note", A, B,
        {"a": {"implementation_sha256": I0, "eval_script_sha256": E0},
         "b": {"implementation_sha256": I0, "eval_script_sha256": E0},
         "crossed_design_cells_actually_executed": []},
        "只改 note 判读本体（报告 §1(e)#5 列为独立变更面）：看机检是否检测得到")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
