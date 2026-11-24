# -*- coding: utf-8 -*-
# _verify_hy4_template_risks.py —— 独立 AST 复核 + 模板新误报风险实测（只读，_verify_ 前缀）
import ast, json, re, pathlib, hashlib
ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
W = ROOT/"lead/gate_template_20261108"
out = {}

BANNED_ATTR_PREFIX = ("ctypes.windll","ctypes.oledll","ctypes.CDLL","ctypes.pythonapi")
BANNED_NAMES = {"OpenProcess","ReadProcessMemory","WriteProcessMemory","VirtualAllocEx",
                "CreateRemoteThread","SetWindowsHookEx","SuspendThread","TerminateProcess"}

def edges(src):
    tree = ast.parse(src)
    imp, attr, calls = [], [], []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names: imp.append(a.name)
        elif isinstance(n, ast.ImportFrom):
            imp.append((n.module or "")+"."+",".join(a.name for a in n.names))
        elif isinstance(n, ast.Attribute):
            parts=[]
            x=n
            while isinstance(x, ast.Attribute):
                parts.append(x.attr); x=x.value
            if isinstance(x, ast.Name): parts.append(x.id)
            chain=".".join(reversed(parts))
            if any(p in chain for p in BANNED_ATTR_PREFIX): attr.append(chain)
        elif isinstance(n, ast.Call):
            f=n.func
            nm = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            if nm in BANNED_NAMES or nm.startswith("StackWalk") or nm.startswith("MiniDump"):
                calls.append("call:"+nm)
    return {"imports":imp, "banned_attr_chains":attr, "banned_calls":calls,
            "call_edges": attr+calls}

# 1. 独立 AST：三个 _verify_* 与两个 _integ_*
targets = {
 "_verify_A_recompute.py": ROOT/"lead/dtrigger_round2_20261107/_verify_A_recompute.py",
 "_verify_C_ast.py": ROOT/"lead/dtrigger_round2_20261107/_verify_C_ast.py",
 "_verify_D_recompute.py": ROOT/"lead/dtrigger_round2_20261107/_verify_D_recompute.py",
 "_integ_test_isolated.py": ROOT/"lead/b2b_isolated_20261107/_integ_test_isolated.py",
 "_integ_probe_isolated.py": ROOT/"lead/b2b_isolated_20261107/_integ_probe_isolated.py",
 "qc151_trip.isolated.py": ROOT/"lead/b2b_isolated_20261107/qc151_trip.isolated.py",
}
for k,p in targets.items():
    try:
        out.setdefault("independent_ast",{})[k]=edges(p.read_text(encoding="utf-8"))
    except Exception as e:
        out.setdefault("independent_ast",{})[k]={"error":str(e)[:200]}

# 2. R3-1 扣行自绑定可行性实测
# 模板：「把现盘文件中该行哈希字段替换为 64 个 '0' 后重算，应与行内声明一致」
#       「字节数同理以 0 占位」
def self_anchor_trial(byte_placeholder):
    # 构造一个含自绑定行的文档，尝试两种占位宽度
    line = "被核对象 SHA256 = " + "0"*64 + "，字节数 = " + byte_placeholder + "\n"
    body = "# doc\n" + line + "正文。\n"
    b = body.encode("utf-8")
    # 「扣行」：把哈希替换为 64 个 0（已是 0），把字节数替换为 0 占位
    h = hashlib.sha256(b).hexdigest()
    # 写回真实哈希，字节数写回真实长度
    real = "被核对象 SHA256 = " + h + "，字节数 = " + str(len(b)) + "\n"
    real_body = "# doc\n" + real + "正文。\n"
    # 校验时把哈希换 0、字节数换同宽 0
    width = len(str(len(real_body.encode("utf-8"))))
    check = "被核对象 SHA256 = " + "0"*64 + "，字节数 = " + "0"*width + "\n"
    check_body = "# doc\n" + check + "正文。\n"
    h2 = hashlib.sha256(check_body.encode("utf-8")).hexdigest()
    return {"placeholder": byte_placeholder,
            "placeholder_width": len(byte_placeholder),
            "real_file_bytes": len(real_body.encode("utf-8")),
            "real_declared_bytes": len(b),
            "byte_width_of_real": len(str(len(real_body.encode("utf-8")))),
            "hash_placeholder_substituted": h2,
            "hash_declared": h,
            "match": h2 == h,
            "byte_match": len(b) == len(real_body.encode("utf-8"))}
