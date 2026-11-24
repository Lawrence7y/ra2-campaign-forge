# -*- coding: utf-8 -*-
r"""_gp_probe.py — 三层谓词现状复核（编排任务第一步）。
只读加载 _g7_predicates.py / _n13_predicates.py / _g9_gate.py，指纹先验（hashlib）。
对三件真实交付件逐件跑 naive / R9 / R10 / R12 / N13(含 R10+R12 注入) / R11，
并做逐 span 对齐，导出冲突面。零真机、零采样；只读保护件，写只落本写域。

实跑命令：
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_probe.py
"""
import hashlib
import importlib.util
import inspect
import json
import pathlib
import sys

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_pipeline_20261109"
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
N13 = ROOT / "lead" / "gate_n13_20261109" / "_n13_predicates.py"
G9 = ROOT / "lead" / "gate_r9r12_20261109" / "_g9_gate.py"

EXPECT = {
    G7: ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    N13: ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649),
    G9: ("a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6", 11623),
}


def load(path, name):
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    exp_sha, exp_n = EXPECT[path]
    if sha != exp_sha or len(raw) != exp_n:
        raise RuntimeError("指纹失配 %s = %s/%d ≠ %s/%d" % (path, sha, len(raw), exp_sha, exp_n))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, (sha, len(raw))


g7, fp_g7 = load(G7, "_gp_g7")
n13, fp_n13 = load(N13, "_gp_n13")

REAL = [
    ("C07_SLOT", ROOT / "lead" / "c07_slot_20261109" / "C07_IDENTITY_SLOT.md"),
    ("TRUTH", ROOT / "lead" / "c07_truth_protocol_20261109" / "C07_TRUTH_SELF_PROOF.md"),
    ("BOUND", ROOT / "lead" / "ledger_bound_20261109" / "LEDGER_BOUND_VOLUME.md"),
]

# 三套词表口径：N13 自带三词 / BAD_BAN 五词（g7 探针族）/ C07 身份词表
TOK_N13 = list(n13.DEFAULT_TOKENS)
TOK_BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
# 编排方 C07 口径（_v12_probe.py:15-18 逐字）：两域各自词表
TOK_C07_SLOT = ["已补登", "已填入", "已填", "已代填"]
TOK_C07_TRUTH = ["已填", "已代填", "已提交"]
REQ = ["被核对象", "SHA256", "字节数"]

out = {
    "fingerprints": {str(G7.relative_to(ROOT)): list(fp_g7),
                     str(N13.relative_to(ROOT)): list(fp_n13)},
    "contracts": {}, "files": {}, "token_probe": {},
}

# ---- (a) 输入/输出契约：签名 + 文档串 + 返回类型实测 ----
for mod, names in ((g7, ("naive_gate", "r9_check", "r10_scan", "r12_scan", "r11_scan")),
                   (n13, ("r13_scan", "r13_assertions"))):
    for n in names:
        f = getattr(mod, n)
        out["contracts"][n] = {
            "module": mod.__name__,
            "signature": str(inspect.signature(f)),
            "doc_first_line": (f.__doc__ or "").strip().splitlines()[0],
        }

# 返回类型实测（单件小文本，避免全量输出）
demo = "被核对象 SHA256 = " + "a" * 64 + "，字节数 = 12\n本笔已入账。"
rets = {}
rets["naive_gate"] = [type(x).__name__ for x in (g7.naive_gate(demo, REQ),)]
rets["r9_check"] = [type(x).__name__ for x in g7.r9_check(demo, REQ)]
rets["r10_scan"] = [type(x).__name__ for x in g7.r10_scan(demo, TOK_N13)]
rets["r12_scan"] = [type(x).__name__ for x in g7.r12_scan(demo, TOK_N13)]
rets["r11_scan"] = [type(x).__name__ for x in g7.r11_scan(demo, WD, root=ROOT)]
rets["r13_scan"] = [type(x).__name__ for x in n13.r13_scan(demo, TOK_N13, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)]
rets["r13_assertions"] = [type(x).__name__ for x in n13.r13_assertions(demo, TOK_N13, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)]
out["contracts"]["_return_container_types_demo"] = rets
out["contracts"]["_demo_problems"] = {
    "r10": g7.r10_scan(demo, TOK_N13)[0],
    "r13": n13.r13_assertions(demo, TOK_N13, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)[0],
}


