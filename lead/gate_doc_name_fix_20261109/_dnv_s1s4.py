# 独立复核员脚本 ④：自己构造 S1–S4 夹具 + 自己实现 Gen-2 / 方案 A 门禁，全程同进程无子进程
# 另加 S5/S6 两个额外探针（本人附加，用于检验「四场景是否足以证明无漏洞」的边界）
import json, re, pathlib, hashlib, shutil

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
BASE = ROOT / "lead/gate_doc_name_fix_20261109/_dnv_s1s4"
OUT = ROOT / "lead/gate_doc_name_fix_20261109/_dnv_s1s4_out.json"
SECTIONS = ["## 1", "## 2", "## 3"]
ELEMENTS = ["未验"]
BANNED = ["已改台账"]
BINDING_RE = re.compile(r"被核对象 SHA256 = [0-9a-fA-F]{64}")
BINDING = "被核对象 SHA256 = " + "a" * 64 + "，字节数 = 1234"

def good_text(tag):
    return "\n".join(["# " + tag, "## 1 一", "## 2 二", "## 3 三", "未验项：无", BINDING]) + "\n"

def bad_banned_text(tag):
    return "\n".join(["# " + tag, "## 1 一", "## 2 二", "## 3 三", "未验项：无", BINDING,
                      "已改台账（越界断言，故意留在真主件里）"]) + "\n"

def incomplete_text(tag):
    # 故意只写 ## 1 / ## 2，且不出现「未验」字样；也不在描述文字里复述被检字面
    return "\n".join(["# " + tag, "## 1 一", "## 2 二", BINDING, "本稿止于第二节"]) + "\n"

# ---- 自己实现的两套门禁；检查项完全一致，唯一差别 = 被核对象怎么选 ----
def gen2(wd):
    P = []; NB = 0; SHA = "MISSING"; B = 0; doc = None
    cands = sorted(wd.glob("*.md")) if wd.is_dir() else []
    if not cands:
        P.append("写域内无 md 交付件")
    else:
        doc = max(cands, key=lambda p: p.stat().st_size)
        raw = doc.read_bytes(); NB = len(raw); SHA = hashlib.sha256(raw).hexdigest()
        t = raw.decode("utf-8", errors="replace")
        for s in SECTIONS:
            if s not in t: P.append("缺小节 " + s)
        for k in ELEMENTS:
            if k not in t: P.append("缺要素 " + k)
        for bad in BANNED:
            if bad in t: P.append("含越界断言 " + bad)
        B = len(BINDING_RE.findall(t))
        if B < 1: P.append("缺规范格式绑定行")
    return {"ok": not P, "problems": P, "doc": (doc.name if doc else "(none)"),
            "docBytes": NB, "docSha256": SHA, "bindings": B}

def planA(wd, name):
    P = []; NB = 0; SHA = "MISSING"; B = 0
    DOC = wd / name
    if not DOC.is_file():
        P.append("主件缺失 " + name + "（写域=" + wd.name + "）")
    else:
        raw = DOC.read_bytes(); NB = len(raw); SHA = hashlib.sha256(raw).hexdigest()
        t = raw.decode("utf-8", errors="replace")
        for s in SECTIONS:
            if s not in t: P.append("缺小节 " + s)
        for k in ELEMENTS:
            if k not in t: P.append("缺要素 " + k)
        for bad in BANNED:
            if bad in t: P.append("含越界断言 " + bad)
        B = len(BINDING_RE.findall(t))
        if B < 1: P.append("缺规范格式绑定行")
    return {"ok": not P, "problems": P, "doc": name,
            "docBytes": NB, "docSha256": SHA, "bindings": B}

# ---- 夹具 ----
if BASE.exists(): shutil.rmtree(BASE)
BASE.mkdir(parents=True)

def put(sub, name, text):
    d = BASE / sub
    if not d.exists(): d.mkdir(parents=True)
    (d / name).write_text(text, encoding="utf-8")
    return d

