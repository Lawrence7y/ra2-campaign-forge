# -*- coding: utf-8 -*-
"""主件名可确定性自检（可复用）：对任意写域判定「主件名是否可确定」。
判定序：
  1) 库内指向该域的最新 dwfrun payload 里的 const DOC="..."（强证据）
  2) 同 payload 任务书【交付】段落里的 X.md 指示（次强证据）
  3) 域内 md 清单：无 _ 前缀者恰一 → 候选；否则 NOT_DETERMINABLE
用法: python -I -X utf8 _dn_gate_selfcheck.py <写域相对路径如 lead/xxx_20261109/>
只读；只打印。"""
import json, os, re, sys

ROOT = r"D:\Project\ra2-campaign-forge"
WFR = r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs"

def extract_payload(text):
    i = text.find("export const payload = ")
    if i < 0:
        return None
    j = i + len("export const payload = ")
    try:
        val, _ = json.JSONDecoder().raw_decode(text[j:])
        return val
    except Exception:
        return None

CONST_DOC_RE = re.compile(r"const DOC\s*=\s*[\"']([^\"']+\.md)[\"']", re.I)
DELIVER_RE = re.compile(r"【交付】[^\n]{0,400}?([A-Z0-9_]{4,}\.md)")
DEFECT_RE = re.compile(
    r"DOC\s*=\s*max\s*\(\s*cands\s*,\s*key\s*=\s*lambda\s*p\s*:\s*p\.stat\(\)\.st_size\s*\)")
EXPECTED_RE = re.compile(r"expected\s*=\s*wd\s*/\s*'([^']+\.md)'")
DOC_WD_RE = re.compile(r"\b(?:doc|DOC|expected)\s*=\s*(?:root|wd)\s*/\s*'([^']+\.md)'")

def check(domain):
    dom_norm = domain.rstrip("/\\")
    dp = os.path.join(ROOT, dom_norm.replace("/", os.sep))
    best = None  # (mtime, source, name, defect)
    for name in os.listdir(WFR):
        p = os.path.join(WFR, name)
        if not os.path.isfile(p):
            continue
        text = open(p, "r", encoding="utf-8", errors="replace").read()
        if dom_norm not in text and dom_norm.replace("/", chr(92)) not in text:
            continue
        payload = extract_payload(text)
        low = payload.get("lowered") if isinstance(payload, dict) else None
        if not low or ("唯一写域 = " + dom_norm) not in low:
            continue
        mtime = os.path.getmtime(p)
        m = EXPECTED_RE.search(low) or CONST_DOC_RE.search(low) or DOC_WD_RE.search(low)
        d = DELIVER_RE.search(low)
        cand, src = (None, None)
        if m:
            cand, src = m.group(1).split("/")[-1], ("payload门禁显式命名(expected/const/doc=)")
        elif d:
            cand, src = d.group(1), "payload任务书【交付】指示"
        if cand and (best is None or mtime > best[0]):
            best = (mtime, src, cand, bool(DEFECT_RE.search(text)))
    mds = []
    if os.path.isdir(dp):
        mds = sorted(n for n in os.listdir(dp)
                     if n.lower().endswith(".md") and os.path.isfile(os.path.join(dp, n)))
    top = [n for n in mds if not n.startswith("_")]
    verdict = {
        "domain": dom_norm,
        "payload_evidence": ({"source": best[1], "main": best[2],
                              "gate_has_docmax": best[3]} if best else None),
        "domain_md": mds,
        "no_underscore_md": top,
    }
    if best and os.path.isfile(os.path.join(dp, best[2])):
        verdict["verdict"] = "DETERMINABLE(主件在场)"
        verdict["main"] = best[2]
    elif best:
        verdict["verdict"] = "DETERMINABLE(主件未交付)"
        verdict["main"] = best[2]
    elif len(top) == 1:
        verdict["verdict"] = "WEAK(仅约定启发式：无_前缀者恰一)"
        verdict["main"] = top[0]
    else:
        verdict["verdict"] = "NOT_DETERMINABLE"
        verdict["main"] = None
    return verdict

if __name__ == "__main__":
    out = []
    for dom in sys.argv[1:]:
        out.append(check(dom))
    print(json.dumps(out, ensure_ascii=False, indent=1))