def layer_run(text, tokens, doc_dir):
    p9, w9 = g7.r9_check(text, REQ)
    p10, w10, h10 = g7.r10_scan(text, tokens)
    p12, h12 = g7.r12_scan(text, tokens)
    p11, w11, b11 = g7.r11_scan(text, doc_dir, root=ROOT)
    p13, d13 = n13.r13_assertions(text, TOK_N13, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    return {"R9": {"problems": p9, "warnings": w9},
            "R10": {"problems": p10, "warnings": w10, "hits": h10},
            "R12": {"problems": p12, "hits": h12},
            "R11": {"problems": p11, "warnings": w11,
                    "bindings": [{"path": b.get("path"), "match": b.get("match")} for b in b11]},
            "N13": {"problems": p13, "details": d13}}


def conflicts(text, tokens):
    """逐 span 对齐：以 (token, pos) 为键，收集 R10 kind / R12 / N13 kind。
    N13 拆分裂缝命中 pos=-1 单独记。返回 PASS/CATCH 不一致的清单。"""
    p10, w10, h10 = g7.r10_scan(text, tokens)
    p12, h12 = g7.r12_scan(text, tokens)
    _, d13 = n13.r13_assertions(text, TOK_N13, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    r10map = {(h["token"], h["pos"]): h for h in h10}
    r12set = {(h["token"], h["pos"]) for h in h12}
    rows, splits = [], []
    for d in d13:
        k = (d["token"], d["pos"])
        if k in r10map or k in r12set or d["pos"] == -1:
            r10kind = r10map.get(k, {}).get("kind")
            # 统一成 catch 布尔：R10 抓住 = assertion 或 double_neg；放过 = negation/quote_mention
            r10_catch = None if r10kind is None else r10kind in ("assertion", "double_neg")
            r12_catch = k in r12set
            n13_catch = d["kind"] == "D"
            rec = {"token": d["token"], "pos": d["pos"], "line": d["line"],
                   "quote": d["quote"][:140], "r10_kind": r10kind,
                   "r10_catch": r10_catch, "r10_pass": (None if r10_catch is None else not r10_catch),
                   "r12_catch": r12_catch,
                   "n13_kind": d["kind"], "n13_catch": n13_catch,
                   "n13_rule": d["rule"],
                   "differ": (r10_catch is not None and r10_catch != n13_catch)
                             or (r12_catch and not n13_catch)}
            if d["pos"] == -1:
                splits.append(rec)
            else:
                rows.append(rec)
    # N13 没有逐处记录、但 R10 报 assertion/double_neg 的 span（词表口径差）
    only_r10 = []
    for h in h10:
        k = (h["token"], h["pos"])
        if k not in {(d["token"], d["pos"]) for d in d13}:
            only_r10.append({"token": h["token"], "pos": h["pos"], "kind": h["kind"],
                             "reason": "该 token 不在 N13 DEFAULT_TOKENS 三词内 或 N13 逐处漏记"})
    return {"aligned": rows, "split_hits": splits, "only_r10_hits": only_r10,
            "conflict_count": sum(1 for r in rows if r["differ"]),
            "aligned_count": len(rows),
            "r10_only_count": len(only_r10)}


for tag, p in REAL:
    raw = p.read_bytes()
    text = raw.decode("utf-8")
    sha = hashlib.sha256(raw).hexdigest()
    rec = {"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha, "bytes": len(raw),
           "crlf": raw.count(b"\r\n"), "lines": len(text.splitlines())}
    # 词表寻迹：三种词表各自 naive 命中 + R10 problems
    probe = {}
    c07_toks = {"C07_SLOT": TOK_C07_SLOT, "TRUTH": TOK_C07_TRUTH}.get(tag, None)
    for tname, toks in (("N13_3", TOK_N13), ("BAD_BAN_5", TOK_BAD_BAN),
                        ("C07_task", c07_toks)):
        if toks is None:
            continue
        naive_hits = [t for t in toks if t in text]
        pp, ww, hh = g7.r10_scan(text, toks)
        kinds = {}
        for h in hh:
            kinds[h["kind"]] = kinds.get(h["kind"], 0) + 1
        probe[tname] = {"naive_hits": naive_hits, "r10_problems": len(pp), "r10_kinds": kinds,
                        "r12_problems": len(g7.r12_scan(text, toks)[0]),
                        "occurrences": len(hh)}
    rec["token_probe"] = probe
    # 逐件逐层结果（三条口径都跑：BAD_BAN 五词 / N13 三词 / 编排方 C07 词表）
    runs = [("BAD_BAN_5", TOK_BAD_BAN), ("N13_3", TOK_N13)]
    if c07_toks is not None:
        runs.append(("C07_task", c07_toks))
    for tname, toks in runs:
        r = layer_run(text, toks, p.parent)
        rec["layers_" + tname] = {
            "R9_problems": r["R9"]["problems"], "R9_warnings": r["R9"]["warnings"],
            "R10_problems": r["R10"]["problems"], "R10_warnings_n": len(r["R10"]["warnings"]),
            "R10_kinds": {k: sum(1 for h in r["R10"]["hits"] if h["kind"] == k)
                          for k in ("assertion", "negation", "quote_mention", "double_neg")},
            "R12_problems": r["R12"]["problems"],
            "R11_problems": r["R11"]["problems"], "R11_bindings": r["R11"]["bindings"],
            "N13_problems": r["N13"]["problems"],
            "N13_kinds": {k: sum(1 for d in r["N13"]["details"] if d["kind"] == k)
                          for k in ("A", "B", "C", "D")},
        }
    # 冲突面对齐（N13 三词口径：只有这三词能被两层共同逐处判）
    rec["conflicts_N13_3"] = conflicts(text, TOK_N13)
    rec["conflicts_BAD_BAN_5"] = conflicts(text, TOK_BAD_BAN)
    if c07_toks is not None:
        rec["conflicts_C07_task"] = conflicts(text, c07_toks)
    out["files"][tag] = rec
    out["token_probe"][tag] = probe

(WD / "_gp_probe_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

# ---- 控制台摘要 ----
print("== 指纹 ==")
for k, v in out["fingerprints"].items():
    print(" ", k, v)
print("\n== (a) 契约 ==")
for k, v in out["contracts"].items():
    print(" ", k, "=>", v if not k.startswith("_") else json.dumps(v, ensure_ascii=False))
for tag, rec in out["files"].items():
    print("\n== (b) 件 %s (%s, %d B) ==" % (tag, rec["path"], rec["bytes"]))
    print("  token_probe:", json.dumps(rec["token_probe"], ensure_ascii=False))
    for tn in ["BAD_BAN_5", "N13_3"] + (["C07_task"] if c07_toks is not None else []):
        L = rec["layers_" + tn]
        print("  -- 口径 %s: R9pro=%d R10pro=%d kinds=%s R12pro=%d R11pro=%d N13pro=%d kinds=%s" %
              (tn, len(L["R9_problems"]), len(L["R10_problems"]), L["R10_kinds"],
               len(L["R12_problems"]), len(L["R11_problems"]), len(L["N13_problems"]),
               L["N13_kinds"]))
        for x in L["N13_problems"][:12]:
            print("       N13:", x[:150])
        if len(L["N13_problems"]) > 12:
            print("       ... N13 共 %d 条" % len(L["N13_problems"]))
    for cn in ("conflicts_N13_3", "conflicts_BAD_BAN_5", "conflicts_C07_task"):
        if cn not in rec:
            continue
        c = rec[cn]
        print("  -- 冲突 %s: aligned=%d differ=%d split=%d only_r10=%d" %
              (cn, c["aligned_count"], c["conflict_count"], len(c["split_hits"]), c["r10_only_count"]))
        for r in c["aligned"]:
            if r["differ"]:
                print("       DIFFER pos=%d L%d tok=%s r10=%s(r10_catch=%s) r12=%s n13=%s(%s) | %s" %
                      (r["pos"], r["line"], r["token"], r["r10_kind"], r["r10_catch"],
                       r["r12_catch"], r["n13_kind"], r["n13_catch"], r["quote"][:70]))
        for r in c["split_hits"][:10]:
            print("       SPLIT L%d tok=%s r10=%s n13=%s | %s" %
                  (r["line"], r["token"], r["r10_kind"], r["n13_kind"], r["quote"][:70]))
print("\nwritten:", WD / "_gp_probe_out.json")
