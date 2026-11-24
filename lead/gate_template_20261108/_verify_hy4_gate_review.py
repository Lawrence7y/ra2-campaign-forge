# -*- coding: utf-8 -*-
# _verify_hy4_gate_review.py —— 独立复核员·hy4 确定性核验脚本（只读；本任务写域内，_verify_ 前缀）
# 运行： python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_template_20261108/_verify_hy4_gate_review.py
import hashlib, os, json, re, pathlib

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
W = ROOT / "lead/gate_template_20261108"

def h(p):
    p = pathlib.Path(p)
    b = p.read_bytes()
    return {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b), "exists": True}

out = {}

# ---- 1. 编排方五指纹实算 ----
FPS = [
    "lead/b2b_isolated_20261107/INTEGRATION_REPORT.md",
    "lead/dtrigger_round2_20261107/CRITERIA_ROUND2.md",
    "lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md",
    "lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md",
    "lead/d13d14_cards_20261108/DECISION_QUESTIONS.md",
]
CLAIM = {
    "lead/b2b_isolated_20261107/INTEGRATION_REPORT.md": ("654634313698abf3cec61017e418091b97a4ebe17919fdf6fb3c9ebf22f62398", 24022),
    "lead/dtrigger_round2_20261107/CRITERIA_ROUND2.md": ("bcd7c8e53f6987a899f78fd1bd8ae90247193f1897aadf15cc58daa45211982a", 49968),
    "lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md": ("7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0", 29619),
    "lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md": ("1209ca4c8149722fffd1731a0f435637a2988a6e90993f87ef632eb4763b585e", 33431),
    "lead/d13d14_cards_20261108/DECISION_QUESTIONS.md": ("0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f", 27172),
}
fp = {}
for t in FPS:
    r = h(ROOT/t)
    c = CLAIM[t]
    r["claim_sha"] = c[0]; r["claim_bytes"] = c[1]
    r["match"] = (r["sha256"] == c[0] and r["bytes"] == c[1])
    fp[t] = r
out["five_fingerprints"] = fp
out["five_all_match"] = all(v["match"] for v in fp.values())

# ---- 2. 交付件指纹（报告自报的被核对象 SHA） ----
d = {}
for name in ["GATE_FALSE_POSITIVES.md", "GATE_TEMPLATE_FIXED.py.txt",
             "_gt_gate_cd57bf1c_out.txt", "_gt_gate_1c93b364_out.txt",
             "_gt_gate_2b4e006c_out.txt", "_gt_gate_324c613e_out.txt",
             "_gt_gate_858e5e0b_out.txt", "_gt_edge_audit_out.txt"]:
    d[name] = h(W/name)
out["deliverables"] = d
# 报告 §1:20 声明的模板指纹
out["template_claim_check"] = {
    "declared": "68206e5ed32fc81692f6c6b1ef9d67b53b8c00d0045bcbcaac32df2bfb7fa60d",
    "declared_bytes": 19189,
    "actual": d["GATE_TEMPLATE_FIXED.py.txt"]["sha256"],
    "actual_bytes": d["GATE_TEMPLATE_FIXED.py.txt"]["bytes"],
    "match": d["GATE_TEMPLATE_FIXED.py.txt"]["sha256"] == "68206e5ed32fc81692f6c6b1ef9d67b53b8c00d0045bcbcaac32df2bfb7fa60d" and d["GATE_TEMPLATE_FIXED.py.txt"]["bytes"] == 19189,
}

# ---- 3. 误报一：母本禁词计数 + 副本逐字节 ----
mother = ROOT/"lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"
iso = ROOT/"lead/b2b_isolated_20261107/qc151_trip.isolated.py"
mb = mother.read_bytes(); ib = iso.read_bytes()
out["mother_counts"] = {
    "mother_exists": mother.is_file(), "iso_exists": iso.is_file(),
    "mother_bytes": len(mb), "iso_bytes": len(ib),
    "identical": mb == ib,
    "mother_sha": hashlib.sha256(mb).hexdigest(),
    "iso_sha": hashlib.sha256(ib).hexdigest(),
    "OpenProcess_count": mb.count(b"OpenProcess"),
    "ctypes.windll_count": mb.count(b"ctypes.windll"),
    "ReadProcessMemory_count": mb.count(b"ReadProcessMemory"),
    "MiniDump_count": mb.count(b"MiniDump"),
    "CreateRemoteThread_count": mb.count(b"CreateRemoteThread"),
    "VirtualAllocEx_count": mb.count(b"VirtualAllocEx"),
    "SuspendThread_count": mb.count(b"SuspendThread"),
    "StackWalk_count": mb.count(b"StackWalk"),
}

