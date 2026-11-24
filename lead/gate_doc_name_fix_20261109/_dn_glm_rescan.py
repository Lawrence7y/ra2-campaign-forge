# -*- coding: utf-8 -*-
"""GLM 独立重扫（本会话实跑，不采信编排方数字）。
只读 .zcode/workflow-runs 单层全部 .mjs；
对每个 payload 的 lowered 精确切出 const GATE_CODE 代码块，
在块内判定是否存在 DOC=max(cands,key=lambda p:p.stat().st_size)。
另统计：整文件字面命中（含任务书引用文本，非门禁）、写域、const DOC 主件名、
已显式命名的安全门禁实例（Gen-1 doc=root / Gen-3 expected=wd）。
纯 stat/read；无递归 walk；无子进程；无真机；无采样代码。
"""
import json, os, re, hashlib

WFR = os.path.realpath(r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs")
HERE = os.path.realpath(r"D:\Project\ra2-campaign-forge\lead\gate_doc_name_fix_20261109")
OUT_NAME = "_dn_glm_rescan_out.json"

SEP = chr(92)  # backslash
DEFECT_RE = re.compile(
    r"DOC\s*=\s*max\s*\(\s*cands\s*,\s*key\s*=\s*lambda\s*p\s*:\s*p\.stat\(\)\.st_size\s*\)")
MAX_ANY_RE = re.compile(r"DOC\s*=\s*max\s*\(")
CANDS_RE = re.compile(r"cands\s*=\s*sorted\s*\(\s*wd\.glob\('\*\.md'\)\s*\)")
CONST_DOC_RE = re.compile(r"const\s+DOC\s*=\s*[\"']([^\"']+\.md)[\"']", re.I)
WRITE_DOMAIN_RE = re.compile(r"唯一写域\s*=\s*([A-Za-z0-9_/\-]+)")
WD_ROOT_RE = re.compile(r"wd\s*=\s*root\s*/\s*'([^']+)'")
EXPECTED_RE = re.compile(r"expected\s*=\s*wd\s*/\s*'([^']+\.md)'")
GEN1_RE = re.compile(r"doc\s*=\s*root\s*/\s*'([^']+\.md)'")


def safe_join(base, name):
    """规范化并校验：name 必须是 base 单层内的普通文件名，禁止 .. 与分隔符。"""
    if not name or name in (".", "..") or ".." in name:
        return None
    if "/" in name or SEP in name:
        return None
    b = os.path.realpath(base)
    p = os.path.realpath(os.path.join(b, name))
    if p != b and not p.startswith(b + os.sep):
        return None
    return p


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


def gate_block(low):
    k = low.find("const GATE_CODE = [")
    if k < 0:
        return None
    e1 = low.find("\n].join(", k)
    e2 = low.find("].join(", k)
    cands = [x for x in (e1, e2) if x >= 0]
    if not cands:
        return low[k:min(len(low), k + 8000)]
    return low[k:min(cands)]


def norm(s):
    return s.replace(SEP, "/").rstrip("/") if s else s


def main():
    names = sorted(n for n in os.listdir(WFR) if safe_join(WFR, n) is not None)
    rows = []
    for name in names:
        p = safe_join(WFR, name)
        raw = open(p, "rb").read()
        text = raw.decode("utf-8", errors="replace")
        payload = extract_payload(text)
        low = payload.get("lowered") if isinstance(payload, dict) else None
        rec = {
            "file": name,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "mtime": os.path.getmtime(p),
            "payload_parsed": payload is not None,
            "has_gate_code": False,
            "gate_defect_count": 0,
            "gate_has_docmax_any": False,
            "gate_has_cands": False,
            "file_defect_count": len(DEFECT_RE.findall(text)),
            "lowered_defect_count": (len(DEFECT_RE.findall(low)) if low else 0),
            "write_domain": None,
            "wd_from_gate": None,
            "const_doc": None,
            "expected": None,
            "gen1_doc": None,
            "safe_kind": None,
        }
        gb = None
        if low:
            gb = gate_block(low)
            if gb is not None:
                rec["has_gate_code"] = True
                rec["gate_defect_count"] = len(DEFECT_RE.findall(gb))
                rec["gate_has_docmax_any"] = bool(MAX_ANY_RE.search(gb))
                rec["gate_has_cands"] = bool(CANDS_RE.search(gb))
                ex = EXPECTED_RE.search(gb)
                g1 = GEN1_RE.search(gb)
                if ex:
                    rec["expected"] = ex.group(1)
                if g1:
                    rec["gen1_doc"] = g1.group(1)
                if rec["gate_defect_count"] == 0 and (ex or g1):
                    rec["safe_kind"] = "Gen-3(expected=wd)" if ex else "Gen-1(doc=root)"
            wm = WRITE_DOMAIN_RE.search(low)
            if wm:
                rec["write_domain"] = norm(wm.group(1))
            wr = WD_ROOT_RE.search(gb or "")
            if wr:
                rec["wd_from_gate"] = norm(wr.group(1))
            cd = CONST_DOC_RE.search(low)
            if cd:
                rec["const_doc"] = norm(cd.group(1))
        rows.append(rec)

    defect_rows = [r for r in rows if r["gate_defect_count"] > 0]
    file_hits = [r for r in rows if r["file_defect_count"] > 0]
    safe_rows = [r for r in rows if r["safe_kind"]]
    domains = {}
    for r in defect_rows:
        d = r["write_domain"] or r["wd_from_gate"] or "(unknown)"
        domains.setdefault(d, []).append(r["file"])

    summary = {
        "scanned_files_total": len(names),
        "mjs_files": sum(1 for n in names if n.endswith(".mjs")),
        "payload_parsed": sum(1 for r in rows if r["payload_parsed"]),
        "has_gate_code": sum(1 for r in rows if r["has_gate_code"]),
        "gate_defect_files": len(defect_rows),
        "gate_defect_total_hits": sum(r["gate_defect_count"] for r in defect_rows),
        "gate_defect_domains": len(domains),
        "file_level_defect_files": len(file_hits),
        "file_level_only_not_in_gate": [r["file"] for r in file_hits
                                        if r["gate_defect_count"] == 0],
        "safe_explicit_files": len(safe_rows),
        "safe_gen1": sum(1 for r in safe_rows if r["safe_kind"].startswith("Gen-1")),
        "safe_gen3": sum(1 for r in safe_rows if r["safe_kind"].startswith("Gen-3")),
        "safe_in_defect_set": [r["file"] for r in safe_rows if r["gate_defect_count"] > 0],
        "defect_rows_gate_has_cands": sum(1 for r in defect_rows if r["gate_has_cands"]),
        "defect_rows_const_doc": sum(1 for r in defect_rows if r["const_doc"]),
        "defect_rows_no_const_doc": [r["file"] for r in defect_rows if not r["const_doc"]],
        "domains": {k: v for k, v in sorted(domains.items())},
    }
    out_path = safe_join(HERE, OUT_NAME)
    if out_path is None:
        raise SystemExit("OUT path rejected by allow-list check")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"summary": summary, "defect_rows": defect_rows,
                   "safe_rows": safe_rows, "all_rows": rows},
                  f, ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print("OUT =", out_path)


if __name__ == "__main__":
    main()
