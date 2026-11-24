# -*- coding: utf-8 -*-
r"""_wlv_regress.py — 白名单复核员：独立实现 32 域 / 302 项 / 翻案 5 / 白名单外 0 复算。

独立性声明：
  * 不 import _r9s_regress.py（它会在只读域覆盖写 _r9s_regress_out.json）。
  * 不 import _wl_step1_repro.py（撰写人脚本，避免抄其实现）。
  * 必现要素 token 不用 LOOP_RE 正则抄录：自己解析 lowered 里的 GATE_CODE，
    从 Python 源码 `for k in [...]:\n if k not in t: ...缺要素...` 用 ast 解析列表，
    **且不要求特定变量名 / 特定 P.append 字面模板**，只认 ast.For 的 iter=ast.List
    + 体内含 '缺要素' 字符串常量。
  * 白名单自己从【编排方指纹/任务书】的 5 对硬抄一份（仅作集合对照，不作为语义真值）。
  * 谓词只加载只读域的 _r9s_predicates.py（这是被测对象本身，必须用它，否则测的不是它）。
  * 全部产物只落唯一写域，前缀 _wlv_，不写任何只读域文件。
"""
from __future__ import annotations
import ast, glob, hashlib, importlib.util, json, os, re, sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
RDIR = ROOT / "lead" / "gate_r9sem_20261109"
WDIR = ROOT / "lead" / "whitelist_audit_20261109"
BASELINE_JSON = ROOT / "lead/gate_rejudge32_20261109/_rj_delivery_baseline.json"
MJS_DIR = ROOT / ".zcode/workflow-runs"

# ---- 加载被测谓词（只读域；这是被测对象本身） ----
sys.path.insert(0, str(RDIR))
import _r9s_predicates as R9S  # noqa: E402
import _r9s_samples as SAMPLES  # noqa: E402

print("R9 谓词指纹复算 =", hashlib.sha256(R9S.R9_PATH.read_bytes()).hexdigest(),
      "/", R9S.R9_PATH.stat().st_size, "B")
print("R9 谓词声明     =", R9S.R9_SHA256, "/", R9S.R9_BYTES, "B")

BASE = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
ROWS = BASE["rows"]
MJS = {p.name: p for p in Path(MJS_DIR).glob("*.mjs")}

# ---- 独立提取 GATE_CODE 源码：解 mjs 的 payload.lowered，抓 `const GATE_CODE = [ ... ].join` ----
def extract_gate_code(mjs_path: Path) -> str:
    t = mjs_path.read_text(encoding="utf-8", errors="replace")
    marker = "export const payload = "
    i = t.find(marker)
    if i < 0:
        return ""
    low, _ = json.JSONDecoder().raw_decode(t[i + len(marker):])
    lowered = low.get("lowered", "")
    k = lowered.find("const GATE_CODE = [")
    if k < 0:
        return ""
    # 找 ] .join 的结束（允许换行/空白）
    m = re.search(r"\]\s*\.join", lowered[k:])
    if not m:
        return ""
    body = lowered[k + len("const GATE_CODE = ["): k + m.start()]
    parts = []
    for sm in re.finditer(r'"((?:[^"\\]|\\.)*)"', body):
        try:
            parts.append(json.loads('"' + sm.group(1) + '"'))
        except Exception:
            parts.append(sm.group(1))
    return "\n".join(parts)


