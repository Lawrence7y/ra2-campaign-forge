# 独立复核员脚本 ③-C：验证模板的最小加固是否可让 36/36 缺失态都输出 ok=false
# 加固 = 在 if not DOC.is_file() 之前，把 print 引用且只在 else: 内赋值的名字预初始化为 0
# 只读已有 _dnv_patch36_out.json 与沙盒 .py；不改历史 payload，只在本写域生成加固副本并 compile
import json, re, pathlib, os, shutil, importlib.util, io, contextlib

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
OUT = ROOT / "lead/gate_doc_name_fix_20261109/_dnv_patch36_hardened_out.json"
meta = json.loads((ROOT/"lead/gate_doc_name_fix_20261109/_dnv_patch36_out.json").read_text(encoding="utf-8"))
HDIR = ROOT / "lead/gate_doc_name_fix_20261109/_dnv_hardened"
if HDIR.exists(): shutil.rmtree(HDIR)
HDIR.mkdir(parents=True)

def run_py(py):
    spec = importlib.util.spec_from_file_location("_dnv_gate_h", str(py))
    mod = importlib.util.module_from_spec(spec)
    buf = io.StringIO(); err = None
    try:
        with contextlib.redirect_stdout(buf):
            spec.loader.exec_module(mod)
    except Exception as e:
        err = type(e).__name__ + ": " + str(e)
    last = buf.getvalue().strip().splitlines()[-1] if buf.getvalue().strip() else ""
    try: return json.loads(last), err
    except Exception: return {"ok": None, "raw": last[:200]}, err

rows = []
for r in meta["rows"]:
    src = pathlib.Path(r["gate_py"]).read_text(encoding="utf-8")
    pl = next(ln for ln in src.splitlines() if ln.startswith("print("))
    # print 行里出现的所有标识符（含 len(mods) 这种被函数包住的引用）
    names = set(re.findall(r"\b([A-Za-z_]\w*)\b", pl))
    # 在任意缩进 >0 的行里赋值、且 print 引用的名字，都可能在 else: 不执行时未定义
    inner = set()
    for ln in src.splitlines():
        if ln.startswith(" "):
            mm = re.match(r"\s*([A-Za-z_]\w*)\s*=", ln)
            if mm: inner.add(mm.group(1))
    risky = sorted((names & inner) - {"P", "SHA", "NB", "DOC", "t", "B", "raw"})
    # 在 " DOC=wd/" 行之前插一行预初始化（顶格，所有分支可见）
    anchor = next(i for i, ln in enumerate(src.splitlines()) if "DOC=wd/" in ln)
    lines = src.splitlines()
    init = ";".join((n + "=[]" if re.search(r"\blen\(\s*" + re.escape(n) + r"\s*\)", pl) else n + "=0") for n in risky)
    if init:
        lines.insert(anchor, init)
    hardened = "\n".join(lines) + "\n"
    py = HDIR / (r["file"][:20] + ".py")
    # 保持 wd 指向同一沙盒域（复制原 .py 的路径逻辑）
    py.write_text(hardened, encoding="utf-8")
    compile(hardened, str(py), "exec")
    wd = pathlib.Path(r["wd"])
    main = r["main"]
    absent = wd / ("_absent_" + main)
    os.rename(wd / main, absent)
    out, err = run_py(py)
    os.rename(absent, wd / main)
    rows.append({"file": r["file"], "main": main, "risky": risky,
                 "absent_ok": out.get("ok"), "absent_problems": out.get("problems"),
                 "shaMISSING": out.get("docSha256") == "MISSING", "err": err})

summary = {"sites": len(rows),
           "sites_with_risky": sum(1 for r in rows if r["risky"]),
           "absent_all_parsed": sum(1 for r in rows if r["absent_ok"] is not None),
           "absent_ok_false": sum(1 for r in rows if r["absent_ok"] is False),
           "absent_problem_has_missing": sum(1 for r in rows if r["absent_problems"] and any("主件缺失" in x for x in r["absent_problems"])),
           "absent_shaMISSING": sum(1 for r in rows if r["shaMISSING"]),
           "errors": [r["file"] for r in rows if r["err"]]}
OUT.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
