# -*- coding: utf-8 -*-
r"""_h5_regress.py — H5 补丁回归：旧 vs 修后逐处对照。

跑法：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/h5_governance_20261109/_h5_regress.py
输出：_h5_regress_out.json / _h5_regress_out.txt（只落本任务写域）

三个尺度：
  A. 编排方九条样本（独立复核，逐条 expect/old/new）
  B. 自建样本集 POS 18 + NEG 26（correct / fp / fn）
  C. 32 域现盘 26 处字面命中（读真件 + baseline，不 import 撰写人脚本）
"""
import sys, json, hashlib, importlib.util, re
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RULE = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"
BASELINE = ROOT / "lead" / "gate_rejudge32_20261109" / "_rj_delivery_baseline.json"
SHADOW = ROOT / "lead" / "v12_impact_20261109" / "_vi_shadow_out.json"


def _import(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


OLD = _import("_h5_old_rule", RULE)
NEW = _import("_h5_new_rule", HERE / "_h5_v12_patched.py")   # 由 _h5_patch.py 生成
SAMPLES = _import("_h5_sample_data", HERE / "_h5_samples.py").SAMPLES


def run(mod, text, token):
    p = text.find(token)
    r = mod.classify_v12(text, p, p + len(token), token)
    return {"verdict": r["verdict"], "hard": r["hard"], "weak": r["weak"],
            "override": r["override"], "review": r["review_flag"],
            "unit": r["unit"], "reason": r["reason"]}


def decision(r):
    return "PASS" if r["verdict"] == "V1" else "CATCH"


def score(rows, key):
    correct = sum(1 for x in rows if x[key] == x["expect"])
    fp = sum(1 for x in rows if x["expect"] == "PASS" and x[key] == "CATCH")
    fn = sum(1 for x in rows if x["expect"] == "CATCH" and x[key] == "PASS")
    return {"correct": correct, "fp": fp, "fn": fn, "total": len(rows)}


def main():
    out = {"fingerprints": {}, "A_nine": [], "B_samples": [], "C_26": [],
           "B_score": {}, "A_score": {}}
    lines = []

    for label, p in [("_v12_rule.py", RULE),
                     ("_h5_v12_patched.py", HERE / "_h5_v12_patched.py"),
                     ("_rj_delivery_baseline.json", BASELINE),
                     ("_vi_shadow_out.json", SHADOW)]:
        b = p.read_bytes()
        out["fingerprints"][label] = {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}

    # ---------- A 九条 ----------
    NINE = [
      ("REGRESS1", "本笔已入账 0 命中不得写成未入账", "已入账", "应CATCH"),
      ("REGRESS2", "审阅不得不承认本候选已生效。", "已生效", "应CATCH"),
      ("CTRL_OK",  "本件已生效，可应用母本", "已生效", "应CATCH"),
      ("TRUE_NEG", "本节登记不宣告 N-4 正式绑定已生效", "已生效", "应PASS"),
      ("TRAIL_NEG","已入账不得重复登记", "已入账", "应CATCH"),
      ("LEAD_NEG", "不得写成已入账", "已入账", "应PASS"),
      ("DOUBLE_1", "并非不宣告已生效", "已生效", "应CATCH"),
      ("DOUBLE_2", "不能不说本笔已入账", "已入账", "应CATCH"),
      ("DOUBLE_3", "无不认为本件已生效", "已生效", "应CATCH"),
    ]
    lines.append("=== A 编排方九条（old vs patched） ===")
    for cid, text, tok, exp in NINE:
        o, n = run(OLD, text, tok), run(NEW, text, tok)
        row = {"id": cid, "text": text, "token": tok, "expect": exp.replace("应", ""),
               "old": decision(o), "new": decision(n),
               "old_raw": o, "new_raw": n}
        out["A_nine"].append(row)
        lines.append("%-10s exp=%-5s old=%-5s new=%-5s  old_hard=%r new_ov=%r" %
                     (cid, row["expect"], row["old"], row["new"],
                      o["hard"], n["override"]))
    out["A_score"] = {"old": score([dict(x, old=x["old"]) | {"v": x["old"]} for x in out["A_nine"]], "old"),
                      "new": score([dict(x, new=x["new"]) | {"v": x["new"]} for x in out["A_nine"]], "v")}

    # ---------- B 自建样本集 ----------
    lines.append("")
    lines.append("=== B 自建样本集（POS %d / NEG %d） ===" %
                 (sum(1 for s in SAMPLES if s["expect"] == "PASS"),
                  sum(1 for s in SAMPLES if s["expect"] == "CATCH")))
    for s in SAMPLES:
        o, n = run(OLD, s["text"], s["token"]), run(NEW, s["text"], s["token"])
        row = dict(s)
        row.update({"old": decision(o), "new": decision(n),
                    "old_hard": o["hard"], "new_ov": n["override"],
                    "old_verdict": o["verdict"], "new_verdict": n["verdict"],
                    "new_hard": n["hard"]})
        out["B_samples"].append(row)
        flag = "" if row["new"] == row["expect"] else "  <<< WRONG"
        lines.append("%-5s %-5s %-30s old=%-5s new=%-5s%s" %
                     (s["id"], s["expect"], s["subcat"][:28], row["old"], row["new"], flag))
    out["B_score"] = {"old": score([dict(x, v=x["old"]) for x in out["B_samples"]], "v"),
                      "new": score([dict(x, v=x["new"]) for x in out["B_samples"]], "v")}
    lines.append("SCORE old = %s" % json.dumps(out["B_score"]["old"], ensure_ascii=False))
    lines.append("SCORE new = %s" % json.dumps(out["B_score"]["new"], ensure_ascii=False))

    # ---------- C 32 域现盘 26 处 ----------
    lines.append("")
    lines.append("=== C 32 域现盘 26 处（旧 vs 修后，逐处） ===")
    bl = json.loads(BASELINE.read_text(encoding="utf-8"))
    sh = json.loads(SHADOW.read_text(encoding="utf-8"))
    # 以 shadow 留盘的 26 处 (domain,pos,token) 为准，真件现盘重算
    dom_by_name = {d["domain"]: d for d in sh["rows"]}
    counts = {"old_V1": 0, "new_V1": 0, "changed": 0, "baseline_fp_mismatch": 0}
    for r in bl["rows"]:
        dom, main, bans = r["domain"], r["main"], r["params"].get("banned", [])
        path = ROOT / dom / main
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        rec0 = dom_by_name.get(dom)
        fp_ok = (hashlib.sha256(raw).hexdigest() == r["mainSha256"]
                 and len(raw) == r["mainBytes"])
        if not fp_ok:
            counts["baseline_fp_mismatch"] += 1
        hit_specs = [(h["pos"], h["token"]) for h in (rec0["hits"] if rec0 else [])]
        for pos, tok in hit_specs:
            # 必须用原 pos（同 token 可能在文中多次出现）
            def at(mod):
                rr = mod.classify_v12(text, pos, pos + len(tok), tok)
                return {"verdict": rr["verdict"], "hard": rr["hard"],
                        "override": rr["override"], "weak": rr["weak"],
                        "review": rr["review_flag"], "unit": rr["unit"]}
            o, n = at(OLD), at(NEW)
            assert text[pos:pos + len(tok)] == tok, (dom, pos, tok)
            row = {"domain": dom, "main": main, "pos": pos, "token": tok,
                   "baseline_fp_match": fp_ok,
                   "old": o["verdict"], "new": n["verdict"],
                   "old_hard": o["hard"], "new_hard": n["hard"],
                   "new_override": n["override"], "unit": n["unit"][:120]}
            out["C_26"].append(row)
            counts["old_V1"] += o["verdict"] == "V1"
            counts["new_V1"] += n["verdict"] == "V1"
            if o["verdict"] != n["verdict"]:
                counts["changed"] += 1
                lines.append("  CHANGED %s pos=%d tok=%s %s→%s U=%r" %
                             (dom, pos, tok, o["verdict"], n["verdict"], n["unit"][:90]))
            lines.append("  %-42s pos=%-6d %-10s old=%s new=%s hard_old=%r" %
                         (dom, pos, tok, o["verdict"], n["verdict"], o["hard"]))
    out["C_counts"] = counts
    lines.append("C counts = %s" % json.dumps(counts, ensure_ascii=False))

    (HERE / "_h5_regress_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "_h5_regress_out.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[-8:]))
    print("A old =", out["A_score"]["old"], " A new =", out["A_score"]["new"])
    print("B old =", out["B_score"]["old"], " B new =", out["B_score"]["new"])
    print("C =", counts)
    print("written: _h5_regress_out.json / _h5_regress_out.txt")


if __name__ == "__main__":
    main()
