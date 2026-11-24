# -*- coding: utf-8 -*-
r"""_gpv_probe.py — 独立复核员自写探针：自己 import 两个谓词模块，实跑三件真件。
不采信 _gp_probe_out.* 任何数字；独立实现逐 span 冲突面统计（两个方向都数）。
只读；输出只写本写域 _gpv_ 前缀文件。零真机、零采样。
"""
import hashlib
import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_pipeline_20261109"
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
N13 = ROOT / "lead" / "gate_n13_20261109" / "_n13_predicates.py"

EXP = {G7: ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
       N13: ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649)}


def load(path, name):
    raw = path.read_bytes()
    got = (hashlib.sha256(raw).hexdigest(), len(raw))
    if got != EXP[path]:
        raise RuntimeError("谓词指纹失配 %s" % path)
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m, got


g7, fp7 = load(G7, "_gpv_g7")
n13, fp13 = load(N13, "_gpv_n13")
T3 = list(n13.DEFAULT_TOKENS)
BAD5 = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
C07S = {"C07_SLOT": ["已补登", "已填入", "已填", "已代填"],
        "TRUTH": ["已填", "已代填", "已提交"]}
REQ = ["被核对象", "SHA256", "字节数"]

REAL = [("C07_SLOT", ROOT / "lead/c07_slot_20261109/C07_IDENTITY_SLOT.md"),
        ("TRUTH", ROOT / "lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md"),
        ("BOUND", ROOT / "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md")]


def spans_of(text, tokens):
    """独立提取：finditer 全量，键 (token,pos)。"""
    out = []
    for t in tokens:
        for m in re.finditer(re.escape(t), text):
            out.append((t, m.start()))
    return out


def conflicts_both_ways(text, r10_tokens, n13_tokens):
    """返回两个方向的逐 span 冲突明细 + 只 R10 有答案的 span 数。"""
    p10, w10, h10 = g7.r10_scan(text, r10_tokens)
    p12, h12 = g7.r12_scan(text, r10_tokens)
    p13, d13 = n13.r13_assertions(text, n13_tokens,
                                  r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    r10map = {(h["token"], h["pos"]): h for h in h10}
    r12set = {(h["token"], h["pos"]) for h in h12}
    dmap = {(d["token"], d["pos"]): d for d in d13 if d["pos"] >= 0}
    splits = [d for d in d13 if d["pos"] == -1]

    def catch_r10(kind):
        return kind in ("assertion", "double_neg") if kind is not None else None

    forward, reverse, only_r10 = [], [], []
    for k in spans_of(text, r10_tokens):
        h = r10map.get(k)
        d = dmap.get(k)
        rc = catch_r10(h["kind"] if h else None)
        nc = (d["kind"] == "D") if d else None
        rec = {"token": k[0], "pos": k[1], "r10_kind": h["kind"] if h else None,
               "r10_catch": rc, "r12_catch": k in r12set,
               "n13_kind": d["kind"] if d else "ABSENT", "n13_catch": nc,
               "n13_rule": d["rule"] if d else "",
               "line": text.count("\n", 0, k[1]) + 1}
        if d is None:
            only_r10.append(rec)
        elif rc is True and nc is False:
            forward.append(rec)      # R10 抓住 / N13 放过
        elif rc is False and nc is True:
            reverse.append(rec)      # R10 放过 / N13 抓住
    return {"forward_R10catch_N13pass": forward,
            "reverse_R10pass_N13catch": reverse,
            "only_r10": only_r10,
            "split_D_hits": [{"line": d["line"], "token": d["token"],
                              "quote": d["quote"][:90], "rule": d["rule"]} for d in splits],
            "counts": {"R10_problems": len(p10), "R12_problems": len(p12),
                       "N13_problems": len(p13),
                       "R10_kinds": {kk: sum(1 for h in h10 if h["kind"] == kk)
                                     for kk in ("assertion", "negation", "quote_mention", "double_neg")},
                       "N13_kinds": {kk: sum(1 for d in d13 if d["kind"] == kk)
                                     for kk in ("A", "B", "C", "D")},
                       "R9_problems": len(g7.r9_check(text, REQ)[0]),
                       "spans_total": len(spans_of(text, r10_tokens)),
                       "forward_n": len(forward), "reverse_n": len(reverse),
                       "only_r10_n": len(only_r10), "split_D_n": len(splits)}}


result = {"fingerprints": {str(G7.relative_to(ROOT)): list(fp7),
                           str(N13.relative_to(ROOT)): list(fp13)},
          "files": {}}
for tag, p in REAL:
    raw = p.read_bytes()
    text = raw.decode("utf-8")
    rec = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
           "crlf": raw.count(b"\r\n"), "lines": len(text.splitlines()),
           "vocab_runs": {}}
    c07 = C07S.get(tag)
    runs = [("N13_3__N13_3", T3, T3), ("BAD5__N13_3", BAD5, T3)]
    if c07:
        runs.append(("C07__N13_3", c07, T3))     # 回件口径：N13 固定三词
        runs.append(("C07__C07", c07, c07))      # 额外：N13 强喂 C07 词表
    for label, rtok, ntok in runs:
        rec["vocab_runs"][label] = conflicts_both_ways(text, rtok, ntok)
    # 独立跑 R11（BOUND 报 1 条「引用锚指向不在盘对象」是否复现）
    p11, w11, b11 = g7.r11_scan(text, p.parent, root=ROOT)
    rec["R11"] = {"problems": p11, "warnings_n": len(w11), "bindings_n": len(b11),
                  "null_path_n": sum(1 for b in b11 if b.get("path") is None)}
    result["files"][tag] = rec

(WD / "_gpv_probe_out.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

print("== 独立探针：两模块指纹 ==")
for k, v in result["fingerprints"].items():
    print(" ", k, v)
for tag, rec in result["files"].items():
    print("\n== %s sha=%s bytes=%d crlf=%d lines=%d ==" %
          (tag, rec["sha256"], rec["bytes"], rec["crlf"], rec["lines"]))
    for label, c in rec["vocab_runs"].items():
        s = c["counts"]
        print("  %-14s R9pro=%d R10pro=%d kinds=%s R12pro=%d N13pro=%d kinds=%s "
              "spans=%d 正向(R10抓/N13放)=%d 反向(R10放/N13抓)=%d only_r10=%d splitD=%d" %
              (label, s["R9_problems"], s["R10_problems"], s["R10_kinds"], s["R12_problems"],
               s["N13_problems"], s["N13_kinds"], s["spans_total"], s["forward_n"],
               s["reverse_n"], s["only_r10_n"], s["split_D_n"]))
        for x in c["reverse_R10pass_N13catch"]:
            print("      REVERSE pos=%d L%d tok=%s r10=%s n13=%s | %s" %
                  (x["pos"], x["line"], x["token"], x["r10_kind"], x["n13_kind"], x["n13_rule"][:70]))
        for x in c["forward_R10catch_N13pass"]:
            print("      FORWARD pos=%d L%d tok=%s r10=%s n13=%s | %s" %
                  (x["pos"], x["line"], x["token"], x["r10_kind"], x["n13_kind"], x["n13_rule"][:70]))
    print("  R11: problems=%s warnings=%d bindings=%d null_path=%d" %
          (rec["R11"]["problems"], rec["R11"]["warnings_n"], rec["R11"]["bindings_n"],
           rec["R11"]["null_path_n"]))
print("\nwritten:", WD / "_gpv_probe_out.json")
