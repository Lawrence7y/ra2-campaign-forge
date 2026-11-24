# -*- coding: utf-8 -*-
"""GLM 复核第二步：集合比对 + 主件名来源 + 安全实例性质 + 2 处引用噪音定性。
只读；输出 stdout 摘要与 _dn_glm_sites_out.json。
"""
import json, os, re, hashlib

HERE = os.path.realpath(r"D:\Project\ra2-campaign-forge\lead\gate_doc_name_fix_20261109")
WFR = os.path.realpath(r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs")
ROOT = os.path.realpath(r"D:\Project\ra2-campaign-forge")

# 编排方派发的 38 项 sites（原样录入，用于集合比对）
ORCH_SITES = """13448f03 15585c14 24bda605 27d477b1 3ca3ee7b 53714984 5ad91c91 5e5d5e49
616f12ea 636adfc5 65b875da 65d9f3a9 66e74798 69087c8f 802eb959 80551feb 80d9632c
830e57b2 88b03f6c 903e6b21 962827dd a1c4b1fd a4a38b66 af6f3c87 bc3fed8c bc9d8b8e
bdff6762 c482b235 cd88a9f5 cec38f8b d3ec8aec db5bad08 dcda8414 ebe5b75c f0c21a59
f123d326 fed3c2a2 ffc43bb0""".split()
ORCH_EXPECTED_36 = set(ORCH_SITES) - {"3ca3ee7b", "bdff6762"}

DEFECT_RE = re.compile(
    r"DOC\s*=\s*max\s*\(\s*cands\s*,\s*key\s*=\s*lambda\s*p\s*:\s*p\.stat\(\)\.st_size\s*\)")
DELIVER_RE = re.compile(r"【交付】[^\n]{0,500}?([A-Z0-9_]{4,}\.md)")
DELIVER2_RE = re.compile(r"(?:交付件|主交付件|主件)[^\n]{0,160}?([A-Z0-9_]{4,}\.md)")
CONST_DOC_RE = re.compile(r"const\s+DOC\s*=\s*[\"']([^\"']+\.md)[\"']", re.I)


def extract_payload(text):
    i = text.find("export const payload = ")
    if i < 0:
        return None
    try:
        val, _ = json.JSONDecoder().raw_decode(text[i + len("export const payload = "):])
        return val
    except Exception:
        return None


def gate_block(low):
    k = low.find("const GATE_CODE = [")
    if k < 0:
        return None
    c = [x for x in (low.find("\n].join(", k), low.find("].join(", k)) if x >= 0]
    return low[k:min(c)] if c else low[k:k + 8000]


def prefix8(name):
    m = re.match(r"dwfrun-([0-9a-f]{8})-", name)
    return m.group(1) if m else None


scan = json.load(open(os.path.join(HERE, "_dn_glm_rescan_out.json"), encoding="utf-8"))
defect = scan["defect_rows"]
mine36 = {prefix8(r["file"]) for r in defect}

cmp = {
    "orchestrator_site_count": len(ORCH_SITES),
    "orchestrator_expected_defect_36": len(ORCH_EXPECTED_36),
    "mine_gate_defect_36": len(mine36),
    "mine_minus_orch": sorted(mine36 - ORCH_EXPECTED_36),
    "orch_minus_mine": sorted(ORCH_EXPECTED_36 - mine36),
    "identical": mine36 == ORCH_EXPECTED_36,
}

# 2 个文件级命中但 gate 内无缺陷：定性
noise = []
for r in scan["all_rows"]:
    if r["file_defect_count"] > 0 and r["gate_defect_count"] == 0:
        p = os.path.join(WFR, r["file"])
        t = open(p, encoding="utf-8", errors="replace").read()
        low = extract_payload(t).get("lowered", "")
        gb = gate_block(low) or ""
        k = low.find("DOC=max(cands,key=lambda p:p.stat().st_size)")
        noise.append({
            "file": r["file"],
            "const_doc": r["const_doc"],
            "gate_expected": r["expected"],
            "gate_has_docmax_any": bool(re.search(r"DOC\s*=\s*max\s*\(", gb)),
            "gate_first_400": gb[:400],
            "literal_context": low[max(0, k - 160):k + 120].replace("\n", "|") if k >= 0 else None,
        })

# 每域主件名：const DOC 优先；无则从【交付】/交付件文本取；再看域内实存
domain_main = {}
for r in defect:
    d = r["write_domain"] or r["wd_from_gate"]
    if d not in domain_main:
        domain_main[d] = {"runs": [], "const_doc": r["const_doc"],
                          "deliver_hint": None, "domain_md": [], "no_underscore": []}
    domain_main[d]["runs"].append(r["file"])
    if r["const_doc"]:
        domain_main[d]["const_doc"] = r["const_doc"]

for d, v in domain_main.items():
    dp = os.path.join(ROOT, d.replace("/", os.sep))
    if os.path.isdir(dp):
        v["domain_md"] = sorted(n for n in os.listdir(dp)
                                if n.lower().endswith(".md")
                                and os.path.isfile(os.path.join(dp, n)))
        v["no_underscore"] = [n for n in v["domain_md"] if not n.startswith("_")]
    if not v["const_doc"]:
        # 从该域任一 run 的 lowered 找【交付】/交付件指示
        hints = []
        for f in v["runs"]:
            t = open(os.path.join(WFR, f), encoding="utf-8", errors="replace").read()
            low = extract_payload(t).get("lowered", "")
            for rx in (DELIVER_RE, DELIVER2_RE):
                hints += [m.group(1) for m in rx.finditer(low)]
        v["deliver_hint"] = sorted(set(hints))

# 安全实例性质：抽 3 个 Gen-1 / 3 个 Gen-3 看缺失即 FAIL
safe_sample = []
for r in scan["safe_rows"][:3] + scan["safe_rows"][-3:]:
    t = open(os.path.join(WFR, r["file"]), encoding="utf-8", errors="replace").read()
    low = extract_payload(t).get("lowered", "")
    gb = gate_block(low) or ""
    fail_lines = [ln.strip() for ln in gb.splitlines()
                  if ("P.append" in ln and ("缺失" in ln or "未按约定" in ln or "not " in ln))]
    safe_sample.append({"file": r["file"], "kind": r["safe_kind"],
                        "expected": r["expected"], "gen1_doc": r["gen1_doc"],
                        "fail_lines": fail_lines[:5]})

# 已交付状态与主件/中间稿大小（用于危险度排序）
sizes = {}
for d, v in domain_main.items():
    main = v["const_doc"].split("/")[-1] if v["const_doc"] else None
    if not main and len(v["no_underscore"]) == 1:
        main = v["no_underscore"][0]
    dp = os.path.join(ROOT, d.replace("/", os.sep))
    main_bytes, max_under, max_under_bytes, delta = None, None, None, None
    if main and os.path.isfile(os.path.join(dp, main)):
        main_bytes = os.path.getsize(os.path.join(dp, main))
        unders = [(os.path.getsize(os.path.join(dp, n)), n)
                  for n in v["domain_md"] if n.startswith("_")]
        if unders:
            max_under_bytes, max_under = max(unders)
            delta = max_under_bytes - main_bytes
    sizes[d] = {"main": main, "delivered": main_bytes is not None,
                "main_bytes": main_bytes, "max_underscore": max_under,
                "max_underscore_bytes": max_under_bytes,
                "underscore_minus_main_bytes": delta,
                "md_count": len(v["domain_md"]),
                "no_underscore_count": len(v["no_underscore"])}

out = {"set_comparison": cmp, "file_level_noise": noise,
       "domain_main": domain_main, "safe_sample": safe_sample, "sizes": sizes}
op = os.path.join(HERE, "_dn_glm_sites_out.json")
with open(op, "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps({"set_comparison": cmp, "noise": noise, "safe_sample": safe_sample},
                 ensure_ascii=False, indent=1))
print("DOMAIN_MAIN_SUMMARY")
for d, v in sorted(domain_main.items()):
    print(" ", d, "| const=", v["const_doc"], "| deliver=", v["deliver_hint"],
          "| bare=", v["no_underscore"])
print("OUT =", op)
