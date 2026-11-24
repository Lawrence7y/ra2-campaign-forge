# -*- coding: utf-8 -*-
"""_sl_run10.py — 在 F2-d 十条真实无路径绑定行上逐条跑同文档联查（第三步验证）。

十条清单 = lead/f2d_rootcause_20261109/F2D_ROOT_CAUSE.md §2.3（条 1—10），
另附 2 条编排方提取件多出的无路径行位（不在十条清单，见 §2.2-4）作对照：
  附加A lead/b2b_isolated_20261107/INTEGRATION_REPORT.md:147（:148 紧邻行有路径，F2D 排除）
  附加B lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md:6（「母本 SHA256 =」无
        「被核对象」前缀，BIND_RE（_g7_predicates.py:152）不命中，非绑定行）

每条先做两道守卫再联查：①五件现盘 hashlib 重算对照 F2D §2.1 记录前缀+字节数（漂移守卫）；
②行位实读照录、hex 与预期值逐位比对（对齐守卫）。只读；输出落本写域 _sl_run10_out.json。"""

import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(r"D:\Project\ra2-campaign-forge\lead\samedoc_link_20261109")
REPO = Path(r"D:\Project\ra2-campaign-forge")

spec = importlib.util.spec_from_file_location("_sl_link_mod", HERE / "_sl_link.py")
sl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sl)

MOTHER = "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636"
CAND = "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2"
SPEC = "cb4f3011a75f616032524814cba9c05e055ca41636836f7e3a15d6d876e8d306"
R1 = "3343cfbe467d38f442cd9e422e691d0123fc046938c4d242f57c629bd41d4125"

A_RESIDUAL = REPO / r"lead\a_residual_n1_20261108\A_RESIDUAL_REFERENCES.md"
INTEG_REP = REPO / r"lead\b2b_isolated_20261107\INTEGRATION_REPORT.md"
INTEG_EXEC = REPO / r"lead\b2b_isolated_20261107\_integ_INTEGRATION_REPORT.md"
B_EXEC = REPO / r"lead\bexec_n4_20261108\B_EXECUTION_SPEC.md"
N4_SPEC = REPO / r"lead\bexec_n4_20261108\_n4_SPEC_N4_B2B_MATRIX.md"

# F2D_ROOT_CAUSE.md:48 五证据件指纹（前缀+字节数，漂移守卫）
DOC_FP = {A_RESIDUAL: ("1209ca4c", 33431), INTEG_REP: ("65463431", 24022),
          INTEG_EXEC: ("9742f2cc", 15179), B_EXEC: ("be733335", 32183),
          N4_SPEC: ("cb4f3011", 22136)}

# (条号, doc, 行号, 预期hex, 预期字节数)
TEN = [
    ("条1", A_RESIDUAL, 130, R1, 26435),
    ("条2", INTEG_REP, 31, CAND, 412759),
    ("条3", INTEG_EXEC, 5, CAND, 412759),
    ("条4", B_EXEC, 51, MOTHER, 399508),
    ("条5", B_EXEC, 52, CAND, 412759),
    ("条6", B_EXEC, 53, SPEC, 22136),
    ("条7", B_EXEC, 228, MOTHER, 399508),
    ("条8", B_EXEC, 229, CAND, 412759),
    ("条9", N4_SPEC, 28, MOTHER, 399508),
    ("条10", N4_SPEC, 29, CAND, 412759),
]
EXTRA = [
    ("附加A", INTEG_REP, 147, CAND, 412759),
    ("附加B", INTEG_EXEC, 6, MOTHER, 399508),
]

HEX_RE = re.compile(r"[0-9a-fA-F]{64}")


