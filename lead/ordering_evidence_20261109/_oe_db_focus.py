# -*- coding: utf-8 -*-
"""_oe_db_focus.py -- 定点抽取 CLI 会话库中 seal 相关 part 的 rowid/time_created/上下文。
只读 DB；唯一写 = 本任务写域 _oe_db_focus_out.json
Run: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/ordering_evidence_20261109/_oe_db_focus.py"
"""
import sqlite3, json, os, datetime, pathlib
DB = r"C:\Users\Administrator\.zcode\cli\db\db.sqlite"
W = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\ordering_evidence_20261109")
con = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=30)
c = con.cursor()
TZ = datetime.timezone(datetime.timedelta(hours=8))
def fmt(ms):
    if ms is None: return None
    return datetime.datetime.fromtimestamp(ms/1000, TZ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " +08:00"
out = {"tz": "UTC+8", "epoch_unit": "milliseconds", "seal_mtime_epoch_s": 1794220384,
       "seal_mtime_local": "2026-11-09 18:33:04",
       "V1_reg_out_mtime_local": "2026-11-09 13:53:57"}

# 取 rowid 630000~640000 区间内 seal 关键词命中（避免全表 LIKE 扫描）
KEYS = ["63ebd27428c1", "_cr_seal.json", "_cr_build_seal", "SEAL WRITTEN",
        "independent_blind_adjudicator", "_cr_real_verify.py", "_gp_regression_out.json"]
out["earliest_per_key"] = {}
for k in KEYS:
    rows = [list(r) for r in c.execute(
        "SELECT rowid, message_id, session_id, time_created, time_updated, sequence, substr(data,1,400) "
        "FROM part WHERE rowid BETWEEN 600000 AND 644467 AND data LIKE ? ORDER BY rowid LIMIT 6",
        ("%" + k + "%",))]
    out["earliest_per_key"][k] = [{"rowid": r[0], "message_id": r[1], "session_id": r[2],
        "time_created_ms": r[3], "time_created_local": fmt(r[3]), "sequence": r[5],
        "data_head": r[6]} for r in rows]

# 精确取 "SEAL WRITTEN" 命中的 part 全文（生成时刻的直接痕迹）
out["seal_written_parts"] = []
for r in c.execute(
    "SELECT rowid, message_id, session_id, time_created, time_updated, sequence, data "
    "FROM part WHERE rowid BETWEEN 600000 AND 644467 AND data LIKE '%SEAL WRITTEN%' ORDER BY rowid LIMIT 8"):
    out["seal_written_parts"].append({"rowid": r[0], "message_id": r[1], "session_id": r[2],
        "time_created_ms": r[3], "time_created_local": fmt(r[3]), "sequence": r[5],
        "data_full": r[6][:4000]})

# 首个 seal sha 出现的 part 全文
out["first_seal_sha_parts"] = []
for r in c.execute(
    "SELECT rowid, message_id, session_id, time_created, time_updated, sequence, data "
    "FROM part WHERE rowid BETWEEN 630000 AND 644467 AND data LIKE '%63ebd27428c1%' ORDER BY rowid LIMIT 4"):
    out["first_seal_sha_parts"].append({"rowid": r[0], "message_id": r[1], "session_id": r[2],
        "time_created_ms": r[3], "time_created_local": fmt(r[3]), "sequence": r[5],
        "data_full": r[6][:3000]})

# 对照：新写的 _oe_ 件（本会话）在库中的时间戳，验证库是否覆盖当前会话
out["current_session_rows"] = [list(r) for r in c.execute(
    "SELECT rowid,time_created,substr(data,1,120) FROM part WHERE rowid > 644000 ORDER BY rowid LIMIT 5")]

# 该区间内 time_created 的整体范围 + rowid/time 单调性（区间内）
rows = [list(r) for r in c.execute(
    "SELECT rowid,time_created FROM part WHERE rowid BETWEEN 630000 AND 644467 ORDER BY rowid")]
inv = sum(1 for a,b in zip(rows, rows[1:]) if b[1] < a[1])
out["window"] = {"n_rows": len(rows), "first": [rows[0][0], fmt(rows[0][1])],
                 "last": [rows[-1][0], fmt(rows[-1][1])], "n_time_backwards": inv}

# 会话 id -> session 表时间与目录
sids = sorted({p["session_id"] for v in out["earliest_per_key"].values() for p in v})
out["sessions"] = []
for sid in sids[:20]:
    r = c.execute("SELECT id,directory,title,time_created,time_updated FROM session WHERE id=?", (sid,)).fetchone()
    if r:
        out["sessions"].append({"id": r[0], "directory": r[1], "title": r[2],
                                "time_created_local": fmt(r[3]), "time_updated_local": fmt(r[4])})

# tool_usage 在 seal mtime 附近的记录（started_at 单位判定）
out["tool_usage_recent"] = [list(r) for r in c.execute(
    "SELECT tool_name,started_at,completed_at,exit_code,output_bytes,side_effect_scope,read_only "
    "FROM tool_usage ORDER BY started_at DESC LIMIT 5")]

con.close()
op = W / "_oe_db_focus_out.json"
op.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
for k, v in out["earliest_per_key"].items():
    print("KEY %-38s earliest(rowid,t) =", [(p["rowid"], p["time_created_local"]) for p in v[:2]])
print("WINDOW =", out["window"])
print("SESSIONS =", [(s["id"][:16], s["time_created_local"], (s["title"] or "")[:40]) for s in out["sessions"]])
print("TOOL_USAGE_RECENT =", out["tool_usage_recent"][:2])
print("WROTE", op)
