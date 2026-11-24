# -*- coding: utf-8 -*-
r"""_rj_delivery_verify.py — 交付件 GATE_REJUDGE_32.md 的自证实跑。

三件事（全部只读现盘主件 / 谓词库 / 基线，唯一写域内落 _rj_delivery_* 产物）：
(1) bindings=0 六域：用各自 GATE_CODE 里真实的 B=re.findall(...) 正则复算绑定行；
(2) 修正版最小判据片段（§5 补遗）在 13 个问题域上的全量模拟，含语境类 A/B/C/D/E；
(3) 复核意见指出的 5 条「真断言反例」是否会被修正版豁免（假阴性探针）。

零真机、零采样；不写任何已交付件 / 历史 payload / 台账。
"""
import hashlib
import importlib.util
import json
import re
import ast
import glob
import os
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_rejudge32_20261109"
PRED = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
PRED_SHA = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
PRED_BYTES = 11743
BASE = json.loads((WDIR / "_rj_delivery_baseline.json").read_text(encoding="utf-8"))
ROWS = BASE["rows"]
RUNS = {os.path.basename(p): p for p in glob.glob(str(ROOT / ".zcode/workflow-runs/*.mjs"))}

assert hashlib.sha256(PRED.read_bytes()).hexdigest() == PRED_SHA
assert PRED.stat().st_size == PRED_BYTES
_sp = importlib.util.spec_from_file_location("_rjd_g7pred", PRED)
g7 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(g7)

OUT = {"pred_sha256": PRED_SHA, "pred_bytes": PRED_BYTES,
       "baseline_sha256": hashlib.sha256((WDIR / "_rj_delivery_baseline.json").read_bytes()).hexdigest()}

# ---------------------------------------------------------------- (1) 真绑定行
GDUMP = json.loads((WDIR / "_rj_gate_src_dump_out.json").read_text(encoding="utf-8"))
STRICT = re.compile(r"被核对象 SHA256 = [0-9a-fA-F]{64}")
bind_rows = []
for r in ROWS:
    if r["bindings"] != 0:
        continue
    dom = r["domain"]
    mp = ROOT / dom.rstrip("/") / r["main"]
    t = mp.read_text(encoding="utf-8", errors="replace")
    src = GDUMP[dom.strip("/").split("/")[-1]]["gate_src"]
    real = re.findall(r"B\s*=\s*len\(re\.findall\((r'[^']+')|B\s*=\s*re\.findall\((r'[^']+')", src)
    exprs = [a or b for a, b in real]
    expr = exprs[0][2:-1] if exprs else None
    count = len(re.findall(expr, t)) if expr else None
    strict_lines = [i + 1 for i, ln in enumerate(t.split("\n")) if STRICT.search(ln)]
    bind_rows.append({"domain": dom, "baseline_bindingRegex": r["params"]["bindingRegex"],
                      "real_binding_regex": expr, "real_B": count,
                      "strict_adjacent_lines": strict_lines, "strict_adjacent_count": len(strict_lines)})
OUT["bindings_zero_real_counts"] = bind_rows


