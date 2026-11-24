# -*- coding: utf-8 -*-
r"""_wl_step1_repro.py — 白名单独立审查 / 第一步基线复核。

只做只读复算：加载只读域 lead/gate_r9sem_20261109/ 的 _r9s_predicates.py 与
_r9s_samples.py，独立重跑 (A) 正负样本 (B) 4 域 (C) 32 域 / 302 项翻案。
不调用 _r9s_regress.py（它会覆盖写只读域内的 _r9s_regress_out.json）。
白名单在脚本里独立硬抄一份，用于验证「白名单外 0」的自证结构。

产物：_wl_step1_out.json / _wl_step1_stdout.txt（全部落唯一写域）。
"""
from __future__ import annotations
import ast, glob, hashlib, importlib.util, json, os, re, sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "whitelist_audit_20261109"
RDIR = ROOT / "lead" / "gate_r9sem_20261109"
sys.path.insert(0, str(RDIR))
import _r9s_predicates as R9S
import _r9s_samples as S

BASE = json.loads((ROOT / "lead/gate_rejudge32_20261109/_rj_delivery_baseline.json")
                  .read_text(encoding="utf-8"))
ROWS = BASE["rows"]
RUNS = {os.path.basename(p): p for p in glob.glob(str(ROOT / ".zcode/workflow-runs/*.mjs"))}

LOOP_RE = re.compile(
    r"for (\w+) in (\[[^\]]+\]):\n\s*if \1 not in t: P\.append\('缺要素 '\+\1\)"
)

def gate_src(low: str) -> str:
    k = low.find("const GATE_CODE = [")
    end = low.find("].join", k)
    if k < 0 or end < 0: return ""
    body = low[k + len("const GATE_CODE = ["):end]
    parts = []
    for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', body):
        try: parts.append(json.loads('"' + m.group(1) + '"'))
        except Exception: parts.append(m.group(1))
    return "\n".join(parts) if parts else ""

def elements_of(r) -> list[str]:
    p = RUNS.get(r["run"]); elems = []
    if p:
        t = Path(p).read_text(encoding="utf-8", errors="replace")
        i = t.find("export const payload = ")
        if i >= 0:
            low, _ = json.JSONDecoder().raw_decode(t[i + len("export const payload = "):])
            src = gate_src(low.get("lowered", ""))
            for m in LOOP_RE.finditer(src):
                try: elems += ast.literal_eval(m.group(2))
                except Exception: pass
    return [x for x in elems if x]

# 独立硬抄白名单（与 _r9s_regress.py:113-119 同值，用于复现其判定）
WHITELIST = {
    ("lead/matrix_ab_ruling_20261109/", "需谁批准"),
    ("lead/matrix_reach_20261109/", "实跑输出"),
    ("lead/n11_wording_fix_20261108/", "改前改后"),
    ("lead/s604_script_gap_20261109/", "脚本存在性"),
    ("lead/s604_script_gap_20261109/", "可重建"),
}

OUT = {"r9_pred_sha256": R9S.R9_SHA256,
       "r9_pred_recomputed": hashlib.sha256(R9S.R9_PATH.read_bytes()).hexdigest(),
       "baseline_sha256": hashlib.sha256((ROOT / "lead/gate_rejudge32_20261109/_rj_delivery_baseline.json").read_bytes()).hexdigest(),
       "spec_inventory": R9S.spec_inventory()}

print("=== (A) 正负样本集（POS=%d NEG=%d）===" % (len(S.POS), len(S.NEG)))
sample_rows = []
for s in S.SAMPLES:
    ok, layer, _ = R9S.r9s_element_present(s["text"], s["token"])
    hit = (ok == s["expect"])
    sample_rows.append({"id": s["id"], "token": s["token"], "expect": s["expect"],
                        "present": ok, "layer": layer, "pass": hit, "why": s["why"],
                        "text": s["text"]})
    print("  %-4s %-6s expect=%-5s actual=%-5s layer=%-10s %s" %
          (s["id"], s["token"], s["expect"], ok, layer or "(none)", "PASS" if hit else "**FAIL**"))
