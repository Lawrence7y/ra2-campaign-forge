# -*- coding: utf-8 -*-
# _cs_holdout.py : 过拟合检测方法实跑演示（不改谓词/不改语料，只在写域内造【未见变体】）
#   - 从 N13 自家 42 条出发，做「同义/形态扰动」生成未见样本，人工给 expect
#   - 对比 N13 单层 / chain / V1V2 独立谓词在未见样本上的表现
#   - 半定量估计「三层都过」的有效独立层数
import os, sys, json, pathlib, importlib.util, hashlib, re, collections
ROOT = r"D:\Project\ra2-campaign-forge"
os.chdir(ROOT)
WD = pathlib.Path(ROOT) / "lead" / "gate_pipeline_20261109"
N13_PATH = WD.parent / "gate_n13_20261109" / "_n13_predicates.py"
G7_PATH = WD.parent / "gate_fp7_20261108" / "_g7_predicates.py"
V12_PATH = WD.parent / "gate_v1v2_20261109" / "_v12_rule.py"

def _load(path, name, want=None):
    raw = path.read_bytes()
    if want:
        assert (hashlib.sha256(raw).hexdigest(), len(raw)) == want
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

g7 = _load(G7_PATH, "_cs_h_g7", ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743))
n13 = _load(N13_PATH, "_cs_h_n13", ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649))
v12 = _load(V12_PATH, "_cs_h_v12", ("15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0", 9148))
sys.path.insert(0, str(WD))
import _gp_pipeline as P
R10FN = g7.r10_scan
T = list(n13.DEFAULT_TOKENS)

# ---- 未见变体：由 N13 自家 42 条的形态做「扰动」，不在任何回归语料中 ----
# (id, text, expect, 扰动类别, 由哪条母本启发)
UNSEEN = [
    # 正样本扰动：把 A/B/C 标记换成同义/变体，语义仍应放行
    ("U-P01", "### 1(c) 有没有已追加的？", "PASS", "问句 + 换 token（P01 启发）"),
    ("U-P02", "**已生效核查实跑命令**：", "PASS", "核查动作标签 + 换 token（P05 启发）"),
    ("U-P03", "## 2 · 上游指纹 + 已追加 grep 结果", "PASS", "小节标题 + 换 token（P03 启发）"),
    ("U-P04", "| 笔 | 已追加? |", "PASS", "表头问询列名 + 换 token（P12 启发）"),
    ("U-P05", "  - 有没有已生效的？台账确认 = 0 命中。", "PASS", "缩进列表 + 换 token（P11 启发）"),
    ("U-P06", "不追加 N-4 正式绑定已生效。", "PASS", "否定式 + 换否定词（P08 启发）"),
    ("U-P07", "**不得写成「本笔已入账」**；本件只登记。", "PASS", "禁止 + 引证 + 换 token（P13 启发）"),
    ("U-P08", "### 3 已生效检索结果（清单）", "PASS", "标题清单 + 换 token（P15 启发）"),
    # 负样本扰动：换主语 / 换标记 / 换位置，语义仍是真断言
    ("U-N01", "此笔已于 §706 入账。", "CATCH", "换主语「此笔」+ 换节号（N01 启发）"),
    ("U-N02", "本回件已生效，可应用母本", "CATCH", "换主语「本回件」（N04 启发）"),
    ("U-N03", "该条已追加至台账尾部。", "CATCH", "换主语「该条」（N05 启发）"),
    ("U-N04", "第 8 笔已生效。", "CATCH", "换序号 + 换 token（N06 启发）"),
    ("U-N05", "未核 grep 结果：本笔已入账", "CATCH", "前置未核标签 + 主语（N19/V1 启发）"),
    ("U-N06", "检索结果：第 7 笔已追加", "CATCH", "A 标记同义改写「检索结果」（N20 启发）"),
    ("U-N07", "§2 清单 / 该笔已生效 / §3 依赖", "CATCH", "斜杠微段 + 换主语（N21 启发）"),
    ("U-N08", "grep 结果：此条已追加", "CATCH", "A 标记 + 换主语「此条」（N23 启发）"),
    ("U-N09", "核查清单：已生效核验 0 命中，但本件已入账", "CATCH", "检索 + 转折真断言（N18 启发）"),
    ("U-N10", "本件登记闭合，母本即日起适用", "CATCH", "词表外同义完成断言（GP-A2 同形）"),
    ("U-N11", "三值填毕，见证已由编排方签字", "CATCH", "词表外同义完成断言（GP-A3 同形）"),
    ("U-N12", "亦非不宣告 N-4 正式绑定已生效", "CATCH", "分离型双重否定（GP-A1 同形）"),
]

def n13v(text, toks=T):
    p, _ = n13.r13_assertions(text, toks, r10_scan=R10FN, r12_scan=g7.r12_scan)
    return "CATCH" if p else "PASS"

