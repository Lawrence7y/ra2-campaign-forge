# -*- coding: utf-8 -*-
"""_oe_deep.py -- 内容因果链细节：5 个 file_sha256 是否在 V1 输出中；DB 中首次/二次 seal 生成输出全文。
只读 DB 与只读域；唯一写 = 本任务写域 _oe_deep_out.json
"""
import sqlite3, json, pathlib, datetime, os, re
DB = r"C:\Users\Administrator\.zcode\cli\db\db.sqlite"
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "ordering_evidence_20261109"
TZ = datetime.timezone(datetime.timedelta(hours=8))
def fmt(ms): return datetime.datetime.fromtimestamp(ms/1000, TZ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
out = {}

# (1) seal 的 5 个 file_sha256 / evidence_span_sha256 是否出现在 V1 三份输出里
sealj = json.loads((ROOT/"lead/cert_realcheck_20261109/_cr_seal.json").read_text(encoding="utf-8"))
V1FILES = [
 "lead/gate_pipeline_20261109/_gp_regression_out.json",
 "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json",
 "lead/gate_pipeline_20261109/_gp_regression_out.txt",
 "lead/gate_r9sem_20261109/_r9s_regress_out.json",
 "lead/gate_r9sem_20261109/_r9s_regress_stdout.txt",
]
blobs = {r: (ROOT/r).read_bytes() for r in V1FILES if (ROOT/r).is_file()}
out["seal_anchor_hashes_in_V1"] = {}
for i, it in enumerate(sealj["items"]):
    for k in ("file_sha256", "evidence_span_sha256"):
        h = it[k].encode()
        out["seal_anchor_hashes_in_V1"]["item%d.%s" % (i, k)] = {
            "sha": it[k], "present_in": [r for r, b in blobs.items() if h in b]}
# seal 自身的 sha 是否在 V1
out["seal_self_sha_in_V1"] = [r for r, b in blobs.items()
    if b"63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23" in b]

# (2) DB 中 3 个关键 Bash part 的完整 output（seal 生成器实跑输出）
con = sqlite3.connect("file:"+DB+"?mode=ro", uri=True, timeout=30)
c = con.cursor()
out["builder_run_parts"] = []
for r in c.execute(
    "SELECT rowid,time_created,data FROM part WHERE rowid IN (635250,635544,635535) ORDER BY rowid"):
    d = json.loads(r[2])
    st = d.get("state", {})
    out["builder_run_parts"].append({
        "rowid": r[0], "time_local": fmt(r[1]),
        "tool": d.get("tool"), "command": st.get("input", {}).get("command"),
        "output": (st.get("output") or "")[-1500:],
        "output_len": len(st.get("output") or "")})
# 提取所有 "sha256 = <64hex>" 和 "bytes=" 行
out["builder_printed_seal_hashes"] = []
for p in out["builder_run_parts"]:
    for m in re.finditer(r"sha256\s*=\s*([0-9a-f]{64})", p["output"] or ""):
        out["builder_printed_seal_hashes"].append({"rowid": p["rowid"], "t": p["time_local"], "sha": m.group(1)})
    for m in re.finditer(r"bytes\s*=\s*(\d+)", p["output"] or ""):
        out["builder_printed_seal_hashes"].append({"rowid": p["rowid"], "t": p["time_local"], "bytes": m.group(1)})

# (3) DB 中最早的 V1 回归相关 part（_gp_regression_out.json / 13:53）
out["V1_parts"] = []
for r in c.execute(
    "SELECT rowid,time_created,substr(data,1,500) FROM part "
    "WHERE rowid BETWEEN 615000 AND 630000 AND data LIKE '%_gp_regression_out.json%' "
    "ORDER BY rowid LIMIT 5"):
    out["V1_parts"].append({"rowid": r[0], "time_local": fmt(r[1]), "head": r[2]})

# (4) _cr_real_verify.py 中常量被写入的 part（old->new）
out["verify_const_edit"] = []
for r in c.execute(
    "SELECT rowid,time_created,data FROM part WHERE rowid=635552"):
    d = json.loads(r[2]); out["verify_const_edit"].append({
        "rowid": r[0], "time_local": fmt(r[1]),
        "old_string": d["state"]["input"].get("old_string"),
        "new_string": d["state"]["input"].get("new_string")})

# (5) rowid 单调性：局部窗口内 time_created 倒退的比例（连续 3 个窗口）
out["rowid_monotonicity_windows"] = []
for lo, hi in [(600000,620000),(620000,635000),(635000,644467)]:
    rows = [list(r) for r in c.execute(
        "SELECT rowid,time_created FROM part WHERE rowid BETWEEN ? AND ? ORDER BY rowid", (lo,hi))]
    inv = sum(1 for a,b in zip(rows,rows[1:]) if b[1] < a[1])
    out["rowid_monotonicity_windows"].append({"window":[lo,hi],"n":len(rows),"backwards":inv})
con.close()

# (6) USN / VSS / 事件日志 可用性（仅查询，不启用/不修改）
import subprocess
def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=True)
        return {"rc": r.returncode, "out": (r.stdout+r.stderr)[:1200]}
    except Exception as e: return {"err": repr(e)}
out["fs_journal_availability"] = {}
out["fs_journal_availability"]["fsutil_usn_queryjournal_D"] = run("fsutil usn queryjournal D: 2>&1")
out["fs_journal_availability"]["vssadmin_list_shadows"] = run("vssadmin list shadows 2>&1")
out["fs_journal_availability"]["wevtutil_security_4663_count"] = run(
    'wevtutil qe Security /q:"*[System[(EventID=4663)]]" /c:1 /f:text /rd:true 2>&1')

op = W/"_oe_deep_out.json"
op.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("SELF_SHA_IN_V1 =", out["seal_self_sha_in_V1"])
print("ANCHOR_HASHES_IN_V1 =", json.dumps(out["seal_anchor_hashes_in_V1"], ensure_ascii=False)[:1500])
print("\nBUILDER RUNS:")
for p in out["builder_run_parts"]:
    print(" rowid=%s t=%s cmd=%s" % (p["rowid"], p["time_local"], p["command"]))
    print("   output_tail:", repr((p["output"] or "")[-420:]))
print("\nPRINTED_HASHES =", out["builder_printed_seal_hashes"])
print("\nVERIFY_CONST_EDIT =", json.dumps(out["verify_const_edit"], ensure_ascii=False)[:900])
print("\nV1_PARTS =", [(p["rowid"], p["time_local"]) for p in out["V1_parts"]])
print("\nROWID_MONO =", out["rowid_monotonicity_windows"])
print("\nFS_JOURNAL =", json.dumps(out["fs_journal_availability"], ensure_ascii=False)[:1400])
print("WROTE", op)
