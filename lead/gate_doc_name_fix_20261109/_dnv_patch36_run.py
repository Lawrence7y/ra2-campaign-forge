# 独立复核员脚本 ③-B：逐处实跑「主件在场 / 主件改名缺失」两态
# 由 Bash 直接以 python -I -X utf8 <绝对脚本> 执行；本脚本内部不动态执行、不调用子进程
# 门禁 .py 文件由 ③-A 落盘；此处仅用 os.rename 改名沙盒副本（不动历史域），逐处输出 JSON 一行
import json, pathlib, os

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
OUT = ROOT / "lead/gate_doc_name_fix_20261109/_dnv_patch36_run_out.json"
meta = json.loads((ROOT / "lead/gate_doc_name_fix_20261109/_dnv_patch36_out.json").read_text(encoding="utf-8"))
rows = meta["rows"]

def run_gate_file(py_abs):
    # 直接 importlib 规格加载 .py：等价于 python <file>，但避免子进程与 shell
    import importlib.util
    spec = importlib.util.spec_from_file_location("_dnv_gate_instance", py_abs)
    mod = importlib.util.module_from_spec(spec)
    import io, contextlib
    buf = io.StringIO(); err = None
    try:
        with contextlib.redirect_stdout(buf):
            spec.loader.exec_module(mod)
    except Exception as e:
        err = type(e).__name__ + ": " + str(e)
    last = buf.getvalue().strip().splitlines()[-1] if buf.getvalue().strip() else ""
    try: return json.loads(last), err
    except Exception: return {"ok": None, "raw": last[:300]}, err

out = []
for r in rows:
    wd = pathlib.Path(r["wd"])
    main = r["main"]
    py = r["gate_py"]
    a, ea = run_gate_file(py)
    absent = wd / ("_absent_" + main)
    os.rename(wd / main, absent)
    b, eb = run_gate_file(py)
    os.rename(absent, wd / main)
    out.append({"file": r["file"], "main": main,
                "present": {"ok": a.get("ok"), "doc": a.get("doc"), "problems": a.get("problems"),
                            "docSha256_head": (a.get("docSha256") or "")[:16], "err": ea},
                "absent": {"ok": b.get("ok"), "doc": b.get("doc"), "problems": b.get("problems"),
                           "docBytes": b.get("docBytes"), "shaMISSING": b.get("docSha256") == "MISSING", "err": eb}})

summary = {
    "sites": len(out),
    "present_all_parsed": sum(1 for r in out if r["present"]["ok"] is not None),
    "present_doc_is_main": sum(1 for r in out if r["present"]["doc"] == r["main"]),
    "present_ok_true": sum(1 for r in out if r["present"]["ok"] is True),
    "absent_all_parsed": sum(1 for r in out if r["absent"]["ok"] is not None),
    "absent_ok_false": sum(1 for r in out if r["absent"]["ok"] is False),
    "absent_problem_has_missing": sum(1 for r in out if r["absent"]["problems"] and any("主件缺失" in x for x in r["absent"]["problems"])),
    "absent_shaMISSING": sum(1 for r in out if r["absent"]["shaMISSING"]),
    "absent_docBytes_zero": sum(1 for r in out if r["absent"]["docBytes"] == 0),
    "present_errors": [r["file"] for r in out if r["present"]["err"]],
    "absent_errors": [r["file"] for r in out if r["absent"]["err"]],
}
OUT.write_text(json.dumps({"summary": summary, "rows": out}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
