# -*- coding: utf-8 -*-
r"""_fpv_rerun.py — 独立复核员：原样重跑被核回件的两支主脚本，
只把脚本内部写盘文件名改写到 _fpv_ 前缀（不覆盖、不修改任何 _fp_ 件），
并把 stdout 落到 _fpv_ 文件后与存储的 _fp_*_stdout.txt 逐字节比对。

不改任何对抗集/谓词/语料；唯一写域 lead/fp_pattern_20261109/，前缀 _fpv_。
"""
import sys, io, json, hashlib, contextlib
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "fp_pattern_20261109"
OUT = {}
def emit(k, v):
    OUT[k] = v
    print("[%s] %s" % (k, json.dumps(v, ensure_ascii=False)))

def rerun(script, old_write, new_write):
    src = (WD / script).read_text(encoding="utf-8")
    assert old_write in src, "write-target not found in " + script
    patched = src.replace('"' + old_write + '"', '"' + new_write + '"')
    assert patched != src
    buf = io.StringIO()
    g = {"__name__": "__main__", "__file__": str(WD / script)}
    with contextlib.redirect_stdout(buf):
        exec(compile(patched, str(WD / script), "exec"), g)
    return buf.getvalue()

targets = [
    ("_fp_recompute.py", "_fp_recompute_out.json", "_fpv_rerun_recompute_out.json"),
    ("_fp_classify.py", "_fp_classify_out.json", "_fpv_rerun_classify_out.json"),
]
res = {}
for script, oldw, neww in targets:
    tag = "recompute" if "recompute" in script else "classify"
    stored_name = "_fp_%s_stdout.txt" % tag
    got = rerun(script, oldw, neww)
    out_name = "_fpv_rerun_%s_stdout.txt" % tag
    (WD / out_name).write_text(got, encoding="utf-8")
    stored = (WD / stored_name).read_bytes()
    gotb = got.encode("utf-8")
    res[tag] = {"script": script, "rerun_lines": len(got.splitlines()),
                "stored_lines": len(stored.decode("utf-8").splitlines()),
                "rerun_sha256": hashlib.sha256(gotb).hexdigest(),
                "stored_sha256": hashlib.sha256(stored).hexdigest(),
                "byte_identical": gotb == stored,
                "rerun_stdout_file": out_name,
                "internal_out_redirected_to": neww}
    # 逐行差异（若有）
    if gotb != stored:
        a, b = got.splitlines(), stored.decode("utf-8").splitlines()
        res[tag]["first_diffs"] = [(i+1, a[i] if i < len(a) else "<EOF>",
                                    b[i] if i < len(b) else "<EOF>")
                                   for i in range(max(len(a), len(b)))
                                   if (a[i] if i < len(a) else None) != (b[i] if i < len(b) else None)][:5]
emit("verbatim_rerun_vs_stored", res)
emit("all_verbatim_identical", all(z["byte_identical"] for z in res.values()))

# 顺带核：被改写产生的 _fpv_rerun_*_out.json 与存储 _fp_*_out.json 内容是否一致
for tag, o, n in [("recompute", "_fp_recompute_out.json", "_fpv_rerun_recompute_out.json"),
                  ("classify", "_fp_classify_out.json", "_fpv_rerun_classify_out.json")]:
    a = json.loads((WD / o).read_text(encoding="utf-8"))
    b = json.loads((WD / n).read_text(encoding="utf-8"))
    emit("out_json_match_" + tag, {"keys_equal": set(a) == set(b),
         "json_equal": a == b, "n_keys": len(a)})

(WD / "_fpv_rerun_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _fpv_rerun_out.json")
