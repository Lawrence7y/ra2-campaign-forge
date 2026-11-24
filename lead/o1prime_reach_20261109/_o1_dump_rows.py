# -*- coding: utf-8 -*-
"""O1' 全量留痕：复跑一个真实 write_bytes 失败例（ACL 拒写）+ 一个缺失目录例，
把 rec.rows（含完整 traceback，文件名/行号即被核件真实路径行号）与 spy 观测
dump 成 JSON 落写域，供绑定复核。"""
import hashlib
import importlib.util
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

CAND = Path(r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py")
OUT = Path(r"D:\Project\ra2-campaign-forge\lead\o1prime_reach_20261109")
TMP = OUT / "_o1_tmp"

raw = CAND.read_bytes()
print("被核对象 SHA256 =", hashlib.sha256(raw).hexdigest())
print("字节数 =", len(raw))

spec = importlib.util.spec_from_file_location("qc151_cand_o1", CAND)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

real_classify = mod.classify_except_freshness
spy = {}

def classify_spy(pre, post):
    ret = real_classify(pre, post)
    spy["post_in"] = dict(post) if isinstance(post, dict) else repr(post)
    spy["ret"] = dict(ret)
    return ret

mod.classify_except_freshness = classify_spy

def one_case(tag, deny):
    rec = mod.Recorder()
    carrier = TMP / ("dcarrier_" + tag)
    if carrier.exists():
        shutil.rmtree(carrier)
    carrier.mkdir(parents=True)
    pre = mod.make_pre_freshness_snapshot(carrier / "except.txt")
    (carrier / "except.txt").write_bytes(
        ("O1' 全量留痕趟 " + tag + " " + datetime.now().isoformat(timespec="milliseconds") + "\n").encode("utf-8"))
    if tag == "B1":
        out_dir = TMP / "dump_vanished_out"          # 不创建
        if out_dir.exists():
            shutil.rmtree(out_dir)
    else:
        out_dir = TMP / "dump_denied_out"
        if out_dir.exists():
            subprocess.run(["icacls", str(out_dir), "/remove:d", "*S-1-1-0"],
                           capture_output=True)
            shutil.rmtree(out_dir, ignore_errors=True)
        out_dir.mkdir(parents=True)
        r = subprocess.run(["icacls", str(out_dir), "/deny", "*S-1-1-0:(WD)"],
                           capture_output=True)
        print("icacls deny rc =", r.returncode)
        if r.returncode != 0:
            print("deny 失败，跳过")
            return None
    raised = None
    try:
        mod.copy_post_except_evidence(rec, carrier, out_dir, pre_freshness_snapshot=pre)
    except Exception as exc:
        raised = type(exc).__name__ + ": " + str(exc)
    if deny:
        subprocess.run(["icacls", str(out_dir), "/remove:d", "*S-1-1-0"],
                       capture_output=True)
    return {"tag": tag, "pre_state": pre.get("state"), "raised": raised,
            "spy": dict(spy), "rows": rec.rows}

res = [one_case("B1", deny=False), one_case("B4", deny=True)]
res = [r for r in res if r]
(OUT / "_o1_rows_dump.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
for r in res:
    print("=" * 70)
    print("CASE", r["tag"], "| pre_state =", r["pre_state"])
    print("raised =", r["raised"])
    print("spy.ret =", json.dumps(r["spy"]["ret"], ensure_ascii=False))
    for row in r["rows"]:
        if row["key"] == "freshness_copy_traceback":
            print("---- 完整 traceback（注意文件路径与行号即被核件本体） ----")
            print(row["value"])
print("DUMP_DONE ->", str(OUT / "_o1_rows_dump.json"))