def chainv(text, toks=T):
    r = P.gate_check(text, toks, WD, g7, n13, T)
    return "CATCH" if any(p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN") for p in r["problems"]) else "PASS"

def v12v(text):
    """V1V2 独立谓词：任一 V2_OVERRIDE 词族 span 被判 V2 ⇒ CATCH"""
    for tok in set(list(v12.V2_OVERRIDE) + list(T)):
        for m in re.finditer(re.escape(tok), text):
            c = v12.classify_v12(text, m.start(), m.end(), tok)
            if c["verdict"] == "V2":
                return "CATCH"
    return "PASS"

print("### 未见变体过拟合探针：%d 条（不在任何回归语料中）" % len(UNSEEN))
print("%-8s %-6s %-8s %-8s %-8s %-6s | %s" % ("id", "expect", "n13", "chain", "v12", "一致", "text"))
rows = []
for cid, text, expect, note in UNSEEN:
    a, b, c = n13v(text), chainv(text), v12v(text)
    rows.append((cid, expect, a, b, c, note, text))
    print("%-8s %-6s %-8s %-8s %-8s %-6s | %s" %
          (cid, expect, a, b, c, "OK" if a == b else "DIFF", text[:38]))

def score(key):
    ok = sum(1 for r in rows if r[1] == r[key])
    fp = sum(1 for r in rows if r[1] == "PASS" and r[key] == "CATCH")
    fn = sum(1 for r in rows if r[1] == "CATCH" and r[key] == "PASS")
    return ok, fp, fn, len(rows)
print("\n逐层成绩（未见变体）:")
for k, name in [(2, "n13"), (3, "chain"), (4, "v12独立谓词")]:
    ok, fp, fn, n = score(k)
    print("  %-14s correct=%2d/%d  fp=%d  fn=%d  acc=%.1f%%" % (name, ok, n, fp, fn, 100.0 * ok / n))
print("\n  N13 自家 42 条（回归内）= 42/42 = 100.0%%；未见变体 20 条 = %d/20 %.1f%%" %
      (score(2)[0], 100.0 * score(2)[0] / 20))
print("  → 落差即过拟合幅度（本探针为示例性扰动，不是正式留出集）")

print("\n### 有效独立层数半定量（74 行 JSON）")
O = json.loads((WD / "_gp_regression_out.json").read_text(encoding="utf-8"))
R = O["rows"]
# P(三层全 PASS | 任一单层 PASS) 与条件熵
n13p = [r for r in R if r["n13"] == "PASS"]
p_r10 = sum(1 for r in n13p if r["r10"] == "PASS") / len(n13p)
p_r12 = sum(1 for r in n13p if r["r12"] == "PASS") / len(n13p)
allp = [r for r in R if all(r[c] == "PASS" for c in ("r10", "r12", "n13"))]
wrong = [r for r in allp if r["expect"] == "CATCH"]
print("  P(r10=PASS|n13=PASS)=%.3f  P(r12=PASS|n13=PASS)=%.3f" % (p_r10, p_r12))
print("  三层全 PASS=%d/74 (%.1f%%)，其中真断言=%d/18 (%.1f%%)" %
      (len(allp), 100.0 * len(allp) / 74, len(wrong), 100.0 * len(wrong) / len(allp)))
# 独立假设下的期望联合概率 vs 实测
import math
p_any = sum(1 for r in R if r["n13"] == "PASS") / 74
joint_indep = p_any * (sum(1 for r in R if r["r10"] == "PASS") / 74) * (sum(1 for r in R if r["r12"] == "PASS") / 74)
print("  独立假设下 E[P(三层全PASS)] = %.4f（%.1f/74）；实测 %d/74 = %.4f ⇒ 实测/独立 = %.2f" %
      (joint_indep, joint_indep * 74, len(allp), len(allp) / 74, (len(allp) / 74) / joint_indep))
# 互信息（二值）
def mi(a, b):
    ca, cb = collections.Counter(r[a] for r in R), collections.Counter(r[b] for r in R)
    joint = collections.Counter((r[a], r[b]) for r in R)
    v = 0.0
    for x, nx in ca.items():
        for y, ny in cb.items():
            pxy = joint[(x, y)] / 74
            if pxy:
                v += pxy * math.log2(pxy / ((nx / 74) * (ny / 74)))
    return v
for a, b in [("r10", "n13"), ("r12", "n13"), ("r10", "r12")]:
    print("  MI(%s,%s) = %.4f bit" % (a, b, mi(a, b)))
print("  提示：r12=PASS 在 n13=PASS 时概率=1.000（R12 只在 double_neg 时报，N13 自身消费 R12），")
print("        故 R12 对 N13 的「都过」不提供任何新信息 → 有效独立层数约 1～1.3 层。")

out = {"unseen": [{"id": r[0], "expect": r[1], "n13": r[2], "chain": r[3],
                   "v12": r[4], "note": r[5], "text": r[6]} for r in rows]}
(WD.parent / "chain_vs_single_20261109" / "_cs_holdout_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _cs_holdout_out.json")