S1 = put("S1", "MAIN.md", good_text("S1 正常主件"))
S2 = put("S2", "MAIN.md", bad_banned_text("S2 真主件含违禁"))
put("S2", "_side_big.md", good_text("S2 侧件干净") + "x" * 8000)
S3 = put("S3", "MAIN.md", incomplete_text("S3 真主件缺要素"))
put("S3", "_mid_complete.md", good_text("S3 中稿补齐") + "y" * 8000)
S4 = put("S4", "_only_side.md", good_text("S4 仅侧件"))
# S5（本人附加）：双 bare 主件，坏的更大
S5 = put("S5", "MAIN.md", good_text("S5 约定主件"))
put("S5", "OTHER_BIGGER.md", bad_banned_text("S5 另一 bare 件含违禁") + "z" * 12000)
# S6（本人附加）：同字节并列，max 退化为排序取首
S6 = put("S6", "MAIN.md", good_text("S6 约定主件"))
put("S6", "AAA_SAME.md", bad_banned_text("S6 同字节侧件") )
# 让两者字节数完全相同
a = (S6 / "MAIN.md").read_bytes(); b = (S6 / "AAA_SAME.md").read_bytes()
if len(a) != len(b):
    (S6 / "AAA_SAME.md").write_bytes(b + b" " * (len(a) - len(b)) if len(a) > len(b) else b[:len(a)])

cases = [("S1 正常", "S1", "MAIN.md"), ("S2 违禁词藏主件+侧件更大", "S2", "MAIN.md"),
         ("S3 主件缺要素+中稿更大", "S3", "MAIN.md"), ("S4 主件缺失仅侧件", "S4", "MAIN.md"),
         ("S5 双 bare 主件(坏的更大)", "S5", "MAIN.md"), ("S6 同字节并列(排序取首)", "S6", "MAIN.md")]
results = []
for label, sub, name in cases:
    d = BASE / sub
    md_files = sorted(x.name for x in d.glob("*.md"))
    sizes = {x.name: x.stat().st_size for x in d.glob("*.md")}
    g = gen2(d); a = planA(d, name)
    results.append({"scenario": label, "wd_files": md_files, "sizes": sizes,
                    "gen2": g, "planA": a})

# 断言：设计回件 §4.2 的四条期望
expect = {"S1 正常": ("PASS", "PASS"), "S2 违禁词藏主件+侧件更大": ("PASS", "FAIL"),
          "S3 主件缺要素+中稿更大": ("PASS", "FAIL"), "S4 主件缺失仅侧件": ("PASS", "FAIL")}
checks = []
for r in results[:4]:
    gv = "PASS" if r["gen2"]["ok"] else "FAIL"
    av = "PASS" if r["planA"]["ok"] else "FAIL"
    e = expect[r["scenario"]]
    checks.append({"scenario": r["scenario"], "gen2": gv, "planA": av, "expected": list(e), "match": (gv, av) == e})

OUT.write_text(json.dumps({"cases": results, "checks": checks,
                           "all_four_match": all(c["match"] for c in checks),
                           "extra_probes": [{"scenario": r["scenario"], "gen2_ok": r["gen2"]["ok"],
                                             "gen2_doc": r["gen2"]["doc"], "planA_ok": r["planA"]["ok"],
                                             "planA_doc": r["planA"]["doc"]} for r in results[4:]]},
                          ensure_ascii=False, indent=2), encoding="utf-8")
print("SCENARIO                                | Gen2 ok / doc                  | PlanA ok / doc / problems")
for r in results:
    print("%-38s | %-5s %-22s | %-5s %-10s %s" % (
        r["scenario"], r["gen2"]["ok"], r["gen2"]["doc"], r["planA"]["ok"], r["planA"]["doc"],
        "；".join(r["planA"]["problems"])))
print()
print(json.dumps({"checks": checks, "all_four_match": all(c["match"] for c in checks),
                  "extra_probes": [{"scenario": r["scenario"], "gen2_ok": r["gen2"]["ok"],
                                    "gen2_doc": r["gen2"]["doc"], "planA_ok": r["planA"]["ok"]} for r in results[4:]]},
                 ensure_ascii=False, indent=2))