# ---- 独立提取必现要素列表（行式实现，不用 _r9s_regress.py 的 LOOP_RE 模板正则） ----
# 逐行扫 GATE_CODE 源码：对每一行里的每个 [ ... ] 尝试 ast.literal_eval；
# 若结果是「非空字符串列表」，且该行是 `for ... in <该列表>:` 形式、
# 其循环体内（后续缩进行）出现含 '缺要素' 的字符串，则认定为必现要素列表。
# 与被测脚本/撰写人脚本的差别：不做整篇 ast.parse（GATE_CODE 含 JS 拼接行，
# 整体不是合法 Python），不做 P.append 字面模板匹配，按行独立解析列表字面量。
def elements_from_gate_src(src: str) -> list[str]:
    lines = src.split("\n")
    out = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("for ") or " in " not in stripped or not stripped.endswith(":"):
            continue
        # 找该行所有形如 [ ... ] 的括号片段（最外层，简单配对）
        for open_i, ch in enumerate(line):
            if ch != "[":
                continue
            depth = 0
            close_i = -1
            for j in range(open_i, len(line)):
                if line[j] == "[":
                    depth += 1
                elif line[j] == "]":
                    depth -= 1
                    if depth == 0:
                        close_i = j
                        break
            if close_i < 0:
                continue
            frag = line[open_i: close_i + 1]
            try:
                val = ast.literal_eval(frag)
            except Exception:
                continue
            if not (isinstance(val, (list, tuple)) and val
                    and all(isinstance(v, str) and v for v in val)):
                continue
            # 该列表是否就是 for 的迭代对象
            if frag not in stripped:
                continue
            # 循环体：后续缩进行，直到缩进回到表头缩进或更浅
            head_indent = len(line) - len(line.lstrip())
            body_has_missing = False
            for nxt in lines[idx + 1:]:
                if not nxt.strip():
                    continue
                ind = len(nxt) - len(nxt.lstrip())
                if ind <= head_indent:
                    break
                if "缺要素" in nxt:
                    body_has_missing = True
                    break
            if not body_has_missing:
                continue
            out.extend(list(val))
    return out


def elements_of(row) -> list[str]:
    p = MJS.get(row["run"])
    if not p:
        return []
    return elements_from_gate_src(extract_gate_code(p))


# ---- 独立复跑 (A) 正负样本 ----
print("\n=== (A) 正负样本独立复跑 ===")
sample_rows = []
for s in SAMPLES.SAMPLES:
    ok, layer, _ = R9S.r9s_element_present(s["text"], s["token"])
    sample_rows.append({"id": s["id"], "expect": s["expect"], "present": ok,
                        "layer": layer, "pass": ok == s["expect"]})
pos_n = sum(1 for x in sample_rows if x["expect"])
neg_n = sum(1 for x in sample_rows if not x["expect"])
pos_pass = sum(1 for x in sample_rows if x["expect"] and x["pass"])
neg_pass = sum(1 for x in sample_rows if not x["expect"] and x["pass"])
print(f"  POS {pos_pass}/{pos_n}  NEG {neg_pass}/{neg_n}  all_pass={pos_pass==pos_n and neg_pass==neg_n}")

# ---- 独立复跑 (C) 32 域全量 ----
# 白名单：本复核员独立抄录任务书点名的 5 对（只作集合对照，不采信其语义）
WHITELIST = {
    ("lead/matrix_ab_ruling_20261109/", "需谁批准"),
    ("lead/matrix_reach_20261109/", "实跑输出"),
    ("lead/n11_wording_fix_20261108/", "改前改后"),
    ("lead/s604_script_gap_20261109/", "脚本存在性"),
    ("lead/s604_script_gap_20261109/", "可重建"),
}
print("\n=== (C) 32 域全量独立复跑 ===")
all_rows, flips, tightens = [], [], []
n_items = 0
for r in ROWS:
    dom = r["domain"]
    mp = ROOT / dom.rstrip("/") / r["main"]
    if not mp.is_file():
        print("  MAIN MISSING:", dom)
        all_rows.append({"domain": dom, "main_missing": True, "elements": [], "per_element": []})
        continue
    text = mp.read_text(encoding="utf-8", errors="replace")
    elems = elements_of(r)
    per = []
    for k in elems:
        ok0, lay0 = R9S.R9.r9_element_present(text, k)
        ok1, lay1, _d = R9S.r9s_element_present(text, k)
        per.append({"token": k, "r9": ok0, "r9_layer": lay0, "r9s": ok1, "r9s_layer": lay1})
        n_items += 1
        if (not ok0) and ok1:
            flips.append({"domain": dom, "token": k, "whitelisted": (dom, k) in WHITELIST})
        if ok0 and (not ok1):
            tightens.append({"domain": dom, "token": k})
    all_rows.append({"domain": dom, "elements": elems, "per_element": per})
    changed = [x for x in per if x["r9"] != x["r9s"]]
    if changed:
        print(f"  {dom:<48} elems={len(elems):2d} changed={json.dumps(changed, ensure_ascii=False)}")