pos_n = sum(1 for x in sample_rows if x["expect"])
neg_n = sum(1 for x in sample_rows if not x["expect"])
pos_pass = sum(1 for x in sample_rows if x["expect"] and x["pass"])
neg_pass = sum(1 for x in sample_rows if not x["expect"] and x["pass"])
OUT["samples"] = {"rows": sample_rows, "positive": pos_n, "negative": neg_n,
                  "positive_pass": pos_pass, "negative_pass": neg_pass,
                  "all_pass": pos_pass == pos_n and neg_pass == neg_n}
print("  → POS %d/%d  NEG %d/%d  all_pass=%s" % (pos_pass, pos_n, neg_pass, neg_n, OUT["samples"]["all_pass"]))

# (C) 32 域
print("\n=== (C) 32 域全量：R9 → R9S 逐要素翻案 ===")
all_rows, flips, tightens = [], [], []
for r in ROWS:
    dom = r["domain"]
    mp = ROOT / dom.rstrip("/") / r["main"]
    if not mp.is_file():
        all_rows.append({"domain": dom, "main_missing": True}); print("  %-46s MAIN MISSING" % dom); continue
    text = mp.read_text(encoding="utf-8", errors="replace")
    elems = elements_of(r)
    per = []
    for k in elems:
        ok0, lay0 = R9S.R9.r9_element_present(text, k)
        ok1, lay1, _d = R9S.r9s_element_present(text, k)
        per.append({"token": k, "r9_present": ok0, "r9_layer": lay0,
                    "r9s_present": ok1, "r9s_layer": lay1})
        if (not ok0) and ok1:
            flips.append({"domain": dom, "token": k, "whitelisted": (dom, k) in WHITELIST, "main": r["main"]})
        if ok0 and (not ok1):
            tightens.append({"domain": dom, "token": k, "main": r["main"], "r9_layer": lay0})
    all_rows.append({"domain": dom, "main": r["main"], "elements": elems, "per_element": per})
    changed = [x for x in per if x["r9_present"] != x["r9s_present"] or x["r9_layer"] != x["r9s_layer"]]
    print("  %-46s elems=%d changed=%s" % (dom, len(elems), json.dumps(
        [{"t": x["token"], "r9": x["r9_present"], "r9s": x["r9s_present"], "l1": x["r9s_layer"]} for x in changed], ensure_ascii=False)))
n_items = sum(len(x["per_element"]) for x in all_rows)
OUT["domains32"] = {"n_domains": len(ROWS), "n_items": n_items, "rows": all_rows,
                    "flips": flips, "n_flips": len(flips), "tightens": tightens,
                    "n_tightens": len(tightens),
                    "flips_outside_whitelist": [f for f in flips if not f["whitelisted"]],
                    "whitelist": [list(x) for x in sorted(WHITELIST)]}
OUT["no_relaxation"] = (len([f for f in flips if not f["whitelisted"]]) == 0
                        and len(flips) == len(WHITELIST) and all(f["whitelisted"] for f in flips))
print("\n  n_domains=%d n_items=%d n_flips=%d outside_whitelist=%d n_tightens=%d no_relaxation=%s" %
      (len(ROWS), n_items, len(flips), len([f for f in flips if not f["whitelisted"]]),
       len(tightens), OUT["no_relaxation"]))
for f in flips:
    print("     FLIP %-46s %-12s whitelisted=%s" % (f["domain"], f["token"], f["whitelisted"]))

# 把编排方 JSON 的对应数字也读出来做交叉比对
p = RDIR / "_r9s_regress_out.json"
ref = json.loads(p.read_text(encoding="utf-8"))
OUT["cross_check_ref"] = {
    "ref_samples_all_pass": ref["samples"]["all_pass"],
    "ref_positive": ref["samples"]["positive"], "ref_negative": ref["samples"]["negative"],
    "ref_n_domains": ref["domains32"]["n_domains"], "ref_n_flips": ref["domains32"]["n_flips"],
    "ref_outside": len(ref["domains32"]["flips_outside_whitelist"]),
    "ref_n_tightens": ref["domains32"]["n_tightens"],
    "ref_no_relaxation": ref["no_relaxation"], "ref_verdict": ref["verdict"],
    "ref_main_missing": [x["domain"] for x in ref["domains32"]["rows"] if x.get("main_missing")],
}
print("\n=== cross-check against _r9s_regress_out.json ===")
print(json.dumps(OUT["cross_check_ref"], ensure_ascii=False, indent=1))
print("  identical_flips = %s" % ([sorted((f["domain"], f["token"]) for f in ref["domains32"]["flips"])] ==
                                [sorted((f["domain"], f["token"]) for f in flips)]))

