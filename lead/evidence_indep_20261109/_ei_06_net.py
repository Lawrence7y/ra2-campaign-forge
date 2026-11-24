# -*- coding: utf-8 -*-
"""_ei_06_net.py — net-benefit sweep over 4th-layer rescue triggers and
V1V2 verdict filters, on the full 74-row corpus. Quantifies step 3(c) exactly.
python -I -X utf8 -B <abs path>
"""
import hashlib
import importlib.util
import json
import pathlib
import re
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "evidence_indep_20261109"
N13_DIR = ROOT / "lead" / "gate_n13_20261109"
N13_SHA = "e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079"
N13_N = 16649


def fp(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def load(p, name):
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    p13 = next(p for p in N13_DIR.iterdir() if p.is_file() and fp(p) == (N13_SHA, N13_N))
    n13 = load(p13, "_ei_net_n13")
    v12 = load(ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py", "_ei_net_v12")
    e4 = load(W / "_ei_04_v12_layer.py", "_ei_net_e4")
    reg = load(ROOT / "lead" / "gate_n13_20261109" / "_n13_regression.py", "_ei_net_reg")
    C = e4.build_corpus(n13, reg)
    sys.path.insert(0, str(ROOT / "lead" / "gate_pipeline_20261109"))
    import _gp_pipeline as P
    O = json.loads((ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression_out.json")
                   .read_text(encoding="utf-8"))
    ref = {r["id"]: r for r in O["rows"]}
    D4 = json.loads((W / "_ei_04_v12_layer_out.json").read_text(encoding="utf-8"))
    v12row = {r["id"]: r for r in D4["rows"]}
    T = list(n13.DEFAULT_TOKENS)

    # per-row V12 detail: which V2 spans, whether any is a hard override (not DEFAULT)
    def v12_detail(text):
        hits = []
        for tok in sorted(set(list(v12.V2_OVERRIDE) + T), key=len, reverse=True):
            for m in re.finditer(re.escape(tok), text):
                c = v12.classify_v12(text, m.start(), m.end(), tok)
                if c["verdict"] == "V2":
                    hits.append({"token": tok, "override": c["override"],
                                 "review": c["review_flag"], "hard": c["hard"]})
        return {"catch": bool(hits), "hard_override": any(h["override"] for h in hits),
                "only_default": bool(hits) and all(h["review"] for h in hits),
                "hits": hits}

    rows = []
    for it in C:
        rid = it["id"]
        v = ref[rid]
        text = it["text"]
        d = v12_detail(text)
        ext = P.extract_spans(text, it["tokens"])
        rows.append({"id": rid, "expect": v["expect"], "base": v["chain"],
                     "spans": ext["count"],
                     "all_pass": all(v[k] == "PASS" for k in ("r10", "r12", "n13")),
                     "v12": "CATCH" if d["catch"] else "PASS",
                     "hard_override": d["hard_override"],
                     "only_default": d["only_default"],
                     "v12_hits": d["hits"]})

    def sc(finals):
        ok = sum(1 for r, f in zip(rows, finals) if r["expect"] == f)
        fp = sum(1 for r, f in zip(rows, finals) if r["expect"] == "PASS" and f == "CATCH")
        fn = sum(1 for r, f in zip(rows, finals) if r["expect"] == "CATCH" and f == "PASS")
        return {"correct": ok, "fp": fp, "fn": fn, "acc": ok / len(rows),
                "delta_correct": ok - 69, "delta_errors": (fp + fn) - 5}

    variants = {}
    # baseline
    variants["0_baseline_chain"] = [r["base"] for r in rows]
    # 1: naive OR of all 4 layers
    variants["1_naive_OR_all4"] = ["CATCH" if r["base"] == "CATCH" or r["v12"] == "CATCH" else "PASS"
                                   for r in rows]
    # 2: monotone rescue triggered by spans==0 OR all3PASS
    variants["2_monotone_spans0_or_allPASS"] = [
        "CATCH" if r["base"] == "CATCH" or
        ((r["spans"] == 0 or r["all_pass"]) and r["v12"] == "CATCH") else "PASS" for r in rows]
    # 3: monotone rescue triggered only by spans==0 (the dead-K7 blind spot)
    variants["3_monotone_spans0_only"] = [
        "CATCH" if r["base"] == "CATCH" or (r["spans"] == 0 and r["v12"] == "CATCH") else "PASS"
        for r in rows]
    # 4: spans==0 AND hard V2_OVERRIDE only (exclude DEFAULT fail-closed review flags)
    variants["4_monotone_spans0_hard_override"] = [
        "CATCH" if r["base"] == "CATCH" or
        (r["spans"] == 0 and r["v12"] == "CATCH" and r["hard_override"]) else "PASS" for r in rows]
    # 5: all3PASS AND hard_override only
    variants["5_monotone_allPASS_hard_override"] = [
        "CATCH" if r["base"] == "CATCH" or
        (r["all_pass"] and r["v12"] == "CATCH" and r["hard_override"]) else "PASS" for r in rows]
    # 6: spans==0 OR all3PASS, hard_override only
    variants["6_monotone_gated_hard_override"] = [
        "CATCH" if r["base"] == "CATCH" or
        ((r["spans"] == 0 or r["all_pass"]) and r["v12"] == "CATCH" and r["hard_override"])
        else "PASS" for r in rows]

    out = {"n": len(rows),
           "spans0_ids": [r["id"] for r in rows if r["spans"] == 0],
           "all_pass_ids": [r["id"] for r in rows if r["all_pass"]],
           "variants": {k: sc(v) for k, v in variants.items()}}
    for k, v in variants.items():
        s = out["variants"][k]
        s["rescued_fn"] = [r["id"] for r, f in zip(rows, v)
                           if r["base"] == "PASS" and f == "CATCH" and r["expect"] == "CATCH"]
        s["new_fp"] = [r["id"] for r, f in zip(rows, v)
                       if r["base"] == "PASS" and f == "CATCH" and r["expect"] == "PASS"]
        s["new_fn"] = [r["id"] for r, f in zip(rows, v)
                       if r["base"] == "CATCH" and f == "PASS" and r["expect"] == "CATCH"]
    # GP-A1/A2/A3 V12 detail
    out["GP_A_v12_detail"] = [{"id": r["id"], **{k: r[k] for k in
                               ("spans", "all_pass", "v12", "hard_override", "only_default", "v12_hits")}}
                              for r in rows if r["id"].startswith("GP-A")]
    # holdout (20 unseen) V12 from read-only _cs_holdout_out.json
    H = json.loads((ROOT / "lead" / "chain_vs_single_20261109" / "_cs_holdout_out.json")
                   .read_text(encoding="utf-8"))["unseen"]
    hv = {"n": len(H),
          "v12_correct": sum(1 for r in H if r["expect"] == r["v12"]),
          "v12_fp": sum(1 for r in H if r["expect"] == "PASS" and r["v12"] == "CATCH"),
          "v12_fn": sum(1 for r in H if r["expect"] == "CATCH" and r["v12"] == "PASS"),
          "source": "lead/chain_vs_single_20261109/_cs_holdout_out.json (read-only, 20 rows)"}
    out["holdout_v12"] = hv
    (W / "_ei_06_net_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
