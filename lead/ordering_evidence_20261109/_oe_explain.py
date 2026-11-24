# -*- coding: utf-8 -*-
"""_oe_explain.py -- 解释 ctime 异常（首次生成 vs 覆写）、atime 可读性漂移、
WHITELIST 在 append-only DB 中的最早出现（内容/日志级定序）。
只读 DB 与只读域；唯一写 = 本任务写域 _oe_explain_out.json
"""
import sqlite3, json, pathlib, datetime, os, time
DB = r"C:\Users\Administrator\.zcode\cli\db\db.sqlite"
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "ordering_evidence_20261109"
TZ = datetime.timezone(datetime.timedelta(hours=8))
def fmt(ms): return datetime.datetime.fromtimestamp(ms/1000, TZ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " +08:00"
out = {}

# (1) seal ctime/mtime 精确 epoch，与 DB 两次生成时刻对齐
p = ROOT/"lead/cert_realcheck_20261109/_cr_seal.json"
s = p.stat()
b = ROOT/"lead/cert_realcheck_20261109/_cr_build_seal.py"
bs = b.stat()
out["seal_times_exact"] = {
  "mtime_epoch": s.st_mtime, "ctime_epoch": s.st_ctime, "atime_epoch": s.st_atime,
  "mtime_local": fmt(s.st_mtime*1000), "ctime_local": fmt(s.st_ctime*1000),
  "atime_local": fmt(s.st_atime*1000), "bytes": s.st_size,
}
out["builder_times_exact"] = {
  "mtime_epoch": bs.st_mtime, "ctime_epoch": bs.st_ctime,
  "mtime_local": fmt(bs.st_mtime*1000), "ctime_local": fmt(bs.st_ctime*1000), "bytes": bs.st_size}

# (2) atime 漂移实证：读之前记一次，读之后记一次（只读操作引起的元数据写入）
rel = "lead/seal_chronology_20261109/_sc_ctime.py"
q = ROOT/rel
a0 = q.stat().st_atime
q.read_bytes()
a1 = q.stat().st_atime
out["atime_drift_on_read"] = {"file": rel, "atime_before_epoch": a0, "atime_after_epoch": a1,
   "atime_before_local": fmt(a0*1000), "atime_after_local": fmt(a1*1000),
   "changed_by_our_own_read": a1 > a0}

con = sqlite3.connect("file:"+DB+"?mode=ro", uri=True, timeout=30)
c = con.cursor()
# (3) DB 两次 _cr_build_seal.py 实跑的完整时序（append-only rowid 顺序）
out["two_builder_runs"] = []
for r in c.execute(
   "SELECT rowid,time_created,data FROM part WHERE rowid IN (635243,635245,635250,635535,635544,635552) ORDER BY rowid"):
    d = json.loads(r[2]); st = d.get("state",{}); inp = st.get("input",{})
    o = st.get("output") or ""
    out["two_builder_runs"].append({
      "rowid": r[0], "time_local": fmt(r[1]), "tool": d.get("tool"),
      "file_path": inp.get("file_path"), "command": inp.get("command"),
      "seal_written_line": [ln for ln in o.splitlines() if "sha256 = " in ln or "bytes  =" in ln or "SEAL WRITTEN" in ln][-4:],
    })

# (4) WHITELIST 字面量 / spec keys 在 DB 中最早出现（是否在 V1 输出之前）
# 用高频唯一串缩小扫描范围
needles = ["需谁批准", "本次任务书指名要求改判的 5 处", "WHITELIST = {", "s604_script_gap_20261109", "matrix_ab_ruling_20261109"]
out["whitelist_earliest"] = {}
for k in needles:
    rows = [list(r) for r in c.execute(
      "SELECT rowid,time_created,substr(data,1,220) FROM part WHERE rowid < 635000 AND data LIKE ? ORDER BY rowid LIMIT 3",
      ("%"+k+"%",))]
    out["whitelist_earliest"][k] = [{"rowid": r[0], "t": fmt(r[1]), "head": r[2]} for r in rows]

# (5) V1 回归输出生成 part（含 13:53 或 V1 完成字样）
out["V1_output_parts"] = []
for r in c.execute(
   "SELECT rowid,time_created,substr(data,1,260) FROM part "
   "WHERE rowid BETWEEN 619000 AND 626000 AND (data LIKE '%_gp_regression_out.json%' OR data LIKE '%_r9s_regress_out.json%') "
   "ORDER BY rowid LIMIT 8"):
    out["V1_output_parts"].append({"rowid": r[0], "t": fmt(r[1]), "head": r[2]})

# (6) dwf_run / dwf_event 是否提供更干净的 sequence 顺序（含本次工作流）
out["dwf_run_recent"] = [list(r) for r in c.execute(
   "SELECT id,cwd,time_created,time_updated,status FROM dwf_run ORDER BY time_created DESC LIMIT 5")]
out["dwf_event_seq_sample"] = [list(r) for r in c.execute(
   "SELECT run_id,sequence,type,time_created FROM dwf_event ORDER BY time_created DESC LIMIT 5")]

# (7) part rowid 非单调的成因样本：同一 session 内相邻 rowid 的 time_created
out["rowid_inversion_examples"] = []
rows = [list(r) for r in c.execute(
   "SELECT rowid,session_id,time_created FROM part WHERE rowid BETWEEN 635000 AND 636000 ORDER BY rowid")]
for a,bb in zip(rows,rows[1:]):
    if bb[2] < a[2]:
        out["rowid_inversion_examples"].append([a,bb])
        if len(out["rowid_inversion_examples"])>=4: break
con.close()

op = W/"_oe_explain_out.json"
op.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("SEAL_TIMES =", json.dumps(out["seal_times_exact"], ensure_ascii=False))
print("BUILDER_TIMES =", json.dumps(out["builder_times_exact"], ensure_ascii=False))
print("ATIME_DRIFT =", json.dumps(out["atime_drift_on_read"], ensure_ascii=False))
print("\nTWO BUILDER RUNS + EDITS:")
for x in out["two_builder_runs"]:
    print(" rowid=%-7s t=%s tool=%-6s %s" % (x["rowid"], x["time_local"], x["tool"],
        (x["file_path"] or x["command"] or "")[:95]))
    if x["seal_written_line"]: print("    ", x["seal_written_line"])
print("\nWHITELIST_EARLIEST:")
for k,v in out["whitelist_earliest"].items():
    print(" ", k, "->", [(p["rowid"],p["t"]) for p in v])
print("\nV1_PARTS:", [(x["rowid"],x["t"]) for x in out["V1_output_parts"]])
print("\nDWF_RUN_RECENT:", out["dwf_run_recent"][:2])
print("DWF_EVENT:", out["dwf_event_seq_sample"][:2])
print("INVERSION_EX:", json.dumps(out["rowid_inversion_examples"][:2], ensure_ascii=False)[:600])
print("WROTE", op)
