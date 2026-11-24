# -*- coding: utf-8 -*-
"""撰写员独立复核 C：S1–S4 回归 + S5/S6 边界探针。
自检夹具在本写域重建；旧门禁 = max 猜大；新门禁 = 加固版方案 A（含 else-only 预初始化）。
同进程调用，无子进程、无真机、无采样。python -I -X utf8 <绝对路径>"""
import json, re, pathlib, hashlib, shutil

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
BASE = ROOT / "lead/gate_doc_name_fix_20261109/_dnw_s1s4"
OUT = ROOT / "lead/gate_doc_name_fix_20261109/_dnw_s1s4_out.json"
SECTIONS = ["## 1", "## 2", "## 3"]
ELEMENTS = ["未验"]
BANNED = ["已改台账"]
BINDING_RE = re.compile(r"被核对象 SHA256 = [0-9a-fA-F]{64}")
BINDING = "被核对象 SHA256 = " + "b" * 64 + "，字节数 = 999"

def good(tag):
    return "\n".join(["# " + tag, "## 1 a", "## 2 b", "## 3 c", "未验项：无", BINDING]) + "\n"
def with_banned(tag):
    return good(tag) + "已改台账（越界断言，故意留在真主件里）\n"
def incomplete(tag):
    return "\n".join(["# " + tag, "## 1 a", "## 2 b", BINDING, "本稿止于第二节"]) + "\n"

def checks(t):
    P = []
    for s in SECTIONS:
        if s not in t: P.append("缺小节 " + s)
    for k in ELEMENTS:
        if k not in t: P.append("缺要素 " + k)
    for bad in BANNED:
        if bad in t: P.append("含越界断言 " + bad)
    return P

def gen2(wd):
    P, NB, SHA, B, doc = [], 0, "MISSING", 0, None
    cands = sorted(wd.glob("*.md")) if wd.is_dir() else []
    if not cands:
        P.append("写域内无 md 交付件")
    else:
        doc = max(cands, key=lambda p: p.stat().st_size)
        raw = doc.read_bytes(); NB = len(raw); SHA = hashlib.sha256(raw).hexdigest()
        t = raw.decode("utf-8", errors="replace")
        P += checks(t)
        B = len(BINDING_RE.findall(t))
        if B < 1: P.append("缺规范格式绑定行")
    return {"ok": not P, "problems": P, "doc": (doc.name if doc else "(none)"),
            "docBytes": NB, "docSha256": SHA, "bindings": B}

def planA_hardened(wd, name):
    # 加固版：显式命名 + else-only 变量预初始化（此处示例 mods/modsN）+ 缺失即 FAIL
    P, NB, B = [], 0, 0
    SHA = "MISSING"
    mods = []           # 加固：预初始化 print 会引用的 else-only 变量
    DOC = wd / name
    if not DOC.is_file():
        P.append("主件缺失 " + name + "（写域=" + wd.name + "）")
    else:
        raw = DOC.read_bytes(); NB = len(raw); SHA = hashlib.sha256(raw).hexdigest()
        t = raw.decode("utf-8", errors="replace")
        P += checks(t)
        B = len(BINDING_RE.findall(t))
        if B < 1: P.append("缺规范格式绑定行")
        mods = list(wd.glob("_side_*.md"))
    return {"ok": not P, "problems": P, "doc": name, "docBytes": NB,
            "docSha256": SHA, "bindings": B, "sideCount": len(mods)}

if BASE.exists(): shutil.rmtree(BASE)
BASE.mkdir(parents=True)
def put(sub, name, text):
    d = BASE / sub
    if not d.exists(): d.mkdir(parents=True)
    (d / name).write_text(text, encoding="utf-8")
    return d

put("S1", "MAIN.md", good("S1 正常"))
put("S2", "MAIN.md", with_banned("S2 真主件含违禁"))
put("S2", "_side_big.md", good("S2 侧件干净") + "x" * 9000)
put("S3", "MAIN.md", incomplete("S3 真主件缺要素"))
put("S3", "_mid_complete.md", good("S3 中稿补齐") + "y" * 9000)
put("S4", "_only_side.md", good("S4 仅侧件在场"))
# S5 双 bare 件（坏的更大）
put("S5", "MAIN.md", good("S5 约定主件"))
put("S5", "OTHER_BIGGER.md", with_banned("S5 另一个 bare 件") + "z" * 13000)
# S6 同字节并列
put("S6", "MAIN.md", good("S6 约定主件"))
put("S6", "AAA_SAME.md", with_banned("S6 同字节侧件"))
a = (BASE / "S6/MAIN.md").read_bytes(); b = (BASE / "S6/AAA_SAME.md").read_bytes()
if len(a) >= len(b):
    (BASE / "S6/AAA_SAME.md").write_bytes(b + b" " * (len(a) - len(b)))

cases = [("S1 正常", "S1", "MAIN.md"),
         ("S2 违禁词藏主件+侧件更大", "S2", "MAIN.md"),
         ("S3 主件缺要素+中稿补齐", "S3", "MAIN.md"),
         ("S4 主件缺失仅侧件", "S4", "MAIN.md"),
         ("S5 双 bare 主件(坏件更大)", "S5", "MAIN.md"),
         ("S6 同字节并列", "S6", "MAIN.md")]
expect = {"S1 正常": ("PASS", "PASS"), "S2 违禁词藏主件+侧件更大": ("PASS", "FAIL"),
          "S3 主件缺要素+中稿补齐": ("PASS", "FAIL"), "S4 主件缺失仅侧件": ("PASS", "FAIL")}
results, checks_rows = [], []
for label, sub, name in cases:
    d = BASE / sub
    sizes = {x.name: x.stat().st_size for x in d.glob("*.md")}
    g, a = gen2(d), planA_hardened(d, name)
    results.append({"scenario": label, "sizes": sizes, "gen2": g, "planA": a})
    if label in expect:
        gv = "PASS" if g["ok"] else "FAIL"
        av = "PASS" if a["ok"] else "FAIL"
        e = expect[label]
        checks_rows.append({"scenario": label, "gen2": gv, "planA": av,
                            "expected": list(e), "match": (gv, av) == e})
all_four = all(c["match"] for c in checks_rows)
out = {"all_four_match": all_four, "checks": checks_rows, "cases": results,
       "extra_probes": [{"scenario": r["scenario"], "gen2_ok": r["gen2"]["ok"],
                         "gen2_doc": r["gen2"]["doc"], "planA_ok": r["planA"]["ok"],
                         "planA_problems": r["planA"]["problems"]} for r in results[4:]]}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("%-30s | %-6s %-18s | %-6s %-8s %s" % ("SCENARIO", "Gen2", "doc", "PlanA", "doc", "problems"))
for r in results:
    print("%-30s | %-6s %-18s | %-6s %-8s %s" % (
        r["scenario"], r["gen2"]["ok"], r["gen2"]["doc"], r["planA"]["ok"], r["planA"]["doc"],
        "；".join(r["planA"]["problems"])))
print()
print(json.dumps({"all_four_match": all_four, "checks": checks_rows,
                  "extra_probes": out["extra_probes"]}, ensure_ascii=False, indent=1))