def run_one(tag, doc, line_no, exp_hex, exp_bytes):
    rec = {"tag": tag, "doc": str(doc.relative_path if False else doc), "line": line_no}
    rec["doc"] = str(doc)
    raw = doc.read_bytes()
    sha_doc = hashlib.sha256(raw).hexdigest()
    pref, nbytes = DOC_FP[doc]
    rec["doc_sha12"] = sha_doc[:12]
    rec["doc_drift_guard"] = "MATCH" if (sha_doc.startswith(pref) and len(raw) == nbytes) \
        else "DRIFT(%s…/%d ≠ %s…/%d)" % (sha_doc[:8], len(raw), pref, nbytes)
    lines = raw.decode("utf-8").splitlines()
    line = lines[line_no - 1]
    rec["line_excerpt"] = line[:110]
    hexes = HEX_RE.findall(line)
    rec["hex_align_guard"] = "MATCH" if (hexes and hexes[0].lower() == exp_hex) \
        else "MISMATCH(%s vs %s)" % (hexes[:1], exp_hex[:12])
    bm = sl.BYTES_RE.search(line)
    bytes_decl = int(sl._COMMA.sub("", bm.group(1))) if bm else None
    rec["bytes_decl"] = bytes_decl
    r = sl.link(raw.decode("utf-8"), doc.parent, exp_hex, bytes_decl)
    rec["verdict"] = r["verdict"]
    rec["anchors"] = [{"path": a["path"], "sha12": a["sha"][:12], "size": a["size"],
                       "tokens": [(t["token"], t["lines"]) for t in a["tokens"]]}
                      for a in r["anchors"]]
    rec["reverify"] = r["reverify"]
    rec["declared_but_mismatched"] = r["declared_but_mismatched"]
    rec["stats"] = r["stats"]
    rec["warning"] = r["warning"]
    return rec


def main():
    all_recs = []
    for tag, doc, ln, hexv, nb in TEN + EXTRA:
        rec = run_one(tag, doc, ln, hexv, nb)
        all_recs.append(rec)
    ten = [r for r in all_recs if r["tag"].startswith("条")]
    extra = [r for r in all_recs if r["tag"].startswith("附加")]

    def short(p, n=58):
        p = str(p)
        return p if len(p) <= n else "…" + p[-n:]

    print("=" * 100)
    print("同文档联查 · F2-d 十条真实验证（谓词 _sl_link.py；判据：唯一命中才采）")
    print("=" * 100)
    for rec in all_recs:
        print("\n[%s] %s:%d" % (rec["tag"], Path(rec["doc"]).name, rec["line"]))
        print("  漂移守卫: %s | hex对齐: %s | 声明字节数: %s" %
              (rec["doc_drift_guard"], rec["hex_align_guard"], rec["bytes_decl"]))
        print("  行照录: %s" % rec["line_excerpt"])
        print("  判定: %s" % rec["verdict"])
        for a in rec["anchors"]:
            print("  锚: %s（sha %s… / %d B）tokens=%s" %
                  (short(a["path"]), a["sha12"], a["size"], a["tokens"]))
        if rec["reverify"]:
            print("  回验: ok=%s（现盘 %s…/%d B）" %
                  (rec["reverify"]["ok"], rec["reverify"]["sha"][:12],
                   rec["reverify"]["bytes"]))
        for d in rec["declared_but_mismatched"]:
            print("  [辅助·粗粒度] 同行声明不符: %s（%s…/%d B，hex 行 %s）" %
                  (short(d["path"]), d["sha12"], d["size"], d["hex_near_lines"]))
        print("  warning: %s" % rec["warning"])

    closed = [r for r in ten if r["verdict"] == "unique" and r["reverify"] and r["reverify"]["ok"]]
    multi = [r for r in ten if r["verdict"] == "multi"]
    zero = [r for r in ten if r["verdict"] == "zero"]
    uniq_bad = [r for r in ten if r["verdict"] == "unique" and not (r["reverify"] and r["reverify"]["ok"])]
    print("\n" + "=" * 100)
    print("统计（F2-d 十条）: 自动闭合(唯一命中且回验 MATCH) = %d/10；多命中放弃 = %d 条 %s；"
          "零命中保留 R3-3b = %d 条 %s；唯一命中但回验失配 = %d 条"
          % (len(closed), len(multi), [r["tag"] for r in multi],
             len(zero), [r["tag"] for r in zero], len(uniq_bad)))
    print("调查件口径（F2D_ROOT_CAUSE.md:238）: 9/10 可自动闭合，唯一例外 = 条1（r1 不在盘）。")
    diff = [r["tag"] for r in multi]
    if len(closed) == 9 and not multi:
        print("与 9/10 口径一致。")
    else:
        print("与 9/10 口径的差异：多命中条 = %s（该条对象在盘且哈希对，但同文档存在另一"
              "同 hash 不同路径项，按「唯一命中才采」放弃）" % (diff if diff else "无"))
    print("附加对照行位判定: " + "; ".join("%s→%s" % (r["tag"], r["verdict"]) for r in extra))
    out = HERE / "_slv_run10copy_out.json"
    out.write_text(json.dumps({"ten": all_recs}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("机读件已落盘: %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
