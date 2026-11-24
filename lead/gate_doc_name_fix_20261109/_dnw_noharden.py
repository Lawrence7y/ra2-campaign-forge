# -*- coding: utf-8 -*-
"""撰写员独立复核 D：未加固模板（§2.1 印刷形态，无 else-only 预初始化）对照。
删除 _dnw_template_out.json 记录的 init_line，主件缺失态实跑 → 复现 6/36 NameError。
只在本写域沙盒副本上操作，绝不碰历史件。python -I -X utf8 <绝对路径>"""
import json, pathlib, importlib.util, io, contextlib, os

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
META = json.loads((ROOT / "lead/gate_doc_name_fix_20261109/_dnw_template_out.json").read_text(encoding="utf-8"))
OUT = ROOT / "lead/gate_doc_name_fix_20261109/_dnw_noharden_out.json"

def run_module(py):
    spec = importlib.util.spec_from_file_location("_dnw_noharden", str(py))
    mod = importlib.util.module_from_spec(spec)
    buf = io.StringIO(); err = None
    try:
        with contextlib.redirect_stdout(buf):
            spec.loader.exec_module(mod)
    except Exception as e:
        err = type(e).__name__ + ": " + str(e)
    last = buf.getvalue().strip().splitlines()[-1] if buf.getvalue().strip() else ""
    try: return json.loads(last), err
    except Exception: return {"ok": None, "raw": last[:160]}, err

rows = []
for r in META["rows"]:
    domain, main, init_line = r["domain"], r["main"], r["init_line"]
    wd = ROOT / "lead/gate_doc_name_fix_20261109/_dnw_sandbox" / domain
    py = wd / "_dnw_gate.py"
    src = py.read_text(encoding="utf-8")
    # 精确删除本轮插入的预初始化行（顶格、唯一）
    lines = src.splitlines()
    removed = 0
    if init_line:
        keep = []
        for ln in lines:
            if ln == init_line and removed == 0:
                removed += 1; continue
            keep.append(ln)
        lines = keep
    src2 = "\n".join(lines) + "\n"
    py2 = wd / "_dnw_gate_noharden.py"
    py2.write_text(src2, encoding="utf-8")
    # 主件缺失态
    absent = wd / ("_absent_" + main)
    present_path = wd / main
    os.rename(present_path, absent)
    try:
        out, err = run_module(py2)
    finally:
        if absent.exists() and not present_path.exists():
            os.rename(absent, present_path)
    probs = out.get("problems") or []
    rows.append({"file": r["file"][:20], "domain": domain, "main": main,
                 "init_removed": bool(init_line), "removed_ok": removed == (1 if init_line else 0),
                 "ok": out.get("ok"), "parsed": out.get("ok") is not None,
                 "has_missing": any("主件缺失" in x for x in probs), "err": err})
    py2.unlink()

summary = {
    "sites": len(rows),
    "absent_parsed": sum(1 for x in rows if x["parsed"]),
    "absent_ok_false": sum(1 for x in rows if x["ok"] is False),
    "absent_has_missing_msg": sum(1 for x in rows if x["has_missing"]),
    "absent_errors": [x["file"] for x in rows if x["err"]],
    "error_details": [{"file": x["file"], "err": x["err"]} for x in rows if x["err"]],
}
OUT.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
