# -*- coding: utf-8 -*-
# _verify_hy4_claims.py —— 复核其余具体断言（只读，本写域 _verify_ 前缀）
import json, re, pathlib, hashlib
ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
W = ROOT/"lead/gate_template_20261108"
out = {}

def rd(p): return (ROOT/p).read_text(encoding="utf-8", errors="ignore").splitlines()

# 1. NEXT_STEPS:103
ns = rd("lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md")
out["NEXT_STEPS_103"] = {"n_lines": len(ns),
  "line99_108": [f"{i}: {ns[i-1]}" for i in range(99,109) if i<=len(ns)]}
out["NEXT_STEPS_103"]["contains_最少字段"] = "最少字段" in "\n".join(ns[98:108])
out["NEXT_STEPS_103"]["contains_最小字段"] = "最小字段" in "\n".join(ns[98:108])

# 2. PERF_REPAIR_HANDOFF 六要素行
ph = rd("lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md")
out["PERF_elements"] = {}
for kw in ["最少字段","采集时机","量级","同图控制","帧数","代价上限","能排除的假设","最小字段"]:
    out["PERF_elements"][kw] = [i for i,l in enumerate(ph,1) if kw in l]

# 3. N-8 转述行 113/139
sl = rd("lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md")
out["N8_lines"] = {i: sl[i-1] for i in [113,139] if i<=len(sl)}
out["N8_all_最小字段_lines"] = [i for i,l in enumerate(sl,1) if "最小字段" in l]

# 4. A_RESIDUAL 关键行
ar = rd("lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md")
out["AR_lines"] = {i: ar[i-1] for i in [4,12,130,159] if i<=len(ar)}
out["AR_contains_1209ca4c"] = "1209ca4c" in "\n".join(ar)
out["AR_contains_3343cfbe"] = "3343cfbe" in "\n".join(ar)
# JSON 现盘
js = ROOT/"lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json"
out["ACCEPTANCE_JSON"] = {"sha": hashlib.sha256(js.read_bytes()).hexdigest(), "bytes": js.stat().st_size}

# 5. 01a1190d 载荷中「绑定锚错位」原文
mjs = (ROOT/".zcode/workflow-runs/dwfrun-01a1190d-62d0-4b75-b05b-4044a79a82be.mjs").read_text(encoding="utf-8")
out["01a1190d_has_绑定锚错位"] = "绑定锚错位" in mjs
out["01a1190d_has_ACCEPT或PARTIAL"] = ("ACCEPT" in mjs and "PARTIAL" in mjs)
idx = mjs.find("绑定锚错位")
out["01a1190d_context"] = mjs[max(0,idx-150):idx+400] if idx>=0 else "NOT FOUND"

# 6. _integ_* 文件禁词命中行
for name in ["_integ_test_isolated.py","_integ_probe_isolated.py","_integ_check_isolated.py"]:
    p = ROOT/"lead/b2b_isolated_20261107"/name
    lines = p.read_text(encoding="utf-8").splitlines()
    kws = ["SuspendThread","StackWalk","MiniDump","ctypes.windll","mock.patch","patch(","OpenProcess"]
    out.setdefault("integ_lines", {})[name] = {str(i): l for i,l in enumerate(lines,1) if any(k in l for k in kws)}

# 7. 母本计数（按门禁词表逐词精确计数）
mb = (ROOT/"lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py").read_bytes()
for k in [b"OpenProcess",b"ReadProcessMemory",b"SuspendThread",b"StackWalk",b"MiniDump",b"CreateRemoteThread",b"ctypes.windll"]:
    out.setdefault("mother_banned_counts", {})[k.decode()] = mb.count(k)

# 8. 模板是否引入新误报风险：检查 R3-1 自绑定可行性 / R4 派生做差 / R6 双件 / R1 节号
tpl = (W/"GATE_TEMPLATE_FIXED.py.txt").read_text(encoding="utf-8")
out["template_rules_present"] = {("R"+str(i)): ("R"+str(i)+".") in tpl for i in range(9)}
# 模板含三禁词拼接形态吗？
out["template_concat_ban"] = {kw: (kw in tpl) for kw in ["gam'+'emd.exe","ra2'+'loader","task'+'kill",
                                                         "gamemd.exe","ra2loader","taskkill"]}
# 模板中的可运行 python 片段（含 hashlib.sha256 / open / ast.parse / subprocess）
out["template_exec_like"] = {
  "hashlib.sha256(" : tpl.count("hashlib.sha256("),
  "open(doc,'rb')" : tpl.count("open(doc,'rb')"),
  "ast.parse" : tpl.count("ast.parse"),
  "subprocess." : tpl.count("subprocess."),
  "os.system" : tpl.count("os.system"),
  "import ctypes" : tpl.count("import ctypes"),
  "= ctypes" : tpl.count("= ctypes"),
}

# 9. 双件并存实测（R6 现场）
for d, main, shadow in [("lead/perf_repair_n11_20261108","PERF_REPAIR_HANDOFF.md","_n11_PERF_REPAIR_HANDOFF.md"),
                         ("lead/d13d14_cards_20261108","DECISION_QUESTIONS.md","_n10_D13D14_CARDS_20261108.md")]:
    r={}
    for n in [main,shadow]:
        p=ROOT/d/n
        r[n]={"exists":p.is_file(),"sha":hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None,
              "bytes":p.stat().st_size if p.is_file() else None}
    out.setdefault("dual_files",{})[d]=r

# 10. 报告「零真机/零采样/未改既有件/未commit」声明处
rep = (W/"GATE_FALSE_POSITIVES.md").read_text(encoding="utf-8")
out["report_claims"] = {k: (k in rep) for k in ["零真机","零采样代码","未修改任何既有工作流脚本","未 commit","未 push",
                                                  "未验","不可引用","残留风险"]}
# 报告内是否出现「本运行门禁 858e5e0b 对报告本身扫」相关断言
out["report_858e5e0b_claim"] = {k: (k in rep) for k in ["858e5e0b","本运行门禁","对报告本身扫","活样本"]}

# 11. 写域外是否有本轮新增/修改（git status 快照比对：仅列出写域外且今日修改的 .py/.md）
import subprocess, os
r = subprocess.run(["git","status","--porcelain"], cwd=str(ROOT), capture_output=True, text=True)
out["git_status_write_domain_outside"] = [l for l in r.stdout.splitlines()
      if ("gate_template_20261108" not in l) and any(x in l for x in ["_verify_hy4","GATE_FALSE","GATE_TEMPLATE"])]
out["git_status_total_lines"] = len(r.stdout.splitlines())

print(json.dumps(out, ensure_ascii=False, indent=1))
