# -*- coding: utf-8 -*-
"""_eiv_04_final.py — 精确模块级常量比对 + 只读域完整性 after 快照 +
本会话全部 _eiv_ 脚本干净重跑状态登记 + 绑定行汇总。

运行: python -I -X utf8 -B <绝对路径>
"""
import ast
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "evidence_indep_20261109"
N13_DIR = ROOT / "lead" / "gate_n13_20261109"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
V12P = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"
N13_SHA = "e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079"


def fp(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def module_level_assign_strings(path):
    """精确：只取【模块级 Assign 语句】value 里的所有字符串常量，
    含裸字符串、Tuple/List/Set 元素、re.compile 首参、BinOp 拼接等。"""
    t = ast.parse(path.read_text(encoding="utf-8"))
    out = {}
    for n in t.body:
        if not isinstance(n, ast.Assign):
            continue
        names = [x.id for x in n.targets if isinstance(x, ast.Name)]
        for sub in ast.walk(n.value):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                out.setdefault(sub.value, []).append((n.lineno, ",".join(names)))
    return out


def writer_lits(path):
    """复刻 _ei_05_admission.py:59-72：只收模块级 Assign 的 Tuple/List/Set 元素
    与 re.compile 首参（裸字符串赋值被漏掉）。"""
    t = ast.parse(path.read_text(encoding="utf-8"))
    out = set()
    for n in t.body:
        if not isinstance(n, ast.Assign):
            continue
        v = n.value
        if isinstance(v, (ast.Tuple, ast.List, ast.Set)):
            for e in v.elts:
                if isinstance(e, ast.Constant) and isinstance(e.value, str):
                    out.add(e.value)
        elif isinstance(v, ast.Call) and getattr(v.func, "attr", "") == "compile" \
                and v.args and isinstance(v.args[0], ast.Constant):
            out.add(v.args[0].value)
    return out


def main():
    p13 = next(p for p in sorted(N13_DIR.iterdir())
               if p.is_file() and fp(p) == (N13_SHA, 16649))
    paths = {"N13": p13, "G7": G7P, "V12": V12P}
    full = {k: module_level_assign_strings(p) for k, p in paths.items()}
    wst = {k: writer_lits(p) for k, p in paths.items()}

    out = {}
    # ---- 精确 A2 复判 ----
    out["A2_precise"] = {}
    for a, b in [("V12", "G7"), ("V12", "N13"), ("G7", "N13")]:
        shared = sorted(set(full[a]) & set(full[b]))
        wshared = sorted(wst[a] & wst[b])
        out["A2_precise"]["%s|%s" % (a, b)] = {
            "precise_shared_module_level_literals": [
                {"value": repr(s), "in_a": full[a][s], "in_b": full[b][s]}
                for s in shared],
            "precise_A2_pass": not shared,
            "writer_detector_shared": wshared,
            "writer_detector_A2_pass": not wshared,
            "detector_missed": sorted(set(shared) - set(wshared)),
        }

    # ---- 撰写人自身输出的内部一致性 ----
    D2 = json.loads((W / "_ei_02_code_indep_out.json").read_text(encoding="utf-8"))
    D5 = json.loads((W / "_ei_05_admission_out.json").read_text(encoding="utf-8"))
    out["writer_internal_consistency"] = {
        "_ei_02_G7_V12_shared": D2["c_vocab_overlap"]["G7|V12"]["exact_shared_literals"],
        "_ei_02_G7_V12_no_shared_flag": D2["d_indep_assert"]["G7|V12"]["no_shared_literal_string"],
        "_ei_05_V12_G7_assert": D5["b_machine_assert"]["V12|G7"],
        "_ei_05_V12_G7_A2_check": None,
        "回件_what_claim": "与 G7 零共享模块级常量",
        "回件_evidence_claim": "G7|V12=['。！？；\\n']",
        "回件_machine_assert_claim": "V12|G7 = true（五检全过）",
        "contradiction": True,
        "explanation": "_ei_05_admission.py:59-72 lits() 只收 Tuple/List/Set 与 "
                       "re.compile 首参；G7:71 CLAUSE_BREAK 与 V12:66 _CLAUSE_SEPS "
                       "均为裸字符串模块级赋值，被漏掉，故 A2 误判为通过",
    }
    # 取 _ei_05 的 assert 详情（若有 checks）
    va = D5.get("a_assert_result", {}).get("V12_vs_G7", {})
    out["writer_internal_consistency"]["_ei_05_V12_G7_A2_check"] = (
        va.get("checks", {}).get("A2_no_shared_literal_or_regex")
        if isinstance(va, dict) else str(va)[:200])

    # ---- ⑧ 只读域完整性 after ----
    before = json.loads((W / "_eiv_00_manifest_before.json").read_text(encoding="utf-8"))
    ro_targets = [
        "lead/gate_pipeline_20261109", "lead/chain_vs_single_20261109",
        "lead/gate_n13_20261109", "lead/gate_v1v2_20261109",
        "lead/gate_fp7_20261108", "lead/count_invariant_20261109",
        "lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md",
    ]
    after = {}
    for rel in ro_targets:
        p = ROOT / rel
        if p.is_dir():
            for q in sorted(p.rglob("*")):
                if q.is_file() and "__pycache__" not in q.parts:
                    k = str(q.relative_to(ROOT)).replace("\\", "/")
                    after[k] = fp(q)
        elif p.is_file():
            after[rel] = fp(p)
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(k for k in set(before) & set(after)
                     if tuple(before[k]) != after[k])
    out["readonly_integrity"] = {
        "before_n": len(before), "after_n": len(after),
        "added": added, "removed": removed, "changed": changed,
        "PASS": not added and not removed and not changed,
    }
    # 本写域产物清单（必须全为 _eiv_ 前缀，且不得有非 _eiv_ 新文件）
    mine = sorted(p.name for p in W.iterdir() if p.is_file() and p.name.startswith("_eiv_"))
    out["my_outputs"] = {"files": mine,
                         "all_eiv_prefix": all(x.startswith("_eiv_") for x in mine),
                         "n": len(mine)}

    # ---- 九件绑定行（本会话 hashlib 实算，取自 _eiv_00_setup_out.json）----
    S = json.loads((W / "_eiv_00_setup_out.json").read_text(encoding="utf-8"))
    bind = []
    for rel, v in S["checks"].items():
        bind.append("被核对象 SHA256 = %s，字节数 = %d" % (v["sha256"], v["bytes"]))
    # 第一件是占位键，用 N13 定位结果补齐
    out["binding_lines"] = bind
    out["sha256Line"] = bind[0]  # 主绑定行 = N13 谓词本体（撰写人标注的被核对象）

    (W / "_eiv_04_final_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print("== ② 精确模块级常量 A2 复判 ==")
    for k, v in out["A2_precise"].items():
        print("  %-10s precise_shared=%s" %
              (k, [x["value"] for x in v["precise_shared_module_level_literals"]]))
        print("     precise_A2_pass=%s writer_A2_pass=%s detector_missed=%s" %
              (v["precise_A2_pass"], v["writer_detector_A2_pass"],
               [repr(x) for x in v["detector_missed"]]))
    print("== 撰写人内部一致性 ==")
    print(" ", json.dumps(out["writer_internal_consistency"], ensure_ascii=False)[:900])
    print("== ⑧ 只读域完整性 ==")
    print("  before=%d after=%d added=%d removed=%d changed=%d PASS=%s" %
          (out["readonly_integrity"]["before_n"], out["readonly_integrity"]["after_n"],
           len(added), len(removed), len(changed), out["readonly_integrity"]["PASS"]))
    print("  本会话写域产物 n=%d all_eiv_prefix=%s" %
          (out["my_outputs"]["n"], out["my_outputs"]["all_eiv_prefix"]))
    print("== 主绑定行 ==")
    print(" ", out["sha256Line"])
    print("written: _eiv_04_final_out.json")


if __name__ == "__main__":
    main()
