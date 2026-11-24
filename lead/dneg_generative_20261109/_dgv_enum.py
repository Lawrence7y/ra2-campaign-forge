# -*- coding: utf-8 -*-
r"""_dgv_enum.py — 独立复核⑥：项目内其它「枚举式正则」清单，自己重新搜，不采信作者清单。
两种独立判据：
  (i) 源码行级：含 re.compile/re.findall 且该行字面串里 ≥4 个中文选择支；
  (ii) AST 级：解析所有 .py 的 re.compile 第一个参数（常量字符串），统计 | 分隔的中文支，
      可抓跨行拼接与作者行级判据漏掉的形态。
零真机、零采样；纯静态文本 + ast；输出只落写域。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dgv_enum.py
"""
import sys, json, re, ast
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path("D:/Project/ra2-campaign-forge/lead")
WD = ROOT / "dneg_generative_20261109"
ZH = re.compile(r"[\u4e00-\u9fff]")

# ---------- (i) 行级（作者 _dg_step5c.py 的同口径，独立实现）----------
line_hits = []
for p in sorted(ROOT.rglob("*.py")):
    try: t = p.read_text("utf-8", errors="ignore")
    except Exception: continue
    for i, line in enumerate(t.splitlines(), 1):
        if "re.compile" not in line and "re.findall" not in line:
            continue
        for m in re.finditer(r"[rRuUbBfF]*([\"'])(.{20,600}?)\1", line):
            s = m.group(2)
            parts = [x.strip() for x in s.split("|") if x.strip()]
            zh = [x for x in parts if ZH.search(x)]
            if len(zh) >= 4:
                line_hits.append({"file": str(p.relative_to(ROOT)).replace("\\", "/"),
                                  "line": i, "n_zh": len(zh), "sample": " | ".join(zh[:6]),
                                  "raw": line.strip()[:160]})
                break
seen, line_uniq = set(), []
for r in line_hits:
    k = (r["file"], r["line"])
    if k in seen: continue
    seen.add(k); line_uniq.append(r)
line_uniq.sort(key=lambda x: -x["n_zh"])

# ---------- (ii) AST 级（独立、更严）----------
def const_str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = const_str(node.left), const_str(node.right)
        if a is not None and b is not None: return a + b
    if isinstance(node, ast.JoinedStr):
        out = ""
        for v in node.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str): out += v.value
            else: return None
        return out
    return None

ast_hits = []
for p in sorted(ROOT.rglob("*.py")):
    try: t = p.read_text("utf-8", errors="ignore")
    except Exception: continue
    try: tree = ast.parse(t)
    except SyntaxError: continue
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call): continue
        f = n.func
        is_re = (isinstance(f, ast.Attribute) and f.attr in ("compile", "findall", "search", "match", "finditer")
                 and isinstance(f.value, ast.Name) and f.value.id == "re")
        if not is_re or not n.args: continue
        s = const_str(n.args[0])
        if s is None: continue
        # 忽略分组里的 (?:...) 干扰，只数纯中文/词组选择支
        parts = [x.strip("()?:^$ \t") for x in s.split("|")]
        zh = [x for x in parts if ZH.search(x) and len(x) <= 30]
        if len(zh) >= 4:
            ast_hits.append({"file": str(p.relative_to(ROOT)).replace("\\", "/"),
                             "line": n.lineno, "n_zh": len(zh),
                             "sample": " | ".join(zh[:8]),
                             "pattern_head": s[:120]})
ast_uniq, seen2 = [], set()
for r in ast_hits:
    k = (r["file"], r["line"])
    if k in seen2: continue
    seen2.add(k); ast_uniq.append(r)
ast_uniq.sort(key=lambda x: -x["n_zh"])

print("=== ⑥ 独立重搜：行级判据（≥4 中文选择支）===")
print("  命中行数 =", len(line_uniq))
for r in line_uniq[:45]:
    print("  %3d %s:%d  %s" % (r["n_zh"], r["file"], r["line"], r["sample"][:76]))
print("\n=== ⑥ 独立重搜：AST 判据（≥4 中文选择支，可跨行）===")
print("  命中调用数 =", len(ast_uniq))
for r in ast_uniq[:45]:
    print("  %3d %s:%d  %s" % (r["n_zh"], r["file"], r["line"], r["sample"][:76]))

# 作者点名清单逐条核对是否在本次独立结果内
FOCUS = ["gate_fp7_20261108/_g7_predicates.py:69", "gate_fp7_20261108/_g7_predicates.py:76",
         "gate_n13_20261109/_n13_pasteable.py:14", "gate_n13_20261109/_n13_pasteable.py:23",
         "gate_v1v2_20261109/_v12_rule.py:38", "gate_v1v2_20261109/_v12_rule.py:43",
         "h5_governance_20261109/_h5_pasteable.py:55", "h5_governance_20261109/_h5_pasteable.py:59",
         "h5_governance_20261109/_h5_pasteable.py:65",
         "re_line_20261105/W7_W4_REVIEW/_w7_c.py:236",
         "refsync_scope_20261109/_rs_markers.py:30"]
line_set = {(r["file"], r["line"]) for r in line_uniq}
ast_set = {(r["file"], r["line"]) for r in ast_uniq}
print("\n=== ⑥ 作者点名 11 处逐条核对 ===")
focus_rows = []
for f in FOCUS:
    fp, ln = f.rsplit(":", 1); ln = int(ln)
    p = ROOT / fp
    exists = p.is_file()
    src = p.read_text("utf-8", errors="ignore").splitlines()[ln-1].strip()[:110] if exists and ln <= len(p.read_text("utf-8", errors="ignore").splitlines()) else ""
    r = {"ref": f, "exists": exists, "src": src,
         "in_line_hits": (fp, ln) in line_set, "in_ast_hits": (fp, ln) in ast_set}
    focus_rows.append(r)
    print("  %-62s exists=%-5s line_hit=%-5s ast_hit=%-5s | %s" %
          (f, exists, r["in_line_hits"], r["in_ast_hits"], src[:70]))

# 与作者 _dg_step5c_out.json 数字对照
claim = json.loads((WD / "_dg_step5c_out.json").read_text("utf-8"))
print("\n=== ⑥ 与作者申报对照 ===")
print("  作者 _dg_step5c_out.json n =", claim["n"])
print("  本复核 行级 n =", len(line_uniq), " AST n =", len(ast_uniq))
print("  作者 68 处是否可复现：", "是（行级同口径）" if len(line_uniq) == claim["n"] else "否：%d vs %d" % (len(line_uniq), claim["n"]))

out = {"line_hits": line_uniq, "line_n": len(line_uniq),
       "ast_hits": ast_uniq, "ast_n": len(ast_uniq),
       "focus": focus_rows, "author_n": claim["n"]}
(WD / "_dgv_enum_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dgv_enum_out.json")