outside = [f for f in flips if not f["whitelisted"]]
no_relax = (len(outside) == 0 and len(flips) == len(WHITELIST)
            and all(f["whitelisted"] for f in flips))
verdict = "PASS" if (pos_pass == pos_n and neg_pass == neg_n and no_relax) else "FAIL"
print(f"\n  ★ n_domains={len(ROWS)}  n_items={n_items}  n_flips={len(flips)}  "
      f"outside_whitelist={len(outside)}  n_tightens={len(tightens)}  "
      f"no_relaxation={no_relax}  VERDICT={verdict}")
for f in flips:
    print(f"     FLIP {f['domain']:<46} {f['token']:<10} whitelisted={f['whitelisted']}")

# 独立提取器结果 vs 编排方 JSON 的逐域 elements 对照（交叉验证提取器本身）
ref = json.loads((RDIR / "_r9s_regress_out.json").read_text(encoding="utf-8"))
mism = []
for a, b in zip(all_rows, ref["domains32"]["rows"]):
    if a.get("elements", []) != b.get("elements", []):
        mism.append((a["domain"], a.get("elements"), b.get("elements")))
print(f"\n  element_extractor_matches_ref = {len(mism)==0}   mismatches={len(mism)}")
for m in mism[:5]:
    print("    MISMATCH", json.dumps(m, ensure_ascii=False)[:300])
print(f"  ref: n_domains={ref['domains32']['n_domains']} n_flips={ref['domains32']['n_flips']} "
      f"outside={len(ref['domains32']['flips_outside_whitelist'])} "
      f"n_tightens={ref['domains32']['n_tightens']} no_relaxation={ref['no_relaxation']} verdict={ref['verdict']}")
print(f"  ref: sum(per_element)={sum(len(x.get('per_element',[])) for x in ref['domains32']['rows'])}")
print(f"  identical_flips = {sorted((f['domain'],f['token']) for f in ref['domains32']['flips']) == sorted((f['domain'],f['token']) for f in flips)}")

# ★ 结构性质：已登记 token 出现次数 / 白名单外次数 / 未登记 token 项数
reg_tokens = set(R9S.SPECS.keys())
reg_occ = 0
reg_outside = []
for row in all_rows:
    for e in row["per_element"]:
        if e["token"] in reg_tokens:
            reg_occ += 1
            if (row["domain"], e["token"]) not in WHITELIST:
                reg_outside.append((row["domain"], e["token"], e["r9"], e["r9s"]))
print(f"\n  registered_tokens={sorted(reg_tokens)}")
print(f"  registered_token_occurrences={reg_occ}  outside_whitelist={len(reg_outside)}")
for x in reg_outside:
    print(f"     {x[0]:<48} {x[1]:<10} r9={x[2]} r9s={x[3]}")
print(f"  unregistered_token_items = {n_items - reg_occ}")

OUT = {"samples": sample_rows, "n_domains": len(ROWS), "n_items": n_items,
       "n_flips": len(flips), "outside_whitelist": len(outside),
       "n_tightens": len(tightens), "no_relaxation": no_relax, "verdict": verdict,
       "flips": flips, "registered_occurrences": reg_occ,
       "registered_outside": [list(x) for x in reg_outside],
       "element_extractor_matches_ref": len(mism) == 0,
       "all_rows": all_rows}
(WDIR / "_wlv_regress_out.json").write_text(
    json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\nWROTE _wlv_regress_out.json")
