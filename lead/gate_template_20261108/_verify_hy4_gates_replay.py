# -*- coding: utf-8 -*-
# _verify_hy4_gates_replay.py —— 独立从 .mjs 提取 GATE_CODE 并原样复跑（不复用审计员提取件）
# 运行： python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_template_20261108/_verify_hy4_gates_replay.py
import json, re, pathlib, hashlib, subprocess, sys

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
RUNS = ROOT/".zcode/workflow-runs"
W = ROOT/"lead/gate_template_20261108"

def extract_lowered(mjs_path):
    s = mjs_path.read_text(encoding="utf-8")
    m = re.search(r"export const payload = ", s)
    if not m: return None, "no payload"
    try:
        obj, _ = json.JSONDecoder().raw_decode(s[m.end():])
    except Exception as e:
        return None, "json fail "+str(e)
    return obj.get("lowered", ""), "ok"

def extract_gate_src(lowered):
    if not lowered: return None
    m = re.search(r"const GATE_CODE\s*=\s*\[(.*?)\]\.join\(", lowered, re.S)
    if not m: return None
    seg = m.group(1)
    # 逐行取 JS 字符串字面量并解码
    arr = []
    for sm in re.finditer(r'"((?:[^"\\]|\\.)*)"\s*,?', seg):
        try:
            arr.append(json.loads('"'+sm.group(1)+'"'))
        except Exception:
            pass
    return "\n".join(arr) if arr else None

out = {"gates": {}, "gate_count": 0, "gate_value_compare": [], "replays": {}}

# ---- 扫描全部 dwfrun-*.mjs 的 GATE_CODE ----
allmjs = sorted(RUNS.glob("dwfrun-*.mjs"))
for p in allmjs:
    low, st = extract_lowered(p)
    src = extract_gate_src(low) if low else None
    if src is None:
        continue
    rid = p.name[7:15]
    out["gate_count"] += 1
    has_hex = ("hexdigest" in src) or ("sha256(" in src and "read_bytes" in src)
    has_st_size_compare = bool(re.search(r"st_size|getsize|os\.stat", src)) and bool(re.search(r"==|!=|match|compare|重算", src))
    rec = {"file": p.name, "src_chars": len(src), "has_hexdigest_or_recompute": has_hex,
           "has_banned_word_scan": ("含禁用词" in src or "for bad in" in src),
           "has_size_value_compare": has_st_size_compare,
           "root": (re.search(r"root=pathlib\.Path\('([^']+)'\)", src) or [None,"?"])[1] if "root=pathlib.Path" in src else "?"}
    out["gates"][rid] = rec
    if has_hex or has_st_size_compare:
        out["gate_value_compare"].append(rid)

# ---- 逐字比对：从 mjs 复原的 gate 源码 vs 审计员落盘的 _gt_gate_*.py ----
MAP = {
    "cd57bf1c": ("_gt_gate_cd57bf1c.py", "_gt_gate_cd57bf1c_out.txt"),
    "1c93b364": ("_gt_gate_1c93b364.py", "_gt_gate_1c93b364_out.txt"),
    "2b4e006c": ("_gt_gate_2b4e006c.py", "_gt_gate_2b4e006c_out.txt"),
    "324c613e": ("_gt_gate_324c613e.py", "_gt_gate_324c613e_out.txt"),
    "858e5e0b": ("_gt_gate_858e5e0b.py", "_gt_gate_858e5e0b_out.txt"),
}
out["verbatim_match"] = {}
for rid,(pyf,outf) in MAP.items():
    p = next((q for q in allmjs if q.name.startswith("dwfrun-"+rid)), None)
    low,_ = extract_lowered(p)
    src = extract_gate_src(low)
    disk = (W/pyf).read_text(encoding="utf-8") if (W/pyf).is_file() else None
    out["verbatim_match"][rid] = {
        "mjs_gate_found": src is not None,
        "disk_extract_matches_mjs": (src is not None and disk is not None and src.strip()==disk.strip()),
        "mjs_src": src,
    }

