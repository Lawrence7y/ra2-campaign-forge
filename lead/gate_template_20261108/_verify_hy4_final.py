# -*- coding: utf-8 -*-
# _verify_hy4_final.py —— 收尾核验（只读，_verify_ 前缀）
import json, re, pathlib, hashlib, subprocess, sys
ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
RUNS = ROOT/".zcode/workflow-runs"
W = ROOT/"lead/gate_template_20261108"
out = {}

def low(p):
    s=p.read_text(encoding="utf-8")
    i=s.find('{"lowered":')
    if i<0: return None
    try: return json.JSONDecoder().raw_decode(s[i:])[0].get("lowered","")
    except Exception: return None

# 1. 20 vs 17：是否每个 GATE_CODE 都被 worldRead/gateRun 实跑
rows=[]
for p in sorted(RUNS.glob("dwfrun-*.mjs")):
    src=low(p)
    if src is None: continue
    if "const GATE_CODE = [" not in src: continue
    invoked = ("gateRun" in src) or ("GATE_CODE" in src and "worldRead" in src and "run" in src)
    # 是否含 gateRun 调用行
    has_gateRun_call = bool(re.search(r"(?:gateRun|gate_result)\s*=\s*await\s+__host\.worldRead", src))
    rows.append({"run":p.name[:15], "has_gateRun_call":has_gateRun_call,
                 "gateOk_field": "gateOk" in src, "root": (re.search(r"root=pathlib\.Path\('([^']+)'\)",src) or [None,"?"])[1] if "root=pathlib.Path" in src else "?"})
out["gate_inventory"]={"total":len(rows),"with_gateRun_call":sum(r["has_gateRun_call"] for r in rows),
                       "with_gateOk":sum(r["gateOk_field"] for r in rows),"rows":rows}

# 2. R3-1 修正试验：固定宽度占位符（与最终字节数位数一致）能否自洽
def trial(width):
    ph = "0"*width
    line0 = "被核对象 SHA256 = " + "0"*64 + "，字节数 = " + ph + "\n"
    body0 = "# doc\n" + line0 + "正文。\n"
    n = len(body0.encode("utf-8"))
    # 声明值 = 对「哈希占位」版本重算
    h = hashlib.sha256(body0.encode("utf-8")).hexdigest()
    line1 = "被核对象 SHA256 = " + h + "，字节数 = " + str(n) + "\n"
    body1 = "# doc\n" + line1 + "正文。\n"
    n1 = len(body1.encode("utf-8"))
    # 校验：把哈希换 0、字节数换同宽 0
    line2 = "被核对象 SHA256 = " + "0"*64 + "，字节数 = " + "0"*len(str(n1)) + "\n"
    body2 = "# doc\n" + line2 + "正文。\n"
    h2 = hashlib.sha256(body2.encode("utf-8")).hexdigest()
    return {"placeholder_width":width,"declared_bytes":n,"final_bytes":n1,
            "byte_decl_matches_final": n==n1,
            "placeholder_width_matches_final_digits": width==len(str(n1)),
            "hash_declared":h[:16],"hash_recomputed_on_zeroed":h2[:16],
            "hash_match":h==h2}
out["R3_1_fixed_width_trials"]=[trial(w) for w in [1,2,3,4,5,6]]

# 3. DECISION_QUESTIONS.md:130 绑定行指向
dq=(ROOT/"lead/d13d14_cards_20261108/DECISION_QUESTIONS.md").read_text(encoding="utf-8").splitlines()
out["DQ_130"]=dq[129] if len(dq)>=130 else "N/A"
out["DQ_all_binding_lines"]=[(i,l) for i,l in enumerate(dq,1) if "被核对象 SHA256" in l]
out["DQ_sha"]=hashlib.sha256((ROOT/"lead/d13d14_cards_20261108/DECISION_QUESTIONS.md").read_bytes()).hexdigest()

# 4. _gt_gate_*.py 在我复跑提取器后是否仍与 mjs 逐字一致（确认未改动既有件）
def gate_src(src):
    m=re.search(r"const GATE_CODE\s*=\s*\[(.*?)\]\.join\(", src, re.S)
    if not m: return None
    arr=[]
    for sm in re.finditer(r'"((?:[^"\\]|\\.)*)"\s*,?', m.group(1)):
        try: arr.append(json.loads('"'+sm.group(1)+'"'))
        except Exception: pass
    return "\n".join(arr) if arr else None
chk={}
for short,pyf in [("cd57bf1c","_gt_gate_cd57bf1c.py"),("1c93b364","_gt_gate_1c93b364.py"),
                  ("2b4e006c","_gt_gate_2b4e006c.py"),("324c613e","_gt_gate_324c613e.py"),
                  ("858e5e0b","_gt_gate_858e5e0b.py")]:
    p=next(q for q in RUNS.glob("dwfrun-*.mjs") if q.name.startswith("dwfrun-"+short))
    recon=gate_src(low(p))
    disk=(W/pyf).read_text(encoding="utf-8")
    chk[short]={"match":recon is not None and recon.strip()==disk.strip(),
                "disk_sha":hashlib.sha256(disk.encode()).hexdigest()[:16]}
out["gt_gate_files_still_verbatim"]=chk

# 5. 报告 §1 声称「17 个含门禁的运行」— 直接计数
out["report_claims_17"] = "17 个" in (W/"GATE_FALSE_POSITIVES.md").read_text(encoding="utf-8")
out["actual_gate_count"] = len(rows)

# 6. 858e5e0b 的 ASK 层「不得含字面量」原文
src858=low(next(q for q in RUNS.glob("dwfrun-*.mjs") if q.name.startswith("dwfrun-858e5e0b")))
i=src858.find("不得含")
out["ask_level_ban_literal"] = src858[max(0,i-120):i+120] if i>=0 else "NOT FOUND"
out["ask_level_ban_in_GATE_CODE"] = "不得含" in (gate_src(src858) or "")

# 7. 写域内我新增的文件清单（仅 _verify_ 前缀 + 输出）
out["my_verify_files"]=[p.name for p in sorted(W.glob("_verify_hy4*"))]

print(json.dumps(out,ensure_ascii=False,indent=1))