out["R3_1_self_anchor_trials"] = [self_anchor_trial("0"), self_anchor_trial("00000"), self_anchor_trial("000000")]

# 3. R2 同义词是否在本会话既有语料出现（检验「由领域语料编译」）
corpus = []
for p in (ROOT/"lead").rglob("*"):
    if p.is_file() and p.suffix in {".md",".txt"} and "gate_template_20261108" not in str(p):
        try: corpus.append(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception: pass
ALL = "\n".join(corpus)
syn = ['最少字段','最小字段','最小观测字段','字段清单','最少观测字段','观测字段与口径',
       '采集时机','读数时机','采样时机','观测时机','量级与同图控制','量级／同图控制',
       '量级/同图控制','同图控制','量级参照','量级与对照','所需帧数论证','所需帧数',
       '帧数论证','趟数论证','样本量论证','所需趟数','代价上限','成本上限','代价估算',
       '成本假设','接受度','能排除的假设','可排除假设','可排除的假设','排除项','判死方向',
       '不放行采集','不自动扩大采集','仅放行技术规格评审','禁止依赖未确认结论的修改或采集']
out["R2_synonym_corpus_hits"] = {s: ALL.count(s) for s in syn}
out["R2_synonyms_zero_hits"] = [s for s in syn if ALL.count(s)==0]

# 4. R4-1 「import ctypes」作为边 → 新误报面实测
benign = "import ctypes\nx = ctypes.c_int(3)\nprint(x.value)\n"
out["R4_import_ctypes_edge"] = edges(benign)
out["R4_old_gate_would_flag_benign"] = any(b in benign for b in
    ['OpenProcess','ReadProcessMemory','SuspendThread','StackWalk','MiniDump','CreateRemoteThread','ctypes.windll','VirtualAllocEx'])

# 5. R3-2 vs R3-3 冲突实测：历史锚绑定行格式与引用锚格式相同
ar = (ROOT/"lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md").read_text(encoding="utf-8")
lines = [l for l in ar.splitlines() if "被核对象 SHA256" in l]
out["R3_historical_anchor_lines"] = lines
out["R3_historical_line_has_explicit_path"] = any("A_RESIDUAL_REFERENCES.md" in l or ".md" in l for l in lines)
out["R3_current_file_recompute"] = hashlib.sha256((ROOT/"lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md").read_bytes()).hexdigest()

# 6. 模板含三禁词未掩码（与报告「全程掩码书写」对照）
tpl = (W/"GATE_TEMPLATE_FIXED.py.txt").read_text(encoding="utf-8")
out["template_unmasked_literals"] = {k: tpl.count(k) for k in ["gamemd.exe","ra2loader","taskkill"]}
rep = (W/"GATE_FALSE_POSITIVES.md").read_text(encoding="utf-8")
out["report_unmasked_literals"] = {k: rep.count(k) for k in ["gamemd.exe","ra2loader","taskkill"]}
# 858e5e0b gate 是否检查模板内容（只检查 is_file？）
gate = (W/"_gt_gate_858e5e0b.py").read_text(encoding="utf-8")
out["gate858_reads_template_text"] = "tpl.read_text" in gate or "tpl.read_bytes" in gate
out["gate858_template_check"] = [l for l in gate.splitlines() if "tpl" in l]

print(json.dumps(out, ensure_ascii=False, indent=1))