# ---------------------------------------------------------------- (2) 修正版片段
def classify(t, h, line):
    """R10 语境类：A 检索动作/检索对象，B 小节标题/表头，C 否定式/短引证，
    D 真断言，E 新增语用类（条件分支/可核项清单格/自检清单条文）。
    豁免规则刻意收窄：只放过「被讨论的对象」，不放过完成体陈述。"""
    tok = h["token"]
    if h["kind"] == "double_neg":
        return "D"          # 交 R12 判违规，不在这里豁免
    if h["kind"] in ("negation", "quote_mention"):
        return "C"
    if re.search(r"<[^>\n]{0,40}" + re.escape(tok) + r"[^>\n]{0,40}>", line):
        return "A"          # <已填件路径> 命令占位符
    if re.search(re.escape(tok) + r"(文件|的)", line) and ("未覆盖" in line or "不可能" in line):
        return "A"          # 「已删除文件」= 未覆盖申报里的检索对象，非「已删除了什么」
    if "先例" in line and "非" in line:
        return "A"          # 他件状态引述
    if ("是否" + tok) in line and (line.lstrip().startswith("#") or line.lstrip().startswith("|")):
        return "B"          # 「是否已填」提问式标题 / 表头
    antonym = "未" + (tok[1:] if tok.startswith("已") else tok)
    if "→" in line and antonym in line:
        return "E"          # 条件分支标签（「已填 → …；未填且… → …」）
    if re.match(r"^\s*\|\s*[A-G](?=\s|\|)", line) and ("拒绝" in line or "判定" in line):
        return "E"          # 可核项清单格
    if len(re.findall(r"(?:^|[；;\s])\d+\.\s", line)) >= 3:
        return "E"          # 同一行 ≥3 个编号自检条文
    return "D"


def line_of(t, pos):
    s = t.rfind("\n", 0, pos) + 1
    e = t.find("\n", pos)
    e = len(t) if e < 0 else e
    return t[s:e]


def gate(wd, main, elems, sections, banned):
    """§5 可粘贴最小片段的自洽可执行版：始终输出合法 JSON；主件缺失即 FAIL。"""
    P = []; NB = 0; SHA = "MISSING"; B = 0
    mods = []; hk = 0; rows = []; dd = 0; rd = 0     # <ELSE_ONLY_VARS> 预初始化
    DOC = wd / main
    pred = None
    if not PRED.is_file() or hashlib.sha256(PRED.read_bytes()).hexdigest() != PRED_SHA \
            or PRED.stat().st_size != PRED_BYTES:
        P.append("谓词库缺失/指纹失配")
    else:
        spec = importlib.util.spec_from_file_location("_rjd_g7p_in_gate", PRED)
        pred = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pred)
    if not DOC.is_file():
        P.append("主件缺失 " + main + "（写域=" + wd.name + "）")
    else:
        raw = DOC.read_bytes(); NB = len(raw)
        SHA = hashlib.sha256(raw).hexdigest()
        t = raw.decode("utf-8", errors="replace")
        if pred is not None:
            for s in sections:
                if s not in t:
                    P.append("缺小节 " + s)
            for k in elems:
                ok, _ = pred.r9_element_present(t, k)
                if not ok:
                    P.append("缺要素 " + k + "（R9：raw 与归一化文本双缺）")
            p10, w10, h10 = pred.r10_scan(t, banned)
            for h in h10:
                line = line_of(t, h["pos"])
                cls = classify(t, h, line)
                if cls == "D":
                    P.append("含越权断言 %s @L%d（D 真断言）"
                             % (h["token"], t.count("\n", 0, h["pos"]) + 1))
            for x in pred.r12_scan(t, banned)[0]:
                P.append("R12 " + x)
            p11, w11, binds = pred.r11_scan(t, wd, root=ROOT)
            B = len(binds)
            for x in p11:
                P.append("R11 " + x)
            if B < 1:
                P.append("缺 SHA256 绑定行（R11）")
    return {"ok": not P, "problems": P, "doc": main, "docBytes": NB,
            "docSha256": SHA, "bindings": B}


def gate_src(low):
    k = low.find("const GATE_CODE = [")
    end = low.find("].join", k)
    body = low[k + len("const GATE_CODE = ["):end]
    parts = []
    for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', body):
        try:
            parts.append(json.loads('"' + m.group(1) + '"'))
        except Exception:
            parts.append(m.group(1))
    return "\n".join(parts) if parts else ""


