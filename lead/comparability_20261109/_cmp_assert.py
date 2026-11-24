# -*- coding: utf-8 -*-
r"""_cmp_assert.py — 可比性机检断言（只审计/只设计，不改任何语料/脚本/产物）。

用法：
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/comparability_20261109/_cmp_assert.py \
      <A.json> <B.json> [--manifest <manifest.json>] [--out <out.json>]

五条轴线（四要素 + 输入/度量口径）：
  S 样本集     = 每行 (id, text_head 的 sha256, tokens, family) 的冻结集合
  G 真值标注   = id -> expect（另把 note 作为「判读依据」单独报告）
  I 被测实现   = manifest 提供的 chain/algorithm sha256（JSON 本身不携带）
  E 评测脚本   = manifest 提供的 regression script sha256 + 依赖 sha256（JSON 本身不携带）
  M 度量/口径  = 从 rows[] 独立重算 ok/fp/fn 并与声明值比对，锁死评分公式

判据：
  COMPARABLE          = 恰有 1 条轴不同且该轴被显式声明，其余轴指纹齐备且相同
  REPLICATION         = 0 条轴不同（复现校验，不是「改良」比较）
  PARTIALLY_COMPARABLE= 存在非空共有子集，其上 S/G/M 冻结、仅 I 不同；只许报子集范围
  NOT_COMPARABLE      = 2 条及以上轴不同且无 2x2 交叉实测 / 分母不同 / 度量不同
  INDETERMINATE       = 任一轴指纹缺失或不可核验（例如 v1 脚本未留盘）——拒绝出具可比证明

★ 关键纪律：任何指纹缺失都不得判 COMPARABLE。「部分可比」必须同时输出子集范围，
  且不得把子集结论外推为全语料结论。
"""
import argparse
import hashlib
import json
import pathlib
import sys

AXES = ("S", "G", "I", "E", "M")
JUDGE_COLS = ("naive", "r10", "r12", "n13", "chain")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load(p):
    raw = pathlib.Path(p).read_bytes()
    return json.loads(raw.decode("utf-8")), sha(raw), len(raw)


def sample_manifest(d):
    """返回 id -> 冻结身份；text_head 是 90 字截断，故标 text_scope。"""
    out = {}
    for r in d["rows"]:
        canon = json.dumps(
            {"id": r["id"], "text_head": r.get("text_head", ""),
             "tokens": r.get("tokens", []), "family": r.get("family", "")},
            ensure_ascii=False, sort_keys=True).encode("utf-8")
        out[r["id"]] = {"sha256": sha(canon), "text_scope": "text_head[:90]_only",
                        "expect": r.get("expect"), "note": r.get("note", "")}
    return out


def recompute_stat(d):
    st = {}
    for m in JUDGE_COLS:
        ok = fp = fn = 0
        for r in d["rows"]:
            if r[m] == r["expect"]:
                ok += 1
            elif r["expect"] == "PASS":
                fp += 1
            else:
                fn += 1
        st[m] = {"ok": ok, "fp": fp, "fn": fn}
    return st


