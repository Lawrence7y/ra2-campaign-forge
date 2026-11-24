# -*- coding:  utf-8 -*-
"""32 个历史写域补跑门禁（无 exec 版）：
1) 自扫锁定 36 处真实缺陷 run（GATE_CODE 内含 DOC=max；任务书引用不算）；
2) 每域取最新 run：从 GATE_CODE 源码用 ast.literal_eval 提取检查参数
   （小节表 / 要素表 for-循环 / 违禁表 / 绑定行正则）；
3) 用统一检查器按「显式主件」重放各任务自己的检查；
4) 独立计算主件 sha256/字节数/是否最大。
不改 payload、不改交付件；只打印。"""
import json, os, re, ast, hashlib

ROOT = r"D:\Project\ra2-campaign-forge"
WFR = r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs"

DEFECT_RE = re.compile(
    r"DOC\s*=\s*max\s*\(\s*cands\s*,\s*key\s*=\s*lambda\s*p\s*:\s*p\.stat\(\)\.st_size\s*\)")
CONST_DOC_RE = re.compile(r"const DOC\s*=\s*[\"']([^\"']+\.md)[\"']", re.I)
DELIVER_RE = re.compile(r"【交付】[^\n]{0,400}?([A-Z0-9_]{4,}\.md)")
WRITE_DOMAIN_RE = re.compile(r"唯一写域\s*=\s*([^\n\\\"，。]+)")
LOOP_RE = re.compile(r"for (\w+) in (\[[^\]]+\]):\n\s*if \1 not in t: P\.append\('缺要素 '\+\1\)")
BANNED_RE = re.compile(r"for bad in (\[[^\]]+\]):")
SECT_RE = re.compile(r"for s in (\[[^\]]+\]):")
BIND_RE = re.compile(r"re\.findall\((r'[^']+')")

def extract_payload(text):
    i = text.find("export const payload = ")
    if i < 0:
        return None
    j = i + len("export const payload compound")
    j = i + len("export const payload = ")
    try:
        val, _ = json.JSONDecoder().raw_decode(text[j:])
        return val
    except Exception:
        return None

def extract_gate_src(low):
    """扫描 const GATE_CODE = [ ... ].join 的每个双引号字面量并 JSON 解码，
    按序拼接为 python 源码文本。JS 拼接段（+ 变量 +）被自然略去。"""
    k = low.find("const GATE_CODE = [")
    if k < 0:
        return None
    end = low.find("].join", k)
    if end < 0:
        return None
    body = low[k + len("const GATE_CODE = ["):end]
    lit_re = re.compile(r'"((?:[^"\\]|\\.)*)"')
    parts = []
    for m in lit_re.finditer(body):
        try:
            parts.append(json.loads('"' + m.group(1) + '"'))
        except Exception:
            parts.append(m.group(1))
    return "\n".join(parts) if parts else None

def gate_params(src):
    """从门禁源码提取：sections/elements/banned/binding 正则。"""
    p = {"sections": None, "elements": [], "banned": [], "bind": None,
         "unparsed_checks": 0}
    m = SECT_RE.search(src)
    if m:
        try:
            p["sections"] = ast.literal_eval(m.group(1))
        except Exception:
            pass
    for m in LOOP_RE.finditer(src):
        try:
            p["elements"].append(ast.literal_eval(m.group(2)))
        except Exception:
            p["unparsed_checks"] += 1
    m = BANNED_RE.search(src)
    if m:
        try:
            p["banned"] = ast.literal_eval(m.group(1))
        except Exception:
            p["unparsed_checks"] += 1
    m = BIND_RE.search(src)
    if m:
        p["bind"] = m.group(1)[2:-1]  # 去 r'' 前后缀
    return p

def run_gate_on(main_path, params):
    P = []
    raw = open(main_path, "rb").read()
    t = raw.decode("utf-8", errors="replace")
    if params["sections"]:
        for s in params["sections"]:
            if s not in t:
                P.append("缺小节 " + s)
    for lst in params["elements"]:
        for k in lst:
            if k not in t:
                P.append("缺要素 " + k)
    for bad in params["banned"]:
        if bad in t:
            P.append("含越界断言 " + bad)
    nb = 0
    if params["bind"]:
        nb = len(re.findall(params["bind"], t))
        if nb < 1:
            P.append("缺规范格式绑定行")
    return P, nb

def main():
    runs = []
    for name in sorted(os.listdir(WFR)):
        p = os.path.join(WFR, name)
        if not os.path.isfile(p):
            continue
        text = open(p, "r", encoding="utf-8", errors="replace").write
        text = open(p, "r", encoding="utf-8", errors="replace").read()
        i = text.find("export const payload = ")
        if i < 0:
            continue
        val, _ = json.JSONDecoder().raw_decode(text[i + len("export const payload = "):])
        low = val.get("lowered") or ""
        wm = WRITE_DOMAIN_RE.search(low)
        if not wm:
            continue
        dom = wm.group(1).strip()
        if "gate_doc_name_fix_20261109" in dom:
            continue
        if not DEFECT_RE.search(low):
            continue
        gsrc = extract_gate_src(low)
        if gsrc is None or " DOC=max(" not in gsrc:
            continue
        cd = CONST_DOC_RE.search(low)
        main_name = cd.group(1).split("/")[-1] if cd else None
        if not main_name:
            d = DELIVER_RE.search(low)
            main_name = d.group(1) if d else None
        runs.append({"run": name, "domain": dom, "main": main_name,
                     "mtime": os.path.getmtime(p), "gate_src": gsrc})
    by_dom = {}
    for r in runs:
        if r["main"] is None:
            continue
        if r["domain"] not in by_dom or r["mtime"] > by_dom[r["domain"]]["mtime"]:
            by_dom[r["domain"]] = r
    rows = []
    for dom, r in sorted(by_dom.items()):
        main_name = r["main"]
        dp = os.path.join(ROOT, dom.replace("/", os.sep).rstrip(os.sep))
        mp = os.path.join(dp, main_name)
        rec = {"domain": dom, "run": r["run"], "main": main_name}
        mds = []
        if os.path.isdir(dp):
            mds = [(n, os.path.getsize(os.path.join(dp, n))) for n in os.listdir(dp)
                   if n.lower().endswith(".md") and os.path.isfile(os.path.join(dp, n))]
        if os.path.isfile(mp):
            raw = open(mp, "rb").read()
            rec["mainBytes"] = len(raw)
            rec["mainSha256"] = hashlib.sha256(raw).hexdigest()
            rec["mainIsLargest"] = (main_name == max(mds, key=lambda x: x[1])[0]) if mds else None
            params = gate_params(r["gate_src"])
            P, nb = run_gate_on(mp, params)
            rec["params"] = {"sections": params["sections"],
                             "elementLists": len(params["elements"]),
                             "banned": params["banned"],
                             "bindingRegex": params["bind"],
                             "unparsed": params["unparsed_checks"]}
            rec["gateProblems"] = P
            rec["bindings"] = nb
        else:
            rec["mainBytes"] = None
            rec["mainSha256"] = "MISSING"
            rec["mainIsLargest"] = None
            rec["gateProblems"] = ["主件缺失（补跑时仍不在场）"]
            rec["bindings"] = 0
        rows.append(rec)
    print(json.dumps({"domains": len(rows), "rows": rows}, ensure_ascii=False, indent=1))

main()