LOOP_RE = re.compile(r"for (\w+) in (\[[^\]]+\]):\n\s*if \1 not in t: P\.append\('缺要素 '\+\1\)")
SECT_RE = re.compile(r"for s in (\[[^\]]+\]):")
sim = []
for r in ROWS:
    if not r["gateProblems"]:
        continue
    dom = r["domain"]
    wd = ROOT / dom.rstrip("/")
    p = RUNS.get(r["run"])
    elems, sects = [], []
    if p:
        t = Path(p).read_text(encoding="utf-8", errors="replace")
        i = t.find("export const payload = ")
        low, _ = json.JSONDecoder().raw_decode(t[i + len("export const payload = "):])
        src = gate_src(low.get("lowered", ""))
        for m in LOOP_RE.finditer(src):
            try:
                elems += ast.literal_eval(m.group(2))
            except Exception:
                pass
        ms = SECT_RE.search(src)
        if ms:
            try:
                sects = ast.literal_eval(ms.group(1))
            except Exception:
                pass
    res = gate(wd, r["main"], [x for x in elems if x], sects, r["params"]["banned"])
    sim.append({"domain": dom, "elements": elems, "sections": sects, "result": res})
OUT["corrected_fragment_sim"] = sim
OUT["corrected_fragment_fail_domains"] = [x["domain"] for x in sim if not x["result"]["ok"]]
OUT["corrected_fragment_fail_count"] = len(OUT["corrected_fragment_fail_domains"])

# ---------------------------------------------------------------- (3) 假阴性探针
PROBES = [
    "| 1 | **已改台账**（2026-11-09 完成） | 主件 X |",
    "1. 已改门禁，缺口已修补完毕。",
    "### 5.4 已填身份值（reviewerSessionId = real-value）",
    "| 状态 | 已生效 |",
    "- 处置：已填 → 见证同为声明",
]
probe_rows = []
for line in PROBES:
    for tok in ("已改台账", "已改门禁", "已填", "已生效"):
        for m in re.finditer(re.escape(tok), line):
            hit = g7.r10_context(line, m.start(), m.end())
            probe_rows.append({"line": line, "token": tok, "kind": hit["kind"],
                               "class": classify(line, {"token": tok, "kind": hit["kind"]}, line)})
OUT["false_negative_probes"] = probe_rows
OUT["false_negative_probes_all_still_D"] = all(
    x["class"] == "D" for x in probe_rows if x["kind"] == "assertion")
OUT["cjk_or_b"] = {"见证已填或S1有记载": bool(re.search(r"\b或\b", "见证已填或S1有记载")),
                   "通过档或存疑档": bool(re.search(r"\b或\b", "通过档或存疑档"))}
# 复核件 _rjv_step5.py:37 的要素 token 提取（off-by-one 实读）
OUT["rjv_step5_token_slice"] = {"source": "_rjv_step5.py:37", "code": "tok = prob[5:]",
                                "example": "缺要素 可重建"[5:], "expected": "可重建"}

(WDIR / "_rj_delivery_verify_out.json").write_text(
    json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

print("=== (1) bindings=0 六域真实绑定行 ===")
for x in bind_rows:
    print("  %-46s real_B=%s strict=%d regex=%s"
          % (x["domain"], x["real_B"], x["strict_adjacent_count"], x["real_binding_regex"]))
print("=== (2) 修正版片段 13 域模拟 ===")
for x in sim:
    print("  %-46s ok=%-5s problems=%s"
          % (x["domain"], x["result"]["ok"], x["result"]["problems"][:4]))
print("  fail_count=%d fail=%s" % (OUT["corrected_fragment_fail_count"],
                                   OUT["corrected_fragment_fail_domains"]))
print("=== (3) 假阴性探针 ===")
for x in probe_rows:
    print("  %-58s token=%s kind=%s class=%s" % (x["line"][:56], x["token"], x["kind"], x["class"]))
print("  all_assertion_probes_still_D=%s" % OUT["false_negative_probes_all_still_D"])
print("  cjk_or_b=%s" % OUT["cjk_or_b"])
print("  rjv_step5_slice=%s" % OUT["rjv_step5_token_slice"])