def metric_signature(d):
    declared = d.get("single_layer_vs_chain", {})
    recomputed = recompute_stat(d)
    consistent = all(declared.get(m) == recomputed[m] for m in JUDGE_COLS)
    n = len(d["rows"])
    catch = sum(1 for r in d["rows"] if r["expect"] == "CATCH")
    return {"rule": "ok=(got==expect); fp=(expect=PASS,got=CATCH); fn=(expect=CATCH,got=PASS)",
            "declared_equals_recomputed": consistent, "n": n,
            "class_balance": {"CATCH": catch, "PASS": n - catch},
            "declared": declared, "recomputed": recomputed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    args = ap.parse_args()

    A, fa, na = load(args.a)
    B, fb, nb = load(args.b)
    man = json.loads(pathlib.Path(args.manifest).read_text(encoding="utf-8")) if args.manifest else {}

    SA, SB = sample_manifest(A), sample_manifest(B)
    GA = {k: v["expect"] for k, v in SA.items()}
    GB = {k: v["expect"] for k, v in SB.items()}
    MA, MB = metric_signature(A), metric_signature(B)

    ids_a, ids_b = set(SA), set(SB)
    common = sorted(ids_a & ids_b)
    only_a, only_b = sorted(ids_a - ids_b), sorted(ids_b - ids_a)

    texts_a = {r["text_head"] for r in A["rows"]}
    texts_b = {r["text_head"] for r in B["rows"]}
    # 文本键对齐：识别「换 id 不换题」的重命名
    head_a = {r["id"]: r["text_head"] for r in A["rows"]}
    head_b = {r["id"]: r["text_head"] for r in B["rows"]}
    toks_a = {r["id"]: r["tokens"] for r in A["rows"]}
    toks_b = {r["id"]: r["tokens"] for r in B["rows"]}
    rename_pairs = [(x, y) for x in only_a for y in only_b
                    if head_a[x] == head_b[y]]

    ra = {r["id"]: r for r in A["rows"]}
    rb = {r["id"]: r for r in B["rows"]}
    sample_diff = {
        "n_a": len(ids_a), "n_b": len(ids_b), "n_common": len(common),
        "ids_only_a": only_a, "ids_only_b": only_b,
        "text_keys_only_a": sorted(texts_a - texts_b),
        "text_keys_only_b": sorted(texts_b - texts_a),
        "text_identical_but_renamed": rename_pairs,
        "text_head_changed_on_common": [i for i in common if ra[i]["text_head"] != rb[i]["text_head"]],
        "tokens_changed_on_common": [i for i in common if ra[i]["tokens"] != rb[i]["tokens"]],
    }
    expect_changes = [{"id": i, "a_expect": GA[i], "b_expect": GB[i],
                       "text_head": ra[i]["text_head"]}
                      for i in common if GA[i] != GB[i]]
    note_changes = [{"id": i, "a_note": SA[i]["note"], "b_note": SB[i]["note"]}
                    for i in common if SA[i]["note"] != SB[i]["note"]]
    single_layer_identical = all(
        all(ra[i][m] == rb[i][m] for m in JUDGE_COLS[:-1]) for i in common)
    chain_changed = [i for i in common if ra[i]["chain"] != rb[i]["chain"]]

    # 严格局域：同 id / 同文本 / 同标注 / 同 tokens（单层输出另作核对）
    strict_ids = [i for i in common if GA[i] == GB[i]
                  and ra[i]["text_head"] == rb[i]["text_head"]
                  and ra[i]["tokens"] == rb[i]["tokens"]]

    # 各轴状态
    axis = {}
    axis["S"] = {"state": "SAME" if (not only_a and not only_b
                                     and not sample_diff["text_head_changed_on_common"]
                                     and not sample_diff["tokens_changed_on_common"]) else "DIFFERENT",
                 "verifiable": True, "fingerprint_a": sha(json.dumps(SA, ensure_ascii=False, sort_keys=True).encode()),
                 "fingerprint_b": sha(json.dumps(SB, ensure_ascii=False, sort_keys=True).encode())}
    axis["G"] = {"state": "SAME" if not expect_changes else "DIFFERENT",
                 "verifiable": True, "fingerprint_a": sha(json.dumps(GA, sort_keys=True).encode()),
                 "fingerprint_b": sha(json.dumps(GB, sort_keys=True).encode())}
    ia = man.get("a", {}).get("implementation_sha256")
    ib = man.get("b", {}).get("implementation_sha256")
    ea = man.get("a", {}).get("eval_script_sha256")
    eb = man.get("b", {}).get("eval_script_sha256")
    axis["I"] = {"state": "UNKNOWN" if (ia is None or ib is None) else ("SAME" if ia == ib else "DIFFERENT"),
                 "verifiable": ia is not None and ib is not None,
                 "fingerprint_a": ia, "fingerprint_b": ib,
                 "note": "回归 JSON 不携带被测实现指纹；须由 manifest 提供，否则拒绝判可比"}
    axis["E"] = {"state": "UNKNOWN" if (ea is None or eb is None) else ("SAME" if ea == eb else "DIFFERENT"),
                 "verifiable": ea is not None and eb is not None,
                 "fingerprint_a": ea, "fingerprint_b": eb,
                 "note": "v1 并集回归脚本未留盘 → E 轴不可核验"}
    # M 只锁「评分公式 + 声明/重算自洽」。分母 n 与类别平衡是 S 的后果，
    # 不重复计为第五根独立轴，否则会把同一次样本集变更算两遍。
    m_same = (MA["rule"] == MB["rule"] and MA["declared_equals_recomputed"]
              and MB["declared_equals_recomputed"])
    axis["M"] = {"state": "SAME" if m_same else "DIFFERENT", "verifiable": True,
                 "fingerprint_a": sha(MA["rule"].encode()),
                 "fingerprint_b": sha(MB["rule"].encode()),
                 "note": ("评分公式相同；分母 n=%d→%d、类别平衡变化归入 S 轴，"
                          "不重复计轴" % (MA["n"], MB["n"]))}

    diff_axes = [k for k in AXES if axis[k]["state"] == "DIFFERENT"]
    unknown_axes = [k for k in AXES if axis[k]["state"] == "UNKNOWN"
                    or not axis[k]["verifiable"]]
    crossed = man.get("crossed_design_cells_actually_executed", [])
    # manifest 与输入文件自洽：同一份输入文件却声明两次实现不同，属证据冲突，
    # 拒绝出具可比证明（fail-closed）。
    manifest_conflict = bool(man) and fa == fb and (
        ia != ib or ea != eb)

    if manifest_conflict:
        verdict = "INDETERMINATE"
        reason = ("两份输入 JSON 字节相同，但 manifest 声明 I/E 轴不同 → 证据冲突，"
                  "拒绝出具可比证明；复现校验须用 a/b 指纹相同的 manifest")
    elif unknown_axes:
        verdict = "INDETERMINATE"
        reason = ("轴 %s 指纹缺失/不可核验，拒绝出具可比证明；"
                  "若补齐 manifest 且其余轴冻结，可重判" % ",".join(unknown_axes))
    elif len(diff_axes) == 0:
        verdict = "REPLICATION"
        reason = "0 轴不同：这是复现校验，不是改良比较；两次结果应逐行一致"
    elif len(diff_axes) == 1 and axis["S"]["state"] == "SAME" and axis["M"]["state"] == "SAME":
        verdict = "COMPARABLE"
        reason = ("恰有 1 轴(%s)不同且 S/G/M 冻结、E 轴指纹齐备：差值可归因到该轴"
                  % diff_axes[0])
    elif len(diff_axes) == 1:
        verdict = "PARTIALLY_COMPARABLE"
        reason = ("1 轴不同但样本集或度量口径也非严格冻结；只允许在共有子集上比较" )
    elif crossed and len(crossed) >= 2 ** len(diff_axes):
        verdict = "COMPARABLE_CROSSED"
        reason = ("%d 轴不同，但 2^%d 个交叉单元格均已实跑：可估主效应与交互项"
                  % (len(diff_axes), len(diff_axes)))
    else:
        verdict = "NOT_COMPARABLE"
        reason = ("%d 轴同时不同(%s)且无 %d 格交叉实测：差值不可归因"
                  % (len(diff_axes), ",".join(diff_axes), 2 ** len(diff_axes)))

    # 共有子集上的配对结论（若未知轴存在，必须标注「未验重跑」）
    subset = {"scope": strict_ids, "n": len(strict_ids),
              "chain_changed_ids": [i for i in strict_ids if i in chain_changed],
              "single_layer_outputs_identical": single_layer_identical}
    for nm, d, ids in ((args.label_a, A, strict_ids), (args.label_b, B, strict_ids)):
        rd = {r["id"]: r for r in d["rows"]}
        subset[nm + "_chain_ok"] = sum(
            1 for i in ids if rd[i]["chain"] == rd[i]["expect"])

    out = {
        "inputs": {args.label_a: {"sha256": fa, "bytes": na, "path": args.a},
                   args.label_b: {"sha256": fb, "bytes": nb, "path": args.b}},
        "manifest_supplied": bool(man),
        "axes": axis, "differing_axes": diff_axes, "unknown_axes": unknown_axes,
        "verdict": verdict, "reason": reason,
        "sample_diff": sample_diff,
        "expect_changes": expect_changes, "n_expect_changes": len(expect_changes),
        "note_changes": note_changes, "n_note_changes": len(note_changes),
        "n_text_head_changes_on_common": len(sample_diff["text_head_changed_on_common"]),
        "n_tokens_changes_on_common": len(sample_diff["tokens_changed_on_common"]),
        "conflicts": {args.label_a: A.get("chain_conflicts_total"),
                      args.label_b: B.get("chain_conflicts_total")},
        "unresolved": {args.label_a: A.get("chain_unresolved_total"),
                       args.label_b: B.get("chain_unresolved_total")},
        "metric": {args.label_a: MA, args.label_b: MB},
        "single_layer_outputs_identical_on_common": single_layer_identical,
        "strict_subset": subset,
        "strict_subset_caveat": ("v1 评测脚本未留盘 → 该子集上「除合成裁决外其余输入相同」"
                                 "仅由输出列推断，未经脚本级复核，标「未验重跑」"),
        "attribution_scope_limit": ("子集结论只覆盖列出的 id，不得外推为全语料结论，"
                                    "也不得外推为「合成链 vs N13 单层」结论"),
    }
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if args.out:
        pathlib.Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