# ---- 4. _verify_* 的 BANNED 常量行 ----
vs = {}
for name, key in [("_verify_A_recompute.py","BANNED_PAT"),
                  ("_verify_C_ast.py","BANNED"),
                  ("_verify_D_recompute.py","forbid")]:
    p = ROOT/"lead/dtrigger_round2_20261107"/name
    if p.is_file():
        lines = p.read_text(encoding="utf-8").splitlines()
        hits = [(i+1, l) for i,l in enumerate(lines) if key in l]
        vs[name] = {"exists": True, "key": key, "hits": hits[:8], "n_hits": len(hits),
                    "sha": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
    else:
        vs[name] = {"exists": False}
out["verify_banned_constants"] = vs

# ---- 5. 门禁 858e5e0b 真实 GATE_CODE 是否含三禁词扫描 ----
mjs = (ROOT/".zcode/workflow-runs/dwfrun-858e5e0b-5cc3-458e-b7cf-cea3224b3559.mjs").read_text(encoding="utf-8")
# 抽取 GATE_CODE 数组片段
m = re.search(r"const GATE_CODE = \[(.*?)\]\.join", mjs, re.S)
gateseg = m.group(1) if m else ""
out["gate_858e5e0b"] = {
    "gate_segment_found": bool(m),
    "contains_gamemd_literal": "gamemd" in gateseg.lower(),
    "contains_ra2loader_literal": "ra2loader" in gateseg.lower(),
    "contains_taskkill_literal": "taskkill" in gateseg.lower(),
    "contains_含禁用词": "含禁用词" in gateseg,
    "contains_for_bad_in": "for bad in" in gateseg,
    "gate_segment_chars": len(gateseg),
    "gate_lines": gateseg.count("\\n") + 1,
}
# 全 mjs 里是否把三禁词作为「禁词表」出现在任何 GATE 检查（区别于 IRON/ASK 文案）
for kw in ["gamemd.exe", "ra2loader", "taskkill"]:
    out["gate_858e5e0b"]["mjs_occurrences_"+kw] = mjs.count(kw)
# 与落盘提取件逐字比对
ext = (W/"_gt_gate_858e5e0b.py").read_text(encoding="utf-8")
# 把 GATE_CODE 的 JS 字符串还原成 python 源码
try:
    arr = json.loads("["+gateseg+"]")
    recon = "\n".join(arr)
except Exception as e:
    recon = "PARSE_FAIL:"+str(e)
out["gate_858e5e0b"]["extracted_file_matches_recon"] = (ext.strip() == recon.strip())
out["gate_858e5e0b"]["recon_head"] = recon[:200]

# ---- 6. 模板是否含「真实采样 API 调用」形态（Call 节点 / import ctypes 执行） ----
tpl = (W/"GATE_TEMPLATE_FIXED.py.txt").read_text(encoding="utf-8")
# 统计禁词在模板中的出现（容忍掩码/拼接）
for kw in ["OpenProcess","ReadProcessMemory","ctypes","gamemd","ra2loader","taskkill",
           "SuspendThread","StackWalk","MiniDump","VirtualAllocEx","WriteProcessMemory",
           "CreateRemoteThread","TerminateProcess","subprocess","os.system","ast.parse"]:
    out.setdefault("template_literals", {})[kw] = tpl.count(kw)
# 模板是否为可 import 的 python（应为「否」：纯文本设计稿）
try:
    import ast
    ast.parse(tpl)
    out["template_is_valid_python"] = True
except Exception as e:
    out["template_is_valid_python"] = False
    out["template_ast_error"] = str(e)[:200]

# ---- 7. 报告内掩码 vs 未掩码 ----
rep = (W/"GATE_FALSE_POSITIVES.md").read_text(encoding="utf-8")
for kw in ["gamemd.exe","ra2loader","taskkill","game·md.exe","ra2·loader","task·kill",
           "OpenProcess","ReadProcessMemory","ctypes.windll","Open·Process"]:
    out.setdefault("report_literals", {})[kw] = rep.count(kw)

print(json.dumps(out, ensure_ascii=False, indent=1))