# ---- 原样复跑：用从 mjs 复原的源码，通过 python -I -X utf8 -c 执行 ----
for rid in MAP:
    p = next((q for q in allmjs if q.name.startswith("dwfrun-"+rid)), None)
    low,_ = extract_lowered(p)
    src = extract_gate_src(low)
    if src is None:
        out["replays"][rid] = {"error":"no gate src"}; continue
    r = subprocess.run([sys.executable,"-I","-X","utf8","-c",src],
                       capture_output=True, text=True, cwd=str(ROOT))
    diskout = (W/MAP[rid][1]).read_text(encoding="utf-8").strip() if (W/MAP[rid][1]).is_file() else ""
    out["replays"][rid] = {
        "exit": r.returncode,
        "stdout": r.stdout.strip(),
        "stderr": r.stderr.strip()[:400],
        "matches_claimed_out_file": r.stdout.strip()==diskout,
    }
    try:
        out["replays"][rid]["parsed"] = json.loads(r.stdout.strip())
    except Exception as e:
        out["replays"][rid]["parse_err"] = str(e)[:200]

# ---- 858e5e0b 全 mjs 中三禁词出现位置 ----
p858 = next(q for q in allmjs if q.name.startswith("dwfrun-858e5e0b"))
low858,_ = extract_lowered(p858)
for kw in ["gamemd.exe","ra2loader","taskkill"]:
    idxs = [m.start() for m in re.finditer(re.escape(kw), low858)]
    ctx = [low858[max(0,i-90):i+60].replace("\\n"," ") for i in idxs]
    out.setdefault("kw858_context", {})[kw] = ctx

# ---- 858e5e0b gate 是否含 for-bad-in 禁词扫描 ----
out["gate858_has_for_bad_in"] = "for bad in" in (out["verbatim_match"]["858e5e0b"]["mjs_src"] or "")
out["gate858_has_含禁用词"] = "含禁用词" in (out["verbatim_match"]["858e5e0b"]["mjs_src"] or "")

# ---- 「字节数 = 26,435」正则截断实测 ----
txt1 = "字节数 = 26,435"
txt2 = "字节数 = 26435"
out["regex_truncation"] = {
    "comma_form_findall": re.findall(r'字节数\s*=\s*\d+', txt1),
    "plain_form_findall": re.findall(r'字节数\s*=\s*\d+', txt2),
    "comma_numeric_extract": [re.search(r'\d+', x).group() for x in re.findall(r'字节数\s*=\s*\d+', txt1)],
}

# ---- 五份指纹件 '## 1'..'## 6' 与禁词命中 ----
FPS = ["lead/b2b_isolated_20261107/INTEGRATION_REPORT.md",
       "lead/dtrigger_round2_20261107/CRITERIA_ROUND2.md",
       "lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md",
       "lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md",
       "lead/d13d14_cards_20261108/DECISION_QUESTIONS.md"]
sec = {}
for f in FPS:
    t = (ROOT/f).read_text(encoding="utf-8")
    sec[f] = {"missing_sections": [s for s in ['## 1','## 2','## 3','## 4','## 5','## 6'] if s not in t],
              "sha_bindings": len(re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?', t)),
              "banned_hits": [b for b in ['gamemd.exe','ra2loader','taskkill','OpenProcess','ReadProcessMemory',
                              'SuspendThread','StackWalk64','MiniDumpWriteDump','CreateRemoteThread',
                              'SetWindowsHookEx','ctypes.windll','VirtualAllocEx','WriteProcessMemory',
                              'TerminateProcess','MiniDump','StackWalk'] if b in t]}
out["five_docs_checks"] = sec

# ---- 全树检索 ----
def grep_tree(pat, base):
    hits=[]
    for p in base.rglob("*"):
        if p.is_file() and p.suffix in {".md",".txt",".py",".json"}:
            try:
                for i,l in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(),1):
                    if pat in l: hits.append(f"{p.relative_to(ROOT)}:{i}")
            except Exception: pass
    return hits
out["最小字段_hits"] = grep_tree("最小字段", ROOT/"lead")
out["缺要素_hits"] = grep_tree("缺要素", ROOT/"lead")[:20]
out["缺要素_hits_count"] = len(grep_tree("缺要素", ROOT/"lead"))

# ---- 报告内是否含自身 SHA 绑定行 ----
rep = (W/"GATE_FALSE_POSITIVES.md").read_text(encoding="utf-8")
out["report_binding_lines"] = re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?[^\n]*', rep)
out["report_contains_68206e5e"] = "68206e5ed32fc81692f6c6b1ef9d67b53b8c00d0045bcbcaac32df2bfb7fa60d" in rep

print(json.dumps(out, ensure_ascii=False, indent=1))