(WDIR / "_wl_step1_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\nWROTE _wl_step1_out.json")

# ---------- 出口改造（纯追加：以上 1-144 行与原件逐字节一致，未改一字）----------
# 原型：lead/dtrigger_compare_20261107/_check_dtrigger.py:31-35 + :226-228
#
# A. 原件「对自身的检查」与现有输出通道（本会话逐行实读 + AST 实核）：
#    :73       hit = (ok == s["expect"])（逐样本复算：谓词结果是否合期望）
#    :77-78    print(..., "PASS" if hit else "**FAIL**") —— 唯一互斥裁决对（E0/GA2）
#    :83-86    OUT["samples"]["all_pass"] → :86 print(... all_pass=%s)
#    :118-122  OUT["no_relaxation"] → :120-122 print(... no_relaxation=%s)
#    :126-141  cross-check → :140-141 print("  identical_flips = %s" % (...))
#              比较本件 flips 与派发件 _r9s_regress_out.json 的 flips 是否逐项同集
#    通道：以上全部 stdout print；:143 OUT 写盘 _wl_step1_out.json（产物通道，含
#          samples.all_pass / no_relaxation / cross_check_ref）；:144 print("WROTE ...")。
#          全件无 assert、无 sys.exit/SystemExit/raise、无 __main__ 守卫
#          （AST：Assert=0 / Raise=0 / 守卫=0 / 顶层 def 仅 gate_src,elements_of）。
#    不纳入聚合：:69/:89 标题、:110-111 逐域 elems/changed、:123-124 FLIP 清单、
#          :138-139 参考读数 JSON —— 均为领域观测，原件未给二值裁决；
#          取反塞进合取会改掉原件判定（同库 _w2v_probe2.py:122-123 口径）。
#
# B/C. 纯追加（C1）：不删/不改/不重排任何原件行，不新增任何 import。
#    原件无 __main__ 块；全库实 grep 无 import 本件的 Python 语句（仅
#          _wlv_fingerprints.py:44 路径串、_wlv_regress.py:6 明言「不 import」、
#          台账/文档引用）⇒ 无被别的脚本 import 的库本体，C2 不适用。
#    C3 从严：不新增任何模块级名字。ok 是原件 :72 已有模块级名，仅在全文末尾
#          重新赋值，其后无原件语句、无调用方 ⇒ 不遮蔽/覆盖任何调用方同名符号；
#          不定义 check（避免新增全局名、避免重写 :77-78 必须逐字保留的打印）。
#          采用同库 _se_enum.py:351-358 / _g7_reverse_validate.py:179-182 的
#          「ok = True + 多条 ok = ok and bool(cond)」纯追加形态。
#    cond 逐字复用原件已算出并已打印的三个自检布尔，不取反、不新增、不重跑；
#    三个布尔原值原样打印/原样写盘均不变 ⇒ 不改语义。模板「各项检查改为
#    check(...)」需改 :77-78 等原件行、与 C1 冲突，故改为末尾合取聚合，
#    聚合语义（全部通过才真）与模板一致。
ok = True
ok = ok and bool(OUT["samples"]["all_pass"])     # 原件 :85/:86；涵盖 :73/:78 全部 hit
ok = ok and bool(OUT["no_relaxation"])           # 原件 :118-122
ok = ok and bool(                                # 原件 :140-141 identical_flips 同一式
    [sorted((f["domain"], f["token"]) for f in ref["domains32"]["flips"])] ==
    [sorted((f["domain"], f["token"]) for f in flips)])
print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
raise SystemExit(0 if ok else 1)
